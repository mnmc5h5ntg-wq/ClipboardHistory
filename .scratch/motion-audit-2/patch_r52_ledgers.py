#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R52 台账（第 54 轮 / D-111 / U-78 / BACKLOG 71 轴更正 + 新开 77、78 / CHANGELOG / Round 52 / 报告对账）。

数字来源：
  两次 CI 红的原文        <- gh run view 38543090198 / 38543812477（逐步骤读过，见 ROUND 里的引用）
  登记放宽的依据          <- run 38538371464 与 38543812477 的 `clock-coarse-in-window` 毫秒数
  脚本自测 101 → 105      <- `python3 -m unittest discover -s scripts/tests`（本机实跑，OK）
  变异 M254–M259 全 CAUGHT <- /tmp/r52_mutations.log（电池自己复跑一遍确认还原后 OK）
  热图台阶的通道读数      <- .scratch/motion-audit-2/heat_ladder_preview.py 对 /tmp/r51-frames 的实测
曲线由 curve_from_ledger.py 重算并做前缀对账。
"""
import io
import os
import re
import subprocess

os.chdir("/Users/wangziyi/Codex_Project0")

ROUND = '''
---

## 第 54 轮 · R52：覆盖率地板第一次在 runner 上开口说话，说的是"我的登记与实际不符"（U-78 / D-111 / BACKLOG 77、78）

### 开场缺陷清单（坐标）

| 位点 | 现状 | 缺陷 |
|---|---|---|
| CI run 38543090198 的 `Motion coverage floor` | `MOTION_FLOOR_NO_RESOLVE`（红） | 红**没有名字**。那一次整族一条 `MOTION_*` 读数都没打，而 CI 步骤只 `grep MOTION_NOT_RUN=`；XCTest 层 `XCTSkipUnless` 打的是中文句子（"动效胶片探针：设 … 才跑"），不带那个前缀 ⇒ 解释"为什么整族没跑"的那一行从来没被打出来过（R36 的规矩在这里断了） |
| CI run 38543812477 的同一格 | `MOTION_FLOOR_BAD_REASON notice-banner 的理由是 clock-coarse-in-window，而登记过的是 无` | 闸门是对的，**登记是旧的**：R46 那句"runner 上四次全部判到 ⇒ 要求它判到"已经被两次实测推翻（38538371464 最粗 76ms/声明 150ms；38543812477 同一理由）。本机这一臂一直是 `premise-not-visible` |
| `MOTION_FLOOR_OK` 的打印条件 | 只在"一条结果都没有"时打 | 加了非红的提示行（SKIPPED / THIN）之后，"绿但有话要说"在日志里长得像"什么都没判" |
| 登记表放宽之后的地板 | 地板从 3 降到 2 | 放宽的**副作用**：任何 `must_judge` 臂缺席都会先撞 `BAD_REASON`（它没登记理由）⇒ `UNDERCOVERED` 再也无法单独红。旧的那格自测（`under_covered`）因此悄悄失效，是 `test_ci_report_selftest` 抓住的 |

### 修法

1. **红必须有名字**：`NO_RESOLVE` 之后紧跟一行 `MOTION_FLOOR_SKIPS n=… 测试名：原因…`，
   由新解析器从 `Test Case … : Test skipped - <原因>` 里读 —— **不要求原因带我的前缀**。
2. **登记跟着测量走，且必须留证据**：`notice-banner` 改成 `must_judge=false` +
   允许 `clock-coarse-in-window` / `premise-not-visible`，note 里写清是哪两次 run、多少毫秒。
   新增一条自测 `testRelaxedArmsMustCiteARunId`：**任何放宽的臂，note 里必须有 run 号或夹具路径** ——
   这一格防的就是"为了让 CI 变绿而把登记改松"（本仓库记过一整族）。
3. **`MOTION_FLOOR_THIN`（不红，但必须说）**：横幅那一族两臂**同时**判不到时打一行。
   不红是因为两台机器今天都做不到（声明 150/120ms，段内最粗实测 runner 73–76ms、本机 96–101ms，
   都粗过 0.5×声明）；要说是因为不说就会变成"这一族没被看"的常态。红仍然留给新形状。
4. **地板那一格换成一个仍然只有地板能抓的形状**：`judged=1/4` 而 not-run 名单只有两条已登记的横幅臂
   ⇒ `judged` 与名单**不自洽**（判据说谎），`REDS=1` 钉住"只有地板这一条红"。
5. `MOTION_FLOOR_OK` 改成"没有红就打"，与 THIN/SKIPPED 共存。

### 真实视觉审查（这一轮看的是上一轮那张表用错了轴）

R51 写进台账的那句"暗档 0 次 vs 1 次只差 4/255"，**度量轴选错了**（本仓库记过这一族：
只用亮度判两态可否分辨是用错轴）。`VisualHeat.empty` 用 `primary`（灰），四档数据用 `accent`（蓝），
所以"空 → 第 1 档"那一步主要是**色相翻转**而不是明度变化：

| 相邻台阶 | Δ亮度 | Δ最大通道 |
|---|---|---|
| 背景 → 空格子 | 暗 +11 / 亮 −12 | 11 / 12 |
| 空 → 第 1 档 | 暗 **+4** / 亮 −13 | **30 / 28** |
| 第 1 → 第 2 档 | 暗 +13 / 亮 −23 | 36 / 35 |
| 第 2 → 第 3 档 | 暗 +17 / 亮 −32 | 49 / 50 |
| 第 3 → 第 4 档 | 暗 +21 / 亮 −42 | 64 / 71 |

⇒ 暗档那一步在 B 通道上差 30/255（41→71），**在亮度轴上是 4，在颜色轴上是 30**。
"0 次与 1 次分不开"这个结论今天**不成立**，它是我用错轴造出来的。
R53 的判据必须建在色度感知的距离上（或至少取通道最大值），并且不许再拿 `perceptibleBand255=18`
那把亮度尺直接套到"灰 vs 蓝"上。人工批次 53.1 因此更关键了：那一眼只有你能判。

本轮没有新的可看画面（零产品改动、零 Swift 改动、116 帧不变）；看的是两张既有帧的**重新读法**。

### 验证

- 脚本自测 **101 → 105**（`Ran 105 tests … OK`）：新增 4 格（silent-run 命名、无前缀 skip 也要捞、
  放宽必须留证据、THIN 不许替 BAD_REASON 兜底），并把 `under_covered` 那一格换成自洽形状。
- 变异 **M254–M259 六支全 CAUGHT**（`红得不对=0 还原不干净=0`，电池跑完自己复跑一遍确认全绿）。
- 闸门对**本机今天那份真日志**（`/tmp/r51-motion.log`）：`MOTION_FLOOR_THIN` + `MOTION_FLOOR_OK=2/4`
  + `REDS=0`，exit 0 —— 这就是"该放行的放行、该说的要说"。
- 产品代码零改动、Swift 判据零改动、116 帧不变 ⇒ **不换装**、不需要 `frame_baseline update`。
- 自评 **94 / 100**。

'''

DECISION = '''
---

## D-111（R52）：登记是测量，不是愿望；放宽必须留证据，且必须把放宽的副作用算出来

**背景**：R46 建的覆盖率地板第一次在 runner 上红，红的是 `notice-banner` 换了坏法。
两条路：把红留着（每天重复、没人能今天修 ⇒ 训练人无视红），或改登记（放宽）。

**决定**：
1. **登记跟着实测走**。`notice-banner` 从 `must_judge=true` 改成放行两个已观测理由，
   note 里写死是哪两次 run、多少毫秒对多少毫秒。
2. **放宽必须留证据，由一条自测钉住**：`testRelaxedArmsMustCiteARunId` 要求任何
   `must_judge=false` 的臂的 note 里出现 run 号或夹具路径。没有出处的放宽 = 测试红。
3. **放宽的副作用必须算出来**：地板从 3 降到 2 之后，`UNDERCOVERED` 失去了单独红的能力
   （任何必须判到的臂缺席都会先撞 `BAD_REASON`）。这一条不是"应该没人发现"，
   而是**必须被自测发现**——它确实被 `test_ci_report_selftest` 发现了（那一格静默失效）。
   于是把 `under_covered` 换成一个只有地板能抓的形状（`judged` 与 not-run 名单不自洽）。
4. **不红不等于不说**：两臂同场缺席打 `MOTION_FLOOR_THIN`。红留给新形状，
   已知事实留一行字 —— 这是 R36（红必须有名字）与 R39（恒红的守卫会被人删）之间的折法。
5. **度量轴错了的数要撤回**：R51 那句"暗档只差 4/255"用的是 Rec.709 亮度，
   而"空 → 第 1 档"是灰→蓝的色相翻转（B 通道差 30）。结论撤回到"未定，等色度判据与人眼"。

**代价**：登记表从此多一个 `thin_warnings` 段；闸门多一个解析器；
以及一条真实的覆盖损失被写成了"已知且被看着"，而不是"被一条恒红掩盖"。
'''

BACKLOG_71_FIX = '''
    **R52 把这条的度量轴更正了（上面那张表的结论作废）**：`perceptibleBand255 = 18` 是**亮度**尺，
    而 `empty` 用 `primary`（灰）、四档用 `accent`（蓝），"空 → 第 1 档"主要是**色相**翻转。
    同一份像素按通道取最大差：暗档那一步是 **30**（B 通道 41→71）、亮档是 28（R 通道 243→215），
    都在 18 之上 —— 所以"0 次与 1 次分不开"这个结论**不成立**，是我用错轴造出来的
    （本仓库记过这一族：只用亮度判两态可否分辨 = 用错轴）。
    R53 的判据因此改成：① 距离必须取**通道最大差或 ΔE**，不许只用 Rec.709 亮度；
    ② 先跑判据再决定改不改数值 —— 现在的数据倾向于"梯子不用动"；
    ③ 人工批次 53.1 的那一眼是这条的**主判据**，我的尺退到"别用错轴"的位置。
'''

BACKLOG_77 = '''
77. **横幅那一族的动效覆盖，两台机器今天都量不到**（R52 开，来自 `MOTION_FLOOR_THIN`）：
    `notice-banner` 声明 150ms、`notice-banner-dismiss` 声明 120ms，
    而"事件段内最粗的一次采样"实测 runner 73–76ms、本机 96–101ms —— 全部粗过 0.5×声明这条分辨率线，
    于是这两臂只能报 `clock-coarse-in-window`（本机 `notice-banner` 甚至是 `premise-not-visible`）。
    R46 的登记表当时把它们写成"必须判到"，R52 按实测放行并打 THIN；**放行不是修好**。
    根因是抓帧器自己：一帧 `cacheDisplay` 在事件段内要 70–100ms（BACKLOG 74 那条的同一件事），
    而 150ms 的过渡只有 2–3 帧可拍。三条候选路（R54 之前先想清楚再动）：
    a) **降每帧成本**：把 `Grabber` 的位图尺寸按 1× 拍（现在按 backingScale 拍 2×，像素数是 4 倍）；
    b) **给判据一个慢动作夹具**：一个 `declared=600ms` 的"故意慢版"横幅，专供量"有没有过程"，
       产品仍按 150ms 走 —— 这不算为过夹具改产品，因为改的是**测试里的注入参数**；
    c) **承认这一族交给人眼**：把它写进人工批次并从覆盖地板里除名（最诚实也最弱，要先有人批准）。
    判"该走哪条"的证据：本机与 runner 各一卷 `MOTION notice-banner*` 的 `时刻ms=[…]` 全列。
'''

BACKLOG_78 = '''
78. **run 38543090198：动效那一族整次没打任何读数，原因至今未证实**（R52 开）：
    `Executed 28 tests`、`胶片: 9`、`motion suite exit: 0`，而 `MOTION_SUMMARY` 与
    `MOTION_RESOLVE_SUMMARY` 一行都没有，`---- 动效读数 ----` 段是空的。
    原始 `motion.log` 没上传，所以**我不能说它是为什么**（R42 那一族：读到 0 要先证三件事）。
    候选：① 场景判据 `testTransitionsAreActuallyRunning` 被 `XCTSkipUnless` skip 掉
    （env 没进到测试进程？它的 skip 原因不带 `MOTION_NOT_RUN=`，所以那一步的 grep 看不见）；
    ② 记录到一半窗口没开成 ⇒ `frames.count <= 4` 走了 `XCTFail`+continue？不，那会打红；
    ③ 打印被 XCTest 吞掉（本机全量跑里也观察到过 stdout 丢失，见 R51 那次
    `CAPTURE_PATH` 在全量日志里一行都没有）。
    R52 已经把这一格变成**有名字的红**（`MOTION_FLOOR_SKIPS` 会把 skip 原因逐条打出来），
    结案条件：下一次 runner 运行里读那一行 —— 它要么直接给出原因，要么证明"连 skip 都没有"，
    那时 ③ 就是唯一剩下的解释，要单独查打印通道。
'''

BATCH_NOTE = '''| 53.1（**R52 更新了这一条的问法**） | 设置 → 统计，看那张日历热图**最下面几档**：图例里"最少"那一格，和它右边"1 次"那一格 | 是**两个不同的颜色**，还是**看起来同一格**？如果不同，是"深浅不同"还是"一个发灰、一个发蓝"？ | R52 发现我上一轮那句"只差 4/255"用错了轴：那是**亮度**尺，而这两格差在**色相**（灰 → 蓝，B 通道差 30）。所以现在连我自己都不能判这件事 —— 第三问正是我要的：如果你答"一个发灰一个发蓝"，那这张图的数据可读性是好的，BACKLOG 71 就不用改数值 |
'''

CHANGELOG = '''### Fixed（R52：覆盖率地板第一次在 runner 上红，红的是登记与实际不符）
- `motion_floor_gate.py`：`NO_RESOLVE` 之后新增一行 `MOTION_FLOOR_SKIPS`，
  把日志里 `Test Case … : Test skipped - <原因>` 逐条打出来。
  以前 CI 那一步只 `grep MOTION_NOT_RUN=`，而 XCTest 层 `XCTSkipUnless` 的中文原因不带这个前缀
  ⇒ run 38543090198 那种"整族一条读数都没有"的红**没有名字**（R36 的规矩断了）。
- 登记表 `motion_floor_expectations.json`：`notice-banner` 从 `must_judge=true` 改成
  放行 `clock-coarse-in-window` / `premise-not-visible`，note 里写死依据
  （run 38538371464 最粗 76ms vs 声明 150ms；run 38543812477 同一理由；本机一直是 premise-not-visible）。
  **登记是测量，不是愿望**（D-111），且新增自测要求任何放宽都必须留 run 号或夹具出处。
- 新增 `MOTION_FLOOR_THIN`（**不红**）：横幅两臂同场缺席时打一行，指向 BACKLOG 77。
- 新增 `thin_warnings` 段；`MOTION_FLOOR_OK` 从"只有一条结果都没有才打"改成"没有红就打"，
  与 THIN/SKIPPED 共存。
- 自测 101 → **105**：`under_covered` 那一格换成"`judged` 与 not-run 名单不自洽"的形状 ——
  因为地板从 3 降到 2 之后，`UNDERCOVERED` 已无法单独红（任何 must_judge 臂缺席都会先撞 `BAD_REASON`）。
  这一格失效是 `test_ci_report_selftest` 抓住的，不是我发现的。
- 更正 R51 写进台账的热图台阶结论：那句"暗档 0 次 vs 1 次只差 4/255"用的是**亮度**轴，
  而该步是灰→蓝的**色相**翻转（B 通道差 30）⇒ 结论撤回，BACKLOG 71 改判轴（R53）。
- 产品代码零改动、Swift 判据零改动、116 帧逐字节不变。变异 M254–M259 六支全 CAUGHT。

'''

VISUAL = """
---

