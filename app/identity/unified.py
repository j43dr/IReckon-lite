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
    platform_type: PlatformType
    behavior_mapping: Dict[str, Any]
    style_overrides: Dict[str, Any]


@dataclass
class RelationshipLevel:
    user_id: str
    platform: str
    interaction_count: int
    interaction_depth: float
    last_interaction: str
    relationship_score: float


class CrossPlatformIdentity:
    def __init__(self):
        self._data_dir = Path(config_manager.get("system.data_dir", "./data")) / "identity"
        self._data_dir.mkdir(parents=True, exist_ok=True)
        self._platform_adapters: Dict[PlatformType, PlatformAdapter] = {}
        self._relationship_map: Dict[str, List[RelationshipLevel]] = {}
        self._mood_state = "neutral"
        self._interaction_log: List[Dict] = []
        self._load_persisted_state()
        self._init_platform_adapters()

    def _load_persisted_state(self):
        state_file = self._data_dir / "identity_state.json"
        if state_file.exists():
            try:
                data = json.loads(state_file.read_text(encoding="utf-8"))
                self._mood_state = data.get("mood_state", "neutral")
                self._relationship_map = {
                    uid: [RelationshipLevel(**r) for r in rels]
                    for uid, rels in data.get("relationships", {}).items()
                }
            except Exception as e:
                logger.error(f"加载身份状态失败: {e}")

    def _save_persisted_state(self):
        state_file = self._data_dir / "identity_state.json"
        try:
            state_file.write_text(json.dumps({
                "mood_state": self._mood_state,
                "relationships": {
                    uid: [r.__dict__ for r in rels]
                    for uid, rels in self._relationship_map.items()
                },
                "saved_at": datetime.now(timezone.utc).isoformat(),
            }, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception as e:
            logger.error(f"保存身份状态失败: {e}")

    def _init_platform_adapters(self):
        self._platform_adapters[PlatformType.VRChat] = PlatformAdapter(
            platform_type=PlatformType.VRChat,
            behavior_mapping={
                "happy": {"expression": "smile", "gait": "bouncy"},
                "confused": {"expression": "tilt_head", "particles": "question_marks"},
                "thinking": {"expression": "scratch_chin", "animation": "thinking_pose"},
            },
            style_overrides={"response_format": "brief", "use_emotes": True},
        )
        self._platform_adapters[PlatformType.QQ] = PlatformAdapter(
            platform_type=PlatformType.QQ,
            behavior_mapping={
                "happy": {"tone": "cheerful", "frequency": "high"},
                "serious": {"tone": "formal", "frequency": "normal"},
            },
            style_overrides={"response_format": "chat", "group_aware": True},
        )
        self._platform_adapters[PlatformType.MINECRAFT] = PlatformAdapter(
            platform_type=PlatformType.MINECRAFT,
            behavior_mapping={
                "helpful": {"strategy": "follow_player", "build_assist": True},
                "creative": {"strategy": "suggest_builds", "use_redstone": True},
            },
            style_overrides={"response_format": "game_actions", "coordinate_aware": True},
        )
        self._platform_adapters[PlatformType.WEB] = PlatformAdapter(
            platform_type=PlatformType.WEB,
            behavior_mapping={},
            style_overrides={},
        )

    async def store_interaction(self, user_id: str, platform: PlatformType, content: str, metadata: Optional[Dict] = None) -> str:
        interaction_id = f"int-{user_id}-{platform.value}-{datetime.now(timezone.utc).strftime('%H%M%S')}"
        await vector_store.add_documents(
            collection="unified_memory",
            ids=[interaction_id],
            documents=[content],
            metadatas=[{
                "user_id": user_id,
                "platform": platform.value,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "type": "interaction",
                **(metadata or {}),
            }],
        )
        self._interaction_log.append({
            "id": interaction_id,
            "user_id": user_id,
            "platform": platform.value,
            "content": content[:100],
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        if len(self._interaction_log) > 1000:
            self._interaction_log = self._interaction_log[-1000:]
        await self._update_relationship(user_id, platform, content)
        self._save_persisted_state()
        return interaction_id

    async def _update_relationship(self, user_id: str, platform: PlatformType, content: str):
        if user_id not in self._relationship_map:
            self._relationship_map[user_id] = []
        rel = next((r for r in self._relationship_map[user_id] if r.platform == platform.value), None)
        if rel is None:
            rel = RelationshipLevel(
                user_id=user_id, platform=platform.value,
                interaction_count=0, interaction_depth=0.5,
                last_interaction=datetime.now(timezone.utc).isoformat(),
                relationship_score=0.1,
            )
            self._relationship_map[user_id].append(rel)
        rel.interaction_count += 1
        rel.last_interaction = datetime.now(timezone.utc).isoformat()
        depth = min(1.0, len(content) / 500.0)
        rel.interaction_depth = round((rel.interaction_depth + depth) / 2.0, 3)
        rel.relationship_score = round(min(1.0, rel.relationship_score + 0.01), 3)

    async def retrieve_memory(self, query: str, user_id: Optional[str] = None, platform_filter: Optional[PlatformType] = None, n_results: int = 5) -> List[Dict]:
        results = await vector_store.search_collection(
            collection="unified_memory",
            query=query,
            n_results=n_results * 2,
        )
        if user_id:
            results = [r for r in results if r.get("metadata", {}).get("user_id") == user_id]
        if platform_filter:
            results = [r for r in results if r.get("metadata", {}).get("platform") == platform_filter.value]
        return results[:n_results]

    async def search_conversations(self, user_id: str, keyword: str, n_results: int = 5) -> List[Dict]:
        return await self.retrieve_memory(query=keyword, user_id=user_id, n_results=n_results)

    def get_personality_parameters(self) -> Dict[str, float]:
        return personality_system.get_params()

    def update_personality_parameters(self, params: Dict[str, float]) -> bool:
        return personality_system.update_params(params)

    def get_current_mood(self) -> str:
        return self._mood_state

    def set_mood(self, mood: str):
        self._mood_state = mood
        self._save_persisted_state()

    def get_platform_adapter(self, platform: PlatformType) -> Optional[PlatformAdapter]:
        return self._platform_adapters.get(platform)

    async def handle_platform_switch(self, user_id: str, from_platform: PlatformType, to_platform: PlatformType) -> Dict[str, Any]:
        recent_memories = await self.retrieve_memory(query="recent conversation", user_id=user_id, n_results=3)
        mood = self.get_current_mood()
        relationship_score = 0.0
        if user_id in self._relationship_map:
            for rel in self._relationship_map[user_id]:
                if rel.platform == to_platform.value:
                    relationship_score = rel.relationship_score
                    break
        adapter = self.get_platform_adapter(to_platform)
        return {
            "user_id": user_id,
            "from_platform": from_platform.value,
            "to_platform": to_platform.value,
            "recent_context": [m.get("document", "") for m in recent_memories],
            "mood": mood,
            "relationship_score": relationship_score,
            "behavior_mapping": adapter.behavior_mapping if adapter else {},
            "style_overrides": adapter.style_overrides if adapter else {},
        }

    def get_relationship_summary(self, user_id: str) -> Dict[str, Any]:
        if user_id not in self._relationship_map:
            return {"user_id": user_id, "platforms": [], "overall_score": 0.0}
        platforms = self._relationship_map[user_id]
        overall = sum(p.relationship_score for p in platforms) / len(platforms) if platforms else 0.0
        return {
            "user_id": user_id,
            "platforms": [{"platform": p.platform, "interaction_count": p.interaction_count, "relationship_score": p.relationship_score, "last_interaction": p.last_interaction} for p in platforms],
            "overall_score": round(overall, 3),
        }

    def get_status(self) -> Dict[str, Any]:
        total_users = len(self._relationship_map)
        total_interactions = sum(p.interaction_count for platforms in self._relationship_map.values() for p in platforms)
        return {
            "unified_memory": True,
            "personality_sync": True,
            "mood_state": self._mood_state,
            "total_users": total_users,
            "total_interactions": total_interactions,
            "supported_platforms": [p.value for p in PlatformType],
            "memory_size": len(self._interaction_log),
        }


cross_platform_identity = CrossPlatformIdentity()
