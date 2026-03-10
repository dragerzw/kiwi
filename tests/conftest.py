from __future__ import annotations

import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))
from typing import Generator

import pytest
from app import create_app
from app.config import TestConfig
from app.db import db
from app.models import User
from sqlalchemy.orm import Session


@pytest.fixture(scope='session')
def app():
    """Create and configure a new app instance for each test session."""
    app = create_app(TestConfig)
    
    # establish an application context before running the tests
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture(scope='session')
def client(app):
    """A test client for the app."""
    return app.test_client()

@pytest.fixture(scope='function')
def auth_headers(monkeypatch):
    """Provides valid authorization headers for tests."""
    monkeypatch.setattr('app.auth.auth.jwt.get_unverified_header', lambda x: {"kid": "key1"})
    monkeypatch.setattr('app.auth.auth.get_jwks', lambda: {"keys": [{"kid": "key1", "kty": "RSA", "alg": "RS256"}]})
    monkeypatch.setattr('app.auth.auth.RSAAlgorithm.from_jwk', lambda x: "dummy_rsa_key")
    
    def mock_decode(*args, **kwargs):
        return {"sub": "admin", "username": "admin"}
    monkeypatch.setattr('app.auth.auth.jwt.decode', mock_decode)

    return {"Authorization": "Bearer validtoken"}


@pytest.fixture(scope='function', autouse=True)
def db_session(app) -> Generator[Session]:
    """A database session scoped to a single test function."""
    with app.app_context():
        db.create_all()
        
        _populate_database(db.session)
        
        try:
            yield db.session
        finally:
            db.session.remove()
            db.drop_all()


def _populate_database(session):
    admin_user = User(username='admin', password='admin', firstname='Admin', lastname='User', balance=1000.00)
    session.add(admin_user)
    session.commit()
