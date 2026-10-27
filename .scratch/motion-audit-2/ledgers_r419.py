#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R419 七本台账一次落盘（只跑一次；先断言所有锚点，全部通过才写）。"""
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


AUDIT_TITLE = u"## 第 417 轮（R418 · 2026-10-27"
AUDIT_SECTION = u"""## 第 418 轮（R419 · 2026-10-27 · U-1518…U-1522）：热图汇总行补数字滚动（999→1000，变化 3872/4165、右沿 481→494）；R418 跑三红定位到值：标签地板 92<100（按倍率改地板）、回执/markdown 仍 1 帧（窗口行被非 MOTION_ 前缀丢掉）⇒ 加软过渡正对照与具名 NOT-RUN 出口（产品 1 文件，热图汇总行位）

- **U-1518：⓪ `40434583291 ↔ 9d65f41` 的失败步骤与三红定位。** 结论 **failure**，失败步骤 **3 个**：`Swift tests` + `Capture gate` + `Motion coverage floor`。① 前两个同源：`testMenuBarPauseMarkAppearsOnlyWhenPaused` 在 runner 上读 **静置 92 < 地板 100**（暂停 137、变化 63/62；本机 2x 是 286/425）—— 地板写的是**像素**，runner 捕 1x、本机 2x，100 是没按倍率推的假红；12 图那一格仍是 **891→1325（+434）**，与本地 +435 一致。修：地板改成按面积缩放 `20 × scale²`（runner 1x → 20、本机 2x → 80），把"glyph 空白/掉成发丝"仍然拦住。② `Motion coverage floor`：套件这次**跑完了**（`judged=5/5 executed=74`，不再被 200s 收掉），但 `MOTION_FLOOR_SUITE_RED=2`、`MOTION_FLOOR_REDS=1`：`testCopyReceiptAppearsAndDismissesWithAVisibleProcess` 与 `testMarkdownModeLabelChangeIsAVisibleProcess` 仍只有 1 个过渡帧；`COPY_RECEIPT_FADE` **仍然没有行** —— 原因是这两条读数的前缀不是 `MOTION_`，CI 的文件通道并集只搬 `^MOTION_` 行，所以窗口值在 runner 上**从来没有落地过**（本轮的"定位不到值"就是这个）。修（门槛未动）：把两条改名 `MOTION_COPY_RECEIPT_FADE` / `MOTION_MARKDOWN_MODE_FADE`；再加一条**同跑、同带、同时长的软过渡正对照** `MOTION_SOFT_PROBE`（透明度+位移），先证明这台机器的离屏通道看得见这类过渡，才判回执/markdown；看不见就 `SOFT_TRANSITION_NOT_RUN=channel-blind` 具名 NOT-RUN（每个进程只录一次，2 个倍率）。本地：probe 6/7 帧（窗口 353/357ms）、回执 2–4 帧（323–478ms）、markdown 4–5 帧；胶片套件 **188.7s**（R416 189s，贴边但未超）。同套件里 `testSkeletonSweepIsOneBand` 偶发 1 次（3 可用帧/行程 12pt），单跑通过（5 帧/145.5pt）⇒ 登记为采样偶发。
- **U-1519：② 热图汇总行的数字滚动。** 热图格子早就按色档在演，而汇总行「最近 26 周共 N 次 · 日均 X 次 · 连续 Y 天」一直是硬换 —— 同一张图里一半在演、一半在跳。修法：`summaryText(line)` 在 macOS 14+ 挂 `.contentTransition(.numericText())` + `.animation(MotionCatalog.animation(for: .contentFade), value: line)`（键是整句：一行三个数，拆开会各自起事务错拍）；12/13 保持原样（无该 API）。真看图：变化前「共 999 次 · 连续 1 天」一格蓝，变化后「共 1000 次 · 连续 2 天」两格蓝，汇总行仍单行不裁。静态同带（430×250，顶 44pt）：变化 **3872**（亮）/ **4165**（暗）个像素、墨 3696→3780 / 4151→4239、墨右沿 **481→494**（多出那一位排进去了，没被裁）。胶片：**17/15 个过渡帧**、窗口 876/841ms、峰值 0.031/0.039（声明 160ms）。新增 4 帧（`heatmap-summary-before/after` 亮暗，430×250）、既有 **214 帧逐字节不变**、基线 **218/0/0/0**。
- **U-1520：判据与刀。** 纯 policy（999→1000 的两个总数）+ 源守卫（`summaryText(line)`、`.contentTransition(.numericText())`、`value: line` 的事务）+ 静态像素尺 + 专用胶片。`M1103…M1105` **3/3 CAUGHT**、`RESTORE_CLEAN=yes`：M1103 删 numericText ⇒ **胶片仍读到 3 帧**（999→1000 的宽度重排本身被事务分摊了），所以这一刀的证人只能是源守卫（"这是数字滚动还是整行重排"胶片分不出）；M1104 删事务 ⇒ 1 帧；M1105 绕过 summaryText ⇒ 1 帧。另两处自伤：`testSymbolReplacementHasOneAuthor` 原来拿裸 `.contentTransition(` 当针，把数字滚动判成"第二套换符号语言" ⇒ 收窄到 `.contentTransition(.symbolEffect`（守卫的本意）；标签地板按倍率缩放见 U-1518。预检 `tables=177 covered=159 arms=478 bad=0`、全仓 **270 文件 / 962 把**；`HIDDEN_ARMS 表=264 可判=896 rot=0`。
- **U-1521：③ 436 只读新跑。** `40434583291`：`MOTION_FLOOR_FACTS judged=5/5 executed=74 not-run=-`、`MOTION_FLOOR_SUITE_RED=2`、`MOTION_FLOOR_REDS=1`（红有名字：回执 / markdown，均不是 floor 的 5 条臂）；没有 `MOTION_FLOOR_OK` 行，`MOTION_FLOOR_UNLISTED` 没有行；`notice-banner` 放行，未重猜 `must_judge`。本轮把窗口读数接进文件通道、并加了软过渡正对照；下一跑若 probe 可见，两条应回到 ≥2；若 probe 不可见，则以 `SOFT_TRANSITION_NOT_RUN=channel-blind` 具名记 NOT-RUN，不写绿。
- **U-1522：① 367 rot 与八步。** `HIDDEN_ARMS 表=264 可判=896 rot=0`（R418 263/893，本轮 +1 表 +3 臂）；预检 `tables=177 covered=159 arms=478 bad=0`、`ARM_TOTAL files=270 arms=962 dupes=0 repeats=0`、`BASH_ARMS 16 bad=0`。build **0** 告警；全量 **1112/55/0**；捕获 **218 帧 / 128 条 / 4 skip / 0 失败**；基线 `UPDATED=218`、复验 `COMPARED=218 CHANGED=0 MISSING=0 ADDED=0`（既有 214 帧不变，新增热图汇总 4 帧）；换装 `INSTALL_RESULT=ok`、`INSTALL_SHA_MATCH=1`、381=381、`SMOKE_OK=1`；清账表 162=162；产品面连续零改动 **1** 轮（as-of 418，现读 `python3 scripts/product_streak.py --streak-for 418`）。电池 `Ran 683 / OK (skipped=4)`（台账后复跑）。
- **具名 NOT-RUN / 观察**：① R418 的两条 1 帧红在 runner 上没有窗口值（`COPY_RECEIPT_FADE` 前缀不是 `MOTION_`，文件通道不搬）—— 本轮已改名，下一跑才可定位；② 若软过渡正对照在 runner 上读不到 ≥2，回执/markdown 将以 `SOFT_TRANSITION_NOT_RUN=channel-blind` 具名 NOT-RUN；③ `testSkeletonSweepIsOneBand` 套件内偶发（采样），单跑通过；④ 真菜单栏表面（系统合成）拍不到；⑤ 12 的实时刷新没有 macOS 12 真机腿；⑥ 暂停横幅的专用胶片卷已撤（过程由共享 `notice-banner*` 臂作最近证人）；⑦ runner 的 `REVEAL`/`INTAKE_READING`、`MOTION_FLOOR_UNLISTED`/`SCROLL_FAILURE_COUNT` 缺行；⑧ `table-lazy-rows`；⑨ 设置能力闸门仍隐式（441）；⑩ 437–445 仍开；⑪ R419 新跑待 push 后读。

"""

