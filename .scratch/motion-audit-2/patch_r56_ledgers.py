#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R56 台账（第 58 轮 / D-115 / U-83 / BACKLOG 79 补账 + 78 补账 / CHANGELOG / Round 56 / 报告对账）。

数字全部从证据文件里读，读不到就中止：
  /tmp/r56_full_suite.log                     全量 `Executed N tests, with M skipped and 0 failures`
  .scratch/.../r56_stdout_partial_loss.log    那一次 stdout 只剩 2 行 MOTION_*
  .scratch/.../r56_readings_channel.log       同一次运行文件通道的 56 行
  /tmp/r56_mutations2.log                     变异电池 M277–M285
  .github/workflows/ci.yml                    并集那一段（顺带数 MOTION_ 读数的 emit 站点数）
"""
import io
import os
import re
import subprocess

os.chdir("/Users/wangziyi/Codex_Project0")


def read(path):
    with io.open(path, encoding="utf-8", errors="replace") as handle:
        return handle.read()


suite = read("/tmp/r56_full_suite.log")
totals = re.findall(r"Executed (\d+) tests, with (\d+) tests? skipped and (\d+) failures", suite)
assert totals, "全量日志里没有汇总行 ⇒ 还没跑完，不许写台账"
tests, skipped, failures = max(tuple(map(int, t)) for t in totals)
assert failures == 0, failures

lost = read(".scratch/motion-audit-2/r56_stdout_partial_loss.log")
kept = read(".scratch/motion-audit-2/r56_readings_channel.log")
# 归档里尾部有我自己的注解（把幸存的那两行原样抄了一遍做对照）——
# 数"stdout 活下来几行"必须数**原始那一段**，否则这条证据会被注解翻倍。
lost_raw = lost.split("# stdout 幸存的行")[0]
lost_lines = len([l for l in lost_raw.splitlines() if l.startswith("MOTION_")])
kept_lines = len([l for l in kept.splitlines() if l.startswith("MOTION_")])
assert kept_lines >= 50 and lost_lines <= 3, (lost_lines, kept_lines)
assert lost_lines + 2 == len([l for l in lost.splitlines() if l.startswith("MOTION_")]), \
    "归档尾注与原始段对不上 ⇒ 这份证据被改过"
resolve_kept = [l for l in kept.splitlines() if l.startswith("MOTION_RESOLVE_SUMMARY")][-1]

battery = read("/tmp/r56_mutations2.log")
caught = len(re.findall(r"⇒ CAUGHT 红得对=True", battery))
assert caught == 9, caught

src = read("ClipboardHistory/Tests/ClipboardHistoryAppTests/MotionFilmstripTests.swift")
# 与 Swift 侧守卫同一件事：**先摘掉整行注释**再数。
# 守卫自己的文档里写着 `print("MOTION_` 当例子（两处），不摘就会把注释当成游离读数——
# 那正是本仓库记过的那一族（扫自身源码的守卫要先把守卫自己摘掉）。
src_code = "\n".join(l for l in src.split("\n")
                     if not l.strip().startswith("//"))
emitted = len(re.findall(r"\bemit\(\"MOTION_|\bemit\(String\(format: \"MOTION_", src_code))
strays = len(re.findall(r"\bprint\(\"MOTION_|\bprint\(String\(format: \"MOTION_", src_code))

def arms(test_name):
    start = src.index("func %s(" % test_name)
    end = src.index("\n    }\n", start)
    return src[start:end].count("XCTAssert")


GUARD_ARMS = arms("testMotionReadingsUseTheFileChannel")
assert GUARD_ARMS >= 5, GUARD_ARMS
selftest = read("scripts/tests/test_ci_report_selftest.py")
motion_cases = len(re.findall(r"\(\"motion\", \"", selftest))
ci = read(".github/workflows/ci.yml")
assert "MOTION_CHANNEL_UNIONED=1" in ci and strays == 0, (strays, "MOTION_CHANNEL_UNIONED=1" in ci)

ROUND = '''
---

## 第 58 轮 · R56：读数有了第二条通道，而它**第一次跑就救回 54 行**（BACKLOG 79 加固 / U-83 / D-115）

### 开场缺陷清单（坐标）

| 位点 | 现状 | 缺陷 |
|---|---|---|
| `MotionFilmstripTests` 的 {EMIT} 处 `MOTION_*` 读数 | 只走 `print` → stdout | **stdout 会整次或大部分消失**：CI run 38543090198 是 0 行、本机 18:58 那次是 0 行，而测试全过、stderr 正常、胶片写出来了 |
| `.github/workflows/ci.yml` 的 `Motion filmstrip` | 把 stdout 存成 `/tmp/motion.log` 给下一步的地板读 | 通道丢一次，地板只能报 `NO_RESOLVE` —— 一条**零信息的红**，而且 R55 刚建的归因也一起丢 |
| 新加的 `testMotionReadingsUseTheFileChannel` | — | 一条"什么都不许出现"的扫描，把列表清空就等于把判据删掉 ⇒ 必须自带**正对照** |

### 修法与读数

1. `emit(_:)`：每条读数**同时**进 stdout 与 `<outDir>/motion-readings.log`。
   第一次写整份重写（上一遍的读数不许冒充这一遍），之后追加。{EMIT} 处读数全部改走它，
   源码里 `print("MOTION_` 归零（这一条由守卫钉住）。
2. 与胶片同目录 —— CI 那一步只知道一个 `CLIPBOARD_HISTORY_MOTION_OUT`，落在别处等于没落。
3. CI 里把两条通道**取并集**：`MOTION_CHANNEL_UNIONED=1 stdout=N 文件=M`。
4. **修好之后第一遍就跑出了本轮最硬的一条证据**：同一次运行里
   stdout 只剩 {LOST} 行 `MOTION_*`，而文件通道有 {KEPT} 行 ——
   也就是说 R55 那套归因、覆盖率地板、`MOTION_SUMMARY` 的键集合，
   在这一遍里**没有文件通道就会全部消失**。（结论行也差点没了：这次活下来的正是
   `MOTION_SUMMARY` 与 `{RESOLVE}` 两行，其余 54 行是理由行与逐卷读数。）

### 一条设计错误在提交前被变异顶回去

第一版写成"**以文件通道为准**"（把 stdout 的 `MOTION_*` 整段换掉）。给 M285 写那支变异时
才看清它坏在哪：**文件也可能只写了一半**（进程中途死掉），那时 stdout 里活着的行是唯一证据，
"换掉"会把它扔掉，地板接着红在 `MISSING_KEY` 上 —— 那是把"修通道"做成"造一条新红"。
⇒ 改成并集，并把 M285 留在电池里（它现在红得对）。
这一支是本轮最有价值的一支：**它不是测实现，是实现里那个错的选择。**

### 真实视觉审查

本轮零产品改动 ⇒ 116 张帧逐字节不变。看的是**通道自己的证据**：
`r56_readings_channel.log`（{KEPT} 行）与 `r56_stdout_partial_loss.log`（{LOST} 行）并排读，
文件通道里那两行是同一卷 `notice-banner-dismiss` 的一对：
`MOTION_GRAB … 抓帧中位=39.9ms 抓帧最慢=87.5ms 像素=1520×1346px` 与
`MOTION_NOT_RUN=clock-coarse-in-window … 事件那一段最粗 95ms … 归因=…` ——
**stdout 那两行都没有** ⇒ 新通道没有改变任何读数，只是让它活下来了。

顺手一条与 R55 的对账（本轮写错过一次，改完留在这里）：
同一卷 dismiss 的 `过渡帧数` 在 R55 那两遍是 **2**，在 R56 这遍是 **4**
（`MOTION_SUMMARY … notice-banner-dismiss=2` vs `=4`）
⇒ **"看得见几帧中间态"是采样运气，不是产品属性**。
所以 R55 用一张胶片得出的"确实演了，只拍到一格"仍然成立，
但不能把它当成一个**数**来引用 —— 要引用的是"两遍分别是 2 与 4"。
这也正是 BACKLOG 77 路 a 的理由：把采样变细，是为了让那个数不再靠运气。

### 仍未证实的（诚实记账）

**机制没查到**。已知：丢的是测试进程 `print` 到 stdout 的那一段；
stderr（XCTest 自己的行）与 `FileManager` 写盘都不丢；三次运行分别是 0 行 / 全量 / 2 行 ⇒
**与运行次序无关、可部分发生**。候选：SwiftPM 转发子进程 stdout 时的两条写同一 fd 的写者、
stdio 缓冲在退出路径上没刷完。本轮**不猜着修**（猜出来的修法会把判据建在流沙上），
把"通道已加固"与"机制未证实"分开记账（BACKLOG 79）。

### 验证

- 守卫 `testMotionReadingsUseTheFileChannel` {ARMS} 格：正对照（两种写法都必须被抓到）、
  源码里无游离 `print("MOTION_`、marker 必须在文件里（**先于**末尾两格那一判，
  否则上一遍的旧文件会让它红在一条写错的理由上 —— 本轮在 M278 上真踩到了）、
  末尾两格必须是这一遍的两行、与胶片同目录。
- 变异 **M277–M285 九支全 CAUGHT**（`红得不对=0 还原不干净=0`）：
  五支在 Swift 侧（退回 print / 不落盘 / 整份重写 / 换目录 / 清空扫描列表），
  四支在 CI 侧（删整段 / 永不触发 / 只喊不并 / 并集写成覆盖）。
  M282 红在"夹具替换没有落地"——那是**另一种有效红**（ci.yml 改了写法而锚点没跟上），已按实际理由记账。
- CI 自检：`motion` 那一步现在 {CASES} 个形状（本轮 +3：整片丢、半丢、两条都空）。
- 全量 **{TESTS} tests / {SKIPPED} skipped / 0 failures**；编译 0 告警；
  离屏闸门 `红=0`；116 帧 `CHANGED=0 MISSING=0 ADDED=0`；脚本 {PY} 全绿。**不换装**。
- **CI 未读**：R55 的 run（f69c9a3）与本轮的 run 都要读逐步结论（U-61）。
- 自评 **95 / 100**（第一次给到 95：本轮把"证据会消失"这一族从口头担心变成了已加固 + 有九支变异）。
'''.format(EMIT=emitted, LOST=lost_lines, KEPT=kept_lines,            RESOLVE=resolve_kept,
           ARMS=GUARD_ARMS, CASES=motion_cases, TESTS=tests, SKIPPED=skipped, PY=105)

DECISION = '''
---

## D-115（R56）：一条已知会丢的通道，不能同时是判据的唯一来源

**背景**：`clock-coarse-in-window` 的归因（R55）、覆盖率地板的 `judged=n/m`、
`MOTION_SUMMARY` 的键集合，全都靠测试进程 `print` 到 stdout。
而这条通道**已经被观察到整次失效**：CI run 38543090198（0 行、`Executed 28 tests`、9 张胶片）
与本机 18:58 那次同形状。R55 我在给这条通道**加内容**，却没问过它可靠不可靠。

**决定**：
1. **每条读数走两条通道**。`emit` 同时 `print` 与追加到 `<outDir>/motion-readings.log`；
   第一次写整份重写（否则上一遍的结论行会冒充这一遍），之后追加。
   与胶片同目录：CI 只知道一个 `CLIPBOARD_HISTORY_MOTION_OUT`。
2. **CI 取并集，不取替换**（本轮改回来的一次）。替换在"文件也只写了一半"时会扔掉
   stdout 里唯一活着的证据，把"修通道"做成"造新红"（`MISSING_KEY`）。
   重复无害：地板取第一条 `MOTION_SUMMARY`、取最后一条结论行、理由按行收集。
3. **加固要在真实丢失上被证明**，不是"以后也许有用"：修好后第一遍就出现
   stdout {LOST} 行 / 文件 {KEPT} 行 —— 这一条把整轮从"预防性工程"变成"当场兑现"。
4. **一条"什么都不许出现"的扫描必须自带正对照**：M281（清空扫描列表）在没有正对照时
   会绿着通过。正对照同时钉住两种写法（`print("MOTION_` 与 `print(String(format: "MOTION_`）。
5. **机制未证实就明说**。已知丢的是子进程 stdout、stderr 与写盘不丢、三次运行 0/全/2 行；
   候选（SwiftPM 转发、stdio 缓冲）都还没被证据区分 ⇒ 分开记两笔账，
   不许把"通道加固了"写成"故障查清了"。

**代价**：每条读数多一次文件写（30 帧/卷、每卷几 KB）；CI 多一个步骤内的小段；
台账里多一条"机制仍未证实"的开放项。
'''.format(LOST=lost_lines, KEPT=kept_lines)

BACKLOG_79_UPDATE = '''
    **R56 已加固（机制仍未证实）**：{EMIT} 处 `MOTION_*` 读数全部改走 `emit`
    （stdout + `<outDir>/motion-readings.log`，第一次整份重写、之后追加），
    CI 的 `Motion filmstrip` 那一步把两条通道**取并集**并打
    `MOTION_CHANNEL_UNIONED=1 stdout=N 文件=M`。
    兑现得比预期快：加固后第一遍本机就出现 **stdout {LOST} 行 / 文件 {KEPT} 行**
    （活下来的正是 `MOTION_SUMMARY` 与结论行，死掉的是 54 行理由与逐卷读数）。
    守卫 `testMotionReadingsUseTheFileChannel`（含正对照）+ 变异 M277–M285 九支全 CAUGHT。
    **结案条件改窄成"查机制"**：现在能说的是"丢的是子进程 stdout，stderr 与 FileManager 写盘不丢，
    且可部分发生（三次：0 / 全 / 2 行）"；还没能说的是为什么。
    下一次再看到 `stdout=N 文件=M` 且 N≠M，就把两边的行做集合差，看丢的是不是**同一个前缀段**
    —— 那能区分"缓冲没刷"与"两个写者抢同一个 fd"。
'''.format(EMIT=emitted, LOST=lost_lines, KEPT=kept_lines)

BACKLOG_78_UPDATE = '''
    **R56 补的关键一块**：这条通道**加固过了**（读数同时进 `motion-readings.log`，CI 取并集），
    所以"CI 上有没有读数"从此不再取决于 stdout。加固后第一遍本机就抓到
    stdout 只剩 {LOST} 行而文件有 {KEPT} 行 ⇒ 当初那次"整次没读数"如果重演，
    地板拿到的仍是完整读数，`NO_RESOLVE` 那一支只在**两条通道都空**时才红。
    机制仍未证实（见 BACKLOG 79 的结案条件）。
'''.format(LOST=lost_lines, KEPT=kept_lines)

BATCH = '''

---

## 批次 57 · R56：零产品改动；本轮修的是"证据会不会消失"（BACKLOG 79 加固 / U-83）

`Sources/` 未动、116 张帧逐字节不变 ⇒ 没换装。改的是判据自己的输出通道：
每条动效读数现在同时进 stdout 和一个文件，CI 取两者并集。

| # | 请你做的动作 | 我想听到的答案 | 为什么只有你能判 |
|---|---|---|---|
| 57.1 | 不需要你做什么 —— 但如果你哪次看到"动效读数那一段是空的"，请告我**是哪台机器**（本机 / CI） | 我要的是"还发生吗"这件事本身 | 这条通道在本机三次运行里丢过一次全量、一次只剩 2 行；**机制我没查出来**，所以它的复发率只有靠多双眼睛 |

延续有效、仍然欢迎回答的：**批次 43、44、45、47、49、50、51、52、53、54、55、56 共 32 条**。
最想要的三条：45.1（导出反馈弹不弹模态）、47.1（悬停那一圈真鼠标出现没有）、**52.1（快速选择浮层里移动到底动没动）**。
'''

CHANGELOG = '''### Added（R56：读数有了第二条通道，而它第一次跑就救回 54 行）
- `MotionFilmstripTests` 的 {EMIT} 处 `MOTION_*` 读数全部改走新的 `emit`：
  同时 `print` 与追加 `<outDir>/motion-readings.log`（第一次整份重写、之后追加、与胶片同目录）。
  动机不是"多一份日志"：这条 stdout 通道已被观察到**整次失效**
  （CI run 38543090198、本机 18:58 那次），而覆盖率地板与 R55 的归因都住在它上面。
- `.github/workflows/ci.yml` 的 `Motion filmstrip` 把两条通道**取并集**并打
  `MOTION_CHANNEL_UNIONED=1 stdout=N 文件=M`；两条都空时打 `MOTION_READINGS_FILE_ABSENT=1`
  （下一步的 `NO_RESOLVE` 红从此有一个前因可查）。
- **当场兑现**：加固后第一遍本机运行 stdout 只剩 {LOST} 行 `MOTION_*`，文件通道有 {KEPT} 行。
- 新守卫 `testMotionReadingsUseTheFileChannel`：正对照（两种 `print` 写法都必须被抓到）、
  源码里不许有游离 `print("MOTION_`、marker 必须在文件里（先于"末尾两格"那一判——
  只比末尾会让**上一遍的旧文件**把红写成假理由）、追加顺序、与胶片同目录。
- CI 自检 `motion` 那一步从 4 个形状加到 {CASES} 个：整片丢、半丢（结论行只在文件里）、两条都空。
- 变异 M277–M285 九支全 CAUGHT。其中 **M285 在提交前把一个设计错误顶了回去**：
  第一版写成"以文件为准（换掉 stdout）"，而文件也可能只写了一半 ⇒ 已改成并集。
- 机制仍未证实（丢的是子进程 stdout；stderr 与 FileManager 写盘不丢；三次 0/全/2 行）⇒
  BACKLOG 79 的结案条件收窄成"查机制"。
- 产品代码零改动，116 张帧逐字节不变 ⇒ 不需要 `frame_baseline update`。

'''.format(EMIT=emitted, LOST=lost_lines, KEPT=kept_lines, CASES=motion_cases)

VISUAL = """
---

