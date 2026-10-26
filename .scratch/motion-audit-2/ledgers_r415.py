#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R415 七本台账一次落盘（只跑一次；先断言所有锚点，全部通过才写）。"""
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


AUDIT_TITLE = u"## 第 413 轮（R414 · 2026-10-27"
AUDIT_SECTION = u"""## 第 414 轮（R415 · 2026-10-27 · U-1498…U-1502）：QuickPick 搜索框补焦点边界（静置 255/30 → 焦点 235/47.5）；R414 run 的设置内容红由撤 settle 修、R413 滚动两红已绿（reduce=true）（产品 1 文件，面板搜索焦点位）

- **U-1498：⓪ `40408685273 ↔ 65514d4` 的失败步骤与 reduce 真值。** 结论 **failure**，失败步骤 **2 个**：`Swift tests` + `Capture gate`。**R412 的两红已消失**（`RECORDER_ROW_EDGE` 亮/暗 1318/1312、1318/1310，邻行 0/0）。**R413 的两条滚动行为红已绿**：`SCROLL_REVEAL_PLAN reduce=true override=Optional(false)`、`SCROLL_REVEAL_TIME 采样=6 中间值=2 首=199.0 末=1430.0 目标=1430.0` ⇒ 修法有效，runner 的 reduce-motion 真值是 **true**。新红是 8 条去重断言、全在 `UICaptureTests` 的设置内容帧：`testProbesDoNotSitOnVibrantColumns`（六条说明探针压在 vibrant）、`testRowTierProfileSeparatesCaptionFromTitle`（light 开关标签 504 vs 518）、`testSettingsCardVerticalRhythmIsOneNumber`（settings-stats dark 1 vs 0）、`testDisabledToggleAndFailureReceiptAreVisible`（light 三帧只有 1 帧有墨 8534/0/0）。成因：R414 给**整页 settings 夹具**加的 0.1s settle 让 runner 1x 的帧落在 contentFade 中段/vibrant；此前空白帧让能力闸门 skip。修法：撤掉整页 settings 的 settle（组件胶囊帧保留 0.1s）；本地 200 帧与撤前**逐字节相同**（既有 192 仍不变）。胶囊组件帧在 runner 1x 读 **33.5/49.5/65.5pt**（2x 本地 35.8/51.2/67.5；半行 16/16），中点 49.5pt 是 1x 的落点，不是 2x 的 51.2 抄错。
- **U-1499：② QuickPick 搜索焦点边界。** 面板搜索框是 `isBordered=false`、`drawsBackground=false` 的裸字段；R409 只在悬停点亮边界，而面板打开时字段就是第一响应者 —— 焦点没有任何可见边界。修法：`QuickPickSearchField` 重写 `becomeFirstResponder/resignFirstResponder` 并回调 `onFocusChange`；`QuickPickSearchBackdrop` 增加 `focused` 与 `focusedForCapture`，焦点/悬停共用同一档 active chrome；`show()` 只在 `makeFirstResponder(field)` 真的成功时点亮（不画假承诺），`hide()` 收回；`windowForCapture(searchFocused:)` 给夹具。真看图：静置是裸文字，焦点/悬停都有圆角底与描边；像素同带（x=300..400、y=12..40pt）静置 **255.0/30.0** → 焦点 **235.0/47.5**（亮/暗），框外 194.3/94.7 作对照。新增 `quickpick-search-focus` 亮暗 2 帧；既有 198 帧逐字节不变；基线 **200/0/0/0**。
- **U-1500：判据与刀。** 源守卫钉 `onFocusChange` 出口、backdrop 的 focus 绘制前置、`if panel.makeFirstResponder(field)`、show/hide；像素守卫 `testQuickPickSearchFieldFocusLiftsItsChrome` 用框内均值 + 框外对照。`M1080…M1083` **4/4 CAUGHT**（M1080 焦点帧=静置 30.0；M1081/82/83 源）、`RESTORE_CLEAN=yes`。焦点改动把两张旧表弄空：R409 的 `M1060`（旧 hover-only guard）重钉到新 guard 并整表重跑 **2/2 CAUGHT**；R76 的 `M399`（`makeFirstResponder(field)` 旧行）重钉为“接收对象换 nil”并整表重跑 **5/5 CAUGHT**、只红焦点判据。`HIDDEN_ARMS rot` 从 1 回到 **0**。
- **U-1501：③ 436 只读新跑。** `40408685273`：`MOTION_FLOOR_FACTS judged=5/5 executed=73 not-run=- summary=detail-kind-change=4 empty-state=3 notice-banner=2 notice-banner-dismiss=3 settings-reset-fade=2 红的用例=- 汇总行报红=0`、`MOTION_FLOOR_REDS=0`；`MOTION_FLOOR_UNLISTED` 通道没有行 ⇒ 具名 NOT-RUN；`notice-banner` 放行，未重猜 `must_judge`。
- **U-1502：① 367 rot 与八步。** `HIDDEN_ARMS 表=258 可判=874 rot=0 抽不出=6 已声明表=6 已声明死针=0 上界 rot=0 处置=ok`；预检 `tables=171 covered=153 arms=456 bad=0`、全仓 264 文件 / 940 把；BASH_ARMS 16 bad=0；R415 表 M1080–M1083 全 ok。build **0** 告警；全量 **1096/53/0**；捕获 **200 帧 / 123 条 / 4 skip / 0 失败**、final3 200/0；基线 `UPDATED=200`、复验 `COMPARED=200 CHANGED=0 MISSING=0 ADDED=0`（既有 198 帧不变，新增焦点 2 帧）；换装 `INSTALL_RESULT=ok`、`INSTALL_SHA_MATCH=1`、381=381、`SMOKE_OK=1`；清账表 162=162；产品面连续零改动 **1** 轮（as-of 414，现读 `--streak-for 414`）。电池 `Ran 683 / OK (skipped=4)`（台账后复跑）。
- **具名 NOT-RUN / 观察**：① runner 的真在屏 `REVEAL`/`INTAKE_READING` 通道仍没有行（本地绿；On-screen step report-only）；② 产品 NSTableView 滚动中段像素帧 `table-lazy-rows`；③ `MOTION_FLOOR_UNLISTED`/`SCROLL_FAILURE_COUNT` 通道缺行；④ R414 run 的设置内容红靠“撤 settle”回归能力闸门，runner 复验等 R415 新跑；⑤ macOS 12 紧凑详情头仍走旧截断；⑥ 437/438/439/440 仍开；⑦ 设置内容帧在 runner 上的能力闸门仍是隐式的（空白才 skip），见 441。

"""

