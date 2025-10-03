"""
Onboarding schemas
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

# Step 1: Legal
class LegalAcceptance(BaseModel):
    age_confirm: bool = Field(..., description="I am 16 or older")
    accept_tos: bool = Field(..., description="I agree to Terms of Service")
    accept_privacy: bool = Field(..., description="I agree to Privacy Policy")
    region: Optional[str] = Field(None, description="User's region")

# Step 2: Account Basics
class AccountBasics(BaseModel):
    first_name: Optional[str] = Field(None, description="User first name")
    last_name: Optional[str] = Field(None, description="User last name")
    birth_date: Optional[str] = Field(None, description="Birth date in YYYY-MM-DD")
    alias: Optional[str] = Field(None, description="Display name")
    timezone: str = Field("UTC", description="User timezone")
    display_currency: str = Field("USD", description="Display currency")
    pnl_visibility_default: bool = Field(True, description="Show PnL by default")

# Step 3: Security
class SecuritySetup(BaseModel):
    set_password: str = Field(..., min_length=10, description="Password (min 10 chars, required)")
    confirm_password: str = Field(..., description="Confirm password")
    
    # 2FA Method Selection (required)
    two_factor_method: str = Field(..., description="2FA method: email, sms, google_auth, totp (required)")
    phone_number: Optional[str] = Field(None, description="Phone number for SMS 2FA")
    
    # TOTP/Google Auth setup
    totp_code: Optional[str] = Field(None, description="6-digit verification code")

# Step 4: Trading Profile
class TradingProfile(BaseModel):
    experience_level: str = Field(..., description="Trading experience level")
    markets: List[str] = Field(default_factory=lambda: ["crypto"], description="Trading markets")
    style: List[str] = Field(default_factory=list, description="Trading styles")
    timeframes: List[str] = Field(default_factory=list, description="Preferred timeframes")
    platforms: List[str] = Field(default_factory=list, description="Trading platforms")
    days_active_per_week: int = Field(3, ge=0, le=7, description="Days active per week")
    session_pref: List[str] = Field(default_factory=list, description="Trading sessions")

# Step 5: Goals & Risk
class GoalsAndRisk(BaseModel):
    primary_goal: str = Field(..., description="Primary trading goal")
    account_size_band: str = Field(..., description="Account size range")
    risk_per_trade_pct: float = Field(1.0, ge=0.1, le=5.0, description="Risk per trade percentage")
    max_monthly_drawdown_target_pct: float = Field(10.0, ge=2.0, le=50.0, description="Max monthly drawdown target")
    target_winrate_hint: Optional[float] = Field(None, ge=30.0, le=70.0, description="Target win rate hint")

# Step 6: Discipline Rules
class DisciplineRules(BaseModel):
    daily_stop_type: str = Field(..., description="Daily stop type: percent or fixed")
    daily_stop_value: float = Field(..., description="Daily stop value")
    max_trades_per_day: int = Field(5, ge=1, le=100, description="Max trades per day")
    cooldown_minutes: int = Field(30, ge=0, le=240, description="Cooldown between trades")
    quiet_hours_start: Optional[str] = Field(None, description="Quiet hours start (HH:MM)")
    quiet_hours_end: Optional[str] = Field(None, description="Quiet hours end (HH:MM)")
    apply_rules_now: bool = Field(True, description="Apply rules immediately")

# Step 7: Broker Connection
class BrokerConnection(BaseModel):
    venue: str = Field(..., description="Exchange/venue name")
    api_key: str = Field(..., description="API key")
    api_secret: str = Field(..., description="API secret")
    auto_import_last_7_days: bool = Field(True, description="Auto import last 7 days")

# Step 8: Trade Import
class TradeImport(BaseModel):
    import_type: str = Field(..., description="import_type: auto or csv")
    csv_file: Optional[str] = Field(None, description="CSV file content (base64)")
    venue_preset: Optional[str] = Field(None, description="CSV venue preset")
    date_format: Optional[str] = Field(None, description="CSV date format")
    column_mapping: Optional[Dict[str, str]] = Field(None, description="CSV column mapping")

# Step 9: AI Coach Defaults
class CoachDefaults(BaseModel):
    coach_tone: str = Field("succinct", description="Coach tone preference")
    tool_permissions: Dict[str, bool] = Field(default_factory=dict, description="Tool permissions")
    data_window_days: int = Field(30, description="Data window in days")
    action_items_per_session: int = Field(1, ge=1, le=2, description="Action items per session")
    anonymized_usage_optin: bool = Field(False, description="Allow anonymized usage data")

# Step 10: Backtesting Defaults
class BacktestDefaults(BaseModel):
    default_symbol_tf: str = Field("BTC/USDT 1m", description="Default symbol and timeframe")
    fees_bps_default: float = Field(2.0, description="Default fees in basis points")
    slip_bps_default: float = Field(2.0, description="Default slippage in basis points")
    mc_runs_default: int = Field(2000, description="Default Monte Carlo runs")
    default_strategies: List[str] = Field(default_factory=list, description="Default strategies")

# Step 11: Notifications
class NotificationSettings(BaseModel):
    email_alerts: bool = Field(True, description="Enable email alerts")
    telegram_link: Optional[str] = Field(None, description="Telegram bot link")
    daily_summary_time: str = Field("21:00", description="Daily summary time")
    weekly_report_email: bool = Field(True, description="Enable weekly report emails")

# Step 12: Attribution
class AttributionData(BaseModel):
    acquisition_sources: List[str] = Field(default_factory=list, description="Acquisition sources")
    referral_code: Optional[str] = Field(None, description="Referral code")
    community_invite_optin: bool = Field(False, description="Community invite opt-in")

# Step 13: Plan Selection
class PlanSelection(BaseModel):
    plan: str = Field(..., description="Selected plan: free, plus, pro")
    coupon_code: Optional[str] = Field(None, description="Coupon code")

# Step 14: Review & Finish
class OnboardingComplete(BaseModel):
    review_confirmed: bool = Field(True, description="User confirmed review")

# Progress tracking
class OnboardingProgress(BaseModel):
    current_step: int = Field(1, ge=1, le=14)
    completed_steps: List[int] = Field(default_factory=list)
    completed: bool = Field(False)

# Response models
class OnboardingStepResponse(BaseModel):
    success: bool
    message: str
    next_step: Optional[int] = None
    progress: OnboardingProgress

class OnboardingStatusResponse(BaseModel):
    current_step: int
    completed_steps: List[int]
    total_steps: int = 14
    progress_percentage: float
    completed: bool
