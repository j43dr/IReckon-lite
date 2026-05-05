#!/usr/bin/env python3
"""
网页获取实现
"""
import asyncio
from typing import Optional
from loguru import logger


async def fetch_url(url: str, timeout: int = 30) -> str:
    """获取网页内容"""
    try:
        import aiohttp
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=timeout)) as resp:
                return await resp.text()
    except ImportError:
        # 回退到urllib
        import urllib.request
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            return resp.read().decode("utf-8")
    except Exception as e:
        logger.error(f"获取网页失败: {e}")
        return f"Error: {e}"