"""
test_preprocessing.py — Unit tests for preprocessing_service.py

Test matrix covers:
  - Empty / whitespace-only input
  - Unicode NFC normalisation
  - Typographic character substitution (curly quotes, em-dash, etc.)
  - Bullet normalisation (•, ▪, ◦, ‣, ▸, ►, ➤, ✓, ✔, →)
  - Horizontal whitespace collapsing
  - Excessive blank line collapsing
  - Combination / real-world resume snippet
  - Large input (5000+ characters)
"""

import pytest

from backend.app.services.preprocessing_service import preprocess


class TestEmptyInput:
    """Boundary conditions: empty and whitespace-only strings."""

    def test_empty_string_returns_empty(self):
        assert preprocess("") == ""

    def test_whitespace_only_returns_empty(self):
        assert preprocess("   \n\n\t  ") == ""

    def test_none_like_falsy_returns_empty(self):
        # preprocess accepts str; passing an empty string is the contract
        assert preprocess("") == ""


class TestUnicodeNormalisation:
    """NFC normalisation and BOM / zero-width character removal."""

    def test_nfc_composed_form(self):
        # 'é' as decomposed (e + combining acute) should become composed 'é'
        decomposed = "re\u0301sume\u0301"   # e + combining acute twice
        result = preprocess(decomposed)
        assert "\u0301" not in result           # combining accent gone
        assert "é" in result or "resume" in result.lower()

    def test_bom_removed(self):
        result = preprocess("\uFEFFHello World")
        assert "\uFEFF" not in result
        assert result.startswith("Hello")

    def test_zero_width_space_removed(self):
        result = preprocess("Pyth\u200Bon")   # zero-width space inside "Python"
        assert "\u200B" not in result

    def test_non_breaking_space_normalised(self):
        result = preprocess("Hello\u00A0World")
        assert "\u00A0" not in result
        assert "Hello World" in result


class TestTypographicSubstitutions:
    """Curly quotes, dashes, ellipsis normalisation."""

    def test_curly_quotes_to_straight(self):
        result = preprocess("\u2018Hello\u2019 \u201CWorld\u201D")
        assert "'" in result
        assert '"' in result
        assert "\u2018" not in result
        assert "\u201C" not in result

    def test_em_dash_to_hyphen(self):
        result = preprocess("Lead Engineer\u2014FastAPI")
        assert "\u2014" not in result
        assert "-" in result

    def test_en_dash_to_hyphen(self):
        result = preprocess("2020\u20132024")
        assert "\u2013" not in result
        assert "2020-2024" in result

    def test_ellipsis_to_three_dots(self):
        result = preprocess("Python\u2026JavaScript")
        assert "\u2026" not in result
        assert "..." in result


class TestBulletNormalisation:
    """Bullet characters → "- " prefix."""

    @pytest.mark.parametrize("bullet", ["•", "▪", "◦", "‣", "▸", "►", "➤", "✓", "✔", "→"])
    def test_bullet_normalised_to_hyphen(self, bullet):
        text = f"{bullet} Implemented REST API"
        result = preprocess(text)
        assert bullet not in result
        assert result.strip().startswith("-")

    def test_multiple_bullets_normalised(self):
        text = "• Python\n• JavaScript\n• React"
        result = preprocess(text)
        lines = [ln for ln in result.splitlines() if ln.strip()]
        for line in lines:
            assert line.strip().startswith("-"), f"Expected hyphen, got: {line}"


class TestWhitespaceCollapsing:
    """Horizontal whitespace and blank line collapsing."""

    def test_multiple_spaces_collapsed(self):
        result = preprocess("Python   JavaScript    React")
        assert "  " not in result
        assert "Python JavaScript React" in result

    def test_tabs_collapsed_to_space(self):
        result = preprocess("Python\t\tJavaScript")
        assert "\t" not in result

    def test_newlines_preserved(self):
        # Newlines should NOT be collapsed by the horizontal space step
        result = preprocess("Line One\nLine Two\nLine Three")
        assert "\n" in result

    def test_triple_blank_lines_collapsed(self):
        text = "Section A\n\n\n\n\nSection B"
        result = preprocess(text)
        # Should have at most 2 consecutive newlines
        assert "\n\n\n" not in result

    def test_double_blank_line_preserved(self):
        text = "Section A\n\nSection B"
        result = preprocess(text)
        assert "\n\n" in result

    def test_leading_trailing_stripped(self):
        result = preprocess("  \n\nHello World\n\n  ")
        assert result == "Hello World"


class TestRealWorldResume:
    """Integration-style test with a realistic resume snippet."""

    RESUME_SNIPPET = """
\uFEFF  John Doe  \t
j.doe@example.com | +1 (555) 000-1234

PROFESSIONAL SUMMARY
Experienced software engineer\u2014 specialising in Python \u0026 FastAPI.
\u2022\tBuilt RESTful APIs serving 1M+ requests/day.
\u2022\tLed a team of 5 engineers.

TECHNICAL SKILLS
• Python  •  FastAPI  •  Docker  •  PostgreSQL


EDUCATION
B.Tech Computer Science\u2014XYZ University (2018\u20132022)
"""

    def test_bom_removed_from_resume(self):
        result = preprocess(self.RESUME_SNIPPET)
        assert "\uFEFF" not in result

    def test_em_dash_replaced(self):
        result = preprocess(self.RESUME_SNIPPET)
        assert "\u2014" not in result

    def test_bullets_normalised(self):
        result = preprocess(self.RESUME_SNIPPET)
        assert "•" not in result

    def test_tabs_removed(self):
        result = preprocess(self.RESUME_SNIPPET)
        assert "\t" not in result

    def test_no_triple_blank_lines(self):
        result = preprocess(self.RESUME_SNIPPET)
        assert "\n\n\n" not in result

    def test_output_is_non_empty(self):
        result = preprocess(self.RESUME_SNIPPET)
        assert len(result) > 50


class TestLargeInput:
    """Performance / boundary test with large inputs."""

    def test_5000_char_input_processed(self):
        text = "Python JavaScript React\n" * 200   # ~5000 chars
        result = preprocess(text)
        assert len(result) > 0

    def test_repeated_bullets_all_normalised(self):
        text = ("• Skill A\n" * 100)
        result = preprocess(text)
        assert "•" not in result
        lines = [ln for ln in result.splitlines() if ln.strip()]
        assert all(ln.strip().startswith("-") for ln in lines)
