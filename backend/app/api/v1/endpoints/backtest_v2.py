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
    RunConfig, BacktestAnalyzeRequest, BacktestAnalyzeResponse
)
from app.schemas.backtest_copilot import AnalyzeStreamingRequest
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


def sanitize_float(value):
    """Convert NaN/Infinity to None for JSON compliance"""
    if value is None:
        return None
    try:
        import math
        if math.isnan(value) or math.isinf(value):
            return None
        return value
    except (TypeError, ValueError):
        return None

@router.get("/runs", response_model=List[BacktestRunListItem])
async def get_backtest_runs(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = Query(50, ge=1, le=200),
    status: Optional[str] = None,
    strategy_graph_id: Optional[str] = None
):
    """Get user's backtest runs"""
    
    query = db.query(BacktestRun).filter(
        BacktestRun.user_id == current_user.id
    )
    
    if status:
        query = query.filter(BacktestRun.status == status)
    
    if strategy_graph_id:
        query = query.filter(BacktestRun.strategy_graph_id == strategy_graph_id)
    
    runs = query.order_by(BacktestRun.created_at.desc()).limit(limit).all()
    
    # Build list items with strategy names
    items = []
    for run in runs:
        graph = db.query(StrategyGraph).filter(StrategyGraph.id == run.strategy_graph_id).first()
        
        # Sanitize float values to avoid JSON serialization errors
        sharpe = sanitize_float(run.metrics.get("sharpe_ratio")) if run.metrics else None
        cagr = sanitize_float(run.metrics.get("cagr")) if run.metrics else None
        max_dd = sanitize_float(run.metrics.get("max_drawdown")) if run.metrics else None
        total_trades = run.metrics.get("total_trades") if run.metrics else None
        
        item = BacktestRunListItem(
            id=run.id,
            strategy_graph_id=run.strategy_graph_id,
            strategy_name=graph.name if graph else "Unknown",
            status=run.status,
            progress=run.progress,
            sharpe=sharpe,
            cagr=cagr,
            max_dd=max_dd,
            total_trades=total_trades,
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

@router.post("/copilot-stream")
async def copilot_request_stream(
    request: CopilotRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Process AI copilot request with streaming to avoid timeouts"""
    
    from fastapi.responses import StreamingResponse
    import json
    import asyncio
    
    async def generate():
        try:
            # Send initial status
            yield f"data: {json.dumps({'type': 'status', 'message': 'Analyzing your request...'})}\n\n"
            await asyncio.sleep(0.1)
            
            copilot = BacktestCopilot(db, current_user.id)
            
            yield f"data: {json.dumps({'type': 'status', 'message': 'Building strategy with AI...'})}\n\n"
            await asyncio.sleep(0.1)
            
            # Process the request
            response = await copilot.process_request(request)
            
            logger.info(f"Copilot request processed", user_id=current_user.id)
            
            # Send final result
            yield f"data: {json.dumps({'type': 'result', 'data': response.dict()})}\n\n"
            yield f"data: {json.dumps({'type': 'done'})}\n\n"
            
        except Exception as e:
            logger.error(f"Copilot stream failed: {e}", user_id=current_user.id)
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

@router.post("/copilot", response_model=CopilotResponse)
async def copilot_request(
    request: CopilotRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Process AI copilot request (non-streaming, may timeout for complex requests)"""
    
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


@router.get("/conversations/{strategy_id}")
async def get_strategy_conversations(
    strategy_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get conversation history for a specific strategy"""
    from app.models.backtest_conversation import BacktestConversation
    
    try:
        messages = db.query(BacktestConversation).filter(
            BacktestConversation.user_id == current_user.id,
            BacktestConversation.strategy_id == strategy_id
        ).order_by(BacktestConversation.message_index).all()
        
        return {
            "messages": [
                {
                    "id": msg.id,
                    "role": msg.role,
                    "content": msg.content,
                    "metadata": json.loads(msg.message_data) if msg.message_data else None,
                    "created_at": msg.created_at.isoformat()
                }
                for msg in messages
            ]
        }
    except Exception as e:
        logger.error(f"Failed to load conversations: {e}")
        return {"messages": []}


@router.post("/analyze", response_model=BacktestAnalyzeResponse)
async def analyze_backtest_run(
    request: BacktestAnalyzeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    AI-powered backtest analysis endpoint.
    Analyzes a backtest run and answers user questions about the results.
    """
    try:
        logger.info(f"[ANALYZE] Starting analysis request", user_id=current_user.id)
        run_id = request.run_id
        user_question = request.user_question
        backtest_context = request.backtest_context
        chat_history = request.chat_history
        
        logger.info(f"[ANALYZE] Request parsed - run_id: {run_id}, question length: {len(user_question)}", user_id=current_user.id)
        
        if not run_id or not user_question:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing run_id or user_question"
            )
        
        # Verify run belongs to user
        logger.info(f"[ANALYZE] Checking if run exists", user_id=current_user.id, run_id=run_id)
        run = db.query(BacktestRun).filter(
            BacktestRun.id == run_id,
            BacktestRun.user_id == current_user.id
        ).first()
        
        if not run:
            logger.warning(f"[ANALYZE] Run not found", user_id=current_user.id, run_id=run_id)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Backtest run not found"
            )
        
        logger.info(f"[ANALYZE] Run found, initializing OpenAI", user_id=current_user.id)
        
        # Import OpenAI
        from openai import OpenAI
        import os
        
        openai_key = os.getenv("OPENAI_API_KEY")
        logger.info(f"[ANALYZE] OpenAI key present: {bool(openai_key)}", user_id=current_user.id)
        if not openai_key:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="AI service not configured"
            )
        
        client = OpenAI(api_key=openai_key)
        
        # Build analysis prompt
        metrics = backtest_context.get("metrics", {})
        config = backtest_context.get("config", {})
        
        system_prompt = f"""You are an expert quantitative trading analyst specializing in backtest analysis. 

You have access to a backtest run with the following details:

**Strategy Configuration:**
- Symbol: {config.get('symbol', 'N/A')}
- Timeframe: {config.get('timeframe', 'N/A')}
- Initial Capital: ${config.get('initial_capital', 10000):,.2f}
- Start Date: {config.get('start_date', 'N/A')}
- End Date: {config.get('end_date', 'N/A')}

**Performance Metrics:**
- Total Return: {metrics.get('total_return', 0) * 100:.2f}%
- CAGR: {metrics.get('cagr', 0) * 100:.2f}%
- Sharpe Ratio: {metrics.get('sharpe_ratio', 0):.2f}
- Sortino Ratio: {metrics.get('sortino_ratio', 0):.2f}
- Max Drawdown: {metrics.get('max_drawdown', 0) * 100:.2f}%
- Win Rate: {metrics.get('win_rate', 0) * 100:.2f}%
- Profit Factor: {metrics.get('profit_factor', 0):.2f}

**Trade Statistics:**
- Total Trades: {backtest_context.get('total_trades', 0)}
- Winning Trades: {backtest_context.get('winning_trades', 0)}
- Losing Trades: {backtest_context.get('losing_trades', 0)}
- Average Holding Time: {backtest_context.get('avg_holding_time', 0):.2f} hours
- Largest Win: ${backtest_context.get('largest_win', 0):,.2f}
- Largest Loss: ${backtest_context.get('largest_loss', 0):,.2f}
- Average Win: ${metrics.get('avg_win', 0):,.2f}
- Average Loss: ${metrics.get('avg_loss', 0):,.2f}

**Warnings:**
{chr(10).join('- ' + w.get('message', str(w)) for w in backtest_context.get('warnings', []))}

Your task is to provide insightful, actionable analysis based on these metrics. Answer the user's specific questions with:
1. Clear, data-driven insights
2. Specific recommendations for improvement
3. Risk assessment and warnings
4. Comparisons to industry benchmarks where relevant

Be concise but thorough. Use markdown formatting for better readability."""
        
        # Build conversation messages
        messages = [{"role": "system", "content": system_prompt}]
        
        for msg in chat_history[-5:]:  # Last 5 messages for context
            messages.append({
                "role": msg.get("role"),
                "content": msg.get("content")
            })
        
        messages.append({
            "role": "user",
            "content": user_question
        })
        
        # Call OpenAI
        logger.info(f"[ANALYZE] Calling OpenAI API with {len(messages)} messages", user_id=current_user.id)
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            max_tokens=2048,
            temperature=0.7
        )
        
        logger.info(f"[ANALYZE] OpenAI API call successful", user_id=current_user.id)
        ai_response = response.choices[0].message.content
        
        logger.info(f"[ANALYZE] Analysis completed, response length: {len(ai_response)}", user_id=current_user.id, run_id=run_id)
        
        return {
            "response": ai_response,
            "model": "gpt-4o",
            "success": True
        }
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        logger.error(f"Failed to analyze backtest: {e}\n{error_details}", user_id=current_user.id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analysis failed: {str(e)}"
        )


