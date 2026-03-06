"""Tests for x402 protocol utilities, EIP-3009, and Permit2 signing."""

import base64
import json

import pytest
from eth_account import Account

from axonfi.constants import USDC
from axonfi.eip3009 import (
    USDC_EIP712_DOMAIN,
    random_nonce,
    sign_transfer_with_authorization,
)
from axonfi.permit2 import (
    PERMIT2_ADDRESS,
    X402_PROXY_ADDRESS,
    random_permit2_nonce,
    sign_permit2_witness_transfer,
)
from axonfi.x402 import (
    extract_x402_metadata,
    find_matching_option,
    format_payment_signature,
    parse_chain_id,
    parse_payment_required,
    X402PaymentOption,
)

BOT_KEY = "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80"
BOT_ADDRESS = Account.from_key(BOT_KEY).address
MERCHANT = "0x70997970C51812dc3A010C7d01b50e0d17dc79C8"
CHAIN_ID = 84532
USDC_ADDRESS = USDC[CHAIN_ID]


def _make_header(overrides=None):
    data = {
        "x402Version": 1,
        "resource": {
            "url": "https://weather-api.example.com/forecast",
            "description": "Premium weather forecast data",
            "mimeType": "application/json",
        },
        "accepts": [
            {
                "payTo": MERCHANT,
                "amount": "1000000",
                "asset": USDC_ADDRESS,
                "network": f"eip155:{CHAIN_ID}",
                "scheme": "exact",
            }
        ],
    }
    if overrides:
        data.update(overrides)
    return base64.b64encode(json.dumps(data).encode()).decode()


# ============================================================================
# Header parsing
# ============================================================================


class TestParsePaymentRequired:
    def test_parses_base64_header(self):
        result = parse_payment_required(_make_header())
        assert result.x402_version == 1
        assert result.resource.url == "https://weather-api.example.com/forecast"
        assert len(result.accepts) == 1
        assert result.accepts[0].pay_to == MERCHANT

    def test_parses_plain_json(self):
        raw = json.dumps(
            {
                "x402Version": 1,
                "resource": {"url": "https://example.com"},
                "accepts": [
                    {
                        "payTo": MERCHANT,
                        "amount": "100",
                        "asset": USDC_ADDRESS,
                        "network": "eip155:84532",
                    }
                ],
            }
        )
        result = parse_payment_required(raw)
        assert result.resource.url == "https://example.com"

    def test_throws_on_missing_accepts(self):
        header = base64.b64encode(
            json.dumps({"resource": {"url": "test"}}).encode()
        ).decode()
        with pytest.raises(ValueError, match="no payment options"):
            parse_payment_required(header)

    def test_throws_on_empty_accepts(self):
        header = base64.b64encode(
            json.dumps({"resource": {"url": "test"}, "accepts": []}).encode()
        ).decode()
        with pytest.raises(ValueError, match="no payment options"):
            parse_payment_required(header)

    def test_throws_on_missing_resource(self):
        header = base64.b64encode(
            json.dumps(
                {
                    "accepts": [
                        {
                            "payTo": MERCHANT,
                            "amount": "100",
                            "asset": USDC_ADDRESS,
                            "network": "eip155:84532",
                        }
                    ]
                }
            ).encode()
        ).decode()
        with pytest.raises(ValueError, match="missing resource"):
            parse_payment_required(header)


# ============================================================================
# CAIP-2 chain ID parsing
# ============================================================================


class TestParseChainId:
    def test_parses_base_mainnet(self):
        assert parse_chain_id("eip155:8453") == 8453

    def test_parses_base_sepolia(self):
        assert parse_chain_id("eip155:84532") == 84532

    def test_parses_arbitrum(self):
        assert parse_chain_id("eip155:42161") == 42161

    def test_throws_on_non_eip155(self):
        with pytest.raises(ValueError, match="unsupported network format"):
            parse_chain_id("solana:mainnet")

    def test_throws_on_invalid_format(self):
        with pytest.raises(ValueError, match="unsupported network format"):
            parse_chain_id("8453")

    def test_throws_on_non_numeric(self):
        with pytest.raises(ValueError, match="invalid chain ID"):
            parse_chain_id("eip155:base")


# ============================================================================
# Chain matching + USDC preference
# ============================================================================


class TestFindMatchingOption:
    def test_returns_usdc_when_available(self):
        weth = "0x4200000000000000000000000000000000000006"
        accepts = [
            X402PaymentOption(
                pay_to=MERCHANT,
                amount="500000000000000",
                asset=weth,
                network="eip155:84532",
                scheme="permit2",
            ),
            X402PaymentOption(
                pay_to=MERCHANT,
                amount="1000000",
                asset=USDC_ADDRESS,
                network="eip155:84532",
                scheme="exact",
            ),
        ]
        result = find_matching_option(accepts, CHAIN_ID)
        assert result is not None
        assert result.asset == USDC_ADDRESS

    def test_falls_back_to_non_usdc(self):
        weth = "0x4200000000000000000000000000000000000006"
        accepts = [
            X402PaymentOption(
                pay_to=MERCHANT,
                amount="500000000000000",
                asset=weth,
                network="eip155:84532",
            ),
        ]
        result = find_matching_option(accepts, CHAIN_ID)
        assert result is not None
        assert result.asset == weth

    def test_returns_none_when_no_match(self):
        accepts = [
            X402PaymentOption(
                pay_to=MERCHANT,
                amount="1000000",
                asset=USDC_ADDRESS,
                network="eip155:8453",
            ),
        ]
        result = find_matching_option(accepts, CHAIN_ID)
        assert result is None


