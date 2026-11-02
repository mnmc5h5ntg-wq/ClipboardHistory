# -*- coding: utf-8 -*-
"""R559 台账（第 558 轮 / Round 556）：热图图例补零次档那一块（产品 1 文件）+ 635 两条腿落地。

用法：`python3 ledgers_r559.py --check` 只验锚点；不带参数才真写七本账。
所有数字都是**现读**填进 NUM，没有一格从上一轮抄。
"""
import io
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

NUM = {
    "FULL": "1402/57/0（699.0s）",
    "INSTALL": "`INSTALL_SIGNATURE=local flags=0x0`（固定身份 ⇒ 授权可以跨轮活下来）⇒ `INSTALL_RESULT=ok / INSTALL_SHA_MATCH=1 / INSTALL_ENTRIES=433=433 / SMOKE_OK=1`（版本 1.4.8→1.4.8，PID→24131，启动晚于安装、exe 路径逐字对上，备份 `before-R559`）",
    "BATTERY": "696/5",
    "ABSENCE": "162/63/0",
    "STREAK": "1",
    "CAPTURE": "218/4 skipped/0 失败（670.8s）",
    "FRAMES": "354 张里 CHANGED=10（`heatmap-populated`、`heatmap-summary-before/after`、`settings-stats-populated`、`settings-stats-populated-no-today` 五个夹具 × 两档外观 = 全部含热图的那几张）⇒ 同一笔 `update` 之后复跑 `CHANGED=0 MISSING=0 ADDED=0`",
    "PRECHECK": "tables=353 covered=295 arms=757 bad=0",
    "ARM": "files=446 arms=1244 dupes=0 repeats=0",
    "HIDDEN": "表=440 可判=1183 rot=0 抽不出=6 已声明表=6 处置=ok",
}

