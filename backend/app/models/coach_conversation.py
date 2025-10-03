"""
Coach Conversation Model - Stores conversation history for context
"""

from sqlalchemy import Column, String, Text, DateTime, Integer
from sqlalchemy.sql import func
import uuid

from app.core.database import Base


class CoachConversation(Base):
    """Store conversation history for AI Coach"""
    
    __tablename__ = "coach_conversations"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), nullable=False, index=True)  # String instead of UUID for SQLite
    session_id = Column(String(100), nullable=False, index=True)  # Groups related messages
    role = Column(String(20), nullable=False)  # 'user', 'assistant', 'system'
    content = Column(Text, nullable=False)
    message_index = Column(Integer, nullable=False)  # Order in conversation
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<CoachConversation {self.role}: {self.content[:50]}...>"

