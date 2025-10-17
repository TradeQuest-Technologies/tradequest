"""
AI Copilot for backtesting - strategy generation, diagnosis, optimization
"""

from typing import Dict, List, Any, Optional
import json
import structlog
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from app.models.backtest_v2 import StrategyGraph, BacktestRun
from app.models.trade import Trade
from app.models.backtest_conversation import BacktestConversation
from app.schemas.backtest_v2 import (
    CopilotRequest, CopilotResponse, GraphChange, ExpectedImpact,
    BlockNode, BlockType
)
from app.services.ai_router import ai_router
from datetime import datetime
import uuid

logger = structlog.get_logger()


class BacktestCopilot:
    """AI-powered backtesting copilot with trade analysis"""
    
    def __init__(self, db: Session, user_id: str):
        self.db = db
        self.user_id = user_id
        
        # Import services for trade analysis
        from app.services.ohlcv_service import OHLCVService
        from app.services.code_executor import CodeExecutor
        from app.services.storage_service import storage_service
        from pathlib import Path
        
        self.ohlcv_service = OHLCVService()
        self.code_executor = CodeExecutor()
        
        # Create workspace for this user
        self.workspace_path = storage_service.create_coach_workspace(self.user_id, f"backtest-{datetime.now().timestamp()}")
        self.workspace_dir = Path(self.workspace_path) if not storage_service.use_s3 else None
    
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
            
            # Get conversation history for this strategy
            conversation_history = []
            if request.strategy_graph_id:
                history = self.db.query(BacktestConversation).filter(
                    BacktestConversation.user_id == self.user_id,
                    BacktestConversation.strategy_id == request.strategy_graph_id
                ).order_by(BacktestConversation.message_index).limit(20).all()
                
                for msg in history:
                    conversation_history.append({
                        "role": msg.role,
                        "content": msg.content
                    })
            
            # Create system prompt
            system_prompt = self._create_system_prompt()
            
            # Create user message
            user_message = self._create_user_message(request, context)
            
            # Build messages array with history
            messages = [{"role": "system", "content": system_prompt}]
            messages.extend(conversation_history)
            messages.append({"role": "user", "content": user_message})
            
            # Define tools for function calling
            tools = [
                {
                    "type": "function",
                    "function": {
                        "name": "execute_python",
                        "description": "Execute Python code to analyze trades, calculate indicators, run ML models. Pre-loaded: pandas, numpy, scipy, talib, matplotlib, sklearn. Can use pip install for additional packages.",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "code": {"type": "string", "description": "Python code to execute"},
                                "description": {"type": "string", "description": "What this code does"}
                            },
                            "required": ["code"]
                        }
                    }
                },
                {
                    "type": "function",
                    "function": {
                        "name": "get_user_trades",
                        "description": "Get detailed trade data for analysis",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "limit": {"type": "integer", "description": "Number of trades to fetch (default 100, max 500)"}
                            }
                        }
                    }
                },
                {
                    "type": "function",
                    "function": {
                        "name": "create_blocks",
                        "description": "Create strategy blocks based on analysis findings. IMPORTANT: Blocks must be connected via 'inputs' array. Each block's 'inputs' should list the IDs of blocks that feed into it.",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "blocks": {
                                    "type": "array",
                                    "description": "Array of block definitions with connections",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "id": {"type": "string", "description": "Unique block ID (e.g., 'data1', 'rsi1')"},
                                            "type": {"type": "string", "description": "Block type (e.g., 'data.loader', 'feature.rsi')"},
                                            "params": {"type": "object", "description": "Block parameters"},
                                            "inputs": {
                                                "type": "array",
                                                "description": "Array of block IDs that feed into this block",
                                                "items": {"type": "string"}
                                            }
                                        },
                                        "required": ["id", "type", "params", "inputs"]
                                    }
                                },
                                "explanation": {"type": "string", "description": "Explain how blocks match the analysis"}
                            },
                            "required": ["blocks", "explanation"]
                        }
                    }
                }
            ]
            
            # Call AI using router
            logger.info(f"Calling AI for copilot request: {request.message[:100]}")
            
            response = await ai_router.chat_completion(
                messages=messages,
                user_id=self.user_id,
                request_type="copilot",
                temperature=0.7,
                tools=tools,
                tool_choice="auto",
                force_model="gpt-4o",  # Copilot needs GPT-4o for complex analysis
                use_cache=False,  # Don't cache tool-based requests
                priority=1
            )
            
            # Handle function calls in a loop
            assistant_message = response.choices[0].message
            all_changes = []
            final_message_parts = []
            
            while assistant_message.tool_calls:
                # Execute each tool call
                for tool_call in assistant_message.tool_calls:
                    function_name = tool_call.function.name
                    function_args = json.loads(tool_call.function.arguments)
                    
                    logger.info(f"Executing tool: {function_name}")
                    
                    # Execute the tool
                    tool_result = await self._execute_tool(function_name, function_args)
                    
                    # Add tool response to messages
                    messages.append({
                        "role": "assistant",
                        "content": None,
                        "tool_calls": [tool_call.model_dump()]
                    })
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": json.dumps(tool_result)
                    })
                    
                    # If create_blocks was called, convert to GraphChange format
                    if function_name == "create_blocks":
                        blocks = function_args.get("blocks", [])
                        for block in blocks:
                            # Convert block to GraphChange format
                            graph_change = {
                                "op": "add",
                                "target": block.get("id", f"node_{len(all_changes)}"),
                                "payload": block
                            }
                            all_changes.append(graph_change)
                        final_message_parts.append(function_args.get("explanation", ""))
                
                # Get next response using router
                response = await ai_router.chat_completion(
                    messages=messages,
                    user_id=self.user_id,
                    request_type="copilot",
                    temperature=0.7,
                    tools=tools,
                    tool_choice="auto",
                    force_model="gpt-4o",
                    use_cache=False,
                    priority=1
                )
                assistant_message = response.choices[0].message
            
            # Final message
            final_message = assistant_message.content or "\n\n".join(final_message_parts)
            
            # Convert changes to proper format
            parsed = {
                "message": final_message,
                "changes": all_changes,
                "expected_impacts": [],
                "suggested_next_steps": ["Run the backtest to validate the strategy"]
            }
            
            # Save conversation to database
            if request.strategy_graph_id:
                # Get next message index
                max_index = self.db.query(func.max(BacktestConversation.message_index)).filter(
                    BacktestConversation.user_id == self.user_id,
                    BacktestConversation.strategy_id == request.strategy_graph_id
                ).scalar() or 0
                
                # Save user message
                user_conv = BacktestConversation(
                    id=str(uuid.uuid4()),
                    user_id=self.user_id,
                    strategy_id=request.strategy_graph_id,
                    role="user",
                    content=request.message,
                    message_index=max_index + 1
                )
                self.db.add(user_conv)
                
                # Save assistant message with metadata
                metadata = {
                    "changes": parsed.get("changes", []),
                    "expected_impacts": parsed.get("expected_impacts", []),
                    "suggested_next_steps": parsed.get("suggested_next_steps", [])
                }
                
                assistant_conv = BacktestConversation(
                    id=str(uuid.uuid4()),
                    user_id=self.user_id,
                    strategy_id=request.strategy_graph_id,
                    role="assistant",
                    content=parsed.get("message", ""),
                    message_data=json.dumps(metadata),
                    message_index=max_index + 2
                )
                self.db.add(assistant_conv)
                self.db.commit()
            
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
        """Build context for copilot with trade data"""
        
        context = {
            "user_id": self.user_id,
            "message": request.message
        }
        
        # Get user's trade history for analysis
        from app.models.trade import Trade
        trades = self.db.query(Trade).filter(
            Trade.user_id == self.user_id
        ).order_by(desc(Trade.filled_at)).limit(100).all()
        
        if trades:
            context["user_trades_summary"] = {
                "total_trades": len(trades),
                "symbols": list(set([t.symbol for t in trades])),
                "venues": list(set([t.venue for t in trades])),
                "date_range": {
                    "start": trades[-1].filled_at.isoformat() if trades else None,
                    "end": trades[0].filled_at.isoformat() if trades else None
                }
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
    
    async def _get_user_trades_data(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get user's trade data for analysis"""
        trades = self.db.query(Trade).filter(
            Trade.user_id == self.user_id
        ).order_by(desc(Trade.filled_at)).limit(limit).all()
        
        trades_data = []
        for trade in trades:
            trades_data.append({
                "symbol": trade.symbol or "UNKNOWN",  # Handle legacy trades
                "side": trade.side,
                "quantity": float(trade.qty),
                "entry_price": float(trade.avg_price),
                "pnl": float(trade.pnl),
                "fees": float(trade.fees),
                "filled_at": trade.filled_at.isoformat() if trade.filled_at else None,
                "submitted_at": trade.submitted_at.isoformat() if trade.submitted_at else None,
                "venue": trade.venue
            })
        
        return trades_data
    
    async def _execute_tool(self, function_name: str, function_args: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool function"""
        
        try:
            if function_name == "execute_python":
                code = function_args.get("code", "")
                
                # Add workspace_dir to context
                context_data = {
                    "workspace_dir": str(self.workspace_path),
                    "trades_data": await self._get_user_trades_data(500)  # Give AI access to trades
                }
                
                result = self.code_executor.execute(code, context_data)
                return {
                    "success": result.get("success"),
                    "result": result.get("result"),
                    "stdout": result.get("stdout", ""),
                    "error": result.get("error")
                }
            
            elif function_name == "get_user_trades":
                limit = function_args.get("limit", 100)
                limit = min(limit, 500)  # Cap at 500
                trades = await self._get_user_trades_data(limit)
                return {
                    "trades": trades,
                    "count": len(trades)
                }
            
            elif function_name == "create_blocks":
                # Just return the blocks - they'll be added to changes
                return {
                    "success": True,
                    "blocks_created": len(function_args.get("blocks", []))
                }
            
            else:
                return {"error": f"Unknown function: {function_name}"}
                
        except Exception as e:
            logger.error(f"Tool execution failed: {e}")
            return {"error": str(e)}
    
    def _create_system_prompt(self) -> str:
        """Create concise system prompt for copilot"""
        
        return """You are an expert quantitative trading strategist and copilot. Your job is to BUILD WORKING STRATEGIES, not just talk about them.

## CRITICAL RULES:

1. **BE ACTION-ORIENTED**: When user asks to build/create/make a strategy, DO IT IMMEDIATELY. Don't ask questions unless absolutely necessary.

2. **DEFAULT ASSUMPTIONS**: If user doesn't specify:
   - Symbol: Use BTC/USDT (most popular)
   - Timeframe: Use 1h (good for trend following)
   - Date range: Use last 90 days

3. **ALWAYS RETURN BLOCKS**: Every response should include actual block changes in the JSON, not just talk about it.

## Your Capabilities

1. **Strategy Design**: Create complete block-based strategy graphs
2. **Advanced Trade Analysis**: Use Python to analyze patterns (when needed)
3. **Optimization**: Suggest parameter improvements
4. **Diagnosis**: Analyze backtest results and identify issues

## WORKFLOW

When user says "build me a strategy" or "create a strategy":

**DO THIS IMMEDIATELY:**

1. **Interpret Intent**:
   - "trend following" → Use MACD + EMA crossovers
   - "mean reversion" → Use RSI + Bollinger Bands  
   - "advanced quant" → Add ATR, multiple confirmations, volatility sizing
   - "cool strategy" → Create something sophisticated with 3+ indicators

2. **CREATE THE BLOCKS** (Don't ask, just do it):
   - Start with data.loader
   - Add 2-3 feature blocks (indicators)
   - Add signal block (rule or threshold)
   - Add sizing block (vol_target for advanced strategies)
   - Add risk block (stop/take profit)
   - Add exec block
   - CONNECT THEM via inputs array

3. **Return JSON**: Always include the "changes" array with actual blocks

## Example Response to "Build me a cool trend following strategy":

```json
{
  "message": "**Advanced Trend-Following Strategy Created**\n\nI've built a sophisticated multi-indicator strategy:\n- MACD (12/26/9) for primary trend detection\n- EMA 50 & 200 for trend confirmation (only trade in direction of major trend)\n- ATR-based volatility sizing (risk 2% per trade)\n- Dynamic stops at 2x ATR\n\nThis is ready to backtest on BTC/USDT 1h!",
  "changes": [
    {"op": "add", "target": "data1", "payload": {"id": "data1", "type": "data.loader", "params": {"symbol": "BTC/USDT", "timeframe": "1h"}, "inputs": []}},
    {"op": "add", "target": "macd1", "payload": {"id": "macd1", "type": "feature.macd", "params": {"fast_period": 12, "slow_period": 26, "signal_period": 9}, "inputs": ["data1"]}},
    {"op": "add", "target": "ema50", "payload": {"id": "ema50", "type": "feature.ema", "params": {"period": 50}, "inputs": ["data1"]}},
    {"op": "add", "target": "ema200", "payload": {"id": "ema200", "type": "feature.ema", "params": {"period": 200}, "inputs": ["data1"]}},
    {"op": "add", "target": "atr1", "payload": {"id": "atr1", "type": "feature.atr", "params": {"period": 14}, "inputs": ["data1"]}},
    {"op": "add", "target": "sig1", "payload": {"id": "sig1", "type": "signal.rule", "params": {"rule": "macd_cross_up AND price>ema50 AND ema50>ema200 -> long; macd_cross_down AND price<ema50 AND ema50<ema200 -> short"}, "inputs": ["macd1", "ema50", "ema200"]}},
    {"op": "add", "target": "size1", "payload": {"id": "size1", "type": "sizing.vol_target", "params": {"target_vol": 0.15, "max_position": 0.02}, "inputs": ["sig1", "atr1"]}},
    {"op": "add", "target": "risk1", "payload": {"id": "risk1", "type": "risk.stop_take", "params": {"stop_atr_mult": 2.0, "take_atr_mult": 3.0}, "inputs": ["size1", "atr1"]}},
    {"op": "add", "target": "exec1", "payload": {"id": "exec1", "type": "exec.market", "params": {"slippage_bps": 5, "fee_bps": 10}, "inputs": ["risk1"]}}
  ],
  "run_proposal": {"baseline": true},
  "suggested_next_steps": ["Click 'Run Backtest' to test this strategy"]
}
```

## NO MORE ASKING FOR CLARIFICATION

If user says:
- "Build trend strategy" → BUILD IT with MACD/EMA
- "Make mean reversion" → BUILD IT with RSI/Bollinger
- "Cool strategy" → BUILD IT with 3+ indicators
- "Advanced quant" → BUILD IT with ML/statistical features

STOP ASKING. START BUILDING.

**Example Flow:**
User: "Analyze my last 500 trades and create a strategy"

1. First, execute Python code to:
   - Load all their trades
   - Calculate advanced indicators (Bollinger, Stochastic, ATR, Volume Profile, etc.)
   - Run ML models (Random Forest, XGBoost) to find patterns
   - Identify optimal entry conditions
   - Create visualization showing findings
   
2. Then, create simple blocks based on findings:
   - If analysis shows RSI<35 + MACD cross works best → create those blocks
   - If analysis shows specific stop loss levels → create risk.stop_take block
   - Keep it simple - blocks are just execution, not analysis

## Trade Data Access

You have access to the user's trade history summary in the context. When a user asks you to analyze their trades:
- You can see their symbols, venues, date ranges, and trade count
- You can infer their trading style (scalping, swing, day trading) from the data
- You can suggest strategies that match their historical patterns
- Example: "I see you trade BTC/USDT frequently. Let me create a strategy using RSI and MACD based on your entry patterns."

## Python Execution & Package Installation

You can execute Python code to analyze data. The environment includes:
- **Pre-installed**: pandas, numpy, scipy, talib, matplotlib, seaborn, plotly
- **Pip Install**: Use `pip install package-name` in your code to install any package you need
- **Example**: If you need sklearn for regression: `pip install scikit-learn`
- The system will automatically install packages before running your code

## Image Generation

You can create visualizations to help users understand strategies:
- **Save images**: Use `plt.savefig(f'{workspace_dir}/chart_name.png', dpi=150, bbox_inches='tight')`
- **Return image**: Set `result = {'image': 'chart_name.png', 'analysis': 'Your insights'}`
- **workspace_dir** is available as a variable in your Python environment
- **Example**: Create equity curves, heatmaps, indicator comparisons, etc.

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

## Block Operations

You can:
1. **Add blocks**: `{"op": "add", "target": "block_id", "payload": {...}}`
2. **Update blocks**: `{"op": "update", "target": "existing_block_id", "payload": {"params": {...}}}`
3. **Delete blocks**: `{"op": "delete", "target": "existing_block_id", "payload": null}`

**CRITICAL: Connect blocks via 'inputs' array!**
- data.loader has `inputs: []` (no inputs)
- feature.rsi has `inputs: ["data1"]` (connects to data loader)
- signal.threshold has `inputs: ["rsi1"]` (connects to RSI)
- exec.market has `inputs: ["risk1"]` (connects to risk management)

Example flow: data1 → rsi1 → sig1 → size1 → risk1 → exec1

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

**Example 1: Reverse Engineer from User Trades**

User: "Look at my past 100 trades. I entered using MACD, RSI and SMA. Can you analyze my trades and hardcode my strategy into these blocks?"

Response:
```json
{
  "message": "I analyzed your last 100 trades and identified your strategy pattern:\n\n**Your Trading Style:**\n- Primary symbols: BTC/USDT, ETH/USDT\n- Entry signals: MACD crossover + RSI confirmation\n- Average hold time: 4-6 hours\n- Risk: ~2% per trade\n\nI've created a block strategy that matches your approach:\n1. MACD (12,26,9) for trend\n2. RSI (14) for confirmation (enter when RSI 40-60 on MACD cross)\n3. SMA (50) as trend filter\n4. ATR-based stops at 2x\n\nThis should replicate your manual strategy. Let's backtest it!",
  "changes": [
    {"op": "add", "target": "data1", "payload": {"id": "data1", "type": "data.loader", "params": {"symbol": "BTC/USDT", "timeframe": "1h"}, "inputs": []}},
    {"op": "add", "target": "macd1", "payload": {"id": "macd1", "type": "feature.macd", "params": {"fast_period": 12, "slow_period": 26, "signal_period": 9}, "inputs": ["data1"]}},
    {"op": "add", "target": "rsi1", "payload": {"id": "rsi1", "type": "feature.rsi", "params": {"period": 14}, "inputs": ["data1"]}},
    {"op": "add", "target": "sma1", "payload": {"id": "sma1", "type": "feature.ema", "params": {"period": 50}, "inputs": ["data1"]}},
    {"op": "add", "target": "sig1", "payload": {"id": "sig1", "type": "signal.rule", "params": {"rule": "macd_cross AND rsi>40 AND rsi<60 AND price>sma50 -> long"}, "inputs": ["macd1", "rsi1", "sma1"]}},
    {"op": "add", "target": "size1", "payload": {"id": "size1", "type": "sizing.fixed", "params": {"position_size": 0.02}, "inputs": ["sig1"]}},
    {"op": "add", "target": "risk1", "payload": {"id": "risk1", "type": "risk.stop_take", "params": {"stop_atr_mult": 2.0, "take_atr_mult": 3.0}, "inputs": ["size1"]}},
    {"op": "add", "target": "exec1", "payload": {"id": "exec1", "type": "exec.market", "params": {"slippage_bps": 5, "fee_bps": 10}, "inputs": ["risk1"]}}
  ],
  "run_proposal": {"baseline": true},
  "suggested_next_steps": ["Run the backtest to see how your strategy performs", "Compare results to your actual trades"]
}
```

**Example 2: Build from Scratch**

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
        
        # DON'T send trade data - AI can access it via get_user_trades tool when needed
        if "user_trades_summary" in context:
            summary = context["user_trades_summary"]
            parts.append(f"\nNote: User has {summary['total_trades']} trades available. Use get_user_trades tool to analyze them.")
        
        if "current_graph" in context:
            graph = context["current_graph"]
            parts.append(f"\nCurrent strategy: {graph['name']} ({len(graph['nodes'])} blocks)")
            # Send block details so AI can see what's already there
            parts.append("\nCurrent blocks:")
            for node in graph['nodes']:
                node_desc = f"  - {node.get('id')}: {node.get('type')}"
                if node.get('params'):
                    # Show key params only
                    key_params = list(node.get('params', {}).items())[:2]
                    if key_params:
                        param_str = ', '.join([f"{k}={v}" for k, v in key_params])
                        node_desc += f" ({param_str})"
                parts.append(node_desc)
        
        if "last_results" in context:
            results = context["last_results"]
            parts.append(f"\nLast run: {results['status']}, {results['total_trades']} trades")
            if results.get("metrics"):
                m = results["metrics"]
                # Only key metrics, one line
                parts.append(f"Sharpe={m.get('sharpe_ratio', 'N/A')}, Win%={m.get('win_rate', 'N/A')}, MaxDD={m.get('max_drawdown', 'N/A')}")
            
            if results.get("warnings"):
                parts.append(f"Warnings: {len(results['warnings'])}")
                for w in results["warnings"][:3]:  # Show first 3
                    parts.append(f"  - {w.get('type')}: {w.get('message')}")
        
        return "\n".join(parts)

