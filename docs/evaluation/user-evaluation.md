# User Evaluation

평가 집계와 계산에 사용한 자료는 [공개 JSON](artifacts/user-evaluation-summary.json)과 [데이터 출처](data-provenance.md)에서 확인할 수 있습니다.

## Learning Scores

완전한 PRE/POST 25쌍을 사용했습니다. 원점수의 사전·사후 차이와 정규화 향상도를 별도로 분석했습니다.

| 평가 항목 | 결과 |
| --- | ---: |
| PRE 평균(표본 표준편차) | 3.52 (7.500667) |
| POST 평균(표본 표준편차) | 5.92 (8.260952) |
| 평균 원점수 변화 | +2.40점 |
| 원점수 대응표본 t 검정 | t(24) = 1.306717, 양측 p = 0.203692 |
| 원점수 변화의 Cohen's dz | 0.261343 |
| 정규화 향상도 평균(표본 표준편차) | 0.332947 (0.504211) |
| 정규화 향상도를 0과 비교한 일표본 t 검정 | t(24) = 3.301663, 양측 p = 0.002999702 |
| 정규화 향상도의 Cohen's d | 0.660333 |

정규화 향상도는 당시 점수 범위인 −30점부터 15점을 사용합니다.

~~~text
POST > PRE: g = (POST - PRE) / (15 - PRE)
POST ≤ PRE: g = (POST - PRE) / (PRE + 30)
~~~

원자료 집계 기록의 25개 값에는 분모가 0인 사례가 없습니다. 공개 집계는 `d = mean(g) / sample_sd(g)`, `t = d × sqrt(n)`으로 일표본 검정을 재계산할 수 있게 제공합니다. 당시 사용한 검정 명세는 남아 있지 않습니다. 원점수의 평균 변화는 +2.40점이며 대응표본 검정의 p값은 약 0.204입니다. 정규화 향상도를 0과 비교하면 p값은 약 0.003입니다.

현재 앱이 비교에 사용하는 공식과 문항 일치 조건은 [PRE/POST Comparison](../development.md#prepost-comparison)에 설명합니다.

## Usability Survey

| 문항 | 유효 응답 | 평균 / 5 | 4점 이상 | 결측 |
| --- | ---: | ---: | ---: | ---: |
| 경제 개념 이해에 대한 학습 도움도 | 32 | 4.22 | 25/32 (78.125%) | 0 |
| 단계별 힌트의 적절성 | 31 | 4.10 | 25/31 (80.645%) | 1 |

학습 도움도의 응답은 3점 7명, 4점 11명, 5점 14명입니다. 힌트 적절성은 2점 4명, 3점 2명, 4점 12명, 5점 13명입니다. 실제 힌트 노출 여부와 점수 표본·설문 간 참여자 연결 정보는 공개 집계에 포함되어 있지 않습니다.

## Interpretation Limits

개념 읽기 집단의 기록 30개에서 PRE와 POST 평균은 각각 6.666667점과 7.033333점입니다. 무작위 배정과 표본 선정 과정은 확인할 수 없습니다. 집단별 평균은 평가 결과를 기술하는 값이며, Antutor의 사용이 학습 차이를 일으켰는지 판단하려면 집단 간 비교 설계가 필요합니다.

## Exploratory Evaluator Comparison

팀 프로젝트에서는 SemEval-2013 Beetle 전문가 레이블과 네 평가 방식의 스피어만 순위 상관계수를 비교했습니다. 프로젝트 기록에 남은 값은 다음과 같습니다.

| 평가 방식 | 스피어만 순위 상관계수 |
| --- | ---: |
| LLM Judge | 0.66 |
| LLM Atomic | 0.61 |
| 코사인 유사도 | 0.55 |
| NLI | 0.16 |

이 비교는 평가 구조를 선택할 때 참고한 탐색 실험입니다. 개별 예측값과 전체 실행 기록이 없어 공개 자료에서 수치를 다시 계산할 수 있는 범위는 위 학습 점수·설문 집계로 한정됩니다.

## Reproduction

저장소 루트에서 평가용 의존성을 설치하고 스크립트를 실행합니다.

~~~powershell
# Windows PowerShell
.\.venv\Scripts\python.exe -m pip install -r scripts/evaluation/requirements.txt
.\.venv\Scripts\python.exe scripts/evaluation/user_evaluation.py
~~~

~~~sh
# Linux / macOS
.venv/bin/python -m pip install -r scripts/evaluation/requirements.txt
.venv/bin/python scripts/evaluation/user_evaluation.py
~~~

스크립트는 공개 JSON에서 두 검정, 효과크기와 설문 통계를 계산합니다. 같은 스키마의 다른 집계는 `--summary path/to/summary.json`으로 선택할 수 있습니다.