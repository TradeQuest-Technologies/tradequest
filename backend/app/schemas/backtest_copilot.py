"""
Schemas for Advanced Backtest Copilot (Agentic AI System)
"""

from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional, Literal
from datetime import datetime


# ============================================================================
# STREAMING EVENT SCHEMAS
# ============================================================================

class StreamEventBase(BaseModel):
    """Base class for all streaming events"""
    type: str
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class ToolCallEvent(StreamEventBase):
    """Event when AI calls a tool"""
    type: Literal["tool_call"] = "tool_call"
    tool: str
    params: Dict[str, Any]
    call_id: str


class ToolResultEvent(StreamEventBase):
    """Event when tool execution completes"""
    type: Literal["tool_result"] = "tool_result"
    tool: str
    result: Any
    call_id: str
    success: bool = True
    error: Optional[str] = None


class ThinkingEvent(StreamEventBase):
    """Event for AI reasoning/thinking"""
    type: Literal["thinking"] = "thinking"
    content: str


class MessageEvent(StreamEventBase):
    """Event for AI message/response"""
    type: Literal["message"] = "message"
    content: str


class ChartEvent(StreamEventBase):
    """Event when chart is generated"""
    type: Literal["chart"] = "chart"
    chart_id: str
    url: str
    title: str
    description: Optional[str] = None


class ParameterUpdateEvent(StreamEventBase):
    """Event when AI suggests parameter changes"""
    type: Literal["parameter_update"] = "parameter_update"
    params: Dict[str, Any]
    reasoning: str
    requires_approval: bool = True


class BacktestTriggeredEvent(StreamEventBase):
    """Event when new backtest run is triggered"""
    type: Literal["backtest_triggered"] = "backtest_triggered"
    run_id: str
    config: Dict[str, Any]


class ErrorEvent(StreamEventBase):
    """Event for errors"""
    type: Literal["error"] = "error"
    error: str
    details: Optional[str] = None


class DoneEvent(StreamEventBase):
    """Event indicating stream completion"""
    type: Literal["done"] = "done"


# ============================================================================
# REQUEST/RESPONSE SCHEMAS
# ============================================================================

class AnalyzeStreamingRequest(BaseModel):
    """Request for streaming backtest analysis"""
    run_id: str
    user_question: str
    chat_history: List[Dict[str, str]] = Field(default_factory=list)
    context: Dict[str, Any] = Field(default_factory=dict)
    current_tab: Optional[str] = None  # Which tab user is viewing


# ============================================================================
# TOOL PARAMETER SCHEMAS
# ============================================================================

class TradeFilter(BaseModel):
    """Filters for trade queries"""
    symbol: Optional[str] = None
    side: Optional[Literal["long", "short"]] = None
    min_pnl: Optional[float] = None
    max_pnl: Optional[float] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    winners_only: bool = False
    losers_only: bool = False


class ParameterUpdate(BaseModel):
    """Parameter update payload"""
    leverage: Optional[float] = Field(None, ge=1, le=10)
    position_size_percent: Optional[float] = Field(None, ge=1, le=100)
    stop_loss_percent: Optional[float] = Field(None, ge=0, le=100)
    take_profit_percent: Optional[float] = Field(None, ge=0, le=100)
    min_holding_hours: Optional[float] = Field(None, ge=0)
    max_holding_hours: Optional[float] = Field(None, ge=0)
    filter_losers: Optional[bool] = None
    filter_winners: Optional[bool] = None


class BacktestConfig(BaseModel):
    """Configuration for triggering new backtest"""
    strategy_graph_id: str
    symbol: str
    timeframe: str
    start_date: str
    end_date: str
    initial_capital: float = 10000
    parameters: Dict[str, Any] = Field(default_factory=dict)


class ChartConfig(BaseModel):
    """Configuration for chart generation"""
    chart_type: Literal["line", "bar", "scatter", "heatmap", "candlestick"]
    title: str
    data: Dict[str, Any]
    options: Dict[str, Any] = Field(default_factory=dict)


# ============================================================================
# TOOL RESULT SCHEMAS
# ============================================================================

class RunSummary(BaseModel):
    """Summary of a backtest run"""
    id: str
    strategy_graph_id: str
    config: Dict[str, Any]
    metrics: Dict[str, float]
    warnings: List[Dict[str, Any]]
    status: str
    created_at: str


class TradeDetail(BaseModel):
    """Detailed trade information"""
    entry_time: str
    exit_time: str
    symbol: Optional[str]
    side: str
    entry_price: float
    exit_price: float
    quantity: float
    pnl: float
    pnl_pct: float
    fees: float
    slippage: float
    mfe: float
    mae: float
    holding_time_hours: float


class ComparisonResult(BaseModel):
    """Result of comparing multiple runs"""
    runs: List[Dict[str, Any]]
    metrics_comparison: Dict[str, List[float]]
    best_run_id: str
    improvement_pct: Dict[str, float]

