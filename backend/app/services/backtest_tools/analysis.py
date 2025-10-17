"""
Analysis Tools for Backtest Copilot
Read-only tools for analyzing backtest runs, trades, and metrics.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.models.backtest_v2 import BacktestRun
from app.models.user import User
import structlog

logger = structlog.get_logger()


class AnalysisTools:
    """Tools for analyzing backtest runs and trades"""
    
    def __init__(self, db: Session, user: User):
        self.db = db
        self.user = user
    
    def get_run_summary(self, run_id: str) -> Dict[str, Any]:
        """
        Fetch complete summary of a backtest run.
        
        Returns:
        - id, strategy_graph_id, status
        - config (symbol, timeframe, dates, capital)
        - metrics (all performance metrics)
        - warnings
        """
        run = self.db.query(BacktestRun).filter(
            BacktestRun.id == run_id,
            BacktestRun.user_id == self.user.id
        ).first()
        
        if not run:
            raise ValueError(f"Run {run_id} not found")
        
        return {
            "id": run.id,
            "strategy_graph_id": run.strategy_graph_id,
            "status": run.status,
            "created_at": run.created_at.isoformat() if run.created_at else None,
            "config": run.config or {},
            "metrics": run.metrics or {},
            "warnings": run.warnings or [],
            "progress": run.progress
        }
    
    def get_trades_detailed(
        self,
        run_id: str,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Query specific trades with filters.
        
        Filters:
        - symbol: str
        - side: 'long' or 'short'
        - min_pnl: float
        - max_pnl: float
        - start_date: ISO string
        - end_date: ISO string
        - winners_only: bool
        - losers_only: bool
        - limit: int (default 100)
        """
        run = self.db.query(BacktestRun).filter(
            BacktestRun.id == run_id,
            BacktestRun.user_id == self.user.id
        ).first()
        
        if not run or not run.trades:
            return []
        
        trades = run.trades
        filters = filters or {}
        
        # Apply filters
        if filters.get('symbol'):
            trades = [t for t in trades if t.get('symbol') == filters['symbol']]
        
        if filters.get('side'):
            trades = [t for t in trades if t.get('side') == filters['side']]
        
        if filters.get('min_pnl') is not None:
            trades = [t for t in trades if t.get('pnl', 0) >= filters['min_pnl']]
        
        if filters.get('max_pnl') is not None:
            trades = [t for t in trades if t.get('pnl', 0) <= filters['max_pnl']]
        
        if filters.get('winners_only'):
            trades = [t for t in trades if t.get('pnl', 0) > 0]
        
        if filters.get('losers_only'):
            trades = [t for t in trades if t.get('pnl', 0) < 0]
        
        if filters.get('start_date'):
            start_dt = datetime.fromisoformat(filters['start_date'].replace('Z', '+00:00'))
            trades = [t for t in trades if datetime.fromisoformat(t['entry_time'].replace('Z', '+00:00')) >= start_dt]
        
        if filters.get('end_date'):
            end_dt = datetime.fromisoformat(filters['end_date'].replace('Z', '+00:00'))
            trades = [t for t in trades if datetime.fromisoformat(t['entry_time'].replace('Z', '+00:00')) <= end_dt]
        
        # Limit results
        limit = filters.get('limit', 100)
        return trades[:limit]
    
    def get_equity_curve(self, run_id: str) -> List[Dict[str, Any]]:
        """
        Fetch equity curve data for visualization.
        
        Returns list of:
        - timestamp
        - equity
        - drawdown_pct
        - trade_count
        """
        run = self.db.query(BacktestRun).filter(
            BacktestRun.id == run_id,
            BacktestRun.user_id == self.user.id
        ).first()
        
        if not run or not run.equity_curve:
            return []
        
        return run.equity_curve
    
    def compare_runs(self, run_ids: List[str]) -> Dict[str, Any]:
        """
        Compare multiple backtest runs side-by-side.
        
        Returns:
        - runs: List of run summaries
        - metrics_comparison: Dict mapping metric name to list of values
        - best_run_id: ID of best performing run (by Sharpe)
        - improvement_pct: Percentage improvement from worst to best
        """
        runs = self.db.query(BacktestRun).filter(
            BacktestRun.id.in_(run_ids),
            BacktestRun.user_id == self.user.id
        ).all()
        
        if not runs:
            return {"runs": [], "metrics_comparison": {}, "best_run_id": None, "improvement_pct": {}}
        
        # Build comparison
        run_summaries = []
        metrics_comparison = {}
        
        for run in runs:
            summary = {
                "id": run.id,
                "created_at": run.created_at.isoformat() if run.created_at else None,
                "config": run.config or {},
                "metrics": run.metrics or {}
            }
            run_summaries.append(summary)
            
            # Collect metrics
            for metric_name, metric_value in (run.metrics or {}).items():
                if metric_name not in metrics_comparison:
                    metrics_comparison[metric_name] = []
                metrics_comparison[metric_name].append(metric_value)
        
        # Find best run by Sharpe ratio
        best_run_id = None
        best_sharpe = float('-inf')
        
        for run in runs:
            sharpe = (run.metrics or {}).get('sharpe_ratio', 0)
            if sharpe > best_sharpe:
                best_sharpe = sharpe
                best_run_id = run.id
        
        # Calculate improvement
        improvement_pct = {}
        for metric_name, values in metrics_comparison.items():
            if len(values) >= 2 and all(isinstance(v, (int, float)) for v in values):
                min_val = min(values)
                max_val = max(values)
                if min_val != 0:
                    improvement_pct[metric_name] = ((max_val - min_val) / abs(min_val)) * 100
        
        return {
            "runs": run_summaries,
            "metrics_comparison": metrics_comparison,
            "best_run_id": best_run_id,
            "improvement_pct": improvement_pct
        }
    
    def execute_python(self, run_id: str, code: str) -> Any:
        """
        Execute Python code with efficient file-based data access.
        
        Pre-loaded globals:
        - run_data: dict with run info
        - trades_file: str path to CSV file with all trades
        - equity_curve_file: str path to pickle file with equity curve
        - pd, np, scipy, statsmodels: pre-imported
        - get_trades_filtered: function to filter trades
        - fetch_ohlcv: function to get market data
        
        Must set 'result' variable for output.
        """
        import pandas as pd
        import numpy as np
        import scipy
        import scipy.stats
        from scipy import stats
        import statsmodels
        import statsmodels.api as sm
        from datetime import datetime, timedelta
        import math
        import statistics
        from collections import defaultdict
        import tempfile
        import pickle
        
        # Fetch run data
        run = self.db.query(BacktestRun).filter(
            BacktestRun.id == run_id,
            BacktestRun.user_id == self.user.id
        ).first()
        
        if not run:
            raise ValueError(f"Run {run_id} not found")
        
        run_data = {
            "id": run.id,
            "config": run.config or {},
            "metrics": run.metrics or {},
            "warnings": run.warnings or [],
            "num_trades": len(run.trades or [])
        }
        
        # Save trades to temp CSV file (efficient for large datasets)
        trades_fd, trades_file_path = tempfile.mkstemp(suffix='.csv', prefix=f'trades_{run_id}_')
        if run.trades:
            trades_df = pd.DataFrame(run.trades)
            trades_df.to_csv(trades_file_path, index=False)
        
        # Save equity curve to temp pickle file
        equity_fd, equity_file_path = tempfile.mkstemp(suffix='.pkl', prefix=f'equity_{run_id}_')
        with open(equity_file_path, 'wb') as f:
            pickle.dump(run.equity_curve or [], f)
        
        # Helper functions
        def get_trades_filtered(filters: Dict[str, Any]) -> List[Dict[str, Any]]:
            return self.get_trades_detailed(run_id, filters)
        
        def fetch_ohlcv(symbol: str, start: str, end: str, timeframe: str = '1m') -> List[Dict[str, Any]]:
            """Fetch OHLCV data - currently returns empty list (market data integration in progress)"""
            logger.warning("Market data fetching not available in execute_python context")
            return []
        
        # Build globals with FILE PATHS instead of raw data
        exec_globals = {
            "run_data": run_data,
            "trades_file": trades_file_path,  # Path to CSV file
            "equity_curve_file": equity_file_path,  # Path to pickle file
            "get_trades_filtered": get_trades_filtered,
            "fetch_ohlcv": fetch_ohlcv,
            "pd": pd,
            "np": np,
            "scipy": scipy,
            "stats": stats,
            "sm": sm,
            "statsmodels": statsmodels,
            "datetime": datetime,
            "timedelta": timedelta,
            "math": math,
            "statistics": statistics,
            "defaultdict": defaultdict,
            "pickle": pickle,
            "result": None
        }
        
        # Execute code with timeout
        try:
            exec(code, exec_globals)
            result = exec_globals.get("result", "Code executed but no result set")
            
            # Recursively convert pandas/numpy objects to JSON-friendly format
            def convert_to_json_safe(obj):
                """Recursively convert pandas/numpy objects to JSON-safe types"""
                if isinstance(obj, dict):
                    return {str(k): convert_to_json_safe(v) for k, v in obj.items()}
                elif isinstance(obj, (list, tuple)):
                    return [convert_to_json_safe(item) for item in obj]
                elif hasattr(obj, 'to_json'):  # DataFrame or Series
                    import json
                    return json.loads(obj.to_json(orient='split', date_format='iso'))
                elif hasattr(obj, 'tolist'):  # numpy array
                    return obj.tolist()
                elif hasattr(obj, 'item'):  # numpy scalar
                    return obj.item()
                else:
                    return obj
            
            result = convert_to_json_safe(result)
            return result
        except Exception as e:
            return f"Error executing code: {str(e)}"
        finally:
            # Clean up temp files
            try:
                import os
                os.close(trades_fd)
                os.close(equity_fd)
                os.unlink(trades_file_path)
                os.unlink(equity_file_path)
            except:
                pass  # Ignore cleanup errors
    
    def calculate_custom_metric(
        self,
        run_id: str,
        metric_name: str,
        calculation_code: str
    ) -> float:
        """
        Calculate a custom metric using Python code.
        
        The code should set 'result' to a numeric value.
        """
        result = self.execute_python(run_id, calculation_code)
        
        if isinstance(result, (int, float)):
            return result
        else:
            raise ValueError(f"Metric calculation did not return a number: {result}")
    
    def fetch_market_data(
        self,
        symbol: str,
        start_time: str,
        end_time: str,
        timeframe: str = '1m'
    ) -> List[Dict[str, Any]]:
        """
        Get OHLCV data for market context analysis.
        
        Returns list of candles with:
        - timestamp, open, high, low, close, volume
        
        Note: Market data fetching integration in progress.
        """
        logger.warning(f"Market data fetching not yet available for {symbol}")
        return []
    
    def find_best_runs(
        self,
        strategy_graph_id: Optional[str] = None,
        metric: str = 'sharpe_ratio',
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Query top N backtest runs by any metric.
        
        Args:
        - strategy_graph_id: Filter by strategy (optional)
        - metric: Metric to sort by (default: sharpe_ratio)
        - limit: Number of runs to return
        """
        query = self.db.query(BacktestRun).filter(
            BacktestRun.user_id == self.user.id,
            BacktestRun.status == 'completed'
        )
        
        if strategy_graph_id:
            query = query.filter(BacktestRun.strategy_graph_id == strategy_graph_id)
        
        runs = query.order_by(desc(BacktestRun.created_at)).limit(100).all()
        
        # Sort by metric
        runs_with_metric = []
        for run in runs:
            metric_value = (run.metrics or {}).get(metric)
            if metric_value is not None:
                runs_with_metric.append({
                    "id": run.id,
                    "strategy_graph_id": run.strategy_graph_id,
                    "created_at": run.created_at.isoformat() if run.created_at else None,
                    "metrics": run.metrics or {},
                    "config": run.config or {},
                    metric: metric_value
                })
        
        # Sort descending by metric
        runs_with_metric.sort(key=lambda x: x[metric], reverse=True)
        
        return runs_with_metric[:limit]

