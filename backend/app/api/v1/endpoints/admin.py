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
from app.core.config import settings
from app.models.user import User, Subscription
from app.models.trade import Trade
from app.models.social import CommunityPost, CommunityInsight
from app.services.stripe_service import StripeService
from datetime import timezone
from fastapi import Request

logger = structlog.get_logger()
router = APIRouter()

# Admin rate limiting (stricter than global)
_admin_failed_attempts = {}  # {ip: [timestamps]}
_admin_lockout_until = {}  # {ip: timestamp}

def _check_admin_rate_limit(ip_address: str) -> bool:
    """Check if IP is rate limited for admin endpoints - 5 attempts = 1 hour lockout"""
    import time
    current_time = time.time()
    
    # Check if IP is locked out
    if ip_address in _admin_lockout_until:
        if current_time < _admin_lockout_until[ip_address]:
            return False  # Still locked out
        else:
            # Lockout expired, clear it
            del _admin_lockout_until[ip_address]
            _admin_failed_attempts[ip_address] = []
    
    # Clean old failed attempts (older than 1 hour)
    if ip_address in _admin_failed_attempts:
        _admin_failed_attempts[ip_address] = [
            ts for ts in _admin_failed_attempts[ip_address]
            if ts > current_time - 3600  # 1 hour
        ]
    
    # Check if too many failed attempts (5 attempts = lockout for 1 hour)
    if ip_address in _admin_failed_attempts:
        recent_failures = [
            ts for ts in _admin_failed_attempts[ip_address]
            if ts > current_time - 3600  # 1 hour window
        ]
        if len(recent_failures) >= 5:
            # Lockout for 1 hour
            _admin_lockout_until[ip_address] = current_time + 3600
            logger.warning("Admin endpoint locked out due to too many failed attempts", ip_address=ip_address)
            return False
    
    return True

def _record_admin_failed_attempt(ip_address: str):
    """Record a failed admin password attempt"""
    import time
    current_time = time.time()
    
    if ip_address not in _admin_failed_attempts:
        _admin_failed_attempts[ip_address] = []
    
    _admin_failed_attempts[ip_address].append(current_time)
    
    # Clean old entries (keep last hour)
    _admin_failed_attempts[ip_address] = [
        ts for ts in _admin_failed_attempts[ip_address]
        if ts > current_time - 3600  # Keep last hour
    ]

# Admin audit logging helper
def log_admin_action(action: str, resource_type: str, resource_id: str, details: Optional[Dict[str, Any]] = None, request: Optional[Request] = None):
    """Log admin actions for audit trail"""
    ip_address = request.client.host if request and request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown") if request else "unknown"
    
    logger.info(
        "Admin action",
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        ip_address=ip_address,
        user_agent=user_agent,
        details=details or {}
    )

def verify_admin_password(
    x_admin_password: Optional[str] = Header(None),
    request: Request = None
):
    """Verify admin password from header - SECURED with rate limiting. Returns role name."""
    admin_password = settings.ADMIN_PASSWORD
    social_media_password = settings.SOCIAL_MEDIA_MANAGER_PASSWORD
    
    # Get IP address for rate limiting
    try:
        ip_address = request.client.host if request and hasattr(request, 'client') and request.client else "unknown"
    except:
        ip_address = "unknown"
    
    # Check rate limiting BEFORE password check
    if not _check_admin_rate_limit(ip_address):
        logger.warning("Admin endpoint rate limited", ip_address=ip_address)
        # Calculate remaining lockout time
        import time
        remaining_time = int((_admin_lockout_until.get(ip_address, 0) - time.time()) / 60)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Too many failed attempts. Please try again in {remaining_time} minutes."
        )
    
    if not x_admin_password:
        _record_admin_failed_attempt(ip_address)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Admin password required"
        )
    
    # Check for social media manager password
    if social_media_password and x_admin_password == social_media_password:
        # Clear failed attempts on successful login
        if ip_address in _admin_failed_attempts:
            _admin_failed_attempts[ip_address] = []
        if ip_address in _admin_lockout_until:
            del _admin_lockout_until[ip_address]
        return "social_media_manager"
    
    # Check for full admin password
    # Security check: Fail if using default password in production
    if settings.ENVIRONMENT == "production" and admin_password == "TRADE!@#$%^":
        logger.error("CRITICAL: Admin password not changed from default in production!")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Server configuration error"
        )
    
    if x_admin_password != admin_password:
        # Record failed attempt
        _record_admin_failed_attempt(ip_address)
        logger.warning("Failed admin password attempt", ip_address=ip_address)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid admin password"
        )
    
    # Clear failed attempts on successful login
    if ip_address in _admin_failed_attempts:
        _admin_failed_attempts[ip_address] = []
    if ip_address in _admin_lockout_until:
        del _admin_lockout_until[ip_address]
    
    return "admin"

