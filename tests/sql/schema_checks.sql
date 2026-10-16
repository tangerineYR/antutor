\set ON_ERROR_STOP on
BEGIN;
DO $$
DECLARE role_name text; t text; f record;
BEGIN
    FOREACH role_name IN ARRAY ARRAY['anon','authenticated'] LOOP
        FOREACH t IN ARRAY ARRAY['users','concepts','sessions','chat_logs','user_attendance','questions',
            'quiz_attempts','quiz_answers','semantic_cache','security_logs'] LOOP
            IF has_table_privilege(role_name, 'public.' || t, 'SELECT,INSERT,UPDATE,DELETE') THEN
                RAISE EXCEPTION 'Unexpected table privileges for % on %', role_name,t;
            END IF;
            IF NOT (SELECT relrowsecurity FROM pg_class WHERE oid=('public.'||t)::regclass) THEN
                RAISE EXCEPTION 'Missing RLS: %',t;
            END IF;
        END LOOP;
        FOR f IN SELECT oid FROM pg_proc WHERE proname IN ('match_semantic_cache','match_semantic_cache_v2') LOOP
            IF has_function_privilege(role_name,f.oid,'EXECUTE') THEN
                RAISE EXCEPTION 'Unexpected function privilege for %',role_name;
            END IF;
        END LOOP;
    END LOOP;
END $$;
SET LOCAL ROLE service_role;
INSERT INTO users(user_id,username,password_hash) VALUES ('00000000-0000-0000-0000-000000000001','testuser','test-hash');
INSERT INTO concepts(concept_id,name,definition) VALUES (1001,'test inflation','Prices rise');
INSERT INTO sessions(session_id,user_id,concept_id) VALUES (1001,'00000000-0000-0000-0000-000000000001',1001);
INSERT INTO questions(question_id,concept_id,question_text,option_1,option_2,option_3,option_4,option_5,correct_option)
VALUES (1001,1001,'test','a','b','c','d','e',1);
INSERT INTO quiz_attempts(attempt_id,session_id,user_id,quiz_type,total_score)
VALUES (1001,1001,'00000000-0000-0000-0000-000000000001','PRE',0);
INSERT INTO quiz_answers(attempt_id,question_id,selected_option,confidence_level,is_correct,earned_score)
VALUES (1001,1001,6,0,false,0);
DO $$ BEGIN
    BEGIN
        UPDATE quiz_answers SET confidence_level=3 WHERE attempt_id=1001;
        RAISE EXCEPTION 'Invalid uncertainty accepted';
    EXCEPTION WHEN check_violation THEN NULL; END;
    BEGIN
        UPDATE quiz_answers SET earned_score=-6 WHERE attempt_id=1001;
        RAISE EXCEPTION 'Uncertainty penalty accepted';
    EXCEPTION WHEN check_violation THEN NULL; END;
END $$;
INSERT INTO security_logs(user_id,threat_type,transport)
VALUES ('00000000-0000-0000-0000-000000000001','prompt_injection','rest');
INSERT INTO semantic_cache(concept,last_question,namespace,user_answer,cached_response,embedding)
VALUES ('test','why',repeat('a',64),'answer','feedback',array_fill(0.1::real,ARRAY[384])::vector);
DO $$
DECLARE hits integer; v vector := array_fill(0.1::real,ARRAY[384])::vector;
BEGIN
    SELECT count(*) INTO hits FROM match_semantic_cache_v2('test','why',repeat('a',64),v,0.98,1,true);
    IF hits <> 1 THEN RAISE EXCEPTION 'Expected cache hit'; END IF;
    SELECT count(*) INTO hits FROM match_semantic_cache_v2('test','why',repeat('b',64),v,0.98,1,true);
    IF hits <> 0 THEN RAISE EXCEPTION 'Cross-namespace leak'; END IF;
    PERFORM * FROM match_semantic_cache_v2('test','why',repeat('a',64),v,0.98,1,false);
    IF (SELECT hit_count FROM semantic_cache WHERE namespace=repeat('a',64)) <> 1 THEN
        RAISE EXCEPTION 'Hit counter incorrect'; END IF;
    UPDATE semantic_cache SET created_at=now()-interval '25 hours' WHERE namespace=repeat('a',64);
    SELECT count(*) INTO hits FROM match_semantic_cache_v2('test','why',repeat('a',64),v,0.98,1,true);
    IF hits <> 0 THEN RAISE EXCEPTION 'Expired cache hit'; END IF;
END $$;
-- Concept deletion must cascade through sessions, chats and assessments.
INSERT INTO chat_logs(session_id,turn_number,user_message,ai_response) VALUES (1001,1,'test','test');
DELETE FROM concepts WHERE concept_id=1001;
DO $$ BEGIN
    IF EXISTS (SELECT 1 FROM sessions WHERE session_id=1001)
       OR EXISTS (SELECT 1 FROM chat_logs WHERE session_id=1001)
       OR EXISTS (SELECT 1 FROM quiz_attempts WHERE session_id=1001)
       OR EXISTS (SELECT 1 FROM questions WHERE question_id=1001)
       OR EXISTS (SELECT 1 FROM quiz_answers WHERE attempt_id=1001) THEN
        RAISE EXCEPTION 'Concept cascade failed';
    END IF;
END $$;
RESET ROLE;
SET LOCAL ROLE anon;
DO $$ BEGIN
    BEGIN
        PERFORM * FROM public.questions;
        RAISE EXCEPTION 'anon could read answers';
    EXCEPTION WHEN insufficient_privilege THEN NULL; END;
    BEGIN
        PERFORM * FROM public.match_semantic_cache_v2('test','why',repeat('a',64),array_fill(0.1::real,ARRAY[384])::vector);
        RAISE EXCEPTION 'anon could execute cache RPC';
    EXCEPTION WHEN insufficient_privilege THEN NULL; END;
END $$;
ROLLBACK;
