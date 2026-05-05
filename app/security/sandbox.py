from loguru import logger
from typing import Dict, Any


class SandboxEnvironment:
    def __init__(self):
        self.allowed_modules = ["json", "os", "re", "asyncio", "math", "random"]
        self.blocked_modules = ["subprocess", "socket", "ctypes"]

    async def execute(self, code: str) -> Dict[str, Any]:
        try:
            import asyncio
            import io
            import sys
            
            stdout_capture = io.StringIO()
            sys.stdout = stdout_capture
            
            local_vars = {"__name__": "__main__", "__builtins__": __builtins__}
            exec(code, local_vars)
            
            return {"success": True, "output": stdout_capture.getvalue()}
        except Exception as e:
            return {"success": False, "error": str(e)}


sandbox = SandboxEnvironment()