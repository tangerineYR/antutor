-- Disposable transaction: no real learner rows touched, no persistent ANN index.
\set ON_ERROR_STOP on
BEGIN;
CREATE TEMP TABLE cache_benchmark (
    namespace text PRIMARY KEY,
    embedding vector(384) NOT NULL
) ON COMMIT DROP;
INSERT INTO cache_benchmark
SELECT md5(i::text), array_fill(0.1::real, ARRAY[384])::vector FROM generate_series(1,10000) i;
ANALYZE cache_benchmark;
EXPLAIN (ANALYZE, BUFFERS)
SELECT 1 - (embedding <=> array_fill(0.1::real,ARRAY[384])::vector) AS similarity
FROM cache_benchmark WHERE namespace=md5('5000')
AND 1 - (embedding <=> array_fill(0.1::real,ARRAY[384])::vector) >= 0.98;
ROLLBACK;
