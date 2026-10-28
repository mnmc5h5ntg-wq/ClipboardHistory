#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R447 七本台账一次落盘（只跑一次；先断言所有锚点，全部通过才写）。"""
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


AUDIT_TITLE = u"## 第 445 轮（R446 · 2026-10-28"
AUDIT_SECTION = u"""## 第 446 轮（R447 · 2026-10-28 · U-1658…U-1662）：Markdown 主题分隔线改成通栏 1pt 线（旧 24 个 `─` 字符比正文窄、比行厚、复制带字符 → 新 612.0pt/1.0pt/1 条；2 张新帧、基线 252→254）（产品 3 文件，主题分隔线位）

- **U-1658：⓪ push 与四跑。** 开工只读验 remote 仍为 `36284e1` 后一次快进 push **`36284e1..ecb8e69` success**（两笔：补记 2dd3284 + 预记 ecb8e69），HEAD = origin/main = `ecb8e69`、**ahead=0**。成对读数：① **`40617745753 ↔ fe956e3`** failure **2 步**：`testProbesDoNotSitOnVibrantColumns` 22≠20（R446 已修）+ `testSidebarSearchMatchesTheSourceAppName` dark 行带 1<3（1x 暗档侧栏盲区，2dd3284 已改具名 NOT-RUN）；同跑 `HISTORY_SEARCH_SOURCE light 行数 1/行带 3、dark 1/1`、`HISTORY_ROW_SOURCE 139.0/74.0`、`SETTINGS_ABOUT_ROW 7/7`、`CODE_LINE_NUMBERS 54.0/3/21.0/100%`、`TABLE_HEADER 1.10`；`CODE_LANGUAGE` 不在该提交上（R446 代码更晚）。② **`40620912699 ↔ 36284e1`** failure **1 步**＝同一个 dark 行带 1<3（补记 2dd3284 之后的首跑尚未到）；R446 读数在 runner 1x 上真读到了：`CODE_LANGUAGE light 右区=510..646pt 标签墨=116 无语言臂=0 第二行=0/0 行号带=3/3 正文左=21.0/21.0pt`、`dark 126`（地板 12，过）；`PROBE_DOMAIN 问了 44 条、判成 20 条`（R446 的 -2 条修法在 runner 上成立）；`HISTORY_SEARCH_SOURCE light 1/3、dark 1/1`；`MOTION_FLOOR_FACTS judged=5/5 executed=77 not-run=-`（一个 copy-receipt 采样红，report-only）。③ **`40613782362 ↔ eeccad0`** failure 1 步＝vibrant 22≠20；`HISTORY_SEARCH_SOURCE` 在该提交上 test-not-in-commit ⇒ NOT-RUN。④ **`40605228813 ↔ bdb4737`** failure 2 步（同一 vibrant + 设置关于行 0≠7）。⑤ **`40623613789 ↔ ecb8e69`** 在台账时读为 **in_progress**（单跑 `gh run view` 一次 EOF）⇒ NOT-RUN，R448 ⓪ 必须读。
- **U-1659：① 腐烂与预检（含一次自己的针腐烂）。** `HIDDEN_ARMS 表=312 可判=1005 rot=0`；`NEEDLE_PRECHECK tables=225 covered=207 arms=588 bad=0`、`ARM_TOTAL files=318 arms=1071`。本轮在 `drawBackground` 插入 `drawThematicBreaks` 之后，R446 的 `M1226` 两行锚点（`drawCodeBlockBackgrounds` 紧跟 `drawCodeLanguageTags`）命中 0 —— 先读到 `bad=1`，把针重钉到单行 `drawCodeLanguageTags(in: rect)` 并**复跑 R446 表 2/2 CAUGHT**，precheck 才回到 bad=0（R441 的「针腐烂重钉必复跑旧表」同族）。
- **U-1660：② 主题分隔线改成通栏线。** 缺陷形状：`thematicBreakText = String(repeating: "─", count: 24)` —— 帧上是一条比正文窄（长度由字数决定）、比行高厚的字符线，而且复制渲染结果会带出 24 个 `─`。修法：新 `ThematicBreakRule` 纯策略（`thickness=1`、`secondaryLabelColor`、`rect(containerOriginX:containerWidth:lineTop:lineHeight:)` 通栏居中、`placeholder=" "`）；`MarkdownPresentation.thematicBreakAttribute` 只标范围，属性串里只留一个占位空格（保住行高，复制看不见）；`ChineseSelectableNSTextView.drawThematicBreaks` 在背景层按列宽画 1pt 线。旧/新：`THEMATIC_RULE light 长线=612.0pt 带高=1.0pt 带数=1`、`dark 同形`；复制语义：属性串不含 `─`、可见文字仍是"甲\\n\\n乙"。夹具 `detail-rule`（H1 + 两段 + 一条 `---`）；**2 张新帧、0 张旧帧变化**（现有夹具都没有主题分隔线），基线 **252→254 / 0/0/0**；已看亮/暗两条通栏细线，间距正常。Store 未动（1108 行/52 方法/最长 66）。
- **U-1661：判据、刀与 needle 修正。** 新单测 `ThematicBreakRuleTests` 4 条（复制无 `─`、属性恰好一段且值为占位空格、通栏/1pt/居中、负宽与零行高不越界）+ 帧判据 `testThematicBreaksAreDrawnAsALine`（正文区 y 70..500 找最长连续墨行：≥450pt、带高 ≤4pt、**带数恰 1**）。`M1228`（删绘制调用）⇒ 帧判据 CAUGHT；`M1229`（退回 24 个 `─`）⇒ 复制语义单测 CAUGHT（帧上背景线仍在，所以这条只能由单测抓，表里写明）⇒ **2/2**、RESTORE_CLEAN=yes。M1228 第一次跑报 `命中=False`：刀表 needle 写「通栏线」，实际红文是「通栏**长**线」—— 与 R446 漏「有」同族；修 needle 后复跑 2/2。
- **U-1662：八步与具名 NOT-RUN。** build **0 告警**（`ROUND_WARNING_GATE warnings=0 incremental=0 cold=0 target=build-tests`）；捕获卷 **254 帧**、`COMPARED=254 CHANGED=0 MISSING=0 ADDED=0`；全量 **1223/57/5**（5 个断言全在 `SelectionRevealAnimationTests`）；单跑 `caffeinate -u` **4/4** ⇒ `LOCAL_SCROLL_SESSION_NOT_RUN=full-suite-order`（449）；换装 `INSTALL_RESULT=ok / SHA_MATCH=1 / 381=381`；`STORE-SIZE lines=1108 funcs=52 longest=66`；产品面连续零改动 **1** 轮（as-of 446，`python3 scripts/product_streak.py --streak-for 446`，last=dc477b8）；清账与电池在台账后复跑。**具名 NOT-RUN**：① `40623613789 ↔ ecb8e69`（in_progress）；② eeccad0 的 `HISTORY_SEARCH_SOURCE`（test-not-in-commit）；③ 436 新跑 Motion floor 的 ecb8e69 臂（未完成；36284e1 臂 `judged=5/5 executed=77`）；④ HTML 的 `<hr>` 没有同一条通栏线（478）；⑤ 设置内容列 1x 平涂；⑥ 设置脚注带 1x；⑦ 主窗口 content 帧 1x；⑧ 高夹具 1x；⑨ 13+ 菜单像素/标题；⑩ 真实拖拽；⑪ Dock 像素；⑫ 源图标最小窗文字 1x；⑬ 本地全量 5 条滚动红（449）；⑭ 2x/extended；⑮ 固定块揭示偏移（455）；⑯ 跨年时间（456）；⑰ 主列表暗档文字盲区（457）；⑱ 真机/多屏（447）；⑲ 真菜单栏、12 实时腿；⑳ `table-lazy-rows`；㉑ HTML 六档字号（460）；㉒ 清除 × 命中区（461）；㉓ 分隔线令牌（462）；㉔ 展开态已加载内容无帧（463）；㉕ 其它自绘控件帮助文本（464）；㉖ HTML 引用块无导引线（465）；㉗ HTML 表格表头无同档（466）；㉘ 100+ 行行号（467）；㉙ HTML 代码块行号（468）；㉚ 行号选中/滚动两态（469）；㉛ 关于页 1x 盲（470）；㉜ M613 机器前提（472）；㉝ 真机 vibrant 暗档（473）；㉞ 长来源截断（474）；㉟ bundle ID 未搜（475）；㊱ 长首行标签省略无帧（476）；㊲ HTML 代码块无语言标签（477）；㊳ 437–478 的未结项仍开。

"""

