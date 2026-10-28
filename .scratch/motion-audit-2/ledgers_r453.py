#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R453 七本台账一次落盘（只跑一次；先断言所有锚点，全部通过才写）。"""
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


AUDIT_TITLE = u"## 第 451 轮（R452 · 2026-10-28"
AUDIT_SECTION = u"""## 第 452 轮（R453 · 2026-10-28 · U-1688…U-1692）：删除线（作者标记的删除内容）正文弱一档（逐字相同的两段：亮 137.9 vs 82.0、暗 147.2 vs 192.3；字形间隙 9/9 仍被 AppKit 的线填上；2 张新帧、基线 260→262）（产品 1 文件，删除线语义位）

- **U-1688：⓪ push 与跑。** 开工 remote=`e750598`、ahead=0，`git push` 为 **no-op**；当时 `40640660665 ↔ 86044bf`（R451 head）、`40642482086 ↔ e083179`（R452 head）、`40642524490 ↔ e750598`（R452 预记 head）读时都 in_progress、`gh` 单跑 EOF ⇒ NOT-RUN。**收口前重试 `gh` 恢复，三跑全部 completed success**：`40640660665` 的 `LIST_HANG_STYLE light/dark 制表位数=1 制表位=16.0 续行=16.0 首行=0.0pt`（R451 签收）；`40642482086` 的 `WEIGHT_CENTER_TICK_NOT_RUN=runner-settings-content-flat light/dark 轨=1`（**按设计具名 NOT-RUN**：设置内容列在 runner 1x 平涂，本地 2x 是刻度证人）；`40642524490` success。已读：`40636558557 ↔ 667d1a2` success（TASK_DIM 1x：亮 158.0/115.1 +42.9、暗 128.4/166.4 −38.0）；`40636617018 ↔ eb04e37` success；`40634880705 ↔ 9743379` failure（`testProductDurationRevealStillMovesOverTime` 无中间 origin ⇒ `RUNNER_SCROLL_SESSION_FLAKE`，同代码 224b8ee/107f2b3 两跑 success + Motion `testMarkdownModeLabelChange` 1<2）；`40629776895`/`40623613789` failure 仅 Motion floor、`40620912699` failure 1 步（dark 行带，已修）。436 只复核 Motion floor：`judged=4/5 executed=77 not-run=notice-banner`、红 0；采样红原样重跑，不改门槛、不重猜 `must_judge`。
- **U-1689：① 腐烂与预检。** `HIDDEN_ARMS 表=318 可判=1017 rot=0`；`NEEDLE_PRECHECK tables=231 covered=213 arms=600 bad=0`、`ARM_TOTAL files=324 arms=1083`。本轮改的是 Markdown 呈现层的颜色分支，没有弄断旧针。
- **U-1690：② 删除线正文弱化。** 缺陷形状：`~~` 标记的删除内容渲染后与正常正文同色同重 —— 删除内容还和仍然有效的文字抢视线。修法：`MarkdownPresentation.attributes(for:in:dimmed:)` 里 `struck`（`.strikethrough` 且非链接）用 `struckTextColor = secondaryLabelColor`；可点链接仍保留链接色（假 affordance 比弱化更坏）。旧/新（两段逐字相同的 `同样的字`）：`STRIKE_DIM light 删除=137.9 正常=82.0 差=+55.9`、`dark 147.2/192.3 差=−45.2`，字形间隙 9/9 被删除线填上（AppKit 的 `.strikethroughStyle` 一直在画，自绘线是冗余的，已撤）。夹具 `detail-strike`；**2 张新帧、0 张旧帧变化**（markdown 样例没有 `~~`），基线 **260→262 / 0/0/0**；已看亮/暗：删除段灰、正常段黑/白。Store 未动（1108 行/52 方法/最长 66）。
- **U-1691：判据、刀与证人换代。** 新单测 `StrikethroughPresentationTests` 3 条（删除段与正常段颜色不同、删除线属性仍在；删除线内链接保留链接色；文字/visibleText 不变）+ 帧判据 `testStruckTextIsDeEmphasized`（灰度差亮 ≥+20、暗 ≤−20；正常段的字形间隙列在删除段被填 ≥1）。**证人换代记**：第一版用"最长连续墨"当线证人 —— M1241（去掉自绘线）两次 ESCAPED，因为灰字的抗锯齿会并成一条长墨；同时证明 AppKit 的删除线一直在画（间隙 9/9 被填）。最终产品不画自绘线，间隙列只作**前提**证人，颜色差是新面。`M1240`（删除段不弱化）⇒ 单测+帧判据 CAUGHT；`M1241`（两段都弱化）⇒ 同上 CAUGHT ⇒ **2/2**、RESTORE_CLEAN=yes。
- **U-1692：八步与具名 NOT-RUN。** build **0 告警**；捕获卷 **262 帧**、`COMPARED=262 CHANGED=0 MISSING=0 ADDED=0`；全量 **1244/57/5**（5 个断言全在 `SelectionRevealAnimationTests`）；单跑 `caffeinate -u` **4/4** ⇒ `LOCAL_SCROLL_SESSION_NOT_RUN=full-suite-order`（449）；换装 `INSTALL_RESULT=ok / SHA_MATCH=1 / 381=381`；`STORE-SIZE lines=1108 funcs=52 longest=66`；产品面连续零改动 **1** 轮（as-of 452，`python3 scripts/product_streak.py --streak-for 452`，last=7d9be37）；清账与电池在台账后复跑。**具名 NOT-RUN**：① `WEIGHT_CENTER_TICK_NOT_RUN=runner-settings-content-flat`（R452 的刻度在 runner 1x 的具名出口，非红）；② R453 自身跑（提交后创建）；③ `RUNNER_SCROLL_SESSION_FLAKE`（9743379 的滚动红；R454 重跑复核）；④ 436 的 markdown 模式标签采样红（1<2；未复现于其他跑）；⑤ HTML 的 `<del>` 没有同一条颜色弱化（484）；⑥ HTML 列表缩进/任务弱化/表格体行（482/481/479）；⑦ 设置内容列 1x 平涂；⑧ 设置脚注带 1x；⑨ 主窗口 content 帧 1x；⑩ 高夹具 1x；⑪ 13+ 菜单像素/标题；⑫ 真实拖拽；⑬ Dock 像素；⑭ 源图标最小窗文字 1x；⑮ 本地全量 5 条滚动红（449）；⑯ 2x/extended；⑰ 固定块揭示偏移（455）；⑱ 跨年时间（456）；⑲ 主列表暗档文字盲区（457）；⑳ 真机/多屏（447）；㉑ 真菜单栏、12 实时腿；㉒ `table-lazy-rows`；㉓ HTML 六档字号（460）；㉔ 清除 × 命中区（461）；㉕ 分隔线令牌（462）；㉖ 展开态已加载内容无帧（463）；㉗ 其它自绘控件帮助文本（464）；㉘ HTML 引用块无导引线（465）；㉙ HTML 表格表头无同档（466）；㉚ 100+ 行行号（467）；㉛ HTML 代码块行号（468）；㉜ 行号选中/滚动两态（469）；㉝ 关于页 1x 盲（470）；㉞ M613 机器前提（472）；㉟ 真机 vibrant 暗档（473）；㊱ 长来源截断（474）；㊲ bundle ID 未搜（475）；㊳ 长首行标签省略无帧（476）；㊴ HTML 代码块无语言标签（477）；㊵ HTML `<hr>` 无通栏线（478）；㊶ HTML 表格体行无同一条线（479）；㊷ QuickPick 键盘提示 1x（480）；㊸ HTML 任务列表无弱化（481）；㊹ HTML 列表缩进（482）；㊺ 中心刻度端点标签（483）；㊻ 437–484 的未结项仍开。

"""

