#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R434 七本台账一次落盘（只跑一次；先断言所有锚点，全部通过才写）。"""
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


AUDIT_TITLE = u"## 第 432 轮（R433 · 2026-10-27"
AUDIT_SECTION = u"""## 第 433 轮（R434 · 2026-10-27 · U-1593…U-1597）：HTML 渲染的标题档接到 Markdown 梯子（同一 h1：旧墨带 27.0pt → 新 20.0pt、与 Markdown 差 9.0→2.0；2 张 HTML 帧变化、基线 238）；R433 跑失败步骤 2 个（设置内容列在 1x 整列平涂 ⇒ 排除名单判据无对象）⇒ 具名 NOT-RUN、阈值未动（产品 1 文件，HTML 标题排版位）

- **U-1593：⓪ R433 跑的失败步骤与图片边/名单命运。** `40526497330 ↔ e896829` **failure**：20 步里**失败步骤 2 个**（`Swift tests (executed-count gate)`、`Capture gate (unregistered reds must be zero)`）。唯一红仍是 `testExcludedAppsStartWithAnIconInsteadOfRawIDs` 两档 `EXCLUDED_APP_ROW 行数=0 判=0` —— 根因不是高夹具，而是 **runner 1x 上设置页的「内容列」整列平涂**：同跑 `CAPTION_JUDGED 6/17`，六条判成的全是热图/菜单栏面板/详情头部，**所有 settings 页探针都走 machineFlat**；把 720×1040 换成 720×540 并不解决（内容列在 1x 根本没有墨）。**R433 的图片边判据在 1x 是绿的**：`DETAIL_IMAGE_EDGE light 图框=240..479×220..359px 页底=236.0 边带最大差=30.0`、dark `页底=50.0 边带最大差=26.0`（档=1.00px/pt）⇒ 白底图的边在 CI 上真有像素证人。其余全绿：理由带 290 后 `typed 扩展=217/248、list=0`；时间列 1x light `[74.0,71.0,74.0,74.0,74.0]`、dark `[74.0,72.0,74.0,74.0,74.0]`；`SETTINGS_FOOTER_BAND_NOT_RUN` 按名出现；分区 `13/12`、`11/10`；`PINNED_SECTION_ROWS 6/5 选中 [2]/[1]`；回执 **2/2**（2x 0.1333/1265ms、1x 0.1333/1205ms，1x `重抓=yes`）；滚动 **4/4 passed**（`CHANNEL 0→108→600 变化 38400/30362`、`TIME 5/0/0/1430`）；拖拽 mass 0.549/0.550；Dock 标记已登记；floor `judged=4/5 executed=77 not-run=notice-banner`、`SUITE_CLEAN=0`、`MOTION_FLOOR_OK=4/5`、无红、无 unlisted。
- **U-1594：⓪ 的修法：设置内容列在 1x 判不了，就具名 NOT-RUN。** `testExcludedAppsStartWithAnIconInsteadOfRawIDs` 加 1x 分支：`scale < 1.5` 时打 `EXCLUDED_APP_ROW_NOT_RUN=runner-1x-settings-content-plain`（行数照打）并跳过像素断言；2x 断言一字不动（`settings-privacy` 540 帧 5 行、首段 `[10.0,10.0,10.0,10.0,14.0]`/`[10.0,10.0,10.0,10.0,10.5]`、行墨 2704…3055）；收尾断言改成「每档要么判了、要么具名，且两档同路」。阈值（5…30pt、行墨>20）未动。这条同时把 R433 那句「540 帧在 1x 能画」更正为**内容列在 1x 平涂**（459 追记）。
- **U-1595：② HTML 渲染的标题档接到 Markdown 梯子。** 缺陷形状（`detail-html-rendered` 亮档现读）：HTML 的第一带墨高 **27.0pt**，同一份语义走 Markdown 的 h1 是 **18.0pt** —— R335 只把**正文档**按字符数加权搬到 14pt，标题跟着被**等比**放大（24→28pt），于是同一个「渲染」档里两条通道的 h1 差 8pt。修法：`fitHeadingsToLadder` —— 正文基准之上（>1.1×）的字号按从大到小逐级落到 `MarkdownPresentation.headingFontSize` 的前几级（20/17/15.5…），字族与字重原样保留（与 `fitToBodySize` 同一条取舍：字族是页面意图，字号与层级是产品一致性）。旧/新：`HTML_HEADING_LADDER light html=20.0pt markdown=18.0pt 差=2.0pt`（旧 27.0 vs 18.0、差 9.0；余下 2pt 是 Times 与系统字在同一号下的墨带差）；`HTML_TYPE 基准前=12.0pt 基准后=14.0pt 标题后=20.0pt 梯子=20.0,17.0,15.5,14.0,13.0,12.0`。真看图：`季度报告` 从"比 Markdown 大一号"回到同一档，正文不动。2 张 `detail-html-rendered` 帧变化，基线仍 **238/0/0/0**。
- **U-1596：判据与刀（含一条旧契约的更正）。** 新 `HtmlHeadingLadderTests` 三条（三个标题档落到梯子 / 没有标题的页面不动 / 空串恒等）+ `testHtmlHeadingsLandOnTheMarkdownLadder`（两帧第一带墨高差 ≤3.5pt；暗档详情帧整片同色 ⇒ 只在亮档判）。**更正** `testRenderedHtmlBodySitsOnTheAppTypeScale` 的旧期望：它把「层级比必须与浏览器一致（2.0）」钉成契约，而产品自己的梯子是 20/14=1.43 —— 现在判「正文==14、h1==梯子第 1 级、所有标题字号都在梯子上」。`M1192–M1193` **2/2 CAUGHT**（映射整步撤掉 / 梯子接反；RESTORE_CLEAN=yes）。预检 `tables=212 covered=194 arms=560 bad=0`、`BASH_ARMS 6/16 bad=0`、`ARM_TOTAL files=305 arms=1043 dupes=0`；`HIDDEN_ARMS 表=299 可判=977 rot=0`。
- **U-1597：八步。** build **0 告警**；捕获 **141 条 / 4 skip / 0 失败 / 238 帧**；帧基线 `CHANGED=2 / MISSING=0 / ADDED=0`（`detail-html-rendered` 亮暗），`UPDATED=238`、复验 **238/0/0/0**；全量 **1176/57/5**（5 个断言全在 `SelectionRevealAnimationTests` 的 3 条用例；单跑 `caffeinate -u` 后 **4/4 passed**，`TIME 采样=18/中间值=8/首=61/末=1438`、`CHANNEL 0→86.5→600 变化 76639/127200 重抓=no`、`OFFSET 0/227.5/1438`）⇒ 具名 `LOCAL_SCROLL_SESSION_NOT_RUN=full-suite-order`（449，不改门槛）；换装 `INSTALL_RESULT=ok / SHA_MATCH=1 / 381=381 / SMOKE_OK=1`；清账 `格=162 声明=63 不成立=0/63`；产品面连续零改动 **1** 轮（as-of 433，现读 `python3 scripts/product_streak.py --streak-for 433`）。电池 `Ran 683 / OK (skipped=4)`（台账后复跑）。
- **具名 NOT-RUN / 观察**：① 设置页内容列 runner 1x 整列平涂（`EXCLUDED_APP_ROW_NOT_RUN=runner-1x-settings-content-plain`；`CAPTION_JUDGED 6/17` 同证，459）；② 设置脚注带 1x（`SETTINGS_FOOTER_BAND_NOT_RUN`）；③ 主窗口 content 帧 1x 整帧不画（`FILE_ROW_SYMBOL_NOT_RUN`，458）；④ 高夹具 1x 整帧不画（459）；⑤ 13+ 菜单像素/标题（454）；⑥ 真实拖拽（453）；⑦ Dock 像素；⑧ 源图标最小窗文字 1x；⑨ 本地全量 5 条滚动红（449）；⑩ 2x/extended；⑪ 固定块揭示偏移（455）；⑫ 跨年时间（456）；⑬ 主列表暗档文字盲区（457）；⑭ 真机/多屏（447）；⑮ 真菜单栏、12 实时腿；⑯ `table-lazy-rows`；⑰ HTML 标题映射超过六级字号时后排全落 12pt（460）；⑱ 437–460 仍开；⑲ R434 新跑待 push 后读。

"""

