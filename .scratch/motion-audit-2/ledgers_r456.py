#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R456 七本台账一次落盘（只跑一次；先断言所有锚点，全部通过才写）。"""
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


AUDIT_TITLE = u"## 第 454 轮（R455 · 2026-10-28"
AUDIT_SECTION = u"""## 第 455 轮（R456 · 2026-10-28 · U-1703…U-1707）：侧栏搜索命中在行内高亮（旧 0/0 → 新来源带 1200/1560、正文标题带 2185/2660；2 张旧帧变化 + 2 张新帧、基线 262→264）（产品 3 文件，列表命中高亮位）

- **U-1703：⓪ push 与 CI 读数。** 开工 remote=`d48bb05`、本地 ahead=4（`c94a995`/`16379c5`/`7200fa5`/`8f69d82`）；`git push origin main` **两次探针均被拒**（`Connection closed by 20.205.243.166 port 22`）⇒ **`PUSH_BLOCKED=network`：HEAD=`c94a995`、origin/main=`d48bb05`、ahead=4**。`gh run view 40653092761`（R454 head，DEEMPHASIS_CONTRAST）仍 **EOF** ⇒ **`CI_READ_BLOCKED=network`、NOT-RUN**；R455 主笔/追记因同一断网没有创建跑，R456 自身跑待推送后创建 ⇒ 全部 NOT-RUN。沿用 R455 已读（其 run 未变）：`40645430259 ↔ 5c925a9` success（STRIKE_DIM 135.4/108.0 +27.4、141.8/174.6 −32.7、隙 3/3；TASK_DIM 157.9/114.7 +43.2、128.4/166.4 −38.1）、`40645469967 ↔ c041c8d` failure 只有 Motion receipt 1<2（Swift 全绿）、`40640660665`/`40642482086`/`40642524490`/`40636558557` success、`40634880705 ↔ 9743379` 滚动会话采样红 + Motion 模式标签 1<2、`0737460`/`ecb8e69` 仅 Motion、`36284e1` dark 行带已修。436：本轮没有新跑 ⇒ **`MOTION_FLOOR_NOT_RUN=no-new-run（CI_READ_BLOCKED=network）`**，不重猜 `must_judge`。
- **U-1704：① 腐烂与预检。** `HIDDEN_ARMS 表=321 可判=1024 rot=0`；`NEEDLE_PRECHECK tables=234 covered=216 arms=607 bad=0`、`ARM_TOTAL files=327 arms=1090`。本轮的共用行改动把 R444 的 `M1220` 针打空（预检先读 `命中=0`）⇒ 按新 `HistoryRowMatchHighlight.sourceLine(...)` 调用重钉、R444 表复跑 **2/2 RESTORE_CLEAN**；预检回到 bad=0。
- **U-1705：② 侧栏搜索命中高亮。** 缺陷形状：过滤从 R445 起会匹配正文与来源 App 名，但行里**一个字都不标** —— 只命中来源的行（`sidebar-search-source`）整行没有线索；正文命中落在两行截断之外时也一样（旧帧实测黄像素 `0/0`）。修法：新 `HistoryRowMatchHighlight` 复用 `MatchHighlighting.segments`（与过滤同源的大小写/变音符号语义），标题/文件名按查询标命中片段、来源行**只标 App 名不标时间**（时间不是搜索字段），命中片段带 `DetailTypography.highlightColor` 底；空查询/无命中原样。旧/新：`HISTORY_ROW_MATCH light 来源查询 标题黄=0 来源黄=0 → 0/1200；正文查询 0/0 → 2185/0；无查询 0/0`、`dark 0/0 → 0/1560；0/0 → 2660/0；0/0`。**2 张旧帧变化**（`sidebar-search-source` 亮/暗）+ **2 张新帧**（`sidebar-search-content` 亮/暗）、0 缺失；基线 **262→264**（同 commit 更新）；已逐张看亮/暗：黄底只压在命中字上、不压相邻字、不挪版式。Store 未动（1108 行/52 方法/最长 66）。
- **U-1706：判据与刀。** 新单测 `HistoryRowMatchHighlightTests` 7 条（多处命中、空查询不退化、无命中、大小写与过滤同源、来源行只标 App 名、时间永不标、空来源只留时间）+ 帧判据 `testSidebarSearchRowsShowWhyTheyMatched`（同帧切三条文字带：来源查询 → 标题黄 0/来源黄 1200/1560；正文查询 → 标题黄 2185/2660/来源黄 0；无查询 → 0/0；地板 40×scale²=160）。旧形态下该判据先红、留下 `0/0` 旧读数。`M1248`（侧栏不传搜索词）/`M1249`（来源行不标 App 名）/`M1250`（所有片段都上底、空查询也发黄）⇒ **3/3 CAUGHT**、RESTORE_CLEAN=yes；R444 旧表重钉后 **2/2**。
- **U-1707：八步与具名 NOT-RUN。** build **0 告警**（冷编同）；捕获卷 **264 帧**、`CHANGED=2 ADDED=2 MISSING=0`，更新后 `264/0/0/0`；全量 **1260/56/0**（403s；本轮 5 条本地滚动红未复现，`LOCAL_SCROLL_SESSION_NOT_RUN` 口径保留；`PerfBudget` 本轮未红）；换装 `INSTALL_RESULT=ok / SHA_MATCH=1 / 383=383`（版本 1.4.8）；`STORE-SIZE lines=1108 funcs=52 longest=66`；产品面连续零改动 **1** 轮（as-of 455，`python3 scripts/product_streak.py --streak-for 455`，last=8f69d82）；清账与电池在台账后复跑。**具名 NOT-RUN**：① `40653092761 ↔ d48bb05`（CI_READ_BLOCKED）；② R455 两跑/R456 自身跑（未创建）；③ `PUSH_BLOCKED=network`（ahead=4）；④ 436 Motion floor（无新跑）；⑤ `LOCAL_SCROLL_SESSION_NOT_RUN`（本跑未复现）；⑥ 截断外/OCR 命中在列表无高亮（487）；⑦ 多文件第 2/3 个文件名命中无高亮（488）；⑧ 高亮色在选中底上的对比（489）；⑨ 弱化色选中态（485）；⑩ HTML 的 `<del>`（484）；⑪ HTML 列表缩进/任务弱化/表格体行（482/481/479）；⑫ 设置内容列 1x 平涂；⑬ 设置脚注带 1x；⑭ 主窗口 content 帧 1x；⑮ 高夹具 1x；⑯ 13+ 菜单像素/标题；⑰ 真实拖拽；⑱ Dock 像素；⑲ 源图标最小窗文字 1x；⑳ 2x/extended；㉑ 固定块揭示偏移（455）；㉒ 跨年时间（456）；㉓ 主列表暗档文字盲区（457）；㉔ 真机/多屏（447）；㉕ 真菜单栏、12 实时腿；㉖ `table-lazy-rows`；㉗ HTML 六档字号（460）；㉘ 清除 × 命中区（461）；㉙ 分隔线令牌（462）；㉚ 展开态已加载内容无帧（463）；㉛ 其它自绘控件帮助文本（464）；㉜ HTML 引用块无导引线（465）；㉝ HTML 表格表头无同档（466）；㉞ 100+ 行行号（467）；㉟ HTML 代码块行号（468）；㊱ 行号选中/滚动两态（469）；㊲ 关于页 1x 盲（470）；㊳ M613 机器前提（472）；㊴ 真机 vibrant 暗档（473）；㊵ 长来源截断（474）；㊶ bundle ID 未搜（475）；㊷ 长首行标签省略无帧（476）；㊸ HTML 代码块无语言标签（477）；㊹ HTML `<hr>` 无通栏线（478）；㊺ HTML 表格体行无同一条线（479）；㊻ QuickPick 键盘提示 1x（480）；㊼ HTML 任务列表无弱化（481）；㊽ HTML 列表缩进（482）；㊾ 中心刻度端点标签（483）；㊿ HTML 的 `<del>`（484）；[51] 弱化色选中态（485）；[52] 行内码两侧标点无 padding（486）；[53] 437–489 的未结项仍开。

"""

