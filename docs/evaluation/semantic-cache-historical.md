# Historical Semantic Cache Benchmark

프로젝트 당시 서로 다르게 표현한 인플레이션 답변 두 건을 순서대로 요청해 응답 시간을 비교했습니다. [원본 차트](artifacts/semantic-cache-historical.png)와 [당시 측정 코드](https://github.com/tangerineYR/antutor/blob/1c5e5ba192f80661aac45d65b16073a3b7761718/performance_test/semantic_caching_test.py)에 측정 조건이 남아 있습니다.

| 요청 조건 | 차트의 응답 시간 |
| --- | ---: |
| 전체 LLM 그래프 실행을 의도한 요청 | 30.314초 |
| 유사 답변 캐시 재사용을 의도한 요청 | 4.228초 |
| 첫 요청 대비 시간 차이 | 약 86.1% 감소 |

![당시 첫 번째 요청 30,314ms와 두 번째 요청 4,228ms를 표시한 차트](artifacts/semantic-cache-historical.png)

## Measurement Procedure

당시 스크립트는 서로 다른 사용자·세션의 `POST /chat` 요청을 각각 한 번 보내고, 사이에 1.5초를 기다립니다. 클라이언트에서 `time.time()`으로 경과 시간을 측정해 정수 밀리초로 표시합니다.

## Limits

- HTTP 오류가 발생해도 스크립트는 경과 시간을 반환합니다. 성공 응답의 `from_cache` 값은 출력하며 차트 저장 조건으로 검사하지 않습니다. 저장된 차트에는 응답 성공 여부와 캐시 적중 로그가 남아 있지 않습니다.
- 조건당 요청이 한 번이므로 반복 측정의 분산, 신뢰구간과 동시 사용자 지연은 계산할 수 없습니다. 정확한 서버 커밋·GPU·모델 revision·이미지 digest를 함께 기록한 실행 명세도 없습니다.
- 현재 구현의 캐시는 학습자·세션·입력·프롬프트 상태로 조회 범위를 지정합니다. 위 두 요청의 시간은 당시 비교값입니다. 현재 캐시의 상태 격리 테스트는 [캐시 테스트](../../tests/test_semantic_cache.py)에 있습니다.

당시 스크립트는 측정 전에 세션 로그와 개념 캐시 일부를 삭제합니다. 개발 검사에는 [자동화 테스트](../development.md#tests-and-runtime-data)를 사용합니다. [차트 출처와 체크섬](data-provenance.md#historical-cache-chart)