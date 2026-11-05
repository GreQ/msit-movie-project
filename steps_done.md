# Protocol – MoviWeb App (Flask + SQLAlchemy)

Protocol of how the Codio guide *"Movie Project – Flask + SqlAlchemy (new)"*
was turned into this project. Date: 2026-11-05.

## 1. Reading the guide

- Opened the guide in Chrome with the Claude in Chrome extension.
- The guide is rendered in a cross-origin iframe (`*.codio.io/__guides__.html`),
  so its text could not be extracted directly. The guide files are not stored
  in the Codio workspace either (`.guides/` only has images, a script and
  `styles.css`). I therefore paged through all 17 sections with screenshots
  and expanded every collapsible hint.
- Sections read:
  1. Flask Web Application – goal: turn the CLI movie app into a web app;
     users register a name and keep a list of favourite movies, details from OMDb.
  2. Setting Up Your Development Environment – new project `MoviWebApp`,
     virtual environment, `pip install flask`, GitHub repo, commit regularly.
  3. Project Structure and Core Functionalities – UI (Flask/HTML/CSS) +
     data management class; create/select users; add, delete, update, list movies.
  4. Planning Project Structure – `app.py`, `static/`, `templates/`, `venv/`.
  5. Database – User (`id`, `name`), Movie (`id`, `name`, `director`, `year`,
     `poster_url`); link via a `user_id` foreign key in the Movie table.
  6. SQLAlchemy ORM – `models.py` with `db = SQLAlchemy()`, `User` and `Movie` models.
  7. Data Manager – `data_manager.py` with `create_user`, `get_users`,
     `get_movies(user_id)`, `add_movie(movie)`, `update_movie(movie_id, new_title)`,
     `delete_movie(movie_id)`; OMDb may be fetched in the data manager or in `app.py`.
  8. Setting Up Your Flask Application – config `sqlite:///data/movies.db`,
     `db.init_app(app)`, `db.create_all()` in an app context, `app.run()`.
  9. Integrating DataManager – first `/users` test route.
  10. Planning Your Routes – the six routes (see below); update edits the title
      without OMDb; fetch OMDb data, build a `Movie` object, show posters.
  11. Templates – `base.html` with `{% block content %}`, `static/style.css`.
  12. Display users – `index.html` user list linking to `get_movies`,
      add-user form posting to `create_user`, `index()` hint.
  13. Building the Other Routes – templates, DataManager, route parameters, forms.
  14. Error Handling – 404 handler with `404.html`, try/except around I/O.
  15. BONUS: User Experience Design – CSS, logo, colour scheme, navigation,
      "back to users", clickable logo, hover feedback.
  16. BONUS: Deploying (PythonAnywhere) – optional, not done.
  17. Submit Project – upload code, push to GitHub.

## 2. Decisions taken with the user

| Question | Decision |
|---|---|
| OMDb API key | No key yet → key read from `.env` (`OMDB_API_KEY`); **fallback**: save the movie with the title only and show a warning |
| Where to fetch OMDb data | In `app.py` via a separate `omdb_client.py`; a ready `Movie` object is passed to `DataManager.add_movie(movie)` (guide's suggested signature) |
| Styling | Hand-written `static/style.css`, no CSS framework |
| Tests | Yes, pytest suite with OMDb mocked |
| Raw SQL vs ORM | SQLAlchemy ORM (the project title and guide hints use it) |

## 3. Implementation steps (one git commit each)

1. **Skeleton** – `git init -b main`; `python -m venv .venv` (Python 3.15.0);
   installed the latest releases: Flask 3.1.3, Flask-SQLAlchemy 3.1.1,
   SQLAlchemy 2.1.8, requests 2.34.2, python-dotenv 1.2.4, pytest 9.2.0 →
   pinned in `requirements.txt`. Created `.gitignore` (venv, caches, `.env`,
   `data/*.db`), `.env.example`, `data/`, `static/`, `templates/`, `tests/`.
2. **Models + DataManager** – `models.py` (User/Movie, one-to-many relationship,
   cascade delete), `data_manager.py` (all guide methods plus `get_user`/`get_movie`;
   commits roll back on `SQLAlchemyError`).
3. **OMDb client** – `omdb_client.fetch_movie(title)` returns
   `name/director/year/poster_url` or `None` (no key, network/HTTP error,
   bad JSON, "Movie not found"); cleans `N/A`, parses year ranges.
4. **Flask app** – `app.py` with `create_app()` factory, config from `.env`,
   the six routes, input validation (trim, length limits), ownership checks
   (movie must belong to the user in the URL), flash messages, 404/405/500 handlers.
5. **Templates & CSS** – `base.html` (logo, nav, flashes, footer), `index.html`,
   `movies.html` (poster card grid, inline rename form, delete with confirm),
   `404.html`, `error.html`, `static/style.css`, `static/logo.svg`.
6. **Tests** – `tests/` with 29 (later 30) tests for DataManager, routes and
   OMDb client.
7. **Bug fix found by manual testing** – `/favicon.ico` 404 → redirect to logo.
8. **Documentation** – this file, `prompt.md`, `README.md`.

### Route map implemented

| Method | URL | Function |
|---|---|---|
| GET | `/` | `index` – list users + add-user form |
| POST | `/users` | `create_user` |
| GET | `/users/<int:user_id>/movies` | `get_movies` |
| POST | `/users/<int:user_id>/movies` | `add_movie` (OMDb lookup, fallback) |
| POST | `/users/<int:user_id>/movies/<int:movie_id>/update` | `update_movie` |
| POST | `/users/<int:user_id>/movies/<int:movie_id>/delete` | `delete_movie` |

## 4. Bugs found and fixed while checking

| # | Problem | Fix |
|---|---|---|
| 1 | Delete-confirm JavaScript would break for titles containing `'` (e.g. *Schindler's List*) because Jinja escaping is decoded by the HTML parser before JS runs | Title passed via `data-title` attribute and read with `this.dataset.title` (verified in the browser) |
| 2 | 7 DataManager tests failed with "Working outside of application context" | `dm` fixture now depends on the `app` fixture |
| 3 | Under `pytest -W error`, unclosed SQLite connections (Python 3.15 `ResourceWarning`) | `db.engine.dispose()` in fixture teardown |
| 4 | Every page caused a `GET /favicon.ico 404` in the server log | `/favicon.ico` route redirecting to `static/logo.svg` + test |
| 5 | Importing `app.py` in tests would have created/touched the real `data/movies.db` | DB URI overridable via `DATABASE_URL`; tests set it to in-memory before import |

## 5. Verification

- `pytest -q -W error` → **30 passed** (warnings treated as errors).
- Ran the real server (`python app.py`) and used it in the browser pane:
  created user "Deb", added "Schindler's List" (no API key → title-only movie
  with warning flash), renamed it to "Titanic", deleted it. No console errors,
  no server errors, CSS and logo load.
- `pip list --outdated` → nothing outdated.
- Not verified: a real OMDb lookup (no API key available yet). The success path
  is covered by mocked tests; once a key is in `.env` posters/director/year appear.
- Not done: deployment to PythonAnywhere (bonus), pushing to a GitHub remote.
