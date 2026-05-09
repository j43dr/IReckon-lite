from typing import Dict, Any


class ContentFilter:
    def __init__(self):
        self.role = "content_filter"
        self.blocked_patterns = []

    async def check(self, content: str) -> Dict[str, Any]:
        for pattern in self.blocked_patterns:
            if pattern in content.lower():
                return {"allowed": False, "reason": "blocked_pattern"}
        return {"allowed": True}

    async def filter(self, content: str) -> str:
        result = await self.check(content)
        if result["allowed"]:
            return content
        return "[FILTERED]"


content_filter = ContentFilter()