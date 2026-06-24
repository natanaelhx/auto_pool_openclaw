STABLES = {"USDC", "USDT", "DAI", "FRAX", "USDS", "LUSD", "PYUSD"}
ETH_ASSETS = {"ETH", "WETH", "STETH", "WSTETH", "RETH"}
BTC_ASSETS = {"BTC", "WBTC", "TBTC", "CBBTC"}
SOL_ASSETS = {"SOL", "MSOL", "JITOSOL"}
BLUE_CHIPS = ETH_ASSETS | BTC_ASSETS | SOL_ASSETS


def score_from_market_metrics(metrics):
    if not metrics:
        return None
    range_pct = float(metrics.get("range_pct") or 0.0)
    realized_volatility = float(metrics.get("realized_volatility") or 0.0)
    max_drawdown = float(metrics.get("max_drawdown") or 0.0)
    pressure = max(range_pct, realized_volatility * 1.5, max_drawdown * 1.2)
    if pressure <= 0.02:
        return 94.0
    if pressure <= 0.06:
        return 86.0
    if pressure <= 0.10:
        return 76.0
    if pressure <= 0.16:
        return 66.0
    if pressure <= 0.24:
        return 54.0
    return 40.0


def volatility_from_market_metrics(metrics):
    if not metrics:
        return None
    range_pct = float(metrics.get("range_pct") or 0.0)
    realized_volatility = float(metrics.get("realized_volatility") or 0.0)
    max_drawdown = float(metrics.get("max_drawdown") or 0.0)
    return max(0.01, min(0.60, max(range_pct * 0.60, realized_volatility, max_drawdown)))


def estimate_lateralization_score(assets, market_metrics=None):
    market_score = score_from_market_metrics(market_metrics)
    if market_score is not None:
        return market_score

    upper_list = [asset.upper() for asset in assets]
    upper = set(upper_list)
    stable_count = sum(1 for asset in upper_list if asset in STABLES)
    eth_count = sum(1 for asset in upper_list if asset in ETH_ASSETS)
    btc_count = sum(1 for asset in upper_list if asset in BTC_ASSETS)
    sol_count = sum(1 for asset in upper_list if asset in SOL_ASSETS)
    blue_count = eth_count + btc_count + sol_count

    if stable_count >= 2:
        return 92.0
    if stable_count == 1 and (eth_count == 1 or btc_count == 1):
        return 76.0
    if stable_count == 1 and sol_count == 1:
        return 72.0
    if eth_count >= 2 or btc_count >= 2 or sol_count >= 2:
        return 74.0
    if btc_count >= 1 and eth_count >= 1:
        return 70.0
    if upper <= BLUE_CHIPS:
        return 68.0
    if stable_count == 1:
        return 54.0
    return 42.0


def estimate_pair_volatility(assets, profile, market_metrics=None):
    market_volatility = volatility_from_market_metrics(market_metrics)
    if market_volatility is not None:
        base = market_volatility
        if profile == "conservador":
            return base * 1.10
        if profile == "agressivo":
            return base * 0.90
        return base

    upper_list = [asset.upper() for asset in assets]
    upper = set(upper_list)
    stable_count = sum(1 for asset in upper_list if asset in STABLES)
    eth_count = sum(1 for asset in upper_list if asset in ETH_ASSETS)
    btc_count = sum(1 for asset in upper_list if asset in BTC_ASSETS)
    sol_count = sum(1 for asset in upper_list if asset in SOL_ASSETS)

    base = 0.06
    if stable_count >= 2:
        base = 0.015
    elif stable_count == 1 and (eth_count == 1 or btc_count == 1):
        base = 0.09
    elif stable_count == 1 and sol_count == 1:
        base = 0.095
    elif eth_count >= 2 or btc_count >= 2 or sol_count >= 2:
        base = 0.08
    elif btc_count >= 1 and eth_count >= 1:
        base = 0.11
    elif upper <= BLUE_CHIPS:
        base = 0.12
    elif stable_count == 1:
        base = 0.18
    else:
        base = 0.28

    if profile == "conservador":
        return base * 1.10
    if profile == "agressivo":
        return base * 0.90
    return base


def estimate_lateralization_days(score: float) -> int:
    if score >= 90:
        return 30
    if score >= 75:
        return 21
    if score >= 65:
        return 14
    if score >= 50:
        return 7
    return 3
