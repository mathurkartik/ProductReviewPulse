import re

EMAIL_REGEX = re.compile(r"[\w\.-]+@[\w\.-]+\.\w+")
PHONE_REGEX = re.compile(r"\+?\d{10,14}")
AADHAAR_REGEX = re.compile(r"\b\d{4}\s?\d{4}\s?\d{4}\b")


def scrub_pii(text: str) -> str:
    if not text:
        return text
    text = EMAIL_REGEX.sub("[EMAIL]", text)
    text = PHONE_REGEX.sub("[PHONE]", text)
    text = AADHAAR_REGEX.sub("[AADHAAR]", text)
    return text
