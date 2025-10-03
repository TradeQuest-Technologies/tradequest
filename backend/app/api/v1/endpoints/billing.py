"""
Billing endpoints for Stripe integration
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import Dict, Any
import structlog

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.user import User, Subscription
from app.services.stripe_service import StripeService
from app.core.plan_limits import get_user_plan, get_plan_limits, check_trade_limit, check_ai_coaching_limit

logger = structlog.get_logger()
router = APIRouter()

@router.get("/plans")
async def get_plans():
    """Get available subscription plans"""
    
    stripe_service = StripeService()
    return stripe_service.get_plans()

@router.get("/subscription")
async def get_subscription(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's current subscription and usage"""
    
    # Get subscription from database
    subscription = db.query(Subscription).filter(Subscription.user_id == current_user.id).first()
    
    # Get plan (defaults to free if no subscription)
    plan = subscription.plan if subscription else "free"
    plan_limits = get_plan_limits(plan)
    
    # Check current usage
    trade_limit_info = check_trade_limit(db, current_user.id)
    coaching_limit_info = check_ai_coaching_limit(db, current_user.id)
    
    return {
        "plan": plan,
        "status": subscription.status if subscription else "active",
        "limits": {
            "trades_per_month": plan_limits["trades_per_month"],
            "ai_coaching_sessions_per_month": plan_limits["ai_coaching_sessions_per_month"],
            "backtest_runs_per_month": plan_limits["backtest_runs_per_month"]
        },
        "usage": {
            "trades": trade_limit_info,
            "ai_coaching": coaching_limit_info
        },
        "features": plan_limits["features"],
        "can_upgrade": plan == "free"
    }

@router.post("/checkout")
async def create_checkout_session(
    plan: str,
    success_url: str = "http://localhost:3000/dashboard?success=true",
    cancel_url: str = "http://localhost:3000/pricing?canceled=true",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create Stripe checkout session"""
    
    if plan not in ["plus"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid plan. Only 'plus' plan is available."
        )
    
    stripe_service = StripeService()
    
    try:
        session_data = stripe_service.create_checkout_session(
            user_id=str(current_user.id),
            user_email=current_user.email,
            plan=plan,
            success_url=success_url,
            cancel_url=cancel_url
        )
        
        return {
            "checkout_url": session_data["url"],
            "session_id": session_data["session_id"],
            "plan": plan
        }
        
    except Exception as e:
        logger.error("Checkout creation failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create checkout session: {str(e)}"
        )

@router.post("/portal")
async def create_customer_portal_session(
    return_url: str = "http://localhost:3000/settings",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create customer portal session for subscription management"""
    
    # Get user's subscription
    subscription = db.query(Subscription).filter(Subscription.user_id == current_user.id).first()
    
    if not subscription or not subscription.stripe_customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active subscription found"
        )
    
    stripe_service = StripeService()
    
    try:
        portal_data = stripe_service.create_customer_portal_session(
            customer_id=subscription.stripe_customer,
            return_url=return_url
        )
        
        return {
            "portal_url": portal_data["url"]
        }
        
    except Exception as e:
        logger.error("Portal creation failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create portal session: {str(e)}"
        )

@router.post("/webhook")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    """Handle Stripe webhook events"""
    
    payload = await request.body()
    signature = request.headers.get("stripe-signature")
    
    if not signature:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing stripe-signature header"
        )
    
    stripe_service = StripeService()
    
    # Verify webhook signature
    if not stripe_service.verify_webhook_signature(payload, signature):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid webhook signature"
        )
    
    # Parse webhook event
    import json
    event = json.loads(payload)
    
    logger.info("Stripe webhook received", event_type=event["type"])
    
    try:
        if event["type"] == "checkout.session.completed":
            await handle_checkout_completed(event, db)
        elif event["type"] == "customer.subscription.updated":
            await handle_subscription_updated(event, db)
        elif event["type"] == "customer.subscription.deleted":
            await handle_subscription_deleted(event, db)
        elif event["type"] == "invoice.payment_succeeded":
            await handle_payment_succeeded(event, db)
        elif event["type"] == "invoice.payment_failed":
            await handle_payment_failed(event, db)
        
        return {"status": "success"}
        
    except Exception as e:
        logger.error("Webhook processing failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Webhook processing failed: {str(e)}"
        )

async def handle_checkout_completed(event: Dict[str, Any], db: Session):
    """Handle successful checkout"""
    
    session = event["data"]["object"]
    user_id = session["metadata"]["user_id"]
    plan = session["metadata"]["plan"]
    customer_id = session["customer"]
    
    # Update user subscription
    subscription = db.query(Subscription).filter(Subscription.user_id == user_id).first()
    
    if subscription:
        subscription.stripe_customer = customer_id
        subscription.plan = plan
        subscription.status = "active"
    else:
        subscription = Subscription(
            user_id=user_id,
            stripe_customer=customer_id,
            plan=plan,
            status="active"
        )
        db.add(subscription)
    
    db.commit()
    
    logger.info("Subscription activated", user_id=user_id, plan=plan)

async def handle_subscription_updated(event: Dict[str, Any], db: Session):
    """Handle subscription updates"""
    
    subscription_data = event["data"]["object"]
    customer_id = subscription_data["customer"]
    
    # Find subscription by customer ID
    subscription = db.query(Subscription).filter(
        Subscription.stripe_customer == customer_id
    ).first()
    
    if subscription:
        subscription.status = subscription_data["status"]
        db.commit()
        
        logger.info("Subscription updated", customer_id=customer_id, status=subscription_data["status"])

async def handle_subscription_deleted(event: Dict[str, Any], db: Session):
    """Handle subscription cancellation"""
    
    subscription_data = event["data"]["object"]
    customer_id = subscription_data["customer"]
    
    # Find subscription by customer ID
    subscription = db.query(Subscription).filter(
        Subscription.stripe_customer == customer_id
    ).first()
    
    if subscription:
        subscription.status = "canceled"
        subscription.plan = "free"
        db.commit()
        
        logger.info("Subscription canceled", customer_id=customer_id)

async def handle_payment_succeeded(event: Dict[str, Any], db: Session):
    """Handle successful payment"""
    
    invoice = event["data"]["object"]
    customer_id = invoice["customer"]
    
    logger.info("Payment succeeded", customer_id=customer_id, amount=invoice["amount_paid"])

async def handle_payment_failed(event: Dict[str, Any], db: Session):
    """Handle failed payment"""
    
    invoice = event["data"]["object"]
    customer_id = invoice["customer"]
    
    # Update subscription status
    subscription = db.query(Subscription).filter(
        Subscription.stripe_customer == customer_id
    ).first()
    
    if subscription:
        subscription.status = "past_due"
        db.commit()
    
    logger.warning("Payment failed", customer_id=customer_id)
