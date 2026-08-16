# Personal Knowledge Coordinator

A central personal knowledge, task, and multi-agent coordination system built around Hermes Agent.

Guiding principle:

> Capture everything. Organize automatically. Retrieve by meaning. Delegate work when appropriate. Preserve original context. Surface results later.

This repository is the first working skeleton. It intentionally starts with a small vertical slice rather than a giant speculative system.

## Current status

Implemented prototype slice:

- Raw captures preserve original wording.
- A coordinator classifier recognizes the Parts Advisor / part-suite UI example.
- The system creates a project-scoped observation and persistent task.
- The task appears in an inbox view.
- Assignment and creation activity are stored durably.
- A management-private Tom callbacks conversation path is covered in tests to prove scope separation is part of the schema from the start.

The current runnable prototype uses a repository-local SQLite adapter for fast tests and demos. The documented production target is PostgreSQL with row-level/security-aware scopes; see `DATABASE.md` and `SECURITY.md`.

## Quick demo

```bash
nix develop
python -m pkc.cli --db data/knowledge.sqlite3 init-db
python -m pkc.cli --db data/knowledge.sqlite3 capture "I don't like the UI for the Parts Advisor page in part-suite."
python -m pkc.cli --db data/knowledge.sqlite3 inbox
```

## Test

```bash
nix develop --command python -m pytest -q
```

## Non-goals for the initial slice

- No Obsidian vault migration yet.
- No production deployment yet.
- No destructive rewrite of existing Hermes state.
- No reliance on the LLM context window as memory.
