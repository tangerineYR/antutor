import os
from dotenv import load_dotenv

# .env 파일의 환경 변수를 불러옵니다. (override=True로 핫리로드 시 즉각 반영)
load_dotenv(override=False)
# --- Authentication Configuration ---
from security_config import validate_secret, parse_origins
SECRET_KEY = validate_secret(os.getenv("SECRET_KEY"))
ENABLE_BENCHMARK_ENDPOINT = os.getenv("ENABLE_BENCHMARK_ENDPOINT", "false").lower() == "true"
ALLOWED_ORIGINS = parse_origins(os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:3000,http://127.0.0.1:3000,https://antutor.pages.dev",
))
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7 # 1 week expiration

# --- Constants are now managed in DB ---

# Project deployment: vLLM / Qwen3-14B-AWQ. Ollama remains an explicit local option.
LLM_BACKEND_TYPE = os.getenv("LLM_BACKEND_TYPE", "vllm").strip().lower()
if LLM_BACKEND_TYPE not in {"vllm", "ollama"}:
    raise ValueError("LLM_BACKEND_TYPE must be vllm or ollama")


def vllm_base_url(endpoint: str) -> str:
    endpoint = endpoint.rstrip("/")
    return endpoint if endpoint.endswith("/v1") else endpoint + "/v1"


_default_endpoint = ("http://localhost:8000/v1" if LLM_BACKEND_TYPE == "vllm"
                     else "http://localhost:11434/api/chat")
_default_model = "Qwen/Qwen3-14B-AWQ" if LLM_BACKEND_TYPE == "vllm" else "qwen3:8b"
LOCAL_LLM_ENDPOINT = os.getenv("LOCAL_LLM_ENDPOINT", _default_endpoint)
DRAFT_LLM_ENDPOINT = os.getenv("DRAFT_LLM_ENDPOINT", LOCAL_LLM_ENDPOINT)
DEBATE_LLM_ENDPOINT = os.getenv("DEBATE_LLM_ENDPOINT", LOCAL_LLM_ENDPOINT)
if LLM_BACKEND_TYPE == "vllm":
    LOCAL_LLM_ENDPOINT = vllm_base_url(LOCAL_LLM_ENDPOINT)
    DRAFT_LLM_ENDPOINT = vllm_base_url(DRAFT_LLM_ENDPOINT)
    DEBATE_LLM_ENDPOINT = vllm_base_url(DEBATE_LLM_ENDPOINT)
VLLM_API_KEY = os.getenv("VLLM_API_KEY", "")
LOCAL_LLM_MODEL = os.getenv("LOCAL_LLM_MODEL", _default_model)
DRAFT_LLM_MODEL = os.getenv("DRAFT_LLM_MODEL", LOCAL_LLM_MODEL)
DEBATE_LLM_MODEL = os.getenv("DEBATE_LLM_MODEL", LOCAL_LLM_MODEL)
# NEWS_API_KEY = os.getenv("NEWS_API_KEY", "")  # Deprecated: replaced by Tavily Search
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "")
# DEEPL_API_KEY = os.getenv("DEEPL_API_KEY", "")  # Deprecated: replaced by Azure Translator
AZURE_TRANSLATOR_KEY = os.getenv("AZURE_TRANSLATOR_KEY", "")
AZURE_TRANSLATOR_REGION = os.getenv("AZURE_TRANSLATOR_REGION", "koreacentral")
ENABLE_KOREAN_TRANSLATION = os.getenv("ENABLE_KOREAN_TRANSLATION", "true").lower() == "true"

# --- Supabase Database Configuration ---
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

# --- Neo4j Knowledge Graph Configuration ---
NEO4J_URI      = os.getenv("NEO4J_URI", "")
NEO4J_USER     = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "")
NEO4J_DATABASE = os.getenv("NEO4J_DATABASE", "neo4j")

# --- Keyword Detection for Give-Up (Supports English & Korean) ---
GIVE_UP_KEYWORDS = [
    # English
    "don't know", "give up", "not sure", "no idea", "hint", 
    "can't explain", "too hard", "stuck", "confused", "help me", "idk",
    # Korean
    "모르겠", "잘 몰라", "힌트", "모름", "알려줘",
    "설명 못하", "몰라"
]


# Private learner/model traces are opt-in and must never be committed.
ENABLE_PRIVATE_DEBUG_LOGS = os.getenv("ENABLE_PRIVATE_DEBUG_LOGS", "false").lower() == "true"
PRIVATE_LOG_DIR = os.getenv("PRIVATE_LOG_DIR", os.path.join(os.path.dirname(os.path.dirname(__file__)), "runtime-logs"))
