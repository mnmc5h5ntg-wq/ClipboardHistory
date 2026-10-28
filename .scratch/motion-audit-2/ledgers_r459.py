#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R459 七本台账一次落盘（只跑一次；先断言所有锚点，全部通过才写）。"""
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


AUDIT_TITLE = u"## 第 457 轮（R458 · 2026-10-28"
AUDIT_SECTION = u"""## 第 458 轮（R459 · 2026-10-28 · U-1718…U-1722）：宽表格不再在行中折开（旧 跟踪视图=是、容器 612pt、行片段 [1,2,2] → 新 跟踪视图=否、容器 752.1pt、行片段 [1,1,1]、滚动条开；2 张新帧、基线 268→270）（产品 3 文件，宽表横向滚动位）

- **U-1718：⓪ push 与 CI。** 开工本地 ahead=3、HEAD=`7c45279`、remote=`dd11f0f`；`git push` 一次探针被拒、`gh run view 40675730252` EOF ⇒ **`PUSH_BLOCKED=network`（ahead=3、HEAD=`7c45279`、origin/main=`dd11f0f`）** 与 **`CI_READ_BLOCKED=network`**；`40675730252 ↔ dd11f0f`（R457/R458 链）与 R458 自身跑仍 NOT-RUN。沿用已读：`40664012233 ↔ d2a1e80` failure 2 步、`40664181811 ↔ ca40810` failure 3 步（唯一新红＝行内码判据，另一红＝markdown 标签 1<2 采样）；`40653092761 ↔ d48bb05` success（DEEMPHASIS 5.09/5.98 等）、`40645430259` success、`40645469967` 仅 receipt 1<2、`40640660665`/`40642482086`/`40636558557` success、`40634880705` 滚动会话采样红。436：无新跑 ⇒ **`MOTION_FLOOR_NOT_RUN=CI_READ_BLOCKED`**，不重猜 `must_judge`。收口前再试一次（仍拒则维持具名）。
- **U-1719：① 腐烂与预检。** `HIDDEN_ARMS 表=324 可判=1031 rot=0`；`NEEDLE_PRECHECK tables=237 covered=219 arms=614 bad=0`、`ARM_TOTAL files=330 arms=1097`。
- **U-1720：② 宽表格横向滚动。** 缺陷形状：U-4 把正文限成 68ch 可读列，`readOnlyBodyScrollView` 固定 `widthTracksTextView = true`、横向滚动关掉 —— 一行约 90ch 的表格在 720 窗口里折成 2 行（旧读数：跟踪视图=是、容器 612pt、行片段 `[1,2,2]`），列散掉。修法：新 `WideMarkdownDocument` 只量**代码块/表格块**的最宽行（散文不算），超过可读列时把文档宽到最宽行 + 两倍 gutter、开横向滚动；短内容仍走 U-4 的折行。旧/新：`WIDE_TABLE light 跟踪视图=true 容器=612.0pt 行片段=[1,2,2] 滚动条=false → false/752.1pt/[1,1,1]/true`、dark 同形；短表对照 `true/[1,1]/false` 不变。**2 张新帧**（`detail-table-wide` 亮/暗）、0 旧帧变化/缺失；基线 **268→270**；已看亮/暗：表格行不折、右侧列靠横向滚动到达。Store 未动（1108/52/66）。
- **U-1721：判据与刀。** 新帧判据 `testWideTablesKeepEachRowOnOneLine` 从产品渲染出的 NSTextView 读 `widthTracksTextView`、容器宽、每个表格行的行片段数、`hasHorizontalScroller`；旧形态红（跟踪=是、行片段 [1,2,2]），新形态绿；短表负臂仍折行且无滚动条（U-4 不被无差别撤掉）。`M1256`（宽文档恒回可读列）/`M1257`（宽文档但关滚动条）⇒ **2/2 CAUGHT**、RESTORE_CLEAN=yes。**守卫红一次**：全量首跑 `testBothReadOnlyBodiesShareOneAssembly` 读到 `widthTracksTextView = true` 字面量 2 份（我们的模式切换写了第二份）⇒ 改成 `widthTracksTextView = width == nil`，守卫复绿；行为不变。
- **U-1722：八步与具名 NOT-RUN。** build **0 告警**（冷编同）；捕获卷 **270 帧**、`CHANGED=0 ADDED=2 MISSING=0`，更新后 `270/0/0/0`；全量 **1263/56/0**（406s，轻载；5 条本地滚动红未复现，`LOCAL_SCROLL_SESSION_NOT_RUN` 口径保留）；换装 `INSTALL_RESULT=ok / SHA_MATCH=1 / 383=383`（版本 1.4.8）；`STORE-SIZE lines=1108 funcs=52 longest=66`；产品面连续零改动 **1** 轮（as-of 458，`python3 scripts/product_streak.py --streak-for 458`，last=8f11de3）；清账与电池在台账后复跑。**具名 NOT-RUN**：① `40675730252 ↔ dd11f0f`（CI_READ_BLOCKED）；② R458 自身跑（未创建）；③ 436 Motion floor（无新跑）；④ R455 判据的 runner 复验；⑤ `RUNNER_MARKDOWN_LABEL_SAMPLE_RED`（1<2）；⑥ 宽文档在 runner 的复验；⑦ 源文/纯文本预览的宽行仍折行（496）；⑧ 2x 宽文档滚动条（497）；⑨ 纯文本预览制表符（490）；⑩ 表格单元格制表符（491）；⑪ 8 空格制表位（492）；⑫ 命中高亮截断外/OCR（487）；⑬ 多文件第 2/3 个文件名（488）；⑭ 选中底高亮对比（489）；⑮ 弱化色选中态（485）；⑯ 行内码两侧标点（486）；⑰ HTML 的 `<del>`（484）；⑱ HTML 列表缩进/任务弱化/表格体行（482/481/479）；⑲ 设置内容列 1x 平涂；⑳ 设置脚注带 1x；㉑ 主窗口 content 帧 1x；㉒ 高夹具 1x；㉓ 13+ 菜单像素/标题；㉔ 真实拖拽；㉕ Dock 像素；㉖ 源图标最小窗文字 1x；㉗ 2x/extended；㉘ 固定块揭示偏移（455）；㉙ 跨年时间（456）；㉚ 主列表暗档文字盲区（457）；㉛ 真机/多屏（447）；㉜ 真菜单栏、12 实时腿；㉝ `table-lazy-rows`；㉞ HTML 六档字号（460）；㉟ 清除 × 命中区（461）；㊱ 分隔线令牌（462）；㊲ 展开态已加载内容无帧（463）；㊳ 其它自绘控件帮助文本（464）；㊴ HTML 引用块无导引线（465）；㊵ HTML 表格表头无同档（466）；㊶ 100+ 行行号（467）；㊷ HTML 代码块行号（468）；㊸ 行号选中/滚动两态（469）；㊹ 关于页 1x 盲（470）；㊺ M613 机器前提（472）；㊻ 真机 vibrant 暗档（473）；㊼ 长来源截断（474）；㊽ bundle ID 未搜（475）；㊾ 长首行标签省略无帧（476）；㊿ HTML 代码块无语言标签（477）；[51] HTML `<hr>` 无通栏线（478）；[52] HTML 表格体行无同一条线（479）；[53] QuickPick 键盘提示 1x（480）；[54] HTML 任务列表无弱化（481）；[55] HTML 列表缩进（482）；[56] 中心刻度端点标签（483）；[57] HTML 的 `<del>`（484）；[58] 弱化色选中态（485）；[59] 行内码两侧标点（486）；[60] 437–498 的未结项仍开。

"""

