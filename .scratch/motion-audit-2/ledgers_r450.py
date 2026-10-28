#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R450 七本台账一次落盘（只跑一次；先断言所有锚点，全部通过才写）。"""
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


AUDIT_TITLE = u"## 第 448 轮（R449 · 2026-10-28"
AUDIT_SECTION = u"""## 第 449 轮（R450 · 2026-10-28 · U-1673…U-1677）：已完成任务项的正文弱一档（逐字相同的两行：亮 148.3 vs 85.1、暗 136.0 vs 184.7；2 张新帧 + 2 张旧帧变化、基线 256→258）（产品 2 文件，任务项完成态位）

- **U-1673：⓪ push 与六跑。** 开工 remote=`224b8ee`、ahead=2，一次快进 push **`224b8ee..9743379` success**（预记 80c9516 + 补记 9743379），HEAD=origin/main=`9743379`、**ahead=0**。`gh run list`：**`40634880705 ↔ 9743379`** 与 **`40632882239 ↔ 224b8ee`** 读时 **in_progress**；随后 `gh` 列表/单跑均 **EOF** ⇒ 这两跑（含 R449 的 `QUICKPICK_HINT` 1x 读数）**NOT-RUN**，R451 ⓪ 必读。已读：**`40629867848 ↔ 107f2b3` success**，同跑读数 `TABLE_ROW_LINES light/dark 3/0/108.0/102.0/1.0`、`THEMATIC_RULE 597.0/1.0/1`、`CODE_LANGUAGE 116/126`、`HISTORY_SEARCH_SOURCE light 1/3、dark 1/1`（+ dark `NOT_RUN 行带=1`）、`HISTORY_ROW_SOURCE 139.0/74.0 差 65.0 左 97.0/97.0`、`SETTINGS_ABOUT_ROW 7/7`、`CODE_LINE_NUMBERS 54.0/3/21.0/100%`、`TABLE_HEADER 1.10`、`PROBE_DOMAIN 44/20`；**`40629776895 ↔ 0737460` failure，唯一失败步＝Motion coverage floor**，原文 `MOTION_FLOOR_FACTS judged=5/5 executed=77`、`MOTION_FLOOR_SUITE_RED=1`＝`testMarkdownModeLabelChangeIsAVisibleProcess`（1x 只有 1 个过渡帧，要 ≥2；采样红、未登记）；`40623613789 ↔ ecb8e69` failure 仅 Motion floor（`testCopyReceipt...` 1<2）；`40620912699 ↔ 36284e1` failure 1 步（dark 行带，已修）、`40617745753 ↔ fe956e3` failure 2 步、`40613782362 ↔ eeccad0` failure 1 步。436 只复核 Motion floor：107f2b3 整跑 success（同代码的 motion 卷通过），0737460/ecb8e69 的红分别是 markdown 模式标签与回执采样、均未在 107f2b3 复现；不改门槛、不重猜 `must_judge`。
- **U-1674：① 腐烂与预检。** `HIDDEN_ARMS 表=314 可判=1009 rot=0`；`NEEDLE_PRECHECK tables=228 covered=210 arms=594 bad=0`、`ARM_TOTAL files=321 arms=1077`。本轮改的是 Markdown 呈现层的颜色分支，没有弄断旧针。
- **U-1675：② 已完成任务项的正文弱化。** 缺陷形状：勾选态只落在 `☑`/`☐` 两个小字形上，正文与未完成项同色同重 —— 扫一份清单分不出做完的。修法：新 `TaskItemPresentation` 纯策略（`dimsText`、`completedTextColor = secondaryLabelColor`）；`MarkdownPresentation.attributes(for:in:dimmed:)` 对完成项文字降一档（**可点链接仍保留链接色**，不造假 affordance），`appendRuns` 透传，`.unorderedItem` 只在 `.checked` 时 `dimmed`。旧/新（逐字相同的两行 `待办事项`，x 40..300 排除标记）：`TASK_DIM light 勾选=148.3 未勾选=85.1 差=+63.2 墨数=1149/1269`、`dark 136.0/184.7 差=-48.7 墨数=1287/1393`（两行墨数比 1.10，证明差来自颜色）；`☑`/`☐` 标记与 `visibleText` 不动。夹具 `detail-tasks`（一勾一未勾、正文逐字相同）；**2 张新帧、2 张旧帧变化**（`detail-markdown-rendered` 亮/暗的已完成项「解析层完成」也变灰），基线 **256→258 / 0/0/0**；已看亮/暗两行对比与 markdown 样例，完成项退后、未完成项保持主色。Store 未动（1108 行/52 方法/最长 66）。
- **U-1676：判据与刀。** 新单测 `TaskItemPresentationTests` 3 条（只有 checked 弱化；属性串里两行文字色不同；标记与 `visibleText` 不变）+ 帧判据 `testCheckedTasksDimTheirText`（两行正文墨像素平均灰度差：亮 ≥+20、暗 ≤−20；两行墨数比 ≤1.25）。`M1234`（完成项不弱化）⇒ 单测+帧判据 CAUGHT；`M1235`（两条都弱化）⇒ 同上 CAUGHT ⇒ **2/2**、RESTORE_CLEAN=yes。
- **U-1677：八步与具名 NOT-RUN。** build **0 告警**（`ROUND_WARNING_GATE warnings=0 incremental=0 cold=0 target=build-tests`）；捕获卷 **258 帧**、`COMPARED=258 CHANGED=0 MISSING=0 ADDED=0`；全量 **1234/57/5**（5 个断言全在 `SelectionRevealAnimationTests`）；单跑 `caffeinate -u` **4/4** ⇒ `LOCAL_SCROLL_SESSION_NOT_RUN=full-suite-order`（449）；换装 `INSTALL_RESULT=ok / SHA_MATCH=1 / 381=381`；`STORE-SIZE lines=1108 funcs=52 longest=66`；产品面连续零改动 **1** 轮（as-of 449，`python3 scripts/product_streak.py --streak-for 449`，last=07fcd2f）；清账与电池在台账后复跑。**具名 NOT-RUN**：① `40634880705 ↔ 9743379`（in_progress 后 gh EOF）；② `40632882239 ↔ 224b8ee`（含 `QUICKPICK_HINT` 1x；同上）；③ R450 自身跑（提交后创建）；④ 436 新跑 Motion floor（107f2b3 success；两个采样红未复现）；⑤ HTML 任务列表没有同一条完成态弱化（481）；⑥ HTML 表格体行无同一条线（479）；⑦ 设置内容列 1x 平涂；⑧ 设置脚注带 1x；⑨ 主窗口 content 帧 1x；⑩ 高夹具 1x；⑪ 13+ 菜单像素/标题；⑫ 真实拖拽；⑬ Dock 像素；⑭ 源图标最小窗文字 1x；⑮ 本地全量 5 条滚动红（449）；⑯ 2x/extended；⑰ 固定块揭示偏移（455）；⑱ 跨年时间（456）；⑲ 主列表暗档文字盲区（457）；⑳ 真机/多屏（447）；㉑ 真菜单栏、12 实时腿；㉒ `table-lazy-rows`；㉓ HTML 六档字号（460）；㉔ 清除 × 命中区（461）；㉕ 分隔线令牌（462）；㉖ 展开态已加载内容无帧（463）；㉗ 其它自绘控件帮助文本（464）；㉘ HTML 引用块无导引线（465）；㉙ HTML 表格表头无同档（466）；㉚ 100+ 行行号（467）；㉛ HTML 代码块行号（468）；㉜ 行号选中/滚动两态（469）；㉝ 关于页 1x 盲（470）；㉞ M613 机器前提（472）；㉟ 真机 vibrant 暗档（473）；㊱ 长来源截断（474）；㊲ bundle ID 未搜（475）；㊳ 长首行标签省略无帧（476）；㊴ HTML 代码块无语言标签（477）；㊵ HTML `<hr>` 无通栏线（478）；㊶ HTML 表格体行无同一条线（479）；㊷ QuickPick 键盘提示 1x 读数（480）；㊸ 437–481 的未结项仍开。

"""

