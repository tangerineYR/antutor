import sys
if sys.platform != "win32":
    try:
        import uvloop
        uvloop.install()
    except ImportError:
        pass

from contextlib import asynccontextmanager
import asyncio
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from config import ALLOWED_ORIGINS

# Import standard routers
from routers import users, dictionary, chat, sandbox, benchmark, attendance, quiz

@asynccontextmanager
async def lifespan(app: FastAPI):
    # ⚠️ Render 무료 플랜(512MB) 메모리 절약을 위해 warm-up 비활성화
    # 임베딩 모델은 첫 요청 시 lazy 로딩됩니다.
    # (로컬 개발 시 warm-up을 원하면 아래 주석을 풀어 사용하세요)
    # async def _warmup():
    #     try:
    #         from services.semantic_cache import get_embedding
    #         await get_embedding("warmup")
    #         print("🚀 [Startup] Embedding model warm-up complete.", flush=True)
    #     except Exception as e:
    #         print(f"⚠️ [Startup] Embedding warm-up failed (non-critical): {e}", flush=True)
    # asyncio.create_task(_warmup())
    print("✅ [Startup] Server started (embedding lazy-load mode).", flush=True)
    yield

app = FastAPI(
    title="Antutor Metric AI Backend",
    description="Sejong University Capstone Backend",
    lifespan=lifespan
)

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    # Pydantic errors include input/ctx (including passwords); allowlist safe fields.
    errors = [{"loc": error["loc"], "type": error["type"],
               "msg": "Invalid value" if error["type"] == "value_error" else error["msg"]}
              for error in exc.errors()]
    return JSONResponse(status_code=422, content={"detail": errors})



app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------
# Application API Endpoints (Routers)
# ---------------------------------------------------------
from database import supabase

app.include_router(users.router)
app.include_router(dictionary.router)
app.include_router(chat.router)
app.include_router(sandbox.router)
app.include_router(benchmark.router)
app.include_router(attendance.router)
app.include_router(quiz.router)

@app.get("/debug-concepts")
def debug_concepts():
    return supabase.table("concepts").select("name").execute().data

@app.get("/")
@app.head("/")
def health_check():
    return {"status": "ok", "message": "Server is running."}