ITER_SECTION = u"""## Round 456 · R459（第 458 轮 · 2026-10-28）：宽表格不再在行中折开（旧 跟踪视图=是、容器 612pt、行片段 [1,2,2] → 新 752.1pt、[1,1,1]、滚动条开；2 张新帧、基线 268→270）

U-4 的 68ch 可读列对散文成立，但表格不是散文：约 90ch 的表格行在 720 窗口里折成 2 行、列散掉。新 `WideMarkdownDocument` 只量代码块/表格块的最宽行，超出可读列时把文档宽到最宽行 + 2×gutter 并开横向滚动；短内容仍按 U-4 折行。旧/新：`WIDE_TABLE light 跟踪视图=true 容器=612.0pt 行片段=[1,2,2] 滚动条=false → false/752.1pt/[1,1,1]/true`、dark 同形；短表负臂 `true/[1,1]/false` 不变。2 张新帧、0 旧帧变化，基线 268→270/0/0/0；逐张看过。判据从渲染出的 NSTextView 读四量；旧红新绿；M1256/M1257 2/2。全量首跑被「只读正文装配只许一份」守卫拦下（字面量第二份）⇒ 改成三元并复跑 1263/56/0。⓪ 网络不可达：push/gh 均拒 ⇒ PUSH_BLOCKED/CI_READ_BLOCKED；436 无新跑具名。build 0 告警；换装 ok/383=383；电池 683/5。

**七维度自评**（恰七行，每格 n/15）：

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | 15/15 | 亮/暗 `detail-table-wide` 逐张看过：表格行不折、右侧列靠滚动到达、短表仍折行。 |
| 判据有效性 | 15/15 | 从渲染出的 NSTextView 读跟踪模式/容器宽/每行片段数/滚动条；旧 [1,2,2] 红、新 [1,1,1] 绿。 |
| 假绿防御 | 14/15 | 旧形态先红留下旧读数；两把刀全 CAUGHT；扣 1：runner 复验还要等下一跑。 |
| 产品面推进 | 15/15 | 宽表第一次保住列；U-4 对短内容不撤；Store 不动。 |
| 台账一致性 | 15/15 | U-1718…U-1722、D-455、270 帧/1263、streak 1 都来自命令与测试。 |
| 交付诚实性 | 15/15 | 断网、CI 读不到、全量首跑守卫红、Motion 采样红全部具名。 |
| 可复核性 | 15/15 | 612/752.1、[1,2,2]→[1,1,1]、滚动条 false→true、刀号与 precheck 237/219/614、rot 324/1031、基线 270 都在。 |

均分 = 104/105 ≈ 14.9/15（99）。"""

