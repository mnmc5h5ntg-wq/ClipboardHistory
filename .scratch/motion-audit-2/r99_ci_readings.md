# R99 开场读的 CI：run 38898253512（R98 的 `3a05933`）

读的时间：2026-10-16 21:15（本地）。同一支判据在 R97 的 run `38891183309` 里也读了，
用来判"这一红是 R98 带来的还是环境噪声"。

## 1. 结论：failure，红有名字

```
build-and-test  On-screen probe coverage floor  → exit 1
PROBE_COVERAGE_SUMMARY 源码用例=11 登记=11 runner可跑=6 runner不可跑=5 本次下结论=5 红=2
  NOT_RUN testOffScreenProgrammaticSelectionIsRevealedAndNotJumped：登记为 runner=can，而这次日志里没有它的结论行
  FAILED testFrameIntervalsUnderStateChanges：XCTAssertLessThanOrEqual 在这份日志里打红了 ⇒ 红要能被读，也要有人负责
  PROBE_NOT_RUN 6/11 条在屏判据这次没下结论：testRowGesturesWorkInsideTheRealSidebarContainer testOffScreenProgrammaticSelectionIsRevealedAndNotJumped testRowIndexDriftDoesNotMoveTheViewport testSidebarListFocusRingAfterClick testRowProxyCensusAsksTheConsequenceNotTheShape testRightClickMenusAppKitWouldShowAreChinese
  PROBE_ORDER 露面=6/11 未闭口=1 前缀=1
  PROBE_QUEUED 5/11 条一次都没轮到：testRowGesturesWorkInsideTheRealSidebarContainer testRowIndexDriftDoesNotMoveTheViewport testSidebarListFocusRingAfterClick testRowProxyCensusAsksTheConsequenceNotTheShape testRightClickMenusAppKitWouldShowAreChinese
```

对照（R97 的 run `38891183309`，同一支判据）：

```
PROBE_COVERAGE_SUMMARY 源码用例=11 登记=11 runner可跑=6 runner不可跑=5 本次下结论=6 红=0
PROBE_ORDER 露面=7/11 未闭口=1 前缀=1
```

⇒ **不是环境噪声**：R97 六条 `can` 全下结论、零红；R98 只有五条下结论、两条红。
`未闭口=1` 两轮都有（那条的名字归 `ui_probe_report.py` 判，见 R94 的分工注释），
差别在 R98 少了一条结论、多了一条断言红。

## 2. BACKLOG 144 要的那一格：种子判据在 runner 上是 NOT_RUN

```
SEED_GUARD settings-privacy-excluded light 期望=2 右边缘墨带=0 整页墨带=0 填充=…
SEED_GUARD settings-privacy-excluded dark  期望=2 右边缘墨带=0 整页墨带=0 填充=…
SEED_GUARD_NOT_RUN settings-privacy-excluded light（整页零墨 ⇒ 这台机器拍不出这一页）
SEED_GUARD_NOT_RUN settings-privacy-excluded dark（整页零墨 ⇒ 这台机器拍不出这一页）
SEED_GUARD_NOT_RUN：两档所有种子夹具都画不出墨 ⇒ 种子通道记为未运行（BACKLOG 43 同族），不算通过
```

144 的 ① 问的是"绿、红、还是 skip"⇒ 答案是 **skip（未运行）**，且它自己把理由说全了。
144 担心的那个中间态（"别处画得出、那两行画不出"⇒ 判据会红得不是产品）**没有出现**：
runner 上那一屏是**整页**零墨，闸门走的是它设计上该走的那一支。
⇒ 144 结案；不加地板、不改闸门（144 原文就禁了这两条路）。

**留下的新问题**：种子通道在 runner 上至今**没有真值点**（本机两档都有：整页墨带 34、右边缘 2）。
这一格现在只能记成"runner 未覆盖"，不能记成"runner 通过"。

## 3. BACKLOG 145（本轮开并修）：那一条红的"为什么"被丢在正则里

`FAILED testFrameIntervalsUnderStateChanges：XCTAssertLessThanOrEqual 在这份日志里打红了`
—— 名字有、断言类型有、**那一句没有**。而那一整行本来在日志里是完整的：

```
error: -[ClipboardHistoryAppTests.UIInteractionProbeTests testFrameIntervalsUnderStateChanges] :
       XCTAssertLessThanOrEqual failed: ("…") is greater than ("…") - <判据自己写的那句理由>
```

`scripts/probe_coverage_gate.py` 的 `ASSERTION_RED` 写成
`… : (XCTAssert\w+)` 就停了，第三个组没有 ⇒ 后半段被丢掉，而那一步又没有别的通道能补
（`/tmp/motion.log` 不上传；`ui.log` 里那一行被正则截短）。

R59 / BACKLOG 86 在 motion 那一步已经记过同一条教训（"名字不够，还要那一句为什么"），
这一支漏了 ⇒ 本轮补上，并加一条 python 判据钉住"数值与理由都必须在"。

## 4. BACKLOG 146（新开，本轮不猜）

`testFrameIntervalsUnderStateChanges` 在 runner 上到底为什么红。
本轮能排除的只有两件事：① 它不是环境噪声（见 §1 的 R97 对照）；
② 它不是 R98 那次产品改动带出来的（那次只动设置窗口那张卡片的留白档，
而这条判据量的是主窗口 900×640 灌数据时的帧间隔；本机 R99 那一卷 `PROBE_EXIT=0`、
11 例 / 3 skip / 0 failures）。

判它需要的是 **145 修好之后、下一次 run 里那一句原文**。同一次 run 还要看
`testOffScreenProgrammaticSelectionIsRevealedAndNotJumped` 会不会随红的那条一起消失 ——
若仍不闭口，那是 R61 那条 reveal 判据自己的问题（它有没有在 runner 上跑完），与 146 分开记。
