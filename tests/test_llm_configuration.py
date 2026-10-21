"""Provider defaults and request contracts; no live GPU/LLM calls."""
import json
import os
from pathlib import Path
import subprocess
import sys

import httpx
import pytest

ROOT = Path(__file__).resolve().parents[1]


def load_settings(overrides):
    env = {k: v for k, v in os.environ.items()
           if not (k.startswith(('LOCAL_LLM_', 'DRAFT_LLM_', 'DEBATE_LLM_', 'VLLM_'))
                   or k == 'LLM_BACKEND_TYPE')}
    env.update(PYTHON_DOTENV_DISABLED='1', PYTHONPATH=str(ROOT / 'back'))
    env.update(overrides)
    return subprocess.run([sys.executable, '-c', '''
import json, config
from multi_agent.llm_config import draft_llm, debate_llm, synthesis_llm
keys = ['LLM_BACKEND_TYPE', 'LOCAL_LLM_MODEL', 'DRAFT_LLM_MODEL', 'DEBATE_LLM_MODEL',
        'LOCAL_LLM_ENDPOINT', 'DRAFT_LLM_ENDPOINT', 'DEBATE_LLM_ENDPOINT']
result = {k: getattr(config,k) for k in keys}
result['clients'] = [type(x.bound).__name__ for x in (draft_llm,debate_llm,synthesis_llm)]
result['models'] = [getattr(x.bound,'model_name',None) or x.bound.model for x in (draft_llm,debate_llm,synthesis_llm)]
print(json.dumps(result))
'''], cwd=ROOT, env=env, capture_output=True, text=True)


@pytest.mark.parametrize('backend,model,endpoint,client', [
    (None, 'Qwen/Qwen3-14B-AWQ', 'http://localhost:8000/v1', 'ChatOpenAI'),
    ('ollama', 'qwen3:8b', 'http://localhost:11434/api/chat', 'ChatOllama'),
])
def test_defaults_construct_matching_graph_clients(backend, model, endpoint, client):
    result = load_settings({'LLM_BACKEND_TYPE': backend} if backend else {})
    assert result.returncode == 0, result.stderr
    settings = json.loads(result.stdout)
    for prefix in ('LOCAL', 'DRAFT', 'DEBATE'):
        assert settings[f'{prefix}_LLM_MODEL'] == model
        assert settings[f'{prefix}_LLM_ENDPOINT'] == endpoint
    assert settings['clients'] == [client] * 3
    assert settings['models'] == [model] * 3


def test_custom_models_endpoints_and_trailing_slashes():
    result = load_settings({'LOCAL_LLM_MODEL': 'shared-model', 'DRAFT_LLM_MODEL': 'draft-model',
                            'LOCAL_LLM_ENDPOINT': 'http://localhost:9000/v1/',
                            'DRAFT_LLM_ENDPOINT': 'http://localhost:9001/',
                            'DEBATE_LLM_ENDPOINT': 'http://localhost:9002/v1'})
    assert result.returncode == 0, result.stderr
    settings = json.loads(result.stdout)
    assert settings['models'] == ['draft-model', 'shared-model', 'shared-model']
    assert [settings[f'{p}_LLM_ENDPOINT'] for p in ('LOCAL','DRAFT','DEBATE')] == [
        'http://localhost:9000/v1', 'http://localhost:9001/v1', 'http://localhost:9002/v1']


def test_invalid_provider_does_not_silently_use_ollama():
    result = load_settings({'LLM_BACKEND_TYPE': 'vlmm'})
    assert result.returncode != 0
    assert 'LLM_BACKEND_TYPE must be vllm or ollama' in result.stderr


@pytest.mark.parametrize('backend', ['vllm', 'ollama'])
@pytest.mark.parametrize('route', ['helper', 'sandbox'])
async def test_json_request_protocol(monkeypatch, backend, route):
    from services import llm_agent
    from routers import sandbox
    from schemas import PromptTuningSandboxRequest
    module = llm_agent if route == 'helper' else sandbox
    endpoint = 'http://localhost:8000/v1/' if backend == 'vllm' else 'http://localhost:11434/api/chat'
    monkeypatch.setattr(module, 'LLM_BACKEND_TYPE', backend)
    monkeypatch.setattr(module, 'LOCAL_LLM_ENDPOINT', endpoint)
    monkeypatch.setattr(module, 'LOCAL_LLM_MODEL', 'test-model')
    monkeypatch.setattr(module, 'VLLM_API_KEY', 'test-only-key')
    requests = []

    def respond(request):
        requests.append(request)
        body = {'choices': [{'message': {'content': '{"ok":true}'}}]} if backend == 'vllm' else {
            'message': {'content': '{"ok":true}'}}
        return httpx.Response(200, json=body)

    client = httpx.AsyncClient(transport=httpx.MockTransport(respond))
    monkeypatch.setattr(module.httpx, 'AsyncClient', lambda: client)
    if route == 'helper':
        response = await llm_agent.call_local_llm('hello', is_json=True, temperature=0.2)
        assert json.loads(response) == {'ok': True}
    else:
        response = await sandbox.ai_test_sandbox(PromptTuningSandboxRequest(
            system_prompt='system', user_prompt='hello', is_json=True, temperature=0.2), current_user='test')
        assert response['status'] == 'success'
        assert json.loads(response['response']) == {'ok': True}
    assert len(requests) == 1
    request = requests[0]
    payload = json.loads(request.content)
    assert payload['model'] == 'test-model'
    assert payload['messages'][-1] == {'role': 'user', 'content': 'hello'}
    if route == 'sandbox':
        assert payload['messages'][0] == {'role': 'system', 'content': 'system'}
    if backend == 'vllm':
        assert str(request.url) == 'http://localhost:8000/v1/chat/completions'
        assert request.headers['Authorization'] == 'Bearer test-only-key'
        assert payload['response_format'] == {'type': 'json_object'}
        assert payload['temperature'] == 0.2
        assert 'options' not in payload and 'format' not in payload
    else:
        assert str(request.url) == endpoint
        assert payload['options']['temperature'] == 0.2
        assert payload['format'] == 'json'
        assert 'Authorization' not in request.headers