ITER_SECTION = u"""## Round 450 · R453（第 452 轮 · 2026-10-28）：删除线（作者标记的删除内容）正文弱一档（亮 137.9/82.0 +55.9、暗 147.2/192.3 −45.2；字形间隙 9/9 仍被 AppKit 的线填上；2 张新帧、基线 262）

`~~` 删除的内容与正常正文同色。`attributes(for:in:dimmed:)` 里 `struck`（删除线且非链接）用 `secondaryLabelColor`；链接保留链接色。夹具 `detail-strike`（两段逐字相同的 `同样的字`）：`STRIKE_DIM light 137.9/82.0 差=+55.9`、`dark 147.2/192.3 差=−45.2`、`隙=9/9`。2 张新帧、0 旧帧变化，基线 262/0/0/0；已看亮/暗。**证人换代记**：第一版"最长连续墨"线证人被灰字抗锯齿骗过（M1241 去掉自绘线两次 ESCAPED），却证明 AppKit 的线一直在画（间隙 9/9 被填）⇒ 产品不自绘线，间隙列只作前提；M1240/M1241 2/2。⓪：开工 no-op push；收口前 gh 恢复，40640660665/40642482086/40642524490 三跑 success，LIST_HANG_STYLE 16/16/0 签收、WEIGHT_CENTER_TICK 在 runner 具名 NOT_RUN（设置内容列平涂）；TASK_DIM 1x 158.0/115.1、128.4/166.4 签收；9743379 滚动会话采样红 + Motion 模式标签 1<2。全量 1244/57/5；捕获 262；换装 ok/SHA_MATCH=1/381=381；电池 683/5。

**七维度自评**（恰七行，每格 n/15）：

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | 15/15 | 亮/暗 detail-strike 逐张看过：删除段灰、正常段黑/白；删除线在帧上是 AppKit 的（间隙 9/9）。 |
| 判据有效性 | 15/15 | 两段逐字相同的灰度差（亮 +、暗 −）+ 字形间隙列前提；M1240/M1241 2/2。 |
| 假绿防御 | 15/15 | 最长连续墨证人被抗锯齿骗过两次时没有采信，换间隙列并写明；自绘线撤掉、不冒领 AppKit 的线。 |
| 产品面推进 | 14/15 | 删除内容第一次在正文上退后；Store 不动；扣 1：HTML 的 `<del>` 未覆盖（484）。 |
| 台账一致性 | 15/15 | U-1688…U-1692、D-449、no-op push/ahead=0、262 帧/1244、STORE-SIZE 1108/66 都从命令与测试解析。 |
| 交付诚实性 | 15/15 | 三跑 in_progress→收口 success 与 WEIGHT_CENTER_TICK 具名 NOT_RUN 并列写；两次 M1241 ESCAPED 与证人换代照记。 |
| 可复核性 | 15/15 | 137.9/82.0/+55.9、147.2/192.3/−45.2、隙 9/9、刀号与 precheck 231/213/600、rot 318/1017、基线 262 都在。 |

均分 = 104/105 ≈ 14.9/15（99）。"""

