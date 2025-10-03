"""
AI Coach Service - Trading Intelligence Agent

Architecture:
- Lean system prompt (role + mission)
- Self-documenting tools
- Dynamic context injection
- Natural ReAct loop (Reason → Act → Observe)
"""

import json
import structlog
import traceback
import asyncio
from typing import List, Dict, Optional, Any, AsyncGenerator
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
import openai
from collections import defaultdict

from app.core.config import settings
from app.models.trade import Trade
from app.models.coach_conversation import CoachConversation
from app.services.ohlcv_service import OHLCVService
from app.services.code_executor import CodeExecutor
import uuid as uuid_lib

logger = structlog.get_logger()


class AICoachService:
    def __init__(self, db: Session, user_id, session_id: Optional[str] = None):
        self.db = db
        self.user_id = str(user_id) if not isinstance(user_id, str) else user_id
        self.session_id = session_id or str(uuid_lib.uuid4())
        self.ohlcv_service = OHLCVService()
        self.code_executor = CodeExecutor()
        self.client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
        self.async_client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.max_history = 20
        
        # Create persistent workspace for this session
        from pathlib import Path
        from app.services.storage_service import storage_service
        
        self.workspace_path = storage_service.create_coach_workspace(self.user_id, self.session_id)
        self.workspace_dir = Path(self.workspace_path)
        
        # For local storage, ensure directory exists
        if not storage_service.use_s3:
            self.workspace_dir.mkdir(parents=True, exist_ok=True)
        
        # Cache for bulk OHLCV data in this session
        self.ohlcv_cache = {}
        
        # Persistent Python execution context (variables saved across execute_python calls)
        self.python_context = {}
        
        # Elite trading analyst system prompt
        self.system_prompt = """You are an elite quantitative trading analyst specializing in retail trader performance forensics.

AVAILABLE TOOLS:
- **get_trades_summary**: Get overview of trading performance (win rate, PnL, common symbols)
- **execute_python**: Run Python code with pandas, numpy, scipy, talib pre-loaded. Has access to trades_data list.
- **analyze_trade_context**: Get detailed context for specific trades
- **discover_patterns**: Test specific hypotheses about trading behavior
- **fetch_ohlcv_data**: Fetch OHLCV candlestick data (auto-routes: Polygon for stocks/forex, Binance Vision for crypto)
- **fetch_aggtrades_data**: Fetch granular trade-level data for crypto (Binance Vision)

PYTHON EXECUTION ENVIRONMENT:
- Pre-imported: pandas as pd, numpy as np, scipy, talib, matplotlib.pyplot as plt, seaborn as sns, plotly (go, px)
- Available: trades_data (list of dicts with keys: symbol, side, quantity, entry_price, exit_price, pnl, filled_at, submitted_at, duration_seconds)
- CRITICAL: filled_at = ENTRY time (when position opened), submitted_at = EXIT time (when position closed)
- Can import additional libraries, create visualizations, run statistical tests
- All data fetched via fetch_ohlcv_data or fetch_aggtrades_data is saved to workspace and accessible
- IMPORTANT: get_ohlcv() may return empty list if data unavailable (future dates, missing symbols) - always check before processing!

IMAGE GENERATION - CREATE VISUAL INSIGHTS:
- **Matplotlib/Seaborn**: Create static charts (equity curves, distributions, heatmaps, etc.)
- **Plotly**: Create interactive charts (optional, but matplotlib is simpler)
- **Save charts**: MUST use workspace_dir variable (it's a string path): `plt.savefig(f'{workspace_dir}/chart_name.png', dpi=150, bbox_inches='tight')`
- **Return image path**: Set `result = {'image': 'chart_name.png', 'analysis': 'Your insights here'}` (ONLY the filename, NOT full path)
- **CRITICAL**: workspace_dir is available as a variable in your Python environment - use it directly!
- **WRONG**: `plt.savefig('chart.png')` or `plt.savefig('/mnt/data/chart.png')` ❌
- **CORRECT**: `plt.savefig(f'{workspace_dir}/chart.png')` ✅
- **Example**:
```python
import matplotlib.pyplot as plt
plt.figure(figsize=(12, 6))
plt.plot(data)
plt.title('My Analysis')
plt.savefig(f'{workspace_dir}/my_chart.png', dpi=150, bbox_inches='tight')
plt.close()
result = {'image': 'my_chart.png', 'analysis': 'Key insights here'}
```
- **Examples**:
  * Equity curve: Plot cumulative PnL over time
  * Win/Loss distribution: Histogram of PnL values
  * Entry quality heatmap: RSI vs MACD at entry colored by outcome
  * Time-of-day performance: Bar chart of win rate by hour
  * Bayesian analysis: Posterior distributions, credible intervals
  * Correlation matrix: Heatmap of trade metrics correlations
- **Best practices**: Clear labels, titles, legends; use seaborn for beautiful defaults; close figures with `plt.close()` after saving

SMART DATA FETCHING STRATEGY:
- **Be precise**: Only fetch data you actually need for the specific analysis
- **Time windows**: For entry/exit quality, fetch ~10-30 minutes BEFORE entry to ~10-30 minutes AFTER exit
- **Indicators need history**: 
  * RSI(14): Needs 14+ periods before first trade (fetch extra 30+ periods to warm up)
  * MACD(12,26,9): Needs 34+ periods before first trade (fetch extra 50+ periods)
  * Always add buffer periods BEFORE the analysis window
- **Multiple trades, same symbol**: 
  * Calculate overall time range: (earliest_entry - indicator_warmup) to (latest_exit + buffer)
  * Fetch ONCE for that range, analyze all trades together
- **Multiple symbols**: Fetch each symbol's time range separately (they may not overlap)

CRITICAL - FILE-BASED DATA FLOW:
- fetch_ohlcv_data saves data to CSV files and returns FILE PATH, not raw data
- Workflow MUST be:
  1. fetch_ohlcv_data(symbol, start_time, end_time, "1m") → returns {"file": "data/coach_workspaces/.../SEI_USDT_1m_20240901_20240902.csv", "candles": 1440}
  2. IMMEDIATELY call execute_python to load and process the file:
     - Load: df = pd.read_csv('data/coach_workspaces/.../SEI_USDT_1m_20240901_20240902.csv')
     - Convert: closes = df['close'].values
     - Calculate: rsi = talib.RSI(closes, 14); macd, signal, hist = talib.MACD(closes)
     - Extract metrics per trade: rsi_at_entry, macd_at_entry, trend_direction, etc.
     - Return ONLY small summary: result = {"trades_analyzed": 100, "avg_rsi_at_entry": 52.3, "good_entries": 67, ...}
  3. Continue with compact summaries, never load entire files into conversation context

EXAMPLE - Analyzing entry timing with RSI/MACD for 100 trades:

**ITERATION 1: Calculate time ranges AND fetch data (multiple tool calls)**
```python
# execute_python: Calculate time ranges
df = pd.DataFrame(trades_data)
last_100 = df.nlargest(100, 'filled_at')
symbols = last_100['symbol'].unique()
time_ranges = {}
for symbol in symbols:
    symbol_trades = last_100[last_100['symbol'] == symbol]
    start_time = symbol_trades['filled_at'].min() - timedelta(hours=1)  # 1hr buffer for RSI/MACD
    end_time = symbol_trades['submitted_at'].max() + timedelta(minutes=30)
    time_ranges[symbol] = {'start': start_time.isoformat(), 'end': end_time.isoformat()}
result = time_ranges  # Returns: {'SEI_USDT': {'start': '2024-09-01T10:00:00', 'end': '2024-09-01T18:00:00'}, ...}
```

**SAME ITERATION: Immediately fetch data (don't wait for next iteration!)**
```
# fetch_ohlcv_data for SEI_USDT: symbol='SEI_USDT', start='2024-09-01T10:00:00', end='2024-09-01T18:00:00', timeframe='1m'
# fetch_ohlcv_data for ARKM_USDT: symbol='ARKM_USDT', start='2024-09-01T11:00:00', end='2024-09-01T17:00:00', timeframe='1m'
# (fetch all symbols)
```

**ITERATION 2: Load files and calculate indicators**
```python
# execute_python: Load CSV files and calculate RSI/MACD at each trade entry
files = {
    'SEI_USDT': 'data/coach_workspaces/.../SEI_USDT_1m_20240901_20240902.csv',
    'ARKM_USDT': 'data/coach_workspaces/.../ARKM_USDT_1m_20240901_20240902.csv',
    'DOGE_USDT': 'data/coach_workspaces/.../DOGE_USDT_1m_20240901_20240902.csv'
}

results = {}
for symbol, filepath in files.items():
    # Load from CSV file (not from memory!)
    df_ohlcv = pd.read_csv(filepath)
    df_ohlcv['timestamp'] = pd.to_datetime(df_ohlcv['timestamp'])
    closes = df_ohlcv['close'].values
    
    rsi = talib.RSI(closes, 14)
    macd, signal_line, hist = talib.MACD(closes)
    
    # For each trade, find RSI/MACD at entry time
    symbol_trades = last_100[last_100['symbol'] == symbol]
    for _, trade in symbol_trades.iterrows():
        entry_time = trade['filled_at']
        # Find closest candle to entry_time
        idx = (df_ohlcv['timestamp'] - entry_time).abs().idxmin()
        results[trade['id']] = {
            'rsi_at_entry': rsi[idx],
            'macd_at_entry': macd[idx],
            'signal_at_entry': signal_line[idx]
        }

result = {
    'trades_analyzed': len(results),
    'avg_rsi_at_entry': float(np.mean([r['rsi_at_entry'] for r in results.values()])),
    'good_entries_pct': sum(1 for r in results.values() if 30 < r['rsi_at_entry'] < 70) / len(results) * 100
}  # Returns compact summary from file analysis!
```

Communication style:
- Lead with the punchline (TL;DR insight)
- Support with evidence (specific numbers, not ranges)
- End with 1-2 actionable recommendations with expected impact

CRITICAL: You are a DISCOVERY ENGINE, not a checklist.
- **CONVERSATIONAL FIRST**: Respond naturally to greetings, questions, and casual conversation
- **TOOLS ONLY WHEN NEEDED**: Only call functions when user asks for specific analysis or data
- **NO AUTO-ANALYSIS**: Don't automatically analyze trades unless explicitly requested
- When asked about "weaknesses" or "patterns", don't jump to assumptions
- Start broad: analyze distribution of losses, identify outliers, find correlations
- Let the DATA reveal patterns - you might find hundreds of micro-patterns
- Think like a forensic investigator: "What's unusual here? What doesn't fit?"
"""

    def _get_tool_definitions(self) -> List[Dict]:
        """
        Tool definitions are self-documenting.
        Each tool clearly explains WHAT it does and WHEN to use it.
        """
        return [
            {
                "type": "function",
                "function": {
                    "name": "get_trades_summary",
                    "description": """Get aggregated trading statistics and performance metrics.

USE THIS FIRST for any performance question to get the big picture.

Returns:
- Total trades, wins/losses, win rate
- Net P&L and profit factor
- Symbol breakdown with individual win rates
- Side (long/short) performance
- Recent performance trends

Best for: "How am I doing?", "What's my win rate?", "Which symbols are best?"
""",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "days_back": {
                                "type": "integer",
                                "description": "Number of days to analyze (e.g., 30, 90, 365)"
                            }
                        },
                        "required": ["days_back"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "execute_python",
                    "description": """Execute Python code for calculations, indicators, and pattern analysis.

PRE-LOADED GLOBALS:
- trades_data: List of all user trades (dicts with id, symbol, side, pnl, qty, avg_price, filled_at, submitted_at, etc.)
  * IMPORTANT: filled_at and submitted_at are DATETIME OBJECTS (not strings) - use them directly!
- total_trades: Count of trades
- get_ohlcv(symbol, start_time, end_time, timeframe): Function to fetch OHLCV data (accepts datetime objects or ISO strings)
- get_aggtrades(symbol, start_time, end_time): Function to fetch aggregated trades data (crypto only, more granular than OHLCV)

PRE-IMPORTED LIBRARIES (DO NOT import them again):
- pd, pandas: Pandas library (already imported)
- np, numpy: NumPy library (already imported)
- talib: Technical Analysis library (already imported - use directly)
- scipy: SciPy and scipy.stats (already imported)
- datetime, timedelta: Date/time utilities
- math, statistics: Math libraries
- defaultdict: From collections

IMPORTANT: These are already available! Just use them directly:
```python
# CORRECT - Just use them:
df = pd.DataFrame(trades_data)
rsi = talib.RSI(np.array(closes))
from scipy.stats import ttest_ind

# WRONG - Don't import:
import pandas as pd  # ❌ Already available!
import talib  # ❌ Already available!
```

EXAMPLES:
```python
# Convert trades to DataFrame
df = pd.DataFrame(trades_data)

# Win rate by symbol
wins = df[df['pnl'] > 0].groupby('symbol').size()
total = df.groupby('symbol').size()
win_rate = (wins / total * 100).round(2)
print(win_rate)

# Find worst losses
worst_losses = df.nsmallest(5, 'pnl')[['id', 'symbol', 'pnl', 'filled_at']]
result = worst_losses.to_dict('records')

# Fetch OHLCV and calculate RSI for a trade
trade = trades_data[0]
entry_time = trade['filled_at']  # Already a datetime object!
exit_time = trade['submitted_at']  # Already a datetime object!
start = entry_time - timedelta(minutes=30)
end = exit_time + timedelta(minutes=30)
ohlcv = get_ohlcv(trade['symbol'], start, end, '1m')

# ALWAYS check if OHLCV data is available before processing
if ohlcv and len(ohlcv) > 0:
    closes = [candle['close'] for candle in ohlcv]
    rsi = talib.RSI(np.array(closes))
    result = f"RSI calculated: {rsi[-1]}"
else:
    result = "No OHLCV data available (may be future dates or missing symbol)"
```

Set 'result' variable for output.

Best for: Complex calculations, indicator analysis, statistical tests, finding patterns in trades.
""",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "code": {
                                "type": "string",
                                "description": "Python code to execute. Use 'result' variable to return output."
                            }
                        },
                        "required": ["code"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_trade_ohlcv",
                    "description": """Fetch OHLCV (candlestick) data for a specific trade.

Returns price data from 30 minutes BEFORE entry to 30 minutes AFTER exit.

CRITICAL: trade_id must be a UUID from trades_data, NOT a symbol!

WORKFLOW:
1. First use execute_python to analyze trades_data and get trade UUIDs
2. Then call this function with the actual UUID (e.g., 'a7f3c8e2-1234-...')

EXAMPLE:
```python
# In execute_python:
df = pd.DataFrame(trades_data)
worst_trade_id = df.nsmallest(1, 'pnl')['id'].iloc[0]
result = worst_trade_id  # Returns the UUID
```
# Then call:
get_trade_ohlcv(trade_id=<that_uuid>, timeframe='1m')

Best for: Analyzing entry/exit quality, trend alignment, support/resistance, momentum at entry.
""",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "trade_id": {
                                "type": "string",
                                "description": "Trade UUID (get from trades_data, NOT the symbol!)"
                            },
                            "timeframe": {
                                "type": "string",
                                "description": "Candle timeframe",
                                "enum": ["1m", "5m", "15m", "1h", "4h", "1d"]
                            }
                        },
                        "required": ["trade_id", "timeframe"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "discover_patterns",
                    "description": """AI-DRIVEN PATTERN DISCOVERY: Find ANY statistical patterns in trading behavior.

THIS IS NOT A PREDEFINED LIST. You decide what patterns to investigate based on the trader's data.

APPROACH:
1. Look at the trades_data and identify hypotheses worth testing
2. Use execute_python to run statistical tests (scipy.stats, correlations, etc.)
3. Test for significance (p < 0.05, confidence intervals, effect sizes)
4. Return patterns that have STATISTICAL BACKING, not guesses

DISCOVERY DIMENSIONS (explore ANY angle, not just these):
- **Behavioral**: Any pattern in trading behavior after wins/losses/streaks
- **Temporal**: Time-based patterns (hourly, daily, weekly, monthly, duration)
- **Market Context**: Performance under different market conditions
- **Entry/Exit Quality**: Timing, price levels, technical setups
- **Position Sizing**: Any sizing patterns or anomalies
- **Symbol/Asset**: Performance variations across instruments
- **Sequential**: Patterns in consecutive trades, order effects
- **Statistical Outliers**: Unusual distributions, fat tails, skewness
- **Custom Hypotheses**: ANYTHING the data suggests - be creative!

HOW TO USE THIS TOOL:
Call this when you've identified a hypothesis worth testing. Pass:
- hypothesis: What pattern you want to test (e.g., "trader increases size after losses")
- metric: What to measure (e.g., "position size change", "win rate", "P&L impact")
- comparison: What to compare (e.g., "after wins vs after losses", "morning vs afternoon")

Returns:
- statistical_significance: p-value and confidence interval
- effect_size: How large the difference is
- affected_trades: Which trades show this pattern
- financial_impact: Dollar value of the pattern
- recommendation: Specific, actionable advice

CRITICAL: You must provide the analysis approach. This tool executes YOUR statistical test.
""",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "hypothesis": {
                                "type": "string",
                                "description": "The pattern you want to test (e.g., 'Position size increases after losses')"
                            },
                            "analysis_code": {
                                "type": "string",
                                "description": "Python code to test this hypothesis. Must set 'result' dict with: detected (bool), significance (float), effect_size (float), affected_trades (list), financial_impact (float)"
                            }
                        },
                        "required": ["hypothesis", "analysis_code"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "fetch_ohlcv_data",
                    "description": """Fetch OHLCV (candlestick) data for any symbol and time range.
                    
Use this when you need price data for analysis:
- Analyzing entry/exit quality vs market conditions
- Calculating technical indicators
- Understanding price action during trade periods
- Market context analysis

ROUTING LOGIC:
- **Crypto symbols** (contain '/' or '_'): Uses Binance Vision → CCXT fallback
- **Stock symbols**: Uses Polygon Flat Files
- **Auto-detects** asset type and exchanges

PARAMETERS:
- symbol: Trading pair (e.g., 'BTC/USDT', 'DOGE_USDT/USDT', 'AAPL')
- start_time: ISO datetime string (e.g., '2024-01-01T00:00:00')
- end_time: ISO datetime string (e.g., '2024-01-02T23:59:59')
- timeframe: Candle interval - '1m', '5m', '15m', '1h', '4h', '1d' (default: '1m')

RETURNS:
List of OHLCV candles with: timestamp, open, high, low, close, volume
Returns empty list if data unavailable (e.g., future dates in paper trading)

EXAMPLE:
fetch_ohlcv_data(symbol='DOGE_USDT/USDT', start_time='2024-09-01T00:00:00', end_time='2024-09-01T23:59:59', timeframe='1m')
""",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "symbol": {"type": "string", "description": "Trading symbol (crypto or stock)"},
                            "start_time": {"type": "string", "description": "Start datetime in ISO format"},
                            "end_time": {"type": "string", "description": "End datetime in ISO format"},
                            "timeframe": {"type": "string", "description": "Candle timeframe", "default": "1m"}
                        },
                        "required": ["symbol", "start_time", "end_time"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "fetch_aggtrades_data",
                    "description": """Fetch aggregated trades data for crypto symbols (more granular than OHLCV).
                    
Use this when you need detailed trade-level data:
- Analyzing exact entry/exit prices vs market microstructure
- Understanding bid/ask spreads and market impact
- Volume-weighted analysis
- Order flow analysis

LIMITATIONS:
- **Crypto only**: AggTrades not available for stocks
- **Large datasets**: Use judiciously for long time ranges

ROUTING LOGIC:
- **Crypto symbols**: Uses Binance Vision aggtrades
- **Stock symbols**: Returns empty (not available)

PARAMETERS:
- symbol: Crypto trading pair (e.g., 'BTC/USDT', 'DOGE_USDT/USDT')
- start_time: ISO datetime string (e.g., '2024-01-01T00:00:00')
- end_time: ISO datetime string (e.g., '2024-01-01T23:59:59')

RETURNS:
List of aggregated trades with: timestamp, price, quantity, is_buyer_maker, agg_trade_id
Returns empty list for stocks or if data unavailable

EXAMPLE:
fetch_aggtrades_data(symbol='DOGE_USDT/USDT', start_time='2024-09-01T00:00:00', end_time='2024-09-01T23:59:59')
""",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "symbol": {"type": "string", "description": "Crypto trading symbol"},
                            "start_time": {"type": "string", "description": "Start datetime in ISO format"},
                            "end_time": {"type": "string", "description": "End datetime in ISO format"}
                        },
                        "required": ["symbol", "start_time", "end_time"]
                    }
                }
            }
        ]

    async def chat(self, user_message: str) -> Dict[str, Any]:
        """Process user message with natural ReAct reasoning loop"""
        
        operations = []
        
        try:
            # Load conversation history
            operations.append({
                "type": "system",
                "name": "Loading conversation history",
                "status": "running",
                "details": f"Session: {self.session_id}"
            })
            
            history = await self._get_conversation_history()
            operations[-1]["status"] = "completed"
            operations[-1]["result"] = f"Loaded {len(history)} previous messages"
            
            # Save user message
            await self._save_message("user", user_message, len(history))
            
            # Build messages for OpenAI
            messages = [{"role": "system", "content": self.system_prompt}]
            
            # Add dynamic context - inject current trades data
            operations.append({
                "type": "data_load",
                "name": "Loading trades data",
                "status": "running",
                "details": "Fetching user's trading history"
            })
            
            context_msg = await self._build_context_message()
            messages.append({"role": "system", "content": context_msg})
            operations[-1]["status"] = "completed"
            operations[-1]["result"] = "Trades data injected into context"
            
            # Add conversation history
            for msg in history:
                messages.append({"role": msg.role, "content": msg.content})
            
            # Add current user message
            messages.append({"role": "user", "content": user_message})
            
            # ReAct Loop: Reason → Act → Observe → Repeat
            max_iterations = 8
            iteration = 0
            final_message = None
            
            tools = self._get_tool_definitions()
            
            while iteration < max_iterations:
                iteration += 1
                
                operations.append({
                    "type": "reasoning",
                    "name": f"Reasoning step {iteration}",
                    "status": "running",
                    "details": "AI analyzing available data and deciding next action"
                })
                
                # Call OpenAI
                response = self.client.chat.completions.create(
                    model="gpt-4o",
                    messages=messages,
                    tools=tools,
                    tool_choice="auto",
                    temperature=0.1
                )
                
                operations[-1]["status"] = "completed"
                operations[-1]["result"] = "Decision made"
                
                response_message = response.choices[0].message
                
                # If AI wants to use tools, execute them
                if response_message.tool_calls:
                    # Add AI's tool calls to history
                    messages.append({
                        "role": "assistant",
                        "content": None,
                        "tool_calls": [tc.model_dump() for tc in response_message.tool_calls]
                    })
                    
                    # Execute each tool
                    for tool_call in response_message.tool_calls:
                        function_name = tool_call.function.name
                        function_args = json.loads(tool_call.function.arguments)
                        
                        operation = {
                            "type": "tool_call",
                            "name": function_name,
                            "status": "running",
                            "details": json.dumps(function_args, indent=2)[:300]
                        }
                        operations.append(operation)
                        
                        logger.info("AI Coach calling function", function=function_name, args=function_args)
                        
                        # Execute the function
                        try:
                            if function_name == "get_trades_summary":
                                function_response = await self._get_trades_summary(function_args.get("days_back", 90))
                            elif function_name == "execute_python":
                                function_response = await self._execute_python(function_args.get("code", ""))
                            elif function_name == "get_trade_ohlcv":
                                function_response = await self._get_trade_ohlcv(
                                    function_args.get("trade_id"),
                                    function_args.get("timeframe", "5m")
                                )
                            elif function_name == "discover_patterns":
                                function_response = await self._discover_patterns(
                                    function_args.get("hypothesis"),
                                    function_args.get("analysis_code")
                                )
                            elif function_name == "fetch_ohlcv_data":
                                function_response = await self._fetch_ohlcv_data(
                                    function_args.get("symbol"),
                                    function_args.get("start_time"),
                                    function_args.get("end_time"),
                                    function_args.get("timeframe", "1m")
                                )
                            elif function_name == "fetch_aggtrades_data":
                                function_response = await self._fetch_aggtrades_data(
                                    function_args.get("symbol"),
                                    function_args.get("start_time"),
                                    function_args.get("end_time")
                                )
                            else:
                                function_response = {"error": f"Unknown function: {function_name}"}
                            
                            operations[-1]["status"] = "completed"
                            result_preview = str(function_response)[:200]
                            operations[-1]["result"] = result_preview if len(result_preview) < 200 else result_preview + "..."
                            
                        except Exception as e:
                            logger.error("Function execution failed", function=function_name, error=str(e))
                            function_response = {"error": str(e)}
                            operations[-1]["status"] = "failed"
                            operations[-1]["result"] = str(e)
                        
                        # Add tool result to messages (convert to JSON-safe format)
                        try:
                            content_str = json.dumps(function_response)
                        except (TypeError, ValueError) as e:
                            # Handle non-serializable results (like tuple keys in dicts)
                            content_str = json.dumps({"result": str(function_response)[:500], "note": "Result converted to string (contains non-JSON types)"})
                        
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": content_str
                        })
                    
                    # Continue loop - AI will see results and decide next action
                    continue
                
                else:
                    # No more tool calls - AI has final answer
                    final_message = response_message.content
                    break
            
            if not final_message:
                final_message = "Analysis reached maximum iterations. Please try rephrasing your question or breaking it into smaller parts."
            
            # Save assistant response
            await self._save_message("assistant", final_message, len(history) + 1)
            
            logger.info("AI Coach chat completed", 
                       user_id=self.user_id, 
                       session_id=self.session_id,
                       iterations=iteration)
            
            return {
                "message": final_message,
                "session_id": self.session_id,
                "thinking": {
                    "operations": operations,
                    "iterations": iteration
                }
            }
            
        except Exception as e:
            logger.error("AI Coach chat failed", error=str(e), traceback=traceback.format_exc())
            raise Exception(f"Failed to process your message: {str(e)}")

    async def chat_stream(self, user_message: str) -> AsyncGenerator[str, None]:
        """
        Stream chat processing with live operation updates.
        Yields SSE-formatted events for real-time UI updates.
        """
        
        logger.info("Chat stream started", user_id=self.user_id, session_id=self.session_id)
        
        try:
            # Stream: Loading history
            yield self._format_sse({
                "type": "operation",
                "data": {
                    "type": "system",
                    "name": "Loading conversation history",
                    "status": "running",
                    "details": f"Session: {self.session_id}"
                }
            })
            await asyncio.sleep(0)  # Allow other requests to process
            
            history = await self._get_conversation_history()
            
            yield self._format_sse({
                "type": "operation",
                "data": {
                    "type": "system",
                    "name": "Loading conversation history",
                    "status": "completed",
                    "result": f"Loaded {len(history)} messages"
                }
            })
            await asyncio.sleep(0)
            
            # Save user message
            await self._save_message("user", user_message, len(history))
            
            # Build messages
            messages = [{"role": "system", "content": self.system_prompt}]
            
            # Stream: Loading context
            yield self._format_sse({
                "type": "operation",
                "data": {
                    "type": "data_load",
                    "name": "Building trading profile",
                    "status": "running",
                    "details": "Analyzing trading history and patterns"
                }
            })
            await asyncio.sleep(0)
            
            context_msg = await self._build_rich_context()
            messages.append({"role": "system", "content": context_msg})
            
            yield self._format_sse({
                "type": "operation",
                "data": {
                    "type": "data_load",
                    "name": "Building trading profile",
                    "status": "completed",
                    "result": "Profile ready with pre-computed insights"
                }
            })
            await asyncio.sleep(0)
            
            # Add history and current message
            for msg in history:
                messages.append({"role": msg.role, "content": msg.content})
            messages.append({"role": "user", "content": user_message})
            
            # ReAct Loop with streaming
            max_iterations = 10
            iteration = 0
            final_message = None
            tools = self._get_tool_definitions()
            
            while iteration < max_iterations:
                iteration += 1
                
                # Stream: Reasoning
                yield self._format_sse({
                    "type": "operation",
                    "data": {
                        "type": "reasoning",
                        "name": f"Reasoning cycle {iteration}",
                        "status": "running",
                        "details": "AI analyzing data and planning next action"
                    }
                })
                await asyncio.sleep(0)
                
                # Call OpenAI (async to avoid blocking the event loop)
                try:
                    logger.info(f"[STREAM] Calling OpenAI API - iteration {iteration}")
                    response = await self.async_client.chat.completions.create(
                        model="gpt-4o",
                        messages=messages,
                        tools=tools,
                        tool_choice="auto",
                        temperature=0.1
                    )
                    logger.info(f"[STREAM] OpenAI API response received - iteration {iteration}")
                except Exception as e:
                    logger.error(f"[STREAM] OpenAI API call failed: {type(e).__name__}: {str(e)}", exc_info=True)
                    error_msg = f"⚠️ **Analysis Failed**\n\nOpenAI API error: {str(e)}\n\nPlease try again."
                    yield self._format_sse({"type": "final_message", "data": {"message": error_msg}})
                    return
                
                yield self._format_sse({
                    "type": "operation",
                    "data": {
                        "type": "reasoning",
                        "name": f"Reasoning cycle {iteration}",
                        "status": "completed",
                        "result": "Decision made"
                    }
                })
                await asyncio.sleep(0)
                
                response_message = response.choices[0].message
                
                # Tool execution
                if response_message.tool_calls:
                    messages.append({
                        "role": "assistant",
                        "content": None,
                        "tool_calls": [tc.model_dump() for tc in response_message.tool_calls]
                    })
                    
                    for tool_call in response_message.tool_calls:
                        function_name = tool_call.function.name
                        function_args = json.loads(tool_call.function.arguments)
                        
                        # Stream: Tool start
                        event_data = self._format_sse({
                            "type": "operation",
                            "data": {
                                "type": "tool_call",
                                "name": function_name,
                                "status": "running",
                                "details": json.dumps(function_args, indent=2)[:300]
                            }
                        })
                        logger.info(f"[STREAM] Yielding operation start: {function_name}")
                        yield event_data
                        await asyncio.sleep(0)
                        
                        logger.info("AI Coach calling function", function=function_name, args=function_args)
                        
                        # Execute function
                        try:
                            if function_name == "get_trades_summary":
                                function_response = await self._get_trades_summary(function_args.get("days_back", 90))
                            elif function_name == "execute_python":
                                function_response = await self._execute_python(function_args.get("code", ""))
                                
                                # AUTO-RETRY: If Python execution failed, add helpful error context with common fixes
                                if not function_response.get("success"):
                                    error_msg = function_response.get("error", "Unknown error")
                                    fix_hint = "⚠️ Python Error Detected!\n\n" + f"Error: {error_msg}\n\n"
                                    
                                    # COMMON ERRORS DATABASE with exact fixes
                                    if "'Index' object has no attribute 'abs'" in error_msg or "'TimedeltaIndex' object has no attribute 'abs'" in error_msg:
                                        fix_hint += (
                                            "**PANDAS FIX**: Use np.abs() instead of .abs() on Index objects:\n\n"
                                            "```python\n"
                                            "# ❌ WRONG:\n"
                                            "entry_index = (timestamps - entry_time).abs().argmin()\n\n"
                                            "# ✅ CORRECT:\n"
                                            "time_diffs = np.abs((timestamps - entry_time).total_seconds())\n"
                                            "entry_index = time_diffs.argmin()\n"
                                            "```"
                                        )
                                    elif "name" in error_msg.lower() and "not defined" in error_msg.lower():
                                        var_name = error_msg.split("'")[1] if "'" in error_msg else "variable"
                                        fix_hint += (
                                            f"**SCOPE FIX**: Variable '{var_name}' not defined in current execution.\n\n"
                                            f"Each execute_python call starts fresh. Re-define variables:\n"
                                            f"```python\n"
                                            f"df = pd.DataFrame(trades_data)\n"
                                            f"last_100 = df.nlargest(100, 'filled_at')\n"
                                            f"```"
                                        )
                                    elif "list indices must be integers" in error_msg.lower() or "float' object cannot be interpreted as an integer" in error_msg.lower():
                                        fix_hint += (
                                            "**INDEX FIX**: Array index must be int, not float:\n\n"
                                            "```python\n"
                                            "# ❌ WRONG:\n"
                                            "value = rsi[entry_index]  # entry_index might be float\n\n"
                                            "# ✅ CORRECT:\n"
                                            "value = rsi[int(entry_index)]\n"
                                            "```"
                                        )
                                    elif "cannot convert the series to" in error_msg.lower() or "truth value" in error_msg.lower():
                                        fix_hint += (
                                            "**BOOLEAN FIX**: Use .any() or .all() for Series in conditionals:\n\n"
                                            "```python\n"
                                            "# ❌ WRONG:\n"
                                            "if df['column'] > 0:\n\n"
                                            "# ✅ CORRECT:\n"
                                            "if (df['column'] > 0).any():\n"
                                            "```"
                                        )
                                    else:
                                        fix_hint += "Check the error and try again with the corrected code."
                                    
                                    function_response["fix_hint"] = fix_hint
                                
                                # Check if image was supposed to be generated but result doesn't have it
                                if function_response.get("success") and isinstance(function_response.get("result"), dict):
                                    if "image" in function_response["result"]:
                                        image_file = function_response["result"]["image"]
                                        # Check if it's a weird path like "sandbox:/mnt/data/..."
                                        if image_file.startswith("sandbox:") or "/mnt/data/" in image_file:
                                            function_response["result"]["image_error"] = (
                                                f"⚠️ IMAGE SAVE ERROR!\n\n"
                                                f"You tried to save to: {image_file}\n\n"
                                                f"**WRONG PATH!** You must use the workspace_dir variable:\n"
                                                f"```python\n"
                                                f"plt.savefig(f'{{workspace_dir}}/my_chart.png')\n"
                                                f"result = {{'image': 'my_chart.png'}}  # Just filename!\n"
                                                f"```\n\n"
                                                f"Try again with the correct path!"
                                            )
                            elif function_name == "get_trade_ohlcv":
                                function_response = await self._get_trade_ohlcv(
                                    function_args.get("trade_id"),
                                    function_args.get("timeframe", "5m")
                                )
                            elif function_name == "discover_patterns":
                                function_response = await self._discover_patterns(
                                    function_args.get("hypothesis"),
                                    function_args.get("analysis_code")
                                )
                            elif function_name == "fetch_ohlcv_data":
                                function_response = await self._fetch_ohlcv_data(
                                    function_args.get("symbol"),
                                    function_args.get("start_time"),
                                    function_args.get("end_time"),
                                    function_args.get("timeframe", "1m")
                                )
                            elif function_name == "fetch_aggtrades_data":
                                function_response = await self._fetch_aggtrades_data(
                                    function_args.get("symbol"),
                                    function_args.get("start_time"),
                                    function_args.get("end_time")
                                )
                            else:
                                function_response = {"error": f"Unknown function: {function_name}"}
                            
                            result_preview = str(function_response)[:200]
                            
                            # Stream: Tool complete
                            event_data = self._format_sse({
                                "type": "operation",
                                "data": {
                                    "type": "tool_call",
                                    "name": function_name,
                                    "status": "completed",
                                    "result": result_preview if len(result_preview) < 200 else result_preview + "..."
                                }
                            })
                            logger.info(f"[STREAM] Yielding operation complete: {function_name}")
                            yield event_data
                            await asyncio.sleep(0)
                            
                        except Exception as e:
                            logger.error("Function execution failed", function=function_name, error=str(e))
                            function_response = {"error": str(e)}
                            
                            # Stream: Tool failed
                            yield self._format_sse({
                                "type": "operation",
                                "data": {
                                    "type": "tool_call",
                                    "name": function_name,
                                    "status": "failed",
                                    "result": str(e)
                                }
                            })
                            await asyncio.sleep(0)
                            
                            # Send failure message and stop
                            error_msg = f"⚠️ **Analysis Failed**\n\nI encountered an error while trying to {function_name.replace('_', ' ')}:\n\n```\n{str(e)[:300]}\n```\n\nPlease try rephrasing your request or asking a different question."
                            yield self._format_sse({"type": "final_message", "data": {"message": error_msg}})
                            await asyncio.sleep(0)
                            
                            # Save failure message
                            await self._save_message("assistant", error_msg, iteration + 1)
                            
                            yield self._format_sse({"type": "done"})
                            await asyncio.sleep(0)
                            return
                        
                        # Add tool result to messages (convert to JSON-safe format)
                        try:
                            content_str = json.dumps(function_response)
                        except (TypeError, ValueError) as e:
                            # Handle non-serializable results (like tuple keys in dicts)
                            content_str = json.dumps({"result": str(function_response)[:500], "note": "Result converted to string (contains non-JSON types)"})
                        
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": content_str
                        })
                    
                    continue
                
                else:
                    # AI has final answer
                    final_message = response_message.content
                    
                    # Quality control: check for vague responses
                    if self._is_vague_response(final_message) and iteration < max_iterations - 1:
                        # Stream: Quality check failed
                        yield self._format_sse({
                            "type": "operation",
                            "data": {
                                "type": "quality_control",
                                "name": "Response quality check",
                                "status": "failed",
                                "result": "Response lacks specificity. Re-analyzing..."
                            }
                        })
                        await asyncio.sleep(0)
                        
                        messages.append({
                            "role": "system",
                            "content": "Your response lacks specific numbers and statistical significance. Re-run analysis with exact figures, confidence intervals, and concrete recommendations."
                        })
                        continue
                    
                    break
            
            if not final_message:
                final_message = "Analysis reached maximum iterations. Please try breaking your question into smaller parts."
            
            # Save assistant response
            await self._save_message("assistant", final_message, len(history) + 1)
            
            # Stream: Final message (clean up any bad image paths in the message text)
            import re
            cleaned_message = final_message
            # Fix markdown image paths: ![alt](sandbox:/path/to/file.png) -> ![alt](filename.png)
            cleaned_message = re.sub(
                r'!\[([^\]]*)\]\((?:sandbox:|/mnt/data/|/api/v1/coach/image/[^/]+/[^/]+/)*([^/)]+\.(?:png|jpg|jpeg|gif|svg))\)',
                r'![\1](\2)',
                cleaned_message
            )
            
            yield self._format_sse({
                "type": "final_message",
                "data": {
                    "message": cleaned_message,
                    "session_id": self.session_id,
                    "iterations": iteration
                }
            })
            await asyncio.sleep(0)
            
            # Stream: Done
            yield self._format_sse({"type": "done"})
            await asyncio.sleep(0)
            
        except Exception as e:
            logger.error("AI Coach stream failed", error=str(e), traceback=traceback.format_exc())
            yield self._format_sse({
                "type": "error",
                "data": {"error": str(e)}
            })

    def _format_sse(self, data: dict) -> str:
        """Format data as Server-Sent Event"""
        return f"data: {json.dumps(data)}\n\n"

    def _is_vague_response(self, message: str) -> bool:
        """Detect vague/unhelpful responses - enhanced with statistical markers"""
        import re
        
        if not message or len(message) < 100:
            return True
        
        # Count vague qualifiers
        vague_phrases = [
            "might", "could", "possibly", "seems like", "seems to",
            "around", "approximately", "roughly", "maybe", "perhaps",
            "likely", "probably", "i think", "appears to", "suggests"
        ]
        
        message_lower = message.lower()
        vague_count = sum(1 for phrase in vague_phrases if phrase in message_lower)
        
        # Check for concrete numbers and statistics (signs of specificity)
        has_percentages = bool(re.search(r'\d+\.?\d*%', message))
        has_dollar_amounts = bool(re.search(r'\$\d+\.?\d*', message))
        has_decimals = bool(re.search(r'\d+\.\d+', message))
        has_statistics = any(term in message_lower for term in [
            'p-value', 'confidence', 'significance', 'standard deviation',
            'correlation', 'r-squared', 'alpha', 'beta', 'sharpe',
            'statistical', 'coefficient', 'z-score', 't-test'
        ])
        has_specific_counts = bool(re.search(r'\d+ trades?', message, re.IGNORECASE))
        
        # Calculate specificity score
        specificity_indicators = [
            has_percentages,
            has_dollar_amounts,
            has_decimals,
            has_statistics,
            has_specific_counts
        ]
        specificity_score = sum(specificity_indicators)
        
        # Vague if: many qualifiers (≥3) AND low specificity (≤1)
        is_vague = vague_count >= 3 and specificity_score <= 1
        
        # Also vague if NO concrete numbers at all and has any vague language
        no_numbers = not any([has_percentages, has_dollar_amounts, has_decimals, has_specific_counts])
        is_vague = is_vague or (no_numbers and vague_count >= 2)
        
        return is_vague

    async def _build_context_message(self) -> str:
        """Build dynamic context with current trades data"""
        
        # Get all user trades
        trades = self.db.query(Trade).filter(
            Trade.user_id == self.user_id
        ).order_by(desc(Trade.filled_at)).all()
        
        trades_data = []
        for trade in trades:
            trades_data.append({
                "id": trade.id,
                "symbol": trade.symbol,
                "side": trade.side,
                "qty": float(trade.qty) if trade.qty else 0,
                "avg_price": float(trade.avg_price) if trade.avg_price else 0,
                "fees": float(trade.fees) if trade.fees else 0,
                "pnl": float(trade.pnl) if trade.pnl else 0,
                "filled_at": trade.filled_at.isoformat() if trade.filled_at else None,
                "submitted_at": trade.submitted_at.isoformat() if trade.submitted_at else None,
                "venue": trade.venue,
                "account": trade.account
            })
        
        context = f"""CURRENT DATA AVAILABLE:

Total Trades: {len(trades_data)}
Most Recent: {trades_data[0]['symbol'] if trades_data else 'None'} on {trades_data[0]['filled_at'] if trades_data else 'N/A'}

All trades are pre-loaded in your Python environment as 'trades_data'.
You can immediately start analyzing without fetching data first."""
        
        return context

    async def _build_rich_context(self) -> str:
        """Build context with pre-computed insights"""
        
        trades = self.db.query(Trade).filter(
            Trade.user_id == self.user_id
        ).order_by(desc(Trade.filled_at)).all()
        
        if not trades:
            return "No trading history available. Unable to analyze."
        
        # Pre-compute key metrics
        total_pnl = sum(float(t.pnl) for t in trades if t.pnl)
        win_rate = len([t for t in trades if t.pnl and float(t.pnl) > 0]) / len(trades)
        
        # Detect streak
        recent_streak = self._detect_streak(trades[:10])
        
        # Worst performer
        worst_symbol = self._worst_performing_symbol(trades)
        
        # Time pattern hint
        time_hint = self._quick_time_analysis(trades)
        
        context = f"""TRADING PROFILE SNAPSHOT:
Total Trades: {len(trades)}
Net P&L: ${total_pnl:,.2f}
Win Rate: {win_rate:.1%}
Most Recent: {trades[0].symbol} ({float(trades[0].pnl):+.2f}) on {trades[0].filled_at.strftime('%Y-%m-%d %H:%M')}

⚠️ IMMEDIATE OBSERVATIONS:
- Current streak: {recent_streak}
- Worst performer: {worst_symbol['symbol']} ({worst_symbol['win_rate']:.1%} win rate, ${worst_symbol['pnl']:,.2f})
- Time pattern: {time_hint}

All trades pre-loaded as 'trades_data' in Python environment. Focus on actionable, quantified findings."""
        
        return context

    def _detect_streak(self, recent_trades: List[Trade]) -> str:
        """Detect current winning/losing streak"""
        if not recent_trades:
            return "No recent trades"
        
        streak = 0
        streak_type = None
        
        for trade in recent_trades:
            if not trade.pnl:
                break
            
            pnl = float(trade.pnl)
            current_type = "win" if pnl > 0 else "loss"
            
            if streak_type is None:
                streak_type = current_type
                streak = 1
            elif streak_type == current_type:
                streak += 1
            else:
                break
        
        return f"{streak} {streak_type}{'s' if streak > 1 else ''} in a row"

    def _worst_performing_symbol(self, trades: List[Trade]) -> dict:
        """Find worst performing symbol"""
        
        symbol_stats = defaultdict(lambda: {"wins": 0, "total": 0, "pnl": 0})
        
        for trade in trades:
            if not trade.pnl:
                continue
            symbol = trade.symbol
            symbol_stats[symbol]["total"] += 1
            symbol_stats[symbol]["pnl"] += float(trade.pnl)
            if float(trade.pnl) > 0:
                symbol_stats[symbol]["wins"] += 1
        
        if not symbol_stats:
            return {"symbol": "N/A", "win_rate": 0, "pnl": 0}
        
        # Find symbol with lowest win rate (min 5 trades)
        qualified = {s: stats for s, stats in symbol_stats.items() if stats["total"] >= 5}
        
        if not qualified:
            return {"symbol": "N/A", "win_rate": 0, "pnl": 0}
        
        worst = min(qualified.items(), key=lambda x: x[1]["wins"] / x[1]["total"])
        
        return {
            "symbol": worst[0],
            "win_rate": worst[1]["wins"] / worst[1]["total"],
            "pnl": worst[1]["pnl"]
        }

    def _quick_time_analysis(self, trades: List[Trade]) -> str:
        """Quick time-of-day pattern hint"""
        
        hour_pnl = defaultdict(float)
        
        for trade in trades:
            if trade.filled_at and trade.pnl:
                hour = trade.filled_at.hour
                hour_pnl[hour] += float(trade.pnl)
        
        if not hour_pnl:
            return "Insufficient data"
        
        best_hour = max(hour_pnl.items(), key=lambda x: x[1])
        worst_hour = min(hour_pnl.items(), key=lambda x: x[1])
        
        return f"Best hour: {best_hour[0]}:00 (+${best_hour[1]:.0f}), Worst: {worst_hour[0]}:00 (${worst_hour[1]:.0f})"

    async def _get_trades_summary(self, days_back: int = 90) -> Dict[str, Any]:
        """Get aggregated trading statistics"""
        
        cutoff_date = datetime.now() - timedelta(days=days_back)
        
        trades = self.db.query(Trade).filter(
            Trade.user_id == self.user_id,
            Trade.filled_at >= cutoff_date
        ).all()
        
        if not trades:
            return {
                "total_trades": 0,
                "message": f"No trades found in the last {days_back} days"
            }
        
        total_trades = len(trades)
        winning_trades = len([t for t in trades if t.pnl and float(t.pnl) > 0])
        losing_trades = len([t for t in trades if t.pnl and float(t.pnl) < 0])
        win_rate = (winning_trades / total_trades) if total_trades > 0 else 0
        
        total_pnl = sum(float(t.pnl) if t.pnl else 0 for t in trades)
        avg_win = sum(float(t.pnl) for t in trades if t.pnl and float(t.pnl) > 0) / winning_trades if winning_trades > 0 else 0
        avg_loss = sum(float(t.pnl) for t in trades if t.pnl and float(t.pnl) < 0) / losing_trades if losing_trades > 0 else 0
        
        # Symbol breakdown
        symbol_stats = {}
        for trade in trades:
            symbol = trade.symbol
            if symbol not in symbol_stats:
                symbol_stats[symbol] = {
                    "count": 0,
                    "pnl": 0,
                    "wins": 0,
                    "losses": 0,
                    "win_rate": 0
                }
            
            symbol_stats[symbol]["count"] += 1
            symbol_stats[symbol]["pnl"] += float(trade.pnl) if trade.pnl else 0
            
            if trade.pnl and float(trade.pnl) > 0:
                symbol_stats[symbol]["wins"] += 1
            elif trade.pnl and float(trade.pnl) < 0:
                symbol_stats[symbol]["losses"] += 1
        
        # Calculate win rates
        for symbol, stats in symbol_stats.items():
            if stats["count"] > 0:
                stats["win_rate"] = round(stats["wins"] / stats["count"], 3)
        
        return {
            "period_days": days_back,
            "total_trades": total_trades,
            "winning_trades": winning_trades,
            "losing_trades": losing_trades,
            "win_rate": round(win_rate, 3),
            "total_pnl": round(total_pnl, 2),
            "avg_win": round(avg_win, 2),
            "avg_loss": round(avg_loss, 2),
            "profit_factor": round(abs(avg_win / avg_loss), 2) if avg_loss != 0 else 0,
            "symbol_breakdown": symbol_stats
        }

    async def _execute_python(self, code: str) -> Dict[str, Any]:
        """Execute Python code with security and pre-loaded data"""
        
        # Security: Check for forbidden imports/operations
        # Only check for actual import statements or function calls, not substrings
        import re
        FORBIDDEN_PATTERNS = [
            r'\bimport\s+os\b',
            r'\bimport\s+sys\b', 
            r'\bimport\s+subprocess\b',
            r'\bfrom\s+os\b',
            r'\bfrom\s+sys\b',
            r'\bopen\s*\(',
            r'\beval\s*\(',
            r'\bexec\s*\(',
        ]
        for pattern in FORBIDDEN_PATTERNS:
            if re.search(pattern, code):
                return {"error": f"Forbidden operation detected: {pattern}"}
        
        # Get all trades
        trades = self.db.query(Trade).filter(
            Trade.user_id == self.user_id
        ).order_by(desc(Trade.filled_at)).all()
        
        # Convert to serializable format with datetime objects (not strings!)
        from datetime import datetime as dt_class
        trades_data = []
        for trade in trades:
            trades_data.append({
                "id": trade.id,
                "symbol": trade.symbol,
                "side": trade.side,
                "qty": float(trade.qty) if trade.qty else 0,
                "avg_price": float(trade.avg_price) if trade.avg_price else 0,
                "fees": float(trade.fees) if trade.fees else 0,
                "pnl": float(trade.pnl) if trade.pnl else 0,
                # Keep as datetime objects for Python calculations
                "filled_at": trade.filled_at if trade.filled_at else None,
                "submitted_at": trade.submitted_at if trade.submitted_at else None,
                "venue": trade.venue,
                "account": trade.account
            })
        
        # Create get_ohlcv helper function (synchronous wrapper with smart caching)
        def get_ohlcv_helper(symbol: str, start_time, end_time, timeframe: str = '1m'):
            """Helper function available in Python execution - fetches OHLCV data with intelligent caching.
            
            Args:
                symbol: Trading symbol (e.g., 'DOGE_USDT/USDT', 'AAPL', 'BTC/USDT')
                start_time: Start datetime (ISO string or datetime object)
                end_time: End datetime (ISO string or datetime object)
                timeframe: Candle interval - '1m', '5m', '15m', '1h' (default: '1m')
            
            Returns:
                List of OHLCV candles with timestamp, open, high, low, close, volume
                Returns empty list if data unavailable (e.g., paper trading with future dates)
            """
            import asyncio
            import pickle
            
            # Create cache key
            cache_key = f"{symbol}_{timeframe}_{start_time}_{end_time}"
            
            # Check memory cache first
            if cache_key in self.ohlcv_cache:
                return self.ohlcv_cache[cache_key]
            
            # Check disk cache (persistent per session)
            cache_file = self.workspace_dir / f"{cache_key.replace('/', '_').replace(':', '_')}.pkl"
            if cache_file.exists():
                try:
                    with open(cache_file, 'rb') as f:
                        result = pickle.load(f)
                        self.ohlcv_cache[cache_key] = result
                        return result
                except:
                    pass
            
            # Fetch fresh data (use CCXT as fallback for crypto, Polygon for stocks)
            try:
                loop = asyncio.new_event_loop()
                result = loop.run_until_complete(
                    self.ohlcv_service.get_ohlcv(
                        symbol=symbol,
                        start_time=start_time,
                        end_time=end_time,
                        timeframe=timeframe,
                        exchange="polygon" if "_" not in symbol else "binance",  # Polygon for stocks, binance for crypto
                        asset_type="stock" if "_" not in symbol else "crypto"
                    )
                )
                loop.close()
                
                # Cache the result
                if result:
                    self.ohlcv_cache[cache_key] = result
                    with open(cache_file, 'wb') as f:
                        pickle.dump(result, f)
                
                return result
            except Exception as e:
                return []  # Return empty list on error
        
        # Create get_aggtrades helper function (synchronous wrapper with smart caching)
        def get_aggtrades_helper(symbol: str, start_time, end_time):
            """Helper function available in Python execution - fetches aggregated trades data with intelligent caching.
            
            Args:
                symbol: Trading symbol (e.g., 'DOGE_USDT/USDT', 'BTC/USDT') - crypto only
                start_time: Start datetime (ISO string or datetime object)
                end_time: End datetime (ISO string or datetime object)
            
            Returns:
                List of aggregated trade records with timestamp, price, quantity, is_buyer_maker
                Returns empty list if data unavailable or for stocks
            """
            import asyncio
            import pickle
            
            # Create cache key
            cache_key = f"aggtrades_{symbol}_{start_time}_{end_time}"
            
            # Check memory cache first
            if cache_key in self.ohlcv_cache:
                return self.ohlcv_cache[cache_key]
            
            # Check disk cache (persistent per session)
            cache_file = self.workspace_dir / f"aggtrades_{cache_key.replace('/', '_').replace(':', '_')}.pkl"
            if cache_file.exists():
                try:
                    with open(cache_file, 'rb') as f:
                        result = pickle.load(f)
                        self.ohlcv_cache[cache_key] = result
                        return result
                except:
                    pass
            
            # Fetch fresh data (only for crypto symbols)
            try:
                loop = asyncio.new_event_loop()
                result = loop.run_until_complete(
                    self.ohlcv_service.get_aggtrades(
                        symbol=symbol,
                        start_time=start_time,
                        end_time=end_time,
                        exchange="binance",
                        asset_type="crypto"
                    )
                )
                loop.close()
                
                # Cache the result
                if result:
                    self.ohlcv_cache[cache_key] = result
                    with open(cache_file, 'wb') as f:
                        pickle.dump(result, f)
                
                return result
            except Exception as e:
                return []  # Return empty list on error
        
        # Build context - start with persistent context from previous executions
        context = {
            **self.python_context,  # Include variables from previous executions!
            "trades_data": trades_data,
            "total_trades": len(trades_data),
            "get_ohlcv": get_ohlcv_helper,
            "get_aggtrades": get_aggtrades_helper,
            "workspace_dir": str(self.workspace_dir)  # So code can save images here
        }
        
        # Execute code in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, self.code_executor.execute, code, context)
        
        # Check if result contains image path and convert to URL
        if result.get("success") and isinstance(result.get("result"), dict):
            if "image" in result["result"]:
                image_filename = result["result"]["image"]
                
                # Clean up bad paths (AI sometimes returns wrong paths)
                from pathlib import Path
                # If it contains "sandbox:", "/mnt/", "/api/v1/", or other path indicators, extract just filename
                if any(x in image_filename for x in ["sandbox:", "/mnt/", "/api/v1/", "http://", "https://"]):
                    # Extract just the filename from any complex path
                    image_filename = Path(image_filename).name
                    result["result"]["image"] = image_filename  # Update to just filename
                    logger.warning(f"AI returned complex image path, cleaned to: {image_filename}")
                
                # If it's just a filename, prepend workspace path
                if not image_filename.startswith("/") and ":" not in image_filename:
                    image_path = self.workspace_dir / image_filename
                    # Create URL path that frontend can access (includes user_id for path-based security)
                    result["result"]["image_url"] = f"/api/v1/coach/image/{self.user_id}/{self.session_id}/{image_filename}"
                    result["result"]["image_path"] = str(image_path)
        
        # Save variables to persistent context for next execution (except functions and large data)
        if result.get("success") and "context" in result:
            # Update persistent context with new variables
            for key, value in result["context"].items():
                # Only save simple variables (not functions, not trades_data)
                if key not in ["get_ohlcv", "get_aggtrades", "trades_data", "total_trades"] and not callable(value):
                    try:
                        # Test if it's serializable
                        import pickle
                        pickle.dumps(value)
                        self.python_context[key] = value
                    except:
                        pass  # Skip non-serializable values
        
        return result

    async def _get_trade_ohlcv(self, trade_id: str, timeframe: str = '1m') -> Dict[str, Any]:
        """Get OHLCV data for a specific trade"""
        
        trade = self.db.query(Trade).filter(
            Trade.id == trade_id,
            Trade.user_id == self.user_id
        ).first()
        
        if not trade:
            return {"error": f"Trade {trade_id} not found"}
        
        if not trade.filled_at or not trade.submitted_at:
            return {"error": "Trade missing entry/exit timestamps"}
        
        # Get OHLCV from 30min before entry to 30min after exit
        start_time = trade.filled_at - timedelta(minutes=30)
        end_time = trade.submitted_at + timedelta(minutes=30)
        
        ohlcv_data = await self.ohlcv_service.get_ohlcv(
            symbol=trade.symbol,
            start_time=start_time,
            end_time=end_time,
            timeframe=timeframe,
            exchange="polygon" if "_" not in trade.symbol else "binance",
            asset_type="stock" if "_" not in trade.symbol else "crypto"
        )
        
        return {
            "trade_id": trade_id,
            "symbol": trade.symbol,
            "entry_time": trade.filled_at.isoformat(),
            "exit_time": trade.submitted_at.isoformat(),
            "timeframe": timeframe,
            "candles": ohlcv_data,
            "candle_count": len(ohlcv_data)
        }

    async def _discover_patterns(self, hypothesis: str, analysis_code: str) -> Dict[str, Any]:
        """
        AI-driven pattern discovery - executes custom statistical analysis
        The AI provides the hypothesis and analysis code to test it
        """
        
        logger.info("Pattern discovery requested", hypothesis=hypothesis)
        
        # Get all trades for analysis
        trades = self.db.query(Trade).filter(
            Trade.user_id == self.user_id
        ).order_by(Trade.filled_at).all()
        
        if len(trades) < 20:
            return {
                "error": "Insufficient data for pattern discovery (need at least 20 trades)",
                "hypothesis": hypothesis
            }
        
        # Convert to serializable format with datetime objects (not strings!)
        trades_data = []
        for trade in trades:
            trades_data.append({
                "id": trade.id,
                "symbol": trade.symbol,
                "side": trade.side,
                "qty": float(trade.qty) if trade.qty else 0,
                "avg_price": float(trade.avg_price) if trade.avg_price else 0,
                "fees": float(trade.fees) if trade.fees else 0,
                "pnl": float(trade.pnl) if trade.pnl else 0,
                # Keep as datetime objects for Python calculations
                "filled_at": trade.filled_at if trade.filled_at else None,
                "submitted_at": trade.submitted_at if trade.submitted_at else None,
                "venue": trade.venue,
                "account": trade.account
            })
        
        # Build context with scipy for statistical tests
        context = {
            "trades_data": trades_data,
            "total_trades": len(trades_data),
            "hypothesis": hypothesis
        }
        
        # Execute the AI's analysis code in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        execution_result = await loop.run_in_executor(None, self.code_executor.execute, analysis_code, context)
        
        if not execution_result.get("success"):
            return {
                "error": f"Pattern analysis failed: {execution_result.get('error')}",
                "hypothesis": hypothesis,
                "traceback": execution_result.get("traceback", "")
            }
        
        result = execution_result.get("result")
        
        if not result or not isinstance(result, dict):
            return {
                "error": "Analysis code must return a dict with: detected, significance, effect_size, affected_trades, financial_impact",
                "hypothesis": hypothesis,
                "received": str(result)[:200]
            }
        
        # Validate required fields
        required_fields = ["detected", "significance"]
        missing = [f for f in required_fields if f not in result]
        
        if missing:
            return {
                "error": f"Missing required fields in result: {missing}",
                "hypothesis": hypothesis,
                "received_fields": list(result.keys())
            }
        
        # Add metadata
        result["hypothesis"] = hypothesis
        result["trades_analyzed"] = len(trades_data)
        result["stdout"] = execution_result.get("stdout", "")
        
        # Log significant patterns
        if result.get("detected") and result.get("significance", 1.0) < 0.05:
            logger.info("Significant pattern discovered", 
                       hypothesis=hypothesis,
                       significance=result.get("significance"),
                       financial_impact=result.get("financial_impact"))
        
        return result

    async def _fetch_ohlcv_data(
        self, 
        symbol: str, 
        start_time: str, 
        end_time: str, 
        timeframe: str = "1m"
    ) -> Dict[str, Any]:
        """Fetch OHLCV data for any symbol and time range"""
        
        try:
            # Parse datetime strings
            from datetime import datetime
            start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
            
            # Fetch data using OHLCV service
            ohlcv_data = await self.ohlcv_service.get_ohlcv(
                symbol=symbol,
                timeframe=timeframe,
                start_time=start_dt,
                end_time=end_dt,
                exchange="polygon" if "/" not in symbol and "_" not in symbol else "binance",
                asset_type="stock" if "/" not in symbol and "_" not in symbol else "crypto"
            )
            
            logger.info("Fetched OHLCV data", 
                       symbol=symbol, 
                       timeframe=timeframe,
                       count=len(ohlcv_data),
                       time_range=f"{start_time} to {end_time}")
            
            # Save OHLCV data to workspace as CSV for efficient loading
            import csv
            from pathlib import Path
            
            filename = f"{symbol.replace('/', '_')}_{timeframe}_{start_dt.strftime('%Y%m%d')}_{end_dt.strftime('%Y%m%d')}.csv"
            filepath = self.workspace_dir / filename
            
            with open(filepath, 'w', newline='') as f:
                if ohlcv_data:
                    writer = csv.DictWriter(f, fieldnames=ohlcv_data[0].keys())
                    writer.writeheader()
                    writer.writerows(ohlcv_data)
            
            # Return absolute path string (safe for any working directory)
            return {
                "success": True,
                "symbol": symbol,
                "timeframe": timeframe,
                "candles": len(ohlcv_data),
                "file": str(filepath.absolute()),
                "time_range": f"{start_time} to {end_time}",
                "message": f"Saved {len(ohlcv_data)} candles. Use pd.read_csv(r'{filepath.absolute()}') to load."
            }
            
        except Exception as e:
            logger.error("Failed to fetch OHLCV data", 
                        error=str(e), 
                        symbol=symbol, 
                        start_time=start_time, 
                        end_time=end_time)
            return {
                "success": False,
                "error": str(e),
                "symbol": symbol,
                "timeframe": timeframe
            }

    async def _fetch_aggtrades_data(
        self, 
        symbol: str, 
        start_time: str, 
        end_time: str
    ) -> Dict[str, Any]:
        """Fetch aggregated trades data for crypto symbols"""
        
        try:
            # Parse datetime strings
            from datetime import datetime
            start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
            
            # Check if it's a crypto symbol
            if "/" not in symbol and "_" not in symbol:
                return {
                    "success": False,
                    "error": "AggTrades only available for crypto symbols",
                    "symbol": symbol,
                    "data": []
                }
            
            # Fetch data using OHLCV service
            aggtrades_data = await self.ohlcv_service.get_aggtrades(
                symbol=symbol,
                start_time=start_dt,
                end_time=end_dt,
                exchange="binance",
                asset_type="crypto"
            )
            
            logger.info("Fetched aggtrades data", 
                       symbol=symbol, 
                       count=len(aggtrades_data),
                       time_range=f"{start_time} to {end_time}")
            
            return {
                "success": True,
                "symbol": symbol,
                "count": len(aggtrades_data),
                "data": aggtrades_data,
                "time_range": f"{start_time} to {end_time}"
            }
            
        except Exception as e:
            logger.error("Failed to fetch aggtrades data", 
                        error=str(e), 
                        symbol=symbol, 
                        start_time=start_time, 
                        end_time=end_time)
            return {
                "success": False,
                "error": str(e),
                "symbol": symbol,
                "data": []
            }

    async def _get_conversation_history(self) -> List[CoachConversation]:
        """Get recent conversation history"""
        return self.db.query(CoachConversation).filter(
            CoachConversation.user_id == self.user_id,
            CoachConversation.session_id == self.session_id
        ).order_by(CoachConversation.message_index.asc()).limit(self.max_history).all()

    async def _save_message(self, role: str, content: str, index: int):
        """Save message to conversation history"""
        message = CoachConversation(
            id=str(uuid_lib.uuid4()),
            user_id=self.user_id,
            session_id=self.session_id,
            role=role,
            content=content,
            message_index=index
        )
        self.db.add(message)
        self.db.commit()
        
        logger.info("Saved coach message",
                   user_id=self.user_id,
                   session_id=self.session_id,
                   role=role,
                   index=index)

    async def clear_session_history(self):
        """Delete all messages for current session"""
        self.db.query(CoachConversation).filter(
            CoachConversation.user_id == self.user_id,
            CoachConversation.session_id == self.session_id
        ).delete()
        self.db.commit()
        logger.info("Cleared coach session", session_id=self.session_id)

    def get_conversations_list(self) -> List[Dict[str, Any]]:
        """Get list of all conversation sessions"""
        from sqlalchemy import func
        
        conversations = self.db.query(
            CoachConversation.session_id,
            func.min(CoachConversation.content).label('title'),
            func.max(CoachConversation.content).label('last_message'),
            func.count(CoachConversation.id).label('message_count'),
            func.min(CoachConversation.created_at).label('created_at'),
            func.max(CoachConversation.created_at).label('updated_at')
        ).filter(
            CoachConversation.user_id == self.user_id,
            CoachConversation.role == 'user'
        ).group_by(
            CoachConversation.session_id
        ).order_by(
            func.max(CoachConversation.created_at).desc()
        ).all()
        
        return [
            {
                "session_id": conv.session_id,
                "title": conv.title[:100] if conv.title else "New Conversation",
                "last_message": conv.last_message[:200] if conv.last_message else "",
                "message_count": conv.message_count,
                "created_at": conv.created_at.isoformat() if conv.created_at else None,
                "updated_at": conv.updated_at.isoformat() if conv.updated_at else None
            }
            for conv in conversations
        ]

    def get_conversation_messages(self, session_id: str) -> List[Dict[str, Any]]:
        """Get all messages for a specific conversation"""
        messages = self.db.query(CoachConversation).filter(
            CoachConversation.user_id == self.user_id,
            CoachConversation.session_id == session_id
        ).order_by(CoachConversation.message_index.asc()).all()
        
        return [
            {
                "role": msg.role,
                "content": msg.content,
                "created_at": msg.created_at.isoformat() if msg.created_at else None
            }
            for msg in messages
        ]
