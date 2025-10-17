"""
Custom Blocks API - Create, publish, and share custom blocks
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from typing import List, Optional
import structlog
import json
import uuid

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.user import User
from app.models.custom_block import CustomBlock, UserBlockLibrary, BlockRating
from pydantic import BaseModel

logger = structlog.get_logger()
router = APIRouter()


# Schemas
class BlockCreate(BaseModel):
    name: str
    description: Optional[str] = None
    category: str  # data, feature, signal, sizing, risk, exec
    code: str
    input_schema: Optional[str] = None
    output_schema: Optional[str] = None
    parameters: Optional[str] = None
    tags: Optional[List[str]] = None


class BlockUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    code: Optional[str] = None
    input_schema: Optional[str] = None
    output_schema: Optional[str] = None
    parameters: Optional[str] = None
    tags: Optional[List[str]] = None


class BlockResponse(BaseModel):
    id: str
    user_id: str
    name: str
    description: Optional[str]
    category: str
    code: str
    input_schema: Optional[str]
    output_schema: Optional[str]
    parameters: Optional[str]
    is_public: bool
    is_verified: bool
    downloads: int
    rating: float
    rating_count: int
    version: str
    tags: Optional[List[str]]
    created_at: str
    is_in_library: bool = False
    
    class Config:
        from_attributes = True


class RatingCreate(BaseModel):
    rating: int  # 1-5
    comment: Optional[str] = None


# ============================================================================
# CUSTOM BLOCKS CRUD
# ============================================================================

@router.post("/blocks", response_model=BlockResponse)
async def create_custom_block(
    block_data: BlockCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new custom block"""
    
    try:
        # Validate category
        valid_categories = ['data', 'feature', 'signal', 'sizing', 'risk', 'exec', 'other']
        if block_data.category not in valid_categories:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid category. Must be one of: {', '.join(valid_categories)}"
            )
        
        # Create block
        block = CustomBlock(
            id=str(uuid.uuid4()),
            user_id=current_user.id,
            name=block_data.name,
            description=block_data.description,
            category=block_data.category,
            code=block_data.code,
            input_schema=block_data.input_schema,
            output_schema=block_data.output_schema,
            parameters=block_data.parameters,
            tags=json.dumps(block_data.tags) if block_data.tags else None,
            is_public=False  # Private by default
        )
        
        db.add(block)
        
        # Automatically add to user's library
        library_entry = UserBlockLibrary(
            id=str(uuid.uuid4()),
            user_id=current_user.id,
            block_id=block.id
        )
        db.add(library_entry)
        
        db.commit()
        db.refresh(block)
        
        logger.info("Custom block created", user_id=current_user.id, block_id=block.id, name=block.name)
        
        return BlockResponse(
            id=block.id,
            user_id=block.user_id,
            name=block.name,
            description=block.description,
            category=block.category,
            code=block.code,
            input_schema=block.input_schema,
            output_schema=block.output_schema,
            parameters=block.parameters,
            is_public=block.is_public,
            is_verified=block.is_verified,
            downloads=block.downloads,
            rating=block.rating / 100.0 if block.rating else 0.0,
            rating_count=block.rating_count,
            version=block.version,
            tags=json.loads(block.tags) if block.tags else [],
            created_at=block.created_at.isoformat(),
            is_in_library=True
        )
        
    except Exception as e:
        logger.error("Failed to create custom block", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create block: {str(e)}"
        )


