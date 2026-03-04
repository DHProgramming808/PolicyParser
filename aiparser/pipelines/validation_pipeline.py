from __future__ import annotations
import sys
import json

from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from pathlib import Path

from ..csv_loader import load_correct_policy_concepts, PolicyCodeCsvSchema

from ..data_validation.base import DataEvaluationModel
from ..data_validation.cross_check_result_utils import cross_reference_retrieval, cross_reference_inference, cross_check_inference_vs_retrieval
from ..models import ValidationAuditTrail, Concept, CorrectPolicyCodes, InferenceResult, InferenceAccuracyEvaluation, RetrievalRealCrossReference, RetrievalInferenceCrossCheck, InferenceRealCrossReference, RetrievedConcept, InferredCode


def get_real_codes_match_text(real_codes_raw: List[CorrectPolicyCodes], original_text: str = "-", text_id: str = "-") -> List[Concept]:
    for cpc in real_codes_raw:
        if cpc.policy_id == text_id or cpc.policy_uuid == original_text:
            return cpc.codes
    return []


@dataclass
class ValidationPipelineConfig: # TODO configure
    temp_config: str

class ResultValidationPipeline:
    def __init__(
        self,
        data_evaluation_model: DataEvaluationModel,
        config: ValidationPipelineConfig = ValidationPipelineConfig(),
        audit_trail: ValidationAuditTrail = None,
        *,
        model_info: Optional[Dict[str, Any]] = None
    ) -> None:
        self._data_evaluation_model = data_evaluation_model
        self._config = config
        self._audit_trail = audit_trail
        self._model_info = model_info or {}

    def run(self, original_text: str, retrieved_codes: List[RetrievedConcept], inferred_codes: List[InferredCode], csv_path: str = "") -> InferenceAccuracyEvaluation:

        # retrieve correct codes
        real_codes_csv = "aiparser/data/policies_cleaned_labels.csv" # csv_path
        real_codes_raw = load_correct_policy_concepts(real_codes_csv, PolicyCodeCsvSchema())

        real_codes: List[Concept] = get_real_codes_match_text(real_codes_raw, original_text)

        # get precision and recall / find errors in inferencing policy text
        retrieval_precision_recall: RetrievalRealCrossReference = cross_reference_retrieval(retrieved_codes, real_codes)
        inference_precision_recall: InferenceRealCrossReference = cross_reference_inference(inferred_codes, real_codes)
        cross_check_inference_retrieval: RetrievalInferenceCrossCheck = cross_check_inference_vs_retrieval(retrieval_precision_recall, inference_precision_recall)

        # build audit trail
        if self._audit_trail is None:
            self._a

        # run evaluation

        evaluation: InferenceAccuracyEvaluation = self._data_evaluation_model.evaulate_inference_accuracy(original_text, inference_precision_recall, retrieval_precision_recall, cross_check_inference_retrieval)

        return evaluation

