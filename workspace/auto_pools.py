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
from audit import run_audit
from dry_run import simulate
from engines.scoring import rank_pools
from executor import execute_guarded
from ops import build_bridge_plan, build_swap_plan
from planner import build_execution_plan
from wallet import analyze_wallet
from watcher import review_positions


def parse_args():
    parser = argparse.ArgumentParser(description="Auto Pool OpenClaw - scan, ranking, dry-run, plano e execucao guardada DeFi.")
    parser.add_argument("--mode", choices=["scan", "rank", "dry-run", "plan", "execute", "swap", "bridge", "wallet", "watch", "audit", "wizard"], default="rank")
    parser.add_argument("--action", choices=["open", "close", "collect", "rebalance"], default="open", help="Acao usada no modo execute.")
    parser.add_argument("--position-id", default="", help="ID de posicao simulada para close, collect ou rebalance.")
    parser.add_argument("--confirm", action="store_true", help="Confirmacao explicita para execucao guardada. Nao faz broadcast nesta release.")
    parser.add_argument("--profile", choices=["conservador", "moderado", "agressivo"], default=os.getenv("AUTO_POOLS_DEFAULT_PROFILE", "conservador"))
    parser.add_argument("--chain", choices=["all", "ethereum", "arbitrum", "base", "optimism", "polygon", "solana"], default="all")
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--capital", type=float, default=1000.0)
    parser.add_argument("--allocation-pct", type=float, default=0.08)
    parser.add_argument("--market-data", action="store_true", help="Usa candles publicos quando disponiveis para lateralizacao.")
    parser.add_argument("--wallet-address", default=os.getenv("AUTO_POOLS_WALLET_ADDRESS", ""), help="Endereco publico para modo wallet.")
    parser.add_argument("--from-chain", default="", help="Chain de origem para bridge/swap.")
    parser.add_argument("--to-chain", default="", help="Chain de destino para bridge.")
    parser.add_argument("--from-token", default="", help="Token de origem para swap.")
    parser.add_argument("--to-token", default="", help="Token de destino para swap.")
    parser.add_argument("--token", default="", help="Token para bridge.")
    parser.add_argument("--amount-usd", type=float, default=0.0, help="Valor nocional em USD para swap/bridge.")
    parser.add_argument("--slippage-bps", type=int, default=0, help="Slippage maximo solicitado em bps; limitado pelo perfil.")
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
        if item.trend_regime != "unknown":
            print(
                "   Indicadores: "
                f"RSI14 {item.rsi_14:.1f} | ATR14 {item.atr_pct_14 * 100:.2f}% | "
                f"Bollinger {item.bollinger_width_pct * 100:.2f}% | ADX14 {item.adx_14:.1f} | "
                f"Regime {item.trend_regime}"
            )
        if item.range_suggestion:
            print(
                "   Range sugerido: "
                f"{item.range_suggestion.lower_pct * 100:.2f}% a "
                f"+{item.range_suggestion.upper_pct * 100:.2f}% | "
                f"confianca {item.range_suggestion.confidence}"
            )
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

    if args.mode == "wallet":
        payload = analyze_wallet(args.wallet_address)
        if args.json:
            output_json(payload)
        else:
            print("Carteira")
            print(f"Endereco: {payload['wallet'] or 'nao informado'}")
            print(f"Valida: {payload['validation']['valid']} | Familia: {payload['validation']['chain_family']}")
            print(f"Exposicao simulada: US$ {payload['exposure']['total_simulated_usd']:,.2f}")
            print(f"Posicoes abertas simuladas: {len(payload['exposure']['open_positions'])}")
        return

    if args.mode == "watch":
        payload = review_positions()
        if args.json:
            output_json(payload)
        else:
            print("Watcher")
            print(f"Posicoes revisadas: {payload['positions_reviewed']}")
            print(f"Alertas: {payload['alerts_count']}")
            for review in payload["reviews"]:
                print(f"- {review['position_id']} {review['pool']}: {review['action']} ({'; '.join(review['alerts']) or 'sem alertas'})")
        return

    if args.mode == "audit":
        payload = run_audit(os.path.dirname(BASE_DIR))
        if args.json:
            output_json(payload)
        else:
            print("Auditoria")
            print(f"Status: {payload['status']}")
            for check in payload["checks"]:
                print(f"- {check['name']}: {check['status']}")
        return

    if args.mode == "swap":
        chain = args.from_chain or args.chain
        payload = asdict(build_swap_plan(chain, args.from_token, args.to_token, args.amount_usd, args.profile, args.slippage_bps))
        if args.json:
            output_json(payload)
        else:
            print("Plano de swap")
            print(f"Status: {payload['status']}")
            print(f"Rota: {payload['from_chain']} {payload['from_token']} -> {payload['to_token']}")
            print(f"Valor: US$ {payload['amount_usd']:,.2f} | Slippage: {payload['slippage_bps']} bps")
            print(f"Adapter: {payload['adapter_family']}")
            print(f"Broadcast: {payload['broadcasted']}")
            print(f"Bloqueios: {'; '.join(payload['blocked_reasons']) or 'nenhum'}")
        return

    if args.mode == "bridge":
        payload = asdict(
            build_bridge_plan(args.from_chain, args.to_chain, args.token or args.from_token, args.amount_usd, args.profile, args.slippage_bps)
        )
        if args.json:
            output_json(payload)
        else:
            print("Plano de bridge")
            print(f"Status: {payload['status']}")
            print(f"Rota: {payload['from_chain']} -> {payload['to_chain']} | Token: {payload['from_token']}")
            print(f"Valor: US$ {payload['amount_usd']:,.2f} | Slippage: {payload['slippage_bps']} bps")
            print(f"Adapter: {payload['adapter_family']}")
            print(f"Broadcast: {payload['broadcasted']}")
            print(f"Bloqueios: {'; '.join(payload['blocked_reasons']) or 'nenhum'}")
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
    if args.mode in {"plan", "execute"}:
        plan = build_execution_plan(best, args.capital, args.allocation_pct)
        if args.mode == "execute":
            receipt = execute_guarded(plan, args.action, args.confirm, args.position_id or None)
            if args.json:
                output_json({"mode": "execute", "profile": args.profile, "result": asdict(receipt)})
            else:
                print("Execucao guardada")
                print(f"Acao: {receipt.action}")
                print(f"Status: {receipt.status}")
                print(f"Pool: {receipt.chain} / {receipt.protocol} / {receipt.pool}")
                print(f"Position ID: {receipt.position_id}")
                print(f"Broadcast: {receipt.broadcasted}")
                print(f"Bloqueios: {'; '.join(receipt.blocked_reasons) or 'nenhum'}")
                print("Passos simulados:")
                for step in receipt.executed_steps:
                    print(f"- {step}")
            return

        if args.json:
            output_json({"mode": "plan", "profile": args.profile, "result": asdict(plan)})
        else:
            print("Plano operacional")
            print(f"Pool: {plan.chain} / {plan.protocol} / {plan.pool}")
            print(f"Adapter: {plan.adapter_family}")
            print(f"Alocacao planejada: US$ {plan.allocation_usd:,.2f}")
            if plan.range_suggestion:
                print(
                    "Range sugerido: "
                    f"{plan.range_suggestion.lower_pct * 100:.2f}% a "
                    f"+{plan.range_suggestion.upper_pct * 100:.2f}% "
                    f"(gatilho {plan.range_suggestion.rebalance_trigger_pct * 100:.2f}%, "
                    f"confianca {plan.range_suggestion.confidence})"
                )
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
        if best.trend_regime != "unknown":
            print(
                "Indicadores: "
                f"RSI14 {best.rsi_14:.1f} | ATR14 {best.atr_pct_14 * 100:.2f}% | "
                f"Bollinger {best.bollinger_width_pct * 100:.2f}% | ADX14 {best.adx_14:.1f} | "
                f"Regime {best.trend_regime}"
            )
        if best.range_suggestion:
            print(
                "Range sugerido: "
                f"{best.range_suggestion.lower_pct * 100:.2f}% a "
                f"+{best.range_suggestion.upper_pct * 100:.2f}% | "
                f"gatilho {best.range_suggestion.rebalance_trigger_pct * 100:.2f}% | "
                f"confianca {best.range_suggestion.confidence}"
            )
        print(f"Perda maxima estimada por drawdown: US$ {dry_run.max_loss_estimate_usd:,.2f}")
        print(f"IL estimado: US$ {dry_run.il_estimate_usd:,.2f}")
        if best.blocks:
            print(f"Bloqueios: {'; '.join(best.blocks)}")


if __name__ == "__main__":
    main()
