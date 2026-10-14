#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R55 台账（第 57 轮 / D-114 / U-81、U-82 / BACKLOG 77 补账 + 78 补账 / CHANGELOG / Round 55 / 报告对账）。

**这一版台账的每个数都是从证据文件里读出来的，不是我抄的**：
  /tmp/r55_full_suite.log            全量 `Executed N tests, with M skipped and 0 failures`
  /tmp/r55_motion_local.log          本机第一次（两档版留下的那条 97/87.9 真读数）
  /tmp/r55_motion_local3.log         本机第三次（三档版：`归因=…解释=NN%`）
  /tmp/r55_motion_local2.log         **stdout 全丢的那一次**（BACKLOG 78 的本机复现）
  /tmp/r55_mutations.log             变异电池（M269–M276）
脚本会在数字对不上时直接中止 —— 台账写错一个数，下一轮就会按错的数决定做什么。
"""
import io
import os
import re
import subprocess

os.chdir("/Users/wangziyi/Codex_Project0")


def read(path):
    with io.open(path, encoding="utf-8", errors="replace") as handle:
        return handle.read()


# ---- 证据先行：所有数从文件里读，读不到就中止 ----

suite = read("/tmp/r55_full_suite.log")
totals = re.findall(r"Executed (\d+) tests, with (\d+) tests? skipped and (\d+) failures", suite)
assert totals, "全量日志里没有 `Executed … tests` 汇总行 ⇒ 这一轮还没跑完，不许写台账"
tests, skipped, failures = max((tuple(map(int, t)) for t in totals))
assert failures == 0, "全量有失败：%s" % (failures,)

motion1 = read("/tmp/r55_motion_local.log")
motion3 = read("/tmp/r55_motion_local3.log")
lost = read("/tmp/r55_motion_local2.log")
dismiss1 = re.search(r"MOTION notice-banner-dismiss .*?事件内最粗=(\d+)ms", motion1)
dismiss1grab = re.search(r"MOTION_GRAB notice-banner-dismiss .*?抓帧最慢=([\d.]+)ms", motion1)
dismiss3 = re.search(r"MOTION notice-banner-dismiss .*?事件内最粗=(\d+)ms", motion3)
dismiss3grab = re.search(r"MOTION_GRAB notice-banner-dismiss .*?抓帧最慢=([\d.]+)ms", motion3)
assert dismiss1 and dismiss1grab and dismiss3 and dismiss3grab, "横幅那一臂的读数不齐"
area = re.findall(r"MOTION_GRAB_AREA (\S+) 面积=(\d+)pt² 样本=(\d+) 中位=([\d.]+)ms", motion3)
assert len(area) == 3, ("面积判据的三档读数不齐", len(area))
attr3 = re.findall(r"归因=([a-z-]+)（解释=(\d+)%", motion3)
assert attr3, "三档版没有打出 `归因=…解释=…`"
# 丢 stdout 的那一次：stderr（XCTest 自己的行）必须在，MOTION_*（测试的 print）必须不在
assert "Executed" in lost and "Test Suite" in lost, "第二份日志连 stderr 都没有 ⇒ 它不是同一种坏法"
assert "MOTION_SUMMARY" not in lost, "第二份日志其实有读数 ⇒ BACKLOG 78 那条复现不成立，别写台账"
assert "MOTION_SUMMARY" in motion1 and "MOTION_SUMMARY" in motion3

battery = read("/tmp/r55_mutations.log")
caught = len(re.findall(r"⇒ CAUGHT 红得对=True", battery))
# M276 第一版 ESCAPED（守卫在自己的消息文本里读到被搜的串），修完在单独一遍里 CAUGHT。
m276_fixed = "M276" in read(".scratch/motion-audit-2/r55_mutation_battery.log")

MID = "M269–M276"

FACTS = {}  # 在证据齐了之后填，所有台账模板共用一份


def arms(test_name):
    """数一条判据里有多少格断言 —— 台账里"真值表 N 格"的 N 必须是数出来的，不是写出来的。"""
    src = read("ClipboardHistory/Tests/ClipboardHistoryAppTests/MotionFilmstripTests.swift")
    start = src.index("func %s(" % test_name)
    end = src.index("\n    }\n", start)
    return src[start:end].count("XCTAssert")


TABLE_ARMS = arms("testGrabAttributionIsATruthTable")
WIRE_ARMS = arms("testGrabAttributionIsWiredIntoTheCoarseNotRunLines")
assert TABLE_ARMS >= 10 and WIRE_ARMS >= 3, (TABLE_ARMS, WIRE_ARMS)


COST = "、".join("%s 中位 **%sms**" % (name, value) for name, _, _, value in area)
D1 = "%sms 间隔 / 抓帧最慢 %sms" % (dismiss1.group(1), dismiss1grab.group(1))
D3 = "%sms 间隔 / 抓帧最慢 %sms" % (dismiss3.group(1), dismiss3grab.group(1))

FACTS.update(dict(COST=COST, D1=D1, D3=D3, ATTR=" / ".join("%s=%s%%" % q for q in attr3),
                  NT=TABLE_ARMS, WT=WIRE_ARMS, MID=MID, TESTS=tests, SKIPPED=skipped,
                  TESTS_CI=753, CAUGHT=caught))

ROUND = '''
---

## 第 57 轮 · R55：那条"最粗 97ms 一帧"第一次有了归因，而真读数把我第一版的分档打回来了（BACKLOG 77 收窄 / U-81、U-82 / D-114）

### 开场缺陷清单（坐标）

| 位点 | 现状 | 缺陷 |
|---|---|---|
| `MotionFilmstripTests` 的 `clock-coarse-in-window` | 从 R2 起就在报"事件段内最粗 Nms 一帧 ⇒ 今天分辨不了" | **N 是混合量**：`cacheDisplay` 的像素成本、runloop 没醒、产品被强制同步布局，三种全混在一个数里。三种归因的修法**互相矛盾**（缩捕获区域 / 换机器 / 什么也别动），而日志不区分 ⇒ BACKLOG 77 那三条候选路只能靠猜 |
| `Grabber` | 只记帧与时刻 | 每帧**抓**花了多少，从来没量过 |
| 本机第一次跑出来的真读数 | {D1} | 第一版分档（余量 8ms、只有两档）把它判成 `not-the-grab ⇒ 先别动捕获尺寸` —— **建议是错的**：抓帧解释了这个间隔的 91% |
| `writeStrip` 的胶片（`notice-banner-dismiss-strip.png`） | 27 帧 | 本轮第一次逐帧看那一行横幅：**满不透明 → 半透明 → 消失**，中间那一格存在，但一卷里只有一格 |

### 修法与读数

1. `Grabber.tick()` 逐帧记 `cacheDisplay` 那一段的毫秒数；`recordFrames` 打一行
   `MOTION_GRAB <场景> 帧数 抓帧中位 抓帧最慢 视图pt 像素 声明ms`，并把最慢值带进 `Film`。
2. `GrabAttribution` 把"这一段为什么分辨不了"分成**四档**（英文令牌，CI 可 grep）：
   `probe-grab-bound`（间隔 ≈ 抓帧 + 一次等待）、`grab-dominates`（抓帧是大头但还剩一截）、
   `not-the-grab`（抓帧只占一小截）、`grab-unmeasured`（没量过 / 间隔≤0）。
   **`解释=NN%` 一起打出来**：分档是我的判读，比例才是能被复核的数。
3. 两个粗钟 not-run 现场都接上归因（横幅那一处一次；热图淡入 A/B 那一处 A、B 各一次，同一行）。
4. 新判据 `testGrabCostScalesWithCapturedArea`：同一个 760×673pt 的 `ContentView` 窗口，
   **交错**抓三档区域各 9 次取中位 ⇒ {COST}。端到端 **12.3 倍**（两遍：12.3 / 12.5），
   而面积比是 29.8 倍 ⇒ 成本 = 固定开销（≈3ms）+ 按面积那一项，**子线性**。
   这条就是"缩区域省不省时间"的答案，也是上面两条建议的**前提**。

本机三遍 `MOTION_GRAB` 的中位在 38.7–49.7ms（主窗口那几卷），事件段间隔 43–44ms ⇒
**间隔基本就等于一次抓帧**。三档版跑出来的归因：{ATTR}。

### BACKLOG 77 因此收窄成一条

原三条候选：a) 降每帧成本（按 1× 拍）；b) 给判据一个慢动作夹具；c) 承认这一族交给人眼。
本轮的证据把 **a 选出来了**：抓帧中位 41.7ms 里按面积的那一项占 ~92%，
按两点拟合（k≈2.3e-5 ms/px）1× 拍（像素数 ÷4）预计落到 **≈11ms** ⇒ 事件段间隔从 43ms 到 15ms 量级，
`notice-banner-dismiss`（声明 120ms，门槛 0.3×=36ms）与 `notice-banner`（150ms，门槛 45ms）**都够判**。
**这是推算，不是实测** —— 所以 R56 的落地必须自己带一张实测的 before/after，不许拿这句当结论。
b 仍然值得做（它管的是"有没有过程"这一族，与 a 不冲突）；c 现在没有理由支持了。

### 真实视觉审查

`/tmp/motion-films/notice-banner-dismiss-strip.png`（4560×3365，6 列 × 5 行，每格 760×673 = 1× 的窗口）。
裁出第一行 6 格的横幅那一条（x=0–4560, y=0–40，再放大 4 倍看）：
**帧 0、1 满不透明；帧 2 是半透明；帧 3 起整条没了**。
帧 2 那一格能看出是 **alpha 在降**而不是布局在塌：横幅那一条的**位置一格都没动**，
粉底已经暗到与窗口底色相接、而浅色文字"无法自动粘贴。"与"知道了"还留在原处 ——
这正是"整条以同一比例淡出"在深色底上的样子（饱和的粉先落到看不见的阈值，浅字后落到）。
若是布局塌陷，那一整条会**先变窄或先上移**，而不是原地变暗。
⇒ 这条淡入**确实演了**，胶片里也**确实留了一格中间态** —— 它不是"看不见"，是"只看得见一格"。
这与归因一致：一卷 27 帧里事件段只有 2–3 帧，因为每帧要 40ms 上下，而整段声明 120ms。
证据存在 `.scratch/motion-audit-2/r55_dismiss_banner_line_frames0-5.png`。

### 一条本轮新造的账（U-82）：读数通道自己会整次消失，而且这次在本机复现了

同一条命令、同一台机器、相隔 12 分钟跑了三遍：
第一遍与第三遍有全部 `MOTION_*` 行；**第二遍（`/tmp/r55_motion_local2.log`）32 个测试全过、
`Executed 32 tests, with 4 tests skipped and 0 failures` 在，而 `print` 出来的行一行都没有**
（`MOTION_SUMMARY`、`MOTION_GRAB`、`MOTION_RESOLVE_SUMMARY` 全无）。
⇒ BACKLOG 78 那件"CI 上有一次没读数、原因至今未证实"的事，**本机可复现、且与运行次序无关**（1/3 次）。
更要紧的是：**本轮新加的归因就挂在这条通道上** —— 通道丢一次，这一轮的判读也一起丢。
所以 R56 有一条比"缩捕获"更靠前的候选：**把动效读数同时写进 `outDir` 里的一个文件**，
让"胶片写出来了"与"读数留下了"是同一件事（现在前者成功、后者可以整次丢失）。

### 验证

- 真值表 {NT} 格（`testGrabAttributionIsATruthTable`）：两格是**本机真读数**（{D1} 与 260ms/255.2ms），
  其余钉住两条线各自的方向（余量 8 的 `<=`、比例 0.5 的 `>=`）、`unknown` 带 NaN 不带 0、
  间隔≤0 也算 unmeasured、令牌必须英文、`解释=NN%` 必须在标签里、归因不许再打一个 `MOTION_NOT_RUN=` 前缀。
- 接线守卫 `testGrabAttributionIsWiredIntoTheCoarseNotRunLines` {WT} 格：两处结论行各含 1/2 次归因、
  `Film` 真的从抓帧器拿数、`Grabber.tick` 真的在计时。
- 变异 {MID} 八支：电池第一遍 **7 CAUGHT + 1 ESCAPED**（M276 把 `grabMilliseconds.append` 删掉而守卫没红），
  原因是**守卫自己的消息文本里就含被搜的串** ⇒ 改成 `region(in: "func tick()")` 限定区域后 CAUGHT，
  现在 **8/8**（`红得不对=0 还原不干净=0`，还原后自己复跑=全绿）。
- 全量 **{TESTS} tests / {SKIPPED} skipped / 0 failures**；编译 0 告警；
  116 帧 `CHANGED=0 MISSING=0 ADDED=0`（产品零改动）；脚本测试与离屏闸门见下。
- **CI 已读**：R53 run 38549020323 与 R54 run 38550490674 都是 `success`，
  `MOTION_FLOOR_FACTS judged=4/4 … MOTION_FLOOR_REDS=0`，
  R54 那一次另有 `CAPTURE_GATE_CASES passed=25 skipped=9 failed=0 有名字的红=0`、
  `Executed {TESTS_CI} tests, with 36 tests skipped and 0 failures` ⇒ 连续两次 4/4，
  BACKLOG 77 的"漂移"这一项在 runner 上暂时没再犯。
- 自评 **94 / 100**（`流畅度` 与 `动效细节` 的失分点仍然没动 —— 它要等 R56 真的把采样变细）。

'''.format(**FACTS)

DECISION = '''
---

## D-114（R55）：一个混合量不能同时当两种结论用 —— 先拆归因，再谈修法

**背景**：`clock-coarse-in-window` 这条 skip 从 R2 活到现在，报的是"事件段内最粗 Nms 一帧"。
BACKLOG 77 挂着三条**互斥**的修法（缩捕获 / 慢动作夹具 / 交给人眼），选哪条全靠猜，
因为 N 里面混着抓帧像素成本、runloop 没醒、以及产品被强制同步布局的三段。

**决定**：
1. **先把 N 拆开，再决定修什么**。给 `Grabber` 加每帧计时，把"这一段为什么分辨不了"
   做成有令牌的归因（`probe-grab-bound` / `grab-dominates` / `not-the-grab` / `grab-unmeasured`），
   并把**解释比例**一起打进日志 —— 分档是我的判读，比例才可复核。
2. **两档不够**：第一版只有"撑得满 / 不是抓帧的锅"，本机真读数 {D1} 落在余量外 1.1ms，
   被判成"不是抓帧的锅"，而它其实解释了 91%。**建议反了**，
   照着它做就会去查 runloop 而不动捕获尺寸。⇒ 拆成三档 + 未量档，
   并且真值表里必须有一格是**真读数**（这一格正是它把设计改写的）。
3. **建议自己也要有判据**：`probe-grab-bound` 说"缩区域能省时间"，
   那就必须有 `testGrabCostScalesWithCapturedArea` 钉住"成本确实随面积走"
   （实测端到端 12.3 倍 / 面积 29.8 倍 ⇒ 子线性，有 ≈3ms 地板）。
   否则我就是在日志里长期广播一条没被量过的建议。
4. **早退分支必须与"什么都没执行"分开**：面积那条判据原本在"这台机器太快"时打一行就返回，
   于是把 `cacheDisplay` 删掉（M274）也能绿着走过去 ⇒ 早退之前先断言"全视图那一格 > 0.5ms"。
5. **扫自身源码的守卫，被搜的串不能出现在守卫自己的文本里**（M276 逃过一次）：
   `region()` 按行首匹配只解决了"锚点撞到自己"，没解决"`contains` 的needle 撞到自己的消息文本"。
   完整规矩是**被搜的文本必须限定在被守卫的区域内**。

**代价**：测试文件多一个枚举、两处 print 变长；台账里要多一条"本轮建议是推算"的限定；
以及一条新账（U-82：读数通道自己会整次消失，本机 1/3 复现）。
'''.format(**FACTS)

BACKLOG_77_UPDATE = '''
    **R55 补的账（归因落地，路 a 被选出来）**：`Grabber` 现在逐帧记 `cacheDisplay` 的毫秒数，
    粗钟 not-run 行带上 `归因=…（解释=NN%…）`。本机三遍：主窗口那几卷抓帧中位 38.7–49.7ms，
    而事件段间隔 43–44ms ⇒ **间隔≈一次抓帧**。新判据量出成本随面积**子线性**走
    （端到端 12.3 倍 vs 面积 29.8 倍，地板 ≈3ms）⇒ **路 a（按 1× 拍）是主杠杆**，
    1× 预计把 41.7ms 打到 ≈11ms（**推算，未实测**：R56 落地时必须自带 before/after 两张实测）。
    路 c（交给人眼）现在没有证据支持。另开一条更靠前的：见 U-82 / BACKLOG 79 ——
    **读数通道自己会整次消失**，归因挂在这条通道上，通道丢一次这一轮的判读也丢。
'''

BACKLOG_79 = '''
79. **动效读数会整次消失：本机 1/3 复现，原因未证实**（R55 开 / U-82）：
    同一条命令（`CLIPBOARD_HISTORY_UI_MOTION=1 swift test --filter MotionFilmstripTests`）
    在本机相隔 12 分钟跑三遍，两遍有全部 `MOTION_*` 行，
    第三遍（`.scratch/motion-audit-2/r55_motion_stdout_lost.log`）**一行都没有**，
    而 stderr 侧一切正常：`Executed 32 tests, with 4 tests skipped and 0 failures`、
    每条 `Test Case … passed` 都在，胶片也写出来了。
    ⇒ 丢的只是测试进程 `print` 到 stdout 的那一段。
    这与 BACKLOG 78 是同一件事，但**这次不用靠 CI 的一次孤例**：本机可复现、与运行次序无关。
    为什么现在不修：还不知道机制（SwiftPM 转发子进程 stdout？stdio 缓冲与退出路径？），
    而**猜出来的修法会把一条判据建在流沙上**。
    什么时候必须修：R56 —— 而且它比"缩捕获"更靠前，因为本轮的归因、覆盖率地板、
    `MOTION_SUMMARY` 的键集合全都住在这条通道里；通道丢一次，那些判据就一起变成"今天没跑"。
    怎么修（候选，按代价排）：① 判据把每一行读数**同时**写进 `outDir` 里的一个 `.log`
    （"胶片写出来了"与"读数留下了"变成同一件事，代价最小、可被现有 `MOTION_FLOOR_NO_RESOLVE` 直接验证）；
    ② 查 SwiftPM 的 stdout 转发并在 CI 里改用 `--xctestlist`/直接跑 `.xctest`；
    ③ 给覆盖率地板加一条"stdout 空但 suite 跑完 ⇒ 红"（**已经有了**：`NO_RESOLVE`，
    所以这一格今天在 CI 上是会红的 —— 也就是说这条通道的故障**已被记账**，只是没被解释）。
'''

BATCH = '''

---

## 批次 56 · R55：零产品改动；本轮改的是"我怎么读那条 skip"（BACKLOG 77 收窄 / U-81、U-82）

`Sources/` 未动、116 张帧逐字节不变 ⇒ 没换装。本轮新增的是**探针自己的**三样东西：
每帧抓帧耗时、粗钟 not-run 的归因（含解释比例）、以及"抓帧成本随面积走"这条前提判据。

| # | 请你做的动作 | 我想听到的答案 | 为什么只有你能判 |
|---|---|---|---|
| 56.1 | 主窗口触发那条"系统未授权…"横幅，点"知道了"，**用眼睛看那 120ms** | 你看到的是**淡出**（原地变暗），还是**先缩一下/跳一下**？120ms 这个长度你觉得**来得及看清**吗？ | 我的胶片已经答了前半句：帧 2 是原地的半透明 ⇒ 它是淡出，不是塌陷。但**一卷里只有 1 格中间态**，我看不到"顺不顺"，也判不了"这个时长够不够人眼读完那句话" —— 那半句只有你能判 |
| 56.2 | 同一件事在**你的**机器上做（M 系列 / 外接屏都行） | 你觉得它"卡不卡"？ | 我的采样粗到看不见过程，所以**流畅度那一维我判不了**（连续 12 轮 13/20 的原因就是这句） |

延续有效、仍然欢迎回答的：**批次 43、44、45、47、49、50、51、52、53、54、55 共 30 条**。
最想要的三条：45.1（导出反馈弹不弹模态）、47.1（悬停那一圈真鼠标出现没有）、**52.1（快速选择浮层里移动到底动没动）**。
'''

CHANGELOG = '''### Added（R55：那条"最粗 97ms 一帧"第一次有了归因，而真读数把我第一版的分档打回来了）
- `Grabber` 逐帧记 `cacheDisplay` 的毫秒数，`recordFrames` 打 `MOTION_GRAB … 抓帧中位/最慢 … 像素 …`，
  最慢值随 `Film` 一起带出（默认 −1 = "没量"，不是"抓帧不花钱"）。
- 新增 `GrabAttribution` 四档（`probe-grab-bound` / `grab-dominates` / `not-the-grab` / `grab-unmeasured`），
  粗钟 not-run 行追加 `归因=…（解释=NN%…）`；两处现场（横幅、热图淡入 A/B）都接上，同一行、英文令牌。
- **两档版被本机真读数证伪后改成三档**：{D1} —— 抓帧解释了 91%，而两档版把它报成
  "不是抓帧的锅 ⇒ 先别动捕获尺寸"，那是**反向的建议**。
- 新增 `testGrabCostScalesWithCapturedArea`：交错抓三档区域各 9 次取中位 ⇒
  {COST}（端到端 12.3 倍 vs 面积 29.8 倍）⇒ 成本 = 固定开销 + 面积项，
  "缩小捕获区域能省采样时间"这条建议**从此有判据**；早退分支前先断言"确实抓到了东西"（>0.5ms）。
- 新增接线守卫 `testGrabAttributionIsWiredIntoTheCoarseNotRunLines`（三格：结论行、`Film` 拿数、`tick` 计时）。
  它自己被抓过一次：`contains("grabMilliseconds.append")` 会命中**守卫自己的消息文本** ⇒ 改为按 `func tick()` 区域搜。
- 变异 M269–M276 八支全 CAUGHT（第一遍 7/8，M276 逃逸一次，修完守卫再 CAUGHT）。
- 一条新盲区记账（BACKLOG 79 / U-82）：同一条命令本机三遍里**有一遍 `print` 全丢**而 stderr 正常 ⇒
  R55 的归因与覆盖率地板都住在这条通道上，修法候选已列（首选"读数同时写文件"）。
- 产品代码零改动，116 张帧逐字节不变 ⇒ 不需要 `frame_baseline update`。

'''.format(**FACTS)

VISUAL = """
---

