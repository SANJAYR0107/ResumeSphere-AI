"""
test_recruiter_service.py — Unit tests for the recruiter_service.py
"""

from backend.app.services.recruiter_service import generate_recruiter_insights

def test_generate_recruiter_insights():
    skills = ["Python", "FastAPI", "React", "Docker"]
    exp_text = "Worked as a Senior Developer. " * 30 # approx 900 chars
    proj_text = "Built a complex app." * 10
    
    # 1. High score
    res = generate_recruiter_insights(
        ats_score=92,
        skills=skills,
        experience_text=exp_text,
        projects_text=proj_text
    )
    
    assert res["recruiter_summary"]["pass_ats"] is True
    assert "Recommend" in res["recruiter_summary"]["hiring_recommendation"]
    assert "Mid-Level" in res["career_insights"]["career_level"] or "Senior" in res["career_insights"]["career_level"]
    assert "Software Engineer" in res["career_insights"]["best_job_roles"]
    assert res["interview_readiness"]["interview_score"] > 80

    # 2. Low score
    res_low = generate_recruiter_insights(
        ats_score=50,
        skills=["Python"],
        experience_text="Worked briefly.",
        projects_text=""
    )
    
    assert res_low["recruiter_summary"]["pass_ats"] is False
    assert res_low["recruiter_summary"]["hiring_recommendation"] == "Do Not Recommend"
    assert "Entry-Level" in res_low["career_insights"]["career_level"]
    assert res_low["interview_readiness"]["interview_score"] < 70