ITER_SECTION = u"""## Round 447 · R450（第 449 轮 · 2026-10-28）：已完成任务项的正文弱一档（逐字相同的两行：亮 148.3 vs 85.1、暗 136.0 vs 184.7；2 张新帧 + 2 张旧帧变化、基线 256→258）

勾选态只落在 ☑/☐ 小字形上，正文与未完成项同色。新 `TaskItemPresentation`（只有 checked 弱化、`secondaryLabelColor`）；`attributes(for:in:dimmed:)` 对完成项文字降一档，链接仍保留链接色；`.unorderedItem` 只在 checked 时 dimmed。夹具 `detail-tasks`（一勾一未勾、正文逐字相同）：`TASK_DIM light 勾选=148.3 未勾选=85.1 差=+63.2 墨数=1149/1269`、`dark 136.0/184.7 差=-48.7 墨数=1287/1393`；标记与 visibleText 不动。2 张新帧 + 2 张旧帧变化（detail-markdown-rendered 的「解析层完成」也变灰），基线 258/0/0/0；已看亮/暗。M1234/M1235 2/2。⓪：push 224b8ee..9743379 success、ahead=0；107f2b3 跑 success（TABLE_ROW_LINES 3/0/108.0/102.0/1.0、THEMATIC_RULE 597/1/1、CODE_LANGUAGE 116/126、HISTORY_SEARCH_SOURCE 1/3 + dark NOT_RUN、HISTORY_ROW_SOURCE 139/74、SETTINGS_ABOUT_ROW 7/7、CODE_LINE_NUMBERS 54/3/21/100%、TABLE_HEADER 1.10、PROBE_DOMAIN 44/20）；0737460 跑 failure 仅 Motion floor（testMarkdownModeLabelChange 1<2）；40632882239/40634880705 in_progress 后 gh EOF ⇒ NOT-RUN。全量 1234/57/5（滚动具名）；捕获 258；换装 ok/SHA_MATCH=1/381=381；电池 683/5。

**七维度自评**（恰七行，每格 n/15）：

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | 15/15 | 亮/暗 detail-tasks 与 markdown 样例逐张看过：完成项退后、未完成项保持主色；不是只看数字。 |
| 判据有效性 | 15/15 | 两行逐字相同、只比正文墨像素平均灰度（亮 +、暗 −），墨数比 ≤1.25；标记与 visibleText 契约另有单测；M1234/M1235 2/2。 |
| 假绿防御 | 15/15 | 墨数比排除"少画字"；链接不弱化防假 affordance；旧形状（不弱化/都弱化）由两把刀钉住。 |
| 产品面推进 | 14/15 | 完成态第一次在正文上可见；Store 不动；扣 1：HTML 任务列表未覆盖（481）。 |
| 台账一致性 | 15/15 | U-1673…U-1677、D-446、push 9743379、258 帧/1234、STORE-SIZE 1108/66 都从命令与测试解析。 |
| 交付诚实性 | 15/15 | 两新跑 in_progress/EOF 具名；0737460 的 Motion 红原文（markdown 模式标签 1<2）照记；107f2b3 success 与采样红未复现并列写。 |
| 可复核性 | 15/15 | 148.3/85.1/+63.2、136.0/184.7/−48.7、墨数 1149/1269、刀号与 precheck 228/210/594、rot 314/1009、基线 258 都在。 |

均分 = 104/105 ≈ 14.9/15（99）。"""

