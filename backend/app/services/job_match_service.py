"""
job_match_service.py  —  Phase 3 Job Role Matching Engine

Purpose
-------
Intelligently recommend jobs based on skills, experience, projects, education,
certifications, ATS Score, Resume Strength Index, and semantic similarity.
"""

import logging
import numpy as np

# Existing imports
from backend.app.services.embedding_service import get_embedding, get_raw_vector
from backend.app.services.preprocessing_service import preprocess
from backend.app.services.skill_extractor_service import extract_skills

logger = logging.getLogger(__name__)

JOB_PROFILES = [
    {
        "role_name": "Java Backend Developer",
        "required_skills": ["Java", "Spring Boot", "SQL", "REST API", "Microservices"],
        "preferred_skills": ["Docker", "Kubernetes", "AWS", "Kafka", "PostgreSQL"],
        "experience_level": "Mid",
        "education": "Bachelor's",
        "certifications": ["AWS Certified Developer"],
        "keywords": ["backend", "java", "spring", "api"]
    },
    {
        "role_name": "Full Stack Developer",
        "required_skills": ["JavaScript", "React", "Node.js", "HTML", "CSS"],
        "preferred_skills": ["TypeScript", "MongoDB", "Express", "Docker", "AWS"],
        "experience_level": "Mid",
        "education": "Bachelor's",
        "certifications": [],
        "keywords": ["frontend", "backend", "full stack", "react", "node"]
    },
    {
        "role_name": "Frontend Developer",
        "required_skills": ["JavaScript", "HTML", "CSS", "React"],
        "preferred_skills": ["Vue.js", "TypeScript", "Redux", "Webpack"],
        "experience_level": "Junior",
        "education": "Bachelor's",
        "certifications": [],
        "keywords": ["ui", "ux", "frontend", "web"]
    },
    {
        "role_name": "Python Developer",
        "required_skills": ["Python", "Django", "SQL", "REST API"],
        "preferred_skills": ["Flask", "FastAPI", "Docker", "AWS", "PostgreSQL"],
        "experience_level": "Mid",
        "education": "Bachelor's",
        "certifications": [],
        "keywords": ["python", "backend", "django", "flask", "fastapi"]
    },
    {
        "role_name": "Data Analyst",
        "required_skills": ["SQL", "Excel", "Python", "Data Visualization"],
        "preferred_skills": ["Tableau", "Power BI", "R", "Statistics"],
        "experience_level": "Junior",
        "education": "Bachelor's",
        "certifications": ["Google Data Analytics"],
        "keywords": ["data", "analysis", "sql", "dashboard"]
    },
    {
        "role_name": "Machine Learning Engineer",
        "required_skills": ["Python", "Machine Learning", "PyTorch", "TensorFlow"],
        "preferred_skills": ["Scikit-Learn", "SQL", "AWS", "Docker", "NLP"],
        "experience_level": "Senior",
        "education": "Master's",
        "certifications": ["AWS Machine Learning Specialty"],
        "keywords": ["ml", "ai", "model", "training"]
    },
    {
        "role_name": "Cloud Engineer",
        "required_skills": ["AWS", "Linux", "Networking", "Python"],
        "preferred_skills": ["Azure", "GCP", "Terraform", "Docker"],
        "experience_level": "Mid",
        "education": "Bachelor's",
        "certifications": ["AWS Solutions Architect"],
        "keywords": ["cloud", "infrastructure", "aws", "azure"]
    },
    {
        "role_name": "DevOps Engineer",
        "required_skills": ["Linux", "Docker", "Kubernetes", "CI/CD", "AWS"],
        "preferred_skills": ["Terraform", "Ansible", "Python", "Bash"],
        "experience_level": "Senior",
        "education": "Bachelor's",
        "certifications": ["CKA"],
        "keywords": ["pipeline", "automation", "deployment", "infrastructure"]
    },
    {
        "role_name": "Software Engineer",
        "required_skills": ["Java", "Python", "Algorithms", "Data Structures", "SQL"],
        "preferred_skills": ["C++", "System Design", "Cloud", "Git", "Javascript"],
        "experience_level": "Entry",
        "education": "Bachelor's",
        "certifications": [],
        "keywords": ["software", "development", "coding"]
    },
    {
        "role_name": "QA Engineer",
        "required_skills": ["Manual Testing", "Automated Testing", "Selenium", "Python"],
        "preferred_skills": ["Cypress", "Appium", "JIRA", "API Testing"],
        "experience_level": "Junior",
        "education": "Bachelor's",
        "certifications": ["ISTQB"],
        "keywords": ["quality", "assurance", "testing", "automation"]
    },
    {
        "role_name": "AI Engineer",
        "required_skills": ["Python", "Deep Learning", "NLP", "PyTorch"],
        "preferred_skills": ["LLMs", "Generative AI", "Hugging Face", "MLOps"],
        "experience_level": "Senior",
        "education": "Master's",
        "certifications": [],
        "keywords": ["ai", "generative", "llm", "neural"]
    }
]

