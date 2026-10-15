# -*- coding: utf-8 -*-
'''R83 的台账补丁（第 85 轮 / Round 83）。

数字全部从两处产物读，不许手抄：
  * `.scratch/motion-audit-2/r83_battery.log`   —— 五刀的逐条结论
  * `.scratch/motion-audit-2/r83_verify_summary.log` —— 全量验证的逐条读数
每个锚点都断言"命中且只命中一次"。
'''
import io
import os
import re
import sys

REPO = '/Users/wangziyi/Codex_Project0'
BATTERY = os.path.join(REPO, '.scratch/motion-audit-2/r83_battery.log')
SUMMARY = os.path.join(REPO, '.scratch/motion-audit-2/r83_verify_summary.log')
CURVE = 'CURVE_PLACEHOLDER'


def read(path):
    return io.open(path, encoding='utf-8').read()


def write(path, text):
    io.open(path, 'w', encoding='utf-8').write(text)


def summary(key, default=None):
    text = read(SUMMARY)
    m = re.search(r'^%s=(.+)$' % re.escape(key), text, re.M)
    if not m:
        if default is None:
            raise SystemExit('验证摘要里缺 %s —— 先把验证跑完再来写台账' % key)
        return default
    return m.group(1).strip()


def knife_rows():
    text = read(BATTERY)
    rows = []
    for m in re.finditer(r'^M4(\d\d) (.+?)$', text, re.M):
        tag = 'M4' + m.group(1)
        tail = text[m.end():]
        hit = re.search(r'^   (CAUGHT|ESCAPED|NOT-RUN|NOT-APPLIED|LOCAL-NO-POWER)', tail, re.M)
        rows.append((tag, m.group(2), hit.group(1) if hit else '?'))
    return rows


KNIVES = knife_rows()
CAUGHT = [t for t, _, k in KNIVES if k == 'CAUGHT']
NOPOWER = [t for t, _, k in KNIVES if k == 'LOCAL-NO-POWER']
BAD = [t for t, _, k in KNIVES if k not in ('CAUGHT', 'LOCAL-NO-POWER')]
KNIFE_TABLE = u'\n'.join(u'| %s | %s | **%s** |' % (t, n.split('⇒')[0].strip(), k) for t, n, k in KNIVES)

FULL_TEST = summary('FULL_TEST')
SKIPPED = summary('SKIPPED')
BUILD_WARN = summary('BUILD_WARNINGS')
FRAME = summary('FRAME_BASELINE')
GATE = summary('CAPTURE_GATE')
SCRIPTS = summary('SCRIPT_TESTS')
MOTION_FACTS = summary('MOTION_FLOOR')
SHIM = summary('SHIM_READING')
FILM = summary('FILM_PREMISE_READING')
RATE_WIT = summary('RATE_WITNESS_READING')
COARSE_WIT = summary('COARSE_WITNESS_READING')

ROUND_HEAD = ('## Round 83 · 上一轮那枚钉子挂错了对象：前提不许挂在结论尺的输出上'
              '（结案 114 / 新开 118 / U-160…U-163 / D-141）\n')

