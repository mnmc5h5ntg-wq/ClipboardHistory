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

### Definition of done（第三轮审计 C-1 / C-5 定的硬规矩）

两条规矩，都是"上一轮真栽过跟头"之后写下来的，不是风格偏好：

1. **修复的验收测试必须从产品入口进入** —— `HistoryStore`、`ClipboardIntake`、设置/视图实际消费的字段，
   不许只调内部纯函数就宣称修好了。理由：第二轮 N-1 的守卫测试绕过 adapter 直调 engine，
   于是"几百条断言全绿、产品照崩"；第三轮 D-7 的在屏探针在 CI 一次也没跑过，同一族。
   只测纯函数的文件要在开头显式写 `// 不覆盖管线：…` 并指出管线级判据在哪
   （见 `EntryDragPlannerTests`、`FilterPillMotionTests`、`RowInteractionTests`）。
   管线级样本见 `PipelineAcceptanceTests`（三条：采集→降采样→入库、来源归因→菜单标签、暂停→采集入口）。
2. **`HistoryStore` 只减不加**：不拆类（500 条上限下拆是过度工程），但新特性一律先建
   `*Policy` / `*Planner` 纯函数，Store 里只留薄胶水。这条由一条会红的守卫钉住
   （`testHistoryStoreAverageFunctionLengthDoesNotGrow`：行数 ÷ 顶层方法数，上限只准降不准升）。
