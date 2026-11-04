# FT-III Case Study — CampusDesk Cloud

**Course:** 21CSE362T Cloud Computing

## Problem and requirements (2 marks)
Campus support requests managed by email or paper are difficult to track and audit. Build a student ticket portal with secure user accounts, admin management, persistent storage and browser access over the internet.

## Cloud design
The application is delivered as software to end users (SaaS-style experience), hosted on **Render PaaS**, using **Neon managed PostgreSQL** as a database service. Clients communicate with Render over HTTPS; the application accesses Neon through a TLS PostgreSQL connection. The underlying VM provisioning is abstracted from the developer.

## Implementation (8 marks)
- **Compute:** Python 3.11, FastAPI, Uvicorn; reproducible `render.yaml` Blueprint
- **Database:** SQLAlchemy ORM, PostgreSQL with `users`, `tickets`, `ticket_events` tables and relationships
- **Security:** PBKDF2 salted password hashes; signed session cookies; HTTP-only cookie defaults; CSRF tokens; server-side role authorization; input validation; secure headers; HTTPS and database SSL
- **Functionality:** student signup/login, ticket creation, dashboard, ticket details and audit history; admin dashboard, status and priority updates; health and protected summary API
- **Configuration:** credentials and database URL supplied as deployment environment variables, not committed to code
- **Testing:** isolated SQLite test data used to validate workflows before cloud deployment

## Results and evaluation (2 marks)
Local testing shows the application workflow is feasible. A successfully connected Render deployment with a healthy `/health` response and an end-to-end student/admin demo provides direct evidence of cloud operation. The application persists data in Neon independently of Render's ephemeral compute.

**Scalability:** the managed platform can be upgraded to larger instances; a database pool and load balancing would be needed for more concurrent users. **Cost:** free tiers can be $0 within quotas but do not provide guaranteed uptime; verify current provider limits.

## Limitations
No email alerts, attachments, MFA, rate limiting, automatic backups or measured production scalability. Do not present local benchmark timings as cloud performance results.
