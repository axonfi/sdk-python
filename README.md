# axonfi

Python SDK for [Axon](https://axonfi.xyz) — treasury and payment infrastructure for autonomous AI agents.

Axon lets bot operators deploy non-custodial vaults, register bot public keys, define spending policies, and let their bots make gasless payments — without bots ever touching private keys or gas.

## Installation

```bash
pip install axonfi
```

## Prerequisites

Before using the SDK, you need an Axon vault with a registered bot:

1. **Deploy a vault** — Go to [app.axonfi.xyz](https://app.axonfi.xyz), connect your wallet, and deploy a vault on your target chain. The vault is a non-custodial smart contract — only you (the owner) can withdraw funds.

2. **Fund the vault** — Send USDC (or any ERC-20) to your vault address. Anyone can deposit directly to the contract.

3. **Register a bot** — In the dashboard, go to your vault → Bots → Add Bot. You can either:
   - **Generate a new keypair** (recommended) — the dashboard creates a key and downloads an encrypted keystore JSON file. You set the passphrase.
   - **Bring your own key** — paste an existing public key if you manage keys externally.

4. **Configure policies** — Set per-transaction caps, daily spending limits, velocity windows, and destination whitelists. The bot can only operate within these bounds.

5. **Get the bot key** — Your agent needs the bot's private key to sign payment intents. Use the keystore file + passphrase (recommended) or export the raw private key for quick testing.

The vault owner's wallet stays secure — the bot key can only sign intents within the policies you configure, and can be revoked instantly from the dashboard.

## Quick Start

### Option 1: Keystore file + passphrase (recommended)

When you register a bot on the [Axon dashboard](https://app.axonfi.xyz), it generates a keystore JSON file. This is the safest way to load a bot key — the private key stays encrypted on disk and only lives in memory while the bot runs.

```python
import json
from eth_account import Account
from axonfi import AxonClient, Chain, Token

# Load encrypted keystore file (downloaded from the dashboard)
with open("bot-keystore.json") as f:
    keystore = json.load(f)

# Decrypt with your passphrase (set when you registered the bot)
private_key = Account.decrypt(keystore, "your-passphrase")

client = AxonClient(
    vault_address="0x...",
    chain_id=Chain.BaseSepolia,
    bot_private_key="0x" + private_key.hex(),
)

# Pay 5 USDC — SDK handles decimals automatically
result = await client.pay(
    to="0x...recipient...",
    token=Token.USDC,
    amount=5,
    memo="API call #1234 — weather data",
)

print(result.status, result.tx_hash)
```

### Option 2: Raw private key (for quick testing)

```python
from axonfi import AxonClient, Chain

client = AxonClient(
    vault_address="0x...",
    chain_id=Chain.BaseSepolia,
    bot_private_key="0x...",  # From env var or .env file — never hardcode
)

result = await client.pay(to="0x...", token=Token.USDC, amount=5)
```

### Synchronous Usage (LangChain, CrewAI)

Both options work with the sync client too — just swap `AxonClient` for `AxonClientSync`:

```python
from axonfi import AxonClientSync, Chain, Token

client = AxonClientSync(
    vault_address="0x...",
    chain_id=Chain.BaseSepolia,
    bot_private_key="0x...",
)

result = client.pay(to="0x...", token=Token.USDC, amount=5)
```

## Features

- **EIP-712 signing** for all intent types (payment, execute, swap)
- **Async + sync** clients — use `AxonClient` (async) or `AxonClientSync`
- **Human-friendly amounts** — pass `5` or `"5.2"` instead of `5000000`
- **Token registry** — use `"USDC"` or `Token.USDC` instead of addresses
- **Full relayer API** — pay, execute DeFi protocols, swap, poll, check balances

## API Reference

### AxonClient / AxonClientSync

| Method | Description |
|--------|-------------|
| `pay(to, token, amount, ...)` | Create, sign, and submit a payment |
| `execute(protocol, call_data, token, amount, ...)` | DeFi protocol interaction |
| `swap(to_token, min_to_amount, ...)` | In-vault token swap |
| `get_balance(token)` | Vault balance for a token |
| `get_balances(tokens)` | Multiple balances in one call |
| `is_active()` | Whether this bot is active |
| `is_paused()` | Whether the vault is paused |
| `get_vault_info()` | Owner, operator, paused, version |
| `can_pay_to(destination)` | Destination whitelist/blacklist check |
| `poll(request_id)` | Poll async payment status |

### Signing Utilities

```python
from axonfi import sign_payment, encode_ref, PaymentIntent

ref = encode_ref("my memo")
intent = PaymentIntent(bot="0x...", to="0x...", token="0x...", amount=1000000, deadline=1700000000, ref=ref)
signature = sign_payment(private_key, vault_address, chain_id, intent)
```

### Constants

```python
from axonfi import Chain, USDC, Token, KNOWN_TOKENS

chain_id = Chain.BaseSepolia       # 84532
usdc_addr = USDC[chain_id]        # 0x036CbD...
decimals = KNOWN_TOKENS["USDC"].decimals  # 6
```

## HTTP 402 Paywalls (x402)

The SDK includes utilities for handling [x402](https://www.x402.org/) paywalls — APIs that charge per-request via HTTP 402 Payment Required.

```python
import httpx
from axonfi import (
    parse_payment_required,
    find_matching_option,
    extract_x402_metadata,
    format_payment_signature,
)

response = await httpx.AsyncClient().get("https://api.example.com/data")

if response.status_code == 402:
    # 1. Parse the PAYMENT-REQUIRED header
    header = response.headers["payment-required"]
    parsed = parse_payment_required(header)

    # 2. Find a payment option matching your chain
    option = find_matching_option(parsed.accepts, client.chain_id)

    # 3. Fund the bot from the vault
    result = await client.pay(
        to=client.bot_address,
        token=option.asset,
        amount=int(option.amount),
        x402_funding=True,
    )

    # 4. Sign the authorization and retry
    signature_header = format_payment_signature({
        "scheme": "exact",
        "signature": "...",  # EIP-3009 or Permit2 sig
    })

    data = await httpx.AsyncClient().get(
        "https://api.example.com/data",
        headers={"PAYMENT-SIGNATURE": signature_header},
    )
```

The full pipeline applies — spending limits, AI verification, human review — even for 402 payments. Vault owners see every paywall payment in the dashboard with the resource URL, merchant address, and amount.

Supports EIP-3009 (USDC, gasless) and Permit2 (any ERC-20) settlement schemes.

## Supported Chains

| Chain | ID | Status |
|-------|----|--------|
| Base | 8453 | Mainnet |
| Base Sepolia | 84532 | Testnet |
| Arbitrum One | 42161 | Mainnet |
| Arbitrum Sepolia | 421614 | Testnet |

## Links

- [Website](https://axonfi.xyz)
- [Dashboard](https://app.axonfi.xyz)
- [Documentation](https://axonfi.xyz/llms.txt)
- [PyPI — axonfi](https://pypi.org/project/axonfi/)
- [npm — @axonfi/sdk](https://www.npmjs.com/package/@axonfi/sdk) (TypeScript SDK)
- [Smart Contracts](https://github.com/axonfi/contracts)
- [Examples](https://github.com/axonfi/examples)
- [GitHub](https://github.com/axonfi/sdk-python)
- [Twitter/X — @axonfixyz](https://x.com/axonfixyz)
