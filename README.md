# axonfi

Python SDK for [Axon](https://axonfi.xyz) — treasury and payment infrastructure for autonomous AI agents.

Axon lets bot operators deploy non-custodial vaults, register bot public keys, define spending policies, and let their bots make gasless payments — without bots ever touching private keys or gas.

## Installation

```bash
pip install axonfi
```

## Quick Start

### Option 1: Keystore file + passphrase (recommended)

When you register a bot on the [Axon dashboard](https://app.axonfi.xyz), it generates a keystore JSON file. This is the safest way to load a bot key — the private key stays encrypted on disk and only lives in memory while the bot runs.

```python
import json
from eth_account import Account
from axonfi import AxonClient, Chain

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
    token="USDC",
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

result = await client.pay(to="0x...", token="USDC", amount=5)
```

### Synchronous Usage (LangChain, CrewAI)

Both options work with the sync client too — just swap `AxonClient` for `AxonClientSync`:

```python
from axonfi import AxonClientSync, Chain

client = AxonClientSync(
    vault_address="0x...",
    chain_id=Chain.BaseSepolia,
    bot_private_key="0x...",
)

result = client.pay(to="0x...", token="USDC", amount=5)
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
