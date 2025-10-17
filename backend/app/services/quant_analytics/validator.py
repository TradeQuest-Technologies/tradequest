"""
Statistical Validation Service
Monte Carlo simulation, bootstrap analysis, overfitting detection
"""

import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional, Tuple
from scipy import stats
from sklearn.model_selection import TimeSeriesSplit
import structlog

logger = structlog.get_logger()


class StatisticalValidator:
    """Statistical validation for trading strategies"""
    
    def __init__(self, trades: List[Dict], equity_curve: List[Dict], config: Dict):
        """
        Initialize statistical validator
        
        Args:
            trades: List of trade dictionaries
            equity_curve: List of equity points
            config: Strategy configuration
        """
        self.trades = trades
        self.equity_curve = equity_curve
        self.config = config
        self.initial_capital = config.get('initial_capital', 10000)
        
        self.returns = np.array([t['pnl'] / self.initial_capital for t in trades])
        self.pnls = np.array([t['pnl'] for t in trades])
        
        logger.info(f"StatisticalValidator initialized", trades=len(trades))
    
    def calculate_all_validations(self) -> Dict[str, Any]:
        """Run all statistical validations"""
        try:
            return {
                'monte_carlo': self.run_monte_carlo(),
                'bootstrap': self.run_bootstrap_analysis(),
                'overfitting': self.detect_overfitting(),
                'trade_independence': self.test_trade_independence(),
                'hypothesis_tests': self.run_hypothesis_tests(),
                'luck_vs_skill': self.analyze_luck_vs_skill()
            }
        except Exception as e:
            logger.error(f"Statistical validation failed: {e}", exc_info=True)
            raise
    
    def run_monte_carlo(self, n_simulations: int = 1000, seed: int = 42) -> Dict[str, Any]:
        """
        Run Monte Carlo simulation by randomly shuffling trade order
        Shows range of possible outcomes to validate if results were luck
        """
        if len(self.trades) < 10:
            return {'error': 'Insufficient trades for Monte Carlo'}
        
        np.random.seed(seed)
        
        # Store simulation results
        final_equities = []
        max_drawdowns = []
        sharpe_ratios = []
        
        # Run simulations
        for _ in range(n_simulations):
            # Randomly shuffle trade order
            shuffled_pnls = np.random.permutation(self.pnls)
            
            # Calculate equity curve
            equity = self.initial_capital + np.cumsum(shuffled_pnls)
            final_equities.append(equity[-1])
            
            # Calculate max drawdown
            running_max = np.maximum.accumulate(equity)
            drawdown = (equity - running_max) / running_max
            max_drawdowns.append(np.min(drawdown) * 100)
            
            # Calculate Sharpe ratio
            returns = shuffled_pnls / self.initial_capital
            sharpe = (np.mean(returns) / np.std(returns) * np.sqrt(len(returns))) if np.std(returns) > 0 else 0
            sharpe_ratios.append(sharpe)
        
        # Actual results
        actual_equity = self.equity_curve[-1]['equity'] if self.equity_curve else self.initial_capital
        actual_return = (actual_equity - self.initial_capital) / self.initial_capital * 100
        actual_sharpe = np.mean(self.returns) / np.std(self.returns) * np.sqrt(len(self.returns)) if np.std(self.returns) > 0 else 0
        
        # Calculate statistics
        simulated_returns = [(eq - self.initial_capital) / self.initial_capital * 100 for eq in final_equities]
        
        return {
            'simulations_run': n_simulations,
            'equity_distribution': {
                'mean': float(np.mean(final_equities)),
                'median': float(np.median(final_equities)),
                'std': float(np.std(final_equities)),
                'min': float(np.min(final_equities)),
                'max': float(np.max(final_equities)),
                'percentile_5': float(np.percentile(final_equities, 5)),
                'percentile_95': float(np.percentile(final_equities, 95)),
                'histogram': self._create_histogram(simulated_returns, bins=50)
            },
            'drawdown_distribution': {
                'mean': float(np.mean(max_drawdowns)),
                'median': float(np.median(max_drawdowns)),
                'percentile_5': float(np.percentile(max_drawdowns, 5)),
                'percentile_95': float(np.percentile(max_drawdowns, 95)),
                'histogram': self._create_histogram(max_drawdowns, bins=30)
            },
            'sharpe_distribution': {
                'mean': float(np.mean(sharpe_ratios)),
                'median': float(np.median(sharpe_ratios)),
                'percentile_5': float(np.percentile(sharpe_ratios, 5)),
                'percentile_95': float(np.percentile(sharpe_ratios, 95))
            },
            'actual_vs_simulated': {
                'actual_return_pct': float(actual_return),
                'actual_sharpe': float(actual_sharpe),
                'actual_percentile': float(stats.percentileofscore(simulated_returns, actual_return)),
                'sharpe_percentile': float(stats.percentileofscore(sharpe_ratios, actual_sharpe)),
                'outperformed_pct': float(np.sum(np.array(simulated_returns) < actual_return) / n_simulations * 100)
            },
            'confidence_bands': self._calculate_confidence_bands(),
            'interpretation': self._interpret_monte_carlo(
                actual_return,
                simulated_returns,
                float(stats.percentileofscore(simulated_returns, actual_return))
            )
        }
    
    def _create_histogram(self, data: List[float], bins: int = 30) -> Dict[str, List]:
        """Create histogram data for visualization"""
        counts, bin_edges = np.histogram(data, bins=bins)
        bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2
        
        return {
            'counts': [int(c) for c in counts],
            'bin_centers': [float(bc) for bc in bin_centers],
            'bin_edges': [float(be) for be in bin_edges]
        }
    
    def _calculate_confidence_bands(self) -> Dict[str, Any]:
        """Calculate confidence bands for equity curve"""
        if not self.equity_curve or len(self.equity_curve) < 2:
            return {'error': 'Insufficient equity curve data'}
        
        # Simulate equity curves
        n_sims = 100
        equity_curves = []
        
        for _ in range(n_sims):
            shuffled_pnls = np.random.permutation(self.pnls)
            equity = self.initial_capital + np.cumsum(shuffled_pnls)
            # Interpolate to match original equity curve length
            equity_curves.append(np.interp(
                np.linspace(0, len(equity)-1, len(self.equity_curve)),
                np.arange(len(equity)),
                equity
            ))
        
        equity_curves = np.array(equity_curves)
        
        # Calculate percentile bands
        timestamps = [point['timestamp'] for point in self.equity_curve]
        actual_equity = [point['equity'] for point in self.equity_curve]
        
        return {
            'timestamps': timestamps,
            'actual_equity': actual_equity,
            'percentile_5': [float(p) for p in np.percentile(equity_curves, 5, axis=0)],
            'percentile_25': [float(p) for p in np.percentile(equity_curves, 25, axis=0)],
            'percentile_50': [float(p) for p in np.percentile(equity_curves, 50, axis=0)],
            'percentile_75': [float(p) for p in np.percentile(equity_curves, 75, axis=0)],
            'percentile_95': [float(p) for p in np.percentile(equity_curves, 95, axis=0)]
        }
    
    def _interpret_monte_carlo(self, actual_return: float, simulated_returns: List[float], 
                                percentile: float) -> str:
        """Interpret Monte Carlo results"""
        if percentile > 90:
            return (f"Excellent! Your actual return ({actual_return:.2f}%) exceeded "
                   f"{percentile:.0f}% of simulated outcomes. This suggests genuine edge, not luck.")
        elif percentile > 70:
            return (f"Good. Your result ({actual_return:.2f}%) is above average "
                   f"(top {100-percentile:.0f}%). Strategy shows promise.")
        elif percentile > 30:
            return (f"Average. Your result ({actual_return:.2f}%) is typical. "
                   f"Could be improved or might be mostly luck.")
        else:
            return (f"Below average. Your result ({actual_return:.2f}%) is in the bottom "
                   f"{percentile:.0f}%. Consider if this was a particularly unlucky sequence.")
    
    def run_bootstrap_analysis(self, n_bootstrap: int = 1000, seed: int = 42) -> Dict[str, Any]:
        """
        Bootstrap analysis - resample trades with replacement
        Validates if metrics are statistically significant
        """
        if len(self.trades) < 20:
            return {'error': 'Insufficient trades for bootstrap analysis'}
        
        np.random.seed(seed)
        
        # Metrics to bootstrap
        win_rates = []
        sharpe_ratios = []
        profit_factors = []
        expectancies = []
        
        for _ in range(n_bootstrap):
            # Resample with replacement
            sample_indices = np.random.choice(len(self.pnls), size=len(self.pnls), replace=True)
            sample_pnls = self.pnls[sample_indices]
            
            # Calculate metrics
            wins = sample_pnls[sample_pnls > 0]
            losses = sample_pnls[sample_pnls < 0]
            
            win_rate = len(wins) / len(sample_pnls) if len(sample_pnls) > 0 else 0
            win_rates.append(win_rate)
            
            sample_returns = sample_pnls / self.initial_capital
            sharpe = (np.mean(sample_returns) / np.std(sample_returns) * np.sqrt(len(sample_returns))) if np.std(sample_returns) > 0 else 0
            sharpe_ratios.append(sharpe)
            
            total_wins = np.sum(wins) if len(wins) > 0 else 0
            total_losses = abs(np.sum(losses)) if len(losses) > 0 else 1
            profit_factor = total_wins / total_losses if total_losses > 0 else 0
            profit_factors.append(profit_factor)
            
            expectancy = np.mean(sample_pnls)
            expectancies.append(expectancy)
        
        # Calculate confidence intervals
        return {
            'bootstrap_samples': n_bootstrap,
            'win_rate': {
                'mean': float(np.mean(win_rates)),
                'ci_95_lower': float(np.percentile(win_rates, 2.5)),
                'ci_95_upper': float(np.percentile(win_rates, 97.5)),
                'std_error': float(np.std(win_rates))
            },
            'sharpe_ratio': {
                'mean': float(np.mean(sharpe_ratios)),
                'ci_95_lower': float(np.percentile(sharpe_ratios, 2.5)),
                'ci_95_upper': float(np.percentile(sharpe_ratios, 97.5)),
                'std_error': float(np.std(sharpe_ratios))
            },
            'profit_factor': {
                'mean': float(np.mean(profit_factors)),
                'ci_95_lower': float(np.percentile(profit_factors, 2.5)),
                'ci_95_upper': float(np.percentile(profit_factors, 97.5)),
                'std_error': float(np.std(profit_factors))
            },
            'expectancy': {
                'mean': float(np.mean(expectancies)),
                'ci_95_lower': float(np.percentile(expectancies, 2.5)),
                'ci_95_upper': float(np.percentile(expectancies, 97.5)),
                'std_error': float(np.std(expectancies))
            },
            'interpretation': self._interpret_bootstrap(win_rates, sharpe_ratios)
        }
    
    def _interpret_bootstrap(self, win_rates: List[float], sharpe_ratios: List[float]) -> Dict[str, str]:
        """Interpret bootstrap results"""
        interpretations = {}
        
        # Win rate interpretation
        wr_ci_lower = np.percentile(win_rates, 2.5)
        if wr_ci_lower > 0.55:
            interpretations['win_rate'] = "Statistically significant edge - Win rate consistently above 55%"
        elif wr_ci_lower > 0.50:
            interpretations['win_rate'] = "Moderate edge - Win rate likely above 50%"
        else:
            interpretations['win_rate'] = "Edge uncertain - Win rate confidence interval includes 50%"
        
        # Sharpe interpretation
        sharpe_ci_lower = np.percentile(sharpe_ratios, 2.5)
        if sharpe_ci_lower > 1.0:
            interpretations['sharpe'] = "Strong statistical significance - Sharpe consistently above 1.0"
        elif sharpe_ci_lower > 0.5:
            interpretations['sharpe'] = "Moderately significant - Positive risk-adjusted returns"
        else:
            interpretations['sharpe'] = "Not statistically significant - Results could be luck"
        
        return interpretations
    
    def detect_overfitting(self) -> Dict[str, Any]:
        """
        Detect overfitting using walk-forward analysis
        Split data into train/test sets and compare performance
        """
        if len(self.trades) < 50:
            return {'error': 'Insufficient trades for overfitting detection (need 50+)'}
        
        # Time series split (respects temporal order)
        n_splits = 5
        tscv = TimeSeriesSplit(n_splits=n_splits)
        
        train_metrics = []
        test_metrics = []
        degradation_scores = []
        
        for train_idx, test_idx in tscv.split(self.pnls):
            train_pnls = self.pnls[train_idx]
            test_pnls = self.pnls[test_idx]
            
            # Calculate metrics for train and test
            train_sharpe = self._calculate_sharpe(train_pnls)
            test_sharpe = self._calculate_sharpe(test_pnls)
            
            train_win_rate = np.sum(train_pnls > 0) / len(train_pnls) if len(train_pnls) > 0 else 0
            test_win_rate = np.sum(test_pnls > 0) / len(test_pnls) if len(test_pnls) > 0 else 0
            
            train_metrics.append({
                'sharpe': train_sharpe,
                'win_rate': train_win_rate,
                'avg_pnl': float(np.mean(train_pnls))
            })
            
            test_metrics.append({
                'sharpe': test_sharpe,
                'win_rate': test_win_rate,
                'avg_pnl': float(np.mean(test_pnls))
            })
            
            # Degradation score
            degradation = 1 - (test_sharpe / train_sharpe) if train_sharpe > 0 else 1
            degradation_scores.append(degradation)
        
        # Calculate overall overfitting risk score (0-100)
        avg_degradation = np.mean(degradation_scores)
        overfitting_risk = min(100, max(0, avg_degradation * 100))
        
        # Classify risk level
        if overfitting_risk < 20:
            risk_level = "Low"
            interpretation = "Strategy generalizes well - Low overfitting risk"
        elif overfitting_risk < 40:
            risk_level = "Moderate"
            interpretation = "Some performance degradation - Monitor carefully"
        elif overfitting_risk < 60:
            risk_level = "High"
            interpretation = "Significant degradation - Likely overfit to historical data"
        else:
            risk_level = "Severe"
            interpretation = "Extreme degradation - Strategy may not work in live trading"
        
        return {
            'overfitting_risk_score': float(overfitting_risk),
            'risk_level': risk_level,
            'train_test_splits': n_splits,
            'train_performance': {
                'avg_sharpe': float(np.mean([m['sharpe'] for m in train_metrics])),
                'avg_win_rate': float(np.mean([m['win_rate'] for m in train_metrics])),
                'avg_pnl': float(np.mean([m['avg_pnl'] for m in train_metrics]))
            },
            'test_performance': {
                'avg_sharpe': float(np.mean([m['sharpe'] for m in test_metrics])),
                'avg_win_rate': float(np.mean([m['win_rate'] for m in test_metrics])),
                'avg_pnl': float(np.mean([m['avg_pnl'] for m in test_metrics]))
            },
            'performance_degradation': {
                'sharpe_degradation_pct': float((1 - np.mean([m['sharpe'] for m in test_metrics]) / np.mean([m['sharpe'] for m in train_metrics])) * 100) if np.mean([m['sharpe'] for m in train_metrics]) > 0 else 0,
                'win_rate_degradation_pct': float((1 - np.mean([m['win_rate'] for m in test_metrics]) / np.mean([m['win_rate'] for m in train_metrics])) * 100) if np.mean([m['win_rate'] for m in train_metrics]) > 0 else 0
            },
            'interpretation': interpretation
        }
    
    def _calculate_sharpe(self, pnls: np.ndarray) -> float:
        """Calculate Sharpe ratio from PnLs"""
        if len(pnls) == 0:
            return 0
        returns = pnls / self.initial_capital
        return (np.mean(returns) / np.std(returns) * np.sqrt(len(returns))) if np.std(returns) > 0 else 0
    
    def test_trade_independence(self) -> Dict[str, Any]:
        """
        Test if trades are independent (no autocorrelation)
        """
        if len(self.returns) < 30:
            return {'error': 'Insufficient trades for independence test'}
        
        # Lag-1 autocorrelation
        lag1_corr = np.corrcoef(self.returns[:-1], self.returns[1:])[0, 1]
        
        # Durbin-Watson statistic (tests for autocorrelation)
        # DW ≈ 2(1-r) where r is lag-1 autocorrelation
        # DW near 2 suggests independence, <1.5 or >2.5 suggests autocorrelation
        dw_stat = 2 * (1 - lag1_corr)
        
        is_independent = 1.5 < dw_stat < 2.5
        
        return {
            'lag1_autocorrelation': float(lag1_corr),
            'durbin_watson_statistic': float(dw_stat),
            'is_independent': bool(is_independent),
            'interpretation': (
                "Trades appear independent - Good!" if is_independent
                else "Trades show autocorrelation - Consider filtering or adjusting strategy"
            )
        }
    
    def run_hypothesis_tests(self) -> Dict[str, Any]:
        """
        Run statistical hypothesis tests on key metrics
        """
        if len(self.trades) < 20:
            return {'error': 'Insufficient trades for hypothesis testing'}
        
        tests = {}
        
        # Test 1: Is win rate significantly > 50%?
        wins = np.sum(self.pnls > 0)
        n_trades = len(self.pnls)
        win_rate = wins / n_trades
        
        # Binomial test
        p_value_wr = stats.binom_test(wins, n_trades, 0.5, alternative='greater')
        tests['win_rate_above_50'] = {
            'actual_win_rate': float(win_rate),
            'null_hypothesis': "Win rate = 50%",
            'p_value': float(p_value_wr),
            'is_significant': bool(p_value_wr < 0.05),
            'conclusion': (
                f"Win rate ({win_rate*100:.1f}%) is statistically significant (p={p_value_wr:.4f})"
                if p_value_wr < 0.05
                else f"Win rate ({win_rate*100:.1f}%) is NOT statistically different from 50% (p={p_value_wr:.4f})"
            )
        }
        
        # Test 2: Is average PnL significantly > 0?
        t_stat, p_value_pnl = stats.ttest_1samp(self.pnls, 0)
        tests['positive_expectancy'] = {
            'actual_avg_pnl': float(np.mean(self.pnls)),
            'null_hypothesis': "Average PnL = 0",
            't_statistic': float(t_stat),
            'p_value': float(p_value_pnl / 2),  # One-sided test
            'is_significant': bool((p_value_pnl / 2) < 0.05 and np.mean(self.pnls) > 0),
            'conclusion': (
                f"Positive expectancy is statistically significant (p={p_value_pnl/2:.4f})"
                if (p_value_pnl / 2) < 0.05 and np.mean(self.pnls) > 0
                else f"Positive expectancy is NOT statistically proven (p={p_value_pnl/2:.4f})"
            )
        }
        
        # Test 3: Is Sharpe ratio significantly > 0?
        sharpe = self._calculate_sharpe(self.pnls)
        # Approximation: Sharpe is significant if |Sharpe| > 1.96/sqrt(n) at 95% confidence
        sharpe_threshold = 1.96 / np.sqrt(len(self.pnls))
        tests['sharpe_significant'] = {
            'actual_sharpe': float(sharpe),
            'threshold': float(sharpe_threshold),
            'is_significant': bool(abs(sharpe) > sharpe_threshold),
            'conclusion': (
                f"Sharpe ratio ({sharpe:.2f}) is statistically significant"
                if abs(sharpe) > sharpe_threshold
                else f"Sharpe ratio ({sharpe:.2f}) is NOT statistically significant"
            )
        }
        
        return tests
    
    def analyze_luck_vs_skill(self) -> Dict[str, Any]:
        """
        Analyze probability that results are due to luck vs skill
        """
        if len(self.trades) < 10:
            return {'error': 'Insufficient trades'}
        
        # Calculate actual performance
        actual_return = np.sum(self.pnls)
        actual_sharpe = self._calculate_sharpe(self.pnls)
        win_rate = np.sum(self.pnls > 0) / len(self.pnls)
        
        # Simulate random trading (coin flip)
        n_sims = 10000
        np.random.seed(42)
        
        # Random trades with same win/loss magnitude distribution
        random_sharpes = []
        for _ in range(n_sims):
            # Randomly assign wins/losses
            random_outcomes = np.random.choice(self.pnls, size=len(self.pnls), replace=True)
            random_sharpe = self._calculate_sharpe(random_outcomes)
            random_sharpes.append(random_sharpe)
        
        # Calculate percentile of actual Sharpe in random distribution
        percentile = stats.percentileofscore(random_sharpes, actual_sharpe)
        
        # Probability results are due to luck
        prob_luck = max(0, 100 - percentile) if actual_sharpe > 0 else percentile
        prob_skill = 100 - prob_luck
        
        # Classification
        if prob_skill > 95:
            classification = "Very likely skill-based"
        elif prob_skill > 80:
            classification = "Probably skill-based"
        elif prob_skill > 60:
            classification = "Mixed - some skill, some luck"
        elif prob_skill > 40:
            classification = "Uncertain - need more data"
        else:
            classification = "Likely mostly luck"
        
        return {
            'probability_skill_pct': float(prob_skill),
            'probability_luck_pct': float(prob_luck),
            'classification': classification,
            'actual_sharpe': float(actual_sharpe),
            'random_sharpe_percentile': float(percentile),
            'interpretation': (
                f"Your results have a {prob_skill:.1f}% probability of being due to skill "
                f"rather than luck. {classification}."
            )
        }

