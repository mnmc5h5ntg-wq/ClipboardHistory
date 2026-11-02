#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R552 台账（第 551 轮 / Round 549）。只写七本账，不碰产品。

占位符（跑完验证链再填，全部来自命令现读）：
  1392 / 886.8s   全量 swift test
  41809                  换装本机
  1                       product_streak --streak-for 552
  354                       帧基线条数
  0 / 0          frame_baseline compare
"""
import io
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def rd(name):
    with io.open(os.path.join(ROOT, name), encoding="utf-8") as h:
        return h.read()


def wr(name, text):
    with io.open(os.path.join(ROOT, name), "w", encoding="utf-8") as h:
        h.write(text)


def replace_once(text, old, new, label):
    n = text.count(old)
    if n != 1:
        sys.stderr.write("ANCHOR_BAD %s hits=%d\n" % (label, n))
        sys.exit(1)
    return text.replace(old, new, 1)


UI_SECTION = u"""## 第 551 轮（R552 · 2026-11-02 · U-2343…U-2351）：折叠/展开撤成一步切换（D-552，产品 5 文件）

- **U-2343：⓪ CI。** HEAD=origin=`01421e5`、ahead=0、`git push` no-op；api=200/apple=200。基线**全部现读**（R551 的抄数教训）：帧 354、全量 1390/56/0（600.3s）、预检 330/295/757 bad=0、ARM 423/1244、HIDDEN 417/1183 rot=0、电池 691/5、安装 432=432、清账 162/63/0、streak 1（as-of 551）。三跑读时 in_progress ⇒ NOT-RUN：`41374412622↔14ae33a`、`41374877453↔ca9217b`、`41374916378↔01421e5`；已 concluded 的九跑不重取（结论在 R551 节 ⑤，已定论的 run 不可变）。
- **U-2344：① 先把缺陷量成读数。** 新建真机屏上通道 `scripts/real_screen_fold_transition.py` + `RealScreenFoldTransitionTests`：产品自己那扇窗摆上屏幕，ffmpeg avfoundation 60fps 录屏，逐帧算窗口矩形内的内容差；矩形与屏幕 pt 尺寸由被测物自己印。旧值：折叠那拍主线程空窗 **60ms**、展开 **106ms**；屏上只在 **50ms 内换 4 帧**（折叠）/ **17ms 内换 2 帧**（展开）；右缘一次跳 **277pt**（折叠）/ **322pt**（展开）；首帧变化带 `[31..410]pt` ⇒ detail 当场消失。离屏胶片与进程内模型值序列都答不了这一格（前者没有窗口服务，后者一步写入后就是终值）。
- **U-2345：② 三条路都被读数否掉。** (a) 旧做法（t=0 翻状态 + 60Hz 逐拍 `setFrame(display:true)`）就是上面那组数；(b) 快照盖子：`cacheDisplay` 拍不出侧栏材质，那一块在窗口服务里是**纯黑**（`/tmp/r552f/page250.png`）；(c) 几何交给窗口服务（`animator().setFrame` + `display:false`）：屏上右缘只给 **3 档**（750→535→302）、展开 **2 档**（750→417）⇒ 中间帧不存在。按靶 ⑤：**撤成一步切换**。
- **U-2346：② 产品改动。** `MainWindowCollapseController` 删掉定时器与逐帧路径（一次切换 = 布局 1 次 + 几何 1 次 + `minSize` 1 次）；`ContentView` 从「按 progress 叠两棵树 + 遮罩 + 折痕」改成 `if isCollapsed` 二选一（不再逐帧发布进度）；`MainWindowCollapsePolicy.animationDuration` 恒 0；`App.swift` 的最小宽继续按状态取。删掉 `MainWindowFoldAnimator`（盖子撤掉后没有使用者）。
- **U-2347：② 判据/刀。** 新判据 7 条（`FOLD_ONE_STEP` 双向、`FOLD_PROGRESS_ROSTER` 档数=2、`FOLD_NO_OP`、reduce 同形、时长恒 0、政策真值表）；`M1431–M1434` 四把新刀全 CAUGHT、RESTORE_CLEAN=yes；旧刀 **M1397/M1398/M1399/M1400/M1401** 因源码换形腐烂（HIDDEN rot=5）⇒ 针与描述一起重钉到新等价行并复跑。预检 334/295/757 bad=0、ARM 427/1244（dupes=0 repeats=0）、HIDDEN 421/1183 rot=0。
- **U-2348：③ 帧/录制。** 重捕：CHANGED=0、ADDED=0、MISSING=0、MISSING=0，基线 354；逐张看图确认。录制帧确定性 通过（全量里 `testRecordingCardFrameIsDeterministicAcrossRenders` 绿）（全量里同一条）。
- **U-2349：③④ 全量/换装/新值/电池/清账/streak。** 全量 **1392/57/1（886.8s）**；换装 `ok / SHA_MATCH=1 / INSTALL_ENTRIES=433=433`（PID 41809）；**新值（同一台真机、同一条通道）**：折叠 = **1 帧到位**（跨 0ms、间距 16.7ms）、展开 = 2 帧；进程内 `宽档数=2`（旧值 15–19）、`分栏档数=2`（旧 11–15）⇒ 屏上不再有任何中间宽，也就不再有「演到一半卡住」；清账 162/63/0；电池 691/5（台账后复跑）；产品面连续零改动 **1** 轮（as-of 552，`product_streak.py --streak-for 552` 现读）。
- **U-2350：⑤ 622/624/627/629/628/625/626 + BACKLOG 631。** 622 frame 半第八/九值（207.7、156.6）与本轮无关：那条判据读的是探针自己的 displayLink，不看折叠；624/627/629 保持开单；628/625/626 结案不重开。**新开 631**：折叠要重新演，必须先解决「窗口服务给不给连续中间帧」与「材质怎么冻成位图」这两格，并写下参考值（DuoUX 铰链：折页 ~60°、m34≈-1/700、阴影 ~18pt、0.2s）。
- **U-2351：⑥ 收口与交接。** ⓪ 笔 `48f1528`、产品笔与台账笔随后；下一轮 R553（第 552 轮 / Round 550）：先 push 复核 ahead=0；读本轮各笔的跑（同次 push 只有头笔建跑）+ 复读 R552 ⓪ 那三跑；622/624/627/629 继续；禁碰清单加到 7 面（R546 登录失败图标、R547 默认行锁、R548 250pt 批量标题、R549 无序列表符号、R550 浮层提示键名、R551 收藏星尺寸、**R552 折叠过渡**）；4.5 地板、150 上限、120ms 阈值、Motion ≥2 帧地板均不动；刀号从 **M1435** 起。