@router.get("/blocks/my", response_model=List[BlockResponse])
async def get_my_blocks(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's custom blocks"""
    
    blocks = db.query(CustomBlock).filter(
        CustomBlock.user_id == current_user.id
    ).order_by(CustomBlock.created_at.desc()).all()
    
    return [
        BlockResponse(
            id=block.id,
            user_id=block.user_id,
            name=block.name,
            description=block.description,
            category=block.category,
            code=block.code,
            input_schema=block.input_schema,
            output_schema=block.output_schema,
            parameters=block.parameters,
            is_public=block.is_public,
            is_verified=block.is_verified,
            downloads=block.downloads,
            rating=block.rating / 100.0 if block.rating else 0.0,
            rating_count=block.rating_count,
            version=block.version,
            tags=json.loads(block.tags) if block.tags else [],
            created_at=block.created_at.isoformat(),
            is_in_library=True
        )
        for block in blocks
    ]


@router.get("/blocks/library", response_model=List[BlockResponse])
async def get_my_library(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get blocks in user's library"""
    
    # Get block IDs from library
    library_entries = db.query(UserBlockLibrary).filter(
        UserBlockLibrary.user_id == current_user.id
    ).all()
    
    block_ids = [entry.block_id for entry in library_entries]
    
    if not block_ids:
        return []
    
    blocks = db.query(CustomBlock).filter(
        CustomBlock.id.in_(block_ids)
    ).all()
    
    return [
        BlockResponse(
            id=block.id,
            user_id=block.user_id,
            name=block.name,
            description=block.description,
            category=block.category,
            code=block.code,
            input_schema=block.input_schema,
            output_schema=block.output_schema,
            parameters=block.parameters,
            is_public=block.is_public,
            is_verified=block.is_verified,
            downloads=block.downloads,
            rating=block.rating / 100.0 if block.rating else 0.0,
            rating_count=block.rating_count,
            version=block.version,
            tags=json.loads(block.tags) if block.tags else [],
            created_at=block.created_at.isoformat(),
            is_in_library=True
        )
        for block in blocks
    ]


@router.get("/blocks/public", response_model=List[BlockResponse])
async def get_public_blocks(
    category: Optional[str] = None,
    search: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get public blocks from community"""
    
    query = db.query(CustomBlock).filter(CustomBlock.is_public == True)
    
    if category:
        query = query.filter(CustomBlock.category == category)
    
    if search:
        query = query.filter(
            or_(
                CustomBlock.name.ilike(f"%{search}%"),
                CustomBlock.description.ilike(f"%{search}%")
            )
        )
    
    blocks = query.order_by(CustomBlock.downloads.desc(), CustomBlock.rating.desc()).limit(100).all()
    
    # Check which blocks are in user's library
    library_block_ids = set([
        entry.block_id for entry in 
        db.query(UserBlockLibrary).filter(UserBlockLibrary.user_id == current_user.id).all()
    ])
    
    return [
        BlockResponse(
            id=block.id,
            user_id=block.user_id,
            name=block.name,
            description=block.description,
            category=block.category,
            code=block.code,
            input_schema=block.input_schema,
            output_schema=block.output_schema,
            parameters=block.parameters,
            is_public=block.is_public,
            is_verified=block.is_verified,
            downloads=block.downloads,
            rating=block.rating / 100.0 if block.rating else 0.0,
            rating_count=block.rating_count,
            version=block.version,
            tags=json.loads(block.tags) if block.tags else [],
            created_at=block.created_at.isoformat(),
            is_in_library=block.id in library_block_ids
        )
        for block in blocks
    ]


@router.post("/blocks/{block_id}/publish")
async def publish_block(
    block_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Publish a block to the public library"""
    
    block = db.query(CustomBlock).filter(
        CustomBlock.id == block_id,
        CustomBlock.user_id == current_user.id
    ).first()
    
    if not block:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Block not found"
        )
    
    block.is_public = True
    db.commit()
    
    logger.info("Block published", user_id=current_user.id, block_id=block_id)
    
    return {"message": "Block published successfully"}


@router.post("/blocks/{block_id}/add-to-library")
async def add_to_library(
    block_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Add a public block to user's library"""
    
    # Check if block exists and is public
    block = db.query(CustomBlock).filter(
        CustomBlock.id == block_id,
        CustomBlock.is_public == True
    ).first()
    
    if not block:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Public block not found"
        )
    
    # Check if already in library
    existing = db.query(UserBlockLibrary).filter(
        UserBlockLibrary.user_id == current_user.id,
        UserBlockLibrary.block_id == block_id
    ).first()
    
    if existing:
        return {"message": "Block already in your library"}
    
    # Add to library
    library_entry = UserBlockLibrary(
        id=str(uuid.uuid4()),
        user_id=current_user.id,
        block_id=block_id
    )
    db.add(library_entry)
    
    # Increment download count
    block.downloads += 1
    
    db.commit()
    
    logger.info("Block added to library", user_id=current_user.id, block_id=block_id)
    
    return {"message": "Block added to your library"}


@router.post("/blocks/{block_id}/rate")
async def rate_block(
    block_id: str,
    rating_data: RatingCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Rate a public block"""
    
    if rating_data.rating < 1 or rating_data.rating > 5:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Rating must be between 1 and 5"
        )
    
    # Check if block exists
    block = db.query(CustomBlock).filter(CustomBlock.id == block_id).first()
    if not block:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Block not found"
        )
    
    # Check if user already rated
    existing_rating = db.query(BlockRating).filter(
        BlockRating.user_id == current_user.id,
        BlockRating.block_id == block_id
    ).first()
    
    if existing_rating:
        # Update existing rating
        old_rating = existing_rating.rating
        existing_rating.rating = rating_data.rating
        existing_rating.comment = rating_data.comment
        
        # Recalculate average
        block.rating = int(((block.rating * block.rating_count) - old_rating + rating_data.rating) / block.rating_count * 100)
    else:
        # Create new rating
        new_rating = BlockRating(
            id=str(uuid.uuid4()),
            user_id=current_user.id,
            block_id=block_id,
            rating=rating_data.rating,
            comment=rating_data.comment
        )
        db.add(new_rating)
        
        # Update block rating
        total_rating = (block.rating * block.rating_count) + (rating_data.rating * 100)
        block.rating_count += 1
        block.rating = int(total_rating / block.rating_count)
    
    db.commit()
    
    return {"message": "Rating submitted successfully"}


@router.delete("/blocks/{block_id}")
async def delete_block(
    block_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a custom block"""
    
    block = db.query(CustomBlock).filter(
        CustomBlock.id == block_id,
        CustomBlock.user_id == current_user.id
    ).first()
    
    if not block:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Block not found"
        )
    
    # Remove from all libraries
    db.query(UserBlockLibrary).filter(UserBlockLibrary.block_id == block_id).delete()
    
    # Remove ratings
    db.query(BlockRating).filter(BlockRating.block_id == block_id).delete()
    
    # Delete block
    db.delete(block)
    db.commit()
    
    logger.info("Custom block deleted", user_id=current_user.id, block_id=block_id)
    
    return {"message": "Block deleted successfully"}


@router.get("/blocks/{block_id}", response_model=BlockResponse)
async def get_block(
    block_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific block"""
    
    block = db.query(CustomBlock).filter(CustomBlock.id == block_id).first()
    
    if not block:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Block not found"
        )
    
    # Check if user has access (own block or public)
    if block.user_id != current_user.id and not block.is_public:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # Check if in user's library
    in_library = db.query(UserBlockLibrary).filter(
        UserBlockLibrary.user_id == current_user.id,
        UserBlockLibrary.block_id == block_id
    ).first() is not None
    
    return BlockResponse(
        id=block.id,
        user_id=block.user_id,
        name=block.name,
        description=block.description,
        category=block.category,
        code=block.code,
        input_schema=block.input_schema,
        output_schema=block.output_schema,
        parameters=block.parameters,
        is_public=block.is_public,
        is_verified=block.is_verified,
        downloads=block.downloads,
        rating=block.rating / 100.0 if block.rating else 0.0,
        rating_count=block.rating_count,
        version=block.version,
        tags=json.loads(block.tags) if block.tags else [],
        created_at=block.created_at.isoformat(),
        is_in_library=in_library
    )


@router.get("/categories")
async def get_categories():
    """Get available block categories"""
    return {
        "categories": [
            {"id": "data", "name": "Data Sources", "description": "Load and transform data"},
            {"id": "feature", "name": "Features & Indicators", "description": "Technical indicators and features"},
            {"id": "signal", "name": "Signal Generation", "description": "Entry and exit signals"},
            {"id": "sizing", "name": "Position Sizing", "description": "Determine position sizes"},
            {"id": "risk", "name": "Risk Management", "description": "Stop losses and risk controls"},
            {"id": "exec", "name": "Execution", "description": "Order execution and slippage"},
            {"id": "other", "name": "Other", "description": "Miscellaneous blocks"}
        ]
    }


class TestBlockRequest(BaseModel):
    code: str
    parameters: Optional[str] = None


@router.post("/test")
async def test_block(
    request: TestBlockRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Test a custom block's code"""
    
    code = request.code
    parameters = request.parameters
    
    try:
        from app.services.code_executor import CodeExecutor
        import pandas as pd
        import numpy as np
        
        executor = CodeExecutor()
        
        # Create sample data for testing
        dates = pd.date_range('2024-01-01', periods=100, freq='1h')
        sample_data = pd.DataFrame({
            'open': np.random.randn(100).cumsum() + 100,
            'high': np.random.randn(100).cumsum() + 102,
            'low': np.random.randn(100).cumsum() + 98,
            'close': np.random.randn(100).cumsum() + 100,
            'volume': np.random.randint(1000, 10000, 100)
        }, index=dates)
        
        # Parse parameters
        params = {}
        if parameters:
            try:
                params = json.loads(parameters)
                # Extract default values
                params = {k: v.get('default') for k, v in params.items() if 'default' in v}
            except:
                pass
        
        # Wrap the code in an execute function if not already
        if 'def execute' not in code:
            code = f"""
def execute(inputs, params, data):
{chr(10).join('    ' + line for line in code.split(chr(10)))}
"""
        
        # Test execution
        test_code = f"""
{code}

# Test the function
result = execute([], {params}, data)
"""
        
        result = executor.execute(test_code, {'data': sample_data})
        
        if result.get('success'):
            # Clean the output for JSON serialization
            output = result.get('result')
            if output:
                try:
                    json.dumps(output)
                except (TypeError, ValueError):
                    output = str(output)[:1000]  # Truncate if too long
            
            return {
                "success": True,
                "message": "Block executed successfully",
                "output": output,
                "stdout": result.get('stdout', '')
            }
        else:
            return {
                "success": False,
                "error": result.get('stderr', 'Unknown error')
            }
            
    except Exception as e:
        logger.error(f"Block test failed: {e}")
        return {
            "success": False,
            "error": str(e)
        }


class AIHelpRequest(BaseModel):
    request: str
    current_code: Optional[str] = None


@router.post("/ai-help")
async def ai_help(
    help_request: AIHelpRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get AI help to generate block code with advanced capabilities (with extended timeout)"""
    
    try:
        from app.services.block_ai_helper import BlockAIHelper
        import asyncio
        
        helper = BlockAIHelper(user_id=current_user.id)
        
        # Increase timeout to 120 seconds for AI generation
        result = await asyncio.wait_for(
            helper.generate_block_code(
                request=help_request.request,
                current_code=help_request.current_code,
                context={}
            ),
            timeout=120.0
        )
        
        if result.get("success"):
            return {
                "code": result.get("code"),
                "parameters": result.get("parameters"),
                "message": result.get("message"),
                "execution_log": result.get("execution_log", [])
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.get("message", "AI help failed")
            )
        
    except asyncio.TimeoutError:
        logger.error("AI help timed out after 120 seconds")
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="AI generation is taking too long. Please try a simpler request or try again later."
        )
    except Exception as e:
        logger.error(f"AI help failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI help failed: {str(e)}"
        )

@router.post("/ai-help-stream")
async def ai_help_stream(
    help_request: AIHelpRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get AI help with streaming to avoid timeouts"""
    
    from fastapi.responses import StreamingResponse
    import json
    import asyncio
    
    async def generate():
        try:
            from app.services.block_ai_helper import BlockAIHelper
            
            # Send initial status
            yield f"data: {json.dumps({'type': 'status', 'message': 'Starting AI generation...'})}\n\n"
            await asyncio.sleep(0.1)
            
            helper = BlockAIHelper(user_id=current_user.id)
            
            yield f"data: {json.dumps({'type': 'status', 'message': 'Analyzing request...'})}\n\n"
            await asyncio.sleep(0.1)
            
            # Generate the code
            result = await helper.generate_block_code(
                request=help_request.request,
                current_code=help_request.current_code,
                context={}
            )
            
            if result.get("success"):
                # Send final result
                yield f"data: {json.dumps({'type': 'result', 'data': {'code': result.get('code'), 'parameters': result.get('parameters'), 'message': result.get('message'), 'execution_log': result.get('execution_log', [])}})}\n\n"
            else:
                yield f"data: {json.dumps({'type': 'error', 'message': result.get('message', 'AI help failed')})}\n\n"
            
            yield f"data: {json.dumps({'type': 'done'})}\n\n"
            
        except Exception as e:
            logger.error(f"AI help stream failed: {e}")
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )
