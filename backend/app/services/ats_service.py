"""
ats_service.py  —  Phase 4 ATS Scoring Engine

Purpose
-------
Compute a rules-based ATS (Applicant Tracking System) compatibility score
for a preprocessed resume, broken down into nine weighted categories.

Scoring Rubric (100 points total)
----------------------------------
  Category           Max Pts  Signal
  -----------------  -------  --------------------------------------------------
  contact_info          10    email, phone, and/or LinkedIn detected in text
  summary               10    "summary" section detected
  experience            15    "experience" section detected + content length
  education             10    "education" section detected
  skills                15    skill count scaled to 15 skills = full score
  projects              10    "projects" section detected
  certifications        10    "certifications" section detected
  resume_length          5    word count in optimal range (300–700 words)
  keyword_density       10    unique skill count / word count ratio
  formatting             5    use of bullet points and clear sections

Total                  100

Inputs
------
sections     : dict[str, str]   — output of section_service.detect_sections()
skills       : list[str]        — skill names from skill_extractor_service
raw_text     : str              — preprocessed resume text

Outputs
-------
dict
    {"ats_score": int, "breakdown": dict[str, int]}
    ``ats_score`` is the sum of all breakdown values (0–100).

Exceptions
----------
No exceptions are raised.  All inputs are validated defensively.

Complexity
----------
O(T) where T = len(raw_text) — one pass each for regex checks and word split.
"""

import logging
import re

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Compiled patterns for contact-information detection
# ---------------------------------------------------------------------------

_RE_EMAIL: re.Pattern = re.compile(
    r"[\w.+-]+@[\w-]+\.[a-zA-Z]{2,}",
)
_RE_PHONE: re.Pattern = re.compile(
    r"(\+?[\d][\d\s\-()+]{6,}\d)",
)
_RE_LINKEDIN: re.Pattern = re.compile(
    r"linkedin\.com",
    re.IGNORECASE,
)

# ---------------------------------------------------------------------------
# Scoring thresholds
# ---------------------------------------------------------------------------

# Skill count that earns the full 20 skill points
_SKILLS_FULL_THRESHOLD: int = 15

# Word-count range that earns full resume-length points
_LENGTH_OPTIMAL_LOW: int = 300
_LENGTH_OPTIMAL_HIGH: int = 700
_LENGTH_ACCEPTABLE_LOW: int = 200
_LENGTH_ACCEPTABLE_HIGH: int = 1200

# Keyword-density thresholds (skills per 100 words)
_DENSITY_HIGH: float = 3.0
_DENSITY_MED: float = 1.5


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def compute_ats_score(
    sections: dict[str, str],
    skills: list[str],
    raw_text: str,
) -> dict:
    """Compute an ATS compatibility score with a per-category breakdown.

    Parameters
    ----------
    sections : dict[str, str]
        Section map produced by ``section_service.detect_sections()``.
    skills : list[str]
        Canonical skill names produced by ``skill_extractor_service``.
    raw_text : str
        Preprocessed resume text (output of ``preprocessing_service``).

    Returns
    -------
    dict
        ``{"ats_score": int, "breakdown": dict[str, int]}``
        The ``ats_score`` is the sum of all values in ``breakdown`` and lies
        in the range [0, 100].
    """
    breakdown: dict[str, int] = {}

    # ── 1. Contact Information (10 pts) ───────────────────────────────────
    contact: int = 0
    if _RE_EMAIL.search(raw_text):
        contact += 4
    if _RE_PHONE.search(raw_text):
        contact += 4
    if _RE_LINKEDIN.search(raw_text):
        contact += 2
    breakdown["contact_info"] = min(contact, 10)

    # ── 2. Summary (10 pts) ───────────────────────────────────────────────
    breakdown["summary"] = 10 if "summary" in sections else 0

    # ── 3. Experience (15 pts) ────────────────────────────────────────────
    if "experience" in sections:
        exp_len = len(sections["experience"])
        if exp_len >= 400:
            breakdown["experience"] = 15
        elif exp_len >= 200:
            breakdown["experience"] = 10
        else:
            breakdown["experience"] = 5
    else:
        breakdown["experience"] = 0

    # ── 4. Education (10 pts) ─────────────────────────────────────────────
    breakdown["education"] = 10 if "education" in sections else 0

    # ── 5. Skills (15 pts) — linear scale, capped at _SKILLS_FULL_THRESHOLD
    skill_count = len(skills)
    raw_skills_pts = int(skill_count / _SKILLS_FULL_THRESHOLD * 15)
    breakdown["skills"] = min(raw_skills_pts, 15)

    # ── 6. Projects (10 pts) ──────────────────────────────────────────────
    breakdown["projects"] = 10 if "projects" in sections else 0

    # ── 7. Certifications (10 pts) ────────────────────────────────────────
    breakdown["certifications"] = 10 if "certifications" in sections else 0

    # ── 8. Resume Length (5 pts) ──────────────────────────────────────────
    word_count = len(raw_text.split()) if raw_text else 0
    if _LENGTH_OPTIMAL_LOW <= word_count <= _LENGTH_OPTIMAL_HIGH:
        breakdown["resume_length"] = 5
    elif (
        _LENGTH_ACCEPTABLE_LOW <= word_count < _LENGTH_OPTIMAL_LOW
        or _LENGTH_OPTIMAL_HIGH < word_count <= _LENGTH_ACCEPTABLE_HIGH
    ):
        breakdown["resume_length"] = 3
    elif word_count > 0:
        breakdown["resume_length"] = 1
    else:
        breakdown["resume_length"] = 0

    # ── 9. Keyword Density (10 pts) — unique skills per 100 words ──────────
    if word_count > 0:
        density = skill_count / word_count * 100
        if density >= _DENSITY_HIGH:
            breakdown["keyword_density"] = 10
        elif density >= _DENSITY_MED:
            breakdown["keyword_density"] = 5
        else:
            breakdown["keyword_density"] = 2
    else:
        breakdown["keyword_density"] = 0

    # ── 10. Formatting (5 pts) ────────────────────────────────────────────
    formatting_pts: int = 0
    # Check for bullet points
    if re.search(r"^[ \t]*[•\-\*]", raw_text, re.MULTILINE):
        formatting_pts += 3
    # Check if a decent number of distinct sections were detected
    if len(sections) >= 3:
        formatting_pts += 2
    breakdown["formatting"] = formatting_pts

    ats_score: int = sum(breakdown.values())

    logger.info(
        "ats_service: score=%d  skills=%d  words=%d  sections=%s",
        ats_score,
        skill_count,
        word_count,
        sorted(sections.keys()),
    )

    return {
        "ats_score": ats_score,
        "breakdown": breakdown,
    }
