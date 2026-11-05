"""DataManager: the single place where the app talks to the database.

All CRUD operations go through this class (guide: "Data Management").
Methods raise ``SQLAlchemyError`` subclasses only after rolling the
session back, so a failed write never leaves the session in a broken
state; the Flask routes catch these and show a friendly message.
"""

from sqlalchemy.exc import SQLAlchemyError

from models import db, User, Movie


class DataManager:
    """CRUD operations for users and their favourite movies."""

    # ----------------------------------------------------------- helpers
    @staticmethod
    def _commit():
        """Commit the session; roll back and re-raise on failure."""
        try:
            db.session.commit()
        except SQLAlchemyError:
            db.session.rollback()
            raise

    # ------------------------------------------------------------- users
    def create_user(self, name):
        """Add a new user to the database and return it."""
        new_user = User(name=name)
        db.session.add(new_user)
        self._commit()
        return new_user

    def get_users(self):
        """Return a list of all users, ordered by name."""
        return db.session.execute(
            db.select(User).order_by(User.name, User.id)
        ).scalars().all()

    def get_user(self, user_id):
        """Return the user with ``user_id`` or ``None``."""
        return db.session.get(User, user_id)

    # ------------------------------------------------------------ movies
    def get_movies(self, user_id):
        """Return a list of all movies of a specific user."""
        return db.session.execute(
            db.select(Movie).filter_by(user_id=user_id).order_by(Movie.id)
        ).scalars().all()

    def get_movie(self, movie_id):
        """Return the movie with ``movie_id`` or ``None``."""
        return db.session.get(Movie, movie_id)

    def add_movie(self, movie):
        """Add a new ``Movie`` object (already linked to a user)."""
        db.session.add(movie)
        self._commit()
        return movie

    def update_movie(self, movie_id, new_title):
        """Change the title of a movie. Returns the movie or ``None``."""
        movie = self.get_movie(movie_id)
        if movie is None:
            return None
        movie.name = new_title
        self._commit()
        return movie

    def delete_movie(self, movie_id):
        """Delete a movie. Returns ``True`` if it existed."""
        movie = self.get_movie(movie_id)
        if movie is None:
            return False
        db.session.delete(movie)
        self._commit()
        return True
