"""Tests for EIP-712 signing — must produce valid signatures matching TS SDK behavior."""

import re

from eth_account import Account

from axonfi.signer import encode_ref, sign_execute_intent, sign_payment, sign_swap_intent
from axonfi.types import ExecuteIntent, PaymentIntent, SwapIntent
from web3 import Web3

# Deterministic test key — NOT a real key, for testing only
TEST_PRIVATE_KEY = "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80"
TEST_ACCOUNT = Account.from_key(TEST_PRIVATE_KEY)
TEST_VAULT = "0x1234567890abcdef1234567890abcdef12345678"
TEST_CHAIN_ID = 84532

DEADLINE = 1_700_000_000  # Fixed deadline for deterministic tests


# ---------------------------------------------------------------------------
# encode_ref
# ---------------------------------------------------------------------------


def test_encode_ref_returns_keccak256():
    memo = "API call #1234 — weather data"
    expected = "0x" + Web3.keccak(text=memo).hex()
    assert encode_ref(memo) == expected


def test_encode_ref_hex_format():
    result = encode_ref("hello")
    assert re.match(r"^0x[0-9a-f]{64}$", result)


def test_encode_ref_different_inputs():
    assert encode_ref("hello") != encode_ref("world")


def test_encode_ref_consistent():
    assert encode_ref("test") == encode_ref("test")


# ---------------------------------------------------------------------------
# sign_payment
# ---------------------------------------------------------------------------


def test_sign_payment_valid_signature():
    intent = PaymentIntent(
        bot=TEST_ACCOUNT.address,
        to="0x000000000000000000000000000000000000dEaD",
        token="0x036CbD53842c5426634e7929541eC2318f3dCF7e",
        amount=1_000_000,
        deadline=DEADLINE,
        ref=encode_ref("test payment"),
    )
    sig = sign_payment(TEST_PRIVATE_KEY, TEST_VAULT, TEST_CHAIN_ID, intent)
    # Should be a hex string (with or without 0x prefix), 130 hex chars = 65 bytes
    clean = sig.replace("0x", "")
    assert len(clean) == 130
    assert re.match(r"^[0-9a-fA-F]{130}$", clean)


def test_sign_payment_deterministic():
    intent = PaymentIntent(
        bot=TEST_ACCOUNT.address,
        to="0x000000000000000000000000000000000000dEaD",
        token="0x036CbD53842c5426634e7929541eC2318f3dCF7e",
        amount=1_000_000,
        deadline=DEADLINE,
        ref=encode_ref("test payment"),
    )
    sig1 = sign_payment(TEST_PRIVATE_KEY, TEST_VAULT, TEST_CHAIN_ID, intent)
    sig2 = sign_payment(TEST_PRIVATE_KEY, TEST_VAULT, TEST_CHAIN_ID, intent)
    assert sig1 == sig2


# ---------------------------------------------------------------------------
# sign_execute_intent
# ---------------------------------------------------------------------------


def test_sign_execute_intent_valid():
    intent = ExecuteIntent(
        bot=TEST_ACCOUNT.address,
        protocol="0x000000000000000000000000000000000000bEEF",
        calldata_hash=Web3.keccak(hexstr="0x1234").hex(),
        token="0x036CbD53842c5426634e7929541eC2318f3dCF7e",
        amount=500_000,
        deadline=DEADLINE,
        ref=encode_ref("test execute"),
    )
    sig = sign_execute_intent(TEST_PRIVATE_KEY, TEST_VAULT, TEST_CHAIN_ID, intent)
    clean = sig.replace("0x", "")
    assert len(clean) == 130


# ---------------------------------------------------------------------------
# sign_swap_intent
# ---------------------------------------------------------------------------


def test_sign_swap_intent_valid():
    intent = SwapIntent(
        bot=TEST_ACCOUNT.address,
        to_token="0x036CbD53842c5426634e7929541eC2318f3dCF7e",
        min_to_amount=900_000,
        from_token="0x000000000000000000000000000000000000dEaD",
        max_from_amount=1_000_000,
        deadline=DEADLINE,
        ref=encode_ref("test swap"),
    )
    sig = sign_swap_intent(TEST_PRIVATE_KEY, TEST_VAULT, TEST_CHAIN_ID, intent)
    clean = sig.replace("0x", "")
    assert len(clean) == 130
