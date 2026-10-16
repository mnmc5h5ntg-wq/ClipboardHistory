# R91 的第一步：读 R90 推送的 CI（run 38846896495 / `091d216`）

读法：`gh run view 38846896495 --log`（4359 行，落到 `/tmp/r90_ci.log`）+ 对照前两次
`38838819089`（`a68a08f` = R89）与 `38826160092`（`d44d344` = R89 之前那一格）。
作业结论 `failure`，红的两步是 `Capture gate` 与 `On-screen probe coverage floor`。

## 头条：最后两道闸门读的不是真日志，是我自己自检的夹具

`Capture gate` 在 run 里说的这句话是**假的**：

```
CAPTURE_GATE_CHANNELS stdout=1 readings=404 行 补回=402 行（stdout 没有的读数）
CAPTURE_GATE_CASES passed=0 skipped=0 failed=0 有名字的红=0 NOT_RUN=49
CAPTURE_GATE_RESULT=fail 日志里没有任何 `Test Case ... passed|failed|skipped` 行
  ⇒ 这一步没跑到用例（挂死、崩溃、或 filter 打错）。**没跑不算通过**
```

而**同一次 run 的捕获那一步**（03:44:47→03:47:50，早于自检那一步）自己打的是：

```
Test Suite 'UICaptureTests' passed … Executed 47 tests, with 9 tests skipped and 0 failures in 177.801 seconds
capture 文件通道：404 行读数 @ /tmp/shots-ci/capture-readings.log
captured frames: 124  executed: 47  捕获失效帧: 0
```

⇒ 捕获卷在 runner 上**跑完了、0 红、124 帧**，闸门却说"一个用例都没跑到"。

机制（本机**实测**，不是读代码猜的）：往 `/tmp/frames.log` 写一行 `REAL-MARKER`，跑
`python3 -m unittest scripts.tests.test_ci_report_selftest`，之后该文件变成

```
Test Case '-[p probeA]' started.        ← REAL-MARKER 一行不剩（grep -c = 0）
```

—— 和 runner 上闸门读到的 `started=probeA` 一模一样。`run_bash()` 只把 **`/tmp/shots-ci`**
换到自检临时目录：

```python
prepared = script.replace("/tmp/shots-ci", shots_dir)
```

而 `SUBSTITUTIONS["capture_gate"]` 造的夹具命令是字面量：

```
cp FAKE_LOG /tmp/frames.log; mkdir -p /tmp/shots-ci; rm -f /tmp/shots-ci/capture-readings.log; …
```

`onscreen` / `motion` 两格同理：`cp FAKE_LOG /tmp/ui.log &`、`cp FAKE_LOG /tmp/motion.log &`。
⇒ 只要 `Release script tests` 这一步（`python3 -m unittest discover -s scripts/tests`）**先于**闸门跑，
`/tmp/frames.log`、`/tmp/ui.log`、`/tmp/motion.log` 就成了最后一格的假日志。

时间线（run 38846896495，全部同机同 `/tmp`）：
03:47:50 捕获结束 → 03:47:50 在屏那一步开始 → 03:51:50 看门狗 `Killed: 9` →
03:51:51 在屏那一步打出**真**读数 → 03:51:51–03:53:41 胶片 → 03:53+ **自检**（覆盖 `/tmp/*.log`）
→ 03:54–03:55 全量 `swift test` → 03:57:22 两道**最终闸门**读被覆盖后的文件。

这一刀是 R89 挨的：`a68a08f` 把 `Capture gate` 从"紧跟捕获那一步"挪到作业末尾加 `if: always()`
（理由正当：它一红就吃掉后面七步的证据）。挪位置本身没错，错的是自检往共享 `/tmp` 里写。
对照三次 run 完全吻合：

| run | 提交 | `补回` | `passed` | 闸门 |
| --- | --- | --- | --- | --- |
| 38826160092 | `d44d344`（挪之前） | **0 行** | 38 | ok |
| 38838819089 | `a68a08f`（挪之后第一次） | 402 行 | 0 | fail |
| 38846896495 | `091d216` | 402 行 | 0 | fail |

⇒ **可复现，不是骰子**（2/2），且 `readings=404` 两次一模一样 —— 因为读数文件的路径被换到了
临时目录，真那份从没被自检碰过，所以它一直是真的 404 行。这也是 `NOT_RUN=49` 那批读数是**真**的、
而 `passed=0` 是假的的原因：并集里 402 行来自真文件，结论行只可能来自被覆盖的那个通道。

