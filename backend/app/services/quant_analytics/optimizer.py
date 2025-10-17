"""
Strategy Optimization Service
Parameter sweeps, position sizing, and optimization algorithms
"""

import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional, Tuple
from itertools import product
import structlog

logger = structlog.get_logger()


class StrategyOptimizer:
    """Strategy optimization and parameter tuning"""
    
    def __init__(self, trades: List[Dict], config: Dict):
        """
        Initialize optimizer
        
        Args:
            trades: List of trade dictionaries
            config: Strategy configuration
        """
        self.trades = trades
        self.config = config
        self.initial_capital = config.get('initial_capital', 10000)
        
        logger.info(f"StrategyOptimizer initialized", trades=len(trades))
    
    def optimize_parameters(self, parameter_ranges: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run parameter sweep optimization
        
        Args:
            parameter_ranges: Dict of {param_name: {'min': x, 'max': y, 'step': z}}
        
        Returns:
            Optimization results with heatmap data and best parameters
        """
        try:
            # Extract parameter ranges
            params_to_optimize = []
            param_names = []
            
            for param_name, param_config in parameter_ranges.items():
                param_names.append(param_name)
                values = np.arange(
                    param_config['min'],
                    param_config['max'] + param_config['step'],
                    param_config['step']
                )
                params_to_optimize.append(values)
            
            # Generate all combinations
            param_combinations = list(product(*params_to_optimize))
            total_combinations = len(param_combinations)
            
            logger.info(f"Testing {total_combinations} parameter combinations")
            
            # Test each combination
            results = []
            for combo in param_combinations:
                param_dict = dict(zip(param_names, combo))
                metrics = self._test_parameters(param_dict)
                results.append({
                    'parameters': param_dict,
                    'metrics': metrics
                })
            
            # Find best by Sharpe ratio
            best_result = max(results, key=lambda x: x['metrics'].get('sharpe_ratio', -999))
            
            # Create heatmap data (for 2-parameter optimization)
            heatmap_data = None
            if len(param_names) == 2:
                heatmap_data = self._create_heatmap(results, param_names, params_to_optimize)
            
            # Top 10 results
            top_10 = sorted(results, key=lambda x: x['metrics'].get('sharpe_ratio', -999), reverse=True)[:10]
            
            return {
                'total_combinations_tested': total_combinations,
                'best_parameters': best_result['parameters'],
                'best_metrics': best_result['metrics'],
                'top_10_configurations': [
                    {
                        'parameters': r['parameters'],
                        'sharpe_ratio': r['metrics'].get('sharpe_ratio', 0),
                        'total_return_pct': r['metrics'].get('total_return_pct', 0),
                        'max_drawdown_pct': r['metrics'].get('max_drawdown_pct', 0),
                        'win_rate_pct': r['metrics'].get('win_rate_pct', 0)
                    }
                    for r in top_10
                ],
                'heatmap_data': heatmap_data,
                'improvement_vs_original': self._calculate_improvement(best_result['metrics'])
            }
        
        except Exception as e:
            logger.error(f"Parameter optimization failed: {e}", exc_info=True)
            raise
    
    def _test_parameters(self, params: Dict[str, float]) -> Dict[str, float]:
        """
        Test a specific parameter combination by adjusting existing trades
        
        This simulates what would have happened with different parameters
        """
        # Apply parameters to trades
        adjusted_trades = []
        
        for trade in self.trades:
            adjusted_pnl = trade['pnl']
            
            # Apply stop loss if specified
            if 'stop_loss_pct' in params and params['stop_loss_pct'] > 0:
                max_loss = -trade['entry_price'] * trade['quantity'] * (params['stop_loss_pct'] / 100)
                if adjusted_pnl < max_loss:
                    adjusted_pnl = max_loss
            
            # Apply take profit if specified
            if 'take_profit_pct' in params and params['take_profit_pct'] > 0:
                max_gain = trade['entry_price'] * trade['quantity'] * (params['take_profit_pct'] / 100)
                if adjusted_pnl > max_gain:
                    adjusted_pnl = max_gain
            
            # Apply position size multiplier
            if 'position_size_pct' in params:
                adjusted_pnl *= (params['position_size_pct'] / 100)
            
            # Apply leverage
            if 'leverage' in params:
                adjusted_pnl *= params['leverage']
            
            # Filter by holding time
            if 'min_holding_hours' in params:
                if trade.get('holding_time_hours', 0) < params['min_holding_hours']:
                    continue  # Skip this trade
            
            if 'max_holding_hours' in params:
                if trade.get('holding_time_hours', 999) > params['max_holding_hours']:
                    continue  # Skip this trade
            
            adjusted_trades.append(adjusted_pnl)
        
        # Calculate metrics
        if len(adjusted_trades) == 0:
            return {
                'sharpe_ratio': -999,
                'total_return_pct': -100,
                'max_drawdown_pct': 100,
                'win_rate_pct': 0,
                'profit_factor': 0,
                'total_trades': 0
            }
        
        adjusted_pnls = np.array(adjusted_trades)
        returns = adjusted_pnls / self.initial_capital
        
        # Sharpe ratio
        sharpe = (np.mean(returns) / np.std(returns) * np.sqrt(len(returns))) if np.std(returns) > 0 else 0
        
        # Total return
        total_return = np.sum(adjusted_pnls)
        total_return_pct = (total_return / self.initial_capital) * 100
        
        # Max drawdown
        equity = self.initial_capital + np.cumsum(adjusted_pnls)
        running_max = np.maximum.accumulate(equity)
        drawdown = (equity - running_max) / running_max * 100
        max_drawdown = np.min(drawdown)
        
        # Win rate
        wins = adjusted_pnls[adjusted_pnls > 0]
        losses = adjusted_pnls[adjusted_pnls < 0]
        win_rate = len(wins) / len(adjusted_pnls) if len(adjusted_pnls) > 0 else 0
        
        # Profit factor
        total_wins = np.sum(wins) if len(wins) > 0 else 0
        total_losses = abs(np.sum(losses)) if len(losses) > 0 else 1
        profit_factor = total_wins / total_losses if total_losses > 0 else 0
        
        return {
            'sharpe_ratio': float(sharpe),
            'total_return_pct': float(total_return_pct),
            'max_drawdown_pct': float(max_drawdown),
            'win_rate_pct': float(win_rate * 100),
            'profit_factor': float(profit_factor),
            'total_trades': len(adjusted_trades)
        }
    
    def _create_heatmap(self, results: List[Dict], param_names: List[str], 
                        param_values: List[np.ndarray]) -> Dict[str, Any]:
        """Create heatmap data for 2-parameter optimization"""
        param1_name, param2_name = param_names
        param1_values = param_values[0]
        param2_values = param_values[1]
        
        # Create 2D grid of Sharpe ratios
        sharpe_grid = np.zeros((len(param2_values), len(param1_values)))
        
        for result in results:
            p1 = result['parameters'][param1_name]
            p2 = result['parameters'][param2_name]
            
            i = np.where(param1_values == p1)[0][0]
            j = np.where(param2_values == p2)[0][0]
            
            sharpe_grid[j, i] = result['metrics'].get('sharpe_ratio', 0)
        
        return {
            'x_param': param1_name,
            'y_param': param2_name,
            'x_values': [float(v) for v in param1_values],
            'y_values': [float(v) for v in param2_values],
            'sharpe_values': sharpe_grid.tolist(),
            'colorscale': 'RdYlGn'  # Red-Yellow-Green
        }
    
    def _calculate_improvement(self, optimized_metrics: Dict[str, float]) -> Dict[str, Any]:
        """Calculate improvement vs original strategy"""
        # Calculate original metrics
        original_pnls = np.array([t['pnl'] for t in self.trades])
        original_returns = original_pnls / self.initial_capital
        original_sharpe = (np.mean(original_returns) / np.std(original_returns) * np.sqrt(len(original_returns))) if np.std(original_returns) > 0 else 0
        
        original_equity = self.initial_capital + np.cumsum(original_pnls)
        original_running_max = np.maximum.accumulate(original_equity)
        original_drawdown = (original_equity - original_running_max) / original_running_max * 100
        original_max_dd = np.min(original_drawdown)
        
        original_return_pct = (np.sum(original_pnls) / self.initial_capital) * 100
        
        # Calculate improvements
        sharpe_improvement = ((optimized_metrics['sharpe_ratio'] - original_sharpe) / abs(original_sharpe) * 100) if original_sharpe != 0 else 0
        return_improvement = optimized_metrics['total_return_pct'] - original_return_pct
        dd_improvement = optimized_metrics['max_drawdown_pct'] - original_max_dd  # Negative is better
        
        return {
            'original_sharpe': float(original_sharpe),
            'optimized_sharpe': float(optimized_metrics['sharpe_ratio']),
            'sharpe_improvement_pct': float(sharpe_improvement),
            'original_return_pct': float(original_return_pct),
            'optimized_return_pct': float(optimized_metrics['total_return_pct']),
            'return_improvement_pct': float(return_improvement),
            'original_max_dd_pct': float(original_max_dd),
            'optimized_max_dd_pct': float(optimized_metrics['max_drawdown_pct']),
            'dd_improvement_pct': float(dd_improvement)
        }
    
    def calculate_kelly_criterion(self) -> Dict[str, Any]:
        """
        Calculate Kelly Criterion for optimal position sizing
        
        Kelly % = (Win Rate * Avg Win - Loss Rate * Avg Loss) / Avg Win
        """
        if len(self.trades) == 0:
            return {'error': 'No trades to analyze'}
        
        pnls = np.array([t['pnl'] for t in self.trades])
        wins = pnls[pnls > 0]
        losses = pnls[pnls < 0]
        
        if len(wins) == 0 or len(losses) == 0:
            return {'error': 'Need both winning and losing trades'}
        
        win_rate = len(wins) / len(pnls)
        loss_rate = 1 - win_rate
        avg_win = np.mean(wins)
        avg_loss = abs(np.mean(losses))
        
        # Kelly formula
        kelly_pct = (win_rate * avg_win - loss_rate * avg_loss) / avg_win
        
        # Recommended Kelly (use half Kelly for safety)
        safe_kelly_pct = kelly_pct * 0.5
        
        # Practical interpretation
        if kelly_pct <= 0:
            recommendation = "Negative Kelly - Strategy has negative expectancy, don't trade it"
        elif kelly_pct > 1:
            recommendation = "Kelly > 100% - Very strong edge, but use max 25% position size for safety"
        elif kelly_pct > 0.5:
            recommendation = f"Use {safe_kelly_pct*100:.1f}% position size (half Kelly for safety)"
        else:
            recommendation = f"Use {kelly_pct*100:.1f}% position size"
        
        return {
            'kelly_percentage': float(kelly_pct * 100),
            'safe_kelly_percentage': float(safe_kelly_pct * 100),
            'win_rate': float(win_rate),
            'avg_win': float(avg_win),
            'avg_loss': float(avg_loss),
            'recommendation': recommendation,
            'interpretation': (
                f"Kelly Criterion suggests risking {kelly_pct*100:.1f}% of capital per trade. "
                f"For safety, use half Kelly ({safe_kelly_pct*100:.1f}%) to reduce risk of ruin."
            )
        }
    
    def compare_position_sizing_methods(self) -> Dict[str, Any]:
        """
        Compare different position sizing methods
        """
        if len(self.trades) == 0:
            return {'error': 'No trades to analyze'}
        
        methods = {}
        
        # Method 1: Fixed dollar amount (current)
        current_pnls = np.array([t['pnl'] for t in self.trades])
        methods['current'] = self._calculate_method_metrics(current_pnls, 'Current Strategy')
        
        # Method 2: Fixed percentage (2% risk per trade)
        fixed_pct_pnls = current_pnls * 0.02 / (np.mean(np.abs(current_pnls)) / self.initial_capital)
        methods['fixed_2pct'] = self._calculate_method_metrics(fixed_pct_pnls, 'Fixed 2% Risk')
        
        # Method 3: Kelly Criterion
        kelly_result = self.calculate_kelly_criterion()
        if 'kelly_percentage' in kelly_result:
            kelly_multiplier = kelly_result['safe_kelly_percentage'] / 100
            kelly_pnls = current_pnls * kelly_multiplier
            methods['kelly'] = self._calculate_method_metrics(kelly_pnls, 'Kelly Criterion')
        
        # Method 4: Anti-Martingale (increase size after wins)
        anti_martingale_pnls = []
        multiplier = 1.0
        for pnl in current_pnls:
            anti_martingale_pnls.append(pnl * multiplier)
            if pnl > 0:
                multiplier = min(multiplier * 1.5, 3.0)  # Increase up to 3x
            else:
                multiplier = 1.0  # Reset after loss
        methods['anti_martingale'] = self._calculate_method_metrics(
            np.array(anti_martingale_pnls), 'Anti-Martingale'
        )
        
        # Rank by Sharpe ratio
        ranked = sorted(methods.items(), key=lambda x: x[1]['sharpe_ratio'], reverse=True)
        
        return {
            'methods': methods,
            'best_method': ranked[0][0],
            'ranking': [{'method': k, 'sharpe': v['sharpe_ratio']} for k, v in ranked]
        }
    
    def _calculate_method_metrics(self, pnls: np.ndarray, method_name: str) -> Dict[str, Any]:
        """Calculate metrics for a position sizing method"""
        returns = pnls / self.initial_capital
        sharpe = (np.mean(returns) / np.std(returns) * np.sqrt(len(returns))) if np.std(returns) > 0 else 0
        
        total_return = np.sum(pnls)
        total_return_pct = (total_return / self.initial_capital) * 100
        
        equity = self.initial_capital + np.cumsum(pnls)
        running_max = np.maximum.accumulate(equity)
        drawdown = (equity - running_max) / running_max * 100
        max_drawdown = np.min(drawdown)
        
        return {
            'method_name': method_name,
            'sharpe_ratio': float(sharpe),
            'total_return_pct': float(total_return_pct),
            'max_drawdown_pct': float(max_drawdown),
            'final_equity': float(equity[-1]) if len(equity) > 0 else self.initial_capital
        }

