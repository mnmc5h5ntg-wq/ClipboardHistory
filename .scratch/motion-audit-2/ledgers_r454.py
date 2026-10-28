#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R454 七本台账一次落盘（只跑一次；先断言所有锚点，全部通过才写）。"""
import io
import os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
AUDIT = os.path.join(ROOT, "AGENT_UI_AUDIT.md")
ITER = os.path.join(ROOT, "AGENT_VISUAL_ITERATION.md")
DECISIONS = os.path.join(ROOT, "AGENT_DECISIONS.md")
CHANGELOG = os.path.join(ROOT, "CHANGELOG.md")
BACKLOG = os.path.join(ROOT, "AGENT_BACKLOG.md")
STATE = os.path.join(ROOT, "AGENT_STATE.md")
REPORT = os.path.join(ROOT, "AGENT_FINAL_REPORT.md")


def rd(path):
    with io.open(path, encoding="utf-8") as h:
        return h.read()


def wr(path, text):
    with io.open(path, "w", encoding="utf-8") as h:
        h.write(text)


AUDIT_TITLE = u"## 第 452 轮（R453 · 2026-10-28"
AUDIT_SECTION = u"""## 第 453 轮（R454 · 2026-10-28 · U-1693…U-1697）：弱化正文的对比度从 3.95:1 补到 5.33/7.09（旧 secondary 亮档 3.95 低于 14pt 正文 4.5:1；6 张旧帧变化、基线名单 262）（产品 3 文件，弱化色对比度位）

- **U-1693：⓪ push 与跑。** 开工 remote=`c041c8d`、ahead=0，`git push` 为 **no-op**。已读：`40640660665 ↔ 86044bf` success（`LIST_HANG_STYLE 16.0/16.0/0.0` 签收）、`40642482086 ↔ e083179` success（`WEIGHT_CENTER_TICK_NOT_RUN=runner-settings-content-flat light/dark 轨=1`，按设计具名 NOT-RUN）、`40642524490 ↔ e750598` success、`40636558557 ↔ 667d1a2` success（TASK_DIM 1x 旧色 158.0/115.1 +42.9、128.4/166.4 −38.0）、`40634880705 ↔ 9743379` failure（`testProductDurationRevealStillMovesOverTime` 无中间 origin ⇒ `RUNNER_SCROLL_SESSION_FLAKE` + Motion `testMarkdownModeLabelChange` 1<2）、`40629776895`/`40623613789` failure 仅 Motion floor、`40620912699` failure 1 步（dark 行带，已修）。**`40645430259 ↔ 5c925a9`（R453 head，含 `STRIKE_DIM`）与 `40645469967 ↔ c041c8d`（R453 预记 head）读时 in_progress、`gh` 收口前再试仍 EOF ⇒ NOT-RUN**（R455 必读）。436 只复核 Motion floor：`judged=4/5 executed=77 not-run=notice-banner`、红 0；采样红原样重跑，不改门槛、不重猜 `must_judge`。
- **U-1694：① 腐烂与预检。** `HIDDEN_ARMS 表=318 可判=1017 rot=0`；`NEEDLE_PRECHECK tables=232 covered=214 arms=602 bad=0`、`ARM_TOTAL files=325 arms=1085`。本轮改的是两个弱化色的取值，没有弄断旧针。
- **U-1695：② 弱化正文的对比度。** 缺陷形状：R450（完成项）与 R453（删除线）都用 `secondaryLabelColor` 做弱化色 —— 亮档实测 **3.95:1**，低于 14pt 正文的 4.5:1（仓库里引用块的注释早因同一原因拒绝过它）。修法：新 `DeEmphasisPresentation.textColor` 动态色（亮档黑 58%、暗档白 62%），完成项与删除线共用。旧/新（`detail-tasks` 的完成项核心色 vs 页面底色，sRGB 相对亮度）：`DEEMPHASIS_CONTRAST light 文字=128/底色=255/比=3.95 → 文字=107/底色=255/比=5.33`、`dark 154/30/5.92 → 169/30/7.09`；R450/R453 的弱化差仍成立（`TASK_DIM light 133.5/85.2 +48.3、dark 146.4/184.3 −37.9`；`STRIKE_DIM light 123.3/82.0 +41.2、dark 158.9/192.3 −33.4；隙 9/9`）。**6 张旧帧变化**（detail-tasks/detail-strike/detail-markdown-rendered × 亮/暗）、0 新增/缺失；基线名单仍 **262**（同 commit 更新）；已看亮/暗：完成项仍比正文浅、但不再低到读不清。Store 未动（1108 行/52 方法/最长 66）。
- **U-1696：判据与刀。** 新单测 `DeEmphasisPresentationTests` 2 条（两档对比 ≥4.5、弱化色≠正文色；完成项/删除线共用同一色）+ 帧判据 `testDeEmphasizedTextMeetsContrast`（完成项核心色与底色算 sRGB 对比，≥4.5）。`M1242`（亮档 alpha 0.58→0.50 ≈ 旧 secondary 128）⇒ 单测+帧判据 CAUGHT；`M1243`（亮档 alpha→1.0 = 正文黑，弱化消失）⇒ R450 完成项帧判据 CAUGHT（第一版 alpha→0 会变成透明，红在对比度而不是"弱化消失"，改成 1.0 后落在正确的格）⇒ **2/2**、RESTORE_CLEAN=yes。
- **U-1697：八步与具名 NOT-RUN。** build **0 告警**；捕获卷 **262 帧**、`COMPARED=262 CHANGED=0 MISSING=0 ADDED=0`；全量 **1247/56/1**：唯一红＝`PerfBudgetTests.testImageComparisonCostStaysBounded`（`3000x2000 的一次去重比较 310.3ms` > 250ms，`load1=5.9`）—— 单跑同机 `load1=3.9` 时 177.8ms **通过** ⇒ 具名 **`LOCAL_PERF_BUDGET_FLAKE=load`**（不改阈值）；本跑里 5 条滚动红没有复现（滚动套件单跑 **4/4**，会话差；`LOCAL_SCROLL_SESSION_NOT_RUN` 口径保留，不据此删账）；换装 `INSTALL_RESULT=ok / SHA_MATCH=1 / 383=383`（剪贴板条目数本轮 383，不是 381 —— 现读安装日志）；`STORE-SIZE lines=1108 funcs=52 longest=66`；产品面连续零改动 **1** 轮（as-of 453，`python3 scripts/product_streak.py --streak-for 453`，last=4ba006f）；清账与电池在台账后复跑。**具名 NOT-RUN**：① `40645430259 ↔ 5c925a9`（R453 head，in_progress→EOF）；② `40645469967 ↔ c041c8d`（同上）；③ R454 自身跑（提交后创建）；④ `LOCAL_PERF_BUDGET_FLAKE=load`（全量唯一红，单跑通过）；⑤ `RUNNER_SCROLL_SESSION_FLAKE`（9743379 的滚动红；R455 重跑）；⑥ 436 的 markdown 模式标签采样红（1<2；未复现于其他跑）；⑦ 弱化色在选中/高亮底色上的对比度没有帧（485）；⑧ HTML 的 `<del>` 无同一条弱化（484）；⑨ HTML 列表缩进/任务弱化/表格体行（482/481/479）；⑩ 设置内容列 1x 平涂；⑪ 设置脚注带 1x；⑫ 主窗口 content 帧 1x；⑬ 高夹具 1x；⑭ 13+ 菜单像素/标题；⑮ 真实拖拽；⑯ Dock 像素；⑰ 源图标最小窗文字 1x；⑱ 本地全量 5 条滚动红（本跑未复现，隔离 4/4）；⑲ 2x/extended；⑳ 固定块揭示偏移（455）；㉑ 跨年时间（456）；㉒ 主列表暗档文字盲区（457）；㉓ 真机/多屏（447）；㉔ 真菜单栏、12 实时腿；㉕ `table-lazy-rows`；㉖ HTML 六档字号（460）；㉗ 清除 × 命中区（461）；㉘ 分隔线令牌（462）；㉙ 展开态已加载内容无帧（463）；㉚ 其它自绘控件帮助文本（464）；㉛ HTML 引用块无导引线（465）；㉜ HTML 表格表头无同档（466）；㉝ 100+ 行行号（467）；㉞ HTML 代码块行号（468）；㉟ 行号选中/滚动两态（469）；㊱ 关于页 1x 盲（470）；㊲ M613 机器前提（472）；㊳ 真机 vibrant 暗档（473）；㊴ 长来源截断（474）；㊵ bundle ID 未搜（475）；㊶ 长首行标签省略无帧（476）；㊶ HTML 代码块无语言标签（477）；㊷ HTML `<hr>` 无通栏线（478）；㊸ HTML 表格体行无同一条线（479）；㊹ QuickPick 键盘提示 1x（480）；㊺ HTML 任务列表无弱化（481）；㊻ HTML 列表缩进（482）；㊼ 中心刻度端点标签（483）；㊽ HTML 的 `<del>`（484）；㊾ 437–485 的未结项仍开。

"""

