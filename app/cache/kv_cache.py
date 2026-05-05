#!/usr/bin/env python3
"""KV Cache for 3.0 self-sustaining state"""
import json
from pathlib import Path
from app.core.config import config_manager

CACHE_ROOT = Path(config_manager.get("system.data_dir", "./data")) / "cache"
CACHE_ROOT.mkdir(parents=True, exist_ok=True)
CACHE_FILE = CACHE_ROOT / "kv_cache.json"

def load_kv_cache() -> dict:
    if not CACHE_FILE.exists():
        return {}
    try:
        with open(CACHE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {}

def save_kv_cache(data: dict) -> None:
    with open(CACHE_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)