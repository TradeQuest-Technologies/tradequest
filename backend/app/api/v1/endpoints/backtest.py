"""
Backtesting endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any
import structlog

from app.core.database import get_db
from app.core.auth import get_current_user
from app.core.plan_gates import check_backtest_limit
from app.schemas.strategy import BacktestRequest, BacktestResponse, StrategyCreate, StrategyResponse
from app.models.user import User
from app.models.strategy import Strategy, Backtest
from app.services.backtester import BacktestEngine

logger = structlog.get_logger()
router = APIRouter()

@router.post("/run", response_model=BacktestResponse)
async def run_backtest(
    request: BacktestRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Run a backtest"""
    
    # Check plan limits
    if not check_backtest_limit(current_user, db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Backtest limit reached for your plan. Upgrade to run more backtests."
        )
    
    try:
        # Initialize backtest engine
        engine = BacktestEngine()
        
        # Run backtest
        result = await engine.run_backtest(
            symbol=request.symbol,
            timeframe=request.timeframe,
            lookback_bars=request.lookback_bars,
            strategy=request.strategy,
            fees_bps=request.fees_bps,
            slippage_bps=request.slippage_bps
        )
        
        # Save backtest result
        backtest = Backtest(
            user_id=current_user.id,
            metrics=result["metrics"],
            equity_curve=result["equity_curve"],
            trades=result["trades"],
            mc_summary=result["mc_summary"]
        )
        
        db.add(backtest)
        db.commit()
        db.refresh(backtest)
        
        logger.info("Backtest completed", user_id=str(current_user.id), backtest_id=str(backtest.id))
        
        return BacktestResponse.from_orm(backtest)
        
    except Exception as e:
        logger.error("Backtest failed", user_id=str(current_user.id), error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Backtest failed: {str(e)}"
        )

@router.post("/quick", response_model=BacktestResponse)
async def quick_backtest(
    request: BacktestRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Run a quick backtest (limited data)"""
    
    # Limit lookback for quick backtests
    request.lookback_bars = min(request.lookback_bars, 1000)
    
    return await run_backtest(request, current_user, db)

@router.post("/strategies", response_model=StrategyResponse)
async def create_strategy(
    strategy_data: StrategyCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new strategy"""
    
    strategy = Strategy(
        user_id=current_user.id,
        name=strategy_data.name,
        spec=strategy_data.spec
    )
    
    db.add(strategy)
    db.commit()
    db.refresh(strategy)
    
    logger.info("Strategy created", user_id=str(current_user.id), strategy_id=str(strategy.id))
    
    return StrategyResponse.from_orm(strategy)

@router.get("/strategies", response_model=List[StrategyResponse])
async def get_strategies(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's strategies"""
    
    strategies = db.query(Strategy).filter(Strategy.user_id == current_user.id).all()
    
    return [StrategyResponse.from_orm(strategy) for strategy in strategies]

@router.get("/backtests", response_model=List[BacktestResponse])
async def get_backtests(
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's backtests"""
    
    backtests = db.query(Backtest).filter(
        Backtest.user_id == current_user.id
    ).order_by(Backtest.created_at.desc()).limit(limit).all()
    
    return [BacktestResponse.from_orm(backtest) for backtest in backtests]

@router.get("/strategies/templates")
async def get_strategy_templates():
    """Get available strategy templates"""
    
    templates = {
        "sma_cross": {
            "name": "SMA Cross",
            "description": "Simple Moving Average crossover strategy",
            "spec": {
                "type": "sma_cross",
                "fast_period": 10,
                "slow_period": 20,
                "position_size": 1.0
            }
        },
        "rsi_revert": {
            "name": "RSI Mean Reversion",
            "description": "RSI-based mean reversion strategy",
            "spec": {
                "type": "rsi_revert",
                "rsi_period": 14,
                "oversold": 30,
                "overbought": 70,
                "position_size": 1.0
            }
        },
        "atr_trail": {
            "name": "ATR Trailing Stop",
            "description": "ATR-based trailing stop strategy",
            "spec": {
                "type": "atr_trail",
                "atr_period": 14,
                "atr_multiplier": 2.0,
                "position_size": 1.0
            }
        }
    }
    
    return templates
