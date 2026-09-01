"""Plotly interactive charts for topic mastery radar, accuracy trends, and error distribution."""
from __future__ import annotations

from typing import Any, Dict, List, Optional

import plotly.express as px
import plotly.graph_objects as go
from sqlalchemy.orm import Session

from db.database import get_session
from db.models import Attempt, MockExamResult, TopicMastery


def get_user_analytics_data(user_id: Optional[int]) -> Dict[str, Any]:
    """Fetches attempt history, mastery scores, and mock exam results for a user."""
    if not user_id:
        return {
            "attempts": [],
            "mastery": [],
            "mock_results": [],
            "total_attempts": 0,
            "accuracy": 0.0,
            "avg_score": 0.0,
        }

    with get_session() as session:
        attempts = session.query(Attempt).filter(Attempt.user_id == user_id).order_by(Attempt.created_at.asc()).all()
        mastery = session.query(TopicMastery).filter(TopicMastery.user_id == user_id).all()
        mocks = session.query(MockExamResult).filter(MockExamResult.user_id == user_id).all()

        total = len(attempts)
        correct = sum(1 for a in attempts if a.is_correct)
        accuracy = round((correct / total) * 100.0, 1) if total > 0 else 0.0
        avg_score = round(sum(a.score for a in attempts) / total, 1) if total > 0 else 0.0

        return {
            "attempts": attempts,
            "mastery": mastery,
            "mock_results": mocks,
            "total_attempts": total,
            "correct_attempts": correct,
            "accuracy": accuracy,
            "avg_score": avg_score,
        }


def create_mastery_radar_chart(mastery_records: List[TopicMastery]) -> Optional[go.Figure]:
    """Generates a Plotly Radar/Polar chart of Topic Mastery scores (0-100%)."""
    if not mastery_records:
        return None

    # Take top 8 topics for readability
    subset = mastery_records[:8]
    categories = [m.topic for m in subset]
    scores = [m.mastery_score for m in subset]

    # Close the polygon loop
    categories.append(categories[0])
    scores.append(scores[0])

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=scores,
        theta=categories,
        fill="toself",
        fillcolor="rgba(99, 102, 241, 0.35)",
        line=dict(color="#818cf8", width=2),
        name="Topic Mastery",
    ))

    fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 100], color="#94a3b8", gridcolor="rgba(255,255,255,0.1)"),
            angularaxis=dict(color="#e2e8f0", gridcolor="rgba(255,255,255,0.1)"),
            bgcolor="rgba(15, 23, 42, 0.4)",
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=30, r=30, t=30, b=30),
        showlegend=False,
        height=320,
    )
    return fig


def create_accuracy_trend_chart(attempts: List[Attempt]) -> Optional[go.Figure]:
    """Generates a rolling accuracy trend line chart over chronological attempts."""
    if not attempts:
        return None

    x_vals = list(range(1, len(attempts) + 1))
    scores = [a.score for a in attempts]
    
    # Calculate rolling 5-attempt accuracy
    rolling_acc = []
    for i in range(len(attempts)):
        window = attempts[max(0, i - 4): i + 1]
        acc = (sum(1 for a in window if a.is_correct) / len(window)) * 100.0
        rolling_acc.append(round(acc, 1))

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=x_vals,
        y=rolling_acc,
        mode="lines+markers",
        name="Rolling Accuracy (%)",
        line=dict(color="#06b6d4", width=3),
        marker=dict(size=6, color="#38bdf8"),
    ))

    fig.update_layout(
        xaxis=dict(title="Attempt Number", color="#94a3b8", gridcolor="rgba(255,255,255,0.08)"),
        yaxis=dict(title="Accuracy (%)", range=[0, 105], color="#94a3b8", gridcolor="rgba(255,255,255,0.08)"),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=20, r=20, t=20, b=20),
        height=280,
        font=dict(color="#e2e8f0"),
    )
    return fig


def create_error_distribution_chart(attempts: List[Attempt]) -> Optional[go.Figure]:
    """Generates a Donut chart showing distribution of student error categories."""
    if not attempts:
        return None

    errors = [a.error_type for a in attempts if a.error_type and a.error_type.lower() != "none"]
    if not errors:
        return None

    counts: Dict[str, int] = {}
    for err in errors:
        counts[err] = counts.get(err, 0) + 1

    fig = go.Figure(data=[go.Pie(
        labels=list(counts.keys()),
        values=list(counts.values()),
        hole=0.55,
        marker=dict(colors=["#ef4444", "#f59e0b", "#8b5cf6", "#ec4899", "#3b82f6"]),
        textinfo="label+percent",
        textfont=dict(color="#ffffff"),
    )])

    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=20, r=20, t=20, b=20),
        height=280,
        showlegend=False,
    )
    return fig