ITER_SECTION = u"""## Round 444 · R447（第 446 轮 · 2026-10-28）：Markdown 主题分隔线改成通栏 1pt 线（旧 24 个 `─` 字符比正文窄、比行厚、复制带字符 → 新 612.0pt/1.0pt/1 条；2 张新帧、基线 252→254）

缺陷是旧 `thematicBreakText` 的 24 个 `─`：长度由字数决定（比正文窄）、墨带是一行字高（>4pt），复制渲染结果会带出这 24 个字符。新 `ThematicBreakRule` 纯策略（1pt、secondaryLabelColor、通栏居中、占位空格）；属性串里只留一个空格保住行高，背景层 `drawThematicBreaks` 按列宽画线。夹具 `detail-rule`（H1 + 两段 + 一条 `---`），读数 `THEMATIC_RULE light 长线=612.0pt 带高=1.0pt 带数=1`、dark 同形；复制语义单测断言无 `─`。2 张新帧、0 旧帧变化，基线 254/0/0/0。M1228/M1229 2/2（M1229 只能由复制语义单测抓，表里写明；M1228 首跑 needle 漏「长」字，修后复跑红得对）。⓪：push 36284e1..ecb8e69 success、ahead=0；40617745753↔fe956e3 failure 2 步（vibrant 22≠20、dark 行带 1<3）；40620912699↔36284e1 failure 1 步（dark 行带；CODE_LANGUAGE 1x 316/381→实读 116/126、无语言臂 0、PROBE_DOMAIN 44/20 过）；ecb8e69 跑 in_progress。全量 1223/57/5（滚动具名）；捕获 254；换装 ok/SHA_MATCH=1/381=381；清账与电池在台账后复跑。

**七维度自评**（恰七行，每格 n/15）：

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | 15/15 | 亮/暗 detail-rule 逐张看过：一条通栏细线、两段间距正常；不是只看数字。 |
| 判据有效性 | 15/15 | 帧上量长线（612pt）、带高（1pt）、带数（1），配复制语义单测（无 `─`、属性一段）；M1228/M1229 2/2。 |
| 假绿防御 | 15/15 | 带数恰 1 防"别的块冒充"；1x 用离背景阈值而非纯色墨；M1229 的帧仍画线，明写只能由单测抓；M1228 needle 漏字照记。 |
| 产品面推进 | 14/15 | 把"装饰线不进剪贴板 + 长度跟列宽"真接进产品；Store 不动；扣 1：HTML `<hr>` 没有同一条线（478）。 |
| 台账一致性 | 15/15 | U-1658…U-1662、D-443、push ecb8e69、254 帧/1223、STORE-SIZE 1108/66 都从命令与测试解析。 |
| 交付诚实性 | 15/15 | ecb8e69 跑 in_progress 具名；M1228/M1226 两次 needle 漏字都照记并复跑；runner 1x 的 116/126 与本地 316/381 分开写。 |
| 可复核性 | 15/15 | 612/1/1、y 窗口 70..500、刀号与 precheck 225/207/588、rot 312/1005、基线 254 都在。 |

均分 = 104/105 ≈ 14.9/15（99）。"""

