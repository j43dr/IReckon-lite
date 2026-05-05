#!/usr/bin/env python3
"""
process - 进程管理 - 跨平台通用
支持: Windows, Linux, macOS, Android(termux)
"""
import platform
from typing import Dict, Optional, List


async def run(action: str, name: Optional[str] = None, **kwargs) -> Dict:
    """进程操作"""
    system = platform.system().lower()
    
    try:
        if action == "list":
            return await _list_processes(system)
        elif action == "find" and name:
            return await _find_process(system, name)
        elif action == "kill" and name:
            return await _kill_process(system, name)
        else:
            return {"success": False, "error": f"Unknown action: {action}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


async def _list_processes(system: str) -> Dict:
    """列出进程"""
    import asyncio
    
    if system == "windows":
        proc = await asyncio.create_subprocess_shell(
            'tasklist /FO CSV /NH',
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, _ = await proc.communicate()
        
        processes = []
        for line in stdout.decode().strip().split("\n")[:20]:
            if line:
                parts = line.split(",")
                if len(parts) >= 2:
                    processes.append({
                        "name": parts[0].strip('"'),
                        "pid": parts[1].strip('"')
                    })
        
        return {"success": True, "processes": processes}
    
    elif system in ["linux", "android"]:
        proc = await asyncio.create_subprocess_shell(
            'ps -eo pid,comm,%mem --no-headers | head -20',
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, _ = await proc.communicate()
        
        processes = []
        for line in stdout.decode().strip().split("\n"):
            parts = line.split()
            if len(parts) >= 3:
                processes.append({
                    "pid": parts[0],
                    "name": parts[1],
                    "mem": parts[2]
                })
        
        return {"success": True, "processes": processes}
    
    elif system == "darwin":
        proc = await asyncio.create_subprocess_shell(
            'ps -eo pid,comm,%mem --no-headers | head -20',
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, _ = await proc.communicate()
        
        processes = []
        for line in stdout.decode().strip().split("\n"):
            parts = line.split()
            if len(parts) >= 3:
                processes.append({
                    "pid": parts[0],
                    "name": parts[1],
                    "mem": parts[2]
                })
        
        return {"success": True, "processes": processes}
    
    return {"success": False, "error": "Unknown system"}


async def _find_process(system: str, name: str) -> Dict:
    """查找进程"""
    import asyncio
    
    if system == "windows":
        proc = await asyncio.create_subprocess_shell(
            f'tasklist /FI "IMAGENAME eq {name}" /FO CSV /NH',
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, _ = await proc.communicate()
        
        return {
            "success": True,
            "found": name in stdout.decode(),
            "output": stdout.decode()[:300]
        }
    
    else:
        proc = await asyncio.create_subprocess_shell(
            f'pgrep -f "{name}"',
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, _ = await proc.communicate()
        
        pids = [p.strip() for p in stdout.decode().strip().split("\n") if p.strip()]
        
        return {
            "success": True,
            "found": len(pids) > 0,
            "pids": pids
        }


async def _kill_process(system: str, name: str) -> Dict:
    """终止进程"""
    import asyncio
    
    # 检查是否为PID
    try:
        pid = int(name)
    except ValueError:
        # 是进程名，先查找PID
        result = await _find_process(system, name)
        if not result.get("found"):
            return {"success": False, "error": f"Process not found: {name}"}
        pids = result.get("pids", [])
        if not pids:
            return {"success": False, "error": f"No PID for: {name}"}
        pid = int(pids[0])
    
    if system == "windows":
        proc = await asyncio.create_subprocess_shell(
            f'taskkill /PID {pid} /F',
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        _, stderr = await proc.communicate()
        
        return {
            "success": proc.returncode == 0,
            "killed": pid,
            "error": stderr.decode() if proc.returncode != 0 else None
        }
    
    else:
        proc = await asyncio.create_subprocess_shell(
            f'kill -9 {pid}',
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        _, stderr = await proc.communicate()
        
        return {
            "success": proc.returncode == 0,
            "killed": pid,
            "error": stderr.decode() if proc.returncode != 0 else None
        }


if __name__ == "__main__":
    import asyncio
    print(asyncio.run(run("list")))
    print(asyncio.run(run("find", name="python")))
    print(asyncio.run(run("kill", name="1")))