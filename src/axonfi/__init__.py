"""axonfi — Treasury and payment infrastructure for autonomous AI agents."""

from .amounts import parse_amount, resolve_token_decimals
from .client import AxonClient, AxonClientSync
from .constants import (
    ALLOWED_WINDOWS,
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
    WINDOW_THREE_HOURS,
    Chain,
    PaymentErrorCode,
    RelayerAPI,
)
from .eip3009 import (
    USDC_EIP712_DOMAIN,
    random_nonce,
    sign_transfer_with_authorization,
)
from .permit2 import (
    PERMIT2_ADDRESS,
    X402_PROXY_ADDRESS,
    random_permit2_nonce,
    sign_permit2_witness_transfer,
)
from .signer import encode_ref, sign_execute_intent, sign_payment, sign_swap_intent
from .tokens import (
    DEFAULT_APPROVED_TOKENS,
    KNOWN_TOKENS,
    Token,
    get_default_approved_tokens,
    get_known_tokens_for_chain,
    get_token_symbol_by_address,
    resolve_token,
)
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
from .vault import (
    BotConfigInput,
    SpendingLimitInput,
    add_bot,
    deploy_vault,
    deposit,
    remove_bot,
    update_bot_config,
)
from .x402 import (
    X402HandleResult,
    X402PaymentOption,
    X402PaymentRequired,
    X402Resource,
    extract_x402_metadata,
    find_matching_option,
    format_payment_signature,
    parse_chain_id,
    parse_payment_required,
)

__version__ = "0.3.2"

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
    "WINDOW_THREE_HOURS",
    "WINDOW_ONE_DAY",
    "WINDOW_ONE_WEEK",
    "WINDOW_THIRTY_DAYS",
    "ALLOWED_WINDOWS",
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
    "DEFAULT_APPROVED_TOKENS",
    "get_default_approved_tokens",
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
    # EIP-3009
    "sign_transfer_with_authorization",
    "random_nonce",
    "USDC_EIP712_DOMAIN",
    # Permit2
    "sign_permit2_witness_transfer",
    "random_permit2_nonce",
    "PERMIT2_ADDRESS",
    "X402_PROXY_ADDRESS",
    # Vault operations
    "deploy_vault",
    "add_bot",
    "update_bot_config",
    "remove_bot",
    "deposit",
    "BotConfigInput",
    "SpendingLimitInput",
    # x402
    "parse_payment_required",
    "parse_chain_id",
    "find_matching_option",
    "extract_x402_metadata",
    "format_payment_signature",
    "X402Resource",
    "X402PaymentOption",
    "X402PaymentRequired",
    "X402HandleResult",
]
