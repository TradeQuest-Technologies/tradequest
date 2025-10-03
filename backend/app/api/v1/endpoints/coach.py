"""
AI Coach endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import List, Optional
import structlog

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.user import User
from app.models.coach_conversation import CoachConversation
from app.services.ai_coach_service import AICoachService
from pydantic import BaseModel

logger = structlog.get_logger()

router = APIRouter()


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    response: str
    suggestions: Optional[List[str]] = None
    insights: Optional[List[dict]] = None
    session_id: str
    thinking: Optional[dict] = None  # Add thinking/operations data


class ConversationSummary(BaseModel):
    session_id: str
    title: str
    last_message: str
    message_count: int
    created_at: str
    updated_at: str


@router.post("/chat/stream")
async def chat_with_coach_stream(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Chat with AI Trading Coach - STREAMING with live operation updates"""
    
    try:
        logger.info(f"[COACH STREAM] Request received - user: {current_user.id}, session: {request.session_id}, message: {request.message[:100]}")
        coach_service = AICoachService(db, current_user.id, session_id=request.session_id)
        logger.info(f"[COACH STREAM] Service initialized - starting stream")
        
        return StreamingResponse(
            coach_service.chat_stream(request.message),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"  # Disable nginx buffering
            }
        )
        
    except Exception as e:
        logger.error("Failed to process coach chat stream", error=str(e), user_id=str(current_user.id))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process your message: {str(e)}"
        )


@router.post("/chat", response_model=ChatResponse)
async def chat_with_coach(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Chat with AI Trading Coach - LEGACY non-streaming endpoint (kept for compatibility)"""
    
    try:
        coach_service = AICoachService(db, current_user.id, session_id=request.session_id)
        response = await coach_service.chat(request.message)
        
        return ChatResponse(
            response=response.get("message", ""),
            suggestions=response.get("suggestions"),
            insights=response.get("insights"),
            session_id=response.get("session_id"),
            thinking=response.get("thinking")
        )
        
    except Exception as e:
        logger.error("Failed to process coach chat", error=str(e), user_id=str(current_user.id))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process your message: {str(e)}"
        )


@router.get("/conversations", response_model=List[ConversationSummary])
async def get_conversations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get list of user's conversation sessions"""
    
    try:
        # Get all sessions with their first and last messages
        user_id_str = str(current_user.id)
        
        # Subquery to get first message of each session (for title)
        first_msg_subq = db.query(
            CoachConversation.session_id,
            func.min(CoachConversation.message_index).label('first_index')
        ).filter(
            CoachConversation.user_id == user_id_str,
            CoachConversation.role == 'user'
        ).group_by(CoachConversation.session_id).subquery()
        
        # Get session summaries
        sessions = db.query(
            CoachConversation.session_id,
            func.min(CoachConversation.created_at).label('created_at'),
            func.max(CoachConversation.created_at).label('updated_at'),
            func.count(CoachConversation.id).label('message_count')
        ).filter(
            CoachConversation.user_id == user_id_str
        ).group_by(
            CoachConversation.session_id
        ).order_by(
            desc('updated_at')
        ).all()
        
        # Get first user message for each session for title
        conversations = []
        for session in sessions:
            first_user_msg = db.query(CoachConversation).filter(
                CoachConversation.user_id == user_id_str,
                CoachConversation.session_id == session.session_id,
                CoachConversation.role == 'user'
            ).order_by(CoachConversation.message_index.asc()).first()
            
            title = first_user_msg.content[:50] + "..." if first_user_msg and len(first_user_msg.content) > 50 else (first_user_msg.content if first_user_msg else "New Conversation")
            
            conversations.append(ConversationSummary(
                session_id=session.session_id,
                title=title,
                last_message=title,  # Could be improved to show last message
                message_count=session.message_count,
                created_at=session.created_at.isoformat(),
                updated_at=session.updated_at.isoformat()
            ))
        
        return conversations
        
    except Exception as e:
        logger.error("Failed to get conversations", error=str(e), user_id=str(current_user.id))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get conversations: {str(e)}"
        )


