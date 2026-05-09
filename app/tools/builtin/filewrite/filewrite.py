#!/usr/bin/env python3
"""
filewrite - 写入文件
"""
import os
from typing import Dict


async def run(path: str, content: str, append: bool = False, **kwargs) -> Dict:
    """写入文件内容"""
    path = os.path.expanduser(path)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    
    mode = "a" if append else "w"
    try:
        with open(path, mode, encoding="utf-8") as f:
            f.write(content)
        return {"path": path, "written": len(content), "success": True}
    except Exception as e:
        return {"path": path, "written": 0, "error": str(e)}


if __name__ == "__main__":
    import asyncio
    print(asyncio.run(run("test.txt", "hello")))