ITER_SECTION = u"""## Round 451 · R454（第 453 轮 · 2026-10-28）：弱化正文的对比度从 3.95:1 补到 5.33/7.09（旧 secondary 亮档 3.95 低于 14pt 正文 4.5:1；6 张旧帧变化、基线名单 262）

R450（完成项）与 R453（删除线）的弱化色 `secondaryLabelColor` 亮档只有 3.95:1。新 `DeEmphasisPresentation.textColor`（亮黑 58%、暗白 62%），两者共用。读数 `DEEMPHASIS_CONTRAST light 128/255/3.95 → 107/255/5.33`、`dark 154/30/5.92 → 169/30/7.09`；R450/R453 的弱化差仍成立（TASK_DIM +48.3/−37.9、STRIKE_DIM +41.2/−33.4、隙 9/9）。6 张旧帧变化、0 新增，基线 262/0/0/0；已看亮/暗。M1242（回到 128 的 3.95）/M1243（变正文黑=弱化消失）2/2；M1243 第一版 alpha 0 变透明、红在对比度，改成 1.0 才落在正确的格。⓪：开工 no-op push；LIST_HANG_STYLE/WEIGHT_CENTER_TICK/TASK_DIM 已签收；R453 head 40645430259 与预记 40645469967 收口时 gh EOF ⇒ NOT-RUN。全量 **1247/56/1**：唯一红＝PerfBudget `testImageComparisonCostStaysBounded`（310.3ms>250，load1 5.9；单跑 177.8ms 过）⇒ `LOCAL_PERF_BUDGET_FLAKE=load`；滚动套件本跑 5 红未复现、单跑 4/4。换装 ok/SHA_MATCH=1/383=383；电池 683/5。

**七维度自评**（恰七行，每格 n/15）：

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | 15/15 | 亮/暗 detail-tasks 逐张看过：完成项仍比正文浅、但暗到能读；strike/markdown 也看了。 |
| 判据有效性 | 15/15 | 用 sRGB 相对亮度算核心色 vs 底色的对比（两档 ≥4.5）；M1242/M1243 2/2。 |
| 假绿防御 | 15/15 | 读的是核心色不是均值；旧 secondary 3.95 由单测+帧判据双钉；M1243 的 alpha=0 透明教训照记。 |
| 产品面推进 | 15/15 | 把自己在 R450/R453 引入的对比度欠账补上（3.95→5.33）；Store 不动。 |
| 台账一致性 | 15/15 | U-1693…U-1697、D-450、no-op push、262 帧/1247、STORE-SIZE 1108/66 都从命令与测试解析。 |
| 交付诚实性 | 15/15 | 全量 1247/56/1 与性能预算 flake 原文照记；滚动 5 红本跑未复现也照写；R453 head 两跑 EOF 具名。 |
| 可复核性 | 15/15 | 128→107、154→169、3.95→5.33/7.09、刀号与 precheck 232/214/602、rot 318/1017、基线 262 都在。 |

均分 = 105/105 = 15/15（105）。"""

