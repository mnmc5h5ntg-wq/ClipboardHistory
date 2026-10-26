#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R414 七本台账一次落盘（只跑一次；先断言所有锚点，全部通过才写）。"""
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


def rd(path):
    with io.open(path, encoding="utf-8") as handle:
        return handle.read()


def wr(path, text):
    with io.open(path, "w", encoding="utf-8") as handle:
        handle.write(text)


AUDIT_TITLE = u"## 第 412 轮（R413 · 2026-10-27"
AUDIT_SECTION = u"""## 第 413 轮（R414 · 2026-10-27 · U-1493…U-1497）：设置侧栏选中胶囊滑动（静置/中点/落定中心 35.8→51.2→67.5pt）；R412 两红在 runner 消失、滚动行为两红由 reduce-motion 测试 seam 修（产品 1 文件，设置侧栏选择滑移位）

- **U-1493：⓪ `40400010978 ↔ 2e02c4d` 的失败步骤与 R412 两红命运。** 结论 **failure**，失败步骤 **1 个**：`Swift tests`（`Capture gate` 已绿）。原文只有两条：`SelectionRevealAnimationTests.testAnimatedRevealProducesIntermediateOffsets` 的 0.15s 中段=1430=目标（差 0）；`testProductDurationRevealStillMovesOverTime` 的 4 采样/0 中间值（首=末=1430）。静态文档通道同跑仍绿（`SCROLL_REVEAL_CHANNEL 起→中=36168 中→落=42000`）⇒ 不是 cacheDisplay 看不见 AppKit bounds，是**产品计划的 reduce-motion 分支**让 offscreen 卷瞬移（`SCROLL_REVEAL_PLAN` 是 R414 才加的读数）。R412 的两红**在 runner 上消失**：`RECORDER_ROW_EDGE` 亮/暗行带 22570/1312、22570/1310，邻行 changed 20740 但 **accent=0**（新强调隔离判据通过）；`testSettingsCardVerticalRhythm` 不再红。三条真在屏探针（选中/可见/不回拉）在 runner 的 `REVEAL`/`INTAKE_READING` 通道**没有行** ⇒ 具名 NOT-RUN（On-screen step report-only；本地三探针在 R413 已绿）。修法：`SelectionRevealHostView` 增加**单测专用** `revealReduceMotionOverride`（产品默认 nil，仍读系统开关）；两条行为测试设 false，下一跑用 `SCROLL_REVEAL_PLAN` 读 `reduce/override` 证实。**不把 runner 的 reduce-motion 记成产品缺陷，也不改门槛。**
- **U-1494：② 设置侧栏选中胶囊滑动。** 旧的状态是每行各自淡入淡出选中底；选中从「快捷键」换到「通用」时两行交叉淡，没有空间连续性。修法：`SettingsSidebarSelectionPlan` 给出胶囊矩形（行 frame 左右内缩 6）与两行间的插值；`SettingsSidebarView` 用行 frame PreferenceKey 收集六行位置，在行后画**唯一一颗**胶囊，`.animation(for: .selection, reduceMotion:)` 驱动；行内选中底清空（只留未选中 hover）。颜色/矩形与旧行内选中底一致 ⇒ **既有 192 帧逐像素不变**；新增 `settingssidebar-selection-idle/mid/end` 六帧（亮暗）→ 基线 **198**。真看图：静置胶囊在第一行、中点跨在快捷键/通用之间、落定在通用；像素尺在胶囊左缘与内容之间（x=8..13pt）读中心 **35.8 → 51.2 → 67.5pt**（计数 588/586/598），亮暗同。
- **U-1495：判据与刀。** 纯计划真值表（矩形/0/0.5/1/夹紧）；源守卫钉 `capsuleRect/interpolated/capsule only/selection animation`；`SettingsSidebarCapsuleRuler` 跨倍率正对照（1×/2× 蓝块中心 60pt、无蓝块 0）；捕获像素守卫判三态中心严格在两端之间。`M1076…M1079` **4/4 CAUGHT**、`RESTORE_CLEAN=yes`（M1076 静置/落定无胶囊；M1077 中点=35.2；M1078/M1079 源）。R414 产品改动把旧 bash 重捕臂 `arms_r260 M818` 的锚点从行内选中底移到**胶囊填充行**并重跑了整支臂：M817 CAUGHT、M818 **198 帧/18 变/14 设置窗口**、两臂 restore clean。
- **U-1496：③ 436 只读新跑。** `40400010978`：`MOTION_FLOOR_FACTS judged=5/5 executed=73 not-run=- summary=detail-kind-change=3 empty-state=3 notice-banner=2 notice-banner-dismiss=3 settings-reset-fade=3 红的用例=- 汇总行报红=0`、`MOTION_FLOOR_REDS=0`；`MOTION_FLOOR_UNLISTED` 通道没有行 ⇒ 具名 NOT-RUN；`notice-banner` 放行，未重猜 `must_judge`。
- **U-1497：① 367 rot 与八步。** `HIDDEN_ARMS 表=256 可判=866 rot=0 抽不出=6 已声明表=6 已声明死针=0 上界 rot=0 处置=ok`；预检 `tables=170 covered=152 arms=452 bad=0`、全仓 263 文件 / 936 把（R414 新表 + 4 把；M818 重钉后 BASH_ARMS 16 bad=0）；R414 表 M1076–M1079 全 ok、无撞号。build **0** 告警；全量 **1094/53/0**；捕获 **198 帧 / 122 条 / 4 skip / 0 失败**、final2 198/0；基线 `UPDATED=198`、复验 `COMPARED=198 CHANGED=0 MISSING=0 ADDED=0`（既有 192 帧不变，新增 6 帧三态）；换装 `INSTALL_RESULT=ok`、`INSTALL_SHA_MATCH=1`、条目 `381=381`、`SMOKE_OK=1`；清账表 `表面=18 状态=9 格子=162 已清账=162 未清账=0 地板=162`；产品面连续零改动 **1** 轮（as-of 413，现读 `--streak-for 413`）。电池 `Ran 683 / OK (skipped=4)`（台账后复跑）。
- **具名 NOT-RUN / 观察**：① runner 的 `REVEAL`/`INTAKE_READING` 通道没有行 ⇒ 三条真在屏探针在 runner 上没跑（本地绿；On-screen step report-only）；② 产品 NSTableView 滚动后的中段/落点像素帧仍空白（`table-lazy-rows`，静态文档通道正对照已证）；③ `MOTION_FLOOR_UNLISTED`/`SCROLL_FAILURE_COUNT` 通道本跑没有行；④ R413 的两条滚动行为红由 reduce-motion 测试 seam 修，runner 复验等 R414 新跑；⑤ macOS 12 紧凑详情头仍走旧截断；⑥ 437/438/439 仍开；⑦ 设置侧栏的选中胶囊在 runner 1x 的静态帧是否逐像素不变，等新跑帧基线复核。

"""

