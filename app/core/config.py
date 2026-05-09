import os
import re
import yaml
import threading
import atexit
from pathlib import Path
from typing import Any, Dict, Optional
from loguru import logger

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False

class ConfigManager:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if hasattr(self, "_init") and self._init:
            return
        self._init = True
        self._config_lock = threading.RLock()
        self._observer = None
        base_dir = Path(os.environ.get("IRECKON_HOME", ".")).resolve()
        self.config_path = base_dir / "config" / "config.yaml"
        if not self.config_path.exists():
            self.config_path = Path("config/config.yaml")
        self.config = {}
        self._load_config()
        self._start_watcher()
        atexit.register(self.shutdown)

    def _load_config(self):
        if not self.config_path.exists():
            self.config = {"system": {"version": "3.0", "data_dir": "./data", "output_dir": "./data/outputs"}}
            return
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                raw = yaml.safe_load(f) or {}
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            raw = {}
        self.config = self._expand_env_vars(raw)

    def _expand_env_vars(self, obj):
        if isinstance(obj, dict):
            return {k: self._expand_env_vars(v) for k, v in obj.items()}
        elif isinstance(obj, str):
            def replacer(m):
                expr = m.group(1)
                if ":-" in expr:
                    v, d = expr.split(":-", 1)
                    return os.environ.get(v, d)
                return os.environ.get(expr, "")
            return re.sub(r"\${([^}]+)}", replacer, obj)
        return obj

    def _start_watcher(self):
        if not WATCHDOG_AVAILABLE:
            return
        try:
            self._observer = Observer()
            def handler(s, e):
                if "config.yaml" in str(e.src_path):
                    self._load_config()
            h = type("H", (FileSystemEventHandler,), {"on_modified": handler})()
            self._observer.schedule(h, path=str(self.config_path.parent), recursive=False)
            self._observer.start()
        except Exception:
            self._observer = None

    def shutdown(self):
        if self._observer:
            self._observer.stop()
            self._observer.join(timeout=1.0)

    def reload(self):
        self._load_config()

    def get(self, key, default=None):
        value = self.config
        try:
            for k in key.split("."):
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default

    def get_all(self):
        import copy
        return copy.deepcopy(self.config)

    def update(self, key, value):
        """更新配置值（内存中）"""
        keys = key.split(".")
        current = self.config
        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]
        current[keys[-1]] = value

    def update_nested(self, updates: Dict[str, Any]):
        """批量更新嵌套配置"""
        for key, value in updates.items():
            self.update(key, value)

    def save(self):
        """保存配置到文件"""
        import copy
        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                yaml.dump(copy.deepcopy(self.config), f, default_flow_style=False, allow_unicode=True)
            logger.info(f"Config saved to {self.config_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to save config: {e}")
            return False


config_manager = ConfigManager()
