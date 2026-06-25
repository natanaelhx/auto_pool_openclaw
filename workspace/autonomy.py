import json
import os
from dataclasses import asdict
from datetime import datetime, timezone
from typing import Dict, List

from adapters.defillama import fetch_pools
from adapters.market_data import pair_market_metrics
from audit import run_audit
from engines.scoring import rank_pools
from executor import execute_guarded
from planner import build_execution_plan
from state.store import append_decision, load_positions
from watcher import review_positions
from wizard import CONFIG_PATH, load_config


AUTO_DECISIONS_PATH = os.path.join(os.path.dirname(CONFIG_PATH), "auto_pools_decisions.json")

DEFAULT_AUTONOMY = {
    "enabled": False,
    "profile": "conservador",
    "capital_usd": 1000.0,
    "allocation_pct": 0.08,
    "limit": 10,
    "chain": "all",
    "market_data": False,
    "min_score": 70.0,
    "max_open_positions": 3,
    "daily_budget_usd": 250.0,
    "open_if_clear": False,
}

SIMULATION_ADVISORY_REASONS = {
    "execution-disabled",
    "missing-signer",
    "missing-signer-ref",
    "local-private-key-signer-disabled",
}


def _truthy(value: str) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "y", "on"}


def _float_env(name: str, default: float, minimum: float, maximum: float) -> float:
    raw = os.getenv(name, "").strip()
    if not raw:
        return default
    try:
        value = float(raw)
    except ValueError:
        return default
    return max(minimum, min(maximum, value))


def _int_env(name: str, default: int, minimum: int, maximum: int) -> int:
    raw = os.getenv(name, "").strip()
    if not raw:
        return default
    try:
        value = int(raw)
    except ValueError:
        return default
    return max(minimum, min(maximum, value))


def _load_autonomy_config(overrides: Dict = None) -> Dict:
    stored = load_config()
    config = dict(DEFAULT_AUTONOMY)
    config.update({key: value for key, value in stored.items() if key in config})
    config.update(
        {
            "enabled": _truthy(os.getenv("AUTO_POOLS_AUTONOMY_ENABLE", str(config["enabled"]))),
            "profile": os.getenv("AUTO_POOLS_DEFAULT_PROFILE", str(config["profile"])).strip() or config["profile"],
            "capital_usd": _float_env("AUTO_POOLS_CAPITAL_USD", float(config["capital_usd"]), 1.0, 1_000_000_000.0),
            "allocation_pct": _float_env("AUTO_POOLS_ALLOCATION_PCT", float(config["allocation_pct"]), 0.001, 0.30),
            "limit": _int_env("AUTO_POOLS_LIMIT", int(config["limit"]), 1, 50),
            "chain": os.getenv("AUTO_POOLS_CHAIN", str(config["chain"])).strip().lower() or config["chain"],
            "market_data": _truthy(os.getenv("AUTO_POOLS_MARKET_DATA", str(config["market_data"]))),
            "min_score": _float_env("AUTO_POOLS_MIN_SCORE", float(config["min_score"]), 0.0, 100.0),
            "max_open_positions": _int_env(
                "AUTO_POOLS_MAX_OPEN_POSITIONS", int(config["max_open_positions"]), 0, 50
            ),
            "daily_budget_usd": _float_env("AUTO_POOLS_DAILY_BUDGET_USD", float(config["daily_budget_usd"]), 0.0, 1_000_000.0),
            "open_if_clear": _truthy(os.getenv("AUTO_POOLS_OPEN_IF_CLEAR", str(config["open_if_clear"]))),
        }
    )
    if overrides:
        config.update({key: value for key, value in overrides.items() if value is not None})
    config["allocation_pct"] = max(0.001, min(float(config["allocation_pct"]), 0.30))
    config["limit"] = max(1, min(int(config["limit"]), 50))
    config["max_open_positions"] = max(0, int(config["max_open_positions"]))
    config["daily_budget_usd"] = max(0.0, float(config["daily_budget_usd"]))
    config["min_score"] = max(0.0, min(float(config["min_score"]), 100.0))
    return config


def _open_positions_count() -> int:
    positions = load_positions().get("positions", [])
    return len([item for item in positions if str(item.get("status", "")).startswith("open")])


