#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R455 七本台账一次落盘（只跑一次；先断言所有锚点，全部通过才写）。"""
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


AUDIT_TITLE = u"## 第 453 轮（R454 · 2026-10-28"
AUDIT_SECTION = u"""## 第 454 轮（R455 · 2026-10-28 · U-1698…U-1702）：行内代码底色带补空白侧内边距（旧带 94.5pt/字 92.0pt、左右各 ~1pt → 新带 98.5pt/字 92.5pt、隙 6.0pt；2 张旧帧变化、基线名单 262）（产品 2 文件，行内代码底色位）

- **U-1698：⓪ push 与跑。** 开工 remote=`c041c8d`、ahead=3，一次快进 push **`c041c8d..d48bb05` success**（三笔：ee930b6/b478b2a/d48bb05），HEAD=origin/main=`d48bb05`、**ahead=0**。已读：**`40645430259 ↔ 5c925a9` success**（R453 head）：`TASK_DIM light 157.9/114.7 +43.2、dark 128.4/166.4 −38.1`、`STRIKE_DIM light 135.4/108.0 +27.4、dark 141.8/174.6 −32.7、隙 3/3`（旧弱化色在 runner 1x 签收）；**`40645469967 ↔ c041c8d` failure，失败步骤只有 Motion coverage floor**：`testCopyReceiptAppearsAndDismissesWithAVisibleProcess` 1 帧<2（采样红、未登记），Swift 测试全绿；`40640660665`（LIST_HANG_STYLE 已签收）/`40642482086`（WEIGHT_CENTER_TICK 具名 NOT_RUN）/`40642524490`/`40636558557`（TASK_DIM 1x）均 success；`40634880705 ↔ 9743379` failure（滚动会话采样红 + Motion 模式标签 1<2）；`0737460`/`ecb8e69` 仅 Motion；`36284e1` dark 行带（已修）。R454 head `40653092761 ↔ d48bb05` 读时 in_progress ⇒ NOT-RUN（R456 必读 DEEMPHASIS_CONTRAST）。436 只复核 Motion floor：`judged=4/5 executed=77 not-run=notice-banner`、红 0；采样红原样重跑，不改门槛、不重猜 `must_judge`。
- **U-1699：① 腐烂与预检。** `HIDDEN_ARMS 表=318 可判=1017 rot=0`；`NEEDLE_PRECHECK tables=233 covered=215 arms=604 bad=0`、`ARM_TOTAL files=326 arms=1087`。本轮改的是内联码底色的绘制，没弄断旧针。
- **U-1700：② 行内代码底色带的空白侧内边距。** 缺陷形状：内联码底色由属性串 `.backgroundColor` 涂，只到字形 advance —— 实测底色带 94.5pt、字宽 92.0pt，左右各 ~1pt，行内码和相邻正文挤在一起。修法：去掉 `.backgroundColor`，新 `InlineCodeBackground` 策略在背景层画圆角带（上下各 1pt）；横向只向**空白侧**各让 3pt（前一个是空格/行首、后一个是空格/行尾）—— 紧贴标点时不让，否则底色会盖到后随的“。”上。旧/新：`INLINE_CODE_PAD light 带宽=98.5pt 字宽=92.5pt 隙=6.0pt`、`dark 同形`（旧 94.5/92.0/2.5）。**2 张旧帧变化**（`detail-markdown-rendered` 亮/暗）、0 新增/缺失；基线名单仍 **262**（同 commit 更新）；已看亮/暗：带左缘离开“行内”的末字、右缘停在“。”前，不压字。Store 未动（1108 行/52 方法/最长 66）。
- **U-1701：判据、刀与一次旧期望修正。** 新单测 `InlineCodeBackgroundTests` 4 条（属性契约：有 `inlineCodeAttribute`、不再背 `.backgroundColor`；空白侧/标点侧 padding；rect 几何；文字不变）+ 帧判据 `testInlineCodeBackgroundHasPadding`（找 40..150pt 的**连续**带色行 — 文字抗锯齿是碎片进不来 — 量带内字宽，隙 ≥4.5pt）。`M1246`（不画带）⇒ 帧判据 CAUGHT；`M1247`（横向 padding 3→0）⇒ CAUGHT ⇒ **2/2**、RESTORE_CLEAN=yes。**旧期望修正**：全量跑红在 `Round4MarkdownTests.testMarkdownFileGoesThroughTheRealPreviewPipelineIntoAStyledTextView`（它钉着 `.backgroundColor`）；契约是"行内码有可区分底色"，R455 换成 `inlineCodeAttribute` + 自绘带，于是把断言改到新属性并写明像素证人在 `testInlineCodeBackgroundHasPadding`，过滤重跑通过（不是放宽，是机制换代）。
- **U-1702：八步与具名 NOT-RUN。** build **0 告警**；捕获卷 **262 帧**、`COMPARED=262 CHANGED=0 MISSING=0 ADDED=0`；全量 **1252/56/1**：唯一红＝上述 `Round4MarkdownTests` 旧期望（已改并通过过滤复跑；第二次全量在负载下挂起被停 ⇒ 具名 **`FULL_SUITE_REREAD_NOT_RUN=load-hang`**）；`PerfBudgetTests.testImageComparisonCostStaysBounded` 在混合/高负载跑里仍偶发 `310ms>250`（单跑 178ms 过）⇒ 再次具名 **`LOCAL_PERF_BUDGET_FLAKE=load`**，不改阈值；滚动套件单跑 **4/4**（本跑未复现 5 红；`LOCAL_SCROLL_SESSION_NOT_RUN` 口径保留）；换装 `INSTALL_RESULT=ok / SHA_MATCH=1 / 383=383`（条目 383）；`STORE-SIZE lines=1108 funcs=52 longest=66`；产品面连续零改动 **1** 轮（as-of 454，`python3 scripts/product_streak.py --streak-for 454`，last=ee930b6）；清账与电池在台账后复跑。**具名 NOT-RUN**：① `40653092761 ↔ d48bb05`（R454 head，in_progress）；② R455 自身跑（提交后创建）；③ `FULL_SUITE_REREAD_NOT_RUN=load-hang`；④ `LOCAL_PERF_BUDGET_FLAKE=load`；⑤ `RUNNER_SCROLL_SESSION_FLAKE`（9743379；R456 重跑）；⑥ 436 的 receipt 采样红（`40645469967` 唯一红，1<2）；⑦ 行内代码带在两侧都是标点时横向 padding=0（486）；⑧ 弱化色在选中/高亮底色上的对比度（485）；⑨ HTML 的 `<del>` 无弱化（484）；⑩ HTML 列表缩进/任务弱化/表格体行（482/481/479）；⑪ 设置内容列 1x 平涂；⑫ 设置脚注带 1x；⑬ 主窗口 content 帧 1x；⑭ 高夹具 1x；⑮ 13+ 菜单像素/标题；⑯ 真实拖拽；⑰ Dock 像素；⑱ 源图标最小窗文字 1x；⑲ 本地全量 5 条滚动红（本跑未复现、隔离 4/4）；⑳ 2x/extended；㉑ 固定块揭示偏移（455）；㉒ 跨年时间（456）；㉓ 主列表暗档文字盲区（457）；㉔ 真机/多屏（447）；㉕ 真菜单栏、12 实时腿；㉖ `table-lazy-rows`；㉗ HTML 六档字号（460）；㉘ 清除 × 命中区（461）；㉙ 分隔线令牌（462）；㉚ 展开态已加载内容无帧（463）；㉛ 其它自绘控件帮助文本（464）；㉜ HTML 引用块无导引线（465）；㉝ HTML 表格表头无同档（466）；㉞ 100+ 行行号（467）；㉟ HTML 代码块行号（468）；㊱ 行号选中/滚动两态（469）；㊲ 关于页 1x 盲（470）；㊳ M613 机器前提（472）；㊴ 真机 vibrant 暗档（473）；㊵ 长来源截断（474）；㊶ bundle ID 未搜（475）；㊷ 长首行标签省略无帧（476）；㊸ HTML 代码块无语言标签（477）；㊹ HTML `<hr>` 无通栏线（478）；㊺ HTML 表格体行无同一条线（479）；㊻ QuickPick 键盘提示 1x（480）；㊼ HTML 任务列表无弱化（481）；㊽ HTML 列表缩进（482）；㊾ 中心刻度端点标签（483）；㊿ HTML 的 `<del>`（484）；[51] 弱化色选中态对比（485）；[52] 437–486 的未结项仍开。

"""

