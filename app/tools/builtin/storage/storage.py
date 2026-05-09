#!/usr/bin/env python3
"""
storage - 存储状态 - 跨平台通用
支持: Windows, Linux, macOS, Android(termux)
"""
import os
import shutil
from typing import Dict, Optional


async def run(path: Optional[str] = None, **kwargs) -> Dict:
    """获取存储状态"""
    try:
        path = path or os.getcwd()
        
        # 获取磁盘使用情况
        usage = shutil.disk_usage(path)
        
        return {
            "success": True,
            "total": usage.total,
            "used": usage.used,
            "free": usage.free,
            "percent": round(usage.used / usage.total * 100, 1),
            "total_gb": round(usage.total / (1024**3), 2),
            "used_gb": round(usage.used / (1024**3), 2),
            "free_gb": round(usage.free / (1024**3), 2)
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


# Android Termux 专用存储路径
ANDROID_STORAGE = {
    "internal": "/data",
    "external": "/sdcard",
    "termux": "/data/data/com.termux/files"
}


async def run_android() -> Dict:
    """Android存储"""
    import asyncio
    
    results = {}
    for name, path in ANDROID_STORAGE.items():
        try:
            usage = shutil.disk_usage(path)
            results[name] = {
                "total_gb": round(usage.total / (1024**3), 2),
                "free_gb": round(usage.free / (1024**3), 2),
                "percent": round(usage.used / usage.total * 100, 1)
            }
        except:
            pass
    
    return results


if __name__ == "__main__":
    import asyncio
    print(asyncio.run(run()))