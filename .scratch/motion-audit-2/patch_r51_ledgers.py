#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R51 台账（第 53 轮 / D-110 / U-77 / BACKLOG 71 补实测 + 新开 76 / CHANGELOG / Round 51 / 报告对账）。

数字来源（全部实测，不抄记忆）：
  M249–M252 CAUGHT / M253 按设计绿   <- /tmp/r51_mutations.log
  同一次跑的三行读数                 <- 上面日志里的 `RD |` 与预检两行
  750 例 / 29 skip / 0 failures      <- /tmp/r51-full.log（R50 与 R51 合并验证的那一遍）
  0 告警 / 116 帧 CHANGED=0          <- /tmp/r51-build.log、上面同一遍
  闸门                               <- 离屏 `红=0`；地板闸门本机**无输入**（见 STATE 里那句）
  暗/亮热图台阶 Δ                    <- .scratch/motion-audit-2/heat_ladder_preview.py 对 /tmp/r51-frames 的实测
曲线由 curve_from_ledger.py 重算，并做前缀对账（U-73 那一族的规矩）。
"""
import io
import os
import re
import subprocess

os.chdir("/Users/wangziyi/Codex_Project0")

ROUND = '''
---

## 第 53 轮 · R51：上一轮那条判据红得**不正确** —— 它测的是后台写，不是主线程写（U-77 / D-110 / BACKLOG 76）

### 开场缺陷清单（坐标）

| 位点 | 现状 | 缺陷 |
|---|---|---|
| `CapturePathWriteBudgetTests.testAddingACopyWritesNothingOnTheMainThread`（R49 版） | 复制前后各拍一次"临时目录里有哪些文件"，多一个就红 | **测错了对象**。`FileHistoryPersistence` 的原子写在**后台** `saveQueue` 上留下 `history.json.sb-11faeef9-PWSNBE`，快照分不清"主线程同步写"与"后台正在写"。它在本机第一次全量跑就红，CI run 38538371464 也红 —— 而目标禁的是"**同步**磁盘写"，异步后台写正是设计要求的形状 ⇒ 两条红都是判据的错 |
| R49 的时长判据 | 40 个样本全在"几条记录"的小库里测 | 这条链的主线程成本**随库大小增长**（同一次跑：小库 median 0.55ms ⇒ 480 条时 2.47ms，4.5 倍）。"不许有同步磁盘写"最要紧的一天是接近 500 条上限那天，只测小库等于没测 |
| R51 **第一版**新加的前提断言 | `XCTAssertGreaterThanOrEqual(seeding.entries.count, Self.fullArchiveEntries - 20)` | **自适应阈值恒真**：把 `fullArchiveEntries` 改小，地板跟着一起缩（480→1 时地板变成 -19，永远绿）。设计 M251 时才看见 —— 与 `sampleCount`/`minimumSampleCount` 必须分开是同一族，我上一轮刚记过一次 |

### 修法

1. **判据一换成"堵住写队列"**：注入一个串行 `DispatchQueue`，先 `async { blocked.wait() }` 把它堵死，
   再从产品入口 `store.add(...)`。
   ① 堵着 ⇒ 盘上不许出现 `history.json`，也不许出现 `daily-copy.json`（写如果发生在调用线程，
   它绕不开这个堵：要么当场出现文件，要么直接卡住 ⇒ 两种都红）；
   ② `blocked.signal()` 放开之后两个文件**都必须出现** —— 这一句是对照组。
   没有对照组，"没写盘"可以靠"根本没接上盘"来绿（M250 就是去把闸门焊死，看这条会不会红；它红了）。
2. **新增判据三：快满的库**。先用真持久化造 480 条、重新开一个"写队列被堵住"的库
   （此时主线程只剩快照与这条链上的其它工作），再采 40 个样本。门槛 20ms 从四次实测推导
   （`median=2.34 / 2.43 / 2.47 / 2.49ms`、`p95=2.56 / 2.64 / 3.39 / 5.91ms` ⇒ 按**最差**那一遍留 8 倍）。
3. **前提地板改成独立绝对数** `fullArchivePremiseFloor = 400`，与 `fullArchiveEntries` 脱钩。
4. 删掉 R49 那两条随快照一起失效的辅助函数（`snapshot(of:)` / `difference(_:_:)`）。

### 三条判据各管什么（M249 与 M253 把边界量出来了）

- **M249（产品侧：`save` 不排队列，在调用线程 `perform()`）** ⇒ 行为判据红了，
  而**同一支变异下时长判据打印 `add 用时=2.54ms`，仍然绿**。
  也就是说在小库上"真的同步写一次盘"只值 2ms：任何按 ms 定的门槛要么松到抓不住它，
  要么紧到在 CI 那台更慢的机器上恒红（R38 那条规矩）。**这两条不是冗余，是互不覆盖。**
- **M253（灵敏度：把 `saveSnapshot` 真跑两遍）** ⇒ **按设计绿**，而且它推翻了我本轮先写的一句话。
  我原本在注释里写"这条测的是整库快照，因为它在调用线程上跑"；实测 median 只从 2.43 涨到 2.93ms
  ⇒ 整库快照只占约 0.5ms（median 的五分之一），剩下那 1.9ms 在别处。
  注释与失败消息都改了：红了之后第一件事是**分段量**，不是直接搬 `saveSnapshot`
  （那是把两成的问题解决成全部的问题）。分段量这件事开成 **BACKLOG 76**。
- M250（闸门永远不放开）与 M252（账本永不落盘）红在两个对照组上 —— 它们证明"没写盘"那两条不是空话。

### 真实视觉审查

本轮零产品改动、116 帧逐字节不变。看的是**上一轮欠的那张暗档热图**：
`heatmap-cell-strip-still-90x140-dark.png`（180×280 px，两列 × 七行，格子在 x=32–53 与 x=88–109）。
眼睛的结论是"最下面两行里，第 1 档和空格子我分不出来"，顺手用
`.scratch/motion-audit-2/heat_ladder_preview.py` 把"几乎同色"变成一个数（Rec.709 亮度，
本仓库那把 `perceptibleBand255 = 18` 的尺）：

| 台阶 | 暗档 Δ | 亮档 Δ |
|---|---|---|
| 背景 → 空格子 | +15 | −12 |
| 空 → 第 1 档 | +13 | +13 |
| 第 1 → 第 2 档 | +17 | +23 |
| 第 2 → 第 3 档 | +21 | +42 |
| 第 3 → 第 4 档 | —（顶档） | —（顶档） |

**两种外观下最低两级都过不了 18 这条线**（暗档 15/13，亮档 12/13）。
⇒ "0 次"与"1 次"在两种模式下都会被抹成同一个意思，这不是审美问题是数据可读性问题。
数字已写进 BACKLOG 71，判据与（可能的）梯子数值改动留给 R52 —— 那会改像素，帧基线要 `update`。

### 验证

- 变异 M249–M252 四支该红的全红（`该红没红=0 还原不干净=0`），M253 按设计绿并给出分辨率结论。
- `swift build --build-tests` **0 告警**；全量 **750 例 / 29 skip / 0 failures**；
  离屏闸门 `passed=721 skipped=29 failed=0 NOT_RUN=0 红=0`；116 帧 `CHANGED=0 MISSING=0 ADDED=0`；
  脚本 101 全绿。**动效覆盖地板闸门本机没有输入**：motion 场景判据要
  `CLIPBOARD_HISTORY_UI_MOTION=1` 才跑（会抢前台），本机全量跑里是 skip ⇒
  那一门的 `MOTION_FLOOR_NO_RESOLVE` 是**喂错了日志**（我把全量日志喂给它），不是产品退化；
  它的真结论只能等 runner。
- **R49 的电池自己也会烂**：拿 M244 的锚点再注入一次，脚本在 `apply()` 处中止 ——
  原文是 `注入中止：那段话出现 0 次，不是 1 次 —— 电池与代码脱节`（锚点
  `for case let url as URL in walked {` 随那条被本轮删掉的判据一起没了）。
  这是 `apply()` 的计数自检第一次撞在**真实的腐烂**上，而不只是防重复匹配。
- 自评 **94 / 100**（`性能` 已在 15/15 的天花板：本轮做的事就是把"主线程花多久"变成三个可红的数）。

'''

DECISION = '''
---

## D-110（R51）：一条判据红了，先问"它红的那件事是不是它说的那件事"

**背景**：R49 给"采集路径上不许有同步磁盘写"立了第一条会红的判据。它在本机全量跑与 CI 上都红了。
如果当时按"红了 = 产品有同步写"去改产品，就会为了一个不存在的问题动 `FileHistoryPersistence`。

**决定**：
1. **红先对账再修**。这条判据红在多出来的那个文件是 `history.json.sb-XXXX` —— 原子写的临时文件，
   由后台 `saveQueue` 创建。它证明的是"有写在跑"，不是"主线程在写"。判据测错了对象，撤回重写。
2. **能区分"同步"与"异步"的只有阻塞，不是快照**：把注入的写队列堵起来，
   同步写绕不开堵（当场出现文件或卡住超时），异步写必然被推迟。
   再加一句"放开闸门之后必须出现"当对照组，否则"没写盘"能靠"根本没接上盘"来绿。
3. **判据的分辨率要写进判据**。M249 证明同步写只值 2.54ms ⇒ 时长门槛抓不住它，
   这句话就写在 `blockedQueueBudgetMilliseconds` 的注释里，防止下一个人以为时长那条也在管同步写。
4. **前提断言的地板不许由它要保护的那个变量推导**（M251：`fullArchiveEntries - 20` 恒真）。
   与 `sampleCount` / `minimumSampleCount` 分开是同一条规矩的第二次兑现。

**代价**：判据多一条（480 条造库那一遍约 1.5s）；注释变长；
以及一条不体面的公开边界 —— 这条时长判据防得住数量级的退化，防不住 2 倍。
'''

BACKLOG_71_APPEND = '''
    **R51 的预览实测**（`.scratch/motion-audit-2/heat_ladder_preview.py`，对
    `heatmap-cell-strip-still-90x140-{dark,light}.png`，Rec.709 亮度、`perceptibleBand255 = 18`）：
    暗档 背景→空格子 Δ=+15、空→第 1 档 Δ=+13、第 1→2 档 +17、第 2→3 档 +21；
    亮档对应 12 / 13 / 23 / 42。⇒ **两种外观下最低两级都低于 18**，
    "0 次"与"1 次"在两种模式下都分不开。R47 那句看图结论现在有了数。
    R52 该做的：把这条变成 `renderCell` 上的判据（相邻档 Δ ≥ 从实测推导的地板），
    并决定是抬 `empty` 还是抬梯子第 1 级 —— 改数值要同时改判据期望并 `frame_baseline.py update`。
'''

BACKLOG_76 = '''
76. **主线程那条链没有分段读数**（R51 / M253 实测开）：480 条的库里一次复制 `median≈2.4ms`，
    而把整库快照 `saveSnapshot` 跑两遍只涨 0.5ms ⇒ **快照只占约 1/5**，剩下 1.9ms 不知道在哪
    （候选：`ClipboardEntryIntelligenceAdapter` 的整库摘要、去重索引、降采样规划、`@Published` 引发的视图 diff）。
    现在这条判据只能说"总共多少"，不能说"哪一段在长"。
    为什么现在不修：目标里那句硬要求是"**不许有同步磁盘写**"，那一条已经由行为判据钉住（M249 会红）；
    这 1.9ms 里没有写盘，是纯计算，且 2.4ms 远在可感知线（≈100ms）之下。
    什么时候必须修：`CAPTURE_PATH_FULL_ARCHIVE` 的 median 涨到接近门槛（20ms）的一半时 ——
    那时"先分段再决定搬什么"就不再是可选，因为盲搬会把两成的问题当全部（本轮我自己就先写错了这句话）。
    怎么量：在 `HistoryStore.add` 的四个段各打一次 `DispatchTime`，用一条真判据（从产品入口）断言
    "任一段的 median ≤ 总 median 的 60%"，超了就把那一段的名字打出来。
'''

BATCH = '''

---

## 批次 53 · R51：零产品改动；一条**只有你的眼睛能判**的新问题（BACKLOG 71）

`Sources/` 未动、116 张帧逐字节不变 ⇒ 没换装。本轮改的是判据（采集路径那条），外加一次实测看图。

| # | 请你做的动作 | 我想听到的答案 | 为什么只有你能判 |
|---|---|---|---|
| 53.1 | 设置 → 统计，看那张日历热图**最下面几档**：图例里"最少"那一格，和它右边"1 次"那一格 | 是**两个不同的颜色**，还是**看起来同一格**？ | 我的尺子给出 Δ=13–15（低于本仓库 18 那条线），但 Δ 是我自己定的近似；"人眼在真实屏幕上分不分得开"只有你判得了 |
| 53.2 | 库里已经有几百条记录时，连续复制几条，注意 ⌘C 之后那一下 | 有没有**任何**停顿感（哪怕很轻）？ | 我量到的是 median 2.4ms（远在人能感觉到的 ~100ms 之下），但我的门槛要退化 8 倍才红 —— 你说"有"，就是门槛错，不是产品错 |

延续有效、仍然欢迎回答的：**批次 43、44、45、47、49、50、51、52 共 24 条**。
最想要的三条：45.1（导出反馈弹不弹模态）、47.1（悬停那一圈真鼠标出现没有）、**52.1（快速选择浮层里移动到底动没动）**。
'''

CHANGELOG = '''### Fixed（R51：上一轮那条"同步写盘"判据测错了对象）
- `CapturePathWriteBudgetTests.testAddingACopyWritesNothingOnTheMainThread` 从"目录快照不许多文件"
  改成"**把注入的写队列堵起来**"：堵着 ⇒ 盘上不许出现 `history.json` / `daily-copy.json`；
  放开闸门 ⇒ 两个都必须出现（对照组）。
  旧那条在全量跑与 CI（run 38538371464）上都红，而红得不对 —— 多出来的
  `history.json.sb-11faeef9-PWSNBE` 是**后台** `saveQueue` 的原子写临时文件，
  目标禁的是"**同步**磁盘写"，异步写正是设计要求的形状。
- 新增 `testAddingACopyWithANearlyFullArchiveStaysInsideBudget`：480 条的库 + 堵住的队列，
  测"主线程只剩这条链"时一次复制花多久（本机 median 2.34–2.49ms，门槛 20ms 按最差那一遍推导）。
  旧的两条时长判据只测了几条记录的小库，而这条链的成本随库大小增长（0.55ms → 2.47ms）。
- 前提断言的地板与造库数量脱钩（`fullArchivePremiseFloor = 400`）：
  第一版写成 `fullArchiveEntries - 20` ⇒ 自适应阈值恒真，M251 才把它抓出来。
- 注释与失败消息里那句"这条测的是整库快照"被 M253 推翻并改正：快照只占 median 的约 1/5，
  红了之后要先分段量（BACKLOG 76），不要直接搬 `saveSnapshot`。
- 删掉随旧判据一起失效的两个辅助函数。变异 M249–M252 四支全 CAUGHT，M253 按设计绿（灵敏度实测）。
- 产品代码零改动，116 张帧逐字节不变。

'''

VISUAL = """
---

