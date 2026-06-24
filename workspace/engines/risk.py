def liquidity_score(tvl_usd: float, volume_24h_usd: float) -> float:
    tvl_component = min(60.0, max(0.0, tvl_usd / 1_000_000.0))
    volume_component = min(40.0, max(0.0, volume_24h_usd / 250_000.0))
    return min(100.0, tvl_component + volume_component)


def estimate_drawdown(pair_volatility: float, liquidity: float, profile: str) -> float:
    liquidity_relief = min(0.05, liquidity / 100.0 * 0.05)
    multiplier = {"conservador": 1.25, "moderado": 1.0, "agressivo": 0.85}.get(profile, 1.0)
    return max(0.01, pair_volatility * multiplier - liquidity_relief)


from engines.scenarios import conservative_blocks


def guardrails(pool, profile: str, drawdown: float, il: float):
    blocks = []
    warnings = []
    min_tvl = {"conservador": 20_000_000, "moderado": 8_000_000, "agressivo": 3_000_000}.get(profile, 8_000_000)
    max_drawdown = {"conservador": 0.10, "moderado": 0.18, "agressivo": 0.30}.get(profile, 0.18)
    max_il = {"conservador": 0.03, "moderado": 0.07, "agressivo": 0.12}.get(profile, 0.07)

    if pool.tvl_usd < min_tvl:
        blocks.append(f"TVL abaixo do minimo para perfil {profile}.")
    if pool.apr > 0.80 and profile != "agressivo":
        blocks.append("APR anormalmente alto para perfil nao agressivo.")
    if drawdown > max_drawdown:
        blocks.append("Drawdown estimado acima do limite do perfil.")
    if il > max_il:
        blocks.append("Impermanent loss estimado acima do limite do perfil.")
    if pool.volume_24h_usd and pool.volume_24h_usd < pool.tvl_usd * 0.01:
        warnings.append("Volume 24h baixo em relacao ao TVL.")
    if profile == "conservador":
        blocks.extend(conservative_blocks(pool.assets))

    return blocks, warnings
