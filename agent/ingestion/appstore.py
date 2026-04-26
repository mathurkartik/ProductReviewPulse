import hashlib
import re
from collections.abc import Generator
from datetime import UTC, datetime

import httpx
import structlog

from agent.ingestion.filters import is_valid_review
from agent.ingestion.models import RawReview
from agent.ingestion.pii import scrub_pii

log = structlog.get_logger()


def _parse_date(date_str: str, since: datetime) -> datetime:
    try:
        review_date = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
    except ValueError:
        review_date = datetime.now(UTC)
    if review_date.tzinfo is None:
        review_date = review_date.replace(tzinfo=since.tzinfo)
    return review_date


def _process_review(
    product_key: str,
    external_id: str,
    title: str | None,
    body: str,
    rating: int | None,
    review_date: datetime,
    version: str | None,
) -> RawReview | None:
    if not is_valid_review(body, language="en"):
        return None

    body_scrubbed = scrub_pii(body)
    rev_id = hashlib.sha1(f"appstore{external_id}".encode()).hexdigest()
    return RawReview(
        id=rev_id,
        product_key=product_key,
        source="appstore",
        external_id=external_id,
        rating=rating or 0,
        title=title,
        body=body_scrubbed,
        posted_at=review_date,
        version=version,
        language="en",
        country="in",
    )


def fetch_appstore_reviews(
    product_key: str, app_store_id: str, since: datetime
) -> Generator[RawReview, None, None]:
    client = httpx.Client(
        timeout=10.0,
        follow_redirects=True,
        headers={
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
        },
    )

    found_any = False

    # 1. Try iTunes RSS (up to 10 pages)
    for page in range(1, 11):
        url = f"https://itunes.apple.com/in/rss/customerreviews/page={page}/id={app_store_id}/sortBy=mostRecent/json"
        try:
            response = client.get(url)
            if response.status_code == 200:
                data = response.json()
                entries = data.get("feed", {}).get("entry", [])
                if entries:
                    found_any = True
                    for entry in entries:
                        if "author" not in entry:
                            continue
                        external_id = entry.get("id", {}).get("label", "")
                        body_text = entry.get("content", {}).get("label", "")
                        date_str = entry.get("updated", {}).get("label", "")
                        review_date = _parse_date(date_str, since)

                        if review_date < since:
                            return

                        rating = int(entry.get("im:rating", {}).get("label", "0"))
                        version = entry.get("im:version", {}).get("label")
                        
                        rev = _process_review(
                            product_key, external_id, entry.get("title", {}).get("label"),
                            body_text, rating, review_date, version
                        )
                        if rev:
                            yield rev
                else:
                    break
        except Exception:
            break

    # 2. Fallback: Scrape HTML if RSS was empty
    if not found_any:
        import json
        from bs4 import BeautifulSoup

        url = f"https://apps.apple.com/in/app/reviews/id{app_store_id}"
        log.info("ingest.appstore.fallback.start", url=url)
        try:
            r = client.get(url)
            if r.status_code == 200:
                soup = BeautifulSoup(r.text, "lxml")
                scripts = soup.find_all("script")
                log.info("ingest.appstore.fallback.scripts_found", count=len(scripts))
                for s in scripts:
                    content = s.string or ""
                    if "reviewerName" in content:
                        try:
                            match = re.search(r"\{.*\}", content, re.DOTALL)
                            if match:
                                data = json.loads(match.group(0))

                                def find_reviews(obj):
                                    if isinstance(obj, dict):
                                        if obj.get("$kind") == "Review":
                                            yield obj
                                        for v in obj.values():
                                            yield from find_reviews(v)
                                    elif isinstance(obj, list):
                                        for item in obj:
                                            yield from find_reviews(item)

                                count = 0
                                for r_data in find_reviews(data):
                                    body = r_data.get("contents", "")
                                    title = r_data.get("title", "")
                                    author = r_data.get("reviewerName", "Anonymous")
                                    date_str = r_data.get("date")
                                    rating = r_data.get("rating")
                                    ext_id = (
                                        r_data.get("id")
                                        or hashlib.sha1(
                                            f"{author}{date_str}{body[:20]}".encode()
                                        ).hexdigest()
                                    )

                                    review_date = _parse_date(date_str, since)
                                    if review_date < since:
                                        continue

                                    rev = _process_review(
                                        product_key, str(ext_id), title, body,
                                        int(rating) if rating else None, review_date, None
                                    )
                                    if rev:
                                        count += 1
                                        yield rev
                                log.info("ingest.appstore.fallback.extracted", count=count)
                        except Exception as e:
                            log.error("ingest.appstore.fallback.parse_error", error=str(e))
            else:
                log.error("ingest.appstore.fallback.http_error", status=r.status_code)
        except Exception as e:
            log.error("ingest.appstore.fallback.request_error", error=str(e))
