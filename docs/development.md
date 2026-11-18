# Development and Verification

실행 가능한 백엔드는 FastAPI·LangGraph와 Supabase를 사용합니다. 기본 추론 설정은 vLLM/OpenAI 호환 API와 `Qwen/Qwen3-14B-AWQ`이며, Ollama·Neo4j·Tavily·Azure Translator는 구성에 따라 사용합니다. 추론 서버 연결과 Ollama 선택은 [GCP/vLLM 설정](deployment/gcp-vllm.md)을 참고하세요. 단위 테스트와 비-LLM API 통합 검사에는 실제 모델 서버가 필요하지 않습니다.

## Development Environment

CI는 Python 3.12와 Node 22를 사용합니다. 다음 명령은 저장소 루트에서 실행하는 일반 로컬 설치 예시입니다.

**Windows PowerShell**

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install torch --index-url https://download.pytorch.org/whl/cpu
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pip check
```

**Linux / macOS**

```sh
python3 -m venv .venv
.venv/bin/python -m pip install torch --index-url https://download.pytorch.org/whl/cpu
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/python -m pip check
```

Linux CI는 CPU용 `torch==2.14.1+cpu`를 명시적으로 설치합니다. CI 재현에 필요한 의존성 버전과 명령은 [워크플로](../.github/workflows/ci.yml)를 참고하세요. GPU 모델 서버는 별도로 설치하고 실행합니다.

로컬 DB와 비밀값은 아래 Database 절에서 준비합니다. 준비가 끝난 뒤 저장소 루트에서 백엔드를 시작합니다.

```powershell
# Windows PowerShell
cd back
..\.venv\Scripts\python.exe -m uvicorn main:app --port 8080
```

```sh
# Linux / macOS
cd back
../.venv/bin/python -m uvicorn main:app --port 8080
```

프론트는 별도 터미널의 저장소 루트에서 실행합니다.

```sh
cd front
npm ci
npm test -- --watchAll=false --runInBand
npm run build
npm start
```

백엔드 8080 포트는 프론트 개발 환경의 API 주소와 맞춰져 있습니다. 운영 API 주소는 `front/.env.production`을 참고해 배포 환경에 맞게 설정합니다.

## Authentication and Security

`SECRET_KEY`는 import·서버 시작 시 필요하며 최소 32 UTF-8 바이트여야 합니다. 알려진 예시 값, 반복 문자, 문자 다양성이 낮은 값은 거부합니다. 이 검사가 키의 엔트로피를 보장하지는 않으므로 암호학적 난수 생성기를 사용해야 합니다. 기존 환경변수가 `.env`보다 우선합니다. 실제 키를 추적되는 예시 파일이나 CI 설정에 넣지 않습니다.

신규 가입 암호는 Unicode·공백·문장부호를 허용하며 8–72자여야 합니다. bcrypt 제한에 따라 UTF-8 인코딩 결과도 72바이트 이하여야 합니다. 강화된 정책은 가입에 적용하며 기존 계정의 로그인 검증 방식은 유지합니다.

`ALLOWED_ORIGINS`는 쉼표로 구분한 정확한 origin 목록입니다. 경로나 와일드카드를 넣지 않습니다. 기본값에는 localhost/127.0.0.1의 3000 포트와 `https://antutor.pages.dev`가 포함되며, 실제 배포 origin을 명시적으로 설정해야 합니다. WebSocket은 네이티브 클라이언트도 허용된 Origin이 필요하고, 첫 메시지의 JWT와 세션 소유권을 확인합니다.

`ENABLE_BENCHMARK_ENDPOINT`의 기본값은 `false`이며 이때 해당 API는 404를 반환합니다. 활성화해도 백엔드 사용자 인증이 필요합니다. 통제된 개발 환경에서만 활성화합니다.

