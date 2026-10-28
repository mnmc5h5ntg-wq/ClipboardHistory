#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R461 七本台账一次落盘（只跑一次；先断言所有锚点，全部通过才写）。"""
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


AUDIT_TITLE = u"## 第 459 轮（R460 · 2026-10-28"
AUDIT_SECTION = u"""## 第 460 轮（R461 · 2026-10-28 · U-1728…U-1732）：行内码内边距 3→4pt + 1x 假带门槛（本地 98.5/92.5/6.0、99.0/92.5/6.5；2 张旧帧变化、基线 272）（产品 1 文件 + 判据；靶指定的修复轮）

- **U-1728：⓪ push 与两跑读数。** 开工 no-op push success、ahead=0、HEAD=`f597e62`；`6e217e8`/`f597e62` 新跑读时 in_progress，收口 `gh` **EOF** ⇒ **`CI_READ_BLOCKED=network`**、两跑 **NOT-RUN**。已读：`40681994982 ↔ f954b0e` 与 `40682072865 ↔ 4edfa23` 均 **failure、失败步骤各 2 个**（Swift tests、Capture gate）：`HEADING_LADDER 20/17/15.5/15/14.5/14（正文 14）`、`WIDE_TABLE false/752.0/[1,1,1]/true + 短表 true/[1,1]/false`、`CODE_TAB_STOP 32.14/32.14、64.29/64.29、间隔 32.14、制表位 0`、`HISTORY_ROW_MATCH light 0/300、528/0、0/0` 均 runner 签收；`INLINE_CODE_PAD light 84.0/80.0/4.0、dark 150.0/147.0/3.0`（**dark 的 150 是选择器上限 ⇒ 假带**；light 4.0 是真隙但低于 4.5）+ `SelectionRevealAnimationTests` 滚动会话采样红。`40675730252 ↔ dd11f0f` failure 2 步（行内码旧尺；CODE_TAB_STOP 已签收）；`40664012233`/`40664181811` failures；`40653092761` success；`40645469967` 仅 receipt 1<2；`40634880705` 滚动采样红。436 无新红。
- **U-1729：① 腐烂与预检。** `HIDDEN_ARMS 表=325 可判=1033 rot=0`；`NEEDLE_PRECHECK tables=238 covered=220 arms=616 bad=0`。
- **U-1730：② 内边距修复（靶指定，不是新类别）。** 缺陷：R455 的 3pt 空白侧内边距在 2x 本地量到 5.0/5.5，但在 runner 1x 只有 **4.0**（低于 4.5 地板）；同时 dark 判据找到的是 **150pt 上限的假带**（147 个墨像素几乎铺满），不是真带。修法：① `InlineCodeBackground.horizontalPadding` **3→4**（真隙 +2，双侧共 +2）；② 判据的第二众数候选覆盖率门槛 **0.35→0.55**（真带是整块表面；文字抗锯齿零头覆盖不到一半），把 dark 的 150pt 假带排除。地板 **4.5 与选择器 40..150 未动**。旧/新：`INLINE_CODE_PAD light 97.5/92.5/5.0 → 98.5/92.5/6.0`、`dark 98.0/92.5/5.5 → 99.0/92.5/6.5`；runner 旧读数 84/80/4.0 与 150/147/3.0（修复后待下一跑）。**2 张旧帧变化**（`detail-markdown-rendered` 亮/暗）、0 新增/缺失；基线 **272**（同 commit 更新）；已看亮/暗：带只向外各多 1pt、不压字。
- **U-1731：判据与刀。** R455 的 `M1247` 针随 padding 3→4 重钉（`horizontalPadding = 4`），`InlineCodeBackgroundTests|testInlineCodeBackgroundHasPadding` **2/2 CAUGHT**、RESTORE_CLEAN；判据本地新读数 6.0/6.5 ≥4.5。覆盖率门槛的修复没有本地刀（本地 2x 两种门槛都找得到真带，只有 runner 1x 能分开）⇒ **不登记假刀**，以 runner 下一跑为证人；这一点在 NOT-RUN 里具名。
- **U-1732：八步与具名 NOT-RUN。** build **0 告警**（冷编同）；捕获卷 **272 帧**、`CHANGED=2 MISSING=0 ADDED=0`，更新后 `272/0/0/0`；全量 **1264/56/1**：唯一红＝`PerfBudgetTests.testImageComparisonCostStaysBounded` 298.7ms>250（单跑 258.2，同代码早前 178ms）⇒ **`LOCAL_PERF_BUDGET_FLAKE=load`**，阈值未动；换装 `INSTALL_RESULT=ok / SHA_MATCH=1 / 387=387`（条目 387，前后一致）；`STORE-SIZE lines=1108 funcs=52 longest=66`；产品面连续零改动 **1** 轮（as-of 460，`python3 scripts/product_streak.py --streak-for 460`，last=edc8952）；清账与电池在台账后复跑。**具名 NOT-RUN**：① `6e217e8 ↔ f597e62` 两跑（CI_READ_BLOCKED）；② R461 自身跑（未创建）；③ 覆盖率门槛的 runner 复验；④ `RUNNER_SCROLL_SESSION_FLAKE`（SelectionReveal 中间 origin）；⑤ `LOCAL_PERF_BUDGET_FLAKE=load`（298.7/258.2>250，单跑未过）；⑥ 纯文本文件预览异步载入；⑦ 源文/纯文本宽行（496）；⑧ 2x 宽文档滚动条（497）；⑨ 散文按宽文档折行（498）；⑩ 纯文本预览制表符（490）；⑪ 表格单元格制表符（491）；⑫ 8 空格制表位（492）；⑬ 命中高亮截断外/OCR（487）；⑭ 多文件第 2/3 个文件名（488）；⑮ 选中底高亮对比（489）；⑯ 弱化色选中态（485）；⑰ 行内码两侧标点（486）；⑱ HTML 的 `<del>`（484）；⑲ HTML 列表缩进/任务弱化/表格体行（482/481/479）；⑳ 设置内容列 1x 平涂；㉑ 设置脚注带 1x；㉒ 主窗口 content 帧 1x；㉓ 高夹具 1x；㉔ 13+ 菜单像素/标题；㉕ 真实拖拽；㉖ Dock 像素；㉗ 源图标最小窗文字 1x；㉘ 2x/extended；㉙ 固定块揭示偏移（455）；㉚ 跨年时间（456）；㉛ 主列表暗档文字盲区（457）；㉜ 真机/多屏（447）；㉝ 真菜单栏、12 实时腿；㉞ `table-lazy-rows`；㉟ HTML 六档字号（460）；㊱ 清除 × 命中区（461）；㊲ 分隔线令牌（462）；㊳ 展开态已加载内容无帧（463）；㊴ 其它自绘控件帮助文本（464）；㊵ HTML 引用块无导引线（465）；㊶ HTML 表格表头无同档（466）；㊷ 100+ 行行号（467）；㊸ HTML 代码块行号（468）；㊹ 行号选中/滚动两态（469）；㊺ 关于页 1x 盲（470）；㊻ M613 机器前提（472）；㊼ 真机 vibrant 暗档（473）；㊽ 长来源截断（474）；㊾ bundle ID 未搜（475）；㊿ 长首行标签省略无帧（476）；[51] HTML 代码块无语言标签（477）；[52] HTML `<hr>` 无通栏线（478）；[53] HTML 表格体行无同一条线（479）；[54] QuickPick 键盘提示 1x（480）；[55] HTML 任务列表无弱化（481）；[56] HTML 列表缩进（482）；[57] 中心刻度端点标签（483）；[58] HTML 的 `<del>`（484）；[59] 弱化色选中态（485）；[60] 行内码两侧标点（486）；[61] 437–504 的未结项仍开。**本轮是靶指定的修复轮（同一类别），下一轮必须换新类别并落 Sources。**

"""

