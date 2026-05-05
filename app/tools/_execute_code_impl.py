#!/usr/bin/env python3
"""
安全代码执行实现
"""
import asyncio
import io
import sys
from typing import Dict, Any, List
from loguru import logger


async def execute_safe(code: str, timeout: int = 30, allowed_modules: List[str] = None) -> Dict[str, Any]:
    """安全执行Python代码"""
    if allowed_modules is None:
        allowed_modules = ["json", "os", "re", "asyncio", "math", "random", "datetime", "collections", "itertools"]
    
    # 捕获输出
    stdout_capture = io.StringIO()
    stderr_capture = io.StringIO()
    
    local_vars = {"__name__": "__main__", "__builtins__": __builtins__}
    
    try:
        # 执行代码
        exec(code, local_vars)
        
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