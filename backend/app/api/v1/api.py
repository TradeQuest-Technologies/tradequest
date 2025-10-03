"""
Main API router that includes all endpoint routers
"""

from fastapi import APIRouter
from app.api.v1.endpoints import auth, broker, market, journal, backtest, backtest_v2, ai, billing, alerts, reports, messaging, settings, data, dev, onboarding, two_factor, notifications, custom_venue, coach

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(broker.router, prefix="/broker", tags=["broker"])
api_router.include_router(market.router, prefix="/market", tags=["market-data"])
api_router.include_router(journal.router, prefix="/journal", tags=["journal"])
api_router.include_router(backtest.router, prefix="/backtest", tags=["backtesting"])
api_router.include_router(backtest_v2.router, prefix="/backtest/v2", tags=["backtesting-v2"])
api_router.include_router(ai.router, prefix="/ai", tags=["ai-tools"])
api_router.include_router(coach.router, prefix="/coach", tags=["ai-coach"])
api_router.include_router(billing.router, prefix="/billing", tags=["billing"])
api_router.include_router(alerts.router, prefix="/alerts", tags=["alerts"])
api_router.include_router(reports.router, prefix="/reports", tags=["reports"])
api_router.include_router(messaging.router, prefix="/messaging", tags=["messaging"])
api_router.include_router(settings.router, prefix="/settings", tags=["settings"])
api_router.include_router(data.router, prefix="/data", tags=["data"])
api_router.include_router(dev.router, prefix="/dev", tags=["developer"])
api_router.include_router(onboarding.router, prefix="/onboarding", tags=["onboarding"])
api_router.include_router(two_factor.router, prefix="/2fa", tags=["two-factor"])
api_router.include_router(notifications.router, prefix="/notifications", tags=["notifications"])
api_router.include_router(custom_venue.router, prefix="/venues", tags=["custom-venues"])
