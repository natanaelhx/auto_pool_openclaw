import os

from models.schemas import ExecutionGuardrails, PoolExecutionPlan


EVM_CHAINS = {"ethereum", "arbitrum", "base", "optimism", "polygon"}
SOLANA_CHAINS = {"solana"}


def _truthy(value) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "y", "on"}


def _adapter_family(chain: str, protocol: str) -> str:
    protocol = protocol.lower()
    chain = chain.lower()
    if chain in SOLANA_CHAINS:
        if "orca" in protocol:
            return "solana-orca-whirlpools"
        if "raydium" in protocol:
            return "solana-raydium"
        return "solana-generic-lp"
    if "uniswap" in protocol:
        return "evm-uniswap-v3"
    if "aerodrome" in protocol or "velodrome" in protocol:
        return "evm-slipstream"
    if "curve" in protocol:
        return "evm-curve-stableswap"
    if "balancer" in protocol:
        return "evm-balancer"
    return "evm-generic-lp"


def _entry_steps(chain: str, adapter: str) -> list:
    if chain in SOLANA_CHAINS:
        return [
            "Carregar endereco publico da wallet e saldos SPL.",
            "Buscar pool, vaults, tick arrays/bin arrays e configuracao do protocolo.",
            "Simular add liquidity em RPC/SDK antes de montar transacao.",
            "Criar ou validar associated token accounts necessarias.",
            "Montar instrucao add liquidity com slippage e range definidos.",
            "Bloquear envio: esta versao nao assina nem transmite transacao.",
        ]
    return [
        "Carregar endereco publico da wallet e saldos ERC-20.",
        "Resolver contratos do protocolo, pool, router/position manager e tokens.",
        "Simular quote e checar preco/range antes de approve.",
        "Preparar approve limitado por token, nunca allowance infinito por padrao.",
        "Montar calldata de add liquidity/mint/increaseLiquidity conforme adaptador.",
        "Bloquear envio: esta versao nao assina nem transmite transacao.",
    ]


def _exit_steps(chain: str) -> list:
    if chain in SOLANA_CHAINS:
        return [
            "Ler posicao LP/NFT/conta de liquidez.",
            "Simular remove liquidity e collect fees.",
            "Aplicar limite de slippage e minimo recebido por token.",
            "Montar instrucao de retirada parcial ou total.",
            "Bloquear envio ate existir signer seguro e confirmacao explicita.",
        ]
    return [
        "Ler posicao LP/NFT e fees acumuladas.",
        "Simular decreaseLiquidity/removeLiquidity e collect.",
        "Aplicar minimo recebido, deadline e limite de gas.",
        "Montar calldata de retirada parcial ou total.",
        "Bloquear envio ate existir signer seguro e confirmacao explicita.",
    ]


def _rebalance_steps() -> list:
    return [
        "Recalcular score, drawdown, IL e lateralizacao.",
        "Comparar range atual contra range alvo.",
        "Se violar limite, gerar ExitPlan antes de novo EntryPlan.",
        "Executar sempre como duas fases: sair/coletar, depois entrar novamente.",
        "Exigir nova simulacao e confirmacao antes de qualquer versao com envio real.",
    ]


def build_execution_plan(score, capital_usd: float, allocation_pct: float) -> PoolExecutionPlan:
    pool = score.pool
    chain = pool.chain.lower()
    adapter = _adapter_family(chain, pool.protocol)
    allocation_pct = max(0.0, min(allocation_pct, 0.30))
    allocation_usd = round(capital_usd * allocation_pct, 2)
    assets = pool.assets or ["UNKNOWN", "UNKNOWN"]
    per_asset = round(allocation_usd / max(len(assets), 1), 2)
    execution_enabled = _truthy(os.getenv("AUTO_POOLS_EXECUTION_ENABLE", "false"))
    signer_ref = os.getenv("AUTO_POOLS_SIGNER_REF", "").strip()

    blocked = list(score.blocks)
    if score.decision == "bloqueado":
        blocked.append("pool-score-bloqueado")
    if not execution_enabled:
        blocked.append("execution-disabled")
    if execution_enabled and not signer_ref:
        blocked.append("missing-signer-ref")

    return PoolExecutionPlan(
        action="plan",
        chain=chain,
        protocol=pool.protocol,
        pool=pool.pool,
        assets=assets,
        profile=score.profile,
        allocation_usd=allocation_usd,
        token_amounts_usd={asset: per_asset for asset in assets},
        range_suggestion=score.range_suggestion,
        adapter_family=adapter,
        entry_steps=_entry_steps(chain, adapter),
        exit_steps=_exit_steps(chain),
        rebalance_steps=_rebalance_steps(),
        guardrails=ExecutionGuardrails(
            dry_run_only=True,
            execution_enabled=False,
            requires_confirmation=True,
            slippage_bps=30 if score.profile == "conservador" else 50,
            max_gas_usd=12.0 if chain in EVM_CHAINS else 0.25,
            deadline_seconds=900,
            max_drawdown_pct=round(score.estimated_drawdown * 100.0, 4),
            max_il_pct=round(score.estimated_il * 100.0, 4),
            blocked_reasons=sorted(set(blocked)),
        ),
        notes=[
            "Plano operacional gerado sem assinatura e sem broadcast.",
            "Seed phrase e chave privada nunca devem ser informadas no chat ou salvas no Git.",
            "Execucao on-chain real exige release futura com signer seguro, simulacao e confirmacao explicita.",
        ],
    )