DECISION_446 = u"""## D-446 已完成任务项的文字降一档，标记保留（R450）

- 背景：勾选态只落在 ☑/☐ 两个小字形上，正文与未完成项同色同重，扫清单分不出做完的。
- 决定：`TaskItemPresentation.dimsText(.checked)`；`attributes(for:in:dimmed:)` 把完成项文字降到 `secondaryLabelColor`；可点链接仍保留链接色；☑/☐ 与 `visibleText` 不动。
- 理由：完成态是任务项的主要内容状态；弱化正文让已完成项退后；链接可点性不能因弱化变假 affordance。
- 兼容性/迁移：新夹具 `detail-tasks`；`detail-markdown-rendered` 亮/暗因已完成项变灰而更新；基线 256→258。
- 边界：HTML 任务列表未接（481）。
- 回滚：`dimmed:` 传 false 或删 `TaskItemPresentation` 即可；或 `git revert`。
"""

CHANGELOG_SECTION = u"""### 已完成任务项的正文弱一档（逐字相同的两行：亮 148.3 vs 85.1、暗 136.0 vs 184.7；2 张新帧 + 2 张旧帧变化、基线 258）（R450 / 第 449 轮 / Round 447 / U-1673…U-1677 · 产品 2 文件，任务项完成态位）

"""