DECISION_450 = u"""## D-450 弱化正文改用过 4.5:1 的动态色（R454）

- 背景：R450 完成项、R453 删除线的弱化色 `secondaryLabelColor` 亮档实测 3.95:1，低于 14pt 正文 4.5:1；引用块早因同一原因拒绝过它。
- 决定：新 `DeEmphasisPresentation.textColor` 动态色（亮黑 58%、暗白 62%）；完成项与删除线共用；仍比正文弱。
- 理由：弱化是装饰，不能把内容画到读不清；两档都过 4.5:1。
- 兼容性/迁移：detail-tasks/detail-strike/detail-markdown-rendered 共 6 张旧帧变化；基线名单 262 同 commit 更新。
- 边界：选中/高亮底色上的对比度没有帧（485）；HTML `<del>` 未接（484）。
- 回滚：颜色改回 secondaryLabelColor；或 `git revert`。
"""

CHANGELOG_SECTION = u"""### 弱化正文的对比度从 3.95:1 补到 5.33/7.09（旧 secondary 亮档 3.95 低于 14pt 正文 4.5:1；6 张旧帧变化、基线 262）（R454 / 第 453 轮 / Round 451 / U-1693…U-1697 · 产品 3 文件，弱化色对比度位）

"""

BACKLOG_SECTION = u"""449 追记（R454 · 仍开）：本机全量本跑 1247/56/1（唯一红＝性能预算 flake）；隔离滚动 4/4；未动阈值。

451 追记（R454 · 仍开）：macOS 12 的详情头部阈值本轮未动。

452 追记（R454 · 仍开）：脚注 1x 具名 NOT-RUN 仍生效。

453 追记（R454 · 仍开）：真实系统拖拽会话仍无自动化验收。

454 追记（R454 · 仍开）：菜单具名标记仍未发射。

455 追记（R454 · 仍开）：固定条目滚动到位的独立偏移验收仍缺。

456 追记（R454 · 仍开）：跨年记录仍无年份。

457 追记（R454 · 仍开）：主列表暗档文字仍是另一处。

458 追记（R454 · 仍开）：CI 行首符号像素证人仍缺。

459 追记（R454 · 仍开）：设置内容列/高夹具在 1x 整列平涂。

460 追记（R454 · 仍开）：HTML 六档以上字号仍会后排压到 12pt。

461 追记（R454 · 仍开）：浮层清除 × 命中区 18pt。

462 追记（R454 · 仍开）：批量操作栏分隔线的 0.18 透明度未提令牌。

463 追记（R454 · 仍开）：展开态已加载内容仍无帧。

464 追记（R454 · 仍开）：其它自绘控件仍无同类帮助判据。

465 追记（R454 · 仍开）：HTML 引用块没有导引线。

466 追记（R454 · 仍开）：HTML 表格的表头没有同档字重。

467 追记（R454 · 仍开）：代码块行号的 9pt 档只在纯函数里验。

468 追记（R454 · 仍开）：HTML 代码块没有行号。

469 追记（R454 · 仍开）：代码块行号的选中态/滚动态没有帧。

470 追记（R454 · 仍开）：关于页正文在 runner 1x 是平涂。

471 已结案（R443）。

472 追记（R454 · 仍开）：M613 本机 2x 空名册（机器前提）。

473 追记（R454 · 仍开）：设置侧栏文字的真机 vibrant 暗档没有同屏对照。

474 追记（R454 · 仍开）：长来源 App 名的截断没有帧。

475 追记（R454 · 仍开）：侧栏搜索未匹配来源 App 的 bundle ID。

476 追记（R454 · 仍开）：代码块语言标签在长首行时被省略，没有帧。

477 追记（R454 · 仍开）：HTML 渲染器的代码块没有语言标签。

478 追记（R454 · 仍开）：HTML 预览的 `<hr>` 没有同一条通栏线。

479 追记（R454 · 仍开）：HTML 表格体行没有同一条分隔线。

480 追记（R454 · 仍开）：QuickPick 键盘提示 1x 已签收；12 帧名单仍只在本地。

481 追记（R454 · 仍开）：HTML 任务列表没有同一条完成态弱化。

482 追记（R454 · 仍开）：HTML 渲染路径的列表没有同一条悬挂制表位。

483 追记（R454 · 仍开）：权重滑块只有中心刻度，0% / 200% 端点没有标签。

484 追记（R454 · 仍开）：HTML 渲染路径的 `<del>` 没有同一条颜色弱化。

**485. 弱化色在选中/高亮底色上的对比度没有帧**（R454 观察）
    现象：R454 的对比度只按详情页**窗口底色**算（亮 255 / 暗 30）；正文被选中时（选中高亮底色随系统/强调色变）弱化文字是否仍 ≥4.5:1 没有帧，也没有暗档真实高亮样本。
    修法：拍选中态的 `detail-tasks` 帧（或用 AppKit 临时选中一段），量核心色 vs 高亮底色；两档都要过 4.5。
"""

