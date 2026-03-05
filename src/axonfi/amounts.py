"""Human-friendly amount conversion utilities."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation

from .tokens import KNOWN_TOKENS, get_token_symbol_by_address


def resolve_token_decimals(token: str) -> int:
    """Look up decimals for a token by symbol or address.

    Args:
        token: A known symbol ('USDC'), Token enum value, or address ('0x...')

    Returns:
        The number of decimals for the token.

    Raises:
        ValueError: If the token is unknown.
    """
    if isinstance(token, str) and token.startswith("0x"):
        symbol = get_token_symbol_by_address(token)
        if not symbol:
            raise ValueError(
                f"Unknown token address {token} — cannot determine decimals. "
                "Use an int amount instead, or pass a known token symbol."
            )
        return KNOWN_TOKENS[symbol].decimals

    entry = KNOWN_TOKENS.get(token)
    if not entry:
        known = ", ".join(KNOWN_TOKENS.keys())
        raise ValueError(
            f'Unknown token symbol "{token}" — cannot determine decimals. '
            f"Use an int amount instead, or use a known symbol ({known})."
        )
    return entry.decimals


def parse_amount(amount: int | float | str, token: str) -> int:
    """Convert a human-friendly amount to raw base units (int).

    - **int** → passed through as-is (already in base units)
    - **float** → converted via Decimal for precision
    - **str** → parsed via Decimal

    Args:
        amount: The amount as int (raw), float (human), or str (human).
        token: Token identifier used to look up decimals (symbol or address).

    Returns:
        The amount in token base units as int.

    Raises:
        ValueError: If the amount has more decimal places than the token supports.
    """
    if isinstance(amount, int) and not isinstance(amount, bool):
        return amount

    decimals = resolve_token_decimals(token)

    # Convert to string for Decimal parsing
    if isinstance(amount, float):
        s = str(amount)
    else:
        s = str(amount)

    # Validate precision
    if "." in s:
        decimal_places = len(s) - s.index(".") - 1
        if decimal_places > decimals:
            token_label = "this token" if token.startswith("0x") else token
            raise ValueError(
                f'Amount "{s}" has {decimal_places} decimal places, '
                f"but {token_label} only supports {decimals}. "
                "Truncate or round your amount."
            )

    try:
        d = Decimal(s)
    except InvalidOperation:
        raise ValueError(f"Invalid amount: {s}")

    return int(d * Decimal(10**decimals))