유효성 검사 응답에는 필드 위치·유형·메시지를 포함하고 Pydantic의 입력값이나 context는 포함하지 않습니다. Guardrail 차단 시 `security_logs`에는 분류·전송 방식·선택적 사용자 UUID·서버 시각을 기록하며, 원문 학습자 입력과 매칭 문자열은 저장하지 않습니다. 감사 DB 장애가 나도 요청은 차단하고 일반적인 경고만 기록합니다. 감사 기록 대기는 2초로 제한하지만 이미 실행된 동기 worker는 이후에 끝날 수 있습니다.

보안 감사 레코드는 원문을 제외한 분류 정보로 구성합니다. 일반 대화 기록에는 사용자 메시지를 저장하며 REST 채팅 로그에는 답변 일부가 출력되므로, 운영 시 대화 기록과 로그의 접근 권한·보존 기간을 함께 관리합니다.

## Database Baseline

`supabase/migrations/`의 다섯 파일은 애플리케이션 코드와 설계 자료를 바탕으로 구성한 **신규 DB용 기준 스키마**입니다. 사용자는 UUID, 세션·개념·문항·퀴즈 시도는 bigint ID를 사용합니다. 출석 테이블명은 코드와 같은 `user_attendance`입니다.

기준 스키마에는 사용자·개념에서 세션·대화 기록으로 이어지는 삭제 관계, 퀴즈 평가와 `hakes_gain`, 일일 출석의 유일성 제약 등이 포함됩니다. 기존 DB는 타입·제약조건·권한·컬럼을 대조하고 백업한 뒤 배포별 업그레이드를 준비해야 합니다. 기존 테이블 위에 기준 마이그레이션을 그대로 실행하지 않습니다. 기존 `security_logs`는 `user_id`, `threat_type`, `transport`, `created_at`과 정합성을 확인해야 합니다.

캐시는 `namespace`, 해당 유일성 인덱스, `hit_count`, v2 RPC를 사용합니다. 기존 DB에 연결하려면 이 구성을 확인해야 합니다. 조회 대상은 namespace가 지정된 캐시 행입니다.

Supabase에는 `anon`, `authenticated`, `service_role` 역할이 제공됩니다. 로컬 Docker 초기화는 이에 대응하는 역할을 준비합니다. 기준 마이그레이션은 애플리케이션 테이블에 RLS를 활성화하고 브라우저용 정책과 직접 접근 권한을 제공하지 않습니다. 일반 애플리케이션 접근은 FastAPI의 **service-role 키**를 사용하며 anon 키만으로는 동작하지 않습니다. 애플리케이션 자체 JWT는 Supabase Auth JWT와 다릅니다. 사용자·세션 소유권 검증 책임은 백엔드에 있습니다.

PUBLIC/anon/authenticated는 문제 테이블을 읽거나 두 캐시 RPC를 실행할 수 없습니다. 마이그레이션 역할이 이후 생성하는 객체의 기본 권한도 제한합니다. DB 관리자 권한까지 없다는 뜻은 아닙니다.

## Local Docker Setup

다음은 신규·폐기 가능한 로컬 환경용 절차입니다. 첫 Docker 실행 **전에** 저장소 루트에서 설정을 생성합니다.

```powershell
# Windows PowerShell
.\.venv\Scripts\python.exe scripts/create_local_env.py
```

```sh
# Linux / macOS
.venv/bin/python scripts/create_local_env.py
```

이 스크립트는 Git에서 제외되는 루트 `.env`를 생성하고 기존 파일 덮어쓰기를 거부합니다. Compose에 필요한 `LOCAL_DB_PASSWORD`, `LOCAL_NEO4J_PASSWORD`와 로컬 서비스 설정을 준비합니다. DB와 HTTP 서비스가 같은 인증값을 사용하도록 생성 후 Docker를 실행합니다.

기존 `.env`가 있으면 보존하고 설정을 대조합니다. `--output`으로 별도 파일을 만든 경우 Compose의 `--env-file`뿐 아니라 백엔드와 테스트 프로세스에도 같은 설정을 전달해야 합니다. 통합 실행기는 기본적으로 루트 `.env`를 읽습니다. 암호를 바꾸어도 기존 DB 볼륨의 암호가 자동 변경되지는 않습니다. 생성된 서비스 토큰은 30일 후 만료되며 운영 환경에 사용하지 않습니다.

