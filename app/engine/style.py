from loguru import logger
from app.core.config import config_manager
from typing import Dict, Any


class StyleManager:
    def __init__(self):
        self.default_style = config_manager.get("style.default", "professional")
        self.styles = {
            "professional": {"tone": "formal", "length": "medium"},
            "casual": {"tone": "informal", "length": "short"},
            "creative": {"tone": "creative", "length": "varied"},
        }

    def get_style(self, name: str = None) -> Dict[str, Any]:
        style_name = name or self.default_style
        return self.styles.get(style_name, self.styles[self.default_style])


style_manager = StyleManager()