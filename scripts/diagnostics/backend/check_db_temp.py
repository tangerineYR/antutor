# Manual tool: may contact real services; not part of the automated test suite.
import os as _os
import sys as _sys
from pathlib import Path as _Path
_REPO = next(p for p in _Path(__file__).resolve().parents if (p / "back").is_dir())
_sys.path[:0] = [str(_REPO), str(_REPO / "back")]
_os.chdir(_REPO)

import os
import sys

from dotenv import load_dotenv
load_dotenv(str(_REPO / ".env"))

from supabase import create_client, Client
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

try:
    res = supabase.table("chat_logs").select("news_urls").limit(1).execute()
    print("Column 'news_urls' exists!")
except Exception as e:
    print("Error:", e)
