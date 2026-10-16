# R90 的两条实测结论（都推翻了我自己上一轮写下的东西）

## 1. BACKLOG 93 有答案了：在屏那一卷挂在**真实拖拽会话**里，栈是完整的

诊断脚本：`.scratch/motion-audit-2/spike_r90_channel_diag.sh`（不杀进程，每 20 秒取样一次）。
取样表（本机，无并发）：

```
SAMPLE t=040s bytes=119 heartbeat=0
SAMPLE t=060s bytes=119 heartbeat=0
SAMPLE t=080s bytes=119 heartbeat=0
SAMPLE t=100s bytes=119 heartbeat=0
SAMPLE t=120s bytes=119 heartbeat=0
FINAL  exit=137 bytes=119 heartbeat=0
```

而 `sample` 抓到的主线程栈（`/tmp/r90_sample.txt`，进程已活 7 分 25 秒、0.0% CPU、state=S）：

```
-[XCTestCase invokeTestMethod:]
 @objc UIInteractionProbeTests.testDragSelectExpandsSelectionInsideTheRealList()
 UIInteractionProbeTests.MouseSynthesizer.drag(from:through:to:)
 UIInteractionProbeTests.MouseSynthesizer.send(_:at:clicks:number:)
 -[NSWindow(NSEventRouting) sendEvent:]
 -[_NSGFGestureEnvironment _routeMouseEventToActiveGestureRecognizers:]
 _NSGestureRecognizerSortAndSendDelayedEvents
 -[NSRunLoop runUntilDate:]
 -[NSCoreDragManager _dragUntilMouseUp:location:modifiers:]
 CoreDragStartDraggingAsync
 NSCoreDragCGEventBlockingProc
 -[NSApplication nextEventMatchingMask:…] → _BlockUntilNextEventMatchingListInMode → mach_msg
```

⇒ **挂在哪儿**：`testDragSelectExpandsSelectionInsideTheRealList` 用 `window.sendEvent:` 合成鼠标事件，
AppKit 的手势环境把它认成一次真拖拽，于是 `NSCoreDragManager` 起了一个**自己的模态事件循环**
（`_dragUntilMouseUp`），它从窗口服务器要"下一个事件"，而合成事件不会从那条路回来 ⇒ 永久阻塞。
⇒ 这不是 runner 专属：本机今天同样挂（7 分钟没动）。R88 记的"本机 90 秒内这一卷能跑完"
是**另一台机器/另一天**的读数，不能拿来给今天签字。
⇒ 这也解释了 runner 上 `started=0 concluded=0` 而 `RUNNER_ALIVE=1`：不是"用例在跑只是日志丢了"，
而是**第一条之后的那条就卡死在这里**（`testAccessibilityTreeCoverage` 先 skip，然后 drag 卡住）。

### 处置（下一刀做什么，不做什么）

- 做：给这条探针的 `send(...)` 包一层**进程级看门狗**（文件里已有 `PopupWatchdog`，同一形状），
  或者把"拖选"从"合成真事件"改成"直接调用手势/选择逻辑" —— 后者是改判据的含义，要先想清楚判的还是不是那件事。
- 不做：把这条探针删掉或 skip 掉来让 CI 变绿（那是"删测试绕开检查"）。
- 不许：把"runner 上跑不完"再归因给环境而不给栈 —— 现在栈有了，归因就是这条用例自己。

## 2. BACKLOG 122 的前提被证伪：stderr **不**活得过 `swift test` 的收杀

R89 我在 `r89_design_probe_heartbeat.md` 里写：`emit` 走 `FileHandle.standardError.write` = 直接
`write(2)`、不经 stdio 缓冲，而 CI 是 `> /tmp/ui.log 2>&1` ⇒ 心跳天然活得过 SIGKILL。
本轮把心跳真的加进 `setUpWithError()` 之后实测：

- 取样时进程活着、且已经跑到**第二条用例的方法体里**（栈为证 ⇒ 至少两次 `setUpWithError` 已经执行），
  而 `ui.log` 里 `heartbeat=0`、字节数从 40 秒到 120 秒一直是 119。

⇒ 错在哪：`2>&1` 只保证 fd 2 与 fd 1 指向**同一个目的地**，而那个目的地不是文件 ——
SwiftPM 的驱动把孩子的 stdout/stderr 接进**自己的管道**再转发，孩子的 `write(2)` 落到管道里，
驱动被 SIGKILL 时它自己那块缓冲一起丢。所以"无缓冲"这句是对的（孩子侧），
"活得过 kill"这句是错的（中间多了一跳）。
⇒ 结论：**要活得过收杀，必须自己开文件写**（`CaptureReadings` 那条文件腿的形状），
不能靠 stderr。R89 那条设计笔记要在台账里被明确撤回，而不是悄悄改掉。
⇒ 顺带一条复用上的坑：`CaptureReadings.readingsURL` 是按 `CLIPBOARD_HISTORY_UI_SHOTS` 推导的，
而 CI 的捕获卷与在屏卷**用的是同一个目录** ⇒ 在屏卷第一次写会把捕获卷的读数文件整份重写
（那是它自己的规矩："上一遍的读数冒充这一遍"）。所以心跳要有**自己的** URL，
并复用同一套加锁写入，而不是共用那份文件。