@router.get("/runs/{run_id}/risk-analysis")
async def get_risk_analysis(
    run_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Comprehensive risk analysis for a backtest run
    """
    try:
        # Verify run belongs to user
        run = db.query(BacktestRun).filter(
            BacktestRun.id == run_id,
            BacktestRun.user_id == current_user.id
        ).first()
        
        if not run:
            raise HTTPException(status_code=404, detail="Backtest run not found")
        
        if run.status != 'completed':
            raise HTTPException(status_code=400, detail="Backtest must be completed")
        
        # Import analyzer
        from app.services.quant_analytics import RiskAnalyzer
        
        # Initialize analyzer
        analyzer = RiskAnalyzer(
            trades=run.trades or [],
            equity_curve=run.equity_curve or [],
            config=run.config
        )
        
        # Calculate all risk metrics
        results = analyzer.calculate_all_metrics()
        
        logger.info(f"Risk analysis completed", user_id=current_user.id, run_id=run_id)
        
        return results
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Risk analysis failed: {e}", user_id=current_user.id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Risk analysis failed: {str(e)}"
        )


@router.get("/runs/{run_id}/validate")
async def get_statistical_validation(
    run_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Statistical validation including Monte Carlo, bootstrap, and overfitting detection
    """
    try:
        # Verify run belongs to user
        run = db.query(BacktestRun).filter(
            BacktestRun.id == run_id,
            BacktestRun.user_id == current_user.id
        ).first()
        
        if not run:
            raise HTTPException(status_code=404, detail="Backtest run not found")
        
        if run.status != 'completed':
            raise HTTPException(status_code=400, detail="Backtest must be completed")
        
        # Import validator
        from app.services.quant_analytics import StatisticalValidator
        
        # Initialize validator
        validator = StatisticalValidator(
            trades=run.trades or [],
            equity_curve=run.equity_curve or [],
            config=run.config
        )
        
        # Run all validations
        results = validator.calculate_all_validations()
        
        logger.info(f"Statistical validation completed", user_id=current_user.id, run_id=run_id)
        
        return results
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Statistical validation failed: {e}", user_id=current_user.id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Validation failed: {str(e)}"
        )


