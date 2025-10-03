"""
Walk-forward validation engine
"""

from typing import List, Dict, Any
import pandas as pd
from datetime import datetime, timedelta
import structlog

from app.schemas.backtest_v2 import BlockNode, RunConfig, WalkForwardConfig, FoldResult, BacktestMetrics
from app.services.backtest_engine_v2 import BacktestEngineV2

logger = structlog.get_logger()


class WalkForwardEngine:
    """Walk-forward validation with rolling or expanding windows"""
    
    def __init__(self):
        self.engine = BacktestEngineV2()
    
    async def run_walk_forward(
        self,
        graph_nodes: List[BlockNode],
        graph_outputs: List[str],
        config: RunConfig,
        wf_config: WalkForwardConfig,
        progress_callback=None
    ) -> Dict[str, Any]:
        """
        Run walk-forward validation
        
        Args:
            graph_nodes: Strategy graph
            graph_outputs: Output node IDs
            config: Base config
            wf_config: Walk-forward configuration
            progress_callback: Progress updates
            
        Returns:
            Walk-forward results with per-fold metrics
        """
        
        try:
            # Generate fold windows
            folds = self._generate_folds(
                config.start_date,
                config.end_date,
                wf_config.train_window_days,
                wf_config.test_window_days,
                wf_config.folds,
                wf_config.mode
            )
            
            logger.info(f"Generated {len(folds)} walk-forward folds")
            
            # Run backtest for each fold
            fold_results = []
            all_trades = []
            
            for i, fold in enumerate(folds):
                if progress_callback:
                    progress = int((i / len(folds)) * 80) + 10
                    await progress_callback(progress, f"Running fold {i+1}/{len(folds)}...")
                
                logger.info(f"Running fold {i+1}: train={fold['train_start']} to {fold['train_end']}, test={fold['test_start']} to {fold['test_end']}")
                
                # Create config for test period
                fold_config = config.copy(deep=True)
                fold_config.start_date = fold["test_start"]
                fold_config.end_date = fold["test_end"]
                
                # Run backtest
                result = await self.engine.run_backtest(
                    graph_nodes,
                    graph_outputs,
                    fold_config,
                    progress_callback=None
                )
                
                if result.get("success"):
                    fold_result = FoldResult(
                        fold=i + 1,
                        train_start=fold["train_start"],
                        train_end=fold["train_end"],
                        test_start=fold["test_start"],
                        test_end=fold["test_end"],
                        metrics=result["metrics"],
                        trade_count=len(result.get("trades", []))
                    )
                    fold_results.append(fold_result)
                    
                    # Collect trades
                    all_trades.extend(result.get("trades", []))
                    
                    logger.info(f"Fold {i+1} complete: Sharpe={result['metrics'].sharpe_ratio:.2f}, Trades={len(result.get('trades', []))}")
                else:
                    logger.error(f"Fold {i+1} failed: {result.get('error')}")
            
            # Aggregate fold metrics
            if fold_results:
                avg_metrics = self._aggregate_fold_metrics(fold_results)
            else:
                avg_metrics = None
            
            if progress_callback:
                await progress_callback(90, "Aggregating results...")
            
            return {
                "success": True,
                "folds": fold_results,
                "avg_metrics": avg_metrics,
                "all_trades": all_trades,
                "total_folds": len(folds)
            }
            
        except Exception as e:
            logger.error(f"Walk-forward validation failed: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
    
    def _generate_folds(
        self,
        start_date: str,
        end_date: str,
        train_window_days: int,
        test_window_days: int,
        n_folds: int,
        mode: str
    ) -> List[Dict[str, str]]:
        """Generate fold windows"""
        
        start = pd.to_datetime(start_date)
        end = pd.to_datetime(end_date)
        
        total_days = (end - start).days
        
        if mode == "rolling":
            # Rolling window: fixed train/test size, advancing through time
            fold_stride = (total_days - train_window_days - test_window_days) // (n_folds - 1)
            fold_stride = max(fold_stride, test_window_days)
            
            folds = []
            for i in range(n_folds):
                train_start = start + timedelta(days=i * fold_stride)
                train_end = train_start + timedelta(days=train_window_days)
                test_start = train_end
                test_end = test_start + timedelta(days=test_window_days)
                
                # Don't exceed end date
                if test_end > end:
                    break
                
                folds.append({
                    "train_start": train_start.strftime("%Y-%m-%d"),
                    "train_end": train_end.strftime("%Y-%m-%d"),
                    "test_start": test_start.strftime("%Y-%m-%d"),
                    "test_end": test_end.strftime("%Y-%m-%d")
                })
        
        else:  # expanding
            # Expanding window: growing train size, fixed test size
            total_test_days = n_folds * test_window_days
            remaining_days = total_days - total_test_days
            
            folds = []
            for i in range(n_folds):
                train_start = start
                train_end = start + timedelta(days=train_window_days + i * (remaining_days // n_folds))
                test_start = train_end
                test_end = test_start + timedelta(days=test_window_days)
                
                if test_end > end:
                    test_end = end
                
                folds.append({
                    "train_start": train_start.strftime("%Y-%m-%d"),
                    "train_end": train_end.strftime("%Y-%m-%d"),
                    "test_start": test_start.strftime("%Y-%m-%d"),
                    "test_end": test_end.strftime("%Y-%m-%d")
                })
        
        return folds
    
    def _aggregate_fold_metrics(self, folds: List[FoldResult]) -> BacktestMetrics:
        """Aggregate metrics across folds"""
        
        # Average key metrics
        avg_cagr = sum(f.metrics.cagr for f in folds) / len(folds)
        avg_sharpe = sum(f.metrics.sharpe_ratio for f in folds) / len(folds)
        avg_sortino = sum(f.metrics.sortino_ratio for f in folds) / len(folds)
        avg_calmar = sum(f.metrics.calmar_ratio for f in folds) / len(folds)
        max_dd = max(f.metrics.max_drawdown for f in folds)
        avg_win_rate = sum(f.metrics.win_rate for f in folds) / len(folds)
        total_trades = sum(f.metrics.total_trades for f in folds)
        
        return BacktestMetrics(
            cagr=avg_cagr,
            total_return=sum(f.metrics.total_return for f in folds) / len(folds),
            sharpe_ratio=avg_sharpe,
            sortino_ratio=avg_sortino,
            calmar_ratio=avg_calmar,
            stdev=sum(f.metrics.stdev for f in folds) / len(folds),
            max_drawdown=max_dd,
            max_drawdown_duration_days=None,
            ulcer_index=None,
            total_trades=total_trades,
            win_rate=avg_win_rate,
            profit_factor=sum(f.metrics.profit_factor for f in folds) / len(folds),
            avg_win=sum(f.metrics.avg_win for f in folds) / len(folds),
            avg_loss=sum(f.metrics.avg_loss for f in folds) / len(folds),
            expectancy=sum(f.metrics.expectancy for f in folds) / len(folds),
            exposure_pct=sum(f.metrics.exposure_pct for f in folds) / len(folds),
            turnover=sum(f.metrics.turnover for f in folds) / len(folds),
            total_fees=sum(f.metrics.total_fees for f in folds),
            total_slippage=sum(f.metrics.total_slippage for f in folds)
        )

