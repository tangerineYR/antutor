# Graph Seed Provenance

공개 시드 [`seed/relation_data.csv`](seed/relation_data.csv)에는 경제 개념 31개와 관계 69개가 있습니다. 팀 프로젝트의 관계 CSV(UTF-8, 80행)를 기반으로 합니다. 공개 관계에 연결된 31개 개념은 PostgreSQL 개념 시드의 30개와 그래프에만 있는 `recession`으로 구성됩니다.

| 정규화 항목 | 적용 규칙 |
| --- | --- |
| 개념명 | Unicode NFKC, 소문자, 공백 정규화와 등록된 별칭 적용 |
| 대칭 관계 | `RELATED_TO`, `CONTRASTS_WITH`의 양 끝 개념을 정렬해 역방향 중복 제거 |
| 방향 관계 | `CAUSES`, `PART_OF`, `REQUIRES`의 원래 방향 유지 |
| 관계 설명 | 동일한 설명은 한 번 저장하며, 같은 관계에 서로 다른 설명이 있으면 함께 보존 |

스태그플레이션과 실업의 관계에는 원자료의 두 설명이 모두 남아 있습니다. 관계와 설명은 원자료의 경제 개념을 구조화한 것으로, 활용 목적에 맞춘 개념 검수는 별도입니다.

적재는 [Python 시드 실행기](../scripts/seed_neo4j.py) 또는 Neo4j import 디렉터리에 CSV를 둔 뒤 [`import.cypher`](import.cypher)로 수행합니다. 두 방식 모두 관계 종류를 제한하고, 개념명 유일성 제약과 `MERGE` 키를 사용합니다. [Neo4j 로컬 설정](../docs/development.md#neo4j)