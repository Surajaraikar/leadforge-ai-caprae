import json
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path

from app.models import DashboardStats, Lead, LeadPage, SortOption


class Database:
    def __init__(self, path: Path) -> None:
        self.path = path

    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self.path, timeout=10)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA journal_mode = WAL")
        try:
            yield connection
            connection.commit()
        finally:
            connection.close()

    def initialize(self) -> None:
        with self.connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS searches (
                    id TEXT PRIMARY KEY,
                    keyword TEXT NOT NULL,
                    location TEXT NOT NULL,
                    raw_count INTEGER NOT NULL,
                    duplicate_count INTEGER NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS leads (
                    id TEXT PRIMARY KEY,
                    source_id TEXT NOT NULL UNIQUE,
                    fingerprint TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    name TEXT NOT NULL,
                    city TEXT,
                    score INTEGER NOT NULL CHECK(score BETWEEN 0 AND 100),
                    completeness INTEGER NOT NULL CHECK(completeness BETWEEN 0 AND 25),
                    search_id TEXT NOT NULL,
                    discovered_at TEXT NOT NULL,
                    FOREIGN KEY(search_id) REFERENCES searches(id)
                );
                CREATE INDEX IF NOT EXISTS idx_leads_score ON leads(score DESC);
                CREATE INDEX IF NOT EXISTS idx_leads_city ON leads(city);
                CREATE INDEX IF NOT EXISTS idx_leads_discovered ON leads(discovered_at DESC);
                CREATE INDEX IF NOT EXISTS idx_leads_fingerprint ON leads(fingerprint);
                """
            )

    def save_discovery(
        self,
        search_id: str,
        keyword: str,
        location: str,
        raw_count: int,
        duplicate_count: int,
        leads: list[Lead],
        fingerprints: dict[str, str],
    ) -> None:
        created_at = datetime.now(UTC).isoformat()
        with self.connect() as connection:
            connection.execute(
                "INSERT INTO searches VALUES (?, ?, ?, ?, ?, ?)",
                (search_id, keyword, location, raw_count, duplicate_count, created_at),
            )
            connection.executemany(
                """
                INSERT INTO leads (
                    id, source_id, fingerprint, payload, name, city, score,
                    completeness, search_id, discovered_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(source_id) DO UPDATE SET
                    fingerprint=excluded.fingerprint,
                    payload=excluded.payload,
                    name=excluded.name,
                    city=excluded.city,
                    score=excluded.score,
                    completeness=excluded.completeness,
                    search_id=excluded.search_id,
                    discovered_at=excluded.discovered_at
                """,
                [
                    (
                        lead.id,
                        lead.source_id,
                        fingerprints[lead.id],
                        lead.model_dump_json(),
                        lead.name,
                        lead.city,
                        lead.score,
                        lead.score_breakdown.completeness,
                        search_id,
                        lead.discovered_at.isoformat(),
                    )
                    for lead in leads
                ],
            )

    @staticmethod
    def _row_to_lead(row: sqlite3.Row) -> Lead:
        return Lead.model_validate(json.loads(str(row["payload"])))

    def list_leads(
        self,
        page: int,
        page_size: int,
        min_score: int,
        complete_only: bool,
        query: str | None,
        sort: SortOption,
    ) -> LeadPage:
        where = ["score >= ?"]
        params: list[object] = [min_score]
        if complete_only:
            where.append("completeness >= 19")
        if query:
            where.append("(name LIKE ? ESCAPE '\\' OR city LIKE ? ESCAPE '\\')")
            escaped = query.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
            like = f"%{escaped}%"
            params.extend([like, like])
        order_by = {
            "score_desc": "score DESC, name COLLATE NOCASE",
            "score_asc": "score ASC, name COLLATE NOCASE",
            "newest": "discovered_at DESC",
            "name": "name COLLATE NOCASE ASC",
        }[sort]
        clause = " AND ".join(where)
        # The fragments in these two statements only come from the fixed clauses and
        # sort allow-list above. User values stay bound as SQLite parameters.
        with self.connect() as connection:
            total = int(
                connection.execute(
                    f"SELECT COUNT(*) FROM leads WHERE {clause}",  # noqa: S608
                    params,
                ).fetchone()[0]
            )
            rows = connection.execute(
                f"SELECT payload FROM leads WHERE {clause} "  # noqa: S608
                f"ORDER BY {order_by} LIMIT ? OFFSET ?",
                [*params, page_size, (page - 1) * page_size],
            ).fetchall()
        pages = max(1, (total + page_size - 1) // page_size)
        return LeadPage(
            items=[self._row_to_lead(row) for row in rows],
            total=total,
            page=page,
            page_size=page_size,
            pages=pages,
        )

    def selected_leads(self, ids: list[str] | None = None) -> list[Lead]:
        with self.connect() as connection:
            if ids:
                placeholders = ",".join("?" for _ in ids)
                rows = connection.execute(
                    f"SELECT payload FROM leads WHERE id IN ({placeholders}) "  # noqa: S608
                    "ORDER BY score DESC",
                    ids,
                ).fetchall()
            else:
                rows = connection.execute(
                    "SELECT payload FROM leads ORDER BY score DESC, name COLLATE NOCASE"
                ).fetchall()
        return [self._row_to_lead(row) for row in rows]

    def stats(self) -> DashboardStats:
        with self.connect() as connection:
            lead_row = connection.execute(
                """
                SELECT COUNT(*) AS total,
                       SUM(CASE WHEN score >= 65 THEN 1 ELSE 0 END) AS qualified,
                       SUM(CASE WHEN completeness >= 19 THEN 1 ELSE 0 END) AS complete,
                       COALESCE(AVG(score), 0) AS average
                FROM leads
                """
            ).fetchone()
            search_row = connection.execute(
                "SELECT COUNT(*) AS total, MAX(created_at) AS latest FROM searches"
            ).fetchone()
        return DashboardStats(
            total_leads=int(lead_row["total"]),
            qualified_leads=int(lead_row["qualified"] or 0),
            complete_leads=int(lead_row["complete"] or 0),
            average_score=round(float(lead_row["average"]), 1),
            searches_run=int(search_row["total"]),
            last_search_at=search_row["latest"],
        )