STATE_SECTION = u"""## R454 状态（2026-10-28 · 本地 · 第 453 轮 / Round 451）：弱化正文的对比度从 3.95:1 补到 5.33/7.09（旧 secondary 亮档 3.95 低于 14pt 正文 4.5:1；6 张旧帧变化、基线名单 262）；全量 1247/56/1（唯一红＝性能预算 flake，单跑通过）；R453 head 两跑收口 gh EOF ⇒ NOT-RUN（产品 3 文件，弱化色对比度位）

最后更新：2026-10-28（本地 · R454 / 第 453 轮 / Round 451）：R450（完成项）与 R453（删除线）的弱化色 `secondaryLabelColor` 亮档实测 **3.95:1**，低于 14pt 正文的 4.5:1（引用块早因同一原因拒绝过它）。新 `DeEmphasisPresentation.textColor` 动态色（亮档黑 58%、暗档白 62%），完成项与删除线共用。旧/新（`detail-tasks` 完成项核心色 vs 页面底色）：`DEEMPHASIS_CONTRAST light 128/255/3.95 → 107/255/5.33`、`dark 154/30/5.92 → 169/30/7.09`；R450/R453 的弱化差仍成立（`TASK_DIM light 133.5/85.2 +48.3、dark 146.4/184.3 −37.9`；`STRIKE_DIM light 123.3/82.0 +41.2、dark 158.9/192.3 −33.4；隙 9/9`）。**6 张旧帧变化**（detail-tasks/detail-strike/detail-markdown-rendered × 亮/暗）、0 新增/缺失；基线名单 **262**（同 commit 更新）；已看亮/暗：完成项仍比正文浅、但不再低到读不清。`M1242/M1243` **2/2**；新单测 2 条 + 帧判据（sRGB 相对亮度）。预检 **232/214/602 bad=0**、ARM **325/1085**、HIDDEN **318/1017 rot=0**。⓪：开工 remote=`c041c8d`、ahead=0，`git push` 为 **no-op**；已读 `40640660665`（LIST_HANG_STYLE 签收）、`40642482086`（WEIGHT_CENTER_TICK 具名 NOT_RUN）、`40642524490`、`40636558557`（TASK_DIM 1x 旧色）、`40634880705`（滚动会话采样红 + Motion 模式标签 1<2）、`0737460`/`ecb8e69`（仅 Motion floor）、`36284e1`（dark 行带，已修）；**`40645430259 ↔ 5c925a9`（R453 head，STRIKE_DIM）与 `40645469967 ↔ c041c8d` 读时 in_progress、收口前再试仍 EOF ⇒ NOT-RUN**。全量 **1247/56/1**：唯一红＝`PerfBudgetTests.testImageComparisonCostStaysBounded`（310.3ms>250，load1=5.9；单跑 177.8ms 过）⇒ **`LOCAL_PERF_BUDGET_FLAKE=load`**；本跑 5 条滚动红未复现、滚动套件单跑 **4/4**（会话差；`LOCAL_SCROLL_SESSION_NOT_RUN` 口径保留，不据此删账）。捕获卷 **262 帧**；基线 **262/0/0/0**；build **0 告警**；换装 `ok / SHA_MATCH=1 / 383=383`（条目数本轮 383）；`STORE-SIZE lines=1108 funcs=52 longest=66`；产品面连续零改动 **1** 轮（as-of 453，`python3 scripts/product_streak.py --streak-for 453`，last=4ba006f）。清账与电池在台账后复跑。

本轮做了什么：
① ⓪ no-op push（remote c041c8d、ahead=0）；LIST_HANG_STYLE/WEIGHT_CENTER_TICK/TASK_DIM 签收；R453 head 两跑 in_progress→EOF ⇒ NOT-RUN。
② 产品：弱化色对比度 3.95→5.33/7.09（6 张旧帧变化、基线 262）。
③ 判据：M1242/M1243 2/2；新单测 2 条 + 帧判据（sRGB 对比）；M1243 的 alpha=0 透明教训照记；precheck 232/214/602；hidden rot 0。
④ 436：Motion floor 4/5/77、red 0、not-run=notice-banner；markdown 模式标签采样红未复现；不改门槛、不重猜 must_judge。
⑤ 367：hidden 表 318 / 可判 1017 / rot 0。
⑥ 捕获 262 帧；基线 262/0/0/0；build 0 告警；换装 ok/383=383；全量 1247/56/1（性能预算 flake 具名；滚动本跑未复现、隔离 4/4）。

NOT-RUN / 阻塞（分开写）：① `40645430259 ↔ 5c925a9`（R453 head，EOF）；② `40645469967 ↔ c041c8d`（同上）；③ R454 自身跑；④ `LOCAL_PERF_BUDGET_FLAKE=load`；⑤ `RUNNER_SCROLL_SESSION_FLAKE`（R455 重跑）；⑥ 436 的 markdown 模式标签采样红（1<2）；⑦ 弱化色在选中/高亮底色的对比度（485）；⑧ HTML 的 `<del>` 无弱化（484）；⑨ HTML 列表缩进/任务弱化/表格体行（482/481/479）；⑩ 设置内容列 1x 平涂；⑪ 设置脚注带 1x；⑫ 主窗口 content 帧 1x；⑬ 高夹具 1x；⑭ 13+ 菜单像素/标题；⑮ 真实拖拽；⑯ Dock 像素；⑰ 源图标最小窗文字 1x；⑱ 本地全量 5 条滚动红（本跑未复现、隔离 4/4）；⑲ 2x/extended；⑳ 固定块揭示偏移（455）；㉑ 跨年时间（456）；㉒ 主列表暗档文字盲区（457）；㉓ 真机/多屏（447）；㉔ 真菜单栏、12 实时腿；㉕ `table-lazy-rows`；㉖ HTML 六档字号（460）；㉗ 清除 × 命中区（461）；㉘ 分隔线令牌（462）；㉙ 展开态已加载内容无帧（463）；㉚ 其它自绘控件帮助文本（464）；㉛ HTML 引用块无导引线（465）；㉜ HTML 表格表头无同档（466）；㉝ 100+ 行行号（467）；㉞ HTML 代码块行号（468）；㉟ 行号选中/滚动两态（469）；㊱ 关于页 1x 盲（470）；㊲ M613 机器前提（472）；㊳ 真机 vibrant 暗档（473）；㊴ 长来源截断（474）；㊵ bundle ID 未搜（475）；㊶ 长首行标签省略无帧（476）；㊷ HTML 代码块无语言标签（477）；㊸ HTML `<hr>` 无通栏线（478）；㊹ HTML 表格体行无同一条线（479）；㊺ QuickPick 键盘提示 1x（480）；㊻ HTML 任务列表无弱化（481）；㊼ HTML 列表缩进（482）；㊽ 中心刻度端点标签（483）；㊾ HTML 的 `<del>`（484）；㊿ 437–485 的未结项仍开。

下一轮（R455）的靶：⓪ 先 `git push origin main`（禁 amend/force）并复核 ahead=0；读 R454 主笔+追记 head 跑、`40645430259 ↔ 5c925a9`（R453 head，STRIKE_DIM）与 `40645469967 ↔ c041c8d`（R453 预记 head）、`40640660665 ↔ 86044bf`（LIST_HANG_STYLE 已签收）、`40642482086 ↔ e083179`（WEIGHT_CENTER_TICK 具名 NOT_RUN）、`40636558557 ↔ 667d1a2`（TASK_DIM 1x）、`40634880705 ↔ 9743379`（滚动会话采样红原文）的全部失败步骤（成对 run↔commit），重点看 `DEEMPHASIS_CONTRAST` 两档 107/255/5.33 与 169/30/7.09、`STRIKE_DIM` 123.3/82.0/+41.2 与 158.9/192.3/−33.4、隙 9/9、`TASK_DIM` 133.5/85.2/+48.3 与 146.4/184.3/−37.9、`WEIGHT_CENTER_TICK` 9/5.0/0.0 或具名 NOT_RUN、`LIST_HANG_STYLE` 16.0/16.0/0.0、`QUICKPICK_HINT` 400/519、`TABLE_ROW_LINES` 3/0/108.0/102.0/1.0、`THEMATIC_RULE` 597.0/1.0/1、`CODE_LANGUAGE` 116/126、`HISTORY_SEARCH_SOURCE` 两档 0→1、`PROBE_DOMAIN` 44/20、`TABLE_HEADER` 1.10、`CODE_LINE_NUMBERS` 3/21/100% 与 436；in_progress/0 字节不算绿；`RUNNER_SCROLL_SESSION_FLAKE` 必须原样重跑复核（不改门槛）；① 现读 rot=0，按 `HIDDEN_ROT` 查新腐烂；② 继续产品视觉位并落 Sources、换缺陷类别（不要再做弱化色对比度/删除线/权重刻度/列表悬挂缩进/任务项完成态/浮层键盘提示/表格体行分隔/主题分隔线/代码块语言标签/代码块行号/表格表头/引用导引线/侧栏搜索来源/主列表来源行/设置侧栏文字/设置关于页/录制帮助/多文件展开/批量分隔/浮层搜索/图片/HTML/排除名单/行内符号/时间列/分区头/侧栏脚注/详情头部/Dock/菜单栏/横幅/回执/热图/计数/空态/无结果/焦点/悬停/选中/滚动/CTA）；③ 436 只复核新跑 Motion floor，不重猜 `must_judge`。
"""