```sh
docker compose --profile api up -d --wait db rest gateway
```

마이그레이션은 Bash, `sha256sum`, Docker CLI가 필요합니다. Windows에서는 Docker Desktop에 연결 가능한 Git Bash 또는 WSL에서 저장소 루트를 열어 실행합니다. 컨테이너에 마운트되는 `scripts/db/*.sh`는 LF 줄바꿈이어야 합니다.

```sh
bash scripts/db/migrate.sh
bash scripts/db/migrate.sh
```

각 마이그레이션 파일은 트랜잭션과 checksum ledger를 사용해 적용합니다. 두 번째 실행은 checksum이 같은 적용 완료 파일을 건너뜁니다. 적용된 파일을 수정하면 실패하므로 배포된 마이그레이션을 고치지 말고 별도의 업그레이드 파일을 준비해야 합니다. 이 동작은 퀴즈 API의 여러 저장 요청을 단일 트랜잭션으로 묶는 기능과는 별개입니다.

개념 Seed를 먼저 적재하고 예시 문항을 추가합니다.

**Bash**

```sh
docker compose exec -T db psql -U postgres -d antutor -v ON_ERROR_STOP=1 < supabase/seed/concepts.sql
docker compose exec -T db psql -U postgres -d antutor -v ON_ERROR_STOP=1 < supabase/seed/concepts.example.sql
docker compose restart rest
```

**Windows PowerShell**

```powershell
cmd /c "docker compose exec -T db psql -U postgres -d antutor -v ON_ERROR_STOP=1 < supabase\seed\concepts.sql"
cmd /c "docker compose exec -T db psql -U postgres -d antutor -v ON_ERROR_STOP=1 < supabase\seed\concepts.example.sql"
docker compose restart rest
```

PostgREST 재시작은 마이그레이션 이후 스키마 캐시를 다시 읽기 위한 절차입니다. DB는 기본 loopback 포트 54322, gateway는 54321을 사용합니다. `LOCAL_DB_PORT`와 `LOCAL_API_PORT`로 포트를 바꿀 수 있으며, HTTP 포트를 바꾸면 `SUPABASE_URL`도 맞춰야 합니다.

gateway는 `/rest/v1`을 PostgREST로 전달합니다. PostgREST는 NOINHERIT authenticator로 로그인한 뒤 서명된 service-role claim에 따라 역할을 전환합니다. 익명 접근은 차단됩니다. 이 구성은 최소 테이블/RPC HTTP gateway이며 Supabase Auth·Storage·Realtime 전체를 재현하지 않습니다. FastAPI의 자체 가입·JWT 흐름은 해당 테이블/RPC 작업을 사용합니다. FastAPI는 루트 `.env`를 읽지만 실제 LLM 응답에는 별도 모델 서버가 필요합니다.

원본으로 제공된 두 개념 CSV는 열 순서만 다릅니다. `concepts.sql`은 제공된 필드를 보존한 원본 30개 레코드를 적재합니다. [Seed 출처](../supabase/seed/data-provenance.md)를 참고하세요. `concepts.example.sql`은 기존 개념을 덮어쓰지 않고 인플레이션 예시 문항 1개를 추가합니다. Seed는 재실행할 수 있으며 ID·이름 충돌 시 기존 관계를 임의로 재매핑하지 않고 실패합니다. 신규 Supabase 환경에서는 권한·확장 구성을 확인한 뒤 이 기준 스키마와 Seed를 적용합니다.

## SQL Verification

SQL 검사는 트랜잭션 안에서 시험 데이터를 생성한 뒤 롤백하며, 실제 접근 거부·삭제 관계·퀴즈 제약조건·캐시 카운터와 TTL을 확인합니다.