ITER_SECTION = u"""## Round 453 · R456（第 455 轮 · 2026-10-28）：侧栏搜索命中在行内高亮（旧 0/0 → 来源带 1200/1560、正文标题带 2185/2660；2 张旧帧变化 + 2 张新帧、基线 262→264）

过滤匹配正文与来源 App 名，行里却一个字都不标。新 `HistoryRowMatchHighlight` 复用 `MatchHighlighting` 切分：标题/文件名按查询标高亮，来源行只标 App 名不标时间，空查询/无命中原样；颜色用 `DetailTypography.highlightColor`。旧/新：`HISTORY_ROW_MATCH light 来源查询 0/0 → 0/1200、正文查询 0/0 → 2185/0、无查询 0/0`、dark 同形（0/1560、2660/0）。2 张旧帧变化 + 2 张新帧、0 缺失，基线 262→264/0/0/0；逐张看过黄底不压字、不挪版式。单测 7/7；M1248–M1250 3/3；R444 M1220 重钉后 2/2；precheck 234/216/607、rot 321/1024=0。⓪ push 两次探针被拒 ⇒ PUSH_BLOCKED（HEAD c94a995、ahead=4）；gh EOF ⇒ CI_READ_BLOCKED；436 无新跑具名。全量 1260/56/0（滚动红未复现）；build 0 告警；换装 ok/383=383；电池 683/5。

**七维度自评**（恰七行，每格 n/15）：

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | 15/15 | 4 张帧逐张看过：黄底只压命中字、不压相邻字、标题/来源行版式不动。 |
| 判据有效性 | 15/15 | 同帧切三条文字带、按字段分臂（来源/标题/负对照）；旧 0、新 1200–2660，地板 160。 |
| 假绿防御 | 14/15 | 负查询与错字段两臂都 0；扣 1：命中在截断之外/OCR 时列表无可见高亮，已记 487。 |
| 产品面推进 | 15/15 | 搜索第一次在列表里说清为什么命中；3 个 Sources 文件；Store 不动。 |
| 台账一致性 | 15/15 | U-1703…U-1707、D-452、push ahead=4、264 帧/1260、1108/66 都来自命令与测试。 |
| 交付诚实性 | 15/15 | 断网、CI 读不到、436 无新跑、滚动红未复现全部具名；全量 1260/56/0 照记。 |
| 可复核性 | 15/15 | 1200/1560/2185/2660、旧 0/0、地板 160、刀号与 precheck 234/216/607、rot 321/1024、基线 264 都在。 |

均分 = 104/105 ≈ 14.9/15（99）。"""

