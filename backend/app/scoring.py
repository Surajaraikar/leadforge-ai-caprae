import math
import re
from collections.abc import Mapping

from app.models import ScoreBreakdown


def normalize(value: str | None) -> str:
    if not value:
        return ""
    return re.sub(r"[^a-z0-9]+", " ", value.casefold()).strip()


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    radius = 6371.0088
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lon2 - lon1)
    a = math.sin(d_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(
        d_lambda / 2
    ) ** 2
    return radius * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def score_lead(
    tags: Mapping[str, str], keyword: str, distance_km: float | None
) -> tuple[int, ScoreBreakdown]:
    searchable = normalize(
        " ".join(
            [
                tags.get("name", ""),
                tags.get("amenity", ""),
                tags.get("shop", ""),
                tags.get("office", ""),
                tags.get("craft", ""),
                tags.get("tourism", ""),
                tags.get("leisure", ""),
                tags.get("description", ""),
            ]
        )
    )
    terms = [term for term in normalize(keyword).split() if len(term) > 1]
    matches = sum(term in searchable for term in terms)
    if terms and matches == len(terms):
        relevance = 35
    elif matches:
        relevance = 25
    else:
        relevance = 12

    if distance_km is None:
        proximity = 8
    elif distance_km <= 2:
        proximity = 25
    elif distance_km <= 5:
        proximity = 21
    elif distance_km <= 10:
        proximity = 17
    elif distance_km <= 25:
        proximity = 12
    else:
        proximity = 6

    website = tags.get("website") or tags.get("contact:website")
    phone = tags.get("phone") or tags.get("contact:phone")
    email = tags.get("email") or tags.get("contact:email")
    has_address = bool(tags.get("addr:street") or tags.get("addr:full"))
    completeness = (8 if website else 0) + (6 if phone else 0) + (5 if email else 0)
    completeness += 6 if has_address else 0

    signals = 0
    if tags.get("opening_hours"):
        signals += 5
    if tags.get("brand") or tags.get("operator"):
        signals += 4
    if tags.get("wikidata") or tags.get("wikipedia"):
        signals += 3
    if tags.get("start_date"):
        signals += 3

    reasons = [f"{relevance}/35 keyword relevance", f"{proximity}/25 location proximity"]
    if completeness:
        reasons.append(f"{completeness}/25 available contact and address fields")
    else:
        reasons.append("0/25 contact and address fields are missing")
    if signals:
        reasons.append(f"{signals}/15 additional public business signals")
    else:
        reasons.append("0/15 no additional public business signals")

    breakdown = ScoreBreakdown(
        relevance=relevance,
        proximity=proximity,
        completeness=completeness,
        business_signals=signals,
        reasons=reasons,
    )
    return relevance + proximity + completeness + signals, breakdown
