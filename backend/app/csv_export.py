import csv
import io

from app.models import Lead

DANGEROUS_PREFIXES = ("=", "+", "-", "@", "\t", "\r")


def safe_cell(value: object | None) -> str:
    text = "" if value is None else str(value)
    if text.startswith(DANGEROUS_PREFIXES):
        return f"'{text}"
    return text


def export_leads(leads: list[Lead]) -> str:
    output = io.StringIO(newline="")
    writer = csv.writer(output)
    writer.writerow(
        [
            "Company",
            "Category",
            "Score",
            "Address",
            "City",
            "Website",
            "Phone",
            "Email",
            "Distance (km)",
            "Source",
            "Discovered at",
        ]
    )
    for lead in leads:
        writer.writerow(
            [
                safe_cell(lead.name),
                safe_cell(lead.category),
                lead.score,
                safe_cell(lead.address),
                safe_cell(lead.city),
                safe_cell(lead.website),
                safe_cell(lead.phone),
                safe_cell(lead.email),
                lead.distance_km if lead.distance_km is not None else "",
                str(lead.source_url),
                lead.discovered_at.isoformat(),
            ]
        )
    return output.getvalue()
