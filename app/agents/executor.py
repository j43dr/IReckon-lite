from typing import Dict, Any


class ExecutorAgent:
    def __init__(self, capability=None):
        self.role = "executor"

    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        return {"status": "completed", "task_id": task.get("task_id")}


executor_agent = ExecutorAgent()