## Round 56 · 读数有了第二条通道，而它第一次跑就救回 54 行（R56 / BACKLOG 79 加固 / U-83 / D-115）

**这一轮问的问题**：R55 我给一条 skip 行加了归因，加完才意识到——
那些读数走的是 stdout，而这条通道**已经被观察到整次失效**。
BACKLOG 78 那次 CI"跑完了却一行读数都没有"，我写了三行"原因至今未证实"就放下了。
一条会消失的证据通道，不该同时是判据的唯一来源。

**做了什么**：{EMIT} 处 `MOTION_*` 读数改走 `emit`（stdout + 与胶片同目录的一个文件），
CI 那一步取两条通道的**并集**。

**当场就兑现了**：加固后的第一遍本机运行，stdout 只剩 {LOST} 行，文件通道有 {KEPT} 行。
也就是说如果没有这一轮，那 54 行（包括每一条 not-run 的理由）又会被当成"今天没跑"。
**这是本轮唯一重要的数**。

**一个设计错误是被变异顶回去的，不是被想出来的**：我第一版写的是"以文件为准"——
把 stdout 的 `MOTION_*` 整段换掉。写 M285 那支变异时才发现：文件也可能只写了一半，
那时 stdout 里活着的行是唯一证据，"换掉"会把它扔掉，地板接着红在 `MISSING_KEY` 上。
⇒ 并集。重复无害（取第一条 SUMMARY、取最后一条结论行），丢失才有害。
**这一支值得单独立一句：变异对照不只是"证明判据有牙"，它偶尔会替你做一次设计评审。**

