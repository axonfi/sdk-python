"""Chain enums, USDC addresses, EIP-712 constants, error codes, and relayer API paths."""

from enum import IntEnum

from web3 import Web3

# ============================================================================
# EIP-712 type hashes
# ============================================================================

PAYMENT_INTENT_TYPEHASH: str = (
    "0x"
    + Web3.keccak(
        text="PaymentIntent(address bot,address to,address token,uint256 amount,uint256 deadline,bytes32 ref)"
    ).hex()
)

EXECUTE_INTENT_TYPEHASH: str = (
    "0x"
    + Web3.keccak(
        text="ExecuteIntent(address bot,address protocol,bytes32 calldataHash,"
        "address[] tokens,uint256[] amounts,uint256 value,uint256 deadline,bytes32 ref)"
    ).hex()
)

SWAP_INTENT_TYPEHASH: str = (
    "0x"
    + Web3.keccak(
        text="SwapIntent(address bot,address toToken,uint256 minToAmount,"
        "address fromToken,uint256 maxFromAmount,uint256 deadline,bytes32 ref)"
    ).hex()
)

EIP712_DOMAIN_NAME = "AxonVault"
EIP712_DOMAIN_VERSION = "1"

# ============================================================================
# Native ETH sentinel
# ============================================================================

NATIVE_ETH: str = "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE"

# ============================================================================
# USDC addresses per chain
# ============================================================================

USDC: dict[int, str] = {
    8453: "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",  # Base mainnet
    84532: "0x036CbD53842c5426634e7929541eC2318f3dCF7e",  # Base Sepolia
    42161: "0xaf88d065e77c8cC2239327C5EDb3A432268e5831",  # Arbitrum One
    421614: "0x75faf114eafb1BDbe2F0316DF893fd58CE46AA4d",  # Arbitrum Sepolia
}

# ============================================================================
# Chain enum & supported chain IDs
# ============================================================================


class Chain(IntEnum):
    Base = 8453
    BaseSepolia = 84532
    Arbitrum = 42161
    ArbitrumSepolia = 421614


SUPPORTED_CHAIN_IDS: tuple[int, ...] = (8453, 84532, 42161, 421614)

# ============================================================================
# Chain metadata
# ============================================================================

CHAIN_NAMES: dict[int, str] = {
    Chain.Base: "Base",
    Chain.BaseSepolia: "Base Sepolia",
    Chain.Arbitrum: "Arbitrum One",
    Chain.ArbitrumSepolia: "Arbitrum Sepolia",
    10: "Optimism",
    11155420: "OP Sepolia",
    137: "Polygon",
    80002: "Polygon Amoy",
}

EXPLORER_TX: dict[int, str] = {
    Chain.Base: "https://basescan.org/tx/",
    Chain.BaseSepolia: "https://sepolia.basescan.org/tx/",
    Chain.Arbitrum: "https://arbiscan.io/tx/",
    Chain.ArbitrumSepolia: "https://sepolia.arbiscan.io/tx/",
    10: "https://optimistic.etherscan.io/tx/",
    11155420: "https://sepolia-optimism.etherscan.io/tx/",
    137: "https://polygonscan.com/tx/",
    80002: "https://amoy.polygonscan.com/tx/",
}

EXPLORER_ADDR: dict[int, str] = {
    Chain.Base: "https://basescan.org/address/",
    Chain.BaseSepolia: "https://sepolia.basescan.org/address/",
    Chain.Arbitrum: "https://arbiscan.io/address/",
    Chain.ArbitrumSepolia: "https://sepolia.arbiscan.io/address/",
    10: "https://optimistic.etherscan.io/address/",
    11155420: "https://sepolia-optimism.etherscan.io/address/",
    137: "https://polygonscan.com/address/",
    80002: "https://amoy.polygonscan.com/address/",
}

# ============================================================================
# Time constants (seconds)
# ============================================================================

DEFAULT_DEADLINE_SECONDS = 300  # 5 minutes

WINDOW_ONE_HOUR = 3600
WINDOW_THREE_HOURS = 10800
WINDOW_ONE_DAY = 86400
WINDOW_ONE_WEEK = 604800
WINDOW_THIRTY_DAYS = 2592000

# Only these window values are accepted on-chain. Arbitrary durations revert.
ALLOWED_WINDOWS: frozenset[int] = frozenset(
    {
        WINDOW_ONE_HOUR,
        WINDOW_THREE_HOURS,
        WINDOW_ONE_DAY,
        WINDOW_ONE_WEEK,
        WINDOW_THIRTY_DAYS,
    }
)