BACKLOG_SECTION = u"""449 追记（R450 · 仍开）：本机全量仍 5 断言红（3 条用例）、单跑 4/4 绿；未动阈值。

451 追记（R450 · 仍开）：macOS 12 的详情头部阈值本轮未动。

452 追记（R450 · 仍开）：脚注 1x 具名 NOT-RUN 仍生效。

453 追记（R450 · 仍开）：真实系统拖拽会话仍无自动化验收。

454 追记（R450 · 仍开）：菜单具名标记仍未发射。

455 追记（R450 · 仍开）：固定条目滚动到位的独立偏移验收仍缺。

456 追记（R450 · 仍开）：跨年记录仍无年份。

457 追记（R450 · 仍开）：主列表暗档文字仍是另一处。

458 追记（R450 · 仍开）：CI 行首符号像素证人仍缺。

459 追记（R450 · 仍开）：设置内容列/高夹具在 1x 整列平涂。

460 追记（R450 · 仍开）：HTML 六档以上字号仍会后排压到 12pt。

461 追记（R450 · 仍开）：浮层清除 × 命中区 18pt。

462 追记（R450 · 仍开）：批量操作栏分隔线的 0.18 透明度未提令牌。

463 追记（R450 · 仍开）：展开态已加载内容仍无帧。

464 追记（R450 · 仍开）：其它自绘控件仍无同类帮助判据。

465 追记（R450 · 仍开）：HTML 引用块没有导引线。

466 追记（R450 · 仍开）：HTML 表格的表头没有同档字重。

467 追记（R450 · 仍开）：代码块行号的 9pt 档只在纯函数里验。

468 追记（R450 · 仍开）：HTML 代码块没有行号。

469 追记（R450 · 仍开）：代码块行号的选中态/滚动态没有帧。

470 追记（R450 · 仍开）：关于页正文在 runner 1x 是平涂。

471 已结案（R443）。

472 追记（R450 · 仍开）：M613 本机 2x 空名册（机器前提）。

473 追记（R450 · 仍开）：设置侧栏文字的真机 vibrant 暗档没有同屏对照。

474 追记（R450 · 仍开）：长来源 App 名的截断没有帧。

475 追记（R450 · 仍开）：侧栏搜索未匹配来源 App 的 bundle ID。

476 追记（R450 · 仍开）：代码块语言标签在长首行时被省略，没有帧。

477 追记（R450 · 仍开）：HTML 渲染器的代码块没有语言标签。

478 追记（R450 · 仍开）：HTML 预览的 `<hr>` 没有同一条通栏线。

479 追记（R450 · 仍开）：HTML 表格体行没有同一条分隔线。

480 追记（R450 · 仍开）：QuickPick 键盘提示的 runner 1x 像素读数本轮仍未读（gh EOF）。

**481. HTML 渲染路径的任务列表没有同一条完成态弱化**（R450 观察）
    现象：R450 只弱化了 Markdown 渲染路径的已完成任务项文字；HTML 预览走 `NSAttributedString` 的 HTML 导入，任务列表（`<input type=checkbox>`/`<li>`）是另一条路径，没有同一条正文降档，也没有帧。
    修法：给 HTML 预览拍一张含 `[x]/[ ]` 或 checkbox 的帧，量完成项正文灰度；若导入器不给状态，则用同一 `TaskItemPresentation` 在 HTML 渲染路径补。
"""

