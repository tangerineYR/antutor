# Graph seed provenance

Source: user-uploaded `relation_data.csv` (80 rows, UTF-8).
SHA-256 of the supplied bytes: `d76ef7b46ce3f7850e2628a85bfeb74dd1d8c0c38a4381261314e4ad4f2d7cf2`.

Canonical output: `seed/relation_data.csv`, 69 relationships over 32 concepts.
Identifiers use Unicode NFKC, lowercase, normalized whitespace and explicit aliases.
`RELATED_TO` and `CONTRASTS_WITH` are symmetric and use sorted endpoints.
Other types preserve supplied direction; no causal direction was inferred from prose.
Repeated edges with identical reasons collapse. The two descriptions of the
stagflation/unemployment relationship are both retained, joined by ` | `.
Reason text remains in its original language. This is deduplication, not independent
verification or correction of the economic claims in the source.

Use `scripts/seed_neo4j.py` for parameterized ingestion, or copy the canonical CSV
into Neo4j's import directory and run `import.cypher` with cypher-shell. Both paths
use the same allowlisted relationship types, uniqueness constraint and MERGE keys.
Import into a dedicated/new graph; neither importer deletes unrelated existing data.
