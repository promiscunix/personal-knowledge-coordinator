# Database Design

Production target: PostgreSQL.

Prototype target: repository-local SQLite for tests and demo only. The schema in `src/pkc/app.py` is intentionally simple; `sql/postgresql/001_initial.sql` is the intended direction for production migrations.

## Core principles

- Preserve raw source material.
- Every derived record points back to a raw capture/source.
- Store opinion/observation as attributed observation, not verified fact.
- Use deterministic queries for deterministic questions.
- Add embeddings/pgvector only where semantic retrieval is useful.
- Scope records so unrelated agents do not see private material.

## Initial conceptual tables

- `raw_captures`
- `projects`
- `people`
- `observations`
- `conversations`
- `commitments`
- `tasks`
- `activity_events`

Planned next tables:

- `sources`
- `source_files`
- `record_links`
- `reminders`
- `calendar_events`
- `decisions`
- `references`
- `articles`
- `books`
- `quotes`
- `recipes`
- `research_reports`
- `daily_summaries`, `weekly_summaries`, `monthly_summaries`
- `embeddings` or per-record embedding columns via pgvector, only after initial retrieval needs are proven

## Task states

The system-level task states requested by the user are:

- captured
- classified
- queued
- working
- blocked
- waiting_on_user
- ready_for_review
- approved
- done
- cancelled
- archived

Hermes Kanban has its own operational states (`triage`, `todo`, `ready`, `running`, `blocked`, `review`, `done`, `archived`). A mapping table or enum adapter will preserve the user's semantic task state while syncing to Hermes Kanban for execution.
