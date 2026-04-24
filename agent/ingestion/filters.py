import emoji


def is_valid_review(body: str, language: str | None = None) -> bool:
    """
    Apply ingestion filters:
    - Language must be 'en' (or unspecified)
    - Length must be at least 3 words
    - Must not contain emojis
    """
    if language and not language.lower().startswith("en"):
        return False
    
    words = body.split()
    if len(words) < 3:
        return False
        
    # Filter out reviews that contain ONLY emojis
    if emoji.replace_emoji(body, replace='').strip() == "":
        return False
        
    return True
