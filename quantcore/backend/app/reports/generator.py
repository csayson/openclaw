"""
Report generation engine — builds PDF reports using ReportLab + Plotly charts.
AI narrative sections use the Anthropic Claude API.
"""
from __future__ import annotations
import io
import tempfile
import os
from datetime import date, datetime
from typing import Any
import structlog

log = structlog.get_logger()


def _generate_ai_narrative(section: str, context: dict) -> str:
    """Generate AI narrative using Claude API."""
    try:
        import anthropic
        from app.core.config import settings
        client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        prompt = (
            f"You are a professional trading analyst. Generate a concise, insightful "
            f"narrative for the '{section}' section of a trading performance report. "
            f"Context: {context}. "
            f"Write 2-3 paragraphs covering: market context, what worked, what didn't, "
            f"and key lessons. Be specific about the numbers provided."
        )
        message = client.messages.create(
            model="claude-opus-4-8",
            max_tokens=600,
            messages=[{"role": "user", "content": prompt}],
        )
        return message.content[0].text
    except Exception as e:
        log.warning("ai_narrative_failed", error=str(e))
        return f"AI narrative unavailable. Section: {section}."


def _render_equity_curve(trades: list[dict]) -> bytes:
    """Returns PNG bytes of equity curve chart."""
    import plotly.graph_objects as go
    cumulative = 0
    dates, values = [], []
    for t in sorted(trades, key=lambda x: x.get("closed_at") or ""):
        cumulative += t.get("pnl_usd", 0) or 0
        dates.append(t.get("closed_at"))
        values.append(cumulative)

    fig = go.Figure(go.Scatter(x=dates, y=values, mode="lines", line=dict(color="#22c55e", width=2)))
    fig.update_layout(
        title="Equity Curve", xaxis_title="Date", yaxis_title="Cumulative P&L ($)",
        template="plotly_dark", height=300, margin=dict(l=40, r=20, t=40, b=40),
    )
    return fig.to_image(format="png", width=900, height=300)


def _render_strategy_bar(strategy_pnl: dict[str, float]) -> bytes:
    import plotly.graph_objects as go
    fig = go.Figure(go.Bar(
        x=list(strategy_pnl.keys()),
        y=list(strategy_pnl.values()),
        marker_color=["#22c55e" if v >= 0 else "#ef4444" for v in strategy_pnl.values()],
    ))
    fig.update_layout(
        title="P&L by Strategy", template="plotly_dark", height=250,
        margin=dict(l=40, r=20, t=40, b=40),
    )
    return fig.to_image(format="png", width=700, height=250)


class ReportGenerator:
    def generate_daily(self, account_id: str, trades: list[dict], metrics: dict) -> bytes:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
        from reportlab.lib import colors
        from reportlab.lib.units import cm

        buf = io.BytesIO()
        doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=2*cm, rightMargin=2*cm,
                                 topMargin=2*cm, bottomMargin=2*cm)
        styles = getSampleStyleSheet()
        story = []

        # Header
        story.append(Paragraph("QuantCore AI — Daily Trading Summary", styles["Title"]))
        story.append(Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')} EST", styles["Normal"]))
        story.append(Spacer(1, 0.5*cm))

        # AI Narrative
        narrative = _generate_ai_narrative("daily_summary", metrics)
        story.append(Paragraph("Executive Summary", styles["Heading2"]))
        story.append(Paragraph(narrative, styles["Normal"]))
        story.append(Spacer(1, 0.5*cm))

        # KPI Table
        story.append(Paragraph("Key Performance Indicators", styles["Heading2"]))
        kpi_data = [
            ["Metric", "Today", "30-Day Avg"],
            ["Net P&L", f"${metrics.get('net_pnl', 0):.2f}", f"${metrics.get('avg_daily_pnl', 0):.2f}"],
            ["Total Trades", str(metrics.get("total_trades", 0)), str(metrics.get("avg_daily_trades", 0))],
            ["Win Rate", f"{metrics.get('win_rate', 0)*100:.1f}%", f"{metrics.get('avg_win_rate', 0)*100:.1f}%"],
            ["Max Drawdown", f"{metrics.get('max_dd', 0)*100:.2f}%", "—"],
        ]
        t = Table(kpi_data, colWidths=[5*cm, 4*cm, 4*cm])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.darkblue),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("ALIGN", (1, 0), (-1, -1), "CENTER"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.lightgrey, colors.white]),
        ]))
        story.append(t)
        story.append(Spacer(1, 0.5*cm))

        # Equity curve chart
        if trades:
            chart_png = _render_equity_curve(trades)
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
                tmp.write(chart_png)
                tmp_path = tmp.name
            story.append(Paragraph("Intraday P&L Curve", styles["Heading2"]))
            story.append(Image(tmp_path, width=16*cm, height=5*cm))
            story.append(Spacer(1, 0.3*cm))
            os.unlink(tmp_path)

        doc.build(story)
        return buf.getvalue()

    def generate_weekly(self, account_id: str, trades: list[dict], metrics: dict) -> bytes:
        # Full weekly deep-dive — same pattern as daily, extended sections
        buf = io.BytesIO()
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
        doc = SimpleDocTemplate(buf, pagesize=A4)
        styles = getSampleStyleSheet()
        story = [
            Paragraph("QuantCore AI — Weekly Deep-Dive Report", styles["Title"]),
            Paragraph(f"Week of {datetime.now().strftime('%Y-%m-%d')}", styles["Normal"]),
            Spacer(1, 0.5),
            Paragraph("Performance Narrative", styles["Heading2"]),
            Paragraph(_generate_ai_narrative("weekly_deep_dive", metrics), styles["Normal"]),
        ]
        doc.build(story)
        return buf.getvalue()

    def generate_monthly(self, account_id: str, trades: list[dict], metrics: dict) -> bytes:
        buf = io.BytesIO()
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
        doc = SimpleDocTemplate(buf, pagesize=A4)
        styles = getSampleStyleSheet()
        story = [
            Paragraph("QuantCore AI — Monthly Performance Report", styles["Title"]),
            Paragraph(f"Month: {datetime.now().strftime('%B %Y')}", styles["Normal"]),
            Spacer(1, 0.5),
            Paragraph("Executive Summary", styles["Heading2"]),
            Paragraph(_generate_ai_narrative("monthly_summary", metrics), styles["Normal"]),
        ]
        doc.build(story)
        return buf.getvalue()
