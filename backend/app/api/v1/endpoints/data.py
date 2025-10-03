"""
Data management endpoints (export, delete account)
"""

from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel
import structlog
import json
import zipfile
import io

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.user import User
from app.models.trade import Trade, JournalEntry
from app.models.strategy import Strategy, Backtest

logger = structlog.get_logger()
router = APIRouter()

# Pydantic models
class ExportRequest(BaseModel):
    format: str = "json"  # json, csv, zip
    include_trades: bool = True
    include_journal: bool = True
    include_strategies: bool = True
    include_backtests: bool = True
    date_range: Optional[Dict[str, str]] = None

class DeleteAccountRequest(BaseModel):
    confirmation: str
    reason: Optional[str] = None

@router.post("/export")
async def export_user_data(
    export_request: ExportRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Export all user data"""
    
    try:
        export_data = {
            "user_info": {
                "email": current_user.email,
                "created_at": current_user.created_at.isoformat(),
                "export_date": datetime.utcnow().isoformat()
            },
            "trades": [],
            "journal_entries": [],
            "strategies": [],
            "backtests": []
        }
        
        # Export trades
        if export_request.include_trades:
            trades = db.query(Trade).filter(Trade.user_id == current_user.id).all()
            for trade in trades:
                export_data["trades"].append({
                    "id": str(trade.id),
                    "account": trade.account,
                    "venue": trade.venue,
                    "symbol": trade.symbol,
                    "side": trade.side,
                    "qty": float(trade.qty),
                    "avg_price": float(trade.avg_price),
                    "fees": float(trade.fees),
                    "pnl": float(trade.pnl),
                    "submitted_at": trade.submitted_at.isoformat() if trade.submitted_at else None,
                    "filled_at": trade.filled_at.isoformat(),
                    "order_ref": trade.order_ref,
                    "session_id": trade.session_id,
                    "raw": trade.raw
                })
        
        # Export journal entries
        if export_request.include_journal:
            journal_entries = db.query(JournalEntry).filter(JournalEntry.user_id == current_user.id).all()
            for entry in journal_entries:
                export_data["journal_entries"].append({
                    "id": str(entry.id),
                    "trade_id": str(entry.trade_id) if entry.trade_id else None,
                    "timestamp": entry.ts.isoformat(),
                    "note": entry.note,
                    "tags": entry.tags,
                    "attachments": entry.attachments
                })
        
        # Export strategies
        if export_request.include_strategies:
            strategies = db.query(Strategy).filter(Strategy.user_id == current_user.id).all()
            for strategy in strategies:
                export_data["strategies"].append({
                    "id": str(strategy.id),
                    "name": strategy.name,
                    "spec": strategy.spec,
                    "created_at": strategy.created_at.isoformat()
                })
        
        # Export backtests
        if export_request.include_backtests:
            backtests = db.query(Backtest).filter(Backtest.user_id == current_user.id).all()
            for backtest in backtests:
                export_data["backtests"].append({
                    "id": str(backtest.id),
                    "strategy_id": str(backtest.strategy_id) if backtest.strategy_id else None,
                    "created_at": backtest.created_at.isoformat(),
                    "metrics": backtest.metrics,
                    "equity_curve": backtest.equity_curve,
                    "trades": backtest.trades,
                    "mc_summary": backtest.mc_summary
                })
        
        # Generate export file
        if export_request.format == "json":
            content = json.dumps(export_data, indent=2)
            media_type = "application/json"
            filename = f"tradequest_export_{current_user.id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
            
        elif export_request.format == "zip":
            # Create ZIP file with multiple formats
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                # Add JSON file
                zip_file.writestr("data.json", json.dumps(export_data, indent=2))
                
                # Add CSV files
                if export_data["trades"]:
                    csv_content = _trades_to_csv(export_data["trades"])
                    zip_file.writestr("trades.csv", csv_content)
                
                if export_data["journal_entries"]:
                    csv_content = _journal_to_csv(export_data["journal_entries"])
                    zip_file.writestr("journal.csv", csv_content)
            
            zip_buffer.seek(0)
            content = zip_buffer.getvalue()
            media_type = "application/zip"
            filename = f"tradequest_export_{current_user.id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.zip"
            
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unsupported export format. Use 'json' or 'zip'"
            )
        
        logger.info("Data export completed", user_id=str(current_user.id), format=export_request.format)
        
        return Response(
            content=content,
            media_type=media_type,
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as e:
        logger.error("Data export failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export data: {str(e)}"
        )

@router.post("/delete-account")
async def delete_account(
    delete_request: DeleteAccountRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Request account deletion"""
    
    if delete_request.confirmation != "DELETE":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Confirmation must be 'DELETE'"
        )
    
    try:
        from app.services.email_service import EmailService
        from app.services.session_service import SessionService
        
        # Calculate deletion date (7 days grace period)
        deletion_date = datetime.utcnow() + datetime.timedelta(days=7)
        
        # TODO: Store deletion request in database
        deletion_job = {
            "user_id": str(current_user.id),
            "requested_at": datetime.utcnow().isoformat(),
            "scheduled_deletion": deletion_date.isoformat(),
            "reason": delete_request.reason,
            "status": "pending"
        }
        
        # Send confirmation email
        email_service = EmailService()
        await email_service.send_account_deletion_confirmation(
            current_user.email,
            deletion_date.isoformat()
        )
        
        # Revoke all sessions except current one
        session_service = SessionService()
        revoked_count = session_service.revoke_all_sessions(str(current_user.id))
        
        logger.info("Account deletion requested", 
                   user_id=str(current_user.id),
                   deletion_date=deletion_date.isoformat(),
                   sessions_revoked=revoked_count)
        
        return {
            "message": "Account deletion requested successfully",
            "deletion_scheduled": deletion_job["scheduled_deletion"],
            "grace_period_days": 7,
            "job_id": f"delete_{current_user.id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            "sessions_revoked": revoked_count
        }
        
    except Exception as e:
        logger.error("Account deletion request failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to request account deletion: {str(e)}"
        )

