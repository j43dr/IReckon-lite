#!/usr/bin/env python3
"""Dynamic Vision Perception System for 3.0 - Unified Vision System.
Implements async frame processing, privacy mode, micro-model inference, and large model wake-up.
"""
import asyncio
import json
import time
from pathlib import Path
from typing import List, Dict, Optional, Any
from collections import deque
from datetime import datetime, timezone
from enum import Enum
from app.core.config import config_manager
from app.core.database import db
from loguru import logger


class VisionState(Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    PROCESSING = "processing"


class VisionEvent:
    def __init__(self, frame_id: str, payload: Dict):
        self.frame_id = frame_id
        self.payload = payload


class RingBuffer:
    def __init__(self, capacity: int = 300):  # 1 minute at 5fps
        self._buffer = deque(maxlen=capacity)
    
    def push(self, item):
        self._buffer.append(item)
    
    def get_recent(self, n: int = 10) -> List:
        return list(self._buffer)[-n:]
    
    def clear(self):
        self._buffer.clear()
    
    def size(self) -> int:
        return len(self._buffer)


class VisionSystem:
    """
    Unified vision system with:
    1. Async streaming frame processing
    2. Subconscious micro-model layer (always-on)
    3. Large model wake-up on important events
    4. Privacy mode with one-click pause
    """
    def __init__(self):
        self._queue = asyncio.Queue()
        self._ring_buffer = RingBuffer(capacity=config_manager.get("vision.buffer_size", 300))
        self._running = False
        self._privacy_mode = False
        self._state = VisionState.ACTIVE
        self._confidence_threshold = config_manager.get("vision.confidence_threshold", 0.6)
        self._wake_up_frames = config_manager.get("vision.wake_up_frames", 5)
        self._low_confidence_streak = 0
        self._frame_rate = config_manager.get("vision.frame_rate", 5)
        self._important_targets: List[str] = config_manager.get("vision.important_targets", [])
        self._annotation_enabled = config_manager.get("vision.annotation_enabled", True)
        self._micro_model_latency_ms = 8.0
        self._data_dir = Path(config_manager.get("system.data_dir", "./data")) / "vision"
        self._data_dir.mkdir(parents=True, exist_ok=True)
    
    async def start(self):
        self._running = True
        self._state = VisionState.ACTIVE
        logger.info(f"Vision system started at {self._frame_rate} fps (Micro-model layer active)")
        asyncio.create_task(self._subconscious_loop())
    
    async def stop(self):
        self._running = False
        self._state = VisionState.PAUSED
        logger.info("Vision system stopped")

    async def toggle_privacy(self, enabled: bool):
        """Toggle privacy mode. Clears buffer immediately."""
        self._privacy_mode = enabled
        self._state = VisionState.PAUSED if enabled else VisionState.ACTIVE
        if enabled:
            self._ring_buffer.clear()
            logger.warning("Privacy mode ON: Vision buffer cleared")
        else:
            logger.info("Privacy mode OFF")

    async def process_frame(self, frame_data: bytes, source: str = "camera") -> Dict:
        """Process a single frame with micro-model."""
        if self._privacy_mode:
            logger.debug("Privacy mode ON - dropping frame")
            return {"objects": [], "motion": "unknown", "anomaly": "PRIVACY_MODE", "confidence": 0.0}
        
        frame_id = f"frame-{datetime.now(timezone.utc).strftime('%H%M%S%f')}"
        frame = {"frame_id": frame_id, "source": source, "size_bytes": len(frame_data)}
        
        # Run micro-model inference (simulated)
        detection = await self._run_micro_model(frame_data, frame_id)
        
        # Push to ring buffer
        self._ring_buffer.push({"frame_id": frame_id, "analysis": detection})
        
        # Check if large model should be woken up
        if await self._check_wakeup_conditions(detection):
            await self._trigger_large_model_analysis(detection)
        
        return detection

    def _analyze_micro(self, frame: Dict) -> Dict:
        """Run micro-model feature extraction on frame data."""
        objects = frame.get("objects", [])
        has_important = any(o.get("important", False) for o in objects)
        max_conf = max([o.get("confidence", 0) for o in objects], default=1.0)
        return {
            "objects": objects,
            "motion": frame.get("motion", "static"),
            "has_important": has_important,
            "max_confidence": max_conf,
            "anomaly": max_conf < self._confidence_threshold
        }

    async def _run_micro_model(self, frame_data: bytes, frame_id: str) -> Dict:
        """Run micro vision model inference on frame bytes."""
        await asyncio.sleep(self._micro_model_latency_ms / 1000.0)

        objects = []
        motion = "static"
        data_len = len(frame_data)

        if data_len > 100:
            byte_sum = sum(frame_data[:min(1024, data_len)])
            entropy_estimate = len(set(frame_data[:1024])) / min(1024, data_len) if data_len > 0 else 0

            if entropy_estimate > 0.6 and data_len > 500:
                objects.append({"type": "person", "confidence": round(0.7 + entropy_estimate * 0.25, 2),
                                "bbox": [100, 100, 200, 200]})
                motion = "moving"
            elif entropy_estimate > 0.4:
                objects.append({"type": "object", "confidence": round(0.5 + entropy_estimate * 0.3, 2),
                                "bbox": [50, 50, 150, 150]})
                motion = "static"

        anomaly = None
        confidence = max([o.get("confidence", 0) for o in objects], default=0.0)
        if not objects and data_len > 100:
            anomaly = "UNKNOWN_CONTENT"
        elif data_len > 10000:
            anomaly = "LARGE_FRAME"

        return {
            "frame_id": frame_id,
            "objects": objects,
            "motion": motion,
            "anomaly": anomaly,
            "confidence": confidence,
            "inference_time_ms": self._micro_model_latency_ms
        }

    async def _check_wakeup_conditions(self, detection: Dict) -> bool:
        """Check if large model should be woken up."""
        wakeup = False
        
        for obj in detection.get("objects", []):
            if obj.get("type") in self._important_targets:
                logger.info(f"Important target detected: {obj.get('type')} - waking up large model")
                wakeup = True
                break
        
        if detection.get("confidence", 1.0) < 0.5 and detection.get("objects"):
            logger.info("Unknown object detected - waking up large model")
            wakeup = True
        
        return wakeup

    async def _wake_up_strategy(self, analysis: Dict) -> bool:
        """Determine if large model needs to be woken up."""
        if analysis.get("has_important"):
            self._low_confidence_streak = 0
            return True
        
        if analysis.get("anomaly"):
            self._low_confidence_streak += 1
            if self._low_confidence_streak >= self._wake_up_frames:
                logger.info(f"Wake up triggered: {self._low_confidence_streak} frames of low confidence")
                self._low_confidence_streak = 0
                return True
        else:
            self._low_confidence_streak = 0
        return False

    async def _subconscious_loop(self):
        while self._running:
            try:
                frame = await asyncio.wait_for(self._queue.get(), timeout=1.0)
                if self._privacy_mode:
                    continue
                
                analysis = self._analyze_micro(frame.payload)
                self._ring_buffer.push({"frame_id": frame.frame_id, "analysis": analysis})
                
                if await self._wake_up_strategy(analysis):
                    await self._trigger_large_model_analysis(analysis)
                    
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Vision loop error: {e}")

    async def _trigger_large_model_analysis(self, trigger_data: Dict):
        """Send key frames to large model for deep analysis."""
        key_frames = self._ring_buffer.get_recent(self._wake_up_frames)
        context = {
            "trigger": trigger_data,
            "recent_frames": key_frames,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        logger.info(f"Triggering deep analysis for {len(key_frames)} frames")
        return context

    async def push_frame(self, frame: Dict) -> None:
        if self._privacy_mode:
            return
        await self._queue.put(VisionEvent(frame.get("frame_id", "unknown"), frame))

    async def enable_privacy_mode(self) -> None:
        await self.toggle_privacy(True)
    
    async def disable_privacy_mode(self, user_confirmation: bool = False) -> bool:
        if not user_confirmation:
            return False
        await self.toggle_privacy(False)
        return True

    async def get_annotated_stream(self) -> Optional[bytes]:
        if self._privacy_mode:
            return None
        recent = self._ring_buffer.get_recent(5)
        annotation = {
            "frame_count": len(recent),
            "state": self._state.value,
            "recent_objects": [
                {"frame_id": r["frame_id"], "objects": r["analysis"].get("objects", []),
                 "motion": r["analysis"].get("motion", "unknown")}
                for r in recent if "analysis" in r
            ],
            "important_targets": self._important_targets,
            "generated_at": datetime.now(timezone.utc).isoformat()
        }
        return json.dumps(annotation, ensure_ascii=False).encode("utf-8")
    
    def register_important_target(self, target_type: str) -> None:
        if target_type not in self._important_targets:
            self._important_targets.append(target_type)
            logger.info(f"Registered important target: {target_type}")

    async def get_current_state(self) -> Dict[str, Any]:
        return {
            "state": self._state.value,
            "privacy_mode": self._privacy_mode,
            "buffer_size": self._ring_buffer.size(),
            "objects": self._ring_buffer.get_recent(1)[0].get("analysis", {}).get("objects", []) if self._ring_buffer.size() > 0 else [],
            "motion": self._ring_buffer.get_recent(1)[0].get("analysis", {}).get("motion", "unknown") if self._ring_buffer.size() > 0 else "unknown",
            "is_game": False,
            "game_id": None
        }

    def get_status(self) -> Dict[str, Any]:
        return {
            "state": self._state.value,
            "privacy_mode": self._privacy_mode,
            "frame_rate": self._frame_rate,
            "buffer_size": self._ring_buffer.size(),
            "micro_model_latency_ms": self._micro_model_latency_ms,
            "important_targets": self._important_targets,
            "annotation_enabled": self._annotation_enabled
        }

# Global singleton
vision_system = VisionSystem()
