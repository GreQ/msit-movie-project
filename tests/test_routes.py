"""Integration tests for the Flask routes (OMDb is always mocked)."""

from sqlalchemy.exc import OperationalError

from models import Movie


def _make_user(dm, name="Deb"):
    return dm.create_user(name)


# ------------------------------------------------------------------ users
def test_index_empty(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"No users yet" in response.data


def test_create_user_and_list(client):
    response = client.post("/users", data={"name": "  Deb  "}, follow_redirects=True)
    assert response.status_code == 200
    assert b"Welcome, Deb!" in response.data
    assert b'href="/users/1/movies"' in response.data


def test_create_user_rejects_blank_name(client, dm):
    response = client.post("/users", data={"name": "   "}, follow_redirects=True)
    assert b"Please enter a name" in response.data
    assert dm.get_users() == []


def test_create_user_rejects_too_long_name(client, dm):
    client.post("/users", data={"name": "x" * 101})
    assert dm.get_users() == []


def test_get_on_users_is_not_allowed(client):
    response = client.get("/users")
    assert response.status_code == 405
    assert b"not allowed" in response.data


# ----------------------------------------------------------------- movies
def test_movies_page_for_unknown_user_is_404(client):
    response = client.get("/users/99/movies")
    assert response.status_code == 404
    assert b"Page not found" in response.data


def test_add_movie_with_omdb_data(client, dm, fake_omdb):
    user = _make_user(dm)
    response = client.post(
        f"/users/{user.id}/movies", data={"title": "titanic"}, follow_redirects=True
    )
    assert response.status_code == 200
    assert b"Added" in response.data
    assert b"James Cameron" in response.data
    assert b"https://example.com/poster.jpg" in response.data
    movie = dm.get_movies(user.id)[0]
    assert (movie.name, movie.year) == ("Titanic", 1997)


def test_add_movie_falls_back_to_title_only(client, dm, no_omdb):
    user = _make_user(dm)
    response = client.post(
        f"/users/{user.id}/movies", data={"title": "Unknown Film"}, follow_redirects=True
    )
    assert b"no details were found" in response.data
    movie = dm.get_movies(user.id)[0]
    assert movie.name == "Unknown Film"
    assert movie.director is None


def test_add_movie_rejects_blank_title(client, dm, no_omdb):
    user = _make_user(dm)
    client.post(f"/users/{user.id}/movies", data={"title": ""})
    assert dm.get_movies(user.id) == []


def test_add_movie_to_unknown_user_is_404(client, no_omdb):
    assert client.post("/users/5/movies", data={"title": "x"}).status_code == 404


def test_update_movie(client, dm):
    user = _make_user(dm)
    movie = dm.add_movie(Movie(name="Titanc", user_id=user.id))
    response = client.post(
        f"/users/{user.id}/movies/{movie.id}/update",
        data={"title": "Titanic"},
        follow_redirects=True,
    )
    assert b"Renamed to" in response.data
    assert dm.get_movie(movie.id).name == "Titanic"


def test_update_movie_of_other_user_is_404(client, dm):
    deb = _make_user(dm, "Deb")
    bob = _make_user(dm, "Bob")
    movie = dm.add_movie(Movie(name="Heat", user_id=bob.id))
    response = client.post(
        f"/users/{deb.id}/movies/{movie.id}/update", data={"title": "Hacked"}
    )
    assert response.status_code == 404
    assert dm.get_movie(movie.id).name == "Heat"


def test_delete_movie(client, dm):
    user = _make_user(dm)
    movie = dm.add_movie(Movie(name="Titanic", user_id=user.id))
    response = client.post(
        f"/users/{user.id}/movies/{movie.id}/delete", follow_redirects=True
    )
    assert b"Deleted" in response.data
    assert dm.get_movies(user.id) == []


def test_delete_unknown_movie_is_404(client, dm):
    user = _make_user(dm)
    assert client.post(f"/users/{user.id}/movies/9/delete").status_code == 404


def test_html_in_titles_is_escaped(client, dm, no_omdb):
    user = _make_user(dm)
    response = client.post(
        f"/users/{user.id}/movies",
        data={"title": "<script>alert(1)</script>"},
        follow_redirects=True,
    )
    assert b"<script>alert(1)</script>" not in response.data
    assert b"&lt;script&gt;" in response.data


def test_database_error_shows_friendly_message(client, dm, monkeypatch):
    def broken(name):
        raise OperationalError("INSERT", {}, Exception("disk full"))
    monkeypatch.setattr(dm, "create_user", broken)
    response = client.post("/users", data={"name": "Deb"}, follow_redirects=True)
    assert response.status_code == 200
    assert b"could not be saved" in response.data


def test_favicon_redirects_to_logo(client):
    response = client.get("/favicon.ico")
    assert response.status_code == 301
    assert response.headers["Location"].endswith("/static/logo.svg")
