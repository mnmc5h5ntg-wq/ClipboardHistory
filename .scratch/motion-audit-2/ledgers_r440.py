#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R440 七本台账一次落盘（只跑一次；先断言所有锚点，全部通过才写）。"""
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


AUDIT_TITLE = u"## 第 438 轮（R439 · 2026-10-28"
AUDIT_SECTION = u"""## 第 439 轮（R440 · 2026-10-28 · U-1623…U-1627）：Markdown 表格表头补等宽 semibold（解析器丢掉 `| --- |` 行后表头/表体同形；新夹具两行逐字相同：light 墨量比 1.40、dark 1.25，左沿 23.0/23.5pt 同轴、行距 9.0pt；2 张旧帧变化 + 2 张新帧，基线 240→242）（产品 3 文件 + 1 新策略，详情正文表格位）

- **U-1623：⓪ 两跑与 R439 签收。** `api=200` / `apple=200`；`git push origin main` 为 **no-op**（Everything up-to-date），HEAD = origin/main = `fc88822`、**ahead=0**。`40573915633 ↔ 42c09ad` 与 `40573988870 ↔ fc88822` 都 **completed / success、失败步骤 0**。`MARKDOWN_QUOTE_RULE` 在 runner 1x 上的读数：light `竖墨=57.0pt 源=15.0pt 文字左=39.0pt 净距=12.0pt`、dark `57.0/15.0/38.0/11.0` ⇒ 两档都过 30pt、负对照都在 20pt 内（本机 57.0 / 14.5）。上一轮的两个采样红 **没有复现**：`testProductDurationRevealStillMovesOverTime` 本跑 **passed（0.832s）**、`testMarkdownModeLabelChangeIsAVisibleProcess` 在 Swift tests 里 skipped、Motion gate `passed=45 skipped=46 failed=0 有名字的红=0`；Capture gate `passed=129 skipped=17 failed=0`。两跑都报告同样 4 张**环境帧**差异（`glass-pill-copy-receipt-failed` ×2、`settings-general-login-failed` ×2），门放行 ⇒ 稳定的 runner/本机差异，不是本轮引入。**436**：`MOTION_FLOOR_FACTS judged=4/5 executed=77 not-run=notice-banner 红的用例=- 汇总行报红=0 机器=github-runner`（上一跑 judged=5/5；本跑 notice-banner 是具名 NOT-RUN，不是红）。
- **U-1624：① 腐烂。** `HIDDEN_ARMS 表=305 可判=990 rot=0 抽不出=6 已声明表=6 处置=ok`；新表 `mutate_r440_table_header` 已登记进 `TABLES`。`NEEDLE_PRECHECK tables=218 covered=200 arms=573 bad=0`、`BASH_ARMS 6/16 bad=0`、`ARM_TOTAL files=311 arms=1056 dupes=0 repeats=0`。
- **U-1625：② 表格表头补等宽 semibold。** 缺陷形状：`MarkdownScanner.collectTable` 把 `| --- |` 分隔行丢掉后，表头与表体在渲染里**同字号、同字重、同颜色**，作者写下的表头意图在屏幕上没有证人。修法：新 `TableHeaderPresentation`（表头字体 = `monospacedSystemFont(codeFontSize, .semibold)`；`headerRange(in:)` 取表格块第一行），`MarkdownPresentation` 只给第一行换字体 —— 等宽字体的 semibold 与 regular **推进宽度相同**，所以不挪列（R234 明确说过列重排是刻意不做的）。新夹具 `detail-table` 的两行**逐字相同**，墨量比就是字重差的读数：light `表头墨=799 表体墨=569 比=1.40`、dark `855/685 比=1.25`，左沿 `23.0/23.5pt`（0.5pt 是笔画宽度，不是挪列）、行距 `9.0pt`；旧形状（两行 regular）由刀 M1206 复现，比≈1.00。帧变化恰 **2 张旧帧**（`detail-markdown-rendered` 亮/暗的表头变重）+ **2 张新帧**（`detail-table` 亮/暗），基线 **240→242**、复验 **242/0/0/0**。已逐张看 `detail-table` 亮/暗与 `detail-markdown-rendered`：表头明显更重、竖线同轴、暗档可读。
- **U-1626：判据与刀。** 新单测 `TableHeaderPresentationTests` 3 条（首行范围、字体等宽+semibold+字号、属性串只加粗表头不碰表体/段落）；新帧判据 `testTableHeadersAreSemibold`（同帧两行墨量比 ≥1.08、左沿差 ≤1pt、行距 <30pt，带通道前提 `TABLE_HEADER_NOT_RUN=runner-detail-frame-plain`）。`M1206–M1207` **2/2 CAUGHT**、RESTORE_CLEAN=yes（表头字体不写 / 整块都 semibold）；第一次 0 告警门抓到判据里一个未使用的 `width` 变量，删掉后冷编 **warnings=0** 复跑。
- **U-1627：八步与具名 NOT-RUN。** build **0 告警**（含修掉那一条）；捕获 **147 条 / 4 skip / 0 失败 / 242 帧**；帧基线 `COMPARED=242 CHANGED=0 MISSING=0 ADDED=0`（update 之后复验）；全量 **1192/57/5**（5 个断言全在 `SelectionRevealAnimationTests` 的 3 条用例：2/2/1；单跑 `caffeinate -u` 后 **4/4 passed**：`OFFSET 0/199.0/1438`、`TIME 18/9/47.5/1438`、`CHANNEL 0→83.0→600 变化 40524/110400 重抓=no`）⇒ 具名 `LOCAL_SCROLL_SESSION_NOT_RUN=full-suite-order`（449，不改门槛）；连着第二次单跑出现过一次**全 0 采样**（16 帧全 0，下一次复跑 4/4 绿）⇒ 记 `SCROLL_REVEAL_SESSION_BLIND=one-run-zero-readings`，不降门槛；换装 `INSTALL_RESULT=ok / SHA_MATCH=1 / 381=381 / SMOKE_OK=1`；清账 `格=162 声明=63 不成立=0/63`；产品面连续零改动 **1** 轮（as-of 439，现读 `python3 scripts/product_streak.py --streak-for 439`，last=1f7c4f1）。电池 `Ran 683 / OK (skipped=5)`（台账后复跑）。**具名 NOT-RUN**：① 表格表头字重的 runner 1x 读数（R440 提交后的新跑才读）；② HTML 路径的表格表头没有同档处理（466）；③ `MOTION_FLOOR_FACTS` 的 notice-banner 本跑未判（具名 NOT-RUN，不是红）；④ 设置内容列 1x 平涂；⑤ 设置脚注带 1x；⑥ 主窗口 content 帧 1x；⑦ 高夹具 1x；⑧ 13+ 菜单像素/标题；⑨ 真实拖拽；⑩ Dock 像素；⑪ 源图标最小窗文字 1x；⑫ 本地全量 5 条滚动红（449）；⑬ 2x/extended；⑭ 固定块揭示偏移（455）；⑮ 跨年时间（456）；⑯ 主列表暗档文字盲区（457）；⑰ 真机/多屏（447）；⑱ 真菜单栏、12 实时腿；⑲ `table-lazy-rows`；⑳ HTML 六档字号（460）；㉑ 清除 × 命中区（461）；㉒ 分隔线令牌（462）；㉓ 展开态已加载内容无帧（463）；㉔ 其它自绘控件帮助文本（464）；㉕ HTML 引用块无导引线（465）；㉖ 437–466 仍开。

"""

