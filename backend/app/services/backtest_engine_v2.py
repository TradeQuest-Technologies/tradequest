"""
Enhanced Backtesting Engine v2
Event-driven simulator with block-based strategy graph execution
"""

import asyncio
from typing import Dict, List, Any, Optional
import pandas as pd
import numpy as np
from datetime import datetime
import structlog
import hashlib
import json

from app.services.blocks import BlockRegistry, BlockContext, BlockOutput
from app.schemas.backtest_v2 import (
    BlockNode, RunConfig, BacktestMetrics, EquityPoint, 
    Trade, FoldResult, MonteCarloSummary, RunWarning
)

logger = structlog.get_logger()


class GraphExecutor:
    """Executes strategy graph (DAG of blocks)"""
    
    def __init__(self, nodes: List[BlockNode], outputs: List[str]):
        self.nodes = {node.id: node for node in nodes}
        self.outputs = outputs
        self.execution_order = self._topological_sort()
    
    def _topological_sort(self) -> List[str]:
        """Sort nodes in execution order (topological sort)"""
        # Build dependency graph
        in_degree = {node_id: 0 for node_id in self.nodes}
        adjacency = {node_id: [] for node_id in self.nodes}
        
        for node_id, node in self.nodes.items():
            for input_id in node.inputs:
                if input_id in self.nodes:
                    adjacency[input_id].append(node_id)
                    in_degree[node_id] += 1
        
        # Kahn's algorithm
        queue = [node_id for node_id, degree in in_degree.items() if degree == 0]
        sorted_nodes = []
        
        while queue:
            node_id = queue.pop(0)
            sorted_nodes.append(node_id)
            
            for neighbor in adjacency[node_id]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
        
        if len(sorted_nodes) != len(self.nodes):
            raise ValueError("Graph contains a cycle")
        
        return sorted_nodes
    
    async def execute(self, initial_context: BlockContext) -> tuple[BlockContext, Dict[str, BlockOutput]]:
        """Execute all blocks in order"""
        results: Dict[str, BlockOutput] = {}
        context = initial_context
        
        for node_id in self.execution_order:
            node = self.nodes[node_id]
            
            # Get inputs from previous blocks
            input_results = [results[inp_id] for inp_id in node.inputs if inp_id in results]
            
            # Create executor
            try:
                executor = BlockRegistry.create(node.type, node_id, node.params)
            except Exception as e:
                logger.error(f"Failed to create executor for {node_id}: {e}")
                # Create error output
                results[node_id] = BlockOutput(
                    success=False,
                    context=context,
                    error=f"Executor creation failed: {str(e)}"
                )
                continue
            
            # Execute block
            try:
                output = await executor.execute(context, input_results)
                results[node_id] = output
                
                if output.success:
                    context = output.context
                    logger.info(f"Block {node_id} ({node.type}) executed successfully", data=output.data)
                else:
                    logger.error(f"Block {node_id} ({node.type}) failed: {output.error}")
                    
            except Exception as e:
                logger.error(f"Block {node_id} execution failed: {e}")
                results[node_id] = BlockOutput(
                    success=False,
                    context=context,
                    error=f"Execution error: {str(e)}"
                )
        
        # Verify output blocks executed successfully
        for output_id in self.outputs:
            if output_id not in results or not results[output_id].success:
                logger.warning(f"Output block {output_id} did not execute successfully")
        
        return context, results