DECISION_452 = u"""## D-452 行内命中高亮只标可见且参与匹配的片段（R456）

- 背景：侧栏过滤匹配正文与来源 App 名，行里不标高亮 —— 只命中来源的行没有任何线索，正文命中在截断之外时也一样。
- 决定：`HistoryRowMatchHighlight` 复用 `MatchHighlighting` 的切分（与过滤同源）；标题/文件名标命中片段，来源行只标 App 名；时间不标（不参与过滤）；空查询/无命中不编高亮；颜色沿用 `DetailTypography.highlightColor`。
- 理由：高亮是「为什么这行在」的答案，亮的位置必须与过滤谓词对齐；同源切分避免两套语义。
- 兼容性/迁移：`sidebar-search-source` 亮/暗 2 张旧帧变化，新增 `sidebar-search-content` 亮/暗；基线 262→264 同 commit 更新。
- 边界：命中在截断之外/OCR（487）、多文件第 2/3 个文件名（488）、选中底上的高亮对比（489）。
- 回滚：删 `HistoryRowMatchHighlight` 的接线；或 `git revert`。
"""

CHANGELOG_SECTION = u"""### 侧栏搜索命中在行内高亮（旧 0/0 → 来源带 1200/1560、正文标题带 2185/2660；2 张旧帧变化 + 2 张新帧、基线 262→264）（R456 / 第 455 轮 / Round 453 / U-1703…U-1707 · 产品 3 文件，列表命中高亮位）

"""