```sh
# Bash
docker compose exec -T db psql -U postgres -d antutor -v ON_ERROR_STOP=1 < tests/sql/schema_checks.sql
```

```powershell
# Windows PowerShell
cmd /c "docker compose exec -T db psql -U postgres -d antutor -v ON_ERROR_STOP=1 < tests\sql\schema_checks.sql"
```

마이그레이션 재실행은 앞 절의 두 번째 `migrate.sh` 호출로 확인합니다. Seed 재실행은 `concepts.sql` 적재 명령을 한 번 더 실행하여 확인합니다. CI의 database job도 이 두 재실행을 포함합니다. Docker 볼륨은 명시적으로 제거하기 전까지 유지됩니다.

## Quiz API Contract

### GET /quiz/{concept}

별도 사용자 인증 의존성이 없는 조회 API입니다. 개념명은 공통 정규화 함수로 처리하고 `concepts.name`으로 찾습니다. 예를 들어 `인플레이션`은 `inflation`으로 매핑됩니다. 등록된 alias와 문자열 정규화를 사용하는 기능이며 임의의 자연어를 의미 검색하는 기능은 아닙니다.

문제는 해당 `concept_id`로 필터링하고 `question_id` 오름차순 최대 5개를 반환합니다. 각 응답은 `id`, `concept`, `question`, `choices`를 포함하고 정답·해설은 포함하지 않습니다. `concept`는 DB에서 확인한 이름입니다.

| 상황 | 응답 |
|---|---|
| 등록된 개념에 문제 있음 | 200, 해당 개념의 문항 배열 |
| 등록된 개념에 문제 없음 | 200, `[]` |
| 등록되지 않은 개념 | 404 |
| 개념·문제 DB 조회 실패 | 503 |

### POST /quiz/submit

인증이 필요한 제출 API입니다. `QuizSubmission`의 `user_id`는 문자열 필수 필드로 남아 있지만, 저장할 사용자 ID는 인증 토큰에서 얻은 값으로 덮어씁니다. 요청 본문의 사용자 ID를 신뢰하지 않습니다.

`answers`는 최소 1개여야 합니다. `question_id`는 정수 또는 비어 있지 않은 문자열이며 bool은 거부합니다. 중복 판정에는 문자열 변환 후 앞뒤 공백을 제거한 값을 사용하므로 `1`과 `"1"`은 중복입니다. 모든 ID 문자열을 숫자로 정규화하는 계약은 아닙니다.

`selected_choice`는 정수 1–6, `confidence_level`은 정수 0–3입니다. 선택지 6은 확신도 0과 함께 사용하고 점수는 0입니다. 선택지 1–5는 확신도 1–3이어야 합니다.

모든 제출 문항이 요청한 개념에 속하는지 저장 전에 확인합니다. `session_id`를 전달하면 해당 세션이 인증된 사용자 소유이며 요청한 개념과 일치해야 합니다. 점수는 DB 정답과 CBM 규칙을 사용하여 서버에서 계산합니다.

| 상황 | 처리 |
|---|---|
| 빈 답안·중복 ID·스키마 규칙 위반 | 422 |
| 조회된 결과에 제출 문항이 없거나 다른 개념의 문항 | 422, 퀴즈 삽입 전에 거부 |
| 등록되지 않은 개념 | 404 |
| 요청 세션이 없거나 사용자·개념 불일치 | 404 |
| 개념·세션·채점 데이터 조회, 저장 또는 후처리 DB 실패 | 503 |
| PRE 정상 제출 | 점수와 최대 점수; 정답·해설 상세는 `null` |
| POST 정상 제출 | 점수와 제출 문항의 정답·해설·획득 점수 |

제출 검증의 기준은 개념 소속과 답안의 유효성입니다. POST는 해당 개념에 속하는 문항을 최소 1개 받으며, GET의 최대 5개 제한은 조회에만 적용됩니다. PRE·POST 유형은 요청의 `is_pre_test`로 구분합니다. 호출자는 이 API를 이용해 학습 순서와 제출할 문항 구성을 관리합니다.

