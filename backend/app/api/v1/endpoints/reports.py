"""
Reports generation endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta, date
from pydantic import BaseModel
import structlog
import json

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.user import User
from app.models.trade import Trade
from app.services.pdf_service import PDFService
from app.services.email_service import EmailService

logger = structlog.get_logger()
router = APIRouter()

# Pydantic models
class DailyReport(BaseModel):
    date: str
    trades_count: int
    total_pnl: float
    win_rate: float
    adherence_score: float
    ai_note: str

class WeeklyReport(BaseModel):
    week_start: str
    week_end: str
    consistency_score: float
    total_trades: int
    total_pnl: float
    win_rate: float
    action_items: List[str]
    habits_summary: Dict[str, Any]

class MonthlyReport(BaseModel):
    month: str
    trends: Dict[str, Any]
    regime_shifts: List[str]
    symbol_mix: Dict[str, int]
    performance_summary: Dict[str, Any]

@router.get("/daily")
async def get_daily_report(
    report_date: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get daily report"""
    
    if not report_date:
        report_date = datetime.utcnow().strftime("%Y-%m-%d")
    
    try:
        # Parse date
        target_date = datetime.fromisoformat(report_date).date()
        start_time = datetime.combine(target_date, datetime.min.time())
        end_time = start_time + timedelta(days=1)
        
        # Get trades for the day
        trades = db.query(Trade).filter(
            Trade.user_id == current_user.id,
            Trade.filled_at >= start_time,
            Trade.filled_at < end_time
        ).all()
        
        # Calculate metrics
        trades_count = len(trades)
        total_pnl = sum(trade.pnl for trade in trades)
        winning_trades = [t for t in trades if t.pnl > 0]
        win_rate = len(winning_trades) / trades_count if trades_count > 0 else 0
        
        # Mock adherence score (in real app, this would be calculated from rules)
        adherence_score = 0.85 if trades_count > 0 else 1.0
        
        # Generate AI note
        ai_note = _generate_daily_ai_note(trades_count, total_pnl, win_rate, adherence_score)
        
        report = DailyReport(
            date=report_date,
            trades_count=trades_count,
            total_pnl=total_pnl,
            win_rate=win_rate,
            adherence_score=adherence_score,
            ai_note=ai_note
        )
        
        return report
        
    except Exception as e:
        logger.error("Daily report generation failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate daily report: {str(e)}"
        )

