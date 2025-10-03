"""
AI orchestrator endpoints for chat tools
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import structlog

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.user import User
from app.models.trade import Trade
from app.services.ai_coach import AICoach
from app.services.market_data import MarketDataService

logger = structlog.get_logger()
router = APIRouter()

@router.get("/tools/get_ohlcv")
async def get_ohlcv_tool(
    symbol: str,
    tf: str = "1m",
    limit: int = 1000,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """AI tool: Get OHLCV data"""
    
    try:
        market_service = MarketDataService()
        candles = await market_service.get_ohlcv(symbol, tf, limit)
        
        return {
            "symbol": symbol,
            "timeframe": tf,
            "candles": candles,
            "count": len(candles)
        }
        
    except Exception as e:
        logger.error("AI tool get_ohlcv failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch OHLCV: {str(e)}"
        )

@router.get("/tools/get_trades")
async def get_trades_tool(
    since_minutes: int = 60,
    symbol: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """AI tool: Get recent trades"""
    
    try:
        since_time = datetime.utcnow() - timedelta(minutes=since_minutes)
        
        query = db.query(Trade).filter(Trade.user_id == current_user.id)
        
        if symbol:
            query = query.filter(Trade.symbol == symbol)
        
        trades = query.filter(Trade.filled_at >= since_time).order_by(Trade.filled_at.desc()).all()
        
        # Convert to dict format
        trades_data = []
        for trade in trades:
            trades_data.append({
                "id": str(trade.id),
                "symbol": trade.symbol,
                "side": trade.side,
                "qty": float(trade.qty),
                "price": float(trade.avg_price),
                "pnl": float(trade.pnl),
                "filled_at": trade.filled_at.isoformat(),
                "venue": trade.venue
            })
        
        return {
            "trades": trades_data,
            "count": len(trades_data),
            "since_minutes": since_minutes
        }
        
    except Exception as e:
        logger.error("AI tool get_trades failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch trades: {str(e)}"
        )

@router.post("/tools/get_trade_context")
async def get_trade_context_tool(
    trade_data: Dict[str, Any],
    tf: str = "1m",
    pre_mins: int = 60,
    post_mins: int = 60,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """AI tool: Get candles around a trade"""
    
    try:
        market_service = MarketDataService()
        
        # Extract trade info
        symbol = trade_data.get("symbol")
        filled_at = trade_data.get("filled_at")
        
        if not symbol or not filled_at:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Trade must include symbol and filled_at"
            )
        
        # Parse datetime if it's a string
        if isinstance(filled_at, str):
            filled_at = datetime.fromisoformat(filled_at.replace('Z', '+00:00'))
        
        # Calculate time window
        start_time = filled_at - timedelta(minutes=pre_mins)
        end_time = filled_at + timedelta(minutes=post_mins)
        
        # Fetch candles
        candles = await market_service.get_ohlcv_range(symbol, tf, start_time, end_time)
        
        return {
            "trade": trade_data,
            "timeframe": tf,
            "pre_mins": pre_mins,
            "post_mins": post_mins,
            "candles": candles,
            "trade_timestamp": filled_at.isoformat()
        }
        
    except Exception as e:
        logger.error("AI tool get_trade_context failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch trade context: {str(e)}"
        )

@router.post("/tools/backtest_quick")
async def backtest_quick_tool(
    symbol: str,
    tf: str = "1m",
    lookback_bars: int = 1000,
    strategy_spec: Dict[str, Any] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """AI tool: Quick backtest"""
    
    try:
        from app.services.backtester import BacktestEngine
        
        if not strategy_spec:
            # Default SMA cross strategy
            strategy_spec = {
                "type": "sma_cross",
                "fast_period": 10,
                "slow_period": 20,
                "position_size": 1.0
            }
        
        engine = BacktestEngine()
        result = await engine.run_backtest(
            symbol=symbol,
            timeframe=tf,
            lookback_bars=lookback_bars,
            strategy=strategy_spec,
            fees_bps=5.0,
            slippage_bps=2.0
        )
        
        return {
            "symbol": symbol,
            "timeframe": tf,
            "strategy": strategy_spec,
            "metrics": result["metrics"],
            "trade_count": len(result["trades"])
        }
        
    except Exception as e:
        logger.error("AI tool backtest_quick failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Quick backtest failed: {str(e)}"
        )

@router.post("/tools/coach_trade")
async def coach_trade_tool(
    trade_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """AI tool: Coach analysis for a specific trade"""
    
    try:
        # Get trade
        trade = db.query(Trade).filter(
            Trade.id == trade_id,
            Trade.user_id == current_user.id
        ).first()
        
        if not trade:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Trade not found"
            )
        
        # Initialize AI coach
        coach = AICoach()
        
        # Analyze trade
        analysis = await coach.analyze_trade(trade, db)
        
        return {
            "trade_id": trade_id,
            "summary": analysis["summary"],
            "action_item": analysis["action_item"],
            "context": analysis.get("context", {})
        }
        
    except Exception as e:
        logger.error("AI tool coach_trade failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Trade coaching failed: {str(e)}"
        )

@router.post("/tools/coach_session")
async def coach_session_tool(
    date: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """AI tool: Coach analysis for a trading session"""
    
    try:
        # Parse date
        session_date = datetime.fromisoformat(date)
        start_time = session_date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_time = start_time + timedelta(days=1)
        
        # Get trades for the day
        trades = db.query(Trade).filter(
            Trade.user_id == current_user.id,
            Trade.filled_at >= start_time,
            Trade.filled_at < end_time
        ).order_by(Trade.filled_at).all()
        
        if not trades:
            return {
                "date": date,
                "summary": "No trades found for this date.",
                "action_item": "Consider reviewing your trading plan and market conditions.",
                "trades_count": 0
            }
        
        # Initialize AI coach
        coach = AICoach()
        
        # Analyze session
        analysis = await coach.analyze_session(trades, db)
        
        return {
            "date": date,
            "summary": analysis["summary"],
            "action_item": analysis["action_item"],
            "trades_count": len(trades),
            "session_metrics": analysis.get("metrics", {})
        }
        
    except Exception as e:
        logger.error("AI tool coach_session failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Session coaching failed: {str(e)}"
        )