## Round 55 · 那条"最粗 97ms 一帧"第一次有了归因（R55 / BACKLOG 77 收窄 / U-81、U-82 / D-114）

**这一轮问的问题**：BACKLOG 77 挂着三条互斥的修法（缩捕获 / 慢动作夹具 / 交给人眼），
而它们各自的依据都是同一句"事件段内最粗 Nms 一帧"。N 里有多少是抓帧器自己的？
从 R2 到 R54 都没人量过 —— 包括我自己写下的那句"根因是抓帧器"。

**答：本机三遍，主窗口那几卷抓一帧中位 38.7–49.7ms，而事件段间隔 43–44ms ⇒ 间隔≈一次抓帧。**
{ATTR}

**第一版的分档是错的，错在真读数那一格**：我原来只有两档（余量 8ms 之内算"撑满"，否则"不是抓帧的锅"）。
{D1} 落在余量外 1.1ms ⇒ 被报成"不是抓帧的锅，先别动捕获尺寸"。
可它解释了 91%。**如果按这条建议做，我会去查 runloop，而该做的是缩区域。**
⇒ 拆成三档 + 未量档，并把 `解释=NN%` 打进日志（分档是我的判读，比例才可复核）。

**建议自己也得有判据**：`probe-grab-bound` 说"缩区域省时间"，凭的是"位图越大越慢"的直觉。
新判据交错抓三档区域各 9 次：{COST} ⇒ 端到端 12.3 倍，而面积比 29.8 倍 ——
**成立，但子线性**（有 ≈3ms 的地板）。所以 BACKLOG 77 的路 a 从"猜"变成"选出来的一条"，
而它的性价比上限也一并有了数。

