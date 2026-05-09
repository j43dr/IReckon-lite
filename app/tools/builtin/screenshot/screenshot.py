#!/usr/bin/env python3
"""
screenshot - 屏幕截图
"""
import uuid
from typing import Dict, Optional


async def run(save_path: Optional[str] = None, **kwargs) -> Dict:
    """屏幕截图"""
    try:
        from PIL import ImageGrab
        import uuid
        
        if save_path is None:
            save_path = f"screen_{uuid.uuid4().hex[:8]}.png"
        
        img = ImageGrab.grab()
        img.save(save_path)
        
        return {"success": True, "path": save_path}
    except ImportError:
        return {"success": False, "error": "PIL not installed"}
    except Exception as e:
        return {"success": False, "error": str(e)}


if __name__ == "__main__":
    import asyncio
    print(asyncio.run(run()))