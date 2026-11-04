# CampusDesk Cloud — Viva and demo

## Demonstration script
1. Explain the architecture: browser → HTTPS → Render PaaS → Neon managed PostgreSQL.
2. Open the live Render URL's `/health` endpoint and show the database connected.
3. Register/login as a student and create a ticket.
4. Sign in as administrator and update its status.
5. Log back in as the student and show the updated status and audit trail.
6. Show Render build/deployment logs, Neon database tables (without exposing credentials), and the GitHub `render.yaml`.

## Quick viva questions
**What is cloud computing?** On-demand access to remotely provided computing resources with managed scalability and measured usage.

**Why is this a cloud project?** Application hosting and persistent database are external managed services reachable over the internet, not merely a local website.

**What is PaaS?** A platform that runs user-written apps while managing infrastructure and deployment tools.

**What is SaaS?** Application functionality delivered to end users through a browser.

**Why Render?** Managed Python web-service deployment, HTTPS ingress, build/deploy automation and environment variables.

**Why Neon?** Hosted PostgreSQL separated from compute, enabling durable ticket storage across app restarts/redeploys.

**Why not SQLite on Render?** The web service's local filesystem may not persist on restart or redeploy.

**What is an SLA?** A service-level agreement defining provider commitments such as availability.

**What is virtualization?** Abstraction allowing multiple isolated compute environments to share physical infrastructure.

**What does capacity planning mean?** Estimate traffic, CPU/memory, concurrent connections and database usage to size resources.

**How is data secured?** Password hashing, signed sessions, HTTPS, TLS database connections, CSRF protection and server-side authorization.

**What is the health endpoint?** A monitoring URL that checks both the API and a database query.

**How to scale?** Increase instance capacity, add replicas/load balancing as supported, pool DB connections, add indexes/metrics.

**What is the main limitation?** Free infrastructure can sleep and lacks high-availability guarantees. This is an academic demo, not production-certified.