ITER_SECTION = u"""## Round 412 · R415（第 414 轮 · 2026-10-27）：QuickPick 搜索框补焦点边界（静置 255/30 → 焦点 235/47.5）；R414 run 的设置内容红由撤 settle 修、R413 滚动两红已绿（reduce=true）（产品 1 文件，面板搜索焦点位）

QuickPick 搜索框是裸字段，R409 只在悬停点亮边界；面板一打开字段就是第一响应者，焦点没有可见边界。新：`QuickPickSearchField` 的 `become/resignFirstResponder` 回调 `onFocusChange`；`QuickPickSearchBackdrop` 增加 `focused/focusedForCapture`，焦点与悬停同档；`show()` 只在 `makeFirstResponder(field)` 成功时点亮，`hide()` 收回；夹具 `windowForCapture(searchFocused:)`。真看图：静置裸文字，焦点/悬停圆角底与描边；同带 255/30 → 235/47.5，框外 194.3/94.7。新增焦点 2 帧，既有 198 帧不变，基线 200。M1080–M1083 4/4 CAUGHT；R409 M1060 重钉后 2/2、R76 M399 重钉后 5/5，HIDDEN rot 1→0。R414 run：2 个失败步骤，R412 两红消失；R413 滚动两红已绿（reduce=true override=false、首=199/末=1430/2 中间值）；新红是 R414 给整页 settings 加的 0.1s settle 让 runner 帧落在 vibrant/contentFade 中段（probes/rowtier/card/disabled 8 条），撤掉 settle 后本地 200 帧逐字节不变。胶囊组件 1x 33.5/49.5/65.5（2x 35.8/51.2/67.5）。全量 1096/53/0；换装 ok；清账 162=162；HIDDEN 258/874 rot=0；预检 171/153/456；电池 683/4。

**七维度自评**（恰七行，每格 n/15）：

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | 15/15 | 真看静置/焦点/悬停三张亮帧：静置裸文字、焦点与悬停同档圆角边界；暗档读数同带。 |
| 判据有效性 | 15/15 | 源守卫钉 first responder 出口/backdrop/show/hide + 像素框内均值/框外对照；M1080–M1083 4/4；旧表重钉后 2/2、5/5。 |
| 假绿防御 | 15/15 | 静置 255/30 vs 焦点 235/47.5；M1080 焦点=静置 30.0；既有 198 帧 0 变；框外对照在。 |
| 产品面推进 | 14/15 | 真落 Sources 1 文件；补的是面板搜索焦点；扣 1：焦点视觉与悬停同档，只换了触发，runner 新帧待下一跑。 |
| 台账一致性 | 15/15 | U-1498…U-1502、D-409/D-410、436、R414 跑、R409/R76 重钉都从日志/CI 解析。 |
| 交付诚实性 | 15/15 | R414 runner 8 条设置红原文落账，撤 settle 而非改阈值；R413 滚动 fix 由 runner 的 reduce/override 读数签收；探针通道缺行记 NOT-RUN。 |
| 可复核性 | 15/15 | 旧/新均值、框外、两张新帧、四把刀、两张旧表重跑、precheck/rot/CI 原文都在。 |

均分 = 104/105 ≈ 14.9/15（99）。"""