DECISION_449 = u"""## D-449 删除线（`~~`）正文降一档，链接保留链接色（R453）

- 背景：`~~` 标记的删除内容渲染后与正常正文同色同重，删除内容还和仍然有效的文字抢视线。
- 决定：`attributes(for:in:dimmed:)` 里 `struck`（`.strikethrough` 且非链接）用 `secondaryLabelColor`；可点链接仍保留链接色。
- 理由：删除内容是作者标记的"不再有效"；弱化让它在视觉上退后；链接可点性不能因弱化变假 affordance。
- 兼容性/迁移：新夹具 `detail-strike`（2 帧，基线 260→262）；markdown 样例没有 `~~`，0 张旧帧变化。
- 边界：HTML 的 `<del>` 未接（484）；删除线本身由 AppKit 画，产品不自绘。
- 回滚：把 `struck` 分支删掉即可；或 `git revert`。
"""

CHANGELOG_SECTION = u"""### 删除线（`~~`）正文弱一档（亮 137.9 vs 82.0、暗 147.2 vs 192.3；字形间隙 9/9 仍被 AppKit 的线填上；2 张新帧、基线 262）（R453 / 第 452 轮 / Round 450 / U-1688…U-1692 · 产品 1 文件，删除线语义位）

"""

BACKLOG_SECTION = u"""449 追记（R453 · 仍开）：本机全量仍 5 断言红（3 条用例）、单跑 4/4 绿；未动阈值。

451 追记（R453 · 仍开）：macOS 12 的详情头部阈值本轮未动。

452 追记（R453 · 仍开）：脚注 1x 具名 NOT-RUN 仍生效。

453 追记（R453 · 仍开）：真实系统拖拽会话仍无自动化验收。

454 追记（R453 · 仍开）：菜单具名标记仍未发射。

455 追记（R453 · 仍开）：固定条目滚动到位的独立偏移验收仍缺。

456 追记（R453 · 仍开）：跨年记录仍无年份。

457 追记（R453 · 仍开）：主列表暗档文字仍是另一处。

458 追记（R453 · 仍开）：CI 行首符号像素证人仍缺。

459 追记（R453 · 仍开）：设置内容列/高夹具在 1x 整列平涂。

460 追记（R453 · 仍开）：HTML 六档以上字号仍会后排压到 12pt。

461 追记（R453 · 仍开）：浮层清除 × 命中区 18pt。

462 追记（R453 · 仍开）：批量操作栏分隔线的 0.18 透明度未提令牌。

463 追记（R453 · 仍开）：展开态已加载内容仍无帧。

464 追记（R453 · 仍开）：其它自绘控件仍无同类帮助判据。

465 追记（R453 · 仍开）：HTML 引用块没有导引线。

466 追记（R453 · 仍开）：HTML 表格的表头没有同档字重。

467 追记（R453 · 仍开）：代码块行号的 9pt 档只在纯函数里验。

468 追记（R453 · 仍开）：HTML 代码块没有行号。

469 追记（R453 · 仍开）：代码块行号的选中态/滚动态没有帧。

470 追记（R453 · 仍开）：关于页正文在 runner 1x 是平涂。

471 已结案（R443）。

472 追记（R453 · 仍开）：M613 本机 2x 空名册（机器前提）。

473 追记（R453 · 仍开）：设置侧栏文字的真机 vibrant 暗档没有同屏对照。

474 追记（R453 · 仍开）：长来源 App 名的截断没有帧。

475 追记（R453 · 仍开）：侧栏搜索未匹配来源 App 的 bundle ID。

476 追记（R453 · 仍开）：代码块语言标签在长首行时被省略，没有帧。

477 追记（R453 · 仍开）：HTML 渲染器的代码块没有语言标签。

478 追记（R453 · 仍开）：HTML 预览的 `<hr>` 没有同一条通栏线。

479 追记（R453 · 仍开）：HTML 表格体行没有同一条分隔线。

480 追记（R453 · 仍开）：QuickPick 键盘提示 1x 已签收；12 帧名单仍只在本地。

481 追记（R453 · 仍开）：HTML 任务列表没有同一条完成态弱化。

482 追记（R453 · 仍开）：HTML 渲染路径的列表没有同一条悬挂制表位。

483 追记（R453 · 仍开）：权重滑块只有中心刻度，0% / 200% 端点没有标签。

**484. HTML 渲染路径的 `<del>` 没有同一条颜色弱化**（R453 观察）
    现象：R453 只弱化了 Markdown 渲染路径的删除线文字；HTML 预览的 `<del>`/`<s>` 走 `NSAttributedString` 的 HTML 导入，是另一条路径，没有同一条 `secondaryLabelColor` 降档，也没有帧。
    修法：给 HTML 预览拍一张含 `<del>` 的帧，量删除段与正常段的灰度差；若导入器不给删除线，用同一 `struckTextColor` 在 HTML 路径补。
"""

