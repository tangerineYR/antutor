# Neo4j 지식그래프 연동 서비스
# EconomicConcept 노드 간의 관계를 양방향으로 조회하여
# LLM 프롬프트에 사용할 수 있는 텍스트 형태로 반환합니다.

from neo4j import AsyncGraphDatabase
from config import NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD, NEO4J_DATABASE
from services.concept_normalization import normalize_concept

# The driver handles neo4j+s/bolt+s TLS verification. Plain bolt is supported
# for the loopback-only Docker development instance; do not strip secure schemes.
# Relationship type -> English description mapping
ACTION_EN_MAP = {
    "CAUSES": "causes or affects",
    "RELATED_TO": "is closely related to",
    "PART_OF": "is a part of or encompasses",
    "CONTRASTS_WITH": "contrasts with",
    "REQUIRES": "requires prior understanding of",
}

_CYPHER_QUERY = """
MATCH (a:EconomicConcept {name: $keyword})-[r]-(b:EconomicConcept)
RETURN startNode(r).name AS Subject,
       type(r)              AS Action,
       r.reason             AS Reason,
       endNode(r).name  AS Object
"""


_driver = None

async def get_neo4j_driver():
    global _driver
    if _driver is None:
        _driver = AsyncGraphDatabase.driver(
            NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD)
        )
    return _driver

async def get_economic_facts(keyword: str) -> str:
    """
    keyword: 영문 경제 개념명 (예: 'opportunity cost')
    Returns: 팩트 문장들을 개행으로 이어붙인 문자열.
             매칭 결과가 없으면 안내 문자열 반환.
    """
    facts: list[str] = []

    driver = await get_neo4j_driver()
    
    async def _fetch_records(tx):
        _res = await tx.run(_CYPHER_QUERY, keyword=normalize_concept(keyword))
        return await _res.data()

    async with driver.session(database=NEO4J_DATABASE) as session:
        # execute_read는 커넥션 끊김 등 Transient Error 발생 시 자동 재시도를 수행합니다.
        records = await session.execute_read(_fetch_records)

    for record in records:
        subject = record["Subject"]
        action  = record["Action"]
        reason  = record.get("Reason")
        obj     = record["Object"]
        action_en = ACTION_EN_MAP.get(action, "is related to")
        
        fact_str = f"- {subject} {action_en} {obj}."
        if reason:
            fact_str += f" (Reason: {reason})"
        facts.append(fact_str)

    if not facts:
        return f"No relationship data found for '{keyword}' in the knowledge graph."

    return "\n".join(facts)


async def retrieve_knowledge_graph(concept: str) -> str:
    """
    llm_agent.py 의 retrieve_knowledge_graph 와 동일한 시그니처로
    기존 코드를 그대로 교체할 수 있는 어댑터 함수입니다.

    concept: 영문 또는 한글 개념명
    Returns: LLM 프롬프트에 삽입용 문자열
    """
    try:
        facts_text = await get_economic_facts(concept)
        return (
            f"[Knowledge Graph Context for '{concept}']\n"
            f"{facts_text}"
        )
    except Exception as e:
        # Graceful fallback on Neo4j connection failure
        print(f"[KnowledgeGraph] ⚠️ Neo4j Query Failed (keyword={concept}): {e}", flush=True)
        return f"Error retrieving knowledge graph: {str(e)}"
