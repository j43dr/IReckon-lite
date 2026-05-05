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
        except:
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
        except:
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
        except:
            return default

    def get_all(self):
        import copy
        return copy.deepcopy(self.config)


config_manager = ConfigManager()
