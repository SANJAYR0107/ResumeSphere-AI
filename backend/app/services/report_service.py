"""
report_service.py - Phase 4 Downloadable PDF Report Service

Purpose
-------
Generates a downloadable PDF report summarizing the Phase 4 Optimization Engine
results (Scores, Keyword Breakdown, ATS Suggestions, Rewrites, Interview Prep,
Executive Summary) using ReportLab.
"""

import io
import logging
from typing import Any

from reportlab.lib import colors  # type: ignore[import-untyped]
from reportlab.lib.pagesizes import letter  # type: ignore[import-untyped]
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet  # type: ignore[import-untyped]
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle  # type: ignore[import-untyped]

logger = logging.getLogger(__name__)


def generate_pdf_report(analysis_data: dict[str, Any]) -> bytes:
    """Generate a PDF report from Phase 4 optimization analysis data.

    Returns raw bytes suitable for streaming as an application/pdf attachment.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40
    )

    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        textColor=colors.HexColor('#0f172a'),
        alignment=0,
        spaceAfter=10
    )

    subtitle_style = ParagraphStyle(
        'DocSubTitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#64748b'),
        spaceAfter=15
    )

    h2_style = ParagraphStyle(
        'SectionHeader',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=14,
        leading=18,
        textColor=colors.HexColor('#1e293b'),
        spaceBefore=12,
        spaceAfter=8
    )

    body_style = ParagraphStyle(
        'BodyTextCustom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=13,
        textColor=colors.HexColor('#334155'),
        spaceAfter=6
    )

    bullet_style = ParagraphStyle(
        'BulletCustom',
        parent=body_style,
        leftIndent=12,
        spaceAfter=4
    )

    story = []

    # Title Banner
    story.append(Paragraph("ResumeSphere AI — Optimization Report", title_style))
    role_title = analysis_data.get("role_title", "Target Job Role")
    story.append(Paragraph(f"Target Role: <b>{role_title}</b> | Generated on Phase 4 Optimization Engine", subtitle_style))
    story.append(Spacer(1, 5))

    # 1. Match Summary Table
    match_data = analysis_data.get("match_scores", {})
    overall_match = match_data.get("overall_match", 85)
    ats_match = match_data.get("ats_match", 80)
    semantic_match = match_data.get("semantic_match", 88)
    keyword_match = match_data.get("keyword_match", 75)
    confidence = match_data.get("confidence", "High")

    table_data = [
        ["Overall Match", "ATS Match", "Semantic Match", "Keyword Match", "Confidence Level"],
        [f"{overall_match}%", f"{ats_match}%", f"{semantic_match}%", f"{keyword_match}%", confidence]
    ]

    t = Table(table_data, colWidths=[105, 105, 105, 105, 105])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e293b')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9.5),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BACKGROUND', (0, 1), (-1, 1), colors.HexColor('#f8fafc')),
        ('TEXTCOLOR', (0, 1), (-1, 1), colors.HexColor('#0f172a')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
    ]))
    story.append(t)
    story.append(Spacer(1, 12))

    # 2. Executive Summary
    exec_summary = analysis_data.get("executive_summary", {})
    readiness = exec_summary.get("hiring_readiness", "Moderate Readiness")
    rec = exec_summary.get("overall_recommendation", "Application recommended after applying key rewrites.")
    
    story.append(Paragraph("Executive Summary", h2_style))
    story.append(Paragraph(f"<b>Hiring Readiness:</b> <font color='#2563eb'>{readiness}</font>", body_style))
    story.append(Paragraph(f"<b>Assessment:</b> {rec}", body_style))
    
    story.append(Spacer(1, 6))

    # 3. Keyword Breakdown
    kw_data = analysis_data.get("keyword_analysis", {})
    matched_kws = ", ".join(kw_data.get("matched_keywords", [])[:8]) or "None"
    missing_kws = ", ".join(kw_data.get("missing_keywords", [])[:8]) or "None"
    important_missing = ", ".join(kw_data.get("important_missing_keywords", [])[:5]) or "None"

    story.append(Paragraph("Keyword Analysis", h2_style))
    story.append(Paragraph(f"<b>Matched Keywords:</b> <font color='#16a34a'>{matched_kws}</font>", body_style))
    story.append(Paragraph(f"<b>Missing Keywords:</b> <font color='#dc2626'>{missing_kws}</font>", body_style))
    story.append(Paragraph(f"<b>Important Missing (High Priority):</b> <font color='#b91c1c'><b>{important_missing}</b></font>", body_style))
    story.append(Spacer(1, 6))

    # 4. ATS Optimization & Simulator
    sim_data = analysis_data.get("ats_simulator", {})
    curr_score = sim_data.get("current_ats_score", 70)
    pred_score = sim_data.get("predicted_ats_score", 88)
    delta = sim_data.get("expected_improvement", 18)

    story.append(Paragraph("ATS Improvement Simulator", h2_style))
    story.append(Paragraph(f"Current ATS Score: <b>{curr_score}/100</b> &nbsp;|&nbsp; Predicted Score: <b><font color='#2563eb'>{pred_score}/100</font></b> &nbsp;|&nbsp; Expected Gain: <b><font color='#16a34a'>+{delta} Points</font></b>", body_style))

    # Suggestions list
    ats_suggs = analysis_data.get("ats_suggestions", [])
    if ats_suggs:
        story.append(Spacer(1, 4))
        story.append(Paragraph("<b>Top ATS Optimization Actions:</b>", body_style))
        for sug in ats_suggs[:4]:
            text = f"• [{sug.get('category', 'Action')}] {sug.get('suggestion', '')} - {sug.get('explanation', '')}"
            story.append(Paragraph(text, bullet_style))

    story.append(Spacer(1, 8))

    # 5. Professional Summary Rewrite Suggestion
    rewrites = analysis_data.get("rewrite_suggestions", {})
    summary_rewrite = rewrites.get("professional_summary", "")
    if summary_rewrite:
        story.append(Paragraph("Recommended Professional Summary Rewrite", h2_style))
        story.append(Paragraph(f"<i>\"{summary_rewrite}\"</i>", body_style))
        story.append(Spacer(1, 8))

    # 6. Interview Preparation & Topics
    interview_data = analysis_data.get("interview_alignment", {})
    questions = interview_data.get("technical_questions", [])
    if questions:
        story.append(Paragraph("Likely Technical Interview Questions", h2_style))
        for q in questions[:3]:
            story.append(Paragraph(f"• {q}", bullet_style))

    doc.build(story)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes
