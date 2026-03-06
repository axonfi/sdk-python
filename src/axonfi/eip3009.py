"""EIP-3009 TransferWithAuthorization signing for USDC."""

from __future__ import annotations

import os

from eth_account import Account

from .constants import USDC

# Per-chain EIP-712 domain parameters for USDC's EIP-3009 implementation.
USDC_EIP712_DOMAIN: dict[int, dict[str, str]] = {
    8453: {"name": "USD Coin", "version": "2"},  # Base mainnet
    84532: {"name": "USDC", "version": "2"},  # Base Sepolia
    42161: {"name": "USD Coin", "version": "2"},  # Arbitrum One
    421614: {"name": "USDC", "version": "2"},  # Arbitrum Sepolia
}

_TRANSFER_WITH_AUTHORIZATION_TYPES = {
    "TransferWithAuthorization": [
        {"name": "from", "type": "address"},
        {"name": "to", "type": "address"},
        {"name": "value", "type": "uint256"},
        {"name": "validAfter", "type": "uint256"},
        {"name": "validBefore", "type": "uint256"},
        {"name": "nonce", "type": "bytes32"},
    ],
}


def random_nonce() -> str:
    """Generate a random bytes32 nonce for EIP-3009.

    Returns a 0x-prefixed 64-character hex string.
    """
    return "0x" + os.urandom(32).hex()


def _to_bytes32(hex_str: str) -> bytes:
    """Convert a 0x-prefixed hex string to 32 bytes."""
    clean = hex_str[2:] if hex_str.startswith("0x") else hex_str
    return bytes.fromhex(clean)


def sign_transfer_with_authorization(
    private_key: str,
    chain_id: int,
    *,
    from_address: str,
    to: str,
    value: int,
    valid_after: int = 0,
    valid_before: int = 0,
    nonce: str | None = None,
) -> str:
    """Sign an EIP-3009 TransferWithAuthorization for USDC.

    Args:
        private_key: Signer's private key (must match from_address).
        chain_id: Chain ID (determines USDC domain name/version).
        from_address: Token holder (sender).
        to: Recipient of the transfer.
        value: Amount in token base units (USDC: 6 decimals).
        valid_after: Unix timestamp — transfer invalid before this time. Usually 0.
        valid_before: Unix timestamp — transfer invalid after this time.
        nonce: Random bytes32 nonce. Auto-generated if omitted.

    Returns:
        EIP-712 signature as 0x-prefixed hex string.
    """
    domain_config = USDC_EIP712_DOMAIN.get(chain_id)
    if not domain_config:
        raise ValueError(f"EIP-3009 not configured for chain {chain_id}")

    usdc_address = USDC.get(chain_id)
    if not usdc_address:
        raise ValueError(f"USDC address not known for chain {chain_id}")

    if nonce is None:
        nonce = random_nonce()

    domain = {
        "name": domain_config["name"],
        "version": domain_config["version"],
        "chainId": chain_id,
        "verifyingContract": usdc_address,
    }

    message = {
        "from": from_address,
        "to": to,
        "value": value,
        "validAfter": valid_after,
        "validBefore": valid_before,
        "nonce": _to_bytes32(nonce),
    }

    signed = Account.sign_typed_data(
        private_key,
        domain,
        _TRANSFER_WITH_AUTHORIZATION_TYPES,
        message,
    )
    h = signed.signature.hex()
    return h if h.startswith("0x") else "0x" + h