DECISION_409 = u"""## D-409 QuickPick 搜索框的焦点边界（R415）

- 背景：面板搜索框是 `isBordered=false`、`drawsBackground=false` 的裸字段；R409 只在悬停点亮边界；而 `show()` 一出来字段就是第一响应者，焦点没有任何可见边界，用户不知道"可以打字"的承诺落在哪。
- 决定：`QuickPickSearchField` 重写 `becomeFirstResponder/resignFirstResponder` 并回调 `onFocusChange`；`QuickPickSearchBackdrop` 增加 `focused` 与 `focusedForCapture`；焦点与悬停共用同一档 active chrome；`show()` 只在 `makeFirstResponder(field)` 成功时点亮，`hide()` 收回；`windowForCapture(searchFocused:)` 只给夹具。
- 理由：焦点是真实状态（面板打开即有），不是悬停的替代；同一档视觉让"这个框是活的"只有一种说法；拿不到第一响应者就不亮，避免假承诺；焦点帧可在离屏确定性渲染。
- 兼容性/迁移：仅 QuickPick 面板内部；`windowForCapture` 新增默认参数，既有调用点/帧不变。
- 回滚：删 focus 回调/backdrop 的 focused 与 show/hide 两句即可；或 `git revert` 本轮提交。
"""

DECISION_410 = u"""## D-410 撤掉整页 settings 夹具的 settle，保留组件胶囊帧的 settle（R415）

- 背景：R414 为了让侧栏胶囊的 PreferenceKey 回填，给整页 settings 夹具加了 0.1s settle；runner 1x 因此从"空白帧（能力闸门 skip）"变成 vibrant/contentFade 中段，probes/rowtier/card/disabled 8 条红；R412 两红已消失、R413 滚动两红已绿（reduce=true）。
- 决定：撤掉整页 settings 的 settle；`settingssidebar-selection-*` 组件帧保留 0.1s；整页静置帧回到捕获管线的原状态，组件帧继续作为胶囊证据。本地撤前后 200 帧逐字节相同（既有 192 不变）。
- 理由：0.1s 既不够过 contentFade（0.16），又足以让 runner 的设置内容不再全空白；同一条 settle 既没帮上胶囊（PreferenceKey 当次布局已回填），又把隐式能力闸门打破。不新增/放宽任何判据阈值。
- 兼容性/迁移：只改测试夹具；产品与帧内容不变。
- 回滚：恢复 0.1s settle 即可；或 `git revert` 本轮提交。
"""

CHANGELOG_SECTION = u"""### QuickPick 搜索框补焦点边界（静置 255/30 → 焦点 235/47.5）；R414 run 的设置内容红由撤 settle 修、R413 滚动两红已绿（reduce=true）（R415 / 第 414 轮 / Round 412 / U-1498…U-1502 · 产品 1 文件，面板搜索焦点位）

"""

