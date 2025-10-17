"""
Risk Analysis Service
Comprehensive risk metrics for backtest evaluation
"""

import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional, Tuple
from scipy import stats
from datetime import datetime, timedelta
import structlog

logger = structlog.get_logger()


class RiskAnalyzer:
    """Professional risk analysis for trading strategies"""
    
    def __init__(self, trades: List[Dict], equity_curve: List[Dict], config: Dict):
        """
        Initialize risk analyzer
        
        Args:
            trades: List of trade dictionaries with pnl, entry_time, exit_time, etc.
            equity_curve: List of equity points with timestamp, equity, drawdown_pct
            config: Strategy configuration (initial_capital, etc.)
        """
        self.trades = trades
        self.equity_curve = equity_curve
        self.config = config
        self.initial_capital = config.get('initial_capital', 10000)
        
        # Convert to numpy arrays for calculations
        self.returns = np.array([t['pnl'] / self.initial_capital for t in trades])
        self.pnls = np.array([t['pnl'] for t in trades])
        
        logger.info(f"RiskAnalyzer initialized", 
                   trades=len(trades),
                   initial_capital=self.initial_capital)
    
    def calculate_all_metrics(self) -> Dict[str, Any]:
        """Calculate all risk metrics"""
        try:
            return {
                'var_analysis': self.calculate_var(),
                'cvar_analysis': self.calculate_cvar(),
                'stress_tests': self.calculate_stress_tests(),
                'drawdown_analysis': self.calculate_drawdown_analysis(),
                'risk_metrics': self.calculate_risk_metrics(),
                'tail_risk': self.calculate_tail_risk(),
                'position_risk': self.calculate_position_risk()
            }
        except Exception as e:
            logger.error(f"Risk analysis failed: {e}", exc_info=True)
            raise
    
    def calculate_var(self, confidence_levels: List[float] = [0.95, 0.99]) -> Dict[str, Any]:
        """
        Calculate Value-at-Risk using multiple methods
        
        Returns dict with VaR at different confidence levels
        """
        if len(self.returns) == 0:
            return {'error': 'No trades to analyze'}
        
        var_results = {}
        
        for conf in confidence_levels:
            alpha = 1 - conf
            
            # Historical VaR
            historical_var = np.percentile(self.returns, alpha * 100)
            
            # Parametric VaR (assumes normal distribution)
            mean_return = np.mean(self.returns)
            std_return = np.std(self.returns)
            parametric_var = mean_return + std_return * stats.norm.ppf(alpha)
            
            # Monte Carlo VaR (simulate 10000 scenarios)
            np.random.seed(42)
            simulated_returns = np.random.normal(mean_return, std_return, 10000)
            monte_carlo_var = np.percentile(simulated_returns, alpha * 100)
            
            var_results[f'{int(conf*100)}%'] = {
                'historical': float(historical_var),
                'parametric': float(parametric_var),
                'monte_carlo': float(monte_carlo_var),
                'historical_dollar': float(historical_var * self.initial_capital),
                'interpretation': self._interpret_var(historical_var, conf)
            }
        
        return var_results
    
    def _interpret_var(self, var_value: float, confidence: float) -> str:
        """Generate human-readable VaR interpretation"""
        days_per_loss = 1 / (1 - confidence)
        return (f"With {confidence*100:.0f}% confidence, you won't lose more than "
                f"{abs(var_value)*100:.2f}% in a single trade. "
                f"Expect losses exceeding this roughly 1 in every {days_per_loss:.0f} trades.")
    
    def calculate_cvar(self, confidence_levels: List[float] = [0.95, 0.99]) -> Dict[str, Any]:
        """
        Calculate Conditional VaR (Expected Shortfall)
        CVaR is the average of all losses worse than VaR
        """
        if len(self.returns) == 0:
            return {'error': 'No trades to analyze'}
        
        cvar_results = {}
        
        for conf in confidence_levels:
            alpha = 1 - conf
            var_threshold = np.percentile(self.returns, alpha * 100)
            
            # CVaR is the mean of all returns below VaR
            tail_losses = self.returns[self.returns <= var_threshold]
            cvar = np.mean(tail_losses) if len(tail_losses) > 0 else var_threshold
            
            cvar_results[f'{int(conf*100)}%'] = {
                'cvar': float(cvar),
                'cvar_dollar': float(cvar * self.initial_capital),
                'var_threshold': float(var_threshold),
                'tail_trade_count': int(len(tail_losses)),
                'interpretation': (f"When losses exceed VaR, the average loss is "
                                 f"{abs(cvar)*100:.2f}% (${abs(cvar * self.initial_capital):.2f})")
            }
        
        return cvar_results
    
    def calculate_stress_tests(self) -> Dict[str, Any]:
        """
        Simulate market stress scenarios
        """
        scenarios = {
            'minor_crash': -0.10,  # -10% market move
            'moderate_crash': -0.20,  # -20% market move
            'severe_crash': -0.30,  # -30% market move
            'black_swan': -0.40,  # -40% market move
        }
        
        results = {}
        current_equity = self.equity_curve[-1]['equity'] if self.equity_curve else self.initial_capital
        
        for scenario_name, market_drop in scenarios.items():
            # Simple stress test: assume strategy beta of 0.5 to market
            # (strategy moves half as much as market)
            strategy_impact = market_drop * 0.5
            stressed_equity = current_equity * (1 + strategy_impact)
            loss_amount = current_equity - stressed_equity
            loss_pct = (loss_amount / current_equity) * 100
            
            results[scenario_name] = {
                'market_drop_pct': market_drop * 100,
                'estimated_strategy_impact_pct': strategy_impact * 100,
                'projected_equity': float(stressed_equity),
                'projected_loss': float(loss_amount),
                'projected_loss_pct': float(loss_pct),
                'recovery_trades_needed': self._estimate_recovery_trades(loss_amount)
            }
        
        return results
    
    def _estimate_recovery_trades(self, loss_amount: float) -> int:
        """Estimate number of trades needed to recover from loss"""
        if len(self.returns) == 0 or loss_amount <= 0:
            return 0
        
        avg_win = np.mean([p for p in self.pnls if p > 0]) if any(p > 0 for p in self.pnls) else 0
        if avg_win <= 0:
            return 999  # Can't recover
        
        return int(np.ceil(loss_amount / avg_win))
    
    def calculate_drawdown_analysis(self) -> Dict[str, Any]:
        """
        Comprehensive drawdown analysis
        """
        if not self.equity_curve or len(self.equity_curve) < 2:
            return {'error': 'Insufficient equity curve data'}
        
        # Extract equity values
        equity_values = [point['equity'] for point in self.equity_curve]
        timestamps = [point['timestamp'] for point in self.equity_curve]
        
        # Calculate drawdowns
        running_max = np.maximum.accumulate(equity_values)
        drawdowns = (np.array(equity_values) - running_max) / running_max * 100
        
        # Find all drawdown periods
        drawdown_periods = self._identify_drawdown_periods(drawdowns, timestamps)
        
        # Top 5 worst drawdowns
        top_drawdowns = sorted(drawdown_periods, key=lambda x: x['max_dd_pct'], reverse=True)[:5]
        
        # Current drawdown
        current_dd = drawdowns[-1]
        is_in_drawdown = current_dd < -0.1  # More than 0.1% drawdown
        
        # Drawdown statistics
        dd_stats = {
            'average_drawdown': float(np.mean([d for d in drawdowns if d < 0])) if any(d < 0 for d in drawdowns) else 0,
            'median_drawdown': float(np.median([d for d in drawdowns if d < 0])) if any(d < 0 for d in drawdowns) else 0,
            'drawdown_frequency': int(len(top_drawdowns)),
            'avg_recovery_time_hours': float(np.mean([dd['recovery_time_hours'] for dd in drawdown_periods if dd['recovered']])) if any(dd['recovered'] for dd in drawdown_periods) else None
        }
        
        return {
            'current_drawdown_pct': float(current_dd),
            'is_in_drawdown': bool(is_in_drawdown),
            'max_drawdown_pct': float(np.min(drawdowns)),
            'top_5_drawdowns': top_drawdowns,
            'drawdown_statistics': dd_stats,
            'drawdown_series': [float(dd) for dd in drawdowns],  # For charting
            'timestamps': timestamps
        }
    
    def _identify_drawdown_periods(self, drawdowns: np.ndarray, timestamps: List[str]) -> List[Dict]:
        """Identify distinct drawdown periods"""
        periods = []
        in_drawdown = False
        start_idx = 0
        max_dd = 0
        
        for i, dd in enumerate(drawdowns):
            if dd < -0.1 and not in_drawdown:  # Drawdown starts
                in_drawdown = True
                start_idx = i
                max_dd = dd
            elif in_drawdown:
                if dd < max_dd:
                    max_dd = dd
                if dd >= -0.05:  # Drawdown ends (recovered to within 0.05%)
                    # Parse timestamps
                    start_time = datetime.fromisoformat(timestamps[start_idx].replace('Z', '+00:00'))
                    end_time = datetime.fromisoformat(timestamps[i].replace('Z', '+00:00'))
                    duration = (end_time - start_time).total_seconds() / 3600  # hours
                    
                    periods.append({
                        'start_idx': int(start_idx),
                        'end_idx': int(i),
                        'start_time': timestamps[start_idx],
                        'end_time': timestamps[i],
                        'max_dd_pct': float(max_dd),
                        'duration_hours': float(duration),
                        'recovery_time_hours': float(duration),
                        'recovered': True
                    })
                    in_drawdown = False
        
        # Handle ongoing drawdown
        if in_drawdown:
            start_time = datetime.fromisoformat(timestamps[start_idx].replace('Z', '+00:00'))
            end_time = datetime.fromisoformat(timestamps[-1].replace('Z', '+00:00'))
            duration = (end_time - start_time).total_seconds() / 3600
            
            periods.append({
                'start_idx': int(start_idx),
                'end_idx': int(len(drawdowns) - 1),
                'start_time': timestamps[start_idx],
                'end_time': timestamps[-1],
                'max_dd_pct': float(max_dd),
                'duration_hours': float(duration),
                'recovery_time_hours': None,
                'recovered': False
            })
        
        return periods
    
    def calculate_risk_metrics(self) -> Dict[str, Any]:
        """
        Calculate comprehensive risk metrics
        """
        if len(self.returns) == 0:
            return {'error': 'No trades to analyze'}
        
        # Basic statistics
        mean_return = np.mean(self.returns)
        std_return = np.std(self.returns)
        
        # Sharpe Ratio (assuming 0% risk-free rate)
        sharpe = (mean_return / std_return * np.sqrt(len(self.returns))) if std_return > 0 else 0
        
        # Sortino Ratio (downside deviation only)
        downside_returns = self.returns[self.returns < 0]
        downside_std = np.std(downside_returns) if len(downside_returns) > 0 else std_return
        sortino = (mean_return / downside_std * np.sqrt(len(self.returns))) if downside_std > 0 else 0
        
        # Rolling volatility (20-trade window)
        if len(self.returns) >= 20:
            rolling_vol = pd.Series(self.returns).rolling(20).std().dropna()
            volatility_stats = {
                'current_volatility': float(rolling_vol.iloc[-1]) if len(rolling_vol) > 0 else float(std_return),
                'avg_volatility': float(rolling_vol.mean()),
                'max_volatility': float(rolling_vol.max()),
                'min_volatility': float(rolling_vol.min()),
                'volatility_series': [float(v) for v in rolling_vol.values]
            }
        else:
            volatility_stats = {
                'current_volatility': float(std_return),
                'avg_volatility': float(std_return),
                'note': 'Insufficient data for rolling volatility'
            }
        
        # Risk/Return ratio
        risk_return_ratio = abs(mean_return / std_return) if std_return > 0 else 0
        
        return {
            'sharpe_ratio': float(sharpe),
            'sortino_ratio': float(sortino),
            'volatility': float(std_return),
            'downside_volatility': float(downside_std),
            'risk_return_ratio': float(risk_return_ratio),
            'volatility_analysis': volatility_stats,
            'interpretation': self._interpret_risk_metrics(sharpe, sortino, std_return)
        }
    
    def _interpret_risk_metrics(self, sharpe: float, sortino: float, volatility: float) -> Dict[str, str]:
        """Interpret risk metrics for user"""
        interpretations = {}
        
        # Sharpe interpretation
        if sharpe > 2:
            interpretations['sharpe'] = "Excellent - Very strong risk-adjusted returns"
        elif sharpe > 1:
            interpretations['sharpe'] = "Good - Solid risk-adjusted performance"
        elif sharpe > 0.5:
            interpretations['sharpe'] = "Fair - Acceptable but room for improvement"
        else:
            interpretations['sharpe'] = "Poor - Returns don't justify the risk"
        
        # Sortino interpretation
        if sortino > 2:
            interpretations['sortino'] = "Excellent - Minimal downside risk"
        elif sortino > 1:
            interpretations['sortino'] = "Good - Well-controlled downside"
        else:
            interpretations['sortino'] = "Needs improvement - High downside volatility"
        
        # Volatility interpretation
        if volatility < 0.02:
            interpretations['volatility'] = "Low - Very consistent returns"
        elif volatility < 0.05:
            interpretations['volatility'] = "Moderate - Normal volatility"
        else:
            interpretations['volatility'] = "High - Large swings in performance"
        
        return interpretations
    
    def calculate_tail_risk(self) -> Dict[str, Any]:
        """
        Analyze tail risk (fat tails, extreme events)
        """
        if len(self.returns) < 30:  # Need sufficient data
            return {'error': 'Insufficient data for tail risk analysis'}
        
        # Skewness (asymmetry of distribution)
        skewness = stats.skew(self.returns)
        
        # Kurtosis (fat tails)
        kurtosis = stats.kurtosis(self.returns)
        
        # Jarque-Bera test for normality
        jb_stat, jb_pvalue = stats.jarque_bera(self.returns)
        is_normal = jb_pvalue > 0.05
        
        # Identify extreme events (>3 standard deviations)
        std = np.std(self.returns)
        mean = np.mean(self.returns)
        extreme_events = self.returns[np.abs(self.returns - mean) > 3 * std]
        
        return {
            'skewness': float(skewness),
            'skewness_interpretation': self._interpret_skewness(skewness),
            'kurtosis': float(kurtosis),
            'kurtosis_interpretation': self._interpret_kurtosis(kurtosis),
            'is_normally_distributed': bool(is_normal),
            'jarque_bera_pvalue': float(jb_pvalue),
            'extreme_events_count': int(len(extreme_events)),
            'extreme_events_pct': float(len(extreme_events) / len(self.returns) * 100),
            'largest_gain': float(np.max(self.returns)),
            'largest_loss': float(np.min(self.returns)),
            'tail_ratio': float(abs(np.min(self.returns)) / np.max(self.returns)) if np.max(self.returns) > 0 else 0
        }
    
    def _interpret_skewness(self, skewness: float) -> str:
        """Interpret skewness value"""
        if skewness > 0.5:
            return "Positive skew - More large gains than large losses (good)"
        elif skewness < -0.5:
            return "Negative skew - More large losses than large gains (concerning)"
        else:
            return "Roughly symmetric - Balanced distribution"
    
    def _interpret_kurtosis(self, kurtosis: float) -> str:
        """Interpret kurtosis value"""
        if kurtosis > 3:
            return "Fat tails - Higher risk of extreme events than normal distribution"
        elif kurtosis < -1:
            return "Thin tails - Fewer extreme events than normal"
        else:
            return "Normal tails - Standard risk profile"
    
    def calculate_position_risk(self) -> Dict[str, Any]:
        """
        Analyze position-level risk
        """
        if not self.trades:
            return {'error': 'No trades to analyze'}
        
        # Extract position sizes if available
        position_sizes = []
        for trade in self.trades:
            position_value = trade.get('quantity', 0) * trade.get('entry_price', 0)
            position_sizes.append(position_value)
        
        if not position_sizes or all(p == 0 for p in position_sizes):
            return {'note': 'Position size data not available'}
        
        # Calculate concentration metrics
        max_position = np.max(position_sizes)
        avg_position = np.mean(position_sizes)
        position_concentration = max_position / avg_position if avg_position > 0 else 1
        
        # Calculate max exposure as % of capital
        max_exposure_pct = (max_position / self.initial_capital) * 100
        avg_exposure_pct = (avg_position / self.initial_capital) * 100
        
        return {
            'max_position_size': float(max_position),
            'avg_position_size': float(avg_position),
            'max_exposure_pct': float(max_exposure_pct),
            'avg_exposure_pct': float(avg_exposure_pct),
            'position_concentration': float(position_concentration),
            'concentration_interpretation': (
                "High concentration - Large position size variation" if position_concentration > 2
                else "Moderate concentration - Consistent position sizing"
            )
        }