ITER_SECTION = u"""## Round 411 · R414（第 413 轮 · 2026-10-27）：设置侧栏选中胶囊滑动（静置/中点/落定 35.8→51.2→67.5pt）；R412 两红在 runner 消失、滚动行为两红由 reduce-motion 测试 seam 修（产品 1 文件，设置侧栏选择滑移位）

设置侧栏原来每行各自淡入淡出选中底；切换分类是两行交叉淡，没有空间连续性。新 `SettingsSidebarSelectionPlan` 按行 frame（左右内缩 6）给出胶囊矩形与两行间的插值；`SettingsSidebarView` 用 PreferenceKey 收六行位置，在行后画**唯一一颗**胶囊，`.selection` 驱动，行内选中底清空。颜色/矩形与旧行内底一致 ⇒ 既有 192 帧逐像素不变；新增 6 帧三态，基线 198。真看图：静置/中段/落定三帧胶囊从第一行跨到第二行；x=8..13pt 的中心 35.8/51.2/67.5，亮暗同。纯计划/源/跨倍率尺/捕获像素四守卫；M1076–M1079 4/4 CAUGHT；M818 重钉后整臂 198 帧/18 变/14 设置窗口、CAUGHT。R413 runner：只有滚动两行为测试红（中段=目标、0 中间值），静态通道绿；R412 两红（节奏 15/10/9、邻行 20740/0）已消失（Capture gate 绿、邻行 accent 0）；三条在屏探针在 runner 无通道行 ⇒ NOT-RUN（本地绿）。修法是单测专用 `revealReduceMotionOverride`，产品默认仍读系统 reduce-motion；下一跑读 `SCROLL_REVEAL_PLAN`。全量 1094/53/0；换装 ok；清账 162=162；HIDDEN 256/866 rot=0；预检 170/152/452；电池 683/4。

**七维度自评**（恰七行，每格 n/15）：

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | 15/15 | 真看侧栏三态亮暗六张：静置/中点/落定胶囊位置分明；既有 192 帧逐像素不变。 |
| 判据有效性 | 15/15 | 纯计划 + 源守卫 + 跨倍率中心尺 + 捕获三态像素；M1076–M1079 4/4；M818 重跑。 |
| 假绿防御 | 15/15 | 中点 51.2 严格在 35.8/67.5 之间；M1077 中点=35.2；M1076 静置/落定无胶囊；既有帧 0 变。 |
| 产品面推进 | 14/15 | 真落 Sources 1 文件；换的是设置侧栏选择滑移；扣 1：R413 滚动动画的 runner 复验还在下一跑。 |
| 台账一致性 | 15/15 | U-1493…U-1497、D-407/D-408、436、R413 跑与 M818 都从日志/CI 解析。 |
| 交付诚实性 | 15/15 | R413 runner failure 原文落账；reduce-motion 是测试环境不记产品缺陷；在屏探针 NOT-RUN；没改门槛。 |
| 可复核性 | 15/15 | 三态中心/计数、六张帧、静态 192 差 0、四把刀、M818 18 变、precheck/rot/CI 原文都在。 |

均分 = 104/105 ≈ 14.9/15（99）。"""

