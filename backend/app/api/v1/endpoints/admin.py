"""
Admin control panel endpoints - protected with password
"""

from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import Dict, Any, Optional
import structlog
from pydantic import BaseModel
from datetime import datetime, timedelta

from app.core.database import get_db
from app.models.user import User, Subscription
from app.models.trade import Trade
from app.services.stripe_service import StripeService

logger = structlog.get_logger()
router = APIRouter()

# Admin password
ADMIN_PASSWORD = "TRADE!@#$%^"

def verify_admin_password(x_admin_password: Optional[str] = Header(None)):
    """Verify admin password from header"""
    if not x_admin_password or x_admin_password != ADMIN_PASSWORD:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid admin password"
        )
    return True

class UpdateSubscriptionRequest(BaseModel):
    user_id: str
    plan: str
    status: str

class UpdateUserRequest(BaseModel):
    email: Optional[str] = None
    onboarding_completed: Optional[bool] = None

@router.get("/dashboard")
async def get_admin_dashboard(
    db: Session = Depends(get_db),
    _: bool = Depends(verify_admin_password)
):
    """Get comprehensive admin dashboard overview"""
    
    # User statistics
    total_users = db.query(func.count(User.id)).scalar()
    users_today = db.query(func.count(User.id)).filter(
        User.created_at >= datetime.utcnow() - timedelta(days=1)
    ).scalar()
    users_this_week = db.query(func.count(User.id)).filter(
        User.created_at >= datetime.utcnow() - timedelta(days=7)
    ).scalar()
    users_this_month = db.query(func.count(User.id)).filter(
        User.created_at >= datetime.utcnow() - timedelta(days=30)
    ).scalar()
    
    # Subscription statistics
    total_subscriptions = db.query(func.count(Subscription.user_id)).scalar()
    active_subscriptions = db.query(func.count(Subscription.user_id)).filter(
        Subscription.status == "active"
    ).scalar()
    
    subscriptions_by_plan = db.query(
        Subscription.plan,
        func.count(Subscription.user_id).label('count')
    ).group_by(Subscription.plan).all()
    
    # Trade statistics
    total_trades = db.query(func.count(Trade.id)).scalar()
    trades_today = db.query(func.count(Trade.id)).filter(
        Trade.entry_date >= datetime.utcnow().date()
    ).scalar()
    trades_this_week = db.query(func.count(Trade.id)).filter(
        Trade.entry_date >= (datetime.utcnow() - timedelta(days=7)).date()
    ).scalar()
    
    # Revenue (estimate based on active subscriptions)
    plus_monthly_count = db.query(func.count(Subscription.user_id)).filter(
        Subscription.plan == "plus_monthly",
        Subscription.status == "active"
    ).scalar() or 0
    plus_yearly_count = db.query(func.count(Subscription.user_id)).filter(
        Subscription.plan == "plus_yearly",
        Subscription.status == "active"
    ).scalar() or 0
    
    mrr = (plus_monthly_count * 29) + (plus_yearly_count * 24.17)  # 290/12
    arr = mrr * 12
    
    # Recent users
    recent_users = db.query(User).order_by(desc(User.created_at)).limit(10).all()
    
    return {
        "users": {
            "total": total_users,
            "today": users_today,
            "this_week": users_this_week,
            "this_month": users_this_month,
            "recent": [
                {
                    "id": str(user.id),
                    "email": user.email,
                    "created_at": user.created_at.isoformat() if user.created_at else None,
                    "onboarding_completed": user.onboarding_completed
                }
                for user in recent_users
            ]
        },
        "subscriptions": {
            "total": total_subscriptions,
            "active": active_subscriptions,
            "by_plan": {plan: count for plan, count in subscriptions_by_plan}
        },
        "trades": {
            "total": total_trades,
            "today": trades_today,
            "this_week": trades_this_week
        },
        "revenue": {
            "mrr": round(mrr, 2),
            "arr": round(arr, 2),
            "plus_monthly_subs": plus_monthly_count,
            "plus_yearly_subs": plus_yearly_count
        }
    }

