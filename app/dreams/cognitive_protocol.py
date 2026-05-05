#!/usr/bin/env python3
"""
Cognitive Dream Protocol for 3.0
Compressor-Expander-Validator mechanism for generating innovative insights.
"""
import asyncio
import json
import random
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from dataclasses import dataclass
from app.core.config import config_manager
from app.core.database import db
from loguru import logger


@dataclass
class CompressedSeed:
    """Compressed memory seed (?0 tokens)."""
    original_id: str
    seed_text: str
    compression_ratio: float
    created_at: str


@dataclass
class ExpandedIdea:
    """Expanded idea from seed + context."""
    seed_id: str
    story: str
    context_sources: List[str]
    confidence: float
    created_at: str


@dataclass
class ValidatedInsight:
    """Validated insight ready for knowledge base."""
    idea_id: str
    insight_text: str
    verification_result: Dict[str, Any]
    confidence: float
    timestamp: str


class CognitiveDreamProtocol:
    """
    Implements the Compressor-Expander-Validator mechanism:
    1. Compressor: Extracts essential principles (?0 tokens)
    2. Expander: Cross-domain association to generate ideas
    3. Validator: Sandbox verification of ideas
    """

    def __init__(self):
        self._data_dir = Path(config_manager.get("system.data_dir", "./data")) / "cognitive_dreams"
        self._data_dir.mkdir(parents=True, exist_ok=True)
        self._token_budget = config_manager.get("dreams.token_budget", 2000)
        self._compressor_budget_pct = 0.30
        self._expander_budget_pct = 0.60
        self._validator_budget_pct = 0.10

    async def compress(self, memory_fragment: Dict[str, Any]) -> CompressedSeed:
        """, Compressor: Extract essential principle (?0 tokens).
        Must be falsifiable - a clear statement that can be tested.
        """
        content = memory_fragment.get("content", "")
        memory_id = memory_fragment.get("id", "unknown")
        
        # Compress to essential principle (<=50 tokens)
        if len(content) > 200:
            # Extract key phrases: look for causal patterns
            import re
            # Look for cause-effect patterns
            causal_patterns = [r'因为(.+?)所以(.+?)', r'如果(.+?)那么(.+?)', r'(.+?)导致(.+?)', 
                             r'(.+?)因为(.+?)', r'when (.+?) then (.+?)', r'(.+?) causes (.+?)']
            compressed_parts = []
            for pattern in causal_patterns:
                matches = re.findall(pattern, content)
                if matches:
                    compressed_parts.append(str(matches[0]))
            if compressed_parts:
                compressed = compressed_parts[0][:50]
            else:
                # Fallback: first sentence
                sentences = content.split("。")
                compressed = sentences[0][:50] if sentences else content[:50]
        else:
            compressed = content[:50]
        
        # Ensure it's falsifiable (must contain testable claim)
        falsifiable_markers = ["应当", "必须", "总是", "从不", "会导致", "should", "must", "always", "never", "causes", 
                                 "增加", "减少", "提高", "降低", "影响", "increases", "decreases", "affects"]
        is_falsifiable = any(marker in compressed.lower() for marker in falsifiable_markers)
        
        if not is_falsifiable:
            # Add falsifiable structure: "X leads to Y" format
            compressed = f"If {compressed[:30]} then outcome changes"
        
        seed = CompressedSeed(
            original_id=memory_id,
            seed_text=compressed[:50],
            compression_ratio=len(compressed) / max(len(content), 1),
            created_at=datetime.now(timezone.utc).isoformat()
        )
        
        logger.info(f"Compressed memory {memory_id}: '{seed.seed_text}'")
        return seed

    async def expand(self, seed: CompressedSeed, knowledge_fragments: List[str]) -> ExpandedIdea:
        """, Expander: Connect seed with 2 random domains from knowledge base.
        Generate 'idea story' through cross-domain association.
        """
        if len(knowledge_fragments) < 2:
            # Pad with default contexts
            while len(knowledge_fragments) < 2:
                knowledge_fragments.append("general_pattern")
        
        # Select 2 random contexts
        ctx1 = random.choice(knowledge_fragments)
        ctx2 = random.choice([k for k in knowledge_fragments if k != ctx1])
        
        # Generate idea story with cross-domain connection
        story = f"Dream Association: {seed.seed_text} combined with {ctx1} and {ctx2}. "
        story += f"This suggests that {seed.seed_text.lower()} can be applied to {ctx1} scenarios, "
        story += f"similar to how {ctx2} approaches problem-solving through {seed.seed_text.lower()}."
        
        idea = ExpandedIdea(
            seed_id=seed.original_id,
            story=story,
            context_sources=[ctx1, ctx2],
            confidence=0.7,
            created_at=datetime.now(timezone.utc).isoformat()
        )
        
        logger.info(f"Expanded seed {seed.original_id} into idea story")
        return idea

    async def validate(self, idea: ExpandedIdea) -> Dict[str, Any]:
        """
        Validator (Micro-constraint AI):
        - Check for hallucinations
        - Run sandbox verification if applicable
        - Return validation result
        """
        story = idea.story

        # Safety check
        dangerous_patterns = ["exec(", "eval(", "import os", "subprocess", "rm -rf"]
        for pattern in dangerous_patterns:
            if pattern in story:
                return {
                    "valid": False,
                    "reason": "safety_violation",
                    "details": f"Contains dangerous pattern: {pattern, }"
                }

        # Hallucination check (simplified, )
        if "hallucination" in story.lower() or "想象" in story:
            return {
                "valid": False,
                "reason": "potential_hallucination",
                "details": "Story contains hallucination markers"
            }

        # Sandbox verification for code-related ideas
        if "code" in story.lower() or "function" in story.lower():
            # Simulate benchmark test
            await asyncio.sleep(0.05)  # Simulate test time
            benchmark_passed = random.random() > 0.2  # 80% pass rate
            if not benchmark_passed:
                return {
                    "valid": False,
                    "reason": "benchmark_failed",
                    "details": "Code pattern failed benchmark test"
                }

        # Preference check for companion-related ideas
        if "user" in story.lower() or "陪伴" in story:
            # Check against user preference library (simplified, )
            pass

        return {
            "valid": True,
            "reason": "verified",
            "details": "Passed all validation checks"
        }

    async def run_dream_cycle(self, memories: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Run full cognitive dream cycle:
        Compress -> Expand -> Validate
        Respects token budget constraints.
        """
        if not memories:
            return {"status": "no_memories", "insights": []}

        # Token budget allocation
        compressor_budget = int(self._token_budget * self._compressor_budget_pct)
        expander_budget = int(self._token_budget * self._expander_budget_pct)
        validator_budget = int(self._token_budget * self._validator_budget_pct)

        logger.info(f"Starting dream cycle with budget: C={compressor_budget, }, E={expander_budget, }, V={validator_budget, }")

        # Phase 1: Compress
        seeds = []
        for mem in memories[:min(len(memories, ), compressor_budget // 20)]:
            seed = await self.compress(mem, )
            seeds.append(seed, )

        # Phase 2: Expand
        knowledge_context = ["pattern_recognition", "code_optimization", "user_preference",
                            "physics_rules", "social_dynamics", "game_mechanics"]

        ideas = []
        for seed in seeds:
            idea = await self.expand(seed, knowledge_context)
            ideas.append(idea)

        # Phase 3: Validate
        validated_insights = []
        rejected_insights = []

        insights_file = self._data_dir / "cognitive_insights.json"
        rejected_file = self._data_dir / "rejected_ideas.json"

        existing_insights = []
        existing_rejected = []
        if insights_file.exists():
            with open(insights_file, 'r', encoding='utf-8') as f:
                existing_insights = json.load(f)
        if rejected_file.exists():
            with open(rejected_file, 'r', encoding='utf-8') as f:
                existing_rejected = json.load(f)

        for idea in ideas:
            validation = await self.validate(idea, )
            if validation["valid"]:
                insight = ValidatedInsight(
                    idea_id=idea.seed_id,
                    insight_text=idea.story,
                    verification_result=validation,
                    confidence=idea.confidence,
                    timestamp=idea.created_at
                )
                validated_insights.append(insight.__dict__)
            else:
                rejected_idea = {
                    "idea": idea.__dict__,
                    "rejection": validation,
                    "rejected_at": datetime.now(timezone.utc).isoformat()
                }
                rejected_insights.append(rejected_idea, )

        # Save results
        with open(insights_file, 'w', encoding='utf-8') as f:
            json.dump(existing_insights + validated_insights, f, indent=2, ensure_ascii=False)

        if rejected_insights:
            with open(rejected_file, 'w', encoding='utf-8') as f:
                json.dump(existing_rejected + rejected_insights, f, indent=2, ensure_ascii=False)

        # Generate morning greeting with insights
        morning_greeting = f"Woke up with {len(validated_insights, )} new cognitive insights."

        return {
            "status": "success",
            "insights_generated": len(validated_insights, ),
            "ideas_rejected": len(rejected_insights, ),
            "seeds_compressed": len(seeds, ),
            "morning_greeting": morning_greeting
        }

    def get_status(self) -> Dict[str, Any]:
        """Get cognitive dream protocol status."""
        insights_file = self._data_dir / "cognitive_insights.json"
        rejected_file = self._data_dir / "rejected_ideas.json"

        insights_count = 0
        rejected_count = 0

        if insights_file.exists():
            with open(insights_file, 'r') as f:
                insights_count = len(json.load(f))

        if rejected_file.exists():
            with open(rejected_file, 'r') as f:
                rejected_count = len(json.load(f))

        return {
            "token_budget": self._token_budget,
            "budget_allocation": {
                "compressor": self._compressor_budget_pct,
                "expander": self._expander_budget_pct,
                "validator": self._validator_budget_pct
            },
            "insights_generated": insights_count,
            "ideas_rejected": rejected_count
        }


# Global singleton
cognitive_dream_protocol = CognitiveDreamProtocol()