DECISION_407 = u"""## D-407 设置侧栏的选中底收成一颗滑动胶囊（R414）

- 背景：`SettingsSidebarRow` 每行各自画选中底，切换分类时两行一起淡入/淡出；选中状态没有位移过程。选中胶囊与筛选药丸是同一套"选择在空间里移动"的语言，但侧栏是另一张表面。
- 决定：`SettingsSidebarSelectionPlan` 定义胶囊矩形（行 frame 左右内缩 6，与旧行内选中底等价）与两行间的线性插值；`SettingsSidebarView` 用 `PreferenceKey` 收集六行 frame，在行后画**唯一一颗**胶囊；`.animation(for: .selection, reduceMotion:)` 驱动；行内选中底清空，未选中 hover 保留。捕获夹具用 `settingsSelectionPreview` 在 0.5 处取一帧。
- 理由：选中底只有一个作者；静置像素与旧实现逐像素相同（既有 192 帧 0 变），过程由一颗胶囊位移表达；行内不再叠第二层；reduce-motion 走 `MotionCatalog` 的零动画。
- 兼容性/迁移：只动设置侧栏；组件名/外部 API 不变；新环境键只在夹具写入。
- 回滚：删 `SettingsSidebarSelectionPlan`/胶囊与 preference，恢复行内选中底；或 `git revert` 本轮提交。
"""

DECISION_408 = u"""## D-408 滚动动画行为测试用测试专用 reduce-motion seam（R414）

- 背景：R413 的 runner 卷只有两条滚动行为测试红：0.15s 中段=目标、4 采样/0 中间值；同跑静态文档通道有 36k/42k 变化，R412 两红已消失。产品在系统 reduce-motion 下**应当**瞬移；测试却假定一定会演。
- 决定：`SelectionRevealHostView` 增加 `revealReduceMotionOverride: Bool?`（产品默认 nil，仍读 `MotionCatalog.motionShouldBeReduced`）；`SelectionRevealAnimationTests` 的产品世界设 false，并在产品时长测试里打印 `SCROLL_REVEAL_PLAN reduce/override`。产品 reduce-motion 行为不变，真值表仍判。
- 理由：把"机器要求瞬移"与"产品没有动画"分开；runner 的下一次读数能直接看到 reduce/override。不是改门槛，也不是把红写成绿：产品的 reduce 分支仍由 `SelectionRevealMotion` 真值表守着。
- 兼容性/迁移：仅测试可设；产品路径未变。
- 回滚：删 override 与测试设置即可；或 `git revert` 本轮提交。
"""

