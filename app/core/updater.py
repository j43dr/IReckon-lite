import json
import time
from pathlib import Path
from typing import Dict, Any, Optional
from loguru import logger
from app.core.config import config_manager


class CoreUpdater:
    def __init__(self):
        self.version = "3.0"
        self._checked = False
        self._last_check = 0.0
        self._latest_version: Optional[str] = None
        self._data_dir = Path(config_manager.get("system.data_dir", "./data"))
        self._version_file = self._data_dir / "version_check.json"
        self._version_file.parent.mkdir(parents=True, exist_ok=True)
        self._load_state()

    def _load_state(self):
        if self._version_file.exists():
            try:
                with open(self._version_file, 'r') as f:
                    data = json.load(f)
                self._last_check = data.get("last_check", 0.0)
                self._latest_version = data.get("latest_version")
                self._checked = data.get("checked", False)
            except Exception:
                pass

    def _save_state(self):
        try:
            with open(self._version_file, 'w') as f:
                json.dump({
                    "last_check": self._last_check,
                    "latest_version": self._latest_version,
                    "checked": self._checked,
                    "current_version": self.version,
                }, f)
        except Exception as e:
            logger.error(f"Failed to save version state: {e}")

    def should_check(self) -> bool:
        return not self._checked and (time.time() - self._last_check) > 86400

    def mark_checked(self):
        self._checked = True
        self._last_check = time.time()
        self._save_state()

    async def check(self) -> Optional[str]:
        check_url = config_manager.get("updater.check_url", "")
        if check_url:
            try:
                import urllib.request
                req = urllib.request.Request(check_url, method="GET",
                                             headers={"User-Agent": "IReckon/3.0"})
                with urllib.request.urlopen(req, timeout=10) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                    self._latest_version = data.get("version", self.version)
            except Exception as e:
                logger.warning(f"Update check failed: {e}")
                return None

        self._checked = True
        self._last_check = time.time()
        self._save_state()
        return self._latest_version

    async def check_updates(self) -> Dict[str, Any]:
        latest = await self.check()
        if latest is None:
            return {"current": self.version, "latest": self._latest_version or self.version,
                    "up_to_date": True, "checked": False}
        return {"current": self.version, "latest": latest,
                "up_to_date": latest == self.version, "checked": True}

    async def apply_update(self, update: Dict) -> bool:
        version = update.get("version", "")
        logger.info(f"Applying update: {version}")
        self._latest_version = version
        self.version = version
        self._save_state()
        return True


core_updater = CoreUpdater()
updater = core_updater