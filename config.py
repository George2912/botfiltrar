import os
from typing import Set


def _parse_user_ids(raw: str | None) -> Set[int]:
    if not raw:
        return set()
    ids: Set[int] = set()
    for item in raw.split(","):
        item = item.strip()
        if not item:
            continue
        try:
            ids.add(int(item))
        except ValueError:
            continue
    return ids


TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
ALLOWED_USER_IDS = _parse_user_ids(os.getenv("ALLOWED_USER_IDS"))
MAX_TARJETAS_PER_REQUEST = int(os.getenv("MAX_TARJETAS_PER_REQUEST", "50"))
REQUEST_TIMEOUT_SECONDS = int(os.getenv("REQUEST_TIMEOUT_SECONDS", "30"))
PROXY_HOST = os.getenv("PROXY_HOST", "geo.iproyal.com").strip()
PROXY_PORT = os.getenv("PROXY_PORT", "11200").strip()
PROXY_USERNAME = os.getenv("PROXY_USERNAME", "fEMMVG3irwJKw9cf").strip()
PROXY_PASSWORD = os.getenv("PROXY_PASSWORD", "mFpxOzaZBswDLOQ9").strip()
PROXY_COUNTRY = os.getenv("PROXY_COUNTRY", "mx").strip()
PROXY_URL = os.getenv("PROXY_URL", "").strip() or (
    f"http://{PROXY_USERNAME}:{PROXY_PASSWORD}_country-{PROXY_COUNTRY}@{PROXY_HOST}:{PROXY_PORT}"
)
WORKER_LIMIT = int(os.getenv("WORKER_LIMIT", "4"))


def is_allowed_user(user_id: int) -> bool:
    return not ALLOWED_USER_IDS or user_id in ALLOWED_USER_IDS
