"""
section_service.py  —  Phase 3 Resume Section Detection Service

Purpose
-------
Split a preprocessed resume string into semantically labelled sections
(Summary, Experience, Education, Skills, etc.) so downstream NLP stages
can operate on targeted text rather than the entire document.

Strategy
--------
Resume sections are universally delimited by a heading line — a short line
that is either:
  • ALL CAPS (e.g. "WORK EXPERIENCE"), or
  • Title Case followed by an optional colon (e.g. "Education:", "Skills")

We maintain a priority-ordered list of compiled heading patterns, one per
logical section.  The detector scans the text line-by-line and, whenever a
line matches a heading, starts collecting its content into that section's
bucket until the next heading is encountered.

Supported sections (canonical key → display heading)
-----------------------------------------------------
  summary         | PROFESSIONAL SUMMARY / CAREER SUMMARY / PROFILE / OBJECTIVE / ABOUT ME
  experience      | WORK EXPERIENCE / PROFESSIONAL EXPERIENCE / EMPLOYMENT
  education       | EDUCATION / ACADEMIC BACKGROUND
  skills          | SKILLS / TECHNICAL SKILLS / CORE SKILLS / KEY SKILLS /
                  | TECHNOLOGIES / TECHNOLOGY STACK / TECHNICAL EXPERTISE
  projects        | PROJECTS / PERSONAL PROJECTS / ACADEMIC PROJECTS
  certifications  | CERTIFICATIONS / LICENSES / CREDENTIALS
  achievements    | ACHIEVEMENTS / AWARDS / HONORS
  languages       | LANGUAGES / LANGUAGE PROFICIENCY
  publications    | PUBLICATIONS / RESEARCH
  internships     | INTERNSHIPS / TRAINING
  volunteer       | VOLUNTEER / COMMUNITY SERVICE
  other           | (catch-all for unrecognised headings)

Inputs
------
text : str
    Preprocessed resume text (output of ``preprocessing_service.preprocess``).

Outputs
-------
dict[str, str]
    Mapping of section_key → section_text.  Sections not present in the
    resume will not appear in the dictionary.  An ``other`` key captures
    any content before the first heading and any unrecognised sections.

Exceptions
----------
No exceptions are raised.  An empty input returns an empty dict.

Complexity
----------
O(L × H) where L = number of lines, H = number of heading patterns (fixed at
12).  In practice this is effectively O(L).
"""

import logging
import re

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Section taxonomy — ordered from most specific to least specific
# ---------------------------------------------------------------------------
# Each entry is (canonical_key, compiled_regex).
# The regex matches a heading line case-insensitively.
# Patterns use word boundaries to avoid partial matches (e.g. "skills" inside
# "soft skills" matching the skills section unintentionally).
# ---------------------------------------------------------------------------

_SECTION_PATTERNS: list[tuple[str, re.Pattern]] = [
    (
        "contact",
        re.compile(
            r"^\s*(?:contact(?:\s+(?:info|information|details))?|personal\s+(?:info|information|details)|get\s+in\s+touch)\s*$",
            re.IGNORECASE,
        ),
    ),
    (
        "summary",
        re.compile(
            r"^\s*(?:professional\s+summary|career\s+summary|summary|profile"
            r"|objective|about\s+me|career\s+objective|career\s+profile"
            r"|personal\s+statement)\s*$",
            re.IGNORECASE,
        ),
    ),
    (
        "experience",
        re.compile(
            r"^\s*(?:work\s+experience|professional\s+experience|relevant\s+experience"
            r"|employment(?:\s+history)?|work\s+history|experience|history|career\s+history)\s*$",
            re.IGNORECASE,
        ),
    ),
    (
        "education",
        re.compile(
            r"^\s*(?:education(?:al\s+background)?|academic\s+(?:background|qualifications?|history)"
            r"|qualifications?|degrees?|academics)\s*$",
            re.IGNORECASE,
        ),
    ),
    (
        "skills",
        re.compile(
            r"^\s*(?:technical\s+skills?|core\s+skills?|key\s+skills?"
            r"|professional\s+skills?|skills?|my\s+skills|skill\s+set"
            r"|technical\s+expertise|technology\s+stack|tech\s+stack"
            r"|technologies|core\s+competenc(?:y|ies)|competenc(?:y|ies)|expertise)\s*$",
            re.IGNORECASE,
        ),
    ),
    (
        "projects",
        re.compile(
            r"^\s*(?:personal\s+|academic\s+|key\s+|notable\s+|side\s+)?(?:projects?|project\s+experience)\s*$",
            re.IGNORECASE,
        ),
    ),
    (
        "certifications",
        re.compile(
            r"^\s*(?:certifications?|certificates?|licenses?|credentials?|accreditations?)\s*$",
            re.IGNORECASE,
        ),
    ),
    (
        "achievements",
        re.compile(
            r"^\s*(?:achievements?|awards?|honors?|honours?|accomplishments?|recognition)\s*$",
            re.IGNORECASE,
        ),
    ),
    (
        "languages",
        re.compile(
            r"^\s*(?:languages?(?:\s+proficiency)?|linguistic\s+skills?)\s*$",
            re.IGNORECASE,
        ),
    ),
    (
        "publications",
        re.compile(
            r"^\s*(?:publications?|research(?:\s+(?:papers?|publications?|experience))?|patents?|papers?)\s*$",
            re.IGNORECASE,
        ),
    ),
    (
        "internships",
        re.compile(
            r"^\s*(?:internships?|trainings?|apprenticeships?)\s*$",
            re.IGNORECASE,
        ),
    ),
    (
        "volunteer",
        re.compile(
            r"^\s*(?:volunteer(?:ing)?(?:\s+(?:experience|work|service))?"
            r"|community\s+service|social\s+work)\s*$",
            re.IGNORECASE,
        ),
    ),
    (
        "leadership",
        re.compile(
            r"^\s*(?:leadership(?:\s+(?:experience|roles?))?|extracurriculars?|activities)\s*$",
            re.IGNORECASE,
        ),
    ),
    (
        "hobbies",
        re.compile(
            r"^\s*(?:hobbies|interests|pastimes)\s*$",
            re.IGNORECASE,
        ),
    ),
]

