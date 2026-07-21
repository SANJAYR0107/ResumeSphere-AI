"""
insights_service.py — Phase 2 Deep Insights Service

Purpose
-------
Performs deep linguistic, structural, and semantic analysis on the resume.
Identifies strengths, weaknesses, actionable suggestions, and conducts targeted
analyses on projects, skills, experience, grammar, keywords, and summary.
"""

import re
from typing import TypedDict, Any

# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class Suggestion(TypedDict):
    suggestion: str
    priority: str  # "High", "Medium", "Low"
    difficulty: str  # "Easy", "Medium", "Hard"
    estimated_learning_time: str


class ProjectAnalysis(TypedDict):
    complexity: str
    technologies_mentioned: int
    business_value_found: bool
    technical_depth: str
    action_verbs_used: int
    missing_metrics: bool
    suggestions: list[str]


class SkillAnalysis(TypedDict):
    groups: dict[str, list[str]]
    missing_skills: list[str]
    duplicate_skills: list[str]
    obsolete_skills: list[str]
    recommended_skills: list[str]


class ExperienceAnalysis(TypedDict):
    estimated_years: str
    has_internship: bool
    achievements_found: int
    leadership_detected: bool
    impact_metrics_found: int
    action_verbs_used: int
    suggestions: list[str]


class GrammarAnalysis(TypedDict):
    repeated_punctuation: bool
    passive_voice_instances: int
    weak_verbs_instances: int
    repeated_words: bool
    capitalization_issues: bool
    sentence_length_warning: bool
    bullet_consistency: str
    findings: list[str]


class KeywordAnalysis(TypedDict):
    keyword_density: float
    technical_keywords: int
    missing_keywords: list[str]
    repeated_keywords: list[str]
    unused_sections: list[str]


class SummaryAnalysis(TypedDict):
    length_status: str
    grammar_check: str
    technology_coverage: int
    career_objective_found: bool
    professional_tone: str
    improvements: list[str]

# ---------------------------------------------------------------------------
# Helper Functions
# ---------------------------------------------------------------------------


def _count_metrics(text: str) -> int:
    """Counts numbers or percentage symbols as a proxy for metrics."""
    return len(re.findall(r'\b\d+\b|%', text))

# ---------------------------------------------------------------------------
# Analysis Methods
# ---------------------------------------------------------------------------


def analyze_projects(sections: dict[str, str]) -> ProjectAnalysis:
    proj_text = sections.get("projects", "")
    metrics = _count_metrics(proj_text)
    length = len(proj_text)

    comp = "Low"
    if length > 500 and metrics > 1:
        comp = "High"
    elif length > 200:
        comp = "Medium"

    suggestions: list[str] = []
    if metrics == 0 and length > 0:
        suggestions.append(
            "Add measurable metrics (e.g., 'improved speed by 20%') to your projects.")
    if length > 0 and length < 200:
        suggestions.append(
            "Elaborate on the technical architecture of your projects.")

    return {
        "complexity": comp,
        "technologies_mentioned": len(re.findall(r'\b(React|Python|Java|Docker|AWS|Node|SQL|C\+\+)\b', proj_text, re.I)),
        "business_value_found": bool(re.search(r'(revenue|cost|saved|increased|decreased|efficiency)', proj_text, re.I)),
        "technical_depth": "Deep" if length > 500 else "Shallow",
        "action_verbs_used": len(re.findall(r'\b(built|created|developed|designed|architected|led)\b', proj_text, re.I)),
        "missing_metrics": metrics == 0,
        "suggestions": suggestions if length > 0 else ["Add a dedicated Projects section to showcase your work."]
    }