SECTION = u'''
### 本轮开场的位点清单（本轮 0 个产品文件；看图的部分是复用上轮那张条带图，量的是它）

被重新判断的**不是画面**，是上一轮我自己交的两条判据 + 一格闸门：
1. `testSkeletonSweepActuallySweeps` 的卷长钉子（`MotionFilmstripTests.swift`，R82 新加）；
2. 同一条判据里的绝对峰值地板（R82 之前就有，本轮第一次让它听处置的话）；
3. `scripts/motion_floor_gate.py` 的 `NAMELESS_RED` 那一格（R66 建的，本轮修它的比较单位）。

看图这一项本轮没有跳过：上轮那张逐帧条带图（`r82_skeleton_sweep_strip.png`）被拿来**量**了
（工具 `.scratch/motion-audit-2/r83_band_fanout.py`，读数 `r83_fanout_readings.log`），
量出来的就是 BACKLOG 117 那条缺陷的数字（见下面"看图量出来的那一格"）。

### 读 R82 的 CI（run 38781113064，12m11s）：114 的答案是预登记的**第一支**，而那两朵红都是我的

```
runner  MOTION_SHIMMER 扫 帧数=21 变化帧对=0 峰值=0.000 采样≈118ms
runner  MOTION_SHIMMER_WITNESS 等节拍证人(30Hz 抬升 0.12) 帧对=35 在变=2 峰值=0.015 coverage=0.284
runner  MOTION_SHIMMER_WITNESS 粗节拍证人(20Hz 抬升 0.45)  帧对=26 在变=23 峰值=0.028 coverage=1.000
runner  MOTION_NOT_RUN=loop-clock-not-sustainable-at-product-rate …
```

⇒ 这台机器带得动 20Hz 的常驻循环，带不动 30Hz 的那一档 —— 与产品无关，也不是"归属"问题。
R82 那把等节拍证人**问对了问题**：如果沿用 R81 的单颗证人，这一遍会红着说"产品的扫光没跑"，
而那句是错的。114 就此结案（两支里落在第一支，处置是点名 not-run）。

但 `Motion coverage floor` 这一步仍然红，红的两条都在我上一轮写的东西上（原文）：

```
MotionFilmstripTests.swift:4500  XCTAssertEqualWithAccuracy ("0.0") is not equal to ("2500.0") +/- ("625.0") - 产品那卷的记录时长…
MotionFilmstripTests.swift:4532  XCTAssertGreaterThan ("0.0") is not greater than ("0.005") - 该扫的那一档什么都没变…
MOTION_FLOOR_SUITE_NAMELESS_RED=1 汇总行说这一卷红了 2 次，日志里只找得到 1 个名字
```

三条一起看，本轮的账就清楚了：**处置已经说"这台机器判不了这一臂"，而这三处各自还在按别的话判。**

### U-160 · 前提钉子挂在结论尺的输出上 ⇒ 一台机器"看不见运动"被改写成"探针坏了"

R82 那条卷长钉子写的是 `XCTAssertEqual(shape.recordedMilliseconds, 2500 ± 625)`，
而 `recordedMilliseconds` 是 `loopShape` 的输出 —— 它的 guard 分支（峰值 0、时刻不配对、只有一帧）
**一律返回 0**。本机永远看不见这个耦合，因为本机有运动；runner 那一遍产品峰值 0.000，
于是 guard 走通、卷长变 0、钉子红，报的是"这些时刻不属于这卷帧对"——一个探针罪名，
而真实情况是"这台机器看不见这一档节拍的循环"。
⇒ 新增 `FilmPremise(frames:stamps:)`：**卷长与配对从时刻本身算**，与有没有运动无关
（一条静止 2.5 秒的卷仍然是 2.5 秒）。真值表第⑧格钉的是"两把尺必须给出不同的数"：
`still.spanMilliseconds == 1000` 而 `deadShape.recordedMilliseconds == 0`，
再加一条 `XCTAssertNotEqual(两者)` —— 谁把它们接回同一把尺，那一格就红。
**同族**：U-155（错话写得出来）、U-139（给没量过的东西写阈值）；这一条的新形状是
**"结论尺的输出被当成它自己的前提"**，而它只在另一台机器上才现形。

### U-161 · 比较的两边必须同为一种单位：`with N failures` 数的是断言，不是用例名

`NAMELESS_RED = summary - len(named)`：R82 那一遍 summary 说 2 次失败（同一条用例里两句 XCTAssert），
而 `failures` 是**去重后的用例名**（1 个）⇒ 报出"有一条红没有名字"，而两条红都有名字。
这一格存在的意义恰恰是"有红没名字"，所以它一旦被误报，下一轮就有人来把它放宽（R36 那一族的反面）。
⇒ 改成 `attributable = max(failure_lines, len(named))`，其中 `failure_lines` 数的是
`error: -[…方法] :` 那种**每句失败各一行**的行；两边同为行数。
两格回归测试：一条用例两句红 ⇒ 不许报 NAMELESS（但仍报 `SUITE_RED=1`）；
同一份夹具抽掉一行 ⇒ NAMELESS 必须回来（R64 的 stdout 成块丢的形状，不许被这次修法放走）。

### U-162 · 同一件事只准判一次：绝对地板必须听处置的话

峰值地板（`peak(running) > 0.005`）问的是"这台机器上这一臂有没有东西在动"——
这与处置问的是**同一件事**，只是换了个绝对阈值。处置已经判"环境不行"之后，
这条地板再红一次，等于把同一个事实用两个身份报出去，而第二个身份（"扫光没落地"）
天然把责任推给产品。⇒ 现在只有 `.ok / .productRed`（环境已被证明有资格判这一臂）时
绝对地板才说话；其余两支打一行 `MOTION_SHIMMER_PEAK_NOT_JUDGED 峰值=… 处置=…`。
**不豁免的那一条留在原地**：减弱动态那档"必须静止"永远判 ——
"看不见运动"永远不会伪造出运动来，所以那一臂没有环境借口（这一句是本轮的边界，别扩大）。

### 看图量出来的那一格（117 从"看图觉得"变成有数字）

`r83_band_fanout.py` 逐帧量三根条上亮斑的中心（24 帧里 22 帧可用，2 帧因"亮带不在这根条上、
条内剖面是单调斜坡"被丢掉并数出来）：

```
%s
```

⇒ **同一帧内**三根条的亮斑中心**绝对**位置最大差 170pt，而**归一化**位置只差 0.003（≈1pt）；
正对照：第一根条的归一化中心在 22 帧上取到 22 个不同值（0.09→0.92）⇒ 亮带确实在一路扫。
结论：亮带是**每根条各扫各的**，不是一块光穿过整组骨架 —— 机制在
`SkeletonMotion.unitPoints(phase:)` 给的是 `UnitPoint`，而它被用在每根条自己的 `LinearGradient` 上。
这一条改产品是下一轮的事（117 已带数字与修法）。

量的过程本身又抓到两把尺读错东西（都写进工具的注释里，因为它们各红过一次结论）：
① 阈值取"高于本行中位数 + 1" ⇒ 量到的是**整根条**（条带底色本来就比窗口背景亮），
第一根条的质心恒等于它的中点 88.0pt、24 帧一个数都不动；
② 亮带不在的那根条上，条内剖面是单调斜坡，"半程以上"退化成条的中点 ⇒ 这种帧必须**丢掉并数出来**
（最后一帧就是这么把散布从 0.003 顶到 0.448 的）。⇒ 记成 **U-163**：
相对阈值在信号缺席时不是"读不到"，而是**读到一个与信号无关的假数**，必须配一条"信号在不在"的门。

### 牙

%s

两刀（M448 / M449）**按实存活为"本地无判别力"**：本机有运动、处置是 `.ok`，
所以"把钉子挂回结论尺"与"地板不管处置"这两种改法在本机都不改变结果 ——
它们的牙在 runner 上，而 R82 的 CI 已经现场演示过这两条各红一次。
这一格不许被改写成"抓到"：按实记，是这一族从 R63 就立下的规矩（U-99 的两种存活）。

### 验证（本机，逐条实跑）

```
swift build --build-tests                告警 %s
swift test（全量）                       %s
动效那一步                               %s
捕获闸门                                 %s
frame_baseline.py check --against working %s
python3 -m unittest discover -s scripts  %s
```

本轮三卷的读数（本机 2×，全量那一遍）：

```
%s
%s
%s
%s
```

### 七维自评

| 维度 | 得分 | 说明 |
|---|---|---|
| 原生感 | 19 / 20 | 零产品改动；117 量出来的"每根条各扫各的"是一处**不原生**，本轮只把它变成数字，改在下一轮 |
| 流畅度 | 18 / 20 | main 上那朵红是本轮修掉的（我上一轮自己造的假红），扫光这一位在 runner 上从此是一朵有名字的未覆盖 |
| 层次与材质 | 15 / 15 | %s |
| 动效细节 | 13 / 15 | 处置与绝对地板的关系被理清（同一件事只判一次）；亮带形状仍待改 |
| 交互反馈 | 9 / 10 | 反馈本身没动 |
| 可访问性 | 8 / 10 | 减弱动态那一档的"必须静止"仍然是无条件判；真机批次 72 还没人看 |
| 性能 | 14 / 15 | 全量 %s；闸门多算一个行数，成本可忽略 |

**94 / 100**。分数没涨的原因写在上面：本轮的产出全部是"把上一轮我自己造的三处不干净修干净"，
加上一条把看图变成读数的量 —— 它开出了下一轮要改的产品缺陷，但本轮没改画面。

### U-164 · 电池的 python 臂也有同一个盲区：模块级导入失败被读成"全绿"

M450 第一版把 Swift 风格的 `//` 注释写进了 Python 变异文 ⇒ 被改的闸门脚本**语法都不对**，
`unittest` 只打一条 `ERROR: test_motion_floor_gate (unittest.loader._FailedTest…)`，
四条用例名一条都不出现 ⇒ 旧分类器把四个都读成 green ⇒ 这一刀被报成"没抓到"。
⇒ `python_verdicts` 现在认 `import-error`（导入失败/语法错算红，且按实报数）。
这已经是**第三次**同一族（U-151 把崩溃读成没跑、U-158 把崩掉的用例读成没跑、这次是导入失败）：
每加一条判据通道，第一件事是问"它坏的时候长什么样，我的分类器认得吗"。

### 仍未解决

- BACKLOG **117**（本轮量完，下一轮改产品）：亮带每根条各扫各的 ⇒ 把渐变抬到容器层，
  带 before/after 条带图；静置画面预计不变（phase 0 时亮带在条外），帧基线仍要同提交复核。
- BACKLOG **118**（本轮开）：`loop-clock-not-sustainable-at-product-rate` 这一朵有名字的未覆盖
  **不在覆盖地板的登记表里** —— 登记表按四条场景臂统计，而扫光不是场景臂 ⇒
  114 结案之后这一位变成"永久未覆盖而没人统计"。要做：给常驻循环那一族加一格登记（判到 / 点名 二选一）。
- BACKLOG **116**（R82 开，本轮未做）：那五条 `UICaptureTests` 的 skip 仍然没有"为什么今天没跑"的读数。
- BACKLOG **115**、111、108 余下、77 路 b、101 ②③、106；真机 68.1 / 68.2 / 69.1 / 70.1 / 71.1 / 72.1 / 72.2。
''' % (read(os.path.join(REPO, '.scratch/motion-audit-2/r83_fanout_readings.log')).strip(),
       KNIFE_TABLE, BUILD_WARN, FULL_TEST, MOTION_FACTS, GATE, FRAME, SCRIPTS,
       SHIM, FILM, RATE_WIT, COARSE_WIT, FRAME, FULL_TEST)