ITER_SECTION = u"""## Round 452 · R455（第 454 轮 · 2026-10-28）：行内代码底色带补空白侧内边距（旧带 94.5pt/字 92.0pt、隙 2.5 → 新带 98.5pt/字 92.5pt、隙 6.0；2 张旧帧变化、基线 262）

内联码底色原由 `.backgroundColor` 涂，只到字形 advance。去掉属性底色，新 `InlineCodeBackground` 在背景层画圆角带（上下 1pt），横向只向空白侧各 3pt（紧贴标点不让，避免盖住后随的“。”）。读数 `INLINE_CODE_PAD light 98.5/92.5/隙 6.0`、dark 同形。2 张旧帧变化、0 新增，基线 262/0/0/0；已看亮/暗带缘。M1246/M1247 2/2；旧期望 `Round4MarkdownTests` 从 `.backgroundColor` 改到 `inlineCodeAttribute`（机制换代，过滤复跑通过）。全量 1252/56/1（旧期望红，已修；二次全量负载下挂起 ⇒ FULL_SUITE_REREAD_NOT_RUN；perf flake 具名）；滚动单跑 4/4。⓪：push c041c8d..d48bb05 success、ahead=0；R453 head 5c925a9 success（STRIKE_DIM/TASK_DIM 签收）；c041c8d 唯一红＝Motion receipt 采样；R454 head in_progress。换装 ok/383=383；电池 683/5。

**七维度自评**（恰七行，每格 n/15）：

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | 15/15 | 亮/暗 detail-markdown-rendered 逐张看过：带左缘离开“行内”、右缘停在“。”前，不压字。 |
| 判据有效性 | 15/15 | 连续带色行找带、带内字宽算隙（≥4.5；旧 2.5）；M1246/M1247 2/2。 |
| 假绿防御 | 15/15 | 连续段排除抗锯齿碎片、带缺失从 NOT-RUN 改红、标点侧不 padding；旧期望修正写明机制换代并有像素证人。 |
| 产品面推进 | 14/15 | 行内码第一次有可读内边距；Store 不动；扣 1：两侧都是标点时无横向 padding（486）。 |
| 台账一致性 | 15/15 | U-1698…U-1702、D-451、push d48bb05、262 帧/1252、STORE-SIZE 1108/66 都从命令与测试解析。 |
| 交付诚实性 | 15/15 | 全量 1252/56/1 的旧期望红与二次挂起、perf/滚动 flake 全部照记；R454 head in_progress 具名。 |
| 可复核性 | 15/15 | 98.5/92.5/6.0、旧 94.5/92.0/2.5、刀号与 precheck 233/215/604、rot 318/1017、基线 262 都在。 |

均分 = 104/105 ≈ 14.9/15（99）。"""

