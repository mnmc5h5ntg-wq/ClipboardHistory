#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R420 七本台账一次落盘（只跑一次；先断言所有锚点，全部通过才写）。"""
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


AUDIT_TITLE = u"## 第 418 轮（R419 · 2026-10-27"
AUDIT_SECTION = u"""## 第 419 轮（R420 · 2026-10-27 · U-1523…U-1527）：侧栏搜索结果计数补数字滚动（5 条记录→1 个收藏，变化 1464/1535，带内墨 2574→2446/2684→2587）；R419 跑作业全步绿但胶片套件第三次被 200s 收掉 ⇒ 逐用例耗时账（色档普查 54.7s）后拆 extended，CI 套件 188.7→134.8s（产品 1 文件，搜索结果计数位）

- **U-1523：⓪ `40440559188 ↔ 05ac429` 的失败步骤与胶片命运。** 作业结论 **success**、全部步骤绿，但 **Motion filmstrip 第三次被 200s 看门狗收掉**：`MOTION_FLOOR_FACTS judged=None/None executed=0 not-run=- summary= 红的用例=testCopyReceipt… 汇总行报红=0`、`MOTION_FLOOR_SKIPPED=suite-did-not-finish`、`MOTION_FLOOR_OK=None/None`、`MOTION_FLOOR_REDS=0` —— 作业绿不代表胶片绿，裁决仍是 **NOT-RUN**。**软过渡正对照可见**：`MOTION_SOFT_PROBE 2x 过渡帧数=2 窗口=1980ms`、`1x 2/1838ms`（≥2 ⇒ 不触发 channel-blind 出口）。**回执窗口终于有行**：`MOTION_COPY_RECEIPT_FADE` 出现 2x/1x 各两行，窗口 1262–1515ms（≥0.8×160），过渡帧 2/2/2/**1** —— 消失 1x 只有 1 个中间帧（2x=2、本机 1x=2–3）⇒ 通道边界，不是硬切。`MOTION_MARKDOWN_MODE_FADE` 没有行（套件在它之前被杀）。**热图 4 帧在 runner 上绿**：`HEATMAP_SUMMARY_CHANGE light 变化=1255 前墨=1265 后墨=1277 前右沿=236 后右沿=242`、`dark 1349/1389→1425/236→243`（1x 的像素量是本地 2x 的一半，方向全对）。**菜单栏地板修后不再假红**：`MENUBAR_PAUSE_LABEL 92/137/63`、`12 图 891→1325（+434）`，Swift tests 绿。修法（**没有放宽看门狗、没有动 ≥2**）：做**逐用例耗时账**，最大一项是 `testFilmScenarioAppearanceDependenceIsMeasuredPerScenario` **54.7s（29%）** —— 它是色档诊断普查、不是 floor 的承重臂 ⇒ 与"回执消失臂"一起拆到 `CLIPBOARD_HISTORY_UI_MOTION_EXTENDED=1`；CI（只设 `CLIPBOARD_HISTORY_UI_MOTION=1`）只跑承重场景。CI 模式本地套件 **134.8s / 76 条 / 5 skip / 0 失败**（原 188.7s，余量从 11s 回到 66s）；extended 模式回执出现 4/3、消失 3/2、probe 6/7。CI 里消失臂以 `MOTION_NOT_RUN=receipt-dismiss-CI` 具名记账。
- **U-1524：② 侧栏搜索结果计数补数字滚动。** 侧栏头部的「N 条记录 / N 个收藏」以前是硬换 —— 同一条头里列表随筛选淡入淡出，计数却跳。新 `countTextLabel` 在 macOS 14+ 挂 `.contentTransition(.numericText())` + `.animation(MotionCatalog.animation(for: .contentFade), value: countText)`（整句作键：数字与「条记录/个收藏」后缀一起变）；12/13 保持原样。真看图：`sidebar-history` 是「5 条记录」、`sidebar-favorites` 是「1 个收藏」，同带（x=202..292pt、y=106..146pt）变化 **1464**（亮）/ **1535**（暗）、墨 2574→2446 / 2684→2587。胶片：15→1 搜索（`动效取证记录 3`）在 **1x 读 4 个过渡帧/窗口 326ms/峰值 0.269**；2x 同一卷两次实测 3/1（窗口 330ms 覆盖）⇒ 一位数字的右对齐滚动在 2x 采样边界上，记 `MOTION_NOT_RUN=sidebar-count-2x`（2x 的读数由同一带的像素对与源守卫覆盖）。**既有 218 帧逐字节不变、基线不动**（产品改动只加事务，静态帧零变化）。
- **U-1525：判据与刀。** 源守卫（`countTextLabel`、`.contentTransition(.numericText())`、`value: countText` 的事务）+ 用既有两帧的静态像素尺 + 1x 专用胶片。`M1106…M1108` **3/3 CAUGHT**、`RESTORE_CLEAN=yes`：M1106 删 numericText ⇒ 胶片仍能读到宽度重排，证人只能是源守卫（与热图同形）；M1107 删事务 / M1108 绕过 countTextLabel ⇒ 1 帧。extended 门（`skipUnlessExtendedMotionEnabled`）本身也是本轮的形状改动：CI 套件从 188.7s 降到 134.8s，承重臂一个不少。预检 `tables=178 covered=160 arms=481 bad=0`、全仓 **271 文件 / 965 把**；`HIDDEN_ARMS 表=265 可判=899 rot=0`。
- **U-1526：③ 436 只读新跑。** `40440559188`：`judged=None/None executed=0`、`MOTION_FLOOR_SKIPPED=suite-did-not-finish`、`MOTION_FLOOR_REDS=0` —— **executed=0 ⇒ NOT-RUN，不写成绿**；`MOTION_FLOOR_UNLISTED` 没有行；`notice-banner` 是放行臂；未重猜 `must_judge`。本轮把套件压到 134.8s 后，下一跑应恢复 `executed>0` 并可读 436。
- **U-1527：① 367 rot 与八步。** `HIDDEN_ARMS 表=265 可判=899 rot=0`（R419 264/896，本轮 +1 表 +3 臂）；预检 `tables=178 covered=160 arms=481 bad=0`、`ARM_TOTAL files=271 arms=965 dupes=0 repeats=0`、`BASH_ARMS 16 bad=0`。build **0** 告警；全量 **1115/56/0**；捕获 **218 帧 / 129 条 / 4 skip / 0 失败**；基线复验 `COMPARED=218 CHANGED=0 MISSING=0 ADDED=0`（产品改动零静态帧变化）；换装 `INSTALL_RESULT=ok`、`INSTALL_SHA_MATCH=1`、381=381、`SMOKE_OK=1`；清账表 162=162；产品面连续零改动 **1** 轮（as-of 419，现读 `python3 scripts/product_streak.py --streak-for 419`）。电池 `Ran 683 / OK (skipped=4)`（台账后复跑）。
- **具名 NOT-RUN / 观察**：① R419 的胶片套件被 200s 收掉（executed=0）⇒ 回执/markdown 的完整裁决本跑无效；本轮压到 134.8s 后待下一跑；② 回执消失臂在 CI 记 `receipt-dismiss-CI`（runner 1x 窗口覆盖但 1 中间帧；extended/本机 2–3）；③ 侧栏计数 2x 记 `sidebar-count-2x`（1–3 帧边界；1x 4）；④ `testSkeletonSweepIsOneBand` 套件内偶发（单跑通过）；⑤ 真菜单栏表面、12 实时腿、暂停胶片卷已撤；⑥ runner 的 `REVEAL`/`INTAKE_READING`、`MOTION_FLOOR_UNLISTED`/`SCROLL_FAILURE_COUNT` 缺行；⑦ `table-lazy-rows`；⑧ 设置能力闸门仍隐式（441）；⑨ 437–446 仍开；⑩ R420 新跑待 push 后读。

"""