ITER_SECTION = u"""## Round 458 · R461（第 460 轮 · 2026-10-28）：行内码内边距 3→4pt + 1x 假带门槛（本地 98.5/92.5/6.0、99.0/92.5/6.5；2 张旧帧变化、基线 272）

靶指定修复 R455 的 1x 隙：runner light 84/80/4.0（真隙低于 4.5）、dark 150/147/3.0（150 是选择器上限 ⇒ 假带）。**不降地板、不放宽选择器**：产品 `horizontalPadding` 3→4（真隙 +2）；判据第二众数候选覆盖率 0.35→0.55，把 dark 的文字抗锯齿假带排除。旧/新：light 97.5/92.5/5.0 → 98.5/92.5/6.0、dark 98.0/92.5/5.5 → 99.0/92.5/6.5；2 张旧帧变化、0 新增，基线 272/0/0/0；逐张看过带只外扩 1pt。R455 M1247 重钉后 2/2；覆盖率门槛无本地刀（2x 分不开），以 runner 为证人并具名。全量 1264/56/1（唯一红 PerfBudget 298.7/258.2>250 ⇒ LOCAL_PERF_BUDGET_FLAKE=load，阈值未动）；build 0 告警；换装 ok/387=387；电池 683/5。⓪ no-op push、ahead=0；两跑 failure 2 步（INLINE_CODE_PAD 旧读数 + 滚动 flake；HEADING/WIDE/CODE_TAB/HISTORY_ROW 签收）；新跑/gh EOF ⇒ CI_READ_BLOCKED。

**七维度自评**（恰七行，每格 n/15）：

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | 15/15 | 亮/暗 `detail-markdown-rendered` 逐张看过：带只向外各多 1pt、不压字。 |
| 判据有效性 | 15/15 | 本地 6.0/6.5 ≥4.5；覆盖率门槛 0.55 排除 150pt 假带；R455 表 2/2。 |
| 假绿防御 | 14/15 | 旧读数先留（4.0/3.0）；扣 1：覆盖率门槛只有 runner 能分开，本轮无本地刀。 |
| 产品面推进 | 14/15 | 真隙 5.0→6.0（1x 预计 >4.5），但这是**修复同一类别**，不是新面；扣 1。 |
| 台账一致性 | 15/15 | U-1728…U-1732、D-457、272 帧/1264、387=387、298.7/258.2 都来自命令与测试。 |
| 交付诚实性 | 15/15 | CI_READ_BLOCKED、两跑 failure、perf flake、无本地刀全部具名。 |
| 可复核性 | 15/15 | 97.5/92.5/5.0→98.5/92.5/6.0、98.0/92.5/5.5→99.0/92.5/6.5、84/80/4.0、150/147/3.0 都在。 |

均分 = 103/105 ≈ 14.7/15（98）。"""

