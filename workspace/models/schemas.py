from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class PoolCandidate:
    chain: str
    protocol: str
    pool: str
    assets: List[str]
    apr: float
    tvl_usd: float
    volume_24h_usd: float = 0.0
    base_apr: float = 0.0
    reward_apr: float = 0.0
    source: List[str] = field(default_factory=list)


@dataclass
class PoolScore:
    pool: PoolCandidate
    profile: str
    score: float
    risk_adjusted_apr: float
    estimated_drawdown: float
    estimated_il: float
    lateralization_score: float
    lateralization_days_estimate: int
    scenario: str
    decision: str
    reasons: List[str]
    blocks: List[str]
    market_data_source: str = "heuristic"
    observed_range_pct: float = 0.0
    observed_volatility: float = 0.0
    rsi_14: float = 0.0
    atr_pct_14: float = 0.0
    bollinger_width_pct: float = 0.0
    adx_14: float = 0.0
    trend_regime: str = "unknown"
    range_suggestion: "RangeSuggestion" = None


@dataclass
class DryRunResult:
    score: PoolScore
    capital_usd: float
    allocation_pct: float
    allocation_usd: float
    max_loss_estimate_usd: float
    il_estimate_usd: float
    expected_yearly_yield_usd: float
    post_allocation: Dict[str, float]


@dataclass
class ExecutionGuardrails:
    dry_run_only: bool
    execution_enabled: bool
    requires_confirmation: bool
    slippage_bps: int
    max_gas_usd: float
    deadline_seconds: int
    max_drawdown_pct: float
    max_il_pct: float
    blocked_reasons: List[str]


@dataclass
class PoolExecutionPlan:
    action: str
    chain: str
    protocol: str
    pool: str
    assets: List[str]
    profile: str
    allocation_usd: float
    token_amounts_usd: Dict[str, float]
    range_suggestion: "RangeSuggestion"
    adapter_family: str
    entry_steps: List[str]
    exit_steps: List[str]
    rebalance_steps: List[str]
    guardrails: ExecutionGuardrails
    notes: List[str]


@dataclass
class ExecutionReceipt:
    action: str
    status: str
    chain: str
    protocol: str
    pool: str
    adapter_family: str
    position_id: Optional[str]
    simulated: bool
    broadcasted: bool
    tx_hash: Optional[str]
    guardrails: ExecutionGuardrails
    blocked_reasons: List[str]
    executed_steps: List[str]
    state_path: str
    notes: List[str]


@dataclass
class RangeSuggestion:
    method: str
    center: str
    lower_pct: float
    upper_pct: float
    width_pct: float
    rebalance_trigger_pct: float
    confidence: str
    notes: List[str]


@dataclass
class OperationPlan:
    mode: str
    status: str
    profile: str
    from_chain: str
    to_chain: Optional[str]
    from_token: str
    to_token: str
    amount_usd: float
    adapter_family: str
    slippage_bps: int
    dry_run_only: bool
    broadcasted: bool
    tx_hash: Optional[str]
    blocked_reasons: List[str]
    steps: List[str]
    notes: List[str]