# A heading line is short (≤ 80 chars), not a sentence (no period at the end
# of the cleaned version), and matches at least one section pattern above.
# This guard prevents false positives on regular paragraph text.
_MAX_HEADING_LENGTH: int = 80


def _is_heading_line(line: str) -> bool:
    """Return True if the line looks like a section heading.

    A heading must be:
    - Non-empty after stripping punctuation/whitespace
    - ≤ 80 characters (headings are short)
    - Matches at least one known section pattern (case-insensitive, full-line)

    Parameters
    ----------
    line : str
        A single line from the resume text.

    Returns
    -------
    bool
    """
    stripped = line.strip().rstrip(":").strip()
    if not stripped or len(stripped) > _MAX_HEADING_LENGTH:
        return False
    return any(pat.search(stripped) for _, pat in _SECTION_PATTERNS)


def _classify_heading(line: str) -> str:
    """Return the canonical section key for a heading line.

    Parameters
    ----------
    line : str
        A line confirmed to be a section heading.

    Returns
    -------
    str
        One of the canonical section keys, or ``"other"`` if no pattern
        matches (should not happen if ``_is_heading_line`` returned True).
    """
    stripped = line.strip().rstrip(":").strip()
    for key, pat in _SECTION_PATTERNS:
        if pat.search(stripped):
            return key
    return "other"


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def detect_sections(text: str) -> dict[str, str]:
    """Split preprocessed resume text into labelled sections.

    Parameters
    ----------
    text : str
        Preprocessed resume text (output of
        ``preprocessing_service.preprocess``).

    Returns
    -------
    dict[str, str]
        ``{section_key: section_text}`` mapping.  Only sections that are
        actually present in the resume are included.  Content before the
        first recognisable heading is stored under ``"other"``.

    Examples
    --------
    >>> sections = detect_sections(resume_text)
    >>> print(sections.get("experience", ""))
    """
    if not text:
        logger.warning(
            "section_service: received empty text; returning empty dict")
        return {}

    lines: list[str] = text.splitlines()
    sections: dict[str, str] = {}
    current_key: str = "other"
    current_lines: list[str] = []

    for line in lines:
        if _is_heading_line(line):
            # Flush previous section buffer
            if current_lines:
                content = "\n".join(current_lines).strip()
                if content:
                    if current_key in sections:
                        sections[current_key] += "\n" + content
                    else:
                        sections[current_key] = content
            current_key = _classify_heading(line)
            current_lines = []
        else:
            current_lines.append(line)

    # Flush the final buffer
    if current_lines:
        content = "\n".join(current_lines).strip()
        if content:
            if current_key in sections:
                sections[current_key] += "\n" + content
            else:
                sections[current_key] = content

    # Remove the "other" key if it contains only whitespace
    if sections.get("other", "").strip() == "":
        sections.pop("other", None)

    detected: list[str] = list(sections.keys())
    logger.info(
        "section_service: detected %d section(s): %s",
        len(detected),
        detected,
    )
    return dict(sections)
