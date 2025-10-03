"""
Custom Venue model for user-defined brokers
"""

import uuid
from sqlalchemy import Column, String, DateTime, Boolean
from sqlalchemy.sql import func
from app.core.database import Base

class CustomVenue(Base):
    """User-defined custom venues/brokers"""
    __tablename__ = "custom_venues"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, nullable=False, index=True)
    venue_name = Column(String, nullable=False)  # Display name like "My Custom Broker"
    venue_code = Column(String, nullable=False)  # Code like "MY_CUSTOM_BROKER"
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<CustomVenue(id={self.id}, name={self.venue_name}, code={self.venue_code})>"