STATE_SECTION = u"""## R450 状态（2026-10-28 · 本地 · 第 449 轮 / Round 447）：已完成任务项的正文弱一档（逐字相同的两行：亮 148.3 vs 85.1、暗 136.0 vs 184.7；2 张新帧 + 2 张旧帧变化、基线 256→258）；107f2b3 跑 success 签收 R448 的 TABLE_ROW_LINES/THEMATIC_RULE；两新跑 in_progress 后 gh EOF ⇒ CI_READ_BLOCKED（产品 2 文件，任务项完成态位）

最后更新：2026-10-28（本地 · R450 / 第 449 轮 / Round 447）：勾选态只落在 `☑`/`☐` 两个小字形上，正文与未完成项同色同重。新 `TaskItemPresentation` 纯策略（只有 checked 弱化、`secondaryLabelColor`）；`MarkdownPresentation.attributes(for:in:dimmed:)` 对完成项文字降一档（可点链接仍保留链接色），`appendRuns` 透传，`.unorderedItem` 只在 `.checked` 时 `dimmed`。旧/新（逐字相同的两行 `待办事项`，x 40..300 排除标记）：`TASK_DIM light 勾选=148.3 未勾选=85.1 差=+63.2 墨数=1149/1269`、`dark 136.0/184.7 差=-48.7 墨数=1287/1393`（墨数比 1.10）；`☑`/`☐` 与 `visibleText` 不动。夹具 `detail-tasks`；**2 张新帧、2 张旧帧变化**（`detail-markdown-rendered` 的「解析层完成」也变灰），基线 **256→258 / 0/0/0**；已看亮/暗。`M1234/M1235` **2/2**；新单测 3 条 + 帧判据；预检 **228/210/594 bad=0**、ARM **321/1077**、HIDDEN **314/1009 rot=0**。⓪：一次快进 push **`224b8ee..9743379` success**（两笔）、HEAD=origin/main=`9743379`、**ahead=0**；`gh run list` 读到 `40634880705 ↔ 9743379` 与 `40632882239 ↔ 224b8ee` 均 **in_progress**，随后 `gh` EOF ⇒ **`CI_READ_BLOCKED=network`**（两跑含 `QUICKPICK_HINT` 1x 读数 NOT-RUN）；**`40629867848 ↔ 107f2b3` success**，同跑 `TABLE_ROW_LINES 3/0/108.0/102.0/1.0`、`THEMATIC_RULE 597.0/1.0/1`、`CODE_LANGUAGE 116/126`、`HISTORY_SEARCH_SOURCE light 1/3、dark 1/1`+NOT_RUN、`HISTORY_ROW_SOURCE 139.0/74.0`、`SETTINGS_ABOUT_ROW 7/7`、`CODE_LINE_NUMBERS 54.0/3/21.0/100%`、`TABLE_HEADER 1.10`、`PROBE_DOMAIN 44/20`；**`40629776895 ↔ 0737460` failure 仅 Motion floor**（`judged=5/5 executed=77`、`testMarkdownModeLabelChangeIsAVisibleProcess` 1 帧<2，采样红、未登记）；`40623613789 ↔ ecb8e69` failure 仅 Motion floor（`testCopyReceipt...` 1<2）；`40620912699 ↔ 36284e1` failure 1 步（dark 行带，已修）。receipt/markdown 模式两个采样红都未在 107f2b3 复现；不改门槛、不重猜 `must_judge`。本地全量 **1234/57/5**（5 断言全在 `SelectionRevealAnimationTests`）；单跑 **4/4** ⇒ `LOCAL_SCROLL_SESSION_NOT_RUN=full-suite-order`（449）。捕获卷 **258 帧**；基线 **258/0/0/0**；build **0 告警**；换装 `ok / SHA_MATCH=1 / 381=381`；`STORE-SIZE lines=1108 funcs=52 longest=66`；产品面连续零改动 **1** 轮（as-of 449，`python3 scripts/product_streak.py --streak-for 449`，last=07fcd2f）。清账与电池在台账后复跑。

本轮做了什么：
① ⓪ push 224b8ee..9743379 success、ahead=0；107f2b3 跑 success 签收 R448 读数；0737460 failure 原文＝Motion floor 的 markdown 模式标签 1<2；两新跑 in_progress 后 gh EOF ⇒ NOT-RUN。
② 产品：完成项正文弱一档（亮 +63.2、暗 −48.7；2 新帧 + 2 旧帧变化、基线 258）。
③ 判据：M1234/M1235 2/2；新单测 3 条 + 帧判据（灰度差/墨数比）；precheck 228/210/594；hidden rot 0。
④ 436：107f2b3 success；0737460/ecb8e69 的两个采样红未复现；不改门槛、不重猜 must_judge。
⑤ 367：hidden 表 314 / 可判 1009 / rot 0。
⑥ 捕获 258 帧；基线 258/0/0/0；build 0 告警；换装 ok；本地全量 1234/57/5（滚动具名）。

NOT-RUN / 阻塞（分开写）：① `40634880705 ↔ 9743379`（in_progress 后 gh EOF）；② `40632882239 ↔ 224b8ee`（含 QUICKPICK_HINT 1x；同上）；③ R450 自身跑；④ 436 新跑 Motion floor（107f2b3 success；两个采样红未复现）；⑤ HTML 任务列表无同一条弱化（481）；⑥ HTML 表格体行无同一条线（479）；⑦ 设置内容列 1x 平涂；⑧ 设置脚注带 1x；⑨ 主窗口 content 帧 1x；⑩ 高夹具 1x；⑪ 13+ 菜单像素/标题；⑫ 真实拖拽；⑬ Dock 像素；⑭ 源图标最小窗文字 1x；⑮ 本地全量 5 条滚动红（449）；⑯ 2x/extended；⑰ 固定块揭示偏移（455）；⑱ 跨年时间（456）；⑲ 主列表暗档文字盲区（457）；⑳ 真机/多屏（447）；㉑ 真菜单栏、12 实时腿；㉒ `table-lazy-rows`；㉓ HTML 六档字号（460）；㉔ 清除 × 命中区（461）；㉕ 分隔线令牌（462）；㉖ 展开态已加载内容无帧（463）；㉗ 其它自绘控件帮助文本（464）；㉘ HTML 引用块无导引线（465）；㉙ HTML 表格表头无同档（466）；㉚ 100+ 行行号（467）；㉛ HTML 代码块行号（468）；㉜ 行号选中/滚动两态（469）；㉝ 关于页 1x 盲（470）；㉞ M613 机器前提（472）；㉟ 真机 vibrant 暗档（473）；㊱ 长来源截断（474）；㊲ bundle ID 未搜（475）；㊳ 长首行标签省略无帧（476）；㊴ HTML 代码块无语言标签（477）；㊵ HTML `<hr>` 无通栏线（478）；㊶ HTML 表格体行无同一条线（479）；㊷ QuickPick 键盘提示 1x 读数（480）；㊸ 437–481 的未结项仍开。

下一轮（R451）的靶：⓪ 先 `git push origin main`（禁 amend/force）并复核 ahead=0；读 R450 主笔+追记 head 跑、`40634880705 ↔ 9743379`、`40632882239 ↔ 224b8ee`（含 `QUICKPICK_HINT`）与 `40629776895 ↔ 0737460`（failure 原文＝Motion floor markdown 模式标签 1<2）、`40629867848 ↔ 107f2b3`（success，R448 读数）、`40623613789 ↔ ecb8e69`、`40620912699 ↔ 36284e1`、`40617745753 ↔ fe956e3`、`40613782362 ↔ eeccad0` 的全部失败步骤（成对 run↔commit），重点看 `TASK_DIM` 两档 148.3/85.1/+63.2 与 136.0/184.7/−48.7、`QUICKPICK_HINT` 1566/1848/0 与 12 帧、`TABLE_ROW_LINES` 3/0/108.0/102.0/1.0、`THEMATIC_RULE` 597.0/1.0/1、`CODE_LANGUAGE` 116/126/0/0、`HISTORY_SEARCH_SOURCE` 两档 0→1、亮档行带 3 / 暗档具名 NOT-RUN、`HISTORY_ROW_SOURCE` 139.0/74.0、`SETTINGS_ABOUT_ROW` 7/7、`PROBE_DOMAIN` 44/20、`CODE_LINE_NUMBERS` 3/21/100%、`TABLE_HEADER` 1.10/1.11 与 436；in_progress/0 字节不算绿；① 现读 rot=0，按 `HIDDEN_ROT` 查新腐烂；② 继续产品视觉位并落 Sources、换缺陷类别（不要再做任务项完成态/浮层键盘提示/表格体行分隔/主题分隔线/代码块语言标签/代码块行号/表格表头/引用导引线/侧栏搜索来源/主列表来源行/设置侧栏文字/设置关于页/录制帮助/多文件展开/批量分隔/浮层搜索/图片/HTML/排除名单/行内符号/时间列/分区头/侧栏脚注/详情头部/Dock/菜单栏/横幅/回执/热图/计数/空态/无结果/焦点/悬停/选中/滚动/CTA）；③ 436 只复核新跑 Motion floor，不重猜 `must_judge`。
"""