class UpdateSubscriptionRequest(BaseModel):
    user_id: str
    plan: str
    status: str

class UpdateUserRequest(BaseModel):
    email: Optional[str] = None
    onboarding_completed: Optional[bool] = None

@router.get("/role")
async def get_admin_role(
    role: str = Depends(verify_admin_password)
):
    """Get the current admin role"""
    return {"role": role}

@router.get("/social-media-password")
async def get_social_media_password(
    role: str = Depends(verify_admin_password)
):
    """Get the social media manager password (admin only)"""
    if role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only full admins can view this password"
        )
    
    return {
        "password": settings.SOCIAL_MEDIA_MANAGER_PASSWORD,
        "note": "This password grants access to referrals and analytics tabs only"
    }

@router.get("/dashboard")
async def get_admin_dashboard(
    db: Session = Depends(get_db),
    role: str = Depends(verify_admin_password)
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
        Trade.filled_at >= datetime.utcnow() - timedelta(days=1)
    ).scalar()
    trades_this_week = db.query(func.count(Trade.id)).filter(
        Trade.filled_at >= datetime.utcnow() - timedelta(days=7)
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
    role: str = Depends(verify_admin_password)
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
    role: str = Depends(verify_admin_password)
):
    """Get detailed information about a specific user"""
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    subscription = db.query(Subscription).filter(Subscription.user_id == user.id).first()
    trades = db.query(Trade).filter(Trade.user_id == user.id).order_by(desc(Trade.filled_at)).limit(20).all()
    
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
                "filled_at": trade.filled_at.isoformat() if trade.filled_at else None,
                "pnl": float(trade.pnl) if trade.pnl else None
            }
            for trade in trades
        ]
    }

@router.post("/users/{user_id}/subscription")
async def update_user_subscription(
    user_id: str,
    request: UpdateSubscriptionRequest,
    http_request: Request,
    db: Session = Depends(get_db),
    role: str = Depends(verify_admin_password)
):
    """Update a user's subscription (manual override) - SECURED"""
    
    # Validate plan value (prevent injection/unauthorized plans)
    valid_plans = ["free", "plus_monthly", "plus_yearly", "pro_monthly", "pro_yearly"]
    if request.plan not in valid_plans:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid plan. Must be one of: {', '.join(valid_plans)}"
        )
    
    # Validate status value
    valid_statuses = ["active", "canceled", "past_due", "trialing", "incomplete", "incomplete_expired"]
    if request.status not in valid_statuses:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
        )
    
    # Validate user_id format (UUID)
    import re
    uuid_pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
    if not re.match(uuid_pattern, user_id, re.IGNORECASE):
        raise HTTPException(status_code=400, detail="Invalid user ID format")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get current subscription for audit
    subscription = db.query(Subscription).filter(Subscription.user_id == user.id).first()
    old_plan = subscription.plan if subscription else "none"
    old_status = subscription.status if subscription else "none"
    
    # Update subscription
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
    db.refresh(subscription)
    
    # CRITICAL: Audit log for subscription changes
    log_admin_action(
        "update_subscription",
        "subscription",
        user_id,
        {
            "user_email": user.email,
            "old_plan": old_plan,
            "new_plan": request.plan,
            "old_status": old_status,
            "new_status": request.status,
            "stripe_customer": subscription.stripe_customer,
            "stripe_subscription": subscription.stripe_subscription
        },
        http_request
    )
    
    logger.warning(
        "Admin subscription change",
        user_id=user_id,
        user_email=user.email,
        old_plan=old_plan,
        new_plan=request.plan,
        old_status=old_status,
        new_status=request.status
    )
    
    return {
        "success": True,
        "subscription": {
            "plan": subscription.plan,
            "status": subscription.status
        },
        "audit": {
            "old_plan": old_plan,
            "old_status": old_status
        }
    }