@router.post("/runs/{run_id}/optimize")
async def optimize_strategy(
    run_id: str,
    request: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Optimize strategy parameters using parameter sweep
    
    Request body should contain:
    {
        "parameter_ranges": {
            "stop_loss_pct": {"min": 1, "max": 5, "step": 0.5},
            "take_profit_pct": {"min": 2, "max": 10, "step": 1},
            ...
        }
    }
    """
    try:
        # Verify run belongs to user
        run = db.query(BacktestRun).filter(
            BacktestRun.id == run_id,
            BacktestRun.user_id == current_user.id
        ).first()
        
        if not run:
            raise HTTPException(status_code=404, detail="Backtest run not found")
        
        if run.status != 'completed':
            raise HTTPException(status_code=400, detail="Backtest must be completed")
        
        parameter_ranges = request.get('parameter_ranges', {})
        
        if not parameter_ranges:
            raise HTTPException(status_code=400, detail="No parameter ranges provided")
        
        # Import optimizer
        from app.services.quant_analytics import StrategyOptimizer
        
        # Initialize optimizer
        optimizer = StrategyOptimizer(
            trades=run.trades or [],
            config=run.config
        )
        
        # Run optimization
        results = optimizer.optimize_parameters(parameter_ranges)
        
        # Also include position sizing analysis
        kelly = optimizer.calculate_kelly_criterion()
        position_sizing = optimizer.compare_position_sizing_methods()
        
        results['kelly_criterion'] = kelly
        results['position_sizing_comparison'] = position_sizing
        
        logger.info(f"Optimization completed", user_id=current_user.id, run_id=run_id,
                   combinations=results.get('total_combinations_tested', 0))
        
        return results
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Optimization failed: {e}", user_id=current_user.id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Optimization failed: {str(e)}"
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


# ============================================================================
# ADVANCED AI COPILOT (AGENTIC SYSTEM)
# ============================================================================

@router.post("/analyze-streaming")
async def analyze_backtest_streaming(
    request: AnalyzeStreamingRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Advanced agentic AI analysis with streaming responses.
    
    Returns Server-Sent Events (SSE) stream with:
    - tool_call: When AI calls a tool
    - tool_result: Tool execution result
    - thinking: AI reasoning
    - message: AI response text
    - chart: Generated chart
    - parameter_update: Suggested parameter changes
    - backtest_triggered: New backtest run started
    - error: Error occurred
    - done: Stream complete
    """
    from app.services.backtest_copilot_advanced import BacktestCopilotAdvanced
    
    async def event_generator():
        """Generate SSE events"""
        # Create a new DB session that lives for the entire streaming duration
        from app.core.database import SessionLocal
        streaming_db = SessionLocal()
        
        try:
            copilot = BacktestCopilotAdvanced(streaming_db, current_user)
            
            logger.info("[SSE] Starting to iterate over analyze_streaming")
            event_count = 0
            async for event in copilot.analyze_streaming(
                run_id=request.run_id,
                user_question=request.user_question,
                chat_history=request.chat_history,
                context=request.context
            ):
                event_count += 1
                event_type = event.get('type', 'unknown') if isinstance(event, dict) else 'unknown'
                logger.info(f"[SSE] Received event #{event_count}, type: {event_type}")
                
                # Convert datetime to string for JSON serialization
                if isinstance(event, dict) and 'timestamp' in event:
                    from datetime import datetime
                    if isinstance(event['timestamp'], datetime):
                        event['timestamp'] = event['timestamp'].isoformat()
                
                # Use custom encoder to handle numpy types and pandas objects
                import numpy as np
                import pandas as pd
                
                class NumpyEncoder(json.JSONEncoder):
                    def default(self, obj):
                        if isinstance(obj, (np.integer, np.int32, np.int64)):
                            return int(obj)
                        elif isinstance(obj, (np.floating, np.float32, np.float64)):
                            return float(obj)
                        elif isinstance(obj, (np.bool_,)):
                            return bool(obj)
                        elif isinstance(obj, np.ndarray):
                            return obj.tolist()
                        elif isinstance(obj, (pd.DataFrame, pd.Series)):
                            return obj.to_dict()
                        return super().default(obj)
                
                # Format as SSE with explicit byte encoding
                sse_data = "data: {}\n\n".format(json.dumps(event, cls=NumpyEncoder))
                logger.info(f"[SSE] Yielding event #{event_count}, first 100 chars: {repr(sse_data[:100])}")
                # Yield as bytes to preserve newlines
                yield sse_data.encode()
                logger.info(f"[SSE] Successfully yielded event #{event_count}")
            
            logger.info(f"[SSE] Finished iterating, total events: {event_count}")
        
        except Exception as e:
            logger.error(f"Streaming analysis error: {e}", exc_info=True)
            from datetime import datetime
            error_event = {
                "type": "error",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
            yield "data: {}\n\n".format(json.dumps(error_event)).encode()
            
            done_event = {"type": "done", "timestamp": datetime.utcnow().isoformat()}
            yield "data: {}\n\n".format(json.dumps(done_event)).encode()
        
        finally:
            # Close the streaming database session
            streaming_db.close()
            logger.info("[SSE] Streaming database session closed")
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@router.get("/charts/{chart_id}")
async def get_chart(
    chart_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Serve a generated chart by ID.
    
    Charts are generated by the AI copilot visualization tools.
    """
    from pathlib import Path
    
    chart_path = Path("charts") / f"{chart_id}.png"
    
    if not chart_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chart not found"
        )
    
    return FileResponse(
        chart_path,
        media_type="image/png",
        headers={"Cache-Control": "public, max-age=3600"}
    )

