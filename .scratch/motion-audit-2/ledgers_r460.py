#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R460 七本台账一次落盘（只跑一次；先断言所有锚点，全部通过才写）。"""
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


AUDIT_TITLE = u"## 第 458 轮（R459 · 2026-10-28"
AUDIT_SECTION = u"""## 第 459 轮（R460 · 2026-10-28 · U-1723…U-1727）：纯文本文件预览接上 68ch 可读列（旧正文宽 1100pt、可读列 652pt → 新 652/652；2 张新帧、基线 270→272）（产品 1 文件，纯文本文件预览列宽位）

- **U-1723：⓪ push 与两跑读数。** 开工 no-op push success、ahead=0、HEAD=`4edfa23`；新跑 `40681994982 ↔ f954b0e` 与 `40682072865 ↔ 4edfa23` 读时 in_progress ⇒ **NOT-RUN**。**收口读：两跑均 completed=failure，失败步骤各 2 个**（`Swift tests (executed-count gate)`、`Capture gate (unregistered reds must be zero)`）；`f954b0e` 跑的关键读数：`HEADING_LADDER 20/17/15.5/15/14.5/14（正文 14）` **runner 签收**、`WIDE_TABLE false/752.0/[1,1,1]/true + 短表 true/[1,1]/false` **runner 签收**、`CODE_TAB_STOP 32.14/32.14、64.29/64.29、间隔 32.14、制表位 0` 两档签收、`HISTORY_ROW_MATCH light 0/300、528/0、0/0` 签收、dark NOT-RUN；但 `INLINE_CODE_PAD light 84.0/80.0/4.0、dark 150.0/147.0/3.0` —— **带已经找得到（透明页修复生效），1x 下隙低于 4.5，dark 还触到 150pt 上限** ⇒ `testInlineCodeBackgroundHasPadding` 仍红；另 `SelectionRevealAnimationTests.testProductDurationRevealStillMovesOverTime` 红（滚动会话采样 flake）。`40675730252 ↔ dd11f0f` failure 2 步（同一行内码旧尺；`CODE_TAB_STOP` 已签收）；`40664012233`/`40664181811` failures；`40653092761` success；`40645430259` success；`40645469967` 仅 receipt 1<2；`40634880705` 滚动采样红。436：`f954b0e` 跑 Motion `judged` 见日志（无新红），采样红仍具名。
- **U-1724：① 腐烂与预检。** `HIDDEN_ARMS 表=325 可判=1033 rot=0`；`NEEDLE_PRECHECK tables=238 covered=220 arms=616 bad=0`、`ARM_TOTAL files=331 arms=1099`。
- **U-1725：② 纯文本文件预览列宽。** 缺陷形状：U-4 的 68ch 可读列只接在 Markdown/正文分支，`DetailFileView.textPreview` 的纯文本 else 分支直接建 `ChineseSelectableTextView`，在 1100 窗口里正文宽 **1100pt**（可读列 652pt），长行一路铺满详情区。修法：纯文本文件也用**它自己的 13pt 字体**算 68ch 列（`DetailTypography.columnWidth(font:)`），加列宽与左对齐；字体字面量保留（`Round4MarkdownTests` 的静态守卫）。旧/新：`FILE_TEXT_PREVIEW light 正文宽=1100.0pt 可读列=652.0pt → 652.0/652.0`、dark 同形。新增真实 `.txt` 夹具 `detail-file-text-wide`（1100×800，settle 1.2s 等异步载入），**2 张新帧**、0 旧帧变化/缺失；基线 **270→272**；已看亮/暗：长行在可读列内折行、右侧留白。Store 未动（1108/52/66）。
- **U-1726：判据与刀。** 新帧判据 `testPlainTextFilePreviewUsesTheReadableColumn` 从产品渲染出的 NSTextView 读正文 frame 宽，要求 ≤ 13pt 的 68ch 列；旧形态红（1100>653），新形态绿；`M1258`（撤列）/`M1259`（硬编码 900pt）⇒ **2/2 CAUGHT**、RESTORE_CLEAN=yes。**守卫红一次**：全量首跑 `testFilePreviewRoutesMarkdownFilesToTheRenderer` 要求 13pt 等宽字面量仍在调用点 ⇒ 保留字面量、列宽另取 `fileFont`，复绿；M1258 随之重钉并复跑 2/2。
- **U-1727：八步与具名 NOT-RUN。** build **0 告警**（冷编同）；捕获卷 **272 帧**、`CHANGED=0 ADDED=2 MISSING=0`，更新后 `272/0/0/0`；全量 **1264/56/0**（439s，轻载）；换装 `INSTALL_RESULT=ok / SHA_MATCH=1 / 386=386`（条目从 383 增到 386，前后一致，无丢失）；`STORE-SIZE lines=1108 funcs=52 longest=66`；产品面连续零改动 **1** 轮（as-of 459，`python3 scripts/product_streak.py --streak-for 459`，last=ff77c27）；清账与电池在台账后复跑。**具名 NOT-RUN**：① `40681994982 ↔ f954b0e` 与 `40682072865 ↔ 4edfa23`（completed=failure，见 U-1723）；② R460 自身跑（未创建）；③ `INLINE_CODE_PAD` 的 1x 隙（light 4.0、dark 触顶 150，floor 4.5 未动，499）；④ `RUNNER_SCROLL_SESSION_FLAKE`（SelectionReveal 中间 origin）；⑤ 文件预览的异步载入（settle 1.2s，runner 若读不到则具名 `FILE_TEXT_PREVIEW_NOT_RUN=load-timeout`）；⑥ 源文/纯文本预览的宽行（496）；⑦ 2x 宽文档滚动条（497）；⑧ 散文按宽文档折行（498）；⑨ 纯文本预览制表符（490）；⑩ 表格单元格制表符（491）；⑪ 8 空格制表位（492）；⑫ 命中高亮截断外/OCR（487）；⑬ 多文件第 2/3 个文件名（488）；⑭ 选中底高亮对比（489）；⑮ 弱化色选中态（485）；⑯ 行内码两侧标点（486）；⑰ HTML 的 `<del>`（484）；⑱ HTML 列表缩进/任务弱化/表格体行（482/481/479）；⑲ 设置内容列 1x 平涂；⑳ 设置脚注带 1x；㉑ 主窗口 content 帧 1x；㉒ 高夹具 1x；㉓ 13+ 菜单像素/标题；㉔ 真实拖拽；㉕ Dock 像素；㉖ 源图标最小窗文字 1x；㉗ 2x/extended；㉘ 固定块揭示偏移（455）；㉙ 跨年时间（456）；㉚ 主列表暗档文字盲区（457）；㉛ 真机/多屏（447）；㉜ 真菜单栏、12 实时腿；㉝ `table-lazy-rows`；㉞ HTML 六档字号（460）；㉟ 清除 × 命中区（461）；㊱ 分隔线令牌（462）；㊲ 展开态已加载内容无帧（463）；㊳ 其它自绘控件帮助文本（464）；㊴ HTML 引用块无导引线（465）；㊵ HTML 表格表头无同档（466）；㊶ 100+ 行行号（467）；㊷ HTML 代码块行号（468）；㊸ 行号选中/滚动两态（469）；㊹ 关于页 1x 盲（470）；㊺ M613 机器前提（472）；㊻ 真机 vibrant 暗档（473）；㊼ 长来源截断（474）；㊽ bundle ID 未搜（475）；㊾ 长首行标签省略无帧（476）；㊿ HTML 代码块无语言标签（477）；[51] HTML `<hr>` 无通栏线（478）；[52] HTML 表格体行无同一条线（479）；[53] QuickPick 键盘提示 1x（480）；[54] HTML 任务列表无弱化（481）；[55] HTML 列表缩进（482）；[56] 中心刻度端点标签（483）；[57] HTML 的 `<del>`（484）；[58] 弱化色选中态（485）；[59] 行内码两侧标点（486）；[60] 437–501 的未结项仍开。

"""