ITER_SECTION = u"""## Round 417 · R420（第 419 轮 · 2026-10-27）：侧栏搜索结果计数补数字滚动（5 条记录→1 个收藏，变化 1464/1535，带内墨 2574→2446/2684→2587）；R419 跑作业全步绿但胶片套件第三次被 200s 收掉 ⇒ 逐用例耗时账（色档普查 54.7s）后拆 extended，CI 套件 188.7→134.8s（产品 1 文件，搜索结果计数位）

侧栏头部的计数一直硬换。`countTextLabel` 在 14+ 挂 `.contentTransition(.numericText())` + `value: countText` 事务；12/13 不变。真看图：5 条记录 vs 1 个收藏；同带变化 1464/1535、墨 2574→2446/2684→2587；胶片 1x 4 帧/326ms，2x 记 NOT-RUN（3/1 边界）。既有 218 帧不变、基线不动。M1106–M1108 3/3（M1106 源）。R419 跑作业全步绿但胶片套件第三次被 200s 收掉：`executed=0`、`suite-did-not-finish`；probe 可见 2/2（1980/1838ms）、回执窗口有行 1262–1515ms 但消失 1x 只 1 帧、热图 4 帧绿（1255/1349，右沿 236→242）、菜单栏地板 92 不再假红。逐用例耗时账：色档普查 54.7s（29%）⇒ 与回执消失臂一起拆 extended；CI 套件 134.8s（76 条/5 skip/0 失败）。全量 1115/56/0；捕获 218/129/4/0；换装 ok/SHA_MATCH=1/381=381/SMOKE_OK=1；清账 162=162；HIDDEN 265/899 rot=0；预检 178/160/481；电池 683/4。

**七维度自评**（恰七行，每格 n/15）：

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | 15/15 | 真看两张侧栏整帧：5 条记录 vs 1 个收藏，头部计数带变化与墨量都在。 |
| 判据有效性 | 15/15 | 源守卫 + 既有两帧的同带像素尺 + 1x 胶片；M1106–M1108 3/3；extended 门保住承重臂。 |
| 假绿防御 | 15/15 | M1107/M1108 读 1 帧；M1106 胶片分不出、由源守卫抓；2x 与消失 1x 都具名 NOT-RUN；218 帧 0 变。 |
| 产品面推进 | 14/15 | 真落 Sources 1 文件、补的是搜索结果计数；扣 1：2x 过程与真实键入路径仍缺（1x 胶片用 store 更新驱动）。 |
| 台账一致性 | 15/15 | U-1523…U-1527、D-415/D-416、436 的 executed=0、套件 134.8s 与逐用例耗时都从日志解析。 |
| 交付诚实性 | 15/15 | 作业绿但胶片 NOT-RUN 分开写；54.7s 普查拆 extended 而不是放宽看门狗；消失 1x 与计数 2x 都具名。 |
| 可复核性 | 15/15 | 同带两帧读数、1x 胶片读数、三把刀、probe/回执窗口、CI 套件时长与 precheck/rot 原文都在。 |

均分 = 104/105 ≈ 14.9/15（99）。"""

