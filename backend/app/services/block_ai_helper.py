"""
AI Helper for Custom Block Creation
Advanced AI assistant with function calling, code execution, and analysis
"""

from sqlalchemy.orm import Session
import structlog
import json
from typing import Dict, Any, List, Optional
from pathlib import Path

from app.services.code_executor import CodeExecutor
from app.services.storage_service import storage_service
from app.services.ai_router import ai_router

logger = structlog.get_logger()


class BlockAIHelper:
    """AI-powered assistant for creating custom trading blocks"""
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.code_executor = CodeExecutor()
        
        # Create workspace for this session
        from datetime import datetime
        self.workspace_path = storage_service.create_coach_workspace(
            self.user_id, 
            f"block-helper-{datetime.now().timestamp()}"
        )
        self.workspace_dir = Path(self.workspace_path) if not storage_service.use_s3 else None
    
    async def generate_block_code(
        self, 
        request: str, 
        current_code: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Generate or improve block code using AI with advanced capabilities"""
        
        try:
            system_prompt = self._create_system_prompt()
            user_message = self._create_user_message(request, current_code, context)
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ]
            
            # Define tools for function calling
            tools = [
                {
                    "type": "function",
                    "function": {
                        "name": "execute_python",
                        "description": "Execute Python code to test ideas, analyze data, or validate logic. Can install packages with pip.",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "code": {
                                    "type": "string",
                                    "description": "Python code to execute"
                                },
                                "description": {
                                    "type": "string",
                                    "description": "What this code does"
                                }
                            },
                            "required": ["code"]
                        }
                    }
                },
                {
                    "type": "function",
                    "function": {
                        "name": "test_block_code",
                        "description": "Test a block's execute function with sample OHLCV data",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "code": {
                                    "type": "string",
                                    "description": "The execute function code to test"
                                },
                                "params": {
                                    "type": "object",
                                    "description": "Parameters to pass to the function"
                                }
                            },
                            "required": ["code"]
                        }
                    }
                },
                {
                    "type": "function",
                    "function": {
                        "name": "generate_parameter_schema",
                        "description": "Generate a JSON schema for block parameters",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "parameters": {
                                    "type": "array",
                                    "description": "List of parameter definitions",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "name": {"type": "string"},
                                            "type": {"type": "string"},
                                            "default": {},
                                            "description": {"type": "string"}
                                        }
                                    }
                                }
                            },
                            "required": ["parameters"]
                        }
                    }
                }
            ]
            
            # Initial AI call using router
            response = await ai_router.chat_completion(
                messages=messages,
                user_id=self.user_id,
                request_type="block_helper",
                temperature=0.7,
                tools=tools,
                tool_choice="auto",
                force_model="gpt-4o",  # Block creation needs GPT-4o
                use_cache=False,  # Don't cache tool-based requests
                priority=1  # Higher priority for block creation
            )
            
            assistant_message = response.choices[0].message
            final_code = None
            final_params = None
            execution_log = []
            
            # Handle tool calls in a loop
            while assistant_message.tool_calls:
                for tool_call in assistant_message.tool_calls:
                    function_name = tool_call.function.name
                    function_args = json.loads(tool_call.function.arguments)
                    
                    logger.info(f"AI calling tool: {function_name}")
                    
                    # Execute the tool
                    tool_result = await self._execute_tool(function_name, function_args)
                    
                    # Clean tool result for logging (remove non-serializable objects)
                    clean_result = {}
                    for key, value in tool_result.items():
                        try:
                            json.dumps(value)
                            clean_result[key] = value
                        except (TypeError, ValueError):
                            clean_result[key] = str(value)[:500]  # Truncate long strings
                    
                    execution_log.append({
                        "tool": function_name,
                        "args": function_args,
                        "result": clean_result
                    })
                    
                    # Add tool call and result to messages
                    messages.append({
                        "role": "assistant",
                        "content": None,
                        "tool_calls": [tool_call.model_dump()]
                    })
                    
                    # Serialize tool result (handle numpy arrays)
                    try:
                        result_str = json.dumps(tool_result)
                    except TypeError:
                        # Handle non-serializable objects (numpy arrays, etc)
                        result_str = str(tool_result)
                    
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": result_str
                    })
                
                # Get next response using router
                response = await ai_router.chat_completion(
                    messages=messages,
                    user_id=self.user_id,
                    request_type="block_helper",
                    temperature=0.7,
                    tools=tools,
                    tool_choice="auto",
                    force_model="gpt-4o",
                    use_cache=False,
                    priority=1
                )
                assistant_message = response.choices[0].message
            
            # Extract final code from assistant's message
            final_message = assistant_message.content or ""
            
            # Try to extract code from markdown
            if "```python" in final_message:
                final_code = final_message.split("```python")[1].split("```")[0].strip()
            elif "```" in final_message:
                final_code = final_message.split("```")[1].split("```")[0].strip()
            elif current_code:
                final_code = current_code
            
            # Extract parameter schema if mentioned
            if "parameter" in final_message.lower() and "{" in final_message:
                try:
                    # Try to extract JSON
                    json_start = final_message.find("{")
                    json_end = final_message.rfind("}") + 1
                    if json_start >= 0 and json_end > json_start:
                        final_params = final_message[json_start:json_end]
                except:
                    pass
            
            return {
                "code": final_code,
                "parameters": final_params,
                "message": final_message,
                "execution_log": execution_log,
                "success": True
            }
            
        except Exception as e:
            logger.error(f"Block AI helper failed: {e}", exc_info=True)
            return {
                "code": current_code,
                "message": f"Error: {str(e)}",
                "success": False
            }
    
    async def _execute_tool(self, tool_name: str, tool_args: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool based on its name"""
        
        if tool_name == "execute_python":
            code = tool_args.get("code")
            context_data = {"workspace_dir": str(self.workspace_dir)} if self.workspace_dir else {}
            result = self.code_executor.execute(code, context_data)
            return result
        
        elif tool_name == "test_block_code":
            code = tool_args.get("code")
            params = tool_args.get("params", {})
            
            # Create sample OHLCV data
            import pandas as pd
            import numpy as np
            
            dates = pd.date_range('2024-01-01', periods=100, freq='1h')
            sample_data = pd.DataFrame({
                'open': np.random.randn(100).cumsum() + 100,
                'high': np.random.randn(100).cumsum() + 102,
                'low': np.random.randn(100).cumsum() + 98,
                'close': np.random.randn(100).cumsum() + 100,
                'volume': np.random.randint(1000, 10000, 100)
            }, index=dates)
            
            # Wrap code if needed
            if 'def execute' not in code:
                code = f"""
def execute(inputs, params, data):
{chr(10).join('    ' + line for line in code.split(chr(10)))}
"""
            
            test_code = f"""
{code}

# Test the function
result = execute([], {params}, data)
"""
            
            result = self.code_executor.execute(test_code, {'data': sample_data})
            return result
        
        elif tool_name == "generate_parameter_schema":
            parameters = tool_args.get("parameters", [])
            schema = {}
            for param in parameters:
                schema[param["name"]] = {
                    "type": param.get("type", "number"),
                    "default": param.get("default"),
                    "description": param.get("description", "")
                }
                if "min" in param:
                    schema[param["name"]]["min"] = param["min"]
                if "max" in param:
                    schema[param["name"]]["max"] = param["max"]
            
            return {"schema": json.dumps(schema, indent=2)}
        
        else:
            return {"error": f"Unknown tool: {tool_name}"}
    
    def _create_system_prompt(self) -> str:
        """Create comprehensive system prompt for block creation"""
        
        return """You are an expert quantitative developer and trading systems architect helping users create custom trading blocks.

## Your Capabilities

1. **Code Generation**: Write clean, efficient Python code for trading blocks
2. **Testing & Validation**: Test code with sample data to ensure it works
3. **Analysis**: Run advanced analysis to understand patterns and requirements
4. **Package Management**: Install any Python packages needed (pip install)
5. **Visualization**: Create charts and plots to validate logic

## Block Structure

Every block must have an `execute` function:

```python
def execute(inputs, params, data):
    \"\"\"
    Args:
        inputs: List of values from connected blocks
        params: Dict of parameters (from JSON schema)
        data: pandas DataFrame with OHLCV data
              Columns: open, high, low, close, volume
              Index: datetime
    
    Returns:
        Dict with named outputs
        Example: {"rsi": rsi_values, "signal": buy_signal}
    \"\"\"
    # Your code here
    return {"output_name": value}
```

## Available Libraries

**Pre-installed**: pandas, numpy, talib, scipy, sklearn, matplotlib, seaborn, plotly

**Can install**: Any package via `pip install package-name` in your code

## Best Practices

1. **Test First**: Use `test_block_code` to validate logic before finalizing
2. **Handle Errors**: Add try/except for robust code
3. **Vectorize**: Use pandas/numpy operations (avoid loops)
4. **Document**: Add docstrings and comments
5. **Validate Inputs**: Check data types and ranges
6. **Return Named Outputs**: Always return a dict with descriptive keys

## Workflow

When user asks for a block:

1. **Understand**: Ask clarifying questions if needed
2. **Research**: Use `execute_python` to test ideas/algorithms
3. **Implement**: Write the execute function
4. **Test**: Use `test_block_code` to validate with sample data
5. **Refine**: Fix issues and optimize
6. **Document**: Provide clear parameter schema

## Example: RSI Divergence Block

```python
def execute(inputs, params, data):
    import talib
    import numpy as np
    
    period = params.get('rsi_period', 14)
    lookback = params.get('lookback', 5)
    
    # Calculate RSI
    rsi = talib.RSI(data['close'].values, timeperiod=period)
    
    # Find divergences
    price_peaks = np.zeros(len(data))
    rsi_peaks = np.zeros(len(data))
    
    for i in range(lookback, len(data) - lookback):
        # Price makes higher high
        if data['close'].iloc[i] > data['close'].iloc[i-lookback:i].max():
            price_peaks[i] = 1
            # But RSI makes lower high (bearish divergence)
            if rsi[i] < rsi[i-lookback:i].max():
                rsi_peaks[i] = -1  # Bearish
    
    return {
        "rsi": rsi,
        "divergence": rsi_peaks,
        "bearish_divergence": rsi_peaks == -1
    }
```

## Parameter Schema Example

```json
{
  "rsi_period": {
    "type": "integer",
    "default": 14,
    "min": 2,
    "max": 100,
    "description": "RSI calculation period"
  },
  "lookback": {
    "type": "integer",
    "default": 5,
    "min": 2,
    "max": 50,
    "description": "Lookback period for divergence detection"
  }
}
```

Remember: You're helping traders build professional-grade indicators. Be thorough, test everything, and explain your approach."""
    
    def _create_user_message(
        self, 
        request: str, 
        current_code: Optional[str], 
        context: Optional[Dict[str, Any]]
    ) -> str:
        """Create user message with context"""
        
        parts = [f"User request: {request}"]
        
        if current_code:
            parts.append(f"\nCurrent code:\n```python\n{current_code}\n```")
            parts.append("\nPlease improve, modify, or debug this code based on the request.")
        else:
            parts.append("\nPlease create a new block from scratch.")
        
        if context:
            if "category" in context:
                parts.append(f"\nBlock category: {context['category']}")
            if "description" in context:
                parts.append(f"\nUser's description: {context['description']}")
        
        return "\n".join(parts)