ITER_SECTION = u"""## Round 457 · R460（第 459 轮 · 2026-10-28）：纯文本文件预览接上 68ch 可读列（旧 1100pt、可读列 652pt → 新 652/652；2 张新帧、基线 270→272）

U-4 的 68ch 可读列只接在 Markdown/正文分支，纯文本文件预览在 1100 窗口里正文宽 1100pt（可读列 652）。修法：纯文本文件也用它的 13pt 字体算 68ch 列并左对齐；13pt 字面量保留（静态守卫）。旧/新：`FILE_TEXT_PREVIEW light 1100.0/652.0 → 652.0/652.0`、dark 同形。新增真实 `.txt` 夹具 1100×800，2 张新帧、0 变化，基线 270→272/0/0/0；逐张看过长行在列内折、右侧留白。判据从渲染出的 NSTextView 读正文 frame 宽；旧红新绿；M1258/M1259 2/2；全量首跑因 13pt 字面量守卫红一次，保留字面量后 1264/56/0。⓪ no-op push、ahead=0；两跑 completed=failure：`HEADING_LADDER`/`WIDE_TABLE`/`CODE_TAB_STOP`/`HISTORY_ROW_MATCH` 均签收，`INLINE_CODE_PAD` 1x 读 84/80/4.0 与 150/147/3.0（floor 4.5 未动）仍红 + 滚动会话 flake。换装 ok/386=386；电池 683/5。

**七维度自评**（恰七行，每格 n/15）：

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | 15/15 | 亮/暗 `detail-file-text-wide` 逐张看过：长行在 652pt 列内折行、右侧留白。 |
| 判据有效性 | 15/15 | 从渲染出的 NSTextView 读正文 frame 宽；旧 1100>653 红、新 652 绿。 |
| 假绿防御 | 14/15 | 旧形态先红；两把刀全 CAUGHT；扣 1：`INLINE_CODE_PAD` 1x 隙仍红（499）。 |
| 产品面推进 | 15/15 | 纯文本文件第一次有可读列；字体与静态守卫保持；Store 不动。 |
| 台账一致性 | 15/15 | U-1723…U-1727、D-456、272 帧/1264、386=386 都来自命令与测试。 |
| 交付诚实性 | 15/15 | 两跑 completed=failure、行内码 1x 读数、滚动 flake、守卫红都照记。 |
| 可复核性 | 15/15 | 1100→652、652/652、84/80/4.0、150/147/3.0、刀号与 precheck 238/220/616、rot 325/1033、基线 272 都在。 |

均分 = 104/105 ≈ 14.9/15（99）。"""

