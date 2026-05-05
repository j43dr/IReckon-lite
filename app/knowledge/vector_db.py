from loguru import logger
from typing import List, Dict, Any


class VectorDB:
    def __init__(self):
        self.collections = {}

    async def create_collection(self, name: str):
        self.collections[name] = []

    async def insert(self, collection: str, data: Dict):
        if collection not in self.collections:
            await self.create_collection(collection)
        self.collections[collection].append(data)

    async def query(self, collection: str, filter: Dict = None) -> List[Dict]:
        return self.collections.get(collection, [])


vector_db = VectorDB()