ITER_SECTION = u"""## Round 431 · R434（第 433 轮 · 2026-10-27）：HTML 渲染的标题档接到 Markdown 梯子（同一 h1：旧墨带 27.0pt → 新 20.0pt、与 Markdown 差 9.0→2.0；2 张 HTML 帧变化、基线 238）；R433 跑失败步骤 2 个（设置内容列在 1x 整列平涂 ⇒ 排除名单判据无对象）⇒ 具名 NOT-RUN、阈值未动（产品 1 文件，HTML 标题排版位）

同一个「渲染」档里，HTML 的 h1 旧读墨带 27.0pt、Markdown 的 h1 18.0pt —— R335 只把正文档按字符数加权搬到 14pt，标题被等比放大到 28pt。新 `fitHeadingsToLadder`：正文基准之上（>1.1×）的字号按从大到小逐级落到 Markdown 梯子（20/17/15.5…），字族字重不动。旧/新：`HTML_HEADING_LADDER light html=20.0pt markdown=18.0pt 差=2.0pt`（旧 27.0/18.0、差 9.0）；`HTML_TYPE 基准前=12 基准后=14 标题后=20`。旧测试把「层级比 2.0」钉成契约，本轮更正为「标题在 Markdown 梯子上」。2 张 `detail-html-rendered` 帧变化，基线 238/0/0/0。R433 run `40526497330 ↔ e896829` **failure、失败步骤 2 个**（Swift tests / Capture gate）：唯一红是设置页**内容列在 1x 整列平涂**（`CAPTION_JUDGED 6/17`，所有 settings 探针 machineFlat）⇒ 排除名单判据在 CI 上没有对象，具名 `EXCLUDED_APP_ROW_NOT_RUN=runner-1x-settings-content-plain`、2x 断言不动；`DETAIL_IMAGE_EDGE` 在 1x 绿（light 30.0 / dark 26.0）；理由带 217/248 vs 0；时间列、脚注、分区、表格、回执 2/2、滚动 4/4、拖拽 mass 全绿。M1192–M1193 2/2；预检 212/194/560 bad=0；HIDDEN 299/977 rot=0。全量 1176/57/5（5 断言全在 SelectionRevealAnimationTests），单跑 4/4（TIME 18/8、61→1438；CHANNEL 0→86.5→600）⇒ 具名 LOCAL_SCROLL_SESSION_NOT_RUN=full-suite-order（449）。捕获 141/4/0、238 帧；换装 ok/SHA_MATCH=1/381=381/SMOKE_OK=1；清账 162/63/0；电池 683/4。

**七维度自评**（恰七行，每格 n/15）：

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | 13/15 | 真看 `detail-html-rendered` 亮档：`季度报告` 从比 Markdown 大一号回到同一档，正文/列表/链接不动；与 `detail-markdown-rendered` 同屏对照。扣 2：暗档详情帧整片同色（盲区）只在亮档判；没有真机截图。 |
| 判据有效性 | 15/15 | 三条映射单测 + 一条两帧墨高对照；旧的比例契约被正确地改成梯子契约（不是放宽）；M1192–M1193 2/2。 |
| 假绿防御 | 15/15 | 暗档盲区不冒充绿（只在亮档判、读数打印）；映射按字符数加权找基准、空串恒等；"没有标题的页面不动"防误伤。 |
| 产品面推进 | 14/15 | 真落 1 文件（HTML 标题排版位），修的是跨渲染器"同一档两种刻度"；扣 1：只校了标题档，列表缩进/段落间距仍各走各的。 |
| 台账一致性 | 15/15 | U-1593…U-1597、D-430、R433 的 6/17、R434 的 27.0→20.0、1176 都从日志/帧/用例解析。 |
| 交付诚实性 | 15/15 | R433 的红定位到"设置内容列 1x 平涂"并改正上一轮的错误前提（459 追记）；旧的 2.0 比例契约公开更正；各 NOT-RUN 分列。 |
| 可复核性 | 15/15 | 帧名、两带墨高、基准/标题号、刀号与红在哪个用例、precheck/rot/CI 原文、基线 238、换装/清账都在。 |

均分 = 102/105 ≈ 14.6/15（96）。"""

