#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R413 七本台账一次落盘（只跑一次；先断言所有锚点，全部通过才写）。"""
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


AUDIT_TITLE = u"## 第 411 轮（R412 · 2026-10-27"
AUDIT_SECTION = u"""## 第 412 轮（R413 · 2026-10-27 · U-1488…U-1492）：跨视口长跳补滚动到位动画（0→203→1438；旧瞬移 0/15 中间值）；R412 录制描边 runner 红修复（纵向 0 + 强调隔离）（产品 1 文件，滚动到位位）

- **U-1488：⓪ `40385615419 ↔ 130be12` 的失败步骤与 R412 行描边命运。** 结论 **failure**，失败步骤 **2 个**：`Swift tests` + `Capture gate`。原文：① `testSettingsCardVerticalRhythmIsOneNumber` 的 `settings-shortcuts-recording light` 读 **15/10/9**，最大留白 15.0、最小 9.0（差 **6.0 > 4.5**）；② `testCaptureKeyViews` 邻行 `changed=20740`、`accent=0`（亮/暗同）；录制行带 **22570/1321**、**22570/1319**。⇒ 两件事：描边纵向 −2 侵入行距（节奏红）；runner 1x 的 idle/recording 整页有 **1 级底色差**（邻行 100% 变化但强调 0），不是描边泄漏。修法：描边**纵向不外扩**（0）；邻行隔离从“任意变化”改判**强调色**，并补 0.82 灰底色 vs 强调泄漏的真值表。本地最终捕获 `RECORDER_ROW_EDGE` 亮 **4016/3958**、暗 **4016/3956**，邻行 **0/0**；`settings-shortcuts-recording` 亮暗 2 帧变化，基线 192/0。**runner 侧的 15/10/9 与 20740/0 要等下一跑复验；本轮不宣称已绿。** ⓪ 另：R411 hover 夹具 0.3s 落定经第二次同码捕获（`/tmp/r413_settle_b`，122/4/0）验证，`sidebar-row-hover` 亮/暗与 `settings-shortcuts-recording` 亮/暗四张 hash 与已提交基线**逐字节相同**，218/209 相位差不再现。`QUICKPICK_EMPTY_FIELD 30/1`、`RECORDER_ROW_EDGE_SCALE 1x 276 / 2x 1104`、fast row 4807/4767 均仍绿。
- **U-1489：② 跨视口长跳的滚动到位动画。** 旧的 `SelectedRowRevealer` 在延后一回合后一次 `scrollRowToVisible` 瞬移；方向键近步也走同一条。新 `SelectionRevealMotion.plan`：距离 > 一屏且非减弱动态才 animated，时长 `.slider` 0.20；instant 与 animated 共用**系统最小滚动目标**。关键是在屏探针抓到的两版自伤：① 纯 `clip.animator().setBoundsOrigin` 滚到位了（origin 1977）但 List 选中集仍是 **[]** —— 纯 bounds 动画不替 List 物化行；② 只把 `scrollRowToVisible` 放前面、目标在物化前读，会从 2191 跳到 3211。最终实现：先 `table.scrollRowToVisible(row)`、layout、再滚一次读**物化后的系统目标**，回起点演到该目标，完成时 `setBoundsOrigin` + reflect + 再 `scrollRowToVisible(row)` 物化落点。真在屏（`CLIPBOARD_HISTORY_UI_INTERACTION=1`）：臂2 选中集合 **[60]**、该行在可视区 **true**、origin **3211**、臂3 用户滚开后收藏/撤收藏仍 **0.0**；drift 探针 origin 3143→0（删顶部一条不拉回）；intake 新记录 0→159、选中 [4]、在屏 true。离屏逐时：产品时长 **17 采样 / 7 中间值**、首 68、末 **1438**、目标 1438、时长 0.20；慢放 **0→203→1438**。像素通道：静态文档 start/mid/end 变化 **111729/148800**；产品 NSTableView 滚动后新物化行不被 `cacheDisplay` 画出（中段/落点帧空白）⇒ 产品像素中段**具名 NOT-RUN `table-lazy-rows`**，产品运动由 origin 逐时读数作证。
- **U-1490：判据与刀。** 纯函数 `SelectionRevealMotion.plan` 真值表（近步/跨屏/减弱/视口 0/严格门槛）；源守卫钉 `scrollRowToVisible → layout → 再滚 → 回起点 → animator.setBoundsOrigin → duration`；离屏真 NSScrollView 行为（产品时长 + 慢放 + 近步）；静态文档像素通道正对照。`M1070…M1075` **5/5 CAUGHT**、`RESTORE_CLEAN=yes`：M1070 计划 instant ⇒ **15 采样 / 0 中间值**；M1073 时长归零 / M1074 不回起点 ⇒ 中段=1438；M1075 删掉两次系统滚动 ⇒ 首/末 **0/0**、目标 1438。R412 的 `M1065…M1069` 在描边纵向 0 后重跑仍 **5/5 CAUGHT**（M1067 0/0；M1068 变化 4819、强调 0）。
- **U-1491：③ 436 只读新跑。** `MOTION_FLOOR_FACTS judged=5/5 executed=73 not-run=- summary=detail-kind-change=3 empty-state=3 notice-banner=2 notice-banner-dismiss=3 settings-reset-fade=3 红的用例=- 汇总行报红=0`、`MOTION_FLOOR_REDS=0`；`MOTION_FLOOR_UNLISTED` 通道没有一行 ⇒ 记具名 NOT-RUN；`Release script tests` 的 `UNLISTED … ok` 在；`notice-banner` 放行，未重猜 `must_judge`。
- **U-1492：① 367 rot 与八步。** `HIDDEN_ARMS 表=256 可判=866 rot=0 抽不出=6 已声明表=6 已声明死针=0 上界 rot=0 处置=ok`；预检 `tables=169 covered=151 arms=448 bad=0`、全仓 262 文件 / 932 把；R413 表 M1070–M1075 全 ok、无撞号。build **0** 告警；全量 **1091/53/0**（首跑 1 条 `PerfBudget` 瞬态 262.9/269.86ms >250；单跑 148.02ms，复跑 0；阈值未改）；捕获 final3 **122/4/0**、final4 **192/0**；基线 `UPDATED=192`、复验 `COMPARED=192 CHANGED=0 MISSING=0 ADDED=0`（相对 R412 基线只改 recording 亮暗 2 帧）；换装 `INSTALL_RESULT=ok`、`INSTALL_SHA_MATCH=1`、条目 `381=381`、`SMOKE_OK=1`；清账表 `表面=18 状态=9 格子=162 已清账=162 未清账=0 地板=162`；产品面连续零改动 **1** 轮（as-of 412，现读 `--streak-for 412`）。电池 `Ran 683 / OK (skipped=4)`（台账后复跑）。
- **具名 NOT-RUN / 观察**：① 产品 NSTableView 滚动后新物化行的中段/落点像素帧空白（`table-lazy-rows`；静态文档通道正对照已证明 AppKit bounds 动画可拍，产品运动由 origin 作证）；② `MOTION_FLOOR_UNLISTED` 与 `SCROLL_FAILURE_COUNT` 通道本跑没有行；③ macOS 12 紧凑详情头仍走旧截断；④ 主列表/浮层来源搜索语言未统一（437）；⑤ 设置卡其它行族无行级状态（438）；⑥ 离屏 NSTableView 滚动帧通道边界记 439。

"""