DECISION_451 = u"""## D-451 行内代码底色带只向空白侧加 padding（R455）

- 背景：内联码底色由 `.backgroundColor` 涂，只到字形 advance（带 94.5pt、字 92.0pt、隙 2.5），行内码与正文挤在一起。
- 决定：去掉属性底色，`InlineCodeBackground` 在背景层画圆角带（上下 1pt）；横向只在空白侧加 3pt（前一个是空格/行首、后一个是空格/行尾），紧贴标点时不加。
- 理由：给行内码留出可读内边距，同时不把底色盖到后随标点上；纯策略可单测，Store 不动（1108/66）。
- 兼容性/迁移：`detail-markdown-rendered` 亮/暗 2 张旧帧变化；基线 262 同 commit 更新；`Round4MarkdownTests` 的 `.backgroundColor` 断言改到 `inlineCodeAttribute`（机制换代，意图不变）。
- 边界：两侧都是标点时横向 padding=0（486）；选中态无帧。
- 回滚：恢复 `.backgroundColor` 并删绘制；或 `git revert`。
"""

CHANGELOG_SECTION = u"""### 行内代码底色带补空白侧内边距（旧带 94.5pt/字 92.0pt、隙 2.5 → 新带 98.5pt/字 92.5pt、隙 6.0；2 张旧帧变化、基线 262）（R455 / 第 454 轮 / Round 452 / U-1698…U-1702 · 产品 2 文件，行内代码底色位）

"""

