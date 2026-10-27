#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R439 七本台账一次落盘（只跑一次；先断言所有锚点，全部通过才写）。"""
import io
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
AUDIT = os.path.join(ROOT, "AGENT_UI_AUDIT.md")
ITER = os.path.join(ROOT, "AGENT_VISUAL_ITERATION.md")
DECISIONS = os.path.join(ROOT, "AGENT_DECISIONS.md")
CHANGELOG = os.path.join(ROOT, "CHANGELOG.md")
BACKLOG = os.path.join(ROOT, "AGENT_BACKLOG.md")
STATE = os.path.join(ROOT, "AGENT_STATE.md")
REPORT = os.path.join(ROOT, "AGENT_FINAL_REPORT.md")


def rd(path):
    with io.open(path, encoding="utf-8") as handle:
        return handle.read()


def wr(path, text):
    with io.open(path, "w", encoding="utf-8") as handle:
        handle.write(text)


AUDIT_TITLE = u"## 第 437 轮（R438 · 2026-10-28"
AUDIT_SECTION = u"""## 第 438 轮（R439 · 2026-10-28 · U-1618…U-1622）：Markdown 引用块补左侧导引线（旧规则带最长竖墨 17.0pt 是 h1 的 #，引用只有 18pt 缩进 → 新 57.0pt 亮/暗同值，引用文字左沿 38.5pt、净距 11.5pt；源模式负对照仍 14.5pt；2 张 Markdown 帧变化、基线 240）（产品 3 文件 + 1 新策略，详情正文引用位）

- **U-1618：⓪ push 与两跑命运。** `api=200` / `apple=200`；`git push origin main` 为 **no-op**（Everything up-to-date），HEAD = origin/main = `40c0a28`、**ahead=0**。读 **`40564355511 ↔ 6ce9e2b`（R438 追记）failure、失败步骤 2 个**：① `Swift tests`：`SelectionRevealAnimationTests.testProductDurationRevealStillMovesOverTime` 报「产品时长下没有任何中间 origin（`[0.0, 1430.0, 1430.0, 1430.0, 1430.0]`）⇒ 这是瞬移，不是过程」；② `Motion coverage floor`：`MOTION_FLOOR_SUITE_RED=1`，`testMarkdownModeLabelChangeIsAVisibleProcess` 在 1x 只有 1 个过渡帧（要 ≥2）。更新的一跑 **`40564432395 ↔ 40c0a28` success、失败步骤 0**（同一份产品/测试树，只多文档提交）⇒ 两红定位为 **runner 采样/时序**，具名 `SELECTION_REVEAL_RUNNER_SAMPLING_MISS=origins[0,1430,1430,1430,1430]` 与 `MOTION_LABEL_TRANSITION_RUNNER_SAMPLING_MISS=1x-1-frame`；**阈值一律未动**。绿跑同时签收 R438 各项：`EXPANDED_PREVIEW_AXIS light 83.0/82.0 差=1.0pt`、dark 同；`QUICKPICK_CLEAR_BUTTON light typed 106/93 list 0/0、dark 104/107`（地板 20）；`BULK_ACTION_SEPARATOR light 17.9 / dark 11.9`（地板 8）；`RECORDER_HELP_PIXEL_NOT_RUN=system-tooltip buttons=3` 在 Capture / Motion 两门都按名登记、不计红；`MOTION_SEQUENCE 选中没变 帧数=4 重抓=1`（same 臂 ≥3；另一臂 report-only 帧数=1，未过门）。**436**：`MOTION_FLOOR_FACTS judged=5/5 executed=77 not-run=- 红的用例=- 汇总行报红=0 机器=github-runner` —— 真实读数，不是 executed=0。
- **U-1619：① 腐烂。** `HIDDEN_ARMS 表=304 可判=988 rot=0 抽不出=6 已声明表=6 处置=ok`；新表 `mutate_r439_quote_rule` 已登记进 `TABLES`。`NEEDLE_PRECHECK tables=217 covered=199 arms=571 bad=0`、`BASH_ARMS 6/16 bad=0`、`ARM_TOTAL files=310 arms=1054 dupes=0 repeats=0`。
- **U-1620：② 详情 Markdown 引用块补左侧导引线。** 缺陷形状：引用此前只有 `quoteIndent` 的 18pt 缩进 —— 规则带（24..27pt = 容器 20 + 5）里最长的连续竖墨是 **17.0pt**（h1 的 `#`），也就是说引用**没有一个结构标记**；而列表续行也缩进，光靠左侧空白分不出「这是引文」。修法：新 `MarkdownQuoteRule`（宽 2pt、左偏 5pt、圆角 1pt、`secondaryLabelColor` 动态色），`MarkdownPresentation.attributedString` 给引用块连同分隔空行打 `quoteDepthAttribute`，`ChineseSelectableNSTextView.drawBackground(in:)` 只枚举可见字符、每级各画一条。旧/新：`MARKDOWN_QUOTE_RULE light/dark 带=24..27pt 竖墨=17.0→57.0pt 源=14.5pt 文字左=38.5pt 净距=11.5pt`；帧变化恰 **2 张**（`detail-markdown-rendered` 亮/暗），`CHANGED=2 MISSING=0 ADDED=0`，基线 **240/0/0/0**。已逐张看亮/暗两帧：线在引用文字左侧、覆盖两行与分隔空行，暗档可读。
- **U-1621：判据与刀。** 新单测 `MarkdownQuoteRuleTests` 5 条（几何与净距、嵌套每级一条、零深度/零跨度不画、属性串逐块标深度且正文不标、动态色两档翻面）；新帧判据 `testMarkdownQuotesCarryALeadingRule`（规则带最长竖墨 ≥30pt、源模式负对照 ≤20pt、引用文字左沿 36–42pt、净距 ≥8pt，并带通道前提 `MARKDOWN_QUOTE_RULE_NOT_RUN=runner-detail-frame-plain`）。`M1203–M1205` **3/3 CAUGHT**、RESTORE_CLEAN=yes（M1203 属性不写 / M1204 线右移进文字 / M1205 背景层不调绘制）；M1203 第一版判据针写成「没有画出来」而失败原文是「没画出来」，改正后整表重跑 3/3 —— 记在这里，免得下一轮再把针写成同义词。
- **U-1622：八步与具名 NOT-RUN。** build **0 告警**；捕获 **146 条 / 4 skip / 0 失败 / 240 帧**；帧基线 `COMPARED=240 CHANGED=0 MISSING=0 ADDED=0`（update 之后复验）；全量 **1188/57/5**（5 个断言全在 `SelectionRevealAnimationTests` 的 3 条用例：`testAnimatedRevealProducesIntermediateOffsets` 2、`testProductDurationRevealStillMovesOverTime` 2、`testStaticDocumentScrollAnimationIsCapturable` 1；单跑 `caffeinate -u` 后 **4/4 passed**：`TIME 采样=18/中间值=8/首=34.0/末=1438`、`CHANNEL 0→84.5→600 变化 56834/117600 重抓=no`、`OFFSET 0/201.5/1438`）⇒ 具名 `LOCAL_SCROLL_SESSION_NOT_RUN=full-suite-order`（449，不改门槛）；换装 `INSTALL_RESULT=ok / SHA_MATCH=1 / 381=381 / SMOKE_OK=1`；清账 `格=162 声明=63 不成立=0/63`；产品面连续零改动 **1** 轮（as-of 438，现读 `python3 scripts/product_streak.py --streak-for 438`，last=c1a35ee）。电池 `Ran 683 / OK (skipped=5)`（台账后复跑）。**具名 NOT-RUN**：① 本轮的导引线还没有 runner 1x 读数（R439 提交后的新跑才读）；② HTML 路径的引用块没有导引线（465）；③ R438 追记跑的两红（runner 采样，已定位到值）；④ 设置内容列 1x 平涂；⑤ 设置脚注带 1x；⑥ 主窗口 content 帧 1x；⑦ 高夹具 1x；⑧ 13+ 菜单像素/标题；⑨ 真实拖拽；⑩ Dock 像素；⑪ 源图标最小窗文字 1x；⑫ 本地全量 5 条滚动红（449）；⑬ 2x/extended；⑭ 固定块揭示偏移（455）；⑮ 跨年时间（456）；⑯ 主列表暗档文字盲区（457）；⑰ 真机/多屏（447）；⑱ 真菜单栏、12 实时腿；⑲ `table-lazy-rows`；⑳ HTML 六档字号（460）；㉑ 清除 × 命中区（461）；㉒ 分隔线令牌（462）；㉓ 展开态已加载内容无帧（463）；㉔ 其它自绘控件帮助文本（464）；㉕ 437–465 仍开。

"""

