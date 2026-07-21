"""
skill_gap_service.py  —  Phase 4 Skill Gap Analysis

Purpose
-------
Analyse the gap between a candidate's skills and a target job description,
and generate actionable learning suggestions and recommended skills.
"""

import logging

logger = logging.getLogger(__name__)


def analyze_skill_gap(
    matched_skills: list[str],
    missing_skills: list[str],
) -> dict:
    """Analyze the skill gap and provide actionable learning suggestions.

    Parameters
    ----------
    matched_skills : list[str]
        Skills present in both the resume and the job description.
    missing_skills : list[str]
        Skills present in the job description but absent from the resume.

    Returns
    -------
    dict
        {
            "matched_skills": list[str],
            "missing_skills": list[str],
            "recommended_skills": list[str],
            "learning_suggestions": list[str],
        }
    """
    learning_suggestions = []

    # Recommended skills are the missing ones, prioritised by importance
    # (assuming JD order or just top 5)
    recommended_skills = missing_skills[:10]

    if not missing_skills:
        learning_suggestions.append(
            "Excellent match! Your skill set perfectly aligns with the job description. Focus on interview preparation and system design.")
    else:
        top_missing = missing_skills[:3]
        learning_suggestions.append(
            f"Prioritise learning these core skills: {', '.join(top_missing)}."
        )

        missing_lower = {s.lower() for s in missing_skills}

        if missing_lower & {
            "python",
            "java",
            "javascript",
            "c++",
            "c#",
            "go",
            "typescript",
                "ruby"}:
            learning_suggestions.append(
                "Build small, domain-specific projects to gain practical experience with the missing programming languages.")

        if missing_lower & {
            "aws",
            "azure",
            "gcp",
            "docker",
            "kubernetes",
                "terraform"}:
            learning_suggestions.append(
                "Consider earning a fundamental cloud or DevOps certification (e.g., AWS Cloud Practitioner) to close the infrastructure gap.")

        if missing_lower & {
            "react",
            "angular",
            "vue",
            "html",
            "css",
                "next.js"}:
            learning_suggestions.append(
                "Create a frontend portfolio project or UI clone to demonstrate proficiency in the missing web frameworks.")

        if missing_lower & {"sql", "postgresql", "mongodb", "mysql", "redis"}:
            learning_suggestions.append(
                "Practice writing complex queries on LeetCode or HackerRank to improve your database skills.")

        if missing_lower & {
            "machine learning",
            "tensorflow",
            "pytorch",
            "scikit-learn",
            "pandas",
                "numpy"}:
            learning_suggestions.append(
                "Complete a Kaggle competition or a data science tutorial to bridge the gap in machine learning tools.")

        learning_suggestions.append(
            "If you already have basic familiarity with any of these missing skills, ensure you explicitly add them to your resume's Skills section.")

    logger.info(
        "skill_gap_service: generated %d learning suggestions for %d missing skills.",
        len(learning_suggestions),
        len(missing_skills))

    return {
        "matched_skills": matched_skills,
        "missing_skills": missing_skills,
        "recommended_skills": recommended_skills,
        "learning_suggestions": learning_suggestions,
    }
