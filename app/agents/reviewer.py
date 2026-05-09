from loguru import logger
from app.agents.base import BaseAgent
from typing import Dict, Any


class ReviewerAgent(BaseAgent):
    def __init__(self, capability=None):
        super().__init__(role="reviewer", capability=capability)
        self.criteria = ["accuracy", "completeness", "clarity"]

    async def review(self, content: str) -> Dict[str, Any]:
        score = 80
        feedback = "Good result"
        
        return {
            "score": score,
            "feedback": feedback,
            "criteria_met": self.criteria
        }


reviewer_agent = ReviewerAgent()