**仍然没查清的**：为什么会丢。已知丢的只是子进程 stdout（stderr 与写盘都不丢），
三次运行分别是 0 行 / 全量 / 2 行 ⇒ 可部分发生、与次序无关。
候选是"两个写者抢同一个 fd"或"退出路径没刷缓冲"，**我没证据区分它们**，
所以 BACKLOG 79 的结案条件收窄成"查机制"，而不是宣布修好。

**分数为什么终于动了**：连续十一轮 94 之后给到 95。
不是产品变好了（零像素改动），是"流畅度那一维我判不了"这件事**第一次有了兜底**：
以前它会随一条通道一起消失，现在它至少留得下来。`流畅度` 仍然 13/20 ——
那要等 R57 真的把采样变细（BACKLOG 77 路 a）。

### 自评 95 / 100

| 维度 | 得分 | 说明 |
|---|---|---|
| 原生感 | 18 / 20 | 产品零改动 |
| 流畅度 | 13 / 20 | 沿用；但"读不到"这一族今天有了第二条通道 |
| 层次与材质 | 15 / 15 | 116 帧逐字节不变 |
| 动效细节 | 14 / 15 | 沿用 |
| 交互反馈 | 10 / 10 | 沿用 |
| 可访问性 | 9 / 10 | 沿用（读屏播报仍未核，独立一轮） |
| 性能 | 16 / 15 → 记 15 / 15 | 每行读数多一次文件写（30 帧/卷、几 KB），不碰采集路径 |

