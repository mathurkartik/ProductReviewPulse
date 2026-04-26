import hashlib
from collections.abc import Generator
from datetime import datetime

from google_play_scraper import Sort, reviews

from agent.ingestion.filters import is_valid_review
from agent.ingestion.models import RawReview
from agent.ingestion.pii import scrub_pii


def fetch_playstore_reviews(
    product_key: str, play_store_id: str, since: datetime
) -> Generator[RawReview, None, None]:
    continuation_token = None

    while True:
        result, continuation_token = reviews(
            play_store_id,
            lang="en",
            country="in",
            sort=Sort.NEWEST,
            count=100,
            continuation_token=continuation_token,
        )

        if not result:
            break

        older_found = False
        for review in result:
            review_date = review.get("at")
            if not review_date:
                continue

            if review_date.tzinfo is None:
                review_date = review_date.replace(tzinfo=since.tzinfo)

            if review_date < since:
                older_found = True
                break

            body_text = review.get("content", "")
            if not is_valid_review(body_text, language="en"):
                continue

            body_scrubbed = scrub_pii(body_text)
            external_id = review.get("reviewId", "")
            rev_id = hashlib.sha1(f"playstore{external_id}".encode()).hexdigest()

            yield RawReview(
                id=rev_id,
                product_key=product_key,
                source="playstore",
                external_id=external_id,
                rating=review.get("score", 0),
                title=None,  # Play store reviews don't have titles
                body=body_scrubbed,
                posted_at=review_date,
                version=review.get("reviewCreatedVersion"),
                language="en",
                country="in",
            )

        if older_found or not continuation_token:
            break
