"""Shared pytest fixtures: every test gets an isolated, throwaway SQLite DB."""
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture(autouse=True)
def isolated_db(tmp_path, monkeypatch):
    import db.database as database
    from sqlalchemy.orm import sessionmaker

    db_path = str(tmp_path / "test_examcoach.db")
    test_engine = database._make_engine(db_path)
    monkeypatch.setattr(database, "DB_PATH", db_path)
    monkeypatch.setattr(database, "engine", test_engine)
    monkeypatch.setattr(database, "SessionLocal", sessionmaker(bind=test_engine, expire_on_commit=False))
    database.init_db()
    yield
    test_engine.dispose()
