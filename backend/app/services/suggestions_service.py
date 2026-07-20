"""
suggestions_service.py  —  Phase 4 Resume Suggestions Generator

Purpose
-------
Produce an ordered list of actionable, plain-English suggestions that tell
the candidate exactly how to improve their resume's ATS compatibility and
overall quality.

Strategy
--------
Pure rules-based analysis — no ML inference, zero latency overhead.
Suggestions are prioritised by estimated impact (high-impact items first).

Rules applied (in priority order)
----------------------------------
1.  Missing summary section          → add professional summary
2.  Missing experience section       → add work experience
3.  Thin experience section          → expand with quantified achievements
4.  Low skill count (< 8)            → add more technical skills
5.  Missing education section        → add education
6.  Missing projects section         → add projects
7.  Missing certifications           → add certifications
8.  Resume too short (< 300 words)   → increase length
9.  Resume too long (> 1 200 words)  → condense to 1–2 pages
10. Low keyword density              → list skills in dedicated section
11. Incomplete contact info          → add email / phone / LinkedIn
12. Very low overall ATS score       → tailor to job description

Inputs
------
sections      : dict[str, str]   — section_service output
skills        : list[str]        — skill names from skill_extractor_service
raw_text      : str              — preprocessed resume text
ats_breakdown : dict[str, int]   — ats_service breakdown dict

Outputs
-------
list[str]
    Actionable suggestion strings, ordered by estimated impact.
    May be empty if the resume is already comprehensive.

Exceptions
----------
No exceptions are raised.

Complexity
----------
O(1) — constant number of rule checks regardless of text length.
"""

import logging

logger = logging.getLogger(__name__)


def generate_suggestions(
    sections: dict[str, str],
    skills: list[str],
    raw_text: str,
    ats_breakdown: dict[str, int],
) -> list[str]:
    """Generate actionable improvement suggestions for a resume.

    Parameters
    ----------
    sections : dict[str, str]
        Detected section map from ``section_service.detect_sections()``.
    skills : list[str]
        Skill names extracted by ``skill_extractor_service``.
    raw_text : str
        Preprocessed resume text.
    ats_breakdown : dict[str, int]
        Per-category score breakdown from ``ats_service.compute_ats_score()``.

    Returns
    -------
    list[str]
        Ordered list of actionable suggestion strings.  May be empty if the
        resume already satisfies all heuristics.
    """
    suggestions: list[str] = []
    word_count: int = len(raw_text.split()) if raw_text else 0
    skill_count: int = len(skills)
    ats_total: int = sum(ats_breakdown.values())

    # ── High-impact rules ─────────────────────────────────────────────────

    if "summary" not in sections:
        suggestions.append(
            "Add a professional Summary section — a 3–5 sentence pitch highlighting "
            "your key strengths, years of experience, and career goals."
        )

    if "experience" not in sections:
        suggestions.append(
            "Add a Work Experience section listing your past roles, employers, "
            "dates, and key responsibilities."
        )
    elif len(sections.get("experience", "")) < 200:
        suggestions.append(
            "Expand your Experience section with quantified achievements "
            "(e.g. 'Reduced API latency by 35 %', 'Led a team of 6 engineers'). "
            "Numbers make bullet points 40 % more impactful."
        )

    if skill_count < 8:
        suggestions.append(
            f"Add more technical skills — only {skill_count} detected. "
            "ATS systems scan for keywords; aim for 12–20 relevant skills in a "
            "dedicated Skills section."
        )

    # ── Medium-impact rules ───────────────────────────────────────────────

    if "education" not in sections:
        suggestions.append(
            "Add an Education section with your degree, institution, major, "
            "and graduation year."
        )

    if "projects" not in sections:
        suggestions.append(
            "Add a Projects section to showcase hands-on work — include the "
            "tech stack and a one-line description of each project."
        )

    if "certifications" not in sections:
        suggestions.append(
            "Add relevant Certifications (e.g. AWS Solutions Architect, Google "
            "Cloud, PMP, Kubernetes) to significantly boost recruiter confidence."
        )

    # ── Resume length ─────────────────────────────────────────────────────

    if word_count < 300:
        suggestions.append(
            f"Your resume is too brief ({word_count} words). "
            "Aim for 400–600 words for entry-level positions or "
            "600–900 words for senior roles."
        )
    elif word_count > 1200:
        suggestions.append(
            f"Your resume is very long ({word_count} words). "
            "Condense it to 1–2 pages — recruiters spend an average of "
            "7 seconds on an initial scan."
        )

    # ── Keyword density ───────────────────────────────────────────────────

    if ats_breakdown.get("keyword_density", 5) < 3:
        suggestions.append(
            "Increase keyword density by listing your tools and technologies "
            "explicitly in a dedicated Skills section rather than burying them "
            "in prose."
        )

    # ── Contact information ───────────────────────────────────────────────

    if ats_breakdown.get("contact_info", 10) < 6:
        suggestions.append(
            "Ensure your contact information is complete: professional email "
            "address, phone number, and your LinkedIn profile URL."
        )

    # ── Overall ATS score ─────────────────────────────────────────────────

    if ats_total < 55:
        suggestions.append(
            "Overall ATS compatibility is low. Tailor your resume to the specific "
            "job description you are applying for — mirror keywords from the posting "
            "for significantly better pass rates."
        )

    logger.info(
        "suggestions_service: generated %d suggestion(s) "
        "(ats=%d, skills=%d, words=%d)",
        len(suggestions),
        ats_total,
        skill_count,
        word_count,
    )

    return suggestions
