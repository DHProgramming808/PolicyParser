from __future__ import annotations
from abc import ABC, abstractmethod
from typing import List, Dict
from ..models import InferredCode, InferenceRealCrossReference, Concept, RetrievedConcept, RetreivalRealCrossReference, RetrievalInferenceCrossCheck, InferenceAccuracyEvaluation


class DataValidationModel(ABC):
    @abstractmethod
    #This method will provide the evaluation of the accuracy of inferred codes and attempt to reason why
    # Algorithmic -> will look at Correct, Missed, Wrong codes to determine which step is most likely to fail, then send back pre-determined reasonings from dev
    # AI v1 -> will isolate take these signals and send them into LLM to get back reasoning why some codes were missed and some were not.
    # AI v2 -> will send the entire text alongside the evaluation metadata with the Correct, Missed, and Wrong codes, to a reasoning LLM and try to get back a reason
    def evaulate_inference_accuracy(self, inferece_cross_reference: InferenceRealCrossReference, retrieval_cross_reference: RetreivalRealCrossReference, retrieval_inference_cross_check: RetrievalInferenceCrossCheck) -> InferenceAccuracyEvaluation:
        ...