# ============================================================================
# Metadata extraction
# ============================================================================


class TestExtractMetadata:
    def test_extracts_all_fields(self):
        parsed = parse_payment_required(_make_header())
        meta = extract_x402_metadata(parsed, parsed.accepts[0])
        assert meta["resource_url"] == "https://weather-api.example.com/forecast"
        assert meta["memo"] == "Premium weather forecast data"
        assert "0x7099" in meta["recipient_label"]
        assert meta["metadata"]["x402_version"] == "1"
        assert meta["metadata"]["x402_scheme"] == "exact"
        assert meta["metadata"]["x402_mime_type"] == "application/json"
        assert meta["metadata"]["x402_merchant"] == MERCHANT


# ============================================================================
# Header format roundtrip
# ============================================================================


class TestFormatPaymentSignature:
    def test_encodes_as_base64_json(self):
        payload = {"scheme": "exact", "signature": "0xabc"}
        encoded = format_payment_signature(payload)
        decoded = json.loads(base64.b64decode(encoded))
        assert decoded["scheme"] == "exact"
        assert decoded["signature"] == "0xabc"


# ============================================================================
# EIP-3009 signing
# ============================================================================


class TestSignTransferWithAuthorization:
    def test_produces_valid_signature(self):
        sig = sign_transfer_with_authorization(
            BOT_KEY,
            CHAIN_ID,
            from_address=BOT_ADDRESS,
            to=MERCHANT,
            value=1_000_000,
            valid_before=999999999,
        )
        assert sig.startswith("0x")
        assert len(sig) == 132  # 0x + 130 hex chars

    def test_deterministic(self):
        nonce = "0x" + "00" * 31 + "01"
        kwargs = dict(
            from_address=BOT_ADDRESS,
            to=MERCHANT,
            value=1_000_000,
            valid_before=999999999,
            nonce=nonce,
        )
        sig1 = sign_transfer_with_authorization(BOT_KEY, CHAIN_ID, **kwargs)
        sig2 = sign_transfer_with_authorization(BOT_KEY, CHAIN_ID, **kwargs)
        assert sig1 == sig2

    def test_throws_for_unsupported_chain(self):
        with pytest.raises(ValueError, match="not configured"):
            sign_transfer_with_authorization(
                BOT_KEY,
                999999,
                from_address=BOT_ADDRESS,
                to=MERCHANT,
                value=1_000_000,
                valid_before=999999999,
            )


class TestRandomNonce:
    def test_format(self):
        nonce = random_nonce()
        assert nonce.startswith("0x")
        assert len(nonce) == 66

    def test_unique(self):
        nonces = {random_nonce() for _ in range(10)}
        assert len(nonces) == 10


# ============================================================================
# Permit2 signing
# ============================================================================


class TestSignPermit2WitnessTransfer:
    def test_produces_valid_signature(self):
        sig = sign_permit2_witness_transfer(
            BOT_KEY,
            CHAIN_ID,
            token=USDC_ADDRESS,
            amount=1_000_000,
            spender=X402_PROXY_ADDRESS,
            nonce=42,
            deadline=999999999,
            witness_to=MERCHANT,
            witness_requested_amount=1_000_000,
        )
        assert sig.startswith("0x")
        assert len(sig) == 132

    def test_deterministic(self):
        kwargs = dict(
            token=USDC_ADDRESS,
            amount=1_000_000,
            spender=X402_PROXY_ADDRESS,
            nonce=1,
            deadline=999999999,
            witness_to=MERCHANT,
            witness_requested_amount=1_000_000,
        )
        sig1 = sign_permit2_witness_transfer(BOT_KEY, CHAIN_ID, **kwargs)
        sig2 = sign_permit2_witness_transfer(BOT_KEY, CHAIN_ID, **kwargs)
        assert sig1 == sig2


class TestRandomPermit2Nonce:
    def test_returns_int(self):
        nonce = random_permit2_nonce()
        assert isinstance(nonce, int)
        assert nonce >= 0

    def test_unique(self):
        nonces = {random_permit2_nonce() for _ in range(10)}
        assert len(nonces) == 10


# ============================================================================
# Constants
# ============================================================================


class TestConstants:
    def test_permit2_address(self):
        assert PERMIT2_ADDRESS == "0x000000000022D473030F116dDEE9F6B43aC78BA3"

    def test_x402_proxy_address(self):
        assert X402_PROXY_ADDRESS == "0x4020CD856C882D5fb903D99CE35316A085Bb0001"

    def test_usdc_domains(self):
        assert USDC_EIP712_DOMAIN[8453] == {"name": "USD Coin", "version": "2"}
        assert USDC_EIP712_DOMAIN[84532] == {"name": "USDC", "version": "2"}
        assert USDC_EIP712_DOMAIN[42161] == {"name": "USD Coin", "version": "2"}
        assert USDC_EIP712_DOMAIN[421614] == {"name": "USDC", "version": "2"}
