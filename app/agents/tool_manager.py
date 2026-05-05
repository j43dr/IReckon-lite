from loguru import logger
from typing import Dict, Any, List


class ToolManager:
    def __init__(self):
        self.tools = {}
        self._register_defaults()

    def _register_defaults(self):
        defaults = {
            "search": {"description": "Search web", "enabled": True},
            "web_fetch": {"description": "Fetch webpage", "enabled": True},
            "file_read": {"description": "Read file", "enabled": True},
            "file_write": {"description": "Write file", "enabled": True},
            "execute_code": {"description": "Execute code", "enabled": True},
            "screenshot": {"description": "Take screenshot", "enabled": True},
        }
        for name, config in defaults.items():
            if name not in self.tools:
                self.tools[name] = config

    def get_tool(self, name: str) -> Dict:
        return self.tools.get(name, {})

    def list_tools(self) -> List[str]:
        return list(self.tools.keys())

    def is_enabled(self, name: str) -> bool:
        tool = self.get_tool(name)
        return tool.get("enabled", False)


tool_manager = ToolManager()