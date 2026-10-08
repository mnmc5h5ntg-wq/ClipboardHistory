# Domain Docs

How the engineering skills should consume this repo's domain documentation when exploring the codebase.

## Layout

This is a single-context repo. The primary domain context is the macOS clipboard history app, including clipboard monitoring, history presentation, previews, menu bar behavior, global shortcuts, packaging, and release workflow.

## Before exploring, read these

- `CONTEXT.md` at the repo root, if it exists
- `docs/adr/`, if it exists, for architecture decisions that touch the area being changed

If these files do not exist, proceed silently. Do not flag their absence or suggest creating them upfront. The producer skill (`grill-with-docs`) can create or update them when project terms or architectural decisions are actually resolved.

## Expected structure

```text
/
|-- CONTEXT.md
|-- docs/
|   `-- adr/
|       |-- 0001-example-decision.md
|       `-- 0002-example-decision.md
`-- ClipboardHistory/
```

## Use the glossary's vocabulary

When output names a domain concept, use the terms defined in `CONTEXT.md`. If the concept is not in the glossary yet, either use the term already present in code or README, or note it as a possible gap for `grill-with-docs`.

## Flag ADR conflicts

If output contradicts an existing ADR, surface it explicitly instead of silently overriding it.