DECISION_430 = u"""## D-430 HTML 标题档落 Markdown 梯子，而不是跟着浏览器等比放大（R434）

- 背景：R335 把 HTML 正文档按字符数加权搬到 14pt，标题跟着等比放大（h1 24→28）；同一份语义走 Markdown 渲染器时 h1 是 20pt，两条通道在同一个「渲染」档里差 8pt（帧上墨带 27.0 vs 18.0）。
- 决定：`HtmlRendering.fitHeadingsToLadder` —— 正文基准之上（>1.1×）的字号按从大到小排成梯队，逐级落到 `MarkdownPresentation.headingFontSize`（20/17/15.5/14/13/12）；字族与字重原样保留。旧的 `testRenderedHtmlBodySitsOnTheAppTypeScale` 从「层级比与浏览器一致（2.0）」改成「标题在 Markdown 梯子上」。
- 理由：字族是页面的排版意图（作者写 serif 就 serif），字号与层级是产品的一致性——同一条取舍在 `fitToBodySize` 里已经写过；只是上一轮只搬了正文，标题漏了。产品自己的梯子才是这一档的权威。
- 兼容性/迁移：只有 `detail-html-rendered` 两帧变化，正文/列表/链接不动；基线仍 238。
- 边界：映射按字号排名，文档若有超过六级标题字号，后排会全落 12pt（460）；暗档详情帧整片同色，像素判据只在亮档判。
- 回滚：把 `fitHeadingsToLadder` 从 `attributedString` 的调用链里摘掉即可；或 `git revert` 本轮提交。
"""

