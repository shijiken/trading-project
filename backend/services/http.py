"""Shared HTTP helper for the ETL clients.

EIA and FRED both occasionally return 5xx or time out; a scheduled run that
gives up on the first blip silently leaves a gap in the price history until
the next 6-hour cycle, so transient failures are retried with backoff.
"""
import logging
import time

import requests

log = logging.getLogger(__name__)

MAX_ATTEMPTS = 3
BACKOFF_SECONDS = 2
RETRY_STATUS = {429, 500, 502, 503, 504}


def get_with_retry(url, params=None, timeout=30, max_attempts=MAX_ATTEMPTS, backoff=BACKOFF_SECONDS):
    last_error = None

    for attempt in range(1, max_attempts + 1):
        try:
            resp = requests.get(url, params=params, timeout=timeout)
            if resp.status_code in RETRY_STATUS and attempt < max_attempts:
                log.warning("HTTP %s from %s (attempt %s/%s)", resp.status_code, url, attempt, max_attempts)
                last_error = requests.HTTPError(f"status {resp.status_code}")
            else:
                resp.raise_for_status()
                return resp
        except (requests.Timeout, requests.ConnectionError) as e:
            last_error = e
            log.warning("%s calling %s (attempt %s/%s)", type(e).__name__, url, attempt, max_attempts)

        if attempt < max_attempts:
            time.sleep(backoff * attempt)  # linear backoff

    raise last_error
