# Manual tool: may contact real services; not part of the automated test suite.
import os as _os
import sys as _sys
from pathlib import Path as _Path
_REPO = next(p for p in _Path(__file__).resolve().parents if (p / "back").is_dir())
_sys.path[:0] = [str(_REPO), str(_REPO / "back")]
_os.chdir(_REPO)

import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from database import supabase

try:
    res = supabase.table("questions").select("*").limit(1).execute()
    print("Columns:", res.data[0].keys() if res.data else "No data")
except Exception as e:
    print("Error:", e)
