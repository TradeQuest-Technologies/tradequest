"""
AI Coach service for trade analysis
"""

from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import structlog
import numpy as np

from app.models.trade import Trade
from app.services.market_data import MarketDataService

logger = structlog.get_logger()

class AICoach:
    """AI Coach for trade analysis and coaching"""
    
    def __init__(self):
        self.market_service = MarketDataService()
    
    async def analyze_trade(self, trade: Trade, db) -> Dict[str, Any]:
        """Analyze a single trade and provide coaching"""
        
        try:
            # Get market context around the trade
            context = await self._get_trade_context(trade)
            
            # Analyze the trade
            analysis = self._analyze_trade_execution(trade, context)
            
            # Generate coaching summary
            summary = self._generate_summary(trade, analysis)
            action_item = self._generate_action_item(trade, analysis)
            
            return {
                "summary": summary,
                "action_item": action_item,
                "context": context,
                "analysis": analysis
            }
            
        except Exception as e:
            logger.error("Trade analysis failed", trade_id=str(trade.id), error=str(e))
            return {
                "summary": "Unable to analyze this trade due to data limitations.",
                "action_item": "Ensure you have sufficient market data and trade context.",
                "context": {},
                "analysis": {}
            }
    
    async def analyze_session(self, trades: List[Trade], db) -> Dict[str, Any]:
        """Analyze a trading session"""
        
        if not trades:
            return {
                "summary": "No trades to analyze.",
                "action_item": "Review your trading plan and market conditions.",
                "metrics": {}
            }
        
        try:
            # Calculate session metrics
            metrics = self._calculate_session_metrics(trades)
            
            # Analyze patterns
            patterns = self._analyze_session_patterns(trades)
            
            # Generate coaching
            summary = self._generate_session_summary(metrics, patterns)
            action_item = self._generate_session_action_item(metrics, patterns)
            
            return {
                "summary": summary,
                "action_item": action_item,
                "metrics": metrics,
                "patterns": patterns
            }
            
        except Exception as e:
            logger.error("Session analysis failed", error=str(e))
            return {
                "summary": "Unable to analyze this trading session.",
                "action_item": "Review your trades manually and consider your risk management.",
                "metrics": {},
                "patterns": {}
            }
    
    async def _get_trade_context(self, trade: Trade) -> Dict[str, Any]:
        """Get market context around a trade"""
        
        try:
            # Get candles around the trade
            start_time = trade.filled_at - timedelta(minutes=60)
            end_time = trade.filled_at + timedelta(minutes=60)
            
            candles = await self.market_service.get_ohlcv_range(
                trade.symbol, "1m", start_time, end_time
            )
            
            if not candles:
                return {}
            
            # Find the trade candle
            trade_timestamp = int(trade.filled_at.timestamp() * 1000)
            trade_candle = None
            
            for candle in candles:
                if abs(candle["timestamp"] - trade_timestamp) < 60000:  # Within 1 minute
                    trade_candle = candle
                    break
            
            if not trade_candle:
                return {"candles": candles}
            
            # Calculate some basic indicators
            context = {
                "candles": candles,
                "trade_candle": trade_candle,
                "price_vs_high": trade.avg_price / trade_candle["high"] if trade_candle["high"] > 0 else 1,
                "price_vs_low": trade.avg_price / trade_candle["low"] if trade_candle["low"] > 0 else 1,
                "volume": trade_candle["volume"]
            }
            
            return context
            
        except Exception as e:
            logger.warning("Failed to get trade context", error=str(e))
            return {}
    
    def _analyze_trade_execution(self, trade: Trade, context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze trade execution quality"""
        
        analysis = {
            "execution_quality": "unknown",
            "timing": "unknown",
            "size": "unknown",
            "risk": "unknown"
        }
        
        if not context or "trade_candle" not in context:
            return analysis
        
        trade_candle = context["trade_candle"]
        
        # Analyze execution quality
        if trade.side == "buy":
            if trade.avg_price <= trade_candle["low"] * 1.01:  # Within 1% of low
                analysis["execution_quality"] = "excellent"
            elif trade.avg_price <= trade_candle["close"]:
                analysis["execution_quality"] = "good"
            else:
                analysis["execution_quality"] = "poor"
        else:  # sell
            if trade.avg_price >= trade_candle["high"] * 0.99:  # Within 1% of high
                analysis["execution_quality"] = "excellent"
            elif trade.avg_price >= trade_candle["close"]:
                analysis["execution_quality"] = "good"
            else:
                analysis["execution_quality"] = "poor"
        
        # Analyze timing
        candle_range = trade_candle["high"] - trade_candle["low"]
        if candle_range > 0:
            if trade.side == "buy":
                position_in_range = (trade.avg_price - trade_candle["low"]) / candle_range
            else:
                position_in_range = (trade_candle["high"] - trade.avg_price) / candle_range
            
            if position_in_range < 0.2:
                analysis["timing"] = "excellent"
            elif position_in_range < 0.5:
                analysis["timing"] = "good"
            else:
                analysis["timing"] = "poor"
        
        return analysis
    
    def _generate_summary(self, trade: Trade, analysis: Dict[str, Any]) -> str:
        """Generate coaching summary"""
        
        execution_quality = analysis.get("execution_quality", "unknown")
        timing = analysis.get("timing", "unknown")
        
        summary_parts = []
        
        # Execution quality
        if execution_quality == "excellent":
            summary_parts.append("Excellent execution - you got a great price.")
        elif execution_quality == "good":
            summary_parts.append("Good execution with reasonable pricing.")
        elif execution_quality == "poor":
            summary_parts.append("Poor execution - consider improving your entry timing.")
        
        # Timing
        if timing == "excellent":
            summary_parts.append("Perfect timing within the candle range.")
        elif timing == "good":
            summary_parts.append("Decent timing, but room for improvement.")
        elif timing == "poor":
            summary_parts.append("Poor timing - you're buying/selling at the wrong end of the range.")
        
        # PnL context
        if trade.pnl > 0:
            summary_parts.append(f"Profitable trade with ${trade.pnl:.2f} gain.")
        elif trade.pnl < 0:
            summary_parts.append(f"Losing trade with ${abs(trade.pnl):2f} loss.")
        
        return " ".join(summary_parts) if summary_parts else "Trade executed successfully."
    
    def _generate_action_item(self, trade: Trade, analysis: Dict[str, Any]) -> str:
        """Generate actionable advice"""
        
        execution_quality = analysis.get("execution_quality", "unknown")
        timing = analysis.get("timing", "unknown")
        
        if execution_quality == "poor" or timing == "poor":
            return "Focus on improving your entry timing. Wait for better prices within the candle range."
        elif execution_quality == "good" and timing == "good":
            return "Continue your current approach - execution is solid."
        else:
            return "Review your entry strategy and consider using limit orders for better execution."
    
    def _calculate_session_metrics(self, trades: List[Trade]) -> Dict[str, Any]:
        """Calculate session metrics"""
        
        if not trades:
            return {}
        
        total_trades = len(trades)
        winning_trades = [t for t in trades if t.pnl > 0]
        losing_trades = [t for t in trades if t.pnl < 0]
        
        win_rate = len(winning_trades) / total_trades if total_trades > 0 else 0
        total_pnl = sum(t.pnl for t in trades)
        
        avg_win = np.mean([t.pnl for t in winning_trades]) if winning_trades else 0
        avg_loss = np.mean([t.pnl for t in losing_trades]) if losing_trades else 0
        
        return {
            "total_trades": total_trades,
            "win_rate": win_rate,
            "total_pnl": total_pnl,
            "avg_win": avg_win,
            "avg_loss": avg_loss,
            "profit_factor": abs(avg_win / avg_loss) if avg_loss != 0 else 0
        }
    
    def _analyze_session_patterns(self, trades: List[Trade]) -> Dict[str, Any]:
        """Analyze trading patterns"""
        
        patterns = {
            "symbols": {},
            "sides": {"buy": 0, "sell": 0},
            "time_patterns": {}
        }
        
        for trade in trades:
            # Symbol patterns
            if trade.symbol not in patterns["symbols"]:
                patterns["symbols"][trade.symbol] = {"count": 0, "pnl": 0}
            patterns["symbols"][trade.symbol]["count"] += 1
            patterns["symbols"][trade.symbol]["pnl"] += trade.pnl
            
            # Side patterns
            patterns["sides"][trade.side] += 1
            
            # Time patterns (hour of day)
            hour = trade.filled_at.hour
            if hour not in patterns["time_patterns"]:
                patterns["time_patterns"][hour] = {"count": 0, "pnl": 0}
            patterns["time_patterns"][hour]["count"] += 1
            patterns["time_patterns"][hour]["pnl"] += trade.pnl
        
        return patterns
    
    def _generate_session_summary(self, metrics: Dict[str, Any], patterns: Dict[str, Any]) -> str:
        """Generate session summary"""
        
        total_trades = metrics.get("total_trades", 0)
        win_rate = metrics.get("win_rate", 0)
        total_pnl = metrics.get("total_pnl", 0)
        
        summary_parts = []
        
        summary_parts.append(f"Traded {total_trades} times with {win_rate:.1%} win rate.")
        
        if total_pnl > 0:
            summary_parts.append(f"Profitable session with ${total_pnl:.2f} gain.")
        elif total_pnl < 0:
            summary_parts.append(f"Losing session with ${abs(total_pnl):.2f} loss.")
        else:
            summary_parts.append("Break-even session.")
        
        # Add pattern insights
        symbols = patterns.get("symbols", {})
        if len(symbols) > 1:
            best_symbol = max(symbols.items(), key=lambda x: x[1]["pnl"])
            summary_parts.append(f"Best performing symbol: {best_symbol[0]}.")
        
        return " ".join(summary_parts)
    
    def _generate_session_action_item(self, metrics: Dict[str, Any], patterns: Dict[str, Any]) -> str:
        """Generate session action item"""
        
        win_rate = metrics.get("win_rate", 0)
        profit_factor = metrics.get("profit_factor", 0)
        
        if win_rate < 0.4:
            return "Focus on improving your win rate. Review your trade selection criteria."
        elif profit_factor < 1.0:
            return "Work on risk management. Your average losses are larger than wins."
        elif win_rate > 0.6 and profit_factor > 1.5:
            return "Excellent session! Continue your current approach."
        else:
            return "Review your trading plan and consider position sizing adjustments."
