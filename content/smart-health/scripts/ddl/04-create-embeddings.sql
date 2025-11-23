-- ##################################################
-- #          PGVECTOR INSTALLATION SCRIPT          #
-- ##################################################
-- This script installs and configures the pgvector extension for PostgreSQL.
-- pgvector enables vector similarity search capabilities needed for:
-- - Semantic search on medical records
-- - LLM embeddings storage and retrieval
-- - AI-powered query matching
-- Target DBMS: PostgreSQL with pgvector support

-- ##################################################
-- #         EXTENSION INSTALLATION                 #
-- ##################################################

-- Install pgvector extension
-- Note: This requires that pgvector is already installed in your PostgreSQL instance
-- Installation instructions: https://github.com/pgvector/pgvector or https://www.youtube.com/watch?v=xvRwwAF_-X4
CREATE EXTENSION IF NOT EXISTS vector;

-- Verify extension is installed
--SELECT * FROM pg_extension WHERE extname = 'vector';

-- ##################################################z
-- #    EMBEDDINGS FOR USER-FOCUSED LLM QUERIES    #
-- ##################################################

BEGIN;

-- 1. ESENCIAL: Historial de conversaciones de usuarios
-- Permite búsqueda semántica de preguntas similares previas
ALTER TABLE smart_health.audit_logs 
ADD COLUMN IF NOT EXISTS question_embedding vector(1536);

COMMENT ON COLUMN smart_health.audit_logs.question_embedding 
IS 'Vector embedding de la pregunta del usuario para búsqueda de conversaciones similares (OpenAI text-embedding-ada-002, 1536 dims)';

-- Índice IVFFlat para búsqueda rápida de similitud coseno
CREATE INDEX IF NOT EXISTS idx_audit_logs_question_embedding 
ON smart_health.audit_logs 
USING ivfflat (question_embedding vector_cosine_ops)
WITH (lists = 100);

COMMENT ON INDEX smart_health.idx_audit_logs_question_embedding 
IS 'Índice IVFFlat para búsqueda rápida de similitud coseno en preguntas de usuarios';

-- 2. IMPORTANTE: Búsqueda semántica en historias clínicas
-- Permite buscar síntomas, tratamientos y condiciones similares
ALTER TABLE smart_health.medical_records 
ADD COLUMN IF NOT EXISTS summary_embedding vector(1536);

COMMENT ON COLUMN smart_health.medical_records.summary_embedding 
IS 'Vector embedding del resumen médico para búsqueda semántica de síntomas, tratamientos y condiciones similares (OpenAI text-embedding-ada-002, 1536 dims)';

-- Índice IVFFlat para búsqueda rápida de similitud coseno
CREATE INDEX IF NOT EXISTS idx_medical_records_summary_embedding 
ON smart_health.medical_records 
USING ivfflat (summary_embedding vector_cosine_ops)
WITH (lists = 100);

COMMENT ON INDEX smart_health.idx_medical_records_summary_embedding 
IS 'Índice IVFFlat para búsqueda rápida de similitud coseno en resúmenes médicos';

COMMIT;

-- ##################################################
-- #         FUNCIONES DE UTILIDAD                  #
-- ##################################################

-- Función para buscar preguntas similares en audit_logs
--CREATE OR REPLACE FUNCTION smart_health.find_similar_questions(
--    query_embedding vector(1536),
--    similarity_threshold float DEFAULT 0.8,
--    max_results int DEFAULT 5
--)
--RETURNS TABLE (
--    audit_log_id INTEGER,
--    user_id INTEGER,
--    question TEXT,
--    response_json JSONB,
--   similarity_score FLOAT,
--    created_at TIMESTAMP
--) AS $func$
--BEGIN
--    RETURN QUERY
--    SELECT 
--        al.audit_log_id,
--        al.user_id,
--        al.question,
--        al.response_json,
--        1 - (al.question_embedding <=> query_embedding) as similarity_score,
--        al.created_at
--    FROM smart_health.audit_logs al
--    WHERE al.question_embedding IS NOT NULL
--    ORDER BY al.question_embedding <=> query_embedding
--    LIMIT max_results;
--END;
--$func$ LANGUAGE plpgsql;

--COMMENT ON FUNCTION smart_health.find_similar_questions IS 
--'Busca preguntas similares en el historial de audit_logs usando similitud coseno. 
--Parámetros: query_embedding (vector a buscar), similarity_threshold (umbral mínimo), max_results (máximo de resultados)';

-- Función para buscar registros médicos similares
--CREATE OR REPLACE FUNCTION smart_health.find_similar_medical_records(
--    query_embedding vector(1536),
--    patient_id_filter INTEGER DEFAULT NULL,
--    max_results int DEFAULT 10
--)
--RETURNS TABLE (
--    medical_record_id INTEGER,
--    patient_id INTEGER,
--    doctor_id INTEGER,
--    summary_text TEXT,
--    similarity_score FLOAT,
--    registration_datetime TIMESTAMP
--) AS $func$
--BEGIN
--    RETURN QUERY
--    SELECT 
--        mr.medical_record_id,
--       mr.patient_id,
--        mr.doctor_id,
--        mr.summary_text,
--        1 - (mr.summary_embedding <=> query_embedding) as similarity_score,
--        mr.registration_datetime
--    FROM smart_health.medical_records mr
--    WHERE mr.summary_embedding IS NOT NULL
--      AND (patient_id_filter IS NULL OR mr.patient_id = patient_id_filter)
--    ORDER BY mr.summary_embedding <=> query_embedding
--   LIMIT max_results;
--END;
--$func$ LANGUAGE plpgsql;

--COMMENT ON FUNCTION smart_health.find_similar_medical_records IS 
--'Busca registros médicos similares usando similitud coseno.
--Parámetros: query_embedding (vector a buscar), patient_id_filter (opcional, filtrar por paciente), max_results (máximo de resultados)';

-- ##################################################
-- #                 END OF SCRIPT                  #
-- ##################################################