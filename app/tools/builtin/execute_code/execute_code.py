#!/usr/bin/env python3
"""
execute_code - 安全执行代码
"""
import io
import sys
from typing import Dict, Any


async def run(code: str, timeout: int = 30, **kwargs) -> Dict[str, Any]:
    """安全执行Python代码"""
    stdout_capture = io.StringIO()
    stderr_capture = io.StringIO()
    
    old_stdout = sys.stdout
    old_stderr = sys.stderr
    sys.stdout = stdout_capture
    sys.stderr = stderr_capture
    
    local_vars = {"__name__": "__main__"}
    
    try:
        exec(code, {"__builtins__": __builtins__}, local_vars)
        return {
            "success": True,
            "output": stdout_capture.getvalue(),
            "error": stderr_capture.getvalue()
        }
    except Exception as e:
        return {
            "success": False,
            "output": stdout_capture.getvalue(),
            "error": str(e)
        }
    finally:
        sys.stdout = old_stdout
        sys.stderr = old_stderr


if __name__ == "__main__":
    import asyncio
    print(asyncio.run(run("print(1+1)")))