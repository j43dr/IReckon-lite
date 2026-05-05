from loguru import logger
from typing import Dict, Any, List


class BaseAgent:
    def __init__(self, role: str, system_prompt: str = ""):
        self.role = role
        self.system_prompt = system_prompt

    async def think(self, prompt: str) -> str:
        return f"Thought about: {prompt}"

    async def act(self, action: str) -> Dict:
        return {"status": "done", "action": action}


class LearnerAgent(BaseAgent):
    def __init__(self, capability=None):
        super().__init__(role="learner", system_prompt="I learn things.")
        self.learned_topics = []

    async def learn(self, topic: str, content: str) -> Dict[str, Any]:
        logger.info(f"Learning: {topic}")
        self.learned_topics.append({"topic": topic})
        return {"learned": True, "topic": topic}


learner_agent = LearnerAgent()


class ExecutorAgent(BaseAgent):
    def __init__(self, capability=None):
        super().__init__(role="executor", system_prompt="I execute tasks.")

    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        return {"status": "completed", "task_id": task.get("task_id")}


executor_agent = ExecutorAgent()


class ContentFilter(BaseAgent):
    def __init__(self, capability=None):
        super().__init__(role="content_filter", system_prompt="I filter content.")
        self.blocked_patterns = []

    async def check(self, content: str) -> Dict[str, Any]:
        for pattern in self.blocked_patterns:
            if pattern in content.lower():
                return {"allowed": False}
        return {"allowed": True}


content_filter = ContentFilter()