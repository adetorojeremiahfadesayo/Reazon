import os
import re
from typing import Optional

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

from src.config import (
    REPORTS_DIR, LearnerProfile, StudyPlan, ReadinessReport, ExamBadge
)


def _safe_filename(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", value).strip("_")


def _doc(path: str):
    return SimpleDocTemplate(path, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)


def export_study_plan_pdf(profile: LearnerProfile, plan: StudyPlan, output_dir: Optional[str] = None) -> str:
    output_dir = output_dir or REPORTS_DIR
    os.makedirs(output_dir, exist_ok=True)
    path = os.path.join(output_dir, f"{_safe_filename(profile.learner_id)}_{plan.certification_target}_study_plan.pdf")
    styles = getSampleStyleSheet()
    story = [
        Paragraph("Reazon Internship Development Program", styles["Title"]),
        Paragraph(f"Study Plan: {profile.name} - {plan.certification_target}", styles["Heading2"]),
        Paragraph(f"Role: {profile.role}", styles["Normal"]),
        Paragraph(f"Total: {plan.total_hours} hours across {plan.total_weeks} weeks", styles["Normal"]),
        Spacer(1, 12),
    ]
    rows = [["Week", "Hours", "Focus Domains", "Workload Note"]]
    for week in plan.schedule:
        rows.append([
            str(week.week_number),
            str(week.hours_allocated),
            ", ".join(week.focus_domains),
            week.adjustment_reason or "Standard workload"
        ])
    table = Table(rows, colWidths=[42, 42, 220, 210])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f2937")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    story.append(table)
    _doc(path).build(story)
    return path


def export_readiness_pdf(profile: LearnerProfile, report: ReadinessReport, output_dir: Optional[str] = None) -> str:
    output_dir = output_dir or REPORTS_DIR
    os.makedirs(output_dir, exist_ok=True)
    path = os.path.join(output_dir, f"{_safe_filename(profile.learner_id)}_{report.certification_target}_readiness.pdf")
    styles = getSampleStyleSheet()
    story = [
        Paragraph("Intern Certification Readiness Report", styles["Title"]),
        Paragraph(f"{profile.name} - {report.certification_target}", styles["Heading2"]),
        Paragraph(f"Overall readiness: {report.overall_readiness}%", styles["Normal"]),
        Paragraph(f"Booking recommendation: {report.booking_recommendation}", styles["Normal"]),
        Paragraph(f"Remediation: {report.remediation_plan}", styles["Normal"]),
        Spacer(1, 12),
    ]
    rows = [["Domain", "Score"]]
    for domain, score in report.domain_scores.items():
        rows.append([domain, f"{score}%"])
    table = Table(rows, colWidths=[360, 100])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f2937")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
    ]))
    story.append(table)
    _doc(path).build(story)
    return path


def export_badge_pdf(badge: ExamBadge, output_dir: Optional[str] = None) -> str:
    output_dir = output_dir or REPORTS_DIR
    os.makedirs(output_dir, exist_ok=True)
    path = os.path.join(output_dir, f"{_safe_filename(badge.badge_id)}.pdf")
    styles = getSampleStyleSheet()
    story = [
        Paragraph("Internship Development Badge Certificate", styles["Title"]),
        Spacer(1, 18),
        Paragraph(badge.name, styles["Heading1"]),
        Paragraph(f"Issued to: {badge.issued_to}", styles["Heading2"]),
        Paragraph(f"Certification: {badge.certification_target}", styles["Normal"]),
        Paragraph(f"Score: {badge.score}%", styles["Normal"]),
        Paragraph(f"Criteria: {badge.criteria}", styles["Normal"]),
        Paragraph(f"Badge ID: {badge.badge_id}", styles["Normal"]),
        Spacer(1, 18),
        Paragraph("Synthetic internship credential. Not an official Microsoft certification.", styles["Italic"]),
    ]
    _doc(path).build(story)
    return path
