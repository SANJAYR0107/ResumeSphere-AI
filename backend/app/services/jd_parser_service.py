"""
jd_parser_service.py - Phase 4 Job Description Parsing Service

Purpose
-------
Parses, cleans, and structures target Job Descriptions from either raw text
or uploaded PDF files. Extracts skills, requirements, role titles, and metadata.
"""

import logging
import re
from pathlib import Path
from typing import TypedDict, Any

from backend.app.services.parser_service import extract_text_from_pdf, clean_text
from backend.app.services.preprocessing_service import preprocess
from backend.app.services.skill_extractor_service import SkillMatch, extract_skills

logger = logging.getLogger(__name__)


class ParsedJobDescription(TypedDict):
    """Structured representation of a parsed Job Description."""
    raw_text: str
    clean_text: str
    role_title: str
    extracted_skills: list[str]
    skill_details: list[SkillMatch]
    required_skills: list[str]
    preferred_skills: list[str]
    estimated_yoe: int
    required_education: str
    keywords: list[str]


def parse_jd_text(jd_text: str) -> ParsedJobDescription:
    """Parse a Job Description string into a structured model."""
    if not jd_text or not jd_text.strip():
        return ParsedJobDescription(
            raw_text="",
            clean_text="",
            role_title="Target Role",
            extracted_skills=[],
            skill_details=[],
            required_skills=[],
            preferred_skills=[],
            estimated_yoe=0,
            required_education="Bachelor's Degree",
            keywords=[],
        )

    cleaned = preprocess(jd_text)
    skills_data = extract_skills(cleaned)
    skill_names = [s["skill"] for s in skills_data]

    # Heuristic for Role Title
    lines = [line.strip() for line in jd_text.splitlines() if line.strip()]
    role_title = "Target Role"
    for line in lines[:5]:
        line_clean = re.sub(r'[^a-zA-Z0-9\s\-]', '', line).strip()
        if 5 <= len(line_clean) <= 60 and not any(h in line_clean.lower() for h in ["job description", "about us", "summary", "responsibilities"]):
            role_title = line_clean
            break

    # Heuristic for YOE
    yoe_match = re.search(r'(\d+)\+?\s*(?:-\s*\d+)?\s*(?:years?|yrs?)(?:\s*of)?\s*experience', cleaned, re.IGNORECASE)
    estimated_yoe = int(yoe_match.group(1)) if yoe_match else 2

    # Split required vs preferred skills
    req_skills: list[str] = []
    pref_skills: list[str] = []
    
    # Split JD text into sections if possible
    lower_text = cleaned.lower()
    req_index = lower_text.find("requirement")
    pref_index = lower_text.find("preferred") if "preferred" in lower_text else lower_text.find("nice to have")

    if pref_index != -1 and req_index != -1 and pref_index > req_index:
        req_text = cleaned[req_index:pref_index]
        pref_text = cleaned[pref_index:]
        req_skills = [s["skill"] for s in extract_skills(req_text)]
        pref_skills = [s["skill"] for s in extract_skills(pref_text)]
    
    if not req_skills:
        req_skills = skill_names[:max(1, len(skill_names) // 2)]
        pref_skills = skill_names[max(1, len(skill_names) // 2):]

    # Extract general keywords
    words = re.findall(r'\b[a-zA-Z]{3,}\b', cleaned.lower())
    common_words = {"and", "the", "for", "with", "you", "will", "our", "are", "have", "this", "that", "from", "team", "work", "job", "role"}
    filtered_words = [w for w in words if w not in common_words]
    
    # Value counts for keywords
    from collections import Counter
    top_keywords = [w.capitalize() for w, _ in Counter(filtered_words).most_common(15)]

    # Education detection
    education = "Bachelor's Degree"
    if "master" in lower_text or "m.s" in lower_text or "phd" in lower_text:
        education = "Master's / Ph.D."
    elif "high school" in lower_text or "associate" in lower_text:
        education = "Associate / Diploma"

    return ParsedJobDescription(
        raw_text=jd_text,
        clean_text=cleaned,
        role_title=role_title,
        extracted_skills=skill_names,
        skill_details=skills_data,
        required_skills=req_skills,
        preferred_skills=pref_skills,
        estimated_yoe=estimated_yoe,
        required_education=education,
        keywords=top_keywords,
    )


def parse_jd_file(file_path: Path) -> ParsedJobDescription:
    """Extract text from a Job Description PDF file and parse it."""
    extraction = extract_text_from_pdf(file_path)
    raw_text = extraction["raw_text"]
    return parse_jd_text(raw_text)
