#!/usr/bin/env python3
"""2.0 Self bootstrap orchestrator

This module coordinates a self-improvement run in a safe, testable way.
"""

import asyncio
from typing import Dict
from app.engine.self_improve import self_improver

async def bootstrap_run(dry_run: bool = True) -> Dict[str, object]:
    """Run bootstrap"""
    if not getattr(self_improver, "_enabled", True):
        return {"enabled": False, "dry_run": dry_run}
    
    task_id = f"bootstrap-{asyncio.get_running_loop().time()}"
    try:
        analysis = await self_improver.analyze(task_id)
        if dry_run:
            return {"enabled": True, "dry_run": dry_run, "analysis": analysis}
        else:
            return {"enabled": True, "dry_run": dry_run, "applied": True}
    except Exception as e:
        return {"enabled": False, "error": str(e)}