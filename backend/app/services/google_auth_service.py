import os
import logging
from typing import Optional, Dict, Any
from google.auth.transport import requests
from google.oauth2 import id_token
from google.auth.exceptions import GoogleAuthError
from app.core.config import settings

logger = logging.getLogger(__name__)

class GoogleAuthService:
    """Google OAuth 2.0 service for authentication"""
    
    def __init__(self):
        self.client_id = settings.GOOGLE_CLIENT_ID
        
        if not self.client_id:
            logger.warning("Google OAuth not configured")
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify Google ID token and return user info"""
        if not self.client_id:
            logger.error("Google OAuth not configured")
            return None
        
        try:
            # Verify the token
            idinfo = id_token.verify_oauth2_token(
                token, 
                requests.Request(), 
                self.client_id
            )
            
            # Verify issuer
            if idinfo['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
                logger.error("Invalid token issuer")
                return None
            
            logger.info("Google token verified", email=idinfo.get('email'))
            
            return {
                'google_id': idinfo['sub'],
                'email': idinfo['email'],
                'name': idinfo.get('name'),
                'picture': idinfo.get('picture'),
                'email_verified': idinfo.get('email_verified', False)
            }
            
        except ValueError as e:
            logger.error("Invalid Google token", error=str(e))
            return None
        except GoogleAuthError as e:
            logger.error("Google auth error", error=str(e))
            return None
    
    def generate_auth_url(self, state: str = None) -> str:
        """Generate Google OAuth authorization URL"""
        base_url = "https://accounts.google.com/o/oauth2/v2/auth"
        params = {
            'client_id': self.client_id,
            'redirect_uri': f"{settings.FRONTEND_URL}/auth/google/callback",
            'scope': 'openid email profile',
            'response_type': 'code',
            'access_type': 'offline',
            'prompt': 'consent'
        }
        
        if state:
            params['state'] = state
        
        # Build URL with parameters
        param_string = '&'.join([f"{k}={v}" for k, v in params.items()])
        return f"{base_url}?{param_string}"
    
    def is_configured(self) -> bool:
        """Check if Google OAuth is properly configured"""
        return bool(self.client_id)