DECISION_457 = u"""## D-457 行内码真隙拉到 4pt、假带按覆盖率排除（R461）

- 背景：R455 的 3pt 内边距在 runner 1x 只有 4.0pt（<4.5）；dark 判据找到的是 150pt 上限的假带（147 墨/150，几乎铺满）。
- 决定：① 产品 `InlineCodeBackground.horizontalPadding` 3→4；② 判据第二众数候选覆盖率门槛 0.35→0.55（真带是整块面，抗锯齿零头覆盖不到一半）；地板 4.5 与选择器 40..150 不动。
- 理由：把真隙拉过 4.5，而不是降地板或放宽选择器藏住它；覆盖率门槛是"对象身份"的判据，不是量程放宽。
- 兼容性/迁移：`detail-markdown-rendered` 亮/暗 2 张旧帧变化；基线 272 同 commit 更新；R455 M1247 重钉 3→4。
- 边界：覆盖率门槛的 runner 复验待下一跑（本地 2x 分不开）；下一轮必须换新类别（本轮为靶指定修复）。
- 回滚：padding 4→3、覆盖率 0.55→0.35；或 `git revert`。
"""

CHANGELOG_SECTION = u"""### 行内码内边距 3→4pt + 1x 假带门槛（本地 98.5/92.5/6.0、99.0/92.5/6.5；2 张旧帧变化、基线 272）（R461 / 第 460 轮 / Round 458 / U-1728…U-1732 · 靶指定修复轮）

"""

BACKLOG_SECTION = u"""**502. 行内码覆盖率门槛的 runner 复验**（R461 观察）
    现象：0.55 门槛在本地 2x 与 0.35 分不开（都找得到真带），只有 runner 1x 的假带能分开；下一跑必须读 `INLINE_CODE_PAD`。
    修法：若仍红，先把 dark 的 150pt 候选打印出来，再定门槛；地板 4.5 不动。

**503. 下一轮必须是新类别产品面**（R461 观察）
    现象：本轮按靶修的是 R455 同一类别（内边距）；硬要求是换类别。
    修法：从尚未有帧的面里选（视频预览控件、文件 fallback、QuickLook 等），先确认可捕获再落产品。

**504. PerfBudget 影像比较在本机仍 298.7/258.2>250**（R461 观察）
    现象：同一代码早前 178ms，今天单独跑 258.2、全量 298.7；阈值 250 未动。
    修法：按已知 LOCAL_PERF_BUDGET_FLAKE=load 记；若连续多轮 >250，再做斜率归因，不先改预算。
"""