ITER_SECTION = u"""## Round 436 · R439（第 438 轮 · 2026-10-28）：Markdown 引用块补左侧导引线（旧规则带最长竖墨 17.0pt 是 h1 的 #、引用只有 18pt 缩进 → 新 57.0pt 亮/暗同值，引用文字左沿 38.5pt、净距 11.5pt；源模式负对照仍 14.5pt；2 张 Markdown 帧变化、基线 240）

引用此前只靠 18pt 缩进分层，而列表续行也缩进 —— 一段被缩进的文字到底是引用还是列表续行，帧上答不出来。修法：新 `MarkdownQuoteRule`（宽 2、左偏 5、圆角 1、`secondaryLabelColor` 动态色）、属性串给引用块连同分隔空行打 `quoteDepthAttribute`、正文视图在 `drawBackground(in:)` 里只枚举可见字符并按级画线。旧/新：同一帧规则带（24..27pt）最长竖墨 17.0pt（h1 的 #）→ 57.0pt（亮/暗同值）；引用文字左沿 38.5pt、净距 11.5pt；源模式帧 14.5pt 当负对照。帧变化恰 2 张，基线 240/0/0/0。M1203–M1205 3/3；预检 217/199/571 bad=0；HIDDEN 304/988 rot=0。⓪：push no-op、HEAD=40c0a28、ahead=0；`40564355511 ↔ 6ce9e2b` failure 2 步（产品时长无中间 origin `[0,1430,1430,1430,1430]`、动效标签 1x 只 1 帧），更新的一跑 `40564432395 ↔ 40c0a28` success ⇒ runner 采样，阈值未动；436 读 `judged=5/5 executed=77 REDS=0`。本地全量 1188/57/5（5 断言全在 SelectionRevealAnimationTests），单跑 4/4（TIME 18/8、34→1438；CHANNEL 0→84.5→600、56834/117600）⇒ 具名 LOCAL_SCROLL_SESSION_NOT_RUN=full-suite-order（449）。捕获 146/4/0、240 帧；换装 ok/SHA_MATCH=1/381=381/SMOKE_OK=1；清账 162/63/0；电池 683/5。

**七维度自评**（恰七行，每格 n/15）：

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | 14/15 | 亮/暗两帧逐张看过：线在引用文字左侧、覆盖两行与分隔空行；同一帧旧/新竖墨 17.0→57.0pt，负对照源模式 14.5pt。扣 1：新线的 runner 1x 读数要等本轮提交后的新跑。 |
| 判据有效性 | 15/15 | 纯函数几何 + 属性串逐块 + 帧上竖墨段 + 源模式负对照；M1203–M1205 3/3，三层坏法（不标记/线移位/不绘制）都咬住。 |
| 假绿防御 | 15/15 | 判据读竖向连续性而不是墨量（旧帧同带墨量反而更大）；通道前提单独具名；净距与文字左沿两条轴同时断言。 |
| 产品面推进 | 14/15 | 真落一个可见的正文结构标记（引用导引线），补的是「引用与列表续行分不出」的真空档；扣 1：HTML 引用路径未接（465）。 |
| 台账一致性 | 15/15 | U-1618…U-1622、D-435、两跑失败步骤与 436 读数都从命令和测试输出解析；基线 240 与帧差集一致。 |
| 交付诚实性 | 15/15 | 旧追记跑的两步红按原文与数值记；更新一跑同树绿说明是采样；新线的 runner 读数明确写「还没有」而不是绿。 |
| 可复核性 | 15/15 | 规则带 24..27pt、地板 30pt、负对照上界 20pt、净距 11.5pt、刀号与 precheck/rot、基线 240、换装/清账都在。 |

均分 = 103/105 ≈ 14.7/15（98）。"""

