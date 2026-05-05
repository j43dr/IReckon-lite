from loguru import logger
from typing import Dict, Any, List
from app.engine.registry import role_registry


class WorkflowEngine:
    def __init__(self):
        self.workflows = {}

    def register_workflow(self, name: str, steps: List[str]):
        self.workflows[name] = steps

    async def execute(self, workflow_name: str, context: Dict) -> Dict:
        steps = self.workflows.get(workflow_name, [])
        results = []
        
        for step in steps:
            logger.info(f"Executing step: {step}")
            results.append({"step": step, "status": "done"})
        
        return {"workflow": workflow_name, "results": results}

    def list_workflows(self) -> List[str]:
        return list(self.workflows.keys())


workflow_engine = WorkflowEngine()