STATE_SECTION = u"""## R453 状态（2026-10-28 · 本地 · 第 452 轮 / Round 450）：删除线（作者标记的删除内容）正文弱一档（亮 137.9 vs 82.0、暗 147.2 vs 192.3；字形间隙 9/9 仍被 AppKit 的线填上；2 张新帧、基线 260→262）；收口前 gh 恢复，R451/R452 三跑 success、LIST_HANG_STYLE 16/16/0 签收、WEIGHT_CENTER_TICK 在 runner 具名 NOT_RUN（产品 1 文件，删除线语义位）

最后更新：2026-10-28（本地 · R453 / 第 452 轮 / Round 450）：`~~` 标记的删除内容与正常正文同色同重。`MarkdownPresentation.attributes(for:in:dimmed:)` 里 `struck`（`.strikethrough` 且非链接）用 `struckTextColor = secondaryLabelColor`；可点链接仍保留链接色。旧/新（两段逐字相同的 `同样的字`）：`STRIKE_DIM light 删除=137.9 正常=82.0 差=+55.9`、`dark 147.2/192.3 差=−45.2`、字形间隙 9/9 被填（AppKit 的 `.strikethroughStyle` 一直在画，自绘线冗余已撤）。夹具 `detail-strike`；**2 张新帧、0 张旧帧变化**（markdown 样例没有 `~~`），基线 **260→262 / 0/0/0**；已看亮/暗。**证人换代记**：第一版"最长连续墨"当线证人，M1241（去掉自绘线）两次 ESCAPED —— 灰字抗锯齿会并成长墨，且证明 AppKit 的线一直在画（间隙 9/9）；最终产品不自绘线，间隙列只作前提，颜色差是新面。`M1240/M1241` **2/2**；新单测 3 条 + 帧判据。预检 **231/213/600 bad=0**、ARM **324/1083**、HIDDEN **318/1017 rot=0**。⓪：开工 remote=`e750598`、ahead=0，`git push` 为 **no-op**；三跑读时 in_progress、`gh` EOF ⇒ NOT-RUN；**收口前重试 gh 恢复，三跑全部 success**：`40640660665 ↔ 86044bf` 的 `LIST_HANG_STYLE 16.0/16.0/0.0` 签收、`40642482086 ↔ e083179` 的 `WEIGHT_CENTER_TICK_NOT_RUN=runner-settings-content-flat light/dark 轨=1`（**按设计具名 NOT-RUN**，非红）、`40642524490 ↔ e750598` success；`40636558557 ↔ 667d1a2` success（TASK_DIM 1x 158.0/115.1 +42.9、128.4/166.4 −38.0）；`40636617018` success；`40634880705 ↔ 9743379` failure（`testProductDurationRevealStillMovesOverTime` 无中间 origin ⇒ `RUNNER_SCROLL_SESSION_FLAKE`，同代码 224b8ee/107f2b3 两跑 success + Motion `testMarkdownModeLabelChange` 1<2）；`0737460`/`ecb8e69` failure 仅 Motion floor、`36284e1` failure 1 步（dark 行带，已修）。本地全量 **1244/57/5**（5 断言全在 `SelectionRevealAnimationTests`）；单跑 **4/4** ⇒ `LOCAL_SCROLL_SESSION_NOT_RUN=full-suite-order`（449）。捕获卷 **262 帧**；基线 **262/0/0/0**；build **0 告警**；换装 `ok / SHA_MATCH=1 / 381=381`；`STORE-SIZE lines=1108 funcs=52 longest=66`；产品面连续零改动 **1** 轮（as-of 452，`python3 scripts/product_streak.py --streak-for 452`，last=7d9be37）。清账与电池在台账后复跑。

本轮做了什么：
① ⓪ 开工 no-op push（remote e750598、ahead=0）；三跑 in_progress/gh EOF ⇒ NOT-RUN，收口前重试恢复：三跑 success，LIST_HANG_STYLE 16/16/0 签收、WEIGHT_CENTER_TICK 具名 NOT_RUN（设置内容列平涂）；TASK_DIM 1x 签收；9743379 滚动采样红 + Motion 模式标签 1<2。
② 产品：删除线正文弱一档（亮 +55.9、暗 −45.2；2 新帧、基线 262）。
③ 判据：M1240/M1241 2/2；新单测 3 条 + 帧判据（灰度差/间隙列前提）；两次 ESCAPED 与证人换代照记；precheck 231/213/600；hidden rot 0。
④ 436：Motion floor 4/5/77、red 0、not-run=notice-banner；markdown 模式标签采样红未复现；不改门槛、不重猜 must_judge。
⑤ 367：hidden 表 318 / 可判 1017 / rot 0。
⑥ 捕获 262 帧；基线 262/0/0/0；build 0 告警；换装 ok；本地全量 1244/57/5（滚动具名）。

NOT-RUN / 阻塞（分开写）：① `WEIGHT_CENTER_TICK_NOT_RUN=runner-settings-content-flat`（R452 刻度的具名出口，非红）；② R453 自身跑；③ `RUNNER_SCROLL_SESSION_FLAKE`（R454 重跑复核）；④ 436 的 markdown 模式标签采样红（1<2；未复现于其他跑）；⑤ HTML 的 `<del>` 无同一条弱化（484）；⑥ HTML 列表缩进/任务弱化/表格体行（482/481/479）；⑦ 设置内容列 1x 平涂；⑧ 设置脚注带 1x；⑨ 主窗口 content 帧 1x；⑩ 高夹具 1x；⑪ 13+ 菜单像素/标题；⑫ 真实拖拽；⑬ Dock 像素；⑭ 源图标最小窗文字 1x；⑮ 本地全量 5 条滚动红（449）；⑯ 2x/extended；⑰ 固定块揭示偏移（455）；⑱ 跨年时间（456）；⑲ 主列表暗档文字盲区（457）；⑳ 真机/多屏（447）；㉑ 真菜单栏、12 实时腿；㉒ `table-lazy-rows`；㉓ HTML 六档字号（460）；㉔ 清除 × 命中区（461）；㉕ 分隔线令牌（462）；㉖ 展开态已加载内容无帧（463）；㉗ 其它自绘控件帮助文本（464）；㉘ HTML 引用块无导引线（465）；㉙ HTML 表格表头无同档（466）；㉚ 100+ 行行号（467）；㉛ HTML 代码块行号（468）；㉜ 行号选中/滚动两态（469）；㉝ 关于页 1x 盲（470）；㉞ M613 机器前提（472）；㉟ 真机 vibrant 暗档（473）；㊱ 长来源截断（474）；㊲ bundle ID 未搜（475）；㊳ 长首行标签省略无帧（476）；㊴ HTML 代码块无语言标签（477）；㊵ HTML `<hr>` 无通栏线（478）；㊶ HTML 表格体行无同一条线（479）；㊷ QuickPick 键盘提示 1x（480）；㊸ HTML 任务列表无弱化（481）；㊹ HTML 列表缩进（482）；㊺ 中心刻度端点标签（483）；㊻ 437–484 的未结项仍开。

下一轮（R454）的靶：⓪ 先 `git push origin main`（禁 amend/force）并复核 ahead=0；读 R453 主笔+追记 head 跑、`40640660665 ↔ 86044bf`（LIST_HANG_STYLE 已签收）、`40642482086 ↔ e083179`（WEIGHT_CENTER_TICK 具名 NOT_RUN）、`40642524490 ↔ e750598` 与 `40636558557 ↔ 667d1a2`（TASK_DIM 1x）、`40634880705 ↔ 9743379`（滚动会话采样红原文）、`40623613789 ↔ ecb8e69`、`40620912699 ↔ 36284e1` 的全部失败步骤（成对 run↔commit），重点看 `STRIKE_DIM` 两档 137.9/82.0/+55.9 与 147.2/192.3/−45.2、隙 9/9、`WEIGHT_CENTER_TICK` 9/5.0/0.0 或具名 NOT_RUN、`LIST_HANG_STYLE` 16.0/16.0/0.0、`TASK_DIM` 158.0/115.1、`QUICKPICK_HINT` 400/519、`TABLE_ROW_LINES` 3/0/108.0/102.0/1.0、`THEMATIC_RULE` 597.0/1.0/1、`CODE_LANGUAGE` 116/126、`HISTORY_SEARCH_SOURCE` 两档 0→1、`PROBE_DOMAIN` 44/20、`TABLE_HEADER` 1.10、`CODE_LINE_NUMBERS` 3/21/100% 与 436；in_progress/0 字节不算绿；`RUNNER_SCROLL_SESSION_FLAKE` 必须原样重跑复核（不改门槛）；① 现读 rot=0，按 `HIDDEN_ROT` 查新腐烂；② 继续产品视觉位并落 Sources、换缺陷类别（不要再做删除线/权重刻度/列表悬挂缩进/任务项完成态/浮层键盘提示/表格体行分隔/主题分隔线/代码块语言标签/代码块行号/表格表头/引用导引线/侧栏搜索来源/主列表来源行/设置侧栏文字/设置关于页/录制帮助/多文件展开/批量分隔/浮层搜索/图片/HTML/排除名单/行内符号/时间列/分区头/侧栏脚注/详情头部/Dock/菜单栏/横幅/回执/热图/计数/空态/无结果/焦点/悬停/选中/滚动/CTA）；③ 436 只复核新跑 Motion floor，不重猜 `must_judge`。
"""