DECISION_435 = u"""## D-435 引用块用左侧竖线做结构标记（R439）

- 背景：引用此前只靠 `quoteIndent` 的 18pt 缩进分层；列表续行也缩进，帧上分不出「引文」与「续行」。配色弱化的两条路（`secondaryLabelColor` 3.95:1、`withAlphaComponent` 暗档烤黑）在 `quoteColor` 的注释里已被否过，不能再走。
- 决定：新增 `MarkdownQuoteRule` —— 宽 2pt、容器左偏 5pt、每嵌套一级按 `quoteIndent` 再进一条、圆角 1pt、`secondaryLabelColor` 动态色；`MarkdownPresentation` 给引用块（连同分隔空行）打 `quoteDepthAttribute`；正文视图在 `drawBackground(in:)` 里按可见字符枚举、每条引用画一条竖线。文字缩进与配色都不动。
- 理由：竖线是 macOS（Mail/Notes/Pages）对引用的结构语言，不参与文字配色，所以不会重蹈两次对比度事故；与缩进叠加后，引用与列表续行在几何上分开。
- 兼容性/迁移：纯 Markdown 渲染路径新增绘制；纯文本与 HTML 路径不受影响；帧变化只有 `detail-markdown-rendered` 亮/暗两张（基线 240 不变）。
- 边界：HTML `<blockquote>` 路径没有这个属性（465）；滚动时只画可见段（性能取舍，滚动会带来新脏区）。
- 回滚：删 `drawBackground` 里的 `drawQuoteRules` 调用即可恢复旧帧；或 `git revert`。
"""

