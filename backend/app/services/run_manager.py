"""
Backtest run manager with job queue and state management
"""

import asyncio
from typing import Dict, List, Optional, Callable
from datetime import datetime
import structlog
from sqlalchemy.orm import Session
from enum import Enum

from app.models.backtest_v2 import BacktestRun, StrategyGraph
from app.schemas.backtest_v2 import RunStatus, BacktestRunCreate, RunConfig
from app.services.backtest_engine_v2 import BacktestEngineV2
from app.services.walk_forward import WalkForwardEngine

logger = structlog.get_logger()


class JobPriority(Enum):
    INTERACTIVE = 1
    BATCH = 2
    LOW = 3


class RunJob:
    """Represents a backtest job"""
    
    def __init__(
        self,
        run_id: str,
        graph_id: str,
        config: RunConfig,
        priority: JobPriority = JobPriority.INTERACTIVE
    ):
        self.run_id = run_id
        self.graph_id = graph_id
        self.config = config
        self.priority = priority
        self.status = RunStatus.QUEUED
        self.progress = 0.0
        self.cancel_requested = False
        self.task: Optional[asyncio.Task] = None


class RunManager:
    """Manages backtest run execution with queuing and concurrency control"""
    
    def __init__(self, max_concurrent_runs: int = 4):
        self.max_concurrent_runs = max_concurrent_runs
        self.jobs: Dict[str, RunJob] = {}
        self.queue: asyncio.PriorityQueue = asyncio.PriorityQueue()
        self.running_jobs: Dict[str, RunJob] = {}
        self.completed_jobs: Dict[str, RunJob] = {}
        
        self.engine = BacktestEngineV2()
        self.wf_engine = WalkForwardEngine()
        
        self._worker_task: Optional[asyncio.Task] = None
        self._running = False
    
    def start(self):
        """Start the worker loop"""
        if not self._running:
            self._running = True
            self._worker_task = asyncio.create_task(self._worker_loop())
            logger.info("RunManager started")
    
    async def stop(self):
        """Stop the worker loop"""
        self._running = False
        if self._worker_task:
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass
        logger.info("RunManager stopped")
    
    async def submit_run(
        self,
        run: BacktestRun,
        graph: StrategyGraph,
        config: RunConfig,
        db: Session
    ) -> str:
        """
        Submit a backtest run to the queue
        
        Returns:
            run_id
        """
        
        # Determine priority
        priority_map = {
            "interactive": JobPriority.INTERACTIVE,
            "batch": JobPriority.BATCH,
            "low": JobPriority.LOW
        }
        priority = priority_map.get(config.priority, JobPriority.BATCH)
        
        # Create job (store IDs only, not ORM objects)
        job = RunJob(
            run_id=run.id,
            graph_id=graph.id,
            config=config,
            priority=priority
        )
        
        self.jobs[run.id] = job
        
        # Update run status
        run.status = RunStatus.QUEUED
        run.progress = 0.0
        db.commit()
        
        # Add to queue (priority, timestamp, job)
        await self.queue.put((priority.value, datetime.utcnow().timestamp(), job))
        
        logger.info(f"Run {run.id} submitted to queue with priority {priority.name}")
        
        return run.id
    
    async def cancel_run(self, run_id: str, db: Session):
        """Cancel a running or queued job"""
        
        if run_id in self.jobs:
            job = self.jobs[run_id]
            job.cancel_requested = True
            
            if job.task:
                job.task.cancel()
            
            job.status = RunStatus.CANCELED
            
            # Update DB
            run = db.query(BacktestRun).filter(BacktestRun.id == run_id).first()
            if run:
                run.status = RunStatus.CANCELED
                run.finished_at = datetime.utcnow()
                db.commit()
            
            logger.info(f"Run {run_id} canceled")
    
    def get_job_status(self, run_id: str) -> Optional[Dict]:
        """Get current job status"""
        
        if run_id in self.jobs:
            job = self.jobs[run_id]
            return {
                "run_id": run_id,
                "status": job.status,
                "progress": job.progress
            }
        return None
    
    async def _worker_loop(self):
        """Main worker loop processing jobs"""
        
        logger.info("Worker loop started")
        
        while self._running:
            try:
                # Check if we can accept more jobs
                if len(self.running_jobs) < self.max_concurrent_runs:
                    try:
                        # Get next job from queue (wait up to 1 second)
                        priority, timestamp, job = await asyncio.wait_for(
                            self.queue.get(),
                            timeout=1.0
                        )
                        
                        # Start job
                        job.task = asyncio.create_task(self._execute_job(job))
                        self.running_jobs[job.run_id] = job
                        
                        logger.info(f"Started run {job.run_id} (priority {priority})")
                        
                    except asyncio.TimeoutError:
                        pass  # No jobs in queue, continue
                else:
                    # Wait a bit before checking again
                    await asyncio.sleep(0.5)
                
                # Clean up completed jobs
                completed = [
                    run_id for run_id, job in self.running_jobs.items()
                    if job.task and job.task.done()
                ]
                for run_id in completed:
                    job = self.running_jobs.pop(run_id)
                    self.completed_jobs[run_id] = job
                    logger.info(f"Run {run_id} completed with status {job.status}")
                
            except Exception as e:
                logger.error(f"Worker loop error: {e}", exc_info=True)
                await asyncio.sleep(1.0)
    
    async def _execute_job(self, job: RunJob):
        """Execute a single backtest job"""
        
        from app.core.database import SessionLocal
        db = SessionLocal()
        
        try:
            # Load the graph in this session (fresh query)
            graph = db.query(StrategyGraph).filter(StrategyGraph.id == job.graph_id).first()
            if not graph:
                raise ValueError(f"Strategy graph {job.graph_id} not found")
            
            # Extract graph data before using it in async context
            graph_nodes = graph.nodes  # This is JSON from DB
            graph_outputs = graph.outputs
            
            # Convert config to RunConfig object if it's a dict
            if isinstance(job.config, dict):
                from app.schemas.backtest_v2 import RunConfig
                config = RunConfig(**job.config)
            else:
                config = job.config
            
            # Update status
            job.status = RunStatus.PREPARING
            job.progress = 5.0
            
            run = db.query(BacktestRun).filter(BacktestRun.id == job.run_id).first()
            if run:
                run.status = RunStatus.PREPARING
                run.started_at = datetime.utcnow()
                db.commit()
            
            # Progress callback
            async def progress_callback(progress: float, message: str):
                if job.cancel_requested:
                    raise asyncio.CancelledError("Run canceled by user")
                
                job.progress = progress
                
                run = db.query(BacktestRun).filter(BacktestRun.id == job.run_id).first()
                if run:
                    run.progress = progress
                    db.commit()
                
                logger.debug(f"Run {job.run_id}: {progress}% - {message}")
            
            await progress_callback(10, "Starting backtest...")
            
            # Check if walk-forward is enabled
            if config.walk_forward and config.walk_forward.enabled:
                logger.info(f"Run {job.run_id}: Running walk-forward validation")
                
                result = await self.wf_engine.run_walk_forward(
                    graph_nodes=graph_nodes,
                    graph_outputs=graph_outputs,
                    config=config,
                    wf_config=config.walk_forward,
                    progress_callback=progress_callback
                )
            else:
                logger.info(f"Run {job.run_id}: Running standard backtest")
                
                result = await self.engine.run_backtest(
                    graph_nodes=graph_nodes,
                    graph_outputs=graph_outputs,
                    config=config,
                    progress_callback=progress_callback
                )
            
            # Update run with results
            if result.get("success"):
                job.status = RunStatus.COMPLETED
                job.progress = 100.0
                
                run = db.query(BacktestRun).filter(BacktestRun.id == job.run_id).first()
                if run:
                    run.status = RunStatus.COMPLETED
                    run.progress = 100.0
                    run.metrics = result.get("metrics").dict() if result.get("metrics") else None
                    run.equity_curve = [ec.dict() for ec in result.get("equity_curve", [])]
                    run.trades = result.get("trades", [])
                    run.folds = [f.dict() for f in result.get("folds", [])] if result.get("folds") else None
                    run.mc_summary = result.get("mc_summary").dict() if result.get("mc_summary") else None
                    run.warnings = [w.dict() for w in result.get("warnings", [])]
                    run.graph_sha = result.get("graph_sha")
                    run.params_sha = result.get("params_sha")
                    run.data_sha = result.get("data_sha")
                    run.repro_id = result.get("repro_id")
                    run.finished_at = datetime.utcnow()
                    run.duration_seconds = (run.finished_at - run.started_at).total_seconds()
                    
                    try:
                        db.commit()
                        logger.info(f"Run {job.run_id} completed successfully - database updated")
                    except Exception as commit_error:
                        logger.error(f"Failed to commit run results: {commit_error}", exc_info=True)
                        db.rollback()
                        # Try saving with reduced data
                        try:
                            run.equity_curve = []  # Clear large data
                            run.trades = []
                            run.diagnostics = {"error": "Results too large to store", "commit_error": str(commit_error)}
                            db.commit()
                            logger.warning(f"Saved run {job.run_id} status without full results data")
                        except:
                            logger.error(f"Failed to save even minimal run data for {job.run_id}")
                
                else:
                    logger.error(f"Run {job.run_id} not found in database after completion")
            else:
                job.status = RunStatus.FAILED
                
                run = db.query(BacktestRun).filter(BacktestRun.id == job.run_id).first()
                if run:
                    run.status = RunStatus.FAILED
                    run.finished_at = datetime.utcnow()
                    # Store error in diagnostics
                    run.diagnostics = {"error": result.get("error")}
                    db.commit()
                
                logger.error(f"Run {job.run_id} failed: {result.get('error')}")
            
        except asyncio.CancelledError:
            job.status = RunStatus.CANCELED
            
            run = db.query(BacktestRun).filter(BacktestRun.id == job.run_id).first()
            if run:
                run.status = RunStatus.CANCELED
                run.finished_at = datetime.utcnow()
                db.commit()
            
            logger.info(f"Run {job.run_id} canceled")
            
        except Exception as e:
            job.status = RunStatus.FAILED
            
            run = db.query(BacktestRun).filter(BacktestRun.id == job.run_id).first()
            if run:
                run.status = RunStatus.FAILED
                run.finished_at = datetime.utcnow()
                run.diagnostics = {"error": str(e)}
                db.commit()
            
            logger.error(f"Run {job.run_id} execution error: {e}", exc_info=True)
            
        finally:
            db.close()


# Global run manager instance
_run_manager: Optional[RunManager] = None


def get_run_manager() -> RunManager:
    """Get or create global run manager"""
    global _run_manager
    if _run_manager is None:
        _run_manager = RunManager(max_concurrent_runs=4)
        _run_manager.start()
    return _run_manager