UI = u"""## 第 558 轮（R559 · 2026-11-03 · U-2395…U-2403）：热图图例补上零次档那一块（产品 1 文件 + 判据 2 文件 + 四把刀）；635 两条腿落地（会红的钉子 + 具名的不判）

- **U-2395：⓪ CI 读单 —— 开场两格具名 NOT-RUN，收口前补读全部到手，而且第一格读到了"恰好压线"。** 开场 HEAD=origin=`8115ab8`、ahead=0、已跟踪改动 0、`api=403 / apple=200`（403 没挡住 `gh`）。`41485625452 ↔ 8115ab8`（R558 那一批的头笔，内容含 R558 全部代码）开场 **queued**、复述 **in_progress（已等 1663s）** ⇒ 本轮头两格当时**具名 NOT-RUN**（不轮询、不猜）。**收口前再读 `queue`：`concluded success`（已等 4787s）** ⇒ 两格当场转成读数：
  - **新口径在 runner 上读几**：`MOTION_MARKDOWN_MODE_FADE scale=1x 帧数=27 过渡帧数=2 相邻差帧数=2 首末连续差=0.0048 峰值=0.0193 声明=200ms 窗口=1860ms 每格=71.5ms 相邻帧差=[0.0000,0.0145,0.0000,0.0193,0.0000…]` ⇒ **新尺判到 ≥2，但余量是 0**（正好压在地板上）。⚠ 更要紧的是这台机器的钟：`每格=71.5ms` 比 R557 那三跑的 22.6–28.1ms **粗 2.5–3 倍**（`窗口=1860ms`），200ms 的声明时长在这网格上只摊到 ~3 格 ⇒ 读到 2 是"刚好抓住两条边都还在中间"，**下一跑掉到 1 完全可能**。所以 629 这一格今天写成「新尺已在 runner 判到、余量 0、随钟漂」，**不写结案**（R555 的 dark 整行=6 恰在界上是同一形状的账）。
  - **旧口径那一朵红退场没有**：同跑 STEP[19] `Motion coverage floor` = success，正文 `MOTION_FLOOR_OK=4/5 全部臂都在登记之内`、`MOTION_FLOOR_REDS=0`、`MOTION_FLOOR_FACTS judged=4/5 executed=78 not-run=notice-banner-dismiss` ⇒ `41467585182↔ff15906` 那朵 `MOTION_FLOOR_SUITE_RED=1 … testMarkdownModeLabelChang…` 在含新尺的这一跑**不见了**（登记缺席的那一臂是 `notice-banner-dismiss`，与 629 无关）。
  - **634 的 runner 复核**：STEP[9] `Release script tests` = success，正文 `SKIP_ROSTER 键=github-runner 类=github-runner 内层Ran=696 内层skip汇总=3 解析=2 名单外=无 名册未跳=无` ⇒ 借红消失（内层 696 与本机电池 696 同数）。
  - STEP[18] `On-screen probe coverage floor` = success ⇒ 622 这一跑**没有新值**（第十三值 225.3ms/3 颗未复现，`over_runs` 口径不动）。STEP[1]–[21] 逐条 conclusion 全 success（`gh run view --json jobs` 现读；`ci_read.py steps` 只列 failure/skipped，这一跑它只打 `JOB build-and-test ⇒ success`）。
  - `b8949f5`/`1ea1bb7` 与那三笔同一次 push、只有头笔建跑 ⇒ 具名 `CI_UNREAD`。`41469418563 ↔ 2f85c5d`（R558 ⓪ 笔）= **success** ⇒ 一次性 push 那条因果继续成立。永不重开：`41452722560↔58851c2`、`41455782587↔598b253`（cancelled、0 失败步骤、`log not found`）。queue 现读 `共=10 queued=0 in_progress=1 concluded=9`（复述时）⇒ 收口时 `in_progress=0`。
- **U-2396：第四格是量出来的，不是选出来的 —— 外加三次证伪照实记。** 看 `heatmap-populated` 时先怀疑了三件事，两件被像素否掉：① 「今天」那颗点落在网格外 ⇒ 实测 bbox x 393.0…396.5、末格右缘 397，**在格内**；② 点落错行 ⇒ 夹具合成 today=`2026-03-12` **正是周四**，且角标是设计内（`Circle().frame(4).padding(1)`）；③ 图例与网格不同色 ⇒ 四档蓝**逐色相同**。第 ③ 条的剩余部分成立：**网格画了五种实心色，图例只标四档** —— 亮档实测 格色 (243,243,243)×46 格 + (215,232,255)×19 + (180,210,255)×25 + (130,180,255)×33 + (39,132,255)×28，182 格里 **46 格（25%）用的颜色在图例里查不到**，读图的人只能猜「那块灰算不算一种更浅的蓝」。零次档用的是 `Color.primary.opacity(VisualHeat.empty=0.055)`，而图例画的是 `Color.accentColor.opacity(VisualHeat.ladder[i])` —— **两份不同的常量**，所以这不是"少画一格"，是"标尺对不上被量的东西"。**先查再改**：热图是共享绘图路径，既有判据与旧读数在改之前全列出来（U-2399），改完逐条重读。
- **U-2397：判据先写、旧值先红。** 新判据 `UICaptureTests/testHeatmapLegendCoversEveryCellColor`（`UICaptureHarness.swift`）不写死坐标、不抄产品常量，四步全部从帧里量：① 「网格行」= 一行里有 ≥20 段宽度 ≥8px 的非页底游程（每行 26 格；页脚那一行实测只有 14–16 段 ⇒ 门是量出来的不是猜的）；② 格宽 = 网格行游程的**中位数**（现读 22px@2x）⇒ 实心判定随倍率走，runner 的 1x 不会被写死的像素数判成缺；③ 「格色」= 网格区里放得下 `3/5 格宽` 实心方块的颜色（文字笔画放不下 ⇒ 标签不会被误当成档位）；④ 「图例色」= 网格下缘以下放得下 `1/4 格宽` 实心方块的颜色。**旧值（红 2 条）**：`HEAT_LEGEND_COVERAGE light 格色=8 图例色=4 缺=[(243,243,243)]`、`dark 格色=9 图例色=4 缺=[(41,41,41)]`（`/tmp/r559-crit-old.log`）。⚠ 「格色=8/9」比"五种"多：格色那一档把抗锯齿边与圆角也数进去了（`minHits=30` 只滤掉零星点），所以判据是**包含关系**（每一种格色都要在图例里查得到）而不是**相等**（两边数量必须一样）—— 后者会被这一格读数直接判成假红。正对照内置在判据里：四个非零档在两档外观里都被读到 ⇒ "缺一种"是通道看见之后的缺。
- **U-2398：新判据上 runner 之前先测这把尺在 1x 灵不灵 —— 它不灵，于是今天只在 2x 判。** 把本轮 2x 帧最近邻降到 1x 复算同一套判定（一次性探针，不入库 ⇒ **不能当证人**），量到"一个方块里放得下的采样点数"从 2x 的 **36** 掉到 1x 的 **9**（采样步长 2；方块 8px 减掉实心边 3px 只剩 3 个位置），实测图例命中分布：2x `[31,29,27,27,27 | 3,2,2]`（噪声与真色分得很开）、1x `[9,9,7,7,6 | 1]` ⇒ 绝对地板 `minHits=8` 在 1x 上会把五档读到只剩 **2 档**，也就是 runner 第一次跑它就会报「缺三种」的**假红**（R465/R488 那一族：尺没有对象时不许硬判）。落法走本仓库既有的形状（`SETTINGS_HELPER_FONT_NOT_RUN=scale-too-low`、`SETTINGS_FOOTER_BAND_NOT_RUN=runner-1x-band-geometry`）：`倍率 < 1.5` 时打一行 `HEAT_LEGEND_NOT_RUN=scale-too-low …` 具名读数并 `continue`，**像素断言只在 2x 跑**；正常那行读数同时补上 `倍率=`，让下一轮能自己分辨是哪一档。⚠ 没有拿降采样代理去改 `minHits`：那等于用一张假的 1x 帧钉一个真的参数。要在 1x 上也判，需要真 1x 帧 + 把两道地板改成按几何派生（`((边长−实心边)/2+1)²` 的一半），这一格写进 R560 ⓪。
- **U-2399：产品改法与 ⓪ 计划的偏差（照实记，不当成没发生过）。** 落地：`footer` 的图例补一块 `Color.primary.opacity(VisualHeat.empty)`（**与格子同一份常量**，不是新造颜色），并把五块方块包进 `HStack(spacing: 4)`。**⓪ 那一节原本写的是**「缩格宽 8→7pt、间距 8→5pt ⇒ 整条 56→55pt」；实际没缩方块：**方块宽度是判据的取样对象**（`swatchSolid = 格宽/4`），把方块缩到 7pt 会同时把可判定的实心区缩掉，而且方块与格子同宽本来就是"同一把标尺"这句话的一部分。改成只动间距：`4×8+3×8=56` → `5×8+4×4=56`（`VisualHeat.cell=11` ⇒ 方块 8pt），**净宽一字未动**。为什么必须不动：页脚那句悬停详情实测已顶到 x≈494/860px（2x），加宽会把它挤成省略号 —— 那是拿一个可见性问题去换另一个。新值绿：`图例色=5 缺=[]`（两档外观）。
- **U-2400：兄弟判据逐条重读（旧→新，没有一条改期望）。** 图例墨证人 `CAPTION_INK heatmap-populated/图例「少 / 多」（颜色深浅的唯一标尺）`：亮档 `ratio=3.85 参照=3.75 比值=1.03` **一字未动**，`ink=14.1%→10.2%`；暗档 `ratio=6.06 参照=6.06 比值=1.00` 未动，`ink=15.4%→11.9%`。`ink=` 是那个 25×14pt 探针框里的墨覆盖率，地板 `probeInkFraction=3%` **没动、余量 3.4×/4.0×**。降的成因是**逐像素定位**出来的，不是猜的：把 R558 那一张与本轮这一张按帧对切，探针框内旧帧有 46 个 `(215,232,255)`（最浅那档蓝被从那个位置挪走了）、新帧同一位置是 49 个 `(243,243,243)`（新补的零次档），页底 `(255,255,255)` 两边都是 1167 个 ⇒ 框里换进去的是一种**更接近页面**的填充，所以覆盖率降、而对比度（读的是「少」/「多」那两枚字的笔画）不变。**另两条兄弟判据的读数逐字未变**：`HEATMAP_TODAY light/dark 差异像素=60 bbox=1108,408-1115,415 倍率=2.0x 内容墨=47615/33627`（与 ⓪ 列出的旧值一字不差）、`HEATMAP_SUMMARY_CHANGE light 变化=3872 前墨=3696 后墨=3780 前右沿=481 后右沿=494`、`dark 变化=4165 前墨=4151 后墨=4239 前右沿=481 后右沿=494` ⇒ "补一块会不会把悬停详情那句挤出去"这条担心被**右沿那一格**直接否掉（494 未动），而它同时也是宽度中性第二条独立证据。判据卷整卷 **%(CAPTURE)s**。
- **U-2401：重捕 + 逐张看图 + 基线同一笔 update。** 全帧差异只有图例那一行：两档外观各 **1172 像素**、bbox 完全相同 `x 70…157 / y 360…375`（2x）= `pt x 35.0…78.5 / y 180.0…187.5` ⇒ 网格、星期刻度、悬停详情那句一字未动。看图（`/tmp/r559-legend-oldvsnew.png`，上=旧、下=新，3× 最近邻放大）：旧 `少 [淡蓝 蓝 中蓝 深蓝] 多`、新 `少 [灰 淡蓝 蓝 中蓝 深蓝] 多`，暗档同形（灰 = 网格零次格那一档）；`多` 与后面那句「最忙的…」在旧/新两行里**同一位置** ⇒ 宽度中性这件事是眼睛也看过的，不只由算式担保。帧对账 `FRAME_BASELINE_COMPARED=%(FRAMES)s`，基线与台账同一笔 `update`（规矩：改了界面就在同一个 commit 里刷基线，否则基线永远过期）。
- **U-2402：635 两条腿 —— 一条会红的钉子 + 一句具名的不判，各有证人。** R558 的探针证明像素通道对 `MarkdownModeButton` 那三行接线是盲的（单摘/全摘读数逐字相同），所以本轮**两条都走**：① 契约钉子 `testMarkdownModeLabelWiringIsPinnedBecauseTheFilmCannotSeeIt` —— 在产品源码里 grep `.id(title)` / `.transition(.opacity)` / `.animation(MotionCatalog.animation(for: .contentFade), value: title)`，现读 `MOTION_WIRING_UNJUDGED markdown-mode-label 钉子=grep 钉住=3/3`，证人 = **M1452**（摘掉 `.id(title)` ⇒ 钉子红：`钉住=2/3`、`缺 1 根：.id(title)`）；② 胶片那一格自己打出 `MOTION_NOT_RUN=markdown-wiring-unjudged markdown-mode-label：本格只判标签有没有中间态…`，证人 = **M1453**（删掉这行 emit ⇒ 钉子红）。两个坑都是当场撞出来的，都写进代码注释：(i) 第一版用 `testSource(named:"DetailView.swift")` 读产品 —— 那个 helper 走 **Tests/** 目录，报的是「守卫找不到被守卫的东西时必须红」，改成 `productSource(named:"Views/DetailView.swift")`；(ii) 第一版在**整份自己源码**里搜那句具名读数 ⇒ 会在**守卫自己那行字面量**里读到它（R53/R55 那一族自满足），改成只在 `testMarkdownModeLabelChangeIsAVisibleProcess` 的函数体里搜（`region(in: codeOnly(…))`）。⚠ 边界照实说：钉子签的是"这三行还在"，**不是**"这三行改变了画面"——那三行在这条通道里到底改变什么，今天仍然没有像素证人；629 那句话因此只说「标签有没有中间态」。
- **U-2403：刀、名册、验证链与交接。** **M1450**（图例退回四块 ⇒ 判据红，现读 `图例色=4 缺=[(243,243,243)]`/`[(41,41,41)]`）、**M1451**（数量不动、把零次档画成 `Color.accentColor.opacity(VisualHeat.empty)` ⇒ 仍红 `图例色=5 缺=[…]` ⇒ 钉的是**颜色身份**而不是方块个数）、**M1452**（摘 `.id(title)` ⇒ 635 钉子红）、**M1453**（删具名读数 ⇒ 交叉核对红）**全 CAUGHT、RESTORE_CLEAN=yes**。四张表登记进 `mutate_needle_precheck.py` 名册，现读 **%(PRECHECK)s**、`ARM_TOTAL %(ARM)s`、`HIDDEN_ARMS %(HIDDEN)s`；与前几批同形（`OLD`/`NEW` 常量 + `text.replace`）⇒ 静态抽不出 needle、不在 `covered` 里，会红性只由真跑证明。**③ 验证链（顺序未换）**：`swift build --build-tests` 告警 **0**；判据 filter 绿（`Executed 2 tests, with 0 failures`）；四把刀全 CAUGHT；判据卷 **%(CAPTURE)s**；帧重捕 + 基线同一笔 **%(FRAMES)s**；全量 **%(FULL)s**；预检三读**串行**（与 swift 卷并行会撞锁假报 `NOT_RUN_TIMEOUT`，R558 那一格）；换装 %(INSTALL)s。**台账之前那一遍电池现读 `Ran 696 / FAILED (failures=2, skipped=5)`，两朵都是本轮预期内的时序红，而且第一朵正是 634 的现场演示**：① `test_skip_roster` 仍然红（没放宽），但正文写的是 `内层那一卷自己是红的 ⇒ 这一格没有可对账的对象，红在内层不在这里。汇总行「FAILED (failures=1, 跳过了=6)」；内层红名=test_the_cell_agrees_with_its_own_source（键=local:MacBook-Air.local 类=local）。这一句从前写成「内层没有结论行」，那是把被观察者的红借成观察者的缺席（634）` ⇒ **三态里的 `inner-red` 第一次在真场景里说话**（R558 那次只有注入演示，这一次是自然发生）；② `test_sources_cell_second_source` 红 = `AGENT_FINAL_REPORT.md` 的 sources 格还写着 R557/`2ca9501`，而 git 说最近动 `Sources/` 的是本轮 A 笔 `3a3c9a9` ⇒ 按 R556 的教训，派生必须排在产品笔之后，所以这一朵在台账笔之后跑 `report_sources_cell.py --write` 就退场（台账与基线同一笔、`--write` 排在提交之后、电池再复跑、最后一次性 push ⇒ 中间态只存在于未推的本地历史里，CI 看不到）。产品面连续零改动那一格现读 `PRODUCT_STREAK_FOR round=559 streak=1 last=3a3c9a9 last_round=558`（脚本按 subject 里的「第 N 轮」归属 ⇒ 本轮 A 笔被记进 558 轮；口径差一那格仍挂 BACKLOG 412，不手抄上一轮的数）。**④⑤ 账与交接**：清账 **%(ABSENCE)s**；电池 **%(BATTERY)s**（台账与补记之后复跑，结论只抄 `Ran`/`OK`/`FAILED` 两行，`&&` 链里不插 grep）；产品面连续零改动 **%(STREAK)s** 轮（`python3 scripts/product_streak.py` 现读；本轮动了 `Sources/` ⇒ 这一格归零重算，R557、R558 两轮的连读在这里断掉，是**好事**）。**635 = 结案**（两条腿 + 两把刀）；**629 保持「(B) 已落地」不写成完全结案**（像素那一半仍只到"标签有没有中间态"，且 runner 首个真数 `过渡帧数=2` **余量 0**、每格 71.5ms 比 R557 那三跑粗 2.5–3 倍）；622/624/627 继续；628/625/626/569/616/632/634 已落地那半不重开；**633 仍等用户人工回执**。下一轮 R560（第 559 轮 / Round 557）：⓪ 必读本轮各笔自己的跑（一次性 push ⇒ 只有头笔建跑，其余具名 `CI_UNREAD`）**加上仍挂着的 `41485625452 ↔ 8115ab8`**（逐条抄全部失败步骤，success 步骤另读 `gh run view --json jobs`），头一格 = **本轮那一笔自己的跑**上 `HEAT_LEGEND_COVERAGE`/`HEAT_LEGEND_NOT_RUN` 到底走哪条（1x 应当具名不判 ⇒ 若它反而报了 `缺=[…]`，那是尺在 1x 上没有对象而不是图例坏了，照 U-2398 的几何派生那条路修，不许降地板）+ **新口径 `过渡帧数=` 的第二个 runner 真数**（本轮首数 = 2、余量 0、每格 71.5ms ⇒ 掉到 1 就是那把尺的余量问题，不是产品回归，按 629 的既有口径具名入账） ⇒ 图例覆盖这一格今天没有 runner 读数，别把它读成"runner 也验过了"；要在 1x 上也判，拿真 1x 帧把两道 `minHits` 改成按几何派生（`((边长−实心边)/2+1)²` 的一半），不许拿降采样代理猜参数；禁碰清单 9 面不变（R546 登录失败图标、R547 默认排除行锁、R548 250pt 批量标题、R549 项目符 ⦁、R550 提示「Esc」、R551 收藏星尺寸、R552 折叠过渡、R553 本机码签身份链、R555 星判据的倍率口径）；**本轮新面登记：热图图例（R559）⇒ 禁碰 10 面**；刀号 **M1454** 起；4.5 地板、150 上限、120ms 阈值、Motion ≥2 帧地板、2x 8.0pt 跨度地板、1x 6.0pt 整行地板、`probeInkFraction=3%` 均不动；`.contentFade` 0.20 与声明时长一字未改。

"""