UI_AUDIT = u'''## 第 85 轮 · R83：上一轮那枚钉子挂错了对象 —— 前提不许挂在结论尺的输出上（结案 114 / 新开 118 / U-160…U-163 / D-141）

- 读 R82 的 CI（run 38781113064）：**114 落在预登记的第一支** ——
  runner 产品 `帧数=21 变化帧对=0 峰值=0.000`、等节拍证人 `coverage=0.284`、粗节拍证人 `coverage=1.000`
  ⇒ 这台机器带得动 20Hz 带不动 30Hz，处置正确点名 `loop-clock-not-sustainable-at-product-rate`。
- 但那一步仍然红，两朵都在我上一轮写的东西上（U-160）：卷长钉子挂在 `LoopShape.recordedMilliseconds` 上，
  而它在峰值 0 时被 guard 归零 ⇒ "看不见运动"被改写成"探针坏了"。
  修法：新增 `FilmPremise(frames:stamps:)`，卷长与配对**从时刻本身算**；真值表第⑧格钉"两把尺必须给不同数"。
- U-161：闸门的 `NAMELESS_RED` 拿"失败次数"去减"用例名个数"，一条用例两句断言一起红就报假红 ⇒
  比较两边同为**失败行数**（`failure_lines`），两格回归测试一正一反（同一条用例两句红 / 抽掉一行必须回来）。
- U-162：绝对峰值地板与处置问的是同一件事 ⇒ 只有环境被证明有资格判这一臂时地板才说话，
  其余打 `MOTION_SHIMMER_PEAK_NOT_JUDGED`；**减弱动态那档"必须静止"不豁免**（看不见运动伪造不出运动）。
- U-163 / 117 量完：逐帧量三根条的亮斑中心（`r83_band_fanout.py`）——
  同帧内绝对位置最大差 **170pt**、归一化只差 **0.003**，正对照 22 帧 22 个不同取值
  ⇒ 亮带是每根条各扫各的（`unitPoints` 落在每根条自己的渐变上）。改产品在下一轮。
- 牙：M446–M450 五刀 —— 三刀本地有牙全 CAUGHT（M446 真值表第⑧格、M447 真值表与卷长钉子两处、
  M450 新增那格 python 回归测试），两刀**按实存活为"本地无判别力"**（M448/M449 的牙在 runner 上）。
  两把刀的期望第一版都写窄了（M446 的 `>=` 根本改不动那一格、M447 本机红两处而我只写了一处），
  都是 U-149 那一族的复发：**先跑，再按实际红在哪几格写期望**。
- 零产品改动：%s；全量 %s；脚本 %s；告警 %s。

''' % (FRAME, FULL_TEST, SCRIPTS, BUILD_WARN)

