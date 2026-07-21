"""
quality_service.py — Resume Quality Checks
"""

import re
from typing import TypedDict


class QualityReport(TypedDict):
    has_email: bool
    has_phone: bool
    has_linkedin: bool
    has_github: bool
    has_portfolio: bool
    missing_sections: list[str]
    word_count: int
    bullet_consistency: str
    action_verbs_found: list[str]
    weak_verbs_found: list[str]
    passive_language_found: list[str]
    grammar_issues: list[str]
    quality_score: int


_RE_EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[a-zA-Z]{2,}")
_RE_PHONE = re.compile(r"\+?\d[\d\s\-\(\)]{7,}\d")
_RE_LINKEDIN = re.compile(r"linkedin\.com/in/[a-zA-Z0-9_-]+", re.IGNORECASE)
_RE_GITHUB = re.compile(r"github\.com/[a-zA-Z0-9_-]+", re.IGNORECASE)
_RE_PORTFOLIO = re.compile(
    r"(portfolio|dribbble\.com|behance\.net|bitbucket|gitlab|medium\.com)",
    re.IGNORECASE)

WEAK_VERBS = {
    "helped",
    "worked",
    "did",
    "made",
    "responsible for",
    "handled",
    "assisted",
    "managed to"}
PASSIVE_LANGUAGE = {
    "was responsible for",
    "duties included",
    "served as",
    "was tasked with",
    "were responsible for",
    "hired to"}
ACTION_VERBS = {
    "developed",
    "led",
    "managed",
    "designed",
    "created",
    "built",
    "spearheaded",
    "architected",
    "implemented",
    "orchestrated",
    "optimized",
    "streamlined",
    "engineered"}


def analyze_quality(raw_text: str, sections: dict[str, str]) -> QualityReport:
    """Analyze the resume text and sections to generate a quality report."""
    word_count = len(raw_text.split())

    has_email = bool(_RE_EMAIL.search(raw_text))
    has_phone = bool(_RE_PHONE.search(raw_text))
    has_linkedin = bool(_RE_LINKEDIN.search(raw_text))
    has_github = bool(_RE_GITHUB.search(raw_text))
    has_portfolio = bool(_RE_PORTFOLIO.search(raw_text))

    expected_sections = [
        "summary",
        "education",
        "projects",
        "skills",
        "experience"]
    missing_sections = [
        sec for sec in expected_sections if sec not in sections]

    # Check optional sections presence (doesn't hurt score, but good for
    # reporting)
    optional_sections = ["certifications", "achievements", "volunteer"]

    raw_lower = raw_text.lower()
    weak_verbs_found = [
        verb for verb in WEAK_VERBS if re.search(
            r"\b" + verb + r"\b", raw_lower)]
    passive_language_found = [
        phrase for phrase in PASSIVE_LANGUAGE if phrase in raw_lower]
    action_verbs_found = [
        verb for verb in ACTION_VERBS if re.search(
            r"\b" + verb + r"\b", raw_lower)]

    # Check if multiple bullet types exist in raw text (before preprocessing removed them)
    # Since raw_text passed here might be preprocessed, we assume preprocessed text has normalized bullets to '- '
    # Wait, the pipeline passes clean_text to this service. We can't check original bullets from clean_text.
    # To be accurate, we'll just say 'Consistent' if we use the clean text since preprocessing normalizes them.
    # We will check if there are lingering strange bullets.
    strange_bullets = re.search(r"^\s*[•▪◦‣▸►➤✓✔→\*]", raw_text, re.MULTILINE)
    bullet_consistency = "Inconsistent" if strange_bullets else "Consistent"

    grammar_issues = []
    if word_count < 150:
        grammar_issues.append(
            "Resume is too short, lacking detail (under 150 words).")
    elif word_count > 1000:
        grammar_issues.append(
            "Resume might be too long and wordy (over 1000 words).")

    # Basic rule-based grammar check: check for lowercase bullet points
    if re.search(r"^-\s+[a-z]", raw_text, re.MULTILINE):
        grammar_issues.append(
            "Some bullet points start with a lowercase letter.")

    # Check for excessive exclamation marks
    if "!!" in raw_text or "! " in raw_text:
        grammar_issues.append(
            "Avoid using exclamation marks in professional resumes.")

    score = 100
    if not has_email:
        score -= 10
    if not has_phone:
        score -= 10
    if not has_linkedin:
        score -= 10
    score -= (len(missing_sections) * 10)
    score -= (len(weak_verbs_found) * 5)
    score -= (len(passive_language_found) * 5)

    # Bonus for action verbs
    if action_verbs_found:
        score += min(10, len(action_verbs_found) * 2)

    if bullet_consistency == "Inconsistent":
        score -= 5

    score = max(0, min(100, score))

    return {
        "has_email": has_email,
        "has_phone": has_phone,
        "has_linkedin": has_linkedin,
        "has_github": has_github,
        "has_portfolio": has_portfolio,
        "missing_sections": missing_sections,
        "word_count": word_count,
        "bullet_consistency": bullet_consistency,
        "action_verbs_found": action_verbs_found,
        "weak_verbs_found": weak_verbs_found,
        "passive_language_found": passive_language_found,
        "grammar_issues": grammar_issues,
        "quality_score": score
    }
