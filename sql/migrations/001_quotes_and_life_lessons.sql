CREATE TABLE quotes (
    id uuid PRIMARY KEY,
    exact_text text NOT NULL CHECK (btrim(exact_text) <> ''),
    speaker text,
    source_label text,
    source_locator text,
    attribution_confidence smallint NOT NULL DEFAULT 50 CHECK (attribution_confidence BETWEEN 0 AND 100),
    attribution_status text NOT NULL DEFAULT 'unknown' CHECK (attribution_status IN ('verified', 'likely', 'unknown', 'misattributed_warning', 'personal')),
    privacy_scope text NOT NULL,
    source_capture_id uuid NOT NULL REFERENCES raw_captures(id),
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE life_lessons (
    id uuid PRIMARY KEY,
    lesson_text text NOT NULL CHECK (btrim(lesson_text) <> ''),
    privacy_scope text NOT NULL,
    source_capture_id uuid NOT NULL REFERENCES raw_captures(id),
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX idx_quotes_created_at ON quotes (created_at DESC);
CREATE INDEX idx_quotes_speaker ON quotes (speaker);
CREATE INDEX idx_life_lessons_created_at ON life_lessons (created_at DESC);
