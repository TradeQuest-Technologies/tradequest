"""
User and subscription models
"""

from sqlalchemy import Column, String, DateTime, Text, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from app.core.database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, unique=True, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Onboarding fields
    age_confirmed_at = Column(DateTime(timezone=True))
    tos_accepted_at = Column(DateTime(timezone=True))
    privacy_accepted_at = Column(DateTime(timezone=True))
    region = Column(String)
    onboarding_completed = Column(Boolean, default=False)
    onboarding_completed_at = Column(DateTime(timezone=True))
    
    # Security fields
    totp_enabled = Column(Boolean, default=False)
    password_hash = Column(String)
    
    # Relationships
    subscription = relationship("Subscription", back_populates="user", uselist=False)
    api_keys = relationship("ApiKey", back_populates="user")
    trades = relationship("Trade", back_populates="user")
    journal_entries = relationship("JournalEntry", back_populates="user")
    strategies = relationship("Strategy", back_populates="user")
    backtests = relationship("Backtest", back_populates="user")
    daily_metrics = relationship("DailyMetric", back_populates="user")
    notifications = relationship("Notification", back_populates="user")
    notification_preferences = relationship("NotificationPreference", back_populates="user", uselist=False)

class Subscription(Base):
    __tablename__ = "subscriptions"
    
    user_id = Column(String, ForeignKey("users.id"), primary_key=True)
    stripe_customer = Column(String)
    plan = Column(String, nullable=False, default="free")  # free, plus, pro
    status = Column(String)  # active, canceled, past_due, etc.
    updated_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="subscription")