DECISION_443 = u"""## D-443 主题分隔线由字符改为背景层通栏 1pt 线（R447）

- 背景：`thematicBreakText` 把 `---` 渲染成 24 个 `─`：长度由字数决定、墨带是一行字高、复制渲染结果会带出 24 个字符。
- 决定：新 `ThematicBreakRule` 纯策略（1pt、`secondaryLabelColor`、通栏居中、占位空格）；属性串只留一个占位空格（保住行高），背景层按列宽画线；标签不进文本存储。
- 理由：主题分隔线是装饰不是内容；线长应跟列宽；复制语义可用单测钉住；纯策略不碰 Store（1108/66）。
- 兼容性/迁移：新夹具 `detail-rule`（2 帧，基线 252→254）；现有夹具都没有主题分隔线，0 张旧帧变化。
- 边界：HTML 预览的 `<hr>` 不走这条（478）；线色用 `secondaryLabelColor`，暗档动态。
- 回滚：恢复 `thematicBreakText` 与 `append` 的字符分支、删绘制调用即可；或 `git revert`。
"""

CHANGELOG_SECTION = u"""### Markdown 主题分隔线改为通栏 1pt 线（复制不再带出 24 个 `─`；长线 612.0pt、带高 1.0pt、带数 1；2 张新帧、基线 254）（R447 / 第 446 轮 / Round 444 / U-1658…U-1662 · 产品 3 文件，主题分隔线位）

"""

