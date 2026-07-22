import pytest
from backend.app.services.skill_gap_service import analyze_role_skill_gap

def test_analyze_skill_gap_missing():
    resume_skills = ["Python", "JavaScript"]
    top_role_req = ["Python", "Machine Learning", "PyTorch"]
    top_role_pref = ["Docker", "SQL"]
    
    result = analyze_role_skill_gap(resume_skills, top_role_req, top_role_pref)
    
    assert "overall_score" in result
    assert result["overall_score"] > 0
    assert "Machine Learning" in result["critical_skills"]
    assert "PyTorch" in result["critical_skills"]
    assert "Docker" in result["nice_to_have_skills"]
    assert "SQL" in result["nice_to_have_skills"]
    assert len(result["missing_skills"]) == 4

def test_analyze_skill_gap_perfect():
    resume_skills = ["Python", "SQL", "Docker"]
    top_role_req = ["Python", "SQL"]
    top_role_pref = ["Docker"]
    
    result = analyze_role_skill_gap(resume_skills, top_role_req, top_role_pref)
    
    assert result["overall_score"] == 100
    assert len(result["critical_skills"]) == 0
    assert len(result["nice_to_have_skills"]) == 0
    assert len(result["missing_skills"]) == 0
