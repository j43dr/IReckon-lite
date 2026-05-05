#!/usr/bin/env python3
"""
keyboard - 键盘控制
"""
import asyncio
from typing import Dict


async def run(keys: str, hold: float = 0.1, **kwargs) -> Dict:
    """发送按键"""
    try:
        from pynput.keyboard import Controller, Key
        controller = Controller()
        
        key_map = {
            "enter": Key.enter,
            "ctrl": Key.ctrl_l,
            "alt": Key.alt_l,
            "shift": Key.shift_l,
            "space": Key.space,
            "esc": Key.esc,
            "up": Key.up,
            "down": Key.down,
            "left": Key.left,
            "right": Key.right,
        }
        
        for key in keys.split("+"):
            key = key.strip().lower()
            if key in key_map:
                with controller.pressed(key_map[key]):
                    await asyncio.sleep(hold)
            else:
                controller.press(key)
                await asyncio.sleep(hold)
                controller.release(key)
        
        return {"success": True, "pressed": keys}
    except ImportError:
        return {"success": False, "error": "pynput not installed"}
    except Exception as e:
        return {"success": False, "error": str(e)}


if __name__ == "__main__":
    import asyncio
    print(asyncio.run(run("a")))