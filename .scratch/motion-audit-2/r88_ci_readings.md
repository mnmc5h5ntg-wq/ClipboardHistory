# R88 读 R87 的 CI（run 38818629423 · commit d0b5939 · 22:44→22:53 · build-and-test = **success**）

main 绿了。两件事同时有了答案，其中一件把我上一轮的读数**判成了假话**。

## 1. 那朵假红确实消失了，而 coverage 拿到第五个数据点

```
motion suite exit: 0  executed: 54  胶片: 14  MOTION_RESOLVE_SUMMARY judged=4/4 not-run=-
MOTION_SHIMMER 扫 帧数=23 变化帧对=2 峰值=0.019 采样≈100ms coverage=0.690(地板 0.50) 记录时长=2343ms 判定=一直在动
MOTION_SHIMMER_WITNESS 等节拍证人(30Hz 抬升 0.12) 帧对=32 在变=1 峰值=0.014 coverage=0.043 判定=只动了一下
MOTION_SHIMMER_WITNESS 粗节拍证人(20Hz 抬升 0.45) 帧对=30 在变=23 峰值=0.040 coverage=1.000 判定=一直在动
MOTION_SHIMMER_STATE 判定=ok 原因=-
MOTION_FLOOR_LOOP_JUDGED=skeleton-loop 这一族今天判到了（状态 ok）
MOTION_FLOOR_LOOP_JUDGED=skeleton-band-position 这一族今天判到了（状态 ok）
MOTION_FLOOR_REDS=0
```

⇒ **红没了，但不是靠 D-145 那一支没掉的**：这一遍产品 coverage 0.690 自己在地板上，
所以 `travel` 那一支根本没被触发，`LOOP_NOT_JUDGED=…contradicted-by-travel` **今天没在 runner 上出现**。
⇒ 诚实的结论：D-145 这一轮**没有被 runner 检验**（它只在真值表与本机那 8 刀里活着）。
它挡红的能力仍然是"未证"，这条要留给下一次 coverage 掉到地板以下的那一遍。

**119 的第五个数据点**（同画法、同机器类别、runner）：0.522 / 0.842 / 0.032 / **0.690**
⇒ 跨度 0.81，四遍里两遍在地板上、两遍在地板下。这条判据今天仍然不配当硬门（R86 记过同一句话）。

**新的、更该记的一条**：等节拍那颗**证人**今天读 0.043（"只动了一下"），而产品读 0.690。
R82 立这颗证人的理由是"它与产品同数字、同节拍"，可它自己在 runner 上的分布
（0.671 / 1.000 / 0.043）比产品还宽。今天没造成错判（产品在动 ⇒ 直接判 ok，证人没被问），
但它是 **110 那一族在证人自己身上的第四个实例**：一旦产品掉到地板下、需要证人签字，
这颗证人有 1/3 的概率先说"没在动"。⇒ 新开 **BACKLOG 122**。

## 2. 在屏那一卷：`NO_CASE_STARTED` 那句解释被本机测出来的机制**证伪**了

```
line 13:  8376 Killed: 9  CLIPBOARD_HISTORY_UI_INTERACTION=1 … swift test --filter UIInteractionProbeTests > /tmp/ui.log 2>&1
ui suite exit: 137  executed: 0  skipped: ?  已下结论的用例: 0
UI_PROBE_PROGRESS started=0 concluded=0
UI_PROBE_NO_CASE_STARTED=1 （进程在第一条用例开口之前就死了：看门狗收掉的是启动阶段，不是某条判据）
UI_PROBE_NAMED=1
PROBE_COVERAGE_SUMMARY 源码用例=11 登记=11 runner可跑=0 runner不可跑=11 本次下结论=0 红=0
```

同一次 push 之前，本机按 CI 的**原样**跑了一遍看门狗（`.scratch/motion-audit-2/spike_r88_ci_shape.sh`）：

```
驱动进程 pid=14687（swift-test --filter UIInteractionProbeTests），120s 后 kill -9 它本身
kill 之后清理阶段仍然抓到：14741  …/usr/bin/xctest -XCTest ClipboardHistoryAppTests.UIInteractionProbeTests/testAccessibilityTreeCoverage,…（11 条全在 argv 里）
log_bytes=119  started=0  concluded=0  帧=0
```

⇒ **杀父留子**：`kill -9` 收掉的是 `swift-test` 驱动进程，真正跑用例的 `xctest` 子进程
被 reparent 之后**继续活着**（第一版 spike 里活了 5 分多钟，还占着 `.build` 锁，
把后面两次运行全堵在 "Another instance of SwiftPM is already running"）。
⇒ 所以 `UI_PROBE_NO_CASE_STARTED` 那句"进程在第一条用例开口之前就死了"是**假的**：
用例开了口，只是它的 stdout 在块缓冲里，父进程被 SIGKILL 时一行都没落盘。
⇒ BACKLOG 93 剩下的那一格由此分开：是 **②**（日志通道丢了），不是 ①。
R86 我登记的那句"②为真时 NO_CASE_STARTED 就是一句关于产品的假话"——今天它就是那句假话。

## 3. 其余步骤

* `Swift tests (executed-count gate)` / `Capture gate` / `Frame baseline` / `Release script tests`：全绿（REDS=0、CHANGED=0）。
* `On-screen probe coverage floor` 打了 `PROBE_NOT_RUN` 全 11 条的名字 ⇒ 集合级那一支仍然尽职。
