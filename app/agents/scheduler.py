from typing import Dict, Any


class SchedulerAgent:
    def __init__(self, capability=None):
        self.capability = capability
        self.task_id = None
        self.cancellation_event = None

    def bind_context(self, task_id: str, cancellation_event=None):
        self.task_id = task_id
        self.cancellation_event = cancellation_event

    async def execute(self, req: str, task_id: str) -> Dict[str, Any]:
        return {
            "plan": {"phases": [{"phase": "默认", "description": req}]},
            "team": {},
            "task_board_state": {},
        }

    async def schedule(self, task: Dict[str, Any]) -> Dict[str, Any]:
        return {"status": "scheduled", "task_id": task.get("task_id")}

    async def cancel(self, task_id: str) -> bool:
        return True


scheduler_agent = SchedulerAgent()