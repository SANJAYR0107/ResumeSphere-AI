"""
recommendation_service.py  —  Phase 4 Job Recommendations

Purpose
-------
Return ranked job recommendations from a curated catalogue of 10 profiles
using semantic + skill-overlap scoring.
"""

import logging
from typing import Any, Dict, Optional

import numpy as np

from backend.app.services.embedding_service import (
    get_embedding,
    get_raw_vector,
    is_loaded,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Job Profile Catalogue (10 roles)
# ---------------------------------------------------------------------------

_JOB_PROFILES: dict[str, dict[str, Any]] = {
    "Backend Developer": {
        "description": (
            "Design and build scalable REST APIs and microservices using Python, "
            "FastAPI, Django, Flask, Node.js. Work with PostgreSQL, MongoDB, Redis. "
            "Deploy on AWS using Docker and Kubernetes. Implement CI/CD pipelines "
            "with GitHub Actions. Strong Git and Linux skills required."
        ),
        "skills": [
            "Python", "FastAPI", "Django", "Flask", "PostgreSQL", "MongoDB",
            "Redis", "Docker", "Kubernetes", "AWS", "Git", "Linux",
        ],
    },
    "ML Engineer": {
        "description": (
            "Develop and deploy machine learning models using Python, TensorFlow, "
            "PyTorch, Scikit-learn. Experience with NLP, computer vision, and MLOps. "
            "AWS SageMaker, MLflow, feature engineering, Pandas, NumPy, statistics."
        ),
        "skills": [
            "Python", "TensorFlow", "PyTorch", "Scikit-learn", "NLP",
            "Machine Learning", "Deep Learning", "Pandas", "NumPy", "AWS",
            "Statistics", "Git",
        ],
    },
    "Frontend Developer": {
        "description": (
            "Build responsive, accessible web applications using React, TypeScript, "
            "and JavaScript. Styling with CSS and Tailwind. State management with Redux. "
            "REST API integration, Jest testing, CI/CD, Git, performance optimisation."
        ),
        "skills": [
            "React", "TypeScript", "JavaScript", "HTML", "CSS",
            "Redux", "Node.js", "Git", "Jest",
        ],
    },
    "Full Stack Developer": {
        "description": (
            "End-to-end development using React, Node.js, Python, FastAPI. "
            "PostgreSQL, MongoDB, Redis for data storage. Docker, AWS, CI/CD pipelines. "
            "REST APIs, GraphQL, TypeScript, responsive design, and Git workflows."
        ),
        "skills": [
            "React", "Node.js", "Python", "FastAPI", "PostgreSQL",
            "MongoDB", "Docker", "AWS", "JavaScript", "TypeScript", "Git",
        ],
    },
    "DevOps Engineer": {
        "description": (
            "Manage cloud infrastructure on AWS, Azure, GCP. Container orchestration "
            "with Kubernetes and Docker. Infrastructure-as-Code using Terraform and "
            "Ansible. CI/CD with GitHub Actions and Jenkins. Linux, monitoring, logging."
        ),
        "skills": [
            "AWS", "Docker", "Kubernetes", "Terraform", "Linux",
            "Git", "GitHub Actions", "Python", "Azure",
        ],
    },
    "Data Scientist": {
        "description": (
            "Analyse large datasets using Python, Pandas, NumPy. Build predictive "
            "models with Scikit-learn and XGBoost. Data visualisation with Matplotlib. "
            "SQL, Spark, A/B testing, statistical analysis, and business reporting."
        ),
        "skills": [
            "Python", "Pandas", "NumPy", "Scikit-learn", "Machine Learning",
            "SQL", "Matplotlib", "XGBoost", "Statistics", "Git",
        ],
    },
    "Cloud Architect": {
        "description": (
            "Design resilient cloud architectures on AWS, Azure, and GCP. "
            "Microservices, serverless functions, Kubernetes, Terraform, and security. "
            "Cost optimisation, multi-region deployments, and compliance frameworks."
        ),
        "skills": [
            "AWS", "Azure", "GCP", "Kubernetes", "Terraform",
            "Docker", "Linux", "Python", "Git",
        ],
    },
    "Java Developer": {
        "description": (
            "Develop enterprise-grade applications using Java and Spring Boot. "
            "Hibernate ORM, REST APIs, and microservices architecture. "
            "PostgreSQL, MySQL, Docker, Jenkins CI/CD, Maven, unit and integration testing."
        ),
        "skills": [
            "Java", "Spring Boot", "Hibernate", "PostgreSQL", "MySQL",
            "Docker", "Git", "Maven",
        ],
    },
    "Android Developer": {
        "description": (
            "Build native Android applications using Kotlin and Jetpack Compose. "
            "MVVM architecture, Retrofit for networking, Room for local persistence, "
            "Coroutines, Firebase integration, Google Play publishing, and Git."
        ),
        "skills": [
            "Kotlin", "Java", "Android", "Firebase", "Git",
        ],
    },
    "QA Engineer": {
        "description": (
            "Design and maintain automated test suites using Python, Selenium, "
            "pytest, and Cypress. API testing with Postman. CI/CD integration. "
            "Performance testing, defect lifecycle management, and Agile workflows."
        ),
        "skills": [
            "Python", "Selenium", "pytest", "Git", "Docker",
        ],
    },
}

# Module-level vector cache — populated lazily on first call
_profile_vectors: Optional[Dict[str, np.ndarray]] = None

def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Return cosine similarity between two 1-D numpy arrays."""
    norm_a = float(np.linalg.norm(a))
    norm_b = float(np.linalg.norm(b))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return float(np.dot(a, b) / (norm_a * norm_b))

def _get_profile_vectors() -> dict[str, np.ndarray]:
    """Lazily embed all job profiles and cache the results."""
    global _profile_vectors
    if _profile_vectors is None:
        logger.info(
            "recommendation_service: embedding %d job profiles (one-time startup cost)…",
            len(_JOB_PROFILES),
        )
        vectors: dict[str, np.ndarray] = {}
        for title, profile in _JOB_PROFILES.items():
            get_embedding(profile["description"])
            vec = get_raw_vector()
            if vec is not None:
                vectors[title] = vec.copy()
        _profile_vectors = vectors
        logger.info("recommendation_service: %d profile vectors cached.", len(vectors))
    return _profile_vectors

def get_job_recommendations(
    resume_skills: list[str],
    resume_text: str,
) -> list[dict]:
    """Return the top-5 job recommendations for the given resume."""
    if not is_loaded():
        logger.warning(
            "recommendation_service: embedding model not loaded — "
            "returning empty job recommendations."
        )
        return []

    profile_vectors = _get_profile_vectors()

    # Embed resume once
    get_embedding(resume_text[:2000])
    resume_vec = get_raw_vector()
    resume_vec = resume_vec.copy() if resume_vec is not None else None

    resume_lower: set[str] = {s.lower() for s in resume_skills}

    results: list[dict] = []
    for title, profile in _JOB_PROFILES.items():
        profile_vec = profile_vectors.get(title)

        # Semantic similarity
        if resume_vec is not None and profile_vec is not None:
            if resume_vec.shape != profile_vec.shape:
                raise RuntimeError(
                    f"Dimension mismatch: resume_vec has shape {resume_vec.shape}, "
                    f"but profile_vec '{title}' has shape {profile_vec.shape}."
                )
            sem_sim = _cosine_similarity(resume_vec, profile_vec)
        else:
            sem_sim = 0.0

        # Skill overlap
        profile_lower: set[str] = {s.lower() for s in profile["skills"]}
        overlap_count = len(resume_lower & profile_lower)
        skill_sim = overlap_count / len(profile_lower) if profile_lower else 0.0

        # Matched skills for display
        matched = [s for s in profile["skills"] if s.lower() in resume_lower]

        # Composite score
        raw = sem_sim * 0.7 + skill_sim * 0.3
        match_score = min(int(round(raw * 100)), 100)

        results.append(
            {
                "title": title,
                "match_score": match_score,
                "description": profile["description"][:130] + "…",
                "matched_skills": matched,
            }
        )

    results.sort(key=lambda r: r["match_score"], reverse=True)
    top5 = results[:5]

    logger.info(
        "recommendation_service: recommendations: %s",
        [(r["title"], r["match_score"]) for r in top5],
    )

    return top5