@router.patch("/users/{user_id}")
async def update_user(
    user_id: str,
    request: UpdateUserRequest,
    http_request: Request,
    db: Session = Depends(get_db),
    role: str = Depends(verify_admin_password)
):
    """Update user details - SECURED"""
    
    # Validate user_id format (UUID)
    import re
    uuid_pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
    if not re.match(uuid_pattern, user_id, re.IGNORECASE):
        raise HTTPException(status_code=400, detail="Invalid user ID format")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    changes = {}
    
    if request.email:
        # Validate email format
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, request.email):
            raise HTTPException(status_code=400, detail="Invalid email format")
        
        # Sanitize email
        request.email = request.email.strip().lower()
        
        # Check if email already exists
        existing_user = db.query(User).filter(User.email == request.email, User.id != user_id).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="Email already in use")
        
        old_email = user.email
        user.email = request.email
        changes["email"] = {"old": old_email, "new": request.email}
    
    if request.onboarding_completed is not None:
        old_onboarding = user.onboarding_completed
        user.onboarding_completed = request.onboarding_completed
        if request.onboarding_completed and not user.onboarding_completed_at:
            from datetime import datetime, timezone
            user.onboarding_completed_at = datetime.now(timezone.utc)
        changes["onboarding_completed"] = {"old": old_onboarding, "new": request.onboarding_completed}
    
    db.commit()
    db.refresh(user)
    
    # Audit log
    if changes:
        log_admin_action(
            "update_user",
            "user",
            user_id,
            {
                "user_email": user.email,
                "changes": changes
            },
            http_request
        )
    
    logger.info("Admin updated user", user_id=user_id, email=user.email, changes=changes)
    
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
    http_request: Request,
    db: Session = Depends(get_db),
    role: str = Depends(verify_admin_password)
):
    """Delete a user and all their data - SECURED"""
    
    # Validate user_id format (UUID)
    import re
    uuid_pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
    if not re.match(uuid_pattern, user_id, re.IGNORECASE):
        raise HTTPException(status_code=400, detail="Invalid user ID format")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get user data for audit BEFORE deletion
    user_email = user.email
    user_created_at = user.created_at.isoformat() if user.created_at else None
    onboarding_completed = user.onboarding_completed
    
    # Get subscription info for audit
    subscription = db.query(Subscription).filter(Subscription.user_id == user.id).first()
    subscription_plan = subscription.plan if subscription else "none"
    subscription_status = subscription.status if subscription else "none"
    
    # Get trade count for audit
    trade_count = db.query(Trade).filter(Trade.user_id == user.id).count()
    
    # Delete subscription
    db.query(Subscription).filter(Subscription.user_id == user.id).delete()
    
    # Delete trades
    db.query(Trade).filter(Trade.user_id == user.id).delete()
    
    # Delete user
    db.delete(user)
    db.commit()
    
    # CRITICAL: Audit log for user deletion
    log_admin_action(
        "delete_user",
        "user",
        user_id,
        {
            "user_email": user_email,
            "user_created_at": user_created_at,
            "onboarding_completed": onboarding_completed,
            "subscription_plan": subscription_plan,
            "subscription_status": subscription_status,
            "trade_count": trade_count
        },
        http_request
    )
    
    logger.warning("Admin deleted user", user_id=user_id, email=user_email, trade_count=trade_count)
    
    return {"success": True, "message": f"User {user_email} deleted"}

