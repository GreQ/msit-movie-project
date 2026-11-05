"""Tests for the OMDb client (HTTP is mocked, no network needed)."""

import requests

import omdb_client


class FakeResponse:
    def __init__(self, payload, status=200):
        self._payload = payload
        self.status_code = status

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"{self.status_code}")

    def json(self):
        return self._payload


def test_no_api_key_returns_none(monkeypatch):
    def fail(*args, **kwargs):
        raise AssertionError("must not call the network without a key")
    monkeypatch.setattr(omdb_client.requests, "get", fail)
    assert omdb_client.fetch_movie("Titanic", api_key="") is None


def test_successful_lookup(monkeypatch):
    payload = {
        "Response": "True", "Title": "Titanic", "Year": "1997",
        "Director": "James Cameron", "Poster": "https://img/titanic.jpg",
    }
    monkeypatch.setattr(omdb_client.requests, "get",
                        lambda *a, **k: FakeResponse(payload))
    assert omdb_client.fetch_movie("titanic", api_key="k") == {
        "name": "Titanic", "director": "James Cameron",
        "year": 1997, "poster_url": "https://img/titanic.jpg",
    }


def test_na_values_and_year_ranges(monkeypatch):
    payload = {"Response": "True", "Title": "Some Series", "Year": "2011–2019",
               "Director": "N/A", "Poster": "N/A"}
    monkeypatch.setattr(omdb_client.requests, "get",
                        lambda *a, **k: FakeResponse(payload))
    result = omdb_client.fetch_movie("x", api_key="k")
    assert result["year"] == 2011
    assert result["director"] is None
    assert result["poster_url"] is None


def test_movie_not_found(monkeypatch):
    payload = {"Response": "False", "Error": "Movie not found!"}
    monkeypatch.setattr(omdb_client.requests, "get",
                        lambda *a, **k: FakeResponse(payload))
    assert omdb_client.fetch_movie("zzzz", api_key="k") is None


def test_network_error(monkeypatch):
    def boom(*a, **k):
        raise requests.ConnectionError("offline")
    monkeypatch.setattr(omdb_client.requests, "get", boom)
    assert omdb_client.fetch_movie("Titanic", api_key="k") is None


def test_http_error(monkeypatch):
    monkeypatch.setattr(omdb_client.requests, "get",
                        lambda *a, **k: FakeResponse({}, status=401))
    assert omdb_client.fetch_movie("Titanic", api_key="bad") is None
