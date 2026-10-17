# Manual tool: may contact real services; not part of the automated test suite.
import os as _os
import sys as _sys
from pathlib import Path as _Path
_REPO = next(p for p in _Path(__file__).resolve().parents if (p / "back").is_dir())
_sys.path[:0] = [str(_REPO), str(_REPO / "back")]
_os.chdir(_REPO)

import os
import sys

# Add back directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'back'))

from back.database import supabase

# fetch 1 row from concepts
res = supabase.table("concepts").select("*").limit(1).execute()
print("Concepts data:", res.data)
