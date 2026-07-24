"""
ats_optimizer_service.py - Phase 4 Section-wise Analysis & ATS Optimization Service

Purpose
-------
Evaluates section-wise alignment (Skills, Projects, Experience, Education,
Certifications, Soft Skills) and generates actionable ATS optimization suggestions.
"""

import logging
import re
from typing import TypedDict, Any

logger = logging.getLogger(__name__)


class SectionAnalysisEntry(TypedDict):
    section_name: str
    score: int
    explanation: str
    suggestions: list[str]


class AtsOptimizationSuggestion(TypedDict):
    category: str  # "Placement", "Quantification", "Action Verbs", "Formatting", "Grouping"
    suggestion: str
    explanation: str
    impact: str  # "High", "Medium", "Low"


class SectionWiseAnalysisResult(TypedDict):
    sections: dict[str, SectionAnalysisEntry]
    ats_suggestions: list[AtsOptimizationSuggestion]


def analyze_sections_and_ats_optimization(
    resume_sections: dict[str, str],
    resume_skills: list[str],
    jd_skills: list[str],
    missing_skills: list[str],
    clean_text: str,
    jd_text: str
) -> SectionWiseAnalysisResult:
    """Perform section-wise comparison and generate ATS optimization suggestions."""
    
    # Normalize inputs
    sec_lower = {k.lower(): v for k, v in resume_sections.items()}
    resume_lower = clean_text.lower()
    jd_lower = jd_text.lower()

    sections_res: dict[str, SectionAnalysisEntry] = {}

    # 1. Skills Section
    matched_skills = [s for s in jd_skills if s.lower() in [rs.lower() for rs in resume_skills]]
    skill_score = min(100, int((len(matched_skills) / len(jd_skills)) * 100)) if jd_skills else 80
    sections_res["Skills"] = SectionAnalysisEntry(
        section_name="Skills",
        score=skill_score,
        explanation=f"Matched {len(matched_skills)} of {len(jd_skills)} target job description skills.",
        suggestions=[f"Add missing key skill: {s}" for s in missing_skills[:3]] or ["Skills section is well aligned."]
    )

    # 2. Projects Section
    proj_text = sec_lower.get("projects", "")
    has_proj = len(proj_text) > 50
    proj_matched = [s for s in jd_skills if s.lower() in proj_text.lower()]
    proj_score = 90 if has_proj and len(proj_matched) >= 2 else (65 if has_proj else 35)
    sections_res["Projects"] = SectionAnalysisEntry(
        section_name="Projects",
        score=proj_score,
        explanation="Projects demonstrate practical application of required skills." if proj_score >= 70 else "Project section lacks key JD skills or technical details.",
        suggestions=[f"Include a project demonstrating {s}" for s in missing_skills[:2]] if missing_skills else ["Highlight quantifiable impact metrics in project bullets."]
    )

    # 3. Experience Section
    exp_text = sec_lower.get("experience", "")
    has_exp = len(exp_text) > 100
    metrics_found = len(re.findall(r'\b\d+%\b|\$\d+|\b\d+\s*users\b|\b\d+\s*x\b', exp_text.lower()))
    exp_score = min(100, 60 + (metrics_found * 10) + (15 if has_exp else 0))
    sections_res["Experience"] = SectionAnalysisEntry(
        section_name="Experience",
        score=exp_score,
        explanation=f"Experience section contains {metrics_found} quantifiable metric achievement(s)." if metrics_found else "Experience section needs measurable metrics (%, $, scale).",
        suggestions=["Quantify achievements using numbers, percentages, or dollar values.", "Begin each bullet with strong action verbs (e.g., Architected, Spearheaded, Optimized)."]
    )

    # 4. Education Section
    edu_text = sec_lower.get("education", "")
    has_edu = len(edu_text) > 20
    edu_score = 95 if has_edu else 40
    sections_res["Education"] = SectionAnalysisEntry(
        section_name="Education",
        score=edu_score,
        explanation="Education section is present and clear." if has_edu else "Education section missing or insufficient details.",
        suggestions=[] if has_edu else ["Add degree, major, university name, and graduation year."]
    )

    # 5. Certifications Section
    cert_text = sec_lower.get("certifications", "")
    has_cert = len(cert_text) > 15
    cert_score = 85 if has_cert else 60
    sections_res["Certifications"] = SectionAnalysisEntry(
        section_name="Certifications",
        score=cert_score,
        explanation="Relevant certifications detected." if has_cert else "No explicit certifications section detected.",
        suggestions=["Include industry certifications relevant to the target role (e.g., AWS, CKA, PMP)."] if not has_cert else ["Keep certification titles accurate and un-abbreviated."]
    )

    # 6. Soft Skills Section
    soft_skills = ["communication", "leadership", "collaboration", "problem solving", "teamwork", "agile"]
    soft_found = [sk for sk in soft_skills if sk in resume_lower]
    soft_score = min(100, 50 + (len(soft_found) * 10))
    sections_res["Soft Skills"] = SectionAnalysisEntry(
        section_name="Soft Skills",
        score=soft_score,
        explanation=f"Detected soft skills: {', '.join(soft_found).title()}" if soft_found else "Few soft skills or leadership terms detected.",
        suggestions=["Weave soft skills naturally into experience bullet points (e.g., 'Led cross-functional team')."]
    )

    # ATS Optimization Suggestions
    ats_suggestions: list[AtsOptimizationSuggestion] = []

    # Placement
    for skill in missing_skills[:2]:
        if skill.lower() in clean_text.lower() and skill.lower() not in sec_lower.get("skills", "").lower():
            ats_suggestions.append(AtsOptimizationSuggestion(
                category="Placement",
                suggestion=f"Move '{skill}' into your dedicated Skills section.",
                explanation=f"'{skill}' appears in resume body text but is missing from your explicit Skills list where ATS parsers inspect first.",
                impact="High"
            ))

    # Metric Quantification
    if metrics_found < 3:
        ats_suggestions.append(AtsOptimizationSuggestion(
            category="Quantification",
            suggestion="Quantify at least 3 key achievements with metrics.",
            explanation="ATS algorithms and recruiters rank resumes 40% higher when achievements include %, $, or user scale metrics.",
            impact="High"
        ))

    # Action Verbs
    weak_verbs = ["worked", "handled", "responsible for", "helped", "assisted"]
    found_weak = [v for v in weak_verbs if v in clean_text.lower()]
    if found_weak:
        ats_suggestions.append(AtsOptimizationSuggestion(
            category="Action Verbs",
            suggestion=f"Replace weak verbs like '{found_weak[0]}' with impact verbs.",
            explanation=f"Replace passive terms ('{found_weak[0]}') with high-impact action verbs such as 'Architected', 'Engineered', or 'Spearheaded'.",
            impact="Medium"
        ))

    # Grouping & Formatting
    ats_suggestions.append(AtsOptimizationSuggestion(
        category="Grouping",
        suggestion="Group skills into categories (Languages, Frameworks, Cloud/Tools).",
        explanation="Categorized skills enable ATS parsers to accurately map your expertise to job taxonomy tiers.",
        impact="Medium"
    ))

    return SectionWiseAnalysisResult(
        sections=sections_res,
        ats_suggestions=ats_suggestions
    )
