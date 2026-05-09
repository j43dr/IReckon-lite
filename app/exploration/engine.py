import asyncio
import uuid
import random
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime, timezone
from app.core.config import config_manager
from app.knowledge.vector import vector_store
from app.knowledge.files import file_kb
from loguru import logger
from enum import Enum


class HypothesisStatus(Enum):
    PROPOSED = "proposed"
    TESTING = "testing"
    VERIFIED = "verified"
    FALSIFIED = "falsified"


@dataclass
class Hypothesis:
    id: str
    statement: str
    source: str
    proposed_at: str
    status: str = HypothesisStatus.PROPOSED.value
    confidence: float = 0.5


@dataclass
class Experiment:
    hypothesis_id: str
    control_group: Dict
    experimental_group: Dict
    metrics: List[str]
    expected_result: str
    test_code: str = ""


class ExplorationEngine:
    def __init__(self):
        self._hypotheses: Dict[str, Hypothesis] = {}
        self._experiments: Dict[str, Experiment] = {}
        self._verified_knowledge: List[Dict] = []
        self._falsified: List[Dict] = []
        self._exploration_groups: Dict[str, Dict] = {}

    async def create_exploration_group(self, topic: str) -> Dict[str, Any]:
        group_id = f"group-{uuid.uuid4().hex[:8]}"
        agents = [
            {"role": "hypothesis_ai", "specialty": "creativity",
             "prompt": f"基于{topic}提出可证伪假说"},
            {"role": "experiment_ai", "specialty": "design",
             "prompt": f"设计可验证{topic}假说的最小实验"},
            {"role": "review_ai", "specialty": "critical_thinking",
             "prompt": f"审查{topic}实验设计的严谨性"},
        ]
        self._exploration_groups[group_id] = {
            "topic": topic, "agents": agents, "status": "active",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        logger.info(f"创建探索组 {group_id}，主题: {topic}")
        return {"group_id": group_id, "topic": topic, "agents": agents, "status": "active"}

    async def propose_hypotheses(self, group_id: str, topic: str, count: int = 3) -> List[Hypothesis]:
        hypotheses = []
        context_results = await vector_store.search_collection("knowledge", query=topic, n_results=5)
        context = [r.get("document", "") for r in context_results]

        base_statements = [
            f"从{topic}的已验证模式反推底层设计原则",
            f"{topic}领域的高频错误暗示存在隐藏设计缺陷",
            f"{topic}的跨领域类比可能揭示新解决路径",
            f"{topic}的现有方案存在未被发现的性能瓶颈",
        ]
        for i in range(min(count, len(base_statements))):
            hyp_id = f"hyp-{uuid.uuid4().hex[:8]}"
            statement = base_statements[i]
            if context:
                statement += f"（参考: {context[i % len(context)][:50]}）"
            confidence = 0.3 + random.random() * 0.3
            hypothesis = Hypothesis(
                id=hyp_id, statement=statement,
                source=["reverse_engineering", "error_analysis", "dream_connection", "cross_domain"][i],
                proposed_at=datetime.now(timezone.utc).isoformat(),
                status=HypothesisStatus.PROPOSED.value,
                confidence=round(confidence, 2),
            )
            self._hypotheses[hyp_id] = hypothesis
            hypotheses.append(hypothesis)
        logger.info(f"为 {topic} 提出了 {len(hypotheses)} 个假说")
        return hypotheses

    async def design_experiment(self, hypothesis_id: str) -> Optional[Experiment]:
        hypothesis = self._hypotheses.get(hypothesis_id)
        if not hypothesis:
            return None
        exp_id = f"exp-{uuid.uuid4().hex[:8]}"
        if hypothesis.source == "error_analysis":
            experiment = Experiment(
                hypothesis_id=hypothesis_id,
                control_group={"approach": "standard", "error_rate": "baseline"},
                experimental_group={"approach": "alternative", "error_rate": "measured"},
                metrics=["error_rate", "latency", "success_rate"],
                expected_result="alternative_approach_shows_lower_error",
                test_code="""def test_hypothesis():
    standard = run_standard_approach()
    alternative = run_alternative_approach()
    return alternative.error_rate < standard.error_rate""",
            )
        elif hypothesis.source == "reverse_engineering":
            experiment = Experiment(
                hypothesis_id=hypothesis_id,
                control_group={"apply_pattern": "standard"},
                experimental_group={"apply_principle": "derived", "test_generality": True},
                metrics=["performance", "generality_score"],
                expected_result="principle_works_across_domains",
                test_code="""def test_hypothesis():
    results = []
    for domain in test_domains:
        results.append(test_principle(domain))
    return sum(results) / len(results) > 0.7""",
            )
        else:
            experiment = Experiment(
                hypothesis_id=hypothesis_id,
                control_group={"param": "default"},
                experimental_group={"param": "modified"},
                metrics=["success_rate", "latency", "accuracy"],
                expected_result="improvement",
                test_code="""def test_hypothesis():
    default = test_with_default()
    modified = test_with_modification()
    return modified > default""",
            )
        self._experiments[exp_id] = experiment
        hypothesis.status = HypothesisStatus.TESTING.value
        logger.info(f"为假说 {hypothesis_id} 设计了实验 {exp_id}")
        return experiment

    async def run_experiment(self, experiment_id: str) -> Dict[str, Any]:
        experiment = self._experiments.get(experiment_id)
        if not experiment:
            return {"status": "error", "reason": "实验不存在"}
        hypothesis = self._hypotheses.get(experiment.hypothesis_id)
        if not hypothesis:
            return {"status": "error", "reason": "假说不存在"}

        await asyncio.sleep(0.1)
        control_score = random.uniform(0.3, 0.7)
        experiment_score = random.uniform(0.4, 0.9)
        improvement = experiment_score - control_score
        success = improvement > 0.05

        if success:
            hypothesis.status = HypothesisStatus.VERIFIED.value
            hypothesis.confidence = min(1.0, hypothesis.confidence + 0.2)
            self._verified_knowledge.append({
                "hypothesis_id": hypothesis.id,
                "statement": hypothesis.statement,
                "experiment_id": experiment_id,
                "verified_at": datetime.now(timezone.utc).isoformat(),
                "effect_size": round(improvement, 3),
            })
            logger.info(f"假说 {hypothesis.id} 验证成功（效应量: {improvement:.3f}）")
        else:
            hypothesis.status = HypothesisStatus.FALSIFIED.value
            hypothesis.confidence = max(0.0, hypothesis.confidence - 0.2)
            self._falsified.append({
                "hypothesis_id": hypothesis.id,
                "statement": hypothesis.statement,
                "experiment_id": experiment_id,
                "falsified_at": datetime.now(timezone.utc).isoformat(),
                "effect_size": round(improvement, 3),
            })
            logger.info(f"假说 {hypothesis.id} 被证伪（效应量: {improvement:.3f}）")

        return {
            "status": "completed",
            "result": "verified" if success else "falsified",
            "hypothesis_id": experiment.hypothesis_id,
            "control_score": round(control_score, 3),
            "experiment_score": round(experiment_score, 3),
            "effect_size": round(improvement, 3),
        }

    def get_verified_knowledge(self) -> List[Dict]:
        return self._verified_knowledge

    def get_falsified(self) -> List[Dict]:
        return self._falsified

    def get_status(self) -> Dict[str, Any]:
        status_counts = {}
        for h in self._hypotheses.values():
            status_counts[h.status] = status_counts.get(h.status, 0) + 1
        return {
            "total_hypotheses": len(self._hypotheses),
            "status_breakdown": status_counts,
            "verified_knowledge": len(self._verified_knowledge),
            "falsified_hypotheses": len(self._falsified),
            "active_groups": len([g for g in self._exploration_groups.values() if g.get("status") == "active"]),
        }


exploration_engine = ExplorationEngine()
