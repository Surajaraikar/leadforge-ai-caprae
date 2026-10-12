from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, Field, HttpUrl, field_validator


class DiscoveryRequest(BaseModel):
    keyword: str = Field(min_length=2, max_length=80)
    location: str = Field(min_length=2, max_length=120)
    limit: int = Field(default=40, ge=5, le=100)

    @field_validator("keyword", "location")
    @classmethod
    def clean_search_text(cls, value: str) -> str:
        cleaned = " ".join(value.split())
        if not cleaned:
            raise ValueError("must not be blank")
        return cleaned


class ScoreBreakdown(BaseModel):
    relevance: int = Field(ge=0, le=35)
    proximity: int = Field(ge=0, le=25)
    completeness: int = Field(ge=0, le=25)
    business_signals: int = Field(ge=0, le=15)
    reasons: list[str]


class Lead(BaseModel):
    id: str
    source_id: str
    name: str
    category: str
    address: str | None = None
    city: str | None = None
    region: str | None = None
    country: str | None = None
    latitude: float
    longitude: float
    distance_km: float | None = None
    website: str | None = None
    phone: str | None = None
    email: str | None = None
    opening_hours: str | None = None
    score: int = Field(ge=0, le=100)
    score_breakdown: ScoreBreakdown
    source_url: HttpUrl
    search_keyword: str
    search_location: str
    discovered_at: datetime


class DiscoveryResponse(BaseModel):
    search_id: str
    leads: list[Lead]
    raw_count: int
    duplicate_count: int
    excluded_count: int = 0
    source: Literal["OpenStreetMap"] = "OpenStreetMap"
    searched_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class LeadPage(BaseModel):
    items: list[Lead]
    total: int
    page: int
    page_size: int
    pages: int


class DashboardStats(BaseModel):
    total_leads: int
    qualified_leads: int
    complete_leads: int
    average_score: float
    searches_run: int
    last_search_at: datetime | None


SortOption = Literal["score_desc", "score_asc", "newest", "name"]
