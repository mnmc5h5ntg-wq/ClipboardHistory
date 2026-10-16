# R96 读到的 CI 读数（run 38876999489 / job 116894329916 / `bf6b921`）

作业结论：**success**。这一步是 132 的第一格第一次真的有产物：看门狗在 `kill` 之前拍了栈，
`analyse_sample()` 把它读成了一行判定。

```
UI_PROBE_ORPHAN_XCTEST=0
UI_PROBE_RUNNER_ALIVE=1
ui suite exit: 137  executed: 0  skipped: ?  已下结论的用例: 6
UI_PROBE_PROGRESS started=7 concluded=6
UI_PROBE_CHANNELS pulse=7 started=7 concluded=6
UI_PROBE_HUNG=testRightClickMenusAppKitWouldShowAreChinese
UI_PROBE_HUNG_CHANNEL=pulse
UI_PROBE_CHANNELS_AGREE=1
UI_PROBE_SAMPLE 主线程采样=306 主导路径占比=100% 最深帧=读不到
UI_PROBE_HUNG_KIND=blocked@unknown ⇒ 采样几乎全落在同一个等待帧上（132 分诊：挂）
UI_PROBE_NAMED=1
UI_PROBE_SAMPLE_EXIT=0
```

覆盖率闸门那一步仍然全绿：`本次下结论=6 红=0`、`PROBE_ORDER 露面=7/11 未闭口=1 前缀=1`、
`PROBE_QUEUED 4/11 条一次都没轮到：…`（与上一轮同一批四条）⇒ R95 的登记刷新**没有制造新的红**。

## 那两行 `UI_PROBE_SAMPLE` 是假话，本轮已撤

`主线程采样=306` 是真的（那一行被 `THREADED` 匹配到了），但**那一段里 `NODE` 一个节点都没命中**
⇒ `_dominant_path` 返回 `("", 0)`，而旧写法是
`share = (leaf_count / total) if (total and nodes) else 1.0` —— `nodes` 为空时兜底成 **1.0**，
于是打出"主导路径占比=100%"与 `blocked@unknown`。

这句话的实质是：**我把"读不懂这份文件"说成了"它挂在某个我们不认识的帧上"**。
它比一般的假绿更坏，因为它带着一个具体的百分比与一个具体的判定形状，读的人会以为分诊成功了。
132 要分的"挂 vs 慢"今天仍然没有答案 —— 有答案的是"这份 sample 我还没读懂"。

## 本轮改了三件事

1. `nodes` 为空 ⇒ **不判**（`未量到`），并新增 `UI_PROBE_SAMPLE_UNPARSED=1` 与
   `UI_PROBE_SAMPLE_SHAPE 前若干行=缩进N 数字开头=yes/no 长度=M`。
   **只打形状不打帧名**：台账有一条硬规矩，日志里不许出现用户的剪贴板内容，
   而栈帧名理论上会带上被处理的字符串；诊断"我的正则读不到什么"不需要看帧名。
2. 两格占比的兜底从 `1.0` 改成 `0.0`（读不到就是 0%，不是 100%）。
3. 判定本身换掉：不再从"挑一条最深路径"读数，改成"有多少采样停在等待帧上"
   （`_waiting_leaves`：等待帧套等待帧时只算最内层那一次，并列时把两个族都打出来）。
   这是 137 的正身 —— 旧尺在并列时只能报一个族，而那个族是**我挑的**，不是栈说的。

## 下一轮（R97）读 R96 时要看什么

`UI_PROBE_SAMPLE_SHAPE` 那一行。三种可能，处置各不相同：
* `整段为空` ⇒ 看门狗拍的时候进程已经不在了 ⇒ 要改的是 CI 里 sample 与 kill 的先后（或改成先 SIGSTOP）；
* `缩进N 数字开头=no` ⇒ 主线程块里的行不是"数字 + 帧名"那种形状 ⇒ 我的 `NODE` 需要跟着真实格式改；
* `缩进N 数字开头=yes` 却仍没命中 ⇒ `NODE` 的某一段（比如 `(.*)$` 前的那个 `\s+`）在真实数据上不对。
