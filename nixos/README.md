# NixOS target-machine configuration

This directory is the pull-and-implement NixOS configuration for the new knowledge coordinator computer.

It intentionally does **not** modify the reference machine used during development.

## Fast path on the new computer

```bash
sudo -i
nix-shell -p git
cd /etc
mv nixos nixos.before-pkc.$(date +%Y%m%d%H%M%S) || true
git clone <THIS_REPO_URL> nixos
cd /etc/nixos
sudo nixos-generate-config --show-hardware-config > nixos/hosts/knowledge-node/hardware-configuration.nix
nix flake check
sudo nixos-rebuild switch --flake .#knowledge-node
```

After switch:

```bash
systemctl status postgresql
systemctl status pkc-api
systemctl status hermes-agent
pkc capture "I don't like the UI for the Parts Advisor page in part-suite."
pkc inbox
```

## Secrets

Do not commit secrets. Put Hermes/API credentials into a target-machine secret file and set:

```nix
services.personal-knowledge-coordinator.secretsFile = /run/secrets/hermes-env;
```

The file should be an EnvironmentFile containing values such as provider API keys and messaging gateway tokens.

## What this enables

- PostgreSQL-backed knowledge database.
- Local coordinator capture API on `127.0.0.1:8765`.
- `pkc` CLI on PATH.
- Hermes Agent gateway configured as the coordinator.
- Role accounts/directories for coordinator, librarian, researcher, developer, reviewer.
- Nightly PostgreSQL backups under `/srv/personal-knowledge-coordinator/backups/postgresql`.
