#!/usr/bin/env python3
"""
截图实现
"""
import os
from typing import Optional, Dict
from loguru import logger


async def capture_screen(save_path: Optional[str] = None) -> Dict:
    """屏幕截图"""
    try:
        # 尝试 PIL
        from PIL import ImageGrab
        import uuid
        
        if save_path is None:
            save_path = f"screen_{uuid.uuid4().hex[:8]}.png"
        
        img = ImageGrab.grab()
        img.save(save_path)
        
        return {"success": True, "path": save_path}
    except ImportError:
        return {"success": False, "error": "PIL not installed, install: pip install pillow"}
    except Exception as e:
        return {"success": False, "error": str(e)}