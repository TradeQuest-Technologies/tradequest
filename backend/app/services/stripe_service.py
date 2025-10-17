"""
Stripe billing service
"""

import stripe
from typing import Dict, Any, Optional
from app.core.config import settings
import structlog

logger = structlog.get_logger()

# Initialize Stripe at module level
if settings.STRIPE_SECRET_KEY:
    stripe.api_key = settings.STRIPE_SECRET_KEY
    print(f"[STARTUP] Stripe initialized at module level with key: {settings.STRIPE_SECRET_KEY[:10]}...")
    print(f"[STARTUP] stripe.api_key set: {stripe.api_key is not None}")
    logger.info("Stripe initialized at module level")
else:
    print("[STARTUP ERROR] STRIPE_SECRET_KEY not available at module level")
    logger.warning("STRIPE_SECRET_KEY not available at module level")

# Fix for Stripe 7.8.0 bug - must import checkout explicitly AFTER setting api_key
# Don't import here - will import in the function where it's used

def _ensure_stripe_initialized():
    """Ensure Stripe is properly initialized"""
    if not stripe.api_key:
        if not settings.STRIPE_SECRET_KEY:
            raise ValueError("STRIPE_SECRET_KEY is not configured")
        stripe.api_key = settings.STRIPE_SECRET_KEY

class StripeService:
    """Service for handling Stripe billing operations"""
    
    def __init__(self):
        self.publishable_key = "pk_live_51SBKFxEc0UfOtXXQqpmJlBslvKHKdr8OaBc9hOnh3wgaOxrQcp9wyJ0I4CluxVxTHCqQ22iwpy6o0AsxXezG5Y3z00SBoIkVbX"
        
        # Plan configurations
        self.plans = {
            "free": {
                "name": "Free",
                "price": 0,
                "features": [
                    "Up to 50 trades per month",
                    "Basic trade journal with notes and tags",
                    "Core performance metrics (Win rate, P&L, Profit factor)",
                    "Paper trading simulator",
                    "CSV import/export",
                    "Basic charts and visualizations",
                    "5 AI coaching sessions per month",
                    "Email support"
                ]
            },
            "plus_monthly": {
                "name": "Plus",
                "price": 29,
                "interval": "month",
                "price_id": "price_1SEDPKEc0UfOtXXQWVbLwv3M",  # Live Stripe Price ID (Monthly)
                "features": [
                    "Unlimited trades",
                    "Advanced trade journal with screenshots",
                    "Comprehensive performance metrics & analytics",
                    "Unlimited AI trading coach sessions",
                    "Advanced backtesting studio",
                    "Custom strategy builder",
                    "Advanced charts with technical indicators",
                    "Risk management & discipline alerts",
                    "PDF reports and analytics export",
                    "Priority support",
                    "Custom tags and categories",
                    "Trade session analysis with heatmaps"
                ]
            },
            "plus_yearly": {
                "name": "Plus",
                "price": 290,
                "interval": "year",
                "price_id": "price_1SErESEc0UfOtXXQB8KqnhnL",  # Live Stripe Price ID (Yearly)
                "features": [
                    "Unlimited trades",
                    "Advanced trade journal with screenshots",
                    "Comprehensive performance metrics & analytics",
                    "Unlimited AI trading coach sessions",
                    "Advanced backtesting studio",
                    "Custom strategy builder",
                    "Advanced charts with technical indicators",
                    "Risk management & discipline alerts",
                    "PDF reports and analytics export",
                    "Priority support",
                    "Custom tags and categories",
                    "Trade session analysis with heatmaps"
                ]
            }
        }
    
    def create_checkout_session(
        self,
        user_id: str,
        user_email: str,
        plan: str,
        success_url: str,
        cancel_url: str
    ) -> Dict[str, Any]:
        """Create Stripe checkout session"""
        
        logger.info("StripeService.create_checkout_session called", user_id=user_id, plan=plan)
        
        _ensure_stripe_initialized()
        logger.info("Stripe initialization check passed")
        
        if plan not in ["plus_monthly", "plus_yearly"]:
            raise ValueError("Invalid plan for checkout. Only Plus monthly and yearly plans are available.")
        
        plan_config = self.plans[plan]
        logger.info("Plan config retrieved", price_id=plan_config.get("price_id"))
        
        try:
            # Import Session class directly from stripe.checkout to work around Stripe 7.8.0 bug
            from stripe.checkout import Session as StripeSession
            
            logger.info("About to call StripeSession.create")
            logger.info("StripeSession", exists=StripeSession is not None)
            logger.info("StripeSession.create", exists=hasattr(StripeSession, 'create'))
            
            # Use the price_id directly instead of creating price_data
            # Use StripeSession.create() - direct import of Session class
            session = StripeSession.create(
                payment_method_types=['card'],
                line_items=[{
                    'price': plan_config["price_id"],
                    'quantity': 1,
                }],
                mode='subscription',
                success_url=success_url,
                cancel_url=cancel_url,
                customer_email=user_email,
                allow_promotion_codes=True,  # Enable promo codes for beta testers
                metadata={
                    'user_id': user_id,
                    'plan': plan
                }
            )
            
            logger.info("Checkout session created", user_id=user_id, plan=plan, session_id=session.id)
            
            return {
                "session_id": session.id,
                "url": session.url,
                "plan": plan
            }
            
        except stripe.error.StripeError as e:
            logger.error("Stripe checkout error", error=str(e))
            raise Exception(f"Failed to create checkout session: {str(e)}")
        except Exception as e:
            logger.error("Unexpected error in checkout", error=str(e), error_type=type(e).__name__)
            raise
    
    def create_customer_portal_session(self, customer_id: str, return_url: str) -> Dict[str, Any]:
        """Create customer portal session for subscription management"""
        
        _ensure_stripe_initialized()
        
        try:
            session = stripe.billing_portal.Session.create(
                customer=customer_id,
                return_url=return_url,
            )
            
            return {
                "url": session.url
            }
            
        except stripe.error.StripeError as e:
            logger.error("Stripe portal error", error=str(e))
            raise Exception(f"Failed to create portal session: {str(e)}")
    
    def get_subscription(self, subscription_id: str) -> Optional[Dict[str, Any]]:
        """Get subscription details from Stripe"""
        
        _ensure_stripe_initialized()
        
        try:
            subscription = stripe.Subscription.retrieve(subscription_id)
            
            return {
                "id": subscription.id,
                "status": subscription.status,
                "current_period_start": subscription.current_period_start,
                "current_period_end": subscription.current_period_end,
                "cancel_at_period_end": subscription.cancel_at_period_end,
                "plan": subscription.items.data[0].price.id if subscription.items.data else None
            }
            
        except stripe.error.StripeError as e:
            logger.error("Stripe subscription error", error=str(e))
            return None
    
    def cancel_subscription(self, subscription_id: str) -> bool:
        """Cancel subscription"""
        
        _ensure_stripe_initialized()
        
        try:
            stripe.Subscription.delete(subscription_id)
            logger.info("Subscription canceled", subscription_id=subscription_id)
            return True
            
        except stripe.error.StripeError as e:
            logger.error("Stripe cancel error", error=str(e))
            return False
    
    def get_plans(self) -> Dict[str, Any]:
        """Get available plans"""
        return self.plans
    
    def verify_webhook_signature(self, payload: str, signature: str) -> bool:
        """Verify webhook signature"""
        
        _ensure_stripe_initialized()
        
        try:
            stripe.Webhook.construct_event(
                payload, signature, settings.STRIPE_WEBHOOK_SECRET
            )
            return True
        except stripe.error.SignatureVerificationError:
            return False