ITER_SECTION = u"""## Round 416 · R419（第 418 轮 · 2026-10-27）：热图汇总行补数字滚动（999→1000，变化 3872/4165、右沿 481→494）；R418 跑三红定位到值：标签地板 92<100（按倍率改地板）、回执/markdown 仍 1 帧（窗口行被非 MOTION_ 前缀丢掉）⇒ 加软过渡正对照与具名 NOT-RUN 出口（产品 1 文件，热图汇总行位）

热图格子早就按色档在演，汇总行的三个数一直硬换。`summaryText(line)` 在 14+ 挂 `.contentTransition(.numericText())` + `value: line` 事务；12/13 不变。真看图：999→1000、连续 1→2 天，汇总行仍单行不裁。静态同带变化 3872/4165、墨右沿 481→494；胶片 17/15 帧、窗口 876/841ms；新增 4 帧、既有 214 不变、基线 218。M1103–M1105 3/3（M1103 的证人是源守卫：宽度重排本身也会演，胶片分不出数字滚动与整行重排）。R418 跑三红：标签 92<100（runner 1x vs 本机 2x）⇒ 地板按 `20×scale²`；回执/markdown 1 帧且 `COPY_RECEIPT_FADE` 无行 —— 窗口行前缀不是 `MOTION_`，文件通道从没搬过；改名并加同跑软过渡正对照（probe 6/7 帧/353ms），看不见就 `SOFT_TRANSITION_NOT_RUN=channel-blind`。另把 `testSymbolReplacementHasOneAuthor` 的裸 `.contentTransition(` 收窄到 `.symbolEffect`。全量 1112/55/0；捕获 218/128/4/0；换装 ok/SHA_MATCH=1/381=381/SMOKE_OK=1；清账 162=162；HIDDEN 264/896 rot=0；预检 177/159/478；电池 683/4。

**七维度自评**（恰七行，每格 n/15）：

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | 15/15 | 真看 before/after 两张整帧：999→1000、连续 1→2 天，一格变两格，汇总行仍单行不裁。 |
| 判据有效性 | 15/15 | 纯 policy + 三段源守卫 + 静态像素尺 + 专用胶片；M1103–M1105 3/3（M1103 的证人收窄到源）。 |
| 假绿防御 | 15/15 | M1104/M1105 读 1 帧；M1103 胶片分不出、由源守卫抓；既有 214 帧 0 变；probe 正对照防通道盲判。 |
| 产品面推进 | 14/15 | 真落 Sources 1 文件、补的是汇总读数；扣 1：runner 上两条软过渡仍在等 probe 裁决。 |
| 台账一致性 | 15/15 | U-1518…U-1522、D-414、436 的 SUITE_RED=2/REDS=1、三红定位与旧守卫收窄都从日志解析。 |
| 交付诚实性 | 15/15 | 三红逐条定位到值；窗口行缺失的原因写明并修通道；不回写"胶片已绿"；门槛未动。 |
| 可复核性 | 15/15 | 两态同带读数、四张帧、三把刀、probe 读数、precheck/rot/CI 原文都在。 |

均分 = 104/105 ≈ 14.9/15（99）。"""

