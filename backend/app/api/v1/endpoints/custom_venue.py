"""
Custom Venue endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import structlog

from app.core.database import get_db
from app.core.auth import get_current_user
from app.schemas.custom_venue import CustomVenueCreate, CustomVenueResponse, CustomVenueUpdate, VenueListResponse
from app.models.user import User
from app.models.custom_venue import CustomVenue

logger = structlog.get_logger()
router = APIRouter()

# Standard venues that are always available
STANDARD_VENUES = [
    "MANUAL",
    "INTERACTIVE_BROKERS",
    "TD_AMERITRADE", 
    "SCHWAB",
    "ETRADE",
    "ROBINHOOD",
    "WEBULL",
    "ALPACA",
    "BINANCE",
    "KRAKEN",
    "COINBASE"
]

@router.get("/venues", response_model=VenueListResponse)
async def get_user_venues(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all venues available to the user (standard + custom)"""
    
    custom_venues = db.query(CustomVenue).filter(
        CustomVenue.user_id == current_user.id,
        CustomVenue.is_active == True
    ).all()
    
    return VenueListResponse(
        standard_venues=STANDARD_VENUES,
        custom_venues=custom_venues
    )

@router.post("/venues", response_model=CustomVenueResponse)
async def create_custom_venue(
    venue_data: CustomVenueCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new custom venue"""
    
    # Check if venue code already exists for this user
    existing_venue = db.query(CustomVenue).filter(
        CustomVenue.user_id == current_user.id,
        CustomVenue.venue_code == venue_data.venue_code.upper()
    ).first()
    
    if existing_venue:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A venue with this code already exists"
        )
    
    # Check if it conflicts with standard venues
    if venue_data.venue_code.upper() in STANDARD_VENUES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This venue code conflicts with a standard venue"
        )
    
    custom_venue = CustomVenue(
        user_id=current_user.id,
        venue_name=venue_data.venue_name,
        venue_code=venue_data.venue_code.upper()
    )
    
    db.add(custom_venue)
    db.commit()
    db.refresh(custom_venue)
    
    logger.info("Custom venue created", user_id=str(current_user.id), venue_code=custom_venue.venue_code)
    
    return custom_venue

@router.put("/venues/{venue_id}", response_model=CustomVenueResponse)
async def update_custom_venue(
    venue_id: str,
    venue_data: CustomVenueUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a custom venue"""
    
    custom_venue = db.query(CustomVenue).filter(
        CustomVenue.id == venue_id,
        CustomVenue.user_id == current_user.id
    ).first()
    
    if not custom_venue:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Custom venue not found"
        )
    
    # Update fields
    if venue_data.venue_name is not None:
        custom_venue.venue_name = venue_data.venue_name
    if venue_data.venue_code is not None:
        # Check for conflicts
        if venue_data.venue_code.upper() in STANDARD_VENUES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This venue code conflicts with a standard venue"
            )
        custom_venue.venue_code = venue_data.venue_code.upper()
    if venue_data.is_active is not None:
        custom_venue.is_active = venue_data.is_active
    
    db.commit()
    db.refresh(custom_venue)
    
    logger.info("Custom venue updated", user_id=str(current_user.id), venue_id=venue_id)
    
    return custom_venue

@router.delete("/venues/{venue_id}")
async def delete_custom_venue(
    venue_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a custom venue (soft delete by setting is_active=False)"""
    
    custom_venue = db.query(CustomVenue).filter(
        CustomVenue.id == venue_id,
        CustomVenue.user_id == current_user.id
    ).first()
    
    if not custom_venue:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Custom venue not found"
        )
    
    custom_venue.is_active = False
    db.commit()
    
    logger.info("Custom venue deleted", user_id=str(current_user.id), venue_id=venue_id)
    
    return {"message": "Custom venue deleted successfully"}