## 同一把刀砍在 `On-screen probe coverage floor`

真读数（03:51:51，在屏那一步自己打的，早于自检）：

```
line 40:  6339 Killed: 9  CLIPBOARD_HISTORY_UI_INTERACTION=1 CLI…   （= 240s 看门狗收掉驱动）
UI_PROBE_ORPHAN_XCTEST=0
UI_PROBE_RUNNER_ALIVE=1
ui suite exit: 137  executed: 0  skipped: ?  已下结论的用例: 0
UI_PROBE_PROGRESS started=0 concluded=0
UI_PROBE_CHANNELS pulse=2 started=0 concluded=0
UI_PROBE_HUNG=testAccessibilityTreeCoverage
UI_PROBE_HUNG=testDragSelectExpandsSelectionInsideTheRealList
UI_PROBE_HUNG_CHANNEL=pulse
UI_PROBE_START_LINES_LOST=1
UI_PROBE_NAMED=1
```

假读数（03:57:22，同一份 `ui_probe_report.py` 读被覆盖后的 `/tmp/ui.log`）：

```
PROBE_COVERAGE_SUMMARY 源码用例=11 登记=11 runner可跑=0 runner不可跑=11 本次下结论=0 红=0
UI_PROBE_PROGRESS started=1 concluded=0
UI_PROBE_CHANNELS pulse=2 started=1 concluded=0
UI_PROBE_CHANNELS_CONTRADICT pulse=… started=probeA
PROBE_FLOOR_STOP_UNNAMED=1 在屏那一卷停了，而报告给不出它是怎么停的（退出码 1）
```

`started=probeA` 就是夹具本体：`TRUNCATED = "Test Case '-[p probeA]' started.\n"`。
⇒ 上一轮记的那条"两条通道互相打脸"（R90 的头条之一）**不是 runner 打的**，是夹具打的。
"CONTRADICT 说 pulse 与 log 各指一条"这条红是**假红**，`PROBE_FLOOR_STOP_UNNAMED=1` 也是。

## 于是 R90 欠的两件事，按真读数重新判

1. **`UI_PROBE_ORPHAN_XCTEST` 必须变 0** —— 真读数就是 0，而且是 03:51:51 那一步自己打的。
   R90 记的"看门狗第一次够到了最里层"成立。
2. **心跳通道第一次在 runner 上落盘** —— 成立，且比预期有用：`pulse=2` 给出了两条开了口
   没下结论的用例名，其中一条正是 R91 删掉的那具僵尸 `testDragSelectExpandsSelectionInsideTheRealList`。
   ⇒ R91 的判断不需要撤回：僵尸在 runner 上也占了 240s 里的一段。

**但要分开记账**（机制未证实就不当结论）：心跳只有"开始"没有"结束"，
`started=0 / 已下结论=0` 是驱动那层缓冲随 SIGKILL 整块丢失的结果，
所以"哪一条挂住"只能怀疑**最后开口的那一条**（字典序里在 `testAccessibilityTreeCoverage` 之后的
`testDragSelect…`），`UI_PROBE_HUNG` 打两行是把"开了口没结论"当成"挂在那儿"，
它分不清"跑完了但那行没落盘"。这一格本轮不动判据，登记给 R92 复核 `ui_probe_report.py` 的语义。

## 本轮没读到的、明确记未运行

- 在屏那一卷在 runner 上**能不能跑到结论**：仍没有名字。真读数只能说 240s 里被收掉、
  收掉时驱动还活着（`RUNNER_ALIVE=1`）。R91 本机删僵尸后是 `Executed 10 tests … in 13.782 seconds`，
  这是一条**预测**，要等下一次 CI 兑现（BACKLOG 92 剩余那一格）。
- `MATERIAL_BLIND_NOT_RUN 这台机器 102 帧里一处黑带都没有，而名单上有 10 处`、
  settings 族整体未绘制（BACKLOG 43）、`FRAME_CORNER_AXIS_NOT_RUN` 缩放=1× 药丸内缩 2px、
  `QUICKPICK_FOCUS_AXIS_NOT_RUN` 墨移动 0.0pt² —— 都是 runner 那台机器的通道前提，照旧未运行。
- BACKLOG 126（真屏 vs 离屏那条决定性对照）本机仍未跑：显示器睡着 / 没给录屏权限，
  `CADisplayLink` 0 帧 + `screencapture` 出全黑图。等真机。