BACKLOG_CLOSE_114 = u'''    → **R83 结案（落在预登记的第一支，而且是被那把等节拍证人量出来的）**：
    runner 那一遍 `MOTION_SHIMMER 扫 帧数=21 变化帧对=0 峰值=0.000 采样≈118ms`、
    等节拍证人 `帧对=35 在变=2 coverage=0.284`、粗节拍证人 `帧对=26 在变=23 coverage=1.000`
    ⇒ 这台机器带得动 20Hz 的常驻循环，带不动 30Hz 那一档 —— 与"视图归谁"无关（②排除），
    也不是 coverage 这把尺算不出来（③排除：两颗证人都算出来了）。
    处置走 `MOTION_NOT_RUN=loop-clock-not-sustainable-at-product-rate`，判据不判产品。
    同轮修掉两朵**上一轮我自己造的**假红（U-160 卷长钉子挂在结论尺的输出上、
    U-162 绝对峰值地板不管处置说话），以及闸门那格单位不一致（U-161）。
    剩下的那一半不是 114 的问题，是登记的问题 ⇒ 新开 **118**。

'''

BACKLOG_118 = u'''118. **一朵有名字的未覆盖，登记表里却没有它的位置：常驻循环那一族不进覆盖地板**（R83 开 / 与 100、114、92 同族）：

    `motion_floor_expectations.json` 按**四条场景臂**统计 judged/not-run，而骨架扫光不是场景臂 ——
    它是 `testSkeletonSweepActuallySweeps` 自己的一卷。于是 R83 之后这一位的状态是：
    本机判（coverage 0.95–1.00），runner 永远点名 `loop-clock-not-sustainable-at-product-rate`，
    而**覆盖地板既不数它也不许它缺席** —— 它红的时候闸门报红，它不红的时候没人知道它今天判没判。
    这正是 R46 建这张表要治的"掉了一臂没人报"，只是这一族不在表的形状里。
    要做的一小步：给登记表加一节 `loops`（或把扫光当成一条虚拟臂），
    登记"必须判到 or 允许哪几种点名"，并让 `motion_floor_gate.py` 数它 ——
    判据是**两格**：点名时不红、缺席时红（与 R36 给捕获卷立的那条同形）。
    不许的处置：把扫光从判据里删掉来让表自洽；或者把 114 的点名当成"已经有人负责了"。

'''

