# Active Projects

This is a concise coordination index. Detailed records, source material, decisions, and activity belong in PKC/PostgreSQL and the raw archive.

## Knowledge Node / Personal Knowledge Coordinator

**Status:** Active foundation build.

**Purpose:** Build a durable central PA/coordinator on `knowledge-node`, with Hermes as the working layer and PKC/PostgreSQL plus raw archives as the knowledge data plane.

**Current verified state:**

- Hermes gateway and Telegram are working.
- PKC API health endpoint is working locally.
- The coordinator-owned PKC clone is at `/srv/personal-knowledge-coordinator/workspace/personal-knowledge-coordinator`.
- GitHub SSH authentication for the coordinator is working.
- `/etc/nixos` is the root-owned live configuration and is not edited from this repository without approval.

**Near-term work:**

1. Establish durable operating documentation and current project index.
2. Add a migration runner before further production schema changes.
3. Add first-class quote/life-lesson capture to PKC with source provenance, CLI/API, and tests.
4. Create PKC modules for project/task packets, source ingestion, recipes/experiments, and dashboard/PWA workflows.
5. Import useful context from prior Hermes/theBullpen and Part-Suite work without creating duplicate knowledge.

## Part-Suite Reconcile

**Status:** Top paid MVP.

**Purpose:** Dealership received-versus-billed recovery queue.

**External language:** use “received report” and “received history.”

**Internal language:** RRH / CDK RRH. Do not expose internal jargon unnecessarily in dealership-facing material.

## Knowledge modules to develop

- **Quotes/life lessons:** exact wording, source/attribution confidence, meaning to Dale, professional/training use, relationships, and Quote-of-the-Day eligibility.
- **Recipes/kitchen experiments:** living records of what was used, what was actually done, results, who liked it, freezer/work-lunch notes, changes, and current best version.
- **Dealership training content:** practical, explainable, reusable materials for parts-advisor development.
