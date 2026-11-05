"""SQLAlchemy ORM models for the MoviWeb app.

The ``db`` object is created here without an app and bound later in
``app.py`` via ``db.init_app(app)``, exactly as described in the guide.
"""

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class User(db.Model):
    """A person who keeps a list of favourite movies."""

    __tablename__ = "user"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)

    # One user -> many movies. Deleting a user removes their movies too.
    movies = db.relationship(
        "Movie",
        back_populates="user",
        cascade="all, delete-orphan",
        order_by="Movie.id",
    )

    def __repr__(self):
        return f"<User id={self.id} name={self.name!r}>"

    def __str__(self):
        return self.name


class Movie(db.Model):
    """A movie on one user's favourites list."""

    __tablename__ = "movie"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    director = db.Column(db.String(200))
    year = db.Column(db.Integer)
    poster_url = db.Column(db.String(500))

    # Link Movie to User
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    user = db.relationship("User", back_populates="movies")

    def __repr__(self):
        return (
            f"<Movie id={self.id} name={self.name!r} year={self.year} "
            f"user_id={self.user_id}>"
        )

    def __str__(self):
        return f"{self.name} ({self.year})" if self.year else self.name