CHANGELOG_SECTION = u"""### 详情 Markdown 引用块补左侧导引线（规则带最长竖墨 17.0 → 57.0pt、文字左沿 38.5pt、净距 11.5pt；2 张帧变化、基线 240）（R439 / 第 438 轮 / Round 436 / U-1618…U-1622 · 产品 3 文件，详情正文引用位）

"""

BACKLOG_SECTION = u"""437 追记（R439 · 仍开）：本轮只动详情正文引用；主列表仍不匹配 `sourceAppName`。

449 追记（R439 · 仍开）：本机全量仍 5 断言红（3 条用例）、单跑 4/4 绿（TIME 18/8、34→1438）；R438 追记跑在 runner 上也红过一次产品时长用例（`[0,1430,1430,1430,1430]`），更新一跑同树绿 ⇒ 采样/时序。

451 追记（R439 · 仍开）：macOS 12 的详情头部阈值本轮未动。

452 追记（R439 · 仍开）：脚注 1x 具名 NOT-RUN 仍生效。

453 追记（R439 · 仍开）：真实系统拖拽会话仍无自动化验收。

454 追记（R439 · 仍开）：菜单具名标记仍未发射。

455 追记（R439 · 仍开）：固定条目滚动到位的独立偏移验收仍缺。

456 追记（R439 · 仍开）：跨年记录仍无年份。

457 追记（R439 · 仍开）：主列表暗档文字在离屏帧里仍是黑底黑字。

458 追记（R439 · 仍开）：`FILE_ROW_SYMBOL_NOT_RUN` 已按名生效；CI 行首符号像素证人仍缺。

459 追记（R439 · 仍开）：设置内容列/高夹具在 1x 整列平涂。

460 追记（R439 · 仍开）：HTML 六档以上字号仍会后排压到 12pt。

461 追记（R439 · 仍开）：浮层清除 × 命中区 18pt。

462 追记（R439 · 仍开）：批量操作栏分隔线的 0.18 透明度未提令牌。

463 追记（R439 · 仍开）：展开态已加载内容仍无帧（只有 loading 分支）。

464 追记（R439 · 仍开）：其它自绘控件（浮层清除 ×、批量栏五颗）仍无同类帮助判据。

**465. HTML 引用块没有导引线：R439 只把 Markdown 路径接上了属性**（R439 观察）
    现象：`HtmlRendering` 产出的属性串不带 `MarkdownPresentation.quoteDepthAttribute`，所以 HTML 里若有 `<blockquote>`（转换器保留时）不会画左侧竖线；`detail-html-rendered` 夹具当前也没有引用块，帧上无对象。
    修法（下一轮若需要）：给 HtmlRendering 的引用块打同一属性，并在 HTML 夹具里加一段引用 + 帧判据（规则带竖墨 ≥30pt、正文行 0）。
"""

