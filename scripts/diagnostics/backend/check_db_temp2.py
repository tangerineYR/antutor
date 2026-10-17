# Manual tool: may contact real services; not part of the automated test suite.
import os as _os
import sys as _sys
from pathlib import Path as _Path
_REPO = next(p for p in _Path(__file__).resolve().parents if (p / "back").is_dir())
_sys.path[:0] = [str(_REPO), str(_REPO / "back")]
_os.chdir(_REPO)

import os
import asyncio
from supabase import create_client

SUPABASE_URL = os.getenv("SUPABASE_URL", "https://zpxofmslksixgcvdskzz.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "your-key")
# Assuming key is available in .env
from dotenv import load_dotenv
load_dotenv()

supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

res = supabase.table("chat_logs").select("news_urls, ai_response, turn_number").order("created_at", desc=True).limit(5).execute()
for r in res.data:
    print(f"Turn {r['turn_number']}: news_urls={r['news_urls']}")