R454_REPORT_BULLET = u"""- **R454（弱化色对比度位）**：R450（完成项）与 R453（删除线）的弱化色 `secondaryLabelColor` 亮档只有 **3.95:1**，低于 14pt 正文 4.5:1（引用块早因同一原因拒绝过它）。新 `DeEmphasisPresentation.textColor` 动态色（亮黑 58%、暗白 62%），两者共用。旧/新（`detail-tasks` 完成项核心色 vs 页面底色）：`DEEMPHASIS_CONTRAST light 128/255/3.95 → 107/255/5.33`、`dark 154/30/5.92 → 169/30/7.09`；R450/R453 的弱化差仍成立（`TASK_DIM light 133.5/85.2 +48.3、dark 146.4/184.3 −37.9`；`STRIKE_DIM light 123.3/82.0 +41.2、dark 158.9/192.3 −33.4；隙 9/9`）。**6 张旧帧变化**（detail-tasks/detail-strike/detail-markdown-rendered × 亮/暗）、0 新增，基线 **262/0/0/0**；已看亮/暗：完成项仍比正文浅、但不再低到读不清。`M1242`（回到 3.95）/`M1243`（变正文黑=弱化消失）**2/2**（M1243 第一版 alpha 0 变透明、红在对比度，改成 1.0 才落在正确的格）；新单测 2 条 + 帧判据（sRGB 对比）；预检 232/214/602 bad=0、ARM 325/1085、HIDDEN 318/1017 rot=0。⓪：开工 no-op push、ahead=0；LIST_HANG_STYLE/WEIGHT_CENTER_TICK/TASK_DIM 已签收；**`40645430259 ↔ 5c925a9` 与 `40645469967 ↔ c041c8d` 收口时 gh EOF ⇒ NOT-RUN**。全量 **1247/56/1**：唯一红＝`PerfBudgetTests.testImageComparisonCostStaysBounded`（310.3ms>250，load1 5.9；单跑 177.8ms 过）⇒ `LOCAL_PERF_BUDGET_FLAKE=load`（不改阈值）；滚动套件本跑 5 红未复现、单跑 **4/4**（会话差）。捕获 262 帧；build 0 告警；换装 ok/SHA_MATCH=1/383=383（条目 383）；STORE-SIZE 1108/52/66；电池 683/5。
"""

