# Evaluation Data Provenance

저장소에는 공개 평가 집계와 과거 벤치마크 차트가 보존되어 있습니다. 배포 설정은 별도의 정규화된 구성 기록으로 보존합니다. 이 산출물에는 학습자 식별 정보, 자유서술 답변, 서버 주소 또는 자격증명이 포함되지 않습니다.

| 산출물 | 표현 방식 | 재현 가능한 범위 |
|---|---|---|
| [사용자 평가 집계](artifacts/user-evaluation-summary.json) | 프로젝트 평가 기록의 점수 요약 통계와 설문 평점 빈도 | 평균, t 통계량, p값, 효과크기, 응답 비율 재계산 |
| [과거 캐시 차트](artifacts/semantic-cache-historical.png) | 변경하지 않은 원본 Git 이미지 | 기록된 두 시간 확인 및 상대적 감소율 재계산 |
| [과거 GPU 설정](../deployment/gcp-vllm-historical.json) | 프로젝트 운영 기록의 하드웨어·서버·클라이언트 설정 정규화 | 문서화한 배포 설정 검토; 정확한 과거 실행의 재현은 아님 |

## User Evaluation Aggregates

Antutor 점수 표본에는 평가 점수표의 완전한 PRE/POST 쌍 25개가 모두 포함됩니다. 빈 행과 요약 수식은 제외했습니다. 별도의 헤더 없는 10행 표는 소속 집단과 중복 여부가 불명확하여 제외했습니다. 개념 읽기 집단에는 점수가 있는 기록 30개를 포함하고 서식만 있는 행은 제외했습니다. 이 기록들과 더 큰 설문 표본을 연결하는 선정 과정은 알려져 있지 않습니다. 점수 집단과 사용성 설문 응답자 사이의 참여자 연결을 가정하지 않습니다.

각 점수 지표의 공개 데이터에는 `n`, 산술평균, 표본 표준편차(`ddof=1`)를 보존합니다. 대응표본 원점수 변화의 표준편차는 독립 집단 표준편차를 조합한 값이 아니라 개인별 POST−PRE 차이로 계산한 값입니다. 정규화 향상도는 [User Evaluation](user-evaluation.md)의 비대칭 공식을 사용합니다. 설문에는 각 평점의 빈도와 결측 수를 보존하며 서로 다른 문항을 합치지 않습니다.

집계 과정에서 행 단위 점수, 식별자, 시각, 자유서술 답변을 제거했습니다. 명시한 계산에 필요한 통계는 보존하지만 개인별 대응 관계를 공개하거나 원래 채점·표본 선정의 타당성을 검증하지는 않습니다. 따라서 공개 재현은 집계로부터의 계산을 뜻하며 개별 답변의 독립적인 감사가 아닙니다.

## Historical Cache Chart

PNG는 [`1c5e5ba`의 `performance_test/cache_optimization_result.png`](https://github.com/tangerineYR/antutor/blob/1c5e5ba/performance_test/cache_optimization_result.png)와 바이트 단위로 동일한 이미지입니다.

SHA-256: `43746231a32d009a7be59f6a8d9f479fa9aafd96ebd5e6752b313baee06862d4`.

시간 레이블은 정수 밀리초입니다. 이미지와 함께 원시 시간 표본이나 성공 실행 명세가 제공되지 않습니다. [측정 한계](semantic-cache-historical.md)를 참고하세요.

## Historical GPU Configuration

[gcp-vllm-historical.json](../deployment/gcp-vllm-historical.json)은 기록된 L4 하드웨어와 이후 14B 서버·클라이언트 설정을 정리한 자료입니다. 모델 식별자와 추론 옵션을 보존하고 자격증명과 주소는 제외했습니다. 초기 8B 단계는 별도로 구분합니다. 알 수 없는 모델 revision과 이미지 digest는 `null`이며 릴리스 고정값이나 실행 시각을 임의로 만들지 않았습니다.

이 자료는 정리된 구성 기록이며 실제 서버가 실행 중이었다는 독립적인 증거는 아닙니다.