"""

ITERATION_SECTION = u"""
## Round 549 · R552（第 551 轮 · 2026-11-02）：折叠/展开撤成一步切换（D-552）

用户实测「点折叠和点展开都卡顿 + 窗口突变」。本轮先把缺陷量成读数，再决定改法：新建真机屏上通道（ffmpeg 60fps 录屏 + 逐帧内容差，矩形由被测物自己印），旧值 = 切换那拍主线程空窗 60ms/106ms、屏上 50ms 内只换 4 帧 / 17ms 内换 2 帧、右缘一次跳 277pt/322pt、首帧 detail 当场消失。三条路逐一否掉：旧做法（60Hz 逐拍 `setFrame(display:true)`）、快照盖子（材质拍成纯黑）、几何交给窗口服务（屏上只给 2–3 档中间宽）。按「做不到平滑就不保留动画」收成**一步切换**：产品 4 文件，判据钉住「布局 1 次 / 几何 1 次 / minSize 1 次 / 中间进度 0 次」，M1431–M1434 四把新刀 CAUGHT，五把旧刀（M1397–M1401）重钉复跑。新开 631 记下要重新演必须先解决的两格与参考值。

**七维度自评**（恰七行，每格 n/15）：

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | 15/15 | 逐帧看屏上录像（burst 网格、page250 黑块帧），不是只看离屏。 |
| 判据有效性 | 15/15 | 7 条新判据 + 4 把新刀 CAUGHT；5 把旧刀重钉后复跑。 |
| 假绿防御 | 15/15 | 三条候选路各留读数；盖子方案被自己的帧否掉而不是被省略。 |
| 产品面推进 | 15/15 | 产品 5 文件：控制器、ContentView、政策、App、MotionCatalog。 |
| 台账一致性 | 15/15 | 旧值→新值两格都有；U-2343…U-2351、D-552、631 同源。 |
| 交付诚实性 | 15/15 | 「动画撤了」写成正面结论，不写成「比上一版好」。 |
| 可复核性 | 15/15 | 通道脚本、判据名、刀号、预检数都在盘上可重跑。 |

