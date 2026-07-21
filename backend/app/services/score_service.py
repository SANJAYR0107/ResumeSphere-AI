"""
score_service.py — Phase 2 Score Calculation Service

Purpose
-------
Generates comprehensive Section Scores and an Overall Resume Score out of 100
by synthesizing data from ATS analysis, NLP quality checks, and section extraction.
"""

from typing import TypedDict, Any


class SectionScore(TypedDict):
    score: int
    reason: str
    improvement: str


class OverallScoreResult(TypedDict):
    overall_score: int
    confidence: float
    explanation: str


def _safe_len(text: str) -> int:
    return len(text) if text else 0


def calculate_section_scores(
    sections: dict[str, str],
    skills: list[str],
    quality_report: Any,
    ats_breakdown: dict[str, Any]
) -> dict[str, SectionScore]:
    """Calculate independent scores out of 100 for various resume aspects."""
    scores: dict[str, SectionScore] = {}

    # 1. ATS Score
    ats_score_val = sum(d["score"] for d in ats_breakdown.values()) if ats_breakdown else 0
    scores["ats_score"] = {
        "score": ats_score_val,
        "reason": f"Your ATS compatibility score is {ats_score_val}/100 based on standard parsing metrics.",
        "improvement": "Include missing keywords and ensure standard section headings." if ats_score_val < 80 else "Excellent ATS compatibility."
    }

    # 2. Technical Skills Score
    num_skills = len(skills)
    tech_score = min(100, num_skills * 5)
    scores["technical_skills"] = {
        "score": tech_score,
        "reason": f"Found {num_skills} technical skills.",
        "improvement": "Add more relevant tools, frameworks, and programming languages." if tech_score < 75 else "Strong technical skill presence."
    }

    # 3. Projects Score
    proj_len = _safe_len(sections.get("projects", ""))
    proj_score = min(100, int((proj_len / 500) * 100)) if proj_len > 0 else 0
    scores["projects"] = {
        "score": proj_score,
        "reason": f"Project section length indicates {'strong' if proj_score > 70 else 'light'} detail.",
        "improvement": "Add more detailed projects with measurable outcomes and technologies used." if proj_score < 80 else "Projects are well-detailed."
    }

    # 4. Experience Score
    exp_len = _safe_len(sections.get("experience", ""))
    exp_score = min(100, int((exp_len / 800) * 100)) if exp_len > 0 else 0
    scores["experience"] = {
        "score": exp_score,
        "reason": "Experience section is comprehensive." if exp_score > 75 else "Experience section is lacking detail.",
        "improvement": "Elaborate on professional experience using the STAR method." if exp_score < 80 else "Strong professional experience."
    }

    # 5. Education Score
    has_edu = "education" in sections
    edu_score = 100 if has_edu else 0
    scores["education"] = {
        "score": edu_score,
        "reason": "Education section present." if has_edu else "No education section found.",
        "improvement": "Ensure degree, university, and graduation year are clearly listed." if not has_edu else "Education is well structured."
    }

    # 6. Grammar Score
    grammar_issues = len(quality_report.get("grammar_issues", []))
    grammar_score = max(0, 100 - (grammar_issues * 15))
    scores["grammar"] = {
        "score": grammar_score,
        "reason": f"Detected {grammar_issues} grammar/formatting issues." if grammar_issues > 0 else "No major grammar issues detected.",
        "improvement": "Proofread for punctuation and capitalization consistency." if grammar_issues > 0 else "Grammar is clean."}

    # 7. Formatting Score
    formatting_pts = ats_breakdown.get("formatting_grammar", {}).get("score", 0)
    fmt_score = min(100, formatting_pts)
    scores["formatting"] = {
        "score": fmt_score,
        "reason": "Clear bullet points and standard layout." if fmt_score > 70 else "Layout lacks standard bullet points.",
        "improvement": "Use standard bullet points instead of paragraphs for better readability." if fmt_score < 80 else "Excellent formatting."
    }

    # 8. Professionalism Score
    passive_issues = len(quality_report.get("passive_language_found", []))
    weak_verbs = len(quality_report.get("weak_verbs_found", []))
    prof_score = max(0, 100 - (passive_issues * 10) - (weak_verbs * 5))
    if quality_report.get("has_linkedin") or quality_report.get("has_github"):
        prof_score = min(100, prof_score + 10)

    scores["professionalism"] = {
        "score": prof_score,
        "reason": "Professional tone with strong action verbs." if prof_score >= 90 else "Found passive language or weak verbs.",
        "improvement": "Replace 'responsible for' and 'helped' with strong action verbs like 'spearheaded' or 'architected'." if prof_score < 90 else "Highly professional tone."
    }

    # 9. Keyword Score
    kw_density_pts = ats_breakdown.get("keyword_density", {}).get("score", 0)
    kw_score = min(100, kw_density_pts)
    scores["keyword"] = {
        "score": kw_score,
        "reason": "Good keyword density relative to word count." if kw_score >= 80 else "Low keyword density.",
        "improvement": "Sprinkle more technical keywords naturally throughout experience bullet points." if kw_score < 80 else "Keywords are well balanced."
    }

    # 10. Completeness Score
    missing = len(quality_report.get("missing_sections", []))
    comp_score = max(0, 100 - (missing * 20))
    scores["completeness"] = {
        "score": comp_score,
        "reason": f"Missing {missing} core sections." if missing > 0 else "All core sections present.",
        "improvement": f"Add missing sections: {', '.join(quality_report.get('missing_sections', []))}" if missing > 0 else "Resume is fully complete."
    }

    return scores


def calculate_overall_score(
        section_scores: dict[str, SectionScore]) -> OverallScoreResult:
    """Calculate the overall resume score out of 100 using a weighted average."""

    weights = {
        "ats_score": 0.20,
        "experience": 0.20,
        "technical_skills": 0.15,
        "projects": 0.10,
        "completeness": 0.10,
        "grammar": 0.05,
        "formatting": 0.05,
        "professionalism": 0.05,
        "keyword": 0.05,
        "education": 0.05
    }

    total_score = 0.0
    for key, weight in weights.items():
        score_data = section_scores.get(key)
        score = score_data["score"] if score_data else 0
        total_score += score * weight

    overall = int(round(total_score))

    # Generate explanation
    if overall >= 90:
        exp = "Outstanding resume! Highly optimized for ATS and recruiters. Excellent detail and professional tone."
    elif overall >= 75:
        exp = "Strong resume. Covers most critical areas well but has room for fine-tuning keywords or action verbs."
    elif overall >= 60:
        exp = "Average resume. Needs structural improvements, more measurable achievements, and stronger keywords."
    else:
        exp = "Needs significant improvement. Ensure all core sections are present and thoroughly detailed."

    return {
        "overall_score": min(100, overall),
        "confidence": 0.95,
        "explanation": exp
    }
