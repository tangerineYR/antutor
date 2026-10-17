# Manual tool: may contact real services; not part of the automated test suite.
import os as _os
import sys as _sys
from pathlib import Path as _Path
_REPO = next(p for p in _Path(__file__).resolve().parents if (p / "back").is_dir())
_sys.path[:0] = [str(_REPO), str(_REPO / "back")]
_os.chdir(_REPO)

from back.database import supabase

print("Questions:")
res = supabase.table("questions").select("*").limit(1).execute()
print(res.data)

print("Quiz Attempts:")
res = supabase.table("quiz_attempts").select("*").limit(1).execute()
print(res.data)

print("Quiz Answers:")
res = supabase.table("quiz_answers").select("*").limit(1).execute()
print(res.data)

print("Sessions:")
res = supabase.table("sessions").select("session_id, hakes_gain").limit(1).execute()
print(res.data)
