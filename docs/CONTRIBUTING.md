# Contributing

## Branching

Short-lived feature branches into `main`. Examples: `feature/auth-registration`, `fix/tenant-isolation`, `docs/deployment-guide`, `chore/ci-linting`.

## Commits

Conventional style:

```
feat(auth): add registration endpoint
fix(workspaces): enforce tenant membership checks
docs(readme): add local setup instructions
chore(ci): run frontend lint and backend tests
```

## Safety

- Never commit `.env`, secrets, dumps, or real customer data
- Commit migrations with the model changes that require them
- Keep PRs focused; do not force-push `main`
