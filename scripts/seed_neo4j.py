"""Idempotently load the normalized user-supplied graph."""
import csv
import os
import sys
from pathlib import Path
from neo4j import GraphDatabase

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "back"))
from services.concept_normalization import normalize_concept

ALLOWED_RELATIONS = {"CAUSES", "RELATED_TO", "PART_OF", "CONTRASTS_WITH", "REQUIRES"}

def load_relations(path):
    rows = {}
    with open(path, encoding="utf-8", newline="") as stream:
        for row in csv.DictReader(stream):
            source, target = normalize_concept(row["source"]), normalize_concept(row["target"])
            relation = row["relationship"].strip().upper()
            if not source or not target or relation not in ALLOWED_RELATIONS:
                raise ValueError("Invalid relation row")
            if relation in {"RELATED_TO", "CONTRASTS_WITH"}:
                source, target = sorted((source, target))
            key = (source, relation, target)
            reason = row["reason"].strip()
            if key in rows and rows[key] != reason:
                raise ValueError("Conflicting reasons for duplicate relation")
            rows[key] = reason
    return rows

def seed(driver, rows, database="neo4j"):
    with driver.session(database=database) as session:
        session.run("CREATE CONSTRAINT economic_concept_name IF NOT EXISTS FOR (n:EconomicConcept) REQUIRE n.name IS UNIQUE").consume()
        def write(tx):
            for (source, relation, target), reason in rows.items():
                # Relationship type is strictly allowlisted; values are parameters.
                if relation not in ALLOWED_RELATIONS:
                    raise ValueError("Invalid relation type")
                tx.run(f"MERGE (a:EconomicConcept {{name: $source}}) "
                       f"MERGE (b:EconomicConcept {{name: $target}}) "
                       f"MERGE (a)-[r:{relation}]->(b) SET r.reason=$reason",
                       source=source, target=target, reason=reason).consume()
        session.execute_write(write)

if __name__ == "__main__":
    source = Path(sys.argv[1]) if len(sys.argv)>1 else Path(__file__).resolve().parents[1]/"neo4j/seed/relation_data.csv"
    rows = load_relations(source)
    with GraphDatabase.driver(os.environ["NEO4J_URI"], auth=(os.getenv("NEO4J_USER","neo4j"), os.environ["NEO4J_PASSWORD"])) as driver:
        seed(driver, rows, os.getenv("NEO4J_DATABASE","neo4j"))
    print(f"Seeded {len(rows)} unique relations")