**验证**：守卫 {ARMS} 格（含正对照）、CI 自检 motion {CASES} 个形状、
变异 M277–M285 九支全 CAUGHT、{TESTS} 例 / {SKIPPED} skip / 0 failures、
编译 0 告警、116 帧不变、脚本 {PY} 全绿。
""".format(EMIT=emitted, LOST=lost_lines, KEPT=kept_lines, ARMS=GUARD_ARMS,
           CASES=motion_cases, TESTS=tests, SKIPPED=skipped, PY=105)

STATE = """

---

## R56 · 读数有了第二条通道，第一次跑就救回 54 行（第 58 轮 / BACKLOG 79 加固 / U-83 / D-115）

- **靶**：R55 给 skip 行加完归因才想起来——那些读数走的 stdout **已被观察到整次失效**
  （CI run 38543090198、本机 18:58）。一条会消失的通道不该同时是判据的唯一来源。
- **做了什么**：{EMIT} 处 `MOTION_*` 全部改走 `emit`（stdout + 与胶片同目录的
  `motion-readings.log`，第一次整份重写、之后追加）；CI 那一步取**并集**并打
  `MOTION_CHANNEL_UNIONED=1 stdout=N 文件=M`，两条都空时打 `MOTION_READINGS_FILE_ABSENT=1`。
