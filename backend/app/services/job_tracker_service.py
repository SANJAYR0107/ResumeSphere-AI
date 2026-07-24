"""
job_tracker_service.py - Phase C Job Application Tracker Service

Purpose
-------
Tracks job applications across status stages (Wishlist, Applied, Interview Scheduled,
Offer Received, Rejected). Computes application conversion analytics and timelines.
"""

import uuid
import time
import logging
from typing import TypedDict, Any

logger = logging.getLogger(__name__)


class TrackedJobEntry(TypedDict):
    job_id: str
    company_name: str
    role_title: str
    location: str
    status: str  # "Wishlist", "Applied", "Interview Scheduled", "Offer Received", "Rejected"
    salary_range: str
    applied_date: str
    created_at_timestamp: float
    notes: str


# In-memory application tracking store
_JOB_TRACKER_DB: dict[str, TrackedJobEntry] = {}


def save_tracked_job(
    company_name: str,
    role_title: str,
    location: str = "Remote",
    status: str = "Applied",
    salary_range: str = "$120K - $150K",
    notes: str = ""
) -> TrackedJobEntry:
    """Save or create a tracked job application."""
    job_id = f"job_{uuid.uuid4().hex[:8]}"
    applied_date = time.strftime("%Y-%m-%d")

    job_entry = TrackedJobEntry(
        job_id=job_id,
        company_name=company_name.strip(),
        role_title=role_title.strip(),
        location=location.strip(),
        status=status,
        salary_range=salary_range.strip(),
        applied_date=applied_date,
        created_at_timestamp=time.time(),
        notes=notes.strip()
    )

    _JOB_TRACKER_DB[job_id] = job_entry
    logger.info("Saved tracked job '%s' for company '%s'", job_id, company_name)
    return job_entry


def list_tracked_jobs() -> list[TrackedJobEntry]:
    """List all tracked job applications sorted by timestamp."""
    jobs = list(_JOB_TRACKER_DB.values())
    jobs.sort(key=lambda j: j["created_at_timestamp"], reverse=True)
    return jobs


def delete_tracked_job(job_id: str) -> bool:
    """Delete a tracked job application."""
    if job_id in _JOB_TRACKER_DB:
        del _JOB_TRACKER_DB[job_id]
        return True
    return False


def compute_tracker_analytics() -> dict[str, Any]:
    """Compute application tracking metrics, conversion rates, and status distribution."""
    jobs = list(_JOB_TRACKER_DB.values())
    total_jobs = len(jobs)

    status_counts = {
        "Wishlist": 0,
        "Applied": 0,
        "Interview Scheduled": 0,
        "Offer Received": 0,
        "Rejected": 0
    }

    for j in jobs:
        st = j["status"]
        if st in status_counts:
            status_counts[st] += 1

    interviews = status_counts["Interview Scheduled"] + status_counts["Offer Received"]
    offers = status_counts["Offer Received"]

    interview_rate = round((interviews / total_jobs * 100), 1) if total_jobs > 0 else 0.0
    offer_rate = round((offers / total_jobs * 100), 1) if total_jobs > 0 else 0.0

    return {
        "total_applications": total_jobs,
        "status_distribution": status_counts,
        "interview_conversion_rate": interview_rate,
        "offer_conversion_rate": offer_rate
    }
