"""CampusDesk Cloud — a small, deployable Cloud Computing FT-III case study.

Run locally: python seed_demo.py && uvicorn app:app --reload
Run in cloud: python init_db.py && uvicorn app:app --host 0.0.0.0 --port $PORT
"""
from contextlib import asynccontextmanager
from datetime import datetime, timezone
import hashlib
import hmac
import os
import re
import secrets

from fastapi import FastAPI, Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware
from fastapi.templating import Jinja2Templates
from sqlalchemy import create_engine, ForeignKey, String, Text, DateTime, Integer, select, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, sessionmaker
from sqlalchemy.exc import IntegrityError

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_URL = os.environ.get("DATABASE_URL", f"sqlite:///{os.path.join(BASE_DIR, 'campusdesk.sqlite3')}")
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+psycopg://", 1)
elif DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg://", 1)

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite:") else {}
engine = create_engine(DATABASE_URL, pool_pre_ping=True, pool_recycle=240, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(80))
    email: Mapped[str] = mapped_column(String(160), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(20), default="student")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    tickets: Mapped[list["Ticket"]] = relationship(back_populates="owner")

class Ticket(Base):
    __tablename__ = "tickets"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    title: Mapped[str] = mapped_column(String(120))
    description: Mapped[str] = mapped_column(Text)
    category: Mapped[str] = mapped_column(String(30))
    priority: Mapped[str] = mapped_column(String(15), default="Medium")
    state: Mapped[str] = mapped_column(String(20), default="Open", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    owner: Mapped[User] = relationship(back_populates="tickets")
    events: Mapped[list["TicketEvent"]] = relationship(back_populates="ticket", cascade="all, delete-orphan")

class TicketEvent(Base):
    __tablename__ = "ticket_events"
    id: Mapped[int] = mapped_column(primary_key=True)
    ticket_id: Mapped[int] = mapped_column(ForeignKey("tickets.id"), index=True)
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    note: Mapped[str] = mapped_column(String(400))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    ticket: Mapped[Ticket] = relationship(back_populates="events")
    author: Mapped[User] = relationship()

CATEGORY_OPTIONS = ["Infrastructure", "Application", "Network", "Database", "Security", "Other"]
PRIORITY_OPTIONS = ["Low", "Medium", "High"]
STATE_OPTIONS = ["Open", "In Progress", "Resolved"]

@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield

app = FastAPI(title="CampusDesk Cloud", version="1.0", docs_url=None, redoc_url=None, lifespan=lifespan)
app.add_middleware(SessionMiddleware,
                   secret_key=os.environ.get("SECRET_KEY", "LOCAL_DEMO_ONLY_CHANGE_ME"),
                   https_only=os.environ.get("HTTPS_ONLY", "0") == "1",
                   same_site="lax", max_age=60 * 60 * 8)
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Content-Security-Policy"] = "default-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; script-src 'self'; form-action 'self'; base-uri 'self'; frame-ancestors 'none'"
    if os.environ.get("HTTPS_ONLY", "0") == "1":
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response

def pw_hash(password: str) -> str:
    salt = secrets.token_bytes(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf8"), salt, 310_000)
    return f"pbkdf2_sha256$310000${salt.hex()}${dk.hex()}"

def pw_valid(password: str, encoded: str) -> bool:
    try:
        algorithm, rounds, salt_hex, expected_hex = encoded.split("$")
        if algorithm != "pbkdf2_sha256":
            return False
        actual = hashlib.pbkdf2_hmac("sha256", password.encode("utf8"), bytes.fromhex(salt_hex), int(rounds))
        return hmac.compare_digest(actual, bytes.fromhex(expected_hex))
    except (ValueError, TypeError):
        return False

def get_csrf(request: Request) -> str:
    if "csrf" not in request.session:
        request.session["csrf"] = secrets.token_urlsafe(32)
    return request.session["csrf"]

def require_csrf(request: Request, value: str) -> None:
    if not hmac.compare_digest(request.session.get("csrf", ""), value):
        raise HTTPException(status_code=403, detail="Invalid CSRF token")

def current_user(request: Request, db):
    uid = request.session.get("uid")
    return db.get(User, uid) if uid else None

def page(request: Request, name: str, **context):
    with SessionLocal() as db:
        u = current_user(request, db)
    return templates.TemplateResponse(request=request, name=name,
                                      context={"user": u, "csrf": get_csrf(request),
                                               "categories": CATEGORY_OPTIONS,
                                               "priorities": PRIORITY_OPTIONS,
                                               "states": STATE_OPTIONS, **context})

def navigate(path: str) -> RedirectResponse:
    return RedirectResponse(path, status_code=status.HTTP_303_SEE_OTHER)

def need_user(request: Request, db):
    u = current_user(request, db)
    if not u:
        raise HTTPException(status_code=303, headers={"Location": "/login"})
    return u

def need_admin(request: Request, db):
    u = need_user(request, db)
    if u.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    return u

def fmt(ticket):
    return ticket

@app.get("/health")
def health():
    try:
        with SessionLocal() as db:
            db.execute(select(func.count(User.id))).scalar()
        return {"status": "healthy", "database": "connected", "service": "CampusDesk Cloud"}
    except Exception:
        return JSONResponse({"status": "unhealthy", "database": "disconnected"}, status_code=503)

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    with SessionLocal() as db:
        u = current_user(request, db)
    if u:
        return navigate("/admin" if u.role == "admin" else "/dashboard")
    return page(request, "landing.html", title="Helpdesk for a connected campus")

@app.get("/register", response_class=HTMLResponse)
def register_form(request: Request):
    return page(request, "register.html", title="Create your account", error=None)

@app.post("/register", response_class=HTMLResponse)
def register(request: Request, name: str = Form(""), email: str = Form(""), password: str = Form(""), csrf_form: str = Form("", alias="_csrf")):
    require_csrf(request, csrf_form)
    name, email = name.strip(), email.strip().lower()
    if not (2 <= len(name) <= 80) or not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email) or len(email) > 160 or not (10 <= len(password) <= 128):
        return page(request, "register.html", title="Create your account", error="Enter a valid name, email and password (10+ characters).")
    with SessionLocal() as db:
        u = User(name=name, email=email, password_hash=pw_hash(password), role="student")
        db.add(u)
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            return page(request, "register.html", title="Create your account", error="This email is already registered.")
        request.session.clear()
        request.session["uid"] = u.id
    return navigate("/dashboard")

@app.get("/login", response_class=HTMLResponse)
def login_form(request: Request):
    return page(request, "login.html", title="Sign in", error=None)

@app.post("/login", response_class=HTMLResponse)
def login(request: Request, email: str = Form(""), password: str = Form(""), csrf_form: str = Form("", alias="_csrf")):
    require_csrf(request, csrf_form)
    with SessionLocal() as db:
        u = db.scalar(select(User).where(User.email == email.strip().lower()))
        if not u or not pw_valid(password, u.password_hash):
            return page(request, "login.html", title="Sign in", error="Incorrect email or password.")
        uid, role = u.id, u.role
    request.session.clear()
    request.session["uid"] = uid
    return navigate("/admin" if role == "admin" else "/dashboard")

@app.post("/logout")
def logout(request: Request, csrf_form: str = Form("", alias="_csrf")):
    require_csrf(request, csrf_form)
    request.session.clear()
    return navigate("/")

@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request):
    with SessionLocal() as db:
        u = need_user(request, db)
        if u.role == "admin":
            return navigate("/admin")
        tickets = db.scalars(select(Ticket).where(Ticket.user_id == u.id).order_by(Ticket.created_at.desc())).all()
        stats = {"total": len(tickets), "open": sum(t.state == "Open" for t in tickets),
                 "progress": sum(t.state == "In Progress" for t in tickets),
                 "resolved": sum(t.state == "Resolved" for t in tickets)}
    return page(request, "dashboard.html", title="My helpdesk", tickets=tickets, stats=stats)

