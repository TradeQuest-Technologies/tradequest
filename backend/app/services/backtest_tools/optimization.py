"""
Optimization Tools for Backtest Copilot
Advanced tools for optimization, validation, and statistical analysis.
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional
from scipy import stats
from sqlalchemy.orm import Session

from app.models.backtest_v2 import BacktestRun
from app.models.user import User
import structlog

logger = structlog.get_logger()


class OptimizationTools:
    """Tools for optimization and advanced analysis"""
    
    def __init__(self, db: Session, user: User):
        self.db = db
        self.user = user
    
    def monte_carlo_simulation(
        self,
        run_id: str,
        n_simulations: int = 1000,
        confidence_level: float = 0.95
    ) -> Dict[str, Any]:
        """
        Run Monte Carlo simulation on trade sequence.
        
        Randomly reorders trades to test if results are due to skill or luck.
        
        Returns:
        - original_return: Actual return from backtest
        - simulated_returns: Distribution of simulated returns
        - percentile: Where original falls in distribution
        - confidence_interval: [lower, upper] bounds
        - is_significant: True if original outperforms random chance
        """
        run = self.db.query(BacktestRun).filter(
            BacktestRun.id == run_id,
            BacktestRun.user_id == self.user.id
        ).first()
        
        if not run or not run.trades:
            raise ValueError("Run not found or has no trades")
        
        trades = run.trades
        original_return = (run.metrics or {}).get('total_return', 0)
        
        # Extract trade returns
        trade_returns = [t.get('pnl_pct', 0) for t in trades]
        
        # Run simulations
        simulated_returns = []
        for _ in range(n_simulations):
            # Randomly shuffle trades
            shuffled_returns = np.random.choice(trade_returns, size=len(trade_returns), replace=False)
            cumulative_return = np.prod([1 + r/100 for r in shuffled_returns]) - 1
            simulated_returns.append(cumulative_return * 100)
        
        simulated_returns = np.array(simulated_returns)
        
        # Calculate statistics
        percentile = stats.percentileofscore(simulated_returns, original_return)
        lower_bound = np.percentile(simulated_returns, (1 - confidence_level) / 2 * 100)
        upper_bound = np.percentile(simulated_returns, (1 + confidence_level) / 2 * 100)
        
        is_significant = original_return > upper_bound
        
        return {
            "original_return": original_return,
            "simulated_mean": float(np.mean(simulated_returns)),
            "simulated_std": float(np.std(simulated_returns)),
            "percentile": float(percentile),
            "confidence_interval": [float(lower_bound), float(upper_bound)],
            "is_significant": is_significant,
            "interpretation": (
                f"Your strategy's return ({original_return:.2f}%) falls at the "
                f"{percentile:.1f}th percentile of random orderings. "
                + ("This suggests skill beyond random chance." if is_significant else "This could be due to luck.")
            )
        }
    
    def detect_overfitting(self, run_id: str) -> Dict[str, Any]:
        """
        Statistical tests for overfitting.
        
        Checks:
        - Sample size adequacy
        - Trade frequency consistency
        - Outlier dependence
        - Equity curve smoothness
        
        Returns:
        - risk_score: 0-100 (higher = more overfitting risk)
        - flags: List of warning flags
        - recommendations: How to improve
        """
        run = self.db.query(BacktestRun).filter(
            BacktestRun.id == run_id,
            BacktestRun.user_id == self.user.id
        ).first()
        
        if not run:
            raise ValueError("Run not found")
        
        metrics = run.metrics or {}
        trades = run.trades or []
        
        flags = []
        risk_score = 0
        
        # Check 1: Sample size
        n_trades = len(trades)
        if n_trades < 30:
            flags.append("Insufficient sample size (< 30 trades)")
            risk_score += 30
        elif n_trades < 100:
            flags.append("Small sample size (< 100 trades)")
            risk_score += 15
        
        # Check 2: Win rate
        win_rate = metrics.get('win_rate', 0)
        if win_rate > 0.70:
            flags.append("Unusually high win rate (> 70%)")
            risk_score += 20
        
        # Check 3: Sharpe ratio
        sharpe = metrics.get('sharpe_ratio', 0)
        if sharpe > 3.0:
            flags.append("Unrealistically high Sharpe ratio (> 3.0)")
            risk_score += 25
        
        # Check 4: Outlier dependence
        if trades:
            pnls = [t.get('pnl', 0) for t in trades]
            max_pnl = max(pnls) if pnls else 0
            total_pnl = sum(pnls)
            if max_pnl > 0 and total_pnl > 0 and (max_pnl / total_pnl) > 0.5:
                flags.append("High dependence on single best trade (> 50% of profits)")
                risk_score += 20
        
        # Check 5: Drawdown analysis
        max_dd = metrics.get('max_drawdown', 0)
        if max_dd < 0.05:  # Less than 5% max drawdown
            flags.append("Unusually low max drawdown (< 5%)")
            risk_score += 15
        
        recommendations = []
        if risk_score > 50:
            recommendations.append("Increase sample size with more historical data")
            recommendations.append("Test on out-of-sample data")
            recommendations.append("Perform walk-forward analysis")
            recommendations.append("Check for data snooping bias")
        
        return {
            "risk_score": min(risk_score, 100),
            "risk_level": "Low" if risk_score < 30 else "Medium" if risk_score < 60 else "High",
            "flags": flags,
            "recommendations": recommendations,
            "n_trades": n_trades,
            "interpretation": (
                f"Overfitting risk: {min(risk_score, 100)}/100. "
                + ("Low risk - results appear robust." if risk_score < 30 else
                   "Medium risk - some concerns present." if risk_score < 60 else
                   "High risk - significant overfitting concerns.")
            )
        }
    
    def validate_statistical_significance(
        self,
        run_id: str,
        benchmark_return: float = 0.0
    ) -> Dict[str, Any]:
        """
        Bootstrap analysis and hypothesis testing.
        
        Tests if strategy returns are statistically different from benchmark.
        
        Args:
        - benchmark_return: Return to test against (default: 0)
        
        Returns:
        - t_statistic: T-test statistic
        - p_value: Probability results are due to chance
        - is_significant: True if p < 0.05
        - confidence_interval: 95% CI for mean return
        """
        run = self.db.query(BacktestRun).filter(
            BacktestRun.id == run_id,
            BacktestRun.user_id == self.user.id
        ).first()
        
        if not run or not run.trades:
            raise ValueError("Run not found or has no trades")
        
        # Get trade returns
        trade_returns = [t.get('pnl_pct', 0) for t in run.trades]
        
        if len(trade_returns) < 2:
            return {
                "error": "Insufficient trades for statistical test",
                "is_significant": False
            }
        
        # One-sample t-test against benchmark
        t_statistic, p_value = stats.ttest_1samp(trade_returns, benchmark_return)
        
        # Bootstrap confidence interval
        n_bootstrap = 1000
        bootstrap_means = []
        for _ in range(n_bootstrap):
            sample = np.random.choice(trade_returns, size=len(trade_returns), replace=True)
            bootstrap_means.append(np.mean(sample))
        
        ci_lower = np.percentile(bootstrap_means, 2.5)
        ci_upper = np.percentile(bootstrap_means, 97.5)
        
        is_significant = p_value < 0.05
        
        return {
            "t_statistic": float(t_statistic),
            "p_value": float(p_value),
            "is_significant": is_significant,
            "mean_return_pct": float(np.mean(trade_returns)),
            "confidence_interval_95": [float(ci_lower), float(ci_upper)],
            "n_trades": len(trade_returns),
            "interpretation": (
                f"Mean return per trade: {np.mean(trade_returns):.2f}% "
                f"(95% CI: [{ci_lower:.2f}%, {ci_upper:.2f}%]). "
                + ("Statistically significant at p<0.05." if is_significant else
                   f"Not statistically significant (p={p_value:.3f}).")
            )
        }
    
    def parameter_sensitivity_analysis(
        self,
        run_ids: List[str],
        parameter_name: str
    ) -> Dict[str, Any]:
        """
        Analyze how a parameter affects results across multiple runs.
        
        Args:
        - run_ids: List of run IDs with different parameter values
        - parameter_name: Name of parameter to analyze
        
        Returns:
        - parameter_values: List of parameter values tested
        - metric_values: Corresponding metric values
        - correlation: Correlation between parameter and performance
        - optimal_value: Best parameter value found
        """
        runs = self.db.query(BacktestRun).filter(
            BacktestRun.id.in_(run_ids),
            BacktestRun.user_id == self.user.id
        ).all()
        
        if len(runs) < 2:
            raise ValueError("Need at least 2 runs for sensitivity analysis")
        
        # Extract parameter values and returns
        data_points = []
        for run in runs:
            config = run.config or {}
            param_value = config.get(parameter_name)
            total_return = (run.metrics or {}).get('total_return', 0)
            
            if param_value is not None:
                data_points.append({
                    "parameter_value": param_value,
                    "total_return": total_return,
                    "sharpe_ratio": (run.metrics or {}).get('sharpe_ratio', 0),
                    "max_drawdown": (run.metrics or {}).get('max_drawdown', 0)
                })
        
        if len(data_points) < 2:
            raise ValueError(f"Parameter '{parameter_name}' not found in run configs")
        
        # Calculate correlations
        param_values = [d['parameter_value'] for d in data_points]
        returns = [d['total_return'] for d in data_points]
        sharpes = [d['sharpe_ratio'] for d in data_points]
        
        return_corr, _ = stats.pearsonr(param_values, returns) if len(param_values) > 1 else (0, 1)
        sharpe_corr, _ = stats.pearsonr(param_values, sharpes) if len(param_values) > 1 else (0, 1)
        
        # Find optimal
        best_idx = max(range(len(sharpes)), key=lambda i: sharpes[i])
        optimal_value = param_values[best_idx]
        
        return {
            "parameter_name": parameter_name,
            "n_runs_analyzed": len(data_points),
            "parameter_values": param_values,
            "total_returns": returns,
            "sharpe_ratios": sharpes,
            "correlation_with_return": float(return_corr),
            "correlation_with_sharpe": float(sharpe_corr),
            "optimal_value": optimal_value,
            "optimal_sharpe": sharpes[best_idx],
            "interpretation": (
                f"Parameter '{parameter_name}' shows "
                + ("strong positive" if abs(sharpe_corr) > 0.7 and sharpe_corr > 0 else
                   "strong negative" if abs(sharpe_corr) > 0.7 and sharpe_corr < 0 else
                   "moderate" if abs(sharpe_corr) > 0.3 else "weak")
                + f" correlation with Sharpe ratio (r={sharpe_corr:.2f}). "
                f"Optimal value found: {optimal_value}"
            )
        }
    
    def walk_forward_analysis(
        self,
        run_id: str,
        n_splits: int = 5
    ) -> Dict[str, Any]:
        """
        Test strategy robustness over time using walk-forward analysis.
        
        Splits equity curve into sequential periods and analyzes consistency.
        
        Returns:
        - period_returns: Returns for each period
        - consistency_score: 0-100 (higher = more consistent)
        - declining_performance: True if performance degrades over time
        """
        run = self.db.query(BacktestRun).filter(
            BacktestRun.id == run_id,
            BacktestRun.user_id == self.user.id
        ).first()
        
        if not run or not run.equity_curve:
            raise ValueError("Run not found or has no equity curve")
        
        equity_curve = run.equity_curve
        n_points = len(equity_curve)
        
        if n_points < n_splits * 10:  # Need at least 10 points per split
            raise ValueError(f"Insufficient data points for {n_splits} splits")
        
        # Split into periods
        period_size = n_points // n_splits
        period_returns = []
        
        for i in range(n_splits):
            start_idx = i * period_size
            end_idx = start_idx + period_size if i < n_splits - 1 else n_points
            
            period_equity = equity_curve[start_idx:end_idx]
            start_equity = period_equity[0]['equity']
            end_equity = period_equity[-1]['equity']
            
            period_return = ((end_equity - start_equity) / start_equity) * 100
            period_returns.append({
                "period": i + 1,
                "return_pct": float(period_return),
                "start_date": period_equity[0]['timestamp'],
                "end_date": period_equity[-1]['timestamp']
            })
        
        # Calculate consistency
        returns_only = [p['return_pct'] for p in period_returns]
        positive_periods = sum(1 for r in returns_only if r > 0)
        consistency_score = (positive_periods / n_splits) * 100
        
        # Check for declining performance
        first_half_avg = np.mean(returns_only[:n_splits//2])
        second_half_avg = np.mean(returns_only[n_splits//2:])
        declining_performance = second_half_avg < first_half_avg * 0.7  # 30% decline
        
        return {
            "n_periods": n_splits,
            "period_returns": period_returns,
            "mean_period_return": float(np.mean(returns_only)),
            "std_period_return": float(np.std(returns_only)),
            "consistency_score": float(consistency_score),
            "declining_performance": declining_performance,
            "interpretation": (
                f"Strategy was profitable in {positive_periods}/{n_splits} periods "
                f"({consistency_score:.0f}% consistency). "
                + ("⚠️ Performance declined in later periods." if declining_performance else
                   "Performance remained stable over time.")
            )
        }

