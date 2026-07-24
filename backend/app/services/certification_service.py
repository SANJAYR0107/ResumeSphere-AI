"""
certification_service.py - Phase C Certification Recommendation Engine

Purpose
-------
Recommends and ranks industry certifications (AWS, Azure, GCP, Oracle Java, Spring,
Docker, CKA Kubernetes, MongoDB, React, Node.js) based on candidate skills and role.
"""

import logging
from typing import TypedDict, Any

logger = logging.getLogger(__name__)


class CertificationRecommendation(TypedDict):
    certification_name: str
    issuer: str
    difficulty: str  # "Easy", "Medium", "Hard"
    career_value: str  # "High", "Very High"
    estimated_time: str
    prerequisite_skills: list[str]
    relevance_score: int  # 0 to 100
    official_link: str


CERTIFICATION_CATALOG: list[dict[str, Any]] = [
    {
        "name": "AWS Certified Solutions Architect – Associate",
        "issuer": "Amazon Web Services",
        "difficulty": "Medium",
        "career_value": "Very High",
        "time": "6 - 8 Weeks",
        "skills": ["aws", "cloud", "docker", "python", "java"],
        "link": "https://aws.amazon.com/certification/certified-solutions-architect-associate/"
    },
    {
        "name": "Certified Kubernetes Administrator (CKA)",
        "issuer": "Linux Foundation / CNCF",
        "difficulty": "Hard",
        "career_value": "Very High",
        "time": "8 - 12 Weeks",
        "skills": ["kubernetes", "docker", "devops", "linux"],
        "link": "https://www.cncf.io/certification/cka/"
    },
    {
        "name": "Oracle Certified Professional: Java SE Developer",
        "issuer": "Oracle",
        "difficulty": "Hard",
        "career_value": "High",
        "time": "6 - 10 Weeks",
        "skills": ["java", "spring boot", "backend"],
        "link": "https://education.oracle.com/java-se-developer/trackp_357"
    },
    {
        "name": "Spring Certified Professional",
        "issuer": "VMware Tanzu",
        "difficulty": "Medium",
        "career_value": "High",
        "time": "4 - 6 Weeks",
        "skills": ["spring boot", "java", "microservices"],
        "link": "https://tanzu.vmware.com/training/certification/spring-professional-develop-exam"
    },
    {
        "name": "Docker Certified Associate (DCA)",
        "issuer": "Mirantis / Docker",
        "difficulty": "Medium",
        "career_value": "High",
        "time": "4 - 6 Weeks",
        "skills": ["docker", "containers", "devops"],
        "link": "https://www.docker.com/certification/"
    },
    {
        "name": "MongoDB Certified Developer Associate",
        "issuer": "MongoDB Inc.",
        "difficulty": "Medium",
        "career_value": "High",
        "time": "3 - 5 Weeks",
        "skills": ["mongodb", "nosql", "node", "python"],
        "link": "https://university.mongodb.com/certification"
    }
]


def recommend_certifications(
    resume_skills: list[str],
    target_role: str = "Software Engineer"
) -> list[CertificationRecommendation]:
    """Recommend and rank certifications aligned with candidate skills and target role."""
    user_skills_lower = {s.strip().lower() for s in resume_skills}
    recommendations: list[CertificationRecommendation] = []

    for cert in CERTIFICATION_CATALOG:
        cert_skills = cert["skills"]
        match_count = sum(1 for cs in cert_skills if cs in user_skills_lower or any(cs in us for us in user_skills_lower))
        relevance = min(98, 60 + (match_count * 15))

        recommendations.append(CertificationRecommendation(
            certification_name=cert["name"],
            issuer=cert["issuer"],
            difficulty=cert["difficulty"],
            career_value=cert["career_value"],
            estimated_time=cert["time"],
            prerequisite_skills=[s.title() for s in cert_skills[:3]],
            relevance_score=relevance,
            official_link=cert["link"]
        ))

    recommendations.sort(key=lambda c: c["relevance_score"], reverse=True)
    return recommendations
