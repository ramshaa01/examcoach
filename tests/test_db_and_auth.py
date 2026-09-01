"""Unit tests for SQLite database and bcrypt authentication."""
import os
import pytest
from db.database import init_db, get_session
from db.models import User, Attempt, TopicMastery, MockExamResult
from db.auth import create_user, authenticate, hash_password, verify_password


def test_password_hashing():
    raw = "MySecurePassword123!"
    hashed = hash_password(raw)
    assert hashed != raw
    assert verify_password(raw, hashed) is True
    assert verify_password("WrongPassword", hashed) is False


def test_user_creation_and_authentication():
    init_db()
    test_uname = "pytest_user_99"
    test_pass = "TestPass123"

    user = create_user(test_uname, test_pass)
    assert user.id is not None
    assert user.username == test_uname

    # Authenticate
    auth_user = authenticate(test_uname, test_pass)
    assert auth_user is not None
    assert auth_user.id == user.id

    # Wrong credentials
    assert authenticate(test_uname, "wrongpass") is None
    assert authenticate("nonexistent_user", test_pass) is None


def test_attempt_and_mastery_models():
    init_db()
    with get_session() as session:
        user = session.query(User).first()
        if not user:
            user = User(username="test_schema", password_hash="dummy")
            session.add(user)
            session.flush()

        attempt = Attempt(
            user_id=user.id,
            subject="JEE Physics",
            topic="Thermodynamics",
            difficulty="Moderate (Exam Level)",
            question="Calculate work done in isothermal process",
            student_answer="W = nRT ln(V2/V1)",
            feedback="Correct derivation.",
            score=10.0,
            is_correct=True,
            error_type="None",
        )
        session.add(attempt)
        session.flush()
        assert attempt.id is not None
