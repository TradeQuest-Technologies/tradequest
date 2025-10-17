"""
Plan limits and feature gating
"""

from fastapi import HTTPException, status, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.core.database import get_db
from app.models.user import User, Subscription
from app.models.trade import Trade
import structlog
from datetime import datetime, timedelta

logger = structlog.get_logger()

# Plan limits configuration
PLAN_LIMITS = {
    "free": {
        "trades_per_month": 50,
        "ai_coaching_sessions_per_month": 5,
        "backtest_runs_per_month": 0,  # No backtesting for free users
        "history_retention_months": 3,  # Only last 3 months of history
        "max_custom_tags": 5,  # Maximum 5 custom tags
        "max_portfolios": 1,  # Only 1 portfolio/account
        "max_note_length": 500,  # 500 character limit on notes
        "features": {
            "basic_journal": True,
            "basic_analytics": True,
            "csv_import": False,  # Free users can only manually add trades
            "json_export": False,
            "excel_export": False,
            "trade_screenshots": False,  # No screenshots for free users
            "trade_attachments": False,  # No file attachments
            "paper_trading": True,
            "advanced_analytics": False,
            "advanced_filters": False,  # Basic filters only
            "unlimited_ai_coach": False,
            "backtesting_studio": False,  # No backtesting for free users
            "advanced_backtesting": False,
            "pdf_reports": False,
            "saved_report_templates": False,
            "priority_support": False,
        }
    },
    "plus": {
        "trades_per_month": None,  # Unlimited
        "ai_coaching_sessions_per_month": None,  # Unlimited
        "backtest_runs_per_month": None,  # Unlimited
        "history_retention_months": None,  # Unlimited history forever
        "max_custom_tags": None,  # Unlimited tags
        "max_portfolios": None,  # Unlimited portfolios
        "max_note_length": None,  # Unlimited note length
        "features": {
            "basic_journal": True,
            "basic_analytics": True,
            "csv_import": True,  # Plus users can import CSV
            "json_export": True,  # Plus users can export JSON
            "excel_export": True,  # Plus users can export Excel
            "trade_screenshots": True,  # Plus users can add screenshots
            "trade_attachments": True,  # Plus users can add file attachments
            "paper_trading": True,
            "advanced_analytics": True,
            "advanced_filters": True,  # Advanced filters and search
            "unlimited_ai_coach": True,
            "backtesting_studio": True,  # Plus users get backtesting studio
            "advanced_backtesting": True,
            "pdf_reports": True,
            "saved_report_templates": True,  # Plus users can save report templates
            "priority_support": True,
        }
    }
}


def get_user_plan(db: Session, user_id: str) -> str:
    """Get user's current plan"""
    subscription = db.query(Subscription).filter(
        Subscription.user_id == user_id
    ).first()
    
    if not subscription:
        return "free"
    
    return subscription.plan


def get_plan_limits(plan: str) -> dict:
    """Get limits for a specific plan"""
    # Handle plus_monthly and plus_yearly as plus plan
    if plan in ["plus_monthly", "plus_yearly"]:
        plan = "plus"
    return PLAN_LIMITS.get(plan, PLAN_LIMITS["free"])


def check_feature_access(db: Session, user_id: str, feature: str) -> bool:
    """Check if user has access to a specific feature"""
    plan = get_user_plan(db, user_id)
    limits = get_plan_limits(plan)
    return limits["features"].get(feature, False)


def check_trade_limit(db: Session, user_id: str) -> dict:
    """Check if user has reached their monthly trade limit"""
    plan = get_user_plan(db, user_id)
    limits = get_plan_limits(plan)
    
    # Unlimited for Plus plan
    if limits["trades_per_month"] is None:
        return {"allowed": True, "remaining": None, "limit": None}
    
    # Count trades for current month
    start_of_month = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    trade_count = db.query(func.count(Trade.id)).filter(
        Trade.user_id == user_id,
        Trade.entry_time >= start_of_month
    ).scalar()
    
    limit = limits["trades_per_month"]
    remaining = max(0, limit - trade_count)
    allowed = trade_count < limit
    
    logger.info(
        "Trade limit check",
        user_id=user_id,
        plan=plan,
        trade_count=trade_count,
        limit=limit,
        remaining=remaining,
        allowed=allowed
    )
    
    return {
        "allowed": allowed,
        "remaining": remaining,
        "limit": limit,
        "current": trade_count
    }


def check_ai_coaching_limit(db: Session, user_id: str) -> dict:
    """Check if user has reached their monthly AI coaching limit"""
    from app.models.onboarding import MarketingProfile  # Import here to avoid circular import
    
    plan = get_user_plan(db, user_id)
    limits = get_plan_limits(plan)
    
    # Unlimited for Plus plan
    if limits["ai_coaching_sessions_per_month"] is None:
        return {"allowed": True, "remaining": None, "limit": None}
    
    # For now, we'll track coaching sessions in a simple way
    # In a full implementation, you'd have a coaching_sessions table
    # For MVP, we'll allow based on plan limits
    
    limit = limits["ai_coaching_sessions_per_month"]
    
    # TODO: Implement actual session counting
    # For now, just return the limit info
    return {
        "allowed": True,  # Always allow for now
        "remaining": limit,
        "limit": limit,
        "current": 0
    }


def require_plan(minimum_plan: str):
    """Dependency to require a specific plan level"""
    async def _require_plan(
        current_user: User = Depends(lambda: None),
        db: Session = Depends(get_db)
    ):
        if not current_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required"
            )
        
        user_plan = get_user_plan(db, current_user.id)
        
        # Plan hierarchy: free < plus < pro
        plan_hierarchy = {"free": 0, "plus": 1, "pro": 2}
        
        if plan_hierarchy.get(user_plan, 0) < plan_hierarchy.get(minimum_plan, 0):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"This feature requires {minimum_plan} plan or higher. Please upgrade your subscription."
            )
        
        return current_user
    
    return _require_plan


def require_feature(feature: str):
    """Dependency to require access to a specific feature"""
    async def _require_feature(
        current_user: User = Depends(lambda: None),
        db: Session = Depends(get_db)
    ):
        if not current_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required"
            )
        
        has_access = check_feature_access(db, current_user.id, feature)
        
        if not has_access:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"This feature is not available in your current plan. Please upgrade to access {feature}."
            )
        
        return current_user
    
    return _require_feature


def check_tags_limit(db: Session, user_id: str, tags_list: list) -> dict:
    """Check if user has reached their custom tags limit"""
    plan = get_user_plan(db, user_id)
    limits = get_plan_limits(plan)
    
    max_tags = limits.get("max_custom_tags")
    
    # Unlimited for Plus plan
    if max_tags is None:
        return {"allowed": True, "limit": None, "current": len(tags_list)}
    
    # Check if tags exceed limit
    num_tags = len(tags_list) if tags_list else 0
    allowed = num_tags <= max_tags
    
    return {
        "allowed": allowed,
        "limit": max_tags,
        "current": num_tags
    }


def check_note_length(db: Session, user_id: str, note_text: str) -> dict:
    """Check if note length exceeds plan limit"""
    plan = get_user_plan(db, user_id)
    limits = get_plan_limits(plan)
    
    max_length = limits.get("max_note_length")
    
    # Unlimited for Plus plan
    if max_length is None:
        return {"allowed": True, "limit": None, "current": len(note_text) if note_text else 0}
    
    # Check if note exceeds limit
    note_length = len(note_text) if note_text else 0
    allowed = note_length <= max_length
    
    return {
        "allowed": allowed,
        "limit": max_length,
        "current": note_length
    }