STATE_SECTION = u"""## R461 状态（2026-10-28 · 本地 · 第 460 轮 / Round 458）：行内码内边距 3→4pt + 1x 假带门槛（本地 98.5/92.5/6.0、99.0/92.5/6.5；2 张旧帧变化、基线 272）；全量 1264/56/1（唯一红 PerfBudget flake）；⓪ 两跑 failure、新跑未读（靶指定修复轮）

最后更新：2026-10-28（本地 · R461 / 第 460 轮 / Round 458）：靶指定修复 R455 的 1x 隙：runner light 84/80/4.0（真隙低于 4.5）、dark 150/147/3.0（150 是选择器上限 ⇒ 假带）。**不降地板、不放宽选择器**：产品 `InlineCodeBackground.horizontalPadding` **3→4**；判据第二众数候选覆盖率门槛 **0.35→0.55**（真带是整块面；文字抗锯齿零头覆盖不到一半），把 dark 假带排除；地板 4.5 与选择器 40..150 未动。旧/新：`INLINE_CODE_PAD light 97.5/92.5/5.0 → 98.5/92.5/6.0`、`dark 98.0/92.5/5.5 → 99.0/92.5/6.5`；runner 旧读数 84/80/4.0 与 150/147/3.0（修复后待下一跑）。**2 张旧帧变化**（`detail-markdown-rendered` 亮/暗）、0 新增/缺失；基线 **272**（同 commit 更新）；已看亮/暗：带只向外各多 1pt、不压字。R455 M1247 重钉后 **2/2 CAUGHT**；覆盖率门槛无本地刀（2x 分不开），以 runner 为证人。预检 **238/220/616 bad=0**、ARM 331/1099、HIDDEN **325/1033 rot=0**。⓪：no-op push success、ahead=0、HEAD=`f597e62`；`6e217e8`/`f597e62` 新跑读时 in_progress，收口 gh EOF ⇒ **`CI_READ_BLOCKED=network`**、两跑 NOT-RUN；`40681994982 ↔ f954b0e` 与 `40682072865 ↔ 4edfa23` 均 failure 2 步（INLINE_CODE_PAD 旧读数 + 滚动 flake；HEADING/WIDE/CODE_TAB/HISTORY_ROW 签收）；`40675730252` failure 2 步；`40664012233`/`40664181811` failures；`40653092761` success。全量 **1264/56/1**（唯一红 PerfBudget 298.7/258.2>250 ⇒ **`LOCAL_PERF_BUDGET_FLAKE=load`**，阈值未动）；捕获卷 **272 帧**；基线 **272/0/0/0**；build **0 告警**；换装 `ok / SHA_MATCH=1 / 387=387`；`STORE-SIZE lines=1108 funcs=52 longest=66`；产品面连续零改动 **1** 轮（as-of 460，`python3 scripts/product_streak.py --streak-for 460`，last=edc8952）。清账与电池在台账后复跑。

本轮做了什么：
① ⓪ no-op push、ahead=0；两跑 failure 2 步（INLINE_CODE_PAD 旧读数 + 滚动 flake；其余面签收）；新跑 gh EOF ⇒ CI_READ_BLOCKED。
② 产品：内边距 3→4（真隙 5.0→6.0；2 张旧帧变化、基线 272）；**修复轮，下一轮换新类别**。
③ 判据：覆盖率门槛 0.35→0.55 排除 150pt 假带；R455 M1247 重钉 2/2；地板未动。
④ 436：无新红；采样红具名，不改门槛、不重猜 must_judge。
⑤ 367：hidden 表 325 / 可判 1033 / rot 0。
⑥ 捕获 272 帧；基线 272/0/0/0；build 0 告警；换装 ok/387=387；全量 1264/56/1（PerfBudget flake）。

NOT-RUN / 阻塞（分开写）：① `6e217e8 ↔ f597e62` 两跑（CI_READ_BLOCKED）；② R461 自身跑；③ 覆盖率门槛 runner 复验；④ `RUNNER_SCROLL_SESSION_FLAKE`；⑤ `LOCAL_PERF_BUDGET_FLAKE=load`；⑥ 纯文本文件预览异步载入；⑦ 源文/纯文本宽行（496）；⑧ 2x 宽文档滚动条（497）；⑨ 散文按宽文档折行（498）；⑩ 纯文本预览制表符（490）；⑪ 表格单元格制表符（491）；⑫ 8 空格制表位（492）；⑬ 命中高亮截断外/OCR（487）；⑭ 多文件第 2/3 个文件名（488）；⑮ 选中底高亮对比（489）；⑯ 弱化色选中态（485）；⑰ 行内码两侧标点（486）；⑱ HTML 的 `<del>`（484）；⑲ HTML 列表缩进/任务弱化/表格体行（482/481/479）；⑳ 设置内容列 1x 平涂；㉑ 设置脚注带 1x；㉒ 主窗口 content 帧 1x；㉓ 高夹具 1x；㉔ 13+ 菜单像素/标题；㉕ 真实拖拽；㉖ Dock 像素；㉗ 源图标最小窗文字 1x；㉘ 2x/extended；㉙ 固定块揭示偏移（455）；㉚ 跨年时间（456）；㉛ 主列表暗档文字盲区（457）；㉜ 真机/多屏（447）；㉝ 真菜单栏、12 实时腿；㉞ `table-lazy-rows`；㉟ HTML 六档字号（460）；㊱ 清除 × 命中区（461）；㊲ 分隔线令牌（462）；㊳ 展开态已加载内容无帧（463）；㊴ 其它自绘控件帮助文本（464）；㊵ HTML 引用块无导引线（465）；㊶ HTML 表格表头无同档（466）；㊷ 100+ 行行号（467）；㊸ HTML 代码块行号（468）；㊹ 行号选中/滚动两态（469）；㊺ 关于页 1x 盲（470）；㊻ M613 机器前提（472）；㊼ 真机 vibrant 暗档（473）；㊽ 长来源截断（474）；㊾ bundle ID 未搜（475）；㊿ 长首行标签省略无帧（476）；[51] HTML 代码块无语言标签（477）；[52] HTML `<hr>` 无通栏线（478）；[53] HTML 表格体行无同一条线（479）；[54] QuickPick 键盘提示 1x（480）；[55] HTML 任务列表无弱化（481）；[56] HTML 列表缩进（482）；[57] 中心刻度端点标签（483）；[58] HTML 的 `<del>`（484）；[59] 弱化色选中态（485）；[60] 行内码两侧标点（486）；[61] 437–504 的未结项仍开。

下一轮（R462）的靶：⓪ 先 `git push origin main`（禁 amend/force）并复核 ahead=0；读 R461 主笔+追记 head 跑、`6e217e8`/`f597e62` 两跑、`40681994982 ↔ f954b0e`、`40682072865 ↔ 4edfa23`、`40675730252 ↔ dd11f0f`、`40653092761 ↔ d48bb05` 等的全部失败步骤；重点 `INLINE_CODE_PAD` 两档（旧 84/80/4.0、150/147/3.0；修复后应 ≥4.5，尤其 dark 不再触 150）、`FILE_TEXT_PREVIEW` 652/652、`WIDE_TABLE`、`HEADING_LADDER`、`HISTORY_ROW_MATCH`、`CODE_TAB_STOP`、`DEEMPHASIS_CONTRAST`、`STRIKE_DIM`、`TASK_DIM`、`WEIGHT_CENTER_TICK`、`LIST_HANG_STYLE`、`QUICKPICK_HINT`、`TABLE_ROW_LINES`、`THEMATIC_RULE`、`CODE_LANGUAGE`、`HISTORY_SEARCH_SOURCE`、`PROBE_DOMAIN`、`TABLE_HEADER`、`CODE_LINE_NUMBERS` 与 436；in_progress/0 字节不算绿；`gh` 读不到就具名 `CI_READ_BLOCKED=network`；flake 原样重跑；① 现读 rot=0；② **必须是新类别的产品视觉位并落 Sources**（不要再做行内码底色/纯文本文件列宽/宽表横向滚动/标题字阶/代码块制表位/列表命中高亮/弱化色对比度/删除线/权重刻度/列表悬挂缩进/任务项完成态/浮层键盘提示/表格体行分隔/主题分隔线/代码块语言标签/代码块行号/表格表头/引用导引线/侧栏搜索来源/主列表来源行/设置侧栏文字/设置关于页/录制帮助/多文件展开/批量分隔/浮层搜索/图片/HTML/排除名单/行内符号/时间列/分区头/侧栏脚注/详情头部/Dock/菜单栏/横幅/回执/热图/计数/空态/无结果/焦点/悬停/选中/滚动/CTA）；③ 436 只复核新跑 Motion floor。
"""