@router.post("/cancel-deletion")
async def cancel_account_deletion(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Cancel pending account deletion"""
    
    try:
        # TODO: Cancel pending deletion job
        
        logger.info("Account deletion cancelled", user_id=str(current_user.id))
        
        return {"message": "Account deletion cancelled successfully"}
        
    except Exception as e:
        logger.error("Account deletion cancellation failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cancel account deletion: {str(e)}"
        )

@router.get("/deletion-status")
async def get_deletion_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get account deletion status"""
    
    # Mock implementation
    status = {
        "deletion_requested": False,
        "scheduled_deletion": None,
        "grace_period_days": 0,
        "can_cancel": False
    }
    
    return status

def _trades_to_csv(trades: list) -> str:
    """Convert trades to CSV format"""
    
    if not trades:
        return ""
    
    # CSV header
    csv_lines = ["id,account,venue,symbol,side,qty,avg_price,fees,pnl,submitted_at,filled_at,order_ref,session_id"]
    
    # CSV rows
    for trade in trades:
        csv_lines.append(f"{trade['id']},{trade['account']},{trade['venue']},{trade['symbol']},{trade['side']},{trade['qty']},{trade['avg_price']},{trade['fees']},{trade['pnl']},{trade['submitted_at']},{trade['filled_at']},{trade['order_ref']},{trade['session_id']}")
    
    return "\n".join(csv_lines)

def _journal_to_csv(journal_entries: list) -> str:
    """Convert journal entries to CSV format"""
    
    if not journal_entries:
        return ""
    
    # CSV header
    csv_lines = ["id,trade_id,timestamp,note,tags,attachments"]
    
    # CSV rows
    for entry in journal_entries:
        csv_lines.append(f"{entry['id']},{entry['trade_id']},{entry['timestamp']},{entry['note']},{entry['tags']},{entry['attachments']}")
    
    return "\n".join(csv_lines)