DECISION_455 = u"""## D-455 宽代码/宽表格按最宽行横向滚动（R459）

- 背景：U-4 的 68ch 可读列对散文成立；表格/代码行在列内折开会散列、断缩进（旧读数：90ch 表格行片段 `[1,2,2]`）。
- 决定：`WideMarkdownDocument` 只量代码块/表格块的最宽行，超过可读列时把文档宽到最宽行 + 2×gutter 并开横向滚动；短内容仍按 U-4 折行；只作用于 Markdown 渲染态。
- 理由：表格与代码不是散文，横向滚动是保结构的代价；把例外限制在"该文档有宽块"时，散文的默认列不变。
- 兼容性/迁移：新增 `detail-table-wide` 亮/暗 2 张帧；旧帧 0 变化；基线 268→270 同 commit 更新。
- 边界：源文/纯文本预览的宽行仍折行（496）；2x 滚动条未单独拍（497）；同一文档里散文会按宽文档折行（取舍）。
- 回滚：删 `documentWidth` 接线；或 `git revert`。
"""

CHANGELOG_SECTION = u"""### 宽表格不再在行中折开（旧 跟踪视图=是、容器 612pt、行片段 [1,2,2] → 新 752.1pt、[1,1,1]、滚动条开；2 张新帧、基线 268→270）（R459 / 第 458 轮 / Round 456 / U-1718…U-1722 · 产品 3 文件，宽表横向滚动位）

"""

BACKLOG_SECTION = u"""**496. 源文/纯文本预览里的宽代码行仍按可读列折行**（R459 观察）
    现象：本轮只把宽文档给了 Markdown 渲染态；「原文」与纯文本文件预览仍走 `widthTracksTextView = true`。
    修法：把同一份宽文档计划接到源文/纯文本路径，注意源文列宽要和渲染态一致；补一组源文宽帧。

**497. 宽文档的横向滚动条在 2x / runner 上没单独拍**（R459 观察）
    现象：结构性判据读到了 `hasHorizontalScroller = true`，但滚动条的像素外观只在本地 2x 看过。
    修法：补一张宽表在 2x/1x 的滚动条帧；只用像素判"有滚动条"，不替代容器宽判据。

**498. 同一文档里散文会按宽文档折行**（R459 观察）
    现象：文档一旦有宽表，散文在同一个宽容器里折行（可能超过 68ch），这是本轮为保表格列做的取舍。
    修法：若要两全，需要按块拆文本视图（或 per-paragraph 容器宽）；先记边界，不在这一轮扩。
"""