## Round 51 · 红了之后先问：它红的那件事，是不是它说的那件事（R51 / U-77 / D-110 / BACKLOG 76）

**这一轮问的问题**：R49 那条"采集路径不许同步写盘"的判据，在全量跑与 CI 上都红了。
第一反应是"产品里有同步写"。第二反应应该是：**它红的那个文件是谁写的？**

**答案是后台写的。** `history.json.sb-11faeef9-PWSNBE` 是原子写的临时文件，
由 `saveQueue` 在后台创建 —— 目录快照分不清"主线程同步写"与"后台正在写"，
所以它测的是错的东西。判据撤回重写：把注入的写队列**堵起来**再复制，
同步写绕不开堵（当场出现文件或卡住），异步写必然被推迟；
再加一句"放开闸门之后必须出现"当对照组，否则"没写盘"能靠"根本没接上盘"来绿。

**两支变异把边界量出来了**：
- M249（真把写搬回调用线程）：行为判据红，**时长判据仍然绿**（`add 用时=2.54ms`，门槛 10ms）。
  ⇒ 在小库上同步写只值 2ms，任何 ms 门槛要么松到抓不住它、要么紧到在 CI 上恒红。
  两条判据不是冗余，是互不覆盖 —— 这句话现在写在门槛的注释里。