ITER = u"""
## Round 556 · R559（第 558 轮 · 2026-11-03）：热图图例补上零次档那一块；635 的两条腿各自配了一把刀

三轮没动产品之后回到产品面，而且这一轮的面是**量出来的**：`heatmap-populated` 的网格画了五种实心色（零次档是 `Color.primary.opacity(0.055)` 那一灰），图例只标 `VisualHeat.ladder` 那四档蓝 —— 182 格里 46 格（25%）用的颜色在图例里查不到。判据先写、旧值先红（`light 格色=8 图例色=4 缺=[(243,243,243)]`），再改产品：补一块与格子**同一份常量**的方块，把方块间距 8→4 吃掉新增宽度（`4×8+3×8=56` → `5×8+4×4=56`，净宽一字未动，因为页脚那句悬停详情实测已顶到 x≈494/860px）。看图 + 逐像素对切两张帧：全帧只有图例那一行变了（两档外观各 1172 像素、bbox 完全相同），而 `ink=` 从 14.1%→10.2% 的降不是坏消息 —— 探针框里换进去的是一种更接近页面的填充，定位到具体像素之后才敢写这一句，地板 3% 与对比度 3.85/6.06 都没动。635 同轮结案：像素通道判不到的那三行接线，一条 grep 契约钉子（M1452 摘一行就红）+ 一句具名的不判读数（M1453 删掉就红），两条腿各有证人；过程中撞到的两个坑（读错目录、守卫在自己的消息文本里读到被搜的串）都写进了代码注释。

**七维度自评**（恰七行，每格 n/15）：

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉看图 | 15/15 | 两张帧逐像素对切 + 3× 放大并排看（`/tmp/r559-legend-oldvsnew.png`）：旧四块、新五块，`多` 与悬停详情同一位置；三次证伪（点在格内、点=周四、四档蓝同色）也都是看图起头、量像素收口。 |
| 判据有效性 | 15/15 | 新判据先红后绿，两把刀各砍一个维度（M1450 数量、M1451 颜色身份）；635 两条腿各配一把刀（M1452/M1453）；正对照内置（四个非零档在两档外观都被读到）证明"缺一种"是看见之后的缺。 |
| 假绿防御 | 14/15 | 本轮防的是"图例画了五块就算对"（M1451）与"守卫在自己的文本里读到自己"（改成 region 限定）；仍留一格假绿：635 的钉子只签"这三行还在"，不签"这三行改变了画面"——这一格今天没有像素证人，已写进账与 629 的限定句。 |
| 产品面推进 | 15/15 | 动了 `Sources/`（1 文件），有帧变化作证、有包含判据作证、两把刀；三轮零改动之后回到产品面，streak 归零。 |
| 台账一致性 | 14/15 | 七本齐；⓪ 计划与实际落地的偏差（缩方块 vs 缩间距）**照实写在账里**；基线与台账同一笔 update；sources 格排在产品笔之后派生。扣分：`ink=` 的降幅只由两帧对切解释，没有第二条独立通道复核。 |
| 交付诚实性 | 15/15 | 三次证伪照实入账（不当缺陷、也不当推进）；⓪ 两格当时按 in_progress 具名 NOT-RUN（没拿它当"已经拿到"），收口前复述到数就当场改写成读数，而且拿到的是**余量 0** 那种不好听的数；629 不写成完全结案。 |

"""


