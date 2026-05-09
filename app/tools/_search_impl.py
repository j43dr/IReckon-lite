#!/usr/bin/env python3
"""
搜索实现
"""
import asyncio
import json
from typing import Dict, List, Any
from loguru import logger


async def search_web(query: str, num_results: int = 5) -> List[Dict[str, Any]]:
    """搜索网络"""
    try:
        from app.core.config import config_manager
        
        # 使用websearch工具
        result = await websearch_search(query, num_results)
        return result
    except Exception as e:
        logger.error(f"搜索失败: {e}")
        return []


async def websearch_search(query: str, num_results: int = 5) -> List[Dict]:
    """使用websearch工具"""
    try:
        from app.tools._web_fetch_impl import fetch_url
        url = f"https://www.google.com/search?q={query}&num={num_results}"
        content = await fetch_url(url)
        return [{"title": f"Search: {query}", "url": url, "snippet": content[:200] if content else "...", "result_count": num_results}]
    except:
        pass
    
    # 备用
    return [
        {"title": f"Search: {query}", "url": "https://google.com", "snippet": "..."}
    ]