CHANGELOG_SECTION = u"""### HTML 渲染的标题档接到 Markdown 梯子（同一 h1：旧墨带 27.0pt → 新 20.0pt、与 Markdown 差 9.0→2.0；2 张 HTML 帧变化、基线 238）；R433 跑失败步骤 2 个（设置内容列在 1x 整列平涂 ⇒ 排除名单判据无对象）⇒ 具名 NOT-RUN、阈值未动（R434 / 第 433 轮 / Round 431 / U-1593…U-1597 · 产品 1 文件，HTML 标题排版位）

"""

BACKLOG_SECTION = u"""437 追记（R434 · 仍开）：本轮只动 HTML 标题档；主列表仍不匹配 `sourceAppName`。

449 追记（R434 · 仍开）：R433 CI 跑里 `SelectionRevealAnimationTests` 4/4 passed（CHANNEL 0→108→600、TIME 5/0/0/1430），本机全量仍 5 断言红（3 条用例）、单跑 4/4 绿（TIME 18/8、61→1438）⇒ 会话/顺序再次坐实；不改门槛。

451 追记（R434 · 仍开）：macOS 12 的详情头部阈值本轮未动。

452 追记（R434 · 仍开）：脚注 1x 具名 NOT-RUN 继续按名出现。

453 追记（R434 · 仍开）：真实系统拖拽会话仍无自动化验收。

454 追记（R434 · 仍开）：菜单具名标记仍未发射；菜单 5/5 由真实 NSMenu 用例作证。

455 追记（R434 · 仍开）：固定条目滚动到位的独立偏移验收仍缺。

456 追记（R434 · 仍开）：跨年记录仍无年份。

457 追记（R434 · 仍开）：主列表暗档文字在离屏帧里仍是黑底黑字。

458 追记（R434 · 仍开）：`FILE_ROW_SYMBOL_NOT_RUN` 已按名生效；CI 上的行首符号像素证人仍缺。

459 追记（R434 · 口径更正）：R433 写「540 高的 settings-privacy 在 1x 能画」是错的 —— 真正的限制是**设置页内容列整列平涂**（R433 跑 `CAPTION_JUDGED 6/17`，所有 settings 探针 machineFlat），与帧高无关；因此排除名单判据在 1x 只能具名 `EXCLUDED_APP_ROW_NOT_RUN=runner-1x-settings-content-plain`。

**460. HTML 标题映射按字号排名：文档若有超过六级标题字号，后排会全落 12pt**（R434 观察）
    现象：`fitHeadingsToLadder` 把基准之上的字号从大到小排成梯队、逐级取 `MarkdownPresentation.headingFontSize`；超过六级的部分被 `min(index, ladder.count - 1)` 压到最小一级（12pt），而它们原本可能只是 15–16pt 的强调文本，压到 12pt 反而比正文小。
    修法（下一轮若需要）：给超过梯子长度的字号保留下限（例如不映射、或映射到 13pt 而不是 12pt），并用一份含 7 种字号的合成 HTML 钉住；改之前先确认 `NSAttributedString(html:)` 真能产出那么多种字号（也需要一条现读）。
"""