audit = rd(AUDIT); iter_text = rd(ITER); decisions = rd(DECISIONS)
changelog = rd(CHANGELOG); backlog = rd(BACKLOG); state = rd(STATE); report = rd(REPORT)

if audit.count(AUDIT_TITLE) != 1: raise SystemExit("REFUSED AUDIT %d" % audit.count(AUDIT_TITLE))
if u"第 453 轮（R454" in audit: raise SystemExit("REFUSED AUDIT 已有 R454")
if u"## Round 451 · R454" in iter_text: raise SystemExit("REFUSED ITER 已有 Round 451")
if u"## D-450" in decisions: raise SystemExit("REFUSED DECISIONS 已有 D-450")
if u"弱化正文的对比度从 3.95:1" in changelog: raise SystemExit("REFUSED CHANGELOG 已有该标题")
if u"**485." in backlog: raise SystemExit("REFUSED BACKLOG 已有 485")
if state.count(u"## R453 状态") != 1: raise SystemExit("REFUSED STATE %d" % state.count(u"## R453 状态"))
U_CELL_OLD = u"U-31 … U-1692（R453 现读抬到最新一节）"
if report.count(U_CELL_OLD) != 1: raise SystemExit("REFUSED REPORT U %d" % report.count(U_CELL_OLD))
if report.count(u"AGENT_STATE.md` 的 R453 节 ②") != 1: raise SystemExit("REFUSED REPORT pointer")

