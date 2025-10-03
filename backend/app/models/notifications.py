from sqlalchemy import Column, String, DateTime, Boolean, Text, Enum, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base
import enum
import uuid


class NotificationType(str, enum.Enum):
    """Types of notifications"""
    TRADE_ALERT = "trade_alert"
    PRICE_ALERT = "price_alert"
    SYSTEM_UPDATE = "system_update"
    SECURITY_ALERT = "security_alert"
    ACCOUNT_UPDATE = "account_update"
    MARKET_NEWS = "market_news"
    BACKTEST_COMPLETE = "backtest_complete"
    JOURNAL_REMINDER = "journal_reminder"
    SUBSCRIPTION = "subscription"
    GENERAL = "general"


class NotificationPriority(str, enum.Enum):
    """Notification priority levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class NotificationChannel(str, enum.Enum):
    """Delivery channels for notifications"""
    IN_APP = "in_app"
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"


class Notification(Base):
    """User notifications"""
    __tablename__ = "notifications"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    
    # Notification content
    title = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    notification_type = Column(Enum(NotificationType), nullable=False)
    priority = Column(Enum(NotificationPriority), default=NotificationPriority.MEDIUM)
    
    # Delivery settings
    channels = Column(Text)  # JSON array of NotificationChannel values
    
    # Status tracking
    is_read = Column(Boolean, default=False)
    is_delivered = Column(Boolean, default=False)
    
    # Metadata
    notification_metadata = Column(Text)  # JSON for additional data (e.g., trade_id, price, etc.)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    read_at = Column(DateTime(timezone=True), nullable=True)
    delivered_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="notifications")


class NotificationPreference(Base):
    """User notification preferences"""
    __tablename__ = "notification_preferences"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False, unique=True)
    
    # Channel preferences
    email_enabled = Column(Boolean, default=True)
    sms_enabled = Column(Boolean, default=False)
    push_enabled = Column(Boolean, default=True)
    in_app_enabled = Column(Boolean, default=True)
    
    # Type-specific preferences (JSON)
    type_preferences = Column(Text)  # JSON: {notification_type: {channel: enabled}}
    
    # Quiet hours
    quiet_hours_start = Column(String, nullable=True)  # HH:MM format
    quiet_hours_end = Column(String, nullable=True)    # HH:MM format
    quiet_hours_timezone = Column(String, default="UTC")
    
    # Frequency limits
    email_frequency_limit = Column(String, default="immediate")  # immediate, hourly, daily
    sms_frequency_limit = Column(String, default="daily")        # immediate, hourly, daily
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="notification_preferences")


class NotificationTemplate(Base):
    """Notification templates for different types"""
    __tablename__ = "notification_templates"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Template identification
    template_key = Column(String, nullable=False, unique=True)
    notification_type = Column(Enum(NotificationType), nullable=False)
    
    # Template content
    title_template = Column(String, nullable=False)
    message_template = Column(Text, nullable=False)
    
    # Channel-specific templates
    email_subject_template = Column(String, nullable=True)
    email_html_template = Column(Text, nullable=True)
    sms_template = Column(Text, nullable=True)
    
    # Default settings
    default_channels = Column(Text)  # JSON array of default channels
    default_priority = Column(Enum(NotificationPriority), default=NotificationPriority.MEDIUM)
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
