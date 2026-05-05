#!/usr/bin/env python3
"""
ToolSystem - 工具系统
提供各种可调用工具给AI Agent
"""
import asyncio
import os
import json
import subprocess
import re
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass
from enum import Enum
from loguru import logger
from app.core.config import config_manager


class ToolType(Enum):
    """工具类型"""
    SEARCH = "search"           # 搜索
    WEB_FETCH = "web_fetch"    # 获取网页
    FILE_READ = "file_read"    # 读文件
    FILE_WRITE = "file_write"   # 写文件
    EXECUTE_CODE = "execute_code" # 执行代码
    SCREENSHOT = "screenshot"  # 截图
    KEYBOARD = "keyboard"       # 键盘
    MOUSE = "mouse"            # 鼠标
    CLIPBOARD = "clipboard"    # 剪贴板
    SHELL = "shell"           # Shell命令


@dataclass
class ToolResult:
    """工具执行结果"""
    success: bool
    result: Any = None
    error: str = None
    
    def to_dict(self) -> Dict:
        return {"success": self.success, "result": self.result, "error": self.error}


class BaseTool:
    """工具基类"""
    
    def __init__(self, name: str, description: str, tool_type: ToolType):
        self.name = name
        self.description = description
        self.tool_type = tool_type
    
    async def execute(self, **kwargs) -> ToolResult:
        """执行工具"""
        raise NotImplementedError
    
    def validate_params(self, params: Dict, required: List[str]) -> Optional[str]:
        """验证参数"""
        for key in required:
            if key not in params:
                return f"缺少必需参数: {key}"
        return None


class SearchTool(BaseTool):
    """搜索工具"""
    
    def __init__(self):
        super().__init__("search", "搜索网络获取信息", ToolType.SEARCH)
    
    async def execute(self, query: str, num_results: int = 5, **kwargs) -> ToolResult:
        """执行搜索"""
        error = self.validate_params({"query": query}, ["query"])
        if error:
            return ToolResult(False, error=error)
        
        try:
            from app.tools._search_impl import search_web
            results = await search_web(query, num_results)
            return ToolResult(True, result=results)
        except Exception as e:
            return ToolResult(False, error=str(e))


class WebFetchTool(BaseTool):
    """网页获取工具"""
    
    def __init__(self):
        super().__init__("web_fetch", "获取网页内容", ToolType.WEB_FETCH)
    
    async def execute(self, url: str, **kwargs) -> ToolResult:
        """获取网页"""
        error = self.validate_params({"url": url}, ["url"])
        if error:
            return ToolResult(False, error=error)
        
        try:
            from app.tools._web_fetch_impl import fetch_url
            content = await fetch_url(url)
            return ToolResult(True, result=content)
        except Exception as e:
            return ToolResult(False, error=str(e))


class FileReadTool(BaseTool):
    """文件读取工具"""
    
    def __init__(self):
        super().__init__("file_read", "读取文件内容", ToolType.FILE_READ)
    
    async def execute(self, path: str, offset: int = 0, limit: int = 2000, **kwargs) -> ToolResult:
        """读取文件"""
        error = self.validate_params({"path": path}, ["path"])
        if error:
            return ToolResult(False, error=error)
        
        try:
            path = os.path.expanduser(path)
            if not os.path.exists(path):
                return ToolResult(False, error=f"文件不存在: {path}")
            
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            
            lines = content.split("\n")
            if offset > 0 or limit < len(lines):
                lines = lines[offset:offset+limit]
            
            return ToolResult(True, result={
                "path": path,
                "content": "\n".join(lines),
                "total_lines": len(content.split("\n")),
                "showing": f"{offset+1}-{offset+len(lines)}"
            })
        except Exception as e:
            return ToolResult(False, error=str(e))


class FileWriteTool(BaseTool):
    """文件写入工具"""
    
    def __init__(self):
        super().__init__("file_write", "写入文件内容", ToolType.FILE_WRITE)
    
    async def execute(self, path: str, content: str, append: bool = False, **kwargs) -> ToolResult:
        """写入文件"""
        error = self.validate_params({"path": path, "content": content}, ["path", "content"])
        if error:
            return ToolResult(False, error=error)
        
        try:
            path = os.path.expanduser(path)
            os.makedirs(os.path.dirname(path), exist_ok=True)
            
            mode = "a" if append else "w"
            with open(path, mode, encoding="utf-8") as f:
                f.write(content)
            
            return ToolResult(True, result={"path": path, "written": len(content)})
        except Exception as e:
            return ToolResult(False, error=str(e))