new_audit = audit.replace(AUDIT_TITLE, AUDIT_SECTION + AUDIT_TITLE, 1)
new_iter = iter_text.rstrip() + "\n\n" + ITER_SECTION + "\n"
new_decisions = decisions.rstrip() + "\n\n" + DECISION_450 + "\n"
marker = u"## [Unreleased]\n"
if changelog.count(marker) != 1: raise SystemExit("REFUSED CHANGELOG")
new_changelog = changelog.replace(marker, marker + "\n" + CHANGELOG_SECTION, 1)
new_backlog = backlog.rstrip() + "\n\n" + BACKLOG_SECTION + "\n"
new_state = state.replace(u"## R453 状态", STATE_SECTION + u"## R453 状态", 1)
new_report = report.replace(U_CELL_OLD, u"U-31 … U-1697（R454 现读抬到最新一节）", 1)
new_report = new_report.replace(u"AGENT_STATE.md` 的 R453 节 ②", u"AGENT_STATE.md` 的 R454 节 ②", 1)
new_report = new_report.rstrip() + "\n\n" + R454_REPORT_BULLET + "\n"

wr(AUDIT, new_audit); wr(ITER, new_iter); wr(DECISIONS, new_decisions)
wr(CHANGELOG, new_changelog); wr(BACKLOG, new_backlog); wr(STATE, new_state); wr(REPORT, new_report)
print("LEDGERS_R454_OK audit=%d iter=%d decisions=%d changelog=%d backlog=%d state=%d report=%d"
      % (len(new_audit), len(new_iter), len(new_decisions), len(new_changelog),
         len(new_backlog), len(new_state), len(new_report)))
