from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from app.models.notifications import NotificationType, NotificationPriority, NotificationChannel


class NotificationCreate(BaseModel):
    """Schema for creating a notification"""
    title: str = Field(..., description="Notification title")
    message: str = Field(..., description="Notification message")
    notification_type: NotificationType = Field(..., description="Type of notification")
    priority: NotificationPriority = Field(NotificationPriority.MEDIUM, description="Priority level")
    channels: List[NotificationChannel] = Field([NotificationChannel.IN_APP], description="Delivery channels")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class NotificationResponse(BaseModel):
    """Schema for notification response"""
    id: str
    user_id: str
    title: str
    message: str
    notification_type: NotificationType
    priority: NotificationPriority
    channels: List[NotificationChannel]
    is_read: bool
    is_delivered: bool
    metadata: Optional[Dict[str, Any]]
    created_at: datetime
    read_at: Optional[datetime]
    delivered_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class NotificationListResponse(BaseModel):
    """Schema for notification list response"""
    notifications: List[NotificationResponse]
    total_count: int
    unread_count: int
    page: int
    page_size: int
    has_more: bool


class NotificationMarkRead(BaseModel):
    """Schema for marking notifications as read"""
    notification_ids: List[str] = Field(..., description="List of notification IDs to mark as read")


class NotificationPreferenceResponse(BaseModel):
    """Schema for notification preferences"""
    id: str
    user_id: str
    email_enabled: bool
    sms_enabled: bool
    push_enabled: bool
    in_app_enabled: bool
    type_preferences: Optional[Dict[str, Dict[str, bool]]]
    quiet_hours_start: Optional[str]
    quiet_hours_end: Optional[str]
    quiet_hours_timezone: str
    email_frequency_limit: str
    sms_frequency_limit: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class NotificationPreferenceUpdate(BaseModel):
    """Schema for updating notification preferences"""
    email_enabled: Optional[bool] = None
    sms_enabled: Optional[bool] = None
    push_enabled: Optional[bool] = None
    in_app_enabled: Optional[bool] = None
    type_preferences: Optional[Dict[str, Dict[str, bool]]] = None
    quiet_hours_start: Optional[str] = None
    quiet_hours_end: Optional[str] = None
    quiet_hours_timezone: Optional[str] = None
    email_frequency_limit: Optional[str] = None
    sms_frequency_limit: Optional[str] = None


class NotificationStatsResponse(BaseModel):
    """Schema for notification statistics"""
    total_notifications: int
    unread_notifications: int
    notifications_by_type: Dict[str, int]
    notifications_by_priority: Dict[str, int]
    recent_activity: List[NotificationResponse]