@router.get("/users")
async def get_all_users(
    skip: int = 0,
    limit: int = 50,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    _: bool = Depends(verify_admin_password)
):
    """Get all users with optional search"""
    
    query = db.query(User)
    
    if search:
        query = query.filter(User.email.contains(search))
    
    total = query.count()
    users = query.order_by(desc(User.created_at)).offset(skip).limit(limit).all()
    
    # Get subscription info for each user
    user_data = []
    for user in users:
        subscription = db.query(Subscription).filter(Subscription.user_id == user.id).first()
        trade_count = db.query(func.count(Trade.id)).filter(Trade.user_id == user.id).scalar()
        
        user_data.append({
            "id": str(user.id),
            "email": user.email,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "onboarding_completed": user.onboarding_completed,
            "region": user.region,
            "subscription": {
                "plan": subscription.plan if subscription else "free",
                "status": subscription.status if subscription else "none",
                "stripe_customer": subscription.stripe_customer if subscription else None
            } if subscription else {"plan": "free", "status": "none"},
            "trade_count": trade_count
        })
    
    return {
        "total": total,
        "users": user_data,
        "page": skip // limit + 1,
        "per_page": limit
    }

@router.get("/users/{user_id}")
async def get_user_details(
    user_id: str,
    db: Session = Depends(get_db),
    _: bool = Depends(verify_admin_password)
):
    """Get detailed information about a specific user"""
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    subscription = db.query(Subscription).filter(Subscription.user_id == user.id).first()
    trades = db.query(Trade).filter(Trade.user_id == user.id).order_by(desc(Trade.entry_date)).limit(20).all()
    
    return {
        "user": {
            "id": str(user.id),
            "email": user.email,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "onboarding_completed": user.onboarding_completed,
            "onboarding_completed_at": user.onboarding_completed_at.isoformat() if user.onboarding_completed_at else None,
            "region": user.region,
            "totp_enabled": user.totp_enabled
        },
        "subscription": {
            "plan": subscription.plan if subscription else "free",
            "status": subscription.status if subscription else "none",
            "stripe_customer": subscription.stripe_customer if subscription else None,
            "stripe_subscription": subscription.stripe_subscription if subscription else None
        } if subscription else None,
        "trades": [
            {
                "id": str(trade.id),
                "symbol": trade.symbol,
                "side": trade.side,
                "entry_date": trade.entry_date.isoformat() if trade.entry_date else None,
                "profit_loss": float(trade.profit_loss) if trade.profit_loss else None
            }
            for trade in trades
        ]
    }

@router.post("/users/{user_id}/subscription")
async def update_user_subscription(
    user_id: str,
    request: UpdateSubscriptionRequest,
    db: Session = Depends(get_db),
    _: bool = Depends(verify_admin_password)
):
    """Update a user's subscription (manual override)"""
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    subscription = db.query(Subscription).filter(Subscription.user_id == user.id).first()
    
    if subscription:
        subscription.plan = request.plan
        subscription.status = request.status
    else:
        subscription = Subscription(
            user_id=user.id,
            plan=request.plan,
            status=request.status
        )
        db.add(subscription)
    
    db.commit()
    
    logger.info("Admin updated subscription", user_id=user_id, plan=request.plan, status=request.status)
    
    return {
        "success": True,
        "subscription": {
            "plan": subscription.plan,
            "status": subscription.status
        }
    }

@router.patch("/users/{user_id}")
async def update_user(
    user_id: str,
    request: UpdateUserRequest,
    db: Session = Depends(get_db),
    _: bool = Depends(verify_admin_password)
):
    """Update user details"""
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if request.email:
        user.email = request.email
    
    if request.onboarding_completed is not None:
        user.onboarding_completed = request.onboarding_completed
    
    db.commit()
    
    logger.info("Admin updated user", user_id=user_id)
    
    return {
        "success": True,
        "user": {
            "id": str(user.id),
            "email": user.email,
            "onboarding_completed": user.onboarding_completed
        }
    }

