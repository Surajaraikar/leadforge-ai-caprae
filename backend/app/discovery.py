import asyncio
import time
from datetime import UTC, datetime
from typing import Any
from urllib.parse import urlparse
from uuid import NAMESPACE_URL, uuid4, uuid5

import httpx

from app.config import Settings
from app.deduplication import deduplicate
from app.models import DiscoveryRequest, DiscoveryResponse, Lead
from app.scoring import haversine_km, normalize, score_lead

BUSINESS_CATEGORIES = {
    "amenity",
    "craft",
    "healthcare",
    "industrial",
    "leisure",
    "office",
    "shop",
    "tourism",
}


class DiscoveryError(RuntimeError):
    pass


class DiscoveryService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._cache: dict[str, tuple[float, DiscoveryResponse]] = {}
        self._lock = asyncio.Lock()

    async def discover(self, request: DiscoveryRequest) -> DiscoveryResponse:
        key = f"{normalize(request.keyword)}|{normalize(request.location)}|{request.limit}"
        cached = self._cache.get(key)
        if cached and cached[0] > time.monotonic():
            return self._fresh_search(cached[1])

        async with self._lock:
            cached = self._cache.get(key)
            if cached and cached[0] > time.monotonic():
                return self._fresh_search(cached[1])
            result = await self._fetch(request)
            self._cache[key] = (
                time.monotonic() + self.settings.discovery_cache_seconds,
                result,
            )
            return result

    @staticmethod
    def _fresh_search(cached: DiscoveryResponse) -> DiscoveryResponse:
        return cached.model_copy(
            update={"search_id": str(uuid4()), "searched_at": datetime.now(UTC)}
        )

    async def _fetch(self, request: DiscoveryRequest) -> DiscoveryResponse:
        headers = {"User-Agent": self.settings.osm_user_agent, "Accept": "application/json"}
        timeout = httpx.Timeout(self.settings.request_timeout_seconds)
        try:
            async with httpx.AsyncClient(headers=headers, timeout=timeout) as client:
                geocode = await client.get(
                    "https://nominatim.openstreetmap.org/search",
                    params={"q": request.location, "format": "jsonv2", "limit": 1},
                )
                geocode.raise_for_status()
                locations = geocode.json()
                if not locations:
                    raise DiscoveryError(f'Location "{request.location}" was not found.')
                latitude = float(locations[0]["lat"])
                longitude = float(locations[0]["lon"])
                # The public Nominatim service requires an absolute maximum of one
                # request per second. Discovery is serialized by the service lock.
                await asyncio.sleep(1.05)
                response = await client.get(
                    "https://nominatim.openstreetmap.org/search",
                    params={
                        "q": f"{request.keyword}, {request.location}",
                        "format": "jsonv2",
                        "limit": request.limit,
                        "addressdetails": 1,
                        "extratags": 1,
                        "namedetails": 1,
                    },
                )
                response.raise_for_status()
                elements = response.json()
        except DiscoveryError:
            raise
        except (httpx.HTTPError, KeyError, TypeError, ValueError) as exc:
            raise DiscoveryError(
                "The public business-data provider is temporarily unavailable. "
                "Please retry shortly."
            ) from exc

        leads = [
            lead
            for element in elements[: request.limit]
            if (lead := self._to_lead(element, request, latitude, longitude)) is not None
        ]
        unique, duplicate_count = deduplicate(leads)
        return DiscoveryResponse(
            search_id=str(uuid4()),
            leads=unique[: request.limit],
            raw_count=len(elements),
            duplicate_count=duplicate_count,
            excluded_count=len(elements) - len(leads),
        )

    @staticmethod
    def _to_lead(
        element: dict[str, Any],
        request: DiscoveryRequest,
        search_latitude: float,
        search_longitude: float,
    ) -> Lead | None:
        raw_extra_tags = element.get("extratags") or {}
        tags: dict[str, str] = {
            str(key): str(value) for key, value in raw_extra_tags.items() if value is not None
        }
        name_details = element.get("namedetails") or {}
        name = element.get("name") or name_details.get("name")
        if not name or "lat" not in element or "lon" not in element:
            return None
        category_key = str(element.get("category") or "office")
        category_value = str(element.get("type") or "business")
        if category_key not in BUSINESS_CATEGORIES:
            return None
        tags.update({"name": str(name), category_key: category_value})
        latitude, longitude = float(element["lat"]), float(element["lon"])
        distance = round(haversine_km(search_latitude, search_longitude, latitude, longitude), 1)
        score, breakdown = score_lead(tags, request.keyword, distance)
        element_type = str(element.get("osm_type", "node"))
        element_id = str(element.get("osm_id", element.get("place_id", "")))
        source_id = f"osm:{element_type}:{element_id}"
        category = category_value.replace("_", " ").title()
        address_data: dict[str, str] = element.get("address") or {}
        address = element.get("display_name")
        website = tags.get("website") or tags.get("contact:website")
        if website and not urlparse(website).scheme:
            website = f"https://{website}"
        return Lead(
            id=str(uuid5(NAMESPACE_URL, source_id)),
            source_id=source_id,
            name=name,
            category=category,
            address=address or None,
            city=address_data.get("city")
            or address_data.get("town")
            or address_data.get("village")
            or address_data.get("municipality"),
            region=address_data.get("state"),
            country=address_data.get("country"),
            latitude=latitude,
            longitude=longitude,
            distance_km=distance,
            website=website,
            phone=tags.get("phone") or tags.get("contact:phone"),
            email=tags.get("email") or tags.get("contact:email"),
            opening_hours=tags.get("opening_hours"),
            score=score,
            score_breakdown=breakdown,
            source_url=f"https://www.openstreetmap.org/{element_type}/{element_id}",
            search_keyword=request.keyword,
            search_location=request.location,
            discovered_at=datetime.now(UTC),
        )