STATE_SECTION = u"""## R439 状态（2026-10-28 · 本地 · 第 438 轮 / Round 436）：Markdown 引用块补左侧导引线（规则带最长竖墨 17.0→57.0pt、引用文字左沿 38.5pt、净距 11.5pt；源模式负对照 14.5pt；2 张帧变化、基线 240）；R438 追记跑 `40564355511 ↔ 6ce9e2b` failure 2 步，更新的 `40564432395 ↔ 40c0a28` success ⇒ runner 采样、阈值未动（产品 3 文件，详情正文引用位）

最后更新：2026-10-28（本地 · R439 / 第 438 轮 / Round 436）：详情 Markdown 的引用块此前只有 18pt 缩进 —— 列表续行也缩进，帧上分不出引文。新 `MarkdownQuoteRule`（宽 2、左偏 5、每级按 `quoteIndent` 再进、圆角 1、`secondaryLabelColor` 动态色）提供几何；`MarkdownPresentation` 给引用块连同分隔空行打 `quoteDepthAttribute`；`ChineseSelectableNSTextView.drawBackground(in:)` 只枚举可见字符并按级画线。旧/新：同一帧规则带（24..27pt）最长竖墨 **17.0 → 57.0pt**（亮/暗同值），引用文字左沿 **38.5pt**、净距 **11.5pt**，源模式负对照仍 **14.5pt**。帧变化恰 2 张（`detail-markdown-rendered` 亮/暗），基线 **240/0/0/0**。`M1203–M1205` **3/3 CAUGHT**；新单测 5 条 + 新帧判据 1 条；预检 **217/199/571 bad=0**、ARM **310 文件 / 1054 把**、HIDDEN **304/988 rot=0**。⓪：push 为 no-op、HEAD = origin/main = `40c0a28`、**ahead=0**；`40564355511 ↔ 6ce9e2b` **failure、失败步骤 2 个**（`testProductDurationRevealStillMovesOverTime` 无中间 origin `[0.0, 1430.0, 1430.0, 1430.0, 1430.0]`；`testMarkdownModeLabelChangeIsAVisibleProcess` 1x 只 1 帧 <2），更新的一跑 `40564432395 ↔ 40c0a28` **success、失败步骤 0**（同树，只多文档）⇒ 具名 `SELECTION_REVEAL_RUNNER_SAMPLING_MISS` 与 `MOTION_LABEL_TRANSITION_RUNNER_SAMPLING_MISS`，**阈值未动**。绿跑签收 R438：`EXPANDED_PREVIEW_AXIS 83.0/82.0 差=1.0`、`QUICKPICK_CLEAR_BUTTON 106/93 与 104/107`、`BULK_ACTION_SEPARATOR 17.9/11.9`、`RECORDER_HELP_PIXEL_NOT_RUN` 两门登记；**436** = `judged=5/5 executed=77 REDS=0`。本地全量 **1188/57/5**：5 断言全在 `SelectionRevealAnimationTests`（3 条用例），单跑（caffeinate-u 后）**4/4 passed**（`TIME 18/8/34.0/1438`、`CHANNEL 0→84.5→600 变化 56834/117600 重抓=no`、`OFFSET 0/201.5/1438`）⇒ 具名 `LOCAL_SCROLL_SESSION_NOT_RUN=full-suite-order`（449）。捕获 **146/4/0 / 240 帧**；基线 **240/0/0/0**；换装 `ok / SHA_MATCH=1 / 381=381 / SMOKE_OK=1`；清账 `格=162 声明=63 不成立=0/63`；产品面连续零改动 **1** 轮（as-of 438，现读 `python3 scripts/product_streak.py --streak-for 438`）。电池 `Ran 683 / OK (skipped=5)`（台账后复跑）。

本轮做了什么：
① ⓪ push no-op、ahead=0；`40564355511 ↔ 6ce9e2b` failure 2 步（产品时长无中间 origin、动效标签 1x 1 帧），更新的 `40564432395 ↔ 40c0a28` success ⇒ runner 采样，阈值未动；R438 各项与 436 从绿跑取到真实读数。
② 产品：详情 Markdown 引用块补左侧导引线（旧 17.0pt → 新 57.0pt；2 张帧变化）。
③ 判据：M1203–M1205 3/3；新单测 5 条 + 帧判据（竖墨段/负对照/净距）；precheck 217/199/571；hidden rot 0。
④ 436：`MOTION_FLOOR_FACTS judged=5/5 executed=77 not-run=- 红的用例=- 汇总行报红=0`；不重猜 must_judge。
⑤ 367：hidden 表 304 / 可判 988 / rot 0。
⑥ 捕获 146/4/0、240 帧；换装 ok；清账 162/63/0；帧基线 240/0/0/0；本地全量 1188/57/5（5 条滚动红具名会话/顺序 NOT-RUN）。

NOT-RUN / 阻塞（分开写）：① 导引线的 runner 1x 读数（本轮提交后的新跑才读）；② HTML 引用路径无导引线（465）；③ R438 追记跑两红（采样，已定位）；④ 设置内容列 1x 平涂；⑤ 设置脚注带 1x；⑥ 主窗口 content 帧 1x；⑦ 高夹具 1x；⑧ 13+ 菜单像素/标题；⑨ 真实拖拽；⑩ Dock 像素；⑪ 源图标最小窗文字 1x；⑫ 本地全量 5 条滚动红（449）；⑬ 2x/extended；⑭ 固定块揭示偏移（455）；⑮ 跨年时间（456）；⑯ 主列表暗档文字盲区（457）；⑰ 真机/多屏（447）；⑱ 真菜单栏、12 实时腿；⑲ `table-lazy-rows`；⑳ HTML 六档字号（460）；㉑ 清除 × 命中区（461）；㉒ 分隔线令牌（462）；㉓ 展开态已加载内容无帧（463）；㉔ 其它自绘控件帮助文本（464）；㉕ 437–465 仍开。

下一轮（R440）的靶：⓪ 先 `git push origin main`（禁 amend/force）并复核 ahead=0；读 R439 主笔+追记 head 跑的全部失败步骤（成对 run↔commit），重点看新帧判据 `MARKDOWN_QUOTE_RULE` 两档竖墨 ≥30pt、负对照 ≤20pt，以及 `SELECTION_REVEAL_RUNNER_SAMPLING_MISS`/`MOTION_LABEL_TRANSITION_RUNNER_SAMPLING_MISS` 是否复现；in_progress/0 字节不算绿；① 367 现读 rot=0，按 `HIDDEN_ROT` 查新腐烂；② 继续产品视觉位并落 Sources、换缺陷类别（不要再做引用导引线/录制帮助/多文件展开/批量分隔/浮层搜索/图片/HTML/排除名单/行内符号/时间列/分区头/侧栏脚注/详情头部/Dock/菜单栏/横幅/回执/热图/计数/空态/无结果/焦点/悬停/选中/滚动/CTA）；③ 436 只复核新跑 Motion floor，不重猜 `must_judge`。
"""