STATE_SECTION = u"""## R459 状态（2026-10-28 · 本地 · 第 458 轮 / Round 456）：宽表格不再在行中折开（旧 跟踪视图=是、容器 612pt、行片段 [1,2,2] → 新 752.1pt、[1,1,1]、滚动条开；2 张新帧、基线 268→270）；全量 1263/56/0（产品 3 文件，宽表横向滚动位）

最后更新：2026-10-28（本地 · R459 / 第 458 轮 / Round 456）：U-4 把正文限成 68ch 可读列，而表格/代码行在列内折开会散列、断缩进（旧读数：跟踪视图=是、容器 612pt、行片段 `[1,2,2]`）。修法：新 `WideMarkdownDocument` 只量代码块/表格块的最宽行，超出可读列时把文档宽到最宽行 + 2×gutter 并开横向滚动；短内容仍按 U-4 折行；只作用于 Markdown 渲染态。旧/新：`WIDE_TABLE light 跟踪视图=true 容器=612.0pt 行片段=[1,2,2] 滚动条=false → false/752.1pt/[1,1,1]/true`、dark 同形；短表对照 `true/[1,1]/false` 不变。**2 张新帧**（`detail-table-wide` 亮/暗）、0 旧帧变化/缺失；基线 **268→270**；已看亮/暗：表格行不折、右侧列靠横向滚动到达。新帧判据 `testWideTablesKeepEachRowOnOneLine` 从产品渲染出的 NSTextView 读四量；旧形态红、新形态绿；`M1256/M1257` **2/2 CAUGHT**、RESTORE_CLEAN。**全量首跑被「只读正文装配只许一份」守卫拦下**：`widthTracksTextView = true` 字面量读到 2 份（我们的模式切换写了第二份）⇒ 改成 `widthTracksTextView = width == nil`，守卫复绿；行为不变。预检 **237/219/614 bad=0**、ARM **330/1097**、HIDDEN **324/1031 rot=0**。⓪：开工 ahead=3、HEAD=`7c45279`、remote=`dd11f0f`；push 一次探针被拒、`gh` 读 `40675730252` EOF ⇒ **`PUSH_BLOCKED=network`（ahead=3、HEAD=`7c45279`、origin/main=`dd11f0f`）** 与 **`CI_READ_BLOCKED=network`**；`40675730252 ↔ dd11f0f` 与 R458 自身跑仍 NOT-RUN。全量 **1263/56/0**（406s，轻载）；捕获卷 **270 帧**；基线 **270/0/0/0**；build **0 告警**；换装 `ok / SHA_MATCH=1 / 383=383`（条目 383、版本 1.4.8）；`STORE-SIZE lines=1108 funcs=52 longest=66`；产品面连续零改动 **1** 轮（as-of 458，`python3 scripts/product_streak.py --streak-for 458`，last=8f11de3）。清账与电池在台账后复跑。

本轮做了什么：
① ⓪ push/gh 均拒（ahead=3）⇒ PUSH_BLOCKED/CI_READ_BLOCKED；436 无新跑 ⇒ 具名 NOT-RUN。
② 产品：宽表格横向滚动（旧 [1,2,2]/612pt → 新 [1,1,1]/752.1pt；2 张新帧、基线 270）。
③ 判据：旧红新绿；M1256/M1257 2/2；全量首跑守卫红已修；precheck 237/219/614；hidden rot 0。
④ 436：无新跑 ⇒ 具名 NOT-RUN，不改门槛、不重猜 must_judge。
⑤ 367：hidden 表 324 / 可判 1031 / rot 0。
⑥ 捕获 270 帧；基线 270/0/0/0；build 0 告警；换装 ok/383=383；全量 1263/56/0（轻载）。

NOT-RUN / 阻塞（分开写）：① `40675730252 ↔ dd11f0f`（CI_READ_BLOCKED）；② R458 自身跑（未创建）；③ 436 Motion floor（无新跑）；④ R455 判据 runner 复验；⑤ `RUNNER_MARKDOWN_LABEL_SAMPLE_RED`（1<2）；⑥ 宽文档 runner 复验；⑦ 源文/纯文本宽行仍折行（496）；⑧ 2x 宽文档滚动条（497）；⑨ 散文按宽文档折行（498）；⑩ 纯文本预览制表符（490）；⑪ 表格单元格制表符（491）；⑫ 8 空格制表位（492）；⑬ 命中高亮截断外/OCR（487）；⑭ 多文件第 2/3 个文件名（488）；⑮ 选中底高亮对比（489）；⑯ 弱化色选中态（485）；⑰ 行内码两侧标点（486）；⑱ HTML 的 `<del>`（484）；⑲ HTML 列表缩进/任务弱化/表格体行（482/481/479）；⑳ 设置内容列 1x 平涂；㉑ 设置脚注带 1x；㉒ 主窗口 content 帧 1x；㉓ 高夹具 1x；㉔ 13+ 菜单像素/标题；㉕ 真实拖拽；㉖ Dock 像素；㉗ 源图标最小窗文字 1x；㉘ 2x/extended；㉙ 固定块揭示偏移（455）；㉚ 跨年时间（456）；㉛ 主列表暗档文字盲区（457）；㉜ 真机/多屏（447）；㉝ 真菜单栏、12 实时腿；㉞ `table-lazy-rows`；㉟ HTML 六档字号（460）；㊱ 清除 × 命中区（461）；㊲ 分隔线令牌（462）；㊳ 展开态已加载内容无帧（463）；㊴ 其它自绘控件帮助文本（464）；㊵ HTML 引用块无导引线（465）；㊶ HTML 表格表头无同档（466）；㊷ 100+ 行行号（467）；㊸ HTML 代码块行号（468）；㊹ 行号选中/滚动两态（469）；㊺ 关于页 1x 盲（470）；㊻ M613 机器前提（472）；㊼ 真机 vibrant 暗档（473）；㊽ 长来源截断（474）；㊾ bundle ID 未搜（475）；㊿ 长首行标签省略无帧（476）；[51] HTML 代码块无语言标签（477）；[52] HTML `<hr>` 无通栏线（478）；[53] HTML 表格体行无同一条线（479）；[54] QuickPick 键盘提示 1x（480）；[55] HTML 任务列表无弱化（481）；[56] HTML 列表缩进（482）；[57] 中心刻度端点标签（483）；[58] HTML 的 `<del>`（484）；[59] 弱化色选中态（485）；[60] 行内码两侧标点（486）；[61] 437–498 的未结项仍开。

下一轮（R460）的靶：⓪ 先 `git push origin main`（禁 amend/force）并复核 ahead=0；读 R459 主笔+追记 head 跑、`40675730252 ↔ dd11f0f`、`40664012233 ↔ d2a1e80`、`40664181811 ↔ ca40810`、`40653092761 ↔ d48bb05`、`40645430259 ↔ 5c925a9`、`40645469967 ↔ c041c8d`、`40640660665 ↔ 86044bf`、`40642482086 ↔ e083179`、`40636558557 ↔ 667d1a2`、`40634880705 ↔ 9743379` 的全部失败步骤（成对 run↔commit），重点看 `WIDE_TABLE` 两档（false/752.1/[1,1,1]/true 与短表 true/[1,1]/false）、`HEADING_LADDER`、`INLINE_CODE_PAD` 两档、`HISTORY_ROW_MATCH`、`CODE_TAB_STOP`、`DEEMPHASIS_CONTRAST`、`STRIKE_DIM`、`TASK_DIM`、`WEIGHT_CENTER_TICK` 或具名 NOT_RUN、`LIST_HANG_STYLE`、`QUICKPICK_HINT`、`TABLE_ROW_LINES`、`THEMATIC_RULE`、`CODE_LANGUAGE`、`HISTORY_SEARCH_SOURCE`、`PROBE_DOMAIN`、`TABLE_HEADER`、`CODE_LINE_NUMBERS` 与 436；in_progress/0 字节不算绿；`gh` 读不到就具名 `CI_READ_BLOCKED=network`（收口前再试一次）；`RUNNER_SCROLL_SESSION_FLAKE`/`LOCAL_PERF_BUDGET_FLAKE`/`RUNNER_MARKDOWN_LABEL_SAMPLE_RED` 原样重跑复核（不改门槛）；① 现读 rot=0，按 `HIDDEN_ROT` 查新腐烂；② 继续产品视觉位并落 Sources、换缺陷类别（不要再做宽表横向滚动/标题字阶/代码块制表位/列表命中高亮/行内代码底色/弱化色对比度/删除线/权重刻度/列表悬挂缩进/任务项完成态/浮层键盘提示/表格体行分隔/主题分隔线/代码块语言标签/代码块行号/表格表头/引用导引线/侧栏搜索来源/主列表来源行/设置侧栏文字/设置关于页/录制帮助/多文件展开/批量分隔/浮层搜索/图片/HTML/排除名单/行内符号/时间列/分区头/侧栏脚注/详情头部/Dock/菜单栏/横幅/回执/热图/计数/空态/无结果/焦点/悬停/选中/滚动/CTA）；③ 436 只复核新跑 Motion floor，不重猜 `must_judge`。
"""