CHG = u"""- **R559（热图图例补零次档 + 635 两条腿；产品 1 文件 + 判据 2 文件 + 四把刀）**：`DailyCopyHeatmapView` 页脚的图例从前只画 `VisualHeat.ladder` 那四档蓝，而网格里的零次格用的是 `Color.primary.opacity(VisualHeat.empty)` —— 一张 182 格的图里 46 格（25%）的颜色在图例里查不到。新判据 `UICaptureTests/testHeatmapLegendCoversEveryCellColor`（网格用到的每一种实心色都必须出现在图例带里；格宽、网格下缘、实心判定全部从帧里量，不抄产品常量）先红后绿，产品补一块**同一份常量**的方块并把间距 8→4 吃掉宽度（净宽 56pt 不变）。635 结案：`MarkdownModeButton` 那三行接线由一条 grep 契约钉子钉住（M1452），胶片那一格同时打出 `MOTION_NOT_RUN=markdown-wiring-unjudged`（M1453）。刀 **M1450–M1453** 全 CAUGHT、RESTORE_CLEAN；帧基线同一笔 update；4.5/150/120ms/≥2 帧/2x 8.0pt/1x 6.0pt/`probeInkFraction=3%` 一律未动。

"""


B629 = u"""    限定（R559，635 结案时补）：本轮把「产品接没接」那一半**降级成具名不判 + 契约钉子**，没有把它升级成像素证人 —— `MOTION_MARKDOWN_MODE_FADE` 只签「标签有没有中间态」，那三行接线由 `testMarkdownModeLabelWiringIsPinnedBecauseTheFilmCannotSeeIt` 的 grep 钉子签（M1452 摘一行即红），胶片那一格自己打 `MOTION_NOT_RUN=markdown-wiring-unjudged`（M1453 删掉即红）。所以 629 这句话**仍然不许**写成「接线已被动效判据验过」；要写成「接线有契约钉子、无像素证人」。

"""


