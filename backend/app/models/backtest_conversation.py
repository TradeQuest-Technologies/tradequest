"""
Backtest Copilot Conversation Model - Stores conversation history per strategy
"""

from sqlalchemy import Column, String, Text, Integer, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.core.database import Base


class BacktestConversation(Base):
    """Store conversation history for Backtest AI Copilot per strategy"""
    
    __tablename__ = "backtest_conversations"
    
    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    strategy_id = Column(String, ForeignKey("strategy_graphs.id"), nullable=True)  # Link to strategy
    role = Column(String, nullable=False)  # 'user' or 'assistant'
    content = Column(Text, nullable=False)
    message_data = Column(Text, nullable=True)  # JSON: changes, expected_impacts, suggested_next_steps
    message_index = Column(Integer, nullable=False)  # Order in conversation
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<BacktestConversation {self.role}: {self.content[:50]}...>"