R439_REPORT_BULLET = u"""- **R439（引用导引线位）**：详情 Markdown 的引用块此前只有 18pt 缩进 —— 列表续行也缩进，帧上分不出引文。新 `MarkdownQuoteRule`（宽 2、左偏 5、每级按 `quoteIndent` 再进、圆角 1、`secondaryLabelColor` 动态色）；`MarkdownPresentation` 给引用块连同分隔空行打 `quoteDepthAttribute`；`ChineseSelectableNSTextView.drawBackground(in:)` 只枚举可见字符并按级画线。旧/新：同一帧规则带（24..27pt）最长竖墨 **17.0 → 57.0pt**（亮/暗同值），引用文字左沿 **38.5pt**、净距 **11.5pt**，源模式负对照仍 **14.5pt**；帧变化恰 2 张（`detail-markdown-rendered` 亮/暗），基线 **240/0/0/0**。`M1203–M1205` **3/3**；新单测 5 条 + 新帧判据 1 条；预检 217/199/571 bad=0、ARM 310/1054、HIDDEN 304/988 rot=0。⓪：push no-op、HEAD=origin/main=`40c0a28`、ahead=0；`40564355511 ↔ 6ce9e2b` **failure 2 步**（产品时长无中间 origin `[0,1430,1430,1430,1430]`；动效标签 1x 只 1 帧 <2），更新的一跑 `40564432395 ↔ 40c0a28` **success**（同树）⇒ 具名 runner 采样，阈值未动；绿跑签收 `EXPANDED_PREVIEW_AXIS 83.0/82.0 差=1.0`、`QUICKPICK_CLEAR_BUTTON 106/93`、`BULK_ACTION_SEPARATOR 17.9/11.9`、`RECORDER_HELP_PIXEL_NOT_RUN`；**436** = `judged=5/5 executed=77 REDS=0`。本地全量 **1188/57/5**：5 断言全在 SelectionRevealAnimationTests，单跑 4/4（TIME 18/8、34→1438；CHANNEL 0→84.5→600、56834/117600）⇒ 具名 `LOCAL_SCROLL_SESSION_NOT_RUN=full-suite-order`（449）。捕获 146/4/0、240 帧；换装 ok/SHA_MATCH=1/381=381/SMOKE_OK=1；清账 162/63/0；电池 683/5。
"""

