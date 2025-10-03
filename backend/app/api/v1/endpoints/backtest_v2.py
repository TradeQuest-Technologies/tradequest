"""
Enhanced Backtesting v2 API endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import StreamingResponse, FileResponse
from sqlalchemy.orm import Session
from typing import List, Optional
import structlog
import uuid
import json
import asyncio

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.user import User
from app.models.backtest_v2 import StrategyGraph, BacktestRun, BacktestTemplate, BacktestArtifact
from app.schemas.backtest_v2 import (
    StrategyGraphCreate, StrategyGraphUpdate, StrategyGraphResponse,
    BacktestRunCreate, BacktestRunResponse, BacktestRunListItem,
    CopilotRequest, CopilotResponse, TemplateResponse,
    RunConfig
)
from app.services.run_manager import get_run_manager
from app.services.backtest_copilot import BacktestCopilot

logger = structlog.get_logger()
router = APIRouter()


# ============================================================================
# STRATEGY GRAPHS
# ============================================================================

@router.post("/graphs", response_model=StrategyGraphResponse)
async def create_strategy_graph(
    data: StrategyGraphCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create new strategy graph"""
    
    try:
        # Calculate graph hash
        import hashlib
        graph_json = json.dumps({
            "nodes": [n.dict() for n in data.nodes],
            "edges": [e.dict() for e in data.edges],
            "outputs": data.outputs
        }, sort_keys=True)
        graph_sha = hashlib.sha256(graph_json.encode()).hexdigest()
        
        # Create graph
        graph = StrategyGraph(
            user_id=current_user.id,
            name=data.name,
            description=data.description,
            nodes=[n.dict() for n in data.nodes],
            edges=[e.dict() for e in data.edges] if data.edges else [],
            outputs=data.outputs,
            graph_sha=graph_sha,
            version=1,
            tags=data.tags if data.tags else [],
            is_public=data.is_public
        )
        
        db.add(graph)
        db.commit()
        db.refresh(graph)
        
        logger.info(f"Created strategy graph {graph.id}", user_id=current_user.id)
        
        return StrategyGraphResponse.from_orm(graph)
        
    except Exception as e:
        logger.error(f"Failed to create strategy graph: {e}", user_id=current_user.id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create strategy graph: {str(e)}"
        )


@router.get("/graphs", response_model=List[StrategyGraphResponse])
async def get_strategy_graphs(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = Query(50, ge=1, le=200)
):
    """Get user's strategy graphs"""
    
    graphs = db.query(StrategyGraph).filter(
        StrategyGraph.user_id == current_user.id
    ).order_by(StrategyGraph.created_at.desc()).limit(limit).all()
    
    return [StrategyGraphResponse.from_orm(g) for g in graphs]


