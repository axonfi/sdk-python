"""axonfi — Treasury and payment infrastructure for autonomous AI agents."""

from .client import AxonClient, AxonClientSync
from .constants import (
    CHAIN_NAMES,
    DEFAULT_DEADLINE_SECONDS,
    EIP712_DOMAIN_NAME,
    EIP712_DOMAIN_VERSION,
    EXECUTE_INTENT_TYPEHASH,
    EXPLORER_ADDR,
    EXPLORER_TX,
    NATIVE_ETH,
    PAYMENT_INTENT_TYPEHASH,
    RELAYER_URL,
    SUPPORTED_CHAIN_IDS,
    SWAP_INTENT_TYPEHASH,
    USDC,
    WINDOW_ONE_DAY,
    WINDOW_ONE_HOUR,
    WINDOW_ONE_WEEK,
    WINDOW_THIRTY_DAYS,
    Chain,
    PaymentErrorCode,
    RelayerAPI,
)
from .signer import encode_ref, sign_execute_intent, sign_payment, sign_swap_intent
from .tokens import (
    KNOWN_TOKENS,
    Token,
    get_known_tokens_for_chain,
    get_token_symbol_by_address,
    resolve_token,
)
from .amounts import parse_amount, resolve_token_decimals
from .types import (
    AxonClientConfig,
    DestinationCheckResult,
    ExecuteInput,
    ExecuteIntent,
    PayInput,
    PaymentIntent,
    PaymentResult,
    PaymentStatus,
    RebalanceTokensResult,
    SwapInput,
    SwapIntent,
    TosStatus,
    VaultInfo,
)

__version__ = "0.1.2"

__all__ = [
    # Client
    "AxonClient",
    "AxonClientSync",
    # Constants
    "Chain",
    "NATIVE_ETH",
    "USDC",
    "CHAIN_NAMES",
    "EXPLORER_TX",
    "EXPLORER_ADDR",
    "SUPPORTED_CHAIN_IDS",
    "DEFAULT_DEADLINE_SECONDS",
    "WINDOW_ONE_HOUR",
    "WINDOW_ONE_DAY",
    "WINDOW_ONE_WEEK",
    "WINDOW_THIRTY_DAYS",
    "PAYMENT_INTENT_TYPEHASH",
    "EXECUTE_INTENT_TYPEHASH",
    "SWAP_INTENT_TYPEHASH",
    "EIP712_DOMAIN_NAME",
    "EIP712_DOMAIN_VERSION",
    "PaymentErrorCode",
    "RelayerAPI",
    "RELAYER_URL",
    # Signing
    "sign_payment",
    "sign_execute_intent",
    "sign_swap_intent",
    "encode_ref",
    # Tokens
    "Token",
    "KNOWN_TOKENS",
    "get_known_tokens_for_chain",
    "get_token_symbol_by_address",
    "resolve_token",
    # Amounts
    "parse_amount",
    "resolve_token_decimals",
    # Types
    "PaymentIntent",
    "ExecuteIntent",
    "SwapIntent",
    "PayInput",
    "ExecuteInput",
    "SwapInput",
    "PaymentResult",
    "PaymentStatus",
    "AxonClientConfig",
    "VaultInfo",
    "DestinationCheckResult",
    "RebalanceTokensResult",
    "TosStatus",
]