BACKLOG_SECTION = u"""449 追记（R455 · 仍开）：本机全量 1252/56/1（旧期望红已修；二次全量负载下挂起）；隔离滚动 4/4；未动阈值。

451 追记（R455 · 仍开）：macOS 12 的详情头部阈值本轮未动。

452 追记（R455 · 仍开）：脚注 1x 具名 NOT-RUN 仍生效。

453 追记（R455 · 仍开）：真实系统拖拽会话仍无自动化验收。

454 追记（R455 · 仍开）：菜单具名标记仍未发射。

455 追记（R455 · 仍开）：固定条目滚动到位的独立偏移验收仍缺。

456 追记（R455 · 仍开）：跨年记录仍无年份。

457 追记（R455 · 仍开）：主列表暗档文字仍是另一处。

458 追记（R455 · 仍开）：CI 行首符号像素证人仍缺。

459 追记（R455 · 仍开）：设置内容列/高夹具在 1x 整列平涂。

460 追记（R455 · 仍开）：HTML 六档以上字号仍会后排压到 12pt。

461 追记（R455 · 仍开）：浮层清除 × 命中区 18pt。

462 追记（R455 · 仍开）：批量操作栏分隔线的 0.18 透明度未提令牌。

463 追记（R455 · 仍开）：展开态已加载内容仍无帧。

464 追记（R455 · 仍开）：其它自绘控件仍无同类帮助判据。

465 追记（R455 · 仍开）：HTML 引用块没有导引线。

466 追记（R455 · 仍开）：HTML 表格的表头没有同档字重。

467 追记（R455 · 仍开）：代码块行号的 9pt 档只在纯函数里验。

468 追记（R455 · 仍开）：HTML 代码块没有行号。

469 追记（R455 · 仍开）：代码块行号的选中态/滚动态没有帧。

470 追记（R455 · 仍开）：关于页正文在 runner 1x 是平涂。

471 已结案（R443）。

472 追记（R455 · 仍开）：M613 本机 2x 空名册（机器前提）。

473 追记（R455 · 仍开）：设置侧栏文字的真机 vibrant 暗档没有同屏对照。

474 追记（R455 · 仍开）：长来源 App 名的截断没有帧。

475 追记（R455 · 仍开）：侧栏搜索未匹配来源 App 的 bundle ID。

476 追记（R455 · 仍开）：代码块语言标签在长首行时被省略，没有帧。

477 追记（R455 · 仍开）：HTML 渲染器的代码块没有语言标签。

478 追记（R455 · 仍开）：HTML 预览的 `<hr>` 没有同一条通栏线。

479 追记（R455 · 仍开）：HTML 表格体行没有同一条分隔线。

480 追记（R455 · 仍开）：QuickPick 键盘提示 1x 已签收；12 帧名单仍只在本地。

481 追记（R455 · 仍开）：HTML 任务列表没有同一条完成态弱化。

482 追记（R455 · 仍开）：HTML 渲染路径的列表没有同一条悬挂制表位。

483 追记（R455 · 仍开）：权重滑块只有中心刻度，0% / 200% 端点没有标签。

484 追记（R455 · 仍开）：HTML 渲染路径的 `<del>` 没有同一条颜色弱化。

485 追记（R455 · 仍开）：弱化色在选中/高亮底色上的对比度没有帧。

**486. 行内代码两侧都是标点时没有横向 padding**（R455 观察）
    现象：R455 只向空白侧加 3pt；`` `code`。`` 这类两侧都紧贴标点的行内码横向 padding=0，只剩上下 1pt，视觉上仍偏挤。
    修法：用更小的固定 padding（如 1pt）给标点侧，或渲染层插入 zero-width 间距（不能改可见文字）；加一帧两侧标点的样本。
"""