ITER_SECTION = u"""## Round 410 · R413（第 412 轮 · 2026-10-27）：跨视口长跳补滚动到位动画（0→203→1438；旧瞬移 0/15 中间值）；R412 录制描边 runner 红修复（纵向 0 + 强调隔离）（产品 1 文件，滚动到位位）

旧的揭示是一次 `scrollRowToVisible` 瞬移。新 `SelectionRevealMotion.plan` 只在距离 > 一屏且非减弱动态时演 0.20s（`.slider`），instant 与 animated 共用系统最小滚动目标。真在屏抓到两版自伤：纯 bounds 动画滚到位（origin 1977）但 List 选中集 **[]**；只把系统滚动放前面、目标在物化前读会让 2191 跳 3211。最终：先系统滚 + layout + 再滚读物化后目标，回起点演到该目标，完成时再物化落点。真在屏：选中 [60]、在屏 true、origin 3211；臂3 滚开后收藏/撤收藏仍 0；drift 3143→0；intake 0→159、选中 [4]。离屏：17 采样/7 中间值，首 68、末 1438、目标 1438；慢放 0→203→1438。像素通道：静态文档 111729/148800；产品表格滚动后新行不被 cacheDisplay 画出 ⇒ 产品像素中段具名 NOT-RUN `table-lazy-rows`。R412 的 runner 红：节奏 15/10/9、邻行 20740/0；描边纵向 −2→0，邻行隔离改判强调；本地亮 4016/3958、暗 4016/3956、邻行 0/0，基线 192/0；runner 复验等下一跑。M1070–M1075 5/5 CAUGHT；M1065–M1069 重跑 5/5；HIDDEN 256/866 rot=0；预检 169/151/448；全量 1091/53/0（一次 Perf 瞬态未改阈值）。

**七维度自评**（恰七行，每格 n/15）：

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | 13/15 | 真看录制帧亮暗两张与静态文档 start/mid/end 三张（内容确实移动）；扣 2：产品 NSTableView 中段帧是空白，只有 origin 读数，没有产品中段图。 |
| 判据有效性 | 15/15 | 纯计划真值表 + 源守卫 + 真 NSScrollView 行为 + 静态通道正对照 + 真在屏三探针；M1070–M1075 5/5 CAUGHT。 |
| 假绿防御 | 15/15 | M1070 0/15 中间值、M1073/M1074 中段=1438、M1075 首末 0/0；产品空白像素帧具名 NOT-RUN，不硬改。 |
| 产品面推进 | 14/15 | 真落 Sources 1 文件；修了 R412 runner 红并补滚动到位；扣 1：产品中段像素通道未打通。 |
| 台账一致性 | 15/15 | U-1488…U-1492、D-405/D-406、436、R412 跑失败步骤与 R413 三探针都从日志/CI 解析。 |
| 交付诚实性 | 15/15 | R412 跑 failure 原文落账并修；runner 复验等下一跑；PerfBudget 瞬态单跑 148ms、未改阈值；产品像素 NOT-RUN。 |
| 可复核性 | 15/15 | 失败步骤原文、旧/新 origin、慢放三帧、静态通道差、在屏三探针、五把刀、precheck/rot/CI 原文都在。 |

均分 = 102/105 ≈ 14.6/15（97）。"""