R453_REPORT_BULLET = u"""- **R453（删除线语义位）**：`~~` 标记的删除内容与正常正文同色同重，删除内容还抢视线。`MarkdownPresentation.attributes(for:in:dimmed:)` 里 `struck`（`.strikethrough` 且非链接）用 `secondaryLabelColor`；可点链接仍保留链接色。夹具 `detail-strike`（两段逐字相同的 `同样的字`）：`STRIKE_DIM light 删除=137.9 正常=82.0 差=+55.9`、`dark 147.2/192.3 差=−45.2`、字形间隙 9/9 被填（AppKit 的线一直在画，自绘线冗余已撤）。**2 张新帧、0 张旧帧变化**，基线 **260→262 / 0/0/0**；已看亮/暗删除段灰、正常段黑/白。**证人换代记**：第一版"最长连续墨"线证人被灰字抗锯齿骗过（M1241 去掉自绘线两次 ESCAPED），换间隙列前提；颜色差是新面。`M1240/M1241` **2/2**；新单测 3 条 + 帧判据；预检 231/213/600 bad=0、ARM 324/1083、HIDDEN 318/1017 rot=0。⓪：开工 no-op push、ahead=0；三跑 in_progress/gh EOF ⇒ NOT-RUN，**收口前重试 gh 恢复**：`40640660665 ↔ 86044bf` success（LIST_HANG_STYLE 16/16/0）、`40642482086 ↔ e083179` success（WEIGHT_CENTER_TICK 具名 NOT_RUN=runner-settings-content-flat）、`40642524490 ↔ e750598` success；`40636558557 ↔ 667d1a2` success（TASK_DIM 1x 158.0/115.1、128.4/166.4）；`40634880705 ↔ 9743379` failure（滚动会话采样红 `testProductDurationRevealStillMovesOverTime` + Motion `testMarkdownModeLabelChange` 1<2）。全量 **1244/57/5**（滚动具名），单跑 4/4 ⇒ `LOCAL_SCROLL_SESSION_NOT_RUN=full-suite-order`（449）。捕获 262 帧；build 0 告警；换装 ok/SHA_MATCH=1/381=381；STORE-SIZE 1108/52/66；电池 683/5。
"""

