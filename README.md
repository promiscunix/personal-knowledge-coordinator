# Personal Knowledge Coordinator

A central personal knowledge, task, and multi-agent coordination system built around Hermes Agent.

Guiding principle:

> Capture everything. Organize automatically. Retrieve by meaning. Delegate work when appropriate. Preserve original context. Surface results later.

This repository is the first working skeleton. It intentionally starts with a small vertical slice rather than a giant speculative system.

## Scope

This repository is for building a new configuration for a different computer. The current NixOS machine is being inspected as a reference source only. Do not treat this as permission to update the current machine's `/home/damajha/nixfiles` configuration or live Hermes service.

The target-machine flake entry is:

```bash
sudo nixos-rebuild switch --flake .#knowledge-node
```

Read `INSTALL.md` before first use so the target machine's generated `hardware-configuration.nix` replaces the placeholder.

## Current status

Implemented prototype slice:

- Raw captures preserve original wording.
- A coordinator classifier recognizes the Parts Advisor / part-suite UI example.
- The system creates a project-scoped observation and persistent task.
- The task appears in an inbox view.
- Assignment and creation activity are stored durably.
- A management-private Tom callbacks conversation path is covered in tests to prove scope separation is part of the schema from the start.

The target-machine configuration enables PostgreSQL, a local `pkc-api` capture service, the `pkc` CLI, the official Hermes Agent NixOS module, role accounts for the specialist agents, and nightly PostgreSQL backups. Local tests still use SQLite where useful because they are fast and disposable.

## Quick demo

```bash
nix run .#pkc -- --db data/knowledge.sqlite3 init-db
nix run .#pkc -- --db data/knowledge.sqlite3 capture "I don't like the UI for the Parts Advisor page in part-suite."
nix run .#pkc -- --db data/knowledge.sqlite3 inbox
```

## Test

```bash
nix develop --command python -m pytest -q
nix flake check
nix build .#nixosConfigurations.knowledge-node.config.system.build.toplevel --no-link --print-out-paths
```

## Non-goals for the initial slice

- No Obsidian vault migration yet.
- No production deployment yet.
- No destructive rewrite of existing Hermes state.
- No reliance on the LLM context window as memory.
