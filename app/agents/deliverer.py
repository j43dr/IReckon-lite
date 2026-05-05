from loguru import logger
from app.agents.base import BaseAgent
from typing import Dict, Any


class DelivererAgent(BaseAgent):
    def __init__(self, capability=None):
        super().__init__(role="deliverer", capability=capability)
        self.delivery_methods = ["direct", "structured", "summarized"]

    async def deliver(self, content: str, method: str = "direct") -> str:
        if method == "structured":
            lines = content.split("\n")
            return "\n".join([f"{i+1}. {line}" for i, line in enumerate(lines)])
        elif method == "summarized":
            return await self._summarize(content)
        return content

    async def _summarize(self, content: str) -> str:
        words = content.split()
        if len(words) > 50:
            return " ".join(words[:50]) + "..."
        return content


deliverer_agent = DelivererAgent()