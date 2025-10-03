"""
Code Executor - Secure Sandboxed Python execution for AI Coach
Uses basic sandboxing (RestrictedPython too restrictive for pandas)
"""

import structlog
import sys
import io
import json
from typing import Dict, Any
from contextlib import redirect_stdout, redirect_stderr
import traceback

logger = structlog.get_logger()


class CodeExecutor:
    """
    Executes Python code in a sandboxed environment
    Allows pandas, numpy, scipy, talib for analysis
    """
    
    def __init__(self):
        self.timeout = 30
        self.max_output_size = 100000
    
    def execute(self, code: str, context_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Execute Python code with provided context data
        
        Returns:
            {"success": bool, "result": any, "stdout": str, "error": str}
        """
        
        try:
            # Basic security check
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
                    return {
                        "success": False,
                        "error": f"Forbidden operation detected",
                        "result": None,
                        "stdout": ""
                    }
            
            # Build safe globals
            safe_globals = {
                '__builtins__': {
                    '__import__': __import__,  # Required for import statements
                    'print': print,
                    'len': len,
                    'range': range,
                    'enumerate': enumerate,
                    'zip': zip,
                    'map': map,
                    'filter': filter,
                    'sorted': sorted,
                    'sum': sum,
                    'min': min,
                    'max': max,
                    'abs': abs,
                    'round': round,
                    'int': int,
                    'float': float,
                    'str': str,
                    'list': list,
                    'dict': dict,
                    'set': set,
                    'tuple': tuple,
                    'bool': bool,
                    'True': True,
                    'False': False,
                    'None': None,
                    'isinstance': isinstance,
                    'hasattr': hasattr,
                    'getattr': getattr,
                    'setattr': setattr,
                    'type': type,
                    'any': any,
                    'all': all
                }
            }
            
            # Import allowed modules
            try:
                import pandas as pd
                import numpy as np
                safe_globals['pd'] = pd
                safe_globals['pandas'] = pd
                safe_globals['np'] = np
                safe_globals['numpy'] = np
            except ImportError:
                pass
            
            try:
                import talib
                safe_globals['talib'] = talib
            except ImportError:
                pass
            
            # Import plotting libraries
            try:
                import matplotlib
                matplotlib.use('Agg')  # Non-interactive backend for server-side rendering
                import matplotlib.pyplot as plt
                import seaborn as sns
                safe_globals['matplotlib'] = matplotlib
                safe_globals['plt'] = plt
                safe_globals['seaborn'] = sns
                safe_globals['sns'] = sns
            except ImportError:
                pass
            
            try:
                import plotly
                import plotly.graph_objects as go
                import plotly.express as px
                safe_globals['plotly'] = plotly
                safe_globals['go'] = go
                safe_globals['px'] = px
            except ImportError:
                pass
            
            try:
                import scipy
                import scipy.stats
                safe_globals['scipy'] = scipy
            except ImportError:
                pass
            
            import math
            import statistics
            from datetime import datetime, timedelta
            from collections import defaultdict
            
            safe_globals['math'] = math
            safe_globals['statistics'] = statistics
            safe_globals['datetime'] = datetime
            safe_globals['timedelta'] = timedelta
            safe_globals['defaultdict'] = defaultdict
            
            # Add context data
            if context_data:
                for key, value in context_data.items():
                    safe_globals[key] = value
            
            # Capture output
            stdout_capture = io.StringIO()
            stderr_capture = io.StringIO()
            
            result = None
            # Don't use exec_locals - execute everything in safe_globals so list comprehensions work
            
            with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
                exec(code, safe_globals)
                
                # Get result from safe_globals
                if 'result' in safe_globals:
                    result = safe_globals['result']
            
            stdout_text = stdout_capture.getvalue()[:self.max_output_size]
            stderr_text = stderr_capture.getvalue()[:self.max_output_size]
            
            return {
                "success": True,
                "result": result,
                "stdout": stdout_text,
                "stderr": stderr_text,
                "context": safe_globals  # Return all variables for persistent context
            }
            
        except Exception as e:
            error_trace = traceback.format_exc()
            logger.error("Code execution failed", error=str(e), traceback=error_trace)
            
            return {
                "success": False,
                "error": str(e),
                "traceback": error_trace[:1000],
                "result": None,
                "stdout": ""
            }
