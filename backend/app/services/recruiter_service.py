"""
recruiter_service.py — Phase 4 Recruiter Insights

Purpose
-------
Generates AI-driven insights from the perspective of a recruiter.
Provides hiring recommendations, career roadmaps, and interview readiness.
"""

from typing import TypedDict, Any

# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class RecruiterSummary(TypedDict):
    pass_ats: bool
    top_strengths: list[str]
    top_concerns: list[str]
    hiring_recommendation: str
    overall_impression: str

class CareerInsights(TypedDict):
    best_job_roles: list[str]
    career_level: str
    learning_roadmap: list[str]
    recommended_certifications: list[str]
    technologies_to_learn: list[str]

class InterviewReadiness(TypedDict):
    interview_score: int
    weak_topics: list[str]
    likely_questions: list[str]
    preparation_tips: list[str]

class RecruiterInsightsResult(TypedDict):
    recruiter_summary: RecruiterSummary
    career_insights: CareerInsights
    interview_readiness: InterviewReadiness

class CareerRoadmap(TypedDict):
    current_level: str
    next_target: str
    roadmap_weeks: dict[str, str]
    recommended_certifications: list[str]
    projects_to_build: list[str]
    interview_topics: list[str]
    learning_priority: str

class InterviewPreparation(TypedDict):
    role_name: str
    top_interview_topics: list[str]
    likely_technical_questions: list[str]
    dsa_topics: list[str]
    projects_to_explain: list[str]
    behavioral_questions: list[str]
    preparation_score: int

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def generate_recruiter_insights(
    ats_score: int,
    skills: list[str],
    experience_text: str,
    projects_text: str
) -> RecruiterInsightsResult:
    """Generate comprehensive recruiter insights based on ATS performance and content."""
    
    # 1. Recruiter Summary
    pass_ats = ats_score >= 75
    
    strengths = []
    if ats_score >= 85: strengths.append("Excellent formatting and structure")
    if len(skills) >= 15: strengths.append("Strong technical vocabulary")
    if len(experience_text) > 500: strengths.append("Detailed professional experience")
    if not strengths: strengths.append("Good baseline qualifications")

    concerns = []
    if ats_score < 70: concerns.append("Low keyword optimization for ATS")
    if len(skills) < 10: concerns.append("Lack of diverse technical skills")
    if len(experience_text) < 200: concerns.append("Experience section lacks depth and metrics")

    if ats_score >= 90:
        rec = "Strongly Recommend"
        imp = "This candidate is highly competitive. Proceed to technical interview immediately."
    elif ats_score >= 75:
        rec = "Recommend"
        imp = "Solid candidate with good fundamentals. Worth a screening call."
    else:
        rec = "Do Not Recommend"
        imp = "Candidate needs to heavily revise their resume to pass initial screening."

    summary: RecruiterSummary = {
        "pass_ats": pass_ats,
        "top_strengths": strengths,
        "top_concerns": concerns,
        "hiring_recommendation": rec,
        "overall_impression": imp
    }

    # 2. Career Insights
    # Determine level
    exp_len = len(experience_text)
    if exp_len > 1500: level = "Senior / Lead"
    elif exp_len > 600: level = "Mid-Level"
    else: level = "Entry-Level / Junior"

    roles = ["Software Engineer"]
    if "react" in "".join(skills).lower() or "javascript" in "".join(skills).lower():
        roles.append("Frontend Developer")
    if "python" in "".join(skills).lower() or "java" in "".join(skills).lower():
        roles.append("Backend Developer")
    if "docker" in "".join(skills).lower() or "aws" in "".join(skills).lower():
        roles.append("DevOps Engineer")

    roadmap = [
        "Focus on system design and architecture concepts.",
        "Build a scalable microservices side project.",
        "Contribute to open-source repositories."
    ]

    certs = []
    if "aws" in "".join(skills).lower(): certs.append("AWS Certified Solutions Architect")
    if "azure" in "".join(skills).lower(): certs.append("Microsoft Certified: Azure Developer")
    if not certs: certs = ["AWS Certified Cloud Practitioner", "Certified Kubernetes Application Developer (CKAD)"]

    techs = ["Kubernetes", "GraphQL", "Go"] if "python" in "".join(skills).lower() else ["React", "Node.js", "TypeScript"]

    career: CareerInsights = {
        "best_job_roles": list(set(roles)),
        "career_level": level,
        "learning_roadmap": roadmap,
        "recommended_certifications": certs,
        "technologies_to_learn": techs
    }

    # 3. Interview Readiness
    interview_score = min(100, int((ats_score * 0.8) + (len(projects_text) / 20)))
    
    questions = [
        "Can you describe a time you optimized a poorly performing system?",
        "Walk me through your most complex technical project.",
        "How do you handle disagreements on technical architecture?"
    ]

    tips = [
        "Use the STAR method for behavioral questions.",
        "Be prepared to whiteboard system design for your listed projects.",
        "Review core data structures and algorithms."
    ]

    readiness: InterviewReadiness = {
        "interview_score": interview_score,
        "weak_topics": ["System Design", "Advanced Data Structures"] if interview_score < 80 else ["Niche Framework specifics"],
        "likely_questions": questions,
        "preparation_tips": tips
    }

    return {
        "recruiter_summary": summary,
        "career_insights": career,
        "interview_readiness": readiness
    }