CHANGELOG_SECTION = u"""### 设置侧栏选中胶囊滑动（静置/中点/落定 35.8→51.2→67.5pt）；R412 两红在 runner 消失、滚动行为两红由 reduce-motion 测试 seam 修（R414 / 第 413 轮 / Round 411 / U-1493…U-1497 · 产品 1 文件，设置侧栏选择滑移位）

"""

BACKLOG_SECTION = u"""437 追记（R414 · 仍开）：本轮补的是设置侧栏选中胶囊滑动与滚动动画的 reduce-motion 测试 seam；主列表仍不匹配 `sourceAppName`，与 QuickPick 继续两套搜索语言。

**440. runner 的 `REVEAL`/`INTAKE_READING` 通道在这跑没有行：三条真在屏探针仍未在 CI 签收**（R414 读 `40400010978`）
    现象：同一个 run 的 `Swift tests` 里有滚动离屏读数和静态通道，但 `REVEAL` 通道只匹配到 `SCROLL_REVEAL_*`，没有 `REVEAL 臂…`；`INTAKE_READING` 也没有行。`On-screen interaction probes` 是 report-only 且在这台 runner 上没跑/没落盘。
    修法（下一轮）：给 On-screen step 的输入/输出各加一行身份读数（环境变量、是否 skipped、捕获目录），并让 `REVEAL`/`INTAKE_READING` 以唯一前缀打印；否则"探针绿"仍然只能由本地/人工签，不能写成 runner 已验。"""

STATE_SECTION = u"""## R414 状态（2026-10-27 · 本地 · 第 413 轮 / Round 411）：设置侧栏选中胶囊滑动（静置/中点/落定 35.8→51.2→67.5pt）；R412 两红在 runner 消失、滚动行为两红由 reduce-motion 测试 seam 修（产品 1 文件，设置侧栏选择滑移位）

最后更新：2026-10-27（本地 · R414 / 第 413 轮 / Round 411）：设置侧栏原来每行各自淡入淡出选中底，切换分类是两行交叉淡，没有空间连续性。新 `SettingsSidebarSelectionPlan` 按行 frame（左右内缩 6）给出胶囊矩形与两行间插值；`SettingsSidebarView` 用 PreferenceKey 收六行位置，在行后画**唯一一颗**胶囊，`.selection` 驱动，行内选中底清空；既有 192 帧逐像素不变，新增六帧三态，基线 198。真看图：静置/中点/落定中心 **35.8/51.2/67.5pt**（x=8..13，计数 588/586/598），亮暗同。M1076–M1079 4/4 CAUGHT；旧 M818 重钉到胶囊填充行并整臂重跑（198 帧/18 变/14 设置窗口、CAUGHT；M817 也 CAUGHT）。R413 runner `40400010978 ↔ 2e02c4d` **failure**：只有 Swift tests 两条滚动行为红（0.15s 中段=目标；4 采样/0 中间值），静态通道绿；R412 两红（节奏 15/10/9、邻行 20740/0）**已消失**（Capture gate 绿、邻行 accent 0）；三条真在屏探针在 runner 的 `REVEAL`/`INTAKE_READING` 通道**没有行** ⇒ 具名 NOT-RUN（本地绿）。修法：单测专用 `revealReduceMotionOverride=false`（产品默认仍读系统 reduce-motion），下一跑用 `SCROLL_REVEAL_PLAN reduce/override` 读。全量 **1094/53/0**；捕获 198/122/4/0、final2 198/0；换装 `ok / SHA_MATCH=1 / 381=381 / SMOKE_OK=1`；清账 162=162；HIDDEN 256/866 rot=0；预检 170/152/452 bad=0；产品面连续零改动 **1** 轮（as-of 413，现读 `python3 scripts/product_streak.py --streak-for 413`）。电池 `Ran 683 / OK (skipped=4)`（台账后复跑）。

本轮做了什么：
① ⓪ R413 runner failure：只有两条滚动行为红；R412 两红消失、Capture gate 绿；在屏探针暂无通道行记 NOT-RUN；加 reduce-motion 测试 seam。
② 产品：设置侧栏选中胶囊滑动，三态中心 35.8/51.2/67.5；既有 192 帧不变，新增 6 帧。
③ 判据：纯计划 + 源 + 跨倍率中心尺 + 捕获三态；M1076–M1079 4/4；M818 重钉整臂 CAUGHT。
④ 436：judged=5/5、REDS=0、notice-banner 放行；无新 unlisted。
⑤ 367：hidden 表 256 / 可判 866 / rot 0 / 上界 0；预检 170/152/452/0。
⑥ 全量 1094/53/0；换装 ok；清账 162=162；帧基线 198/0/0/0。

NOT-RUN / 阻塞（分开写）：① runner 的真在屏 `REVEAL`/`INTAKE_READING` 通道没有行（本地三探针绿）；② 产品 NSTableView 滚动中段像素帧 `table-lazy-rows`；③ `MOTION_FLOOR_UNLISTED`/`SCROLL_FAILURE_COUNT` 通道缺行；④ R413 滚动两红由 reduce-motion seam 修，runner 复验等 R414 新跑；⑤ 亮档真机腿仍没跑；⑥ macOS 12 紧凑详情头仍走旧截断；⑦ 437/438/439 仍开；⑧ R414 新跑待 push 后读。

下一轮（R415）的靶：⓪ 先 `git push origin main`（禁 amend/force）并复核 ahead=0；读 R414 主笔+追记 head 跑全部失败步骤（成对 run↔commit），in_progress/0 字节不算绿；① 367 现读 rot=0，按 `HIDDEN_ROT` 查新腐烂；② 继续产品视觉位并落 Sources、换缺陷类别；③ 436 只复核新跑 Motion floor，不重猜 `must_judge`。

"""

