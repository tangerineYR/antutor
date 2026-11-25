# Evaluation Data Provenance

| 공개 자료 | 내용 | 확인할 수 있는 범위 |
| --- | --- | --- |
| [사용자 평가 집계](artifacts/user-evaluation-summary.json) | 점수의 요약 통계와 문항별 설문 평점 빈도 | 평균, 검정 통계량, p값, 효과크기와 응답 비율 |
| [과거 캐시 차트](artifacts/semantic-cache-historical.png) | 프로젝트 당시 Git에 기록한 응답 시간 차트 | 두 요청 시간과 상대적 시간 차이 |
| [과거 GPU 구성](../deployment/gcp-vllm-historical.json) | 운영 자료의 하드웨어·모델·서버·클라이언트 설정 | 기록된 설정과 배포 구성 |

## User Evaluation Aggregates

Antutor 점수 표본은 완전한 PRE/POST 25쌍입니다. 빈 행과 요약 수식이 있는 행은 집계에서 제외합니다. 헤더가 없는 별도 10행은 소속 집단과 중복 여부를 확인할 수 없어 포함하지 않습니다. 개념 읽기 집단의 표본은 점수가 있는 30개 기록입니다. 점수와 설문을 참여자 단위로 연결하는 정보는 공개 집계에 없습니다.

점수는 `n`, 산술평균, 표본 표준편차(`ddof=1`)를 보존합니다. 원점수 변화의 표준편차에는 개인별 `POST − PRE` 차이를 사용합니다. 정규화 향상도의 공식은 [User Evaluation](user-evaluation.md#learning-scores)에 있습니다. 설문은 문항별 평점 빈도와 결측 수를 기록합니다.

개별 점수 행, 식별자, 응답 시각, 자유서술 답변은 공개 범위에서 제외합니다. [재계산 스크립트](user-evaluation.md#reproduction)는 공개 집계로부터 계산합니다. 개별 점수의 채점 과정과 표본 선정은 원자료가 있어야 확인할 수 있습니다.

## Historical Cache Chart

공개 PNG와 [당시 커밋의 차트](https://github.com/tangerineYR/antutor/blob/1c5e5ba192f80661aac45d65b16073a3b7761718/performance_test/cache_optimization_result.png)는 바이트가 같습니다.

차트의 시간은 정수 밀리초입니다. 요청 성공·캐시 적중 로그와 반복 측정값은 공개 자료에 포함되어 있지 않습니다. [측정 조건과 범위](semantic-cache-historical.md#limits)

## Historical GPU Configuration

[배포 기록](../deployment/gcp-vllm-historical.json)은 L4 하드웨어와 후기 14B 모델의 서버·클라이언트 설정을 운영 자료에서 정리한 것입니다. 초기 8B 프로토타입은 [Colab 노트북](../experiments/vllm_qwen3_colab.ipynb)에 남아 있습니다. 서버 주소와 자격증명은 공개 범위에서 제외합니다. 이미지 digest와 모델 revision은 확인할 수 없어 JSON에 `null`로 기록합니다. 이 자료로 검토할 수 있는 범위는 하드웨어와 배포 옵션입니다.