BACKLOG_SECTION = u"""449 追记（R447 · 仍开）：本机全量仍 5 断言红（3 条用例）、单跑 4/4 绿；未动阈值。

451 追记（R447 · 仍开）：macOS 12 的详情头部阈值本轮未动。

452 追记（R447 · 仍开）：脚注 1x 具名 NOT-RUN 仍生效。

453 追记（R447 · 仍开）：真实系统拖拽会话仍无自动化验收。

454 追记（R447 · 仍开）：菜单具名标记仍未发射。

455 追记（R447 · 仍开）：固定条目滚动到位的独立偏移验收仍缺。

456 追记（R447 · 仍开）：跨年记录仍无年份。

457 追记（R447 · 仍开）：主列表暗档文字仍是另一处。

458 追记（R447 · 仍开）：CI 行首符号像素证人仍缺。

459 追记（R447 · 仍开）：设置内容列/高夹具在 1x 整列平涂。

460 追记（R447 · 仍开）：HTML 六档以上字号仍会后排压到 12pt。

461 追记（R447 · 仍开）：浮层清除 × 命中区 18pt。

462 追记（R447 · 仍开）：批量操作栏分隔线的 0.18 透明度未提令牌。

463 追记（R447 · 仍开）：展开态已加载内容仍无帧。

464 追记（R447 · 仍开）：其它自绘控件仍无同类帮助判据。

465 追记（R447 · 仍开）：HTML 引用块没有导引线。

466 追记（R447 · 仍开）：HTML 表格的表头没有同档字重。

467 追记（R447 · 仍开）：代码块行号的 9pt 档只在纯函数里验。

468 追记（R447 · 仍开）：HTML 代码块没有行号。

469 追记（R447 · 仍开）：代码块行号的选中态/滚动态没有帧。

470 追记（R447 · 仍开）：关于页正文在 runner 1x 是平涂。

471 已结案（R443）。

472 追记（R447 · 仍开）：M613 本机 2x 空名册（机器前提）。

473 追记（R447 · 仍开）：设置侧栏文字的真机 vibrant 暗档没有同屏对照。

474 追记（R447 · 仍开）：长来源 App 名的截断没有帧。

475 追记（R447 · 仍开）：侧栏搜索未匹配来源 App 的 bundle ID。

476 追记（R447 · 仍开）：代码块语言标签在长首行时被省略，没有帧。

477 追记（R447 · 仍开）：HTML 渲染器的代码块没有语言标签。

**478. HTML 预览的 `<hr>` 没有同一条通栏线**（R447 观察）
    现象：R447 把 Markdown 的 `---` 改成背景层通栏 1pt 线；HTML 渲染器（`NSAttributedString` 的 HTML 导入）是另一条路径，`<hr>` 的实际落墨没有帧、也没有同一条几何判据。
    修法：给 HTML 渲染路径拍一帧带 `<hr>` 的样例，量同一条长线/带高；若导入器吞了 `<hr>`，用同一 `ThematicBreakRule` 画。
"""

