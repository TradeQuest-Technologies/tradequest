"""
Broker OAuth endpoints (for Coinbase OAuth2 flow)
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
import structlog
import secrets
import uuid
from datetime import datetime

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.user import User
from app.models.api_key import ApiKey
from app.services.coinbase_oauth import CoinbaseOAuthService
from app.services.encryption_service import encryption_service

logger = structlog.get_logger()

router = APIRouter()

# In-memory store for OAuth states (use Redis in production)
oauth_states = {}

@router.get("/coinbase/authorize")
async def coinbase_authorize(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Initiate Coinbase OAuth2 flow
    
    Returns redirect URL to Coinbase authorization page
    """
    
    # Generate random state for CSRF protection
    state = secrets.token_urlsafe(32)
    
    # Store state with user ID
    oauth_states[state] = {
        'user_id': current_user.id,
        'venue': 'coinbase',
        'created_at': datetime.utcnow().isoformat()
    }
    
    # Generate authorization URL
    oauth_service = CoinbaseOAuthService()
    auth_url = oauth_service.get_authorization_url(state)
    
    logger.info("Coinbase OAuth initiated", user_id=current_user.id)
    
    return {
        'authorization_url': auth_url,
        'state': state
    }

@router.get("/coinbase/callback")
async def coinbase_callback(
    code: str,
    state: str,
    db: Session = Depends(get_db)
):
    """
    OAuth2 callback endpoint for Coinbase
    
    User is redirected here after authorizing the app on Coinbase
    """
    
    # Verify state
    state_data = oauth_states.get(state)
    if not state_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired state parameter"
        )
    
    user_id = state_data['user_id']
    
    # Clean up state
    del oauth_states[state]
    
    try:
        # Exchange code for access token
        oauth_service = CoinbaseOAuthService()
        token_data = oauth_service.exchange_code_for_token(code)
        
        access_token = token_data.get('access_token')
        refresh_token = token_data.get('refresh_token')
        expires_at = token_data.get('expires_at')
        
        # Get user info to verify connection
        user_info = oauth_service.get_user_info(access_token)
        
        # Check if already connected
        existing = db.query(ApiKey).filter(
            ApiKey.user_id == user_id,
            ApiKey.venue == 'coinbase'
        ).first()
        
        if existing:
            # Update existing connection
            existing.key_enc = encryption_service.encrypt(access_token)
            existing.secret_enc = encryption_service.encrypt(refresh_token)
            existing.meta = {
                'expires_at': expires_at,
                'user_info': user_info,
                'auth_method': 'oauth2'
            }
            db.commit()
            api_key_id = existing.id
        else:
            # Create new connection
            api_key_id = str(uuid.uuid4())
            new_api_key = ApiKey(
                id=api_key_id,
                user_id=user_id,
                venue='coinbase',
                key_enc=encryption_service.encrypt(access_token),
                secret_enc=encryption_service.encrypt(refresh_token),
                meta={
                    'expires_at': expires_at,
                    'user_info': user_info,
                    'auth_method': 'oauth2'
                }
            )
            db.add(new_api_key)
            db.commit()
        
        logger.info("Coinbase OAuth completed", user_id=user_id)
        
        # Redirect to frontend with success
        from app.core.config import settings
        frontend_url = settings.CORS_ORIGINS[0] if settings.CORS_ORIGINS else "http://localhost:3000"
        return RedirectResponse(url=f"{frontend_url}/brokers?connected=coinbase")
        
    except Exception as e:
        logger.error("OAuth callback failed", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to complete OAuth: {str(e)}"
        )

