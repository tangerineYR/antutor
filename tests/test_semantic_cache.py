from copy import deepcopy
from unittest.mock import AsyncMock, MagicMock
import pytest
from services import semantic_cache as cache


def state():
    return {'cache_scope': {'learner_id': 'a', 'session_id': '1', 'concept_id': '2',
                            'session': {'idk_count': 0}, 'language': 'ko'},
            'concept': 'inflation', 'user_answer': 'Prices rise', 'last_question': 'Why?',
            'session_context': 'previous turn', 'consecutive_high_score_count': 1}

@pytest.mark.parametrize('field,value', [('scaffold_step','Nudge'), ('consecutive_high_score_count',2),
    ('previous_lowest_agent','Market'), ('session_context','different'), ('last_question','How?'),
    ('user_answer','Prices do not rise')])
def test_state_separation(field, value):
    a=state(); b=deepcopy(a); b[field]=value
    assert cache.build_cache_namespace(a,'prompt') != cache.build_cache_namespace(b,'prompt')

@pytest.mark.parametrize('field', ['learner_id','session_id','concept_id','language'])
def test_scope_separation(field):
    a=state(); b=deepcopy(a); b['cache_scope'][field]='other'
    assert cache.build_cache_namespace(a,'prompt') != cache.build_cache_namespace(b,'prompt')

def test_prompt_and_model_versions(monkeypatch):
    a=state(); key=cache.build_cache_namespace(a,'prompt')
    assert key != cache.build_cache_namespace(a,'changed prompt')
    monkeypatch.setenv('MODEL_VERSION','revision-2')
    assert key != cache.build_cache_namespace(a,'prompt')
    key=cache.build_cache_namespace(a,'prompt')
    monkeypatch.setenv('PROMPT_VERSION','revision-2')
    assert key != cache.build_cache_namespace(a,'prompt')

async def test_missing_scope_never_reads_legacy_cache(monkeypatch):
    db=MagicMock(); monkeypatch.setattr(cache,'supabase',db)
    assert await cache.get_cached_response('inflation','answer') is None
    await cache.save_to_cache('inflation','answer','response')
    db.rpc.assert_not_called(); db.table.assert_not_called()

async def test_scoped_hit_increments_and_avoids_only_synthesis(monkeypatch):
    db=MagicMock(); db.rpc.return_value.execute.return_value.data=[{'cached_response':'{"message":"cached"}'}]
    monkeypatch.setattr(cache,'supabase',db)
    monkeypatch.setattr(cache,'get_embedding',AsyncMock(return_value=[0.1]*384))
    generate=AsyncMock()
    assert await cache.cached_synthesis('prompt',state(),generate) == '{"message":"cached"}'
    generate.assert_not_called()
    args=db.rpc.call_args.args
    assert args[0]=='match_semantic_cache_v2' and args[1]['p_record_hit'] is True
    assert args[1]['p_namespace']

async def test_cache_outage_runs_generation(monkeypatch):
    db=MagicMock(); db.rpc.return_value.execute.side_effect=RuntimeError('offline')
    monkeypatch.setattr(cache,'supabase',db)
    monkeypatch.setattr(cache,'get_embedding',AsyncMock(return_value=[0.1]*384))
    generate=AsyncMock(return_value='{"message":"fresh","mode":"normal"}')
    assert 'fresh' in await cache.cached_synthesis('prompt',state(),generate)
    generate.assert_awaited_once()
    db.table.return_value.upsert.assert_called_once()
