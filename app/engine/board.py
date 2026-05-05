from loguru import logger
from typing import Dict, Any


class TaskBoard:
    def __init__(self):
        self.tasks = {}
        self.next_id = 1

    def create_task(self, title: str, description: str = "") -> str:
        task_id = f"task-{self.next_id}"
        self.next_id += 1
        self.tasks[task_id] = {
            "id": task_id,
            "title": title,
            "description": description,
            "status": "pending"
        }
        return task_id

    def get_task(self, task_id: str) -> Dict:
        return self.tasks.get(task_id, {})

    def update_status(self, task_id: str, status: str) -> bool:
        if task_id in self.tasks:
            self.tasks[task_id]["status"] = status
            return True
        return False


task_board = TaskBoard()