class BacktestEngineV2:
    """Enhanced backtesting engine"""
    
    def __init__(self):
        pass
    
    async def run_backtest(
        self,
        graph_nodes: List[Any],  # Can be BlockNode or dict
        graph_outputs: List[str],
        config: RunConfig,
        progress_callback: Optional[callable] = None
    ) -> Dict[str, Any]:
        """
        Run complete backtest
        
        Args:
            graph_nodes: Strategy graph nodes
            graph_outputs: Output node IDs
            config: Run configuration
            progress_callback: Optional callback for progress updates
            
        Returns:
            Complete backtest results
        """
        
        try:
            # Convert graph_nodes to BlockNode objects if they're dicts
            if graph_nodes and isinstance(graph_nodes[0], dict):
                from app.schemas.backtest_v2 import BlockNode
                nodes = [BlockNode(**node) for node in graph_nodes]
            else:
                nodes = graph_nodes
            
            # Set random seeds for reproducibility
            if config.seeds:
                np.random.seed(config.seeds.get("numpy", 42))
                # torch.manual_seed(config.seeds.get("torch", 42))  # If using torch
            
            # Initialize context
            context = BlockContext(
                symbol=config.symbol,
                timeframe=config.timeframe,
                initial_capital=config.initial_capital
            )
            
            # Execute graph
            if progress_callback:
                await progress_callback(10, "Building strategy graph...")
            
            executor = GraphExecutor(nodes, graph_outputs)
            
            if progress_callback:
                await progress_callback(20, "Executing strategy...")
            
            result_context, execution_results = await executor.execute(context)
            
            # Check if any output blocks failed
            failed_outputs = []
            for output_id in graph_outputs:
                if output_id in execution_results and not execution_results[output_id].success:
                    failed_outputs.append(output_id)
            
            if failed_outputs:
                error_messages = []
                for output_id in failed_outputs:
                    error_messages.append(f"{output_id}: {execution_results[output_id].error}")
                
                return {
                    "success": False,
                    "error": f"Strategy execution failed. Output blocks failed: {', '.join(error_messages)}"
                }
            
            if progress_callback:
                await progress_callback(60, "Calculating metrics...")
            
            # Calculate metrics
            metrics = self._calculate_metrics(result_context, config)
            
            if progress_callback:
                await progress_callback(70, "Generating equity curve...")
            
            # Generate equity curve
            equity_curve = self._generate_equity_curve(result_context)
            
            if progress_callback:
                await progress_callback(80, "Running Monte Carlo...")
            
            # Run Monte Carlo if enough trades
            mc_summary = None
            if len(result_context.trades) >= 10:
                mc_summary = self._run_monte_carlo(result_context.trades, n_runs=10000)
            
            if progress_callback:
                await progress_callback(90, "Generating diagnostics...")
            
            # Generate warnings
            warnings = self._generate_warnings(metrics, result_context)
            
            # Calculate hashes for reproducibility
            graph_sha = self._hash_graph(nodes)
            params_sha = self._hash_params(config.dict())
            
            if progress_callback:
                await progress_callback(100, "Complete!")
            
            return {
                "success": True,
                "metrics": metrics,
                "equity_curve": equity_curve,
                "trades": result_context.trades,
                "mc_summary": mc_summary,
                "warnings": warnings,
                "graph_sha": graph_sha,
                "params_sha": params_sha,
                "data_sha": None,  # TODO: Calculate from actual data
                "repro_id": hashlib.sha256(f"{graph_sha}:{params_sha}".encode()).hexdigest()
            }
            
        except Exception as e:
            logger.error(f"Backtest execution failed: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
    
    def _calculate_metrics(self, context: BlockContext, config: RunConfig) -> BacktestMetrics:
        """Calculate comprehensive metrics"""
        
        trades = context.trades
        if not trades:
            return BacktestMetrics(
                cagr=0, total_return=0, sharpe_ratio=0, sortino_ratio=0, calmar_ratio=0,
                stdev=0, max_drawdown=0, max_drawdown_duration_days=None, ulcer_index=None,
                total_trades=0, win_rate=0, profit_factor=0, avg_win=0, avg_loss=0,
                expectancy=0, exposure_pct=0, turnover=0, total_fees=0, total_slippage=0
            )
        
        # Extract trade PnLs
        pnls = [t["pnl"] for t in trades]
        winning_trades = [p for p in pnls if p > 0]
        losing_trades = [p for p in pnls if p < 0]
        
        # Returns
        total_return = sum(pnls)
        total_return_pct = total_return / config.initial_capital
        
        # Time period
        if trades:
            start = pd.to_datetime(trades[0]["entry_time"])
            end = pd.to_datetime(trades[-1]["exit_time"])
            years = (end - start).days / 365.25
            cagr = ((1 + total_return_pct) ** (1 / max(years, 0.1))) - 1 if years > 0 else 0
        else:
            cagr = 0
        
        # Risk metrics
        returns_series = pd.Series(pnls)
        stdev = returns_series.std()
        
        # Sharpe (simplified - using trade-level returns)
        sharpe = (returns_series.mean() / stdev) if stdev > 0 else 0
        
        # Sortino (downside deviation)
        downside_returns = returns_series[returns_series < 0]
        downside_std = downside_returns.std() if len(downside_returns) > 0 else stdev
        sortino = (returns_series.mean() / downside_std) if downside_std > 0 else 0
        
        # Max drawdown (from equity curve)
        equity = config.initial_capital
        equity_curve = [equity]
        for pnl in pnls:
            equity += pnl
            equity_curve.append(equity)
        
        equity_series = pd.Series(equity_curve)
        running_max = equity_series.expanding().max()
        drawdowns = (equity_series - running_max) / running_max
        max_dd = abs(drawdowns.min())
        
        # Calmar
        calmar = cagr / max_dd if max_dd > 0 else 0
        
        # Trade stats
        win_rate = len(winning_trades) / len(trades) if trades else 0
        avg_win = np.mean(winning_trades) if winning_trades else 0
        avg_loss = np.mean(losing_trades) if losing_trades else 0
        profit_factor = abs(sum(winning_trades) / sum(losing_trades)) if losing_trades and sum(losing_trades) != 0 else 0
        expectancy = np.mean(pnls)
        
        # Costs
        total_fees = sum(t.get("fees", 0) for t in trades)
        total_slippage = sum(t.get("slippage", 0) * t.get("quantity", 0) for t in trades)
        
        # Exposure & turnover (simplified)
        total_holding_time = sum(t.get("holding_time_hours", 0) for t in trades)
        exposure_pct = 0.5  # Placeholder
        turnover = len(trades) / max(years, 0.1) if years > 0 else 0
        
        return BacktestMetrics(
            cagr=float(cagr),
            total_return=float(total_return_pct),
            sharpe_ratio=float(sharpe),
            sortino_ratio=float(sortino),
            calmar_ratio=float(calmar),
            stdev=float(stdev),
            max_drawdown=float(max_dd),
            max_drawdown_duration_days=None,
            ulcer_index=None,
            total_trades=len(trades),
            win_rate=float(win_rate),
            profit_factor=float(profit_factor),
            avg_win=float(avg_win),
            avg_loss=float(avg_loss),
            expectancy=float(expectancy),
            exposure_pct=float(exposure_pct),
            turnover=float(turnover),
            total_fees=float(total_fees),
            total_slippage=float(total_slippage)
        )
    
    def _generate_equity_curve(self, context: BlockContext) -> List[EquityPoint]:
        """Generate equity curve points"""
        
        equity_curve = []
        equity = context.initial_capital
        trade_count = 0
        
        for trade in context.trades:
            equity += trade["pnl"]
            trade_count += 1
            
            # Calculate drawdown
            peak = max([ep.equity for ep in equity_curve] + [context.initial_capital])
            drawdown_pct = ((equity - peak) / peak) * 100 if peak > 0 else 0
            
            equity_curve.append(EquityPoint(
                timestamp=trade["exit_time"],
                equity=equity,
                drawdown_pct=drawdown_pct,
                trade_count=trade_count
            ))
        
        return equity_curve
    
    def _run_monte_carlo(self, trades: List[Dict], n_runs: int = 10000) -> MonteCarloSummary:
        """Run Monte Carlo simulation by resampling trades"""
        
        pnls = [t["pnl"] for t in trades]
        
        mc_results = []
        for _ in range(n_runs):
            # Randomly sample trades with replacement
            sample_pnls = np.random.choice(pnls, size=len(pnls), replace=True)
            total_return = np.sum(sample_pnls)
            mc_results.append(total_return)
        
        mc_results = np.array(mc_results)
        
        # Calculate Sharpe for each run
        sharpes = []
        for _ in range(min(n_runs, 1000)):
            sample_pnls = np.random.choice(pnls, size=len(pnls), replace=True)
            sharpe = np.mean(sample_pnls) / np.std(sample_pnls) if np.std(sample_pnls) > 0 else 0
            sharpes.append(sharpe)
        
        sharpes = np.array(sharpes)
        
        return MonteCarloSummary(
            n_runs=n_runs,
            median_return=float(np.median(mc_results)),
            p05_return=float(np.percentile(mc_results, 5)),
            p25_return=float(np.percentile(mc_results, 25)),
            p75_return=float(np.percentile(mc_results, 75)),
            p95_return=float(np.percentile(mc_results, 95)),
            median_sharpe=float(np.median(sharpes)),
            p05_sharpe=float(np.percentile(sharpes, 5)),
            p95_sharpe=float(np.percentile(sharpes, 95))
        )
    
    def _generate_warnings(self, metrics: BacktestMetrics, context: BlockContext) -> List[RunWarning]:
        """Generate diagnostic warnings"""
        
        warnings = []
        
        # Overfit detection
        if metrics.win_rate > 0.95:
            warnings.append(RunWarning(
                type="overfit",
                message=f"Suspiciously high win rate: {metrics.win_rate:.1%}",
                severity="warning",
                details={"win_rate": metrics.win_rate}
            ))
        
        # Low sample size
        if metrics.total_trades < 30:
            warnings.append(RunWarning(
                type="low_sample",
                message=f"Low number of trades: {metrics.total_trades}",
                severity="info",
                details={"total_trades": metrics.total_trades}
            ))
        
        # High turnover
        if metrics.turnover > 500:
            warnings.append(RunWarning(
                type="high_turnover",
                message=f"High turnover may indicate over-trading: {metrics.turnover:.0f} trades/year",
                severity="warning",
                details={"turnover": metrics.turnover}
            ))
        
        # Suspicious metrics
        if metrics.sharpe_ratio > 5.0:
            warnings.append(RunWarning(
                type="suspicious_metric",
                message=f"Unusually high Sharpe ratio: {metrics.sharpe_ratio:.2f}",
                severity="warning",
                details={"sharpe_ratio": metrics.sharpe_ratio}
            ))
        
        return warnings
    
    def _hash_graph(self, nodes: List[BlockNode]) -> str:
        """Calculate hash of graph structure"""
        graph_dict = [
            {"id": n.id, "type": n.type, "params": n.params, "inputs": n.inputs}
            for n in sorted(nodes, key=lambda x: x.id)
        ]
        graph_json = json.dumps(graph_dict, sort_keys=True)
        return hashlib.sha256(graph_json.encode()).hexdigest()
    
    def _hash_params(self, params: Dict) -> str:
        """Calculate hash of parameters"""
        params_json = json.dumps(params, sort_keys=True)
        return hashlib.sha256(params_json.encode()).hexdigest()