- M253（把整库快照跑两遍）：**按设计绿**，而它顺手推翻了我本轮先写的一句注释。
  median 只从 2.43 涨到 2.93ms ⇒ 快照只占五分之一，剩下 1.9ms 在别处。
  我把"这条测的是快照成本"写进注释时没量过 —— 第 N 次犯"数只能从读数来"。

**真实视觉审查**：本轮没有新帧。看的是欠了两轮的那张暗档热图
（`heatmap-cell-strip-still-90x140-dark.png`，格子在 x=32–53 / x=88–109），
并把"最下面两行我分不出来"变成数：暗档最低两级 Δ=15 / 13，亮档 12 / 13，
全部低于本仓库自己的恰可察觉线 18 ⇒ BACKLOG 71 从"看图觉得"升级成"有数了，等判据"。

**分数为什么持平**：`性能` 已经在 15/15 的天花板 —— 本轮做的事就是把"主线程花多久"
变成三个可红的数，而它换不来维度上的分。`流畅度` 仍 13/20：连续七轮在尺子上，
R52 该回到像素（BACKLOG 71 会改格子颜色，帧基线要 update）。

### 自评 94 / 100（与 R45–R50 持平）

| 维度 | 得分 | 说明 |
|---|---|---|
| 原生感 | 18 / 20 | 产品零改动 |
| 流畅度 | 13 / 20 | 沿用；R52 回到像素 |
| 层次与材质 | 15 / 15 | 116 帧逐字节不变；暗档热图那三级 Δ 已入账 |
| 动效细节 | 14 / 15 | 沿用 |
| 交互反馈 | 10 / 10 | 沿用 |
| 可访问性 | 9 / 10 | 沿用（读屏播报仍未核，独立一轮） |
| 性能 | 15 / 15 | 本轮的主战场：采集链从"没数"变成三条判据 + 一个实测边界 |