@router.get("/weekly/pdf")
async def get_weekly_pdf_report(
    week_start: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate weekly PDF report"""
    
    if not week_start:
        # Get start of current week
        today = datetime.utcnow().date()
        week_start = (today - timedelta(days=today.weekday())).strftime("%Y-%m-%d")
    
    try:
        # Parse week start
        start_date = datetime.fromisoformat(week_start).date()
        end_date = start_date + timedelta(days=6)
        
        # Get trades for the week
        start_time = datetime.combine(start_date, datetime.min.time())
        end_time = datetime.combine(end_date, datetime.max.time())
        
        trades = db.query(Trade).filter(
            Trade.user_id == current_user.id,
            Trade.filled_at >= start_time,
            Trade.filled_at <= end_time
        ).all()
        
        # Calculate weekly metrics
        total_trades = len(trades)
        total_pnl = sum(trade.pnl for trade in trades)
        winning_trades = [t for t in trades if t.pnl > 0]
        win_rate = len(winning_trades) / total_trades if total_trades > 0 else 0
        
        # Calculate consistency score
        consistency_score = _calculate_consistency_score(trades)
        
        # Generate action items
        action_items = _generate_weekly_action_items(trades, win_rate, consistency_score)
        
        # Generate habits summary
        habits_summary = _generate_habits_summary(trades)
        
        # Create report data
        report_data = WeeklyReport(
            week_start=week_start,
            week_end=end_date.strftime("%Y-%m-%d"),
            consistency_score=consistency_score,
            total_trades=total_trades,
            total_pnl=total_pnl,
            win_rate=win_rate,
            action_items=action_items,
            habits_summary=habits_summary
        )
        
        # Generate actual PDF
        pdf_service = PDFService()
        pdf_content = await pdf_service.generate_weekly_report(report_data.dict())
        
        logger.info("Weekly PDF report generated", user_id=current_user.id, week_start=week_start)
        
        return Response(
            content=pdf_content,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=weekly_report_{week_start}.pdf"
            }
        )
        
    except Exception as e:
        logger.error("Weekly PDF report generation failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate weekly PDF report: {str(e)}"
        )

@router.get("/monthly")
async def get_monthly_report(
    month: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get monthly overview report"""
    
    if not month:
        month = datetime.utcnow().strftime("%Y-%m")
    
    try:
        # Parse month
        year, month_num = map(int, month.split("-"))
        start_date = date(year, month_num, 1)
        
        if month_num == 12:
            end_date = date(year + 1, 1, 1)
        else:
            end_date = date(year, month_num + 1, 1)
        
        start_time = datetime.combine(start_date, datetime.min.time())
        end_time = datetime.combine(end_date, datetime.min.time())
        
        # Get trades for the month
        trades = db.query(Trade).filter(
            Trade.user_id == current_user.id,
            Trade.filled_at >= start_time,
            Trade.filled_at < end_time
        ).all()
        
        # Calculate trends
        trends = _calculate_monthly_trends(trades)
        
        # Identify regime shifts
        regime_shifts = _identify_regime_shifts(trades)
        
        # Analyze symbol mix
        symbol_mix = _analyze_symbol_mix(trades)
        
        # Performance summary
        performance_summary = _calculate_performance_summary(trades)
        
        report = MonthlyReport(
            month=month,
            trends=trends,
            regime_shifts=regime_shifts,
            symbol_mix=symbol_mix,
            performance_summary=performance_summary
        )
        
        return report
        
    except Exception as e:
        logger.error("Monthly report generation failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate monthly report: {str(e)}"
        )

def _generate_daily_ai_note(trades_count: int, total_pnl: float, win_rate: float, adherence_score: float) -> str:
    """Generate AI note for daily report"""
    
    if trades_count == 0:
        return "No trades today. Consider reviewing market conditions and your trading plan."
    
    notes = []
    
    if total_pnl > 0:
        notes.append(f"Profitable day with ${total_pnl:.2f} gain.")
    elif total_pnl < 0:
        notes.append(f"Losing day with ${abs(total_pnl):.2f} loss.")
    
    if win_rate > 0.6:
        notes.append("Strong win rate indicates good trade selection.")
    elif win_rate < 0.4:
        notes.append("Low win rate suggests need for better trade filtering.")
    
    if adherence_score > 0.9:
        notes.append("Excellent rule adherence.")
    elif adherence_score < 0.7:
        notes.append("Consider improving discipline and rule following.")
    
    return " ".join(notes) if notes else "Standard trading day."

def _calculate_consistency_score(trades: List[Trade]) -> float:
    """Calculate consistency score for the week"""
    
    if len(trades) < 2:
        return 1.0
    
    # Simple consistency based on win rate and PnL variance
    win_rate = len([t for t in trades if t.pnl > 0]) / len(trades)
    pnl_values = [t.pnl for t in trades]
    
    # Higher win rate and lower variance = higher consistency
    consistency = win_rate * 0.7 + (1 - (max(pnl_values) - min(pnl_values)) / max(abs(pnl) for pnl in pnl_values if pnl != 0)) * 0.3
    
    return max(0.0, min(1.0, consistency))

def _generate_weekly_action_items(trades: List[Trade], win_rate: float, consistency_score: float) -> List[str]:
    """Generate action items for weekly report"""
    
    action_items = []
    
    if win_rate < 0.5:
        action_items.append("Improve trade selection criteria to increase win rate")
    
    if consistency_score < 0.7:
        action_items.append("Focus on consistent position sizing and risk management")
    
    if len(trades) > 20:
        action_items.append("Consider reducing trade frequency for better quality")
    
    if not action_items:
        action_items.append("Continue current approach - performance is solid")
    
    return action_items

def _generate_habits_summary(trades: List[Trade]) -> Dict[str, Any]:
    """Generate habits summary"""
    
    if not trades:
        return {"message": "No trades to analyze"}
    
    # Analyze trading patterns
    symbols = {}
    hours = {}
    
    for trade in trades:
        # Symbol habits
        if trade.symbol not in symbols:
            symbols[trade.symbol] = 0
        symbols[trade.symbol] += 1
        
        # Hour habits
        hour = trade.filled_at.hour
        if hour not in hours:
            hours[hour] = 0
        hours[hour] += 1
    
    return {
        "most_traded_symbol": max(symbols.items(), key=lambda x: x[1])[0] if symbols else None,
        "most_active_hour": max(hours.items(), key=lambda x: x[1])[0] if hours else None,
        "symbol_diversity": len(symbols),
        "hour_distribution": hours
    }

def _calculate_monthly_trends(trades: List[Trade]) -> Dict[str, Any]:
    """Calculate monthly trends"""
    
    if not trades:
        return {"message": "No trades to analyze"}
    
    # Group trades by week
    weekly_data = {}
    for trade in trades:
        week_start = trade.filled_at.date() - timedelta(days=trade.filled_at.weekday())
        week_key = week_start.strftime("%Y-%m-%d")
        
        if week_key not in weekly_data:
            weekly_data[week_key] = {"trades": 0, "pnl": 0}
        
        weekly_data[week_key]["trades"] += 1
        weekly_data[week_key]["pnl"] += trade.pnl
    
    # Calculate trends
    weeks = sorted(weekly_data.keys())
    if len(weeks) < 2:
        return {"message": "Insufficient data for trend analysis"}
    
    first_week_pnl = weekly_data[weeks[0]]["pnl"]
    last_week_pnl = weekly_data[weeks[-1]]["pnl"]
    
    pnl_trend = "improving" if last_week_pnl > first_week_pnl else "declining"
    
    return {
        "pnl_trend": pnl_trend,
        "weekly_data": weekly_data,
        "total_weeks": len(weeks)
    }

def _identify_regime_shifts(trades: List[Trade]) -> List[str]:
    """Identify regime shifts in trading"""
    
    shifts = []
    
    if len(trades) < 10:
        return ["Insufficient data for regime analysis"]
    
    # Simple regime shift detection based on volatility
    pnl_values = [t.pnl for t in trades]
    
    # Calculate rolling volatility (simplified)
    if len(pnl_values) > 5:
        recent_vol = sum(abs(pnl) for pnl in pnl_values[-5:]) / 5
        earlier_vol = sum(abs(pnl) for pnl in pnl_values[:5]) / 5
        
        if recent_vol > earlier_vol * 1.5:
            shifts.append("Increased volatility detected in recent trades")
        elif recent_vol < earlier_vol * 0.5:
            shifts.append("Decreased volatility - more conservative trading")
    
    return shifts if shifts else ["No significant regime shifts detected"]

def _analyze_symbol_mix(trades: List[Trade]) -> Dict[str, int]:
    """Analyze symbol trading mix"""
    
    symbol_counts = {}
    for trade in trades:
        if trade.symbol not in symbol_counts:
            symbol_counts[trade.symbol] = 0
        symbol_counts[trade.symbol] += 1
    
    return symbol_counts

def _calculate_performance_summary(trades: List[Trade]) -> Dict[str, Any]:
    """Calculate performance summary"""
    
    if not trades:
        return {"message": "No trades to analyze"}
    
    total_trades = len(trades)
    total_pnl = sum(trade.pnl for trade in trades)
    winning_trades = [t for t in trades if t.pnl > 0]
    losing_trades = [t for t in trades if t.pnl < 0]
    
    win_rate = len(winning_trades) / total_trades if total_trades > 0 else 0
    avg_win = sum(t.pnl for t in winning_trades) / len(winning_trades) if winning_trades else 0
    avg_loss = sum(t.pnl for t in losing_trades) / len(losing_trades) if losing_trades else 0
    
    return {
        "total_trades": total_trades,
        "total_pnl": total_pnl,
        "win_rate": win_rate,
        "avg_win": avg_win,
        "avg_loss": avg_loss,
        "profit_factor": abs(avg_win / avg_loss) if avg_loss != 0 else 0
    }
