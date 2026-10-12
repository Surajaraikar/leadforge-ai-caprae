# Deployment status

Review date: October 11, 2026

## Current state

LeadForge AI is verified as a local two-service application:

- Next.js frontend: `http://127.0.0.1:3000`
- FastAPI backend: `http://127.0.0.1:8000`
- Persistence: local SQLite database
- External data: public OpenStreetMap Nominatim

There is **no public deployment** and no public live-demo URL. The repository has not been published at the time of this report.

## Compatibility assessment

### Frontend — Vercel

The statically generated Next.js dashboard is compatible with Vercel. It would need `NEXT_PUBLIC_API_URL` set to the approved public API origin. The production backend must allow only the deployed frontend origin.

### Backend — Render or equivalent

FastAPI and Uvicorn are compatible with a container or Python web service. A deployment would need:

- a start command such as `uvicorn app.main:app --host 0.0.0.0 --port $PORT`;
- a real `OSM_USER_AGENT` contact value;
- environment-managed allowed origins;
- health checks and structured logging; and
- a hosted data provider or dedicated Nominatim service for reliable usage.

### Database — Supabase PostgreSQL

The current code uses the Python `sqlite3` module directly. Moving to Supabase PostgreSQL is not a configuration-only change: it requires a database adapter/ORM, schema migrations, connection handling, tested query equivalents, and deployment-safe credentials. Silently attaching Supabase to the existing build would risk correctness and exceed the submission’s focused scope.

## Security blockers for a public write-enabled demo

- No authentication or authorization
- No user/workspace isolation
- No durable distributed rate limit
- No shared cache across backend workers
- Public discovery endpoint can consume upstream provider capacity
- SQLite is not appropriate for multiple ephemeral service instances
- No production monitoring, alerting, or abuse protection

## Recommendation before the deadline

Prioritize the verified video and GitHub repository. A rushed public deployment would expose a state-changing API without adequate access controls and would make the demo dependent on public Nominatim availability.

If a public demo is still desired, the safest narrow option is a temporary, access-controlled single-instance backend with a persistent disk and strict request limits, followed by a Vercel frontend. Even that should be deployed only after explicit approval and an end-to-end remote verification pass.

Status: **NOT DEPLOYED — NEEDS USER APPROVAL before any external deployment.**
