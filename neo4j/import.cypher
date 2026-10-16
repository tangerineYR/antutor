// Copy neo4j/seed/relation_data.csv into the server import directory first.
// Input must be the canonical CSV committed in this repository.
CREATE CONSTRAINT economic_concept_name IF NOT EXISTS
FOR (n:EconomicConcept) REQUIRE n.name IS UNIQUE;

LOAD CSV WITH HEADERS FROM 'file:///relation_data.csv' AS row
WITH row WHERE row.relationship IN ['CAUSES','RELATED_TO','PART_OF','CONTRASTS_WITH','REQUIRES']
MERGE (a:EconomicConcept {name: row.source})
MERGE (b:EconomicConcept {name: row.target})
FOREACH (_ IN CASE WHEN row.relationship='CAUSES' THEN [1] ELSE [] END |
  MERGE (a)-[r:CAUSES]->(b) SET r.reason=row.reason)
FOREACH (_ IN CASE WHEN row.relationship='RELATED_TO' THEN [1] ELSE [] END |
  MERGE (a)-[r:RELATED_TO]->(b) SET r.reason=row.reason)
FOREACH (_ IN CASE WHEN row.relationship='PART_OF' THEN [1] ELSE [] END |
  MERGE (a)-[r:PART_OF]->(b) SET r.reason=row.reason)
FOREACH (_ IN CASE WHEN row.relationship='CONTRASTS_WITH' THEN [1] ELSE [] END |
  MERGE (a)-[r:CONTRASTS_WITH]->(b) SET r.reason=row.reason)
FOREACH (_ IN CASE WHEN row.relationship='REQUIRES' THEN [1] ELSE [] END |
  MERGE (a)-[r:REQUIRES]->(b) SET r.reason=row.reason);
