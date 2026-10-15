# R88 spike：看门狗到底收掉了谁（BACKLOG 93 的第三种成因）

跑法：`bash .scratch/motion-audit-2/spike_r88_partial_channel.sh /tmp/r88_spike`
（三个时刻各 `kill -9` 一次：40 / 90 / 150 秒，同一份日志里同时读 started 行与产物目录）

## 读数（原文，2026-10-16 06:45–06:48）

```
SPIKE delay=40s  exit=137 log_bytes=119 started=0 concluded=0 帧_收掉前=0 帧_收掉后=0 探针独有帧=0
SPIKE delay=90s  exit=137 log_bytes=176 started=0 concluded=0 帧_收掉前=0 帧_收掉后=0 探针独有帧=0
SPIKE delay=150s exit=137 log_bytes=176 started=0 concluded=0 帧_收掉前=0 帧_收掉后=0 探针独有帧=0
```

三份日志的**全文**（这就是"一条用例都没开始"那份日志长什么样）：

```
# ui-40.log
[0/1] Planning build
Building for debugging...
[0/4] Write swift-version--58304C5D6DBC2206.txt
Build complete! (0.16s)

# ui-90.log / ui-150.log
Another instance of SwiftPM (PID: 14064) is already running using
'/Users/wangziyi/Codex_Project0/ClipboardHistory/.build', waiting until that process
has finished execution...
```

## 决定性的一条：被收掉之后，跑测试的那个进程还活着

kill 之后 `ps` 读到（etime 是"已经活了多久"）：

```
14064  ppid=1      05:45  .../usr/bin/swift-test --filter UIInteractionProbeTests
14117  ppid=14064  05:44  .../usr/bin/xctest -XCTest ClipboardHistoryAppTests.UIInteractionProbeTests/testAccessibilityTreeCoverage,…(共 11 条) ….xctest
14224  ppid=1      05:04  .../usr/bin/swift-test --filter UIInteractionProbeTests
14337  ppid=1      03:33  .../usr/bin/swift-test --filter UIInteractionProbeTests
```

⇒ 三件事同时成立：
1. **`kill -9` 收掉的是外层，`swift-test` 与 `xctest` 被 reparent 到 launchd 后继续跑**（ppid=1、etime 5 分多钟）；
2. `xctest` 的命令行里带着**全部 11 条用例名** ⇒ 过滤器解析成功、XCTest 已经开始跑 ⇒
   "一条用例都没开始"这句话是**假的**；
3. 它一直跑，而日志停在 119 字节 ⇒ stdout 从没 flush 过（块缓冲，SIGKILL 不会 flush）。

## 这一版 spike 自己的边界（不许越过）

我这一版在 `swift test` 前面套了 `/usr/bin/time -p`，所以 `$!` 拿到的是 **time** 的 PID，
被我 kill 的是 time ⇒ 只证明了"杀祖先会留下活着的 runner"，
**没有**证明 CI 那种形状（`swift test … & pid=$!; kill -9 $pid`，杀的就是 `swift-test` 本身）
也会留下活着的 `xctest`。CI 的形状是"杀父留子"，非常可能同一条路，但那是一次不同的测量。

⇒ 第二版 spike（`spike_r88_ci_shape.sh`）按 CI 的原样跑一次：不加 time，`$!` 就是 swift-test，
kill 之后立刻 `ps` 看 xctest 还在不在。**这一条才是 93 的答案**。

## 顺带量到的：产物通道是**单向**证人

`UIInteractionProbeTests` 11 条里只有 3 条写盘（focus-chain 的两张、reveal 的两张），
而字母序第一条 `testAccessibilityTreeCoverage` 不写。
⇒ "有帧"能证"确实跑过用例"；"没帧"什么都证不了（可能只是还没跑到那三条）。
所以 93 要的是**每条用例都留一行**的通道（R56 给动效卷用过的那个形状），不是帧目录。