STATE_SECTION = u"""## R455 状态（2026-10-28 · 本地 · 第 454 轮 / Round 452）：行内代码底色带补空白侧内边距（旧带 94.5pt/字 92.0pt、隙 2.5 → 新带 98.5pt/字 92.5pt、隙 6.0；2 张旧帧变化、基线 262）；全量 1252/56/1（唯一红＝Round4Markdown 旧 `.backgroundColor` 期望，已改到新属性并过滤复跑；二次全量负载下挂起）；R453 head 5c925a9 success（产品 2 文件，行内代码底色位）

最后更新：2026-10-28（本地 · R455 / 第 454 轮 / Round 452）：内联码底色原由属性串 `.backgroundColor` 涂，只到字形 advance —— 实测带 94.5pt、字 92.0pt，左右各 ~1pt。修法：去掉 `.backgroundColor`，新 `InlineCodeBackground` 在背景层画圆角带（上下各 1pt）；横向只向**空白侧**各让 3pt（前一个是空格/行首、后一个是空格/行尾），紧贴标点时不加（否则会盖住后随的“。”）。旧/新：`INLINE_CODE_PAD light 带宽=98.5pt 字宽=92.5pt 隙=6.0pt`、`dark 同形`（旧 94.5/92.0/2.5）。**2 张旧帧变化**（`detail-markdown-rendered` 亮/暗）、0 新增/缺失；基线名单 **262**（同 commit 更新）；已看亮/暗：带左缘离开“行内”的末字、右缘停在“。”前。`M1246/M1247` **2/2**；新单测 4 条 + 帧判据（连续带色行 + 带内字宽）。**旧期望修正**：全量红在 `Round4MarkdownTests.testMarkdownFileGoesThroughTheRealPreviewPipelineIntoAStyledTextView`（它钉着 `.backgroundColor`）；契约是"行内码有可区分底色"，R455 换成 `inlineCodeAttribute` + 自绘带，于是把断言改到新属性并写明像素证人，过滤重跑通过。预检 **233/215/604 bad=0**、ARM **326/1087**、HIDDEN **318/1017 rot=0**。⓪：一次快进 push **`c041c8d..d48bb05` success**（三笔）、HEAD=origin/main=`d48bb05`、**ahead=0**；**`40645430259 ↔ 5c925a9` success**（STRIKE_DIM light 135.4/108.0 +27.4、dark 141.8/174.6 −32.7、隙 3/3；TASK_DIM 157.9/114.7 +43.2、128.4/166.4 −38.1）；**`40645469967 ↔ c041c8d` failure 只有 Motion floor**（`testCopyReceipt...` 1<2，Swift 全绿）；`40640660665`/`40642482086`/`40642524490`/`40636558557` success；`40634880705 ↔ 9743379` failure（滚动会话采样红 + Motion 模式标签 1<2）；`0737460`/`ecb8e69` 仅 Motion；`36284e1` dark 行带（已修）；`40653092761 ↔ d48bb05`（R454 head）读时 in_progress ⇒ NOT-RUN。全量 **1252/56/1**（旧期望红已改并通过过滤复跑；第二次全量在负载下挂起被停 ⇒ **`FULL_SUITE_REREAD_NOT_RUN=load-hang`**）；`PerfBudgetTests.testImageComparisonCostStaysBounded` 在混合/高负载跑里偶发 310ms>250（单跑 178ms 过）⇒ **`LOCAL_PERF_BUDGET_FLAKE=load`**；滚动套件单跑 **4/4**（本跑未复现 5 红）。捕获卷 **262 帧**；基线 **262/0/0/0**；build **0 告警**；换装 `ok / SHA_MATCH=1 / 383=383`（条目 383）；`STORE-SIZE lines=1108 funcs=52 longest=66`；产品面连续零改动 **1** 轮（as-of 454，`python3 scripts/product_streak.py --streak-for 454`，last=ee930b6）。清账与电池在台账后复跑。

本轮做了什么：
① ⓪ push c041c8d..d48bb05 success、ahead=0；R453 head 5c925a9 success（STRIKE_DIM/TASK_DIM 签收）；c041c8d 唯一红＝Motion receipt 采样；R454 head in_progress ⇒ NOT-RUN。
② 产品：行内代码底色带空白侧内边距（旧 2.5 → 新 6.0；2 张旧帧变化、基线 262）。
③ 判据：M1246/M1247 2/2；新单测 4 条 + 帧判据；旧 `.backgroundColor` 期望改到 `inlineCodeAttribute`（机制换代）；precheck 233/215/604；hidden rot 0。
④ 436：Motion floor 4/5/77、red 0、not-run=notice-banner；receipt 采样红在 c041c8d 上具名；不改门槛、不重猜 must_judge。
⑤ 367：hidden 表 318 / 可判 1017 / rot 0。
⑥ 捕获 262 帧；基线 262/0/0/0；build 0 告警；换装 ok/383=383；全量 1252/56/1（旧期望红已修；二次挂起具名；perf/滚动 flake 具名）。

NOT-RUN / 阻塞（分开写）：① `40653092761 ↔ d48bb05`（R454 head，in_progress）；② R455 自身跑；③ `FULL_SUITE_REREAD_NOT_RUN=load-hang`；④ `LOCAL_PERF_BUDGET_FLAKE=load`；⑤ `RUNNER_SCROLL_SESSION_FLAKE`（9743379；R456 重跑）；⑥ 436 的 receipt 采样红（c041c8d 唯一红，1<2）；⑦ 行内代码两侧标点时无横向 padding（486）；⑧ 弱化色选中态对比（485）；⑨ HTML 的 `<del>`（484）；⑩ HTML 列表缩进/任务弱化/表格体行（482/481/479）；⑪ 设置内容列 1x 平涂；⑫ 设置脚注带 1x；⑬ 主窗口 content 帧 1x；⑭ 高夹具 1x；⑮ 13+ 菜单像素/标题；⑯ 真实拖拽；⑰ Dock 像素；⑱ 源图标最小窗文字 1x；⑲ 本地全量 5 条滚动红（本跑未复现、隔离 4/4）；⑳ 2x/extended；㉑ 固定块揭示偏移（455）；㉒ 跨年时间（456）；㉓ 主列表暗档文字盲区（457）；㉔ 真机/多屏（447）；㉕ 真菜单栏、12 实时腿；㉖ `table-lazy-rows`；㉗ HTML 六档字号（460）；㉘ 清除 × 命中区（461）；㉙ 分隔线令牌（462）；㉚ 展开态已加载内容无帧（463）；㉛ 其它自绘控件帮助文本（464）；㉜ HTML 引用块无导引线（465）；㉝ HTML 表格表头无同档（466）；㉞ 100+ 行行号（467）；㉟ HTML 代码块行号（468）；㊱ 行号选中/滚动两态（469）；㊲ 关于页 1x 盲（470）；㊳ M613 机器前提（472）；㊴ 真机 vibrant 暗档（473）；㊵ 长来源截断（474）；㊶ bundle ID 未搜（475）；㊷ 长首行标签省略无帧（476）；㊸ HTML 代码块无语言标签（477）；㊹ HTML `<hr>` 无通栏线（478）；㊺ HTML 表格体行无同一条线（479）；㊻ QuickPick 键盘提示 1x（480）；㊼ HTML 任务列表无弱化（481）；㊽ HTML 列表缩进（482）；㊾ 中心刻度端点标签（483）；㊿ HTML 的 `<del>`（484）；[51] 弱化色选中态（485）；[52] 437–486 的未结项仍开。

下一轮（R456）的靶：⓪ 先 `git push origin main`（禁 amend/force）并复核 ahead=0；读 R455 主笔+追记 head 跑、`40653092761 ↔ d48bb05`（R454 head，DEEMPHASIS_CONTRAST）、`40645430259 ↔ 5c925a9`（R453 head，STRIKE_DIM 已签收）、`40645469967 ↔ c041c8d`（Motion receipt 采样）、`40640660665 ↔ 86044bf`（LIST_HANG_STYLE 已签收）、`40642482086 ↔ e083179`（WEIGHT_CENTER_TICK 具名 NOT_RUN）、`40636558557 ↔ 667d1a2`（TASK_DIM 1x）、`40634880705 ↔ 9743379`（滚动会话采样红原文）的全部失败步骤（成对 run↔commit），重点看 `INLINE_CODE_PAD` 两档 98.5/92.5/6.0、`DEEMPHASIS_CONTRAST` 107/255/5.33 与 169/30/7.09、`STRIKE_DIM` 135.4/108.0 与 141.8/174.6、`TASK_DIM` 157.9/114.7、`WEIGHT_CENTER_TICK` 9/5.0/0.0 或具名 NOT_RUN、`LIST_HANG_STYLE` 16.0/16.0/0.0、`QUICKPICK_HINT` 400/519、`TABLE_ROW_LINES` 3/0/108.0/102.0/1.0、`THEMATIC_RULE` 597.0/1.0/1、`CODE_LANGUAGE` 116/126、`HISTORY_SEARCH_SOURCE` 两档 0→1、`PROBE_DOMAIN` 44/20、`TABLE_HEADER` 1.10、`CODE_LINE_NUMBERS` 3/21/100% 与 436；in_progress/0 字节不算绿；`RUNNER_SCROLL_SESSION_FLAKE` 与 `LOCAL_PERF_BUDGET_FLAKE` 必须原样重跑复核（不改门槛）；`FULL_SUITE_REREAD_NOT_RUN=load-hang` 下一轮在较轻负载下重读；① 现读 rot=0，按 `HIDDEN_ROT` 查新腐烂；② 继续产品视觉位并落 Sources、换缺陷类别（不要再做行内代码底色/弱化色对比度/删除线/权重刻度/列表悬挂缩进/任务项完成态/浮层键盘提示/表格体行分隔/主题分隔线/代码块语言标签/代码块行号/表格表头/引用导引线/侧栏搜索来源/主列表来源行/设置侧栏文字/设置关于页/录制帮助/多文件展开/批量分隔/浮层搜索/图片/HTML/排除名单/行内符号/时间列/分区头/侧栏脚注/详情头部/Dock/菜单栏/横幅/回执/热图/计数/空态/无结果/焦点/悬停/选中/滚动/CTA）；③ 436 只复核新跑 Motion floor，不重猜 `must_judge`。
"""