DECISION_456 = u"""## D-456 纯文本文件预览也受 68ch 可读列约束（R460）

- 背景：U-4 的可读列只接在 Markdown/正文分支；纯文本文件（.txt/.log）在 1100 窗口里正文宽 1100pt，长行铺满详情区。
- 决定：纯文本文件用**它自己的 13pt 字体**算 68ch 列（`DetailTypography.columnWidth(font:)`）并左对齐；13pt 等宽字体的字面量保留在调用点（静态守卫钉着"非 Markdown 文本走等宽档"）。
- 理由：文件正文和剪贴板正文是同一类阅读对象；列宽必须由字体推进推出来，不能与 Markdown 的 14pt 列混用。
- 兼容性/迁移：新增真实 `.txt` 夹具 `detail-file-text-wide` 亮/暗 2 张帧；旧帧 0 变化；基线 270→272 同 commit 更新。
- 边界：异步载入依赖 settle（runner 读不到时具名 NOT-RUN）；源文/纯文本宽行与宽表滚动仍分开记（496/497/498）。
- 回滚：删纯文本分支的列宽两行；或 `git revert`。
"""

CHANGELOG_SECTION = u"""### 纯文本文件预览接上 68ch 可读列（旧正文宽 1100pt、可读列 652pt → 新 652/652；2 张新帧、基线 270→272）（R460 / 第 459 轮 / Round 457 / U-1723…U-1727 · 产品 1 文件，纯文本文件预览列宽位）

"""

