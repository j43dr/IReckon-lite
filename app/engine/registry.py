from loguru import logger
from app.core.config import config_manager
from typing import Dict, Any


class RoleRegistry:
    def __init__(self):
        self.roles = config_manager.get("roles", {})
        self._register_defaults()

    def _register_defaults(self):
        defaults = {
            "executor": {"description": "执行任务", "priority": 1},
            "reviewer": {"description": "审查结果", "priority": 2},
            "learner": {"description": "学习新知识", "priority": 3},
        }
        for name, config in defaults.items():
            if name not in self.roles:
                self.roles[name] = config

    def get_role(self, name: str) -> Dict:
        return self.roles.get(name, {})

    def list_roles(self):
        return list(self.roles.keys())

    def register_role(self, name: str, config: Dict):
        self.roles[name] = config


role_registry = RoleRegistry()

# 兼容旧API
register_role = role_registry.register_role