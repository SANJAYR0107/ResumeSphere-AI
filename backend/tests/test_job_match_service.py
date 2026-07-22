import pytest
from unittest.mock import patch
from backend.app.services.job_match_service import match_resume_to_jobs

@patch("backend.app.services.job_match_service.get_embedding")
@patch("backend.app.services.job_match_service.get_raw_vector")
def test_match_resume_to_jobs_exact_match(mock_get_raw, mock_get_embed):
    import numpy as np
    mock_get_raw.return_value = np.zeros(384)
    
    # Setup perfect match for Java Backend Developer
    resume_skills = ["Java", "Spring Boot", "SQL", "REST API", "Microservices", "Docker", "AWS", "Kafka"]
    resume_text = "Experienced backend developer specializing in Java and Spring Boot. Microservices and Docker expert."
    ats_score = 95
    rsi = 8.5
    
    result = match_resume_to_jobs(
        resume_text=resume_text,
        resume_skills=resume_skills,
        ats_score=ats_score,
        resume_strength_index=rsi,
        sections={}
    )
    
    assert len(result) == 5
    top_role = result[0]
    
    assert top_role["role_name"] == "Java Backend Developer"
    assert top_role["match_percentage"] > 60
    assert top_role["confidence"] in ["High", "Medium"]
    assert top_role["difficulty"] == "Easy" # Because missing_skills is empty
    assert len(top_role["missing_skills"]) == 0
    assert "Java" in top_role["matched_skills"]

@patch("backend.app.services.job_match_service.get_embedding")
@patch("backend.app.services.job_match_service.get_raw_vector")
def test_match_resume_to_jobs_missing_skills(mock_get_raw, mock_get_embed):
    import numpy as np
    mock_get_raw.return_value = np.zeros(384)
    
    resume_skills = ["Python", "Machine Learning"]
    resume_text = "Junior data scientist working on machine learning."
    ats_score = 50
    rsi = 4.0
    
    result = match_resume_to_jobs(
        resume_text=resume_text,
        resume_skills=resume_skills,
        ats_score=ats_score,
        resume_strength_index=rsi,
        sections={}
    )
    
    ml_role = next(r for r in result if r["role_name"] == "Machine Learning Engineer")
    assert ml_role is not None
    # PyTorch and TensorFlow are missing
    assert "PyTorch" in ml_role["missing_skills"]
    assert "TensorFlow" in ml_role["missing_skills"]
    assert ml_role["difficulty"] == "Hard" # Missing skills + Senior level = Hard
