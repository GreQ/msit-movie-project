"""Unit tests for the DataManager CRUD layer."""

from models import Movie, User, db


def test_create_and_get_users(dm):
    dm.create_user("Deb")
    dm.create_user("Alice")
    names = [u.name for u in dm.get_users()]
    assert names == ["Alice", "Deb"]  # ordered by name


def test_get_user_unknown_returns_none(dm):
    assert dm.get_user(42) is None


def test_add_and_get_movies_per_user(dm):
    deb = dm.create_user("Deb")
    bob = dm.create_user("Bob")
    dm.add_movie(Movie(name="Titanic", year=1997, user_id=deb.id))
    dm.add_movie(Movie(name="Twister", user_id=deb.id))
    dm.add_movie(Movie(name="Heat", user_id=bob.id))

    assert [m.name for m in dm.get_movies(deb.id)] == ["Titanic", "Twister"]
    assert [m.name for m in dm.get_movies(bob.id)] == ["Heat"]


def test_update_movie(dm):
    deb = dm.create_user("Deb")
    movie = dm.add_movie(Movie(name="Titanc", user_id=deb.id))
    updated = dm.update_movie(movie.id, "Titanic")
    assert updated.name == "Titanic"
    assert dm.get_movie(movie.id).name == "Titanic"


def test_update_unknown_movie_returns_none(dm):
    assert dm.update_movie(999, "x") is None


def test_delete_movie(dm):
    deb = dm.create_user("Deb")
    movie = dm.add_movie(Movie(name="Titanic", user_id=deb.id))
    assert dm.delete_movie(movie.id) is True
    assert dm.get_movies(deb.id) == []
    assert dm.delete_movie(movie.id) is False


def test_deleting_user_cascades_to_movies(dm):
    deb = dm.create_user("Deb")
    dm.add_movie(Movie(name="Titanic", user_id=deb.id))
    db.session.delete(deb)
    db.session.commit()
    assert db.session.execute(db.select(Movie)).scalars().all() == []
    assert db.session.execute(db.select(User)).scalars().all() == []
