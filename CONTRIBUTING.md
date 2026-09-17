# Contributing

## Sequential delivery

Start from current `main` and keep one pull request open at a time. Branches use
`task/<name>` or `feat/<name>`. Commit subjects and pull request titles use the
matching `task: ...` or `feat: ...` prefix.

Before requesting review, run every check relevant to the change, inspect the
diff for secrets and generated artifacts, and update documentation and tests
with behavior. Merge only after required checks pass and blocking review is
resolved. Use squash merge and delete the feature branch.

## Security boundary

Never add reviewer-only challenge material, model credentials, raw solve
workspaces, or generated candidate patches to the repository.
