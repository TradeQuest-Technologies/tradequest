"""
Onboarding-related models
"""

from sqlalchemy import Column, String, DateTime, Text, Boolean, Integer, Float, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from app.core.database import Base
from app.core.database_utils import create_json_column

class UserProfile(Base):
    __tablename__ = "user_profiles"
    
    user_id = Column(String, ForeignKey("users.id"), primary_key=True)
    # Identity
    legal_name = Column(String)  # legacy combined name
    first_name = Column(String)
    last_name = Column(String)
    birth_date = Column(String)  # ISO date YYYY-MM-DD
    alias = Column(String)
    timezone = Column(String, default="UTC")
    display_currency = Column(String, default="USD")
    pnl_visibility_default = Column(Boolean, default=True)
    
    # Trading profile
    experience_level = Column(String)  # beginner, intermediate, advanced
    markets = create_json_column()  # JSON array of markets
    style = create_json_column()  # JSON array of trading styles
    timeframes = create_json_column()  # JSON array of timeframes
    platforms = create_json_column()  # JSON array of platforms
    days_active_per_week = Column(Integer, default=3)
    session_pref = create_json_column()  # JSON array of session preferences
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class UserGoals(Base):
    __tablename__ = "user_goals"
    
    user_id = Column(String, ForeignKey("users.id"), primary_key=True)
    primary_goal = Column(String)  # profitability, discipline, learn_strategy
    account_size_band = Column(String)  # <500, 500-2k, 2k-10k, 10k-50k, 50k+
    risk_per_trade_pct = Column(Float, default=1.0)
    target_mdd_pct = Column(Float, default=10.0)
    target_winrate_hint = Column(Float)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class UserSecurity(Base):
    __tablename__ = "user_security"
    
    user_id = Column(String, ForeignKey("users.id"), primary_key=True)
    password_hash = Column(String)
    
    # 2FA settings
    two_factor_method = Column(String, default="email")  # email, sms, google_auth, totp
    totp_secret = Column(String)
    totp_enabled = Column(Boolean, default=False)
    backup_codes_hash = Column(Text)  # JSON array of hashed backup codes
    
    # Phone number for SMS 2FA
    phone_number = Column(String)
    phone_verified = Column(Boolean, default=False)
    
    # Google Auth settings
    google_auth_enabled = Column(Boolean, default=False)
    google_auth_secret = Column(String)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class AlertRules(Base):
    __tablename__ = "alert_rules"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    daily_stop_type = Column(String)  # percent, fixed
    daily_stop_value = Column(Float)
    max_trades_per_day = Column(Integer, default=5)
    cooldown_minutes = Column(Integer, default=30)
    quiet_hours_start = Column(String)  # HH:MM format
    quiet_hours_end = Column(String)  # HH:MM format
    enabled = Column(Boolean, default=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class CoachPreferences(Base):
    __tablename__ = "coach_preferences"
    
    user_id = Column(String, ForeignKey("users.id"), primary_key=True)
    tone = Column(String, default="succinct")  # succinct, detailed
    tools_allowed = Column(Text)  # JSON array of allowed tools
    data_window_days = Column(Integer, default=30)
    action_items_per_session = Column(Integer, default=1)
    anonymized_optin = Column(Boolean, default=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class BacktestPreferences(Base):
    __tablename__ = "backtest_preferences"
    
    user_id = Column(String, ForeignKey("users.id"), primary_key=True)
    default_symbol = Column(String, default="BTC/USDT")
    default_timeframe = Column(String, default="1m")
    fees_bps_default = Column(Float, default=2.0)
    slip_bps_default = Column(Float, default=2.0)
    mc_runs_default = Column(Integer, default=2000)
    default_strategies = Column(Text)  # JSON array of default strategies
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class NotificationSettings(Base):
    __tablename__ = "notification_settings"
    
    user_id = Column(String, ForeignKey("users.id"), primary_key=True)
    email_enabled = Column(Boolean, default=True)
    push_enabled = Column(Boolean, default=True)
    sms_enabled = Column(Boolean, default=False)
    in_app_enabled = Column(Boolean, default=True)
    quiet_hours_start = Column(String)  # HH:MM format
    quiet_hours_end = Column(String)    # HH:MM format
    email_frequency_limit = Column(String, default="immediate")
    sms_frequency_limit = Column(String, default="daily")
    telegram_user_id = Column(String)  # Legacy field
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class MarketingProfile(Base):
    __tablename__ = "marketing_profiles"
    
    user_id = Column(String, ForeignKey("users.id"), primary_key=True)
    acquisition_sources = Column(Text)  # JSON array of sources
    referral_code = Column(String)
    community_invite_optin = Column(Boolean, default=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class OnboardingProgress(Base):
    __tablename__ = "onboarding_progress"
    
    user_id = Column(String, ForeignKey("users.id"), primary_key=True)
    current_step = Column(Integer, default=1)
    completed_steps = Column(Text)  # JSON array of completed step numbers
    completed_at = Column(DateTime(timezone=True))
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
