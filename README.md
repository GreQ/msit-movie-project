# MoviWeb App

A Flask + SQLAlchemy web app where users keep a list of favourite movies.
Movie details (director, year, poster) are fetched from the
[OMDb API](https://www.omdbapi.com/).

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows  (macOS/Linux: source .venv/bin/activate)
pip install -r requirements.txt
copy .env.example .env          # macOS/Linux: cp .env.example .env
```

Put your OMDb key into `.env` (`OMDB_API_KEY=...`). Without a key the app still
works; movies are saved with their title only.

## Run

```bash
python app.py
```

Open http://localhost:5000. Optional env vars: `PORT`, `HOST` (use `0.0.0.0` on
Codio), `FLASK_DEBUG=1`, `DATABASE_URL`.

## Test

```bash
pytest -q
```

## Routes

| Method | URL | Purpose |
|---|---|---|
| GET | `/` | list users, add-user form |
| POST | `/users` | create a user |
| GET | `/users/<user_id>/movies` | list a user's movies |
| POST | `/users/<user_id>/movies` | add a movie (OMDb lookup) |
| POST | `/users/<user_id>/movies/<movie_id>/update` | rename a movie |
| POST | `/users/<user_id>/movies/<movie_id>/delete` | delete a movie |

See `steps_done.md` for the build protocol and `prompt.md` for a full spec.
