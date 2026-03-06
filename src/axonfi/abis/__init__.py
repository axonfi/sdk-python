"""Minimal ABIs for on-chain vault operations."""

import importlib.resources as _res
import json


def _load(name: str) -> list:
    ref = _res.files(__package__).joinpath(name)
    return json.loads(ref.read_text(encoding="utf-8"))

AXON_VAULT_ABI = _load("AxonVault.json")
AXON_VAULT_FACTORY_ABI = _load("AxonVaultFactory.json")
ERC20_ABI = _load("ERC20.json")
