"""State-scoped synthesis cache. No route may bypass evaluation/session updates.

Exact prompt hashing deliberately sacrifices broad semantic reuse for correctness.
Legacy unscoped rows are never read. Cache outages are misses, not chat failures.
"""
from __future__ import annotations
import asyncio
import hashlib
import json
import logging
import os
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from database import supabase
from config import (DRAFT_LLM_MODEL, DEBATE_LLM_MODEL, DRAFT_LLM_ENDPOINT,
                    DEBATE_LLM_ENDPOINT, LLM_BACKEND_TYPE)

logger = logging.getLogger(__name__)
_encoder = None
_encoder_lock = threading.Lock()


def _encode(text):
    global _encoder
    with _encoder_lock:
        if _encoder is None:
            from sentence_transformers import SentenceTransformer
            _encoder = SentenceTransformer("all-MiniLM-L6-v2")
        return _encoder.encode(text, normalize_embeddings=True).tolist()


async def get_embedding(text: str) -> Optional[list[float]]:
    try:
        return await asyncio.to_thread(_encode, text)
    except Exception:
        logger.warning("Semantic embedding unavailable")
        return None


def _hash(value) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                     separators=(",", ":")).encode()).hexdigest()


def build_cache_namespace(state: dict, prompt: str) -> str | None:
    scope = state.get("cache_scope")
    if not scope or any(not scope.get(k) for k in ("learner_id", "session_id", "concept_id")):
        return None
    prompts = Path(__file__).parents[1] / "multi_agent" / "prompts.py"
    return _hash({
        "schema": 2, "scope": scope,
        "last_question_hash": _hash(state.get("last_question", "")),
        "answer_hash": _hash(state.get("user_answer", "")),
        "scaffold_level": state.get("scaffold_step"),
        "scaffold_success": state.get("is_scaffold_success", False),
        "mastery_mode": state.get("consecutive_high_score_count", 0),
        "previous_weakest_agent": state.get("previous_lowest_agent"),
        "session_context": state.get("session_context", ""),
        "prompt_hash": _hash(prompt),
        "prompt_version": os.getenv("PROMPT_VERSION", hashlib.sha256(prompts.read_bytes()).hexdigest()),
        "model_version": os.getenv("MODEL_VERSION", "unversioned"),
        "models": [LLM_BACKEND_TYPE, DRAFT_LLM_MODEL, DEBATE_LLM_MODEL,
                   DRAFT_LLM_ENDPOINT, DEBATE_LLM_ENDPOINT],
    })


async def get_cached_response(concept: str, user_answer: str, last_question: str = "", *, namespace: str | None = None) -> Optional[str]:
    if not namespace or supabase is None:
        return None
    embedding = await get_embedding(user_answer)
    if embedding is None:
        return None
    try:
        result = await asyncio.to_thread(lambda: supabase.rpc("match_semantic_cache_v2", {
            "p_concept": concept, "p_last_question": last_question,
            "p_namespace": namespace, "p_embedding": embedding,
            "p_match_threshold": 0.98, "p_match_count": 1, "p_record_hit": True,
        }).execute())
        return result.data[0]["cached_response"] if result.data else None
    except Exception:
        logger.warning("Semantic cache lookup unavailable")
        return None


async def save_to_cache(concept: str, user_answer: str, response: str, last_question: str = "", *, namespace: str | None = None) -> None:
    if not namespace or not response or supabase is None:
        return
    embedding = await get_embedding(user_answer)
    if embedding is None:
        return
    try:
        # Namespace includes the exact answer/prompt; conflict is safe and atomic.
        await asyncio.to_thread(lambda: supabase.table("semantic_cache").upsert({
            "namespace": namespace, "concept": concept, "last_question": last_question,
            "user_answer": user_answer, "cached_response": response, "embedding": embedding,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }, on_conflict="namespace").execute())
    except Exception:
        logger.warning("Semantic cache write unavailable")


async def cached_synthesis(prompt: str, state: dict, generate):
    namespace = build_cache_namespace(state, prompt)
    args = (state.get("concept", ""), state.get("user_answer", ""))
    question = state.get("last_question") or ""
    cached = await get_cached_response(*args, question, namespace=namespace)
    if cached is not None:
        return cached
    result = await generate(prompt)
    if result:
        # Cache only structured successful synthesis, never fallback/error text.
        try:
            parsed = json.loads(result)
            valid = isinstance(parsed, dict) and isinstance(parsed.get("message"), str) and bool(parsed["message"])
        except (ValueError, TypeError):
            valid = False
        if valid:
            await save_to_cache(*args, result, question, namespace=namespace)
    return result
