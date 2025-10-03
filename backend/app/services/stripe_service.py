"""
Stripe billing service
"""

import stripe
from typing import Dict, Any, Optional
from app.core.config import settings
import structlog

logger = structlog.get_logger()

# Initialize Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY

class StripeService:
    """Service for handling Stripe billing operations"""
    
    def __init__(self):
        self.publishable_key = "pk_test_51SBKG3IvhoH7AcaHmExZTPCnxMCersQIFQ5S3o0yrs41H2ShnmfH8E2Gne7o5Mbk4y2XVi9VuxZeaKWbkuzYqxI300J0G188OP"
        
        # Plan configurations
        self.plans = {
            "free": {
                "name": "Free",
                "price": 0,
                "features": [
                    "Manual CSV import",
                    "1 backtest/day",
                    "Chat read-only tools",
                    "Basic analytics"
                ]
            },
            "plus": {
                "name": "Plus",
                "price": 9,
                "price_id": "price_plus_monthly",  # You'll need to create this in Stripe
                "features": [
                    "Broker auto-sync",
                    "AI coach per trade",
                    "10 backtests/day",
                    "Weekly PDF reports"
                ]
            },
            "pro": {
                "name": "Pro",
                "price": 19,
                "price_id": "price_pro_monthly",  # You'll need to create this in Stripe
                "features": [
                    "Unlimited backtests",
                    "Alerts & notifications",
                    "Shareable strategy cards",
                    "Priority support"
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
        
        if plan not in ["plus", "pro"]:
            raise ValueError("Invalid plan for checkout")
        
        plan_config = self.plans[plan]
        
        try:
            session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{
                    'price_data': {
                        'currency': 'usd',
                        'product_data': {
                            'name': f'TradeQuest {plan_config["name"]}',
                            'description': f'TradeQuest {plan_config["name"]} Plan',
                        },
                        'unit_amount': plan_config["price"] * 100,  # Convert to cents
                        'recurring': {
                            'interval': 'month',
                        },
                    },
                    'quantity': 1,
                }],
                mode='subscription',
                success_url=success_url,
                cancel_url=cancel_url,
                customer_email=user_email,
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
    
    def create_customer_portal_session(self, customer_id: str, return_url: str) -> Dict[str, Any]:
        """Create customer portal session for subscription management"""
        
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
        
        try:
            stripe.Webhook.construct_event(
                payload, signature, settings.STRIPE_WEBHOOK_SECRET
            )
            return True
        except stripe.error.SignatureVerificationError:
            return False