audit = rd(AUDIT); iter_text = rd(ITER); decisions = rd(DECISIONS)
changelog = rd(CHANGELOG); backlog = rd(BACKLOG); state = rd(STATE); report = rd(REPORT)

if audit.count(AUDIT_TITLE) != 1: raise SystemExit("REFUSED AUDIT %d" % audit.count(AUDIT_TITLE))
if u"第 452 轮（R453" in audit: raise SystemExit("REFUSED AUDIT 已有 R453")
if u"## Round 450 · R453" in iter_text: raise SystemExit("REFUSED ITER 已有 Round 450")
if u"## D-449" in decisions: raise SystemExit("REFUSED DECISIONS 已有 D-449")
if u"删除线（`~~`）正文弱一档" in changelog: raise SystemExit("REFUSED CHANGELOG 已有该标题")
if u"**484." in backlog: raise SystemExit("REFUSED BACKLOG 已有 484")
if state.count(u"## R452 状态") != 1: raise SystemExit("REFUSED STATE %d" % state.count(u"## R452 状态"))
U_CELL_OLD = u"U-31 … U-1687（R452 现读抬到最新一节）"
if report.count(U_CELL_OLD) != 1: raise SystemExit("REFUSED REPORT U %d" % report.count(U_CELL_OLD))
if report.count(u"AGENT_STATE.md` 的 R452 节 ②") != 1: raise SystemExit("REFUSED REPORT pointer")