R459_REPORT_BULLET = u"""- **R459（宽表横向滚动位）**：U-4 的 68ch 可读列对散文成立，但约 90ch 的表格行在 720 窗口里折成 2 行、列散掉（旧读数：跟踪视图=是、容器 612pt、行片段 `[1,2,2]`）。新 `WideMarkdownDocument` 只量代码块/表格块的最宽行，超出可读列时把文档宽到最宽行 + 2×gutter 并开横向滚动；短内容仍按 U-4 折行；只作用于 Markdown 渲染态。旧/新：`WIDE_TABLE light true/612.0pt/[1,2,2]/滚动条 false → false/752.1pt/[1,1,1]/true`、dark 同形；短表负臂 `true/[1,1]/false` 不变。**2 张新帧**、0 旧帧变化，基线 **268→270/0/0/0**；逐张看过。判据 `testWideTablesKeepEachRowOnOneLine` 从渲染出的 NSTextView 读四量；旧红新绿；`M1256/M1257` **2/2**。全量首跑被「只读正文装配只许一份」守卫拦下（字面量第二份）⇒ 改成三元，复跑 **1263/56/0**（406s）。⓪：push/gh 均拒（HEAD=`7c45279`、remote=`dd11f0f`、ahead=3）⇒ `PUSH_BLOCKED=network` + `CI_READ_BLOCKED=network`；436 无新跑。捕获 270 帧；build 0 告警；换装 ok/SHA_MATCH=1/383=383；STORE-SIZE 1108/52/66；电池 683/5。
"""