BACKLOG_SECTION = u"""**499. R455 行内码判据在 1x 上仍低于 4.5 地板**（R460 观察）
    现象：透明页修复后带已找得到，但 runner 读 `light 84.0/80.0/4.0`、`dark 150.0/147.0/3.0`（dark 触 150pt 上限，疑把相邻内容并进来）。地板 4.5 未动。
    修法：先查 1x 下带/字的边界（dark 的 150 是选择器上限，不是带）；必要时把带定位改成"页面底 + 两级众数 + 字墨列"的结构量，别降地板。

**500. 纯文本文件预览仍是 13pt，Markdown 正文是 14pt**（R460 观察）
    现象：列宽已分开算，但同一屏两种字号；原文/渲染切换时字号仍差 1pt。
    修法：若要对齐，把文件预览字号也提到 14（并重算列宽）；先补对照帧再定。

**501. 纯文本文件预览夹具依赖 1.2s settle**（R460 观察）
    现象：真实 `.txt` 通过 `DetailFileView` 异步载入；runner 若在 1.2s 内没载入，判据会走具名 NOT-RUN。
    修法：把载入完成做成夹具可观察的条件（例如轮询 text view 是否出现），不要靠墙钟；先记录。
"""

STATE_SECTION = u"""## R460 状态（2026-10-28 · 本地 · 第 459 轮 / Round 457）：纯文本文件预览接上 68ch 可读列（旧正文宽 1100pt、可读列 652pt → 新 652/652；2 张新帧、基线 270→272）；全量 1264/56/0；两跑 failure（行内码 1x 隙仍红）（产品 1 文件，纯文本文件预览列宽位）

最后更新：2026-10-28（本地 · R460 / 第 459 轮 / Round 457）：U-4 的 68ch 可读列只接在 Markdown/正文分支，`DetailFileView.textPreview` 的纯文本 else 分支直接建 `ChineseSelectableTextView`，在 1100 窗口里正文宽 **1100pt**（可读列 652pt），长行一路铺满详情区。修法：纯文本文件也用**它自己的 13pt 字体**算 68ch 列（`DetailTypography.columnWidth(font:)`）并左对齐；13pt 字面量保留（`Round4MarkdownTests` 的静态守卫）。旧/新：`FILE_TEXT_PREVIEW light 正文宽=1100.0pt 可读列=652.0pt → 652.0/652.0`、dark 同形。新增真实 `.txt` 夹具 `detail-file-text-wide`（1100×800，settle 1.2s 等异步载入），**2 张新帧**、0 旧帧变化/缺失；基线 **270→272**；已看亮/暗：长行在可读列内折行、右侧留白。判据 `testPlainTextFilePreviewUsesTheReadableColumn` 从产品渲染出的 NSTextView 读正文 frame 宽；旧红、新绿；`M1258/M1259` **2/2 CAUGHT**、RESTORE_CLEAN。**守卫红一次**：全量首跑 `testFilePreviewRoutesMarkdownFilesToTheRenderer` 要求 13pt 字面量仍在调用点 ⇒ 保留字面量、列宽另取 `fileFont`，复绿；M1258 重钉后复跑 2/2。预检 **238/220/616 bad=0**、ARM **331/1099**、HIDDEN **325/1033 rot=0**。⓪：no-op push success、ahead=0、HEAD=`4edfa23`；**`40681994982 ↔ f954b0e` 与 `40682072865 ↔ 4edfa23` 两跑 completed=failure，失败步骤各 2 个**（Swift tests、Capture gate）：`HEADING_LADDER`/`WIDE_TABLE`/`CODE_TAB_STOP`/`HISTORY_ROW_MATCH` 均 runner 签收；`INLINE_CODE_PAD light 84.0/80.0/4.0、dark 150.0/147.0/3.0`（1x 隙 <4.5、dark 触 150 上限，地板未动）+ `SelectionRevealAnimationTests` 滚动会话采样红。全量 **1264/56/0**（439s，轻载）；捕获卷 **272 帧**；基线 **272/0/0/0**；build **0 告警**；换装 `ok / SHA_MATCH=1 / 386=386`（条目 383→386，前后一致）；`STORE-SIZE lines=1108 funcs=52 longest=66`；产品面连续零改动 **1** 轮（as-of 459，`python3 scripts/product_streak.py --streak-for 459`，last=ff77c27）。清账与电池在台账后复跑。

本轮做了什么：
① ⓪ no-op push、ahead=0；两跑 failure 2 步，`INLINE_CODE_PAD` 1x 隙仍红、滚动 flake；其余面签收。
② 产品：纯文本文件预览接 68ch 可读列（1100→652；2 张新帧、基线 272）。
③ 判据：旧红新绿；M1258/M1259 2/2；全量首跑守卫红已修；precheck 238/220/616；hidden rot 0。
④ 436：无新跑红；采样红具名，不改门槛、不重猜 must_judge。
⑤ 367：hidden 表 325 / 可判 1033 / rot 0。
⑥ 捕获 272 帧；基线 272/0/0/0；build 0 告警；换装 ok/386=386；全量 1264/56/0（轻载）。

NOT-RUN / 阻塞（分开写）：① `40681994982 ↔ f954b0e` 与 `40682072865 ↔ 4edfa23`（completed=failure）；② R460 自身跑（未创建）；③ `INLINE_CODE_PAD` 的 1x 隙（light 4.0、dark 触顶 150，499）；④ `RUNNER_SCROLL_SESSION_FLAKE`；⑤ 文件预览异步载入；⑥ 源文/纯文本宽行（496）；⑦ 2x 宽文档滚动条（497）；⑧ 散文按宽文档折行（498）；⑨ 纯文本预览制表符（490）；⑩ 表格单元格制表符（491）；⑪ 8 空格制表位（492）；⑫ 命中高亮截断外/OCR（487）；⑬ 多文件第 2/3 个文件名（488）；⑭ 选中底高亮对比（489）；⑮ 弱化色选中态（485）；⑯ 行内码两侧标点（486）；⑰ HTML 的 `<del>`（484）；⑱ HTML 列表缩进/任务弱化/表格体行（482/481/479）；⑲ 设置内容列 1x 平涂；⑳ 设置脚注带 1x；㉑ 主窗口 content 帧 1x；㉒ 高夹具 1x；㉓ 13+ 菜单像素/标题；㉔ 真实拖拽；㉕ Dock 像素；㉖ 源图标最小窗文字 1x；㉗ 2x/extended；㉘ 固定块揭示偏移（455）；㉙ 跨年时间（456）；㉚ 主列表暗档文字盲区（457）；㉛ 真机/多屏（447）；㉜ 真菜单栏、12 实时腿；㉝ `table-lazy-rows`；㉞ HTML 六档字号（460）；㉟ 清除 × 命中区（461）；㊱ 分隔线令牌（462）；㊲ 展开态已加载内容无帧（463）；㊳ 其它自绘控件帮助文本（464）；㊴ HTML 引用块无导引线（465）；㊵ HTML 表格表头无同档（466）；㊶ 100+ 行行号（467）；㊷ HTML 代码块行号（468）；㊸ 行号选中/滚动两态（469）；㊹ 关于页 1x 盲（470）；㊺ M613 机器前提（472）；㊻ 真机 vibrant 暗档（473）；㊼ 长来源截断（474）；㊽ bundle ID 未搜（475）；㊾ 长首行标签省略无帧（476）；㊿ HTML 代码块无语言标签（477）；[51] HTML `<hr>` 无通栏线（478）；[52] HTML 表格体行无同一条线（479）；[53] QuickPick 键盘提示 1x（480）；[54] HTML 任务列表无弱化（481）；[55] HTML 列表缩进（482）；[56] 中心刻度端点标签（483）；[57] HTML 的 `<del>`（484）；[58] 弱化色选中态（485）；[59] 行内码两侧标点（486）；[60] 437–501 的未结项仍开。

下一轮（R461）的靶：⓪ 先 `git push origin main`（禁 amend/force）并复核 ahead=0；读 R460 主笔+追记 head 跑、`40681994982 ↔ f954b0e`、`40682072865 ↔ 4edfa23`、`40675730252 ↔ dd11f0f`、`40664012233 ↔ d2a1e80`、`40664181811 ↔ ca40810`、`40653092761 ↔ d48bb05`、`40645430259 ↔ 5c925a9`、`40645469967 ↔ c041c8d`、`40640660665 ↔ 86044bf`、`40642482086 ↔ e083179`、`40636558557 ↔ 667d1a2`、`40634880705 ↔ 9743379` 的全部失败步骤（成对 run↔commit）；重点先修 **`INLINE_CODE_PAD` 的 1x 隙**（light 84/80/4.0、dark 150/147/3.0；地板 4.5 不动）：dark 的 150 是选择器上限，先查 1x 带/字边界；再看 `FILE_TEXT_PREVIEW` 两档 652/652、`WIDE_TABLE`、`HEADING_LADDER`、`HISTORY_ROW_MATCH`、`CODE_TAB_STOP`、`DEEMPHASIS_CONTRAST`、`STRIKE_DIM`、`TASK_DIM`、`WEIGHT_CENTER_TICK`、`LIST_HANG_STYLE`、`QUICKPICK_HINT`、`TABLE_ROW_LINES`、`THEMATIC_RULE`、`CODE_LANGUAGE`、`HISTORY_SEARCH_SOURCE`、`PROBE_DOMAIN`、`TABLE_HEADER`、`CODE_LINE_NUMBERS` 与 436；in_progress/0 字节不算绿；`gh` 读不到就具名 `CI_READ_BLOCKED=network`（收口前再试一次）；`RUNNER_SCROLL_SESSION_FLAKE`/`LOCAL_PERF_BUDGET_FLAKE`/`RUNNER_MARKDOWN_LABEL_SAMPLE_RED` 原样重跑复核（不改门槛）；① 现读 rot=0，按 `HIDDEN_ROT` 查新腐烂；② 继续产品视觉位并落 Sources、换缺陷类别（不要再做纯文本文件列宽/宽表横向滚动/标题字阶/代码块制表位/列表命中高亮/行内代码底色/弱化色对比度/删除线/权重刻度/列表悬挂缩进/任务项完成态/浮层键盘提示/表格体行分隔/主题分隔线/代码块语言标签/代码块行号/表格表头/引用导引线/侧栏搜索来源/主列表来源行/设置侧栏文字/设置关于页/录制帮助/多文件展开/批量分隔/浮层搜索/图片/HTML/排除名单/行内符号/时间列/分区头/侧栏脚注/详情头部/Dock/菜单栏/横幅/回执/热图/计数/空态/无结果/焦点/悬停/选中/滚动/CTA）；③ 436 只复核新跑 Motion floor，不重猜 `must_judge`。
"""

