# GCP L4 and vLLM

Antutor의 기본 추론 설정은 vLLM의 OpenAI 호환 API와 `Qwen/Qwen3-14B-AWQ`입니다. FastAPI는 모델 서버에 요청을 보내므로 백엔드 설치와 모델 서빙은 별도 단계입니다.

## vLLM Configuration

동일한 모델 서버를 사용할 때는 LOCAL 값만 지정합니다. DRAFT와 DEBATE의 주소·모델을 생략하면 각각 LOCAL 값을 사용합니다. 서버나 모델을 분리할 때는 필요한 항목을 추가합니다. [전체 환경변수 예시](../../.env.example)

~~~ini
LLM_BACKEND_TYPE=vllm
LOCAL_LLM_ENDPOINT=http://localhost:8000/v1
LOCAL_LLM_MODEL=Qwen/Qwen3-14B-AWQ
VLLM_API_KEY=
~~~

| 호출 | 주소와 모델 설정 |
| --- | --- |
| 개별 에이전트 호출, 힌트와 프롬프트 실험 | `LOCAL_LLM_ENDPOINT`, `LOCAL_LLM_MODEL` |
| LangGraph 초안 평가 | `DRAFT_LLM_ENDPOINT`, `DRAFT_LLM_MODEL` |
| LangGraph 교차 검토와 최종 합성 | `DEBATE_LLM_ENDPOINT`, `DEBATE_LLM_MODEL` |

이 예시는 백엔드와 GPU 서버가 같은 호스트에 있거나 로컬 포트를 GPU 호스트로 포워딩한 경우에 사용합니다. 인증을 설정한 모델 서버에는 `VLLM_API_KEY`를 비공개 환경변수로 전달합니다. 원격 서비스에는 인증과 HTTPS를 사용합니다.

## GPU Server

GPU 호스트에 NVIDIA 드라이버, Docker와 NVIDIA Container Toolkit을 준비합니다. 다음 예시는 당시 모델과 주요 옵션을 사용하며 호스트의 `127.0.0.1:8000`에 포트를 공개합니다. `VLLM_IMAGE`에는 대상 GPU에서 검증한 이미지 태그나 digest를 지정합니다.

~~~sh
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
~~~

`/v1/models`에서 모델 식별자를 확인하고 `/v1/chat/completions`에서 대표 질문의 응답을 확인합니다. 메모리 옵션과 문맥 길이는 vLLM 버전, GPU 가용 메모리, 동시 요청 수에 맞춰 확인합니다.

## Ollama Configuration

Ollama를 설치하고 `qwen3:8b`를 내려받은 뒤 다음 값을 사용합니다. 다른 모델을 사용하려면 각 단계에 설정한 식별자가 로컬 서버에 설치되어 있어야 합니다.

~~~ini
LLM_BACKEND_TYPE=ollama
LOCAL_LLM_ENDPOINT=http://localhost:11434/api/chat
LOCAL_LLM_MODEL=qwen3:8b
DRAFT_LLM_MODEL=qwen3:8b
DEBATE_LLM_MODEL=qwen3:8b
~~~

Ollama에서 LangGraph의 초안·교차 검토·합성은 모두 `LOCAL_LLM_ENDPOINT`에서 파생한 호스트 주소를 사용합니다. `DRAFT_LLM_MODEL`과 `DEBATE_LLM_MODEL`은 단계별 모델을 선택합니다. 기존 vLLM 설정을 재사용하는 경우 명시된 LOCAL 주소와 모델, DRAFT·DEBATE 모델을 Ollama용으로 바꿉니다. [클라이언트 설정](../../back/multi_agent/llm_config.py)

## Historical Deployment

[과거 배포 설정](gcp-vllm-historical.json)은 GCP Compute Engine `g2-standard-4`, NVIDIA L4 24GB, Ubuntu 22.04와 vLLM의 `Qwen/Qwen3-14B-AWQ` 설정을 담고 있습니다. [Colab 노트북](../experiments/vllm_qwen3_colab.ipynb)은 초기 8B 프로토타입에 해당합니다. 당시 서버 기록에는 `latest` 이미지가 남아 있으며 정확한 이미지 digest와 모델 revision은 확인할 수 없습니다. [배포 기록의 출처와 범위](../evaluation/data-provenance.md#historical-gpu-configuration)