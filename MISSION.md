# Knowledge Node PA Mission

> Build PKC into Dale’s single safe, useful PA: instant live capture into Postgres/raw archive; reviewed Git-based development for system changes; one shared brain across projects, machines, quotes, recipes, sources, tasks, and approvals.

This repository builds Dale's central personal knowledge coordinator on `knowledge-node`.

The coordinator is not a generic chatbot. It helps Dale think, investigate, build, remember, organize, and finish work across NixOS/home-lab systems, Part-Suite product work, source notes, projects/tasks, quotes and life lessons, recipes/kitchen experiments, dealership training content, and future dashboard/PWA workflows.

## Architecture

```text
Data plane:
Telegram → Hermes → PKC API → PostgreSQL + raw archive

Control plane:
workspace Git clone → branch → tests → diff → approval → commit/push → root pulls/rebuilds
```

- PostgreSQL/PKC is the durable structured source of truth for knowledge, notes, captures, tasks, projects, and observations.
- The raw archive preserves original evidence such as transcripts and imported source material.
- Obsidian is a human-readable mirror and import/export layer, not the sole source of truth.
- Hermes memory is a compact index of durable preferences and operating facts; chat history is context, not gospel.
- Git is for changing PKC code, schema, CLI/API, dashboard, documentation, and NixOS configuration—not everyday knowledge capture.

The system should turn useful information into context, decisions, experiments, actions, or clearly indexed references; it should not become another passive inbox.