def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Return cosine similarity between two 1-D numpy arrays."""
    norm_a = float(np.linalg.norm(a))
    norm_b = float(np.linalg.norm(b))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return float(np.dot(a, b) / (norm_a * norm_b))

def match_job_description(
    resume_text: str,
    jd_text: str,
    resume_skills: list[str],
) -> dict:
    """Legacy endpoint for backward compatibility."""
    clean_jd = preprocess(jd_text)
    
    get_embedding(resume_text[:2000])
    resume_vec = get_raw_vector()
    resume_vec = resume_vec.copy() if resume_vec is not None else None

    get_embedding(clean_jd[:2000])
    jd_vec = get_raw_vector()

    semantic_sim = _cosine_similarity(resume_vec, jd_vec) if resume_vec is not None and jd_vec is not None else 0.0

    jd_skills = [s["skill"] for s in extract_skills(clean_jd)]
    resume_lower = {s.lower() for s in resume_skills}
    
    matched_skills = [s for s in jd_skills if s.lower() in resume_lower]
    missing_skills = [s for s in jd_skills if s.lower() not in resume_lower]

    keyword_overlap = len(matched_skills) / len(jd_skills) if jd_skills else 0.0

    raw = semantic_sim * 0.6 + keyword_overlap * 0.4
    match_score = min(int(round(raw * 100)), 100)

    return {
        "match_score": match_score,
        "matched_skills": matched_skills,
        "missing_skills": missing_skills,
        "jd_skills": jd_skills,
        "semantic_similarity": semantic_sim,
    }


def match_resume_to_jobs(
    resume_text: str,
    resume_skills: list[str],
    ats_score: int,
    resume_strength_index: float,
    sections: dict[str, str]
) -> list[dict]:
    """
    Intelligently recommend jobs based on Skills, Experience, Projects, 
    Education, Certifications, ATS Score, Resume Strength, and Semantic Similarity.
    
    Returns Top 5 roles.
    """
    get_embedding(resume_text[:2000])
    resume_vec = get_raw_vector()
    resume_vec = resume_vec.copy() if resume_vec is not None else None

    resume_lower = {s.lower() for s in resume_skills}
    
    scored_profiles = []
    
    for profile in JOB_PROFILES:
        # 1. Skill Match
        req_skills = profile["required_skills"]
        pref_skills = profile["preferred_skills"]
        
        req_matched = [s for s in req_skills if s.lower() in resume_lower]
        pref_matched = [s for s in pref_skills if s.lower() in resume_lower]
        missing_skills = [s for s in req_skills if s.lower() not in resume_lower]
        recommended_skills = [s for s in pref_skills if s.lower() not in resume_lower]
        
        skill_score = 0.0
        if req_skills:
            skill_score += (len(req_matched) / len(req_skills)) * 60
        if pref_skills:
            skill_score += (len(pref_matched) / len(pref_skills)) * 40
            
        # 2. Semantic Match
        profile_text = f"{profile['role_name']} {' '.join(profile['keywords'])} {' '.join(req_skills)}"
        get_embedding(profile_text)
        prof_vec = get_raw_vector()
        semantic_sim = _cosine_similarity(resume_vec, prof_vec) if resume_vec is not None and prof_vec is not None else 0.0
        
        # 3. Overall match calculation incorporating ATS & RSI
        # Base match is 50% skill match, 30% semantic match, 20% general resume strength
        base_match = (skill_score * 0.5) + (semantic_sim * 100 * 0.3) + (min(ats_score, 100) * 0.2)
        
        # Boost based on Resume Strength Index (out of 10)
        base_match += (resume_strength_index / 10.0) * 5
        
        match_percentage = min(100, int(round(base_match)))
        
        # Determine confidence
        confidence = "High" if match_percentage >= 80 else "Medium" if match_percentage >= 60 else "Low"
        
        # Determine difficulty based on level and missing skills
        difficulty = "Medium"
        if profile["experience_level"] == "Senior" and len(missing_skills) > 0:
            difficulty = "Hard"
        elif len(missing_skills) == 0:
            difficulty = "Easy"
            
        scored_profiles.append({
            "role_name": profile["role_name"],
            "match_percentage": match_percentage,
            "matched_skills": req_matched + pref_matched,
            "missing_skills": missing_skills,
            "recommended_skills": recommended_skills,
            "confidence": confidence,
            "difficulty": difficulty
        })
        
    # Sort by highest match percentage and return top 5
    scored_profiles.sort(key=lambda x: int(str(x["match_percentage"])), reverse=True)
    return scored_profiles[:5]
