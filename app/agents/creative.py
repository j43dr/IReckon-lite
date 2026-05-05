from loguru import logger
from app.agents.base import BaseAgent
from typing import Dict, Any, List


class CreativeAgent(BaseAgent):
    def __init__(self, capability=None):
        super().__init__(role="creative", capability=capability)
        self.techniques = ["analogy", "contrast", "combination", "exaggeration"]

    async def generate(self, prompt: str) -> Dict[str, Any]:
        response = await self.think(prompt)
        return {"creative_output": response, "techniques_used": self.techniques}

    async def brainstorm(self, topic: str) -> List[str]:
        prompt = f"Generate creative ideas for: {topic}"
        response = await self.think(prompt)
        ideas = [line.strip() for line in response.split("\n") if line.strip()]
        return ideas[:5]


creative_agent = CreativeAgent()