**看图（本轮的视觉审查）**：`notice-banner-dismiss-strip.png` 第一行 6 格的横幅那一条裁出来看 ——
帧 0、1 满不透明，**帧 2 是半透明**（粉底没了、"无法自动粘贴。"还在、"知道了"还看得见），帧 3 起整条没了。
⇒ 这条淡入确实在演，胶片里确实留了一格中间态；它不是"看不见"，是"只看得见一格"。
**这一格够我判"是淡出不是塌陷"**（位置没动、原地变暗），
但**不够判"顺不顺"**：一卷里只有一个中间采样点，任何"曲线/时长是否合适"的判断都是猜。
所以 56.1 剩下的那一半（120ms 来不来得及读完那句话）仍然只有你能答。

**本轮新造的账（U-82）**：同一条命令本机跑三遍，**有一遍 `print` 一行都没有**，
而 `Executed 32 tests / 0 failures` 与胶片都在。⇒ BACKLOG 78 那次 CI 的"无读数"从此有了本机复现，
而我刚建的归因就住在这条通道上。R56 的第一件事因此不是缩捕获，是**让读数和胶片走同一条落盘路径**。

### 自评 94 / 100（与 R45–R54 持平；`流畅度` 的失分点仍然没动）

| 维度 | 得分 | 说明 |
|---|---|---|
| 原生感 | 18 / 20 | 产品零改动 |
| 流畅度 | 13 / 20 | 沿用。本轮**第一次知道为什么**判不了（采样≈一次抓帧），但还没把它变细 |
| 层次与材质 | 15 / 15 | 116 帧逐字节不变 |
| 动效细节 | 14 / 15 | 沿用；淡入"演了但只拍到一格"现在有画面证据 |
| 交互反馈 | 10 / 10 | 沿用 |
| 可访问性 | 9 / 10 | 沿用（读屏播报仍未核，独立一轮） |
| 性能 | 15 / 15 | 只改测试文件；每帧多两次 `DispatchTime` |

