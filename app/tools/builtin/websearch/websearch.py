#!/usr/bin/env python3
"""
websearch - 搜索工具
"""
import asyncio
from typing import Dict, List, Any


async def run(query: str, num_results: int = 5, **kwargs) -> List[Dict[str, Any]]:
    """执行网络搜索"""
    try:
        from app.tools._search_impl import search_web
        return await search_web(query, num_results)
    except Exception as e:
        return [{"title": f"Error: {e}", "url": "", "snippet": str(e)}]


if __name__ == "__main__":
    import asyncio
    print(asyncio.run(run("test", 3)))