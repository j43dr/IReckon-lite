#!/usr/bin/env python3
"""
battery - 电池状态 - 通用
支持: Windows, Linux, macOS, Android(Termux)
"""
import platform
import asyncio
from typing import Dict


async def run(action: str = "get", **kwargs) -> Dict:
    """获取电池状态"""
    system = platform.system().lower()
    is_android = _check_android()
    
    try:
        if is_android or system == "linux":
            return await _battery_linux(is_android)
        elif system == "windows":
            return await _battery_windows()
        elif system == "darwin":
            return await _battery_mac()
        else:
            return {"success": False, "error": f"Unknown system: {system}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def _check_android() -> bool:
    try:
        import os
        return os.path.exists("/data/data/com.termux") or os.path.exists("/sdcard")
    except:
        return False


async def _run_cmd(cmd: str) -> Dict:
    proc = await asyncio.create_subprocess_shell(
        cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await proc.communicate()
    return {"returncode": proc.returncode, "stdout": stdout.decode(), "stderr": stderr.decode()}


async def _battery_android() -> Dict:
    """Android/Termux电池"""
    # 尝试 termux-battery-status
    result = await _run_cmd("termux-battery-status")
    if result["returncode"] == 0:
        import json
        try:
            data = json.loads(result["stdout"])
            return {
                "success": True,
                "level": int(data.get("percentage", 100)),
                "charging": data.get("status") == "CHARGING",
                "temperature": data.get("temperature")
            }
        except:
            pass
    
    # 尝试读取 /sys
    result = await _run_cmd("cat /sys/class/power_supply/BAT0/capacity 2>/dev/null || echo 100")
    try:
        level = int(result["stdout"].strip())
        return {"success": True, "level": level, "charging": False}
    except:
        pass
    
    return {"success": True, "level": 100, "charging": True, "desktop": True}


async def _battery_linux(is_android: bool) -> Dict:
    """Linux电池"""
    if is_android:
        return await _battery_android()
    
    # 标准Linux
    result = await _run_cmd("cat /sys/class/power_supply/BAT0/capacity 2>/dev/null || echo 100")
    try:
        level = int(result["stdout"].strip())
        return {"success": True, "level": level}
    except:
        pass
    
    return {"success": True, "level": 100}


async def _battery_windows() -> Dict:
    """Windows电池"""
    result = await _run_cmd('powershell -command "(Get-WmiObject -Class Win32_Battery).EstimatedChargeRemaining"')
    try:
        level = int(result["stdout"].strip())
        return {"success": True, "level": level, "charging": False}
    except:
        return {"success": True, "level": 100, "charging": True}


async def _battery_mac() -> Dict:
    """macOS电池"""
    result = await _run_cmd("pmset -g batt | grep -oP '\\d+%' | head -1")
    try:
        level = int(result["stdout"].replace("%", "").strip())
        return {"success": True, "level": level}
    except:
        return {"success": True, "level": 100}


if __name__ == "__main__":
    import asyncio
    print(asyncio.run(run()))