BACKLOG_SECTION = u"""**487. 命中落在截断之外或 OCR 文本时，列表行仍无可见高亮**（R456 观察）
    现象：高亮只标行里可见的文字；正文命中在两行截断之外、图片 OCR 命中、或匹配「图片」字样时，行里没有黄底。
    修法：在行尾补一个「命中在正文中」的指示，或让标题预览优先展示命中上下文；需要新帧与负臂。

**488. 多文件条目只显示首个文件名，命中第 2/3 个文件名时行内无高亮**（R456 观察）
    现象：过滤会匹配任一文件名，但行只显示第一个名字 + 「等 N 个」。
    修法：把命中的那个文件名提到行首（仍保持「等 N 个」），或给计数加命中标记。

**489. 命中高亮色在选中/强调底上的对比度没有帧**（R456 观察）
    现象：`DetailTypography.highlightColor`（systemYellow 32%）只在不选中的行底上量过；选中态是强调蓝，黄底对比未判。
    修法：补一张选中 + 查询的帧，按 sRGB 对比度判定；不与行底高亮共用阈值。
"""

STATE_SECTION = u"""## R456 状态（2026-10-28 · 本地 · 第 455 轮 / Round 453）：侧栏搜索命中在行内高亮（旧 0/0 → 新来源带 1200/1560、正文标题带 2185/2660；2 张旧帧变化 + 2 张新帧、基线 262→264）；全量 1260/56/0（滚动红未复现）；⓪ 两次 push 探针被拒、gh EOF（产品 3 文件，列表命中高亮位）

最后更新：2026-10-28（本地 · R456 / 第 455 轮 / Round 453）：侧栏过滤从 R445 起匹配正文与来源 App 名，但行里此前**一个字都不标** —— 只命中来源的行（`sidebar-search-source`）整行没有线索；正文命中落在两行截断之外时也一样（旧帧黄像素 `0/0`）。修法：新 `HistoryRowMatchHighlight` 复用 `MatchHighlighting.segments`（与过滤同源），标题/文件名标命中片段、来源行**只标 App 名不标时间**，命中片段带 `DetailTypography.highlightColor` 底；空查询/无命中原样。旧/新：`HISTORY_ROW_MATCH light 来源查询 0/0 → 0/1200；正文查询 0/0 → 2185/0；无查询 0/0`、`dark 0/0 → 0/1560；0/0 → 2660/0；0/0`。**2 张旧帧变化**（`sidebar-search-source` 亮/暗）+ **2 张新帧**（`sidebar-search-content` 亮/暗）、0 缺失；基线 **262→264**（同 commit 更新）；已逐张看亮/暗：黄底只压在命中字上、不压相邻字、不挪版式。`M1248/M1249/M1250` **3/3**；新单测 7 条 + 帧判据（同帧三条文字带、地板 40×scale²）。**共用行改动**：R444 的 `M1220` 针被新来源行调用打空 ⇒ 重钉后复跑 **2/2**。预检 **234/216/607 bad=0**、ARM **327/1090**、HIDDEN **321/1024 rot=0**。⓪：开工 ahead=4、两次 push 均被拒（`Connection closed by 20.205.243.166 port 22`）⇒ **`PUSH_BLOCKED=network`（HEAD=`c94a995`、origin/main=`d48bb05`、ahead=4）**；`40653092761 ↔ d48bb05`（R454 head）gh EOF ⇒ **`CI_READ_BLOCKED=network`、NOT-RUN**；R455 两跑/R456 自身跑未创建 ⇒ NOT-RUN。全量 **1260/56/0**（403s；5 条本地滚动红未复现，`LOCAL_SCROLL_SESSION_NOT_RUN` 口径保留；`PerfBudget` 未红）；捕获卷 **264 帧**；基线 **264/0/0/0**；build **0 告警**；换装 `ok / SHA_MATCH=1 / 383=383`（条目 383、版本 1.4.8）；`STORE-SIZE lines=1108 funcs=52 longest=66`；产品面连续零改动 **1** 轮（as-of 455，`python3 scripts/product_streak.py --streak-for 455`，last=8f69d82）。清账与电池在台账后复跑。

本轮做了什么：
① ⓪ push 两次探针被拒（ahead=4）⇒ PUSH_BLOCKED=network；gh EOF ⇒ CI_READ_BLOCKED；436 无新跑 ⇒ MOTION_FLOOR_NOT_RUN；沿用 R455 已读。
② 产品：侧栏搜索命中在行内高亮（来源带 0→1200/1560、正文标题带 0→2185/2660；2 张旧帧变化 + 2 张新帧、基线 264）。
③ 判据：单测 7/7；M1248–M1250 3/3；R444 M1220 重钉 2/2；precheck 234/216/607；hidden rot 0。
④ 436：无新跑 ⇒ 具名 NOT-RUN，不改门槛、不重猜 must_judge。
⑤ 367：hidden 表 321 / 可判 1024 / rot 0。
⑥ 捕获 264 帧；基线 264/0/0/0；build 0 告警；换装 ok/383=383；全量 1260/56/0（滚动红未复现、perf 未红）。

NOT-RUN / 阻塞（分开写）：① `40653092761 ↔ d48bb05`（CI_READ_BLOCKED）；② R455 两跑/R456 自身跑（未创建）；③ `PUSH_BLOCKED=network`（ahead=4）；④ 436 Motion floor（无新跑）；⑤ `LOCAL_SCROLL_SESSION_NOT_RUN`（本跑未复现）；⑥ 截断外/OCR 命中在列表无高亮（487）；⑦ 多文件第 2/3 个文件名命中无高亮（488）；⑧ 高亮色在选中底上的对比（489）；⑨ 弱化色选中态（485）；⑩ HTML 的 `<del>`（484）；⑪ HTML 列表缩进/任务弱化/表格体行（482/481/479）；⑫ 设置内容列 1x 平涂；⑬ 设置脚注带 1x；⑭ 主窗口 content 帧 1x；⑮ 高夹具 1x；⑯ 13+ 菜单像素/标题；⑰ 真实拖拽；⑱ Dock 像素；⑲ 源图标最小窗文字 1x；⑳ 2x/extended；㉑ 固定块揭示偏移（455）；㉒ 跨年时间（456）；㉓ 主列表暗档文字盲区（457）；㉔ 真机/多屏（447）；㉕ 真菜单栏、12 实时腿；㉖ `table-lazy-rows`；㉗ HTML 六档字号（460）；㉘ 清除 × 命中区（461）；㉙ 分隔线令牌（462）；㉚ 展开态已加载内容无帧（463）；㉛ 其它自绘控件帮助文本（464）；㉜ HTML 引用块无导引线（465）；㉝ HTML 表格表头无同档（466）；㉞ 100+ 行行号（467）；㉟ HTML 代码块行号（468）；㊱ 行号选中/滚动两态（469）；㊲ 关于页 1x 盲（470）；㊳ M613 机器前提（472）；㊴ 真机 vibrant 暗档（473）；㊵ 长来源截断（474）；㊶ bundle ID 未搜（475）；㊷ 长首行标签省略无帧（476）；㊸ HTML 代码块无语言标签（477）；㊹ HTML `<hr>` 无通栏线（478）；㊺ HTML 表格体行无同一条线（479）；㊻ QuickPick 键盘提示 1x（480）；㊼ HTML 任务列表无弱化（481）；㊽ HTML 列表缩进（482）；㊾ 中心刻度端点标签（483）；㊿ HTML 的 `<del>`（484）；[51] 弱化色选中态（485）；[52] 行内码两侧标点无 padding（486）；[53] 437–489 的未结项仍开。

下一轮（R457）的靶：⓪ 先只读验 remote（仍 `d48bb05`）再一次快进 push（主笔+追记+补记，以 `git log` 现读为准；禁 amend/force）并复核 ahead=0；读 R456 主笔+追记 head 跑、`40653092761 ↔ d48bb05`（R454 head，DEEMPHASIS_CONTRAST）、`40645430259 ↔ 5c925a9`（STRIKE_DIM 已签收）、`40645469967 ↔ c041c8d`（Motion receipt 采样）、`40640660665 ↔ 86044bf`（LIST_HANG_STYLE 已签收）、`40642482086 ↔ e083179`（WEIGHT_CENTER_TICK 具名 NOT_RUN）、`40636558557 ↔ 667d1a2`（TASK_DIM 1x）、`40634880705 ↔ 9743379`（滚动会话采样红原文）的全部失败步骤（成对 run↔commit），重点看 `HISTORY_ROW_MATCH` 两档（来源/标题/负臂：0/1200、2185/0、0/0；暗 0/1560、2660/0、0/0）、`INLINE_CODE_PAD` 两档 98.5/92.5/6.0、`DEEMPHASIS_CONTRAST` 107/255/5.33 与 169/30/7.09、`STRIKE_DIM` 135.4/108.0 与 141.8/174.6、`TASK_DIM` 157.9/114.7、`WEIGHT_CENTER_TICK` 9/5.0/0.0 或具名 NOT_RUN、`LIST_HANG_STYLE` 16.0/16.0/0.0、`QUICKPICK_HINT` 400/519、`TABLE_ROW_LINES` 3/0/108.0/102.0/1.0、`THEMATIC_RULE` 597.0/1.0/1、`CODE_LANGUAGE` 116/126、`HISTORY_SEARCH_SOURCE` 两档 0→1、`PROBE_DOMAIN` 44/20、`TABLE_HEADER` 1.10、`CODE_LINE_NUMBERS` 3/21/100% 与 436；in_progress/0 字节不算绿；`RUNNER_SCROLL_SESSION_FLAKE` 与 `LOCAL_PERF_BUDGET_FLAKE` 必须原样重跑复核（不改门槛）；① 现读 rot=0，按 `HIDDEN_ROT` 查新腐烂；② 继续产品视觉位并落 Sources、换缺陷类别（不要再做列表命中高亮/行内代码底色/弱化色对比度/删除线/权重刻度/列表悬挂缩进/任务项完成态/浮层键盘提示/表格体行分隔/主题分隔线/代码块语言标签/代码块行号/表格表头/引用导引线/侧栏搜索来源/主列表来源行/设置侧栏文字/设置关于页/录制帮助/多文件展开/批量分隔/浮层搜索/图片/HTML/排除名单/行内符号/时间列/分区头/侧栏脚注/详情头部/Dock/菜单栏/横幅/回执/热图/计数/空态/无结果/焦点/悬停/选中/滚动/CTA）；③ 436 只复核新跑 Motion floor，不重猜 `must_judge`。
"""