new_audit = audit.replace(AUDIT_TITLE, AUDIT_SECTION + AUDIT_TITLE, 1)
new_iter = iter_text.rstrip() + "\n\n" + ITER_SECTION + "\n"
new_decisions = decisions.rstrip() + "\n\n" + DECISION_449 + "\n"
marker = u"## [Unreleased]\n"
if changelog.count(marker) != 1: raise SystemExit("REFUSED CHANGELOG")
new_changelog = changelog.replace(marker, marker + "\n" + CHANGELOG_SECTION, 1)
new_backlog = backlog.rstrip() + "\n\n" + BACKLOG_SECTION + "\n"
new_state = state.replace(u"## R452 状态", STATE_SECTION + u"## R452 状态", 1)
new_report = report.replace(U_CELL_OLD, u"U-31 … U-1692（R453 现读抬到最新一节）", 1)
new_report = new_report.replace(u"AGENT_STATE.md` 的 R452 节 ②", u"AGENT_STATE.md` 的 R453 节 ②", 1)
new_report = new_report.rstrip() + "\n\n" + R453_REPORT_BULLET + "\n"

wr(AUDIT, new_audit); wr(ITER, new_iter); wr(DECISIONS, new_decisions)
wr(CHANGELOG, new_changelog); wr(BACKLOG, new_backlog); wr(STATE, new_state); wr(REPORT, new_report)
print("LEDGERS_R453_OK audit=%d iter=%d decisions=%d changelog=%d backlog=%d state=%d report=%d"
      % (len(new_audit), len(new_iter), len(new_decisions), len(new_changelog),
         len(new_backlog), len(new_state), len(new_report)))
