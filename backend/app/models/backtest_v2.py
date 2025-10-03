"""
Enhanced Backtesting Models v2
Supports: Block-based strategies, ML models, walk-forward validation, artifacts, versioning
"""

from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Integer, Float, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from app.core.database import Base
from app.core.database_utils import create_json_column


class StrategyGraph(Base):
    """Block-based strategy graph (node/edge representation)"""
    __tablename__ = "strategy_graphs"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text)
    
    # Graph structure (nodes + edges)
    nodes = create_json_column(nullable=False)  # [{"id": "data1", "type": "data.loader", "params": {...}, "inputs": []}]
    edges = create_json_column()  # [{"from": "data1", "to": "feat1"}]
    outputs = create_json_column()  # ["exec1"] - output node IDs
    
    # Versioning & reproducibility
    graph_sha = Column(String, nullable=False, index=True)  # SHA-256 of nodes+edges
    version = Column(Integer, default=1)
    parent_id = Column(String, ForeignKey("strategy_graphs.id"))  # For version history
    
    # Metadata
    tags = create_json_column()  # ["mean-reversion", "ml", "crypto"]
    is_template = Column(Boolean, default=False)
    is_public = Column(Boolean, default=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User")
    runs = relationship("BacktestRun", back_populates="strategy_graph", cascade="all, delete-orphan")
    parent = relationship("StrategyGraph", remote_side=[id])


class BacktestRun(Base):
    """Individual backtest run with full reproducibility"""
    __tablename__ = "backtest_runs"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    strategy_graph_id = Column(String, ForeignKey("strategy_graphs.id", ondelete="CASCADE"), nullable=False)
    
    # Run configuration
    config = create_json_column(nullable=False)  # {"seeds": {...}, "wf": {...}, "sweeps": {...}, "stress": [...]}
    
    # Data hashes for reproducibility
    graph_sha = Column(String, nullable=False)
    data_sha = Column(String)  # Hash of OHLCV data used
    params_sha = Column(String)  # Hash of all parameters
    code_sha = Column(String)  # Hash of custom code (if any)
    repro_id = Column(String, unique=True, index=True)  # Combined hash for exact reproduction
    
    # Execution status
    status = Column(String, default="queued")  # queued, preparing, running, aggregating, completed, failed, canceled
    progress = Column(Float, default=0.0)  # 0-100%
    
    # Results
    metrics = create_json_column()  # {"cagr": 0.23, "sharpe": 1.42, "max_dd": -0.18, ...}
    equity_curve = create_json_column()  # [{"timestamp": "...", "equity": 10500, ...}]
    drawdown_curve = create_json_column()
    trades = create_json_column()  # [{"entry_time": "...", "exit_time": "...", "pnl": 123.45, "mfe": 200, "mae": -50, ...}]
    
    # Walk-forward folds
    folds = create_json_column()  # [{"fold": 1, "train_window": "...", "test_window": "...", "metrics": {...}, "chart_refs": [...]}]
    
    # Monte Carlo results
    mc_summary = create_json_column()  # {"median": 15000, "p05": 12000, "p95": 18000, "runs": 10000}
    mc_confidence_bands = create_json_column()  # [{"timestamp": "...", "p05": ..., "median": ..., "p95": ...}]
    
    # Performance & diagnostics
    warnings = create_json_column()  # [{"type": "overfit", "message": "Win rate > 95%", "severity": "high"}]
    diagnostics = create_json_column()  # {"slippage_cost": 234, "fees_paid": 123, "turnover": 12.3, ...}
    
    # Timing
    started_at = Column(DateTime(timezone=True))
    finished_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    duration_seconds = Column(Float)
    
    # Compute resources
    priority = Column(String, default="interactive")  # interactive, batch, low
    max_workers = Column(Integer, default=1)
    
    # Relationships
    user = relationship("User")
    strategy_graph = relationship("StrategyGraph", back_populates="runs")
    artifacts = relationship("BacktestArtifact", back_populates="run")
    sweep_results = relationship("ParameterSweepResult", back_populates="run")


class BacktestArtifact(Base):
    """Versioned artifacts (models, datasets, charts, reports)"""
    __tablename__ = "backtest_artifacts"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    run_id = Column(String, ForeignKey("backtest_runs.id"), nullable=False)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    
    # Artifact metadata
    type = Column(String, nullable=False)  # model, dataset, chart, report, notebook, code
    name = Column(String, nullable=False)
    description = Column(Text)
    
    # Content addressing
    content_sha = Column(String, nullable=False, index=True)
    size_bytes = Column(Integer)
    
    # Storage
    storage_path = Column(String, nullable=False)  # S3/local path
    mime_type = Column(String)
    
    # Artifact metadata
    artifact_metadata = create_json_column()  # Type-specific metadata (e.g., model: {"features": [...], "accuracy": 0.87})
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User")
    run = relationship("BacktestRun", back_populates="artifacts")


class MLModel(Base):
    """Machine learning model registry"""
    __tablename__ = "ml_models"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    run_id = Column(String, ForeignKey("backtest_runs.id"))
    
    # Model metadata
    name = Column(String, nullable=False)
    model_type = Column(String, nullable=False)  # xgboost, lightgbm, sklearn, torch
    task = Column(String, nullable=False)  # classification, regression
    
    # Training configuration
    features = Column(JSON, nullable=False)  # ["rsi_14", "macd", "volume_sma", ...]
    target = Column(String, nullable=False)  # "next_bar_return_sign"
    label_spec = Column(JSON)  # {"type": "triple_barrier", "profit_take": 0.02, "stop_loss": -0.01, "max_hold": 48}
    
    # Performance metrics
    metrics = Column(JSON)  # {"train": {"auc": 0.87, ...}, "val": {"auc": 0.83, ...}, "test": {"auc": 0.81, ...}}
    feature_importances = Column(JSON)  # {"rsi_14": 0.35, "macd": 0.28, ...}
    
    # Versioning
    version = Column(Integer, default=1)
    model_sha = Column(String, nullable=False, index=True)
    data_sha = Column(String)  # Hash of training data
    
    # Storage
    storage_path = Column(String, nullable=False)
    size_bytes = Column(Integer)
    
    # Status
    status = Column(String, default="training")  # training, ready, archived, failed
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    trained_at = Column(DateTime(timezone=True))
    
    # Relationships
    user = relationship("User")
    run = relationship("BacktestRun")


class ParameterSweepResult(Base):
    """Results from parameter optimization sweeps"""
    __tablename__ = "parameter_sweep_results"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    run_id = Column(String, ForeignKey("backtest_runs.id"), nullable=False)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    
    # Sweep configuration
    sweep_type = Column(String, nullable=False)  # grid, random, optuna
    parameters = Column(JSON, nullable=False)  # {"rsi.period": [10, 14, 20], "stop_atr_mult": [1.5, 2.0, 2.5]}
    
    # Individual run result
    param_values = Column(JSON, nullable=False)  # {"rsi.period": 14, "stop_atr_mult": 2.0}
    metrics = Column(JSON, nullable=False)  # {"sharpe": 1.42, "cagr": 0.23, ...}
    
    # Ranking
    rank = Column(Integer)  # 1 = best
    score = Column(Float)  # Optimization score (e.g., Sharpe)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User")
    run = relationship("BacktestRun", back_populates="sweep_results")


class DataCache(Base):
    """OHLCV data cache with versioning"""
    __tablename__ = "data_cache"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Cache key
    symbol = Column(String, nullable=False, index=True)
    timeframe = Column(String, nullable=False, index=True)
    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True), nullable=False)
    
    # Content hash
    data_sha = Column(String, unique=True, nullable=False, index=True)
    
    # Storage
    storage_path = Column(String, nullable=False)
    size_bytes = Column(Integer)
    row_count = Column(Integer)
    
    # Metadata
    source = Column(String)  # binance_vision, polygon, ccxt
    quality_score = Column(Float)  # 0-1, based on data completeness
    
    # Cache management
    access_count = Column(Integer, default=0)
    last_accessed_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True))


class BacktestTemplate(Base):
    """Pre-built strategy templates"""
    __tablename__ = "backtest_templates"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Template metadata
    name = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    category = Column(String, nullable=False)  # mean_reversion, trend_following, ml, statistical_arb
    difficulty = Column(String, default="beginner")  # beginner, intermediate, advanced
    
    # Template graph
    graph_template = Column(JSON, nullable=False)  # StrategyGraph nodes/edges with parameter placeholders
    
    # Example configuration
    example_config = Column(JSON)
    expected_metrics = Column(JSON)  # Typical performance ranges
    
    # Usage stats
    usage_count = Column(Integer, default=0)
    avg_rating = Column(Float)
    
    # Visibility
    is_official = Column(Boolean, default=False)
    is_featured = Column(Boolean, default=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