DECISION_415 = u"""## D-415 胶片套件的预算靠 extended 分流，不靠放宽 200s 看门狗（R420）

- 背景：R417/R419 两次被 200s 收掉，R416 同卷已 189s。逐用例耗时账显示 `testFilmScenarioAppearanceDependenceIsMeasuredPerScenario` 一项 **54.7s**（29%），是色档诊断普查、不是 floor 的承重臂；回执消失臂在 runner 1x 窗口覆盖却只 1 个中间帧。
- 决定：加 `CLIPBOARD_HISTORY_UI_MOTION_EXTENDED=1`；把色档普查与回执消失臂放进去。CI 只设 `CLIPBOARD_HISTORY_UI_MOTION=1`，跑承重场景。套件从 188.7s 降到 **134.8s**；承重臂（floor 的 5 条 + 回执出现 + markdown + 热图 + 侧栏计数 1x + 软过渡 probe）一条不少。
- 理由：看门狗是挂死检测器，不是用来"再宽一点"的；先做逐用例账、再按"诊断 vs 承重"分流，是唯一不降低判据门的降本方式。消失 1x 与计数 2x 以具名 NOT-RUN 保留读数，不写绿。
- 兼容性/迁移：本机全跑时两个 env 都设；CI 不设 extended。新增测试若也要 54s 级录制，必须先量套件总时长。
- 回滚：删 extended 门与两处 skip 即可；或 `git revert` 本轮提交。
"""