## Round 52 · 覆盖率地板第一次开口，说的是"我的登记旧了"；顺手撤回了上一轮一句用错轴的话（R52 / U-78 / D-111 / BACKLOG 77、78）

**这一轮问的问题**：R50/R51 推上去之后 CI 连红两次，两次都在 `Motion coverage floor`。
第一次是 `NO_RESOLVE`（整族没读数），第二次是 `BAD_REASON notice-banner`。
第一反应是"闸门太敏感"。第二反应应该是：**闸门说的是不是事实？**

**是事实。** 登记里那句"runner 上四次全部判到 ⇒ 要求它判到"是 R46 写的，
而它已经被两次实测推翻（最粗 76ms 对声明 150ms）。所以改的是登记，不是闸门 ——
并且加了一条自测：**以后任何放宽必须在 note 里留 run 号**，否则测试红。
放宽本身不可怕，没有出处的放宽才可怕。

**顺带挖出两件更值钱的事**：
1. 那条"整族没读数"的红**没有名字**：CI 只 grep `MOTION_NOT_RUN=`，
   而 XCTest 层 skip 打的是中文句子。现在闸门自己会把 `Test skipped - <原因>` 逐条打出来。
2. 地板从 3 降到 2 之后，`UNDERCOVERED` **失去了单独红的能力**（任何 must_judge 臂缺席都会先撞
   `BAD_REASON`）。这一格静默失效是 `test_ci_report_selftest` 抓住的，不是我。
   于是把它换成一个只有地板能抓的形状：`judged=1/4` 而名单只登记了两条横幅臂 ⇒ 判据说谎。

