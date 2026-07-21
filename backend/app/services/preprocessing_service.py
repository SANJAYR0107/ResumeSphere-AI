"""
preprocessing_service.py  —  Phase 3 Text Preprocessing Service

Purpose
-------
Transform raw PDF-extracted text into a clean, normalised string suitable
for downstream NLP tasks (section detection, skill extraction, embedding).

This service sits immediately after PDF extraction in the pipeline.  Its
job is purely textual hygiene: it never interprets meaning, never classifies,
never extracts — it only cleans.

Responsibilities
----------------
1. Normalise Unicode to NFC form (composed form) so accented characters and
   ligatures are represented consistently.
2. Replace common typographic substitutions (curly quotes, em-dashes, etc.)
   with plain ASCII equivalents so later regex patterns stay simple.
3. Normalise bullet-point characters (•, ▪, ◦, ‣, ▸, ►, ➤, ✓, ✔, –, →)
   to a plain hyphen-space prefix for uniform list parsing.
4. Collapse horizontal whitespace runs (spaces / tabs) to a single space on
   each line.
5. Collapse three or more consecutive blank lines to a single blank line to
   preserve paragraph structure without excessive vertical spacing.
6. Strip leading and trailing whitespace from the final string.

Inputs
------
raw_text : str
    Text as returned by ``parser_service.extract_text_from_pdf``.

Outputs
-------
str
    Cleaned, normalised text.  The character count will usually be slightly
    smaller than the input due to whitespace collapsing.

Exceptions
----------
No exceptions are raised.  The function is designed to be defensive: if the
input is empty or None-like, it returns an empty string.

Complexity
----------
O(n) where n = len(raw_text).  Each regex pass is a single left-to-right scan.
All patterns are compiled at module level so there is zero per-call
compilation overhead.
"""

import logging
import re
import unicodedata

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Compiled regex patterns (module-level — compiled once, reused every call)
# ---------------------------------------------------------------------------

# Matches any run of horizontal whitespace (space, tab, non-breaking space,
# zero-width space, etc.) but NOT newlines — so line structure is preserved.
_RE_HSPACE: re.Pattern = re.compile(r"[^\S\n]+")

# Matches three or more consecutive newlines (with optional spaces between).
_RE_EXCESS_BLANK: re.Pattern = re.compile(r"\n(\s*\n){2,}")

# Matches a hyphen at the end of a line followed by a newline and optional
# spaces
_RE_HYPHENATED_NEWLINE: re.Pattern = re.compile(r"-\n\s*")

# Bullet-point characters commonly produced by PDF renderers, plus standard ascii ones
# Normalised to "- " (hyphen + space) for uniform downstream parsing.
_RE_BULLETS: re.Pattern = re.compile(
    r"^\s*(?:[•▪◦‣▸►➤✓✔→\*\+]|-(?!\w))\s*",
    re.MULTILINE,
)

# Email pattern — retained in the text but used later for candidate_name
# heuristic; not stripped here.

# ---------------------------------------------------------------------------
# Typographic substitution map
# ---------------------------------------------------------------------------

_TYPOGRAPHIC_MAP: dict[str, str] = {
    "\u2018": "'",   # LEFT SINGLE QUOTATION MARK
    "\u2019": "'",   # RIGHT SINGLE QUOTATION MARK
    "\u201A": "'",   # SINGLE LOW-9 QUOTATION MARK
    "\u201B": "'",   # SINGLE HIGH-REVERSED-9 QUOTATION MARK
    "\u201C": '"',   # LEFT DOUBLE QUOTATION MARK
    "\u201D": '"',   # RIGHT DOUBLE QUOTATION MARK
    "\u201E": '"',   # DOUBLE LOW-9 QUOTATION MARK
    "\u201F": '"',   # DOUBLE HIGH-REVERSED-9 QUOTATION MARK
    "\u2010": "-",   # HYPHEN
    "\u2011": "-",   # NON-BREAKING HYPHEN
    "\u2012": "-",   # FIGURE DASH
    "\u2013": "-",   # EN DASH
    "\u2014": "-",   # EM DASH
    "\u2015": "-",   # HORIZONTAL BAR
    "\u2026": "...",  # HORIZONTAL ELLIPSIS
    "\u00A0": " ",   # NON-BREAKING SPACE
    "\u2007": " ",   # FIGURE SPACE
    "\u202F": " ",   # NARROW NO-BREAK SPACE
    "\t": " ",       # TAB
    "\u200B": "",    # ZERO WIDTH SPACE
    "\u200C": "",    # ZERO WIDTH NON-JOINER
    "\u200D": "",    # ZERO WIDTH JOINER
    "\u200E": "",    # LEFT-TO-RIGHT MARK
    "\u200F": "",    # RIGHT-TO-LEFT MARK
    "\uFEFF": "",    # BYTE ORDER MARK
    "\u00AD": "",    # SOFT HYPHEN
    "\u2022": "-",   # BULLET
    "\u25E6": "-",   # WHITE BULLET
    "\u25AA": "-",   # BLACK SMALL SQUARE
    "\u25AB": "-",   # WHITE SMALL SQUARE
}

# Build a single translation table for O(n) substitution
_TRANS_TABLE = str.maketrans(_TYPOGRAPHIC_MAP)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def preprocess(raw_text: str) -> str:
    """Clean and normalise raw resume text for NLP processing.

    Parameters
    ----------
    raw_text : str
        Unprocessed text extracted from a PDF resume.

    Returns
    -------
    str
        Normalised, clean text suitable for section detection, skill
        extraction, and sentence embedding.
    """
    if not raw_text:
        return ""

    logger.debug("Preprocessing: input length=%d chars", len(raw_text))

    # ── Step 1: Unicode NFC normalisation ─────────────────────────────────
    # NFC decomposes then recomposes — turns ä (a + combining umlaut) into
    # the single precomposed character ä, and resolves ligatures like ﬁ→fi.
    text: str = unicodedata.normalize("NFC", raw_text)

    # ── Step 2: De-hyphenate words broken across lines ────────────────────
    text = _RE_HYPHENATED_NEWLINE.sub("", text)

    # ── Step 3: Typographic substitutions ─────────────────────────────────
    text = text.translate(_TRANS_TABLE)

    # ── Step 4: Normalise bullet characters to "- " ───────────────────────
    text = _RE_BULLETS.sub("- ", text)

    # ── Step 5: Collapse horizontal whitespace on each line ────────────────
    text = _RE_HSPACE.sub(" ", text)

    # ── Step 6: Collapse excess blank lines ────────────────────────────────
    text = _RE_EXCESS_BLANK.sub("\n\n", text)

    # ── Step 7: Strip overall leading/trailing whitespace ──────────────────
    text = text.strip()

    logger.debug("Preprocessing: output length=%d chars", len(text))
    return text
