from loguru import logger
from typing import Dict, Any, List, Optional
from .types import TaskStatus
from app.core.database import db
import asyncio
import json


class WorkflowEngine:
    def __init__(self):
        self._phase_handlers = {
            "analysis": self._handle_analysis,
            "planning": self._handle_planning,
            "execution": self._handle_execution,
            "review": self._handle_review,
            "revision": self._handle_revision,
            "delivery": self._handle_delivery,
        }

    async def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        phases = state.get("phases", [])
        if not phases:
            state["status"] = TaskStatus.COMPLETED
            return state

        team = state.get("team", {})
        artifacts = state.get("artifacts", {})

        for i, phase in enumerate(phases):
            if state.get("status") in (TaskStatus.CANCELLED, TaskStatus.FAILED):
                break
            state["current_phase"] = i
            state["status"] = TaskStatus.EXECUTING

            phase_type = phase.get("type", phase.get("role", "execution"))
            phase_desc = phase.get("description", "")
            logger.info(f"执行阶段 {i + 1}/{len(phases)}: [{phase_type}] {phase_desc}")

            room = state.get("room")
            if room:
                try:
                    await room.send_message("system", f"阶段 {i + 1}: {phase_desc}")
                except Exception:
                    pass

            handler = self._phase_handlers.get(phase_type, self._handle_default)
            try:
                phase_result = await handler(state, phase, team)
                artifacts[f"phase_{i}"] = phase_result
                if phase_result.get("failed"):
                    state["error"] = phase_result.get("error", "阶段失败")
                    state["status"] = TaskStatus.FAILED
                    break
            except Exception as e:
                logger.error(f"阶段 {i + 1} 异常: {e}")
                state["error"] = str(e)
                state["status"] = TaskStatus.FAILED
                break

        if state["status"] != TaskStatus.FAILED:
            state["status"] = TaskStatus.COMPLETED
        return state

    async def _handle_analysis(self, state: Dict, phase: Dict, team: Dict) -> Dict:
        task_req = state.get("user_request", "")
        return {"phase": "analysis", "summary": f"已分析需求: {task_req[:50]}..."}

    async def _handle_planning(self, state: Dict, phase: Dict, team: Dict) -> Dict:
        agents = team.get("planner", []) or team.get("scheduler", [])
        plans = []
        for agent in agents:
            try:
                result = await agent.execute(phase.get("description", ""), state.get("task_id", ""))
                plans.append(result)
            except Exception as e:
                logger.warning(f"规划agent执行失败: {e}")
        return {"phase": "planning", "plans": plans}

    async def _handle_execution(self, state: Dict, phase: Dict, team: Dict) -> Dict:
        agents = team.get("executor", []) or team.get("default", [])
        results = []
        for agent in agents:
            try:
                result = await agent.execute({"task_id": state.get("task_id"), **phase})
                results.append(result)
            except Exception as e:
                logger.warning(f"执行agent失败: {e}")
        return {"phase": "execution", "results": results}

    async def _handle_review(self, state: Dict, phase: Dict, team: Dict) -> Dict:
        agents = team.get("reviewer", [])
        if not agents:
            return {"phase": "review", "skipped": True}
        reviews = []
        for agent in agents:
            try:
                result = await agent.review(json.dumps(state.get("artifacts", {})))
                reviews.append(result)
            except Exception as e:
                logger.warning(f"审查agent失败: {e}")
        return {"phase": "review", "reviews": reviews}

    async def _handle_revision(self, state: Dict, phase: Dict, team: Dict) -> Dict:
        return {"phase": "revision", "message": "根据反馈进行修订"}

    async def _handle_delivery(self, state: Dict, phase: Dict, team: Dict) -> Dict:
        agents = team.get("deliverer", [])
        for agent in agents:
            try:
                await agent.deliver(json.dumps(state.get("artifacts", {}), ensure_ascii=False))
            except Exception:
                pass
        return {"phase": "delivery", "delivered": True}

    async def _handle_default(self, state: Dict, phase: Dict, team: Dict) -> Dict:
        return {"phase": phase.get("type", "default"), "status": "completed"}

    def _looks_like_python(self, code: str) -> bool:
        import re
        python_indicators = [
            r'\bdef\s+\w+\s*\(', r'\bclass\s+\w+', r'\bimport\s+\w+',
            r'\bfrom\s+\w+\s+import', r'\bif\s+__name__', r'\breturn\b',
            r'\bprint\s*\(', r'\bfor\s+\w+\s+in', r'\bwhile\b', r'\btry\b',
            r'^\s*@', r'^\s*#',
        ]
        for pattern in python_indicators:
            if re.search(pattern, code, re.MULTILINE):
                return True
        return False

    def _check_python_syntax(self, code: str) -> List[str]:
        errors = []
        try:
            compile(code, '<check>', 'exec')
        except SyntaxError as e:
            errors.append(f"Line {e.lineno}: {e.msg}")
        return errors

    def _is_placeholder_code(self, code: str) -> bool:
        placeholders = [
            "todo", "implement me", "your code here", "fixme",
            "pass  #", "# your", "// todo", "/* todo */",
        ]
        code_lower = code.lower()
        for p in placeholders:
            if p in code_lower:
                return True
        return False

    def _check_html_basics(self, code: str) -> List[str]:
        errors = []
        if "<html" not in code and "<body" not in code and "<div" not in code:
            return errors
        import re
        open_tags = re.findall(r'<(\w+)[^>]*>', code)
        close_tags = re.findall(r'</(\w+)>', code)
        void_elements = {'br', 'hr', 'img', 'input', 'meta', 'link', 'area', 'base', 'col', 'embed', 'source', 'track', 'wbr'}
        stack = []
        for tag in open_tags:
            if tag.lower() not in void_elements:
                stack.append(tag.lower())
        for tag in close_tags:
            t = tag.lower()
            if t in void_elements:
                continue
            if stack and stack[-1] == t:
                stack.pop()
            elif t in stack:
                errors.append(f"[HTML] Unclosed tag: {stack[-1]}")
            else:
                errors.append(f"[HTML] Unexpected closing tag: {t}")
        if stack:
            errors.append(f"[HTML] Unclosed tags: {', '.join(stack)}")
        return errors

    def pre_check_router(self, check_result: Dict) -> str:
        if check_result.get("pre_check_passed"):
            return "pass"
        return "fail"


workflow_engine = WorkflowEngine()
