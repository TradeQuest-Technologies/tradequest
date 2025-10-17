"""
Custom Block Models - User-created blocks for backtesting
"""

from sqlalchemy import Column, String, Text, Boolean, Integer, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from app.core.database import Base


class CustomBlock(Base):
    """User-created custom blocks"""
    
    __tablename__ = "custom_blocks"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    
    # Block metadata
    name = Column(String, nullable=False)  # e.g., "Advanced RSI Divergence"
    description = Column(Text)
    category = Column(String, nullable=False)  # data, feature, signal, sizing, risk, exec
    
    # Block definition (Python code)
    code = Column(Text, nullable=False)  # Python function that defines the block
    
    # Input/output schema
    input_schema = Column(Text)  # JSON schema for inputs
    output_schema = Column(Text)  # JSON schema for outputs
    parameters = Column(Text)  # JSON schema for parameters
    
    # Publishing
    is_public = Column(Boolean, default=False)
    is_verified = Column(Boolean, default=False)  # Admin verified
    downloads = Column(Integer, default=0)
    rating = Column(Integer, default=0)  # Average rating * 100
    rating_count = Column(Integer, default=0)
    
    # Metadata
    version = Column(String, default="1.0.0")
    tags = Column(Text)  # JSON array of tags
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_custom_blocks_user', 'user_id'),
        Index('idx_custom_blocks_public', 'is_public'),
        Index('idx_custom_blocks_category', 'category'),
    )


class UserBlockLibrary(Base):
    """Tracks which blocks a user has added to their library"""
    
    __tablename__ = "user_block_library"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    block_id = Column(String, ForeignKey("custom_blocks.id"), nullable=False)
    added_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Indexes
    __table_args__ = (
        Index('idx_user_block_library_user', 'user_id'),
        Index('idx_user_block_library_unique', 'user_id', 'block_id', unique=True),
    )


class BlockRating(Base):
    """User ratings for public blocks"""
    
    __tablename__ = "block_ratings"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    block_id = Column(String, ForeignKey("custom_blocks.id"), nullable=False)
    rating = Column(Integer, nullable=False)  # 1-5 stars
    comment = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Indexes
    __table_args__ = (
        Index('idx_block_ratings_block', 'block_id'),
        Index('idx_block_ratings_unique', 'user_id', 'block_id', unique=True),
    )
