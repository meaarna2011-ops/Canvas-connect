
BEGIN;

-- Inspect the records targeted for removal.
SELECT COUNT(*) AS generated_count
FROM public.opportunities
WHERE source_name = 'CanvasConnect Aggregator';

-- Inspect the current schema and constraints before proceeding.
SELECT column_name, data_type, udt_name
FROM information_schema.columns
WHERE table_schema = 'public'
  AND table_name = 'opportunities'
ORDER BY ordinal_position;

-- SAFETY STOP:
-- Do not delete records until the replacement INSERT statements
-- have been generated, reviewed, and tested against this schema.
-- Roll back this inspection-only transaction.
ROLLBACK;