@router.post("/sync-stripe")
async def sync_all_stripe_subscriptions(
    db: Session = Depends(get_db),
    role: str = Depends(verify_admin_password)
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
    role: str = Depends(verify_admin_password)
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

class CreateAIPostRequest(BaseModel):
    title: str
    body: str

@router.post("/create-ai-account")
async def create_tradequest_ai_account(
    db: Session = Depends(get_db),
    role: str = Depends(verify_admin_password)
):
    """Create or get TradeQuest AI account"""
    
    ai_user = db.query(User).filter(User.email == "ai@tradequest.tech").first()
    
    if not ai_user:
        ai_user = User(
            email="ai@tradequest.tech",
            display_name="TradeQuest AI",
            bio="Daily market insights and analysis powered by TradeQuest AI",
            onboarding_completed=True,
            onboarding_completed_at=datetime.now(timezone.utc)
        )
        db.add(ai_user)
        db.commit()
        db.refresh(ai_user)
        
        # Create subscription
        subscription = Subscription(
            user_id=ai_user.id,
            plan="pro",
            status="active"
        )
        db.add(subscription)
        db.commit()
        
        logger.info("Created TradeQuest AI account", user_id=str(ai_user.id))
        return {
            "success": True,
            "message": "TradeQuest AI account created",
            "user_id": str(ai_user.id)
        }
    else:
        logger.info("TradeQuest AI account already exists", user_id=str(ai_user.id))
        return {
            "success": True,
            "message": "TradeQuest AI account already exists",
            "user_id": str(ai_user.id)
        }

@router.post("/post-daily-compass")
async def post_daily_market_compass(
    request: CreateAIPostRequest,
    db: Session = Depends(get_db),
    role: str = Depends(verify_admin_password)
):
    """Post daily market compass as TradeQuest AI"""
    
    # Get or create AI user
    ai_user = db.query(User).filter(User.email == "ai@tradequest.tech").first()
    if not ai_user:
        # Create it first
        ai_user = User(
            email="ai@tradequest.tech",
            display_name="TradeQuest AI",
            bio="Daily market insights and analysis powered by TradeQuest AI",
            onboarding_completed=True,
            onboarding_completed_at=datetime.now(timezone.utc)
        )
        db.add(ai_user)
        db.commit()
        db.refresh(ai_user)
        
        subscription = Subscription(user_id=ai_user.id, plan="pro", status="active")
        db.add(subscription)
        db.commit()
    
    # Create the insight (this is what the /insights endpoint queries)
    now = datetime.now(timezone.utc)
    period_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    
    insight = CommunityInsight(
        user_id=ai_user.id,
        title=request.title,
        description=request.body,  # Use description field for the content
        insight_type="trend",  # trend, pattern, or statistic
        category="market",  # trading, market, or behavior
        data={
            "content": request.body,
            "source": "TradeQuest AI",
            "tags": ["market-analysis", "daily-compass", "trading-insights"]
        },
        period_start=period_start,
        period_end=now,
        is_published=True,
        is_featured=True
    )
    
    db.add(insight)
    db.commit()
    db.refresh(insight)
    
    logger.info("Posted daily market compass", insight_id=str(insight.id), user_id=str(ai_user.id))
    
    return {
        "success": True,
        "message": "Daily market compass posted",
        "insight_id": str(insight.id),
        "title": insight.title
    }

@router.get("/insights")
async def get_all_insights(
    user_id: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db),
    role: str = Depends(verify_admin_password)
):
    """Get all community insights (admin only)"""
    
    query = db.query(CommunityInsight)
    
    if user_id:
        # Find user by email or ID
        user = db.query(User).filter(
            (User.id == user_id) | (User.email == user_id)
        ).first()
        if user:
            query = query.filter(CommunityInsight.user_id == user.id)
    
    insights = query.order_by(desc(CommunityInsight.created_at)).limit(limit).all()
    
    return {
        "insights": [
            {
                "id": str(insight.id),
                "title": insight.title,
                "description": insight.description,
                "created_at": insight.created_at.isoformat() if insight.created_at else None,
                "is_published": insight.is_published,
                "is_featured": insight.is_featured,
                "data": insight.data
            }
            for insight in insights
        ]
    }

