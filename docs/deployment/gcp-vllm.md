# GCP L4 and vLLM

The default inference configuration is **vLLM + `Qwen/Qwen3-14B-AWQ`**.
Ollama remains an explicit local option. The Python backend is an inference
client; installing its dependencies does not install or start a GPU model server.

## Historical deployment

The repository preserves a [normalized historical configuration](gcp-vllm-historical.json):
GCP Compute Engine `g2-standard-4`, NVIDIA L4 with 24 GB VRAM, Ubuntu 22.04,
and vLLM serving `Qwen/Qwen3-14B-AWQ`. The record contains the server options and
matching LOCAL/DRAFT/DEBATE model settings, without credentials or server addresses.

The earlier 8B stage and the later 14B configuration are distinct. The
[Colab notebook](../experiments/vllm_qwen3_colab.ipynb) is an 8B prototype, not a
14B deployment manifest. The historical server image was `latest`; its digest and
model revision are unknown. The [provenance](../evaluation/data-provenance.md)
describes what the normalized record can and cannot establish.

## Backend configuration

Use [`.env.example`](../../.env.example) as the configuration reference.
Configure LOCAL as well as DRAFT/DEBATE: individual agents, hint generation and
the prompt sandbox also use LOCAL settings.

```ini
LLM_BACKEND_TYPE=vllm
LOCAL_LLM_ENDPOINT=http://localhost:8000/v1
DRAFT_LLM_ENDPOINT=http://localhost:8000/v1
DEBATE_LLM_ENDPOINT=http://localhost:8000/v1
LOCAL_LLM_MODEL=Qwen/Qwen3-14B-AWQ
DRAFT_LLM_MODEL=Qwen/Qwen3-14B-AWQ
DEBATE_LLM_MODEL=Qwen/Qwen3-14B-AWQ
VLLM_API_KEY=
```

`localhost:8000` refers to a local GPU server or an SSH tunnel to the GPU host.
For a hosted service, use its authenticated HTTPS endpoint and supply its current
API key through private environment configuration.

Omitted DRAFT/DEBATE endpoints inherit LOCAL; omitted DRAFT/DEBATE models inherit
LOCAL's model. Explicit values take precedence. vLLM endpoint suffixes `/` and
`/v1/` are normalized. Unknown backend names fail at startup.

## GPU server

The server requires an appropriate GPU, NVIDIA drivers, Docker and the NVIDIA
Container Toolkit. This example retains the historical model and key options,
with a loopback-only port. Select an image tag or digest validated for the GPU
and model; the historical `latest` reference is not a reproducible version pin.

```sh
: "${VLLM_IMAGE:?Set a validated vLLM image tag or digest}"
docker run --gpus all -d --name antutor-vllm \
  -p 127.0.0.1:8000:8000 --ipc=host \
  -v "$HOME/.cache/huggingface:/root/.cache/huggingface" \
  "$VLLM_IMAGE" \
  --model Qwen/Qwen3-14B-AWQ \
  --quantization awq \
  --gpu-memory-utilization 0.95 \
  --max-model-len 4096 \
  --enable-prefix-caching
```

This command is for local or tunneled development. Public hosting requires TLS
and authentication. Memory use depends on the vLLM version, other GPU workloads
and concurrency; the historical 0.95/4096 settings need validation on the target.

Check the model identifier at `/v1/models`, then send a representative request to
`/v1/chat/completions` and verify its response. An open port does not establish
model readiness. Configuration and mocked protocol tests do not measure GPU
compatibility, generation quality, memory use or inference latency.

## Optional Ollama configuration

When switching an existing environment, replace all explicit model and endpoint
values together:

```ini
LLM_BACKEND_TYPE=ollama
LOCAL_LLM_ENDPOINT=http://localhost:11434/api/chat
DRAFT_LLM_ENDPOINT=http://localhost:11434/api/chat
DEBATE_LLM_ENDPOINT=http://localhost:11434/api/chat
LOCAL_LLM_MODEL=qwen3:8b
DRAFT_LLM_MODEL=qwen3:8b
DEBATE_LLM_MODEL=qwen3:8b
```

Install Ollama and obtain `qwen3:8b` separately. With no explicit endpoint/model
variables, `LLM_BACKEND_TYPE=ollama` selects these defaults automatically.
Changing only the backend does not override previously configured vLLM values.
