from typing import Dict, Any, Optional, TypedDict, List
from enum import Enum


class TaskStatus(Enum):
    PENDING = "pending"
    PLANNING = "planning"
    EXECUTING = "executing"
    REVIEWING = "reviewing"
    REVISING = "revising"
    DELIVERING = "delivering"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"
    CANCELLED = "cancelled"


class TaskState(TypedDict):
    task_id: str
    user_request: str
    plan: Dict[str, Any]
    current_phase: int
    phases: List[Dict[str, Any]]
    team: Dict[str, List[Any]]
    artifacts: Dict[str, str]
    messages: List[Dict]
    status: TaskStatus
    review_rounds: int
    max_review_rounds: int
    last_code: str
    review_feedback: str
    review_passed_this_round: bool
    pre_check_passed: bool
    pre_check_errors: List[str]
    error: Optional[str]
    room: Optional[Any]
    task_board_state: Dict[str, Any]