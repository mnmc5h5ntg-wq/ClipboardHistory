# R92 中途读到 R91 推送的 CI（run 38852286519 / `83439f8`）

读法：`gh run view 38852286519 --log`（4357 行 → `/tmp/r91_ci.log`）。作业 `completed failure`。
**这一份是本轮最重要的一次读数：R91 删掉僵尸探针之后，在屏那一卷第一次在 runner 上下了结论。**

## 1. 真读数（`On-screen interaction probes` 那一步自己打的，04:53:56）

```
line 40: 29973 Killed: 9  CLIPBOARD_HISTORY_UI_INTERACTION=1 CLIPBOAR…   （= 240s 看门狗）
UI_PROBE_ORPHAN_XCTEST=0
UI_PROBE_RUNNER_ALIVE=1
ui suite exit: 137  executed: 0  skipped: ?  已下结论的用例: 6
UI_PROBE_PROGRESS started=7 concluded=6
UI_PROBE_CHANNELS pulse=7 started=7 concluded=6
UI_PROBE_HUNG=testRightClickMenusAppKitWouldShowAreChinese
UI_PROBE_HUNG_CHANNEL=pulse
UI_PROBE_CHANNELS_AGREE=1 （两条通道点的是同一批 ⇒ 心跳那条不是孤证）
```

对照 R90 那一次（`091d216`，僵尸还在）：`已下结论的用例: 0`、`started=0`、`pulse=2`、
`UI_PROBE_NAMED=1` 但两条通道互相打脸。

⇒ **BACKLOG 92 剩下那一格有答案了**：runner 上不是"一条都跑不到"，是**跑到 6 条**。
僵尸探针（`testDragSelectExpandsSelectionInsideTheRealList`）确实是挡在前面的那一个，
而且它不再出现在名单里（`源码用例=10 登记=10`，STALE 没了 ⇒ R91 改的名册与覆盖门对上了）。

⇒ 双通道交叉签核第一次兑现：`CHANNELS_AGREE=1`，两条通道点同一个名字。
R90 设计它的时候只能证明"不一致时退回只报观察"，这次证明"一致时它确实敢点名"。

## 2. 新的那一格：第二具僵尸有名字了

`UI_PROBE_HUNG=testRightClickMenusAppKitWouldShowAreChinese` —— 7 条开了口、6 条有结论，
第 7 条在 240 秒里没跑完被收掉。这条正是人工清单里挂着"要真机"的那一条
（R2-22：原生 `NSMenu` 的中文标题）。本机 R91 那一遍它是**跑完的**（10 条 13.782 秒），
所以这不是"它一定挂"，而是"它在这台 runner 上要么挂要么慢到吃满 240 秒"。⇒ 开 **BACKLOG 132**。

机制上不必然是同一族：CoreDrag 那一族的特征是"等一个不会来的窗口服务器事件"；
`NSMenu.popUp` 也在主线程跑自己的模态循环，同样依赖窗口服务器。
**本轮没有量它**（没在 runner 上 `sample`），所以 132 里写的是"待测"，不是"同一族"。

## 3. 两道最终闸门在这一份 run 里仍然是假红（预期内 —— 修法还没推上去）

```
CAPTURE_GATE_RESULT=fail 日志里没有任何 `Test Case ... passed|failed|skipped` 行
  ⇒ 这一步没跑到用例（挂死、崩溃、或 filter 打错）
PROBE_COVERAGE_SUMMARY 源码用例=10 登记=10 runner可跑=0 runner不可跑=10 本次下结论=0 红=0
  PROBE_NOT_RUN 10/10 条在屏判据这次没下结论：…
```

`本次下结论=0` 与同一次 run 上面那句真读数 `concluded=6` **直接矛盾** ——
这正是 R92 本轮修的那件事：闸门在自检之后跑，读的是被 `cp FAKE_LOG /tmp/ui.log`
覆盖过的夹具。⇒ 这一对矛盾是 BACKLOG 128 最好的现场证据：**同一份 run 里，
同一个问题有两个答案，一个来自真日志、一个来自夹具**。

## 4. 本轮没读到的（明确记未运行）

- 那 6 条结论**分别是什么判定**（pass/skip/fail）：`executed: 0` 是驱动缓冲被 SIGKILL 带走的
  结果（R90 已量），而 `已下结论的用例: 6` 数的是 `Test Case … passed|failed|skipped` 行 ——
  这一份日志里那 6 行的**内容**本轮没逐条读（要按步骤名过滤，见 U-178），留给 R93。
- `testRightClickMenus…` 在 runner 上是挂死还是慢：没 `sample` ⇒ 132 的第一格。
- 帧基线/动效地板那两步：这一份 run 里都是绿的，本轮没重读（无新问题不等于没问题）。
