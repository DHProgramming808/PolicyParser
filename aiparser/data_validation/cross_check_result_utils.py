from __future__ import annotations
from typing import List, Dict
from ..models import InferredCode, InferenceRealCrossReference, Concept, RetrievedConcept, RetreivalRealCrossReference, RetrievalInferenceCrossCheck


def cross_reference_inference(self, inferred_codes: List[InferredCode], real_codes: List[Concept]) -> InferenceRealCrossReference:
    codes_inferred = {inferred_code.code for inferred_code in inferred_codes}
    codes_real = {real_code.code for real_code in real_codes}
    
    correct_codes = [inferred_code for inferred_code in inferred_codes if inferred_code.code in codes_real]
    wrong_codes = [inferred_code for inferred_code in inferred_codes if inferred_code.code not in codes_real]
    missed_codes = [real_code for real_code in real_codes if real_code.code not in codes_inferred]

    inferenceRealCrossReference = InferenceRealCrossReference(
        correct_codes = correct_codes,
        wrong_codes = wrong_codes,
        missed_codes = missed_codes
    )

    return inferenceRealCrossReference



def cross_reference_retrieval(self, retrieved_codes: List[RetrievedConcept], real_codes: List[Concept]) -> RetreivalRealCrossReference:
    codes_retrieved = {retrieved_code.code for retrieved_code in retrieved_codes}
    codes_real = {real_code.code for real_code in real_codes}

    correct_codes = [retrieved_code for retrieved_code in retrieved_codes if retrieved_code.code in codes_real]
    wrong_codes = [retrieved_code for retrieved_code in retrieved_codes if retrieved_code.code not in codes_real]
    missed_codes = [real_code for real_code in real_codes if real_code.code not in codes_retrieved]

    retrievedRealCrossReference = RetreivalRealCrossReference(
        correct_codes = correct_codes,
        wrong_codes = wrong_codes,
        missed_codes = missed_codes
    )

    return retrievedRealCrossReference



    #This method wants to look at things. 
    # 1. Correct codes in retrieval that are missed in inference
    # 2. Wrong codes in retrieval that are correctly excluded in inference
def cross_check_inference_vs_retrieval(self, inference_cross_reference: InferenceRealCrossReference, retrieved_cross_reference: RetreivalRealCrossReference) -> RetrievalInferenceCrossCheck:
    correct_inference_codes = inference_cross_reference.correct_codes
    correct_retrieval_codes = retrieved_cross_reference.correct_codes
    codes_correct_inference = {correct_inferred_code.code for correct_inferred_code in correct_inference_codes}

    wrong_inference_codes = inference_cross_reference.wrong_codes
    wrong_retrieval_codes = retrieved_cross_reference.wrong_codes
    codes_wrong_inference = {wrong_inferred_code.code for wrong_inferred_code in wrong_inference_codes}

    missed_correct_retrieved_to_inference = [correct_retrieved_code for correct_retrieved_code in correct_retrieval_codes if correct_retrieved_code.code not in codes_correct_inference]
    excluded_wrong_retrieved_to_inference = [wrong_retrieved_code for wrong_retrieved_code in wrong_retrieval_codes if wrong_retrieved_code.code not in codes_wrong_inference]

    retrievalInferenceCrossCheck = RetrievalInferenceCrossCheck(
        missed_inference_codes = missed_correct_retrieved_to_inference,
        excluded_wrong_inference_codes = excluded_wrong_retrieved_to_inference
    )

    return retrievalInferenceCrossCheck

