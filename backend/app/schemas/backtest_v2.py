"""
Pydantic schemas for Backtesting v2
"""

from pydantic import BaseModel, Field, validator
from typing import List, Dict, Any, Optional, Literal
from datetime import datetime
from enum import Enum


# ============================================================================
# ENUMS
# ============================================================================

class BlockType(str, Enum):
    """Available block types"""
    # Data
    DATA_LOADER = "data.loader"
    DATA_RESAMPLER = "data.resampler"
    DATA_SPLITTER = "data.splitter"
    
    # Features
    FEATURE_RSI = "feature.rsi"
    FEATURE_MACD = "feature.macd"
    FEATURE_EMA = "feature.ema"
    FEATURE_ATR = "feature.atr"
    FEATURE_VWAP = "feature.vwap"
    FEATURE_CUSTOM = "feature.custom"
    
    # Signals
    SIGNAL_RULE = "signal.rule"
    SIGNAL_CROSSOVER = "signal.crossover"
    SIGNAL_THRESHOLD = "signal.threshold"
    SIGNAL_PATTERN = "signal.pattern"
    SIGNAL_ML = "signal.ml"
    
    # Position Sizing
    SIZING_FIXED = "sizing.fixed"
    SIZING_KELLY = "sizing.kelly"
    SIZING_VOL_TARGET = "sizing.vol_target"
    SIZING_RISK_PARITY = "sizing.risk_parity"
    
    # Risk Management
    RISK_STOP_TAKE = "risk.stop_take"
    RISK_TRAILING = "risk.trailing"
    RISK_TIME_STOP = "risk.time_stop"
    RISK_PORTFOLIO_DD = "risk.portfolio_dd"
    
    # Execution
    EXEC_MARKET = "exec.market"
    EXEC_LIMIT = "exec.limit"
    EXEC_STOP = "exec.stop"
    
    # ML
    ML_TRAIN = "ml.train"
    ML_INFERENCE = "ml.inference"
    ML_FEATURE_ENG = "ml.feature_eng"
    
    # Validation
    VAL_WALK_FORWARD = "val.walk_forward"
    VAL_KFOLD = "val.kfold"
    VAL_PURGED_CV = "val.purged_cv"
    
    # Reports
    REPORT_METRICS = "report.metrics"
    REPORT_TEARSHEET = "report.tearsheet"
    REPORT_TRADES = "report.trades"


class RunStatus(str, Enum):
    QUEUED = "queued"
    PREPARING = "preparing"
    RUNNING = "running"
    AGGREGATING = "aggregating"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELED = "canceled"


class ArtifactType(str, Enum):
    MODEL = "model"
    DATASET = "dataset"
    CHART = "chart"
    REPORT = "report"
    NOTEBOOK = "notebook"
    CODE = "code"


# ============================================================================
# STRATEGY GRAPH
# ============================================================================

class BlockNode(BaseModel):
    """Individual block in strategy graph"""
    id: str = Field(..., description="Unique node ID")
    type: BlockType = Field(..., description="Block type")
    params: Dict[str, Any] = Field(default_factory=dict, description="Block parameters")
    inputs: List[str] = Field(default_factory=list, description="Input node IDs")
    position: Optional[Dict[str, float]] = Field(None, description="UI position {x, y}")


class GraphEdge(BaseModel):
    """Connection between blocks"""
    from_node: str = Field(..., alias="from")
    to_node: str = Field(..., alias="to")
    
    class Config:
        populate_by_name = True


class StrategyGraphCreate(BaseModel):
    """Create new strategy graph"""
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    nodes: List[BlockNode] = Field(..., min_items=1)
    edges: Optional[List[GraphEdge]] = Field(default_factory=list)
    outputs: List[str] = Field(..., min_items=1)
    tags: Optional[List[str]] = Field(default_factory=list)
    is_public: bool = False


class StrategyGraphUpdate(BaseModel):
    """Update strategy graph"""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    nodes: Optional[List[BlockNode]] = None
    edges: Optional[List[GraphEdge]] = None
    outputs: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    is_public: Optional[bool] = None


class StrategyGraphResponse(BaseModel):
    """Strategy graph response"""
    id: str
    user_id: str
    name: str
    description: Optional[str]
    nodes: List[BlockNode]
    edges: List[GraphEdge]
    outputs: List[str]
    graph_sha: str
    version: int
    tags: List[str]
    is_template: bool
    is_public: bool
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True


