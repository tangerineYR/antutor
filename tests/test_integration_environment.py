"""The CI fixture runner must fail before writing to non-local endpoints."""
import importlib.util
from pathlib import Path

import pytest


path = Path(__file__).parent / "integration" / "local_test_environment.py"
spec = importlib.util.spec_from_file_location("local_test_environment", path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def environment():
    return {"ANTUTOR_DISPOSABLE_TESTS": "1", "TEST_API_URL": "http://127.0.0.1:8082",
            "SUPABASE_URL": "http://localhost:54321"}


def test_disposable_loopback_endpoints_are_accepted():
    assert module.require_disposable_environment(environment()) == (
        "http://127.0.0.1:8082", "http://localhost:54321"
    )


@pytest.mark.parametrize("flag", [None, "", "0", "true"])
def test_explicit_opt_in_is_required(flag):
    values = environment()
    values["ANTUTOR_DISPOSABLE_TESTS"] = flag
    with pytest.raises(RuntimeError, match="ANTUTOR_DISPOSABLE_TESTS"):
        module.require_disposable_environment(values)


@pytest.mark.parametrize("key", ["TEST_API_URL", "SUPABASE_URL"])
@pytest.mark.parametrize("url", ["https://example.supabase.co", "http://localhost.example.com",
                                "file:///tmp/test", ""])
def test_remote_or_invalid_endpoint_is_rejected(key, url):
    values = environment()
    values[key] = url
    with pytest.raises(RuntimeError, match="loopback"):
        module.require_disposable_environment(values)
