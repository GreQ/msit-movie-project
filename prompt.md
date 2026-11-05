# Prompt to recreate the MoviWeb App

Copy everything below the line into an AI coding assistant (or use it as a
spec for yourself) to build an equivalent application from scratch.

---

Build **MoviWeb App**, a small Python web application where several users each
keep a list of favourite movies. Movie details come from the OMDb API.

## Tech stack

- Python 3.12+ in a virtual environment (`.venv`).
- Latest releases of: `Flask`, `Flask-SQLAlchemy`, `SQLAlchemy`, `requests`,
  `python-dotenv`, `pytest` – pin exact versions in `requirements.txt`.
- SQLite database at `data/movies.db`, accessed only via SQLAlchemy ORM.
- Jinja2 templates + one hand-written CSS file (no CSS framework, no JS framework).
- Git repository on branch `main`; commit after every logical step with
  descriptive messages (subject line + body explaining what and why).

## Project layout

```
MoviWebApp/
├── app.py              # Flask app factory, routes, error handlers
├── models.py           # db = SQLAlchemy(); User and Movie models
├── data_manager.py     # DataManager class – all DB CRUD
├── omdb_client.py      # fetch_movie(title) -> dict | None
├── requirements.txt
├── .env.example        # OMDB_API_KEY=, FLASK_SECRET_KEY=
├── .gitignore          # .venv, __pycache__, .pytest_cache, .env, data/*.db
├── data/.gitkeep
├── static/style.css, static/logo.svg
├── templates/base.html, index.html, movies.html, 404.html, error.html
└── tests/conftest.py, test_data_manager.py, test_routes.py, test_omdb_client.py
```

## Data model (`models.py`)

- `db = SQLAlchemy()` created without an app (bound later with `db.init_app(app)`).
- `User`: `id` Integer PK, `name` String(100) not null,
  `movies` relationship (back_populates, `cascade="all, delete-orphan"`).
- `Movie`: `id` Integer PK, `name` String(200) not null, `director` String(200),
  `year` Integer, `poster_url` String(500),
  `user_id` Integer `ForeignKey('user.id')` not null, `user` relationship.

## DataManager (`data_manager.py`)

Class `DataManager` using `db.session` and SQLAlchemy 2.x `db.select(...)`:

- `create_user(name)` → User
- `get_users()` → list ordered by name
- `get_user(user_id)` / `get_movie(movie_id)` → object or `None`
- `get_movies(user_id)` → list of that user's movies
- `add_movie(movie)` – takes a ready `Movie` object
- `update_movie(movie_id, new_title)` → movie or `None`
- `delete_movie(movie_id)` → `True`/`False`

Every commit is wrapped: on `SQLAlchemyError` call `db.session.rollback()` and re-raise.

## OMDb client (`omdb_client.py`)

`fetch_movie(title, api_key=None)`:
- key from argument or env `OMDB_API_KEY`; no key → return `None` without a request;
- `GET https://www.omdbapi.com/?apikey=KEY&t=TITLE`, timeout 5 s;
- returns `{"name", "director", "year", "poster_url"}`; convert `"N/A"` to `None`,
  parse `year` from the first 4 digits (handles `"2011–2019"`);
- returns `None` on network/HTTP errors, invalid JSON or `"Response": "False"`;
  never raises.

## Flask app (`app.py`)

- `load_dotenv()`; `create_app(test_config=None)` factory; module-level
  `app = create_app()`; `if __name__ == "__main__": app.run(...)` using env
  `HOST` (default `127.0.0.1`), `PORT` (default 5000), `FLASK_DEBUG=1` for debug.
- Config: `SECRET_KEY` from `FLASK_SECRET_KEY`; `SQLALCHEMY_DATABASE_URI` from
  env `DATABASE_URL`, default `sqlite:///<abs project dir>/data/movies.db`
  (create the `data` folder); `SQLALCHEMY_TRACK_MODIFICATIONS=False`;
  `db.create_all()` inside an app context.
- One module-level `data_manager = DataManager()`.

