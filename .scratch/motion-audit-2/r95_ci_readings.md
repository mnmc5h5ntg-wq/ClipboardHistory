# R95 读到的 CI 读数（run 38864545930 / job 116854254258 / `82fbd1f`）

作业结论：**success**（`gh run view 38864545930 --json jobs` → `116854254258 build-and-test success`）。
下面每一行都是从 `/tmp/r94_ci_job.log`（`gh api .../actions/jobs/116854254258/logs`）里逐字摘的，
时间戳留在行首，方便对回那一步。

## 在屏那一卷（`On-screen probe` 那一步，07:07:55）

```
UI_PROBE_ORPHAN_XCTEST=0 （收掉之后仍在跑的 xctest 数量，必须是 0）
UI_PROBE_RUNNER_ALIVE=1 （看门狗收掉那一刻它还在不在 —— 93 的分诊读数）
UI_PROBE_PROGRESS started=7 concluded=6
UI_PROBE_CHANNELS pulse=7 started=7 concluded=6
UI_PROBE_HUNG=testRightClickMenusAppKitWouldShowAreChinese
UI_PROBE_HUNG_CHANNEL=pulse
UI_PROBE_CHANNELS_AGREE=1 （两条通道点的是同一批 ⇒ 心跳那条不是孤证）
UI_PROBE_NAMED=1
```

## 覆盖率闸门（`On-screen probe coverage floor`，07:12:46 —— 本轮新那两行第一次在 runner 上打）

```
PROBE_COVERAGE_SUMMARY 源码用例=11 登记=11 runner可跑=6 runner不可跑=5 本次下结论=6 红=0
  PROBE_ORDER 露面=7/11 未闭口=1 前缀=1
  PROBE_QUEUED 4/11 条一次都没轮到：testRowGesturesWorkInsideTheRealSidebarContainer testRowIndexDriftDoesNotMoveTheViewport testSidebarListFocusRingAfterClick testRowProxyCensusAsksTheConsequenceNotTheShape
```

同一时间戳之后又打了一遍 `UI_PROBE_*` 那六行（闸门读自己那份日志、报告脚本读另一份），
两批读数**完全一致** ⇒ `红=0` 不是"没判"，是判了且没有一条与登记冲突。

## 这一轮由这些读数决定的三件事

1. **上一轮的预测被证实**：D-152 写的是"翻完之后闸门该绿、作业该转绿"。
   `红=0` 且作业 success ⇒ 六条 `can` 是真的（不是我把推断登记成事实）。
2. **四条 `cannot` 的成因从推断升成读数**：`PROBE_QUEUED` 逐条点了名字。
   其中 `testRowProxyCensusAsksTheConsequenceNotTheShape` 上一轮写的成因是
   "不在 `8e6ed15` 的源码里"（那次闸门读数是 `源码用例=10`），
   而这次是 `源码用例=11` 且它被点名"一次都没轮到" ⇒ 旧成因**被读数推翻**，换成"排队没到"。
   身份一条没翻（`can=6 cannot=5`）：这一轮没有任何一条新下结论。
3. **`UI_PROBE_HUNG` 那条仍然只到"挂在什么上没依据"**：这次多了两格同向读数
   （`RUNNER_ALIVE=1` 收掉那一刻进程还在、`HUNG_CHANNEL=pulse` 心跳与日志同意），
   但"挂 vs 慢"要的是栈 —— `sample` 那一步是本轮新加的，**这份日志里没有它**（它跑在 `82fbd1f`，
   那时看门狗还不拍栈）。⇒ 132 仍开，第一份 runner 栈要读 R95 自己推送的那次。

## 本轮欠着的一格（不许被上面任何一行说成已回答）

`MUTATE_TABLE n=5 caught=4 intended_escaped=1`（分诊那张表）里那 1 格是 **M527**：
`analyse_sample()` 在"同一层有两个 count 都等于 total 的孩子"时取哪一个，没有夹具覆盖。
所以下一次读到 runner 的栈之后，那句"它挂在 X 族"旁边必须带着"并列未覆盖（137）"。