STATE_SECTION = u"""## R447 状态（2026-10-28 · 本地 · 第 446 轮 / Round 444）：Markdown 主题分隔线改成通栏 1pt 线（旧 24 个 `─` 字符比正文窄、比行厚、复制带字符 → 新 612.0pt/1.0pt/1 条；2 张新帧、基线 252→254）；R446 的 CODE_LANGUAGE/PROBE_DOMAIN 在 runner 1x 上真读到并通过（产品 3 文件，主题分隔线位）

最后更新：2026-10-28（本地 · R447 / 第 446 轮 / Round 444）：`thematicBreakText` 把 `---` 渲染成 24 个 `─` —— 长度由字数决定（比正文窄）、墨带是一行字高、复制渲染结果会带出 24 个字符。新 `ThematicBreakRule` 纯策略（1pt、`secondaryLabelColor`、通栏居中、占位空格 `\" \"`）；`MarkdownPresentation.thematicBreakAttribute` 只标范围，属性串只留一个占位空格（保住行高，复制看不见）；`drawThematicBreaks` 在背景层按列宽画线。读数：`THEMATIC_RULE light 长线=612.0pt 带高=1.0pt 带数=1`、`dark 同形`；复制语义单测断言属性串不含 `─`、属性恰好一段。夹具 `detail-rule`（H1 + 两段 + 一条 `---`）；**2 张新帧、0 张旧帧变化**（现有夹具都没有主题分隔线），基线 **252→254 / 0/0/0**；已看亮/暗通栏细线。`M1228/M1229` **2/2**（M1229 只能由复制语义单测抓，帧上背景线仍在；M1228 首跑 needle 漏「长」字，修后复跑红得对）；新单测 4 条 + 帧判据；预检 **225/207/588 bad=0**、ARM **318/1071**、HIDDEN **312/1005 rot=0**。⓪：一次快进 push **`36284e1..ecb8e69` success**（两笔）、HEAD=origin/main=`ecb8e69`、**ahead=0**；成对读数：`40617745753 ↔ fe956e3` failure **2 步**（vibrant 22≠20、dark 行带 1<3；HISTORY_SEARCH_SOURCE light 1/3、dark 1/1；HISTORY_ROW_SOURCE 139.0/74.0；SETTINGS_ABOUT_ROW 7/7；CODE_LINE_NUMBERS 54.0/3/21.0/100%；TABLE_HEADER 1.10）；`40620912699 ↔ 36284e1` failure **1 步**（同一个 dark 行带；`CODE_LANGUAGE light 右区=510..646pt 标签墨=116 无语言臂=0 第二行=0/0 行号带=3/3 正文左=21.0/21.0pt`、dark 126；`PROBE_DOMAIN 44/20` 过；`MOTION_FLOOR_FACTS judged=5/5 executed=77`）；`40613782362 ↔ eeccad0` failure 1 步（vibrant；HISTORY_SEARCH_SOURCE test-not-in-commit）；`40605228813 ↔ bdb4737` failure 2 步；`40623613789 ↔ ecb8e69` 读时 **in_progress**（单跑 EOF）⇒ NOT-RUN。本地全量 **1223/57/5**（5 断言全在 `SelectionRevealAnimationTests`）；单跑 **4/4** ⇒ `LOCAL_SCROLL_SESSION_NOT_RUN=full-suite-order`（449）。捕获卷 **254 帧**；基线 **254/0/0/0**；build **0 告警**；换装 `ok / SHA_MATCH=1 / 381=381`；`STORE-SIZE lines=1108 funcs=52 longest=66`；产品面连续零改动 **1** 轮（as-of 446，`python3 scripts/product_streak.py --streak-for 446`，last=dc477b8）。清账与电池在台账后复跑。

本轮做了什么：
① ⓪ push 36284e1..ecb8e69 success、ahead=0；四跑成对读数取齐（fe956e3 2 步、36284e1 1 步、eeccad0 1 步、bdb4737 2 步）；ecb8e69 跑 in_progress ⇒ NOT-RUN；R446 的 CODE_LANGUAGE 1x 116/126、PROBE_DOMAIN 44/20 真读到并通过。
② 产品：主题分隔线改成通栏 1pt 线（612/1/1；复制无 `─`；2 张新帧、基线 254）。
③ 判据：M1228/M1229 2/2；新单测 4 条 + 帧判据（长线/带高/带数/复制语义）；precheck 225/207/588；hidden rot 0；M1226 因新行腐烂，已重钉并复跑 R446 表 2/2。
④ 436：36284e1 臂 `judged=5/5 executed=77`（一个 copy-receipt 采样红，report-only）；ecb8e69 臂未完成 ⇒ NOT-RUN，不重猜 must_judge。
⑤ 367：hidden 表 312 / 可判 1005 / rot 0。
⑥ 捕获 254 帧；基线 254/0/0/0；build 0 告警；换装 ok；本地全量 1223/57/5（滚动具名）。

NOT-RUN / 阻塞（分开写）：① `40623613789 ↔ ecb8e69`（in_progress）；② eeccad0 的 `HISTORY_SEARCH_SOURCE`（test-not-in-commit）；③ 436 的 ecb8e69 臂 Motion floor；④ HTML `<hr>` 未覆盖（478）；⑤ 设置内容列 1x 平涂；⑥ 设置脚注带 1x；⑦ 主窗口 content 帧 1x；⑧ 高夹具 1x；⑨ 13+ 菜单像素/标题；⑩ 真实拖拽；⑪ Dock 像素；⑫ 源图标最小窗文字 1x；⑬ 本地全量 5 条滚动红（449）；⑭ 2x/extended；⑮ 固定块揭示偏移（455）；⑯ 跨年时间（456）；⑰ 主列表暗档文字盲区（457）；⑱ 真机/多屏（447）；⑲ 真菜单栏、12 实时腿；⑳ `table-lazy-rows`；㉑ HTML 六档字号（460）；㉒ 清除 × 命中区（461）；㉓ 分隔线令牌（462）；㉔ 展开态已加载内容无帧（463）；㉕ 其它自绘控件帮助文本（464）；㉖ HTML 引用块无导引线（465）；㉗ HTML 表格表头无同档（466）；㉘ 100+ 行行号（467）；㉙ HTML 代码块行号（468）；㉚ 行号选中/滚动两态（469）；㉛ 关于页 1x 盲（470）；㉜ M613 机器前提（472）；㉝ 真机 vibrant 暗档（473）；㉞ 长来源截断（474）；㉟ bundle ID 未搜（475）；㊱ 长首行标签省略无帧（476）；㊲ HTML 代码块无语言标签（477）；㊳ 437–478 的未结项仍开。

下一轮（R448）的靶：⓪ 先 `git push origin main`（禁 amend/force）并复核 ahead=0；读 R447 主笔+追记 head 跑、`40623613789 ↔ ecb8e69`（R447 开工时的 in_progress）与 `40620912699 ↔ 36284e1`、`40617745753 ↔ fe956e3`、`40613782362 ↔ eeccad0` 的全部失败步骤（成对 run↔commit），重点看 `THEMATIC_RULE` 两档 612.0/1.0/1、`CODE_LANGUAGE` 两档 116/126/0/0、`HISTORY_SEARCH_SOURCE` 两档 0→1、亮档行带 3 / 暗档具名 NOT-RUN、`HISTORY_ROW_SOURCE` 139.0/74.0、`SETTINGS_ABOUT_ROW` 7/7、`PROBE_DOMAIN` 44/20、`CODE_LINE_NUMBERS` 3/21/100%、`TABLE_HEADER` 1.10/1.11 与 436；in_progress/0 字节不算绿；① 现读 rot=0，按 `HIDDEN_ROT` 查新腐烂；② 继续产品视觉位并落 Sources、换缺陷类别（不要再做主题分隔线/代码块语言标签/代码块行号/表格表头/引用导引线/侧栏搜索来源/主列表来源行/设置侧栏文字/设置关于页/录制帮助/多文件展开/批量分隔/浮层搜索/图片/HTML/排除名单/行内符号/时间列/分区头/侧栏脚注/详情头部/Dock/菜单栏/横幅/回执/热图/计数/空态/无结果/焦点/悬停/选中/滚动/CTA）；③ 436 只复核新跑 Motion floor，不重猜 `must_judge`。
"""

