# R89 读 R88 的 CI（三条 run 全部读到：38825657419 / 38825879726 / 38826160092，commit 984da5f · 3978769 · d44d344，build-and-test 三个都是 **failure**）

main 又红了，而红的是**我上一轮新写的那道门**——它报的不是产品，是我自己修法的第二处不完整。
两件事同时发生，都要记账：

## 1. R88 的新读数第一次在 runner 上说话，并且它是对的

```
On-screen interaction probes (report-only)
  line 13:  8376 Killed: 9  CLIPBOARD_HISTORY_UI_INTERACTION=1 … swift test --filter UIInteractionProbeTests > /tmp/ui.log 2>&1
  ui suite exit: 137  executed: 0  skipped: ?  已下结论的用例: 0
  UI_PROBE_PROGRESS started=0 concluded=0
  UI_PROBE_START_LINES_LOST=1 （收掉的那一刻 xctest 还活着 ⇒ 用例确实开了口，是 stdout 的块缓冲被 SIGKILL 整块带走）
  UI_PROBE_NAMED=1
On-screen probe coverage floor
  PROBE_COVERAGE_SUMMARY 源码用例=11 登记=11 runner可跑=0 runner不可跑=11 本次下结论=0 红=0
  UI_PROBE_START_LINES_LOST=1 …
  PROBE_FLOOR_WATCHDOG_MISSED=1 收掉之后仍有 1 个 xctest 在跑
  ##[error]Process completed with exit code 1.
```

⇒ **93 的成因问题在 runner 上被自己的读数确认了**：`UI_PROBE_RUNNER_ALIVE=1` ⇒ 用例在跑，
"一条用例都没开始"那句（R86–R87 读了两遍的话）确实是假的。R88 那一格设计的目的达成。

## 2. 但 R88 的修法不完整：组杀够不到 xctest

本机把 pid / ppid / **pgid** 一起量出来（`spike_r89_group_kill.sh`，90 秒后按 CI 原样收）：

```
24524 24520 24524  swift-test --filter UIInteractionProbeTests     ← $! 就是它，`set -m` 生效
24581 24524 24581  xctest -XCTest ClipboardHistoryAppTests.UIInteractionProbeTests/…（11 条全在 argv）
PGID_OF_JOB=24524  PID_OF_JOB=24524
（kill -9 -- -24524 之后）
24581     1 24581  xctest -XCTest …                                ← 还活着，ppid=1，pgid 还是自己
```

⇒ `xctest` 自己 `setpgid` 成了**另一个组的组长**，所以它不在驱动进程的组里。
R88 那句 `kill -9 -"$pid"` 杀的是 24524 那个组，里面只有驱动。
⇒ 我的假设"杀父组 = 杀整棵树"在 SwiftPM 上不成立 —— 这一条记进台账（U-192）。

## 3. 第二件更贵的事：我那道红吃掉了七个步骤的证据

`gh run view --json jobs` 的逐步结论：

```
success  Build (must be warning-free)
success  Swift tests (executed-count gate)
success  Offscreen frame capture / Capture gate / On-screen interaction probes
failure  On-screen probe coverage floor          ← 我上一轮加的硬门
skipped  Motion filmstrip (report-only)
skipped  Motion coverage floor                   ← coverage 第六个数据点今天拿不到
skipped  Release script tests
skipped  Info.plist gate
skipped  Frame baseline vs working manifest
skipped  Frame baseline vs previous release
skipped  Runtime launch smoke (report-only)
```

⇒ 仪器的一朵红把**产品该拿的证据整段 skip 掉了**：动效卷、动效地板、脚本自测、
两张帧基线、启动冒烟，一步没跑。R36/R66 那两条"红必须有名字"没有配套的另一半：
**红不许把别的判据变成没跑**。⇒ 四道硬门挪到所有产证据步骤之后，各自 `if: always()`（U-193）。

## 4. 三个 run 都读完了：这朵红是**稳定**的，而"九个"是我手抄错的

`gh api .../runs/<id>/jobs --jq '.jobs[0].steps[] | select(.conclusion=="failure").name'`
与 `select(.conclusion=="skipped") | length`，对三条 R88 的 run 逐条读：

```
run           失败的那一步                        skipped 数
38825657419   On-screen probe coverage floor      7
38825879726   On-screen probe coverage floor      7
38826160092   On-screen probe coverage floor      7
```

三个 run 的在屏那一步读数也逐字一致（`UI_PROBE_RUNNER_ALIVE=1`、`UI_PROBE_ORPHAN_XCTEST=1`、
`UI_PROBE_PROGRESS started=0 concluded=0`、`UI_PROBE_START_LINES_LOST=1`、`UI_PROBE_NAMED=1`、
`ui suite exit: 137 executed: 0 已下结论的用例: 0`）。

⇒ 两件事各自成立：
1. **R88 那道门有牙，而且不闪**：同一个原因连着红三次（0 次假红、0 次漏报）。
   这一格不是好消息——它红是因为我的修法确实不够；但"红得稳定"正是 R36/R66 那一族要的形状。
2. **我上一段正文里的"九个步骤"是假的**：写它的时候我只看了自己列的那张清单，没数过 API 的结论。
   API 说 7。⇒ 台账里那一族的措辞全部按 7 改，并且生成脚本里加了一条守卫：**正文里"X 个步骤"
   必须等于 `SKIPPED_AFTER_GATE` 这个读数**，否则直接拒绝写台账。这条属于 R87 那一族
   （"stale literals 与产物矛盾"），但这次是**新写**的正文就错了，不是旧正文滞后 —— 更值得记。

GATE_STEP=On-screen probe coverage floor
CONSISTENT_RUNS=3/3
SKIPPED_AFTER_GATE=7

## 5. 一条**没成立**的结论：我在电池的变异窗口里读了 `ci.yml`（U-197）

读三条 run 的同时，变异电池正在改这个文件。我用 `grep -c 'if: always()'` 与 ruby 的 YAML 解析读它，
得到：

```
always=5
Swift tests (executed-count gate)   if=      ← 我据此写下"四道门里有一道漏挂，逐门检查是假 OK"
```

电池之外重读：**6**，四道门都挂着；09:13 那次 `接线检查 OK（10 项都在）` 也是对的。
⇒ 我读到的不是事实，是**那一刀**（M492 就叫"删掉一道硬门的 `if: always()`"）。

⇒ 这一族以前只在写侧防过（"电池期间不许提交"），读侧没防过；而读侧更阴 —— 它不报错，
只会给你一份"看起来像事实"的快照，而且恰好支持一个戏剧性的结论（"我的守卫是假 OK"最容易采信）。
⇒ 修法装在唯一的读侧入口：`ledgers_r89.py` 一进来先 `pgrep -f mutate_r89_watchdog.py`，
有电池在跑就 `SystemExit`。**当场验过**：电池正跑时执行 stage A ⇒ 拒绝并打出 pid 31814，
`git status` 里台账一个字节没动。只装读侧是刻意的：`verify_r89.sh` 自己就是启动电池的进程。
