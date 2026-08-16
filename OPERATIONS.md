# Target-machine operations

## Daily use

Capture from CLI:

```bash
pkc capture "I should make sauerkraut this weekend."
pkc inbox
```

Capture through the local API:

```bash
curl -s -X POST http://127.0.0.1:8765/capture \
  -H 'Content-Type: application/json' \
  -d '{"text":"I don'"'"'t like the UI for the Parts Advisor page in part-suite."}'
```

## Service checks

```bash
systemctl status pkc-api --no-pager
systemctl status hermes-agent --no-pager
systemctl status postgresql --no-pager
journalctl -u pkc-api -n 100 --no-pager
```

## Database

```bash
sudo -u pkc psql pkc
```

Useful first checks:

```sql
select captured_at, privacy_scope, raw_text from raw_captures order by captured_at desc limit 10;
select status, title, assigned_agent from tasks order by created_at desc limit 10;
```

## Backups

NixOS `services.postgresqlBackup` writes nightly database dumps to:

```text
/srv/personal-knowledge-coordinator/backups/postgresql
```

Raw archive/export backup directories are reserved at:

```text
/srv/personal-knowledge-coordinator/archive
/srv/personal-knowledge-coordinator/exports
/srv/personal-knowledge-coordinator/backups
```

## Hermes

The Hermes coordinator service uses:

```text
/srv/personal-knowledge-coordinator/hermes
```

Role home directories are created under:

```text
/srv/personal-knowledge-coordinator/agents/{coordinator,librarian,researcher,developer,reviewer}
```

## Approval boundaries

Do not automate these without explicit user approval:

- production deploys
- destructive database migrations
- deletion of important/private data
- changes affecting private employee records
- major auth/security changes
