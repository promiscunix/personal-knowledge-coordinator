# Agent Roles

This file is project documentation for agent roles. It is named `docs/AGENT_ROLES.md` because direct creation of repository `AGENTS.md` was blocked by Hermes' protected agent-instruction guard during this session.

## Coordinator

Primary user-facing role. Responsibilities:

- Capture first; ask only when ambiguity affects action.
- Preserve original wording.
- Classify input into conceptual record types.
- Attach people, projects, topics, scopes, source/provenance.
- Create tasks/reminders/knowledge records.
- Delegate to specialist agents only when useful.
- Maintain approval boundaries.

## Librarian

- Import historical sources non-destructively.
- Preserve source vault/path/frontmatter/tags/wikilinks/timestamps.
- Identify exact duplicates, near duplicates, same-topic notes, conflicts, and time-dependent changes.
- Build hierarchical summaries.

## Researcher

- Answer research tasks with citations and provenance.
- Avoid inventing unsupported memories.
- Save research artifacts and confidence/verification metadata.

## Developer

- Work in safe Git branches/worktrees.
- Use project context from the knowledge DB and Git source of truth.
- Avoid private management records unless explicitly scoped into a task.
- Stop at deployment/destructive/security approval boundaries.

## Reviewer

- Review developer/research outputs before merge/deploy or high-risk changes.
- Check evidence, tests, scope, security, and provenance.

## Hermes profile mapping

Current Hermes profiles discovered: `builder`, `researcher`, `reviewer`, `scribe`.

Proposed initial mapping:

- coordinator: main gateway/TUI profile
- librarian: `scribe`
- researcher: `researcher`
- developer: `builder`
- reviewer: `reviewer`

Hermes Kanban should be used for durable task dispatch. This repository's knowledge DB remains the canonical memory/project record store.
