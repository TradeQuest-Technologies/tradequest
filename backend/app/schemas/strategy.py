"""
Strategy and backtest schemas
"""

from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime

class StrategyBase(BaseModel):
    name: str
    spec: Dict[str, Any]

class StrategyCreate(StrategyBase):
    pass

class StrategyResponse(StrategyBase):
    id: str
    user_id: str
    created_at: datetime
    
    class Config:
        from_attributes = True

class BacktestRequest(BaseModel):
    symbol: str
    timeframe: str = "1m"
    lookback_bars: int = 1000
    strategy: Dict[str, Any]
    fees_bps: float = 5.0  # 0.05%
    slippage_bps: float = 2.0  # 0.02%

class BacktestResponse(BaseModel):
    id: str
    strategy_id: Optional[str] = None
    created_at: datetime
    metrics: Dict[str, Any]
    equity_curve: List[Dict[str, Any]]
    trades: List[Dict[str, Any]]
    mc_summary: Dict[str, Any]
    
    class Config:
        from_attributes = True

class DailyMetricResponse(BaseModel):
    user_id: str
    day: str
    kpis: Dict[str, Any]
    
    class Config:
        from_attributes = True