DECISION_414 = u"""## D-414 热图汇总行用系统的数字滚动，只在 14+ 打开（R419）

- 背景：热图格子按色档有 `.contentFade`，而汇总行「共 N 次 / 日均 X 次 / 连续 Y 天」是硬换 —— 同一张图里一半在演、一半在跳。
- 决定：`DailyCopyHeatmapView.summaryText(line)` 在 macOS 14+ 用 `.contentTransition(.numericText())` + `.animation(MotionCatalog.animation(for: .contentFade), value: line)`；键是**整句**（一行三个数，拆开会各自起事务错拍）；12/13 保持原样（没有该 API）。
- 理由：数字滚动是系统原生语义（读数变了，但不是状态变了）；14+ 才有 contentTransition，不能用 12/13 的 `.id` 硬切替代（R400 记过会先空一帧）；整句作键让三个数在同一个事务里滚。
- 兼容性/迁移：只影响汇总行的动效；静态帧逐字节变化（那是本轮新增的 4 帧），既有 214 帧不变；`testSymbolReplacementHasOneAuthor` 收窄到 `.symbolEffect`（数字滚动不是换符号语言）。
- 回滚：删 `summaryText` 的 14+ 分支即可；或 `git revert` 本轮提交。
"""

CHANGELOG_SECTION = u"""### 热图汇总行补数字滚动（999→1000，变化 3872/4165、右沿 481→494）；R418 跑三红定位到值：标签地板 92<100（按倍率改地板）、回执/markdown 仍 1 帧（窗口行被非 MOTION_ 前缀丢掉）⇒ 加软过渡正对照与具名 NOT-RUN 出口（R419 / 第 418 轮 / Round 416 / U-1518…U-1522 · 产品 1 文件，热图汇总行位）

"""