# ============================================================================
# Payment rejection error codes
# ============================================================================


class PaymentErrorCode:
    SELF_PAYMENT = "SELF_PAYMENT"
    ZERO_ADDRESS = "ZERO_ADDRESS"
    ZERO_AMOUNT = "ZERO_AMOUNT"
    INSUFFICIENT_BALANCE = "INSUFFICIENT_BALANCE"
    INVALID_SIGNATURE = "INVALID_SIGNATURE"
    DEADLINE_EXPIRED = "DEADLINE_EXPIRED"
    BOT_PAUSED = "BOT_PAUSED"
    BOT_NOT_ACTIVE = "BOT_NOT_ACTIVE"
    BLACKLISTED = "BLACKLISTED"
    SPENDING_LIMIT_EXCEEDED = "SPENDING_LIMIT_EXCEEDED"
    TX_COUNT_EXCEEDED = "TX_COUNT_EXCEEDED"
    MAX_PER_TX_EXCEEDED = "MAX_PER_TX_EXCEEDED"
    VAULT_AGGREGATE_EXCEEDED = "VAULT_AGGREGATE_EXCEEDED"
    SIMULATION_FAILED = "SIMULATION_FAILED"
    PENDING_REVIEW = "PENDING_REVIEW"
    RELAYER_OUT_OF_GAS = "RELAYER_OUT_OF_GAS"
    SUBMISSION_FAILED = "SUBMISSION_FAILED"
    DESTINATION_NOT_WHITELISTED = "DESTINATION_NOT_WHITELISTED"
    INVALID_VAULT = "INVALID_VAULT"
    REBALANCE_TOKEN_NOT_ALLOWED = "REBALANCE_TOKEN_NOT_ALLOWED"
    MAX_REBALANCE_AMOUNT_EXCEEDED = "MAX_REBALANCE_AMOUNT_EXCEEDED"
    INTERNAL_ERROR = "INTERNAL_ERROR"


# ============================================================================
# Relayer API paths
# ============================================================================

RELAYER_URL = "https://relay.axonfi.xyz"


class RelayerAPI:
    PAYMENTS = "/v1/payments"
    EXECUTE = "/v1/execute"
    SWAP = "/v1/swap"
    TOS_ACCEPT = "/v1/tos/accept"

    @staticmethod
    def payment(request_id: str) -> str:
        return f"/v1/payments/{request_id}"

    @staticmethod
    def execute(request_id: str) -> str:
        return f"/v1/execute/{request_id}"

    @staticmethod
    def swap(request_id: str) -> str:
        return f"/v1/swap/{request_id}"

    @staticmethod
    def vault_balance(vault: str, token: str, chain_id: int) -> str:
        return f"/v1/vault/{vault}/balance/{token}?chainId={chain_id}"

    @staticmethod
    def vault_balances(vault: str, chain_id: int) -> str:
        return f"/v1/vault/{vault}/balances"

    @staticmethod
    def vault_info(vault: str, chain_id: int) -> str:
        return f"/v1/vault/{vault}/info?chainId={chain_id}"

    @staticmethod
    def bot_status(vault: str, bot: str, chain_id: int) -> str:
        return f"/v1/vault/{vault}/bot/{bot}/status?chainId={chain_id}"

    @staticmethod
    def destination_check(vault: str, bot: str, destination: str, chain_id: int) -> str:
        return f"/v1/vault/{vault}/bot/{bot}/destination/{destination}?chainId={chain_id}"

    @staticmethod
    def protocol_check(vault: str, protocol: str, chain_id: int) -> str:
        return f"/v1/vault/{vault}/protocol/{protocol}?chainId={chain_id}"

    @staticmethod
    def rebalance_tokens(vault: str, chain_id: int) -> str:
        return f"/v1/vault/{vault}/rebalance-tokens?chainId={chain_id}"

    @staticmethod
    def rebalance_token_check(vault: str, token: str, chain_id: int) -> str:
        return f"/v1/vault/{vault}/rebalance-token/{token}?chainId={chain_id}"

    @staticmethod
    def vault_value(vault: str, chain_id: int) -> str:
        return f"/v1/vault/{vault}/value?chainId={chain_id}"

    @staticmethod
    def tos_status(wallet: str) -> str:
        return f"/v1/tos/status?wallet={wallet}"
