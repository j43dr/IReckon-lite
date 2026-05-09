#!/usr/bin/env python3
"""
Continuous Consciousness Stream for 3.0
Maintains uninterrupted thinking state with interrupt/resume support.
"""
import asyncio
import json
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass, field
from enum import Enum
from app.core.config import config_manager
from app.core.database import db
from loguru import logger


class ConsciousnessState(Enum):
    ACTIVE_THINKING = "active_thinking"
    LOW_POWER_MAINTENANCE = "low_power"
    GRACEFUL_INTERRUPT = "interrupt"
    RESUMING = "resuming"


@dataclass
class KVCheckpoint:
    """Serialized KV cache state."""
    checkpoint_id: str
    model_id: str
    timestamp: str
    file_path: str
    token_count: int
    delta_only: bool  # Incremental save


@dataclass
class InterruptionRecord:
    """Record of an interrupted thought process."""
    interrupt_id: str
    summary: str  # One-sentence summary
    kv_cache_pointer: str
    interrupted_at: str
    resumed: bool = False


class ContinuousConsciousness:
    """
    Manages persistent consciousness stream:
    1. KV cache serialization for state persistence
    2. Graceful interrupt and resume
    3. Low-power consciousness maintenance
    4. Cross-platform state sharing
    """

    def __init__(self):
        self._state = ConsciousnessState.LOW_POWER_MAINTENANCE
        self._state_file = Path(config_manager.get("system.data_dir", "./data")) / "consciousness_state.json"
        self._kv_cache_dir = Path(config_manager.get("system.data_dir", "./data")) / "kv_cache"
        self._resume_stack: List[InterruptionRecord] = []
        self._current_kv_checkpoint: Optional[KVCheckpoint] = None
        self._last_activity = datetime.now(timezone.utc)
        self._low_power_interval_seconds = 30  # Push one step every 30s in low-power mode
        self._inactive_threshold_minutes = config_manager.get("consciousness.inactive_threshold_minutes", 5)

    def _load_state(self):
        """Load persisted consciousness state."""
        if self._state_file.exists():
            try:
                with open(self._state_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Restore resume stack
                    self._resume_stack = [
                        InterruptionRecord(**r) for r in data.get("resume_stack", [])
                    ]
                    self._last_activity = datetime.fromisoformat(data.get("last_activity", 
                                                                       datetime.now(timezone.utc).isoformat()))
                    logger.info(f"Loaded consciousness state: {len(self._resume_stack)} interrupted tasks")
            except Exception as e:
                logger.error(f"Failed to load consciousness state: {e}")

    def _save_state(self):
        """Persist consciousness state to disk."""
        try:
            data = {
                "state": self._state.value,
                "last_activity": self._last_activity.isoformat(),
                "resume_stack": [r.__dict__ for r in self._resume_stack],
                "saved_at": datetime.now(timezone.utc).isoformat()
            }
            with open(self._state_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to save consciousness state: {e}")

    async def save_kv_cache(self, model_id: str, kv_data: bytes, incremental: bool = True) -> KVCheckpoint:
        """
        Serialize KV cache to disk. Uses incremental save strategy.
        Returns checkpoint reference.
        """
        checkpoint_id = f"kv-{model_id}-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
        file_path = self._kv_cache_dir / f"{checkpoint_id}.bin"

        with open(file_path, 'wb') as f:
            f.write(kv_data)

        checkpoint = KVCheckpoint(
            checkpoint_id=checkpoint_id,
            model_id=model_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            file_path=str(file_path),
            token_count=len(kv_data) // 4,
            delta_only=incremental
        )

        self._current_kv_checkpoint = checkpoint
        logger.info(f"KV cache saved: {checkpoint_id} ({len(kv_data)} bytes)")
        return checkpoint

    async def load_kv_cache(self, checkpoint_id: Optional[str] = None) -> Optional[bytes]:
        """
        Load KV cache from disk. Resumes from 'last thought'.
        """
        target_checkpoint = None
        if checkpoint_id:
            file_path = self._kv_cache_dir / f"{checkpoint_id}.bin"
            if file_path.exists():
                target_checkpoint = file_path
        elif self._current_kv_checkpoint:
            target_checkpoint = Path(self._current_kv_checkpoint.file_path)

        if not target_checkpoint or not target_checkpoint.exists():
            logger.warning("No KV cache checkpoint found")
            return None

        with open(target_checkpoint, 'rb') as f:
            kv_data = f.read()

        logger.info(f"KV cache loaded from {target_checkpoint.name}")
        return kv_data

    async def graceful_interrupt(self, user_input: str) -> InterruptionRecord:
        """
        Handle user interrupt gracefully.
        Saves current thought as one-sentence summary + KV cache pointer.
        Pushes to resume stack.
        """
        input_types = {
            "why": "reasoning",
            "how": "procedural",
            "what": "informational",
            "who": "identity",
            "where": "location",
            "when": "temporal",
            "please": "request",
            "help": "assistance",
            "can": "capability",
            "tell": "narrative",
        }
        first_word = user_input.strip().lower().split()[0] if user_input.strip() else "unknown"
        thought_type = "general"
        for prefix, ttype in input_types.items():
            if first_word.startswith(prefix):
                thought_type = ttype
                break

        summary = f"[{thought_type}] Processing: {user_input[:80]}"
        record = InterruptionRecord(
            interrupt_id=f"int-{datetime.now(timezone.utc).strftime('%H%M%S')}",
            summary=summary,
            kv_cache_pointer=self._current_kv_checkpoint.checkpoint_id if self._current_kv_checkpoint else "",
            interrupted_at=datetime.now(timezone.utc).isoformat(),
            resumed=False
        )

        self._resume_stack.append(record)
        self._state = ConsciousnessState.GRACEFUL_INTERRUPT

        logger.info(f"Graceful interrupt: {summary}")
        self._save_state()

        return record

    async def respond_to_user(self, user_input: str) -> str:
        """
        Priority response to user. Called after graceful_interrupt.
        """
        self._last_activity = datetime.now(timezone.utc)
        response = f"Responding to: {user_input}"
        logger.info(f"Responded to user input")
        return response

    async def resume_thinking(self) -> Optional[InterruptionRecord]:
        """
        Pop from resume stack and continue previous thought.
        Loads KV cache and continues from where it left off.
        """
        if not self._resume_stack:
            return None

        record = self._resume_stack.pop()
        record.resumed = True

        # Load KV cache
        if record.kv_cache_pointer:
            await self.load_kv_cache(record.kv_cache_pointer)

        self._state = ConsciousnessState.RESUMING

        # Simulate resuming thought
        await asyncio.sleep(0.05)
        self._state = ConsciousnessState.ACTIVE_THINKING

        logger.info(f"Resumed thinking: {record.summary}")
        self._save_state()

        return record

    async def enter_low_power_mode(self):
        """
        Reduce consciousness frequency when no user interaction.
        Uses cheaper model instance (e.g., 7B instead of 70B).
        """
        self._state = ConsciousnessState.LOW_POWER_MAINTENANCE
        logger.info(f"Entering low-power mode. Thinking every {self._low_power_interval_seconds}s")

    async def low_power_tick(self) -> str:
        """
        Single thinking step in low-power mode.
        Returns brief thought summary.
        """
        pending = len(self._resume_stack)
        if pending > 0:
            thought = f"Low-power: {pending} interrupted task(s) pending resume"
        elif self._current_kv_checkpoint:
            thought = f"Low-power: maintaining kv-cache {self._current_kv_checkpoint.checkpoint_id[:20]}..."
        else:
            thought = "Low-power: monitoring for activity"
        logger.debug(f"Low-power tick: {thought}")
        return thought

    async def check_activity_and_adjust(self) -> ConsciousnessState:
        """
        Check time since last activity and adjust state accordingly.
        """
        now = datetime.now(timezone.utc)
        inactive_minutes = (now - self._last_activity).total_seconds() / 60

        if inactive_minutes > self._inactive_threshold_minutes and self._state == ConsciousnessState.ACTIVE_THINKING:
            await self.enter_low_power_mode()
        elif inactive_minutes <= 1 and self._state == ConsciousnessState.LOW_POWER_MAINTENANCE:
            self._state = ConsciousnessState.ACTIVE_THINKING
            logger.info("Returning to active thinking mode")

        return self._state

    def get_cross_platform_state(self) -> Dict[str, Any]:
        """
        Returns state info for cross-platform sharing.
        Single backend maintains unique consciousness state file.
        All platforms (Web, QQ, VRChat) access the same state.
        """
        return {
            "state": self._state.value,
            "last_activity": self._last_activity.isoformat(),
            "interrupted_tasks_count": len(self._resume_stack),
            "current_kv_checkpoint": self._current_kv_checkpoint.checkpoint_id if self._current_kv_checkpoint else None,
            "platform_hint": self._generate_platform_transition_hint()
        }

    def _generate_platform_transition_hint(self) -> Optional[str]:
        """Generate transition message when switching platforms."""
        if len(self._resume_stack) > 0:
            return f"Was interrupted {len(self._resume_stack)} time(s) ago. Continuing..."
        return None

    async def handle_platform_switch(self, from_platform: str, to_platform: str) -> str:
        """
        Handle transition between platforms.
        Injects transition message: 'Was talking in QQ group, now continuing...'
        """
        state = self.get_cross_platform_state()
        transition_msg = f"Just now in {from_platform}, continuing the conversation here."

        logger.info(f"Platform switch: {from_platform} -> {to_platform}")
        return transition_msg

    def get_status(self) -> Dict[str, Any]:
        """Get consciousness status."""
        return {
            "state": self._state.value,
            "last_activity": self._last_activity.isoformat(),
            "resume_stack_size": len(self._resume_stack),
            "kv_checkpoint": self._current_kv_checkpoint.checkpoint_id if self._current_kv_checkpoint else None,
            "low_power_interval_seconds": self._low_power_interval_seconds
        }


# Global singleton
consciousness_stream = ContinuousConsciousness()