R455_REPORT_BULLET = u"""- **R455（行内代码底色位）**：内联码底色原由属性串 `.backgroundColor` 涂，只到字形 advance —— 带 94.5pt、字 92.0pt、隙仅 2.5。去掉属性底色，新 `InlineCodeBackground` 在背景层画圆角带（上下 1pt），横向只向**空白侧**各让 3pt（紧贴标点时不加，避免盖住后随的“。”）。读数 `INLINE_CODE_PAD light 带宽=98.5pt 字宽=92.5pt 隙=6.0pt`、dark 同形（旧 2.5）。**2 张旧帧变化**、0 新增，基线 **262/0/0/0**；已看亮/暗带缘不压字。`M1246/M1247` **2/2**；新单测 4 条 + 帧判据（连续带色行 + 带内字宽）；**旧期望修正**：全量红在 `Round4MarkdownTests` 钉着 `.backgroundColor`，已改到 `inlineCodeAttribute`（机制换代、意图不变）并过滤复跑通过；预检 233/215/604 bad=0、ARM 326/1087、HIDDEN 318/1017 rot=0。⓪：一次快进 push **`c041c8d..d48bb05` success**、HEAD=origin/main=`d48bb05`、ahead=0；`40645430259 ↔ 5c925a9` success（STRIKE_DIM 135.4/108.0 +27.4、dark 141.8/174.6 −32.7、隙 3/3；TASK_DIM 157.9/114.7、128.4/166.4）；`40645469967 ↔ c041c8d` failure 仅 Motion receipt 1<2（Swift 全绿）；`40653092761 ↔ d48bb05`（R454 head）读时 in_progress ⇒ NOT-RUN。全量 **1252/56/1**（旧期望红已修；二次全量负载下挂起 ⇒ `FULL_SUITE_REREAD_NOT_RUN=load-hang`）；PerfBudget 影像比较在混合/高负载跑里偶发 310ms>250（单跑 178ms 过）⇒ `LOCAL_PERF_BUDGET_FLAKE=load`；滚动套件单跑 4/4。捕获 262 帧；build 0 告警；换装 ok/SHA_MATCH=1/383=383（条目 383）；STORE-SIZE 1108/52/66；电池 683/5。
"""

