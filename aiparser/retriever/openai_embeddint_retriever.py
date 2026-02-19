from __future__ import annotations

import math
import threading
from typing import List, Optional, Tuple

from openai import OpenAI

from .base import Retriever
from ..models import Concept, RetrievedConcept


def _cosine(vec1: List[float], vec2: List[float]) -> float:
    dot = 0.0
    nvec1 = 0.0
    nvec2 = 0.0

    for i in range(len(vec1)):
        vec1_i = float(vec1[i])
        vec2_i = float(vec2[i])
        dot += vec1_i * vec2_i
        nvec1 += vec1_i * vec1_i
        nvec2 += vec2_i * vec2_i
    
    denom = math.sqrt(nvec1) * math.sqrt(nvec2)
    return dot / denom if denom > 0 else 0.0


class OpenAIEmbeddingRetriever(Retriever):

    def __init__(
        self,
        *,
        api_key: str,
        base_url: str = "https://api.openai.com/v1",
        embedding_model: str = "text-embedding-3-small",
        batch_size: int = 128,
    ) -> None:
        self._client = OpenAI(api_key = api_key, base_url = base_url)
        self._embedding_model = embedding_model
        self._batch_size = max(1, int(batch_size))

        self._concepts: List[Concept] = []
        self._vectors: List[List[float]] = []
        self._indexed = False

        self._lock = threading.Lock()

    def index(self, concepts: List[Concept]) -> None:
        with self._lock:
            if self._indexed: # TODO - support re-indexing with new concepts
                return
            
            self._concepts = concepts
            texts = [c.concept for c in concepts]

            vectors: List[List[float]] = []
            for start in range(0, len(texts), self._batch_size):
                batch = texts[start : start + self._batch_size]
                response = self._client.embeddings.create(
                    input = batch,
                    model = self._embedding_model,
                )
                for item in response.data:
                    vectors.append(list(item.embedding))

            if len(vectors) != len(concepts):
                raise RuntimeError(
                    f"Expected {len(concepts)} embeddings but got {len(vectors)}"
                )
            
            self._vectors = vectors
            self._indexed = True

    def retrieve(self, input_text: str, *, top_k: int = 10) -> List[RetrievedConcept]:
        if not self._indexed or not self._concepts or not self._vectors:
            return []
        
        top_k = max(1, top_k)

        query = self._client.embeddings.create(
            model = self._embedding_model,
            input = input_text,
        ).data[0].embedding
        query_vec = list(query)

        scored: List[Tuple[float, int]] = []
        for i, concept_vec in enumerate(self._vectors):
            score = _cosine(query_vec, concept_vec)
            if score > 0:
                scored.append((score, i))

        scored.sort(reverse = True, key = lambda x: x[0])
        top = scored[: top_k]

        return [
            RetrievedConcept(
                concept = self._concepts[i], score = float(score)
            )
            for score, i in top
        ]