from loguru import logger
from typing import Dict, Any
import time


class CoreUpdater:
    def __init__(self):
        self.version = "3.0"
        self._checked = False
        self._last_check = 0
        
    def should_check(self) -> bool:
        return not self._checked and (time.time() - self._last_check) > 86400
        
    def mark_checked(self):
        self._checked = True
        self._last_check = time.time()
        
    async def check(self) -> str:
        return None
        
    async def check_updates(self) -> Dict[str, Any]:
        return {"current": self.version, "up_to_date": True}
        
    async def apply_update(self, update: Dict) -> bool:
        logger.info(f"Applying update: {update.get('version')}")
        return True
        

core_updater = CoreUpdater()
updater = core_updater  # 兼容导入