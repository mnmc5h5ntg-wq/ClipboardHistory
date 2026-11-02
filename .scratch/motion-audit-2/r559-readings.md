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

## 待读（截断的链要重跑）
- ~~四把刀~~ **已到手**：M1450 / M1451 / M1452 / M1453 **全 CAUGHT、RESTORE_CLEAN=yes**（`/tmp/r559-knife-*.log`）。
  - M1450（图例退回四块）：`light 格色=8 图例色=4 缺=[(243,243,243)]`、`dark 格色=9 图例色=4 缺=[(41,41,41)]` ⇒ 与"旧值"逐字相同（这一把同时复现了缺陷形状）。
  - M1451（数量不动、颜色换成 `accentColor.opacity(VisualHeat.empty)`）：`图例色=5 缺=[(243,243,243)]` ⇒ 判据看的是**颜色身份**，不是方块个数。
  - M1452（摘 `.id(title)`）：`钉子=grep 钉住=2/3`、红名 `缺 1 根：.id(title)`。
  - M1453（删掉具名不判那行 emit）：红在交叉核对那句。
- ~~兄弟判据~~ **已到手**（判据卷整卷读数，`/tmp/r559-capture.log`）：
  - `HEAT_LEGEND_COVERAGE light 格色=8 图例色=5 缺=[] 格宽=22px 网格下缘 y=333 实心判定 格13px/图例5px`；dark `格色=9 图例色=5 缺=[]`（同格宽）。
  - `HEATMAP_TODAY light/dark 差异像素=60 bbox=1108,408-1115,415 倍率=2.0x 内容墨=47615/33627` ⇒ **与 ⓪ 列的旧值逐字未变**。
  - `HEATMAP_SUMMARY_CHANGE light 变化=3872 前墨=3696 后墨=3780 前右沿=481 后右沿=494`、`dark 变化=4165 前墨=4151 后墨=4239 前右沿=481 后右沿=494` ⇒ **未变**（右沿 494 未动 = 宽度中性的第二条独立证据）。
  - `CAPTION_INK … 图例「少 / 多」 light ratio=3.85 参照=3.75 比值=1.03 ink=10.2%`（旧 14.1%）、`dark ratio=6.06 参照=6.06 比值=1.00 ink=11.9%`（旧 15.4%）⇒ **只有 `ink=` 跳档，对比度与比值一字未动**；地板 `probeInkFraction=3%` 未动，余量 3.4×/4.0×。
    成因（逐像素定位，不是猜）：探针框 `x12..37pt / y176..190pt`（=px 24..74 / 352..380）里，旧帧有 **46 个 (215,232,255)**（最浅那档蓝被挪走）、新帧同一位置 **49 个 (243,243,243)**（新补的零次档），页底 `(255,255,255)` 两边都 **1167 个** ⇒ 换进去的填充更接近页面 ⇒ 覆盖率降；`ratio` 读的是「少」/「多」两枚字（128,128,128 vs 255）所以不变。
- ~~看图~~ **已到手**：两张帧按像素对切（旧 `/tmp/r558-frames2/…`、新 `/tmp/r559-frames/…`）：
  light 与 dark **各自 1172 像素变化、bbox 完全相同** `x 70…157 / y 360…375`（2x）= `pt x35.0…78.5 / y180.0…187.5` ⇒ 只有图例那一行变了。
  放大并排看图 `/tmp/r559-legend-oldvsnew.png`（上旧下新，3× 最近邻）：旧 `少 [淡蓝 蓝 中蓝 深蓝] 多`、新 `少 [灰 淡蓝 蓝 中蓝 深蓝] 多`；`多` 与后面那句「最忙的…」两行同一位置。
- 判据卷 `UICaptureTests` 汇总行（整卷 Executed/failed/skipped）—— 链上仍在跑。
- 帧基线 `compare` + `update`（heatmap-populated 两档必然变 ⇒ 与台账同一笔 update）。
- 全量卷（有界 grep；顺带再看 skipped 57 这一格稳不稳，**不许修回 55**）。
- 预检三读（`mutate_needle_precheck` / `hidden_arms` / `ARM_TOTAL`）⇒ **必须串行**。
- 换装本机（`scripts/install_local.sh --yes --label R559`，撞名就 R559b）。
- 台账 7 本 → 提交 → **再** `report_sources_cell.py --write` → 电池 → **一次性 push**。
- ⓪ 那跑 `41485625452 ↔ 8115ab8`：**收口前复述仍是 in_progress（已等 1663s）** ⇒ 新口径 runner 读数 + 634 复核两格具名 NOT-RUN，挂进 R560 ⓪（`queue 共=10 queued=0 in_progress=1 concluded=9`）。

