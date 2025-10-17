"""
AI System Statistics and Monitoring
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.user import User
from app.services.ai_router import ai_router
from app.services.ai_cache import ai_cache
from app.services.ai_queue import ai_queue

router = APIRouter()


@router.get("/stats")
async def get_ai_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get AI system statistics"""
    
    return {
        "cache": ai_cache.get_stats(),
        "queue": ai_queue.get_queue_status(),
        "user_queue": ai_queue.get_queue_status(current_user.id)
    }


@router.post("/cache/clear")
async def clear_cache(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Clear AI cache (admin only)"""
    
    # TODO: Add admin check
    ai_cache.clear_all()
    
    return {"message": "Cache cleared successfully"}


@router.get("/queue/status")
async def get_queue_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user's queue status"""
    
    return ai_queue.get_queue_status(current_user.id)