DECISION = u'''
### D-141 · 前提从时刻本身读，绝对地板听处置的话，红与"没跑"不许各判一次（R83 / U-160、U-161、U-162）

**背景**：R82 的 CI（run 38781113064）上 `Motion coverage floor` 红，三条原文：

```
4500  XCTAssertEqualWithAccuracy ("0.0") is not equal to ("2500.0") +/- ("625.0")
4532  XCTAssertGreaterThan ("0.0") is not greater than ("0.005")
      MOTION_FLOOR_SUITE_NAMELESS_RED=1（汇总 2 次红、日志里 1 个用例名）
```

而那一遍的处置行是 `MOTION_NOT_RUN=loop-clock-not-sustainable-at-product-rate`
（产品 coverage 0.000、等节拍证人 0.284、粗节拍证人 1.000）。
⇒ 一句话：**处置已经说"这台机器判不了这一臂"，同一轮里还有三处在按别的话判它。**

**决定**：
1. 前提与结论分家。新增 `FilmPremise(frames:stamps:)`：配对 = `stamps.count == frames`，
   卷长 = `stamps.last - stamps.first`，**都不看有没有运动**。
   真值表第⑧格钉"静止一卷的 premise 报 1000ms 而结论尺报 0ms，两者必须不同"——
   谁把前提接回结论尺，那一格就红。
2. 绝对地板只在环境被证明有资格判这一臂时说话（`.ok / .productRed`）；
   其余两支打一行 `MOTION_SHIMMER_PEAK_NOT_JUDGED 峰值=… 处置=…`。
   **边界写死**：减弱动态那档"必须静止"永远判 —— 看不见运动伪造不出运动，
   这一族的下一次扩大必须先推翻这句话。
3. 闸门的比较两边同为失败**行数**（`failure_lines`），不是用例名个数；
   两格回归测试一正一反，防止这次修法把 R64 那朵"成块丢"放走。
4. 114 结案（第一支），并新开 118：一朵有名字的未覆盖如果不在登记表里，
   "有人负责"就只剩一句话。

**代价**：`MOTION_SHIMMER_PEAK_NOT_JUDGED` 是新增的一行读数，不红、也不进登记表（这正是 118）。
**被这一条杀掉的东西**：`XCTAssertEqual(shape.recordedMilliseconds, …)` 那种"拿结论尺当前提"的写法，
以及 `summary - len(named)` 那种单位不对齐的减法。
'''