ITER_SECTION = u"""## Round 437 · R440（第 439 轮 · 2026-10-28）：Markdown 表格表头补等宽 semibold（解析器丢掉 `| --- |` 行后表头/表体同形；新夹具两行逐字相同：light 墨量比 1.40、dark 1.25，左沿 23.0/23.5pt 同轴、行距 9.0pt；2 张旧帧变化 + 2 张新帧，基线 240→242）

`collectTable` 把 `| --- |` 分隔行丢掉后，表头与表体在渲染里同字号、同字重、同颜色 —— 作者写下的表头意图在屏幕上没有证人。修法：新 `TableHeaderPresentation`（表头 = 等宽 semibold、`headerRange` 取第一行），属性串只给表头换字体；等宽字体 semibold 与 regular 推进宽度相同，不挪列。新夹具 `detail-table` 两行逐字相同：light 墨量比 1.40、dark 1.25，左沿 23.0/23.5pt、行距 9.0pt；旧形状由刀复现 ≈1.00。2 张旧帧变化 + 2 张新帧，基线 242/0/0/0。M1206–M1207 2/2；预检 218/200/573 bad=0；HIDDEN 305/990 rot=0。⓪：push no-op、HEAD=fc88822、ahead=0；`40573915633 ↔ 42c09ad` 与 `40573988870 ↔ fc88822` 都 success、失败步骤 0；`MARKDOWN_QUOTE_RULE` 1x 两档 57.0pt、源 15.0pt；两个采样红未复现；436 = `judged=4/5 executed=77 not-run=notice-banner REDS=0`。本地全量 1192/57/5（5 断言全在 SelectionRevealAnimationTests），单跑 4/4（OFFSET 0/199/1438；TIME 18/9/47.5/1438；CHANNEL 0→83→600、40524/110400）⇒ 具名 LOCAL_SCROLL_SESSION_NOT_RUN=full-suite-order（449）；另一次单跑全 0 采样记 `SCROLL_REVEAL_SESSION_BLIND`。捕获 147/4/0、242 帧；换装 ok/SHA_MATCH=1/381=381/SMOKE_OK=1；清账 162/63/0；电池 683/5。

**七维度自评**（恰七行，每格 n/15）：

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | 14/15 | `detail-table` 亮/暗与 `detail-markdown-rendered` 都逐张看过：表头更重、竖线同轴、暗档可读；同帧墨量比 1.40/1.25。扣 1：新夹具没有"旧代码"的基线帧，旧形状 1.00 由刀复现而非旧帧。 |
| 判据有效性 | 15/15 | 两行逐字相同 ⇒ 同帧墨量比是纯字重差；M1206（不写）/M1207（整块都写）2/2，范围与存在性都被咬住。 |
| 假绿防御 | 15/15 | 不读绝对墨量（跟字体版本走），只读同帧两行比；左沿同轴与行距同时断言；通道前提具名。 |
| 产品面推进 | 14/15 | 把一个被解析器丢掉的结构意图（表头）恢复成可见的字重差，且不挪列；扣 1：只动字重，列重排仍按 R234 刻意不做。 |
| 台账一致性 | 15/15 | U-1623…U-1627、D-436、两跑签收、436 judged=4/5 与 242 帧都从命令/测试输出解析。 |
| 交付诚实性 | 15/15 | 两个采样红明确写"未复现"；notice-banner 未判写 NOT-RUN 不写绿；一次全 0 采样单列具名；新字重的 1x 读数写"还要等新跑"。 |
| 可复核性 | 15/15 | 两行夹具、1.08 地板、左沿 1pt、行距 30pt、刀号与 precheck/rot、基线 242、换装/清账都在。 |

均分 = 103/105 ≈ 14.7/15（98）。"""

