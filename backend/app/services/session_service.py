"""
Session management service
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import structlog
import secrets
import hashlib

logger = structlog.get_logger()

class SessionService:
    """Service for managing user sessions"""
    
    def __init__(self):
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
    
    def create_session(self, user_id: str, user_agent: str, ip_address: str) -> str:
        """Create a new session for user"""
        
        # Generate session token
        session_token = secrets.token_urlsafe(32)
        
        # Create session data
        session_data = {
            "user_id": user_id,
            "created_at": datetime.utcnow(),
            "last_activity": datetime.utcnow(),
            "user_agent": user_agent,
            "ip_address": ip_address,
            "is_active": True
        }
        
        # Store session
        self.active_sessions[session_token] = session_data
        
        logger.info("Session created", user_id=user_id, session_token=session_token[:8])
        
        return session_token
    
    def validate_session(self, session_token: str) -> Optional[Dict[str, Any]]:
        """Validate session token and return session data"""
        
        if session_token not in self.active_sessions:
            return None
        
        session_data = self.active_sessions[session_token]
        
        # Check if session is active
        if not session_data.get("is_active", False):
            return None
        
        # Check session expiry (24 hours)
        if datetime.utcnow() - session_data["last_activity"] > timedelta(hours=24):
            self.revoke_session(session_token)
            return None
        
        # Update last activity
        session_data["last_activity"] = datetime.utcnow()
        
        return session_data
    
    def revoke_session(self, session_token: str) -> bool:
        """Revoke a session"""
        
        if session_token in self.active_sessions:
            self.active_sessions[session_token]["is_active"] = False
            logger.info("Session revoked", session_token=session_token[:8])
            return True
        
        return False
    
    def revoke_all_sessions(self, user_id: str) -> int:
        """Revoke all sessions for a user"""
        
        revoked_count = 0
        
        for session_token, session_data in self.active_sessions.items():
            if session_data["user_id"] == user_id and session_data.get("is_active", False):
                session_data["is_active"] = False
                revoked_count += 1
        
        logger.info("All sessions revoked", user_id=user_id, count=revoked_count)
        
        return revoked_count
    
    def get_user_sessions(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all active sessions for a user"""
        
        sessions = []
        
        for session_token, session_data in self.active_sessions.items():
            if (session_data["user_id"] == user_id and 
                session_data.get("is_active", False)):
                
                # Don't expose full session token
                session_info = {
                    "session_id": session_token[:8] + "...",
                    "created_at": session_data["created_at"],
                    "last_activity": session_data["last_activity"],
                    "user_agent": session_data["user_agent"],
                    "ip_address": session_data["ip_address"],
                    "is_current": False  # Will be set by caller
                }
                
                sessions.append(session_info)
        
        return sessions
    
    def cleanup_expired_sessions(self) -> int:
        """Clean up expired sessions"""
        
        expired_count = 0
        current_time = datetime.utcnow()
        
        for session_token, session_data in list(self.active_sessions.items()):
            # Remove sessions older than 7 days
            if current_time - session_data["created_at"] > timedelta(days=7):
                del self.active_sessions[session_token]
                expired_count += 1
        
        if expired_count > 0:
            logger.info("Expired sessions cleaned up", count=expired_count)
        
        return expired_count
    
    def get_session_stats(self) -> Dict[str, Any]:
        """Get session statistics"""
        
        active_count = sum(1 for s in self.active_sessions.values() if s.get("is_active", False))
        total_count = len(self.active_sessions)
        
        return {
            "active_sessions": active_count,
            "total_sessions": total_count,
            "expired_sessions": total_count - active_count
        }