@router.get("/conversations/{session_id}/messages")
async def get_conversation_messages(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all messages for a specific conversation"""
    
    try:
        user_id_str = str(current_user.id)
        
        messages = db.query(CoachConversation).filter(
            CoachConversation.user_id == user_id_str,
            CoachConversation.session_id == session_id
        ).order_by(CoachConversation.message_index.asc()).all()
        
        return [
            {
                "id": str(msg.id),
                "type": msg.role,
                "content": msg.content,
                "timestamp": msg.created_at.isoformat()
            }
            for msg in messages
        ]
        
    except Exception as e:
        logger.error("Failed to get conversation messages", error=str(e), user_id=str(current_user.id))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get messages: {str(e)}"
        )


@router.get("/context")
async def get_coach_context(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current trading context for the AI coach"""
    
    try:
        coach_service = AICoachService(db, current_user.id)
        context = await coach_service.get_trading_context()
        
        return context
        
    except Exception as e:
        logger.error("Failed to get coach context", error=str(e), user_id=str(current_user.id))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get context: {str(e)}"
        )


@router.delete("/session/{session_id}")
async def clear_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Clear conversation history for a session"""
    
    try:
        coach_service = AICoachService(db, current_user.id, session_id=session_id)
        coach_service.clear_session_history()
        
        return {"message": "Session history cleared", "session_id": session_id}
        
    except Exception as e:
        logger.error("Failed to clear session", error=str(e), user_id=str(current_user.id))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear session: {str(e)}"
        )


@router.get("/image/{user_id}/{session_id}/{filename}")
async def get_coach_image(
    user_id: str,
    session_id: str,
    filename: str
):
    """Serve generated images from AI Coach analysis (public endpoint with path-based security)"""
    from fastapi.responses import RedirectResponse, FileResponse
    from pathlib import Path
    from app.services.storage_service import storage_service
    
    try:
        # Build path to image - user_id is now in the URL for security
        image_path = f"coach_workspaces/{user_id}/{session_id}/{filename}"
        
        # Security: Ensure filename doesn't contain path traversal
        if ".." in filename or "/" in filename or "\\" in filename:
            logger.error(f"Invalid filename: {filename}")
            raise HTTPException(status_code=403, detail="Invalid filename")
        
        logger.info(f"Image request: {image_path}")
        
        if storage_service.use_s3:
            # For S3, redirect to presigned URL
            if storage_service.file_exists(image_path):
                presigned_url = storage_service.get_file_url(image_path, expires_in=3600)
                return RedirectResponse(url=presigned_url, status_code=302)
            else:
                logger.error(f"Image not found in S3: {image_path}")
                raise HTTPException(status_code=404, detail="Image not found")
        else:
            # For local storage, serve file directly
            full_path = Path(storage_service.workspace_dir) / user_id / session_id / filename
            
            # Security: Ensure path is within workspace
            workspace_base = Path(storage_service.workspace_dir) / user_id / session_id
            resolved_path = full_path.resolve()
            workspace_resolved = workspace_base.resolve()
            
            # Check if file is within user's workspace
            if not str(resolved_path).startswith(str(workspace_resolved)):
                logger.error(f"Access denied: {resolved_path} not in {workspace_resolved}")
                raise HTTPException(status_code=403, detail="Access denied - path outside workspace")
            
            if not resolved_path.exists():
                logger.error(f"Image not found: {resolved_path}")
                raise HTTPException(status_code=404, detail="Image not found")
            
            return FileResponse(
                path=str(resolved_path),
                media_type="image/png",
                headers={"Cache-Control": "public, max-age=3600"}
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to serve coach image", error=str(e), session_id=session_id, filename=filename)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to load image: {str(e)}"
        )
