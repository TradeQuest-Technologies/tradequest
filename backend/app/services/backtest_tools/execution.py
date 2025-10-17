"""
Execution Tools for Backtest Copilot
Tools for triggering new backtest runs and managing strategies.
"""

from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from datetime import datetime
import uuid
import json

from app.models.backtest_v2 import BacktestRun, StrategyGraph
from app.models.user import User
from app.services.run_manager import get_run_manager
import structlog

logger = structlog.get_logger()


class ExecutionTools:
    """Tools for executing backtests and managing strategies"""
    
    def __init__(self, db: Session, user: User):
        self.db = db
        self.user = user
        self.run_limit_per_session = 10
        self.session_run_count = 0
    
    def trigger_backtest_run(
        self,
        strategy_graph_id: str,
        config_overrides: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Start a new backtest with modified parameters.
        
        Args:
        - strategy_graph_id: ID of strategy to run
        - config_overrides: Parameters to override in config
        
        Returns:
        - run_id: ID of new backtest run
        - status: 'queued'
        - config: Full config for the run
        """
        # Check rate limit
        if self.session_run_count >= self.run_limit_per_session:
            raise ValueError(f"Rate limit exceeded: max {self.run_limit_per_session} runs per session")
        
        # Get strategy graph
        strategy = self.db.query(StrategyGraph).filter(
            StrategyGraph.id == strategy_graph_id,
            StrategyGraph.user_id == self.user.id
        ).first()
        
        if not strategy:
            raise ValueError(f"Strategy {strategy_graph_id} not found")
        
        # Get base config from strategy or use defaults
        base_config = (strategy.config or {}).get('backtest_config', {})
        
        # Apply overrides
        config = {**base_config, **(config_overrides or {})}
        
        # Validate required fields
        required_fields = ['symbol', 'timeframe', 'start_date', 'end_date']
        missing = [f for f in required_fields if f not in config]
        if missing:
            raise ValueError(f"Missing required config fields: {', '.join(missing)}")
        
        # Create new backtest run
        run_id = str(uuid.uuid4())
        new_run = BacktestRun(
            id=run_id,
            user_id=self.user.id,
            strategy_graph_id=strategy_graph_id,
            repro_id=strategy.repro_id,
            config=config,
            status='queued',
            progress=0,
            created_at=datetime.utcnow()
        )
        
        self.db.add(new_run)
        self.db.commit()
        
        # Queue the run
        try:
            run_manager = get_run_manager()
            run_manager.queue_run(run_id, self.user.id, strategy_graph_id, config)
            logger.info(f"Backtest run queued", run_id=run_id, user_id=self.user.id)
        except Exception as e:
            logger.error(f"Failed to queue backtest: {e}")
            new_run.status = 'failed'
            self.db.commit()
            raise
        
        self.session_run_count += 1
        
        return {
            "run_id": run_id,
            "status": "queued",
            "config": config,
            "message": f"Backtest queued successfully (run {self.session_run_count}/{self.run_limit_per_session})"
        }
    
    def clone_and_modify_strategy(
        self,
        source_strategy_id: str,
        modifications: Dict[str, Any],
        new_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Clone a strategy graph and modify its parameters.
        
        Args:
        - source_strategy_id: ID of strategy to clone
        - modifications: Changes to apply to the graph
        - new_name: Name for cloned strategy
        
        Returns:
        - strategy_id: ID of cloned strategy
        - name: Name of cloned strategy
        - modifications_applied: List of changes
        """
        # Get source strategy
        source_strategy = self.db.query(StrategyGraph).filter(
            StrategyGraph.id == source_strategy_id,
            StrategyGraph.user_id == self.user.id
        ).first()
        
        if not source_strategy:
            raise ValueError(f"Strategy {source_strategy_id} not found")
        
        # Clone strategy
        new_strategy_id = str(uuid.uuid4())
        cloned_name = new_name or f"{source_strategy.name} (Clone)"
        
        cloned_graph = StrategyGraph(
            id=new_strategy_id,
            user_id=self.user.id,
            name=cloned_name,
            repro_id=source_strategy.repro_id,
            nodes=source_strategy.nodes.copy() if source_strategy.nodes else [],
            edges=source_strategy.edges.copy() if source_strategy.edges else [],
            config=source_strategy.config.copy() if source_strategy.config else {},
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        # Apply modifications
        modifications_applied = []
        
        if 'config' in modifications:
            for key, value in modifications['config'].items():
                if 'backtest_config' not in cloned_graph.config:
                    cloned_graph.config['backtest_config'] = {}
                cloned_graph.config['backtest_config'][key] = value
                modifications_applied.append(f"Set {key} = {value}")
        
        if 'nodes' in modifications:
            # Modify specific nodes
            for node_id, node_changes in modifications['nodes'].items():
                for node in cloned_graph.nodes:
                    if node.get('id') == node_id:
                        node.update(node_changes)
                        modifications_applied.append(f"Modified node {node_id}")
                        break
        
        self.db.add(cloned_graph)
        self.db.commit()
        
        logger.info(f"Strategy cloned and modified", 
                   source_id=source_strategy_id, 
                   new_id=new_strategy_id)
        
        return {
            "strategy_id": new_strategy_id,
            "name": cloned_name,
            "modifications_applied": modifications_applied,
            "message": f"Strategy cloned successfully with {len(modifications_applied)} modifications"
        }
    
    def save_optimization_result(
        self,
        run_id: str,
        parameters: Dict[str, Any],
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Save an optimized parameter set with notes.
        
        This creates a new strategy variant with the optimized parameters.
        
        Args:
        - run_id: ID of the optimized run
        - parameters: Optimized parameter set
        - notes: Optional notes about the optimization
        
        Returns:
        - strategy_id: ID of new strategy with optimized params
        - saved: True if successful
        """
        # Get the run
        run = self.db.query(BacktestRun).filter(
            BacktestRun.id == run_id,
            BacktestRun.user_id == self.user.id
        ).first()
        
        if not run:
            raise ValueError(f"Run {run_id} not found")
        
        # Get source strategy
        source_strategy = self.db.query(StrategyGraph).filter(
            StrategyGraph.id == run.strategy_graph_id,
            StrategyGraph.user_id == self.user.id
        ).first()
        
        if not source_strategy:
            raise ValueError(f"Source strategy not found")
        
        # Create optimized variant
        optimized_id = str(uuid.uuid4())
        optimized_name = f"{source_strategy.name} (Optimized)"
        
        # Build optimized config
        base_config = source_strategy.config.copy() if source_strategy.config else {}
        backtest_config = base_config.get('backtest_config', {})
        
        optimized_config = {
            **base_config,
            'backtest_config': {
                **backtest_config,
                **parameters
            },
            'optimization_notes': notes,
            'optimized_from_run': run_id,
            'optimized_at': datetime.utcnow().isoformat()
        }
        
        optimized_strategy = StrategyGraph(
            id=optimized_id,
            user_id=self.user.id,
            name=optimized_name,
            repro_id=source_strategy.repro_id,
            nodes=source_strategy.nodes.copy() if source_strategy.nodes else [],
            edges=source_strategy.edges.copy() if source_strategy.edges else [],
            config=optimized_config,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        self.db.add(optimized_strategy)
        self.db.commit()
        
        logger.info(f"Optimization saved", run_id=run_id, strategy_id=optimized_id)
        
        return {
            "strategy_id": optimized_id,
            "name": optimized_name,
            "saved": True,
            "parameters": parameters,
            "notes": notes,
            "message": "Optimized parameters saved as new strategy variant"
        }
    
    def get_run_status(self, run_id: str) -> Dict[str, Any]:
        """
        Get status of a running or completed backtest.
        
        Returns:
        - status: 'queued', 'running', 'completed', 'failed'
        - progress: 0-100
        - metrics: Performance metrics (if completed)
        """
        run = self.db.query(BacktestRun).filter(
            BacktestRun.id == run_id,
            BacktestRun.user_id == self.user.id
        ).first()
        
        if not run:
            raise ValueError(f"Run {run_id} not found")
        
        return {
            "run_id": run_id,
            "status": run.status,
            "progress": run.progress,
            "metrics": run.metrics if run.status == 'completed' else None,
            "error": run.error if run.status == 'failed' else None
        }
    
    def reset_session_limit(self):
        """Reset the session run counter"""
        self.session_run_count = 0

