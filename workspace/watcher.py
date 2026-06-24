from typing import Dict, List

from state.store import load_positions


def _plan_alerts(plan: Dict) -> List[str]:
    alerts = []
    guardrails = plan.get("guardrails") or {}
    range_suggestion = plan.get("range_suggestion") or {}
    blocked = guardrails.get("blocked_reasons") or []
    if blocked:
        alerts.append("guardrails-blocked")
    if range_suggestion.get("confidence") == "baixa":
        alerts.append("low-range-confidence")
    if float(guardrails.get("max_drawdown_pct") or 0.0) >= 10.0:
        alerts.append("drawdown-watch")
    if float(guardrails.get("max_il_pct") or 0.0) >= 3.0:
        alerts.append("impermanent-loss-watch")
    return alerts


def review_positions(state_path: str = None) -> Dict:
    data = load_positions(state_path) if state_path else load_positions()
    reviews = []
    for position in data.get("positions", []):
        status = str(position.get("status", ""))
        if not status.startswith("open"):
            continue
        plan = position.get("plan") or {}
        alerts = _plan_alerts(plan)
        reviews.append(
            {
                "position_id": position.get("position_id"),
                "chain": position.get("chain"),
                "protocol": position.get("protocol"),
                "pool": position.get("pool"),
                "status": status,
                "alerts": alerts,
                "action": "review" if alerts else "hold",
            }
        )
    return {
        "mode": "watch",
        "positions_reviewed": len(reviews),
        "alerts_count": sum(len(item["alerts"]) for item in reviews),
        "reviews": reviews,
        "security": {
            "broadcasted": False,
            "signer_required": False,
            "dry_run_only": True,
        },
    }