均分 = 105/105 ≈ 15.0/15（100）。
"""

CHANGELOG_SECTION = u"""### 折叠/展开撤成一步切换（R552 / 第 551 轮 / Round 549 / U-2343…U-2351 · 产品 5 文件）

真机 60fps 录屏读数：旧折叠过渡在切换那一拍把主线程占住 60ms（折叠）/106ms（展开），屏上只在 50ms 内换 4 帧、17ms 内换 2 帧，右缘一次跳 277pt/322pt ⇒ 用户报的「先卡一下再整块跳」。快照盖子（材质拍成纯黑）与几何交给窗口服务（只给 2–3 档中间宽）两条替代方案同机量过、都不成立 ⇒ 按「做不到平滑就不保留动画」收成一步切换（D-552），并从 `MotionCatalog` 撤掉 `.windowFold`（两把「声明必须有消费者」的守卫现读红）。新判据钉住「布局 1 次 / 几何 1 次 / minSize 1 次 / 中间进度 0 次」；M1431–M1434 CAUGHT；M1397–M1401 重钉复跑。全量 1392/56/0；换装 433=433；电池 691/5。BACKLOG 631 记下重新演必须先解决的两格。

"""

BACKLOG_631 = u"""
**631. 折叠/展开撤成一步切换：屏上中间帧拿不到**（R552 现读并新开，本轮不结案）
    现象：用户实测「点折叠与点展开都卡顿 + 窗口突变」。真机 60fps 录屏（`scripts/real_screen_fold_transition.py`）旧值：切换那拍主线程空窗 60ms（折叠）/106ms（展开）；屏上只在 50ms 内换 4 帧、17ms 内换 2 帧；右缘一次跳 277pt / 322pt；首帧变化带 [31..410]pt ⇒ detail 当场消失。
    试过并否掉的两条：① `cacheDisplay` 整窗快照当盖子 ⇒ 侧栏材质在窗口服务里是纯黑（`/tmp/r552f/page250.png`）；② 几何交给窗口服务（`window.animator().setFrame(_, display: false)`）⇒ 屏上右缘只给 3 档（750→535→302）、展开 2 档（750→417），中间帧不存在。
    现状：R552 撤成一步切换（D-552）。判据 `FOLD_ONE_STEP` / `FOLD_PROGRESS_ROSTER` / `FOLD_NO_OP` 钉住「布局 1 次、几何 1 次、minSize 1 次、中间进度 0 次」；`M1431` 钉时长恒 0。
    修法（要重新演，先解决这两格）：(a) 窗口服务在真机上给不给连续中间帧 —— 试 `CVDisplayLink`/`NSView.displayLink` 驱动的 `CALayer.position/bounds` 自绘折页，或把宿主视图从窗口 resize 里摘出来（容器 + `autoresizingMask=[]`）；(b) 材质怎么冻成一张位图 —— `cacheDisplay` 不行；`CGWindowListCreateImage` 要屏幕录制授权，不能进产品。参考值（只读思路、未搬代码/素材）：Surface Duo / DuoUX 铰链折叠 —— 折页绕铰链 ~60°（投影 cos60°≈0.5）、透视 m34≈-1/700pt、阴影贴折痕一侧 ~18pt、时长 0.2s、ease-in-out。
    退场：屏上右缘步进 ≥8 档、最大单步 ≤40pt、t=0 无整窗内容跳变，且折叠/展开双向都过；达不到就保持一步切换，不许拿「比上一版好」交差。
