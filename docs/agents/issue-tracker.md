# Issue tracker: Local Markdown

> 现状（本轮实测）：`.scratch/` 目前是空目录，真正的 issue 追踪在 GitHub（`gh issue list`，当前 open 的是 #5、#13、#16）。下面的约定描述的是**草稿怎么起草**，不是说那些文件已经存在。

Issues, PRDs, bugs, and development ideas for this repo live as markdown files in `.scratch/` while the project is in active development. Formal bugs and release-ready development ideas can be copied or rewritten into GitHub Issues during release preparation.

## Conventions

- One feature or workstream per directory: `.scratch/<feature-slug>/`
- The PRD is `.scratch/<feature-slug>/PRD.md`
- Implementation issues are `.scratch/<feature-slug>/issues/<NN>-<slug>.md`, numbered from `01`
- Triage state is recorded as a `Status:` line near the top of each issue file; see `triage-labels.md` for the allowed status strings
- Comments and conversation history append to the bottom of the file under a `## Comments` heading

## When a skill says "publish to the issue tracker"

Create a new markdown file under `.scratch/<feature-slug>/`, creating the directory if needed. Do not create a GitHub Issue unless the user explicitly asks to promote or publish release-ready work to GitHub.

## When a skill says "fetch the relevant ticket"

Read the referenced markdown file. The user will normally pass the path, feature slug, or issue number directly.

## Release preparation

Before a release, review the relevant `.scratch/` files and decide which bugs, feature ideas, or PRDs should become GitHub Issues for public tracking.