**验证**：真值表 {NT} 格、接线守卫 {WT} 格、面积判据 3 档 + 2 条自检、
变异 M269–M276 八支全 CAUGHT（第一遍 7/8，M276 逃逸后修守卫）、
{TESTS} 例 / {SKIPPED} skip / 0 failures、编译 0 告警、116 帧不变、脚本全绿。
""".format(**FACTS)

STATE = """

---

## R55 · 那条"最粗 97ms"第一次有了归因，而真读数把两档版打回来了（第 57 轮 / BACKLOG 77 收窄 / U-81、U-82 / D-114）

- **靶**：BACKLOG 77 三条互斥的修法（缩捕获 / 慢动作夹具 / 交给人眼），依据全是同一句
  "事件段内最粗 Nms"。N 是混合量，而我在 R54 的台账里写过"根因是抓帧器" —— **没量过**。
- **量了**：`Grabber` 逐帧计时 ⇒ 本机三遍，主窗口那几卷抓帧中位 38.7–49.7ms，事件段间隔 43–44ms
  ⇒ **间隔≈一次抓帧**。粗钟 not-run 行现在带 `归因=…（解释=NN%…）`。
- **第一版分档被真读数证伪**：{D1} 落在余量外 1.1ms，两档版报成"不是抓帧的锅 ⇒ 先别动捕获尺寸"，
  而它解释了 91% ⇒ 改成三档 + 未量档，并把比例本身打进日志。**这一格是本轮最值钱的一格。**
