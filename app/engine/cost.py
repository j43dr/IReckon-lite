from loguru import logger
from app.core.config import config_manager


class CostTracker:
    def __init__(self):
        self.daily_budget = config_manager.get("cost.daily_budget", 1000)
        self.monthly_budget = config_manager.get("cost.monthly_budget", 10000)
        self._daily_spent = 0
        self._monthly_spent = 0

    async def track(self, tokens: int, model: str):
        cost = tokens * 0.001
        self._daily_spent += cost
        self._monthly_spent += cost
        logger.info(f"Cost: ${cost:.4f} ({tokens} tokens, {model})")

    async def get_status(self):
        return {
            "daily_spent": self._daily_spent,
            "daily_budget": self.daily_budget,
            "monthly_spent": self._monthly_spent,
            "monthly_budget": self.monthly_budget
        }


cost_tracker = CostTracker()