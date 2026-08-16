# Architecture

## Scope clarification

This project is **not** an in-place update to the currently inspected machine's NixOS configuration. The current machine is a reference/inspection host only. The deliverable is a new, clean configuration for a different computer, following the user's detailed guidelines for a centralized Hermes-based personal knowledge, task, and multi-agent coordination system.

Do not modify `/home/damajha/nixfiles` or the current host's live NixOS/Hermes service as part of this repository unless the user explicitly authorizes that later. Machine inspection findings are used to understand existing Hermes state, migration sources, and design constraints.

## Inspection summary from the reference host

Reference host inspected: `theBullpen`, NixOS 26.11, flakes enabled, current working repo `/home/damajha/nixfiles`.

Hermes Agent:

- Installed declaratively through the upstream Hermes NixOS module from flake input `github:NousResearch/hermes-agent`.
- Version: Hermes Agent v0.20.1 (2026-08-13), install method `nixos`.
- Gateway service: `hermes-agent.service`, active/running.
- Service user/group: `gibbs:gibbs`.
- State dir: `/var/lib/hermes`.
- Hermes home: `/var/lib/hermes/.hermes`.
- Working directory: `/var/lib/hermes/workspace`.
- Existing profiles reported by `hermes doctor`: `builder`, `researcher`, `reviewer`, `scribe`.
- Hermes native durable coordination exists through Kanban, backed by SQLite boards and gateway dispatch. This should be reused for agent work queues instead of rebuilding transient in-process subagents.
- Hermes A2A and delegation toolsets are available; Kanban is the better fit for durable cross-agent work.

Current caveats:

- `hermes doctor` reports config version `0 -> 37`; migration via `hermes doctor --fix` is available but was not run in this pass.
- Hermes `state.db` is large (~2.5 GB); pruning/optimization should be planned but not mixed into this project bootstrap.
- PostgreSQL service is currently inactive.
- The existing Nix repo already had unrelated dirty files before this project started (`flake.lock`, `modules/systemLevel/bullpen-workbench/default.nix`, `modules/systemLevel/hermes/default.nix`). This new project was created in a separate Git repository to avoid mixing changes.

## Target system

One coordinator-facing system with specialist agents behind it:

- `coordinator`: captures user input, classifies, routes, asks only when ambiguity matters.
- `librarian`: imports/organizes source material, handles deduplication and summaries.
- `researcher`: performs bounded research and records cited outputs.
- `developer`: works on software tasks in safe branches/worktrees.
- `reviewer`: reviews generated work before risky changes or merge/deploy.

## Data flow

```text
Natural user input
  -> raw capture, verbatim, with source/provenance/scope
  -> deterministic + LLM-assisted classification
  -> structured records: tasks, observations, people, projects, commitments, etc.
  -> activity/history events
  -> optional Hermes Kanban task for specialist work
  -> summaries and retrieval layers
```

The model context window is not the database. Agents retrieve only context required for the current job.

## Storage layers

1. Raw capture: original wording, files, transcripts, imported vault records.
2. Working context: bounded task-specific retrieval.
3. Agent memory: small durable operating notes and role constraints.
4. Long-term structured knowledge: PostgreSQL records.
5. Raw archive: untouched Markdown/PDF/transcript/file sources.

## Initial implementation choice

The production target remains PostgreSQL on the new target computer. The first prototype uses a simple SQLite adapter only to prove the vertical slice and test behavior before writing the target-machine PostgreSQL/NixOS configuration. This avoids accidentally changing services on the reference host.

## Hermes integration plan

- Use Hermes Kanban for durable multi-agent work queues where tasks survive restarts and can be assigned to named profiles.
- Keep the knowledge database separate from transient Hermes conversation memory.
- Store Hermes task IDs/activity references in the knowledge DB when a capture delegates work.
- Use existing Hermes profiles initially (`builder`, `researcher`, `reviewer`, `scribe`) and later map them to canonical roles or create isolated OS/database users where useful.
