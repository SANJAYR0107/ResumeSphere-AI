"""
resume_optimizer_service.py - Phase 4 Resume Rewrites, ATS Simulator, & Executive Summary Service

Purpose
-------
Generates AI-powered resume rewrite suggestions (Summary, Experience, Projects),
runs the ATS Improvement Simulator, builds interview alignment, learning roadmaps,
and generates the Executive Summary.
"""

import logging
from typing import TypedDict, Any

logger = logging.getLogger(__name__)


class RewriteSuggestions(TypedDict):
    professional_summary: str
    experience_bullets: list[str]
    project_descriptions: list[str]
    skills_ordering: list[str]
    achievements: list[str]


class SimulatorChangeItem(TypedDict):
    change: str
    score_boost: int
    category: str


class AtsSimulatorResult(TypedDict):
    current_ats_score: int
    predicted_ats_score: int
    expected_improvement: int
    score_boosting_changes: list[SimulatorChangeItem]


class InterviewAlignmentResult(TypedDict):
    likely_interview_topics: list[str]
    technical_questions: list[str]
    behavioral_questions: list[str]
    coding_topics: list[str]
    system_design_topics: list[str]


class LearningRecommendationItem(TypedDict):
    skill: str
    learning_priority: str  # "High", "Medium", "Low"
    difficulty: str  # "Easy", "Medium", "Hard"
    estimated_learning_time: str
    recommended_free_resources: list[str]
    suggested_practice_projects: list[str]


class ExecutiveSummaryResult(TypedDict):
    strengths: list[str]
    weaknesses: list[str]
    missing_skills: list[str]
    hiring_readiness: str  # "High Readiness", "Moderate Readiness", "Needs Optimization"
    top_improvements: list[str]
    overall_recommendation: str


def generate_rewrite_suggestions(
    candidate_name: str,
    role_title: str,
    resume_skills: list[str],
    missing_skills: list[str],
    yoe: int
) -> RewriteSuggestions:
    """Generate high-impact rewrite suggestions for resume sections."""
    name = candidate_name or "Candidate"
    title = role_title or "Software Engineer"
    skills_str = ", ".join(resume_skills[:5]) if resume_skills else "software engineering"
    top_missing = ", ".join(missing_skills[:2]) if missing_skills else "cloud architecture"

    # Professional Summary Rewrite
    summary_rewrite = (
        f"Results-driven {title} with {max(yoe, 3)}+ years of experience building high-performance applications. "
        f"Proficient in {skills_str}. Proven track record of scaling backend services, optimizing database performance, "
        f"and collaborating in Agile teams. Actively enhancing expertise in {top_missing}."
    )

    # Experience Bullets Rewrites
    exp_bullets = [
        f"Architected and deployed enterprise RESTful APIs using {resume_skills[0] if resume_skills else 'Java'}, reducing latency by 35% across microservices.",
        f"Integrated {missing_skills[0] if missing_skills else 'Docker'} containerization into CI/CD pipeline, accelerating release cycles by 40%.",
        f"Optimized SQL query performance and database indexing, improving system throughput by 50% for 100K+ daily active users."
    ]

    # Project Descriptions Rewrites
    proj_rewrites = [
        f"Scalable {title} Application: Engineered a production-ready application leveraging {skills_str}, implementing JWT authentication, Redis caching, and automated testing suites.",
        f"Cloud Infrastructure Automation: Built automated deployment scripts incorporating {missing_skills[0] if missing_skills else 'AWS'}, achieving 99.9% uptime and zero-downtime deployments."
    ]

    # Optimized Skills Ordering
    prioritized_skills = missing_skills[:3] + [s for s in resume_skills if s not in missing_skills]

    # Achievement Rewrites
    achieve_rewrites = [
        f"Recognized for technical excellence after engineering a automated pipeline using {skills_str}.",
        f"Increased application test coverage from 60% to 92%, resulting in zero critical production bugs over 6 consecutive months."
    ]

    return RewriteSuggestions(
        professional_summary=summary_rewrite,
        experience_bullets=exp_bullets,
        project_descriptions=proj_rewrites,
        skills_ordering=prioritized_skills,
        achievements=achieve_rewrites
    )


def simulate_ats_improvement(
    current_ats_score: int,
    missing_skills: list[str]
) -> AtsSimulatorResult:
    """Simulate ATS score improvement delta if recommendations are implemented."""
    changes: list[SimulatorChangeItem] = []
    total_boost = 0

    if missing_skills:
        boost1 = min(12, len(missing_skills) * 4)
        changes.append(SimulatorChangeItem(
            change=f"Add missing target keywords ({', '.join(missing_skills[:3])}) to Skills section",
            score_boost=boost1,
            category="Keywords"
        ))
        total_boost += boost1

    changes.append(SimulatorChangeItem(
        change="Quantify experience bullets with percentage and metric achievements",
        score_boost=8,
        category="Metrics"
    ))
    total_boost += 8

    changes.append(SimulatorChangeItem(
        change="Align Professional Summary directly with target Job Description role title",
        score_boost=5,
        category="Relevance"
    ))
    total_boost += 5

    predicted_score = min(100, current_ats_score + total_boost)
    delta = predicted_score - current_ats_score

    return AtsSimulatorResult(
        current_ats_score=current_ats_score,
        predicted_ats_score=predicted_score,
        expected_improvement=delta,
        score_boosting_changes=changes
    )


