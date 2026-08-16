# Install on the new knowledge computer

This repo is meant to be pulled onto a fresh/new NixOS machine and used as its system configuration.

It is not an update to the development/reference machine.

## 1. Install base NixOS

Boot the NixOS installer and install a minimal system normally. Use whatever disk layout is appropriate for the new computer. Labeling the root filesystem `nixos` matches the placeholder config, but the recommended path is to replace `hardware-configuration.nix` with the generated one before switching.

## 2. Pull this repo

```bash
sudo -i
nix-shell -p git
cd /etc
mv nixos nixos.before-pkc.$(date +%Y%m%d%H%M%S) || true
git clone <THIS_REPO_URL> nixos
cd /etc/nixos
```

## 3. Generate hardware config for the target machine

```bash
sudo nixos-generate-config --show-hardware-config > nixos/hosts/knowledge-node/hardware-configuration.nix
```

Review the generated file if the target machine has unusual disks, encryption, bootloader needs, or filesystems.

## 4. Add secrets outside Git

Do not commit API keys or bot tokens. Use sops/age later; for first boot you can create a root-owned EnvironmentFile:

```bash
sudo install -d -m 0750 /run/secrets
sudoedit /run/secrets/hermes-env
sudo chmod 0600 /run/secrets/hermes-env
```

Then uncomment/set this in `nixos/hosts/knowledge-node/configuration.nix`:

```nix
services.personal-knowledge-coordinator.secretsFile = /run/secrets/hermes-env;
```

## 5. Check and switch

```bash
nix flake check
sudo nixos-rebuild switch --flake .#knowledge-node
```

## 6. Smoke test

```bash
systemctl status postgresql --no-pager
systemctl status pkc-api --no-pager
systemctl status hermes-agent --no-pager
pkc capture "I don't like the UI for the Parts Advisor page in part-suite."
pkc inbox
curl -s http://127.0.0.1:8765/health
```

Expected result: the capture is preserved, a part-suite task is created, and the task appears in the inbox.

## Current limitations

This is the first pullable implementation. It gives you a real NixOS stack, PostgreSQL, a capture API, Hermes coordinator service, role accounts, and backups. The remaining work is to deepen the app logic: full semantic retrieval, reminders, Kanban sync, dashboard, and non-destructive Obsidian migration.
