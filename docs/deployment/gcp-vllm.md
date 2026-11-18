# GCP L4 and vLLM

기본 추론 설정은 **vLLM + `Qwen/Qwen3-14B-AWQ`**입니다. Ollama는 명시적으로 선택할 수 있는 로컬 대안입니다. Python 백엔드는 추론 클라이언트이므로 백엔드 의존성을 설치하는 것만으로 GPU 모델 서버가 설치되거나 실행되지는 않습니다.

## Historical Deployment

저장소에는 [정규화한 과거 배포 설정](gcp-vllm-historical.json)이 보존되어 있습니다. GCP Compute Engine `g2-standard-4`, NVIDIA L4 24GB VRAM, Ubuntu 22.04에서 vLLM으로 `Qwen/Qwen3-14B-AWQ`를 서빙한 구성입니다. 서버 옵션과 이에 대응하는 LOCAL/DRAFT/DEBATE 모델 설정을 포함하며 자격증명과 서버 주소는 제외했습니다.

초기 8B 단계와 이후 14B 구성은 구분합니다. [Colab 노트북](../experiments/vllm_qwen3_colab.ipynb)은 8B 프로토타입이며 14B 배포 명세가 아닙니다. 당시 서버 이미지는 `latest`였고 이미지 digest와 모델 revision은 알려져 있지 않습니다. 정규화한 기록으로 확인할 수 있는 범위와 한계는 [출처 문서](../evaluation/data-provenance.md)에 설명되어 있습니다.

## Backend Configuration

설정 항목은 [`.env.example`](../../.env.example)을 참고합니다. DRAFT/DEBATE뿐 아니라 LOCAL도 설정해야 합니다. 개별 Agent, 힌트 생성, 프롬프트 sandbox에서도 LOCAL 설정을 사용합니다.

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

`localhost:8000`은 로컬 GPU 서버 또는 GPU 호스트로 연결한 SSH 터널을 뜻합니다. 원격 서비스에는 인증된 HTTPS endpoint를 사용하고 실제 API 키는 비공개 환경 설정으로 전달합니다.

DRAFT/DEBATE endpoint를 생략하면 LOCAL endpoint를, 모델을 생략하면 LOCAL 모델을 상속합니다. 명시한 값이 우선합니다. vLLM endpoint의 `/`, `/v1/` 접미사는 정규화하며 알려지지 않은 backend 이름은 시작 시 거부합니다.

## GPU Server

서버에는 적절한 GPU, NVIDIA 드라이버, Docker, NVIDIA Container Toolkit이 필요합니다. 다음은 과거 모델과 주요 옵션을 유지하면서 포트를 loopback으로 제한한 **GPU 서버의 Bash 실행 예시**입니다. 대상 GPU와 모델에서 검증한 이미지 태그 또는 digest를 선택해야 합니다. 과거의 `latest` 참조는 재현 가능한 버전 고정값이 아닙니다.

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

이 명령은 로컬 또는 터널을 통한 개발용입니다. 외부 공개 서비스에는 TLS와 인증이 필요합니다. 메모리 사용량은 vLLM 버전·다른 GPU 작업·동시 요청 수에 따라 달라지므로 과거의 0.95/4096 설정도 대상 환경에서 검증해야 합니다.

`/v1/models`에서 모델 식별자를 확인한 뒤 `/v1/chat/completions`에 대표 요청을 보내 응답을 검증합니다. 포트가 열려 있다는 사실만으로 모델 준비가 확인되지는 않습니다. 설정 검사와 mock 기반 프로토콜 테스트는 GPU 호환성, 생성 품질, 메모리 사용량, 추론 지연을 측정하지 않습니다.

## Optional Ollama Configuration

기존 환경에서 전환할 때는 명시적으로 설정된 모든 모델명과 endpoint를 함께 바꿉니다.

```ini
LLM_BACKEND_TYPE=ollama
LOCAL_LLM_ENDPOINT=http://localhost:11434/api/chat
DRAFT_LLM_ENDPOINT=http://localhost:11434/api/chat
DEBATE_LLM_ENDPOINT=http://localhost:11434/api/chat
LOCAL_LLM_MODEL=qwen3:8b
DRAFT_LLM_MODEL=qwen3:8b
DEBATE_LLM_MODEL=qwen3:8b
```

Ollama 설치와 `qwen3:8b` 다운로드는 별도로 수행합니다. endpoint·모델 환경변수가 없으면 `LLM_BACKEND_TYPE=ollama`가 위 기본값을 선택합니다. backend 종류만 바꾸어도 기존에 명시한 vLLM 값이 자동으로 덮어써지는 것은 아닙니다.
