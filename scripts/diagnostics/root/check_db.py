# Manual tool: may contact real services; not part of the automated test suite.
import os as _os
import sys as _sys
from pathlib import Path as _Path
_REPO = next(p for p in _Path(__file__).resolve().parents if (p / "back").is_dir())
_sys.path[:0] = [str(_REPO), str(_REPO / "back")]
_os.chdir(_REPO)

import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), 'back'))

from database import supabase

res = supabase.table("semantic_cache").select("*").execute()
print("semantic_cache rows count:", len(res.data))
for row in res.data:
    print(f"ID: {row.get('id')}, Concept: {row.get('concept')}, User Answer: '{row.get('user_answer')[:60]}'")