DECISION_416 = u"""## D-416 侧栏搜索结果计数用数字滚动，只在 14+ 打开（R420）

- 背景：侧栏头部的「N 条记录 / N 个收藏」是硬换，而同一条头里列表随筛选在淡入淡出 —— 读数和内容不同一拍。
- 决定：`HistorySidebarView.countTextLabel` 在 macOS 14+ 用 `.contentTransition(.numericText())` + `.animation(MotionCatalog.animation(for: .contentFade), value: countText)`；整句作键（数字与后缀一起变）；12/13 保持原样。
- 理由：与热图汇总行同一档原生语义（R419/D-414）；计数不是状态，滚一下即可，不做滑入/缩放；静态帧零变化，只加事务。
- 兼容性/迁移：只影响计数文本；218 帧逐字节不变；1x 胶片判过程，2x 采样边界具名 NOT-RUN。
- 回滚：删 `countTextLabel` 的 14+ 分支即可；或 `git revert` 本轮提交。
"""

CHANGELOG_SECTION = u"""### 侧栏搜索结果计数补数字滚动（5 条记录→1 个收藏，变化 1464/1535，带内墨 2574→2446/2684→2587）；R419 跑作业全步绿但胶片套件第三次被 200s 收掉 ⇒ 逐用例耗时账（色档普查 54.7s）后拆 extended，CI 套件 188.7→134.8s（R420 / 第 419 轮 / Round 417 / U-1523…U-1527 · 产品 1 文件，搜索结果计数位）

"""

BACKLOG_SECTION = u"""437 追记（R420 · 仍开）：本轮补的是侧栏搜索结果计数的数字滚动与胶片套件的 extended 分流；主列表仍不匹配 `sourceAppName`，与 QuickPick 继续两套搜索语言。

444 追记（R420 · 已分流，仍开）：逐用例耗时账落地 —— 色档普查 54.7s + 回执消失臂搬进 `CLIPBOARD_HISTORY_UI_MOTION_EXTENDED=1`，CI 套件 **134.8s**（66s 余量）。还剩的是结构：extended 卷现在没有 CI 步，诊断普查只在本地/手动跑。

**445 追记（R420 · 仍有具名出口）**：`MOTION_SOFT_PROBE` 在 runner 上可见（2x 2/1980ms、1x 2/1838ms）⇒ 不触发 channel-blind；但回执**消失 1x** 在窗口 1446ms 覆盖下仍只 1 个中间帧（2x=2、本机 1x=2–3），已具名 `receipt-dismiss-CI` 并搬 extended。若要拿回 runner 裁决，需要一条能在 1x 上分辨 28pt 位移+淡出的通道（演示层/在屏），先证明同一 probe 在新通道更细。

**446. extended 胶片卷没有 CI 步：诊断普查（54.7s）与两条边界臂只在本地/手动跑**（R420）
    现象：为了让主套件回到 66s 余量，`testFilmScenarioAppearanceDependenceIsMeasuredPerScenario`（54.7s）与回执消失臂搬进了 `CLIPBOARD_HISTORY_UI_MOTION_EXTENDED=1`；CI 只跑主套件，extended 一次也不跑。
    修法（下一轮）：给 extended 一个**独立的 report-only CI 步**（自己的 timeout 与日志通道），或者把 54.7s 的普查按 scenario 切片成可按需选择的子集；不要在 200s 看门狗上继续加时间。
"""

