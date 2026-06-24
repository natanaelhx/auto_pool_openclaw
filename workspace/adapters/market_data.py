import json
import math
import urllib.error
import urllib.request


BINANCE_KLINES_URL = "https://api.binance.com/api/v3/klines"
STABLES = {"USDC", "USDT", "DAI", "FRAX", "USDS", "LUSD", "PYUSD", "USDE", "USDC.E", "USDT.E"}
CANONICAL = {
    "BTC": "BTC",
    "WBTC": "BTC",
    "CBBTC": "BTC",
    "TBTC": "BTC",
    "ETH": "ETH",
    "WETH": "ETH",
    "STETH": "ETH",
    "WSTETH": "ETH",
    "RETH": "ETH",
    "CBETH": "ETH",
    "SOL": "SOL",
    "MSOL": "SOL",
    "JITOSOL": "SOL",
    "BSOL": "SOL",
}


def canonical_asset(asset: str) -> str:
    upper = asset.upper()
    if upper in STABLES:
        return "USD"
    return CANONICAL.get(upper, upper)


def fetch_binance_closes(asset: str, interval: str = "1d", limit: int = 30, timeout: int = 8):
    symbol = f"{asset.upper()}USDT"
    url = f"{BINANCE_KLINES_URL}?symbol={symbol}&interval={interval}&limit={limit}"
    request = urllib.request.Request(url, headers={"User-Agent": "auto-pools/0.2.3"})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
        return []
    closes = []
    for row in payload:
        try:
            closes.append(float(row[4]))
        except (IndexError, TypeError, ValueError):
            continue
    return closes


def _returns(values):
    result = []
    for previous, current in zip(values, values[1:]):
        if previous > 0:
            result.append((current / previous) - 1.0)
    return result


def _realized_volatility(values):
    returns = _returns(values)
    if len(returns) < 2:
        return 0.0
    mean = sum(returns) / len(returns)
    variance = sum((item - mean) ** 2 for item in returns) / (len(returns) - 1)
    return math.sqrt(variance) * math.sqrt(len(returns))


def _max_drawdown(values):
    peak = values[0] if values else 0.0
    worst = 0.0
    for value in values:
        peak = max(peak, value)
        if peak > 0:
            worst = max(worst, (peak - value) / peak)
    return worst


def pair_market_metrics(assets, interval: str = "1d", limit: int = 30):
    if len(assets) < 2:
        return None

    left = canonical_asset(assets[0])
    right = canonical_asset(assets[1])

    if left == "USD" and right == "USD":
        return {
            "source": "stable-heuristic",
            "observations": limit,
            "range_pct": 0.01,
            "realized_volatility": 0.005,
            "max_drawdown": 0.005,
        }

    if left == right:
        return {
            "source": "correlated-asset-heuristic",
            "observations": limit,
            "range_pct": 0.04,
            "realized_volatility": 0.02,
            "max_drawdown": 0.025,
        }

    left_prices = [1.0] * limit if left == "USD" else fetch_binance_closes(left, interval=interval, limit=limit)
    right_prices = [1.0] * limit if right == "USD" else fetch_binance_closes(right, interval=interval, limit=limit)
    observations = min(len(left_prices), len(right_prices))
    if observations < max(10, limit // 2):
        return None

    left_prices = left_prices[-observations:]
    right_prices = right_prices[-observations:]
    ratios = [left_price / right_price for left_price, right_price in zip(left_prices, right_prices) if right_price > 0]
    if len(ratios) < max(10, limit // 2):
        return None

    low = min(ratios)
    high = max(ratios)
    range_pct = (high / low) - 1.0 if low > 0 else 0.0
    return {
        "source": "binance",
        "observations": len(ratios),
        "range_pct": range_pct,
        "realized_volatility": _realized_volatility(ratios),
        "max_drawdown": _max_drawdown(ratios),
    }