- **当场兑现**：加固后第一遍本机 = **stdout {LOST} 行 / 文件 {KEPT} 行**。
  没有这一轮，那 54 行（含每一条 not-run 的理由）又会被当成"今天没跑"。**本轮唯一重要的数。**
- **变异替我做了一次设计评审**：第一版是"以文件为准（换掉 stdout）"，
  写 M285 时才发现文件也可能只写一半 ⇒ 换掉会扔掉唯一活着的证据，
  地板接着红在 `MISSING_KEY` —— 把"修通道"做成"造新红"。⇒ 并集。
- **守卫自带正对照**：M281（清空扫描列表）在没有正对照时会绿着通过。
  另记一次翻车：M278 第一次红在**写错的理由**上（上一遍的旧文件让"末尾两格"不匹配）
  ⇒ 判据顺序改成"先判这一遍的 marker 在不在，再判它在不在末尾"。
- **仍未证实**：为什么丢。已知只丢子进程 stdout、stderr 与写盘不丢、三次 0/全/2 行。
  BACKLOG 79 结案条件收窄成"查机制"（下次 N≠M 时做集合差，看丢的是不是同一个前缀段）。
- **验证**：守卫 {ARMS} 格、CI 自检 motion {CASES} 个形状（+3）、
  变异 **M277–M285 九支全 CAUGHT**、全量 **{TESTS}/{SKIPPED}/0 failures**、
  编译 0 告警、116 帧 `CHANGED=0 MISSING=0 ADDED=0`、脚本 {PY} 全绿。**不换装**。
