from loguru import logger
from typing import List, Dict, Any, Optional
import math
import re
from collections import Counter
from .vector import vector_store


class VectorDB:
    def __init__(self):
        self.collections: Dict[str, List[Dict]] = {}

    async def create_collection(self, name: str):
        self.collections[name] = []

    async def insert(self, collection: str, data: Dict):
        if collection not in self.collections:
            await self.create_collection(collection)
        self.collections[collection].append(data)

    async def query(
        self,
        collection: str,
        filter: Optional[Dict] = None,
        limit: int = 50,
    ) -> List[Dict]:
        docs = self.collections.get(collection, [])
        if filter:
            results = []
            for d in docs:
                match = True
                for key, value in filter.items():
                    if key not in d or d[key] != value:
                        match = False
                        break
                if match:
                    results.append(d)
            return results[:limit]
        return docs[:limit]

    async def hybrid_search(
        self,
        collection: str,
        query: str,
        filter: Optional[Dict] = None,
        limit: int = 10,
    ) -> List[Dict]:
        base = await self.query(collection, filter, limit=100)
        if not query or not base:
            return base[:limit]
        results = await vector_store.search_collection(
            "hybrid_" + collection if collection not in vector_store.collections else collection,
            query=query,
            n_results=limit,
        )
        return results if results else base[:limit]


vector_db = VectorDB()
