import uuid
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
import asyncio

from loguru import logger
from app.llm.pool import AICapability
from app.core.logger import log_conversation


@dataclass
class AgentContext:
    task_id: str
    agent_id: str
    role: str
    capability: AICapability
    cancellation_event: asyncio.Event = field(default_factory=asyncio.Event)
    extra: Dict[str, Any] = field(default_factory=dict)


class BaseAgent(ABC):
    def __init__(
        self,
        role: str = "",
        capability: Optional[AICapability] = None,
        system_prompt: str = "",
        llm=None
    ):
        self.role = role
        self.capability = capability
        self.llm = llm
        self.context: Optional[AgentContext] = None
        self.system_prompt = system_prompt

    async def think(self, prompt: str) -> str:
        return "Thinking..."

    async def act(self, action: str) -> Dict[str, Any]:
        return {"status": "done"}

    def bind_context(self, task_id: str):
        self.context = AgentContext(
            task_id=task_id,
            agent_id=str(uuid.uuid4()),
            role=self.role,
            capability=self.capability
        )


class LearnerAgent(BaseAgent):
    def __init__(self, capability=None):
        super().__init__(role="learner", capability=capability, system_prompt="I learn new things.")

    async def learn(self, topic: str, content: str):
        return {"learned": True, "topic": topic}


class ExecutorAgent(BaseAgent):
    def __init__(self, capability=None):
        super().__init__(role="executor", capability=capability, system_prompt="I execute tasks.")

    async def execute(self, task: Dict[str, Any]):
        return {"status": "completed", "task_id": task.get("task_id")}


class ReviewerAgent(BaseAgent):
    def __init__(self, capability=None):
        super().__init__(role="reviewer", capability=capability, system_prompt="I review content.")

    async def review(self, content: str):
        return {"score": 80, "feedback": "OK"}


class DelivererAgent(BaseAgent):
    def __init__(self, capability=None):
        super().__init__(role="deliverer", capability=capability, system_prompt="I deliver results.")

    async def deliver(self, content: str):
        return {"delivered": True, "content": content}


class CreativeAgent(BaseAgent):
    def __init__(self, capability=None):
        super().__init__(role="creative", capability=capability, system_prompt="I generate creative ideas.")

    async def create(self, prompt: str):
        return {"idea": "new idea"}


class ContentFilter(BaseAgent):
    def __init__(self, capability=None):
        super().__init__(role="content_filter", capability=capability, system_prompt="I filter content.")

    async def check(self, content: str):
        return {"allowed": True}


# 全局实例
learner_agent = LearnerAgent()
executor_agent = ExecutorAgent()
reviewer_agent = ReviewerAgent()
deliverer_agent = DelivererAgent()
creative_agent = CreativeAgent()
content_filter = ContentFilter()