R450_REPORT_BULLET = u"""- **R450（任务项完成态位）**：勾选态只落在 ☑/☐ 两个小字形上，正文与未完成项同色同重。新 `TaskItemPresentation`（只有 checked 弱化、`secondaryLabelColor`）；`attributes(for:in:dimmed:)` 对完成项文字降一档（链接仍保留链接色），`.unorderedItem` 只在 checked 时 dimmed。夹具 `detail-tasks`（一勾一未勾、正文逐字相同）：`TASK_DIM light 勾选=148.3 未勾选=85.1 差=+63.2 墨数=1149/1269`、`dark 136.0/184.7 差=-48.7 墨数=1287/1393`；`☑/☐` 与 `visibleText` 不动。**2 张新帧 + 2 张旧帧变化**（`detail-markdown-rendered` 的「解析层完成」也变灰），基线 **256→258 / 0/0/0**；已看亮/暗。`M1234/M1235` **2/2**；新单测 3 条 + 帧判据（灰度差/墨数比）；预检 228/210/594 bad=0、ARM 321/1077、HIDDEN 314/1009 rot=0。⓪：一次快进 push **`224b8ee..9743379` success**、HEAD=origin/main=`9743379`、ahead=0；**`40629867848 ↔ 107f2b3` success**，同跑 `TABLE_ROW_LINES 3/0/108.0/102.0/1.0`、`THEMATIC_RULE 597.0/1.0/1`、`CODE_LANGUAGE 116/126`、`HISTORY_SEARCH_SOURCE light 1/3、dark 1/1`+NOT_RUN、`HISTORY_ROW_SOURCE 139.0/74.0`、`SETTINGS_ABOUT_ROW 7/7`、`CODE_LINE_NUMBERS 54.0/3/21.0/100%`、`TABLE_HEADER 1.10`、`PROBE_DOMAIN 44/20`；**`40629776895 ↔ 0737460` failure 仅 Motion floor**（`judged=5/5 executed=77`、`testMarkdownModeLabelChangeIsAVisibleProcess` 1 帧<2）；`40623613789 ↔ ecb8e69` failure 仅 Motion floor（`testCopyReceipt...` 1<2）；两个采样红均未在 107f2b3 复现；`40634880705 ↔ 9743379` 与 `40632882239 ↔ 224b8ee` 读时 in_progress、随后 gh EOF ⇒ NOT-RUN。全量 **1234/57/5**（滚动具名），单跑 4/4 ⇒ `LOCAL_SCROLL_SESSION_NOT_RUN=full-suite-order`（449）。捕获 258 帧；build 0 告警；换装 ok/SHA_MATCH=1/381=381；STORE-SIZE 1108/52/66；电池 683/5。
"""