DECISION_405 = u"""## D-405 跨视口长跳的滚动到位动画（R413）

- 背景：`SelectedRowRevealer` 在选中项落在视口外时，延后一回合直接 `scrollRowToVisible`；方向键近步与几十行长跳同一条瞬移。长跳没有空间连续性，用户只看到"跳过去了"。
- 决定：`SelectionRevealMotion.plan(distance:viewportHeight:reduceMotion:)` 只在**距离严格大于一屏**且非减弱动态时返回 animated，时长取 `MotionCatalog.duration(for: .slider)`=0.20；近步/减弱动态仍瞬移。animated 路径：先 `table.scrollRowToVisible(row)` 让 List 物化/选中目标行，`layout` 后再滚一次读**物化后的系统目标**，回起点，用 `NSAnimationContext` + `animator().setBoundsOrigin` 以 easeInOut 演到该目标；完成时 `setBoundsOrigin` + `reflectScrolledClipView` + 再 `scrollRowToVisible(row)` 物化落点。instant 路径直接调系统滚动。
- 理由：纯 bounds 动画不会替 SwiftUI List 物化行 —— 真在屏探针读到 origin 1977、选中集 `[]`；把系统滚动放前面但不等于物化后的目标，会让 2191→3211 在末尾跳。系统滚动先做、目标在 layout 后读，选中与落点都真实；近步不演避免方向键粘滞；减弱动态不演，视口照样到目标。
- 兼容性/迁移：只动 `SelectedRowRevealer`，不改选中作者（仍禁 `selectRowIndexes`）；`revealDurationOverride` 只给单测慢放，产品路径 nil。
- 回滚：删 `SelectionRevealMotion` 与动画分支、恢复单一 `scrollRowToVisible` 即可；或 `git revert` 本轮提交。
"""

DECISION_406 = u"""## D-406 录制行描边纵向不外扩，邻行隔离改判强调色（R413）

- 背景：R412 的录制行描边在 runner 1x 上把 `settings-shortcuts-recording` 的卡片节奏读成 15/10/9（差 6.0 > 4.5），`RECORDER_ROW_EDGE` 邻行 `changed=20740` 而 `accent=0`（亮/暗同）。原文指向两件事：描边纵向 −2 侵入行距；runner 的 idle/recording 帧有整页 1 级底色差，不是描边泄漏。
- 决定：描边 `.padding(.vertical, -2)` 改为**不外扩**（与行内容同边）；`RECORDER_ROW_EDGE` 的邻行判据从"任意变化=0"改判**强调色=0**，任意变化只作读数；补合成真值表（0.82 灰底色被忽略、强调泄漏被抓）。行带强调阈值 400、`SettingsRowEmphasis` 数值与产品调用点不变。
- 理由：邻行 20740/0 是窗口焦点导致的整页底色，不是行级状态；隔离要认"强调"这个状态本身。描边纵向 0 不再减少行距；本地最终捕获亮 4016/3958、暗 4016/3956、邻行 0/0，节奏尺与捕获套件绿。
- 兼容性/迁移：只改描边背景的绘制范围与一条像素判据的对象；产品状态/回调/行高不变。
- 回滚：恢复 `.padding(.vertical, -2)` 与任意变化断言即可；或 `git revert` 本轮提交。runner 侧 15/10/9 与 20740/0 的复验在下一跑。
"""