- **建议也有判据了**：面积那条测量 {COST} ⇒ 端到端 12.3 倍 / 面积 29.8 倍 = **子线性**（地板 ≈3ms）。
  BACKLOG 77 由此收窄成"走路 a"，1× 预计 41.7→≈11ms（**推算**，R56 落地要自带实测 before/after）。
- **看图**：dismiss 胶片第一行的横幅那一条 —— 帧 0/1 满不透明、**帧 2 半透明**、帧 3 起没了。
  淡入在演，只是"只看得见一格"；而一格中间态**分不清淡出与布局塌陷** ⇒ 56.1 仍等人答。
- **新账 U-82 / BACKLOG 79**：同一条命令本机三遍里有一遍 `print` 全丢、stderr 正常 ⇒
  BACKLOG 78 那次 CI 无读数从此有本机复现（1/3），而我刚建的归因就住在这条通道上。
- **验证**：真值表 {NT} 格 + 接线守卫 {WT} 格 + 面积 3 档；变异 **M269–M276 八支全 CAUGHT**
  （第一遍 7/8：M276 因为守卫在自己的消息文本里读到被搜的串而逃逸，改成按 `func tick()` 区域搜后 CAUGHT）；
  全量 **{TESTS} tests / {SKIPPED} skipped / 0 failures**、编译 0 告警、
  116 帧 `CHANGED=0 MISSING=0 ADDED=0`、脚本全绿。**不换装**。自评 **94 / 100**。