STATE_SECTION = u"""## R434 状态（2026-10-27 · 本地 · 第 433 轮 / Round 431）：HTML 渲染的标题档接到 Markdown 梯子（同一 h1：旧墨带 27.0pt → 新 20.0pt、与 Markdown 差 9.0→2.0；2 张 HTML 帧变化、基线 238）；R433 跑失败步骤 2 个（设置内容列在 1x 整列平涂 ⇒ 排除名单判据无对象）⇒ 具名 NOT-RUN、阈值未动（产品 1 文件，HTML 标题排版位）

最后更新：2026-10-27（本地 · R434 / 第 433 轮 / Round 431）：同一个「渲染」档里，HTML 的 h1 旧读墨带 **27.0pt**、Markdown 的 h1 **18.0pt** —— R335 只把正文档按字符数加权搬到 14pt，标题被等比放大到 28pt。新 `HtmlRendering.fitHeadingsToLadder`：正文基准之上（>1.1×）的字号按从大到小逐级落到 `MarkdownPresentation.headingFontSize`（20/17/15.5…），字族与字重不动。旧/新：`HTML_HEADING_LADDER light html=20.0pt markdown=18.0pt 差=2.0pt`（旧 27.0/18.0、差 9.0）；`HTML_TYPE 基准前=12.0 基准后=14.0 标题后=20.0 梯子=20.0,17.0,15.5,14.0,13.0,12.0`。旧测试把「层级比 2.0」钉成契约，本轮更正为「标题在 Markdown 梯子上」。2 张 `detail-html-rendered` 帧变化，基线 **238/0/0/0**。R433 run `40526497330 ↔ e896829` **failure，失败步骤 2 个**（Swift tests / Capture gate）：唯一红是设置页**内容列在 1x 整列平涂**（`CAPTION_JUDGED 6/17`，所有 settings 探针 machineFlat）⇒ 排除名单判据在 CI 上没有对象，具名 `EXCLUDED_APP_ROW_NOT_RUN=runner-1x-settings-content-plain`、2x 断言不动；`DETAIL_IMAGE_EDGE` 在 1x 绿（light 图框 240..479×220..359、页底 236、边带差 30.0；dark 50/26.0）；理由带 290 后 typed 217/248、list 0；时间列 1x light `[74,71,74,74,74]`、dark `[74,72,74,74,74]`；脚注 NOT-RUN 按名出现；分区 13/12 与 11/10、表格 6/5；回执 2/2；滚动 4/4（`CHANNEL 0→108→600 38400/30362`、`TIME 5/0/0/1430`）；拖拽 mass 0.549/0.550；floor 4/5/77（notice-banner）无红。`M1192–M1193` **2/2 CAUGHT**；预检 **212/194/560 bad=0**、ARM **305 文件 / 1043 把**、HIDDEN **299/977 rot=0**。本地全量 **1176/57/5**：5 断言全在 `SelectionRevealAnimationTests`（3 条用例），单跑（caffeinate-u 后）**4/4 passed**（`TIME 18/8/61/1438`、`CHANNEL 0→86.5→600 变化 76639/127200 重抓=no`、`OFFSET 0/227.5/1438`）⇒ 具名 `LOCAL_SCROLL_SESSION_NOT_RUN=full-suite-order`（449）。捕获 **141/4/0 / 238 帧**；基线 **238/0/0/0**；换装 `ok / SHA_MATCH=1 / 381=381 / SMOKE_OK=1`；清账 `格=162 声明=63 不成立=0/63`；产品面连续零改动 **1** 轮（as-of 433，现读 `python3 scripts/product_streak.py --streak-for 433`）。电池 `Ran 683 / OK (skipped=4)`（台账后复跑）。

本轮做了什么：
① ⓪ R433 跑 failure、失败步骤 2 个：唯一红是设置内容列 1x 平涂（`CAPTION_JUDGED 6/17`）⇒ 排除名单判据具名 NOT-RUN、阈值未动；图片边判据 1x 绿（30.0/26.0）；理由带/时间列/脚注/分区/表格/回执/滚动/拖拽全绿。
② 产品：HTML 标题档接到 Markdown 梯子（旧 27.0 → 新 20.0，差 9.0→2.0）。
③ 判据：M1192–M1193 2/2；三条映射单测；旧比例契约更正；precheck 212/194/560；hidden rot 0。
④ 436：R433 跑 floor judged=4/5 executed=77（notice-banner）、无红、无 unlisted；本轮不重猜 must_judge。
⑤ 367：hidden 表 299 / 可判 977 / rot 0。
⑥ 捕获 141/4/0、238 帧；换装 ok；清账 162/63/0；帧基线 238/0/0/0；本地全量 1176/57/5（5 条滚动红具名会话/顺序 NOT-RUN，CI 4/4 绿）。

NOT-RUN / 阻塞（分开写）：① 设置内容列 1x 整列平涂（`EXCLUDED_APP_ROW_NOT_RUN=runner-1x-settings-content-plain`，459）；② 设置脚注带 1x；③ 主窗口 content 帧 1x（458）；④ 高夹具 1x（459）；⑤ 13+ 菜单像素/标题（454）；⑥ 真实拖拽（453）；⑦ Dock 像素；⑧ 源图标最小窗文字 1x；⑨ 本地全量 5 条滚动红（449）；⑩ 2x/extended；⑪ 固定块揭示偏移（455）；⑫ 跨年时间（456）；⑬ 主列表暗档文字盲区（457）；⑭ 真机/多屏（447）；⑮ 真菜单栏、12 实时腿；⑯ `table-lazy-rows`；⑰ HTML 六档以上字号（460）；⑱ 437–460 仍开；⑲ R434 新跑待 push 后读。

下一轮（R435）的靶：⓪ 先 `git push origin main`（禁 amend/force）并复核 ahead=0；读 R434 主笔+追记 head 跑全部失败步骤（成对 run↔commit），in_progress/0 字节不算绿；重点看 `HTML_HEADING_LADDER` 在 1x 的读数（旧契约已改，若 runner 上 HTML 帧不画则具名）、`EXCLUDED_APP_ROW_NOT_RUN` 按名出现、`DETAIL_IMAGE_EDGE`、理由带、时间列、脚注、分区、菜单、Dock/搜索/滚动是否仍绿；① 367 现读 rot=0，按 `HIDDEN_ROT` 查新腐烂；② 继续产品视觉位并落 Sources、换缺陷类别；③ 436 只复核新跑 Motion floor，不重猜 `must_judge`。

"""