def generate_interview_alignment(
    role_title: str,
    matched_skills: list[str],
    missing_skills: list[str]
) -> InterviewAlignmentResult:
    """Generate interview preparation aligned with target Job Description."""
    primary_skill = matched_skills[0] if matched_skills else "Software Engineering"

    topics = [
        f"{role_title} Core Concepts & Best Practices",
        f"{primary_skill} Architecture & Performance Tuning",
        "System Scalability & Microservices Design",
        "Database Indexing & Query Optimization"
    ]

    tech_questions = [
        f"How do you handle memory management and concurrency in {primary_skill}?",
        f"Walk me through how you would structure a high-throughput API for {role_title}.",
        "Explain the trade-offs between SQL relational databases and NoSQL document stores."
    ]

    behavioral_questions = [
        "Describe a complex technical disagreement you had with a teammate and how you resolved it.",
        "Tell me about a time a production incident occurred under your watch. What steps did you take?",
        "How do you prioritize technical debt against delivering urgent business features?"
    ]

    coding = [
        "Arrays & Sliding Window Patterns",
        "Hash Map Lookups & String Manipulations",
        "Binary Search & Graph Traversal (BFS/DFS)"
    ]

    sys_design = [
        f"Design a Rate Limiter for {role_title} APIs",
        "Design a Distributed Caching System (Redis architecture)",
        "Design a Real-Time Notification Service"
    ]

    return InterviewAlignmentResult(
        likely_interview_topics=topics,
        technical_questions=tech_questions,
        behavioral_questions=behavioral_questions,
        coding_topics=coding,
        system_design_topics=sys_design
    )


def generate_learning_recommendations(
    missing_skills: list[str]
) -> list[LearningRecommendationItem]:
    """Generate learning recommendations for missing skills."""
    res: list[LearningRecommendationItem] = []
    
    resource_map = {
        "docker": ["Docker Official Docs", "Docker Beginner to Master on FreeCodeCamp"],
        "kubernetes": ["Kubernetes.io Tutorials", "CKA Crash Course on YouTube"],
        "aws": ["AWS Skill Builder", "AWS Certified Solutions Architect Guide"],
        "python": ["Python Docs", "Real Python Tutorials"],
        "java": ["Dev.java", "Baeldung Spring Boot Tutorials"],
        "react": ["React.dev Documentation", "Full Stack Open Course"]
    }

    for skill in missing_skills:
        key = skill.lower()
        free_res = resource_map.get(key, [f"{skill} Official Documentation", f"{skill} FreeCodeCamp Tutorial"])
        
        res.append(LearningRecommendationItem(
            skill=skill,
            learning_priority="High" if skill == missing_skills[0] else "Medium",
            difficulty="Medium" if key in ["docker", "aws", "react"] else ("Hard" if key in ["kubernetes", "system design"] else "Easy"),
            estimated_learning_time="1 - 2 Weeks",
            recommended_free_resources=free_res,
            suggested_practice_projects=[
                f"Build a REST API using {skill}",
                f"Deploy a containerized application with {skill}"
            ]
        ))
    return res


def generate_executive_summary(
    match_score: int,
    ats_score: int,
    matched_skills: list[str],
    missing_skills: list[str],
    role_title: str
) -> ExecutiveSummaryResult:
    """Build high-level executive summary for candidate application readiness."""
    readiness = "High Readiness" if match_score >= 80 else ("Moderate Readiness" if match_score >= 60 else "Needs Optimization")
    
    strengths = [
        f"Strong foundation in core technical skills ({', '.join(matched_skills[:3]) if matched_skills else 'General Tech'}).",
        f"ATS baseline score of {ats_score}/100 indicates solid structure."
    ]

    weaknesses = [
        f"Missing key JD skills ({', '.join(missing_skills[:3]) if missing_skills else 'None'}).",
        "Bullet points could benefit from additional quantified metrics."
    ]

    improvements = [
        f"Integrate target skills ({', '.join(missing_skills[:2])}) into your Skills and Experience sections.",
        "Apply the suggested Professional Summary rewrite to directly align with the role title.",
        "Quantify project achievements with user metrics or percentage gains."
    ]

    rec = f"Candidate shows {readiness.lower()} for the {role_title} position. Implementing the top 3 recommendations will maximize ATS pass rates and interview callback probability."

    return ExecutiveSummaryResult(
        strengths=strengths,
        weaknesses=weaknesses,
        missing_skills=missing_skills,
        hiring_readiness=readiness,
        top_improvements=improvements,
        overall_recommendation=rec
    )
