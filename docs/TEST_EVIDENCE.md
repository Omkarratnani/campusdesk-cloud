# Test evidence

The application has isolated local automated tests covering:
- Student registration and login
- Ticket submission and ticket details
- Admin-only authorization checks
- CSRF rejection
- Administrative ticket updates and event tracking
- Health endpoint and protected summary API

Run locally with:
```bash
pip install -r requirements-dev.txt
python -m pytest -q tests/test_app.py
```

Local results do not prove a successful cloud deployment. Validate the live Render + Neon system separately.
