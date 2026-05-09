import asyncio, uuid, json
from typing import Dict, Any, Optional, List

from loguru import logger
from .types import TaskStatus, TaskState
from app.core.state import StateManager
from app.core.database import db
from app.core.config import config_manager
from app.llm.pool import capability_pool, AICapability
from .room import meeting_room_manager, MeetingRoom, MessageLayer
from .board import TaskBoard
from .learner import idle_loop


class TaskManager:
    _instance: Optional["TaskManager"] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if hasattr(self, "_init") and self._init:
            return
        self._init = True
        self._running: Dict[str, asyncio.Task] = {}
        self._cancel_events: Dict[str, asyncio.Event] = {}

    async def create_task(self, req: str) -> str:
        tid = f"task-{uuid.uuid4().hex[:8]}"
        await db.execute("INSERT INTO tasks(task_id, user_request, status) VALUES(?,?,?)", (tid, req, TaskStatus.PENDING.value))
        return tid

    async def start_task(self, tid: str, scid: Optional[str] = None):
        if tid in self._running:
            return
        ce = asyncio.Event()
        self._cancel_events[tid] = ce

        async def _run():
            try:
                md = config_manager.get("task_defaults.max_task_duration_seconds", 3600)
                await asyncio.wait_for(self._execute_task(tid, scid, ce), timeout=md)
            except (asyncio.TimeoutError, asyncio.CancelledError):
                logger.error(f"任务{tid}超时/取消")
                ce.set()
                await db.execute("UPDATE tasks SET status=? WHERE task_id=?", (TaskStatus.FAILED.value, tid))
            except Exception as e:
                logger.exception(f"任务{tid}异常: {e}")
                await db.execute("UPDATE tasks SET status=? WHERE task_id=?", (TaskStatus.FAILED.value, tid))
            finally:
                self._running.pop(tid, None)
                self._cancel_events.pop(tid, None)
                await meeting_room_manager.close_room(tid)

        self._running[tid] = asyncio.create_task(_run())

    async def _execute_task(self, tid, scid, ce):
        idle_loop.notify_task_started()
        row = await db.fetch_one("SELECT user_request FROM tasks WHERE task_id=?", (tid,))
        if not row:
            raise ValueError(f"任务{tid}不存在")
        req = row[0]
        caps = await capability_pool.get_all()
        if not caps:
            raise ValueError("没有可用的AI能力实例，请先配置AI模型")
        cap = await capability_pool.get_by_id(scid) if scid else caps[0]
        from app.agents.scheduler import SchedulerAgent
        sch = SchedulerAgent(cap)
        sch.bind_context(tid, cancellation_event=ce)
        sr = await sch.execute(req, tid)
        plan, team, room = sr["plan"], sr["team"], await meeting_room_manager.get_room(tid)
        tbs = sr.get("task_board_state", {})
        await db.execute("UPDATE tasks SET status=?,config_snapshot=? WHERE task_id=?", (TaskStatus.EXECUTING.value, json.dumps(plan, ensure_ascii=False), tid))
        st: TaskState = {
            "task_id": tid, "user_request": req, "plan": plan, "current_phase": 0,
            "phases": plan.get("phases", [{"phase": "默认", "description": req}]),
            "team": team, "artifacts": {}, "messages": [], "status": TaskStatus.EXECUTING,
            "review_rounds": 0, "max_review_rounds": 5, "last_code": "", "review_feedback": "",
            "review_passed_this_round": False, "pre_check_passed": False, "pre_check_errors": [],
            "error": None, "room": room, "task_board_state": tbs,
        }
        from .machine import WorkflowEngine
        sm = StateManager(tid)
        engine = WorkflowEngine()
        fs = await engine.run(st)
        await sm.save_snapshot(fs)
        await sm.cleanup()
        await db.execute("UPDATE tasks SET status=?,updated_at=CURRENT_TIMESTAMP WHERE task_id=?", (fs["status"].value, tid))

    async def cancel_task(self, tid: str) -> bool:
        if tid in self._cancel_events:
            self._cancel_events[tid].set()
        if tid in self._running:
            self._running[tid].cancel()
            return True
        return False

    async def resume_task(self, tid: str) -> bool:
        sm = StateManager(tid)
        snap = await sm.load_latest_snapshot()
        if not snap:
            return False

        room = await meeting_room_manager.create_room(tid)
        task_board = TaskBoard.from_state_dict(tid, snap.get("task_board_state", {}))
        team = {}
        for role, caps_data in snap.get("team", {}).items():
            team[role] = []
            for cd in caps_data:
                if isinstance(cd, dict):
                    c = await capability_pool.get_by_id(cd.get("id"))
                    if c:
                        team[role].append(c)
                    else:
                        team[role].append(AICapability(**cd))
                else:
                    team[role].append(cd)
        resumed_state: TaskState = {
            "task_id": tid, "user_request": snap.get("user_request", ""), "plan": snap.get("plan", {}),
            "current_phase": snap.get("current_phase", 0), "phases": snap.get("phases", []),
            "team": team, "artifacts": snap.get("artifacts", {}), "messages": snap.get("messages", []),
            "status": TaskStatus(snap.get("status", "executing")), "review_rounds": snap.get("review_rounds", 0),
            "max_review_rounds": snap.get("max_review_rounds", 5), "last_code": snap.get("last_code", ""),
            "review_feedback": snap.get("review_feedback", ""), "review_passed_this_round": snap.get("review_passed_this_round", False),
            "error": snap.get("error"), "room": room, "task_board_state": task_board.get_state_dict(),
        }
        from .machine import WorkflowEngine
        engine = WorkflowEngine()

        cancel_evt = asyncio.Event()
        self._cancel_events[tid] = cancel_evt

        async def _run_resumed(cancel_event):
            try:
                md = config_manager.get("task_defaults.max_task_duration_seconds", 3600)
                final = await asyncio.wait_for(engine.run(resumed_state), timeout=md)
                await sm.save_snapshot(final)
                await sm.cleanup()
                await db.execute("UPDATE tasks SET status=? WHERE task_id=?", (final["status"].value, tid))
            except asyncio.CancelledError:
                logger.info(f"Resumed task {tid} was cancelled")
                await db.execute("UPDATE tasks SET status=? WHERE task_id=?", (TaskStatus.CANCELLED.value, tid))
            except Exception as e:
                logger.exception(f"恢复失败: {e}")
                await db.execute("UPDATE tasks SET status=? WHERE task_id=?", (TaskStatus.FAILED.value, tid))
            finally:
                self._running.pop(tid, None)
                await meeting_room_manager.close_room(tid)

        task = asyncio.create_task(_run_resumed(cancel_evt))
        self._running[tid] = task
        return True

task_manager = TaskManager()