def _today_allocated_usd(path: str = AUTO_DECISIONS_PATH) -> float:
    if not os.path.exists(path):
        return 0.0
    today = datetime.now(timezone.utc).date().isoformat()
    try:
        with open(path, "r", encoding="utf-8") as handle:
            data = json.load(handle)
    except (json.JSONDecodeError, FileNotFoundError):
        return 0.0
    total = 0.0
    for decision in data.get("decisions", []):
        if not str(decision.get("created_at", "")).startswith(today):
            continue
        if decision.get("decision") != "open-simulated":
            continue
        total += float(decision.get("allocation_usd", 0.0) or 0.0)
    return round(total, 2)


def _market_metrics_for(pools: List) -> Dict:
    metrics_by_pool = {}
    for pool in pools:
        metrics = pair_market_metrics(pool.assets)
        if metrics:
            metrics_by_pool[pool.pool] = metrics
    return metrics_by_pool


def run_autonomy_cycle(overrides: Dict = None) -> Dict:
    config = _load_autonomy_config(overrides)
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    audit = run_audit(root)
    watch = review_positions()
    blocked = []
    advisory = []

    if not config["enabled"]:
        blocked.append("autonomy-disabled")
    if audit["status"] != "pass":
        blocked.append("audit-failed")

    open_positions = _open_positions_count()
    if open_positions >= config["max_open_positions"]:
        blocked.append("max-open-positions-reached")

    pools = fetch_pools(limit=max(config["limit"], 25), chain=config["chain"])
    metrics = _market_metrics_for(pools[: max(config["limit"], 25)]) if config["market_data"] else {}
    ranked = rank_pools(pools, config["profile"], config["limit"], metrics)
    best = next((item for item in ranked if item.decision != "bloqueado"), ranked[0] if ranked else None)

    plan = None
    receipt = None
    decision = "blocked"
    allocation_usd = 0.0

    if not best:
        blocked.append("no-pool-candidates")
    else:
        allocation_usd = round(float(config["capital_usd"]) * float(config["allocation_pct"]), 2)
        if best.score < config["min_score"]:
            blocked.append("score-below-autonomy-minimum")
        today_allocated = _today_allocated_usd()
        if today_allocated + allocation_usd > config["daily_budget_usd"]:
            blocked.append("daily-budget-exceeded")
        plan = build_execution_plan(best, float(config["capital_usd"]), float(config["allocation_pct"]))
        for reason in plan.guardrails.blocked_reasons:
            if reason in SIMULATION_ADVISORY_REASONS:
                advisory.append(reason)
            else:
                blocked.append(reason)

    hard_blocked = sorted(set(blocked))
    can_open = config["enabled"] and config["open_if_clear"] and not hard_blocked and plan is not None
    if can_open:
        receipt = execute_guarded(plan, "open", confirm=True)
        decision = "open-simulated" if receipt.status == "simulated" else "blocked"
        advisory = sorted(set(advisory + receipt.blocked_reasons))
    elif best:
        decision = "candidate-held"

    record = {
        "mode": "auto",
        "decision": decision,
        "profile": config["profile"],
        "chain": config["chain"],
        "pool": best.pool.pool if best else None,
        "protocol": best.pool.protocol if best else None,
        "score": best.score if best else 0.0,
        "allocation_usd": allocation_usd if decision == "open-simulated" else 0.0,
        "blocked_reasons": hard_blocked,
        "advisory_reasons": sorted(set(advisory)),
    }
    append_decision(record)

    return {
        "mode": "auto",
        "config": config,
        "decision": decision,
        "blocked_reasons": hard_blocked,
        "advisory_reasons": sorted(set(advisory)),
        "audit": audit,
        "watch": watch,
        "open_positions": open_positions,
        "best": asdict(best) if best else None,
        "plan": asdict(plan) if plan else None,
        "receipt": asdict(receipt) if receipt else None,
        "state_path": "workspace/state/auto_pools_decisions.json",
        "security": {
            "broadcasted": False,
            "tx_hash": None,
            "private_key_in_output": False,
            "autonomy_requires_env_enable": True,
        },
    }
