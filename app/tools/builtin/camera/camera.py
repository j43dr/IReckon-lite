#!/usr/bin/env python3
"""
camera - 摄像头/相机 - 跨平台通用
支持: Windows, Linux, macOS, Android(termux), iOS(通过系统相机)
"""
import platform
import os
from typing import Dict, Optional, List


async def run(action: str, save_path: Optional[str] = None, **kwargs) -> Dict:
    """相机操作"""
    system = platform.system().lower()
    
    try:
        if action == "capture":
            return await _capture_photo(system, save_path)
        elif action == "list":
            return await _list_cameras(system)
        else:
            return {"success": False, "error": f"Unknown action: {action}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


async def _capture_photo(system: str, save_path: Optional[str]) -> Dict:
    """拍照"""
    import asyncio
    import uuid
    
    if save_path is None:
        save_path = f"camera_{uuid.uuid4().hex[:8]}.jpg"
    
    if system == "windows" or system == "linux":
        # 尝试用OpenCV
        try:
            import cv2
            cap = cv2.VideoCapture(0)
            ret, frame = cap.read()
            cap.release()
            
            if ret:
                cv2.imwrite(save_path, frame)
                return {"success": True, "path": os.path.abspath(save_path)}
        except ImportError:
            pass
        except Exception as e:
            pass
        
        # 尝试用系统命令
        if system == "windows":
            # 使用内置相机应用
            await asyncio.create_subprocess_shell(
                f'powershell -command "Add-Type -AssemblyName System.Windows.Forms; [System.Windows.Forms.SendKeys]::SendWait(\'^c\")',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
        else:
            #Linux/mobile: 使用 fswebcam 或 termux-camera
            proc = await asyncio.create_subprocess_shell(
                'which fswebcam termux-camera-photo 2>/dev/null',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, _ = await proc.communicate()
            
            tool = stdout.decode().strip().split()[0] if stdout.decode().strip() else None
            
            if tool == "fswebcam":
                proc = await asyncio.create_subprocess_shell(
                    f'fswebcam -r 1280x720 {save_path}',
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                await proc.communicate()
                if proc.returncode == 0:
                    return {"success": True, "path": os.path.abspath(save_path)}
            elif tool == "termux-camera-photo":
                proc = await asyncio.create_subprocess_shell(
                    f'termux-camera-photo -c 0 {save_path}',
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                await proc.communicate()
                return {"success": True, "path": save_path}
    
    elif system == "darwin":
        # macOS: 使用系统相机
        return {"success": False, "error": "Use Image Capture app or screenshot tool"}
    
    elif system == "android":
        # Android: 使用termux相机
        proc = await asyncio.create_subprocess_shell(
            f'termux-camera-photo -c 0 {save_path}',
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        await proc.communicate()
        return {"success": True, "path": save_path}
    
    return {"success": False, "error": "No camera tool available"}


async def _list_cameras(system: str) -> Dict:
    """列出可用相机"""
    import asyncio
    
    cameras = []
    
    if system == "windows":
        # 检查 DirectShow
        try:
            import cv2
            for i in range(3):
                try:
                    import cv2
                    cap = cv2.VideoCapture(i)
                    if cap.isOpened():
                        cameras.append({"id": i, "name": f"Camera {i}"})
                        cap.release()
                except:
                    pass
        except ImportError:
            pass
    
    elif system in ["linux", "android"]:
        proc = await asyncio.create_subprocess_shell(
            'ls /dev/video* 2>/dev/null || echo none',
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, _ = await proc.communicate()
        
        for dev in stdout.decode().strip().split():
            if dev:
                cameras.append({"id": dev, "name": dev})
        
        # Termux相机
        if not cameras:
            cameras.append({"id": "0", "name": "Termux Camera"})
    
    elif system == "darwin":
        proc = await asyncio.create_subprocess_shell(
            'system_profiler SPCameraDataType | grep "^    "',
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, _ = await proc.communicate()
        
        for line in stdout.decode().strip().split("\n"):
            if line.strip():
                cameras.append({"name": line.strip()})
    
    return {"success": True, "cameras": cameras}


if __name__ == "__main__":
    import asyncio
    print(asyncio.run(run("list")))
    print(asyncio.run(run("capture")))