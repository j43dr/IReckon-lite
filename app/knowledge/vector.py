from loguru import logger
from typing import List, Dict, Any


class VectorStore:
    def __init__(self):
        self.vectors = {}

    async def add(self, key: str, vector: List[float]):
        self.vectors[key] = vector

    async def search(self, query: List[float], top_k: int = 5) -> List[Dict]:
        return []


vector_store = VectorStore()