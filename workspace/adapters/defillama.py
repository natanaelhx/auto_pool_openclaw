import json
import os
import urllib.error
import urllib.request
from typing import List

from models.schemas import PoolCandidate


DEFILLAMA_POOLS_URL = "https://yields.llama.fi/pools"
MIN_TVL_USD = 1_000_000
MIN_APR = 0.001
MAX_APR = 0.80
SUPPORTED_CHAINS = {
    "ethereum",
    "arbitrum",
    "base",
    "optimism",
    "polygon",
    "solana",
}
SAFE_TOKENS = {
    "USDC",
    "USDT",
    "DAI",
    "FRAX",
    "USDS",
    "LUSD",
    "PYUSD",
    "USDE",
    "USDC.E",
    "USDT.E",
    "WBTC",
    "CBBTC",
    "TBTC",
    "BTC",
    "ETH",
    "WETH",
    "STETH",
    "WSTETH",
    "RETH",
    "CBETH",
    "SOL",
    "MSOL",
    "JITOSOL",
    "BSOL",
}
TRUSTED_PROTOCOLS = {
    "aave-v3",
    "aerodrome",
    "balancer",
    "curve",
    "kamino-liquidity",
    "meteora",
    "orca",
    "orca-dex",
    "raydium",
    "raydium-amm",
    "uniswap-v3",
    "velodrome",
}


def _to_float(value, default=0.0):
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _truthy(value) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def _normalize_apr(value) -> float:
    """Return APR/APY as decimal; DefiLlama APY is commonly percent-formatted."""
    raw = _to_float(value)
    if raw > 1.5:
        return raw / 100.0
    return raw


def _parse_assets(symbol: str):
    cleaned = symbol.replace("-", "/")
    assets = [part.strip().upper() for part in cleaned.split("/") if part.strip()]
    if len(assets) < 2:
        return []
    if len(set(assets[:2])) < 2:
        return []
    return assets[:2]


def _chain_key(chain: str) -> str:
    return chain.strip().lower()


def _safe_assets(assets) -> bool:
    return bool(assets) and all(asset.upper() in SAFE_TOKENS for asset in assets)


def _source_filter_reasons(item, assets, apr: float, tvl_usd: float):
    reasons = []
    chain = _chain_key(str(item.get("chain") or ""))
    protocol = str(item.get("project") or "").strip().lower()
    exposure = str(item.get("exposure") or "").strip().lower()

    if chain not in SUPPORTED_CHAINS:
        reasons.append("unsupported-chain")
    if protocol not in TRUSTED_PROTOCOLS:
        reasons.append("untrusted-protocol")
    if not _safe_assets(assets):
        reasons.append("unsafe-assets")
    if tvl_usd < MIN_TVL_USD:
        reasons.append("low-tvl")
    if apr < MIN_APR:
        reasons.append("low-apr")
    if apr > MAX_APR:
        reasons.append("high-apr-outlier")
    if _truthy(item.get("outlier")):
        reasons.append("source-outlier")
    if str(item.get("status", "active")).lower() not in {"active", ""}:
        reasons.append("inactive")
    if chain == "solana" and exposure and exposure != "multi":
        reasons.append("solana-not-lp")
    return reasons


def _candidate_prescore(pool: PoolCandidate) -> float:
    tvl_score = min(60.0, pool.tvl_usd / 1_000_000.0)
    volume_score = min(25.0, pool.volume_24h_usd / 400_000.0)
    apr_score = min(40.0, pool.apr * 250.0)
    return tvl_score + volume_score + apr_score


def fetch_pools(limit: int = 50, timeout: int = 12, chain: str = "all") -> List[PoolCandidate]:
    chain_filter = _chain_key(chain)
    if os.getenv("AUTO_POOLS_USE_SAMPLE", "").lower() in {"1", "true", "yes"}:
        pools = sample_pools()
        if chain_filter != "all":
            pools = [pool for pool in pools if _chain_key(pool.chain) == chain_filter]
        return pools[:limit]

    request = urllib.request.Request(
        DEFILLAMA_POOLS_URL,
        headers={"User-Agent": "auto-pools/0.2.1"},
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
        return sample_pools()

    pools = []
    for item in payload.get("data", []):
        symbol = str(item.get("symbol") or "")
        assets = _parse_assets(symbol)
        apr = _normalize_apr(item.get("apy"))
        tvl_usd = _to_float(item.get("tvlUsd"))
        item_chain = _chain_key(str(item.get("chain") or "unknown"))
        if chain_filter != "all" and item_chain != chain_filter:
            continue
        if not assets or _source_filter_reasons(item, assets, apr, tvl_usd):
            continue
        pools.append(
            PoolCandidate(
                chain=item_chain,
                protocol=str(item.get("project") or "unknown").lower(),
                pool="/".join(assets),
                assets=assets,
                apr=apr,
                base_apr=_normalize_apr(item.get("apyBase")),
                reward_apr=_normalize_apr(item.get("apyReward")),
                tvl_usd=tvl_usd,
                volume_24h_usd=_to_float(item.get("volumeUsd1d")),
                source=["defillama"],
            )
        )

    pools.sort(key=_candidate_prescore, reverse=True)
    return pools[:limit] or sample_pools()


def sample_pools() -> List[PoolCandidate]:
    return [
        PoolCandidate("ethereum", "curve", "USDC/USDT", ["USDC", "USDT"], 0.047, 120000000, 24000000, source=["sample"]),
        PoolCandidate("arbitrum", "uniswap-v3", "ETH/USDC", ["ETH", "USDC"], 0.126, 52000000, 8800000, source=["sample"]),
        PoolCandidate("base", "aerodrome", "ETH/USDC", ["ETH", "USDC"], 0.151, 41000000, 7100000, source=["sample"]),
        PoolCandidate("solana", "orca", "SOL/USDC", ["SOL", "USDC"], 0.182, 33000000, 9300000, source=["sample"]),
        PoolCandidate("arbitrum", "camelot", "ARB/ETH", ["ARB", "ETH"], 0.264, 9000000, 1200000, source=["sample"]),
    ]