@router.get("/bug-reports")
async def get_all_bug_reports(
    status: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db),
    role: str = Depends(verify_admin_password)
):
    """Get all bug reports (admin only)"""
    
    from app.models.bug_report import BugReport
    
    query = db.query(BugReport)
    
    if status:
        query = query.filter(BugReport.status == status)
    
    bug_reports = query.order_by(desc(BugReport.created_at)).limit(limit).all()
    
    return {
        "bug_reports": [
            {
                "id": str(br.id),
                "user_id": str(br.user_id),
                "user_email": br.user.email if br.user else "Unknown",
                "title": br.title,
                "description": br.description,
                "screenshot_url": br.screenshot_url,
                "url": br.url,
                "user_agent": br.user_agent,
                "logs": br.logs,
                "browser_info": br.browser_info,
                "status": br.status,
                "admin_notes": br.admin_notes,
                "created_at": br.created_at.isoformat() if br.created_at else None,
                "resolved_at": br.resolved_at.isoformat() if br.resolved_at else None
            }
            for br in bug_reports
        ],
        "total": query.count()
    }

@router.patch("/bug-reports/{bug_report_id}")
async def update_bug_report(
    bug_report_id: str,
    status: Optional[str] = None,
    admin_notes: Optional[str] = None,
    db: Session = Depends(get_db),
    role: str = Depends(verify_admin_password)
):
    """Update bug report status (admin only)"""
    
    from app.models.bug_report import BugReport
    
    bug_report = db.query(BugReport).filter(BugReport.id == bug_report_id).first()
    if not bug_report:
        raise HTTPException(status_code=404, detail="Bug report not found")
    
    if status:
        bug_report.status = status
        if status == "resolved":
            bug_report.resolved_at = datetime.now(timezone.utc)
    
    if admin_notes is not None:
        bug_report.admin_notes = admin_notes
    
    db.commit()
    db.refresh(bug_report)
    
    return {
        "success": True,
        "bug_report": {
            "id": str(bug_report.id),
            "status": bug_report.status,
            "admin_notes": bug_report.admin_notes
        }
    }

@router.delete("/insights/{insight_id}")
async def delete_insight(
    insight_id: str,
    db: Session = Depends(get_db),
    role: str = Depends(verify_admin_password)
):
    """Delete a community insight"""
    
    insight = db.query(CommunityInsight).filter(CommunityInsight.id == insight_id).first()
    if not insight:
        raise HTTPException(status_code=404, detail="Insight not found")
    
    db.delete(insight)
    db.commit()
    
    logger.info("Deleted community insight", insight_id=insight_id)
    
    return {
        "success": True,
        "message": "Insight deleted successfully"
    }

# Referral Links Endpoints

class CreateReferralLinkRequest(BaseModel):
    code: str
    name: str
    notes: Optional[str] = None

class UpdateReferralLinkRequest(BaseModel):
    name: Optional[str] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = None

@router.post("/referral-links")
async def create_referral_link(
    request: CreateReferralLinkRequest,
    http_request: Request,
    db: Session = Depends(get_db),
    role: str = Depends(verify_admin_password)
):
    """Create a new referral link"""
    
    from app.models.referral import ReferralLink
    import re
    
    # Input validation: Referral code must be alphanumeric, uppercase, 3-50 chars
    if not re.match(r'^[A-Z0-9]{3,50}$', request.code):
        raise HTTPException(
            status_code=400, 
            detail="Referral code must be 3-50 characters, alphanumeric uppercase only"
        )
    
    # Sanitize name and notes (remove HTML/script tags)
    import html
    sanitized_name = html.escape(request.name[:200])  # Max 200 chars
    sanitized_notes = html.escape(request.notes[:1000]) if request.notes else None  # Max 1000 chars
    
    # Check if code already exists
    existing = db.query(ReferralLink).filter(ReferralLink.code == request.code).first()
    if existing:
        raise HTTPException(status_code=400, detail="Referral code already exists")
    
    referral_link = ReferralLink(
        code=request.code.upper(),  # Normalize to uppercase
        name=sanitized_name,
        notes=sanitized_notes,
        is_active=True
    )
    
    db.add(referral_link)
    db.commit()
    db.refresh(referral_link)
    
    # Audit log
    log_admin_action("create_referral_link", "referral_link", str(referral_link.id), 
                     {"code": request.code, "name": sanitized_name}, http_request)
    
    logger.info("Created referral link", code=request.code, name=request.name)
    
    return {
        "success": True,
        "referral_link": {
            "id": str(referral_link.id),
            "code": referral_link.code,
            "name": referral_link.name,
            "notes": referral_link.notes,
            "is_active": referral_link.is_active,
            "signups_count": referral_link.signups_count,
            "created_at": referral_link.created_at.isoformat() if referral_link.created_at else None
        }
    }

