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
