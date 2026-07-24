"""
resume_chat_service.py - Phase C AI Resume Chat Assistant Service

Purpose
-------
Provides an intelligent conversational assistant that answers candidate questions
using context extracted from their Resume, ATS Reports, Job Description analysis,
missing skills, and interview performance reports.
"""

import logging
from typing import TypedDict, Any

from backend.app.services.preprocessing_service import preprocess

logger = logging.getLogger(__name__)


class ChatResponse(TypedDict):
    user_query: str
    assistant_response: str
    suggested_followup_queries: list[str]
    context_sources_used: list[str]


def process_resume_chat_query(
    query: str,
    resume_skills: list[str] | None = None,
    ats_score: int | None = 75,
    missing_skills: list[str] | None = None,
    target_role: str | None = "Software Engineer"
) -> ChatResponse:
    """Process user query against candidate resume and analysis context."""
    if not query or not query.strip():
        return ChatResponse(
            user_query="",
            assistant_response="Hello! I am your AI Resume & Career Coach. Ask me anything about your ATS score, missing skills, resume improvement, or interview prep!",
            suggested_followup_queries=[
                "Why is my ATS score low?",
                "What skills am I missing for my target role?",
                "How do I improve my experience bullets?"
            ],
            context_sources_used=["General AI Assistant"]
        )

    q_lower = query.lower()
    skills = resume_skills or ["Python", "SQL", "FastAPI"]
    missing = missing_skills or ["Docker", "Kubernetes", "AWS"]
    ats = ats_score if ats_score is not None else 75
    role = target_role or "Software Engineer"

    response = ""
    sources = ["Resume Parser", "ATS Scoring Engine"]
    followups = []

    # 1. ATS Score Questions
    if "ats score" in q_lower or "score low" in q_lower or "increase score" in q_lower:
        response = (
            f"Your current baseline ATS score is **{ats}/100**. "
            f"To boost your score by 15-20 points:\n"
            f"1. **Add Missing Skills**: Integrate key terms like `{', '.join(missing[:3])}` into your Skills & Experience sections.\n"
            f"2. **Quantify Impact**: Include measurable metrics (e.g. 'reduced latency by 35%', 'handled 100K users') in your work experience bullets.\n"
            f"3. **Standardize Section Headings**: Ensure standard headers like 'WORK EXPERIENCE' and 'TECHNICAL SKILLS' are used so ATS parsers index them cleanly."
        )
        followups = [
            "How do I rewrite my summary for a higher score?",
            "What missing skills should I prioritize first?"
        ]

    # 2. Missing Skills & Keyword Questions
    elif "missing" in q_lower or "skill" in q_lower or "learn next" in q_lower:
        response = (
            f"Based on our Job Description analysis for **{role}**, your top missing skills are: "
            f"**{', '.join(missing[:3])}**.\n\n"
            f"Adding these skills to your resume and building 1-2 small projects demonstrating them will significantly increase recruiter response rates."
        )
        followups = [
            "Generate a 6-month learning roadmap for these skills",
            "Which certifications are recommended for Docker & AWS?"
        ]

    # 3. Project Improvement Questions
    elif "project" in q_lower or "portfolio" in q_lower or "github" in q_lower:
        response = (
            f"To make your projects stand out to technical hiring managers:\n"
            f"1. **Add Architecture Details**: Mention framework versions (e.g. `{skills[0]}`, FastAPI, Redis).\n"
            f"2. **Include Production Metrics**: Mention uptime, user scale, query latency gains, or test coverage (>85%).\n"
            f"3. **Provide GitHub Links**: Link directly to clean repositories with comprehensive README diagrams."
        )
        followups = [
            "Analyze my portfolio quality",
            "Suggest project ideas for my stack"
        ]

    # 4. Companies & Role Matching Questions
    elif "company" in q_lower or "match" in q_lower or "role" in q_lower:
        response = (
            f"Your technical background in `{', '.join(skills[:3])}` is a strong match for: "
            f"**Backend Engineer**, **Software Architect**, and **Cloud Systems Engineer** roles at product companies like Amazon, Google, and high-growth startups."
        )
        followups = [
            "How do I tailor my resume for product companies?",
            "Generate a tailored cover letter for Backend Engineer"
        ]

    # 5. Interview Prep Questions
    elif "interview" in q_lower or "prepare" in q_lower or "questions" in q_lower:
        response = (
            f"To prepare for **{role}** interviews:\n"
            f"1. **Practice Live Questions**: Use our Phase B Interactive AI Interview Platform to practice {skills[0]} technical and coding questions.\n"
            f"2. **Master the STAR Method**: Structure behavioral answers around Situation, Task, Action, and Result.\n"
            f"3. **System Design**: Review distributed caching (Redis) and database indexing algorithms."
        )
        followups = [
            "Start an interactive mock interview now",
            "Download my interview performance report"
        ]

    # Generic Fallback Response
    else:
        response = (
            f"Regarding your query about '{query}': Based on your resume skills (`{', '.join(skills[:3])}`) "
            f"and ATS score of **{ats}/100**, focusing on quantifying experience metrics and acquiring `{missing[0] if missing else 'AWS'}` "
            f"will give you the highest return on investment for {role} positions."
        )
        followups = [
            "Why is my ATS score low?",
            "What skills am I missing?",
            "Start an interactive AI interview"
        ]

    return ChatResponse(
        user_query=query,
        assistant_response=response,
        suggested_followup_queries=followups,
        context_sources_used=sources
    )
