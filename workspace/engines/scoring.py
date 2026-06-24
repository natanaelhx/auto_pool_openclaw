from engines.impermanent_loss import estimate_il
from engines.lateralization import estimate_lateralization_days, estimate_lateralization_score, estimate_pair_volatility
from engines.risk import estimate_drawdown, guardrails, liquidity_score
from engines.scenarios import classify_pair, scenario_for_profile
from models.schemas import PoolScore


def score_pool(pool, profile: str, market_metrics=None) -> PoolScore:
    liquidity = liquidity_score(pool.tvl_usd, pool.volume_24h_usd)
    lateral = estimate_lateralization_score(pool.assets, market_metrics)
    lateral_days = estimate_lateralization_days(lateral)
    volatility = estimate_pair_volatility(pool.assets, profile, market_metrics)
    il = estimate_il(volatility)
    drawdown = estimate_drawdown(volatility, liquidity, profile)
    blocks, warnings = guardrails(pool, profile, drawdown, il)

    apr_score = min(100.0, max(0.0, pool.apr * 500.0))
    risk_penalty = min(70.0, drawdown * 180.0 + il * 250.0)
    score = (
        0.20 * liquidity
        + 0.20 * apr_score
        + 0.15 * lateral
        + 0.15 * (100.0 - risk_penalty)
        + 0.10 * max(0.0, 100.0 - il * 700.0)
        + 0.10 * max(0.0, 100.0 - drawdown * 450.0)
        + 0.10 * 75.0
    )
    if blocks:
        score = min(score, 49.0)

    risk_adjusted_apr = max(0.0, pool.apr - drawdown * 0.45 - il * 0.65)
    reasons = [
        f"Cenario: {scenario_for_profile(profile, pool.assets)}",
        f"Tipo de par: {classify_pair(pool.assets)}.",
        f"Liquidez score {liquidity:.1f}/100.",
        f"Lateralizacao estimada {lateral:.1f}/100 por aproximadamente {lateral_days} dias.",
        f"APR ajustado por risco {risk_adjusted_apr * 100:.2f}% ao ano.",
    ] + warnings
    if market_metrics:
        reasons.insert(
            3,
            "Market data: range "
            f"{float(market_metrics.get('range_pct') or 0.0) * 100:.2f}% "
            f"em {int(market_metrics.get('observations') or 0)} observacoes "
            f"via {market_metrics.get('source')}.",
        )

    if blocks:
        decision = "bloqueado"
    elif score >= 75:
        decision = "aprovado"
    elif score >= 60:
        decision = "aprovado_com_limite"
    else:
        decision = "aguardar"

    return PoolScore(
        pool=pool,
        profile=profile,
        score=round(score, 2),
        risk_adjusted_apr=round(risk_adjusted_apr, 6),
        estimated_drawdown=round(drawdown, 6),
        estimated_il=round(il, 6),
        lateralization_score=round(lateral, 2),
        lateralization_days_estimate=lateral_days,
        scenario=scenario_for_profile(profile, pool.assets),
        decision=decision,
        reasons=reasons,
        blocks=blocks,
        market_data_source=str((market_metrics or {}).get("source") or "heuristic"),
        observed_range_pct=round(float((market_metrics or {}).get("range_pct") or 0.0), 6),
        observed_volatility=round(float((market_metrics or {}).get("realized_volatility") or 0.0), 6),
    )


def rank_pools(pools, profile: str, limit: int, market_metrics_by_pool=None):
    market_metrics_by_pool = market_metrics_by_pool or {}
    scored = [score_pool(pool, profile, market_metrics_by_pool.get(pool.pool)) for pool in pools]
    scored.sort(key=lambda item: item.score, reverse=True)
    return scored[:limit]
