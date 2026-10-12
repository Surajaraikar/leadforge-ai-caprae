import re
from urllib.parse import urlparse

from app.models import Lead
from app.scoring import normalize


def normalized_domain(url: str | None) -> str:
    if not url:
        return ""
    candidate = url if "://" in url else f"https://{url}"
    try:
        host = urlparse(candidate).hostname or ""
    except ValueError:
        return ""
    return re.sub(r"^www\.", "", host.casefold())


def fingerprint(lead: Lead) -> str:
    domain = normalized_domain(lead.website)
    if domain:
        return f"domain:{domain}"
    rounded_location = f"{lead.latitude:.4f}:{lead.longitude:.4f}"
    return f"place:{normalize(lead.name)}:{rounded_location}"


def deduplicate(leads: list[Lead]) -> tuple[list[Lead], int]:
    chosen: dict[str, Lead] = {}
    source_ids: set[str] = set()
    duplicates = 0

    for lead in leads:
        if lead.source_id in source_ids:
            duplicates += 1
            continue
        source_ids.add(lead.source_id)
        key = fingerprint(lead)
        existing = chosen.get(key)
        if existing is None:
            chosen[key] = lead
        else:
            duplicates += 1
            if lead.score > existing.score:
                chosen[key] = lead

    return sorted(chosen.values(), key=lambda item: (-item.score, item.name.casefold())), duplicates