@router.get("/graphs/{graph_id}", response_model=StrategyGraphResponse)
async def get_strategy_graph(
    graph_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get specific strategy graph"""
    
    graph = db.query(StrategyGraph).filter(
        StrategyGraph.id == graph_id,
        StrategyGraph.user_id == current_user.id
    ).first()
    
    if not graph:
        raise HTTPException(status_code=404, detail="Strategy graph not found")
    
    return StrategyGraphResponse.from_orm(graph)


@router.patch("/graphs/{graph_id}", response_model=StrategyGraphResponse)
async def update_strategy_graph(
    graph_id: str,
    data: StrategyGraphUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update strategy graph"""
    
    graph = db.query(StrategyGraph).filter(
        StrategyGraph.id == graph_id,
        StrategyGraph.user_id == current_user.id
    ).first()
    
    if not graph:
        raise HTTPException(status_code=404, detail="Strategy graph not found")
    
    # Update fields
    if data.name is not None:
        graph.name = data.name
    if data.description is not None:
        graph.description = data.description
    if data.nodes is not None:
        graph.nodes = [n.dict() for n in data.nodes]
    if data.edges is not None:
        graph.edges = [e.dict() for e in data.edges]
    if data.outputs is not None:
        graph.outputs = data.outputs
    if data.tags is not None:
        graph.tags = data.tags
    if data.is_public is not None:
        graph.is_public = data.is_public
    
    # Recalculate hash if structure changed
    if data.nodes or data.edges or data.outputs:
        import hashlib
        graph_json = json.dumps({
            "nodes": graph.nodes,
            "edges": graph.edges,
            "outputs": graph.outputs
        }, sort_keys=True)
        graph.graph_sha = hashlib.sha256(graph_json.encode()).hexdigest()
        graph.version += 1
    
    db.commit()
    db.refresh(graph)
    
    logger.info(f"Updated strategy graph {graph_id}", user_id=current_user.id)
    
    return StrategyGraphResponse.from_orm(graph)


@router.delete("/graphs/{graph_id}")
async def delete_strategy_graph(
    graph_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete strategy graph"""
    
    graph = db.query(StrategyGraph).filter(
        StrategyGraph.id == graph_id,
        StrategyGraph.user_id == current_user.id
    ).first()
    
    if not graph:
        raise HTTPException(status_code=404, detail="Strategy graph not found")
    
    db.delete(graph)
    db.commit()
    
    logger.info(f"Deleted strategy graph {graph_id}", user_id=current_user.id)
    
    return {"success": True}


# ============================================================================
# BACKTEST RUNS
# ============================================================================

@router.post("/runs", response_model=BacktestRunResponse)
async def create_backtest_run(
    data: BacktestRunCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create and queue new backtest run"""
    
    try:
        # Get strategy graph
        graph = db.query(StrategyGraph).filter(
            StrategyGraph.id == data.strategy_graph_id,
            StrategyGraph.user_id == current_user.id
        ).first()
        
        if not graph:
            raise HTTPException(status_code=404, detail="Strategy graph not found")
        
        # Create run record
        run = BacktestRun(
            user_id=current_user.id,
            strategy_graph_id=graph.id,
            config=data.config.dict(),
            graph_sha=graph.graph_sha,
            status="queued",
            progress=0.0,
            priority=data.config.priority,
            max_workers=data.config.max_workers
        )
        
        db.add(run)
        db.commit()
        db.refresh(run)
        
        # Submit to run manager
        run_manager = get_run_manager()
        await run_manager.submit_run(run, graph, data.config, db)
        
        logger.info(f"Created backtest run {run.id}", user_id=current_user.id)
        
        return BacktestRunResponse.from_orm(run)
        
    except Exception as e:
        logger.error(f"Failed to create backtest run: {e}", user_id=current_user.id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create backtest run: {str(e)}"
        )


@router.get("/runs", response_model=List[BacktestRunListItem])
async def get_backtest_runs(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = Query(50, ge=1, le=200),
    status: Optional[str] = None
):
    """Get user's backtest runs"""
    
    query = db.query(BacktestRun).filter(
        BacktestRun.user_id == current_user.id
    )
    
    if status:
        query = query.filter(BacktestRun.status == status)
    
    runs = query.order_by(BacktestRun.created_at.desc()).limit(limit).all()
    
    # Build list items with strategy names
    items = []
    for run in runs:
        graph = db.query(StrategyGraph).filter(StrategyGraph.id == run.strategy_graph_id).first()
        
        item = BacktestRunListItem(
            id=run.id,
            strategy_graph_id=run.strategy_graph_id,
            strategy_name=graph.name if graph else "Unknown",
            status=run.status,
            progress=run.progress,
            sharpe=run.metrics.get("sharpe_ratio") if run.metrics else None,
            cagr=run.metrics.get("cagr") if run.metrics else None,
            max_dd=run.metrics.get("max_drawdown") if run.metrics else None,
            total_trades=run.metrics.get("total_trades") if run.metrics else None,
            created_at=run.created_at,
            duration_seconds=run.duration_seconds
        )
        items.append(item)
    
    return items


@router.get("/runs/{run_id}", response_model=BacktestRunResponse)
async def get_backtest_run(
    run_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get specific backtest run"""
    
    run = db.query(BacktestRun).filter(
        BacktestRun.id == run_id,
        BacktestRun.user_id == current_user.id
    ).first()
    
    if not run:
        raise HTTPException(status_code=404, detail="Backtest run not found")
    
    return BacktestRunResponse.from_orm(run)


@router.patch("/runs/{run_id}/notes")
async def update_run_notes(
    run_id: str,
    notes_data: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update notes for a backtest run"""
    
    run = db.query(BacktestRun).filter(
        BacktestRun.id == run_id,
        BacktestRun.user_id == current_user.id
    ).first()
    
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    
    # Update or add notes field in diagnostics
    if run.diagnostics is None:
        run.diagnostics = {}
    
    run.diagnostics['notes'] = notes_data.get('notes', '')
    
    # Mark the field as modified for SQLAlchemy to detect change
    from sqlalchemy.orm.attributes import flag_modified
    flag_modified(run, 'diagnostics')
    
    db.commit()
    db.refresh(run)
    
    logger.info(f"Updated notes for run {run_id}", user_id=current_user.id)
    
    return {"message": "Notes updated"}


@router.get("/runs/{run_id}/stream")
async def stream_run_progress(
    run_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Stream run progress updates (SSE)"""
    
    # Verify run exists and belongs to user
    run = db.query(BacktestRun).filter(
        BacktestRun.id == run_id,
        BacktestRun.user_id == current_user.id
    ).first()
    
    if not run:
        raise HTTPException(status_code=404, detail="Backtest run not found")
    
    async def event_generator():
        """Generate SSE events with progress updates"""
        run_manager = get_run_manager()
        
        while True:
            # Get current status
            status = run_manager.get_job_status(run_id)
            
            if status:
                data = json.dumps(status)
                yield f"data: {data}\n\n"
                
                # Stop streaming if completed, failed, or canceled
                if status["status"] in ["completed", "failed", "canceled"]:
                    break
            
            await asyncio.sleep(0.5)
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@router.post("/runs/{run_id}/cancel")
async def cancel_backtest_run(
    run_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Cancel a running backtest"""
    
    run = db.query(BacktestRun).filter(
        BacktestRun.id == run_id,
        BacktestRun.user_id == current_user.id
    ).first()
    
    if not run:
        raise HTTPException(status_code=404, detail="Backtest run not found")
    
    if run.status in ["completed", "failed", "canceled"]:
        raise HTTPException(status_code=400, detail="Run already finished")
    
    run_manager = get_run_manager()
    await run_manager.cancel_run(run_id, db)
    
    logger.info(f"Canceled backtest run {run_id}", user_id=current_user.id)
    
    return {"success": True}


# ============================================================================
# AI COPILOT
# ============================================================================

@router.post("/copilot", response_model=CopilotResponse)
async def copilot_request(
    request: CopilotRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Process AI copilot request"""
    
    try:
        copilot = BacktestCopilot(db, current_user.id)
        response = await copilot.process_request(request)
        
        logger.info(f"Copilot request processed", user_id=current_user.id)
        
        return response
        
    except Exception as e:
        logger.error(f"Copilot request failed: {e}", user_id=current_user.id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Copilot request failed: {str(e)}"
        )


# ============================================================================
# TEMPLATES
# ============================================================================

@router.get("/templates", response_model=List[TemplateResponse])
async def get_templates(
    db: Session = Depends(get_db),
    category: Optional[str] = None,
    featured_only: bool = False
):
    """Get strategy templates"""
    
    query = db.query(BacktestTemplate)
    
    if category:
        query = query.filter(BacktestTemplate.category == category)
    
    if featured_only:
        query = query.filter(BacktestTemplate.is_featured == True)
    
    templates = query.order_by(BacktestTemplate.usage_count.desc()).all()
    
    return [TemplateResponse.from_orm(t) for t in templates]


@router.get("/templates/{template_id}", response_model=TemplateResponse)
async def get_template(
    template_id: str,
    db: Session = Depends(get_db)
):
    """Get specific template"""
    
    template = db.query(BacktestTemplate).filter(
        BacktestTemplate.id == template_id
    ).first()
    
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    # Increment usage count
    template.usage_count += 1
    db.commit()
    
    return TemplateResponse.from_orm(template)

