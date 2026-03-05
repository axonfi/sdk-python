"""Tests for constants module."""

import re

from axonfi.constants import (
    CHAIN_NAMES,
    DEFAULT_DEADLINE_SECONDS,
    EXECUTE_INTENT_TYPEHASH,
    EXPLORER_ADDR,
    EXPLORER_TX,
    NATIVE_ETH,
    PAYMENT_INTENT_TYPEHASH,
    SUPPORTED_CHAIN_IDS,
    SWAP_INTENT_TYPEHASH,
    USDC,
    WINDOW_ONE_DAY,
    WINDOW_ONE_HOUR,
    WINDOW_ONE_WEEK,
    WINDOW_THIRTY_DAYS,
    Chain,
    PaymentErrorCode,
)


def test_chain_enum():
    assert Chain.Base == 8453
    assert Chain.BaseSepolia == 84532
    assert Chain.Arbitrum == 42161
    assert Chain.ArbitrumSepolia == 421614


def test_supported_chain_ids():
    assert 8453 in SUPPORTED_CHAIN_IDS
    assert 84532 in SUPPORTED_CHAIN_IDS
    assert 42161 in SUPPORTED_CHAIN_IDS
    assert 421614 in SUPPORTED_CHAIN_IDS


def test_usdc_addresses():
    for chain_id in SUPPORTED_CHAIN_IDS:
        addr = USDC[chain_id]
        assert addr.startswith("0x")
        assert len(addr) == 42


def test_native_eth():
    assert NATIVE_ETH == "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE"


def test_window_constants():
    assert WINDOW_ONE_HOUR == 3600
    assert WINDOW_ONE_DAY == 86400
    assert WINDOW_ONE_WEEK == 604800
    assert WINDOW_THIRTY_DAYS == 2592000


def test_default_deadline():
    assert DEFAULT_DEADLINE_SECONDS == 300


def test_typehashes_are_hex():
    hex_pattern = re.compile(r"^0x[0-9a-f]{64}$")
    assert hex_pattern.match(PAYMENT_INTENT_TYPEHASH)
    assert hex_pattern.match(EXECUTE_INTENT_TYPEHASH)
    assert hex_pattern.match(SWAP_INTENT_TYPEHASH)


def test_typehashes_are_distinct():
    assert PAYMENT_INTENT_TYPEHASH != EXECUTE_INTENT_TYPEHASH
    assert PAYMENT_INTENT_TYPEHASH != SWAP_INTENT_TYPEHASH
    assert EXECUTE_INTENT_TYPEHASH != SWAP_INTENT_TYPEHASH


def test_chain_names():
    assert CHAIN_NAMES[Chain.Base] == "Base"
    assert CHAIN_NAMES[Chain.BaseSepolia] == "Base Sepolia"


def test_explorer_urls():
    for chain_id in SUPPORTED_CHAIN_IDS:
        assert chain_id in EXPLORER_TX
        assert chain_id in EXPLORER_ADDR
        assert EXPLORER_TX[chain_id].startswith("https://")
        assert EXPLORER_ADDR[chain_id].startswith("https://")


def test_error_codes():
    assert PaymentErrorCode.SELF_PAYMENT == "SELF_PAYMENT"
    assert PaymentErrorCode.INSUFFICIENT_BALANCE == "INSUFFICIENT_BALANCE"
    assert PaymentErrorCode.PENDING_REVIEW == "PENDING_REVIEW"
