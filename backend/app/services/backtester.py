"""
Backtesting engine with strategy implementations
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import structlog
import asyncio

from app.services.market_data import MarketDataService

logger = structlog.get_logger()

class BacktestEngine:
    """Main backtesting engine"""
    
    def __init__(self):
        self.market_service = MarketDataService()
    
    async def run_backtest(
        self,
        symbol: str,
        timeframe: str,
        lookback_bars: int,
        strategy: Dict[str, Any],
        fees_bps: float = 5.0,
        slippage_bps: float = 2.0
    ) -> Dict[str, Any]:
        """Run a complete backtest"""
        
        # Get market data
        candles = await self.market_service.get_ohlcv(symbol, timeframe, lookback_bars)
        
        if len(candles) < 50:
            raise ValueError("Insufficient data for backtesting")
        
        # Convert to DataFrame
        df = pd.DataFrame(candles)
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df.set_index('timestamp', inplace=True)
        
        # Run strategy
        strategy_type = strategy.get("type")
        
        if strategy_type == "sma_cross":
            trades = self._run_sma_cross_strategy(df, strategy)
        elif strategy_type == "rsi_revert":
            trades = self._run_rsi_revert_strategy(df, strategy)
        elif strategy_type == "atr_trail":
            trades = self._run_atr_trail_strategy(df, strategy)
        else:
            raise ValueError(f"Unknown strategy type: {strategy_type}")
        
        # Apply fees and slippage
        trades = self._apply_costs(trades, fees_bps, slippage_bps)
        
        # Calculate metrics
        metrics = self._calculate_metrics(trades, df)
        
        # Generate equity curve
        equity_curve = self._generate_equity_curve(trades)
        
        # Run Monte Carlo simulation
        mc_summary = self._run_monte_carlo(trades)
        
        return {
            "metrics": metrics,
            "equity_curve": equity_curve,
            "trades": trades,
            "mc_summary": mc_summary
        }
    
    def _run_sma_cross_strategy(self, df: pd.DataFrame, strategy: Dict[str, Any]) -> List[Dict[str, Any]]:
        """SMA Crossover strategy"""
        
        fast_period = strategy.get("fast_period", 10)
        slow_period = strategy.get("slow_period", 20)
        position_size = strategy.get("position_size", 1.0)
        
        # Calculate SMAs
        df['sma_fast'] = df['close'].rolling(window=fast_period).mean()
        df['sma_slow'] = df['close'].rolling(window=slow_period).mean()
        
        # Generate signals
        df['signal'] = 0
        df.loc[df['sma_fast'] > df['sma_slow'], 'signal'] = 1  # Buy
        df.loc[df['sma_fast'] < df['sma_slow'], 'signal'] = -1  # Sell
        
        # Generate trades
        trades = []
        position = 0
        
        for i in range(1, len(df)):
            current_signal = df.iloc[i]['signal']
            prev_signal = df.iloc[i-1]['signal']
            
            if current_signal != prev_signal and current_signal != 0:
                price = df.iloc[i]['close']
                
                if current_signal == 1 and position <= 0:  # Buy signal
                    trades.append({
                        "timestamp": df.index[i],
                        "side": "buy",
                        "price": price,
                        "qty": position_size,
                        "pnl": 0
                    })
                    position = position_size
                    
                elif current_signal == -1 and position >= 0:  # Sell signal
                    trades.append({
                        "timestamp": df.index[i],
                        "side": "sell",
                        "price": price,
                        "qty": position_size,
                        "pnl": 0
                    })
                    position = -position_size
        
        return trades
    
    def _run_rsi_revert_strategy(self, df: pd.DataFrame, strategy: Dict[str, Any]) -> List[Dict[str, Any]]:
        """RSI Mean Reversion strategy"""
        
        rsi_period = strategy.get("rsi_period", 14)
        oversold = strategy.get("oversold", 30)
        overbought = strategy.get("overbought", 70)
        position_size = strategy.get("position_size", 1.0)
        
        # Calculate RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=rsi_period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=rsi_period).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))
        
        # Generate signals
        df['signal'] = 0
        df.loc[df['rsi'] < oversold, 'signal'] = 1  # Buy
        df.loc[df['rsi'] > overbought, 'signal'] = -1  # Sell
        
        # Generate trades
        trades = []
        position = 0
        
        for i in range(1, len(df)):
            current_signal = df.iloc[i]['signal']
            prev_signal = df.iloc[i-1]['signal']
            
            if current_signal != prev_signal and current_signal != 0:
                price = df.iloc[i]['close']
                
                if current_signal == 1 and position <= 0:  # Buy signal
                    trades.append({
                        "timestamp": df.index[i],
                        "side": "buy",
                        "price": price,
                        "qty": position_size,
                        "pnl": 0
                    })
                    position = position_size
                    
                elif current_signal == -1 and position >= 0:  # Sell signal
                    trades.append({
                        "timestamp": df.index[i],
                        "side": "sell",
                        "price": price,
                        "qty": position_size,
                        "pnl": 0
                    })
                    position = -position_size
        
        return trades
    
    def _run_atr_trail_strategy(self, df: pd.DataFrame, strategy: Dict[str, Any]) -> List[Dict[str, Any]]:
        """ATR Trailing Stop strategy"""
        
        atr_period = strategy.get("atr_period", 14)
        atr_multiplier = strategy.get("atr_multiplier", 2.0)
        position_size = strategy.get("position_size", 1.0)
        
        # Calculate ATR
        high_low = df['high'] - df['low']
        high_close = np.abs(df['high'] - df['close'].shift())
        low_close = np.abs(df['low'] - df['close'].shift())
        
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = np.max(ranges, axis=1)
        df['atr'] = true_range.rolling(window=atr_period).mean()
        
        # Generate trades (simplified - just buy and hold with trailing stop)
        trades = []
        position = 0
        entry_price = 0
        stop_price = 0
        
        for i in range(atr_period, len(df)):
            price = df.iloc[i]['close']
            atr = df.iloc[i]['atr']
            
            if position == 0:  # No position
                # Buy on first bar after ATR calculation
                if i == atr_period:
                    trades.append({
                        "timestamp": df.index[i],
                        "side": "buy",
                        "price": price,
                        "qty": position_size,
                        "pnl": 0
                    })
                    position = position_size
                    entry_price = price
                    stop_price = price - (atr * atr_multiplier)
            
            elif position > 0:  # Long position
                # Update trailing stop
                new_stop = price - (atr * atr_multiplier)
                if new_stop > stop_price:
                    stop_price = new_stop
                
                # Check if stop hit
                if price <= stop_price:
                    trades.append({
                        "timestamp": df.index[i],
                        "side": "sell",
                        "price": price,
                        "qty": position_size,
                        "pnl": 0
                    })
                    position = 0
        
        return trades
    
    def _apply_costs(self, trades: List[Dict[str, Any]], fees_bps: float, slippage_bps: float) -> List[Dict[str, Any]]:
        """Apply fees and slippage to trades"""
        
        for trade in trades:
            price = trade['price']
            qty = trade['qty']
            
            # Apply slippage
            if trade['side'] == 'buy':
                slippage = price * (slippage_bps / 10000)
                trade['price'] = price + slippage
            else:
                slippage = price * (slippage_bps / 10000)
                trade['price'] = price - slippage
            
            # Calculate fees
            trade['fees'] = price * qty * (fees_bps / 10000)
        
        return trades
    
    def _calculate_metrics(self, trades: List[Dict[str, Any]], df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate backtest metrics"""
        
        if not trades:
            return {
                "total_return": 0,
                "sharpe_ratio": 0,
                "max_drawdown": 0,
                "win_rate": 0,
                "total_trades": 0,
                "avg_trade": 0
            }
        
        # Calculate PnL for each trade pair
        trade_pairs = []
        for i in range(0, len(trades), 2):
            if i + 1 < len(trades):
                buy_trade = trades[i]
                sell_trade = trades[i + 1]
                
                if buy_trade['side'] == 'buy' and sell_trade['side'] == 'sell':
                    pnl = (sell_trade['price'] - buy_trade['price']) * buy_trade['qty']
                    pnl -= buy_trade['fees'] + sell_trade['fees']
                    trade_pairs.append(pnl)
        
        if not trade_pairs:
            return {
                "total_return": 0,
                "sharpe_ratio": 0,
                "max_drawdown": 0,
                "win_rate": 0,
                "total_trades": 0,
                "avg_trade": 0
            }
        
        # Calculate metrics
        total_return = sum(trade_pairs)
        win_rate = len([p for p in trade_pairs if p > 0]) / len(trade_pairs)
        avg_trade = np.mean(trade_pairs)
        
        # Calculate Sharpe ratio (simplified)
        if len(trade_pairs) > 1:
            sharpe_ratio = np.mean(trade_pairs) / np.std(trade_pairs) if np.std(trade_pairs) > 0 else 0
        else:
            sharpe_ratio = 0
        
        # Calculate max drawdown
        cumulative_returns = np.cumsum(trade_pairs)
        running_max = np.maximum.accumulate(cumulative_returns)
        drawdowns = running_max - cumulative_returns
        max_drawdown = np.max(drawdowns) if len(drawdowns) > 0 else 0
        
        return {
            "total_return": float(total_return),
            "sharpe_ratio": float(sharpe_ratio),
            "max_drawdown": float(max_drawdown),
            "win_rate": float(win_rate),
            "total_trades": len(trade_pairs),
            "avg_trade": float(avg_trade)
        }
    
    def _generate_equity_curve(self, trades: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate equity curve data"""
        
        equity_curve = []
        cumulative_pnl = 0
        
        for trade in trades:
            # This is simplified - in reality you'd calculate PnL properly
            cumulative_pnl += trade.get('pnl', 0)
            
            equity_curve.append({
                "timestamp": trade['timestamp'].isoformat() if hasattr(trade['timestamp'], 'isoformat') else str(trade['timestamp']),
                "equity": cumulative_pnl,
                "trade_type": trade['side']
            })
        
        return equity_curve
    
    def _run_monte_carlo(self, trades: List[Dict[str, Any]], n_runs: int = 10000) -> Dict[str, Any]:
        """Run Monte Carlo simulation"""
        
        # Extract trade returns (simplified)
        trade_returns = [trade.get('pnl', 0) for trade in trades]
        
        if not trade_returns:
            return {
                "median_return": 0,
                "p05_return": 0,
                "p95_return": 0,
                "n_runs": n_runs
            }
        
        # Run Monte Carlo simulation
        mc_results = []
        for _ in range(n_runs):
            # Randomly sample trades with replacement
            sample_returns = np.random.choice(trade_returns, size=len(trade_returns), replace=True)
            total_return = np.sum(sample_returns)
            mc_results.append(total_return)
        
        # Calculate percentiles
        mc_results = np.array(mc_results)
        
        return {
            "median_return": float(np.median(mc_results)),
            "p05_return": float(np.percentile(mc_results, 5)),
            "p95_return": float(np.percentile(mc_results, 95)),
            "n_runs": n_runs
        }
