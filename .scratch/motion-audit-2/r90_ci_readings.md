# R90 读 R89 的 CI（run 38838819089 · commit a68a08f · build-and-test = failure，但红的位置换了）

两条硬指标都达成了，而红换到了另一格上 —— 那一格的红是**旧账被顺序照出来**，不是新修法失效。

## 1. R89 那两件事，runner 上第一次有了读数

```
UI_PROBE_ORPHAN_XCTEST=0        ← R88 的三条 run 连着是 1；父壳收残留孩子的组那一刀够到了
UI_PROBE_RUNNER_ALIVE=1         ← 收掉那一刻 xctest 还在（93 的分诊读数照旧）
ui suite exit: 137  executed: 0  skipped: ?  已下结论的用例: 0
On-screen probe coverage floor  = success   ← 这道门第一次不红（它红是因为 orphans≥1）
Motion coverage floor           = success
skipped 步骤数 = 0              ← R88 是 7：四道硬门挪到证据之后 + `if: always()` 生效
```

⇒ U-192（杀父组 ≠ 杀整棵树）与 U-193（红不许把别的判据变成没跑）两条修法**在 runner 上被证实**。
⇒ 而且这次不是"我说它对了"：是那道门自己从红变绿，而它变绿的唯一依据是 `orphans=0`。

## 2. 新的那一朵红：`Capture gate` 读到 `passed=0 NOT_RUN=49`

```
step 5  Offscreen frame capture (report-only)   success   captured frames: 124  executed: 47  捕获失效帧: 0
step 6  On-screen interaction probes            success
step 7  Motion filmstrip                        success
step 14 Capture gate                            failure
        CAPTURE_GATE_CHANNELS stdout=1 readings=404 行 补回=402 行
        CAPTURE_GATE_CASES passed=0 skipped=0 failed=0 有名字的红=0 NOT_RUN=49
        （49 条全是 `CAPTION_NOT_RUN … 读到 0 个文字墨像素` 那一族）
```

⇒ 帧是好的（124 张、47 条用例、0 张未绘制），坏的是**闸门读的那份读数文件已经不是捕获卷的了**：
`CaptureReadings.readingsURL` 由 `CLIPBOARD_HISTORY_UI_SHOTS` 推导，而 CI 里捕获卷与在屏卷
**共用 `/tmp/shots-ci`**；`CaptureReadings` 自己的规矩是"每个进程对每份文件第一次写要整份重写"
（理由写在它旁边：上一遍的读数冒充这一遍，比没有读数更坏）⇒ 在屏卷第一次写把捕获卷那份换掉了。
⇒ 为什么以前不红：R89 之前捕获闸门紧跟捕获步骤（第 7 位），在屏卷（第 8 位）还没来得及污染它。
**U-193 的修法把闸门挪到证据之后，于是这条一直存在的共用文件第一次可见。**
⇒ 修法：在屏卷改用自己的 `/tmp/shots-probe`（一行），并加一条会红的接线判据
（`testCaptureAndProbeSuitesDoNotShareTheReadingsFile`：两卷的 shots 目录不许相同，
而闸门读的必须是捕获卷那个目录下的 `capture-readings.log`）。变异刀 M504 就是"把目录改回去"。
⇒ 这一格要老实记：**顺序没做错**，它做错的是"把别人的证据搬到自己脚下"这件事一直没人查。

## 3. 顺带：R89 留在 CI 里的那句"这一卷没结论"仍然成立，但成因现在有点名了

在屏那一卷在 runner 上还是 240 秒收不掉（`executed: 0`），而本机 50 秒那一遍同样是
`log_bytes=119 started=0` 且 xctest 活着。R90 心跳接上之后本机量到了挂死的那条：

```
PROBE_PULSE testAccessibilityTreeCoverage
PROBE_PULSE testDragSelectExpandsSelectionInsideTheRealList   ← 最后一条有心跳、没有结论
```

⇒ 与 `sample` 抓到的主线程栈同一条（`MouseSynthesizer.drag` → `NSWindow sendEvent:` →
`_NSGFGestureEnvironment` → `NSCoreDragManager _dragUntilMouseUp` → `mach_msg`）。
⇒ 93 的那一问第一次有两个独立来源同意：产品自己写的心跳，和操作系统给的栈。
