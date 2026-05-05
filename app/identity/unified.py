#!/usr/bin/env python3
"""
Cross-Platform Identity Unification for 3.0
Ensures same AI persona across all platforms with unified memory and personality.
"""
import asyncio
import json
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
from dataclasses import dataclass, field
from enum import Enum
from app.core.config import config_manager
from app.core.database import db
from app.knowledge.vector import vector_store
from app.personality.system import personality_system
from loguru import logger


class PlatformType(Enum):
    WEB = "web"
    QQ = "qq"
    VRChat = "vrchat"
    MINECRAFT = "minecraft"
    WECHAT = "wechat"
    DISCORD = "discord"


@dataclass
class PlatformAdapter:
    """Platform-specific adaptation layer."""
    platform_type: PlatformType
    behavior_mapping: Dict[str, Any]  # How personality maps to platform behavior
    style_overrides: Dict[str, Any]  # Platform-specific style adjustments


@dataclass
class RelationshipLevel:
    """User relationship tracking across platforms."""
    user_id: str
    platform: str
    interaction_count: int
    interaction_depth: float  # 0-1, based on conversation quality
    last_interaction: str
    relationship_score: float  # 0-1


class CrossPlatformIdentity:
    """
    Manages unified identity across platforms:
    1. Unified memory library (single vector DB with platform tags)
    2. Personality parameters centrally managed
    3. Cross-platform state synchronization
    4. Platform-specific adaptation layers
    """

    def __init__(self):
        self._data_dir = Path(config_manager.get("system.data_dir", "./data")) / "identity"
        self._data_dir.mkdir(parents=True, exist_ok=True)
        self._platform_adapters: Dict[PlatformType, PlatformAdapter] = {}
        self._relationship_map: Dict[str, List[RelationshipLevel]] = {}  # user_id -> list of platform relationships
        self._mood_state = "neutral"  # From consciousness stream
        self._init_platform_adapters()

    def _init_platform_adapters(self):
        """Initialize platform-specific adapters."""
        # VRChat: behavior -> avatar actions
        self._platform_adapters[PlatformType.VRChat] = PlatformAdapter(
            platform_type=PlatformType.VRChat,
            behavior_mapping={
                "happy": {"expression": "smile", "gait": "bouncy"},
                "confused": {"expression": "tilt_head", "particles": "question_marks"},
                "thinking": {"expression": "scratch_chin", "animation": "thinking_pose"}
            },
            style_overrides={"response_format": "brief", "use_emotes": True}
        )

        # QQ: behavior -> speech style and frequency
        self._platform_adapters[PlatformType.QQ] = PlatformAdapter(
            platform_type=PlatformType.QQ,
            behavior_mapping={
                "happy": {"tone": "cheerful", "frequency": "high"},
                "serious": {"tone": "formal", "frequency": "normal"}
            },
            style_overrides={"response_format": "chat", "group_aware": True}
        )

        # Minecraft: behavior -> game collaboration strategy
        self._platform_adapters[PlatformType.MINECRAFT] = PlatformAdapter(
            platform_type=PlatformType.MINECRAFT,
            behavior_mapping={
                "helpful": {"strategy": "follow_player", "build_assist": True},
                "creative": {"strategy": "suggest_builds", "use_redstone": True}
            },
            style_overrides={"response_format": "game_actions", "coordinate_aware": True}
        )

        # Web: default behavior
        self._platform_adapters[PlatformType.WEB] = PlatformAdapter(
            platform_type=PlatformType.WEB,
            behavior_mapping={},
            style_overrides={}
        )

    async def store_interaction(self, user_id: str, platform: PlatformType, 
                                content: str, metadata: Optional[Dict] = None) -> str:
        """
        Store interaction in unified memory library.
        All platforms write to same vector DB with platform tag.
        """
        interaction_id = f"int-{user_id}-{platform.value}-{datetime.now(timezone.utc).strftime('%H%M%S')}"

        # Store in vector database with platform tag
        await vector_store.add_documents(
            collection="unified_memory",
            ids=[interaction_id],
            documents=[content],
            metadatas=[{
                "user_id": user_id,
                "platform": platform.value,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "type": "interaction",
                **(metadata or {})
            }]
        )

        # Update relationship
        await self._update_relationship(user_id, platform, content)

        logger.info(f"Stored interaction for {user_id} from {platform.value}")
        return interaction_id

    async def _update_relationship(self, user_id: str, platform: PlatformType, content: str):
        """Update relationship level based on interaction."""
        if user_id not in self._relationship_map:
            self._relationship_map[user_id] = []

        # Find existing relationship for this platform
        rel = None
        for r in self._relationship_map[user_id]:
            if r.platform == platform.value:
                rel = r
                break

        if rel is None:
            rel = RelationshipLevel(
                user_id=user_id,
                platform=platform.value,
                interaction_count=0,
                interaction_depth=0.5,
                last_interaction=datetime.now(timezone.utc).isoformat(),
                relationship_score=0.1
            )
            self._relationship_map[user_id].append(rel)

        # Update
        rel.interaction_count += 1
        rel.last_interaction = datetime.now(timezone.utc).isoformat()
        # Simple depth calculation based on content length and complexity
        depth = min(1.0, len(content) / 500.0)
        rel.interaction_depth = (rel.interaction_depth + depth) / 2.0
        rel.relationship_score = min(1.0, rel.relationship_score + 0.01)

    async def retrieve_memory(self, query: str, user_id: Optional[str] = None, 
                              platform_filter: Optional[PlatformType] = None, 
                              n_results: int = 5) -> List[Dict]:
        """
        Retrieve memories from unified memory library.
        Search is global (platform-agnostic) unless filtered.
        """
        where_clause = {}
        if user_id:
            where_clause["user_id"] = user_id
        if platform_filter:
            where_clause["platform"] = platform_filter.value

        results = await vector_store.search(
            collection="unified_memory",
            query=query,
            n_results=n_results
        )

        # Filter by platform if specified
        if platform_filter:
            results = [r for r in results if r.get("metadata", {}).get("platform") == platform_filter.value]

        logger.debug(f"Retrieved {len(results)} memories for query: {query[:50]}...")
        return results

    def get_personality_parameters(self) -> Dict[str, float]:
        """Get centrally managed personality parameters."""
        return personality_system.get_params()

    def update_personality_parameters(self, params: Dict[str, float]) -> bool:
        """Update personality parameters (takes effect across all platforms)."""
        return personality_system.update_params(params)

    def get_current_mood(self) -> str:
        """Get current mood state from consciousness stream."""
        return self._mood_state

    def set_mood(self, mood: str):
        """Update mood state (shared across all platforms)."""
        self._mood_state = mood
        logger.info(f"Mood updated to: {mood}")

    def get_platform_adapter(self, platform: PlatformType) -> Optional[PlatformAdapter]:
        """Get platform-specific adapter."""
        return self._platform_adapters.get(platform, )

    async def handle_platform_switch(self, user_id: str, from_platform: PlatformType, 
                                     to_platform: PlatformType) -> Dict[str, Any]:
        """
        Handle seamless platform switch.
        Returns context to continue conversation naturally.
        """
        # Get recent memories from any platform
        recent_memories = await self.retrieve_memory(
            query="recent conversation",
            user_id=user_id,
            n_results=3
        )

        # Get current mood/state
        mood = self.get_current_mood()

        # Get relationship info
        relationship_score = 0.0
        if user_id in self._relationship_map:
            for rel in self._relationship_map[user_id]:
                if rel.platform == to_platform.value:
                    relationship_score = rel.relationship_score
                    break

        # Get adapter for target platform
        adapter = self.get_platform_adapter(to_platform)

        return {
            "user_id": user_id,
            "from_platform": from_platform.value,
            "to_platform": to_platform.value,
            "recent_context": [m.get("document", "") for m in recent_memories],
            "mood": mood,
            "relationship_score": relationship_score,
            "behavior_mapping": adapter.behavior_mapping if adapter else {},
            "style_overrides": adapter.style_overrides if adapter else {}
        }

    def get_relationship_summary(self, user_id: str) -> Dict[str, Any]:
        """Get relationship summary across all platforms."""
        if user_id not in self._relationship_map:
            return {"user_id": user_id, "platforms": [], "overall_score": 0.0}

        platforms = self._relationship_map[user_id]
        overall_score = sum(p.relationship_score for p in platforms) / len(platforms) if platforms else 0.0

        return {
            "user_id": user_id,
            "platforms": [
                {
                    "platform": p.platform,
                    "interaction_count": p.interaction_count,
                    "relationship_score": p.relationship_score,
                    "last_interaction": p.last_interaction
                }
                for p in platforms
            ],
            "overall_score": overall_score
        }

    def get_status(self) -> Dict[str, Any]:
        """Get cross-platform identity status."""
        total_users = len(self._relationship_map)
        total_interactions = sum(
            sum(p.interaction_count for p in platforms)
            for platforms in self._relationship_map.values()
        )

        return {
            "unified_memory": True,
            "personality_sync": True,
            "mood_state": self._mood_state,
            "total_users": total_users,
            "total_interactions": total_interactions,
            "supported_platforms": [p.value for p in PlatformType]
        }


# Global singleton
cross_platform_identity = CrossPlatformIdentity()



