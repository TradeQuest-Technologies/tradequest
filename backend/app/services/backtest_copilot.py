"""
AI Copilot for backtesting - strategy generation, diagnosis, optimization
"""

from typing import Dict, List, Any, Optional
import json
import structlog
from openai import AsyncOpenAI
from sqlalchemy.orm import Session

from app.models.backtest_v2 import StrategyGraph, BacktestRun
from app.schemas.backtest_v2 import (
    CopilotRequest, CopilotResponse, GraphChange, ExpectedImpact,
    BlockNode, BlockType
)

logger = structlog.get_logger()


class BacktestCopilot:
    """AI-powered backtesting copilot"""
    
    def __init__(self, db: Session, user_id: str):
        self.db = db
        self.user_id = user_id
        self.client = AsyncOpenAI()
    
    async def process_request(self, request: CopilotRequest) -> CopilotResponse:
        """
        Process copilot request and generate response
        
        Args:
            request: User's request with context
            
        Returns:
            Copilot response with changes and recommendations
        """
        
        try:
            # Build context
            context = await self._build_context(request)
            
            # Create system prompt
            system_prompt = self._create_system_prompt()
            
            # Create user message
            user_message = self._create_user_message(request, context)
            
            # Call OpenAI
            logger.info(f"Calling OpenAI for copilot request: {request.message[:100]}")
            
            response = await self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.7,
                response_format={"type": "json_object"}
            )
            
            # Parse response
            content = response.choices[0].message.content
            parsed = json.loads(content)
            
            # Convert to response schema
            changes = [
                GraphChange(**change) for change in parsed.get("changes", [])
            ]
            
            expected_impacts = [
                ExpectedImpact(**impact) for impact in parsed.get("expected_impacts", [])
            ]
            
            return CopilotResponse(
                message=parsed.get("message", ""),
                changes=changes,
                run_proposal=parsed.get("run_proposal"),
                expected_impacts=expected_impacts,
                suggested_next_steps=parsed.get("suggested_next_steps", [])
            )
            
        except Exception as e:
            logger.error(f"Copilot error: {e}", exc_info=True)
            return CopilotResponse(
                message=f"I encountered an error processing your request: {str(e)}",
                changes=[],
                expected_impacts=[],
                suggested_next_steps=["Try rephrasing your request"]
            )
    
    async def _build_context(self, request: CopilotRequest) -> Dict[str, Any]:
        """Build context for copilot"""
        
        context = {
            "user_id": self.user_id,
            "message": request.message
        }
        
        # Get strategy graph if provided
        if request.strategy_graph_id:
            graph = self.db.query(StrategyGraph).filter(
                StrategyGraph.id == request.strategy_graph_id
            ).first()
            
            if graph:
                context["current_graph"] = {
                    "name": graph.name,
                    "nodes": graph.nodes,
                    "edges": graph.edges,
                    "outputs": graph.outputs
                }
        
        # Get last run results if provided
        if request.last_run_id:
            run = self.db.query(BacktestRun).filter(
                BacktestRun.id == request.last_run_id
            ).first()
            
            if run and run.metrics:
                context["last_results"] = {
                    "status": run.status,
                    "metrics": run.metrics,
                    "warnings": run.warnings,
                    "total_trades": len(run.trades) if run.trades else 0
                }
        
        # Add any additional context from request
        context.update(request.context)
        
        return context
    
    def _create_system_prompt(self) -> str:
        """Create system prompt for copilot"""
        
        return """You are an expert quantitative backtesting copilot. Your role is to help users design, optimize, and diagnose trading strategies.

## Your Capabilities

1. **Strategy Design**: Create block-based strategy graphs from natural language descriptions
2. **Optimization**: Suggest parameter improvements and optimizations
3. **Diagnosis**: Analyze backtest results and identify issues (overfit, leakage, poor risk management)
4. **Walk-Forward**: Recommend validation approaches
5. **Risk Management**: Suggest stop losses, position sizing improvements
6. **ML Integration**: Help integrate machine learning models

## Available Blocks

**Data Blocks:**
- data.loader: Load OHLCV data (symbol, timeframe, start_date, end_date)
- data.resampler: Change timeframe (target_timeframe)
- data.splitter: Split train/test (split_date or split_ratio)

**Feature Blocks:**
- feature.rsi: RSI indicator (period, output_name)
- feature.macd: MACD indicator (fast_period, slow_period, signal_period)
- feature.ema: Exponential moving average (period, source, output_name)
- feature.atr: Average true range (period, output_name)
- feature.vwap: Volume weighted average price
- feature.custom: Custom formula (formula, output_name)

**Signal Blocks:**
- signal.rule: Rule-based signals (rule: "rsi<30 -> long; rsi>70 -> short")
- signal.crossover: MA crossover (fast_feature, slow_feature)
- signal.threshold: Threshold-based (feature, upper_threshold, lower_threshold)
- signal.ml: ML model predictions (model_id, threshold)

**Position Sizing:**
- sizing.fixed: Fixed size (position_size)
- sizing.kelly: Kelly criterion (win_rate, win_loss_ratio, fraction, max_position)
- sizing.vol_target: Volatility targeting (target_vol, lookback, max_position)

**Risk Management:**
- risk.stop_take: Stop loss & take profit (stop_atr_mult, take_atr_mult)
- risk.trailing: Trailing stop (trail_atr_mult)
- risk.time_stop: Time-based exit (max_bars)

**Execution:**
- exec.market: Market orders (slippage_bps, fee_bps, slippage_model)
- exec.limit: Limit orders (limit_offset_bps, fee_bps, fill_probability)

## Response Format

You MUST respond with valid JSON in this exact format:

```json
{
  "message": "Human-readable explanation of what you're proposing",
  "changes": [
    {
      "op": "add|update|remove",
      "target": "node_id or graph.property",
      "payload": {
        // Node data for add/update, or null for remove
      }
    }
  ],
  "run_proposal": {
    "baseline": true,
    "scenarios": [
      {"name": "stress_test", "fee_mult": 2.0, "latency_ms": 30}
    ]
  },
  "expected_impacts": [
    {
      "metric": "sharpe|dd|cagr|win_rate",
      "delta": "+0.2 or -5%",
      "confidence": 0.7
    }
  ],
  "suggested_next_steps": [
    "Run walk-forward validation with 6 folds",
    "Add volatility targeting for better risk management"
  ]
}
```

## Guidelines

1. **TL;DR First**: Start message with clear, actionable summary
2. **Evidence-Based**: Base recommendations on metrics when available
3. **Reproducible**: Use seeds, versioning, and deterministic approaches
4. **Conservative**: Warn about overfitting, leakage, low sample sizes
5. **Practical**: Suggest realistic improvements with expected impact ranges

## Example Interactions

User: "Build a mean-reversion strategy on BTC/USDT 1m using RSI"

Response:
```json
{
  "message": "I'll create a mean-reversion strategy using RSI. The strategy will buy when RSI drops below 30 (oversold) and sell when it rises above 70 (overbought). I'm including ATR-based stops and volatility targeting for risk management.",
  "changes": [
    {"op": "add", "target": "data1", "payload": {"id": "data1", "type": "data.loader", "params": {"symbol": "BTC/USDT", "timeframe": "1m"}, "inputs": []}},
    {"op": "add", "target": "rsi1", "payload": {"id": "rsi1", "type": "feature.rsi", "params": {"period": 14}, "inputs": ["data1"]}},
    {"op": "add", "target": "atr1", "payload": {"id": "atr1", "type": "feature.atr", "params": {"period": 14}, "inputs": ["data1"]}},
    {"op": "add", "target": "sig1", "payload": {"id": "sig1", "type": "signal.threshold", "params": {"feature": "rsi", "upper_threshold": 70, "lower_threshold": 30}, "inputs": ["rsi1"]}},
    {"op": "add", "target": "size1", "payload": {"id": "size1", "type": "sizing.vol_target", "params": {"target_vol": 0.15}, "inputs": ["sig1"]}},
    {"op": "add", "target": "risk1", "payload": {"id": "risk1", "type": "risk.stop_take", "params": {"stop_atr_mult": 2.0, "take_atr_mult": 3.0}, "inputs": ["size1", "atr1"]}},
    {"op": "add", "target": "exec1", "payload": {"id": "exec1", "type": "exec.market", "params": {"slippage_bps": 5, "fee_bps": 2}, "inputs": ["risk1"]}}
  ],
  "run_proposal": {"baseline": true},
  "expected_impacts": [
    {"metric": "sharpe", "delta": "+1.2 to +1.8", "confidence": 0.6},
    {"metric": "max_dd", "delta": "-12% to -18%", "confidence": 0.7}
  ],
  "suggested_next_steps": [
    "Run on 90 days of data to verify behavior",
    "Test with walk-forward validation (6 folds)",
    "Consider adding MACD confirmation for higher conviction signals"
  ]
}
```

User: "Why is my Sharpe ratio so low? Last run got 0.4"

Response (when last_results available):
```json
{
  "message": "Your Sharpe of 0.4 is low. I see 3 main issues: 1) High turnover (45 trades/day) burning fees/slippage, 2) Win rate of 48% with profit factor 1.1 suggests no real edge, 3) No position sizing or risk management. Let's fix these.",
  "changes": [
    {"op": "add", "target": "size1", "payload": {"id": "size1", "type": "sizing.vol_target", "params": {"target_vol": 0.15}, "inputs": ["sig1"]}},
    {"op": "add", "target": "risk1", "payload": {"id": "risk1", "type": "risk.stop_take", "params": {"stop_atr_mult": 2.0, "take_atr_mult": 3.0}, "inputs": ["size1"]}}
  ],
  "expected_impacts": [
    {"metric": "sharpe", "delta": "+0.3 to +0.5", "confidence": 0.65},
    {"metric": "turnover", "delta": "-30%", "confidence": 0.8}
  ],
  "suggested_next_steps": [
    "Add signal filters to reduce false entries (e.g., MACD confirmation)",
    "Increase signal threshold to trade less frequently but with higher conviction",
    "Run walk-forward to verify robustness"
  ]
}
```

Remember: You are helping traders make money. Be precise, actionable, and honest about uncertainty."""
    
    def _create_user_message(self, request: CopilotRequest, context: Dict[str, Any]) -> str:
        """Create user message with context"""
        
        parts = [f"User request: {request.message}"]
        
        if "current_graph" in context:
            graph = context["current_graph"]
            parts.append(f"\nCurrent strategy: {graph['name']}")
            parts.append(f"Nodes: {len(graph['nodes'])}")
            parts.append(f"Node details: {json.dumps(graph['nodes'], indent=2)}")
        
        if "last_results" in context:
            results = context["last_results"]
            parts.append(f"\nLast run results:")
            parts.append(f"Status: {results['status']}")
            if results.get("metrics"):
                metrics = results["metrics"]
                parts.append(f"Metrics:")
                parts.append(f"  - Sharpe: {metrics.get('sharpe_ratio', 'N/A'):.2f}")
                parts.append(f"  - CAGR: {metrics.get('cagr', 'N/A'):.2%}")
                parts.append(f"  - Max DD: {metrics.get('max_drawdown', 'N/A'):.2%}")
                parts.append(f"  - Win Rate: {metrics.get('win_rate', 'N/A'):.2%}")
                parts.append(f"  - Total Trades: {metrics.get('total_trades', 'N/A')}")
                parts.append(f"  - Turnover: {metrics.get('turnover', 'N/A'):.1f}")
            
            if results.get("warnings"):
                parts.append(f"Warnings: {len(results['warnings'])}")
                for w in results["warnings"][:3]:  # Show first 3
                    parts.append(f"  - {w.get('type')}: {w.get('message')}")
        
        return "\n".join(parts)