R460_REPORT_BULLET = u"""- **R460（纯文本文件预览列宽位）**：U-4 的 68ch 可读列只接在 Markdown/正文分支，纯文本文件预览在 1100 窗口里正文宽 **1100pt**（可读列 652pt），长行铺满详情区。修法：纯文本文件用**它自己的 13pt 字体**算 68ch 列并左对齐；13pt 字面量保留（静态守卫）。旧/新：`FILE_TEXT_PREVIEW light 1100.0/652.0 → 652.0/652.0`、dark 同形；新增真实 `.txt` 夹具 `detail-file-text-wide`（1100×800），**2 张新帧**、0 旧帧变化，基线 **270→272/0/0/0**；逐张看过。判据 `testPlainTextFilePreviewUsesTheReadableColumn` 旧红新绿；`M1258/M1259` **2/2**；全量首跑因 13pt 字面量守卫红一次，保留字面量后 **1264/56/0**（439s）。⓪：no-op push、ahead=0；`40681994982 ↔ f954b0e` 与 `40682072865 ↔ 4edfa23` 两跑 **completed=failure，各 2 步**：`HEADING_LADDER`/`WIDE_TABLE`/`CODE_TAB_STOP`/`HISTORY_ROW_MATCH` 均已 runner 签收；`INLINE_CODE_PAD light 84.0/80.0/4.0、dark 150.0/147.0/3.0`（1x 隙 <4.5、dark 触 150 上限，地板未动）仍红 + 滚动会话 flake。捕获 272 帧；build 0 告警；换装 ok/SHA_MATCH=1/386=386（383→386 前后一致）；STORE-SIZE 1108/52/66；电池 683/5。
"""