R456_REPORT_BULLET = u"""- **R456（列表命中高亮位）**：侧栏过滤从 R445 起匹配正文与来源 App 名，但行里此前**一个字都不标** —— 只命中来源的行整行没有线索，正文命中落在两行截断之外时也一样（旧帧黄像素 `0/0`）。新 `HistoryRowMatchHighlight` 复用 `MatchHighlighting.segments`（与过滤同源），标题/文件名标命中片段、来源行**只标 App 名不标时间**，命中片段带 `DetailTypography.highlightColor` 底；空查询/无命中原样。旧/新：`HISTORY_ROW_MATCH light 来源查询 0/0 → 0/1200、正文查询 0/0 → 2185/0、无查询 0/0`、dark 同形（0/1560、2660/0）。**2 张旧帧变化** + **2 张新帧**、0 缺失，基线 **262→264/0/0/0**；逐张看过黄底不压字、不挪版式。单测 7/7；`M1248/M1249/M1250` **3/3**；R444 `M1220` 重钉后 **2/2**；precheck 234/216/607 bad=0、ARM 327/1090、HIDDEN 321/1024 rot=0。⓪：两次 push 探针被拒（`Connection closed ... port 22`）⇒ **`PUSH_BLOCKED=network`（HEAD=`c94a995`、origin/main=`d48bb05`、ahead=4）**；`40653092761 ↔ d48bb05` gh EOF ⇒ **`CI_READ_BLOCKED=network`、NOT-RUN**；436 无新跑 ⇒ `MOTION_FLOOR_NOT_RUN=no-new-run`。全量 **1260/56/0**（403s；滚动 5 红未复现、perf 未红）；捕获 264 帧；build 0 告警；换装 ok/SHA_MATCH=1/383=383（版本 1.4.8）；STORE-SIZE 1108/52/66；电池 683/5。
"""

