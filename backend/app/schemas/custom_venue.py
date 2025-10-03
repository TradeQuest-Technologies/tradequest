"""
Custom Venue schemas
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class CustomVenueBase(BaseModel):
    venue_name: str = Field(..., description="Display name for the venue")
    venue_code: str = Field(..., description="Code for the venue")

class CustomVenueCreate(CustomVenueBase):
    pass

class CustomVenueUpdate(BaseModel):
    venue_name: Optional[str] = None
    venue_code: Optional[str] = None
    is_active: Optional[bool] = None

class CustomVenueResponse(CustomVenueBase):
    id: str
    user_id: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class VenueListResponse(BaseModel):
    standard_venues: List[str]
    custom_venues: List[CustomVenueResponse]
