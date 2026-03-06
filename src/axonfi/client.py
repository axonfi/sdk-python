"""AxonClient — main entry point for bots interacting with Axon."""

from __future__ import annotations

import asyncio
import time
import uuid
from typing import Any

import httpx
from eth_account import Account
from web3 import Web3

from .amounts import parse_amount
from .constants import DEFAULT_DEADLINE_SECONDS, RELAYER_URL, USDC, RelayerAPI
from .eip3009 import USDC_EIP712_DOMAIN, random_nonce, sign_transfer_with_authorization
from .permit2 import X402_PROXY_ADDRESS, random_permit2_nonce, sign_permit2_witness_transfer
from .signer import encode_ref, sign_execute_intent, sign_payment, sign_swap_intent
from .tokens import resolve_token
from .types import (
    DestinationCheckResult,
    ExecuteInput,
    ExecuteIntent,
    PayInput,
    PaymentIntent,
    PaymentResult,
    RebalanceTokensResult,
    SwapInput,
    SwapIntent,
    TosStatus,
    VaultInfo,
)
from .x402 import (
    X402HandleResult,
    extract_x402_metadata,
    find_matching_option,
    format_payment_signature,
    parse_payment_required,
)


class AxonClient:
    """Async client for bots interacting with Axon.

    Handles EIP-712 signing, relayer communication, and status polling.
    Bots never submit transactions directly — they sign intents and the relayer
    handles all on-chain execution.

    Example::

        from axonfi import AxonClient

        client = AxonClient(
            vault_address="0x...",
            chain_id=84532,           # Base Sepolia
            bot_private_key="0x...",
        )

        result = await client.pay(to="0x...", token="USDC", amount=5)
        print(result.status, result.tx_hash)
    """

    def __init__(
        self,
        vault_address: str,
        chain_id: int,
        bot_private_key: str,
        relayer_url: str | None = None,
    ) -> None:
        self.vault_address = vault_address
        self.chain_id = chain_id
        self._private_key = bot_private_key
        self._relayer_url = relayer_url or RELAYER_URL
        self._account = Account.from_key(bot_private_key)
        self._http: httpx.AsyncClient | None = None

    @property
    def bot_address(self) -> str:
        """The bot's address derived from the private key."""
        return self._account.address

    async def _client(self) -> httpx.AsyncClient:
        if self._http is None or self._http.is_closed:
            self._http = httpx.AsyncClient(base_url=self._relayer_url, timeout=30.0)
        return self._http

    async def close(self) -> None:
        """Close the underlying HTTP client."""
        if self._http and not self._http.is_closed:
            await self._http.aclose()

    # ========================================================================
    # pay()
    # ========================================================================

    async def pay(
        self,
        to: str,
        token: str,
        amount: int | float | str,
        *,
        memo: str | None = None,
        idempotency_key: str | None = None,
        resource_url: str | None = None,
        invoice_id: str | None = None,
        order_id: str | None = None,
        recipient_label: str | None = None,
        metadata: dict[str, str] | None = None,
        deadline: int | None = None,
        ref: str | None = None,
        x402_funding: bool | None = None,
    ) -> PaymentResult:
        """Create, sign, and submit a payment intent."""
        inp = PayInput(
            to=to,
            token=token,
            amount=amount,
            memo=memo,
            idempotency_key=idempotency_key,
            resource_url=resource_url,
            invoice_id=invoice_id,
            order_id=order_id,
            recipient_label=recipient_label,
            metadata=metadata,
            deadline=deadline,
            ref=ref,
            x402_funding=x402_funding,
        )
        intent = self._build_payment_intent(inp)
        signature = sign_payment(self._private_key, self.vault_address, self.chain_id, intent)
        return await self._submit_payment(intent, signature, inp)

    # ========================================================================
    # execute()
    # ========================================================================

    async def execute(
        self,
        protocol: str,
        call_data: str,
        token: str,
        amount: int | float | str,
        *,
        memo: str | None = None,
        protocol_name: str | None = None,
        ref: str | None = None,
        idempotency_key: str | None = None,
        deadline: int | None = None,
        metadata: dict[str, str] | None = None,
        from_token: str | None = None,
        max_from_amount: int | float | str | None = None,
    ) -> PaymentResult:
        """Sign and submit a DeFi protocol execution."""
        inp = ExecuteInput(
            protocol=protocol,
            call_data=call_data,
            token=token,
            amount=amount,
            memo=memo,
            protocol_name=protocol_name,
            ref=ref,
            idempotency_key=idempotency_key,
            deadline=deadline,
            metadata=metadata,
            from_token=from_token,
            max_from_amount=max_from_amount,
        )
        intent = self._build_execute_intent(inp)
        signature = sign_execute_intent(self._private_key, self.vault_address, self.chain_id, intent)
        return await self._submit_execute(intent, signature, inp)

    # ========================================================================
    # swap()
    # ========================================================================

    async def swap(
        self,
        to_token: str,
        min_to_amount: int | float | str,
        *,
        memo: str | None = None,
        ref: str | None = None,
        idempotency_key: str | None = None,
        deadline: int | None = None,
        from_token: str | None = None,
        max_from_amount: int | float | str | None = None,
    ) -> PaymentResult:
        """Sign and submit an in-vault token swap."""
        inp = SwapInput(
            to_token=to_token,
            min_to_amount=min_to_amount,
            memo=memo,
            ref=ref,
            idempotency_key=idempotency_key,
            deadline=deadline,
            from_token=from_token,
            max_from_amount=max_from_amount,
        )
        intent = self._build_swap_intent(inp)
        signature = sign_swap_intent(self._private_key, self.vault_address, self.chain_id, intent)
        return await self._submit_swap(intent, signature, inp)

    # ========================================================================
    # x402 (HTTP 402 Payment Required)
    # ========================================================================

    async def x402_fund(
        self,
        amount: int,
        token: str | None = None,
        *,
        resource_url: str | None = None,
        memo: str | None = None,
        recipient_label: str | None = None,
        metadata: dict[str, str] | None = None,
    ) -> PaymentResult:
        """Fund the bot's EOA from the vault for x402 settlement.

        This is a regular Axon payment (to = bot's own address) that goes through
        the full pipeline: policy engine, AI scan, human review if needed.
        """
        token_address = token or USDC.get(self.chain_id)
        if not token_address:
            raise ValueError(f"No default USDC address for chain {self.chain_id}")

        return await self.pay(
            to=self.bot_address,
            token=token_address,
            amount=amount,
            x402_funding=True,
            resource_url=resource_url,
            memo=memo,
            recipient_label=recipient_label,
            metadata=metadata,
        )

    async def x402_handle_payment_required(
        self,
        headers: dict[str, str],
        max_timeout_ms: int = 120_000,
        poll_interval_ms: int = 5_000,
    ) -> X402HandleResult:
        """Handle a full x402 flow: parse header, fund bot, sign authorization, return header.

        Supports both EIP-3009 (USDC) and Permit2 (any ERC-20) settlement.
        The bot's EOA is funded from the vault first (full Axon pipeline applies).

        Args:
            headers: Response headers dict (must contain ``payment-required`` or ``PAYMENT-REQUIRED``).
            max_timeout_ms: Maximum time to wait for pending_review resolution (default: 120s).
            poll_interval_ms: Polling interval for pending_review (default: 5s).

        Returns:
            ``X402HandleResult`` with payment signature, selected option, and funding details.
        """
        # 1. Parse header
        header_value = headers.get("payment-required") or headers.get("PAYMENT-REQUIRED")
        if not header_value:
            raise ValueError("x402: no PAYMENT-REQUIRED header found")

        parsed = parse_payment_required(header_value)

        # 2. Find matching option for this chain
        option = find_matching_option(parsed.accepts, self.chain_id)
        if not option:
            networks = ", ".join(a.network for a in parsed.accepts)
            raise ValueError(f"x402: no payment option matches chain {self.chain_id}. Available: {networks}")

        # 3. Extract metadata
        x402_meta = extract_x402_metadata(parsed, option)

        # 4. Fund bot's EOA from vault
        amount = int(option.amount)
        token_address = option.asset

        funding_result = await self.pay(
            to=self.bot_address,
            token=token_address,
            amount=amount,
            x402_funding=True,
            resource_url=x402_meta.get("resource_url"),
            memo=x402_meta.get("memo"),
            recipient_label=x402_meta.get("recipient_label"),
            metadata=x402_meta.get("metadata"),
        )

        # 5. Poll if pending_review
        if funding_result.status == "pending_review":
            import asyncio

            deadline_ts = time.time() * 1000 + max_timeout_ms
            while funding_result.status == "pending_review" and time.time() * 1000 < deadline_ts:
                await asyncio.sleep(poll_interval_ms / 1000)
                funding_result = await self.poll(funding_result.request_id)
            if funding_result.status == "pending_review":
                raise RuntimeError(f"x402: funding timed out after {max_timeout_ms}ms (still pending_review)")

        if funding_result.status == "rejected":
            raise RuntimeError(f"x402: funding rejected — {funding_result.reason or 'unknown reason'}")

        # 6. Sign appropriate authorization
        pay_to = option.pay_to
        usdc_address = (USDC.get(self.chain_id) or "").lower()
        is_usdc = token_address.lower() == usdc_address

        if is_usdc and self.chain_id in USDC_EIP712_DOMAIN:
            # EIP-3009 path (USDC — gasless)
            nonce = random_nonce()
            valid_after = 0
            valid_before = int(time.time()) + 300  # 5 min

            sig = sign_transfer_with_authorization(
                self._private_key,
                self.chain_id,
                from_address=self.bot_address,
                to=pay_to,
                value=amount,
                valid_after=valid_after,
                valid_before=valid_before,
                nonce=nonce,
            )

            signature_payload = {
                "scheme": "exact",
                "signature": sig,
                "authorization": {
                    "from": self.bot_address,
                    "to": pay_to,
                    "value": str(amount),
                    "validAfter": str(valid_after),
                    "validBefore": str(valid_before),
                    "nonce": nonce,
                },
            }
        else:
            # Permit2 path (any ERC-20)
            nonce = random_permit2_nonce()
            deadline = int(time.time()) + 300

            sig = sign_permit2_witness_transfer(
                self._private_key,
                self.chain_id,
                token=token_address,
                amount=amount,
                spender=X402_PROXY_ADDRESS,
                nonce=nonce,
                deadline=deadline,
                witness_to=pay_to,
                witness_requested_amount=amount,
            )

            signature_payload = {
                "scheme": "permit2",
                "signature": sig,
                "permit": {
                    "permitted": {"token": token_address, "amount": str(amount)},
                    "spender": X402_PROXY_ADDRESS,
                    "nonce": str(nonce),
                    "deadline": str(deadline),
                },
                "witness": {
                    "to": pay_to,
                    "requestedAmount": str(amount),
                },
            }

        # 7. Format PAYMENT-SIGNATURE header
        payment_signature = format_payment_signature(signature_payload)

        funding_data: dict = {
            "requestId": funding_result.request_id,
            "status": funding_result.status,
        }
        if funding_result.tx_hash:
            funding_data["txHash"] = funding_result.tx_hash

        return X402HandleResult(
            payment_signature=payment_signature,
            selected_option=option,
            funding_result=funding_data,
        )

    # ========================================================================
    # Read helpers
    # ========================================================================

    async def get_balance(self, token: str) -> int:
        """Read the vault's ERC-20 balance for a given token (via relayer)."""
        path = RelayerAPI.vault_balance(self.vault_address, token, self.chain_id)
        data = await self._get(path)
        return int(data["balance"])

    async def get_balances(self, tokens: list[str]) -> dict[str, int]:
        """Read multiple token balances in a single call."""
        path = RelayerAPI.vault_balances(self.vault_address, self.chain_id)
        client = await self._client()
        resp = await client.get(
            path,
            params={"chainId": self.chain_id, "tokens": ",".join(tokens)},
        )
        resp.raise_for_status()
        data = resp.json()
        return {addr: int(val) for addr, val in data["balances"].items()}

    async def is_active(self) -> bool:
        """Whether this bot is registered and active in the vault."""
        path = RelayerAPI.bot_status(self.vault_address, self.bot_address, self.chain_id)
        data = await self._get(path)
        return data["isActive"]

    async def is_paused(self) -> bool:
        """Whether the vault is currently paused."""
        path = RelayerAPI.vault_info(self.vault_address, self.chain_id)
        data = await self._get(path)
        return data["paused"]

    async def get_vault_info(self) -> VaultInfo:
        """High-level vault info (owner, operator, paused, version)."""
        path = RelayerAPI.vault_info(self.vault_address, self.chain_id)
        data = await self._get(path)
        return VaultInfo(
            owner=data["owner"],
            operator=data["operator"],
            paused=data["paused"],
            version=data["version"],
        )

    async def can_pay_to(self, destination: str) -> DestinationCheckResult:
        """Check whether this bot can pay to a given destination."""
        path = RelayerAPI.destination_check(self.vault_address, self.bot_address, destination, self.chain_id)
        data = await self._get(path)
        return DestinationCheckResult(allowed=data["allowed"], reason=data.get("reason"))

    async def is_protocol_approved(self, protocol: str) -> bool:
        """Whether a protocol is approved for executeProtocol() calls."""
        path = RelayerAPI.protocol_check(self.vault_address, protocol, self.chain_id)
        data = await self._get(path)
        return data["approved"]

    async def get_rebalance_tokens(self) -> RebalanceTokensResult:
        """Effective rebalance token whitelist for this vault."""
        path = RelayerAPI.rebalance_tokens(self.vault_address, self.chain_id)
        data = await self._get(path)
        return RebalanceTokensResult(
            source=data["source"],
            tokens=data["tokens"],
            rebalance_token_count=data["rebalanceTokenCount"],
        )

    # ========================================================================
    # Polling
    # ========================================================================

    async def poll(self, request_id: str) -> PaymentResult:
        """Poll for the status of an async payment."""
        return self._parse_result(await self._get(RelayerAPI.payment(request_id)))

    async def poll_execute(self, request_id: str) -> PaymentResult:
        """Poll for the status of an async protocol execution."""
        return self._parse_result(await self._get(RelayerAPI.execute(request_id)))

    async def poll_swap(self, request_id: str) -> PaymentResult:
        """Poll for the status of an async swap."""
        return self._parse_result(await self._get(RelayerAPI.swap(request_id)))

    # ========================================================================
    # TOS
    # ========================================================================

    async def get_tos_status(self, wallet: str) -> TosStatus:
        """Check if a wallet has accepted the current TOS version."""
        data = await self._get(RelayerAPI.tos_status(wallet))
        return TosStatus(accepted=data["accepted"], tos_version=data["tosVersion"])

    # ========================================================================
    # Internal helpers
    # ========================================================================

    async def _get(self, path: str) -> Any:
        client = await self._client()
        resp = await client.get(path)
        if resp.status_code >= 400:
            raise RuntimeError(f"Relayer request failed [{resp.status_code}]: {resp.text}")
        return resp.json()

    async def _post(self, path: str, idempotency_key: str, body: dict) -> PaymentResult:
        client = await self._client()
        resp = await client.post(
            path,
            json=body,
            headers={"Idempotency-Key": idempotency_key},
        )
        if resp.status_code >= 400:
            raise RuntimeError(f"Relayer request failed [{resp.status_code}]: {resp.text}")
        return self._parse_result(resp.json())

    def _default_deadline(self) -> int:
        return int(time.time()) + DEFAULT_DEADLINE_SECONDS

    def _resolve_ref(self, memo: str | None, ref: str | None) -> str:
        if ref:
            return ref
        if memo:
            return encode_ref(memo)
        return "0x" + "00" * 32

    def _build_payment_intent(self, inp: PayInput) -> PaymentIntent:
        if inp.to == "0x0000000000000000000000000000000000000000":
            raise ValueError("Payment recipient cannot be the zero address")
        return PaymentIntent(
            bot=self.bot_address,
            to=inp.to,
            token=resolve_token(inp.token, self.chain_id),
            amount=parse_amount(inp.amount, inp.token),
            deadline=inp.deadline or self._default_deadline(),
            ref=self._resolve_ref(inp.memo, inp.ref),
        )

    def _build_execute_intent(self, inp: ExecuteInput) -> ExecuteIntent:
        return ExecuteIntent(
            bot=self.bot_address,
            protocol=inp.protocol,
            calldata_hash="0x" + Web3.keccak(hexstr=inp.call_data).hex(),
            token=resolve_token(inp.token, self.chain_id),
            amount=parse_amount(inp.amount, inp.token),
            deadline=inp.deadline or self._default_deadline(),
            ref=self._resolve_ref(inp.memo, inp.ref),
        )

    def _build_swap_intent(self, inp: SwapInput) -> SwapIntent:
        return SwapIntent(
            bot=self.bot_address,
            to_token=resolve_token(inp.to_token, self.chain_id),
            min_to_amount=parse_amount(inp.min_to_amount, inp.to_token),
            deadline=inp.deadline or self._default_deadline(),
            ref=self._resolve_ref(inp.memo, inp.ref),
        )

    async def _submit_payment(self, intent: PaymentIntent, signature: str, inp: PayInput) -> PaymentResult:
        idem = inp.idempotency_key or str(uuid.uuid4())
        body: dict[str, Any] = {
            "chainId": self.chain_id,
            "vaultAddress": self.vault_address,
            "bot": intent.bot,
            "to": intent.to,
            "token": intent.token,
            "amount": str(intent.amount),
            "deadline": str(intent.deadline),
            "ref": intent.ref,
            "signature": signature,
            "idempotencyKey": idem,
        }
        if inp.memo is not None:
            body["memo"] = inp.memo
        if inp.resource_url is not None:
            body["resourceUrl"] = inp.resource_url
        if inp.invoice_id is not None:
            body["invoiceId"] = inp.invoice_id
        if inp.order_id is not None:
            body["orderId"] = inp.order_id
        if inp.recipient_label is not None:
            body["recipientLabel"] = inp.recipient_label
        if inp.metadata is not None:
            body["metadata"] = inp.metadata
        if inp.x402_funding is not None:
            body["x402Funding"] = inp.x402_funding
        return await self._post(RelayerAPI.PAYMENTS, idem, body)

    async def _submit_execute(self, intent: ExecuteIntent, signature: str, inp: ExecuteInput) -> PaymentResult:
        idem = inp.idempotency_key or str(uuid.uuid4())
        from_token = resolve_token(inp.from_token, self.chain_id) if inp.from_token else None
        max_from_amount = (
            parse_amount(inp.max_from_amount, inp.from_token or inp.token) if inp.max_from_amount is not None else None
        )

        body: dict[str, Any] = {
            "chainId": self.chain_id,
            "vaultAddress": self.vault_address,
            "bot": intent.bot,
            "protocol": intent.protocol,
            "calldataHash": intent.calldata_hash,
            "token": intent.token,
            "amount": str(intent.amount),
            "deadline": str(intent.deadline),
            "ref": intent.ref,
            "signature": signature,
            "callData": inp.call_data,
            "idempotencyKey": idem,
        }
        if from_token is not None:
            body["fromToken"] = from_token
        if max_from_amount is not None:
            body["maxFromAmount"] = str(max_from_amount)
        if inp.memo is not None:
            body["memo"] = inp.memo
        if inp.protocol_name is not None:
            body["protocolName"] = inp.protocol_name
        if inp.metadata is not None:
            body["metadata"] = inp.metadata
        return await self._post(RelayerAPI.EXECUTE, idem, body)

    async def _submit_swap(self, intent: SwapIntent, signature: str, inp: SwapInput) -> PaymentResult:
        idem = inp.idempotency_key or str(uuid.uuid4())
        from_token = resolve_token(inp.from_token, self.chain_id) if inp.from_token else None
        max_from_amount = (
            parse_amount(inp.max_from_amount, inp.from_token or inp.to_token)
            if inp.max_from_amount is not None
            else None
        )

        body: dict[str, Any] = {
            "chainId": self.chain_id,
            "vaultAddress": self.vault_address,
            "bot": intent.bot,
            "toToken": intent.to_token,
            "minToAmount": str(intent.min_to_amount),
            "deadline": str(intent.deadline),
            "ref": intent.ref,
            "signature": signature,
            "idempotencyKey": idem,
        }
        if from_token is not None:
            body["fromToken"] = from_token
        if max_from_amount is not None:
            body["maxFromAmount"] = str(max_from_amount)
        if inp.memo is not None:
            body["memo"] = inp.memo
        return await self._post(RelayerAPI.SWAP, idem, body)

    @staticmethod
    def _parse_result(data: dict) -> PaymentResult:
        return PaymentResult(
            request_id=data.get("requestId", ""),
            status=data.get("status", "rejected"),
            tx_hash=data.get("txHash"),
            poll_url=data.get("pollUrl"),
            estimated_resolution_ms=data.get("estimatedResolutionMs"),
            reason=data.get("reason"),
        )


