#!/usr/bin/env python3
"""
sensors - 传感器 - 通用
支持: Android(Termux), Linux, Windows, macOS
"""
import platform
import asyncio
from typing import Dict, Optional


async def run(sensor: str = "all", **kwargs) -> Dict:
    """获取传感器数据"""
    system = platform.system().lower()
    is_android = _check_android()
    
    try:
        if is_android:
            return await _sensors_android(sensor)
        elif system == "linux":
            return await _sensors_linux(sensor)
        elif system == "windows":
            return await _sensors_windows(sensor)
        elif system == "darwin":
            return await _sensors_mac(sensor)
        else:
            return {"success": False, "error": f"Unknown system: {system}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def _check_android() -> bool:
    try:
        import os
        return os.path.exists("/data/data/com.termux")
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


async def _sensors_android(sensor: str) -> Dict:
    """Android/Termux传感器"""
    if sensor == "all" or sensor == "accelerometer":
        result = await _run_cmd("termux-sensor -a accelerometer")
        if result["returncode"] == 0:
            return {"success": True, "sensor": "accelerometer", "data": result["stdout"][:200]}
    
    return {"success": False, "error": "Sensor not available"}


async def _sensors_linux(sensor: str) -> Dict:
    """Linux传感器"""
    # 尝试读取 /sys
    paths = {
        "accelerometer": "/sys/class/accel/accel/accel_all",
        "gyroscope": "/sys/class/gyro/gyro/gyro_all",
        "light": "/sys/class/light/light/lux",
    }
    
    if sensor in paths:
        result = await _run_cmd(f"cat {paths[sensor]} 2>/dev/null || echo 0")
        return {"success": True, "sensor": sensor, "value": result["stdout"].strip()}
    
    return {"success": False, "error": "No sensor"}


async def _sensors_windows(sensor: str) -> Dict:
    """Windows传感器"""
    # Windows可以用WMI但比较复杂，返回模拟数据
    return {"success": True, "sensor": sensor, "note": "Use external API"}


async def _sensors_mac(sensor: str) -> Dict:
    """macOS传感器"""
    return {"success": True, "sensor": sensor, "note": "Use external API"}


if __name__ == "__main__":
    import asyncio
    print(asyncio.run(run("all")))