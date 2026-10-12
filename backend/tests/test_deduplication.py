from datetime import UTC, datetime

from app.deduplication import deduplicate, normalized_domain
from app.models import Lead, ScoreBreakdown


def make_lead(source_id: str, website: str, score: int) -> Lead:
    return Lead(
        id=source_id,
        source_id=source_id,
        name="Acme Co",
        category="Consulting",
        latitude=1.0,
        longitude=2.0,
        website=website,
        score=score,
        score_breakdown=ScoreBreakdown(
            relevance=20, proximity=20, completeness=10, business_signals=0, reasons=[]
        ),
        source_url="https://www.openstreetmap.org/node/1",
        search_keyword="consulting",
        search_location="Austin",
        discovered_at=datetime.now(UTC),
    )


def test_domain_normalization() -> None:
    assert normalized_domain("https://www.Example.com/path") == "example.com"


def test_duplicate_domains_keep_higher_score() -> None:
    first = make_lead("one", "https://example.com", 50)
    second = make_lead("two", "http://www.example.com/about", 70)
    unique, duplicate_count = deduplicate([first, second])
    assert duplicate_count == 1
    assert [lead.source_id for lead in unique] == ["two"]
