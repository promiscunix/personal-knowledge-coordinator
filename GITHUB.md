# GitHub publishing

The intended remote repository name is:

```text
personal-knowledge-coordinator
```

Recommended visibility: private, because this is personal infrastructure and may later include topology, paths, and operational details.

When GitHub auth is available:

```bash
gh repo create personal-knowledge-coordinator --private --source . --push \
  --description "NixOS/Hermes personal knowledge, task, and multi-agent coordinator"
```

If `gh` is unavailable but a token is available, create the repository through the GitHub API and push `main`.
