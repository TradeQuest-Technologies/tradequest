"""
Messaging integration endpoints (Telegram, Email)
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
from pydantic import BaseModel
import structlog

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.user import User
from app.services.email_service import EmailService
from app.services.telegram_service import TelegramService

logger = structlog.get_logger()
router = APIRouter()

# Pydantic models
class TelegramLink(BaseModel):
    bot_token: str
    chat_id: str

class EmailConfig(BaseModel):
    email: str
    verified: bool = False

class MessageTest(BaseModel):
    message: str
    channel_type: str  # telegram, email

@router.post("/telegram/link")
async def link_telegram(
    telegram_config: TelegramLink,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Link Telegram bot for alerts"""
    
    try:
        # Initialize Telegram service
        telegram_service = TelegramService()
        
        # Send test message to verify the chat_id
        test_success = await telegram_service.send_test_message(telegram_config.chat_id)
        
        if not test_success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to send test message. Please check your chat ID."
            )
        
        # TODO: Store the configuration securely in database
        # For now, just return success
        
        logger.info("Telegram linked", user_id=str(current_user.id), chat_id=telegram_config.chat_id)
        
        return {
            "message": "Telegram successfully linked",
            "chat_id": telegram_config.chat_id,
            "verified": True
        }
        
    except Exception as e:
        logger.error("Telegram linking failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to link Telegram: {str(e)}"
        )

@router.post("/telegram/unlink")
async def unlink_telegram(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Unlink Telegram bot"""
    
    try:
        # TODO: Remove Telegram configuration from user settings
        
        logger.info("Telegram unlinked", user_id=str(current_user.id))
        
        return {"message": "Telegram successfully unlinked"}
        
    except Exception as e:
        logger.error("Telegram unlinking failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to unlink Telegram: {str(e)}"
        )

@router.post("/email/verify")
async def verify_email(
    email_config: EmailConfig,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Verify email address for alerts"""
    
    try:
        # Initialize email service
        email_service = EmailService()
        
        # Generate verification token (in real app, store in database)
        verification_token = f"verify_{current_user.id}_{email_config.email}"
        
        # Send verification email
        email_sent = await email_service.send_verification_email(email_config.email, verification_token)
        
        if not email_sent:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to send verification email"
            )
        
        logger.info("Email verification initiated", user_id=str(current_user.id), email=email_config.email)
        
        return {
            "message": "Verification email sent",
            "email": email_config.email,
            "verified": False
        }
        
    except Exception as e:
        logger.error("Email verification failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send verification email: {str(e)}"
        )

@router.post("/email/confirm")
async def confirm_email(
    token: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Confirm email verification token"""
    
    try:
        # TODO: Validate verification token
        # For now, just return success
        
        logger.info("Email confirmed", user_id=str(current_user.id))
        
        return {
            "message": "Email successfully verified",
            "verified": True
        }
        
    except Exception as e:
        logger.error("Email confirmation failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid verification token: {str(e)}"
        )

@router.post("/test")
async def test_message(
    test_config: MessageTest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Send test message to verify channel"""
    
    try:
        if test_config.channel_type == "telegram":
            # TODO: Get user's Telegram chat ID from database
            chat_id = "123456789"  # Mock chat ID
            
            telegram_service = TelegramService()
            success = await telegram_service.send_test_message(chat_id)
            
            if success:
                logger.info("Test message sent via Telegram", user_id=str(current_user.id))
                return {"message": "Test message sent via Telegram", "channel": "telegram"}
            else:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to send Telegram test message"
                )
            
        elif test_config.channel_type == "email":
            # TODO: Get user's email from database
            user_email = current_user.email
            
            email_service = EmailService()
            success = await email_service.send_alert_email(user_email, {
                "message": "This is a test message from TradeQuest.",
                "rule_name": "Test Alert",
                "triggered_at": "Now",
                "status": "Test"
            })
            
            if success:
                logger.info("Test email sent", user_id=str(current_user.id))
                return {"message": "Test email sent", "channel": "email"}
            else:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to send test email"
                )
            
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unsupported channel type. Use 'telegram' or 'email'"
            )
        
    except Exception as e:
        logger.error("Test message failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send test message: {str(e)}"
        )

@router.get("/status")
async def get_messaging_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get messaging channel status"""
    
    # Mock implementation
    status = {
        "telegram": {
            "linked": True,
            "verified": True,
            "chat_id": "123456789"
        },
        "email": {
            "linked": True,
            "verified": True,
            "email": "user@example.com"
        }
    }
    
    return status
