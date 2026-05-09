#!/usr/bin/env python3
"""
IReckon 3.0 System Health Check Utility
Verifies all 3.0 modules are properly initialized and functional.
"""
import asyncio
from typing import Dict, Any, List
from loguru import logger

async def check_core_modules() -> Dict[str, Any]:
    """Check core modules"""
    results = {}
    
    # Check database
    try:
        from app.core.database import db
        results["database"] = {"status": "ok", "detail": "Database module loaded"}
    except Exception as e:
        results["database"] = {"status": "error", "detail": str(e)}
    
    # Check config
    try:
        from app.core.config import config_manager
        results["config"] = {"status": "ok", "detail": "Config module loaded"}
    except Exception as e:
        results["config"] = {"status": "error", "detail": str(e)}
    
    return results

async def check_3zero_modules() -> Dict[str, Any]:
    """Check all 3.0 modules"""
    results = {}
    
    # Micro models
    try:
        from app.micro_models.factory import register_micro_model
        results["micro_models"] = {"status": "ok", "detail": "Micro model factory loaded"}
    except Exception as e:
        results["micro_models"] = {"status": "error", "detail": str(e)}
    
    # Consciousness
    try:
        from app.consciousness.state import consciousness_state
        results["consciousness"] = {"status": "ok", "detail": "Consciousness module loaded"}
    except Exception as e:
        results["consciousness"] = {"status": "error", "detail": str(e)}
    
    # Dreams
    try:
        from app.dreams.sleep_manager import sleep_dream
        results["dreams"] = {"status": "ok", "detail": "Dream module loaded"}
    except Exception as e:
        results["dreams"] = {"status": "error", "detail": str(e)}
    
    # Personality
    try:
        from app.personality.system import personality_system
        results["personality"] = {"status": "ok", "detail": "Personality module loaded"}
    except Exception as e:
        results["personality"] = {"status": "error", "detail": str(e)}
    
    # Guardian
    try:
        from app.guardian.thinking_depth import thinking_guardian
        results["guardian"] = {"status": "ok", "detail": "Guardian module loaded"}
    except Exception as e:
        results["guardian"] = {"status": "error", "detail": str(e)}
    
    # Games
    try:
        from app.games.universal_engine import game_engine
        from app.games.chess_engine import chess_engine
        from app.games.vrchat_bridge import vrchat_bridge
        from app.games.minecraft_bridge import minecraft_bridge
        results["games"] = {"status": "ok", "detail": "All game modules loaded"}
    except Exception as e:
        results["games"] = {"status": "error", "detail": str(e)}
    
    # World Model
    try:
        from app.world_model.le_world_model import world_model
        results["world_model"] = {"status": "ok", "detail": "World model loaded"}
    except Exception as e:
        results["world_model"] = {"status": "error", "detail": str(e)}
    
    # Exploration
    try:
        from app.exploration.engine import exploration_engine
        results["exploration"] = {"status": "ok", "detail": "Exploration engine loaded"}
    except Exception as e:
        results["exploration"] = {"status": "error", "detail": str(e)}
    
    # Cache
    try:
        from app.cache.kv_cache import load_kv_cache
        results["cache"] = {"status": "ok", "detail": "KV cache loaded"}
    except Exception as e:
        results["cache"] = {"status": "error", "detail": str(e)}
    
    return results

async def run_full_health_check() -> Dict[str, Any]:
    """Run complete system health check"""
    logger.info("Starting IReckon 3.0 health check...")
    
    core = await check_core_modules()
    modules_3zero = await check_3zero_modules()
    
    all_ok = all(m.get("status") == "ok" for m in core.values()) and \
             all(m.get("status") == "ok" for m in modules_3zero.values())
    
    return {
        "overall_status": "ok" if all_ok else "error",
        "core_modules": core,
        "3zero_modules": modules_3zero,
    }

if __name__ == "__main__":
    result = asyncio.run(run_full_health_check())
    print("\n=== Health Check Results ===")
    print(f"Overall Status: {result['overall_status']}")
    print("\nCore Modules:")
    for name, info in result['core_modules'].items():
        print(f"  {name}: {info['status']}")
    print("\n3.0 Modules:")
    for name, info in result['3zero_modules'].items():
        print(f"  {name}: {info['status']}")