CHANGELOG_SECTION = u"""### 跨视口长跳补滚动到位动画（0→203→1438；旧瞬移 0/15 中间值）；R412 录制描边 runner 红修复（纵向 0 + 强调隔离）（R413 / 第 412 轮 / Round 410 / U-1488…U-1492 · 产品 1 文件，滚动到位位）

"""

BACKLOG_SECTION = u"""437 追记（R413 · 仍开）：本轮补的是跨视口滚动到位动画与 R412 录制描边 runner 红；主列表仍不匹配 `sourceAppName`，与 QuickPick 继续两套搜索语言。

**439. 离屏 NSTableView 滚动后新物化行不进 `cacheDisplay`**（R413 观察）
    现象：真 NSTableView 在离屏窗口里滚动后，中段/落点 `cacheDisplay` 帧是空白（起→中变化有、中→落 0）；同一套 AppKit bounds 动画在静态文档视图上三帧两两不同（111729/148800）。⇒ 滚动动效的产品像素中段只能记具名 NOT-RUN `table-lazy-rows`，产品运动由 `documentVisibleRect.origin` 逐时读数作证。
    修法（下一轮若需要产品中段图）：先给 NSTableView 做快照/逐行合成（`rowView.cacheDisplay` 拼到目标 y），或把滚动动效的可视证据改到真在屏探针的 CGWindow 截图；不要在空白帧上硬判。"""

STATE_SECTION = u"""## R413 状态（2026-10-27 · 本地 · 第 412 轮 / Round 410）：跨视口长跳补滚动到位动画（0→203→1438；旧瞬移 0/15 中间值）；R412 录制描边 runner 红修复（纵向 0 + 强调隔离）（产品 1 文件，滚动到位位）

最后更新：2026-10-27（本地 · R413 / 第 412 轮 / Round 410）：旧的揭示是一次 `scrollRowToVisible` 瞬移。新 `SelectionRevealMotion.plan` 只在距离 > 一屏且非减弱动态时演 0.20s（`.slider`），instant 与 animated 共用系统最小滚动目标。真在屏抓到两版自伤：纯 bounds 动画滚到位（origin 1977）但 List 选中集 **[]**；只把系统滚动放前面、目标在物化前读会让 2191 跳 3211。最终：先系统滚 + layout + 再滚读物化后目标，回起点演到该目标，完成时再物化落点。真在屏：选中 [60]、在屏 true、origin 3211；臂3 滚开后收藏/撤收藏仍 0；drift 3143→0；intake 0→159、选中 [4]。离屏：17 采样/7 中间值，首 68、末 1438、目标 1438；慢放 0→203→1438。像素通道：静态文档 111729/148800；产品表格滚动后新行不被 cacheDisplay 画出 ⇒ 产品像素中段具名 NOT-RUN `table-lazy-rows`。R412 的 runner 红：`40385615419 ↔ 130be12` **failure**，2 个失败步骤；节奏 15/10/9、邻行 20740/0；描边纵向 −2→0，邻行隔离改判强调；本地亮 4016/3958、暗 4016/3956、邻行 0/0，基线 192/0；runner 复验等下一跑。M1070–M1075 **5/5 CAUGHT**；M1065–M1069 重跑 5/5；HIDDEN 256/866 rot=0；预检 169/151/448 bad=0；全量 **1091/53/0**（一次 Perf 瞬态 262.9/269.86ms >250，单跑 148.02ms，复跑 0；阈值未改）；换装 `ok / SHA_MATCH=1 / 381=381 / SMOKE_OK=1`；清账 162=162；产品面连续零改动 1 轮（as-of 412）。电池 `Ran 683 / OK (skipped=4)`（台账后复跑）。

本轮做了什么：
① ⓪ R412 头跑 failure：2 个失败步骤，节奏 15/10/9 + 邻行 20740/0；定位为描边纵向 −2 侵入行距 + runner 整页 1 级底色；产品纵向 0、邻行改判强调，本地复验绿；第二次同码捕获四张 hash 全等。
② 产品：跨视口长跳滚动到位动画，真在屏选中/可见/不回拉/采集揭示四格全过；离屏 7/17 中间值、末=目标。
③ 判据：纯计划 + 源守卫 + 真 NSScrollView 行为 + 静态通道正对照 + 三探针；M1070–M1075 5/5 CAUGHT。
④ 436：judged=5/5、REDS=0、UNLISTED 登记 ok、notice-banner 放行，保持结案。
⑤ 367：hidden 表 256 / 可判 866 / rot 0 / 上界 0；预检 169/151/448/0。
⑥ 全量 1091/53/0；换装 ok；清账 162=162；帧基线 192/0/0/0。

NOT-RUN / 阻塞（分开写）：① 产品 NSTableView 滚动后的中段/落点像素帧空白（`table-lazy-rows`；静态文档正对照已证明通道可拍）；② `MOTION_FLOOR_UNLISTED` 与 `SCROLL_FAILURE_COUNT` 通道本跑没有行；③ 亮档真机腿仍没跑；④ macOS 12 紧凑详情头仍走旧截断；⑤ 主列表与浮层来源搜索语言未统一（437）；⑥ 设置卡其它行族没有行级状态（438）；⑦ 离屏滚动帧通道边界记 439；⑧ R413 新跑待 push 后读；⑨ R412 runner 的节奏/邻行复验等 R413 新跑。

下一轮（R414）的靶：⓪ 先 `git push origin main`（禁 amend/force）并复核 ahead=0；读 R413 主笔+追记 head 跑全部失败步骤（成对 run↔commit），in_progress/0 字节不算绿；重点看 R412 的 15/10/9 与 20740/0 是否在 runner 上消失、滚动动画三探针是否绿；① 367 现读 rot=0，按 `HIDDEN_ROT` 查新腐烂；② 继续产品视觉位并落 Sources、换缺陷类别；③ 436 只复核新跑 Motion floor，不重猜 `must_judge`。

"""

