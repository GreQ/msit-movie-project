"""Tiny client for the OMDb API (https://www.omdbapi.com/).

``fetch_movie`` never raises: on a missing key, network problem or an
unknown title it returns ``None`` so the caller can fall back to saving
the movie with the title only.
"""

import logging
import os

import requests

OMDB_URL = "https://www.omdbapi.com/"
TIMEOUT_SECONDS = 5

log = logging.getLogger(__name__)


def _parse_year(raw_year):
    """OMDb years look like '1997' or '2011–2019'; keep the first 4 digits."""
    if raw_year and raw_year[:4].isdigit():
        return int(raw_year[:4])
    return None


def _clean(value):
    """OMDb uses the string 'N/A' for missing values."""
    return None if not value or value == "N/A" else value


def fetch_movie(title, api_key=None):
    """Look up ``title`` on OMDb.

    Returns a dict with keys ``name``, ``director``, ``year`` and
    ``poster_url`` or ``None`` if nothing could be fetched.
    """
    api_key = api_key if api_key is not None else os.getenv("OMDB_API_KEY")
    if not api_key:
        log.info("No OMDB_API_KEY configured; skipping OMDb lookup.")
        return None

    try:
        response = requests.get(
            OMDB_URL,
            params={"apikey": api_key, "t": title},
            timeout=TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        data = response.json()
    except (requests.RequestException, ValueError) as error:
        log.warning("OMDb request failed: %s", error)
        return None

    if data.get("Response") != "True":
        log.info("OMDb found nothing for %r: %s", title, data.get("Error"))
        return None

    return {
        "name": _clean(data.get("Title")) or title,
        "director": _clean(data.get("Director")),
        "year": _parse_year(data.get("Year")),
        "poster_url": _clean(data.get("Poster")),
    }
