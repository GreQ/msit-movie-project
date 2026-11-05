"""Shared pytest fixtures: a fresh app + empty database per test."""

import os
import sys

import pytest

# Make the project root importable and keep the real data/movies.db
# untouched when app.py builds its module-level app on import.
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)
os.environ["DATABASE_URL"] = "sqlite://"
os.environ["OMDB_API_KEY"] = ""

import app as app_module  # noqa: E402
from models import db  # noqa: E402


@pytest.fixture
def app(tmp_path):
    flask_app = app_module.create_app({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": f"sqlite:///{tmp_path / 'test.db'}",
    })
    with flask_app.app_context():
        yield flask_app
        db.session.remove()
        db.drop_all()
        db.engine.dispose()  # close pooled SQLite connections


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def dm(app):
    """DataManager bound to the per-test app context."""
    return app_module.data_manager


@pytest.fixture
def no_omdb(monkeypatch):
    """Simulate OMDb returning nothing."""
    monkeypatch.setattr(app_module.omdb_client, "fetch_movie", lambda title: None)


@pytest.fixture
def fake_omdb(monkeypatch):
    """Simulate a successful OMDb lookup."""
    def fetch(title):
        return {
            "name": title.title(),
            "director": "James Cameron",
            "year": 1997,
            "poster_url": "https://example.com/poster.jpg",
        }
    monkeypatch.setattr(app_module.omdb_client, "fetch_movie", fetch)