class ExecuteCodeTool(BaseTool):
    """代码执行工具"""
    
    def __init__(self):
        super().__init__("execute_code", "执行Python代码", ToolType.EXECUTE_CODE)
        self._allowed_modules = ["json", "os", "re", "asyncio", "math", "random", "datetime", "collections", "itertools"]
    
    async def execute(self, code: str, timeout: int = 30, **kwargs) -> ToolResult:
        """执行代码"""
        error = self.validate_params({"code": code}, ["code"])
        if error:
            return ToolResult(False, error=error)
        
        try:
            from app.tools._execute_code_impl import execute_safe
            result = await execute_safe(code, timeout, self._allowed_modules)
            return ToolResult(True, result=result)
        except Exception as e:
            return ToolResult(False, error=str(e))


class ScreenshotTool(BaseTool):
    """截图工具"""
    
    def __init__(self):
        super().__init__("screenshot", "屏幕截图", ToolType.SCREENSHOT)
    
    async def execute(self, save_path: Optional[str] = None, **kwargs) -> ToolResult:
        """截取屏幕"""
        try:
            from app.tools._screenshot_impl import capture_screen
            result = await capture_screen(save_path)
            return ToolResult(True, result=result)
        except Exception as e:
            return ToolResult(False, error=str(e))


class KeyboardTool(BaseTool):
    """键盘控制工具"""
    
    def __init__(self):
        super().__init__("keyboard", "键盘控制", ToolType.KEYBOARD)
    
    async def execute(self, keys: str, hold: float = 0.1, **kwargs) -> ToolResult:
        """按键"""
        error = self.validate_params({"keys": keys}, ["keys"])
        if error:
            return ToolResult(False, error=error)
        
        try:
            from app.tools._keyboard_impl import press_keys
            await press_keys(keys, hold)
            return ToolResult(True, result={"pressed": keys})
        except Exception as e:
            return ToolResult(False, error=str(e))


class ShellTool(BaseTool):
    """Shell命令工具"""
    
    def __init__(self):
        super().__init__("shell", "执行Shell命令", ToolType.SHELL)
    
    async def execute(self, command: str, timeout: int = 30, **kwargs) -> ToolResult:
        """执行Shell命令"""
        error = self.validate_params({"command": command}, ["command"])
        if error:
            return ToolResult(False, error=error)
        
        try:
            proc = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            try:
                stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
                return ToolResult(True, result={
                    "stdout": stdout.decode("utf-8", errors="ignore"),
                    "stderr": stderr.decode("utf-8", errors="ignore"),
                    "returncode": proc.returncode
                })
            except asyncio.TimeoutError:
                proc.kill()
                return ToolResult(False, error="命令超时")
        except Exception as e:
            return ToolResult(False, error=str(e))


class ToolSystem:
    """
    工具系统 - 管理所有可用工具
    """
    
    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}
        self._register_default_tools()
    
    def _register_default_tools(self):
        """注册默认工具"""
        self.register_tool(SearchTool())
        self.register_tool(WebFetchTool())
        self.register_tool(FileReadTool())
        self.register_tool(FileWriteTool())
        self.register_tool(ExecuteCodeTool())
        self.register_tool(ScreenshotTool())
        self.register_tool(KeyboardTool())
        self.register_tool(ShellTool())
        logger.info(f"已注册 {len(self._tools)} 个工具")
    
    def register_tool(self, tool: BaseTool):
        """注册工具"""
        self._tools[tool.name] = tool
    
    def get_tool(self, name: str) -> Optional[BaseTool]:
        """获取工具"""
        return self._tools.get(name)
    
    def list_tools(self) -> List[Dict]:
        """列出所有工具"""
        return [
            {"name": t.name, "description": t.description, "type": t.tool_type.value}
            for t in self._tools.values()
        ]
    
    async def execute(self, tool_name: str, **kwargs) -> ToolResult:
        """执行工具"""
        tool = self.get_tool(tool_name)
        if not tool:
            return ToolResult(False, error=f"工具不存在: {tool_name}")
        
        try:
            return await tool.execute(**kwargs)
        except Exception as e:
            return ToolResult(False, error=str(e))


# 全局实例
tool_system = ToolSystem()