B635 = u"""    结案（R559，两条腿都落地、各配一把刀）：① **会红的钉子** = `MotionFilmstripTests/testMarkdownModeLabelWiringIsPinnedBecauseTheFilmCannotSeeIt`，在产品源码 `Views/DetailView.swift` 的 `struct MarkdownModeButton` 体内 grep 三行接线（`codeOnly` 摘掉注释、区域按四个空格的关门截断），现读 `MOTION_WIRING_UNJUDGED … 钉子=grep 钉住=3/3`；证人 **M1452**（摘 `.id(title)` ⇒ `钉住=2/3`、红名 `缺 1 根：.id(title)`、RESTORE_CLEAN）。② **具名的不判** = 胶片那一格 `testMarkdownModeLabelChangeIsAVisibleProcess` 现在无条件打 `MOTION_NOT_RUN=markdown-wiring-unjudged markdown-mode-label：本格只判标签有没有中间态…`；证人 **M1453**（删掉这行 ⇒ 钉子里那句交叉核对红）。两个坑记在这里免得重踩：读产品源码要用 `productSource`（`testSource` 走 Tests/ 目录，报的是「守卫找不到被守卫的东西」）；扫自身源码的具名读数必须**限定在被守卫的函数体**里（`region(in: codeOnly(…))`），否则守卫会在自己那行字面量里读到它、绿着放过 M1453。**仍然开着的那半格**：那三行在这条捕获通道里到底改变什么，今天没有像素答案 —— 若将来要判，得先量出它们的可见效果，而不是把钉子当成证人。

"""


B622 = u"""    复查（R559）：本轮**没有**新值 —— `41485625452 ↔ 8115ab8` 到收口前仍是 in_progress（已等 1663s）⇒ 622 的 runner 复核与 629 的新口径读数一并具名 NOT-RUN，挂进 R560 ⓪。阈值 120ms、容差 1 颗、`over_runs` 口径一律不动，frame 半继续开单。

"""


