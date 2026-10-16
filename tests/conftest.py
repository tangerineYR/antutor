import os
import secrets

# Per-process test key, never a deployment fallback.
os.environ["SECRET_KEY"] = secrets.token_urlsafe(48)
os.environ["SUPABASE_URL"] = ""
os.environ["SUPABASE_KEY"] = ""
