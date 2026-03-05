"""Tests for token registry."""

import pytest

from axonfi.tokens import (
    KNOWN_TOKENS,
    Token,
    get_known_tokens_for_chain,
    get_token_symbol_by_address,
    resolve_token,
)


def test_token_enum():
    assert Token.USDC == "USDC"
    assert Token.WETH == "WETH"
    assert Token.WBTC == "WBTC"


def test_known_tokens_decimals():
    assert KNOWN_TOKENS["USDC"].decimals == 6
    assert KNOWN_TOKENS["WETH"].decimals == 18
    assert KNOWN_TOKENS["WBTC"].decimals == 8
    assert KNOWN_TOKENS["DAI"].decimals == 18


def test_known_tokens_addresses():
    usdc = KNOWN_TOKENS["USDC"]
    assert 8453 in usdc.addresses
    assert 84532 in usdc.addresses
    assert 42161 in usdc.addresses


def test_get_known_tokens_for_chain():
    tokens = get_known_tokens_for_chain(8453)
    symbols = [t.symbol for t, _ in tokens]
    assert "USDC" in symbols
    assert "WETH" in symbols


def test_get_token_symbol_by_address():
    # Base USDC
    assert get_token_symbol_by_address("0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913") == "USDC"
    # Case insensitive
    assert get_token_symbol_by_address("0x833589fcd6edb6e08f4c7c32d4f71b54bda02913") == "USDC"
    # Unknown
    assert get_token_symbol_by_address("0x0000000000000000000000000000000000000001") is None


def test_resolve_token_symbol():
    addr = resolve_token("USDC", 84532)
    assert addr == "0x036CbD53842c5426634e7929541eC2318f3dCF7e"


def test_resolve_token_address_passthrough():
    addr = "0x1234567890abcdef1234567890abcdef12345678"
    assert resolve_token(addr, 84532) == addr


def test_resolve_token_zero_address():
    with pytest.raises(ValueError, match="zero address"):
        resolve_token("0x0000000000000000000000000000000000000000", 84532)


def test_resolve_token_unknown_symbol():
    with pytest.raises(ValueError, match="Unknown token symbol"):
        resolve_token("NOTREAL", 84532)


def test_resolve_token_not_on_chain():
    with pytest.raises(ValueError, match="not available on chain"):
        resolve_token("ARB", 8453)  # ARB only on Arbitrum
