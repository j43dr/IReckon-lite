from loguru import logger
from typing import Dict, Any


class SecurityFilter:
    def __init__(self):
        self.blocked = ["hack", "exploit", "malware"]
        self.command_filter = CommandFilter()

    async def check(self, content: str) -> Dict[str, Any]:
        for word in self.blocked:
            if word in content.lower():
                return {"allowed": False, "reason": "blocked"}
        return {"allowed": True}


class CommandFilter:
    def check(self, cmd: str) -> bool:
        dangerous = ["rm -rf", "format", "del /s"]
        return not any(d in cmd for d in dangerous)


security_filter = SecurityFilter()
command_filter = CommandFilter()