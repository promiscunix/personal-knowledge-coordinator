# Instructions for Coding Agents

## Scope

Work only in the coordinator-owned clone:

```text
/srv/personal-knowledge-coordinator/workspace/personal-knowledge-coordinator
```

Do not edit `/etc/nixos` directly. Do not modify live services, PostgreSQL schema/data, firewall/DNS, credentials, or public exposure unless Dale explicitly approves the specific action.

## Data plane versus control plane

- **Data plane:** Telegram → Hermes → PKC API → PostgreSQL/raw archive. Everyday thoughts, quotes, recipes, notes, tasks, and observations belong here, not in Git.
- **Control plane:** this Git clone contains PKC code, schema migrations, CLI/API, dashboard, docs, and NixOS configuration.

Never require a Git commit/push merely to save a knowledge record.

## Development workflow

1. Inspect the existing code and current branch before proposing replacements.
2. Work on a named branch; keep changes narrow and reversible.
3. Write or update tests before implementation where practical.
4. Run the relevant tests/checks and report actual output.
5. Show the diff and explain the design trade-offs.
6. Do not commit, push, rebuild, restart, or apply a live migration without explicit approval.

## Database rules

- Preserve raw captures and provenance for derived records.
- Use additive, ordered migrations; never rely on request-time schema mutation for production evolution.
- Test migrations against a disposable PostgreSQL instance before proposing live application.
- Never put secrets in migrations, test fixtures, source, Git history, or docs.

## Product rules

- Prefer the smallest system that solves the demonstrated operational problem.
- Avoid enterprise architecture without evidence that it is needed.
- Preserve production continuity.
- Keep dealership-facing Part-Suite language practical: “received report” and “received history,” not RRH/CDK RRH unless internal terminology is appropriate.
