#!/usr/bin/env python3
"""
network - 网络状态 - 跨平台通用
支持: Windows, Linux, macOS, Android(termux)
"""
import platform
import socket
from typing import Dict, Optional


async def run(action: str = "status", host: Optional[str] = None, **kwargs) -> Dict:
    """网络操作"""
    system = platform.system().lower()
    
    try:
        if action == "status":
            return await _network_status()
        elif action == "ping":
            return await _ping(host or "8.8.8.8")
        elif action == "speed":
            return await _network_speed()
        else:
            return {"success": False, "error": f"Unknown action: {action}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


async def _network_status() -> Dict:
    """获取网络状态"""
    import asyncio
    
    # 检查互联网连接
    connected = await _check_internet()
    
    # 获取连接类型
    conn_type = "unknown"
    try:
        if platform.system().lower() == "windows":
            proc = await asyncio.create_subprocess_shell(
                'netsh wlan show interfaces | findstr "SSID"',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, _ = await proc.communicate()
            if stdout.decode().strip():
                conn_type = "wifi"
            else:
                conn_type = "ethernet"
        elif platform.system().lower() in ["linux", "android"]:
            proc = await asyncio.create_subprocess_shell(
                'ip link show | grep -q "wlan" && echo wifi || echo ethernet',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, _ = await proc.communicate()
            conn_type = stdout.decode().strip() or "ethernet"
        elif platform.system().lower() == "darwin":
            proc = await asyncio.create_subprocess_shell(
                'networksetup -getairportpower en0 | grep "On"',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, _ = await proc.communicate()
            conn_type = "wifi" if "On" in stdout.decode() else "ethernet"
    except:
        pass
    
    # 获取IP地址
    ip = await _get_ip()
    
    return {
        "success": True,
        "connected": connected,
        "type": conn_type,
        "ip": ip
    }


async def _check_internet() -> bool:
    """检查互联网连接"""
    try:
        socket.create_connection(("8.8.8.8", 53), timeout=3)
        return True
    except OSError:
        try:
            socket.create_connection(("1.1.1.1", 53), timeout=3)
            return True
        except OSError:
            return False


async def _get_ip() -> Optional[str]:
    """获取IP地址"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return None


async def _ping(host: str) -> Dict:
    """Ping测试"""
    import asyncio
    
    system = platform.system().lower()
    if system == "windows":
        proc = await asyncio.create_subprocess_shell(
            f'ping -n 1 -w 1000 {host}',
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
    else:
        proc = await asyncio.create_subprocess_shell(
            f'ping -c 1 -W 1 {host}',
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
    
    stdout, stderr = await proc.communicate()
    output = stdout.decode() + stderr.decode()
    
    success = proc.returncode == 0
    
    # 解析延迟
    latency = None
    if success and "time=" in output:
        import re
        match = re.search(r"time[=<](\d+\.?\d*)\s*ms", output)
        if match:
            latency = float(match.group(1))
    
    return {
        "success": success,
        "host": host,
        "latency": latency,
        "output": output[:200]
    }


async def _network_speed() -> Dict:
    """获取网速（简化版）"""
    import asyncio
    
    # 尝试获取网络接口统计
    system = platform.system().lower()
    try:
        if system == "windows":
            proc = await asyncio.create_subprocess_shell(
                'netsh interface ipv4 show ipstats | findstr "Bytes"',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, _ = await proc.communicate()
        elif system == "linux":
            proc = await asyncio.create_subprocess_shell(
                'cat /proc/net/dev',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, _ = await proc.communicate()
        else:
            # macOS
            proc = await asyncio.create_subprocess_shell(
                'netstat -ib',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, _ = await proc.communicate()
        
        return {
            "success": True,
            "stats": stdout.decode()[:500]
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


if __name__ == "__main__":
    import asyncio
    print(asyncio.run(run("status")))
    print(asyncio.run(run("ping", host="google.com")))