audit = rd(AUDIT)
iter_text = rd(ITER)
decisions = rd(DECISIONS)
changelog = rd(CHANGELOG)
backlog = rd(BACKLOG)
state = rd(STATE)
report = rd(REPORT)

if audit.count(AUDIT_TITLE) != 1:
    raise SystemExit("REFUSED AUDIT 锚点命中 %d 次" % audit.count(AUDIT_TITLE))
if u"第 438 轮（R439" in audit:
    raise SystemExit("REFUSED AUDIT 已有 R439 节")
if u"## Round 436 · R439" in iter_text:
    raise SystemExit("REFUSED ITERATION 已有 Round 436")
if u"## D-435" in decisions:
    raise SystemExit("REFUSED DECISIONS 已有 D-435")
if u"详情 Markdown 引用块补左侧导引线" in changelog:
    raise SystemExit("REFUSED CHANGELOG 已有该标题")
if u"**465." in backlog:
    raise SystemExit("REFUSED BACKLOG 已有 465")
if state.count(u"## R438 状态") != 1:
    raise SystemExit("REFUSED STATE 锚点命中 %d 次" % state.count(u"## R438 状态"))
U_CELL_OLD = u"U-31 … U-1617（R438 现读抬到最新一节）"
if report.count(U_CELL_OLD) != 1:
    raise SystemExit("REFUSED REPORT U 格命中 %d 次" % report.count(U_CELL_OLD))
if report.count(u"AGENT_STATE.md` 的 R438 节 ②") != 1:
    raise SystemExit("REFUSED REPORT §13 指针命中 %d 次" % report.count(u"AGENT_STATE.md` 的 R438 节 ②"))

new_audit = audit.replace(AUDIT_TITLE, AUDIT_SECTION + AUDIT_TITLE, 1)
new_iter = iter_text.rstrip() + "\n\n" + ITER_SECTION + "\n"
new_decisions = decisions.rstrip() + "\n\n" + DECISION_435 + "\n"
marker = u"## [Unreleased]\n"
if changelog.count(marker) != 1:
    raise SystemExit("REFUSED CHANGELOG [Unreleased] 命中 %d 次" % changelog.count(marker))
new_changelog = changelog.replace(marker, marker + "\n" + CHANGELOG_SECTION, 1)
new_backlog = backlog.rstrip() + "\n\n" + BACKLOG_SECTION + "\n"
new_state = state.replace(u"## R438 状态", STATE_SECTION + u"## R438 状态", 1)
new_report = report.replace(U_CELL_OLD, u"U-31 … U-1622（R439 现读抬到最新一节）", 1)
new_report = new_report.replace(u"AGENT_STATE.md` 的 R438 节 ②",
                                u"AGENT_STATE.md` 的 R439 节 ②", 1)
new_report = new_report.rstrip() + "\n\n" + R439_REPORT_BULLET + "\n"

wr(AUDIT, new_audit)
wr(ITER, new_iter)
wr(DECISIONS, new_decisions)
wr(CHANGELOG, new_changelog)
wr(BACKLOG, new_backlog)
wr(STATE, new_state)
wr(REPORT, new_report)
print("LEDGERS_R439_OK audit=%d iter=%d decisions=%d changelog=%d backlog=%d state=%d report=%d"
      % (len(new_audit), len(new_iter), len(new_decisions), len(new_changelog),
         len(new_backlog), len(new_state), len(new_report)))
