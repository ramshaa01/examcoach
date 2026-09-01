"""PDF Progress Report Generator using ReportLab."""
from __future__ import annotations

import datetime as dt
import io
from typing import Any, Dict, List

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import HRFlowable, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from db.models import Attempt, MockExamResult, TopicMastery


def generate_pdf_report(
    username: str,
    analytics_data: Dict[str, Any],
) -> bytes:
    """Generates a downloadable PDF progress summary report."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "ReportTitle",
        parent=styles["Heading1"],
        fontSize=22,
        textColor=colors.HexColor("#4f46e5"),
        spaceAfter=6,
    )
    sub_style = ParagraphStyle(
        "ReportSub",
        parent=styles["Normal"],
        fontSize=10,
        textColor=colors.HexColor("#64748b"),
        spaceAfter=14,
    )
    h2_style = ParagraphStyle(
        "ReportH2",
        parent=styles["Heading2"],
        fontSize=13,
        textColor=colors.HexColor("#1e293b"),
        spaceBefore=12,
        spaceAfter=6,
    )
    body_style = ParagraphStyle(
        "ReportBody",
        parent=styles["Normal"],
        fontSize=9,
        textColor=colors.HexColor("#334155"),
        spaceAfter=4,
    )

    story = []

    # Title & Header
    story.append(Paragraph("🎓 ExamCoach AI - Student Performance Report", title_style))
    story.append(Paragraph(f"Student: <b>{username}</b> | Generated on: {dt.datetime.now().strftime('%d %B %Y, %H:%M')}", sub_style))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#e2e8f0"), spaceAfter=12))

    # High-level KPIs table
    total = analytics_data.get("total_attempts", 0)
    acc = analytics_data.get("accuracy", 0.0)
    avg_s = analytics_data.get("avg_score", 0.0)

    kpi_data = [
        ["Total Questions", "Accuracy Rate", "Average Score (out of 10)"],
        [str(total), f"{acc}%", f"{avg_s} / 10"],
    ]
    t_kpi = Table(kpi_data, colWidths=[170, 170, 170])
    t_kpi.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f1f5f9")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#475569")),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("BACKGROUND", (0, 1), (-1, 1), colors.HexColor("#ffffff")),
        ("TEXTCOLOR", (0, 1), (-1, 1), colors.HexColor("#0f172a")),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ("PADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(t_kpi)
    story.append(Spacer(1, 14))

    # Weak Topics
    story.append(Paragraph("📌 Identified Areas of Improvement", h2_style))
    mastery_list: List[TopicMastery] = analytics_data.get("mastery", [])
    weak_topics = [m for m in mastery_list if m.is_weak or m.mastery_score < 60.0]

    if weak_topics:
        weak_table_data = [["Topic", "Subject", "Attempts", "Mastery %"]]
        for wt in weak_topics[:8]:
            weak_table_data.append([
                wt.topic,
                wt.subject,
                str(wt.total_count),
                f"{wt.mastery_score}%",
            ])
        t_weak = Table(weak_table_data, colWidths=[200, 130, 80, 100])
        t_weak.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#fee2e2")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#991b1b")),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#fca5a5")),
            ("PADDING", (0, 0), (-1, -1), 5),
        ]))
        story.append(t_weak)
    else:
        story.append(Paragraph("No weak topics identified yet. Keep practicing to discover target areas!", body_style))

    story.append(Spacer(1, 14))

    # Recent Attempts
    story.append(Paragraph("📝 Recent Practice Questions", h2_style))
    attempts: List[Attempt] = analytics_data.get("attempts", [])
    if attempts:
        att_data = [["Subject / Topic", "Difficulty", "Score", "Verdict", "Error Type"]]
        for a in attempts[-5:]:
            att_data.append([
                Paragraph(f"<b>{a.subject}</b><br/>{a.topic}", body_style),
                a.difficulty,
                f"{a.score}/10",
                "✓ Correct" if a.is_correct else "✗ Needs Work",
                a.error_type or "None",
            ])
        t_att = Table(att_data, colWidths=[180, 100, 60, 80, 90])
        t_att.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f8fafc")),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
            ("PADDING", (0, 0), (-1, -1), 4),
        ]))
        story.append(t_att)

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()
