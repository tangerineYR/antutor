# Manual tool: may contact real services; not part of the automated test suite.
import os as _os
import sys as _sys
from pathlib import Path as _Path
_REPO = next(p for p in _Path(__file__).resolve().parents if (p / "back").is_dir())
_sys.path[:0] = [str(_REPO), str(_REPO / "back")]
_os.chdir(_REPO)

import requests
import json
import uuid

payload = {
    "session_id": str(uuid.uuid4()),
    "user_id": str(uuid.uuid4()),
    "concept": "인플레이션",
    "is_pre_test": False,
    "answers": [
        {
            "question_id": 1,
            "selected_choice": 1,
            "confidence_level": 1
        }
    ]
}

try:
    res = requests.post("http://localhost:8080/quiz/submit", json=payload)
    print("Status Code:", res.status_code)
    print("Response JSON:", res.json())
except Exception as e:
    print("Error:", e)