### PRE/POST Comparison

POST에 세션이 있으면 같은 사용자·세션의 최신 PRE를 `created_at`, `attempt_id` 내림차순으로 찾습니다. 비교 대상은 이 PRE 한 건이며, 답안의 문항 ID 집합과 개수가 POST 제출과 같을 때 향상도를 계산합니다.

```text
MAX = 채점된 문항 수 × 3
runtime gain = (POST - PRE) / (MAX - PRE)
PRE = MAX인 경우 runtime gain = 0
```

세션 없음, PRE 없음, 최신 PRE 답안 집합·개수 불일치 시 `skill_improvement`, `pre_test_score`, `pre_test_details`는 `null`입니다. 세션이 있는 POST는 이 경우 기존 `sessions.hakes_gain`도 `null`로 갱신합니다. 조회·갱신의 DB 실패는 정상적인 비교 불가와 구분하여 503을 반환합니다.

과거 사용자 평가의 재분석은 점수 향상·하락에 서로 다른 분모를 사용하는 공식입니다. 런타임 계산과 평가 통계의 계산 절차는 구분하며, 평가 집계와 공식은 [User Evaluation](evaluation/user-evaluation.md)을 참고하세요.

### Persistence Limits

퀴즈 저장은 `quiz_attempts` 삽입, `quiz_answers` 삽입, 필요한 경우 세션 향상도 갱신을 각각 별도 HTTP 요청으로 수행합니다. 저장 또는 후처리 실패 시 503을 반환하며, 앞서 처리한 기록은 DB에 남을 수 있습니다. 같은 요청을 다시 제출하면 별도 시도가 생성될 수 있으므로 재시도 처리 시 저장 결과를 확인해야 합니다.

## Attendance API

`GET /api/attendance`와 `POST /api/attendance`는 인증된 사용자를 대상으로 하며 날짜는 KST를 기준으로 처리합니다. DB 처리에서 예외가 발생하면 503을 반환합니다. API 통합 검사는 출석 저장·조회 정상 경로를 확인합니다.

## API and Quiz Integration Checks

폐기 가능한 로컬 DB·PostgREST·gateway에 마이그레이션과 두 Seed를 적용하고 PostgREST를 재시작한 상태에서 실행합니다. 테스트 API용 8082 포트를 비워 두어야 합니다.

`tests/integration/run_api_check.py`는 로컬 FastAPI를 시작한 뒤 `check_api.py`, `check_quiz.py`를 차례로 실행합니다. `check_quiz.py`는 합성 개념·문항·사용자·세션을 만들고 GET 필터링, POST 검증, 소유권, 저장 점수, PRE/POST 향상도를 확인합니다. 잘못된 제출에서 기록이 생성되지 않는지도 확인하지만 저장 중 장애의 트랜잭션 롤백을 검사하는 것은 아닙니다.

```powershell
# Windows PowerShell, 저장소 루트
$env:ANTUTOR_DISPOSABLE_TESTS = '1'
.\.venv\Scripts\python.exe tests/integration/run_api_check.py
```

```sh
# Bash, 저장소 루트
ANTUTOR_DISPOSABLE_TESTS=1 .venv/bin/python tests/integration/run_api_check.py
```

`ANTUTOR_DISPOSABLE_TESTS=1`이 필요하며 API와 Supabase HTTP 주소는 localhost/127.0.0.1/::1이어야 합니다. 실행기는 `TEST_API_URL`을 `http://127.0.0.1:8082`로 지정합니다. 루트 `.env`를 읽되 프로세스 환경변수가 우선하므로 `SUPABASE_URL`과 `SUPABASE_KEY`가 같은 임시 DB를 가리키는지 확인합니다. 운영 자격증명은 필요하지 않습니다. loopback 검사는 로컬 프록시·터널 뒤의 실제 대상이나 DB 폐기 가능성까지 판별하지 못합니다.