**验证**：M249–M252 全 CAUGHT、M253 按设计绿（灵敏度已写进注释）、0 告警、
750 例 / 29 skip / 0 failures、离屏闸门 `红=0`、116 帧不变、脚本 101 全绿。
**动效覆盖地板闸门本机无输入**（motion 场景判据要 `CLIPBOARD_HISTORY_UI_MOTION=1`）⇒ 等 runner。
"""

STATE = """

---

## R51 · 那条判据红得不正确：它测的是后台写，不是主线程写（第 53 轮 / U-77 / D-110 / BACKLOG 76）

- **靶**：R49 立的"采集路径不许同步写盘"判据在全量跑与 CI（run 38538371464）都红。
  对账之后：**红得不对** —— 多出来的是 `history.json.sb-XXXX`，后台 `saveQueue` 的原子写临时文件。
  目录快照分不清同步与异步 ⇒ 判据测错了对象（U-77）。
- **修法**：注入的串行写队列**先堵起来**再 `store.add` ⇒ 堵着不许出现 `history.json` / `daily-copy.json`，
  `blocked.signal()` 之后两个都必须出现（对照组）。没有对照组，"没写盘"能靠"没接上盘"来绿（M250 试了，红）。
- **新增一条**：480 条的库 + 堵住的队列 ⇒ 主线程只剩这条链时一次复制多久。
  四次实测 `median=2.34 / 2.43 / 2.47 / 2.49ms`、`p95=2.56 / 2.64 / 3.39 / 5.91ms` ⇒ 门槛 20ms（最差 median 的 8 倍）。
  旧那两条只测了几条记录的小库，而这条链的成本随库大小增长（同一次跑 0.55 → 2.47ms）。
