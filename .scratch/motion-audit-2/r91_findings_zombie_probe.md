# R91 的结论：那条拖选探针是僵尸，而它挡住的 10 条判据第一次跑出结论

## 1. 一句话

`testDragSelectExpandsSelectionInsideTheRealList` 测的手势在产品里**六天前就被决定不做了**（D-034），
而 D-034 的正文写着"这条探针删除并在原位置留了解释"——**那句话是假的**：
`git log --all -S "func testDragSelect…"` 只有 9d7b5ca 一次增、零次删。
它这六天做的事是：**把整卷在屏判据挡在门外**（CI 上 `executed: 0`、本机 180 秒收不掉）。

## 2. 修法之前先量（三支 spike）

| 量 | 读数 |
|---|---|
| 挂死比例（CI 原样，180s 上限，3 遍） | `RUN 1/2/3 exit=137 用时=180s 心跳=2 started=0 有结论=0`，最后心跳三次都是 `testDragSelectExpandsSelectionInsideTheRealList` ⇒ **恒挂，不是闪挂** |
| 挂在哪（`sample` 主线程） | `-[NSWindow sendEvent:] → -[_NSGestureEnvironmentBase sendEventToGestureRecognizers:] → (Gestures) → _CFRunLoopRunSpecificWithOptions → -[NSCoreDragManager _tryCatchDragUntilMouseUp:…] → _dragUntilMouseUp → CoreDragStartDraggingAsync → NSCoreDragCGEventBlockingProc → _DPSBlockUntilNextEventMatchingListInMode → _BlockUntilNextEventMatchingListInMode` |
| 机制 | "抬起"那一行代码排在 `sendEvent` 的**下游**，而 CoreDrag 等的是**窗口服务器**的真 mouseUp ⇒ 进程内无解 |

### 我第一版修法被自己的测量撤掉

我先按"越过阈值才会起会话"把拖动压成 **2pt 阈值内微移**（`pressNudgeRelease`），以为这样就安全。
再跑一遍：**栈一模一样**（`_tryCatchDragUntilMouseUp` 那个名字本身就说明它在抢这次拖动），
会话照样起来 ⇒ 阈值这个前提是错的，**任何** `.leftMouseDragged` 都会挂。
⇒ 整条撤掉（连助手一起删），只留一行 `DRAG-LIMIT` 读数 + 一条机制级守卫。
⇒ 记 U 条：**"我以为压到阈值内就安全"不是一种证据**；改法的依据必须是重跑的那一遍，不是推理。

## 3. 修完的读数（本轮的交付）

```
修前：心跳 2 / 有结论 0 / 180 秒收不掉（3/3）
修后：Executed 10 tests, with 2 tests skipped and 1 failure in 13.782 seconds
      心跳 10 / passed 7 / skipped 2 / failed 1
```

⇒ 这 10 条在屏判据**第一次**在一条时间线上给出结论（以前它们从没跑完过，CI 与本机都一样）。

两条 skip 都是**有名字的未覆盖**，不是悄悄通过：

```
FRAME_CHANNEL baseline_n=0 screen=有        ⇒ CADisplayLink 0.6s 空转一颗 tick 都没发
testAccessibilityTreeCoverage skipped       ⇒ 原有豁免（R35 那条覆盖规则）
```

`FRAME_CHANNEL` 这一格值得单独说：`testFrameIntervalsUnderStateChanges` 第一次跑到就红了
（`XCTAssertGreaterThan(loaded.n, 60)` 读到 0）。查因不在产品：同一台机器
`screencapture` 返回 2940×1912 **全黑**、`pmset` 报 `UserIsActive 0` ⇒ 显示器睡着 ⇒ 没有可采的刷新。
⇒ 判据改成"采样通道先证明自己活着"：空转 0.6s 拿不到 tick 就报 `FRAME_CHANNEL baseline_n=0` 并 skip。
这不是放宽地板（60fps 那三条一条没动），是**把"仪器没跑"与"产品掉帧"分开** ——
拿 0 个样本判 60fps 与拿它判"通过"一样假。

## 4. 第一条真红：`testSidebarListFocusRingAfterClick`（新开 BACKLOG 127）

```
找不到行代理（要求 KeyViewProxy 宽 200…290、高 <40）
宿主 (0,0,320,460) 窗口内容区 (0,0,320,460)
实际：KeyViewProxy@(12.0, 50.5, 148.0, 25.0)   ← 左半
      KeyViewProxy@(160.0, 50.5, 148.0, 25.0)  ← 右半
      ListTableRowView@(0,10,320,51) ×6
```

⇒ 一行暴露出**两个半宽** `KeyViewProxy`（148 + 148 + 间距 ≈ 320 = 整行宽）。
两种成因，本轮**不定性**：
① 产品的无障碍结构（行被拆成两个可焦点单元 ⇒ Tab 一行停两次、焦点环可能只画半行）；
② 这条判据的期望（"宽 200…290"）是我在它**从没跑出结论**的情况下写的 —— 一个没被正对照校准过的
   几何期望，不配有罪判决（与 U-200/R87 同一族：尺先要能被打红，也要能被打对）。
⇒ BACKLOG 127 的第一步是**正对照**：同一颗尺去量快速选择浮层那一卷列表的行代理，
   看它是不是也两个半宽。是 ⇒ ②（SwiftUI `List` 的固有结构，期望要按实测重推）；
   不是 ⇒ ①（产品缺陷，改无障碍结构）。
⇒ 本轮**不**为了让 CI 绿而改这条期望（那是"为过夹具改判据"），也不删这条探针。
   所以 R91 推上去之后 main 会带着**一朵有名字的红** —— 这是有意的：
   修好僵尸探针的意义就是让红能说话。

## 5. 台账与代码矛盾这一族（本轮第二次撞上"写着做了其实没做"）

R90 记的是"我新写的正文与产物矛盾"（U-196）；R91 是**旧正文里的一个完成态断言与代码矛盾**：
D-034 说"删除并在原位置留了解释"，而解释确实留了（就在原位置），**函数却还在它上面**。
⇒ 教训：一句"已删除 X"必须能被机器复查。本轮把它钉成
   `testProbeSuiteNeverSynthesizesADragSession`：扫的是**事件类型** `(.leftMouseDragged`
   而不是函数名（改名就能绕过函数名扫描），并且要求 `DRAG-LIMIT` 那行读数必须在。
   牙 M505/M506 分别测"把事件加回来"和"把解释/读数删掉"两刀。