# ============================================================================
# BACKTEST RUN
# ============================================================================

class WalkForwardConfig(BaseModel):
    """Walk-forward validation configuration"""
    enabled: bool = True
    folds: int = Field(6, ge=2, le=20)
    mode: Literal["rolling", "expanding"] = "rolling"
    train_window_days: int = Field(120, ge=30)
    test_window_days: int = Field(30, ge=7)


class SweepConfig(BaseModel):
    """Parameter sweep configuration"""
    enabled: bool = False
    type: Literal["grid", "random", "optuna"] = "grid"
    parameters: Dict[str, List[Any]] = Field(default_factory=dict)
    max_trials: Optional[int] = Field(None, ge=1, le=1000)
    optimization_metric: str = "sharpe"
    direction: Literal["maximize", "minimize"] = "maximize"


class StressScenario(BaseModel):
    """Stress test scenario"""
    name: str
    fee_multiplier: float = Field(1.0, ge=0.5, le=10.0)
    slippage_multiplier: float = Field(1.0, ge=0.5, le=10.0)
    latency_ms: int = Field(0, ge=0, le=1000)
    gap_shock_pct: Optional[float] = Field(None, ge=-50, le=50)


class RunConfig(BaseModel):
    """Backtest run configuration"""
    # Data
    symbol: str
    timeframe: str = "1m"
    start_date: str  # ISO format
    end_date: str  # ISO format
    
    # Capital
    initial_capital: float = Field(10000, gt=0)
    
    # Seeds for reproducibility
    seeds: Dict[str, int] = Field(default_factory=lambda: {"numpy": 42, "torch": 42})
    
    # Validation
    walk_forward: Optional[WalkForwardConfig] = None
    
    # Optimization
    sweep: Optional[SweepConfig] = None
    
    # Stress tests
    stress_scenarios: List[StressScenario] = Field(default_factory=list)
    
    # Compute
    priority: Literal["interactive", "batch", "low"] = "interactive"
    max_workers: int = Field(1, ge=1, le=16)


class BacktestRunCreate(BaseModel):
    """Create backtest run"""
    strategy_graph_id: str
    config: RunConfig


class BacktestMetrics(BaseModel):
    """Comprehensive backtest metrics"""
    # Returns
    cagr: float
    total_return: float
    
    # Risk-adjusted
    sharpe_ratio: float
    sortino_ratio: float
    calmar_ratio: float
    
    # Risk
    stdev: float
    max_drawdown: float
    max_drawdown_duration_days: Optional[int]
    ulcer_index: Optional[float]
    
    # Trade stats
    total_trades: int
    win_rate: float
    profit_factor: float
    avg_win: float
    avg_loss: float
    expectancy: float
    
    # Exposure
    exposure_pct: float
    turnover: float
    
    # Costs
    total_fees: float
    total_slippage: float


class EquityPoint(BaseModel):
    """Point in equity curve"""
    timestamp: str
    equity: float
    drawdown_pct: float
    trade_count: int


class Trade(BaseModel):
    """Individual trade"""
    entry_time: str
    exit_time: str
    symbol: str
    side: Literal["long", "short"]
    entry_price: float
    exit_price: float
    quantity: float
    pnl: float
    pnl_pct: float
    fees: float
    slippage: float
    mfe: float  # Maximum favorable excursion
    mae: float  # Maximum adverse excursion
    holding_time_hours: float
    reason: Optional[str] = None  # Signal reason or ML probability


class FoldResult(BaseModel):
    """Walk-forward fold result"""
    fold: int
    train_start: str
    train_end: str
    test_start: str
    test_end: str
    metrics: BacktestMetrics
    trade_count: int


class MonteCarloSummary(BaseModel):
    """Monte Carlo simulation summary"""
    n_runs: int
    median_return: float
    p05_return: float
    p25_return: float
    p75_return: float
    p95_return: float
    median_sharpe: float
    p05_sharpe: float
    p95_sharpe: float


class RunWarning(BaseModel):
    """Run diagnostic warning"""
    type: Literal["overfit", "leakage", "low_sample", "high_turnover", "suspicious_metric"]
    message: str
    severity: Literal["info", "warning", "error"]
    details: Optional[Dict[str, Any]] = None