- **两条判据互不覆盖（M249 实测）**：真把写搬回调用线程之后，行为判据红，
  时长判据打印 `add 用时=2.54ms` **仍然绿** ⇒ 小库上同步写只值 2ms。这句话写进门槛注释，
  防止下一个人以为时长那条也在管同步写。
- **本轮自己错两处**：① 新加的前提断言写成 `fullArchiveEntries - 20` ⇒ 自适应阈值恒真，
  设计 M251 时才发现（与 `sampleCount`/`minimumSampleCount` 同一族，上一轮刚记过一次）；
  ② 注释里写"这条测的是整库快照"，M253 实测 median 只涨 0.5ms ⇒ 快照只占 1/5，
  注释与失败消息都改了，分段量开成 **BACKLOG 76**。
- **真实视觉审查**：零产品改动、116 帧逐字节不变。看的是暗档热图（`heatmap-cell-strip-still-90x140-dark.png`），
  并用 `heat_ladder_preview.py` 把"分不出来"变成数：暗档最低两级 Δ=15 / 13、亮档 12 / 13，
  全部低于 `perceptibleBand255 = 18` ⇒ BACKLOG 71 有数了，R52 去做判据（会改像素，帧基线要 update）。
- **验证**：M249–M252 四支全 CAUGHT、M253 按设计绿；`swift build --build-tests` **0 告警**；
  全量 **750 tests / 29 skipped / 0 failures**；离屏闸门 `passed=721 skipped=29 failed=0 NOT_RUN=0 红=0`；
  116 帧 `CHANGED=0 MISSING=0 ADDED=0`；脚本 **101 全绿**。**不换装**。
  **动效覆盖地板闸门本机没有输入**（motion 场景判据要 `CLIPBOARD_HISTORY_UI_MOTION=1` 才跑，
  全量跑里是 skip）⇒ 本机那一门的 `MOTION_FLOOR_NO_RESOLVE` 是喂错日志，不是产品退化；真结论等 runner。
  自评 **94 / 100**。
