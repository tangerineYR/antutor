"""Validation shared by startup and tests; never includes secret values in errors."""
import math
from collections import Counter
from urllib.parse import urlsplit


def validate_secret(value: str | None) -> str:
    if not value or len(value.encode("utf-8")) < 32:
        raise ValueError("SECRET_KEY must contain at least 32 bytes of random data")
    lowered = value.lower()
    if any(word in lowered for word in ("your-", "your_", "changeme", "change-me", "placeholder", "capstone-2026", "example", "secret_key")):
        raise ValueError("SECRET_KEY must not be a placeholder")
    counts = Counter(value)
    entropy = -sum((n / len(value)) * math.log2(n / len(value)) for n in counts.values())
    if len(counts) < 12 or entropy < 3.5:
        raise ValueError("SECRET_KEY lacks sufficient character diversity; generate a random key")
    return value


def parse_origins(value: str) -> list[str]:
    origins = list(dict.fromkeys(item.strip() for item in value.split(",") if item.strip()))
    for origin in origins:
        parsed = urlsplit(origin)
        if (parsed.scheme not in {"http", "https"} or not parsed.hostname
                or parsed.username or parsed.password or parsed.path or parsed.query
                or parsed.fragment or "*" in origin):
            raise ValueError("ALLOWED_ORIGINS must contain exact HTTP(S) origins without paths or wildcards")
    return origins
