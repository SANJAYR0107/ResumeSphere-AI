"""
ats_service.py  —  Phase 4 Advanced ATS Scoring Engine

Purpose
-------
Compute an explainable, weighted ATS compatibility score for a preprocessed resume.

Evaluates:
Contact Information, Professional Summary, Technical Skills, Experience, Projects, 
Education, Certifications, Achievements (metrics like 20%, 3x), Formatting, Grammar, 
Keywords, Resume Length, Action Verbs, LinkedIn, GitHub, Portfolio.
"""

import logging
import re
from typing import Any
from typing_extensions import TypedDict

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class AtsCategoryBreakdown(TypedDict):
    score: int
    weight: float
    reason: str
    improvement: str

class AtsScoreResult(TypedDict):
    ats_score: int
    ats_grade: str
    hiring_probability: str
    resume_strength_index: float
    recruiter_confidence: str
    breakdown: dict[str, AtsCategoryBreakdown]

# ---------------------------------------------------------------------------
# Compiled patterns
# ---------------------------------------------------------------------------

_RE_EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[a-zA-Z]{2,}")
_RE_PHONE = re.compile(r"(\+?[\d][\d\s\-()+]{6,}\d)")
_RE_LINKEDIN = re.compile(r"linkedin\.com", re.IGNORECASE)
_RE_GITHUB = re.compile(r"github\.com", re.IGNORECASE)
_RE_PORTFOLIO = re.compile(r"(portfolio|my\s*website|personal\s*site|\.dev|\.io)", re.IGNORECASE)

