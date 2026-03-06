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
| `execute(protocol, call_data, token, amount, ...)` | DeFi protocol interaction (see [below](#defi-protocol-execution)) |
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

## DeFi Protocol Execution

Use `execute()` to interact with DeFi protocols (Uniswap, Aave, GMX, Ostium, etc.) from your vault. The relayer handles token approvals, execution, and revocation atomically.

```python
result = await client.execute(
    protocol="0xUniswapRouter",
    call_data="0x...",
    token=Token.USDC,
    amount=100,
)
```

### When the approval target differs from the call target

In simple cases (Uniswap, Aave), the contract you call is the same contract that pulls your tokens — `execute()` handles this automatically in a single call.

But many DeFi protocols split these into two contracts:

- **Call target** (`protocol`) — the contract you send the transaction to (e.g., Ostium's `Trading` for `openTrade()`)
- **Approval target** — the contract that actually calls `transferFrom()` to pull tokens from your vault (e.g., Ostium's `TradingStorage`)

When these differ, you need a **two-step pattern**: first give the approval target a persistent token allowance, then call the action.

**Example — Ostium perpetual futures:**

Ostium's `openTrade()` lives on the Trading contract, but collateral gets pulled by TradingStorage. The vault must approve TradingStorage, not Trading.

```python
USDC = "0x..."                      # USDC on your chain
OSTIUM_TRADING = "0x..."            # calls openTrade()
OSTIUM_TRADING_STORAGE = "0x..."    # pulls USDC via transferFrom()

# Step 1: Persistent approval (one-time) — call approve() on the token contract
# This tells USDC to let TradingStorage spend from the vault.
result = await client.execute(
    protocol=USDC,                         # call target: the token contract itself
    call_data=encode_approve(OSTIUM_TRADING_STORAGE, MAX_UINT256),
    token=USDC,
    amount=0,                              # no token spend, just setting an allowance
    protocol_name="USDC Approve",
)

# Step 2: Open trade — call the action contract
result = await client.execute(
    protocol=OSTIUM_TRADING,               # call target: the Trading contract
    call_data=encode_open_trade(...),
    token=USDC,
    amount=50_000_000,                     # 50 USDC — passed for dashboard/AI visibility
    protocol_name="Ostium",
)
```

**Vault setup (owner, one-time):** Two contracts must be approved via `approveProtocol()`:
1. **USDC** (the token contract) — because the vault calls `approve()` on it directly
2. **Trading** — because the vault calls `openTrade()` on it

TradingStorage does *not* need to be approved — it's just an argument to `approve()`, not a contract the vault calls.

> **Note:** Common tokens (USDC, USDT, WETH, etc.) are pre-approved globally via the Axon registry as default tokens, so you typically only need to approve the DeFi protocol contract itself. You only need to approve a token if it's uncommon and not in the registry defaults.

> **Testnet note:** If the protocol uses a custom token that isn't on Uniswap (e.g., Ostium's testnet USDC), set the bot's `maxPerTxAmount` to `0` to skip TWAP oracle pricing.

This pattern applies to any protocol where the approval target differs from the call target (GMX, some lending protocols, etc.). See the [Ostium perps trader example](https://github.com/axonfi/examples/tree/main/python/ostium-perps-trader) for a complete working implementation.

### `ContractNotApproved` error

If `execute()` reverts with `ContractNotApproved`, the `protocol` address you're calling isn't approved. Two possible causes:

1. **The DeFi protocol contract isn't approved** — the vault owner must call `approveProtocol(address)` on the vault for the protocol contract (e.g., Uniswap Router, Ostium Trading, Lido stETH).
2. **The token contract isn't approved** — when doing a token approval (Step 1 above), the token must either be approved on the vault via `approveProtocol(tokenAddress)` or be a registry default token. Common tokens (USDC, USDT, WETH, DAI, etc.) are pre-approved globally by Axon, but uncommon tokens (e.g., stETH, aUSDC, cTokens) may need manual approval.

**Example — Lido staking/unstaking:** To unstake stETH, Lido's withdrawal contract calls `transferFrom()` to pull stETH from your vault. You need:
- `approveProtocol(stETH)` — so the vault can call `approve()` on the stETH token to grant Lido an allowance
- `approveProtocol(lidoWithdrawalQueue)` — so the vault can call `requestWithdrawals()` on Lido

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

### Mainnet

| Chain        | ID    | Status      |
| ------------ | ----- | ----------- |
| Base         | 8453  | Coming soon |
| Arbitrum One | 42161 | Coming soon |

### Testnet

| Chain            | ID     | Status |
| ---------------- | ------ | ------ |
| Base Sepolia     | 84532  | Live   |
| Arbitrum Sepolia | 421614 | Live   |

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
