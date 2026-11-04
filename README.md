# CampusDesk Cloud | Cloud Computing FT-III Case Study

**Working application:** a student support-ticket platform with a secure student portal and an administrator analytics dashboard. Designed for the **21CSE362T Cloud Computing** course. Includes complete source code, demo data, test cases, cloud deployment definition and presentation screenshots.

## What's implemented

- Student registration/login with PBKDF2 password hashes
- Student ticket submission, personal dashboard, detailed ticket view
- Admin-only dashboard, status and priority edits, ticket audit trail
- Cloud health endpoint (`/health`) and private admin summary API (`/api/summary`)
- Server-side input validation, CSRF verification, signed session cookies, role checks, security headers
- SQLite for local demonstration; **Neon PostgreSQL** for persistent cloud data
- **Render** PaaS deployment with `render.yaml` and HTTPS

## Run locally (Python 3.11+)

**Windows shortcut:** Double-click `RUN_LOCAL_WINDOWS.bat` from inside the extracted project folder. It sets up the environment, seeds the local demo and starts the app. If you prefer commands, follow below.

Install dependencies (Internet needed):

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
```

Populate **local-only demo data**:

```bash
python seed_demo.py
uvicorn app:app --reload
```

Open **http://127.0.0.1:8000**. Local demo credentials:

| Account | Email | Password |
|---|---|---|
| Student | `student@demo.edu` | `StudentDemo123!` |
| Administrator | `admin@demo.edu` | `AdminDemo123!` |

**Important:** The demo accounts/passwords are for local testing ONLY. `seed_demo.py` refuses to seed a PostgreSQL cloud database. For your actual cloud deployment, set a unique administrator email/password using Render environment variables, and create student accounts through registration.

## Test the app

```bash
pip install -r requirements-dev.txt
python -m pytest -q tests/test_app.py
```

Tests use temporary SQLite databases and cover registration, authorization, login failure, CSRF, ticket submission, admin updates, JSON API and health checks.

## Deploy to the cloud

Read **[docs/DEPLOYMENT_GUIDE.md](docs/DEPLOYMENT_GUIDE.md)** for the complete step-by-step instructions to provision the Neon PostgreSQL database and deploy the Render web application using the included `render.yaml`. The cloud infrastructure cannot be provisioned from this ZIP without your own Render/GitHub/Neon account access.

## Design and service model

```text
Student/Admin browser (SaaS user experience)
     | HTTPS, signed session cookie, CSRF token
     v
Render Web Service (PaaS, FastAPI + Uvicorn)
     | SQLAlchemy / TLS PostgreSQL connection
     v
Neon Managed PostgreSQL (DBaaS / PaaS)
```

**Service models:** Render and Neon are managed PaaS services used by the developer. The end-user application behaves as SaaS. We do not directly provision virtual machines (IaaS); the cloud provider abstracts the underlying compute. This maps to Unit II, Unit III (identity/security), Unit IV (capacity/scalability), and Unit V (provider case studies).

### Database schema

- `users(id, name, email, password_hash, role, created_at)`
- `tickets(id, user_id, title, description, category, priority, state, created_at, updated_at)`
- `ticket_events(id, ticket_id, author_id, note, created_at)`

User-to-ticket is one-to-many; ticket-to-event is one-to-many. Primary and foreign keys ensure relational integrity. The server never accepts arbitrary SQL from users.

## Current limits / real-world caveats

- Deployment is **prepared but NOT live** until you perform account-based setup.
- The Render **Free** instance sleeps after inactivity and supports only one instance, so it is not a production-grade/high-availability deployment.
- The free tier's capacity/quotas and price may change. Confirm within each provider dashboard.
- No outbound email notifications, file attachments, rate-limit middleware, backup automation, or production observability have been implemented. Future work could add these.
- Source code is provided for educational demonstration, not production security certification.

## Files

- `app.py`: FastAPI routes, models, security, ticket workflows
- `init_db.py`: schema/bootstrap administrator via environment variables
- `seed_demo.py`: local demo fixture
- `templates/`, `static/`: polished responsive UI
- `render.yaml`: Render Blueprint/IaC
- `Dockerfile`: optional container packaging
- `docs/DEPLOYMENT_GUIDE.md`: detailed cloud deployment
- `docs/CASE_STUDY_REPORT.md`: full written analysis
- `docs/VIVA_AND_DEMO.md`: timed demo and viva Q&A
- `docs/screenshots/`: real, locally rendered app screenshots
- `docs/local_benchmark.json`: measured local HTTP response times (not cloud)

## Official sources

- https://render.com/docs/deploy-flask (Render Python hosting principles)
- https://render.com/docs/web-services
- https://render.com/docs/blueprint-spec
- https://render.com/docs/free
- https://neon.com/pricing
- https://neon.com/docs/connect/connect-from-any-app
