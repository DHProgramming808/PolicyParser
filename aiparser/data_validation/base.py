from __future__ import annotations
from abc import ABC, abstractmethod
from typing import List, Dict
from ..models import InferredCode, InferenceRealCrossReference, Concept


class DataValidationModel(ABC):
    @abstractmethod
    def cross_reference_inference(self, inferred_codes: List[InferredCode], real_codes: List[Concept]) -> List[InferenceRealCrossReference]:
        ...