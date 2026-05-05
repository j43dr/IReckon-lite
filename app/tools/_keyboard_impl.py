#!/usr/bin/env python3
"""
键盘控制实现
"""
import asyncio
from loguru import logger


async def press_keys(keys: str, hold: float = 0.1):
    """发送按键"""
    try:
        # 尝试 pynput
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
                # 单字符
                controller.press(key)
                await asyncio.sleep(hold)
                controller.release(key)
        
        return {"success": True}
    except ImportError:
        return {"success": False, "error": "pynput not installed, pip install pynput"}
    except Exception as e:
        logger.error(f"按键失败: {e}")
        return {"success": False, "error": str(e)}