import json
import asyncio
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
from app.core.config import config_manager
from loguru import logger

STATE_DIR = Path(config_manager.get("system.data_dir", "./data")) / "consciousness"
STATE_DIR.mkdir(parents=True, exist_ok=True)


class ConsciousnessState:
    def __init__(self):
        self.current_state = {}
        self.history = []

    def save_state(self, state: Dict[str, Any]):
        self.current_state = state
        self.history.append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "state": state
        })

    def get_state(self) -> Dict[str, Any]:
        return self.current_state

    def get_history(self) -> List[Dict]:
        return self.history[-10:]


consciousness_state = ConsciousnessState()