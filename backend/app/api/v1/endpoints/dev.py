"""
Developer API token management endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel
import structlog
import secrets
import hashlib

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.user import User

logger = structlog.get_logger()
router = APIRouter()

# Pydantic models
class ApiTokenCreate(BaseModel):
    name: str
    description: Optional[str] = None
    expires_in_days: Optional[int] = None  # None = never expires

class ApiTokenResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    token_preview: str  # First 8 chars + "..."
    created_at: datetime
    last_used: Optional[datetime]
    expires_at: Optional[datetime]
    is_active: bool

class ApiTokenUsage(BaseModel):
    date: str
    requests: int
    endpoints: Dict[str, int]

# Mock storage for API tokens (in real app, this would be a database table)
api_tokens_storage = {}

@router.get("/tokens", response_model=List[ApiTokenResponse])
async def get_api_tokens(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all API tokens for the user"""
    
    # Mock implementation - in real app, these would be stored in database
    user_tokens = []
    
    for token_id, token_data in api_tokens_storage.items():
        if token_data["user_id"] == str(current_user.id):
            user_tokens.append(ApiTokenResponse(
                id=token_id,
                name=token_data["name"],
                description=token_data["description"],
                token_preview=f"{token_data['token'][:8]}...",
                created_at=token_data["created_at"],
                last_used=token_data.get("last_used"),
                expires_at=token_data.get("expires_at"),
                is_active=token_data["is_active"]
            ))
    
    return user_tokens

@router.post("/tokens", response_model=Dict[str, str])
async def create_api_token(
    token_data: ApiTokenCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new API token"""
    
    try:
        # Generate secure token
        token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        
        # Calculate expiration
        expires_at = None
        if token_data.expires_in_days:
            expires_at = datetime.utcnow() + timedelta(days=token_data.expires_in_days)
        
        # Store token (in real app, store hash in database)
        token_id = f"token_{secrets.token_hex(8)}"
        api_tokens_storage[token_id] = {
            "user_id": str(current_user.id),
            "name": token_data.name,
            "description": token_data.description,
            "token": token,  # In real app, store hash only
            "token_hash": token_hash,
            "created_at": datetime.utcnow(),
            "expires_at": expires_at,
            "is_active": True,
            "last_used": None
        }
        
        logger.info("API token created", user_id=str(current_user.id), token_id=token_id)
        
        return {
            "token_id": token_id,
            "token": token,  # Only returned once
            "expires_at": expires_at.isoformat() if expires_at else None,
            "message": "Token created successfully. Store it securely - it won't be shown again."
        }
        
    except Exception as e:
        logger.error("API token creation failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create API token: {str(e)}"
        )

@router.put("/tokens/{token_id}")
async def update_api_token(
    token_id: str,
    token_data: ApiTokenCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update an API token (name, description)"""
    
    try:
        # Find token
        if token_id not in api_tokens_storage:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Token not found"
            )
        
        stored_token = api_tokens_storage[token_id]
        if stored_token["user_id"] != str(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        # Update token data
        stored_token["name"] = token_data.name
        stored_token["description"] = token_data.description
        
        logger.info("API token updated", user_id=str(current_user.id), token_id=token_id)
        
        return {"message": "Token updated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("API token update failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update API token: {str(e)}"
        )

@router.delete("/tokens/{token_id}")
async def revoke_api_token(
    token_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Revoke an API token"""
    
    try:
        # Find token
        if token_id not in api_tokens_storage:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Token not found"
            )
        
        stored_token = api_tokens_storage[token_id]
        if stored_token["user_id"] != str(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        # Revoke token
        stored_token["is_active"] = False
        
        logger.info("API token revoked", user_id=str(current_user.id), token_id=token_id)
        
        return {"message": "Token revoked successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("API token revocation failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to revoke API token: {str(e)}"
        )

@router.get("/tokens/{token_id}/usage")
async def get_token_usage(
    token_id: str,
    days: int = 30,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get API token usage statistics"""
    
    try:
        # Find token
        if token_id not in api_tokens_storage:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Token not found"
            )
        
        stored_token = api_tokens_storage[token_id]
        if stored_token["user_id"] != str(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        # Mock usage data
        usage_data = {
            "token_id": token_id,
            "period_days": days,
            "total_requests": 1250,
            "daily_usage": [
                {"date": "2024-01-01", "requests": 45, "endpoints": {"/api/v1/trades": 20, "/api/v1/journal": 25}},
                {"date": "2024-01-02", "requests": 38, "endpoints": {"/api/v1/trades": 15, "/api/v1/market": 23}},
                {"date": "2024-01-03", "requests": 52, "endpoints": {"/api/v1/trades": 30, "/api/v1/backtest": 22}},
            ],
            "rate_limits": {
                "requests_per_hour": 100,
                "requests_per_day": 1000,
                "current_plan": "pro"
            }
        }
        
        return usage_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Token usage retrieval failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get token usage: {str(e)}"
        )

@router.get("/rate-limits")
async def get_rate_limits(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get API rate limits for current plan"""
    
    # Mock implementation based on user plan
    # In real app, this would come from user subscription
    plan_limits = {
        "free": {
            "requests_per_hour": 10,
            "requests_per_day": 100,
            "concurrent_requests": 2
        },
        "plus": {
            "requests_per_hour": 100,
            "requests_per_day": 1000,
            "concurrent_requests": 5
        },
        "pro": {
            "requests_per_hour": 1000,
            "requests_per_day": 10000,
            "concurrent_requests": 20
        }
    }
    
    # Mock user plan
    user_plan = "pro"  # TODO: Get from user subscription
    
    return {
        "plan": user_plan,
        "limits": plan_limits[user_plan],
        "current_usage": {
            "requests_this_hour": 25,
            "requests_today": 150,
            "concurrent_requests": 1
        }
    }

@router.get("/docs")
async def get_api_docs(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get API documentation"""
    
    docs = {
        "base_url": "https://api.tradequest.com/v1",
        "authentication": {
            "type": "Bearer Token",
            "header": "Authorization: Bearer YOUR_TOKEN_HERE"
        },
        "endpoints": {
            "trades": {
                "GET /trades": "List user trades",
                "POST /trades": "Create new trade",
                "GET /trades/{id}": "Get specific trade"
            },
            "journal": {
                "GET /journal": "List journal entries",
                "POST /journal": "Create journal entry",
                "GET /journal/{id}": "Get specific journal entry"
            },
            "market": {
                "GET /market/ohlcv": "Get OHLCV data",
                "GET /market/stats": "Get market statistics"
            },
            "backtest": {
                "POST /backtest/run": "Run backtest",
                "GET /backtest/{id}": "Get backtest results"
            }
        },
        "rate_limits": "See /dev/rate-limits endpoint",
        "support": "Contact support@tradequest.com for API assistance"
    }
    
    return docs