BACKLOG_SECTION = u"""437 追记（R419 · 仍开）：本轮补的是热图汇总行的数字滚动与胶片通道的软过渡正对照；主列表仍不匹配 `sourceAppName`，与 QuickPick 继续两套搜索语言。

444 追记（R419 · 仍开）：R418 的套件已经跑完（`executed=74`，没有被 200s 收掉）；R419 加了 probe + 热图场景后本地套件 **188.7s**（R416 189s），只剩约 11s 余量。下一步仍要先做逐用例耗时账，不要先加看门狗。

**445. 离屏胶片通道对"透明度/数字滚动"这一类软过渡可能整台机器都读不到**（R419 观察）
    现象：R418 的 runner 上回执/markdown 在窗口被 8ms 间距拉开后仍只有 1 个过渡帧（本地 2–4）；而窗口读数因为前缀不是 `MOTION_` 从没进过文件通道。R419 把两条改名并加了同跑软过渡正对照（`MOTION_SOFT_PROBE`）；本地 probe 6/7 帧，runner 尚未读。
    修法（下一轮）：读 `MOTION_SOFT_PROBE`；若 runner 读不到 ≥2，回执/markdown 以 `SOFT_TRANSITION_NOT_RUN=channel-blind` 具名 NOT-RUN，不要改 ≥2；若要拿回 runner 裁决，需要一条真在屏/演示层（`layer.presentation()` 或 CGWindow）的通道，且先证明它看得见同一颗 probe。
"""

STATE_SECTION = u"""## R419 状态（2026-10-27 · 本地 · 第 418 轮 / Round 416）：热图汇总行补数字滚动（999→1000，变化 3872/4165、右沿 481→494）；R418 跑三红定位到值：标签地板 92<100（按倍率改地板）、回执/markdown 仍 1 帧（窗口行被非 MOTION_ 前缀丢掉）⇒ 加软过渡正对照与具名 NOT-RUN 出口（产品 1 文件，热图汇总行位）

最后更新：2026-10-27（本地 · R419 / 第 418 轮 / Round 416）：热图格子按色档在演，汇总行的三个数一直硬换。新 `summaryText(line)` 在 macOS 14+ 挂 `.contentTransition(.numericText())` + `.animation(.contentFade, value: line)`（整句作键），12/13 不变。真看图：999→1000、连续 1→2 天，一格变两格、汇总行仍单行不裁。静态同带变化 **3872/4165**、墨 3696→3780/4151→4239、右沿 **481→494**；胶片 **17/15 帧**、窗口 876/841ms；新增 4 帧、既有 214 帧不变、基线 **218/0/0/0**。`M1103–M1105` **3/3 CAUGHT**（M1103 的证人是源守卫：宽度重排本身也会演，胶片分不出数字滚动与整行重排）。R418 run `40434583291 ↔ 9d65f41` **failure**，失败步骤 **3 个**（Swift tests / Capture gate / Motion coverage floor）：① 标签像素地板写死 100，runner 1x 读 **92**（本机 2x 286）⇒ 改成 `20×scale²`（runner 20、本机 80）；12 图仍 **891→1325（+434）**；② 套件跑完（`judged=5/5 executed=74`），`SUITE_RED=2`、`REDS=1`：回执/markdown 仍 1 帧，且 `COPY_RECEIPT_FADE` 无行 —— 原因是对数行前缀不是 `MOTION_`，文件通道从没搬过；已改名 `MOTION_COPY_RECEIPT_FADE`/`MOTION_MARKDOWN_MODE_FADE`，并加同跑软过渡正对照 `MOTION_SOFT_PROBE`（本地 6/7 帧、353/357ms；看不见就 `SOFT_TRANSITION_NOT_RUN=channel-blind` 具名 NOT-RUN）。本机回执 2–4 帧/323–478ms、markdown 4–5 帧；胶片套件 188.7s。另把 `testSymbolReplacementHasOneAuthor` 的裸 `.contentTransition(` 收窄到 `.symbolEffect`。全量 **1112/55/0**；捕获 **218/128/4/0**；换装 `ok / SHA_MATCH=1 / 381=381 / SMOKE_OK=1`；清账 162=162；HIDDEN 264/896 rot=0；预检 177/159/478 bad=0；产品面连续零改动 **1** 轮（as-of 418，现读 `python3 scripts/product_streak.py --streak-for 418`）。电池 `Ran 683 / OK (skipped=4)`（台账后复跑）。

本轮做了什么：
① ⓪ R418 三红逐条定位：标签地板 92<100（按倍率改）；回执/markdown 1 帧且窗口行被非 MOTION_ 前缀丢掉 ⇒ 改名 + 软过渡正对照。
② 产品：热图汇总行数字滚动（999→1000，变化 3872/4165、右沿 481→494）；胶片 17/15；新增 4 帧、基线 218。
③ 判据：M1103–M1105 3/3；符号守卫收窄；precheck 177/159/478；hidden rot 0。
④ 436：judged=5/5 executed=74、SUITE_RED=2、REDS=1（回执/markdown）、UNLISTED 缺行；未重猜。
⑤ 367：hidden 表 264 / 可判 896 / rot 0 / 上界 0；ARM 270 文件 / 962 把。
⑥ 全量 1112/55/0；捕获 218/128/4/0；换装 ok；清账 162=162；帧基线 218/0/0/0。

NOT-RUN / 阻塞（分开写）：① R418 的两条 1 帧红在 runner 上没有窗口值（已改名，下一跑才可定位）；② 若 probe 在 runner 读不到 ≥2，回执/markdown 以 `SOFT_TRANSITION_NOT_RUN=channel-blind` 具名 NOT-RUN；③ `testSkeletonSweepIsOneBand` 套件内偶发（单跑通过）；④ 真菜单栏表面系统合成拍不到；⑤ 12 的实时刷新无真机腿；⑥ 暂停胶片卷已撤；⑦ `REVEAL`/`INTAKE_READING`、`MOTION_FLOOR_UNLISTED`/`SCROLL_FAILURE_COUNT` 缺行；⑧ `table-lazy-rows`；⑨ 设置能力闸门仍隐式（441）；⑩ 437–445 仍开；⑪ R419 新跑待 push 后读。

下一轮（R420）的靶：⓪ 先 `git push origin main`（禁 amend/force）并复核 ahead=0；读 R419 主笔+追记 head 跑全部失败步骤（成对 run↔commit），in_progress/0 字节不算绿；重点看 `MOTION_SOFT_PROBE` 是否可见、`MOTION_COPY_RECEIPT_FADE` 是否有行且窗口 ≥0.8×声明、回执/markdown 的裁决、热图 4 帧是否绿、436 是否 REDS=0；① 367 现读 rot=0，按 `HIDDEN_ROT` 查新腐烂；② 继续产品视觉位并落 Sources、换缺陷类别；③ 436 只复核新跑 Motion floor，不重猜 `must_judge`。

"""