- **R50 与 R51 合并验证**：全量那一遍跑在两轮的树上（R50 单独那个提交没有被全量扫过，CI 跑 tip）。
- **下一步（R52）**：① **BACKLOG 71**（相邻档 Δ 判据 + 抬 `empty` 或抬第 1 级，改像素要 update 帧基线）；
  ② 读 R50/R51 的 CI：`MOTION_NATIVE_MOVE 判定=` 落在哪一格、`MOTION_RESOLVE_SUMMARY` 的 not-run 名单；
  ③ BACKLOG 72（其余调用点还在跨度上 —— 已有 `.scratch/motion-audit-2/answer_backlog_72.py`，
  它自检复现了夹具的 135ms vs 45ms，缺的是带 `CLIPBOARD_HISTORY_UI_MOTION=1` 的真胶片日志）。
"""


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
    """带标记的追加：崩过一次的脚本重跑不该留下两份台账。"""
    current = io.open(path, encoding="utf-8").read()
    if marker in current:
        print("跳过（已写过）：%s  ← %s" % (path, marker))
        return
    with io.open(path, "a", encoding="utf-8") as f:
        f.write(text)


def main():
    backlog = io.open("AGENT_BACKLOG.md", encoding="utf-8").read()
    anchor_71 = ("    并且帧基线要 `update`，因为格子颜色会变）。")
    anchor_75_tail = ("    人工批次 52.1 同时问用户的眼睛（快速选择浮层里候选重排那一下有没有滑）。")
    assert backlog.count(anchor_71) == 1, ("BACKLOG 71 锚点", backlog.count(anchor_71))
    assert backlog.count(anchor_75_tail) == 1, ("BACKLOG 75 末尾锚点", backlog.count(anchor_75_tail))

    report = io.open("AGENT_FINAL_REPORT.md", encoding="utf-8").read()
    pairs = [
        ("| 阶段二 **43 轮**审计（R9–R50） | 跑满（要求 ≥20），每轮有可编译改动 + 七维自评 + 真实看图 "
         "| `AGENT_VISUAL_ITERATION.md` Round 9–50 |",
         "| 阶段二 **44 轮**审计（R9–R51） | 跑满（要求 ≥20），每轮有可编译改动 + 七维自评 + 真实看图 "
         "| `AGENT_VISUAL_ITERATION.md` Round 9–51 |"),
        ("| 决定台账 | D-069 … D-109 | `AGENT_DECISIONS.md` |",
         "| 决定台账 | D-069 … D-110 | `AGENT_DECISIONS.md` |"),
        ("| 判据 | 653 → **748** 例（29 skip / 0 failures",
         "| 判据 | 653 → **750** 例（29 skip / 0 failures"),
        ("+ **M100–M248**（阶段二 149 支），全部 CAUGHT（",
         "+ **M100–M253**（阶段二 154 支），全部 CAUGHT（**M253 是唯一按设计绿的：它不测判据有没有牙，"
         "测的是尺子的分辨率**（U-77）；"),
        ("R46 / R47 / R48 各一张不加（三轮都零产品改动，116 帧 `CHANGED=0 MISSING=0 ADDED=0`） |",
         "R46 / R47 / R48 各一张不加（三轮都零产品改动，116 帧 `CHANGED=0 MISSING=0 ADDED=0`）"
         "· R49 / R50 / R51 同样一张不加（三轮都零产品改动；最后一遍是 2026-10-14 的全量跑，"
         "`CHANGED=0 MISSING=0 ADDED=0`） |"),
        ("| 视觉台账 | U-31 … U-76（46 条；", "| 视觉台账 | U-31 … U-77（47 条；"),
        ("U-76 是**探针改了产品没改的东西，再把结论算在产品头上**",
         "U-77 是**判据红得不对**：R49 那条「采集路径不许同步写盘」把后台原子写的 `history.json.sb-XXXX` "
         "当成主线程同步写，全量跑与 CI 都红，而红的是尺（R51 撤回重写成「堵住写队列 + 放开必须出现」，"
         "并用 M249 量出时长判据抓不住同步写）；\n"
         "U-76 是**探针改了产品没改的东西，再把结论算在产品头上**"),
        ("| `AGENT_UI_AUDIT.md` 第 10–52 轮 |", "| `AGENT_UI_AUDIT.md` 第 10–53 轮 |"),
    ]
    changelog = io.open("CHANGELOG.md", encoding="utf-8").read()
    anchor_cl = "## [Unreleased]\n\n### Fixed（R50"
    if "### Fixed（R51" not in changelog:
        assert changelog.count(anchor_cl) == 1, ("CHANGELOG 锚点", changelog.count(anchor_cl))
    # 先验全部锚点再动手（上一版脚本写到一半崩过，留下半截台账 —— U-73 那一族）。
    if "U-77 是" not in report:
        for old, _ in pairs:
            assert report.count(old) == 1, ("FINAL_REPORT 锚点", report.count(old), old[:80])

    # 每一段都带"已经写过就跳过"的标记：这一族脚本在 R48 与本轮都写到一半崩过，
    # 重跑一次就留下两份台账 —— 那比不写更糟（对账时没人能看出哪一份是真的）。
    append_once("AGENT_UI_AUDIT.md", "## 第 53 轮 · R51", ROUND.lstrip("\n"))
    append_once("AGENT_DECISIONS.md", "## D-110（R51）", DECISION)
    append_once("AGENT_VISUAL_ITERATION.md", "## Round 51 ·", VISUAL)
    append_once("AGENT_STATE.md", "## R51 · 那条判据红得不正确", STATE.lstrip("\n"))
    append_once("docs/MANUAL_TEST_v1.4.9_round3.md", "## 批次 53 · R51", BATCH)
    backlog_pairs = []
    if "**R51 的预览实测**" not in backlog:
        backlog_pairs.append((anchor_71, anchor_71 + "\n" + BACKLOG_71_APPEND.strip("\n")))
    if "76. **主线程那条链没有分段读数**" not in backlog:
        backlog_pairs.append((anchor_75_tail, anchor_75_tail + "\n" + BACKLOG_76.strip("\n")))
    if backlog_pairs:
        patch("AGENT_BACKLOG.md", backlog_pairs)
    if "### Fixed（R51" not in changelog:
        patch("CHANGELOG.md", [(anchor_cl, "## [Unreleased]\n\n" + CHANGELOG + "### Fixed（R50")])
    # 曲线要在 Round 51 落进台账之后再解析（先写后读，否则 n 少一轮）。
    head, curve_old, curve_new = check_curve(44, 51)
    if "U-77 是" not in io.open("AGENT_FINAL_REPORT.md", encoding="utf-8").read():
        patch("AGENT_FINAL_REPORT.md", pairs + [(curve_old, curve_new)])
    else:
        patch("AGENT_FINAL_REPORT.md", [(curve_old, curve_new)])
    print("R51 台账已写入；曲线核对：", head)


main()