audit = rd(AUDIT); iter_text = rd(ITER); decisions = rd(DECISIONS)
changelog = rd(CHANGELOG); backlog = rd(BACKLOG); state = rd(STATE); report = rd(REPORT)

if audit.count(AUDIT_TITLE) != 1: raise SystemExit("REFUSED AUDIT %d" % audit.count(AUDIT_TITLE))
if u"第 449 轮（R450" in audit: raise SystemExit("REFUSED AUDIT 已有 R450")
if u"## Round 447 · R450" in iter_text: raise SystemExit("REFUSED ITER 已有 Round 447")
if u"## D-446" in decisions: raise SystemExit("REFUSED DECISIONS 已有 D-446")
if u"已完成任务项的正文弱一档" in changelog: raise SystemExit("REFUSED CHANGELOG 已有该标题")
if u"**481." in backlog: raise SystemExit("REFUSED BACKLOG 已有 481")
if state.count(u"## R449 状态") != 1: raise SystemExit("REFUSED STATE %d" % state.count(u"## R449 状态"))
U_CELL_OLD = u"U-31 … U-1672（R449 现读抬到最新一节）"
if report.count(U_CELL_OLD) != 1: raise SystemExit("REFUSED REPORT U %d" % report.count(U_CELL_OLD))
if report.count(u"AGENT_STATE.md` 的 R449 节 ②") != 1: raise SystemExit("REFUSED REPORT pointer")

