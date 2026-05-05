#!/usr/bin/env python3
"""
clipboard - 剪贴板管理 - 通用
支持: Windows, Linux, macOS, Android(Termux)
"""
import platform
import asyncio
from typing import Dict, Optional


async def run(action: str, text: Optional[str] = None, **kwargs) -> Dict:
    """剪贴板操作"""
    system = platform.system().lower()
    is_android = system == "linux" and _check_android()
    
    try:
        if action == "read":
            return await _read_clipboard(system, is_android)
        elif action == "write":
            if text is None:
                return {"success": False, "error": "text is required for write"}
            return await _write_clipboard(system, is_android, text)
        elif action == "clear":
            return await _write_clipboard(system, is_android, "")
        else:
            return {"success": False, "error": f"Unknown action: {action}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def _check_android() -> bool:
    """检测是否在Android上"""
    try:
        import os
        return os.path.exists("/data/data/com.termux")
    except:
        return False


async def _run_cmd(cmd: str) -> Dict:
    """执行命令"""
    proc = await asyncio.create_subprocess_shell(
        cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await proc.communicate()
    return {
        "returncode": proc.returncode,
        "stdout": stdout.decode("utf-8", errors="ignore"),
        "stderr": stderr.decode("utf-8", errors="ignore")
    }


async def _read_clipboard(system: str, is_android: bool) -> Dict:
    """读取剪贴板"""
    # Termux优先
    if is_android:
        result = await _run_cmd("termux-clipboard-get")
        if result["returncode"] == 0:
            return {"success": True, "text": result["stdout"].strip()}
    
    if system == "windows":
        result = await _run_cmd('powershell -command "Get-Clipboard"')
        return {"success": True, "text": result["stdout"].strip()}
    elif system == "darwin":
        result = await _run_cmd("pbpaste")
        return {"success": True, "text": result["stdout"]}
    else:
        # Linux 尝试 xclip/xsel
        for cmd in ["xclip -selection clipboard -o", "xsel --clipboard"]:
            result = await _run_cmd(cmd)
            if result["returncode"] == 0:
                return {"success": True, "text": result["stdout"]}
        # 最后尝试Wayland
        result = await _run_cmd("wl-paste")
        if result["returncode"] == 0:
            return {"success": True, "text": result["stdout"]}
    
    return {"success": False, "error": "No clipboard tool available"}


async def _write_clipboard(system: str, is_android: bool, text: str) -> Dict:
    """写入剪贴板"""
    # Termux优先
    if is_android:
        result = await _run_cmd(f"termux-clipboard-set '{text}'")
        if result["returncode"] == 0:
            return {"success": True}
    
    if system == "windows":
        text_escaped = text.replace("'", "''")
        result = await _run_cmd(f'powershell -command "Set-Clipboard -Value \'"{text_escaped}\'"')
        return {"success": result["returncode"] == 0}
    elif system == "darwin":
        result = await _run_cmd(f'echo "{text}" | pbcopy')
        return {"success": result["returncode"] == 0}
    else:
        # Linux 尝试 xclip/xsel
        for cmd in [f"echo '{text}' | xclip -selection clipboard", f"echo '{text}' | xsel --clipboard"]:
            result = await _run_cmd(cmd)
            if result["returncode"] == 0:
                return {"success": True}
        # 最后尝试Wayland
        result = await _run_cmd(f"wl-paste '{text}'")
        if result["returncode"] == 0:
            return {"success": True}
    
    return {"success": False, "error": "No clipboard tool available"}


if __name__ == "__main__":
    import asyncio
    print(asyncio.run(run("write", text="test")))
    print(asyncio.run(run("read")))