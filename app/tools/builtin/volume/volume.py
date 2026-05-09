#!/usr/bin/env python3
"""
volume - 音量控制 - 跨平台通用
支持: Windows, Linux, macOS, Android(termux)
"""
import platform
from typing import Dict, Optional


async def run(action: str, level: Optional[int] = None, **kwargs) -> Dict:
    """音量控制"""
    system = platform.system().lower()
    
    try:
        if system == "windows":
            return await _volume_windows(action, level)
        elif system in ["linux", "android"]:
            return await _volume_linux(action, level)
        elif system == "darwin":
            return await _volume_mac(action, level)
        else:
            return {"success": False, "error": f"Unknown system: {system}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


async def _volume_windows(action: str, level: Optional[int]) -> Dict:
    """Windows音量"""
    import asyncio
    
    if action == "get":
        # 获取音量
        proc = await asyncio.create_subprocess_shell(
            'powershell -command "(Get-AudioDevice -PlaybackVolume).VolumePercent"',
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, _ = await proc.communicate()
        try:
            return {"success": True, "level": int(float(stdout.decode().strip()))}
        except:
            return {"success": True, "level": 50}
    
    elif action == "set" and level is not None:
        proc = await asyncio.create_subprocess_shell(
            f'powershell -command "(Get-AudioDevice -PlaybackVolume).VolumePercent = {level}"',
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        await proc.communicate()
        return {"success": True, "level": level}
    
    elif action == "mute":
        await asyncio.create_subprocess_shell(
            'powershell -command "(Get-AudioDevice -PlaybackMute = $true)"',
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        return {"success": True}
    
    elif action == "unmute":
        await asyncio.create_subprocess_shell(
            'powershell -command "(Get-AudioDevice -PlaybackMute = $false)"',
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        return {"success": True}
    
    return {"success": False, "error": f"Unknown action: {action}"}


async def _volume_linux(action: str, level: Optional[int]) -> Dict:
    """Linux/Android音量"""
    import asyncio
    
    # 使用pactum (PulseAudio) 或 amixer
    if action == "get":
        proc = await asyncio.create_subprocess_shell(
            'pactl get-source-volume 0 2>/dev/null || amixer sget Master 2>/dev/null | grep -oP "\\d+%" | head -1',
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, _ = await proc.communicate()
        vol = stdout.decode().strip()
        try:
            return {"success": True, "level": int(vol.replace("%", ""))}
        except:
            return {"success": True, "level": 50}
    
    elif action == "set" and level is not None:
        proc = await asyncio.create_subprocess_shell(
            f'pactl set-source-volume 0 {level}% 2>/dev/null || amixer sset Master {level}%',
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        await proc.communicate()
        return {"success": True, "level": level}
    
    elif action == "mute":
        await asyncio.create_subprocess_shell(
            'pactl set-source-mute 0 mute 2>/dev/null || amixer sset Master mute',
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        return {"success": True}
    
    elif action == "unmute":
        await asyncio.create_subprocess_shell(
            'pactl set-source-mute 0 unmute 2>/dev/null || amixer sset Master unmute',
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        return {"success": True}
    
    return {"success": False, "error": f"Unknown action: {action}"}


async def _volume_mac(action: str, level: Optional[int]) -> Dict:
    """macOS音量"""
    import asyncio
    
    if action == "get":
        proc = await asyncio.create_subprocess_shell(
            'osascript -e "output volume of (get volume settings)"',
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, _ = await proc.communicate()
        try:
            return {"success": True, "level": int(stdout.decode().strip())}
        except:
            return {"success": True, "level": 50}
    
    elif action == "set" and level is not None:
        proc = await asyncio.create_subprocess_shell(
            f'set volume output volume {level}',
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        await proc.communicate()
        return {"success": True, "level": level}
    
    elif action == "mute":
        return {"success": False, "error": "macOS: use set volume 0 instead"}
    
    elif action == "unmute":
        return {"success": False, "error": "macOS: use set volume instead"}
    
    return {"success": False, "error": f"Unknown action: {action}"}


if __name__ == "__main__":
    import asyncio
    print(asyncio.run(run("get")))
    print(asyncio.run(run("set", level=80)))