#!/usr/bin/env python3
import argparse
import json
import os
import sys
from dataclasses import asdict

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

from adapters.defillama import fetch_pools
from adapters.market_data import pair_market_metrics
from dry_run import simulate
from engines.scoring import rank_pools
from planner import build_execution_plan


def parse_args():
    parser = argparse.ArgumentParser(description="Auto Pool OpenClaw - scan, ranking, dry-run e plano DeFi.")
    parser.add_argument("--mode", choices=["scan", "rank", "dry-run", "plan", "wizard"], default="rank")
    parser.add_argument("--profile", choices=["conservador", "moderado", "agressivo"], default=os.getenv("AUTO_POOLS_DEFAULT_PROFILE", "conservador"))
    parser.add_argument("--chain", choices=["all", "ethereum", "arbitrum", "base", "optimism", "polygon", "solana"], default="all")
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--capital", type=float, default=1000.0)
    parser.add_argument("--allocation-pct", type=float, default=0.08)
    parser.add_argument("--market-data", action="store_true", help="Usa candles publicos quando disponiveis para lateralizacao.")
    parser.add_argument("--json", action="store_true", help="Retorna JSON bruto.")
    return parser.parse_args()


def output_json(payload):
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def print_summary(scored):
    print("Resumo")
    for index, item in enumerate(scored, 1):
        pool = item.pool
        print(f"{index}. {pool.chain} / {pool.protocol} / {pool.pool}")
        print(f"   Decisao: {item.decision}")
        print(f"   Score: {item.score}/100")
        print(f"   APR: {pool.apr * 100:.2f}% | APR ajustado: {item.risk_adjusted_apr * 100:.2f}%")
        print(f"   TVL: US$ {pool.tvl_usd:,.0f} | Volume 24h: US$ {pool.volume_24h_usd:,.0f}")
        print(f"   Lateralizacao: {item.lateralization_score:.1f}/100 (~{item.lateralization_days_estimate} dias)")
        print(f"   Market data: {item.market_data_source} | Range observado: {item.observed_range_pct * 100:.2f}%")
        print(f"   Drawdown estimado: {item.estimated_drawdown * 100:.2f}% | IL estimado: {item.estimated_il * 100:.2f}%")
        print(f"   Cenario: {item.scenario}")
        if item.blocks:
            print(f"   Bloqueios: {'; '.join(item.blocks)}")
        print()


def main():
    args = parse_args()

    if args.mode == "wizard":
        from wizard import run_analysis

        config = {
            "profile": args.profile,
            "capital_usd": args.capital,
            "allocation_pct": args.allocation_pct,
            "limit": args.limit,
            "wallet_address": os.getenv("AUTO_POOLS_WALLET_ADDRESS", ""),
            "automation_mode": "dry-run",
            "execution_enabled": False,
            "signer_env": "AUTO_POOLS_SIGNER_REF",
        }
        output_json(run_analysis(config))
        return

    pools = fetch_pools(limit=max(args.limit, 25), chain=args.chain)

    if args.mode == "scan":
        payload = [asdict(pool) for pool in pools[: args.limit]]
        if args.json:
            output_json({"mode": "scan", "profile": args.profile, "pools": payload})
        else:
            print(f"Scan concluido: {len(payload)} pools candidatas.")
            for pool in pools[: args.limit]:
                print(f"- {pool.chain} / {pool.protocol} / {pool.pool}: APR {pool.apr * 100:.2f}%, TVL US$ {pool.tvl_usd:,.0f}")
        return

    metrics_by_pool = {}
    if args.market_data:
        for pool in pools[: max(args.limit, 25)]:
            metrics = pair_market_metrics(pool.assets)
            if metrics:
                metrics_by_pool[pool.pool] = metrics

    scored = rank_pools(pools, args.profile, args.limit, metrics_by_pool)

    if args.mode == "rank":
        if args.json:
            output_json({"mode": "rank", "profile": args.profile, "results": [asdict(item) for item in scored]})
        else:
            print_summary(scored)
        return

    best = next((item for item in scored if item.decision != "bloqueado"), scored[0])
    if args.mode == "plan":
        plan = build_execution_plan(best, args.capital, args.allocation_pct)
        if args.json:
            output_json({"mode": "plan", "profile": args.profile, "result": asdict(plan)})
        else:
            print("Plano operacional")
            print(f"Pool: {plan.chain} / {plan.protocol} / {plan.pool}")
            print(f"Adapter: {plan.adapter_family}")
            print(f"Alocacao planejada: US$ {plan.allocation_usd:,.2f}")
            print(f"Execucao habilitada: {plan.guardrails.execution_enabled}")
            print(f"Dry-run only: {plan.guardrails.dry_run_only}")
            print(f"Bloqueios: {'; '.join(plan.guardrails.blocked_reasons) or 'nenhum'}")
            print("Entrada:")
            for step in plan.entry_steps:
                print(f"- {step}")
            print("Saida:")
            for step in plan.exit_steps:
                print(f"- {step}")
        return

    dry_run = simulate(best, args.capital, args.allocation_pct)
    if args.json:
        output_json({"mode": "dry-run", "profile": args.profile, "result": asdict(dry_run)})
    else:
        print("Dry-run")
        print(f"Pool: {best.pool.chain} / {best.pool.protocol} / {best.pool.pool}")
        print(f"Decisao: {best.decision}")
        print(f"Capital: US$ {args.capital:,.2f}")
        print(f"Alocacao simulada: {dry_run.allocation_pct * 100:.2f}% = US$ {dry_run.allocation_usd:,.2f}")
        print(f"Yield anual esperado ajustado: US$ {dry_run.expected_yearly_yield_usd:,.2f}")
        print(f"Lateralizacao: {best.lateralization_score:.1f}/100 (~{best.lateralization_days_estimate} dias)")
        print(f"Market data: {best.market_data_source} | Range observado: {best.observed_range_pct * 100:.2f}%")
        print(f"Perda maxima estimada por drawdown: US$ {dry_run.max_loss_estimate_usd:,.2f}")
        print(f"IL estimado: US$ {dry_run.il_estimate_usd:,.2f}")
        if best.blocks:
            print(f"Bloqueios: {'; '.join(best.blocks)}")


if __name__ == "__main__":
    main()