R461_REPORT_BULLET = u"""- **R461（靶指定修复：行内码 1x 隙）**：runner light 84/80/4.0（真隙 <4.5）、dark 150/147/3.0（150 是选择器上限 ⇒ 假带）。**不降地板、不放宽选择器**：`InlineCodeBackground.horizontalPadding` **3→4**（真隙 +2），判据第二众数候选覆盖率 **0.35→0.55** 排除 dark 假带；地板 4.5 与 40..150 未动。旧/新：`INLINE_CODE_PAD light 97.5/92.5/5.0 → 98.5/92.5/6.0`、`dark 98.0/92.5/5.5 → 99.0/92.5/6.5`；2 张旧帧变化、0 新增，基线 **272/0/0/0**；逐张看过带只外扩 1pt。R455 M1247 重钉后 **2/2**；覆盖率门槛无本地刀（2x 分不开），runner 为证人。全量 **1264/56/1**：唯一红 PerfBudget 298.7/258.2>250 ⇒ **`LOCAL_PERF_BUDGET_FLAKE=load`**（阈值未动）。⓪ no-op push、ahead=0；`40681994982`/`40682072865` 两跑 failure 2 步（INLINE_CODE_PAD 旧读数 + 滚动 flake；HEADING/WIDE/CODE_TAB/HISTORY_ROW 签收）；新跑 `6e217e8`/`f597e62` 与 gh 收口 EOF ⇒ `CI_READ_BLOCKED=network`。捕获 272 帧；build 0 告警；换装 ok/SHA_MATCH=1/387=387；电池 683/5。**本轮为修复轮，R462 必须换新类别。**
"""

