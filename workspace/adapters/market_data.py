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


def fetch_binance_klines(asset: str, interval: str = "1d", limit: int = 60, timeout: int = 8):
    symbol = f"{asset.upper()}USDT"
    url = f"{BINANCE_KLINES_URL}?symbol={symbol}&interval={interval}&limit={limit}"
    request = urllib.request.Request(url, headers={"User-Agent": "auto-pools/0.3.0"})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
        return []
    candles = []
    for row in payload:
        try:
            candles.append(
                {
                    "open": float(row[1]),
                    "high": float(row[2]),
                    "low": float(row[3]),
                    "close": float(row[4]),
                }
            )
        except (IndexError, TypeError, ValueError):
            continue
    return candles


def fetch_binance_closes(asset: str, interval: str = "1d", limit: int = 60, timeout: int = 8):
    return [item["close"] for item in fetch_binance_klines(asset, interval, limit, timeout)]


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


def _rsi(values, period: int = 14):
    if len(values) <= period:
        return None
    gains = []
    losses = []
    for previous, current in zip(values, values[1:]):
        change = current - previous
        gains.append(max(change, 0.0))
        losses.append(abs(min(change, 0.0)))
    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period
    for gain, loss in zip(gains[period:], losses[period:]):
        avg_gain = ((avg_gain * (period - 1)) + gain) / period
        avg_loss = ((avg_loss * (period - 1)) + loss) / period
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return 100.0 - (100.0 / (1.0 + rs))


def _atr_pct(candles, period: int = 14):
    if len(candles) <= period:
        return None
    true_ranges = []
    previous_close = candles[0]["close"]
    for candle in candles[1:]:
        high = candle["high"]
        low = candle["low"]
        true_ranges.append(max(high - low, abs(high - previous_close), abs(low - previous_close)))
        previous_close = candle["close"]
    atr = sum(true_ranges[-period:]) / period
    close = candles[-1]["close"]
    return atr / close if close > 0 else None


def _bollinger_width_pct(values, period: int = 20, stddevs: float = 2.0):
    if len(values) < period:
        return None
    window = values[-period:]
    mean = sum(window) / period
    variance = sum((value - mean) ** 2 for value in window) / period
    std = math.sqrt(variance)
    return ((mean + stddevs * std) - (mean - stddevs * std)) / mean if mean > 0 else None


def _adx(candles, period: int = 14):
    if len(candles) <= period * 2:
        return None
    plus_dm = []
    minus_dm = []
    true_ranges = []
    for previous, current in zip(candles, candles[1:]):
        up_move = current["high"] - previous["high"]
        down_move = previous["low"] - current["low"]
        plus_dm.append(up_move if up_move > down_move and up_move > 0 else 0.0)
        minus_dm.append(down_move if down_move > up_move and down_move > 0 else 0.0)
        true_ranges.append(
            max(
                current["high"] - current["low"],
                abs(current["high"] - previous["close"]),
                abs(current["low"] - previous["close"]),
            )
        )

    dx_values = []
    for index in range(period, len(true_ranges) + 1):
        tr_sum = sum(true_ranges[index - period : index])
        if tr_sum <= 0:
            continue
        plus_di = 100.0 * sum(plus_dm[index - period : index]) / tr_sum
        minus_di = 100.0 * sum(minus_dm[index - period : index]) / tr_sum
        denominator = plus_di + minus_di
        if denominator > 0:
            dx_values.append(100.0 * abs(plus_di - minus_di) / denominator)
    if len(dx_values) < period:
        return None
    return sum(dx_values[-period:]) / period


def _ratio_candles(left_candles, right_candles):
    observations = min(len(left_candles), len(right_candles))
    result = []
    for left, right in zip(left_candles[-observations:], right_candles[-observations:]):
        if min(right["open"], right["high"], right["low"], right["close"]) <= 0:
            continue
        result.append(
            {
                "open": left["open"] / right["open"],
                "high": left["high"] / right["low"],
                "low": left["low"] / right["high"],
                "close": left["close"] / right["close"],
            }
        )
    return result


def _regime(indicators):
    adx = indicators.get("adx_14")
    rsi = indicators.get("rsi_14")
    bollinger = indicators.get("bollinger_width_pct")
    atr = indicators.get("atr_pct_14")
    if adx is not None and adx >= 28:
        return "tendencia"
    if rsi is not None and (rsi >= 70 or rsi <= 30):
        return "impulso"
    if bollinger is not None and bollinger <= 0.08 and atr is not None and atr <= 0.04:
        return "lateral"
    return "misto"


def _indicator_payload(candles, source: str):
    closes = [item["close"] for item in candles]
    indicators = {
        "rsi_14": _rsi(closes),
        "atr_pct_14": _atr_pct(candles),
        "bollinger_width_pct": _bollinger_width_pct(closes),
        "adx_14": _adx(candles),
    }
    rounded = {key: (round(value, 6) if value is not None else None) for key, value in indicators.items()}
    rounded["trend_regime"] = _regime(indicators)
    rounded["indicator_source"] = source
    return rounded


def pair_market_metrics(assets, interval: str = "1d", limit: int = 60):
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
            "rsi_14": 50.0,
            "atr_pct_14": 0.002,
            "bollinger_width_pct": 0.01,
            "adx_14": 8.0,
            "trend_regime": "lateral",
            "indicator_source": "heuristic",
        }

    if left == right:
        return {
            "source": "correlated-asset-heuristic",
            "observations": limit,
            "range_pct": 0.04,
            "realized_volatility": 0.02,
            "max_drawdown": 0.025,
            "rsi_14": 50.0,
            "atr_pct_14": 0.015,
            "bollinger_width_pct": 0.04,
            "adx_14": 14.0,
            "trend_regime": "lateral",
            "indicator_source": "heuristic",
        }

    stable_candle = {"open": 1.0, "high": 1.0, "low": 1.0, "close": 1.0}
    left_candles = [stable_candle] * limit if left == "USD" else fetch_binance_klines(left, interval=interval, limit=limit)
    right_candles = [stable_candle] * limit if right == "USD" else fetch_binance_klines(right, interval=interval, limit=limit)
    observations = min(len(left_candles), len(right_candles))
    if observations < max(10, limit // 2):
        return None

    candles = _ratio_candles(left_candles, right_candles)
    ratios = [item["close"] for item in candles]
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
        **_indicator_payload(candles, "binance-ratio-ohlc"),
    }