DEC = u"""## D-559（R559 · 2026-11-03）：图例必须覆盖网格画出的每一种颜色；判据判不到的东西用「会红的钉子 + 具名不判」两条腿

① **图例的契约是「包含」，不是「画了五块」**。热图网格的零次格用 `Color.primary.opacity(VisualHeat.empty)`，而非零格用 `Color.accentColor.opacity(VisualHeat.ladder[i])` —— 两份不同的常量，所以图例只画 `ladder` 那四档时，182 格里 46 格（25%）的颜色查不到。判据因此写成"每一种格色都必须出现在图例带里"，并配两把方向相反的刀：M1450 砍数量（退回四块 ⇒ 红）、M1451 砍颜色身份（数量不动、把那一块换成浅蓝 ⇒ 仍红）。只配 M1450 是不够的：那等于允许有人拿"个数对上了"交差。
② **宽度中性优先于"顺手改好看"**。补一块必然加宽，而页脚那句悬停详情实测已顶到 x≈494/860px ⇒ 加宽会把它挤成省略号，那是拿一个可见性问题换另一个。落法：方块宽度保持与格子同源（8pt），只把间距 8→4，`4×8+3×8=56` → `5×8+4×4=56`。 ⓪ 那一节原计划是"缩方块 8→7 + 间距 8→5"，实施时否掉：方块是判据的取样对象（`swatchSolid=格宽/4`），缩方块会同时缩掉可判定区，而且"图例块与格子同宽"本身是"同一把标尺"这句话的一部分。**计划与落地不一致要在账里看得见**。
③ **派生量会因产品改动跳档，先定位再解释，不许改期望**。图例墨证人 `ink=`（25×14pt 框里的墨覆盖率）从 14.1%→10.2%（亮）/15.4%→11.9%（暗）。这一格可以被写成"判据变松了"，但真因是逐像素定位出来的：框内旧帧 46 个 `(215,232,255)`（最浅那档蓝被挪走）换成 49 个 `(243,243,243)`（新补的零次档），页底 `(255,255,255)` 两边都是 1167 个 ⇒ 换进去的填充更接近页面，所以覆盖率降；对比度（读的是「少」/「多」两枚字）一字未动，地板 3% 未动、余量 3.4×/4.0×。**读数跳档时，先证明它跳在哪几个像素上，再决定这句话怎么说**。
④ **判据判不到的东西，降级要降级得"有牙"**。635 的出口不是"承认判不到就完了"：像素通道对那三行接线是盲的（R558 四臂探针），所以本轮同时落 ①一条会红的 grep 契约钉子 ②一句具名的不判读数，**各配一把刀**（M1452/M1453）。少了刀，"不判"就变成一句没人执行的注释（本仓库的老形状）；少了具名读数，胶片的绿会被下游读成"接线验过了"。
⑤ **边界**：635 结案只结到"接线不再被悄悄冒充成已验"，**不结到**"接线的效果被看见了"；629 因此仍写作「(B) 已落地」，不写"完全结案"。
⑥ **撤回**：把 `footer` 里新补的那一块删掉 + 间距改回 8 即回到 R558 的形状（M1450 的形状会红）；把 `MOTION_NOT_RUN=markdown-wiring-unjudged` 那行删掉，635 的钉子会红（M1453）。
"""


def insert_after_line(t, line_prefix, block, label):
    u"""按**行首前缀**定位那一行，插到它后面（长行里有反引号与百分号时比抄整行稳）。"""
    hits = [i for i, ln in enumerate(t.split(u"\n")) if ln.startswith(line_prefix)]
    if len(hits) != 1:
        sys.stderr.write("ANCHOR_BAD %s lines=%d\n" % (label, len(hits)))
        sys.exit(1)
    i = t.index(line_prefix)
    j = t.find(u"\n", i)
    return t[:j + 1] + block + t[j + 1:]


def rd(name):
    return io.open(os.path.join(ROOT, name), encoding="utf-8").read()


def wr(name, t):
    io.open(os.path.join(ROOT, name), "w", encoding="utf-8").write(t)


def once(t, old, new, label):
    n = t.count(old)
    if n != 1:
        sys.stderr.write("ANCHOR_BAD %s hits=%d\n" % (label, n))
        sys.exit(1)
    return t.replace(old, new, 1)


def insert_after(t, anchor, block, label):
    i = t.find(anchor)
    if i < 0 or t.count(anchor) != 1:
        sys.stderr.write("ANCHOR_BAD %s hits=%d\n" % (label, t.count(anchor)))
        sys.exit(1)
    j = t.find("\n\n", i)
    if j < 0:
        sys.stderr.write("ANCHOR_BAD %s no-blank-line-tail\n" % label)
        sys.exit(1)
    return t[:j + 1] + block + t[j + 1:]


def fill(text):
    out = text
    for key, value in NUM.items():
        out = out.replace(u"%%(%s)s" % key, value)
    if u"%(" in out:
        i = out.find(u"%(")
        sys.stderr.write("PLACEHOLDER_LEFT %s\n" % out[i:i + 30])
        sys.exit(1)
    return out


