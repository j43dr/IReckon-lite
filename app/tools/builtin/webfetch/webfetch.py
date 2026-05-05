#!/usr/bin/env python3
"""
webfetch - 获取网页
"""
import asyncio
from typing import Optional


async def run(url: str, timeout: int = 30, **kwargs) -> str:
    """获取网页内容"""
    try:
        from app.tools._web_fetch_impl import fetch_url
        return await fetch_url(url, timeout)
    except Exception as e:
        return f"Error: {e}"


if __name__ == "__main__":
    import asyncio
    print(asyncio.run(run("https://example.com")))