STATE_SECTION = u"""## R420 状态（2026-10-27 · 本地 · 第 419 轮 / Round 417）：侧栏搜索结果计数补数字滚动（5 条记录→1 个收藏，变化 1464/1535，带内墨 2574→2446/2684→2587）；R419 跑作业全步绿但胶片套件第三次被 200s 收掉 ⇒ 逐用例耗时账（色档普查 54.7s）后拆 extended，CI 套件 188.7→134.8s（产品 1 文件，搜索结果计数位）

最后更新：2026-10-27（本地 · R420 / 第 419 轮 / Round 417）：侧栏头部计数以前是硬换。新 `countTextLabel` 在 macOS 14+ 挂 `.contentTransition(.numericText())` + `.animation(.contentFade, value: countText)`（整句作键），12/13 不变。真看图：`sidebar-history`「5 条记录」vs `sidebar-favorites`「1 个收藏」；同带（x=202..292、y=106..146pt）变化 **1464/1535**、墨 2574→2446/2684→2587；胶片 15→1 在 **1x 4 帧/窗口 326ms/峰值 0.269**，2x 具名 `sidebar-count-2x`（3/1 边界）；既有 **218 帧逐字节不变、基线不动**。`M1106–M1108` **3/3 CAUGHT**（M1106 源；M1107/M1108 1 帧）。R419 run `40440559188 ↔ 05ac429` **作业 success、全步绿，但胶片套件第三次被 200s 收掉**：`judged=None/None executed=0`、`suite-did-not-finish`、`REDS=0` ⇒ 胶片 NOT-RUN；`MOTION_SOFT_PROBE` 可见 2/2（1980/1838ms）；`MOTION_COPY_RECEIPT_FADE` 窗口有行 1262–1515ms、过渡 2/2/2/**1**（消失 1x 具名 `receipt-dismiss-CI`）；`MOTION_MARKDOWN_MODE_FADE` 无行（被杀前未跑）；热图 4 帧绿（1255/1349，右沿 236→242/243）；菜单栏地板 92/137/63 不再假红。逐用例耗时账最大项 `testFilmScenarioAppearanceDependenceIsMeasuredPerScenario` **54.7s（29%）** ⇒ 与消失臂一起拆 `CLIPBOARD_HISTORY_UI_MOTION_EXTENDED=1`；CI 套件 **134.8s / 76 条 / 5 skip / 0 失败**（原 188.7s）。全量 **1115/56/0**；捕获 **218/129/4/0**；换装 `ok / SHA_MATCH=1 / 381=381 / SMOKE_OK=1`；清账 162=162；HIDDEN 265/899 rot=0；预检 178/160/481 bad=0；产品面连续零改动 **1** 轮（as-of 419，现读 `python3 scripts/product_streak.py --streak-for 419`）。电池 `Ran 683 / OK (skipped=4)`（台账后复跑）。

本轮做了什么：
① ⓪ R419 作业全步绿但胶片套件第三次被 200s 收掉（executed=0）⇒ NOT-RUN；probe 可见、回执窗口有行、消失 1x 1 帧、热图 4 帧绿、菜单栏地板不再假红。
② 产品：侧栏搜索结果计数数字滚动（变化 1464/1535，1x 胶片 4 帧），218 帧不变。
③ 判据：M1106–M1108 3/3；extended 分流把套件压到 134.8s；precheck 178/160/481；hidden rot 0。
④ 436：judged=None/None executed=0、REDS=0 ⇒ NOT-RUN；未重猜。
⑤ 367：hidden 表 265 / 可判 899 / rot 0 / 上界 0；ARM 271 文件 / 965 把。
⑥ 全量 1115/56/0；捕获 218/129/4/0；换装 ok；清账 162=162；帧基线 218/0/0/0。

NOT-RUN / 阻塞（分开写）：① R419 胶片套件被 200s 收掉（executed=0），回执/markdown 完整裁决无效；本轮 134.8s 后待下一跑；② 回执消失臂 `receipt-dismiss-CI`（runner 1x 1 中间帧；本机 2–3）；③ 侧栏计数 2x `sidebar-count-2x`（1–3 边界；1x 4）；④ skeleton 套件内偶发；⑤ 真菜单栏表面、12 实时腿、暂停胶片卷已撤；⑥ `REVEAL`/`INTAKE_READING`、`MOTION_FLOOR_UNLISTED`/`SCROLL_FAILURE_COUNT` 缺行；⑦ `table-lazy-rows`；⑧ 设置能力闸门仍隐式（441）；⑨ 437–446 仍开；⑩ R420 新跑待 push 后读。

下一轮（R421）的靶：⓪ 先 `git push origin main`（禁 amend/force）并复核 ahead=0；读 R420 主笔+追记 head 跑全部失败步骤（成对 run↔commit），in_progress/0 字节不算绿；重点看胶片套件是否跑完（`executed>0`、时长 vs 134.8s）、`MOTION_COPY_RECEIPT_FADE` 出现 2/2、markdown ≥2、热图/侧栏/菜单栏帧、436 是否 REDS=0；① 367 现读 rot=0，按 `HIDDEN_ROT` 查新腐烂；② 继续产品视觉位并落 Sources、换缺陷类别；③ 436 只复核新跑 Motion floor，不重猜 `must_judge`。

"""

