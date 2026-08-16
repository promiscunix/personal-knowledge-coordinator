-- Initial PostgreSQL direction for Personal Knowledge Coordinator.
-- This is not yet applied to the host. It records the production schema shape
-- corresponding to the tested SQLite prototype.

CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS raw_captures (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    raw_text text NOT NULL,
    source_type text NOT NULL,
    source_ref text,
    source_vault text,
    captured_at timestamptz NOT NULL DEFAULT now(),
    captured_by text NOT NULL,
    privacy_scope text NOT NULL,
    verified boolean NOT NULL DEFAULT false,
    confidence double precision NOT NULL DEFAULT 1.0
);

CREATE TABLE IF NOT EXISTS projects (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    slug text NOT NULL UNIQUE,
    name text NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS people (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    display_name text NOT NULL,
    normalized_name text NOT NULL UNIQUE,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS observations (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    summary text NOT NULL,
    kind text NOT NULL,
    privacy_scope text NOT NULL,
    project_id uuid REFERENCES projects(id),
    source_capture_id uuid NOT NULL REFERENCES raw_captures(id),
    confidence double precision NOT NULL,
    verified boolean NOT NULL DEFAULT false,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS conversations (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    person_id uuid NOT NULL REFERENCES people(id),
    issue text NOT NULL,
    attributed_explanation text,
    privacy_scope text NOT NULL,
    source_capture_id uuid NOT NULL REFERENCES raw_captures(id),
    occurred_at timestamptz NOT NULL DEFAULT now(),
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS commitments (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    person_id uuid REFERENCES people(id),
    summary text NOT NULL,
    status text NOT NULL,
    privacy_scope text NOT NULL,
    source_capture_id uuid NOT NULL REFERENCES raw_captures(id),
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS tasks (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    title text NOT NULL,
    description text NOT NULL,
    status text NOT NULL,
    privacy_scope text NOT NULL,
    project_id uuid REFERENCES projects(id),
    source_capture_id uuid NOT NULL REFERENCES raw_captures(id),
    assigned_agent text,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS activity_events (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_type text NOT NULL,
    entity_id uuid NOT NULL,
    event_type text NOT NULL,
    message text NOT NULL,
    actor text NOT NULL,
    occurred_at timestamptz NOT NULL DEFAULT now(),
    metadata_json jsonb NOT NULL DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS idx_raw_captures_scope ON raw_captures(privacy_scope);
CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
CREATE INDEX IF NOT EXISTS idx_tasks_scope ON tasks(privacy_scope);
CREATE INDEX IF NOT EXISTS idx_activity_entity ON activity_events(entity_type, entity_id);
