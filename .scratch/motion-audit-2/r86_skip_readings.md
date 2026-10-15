# R86 开场测量：BACKLOG 116 那句"skip 的条数会自己动 7 条"，今天复现不出来

命令与产物（都在本机，同一提交 `0f0cced`，同一台机器，四个独立进程）：

| # | 命令 | 结果 | skip 名单 |
|---|---|---|---|
| 1 | `swift test`（全量） | `Executed 801 tests, with 41 tests skipped and 0 failures` | 41 条，见下 |
| 2 | `swift test`（全量，第二遍） | `Executed 801 tests, with 41 tests skipped and 0 failures` | 与第 1 遍**逐名相同**（`diff` 空） |
| 3 | `swift test --filter UICaptureTests`（带 `CLIPBOARD_HISTORY_UI_SHOTS`） | `Executed 47 tests, with 4 tests skipped and 0 failures` | 4 条诊断判据 |
| 4 | 同 3，第二遍 | `Executed 47 tests, with 4 tests skipped and 0 failures` | 与第 3 遍相同 |

⇒ **116 的"同一提交两遍差 7 条"在这四个进程里没有复现**。
它记的是 R81 的 `796 / 38` 与 `796 / 45`。今天同一提交两遍全量给的是 41 / 41，
名单也逐名相同 ⇒ 不能据此说那个抖动不存在，只能说**它不是这一版代码在默认通道上的稳定性质**，
而 116 剩下的、今天仍然成立的那半句是：**这些名字进不了闸门读的那条通道**。

## 41 条 skip 的成因分组（从 `Test skipped - <原因>` 原文聚出来的，不是猜的）

| 条数 | 原因（原文前 72 字） |
|---|---|
| 21 | 动效胶片探针：设 `CLIPBOARD_HISTORY_UI_MOTION=1` 才跑（会抢…） |
| 11 | 在屏交互探针：设 `CLIPBOARD_HISTORY_UI_INTERACTION=1` 才跑（会…） |
| 4 | 诊断用判据：它只回答「这一列是谁画的 / 这一行是标题档还是说明档 / 这一行截不截 / 压在哪个颜色域」 |
| 1 | 离屏语义色探针与视觉审计同开关 |
| 1 | 会开一个真浮层窗口并抢前台：设 `CLIPBOARD_HISTORY_UI_MOTION` |
| 1 | 未设置 `CLIPBOARD_HISTORY_UI_SHOTS`，跳过离屏渲染 |
| 1 | 未设置 `CLIPBOARD_HISTORY_UI_INTERACTION`，跳过在屏交互探针 |
| 1 | 测试进程的 bundle id 在本机不唯一或根本没被列出（ownP…） |
| **41** | 合计（与 `with 41 tests skipped` 对得上） |

⇒ 每条 skip **在测试日志里都有原因**。这里要把 116 原文那句"没有一行为什么今天没跑"**收窄**，
因为它只对了一半：

- **捕获这一族其实已经看得见**：读 R85 的 CI（run 38805382593）时，`Capture gate` 那一步打了
  `CAPTURE_GATE_CASES passed=38 skipped=9 failed=0 有名字的红=0 NOT_RUN=54`，
  并且逐条列出了 `TEXT_SIDE_NOT_RUN settings-shortcuts dark 侧栏列读到 0 个偏离像素（同帧内容区读到 0 个）` 这样的行
  —— 也就是说那五条在 runner 上确实 skip 了，而闸门**从 stdout 并集里读到了它们的名字**。
- **真正缺的是反方向**：闸门只报"它找到的 NOT_RUN"，不报"它没找到的那些"。
  一条判据如果既没跑、也没打 `*_NOT_RUN`（整行缺席），今天仍然没人红 ——
  这与 R85 给 `loops` 那一层修的正是同一件事（`LOOP_SILENT`），只是捕获这一族还没有那一格。
- **文件通道确实没有它们**：本机 `/tmp/r85/shots/capture-readings.log` 514 行里
  `*_NOT_RUN` 只有 `QUICKPICK_FOCUS_RING_NOT_RUN=1` 两行，这五个名字一行都没有。
  但这**不是缺陷**：本机那两遍捕获卷里这五条是**跑了的**（47 条只 skip 了 4 条诊断判据），
  没 skip 自然没有 NOT_RUN 行。⇒ 记这条是为了不让人把"文件通道里没有"读成"通道坏了"。

## 读 CI 时踩到的一个新坑（值得单独记）

`gh run view --log` 把**所有步骤**的日志拼在一起，而 `MOTION_SHIMMER_STATE` 这类状态行会在
**两个步骤**里各出现一次、且取值不同：

| 步骤 | 行 |
|---|---|
| `Swift tests (executed-count gate)`（全量卷，没设开关） | `MOTION_SHIMMER_STATE 判定=skipped 原因=capability-gate` |
| `Motion filmstrip (report-only)`（设了开关那一卷） | `MOTION_SHIMMER_STATE 判定=ok 原因=-` |

⇒ 我第一遍 grep 整份日志时读到"同一族既 ok 又 skipped"，差点把它当成 R85 那层的排序 bug
（闸门是"按最后一条判"）。按步骤名再过滤就清楚了：**两条行来自两次不同的运行，不是同一次自相矛盾**。
闸门读的是 `/tmp/motion.log`（只有设了开关那一卷写它），所以它没被骗 —— 会被骗的是我。
