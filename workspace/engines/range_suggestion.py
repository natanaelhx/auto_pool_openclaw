from models.schemas import RangeSuggestion


PROFILE_MIN_WIDTH = {
    "conservador": 0.08,
    "moderado": 0.12,
    "agressivo": 0.18,
}

PROFILE_MAX_WIDTH = {
    "conservador": 0.35,
    "moderado": 0.55,
    "agressivo": 0.85,
}


def suggest_range(market_metrics, profile: str) -> RangeSuggestion:
    metrics = market_metrics or {}
    observed_range = float(metrics.get("range_pct") or 0.0)
    atr_pct = float(metrics.get("atr_pct_14") or 0.0)
    bollinger_width = float(metrics.get("bollinger_width_pct") or 0.0)
    adx = float(metrics.get("adx_14") or 0.0)
    observations = int(metrics.get("observations") or 0)
    trend_regime = str(metrics.get("trend_regime") or "unknown")

    minimum = PROFILE_MIN_WIDTH.get(profile, PROFILE_MIN_WIDTH["moderado"])
    maximum = PROFILE_MAX_WIDTH.get(profile, PROFILE_MAX_WIDTH["moderado"])
    raw_width = max(minimum, observed_range * 1.20, atr_pct * 6.0, bollinger_width * 1.10)
    width = min(maximum, raw_width)

    if trend_regime in {"tendencia", "impulso"} or adx >= 28:
        confidence = "baixa"
    elif observations >= 45 and trend_regime == "lateral":
        confidence = "alta"
    elif observations >= 20:
        confidence = "media"
    else:
        confidence = "baixa"

    if not metrics:
        method = "heuristic-profile"
        notes = ["Sem candles confiaveis; range baseado apenas no perfil."]
    else:
        method = "market-data-dynamic-range"
        notes = [
            "Range sugerido a partir de range observado, ATR, Bollinger width e regime.",
            "Usar como entrada para simulacao; nao e ordem on-chain.",
        ]
    if confidence == "baixa":
        notes.append("Confianca baixa: exigir range mais largo, menor alocacao ou aguardar novo sinal.")

    return RangeSuggestion(
        method=method,
        center="spot-ratio",
        lower_pct=round(-(width / 2.0), 6),
        upper_pct=round(width / 2.0, 6),
        width_pct=round(width, 6),
        rebalance_trigger_pct=round(width * 0.80, 6),
        confidence=confidence,
        notes=notes,
    )
