"""
Plan gates middleware for feature access control
"""

from fastapi import HTTPException, status, Depends
from sqlalchemy.orm import Session
from typing import Dict, Any
from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.user import User, Subscription
import structlog

logger = structlog.get_logger()

class PlanGates:
    """Plan-based feature access control"""
    
    # Plan limits
    PLAN_LIMITS = {
        "free": {
            "backtests_per_day": 1,
            "broker_sync": False,
            "ai_coach_per_trade": False,
            "weekly_reports": False,
            "alerts": False,
            "strategy_sharing": False
        },
        "plus": {
            "backtests_per_day": 10,
            "broker_sync": True,
            "ai_coach_per_trade": True,
            "weekly_reports": True,
            "alerts": False,
            "strategy_sharing": False
        },
        "pro": {
            "backtests_per_day": -1,  # Unlimited
            "broker_sync": True,
            "ai_coach_per_trade": True,
            "weekly_reports": True,
            "alerts": True,
            "strategy_sharing": True
        }
    }
    
    @staticmethod
    def get_user_plan(user: User, db: Session) -> str:
        """Get user's current plan"""
        subscription = db.query(Subscription).filter(Subscription.user_id == user.id).first()
        return subscription.plan if subscription else "free"
    
    @staticmethod
    def check_feature_access(user: User, feature: str, db: Session) -> bool:
        """Check if user has access to a feature"""
        plan = PlanGates.get_user_plan(user, db)
        limits = PlanGates.PLAN_LIMITS.get(plan, PlanGates.PLAN_LIMITS["free"])
        
        return limits.get(feature, False)
    
    @staticmethod
    def check_usage_limit(user: User, feature: str, current_usage: int, db: Session) -> bool:
        """Check if user is within usage limits"""
        plan = PlanGates.get_user_plan(user, db)
        limits = PlanGates.PLAN_LIMITS.get(plan, PlanGates.PLAN_LIMITS["free"])
        
        limit = limits.get(feature, 0)
        
        # -1 means unlimited
        if limit == -1:
            return True
        
        return current_usage < limit

def require_plan(required_plan: str):
    """Decorator to require minimum plan level"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Extract user and db from kwargs
            user = kwargs.get('current_user')
            db = kwargs.get('db')
            
            if not user or not db:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Missing user or database session"
                )
            
            plan = PlanGates.get_user_plan(user, db)
            plan_hierarchy = {"free": 0, "plus": 1, "pro": 2}
            
            if plan_hierarchy.get(plan, 0) < plan_hierarchy.get(required_plan, 0):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"This feature requires {required_plan} plan or higher"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator

def require_feature(feature: str):
    """Decorator to require specific feature access"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            user = kwargs.get('current_user')
            db = kwargs.get('db')
            
            if not user or not db:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Missing user or database session"
                )
            
            if not PlanGates.check_feature_access(user, feature, db):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"This feature is not available on your current plan"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator

# Convenience functions for common checks
def check_backtest_limit(user: User, db: Session) -> bool:
    """Check if user can run more backtests today"""
    # TODO: Implement daily usage tracking
    # For now, just check plan limits
    plan = PlanGates.get_user_plan(user, db)
    limits = PlanGates.PLAN_LIMITS.get(plan, PlanGates.PLAN_LIMITS["free"])
    return limits.get("backtests_per_day", 0) > 0

def check_broker_sync_access(user: User, db: Session) -> bool:
    """Check if user can sync brokers"""
    return PlanGates.check_feature_access(user, "broker_sync", db)

def check_ai_coach_access(user: User, db: Session) -> bool:
    """Check if user can use AI coach per trade"""
    return PlanGates.check_feature_access(user, "ai_coach_per_trade", db)
