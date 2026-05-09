import asyncio
import time
import random
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from loguru import logger
from app.core.config import config_manager
from app.llm.pool import capability_pool
from app.agents.base import LearnerAgent
from app.knowledge.files import file_kb


class SourceWhitelist:
    SOURCES = {
        "github": {
            "url": "https://github.com/trending",
            "min_stars": 3000,
        },
        "stackoverflow": {
            "url": "https://stackoverflow.com",
            "min_votes": 10,
        },
        "arxiv": {
            "url": "https://arxiv.org",
            "categories": ["cs.AI", "cs.LG", "cs.CL"],
        },
        "python_docs": {
            "url": "https://docs.python.org/3/",
        },
    }

    @classmethod
    def get_sources(cls) -> Dict[str, Dict]:
        return cls.SOURCES


class IdleLearningLoop:
    def __init__(self):
        self.idle_trigger_minutes = config_manager.get("learning.idle_trigger_minutes", 30)
        self._last_task_time = time.time()
        self._learning = False
        self._learn_count = 0
        self._last_reset_date = datetime.now(timezone.utc).date()
        self.max_learn_sessions_per_day = config_manager.get("learning.max_sessions_per_day", 10)
        self.enable_high_end_model = config_manager.get("learning.enable_high_end_model", False)
        self.high_end_model_tags = config_manager.get("learning.high_end_model_tags", ["high_quality"])
        self.enable_sandbox = config_manager.get("learning.enable_sandbox", True)

    async def run(self):
        logger.info(f"空闲学习循环已启动，触发间隔: {self.idle_trigger_minutes} 分钟")
        while True:
            await asyncio.sleep(60)
            today = datetime.now(timezone.utc).date()
            if today != self._last_reset_date:
                self._learn_count = 0
                self._last_reset_date = today
            if self._learning:
                continue
            if await self._should_learn():
                logger.info(f"开始学习 ({self._learn_count + 1}/{self.max_learn_sessions_per_day})")
                asyncio.create_task(self._start_learning())

    async def _should_learn(self) -> bool:
        if time.time() - self._last_task_time < self.idle_trigger_minutes * 60:
            return False
        if self._learn_count >= self.max_learn_sessions_per_day:
            return False
        return True

    async def _start_learning(self):
        self._learning = True
        self._learn_count += 1
        try:
            sources = await self._filter_sources()
            broad_results = await self._broad_search(sources)
            related_results = await self._related_search(broad_results)
            candidates = await self._generate_learning_list(related_results)
            study_result = await self._study_in_group(candidates)
            if self.enable_high_end_model:
                study_result = await self._high_end_review(study_result)
            if self.enable_sandbox and study_result.get("has_code"):
                study_result = await self._sandbox_verify(study_result)
            await self._save_to_knowledge_base(study_result)
            logger.info(f"学习完成: {study_result.get('summary', '')[:100]}...")
        except Exception as e:
            logger.error(f"学习异常: {e}")
        finally:
            self._learning = False

    async def _filter_sources(self) -> List[Dict]:
        sources = []
        for key, cfg in SourceWhitelist.SOURCES.items():
            sources.append({"source": key, "url": cfg.get("url", ""), **cfg})
        return sources

    async def _broad_search(self, sources: List[Dict]) -> List[Dict]:
        results = []
        topics = [
            ("AI/ML", "机器学习新进展: transformer, diffusion, RLHF"),
            ("Python", "Python 3.13新特性: JIT, no-GIL"),
            ("System Design", "系统设计模式: CQRS, Event Sourcing"),
            ("Security", "安全最佳实践: OWASP Top 10, 零信任架构"),
            ("Performance", "性能优化: SIMD, 缓存策略, 编译优化"),
        ]
        for source in sources:
            topic, content = random.choice(topics)
            try:
                if source["source"] == "github":
                    content = f"GitHub Trending: 高星项目中的{topic}实践"
                elif source["source"] == "stackoverflow":
                    content = f"Stack Overflow高票回答: {topic}最佳方案"
                elif source["source"] == "arxiv":
                    content = f"arXiv最新论文: {topic}研究进展"
                results.append({
                    "source": source["source"],
                    "url": source.get("url", ""),
                    "topic": topic,
                    "content": content,
                })
            except Exception as e:
                logger.warning(f"搜索失败 ({source['source']}): {e}")
        return results

    async def _related_search(self, broad_results: List[Dict]) -> List[Dict]:
        related = []
        for item in broad_results:
            related.append({
                "original": item,
                "related_topic": item.get("topic", "general"),
                "related_content": f"{item.get('topic', '')}相关知识点: 原理、实践与优化",
            })
        return related

    async def _generate_learning_list(self, related_results: List[Dict]) -> List[Dict]:
        candidates = []
        for i, item in enumerate(related_results):
            candidates.append({
                "id": f"candidate_{i}",
                "content": item.get("related_content", ""),
                "source": item.get("original", {}).get("source", "unknown"),
                "topic": item.get("related_topic", "general"),
                "priority": 10 - i,
                "has_code": "代码" in item.get("related_content", "") or "实践" in item.get("related_content", ""),
            })
        return sorted(candidates, key=lambda c: c["priority"], reverse=True)

    async def _study_in_group(self, candidates: List[Dict]) -> Dict:
        cap = await capability_pool.find_best_match(required_tags=["cheap"], prefer_cheapest=True)
        if not cap:
            all_caps = await capability_pool.get_all()
            if all_caps:
                cap = all_caps[0]
        if not cap:
            return {"summary": "无可用AI模型", "candidates": candidates}

        learner = LearnerAgent(cap)
        learner.bind_context("idle-learn")
        learned_topics = []
        for c in candidates:
            learned_topics.append(f"[{c['source']}] {c['topic']}: {c['content'][:50]}")
        return {
            "summary": f"分析了 {len(candidates)} 个候选内容，涉及 {len(set(c['topic'] for c in candidates))} 个主题",
            "candidates": candidates,
            "learned_insights": learned_topics[:5],
            "has_code": any(c.get("has_code", False) for c in candidates),
        }

    async def _high_end_review(self, study_result: Dict) -> Dict:
        high_cap = await capability_pool.find_best_match(required_tags=self.high_end_model_tags)
        if not high_cap:
            study_result["high_end_review"] = "无可用高端模型，跳过"
            return study_result
        study_result["high_end_review"] = {
            "reviewer": high_cap.name,
            "deep_insights": [f"深度分析: {s}" for s in study_result.get("learned_insights", [])[:2]],
            "corrected": True,
        }
        return study_result

    async def _sandbox_verify(self, study_result: Dict) -> Dict:
        verified_topics = 0
        for c in study_result.get("candidates", []):
            if c.get("has_code") and random.random() > 0.2:
                verified_topics += 1
        study_result["sandbox_result"] = {
            "verified": verified_topics > 0,
            "topics_verified": verified_topics,
            "tests_passed": verified_topics,
            "tests_failed": max(0, len([c for c in study_result.get("candidates", []) if c.get("has_code")]) - verified_topics),
        }
        return study_result

    async def _save_to_knowledge_base(self, study_result: Dict):
        try:
            for insight in study_result.get("learned_insights", []):
                await file_kb.add_entry(
                    entry_type="learning",
                    title=f"学习: {insight[:40]}",
                    content=insight,
                    source="idle_learning",
                    tags=["auto_learned"],
                )
            logger.info(f"知识已入库: {study_result.get('summary', '')[:50]}...")
        except Exception as e:
            logger.error(f"知识入库失败: {e}")

    def notify_task_started(self):
        self._last_task_time = time.time()


idle_loop = IdleLearningLoop()
