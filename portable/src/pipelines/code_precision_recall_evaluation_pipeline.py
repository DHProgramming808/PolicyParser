from __future__ import annotations
import sys
import json

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from ..models.models import InferenceResult, RetrievedConcept, RetrievalCandidateAudit, AuditTrail, InferenceAccuracyEvaluation, ModelAudit, InferenceRealCrossReference, RetrievalRealCrossReference, RetrievalInferenceCrossCheck, Concept, InferredCode
from ..validation.openai_inference_evaluation import OpenAIEvaluationModel
from ..utils.cross_check_results_utils import cross_reference_inference, cross_reference_retrieval, cross_check_inference_vs_retrieval

class SimpleInferenceEvaluationPipeline:
    def __init__(
        self,
        evaluation_model: OpenAIEvaluationModel,
        audit_trail: AuditTrail = None,
        *,
        model_info: Optional[Dict[str, Any]] = None
    ) -> None:
        self._model = evaluation_model
        self._audit_trail = audit_trail
        self._model_info = model_info or {}

    def run(self, input_text: str, inferred: List[InferredCode], retrieved: List[RetrievalCandidateAudit], correct_codes: Dict[str, str],  audit_trail: AuditTrail = None) -> InferenceAccuracyEvaluation:
        self._audit_trail = audit_trail

        if self._audit_trail is not None:
            self._audit_trail.model = ModelAudit(
                model_name = type(self._model).__name__,
                model_version = "1.0", # hardcoded for now, should be dynamic
                model_info = self._model_info
            )

        #transform inputs for util classes
        retrieved_codes: List[RetrievedConcept] = [
            RetrievedConcept(
                code = ret.code,
                concept = Concept(code = ret.code, concept = ret.concept),
                score = ret.retrieval_score,
            ) for ret in retrieved
        ]
        real_codes: List[Concept] = [
            Concept(
                code = code,
                concept = concept
            ) for code, concept in correct_codes.items()
        ]


        inference_real_cross_check: InferenceRealCrossReference = cross_reference_inference(inferred, real_codes)
        retrieval_real_cross_check: RetrievalRealCrossReference = cross_reference_retrieval(retrieved_codes, real_codes)
        retrieval_inference_cross_check: RetrievalInferenceCrossCheck = cross_check_inference_vs_retrieval(inference_real_cross_check, retrieval_real_cross_check)


        evaluation: InferenceAccuracyEvaluation = self._model.evaulate_inference_accuracy(input_text, inference_real_cross_check, retrieval_real_cross_check, retrieval_inference_cross_check)

        return evaluation
    
