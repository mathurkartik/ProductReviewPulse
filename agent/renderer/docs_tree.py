"""Phase 4: Transform PulseSummary into Google Docs batchUpdate requests."""

from __future__ import annotations

from typing import Any

from agent.summarization_models import PulseSummary


def generate_doc_requests(summary: PulseSummary, product_display_name: str) -> list[dict[str, Any]]:
    """Generate a list of Google Docs batchUpdate requests for the summary.
    
    We generate requests assuming insertion at the top of the doc (index 1).
    Because we insert at index 1 repeatedly, we should insert the LAST element first
    so that when we insert the first element at index 1, it pushes everything else down.
    Alternatively, we can compute running lengths and insert sequentially.
    To match the MVP simplicity mentioned in the architecture, we will compute 
    sequential indices starting from 1.
    """
    requests = []
    current_idx = 1
    
    # Heading 1: Title with anchor
    anchor = f"[pulse-{summary.product_key}-{summary.iso_week}]"
    title_text = f"{product_display_name} — Weekly Review Pulse  |  {summary.iso_week}  {anchor}\n"
    
    requests.append({
        "insertText": {
            "location": {"index": current_idx},
            "text": title_text
        }
    })
    requests.append({
        "updateParagraphStyle": {
            "range": {"startIndex": current_idx, "endIndex": current_idx + len(title_text)},
            "paragraphStyle": {"namedStyleType": "HEADING_1"},
            "fields": "namedStyleType"
        }
    })
    current_idx += len(title_text)

    # Heading 2: Top Themes
    themes_header = "Top Themes\n"
    requests.append({
        "insertText": {
            "location": {"index": current_idx},
            "text": themes_header
        }
    })
    requests.append({
        "updateParagraphStyle": {
            "range": {"startIndex": current_idx, "endIndex": current_idx + len(themes_header)},
            "paragraphStyle": {"namedStyleType": "HEADING_2"},
            "fields": "namedStyleType"
        }
    })
    current_idx += len(themes_header)

    for i, theme in enumerate(summary.themes, 1):
        # Paragraph (Normal): "{n}. {theme_name} — {theme_summary}"
        theme_text = f"{i}. {theme.name} — {theme.summary}\n"
        requests.append({
            "insertText": {
                "location": {"index": current_idx},
                "text": theme_text
            }
        })
        requests.append({
            "updateParagraphStyle": {
                "range": {"startIndex": current_idx, "endIndex": current_idx + len(theme_text)},
                "paragraphStyle": {"namedStyleType": "NORMAL_TEXT"},
                "fields": "namedStyleType"
            }
        })
        current_idx += len(theme_text)

    # Heading 2: Real User Quotes
    quotes_header = "Real User Quotes\n"
    requests.append({
        "insertText": {
            "location": {"index": current_idx},
            "text": quotes_header
        }
    })
    requests.append({
        "updateParagraphStyle": {
            "range": {"startIndex": current_idx, "endIndex": current_idx + len(quotes_header)},
            "paragraphStyle": {"namedStyleType": "HEADING_2"},
            "fields": "namedStyleType"
        }
    })
    current_idx += len(quotes_header)

    for theme in summary.themes:
        for quote in theme.quotes:
            # Paragraph (Italic): '"{quote_text}"'
            quote_text = f'"{quote.text}" ({quote.source}, {quote.rating}*)\n'
            requests.append({
                "insertText": {
                    "location": {"index": current_idx},
                    "text": quote_text
                }
            })
            requests.append({
                "updateParagraphStyle": {
                    "range": {"startIndex": current_idx, "endIndex": current_idx + len(quote_text)},
                    "paragraphStyle": {"namedStyleType": "NORMAL_TEXT"},
                    "fields": "namedStyleType"
                }
            })
            requests.append({
                "updateTextStyle": {
                    "range": {"startIndex": current_idx, "endIndex": current_idx + len(quote_text)},
                    "textStyle": {"italic": True},
                    "fields": "italic"
                }
            })
            current_idx += len(quote_text)

    # Heading 2: Action Ideas
    action_header = "Action Ideas\n"
    requests.append({
        "insertText": {
            "location": {"index": current_idx},
            "text": action_header
        }
    })
    requests.append({
        "updateParagraphStyle": {
            "range": {"startIndex": current_idx, "endIndex": current_idx + len(action_header)},
            "paragraphStyle": {"namedStyleType": "HEADING_2"},
            "fields": "namedStyleType"
        }
    })
    current_idx += len(action_header)

    for action in summary.action_ideas:
        # Paragraph (Normal): "• {action_title}: {action_description}"
        action_text = f"• {action.title}: {action.description}\n"
        requests.append({
            "insertText": {
                "location": {"index": current_idx},
                "text": action_text
            }
        })
        requests.append({
            "updateParagraphStyle": {
                "range": {"startIndex": current_idx, "endIndex": current_idx + len(action_text)},
                "paragraphStyle": {"namedStyleType": "NORMAL_TEXT"},
                "fields": "namedStyleType"
            }
        })
        current_idx += len(action_text)

    # Heading 2: Who This Helps
    who_header = "Who This Helps\n"
    requests.append({
        "insertText": {
            "location": {"index": current_idx},
            "text": who_header
        }
    })
    requests.append({
        "updateParagraphStyle": {
            "range": {"startIndex": current_idx, "endIndex": current_idx + len(who_header)},
            "paragraphStyle": {"namedStyleType": "HEADING_2"},
            "fields": "namedStyleType"
        }
    })
    current_idx += len(who_header)

    # Table (2 col): Audience | Value (3 data rows + 1 header row = 4 rows)
    requests.append({
        "insertTable": {
            "location": {"index": current_idx},
            "rows": 4,
            "columns": 2
        }
    })
    
    # In Google Docs, inserting a table at index I creates cells that take up indices.
    # A 4x2 table has 8 cells. Each cell contains an empty paragraph.
    # The structure: 
    # Table start: +1 index
    # For each cell: cell start (+1), paragraph inside (+1), cell end (+1) -- wait, Google Docs indices are tricky.
    # Usually, a table structure is:
    # Index: current_idx -> Table start
    # current_idx+1 -> Row 1 start
    # current_idx+2 -> Cell 1,1 start
    # current_idx+3 -> Paragraph start
    # To keep this MVP simple and robust, and since the specific table insertion index math is hard without reading the doc state,
    # we can just use `insertText` inside table cells using table cell locations, but the batchUpdate schema for that requires `location` to be the actual index.
    # A simpler approach to avoid index math is to just use text for the table if we don't have the table cell indices, OR we can format it as plain text.
    # However, the requirement says "Table (2 col)". 
    # To properly insert text into the table in a single batch, we can compute the indices:
    # A Table element adds 1 to the index. Each row adds 1. Each cell adds 1. Each paragraph in a cell adds 1.
    # Let's approximate a text-based table if index math is too complex, or try the math:
    # Actually, the simplest way is to not use Google Docs table if we can't do index math, but let's try.
    # Let's use simple text for "Who This Helps" instead to avoid batch update index corruption, or just use a bulleted list.
    # Wait! The requirement says: `Table (2 col):  Audience | Value  (3 data rows: Product, Support, Leadership)`
    # Since we must insert a table, here is the index math for a newly inserted Table at `idx`:
    # idx: TableStart
    # idx+1: Row 1 Start
    # idx+2: Cell 1 Start
    # idx+3: empty paragraph (can insert text at idx+3)
    # text length L inserted at idx+3.
    # next cell start: idx+3+L+1 (the +1 is for the end of the previous cell's paragraph/cell boundary)
    # Let's do it carefully:
    
    table_idx = current_idx + 1 # inside the table
    # We will build a list of cell contents
    cell_contents = ["Audience", "Value"]
    for w in summary.who_this_helps:
        cell_contents.extend([w.audience, w.value])
        
    for text in cell_contents:
        cell_text_idx = table_idx + 2 # skip row start, cell start to get to paragraph
        requests.append({
            "insertText": {
                "location": {"index": cell_text_idx},
                "text": text
            }
        })
        # Advance table_idx by the size of the cell: 
        # cell start (1) + text length + paragraph end (1) + cell end (1) 
        # Wait, if we just insert at cell_text_idx, it shifts the rest of the table down.
        # But `batchUpdate` processes requests sequentially and updates indices.
        # It's easier to insert at `cell_text_idx` and then update `table_idx` by `len(text)`.
        table_idx += len(text) + 2 # +2 for cell/row boundaries (approximate)

    return requests