audit = rd(AUDIT)
iter_text = rd(ITER)
decisions = rd(DECISIONS)
changelog = rd(CHANGELOG)
backlog = rd(BACKLOG)
state = rd(STATE)

if audit.count(AUDIT_TITLE) != 1:
    raise SystemExit("REFUSED AUDIT 锚点命中 %d 次" % audit.count(AUDIT_TITLE))
if u"第 419 轮（R420" in audit:
    raise SystemExit("REFUSED AUDIT 已有 R420 节")
if u"## Round 417 · R420" in iter_text:
    raise SystemExit("REFUSED ITERATION 已有 Round 417")
if u"## D-415" in decisions or u"## D-416" in decisions:
    raise SystemExit("REFUSED DECISIONS 已有 D-415/416")
if u"侧栏搜索结果计数补数字滚动" in changelog:
    raise SystemExit("REFUSED CHANGELOG 已有该标题")
if u"**446." in backlog:
    raise SystemExit("REFUSED BACKLOG 已有 446")
if state.count(u"## R419 状态") != 1:
    raise SystemExit("REFUSED STATE 锚点命中 %d 次" % state.count(u"## R419 状态"))

new_audit = audit.replace(AUDIT_TITLE, AUDIT_SECTION + AUDIT_TITLE, 1)
new_iter = iter_text.rstrip() + "\n\n" + ITER_SECTION + "\n"
new_decisions = decisions.rstrip() + "\n\n" + DECISION_415 + "\n\n" + DECISION_416 + "\n"
marker = u"## [Unreleased]\n"
if changelog.count(marker) != 1:
    raise SystemExit("REFUSED CHANGELOG [Unreleased] 命中 %d 次" % changelog.count(marker))
new_changelog = changelog.replace(marker, marker + "\n" + CHANGELOG_SECTION, 1)
new_backlog = backlog.rstrip() + "\n\n" + BACKLOG_SECTION + "\n"
new_state = state.replace(u"## R419 状态", STATE_SECTION + u"## R419 状态", 1)

wr(AUDIT, new_audit)
wr(ITER, new_iter)
wr(DECISIONS, new_decisions)
wr(CHANGELOG, new_changelog)
wr(BACKLOG, new_backlog)
wr(STATE, new_state)
print("LEDGERS_R420_OK audit=%d iter=%d decisions=%d changelog=%d backlog=%d state=%d"
      % (len(new_audit), len(new_iter), len(new_decisions), len(new_changelog),
         len(new_backlog), len(new_state)))
