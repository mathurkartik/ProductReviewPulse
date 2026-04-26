"""Phase 4: Render HTML and plain-text emails using Jinja2."""

from __future__ import annotations

from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from agent.summarization_models import PulseSummary


def render_emails(
    summary: PulseSummary, product_name: str, doc_link: str = "{DOC_DEEP_LINK}", dashboard_link: str = ""
) -> tuple[str, str]:
    """Render the email HTML and plain text using Jinja2 templates.
    Returns (html_content, text_content).
    """
    template_dir = Path(__file__).parent.parent.parent / "templates"
    env = Environment(loader=FileSystemLoader(str(template_dir)))

    html_template = env.get_template("email.html.j2")
    txt_template = env.get_template("email.txt.j2")

    iso_week_str = f"{summary.window.end.year}-W{summary.window.end.isocalendar()[1]:02d}"
    
    # Prepare template data
    template_data = {
        "product_name": product_name,
        "iso_week": iso_week_str,
        "window_start": summary.window.start.strftime("%b %d"),
        "window_end": summary.window.end.strftime("%b %d, %Y"),
        "total_reviews": summary.stats.total_reviews,
        "avg_rating": f"{summary.stats.avg_rating:.1f}",
        "themes": summary.top_themes,
        "action_ideas": summary.action_ideas,
        "quotes": summary.quotes,
        "doc_link": doc_link,
        "dashboard_link": dashboard_link,
    }

    html_content = html_template.render(**template_data)
    txt_content = txt_template.render(**template_data)

    return html_content, txt_content
