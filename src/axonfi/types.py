"""Dataclasses for Axon SDK types — intents, inputs, and results."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

# ============================================================================
# On-chain structs (mirror Solidity exactly)
# ============================================================================


@dataclass(frozen=True)
class PaymentIntent:
    """Signed payment intent — the core signed data unit."""

    bot: str
    to: str
    token: str
    amount: int
    deadline: int
    ref: str  # bytes32 hex


@dataclass(frozen=True)
class ExecuteIntent:
    """Signed execute intent for DeFi protocol interactions."""

    bot: str
    protocol: str
    calldata_hash: str  # bytes32 hex
    token: str
    amount: int
    deadline: int
    ref: str


@dataclass(frozen=True)
class SwapIntent:
    """Signed swap intent for in-vault token rebalancing."""

    bot: str
    to_token: str
    min_to_amount: int
    deadline: int
    ref: str


# ============================================================================
# SDK input types
# ============================================================================


@dataclass
class PayInput:
    """Input for AxonClient.pay()."""

    to: str
    token: str  # Address, Token enum, or bare symbol ('USDC')
    amount: int | float | str  # raw base units, human number, or human string

    memo: str | None = None
    idempotency_key: str | None = None
    resource_url: str | None = None
    invoice_id: str | None = None
    order_id: str | None = None
    recipient_label: str | None = None
    metadata: dict[str, str] | None = None
    deadline: int | None = None
    ref: str | None = None  # Override ref bytes32 directly
    x402_funding: bool | None = None  # x402 bot-EOA funding flag


@dataclass
class ExecuteInput:
    """Input for AxonClient.execute()."""

    protocol: str
    call_data: str  # hex bytes
    token: str
    amount: int | float | str

    memo: str | None = None
    protocol_name: str | None = None
    ref: str | None = None
    idempotency_key: str | None = None
    deadline: int | None = None
    metadata: dict[str, str] | None = None

    # Pre-swap fields
    from_token: str | None = None
    max_from_amount: int | float | str | None = None


@dataclass
class SwapInput:
    """Input for AxonClient.swap()."""

    to_token: str
    min_to_amount: int | float | str

    memo: str | None = None
    ref: str | None = None
    idempotency_key: str | None = None
    deadline: int | None = None

    # Swap source
    from_token: str | None = None
    max_from_amount: int | float | str | None = None


# ============================================================================
# Result types
# ============================================================================

PaymentStatus = Literal["approved", "pending_review", "rejected"]


@dataclass
class PaymentResult:
    """Result of pay(), execute(), swap(), or poll()."""

    request_id: str
    status: PaymentStatus
    tx_hash: str | None = None
    poll_url: str | None = None
    estimated_resolution_ms: int | None = None
    reason: str | None = None


@dataclass
class VaultInfo:
    """High-level vault info."""

    owner: str
    operator: str
    paused: bool
    version: int


@dataclass
class DestinationCheckResult:
    """Result of a destination check."""

    allowed: bool
    reason: str | None = None


@dataclass
class RebalanceTokensResult:
    """Effective rebalance token whitelist."""

    source: Literal["default", "on_chain"]
    tokens: list[str]
    rebalance_token_count: int


@dataclass
class TosStatus:
    """TOS acceptance status."""

    accepted: bool
    tos_version: str


@dataclass
class AxonClientConfig:
    """Configuration for AxonClient."""

    vault_address: str
    chain_id: int
    bot_private_key: str  # hex, 0x-prefixed