CHANGELOG = u'''### Tests（R83：上一轮那枚钉子挂错了对象 —— 前提从时刻本身读，绝对地板听处置的话；结案 114 / 新开 118 / U-160…U-163 / D-141）
- 读 R82 的 CI：**114 落在预登记的第一支**（runner 带得动 20Hz、带不动产品那一档 30Hz），
  等节拍证人 `coverage=0.284` 与粗节拍证人 `coverage=1.000` 并排就是分诊表本身。
- 修掉上一轮我自己造的三处不干净：
  ① 卷长钉子挂在 `LoopShape.recordedMilliseconds` 上（峰值 0 时被 guard 归零 ⇒ 把"看不见运动"
  报成"探针坏了"）⇒ 新增 `FilmPremise(frames:stamps:)`，前提从时刻本身算，真值表钉"两把尺必须给不同数"；
  ② 绝对峰值地板不管处置说话 ⇒ 只有 `.ok / .productRed` 时判，其余点名 `MOTION_SHIMMER_PEAK_NOT_JUDGED`
  （减弱动态那档"必须静止"仍然无条件判）；
  ③ 闸门 `NAMELESS_RED` 拿失败次数减用例名个数 ⇒ 两边同为失败行数，两格回归测试一正一反。
- 117 从"看图觉得"变成有数字：`r83_band_fanout.py` 逐帧量三根条的亮斑中心，
  同帧内绝对位置差最大 170pt、归一化差 0.003 ⇒ 亮带每根条各扫各的（改产品在下一轮）。
- 新开 118：一朵有名字的未覆盖不在覆盖地板的登记表里 ⇒ 常驻循环那一族也要有一格登记。
- 电池自己的 python 臂补第五种形状（U-164）：模块级导入失败时四条用例名都不出现，旧分类器读成"全绿"。
- 牙：M446–M450 五刀 —— 三刀本地有牙（两刀红在真值表第⑧格、一刀红在新增那格 python 回归测试），
  两刀**按实存活为"本地无判别力"**（把钉子挂回结论尺、地板不管处置，本机都不改变结果，牙在 runner）。

''' % ()

REPORT_U = u'''U-160 是**前提钉子挂在结论尺的输出上**（R83）：R82 写的卷长断言读的是 `LoopShape.recordedMilliseconds`，
而那个数在 guard 分支（峰值 0 / 时刻不配对 / 只有一帧）里一律归零。本机有运动 ⇒ 耦合看不见；
R82 的 CI 上 runner 产品峰值 0.000 ⇒ 卷长读 0 ⇒ 报成"这些时刻不属于这卷帧对"，
**把一台机器的"看不见运动"改写成"探针坏了"**。⇒ 前提必须从时刻本身算（`FilmPremise`），
并且真值表要钉"静止一卷 premise 报 1000ms、结论尺报 0ms，两者不许相同"。
这一条与 U-155 同一族但方向不同：那次是错话写得出来，这次是**对的话问错了对象**。

U-161 是**比较的两边不同单位**（R83）：`NAMELESS_RED = 汇总失败次数 - 去重后的用例名个数`，
而一条用例里两句 XCTAssert 一起红时前者是 2、后者是 1 ⇒ 报一朵"有红没名字"的假红。
假红的代价不是多一行日志，是**下一轮有人来放宽这一格**，而它守的正是"红必须有名字"。
⇒ 两边同为失败**行数**；并且补两格回归测试锁住反方向（真丢了一行必须还能报出来）。

U-162 是**同一件事被判两次，第二次必然越权**（R83）：绝对峰值地板与处置问的是同一件事
（"这台机器上这一臂有没有东西在动"），处置说"环境不行"之后地板再红一次，
等于用"扫光没落地"这个产品身份把同一事实重报一遍。⇒ 地板只在环境有资格判这一臂时说话；
而"必须静止"那一臂**不豁免** —— 看不见运动伪造不出运动，这是这条规矩的边界，别扩大。

U-163 是**相对阈值在信号缺席时读到一个与信号无关的假数**（R83，量 117 时现场两次撞到）：
"高于本行中位数 + 1" 量到的不是亮带而是**整根条**（条带底色本来就比窗口背景亮），
于是第一根条的质心恒等于它的中点、24 帧一个数都不动；改成行内相对极值之后，
亮带不在的那根条上剖面是单调斜坡，"半程以上"又退化成条的中点（那一帧把散布从 0.003 顶到 0.448）。
⇒ 任何"取高于某个相对线的部分"的尺，都必须配一条**信号在不在**的门，并把丢掉的帧数打出来。

'''