Routes (use `int` converters):

| Method | URL | Endpoint | Behaviour |
|---|---|---|---|
| GET | `/` | `index` | render `index.html` with all users |
| POST | `/users` | `create_user` | trim `name`, 1–100 chars, else flash error; redirect `/` |
| GET | `/users/<user_id>/movies` | `get_movies` | 404 if user missing; render `movies.html` |
| POST | `/users/<user_id>/movies` | `add_movie` | trim `title` (1–200); call `omdb_client.fetch_movie`; if data → `Movie(user_id=..., **data)`, else `Movie(name=title)` + warning flash; redirect |
| POST | `/users/<user_id>/movies/<movie_id>/update` | `update_movie` | movie must exist **and belong to user** else 404; rename only (no OMDb) |
| POST | `/users/<user_id>/movies/<movie_id>/delete` | `delete_movie` | same ownership check; delete; redirect |
| GET | `/favicon.ico` | `favicon` | 301 to `static/logo.svg` |

- Catch `SQLAlchemyError` around writes → flash "could not be saved" instead of 500.
- Flash categories: `success`, `warning`, `error`.
- Error handlers: 404 → `404.html`; 405 and 500 → `error.html` (500 also rolls back the session).

## Templates

- `base.html`: `<link>` to `url_for('static', filename='style.css')`; header with
  clickable logo "MovieApp" linking home and a "Users" nav link; flash message
  list; `<main class="container">{% block content %}{% endblock %}</main>`; footer
  crediting OMDb.
- `index.html` (extends base): `<h1>Users</h1>`, `<ul class="user-list">` with a
  link per user to `url_for('get_movies', user_id=user.id)`, empty-state text,
  form `action="{{ url_for('create_user') }}" method="post"` with input + button.
- `movies.html`: "← Back to Users", `<h1>Movies for {{ user.name }}</h1>`, add-movie
  form, grid of cards: poster `<img>` (or 🎬 placeholder), inline update form
  (text input pre-filled with the title + "Update" button), Year, Director,
  red "Delete" button whose form asks `confirm()` – pass the title via
  `data-title` and read `this.dataset.title` (never inline the title into JS).
- `404.html`, `error.html`: friendly message + button back to users.
- All labels present (visually hidden) for accessibility; Jinja autoescaping on.

## Styling (`static/style.css`)

Blue header (#2563eb), light grey background, white rounded cards with soft
shadow, responsive CSS grid (`repeat(auto-fill, minmax(200px, 1fr))`) for users
and movies, posters with `aspect-ratio: 2/3; object-fit: cover`, blue primary and
red danger buttons with hover/active feedback, card lift on hover, coloured
left border for flash messages. Simple SVG clapperboard logo.

## Tests (pytest)

- `conftest.py`: put project root on `sys.path`; set `DATABASE_URL=sqlite://` and
  empty `OMDB_API_KEY` **before** importing `app`; `app` fixture builds
  `create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": sqlite file in tmp_path})`,
  yields inside an app context, then `session.remove()`, `drop_all()`,
  `engine.dispose()`; fixtures `client`, `dm` (depends on `app`), `no_omdb` and
  `fake_omdb` (monkeypatch `app.omdb_client.fetch_movie`).
- Cover: every DataManager method incl. cascade delete; all routes; blank/too-long
  input; 404 for unknown user/movie; 405 for `GET /users`; ownership check;
  HTML escaping of titles; DB error → friendly flash; OMDb client success,
  no key (no network call), `N/A`, year range, not found, network and HTTP errors.
- Must pass with `pytest -q -W error`.

## Docs

`README.md` (setup, run, test, routes), `steps_done.md` (protocol of the work).

## Acceptance checks

1. `pip install -r requirements.txt`, `pytest -q -W error` → all green.
2. `python app.py` → http://localhost:5000 shows the user list.
3. Create a user, add a movie (with a valid OMDb key you see poster, year,
   director; without one the movie is saved with title only and a warning),
   rename it, delete it; unknown URLs show the custom 404 page.
