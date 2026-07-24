"""
career_coach_service.py - Phase C AI Career Coach Engine

Purpose
-------
Generates personalized 6-month AI career growth roadmaps, skill priorities,
milestone timelines, and long-term career goals based on current candidate skills.
"""

import logging
from typing import TypedDict, Any

logger = logging.getLogger(__name__)


class GrowthPhase(TypedDict):
    phase_number: int
    duration_months: str
    focus_title: str
    skill_priorities: list[str]
    action_items: list[str]
    milestone_goal: str


class CareerCoachRoadmap(TypedDict):
    current_skills: list[str]
    target_role: str
    career_path_title: str
    overall_growth_strategy: str
    recommended_timeline: str
    phases: list[GrowthPhase]
    target_companies: list[str]


def generate_career_roadmap(
    resume_skills: list[str],
    target_role: str = "Senior Software Engineer"
) -> CareerCoachRoadmap:
    """Generate a structured 6-month AI career growth roadmap."""
    skills_clean = [s.strip() for s in resume_skills if s.strip()]
    if not skills_clean:
        skills_clean = ["Python", "JavaScript", "SQL"]

    primary_skill = skills_clean[0]

    phases = [
        GrowthPhase(
            phase_number=1,
            duration_months="Months 1 - 2",
            focus_title=f"Advanced Mastery of {primary_skill} & Core Architecture",
            skill_priorities=[primary_skill, "Design Patterns", "Unit Testing"],
            action_items=[
                f"Master advanced features and performance optimization in {primary_skill}.",
                "Build 2 production-ready microservices with automated test coverage > 85%.",
                "Implement structured logging, health checks, and CI/CD pipelines."
            ],
            milestone_goal=f"Deep expertise in {primary_skill} backend architecture."
        ),
        GrowthPhase(
            phase_number=2,
            duration_months="Months 3 - 4",
            focus_title="Cloud Native & Container Orchestration",
            skill_priorities=["Docker", "Kubernetes", "AWS / Cloud Infrastructure"],
            action_items=[
                "Containerize all local services using multi-stage production Dockerfiles.",
                "Deploy services onto Kubernetes (Minikube or Cloud K8s) with Helm charts.",
                "Set up cloud monitoring and automated deployment pipelines."
            ],
            milestone_goal="Full competency in cloud-native containerized infrastructure."
        ),
        GrowthPhase(
            phase_number=3,
            duration_months="Months 5 - 6",
            focus_title="System Design & Product Company Applications",
            skill_priorities=["Distributed Systems", "System Design", "Caching (Redis)"],
            action_items=[
                "Study high-throughput distributed system design patterns (Rate Limiters, Message Queues).",
                "Refine resume with quantified metric achievements using ResumeSphere AI.",
                "Target applications for top product-based engineering companies."
            ],
            milestone_goal=f"Job readiness for {target_role} at top-tier product companies."
        )
    ]

    return CareerCoachRoadmap(
        current_skills=skills_clean,
        target_role=target_role,
        career_path_title=f"{target_role} Accelerated Growth Path",
        overall_growth_strategy=f"Transition from intermediate application development to end-to-end cloud-native software architecture specializing in {primary_skill}.",
        recommended_timeline="6 Months (10 - 12 hours/week)",
        phases=phases,
        target_companies=["Google", "Amazon", "Microsoft", "Top High-Growth Tech Startups"]
    )