DECISION_436 = u"""## D-436 表格表头用等宽 semibold 与表体分开（R440）

- 背景：`MarkdownScanner.collectTable` 丢掉 `| --- |` 分隔行后，表头与表体在渲染里完全同形（同字号、同字重、同颜色）。R234 已决定不改列宽重排，但"表头是哪一行"是作者写下的结构意图，不该一起丢。
- 决定：新增 `TableHeaderPresentation` —— 表头字体 = `monospacedSystemFont(codeFontSize, .semibold)`，`headerRange(in:)` 取表格块第一行；`MarkdownPresentation` 只给第一行换字体，其余行与段落不动。
- 理由：等宽字体的 semibold 与 regular 推进宽度相同 ⇒ 不挪列、不需要重排；同帧两行（逐字相同的夹具）墨量比 light 1.40 / dark 1.25，旧形状 1.00。
- 兼容性/迁移：只影响 Markdown 渲染路径；HTML 路径没有同档处理（466）；纯文本路径不受影响。帧变化 2 张旧帧 + 2 张新帧，基线 240→242。
- 边界：字重差在极小字号/低分屏上可能更弱；runner 1x 读数待新跑（R441 ⓪）。
- 回滚：删 `attributedString` 里的表头字体 post-pass 即可恢复旧帧；或 `git revert`。
"""

