import csv
import io
from datetime import UTC, datetime

from fastapi.testclient import TestClient

from app.csv_export import export_leads, safe_cell
from app.database import Database
from app.deduplication import fingerprint
from app.models import Lead, ScoreBreakdown


def sample_lead() -> Lead:
    return Lead(
        id="lead-1",
        source_id="osm:node:1",
        name="Northstar Accounting",
        category="Accountant",
        address="1 Main Street",
        city="Austin",
        latitude=30.2672,
        longitude=-97.7431,
        distance_km=1.2,
        website="https://northstar.example",
        phone="+1 555 0100",
        email="hello@northstar.example",
        score=82,
        score_breakdown=ScoreBreakdown(
            relevance=35,
            proximity=25,
            completeness=22,
            business_signals=0,
            reasons=["verified"],
        ),
        source_url="https://www.openstreetmap.org/node/1",
        search_keyword="accounting",
        search_location="Austin",
        discovered_at=datetime.now(UTC),
    )


def seed(client: TestClient) -> None:
    database: Database = client.app.state.database
    lead = sample_lead()
    database.save_discovery(
        "search-1",
        "accounting",
        "Austin",
        1,
        0,
        [lead],
        {lead.id: fingerprint(lead)},
    )


def test_health(client: TestClient) -> None:
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["data_source"] == "OpenStreetMap"


def test_persist_list_stats_and_export(client: TestClient) -> None:
    seed(client)
    page = client.get("/api/leads?min_score=65").json()
    assert page["total"] == 1
    assert page["items"][0]["name"] == "Northstar Accounting"
    stats = client.get("/api/stats").json()
    assert stats["qualified_leads"] == 1
    response = client.get("/api/leads/export?ids=lead-1")
    assert response.status_code == 200
    assert "Northstar Accounting" in response.text
    assert (
        response.headers["content-disposition"]
        == 'attachment; filename="leadforge-ai-leads.csv"'
    )


def test_csv_formula_injection_is_escaped() -> None:
    lead = sample_lead().model_copy(update={"name": "=HYPERLINK(\"bad\")"})
    rows = list(csv.reader(io.StringIO(export_leads([lead]))))
    assert rows[1][0].startswith("'=")
    assert safe_cell("+SUM(1,1)").startswith("'+")


def test_repeating_saved_source_updates_without_duplicate_leads(client: TestClient) -> None:
    seed(client)
    database: Database = client.app.state.database
    lead = sample_lead()
    database.save_discovery(
        "search-2",
        "accounting",
        "Austin",
        1,
        0,
        [lead],
        {lead.id: fingerprint(lead)},
    )
    assert client.get("/api/leads").json()["total"] == 1
    assert client.get("/api/stats").json()["searches_run"] == 2
