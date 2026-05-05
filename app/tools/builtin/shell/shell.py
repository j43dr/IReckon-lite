#!/usr/bin/env python3
"""
shell - 执行Shell命令
"""
import asyncio
from typing import Dict


async def run(command: str, timeout: int = 30, **kwargs) -> Dict:
    """执行Shell命令"""
    try:
        proc = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        try:
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
            return {
                "stdout": stdout.decode("utf-8", errors="ignore"),
                "stderr": stderr.decode("utf-8", errors="ignore"),
                "returncode": proc.returncode
            }
        except asyncio.TimeoutError:
            proc.kill()
            return {"stdout": "", "stderr": "Command timeout", "returncode": -1}
    except Exception as e:
        return {"stdout": "", "stderr": str(e), "returncode": -1}


if __name__ == "__main__":
    import asyncio
    print(asyncio.run(run("echo hello")))