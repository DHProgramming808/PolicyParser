from __future__ import annotations

import json
import os
import sys

from typing import List, Dict, Optional, Any

from openai import OpenAI

from .base import DataEvaluationModel
from ..models import ValidationAuditTrail, Concept, InferenceResult, InferenceAccuracyEvaluation, RetrievalRealCrossReference, RetrievalInferenceCrossCheck, InferenceRealCrossReference


class MockEvaluationModel(DataEvaluationModel):

    def __init__(
        self,
        model: Optional[str] = None
    ) -> None:
        self._model = model


    def evaulate_inference_accuracy(self, original_text: str, inference_cross_reference: InferenceRealCrossReference, retrieval_cross_reference: RetreivalRealCrossReference, retrieval_inference_cross_check: RetrievalInferenceCrossCheck) -> InferenceAccuracyEvaluation:
        return InferenceAccuracyEvaluation(
            pct_correct = 0,
            pct_false_pos = 0,
            pct_false_neg = 0,
            code_evaluation = {},
            notes = []
        )