R434_REPORT_BULLET = u"""- **R434（HTML 标题排版位）**：同一个「渲染」档里，HTML 的 h1 旧读墨带 **27.0pt**、Markdown 的 h1 **18.0pt** —— R335 只把正文档按字符数加权搬到 14pt，标题被等比放大到 28pt。新 `HtmlRendering.fitHeadingsToLadder`：正文基准之上（>1.1×）的字号按从大到小逐级落到 `MarkdownPresentation.headingFontSize`（20/17/15.5…），字族与字重不动。旧/新：`HTML_HEADING_LADDER light html=20.0pt markdown=18.0pt 差=2.0pt`（旧 27.0/18.0、差 9.0；余下 2pt 是 Times 与系统字同号下的墨带差）；`HTML_TYPE 基准前=12.0 基准后=14.0 标题后=20.0`。旧测试把「层级比 2.0」钉成契约，本轮更正为「标题在 Markdown 梯子上」。2 张 `detail-html-rendered` 帧变化，基线 **238/0/0/0**。R433 run `40526497330 ↔ e896829` **failure、失败步骤 2 个**（Swift tests / Capture gate）：唯一红是设置页**内容列在 1x 整列平涂**（`CAPTION_JUDGED 6/17`，所有 settings 探针 machineFlat）⇒ 排除名单判据具名 `EXCLUDED_APP_ROW_NOT_RUN=runner-1x-settings-content-plain`、2x 断言不动；`DETAIL_IMAGE_EDGE` 在 1x 绿（light 30.0 / dark 26.0）；理由带 217/248 vs 0；时间列、脚注、分区、表格、回执 2/2、滚动 4/4、拖拽 mass 全绿；floor 4/5/77（notice-banner）。M1192–M1193 **2/2**；预检 212/194/560 bad=0；HIDDEN 299/977 rot=0。本地全量 **1176/57/5**：5 断言全在 SelectionRevealAnimationTests，单跑 4/4（TIME 18/8、61→1438；CHANNEL 0→86.5→600、76639/127200）⇒ 具名 `LOCAL_SCROLL_SESSION_NOT_RUN=full-suite-order`（449）。捕获 141/4/0、238 帧；换装 ok/SHA_MATCH=1/381=381/SMOKE_OK=1；清账 162/63/0；电池 683/4。
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
if u"第 433 轮（R434" in audit:
    raise SystemExit("REFUSED AUDIT 已有 R434 节")
if u"## Round 431 · R434" in iter_text:
    raise SystemExit("REFUSED ITERATION 已有 Round 431")
if u"## D-430" in decisions:
    raise SystemExit("REFUSED DECISIONS 已有 D-430")
if u"HTML 渲染的标题档接到 Markdown 梯子" in changelog:
    raise SystemExit("REFUSED CHANGELOG 已有该标题")
if u"**460." in backlog:
    raise SystemExit("REFUSED BACKLOG 已有 460")
if state.count(u"## R433 状态") != 1:
    raise SystemExit("REFUSED STATE 锚点命中 %d 次" % state.count(u"## R433 状态"))
U_CELL_OLD = u"U-31 … U-1592（R433 现读抬到最新一节）"
if report.count(U_CELL_OLD) != 1:
    raise SystemExit("REFUSED REPORT U 格命中 %d 次" % report.count(U_CELL_OLD))
if report.count(u"AGENT_STATE.md` 的 R433 节 ②") != 1:
    raise SystemExit("REFUSED REPORT §13 指针命中 %d 次" % report.count(u"AGENT_STATE.md` 的 R433 节 ②"))

new_audit = audit.replace(AUDIT_TITLE, AUDIT_SECTION + AUDIT_TITLE, 1)
new_iter = iter_text.rstrip() + "\n\n" + ITER_SECTION + "\n"
new_decisions = decisions.rstrip() + "\n\n" + DECISION_430 + "\n"
marker = u"## [Unreleased]\n"
if changelog.count(marker) != 1:
    raise SystemExit("REFUSED CHANGELOG [Unreleased] 命中 %d 次" % changelog.count(marker))
new_changelog = changelog.replace(marker, marker + "\n" + CHANGELOG_SECTION, 1)
new_backlog = backlog.rstrip() + "\n\n" + BACKLOG_SECTION + "\n"
new_state = state.replace(u"## R433 状态", STATE_SECTION + u"## R433 状态", 1)
new_report = report.replace(U_CELL_OLD, u"U-31 … U-1597（R434 现读抬到最新一节）", 1)
new_report = new_report.replace(u"AGENT_STATE.md` 的 R433 节 ②",
                                u"AGENT_STATE.md` 的 R434 节 ②", 1)
new_report = new_report.rstrip() + "\n\n" + R434_REPORT_BULLET + "\n"

wr(AUDIT, new_audit)
wr(ITER, new_iter)
wr(DECISIONS, new_decisions)
wr(CHANGELOG, new_changelog)
wr(BACKLOG, new_backlog)
wr(STATE, new_state)
wr(REPORT, new_report)
print("LEDGERS_R434_OK audit=%d iter=%d decisions=%d changelog=%d backlog=%d state=%d report=%d"
      % (len(new_audit), len(new_iter), len(new_decisions), len(new_changelog),
         len(new_backlog), len(new_state), len(new_report)))
