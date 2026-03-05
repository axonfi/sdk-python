"""Tests for AxonClient — constructor and intent building."""

import pytest

from axonfi.client import AxonClient

TEST_PRIVATE_KEY = "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80"
TEST_VAULT = "0x1234567890abcdef1234567890abcdef12345678"
TEST_CHAIN_ID = 84532


def test_bot_address_derived():
    client = AxonClient(
        vault_address=TEST_VAULT,
        chain_id=TEST_CHAIN_ID,
        bot_private_key=TEST_PRIVATE_KEY,
    )
    # Hardhat account #0
    assert client.bot_address.lower() == "0xf39fd6e51aad88f6f4ce6ab8827279cfffb92266"


def test_build_payment_intent():
    client = AxonClient(
        vault_address=TEST_VAULT,
        chain_id=TEST_CHAIN_ID,
        bot_private_key=TEST_PRIVATE_KEY,
    )
    intent = client._build_payment_intent(
        __import__("axonfi.types", fromlist=["PayInput"]).PayInput(
            to="0x000000000000000000000000000000000000dEaD",
            token="USDC",
            amount=5.0,
            memo="test",
        )
    )
    assert intent.bot.lower() == client.bot_address.lower()
    assert intent.amount == 5_000_000  # 5 USDC in base units
    assert intent.token == "0x036CbD53842c5426634e7929541eC2318f3dCF7e"  # Base Sepolia USDC


def test_zero_address_rejected():
    client = AxonClient(
        vault_address=TEST_VAULT,
        chain_id=TEST_CHAIN_ID,
        bot_private_key=TEST_PRIVATE_KEY,
    )
    with pytest.raises(ValueError, match="zero address"):
        client._build_payment_intent(
            __import__("axonfi.types", fromlist=["PayInput"]).PayInput(
                to="0x0000000000000000000000000000000000000000",
                token="USDC",
                amount=5.0,
            )
        )
