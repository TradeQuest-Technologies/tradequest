"""
Advanced Backtest Copilot Service
Agentic AI system for backtest analysis with full tool access and streaming responses.
"""

from typing import Dict, Any, List, Optional, AsyncGenerator
from sqlalchemy.orm import Session
import json
import uuid
from datetime import datetime
from pathlib import Path
import numpy as np
import tempfile
import pickle

from openai import OpenAI
from app.models.user import User
from app.services.backtest_tools import (
    AnalysisTools,
    VisualizationTools,
    ParameterTools,
    ExecutionTools,
    OptimizationTools
)
from app.schemas.backtest_copilot import (
    ToolCallEvent,
    ToolResultEvent,
    ThinkingEvent,
    MessageEvent,
    ChartEvent,
    ParameterUpdateEvent,
    BacktestTriggeredEvent,
    ErrorEvent,
    DoneEvent
)
from app.core.config import settings
import structlog

logger = structlog.get_logger()


class NumpyEncoder(json.JSONEncoder):
    """JSON encoder that handles numpy types"""
    def default(self, obj):
        if isinstance(obj, (np.integer, np.int32, np.int64)):
            return int(obj)
        elif isinstance(obj, (np.floating, np.float32, np.float64)):
            return float(obj)
        elif isinstance(obj, (np.bool_,)):
            return bool(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        return super().default(obj)


class BacktestCopilotAdvanced:
    """
    Advanced agentic AI copilot for backtest analysis.
    
    Features:
    - Full tool access (analysis, visualization, parameters, execution, optimization)
    - Streaming responses with visible tool usage
    - Autonomous parameter optimization
    - Multi-turn conversations with context
    """
    
    def __init__(self, db: Session, user: User):
        self.db = db
        self.user = user
        
        # Initialize OpenAI
        if not settings.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY not configured")
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        
        # Initialize tool modules
        self.analysis = AnalysisTools(db, user)
        self.visualization = VisualizationTools(Path("charts"))
        self.parameters = ParameterTools()
        self.execution = ExecutionTools(db, user)
        self.optimization = OptimizationTools(db, user)
        
        # Conversation context
        self.messages = []
        self.tool_results_cache = {}
    
    def _get_tool_definitions(self) -> List[Dict]:
        """
        Define all available tools for the AI.
        Each tool is self-documenting with clear descriptions of what it does and when to use it.
        """
        return [
            # ========== ANALYSIS TOOLS ==========
            {
                "type": "function",
                "function": {
                    "name": "get_run_summary",
                    "description": """Get complete summary of a backtest run including metrics, config, and warnings.
                    
USE THIS FIRST when analyzing a backtest to understand the overall performance.

Returns: id, strategy_graph_id, config, metrics (all performance metrics), warnings, status""",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "run_id": {"type": "string", "description": "Backtest run ID"}
                        },
                        "required": ["run_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_trades_detailed",
                    "description": """Query specific trades with filters.
                    
Filter by symbol, side, P&L range, dates, winners/losers.

Best for: Analyzing specific trades, finding patterns, identifying outliers.""",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "run_id": {"type": "string"},
                            "filters": {
                                "type": "object",
                                "properties": {
                                    "symbol": {"type": "string"},
                                    "side": {"type": "string", "enum": ["long", "short"]},
                                    "min_pnl": {"type": "number"},
                                    "max_pnl": {"type": "number"},
                                    "start_date": {"type": "string"},
                                    "end_date": {"type": "string"},
                                    "winners_only": {"type": "boolean"},
                                    "losers_only": {"type": "boolean"},
                                    "limit": {"type": "integer"}
                                }
                            }
                        },
                        "required": ["run_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "execute_python",
                    "description": """Execute Python code with efficient data access.

PRE-LOADED VARIABLES:
- run_data: dict with run metadata (id, config, metrics, status)
- trades_file: str path to CSV file with ALL trades (use pd.read_csv(trades_file))
- equity_curve_file: str path to pickle file with equity curve
- pd, np, scipy, stats, statsmodels: libraries

EFFICIENT DATA PATTERNS:
1. Sample first: df = pd.read_csv(trades_file, nrows=10)  # Preview
2. Load conditionally: df = pd.read_csv(trades_file) if needed
3. Use filters: df[df['pnl'] < 0].head(20)  # Don't load everything
4. Aggregate in pandas: df.groupby('side').agg({'pnl': ['mean', 'count']})

MUST set 'result' variable for output. Keep it concise.

Best for: Statistical analysis, pattern detection, custom metrics, filtering.""",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "run_id": {"type": "string"},
                            "code": {"type": "string", "description": "Python code to execute"}
                        },
                        "required": ["run_id", "code"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "compare_runs",
                    "description": """Compare multiple backtest runs side-by-side.

Returns metrics comparison, best run ID, improvement percentages.

Best for: Before/after optimization, A/B testing parameters.""",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "run_ids": {"type": "array", "items": {"type": "string"}}
                        },
                        "required": ["run_ids"]
                    }
                }
            },
            
            # ========== VISUALIZATION TOOLS ==========
            {
                "type": "function",
                "function": {
                    "name": "generate_chart",
                    "description": """Generate custom charts: line, bar, scatter, heatmap.

Returns chart_id and URL to display.

Best for: Visualizing custom analysis, trade distributions, correlations.""",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "chart_type": {"type": "string", "enum": ["line", "bar", "scatter", "heatmap"]},
                            "title": {"type": "string"},
                            "data": {"type": "object", "description": "Chart data (x, y, etc.)"},
                            "options": {"type": "object", "description": "Chart options (colors, labels, etc.)"}
                        },
                        "required": ["chart_type", "title", "data"]
                    }
                }
            },
            
            # ========== PARAMETER TOOLS ==========
            {
                "type": "function",
                "function": {
                    "name": "update_leverage",
                    "description": """Modify leverage setting (1-10x).

Changes are pending until user approves.

Returns old/new values and impact description.""",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "run_id": {"type": "string"},
                            "leverage": {"type": "number", "minimum": 1, "maximum": 10}
                        },
                        "required": ["run_id", "leverage"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "update_position_sizing",
                    "description": """Change position size percentage (1-100%).

Scales all trades to new size.""",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "run_id": {"type": "string"},
                            "position_size_percent": {"type": "number", "minimum": 1, "maximum": 100}
                        },
                        "required": ["run_id", "position_size_percent"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "update_stop_loss",
                    "description": """Set/modify stop loss percentage (0-100%, or null to disable).

Caps losses at specified percentage.""",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "run_id": {"type": "string"},
                            "stop_loss_percent": {"type": ["number", "null"]}
                        },
                        "required": ["run_id", "stop_loss_percent"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "batch_update_parameters",
                    "description": """Update multiple parameters at once.

More efficient than individual updates.

Accepts: leverage, position_size_percent, stop_loss_percent, take_profit_percent, min/max_holding_hours, filters.""",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "run_id": {"type": "string"},
                            "updates": {"type": "object", "description": "Dict of parameter names to values"}
                        },
                        "required": ["run_id", "updates"]
                    }
                }
            },
            
            # ========== EXECUTION TOOLS ==========
            {
                "type": "function",
                "function": {
                    "name": "trigger_backtest_run",
                    "description": """Start a new backtest with modified parameters.

RATE LIMITED: Max 10 runs per session.

Returns run_id for the new backtest (will be queued for execution).""",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "strategy_graph_id": {"type": "string"},
                            "config_overrides": {"type": "object", "description": "Parameters to override"}
                        },
                        "required": ["strategy_graph_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_run_status",
                    "description": """Check status of a running or completed backtest.

Returns: status (queued/running/completed/failed), progress, metrics.""",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "run_id": {"type": "string"}
                        },
                        "required": ["run_id"]
                    }
                }
            },
            
            # ========== OPTIMIZATION TOOLS ==========
            {
                "type": "function",
                "function": {
                    "name": "monte_carlo_simulation",
                    "description": """Test if results are due to skill or luck.

Randomly reorders trades 1000 times. If original outperforms most random orderings, it's skill.

Returns: percentile, confidence interval, is_significant.""",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "run_id": {"type": "string"},
                            "n_simulations": {"type": "integer", "default": 1000}
                        },
                        "required": ["run_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "detect_overfitting",
                    "description": """Statistical tests for overfitting.

Checks: sample size, win rate, Sharpe ratio realism, outlier dependence, drawdown.

Returns risk_score (0-100) and specific flags.""",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "run_id": {"type": "string"}
                        },
                        "required": ["run_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "walk_forward_analysis",
                    "description": """Test strategy robustness over time.

Splits equity curve into periods and checks consistency.

Returns: period returns, consistency score, declining performance flag.""",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "run_id": {"type": "string"},
                            "n_splits": {"type": "integer", "default": 5}
                        },
                        "required": ["run_id"]
                    }
                }
            }
        ]
    
    def _execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Execute a tool by name with given arguments"""
        try:
            # Analysis tools
            if tool_name == "get_run_summary":
                return self.analysis.get_run_summary(**arguments)
            elif tool_name == "get_trades_detailed":
                return self.analysis.get_trades_detailed(**arguments)
            elif tool_name == "execute_python":
                return self.analysis.execute_python(**arguments)
            elif tool_name == "compare_runs":
                return self.analysis.compare_runs(**arguments)
            
            # Visualization tools
            elif tool_name == "generate_chart":
                return self.visualization.generate_chart(**arguments)
            
            # Parameter tools
            elif tool_name == "update_leverage":
                return self.parameters.update_leverage(**arguments)
            elif tool_name == "update_position_sizing":
                return self.parameters.update_position_sizing(**arguments)
            elif tool_name == "update_stop_loss":
                return self.parameters.update_stop_loss(**arguments)
            elif tool_name == "batch_update_parameters":
                return self.parameters.batch_update_parameters(**arguments)
            
            # Execution tools
            elif tool_name == "trigger_backtest_run":
                return self.execution.trigger_backtest_run(**arguments)
            elif tool_name == "get_run_status":
                return self.execution.get_run_status(**arguments)
            
            # Optimization tools
            elif tool_name == "monte_carlo_simulation":
                return self.optimization.monte_carlo_simulation(**arguments)
            elif tool_name == "detect_overfitting":
                return self.optimization.detect_overfitting(**arguments)
            elif tool_name == "walk_forward_analysis":
                return self.optimization.walk_forward_analysis(**arguments)
            
            else:
                raise ValueError(f"Unknown tool: {tool_name}")
        
        except Exception as e:
            logger.error(f"Tool execution failed: {tool_name}", error=str(e))
            return {"error": str(e)}
    
    async def analyze_streaming(
        self,
        run_id: str,
        user_question: str,
        chat_history: Optional[List[Dict[str, str]]] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Main analysis method with streaming responses.
        
        Yields events: tool_call, tool_result, thinking, message, chart, parameter_update, etc.
        """
        try:
            # Build system prompt with advanced prompt engineering  
            system_prompt = f"""You are an ELITE quantitative trading analyst with PhD-level expertise in statistical analysis and strategy optimization.

CONTEXT:
- Run ID: {run_id}
- User: {self.user.email}
- Question: {user_question}

==================================================================
YOUR MISSION: Provide DATA-DRIVEN insights using EFFICIENT analysis
==================================================================

CORE CAPABILITIES:
- Deep Analysis (trades, metrics, statistical tests)
- Advanced Visualization (custom charts, distributions, correlations)  
- Parameter Optimization (leverage, sizing, risk management)
- Backtest Execution (trigger new runs with optimized configs)
- Validation (Monte Carlo, overfitting detection, walk-forward)

==================================================================
DATA EFFICIENCY PROTOCOL (CRITICAL!)
==================================================================

When using execute_python:
1. **NEVER load full datasets blindly**
   BAD: df = pd.read_csv(trades_file)
   GOOD: df = pd.read_csv(trades_file, nrows=10)  # Sample first

2. **Use aggregations over raw data**
   GOOD: df.groupby('side')['pnl'].agg(['mean', 'std', 'count'])
   GOOD: df[df['pnl'] < 0].describe()

3. **Load only when necessary**
   - For counts/means: Use small samples or aggregations
   - For detailed analysis: Load full data only if needed

4. **Keep results CONCISE**
   - Return summaries, not raw lists
   - Use top 10, not all 1000

==================================================================
ANALYSIS WORKFLOW
==================================================================

1. START: get_run_summary() -> Understand overall performance
2. DIG DEEPER: Use execute_python with smart sampling
3. VALIDATE: Run statistical significance tests
4. VISUALIZE: Generate charts to show patterns
5. OPTIMIZE: Propose data-backed improvements
6. EXECUTE: Trigger new backtests if requested

==================================================================
BEST PRACTICES
==================================================================

- Be THOROUGH but EFFICIENT (don't waste tokens/time)
- ALWAYS validate statistical significance (p-values, confidence intervals)
- VISUALIZE key findings (charts > text)
- Provide ACTIONABLE recommendations with expected impact
- Use multiple iterations to build comprehensive analysis

==================================================================

Now analyze this backtest intelligently and efficiently."""

            # Build messages
            messages = [{"role": "system", "content": system_prompt}]
            
            # Add chat history (last 5 messages)
            if chat_history:
                for msg in chat_history[-5:]:
                    messages.append({
                        "role": msg.get("role", "user"),
                        "content": msg.get("content", "")
                    })
            
            # Add current question
            messages.append({"role": "user", "content": user_question})
            
            # Iterative tool calling loop
            max_iterations = 15
            iteration = 0
            
            while iteration < max_iterations:
                iteration += 1
                
                # Call OpenAI with tools
                response = self.client.chat.completions.create(
                    model="gpt-4o",
                    messages=messages,
                    tools=self._get_tool_definitions(),
                    tool_choice="auto",
                    max_tokens=4096,
                    temperature=0.7
                )
                
                assistant_message = response.choices[0].message
                
                has_tool_calls = bool(assistant_message.tool_calls)
                has_content = bool(assistant_message.content)
                content_preview = (assistant_message.content or '')[:100]
                
                logger.info(f"[Iteration {iteration}] Got response - tool_calls: {has_tool_calls} ({len(assistant_message.tool_calls or [])}), content: {has_content}, preview: '{content_preview}'")
                
                # Check if AI wants to use tools
                if assistant_message.tool_calls:
                    # Add assistant message to context
                    messages.append({
                        "role": "assistant",
                        "content": assistant_message.content or "",
                        "tool_calls": [
                            {
                                "id": tc.id,
                                "type": "function",
                                "function": {
                                    "name": tc.function.name,
                                    "arguments": tc.function.arguments
                                }
                            }
                            for tc in assistant_message.tool_calls
                        ]
                    })
                    
                    # Execute each tool call
                    logger.info(f"[Iteration {iteration}] Executing {len(assistant_message.tool_calls)} tool calls")
                    for tool_call in assistant_message.tool_calls:
                        tool_name = tool_call.function.name
                        try:
                            arguments = json.loads(tool_call.function.arguments)
                        except:
                            arguments = {}
                        
                        call_id = tool_call.id
                        
                        logger.info(f"[Iteration {iteration}] Tool: {tool_name}, call_id: {call_id}")
                        
                        # Stream tool call event
                        yield ToolCallEvent(
                            tool=tool_name,
                            params=arguments,
                            call_id=call_id
                        ).dict()
                        
                        # Execute tool
                        try:
                            result = self._execute_tool(tool_name, arguments)
                            
                            # Stream tool result event
                            yield ToolResultEvent(
                                tool=tool_name,
                                result=result,
                                call_id=call_id,
                                success=True
                            ).dict()
                            
                            # Add tool result to messages (with truncation for efficiency)
                            result_str = json.dumps(result, cls=NumpyEncoder) if not isinstance(result, str) else result
                            
                            # Truncate large results to save tokens
                            if len(result_str) > 5000:
                                result_str = result_str[:5000] + f"\n... [truncated, {len(result_str)} total chars]"
                            
                            messages.append({
                                "role": "tool",
                                "tool_call_id": call_id,
                                "content": result_str
                            })
                            
                            # Special handling for specific tool types
                            if tool_name == "generate_chart" and isinstance(result, dict):
                                yield ChartEvent(
                                    chart_id=result.get("chart_id", ""),
                                    url=result.get("url", ""),
                                    title=arguments.get("title", "Chart")
                                ).dict()
                            
                            elif tool_name in ["update_leverage", "update_position_sizing", "update_stop_loss", 
                                             "update_take_profit", "batch_update_parameters"]:
                                yield ParameterUpdateEvent(
                                    params=arguments,
                                    reasoning=result.get("impact", "Parameter updated"),
                                    requires_approval=True
                                ).dict()
                            
                            elif tool_name == "trigger_backtest_run" and isinstance(result, dict):
                                yield BacktestTriggeredEvent(
                                    run_id=result.get("run_id", ""),
                                    config=result.get("config", {})
                                ).dict()
                        
                        except Exception as e:
                            logger.error(f"Tool execution failed: {tool_name}", error=str(e))
                            yield ToolResultEvent(
                                tool=tool_name,
                                result=None,
                                call_id=call_id,
                                success=False,
                                error=str(e)
                            ).dict()
                            
                            messages.append({
                                "role": "tool",
                                "tool_call_id": call_id,
                                "content": f"Error: {str(e)}"
                            })
                    
                    # Continue loop to get next AI response
                    continue
                
                else:
                    # No more tool calls - AI has final response
                    logger.info(f"[Iteration {iteration}] AI finished - content length: {len(assistant_message.content or '')}")
                    try:
                        if assistant_message.content:
                            msg_event = MessageEvent(content=assistant_message.content).dict()
                            logger.info(f"[Iteration {iteration}] About to yield MessageEvent with keys: {list(msg_event.keys())}")
                            yield msg_event
                            logger.info(f"[Iteration {iteration}] Successfully yielded MessageEvent")
                        else:
                            logger.warning(f"[Iteration {iteration}] AI returned no content!")
                        
                        # Done
                        done_event = DoneEvent().dict()
                        logger.info(f"[Iteration {iteration}] About to yield DoneEvent with keys: {list(done_event.keys())}")
                        yield done_event
                        logger.info(f"[Iteration {iteration}] Successfully yielded DoneEvent")
                        break
                    except Exception as e:
                        logger.error(f"[Iteration {iteration}] Error yielding events: {e}", exc_info=True)
                        raise
            
            if iteration >= max_iterations:
                yield ErrorEvent(
                    error="Maximum iterations reached",
                    details="Analysis took too long. Try breaking down your question."
                ).dict()
                yield DoneEvent().dict()
        
        except Exception as e:
            logger.error(f"Streaming analysis failed", error=str(e), exc_info=True)
            yield ErrorEvent(error=str(e)).dict()
            yield DoneEvent().dict()

