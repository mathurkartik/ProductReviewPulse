"""Phase 4: Render HTML and plain-text emails using Jinja2."""

from __future__ import annotations

from pathlib import Path
from jinja2 import Environment, FileSystemLoader

from agent.summarization_models import PulseSummary

def render_emails(summary: PulseSummary, product_name: str, doc_link: str = "{DOC_DEEP_LINK}") -> tuple[str, str]:
    """Render the email HTML and plain text using Jinja2 templates.
    Returns (html_content, text_content).
    """
    template_dir = Path(__file__).parent.parent.parent / "templates"
    env = Environment(loader=FileSystemLoader(str(template_dir)))
    
    html_template = env.get_template("email.html.j2")
    txt_template = env.get_template("email.txt.j2")
    
    html_content = html_template.render(
        product_name=product_name,
        iso_week=summary.iso_week,
        themes=summary.themes,
        doc_link=doc_link
    )
    
    txt_content = txt_template.render(
        product_name=product_name,
        iso_week=summary.iso_week,
        themes=summary.themes,
        doc_link=doc_link
    )
    
    return html_content, txt_content
