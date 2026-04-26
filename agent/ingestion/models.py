from datetime import datetime

from pydantic import BaseModel


class RawReview(BaseModel):
    id: str
    product_key: str
    source: str
    external_id: str
    rating: int | None
    title: str | None
    body: str
    posted_at: datetime
    version: str | None
    language: str
    country: str
