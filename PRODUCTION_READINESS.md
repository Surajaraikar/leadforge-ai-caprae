# Production-readiness review

Review date: October 11, 2026

## Verdict

**Ready for take-home evaluation and a controlled local demo. Not ready for an unrestricted public production launch.**

The complete evaluator workflow is verified with real data: discovery, filtering, scoring explanation, deduplication, SQLite persistence, pagination, row selection, and CSV download. A public launch still needs authentication, a production database, distributed caching/rate limiting, and a hosted or dedicated geocoding/business-data provider.

## Verified checks

| Area | Result |
| --- | --- |
| Backend tests | 9 passed |
| Python lint | Ruff passed |
| Python typing | strict mypy passed |
| Frontend lint | ESLint passed with zero warnings |
| TypeScript | `tsc --noEmit` passed |
| Production build | Next.js optimized build passed |
| Dependency audit | 0 known npm vulnerabilities |
| Live discovery | 40 public matches → 32 unique leads; 6 duplicates and 2 non-business matches removed |
| Persistence | Leads and search statistics verified through the API and browser |
| CSV | Full and selected export verified; browser download completed |
| Responsive UI | Desktop and 390×844 mobile layouts inspected; mobile navigation verified |
| Accessibility | Labeled inputs, buttons, checkboxes, score disclosures, tables/cards, focus styles, and reduced-motion support verified |

Two warnings originate inside the current third-party FastAPI/pytest-asyncio test stack on Python 3.14. They do not represent application failures; the application supports Python 3.11+ and all tests pass.

## Correctness and security controls

- No seed/demo companies or fabricated enrichment are shipped.
- Every lead retains an OpenStreetMap source URL and the UI shows attribution.
- Scoring is deterministic, bounded to 100, and exposed as a component breakdown.
- Deduplication prefers source identity, then normalized website domain, then normalized name and rounded location.
- Search values and IDs are parameter-bound in SQLite; sort expressions come from a fixed allow-list.
- CSV values beginning with spreadsheet formula characters are escaped.
- External website URLs are limited to HTTP(S) before rendering.
- API input lengths, result limits, scores, pages, and export selection sizes are validated.
- CORS is allow-listed and includes both standard local loopback origins.
- Secrets, runtime data, build output, and virtual environments are ignored by Git.

## Remaining limitations

- OpenStreetMap coverage and tagging quality vary by market; the tool is a discovery aid, not a commercial enrichment database.
- Public Nominatim has strict usage constraints. The current service serializes discovery and caches repeated searches, but horizontal production scaling requires shared rate limiting and caching.
- SQLite is appropriate for a portable assessment, not concurrent multi-instance deployment.
- There is no authentication or tenant separation because this is a single-user assessment scope.
- The in-process cache is lost on restart and is not shared across workers.
- Public listings can contain stale source data. The product deliberately shows provenance and does not claim independent verification.

## Exact run and demo steps

From the repository root, open two PowerShell terminals.

Backend:

```powershell
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
uvicorn app.main:app --reload --port 8000
```

Frontend:

```powershell
cd frontend
npm install
Copy-Item .env.example .env.local
npm run dev
```

Then open http://localhost:3000 and:

1. Search `coffee` in `Austin, Texas`.
2. Open the first score to show its explanation.
3. Set minimum score to `75+`.
4. Select one or more leads and click Export.
5. Open the CSV and show the source links and missing-field behavior.
