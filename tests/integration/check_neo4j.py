"""Run against a dedicated disposable Neo4j instance, never production."""
import asyncio
import os
import sys
import time
from pathlib import Path
from neo4j import GraphDatabase

root = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(root), str(root / 'back')]
from scripts.seed_neo4j import load_relations, seed

with GraphDatabase.driver(os.environ['NEO4J_URI'], auth=(os.getenv('NEO4J_USER','neo4j'),os.environ['NEO4J_PASSWORD'])) as driver:
    for attempt in range(60):
        try:
            driver.verify_connectivity()
            break
        except Exception:
            if attempt==59: raise
            time.sleep(1)
    rows=load_relations(root/'neo4j/seed/relation_data.csv')
    seed(driver,rows)
    seed(driver,rows)
    with driver.session() as session:
        count=session.run('MATCH (:EconomicConcept)-[r]->(:EconomicConcept) RETURN count(r) AS n').single()['n']
        assert count==len(rows), (count,len(rows))
    from services.knowledge_graph import get_economic_facts, get_neo4j_driver
    async def query():
        result=await get_economic_facts('인플레이션')
        assert 'consumer price index' in result
        await (await get_neo4j_driver()).close()
    asyncio.run(query())
print('Neo4j alias query and idempotent seed passed')
