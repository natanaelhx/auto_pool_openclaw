import re
from collections import defaultdict
from typing import Dict, List

from state.store import load_positions


EVM_RE = re.compile(r"^0x[a-fA-F0-9]{40}$")
SOLANA_RE = re.compile(r"^[1-9A-HJ-NP-Za-km-z]{32,64}$")


def validate_public_wallet(address: str) -> Dict:
    value = (address or "").strip()
    if not value:
        return {"valid": False, "chain_family": "unknown", "reason": "missing-wallet-address"}
    if EVM_RE.fullmatch(value):
        return {"valid": True, "chain_family": "evm", "reason": ""}
    if SOLANA_RE.fullmatch(value):
        return {"valid": True, "chain_family": "solana", "reason": ""}
    return {"valid": False, "chain_family": "unknown", "reason": "invalid-public-wallet-format"}


def _empty_exposure() -> Dict:
    return {
        "total_simulated_usd": 0.0,
        "by_asset": {},
        "by_chain": {},
        "by_protocol": {},
        "open_positions": [],
    }


def analyze_wallet(address: str, state_path: str = None) -> Dict:
    validation = validate_public_wallet(address)
    exposure = _empty_exposure()
    if not validation["valid"]:
        return {
            "wallet": address or "",
            "validation": validation,
            "exposure": exposure,
            "security": {
                "public_address_only": True,
                "seed_phrase_allowed": False,
                "private_key_allowed": False,
                "onchain_read_only": True,
            },
        }

    data = load_positions(state_path) if state_path else load_positions()
    by_asset = defaultdict(float)
    by_chain = defaultdict(float)
    by_protocol = defaultdict(float)
    open_positions: List[Dict] = []

    for position in data.get("positions", []):
        status = str(position.get("status", ""))
        if not status.startswith("open"):
            continue
        allocation = float(position.get("allocation_usd") or 0.0)
        assets = position.get("assets") or []
        if not assets:
            assets = ["UNKNOWN"]
        per_asset = allocation / max(len(assets), 1)
        for asset in assets:
            by_asset[str(asset)] += per_asset
        by_chain[str(position.get("chain", "unknown"))] += allocation
        by_protocol[str(position.get("protocol", "unknown"))] += allocation
        open_positions.append(
            {
                "position_id": position.get("position_id"),
                "chain": position.get("chain"),
                "protocol": position.get("protocol"),
                "pool": position.get("pool"),
                "allocation_usd": round(allocation, 2),
                "status": status,
            }
        )

    total = sum(by_chain.values())
    exposure = {
        "total_simulated_usd": round(total, 2),
        "by_asset": {key: round(value, 2) for key, value in sorted(by_asset.items())},
        "by_chain": {key: round(value, 2) for key, value in sorted(by_chain.items())},
        "by_protocol": {key: round(value, 2) for key, value in sorted(by_protocol.items())},
        "open_positions": open_positions,
    }
    return {
        "wallet": address,
        "validation": validation,
        "exposure": exposure,
        "security": {
            "public_address_only": True,
            "seed_phrase_allowed": False,
            "private_key_allowed": False,
            "onchain_read_only": True,
        },
    }