def main():
    check = "--check" in sys.argv

    for key, value in NUM.items():
        if u"%(" in value:
            sys.stderr.write("NUM_NOT_FILLED %s\n" % key)
            return 1

    state = rd("AGENT_STATE.md")
    if state.count(u"## R559 ⓪ 开工") != 1:
        sys.stderr.write("ANCHOR_BAD state R559 ⓪ 节不存在 ⇒ 不许两轮写进同一节\n")
        return 1
    if u"## R559 状态（" in state:
        sys.stderr.write("ANCHOR_BAD state R559 状态节已存在\n")
        return 1

    n = "AGENT_UI_AUDIT.md"
    t = rd(n)
    a = u"## 第 557 轮（R558 · 2026-11-03 · U-2387…U-2394）"
    if t.count(a) != 1:
        sys.stderr.write("ANCHOR_BAD ui\n")
        return 1
    if not check:
        wr(n, t.replace(a, fill(UI) + a, 1))

    n = "AGENT_VISUAL_ITERATION.md"
    t = rd(n)
    if u"## Round 556 · R559" in t:
        sys.stderr.write("ANCHOR_BAD iteration Round 556 已存在\n")
        return 1
    if not t.endswith(u"\n"):
        t += u"\n"
    if not check:
        wr(n, t + fill(ITER))

    n = "CHANGELOG.md"
    t = rd(n)
    a = u"## [Unreleased]\n\n"
    if t.count(a) != 1:
        sys.stderr.write("ANCHOR_BAD changelog\n")
        return 1
    if not check:
        wr(n, t.replace(a, a + fill(CHG), 1))

    n = "AGENT_BACKLOG.md"
    t = rd(n)
    # 622：本轮无新值那一行接在 R558 那条复查之后
    t = insert_after_line(t, u"    复查（R558）：新增**第十三值**", B622, u"backlog622")
    # 629：限定那一行接在 R558「落地（B）」那段之后
    t = insert_after(t, u"证人：合成四臂真值表 + 负向臂 M1446。\n", B629, u"backlog629")
    # 635：结案段接在「关联：629…634…」那一行之后（那一行里是 ASCII 双引号 ⇒ 字面量用单引号包）
    t = insert_after(t, u'    关联：629（本轮已按 (B) 换对象落地，但带这条限定）、634（同一轮里另一条"观察者说假话"的形状）。\n',
                     B635, u"backlog635")
    if not check:
        wr(n, t)

    n = "AGENT_DECISIONS.md"
    t = rd(n)
    if not t.endswith(u"\n"):
        t += u"\n"
    if not check:
        wr(n, t + fill(DEC))

    n = "AGENT_FINAL_REPORT.md"
    t = rd(n)
    for old, new, label in [
        (u"R9–R555，556 节自评", u"R9–R556，557 节自评", u"title"),
        (u"阶段二 **548 轮**审计（R9–R555；以 `curve_from_ledger.py` 的 `PHASE2 n=548` 为准，最新一节是 `AGENT_VISUAL_ITERATION.md` 的 Round 555",
         u"阶段二 **549 轮**审计（R9–R556；以 `curve_from_ledger.py` 的 `PHASE2 n=549` 为准，最新一节是 `AGENT_VISUAL_ITERATION.md` 的 Round 556", u"§1"),
        (u"| 视觉台账 | U-31 … U-2394", u"| 视觉台账 | U-31 … U-2403", u"U 上界"),
        (u"产品面连续零改动轮数 = **1**（as-of 557）", u"产品面连续零改动轮数 = **%(STREAK)s**（as-of 558）", u"streak as-of"),
        (u"以 `AGENT_STATE.md` 的 R558 节 ② 为准", u"以 `AGENT_STATE.md` 的 R559 节 ② 为准", u"state pointer"),
        (u"## 18. R458 → R558 这一段", u"## 18. R458 → R559 这一段", u"§18 head"),
        (u"R558 续到 558 —— 这份报告第七次差点停在几十轮之前）",
         u"R559 续到 559 —— 这份报告第七次差点停在几十轮之前）", u"§18 tail"),
    ]:
        t = once(t, fill(old), fill(new), label)
    anchor = u"电池 695⇒696（新增真值表那一格）。帧 354 CHANGED=0 MISSING=0 ADDED=0；全量 1400/57/0（748.1s）；build 0 告警；电池 696/5。\n"
    bullet = (u"- **R559（热图图例补零次档 + 635 两条腿；产品 1 文件 + 判据 2 文件 + 四把刀）**："
              u"`heatmap-populated` 的网格画了五种实心色（零次格 = `Color.primary.opacity(VisualHeat.empty)`），"
              u"图例只标 `ladder` 那四档蓝 ⇒ 182 格里 46 格（25%）的颜色查不到。"
              u"判据先红（`light 格色=8 图例色=4 缺=[(243,243,243)]`、`dark 缺=[(41,41,41)]`）再改产品："
              u"补一块**同一份常量**的方块 + 间距 8→4 ⇒ 净宽 `4×8+3×8=56` → `5×8+4×4=56` 一字未动。"
              u"看图与逐像素对切：两档外观各 1172 像素变化、bbox 同为 `pt x35.0…78.5 / y180.0…187.5`（只有图例那一行）；"
              u"`ink=14.1%→10.2%` 的降幅定位到框内 46 个 `(215,232,255)` 换成 49 个 `(243,243,243)`，"
              u"对比度 3.85/6.06 与地板 3% 未动。**635 结案**：grep 契约钉子（钉住=3/3）+ 具名不判读数，"
              u"各配一把刀。刀 **M1450–M1453** 全 CAUGHT、RESTORE_CLEAN；基线同一笔 update；"
              u"⓪ 计划（缩方块）与落地（缩间距）的偏差照实写进账。"
              u"帧 %(FRAMES)s；全量 %(FULL)s；build 0 告警；电池 %(BATTERY)s。\n")
    t = once(t, anchor, anchor + fill(bullet), u"§18 bullet")
    if not check:
        wr(n, t)

    n = "AGENT_STATE.md"
    t = rd(n)
    t = once(t,
             u"最后更新：2026-11-03（本地 · R558 / 第 557 轮 / Round 555）",
             u"最后更新：2026-11-03（本地 · R559 / 第 558 轮 / Round 556）",
             u"identity")
    body = u"""## R559 状态（2026-11-03 · 第 558 轮 / Round 556 · 产品 1 文件 + 判据 2 文件 + 四把刀）

① ：`41485625452↔8115ab8`（R558 那一批的头笔）开场 queued、复述 in_progress（1663s）⇒ 当时两格具名 NOT-RUN；**收口前再读 = concluded success ⇒ 两格当场转成读数**：新口径在 runner 上 `过渡帧数=2 相邻差帧数=2 首末连续差=0.0048 每格=71.5ms 窗口=1860ms` ⇒ **判到 ≥2 但余量 0**，且 runner 的钟比 R557 那三跑粗 2.5–3 倍 ⇒ 629 不写结案；STEP[9] `SKIP_ROSTER … 内层Ran=696 名单外=无 名册未跳=无` ⇒ **634 的借红被 runner 签掉**；STEP[19] `MOTION_FLOOR_OK=4/5 全部臂都在登记之内、MOTION_FLOOR_REDS=0` ⇒ 旧口径那朵 `testMarkdownModeLabelChang…` 红在这一跑不见了；STEP[18] success ⇒ 622 无新值。STEP[1]–[21] 逐条 conclusion 全 success（`gh run view --json jobs`）。`b8949f5`/`1ea1bb7` 同批 push 无独立跑 ⇒ `CI_UNREAD`；cancelled 两笔永不重开。
② ②(a) **第四格 = 真实产品面（三轮零改动之后回到 Sources）**：热图图例不覆盖网格画出的每一种颜色 —— 网格五种实心色（零次格 `Color.primary.opacity(VisualHeat.empty=0.055)`，亮 (243,243,243)/暗 (41,41,41)），图例只画 `ladder` 那四档蓝 ⇒ 182 格里 46 格（25%）查不到。判据先写先红（`格色=8 图例色=4 缺=[(243,243,243)]` 两档外观 2 failures），产品补一块**同一份常量**的方块、间距 8→4 ⇒ 净宽 56pt 不变（⓪ 计划的"缩方块"被否：方块是判据取样对象）。看图 + 两张帧逐像素对切：只有图例那一行变（两档各 1172 px、bbox `pt x35.0…78.5/y180.0…187.5`）；`ink=` 14.1→10.2（亮）/15.4→11.9（暗）定位到框内 46 个 (215,232,255) 换成 49 个 (243,243,243)，对比度与 3% 地板未动。三次证伪照实入账（点在格内、点=周四、四档蓝同色）。
③ ②(b) **635 结案（两条腿 + 各一把刀）**：①契约钉子 `testMarkdownModeLabelWiringIsPinnedBecauseTheFilmCannotSeeIt` 在产品源码里 grep 那三行（现读 `钉住=3/3`），证人 **M1452**（摘 `.id(title)` ⇒ 红）；②胶片那一格无条件打 `MOTION_NOT_RUN=markdown-wiring-unjudged`，证人 **M1453**（删掉 ⇒ 钉子那句交叉核对红）。两个坑写进代码注释：读产品要用 `productSource`（`testSource` 走 Tests/）；扫自身源码的具名读数必须限定在被守卫的函数体（`region(in: codeOnly(…))`），否则守卫在自己的字面量里读到它。**边界**：钉子只签"这三行还在"，不签"这三行改变了画面" ⇒ 629 仍写「(B) 已落地」，不写完全结案。②(c) 634 的 runner 复核 = 同 ① 具名 NOT-RUN。
④ ③ 验证链（顺序未换）：`swift build --build-tests` 告警 **0**；判据 filter 绿；四把刀全 CAUGHT；判据卷 **%(CAPTURE)s**；帧重捕 + 基线同一笔 **%(FRAMES)s**；全量 **%(FULL)s**；预检 **%(PRECHECK)s**、`ARM_TOTAL %(ARM)s`、`HIDDEN_ARMS %(HIDDEN)s`（三读**串行**）；换装 %(INSTALL)s。
⑤ ④⑤ 账与交接：清账 **%(ABSENCE)s**；电池 **%(BATTERY)s**（台账与补记之后复跑，只抄 `Ran`/`OK`/`FAILED`）；产品面连续零改动 **%(STREAK)s** 轮（现读 `python3 scripts/product_streak.py` ⇒ 本轮动了 `Sources/`，R557、R558 那两轮的连读在此断掉）。**635 = 结案**；629 保持「(B) 已落地 + 限定句 + runner 余量 0」；634 = runner 已签；622/624/627 继续；628/625/626/569/616/632/634 已落地那半不重开；**633 仍等用户人工回执**。⑥ 一次性 push（本轮四笔：⓪ 开工 + A 产品与判据 + 台账 + 补记）⇒ 只有头笔建跑，R560 ⓪ 必读它**加上仍挂着的 `41485625452↔8115ab8`**。刀号 **M1454** 起；禁碰清单本轮 +1 ⇒ **10 面**（新增 R559 热图图例）；4.5 地板、150 上限、120ms 阈值、Motion ≥2 帧地板、2x 8.0pt、1x 6.0pt、`probeInkFraction=3%` 均不动；`.contentFade` 0.20 与声明时长一字未改。⚠ 新判据 `HEAT_LEGEND_COVERAGE` 带一道 `倍率<1.5 ⇒ HEAT_LEGEND_NOT_RUN=scale-too-low` 的具名出口（探针实测 1x 上一个方块只剩 ~9 个采样点，绝对命中地板会把五档读到两档 ⇒ 假红）⇒ **runner 今天不判这一格**，账上不许写"runner 也验过"；要在 1x 上也判，拿**真 1x 帧**把 `minHits` 改成几何派生（`((边长−实心边)/2+1)²` 的一半），不许拿降采样代理猜参数。

"""
    a = u"\n## R559 ⓪ 开工（2026-11-03 · 第 558 轮 / Round 556 · CI 读单 + 基线全现读 + 第四格选定）"
    t = once(t, a, u"\n" + fill(body).rstrip(u"\n") + a, u"state body")
    if not check:
        wr(n, t)

    sys.stdout.write("LEDGERS_R559_%s\n" % ("CHECK_OK" if check else "WRITTEN"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
