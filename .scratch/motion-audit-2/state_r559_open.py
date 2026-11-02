# -*- coding: utf-8 -*-
"""R559 ⓪ 开工节：CI 读单（两格具名 NOT-RUN）+ 基线全现读 + 第四格选定（含三次证伪）。"""
import io

P = 'AGENT_STATE.md'
s = io.open(P, encoding='utf-8').read()

anchor = u'## R558 状态（2026-11-03 · 第 557 轮 / Round 555 · 产品 0 文件 + 判据 1 文件 + 观察者 1 文件 + 四把刀）'
assert s.count(anchor) == 1, s.count(anchor)

body = u"""## R559 ⓪ 开工（2026-11-03 · 第 558 轮 / Round 556 · CI 读单 + 基线全现读 + 第四格选定）

> 本节是**开工节**，不是轮次节（标题不写「状态」两字 —— `product_streak.py` 按第一个 `## Rnnn 状态（` 认当前轮）。

**前置实读**：`git log --oneline -3` = `8115ab8` / `1ea1bb7` / `b8949f5`；已跟踪改动 **0**；ahead=**0**（HEAD=origin=`8115ab8`）；`api=403 / apple=200` —— 403 **没有**挡住 `gh`（本轮 `ci_read.py queue` 正常出数）⇒ 不据此判断网，也不据此判产品结论。

**① CI 读单（只登记、不轮询）**
- `41485625452 ↔ 8115ab8`（R558 补记笔 = 那一批的头笔，内容含 R558 全部代码）状态 **queued** ⇒ **两格同时具名 NOT-RUN**：(a) 新口径（两端夹逼）在 runner 上读几；(c) 634 拆完之后 STEP[9] 的 `test_skip_roster` 还红不红。⚠ **不许拿旧口径那一行推新口径会读几** —— 换的是估计量（相邻差占比 → 两端夹逼的连续距离），旧行里没有那个量。
- `b8949f5`（R558 判据笔）与 `1ea1bb7`（台账笔）与那三笔同一次 push、只有头笔建跑 ⇒ 具名 `CI_UNREAD`，不写成"没红"。
- `41469418563 ↔ 2f85c5d`（R558 ⓪ 笔，纯台账、账上格与 git 一致）= **success** ⇒ 上一轮那条「分批 push 造注定红」的因果继续成立，本轮沿用「一次性 push」。
- `41467585182 ↔ ff15906`（R557 补记第二笔）= failure，STEP[9] **绿**，红在 **STEP[18]**（`PROBE_COVERAGE_SUMMARY … 本次跑过=8 红=1`；`testFrameIntervalsUnderStateChanges` 最差帧 **225.3ms** 超锚点 120ms、超锚点 **3 颗**（容差 1）⇒ 622 第十三值）与 **STEP[19]**（`MOTION_FLOOR_SUITE_RED=1 … testMarkdownModeLabelChang…`、`MOTION_FLOOR_REDS=1`、`judged=4/5 executed=77 not-run=notice-banner`、`MOTION_FLOOR_NOT_SEEN=2`；旧口径 `过渡帧数=1 峰值=0.0193 窗口=756ms 每格=29.1ms`）⇒ 两朵都是**既有红**、本轮未碰那两卷，按同族入账；R559 只复核 STEP[19] 在新口径上线后还在不在（拿不到 ⇒ 同上具名）。
- 已具名 NOT-RUN、永不重开：`41452722560 ↔ 58851c2`、`41455782587 ↔ 598b253`（各 15m01s cancelled、0 失败步骤、`--log` 直接 `log not found`）。

**② 基线（本轮全部现读）**：帧 **354**（`docs/frame_baseline.json` 现数，mtime 未动）；清账 **162/63/0**；streak **2**（`python3 scripts/product_streak.py --streak-for 558` 现读，last=`2ca9501`/556 ⇒ R557、R558 两轮都没动产品面，本轮落产品之后这一格归零重算）；预检 **tables=349 covered=295 arms=757 bad=0**、`ARM_TOTAL files=442 arms=1244 dupes=0 repeats=0`、`HIDDEN_ARMS 表=436 可判=1183 rot=0 抽不出=6 已声明表=6 处置=ok`；刀号现读最高 **M1449** ⇒ 本轮从 **M1450** 起。R558 收口现读（本轮动过就重跑，不照抄）：build 告警 0、判据卷 217/4/0（781.0s）、帧 354 CHANGED=0、全量 **1400/57/0（748.1s）**、电池 696/5、安装 433=433 + `INSTALL_SIGNATURE=local`。⚠ skipped 从前一轮 55 变 **57**，去重名单差恰两格（`UICaptureTests/testCaptureKeyViews`、`OffscreenSymbolInkProbeTests/testProductSettingsSidebarIconInk`，都是条件 skip）⇒ 本轮再读一次看稳不稳，只记现读不猜成因，**不许把 57 修回 55**。

**③ 第四格选定：热图图例不覆盖网格画出的全部颜色**（看图 + 像素现读，不是预设）
- 现读（`heatmap-populated` 亮档，2x 帧）：网格用到的色 = **(243,243,243) 零次档 46 格** + (215,232,255) 19 格 + (180,210,255) 25 格 + (130,180,255) 33 格 + (39,132,255) 28 格；图例只画后 **4** 档（`VisualHeat.ladder`），**零次档用的 `Color.primary.opacity(VisualHeat.empty=0.055)` 在图例里没有任何对应块** ⇒ 一张 182 格的图里 46 格（25%）的颜色读图者无法从图例查到。修法只补一块、不新造颜色（用与格子同一份常量）。
- **三次证伪照实记（都不是缺陷、不算推进）**：① 右侧那颗"今天"点我以为落在网格外 ⇒ 量出 bbox x 393.0…396.5、末格右缘 397，**在格内**；② 我以为点落错行 ⇒ 夹具合成 today=`2026-03-12` **正是周四**，点在第 4 行是对的，且角标是设计内（`Circle().frame(4).padding(1)`）；③ 我怀疑图例与网格不同色 ⇒ 实测图例四档与网格四个非零档**逐色相同**。⇒ 唯一成立的是"缺零次档那一块"。
- **先查再改**（热图是共享绘图路径）：既有热图判据与旧读数已列 —— `HEATMAP_TODAY light/dark 差异像素=60 bbox=1108,408-1115,415 倍率=2.0x 内容墨=47615/33627`（R484/R486 那一族，两臂差只在角标）、`HEATMAP_SUMMARY_CHANGE light 变化=3872 前墨=3696 后墨=3780 前右沿=481 后右沿=494` / `dark 变化=4165 前墨=4151 后墨=4239`、图例自己的墨证人 `INK heatmap-populated/图例「少 / 多」 light ratio=3.85 参照=3.75 比值=1.03 ink=14.1%`、`dark ratio=6.06 参照=6.06 比值=1.00 ink=15.4%`。⇒ 补一块必然让**图例墨**与**汇总变化墨**跳档：改完重跑这几条，旧值→新值写进本轮账，**不改期望、不降地板**；页脚那句悬停详情已快顶到右缘（`前右沿=481/后右沿=494`，帧宽 860px=430pt），所以图例补块的代价必须用**缩格宽与间距**吃掉（8→7pt、间距 8→5pt ⇒ 整条 56→55pt，净宽不增）。

**④ 本轮四格**
- (a) 新口径 runner 读数 —— 拿不到 ⇒ 具名 NOT-RUN（见 ①），不轮询、不推测。
- (b) **635** 走哪条出口：探针 `probe_r558_what_the_film_measures.py` 已入库可重跑，但它的结论是"三行单摘与全摘读数逐字不变"⇒ **这条通道判不到那三行**。因此本轮走**降级成具名不判**：判据正文与读数都不许再暗示"接线已验"，并给"不判"这件事配一条**会红的证人**（不许只写注释）。
- (c) 634 的 runner 复核 —— 同 (a) 具名 NOT-RUN。
- (d) **产品位 = ③ 那一格**：`Sources/…/DailyCopyHeatmapView.swift` 图例补零次档一块；证人 = 新的像素包含判据（网格用到的每一种颜色都必须出现在图例带里）；刀 **M1450**（把图例改回四块 ⇒ 必须红）、**M1451**（图例那块零次档用一个与格子不同的 alpha ⇒ 必须红，钉"必须同一个颜色"而不是"画了个差不多的"）。
- 633 仍等用户人工回执；622/624/627 继续；628/625/626/569/616/632 已落地那半不重开；629 只写「(B) 已落地 + 留 635」；禁碰清单 9 面不变；4.5 地板、150 上限、120ms 阈值、Motion ≥2 帧地板、2x 的 8.0pt 跨度地板、1x 的 6.0pt 整行地板一律不动；`.contentFade` 0.20 与声明时长一字不改。

"""

s = s.replace(anchor, body + anchor, 1)
io.open(P, 'w', encoding='utf-8').write(s)
print('R559 ⓪ written')
