# Manual tool: may contact real services; not part of the automated test suite.
import os as _os
import sys as _sys
from pathlib import Path as _Path
_REPO = next(p for p in _Path(__file__).resolve().parents if (p / "back").is_dir())
_sys.path[:0] = [str(_REPO), str(_REPO / "back")]
_os.chdir(_REPO)

import os
import json
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
supabase = create_client(url, key)

res = supabase.table("sessions").select("*").limit(1).execute()
if res.data:
    print(list(res.data[0].keys()))
else:
    print("No sessions found")