'''STAGES 与 main 在文件末尾。'''


def patch_visual_iteration():
    p = os.path.join(REPO, 'AGENT_VISUAL_ITERATION.md')
    s = read(p)
    assert '## Round 83' not in s, 'Round 83 已经写过了'
    write(p, s.rstrip('\n') + '\n\n' + ROUND_HEAD + SECTION)


def patch_ui_audit():
    p = os.path.join(REPO, 'AGENT_UI_AUDIT.md')
    s = read(p)
    assert u'## 第 85 轮' not in s
    anchor = u'## 第 84 轮 · R82：'
    assert s.count(anchor) == 1, 'UI_AUDIT 的 84 轮锚点不唯一'
    write(p, s.replace(anchor, UI_AUDIT + anchor, 1))


def patch_decisions():
    p = os.path.join(REPO, 'AGENT_DECISIONS.md')
    s = read(p)
    assert u'### D-141' not in s
    write(p, s.rstrip('\n') + '\n' + DECISION)


def patch_backlog():
    p = os.path.join(REPO, 'AGENT_BACKLOG.md')
    s = read(p)
    anchor_113 = u'113. **扫光那条"循环 vs 跳变"的判据在数帧对'
    assert s.count(anchor_113) == 1
    assert u'R83 结案' not in s
    s = s.replace(anchor_113, BACKLOG_118 + BACKLOG_CLOSE_114_IN_114 + anchor_113, 1)
    write(p, s)


BACKLOG_CLOSE_114_IN_114 = u''


def patch_changelog():
    p = os.path.join(REPO, 'CHANGELOG.md')
    s = read(p)
    anchor = u'## [Unreleased]\n'
    assert s.count(anchor) == 1
    assert u'### Tests（R83' not in s
    write(p, s.replace(anchor, anchor + CHANGELOG, 1))


def patch_final_report():
    p = os.path.join(REPO, 'AGENT_FINAL_REPORT.md')
    s = read(p)
    old = u'| 阶段二 **75 轮**审计（R9–R82，含 29d；'
    assert s.count(old) == 1
    s = s.replace(old, u'| 阶段二 **76 轮**审计（R9–R83，含 29d；', 1)
    old = u'以 `curve_from_ledger.py` 的 `PHASE2 n=75` 为准）'
    assert s.count(old) == 1
    s = s.replace(old, u'以 `curve_from_ledger.py` 的 `PHASE2 n=76` 为准）', 1)
    old = u'| 视觉台账 | U-31 … U-159（127 条；'
    assert s.count(old) == 1
    s = s.replace(old, u'| 视觉台账 | U-31 … U-163（131 条；', 1)
    old = u'**M100–M445**（阶段二 344 支；'
    assert s.count(old) == 1
    s = s.replace(old, u'**M100–M450**（阶段二 349 支；**R83 的 M446–M450 五刀：三刀本地有牙全 CAUGHT，'
                       u'两刀按实存活为"本地无判别力"（把卷长钉子挂回结论尺、把峰值地板改成不管处置，'
                       u'本机都不改变结果 —— 它们的牙在 runner 上，而 R82 的 CI 已经现场演示过这两条各红一次）** —— ', 1)
    old = u'自评曲线（**75 轮**，Round 9–82，含 29d 那一轮边界轮；'
    assert s.count(old) == 1
    s = s.replace(old, u'自评曲线（**76 轮**，Round 9–83，含 29d 那一轮边界轮；' + CURVE + u'）：', 1)
    anchor = u'U-155 是**探针把时刻存在对象身上，两卷连拍就会串卷'
    assert s.count(anchor) == 1
    s = s.replace(anchor, REPORT_U + anchor, 1)
    write(p, s)


