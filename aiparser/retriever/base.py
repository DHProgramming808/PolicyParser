from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Dict

from ..models import RetrievedConcept, Concept


class Retriever(ABC):
    @abstractmethod
    def index(self, concepts: List[Concept]) -> None:
        ...


    @abstractmethod
    def retrieve(self, input_text: str, *, top_k: int = 10) -> List[RetrievedConcept]:
        ...