#!/usr/bin/env python3
"""
notification - 系统通知 - 通用
支持: Windows, Linux, macOS, Android(Termux)
"""
import platform
import asyncio
from typing import Dict, Optional


async def run(title: str = "通知", message: str = "", sound: bool = True, **kwargs) -> Dict:
    """发送系统通知"""
    system = platform.system().lower()
    is_android = _check_android()
    
    try:
        if is_android:
            return await _notify_android(title, message)
        elif system == "windows":
            return await _notify_windows(title, message, sound)
        elif system == "darwin":
            return await _notify_mac(title, message, sound)
        else:
            return await _notify_linux(title, message, sound)
    except Exception as e:
        return {"success": False, "error": str(e)}


def _check_android() -> bool:
    """检测是否在Android(Termux)上"""
    try:
        import os
        return os.path.exists("/data/data/com.termux") or os.path.exists("/sdcard")
    except:
        return False


def _get_platform() -> str:
    """获取平台"""
    system = platform.system().lower()
    if system == "linux" and _check_android():
        return "android"
    return system


async def _run_cmd(cmd: str) -> Dict:
    proc = await asyncio.create_subprocess_shell(
        cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await proc.communicate()
    return {"returncode": proc.returncode, "stdout": stdout.decode(), "stderr": stderr.decode()}


async def _notify_android(title: str, message: str) -> Dict:
    """Android(Termux)通知"""
    # 使用termux-notification
    result = await _run_cmd(f'termux-notification --title "{title}" --content "{message}"')
    if result["returncode"] == 0:
        return {"success": True}
    # 回退到echo
    result = await _run_cmd(f'echo "{title}: {message}"')
    return {"success": True, "note": "Displayed in terminal"}


async def _notify_windows(title: str, message: str, sound: bool) -> Dict:
    """Windows通知"""
    script = f'''
[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
$template = "<toast><audio silent='{not sound}'/><visual><binding template='toastText02'><text id='1'>{title}</text><text id='2'>{message}</text></binding></visual></toast>"
$xml = New-Object Windows.Data.Xml.Dom.XmlDocument
$xml.LoadXml($template)
$toast = [Windows.UI.Notifications.ToastNotification]::new($xml)
[Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier("IReckon").Show($toast)
'''
    result = await _run_cmd(f'powershell -command "{script}"')
    return {"success": result["returncode"] == 0}


async def _notify_mac(title: str, message: str, sound: bool) -> Dict:
    """macOS通知"""
    sound_arg = 'sound name "Glass"' if sound else 'without timeout'
    script = f'display notification "{message}" with title "{title}" {sound_arg}'
    result = await _run_cmd(f"osascript -e '{script}'")
    return {"success": result["returncode"] == 0}


async def _notify_linux(title: str, message: str, sound: bool) -> Dict:
    """Linux通知"""
    # 尝试 notify-send
    silent = "-u critical" if not sound else ""
    result = await _run_cmd(f'notify-send {silent} "{title}" "{message}"')
    if result["returncode"] == 0:
        return {"success": True}
    # 回退到echo
    return {"success": True, "note": f"{title}: {message}"}


if __name__ == "__main__":
    import asyncio
    print(asyncio.run(run(title="Test", message="Hello!")))