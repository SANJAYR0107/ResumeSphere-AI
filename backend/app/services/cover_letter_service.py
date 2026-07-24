"""
cover_letter_service.py - Phase C AI Cover Letter Generator & PDF Export Service

Purpose
-------
Generates tailored, professional cover letters for Internship, Fresher, Experienced,
and Career Change candidates. Supports PDF generation with ReportLab.
"""

import io
import logging
from typing import TypedDict, Any

from reportlab.lib import colors  # type: ignore[import-untyped]
from reportlab.lib.pagesizes import letter  # type: ignore[import-untyped]
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet  # type: ignore[import-untyped]
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer  # type: ignore[import-untyped]

logger = logging.getLogger(__name__)


class GeneratedCoverLetter(TypedDict):
    candidate_name: str
    target_role: str
    company_name: str
    experience_type: str
    cover_letter_text: str


def generate_cover_letter(
    candidate_name: str = "Jane Doe",
    target_role: str = "Software Engineer",
    company_name: str = "Tech Corporation",
    experience_type: str = "Experienced",
    resume_skills: list[str] | None = None,
    jd_text: str | None = None
) -> GeneratedCoverLetter:
    """Generate a structured, professional cover letter tailored to role and experience level."""
    name = candidate_name.strip() or "Candidate"
    role = target_role.strip() or "Software Engineer"
    company = company_name.strip() or "Tech Corporation"
    skills_str = ", ".join((resume_skills or ["Java", "Spring Boot", "SQL"])[:4])

    if experience_type == "Fresher":
        text = (
            f"Dear Hiring Manager,\n\n"
            f"I am writing to express my strong enthusiasm for the {role} position at {company}. "
            f"As a recent graduate equipped with a solid foundation in {skills_str}, I am eager to contribute my technical knowledge "
            f"and passion for software engineering to your development team.\n\n"
            f"During my academic coursework and personal projects, I successfully engineered scalable applications, "
            f"emphasizing clean architecture, automated testing, and optimal algorithm efficiency. "
            f"My hands-on experience with {skills_str} enables me to quickly adapt and add value to {company}'s ongoing initiatives.\n\n"
            f"I am deeply inspired by {company}'s commitment to engineering innovation and would welcome the opportunity to discuss "
            f"how my background aligns with your team's goals.\n\n"
            f"Sincerely,\n"
            f"{name}"
        )
    elif experience_type == "Internship":
        text = (
            f"Dear Hiring Manager,\n\n"
            f"I am excited to apply for the {role} Internship opportunity at {company}. "
            f"With a strong academic record and hands-on project experience in {skills_str}, "
            f"I am eager to apply my technical problem-solving skills in a high-impact professional setting.\n\n"
            f"Through my coursework and open-source contributions, I have developed a keen interest in building efficient software solutions. "
            f"I am particularly drawn to {company}'s engineering culture and look forward to contributing while expanding my industry skills.\n\n"
            f"Thank you for considering my application.\n\n"
            f"Sincerely,\n"
            f"{name}"
        )
    else:  # Experienced / Career Change
        text = (
            f"Dear Hiring Manager,\n\n"
            f"I am writing to submit my application for the {role} role at {company}. "
            f"With proven experience architecting scalable systems and leveraging expertise in {skills_str}, "
            f"I have a track record of driving system performance, reducing latency, and delivering business value.\n\n"
            f"In my previous work, I spearheaded key technical initiatives that improved application throughput and system reliability. "
            f"I am confident that my technical mastery of {skills_str} and collaborative leadership will make an immediate impact at {company}.\n\n"
            f"I would welcome the opportunity to discuss how my technical expertise can support {company}'s growth objectives.\n\n"
            f"Sincerely,\n"
            f"{name}"
        )

    return GeneratedCoverLetter(
        candidate_name=name,
        target_role=role,
        company_name=company,
        experience_type=experience_type,
        cover_letter_text=text
    )


def generate_cover_letter_pdf(cover_letter_data: dict[str, Any]) -> bytes:
    """Generate a downloadable PDF cover letter using ReportLab."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=50,
        leftMargin=50,
        topMargin=50,
        bottomMargin=50
    )

    styles = getSampleStyleSheet()

    header_style = ParagraphStyle(
        'HeaderStyle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=18,
        leading=22,
        textColor=colors.HexColor('#0f172a'),
        spaceAfter=15
    )

    body_style = ParagraphStyle(
        'BodyStyle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10.5,
        leading=16,
        textColor=colors.HexColor('#334155'),
        spaceAfter=12
    )

    story = []

    name = cover_letter_data.get("candidate_name", "Candidate Name")
    story.append(Paragraph(f"<b>{name}</b>", header_style))
    story.append(Spacer(1, 10))

    text = cover_letter_data.get("cover_letter_text", "")
    paragraphs = text.split("\n\n")
    for p in paragraphs:
        if p.strip():
            formatted_p = p.replace("\n", "<br/>")
            story.append(Paragraph(formatted_p, body_style))
            story.append(Spacer(1, 6))

    doc.build(story)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes
