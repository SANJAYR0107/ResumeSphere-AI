"""
interview_evaluator_service.py - Phase B AI Answer Evaluation & Follow-up Service

Purpose
-------
Evaluates candidate interview answers across technical accuracy, communication quality,
completeness, keyword coverage, confidence, and professionalism. Computes a score out of 10,
identifies missing concepts, strengths, weaknesses, and dynamically generates follow-up questions.
"""

import logging
import re
from typing import TypedDict, Any

from backend.app.services.preprocessing_service import preprocess

logger = logging.getLogger(__name__)


class AnswerEvaluationResult(TypedDict):
    question_id: str
    overall_score: float  # 0.0 to 10.0
    technical_accuracy_score: float  # 0.0 to 10.0
    communication_score: float  # 0.0 to 10.0
    completeness_score: float  # 0.0 to 10.0
    keyword_coverage_score: float  # 0.0 to 10.0
    confidence_score: float  # 0.0 to 10.0
    professionalism_score: float  # 0.0 to 10.0
    matched_keywords: list[str]
    missing_concepts: list[str]
    strengths: list[str]
    weaknesses: list[str]
    suggested_improvements: list[str]
    sample_excellent_answer: str
    follow_up_question: str | None


def evaluate_answer(
    question_text: str,
    answer_text: str,
    expected_concepts: list[str],
    target_skill: str,
    question_id: str = "q_1"
) -> AnswerEvaluationResult:
    """Evaluate candidate answer and generate detailed scoring, feedback, and dynamic follow-up."""
    
    if not answer_text or not answer_text.strip():
        return AnswerEvaluationResult(
            question_id=question_id,
            overall_score=0.0,
            technical_accuracy_score=0.0,
            communication_score=0.0,
            completeness_score=0.0,
            keyword_coverage_score=0.0,
            confidence_score=0.0,
            professionalism_score=0.0,
            matched_keywords=[],
            missing_concepts=expected_concepts,
            strengths=[],
            weaknesses=["No answer was provided."],
            suggested_improvements=["Provide a structured answer using technical concepts."],
            sample_excellent_answer=f"An ideal answer for '{question_text}' should cover {', '.join(expected_concepts)} with specific examples.",
            follow_up_question=f"Could you explain the fundamental concepts of {target_skill}?"
        )

    clean_ans = preprocess(answer_text).lower()
    words = clean_ans.split()
    word_count = len(words)

    # 1. Concept Matching & Keyword Coverage
    matched_kws: list[str] = []
    missing_c: list[str] = []

    for concept in expected_concepts:
        concept_clean = concept.lower()
        if concept_clean in clean_ans or any(w in clean_ans for w in concept_clean.split()):
            matched_kws.append(concept)
        else:
            missing_c.append(concept)

    kw_ratio = (len(matched_kws) / len(expected_concepts)) if expected_concepts else 0.8
    keyword_score = round(min(10.0, kw_ratio * 10.0), 1)

    # 2. Technical Accuracy
    tech_score = round(min(10.0, (keyword_score * 0.7) + (3.0 if word_count >= 30 else word_count * 0.1)), 1)

    # 3. Completeness & Length Assessment
    if word_count >= 80:
        comp_score = 9.5
    elif word_count >= 40:
        comp_score = 8.0
    elif word_count >= 20:
        comp_score = 6.0
    else:
        comp_score = 4.0

    # 4. Communication & Professionalism
    filler_words = ["um", "uh", "like", "maybe", "basically", "you know", "i guess"]
    filler_count = sum(len(re.findall(rf'\b{f}\b', clean_ans)) for f in filler_words)
    comm_score = round(max(3.0, min(10.0, 9.0 - (filler_count * 1.0))), 1)
    prof_score = round(max(4.0, min(10.0, 9.5 - (filler_count * 0.5))), 1)

    # 5. Confidence Score
    weak_phrases = ["not sure", "don't know", "i think maybe", "probably not"]
    has_weakness = any(p in clean_ans for p in weak_phrases)
    conf_score = round(max(3.0, 8.5 if not has_weakness else 5.0), 1)

    # Composite Overall Score out of 10
    overall = round((tech_score * 0.35) + (comp_score * 0.25) + (keyword_score * 0.20) + (comm_score * 0.10) + (conf_score * 0.10), 1)

    # Strengths & Weaknesses
    strengths: list[str] = []
    weaknesses: list[str] = []
    improvements: list[str] = []

    if matched_kws:
        strengths.append(f"Accurately incorporated key concepts: {', '.join(matched_kws)}.")
    if word_count >= 40:
        strengths.append("Provided a detailed explanation with clear structure.")
    
    if missing_c:
        weaknesses.append(f"Missed key concepts: {', '.join(missing_c)}.")
        improvements.append(f"Be sure to explicitly cover {', '.join(missing_c[:2])} when discussing {target_skill}.")
    
    if word_count < 30:
        weaknesses.append("Answer was somewhat concise and could benefit from concrete project examples.")
        improvements.append("Elaborate on real-world production experience or code implementations.")

    # Sample Excellent Answer
    sample_ans = (
        f"A top-tier answer for this role clearly addresses '{question_text}' by stating: "
        f"'In my experience with {target_skill}, I ensure system reliability by focusing on {', '.join(expected_concepts[:3])}. "
        f"For example, during a project build, I implemented these principles to achieve scalable results.'"
    )

    # Dynamic Follow-up Question Generation (Module B4)
    follow_up: str | None = None
    if matched_kws:
        follow_up = f"You mentioned '{matched_kws[0]}'. Can you elaborate on how you optimize or debug issues related to {matched_kws[0]} in a high-concurrency production environment?"
    elif missing_c:
        follow_up = f"Could you explain how '{missing_c[0]}' applies to {target_skill} and how you would design for it?"
    else:
        follow_up = f"What trade-offs do you consider when implementing {target_skill} in real-world systems?"

    return AnswerEvaluationResult(
        question_id=question_id,
        overall_score=overall,
        technical_accuracy_score=tech_score,
        communication_score=comm_score,
        completeness_score=comp_score,
        keyword_coverage_score=keyword_score,
        confidence_score=conf_score,
        professionalism_score=prof_score,
        matched_keywords=matched_kws,
        missing_concepts=missing_c,
        strengths=strengths if strengths else ["Attempted question response."],
        weaknesses=weaknesses if weaknesses else ["Minor depth additions recommended."],
        suggested_improvements=improvements if improvements else ["Keep maintaining structured STAR technique answers."],
        sample_excellent_answer=sample_ans,
        follow_up_question=follow_up
    )
