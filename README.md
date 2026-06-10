# TechKraft Candidate Review Dashboard

Internal candidate scoring and review dashboard for the TechKraft full-stack take-home assignment. It includes a FastAPI API, SQLite persistence, JWT auth, role-based score visibility, a React/Vite dashboard, Docker Compose, seed data, and API tests.

## Stack

- Backend: Python, FastAPI, SQLAlchemy, SQLite, JWT
- Frontend: React, Vite, React Router
- Runtime: Docker Compose

## Run With Docker Compose

```bash
cp .env.example .env
docker compose up --build
```

- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API docs: http://localhost:8000/docs

## Deployed Application & Live Access

### Production Domains (Cloudflare Proxied with automatic HTTPS)
- **Frontend Dashboard:** [https://techkraft.prabe.sh](https://techkraft.prabe.sh)
- **Backend API Docs:** [https://techkraftapi.prabe.sh/docs](https://techkraftapi.prabe.sh/docs)
- **Backend Health Check:** [https://techkraftapi.prabe.sh/health](https://techkraftapi.prabe.sh/health)

### Direct AWS EC2 Server Access (Instant IP Access)
- **Frontend Dashboard:** [https://15.206.210.219](https://15.206.210.219) (HTTPS, bypass warning) or [http://15.206.210.219:5173](http://15.206.210.219:5173)
- **Backend API Docs:** [https://15.206.210.219/docs](https://15.206.210.219/docs) (HTTPS, bypass warning) or [http://15.206.210.219:8000/docs](http://15.206.210.219:8000/docs)
- **Backend Health Check:** [https://15.206.210.219/health](https://15.206.210.219/health) (HTTPS, bypass warning) or [http://15.206.210.219:8000/health](http://15.206.210.219:8000/health)



Seeded demo accounts come from `.env`:

- Admin: `DEMO_ADMIN_EMAIL` / `DEMO_ADMIN_PASSWORD`
- Reviewer: `DEMO_REVIEWER_EMAIL` / `DEMO_REVIEWER_PASSWORD`
- Reviewer 2: `DEMO_REVIEWER2_EMAIL` / `DEMO_REVIEWER2_PASSWORD`

These are dummy local credentials only. Real secrets should be supplied through `.env`, which is intentionally ignored by git.

## Seeded Demo Accounts (For RBAC Testing)

- **Admin Role:** `admin@example.com` / `admin1234`
- **Reviewer Role:** `reviewer@example.com` / `reviewer1234`
- **Reviewer 2 Role:** `reviewer2@example.com` / `reviewer21234`

## Run Locally

Backend:

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

Tests:

```bash
cd backend
pytest
```

## Example API Calls

Login:

```bash
curl -X POST http://localhost:8000/auth/login ^
  -H "Content-Type: application/json" ^
  -d "{\"email\":\"admin@example.com\",\"password\":\"admin1234\"}"
```

List candidates:

```bash
curl "http://localhost:8000/candidates?status=new&skill=React&offset=0&limit=10" ^
  -H "Authorization: Bearer YOUR_TOKEN"
```

Submit score:

```bash
curl -X POST http://localhost:8000/candidates/CANDIDATE_ID/scores ^
  -H "Authorization: Bearer YOUR_TOKEN" ^
  -H "Content-Type: application/json" ^
  -d "{\"category\":\"Technical depth\",\"score\":4,\"note\":\"Good API reasoning.\"}"
```

Generate mock AI summary:

```bash
curl -X POST http://localhost:8000/candidates/CANDIDATE_ID/summary ^
  -H "Authorization: Bearer YOUR_TOKEN"
```

## Features

- JWT login and registration.
- Registration always creates `reviewer` users; role is never accepted from the client.
- Admin users can see all scores and internal notes.
- Reviewer users can score candidates and see only their own scores.
- Candidate filters by status, role, skill, keyword, plus offset/limit pagination with max limit 50.
- Mock AI summary endpoint waits 2 seconds and the frontend shows loading and error states.
- Admin-only internal notes editing.
- Soft delete endpoint sets candidate status to `archived` and writes `deleted_at`; it never hard-deletes.
- Stretch SSE endpoint at `GET /candidates/{id}/stream` streams visible score snapshots.

## Debugging Signal

The bug in the provided snippet is that it loads every candidate with `SELECT * FROM candidates`, then filters and paginates in Python. This matters at scale because the database cannot use indexes for status, keyword, or role filters; memory use and response time grow with the full table size rather than the requested page.

The correct approach is to push filtering, ordering, and pagination into SQL:

```sql
SELECT *
FROM candidates
WHERE status = :status
  AND (lower(name) LIKE :keyword OR lower(email) LIKE :keyword)
ORDER BY created_at DESC
LIMIT :limit OFFSET :offset;
```

The API implements that pattern through SQLAlchemy and adds indexes on status, role, and score lookup fields.

## Architecture Decision Record

### ADR 1: FastAPI Backend

- Context: The assignment needs a compact API with typed request/response validation, async-friendly endpoints, and quick test setup.
- Decision: Use FastAPI with Pydantic schemas and SQLAlchemy.
- Trade-off: The app uses synchronous SQLAlchemy sessions for simplicity; a larger production version could move to fully async database drivers.

### ADR 2: SQLite Schema With JSON Skills

- Context: The prompt allows SQLite or DynamoDB-style modeling and asks for candidates and scores with indexes.
- Decision: Use normalized `candidates`, `scores`, and `users` tables. Candidate skills are stored as JSON text to keep SQLite setup portable.
- Trade-off: Skill filtering uses a text match in this lightweight version. For heavier search requirements, I would normalize skills into a join table or use a search index.

### ADR 3: JWT RBAC At the API Boundary

- Context: Reviewers and admins need different visibility for the same candidate detail route.
- Decision: Authenticate every candidate route with JWT and shape responses based on the current user role. Reviewer score visibility is filtered server-side.
- Trade-off: JWTs are stateless and easy to run locally, but revocation would need token versioning or a server-side denylist in a production system.

## Learning Reflection

I treated this as a small internal product rather than just a set of endpoints, so I spent time making the UI states explicit: loading, empty, forbidden, and summary-generation states. Given more time, I would explore replacing the simple SSE score snapshot with a proper event bus so new scores could fan out instantly across reviewer sessions.