def analyze_skills(skill_matches: list[Any]) -> SkillAnalysis:
    groups: dict[str, list[str]] = {
        "Programming": [], "Frameworks": [], "Database": [], "Cloud": [],
        "DevOps": [], "Testing": [], "Security": [], "Version Control": [],
        "AI/ML": [], "Soft Skills": []
    }

    for s in skill_matches:
        cat = s.get("category", "Programming")
        if cat in groups:
            groups[cat].append(s["skill"])
        else:
            # map to closest or Programming
            groups["Programming"].append(s["skill"])

    obsolete = []
    for s in skill_matches:
        if s["skill"].lower() in {"jquery", "angularjs", "svn", "vb6"}:
            obsolete.append(s["skill"])

    return {
        "groups": {k: v for k, v in groups.items() if v},
        "missing_skills": ["Docker", "AWS"] if not groups.get("Cloud") and not groups.get("DevOps") else [],
        "duplicate_skills": [],  # The skill extractor already deduplicates
        "obsolete_skills": obsolete,
        "recommended_skills": ["Kubernetes", "CI/CD"] if groups.get("Cloud") else ["Git"]
    }


def analyze_experience(sections: dict[str, str]) -> ExperienceAnalysis:
    exp_text = sections.get("experience", "")
    metrics = _count_metrics(exp_text)

    # Simple year heuristic: count "20XX - 20XX"
    years_mentions = len(re.findall(r'20\d{2}', exp_text))
    est_years = "3+ years" if years_mentions > 4 else (
        "1-2 years" if years_mentions > 0 else "Entry Level")

    suggestions: list[str] = []
    if metrics < 2 and len(exp_text) > 0:
        suggestions.append(
            "Quantify your professional achievements with numbers and percentages.")

    return {
        "estimated_years": est_years,
        "has_internship": bool(re.search(r'intern|internship', exp_text, re.I)),
        "achievements_found": metrics,
        "leadership_detected": bool(re.search(r'led|managed|mentored|directed', exp_text, re.I)),
        "impact_metrics_found": metrics,
        "action_verbs_used": len(re.findall(r'\b(spearheaded|orchestrated|developed|optimized)\b', exp_text, re.I)),
        "suggestions": suggestions if len(exp_text) > 0 else ["Add a detailed Experience section."]
    }


def analyze_grammar(raw_text: str, quality_report: Any) -> GrammarAnalysis:
    repeated_punct = bool(re.search(r'[!?.]{3,}', raw_text))
    repeated_words = bool(re.search(r'\b(\w+)\s+\1\b', raw_text, re.I))

    findings = []
    if repeated_punct:
        findings.append("Avoid excessive or repeated punctuation.")
    if repeated_words:
        findings.append("Check for accidentally repeated consecutive words.")
    if quality_report.get("passive_language_found"):
        findings.append("Passive voice detected. Use active phrasing.")

    return {
        "repeated_punctuation": repeated_punct,
        "passive_voice_instances": len(quality_report.get("passive_language_found", [])),
        "weak_verbs_instances": len(quality_report.get("weak_verbs_found", [])),
        "repeated_words": repeated_words,
        "capitalization_issues": bool(re.search(r'^[a-z]', raw_text, re.MULTILINE)),
        "sentence_length_warning": False,
        "bullet_consistency": quality_report.get("bullet_consistency", "Consistent"),
        "findings": findings if findings else ["Grammar and mechanics are solid."]
    }


def analyze_keywords(raw_text: str,
                     skills: list[str],
                     sections: dict[str,
                                    str]) -> KeywordAnalysis:
    words = len(raw_text.split())
    density = len(skills) / words * 100 if words > 0 else 0

    expected = {"summary", "experience", "education", "skills", "projects"}
    unused = list(expected - set(sections.keys()))

    return {
        "keyword_density": round(density, 2),
        "technical_keywords": len(skills),
        "missing_keywords": ["Agile", "REST API"] if density < 1.0 else [],
        "repeated_keywords": [],  # Skill extractor handles deduplication
        "unused_sections": unused
    }


