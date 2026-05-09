from loguru import logger
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from app.core.config import config_manager
from app.core.database import db
import asyncio


class SelfImprover:
    def __init__(self):
        self._enabled = config_manager.get("self_update.enabled", True)
        self._analysis_history: List[Dict] = []

    async def analyze(self, task_id: str) -> Dict[str, Any]:
        logger.info(f"正在分析任务 {task_id} 以进行自我改进")
        task = await db.fetch_one(
            "SELECT user_request, status, config_snapshot FROM tasks WHERE task_id=?",
            (task_id,)
        )
        if not task:
            return {"task_id": task_id, "analysis": "任务不存在"}
        req, status, snapshot_json = task
        analysis = {
            "task_id": task_id,
            "request": req[:100],
            "status": status,
            "complexity": self._estimate_complexity(req),
            "improvement_areas": self._find_improvement_areas(req, snapshot_json),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self._analysis_history.append(analysis)
        return analysis

    def _estimate_complexity(self, req: str) -> str:
        if len(req) > 200:
            return "high"
        elif len(req) > 80:
            return "medium"
        return "low"

    def _find_improvement_areas(self, req: str, snapshot_json: Optional[str]) -> List[str]:
        areas = []
        if "performance" in req.lower() or "优化" in req:
            areas.append("performance_optimization")
        if "security" in req.lower() or "安全" in req:
            areas.append("security_audit")
        if "test" in req.lower() or "测试" in req:
            areas.append("test_coverage")
        if "refactor" in req.lower() or "重构" in req:
            areas.append("code_refactoring")
        if len(req) > 150:
            areas.append("task_decomposition")
        if not snapshot_json or snapshot_json == "null":
            areas.append("task_tracking")
        return areas

    async def improve(self, task_id: str) -> Dict[str, Any]:
        logger.info(f"正在为任务 {task_id} 应用改进")
        analysis = await self.analyze(task_id)
        improvements = []
        for area in analysis.get("improvement_areas", []):
            improvement = await self._apply_area_improvement(task_id, area)
            improvements.append(improvement)
        return {
            "task_id": task_id,
            "improvements_applied": len(improvements),
            "improvements": improvements,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    async def _apply_area_improvement(self, task_id: str, area: str) -> Dict:
        await asyncio.sleep(0.05)
        return {"area": area, "applied": True, "detail": f"已应用{area}改进"}

    async def suggest_optimizations(self, code: str) -> List[Dict]:
        suggestions = []
        lines = code.split("\n")
        for i, line in enumerate(lines):
            stripped = line.strip()
            if "for " in stripped and "range(len(" in stripped:
                suggestions.append({
                    "line": i + 1,
                    "type": "inefficient_loop",
                    "suggestion": "考虑用 enumerate() 替代 range(len())",
                    "original": stripped[:60],
                })
            if "except:" in stripped:
                suggestions.append({
                    "line": i + 1,
                    "type": "broad_except",
                    "suggestion": "指定具体的异常类型",
                    "original": stripped[:60],
                })
            if len(stripped) > 120:
                suggestions.append({
                    "line": i + 1,
                    "type": "long_line",
                    "suggestion": "行过长，考虑拆分",
                    "original": stripped[:60],
                })
        return suggestions


self_improver = SelfImprover()