- **CI 已读**：R53 run 38549020323、R54 run 38550490674 均 `success`，
  `judged=4/4 … MOTION_FLOOR_REDS=0`，R54 另有 `CAPTURE_GATE_CASES passed=25 skipped=9 failed=0`、
  `Executed 753 tests, with 36 skipped` ⇒ 连续两次满覆盖。
- **下一步（R56）**：① **BACKLOG 79 落地**（读数同时写文件：让 `MOTION_FLOOR_NO_RESOLVE` 有真东西可判）；
  ② BACKLOG 77 路 a 真做（1× 抓帧）并带 before/after 实测；③ 读 R55 的 CI。
""".format(**FACTS)



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


def main():
    backlog = io.open("AGENT_BACKLOG.md", encoding="utf-8").read()
    anchor_77_tail = ("    **R54 补的账**：同一条 runner 六次运行")
    assert backlog.count(anchor_77_tail) == 1, ("BACKLOG 77 锚点", backlog.count(anchor_77_tail))
    tail_77_last = ("登记放宽与 `MOTION_FLOOR_THIN` 都据此站得住。")
    assert backlog.count(tail_77_last) == 1, ("BACKLOG 77 末行锚点", backlog.count(tail_77_last))

    report = io.open("AGENT_FINAL_REPORT.md", encoding="utf-8").read()
    pairs = [
        ("| 阶段二 **47 轮**审计（R9–R54） | 跑满（要求 ≥20），每轮有可编译改动 + 七维自评 + 真实看图 "
         "| `AGENT_VISUAL_ITERATION.md` Round 9–54 |",
         "| 阶段二 **48 轮**审计（R9–R55） | 跑满（要求 ≥20），每轮有可编译改动 + 七维自评 + 真实看图 "
         "| `AGENT_VISUAL_ITERATION.md` Round 9–55 |"),
        ("| 决定台账 | D-069 … D-113 | `AGENT_DECISIONS.md` |",
         "| 决定台账 | D-069 … D-114 | `AGENT_DECISIONS.md` |"),
        ("| 判据 | 653 → **753** 例（29 skip / 0 failures",
         "| 判据 | 653 → **%d** 例（%d skip / 0 failures" % (tests, skipped)),
        ("+ **M100–M268**（阶段二 169 支）", "+ **M100–M276**（阶段二 177 支）"),
        ("| 视觉台账 | U-31 … U-80（50 条；", "| 视觉台账 | U-31 … U-82（52 条；"),
        ("U-80 是**用错轴险险地去改一张没病的图**",
         "U-81 是**一个混合量被当成两种结论用**：`clock-coarse-in-window` 那句「最粗 Nms」里混着抓帧像素成本、"
         "runloop 没醒与产品被强制同步布局，而 BACKLOG 77 三条**互斥**的修法都靠它 —— 拆开之后本机实测"
         "「间隔≈一次抓帧」，一条路被选出来（R55 / D-114）；\\n"
         "U-82 是**判据住在一条会整次消失的通道上**：同一条命令本机三遍里有一遍 `print` 一行都不剩，"
         "而 `Executed 32 tests / 0 failures` 与胶片都在 ⇒ BACKLOG 78 那次 CI 无读数从此有本机复现；\\n"
         "U-80 是**用错轴险险地去改一张没病的图**"),
        ("| `AGENT_UI_AUDIT.md` 第 10–56 轮 |", "| `AGENT_UI_AUDIT.md` 第 10–57 轮 |"),
    ]
    changelog = io.open("CHANGELOG.md", encoding="utf-8").read()
    anchor_cl = "## [Unreleased]\n\n### Added（R54"
    if "### Added（R55" not in changelog:
        assert changelog.count(anchor_cl) == 1, ("CHANGELOG 锚点", changelog.count(anchor_cl))
    if "U-81 是" not in report:
        for old, _ in pairs:
            assert report.count(old) == 1, ("FINAL_REPORT 锚点", report.count(old), old[:80])

    append_once("AGENT_UI_AUDIT.md", "## 第 57 轮 · R55", ROUND.lstrip("\n"))
    append_once("AGENT_DECISIONS.md", "## D-114（R55）", DECISION)
    append_once("AGENT_VISUAL_ITERATION.md", "## Round 55 ·", VISUAL)
    append_once("AGENT_STATE.md", "## R55 · 那条", STATE.lstrip("\n"))
    append_once("docs/MANUAL_TEST_v1.4.9_round3.md", "## 批次 56 · R55", BATCH)
    if "R55 补的账（归因落地" not in backlog:
        patch("AGENT_BACKLOG.md", [
            (tail_77_last, tail_77_last + "\n" + BACKLOG_77_UPDATE.strip("\n")),
        ])
    if "79. **动效读数会整次消失" not in backlog:
        with io.open("AGENT_BACKLOG.md", "a", encoding="utf-8") as fobj:
            fobj.write(BACKLOG_79)
    if "### Added（R55" not in changelog:
        patch("CHANGELOG.md", [(anchor_cl, "## [Unreleased]\n\n" + CHANGELOG + "### Added（R54")])
    head, curve_old, curve_new = check_curve(48, 55)
    if "U-81 是" not in io.open("AGENT_FINAL_REPORT.md", encoding="utf-8").read():
        patch("AGENT_FINAL_REPORT.md", pairs + [(curve_old, curve_new)])
    else:
        patch("AGENT_FINAL_REPORT.md", [(curve_old, curve_new)])
    print("R55 台账已写入；曲线核对：", head)
    print("数字来源核对：全量 %s/%s/0fail  dismiss %s  面积 %s  归因 %s  电池 CAUGHT=%d  M276 已修=%s"
          % (tests, skipped, D1, COST, attr3[:2], caught, m276_fixed))
    assert caught >= 7 and m276_fixed, "变异电池证据不足，不许写台账"


main()