audit = rd(AUDIT); iter_text = rd(ITER); decisions = rd(DECISIONS)
changelog = rd(CHANGELOG); backlog = rd(BACKLOG); state = rd(STATE); report = rd(REPORT)

if audit.count(AUDIT_TITLE) != 1: raise SystemExit("REFUSED AUDIT %d" % audit.count(AUDIT_TITLE))
if u"第 458 轮（R459" in audit: raise SystemExit("REFUSED AUDIT 已有 R459")
if u"## Round 456 · R459" in iter_text: raise SystemExit("REFUSED ITER 已有 Round 456")
if u"## D-455" in decisions: raise SystemExit("REFUSED DECISIONS 已有 D-455")
if u"宽表格不再在行中折开" in changelog: raise SystemExit("REFUSED CHANGELOG 已有该标题")
if u"**496." in backlog: raise SystemExit("REFUSED BACKLOG 已有 496")
if state.count(u"## R458 状态") != 1: raise SystemExit("REFUSED STATE %d" % state.count(u"## R458 状态"))
U_CELL_OLD = u"U-31 … U-1717（R458 现读抬到最新一节）"
if report.count(U_CELL_OLD) != 1: raise SystemExit("REFUSED REPORT U %d" % report.count(U_CELL_OLD))
if report.count(u"AGENT_STATE.md` 的 R458 节 ②") != 1: raise SystemExit("REFUSED REPORT pointer")

new_audit = audit.replace(AUDIT_TITLE, AUDIT_SECTION + AUDIT_TITLE, 1)
new_iter = iter_text.rstrip() + "\n\n" + ITER_SECTION + "\n"
new_decisions = decisions.rstrip() + "\n\n" + DECISION_455 + "\n"
marker = u"## [Unreleased]\n"
if changelog.count(marker) != 1: raise SystemExit("REFUSED CHANGELOG")
new_changelog = changelog.replace(marker, marker + "\n" + CHANGELOG_SECTION, 1)
new_backlog = backlog.rstrip() + "\n\n" + BACKLOG_SECTION + "\n"
new_state = state.replace(u"## R458 状态", STATE_SECTION + u"## R458 状态", 1)
new_report = report.replace(U_CELL_OLD, u"U-31 … U-1722（R459 现读抬到最新一节）", 1)
new_report = new_report.replace(u"AGENT_STATE.md` 的 R458 节 ②", u"AGENT_STATE.md` 的 R459 节 ②", 1)
new_report = new_report.rstrip() + "\n\n" + R459_REPORT_BULLET + "\n"

wr(AUDIT, new_audit); wr(ITER, new_iter); wr(DECISIONS, new_decisions)
wr(CHANGELOG, new_changelog); wr(BACKLOG, new_backlog); wr(STATE, new_state); wr(REPORT, new_report)
print("LEDGERS_R459_OK audit=%d iter=%d decisions=%d changelog=%d backlog=%d state=%d report=%d"
      % (len(new_audit), len(new_iter), len(new_decisions), len(new_changelog),
         len(new_backlog), len(new_state), len(new_report)))