@router.get("/referral-links")
async def get_referral_links(
    db: Session = Depends(get_db),
    role: str = Depends(verify_admin_password)
):
    """Get all referral links with statistics (accessible to social media managers)"""
    
    from app.models.referral import ReferralLink
    
    referral_links = db.query(ReferralLink).order_by(desc(ReferralLink.created_at)).all()
    
    # Get user counts per referral code
    referral_stats = []
    for link in referral_links:
        user_count = db.query(User).filter(User.referral_code == link.code).count()
        
        referral_stats.append({
            "id": str(link.id),
            "code": link.code,
            "name": link.name,
            "notes": link.notes,
            "is_active": link.is_active,
            "signups_count": link.signups_count,
            "user_count": user_count,  # Actual users with this referral code
            "first_signup_at": link.first_signup_at.isoformat() if link.first_signup_at else None,
            "last_signup_at": link.last_signup_at.isoformat() if link.last_signup_at else None,
            "created_at": link.created_at.isoformat() if link.created_at else None,
            "updated_at": link.updated_at.isoformat() if link.updated_at else None
        })
    
    return {
        "success": True,
        "referral_links": referral_stats,
        "total": len(referral_stats)
    }

@router.get("/referral-links/{link_id}")
async def get_referral_link_details(
    link_id: str,
    db: Session = Depends(get_db),
    role: str = Depends(verify_admin_password)
):
    """Get detailed statistics for a specific referral link"""
    
    from app.models.referral import ReferralLink
    
    referral_link = db.query(ReferralLink).filter(ReferralLink.id == link_id).first()
    if not referral_link:
        raise HTTPException(status_code=404, detail="Referral link not found")
    
    # Get all users who signed up with this referral code
    users = db.query(User).filter(User.referral_code == referral_link.code).order_by(desc(User.created_at)).all()
    
    return {
        "success": True,
        "referral_link": {
            "id": str(referral_link.id),
            "code": referral_link.code,
            "name": referral_link.name,
            "notes": referral_link.notes,
            "is_active": referral_link.is_active,
            "signups_count": referral_link.signups_count,
            "first_signup_at": referral_link.first_signup_at.isoformat() if referral_link.first_signup_at else None,
            "last_signup_at": referral_link.last_signup_at.isoformat() if referral_link.last_signup_at else None,
            "created_at": referral_link.created_at.isoformat() if referral_link.created_at else None
        },
        "users": [
            {
                "id": str(user.id),
                "email": user.email,
                "created_at": user.created_at.isoformat() if user.created_at else None,
                "onboarding_completed": user.onboarding_completed
            }
            for user in users
        ],
        "total_users": len(users)
    }

@router.patch("/referral-links/{link_id}")
async def update_referral_link(
    link_id: str,
    request: UpdateReferralLinkRequest,
    http_request: Request,
    db: Session = Depends(get_db),
    role: str = Depends(verify_admin_password)
):
    """Update a referral link - SECURED"""
    
    from app.models.referral import ReferralLink
    import html
    import re
    
    # Validate link_id format
    uuid_pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
    if not re.match(uuid_pattern, link_id, re.IGNORECASE):
        raise HTTPException(status_code=400, detail="Invalid link ID format")
    
    referral_link = db.query(ReferralLink).filter(ReferralLink.id == link_id).first()
    if not referral_link:
        raise HTTPException(status_code=404, detail="Referral link not found")
    
    changes = {}
    
    if request.name is not None:
        # Sanitize name
        sanitized_name = html.escape(request.name[:200])
        old_name = referral_link.name
        referral_link.name = sanitized_name
        changes["name"] = {"old": old_name, "new": sanitized_name}
    
    if request.notes is not None:
        # Sanitize notes
        sanitized_notes = html.escape(request.notes[:1000])
        old_notes = referral_link.notes
        referral_link.notes = sanitized_notes
        changes["notes"] = {"old": old_notes, "new": sanitized_notes}
    
    if request.is_active is not None:
        old_active = referral_link.is_active
        referral_link.is_active = request.is_active
        changes["is_active"] = {"old": old_active, "new": request.is_active}
    
    db.commit()
    db.refresh(referral_link)
    
    # Audit log
    if changes:
        log_admin_action(
            "update_referral_link",
            "referral_link",
            link_id,
            {
                "code": referral_link.code,
                "changes": changes
            },
            http_request
        )
    
    logger.info("Updated referral link", link_id=link_id, code=referral_link.code, changes=changes)
    
    return {
        "success": True,
        "referral_link": {
            "id": str(referral_link.id),
            "code": referral_link.code,
            "name": referral_link.name,
            "notes": referral_link.notes,
            "is_active": referral_link.is_active
        }
    }