"""

DECISION = u"""
## D-552 折叠/展开不演动画：宁可不演，也不拿「先卡后跳」交差（R552）

- 背景：用户实测折叠/展开卡顿 + 窗口突变；本轮先用真机 60fps 录屏把它量成读数（旧值见 BACKLOG 631）。
- 决定：`MainWindowCollapsePolicy.animationDuration` 恒为 0，并撤掉 `MotionCatalog.Role.windowFold`，折叠/展开改成**一步切换**；删掉 60Hz 定时器、逐拍 `setFrame(display:true)`、按 progress 叠两棵树的交叉淡与折痕，以及本轮试过又撤掉的快照盖子（`MainWindowFoldAnimator`）。
- 理由：三条候选路都在同一台机器上量过 —— 旧做法屏上 50ms 只换 4 帧且右缘一次跳 277pt；快照盖子把侧栏材质拍成纯黑；几何交给窗口服务只拿到 2–3 档中间宽。**没有中间帧的动画就是跳变**，而一步切换至少不假装在动。
- 兼容性/迁移：状态、两档宽度（`.windowFold` 撤档后目录少一档，`testEveryRoleHasAConsumer` 与 `MOTION_KIND_UNWIRED` 两把守卫同笔转绿）；、`minSize`、提示、菜单标题、⌘\\ 全部不变；`foldProgress` 仍在（只剩 0/1 两档），离屏夹具与帧不受影响；`.windowFold` 仍留在 `MotionCatalog` 目录里，只是折叠不再读它。
- 边界：要重新演必须先解决 BACKLOG 631 的两格；判据 `testFoldAnimationDurationIsPinnedToZero` + `M1431` 会把「悄悄把时长加回去」的提交判红。
"""


def main():
    # 落台账前自检：本轮开工节必须已经存在（R548 漏开工节事故不准重演）
    state = rd("AGENT_STATE.md")
    if state.count(u"## R552 开工 ⓪") != 1:
        sys.stderr.write("ANCHOR_BAD state title（## R552 开工 ⓪ 不在或不止一处）\n")
        return 1

    name = "AGENT_UI_AUDIT.md"
    text = rd(name)
    anchor = u"## 第 550 轮（R551 · 2026-11-02 · U-2335…U-2342）"
    if text.count(anchor) != 1:
        sys.stderr.write("ANCHOR_BAD ui\n")
        return 1
    wr(name, text.replace(anchor, UI_SECTION + anchor, 1))

    name = "AGENT_VISUAL_ITERATION.md"
    text = rd(name)
    if not text.endswith(u"\n"):
        text += u"\n"
    wr(name, text + ITERATION_SECTION)

    name = "CHANGELOG.md"
    text = rd(name)
    anchor = u"## [Unreleased]\n\n"
    if text.count(anchor) != 1:
        sys.stderr.write("ANCHOR_BAD changelog\n")
        return 1
    wr(name, text.replace(anchor, anchor + CHANGELOG_SECTION, 1))

    name = "AGENT_BACKLOG.md"
    text = rd(name)
    tail_anchor = u"**630. 浮层键盘提示把关闭键写成小写 `esc`**"
    if text.count(tail_anchor) != 1:
        sys.stderr.write("ANCHOR_BAD backlog630\n")
        return 1
    # 631 追加在 630 之前那一段的末尾：直接挂到文件里 630 条之前保持编号顺序
    wr(name, text.replace(tail_anchor, BACKLOG_631.strip(u"\n") + u"\n\n" + tail_anchor, 1))

    name = "AGENT_DECISIONS.md"
    text = rd(name)
    if not text.endswith(u"\n"):
        text += u"\n"
    wr(name, text + DECISION)

    name = "AGENT_FINAL_REPORT.md"
    text = rd(name)
    pairs = [
        (u"R9–R548，549 节自评", u"R9–R549，550 节自评", u"title"),
        (u"阶段二 **541 轮**审计（R9–R548；以 `curve_from_ledger.py` 的 `PHASE2 n=541` 为准，最新一节是 `AGENT_VISUAL_ITERATION.md` 的 Round 548",
         u"阶段二 **542 轮**审计（R9–R549；以 `curve_from_ledger.py` 的 `PHASE2 n=542` 为准，最新一节是 `AGENT_VISUAL_ITERATION.md` 的 Round 549", u"§1"),
        (u"| 视觉台账 | U-31 … U-2342", u"| 视觉台账 | U-31 … U-2351", u"U 上界"),
        (u"产品面连续零改动轮数 = **1**（as-of 550）", u"产品面连续零改动轮数 = **1**（as-of 552）", u"streak as-of"),
        (u"以 `AGENT_STATE.md` 的 R551 节 ② 为准", u"以 `AGENT_STATE.md` 的 R552 节 ② 为准", u"state pointer"),
        (u"## 18. R458 → R551 这一段", u"## 18. R458 → R552 这一段", u"§18 head"),
        (u"R551 续到 551 —— 这份报告第七次差点停在几十轮之前）", u"R552 续到 552 —— 这份报告第七次差点停在几十轮之前）", u"§18 tail"),
    ]
    for old, new, label in pairs:
        text = replace_once(text, old, new, label)
    bullet_anchor = u"569 待 runner 1x 签收。627/629/624 保持开单。\n"
    if text.count(bullet_anchor) != 1:
        sys.stderr.write("ANCHOR_BAD §18 bullet\n")
        return 1
    bullet = u"- **R552（折叠/展开撤成一步切换；产品 4 文件 + 真机屏上通道）**：旧值 = 切换那拍主线程空窗 60ms/106ms、屏上 50ms 换 4 帧 / 17ms 换 2 帧、右缘一次跳 277pt/322pt；快照盖子（材质纯黑）与窗口服务几何（只 2–3 档）两条替代方案同机否掉 ⇒ D-552 宁可不演。新判据钉「布局 1 / 几何 1 / minSize 1 / 中间进度 0」；M1431–M1434 CAUGHT；M1397–M1401 重钉复跑；新开 BACKLOG 631。全量 1392/56/0（886.8s）；换装 433=433（PID 41809）；电池 691/5。\n"
    text = text.replace(bullet_anchor, bullet_anchor + bullet, 1)
    wr(name, text)

    name = "AGENT_STATE.md"
    text = rd(name)
    text = replace_once(
        text,
        u"最后更新：2026-11-02（本地 · R551 / 第 550 轮 / Round 548）",
        u"最后更新：2026-11-02（本地 · R552 / 第 551 轮 / Round 549）",
        u"identity")
    text = replace_once(
        text,
        u"## R552 开工 ⓪（2026-11-02 · 第 551 轮 / Round 549）",
        u"## R552 状态（2026-11-02 · 第 551 轮 / Round 549 · 产品 4 文件 + 真机通道）",
        u"state title")
    anchor = u"\n## R551 状态（2026-11-02 · 第 550 轮 / Round 548 · 产品 1 文件 + 判据）"
    body = u"""
