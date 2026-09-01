"""Lightweight single-user auth: bcrypt-hashed password gate with SQLite-backed storage."""
from __future__ import annotations

from typing import Optional

import bcrypt

from db.database import get_session
from db.models import User


def hash_password(raw_password: str) -> str:
    return bcrypt.hashpw(raw_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(raw_password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(raw_password.encode("utf-8"), password_hash.encode("utf-8"))


def any_user_exists() -> bool:
    with get_session() as session:
        return session.query(User).first() is not None


def create_user(username: str, raw_password: str) -> User:
    with get_session() as session:
        user = User(username=username.strip(), password_hash=hash_password(raw_password))
        session.add(user)
        session.flush()
        session.refresh(user)
        session.expunge(user)
        return user


def authenticate(username: str, raw_password: str) -> Optional[User]:
    with get_session() as session:
        user = session.query(User).filter(User.username == username.strip()).first()
        if user and verify_password(raw_password, user.password_hash):
            session.expunge(user)
            return user
        return None


def get_user_by_id(user_id: int) -> Optional[User]:
    with get_session() as session:
        user = session.get(User, user_id)
        if user:
            session.expunge(user)
        return user
