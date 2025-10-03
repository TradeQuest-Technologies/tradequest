from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from typing import List, Optional
import json
from datetime import datetime

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.user import User
from app.models.notifications import (
    Notification, 
    NotificationPreference, 
    NotificationType, 
    NotificationPriority, 
    NotificationChannel
)
from app.schemas.notifications import (
    NotificationCreate,
    NotificationResponse,
    NotificationListResponse,
    NotificationMarkRead,
    NotificationPreferenceResponse,
    NotificationPreferenceUpdate,
    NotificationStatsResponse
)
from app.services.notification_service import NotificationService

router = APIRouter()


@router.get("", response_model=NotificationListResponse)
@router.get("/", response_model=NotificationListResponse)
async def get_notifications(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    unread_only: bool = Query(False),
    notification_type: Optional[NotificationType] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user notifications with pagination and filtering"""
    
    query = db.query(Notification).filter(Notification.user_id == current_user.id)
    
    if unread_only:
        query = query.filter(Notification.is_read == False)
    
    if notification_type:
        query = query.filter(Notification.notification_type == notification_type)
    
    # Get total counts
    total_count = query.count()
    unread_count = db.query(Notification).filter(
        Notification.user_id == current_user.id,
        Notification.is_read == False
    ).count()
    
    # Apply pagination and ordering
    notifications = query.order_by(desc(Notification.created_at)).offset(
        (page - 1) * page_size
    ).limit(page_size).all()
    
    # Convert channels from JSON string to list
    notification_responses = []
    for notif in notifications:
        channels = json.loads(notif.channels) if notif.channels else []
        notification_data = json.loads(notif.notification_metadata) if notif.notification_metadata else None
        
        notification_responses.append(NotificationResponse(
            id=notif.id,
            user_id=notif.user_id,
            title=notif.title,
            message=notif.message,
            notification_type=notif.notification_type,
            priority=notif.priority,
            channels=channels,
            is_read=notif.is_read,
            is_delivered=notif.is_delivered,
            metadata=notification_data,
            created_at=notif.created_at,
            read_at=notif.read_at,
            delivered_at=notif.delivered_at
        ))
    
    return NotificationListResponse(
        notifications=notification_responses,
        total_count=total_count,
        unread_count=unread_count,
        page=page,
        page_size=page_size,
        has_more=(page * page_size) < total_count
    )


@router.get("/stats", response_model=NotificationStatsResponse)
async def get_notification_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get notification statistics for the user"""
    
    # Total notifications
    total_notifications = db.query(Notification).filter(
        Notification.user_id == current_user.id
    ).count()
    
    # Unread notifications
    unread_notifications = db.query(Notification).filter(
        Notification.user_id == current_user.id,
        Notification.is_read == False
    ).count()
    
    # Notifications by type
    type_stats = db.query(
        Notification.notification_type,
        func.count(Notification.id)
    ).filter(
        Notification.user_id == current_user.id
    ).group_by(Notification.notification_type).all()
    
    notifications_by_type = {str(ntype): count for ntype, count in type_stats}
    
    # Notifications by priority
    priority_stats = db.query(
        Notification.priority,
        func.count(Notification.id)
    ).filter(
        Notification.user_id == current_user.id
    ).group_by(Notification.priority).all()
    
    notifications_by_priority = {str(priority): count for priority, count in priority_stats}
    
    # Recent activity (last 5 notifications)
    recent_notifications = db.query(Notification).filter(
        Notification.user_id == current_user.id
    ).order_by(desc(Notification.created_at)).limit(5).all()
    
    recent_activity = []
    for notif in recent_notifications:
        channels = json.loads(notif.channels) if notif.channels else []
        notification_data = json.loads(notif.notification_metadata) if notif.notification_metadata else None
        
        recent_activity.append(NotificationResponse(
            id=notif.id,
            user_id=notif.user_id,
            title=notif.title,
            message=notif.message,
            notification_type=notif.notification_type,
            priority=notif.priority,
            channels=channels,
            is_read=notif.is_read,
            is_delivered=notif.is_delivered,
            metadata=notification_data,
            created_at=notif.created_at,
            read_at=notif.read_at,
            delivered_at=notif.delivered_at
        ))
    
    return NotificationStatsResponse(
        total_notifications=total_notifications,
        unread_notifications=unread_notifications,
        notifications_by_type=notifications_by_type,
        notifications_by_priority=notifications_by_priority,
        recent_activity=recent_activity
    )


@router.post("/mark-read", response_model=dict)
async def mark_notifications_read(
    request: NotificationMarkRead,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Mark notifications as read"""
    
    notifications = db.query(Notification).filter(
        Notification.id.in_(request.notification_ids),
        Notification.user_id == current_user.id
    ).all()
    
    if not notifications:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No notifications found"
        )
    
    # Mark as read
    for notification in notifications:
        notification.is_read = True
        notification.read_at = datetime.utcnow()
    
    db.commit()
    
    return {
        "message": f"Marked {len(notifications)} notifications as read",
        "marked_count": len(notifications)
    }


@router.post("/mark-all-read", response_model=dict)
async def mark_all_notifications_read(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Mark all notifications as read"""
    
    updated_count = db.query(Notification).filter(
        Notification.user_id == current_user.id,
        Notification.is_read == False
    ).update({
        "is_read": True,
        "read_at": datetime.utcnow()
    })
    
    db.commit()
    
    return {
        "message": f"Marked {updated_count} notifications as read",
        "marked_count": updated_count
    }


@router.get("/preferences", response_model=NotificationPreferenceResponse)
async def get_notification_preferences(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user notification preferences"""
    
    preferences = db.query(NotificationPreference).filter(
        NotificationPreference.user_id == current_user.id
    ).first()
    
    if not preferences:
        # Create default preferences
        preferences = NotificationPreference(
            user_id=current_user.id,
            email_enabled=True,
            sms_enabled=False,
            push_enabled=True,
            in_app_enabled=True,
            type_preferences=json.dumps({}),
            quiet_hours_timezone="UTC",
            email_frequency_limit="immediate",
            sms_frequency_limit="daily"
        )
        db.add(preferences)
        db.commit()
        db.refresh(preferences)
    
    type_prefs = json.loads(preferences.type_preferences) if preferences.type_preferences else {}
    
    return NotificationPreferenceResponse(
        id=preferences.id,
        user_id=preferences.user_id,
        email_enabled=preferences.email_enabled,
        sms_enabled=preferences.sms_enabled,
        push_enabled=preferences.push_enabled,
        in_app_enabled=preferences.in_app_enabled,
        type_preferences=type_prefs,
        quiet_hours_start=preferences.quiet_hours_start,
        quiet_hours_end=preferences.quiet_hours_end,
        quiet_hours_timezone=preferences.quiet_hours_timezone,
        email_frequency_limit=preferences.email_frequency_limit,
        sms_frequency_limit=preferences.sms_frequency_limit,
        created_at=preferences.created_at,
        updated_at=preferences.updated_at
    )


@router.put("/preferences", response_model=NotificationPreferenceResponse)
async def update_notification_preferences(
    request: NotificationPreferenceUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update user notification preferences"""
    
    preferences = db.query(NotificationPreference).filter(
        NotificationPreference.user_id == current_user.id
    ).first()
    
    if not preferences:
        preferences = NotificationPreference(user_id=current_user.id)
        db.add(preferences)
    
    # Update fields
    update_data = request.dict(exclude_unset=True)
    for field, value in update_data.items():
        if field == "type_preferences" and value is not None:
            setattr(preferences, field, json.dumps(value))
        else:
            setattr(preferences, field, value)
    
    preferences.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(preferences)
    
    type_prefs = json.loads(preferences.type_preferences) if preferences.type_preferences else {}
    
    return NotificationPreferenceResponse(
        id=preferences.id,
        user_id=preferences.user_id,
        email_enabled=preferences.email_enabled,
        sms_enabled=preferences.sms_enabled,
        push_enabled=preferences.push_enabled,
        in_app_enabled=preferences.in_app_enabled,
        type_preferences=type_prefs,
        quiet_hours_start=preferences.quiet_hours_start,
        quiet_hours_end=preferences.quiet_hours_end,
        quiet_hours_timezone=preferences.quiet_hours_timezone,
        email_frequency_limit=preferences.email_frequency_limit,
        sms_frequency_limit=preferences.sms_frequency_limit,
        created_at=preferences.created_at,
        updated_at=preferences.updated_at
    )


@router.post("/test/sample", response_model=dict)
async def create_sample_notifications(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create sample notifications for testing"""
    
    notification_service = NotificationService()
    
    sample_notifications = [
        {
            "title": "Trade Alert: BTC/USD",
            "message": "BUY signal for BTC/USD at $45,250 - Strong bullish momentum detected",
            "notification_type": NotificationType.TRADE_ALERT,
            "priority": NotificationPriority.HIGH,
            "channels": [NotificationChannel.IN_APP, NotificationChannel.EMAIL],
            "metadata": {"symbol": "BTC/USD", "action": "buy", "price": 45250, "reason": "Strong bullish momentum"}
        },
        {
            "title": "Price Alert: ETH/USD",
            "message": "ETH/USD is now $3,200, above your target of $3,000",
            "notification_type": NotificationType.PRICE_ALERT,
            "priority": NotificationPriority.MEDIUM,
            "channels": [NotificationChannel.IN_APP, NotificationChannel.EMAIL],
            "metadata": {"symbol": "ETH/USD", "currentPrice": 3200, "targetPrice": 3000, "direction": "above"}
        },
        {
            "title": "Security Alert: New Login",
            "message": "A new login was detected from Chrome on Windows - IP: 192.168.1.100",
            "notification_type": NotificationType.SECURITY_ALERT,
            "priority": NotificationPriority.URGENT,
            "channels": [NotificationChannel.IN_APP, NotificationChannel.EMAIL, NotificationChannel.SMS],
            "metadata": {"type": "login", "browser": "Chrome", "os": "Windows", "ip": "192.168.1.100"}
        },
        {
            "title": "Backtest Complete: RSI Strategy",
            "message": "Strategy completed with 45 trades, 68.9% win rate, +$1,250.50 P&L",
            "notification_type": NotificationType.BACKTEST_COMPLETE,
            "priority": NotificationPriority.MEDIUM,
            "channels": [NotificationChannel.IN_APP, NotificationChannel.EMAIL],
            "metadata": {"strategyName": "RSI Strategy", "totalTrades": 45, "winRate": 0.689, "profitLoss": 1250.50}
        },
        {
            "title": "Journal Reminder",
            "message": "It's been 3 days since your last journal entry. Consider documenting your recent trades.",
            "notification_type": NotificationType.JOURNAL_REMINDER,
            "priority": NotificationPriority.LOW,
            "channels": [NotificationChannel.IN_APP],
            "metadata": {"daysSinceLastEntry": 3, "suggestedAction": "Consider documenting your recent trades"}
        }
    ]
    
    created_notifications = []
    
    for notif_data in sample_notifications:
        notification = await notification_service.create_and_send_notification(
            user_id=current_user.id,
            title=notif_data["title"],
            message=notif_data["message"],
            notification_type=notif_data["notification_type"],
            priority=notif_data["priority"].value,
            channels=[channel.value for channel in notif_data["channels"]],
            notification_data=notif_data["metadata"],
            db=db
        )
        
        if notification:
            created_notifications.append(notification.id)
    
    return {
        "message": f"Created {len(created_notifications)} sample notifications",
        "notification_ids": created_notifications
    }
