# code_inference/llm/base.py
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List

from ..models import RetrievedConcept, InferredCode


class CodeInferenceModel(ABC):
    @abstractmethod
    def infer_codes(self, input_text: str, retrieved_concepts: List[RetrievedConcept]) -> List[InferredCode]:
        ...