@router.delete("/referral-links/{link_id}")
async def delete_referral_link(
    link_id: str,
    http_request: Request,
    db: Session = Depends(get_db),
    role: str = Depends(verify_admin_password)
):
    """Delete a referral link (soft delete by setting is_active=False) - SECURED"""
    
    from app.models.referral import ReferralLink
    import re
    
    # Validate link_id format
    uuid_pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
    if not re.match(uuid_pattern, link_id, re.IGNORECASE):
        raise HTTPException(status_code=400, detail="Invalid link ID format")
    
    referral_link = db.query(ReferralLink).filter(ReferralLink.id == link_id).first()
    if not referral_link:
        raise HTTPException(status_code=404, detail="Referral link not found")
    
    # Get data for audit
    code = referral_link.code
    signups_count = referral_link.signups_count
    was_active = referral_link.is_active
    
    # Soft delete - just deactivate
    referral_link.is_active = False
    db.commit()
    
    # Audit log
    log_admin_action(
        "delete_referral_link",
        "referral_link",
        link_id,
        {
            "code": code,
            "signups_count": signups_count,
            "was_active": was_active
        },
        http_request
    )
    
    logger.info("Deactivated referral link", link_id=link_id, code=code, signups_count=signups_count)
    
    return {
        "success": True,
        "message": "Referral link deactivated successfully"
    }

@router.get("/analytics")
async def get_social_media_analytics(
    db: Session = Depends(get_db),
    role: str = Depends(verify_admin_password)
):
    """Get analytics for social media managers - referral performance metrics"""
    
    from app.models.referral import ReferralLink
    
    # Get all referral links
    referral_links = db.query(ReferralLink).order_by(desc(ReferralLink.created_at)).all()
    
    # Calculate overall statistics
    total_signups = sum(link.signups_count for link in referral_links)
    total_users = db.query(func.count(User.id)).filter(User.referral_code.isnot(None)).scalar()
    active_links = sum(1 for link in referral_links if link.is_active)
    
    # Get signups over time (last 30 days)
    signups_over_time = []
    for days_ago in range(30, -1, -1):
        date = datetime.utcnow() - timedelta(days=days_ago)
        count = db.query(func.count(User.id)).filter(
            User.referral_code.isnot(None),
            func.date(User.created_at) == date.date()
        ).scalar()
        signups_over_time.append({
            "date": date.date().isoformat(),
            "signups": count
        })
    
    # Top performing referral links (by signups)
    top_links = sorted(
        [
            {
                "code": link.code,
                "name": link.name,
                "signups": link.signups_count,
                "is_active": link.is_active,
                "first_signup": link.first_signup_at.isoformat() if link.first_signup_at else None,
                "last_signup": link.last_signup_at.isoformat() if link.last_signup_at else None
            }
            for link in referral_links
        ],
        key=lambda x: x["signups"],
        reverse=True
    )[:10]
    
    # Conversion rate (users who completed onboarding)
    users_with_referral = db.query(User).filter(User.referral_code.isnot(None)).all()
    onboarded_count = sum(1 for user in users_with_referral if user.onboarding_completed)
    conversion_rate = (onboarded_count / len(users_with_referral) * 100) if users_with_referral else 0
    
    return {
        "overview": {
            "total_signups": total_signups,
            "total_users": total_users,
            "active_referral_links": active_links,
            "conversion_rate": round(conversion_rate, 2),
            "onboarded_users": onboarded_count
        },
        "signups_over_time": signups_over_time,
        "top_performing_links": top_links
    }