CHANGELOG_SECTION = u"""### 详情 Markdown 表格表头补等宽 semibold（同帧墨量比 light 1.40 / dark 1.25、左沿 23.0/23.5pt、行距 9.0pt；2 张旧帧变化 + 2 张新帧、基线 242）（R440 / 第 439 轮 / Round 437 / U-1623…U-1627 · 产品 3 文件，详情正文表格位）

"""

BACKLOG_SECTION = u"""437 追记（R440 · 仍开）：本轮只动详情表格表头；主列表仍不匹配 `sourceAppName`。

449 追记（R440 · 仍开）：本机全量仍 5 断言红（3 条用例）、单跑 4/4 绿（OFFSET 0/199/1438；TIME 18/9/47.5/1438；CHANNEL 40524/110400）；另一次单跑全 0 采样（16 帧），下一次复跑绿 ⇒ `SCROLL_REVEAL_SESSION_BLIND=one-run-zero-readings`。

451 追记（R440 · 仍开）：macOS 12 的详情头部阈值本轮未动。

452 追记（R440 · 仍开）：脚注 1x 具名 NOT-RUN 仍生效。

453 追记（R440 · 仍开）：真实系统拖拽会话仍无自动化验收。

454 追记（R440 · 仍开）：菜单具名标记仍未发射。

455 追记（R440 · 仍开）：固定条目滚动到位的独立偏移验收仍缺。

456 追记（R440 · 仍开）：跨年记录仍无年份。

457 追记（R440 · 仍开）：主列表暗档文字在离屏帧里仍是黑底黑字。

458 追记（R440 · 仍开）：`FILE_ROW_SYMBOL_NOT_RUN` 已按名生效；CI 行首符号像素证人仍缺。

459 追记（R440 · 仍开）：设置内容列/高夹具在 1x 整列平涂。

460 追记（R440 · 仍开）：HTML 六档以上字号仍会后排压到 12pt。

461 追记（R440 · 仍开）：浮层清除 × 命中区 18pt。

462 追记（R440 · 仍开）：批量操作栏分隔线的 0.18 透明度未提令牌。

463 追记（R440 · 仍开）：展开态已加载内容仍无帧（只有 loading 分支）。

464 追记（R440 · 仍开）：其它自绘控件（浮层清除 ×、批量栏五颗）仍无同类帮助判据。

465 追记（R440 · 仍开）：HTML 引用块没有导引线（只接了 Markdown 路径）。

**466. HTML 表格的表头没有同档字重：R440 只改了 Markdown 路径**（R440 观察）
    现象：`TableHeaderPresentation` 只在 `MarkdownPresentation.attributedString` 里接线；`HtmlRendering` 产出的属性串即使有表格也没有表头字重，且 `detail-html-rendered` 夹具当前没有表格，帧上无对象。
    修法（下一轮若需要）：给 HtmlRendering 的 `<table>` 首行打同一字体（或同一属性），并在 HTML 夹具里加一张两行逐字相同的表 + 帧判据（墨量比 ≥1.08）。
"""

