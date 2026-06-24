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
        rsi = market_metrics.get("rsi_14")
        atr = market_metrics.get("atr_pct_14")
        bollinger = market_metrics.get("bollinger_width_pct")
        adx = market_metrics.get("adx_14")
        reasons.insert(
            3,
            "Market data: range "
            f"{float(market_metrics.get('range_pct') or 0.0) * 100:.2f}% "
            f"em {int(market_metrics.get('observations') or 0)} observacoes "
            f"via {market_metrics.get('source')}.",
        )
        if all(value is not None for value in [rsi, atr, bollinger, adx]):
            reasons.insert(
                4,
                "Indicadores: "
                f"RSI14 {float(rsi):.1f}, ATR14 {float(atr) * 100:.2f}%, "
                f"Bollinger width {float(bollinger) * 100:.2f}%, ADX14 {float(adx):.1f}, "
                f"regime {market_metrics.get('trend_regime') or 'misto'}.",
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
        rsi_14=round(float((market_metrics or {}).get("rsi_14") or 0.0), 6),
        atr_pct_14=round(float((market_metrics or {}).get("atr_pct_14") or 0.0), 6),
        bollinger_width_pct=round(float((market_metrics or {}).get("bollinger_width_pct") or 0.0), 6),
        adx_14=round(float((market_metrics or {}).get("adx_14") or 0.0), 6),
        trend_regime=str((market_metrics or {}).get("trend_regime") or "unknown"),
    )


def rank_pools(pools, profile: str, limit: int, market_metrics_by_pool=None):
    market_metrics_by_pool = market_metrics_by_pool or {}
    scored = [score_pool(pool, profile, market_metrics_by_pool.get(pool.pool)) for pool in pools]
    scored.sort(key=lambda item: item.score, reverse=True)
    return scored[:limit]
