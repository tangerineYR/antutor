<div align="center">

<img src="front/public/images/antutor%20logo%20final.png" width="360" alt="Antutor 로고" />

# Antutor

### Multi-Agent Economics Tutor

**학습자가 경제 개념을 자기 말로 설명하면, 이론·시장 사례·개념 관계를 살펴보는 세 AI 에이전트가 피드백합니다. 답변의 상태에 따라 재설명 요청, 교차 검토, 단계별 힌트를 제공합니다.**

[![Verification](https://github.com/tangerineYR/antutor/actions/workflows/ci.yml/badge.svg)](https://github.com/tangerineYR/antutor/actions/workflows/ci.yml)
![FastAPI](https://img.shields.io/badge/FastAPI-Backend-009688?logo=fastapi&logoColor=white)
![LangGraph](https://img.shields.io/badge/LangGraph-Orchestration-1C3C3C)
![React](https://img.shields.io/badge/React-Frontend-61DAFB?logo=react&logoColor=black)

</div>

## Contents

[Overview](#overview) · [Key Results](#key-results) · [Tech Stack](#tech-stack) · [Engineering Decisions & Validation](#engineering-decisions--validation) · [Architecture](#architecture) · [Quick Start](#quick-start) · [Tests & CI](#tests--ci) · [Documentation](#documentation) · [Scope & Limitations](#scope--limitations)

## Overview

Antutor는 경제 개념을 설명하는 학습자의 답변에서 개념 오해와 보완할 부분을 찾는 캡스톤 프로젝트입니다. 이론 검토 에이전트는 정의와 인과관계를, 시장 에이전트는 실제 사례와 적용 맥락을, 거시경제 에이전트는 다른 개념과의 관계를 평가합니다. 학습자는 답변을 다시 설명하거나 피드백을 바탕으로 대화를 이어갈 수 있습니다.

### Project Info

| 항목 | 내용 |
| --- | --- |
| 유형 | 팀 캡스톤 디자인 |
| 담당 | 팀 리드, 백엔드, AI 에이전트 실행 흐름 설계 |
| 팀 개발 기록 | 2026.03.24–2026.06.03 |
| 개인 포트폴리오 | 2026년 10월 이후 인증·접근 제어, 캐시 격리, DB 마이그레이션, 로컬 실행 및 자동화 검증 개선 |
| 팀 저장소 | [Antutor/antutor-repository](https://github.com/Antutor/antutor-repository) |

## Key Results

| 평가 | 확인된 결과 | 해석 범위 |
| --- | --- | --- |
| 사전·사후 원점수 | PRE/POST 25쌍, 평균 3.52 → 5.92점, 평균 변화 +2.40점 | 대응표본 검정 p ≈ 0.204 |
| 정규화 향상도 | 같은 25쌍의 향상도를 0과 비교한 일표본 검정 p ≈ 0.003, Cohen's d ≈ 0.66 | 점수 상승·하락의 분모가 다른 과거 평가 공식 적용 |
| 사용성 설문 | 학습 도움도 4.22/5(n=32), 힌트 적절성 4.10/5(n=31) | 문항별 유효 응답 집계 |
| 지식그래프 | 관계 데이터 80행을 개념 31개와 고유 관계 69개로 정규화 | Neo4j에 재실행 가능한 시드로 제공 |

학습 점수와 설문은 팀 프로젝트 당시 평가의 집계 자료입니다. 표본과 검정이 답하는 질문은 [사용자 평가](docs/evaluation/user-evaluation.md)에서 확인할 수 있습니다. 캐시의 당시 단일 요청 비교는 [과거 캐시 측정 기록](docs/evaluation/semantic-cache-historical.md)에 남아 있습니다.

## Tech Stack

| 영역 | 기술 | 활용 |
| --- | --- | --- |
| 백엔드 | Python, FastAPI, WebSocket | 세션·채팅·개념 사전·퀴즈·출석 API |
| 평가 흐름 | LangGraph, LangChain, asyncio | 초안 평가, 조건 분기, 교차 검토, 동시 호출 제한 |
| 모델 서빙 | Qwen3, vLLM, Ollama | 기본 OpenAI 호환 추론과 로컬 추론 옵션 |
| 관계형·벡터 데이터 | Supabase PostgreSQL, pgvector, sentence-transformers | 학습 기록, 퀴즈, 문맥별 답변 캐시 |
| 외부 문맥 | Neo4j, Tavily | 개념 관계 및 시장 사례 검색 |
| 웹 화면 | React, Recharts | 인플레이션 채팅 미션, 개념 사전, 출석과 학습 화면 |
| 개발과 검증 | Docker Compose, PostgREST, Nginx, pytest, Jest, GitHub Actions | 로컬 DB·HTTP 구성, API·DB·프런트엔드·그래프 검사 |

## Engineering Decisions & Validation

| 문제 | 설계 결정 | 검증 근거 |
| --- | --- | --- |
| 잘못된 개념 설명이 토론으로 이어질 수 있음 | 이론 검토 에이전트의 판정으로 재설명 경로와 교차 검토 경로를 분기 | [LangGraph 분기 테스트](tests/test_multi_agent_graph.py) |
| 여러 에이전트가 같은 모델 서버를 호출함 | 평가와 교차 검토 내부의 독립 호출을 병렬로 시작하고 세마포어로 추론 동시 호출 제한 | [평가 노드](back/multi_agent/nodes.py) · [모델 호출 설정](back/multi_agent/llm_config.py) |
| 다른 학습 맥락의 답변이 캐시에서 재사용될 수 있음 | 학습자·세션·답변·프롬프트·모델을 범위 키에 반영하고 최종 생성 결과만 재사용 | [캐시 범위 테스트](tests/test_semantic_cache.py) |
| 퀴즈 점수와 비교 대상이 일치해야 함 | 서버에서 개념·문항·세션 소유권을 검증해 채점하고, 같은 문항의 PRE·POST만 비교 | [채점 테스트](tests/test_quiz_scoring.py) · [퀴즈 API 통합 검사](tests/integration/check_quiz.py) |
| DB 구성과 그래프 시드를 반복 설치할 수 있어야 함 | 신규 DB 마이그레이션과 Neo4j 시드를 분리해 적용하고 재실행 시 중복을 방지 | [CI 워크플로](.github/workflows/ci.yml) |

## Architecture

~~~mermaid
flowchart TB
    U["학습자 설명"] --> A["FastAPI 세션·입력 검사"]
    A --> Q{"채팅 경로 판단"}
    Q -->|힌트 요청| H["단계별 힌트"]
    Q -->|일반 평가| C["외부 문맥·세 에이전트 평가"]
    C --> R{"재설명 필요"}
    R -->|예| T["재설명 피드백"]
    R -->|아니요| B["교차 검토·최종 피드백"]
~~~

시장 에이전트에 Tavily 검색 결과를, 거시경제 에이전트에 Neo4j의 개념 관계를 전달합니다. Neo4j는 선택 개념의 양방향 1단계 관계와 설명을 조회합니다. 학습자·대화·퀴즈 상태는 PostgreSQL에 저장합니다. 모델 호출 흐름과 로컬 구성은 [개발 가이드](docs/development.md#tutoring-runtime)를 참고하세요.

## Quick Start

CI는 Python 3.12와 Node.js 22를 사용합니다. Docker Compose는 로컬 PostgreSQL과 HTTP 게이트웨이를 실행합니다. 실제 AI 채팅에는 별도로 실행 중인 추론 서버가 필요합니다.

~~~sh
git clone https://github.com/tangerineYR/antutor.git
cd antutor
~~~

1. [Python·Node 환경](docs/development.md#development-environment)을 준비합니다.
2. [로컬 DB 구성](docs/development.md#local-docker-setup)에 따라 `.env`를 만든 뒤 PostgreSQL·PostgREST·게이트웨이를 시작하고 마이그레이션과 개념 시드를 적용합니다.
3. [추론 서버](docs/deployment/gcp-vllm.md)를 연결합니다. 기본값은 vLLM의 `Qwen/Qwen3-14B-AWQ`이며, Ollama를 선택할 수 있습니다.
4. [백엔드와 프런트엔드](docs/development.md#run-the-application)를 시작합니다. 개발 화면은 `http://localhost:3000`, FastAPI는 `http://localhost:8080`입니다.

웹 미션 선택은 현재 인플레이션 채팅으로 연결됩니다. 개념별 퀴즈 조회·제출 API와 `QuizScreen` 컴포넌트는 별도로 검증합니다. [프런트엔드 범위](docs/development.md#frontend-quiz-scope)

## Tests & CI

| 작업 | 검증 범위 |
| --- | --- |
| Backend | pytest, 임시 DB 기반 API·퀴즈 통합 검사 |
| Database | 마이그레이션과 개념 시드 재실행, 접근 권한·제약, 캐시 카운터·만료 |
| Frontend | Jest, 개념명 URL 인코딩, 퀴즈의 대기·빈 결과 상태, 빌드 |
| Graph | Neo4j 시드 재실행과 개념·관계 확인 |

[실행 방법](docs/development.md#tests-and-runtime-data) · [GitHub Actions](https://github.com/tangerineYR/antutor/actions/workflows/ci.yml)

## Project Structure

| 경로 | 역할 |
| --- | --- |
| [`back/`](back/) | FastAPI 라우터, LangGraph 노드, 상태별 캐시와 평가 서비스 |
| [`front/`](front/) | React 앱, 채팅과 학습 화면, API 호출 |
| [`supabase/`](supabase/) | 신규 PostgreSQL 스키마와 개념 시드 |
| [`neo4j/`](neo4j/) | 개념 관계 시드와 적재 쿼리 |
| [`docs/`](docs/) · [`tests/`](tests/) | 개발·배포·평가 문서와 자동화 검사 |

## Documentation

| 문서 | 내용 |
| --- | --- |
| [Development and Verification](docs/development.md) | 실행 환경, 에이전트 흐름, 퀴즈 API 계약, 로컬·CI 검증 |
| [GCP L4 and vLLM](docs/deployment/gcp-vllm.md) | 기본·로컬 추론 설정과 과거 배포 구성 |
| [User Evaluation](docs/evaluation/user-evaluation.md) | 학습 점수, 설문, 평가 방식의 탐색 비교 |
| [Historical Semantic Cache Benchmark](docs/evaluation/semantic-cache-historical.md) | 과거 단일 요청 비교와 해석 범위 |
| [Evaluation Data Provenance](docs/evaluation/data-provenance.md) | 공개 집계·차트·GPU 구성 기록 |
| [Concept Seed](supabase/seed/data-provenance.md) · [Graph Seed](neo4j/data-provenance.md) | 개념 출처, 관계 정규화와 적재 방법 |

## Scope & Limitations

- 웹 학습 미션은 인플레이션 채팅 중심입니다. 공개 시드에는 개념 30개가 포함되며 일부 정의와 사전 항목은 비어 있거나 자리표시 문구가 들어 있습니다.
- CI는 코드·API·DB·컴포넌트의 동작을 확인합니다. 실제 모델 응답 품질과 GPU 추론 지연은 별도로 측정해야 합니다.
- 캐시 지연 수치는 당시 조건당 요청 1회의 기록입니다. 학습자·세션·정확한 응답 상태로 격리한 현재 캐시의 지연은 별도 측정이 필요합니다.
- 학습 점수는 과거 평가 집계입니다. 평가군의 표본 선정과 배정 방식에는 확인 범위가 있어 집단 간 학습 효과의 인과적 비교는 제한됩니다.

## License & Usage

Antutor는 팀 공동 작업을 기반으로 한 개인 포트폴리오 포크입니다. 저장소의 이용 조건과 팀 작업 출처는 [NOTICE](NOTICE.md)를 참고하세요.