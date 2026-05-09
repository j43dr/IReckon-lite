from loguru import logger
from typing import Dict, Any, List, Optional, Callable, Tuple
from enum import Enum
import asyncio

class MessageSource(Enum):
    USER = "user"
    PUBLIC_SQUARE = "public"
    PRIVATE = "private"
    AI = "ai"

class MessageTrigger:
    def __init__(self, source: MessageSource, content_pattern: Optional[str] = None):
        self.source = source
        self.content_pattern = content_pattern

class RoleStateMachine:
    def __init__(self):
        self._triggers: Dict[str, List[Tuple[MessageTrigger, Callable]]] = {}
        self._role_states: Dict[str, str] = {}
        self._public_messages: List[Dict] = []
        
    def register_trigger(self, role: str, trigger: MessageTrigger, callback: Callable):
        if role not in self._triggers:
            self._triggers[role] = []
        self._triggers[role].append((trigger, callback))
        
    def set_role_state(self, role: str, state: str):
        old_state = self._role_states.get(role, "idle")
        self._role_states[role] = state
        logger.info(f"角色 {role}: {old_state} -> {state}")
        
    def get_role_state(self, role: str) -> str:
        return self._role_states.get(role, "idle")
        
    async def handle_public_message(self, content: str, sender: str, layer: str = "L1") -> List[Dict]:
        msg = {
            "content": content,
            "sender": sender,
            "layer": layer,
            "timestamp": self._get_timestamp()
        }
        self._public_messages.append(msg)
        
        responses = []
        
        if layer == "L1" and sender != "user":
            from app.core.config import config_manager
            show_in_public = config_manager.get("show_roles_in_public", True)
            
            if show_in_public:
                for role_id, callbacks in self._triggers.items():
                    for trigger, callback in callbacks:
                        if trigger.source == MessageSource.PUBLIC_SQUARE:
                            try:
                                if asyncio.iscoroutinefunction(callback):
                                    result = await callback(msg)
                                else:
                                    result = callback(msg)
                                if result:
                                    responses.append({
                                        "role": role_id,
                                        "content": result,
                                        "source": "trigger"
                                    })
                            except Exception as e:
                                logger.error(f"Trigger callback error: {e}")
                                
        return responses
        
    def _get_timestamp(self) -> str:
        from datetime import datetime, timezone
        return datetime.now(timezone.utc).isoformat()
        
    def get_recent_public_messages(self, limit: int = 10) -> List[Dict]:
        return self._public_messages[-limit:]

def create_default_triggers() -> List[tuple]:
    return [
        (
            MessageTrigger(MessageSource.PUBLIC_SQUARE, None),
            lambda msg: logger.info(f"Public message from {msg.get('sender')}") or None
        ),
    ]

role_state_machine = RoleStateMachine()
for trigger, callback in create_default_triggers():
    role_state_machine.register_trigger("scheduler", trigger, callback)