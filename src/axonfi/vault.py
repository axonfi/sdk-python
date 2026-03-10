"""Owner write operations: deploy vault, add/update/remove bots, deposit."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx
from web3 import Web3
from web3.types import TxReceipt

from .abis import AXON_VAULT_ABI, AXON_VAULT_FACTORY_ABI, ERC20_ABI
from .amounts import parse_amount
from .constants import ALLOWED_WINDOWS, NATIVE_ETH, RELAYER_URL
from .tokens import resolve_token

# ============================================================================
# Types
# ============================================================================

USDC_DECIMALS = 6
USDC_UNIT = 10**USDC_DECIMALS  # 1_000_000


@dataclass
class SpendingLimitInput:
    """Human-friendly spending limit. Dollar amounts are plain numbers (e.g. 1000 = $1,000)."""

    amount: float
    """Max spend in this window in USD (e.g. 1000 = $1,000)."""
    max_count: int
    """Max transactions in this window. 0 = no count limit."""
    window_seconds: int
    """Window size in seconds. Use WINDOW constants."""


@dataclass
class BotConfigInput:
    """Human-friendly bot config. Dollar amounts are plain numbers (e.g. 100 = $100).

    The SDK converts to 6-decimal base units (USDC precision) before sending to the contract.
    """

    max_per_tx_amount: float
    """Hard per-tx cap in USD (e.g. 100 = $100). 0 = no cap."""
    max_rebalance_amount: float
    """Hard rebalance cap in USD (e.g. 50 = $50). 0 = no cap."""
    spending_limits: list[SpendingLimitInput]
    """Rolling window spending limits. Up to 5."""
    ai_trigger_threshold: float
    """AI scan trigger threshold in USD (e.g. 50 = $50). 0 = never by amount."""
    require_ai_verification: bool
    """Always require AI scan regardless of amount."""


def _to_config_params(config: BotConfigInput) -> tuple:
    """Convert BotConfigInput to the on-chain tuple format."""
    for sl in config.spending_limits:
        if sl.window_seconds not in ALLOWED_WINDOWS:
            allowed = ", ".join(f"{w}s" for w in sorted(ALLOWED_WINDOWS))
            raise ValueError(
                f"Invalid spending window: {sl.window_seconds}s. Allowed: {allowed}. Use WINDOW constants."
            )
    return (
        round(config.max_per_tx_amount * USDC_UNIT),
        round(config.max_rebalance_amount * USDC_UNIT),
        [(round(sl.amount * USDC_UNIT), sl.max_count, sl.window_seconds) for sl in config.spending_limits],
        round(config.ai_trigger_threshold * USDC_UNIT),
        config.require_ai_verification,
    )


# ============================================================================
# Factory address resolution
# ============================================================================


def _get_factory_address(chain_id: int, relayer_url: str | None = None) -> str:
    """Fetch the factory address for a chain from the relayer."""
    base = relayer_url or RELAYER_URL
    resp = httpx.get(f"{base}/v1/chains", timeout=10)
    resp.raise_for_status()
    data = resp.json()
    for chain in data.get("chains", []):
        if chain.get("chainId") == chain_id and chain.get("factoryAddress"):
            return Web3.to_checksum_address(chain["factoryAddress"])
    raise ValueError(f"No factory address available for chainId {chain_id}")


# ============================================================================
# Owner write operations
# ============================================================================


def operator_max_drain_per_day(
    max_operator_bots: int,
    max_bot_daily_limit: float,
    vault_daily_aggregate: float = 0,
) -> float:
    """Compute max USD an operator-compromised wallet could drain per day.

    Pure computation — no RPC call needed. Pass values from operator ceilings.

    Args:
        max_operator_bots: Maximum bots the operator can add.
        max_bot_daily_limit: Per-bot daily limit in USD (e.g. 5000 = $5,000).
        vault_daily_aggregate: Vault-wide daily aggregate cap in USD. 0 = no cap.

    Returns:
        Maximum daily drain in USD (e.g. 10000 = $10,000).
    """
    if max_operator_bots == 0 or max_bot_daily_limit == 0:
        return 0
    theoretical = max_operator_bots * max_bot_daily_limit
    if vault_daily_aggregate > 0 and vault_daily_aggregate < theoretical:
        return vault_daily_aggregate
    return theoretical


ZERO_REF = b"\x00" * 32


def deploy_vault(
    w3: Web3,
    account: Any,
    chain_id: int,
    *,
    relayer_url: str | None = None,
) -> str:
    """Deploy a new AxonVault via the factory.

    The factory address is fetched automatically from the Axon relayer.

    Args:
        w3: Web3 instance connected to the target chain's RPC.
        account: Account object with address and key (e.g. ``Account.from_key(...)``).
        chain_id: Target chain ID.
        relayer_url: Override relayer URL (defaults to https://relay.axonfi.xyz).

    Returns:
        Vault address (checksummed).
    """
    factory_address = _get_factory_address(chain_id, relayer_url)
    factory = w3.eth.contract(address=factory_address, abi=AXON_VAULT_FACTORY_ABI)

    tx = factory.functions.deployVault().build_transaction(
        {
            "from": account.address,
            "nonce": w3.eth.get_transaction_count(account.address),
            "chainId": chain_id,
        }
    )
    signed = account.sign_transaction(tx)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    receipt: TxReceipt = w3.eth.wait_for_transaction_receipt(tx_hash)

    # Extract vault address from VaultDeployed event (second indexed topic)
    for log in receipt.get("logs", []):
        if len(log.get("topics", [])) >= 3:
            vault_addr = "0x" + log["topics"][2].hex()[-40:]
            return Web3.to_checksum_address(vault_addr)

    raise RuntimeError("VaultDeployed event not found in transaction receipt")


def add_bot(
    w3: Web3,
    account: Any,
    vault_address: str,
    bot_address: str,
    config: BotConfigInput,
) -> str:
    """Register a bot on the vault with its spending configuration.

    Dollar amounts in config are plain numbers (e.g. 100 = $100).
    The SDK converts to 6-decimal base units automatically.

    Args:
        w3: Web3 instance connected to the vault's chain.
        account: Owner or operator account.
        vault_address: Vault to register the bot on.
        bot_address: Public address of the bot.
        config: Bot spending configuration (human-readable USD amounts).

    Returns:
        Transaction hash (hex).
    """
    vault = w3.eth.contract(address=Web3.to_checksum_address(vault_address), abi=AXON_VAULT_ABI)
    params = _to_config_params(config)

    tx = vault.functions.addBot(Web3.to_checksum_address(bot_address), params).build_transaction(
        {
            "from": account.address,
            "nonce": w3.eth.get_transaction_count(account.address),
        }
    )
    signed = account.sign_transaction(tx)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    w3.eth.wait_for_transaction_receipt(tx_hash)
    return tx_hash.hex()


def update_bot_config(
    w3: Web3,
    account: Any,
    vault_address: str,
    bot_address: str,
    config: BotConfigInput,
) -> str:
    """Update an existing bot's spending configuration.

    Args:
        w3: Web3 instance connected to the vault's chain.
        account: Owner or operator account.
        vault_address: Vault the bot is registered on.
        bot_address: Bot to update.
        config: New spending configuration (human-readable USD amounts).

    Returns:
        Transaction hash (hex).
    """
    vault = w3.eth.contract(address=Web3.to_checksum_address(vault_address), abi=AXON_VAULT_ABI)
    params = _to_config_params(config)

    tx = vault.functions.updateBotConfig(Web3.to_checksum_address(bot_address), params).build_transaction(
        {
            "from": account.address,
            "nonce": w3.eth.get_transaction_count(account.address),
        }
    )
    signed = account.sign_transaction(tx)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    w3.eth.wait_for_transaction_receipt(tx_hash)
    return tx_hash.hex()


def remove_bot(
    w3: Web3,
    account: Any,
    vault_address: str,
    bot_address: str,
) -> str:
    """Remove a bot from the vault whitelist.

    Args:
        w3: Web3 instance connected to the vault's chain.
        account: Owner or operator account.
        vault_address: Vault to remove the bot from.
        bot_address: Bot to remove.

    Returns:
        Transaction hash (hex).
    """
    vault = w3.eth.contract(address=Web3.to_checksum_address(vault_address), abi=AXON_VAULT_ABI)

    tx = vault.functions.removeBot(Web3.to_checksum_address(bot_address)).build_transaction(
        {
            "from": account.address,
            "nonce": w3.eth.get_transaction_count(account.address),
        }
    )
    signed = account.sign_transaction(tx)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    w3.eth.wait_for_transaction_receipt(tx_hash)
    return tx_hash.hex()


def deposit(
    w3: Web3,
    account: Any,
    vault_address: str,
    token: str,
    amount: int | float | str,
    *,
    chain_id: int | None = None,
    ref: bytes = ZERO_REF,
) -> str:
    """Deposit tokens or native ETH into the vault.

    Permissionless — anyone can deposit. For ERC-20 tokens, this function
    handles the approve + deposit in one call. For native ETH, pass
    ``'ETH'`` or ``NATIVE_ETH`` as the token.

    Amounts are human-friendly when passed as ``float`` or ``str``
    (e.g. ``500.0`` or ``"500"`` for 500 USDC). Plain ``int`` is treated
    as raw base units for backwards compatibility.

    Args:
        w3: Web3 instance connected to the vault's chain.
        account: Wallet sending the deposit (anyone, not just owner).
        vault_address: Vault to deposit into.
        token: Token symbol ('USDC', 'WETH'), raw address, NATIVE_ETH, or 'ETH' for ETH deposits.
        amount: Human-readable (float/str, e.g. 500.0 for 500 USDC) or raw base units (int).
        chain_id: Chain ID for token symbol resolution. Falls back to ``w3.eth.chain_id``.
        ref: Optional bytes32 reference. Defaults to zero bytes.

    Returns:
        Transaction hash (hex).
    """
    vault_addr = Web3.to_checksum_address(vault_address)
    vault = w3.eth.contract(address=vault_addr, abi=AXON_VAULT_ABI)

    # Resolve token symbol to address
    if token.upper() == "ETH":
        token_address = NATIVE_ETH
    elif token.startswith("0x"):
        token_address = token
    else:
        cid = chain_id if chain_id is not None else w3.eth.chain_id
        token_address = resolve_token(token, cid)

    is_eth = token_address.lower() == NATIVE_ETH.lower()

    # Resolve human-readable amount to base units
    if is_eth:
        resolved_amount = parse_amount(amount, "WETH")  # ETH has same 18 decimals as WETH
    else:
        resolved_amount = parse_amount(amount, token)

    if not is_eth:
        # ERC-20: approve the vault to pull tokens, then deposit
        token_addr = Web3.to_checksum_address(token_address)
        erc20 = w3.eth.contract(address=token_addr, abi=ERC20_ABI)
        approve_tx = erc20.functions.approve(vault_addr, resolved_amount).build_transaction(
            {
                "from": account.address,
                "nonce": w3.eth.get_transaction_count(account.address),
            }
        )
        signed_approve = account.sign_transaction(approve_tx)
        approve_hash = w3.eth.send_raw_transaction(signed_approve.raw_transaction)
        w3.eth.wait_for_transaction_receipt(approve_hash)

    tx_params: dict = {
        "from": account.address,
        "nonce": w3.eth.get_transaction_count(account.address),
    }
    if is_eth:
        tx_params["value"] = resolved_amount

    token_for_contract = Web3.to_checksum_address(token_address)
    tx = vault.functions.deposit(token_for_contract, resolved_amount, ref).build_transaction(tx_params)
    signed = account.sign_transaction(tx)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    w3.eth.wait_for_transaction_receipt(tx_hash)
    return tx_hash.hex()
