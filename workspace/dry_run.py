from models.schemas import DryRunResult


def simulate(score, capital_usd: float, allocation_pct: float) -> DryRunResult:
    allocation_pct = max(0.0, min(allocation_pct, 0.30))
    allocation_usd = capital_usd * allocation_pct
    max_loss = allocation_usd * score.estimated_drawdown
    il_loss = allocation_usd * score.estimated_il
    expected_yield = allocation_usd * score.risk_adjusted_apr
    assets = score.pool.assets or ["UNKNOWN", "UNKNOWN"]
    half = allocation_usd / 2.0
    return DryRunResult(
        score=score,
        capital_usd=capital_usd,
        allocation_pct=allocation_pct,
        allocation_usd=allocation_usd,
        max_loss_estimate_usd=max_loss,
        il_estimate_usd=il_loss,
        expected_yearly_yield_usd=expected_yield,
        post_allocation={assets[0]: half, assets[1]: half},
    )