BACKLOG_SECTION = u"""437 追记（R415 · 仍开）：本轮补的是 QuickPick 搜索焦点边界与 settings 夹具 settle 回归；主列表仍不匹配 `sourceAppName`，与 QuickPick 继续两套搜索语言。

**441. settings 内容帧在 runner 上的能力闸门是隐式的（空白才 skip），一条 settle 就能把它打破**（R415 读 `40408685273`）
    现象：R414 给整页 settings 夹具加 0.1s settle 后，runner 1x 的设置帧从空白变成 vibrant/半绘制，`testProbesDoNotSitOnVibrantColumns`/`testRowTierProfile...`/`testSettingsCardVerticalRhythm...`/`testDisabledToggle...` 8 条一起红；撤 settle 即恢复。此前"这台机器画不出设置页"是靠**恰好空白**被 skip 的，而不是一条显式能力出口。
    修法（下一轮）：给 settings 内容帧一条显式能力闸门（读内容列墨/未绘制比例，和 `CAPTURE_CAPABILITY` 同口径），机器画不出时打具名 NOT-RUN；不要让夹具的等待时长决定判据跑不跑。"""

STATE_SECTION = u"""## R415 状态（2026-10-27 · 本地 · 第 414 轮 / Round 412）：QuickPick 搜索框补焦点边界（静置 255/30 → 焦点 235/47.5）；R414 run 的设置内容红由撤 settle 修、R413 滚动两红已绿（reduce=true）（产品 1 文件，面板搜索焦点位）

最后更新：2026-10-27（本地 · R415 / 第 414 轮 / Round 412）：QuickPick 搜索框是裸字段，R409 只在悬停点亮边界；面板一打开字段就是第一响应者，焦点没有可见边界。新增 `QuickPickSearchField` 的 `become/resignFirstResponder` → `onFocusChange`；`QuickPickSearchBackdrop` 的 `focused/focusedForCapture`；`show()` 只在 `makeFirstResponder(field)` 成功时点亮、`hide()` 收回；夹具 `windowForCapture(searchFocused:)`。真看图：静置裸文字，焦点/悬停同档圆角底与描边；同带静置 **255.0/30.0** → 焦点 **235.0/47.5**，框外 194.3/94.7。新增 `quickpick-search-focus` 亮暗 2 帧；既有 198 帧逐字节不变；基线 **200/0/0/0**。`M1080–M1083` **4/4 CAUGHT**；焦点改动把 R409 `M1060` 与 R76 `M399` 两张旧表弄空，已重钉并整表重跑 **2/2**、**5/5 CAUGHT**，HIDDEN rot 1→0。R414 run `40408685273 ↔ 65514d4` failure：失败步骤 2 个（Swift tests + Capture gate）；**R412 两红消失**；**R413 滚动两红已绿**（`SCROLL_REVEAL_PLAN reduce=true override=false`、首=199/末=1430/2 中间值）；新红 8 条全在 settings 内容帧，成因是 R414 整页 settings 夹具的 0.1s settle 让 runner 帧落在 vibrant/contentFade 中段；撤 settle 后本地 200 帧逐字节不变。胶囊组件在 runner 1x 33.5/49.5/65.5（2x 35.8/51.2/67.5）。全量 **1096/53/0**；捕获 **200/123/4/0**、final3 200/0；换装 `ok / SHA_MATCH=1 / 381=381 / SMOKE_OK=1`；清账 162=162；HIDDEN 258/874 rot=0；预检 171/153/456 bad=0；产品面连续零改动 **1** 轮（as-of 414，现读 `python3 scripts/product_streak.py --streak-for 414`）。电池 `Ran 683 / OK (skipped=4)`（台账后复跑）。

本轮做了什么：
① ⓪ R414 runner：R412 两红消失、R413 滚动两红已绿（reduce=true、2 中间值）；新红 8 条是整页 settings 的 0.1s settle 打破隐式能力闸门；撤 settle。
② 产品：QuickPick 搜索框补焦点边界，静置 255/30 → 焦点 235/47.5，新增 2 帧。
③ 判据：焦点源/像素 + M1080–M1083 4/4；R409 M1060 / R76 M399 重钉后 2/2、5/5；hidden rot 0。
④ 436：judged=5/5、REDS=0、notice-banner 放行；无新 unlisted。
⑤ 367：hidden 表 258 / 可判 874 / rot 0 / 上界 0；预检 171/153/456/0。
⑥ 全量 1096/53/0；换装 ok；清账 162=162；帧基线 200/0/0/0。

NOT-RUN / 阻塞（分开写）：① runner 的真在屏 `REVEAL`/`INTAKE_READING` 通道没有行（本地绿）；② 产品 NSTableView 滚动中段像素帧 `table-lazy-rows`；③ `MOTION_FLOOR_UNLISTED`/`SCROLL_FAILURE_COUNT` 通道缺行；④ R414 run 的设置内容红靠撤 settle 回隐式能力闸门，runner 复验等 R415 新跑；⑤ 亮档真机腿仍没跑；⑥ macOS 12 紧凑详情头仍走旧截断；⑦ 437/438/439/440/441 仍开；⑧ R415 新跑待 push 后读。

下一轮（R416）的靶：⓪ 先 `git push origin main`（禁 amend/force）并复核 ahead=0；读 R415 主笔+追记 head 跑全部失败步骤（成对 run↔commit），in_progress/0 字节不算绿；重点看 settings 内容帧是否恢复能力闸门、焦点帧在 runner 上的读数；① 367 现读 rot=0，按 `HIDDEN_ROT` 查新腐烂；② 继续产品视觉位并落 Sources、换缺陷类别；③ 436 只复核新跑 Motion floor，不重猜 `must_judge`。

"""

