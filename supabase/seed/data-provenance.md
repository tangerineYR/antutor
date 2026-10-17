# Concept seed provenance

Two user-supplied exports contain the same field values, with different column
ordering. Each has 50 CSV rows: 30 concepts and 20 entirely empty rows. The
canonical `concepts.csv` removes only empty rows and reorders columns. Original
IDs (1–30), category, definitions, dictionary content, acceptable extensions,
key terms and defense prompts are retained. Prompt fields are application data,
not instructions for repository automation.

Source checksums (SHA-256):
- `concepts_data csv 36528346333c8033aaebc8875d46e857_all.csv`: `35a50b7940d447233e71448a9fd9d91543c3355d7c2deeb1716c78353c67719e`
- `concepts_data csv 36528346333c8033aaebc8875d46e857.csv`: `94060ee4d717669af27ffe711dfdc09d712ea78d487fed5b62a4202252b75654`

`python scripts/generate_concept_seed.py` regenerates `concepts.sql`. Apply that
file to a fresh migrated database before optional example seeds. It preserves
existing records and rejects ID/name collisions instead of silently remapping
foreign keys. Reruns do not overwrite edited definitions. No learner/account data
is included. The identity sequence is advanced beyond imported IDs.

Neo4j includes `recession`, a relationship-only node absent from the supplied
concept catalog. No definition or concept ID was invented for that node.
The graph alias `gross domestic product (gdp)` maps to catalog name
`gross domestic product`.

Source completeness: 12 records have empty definitions (IDs: 9, 12, 13, 15, 16, 21, 22, 25, 27, 28, 29, 30).
12 records contain placeholder dictionary text. These supplied gaps are
preserved rather than filled with invented content; curate them before using those
concepts for assessed tutoring. Canonical CSV uses LF line endings.