R447_REPORT_BULLET = u"""- **R447（主题分隔线位）**：`thematicBreakText` 把 `---` 渲染成 24 个 `─` —— 长度由字数决定（比正文窄）、墨带是一行字高、复制渲染结果会带出 24 个字符。新 `ThematicBreakRule` 纯策略（1pt、`secondaryLabelColor`、通栏居中、占位空格）；属性串只留一个占位空格（保住行高、复制看不见），`drawThematicBreaks` 在背景层按列宽画线。夹具 `detail-rule`（H1 + 两段 + 一条 `---`）：`THEMATIC_RULE light 长线=612.0pt 带高=1.0pt 带数=1`、dark 同形；复制语义单测断言属性串不含 `─`、属性恰好一段。**2 张新帧、0 张旧帧变化**，基线 **252→254 / 0/0/0**；已看亮/暗通栏细线。`M1228/M1229` **2/2**（M1229 只能由复制语义单测抓，表里写明；M1228 首跑 needle 漏「长」字，修后复跑红得对）；新单测 4 条 + 帧判据；预检 225/207/588 bad=0、ARM 318/1071、HIDDEN 312/1005 rot=0。⓪：一次快进 push **`36284e1..ecb8e69` success**、HEAD=origin/main=`ecb8e69`、ahead=0；成对读数：`40617745753 ↔ fe956e3` failure 2 步（vibrant 22≠20、dark 行带 1<3；HISTORY_SEARCH_SOURCE light 1/3、dark 1/1；HISTORY_ROW_SOURCE 139.0/74.0；SETTINGS_ABOUT_ROW 7/7；CODE_LINE_NUMBERS 54.0/3/21.0/100%；TABLE_HEADER 1.10）、`40620912699 ↔ 36284e1` failure 1 步（同一个 dark 行带；CODE_LANGUAGE light 116/dark 126、无语言臂 0、PROBE_DOMAIN 44/20 过；MOTION_FLOOR_FACTS judged=5/5 executed=77）、`40613782362 ↔ eeccad0` failure 1 步（vibrant；HISTORY_SEARCH_SOURCE test-not-in-commit）、`40605228813 ↔ bdb4737` failure 2 步；`40623613789 ↔ ecb8e69` 读时 in_progress ⇒ NOT-RUN。全量 **1223/57/5**（滚动具名），单跑 4/4 ⇒ `LOCAL_SCROLL_SESSION_NOT_RUN=full-suite-order`（449）。捕获 254 帧；build 0 告警；换装 ok/SHA_MATCH=1/381=381；STORE-SIZE 1108/52/66；清账与电池在台账后复跑。
"""

