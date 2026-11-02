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

### 新判据的 1x 体检（一次性探针，**不入库 ⇒ 不能当证人**）
把本轮 2x 帧最近邻降到 1x，用同一套判定复算：
- `2x light 格色=8 图例色=5 缺=[]`（格宽 22px、实心 格13/图例5）
- `1x light 格色=5 图例色=2 缺=[(39,132,255),(180,210,255),(130,180,255)]` ⇒ **假红**
- `2x dark 格色=9 图例色=5 缺=[]` / `1x dark 格色=5 图例色=1 缺=[4 种]`
命中分布：`2x 图例 [31,29,27,27,27 | 3,2,2]`、`1x 图例 [9,9,7,7,6 | 1]`
⇒ 一个方块能放下的采样点从 2x 的 36 掉到 1x 的 9（步长 2、方块 8px − 实心边 3px ⇒ 3 个位置），
绝对地板 `minHits=8` 在 1x 上必然把五档读到两档。
**处置**：加 `倍率 < 1.5 ⇒ emit HEAT_LEGEND_NOT_RUN=scale-too-low + continue`（同族先例
`SETTINGS_HELPER_FONT_NOT_RUN=scale-too-low`、`SETTINGS_FOOTER_BAND_NOT_RUN=runner-1x-band-geometry`），
并给正常读数补 `倍率=`；**没有**拿降采样代理去改 `minHits`（那是用假 1x 帧钉真参数）。
改完复跑：`swift build --build-tests` 0 告警、判据仍绿 `图例色=5 缺=[] 倍率=2.0x`（两档外观）。
⇒ 图例覆盖这件事**今天没有 runner 读数**，R560 若要在 1x 判：真 1x 帧 + `minHits` 改几何派生。

## 收口时补：全部到手（本轮没有留 NOT-RUN 的自读格）
- 判据卷 `UICaptureTests`：**218/4 skipped/0 失败（670.8s）**（R558 是 217/4/0 ⇒ +1 = 本轮那条图例判据）。
- 帧：`FRAME_BASELINE_COMPARED=354 CHANGED=10 MISSING=0 ADDED=0`，十个名字 = `heatmap-populated`、
  `heatmap-summary-before/after`、`settings-stats-populated`、`settings-stats-populated-no-today` × 两档外观 ⇒ **全是含热图的夹具**；
  `update` 之后复跑 `CHANGED=0`。
- 全量：**1402/57/0（699.0s）**，退出码 0 ⇒ skipped 57 连两跑稳定（只记现读，不动门）。
- 预检三读（串行）：`NEEDLE_PRECHECK tables=353 covered=295 arms=757 bad=0`、
  `ARM_TOTAL files=446 arms=1244 dupes=0 repeats=0`、`HIDDEN_ARMS 表=440 可判=1183 rot=0 抽不出=6 已声明表=6 处置=ok`。
- 换装：`INSTALL_RESULT=ok / INSTALL_SHA_MATCH=1 / INSTALL_ENTRIES=433=433 / SMOKE_OK=1 / INSTALL_SIGNATURE=local flags=0x0`
  （版本 1.4.8→1.4.8、PID→24131、备份 `before-R559`）。
- 清账 **162/63/0**；streak 现读 `PRODUCT_STREAK ledger_round=558 streak=2 …`（⚠ `--streak-for 559` 读 1，
  因为它按 subject 把本轮 A 笔归进 558 轮 ⇒ 口径差一仍挂 BACKLOG 412；账里用门派生的 2）。
- **⓪ 那跑到手了**：`41485625452 ↔ 8115ab8` = **concluded success**（收口前复述，不是轮询）⇒
  新口径 runner 首数 `过渡帧数=2 相邻差帧数=2 首末连续差=0.0048 峰值=0.0193 窗口=1860ms 每格=71.5ms`
  ⇒ **判到 ≥2 但余量 0**，且每格比 R557 那三跑粗 2.5–3 倍 ⇒ 629 不写结案；
  STEP[9] `SKIP_ROSTER … 内层Ran=696 名单外=无 名册未跳=无` ⇒ **634 被 runner 签掉**；
  STEP[19] `MOTION_FLOOR_OK=4/5 MOTION_FLOOR_REDS=0` ⇒ 旧口径那朵红在含新尺的这一跑不见了；STEP[18] success ⇒ 622 无新值。
- **电池四遍（本轮最重要的自伤记录）**：① 台账前 `Ran 696 / FAILED (failures=2, skipped=5)`
  （sources 格未派生 + `test_skip_roster` 以 634 的 `inner-red` 形状红，正文带内层汇总与内层红名 ⇒ 634 第一次在真场景说话）；
  ② 台账后第一遍**涨到** `failures=6, errors=1` ⇒ 多出来的四朵全是本轮写账自造的：
  **七维表只写六行（漏「可复核性」）**、**CHANGELOG 写成 bullet 而不是 `### …（R559 / ` 标题行**、
  **streak 抄了 `--streak-for` 的 1 而门派生是 2**、**那一格还没引用 `scripts/product_streak.py`**；
  ③ 修完剩 streak 两格；④ **`Ran 696 / OK (skipped=5)` 退出码 0**。全程没放宽门、没加豁免、没改期望。
  ⇒ 教训：**R558 刚为「基线也现读」记过一次，同一族在 streak 那一格又发生**（换个字段就忘了"派生值要带取数口"）。
- 提交序列（一次性 push 之前全在本地）：⓪ `809b963` → A `3a3c9a9` → A2 `bad7788` → 台账 `73e91f4` → 更正 `2f26d4c` → 补记（本笔）。
