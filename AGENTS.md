## Agent skills

### Issue tracker

Issues and PRDs are drafted as local markdown files under `.scratch/` (currently empty) and promoted to
GitHub Issues, which is where the live tracker actually is (`gh issue list`). See `docs/agents/issue-tracker.md`.

### Triage labels

The repo uses the default mattpocock/skills triage labels: `needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, and `wontfix`. See `docs/agents/triage-labels.md`.

### Domain docs

This is a single-context repo: use `CONTEXT.md` at the repo root and `docs/adr/` for architecture decisions when they exist. See `docs/agents/domain.md`.

### Third-party agent assets

`.agents/skills/` and `skills-lock.json` are agent-side tooling pinned into this repo. They are not part of
the app: nothing under them is compiled, bundled, or shipped, and the product's build (`make bundle`/`make dmg`)
never reads them. Treat them as third-party code with its own upstream — do not import their conventions into
`Sources/` or assume they are reviewed like product code.