audit = rd(AUDIT); iter_text = rd(ITER); decisions = rd(DECISIONS)
changelog = rd(CHANGELOG); backlog = rd(BACKLOG); state = rd(STATE); report = rd(REPORT)

if audit.count(AUDIT_TITLE) != 1: raise SystemExit("REFUSED AUDIT %d" % audit.count(AUDIT_TITLE))
if u"第 459 轮（R460" in audit: raise SystemExit("REFUSED AUDIT 已有 R460")
if u"## Round 457 · R460" in iter_text: raise SystemExit("REFUSED ITER 已有 Round 457")
if u"## D-456" in decisions: raise SystemExit("REFUSED DECISIONS 已有 D-456")
if u"纯文本文件预览接上 68ch 可读列" in changelog: raise SystemExit("REFUSED CHANGELOG 已有该标题")
if u"**499." in backlog: raise SystemExit("REFUSED BACKLOG 已有 499")
if state.count(u"## R459 状态") != 1: raise SystemExit("REFUSED STATE %d" % state.count(u"## R459 状态"))
U_CELL_OLD = u"U-31 … U-1722（R459 现读抬到最新一节）"
if report.count(U_CELL_OLD) != 1: raise SystemExit("REFUSED REPORT U %d" % report.count(U_CELL_OLD))
if report.count(u"AGENT_STATE.md` 的 R459 节 ②") != 1: raise SystemExit("REFUSED REPORT pointer")

