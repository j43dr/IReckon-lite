#!/usr/bin/env python3
"""
mouse - 鼠标控制
"""
import asyncio
from typing import Dict, Optional


async def run(action: str, x: Optional[int] = None, y: Optional[int] = None, button: str = "left", **kwargs) -> Dict:
    """鼠标控制"""
    try:
        from pynput.mouse import Controller, Button
        
        mouse = Controller()
        
        if action == "move" and x is not None and y is not None:
            mouse.position = (x, y)
        elif action == "click":
            mouse.pressed = getattr(Button, button.capitalize(), Button.left)
            mouse.released = getattr(Button, button.capitalize(), Button.left)
        elif action == "double_click":
            mouse.double_click(getattr(Button, button.capitalize(), Button.left))
        elif action == "right_click":
            mouse.click(Button.right)
        elif action == "drag" and x is not None and y is not None:
            mouse.press(Button.left)
            mouse.position = (x, y)
            mouse.release(Button.left)
        
        return {"success": True, "action": action}
    except ImportError:
        return {"success": False, "error": "pynput not installed"}
    except Exception as e:
        return {"success": False, "error": str(e)}


if __name__ == "__main__":
    import asyncio
    print(asyncio.run(run("move", 100, 100)))