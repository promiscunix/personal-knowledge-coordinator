# Security

Security is a design constraint, not a later feature.

## Scopes

Initial scopes:

- `personal`
- `work`
- `management-private`
- `project:<project-slug>`
- `agent:<agent-name>`
- `general/shared`

Management/private staff conversations must not be exposed to developer/research/recipe agents by default.

## Production enforcement plan

- PostgreSQL roles per agent class where practical.
- Row-level security policies based on `privacy_scope`.
- Separate OS users for strongly isolated specialists if the operational value outweighs complexity.
- Read-only or scope-limited database credentials for specialists.
- Auditable `activity_events` for derived records, task status changes, delegation, and human approval boundaries.
- Secrets only in service environment files or age/sops-managed material, never Markdown, Git, or exported notes.
- Production deploys, destructive migrations, deletion, private employee record changes, and major security changes require human approval.

## Current prototype limitation

The SQLite prototype stores `privacy_scope` and tests management-private classification, but it does not enforce OS/database-level isolation. Do not treat it as a production security boundary.
