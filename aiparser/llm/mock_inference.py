from __future__ import annotations

from typing import Dict, List

from .base import CodeInferenceModel
from ..models import RetrievedConcept, InferredCode


class MockCodeInferenceModel(CodeInferenceModel):


    def infer_codes(self, input_text: str, retrieved_concepts: List[RetrievedConcept]) -> List[InferredCode]:
        by_code: Dict[str, List[RetrievedConcept]] = {}
        for rc in retrieved_concepts:
            by_code.setdefault(rc.concept.code, []).append(rc)

        inferred: List[InferredCode] = []
        for code, concepts in by_code.items():
            hits_sorted = sorted(concepts, key = lambda c: c.score, reverse = True)
            top = hits_sorted[0]
            
            confidence = max(0.01, min(1.0, top.score))

            matched_concepts = [h.concept.concept for h in hits_sorted[:3]]
            justification = (
                f"Matched concepts(s) for code {code}: "
                + "; ".join([f"'{c}'" for c in matched_concepts])
                + f" with confidence {confidence:.2f} based on input"
            )

            inferred.append(
                InferredCode(
                    code = code,
                    confidence = round(confidence, 2),
                    score = confidence,
                    matched_concepts = matched_concepts,
                    justification = justification
                )
            )

        inferred.sort(key = lambda x: x.score, reverse = True)
        return inferred