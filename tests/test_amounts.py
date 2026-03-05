"""Tests for amount parsing — mirrors TS SDK test vectors."""

import pytest

from axonfi.amounts import parse_amount, resolve_token_decimals
from axonfi.tokens import Token


# ---------------------------------------------------------------------------
# resolve_token_decimals
# ---------------------------------------------------------------------------


def test_resolve_by_symbol():
    assert resolve_token_decimals("USDC") == 6
    assert resolve_token_decimals("WETH") == 18
    assert resolve_token_decimals("WBTC") == 8


def test_resolve_by_token_enum():
    assert resolve_token_decimals(Token.USDC) == 6
    assert resolve_token_decimals(Token.DAI) == 18


def test_resolve_by_known_address():
    # Base USDC
    assert resolve_token_decimals("0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913") == 6
    # Arbitrum WETH
    assert resolve_token_decimals("0x82aF49447D8a07e3bd95BD0d56f35241523fBab1") == 18


def test_resolve_unknown_address():
    with pytest.raises(ValueError, match="Unknown token address"):
        resolve_token_decimals("0x0000000000000000000000000000000000000001")


def test_resolve_unknown_symbol():
    with pytest.raises(ValueError, match="Unknown token symbol"):
        resolve_token_decimals("NOTREAL")


# ---------------------------------------------------------------------------
# parse_amount
# ---------------------------------------------------------------------------


def test_int_passthrough():
    assert parse_amount(5_000_000, "USDC") == 5_000_000
    assert parse_amount(0, "WETH") == 0


def test_float_usdc():
    assert parse_amount(5.0, "USDC") == 5_000_000
    assert parse_amount(5.2, "USDC") == 5_200_000
    assert parse_amount(0.01, "USDC") == 10_000


def test_float_weth():
    assert parse_amount(1.0, "WETH") == 1_000_000_000_000_000_000
    assert parse_amount(0.001, "WETH") == 1_000_000_000_000_000


def test_float_wbtc():
    assert parse_amount(1.0, "WBTC") == 100_000_000
    assert parse_amount(0.5, Token.WBTC) == 50_000_000


def test_string_amounts():
    assert parse_amount("5.2", "USDC") == 5_200_000
    assert parse_amount("100", "USDC") == 100_000_000
    assert parse_amount("0.123456", "USDC") == 123_456


def test_token_enum():
    assert parse_amount(10.0, Token.USDC) == 10_000_000
    assert parse_amount("0.5", Token.WETH) == 500_000_000_000_000_000


def test_known_address():
    usdc_base = "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"
    assert parse_amount(5.0, usdc_base) == 5_000_000


def test_zero():
    assert parse_amount(0, "USDC") == 0
    assert parse_amount("0", "USDC") == 0
    assert parse_amount("0.0", "USDC") == 0


def test_excess_precision_throws():
    with pytest.raises(ValueError, match="7 decimal places"):
        parse_amount("5.1234567", "USDC")
    with pytest.raises(ValueError, match="21 decimal places"):
        parse_amount("1.123456789012345678901", "WETH")


def test_unknown_address_with_human_amount():
    with pytest.raises(ValueError, match="Unknown token address"):
        parse_amount(5.0, "0x0000000000000000000000000000000000000001")


def test_int_passthrough_unknown_address():
    assert parse_amount(5_000_000, "0x0000000000000000000000000000000000000001") == 5_000_000
