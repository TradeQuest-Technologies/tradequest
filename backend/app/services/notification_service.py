import json
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
import structlog

logger = structlog.get_logger()

from app.models.notifications import (
    Notification, 
    NotificationPreference, 
    NotificationChannel,
    NotificationType
)
from app.models.user import User
from app.services.email_service import EmailService
from app.services.sms_service import SMSService


class NotificationService:
    """Service for handling notification delivery across multiple channels"""
    
    def __init__(self):
        self.email_service = EmailService()
        self.sms_service = SMSService()
    
    async def send_notification(
        self, 
        notification: Notification, 
        db: Session,
        user: Optional[User] = None
    ) -> bool:
        """Send a notification through all configured channels"""
        
        try:
            if not user:
                user = db.query(User).filter(User.id == notification.user_id).first()
                if not user:
                    logger.error("User not found for notification", notification_id=notification.id)
                    return False
            
            # Get user preferences
            preferences = db.query(NotificationPreference).filter(
                NotificationPreference.user_id == user.id
            ).first()
            
            # Parse channels
            channels = json.loads(notification.channels) if notification.channels else []
            notification_data = json.loads(notification.notification_metadata) if notification.notification_metadata else {}
            
            # Check if we should send based on quiet hours
            if preferences and self._is_quiet_hours(preferences):
                logger.info("Notification suppressed due to quiet hours", 
                          notification_id=notification.id, user_id=user.id)
                return True
            
            # Send through each channel
            delivery_tasks = []
            
            for channel in channels:
                if channel == NotificationChannel.IN_APP.value:
                    # In-app notifications are already "delivered" when created
                    continue
                
                elif channel == NotificationChannel.EMAIL.value:
                    if not preferences or preferences.email_enabled:
                        delivery_tasks.append(
                            self._send_email_notification(notification, user, notification_data)
                        )
                
                elif channel == NotificationChannel.SMS.value:
                    if not preferences or preferences.sms_enabled:
                        delivery_tasks.append(
                            self._send_sms_notification(notification, user, notification_data)
                        )
                
                elif channel == NotificationChannel.PUSH.value:
                    if not preferences or preferences.push_enabled:
                        delivery_tasks.append(
                            self._send_push_notification(notification, user, notification_data)
                        )
            
            # Execute all delivery tasks
            if delivery_tasks:
                results = await asyncio.gather(*delivery_tasks, return_exceptions=True)
                
                # Check if any delivery succeeded
                success = any(
                    result is True for result in results 
                    if not isinstance(result, Exception)
                )
                
                if success:
                    notification.is_delivered = True
                    notification.delivered_at = datetime.utcnow()
                    db.commit()
                
                return success
            
            # If only in-app, mark as delivered
            notification.is_delivered = True
            notification.delivered_at = datetime.utcnow()
            db.commit()
            return True
            
        except Exception as e:
            logger.error("Failed to send notification", 
                        notification_id=notification.id, error=str(e))
            return False
    
    async def send_bulk_notifications(
        self, 
        notifications: List[Notification], 
        db: Session
    ) -> Dict[str, Any]:
        """Send multiple notifications efficiently"""
        
        results = {
            "total": len(notifications),
            "successful": 0,
            "failed": 0,
            "errors": []
        }
        
        # Process notifications in batches to avoid overwhelming services
        batch_size = 10
        for i in range(0, len(notifications), batch_size):
            batch = notifications[i:i + batch_size]
            
            tasks = [
                self.send_notification(notification, db) 
                for notification in batch
            ]
            
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in batch_results:
                if isinstance(result, Exception):
                    results["failed"] += 1
                    results["errors"].append(str(result))
                elif result:
                    results["successful"] += 1
                else:
                    results["failed"] += 1
        
        return results
    
    async def create_and_send_notification(
        self,
        user_id: str,
        title: str,
        message: str,
        notification_type: NotificationType,
        priority: str = "medium",
        channels: List[str] = None,
        notification_data: Dict[str, Any] = None,
        db: Session = None
    ) -> Optional[Notification]:
        """Create and immediately send a notification"""
        
        if channels is None:
            channels = [NotificationChannel.IN_APP.value]
        
        notification = Notification(
            user_id=user_id,
            title=title,
            message=message,
            notification_type=notification_type,
            priority=priority,
            channels=json.dumps(channels),
            notification_metadata=json.dumps(notification_data) if notification_data else None
        )
        
        db.add(notification)
        db.commit()
        db.refresh(notification)
        
        # Send the notification
        success = await self.send_notification(notification, db)
        
        if not success:
            logger.warning("Failed to deliver notification", notification_id=notification.id)
        
        return notification
    
    async def _send_email_notification(
        self, 
        notification: Notification, 
        user: User, 
        notification_data: Dict[str, Any]
    ) -> bool:
        """Send email notification"""
        
        try:
            # Get template based on notification type
            template = self._get_email_template(notification.notification_type)
            
            # Render template with data
            subject = self._render_template(template["subject"], notification_data)
            html_content = self._render_template(template["html"], notification_data)
            text_content = self._render_template(template["text"], notification_data)
            
            # Send email
            success = await self.email_service.send_email(
                to_email=user.email,
                subject=subject,
                html_content=html_content,
                text_content=text_content
            )
            
            if success:
                logger.info("Email notification sent", 
                          notification_id=notification.id, user_email=user.email)
            
            return success
            
        except Exception as e:
            logger.error("Failed to send email notification", 
                        notification_id=notification.id, error=str(e))
            return False
    
    async def _send_sms_notification(
        self, 
        notification: Notification, 
        user: User, 
        notification_data: Dict[str, Any]
    ) -> bool:
        """Send SMS notification"""
        
        try:
            # Get user's phone number (you'll need to add this to User model)
            phone_number = getattr(user, 'phone_number', None)
            if not phone_number:
                logger.warning("No phone number for SMS notification", 
                              notification_id=notification.id, user_id=user.id)
                return False
            
            # Get template
            template = self._get_sms_template(notification.notification_type)
            message = self._render_template(template, notification_data)
            
            # Send SMS
            success = await self.sms_service.send_sms(
                phone_number=phone_number,
                message=message
            )
            
            if success:
                logger.info("SMS notification sent", 
                          notification_id=notification.id, phone_number=phone_number)
            
            return success
            
        except Exception as e:
            logger.error("Failed to send SMS notification", 
                        notification_id=notification.id, error=str(e))
            return False
    
    async def _send_push_notification(
        self, 
        notification: Notification, 
        user: User, 
        notification_data: Dict[str, Any]
    ) -> bool:
        """Send push notification (placeholder for future implementation)"""
        
        try:
            # TODO: Implement push notification service
            # For now, just log that it would be sent
            logger.info("Push notification would be sent", 
                       notification_id=notification.id, user_id=user.id)
            return True
            
        except Exception as e:
            logger.error("Failed to send push notification", 
                        notification_id=notification.id, error=str(e))
            return False
    
    def _is_quiet_hours(self, preferences: NotificationPreference) -> bool:
        """Check if current time falls within user's quiet hours"""
        
        if not preferences.quiet_hours_start or not preferences.quiet_hours_end:
            return False
        
        try:
            now = datetime.utcnow()
            start_time = datetime.strptime(preferences.quiet_hours_start, "%H:%M").time()
            end_time = datetime.strptime(preferences.quiet_hours_end, "%H:%M").time()
            current_time = now.time()
            
            # Handle quiet hours that span midnight
            if start_time <= end_time:
                return start_time <= current_time <= end_time
            else:
                return current_time >= start_time or current_time <= end_time
                
        except Exception as e:
            logger.error("Error checking quiet hours", error=str(e))
            return False
    
    def _get_email_template(self, notification_type: NotificationType) -> Dict[str, str]:
        """Get email template for notification type"""
        
        templates = {
            NotificationType.TRADE_ALERT: {
                "subject": "TradeQuest: Trade Alert - {symbol}",
                "html": """
                <html>
                <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
                    <div style="background: linear-gradient(135deg, #005F73, #FFC300); padding: 30px; text-align: center; border-radius: 10px 10px 0 0;">
                        <h1 style="color: white; margin: 0; font-size: 28px;">TradeQuest</h1>
                    </div>
                    <div style="background: #f8f9fa; padding: 30px; border-radius: 0 0 10px 10px;">
                        <h2 style="color: #333; margin-top: 0;">Trade Alert</h2>
                        <p style="color: #666; font-size: 16px; line-height: 1.5;">
                            {message}
                        </p>
                        <div style="text-align: center; margin: 30px 0;">
                            <a href="https://tradequest.app/dashboard" style="background: #005F73; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; display: inline-block;">
                                View Dashboard
                            </a>
                        </div>
                    </div>
                </body>
                </html>
                """,
                "text": "TradeQuest Trade Alert\n\n{message}\n\nView Dashboard: https://tradequest.app/dashboard"
            },
            NotificationType.PRICE_ALERT: {
                "subject": "TradeQuest: Price Alert - {symbol}",
                "html": """
                <html>
                <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
                    <div style="background: linear-gradient(135deg, #005F73, #FFC300); padding: 30px; text-align: center; border-radius: 10px 10px 0 0;">
                        <h1 style="color: white; margin: 0; font-size: 28px;">TradeQuest</h1>
                    </div>
                    <div style="background: #f8f9fa; padding: 30px; border-radius: 0 0 10px 10px;">
                        <h2 style="color: #333; margin-top: 0;">Price Alert</h2>
                        <p style="color: #666; font-size: 16px; line-height: 1.5;">
                            {message}
                        </p>
                        <div style="text-align: center; margin: 30px 0;">
                            <a href="https://tradequest.app/dashboard" style="background: #005F73; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; display: inline-block;">
                                View Dashboard
                            </a>
                        </div>
                    </div>
                </body>
                </html>
                """,
                "text": "TradeQuest Price Alert\n\n{message}\n\nView Dashboard: https://tradequest.app/dashboard"
            },
            NotificationType.SECURITY_ALERT: {
                "subject": "TradeQuest: Security Alert",
                "html": """
                <html>
                <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
                    <div style="background: linear-gradient(135deg, #dc3545, #FFC300); padding: 30px; text-align: center; border-radius: 10px 10px 0 0;">
                        <h1 style="color: white; margin: 0; font-size: 28px;">TradeQuest</h1>
                    </div>
                    <div style="background: #f8f9fa; padding: 30px; border-radius: 0 0 10px 10px;">
                        <h2 style="color: #dc3545; margin-top: 0;">Security Alert</h2>
                        <p style="color: #666; font-size: 16px; line-height: 1.5;">
                            {message}
                        </p>
                        <div style="text-align: center; margin: 30px 0;">
                            <a href="https://tradequest.app/settings" style="background: #dc3545; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; display: inline-block;">
                                Check Settings
                            </a>
                        </div>
                    </div>
                </body>
                </html>
                """,
                "text": "TradeQuest Security Alert\n\n{message}\n\nCheck Settings: https://tradequest.app/settings"
            }
        }
        
        return templates.get(notification_type, templates[NotificationType.GENERAL])
    
    def _get_sms_template(self, notification_type: NotificationType) -> str:
        """Get SMS template for notification type"""
        
        templates = {
            NotificationType.TRADE_ALERT: "TradeQuest Alert: {message}",
            NotificationType.PRICE_ALERT: "TradeQuest Price Alert: {message}",
            NotificationType.SECURITY_ALERT: "TradeQuest Security Alert: {message}",
            NotificationType.SYSTEM_UPDATE: "TradeQuest Update: {message}",
            NotificationType.ACCOUNT_UPDATE: "TradeQuest Account: {message}",
            NotificationType.MARKET_NEWS: "TradeQuest News: {message}",
            NotificationType.BACKTEST_COMPLETE: "TradeQuest Backtest Complete: {message}",
            NotificationType.JOURNAL_REMINDER: "TradeQuest Reminder: {message}",
            NotificationType.SUBSCRIPTION: "TradeQuest Subscription: {message}",
            NotificationType.GENERAL: "TradeQuest: {message}"
        }
        
        return templates.get(notification_type, templates[NotificationType.GENERAL])
    
    def _render_template(self, template: str, data: Dict[str, Any]) -> str:
        """Render template with data"""
        
        try:
            return template.format(**data)
        except KeyError as e:
            logger.warning("Missing template variable", variable=str(e))
            return template
        except Exception as e:
            logger.error("Template rendering error", error=str(e))
            return template