class AxonClientSync:
    """Synchronous wrapper around AxonClient for non-async contexts.

    Useful for LangChain, CrewAI, and other frameworks that don't use asyncio.

    Example::

        from axonfi import AxonClientSync

        client = AxonClientSync(
            vault_address="0x...",
            chain_id=84532,
            bot_private_key="0x...",
        )

        result = client.pay(to="0x...", token="USDC", amount=5)
        print(result.status, result.tx_hash)
    """

    def __init__(
        self,
        vault_address: str,
        chain_id: int,
        bot_private_key: str,
        relayer_url: str | None = None,
    ) -> None:
        self._async_client = AxonClient(
            vault_address=vault_address,
            chain_id=chain_id,
            bot_private_key=bot_private_key,
            relayer_url=relayer_url,
        )

    @property
    def bot_address(self) -> str:
        return self._async_client.bot_address

    def _run(self, coro):
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop and loop.is_running():
            # We're inside an existing event loop — use a new thread
            import concurrent.futures

            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                return pool.submit(asyncio.run, coro).result()
        else:
            return asyncio.run(coro)

    def pay(self, to: str, token: str, amount: int | float | str, **kwargs) -> PaymentResult:
        return self._run(self._async_client.pay(to=to, token=token, amount=amount, **kwargs))

    def execute(
        self,
        protocol: str,
        call_data: str,
        token: str,
        amount: int | float | str,
        **kwargs,
    ) -> PaymentResult:
        return self._run(
            self._async_client.execute(
                protocol=protocol,
                call_data=call_data,
                token=token,
                amount=amount,
                **kwargs,
            )
        )

    def swap(self, to_token: str, min_to_amount: int | float | str, **kwargs) -> PaymentResult:
        return self._run(self._async_client.swap(to_token=to_token, min_to_amount=min_to_amount, **kwargs))

    def get_balance(self, token: str) -> int:
        return self._run(self._async_client.get_balance(token))

    def get_balances(self, tokens: list[str]) -> dict[str, int]:
        return self._run(self._async_client.get_balances(tokens))

    def is_active(self) -> bool:
        return self._run(self._async_client.is_active())

    def is_paused(self) -> bool:
        return self._run(self._async_client.is_paused())

    def get_vault_info(self) -> VaultInfo:
        return self._run(self._async_client.get_vault_info())

    def can_pay_to(self, destination: str) -> DestinationCheckResult:
        return self._run(self._async_client.can_pay_to(destination))

    def is_protocol_approved(self, protocol: str) -> bool:
        return self._run(self._async_client.is_protocol_approved(protocol))

    def get_rebalance_tokens(self) -> RebalanceTokensResult:
        return self._run(self._async_client.get_rebalance_tokens())

    def x402_fund(self, amount: int, token: str | None = None, **kwargs) -> PaymentResult:
        return self._run(self._async_client.x402_fund(amount, token, **kwargs))

    def x402_handle_payment_required(
        self,
        headers: dict[str, str],
        max_timeout_ms: int = 120_000,
        poll_interval_ms: int = 5_000,
    ):

        return self._run(self._async_client.x402_handle_payment_required(headers, max_timeout_ms, poll_interval_ms))

    def poll(self, request_id: str) -> PaymentResult:
        return self._run(self._async_client.poll(request_id))

    def poll_execute(self, request_id: str) -> PaymentResult:
        return self._run(self._async_client.poll_execute(request_id))

    def poll_swap(self, request_id: str) -> PaymentResult:
        return self._run(self._async_client.poll_swap(request_id))

    def get_tos_status(self, wallet: str) -> TosStatus:
        return self._run(self._async_client.get_tos_status(wallet))

    def close(self) -> None:
        self._run(self._async_client.close())