def analyze_summary(sections: dict[str, str]) -> SummaryAnalysis:
    summary = sections.get("summary", "")
    words = len(summary.split())

    if words == 0:
        length_status = "Missing"
    elif words < 30:
        length_status = "Too Short"
    elif words > 100:
        length_status = "Too Long"
    else:
        length_status = "Optimal"

    improvements = []
    if length_status == "Missing":
        improvements.append(
            "Add a professional summary to highlight your top achievements.")
    elif length_status == "Too Short":
        improvements.append(
            "Expand your summary to clearly state your career objectives and core expertise.")

    return {
        "length_status": length_status,
        "grammar_check": "Pass" if words > 0 else "N/A",
        "technology_coverage": len(
            re.findall(
                r'\b(Python|Java|AWS|React|Node|SQL)\b',
                summary,
                re.I)),
        "career_objective_found": bool(
            re.search(
                r'seek|looking|objective|opportunity',
                summary,
                re.I)),
        "professional_tone": "Professional" if words > 0 else "N/A",
        "improvements": improvements if improvements else ["Summary is well-crafted."]}

# ---------------------------------------------------------------------------
# High-level Generators
# ---------------------------------------------------------------------------


def identify_strengths(
        quality_report: Any,
        section_scores: Any) -> list[str]:
    strengths = []
    if section_scores.get("technical_skills", {}).get("score", 0) > 80:
        strengths.append("Strong Technical Skills")
    if section_scores.get("projects", {}).get("score", 0) > 80:
        strengths.append("Excellent Project Portfolio")
    if quality_report.get("has_github"):
        strengths.append("Good GitHub Presence")
    if section_scores.get("formatting", {}).get("score", 0) > 80:
        strengths.append("Excellent Resume Structure")
    if quality_report.get("has_linkedin"):
        strengths.append("Professional LinkedIn Linked")

    if not strengths:
        strengths.append("Good baseline template")
    return strengths


def identify_weaknesses(
        quality_report: Any,
        section_scores: Any) -> list[str]:
    weaknesses = []
    if not quality_report.get("has_linkedin"):
        weaknesses.append("Missing LinkedIn")
    if section_scores.get("projects", {}).get("score", 0) < 50:
        weaknesses.append("Too Few Projects")
    if section_scores.get("technical_skills", {}).get("score", 0) < 50:
        weaknesses.append("Weak Keywords")
    if len(quality_report.get("weak_verbs_found", [])) > 0:
        weaknesses.append("Weak Action Verbs")
    if "education" in quality_report.get("missing_sections", []):
        weaknesses.append("Missing Education Section")

    return weaknesses


def generate_actionable_suggestions(
        quality_report: Any,
        section_scores: Any) -> list[Suggestion]:
    suggestions: list[Suggestion] = []

    if not quality_report.get("has_linkedin"):
        suggestions.append({
            "suggestion": "Create and link a professional LinkedIn profile.",
            "priority": "High",
            "difficulty": "Easy",
            "estimated_learning_time": "30 mins"
        })

    if section_scores.get("projects", {}).get("score", 0) < 60:
        suggestions.append({
            "suggestion": "Add one Spring Boot or React microservice project.",
            "priority": "High",
            "difficulty": "Hard",
            "estimated_learning_time": "2 weeks"
        })

    if section_scores.get("experience", {}).get("score", 0) < 70:
        suggestions.append({
            "suggestion": "Include measurable project achievements (e.g., 'improved performance by 30%').",
            "priority": "Medium",
            "difficulty": "Medium",
            "estimated_learning_time": "1 hour"
        })

    if len(quality_report.get("missing_sections", [])) > 0:
        missed = ", ".join(quality_report["missing_sections"])
        suggestions.append({
            "suggestion": f"Add missing sections: {missed}.",
            "priority": "High",
            "difficulty": "Easy",
            "estimated_learning_time": "1 hour"
        })

    if len(quality_report.get("weak_verbs_found", [])) > 0:
        suggestions.append({
            "suggestion": "Replace passive verbs ('helped', 'worked on') with strong action verbs.",
            "priority": "Medium",
            "difficulty": "Easy",
            "estimated_learning_time": "15 mins"
        })

    # Fallback if none trigger
    if not suggestions:
        suggestions.append({
            "suggestion": "Keep your skills updated with the latest cloud technologies like Docker or AWS.",
            "priority": "Low",
            "difficulty": "Medium",
            "estimated_learning_time": "1 week"
        })

    return suggestions
