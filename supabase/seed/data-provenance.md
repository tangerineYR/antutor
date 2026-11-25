# Concept Seed Provenance

[`concepts.csv`](concepts.csv)는 팀 프로젝트의 두 개념 내보내기 파일에서 가져온 30개 기록입니다. 원본은 모두 개념 30행과 빈 행 20개로 구성되어 있으며, 같은 값을 서로 다른 열 순서로 담고 있습니다. 공개 CSV는 빈 행을 빼고 열 순서를 통일합니다. ID 1–30, 분류, 정의, 사전 내용, 허용 가능한 확장 설명, 핵심 용어와 답변 검증 프롬프트를 보존합니다.

원본 파일

- `concepts_data csv 36528346333c8033aaebc8875d46e857_all.csv`
- `concepts_data csv 36528346333c8033aaebc8875d46e857.csv`

## Import

저장소 루트에서 `python scripts/generate_concept_seed.py`를 실행하면 [`concepts.sql`](concepts.sql)을 생성합니다. 신규 DB에 마이그레이션을 적용한 뒤 개념을 적재하고, 필요하면 인플레이션 예시 문항을 추가합니다. 시드는 ID와 이름이 서로 충돌하면 오류를 반환합니다. 재실행 시 기존 정의를 보존하며, 자동 생성 ID 시퀀스는 적재한 ID 이후로 맞춥니다. [로컬 DB 설정과 적재 명령](../../docs/development.md#local-docker-setup)

## Coverage

정의가 비어 있는 개념은 12개(ID 9, 12, 13, 15, 16, 21, 22, 25, 27, 28, 29, 30)입니다. 사전 텍스트에 자리표시 문구가 있는 기록도 12개입니다. 공개 CSV에는 이 상태를 보존하며, 평가용으로 쓰려면 해당 내용을 검수해야 합니다. 학습자 및 계정 데이터는 포함하지 않습니다.

[`recession`은 Neo4j의 관계 시드](../../neo4j/data-provenance.md)에만 있습니다. `gross domestic product (gdp)`는 개념 목록의 이름인 `gross domestic product`로 정규화합니다.