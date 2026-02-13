from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from .models import InferenceResult, RetrievedConcept, RetrievalCandidateAudit
from .retriever.base import Retriever
from .llm.base import CodeInferenceModel
from .models import AuditTrail, RetrievalAudit, ModelAudit


@dataclass
class PipelineConfig:
    top_k: int = 15
    min_retrieval_score: float = 0.05


class CodeInferencePipeline:
    def __init__(
        self,
        retriever: Retriever,
        model: CodeInferenceModel,
        config: PipelineConfig = PipelineConfig(),
        audit_trail: AuditTrail = None,
        *,
        model_info: Optional[Dict[str, Any]] = None
    ) -> None:
        self._retriever = retriever
        self._model = model
        self._config = config
        self._audit_trail = audit_trail
        self._model_info = model_info or {}

    def run(self, input_text: str, audit_trail: AuditTrail = None) -> InferenceResult:
        retrieved_raw = self._retriever.retrieve(input_text, top_k=self._config.top_k)
        retrieved = [r for r in retrieved_raw if r.score >= self._config.min_retrieval_score]

        print(f"Retrieved {len(retrieved)} concepts after applying min_retrieval_score filter.")
        retrieval_audit = RetrievalAudit(
            retriever_name = type(self._retriever).__name__,
            retreiver_version = "1.0", # hardcoded for now, should be dynamic
            top_k = self._config.top_k,
            min_retrieval_score = self._config.min_retrieval_score,
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