new_audit = audit.replace(AUDIT_TITLE, AUDIT_SECTION + AUDIT_TITLE, 1)
new_iter = iter_text.rstrip() + "\n\n" + ITER_SECTION + "\n"
new_decisions = decisions.rstrip() + "\n\n" + DECISION_446 + "\n"
marker = u"## [Unreleased]\n"
if changelog.count(marker) != 1: raise SystemExit("REFUSED CHANGELOG")
new_changelog = changelog.replace(marker, marker + "\n" + CHANGELOG_SECTION, 1)
new_backlog = backlog.rstrip() + "\n\n" + BACKLOG_SECTION + "\n"
new_state = state.replace(u"## R449 状态", STATE_SECTION + u"## R449 状态", 1)
new_report = report.replace(U_CELL_OLD, u"U-31 … U-1677（R450 现读抬到最新一节）", 1)
new_report = new_report.replace(u"AGENT_STATE.md` 的 R449 节 ②", u"AGENT_STATE.md` 的 R450 节 ②", 1)
new_report = new_report.rstrip() + "\n\n" + R450_REPORT_BULLET + "\n"

wr(AUDIT, new_audit); wr(ITER, new_iter); wr(DECISIONS, new_decisions)
wr(CHANGELOG, new_changelog); wr(BACKLOG, new_backlog); wr(STATE, new_state); wr(REPORT, new_report)
print("LEDGERS_R450_OK audit=%d iter=%d decisions=%d changelog=%d backlog=%d state=%d report=%d"
      % (len(new_audit), len(new_iter), len(new_decisions), len(new_changelog),
         len(new_backlog), len(new_state), len(new_report)))