API 로그는 `api-integration.log`에 기록합니다. 실행기는 자신이 시작한 API 프로세스를 종료하지만 DB fixture나 Docker 볼륨을 제거하지 않습니다. CI는 별도 종료 단계에서 임시 컨테이너와 볼륨을 정리합니다. 로컬에서는 테스트용으로 만든 Compose 프로젝트와 볼륨인지 확인한 뒤 정리해야 합니다.

## Frontend Quiz Scope

`front/src/api/services.js`의 퀴즈 조회 함수는 URL에 `encodeURIComponent(concept)`를 사용합니다. `QuizScreen`은 `null`/`undefined`를 대기 상태로, `[]`을 조회가 완료된 빈 결과로 구분합니다. 빈 배열이면 한국어 “등록된 퀴즈가 없습니다” 또는 영어 안내를 즉시 표시하며 자동 제출하거나 완료 콜백을 호출하지 않습니다.

문항이 있는 PRE는 기존 최소 로딩 대기 동작을 유지합니다. 네트워크 조회 오류를 빈 콘텐츠로 바꾸는 기능은 없으며, 상위 컴포넌트가 연결될 때 오류와 빈 결과를 구분해야 합니다.

`App.js`의 미션 선택은 인플레이션 학습 세션으로 연결됩니다. `QuizScreen`은 이 렌더링 경로와 분리된 컴포넌트로, 화면에 연결할 때 상위 컴포넌트에서 문항·세션·완료 콜백을 전달해야 합니다. 프론트 테스트는 API를 mock으로 대체하여 컴포넌트와 API 함수의 동작을 검사합니다.

## Conservative Synthesis Cache

캐시는 채팅 라우트에서 조기 반환하는 방식이 아니라 공통 그래프의 retry·최종 synthesis 노드 안에서 재사용합니다. 캐시 적중을 이유로 Guardrail, 전문가 평가, Scaffolding 판단, 세션·로그 갱신을 생략하지 않습니다. 재사용 대상은 구조화된 synthesis 결과이며 점수를 임의로 0으로 만들거나 이력을 건너뛰지 않습니다. 스트리밍 캐시 적중 시 모델 토큰 조각 없이 정상 최종 결과를 전달합니다. Scaffolding 생성과 학습자 범위가 없는 sandbox·benchmark 호출은 캐시하지 않습니다.

namespace는 학습자·세션·개념, 세션 상태, 직전 질문 해시, 정확한 답변, Scaffolding 상태, mastery count, 직전 weakest agent, 이력, 해당 요청의 전문가 근거를 포함한 전체 synthesis 프롬프트, 프롬프트 버전, 모델 설정을 해시합니다. 벡터 유사성만으로 이 경계를 넘을 수 없습니다. 정확한 프롬프트·답변 해시는 학습 상태에 맞는 재사용을 위해 적중률을 의도적으로 낮춥니다.

`MODEL_VERSION`은 변경되지 않는 배포·모델 revision으로 설정하고, 같은 모델명·URL에서 가중치가 변경되면 갱신합니다. `PROMPT_VERSION` 기본값은 프롬프트 소스의 SHA-256이며, 명시적인 릴리스 버전이 있을 때만 덮어씁니다.

범위가 지정된 RPC는 실제 적중 시 `hit_count`를 원자적으로 증가시키고 24시간이 지난 항목을 제외합니다. 조회 시험에서는 카운터를 늘리지 않습니다. 캐시·임베딩 작업 실패 시 일반 생성으로 진행하며 잘못된 형식의 synthesis는 캐시하지 않습니다.

namespace 유일성 덕분에 B-tree로 최대 한 후보를 찾으므로, 측정 근거가 없는 `IVFFlat lists=100` 인덱스를 추가하지 않았습니다. 넓은 범위 검색을 다시 도입한다면 대표 데이터의 재현율·지연·필터 후보 수를 측정한 뒤 ANN 인덱스와 lists 수를 선택해야 합니다. 만료 항목은 백엔드·관리자 권한으로 다음 조건을 사용하여 주기적으로 정리할 수 있습니다.

