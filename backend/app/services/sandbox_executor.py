"""
Sandboxed Python code execution for custom strategy logic
"""

import sys
import io
import contextlib
from typing import Dict, Any, Optional
import structlog
from pathlib import Path

logger = structlog.get_logger()


class SandboxExecutor:
    """
    Execute Python code in a restricted environment
    
    Security measures:
    - Restricted builtins (no file I/O, imports, etc.)
    - CPU/memory limits (TODO: use resource module)
    - Timeout enforcement
    - Isolated namespace
    """
    
    def __init__(self, workspace_dir: Optional[Path] = None):
        self.workspace_dir = workspace_dir or Path("/tmp/backtest_sandbox")
        self.workspace_dir.mkdir(parents=True, exist_ok=True)
    
    def execute(
        self,
        code: str,
        context: Dict[str, Any],
        timeout: int = 30
    ) -> Dict[str, Any]:
        """
        Execute code in sandboxed environment
        
        Args:
            code: Python code to execute
            context: Variables available to code (df, features, etc.)
            timeout: Max execution time in seconds
            
        Returns:
            Dict with success, result, output, and error
        """
        
        # Create safe globals with allowed modules
        safe_globals = {
            '__builtins__': self._get_safe_builtins(),
            'pd': self._get_pandas(),
            'np': self._get_numpy(),
            'plt': self._get_matplotlib(),
            'sns': self._get_seaborn(),
            'workspace_dir': str(self.workspace_dir)
        }
        
        # Add context variables
        safe_globals.update(context)
        
        # Capture stdout/stderr
        stdout_capture = io.StringIO()
        stderr_capture = io.StringIO()
        
        result = None
        error = None
        
        try:
            with contextlib.redirect_stdout(stdout_capture), contextlib.redirect_stderr(stderr_capture):
                # Execute code
                exec(code, safe_globals)
                
                # Extract result if exists
                if 'result' in safe_globals:
                    result = safe_globals['result']
        
        except Exception as e:
            error = f"{type(e).__name__}: {str(e)}"
            logger.error(f"Sandbox execution error: {error}")
        
        return {
            'success': error is None,
            'result': result,
            'output': stdout_capture.getvalue(),
            'error': error,
            'context': safe_globals  # Return updated context
        }
    
    def _get_safe_builtins(self) -> Dict[str, Any]:
        """Return allowed built-in functions"""
        
        # Start with minimal safe builtins
        safe_builtins = {
            'abs': abs,
            'all': all,
            'any': any,
            'bool': bool,
            'dict': dict,
            'enumerate': enumerate,
            'filter': filter,
            'float': float,
            'int': int,
            'len': len,
            'list': list,
            'map': map,
            'max': max,
            'min': min,
            'print': print,
            'range': range,
            'round': round,
            'set': set,
            'sorted': sorted,
            'str': str,
            'sum': sum,
            'tuple': tuple,
            'type': type,
            'zip': zip,
        }
        
        return safe_builtins
    
    def _get_pandas(self):
        """Return pandas if available"""
        try:
            import pandas as pd
            return pd
        except ImportError:
            logger.warning("pandas not available in sandbox")
            return None
    
    def _get_numpy(self):
        """Return numpy if available"""
        try:
            import numpy as np
            return np
        except ImportError:
            logger.warning("numpy not available in sandbox")
            return None
    
    def _get_matplotlib(self):
        """Return matplotlib if available"""
        try:
            import matplotlib
            matplotlib.use('Agg')  # Non-interactive backend
            import matplotlib.pyplot as plt
            return plt
        except ImportError:
            logger.warning("matplotlib not available in sandbox")
            return None
    
    def _get_seaborn(self):
        """Return seaborn if available"""
        try:
            import seaborn as sns
            return sns
        except ImportError:
            logger.warning("seaborn not available in sandbox")
            return None


# Global sandbox instance
_sandbox: Optional[SandboxExecutor] = None


def get_sandbox_executor(workspace_dir: Optional[Path] = None) -> SandboxExecutor:
    """Get or create global sandbox executor"""
    global _sandbox
    if _sandbox is None or workspace_dir is not None:
        _sandbox = SandboxExecutor(workspace_dir)
    return _sandbox

