# R559 自存工作笔记（不是第七本账；收口时抄进 `ledgers_r559.py`）

第 558 轮 / Round 556 · 2026-11-03。顺序规矩：**已到手**只写真的读到的东西，
被切断/超时/没跑的统统进**待读**，旧日志一律不算。

## 已到手

### ⓪ CI（R559 开场那两格，现读）
- `41485625452 ↔ 8115ab8`（R558 补记笔）取号时 **queued** ⇒ 「新口径在 runner 上读几」与
  「634 复核」两格**本轮具名 NOT-RUN**（不是"没红"）。
- `41469418563 ↔ 2f85c5d`（R558 ⓪ 笔）**success**，已签 STEP[9] 转绿。
- `41467585182 ↔ ff15906`：红在 STEP[18]（622 第十三值 225.3ms / 3 颗）+ STEP[19]（旧口径 1）。

### 第四格 · 产品位 = 热图图例（**先写判据、量到旧值红，再改产品**）
- 新判据 `UICaptureTests/testHeatmapLegendCoversEveryCellColor`（`UICaptureHarness.swift`）：
  渲染 `heatmap-populated` 两档外观，网格行 = 一整行里 ≥20 段宽 ≥8px 的实心 run；
  `cellW` = run 宽中位数；实心方块判定 = 边长 `cellSolid=max(4, cellW*3/5)` 的正方形内全部同色（容差 6）。
- **旧值（红，2 failures）**：`light 格色=8 图例色=4 缺=[(243,243,243)]`、
  `dark 格色=9 图例色=4 缺=[(41,41,41)]`
  ⇒ 网格真的画了 8/9 种实心色，图例带里只有 4 种；零次档那一灰（243/41）**查不到**。
  日志：`/tmp/r559-crit-old.log`（现存，2207 字节）；新值那份 `/tmp/r559-crit-new.log`。
- **新值（绿）**：`图例色=5 缺=[]`（light/dark 两臂）。
- 产品改动 `Sources/ClipboardHistoryApp/Views/DailyCopyHeatmapView.swift` `footer`：
  图例补一块 `Color.primary.opacity(VisualHeat.empty)`，并把 5 块方块包进
  `HStack(spacing: 4)`。宽度算式（`VisualHeat.cell = 11` ⇒ 方块 8pt）：
  旧 `4×8 + 3×8 = 56` → 新 `5×8 + 4×4 = 56`，**总宽一字未动** ——
  页脚那句悬停详情实测已顶到 x≈494/860px（2x），加宽会把它挤成省略号，
  那是拿一个可见性问题换另一个。
- `swift build --build-tests` 告警 **0**。

### 635 · 两条腿（一条会红的钉子 + 一句具名的不判）
- 钉子 `MotionFilmstripTests/testMarkdownModeLabelWiringIsPinnedBecauseTheFilmCannotSeeIt`：
  在 `Views/DetailView.swift` 的 `struct MarkdownModeButton` 体内 grep 三行接线，
  现读 `MOTION_WIRING_UNJUDGED markdown-mode-label 钉子=grep 钉住=3/3`。
  - 踩过的两个坑（都红过才知道）：
    1. 第一版拿 `testSource(named:"DetailView.swift")` 读 ⇒ 那是 **Tests/** 目录，
       `productSource` 走 **Sources/ClipboardHistoryApp/**；报的是"守卫找不到被守卫的东西时必须红"，
       这条失败形状是对的，改成 `productSource(named:"Views/DetailView.swift")` 才绿。
    2. 交叉核对第一版在**整份自己源码**里找 `MOTION_NOT_RUN=markdown-wiring-unjudged`
       ⇒ 会在**守卫自己那行字面量**里读到它（R53/R55 那一族自满足），
       改成只在 `testMarkdownModeLabelChangeIsAVisibleProcess` 的函数体里找（`region(in:codeOnly(…))`）。
- 具名不判：胶片那一格现读
  `MOTION_NOT_RUN=markdown-wiring-unjudged markdown-mode-label：本格只判标签有没有中间态…`
- 两格同跑：`Executed 2 tests, with 0 failures`（`CLIPBOARD_HISTORY_UI_MOTION=1`，2.619s）。

### 629 的新口径（本轮又跑了一次胶片，现读）
`MOTION_MARKDOWN_MODE_FADE scale=1x 帧数=27 过渡帧数=5 相邻差帧数=4 首末连续差=0.0031 峰值=0.0097
声明=200ms 窗口=327ms 每格=12.6ms 相邻帧差=[0.0000,0.0097,0.0097,0.0048,0.0048,0.0000×7]
离前=[0.0003,0.0013,0.0018,0.0021,0.0024,0.0026,0.0028,0.0029,0.0030,0.0030,0.0030,0.0030]
离后=[0.0029,0.0021,0.0015,0.0011,0.0007,0.0005,0.0003,0.0002,0.0001,0.0001,0.0000,0.0000]
唯一变化区=行 25…34 列 69…89（10×21px，帧 160×60）`
⇒ 与 R558 那一次同形（`过渡帧数=5 相邻差帧数=4`、离前单调升 / 离后单调降）；
`峰值` 这次 0.0097（R558 是 0.0145）= 采样相位差，不是新东西。

### 看图三次证伪（照实写，不当缺陷）
1. 热图"那颗点落在网格外" ⇒ 量到的坐标其实在网格内（旧的一次看图把页脚当网格）。
2. "周四那一格是空的" ⇒ 合成 today=2026-03-12 就是周四，那一格有值。
3. "图例的蓝和网格的蓝不一样" ⇒ 逐色比过，四档蓝**完全相同**；真正缺的是**零次档那一灰**
   ⇒ 证伪 3 的剩余部分就是本轮的产品位（不是新缺陷，是把当年那条看图结论收干净）。

## 待读（截断的链要重跑）
- 四把刀 `M1450–M1453` 的 verdict + `RESTORE_CLEAN`（`/tmp/r559-knife-*.log`）。
- 兄弟捕获判据的旧→新（产品页脚动过，必须重读）：
  `HEATMAP_TODAY`、`HEATMAP_SUMMARY_CHANGE`、图例 `INK heatmap-populated/图例「少 / 多」`。
- 判据卷 `UICaptureTests` 汇总行（整卷）。
- 帧基线对账：`heatmap-populated` 帧**一定变** ⇒ 只有真 CHANGED 名单确认后才 `update`，且与台账同一笔。
- 全量卷（有界 grep；顺带再看 skipped 57 这一格稳不稳，**不许修回 55**）。
- 预检三读（`mutate_needle_precheck` / `hidden_arms` / `ARM_TOTAL`）⇒ **必须串行**，
  和 swift 卷并行会撞锁假报 `NOT_RUN_TIMEOUT`。
- 换装本机（`--label R559`，撞名就 R559b）。
- 台账 7 本 → 提交 → **再** `report_sources_cell.py --write` → 电池 → **一次性 push**。
- ⓪ 那跑 `41485625452 ↔ 8115ab8` 若已开跑：新口径 `过渡帧数=` 的 runner 真数 + STEP[9] 还红不红。
