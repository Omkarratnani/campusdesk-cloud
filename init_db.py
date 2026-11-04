"""Create schema and (optionally) provision the admin account from environment."""
import os
from sqlalchemy import select
from app import Base, engine, SessionLocal, User, pw_hash


def initialize():
    Base.metadata.create_all(bind=engine)
    admin_email = os.environ.get('ADMIN_EMAIL', '').strip().lower()
    admin_password = os.environ.get('ADMIN_PASSWORD', '')
    if bool(admin_email) != bool(admin_password):
        raise RuntimeError('Set both ADMIN_EMAIL and ADMIN_PASSWORD or neither')
    if admin_email and len(admin_password) < 12:
        raise RuntimeError('ADMIN_PASSWORD must be at least 12 characters')
    if admin_email:
        with SessionLocal() as db:
            if not db.scalar(select(User).where(User.email == admin_email)):
                db.add(User(name='Campus Admin', email=admin_email,
                            password_hash=pw_hash(admin_password), role='admin'))
                db.commit()
                print('Admin account created.')
            else:
                print('Admin account already exists; password unchanged.')
    print('Database schema ready.')

if __name__ == '__main__':
    initialize()