STATE_SECTION = u"""## R440 状态（2026-10-28 · 本地 · 第 439 轮 / Round 437）：Markdown 表格表头补等宽 semibold（解析器丢掉 `| --- |` 行后表头/表体同形；新夹具两行逐字相同：light 墨量比 1.40 / dark 1.25，左沿 23.0/23.5pt、行距 9.0pt；2 张旧帧变化 + 2 张新帧，基线 240→242）；R439 两跑都 success（`MARKDOWN_QUOTE_RULE` 1x 57.0pt、两个采样红未复现、436=judged 4/5 executed 77 REDS 0）（产品 3 文件，详情正文表格位）

最后更新：2026-10-28（本地 · R440 / 第 439 轮 / Round 437）：`MarkdownScanner.collectTable` 丢掉 `| --- |` 分隔行后，表头与表体在渲染里同字号、同字重、同颜色。新 `TableHeaderPresentation`（表头 = 等宽 semibold、`headerRange` 取第一行）；`MarkdownPresentation` 只给表头换字体，等宽字体 semibold 与 regular 推进宽度相同 ⇒ 不挪列。新夹具 `detail-table` 两行逐字相同：light `表头墨=799 表体墨=569 比=1.40`、dark `855/685 比=1.25`，左沿 `23.0/23.5pt`（0.5pt 是笔画宽）、行距 `9.0pt`；旧形状由 M1206 复现 ≈1.00。帧变化 **2 张旧帧 + 2 张新帧**，基线 **240→242 / 0/0/0**。`M1206–M1207` **2/2 CAUGHT**；新单测 3 条 + 新帧判据 1 条；预检 **218/200/573 bad=0**、ARM **311 文件 / 1056 把**、HIDDEN **305/990 rot=0**；0 告警门先抓到判据里一个未使用的 `width`，删后冷编 `warnings=0`。⓪：push no-op、HEAD = origin/main = `fc88822`、**ahead=0**；`40573915633 ↔ 42c09ad` 与 `40573988870 ↔ fc88822` 都 **success、失败步骤 0**；`MARKDOWN_QUOTE_RULE` 1x 两档 `竖墨=57.0pt 源=15.0pt`（文字左 39.0/38.0、净距 12.0/11.0）；`testProductDurationRevealStillMovesOverTime` **passed**、动效标签红 skipped / Motion gate failed=0 ⇒ 两个采样红未复现；两跑同报 4 张环境帧差（login-failed / receipt-failed）⇒ 稳定机器差异；**436** = `MOTION_FLOOR_FACTS judged=4/5 executed=77 not-run=notice-banner 红的用例=- 汇总行报红=0`（notice-banner 具名 NOT-RUN，不是红）。本地全量 **1192/57/5**：5 断言全在 `SelectionRevealAnimationTests`（3 条用例），单跑（caffeinate-u 后）**4/4 passed**（`OFFSET 0/199.0/1438`、`TIME 18/9/47.5/1438`、`CHANNEL 0→83.0→600 变化 40524/110400 重抓=no`）⇒ 具名 `LOCAL_SCROLL_SESSION_NOT_RUN=full-suite-order`（449）；另一次单跑全 0 采样记 `SCROLL_REVEAL_SESSION_BLIND=one-run-zero-readings`，不降门槛。捕获 **147/4/0 / 242 帧**；基线 **242/0/0/0**；换装 `ok / SHA_MATCH=1 / 381=381 / SMOKE_OK=1`；清账 `格=162 声明=63 不成立=0/63`；产品面连续零改动 **1** 轮（as-of 439，现读 `python3 scripts/product_streak.py --streak-for 439`，last=1f7c4f1）。电池 `Ran 683 / OK (skipped=5)`（台账后复跑）。

本轮做了什么：
① ⓪ 两跑 success、失败步骤 0；`MARKDOWN_QUOTE_RULE` 1x 57.0/15.0、两个采样红未复现（不写绿，写未复现）；436 judged=4/5 executed=77 REDS=0（notice-banner NOT-RUN）。
② 产品：表格表头补等宽 semibold（旧两行同形 → 新 light 1.40 / dark 1.25；2 张旧帧 + 2 张新帧，基线 242）。
③ 判据：M1206–M1207 2/2；新单测 3 条 + 帧判据（同帧墨量比/左沿/行距）；precheck 218/200/573；hidden rot 0；0 告警门修掉一个未使用变量。
④ 436：`judged=4/5 executed=77 not-run=notice-banner 红的用例=- 汇总行报红=0`；不重猜 must_judge。
⑤ 367：hidden 表 305 / 可判 990 / rot 0。
⑥ 捕获 147/4/0、242 帧；换装 ok；清账 162/63/0；帧基线 242/0/0/0；本地全量 1192/57/5（5 条滚动红具名会话/顺序 NOT-RUN）。

NOT-RUN / 阻塞（分开写）：① 表头字重的 runner 1x 读数（本轮提交后的新跑才读）；② HTML 表格表头无同档处理（466）；③ 436 的 notice-banner 本跑未判（NOT-RUN，不是红）；④ 设置内容列 1x 平涂；⑤ 设置脚注带 1x；⑥ 主窗口 content 帧 1x；⑦ 高夹具 1x；⑧ 13+ 菜单像素/标题；⑨ 真实拖拽；⑩ Dock 像素；⑪ 源图标最小窗文字 1x；⑫ 本地全量 5 条滚动红（449）；⑬ 2x/extended；⑭ 固定块揭示偏移（455）；⑮ 跨年时间（456）；⑯ 主列表暗档文字盲区（457）；⑰ 真机/多屏（447）；⑱ 真菜单栏、12 实时腿；⑲ `table-lazy-rows`；⑳ HTML 六档字号（460）；㉑ 清除 × 命中区（461）；㉒ 分隔线令牌（462）；㉓ 展开态已加载内容无帧（463）；㉔ 其它自绘控件帮助文本（464）；㉕ HTML 引用块无导引线（465）；㉖ 437–466 仍开。

下一轮（R441）的靶：⓪ 先 `git push origin main`（禁 amend/force）并复核 ahead=0；读 R440 主笔+追记 head 跑的全部失败步骤（成对 run↔commit），重点看新帧判据 `TABLE_HEADER` 两档墨量比 ≥1.08、左沿差 ≤1pt，以及两个 runner 采样名是否复现；in_progress/0 字节不算绿；① 367 现读 rot=0，按 `HIDDEN_ROT` 查新腐烂；② 继续产品视觉位并落 Sources、换缺陷类别（不要再做表格表头/引用导引线/录制帮助/多文件展开/批量分隔/浮层搜索/图片/HTML/排除名单/行内符号/时间列/分区头/侧栏脚注/详情头部/Dock/菜单栏/横幅/回执/热图/计数/空态/无结果/焦点/悬停/选中/滚动/CTA）；③ 436 只复核新跑 Motion floor，不重猜 `must_judge`。
"""

