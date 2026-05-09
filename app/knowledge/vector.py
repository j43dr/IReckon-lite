from loguru import logger
from typing import List, Dict, Any, Optional
import math
import re
from collections import Counter


def _tokenize(text: str) -> List[str]:
    return re.findall(r'\w+', text.lower())


def _compute_tf(text: str) -> Dict[str, float]:
    tokens = _tokenize(text)
    if not tokens:
        return {}
    counts = Counter(tokens)
    max_count = max(counts.values())
    return {word: count / max_count for word, count in counts.items()}


def _compute_idf(documents: List[str]) -> Dict[str, float]:
    n = len(documents)
    if n == 0:
        return {}
    doc_freq: Dict[str, int] = {}
    for doc in documents:
        words = set(_tokenize(doc))
        for word in words:
            doc_freq[word] = doc_freq.get(word, 0) + 1
    return {word: math.log((n + 1) / (freq + 1)) + 1 for word, freq in doc_freq.items()}


def _cosine_similarity(vec1: Dict[str, float], vec2: Dict[str, float]) -> float:
    all_keys = set(vec1) | set(vec2)
    dot = sum(vec1.get(k, 0) * vec2.get(k, 0) for k in all_keys)
    norm1 = math.sqrt(sum(v * v for v in vec1.values()))
    norm2 = math.sqrt(sum(v * v for v in vec2.values()))
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return dot / (norm1 * norm2)


class VectorStore:
    def __init__(self):
        self.vectors: Dict[str, List[float]] = {}
        self.collections: Dict[str, list] = {}
        self._tfidf_vectors: Dict[str, Dict[str, float]] = {}

    async def add(self, key: str, vector: List[float]):
        self.vectors[key] = vector

    async def search(self, query: List[float], top_k: int = 5) -> List[Dict]:
        if not query or not self.vectors:
            return []
        scored = []
        for key, vec in self.vectors.items():
            if len(query) != len(vec):
                continue
            sim = sum(q * v for q, v in zip(query, vec))
            q_norm = math.sqrt(sum(q * q for q in query))
            v_norm = math.sqrt(sum(v * v for v in vec))
            if q_norm > 0 and v_norm > 0:
                sim /= (q_norm * v_norm)
            scored.append((sim, key))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [{"key": k, "score": s} for s, k in scored[:top_k]]

    async def add_documents(
        self,
        collection: str,
        ids: List[str],
        documents: List[str],
        metadatas: Optional[List[Dict]] = None,
    ):
        if collection not in self.collections:
            self.collections[collection] = []
        for i, doc_id in enumerate(ids):
            doc = documents[i] if i < len(documents) else ""
            meta = metadatas[i] if metadatas and i < len(metadatas) else {}
            self.collections[collection].append({
                "id": doc_id,
                "document": doc,
                "metadata": meta,
            })
            self._tfidf_vectors[doc_id] = _compute_tf(doc)
        logger.info(f"Added {len(ids)} documents to collection '{collection}'")

    async def search_collection(
        self,
        collection: str,
        query: str = "",
        n_results: int = 5,
        score_threshold: float = 0.0,
    ) -> List[Dict]:
        docs = self.collections.get(collection, [])
        if not docs:
            return []
        if not query:
            return docs[:n_results]
        query_tf = _compute_tf(query)
        all_docs = [d["document"] for d in docs]
        idf = _compute_idf(all_docs)
        query_tfidf = {}
        for word, tf in query_tf.items():
            query_tfidf[word] = tf * idf.get(word, 1.0)
        scored = []
        for d in docs:
            doc_tf = self._tfidf_vectors.get(d["id"], {})
            doc_tfidf = {}
            for word, tf in doc_tf.items():
                doc_tfidf[word] = tf * idf.get(word, 1.0)
            sim = _cosine_similarity(query_tfidf, doc_tfidf)
            if sim >= score_threshold:
                scored.append((sim, d))
        scored.sort(key=lambda x: x[0], reverse=True)
        results = []
        for score, doc in scored[:n_results]:
            results.append({**doc, "score": round(score, 4)})
        return results

    def get_collection_size(self, collection: str) -> int:
        return len(self.collections.get(collection, []))

    def delete_collection(self, collection: str):
        removed = self.collections.pop(collection, [])
        for doc in removed:
            self._tfidf_vectors.pop(doc["id"], None)


vector_store = VectorStore()
