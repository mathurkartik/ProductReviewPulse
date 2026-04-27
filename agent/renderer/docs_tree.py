"""Phase 4: Transform PulseSummary into Google Docs batchUpdate requests."""

from __future__ import annotations

from typing import Any

from agent.summarization_models import PulseSummary


def generate_doc_requests(
    summary: PulseSummary, product_display_name: str, start_index: int = 1
) -> list[dict[str, Any]]:
    """Generate a list of Google Docs batchUpdate requests for the summary.

    Appends elements starting from `start_index`.
    """
    requests = []
    current_idx = start_index

    # Optional: Insert a page break before the new section if not at the very top
    if current_idx > 1:
        requests.append({"insertPageBreak": {"location": {"index": current_idx}}})
        current_idx += 1  # Page breaks consume 1 index

    iso_week_str = f"{summary.window.end.year}-W{summary.window.end.isocalendar()[1]:02d}"

    # Heading 1: Title with anchor
    anchor = f"[pulse-{summary.product}-{iso_week_str}]"
    title_text = f"{product_display_name} — Weekly Review Pulse  |  {iso_week_str}  {anchor}\n"

    requests.append({"insertText": {"location": {"index": current_idx}, "text": title_text}})
    requests.append(
        {
            "updateParagraphStyle": {
                "range": {"startIndex": current_idx, "endIndex": current_idx + len(title_text)},
                "paragraphStyle": {"namedStyleType": "HEADING_1"},
                "fields": "namedStyleType",
            }
        }
    )
    current_idx += len(title_text)

    # Heading 2: Top Themes
    themes_header = "Top Themes\n"
    requests.append({"insertText": {"location": {"index": current_idx}, "text": themes_header}})
    requests.append(
        {
            "updateParagraphStyle": {
                "range": {"startIndex": current_idx, "endIndex": current_idx + len(themes_header)},
                "paragraphStyle": {"namedStyleType": "HEADING_2"},
                "fields": "namedStyleType",
            }
        }
    )
    current_idx += len(themes_header)

    for i, theme in enumerate(summary.top_themes, 1):
        # Paragraph (Normal): "{n}. {theme_name} — {theme_summary}"
        theme_text = f"{i}. {theme.label} — {theme.description}\n"
        requests.append({"insertText": {"location": {"index": current_idx}, "text": theme_text}})
        requests.append(
            {
                "updateParagraphStyle": {
                    "range": {"startIndex": current_idx, "endIndex": current_idx + len(theme_text)},
                    "paragraphStyle": {"namedStyleType": "NORMAL_TEXT"},
                    "fields": "namedStyleType",
                }
            }
        )
        current_idx += len(theme_text)

    # Heading 2: Real User Quotes
    quotes_header = "Real User Quotes\n"
    requests.append({"insertText": {"location": {"index": current_idx}, "text": quotes_header}})
    requests.append(
        {
            "updateParagraphStyle": {
                "range": {"startIndex": current_idx, "endIndex": current_idx + len(quotes_header)},
                "paragraphStyle": {"namedStyleType": "HEADING_2"},
                "fields": "namedStyleType",
            }
        }
    )
    current_idx += len(quotes_header)

    for quote in summary.quotes:
        # Paragraph (Italic): '"{quote_text}"'
        quote_text = f'"{quote.text}" ({quote.source}, {quote.rating}★)\n'
        requests.append({"insertText": {"location": {"index": current_idx}, "text": quote_text}})
        requests.append(
            {
                "updateParagraphStyle": {
                    "range": {"startIndex": current_idx, "endIndex": current_idx + len(quote_text)},
                    "paragraphStyle": {"namedStyleType": "NORMAL_TEXT"},
                    "fields": "namedStyleType",
                }
            }
        )
        requests.append(
            {
                "updateTextStyle": {
                    "range": {"startIndex": current_idx, "endIndex": current_idx + len(quote_text)},
                    "textStyle": {"italic": True},
                    "fields": "italic",
                }
            }
        )
        current_idx += len(quote_text)

    # Heading 2: Action Ideas
    action_header = "Action Ideas\n"
    requests.append({"insertText": {"location": {"index": current_idx}, "text": action_header}})
    requests.append(
        {
            "updateParagraphStyle": {
                "range": {"startIndex": current_idx, "endIndex": current_idx + len(action_header)},
                "paragraphStyle": {"namedStyleType": "HEADING_2"},
                "fields": "namedStyleType",
            }
        }
    )
    current_idx += len(action_header)

    for action in summary.action_ideas:
        # Paragraph (Normal): "• {action_title}: {action_description}"
        action_text = f"• {action.title}: {action.description}\n"
        requests.append({"insertText": {"location": {"index": current_idx}, "text": action_text}})
        requests.append(
            {
                "updateParagraphStyle": {
                    "range": {
                        "startIndex": current_idx,
                        "endIndex": current_idx + len(action_text),
                    },
                    "paragraphStyle": {"namedStyleType": "NORMAL_TEXT"},
                    "fields": "namedStyleType",
                }
            }
        )
        # Note: could use createParagraphBullets, but bullet char is fine for MVP
        current_idx += len(action_text)

    # Heading 2: What This Solves
    who_header = "What This Solves\n"
    requests.append({"insertText": {"location": {"index": current_idx}, "text": who_header}})
    requests.append(
        {
            "updateParagraphStyle": {
                "range": {"startIndex": current_idx, "endIndex": current_idx + len(who_header)},
                "paragraphStyle": {"namedStyleType": "HEADING_2"},
                "fields": "namedStyleType",
            }
        }
    )
    current_idx += len(who_header)

    # What This Solves - Simple text format instead of table to avoid index issues
    # Use simple text format: "Audience: Value"
    for w in summary.what_this_solves:
        solve_text = f"• {w.audience}: {w.value}\n"
        requests.append({"insertText": {"location": {"index": current_idx}, "text": solve_text}})
        requests.append(
            {
                "updateParagraphStyle": {
                    "range": {"startIndex": current_idx, "endIndex": current_idx + len(solve_text)},
                    "paragraphStyle": {"namedStyleType": "NORMAL_TEXT"},
                    "fields": "namedStyleType",
                }
            }
        )
        current_idx += len(solve_text)

    return requests
