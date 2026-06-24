import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORKSPACE = os.path.join(ROOT, "workspace")
sys.path.insert(0, WORKSPACE)

from adapters.defillama import _normalize_apr, _parse_assets, _source_filter_reasons, fetch_pools, sample_pools
from adapters import market_data
from adapters.market_data import pair_market_metrics
from dry_run import simulate
from models.schemas import PoolCandidate
from engines.scoring import rank_pools
from executor import execute_guarded
from planner import build_execution_plan
from state.store import POSITIONS_PATH
from wizard import build_config_from_args, run_analysis


class Args:
    profile = "conservador"
    capital = 1000.0
    allocation_pct = 0.08
    limit = 3
    wallet_address = ""
    automation_mode = "dry-run"


class AutoPoolsTest(unittest.TestCase):
    def tearDown(self):
        if os.path.exists(POSITIONS_PATH):
            os.remove(POSITIONS_PATH)

    def test_parse_assets_rejects_same_asset_pair(self):
        self.assertEqual(_parse_assets("USDT-USDT"), [])
        self.assertEqual(_parse_assets("ETH-USDC"), ["ETH", "USDC"])

    def test_defillama_apr_percent_is_normalized_to_decimal(self):
        self.assertEqual(_normalize_apr(12.5), 0.125)
        self.assertEqual(_normalize_apr(0.125), 0.125)

    def test_evm_and_solana_source_filters(self):
        evm = {"chain": "Base", "project": "aerodrome", "symbol": "ETH-USDC", "apy": 12.5, "tvlUsd": 25_000_000}
        solana = {"chain": "Solana", "project": "orca-dex", "symbol": "SOL-USDC", "apy": 18.0, "tvlUsd": 25_000_000, "exposure": "multi"}
        bad = {"chain": "Solana", "project": "unknown-farm", "symbol": "MEME-USDC", "apy": 120.0, "tvlUsd": 100_000, "exposure": "single"}

        self.assertEqual(_source_filter_reasons(evm, ["ETH", "USDC"], 0.125, 25_000_000), [])
        self.assertEqual(_source_filter_reasons(solana, ["SOL", "USDC"], 0.18, 25_000_000), [])
        self.assertIn("untrusted-protocol", _source_filter_reasons(bad, ["MEME", "USDC"], 1.20, 100_000))

    def test_sample_scan_can_filter_solana(self):
        os.environ["AUTO_POOLS_USE_SAMPLE"] = "1"
        pools = fetch_pools(limit=10, chain="solana")
        self.assertEqual([pool.chain for pool in pools], ["solana"])
        self.assertEqual(pools[0].pool, "SOL/USDC")

    def test_conservative_ranking_blocks_alt_pairs(self):
        ranked = rank_pools(sample_pools(), "conservador", 5)
        blocked = [item for item in ranked if item.pool.pool == "ARB/ETH"][0]
        self.assertEqual(blocked.decision, "bloqueado")
        self.assertTrue(blocked.blocks)

    def test_conservative_ranking_allows_bluechip_stable_pairs(self):
        ranked = rank_pools(sample_pools(), "conservador", 5)
        sol_stable = [item for item in ranked if item.pool.pool == "SOL/USDC"][0]
        self.assertNotEqual(sol_stable.decision, "bloqueado")
        self.assertFalse(sol_stable.blocks)
        self.assertGreaterEqual(sol_stable.lateralization_score, 70.0)

    def test_conservative_ranking_allows_correlated_bluechip_pairs(self):
        pool = PoolCandidate("solana", "orca-dex", "SOL/JITOSOL", ["SOL", "JITOSOL"], 0.08, 50_000_000, 5_000_000)
        ranked = rank_pools([pool], "conservador", 1)
        self.assertNotIn("Par volatil/volatil fora da lista conservadora.", ranked[0].blocks)
        self.assertGreaterEqual(ranked[0].lateralization_score, 70.0)

    def test_market_data_heuristic_for_stable_and_correlated_pairs(self):
        stable = pair_market_metrics(["USDC", "USDT"])
        correlated = pair_market_metrics(["SOL", "JITOSOL"])
        self.assertEqual(stable["source"], "stable-heuristic")
        self.assertEqual(correlated["source"], "correlated-asset-heuristic")
        self.assertEqual(stable["trend_regime"], "lateral")
        self.assertIn("rsi_14", stable)
        self.assertIn("atr_pct_14", stable)
        self.assertIn("bollinger_width_pct", stable)
        self.assertIn("adx_14", stable)

    def test_coingecko_fallback_builds_market_metrics(self):
        original_binance = market_data.fetch_binance_klines
        original_coingecko = market_data.fetch_coingecko_ohlc

        def fake_binance(*args, **kwargs):
            return []

        def fake_coingecko(*args, **kwargs):
            candles = []
            for index in range(60):
                close = 100.0 + index * 0.2
                candles.append({"open": close - 0.1, "high": close + 0.3, "low": close - 0.3, "close": close})
            return candles

        try:
            market_data.fetch_binance_klines = fake_binance
            market_data.fetch_coingecko_ohlc = fake_coingecko
            metrics = pair_market_metrics(["ARB", "USDC"])
        finally:
            market_data.fetch_binance_klines = original_binance
            market_data.fetch_coingecko_ohlc = original_coingecko

        self.assertEqual(metrics["source"], "coingecko")
        self.assertEqual(metrics["indicator_source"], "coingecko-ratio-ohlc")
        self.assertIn("adx_14", metrics)

    def test_ranking_can_use_market_metrics(self):
        pool = PoolCandidate("ethereum", "uniswap-v3", "ETH/USDC", ["ETH", "USDC"], 0.08, 50_000_000, 5_000_000)
        metrics = {
            "source": "test",
            "observations": 60,
            "range_pct": 0.03,
            "realized_volatility": 0.02,
            "max_drawdown": 0.02,
            "rsi_14": 51.0,
            "atr_pct_14": 0.01,
            "bollinger_width_pct": 0.04,
            "adx_14": 12.0,
            "trend_regime": "lateral",
        }
        ranked = rank_pools([pool], "conservador", 1, {"ETH/USDC": metrics})
        self.assertEqual(ranked[0].market_data_source, "test")
        self.assertEqual(ranked[0].trend_regime, "lateral")
        self.assertEqual(ranked[0].rsi_14, 51.0)
        self.assertEqual(ranked[0].range_suggestion.confidence, "alta")
        self.assertGreaterEqual(ranked[0].lateralization_score, 80.0)

    def test_trending_market_metrics_reduce_lateralization_score(self):
        pool = PoolCandidate("ethereum", "uniswap-v3", "ETH/USDC", ["ETH", "USDC"], 0.08, 50_000_000, 5_000_000)
        lateral_metrics = {
            "source": "test",
            "observations": 60,
            "range_pct": 0.03,
            "realized_volatility": 0.02,
            "max_drawdown": 0.02,
            "rsi_14": 51.0,
            "atr_pct_14": 0.01,
            "bollinger_width_pct": 0.04,
            "adx_14": 12.0,
            "trend_regime": "lateral",
        }
        trend_metrics = dict(lateral_metrics, rsi_14=78.0, atr_pct_14=0.08, bollinger_width_pct=0.22, adx_14=38.0, trend_regime="tendencia")
        lateral = rank_pools([pool], "conservador", 1, {"ETH/USDC": lateral_metrics})[0]
        trend = rank_pools([pool], "conservador", 1, {"ETH/USDC": trend_metrics})[0]
        self.assertLess(trend.lateralization_score, lateral.lateralization_score)
        self.assertGreater(trend.estimated_drawdown, lateral.estimated_drawdown)
        self.assertEqual(trend.range_suggestion.confidence, "baixa")

    def test_dry_run_caps_allocation(self):
        ranked = rank_pools(sample_pools(), "moderado", 1)
        result = simulate(ranked[0], 1000.0, 0.80)
        self.assertEqual(result.allocation_pct, 0.30)
        self.assertEqual(result.allocation_usd, 300.0)

    def test_execution_plan_is_dry_run_only_for_evm(self):
        ranked = rank_pools(sample_pools(), "conservador", 5)
        score = [item for item in ranked if item.pool.chain == "base"][0]
        plan = build_execution_plan(score, 1000.0, 0.08)
        self.assertEqual(plan.adapter_family, "evm-slipstream")
        self.assertIsNotNone(plan.range_suggestion)
        self.assertTrue(plan.guardrails.dry_run_only)
        self.assertFalse(plan.guardrails.execution_enabled)
        self.assertIn("execution-disabled", plan.guardrails.blocked_reasons)

    def test_execution_plan_supports_solana(self):
        ranked = rank_pools(sample_pools(), "moderado", 5)
        score = [item for item in ranked if item.pool.chain == "solana"][0]
        plan = build_execution_plan(score, 1000.0, 0.05)
        self.assertEqual(plan.adapter_family, "solana-orca-whirlpools")
        self.assertIn("associated token accounts", " ".join(plan.entry_steps))

    def test_guarded_executor_never_broadcasts(self):
        ranked = rank_pools(sample_pools(), "conservador", 5)
        score = [item for item in ranked if item.pool.chain == "base"][0]
        plan = build_execution_plan(score, 1000.0, 0.08)
        receipt = execute_guarded(plan, "open", confirm=True)
        self.assertEqual(receipt.status, "simulated")
        self.assertFalse(receipt.broadcasted)
        self.assertIsNone(receipt.tx_hash)
        self.assertIn("dry-run-only-release", receipt.blocked_reasons)
        self.assertIn("execution-disabled", receipt.blocked_reasons)

    def test_guarded_executor_requires_confirmation(self):
        ranked = rank_pools(sample_pools(), "conservador", 5)
        score = [item for item in ranked if item.pool.chain == "base"][0]
        plan = build_execution_plan(score, 1000.0, 0.08)
        receipt = execute_guarded(plan, "open", confirm=False)
        self.assertEqual(receipt.status, "blocked")
        self.assertIn("missing-explicit-confirmation", receipt.blocked_reasons)

    def test_wizard_headless_runs_without_secrets(self):
        os.environ["AUTO_POOLS_USE_SAMPLE"] = "1"
        config = build_config_from_args(Args())
        result = run_analysis(config)
        self.assertFalse(result["security"]["seed_phrase_allowed"])
        self.assertFalse(result["security"]["execution_enabled"])
        self.assertIn("best", result)


if __name__ == "__main__":
    unittest.main()
