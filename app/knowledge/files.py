import json
import os
import re
import uuid
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
import aiofiles
from app.core.database import db
from app.core.logger import logger
from app.core.config import config_manager
from .vector import vector_store


class FileKnowledgeBase:
    def __init__(self):
        data_dir = Path(config_manager.get("system.data_dir", "./data"))
        self.base_dir = data_dir / "knowledge_base"
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self._index_file = self.base_dir / "index.json"
        self._index: Dict[str, Dict] = {}
        self._load_index()

    def _load_index(self):
        if self._index_file.exists():
            try:
                with open(self._index_file, "r", encoding="utf-8") as f:
                    self._index = json.load(f)
            except Exception:
                self._index = {}

    def _save_index(self):
        try:
            with open(self._index_file, "w", encoding="utf-8") as f:
                json.dump(self._index, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存索引失败: {e}")

    async def add_entry(
        self,
        entry_type: str,
        title: str,
        content: str,
        source: str = "",
        tags: Optional[List[str]] = None,
    ):
        entry_id = uuid.uuid4().hex
        type_dir = self.base_dir / entry_type
        type_dir.mkdir(parents=True, exist_ok=True)
        path = type_dir / f"{entry_id}.txt"
        async with aiofiles.open(path, "w", encoding="utf-8") as f:
            await f.write(content)
        self._index[entry_id] = {
            "id": entry_id,
            "type": entry_type,
            "title": title,
            "source": source,
            "tags": tags or [],
            "path": str(path),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "content_length": len(content),
        }
        self._save_index()
        await vector_store.add_documents(
            collection="knowledge_base",
            ids=[entry_id],
            documents=[content],
            metadatas=[{
                "type": entry_type,
                "title": title,
                "source": source,
                "tags": json.dumps(tags or []),
            }],
        )
        logger.info(f"已添加知识条目: {title} ({entry_type})")

    async def search(self, query: str, n_results: int = 10) -> List[Dict]:
        results = await vector_store.search_collection(
            "knowledge_base", query=query, n_results=n_results, score_threshold=0.05
        )
        enriched = []
        for r in results:
            doc_id = r.get("id", "")
            idx_entry = self._index.get(doc_id, {})
            enriched.append({
                "id": doc_id,
                "title": idx_entry.get("title", ""),
                "type": idx_entry.get("type", ""),
                "source": idx_entry.get("source", ""),
                "tags": idx_entry.get("tags", []),
                "content": r.get("document", ""),
                "created_at": idx_entry.get("created_at", ""),
                "score": r.get("score", 0),
            })
        enriched.sort(key=lambda x: x["score"], reverse=True)
        return enriched

    async def get_entry(self, entry_id: str) -> Optional[Dict]:
        idx_entry = self._index.get(entry_id)
        if not idx_entry:
            return None
        path = Path(idx_entry["path"])
        if not path.exists():
            return None
        async with aiofiles.open(path, "r", encoding="utf-8") as f:
            content = await f.read()
        return {**idx_entry, "content": content}

    async def delete_entry(self, entry_id: str) -> bool:
        idx_entry = self._index.pop(entry_id, None)
        if not idx_entry:
            return False
        path = Path(idx_entry["path"])
        if path.exists():
            os.unlink(path)
        self._save_index()
        return True

    def get_stats(self) -> Dict[str, Any]:
        counts: Dict[str, int] = {}
        for entry in self._index.values():
            et = entry.get("type", "unknown")
            counts[et] = counts.get(et, 0) + 1
        return {
            "total_entries": len(self._index),
            "by_type": counts,
        }


file_kb = FileKnowledgeBase()
