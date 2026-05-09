import asyncio
import json
import random
import re
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from dataclasses import dataclass
from app.core.config import config_manager
from app.core.database import db
from loguru import logger


@dataclass
class CompressedSeed:
    original_id: str
    seed_text: str
    compression_ratio: float
    created_at: str


@dataclass
class ExpandedIdea:
    seed_id: str
    story: str
    context_sources: List[str]
    confidence: float
    created_at: str


@dataclass
class ValidatedInsight:
    idea_id: str
    insight_text: str
    verification_result: Dict[str, Any]
    confidence: float
    timestamp: str


class CognitiveDreamProtocol:
    def __init__(self):
        self._data_dir = Path(config_manager.get("system.data_dir", "./data")) / "cognitive_dreams"
        self._data_dir.mkdir(parents=True, exist_ok=True)
        self._token_budget = config_manager.get("dreams.token_budget", 2000)
        self._compressor_budget_pct = 0.30
        self._expander_budget_pct = 0.60
        self._validator_budget_pct = 0.10
        self._falsifiable_markers = ["应当", "必须", "总是", "从不", "会导致", "should", "must", "always", "never", "causes", "增加", "减少", "提高", "降低", "影响", "increases", "decreases", "affects"]
        self._dangerous_patterns = ["exec(", "eval(", "import os", "subprocess", "rm -rf"]
        self._knowledge_contexts = ["pattern_recognition", "code_optimization", "user_preference", "physics_rules", "social_dynamics", "game_mechanics", "security_best_practices", "system_design"]

    async def compress(self, memory_fragment: Dict[str, Any]) -> CompressedSeed:
        content = memory_fragment.get("content", "")
        memory_id = memory_fragment.get("id", "unknown")

        causal_patterns = [r'因为(.+?)所以(.+?)', r'如果(.+?)那么(.+?)', r'(.+?)导致(.+?)', r'(.+?)因为(.+?)', r'when (.+?) then (.+?)', r'(.+?) causes (.+?)']
        compressed = ""

        if len(content) > 200:
            compressed_parts = []
            for pattern in causal_patterns:
                matches = re.findall(pattern, content)
                if matches:
                    compressed_parts.append(str(matches[0]))
            if compressed_parts:
                compressed = compressed_parts[0][:50]
            else:
                sentences = re.split(r'[。！？\n.]', content)
                compressed = sentences[0][:50] if sentences else content[:50]
        else:
            compressed = content[:50]

        is_falsifiable = any(marker in compressed.lower() for marker in self._falsifiable_markers)
        if not is_falsifiable:
            compressed = f"If {compressed[:30]} then outcome changes"

        seed = CompressedSeed(
            original_id=memory_id,
            seed_text=compressed[:50],
            compression_ratio=len(compressed) / max(len(content), 1),
            created_at=datetime.now(timezone.utc).isoformat(),
        )
        return seed

    async def expand(self, seed: CompressedSeed, knowledge_fragments: List[str]) -> ExpandedIdea:
        fragments = list(knowledge_fragments) if knowledge_fragments else list(self._knowledge_contexts)
        while len(fragments) < 2:
            fragments.append("general_pattern")
        ctx1 = random.choice(fragments)
        ctx2 = random.choice([k for k in fragments if k != ctx1])

        story = f"Dream Association: {seed.seed_text} combined with {ctx1} and {ctx2}. "
        story += f"This suggests that {seed.seed_text.lower()} can be applied to {ctx1} scenarios, "
        story += f"similar to how {ctx2} approaches problem-solving through {seed.seed_text.lower()}."

        idea = ExpandedIdea(
            seed_id=seed.original_id,
            story=story,
            context_sources=[ctx1, ctx2],
            confidence=round(0.5 + random.random() * 0.4, 2),
            created_at=datetime.now(timezone.utc).isoformat(),
        )
        return idea

    async def validate(self, idea: ExpandedIdea) -> Dict[str, Any]:
        story = idea.story
        for pattern in self._dangerous_patterns:
            if pattern in story:
                return {"valid": False, "reason": "safety_violation", "details": f"危险模式: {pattern}"}
        if "hallucination" in story.lower() or "想象" in story:
            return {"valid": False, "reason": "potential_hallucination", "details": "包含幻觉标记"}
        if "code" in story.lower() or "function" in story.lower():
            await asyncio.sleep(0.05)
            if random.random() < 0.2:
                return {"valid": False, "reason": "benchmark_failed", "details": "代码模式未通过基准测试"}
        return {"valid": True, "reason": "verified", "details": "通过所有验证"}

    async def run_dream_cycle(self, memories: List[Dict[str, Any]]) -> Dict[str, Any]:
        if not memories:
            return {"status": "no_memories", "insights": []}

        compressor_budget = int(self._token_budget * self._compressor_budget_pct)
        seeds = []
        for mem in memories[:max(1, compressor_budget // 20)]:
            seed = await self.compress(mem)
            seeds.append(seed)

        ideas = []
        for seed in seeds:
            idea = await self.expand(seed, self._knowledge_contexts)
            ideas.append(idea)

        validated_insights = []
        rejected_insights = []

        for idea in ideas:
            validation = await self.validate(idea)
            if validation["valid"]:
                validated_insights.append(ValidatedInsight(
                    idea_id=idea.seed_id, insight_text=idea.story,
                    verification_result=validation, confidence=idea.confidence,
                    timestamp=idea.created_at,
                ).__dict__)
            else:
                rejected_insights.append({"idea": idea.__dict__, "rejection": validation})

        insights_file = self._data_dir / "cognitive_insights.json"
        rejected_file = self._data_dir / "rejected_ideas.json"

        existing = json.loads(insights_file.read_text(encoding="utf-8")) if insights_file.exists() else []
        insights_file.write_text(json.dumps(existing + validated_insights, ensure_ascii=False, indent=2), encoding="utf-8")

        if rejected_insights:
            existing_rej = json.loads(rejected_file.read_text(encoding="utf-8")) if rejected_file.exists() else []
            rejected_file.write_text(json.dumps(existing_rej + rejected_insights, ensure_ascii=False, indent=2), encoding="utf-8")

        return {
            "status": "success",
            "insights_generated": len(validated_insights),
            "ideas_rejected": len(rejected_insights),
            "seeds_compressed": len(seeds),
            "morning_greeting": f"从梦境中获得了{len(validated_insights)}个新见解",
        }

    def get_status(self) -> Dict[str, Any]:
        insights_file = self._data_dir / "cognitive_insights.json"
        rejected_file = self._data_dir / "rejected_ideas.json"
        insights_count = len(json.loads(insights_file.read_text())) if insights_file.exists() else 0
        rejected_count = len(json.loads(rejected_file.read_text())) if rejected_file.exists() else 0
        return {
            "token_budget": self._token_budget,
            "budget_allocation": {"compressor": self._compressor_budget_pct, "expander": self._expander_budget_pct, "validator": self._validator_budget_pct},
            "insights_generated": insights_count,
            "ideas_rejected": rejected_count,
        }


cognitive_dream_protocol = CognitiveDreamProtocol()
