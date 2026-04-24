from datetime import datetime

from pydantic import BaseModel


class RawReview(BaseModel):
    id: str
    product_key: str
    source: str
    external_id: str
    body: str
    rating: int | None
    review_date: datetime
    language: str | None
