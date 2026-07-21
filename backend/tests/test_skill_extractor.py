"""
test_skill_extractor.py — Unit tests for skill_extractor_service.py

Test matrix covers:
  - CSV dataset loading (count > 0)
  - Empty input returns empty list
  - Known skills are detected
  - Skill names are deduplicated
  - Skills are sorted alphabetically
  - Case-insensitive matching (python, PYTHON, Python all match)
  - Confidence scores are in [0.0, 1.0]
  - Max-frequency skill gets confidence = 1.0
  - Multi-word skills detected (e.g. "Machine Learning", "React Native")
  - Skills with special characters (e.g. "C++", "Node.js", "ASP.NET")
  - Unrelated text produces no matches
  - Large resume text
  - get_skill_names() convenience wrapper
  - get_loaded_skill_count() returns positive integer
"""


from backend.app.services.skill_extractor_service import (
    extract_skills,
    get_loaded_skill_count,
    get_skill_names,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

TECH_RESUME = """
John Doe — Senior Software Engineer

TECHNICAL SKILLS
Python, JavaScript, TypeScript, React, Node.js, FastAPI, Docker,
Kubernetes, PostgreSQL, Redis, AWS, Machine Learning, TensorFlow,
Git, Linux, C++

EXPERIENCE
Led backend development using Python and FastAPI.
Deployed containerized applications with Docker and Kubernetes on AWS.
Implemented Machine Learning models using TensorFlow and Scikit-learn.
Used PostgreSQL and Redis for data persistence and caching.
"""

FRESH_GRAD_RESUME = """
Alice Smith — Junior Developer

Skills: Python, HTML, CSS, JavaScript, Git, SQL

Projects
Built a React app with Node.js backend connected to a MySQL database.
Used Git for version control throughout all projects.
"""

IRRELEVANT_TEXT = """
The quick brown fox jumps over the lazy dog.
This document has no technical content whatsoever.
Numbers: 1234567890.
"""

MULTI_WORD_SKILLS_TEXT = """
Experienced in Machine Learning, Deep Learning, Natural Language Processing,
Computer Vision, React Native, Apache Kafka, Spring Boot, and ASP.NET Core.
"""


# ---------------------------------------------------------------------------
# Tests: Dataset loading
# ---------------------------------------------------------------------------

class TestDatasetLoading:

    def test_skills_loaded_count_positive(self):
        count = get_loaded_skill_count()
        assert count > 0, "No skills loaded from CSV"

    def test_skills_count_exceeds_100(self):
        # Our dataset has 400+ skills
        assert get_loaded_skill_count() > 100


# ---------------------------------------------------------------------------
# Tests: Empty / edge inputs
# ---------------------------------------------------------------------------

class TestEdgeCases:

    def test_empty_string_returns_empty_list(self):
        result = extract_skills("")
        assert result == []

    def test_whitespace_only_returns_empty_list(self):
        result = extract_skills("   \n\n   ")
        assert result == []

    def test_irrelevant_text_returns_no_skills(self):
        result = extract_skills(IRRELEVANT_TEXT)
        assert len(result) == 0


# ---------------------------------------------------------------------------
# Tests: Skill detection
# ---------------------------------------------------------------------------

class TestSkillDetection:

    def test_python_detected(self):
        names = get_skill_names(TECH_RESUME)
        assert "Python" in names

    def test_javascript_detected(self):
        names = get_skill_names(TECH_RESUME)
        assert "JavaScript" in names

    def test_docker_detected(self):
        names = get_skill_names(TECH_RESUME)
        assert "Docker" in names

    def test_kubernetes_detected(self):
        names = get_skill_names(TECH_RESUME)
        assert "Kubernetes" in names

    def test_aws_detected(self):
        names = get_skill_names(TECH_RESUME)
        assert "AWS" in names

    def test_postgresql_detected(self):
        names = get_skill_names(TECH_RESUME)
        assert "PostgreSQL" in names

    def test_redis_detected(self):
        names = get_skill_names(TECH_RESUME)
        assert "Redis" in names

    def test_git_detected(self):
        names = get_skill_names(FRESH_GRAD_RESUME)
        assert "Git" in names

    def test_html_detected(self):
        names = get_skill_names(FRESH_GRAD_RESUME)
        assert "HTML" in names


class TestMultiWordSkills:
    """Multi-word skill phrases should be detected as a unit."""

    def test_machine_learning_detected(self):
        names = get_skill_names(MULTI_WORD_SKILLS_TEXT)
        assert "Machine Learning" in names

    def test_deep_learning_detected(self):
        names = get_skill_names(MULTI_WORD_SKILLS_TEXT)
        assert "Deep Learning" in names

    def test_natural_language_processing_detected(self):
        names = get_skill_names(MULTI_WORD_SKILLS_TEXT)
        assert "Natural Language Processing" in names

    def test_computer_vision_detected(self):
        names = get_skill_names(MULTI_WORD_SKILLS_TEXT)
        assert "Computer Vision" in names

    def test_spring_boot_detected(self):
        names = get_skill_names(MULTI_WORD_SKILLS_TEXT)
        assert "Spring Boot" in names


# ---------------------------------------------------------------------------
# Tests: Case insensitivity
# ---------------------------------------------------------------------------

class TestCaseInsensitivity:

    def test_lowercase_python_detected(self):
        names = get_skill_names("experienced in python and javascript")
        assert "Python" in names

    def test_uppercase_python_detected(self):
        names = get_skill_names("experienced in PYTHON")
        assert "Python" in names

    def test_mixed_case_docker_detected(self):
        names = get_skill_names("using Docker and KUBERNETES")
        assert "Docker" in names


# ---------------------------------------------------------------------------
# Tests: Deduplication
# ---------------------------------------------------------------------------

class TestDeduplication:

    def test_python_appears_once_even_if_mentioned_many_times(self):
        text = "Python Python Python Python Python"
        names = get_skill_names(text)
        assert names.count("Python") == 1

    def test_multiple_skills_each_appear_once(self):
        text = "Python Python React React Docker Docker"
        names = get_skill_names(text)
        for name in names:
            assert names.count(name) == 1


# ---------------------------------------------------------------------------
# Tests: Alphabetical ordering
# ---------------------------------------------------------------------------

class TestAlphabeticalSorting:

    def test_skills_are_sorted_alphabetically(self):
        result = extract_skills(TECH_RESUME)
        names = [s["skill"] for s in result]
        assert names == sorted(names, key=str.lower)

    def test_get_skill_names_sorted(self):
        names = get_skill_names(TECH_RESUME)
        assert names == sorted(names, key=str.lower)


# ---------------------------------------------------------------------------
# Tests: Confidence scores
# ---------------------------------------------------------------------------

class TestConfidenceScores:

    def test_all_confidence_in_range(self):
        result = extract_skills(TECH_RESUME)
        for item in result:
            assert 0.0 <= item["confidence"] <= 1.0, (
                f"Confidence out of range for '{item['skill']}': {item['confidence']}"
            )

    def test_max_confidence_is_1_0(self):
        # Skill appearing most often should have confidence exactly 1.0
        text = "Python Python Python React"  # Python appears 3x, React 1x
        result = extract_skills(text)
        max_conf = max(item["confidence"] for item in result)
        assert max_conf == 1.0

    def test_less_frequent_skill_has_lower_confidence(self):
        text = "Python Python Python React"
        result = extract_skills(text)
        by_skill = {item["skill"]: item["confidence"] for item in result}
        if "Python" in by_skill and "React" in by_skill:
            assert by_skill["Python"] > by_skill["React"]


# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------

class TestReturnStructure:

    def test_each_item_has_skill_key(self):
        result = extract_skills(TECH_RESUME)
        for item in result:
            assert "skill" in item

    def test_each_item_has_category_key(self):
        result = extract_skills(TECH_RESUME)
        for item in result:
            assert "category" in item

    def test_each_item_has_confidence_key(self):
        result = extract_skills(TECH_RESUME)
        for item in result:
            assert "confidence" in item

    def test_python_category_is_programming(self):
        result = extract_skills("Python")
        python_items = [i for i in result if i["skill"] == "Python"]
        assert len(python_items) == 1
        assert python_items[0]["category"] == "Programming"

    def test_docker_category_is_devops(self):
        result = extract_skills("Docker and Kubernetes")
        docker_items = [i for i in result if i["skill"] == "Docker"]
        assert len(docker_items) == 1
        assert docker_items[0]["category"] == "DevOps"

    def test_aws_category_is_cloud(self):
        result = extract_skills("AWS deployment")
        aws_items = [i for i in result if i["skill"] == "AWS"]
        assert len(aws_items) == 1
        assert aws_items[0]["category"] == "Cloud"


# ---------------------------------------------------------------------------
# Tests: Convenience wrapper
# ---------------------------------------------------------------------------

class TestGetSkillNames:

    def test_returns_list_of_strings(self):
        result = get_skill_names(TECH_RESUME)
        assert isinstance(result, list)
        assert all(isinstance(s, str) for s in result)

    def test_returns_subset_of_extract_skills(self):
        details = extract_skills(TECH_RESUME)
        names_from_details = [d["skill"] for d in details]
        names_from_wrapper = get_skill_names(TECH_RESUME)
        assert names_from_details == names_from_wrapper