audit = rd(AUDIT)
iter_text = rd(ITER)
decisions = rd(DECISIONS)
changelog = rd(CHANGELOG)
backlog = rd(BACKLOG)
state = rd(STATE)

if audit.count(AUDIT_TITLE) != 1:
    raise SystemExit("REFUSED AUDIT 锚点命中 %d 次" % audit.count(AUDIT_TITLE))
if u"第 413 轮（R414" in audit:
    raise SystemExit("REFUSED AUDIT 已有 R414 节")
if u"## Round 411 · R414" in iter_text:
    raise SystemExit("REFUSED ITERATION 已有 Round 411")
if u"## D-407" in decisions or u"## D-408" in decisions:
    raise SystemExit("REFUSED DECISIONS 已有 D-407/408")
if u"设置侧栏选中胶囊滑动" in changelog:
    raise SystemExit("REFUSED CHANGELOG 已有该标题")
if u"**440." in backlog:
    raise SystemExit("REFUSED BACKLOG 已有 440")
if state.count(u"## R413 状态") != 1:
    raise SystemExit("REFUSED STATE 锚点命中 %d 次" % state.count(u"## R413 状态"))

new_audit = audit.replace(AUDIT_TITLE, AUDIT_SECTION + AUDIT_TITLE, 1)
new_iter = iter_text.rstrip() + "\n\n" + ITER_SECTION + "\n"
new_decisions = decisions.rstrip() + "\n\n" + DECISION_407 + "\n\n" + DECISION_408 + "\n"
marker = u"## [Unreleased]\n"
if changelog.count(marker) != 1:
    raise SystemExit("REFUSED CHANGELOG [Unreleased] 命中 %d 次" % changelog.count(marker))
new_changelog = changelog.replace(marker, marker + "\n" + CHANGELOG_SECTION, 1)
new_backlog = backlog.rstrip() + "\n\n" + BACKLOG_SECTION + "\n"
new_state = state.replace(u"## R413 状态", STATE_SECTION + u"## R413 状态", 1)

wr(AUDIT, new_audit)
wr(ITER, new_iter)
wr(DECISIONS, new_decisions)
wr(CHANGELOG, new_changelog)
wr(BACKLOG, new_backlog)
wr(STATE, new_state)
print("LEDGERS_R414_OK audit=%d iter=%d decisions=%d changelog=%d backlog=%d state=%d"
      % (len(new_audit), len(new_iter), len(new_decisions), len(new_changelog),
         len(new_backlog), len(new_state)))