**真实视觉审查 —— 撤回上一轮一句用错轴的话**：R51 我写"暗档 0 次 vs 1 次只差 4/255"。
那是 Rec.709 **亮度**轴的数。而 `empty` 是灰（`primary`）、第 1 档是蓝（`accent`），
那一步差的是**色相**：B 通道 41→71，差 30。⇒ 那句"分不开"作废，
BACKLOG 71 从"改梯子数值"改成"先把判据的轴换对"。
这是本仓库记过的同一族（只用亮度判两态可否分辨 = 用错轴），我又犯了一次，
而且是在**已经改过一次归位错**的同一张表上。

**分数为什么持平**：`流畅度` 仍 13/20 —— 连续八轮在尺子上。
BACKLOG 77 现在把这件事写成了具体的量（150ms 的过渡 vs 70–100ms 的每帧成本），
R53/R54 要么把每帧成本降下来，要么给判据一个慢动作夹具。

### 自评 94 / 100（与 R45–R51 持平）

| 维度 | 得分 | 说明 |
|---|---|---|
| 原生感 | 18 / 20 | 产品零改动 |
| 流畅度 | 13 / 20 | 沿用；本轮把"量不到动"写成了有毫秒数的具体缺口（BACKLOG 77） |
| 层次与材质 | 15 / 15 | 116 帧逐字节不变 |
| 动效细节 | 14 / 15 | 沿用 |
| 交互反馈 | 10 / 10 | 沿用 |
| 可访问性 | 9 / 10 | 沿用（读屏播报仍未核，独立一轮） |
| 性能 | 15 / 15 | 抓帧器每帧 70–100ms 这件事本轮被量化了，但还没修 |