audit = rd(AUDIT); iter_text = rd(ITER); decisions = rd(DECISIONS)
changelog = rd(CHANGELOG); backlog = rd(BACKLOG); state = rd(STATE); report = rd(REPORT)

if audit.count(AUDIT_TITLE) != 1: raise SystemExit("REFUSED AUDIT %d" % audit.count(AUDIT_TITLE))
if u"第 454 轮（R455" in audit: raise SystemExit("REFUSED AUDIT 已有 R455")
if u"## Round 452 · R455" in iter_text: raise SystemExit("REFUSED ITER 已有 Round 452")
if u"## D-451" in decisions: raise SystemExit("REFUSED DECISIONS 已有 D-451")
if u"行内代码底色带补空白侧内边距" in changelog: raise SystemExit("REFUSED CHANGELOG 已有该标题")
if u"**486." in backlog: raise SystemExit("REFUSED BACKLOG 已有 486")
if state.count(u"## R454 状态") != 1: raise SystemExit("REFUSED STATE %d" % state.count(u"## R454 状态"))
U_CELL_OLD = u"U-31 … U-1697（R454 现读抬到最新一节）"
if report.count(U_CELL_OLD) != 1: raise SystemExit("REFUSED REPORT U %d" % report.count(U_CELL_OLD))
if report.count(u"AGENT_STATE.md` 的 R454 节 ②") != 1: raise SystemExit("REFUSED REPORT pointer")

