# -*- coding: utf-8 -*-
"""R557 ⓪ 开工节：CI 五跑读单 + 基线全现读 + 禁碰逐字抄。"""
import io

P = 'AGENT_STATE.md'
s = io.open(P, encoding='utf-8').read()

anchor = u'## R556 状态（2026-11-02 · 第 555 轮 / Round 553 · 产品 5 文件 + 判据 2 文件 + 三把刀）'
assert s.count(anchor) == 1, s.count(anchor)

body = u"""## R557 ⓪ 开工（2026-11-02 · 第 556 轮 / Round 554 · CI 读单 + 基线全现读）

> 本节是**开工节**，不是轮次节（标题不写「状态」两字 —— `product_streak.py` 按第一个 `## Rnnn 状态（` 认当前轮）。

**前置实读**：`git log --oneline -3` = `58851c2` / `ccab101` / `680aea3`；已跟踪改动 **0**；ahead=**0**（HEAD=origin=`58851c2`）。

**① CI 五跑（只登记、不轮询；in_progress/queued 一律 NOT-RUN；已 concluded 的不重取）**
- `41442000018 ↔ eb883ad`（R556 ⓪ 笔）concluded=**success**、JOB build-and-test success、**失败步骤 0 条** ⇒ 复核通过（这一跑含 R556 之前的全部代码，STEP[9] 连续第二跑绿）。
- `41450045802 ↔ 5ba5b2f`（R556 刀表笔，覆盖产品笔 `1a7e31c`）状态 **in_progress** ⇒ **NOT-RUN**。`gh run view --log` 对它直接回 "logs will be available when it is complete" ⇒ **本轮新加的 `MOTION_MARKDOWN_MODE_FADE … 窗口= / 每格= / 相邻帧差=[…]` 三个 runner 真数一个都没到**。
- `41450081248 ↔ 680aea3`（台账笔）**in_progress** ⇒ NOT-RUN；`41450601769 ↔ ccab101`（补记笔）**in_progress** ⇒ NOT-RUN；`41452722560 ↔ 58851c2`（更正笔）**queued** ⇒ NOT-RUN。队列拥堵（该跑前面排 3 个）。
- 既有红对照：`4139930389`（写作 `41439930389 ↔ 78e7ab5`）concluded=failure，全部失败步骤 = **STEP[15] Swift tests** + **STEP[18] On-screen probe coverage floor**，红名 = `SelectionRevealAnimationTests/testProductDurationRevealStillMovesOverTime`（`[0.0, 1430.0, 1430.0, 1430.0, 1430.0]`）+ `testFrameIntervalsUnderStateChanges` **181.6ms / 2 颗**（622 第十二值）⇒ **同族既有红，本轮未碰该卷**，仍照实在账。
- **后果写清楚**：629 的 (A) 加密录制 / (B) 换判据对象 这两条**修法相反**的路，选择依据正是那三个数；数没到 ⇒ 本轮 **629 = NOT-RUN（具名：等 `41450045802`）**，不靠猜选一条，也不许动 ≥2 帧地板去"绕过"它。

**② 基线（本轮全部现读）**：帧 **354**（`docs/frame_baseline.json`）；清账 **162/63/0**；streak **1**（`python3 scripts/product_streak.py --streak-for 556` 现读，last=`1a7e31c`/555 ⇒ R556 落了产品 5 文件，这一格从 1 重新起算）；HIDDEN **表=429 可判=1183 rot=0 抽不出=6 已声明表=6 已声明死针=0 处置=ok**；预检 **tables=342 covered=295 arms=757 bad=0**、`ARM_TOTAL files=435 arms=1244 dupes=0 repeats=0`；电池 **695/5**（开场即复跑，`Ran 695 tests in 85.895s` / `OK (skipped=5)`）；安装 **433=433** + `INSTALL_SIGNATURE=local`（R556 现读，PID 86092）；全量 **1396/55/0（709.7s）** 是 R556 现读，本轮产品一旦动就重跑。

**③ 禁碰清单（现读逐字抄自 `AGENT_STATE.md` 的 R556 节 ⑤ 与 R555 节 ⑤，共 9 面）**：R546 登录失败图标、R547 默认行锁、R548 250pt 批量标题、R549 无序列表符号、R550 浮层提示键名、R551 收藏星尺寸、R552 折叠过渡、R553 固定码签身份链、R555 收藏星判据的倍率口径。本轮九面一律不动；4.5 地板、150 上限、120ms 阈值、Motion ≥2 帧地板、2x 的 8.0pt 跨度地板、1x 的 6.0pt 整行地板全部冻结。

**④ 本轮靶**
- **(a) 629 = NOT-RUN**（见 ① 的后果行）：三个 runner 真数没到，(A)/(B) 不选。挂给 R558 必读 `41450045802`。
- **(b) 632 的「文本同一次渲染只开一次」**：先量旧值 —— 一次展开 + 每次宽度变化各开几次（计数器 `ProtectedFileAccessLedger` 已在，只存哈希、不落盘、不全局 reset）。落得了就带负向臂与刀；落不了就把"为什么现在落不了"写成**修法相反且有名字的出口**（今天两条路各自要付什么代价），续单不静默。
- **(c) 真实推进（换新类别）**：把 R556 留在注释里的那格监控升级成**会红的判据** —— 「若有夹具把真实存在的图片路径装进侧栏行，`.task` 的异步补图会破坏帧确定性」。上一轮开的口子上一轮补：注释里的分类法等于没有（memory 那条规矩）。
- 633 仍等用户人工回执；622/624/627 继续；628/625/626/569/616 不重开；刀号 **M1443** 起。

"""

s = s.replace(anchor, body + anchor, 1)
io.open(P, 'w', encoding='utf-8').write(s)
print('R557 ⓪ written')