audit = rd(AUDIT); iter_text = rd(ITER); decisions = rd(DECISIONS)
changelog = rd(CHANGELOG); backlog = rd(BACKLOG); state = rd(STATE); report = rd(REPORT)

if audit.count(AUDIT_TITLE) != 1: raise SystemExit("REFUSED AUDIT %d" % audit.count(AUDIT_TITLE))
if u"第 446 轮（R447" in audit: raise SystemExit("REFUSED AUDIT 已有 R447")
if u"## Round 444 · R447" in iter_text: raise SystemExit("REFUSED ITER 已有 Round 444")
if u"## D-443" in decisions: raise SystemExit("REFUSED DECISIONS 已有 D-443")
if u"Markdown 主题分隔线改为通栏 1pt 线" in changelog: raise SystemExit("REFUSED CHANGELOG 已有该标题")
if u"**478." in backlog: raise SystemExit("REFUSED BACKLOG 已有 478")
if state.count(u"## R446 状态") != 1: raise SystemExit("REFUSED STATE %d" % state.count(u"## R446 状态"))
U_CELL_OLD = u"U-31 … U-1657（R446 现读抬到最新一节）"
if report.count(U_CELL_OLD) != 1: raise SystemExit("REFUSED REPORT U %d" % report.count(U_CELL_OLD))
if report.count(u"AGENT_STATE.md` 的 R446 节 ②") != 1: raise SystemExit("REFUSED REPORT pointer")

new_audit = audit.replace(AUDIT_TITLE, AUDIT_SECTION + AUDIT_TITLE, 1)
new_iter = iter_text.rstrip() + "\n\n" + ITER_SECTION + "\n"
new_decisions = decisions.rstrip() + "\n\n" + DECISION_443 + "\n"
marker = u"## [Unreleased]\n"
if changelog.count(marker) != 1: raise SystemExit("REFUSED CHANGELOG")
new_changelog = changelog.replace(marker, marker + "\n" + CHANGELOG_SECTION, 1)
new_backlog = backlog.rstrip() + "\n\n" + BACKLOG_SECTION + "\n"
new_state = state.replace(u"## R446 状态", STATE_SECTION + u"## R446 状态", 1)
new_report = report.replace(U_CELL_OLD, u"U-31 … U-1662（R447 现读抬到最新一节）", 1)
new_report = new_report.replace(u"AGENT_STATE.md` 的 R446 节 ②", u"AGENT_STATE.md` 的 R447 节 ②", 1)
new_report = new_report.rstrip() + "\n\n" + R447_REPORT_BULLET + "\n"

wr(AUDIT, new_audit); wr(ITER, new_iter); wr(DECISIONS, new_decisions)
wr(CHANGELOG, new_changelog); wr(BACKLOG, new_backlog); wr(STATE, new_state); wr(REPORT, new_report)
print("LEDGERS_R447_OK audit=%d iter=%d decisions=%d changelog=%d backlog=%d state=%d report=%d"
      % (len(new_audit), len(new_iter), len(new_decisions), len(new_changelog),
         len(new_backlog), len(new_state), len(new_report)))
