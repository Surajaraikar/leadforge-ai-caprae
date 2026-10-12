from app.scoring import haversine_km, score_lead


def test_complete_relevant_nearby_lead_scores_highly() -> None:
    tags = {
        "name": "Northstar Accounting",
        "office": "accountant",
        "website": "https://northstar.example",
        "phone": "+1 555 0100",
        "email": "hello@northstar.example",
        "addr:street": "Main Street",
        "opening_hours": "Mo-Fr 09:00-17:00",
        "brand": "Northstar",
    }
    score, breakdown = score_lead(tags, "accounting", 1.5)
    assert score >= 80
    assert score == sum(
        [
            breakdown.relevance,
            breakdown.proximity,
            breakdown.completeness,
            breakdown.business_signals,
        ]
    )


def test_score_is_bounded_for_sparse_record() -> None:
    score, breakdown = score_lead({"name": "Unrelated"}, "accounting", None)
    assert 0 <= score <= 100
    assert breakdown.completeness == 0


def test_haversine_distance() -> None:
    assert haversine_km(40.7128, -74.0060, 40.7128, -74.0060) == 0
    assert 3900 < haversine_km(40.7128, -74.0060, 34.0522, -118.2437) < 4000
