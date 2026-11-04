"""LOCAL demo data only. Never run against the public cloud production database."""
import os
from sqlalchemy import select
from app import Base, engine, SessionLocal, User, Ticket, TicketEvent, pw_hash

if not engine.url.get_backend_name() == 'sqlite':
    raise SystemExit('Demo seeding is deliberately restricted to local SQLite.')
Base.metadata.create_all(engine)
with SessionLocal() as db:
    if db.scalar(select(User).where(User.email == 'admin@demo.edu')):
        print('Demo data already present.')
        raise SystemExit(0)
    admin = User(name='Demo Administrator', email='admin@demo.edu', password_hash=pw_hash('AdminDemo123!'), role='admin')
    student = User(name='Demo Student', email='student@demo.edu', password_hash=pw_hash('StudentDemo123!'), role='student')
    db.add_all([admin, student])
    db.flush()
    items = [
        ('Campus Wi-Fi disconnects', 'The campus Wi-Fi disconnects frequently during online classes.', 'Network', 'High', 'Open'),
        ('Lab software access', 'Unable to access the required development software on lab systems.', 'Application', 'Medium', 'In Progress'),
        ('Database login issue', 'My database lab account was not connecting this afternoon.', 'Database', 'Low', 'Resolved'),
        ('Cloud VM request', 'Requesting a small virtual machine for the final year cloud lab demo.', 'Infrastructure', 'Medium', 'Open'),
        ('Password reset support', 'I need help resetting the course portal password securely.', 'Security', 'High', 'In Progress'),
    ]
    for title, description, cat, priority, state in items:
        t = Ticket(user_id=student.id, title=title, description=description,
                   category=cat, priority=priority, state=state)
        db.add(t)
        db.flush()
        db.add(TicketEvent(ticket_id=t.id, author_id=student.id, note='Ticket created'))
        if state != 'Open':
            db.add(TicketEvent(ticket_id=t.id, author_id=admin.id, note='Status updated to ' + state))
    db.commit()
print('Demo account: student@demo.edu / StudentDemo123!')
print('Admin account: admin@demo.edu / AdminDemo123!')
print('Never use these demo passwords on a public deployment.')