new_audit = audit.replace(AUDIT_TITLE, AUDIT_SECTION + AUDIT_TITLE, 1)
new_iter = iter_text.rstrip() + "\n\n" + ITER_SECTION + "\n"
new_decisions = decisions.rstrip() + "\n\n" + DECISION_456 + "\n"
marker = u"## [Unreleased]\n"
if changelog.count(marker) != 1: raise SystemExit("REFUSED CHANGELOG")
new_changelog = changelog.replace(marker, marker + "\n" + CHANGELOG_SECTION, 1)
new_backlog = backlog.rstrip() + "\n\n" + BACKLOG_SECTION + "\n"
new_state = state.replace(u"## R459 状态", STATE_SECTION + u"## R459 状态", 1)
new_report = report.replace(U_CELL_OLD, u"U-31 … U-1727（R460 现读抬到最新一节）", 1)
new_report = new_report.replace(u"AGENT_STATE.md` 的 R459 节 ②", u"AGENT_STATE.md` 的 R460 节 ②", 1)
new_report = new_report.rstrip() + "\n\n" + R460_REPORT_BULLET + "\n"

wr(AUDIT, new_audit); wr(ITER, new_iter); wr(DECISIONS, new_decisions)
wr(CHANGELOG, new_changelog); wr(BACKLOG, new_backlog); wr(STATE, new_state); wr(REPORT, new_report)
print("LEDGERS_R460_OK audit=%d iter=%d decisions=%d changelog=%d backlog=%d state=%d report=%d"
      % (len(new_audit), len(new_iter), len(new_decisions), len(new_changelog),
         len(new_backlog), len(new_state), len(new_report)))