class BacktestRunResponse(BaseModel):
    """Backtest run response"""
    id: str
    user_id: str
    strategy_graph_id: str
    config: RunConfig
    
    # Hashes
    graph_sha: str
    data_sha: Optional[str]
    params_sha: Optional[str]
    repro_id: Optional[str]
    
    # Status
    status: RunStatus
    progress: float
    
    # Results (only if completed)
    metrics: Optional[BacktestMetrics]
    equity_curve: Optional[List[EquityPoint]]
    trades: Optional[List[Trade]]
    folds: Optional[List[FoldResult]]
    mc_summary: Optional[MonteCarloSummary]
    warnings: Optional[List[RunWarning]]
    
    # Timing
    started_at: Optional[datetime]
    finished_at: Optional[datetime]
    duration_seconds: Optional[float]
    created_at: datetime
    
    class Config:
        from_attributes = True


class BacktestRunListItem(BaseModel):
    """Lightweight run list item"""
    id: str
    strategy_graph_id: str
    strategy_name: str
    status: RunStatus
    progress: float
    sharpe: Optional[float]
    cagr: Optional[float]
    max_dd: Optional[float]
    total_trades: Optional[int]
    created_at: datetime
    duration_seconds: Optional[float]


# ============================================================================
# ARTIFACTS
# ============================================================================

class ArtifactCreate(BaseModel):
    """Create artifact"""
    run_id: str
    type: ArtifactType
    name: str
    description: Optional[str]
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ArtifactResponse(BaseModel):
    """Artifact response"""
    id: str
    run_id: str
    user_id: str
    type: ArtifactType
    name: str
    description: Optional[str]
    content_sha: str
    size_bytes: int
    storage_path: str
    metadata: Dict[str, Any]
    created_at: datetime
    
    class Config:
        from_attributes = True


# ============================================================================
# ML MODELS
# ============================================================================

class MLModelCreate(BaseModel):
    """Create ML model"""
    name: str
    model_type: Literal["xgboost", "lightgbm", "sklearn", "torch"]
    task: Literal["classification", "regression"]
    features: List[str]
    target: str
    label_spec: Dict[str, Any]


class MLModelResponse(BaseModel):
    """ML model response"""
    id: str
    user_id: str
    run_id: Optional[str]
    name: str
    model_type: str
    task: str
    features: List[str]
    target: str
    label_spec: Dict[str, Any]
    metrics: Dict[str, Any]
    feature_importances: Dict[str, float]
    version: int
    model_sha: str
    status: str
    created_at: datetime
    trained_at: Optional[datetime]
    
    class Config:
        from_attributes = True


# ============================================================================
# COPILOT
# ============================================================================

class CopilotRequest(BaseModel):
    """AI Copilot request"""
    message: str
    strategy_graph_id: Optional[str] = None
    last_run_id: Optional[str] = None
    context: Dict[str, Any] = Field(default_factory=dict)


class GraphChange(BaseModel):
    """Graph modification operation"""
    op: Literal["add", "update", "remove"]
    target: str  # node_id or "graph.property"
    payload: Optional[Dict[str, Any]] = None


class ExpectedImpact(BaseModel):
    """Expected metric impact from change"""
    metric: str  # sharpe, dd, cagr, etc.
    delta: str  # "+0.2", "-5%"
    confidence: float = Field(..., ge=0, le=1)


class CopilotResponse(BaseModel):
    """AI Copilot response"""
    message: str
    changes: List[GraphChange] = Field(default_factory=list)
    run_proposal: Optional[Dict[str, Any]] = None
    expected_impacts: List[ExpectedImpact] = Field(default_factory=list)
    suggested_next_steps: List[str] = Field(default_factory=list)


# ============================================================================
# TEMPLATES
# ============================================================================

class TemplateResponse(BaseModel):
    """Strategy template response"""
    id: str
    name: str
    description: str
    category: str
    difficulty: str
    graph_template: Dict[str, Any]
    example_config: Dict[str, Any]
    expected_metrics: Dict[str, Any]
    usage_count: int
    is_official: bool
    is_featured: bool
    
    class Config:
        from_attributes = True

