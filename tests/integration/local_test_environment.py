"""Require an explicit opt-in before writing disposable integration fixtures."""
import os
from urllib.parse import urlparse


def require_disposable_environment(environment=None):
    environment = os.environ if environment is None else environment
    if environment.get("ANTUTOR_DISPOSABLE_TESTS") != "1":
        raise RuntimeError("Set ANTUTOR_DISPOSABLE_TESTS=1 only for a disposable test stack")
    api_url = environment.get("TEST_API_URL", "http://127.0.0.1:8082")
    database_url = environment.get("SUPABASE_URL", "")
    for url in (api_url, database_url):
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"} or parsed.hostname not in {
            "localhost", "127.0.0.1", "::1"
        }:
            raise RuntimeError("Integration tests require loopback-only HTTP endpoints")
    return api_url, database_url