**验证**：脚本自测 101 → 105 全绿、M254–M259 六支全 CAUGHT（电池还原后自己复跑一遍确认）、
闸门对本机真日志 `REDS=0` 且打出 THIN+OK。**CI 待读**：下一次 runner 运行要看
`MOTION_FLOOR_SKIPS` 有没有把 38543090198 那次的原因说清楚（BACKLOG 78 的结案条件）。
"""

STATE = """

---

## R52 · 覆盖率地板第一次在 runner 上红，红的是"我的登记旧了"（第 54 轮 / U-78 / D-111 / BACKLOG 77、78）

- **靶**：R50/R51 推上去之后 CI 连红两次，都在 `Motion coverage floor`：
  run 38543090198 `NO_RESOLVE`（整族零读数），run 38543812477
  `BAD_REASON notice-banner 的理由是 clock-coarse-in-window，而登记过的是 无`。
- **闸门说的是事实，旧的是登记**：R46 那句"runner 上四次全部判到"已被两次实测推翻
  （最粗 76ms vs 声明 150ms；本机这一臂一直是 `premise-not-visible`）
  ⇒ `notice-banner` 改成 `must_judge=false` + 放行那两个理由，note 写死 run 号与毫秒（D-111）。
- **放宽必须留证据**：新增自测 `testRelaxedArmsMustCiteARunId` ——
  任何 `must_judge=false` 的臂，note 里没有 run 号或夹具路径就红。没有出处的放宽 = 测试红。