audit = rd(AUDIT); iter_text = rd(ITER); decisions = rd(DECISIONS)
changelog = rd(CHANGELOG); backlog = rd(BACKLOG); state = rd(STATE); report = rd(REPORT)

if audit.count(AUDIT_TITLE) != 1: raise SystemExit("REFUSED AUDIT %d" % audit.count(AUDIT_TITLE))
if u"第 455 轮（R456" in audit: raise SystemExit("REFUSED AUDIT 已有 R456")
if u"## Round 453 · R456" in iter_text: raise SystemExit("REFUSED ITER 已有 Round 453")
if u"## D-452" in decisions: raise SystemExit("REFUSED DECISIONS 已有 D-452")
if u"侧栏搜索命中在行内高亮" in changelog: raise SystemExit("REFUSED CHANGELOG 已有该标题")
if u"**487." in backlog: raise SystemExit("REFUSED BACKLOG 已有 487")
if state.count(u"## R455 状态") != 1: raise SystemExit("REFUSED STATE %d" % state.count(u"## R455 状态"))
U_CELL_OLD = u"U-31 … U-1702（R455 现读抬到最新一节）"
if report.count(U_CELL_OLD) != 1: raise SystemExit("REFUSED REPORT U %d" % report.count(U_CELL_OLD))
if report.count(u"AGENT_STATE.md` 的 R455 节 ②") != 1: raise SystemExit("REFUSED REPORT pointer")