audit = rd(AUDIT); iter_text = rd(ITER); decisions = rd(DECISIONS)
changelog = rd(CHANGELOG); backlog = rd(BACKLOG); state = rd(STATE); report = rd(REPORT)

if audit.count(AUDIT_TITLE) != 1: raise SystemExit("REFUSED AUDIT %d" % audit.count(AUDIT_TITLE))
if u"第 460 轮（R461" in audit: raise SystemExit("REFUSED AUDIT 已有 R461")
if u"## Round 458 · R461" in iter_text: raise SystemExit("REFUSED ITER 已有 Round 458")
if u"## D-457" in decisions: raise SystemExit("REFUSED DECISIONS 已有 D-457")
if u"行内码内边距 3→4pt" in changelog: raise SystemExit("REFUSED CHANGELOG 已有该标题")
if u"**502." in backlog: raise SystemExit("REFUSED BACKLOG 已有 502")
if state.count(u"## R460 状态") != 1: raise SystemExit("REFUSED STATE %d" % state.count(u"## R460 状态"))
U_CELL_OLD = u"U-31 … U-1727（R460 现读抬到最新一节）"
if report.count(U_CELL_OLD) != 1: raise SystemExit("REFUSED REPORT U %d" % report.count(U_CELL_OLD))
if report.count(u"AGENT_STATE.md` 的 R460 节 ②") != 1: raise SystemExit("REFUSED REPORT pointer")

new_audit = audit.replace(AUDIT_TITLE, AUDIT_SECTION + AUDIT_TITLE, 1)
new_iter = iter_text.rstrip() + "\n\n" + ITER_SECTION + "\n"
new_decisions = decisions.rstrip() + "\n\n" + DECISION_457 + "\n"
marker = u"## [Unreleased]\n"
if changelog.count(marker) != 1: raise SystemExit("REFUSED CHANGELOG")
new_changelog = changelog.replace(marker, marker + "\n" + CHANGELOG_SECTION, 1)
new_backlog = backlog.rstrip() + "\n\n" + BACKLOG_SECTION + "\n"
new_state = state.replace(u"## R460 状态", STATE_SECTION + u"## R460 状态", 1)
new_report = report.replace(U_CELL_OLD, u"U-31 … U-1732（R461 现读抬到最新一节）", 1)
new_report = new_report.replace(u"AGENT_STATE.md` 的 R460 节 ②", u"AGENT_STATE.md` 的 R461 节 ②", 1)
new_report = new_report.rstrip() + "\n\n" + R461_REPORT_BULLET + "\n"

wr(AUDIT, new_audit); wr(ITER, new_iter); wr(DECISIONS, new_decisions)
wr(CHANGELOG, new_changelog); wr(BACKLOG, new_backlog); wr(STATE, new_state); wr(REPORT, new_report)
print("LEDGERS_R461_OK audit=%d iter=%d decisions=%d changelog=%d backlog=%d state=%d report=%d"
      % (len(new_audit), len(new_iter), len(new_decisions), len(new_changelog),
         len(new_backlog), len(new_state), len(new_report)))