- **红必须有名字**：`NO_RESOLVE` 之后新增 `MOTION_FLOOR_SKIPS`，逐条打 `Test skipped - <原因>`。
  CI 那一步只 grep `MOTION_NOT_RUN=`，而 XCTest 层 `XCTSkipUnless` 的中文原因不带这个前缀
  ⇒ 整族缺席那种红以前**说不出为什么**。
- **不红不等于不说**：新增 `MOTION_FLOOR_THIN`（非红）—— 横幅两臂同场缺席时打一行，指向 BACKLOG 77
  （150/120ms 的过渡 vs 段内最粗 73–101ms 的每帧成本 ⇒ 两台机器今天都分辨不了）。
  这是 R36（红必须有名字）与 R39（恒红的守卫会被人删）之间的折法。
- **放宽的副作用被自测抓住，不是被我抓住**：地板 3→2 之后 `UNDERCOVERED` 再也无法单独红
  （任何 must_judge 臂缺席都会先撞 `BAD_REASON`）——`test_ci_report_selftest` 的 `under_covered`
  那一格当场失效。换成只有地板能抓的形状：`judged=1/4` 而 not-run 名单只登记两条横幅臂
  ⇒ **`judged` 与名单不自洽**（判据说谎），并用 `REDS=1` 钉住"只有这一条红"。
