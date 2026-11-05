"""MoviWeb App - a Flask + SQLAlchemy web app for favourite movies.

Run it with ``python app.py`` and open http://localhost:5000.

Routes (see guide chapter "Planning Your Routes"):

    GET  /                                           list users + add-user form
    POST /users                                      create a user
    GET  /users/<user_id>/movies                     list a user's movies
    POST /users/<user_id>/movies                     add a movie (OMDb lookup)
    POST /users/<user_id>/movies/<movie_id>/update   rename a movie
    POST /users/<user_id>/movies/<movie_id>/delete   delete a movie
"""

import logging
import os

from dotenv import load_dotenv
from flask import (
    Flask,
    abort,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from sqlalchemy.exc import SQLAlchemyError

import omdb_client
from data_manager import DataManager
from models import db, Movie

load_dotenv()

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DEFAULT_DB_PATH = os.path.join(BASE_DIR, "data", "movies.db")

MAX_USER_NAME_LENGTH = 100
MAX_MOVIE_TITLE_LENGTH = 200

log = logging.getLogger(__name__)
data_manager = DataManager()  # Create an object of your DataManager class


def create_app(test_config=None):
    """Application factory: build and configure the Flask app."""
    app = Flask(__name__)
    app.config.from_mapping(
        SECRET_KEY=os.getenv("FLASK_SECRET_KEY", "dev-only-change-me"),
        SQLALCHEMY_DATABASE_URI=os.getenv(
            "DATABASE_URL", f"sqlite:///{DEFAULT_DB_PATH}"
        ),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
    )
    if test_config:
        app.config.update(test_config)

    os.makedirs(os.path.dirname(DEFAULT_DB_PATH), exist_ok=True)
    db.init_app(app)  # Link the database and the app

    with app.app_context():
        db.create_all()

    register_routes(app)
    register_error_handlers(app)
    return app


# ---------------------------------------------------------------- helpers
def _get_user_or_404(user_id):
    user = data_manager.get_user(user_id)
    if user is None:
        abort(404)
    return user


def _get_users_movie_or_404(user_id, movie_id):
    """Return the movie only if it belongs to ``user_id``."""
    movie = data_manager.get_movie(movie_id)
    if movie is None or movie.user_id != user_id:
        abort(404)
    return movie


def _clean_text(field, max_length):
    """Strip a form field; return ``None`` if empty or too long."""
    value = (request.form.get(field) or "").strip()
    if not value or len(value) > max_length:
        return None
    return value


# ----------------------------------------------------------------- routes
def register_routes(app):
    """Attach all view functions to ``app``."""

    @app.route("/")
    def index():
        """Home page: list all users and show the add-user form."""
        users = data_manager.get_users()
        return render_template("index.html", users=users)

    @app.route("/favicon.ico")
    def favicon():
        """Browsers request /favicon.ico regardless of <link rel=icon>."""
        return redirect(url_for("static", filename="logo.svg"), code=301)

    @app.route("/users", methods=["POST"])
    def create_user():
        """Create a user from the form on the home page."""
        name = _clean_text("name", MAX_USER_NAME_LENGTH)
        if name is None:
            flash(
                f"Please enter a name (1-{MAX_USER_NAME_LENGTH} characters).",
                "error",
            )
            return redirect(url_for("index"))
        try:
            data_manager.create_user(name)
        except SQLAlchemyError:
            log.exception("Could not create user")
            flash("Sorry, the user could not be saved. Please try again.", "error")
            return redirect(url_for("index"))
        flash(f"Welcome, {name}!", "success")
        return redirect(url_for("index"))

    @app.route("/users/<int:user_id>/movies", methods=["GET"])
    def get_movies(user_id):
        """Show the favourite movies of one user."""
        user = _get_user_or_404(user_id)
        movies = data_manager.get_movies(user_id)
        return render_template("movies.html", user=user, movies=movies)

    @app.route("/users/<int:user_id>/movies", methods=["POST"])
    def add_movie(user_id):
        """Add a movie; details are fetched from OMDb when possible."""
        _get_user_or_404(user_id)
        title = _clean_text("title", MAX_MOVIE_TITLE_LENGTH)
        if title is None:
            flash(
                f"Please enter a movie title "
                f"(1-{MAX_MOVIE_TITLE_LENGTH} characters).",
                "error",
            )
            return redirect(url_for("get_movies", user_id=user_id))

        details = omdb_client.fetch_movie(title)
        if details:
            movie = Movie(user_id=user_id, **details)
        else:
            movie = Movie(user_id=user_id, name=title)

        try:
            data_manager.add_movie(movie)
        except SQLAlchemyError:
            log.exception("Could not add movie")
            flash("Sorry, the movie could not be saved. Please try again.", "error")
            return redirect(url_for("get_movies", user_id=user_id))

        if details:
            flash(f"Added “{movie.name}”.", "success")
        else:
            flash(
                f"Added “{title}”, but no details were found on OMDb "
                "(unknown title, no API key or no connection).",
                "warning",
            )
        return redirect(url_for("get_movies", user_id=user_id))

    @app.route(
        "/users/<int:user_id>/movies/<int:movie_id>/update", methods=["POST"]
    )
    def update_movie(user_id, movie_id):
        """Rename a movie without consulting OMDb."""
        _get_users_movie_or_404(user_id, movie_id)
        new_title = _clean_text("title", MAX_MOVIE_TITLE_LENGTH)
        if new_title is None:
            flash("The title must not be empty.", "error")
            return redirect(url_for("get_movies", user_id=user_id))
        try:
            data_manager.update_movie(movie_id, new_title)
        except SQLAlchemyError:
            log.exception("Could not update movie")
            flash("Sorry, the movie could not be updated.", "error")
            return redirect(url_for("get_movies", user_id=user_id))
        flash(f"Renamed to “{new_title}”.", "success")
        return redirect(url_for("get_movies", user_id=user_id))

    @app.route(
        "/users/<int:user_id>/movies/<int:movie_id>/delete", methods=["POST"]
    )
    def delete_movie(user_id, movie_id):
        """Remove a movie from the user's favourites."""
        movie = _get_users_movie_or_404(user_id, movie_id)
        name = movie.name
        try:
            data_manager.delete_movie(movie_id)
        except SQLAlchemyError:
            log.exception("Could not delete movie")
            flash("Sorry, the movie could not be deleted.", "error")
            return redirect(url_for("get_movies", user_id=user_id))
        flash(f"Deleted “{name}”.", "success")
        return redirect(url_for("get_movies", user_id=user_id))


# --------------------------------------------------------- error handling
def register_error_handlers(app):
    """Render friendly pages for common HTTP errors."""

    @app.errorhandler(404)
    def page_not_found(error):
        return render_template("404.html"), 404

    @app.errorhandler(405)
    def method_not_allowed(error):
        return render_template(
            "error.html",
            code=405,
            message="That action is not allowed on this page.",
        ), 405

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template(
            "error.html",
            code=500,
            message="Something went wrong on our side. Please try again.",
        ), 500


app = create_app()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    app.run(
        host=os.getenv("HOST", "127.0.0.1"),  # use 0.0.0.0 on Codio
        port=int(os.getenv("PORT", "5000")),
        debug=os.getenv("FLASK_DEBUG") == "1",
    )