audit = rd(AUDIT)
iter_text = rd(ITER)
decisions = rd(DECISIONS)
changelog = rd(CHANGELOG)
backlog = rd(BACKLOG)
state = rd(STATE)

if audit.count(AUDIT_TITLE) != 1:
    raise SystemExit("REFUSED AUDIT 锚点命中 %d 次" % audit.count(AUDIT_TITLE))
if u"第 412 轮（R413" in audit:
    raise SystemExit("REFUSED AUDIT 已有 R413 节")
if u"## Round 410 · R413" in iter_text:
    raise SystemExit("REFUSED ITERATION 已有 Round 410")
if u"## D-405" in decisions or u"## D-406" in decisions:
    raise SystemExit("REFUSED DECISIONS 已有 D-405/406")
if u"跨视口长跳补滚动到位动画" in changelog:
    raise SystemExit("REFUSED CHANGELOG 已有该标题")
if u"**439." in backlog:
    raise SystemExit("REFUSED BACKLOG 已有 439")
if state.count(u"## R412 状态") != 1:
    raise SystemExit("REFUSED STATE 锚点命中 %d 次" % state.count(u"## R412 状态"))

new_audit = audit.replace(AUDIT_TITLE, AUDIT_SECTION + AUDIT_TITLE, 1)
new_iter = iter_text.rstrip() + "\n\n" + ITER_SECTION + "\n"
new_decisions = decisions.rstrip() + "\n\n" + DECISION_405 + "\n\n" + DECISION_406 + "\n"
marker = u"## [Unreleased]\n"
if changelog.count(marker) != 1:
    raise SystemExit("REFUSED CHANGELOG [Unreleased] 命中 %d 次" % changelog.count(marker))
new_changelog = changelog.replace(marker, marker + "\n" + CHANGELOG_SECTION, 1)
new_backlog = backlog.rstrip() + "\n\n" + BACKLOG_SECTION + "\n"
new_state = state.replace(u"## R412 状态", STATE_SECTION + u"## R412 状态", 1)

wr(AUDIT, new_audit)
wr(ITER, new_iter)
wr(DECISIONS, new_decisions)
wr(CHANGELOG, new_changelog)
wr(BACKLOG, new_backlog)
wr(STATE, new_state)
print("LEDGERS_R413_OK audit=%d iter=%d decisions=%d changelog=%d backlog=%d state=%d"
      % (len(new_audit), len(new_iter), len(new_decisions), len(new_changelog),
         len(new_backlog), len(new_state)))
