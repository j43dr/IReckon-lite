#!/usr/bin/env python3
"""
Sleep and Dream Mechanism for 3.0
Implements memory consolidation, cross-domain association, and insight generation.
Includes Cognitive Dream Protocol (Compressor/Expander/Validator).
"""
import json
import asyncio
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from app.core.config import config_manager
from app.core.database import db
from loguru import logger

DREAM_DIR = Path(config_manager.get("system.data_dir", "./data")) / "dreams"
DREAM_DIR.mkdir(parents=True, exist_ok=True)

class SleepDreamMechanism:
    """Manages sleep state, memory collection, and dream generation."""
    
    def __init__(self):
        self._token_budget = config_manager.get("dreams.token_budget", 2000)
        self._idle_timeout_minutes = config_manager.get("dreams.idle_timeout_minutes", 60)
        self._is_dreaming = False
        self._last_activity = datetime.now(timezone.utc)
        self._current_token_balance = config_manager.get("system.token_balance", 100)
        self._rejected_insights_file = DREAM_DIR / "rejected_insights.json"
        self._morning_greeting = ""
    
    async def check_token_sleep_condition(self) -> Dict[str, Any]:
        """
        Check if token balance triggers sleep.
        Sleep when balance <= 5% (configurable), force sleep at <= 3%.
        When force_sleep is True (<=3%), system will NOT respond to user messages.
        """
        token_threshold_percent = config_manager.get("dreams.token_sleep_threshold_percent", 5)
        force_sleep_percent = config_manager.get("dreams.token_force_sleep_percent", 3)
        
        # Get current token balance from config (updated by system usage)
        self._current_token_balance = config_manager.get("system.token_balance", 100)
        total_budget = config_manager.get("system.token_total_budget", 10000)
        percent_remaining = (self._current_token_balance / total_budget) * 100 if total_budget > 0 else 0
        
        if percent_remaining <= force_sleep_percent:
            # Force sleep: do NOT respond to user
            return {"trigger": True, "reason": "critical_low_token", "force_sleep": True, "percent": percent_remaining}
        elif percent_remaining <= token_threshold_percent:
            # Try to sleep but still respond
            return {"trigger": True, "reason": "low_token", "force_sleep": False, "percent": percent_remaining}
        return {"trigger": False}
    
    async def should_respond_to_user(self) -> bool:
        """
        Check if system should respond to user message.
        When force_sleep is True (<=3% token), do NOT respond.
        """
        token_check = await self.check_token_sleep_condition()
        if token_check["trigger"] and token_check.get("force_sleep"):
            return False
        return True
    
    async def should_enter_sleep(self, task_queue_empty: bool) -> bool:
        """Determine if system should enter sleep mode."""
        token_check = await self.check_token_sleep_condition()
        if token_check["trigger"] and token_check["force_sleep"]:
            return True
        
        if not task_queue_empty:
            return False
        now = datetime.now(timezone.utc)
        idle_minutes = (now - self._last_activity).total_seconds() / 60
        return idle_minutes >= self._idle_timeout_minutes
    
    async def collect_daily_memories(self) -> List[Dict]:
        """Collect high-value memories from today's interactions."""
        memories = []
        try:
            today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            rows = await db.fetch_all(
                "SELECT msg_id, sender_role, content, timestamp, metadata FROM conversation_messages WHERE timestamp LIKE ? LIMIT 100",
                (f"{today}%",)
            )
            for row in rows:
                meta = json.loads(row[4]) if row[4] else {}
                memories.append({
                    "type": meta.get("category", "tech"),
                    "content": row[2][:200] if row[2] else "",
                    "timestamp": row[3],
                    "sender": row[1],
                    "tags": meta.get("tags", [])
                })
            logger.info(f"Collected {len(memories)} memories for dream processing")
        except Exception as e:
            logger.error(f"Failed to collect memories: {e}")
        return memories
    
    async def compress_memory(self, memory: Dict) -> str:
        """Compress memory to essential principle (max 50 tokens)."""
        content = memory.get("content", "")
        if len(content) > 50:
            return content[:47] + "..."
        return content
    
    async def generate_dream_association(self, compressed_seeds: List[str], knowledge_context: List[str]) -> List[Dict]:
        """Generate cross-domain associations from compressed seeds (Expander)."""
        associations = []
        for i, seed in enumerate(compressed_seeds):
            if i + 1 < len(knowledge_context):
                ctx1 = knowledge_context[i % len(knowledge_context)]
                ctx2 = knowledge_context[(i + 1) % len(knowledge_context)]
                associations.append({
                    "seed": seed,
                    "context": [ctx1, ctx2],
                    "story": f"Dream Association: {seed} combined with {ctx1} and {ctx2}",
                    "confidence": 0.7
                })
        return associations
    
    async def validate_insight(self, story: str) -> Dict[str, Any]:
        """Validate generated insight through sandbox checks (Micro-constraint AI)."""
        dangerous_patterns = ["exec(", "eval(", "import os", "subprocess"]
        for pattern in dangerous_patterns:
            if pattern in story:
                return {"valid": False, "reason": "safety_violation"}
        
        if "hallucination_marker" in story.lower():
            return {"valid": False, "reason": "potential_hallucination"}
            
        return {"valid": True}
    
    async def enter_dream_state(self) -> Dict[str, Any]:
        """Execute full dream cycle: collect -> compress -> associate -> validate."""
        if self._is_dreaming:
            return {"status": "already_dreaming"}
        
        self._is_dreaming = True
        logger.info("Entering dream state...")
        
        try:
            memories = await self.collect_daily_memories()
            if not memories:
                return {"status": "no_memories", "message": "No memories to process"}
            
            consumed = 0
            memory_budget = int(self._token_budget * 0.30)
            expanded_budget = int(self._token_budget * 0.60)
            
            compressed_seeds = []
            for mem in memories[:min(len(memories), memory_budget // 20)]:
                seed = await self.compress_memory(mem)
                compressed_seeds.append(seed)
                consumed += len(seed)
            
            knowledge_context = ["pattern_recognition", "code_optimization", "user_preference"]
            associations = await self.generate_dream_association(compressed_seeds, knowledge_context)
            consumed += len(str(associations))
            
            if consumed > self._token_budget:
                logger.warning("Dream token budget exceeded, truncating.")
                associations = associations[:max(1, len(associations) // 2)]
            
            validated_insights = []
            rejected_insights = []
            
            insights_file = DREAM_DIR / "insights.json"
            existing_insights = []
            if insights_file.exists():
                with open(insights_file, 'r', encoding='utf-8') as f:
                    existing_insights = json.load(f)
            
            for assoc in associations:
                validation = await self.validate_insight(assoc.get("story", ""))
                assoc["timestamp"] = datetime.now(timezone.utc).isoformat()
                if validation["valid"]:
                    validated_insights.append(assoc)
                else:
                    assoc["rejection_reason"] = validation["reason"]
                    rejected_insights.append(assoc)
            
            with open(insights_file, 'w', encoding='utf-8') as f:
                json.dump(existing_insights + validated_insights, f, indent=2, ensure_ascii=False)
            
            if rejected_insights:
                existing_rejected = []
                if self._rejected_insights_file.exists():
                    with open(self._rejected_insights_file, 'r', encoding='utf-8') as f:
                        existing_rejected = json.load(f)
                with open(self._rejected_insights_file, 'w', encoding='utf-8') as f:
                    json.dump(existing_rejected + rejected_insights, f, indent=2, ensure_ascii=False)
            
            self._morning_greeting = f"Woke up with {len(validated_insights)} new insights from the dreamscape."
            
            return {
                "status": "success",
                "insights_generated": len(validated_insights),
                "insights_rejected": len(rejected_insights),
                "seeds_compressed": len(compressed_seeds)
            }
        finally:
            self._is_dreaming = False
    
    def get_status(self) -> Dict[str, Any]:
        return {
            "is_dreaming": self._is_dreaming,
            "token_budget": self._token_budget,
            "current_token_balance": self._current_token_balance,
            "idle_timeout_minutes": self._idle_timeout_minutes,
            "last_activity": self._last_activity.isoformat(),
            "morning_greeting": self._morning_greeting
        }
    
    async def sleep(self, force: bool = False) -> Dict[str, Any]:
        """Enter sleep mode and trigger dream cycle."""
        self._last_activity = datetime.now(timezone.utc)
        if force or await self.should_enter_sleep(task_queue_empty=True):
            return await self.enter_dream_state()
        return {"status": "not_ready", "message": "Sleep conditions not met"}
    
    async def wake(self) -> str:
        """Wake from sleep/dream state."""
        self._is_dreaming = False
        self._last_activity = datetime.now(timezone.utc)
        greeting = self._morning_greeting or "Good morning, ready to continue."
        logger.info(f"Woken from dream state: {greeting}")
        return greeting

    async def is_user_input_blocked(self) -> bool:
        """Check if user input should be ignored (e.g. sleeping due to critical token balance)."""
        if self._current_token_balance <= 3:
            return True
        return False

# Global singleton
sleep_dream = SleepDreamMechanism()