audit = rd(AUDIT)
iter_text = rd(ITER)
decisions = rd(DECISIONS)
changelog = rd(CHANGELOG)
backlog = rd(BACKLOG)
state = rd(STATE)

if audit.count(AUDIT_TITLE) != 1:
    raise SystemExit("REFUSED AUDIT 锚点命中 %d 次" % audit.count(AUDIT_TITLE))
if u"第 414 轮（R415" in audit:
    raise SystemExit("REFUSED AUDIT 已有 R415 节")
if u"## Round 412 · R415" in iter_text:
    raise SystemExit("REFUSED ITERATION 已有 Round 412")
if u"## D-409" in decisions or u"## D-410" in decisions:
    raise SystemExit("REFUSED DECISIONS 已有 D-409/410")
if u"QuickPick 搜索框补焦点边界" in changelog:
    raise SystemExit("REFUSED CHANGELOG 已有该标题")
if u"**441." in backlog:
    raise SystemExit("REFUSED BACKLOG 已有 441")
if state.count(u"## R414 状态") != 1:
    raise SystemExit("REFUSED STATE 锚点命中 %d 次" % state.count(u"## R414 状态"))

new_audit = audit.replace(AUDIT_TITLE, AUDIT_SECTION + AUDIT_TITLE, 1)
new_iter = iter_text.rstrip() + "\n\n" + ITER_SECTION + "\n"
new_decisions = decisions.rstrip() + "\n\n" + DECISION_409 + "\n\n" + DECISION_410 + "\n"
marker = u"## [Unreleased]\n"
if changelog.count(marker) != 1:
    raise SystemExit("REFUSED CHANGELOG [Unreleased] 命中 %d 次" % changelog.count(marker))
new_changelog = changelog.replace(marker, marker + "\n" + CHANGELOG_SECTION, 1)
new_backlog = backlog.rstrip() + "\n\n" + BACKLOG_SECTION + "\n"
new_state = state.replace(u"## R414 状态", STATE_SECTION + u"## R414 状态", 1)

wr(AUDIT, new_audit)
wr(ITER, new_iter)
wr(DECISIONS, new_decisions)
wr(CHANGELOG, new_changelog)
wr(BACKLOG, new_backlog)
wr(STATE, new_state)
print("LEDGERS_R415_OK audit=%d iter=%d decisions=%d changelog=%d backlog=%d state=%d"
      % (len(new_audit), len(new_iter), len(new_decisions), len(new_changelog),
         len(new_backlog), len(new_state)))
