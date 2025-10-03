"""
Alerts and discipline system endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel
import structlog

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.user import User

logger = structlog.get_logger()
router = APIRouter()

# Pydantic models
class AlertRule(BaseModel):
    id: Optional[str] = None
    name: str
    rule_type: str  # daily_stop, max_trades, cooldown, quiet_hours
    config: Dict[str, Any]
    enabled: bool = True

class AlertChannel(BaseModel):
    id: Optional[str] = None
    channel_type: str  # telegram, email
    config: Dict[str, Any]
    enabled: bool = True

class AlertRuleResponse(BaseModel):
    id: str
    name: str
    rule_type: str
    config: Dict[str, Any]
    enabled: bool
    created_at: datetime
    updated_at: datetime

class AlertChannelResponse(BaseModel):
    id: str
    channel_type: str
    config: Dict[str, Any]
    enabled: bool
    created_at: datetime
    updated_at: datetime

class AlertHistoryItem(BaseModel):
    id: str
    rule_id: str
    rule_name: str
    triggered_at: datetime
    details: Dict[str, Any]
    resolved_at: Optional[datetime] = None

class StreakInfo(BaseModel):
    streak_type: str
    current_streak: int
    best_streak: int
    last_achievement: Optional[datetime] = None

@router.get("/rules", response_model=List[AlertRuleResponse])
async def get_alert_rules(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all alert rules for the user"""
    
    # Mock implementation - in real app, these would be stored in database
    mock_rules = [
        {
            "id": "rule_1",
            "name": "Daily Stop Loss",
            "rule_type": "daily_stop",
            "config": {"amount": 500, "percentage": 5},
            "enabled": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        },
        {
            "id": "rule_2", 
            "name": "Max Trades Per Day",
            "rule_type": "max_trades",
            "config": {"max_trades": 10},
            "enabled": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
    ]
    
    return mock_rules

@router.post("/rules", response_model=AlertRuleResponse)
async def create_alert_rule(
    rule: AlertRule,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new alert rule"""
    
    # Mock implementation
    new_rule = {
        "id": f"rule_{len(get_alert_rules()) + 1}",
        "name": rule.name,
        "rule_type": rule.rule_type,
        "config": rule.config,
        "enabled": rule.enabled,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    
    logger.info("Alert rule created", rule_id=new_rule["id"], user_id=current_user.id)
    return new_rule

@router.put("/rules/{rule_id}", response_model=AlertRuleResponse)
async def update_alert_rule(
    rule_id: str,
    rule: AlertRule,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update an alert rule"""
    
    # Mock implementation
    updated_rule = {
        "id": rule_id,
        "name": rule.name,
        "rule_type": rule.rule_type,
        "config": rule.config,
        "enabled": rule.enabled,
        "created_at": datetime.utcnow() - timedelta(days=1),
        "updated_at": datetime.utcnow()
    }
    
    logger.info("Alert rule updated", rule_id=rule_id, user_id=current_user.id)
    return updated_rule

@router.delete("/rules/{rule_id}")
async def delete_alert_rule(
    rule_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete an alert rule"""
    
    logger.info("Alert rule deleted", rule_id=rule_id, user_id=current_user.id)
    return {"message": "Alert rule deleted successfully"}

@router.get("/channels", response_model=List[AlertChannelResponse])
async def get_alert_channels(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all alert channels for the user"""
    
    # Mock implementation
    mock_channels = [
        {
            "id": "channel_1",
            "channel_type": "telegram",
            "config": {"bot_token": "***", "chat_id": "123456789"},
            "enabled": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        },
        {
            "id": "channel_2",
            "channel_type": "email",
            "config": {"email": "user@example.com"},
            "enabled": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
    ]
    
    return mock_channels

@router.post("/channels", response_model=AlertChannelResponse)
async def create_alert_channel(
    channel: AlertChannel,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new alert channel"""
    
    # Mock implementation
    new_channel = {
        "id": f"channel_{len(get_alert_channels()) + 1}",
        "channel_type": channel.channel_type,
        "config": channel.config,
        "enabled": channel.enabled,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    
    logger.info("Alert channel created", channel_id=new_channel["id"], user_id=current_user.id)
    return new_channel

@router.post("/channels/{channel_id}/test")
async def test_alert_channel(
    channel_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Test an alert channel"""
    
    logger.info("Alert channel tested", channel_id=channel_id, user_id=current_user.id)
    return {"message": "Test alert sent successfully"}

@router.get("/history", response_model=List[AlertHistoryItem])
async def get_alert_history(
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get alert history"""
    
    # Mock implementation
    mock_history = [
        {
            "id": "alert_1",
            "rule_id": "rule_1",
            "rule_name": "Daily Stop Loss",
            "triggered_at": datetime.utcnow() - timedelta(hours=2),
            "details": {"amount": 500, "current_loss": 520},
            "resolved_at": datetime.utcnow() - timedelta(hours=1)
        },
        {
            "id": "alert_2",
            "rule_id": "rule_2",
            "rule_name": "Max Trades Per Day",
            "triggered_at": datetime.utcnow() - timedelta(days=1),
            "details": {"max_trades": 10, "current_trades": 12},
            "resolved_at": None
        }
    ]
    
    return mock_history[:limit]

@router.get("/streaks", response_model=List[StreakInfo])
async def get_alert_streaks(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get alert streaks and achievements"""
    
    # Mock implementation
    mock_streaks = [
        {
            "streak_type": "no_daily_stops",
            "current_streak": 5,
            "best_streak": 12,
            "last_achievement": datetime.utcnow() - timedelta(days=1)
        },
        {
            "streak_type": "rule_adherence",
            "current_streak": 3,
            "best_streak": 8,
            "last_achievement": datetime.utcnow() - timedelta(hours=6)
        }
    ]
    
    return mock_streaks

@router.get("/state/today")
async def get_today_alert_state(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get today's alert state for dashboard"""
    
    # Mock implementation
    today_state = {
        "daily_stop_used": 0.0,
        "daily_stop_limit": 500.0,
        "trades_today": 3,
        "max_trades_limit": 10,
        "cooldown_active": False,
        "cooldown_until": None,
        "quiet_hours_active": False,
        "quiet_hours_until": None
    }
    
    return today_state