new_audit = audit.replace(AUDIT_TITLE, AUDIT_SECTION + AUDIT_TITLE, 1)
new_iter = iter_text.rstrip() + "\n\n" + ITER_SECTION + "\n"
new_decisions = decisions.rstrip() + "\n\n" + DECISION_452 + "\n"
marker = u"## [Unreleased]\n"
if changelog.count(marker) != 1: raise SystemExit("REFUSED CHANGELOG")
new_changelog = changelog.replace(marker, marker + "\n" + CHANGELOG_SECTION, 1)
new_backlog = backlog.rstrip() + "\n\n" + BACKLOG_SECTION + "\n"
new_state = state.replace(u"## R455 状态", STATE_SECTION + u"## R455 状态", 1)
new_report = report.replace(U_CELL_OLD, u"U-31 … U-1707（R456 现读抬到最新一节）", 1)
new_report = new_report.replace(u"AGENT_STATE.md` 的 R455 节 ②", u"AGENT_STATE.md` 的 R456 节 ②", 1)
new_report = new_report.rstrip() + "\n\n" + R456_REPORT_BULLET + "\n"

wr(AUDIT, new_audit); wr(ITER, new_iter); wr(DECISIONS, new_decisions)
wr(CHANGELOG, new_changelog); wr(BACKLOG, new_backlog); wr(STATE, new_state); wr(REPORT, new_report)
print("LEDGERS_R456_OK audit=%d iter=%d decisions=%d changelog=%d backlog=%d state=%d report=%d"
      % (len(new_audit), len(new_iter), len(new_decisions), len(new_changelog),
         len(new_backlog), len(new_state), len(new_report)))