new_audit = audit.replace(AUDIT_TITLE, AUDIT_SECTION + AUDIT_TITLE, 1)
new_iter = iter_text.rstrip() + "\n\n" + ITER_SECTION + "\n"
new_decisions = decisions.rstrip() + "\n\n" + DECISION_451 + "\n"
marker = u"## [Unreleased]\n"
if changelog.count(marker) != 1: raise SystemExit("REFUSED CHANGELOG")
new_changelog = changelog.replace(marker, marker + "\n" + CHANGELOG_SECTION, 1)
new_backlog = backlog.rstrip() + "\n\n" + BACKLOG_SECTION + "\n"
new_state = state.replace(u"## R454 状态", STATE_SECTION + u"## R454 状态", 1)
new_report = report.replace(U_CELL_OLD, u"U-31 … U-1702（R455 现读抬到最新一节）", 1)
new_report = new_report.replace(u"AGENT_STATE.md` 的 R454 节 ②", u"AGENT_STATE.md` 的 R455 节 ②", 1)
new_report = new_report.rstrip() + "\n\n" + R455_REPORT_BULLET + "\n"

wr(AUDIT, new_audit); wr(ITER, new_iter); wr(DECISIONS, new_decisions)
wr(CHANGELOG, new_changelog); wr(BACKLOG, new_backlog); wr(STATE, new_state); wr(REPORT, new_report)
print("LEDGERS_R455_OK audit=%d iter=%d decisions=%d changelog=%d backlog=%d state=%d report=%d"
      % (len(new_audit), len(new_iter), len(new_decisions), len(new_changelog),
         len(new_backlog), len(new_state), len(new_report)))
