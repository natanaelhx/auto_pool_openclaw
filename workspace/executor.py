import hashlib
import os
from dataclasses import asdict
from typing import List, Optional

from models.schemas import ExecutionReceipt, PoolExecutionPlan
from state.store import find_position, upsert_position


EXECUTION_ACTIONS = {"open", "close", "collect", "rebalance"}


def _truthy(value: str) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "y", "on"}


def _position_id(plan: PoolExecutionPlan) -> str:
    raw = "|".join([plan.chain, plan.protocol, plan.pool, ",".join(plan.assets), plan.profile])
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def _steps_for_action(plan: PoolExecutionPlan, action: str) -> List[str]:
    if action == "open":
        return plan.entry_steps
    if action == "close":
        return plan.exit_steps
    if action == "collect":
        if plan.chain == "solana":
            return [
                "Ler posicao LP/NFT/conta Whirlpool/Raydium.",
                "Simular collect fees via RPC/SDK.",
                "Aplicar minimo recebido por token.",
                "Bloquear broadcast nesta release.",
            ]
        return [
            "Ler posicao NFT/LP e fees acumuladas.",
            "Simular collect/claim no position manager/router.",
            "Aplicar deadline e limite de gas.",
            "Bloquear broadcast nesta release.",
        ]
    return plan.rebalance_steps


def execute_guarded(
    plan: PoolExecutionPlan,
    action: str,
    confirm: bool = False,
    position_id: Optional[str] = None,
) -> ExecutionReceipt:
    if action not in EXECUTION_ACTIONS:
        raise ValueError(f"Acao invalida: {action}")

    requested_enabled = _truthy(os.getenv("AUTO_POOLS_EXECUTION_ENABLE", "false"))
    signer_ref = os.getenv("AUTO_POOLS_SIGNER_REF", "").strip()
    blocked = set(plan.guardrails.blocked_reasons)

    if not requested_enabled:
        blocked.add("execution-disabled")
    if requested_enabled and not signer_ref:
        blocked.add("missing-signer-ref")
    if not confirm:
        blocked.add("missing-explicit-confirmation")
    if plan.guardrails.dry_run_only:
        blocked.add("dry-run-only-release")

    existing_position = None
    resolved_position_id = position_id or _position_id(plan)
    if action in {"close", "collect", "rebalance"}:
        existing_position = find_position(resolved_position_id)
        if not existing_position:
            blocked.add("position-not-found")

    hard_blocks = {
        reason
        for reason in blocked
        if reason in {"missing-explicit-confirmation", "pool-score-bloqueado", "position-not-found"}
        or reason.startswith("Par ")
    }
    status = "blocked" if hard_blocks else "simulated"
    steps = _steps_for_action(plan, action)
    notes = [
        "Execucao guardada concluida sem assinatura e sem broadcast.",
        "Esta release persiste somente estado simulado para auditoria local.",
        "Para execucao real futura, usar signer externo via secret manager e simulacao on-chain obrigatoria.",
    ]

    if status == "simulated":
        if action == "open":
            upsert_position(
                {
                    "position_id": resolved_position_id,
                    "status": "open-simulated",
                    "chain": plan.chain,
                    "protocol": plan.protocol,
                    "pool": plan.pool,
                    "assets": plan.assets,
                    "profile": plan.profile,
                    "allocation_usd": plan.allocation_usd,
                    "adapter_family": plan.adapter_family,
                    "plan": asdict(plan),
                }
            )
        elif action == "close" and existing_position:
            existing_position["status"] = "closed-simulated"
            upsert_position(existing_position)
        elif action == "collect" and existing_position:
            existing_position["last_collect_status"] = "collect-simulated"
            upsert_position(existing_position)
        elif action == "rebalance" and existing_position:
            existing_position["last_rebalance_status"] = "rebalance-simulated"
            existing_position["plan"] = asdict(plan)
            upsert_position(existing_position)

    return ExecutionReceipt(
        action=action,
        status=status,
        chain=plan.chain,
        protocol=plan.protocol,
        pool=plan.pool,
        adapter_family=plan.adapter_family,
        position_id=resolved_position_id,
        simulated=True,
        broadcasted=False,
        tx_hash=None,
        guardrails=plan.guardrails,
        blocked_reasons=sorted(blocked),
        executed_steps=steps,
        state_path="workspace/state/auto_pools_positions.json",
        notes=notes,
    )
