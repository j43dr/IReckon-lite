import json
from pathlib import Path
from typing import List, Dict, Any, Optional
import aiofiles
from app.core.database import db
from app.core.logger import logger
from app.core.config import config_manager


class FileKnowledgeBase:
    def __init__(self):
        data_dir = Path(config_manager.get("system.data_dir", "./data"))
        self.base_dir = data_dir / "knowledge_base"
        self.base_dir.mkdir(parents=True, exist_ok=True)

    async def add_entry(self, entry_type: str, title: str, content: str, source: str = "", tags: Optional[List[str]] = None):
        import uuid
        entry_id = uuid.uuid4().hex
        path = self.base_dir / entry_type / f"{entry_id}.txt"
        path.parent.mkdir(parents=True, exist_ok=True)
        
        async with aiofiles.open(path, "w", encoding="utf-8") as f:
            await f.write(content)
        
        logger.info(f"Added knowledge entry: {title}")

    async def search(self, query: str) -> List[Dict]:
        return []


file_kb = FileKnowledgeBase()