R440_REPORT_BULLET = u"""- **R440（表格表头位）**：`MarkdownScanner.collectTable` 丢掉 `| --- |` 分隔行后，表头与表体在渲染里同字号、同字重、同颜色 —— 作者写下的表头意图在屏幕上没有证人。新 `TableHeaderPresentation`（表头 = 等宽 semibold、`headerRange` 取第一行）；`MarkdownPresentation` 只给表头换字体，等宽字体 semibold 与 regular 推进宽度相同 ⇒ 不挪列（R234 的列重排仍刻意不做）。新夹具 `detail-table` 两行逐字相同：light **墨量比 1.40**、dark **1.25**，左沿 **23.0/23.5pt**、行距 **9.0pt**；旧形状由刀复现 ≈1.00。帧变化 **2 张旧帧 + 2 张新帧**，基线 **240→242 / 0/0/0**。`M1206–M1207` **2/2**；新单测 3 条 + 新帧判据 1 条；预检 218/200/573 bad=0、ARM 311/1056、HIDDEN 305/990 rot=0。⓪：push no-op、HEAD=origin/main=`fc88822`、ahead=0；R439 两跑 `40573915633 ↔ 42c09ad`、`40573988870 ↔ fc88822` 都 **success、失败步骤 0**；`MARKDOWN_QUOTE_RULE` 1x 两档 **57.0pt**、源 15.0pt；`testProductDurationRevealStillMovesOverTime` passed、动效标签红 skipped / Motion gate failed=0 ⇒ 两个采样红未复现；两跑同报 4 张环境帧差（稳定机器差异）；**436** = `judged=4/5 executed=77 not-run=notice-banner REDS=0`（notice-banner NOT-RUN）。本地全量 **1192/57/5**：5 断言全在 SelectionRevealAnimationTests，单跑 4/4（OFFSET 0/199/1438；TIME 18/9/47.5/1438；CHANNEL 0→83→600、40524/110400）⇒ 具名 `LOCAL_SCROLL_SESSION_NOT_RUN=full-suite-order`（449）；另一次单跑全 0 采样记 `SCROLL_REVEAL_SESSION_BLIND`。捕获 147/4/0、242 帧；换装 ok/SHA_MATCH=1/381=381/SMOKE_OK=1；清账 162/63/0；电池 683/5。
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
if u"第 439 轮（R440" in audit:
    raise SystemExit("REFUSED AUDIT 已有 R440 节")
if u"## Round 437 · R440" in iter_text:
    raise SystemExit("REFUSED ITERATION 已有 Round 437")
if u"## D-436" in decisions:
    raise SystemExit("REFUSED DECISIONS 已有 D-436")
if u"详情 Markdown 表格表头补等宽 semibold" in changelog:
    raise SystemExit("REFUSED CHANGELOG 已有该标题")
if u"**466." in backlog:
    raise SystemExit("REFUSED BACKLOG 已有 466")
if state.count(u"## R439 状态") != 1:
    raise SystemExit("REFUSED STATE 锚点命中 %d 次" % state.count(u"## R439 状态"))
U_CELL_OLD = u"U-31 … U-1622（R439 现读抬到最新一节）"
if report.count(U_CELL_OLD) != 1:
    raise SystemExit("REFUSED REPORT U 格命中 %d 次" % report.count(U_CELL_OLD))
if report.count(u"AGENT_STATE.md` 的 R439 节 ②") != 1:
    raise SystemExit("REFUSED REPORT §13 指针命中 %d 次" % report.count(u"AGENT_STATE.md` 的 R439 节 ②"))

new_audit = audit.replace(AUDIT_TITLE, AUDIT_SECTION + AUDIT_TITLE, 1)
new_iter = iter_text.rstrip() + "\n\n" + ITER_SECTION + "\n"
new_decisions = decisions.rstrip() + "\n\n" + DECISION_436 + "\n"
marker = u"## [Unreleased]\n"
if changelog.count(marker) != 1:
    raise SystemExit("REFUSED CHANGELOG [Unreleased] 命中 %d 次" % changelog.count(marker))
new_changelog = changelog.replace(marker, marker + "\n" + CHANGELOG_SECTION, 1)
new_backlog = backlog.rstrip() + "\n\n" + BACKLOG_SECTION + "\n"
new_state = state.replace(u"## R439 状态", STATE_SECTION + u"## R439 状态", 1)
new_report = report.replace(U_CELL_OLD, u"U-31 … U-1627（R440 现读抬到最新一节）", 1)
new_report = new_report.replace(u"AGENT_STATE.md` 的 R439 节 ②",
                                u"AGENT_STATE.md` 的 R440 节 ②", 1)
new_report = new_report.rstrip() + "\n\n" + R440_REPORT_BULLET + "\n"

wr(AUDIT, new_audit)
wr(ITER, new_iter)
wr(DECISIONS, new_decisions)
wr(CHANGELOG, new_changelog)
wr(BACKLOG, new_backlog)
wr(STATE, new_state)
wr(REPORT, new_report)
print("LEDGERS_R440_OK audit=%d iter=%d decisions=%d changelog=%d backlog=%d state=%d report=%d"
      % (len(new_audit), len(new_iter), len(new_decisions), len(new_changelog),
         len(new_backlog), len(new_state), len(new_report)))