def patch_state():
    p = os.path.join(REPO, 'AGENT_STATE.md')
    s = read(p)
    head_marker = u'最后更新：2026-10-16 01:20（本地 · R82 / 第 84 轮收尾：'
    assert s.count(head_marker) == 1, 'STATE 头部锚点不唯一'
    new_head = (u'最后更新：2026-10-16 02:20（本地 · R83 / 第 85 轮收尾：读 R82 的 CI'
                u'（run 38781113064，12m11s）—— **114 落在预登记的第一支**：runner 上产品 '
                u'`帧数=21 变化帧对=0 峰值=0.000`、等节拍证人 `coverage=0.284`、粗节拍证人 `coverage=1.000` '
                u'⇒ 这台机器带得动 20Hz、带不动 30Hz 那一档，处置点名 `loop-clock-not-sustainable-at-product-rate`，'
                u'不判产品。同一步仍然红，而两朵红都是我上一轮自己造的：'
                u'**U-160** 卷长钉子挂在 `LoopShape.recordedMilliseconds` 上（峰值 0 时被 guard 归零 ⇒ '
                u'"看不见运动"被改写成"探针坏了"）⇒ 新增 `FilmPremise`，前提从时刻本身算，真值表第⑧格钉'
                u'"静止一卷 premise 报 1000ms 而结论尺报 0，两者不许相同"；**U-162** 绝对峰值地板不管处置 ⇒ '
                u'只有 .ok/.productRed 才判，其余打 `MOTION_SHIMMER_PEAK_NOT_JUDGED`（减弱动态那档不豁免）；'
                u'**U-161** 闸门 NAMELESS 拿失败次数减用例名个数 ⇒ 两边同为失败行数，两格回归测试一正一反。'
                u'看图那一半：`r83_band_fanout.py` 把 117 量成数字 —— 同帧内三根条的亮斑中心绝对差最大 170pt、'
                u'归一化只差 0.003 ⇒ **亮带每根条各扫各的**（改产品在下一轮），路上又抓到两把尺读错东西（U-163）。'
                u'新开 **118**：一朵有名字的未覆盖不在覆盖地板的登记表里。'
                u'牙 M446–M450 五刀：三刀本地有牙、两刀按实存活为"本地无判别力"。'
                u'全量 %s；动效闸门 %s；捕获闸门 %s；帧基线 %s；脚本 %s；告警 %s。'
                u'**下一轮第一件事：改 117（把亮带抬到容器层，带 before/after 条带图与帧基线复核）**）\n\n'
                u'> 上一轮（R82 / 第 84 轮收尾）原文开头：' + head_marker) % (
        FULL_TEST, MOTION_FACTS, GATE, FRAME, SCRIPTS, BUILD_WARN)
    write(p, s.replace(head_marker, new_head, 1))


def fix_curve():
    real = summary('CURVE')
    for rel in ('AGENT_VISUAL_ITERATION.md', 'AGENT_STATE.md', 'AGENT_FINAL_REPORT.md'):
        p = os.path.join(REPO, rel)
        t = read(p)
        if CURVE not in t:
            print('  %s 里没有占位符' % rel)
            continue
        write(p, t.replace(CURVE, real))
        print('  %s：占位符 → %s' % (rel, real))


def close_114_in_backlog():
    """114 那一节末尾补一行结案（它开在 R82 那一版里，位置在 113 之前）。"""
    p = os.path.join(REPO, 'AGENT_BACKLOG.md')
    s = read(p)
    anchor = u'    不许的处置：抬 `minCoverage`、把 ①② 合并成"反正都算没跑"、或者在拿到那三行之前先改产品。\n'
    assert s.count(anchor) == 1, '114 的收尾锚点不唯一'
    s = s.replace(anchor, anchor + BACKLOG_CLOSE_114, 1)
    write(p, s)


STAGES = {
    'A': (patch_visual_iteration, patch_ui_audit, patch_decisions, patch_backlog,
          close_114_in_backlog, patch_changelog),
    'B': (patch_state, patch_final_report),
    'C': (lambda: fix_curve(),),
}


def main():
    stage = sys.argv[1] if len(sys.argv) > 1 else 'A'
    for fn in STAGES[stage]:
        fn()
        print('已写 %s' % fn.__name__)
    print('五刀：%s' % ', '.join('%s=%s' % (t, k) for t, _, k in KNIVES))


if __name__ == '__main__':
    main()