```sql
DELETE FROM semantic_cache WHERE created_at < now() - interval '24 hours';
```

## Neo4j

`neo4j/seed/relation_data.csv`는 원본 80행 관계 데이터에서 정규화한 결과로, 32개 개념과 69개 고유 관계를 제공합니다. 역방향으로 중복된 RELATED_TO/CONTRASTS_WITH는 합치고 CAUSES/PART_OF/REQUIRES는 제공된 방향을 유지합니다. 같은 관계의 서로 다른 reason은 삭제하지 않고 합칩니다. 제공된 인과관계를 독립적으로 사실 검증한 것은 아닙니다. 원본 체크섬과 변환 정책은 [출처 문서](../neo4j/data-provenance.md)에 있습니다. 개념명 유일성 제약과 MERGE로 재실행 시 중복 생성을 방지합니다.

```sh
docker compose up -d neo4j
```

Neo4j가 연결 가능한 상태가 되면 저장소 루트에서 실행합니다. 로컬 설정은 `NEO4J_URI=bolt://localhost:7687`, `NEO4J_USER=neo4j`, `NEO4J_PASSWORD`에 로컬 Neo4j 암호, `NEO4J_DATABASE=neo4j`를 사용합니다.

```powershell
# Windows PowerShell
.\.venv\Scripts\python.exe scripts/seed_neo4j.py
```

```sh
# Linux / macOS
.venv/bin/python scripts/seed_neo4j.py
```

관리형 Neo4j의 `neo4j+s://` 또는 `bolt+s://` URI는 제공된 검증 가능한 주소를 그대로 사용합니다. 로컬 일반 Bolt 포트는 Compose에서 loopback으로 제한합니다. 드라이버는 설정된 DB를 사용하며 인플레이션/CPI/Interest_Rate 같은 alias는 Seed 적재와 조회에서 같은 방식으로 정규화합니다.

## Tests and Runtime Data

저장소 루트에서 단위 테스트를 실행합니다.

```powershell
# Windows PowerShell
.\.venv\Scripts\python.exe -m pytest -q
```

```sh
# Linux / macOS
.venv/bin/python -m pytest -q
```

단위 테스트는 외부 의존성을 대체하며 실제 추론, 학습자 기록 또는 유료 API 호출을 검증하지 않습니다. 퀴즈 오류 주입과 통합 실행 환경 검사는 단위 테스트에 포함됩니다. 실제 SQL·API·Neo4j 검사는 CI에서 Docker 환경을 사용합니다.

워크플로의 backend job은 단위 테스트와 임시 DB의 API·퀴즈 검사를 실행하고, database job은 신규 마이그레이션·Seed 재실행·권한과 제약조건을 확인합니다. frontend job은 `CI=true`로 Jest와 빌드를 실행하고, graph job은 Neo4j Seed 재실행을 확인합니다. 테스트 결과는 각 커밋의 실행 로그에서 확인합니다.

기존 진단 도구는 `scripts/diagnostics`, 수동 통합·성능 스크립트는 `tests/manual`과 `tests/performance`에 있으며 기본 pytest 대상에서 제외됩니다. DB 쓰기나 유료 추론 호출이 있을 수 있으므로 개별 스크립트를 검토한 뒤 사용합니다. 해당 출력은 자동화 테스트 전체가 통과했다는 근거가 아닙니다.

런타임 로그와 생성 보고서는 Git에서 제외됩니다. debate/sandbox 파일 덤프는 기본 비활성화이며 `ENABLE_PRIVATE_DEBUG_LOGS=true`이면 제외된 `runtime-logs/` 또는 `PRIVATE_LOG_DIR`에 기록합니다. 이 설정과 별도로 stdout 로그도 수집될 수 있으므로, 운영 로그의 접근 권한과 보존 기간은 배포 환경에서 관리해야 합니다.
