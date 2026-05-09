#!/usr/bin/env python3
"""
fileread - 读取文件
"""
import os
from typing import Dict


async def run(path: str, offset: int = 0, limit: int = 2000, **kwargs) -> Dict:
    """读取文件内容"""
    path = os.path.expanduser(path)
    if not os.path.exists(path):
        return {"path": path, "content": "", "error": "File not found", "showing": "0-0"}
    
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        
        lines = content.split("\n")
        if offset > 0 or limit < len(lines):
            lines = lines[offset:offset+limit]
        
        return {
            "path": path,
            "content": "\n".join(lines),
            "total_lines": len(content.split("\n")),
            "showing": f"{offset+1}-{offset+len(lines)}"
        }
    except Exception as e:
        return {"path": path, "content": "", "error": str(e), "showing": "0-0"}


if __name__ == "__main__":
    import asyncio
    print(asyncio.run(run("test.txt")))