@app.get("/tickets/new", response_class=HTMLResponse)
def new_ticket_form(request: Request):
    with SessionLocal() as db:
        need_user(request, db)
    return page(request, "new_ticket.html", title="New support ticket", error=None)

@app.post("/tickets/new", response_class=HTMLResponse)
def create_ticket(request: Request, title: str = Form(""), description: str = Form(""),
                  category: str = Form(""), priority: str = Form("Medium"), csrf_form: str = Form("", alias="_csrf")):
    require_csrf(request, csrf_form)
    title, description = title.strip(), description.strip()
    with SessionLocal() as db:
        u = need_user(request, db)
        if u.role == "admin":
            raise HTTPException(status_code=403, detail="Student ticket submission only")
        if not (5 <= len(title) <= 120) or not (15 <= len(description) <= 2000) or category not in CATEGORY_OPTIONS or priority not in PRIORITY_OPTIONS:
            return page(request, "new_ticket.html", title="New support ticket", error="Title: 5–120 characters; description: 15–2000 characters. Choose valid category and priority.")
        ticket = Ticket(user_id=u.id, title=title, description=description, category=category, priority=priority)
        db.add(ticket)
        db.flush()
        db.add(TicketEvent(ticket_id=ticket.id, author_id=u.id, note="Ticket created"))
        db.commit()
        ticket_id = ticket.id
    return navigate(f"/tickets/{ticket_id}")