def generate_career_roadmap(
    experience_text: str,
    top_role_name: str,
    missing_skills: list[str]
) -> CareerRoadmap:
    """Generate a 4-week personalized career roadmap."""
    exp_len = len(experience_text)
    if exp_len > 1500: current_level = "Senior"
    elif exp_len > 600: current_level = "Mid-Level"
    else: current_level = "Fresher / Junior"
    
    next_target = f"Next Level {top_role_name}" if current_level != "Senior" else f"Lead {top_role_name}"
    
    roadmap_weeks = {
        "Week 1": f"Focus on core fundamentals of {missing_skills[0] if missing_skills else 'Advanced Concepts'}.",
        "Week 2": f"Build small applications using {missing_skills[1] if len(missing_skills) > 1 else 'Best Practices'}.",
        "Week 3": "Integrate databases and deploy your application to the cloud.",
        "Week 4": "Mock interviews, resume refinement, and open-source contributions."
    }
    
    priority = "High priority on system design" if current_level == "Senior" else "High priority on hands-on coding and frameworks"
    
    return {
        "current_level": current_level,
        "next_target": next_target,
        "roadmap_weeks": roadmap_weeks,
        "recommended_certifications": ["AWS Certified Solutions Architect", "Certified Kubernetes Administrator (CKA)"],
        "projects_to_build": [f"Full-stack {top_role_name} application", "Microservices architecture prototype"],
        "interview_topics": ["System Design", "Data Structures", "Framework Internals"],
        "learning_priority": priority
    }

def generate_interview_prep(
    recommended_jobs: list[dict],
    ats_score: int
) -> list[InterviewPreparation]:
    """Generate interview preparation for recommended roles."""
    preps = []
    
    for job in recommended_jobs:
        role = job["role_name"]
        score = min(100, int(job["match_percentage"] * 0.9 + (ats_score * 0.1)))
        
        tech_questions = [
            f"How does concurrency work in {role}'s primary language?",
            f"Explain how you would scale a {role} application to 1M users.",
            "Describe a time you debugged a critical production issue."
        ]
        
        dsa = ["Arrays & Strings", "Hash Maps", "Trees & Graphs"]
        if "Data" in role or "Machine Learning" in role:
            dsa = ["Probability & Statistics", "Matrix Operations", "Dynamic Programming"]
            
        preps.append({
            "role_name": role,
            "top_interview_topics": ["System Design", "Framework Specifics", "Database Optimization"],
            "likely_technical_questions": tech_questions,
            "dsa_topics": dsa,
            "projects_to_explain": ["Your most complex technical challenge", "An end-to-end deployed project"],
            "behavioral_questions": [
                "Tell me about a time you failed and what you learned.",
                "How do you prioritize tech debt vs new features?"
            ],
            "preparation_score": score
        })
        
    return preps # type: ignore
