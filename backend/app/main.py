from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response

from app.config import Settings, get_settings
from app.csv_export import export_leads
from app.database import Database
from app.deduplication import fingerprint
from app.discovery import DiscoveryError, DiscoveryService
from app.models import DashboardStats, DiscoveryRequest, DiscoveryResponse, LeadPage, SortOption


def create_app(settings: Settings | None = None) -> FastAPI:
    configured = settings or get_settings()
    database = Database(configured.database_path)
    discovery = DiscoveryService(configured)

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        database.initialize()
        yield

    api = FastAPI(
        title=configured.app_name,
        version="1.0.0",
        description="Real-data lead discovery with explainable scoring.",
        lifespan=lifespan,
    )
    api.state.database = database
    api.state.discovery = discovery
    api.add_middleware(
        CORSMiddleware,
        allow_origins=configured.allowed_origins,
        allow_credentials=False,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type"],
    )

    def get_database() -> Database:
        return database

    DatabaseDependency = Annotated[Database, Depends(get_database)]

    @api.get("/api/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "data_source": "OpenStreetMap"}

    @api.post("/api/leads/discover", response_model=DiscoveryResponse)
    async def discover_leads(
        request: DiscoveryRequest,
        db: DatabaseDependency,
    ) -> DiscoveryResponse:
        try:
            result = await discovery.discover(request)
        except DiscoveryError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        db.save_discovery(
            result.search_id,
            request.keyword,
            request.location,
            result.raw_count,
            result.duplicate_count,
            result.leads,
            {lead.id: fingerprint(lead) for lead in result.leads},
        )
        return result

    @api.get("/api/leads", response_model=LeadPage)
    def list_leads(
        db: DatabaseDependency,
        page: int = Query(default=1, ge=1),
        page_size: int = Query(default=20, ge=5, le=100),
        min_score: int = Query(default=0, ge=0, le=100),
        complete_only: bool = False,
        query: str | None = Query(default=None, max_length=100),
        sort: SortOption = "score_desc",
    ) -> LeadPage:
        return db.list_leads(page, page_size, min_score, complete_only, query, sort)

    @api.get("/api/stats", response_model=DashboardStats)
    def dashboard_stats(db: DatabaseDependency) -> DashboardStats:
        return db.stats()

    @api.get("/api/leads/export")
    def export(
        db: DatabaseDependency,
        ids: str | None = Query(default=None, max_length=4000),
    ) -> Response:
        parsed_ids = [item for item in (ids or "").split(",") if item]
        if len(parsed_ids) > 100:
            raise HTTPException(
                status_code=422,
                detail="A maximum of 100 selected leads can be exported.",
            )
        leads = db.selected_leads(parsed_ids or None)
        csv_content = export_leads(leads)
        headers = {"Content-Disposition": 'attachment; filename="leadforge-ai-leads.csv"'}
        return Response(content=csv_content, media_type="text/csv; charset=utf-8", headers=headers)

    return api


app = create_app()
