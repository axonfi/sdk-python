"""x402 (HTTP 402 Payment Required) protocol utilities."""

from __future__ import annotations

import base64
import json
from dataclasses import dataclass
from typing import Any

from .constants import USDC


@dataclass
class X402Resource:
    """Resource descriptor from the x402 PAYMENT-REQUIRED header."""

    url: str
    description: str | None = None
    mime_type: str | None = None


@dataclass
class X402PaymentOption:
    """A single payment option from the accepts array."""

    pay_to: str
    amount: str
    asset: str
    network: str
    scheme: str | None = None
    extra: dict[str, Any] | None = None


@dataclass
class X402PaymentRequired:
    """Parsed x402 PAYMENT-REQUIRED response."""

    x402_version: int
    resource: X402Resource
    accepts: list[X402PaymentOption]


@dataclass
class X402HandleResult:
    """Result of handle_payment_required."""

    payment_signature: str
    selected_option: X402PaymentOption
    funding_result: dict[str, Any]


def parse_payment_required(header_value: str) -> X402PaymentRequired:
    """Parse the PAYMENT-REQUIRED header value (base64 JSON or plain JSON)."""
    try:
        decoded = base64.b64decode(header_value).decode("utf-8")
    except Exception:
        decoded = header_value

    parsed = json.loads(decoded)

    accepts = parsed.get("accepts")
    if not accepts or not isinstance(accepts, list) or len(accepts) == 0:
        raise ValueError("x402: no payment options in PAYMENT-REQUIRED header")

    resource_raw = parsed.get("resource")
    if not resource_raw:
        raise ValueError("x402: missing resource in PAYMENT-REQUIRED header")

    resource = X402Resource(
        url=resource_raw["url"],
        description=resource_raw.get("description"),
        mime_type=resource_raw.get("mimeType"),
    )

    options = [
        X402PaymentOption(
            pay_to=opt["payTo"],
            amount=opt["amount"],
            asset=opt["asset"],
            network=opt["network"],
            scheme=opt.get("scheme"),
            extra=opt.get("extra"),
        )
        for opt in accepts
    ]

    return X402PaymentRequired(
        x402_version=parsed.get("x402Version", 1),
        resource=resource,
        accepts=options,
    )


def parse_chain_id(network: str) -> int:
    """Parse a CAIP-2 network identifier to a numeric chain ID.

    Example: parse_chain_id("eip155:8453") -> 8453
    """
    parts = network.split(":")
    if len(parts) != 2 or parts[0] != "eip155":
        raise ValueError(f'x402: unsupported network format "{network}" (expected "eip155:<chainId>")')
    try:
        return int(parts[1])
    except ValueError:
        raise ValueError(f'x402: invalid chain ID in network "{network}"')


def find_matching_option(
    accepts: list[X402PaymentOption],
    chain_id: int,
) -> X402PaymentOption | None:
    """Find a payment option matching the bot's chain ID.

    Prefers USDC options (EIP-3009 path — gasless for bot).
    """
    matching: list[X402PaymentOption] = []

    for option in accepts:
        try:
            option_chain_id = parse_chain_id(option.network)
            if option_chain_id == chain_id:
                matching.append(option)
        except ValueError:
            continue

    if not matching:
        return None

    # Prefer USDC
    usdc_address = USDC.get(chain_id, "").lower()
    if usdc_address:
        for opt in matching:
            if opt.asset.lower() == usdc_address:
                return opt

    return matching[0]


def extract_x402_metadata(
    parsed: X402PaymentRequired,
    selected_option: X402PaymentOption,
) -> dict[str, Any]:
    """Extract metadata fields from a parsed x402 header for payment enrichment.

    Returns a dict with keys: resource_url, memo, recipient_label, metadata.
    """
    metadata: dict[str, str] = {}

    if parsed.x402_version is not None:
        metadata["x402_version"] = str(parsed.x402_version)
    if selected_option.scheme:
        metadata["x402_scheme"] = selected_option.scheme
    if parsed.resource.mime_type:
        metadata["x402_mime_type"] = parsed.resource.mime_type
    if selected_option.pay_to:
        metadata["x402_merchant"] = selected_option.pay_to
    if parsed.resource.description:
        metadata["x402_resource_description"] = parsed.resource.description

    recipient_label = None
    if selected_option.pay_to:
        recipient_label = f"{selected_option.pay_to[:6]}...{selected_option.pay_to[-4:]}"

    return {
        "resource_url": parsed.resource.url,
        "memo": parsed.resource.description,
        "recipient_label": recipient_label,
        "metadata": metadata,
    }


def format_payment_signature(payload: dict[str, Any]) -> str:
    """Format a payment signature payload for the PAYMENT-SIGNATURE header.

    Returns base64-encoded JSON.
    """
    return base64.b64encode(json.dumps(payload).encode("utf-8")).decode("utf-8")
