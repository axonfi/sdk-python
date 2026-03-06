"""Permit2 PermitWitnessTransferFrom signing for any ERC-20."""

from __future__ import annotations

import os

from eth_account import Account

# Canonical Permit2 contract address (same on all EVM chains).
PERMIT2_ADDRESS = "0x000000000022D473030F116dDEE9F6B43aC78BA3"

# x402 facilitator proxy contract address (same on all supported chains).
X402_PROXY_ADDRESS = "0x4020CD856C882D5fb903D99CE35316A085Bb0001"

_PERMIT_WITNESS_TRANSFER_FROM_TYPES = {
    "PermitWitnessTransferFrom": [
        {"name": "permitted", "type": "TokenPermissions"},
        {"name": "spender", "type": "address"},
        {"name": "nonce", "type": "uint256"},
        {"name": "deadline", "type": "uint256"},
        {"name": "witness", "type": "TransferDetails"},
    ],
    "TokenPermissions": [
        {"name": "token", "type": "address"},
        {"name": "amount", "type": "uint256"},
    ],
    "TransferDetails": [
        {"name": "to", "type": "address"},
        {"name": "requestedAmount", "type": "uint256"},
    ],
}


def random_permit2_nonce() -> int:
    """Generate a random uint256 nonce for Permit2."""
    return int.from_bytes(os.urandom(32), "big")


def sign_permit2_witness_transfer(
    private_key: str,
    chain_id: int,
    *,
    token: str,
    amount: int,
    spender: str,
    nonce: int,
    deadline: int,
    witness_to: str,
    witness_requested_amount: int,
) -> str:
    """Sign a Permit2 PermitWitnessTransferFrom for x402.

    Args:
        private_key: Signer's private key (token holder).
        chain_id: Chain ID.
        token: Token contract address.
        amount: Maximum amount the spender can transfer.
        spender: Spender address (the x402 proxy).
        nonce: Unique nonce (random uint256).
        deadline: Unix timestamp — signature invalid after this time.
        witness_to: Recipient address.
        witness_requested_amount: Requested amount.

    Returns:
        EIP-712 signature as 0x-prefixed hex string.
    """
    domain = {
        "name": "Permit2",
        "chainId": chain_id,
        "verifyingContract": PERMIT2_ADDRESS,
    }

    message = {
        "permitted": {"token": token, "amount": amount},
        "spender": spender,
        "nonce": nonce,
        "deadline": deadline,
        "witness": {"to": witness_to, "requestedAmount": witness_requested_amount},
    }

    signed = Account.sign_typed_data(
        private_key,
        domain,
        _PERMIT_WITNESS_TRANSFER_FROM_TYPES,
        message,
    )
    h = signed.signature.hex()
    return h if h.startswith("0x") else "0x" + h
