# CampusDesk Cloud — Deployment guide

## Architecture
Browser (HTTPS) → Render Python/FastAPI web service (PaaS) → Neon PostgreSQL (managed database, TLS).

## 1. Create the database
Sign in at https://console.neon.tech. Create a PostgreSQL project named `campusdesk-db` in a region near the Render service (Singapore if available). In the Neon console use **Connect** to obtain the PostgreSQL connection URL with `sslmode=require`. Treat that URL as a secret. Never put it in GitHub or slides.

## 2. Deploy on Render
Sign in at https://dashboard.render.com. Choose **New → Blueprint**, connect `Omkarratnani/campusdesk-cloud` and select its `render.yaml`. Configure:
- `DATABASE_URL`: the private Neon PostgreSQL connection URL
- `ADMIN_EMAIL`: your own administrator email
- `ADMIN_PASSWORD`: a new, unique password (at least 12 characters)
- `SECRET_KEY`: generated automatically by Blueprint
- `HTTPS_ONLY=1`: already configured in Blueprint

The Blueprint provisions a Python web service with build command `pip install -r requirements.txt`, start command `python init_db.py && uvicorn app:app --host 0.0.0.0 --port $PORT`, and health check at `/health`.

## 3. Live demonstration
Visit the public HTTPS URL provided by Render:
1. Open `/health` — expect `status=healthy`, `database=connected`.
2. Register as student, submit a Network ticket, and view the ticket in the student dashboard.
3. Log out, sign in as admin, and update the ticket status and priority.
4. Sign back in as the student to verify the status change and the recorded activity timeline.
5. Use the admin-only `/api/summary` API to see ticket counts. A student must receive 403.
6. Verify tickets persist after a redeploy because the database is hosted separately.

## Troubleshooting
- **Database disconnected:** check Neon URL, TLS, and database availability.
- **Failed build:** inspect Render logs and Python version.
- **Admin login fails:** `init_db.py` creates an admin only if the email is not already registered. Changing environment password does not reset an existing admin password.
- **Cookies fail:** use the Render HTTPS URL and a stable SECRET_KEY.
- **Slow first request:** free Render instances may spin down when idle.
- **Missing tickets after restart:** check that DATABASE_URL points to Neon and not local SQLite.

## Cost and limitations
Free plans may cost $0 within quotas; confirm current provider pricing. Render Free is not high availability, and the app has no MFA, email verification, rate limiting or production monitoring.

## Official links
https://render.com/docs/blueprint-spec
https://render.com/docs/web-services
https://neon.com/docs/connect/connect-from-any-app