@router.delete("/users/{user_id}")
async def delete_user(
    user_id: str,
    db: Session = Depends(get_db),
    _: bool = Depends(verify_admin_password)
):
    """Delete a user and all their data"""
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Delete subscription
    db.query(Subscription).filter(Subscription.user_id == user.id).delete()
    
    # Delete trades
    db.query(Trade).filter(Trade.user_id == user.id).delete()
    
    # Delete user
    db.delete(user)
    db.commit()
    
    logger.warning("Admin deleted user", user_id=user_id, email=user.email)
    
    return {"success": True, "message": f"User {user.email} deleted"}

@router.post("/sync-stripe")
async def sync_all_stripe_subscriptions(
    db: Session = Depends(get_db),
    _: bool = Depends(verify_admin_password)
):
    """Sync all subscriptions from Stripe"""
    
    import stripe
    
    synced = 0
    errors = []
    
    try:
        # Get all subscriptions from Stripe
        subscriptions = stripe.Subscription.list(limit=100)
        
        for stripe_sub in subscriptions.auto_paging_iter():
            try:
                customer_id = stripe_sub.customer
                customer = stripe.Customer.retrieve(customer_id)
                email = customer.email
                
                if not email:
                    continue
                
                # Find user by email
                user = db.query(User).filter(User.email == email).first()
                if not user:
                    continue
                
                # Update or create subscription
                subscription = db.query(Subscription).filter(Subscription.user_id == user.id).first()
                
                if subscription:
                    subscription.stripe_customer = customer_id
                    subscription.stripe_subscription = stripe_sub.id
                    subscription.status = stripe_sub.status
                    # Determine plan from price
                    if stripe_sub.items.data:
                        price_id = stripe_sub.items.data[0].price.id
                        if "monthly" in price_id.lower() or stripe_sub.items.data[0].price.recurring.interval == "month":
                            subscription.plan = "plus_monthly"
                        else:
                            subscription.plan = "plus_yearly"
                else:
                    subscription = Subscription(
                        user_id=user.id,
                        stripe_customer=customer_id,
                        stripe_subscription=stripe_sub.id,
                        status=stripe_sub.status,
                        plan="plus_monthly"  # Default
                    )
                    db.add(subscription)
                
                synced += 1
                
            except Exception as e:
                errors.append(f"Error syncing subscription {stripe_sub.id}: {str(e)}")
        
        db.commit()
        
        return {
            "success": True,
            "synced": synced,
            "errors": errors
        }
        
    except Exception as e:
        logger.error("Stripe sync failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Stripe sync failed: {str(e)}"
        )

@router.get("/stats")
async def get_platform_stats(
    db: Session = Depends(get_db),
    _: bool = Depends(verify_admin_password)
):
    """Get detailed platform statistics"""
    
    # User growth over time
    user_growth = []
    for days_ago in range(30, 0, -1):
        date = datetime.utcnow() - timedelta(days=days_ago)
        count = db.query(func.count(User.id)).filter(
            User.created_at <= date
        ).scalar()
        user_growth.append({
            "date": date.date().isoformat(),
            "total_users": count
        })
    
    # Subscription breakdown
    subscription_stats = db.query(
        Subscription.plan,
        Subscription.status,
        func.count(Subscription.user_id).label('count')
    ).group_by(Subscription.plan, Subscription.status).all()
    
    # Top traders by trade count
    top_traders = db.query(
        User.email,
        func.count(Trade.id).label('trade_count')
    ).join(Trade, User.id == Trade.user_id).group_by(User.email).order_by(desc('trade_count')).limit(10).all()
    
    return {
        "user_growth": user_growth,
        "subscription_breakdown": [
            {"plan": plan, "status": status, "count": count}
            for plan, status, count in subscription_stats
        ],
        "top_traders": [
            {"email": email, "trade_count": count}
            for email, count in top_traders
        ]
    }