_RE_METRICS = re.compile(r"\b\d+[%]?\b|\b\d+x\b", re.IGNORECASE)
_RE_ACTION_VERBS = re.compile(
    r"\b(spearheaded|architected|orchestrated|optimized|developed|engineered|designed|led|managed|increased|decreased|saved|generated|boosted)\b",
    re.IGNORECASE
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_grade(score: int) -> str:
    if score >= 95: return "A+"
    if score >= 90: return "A"
    if score >= 85: return "B+"
    if score >= 80: return "B"
    if score >= 70: return "C"
    if score >= 60: return "D"
    return "F"

def _get_hiring_prob(score: int) -> str:
    if score >= 90: return "Excellent (Top 5%)"
    if score >= 80: return "Strong (Top 20%)"
    if score >= 70: return "Average"
    return "Low"

def _get_confidence(score: int) -> str:
    if score >= 90: return "Very High"
    if score >= 80: return "High"
    if score >= 65: return "Moderate"
    return "Low"

# ---------------------------------------------------------------------------
# Configurable ATS Weights
# ---------------------------------------------------------------------------

ATS_WEIGHTS = {
    "contact_info": 0.05,
    "summary": 0.05,
    "technical_skills": 0.15,
    "experience": 0.20,
    "projects": 0.10,
    "education": 0.05,
    "achievements": 0.10,
    "action_verbs": 0.05,
    "formatting_grammar": 0.05,
    "external_links": 0.05,
    "keyword_density": 0.05,
    "resume_length": 0.05
}

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def compute_ats_score(
    sections: dict[str, str],
    skills: list[str],
    raw_text: str,
    quality_report: Any = None
) -> AtsScoreResult:
    """Compute an advanced ATS compatibility score with a highly detailed weighted breakdown."""
    if quality_report is None:
        quality_report = {}
        
    breakdown: dict[str, AtsCategoryBreakdown] = {}
    
    total_score = 0.0
    
    # helper for creating breakdown entries
    def add_category(name: str, score: int, reason: str, improvement: str):
        nonlocal total_score
        capped_score = min(100, max(0, score))
        weight = ATS_WEIGHTS.get(name, 0.0)
        breakdown[name] = {
            "score": capped_score,
            "weight": weight,
            "reason": reason,
            "improvement": improvement
        }
        total_score += (capped_score * weight)

    word_count = len(raw_text.split()) if raw_text else 0

    # 1. Contact Information (Weight: 0.05)
    contact_score = 0
    c_reason = []
    if _RE_EMAIL.search(raw_text):
        contact_score += 40
        c_reason.append("Email")
    if _RE_PHONE.search(raw_text):
        contact_score += 40
        c_reason.append("Phone")
    if _RE_LINKEDIN.search(raw_text):
        contact_score += 20
        c_reason.append("LinkedIn")
    
    add_category(
        "contact_info", 
        contact_score, 
        f"Found: {', '.join(c_reason)}." if c_reason else "Missing standard contact details.",
        "Add an email, phone number, and LinkedIn profile to ensure recruiters can contact you." if contact_score < 100 else "Contact info is perfectly formatted."
    )

    # 2. Professional Summary (Weight: 0.05)
    has_summary = "summary" in sections
    add_category(
        "summary",
        100 if has_summary else 0,
        "Professional summary section detected." if has_summary else "Missing professional summary.",
        "Ensure your summary is 3-4 lines highlighting your core expertise and career objectives." if has_summary else "Add a 'Summary' section at the top of your resume."
    )

    # 3. Technical Skills (Weight: 0.15)
    skill_count = len(skills)
    skill_score = min(100, skill_count * 6)
    add_category(
        "technical_skills",
        skill_score,
        f"Detected {skill_count} relevant technical skills.",
        "Add more modern frameworks and programming languages." if skill_score < 90 else "Strong technical skill presence."
    )

    # 4. Experience (Weight: 0.20)
    exp_text = sections.get("experience", "")
    exp_len = len(exp_text)
    exp_score = min(100, int((exp_len / 800) * 100)) if exp_len > 0 else 0
    add_category(
        "experience",
        exp_score,
        "Experience section is highly detailed." if exp_score > 80 else "Experience section lacks sufficient detail.",
        "Use the STAR method (Situation, Task, Action, Result) to expand your bullet points." if exp_score < 80 else "Excellent experience detailing."
    )

    # 5. Projects (Weight: 0.10)
    proj_text = sections.get("projects", "")
    proj_len = len(proj_text)
    proj_score = min(100, int((proj_len / 500) * 100)) if proj_len > 0 else 0
    add_category(
        "projects",
        proj_score,
        "Project section indicates strong detail." if proj_score > 70 else "Project section is light or missing.",
        "Add personal or academic projects to demonstrate hands-on experience." if proj_score < 80 else "Projects are well described."
    )

    # 6. Education (Weight: 0.05)
    has_edu = "education" in sections
    add_category(
        "education",
        100 if has_edu else 0,
        "Education section present." if has_edu else "No education section found.",
        "Education is properly structured." if has_edu else "Add an Education section listing your degrees."
    )

    # 7. Achievements / Metrics (Weight: 0.10)
    metrics_count = len(_RE_METRICS.findall(raw_text))
    metrics_score = min(100, metrics_count * 15)
    add_category(
        "achievements",
        metrics_score,
        f"Found {metrics_count} quantified metric(s) (e.g. %, numbers).",
        "Quantify your impact using numbers, percentages, and timeframes (e.g., 'reduced latency by 40%')." if metrics_score < 75 else "Excellent use of metrics to prove impact."
    )

    # 8. Action Verbs (Weight: 0.05)
    verbs_count = len(_RE_ACTION_VERBS.findall(raw_text))
    verbs_score = min(100, verbs_count * 20)
    add_category(
        "action_verbs",
        verbs_score,
        f"Detected {verbs_count} strong action verbs.",
        "Replace weak verbs (like 'helped' or 'worked on') with strong verbs (like 'spearheaded' or 'architected')." if verbs_score < 80 else "Strong, professional vocabulary."
    )

    # 9. Formatting & Grammar (Weight: 0.05)
    grammar_issues = len(quality_report.get("grammar_issues", []))
    fmt_score = 100
    if not re.search(r"^[ \t]*[•\-\*]", raw_text, re.MULTILINE):
        fmt_score -= 30
    if len(sections) < 3:
        fmt_score -= 20
    fmt_score -= (grammar_issues * 10)
    
    add_category(
        "formatting_grammar",
        fmt_score,
        "Good bullet structures and minimal grammar issues." if fmt_score > 80 else "Layout lacks standard bullet points or has grammar errors.",
        "Ensure standard bullet points are used and thoroughly proofread the document." if fmt_score < 80 else "Formatting and grammar are solid."
    )

    # 10. External Links (Weight: 0.05)
    links_score = 0
    l_reason = []
    if _RE_GITHUB.search(raw_text):
        links_score += 50
        l_reason.append("GitHub")
    if _RE_PORTFOLIO.search(raw_text):
        links_score += 50
        l_reason.append("Portfolio")
    
    add_category(
        "external_links",
        links_score,
        f"Found: {', '.join(l_reason)}." if l_reason else "No GitHub or Portfolio links detected.",
        "Add a link to your GitHub profile or personal portfolio to showcase your code." if links_score < 100 else "Excellent external technical presence."
    )

    # 11. Keyword Density (Weight: 0.05)
    kw_score = 0
    if word_count > 0:
        density = (skill_count / word_count) * 100
        if density >= 3.0: kw_score = 100
        elif density >= 1.5: kw_score = 75
        else: kw_score = 40
        
    add_category(
        "keyword_density",
        kw_score,
        "High keyword density relative to word count." if kw_score > 70 else "Low keyword density.",
        "Sprinkle more industry-standard keywords throughout your experience bullet points." if kw_score < 80 else "Keywords are well balanced."
    )

    # 12. Resume Length (Weight: 0.05)
    len_score = 0
    if 300 <= word_count <= 800:
        len_score = 100
    elif 200 <= word_count < 300 or 800 < word_count <= 1200:
        len_score = 60
    elif word_count > 0:
        len_score = 20

    add_category(
        "resume_length",
        len_score,
        f"Resume length is {word_count} words.",
        "Aim for a sweet spot of 400-700 words (usually 1-2 pages)." if len_score < 100 else "Resume length is optimal."
    )

    final_ats_score = int(round(total_score))
    
    logger.info(f"ats_service: Final ATS Score = {final_ats_score}/100")

    return {
        "ats_score": final_ats_score,
        "ats_grade": _get_grade(final_ats_score),
        "hiring_probability": _get_hiring_prob(final_ats_score),
        "resume_strength_index": round(total_score / 10.0, 1),
        "recruiter_confidence": _get_confidence(final_ats_score),
        "breakdown": breakdown
    }
