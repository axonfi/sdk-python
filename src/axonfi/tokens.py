"""Token registry — single source of truth for known tokens across all chains."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class Token(str, Enum):
    USDC = "USDC"
    USDT = "USDT"
    DAI = "DAI"
    WETH = "WETH"
    WBTC = "WBTC"
    cbBTC = "cbBTC"
    cbETH = "cbETH"
    wstETH = "wstETH"
    rETH = "rETH"
    LINK = "LINK"
    UNI = "UNI"
    AAVE = "AAVE"
    COMP = "COMP"
    CRV = "CRV"
    SNX = "SNX"
    ARB = "ARB"
    AERO = "AERO"
    GMX = "GMX"


@dataclass(frozen=True)
class KnownToken:
    symbol: str
    name: str
    decimals: int
    addresses: dict[int, str] = field(default_factory=dict)


# Chain IDs: 8453=Base, 84532=Base Sepolia, 42161=Arbitrum One, 421614=Arbitrum Sepolia
KNOWN_TOKENS: dict[str, KnownToken] = {
    "USDC": KnownToken("USDC", "USD Coin", 6, {
        8453: "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
        84532: "0x036CbD53842c5426634e7929541eC2318f3dCF7e",
        42161: "0xaf88d065e77c8cC2239327C5EDb3A432268e5831",
        421614: "0x75faf114eafb1BDbe2F0316DF893fd58CE46AA4d",
    }),
    "USDT": KnownToken("USDT", "Tether USD", 6, {
        8453: "0xfde4C96c8593536E31F229EA8f37b2ADa2699bb2",
        84532: "0x323e78f944A9a1FcF3a10efcC5319DBb0bB6e673",
        42161: "0xFd086bC7CD5C481DCC9C85ebE478A1C0b69FCbb9",
    }),
    "DAI": KnownToken("DAI", "Dai Stablecoin", 18, {
        8453: "0x50c5725949A6F0c72E6C4a641F24049A917DB0Cb",
        84532: "0x819ffecd4e64f193e959944bcd57eedc7755e17a",
        42161: "0xDA10009cBd5D07dd0CeCc66161FC93D7c9000da1",
    }),
    "WETH": KnownToken("WETH", "Wrapped Ether", 18, {
        8453: "0x4200000000000000000000000000000000000006",
        84532: "0x4200000000000000000000000000000000000006",
        42161: "0x82aF49447D8a07e3bd95BD0d56f35241523fBab1",
        421614: "0x82aF49447D8a07e3bd95BD0d56f35241523fBab1",
    }),
    "WBTC": KnownToken("WBTC", "Wrapped BTC", 8, {
        8453: "0x0555E30da8f98308EdB960aa94C0Db47230d2B9c",
        42161: "0x2f2a2543B76A4166549F7aaB2e75Bef0aefC5B0f",
    }),
    "cbBTC": KnownToken("cbBTC", "Coinbase Wrapped BTC", 8, {
        8453: "0xcbB7C0000aB88B473b1f5aFd9ef808440eed33Bf",
        42161: "0xcbB7C0000aB88B473b1f5aFd9ef808440eed33Bf",
    }),
    "cbETH": KnownToken("cbETH", "Coinbase Staked ETH", 18, {
        8453: "0x2Ae3F1Ec7F1F5012CFEab0185bfc7aa3cf0DEc22",
        42161: "0x1DEBd73E752bEaF79865Fd6446b0c970EaE7732f",
    }),
    "wstETH": KnownToken("wstETH", "Lido Wrapped stETH", 18, {
        8453: "0xc1CBa3fCea344f92D9239c08C0568f6F2F0ee452",
        42161: "0x5979D7b546E38E414F7E9822514be443A4800529",
    }),
    "rETH": KnownToken("rETH", "Rocket Pool ETH", 18, {
        42161: "0xEC70Dcb4A1EFa46b8F2D97C310C9c4790ba5ffA8",
    }),
    "LINK": KnownToken("LINK", "Chainlink", 18, {
        8453: "0x88Fb150BDc53A65fe94Dea0c9BA0a6dAf8C6e196",
        84532: "0xE4aB69C077896252FAFBD49EFD26B5D171A32410",
        42161: "0xf97f4df75117a78c1A5a0DBb814Af92458539FB4",
    }),
    "UNI": KnownToken("UNI", "Uniswap", 18, {
        8453: "0xc3De830EA07524a0761646a6a4e4be0e114a3C83",
        42161: "0xFa7F8980b0f1E64A2062791cc3b0871572f1F7f0",
    }),
    "AAVE": KnownToken("AAVE", "Aave", 18, {
        8453: "0x63706e401c06ac8513145b7687A14804d17f814b",
        42161: "0xba5DdD1f9d7F570dc94a51479a000E3BCE967196",
    }),
    "COMP": KnownToken("COMP", "Compound", 18, {
        8453: "0x9e1028F5F1D5eDE59748FFceE5532509976840E0",
        42161: "0x354A6dA3fcde098F8389cad84b0182725c6C91dE",
    }),
    "CRV": KnownToken("CRV", "Curve DAO", 18, {
        8453: "0x8Ee73c484A26e0A5df2Ee2a4960B789967dd0415",
        42161: "0x11cDb42B0EB46D95f990BeDD4695A6e3fA034978",
    }),
    "SNX": KnownToken("SNX", "Synthetix", 18, {
        8453: "0x22e6966B799c4D5B13BE962E1D117b56327FDa66",
    }),
    "ARB": KnownToken("ARB", "Arbitrum", 18, {
        42161: "0x912CE59144191C1204E64559FE8253a0e49E6548",
    }),
    "AERO": KnownToken("AERO", "Aerodrome", 18, {
        8453: "0x940181a94A35A4569E4529A3CDfB74e38FD98631",
    }),
    "GMX": KnownToken("GMX", "GMX", 18, {
        42161: "0xfc5A1A6EB076a2C7aD06eD22C90d7E710E35ad0a",
    }),
}

# Pre-built reverse lookup: lowercase address → symbol
_address_to_symbol: dict[str, str] = {}
for _token in KNOWN_TOKENS.values():
    for _addr in _token.addresses.values():
        _address_to_symbol[_addr.lower()] = _token.symbol


def get_known_tokens_for_chain(chain_id: int) -> list[tuple[KnownToken, str]]:
    """All known tokens available on a specific chain. Returns (token, address) pairs."""
    result = []
    for token in KNOWN_TOKENS.values():
        addr = token.addresses.get(chain_id)
        if addr:
            result.append((token, addr))
    return result


def get_token_symbol_by_address(address: str) -> str | None:
    """Reverse-lookup: address → symbol (case-insensitive). Returns None if unknown."""
    return _address_to_symbol.get(address.lower())


def resolve_token(token: str, chain_id: int) -> str:
    """Resolve a Token symbol to its on-chain address for a given chain.

    If an address (0x...) is passed, it is returned as-is.
    Raises ValueError if the symbol has no address on the given chain.
    """
    if isinstance(token, str) and token.startswith("0x"):
        if token == "0x0000000000000000000000000000000000000000":
            raise ValueError("Token address cannot be the zero address")
        return token

    entry = KNOWN_TOKENS.get(token)
    if not entry:
        raise ValueError(f"Unknown token symbol: {token}")

    addr = entry.addresses.get(chain_id)
    if not addr:
        raise ValueError(f"Token {token} is not available on chain {chain_id}")

    return addr