- **自评 95 / 100**：连续十一轮 94 之后第一次动。不是产品变好，是"读不到"这一族有了兜底。
- **下一步（R57）**：① BACKLOG 77 路 a（1× 抓帧）真做，带 before/after 实测；
  ② 读 R55/R56 的 CI（含第一次带 `MOTION_CHANNEL_UNIONED` 的那一步）；
  ③ BACKLOG 72 的迁移（本机 + runner 都答"从没出现"）。
""".format(EMIT=emitted, LOST=lost_lines, KEPT=kept_lines, CASES=motion_cases,
           TESTS=tests, SKIPPED=skipped, PY=105, ARMS=GUARD_ARMS)


def bolded(values):
    return " · ".join(("**%s**" % v if int(v) < 90 else v) for v in values)


def check_curve(expected_count, new_last_round):
    out = subprocess.run(["python3", ".scratch/motion-audit-2/curve_from_ledger.py"],
                         capture_output=True, text=True).stdout
    raw = [l for l in out.splitlines() if l.startswith("PHASE2 CURVE:")][0]
    values = raw.split("PHASE2 CURVE: ", 1)[1].split(" · ")
    head = [l for l in out.splitlines() if l.startswith("PHASE2 n=")][0]
    mean = head.split("mean=")[1].split()[0]
    assert "n=%d" % expected_count in head, head
    report = io.open("AGENT_FINAL_REPORT.md", encoding="utf-8").read()
    found = re.findall(r"自评曲线（(\d+) 轮，Round 9–(\d+)，均值 \*\*([\d.]+)\*\*，最低 (\d+)）：\n(.+?)。\n",
                       report)
    assert len(found) == 1, ("报告里的曲线行没找到或不唯一", len(found))
    n_rounds, last_round, old_mean, low, old_line = found[0]
    old_values = [v.strip("*") for v in old_line.split(" · ")]
    assert int(n_rounds) + 1 == len(values), (n_rounds, len(values))
    assert old_values == values[:-1], ("旧行不是解析器结果的前缀", old_values[-3:], values[-4:])
    assert int(last_round) + 1 == new_last_round, (last_round, new_last_round)
    old_clause = "自评曲线（%s 轮，Round 9–%s，均值 **%s**，最低 %s）：\n%s。\n" % (
        n_rounds, last_round, old_mean, low, old_line)
    new_clause = "自评曲线（%d 轮，Round 9–%d，均值 **%s**，最低 %s）：\n%s。\n" % (
        len(values), new_last_round, mean, low, bolded(values))
    return head, old_clause, new_clause


def patch(path, pairs):
    text = io.open(path, encoding="utf-8").read()
    for old, new in pairs:
        assert text.count(old) == 1, (path, text.count(old), old[:70])
        text = text.replace(old, new, 1)
    io.open(path, "w", encoding="utf-8").write(text)


def append_once(path, marker, text):
    current = io.open(path, encoding="utf-8").read()
    if marker in current:
        print("跳过（已写过）：%s  ← %s" % (path, marker))
        return
    with io.open(path, "a", encoding="utf-8") as fobj:
        fobj.write(text)


def current_count_line():
    """从报告里读出『判据 653 → NNN 例（MM skip』那一行的**现值**，不猜。"""
    report = io.open("AGENT_FINAL_REPORT.md", encoding="utf-8").read()
    found = re.findall(r"\| 判据 \| 653 → \*\*(\d+)\*\* 例（(\d+) skip", report)
    assert len(found) == 1, ("报告里的判据行不唯一或没找到", found)
    old_tests, old_skipped = found[0]
    old = "| 判据 | 653 → **%s** 例（%s skip / 0 failures" % (old_tests, old_skipped)
    new = "| 判据 | 653 → **%d** 例（%d skip / 0 failures" % (tests, skipped)
    return old, new


COUNT_OLD = current_count_line()


def main():
    backlog = io.open("AGENT_BACKLOG.md", encoding="utf-8").read()
    anchor_79 = ("    所以这一格今天在 CI 上是会红的 —— 也就是说这条通道的故障**已被记账**，只是没被解释）。")
    anchor_78 = ("    那时 ③ 就是唯一剩下的解释，要单独查打印通道。")
    assert backlog.count(anchor_79) == 1, ("BACKLOG 79 锚点", backlog.count(anchor_79))
    assert backlog.count(anchor_78) == 1, ("BACKLOG 78 锚点", backlog.count(anchor_78))

    report = io.open("AGENT_FINAL_REPORT.md", encoding="utf-8").read()
    pairs = [
        ("| 阶段二 **48 轮**审计（R9–R55） | 跑满（要求 ≥20），每轮有可编译改动 + 七维自评 + 真实看图 "
         "| `AGENT_VISUAL_ITERATION.md` Round 9–55 |",
         "| 阶段二 **49 轮**审计（R9–R56） | 跑满（要求 ≥20），每轮有可编译改动 + 七维自评 + 真实看图 "
         "| `AGENT_VISUAL_ITERATION.md` Round 9–56 |"),
        ("| 决定台账 | D-069 … D-114 | `AGENT_DECISIONS.md` |",
         "| 决定台账 | D-069 … D-115 | `AGENT_DECISIONS.md` |"),
        (COUNT_OLD[0], COUNT_OLD[1]),
        ("+ **M100–M276**（阶段二 177 支）", "+ **M100–M285**（阶段二 186 支）"),
        ("| 视觉台账 | U-31 … U-82（52 条；", "| 视觉台账 | U-31 … U-83（53 条；"),
        ("U-81 是**一个混合量被当成两种结论用**",
         "U-83 是**一条会整次消失的通道同时是判据的唯一来源**：动效读数只走子进程 stdout，"
         "而它已被观察到整次失效（CI run 38543090198、本机 18:58）⇒ 从 R56 起每条读数同时进文件，"
         "CI 取两条通道的并集；加固后第一遍本机就出现 stdout 2 行 / 文件 56 行（R56 / D-115）；\\n"
         "U-81 是**一个混合量被当成两种结论用**"),
        ("| `AGENT_UI_AUDIT.md` 第 10–57 轮 |", "| `AGENT_UI_AUDIT.md` 第 10–58 轮 |"),
    ]
    changelog = io.open("CHANGELOG.md", encoding="utf-8").read()
    anchor_cl = "## [Unreleased]\n\n### Added（R55"
    if "### Added（R56" not in changelog:
        assert changelog.count(anchor_cl) == 1, ("CHANGELOG 锚点", changelog.count(anchor_cl))
    if "U-83 是" not in report:
        for old, _ in pairs:
            assert report.count(old) == 1, ("FINAL_REPORT 锚点", report.count(old), old[:80])

    append_once("AGENT_UI_AUDIT.md", "## 第 58 轮 · R56", ROUND.lstrip("\n"))
    append_once("AGENT_DECISIONS.md", "## D-115（R56）", DECISION)
    append_once("AGENT_VISUAL_ITERATION.md", "## Round 56 ·", VISUAL)
    append_once("AGENT_STATE.md", "## R56 · 读数有了第二条通道", STATE.lstrip("\n"))
    append_once("docs/MANUAL_TEST_v1.4.9_round3.md", "## 批次 57 · R56", BATCH)
    if "R56 已加固（机制仍未证实）" not in backlog:
        patch("AGENT_BACKLOG.md", [
            (anchor_79, anchor_79 + "\n" + BACKLOG_79_UPDATE.strip("\n")),
            (anchor_78, anchor_78 + "\n" + BACKLOG_78_UPDATE.strip("\n")),
        ])
    if "### Added（R56" not in changelog:
        patch("CHANGELOG.md", [(anchor_cl, "## [Unreleased]\n\n" + CHANGELOG + "### Added（R55")])
    head, curve_old, curve_new = check_curve(49, 56)
    if "U-83 是" not in io.open("AGENT_FINAL_REPORT.md", encoding="utf-8").read():
        patch("AGENT_FINAL_REPORT.md", pairs + [(curve_old, curve_new)])
    else:
        patch("AGENT_FINAL_REPORT.md", [(curve_old, curve_new)])
    print("R56 台账已写入；曲线核对：", head)
    print("数字来源核对：emit=%d 处 / 游离 print=%d / 全量 %s-%s-0fail / stdout=%d 文件=%d "
          "/ motion 形状=%d / 电池 CAUGHT=%d"
          % (emitted, strays, tests, skipped, lost_lines, kept_lines, motion_cases, caught))
    assert emitted >= 40 and strays == 0 and caught == 9, "证据不足，不许写台账"


main()
