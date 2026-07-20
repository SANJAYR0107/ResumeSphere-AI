"""
skill_extractor_service.py  —  Phase 3 Skill Extraction Service

Purpose
-------
Identify technical skills mentioned in a resume by matching against a
configurable skills taxonomy loaded from ``datasets/skills.csv``.

Strategy
--------
1. Load the CSV once at module import time (zero per-request I/O).
2. Build a single compiled ``re.Pattern`` that is the union of all skill
   names, each anchored with word boundaries (``\\b``) and case-insensitive.
   This gives O(n) matching across the entire text in one pass.
3. Scan the preprocessed resume text for all matches.
4. Deduplicate, sort alphabetically, and return with a confidence score.

Confidence scoring
------------------
Confidence is defined as the frequency of a skill's occurrence normalised
by the maximum occurrence count across all matched skills.  A skill that
appears 5 times when the most-frequent skill appears 10 times gets a
confidence of 0.5.  Single-occurrence skills get confidence = 1.0 / max_count.
This is a proxy for emphasis/importance, not a statistical probability.

Skills dataset format
---------------------
The CSV at ``SKILLS_CSV_PATH`` must have exactly two columns:
  skill    — canonical skill name (case-preserved for display)
  category — taxonomy category (Programming, Cloud, etc.)

CSV files with a header row are supported; BOM-free UTF-8 encoding expected.

Inputs
------
text : str
    Preprocessed resume text (output of ``preprocessing_service.preprocess``).

Outputs
-------
list[SkillMatch]
    Sorted alphabetically by skill name.  Each entry is a TypedDict with:
      ``skill``      (str)   — canonical skill name
      ``category``   (str)   — taxonomy category
      ``confidence`` (float) — normalised occurrence score in [0.0, 1.0]

Exceptions
----------
FileNotFoundError
    Raised at import time if ``SKILLS_CSV_PATH`` does not exist.
ValueError
    Raised at import time if the CSV has missing or malformed rows.

Complexity
----------
Import: O(S log S) where S = number of skills (for sorting the pattern)
Per call: O(T) where T = len(text) — a single regex scan of the full text.
"""

import csv
import logging
import re
from typing import TypedDict

from backend.app.config import SKILLS_CSV_PATH

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Data Types
# ---------------------------------------------------------------------------

class SkillMatch(TypedDict):
    """A single matched skill with its taxonomy category and confidence."""
    skill: str
    category: str
    confidence: float


# ---------------------------------------------------------------------------
# Module-level initialisation — runs once at application startup
# ---------------------------------------------------------------------------

class _SkillsDatabase:
    """Internal container for the skills taxonomy.

    Loaded once from CSV.  Not exported — use the module-level functions.
    """

    def __init__(self, csv_path) -> None:
        self.skills: dict[str, str] = {}          # skill_lower → category
        self.canonical: dict[str, str] = {}       # skill_lower → display name
        self._load(csv_path)
        self.pattern: re.Pattern = self._build_pattern()

    def _load(self, csv_path) -> None:
        """Parse the skills CSV into internal lookup dictionaries."""
        from pathlib import Path
        path = Path(csv_path)
        if not path.exists():
            raise FileNotFoundError(
                f"Skills CSV not found at '{path}'. "
                "Ensure datasets/skills.csv exists."
            )

        with path.open(encoding="utf-8-sig") as fh:
            reader = csv.DictReader(fh)
            if reader.fieldnames is None or not {"skill", "category"}.issubset(
                set(reader.fieldnames)
            ):
                raise ValueError(
                    f"skills.csv must have columns 'skill' and 'category'. "
                    f"Found: {reader.fieldnames}"
                )
            for row_num, row in enumerate(reader, start=2):  # 2 = first data row
                skill = (row.get("skill") or "").strip()
                category = (row.get("category") or "").strip()
                if not skill or not category:
                    logger.warning(
                        "skills.csv row %d is incomplete (skill=%r, category=%r) — skipped",
                        row_num,
                        skill,
                        category,
                    )
                    continue
                key = skill.lower()
                self.skills[key] = category
                self.canonical[key] = skill

        logger.info(
            "skill_extractor: loaded %d skills from '%s'",
            len(self.skills),
            path.name,
        )

    def _build_pattern(self) -> re.Pattern:
        """Build a single compiled union regex from all skill names.

        Longer skills are sorted first to prevent shorter sub-matches
        shadowing them (e.g. "Node.js" before "Node").
        """
        # Sort by descending length so longer phrases are tried first
        sorted_skills = sorted(self.skills.keys(), key=len, reverse=True)

        # Escape each skill name so dots, pluses etc. are literal
        escaped = [re.escape(s) for s in sorted_skills]

        # Wrap in word boundaries.  Use (?<!\w) / (?!\w) instead of \b
        # because \b fails on names starting/ending with non-word chars
        # like "C++" or ".NET".
        pattern_str = r"(?<!\w)(" + "|".join(escaped) + r")(?!\w)"
        return re.compile(pattern_str, re.IGNORECASE)


# Singleton — loaded once when the module is first imported
_db: _SkillsDatabase = _SkillsDatabase(SKILLS_CSV_PATH)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def extract_skills(text: str) -> list[SkillMatch]:
    """Identify and return all technical skills present in the resume text.

    Parameters
    ----------
    text : str
        Preprocessed resume text (output of
        ``preprocessing_service.preprocess``).

    Returns
    -------
    list[SkillMatch]
        Deduplicated, alphabetically sorted list of matched skills, each
        with its taxonomy category and a normalised confidence score.
    """
    if not text:
        return []

    # Single-pass regex scan — returns all non-overlapping matches
    matches: list[re.Match] = list(_db.pattern.finditer(text))

    if not matches:
        logger.info("skill_extractor: no skills detected in text")
        return []

    # Count occurrences per skill (case-normalised)
    frequency: dict[str, int] = {}
    for m in matches:
        key = m.group(0).lower()
        frequency[key] = frequency.get(key, 0) + 1

    max_count: int = max(frequency.values())

    # Build result list — one entry per unique skill
    result: list[SkillMatch] = []
    for key, count in frequency.items():
        canonical_name = _db.canonical.get(key, key.title())
        category = _db.skills.get(key, "Unknown")
        confidence = round(count / max_count, 4)
        result.append(
            SkillMatch(
                skill=canonical_name,
                category=category,
                confidence=confidence,
            )
        )

    # Sort alphabetically by skill name (case-insensitive)
    result.sort(key=lambda x: x["skill"].lower())

    logger.info(
        "skill_extractor: matched %d unique skill(s) from %d raw occurrence(s)",
        len(result),
        len(matches),
    )
    return result


def get_skill_names(text: str) -> list[str]:
    """Convenience wrapper that returns only skill name strings.

    Parameters
    ----------
    text : str
        Preprocessed resume text.

    Returns
    -------
    list[str]
        Alphabetically sorted skill names.
    """
    return [m["skill"] for m in extract_skills(text)]


def get_loaded_skill_count() -> int:
    """Return the number of skills loaded from the taxonomy CSV.

    Useful for health-check endpoints and test assertions.

    Returns
    -------
    int
        Total number of unique skills in the database.
    """
    return len(_db.skills)