- **撤回一句用错轴的话**：R51 的"暗档 0 次 vs 1 次只差 4/255"是 Rec.709 **亮度**；
  那一步实际是灰→蓝的**色相**翻转（B 通道 41→71，差 30）⇒ 结论作废，
  BACKLOG 71 改成"先把判据的轴换对，再谈要不要改数值"。同一张表我在这轮里错过位两次
  （一次归位、一次轴），都属于"只用亮度判两态 = 用错轴"那一族。
- **验证**：脚本自测 **101 → 105**（`Ran 105 … OK`）、变异 **M254–M259 六支全 CAUGHT**
  （`红得不对=0 还原不干净=0`，电池跑完自己复跑一遍确认全绿）、
  闸门对本机真日志 `/tmp/r51-motion.log` ⇒ `THIN + OK=2/4 + REDS=0`、exit 0。
  产品零改动、Swift 判据零改动、116 帧不变 ⇒ **不换装**、不需要 `frame_baseline update`。自评 **94 / 100**。
- **CI 待读**：下一次运行看 `MOTION_FLOOR_SKIPS` 有没有把 38543090198 那次的原因说清楚
  （BACKLOG 78 的结案条件），以及 `MOTION_NATIVE_MOVE 判定=` 是否终于出现（BACKLOG 75）。
- **下一步（R53）**：① `MOTION_NATIVE_MOVE` 那行打印要挪到 `requireAppWasActive` **之前**
  （现在两臂读数打了、结论行被 skip 挡在后面 ⇒ runner 跳过时永远看不到三态结论）；
  ② BACKLOG 71 按色度轴重做判据；③ BACKLOG 72 的迁移（本机 3 卷已答"从没出现"，还欠 runner 卷）。
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
    current = io.open(path, encoding="utf-8").read()
    if marker in current:
        print("跳过（已写过）：%s  ← %s" % (path, marker))
        return
    with io.open(path, "a", encoding="utf-8") as f:
        f.write(text)


