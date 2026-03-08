"""EIP-712 signing for Axon payment, execute, and swap intents."""

from __future__ import annotations

from eth_account import Account
from web3 import Web3

from .constants import EIP712_DOMAIN_NAME, EIP712_DOMAIN_VERSION
from .types import ExecuteIntent, PaymentIntent, SwapIntent

# EIP-712 type definitions matching Solidity structs exactly.

_PAYMENT_INTENT_TYPES = {
    "PaymentIntent": [
        {"name": "bot", "type": "address"},
        {"name": "to", "type": "address"},
        {"name": "token", "type": "address"},
        {"name": "amount", "type": "uint256"},
        {"name": "deadline", "type": "uint256"},
        {"name": "ref", "type": "bytes32"},
    ],
}

_EXECUTE_INTENT_TYPES = {
    "ExecuteIntent": [
        {"name": "bot", "type": "address"},
        {"name": "protocol", "type": "address"},
        {"name": "calldataHash", "type": "bytes32"},
        {"name": "tokens", "type": "address[]"},
        {"name": "amounts", "type": "uint256[]"},
        {"name": "value", "type": "uint256"},
        {"name": "deadline", "type": "uint256"},
        {"name": "ref", "type": "bytes32"},
    ],
}

_SWAP_INTENT_TYPES = {
    "SwapIntent": [
        {"name": "bot", "type": "address"},
        {"name": "toToken", "type": "address"},
        {"name": "minToAmount", "type": "uint256"},
        {"name": "deadline", "type": "uint256"},
        {"name": "ref", "type": "bytes32"},
    ],
}


def _make_domain(vault_address: str, chain_id: int) -> dict:
    return {
        "name": EIP712_DOMAIN_NAME,
        "version": EIP712_DOMAIN_VERSION,
        "chainId": chain_id,
        "verifyingContract": vault_address,
    }


def _to_bytes32(hex_str: str) -> bytes:
    """Convert a 0x-prefixed hex string to 32 bytes."""
    clean = hex_str[2:] if hex_str.startswith("0x") else hex_str
    return bytes.fromhex(clean)


def _normalize_sig(sig_bytes: bytes) -> str:
    """Return signature as 0x-prefixed hex string."""
    h = sig_bytes.hex()
    return h if h.startswith("0x") else "0x" + h


def sign_payment(
    private_key: str,
    vault_address: str,
    chain_id: int,
    intent: PaymentIntent,
) -> str:
    """Sign a PaymentIntent using EIP-712. Returns 0x-prefixed hex signature."""
    domain = _make_domain(vault_address, chain_id)
    message = {
        "bot": intent.bot,
        "to": intent.to,
        "token": intent.token,
        "amount": intent.amount,
        "deadline": intent.deadline,
        "ref": _to_bytes32(intent.ref),
    }

    signed = Account.sign_typed_data(
        private_key,
        domain,
        _PAYMENT_INTENT_TYPES,
        message,
    )
    return _normalize_sig(signed.signature)


def sign_execute_intent(
    private_key: str,
    vault_address: str,
    chain_id: int,
    intent: ExecuteIntent,
) -> str:
    """Sign an ExecuteIntent using EIP-712. Returns 0x-prefixed hex signature."""
    domain = _make_domain(vault_address, chain_id)
    message = {
        "bot": intent.bot,
        "protocol": intent.protocol,
        "calldataHash": _to_bytes32(intent.calldata_hash),
        "tokens": list(intent.tokens),
        "amounts": list(intent.amounts),
        "value": intent.value,
        "deadline": intent.deadline,
        "ref": _to_bytes32(intent.ref),
    }

    signed = Account.sign_typed_data(
        private_key,
        domain,
        _EXECUTE_INTENT_TYPES,
        message,
    )
    return _normalize_sig(signed.signature)


def sign_swap_intent(
    private_key: str,
    vault_address: str,
    chain_id: int,
    intent: SwapIntent,
) -> str:
    """Sign a SwapIntent using EIP-712. Returns 0x-prefixed hex signature."""
    domain = _make_domain(vault_address, chain_id)
    message = {
        "bot": intent.bot,
        "toToken": intent.to_token,
        "minToAmount": intent.min_to_amount,
        "deadline": intent.deadline,
        "ref": _to_bytes32(intent.ref),
    }

    signed = Account.sign_typed_data(
        private_key,
        domain,
        _SWAP_INTENT_TYPES,
        message,
    )
    return _normalize_sig(signed.signature)


def encode_ref(memo: str) -> str:
    """Derive the on-chain ref bytes32 from a human-readable memo string.

    Returns keccak256 hash as a 0x-prefixed hex string.
    """
    return "0x" + Web3.keccak(text=memo).hex()
