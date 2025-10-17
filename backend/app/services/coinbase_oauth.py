"""
Coinbase OAuth2 integration service
Docs: https://docs.cloud.coinbase.com/sign-in-with-coinbase/docs/api-users
"""

import requests
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import structlog
from app.core.config import settings

logger = structlog.get_logger()

class CoinbaseOAuthService:
    """Service for Coinbase OAuth2 authentication"""
    
    # Coinbase OAuth endpoints
    AUTHORIZE_URL = "https://www.coinbase.com/oauth/authorize"
    TOKEN_URL = "https://api.coinbase.com/oauth/token"
    REVOKE_URL = "https://api.coinbase.com/oauth/revoke"
    API_BASE = "https://api.coinbase.com/v2"
    
    def __init__(self, client_id: str = None, client_secret: str = None, redirect_uri: str = None):
        """
        Initialize Coinbase OAuth service
        
        Args:
            client_id: Coinbase OAuth app client ID
            client_secret: Coinbase OAuth app client secret
            redirect_uri: OAuth callback URL
        """
        self.client_id = client_id or getattr(settings, 'COINBASE_CLIENT_ID', None)
        self.client_secret = client_secret or getattr(settings, 'COINBASE_CLIENT_SECRET', None)
        self.redirect_uri = redirect_uri or getattr(settings, 'COINBASE_REDIRECT_URI', None)
    
    def get_authorization_url(self, state: str) -> str:
        """
        Generate OAuth authorization URL
        
        Args:
            state: Random state string for CSRF protection
            
        Returns:
            Authorization URL to redirect user to
        """
        params = {
            'response_type': 'code',
            'client_id': self.client_id,
            'redirect_uri': self.redirect_uri,
            'state': state,
            'scope': 'wallet:accounts:read,wallet:transactions:read,wallet:trades:read'
        }
        
        param_string = '&'.join([f"{k}={v}" for k, v in params.items()])
        return f"{self.AUTHORIZE_URL}?{param_string}"
    
    def exchange_code_for_token(self, code: str) -> Dict[str, Any]:
        """
        Exchange authorization code for access token
        
        Args:
            code: Authorization code from OAuth callback
            
        Returns:
            Dict with access_token, refresh_token, expires_in, etc.
        """
        try:
            response = requests.post(self.TOKEN_URL, data={
                'grant_type': 'authorization_code',
                'code': code,
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'redirect_uri': self.redirect_uri
            })
            
            response.raise_for_status()
            token_data = response.json()
            
            # Calculate expiration time
            expires_in = token_data.get('expires_in', 7200)  # Default 2 hours
            token_data['expires_at'] = (datetime.utcnow() + timedelta(seconds=expires_in)).isoformat()
            
            return token_data
            
        except Exception as e:
            logger.error("Failed to exchange code for token", error=str(e))
            raise
    
    def refresh_access_token(self, refresh_token: str) -> Dict[str, Any]:
        """
        Refresh an expired access token
        
        Args:
            refresh_token: Refresh token from previous authorization
            
        Returns:
            Dict with new access_token and expires_in
        """
        try:
            response = requests.post(self.TOKEN_URL, data={
                'grant_type': 'refresh_token',
                'refresh_token': refresh_token,
                'client_id': self.client_id,
                'client_secret': self.client_secret
            })
            
            response.raise_for_status()
            token_data = response.json()
            
            # Calculate expiration time
            expires_in = token_data.get('expires_in', 7200)
            token_data['expires_at'] = (datetime.utcnow() + timedelta(seconds=expires_in)).isoformat()
            
            return token_data
            
        except Exception as e:
            logger.error("Failed to refresh access token", error=str(e))
            raise
    
    def revoke_token(self, access_token: str) -> bool:
        """
        Revoke an access token
        
        Args:
            access_token: Access token to revoke
            
        Returns:
            True if successful
        """
        try:
            response = requests.post(self.REVOKE_URL, data={
                'token': access_token
            })
            
            response.raise_for_status()
            return True
            
        except Exception as e:
            logger.error("Failed to revoke token", error=str(e))
            return False
    
    def get_user_info(self, access_token: str) -> Dict[str, Any]:
        """
        Get user account information
        
        Args:
            access_token: OAuth access token
            
        Returns:
            User account info
        """
        try:
            headers = {'Authorization': f'Bearer {access_token}'}
            response = requests.get(f"{self.API_BASE}/user", headers=headers)
            response.raise_for_status()
            return response.json()
            
        except Exception as e:
            logger.error("Failed to get user info", error=str(e))
            raise
    
    def get_accounts(self, access_token: str) -> List[Dict[str, Any]]:
        """
        Get user's Coinbase accounts
        
        Args:
            access_token: OAuth access token
            
        Returns:
            List of account dictionaries
        """
        try:
            headers = {'Authorization': f'Bearer {access_token}'}
            response = requests.get(f"{self.API_BASE}/accounts", headers=headers)
            response.raise_for_status()
            
            data = response.json()
            return data.get('data', [])
            
        except Exception as e:
            logger.error("Failed to get accounts", error=str(e))
            raise

