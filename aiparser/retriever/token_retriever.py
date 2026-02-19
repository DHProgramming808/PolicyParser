from __future__ import annotations

import re
from typing import List, Tuple

from .base import Retriever
from ..models import Concept, RetrievedConcept


_WORD_REGEX = re.compile(r"[A-Za-z0-9]+(?:[-'][A-Za-z0-9]+)?")

def _tokens(s: str) -> set[str]:
    return {m.group(0).lower() for m in _WORD_REGEX.finditer(s)}


def _jaccard(tokens1: set[str], tokens2: set[str]) -> float:
    if not tokens1 and not tokens2:
        return 1.0
    intersection = tokens1.intersection(tokens2)
    union = tokens1.union(tokens2)
    return len(intersection) / len(union) if union else 0.0


class TokenRetriever(Retriever):
    def __init__(self) -> None:
        self._concepts: List[Concept] = []
        self._concept_tokens: List[set[str]] = []

    def index(self, concepts: List[Concept]) -> None:
        self._concepts = concepts
        self._concept_tokens = [_tokens(c.concept) for c in self._concepts]

    def retrieve(self, input_text: str, *, top_k: int = 10) -> List[RetrievedConcept]:
        if not self._concepts:
            return []
        
        q = _tokens(input_text)
        scored: List[Tuple[float, int]] = []
        for i, concept in enumerate(self._concept_tokens):
            score = _jaccard(q, concept)
            if score > 0:
                scored.append((score, i))



        scored.sort(reverse = True, key = lambda x: x[0])
        top = scored[: max(1, top_k)]

        return [
            RetrievedConcept(concept = self._concepts[i], score = score)
            for score, i in top
        ]