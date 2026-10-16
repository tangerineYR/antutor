-- FastAPI authenticates custom JWTs and enforces ownership. Browsers must never
-- access these tables/RPCs directly. Backend requires Supabase service_role.
DO $$
DECLARE table_name text; seq_name text; proc record;
BEGIN
    FOREACH table_name IN ARRAY ARRAY['users','concepts','sessions','chat_logs','user_attendance',
        'questions','quiz_attempts','quiz_answers','semantic_cache','security_logs'] LOOP
        EXECUTE format('ALTER TABLE public.%I ENABLE ROW LEVEL SECURITY', table_name);
        EXECUTE format('REVOKE ALL ON TABLE public.%I FROM PUBLIC, anon, authenticated', table_name);
        EXECUTE format('GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE public.%I TO service_role', table_name);
        FOR seq_name IN SELECT pg_get_serial_sequence('public.' || table_name, a.attname)
            FROM pg_attribute a WHERE a.attrelid = ('public.' || table_name)::regclass
            AND a.attnum > 0 AND NOT a.attisdropped LOOP
            IF seq_name IS NOT NULL THEN
                EXECUTE format('REVOKE ALL ON SEQUENCE %s FROM PUBLIC, anon, authenticated', seq_name);
                EXECUTE format('GRANT USAGE, SELECT ON SEQUENCE %s TO service_role', seq_name);
            END IF;
        END LOOP;
    END LOOP;
    -- Includes every overload present on an existing installation.
    FOR proc IN SELECT p.oid::regprocedure AS signature FROM pg_proc p
        JOIN pg_namespace n ON n.oid = p.pronamespace
        WHERE n.nspname = 'public' AND p.proname IN ('match_semantic_cache', 'match_semantic_cache_v2') LOOP
        EXECUTE format('REVOKE ALL ON FUNCTION %s FROM PUBLIC, anon, authenticated', proc.signature);
        EXECUTE format('GRANT EXECUTE ON FUNCTION %s TO service_role', proc.signature);
    END LOOP;
END $$;
GRANT USAGE ON SCHEMA public TO service_role;
ALTER DEFAULT PRIVILEGES IN SCHEMA public REVOKE ALL ON TABLES FROM PUBLIC, anon, authenticated;
ALTER DEFAULT PRIVILEGES IN SCHEMA public REVOKE ALL ON SEQUENCES FROM PUBLIC, anon, authenticated;
ALTER DEFAULT PRIVILEGES IN SCHEMA public REVOKE EXECUTE ON FUNCTIONS FROM PUBLIC, anon, authenticated;