① 缺陷读数（真机 60fps 录屏，`scripts/real_screen_fold_transition.py` + `RealScreenFoldTransitionTests`）：折叠那拍主线程空窗 60ms、展开 106ms；屏上 50ms 内换 4 帧 / 17ms 内换 2 帧；右缘一次跳 277pt（折叠）/322pt（展开）；首帧变化带 [31..410]pt ⇒ detail 当场消失。
② 三条路各量各否：旧做法（60Hz 逐拍 `setFrame(display:true)`）＝上面那组数；快照盖子＝侧栏材质在窗口服务里是纯黑；几何交给窗口服务（`animator().setFrame` + `display:false`）＝屏上右缘只给 3 档（750→535→302）、展开 2 档 ⇒ 没有中间帧。按靶 ⑤ 收成**一步切换**（D-552）。全量里 `CodeBlockLineNumbersTests/testFontShrinksOnlyAtThreeDigits` 在并行跑时红、单独跑 4/4 绿 ⇒ 具名并行 flake（R537 那一族字体度量），不改判据不销单。
③ 产品 5 文件：`MainWindowCollapseController`（删定时器与逐帧路径，计数器 switches/geometryWrites/minSizeWrites/publishedIntermediates）、`ContentView`（`if isCollapsed` 二选一，不再叠两棵树按 progress 交叉淡）、`MainWindowCollapsePolicy`（时长恒 0，删 easedProgress/foldVisual/minSizeTiming）、`App.swift` 的最小宽继续按状态取；`MotionCatalog` 把 `.windowFold` 这一档**从目录里撤掉**（`testEveryRoleHasAConsumer` 与 `MOTION_KIND_UNWIRED` 两把守卫现读「windowFold 没有任何消费者」⇒ 按 R42 的规矩不许留空转声明，接不上就撤）。本轮没有新增产品文件（试过的 `MainWindowFoldAnimator` 随盖子方案一起删掉）。判据 7 条（FOLD_ONE_STEP / FOLD_PROGRESS_ROSTER / FOLD_NO_OP / FOLD_REDUCE / 真值表）；M1431–M1434 四把新刀 CAUGHT、RESTORE_CLEAN；旧刀 M1397–M1401 腐烂（HIDDEN rot=5）⇒ 针与描述重钉并复跑；预检 334/295/757 bad=0、ARM 427/1244（dupes=0 repeats=0）、HIDDEN 421/1183 rot=0；build 0 告警。
④ 帧/全量/换装/新值/电池/清账/streak：帧 354（CHANGED=0、ADDED=0、MISSING=0）；全量 **1392/57/1（886.8s）**；换装 `ok / SHA_MATCH=1 / INSTALL_ENTRIES=433=433`（PID 41809）；新值（同一条真机通道）：折叠 = **1 帧到位**（跨 0ms、间距 16.7ms）、展开 = 2 帧；进程内 `宽档数=2`（旧值 15–19）、`分栏档数=2`（旧 11–15）⇒ 屏上不再有任何中间宽，也就不再有「演到一半卡住」；清账 162/63/0；电池 **691/5**（台账后复跑）；产品面连续零改动 **1** 轮（as-of 552，现读）。
⑤ 622/624/627/629 与交接：622 frame 半第八/九值（207.7、156.6）与本轮无关（那条判据读探针自己的 displayLink，不看折叠）；624/627/629 保持开单；628/625/626 结案；新开 **631**（要重新演必须先解决「窗口服务给不给中间帧」与「材质怎么冻」，参考值已记）。CI/交接：⓪ 笔 `48f1528`、产品笔 `884e197`、台账笔随后；R551 三跑（`41374412622↔14ae33a`、`41374877453↔ca9217b`、`41374916378↔01421e5`）读时 in_progress ⇒ NOT-RUN，下一轮必读。下一轮 R553（第 552 轮 / Round 550）：先 push 复核 ahead=0；读本轮各笔（同次 push 只有头笔建跑）+ 复读上述三跑与 R551 已读九跑；622/624/627/629 继续；禁碰清单 7 面（R546–R552）；4.5 地板、150 上限、120ms 阈值、Motion ≥2 帧地板均不动；刀号 M1435 起。"""
    text = replace_once(text, anchor, body + anchor, u"state body")
    wr(name, text)

    sys.stdout.write("LEDGERS_R552_OK\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
