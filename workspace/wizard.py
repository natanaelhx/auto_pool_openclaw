#!/usr/bin/env python3
import argparse
import json
import os
import re
from dataclasses import asdict

from adapters.defillama import fetch_pools
from dry_run import simulate
from engines.scoring import rank_pools

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATE_DIR = os.path.join(BASE_DIR, "state")
CONFIG_PATH = os.path.join(STATE_DIR, "auto_pools_config.json")

PROFILES = {"conservador", "moderado", "agressivo"}
YES = {"s", "sim", "y", "yes"}


def _ask(prompt: str, default: str = "") -> str:
    suffix = f" [{default}]" if default else ""
    value = input(f"{prompt}{suffix}: ").strip()
    return value or default


def _ask_choice(prompt: str, choices, default: str) -> str:
    while True:
        value = _ask(prompt, default).lower()
        if value in choices:
            return value
        print(f"Opcao invalida. Use: {', '.join(sorted(choices))}.")


def _ask_float(prompt: str, default: float, minimum: float, maximum: float) -> float:
    while True:
        raw = _ask(prompt, str(default)).replace(",", ".")
        try:
            value = float(raw)
        except ValueError:
            print("Valor invalido. Digite um numero.")
            continue
        if minimum <= value <= maximum:
            return value
        print(f"Valor fora do intervalo. Use entre {minimum} e {maximum}.")


def _valid_public_wallet(value: str) -> bool:
    if not value:
        return True
    if re.fullmatch(r"0x[a-fA-F0-9]{40}", value):
        return True
    if re.fullmatch(r"[1-9A-HJ-NP-Za-km-z]{32,64}", value):
        return True
    return False


def load_config(path: str = CONFIG_PATH):
    try:
        with open(path, "r", encoding="utf-8") as handle:
            return json.load(handle)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save_config(config, path: str = CONFIG_PATH):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(config, handle, ensure_ascii=False, indent=2)


def build_config_interactive():
    print("Auto Pools Wizard")
    print("Nao cole seed phrase, chave privada ou token. Use apenas endereco publico e variaveis de ambiente.")

    profile = _ask_choice("🛡️ Perfil de risco", PROFILES, "conservador")
    capital = _ask_float("💰 Capital de referencia em USD", 1000.0, 1.0, 1_000_000_000.0)
    allocation_pct = _ask_float("📊 Percentual maximo por pool em decimal", 0.08, 0.001, 0.30)
    limit = int(_ask_float("🔎 Quantidade de pools no ranking", 10, 1, 50))
    wallet = _ask("👛 Endereco publico da carteira, opcional", os.getenv("AUTO_POOLS_WALLET_ADDRESS", ""))
    while not _valid_public_wallet(wallet):
        print("Endereco invalido. Nao use seed phrase; informe apenas endereco publico.")
        wallet = _ask("👛 Endereco publico da carteira, opcional", "")
    automation = _ask_choice("🤖 Modo de automacao: dry-run ou guarded", {"dry-run", "guarded"}, "dry-run")

    return {
        "profile": profile,
        "capital_usd": capital,
        "allocation_pct": allocation_pct,
        "limit": limit,
        "wallet_address": wallet,
        "automation_mode": automation,
        "execution_enabled": False,
        "signer_env": "AUTO_POOLS_SIGNER_REF",
    }


def build_config_from_args(args):
    return {
        "profile": args.profile,
        "capital_usd": args.capital,
        "allocation_pct": args.allocation_pct,
        "limit": args.limit,
        "wallet_address": args.wallet_address or os.getenv("AUTO_POOLS_WALLET_ADDRESS", ""),
        "automation_mode": args.automation_mode,
        "execution_enabled": False,
        "signer_env": "AUTO_POOLS_SIGNER_REF",
    }


def run_analysis(config):
    pools = fetch_pools(limit=max(config["limit"], 25))
    scored = rank_pools(pools, config["profile"], config["limit"])
    best = next((item for item in scored if item.decision != "bloqueado"), scored[0])
    dry_run = simulate(best, config["capital_usd"], config["allocation_pct"])
    return {
        "config": config,
        "best": asdict(best),
        "dry_run": asdict(dry_run),
        "ranking": [asdict(item) for item in scored],
        "security": {
            "seed_phrase_allowed": False,
            "private_key_allowed": False,
            "execution_enabled": False,
            "note": "MVP opera em dry-run. Execucao real exige signer externo e confirmacao futura.",
        },
    }


def parse_args():
    parser = argparse.ArgumentParser(description="Wizard Auto Pools - configuracao guiada em PT-BR.")
    parser.add_argument("--headless", action="store_true", help="Usa parametros/defaults sem perguntas interativas.")
    parser.add_argument("--profile", choices=sorted(PROFILES), default=os.getenv("AUTO_POOLS_DEFAULT_PROFILE", "conservador"))
    parser.add_argument("--capital", type=float, default=1000.0)
    parser.add_argument("--allocation-pct", type=float, default=0.08)
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--wallet-address", default=os.getenv("AUTO_POOLS_WALLET_ADDRESS", ""))
    parser.add_argument("--automation-mode", choices=["dry-run", "guarded"], default="dry-run")
    parser.add_argument("--no-save", action="store_true")
    parser.add_argument("--json", action="store_true")
    return parser.parse_args()


def main():
    args = parse_args()
    config = build_config_from_args(args) if args.headless else build_config_interactive()

    if not _valid_public_wallet(config.get("wallet_address", "")):
        raise SystemExit("Endereco publico invalido. Nunca informe seed phrase ou chave privada.")
    if not args.no_save:
        save_config(config)

    result = run_analysis(config)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    best = result["best"]
    dry = result["dry_run"]
    pool = best["pool"]
    print("\nResultado do Wizard")
    print(f"Perfil: {config['profile']} | Modo: {config['automation_mode']} | Execucao real: desativada")
    print(f"Melhor pool: {pool['chain']} / {pool['protocol']} / {pool['pool']}")
    print(f"Decisao: {best['decision']} | Score: {best['score']}/100")
    print(f"APR: {pool['apr'] * 100:.2f}% | APR ajustado: {best['risk_adjusted_apr'] * 100:.2f}%")
    print(f"Lateralizacao: {best['lateralization_score']:.1f}/100 (~{best['lateralization_days_estimate']} dias)")
    print(f"Drawdown estimado: {best['estimated_drawdown'] * 100:.2f}% | IL: {best['estimated_il'] * 100:.2f}%")
    print(f"Alocacao simulada: US$ {dry['allocation_usd']:,.2f}")
    print(f"Yield anual ajustado: US$ {dry['expected_yearly_yield_usd']:,.2f}")
    print("Seed phrase/chave privada: nao solicitado e nao permitido.")


if __name__ == "__main__":
    main()
