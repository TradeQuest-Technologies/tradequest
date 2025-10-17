"""
Broker API Key model for storing encrypted credentials
"""

from sqlalchemy import Column, String, DateTime, ForeignKey, LargeBinary
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
from app.core.database_utils import create_json_column

class ApiKey(Base):
    __tablename__ = "api_keys"
    
    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    venue = Column(String, nullable=False, index=True)  # 'hyperliquid', 'kraken', 'coinbase', etc.
    
    # Encrypted credentials (using Fernet encryption)
    key_enc = Column(LargeBinary, nullable=False)  # Encrypted API key
    secret_enc = Column(LargeBinary, nullable=False)  # Encrypted API secret
    
    # Additional metadata (connection info, last sync, etc.)
    meta = create_json_column()  # JSONB for PostgreSQL, TEXT for SQLite
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="api_keys")
    
    def __repr__(self):
        return f"<ApiKey(id={self.id}, user_id={self.user_id}, venue={self.venue})>"