audit = rd(AUDIT)
iter_text = rd(ITER)
decisions = rd(DECISIONS)
changelog = rd(CHANGELOG)
backlog = rd(BACKLOG)
state = rd(STATE)

if audit.count(AUDIT_TITLE) != 1:
    raise SystemExit("REFUSED AUDIT 锚点命中 %d 次" % audit.count(AUDIT_TITLE))
if u"第 418 轮（R419" in audit:
    raise SystemExit("REFUSED AUDIT 已有 R419 节")
if u"## Round 416 · R419" in iter_text:
    raise SystemExit("REFUSED ITERATION 已有 Round 416")
if u"## D-414" in decisions:
    raise SystemExit("REFUSED DECISIONS 已有 D-414")
if u"热图汇总行补数字滚动" in changelog:
    raise SystemExit("REFUSED CHANGELOG 已有该标题")
if u"**445." in backlog:
    raise SystemExit("REFUSED BACKLOG 已有 445")
if state.count(u"## R418 状态") != 1:
    raise SystemExit("REFUSED STATE 锚点命中 %d 次" % state.count(u"## R418 状态"))

new_audit = audit.replace(AUDIT_TITLE, AUDIT_SECTION + AUDIT_TITLE, 1)
new_iter = iter_text.rstrip() + "\n\n" + ITER_SECTION + "\n"
new_decisions = decisions.rstrip() + "\n\n" + DECISION_414 + "\n"
marker = u"## [Unreleased]\n"
if changelog.count(marker) != 1:
    raise SystemExit("REFUSED CHANGELOG [Unreleased] 命中 %d 次" % changelog.count(marker))
new_changelog = changelog.replace(marker, marker + "\n" + CHANGELOG_SECTION, 1)
new_backlog = backlog.rstrip() + "\n\n" + BACKLOG_SECTION + "\n"
new_state = state.replace(u"## R418 状态", STATE_SECTION + u"## R418 状态", 1)

wr(AUDIT, new_audit)
wr(ITER, new_iter)
wr(DECISIONS, new_decisions)
wr(CHANGELOG, new_changelog)
wr(BACKLOG, new_backlog)
wr(STATE, new_state)
print("LEDGERS_R419_OK audit=%d iter=%d decisions=%d changelog=%d backlog=%d state=%d"
      % (len(new_audit), len(new_iter), len(new_decisions), len(new_changelog),
         len(new_backlog), len(new_state)))