@app.get("/tickets/{ticket_id}", response_class=HTMLResponse)
def ticket_detail(ticket_id: int, request: Request):
    with SessionLocal() as db:
        u = need_user(request, db)
        ticket = db.get(Ticket, ticket_id)
        if not ticket:
            raise HTTPException(404, "Ticket not found")
        if u.role != "admin" and ticket.user_id != u.id:
            raise HTTPException(403, "Not authorized")
        events = db.scalars(select(TicketEvent).where(TicketEvent.ticket_id == ticket_id).order_by(TicketEvent.created_at.desc())).all()
        # Force loading relationships while session is open.
        owner_name = ticket.owner.name
        event_info = [{"note": e.note, "author": e.author.name, "date": e.created_at} for e in events]
    return page(request, "ticket_detail.html", title=f"Ticket #{ticket_id}", ticket=ticket,
                owner_name=owner_name, events=event_info)

@app.get("/admin", response_class=HTMLResponse)
def admin_dashboard(request: Request, state: str = "All"):
    with SessionLocal() as db:
        need_admin(request, db)
        query = select(Ticket).order_by(Ticket.created_at.desc())
        if state in STATE_OPTIONS:
            query = query.where(Ticket.state == state)
        tickets = db.scalars(query).all()
        for ticket in tickets:
            _ = ticket.owner.name
        all_tickets = db.scalars(select(Ticket)).all()
        stats = {"total": len(all_tickets), "open": sum(t.state == "Open" for t in all_tickets),
                 "progress": sum(t.state == "In Progress" for t in all_tickets),
                 "resolved": sum(t.state == "Resolved" for t in all_tickets)}
        categories = [(cat, sum(t.category == cat for t in all_tickets)) for cat in CATEGORY_OPTIONS]
    return page(request, "admin.html", title="Admin overview", tickets=tickets,
                stats=stats, category_counts=categories, active_state=state)

@app.post("/tickets/{ticket_id}/update")
def update_ticket(ticket_id: int, request: Request, state: str = Form(""), priority: str = Form(""),
                  note: str = Form(""), csrf_form: str = Form("", alias="_csrf")):
    require_csrf(request, csrf_form)
    with SessionLocal() as db:
        admin = need_admin(request, db)
        ticket = db.get(Ticket, ticket_id)
        if not ticket:
            raise HTTPException(404, "Ticket not found")
        if state not in STATE_OPTIONS or priority not in PRIORITY_OPTIONS or len(note.strip()) > 300:
            raise HTTPException(422, "Invalid status, priority or note")
        changes = []
        if state != ticket.state:
            changes.append(f"Status: {ticket.state} → {state}")
        if priority != ticket.priority:
            changes.append(f"Priority: {ticket.priority} → {priority}")
        if note.strip():
            changes.append(note.strip())
        ticket.state, ticket.priority, ticket.updated_at = state, priority, datetime.utcnow()
        if changes:
            db.add(TicketEvent(ticket_id=ticket_id, author_id=admin.id, note=" | ".join(changes)[:400]))
        db.commit()
    return navigate(f"/tickets/{ticket_id}")

@app.get("/api/summary")
def summary(request: Request):
    with SessionLocal() as db:
        need_admin(request, db)
        counts = {state: db.scalar(select(func.count(Ticket.id)).where(Ticket.state == state)) for state in STATE_OPTIONS}
        return {"total": sum(counts.values()), "by_status": counts, "generated_at": datetime.now(timezone.utc).isoformat()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