def main():
    backlog = io.open("AGENT_BACKLOG.md", encoding="utf-8").read()
    anchor_71 = "    这两条互相牵着，R52 要把它们一起判，不许只调一个数就宣布修好。"
    anchor_76_tail = '    "任一段的 median ≤ 总 median 的 60%"，超了就把那一段的名字打出来。'
    audit_53 = "数字已写进 BACKLOG 71，判据与（可能的）梯子数值改动留给 R52 —— 那会改像素，帧基线要 `update`。"
    state_53 = "这是本轮**第三处**自己错：数从读数来了，但\"哪个读数属于哪个台阶\"没对账（同一族：整窗像素把效果归给错的元素）。"
    batch_row = "| 53.1 | 设置 → 统计，看那张日历热图**最下面几档**：图例里\"最少\"那一格，和它右边\"1 次\"那一格 | 是**两个不同的颜色**，还是**看起来同一格**？ | 我的尺子给出**暗档这两格只差 4/255**（亮档 13；本仓库那条恰可察觉线是 18），但 4 是不是\"人眼看不出来\"只有你判得了 —— 这个数还是本轮在同一张图上错过位之后重测出来的 |"
    report = io.open("AGENT_FINAL_REPORT.md", encoding="utf-8").read()
    pairs = [
        ("| 阶段二 **44 轮**审计（R9–R51） | 跑满（要求 ≥20），每轮有可编译改动 + 七维自评 + 真实看图 "
         "| `AGENT_VISUAL_ITERATION.md` Round 9–51 |",
         "| 阶段二 **45 轮**审计（R9–R52） | 跑满（要求 ≥20），每轮有可编译改动 + 七维自评 + 真实看图 "
         "| `AGENT_VISUAL_ITERATION.md` Round 9–52 |"),
        ("| 决定台账 | D-069 … D-110 | `AGENT_DECISIONS.md` |",
         "| 决定台账 | D-069 … D-111 | `AGENT_DECISIONS.md` |"),
        ("+ **M100–M253**（阶段二 154 支）", "+ **M100–M259**（阶段二 160 支）"),
        ("| 脚本测试 | 72 → 83 → **101** passed",
         "| 脚本测试 | 72 → 83 → 101 → **105** passed（R52 新增 4 格，并把放宽登记那一类动作配了出处要求）"),
        ("| 视觉台账 | U-31 … U-77（47 条；", "| 视觉台账 | U-31 … U-78（48 条；"),
        ("U-77 是**判据红得不对**",
         "U-78 是**登记旧了却长得像判据坏了**：覆盖率地板红在 `notice-banner`，而事实是 R46 那句"
         "\"runner 四次全部判到\"已被两次实测推翻（76ms vs 声明 150ms）⇒ 改登记不改闸门，"
         "并新增一条自测钉住\"以后任何放宽必须留 run 号\"；同轮还撤回 R51 自己刚写的一句"
         "\"暗档只差 4/255\"——那是亮度轴，而那一步差的是色相（B 通道 30）；\\n"
         "U-77 是**判据红得不对**"),
        ("| `AGENT_UI_AUDIT.md` 第 10–53 轮 |", "| `AGENT_UI_AUDIT.md` 第 10–54 轮 |"),
    ]
    changelog = io.open("CHANGELOG.md", encoding="utf-8").read()
    anchor_cl = "## [Unreleased]\n\n### Fixed（R51"
    for old, _ in pairs:
        assert report.count(old) == 1, ("FINAL_REPORT 锚点", report.count(old), old[:80])
    assert changelog.count(anchor_cl) == 1, ("CHANGELOG 锚点", changelog.count(anchor_cl))
    for path, anchor in (("AGENT_BACKLOG.md", anchor_71), ("AGENT_BACKLOG.md", anchor_76_tail),
                         ("AGENT_UI_AUDIT.md", audit_53), ("AGENT_STATE.md", state_53)):
        assert io.open(path, encoding="utf-8").read().count(anchor) == 1, (path, anchor[:60])

    append_once("AGENT_UI_AUDIT.md", "## 第 54 轮 · R52", ROUND.lstrip("\n"))
    append_once("AGENT_DECISIONS.md", "## D-111（R52）", DECISION)
    append_once("AGENT_VISUAL_ITERATION.md", "## Round 52 ·", VISUAL)
    append_once("AGENT_STATE.md", "## R52 · 覆盖率地板第一次在 runner 上红", STATE.lstrip("\n"))
    patch("AGENT_BACKLOG.md", [
        (anchor_71, anchor_71 + "\n" + BACKLOG_71_FIX.strip("\n")),
        (anchor_76_tail, anchor_76_tail + "\n" + BACKLOG_77.strip("\n") + "\n" + BACKLOG_78.strip("\n")),
    ]) if "77. **横幅那一族的动效覆盖" not in backlog else print("跳过 BACKLOG 77/78")
    patch("AGENT_UI_AUDIT.md", [(audit_53, audit_53 + "\n\n> **R52 更正（同一张表，第二次）**："
                                 "上面那句\"0 次与 1 次分不开\"**作废** —— 它用的是亮度轴，"
                                 "而那一步差的是色相（灰→蓝，B 通道 30/255）。详见第 54 轮的视觉审查。")])
    patch("AGENT_STATE.md", [(state_53, state_53 + "\n  **（R52 又补一刀）**那张表的**轴**也用错了："
                             "亮度差 4 的那一步，B 通道差 30 ⇒ \"分不开\"这个结论作废，见第 54 轮。")])
    docs = io.open("docs/MANUAL_TEST_v1.4.9_round3.md", encoding="utf-8").read()
    if "53.1（**R52 更新了这一条的问法**）" not in docs:
        patch("docs/MANUAL_TEST_v1.4.9_round3.md", [(batch_row, BATCH_NOTE.strip("\n"))])
    if "### Fixed（R52" not in changelog:
        patch("CHANGELOG.md", [(anchor_cl, "## [Unreleased]\n\n" + CHANGELOG + "### Fixed（R51")])
    head, curve_old, curve_new = check_curve(45, 52)
    if "U-78 是" not in io.open("AGENT_FINAL_REPORT.md", encoding="utf-8").read():
        patch("AGENT_FINAL_REPORT.md", pairs + [(curve_old, curve_new)])
    else:
        patch("AGENT_FINAL_REPORT.md", [(curve_old, curve_new)])
    print("R52 台账已写入；曲线核对：", head)


main()
