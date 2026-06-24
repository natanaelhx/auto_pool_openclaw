def estimate_il(pair_volatility: float) -> float:
    """Approximate IL from expected relative price movement.

    pair_volatility is expressed as decimal movement, e.g. 0.10 for 10%.
    """
    movement = max(0.0, min(pair_volatility, 1.5))
    price_ratio_up = 1.0 + movement
    price_ratio_down = max(0.05, 1.0 - movement)
    il_up = 1.0 - (2.0 * (price_ratio_up ** 0.5) / (1.0 + price_ratio_up))
    il_down = 1.0 - (2.0 * (price_ratio_down ** 0.5) / (1.0 + price_ratio_down))
    return max(il_up, il_down)
