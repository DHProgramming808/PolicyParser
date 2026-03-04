from __future__ import annotations
import sys
import json

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from ..models.models import InferenceResult, RetrievedConcept, RetrievalCandidateAudit, AuditTrail, RetrievalAudit, ModelAudit
from ..retrieval.openai_embedding_retriever import OpenAIEmbeddingRetriever
from ..inference.openai_inference import OpenAIInferenceModel

class SimpleTextCodeInferencePipeline:
    def __init__(
        self,
        retriever: OpenAIEmbeddingRetriever,
        inference_model: OpenAIInferenceModel,
        audit_trail: AuditTrail = None,
        top_k: int = 50,
        min_retrieval_score: float = 0.005,
        *,
        model_info: Optional[Dict[str, Any]] = None
    ) -> None:
        self._retriever = retriever
        self._model = inference_model
        self._top_k = top_k
        self._min_retrieval_score = min_retrieval_score
        self._audit_trail = audit_trail
        self._model_info = model_info or {}

    def run(self, input_text: str, correct_codes: Optional[List[str]] = None, audit_trail: AuditTrail = None) -> InferenceResult:
        self._audit_trail = audit_trail

        retrieved_raw = self._retriever.retrieve(input_text, top_k=self._top_k)
        retrieved = [r for r in retrieved_raw if r.score >= self._min_retrieval_score]

        #print(input_text)
        #print(retrieved)
        #sys.stdout.write("\n")

        retrieval_audit = RetrievalAudit(
            retriever_name = type(self._retriever).__name__,
            retreiver_version = "1.0", # hardcoded for now, should be dynamic
            top_k = self._top_k,
            min_retrieval_score = self._min_retrieval_score,
            candidates = self._to_candidate_audit(retrieved_raw)
        )

        if self._audit_trail is not None:
            self._audit_trail.retrieval = retrieval_audit

        if self._audit_trail is not None:
            self._audit_trail.model = ModelAudit(
                model_name = type(self._model).__name__,
                model_version = "1.0", # hardcoded for now, should be dynamic
                model_info = self._model_info
            )

        inferred = self._model.infer_codes(input_text, retrieved)



        return InferenceResult(
            input_text = input_text,
            inferred = inferred,
            audit = self._audit_trail
        )  
    

    def _to_candidate_audit(self, retrieved: List[RetrievedConcept]) -> List[RetrievalCandidateAudit]:
        return [
            RetrievalCandidateAudit(
                code=r.concept.code,
                concept=r.concept.concept,
                retrieval_score=float(r.score),
            )
            for r in retrieved
        ]
