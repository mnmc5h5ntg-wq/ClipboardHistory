# -*- coding: utf-8 -*-
'''R82 的台账补丁（第 84 轮 / Round 82）。

所有数字都从两处产物里读，不许手抄：
  * `.scratch/motion-audit-2/r82_mutation_battery_v5.log` —— 九刀的逐条结论
  * `.scratch/motion-audit-2/r82_verify_summary.log`     —— 全量验证的逐条读数
每条 anchor 都断言"命中且只命中一次"，落不了地就整批不写。
'''
import io
import os
import re
import sys

REPO = '/Users/wangziyi/Codex_Project0'
BATTERY = os.path.join(REPO, '.scratch/motion-audit-2/r82_mutation_battery_v5.log')
SUMMARY = os.path.join(REPO, '.scratch/motion-audit-2/r82_verify_summary.log')


def read(path):
    return io.open(path, encoding='utf-8').read()


def write(path, text):
    io.open(path, 'w', encoding='utf-8').write(text)


def knife_table():
    text = read(BATTERY)
    rows, order = {}, []
    for m in re.finditer(r'^(M4\d\d) (.+?)$', text, re.M):
        tag, note = m.group(1), m.group(2)
        tail = text[m.end():]
        verdict = re.search(r'   (CAUGHT|ESCAPED|NOT-RUN|NOT-APPLIED)', tail)
        rows[tag] = (note, verdict.group(1) if verdict else '?')
        order.append(tag)
    return [(t,) + rows[t] for t in order]


def summary(key, default=None):
    text = read(SUMMARY)
    m = re.search(r'^%s=(.+)$' % re.escape(key), text, re.M)
    if not m:
        if default is None:
            raise SystemExit('验证摘要里缺 %s —— 先把验证跑完再来写台账' % key)
        return default
    return m.group(1).strip()


KNIVES = knife_table()
CAUGHT = sum(1 for _, _, mark in KNIVES if mark == 'CAUGHT')
ESCAPED = [t for t, _, mark in KNIVES if mark != 'CAUGHT']
FULL_TEST = summary('FULL_TEST')
SKIPPED = summary('SKIPPED')
BUILD_WARN = summary('BUILD_WARNINGS')
FRAME = summary('FRAME_BASELINE')
GATE = summary('CAPTURE_GATE')
SCRIPTS = summary('SCRIPT_TESTS')
MOTION_FACTS = summary('MOTION_FLOOR')
SHIM = summary('SHIM_READING')
RATE_WIT = summary('RATE_WITNESS_READING')
COARSE_WIT = summary('COARSE_WITNESS_READING')
MIRROR = summary('MIRROR_READING')
# 曲线那一格由 `curve_from_ledger.py` 在**本轮台账落盘之后**才量得到（它有尾轮守卫，U-150），
# 所以三段写：A 写内容 → 跑曲线 → B 写 STATE/报告 → C 把占位符换成真读数。
CURVE = 'CURVE_PLACEHOLDER'


ROUND_HEAD = ('## Round 82 · 单颗证人被上一遍 CI 打回：证人必须与它作证的判据**同节拍**'
              '（结案 113、110 的第一实例 / 新开 114–117 / U-155…U-159 / D-140）\n')

SECTION = u'''
### 本轮开场的位点清单（按契约带坐标；本轮 0 个产品文件）

本轮重新判断的那一位是**加载态骨架屏的那条扫光**，位置与尺寸沿用已入账的读数：
详情预览区 `.loading` 分支里那三根 `SkeletonMotion.barFractions = [0.42, 0.86, 0.64]` 的条带，
每根高 8pt、圆角 `VisualRadius.chip` = 4pt，亮带 `bandSize` 0.3 从 x=−0.3 扫到 x=1.0（单位是条带宽），
一圈 `MotionCatalog.duration(for: .skeletonSweep)` = 1.5s、每拍 `SkeletonMotion.tickInterval` = 1/30s。
帧基线里它对应 `detail-loading` 那几张（本轮 %s ⇒ 静置画面一个像素没动）。
"这条该不该有动效"的判断没变（M9 那条感知等待的理由仍然成立，抬升 0.12 也仍然在
`minimumHighlightLift` = 0.08 之上）；**本轮动的是判它的那把尺**。

### 读 R81 的 CI（run 38770024897，12m38s）：唯一那朵红就是 113 说的那朵，而它带了新信息

失败步骤只有一个：`Motion coverage floor`，
`MOTION_FLOOR_FACTS judged=4/4 executed=49 not-run=- 红的用例=testSkeletonSweepActuallySweeps`、
`MOTION_FLOOR_SUITE_RED=1 … ("2") is less than ("3")` —— 与 R80 同一朵，没有新增红；
R80 那四条焦点红在 1× 上不再红（`QUICKPICK_FOCUS_INK 亮 缩放=1× 带墨面积=89.2pt² 焦点搬动=0.0pt²(地板 40.0…)
证人臂撤占位字=88.9pt²` 原样打出来了 ⇒ R81 的处置生效）。**捕获那一步今天全绿**。

真正的收获是那一遍同时打出的两行对照（原文）：

```
runner  MOTION_SHIMMER 扫 帧数=27 变化帧对=2 峰值=0.015 采样≈86ms
runner  MOTION_CONTROL 渐变端点 帧数=21 峰值=0.029 变化帧对=13
runner  MOTION_CONTROL 计数方块 帧数=19 峰值=0.029 变化帧对=17
```

⇒ 如果照 R81 的计划直接换成"一颗证人"，这一遍 CI 会判成 `.productRed`（证人在动、产品没动）。
但那条推论**说过头了**：那颗证人是 20Hz、亮带抬 0.45，而产品是 30Hz、抬 0.12 ——
"这台机器带得动一个 20Hz 高对比循环"并不蕴含"带得动产品那一档"。
R68 立的是"证人必须与判据问同一句话"，那句话里有一个具体的赫兹数和一个具体的抬升。

### 修法一（判据形状）：数帧对 → coverage

`LoopShape(pairs, changingPairs, peak, coverage, recordedMilliseconds)` +
`loopShape(fractions:stamps:)`，判据读 **coverage**（首尾两个"还在变"的帧对之间的时间 ÷ 整卷时长）
⇒ 与帧数无关。`minCoverage = 0.5`：本机真值 **0.955**，一次跳变在 20 帧对上是 **0.05**，
中间十倍空间，0.5 不在刀尖上；地板**不许**为哪台机器过线而移动（110 立的规矩）。
合成真值表 `testTheLoopShapeClassifierIsATruthTable` 里最关键的是第③格：
同一种"一直在变"在 50ms 与 115ms 两档采样下**必须同判定、同 coverage**，
而旧那把"数帧对"的尺在两档上必须给出**不同**的个数 —— 这一格钉的就是换尺的理由本身。

### 修法二（证人）：一颗 → 两颗，等节拍那颗决定红与不红

* `GradientTickView` 开成四个参数（节拍 / 每拍推进量 / 底色 / 亮带），默认值 = 原来写死的那几个数
  ⇒ 老调用点（`requireObservableMotion`、`MOTION_CONTROL`）读数不变；
* `GradientTickView.productRate()`：30Hz、每拍 (1/30)/1.5、0.06→0.18、同一颗 `VisualShape.rounded(VisualRadius.chip)`。
  四个数**写死在测试里**（读产品常量的话，产品哪天把抬升调到看不见，证人跟着一起瞎 ⇒
  "环境看不见"那一支永远有人签字，与 `FadeClockView` 把 150ms 写死是同一条理由）；
  代价由一条新的会红的钉子兜住：`testTheLoopWitnessStillMirrorsTheProductLoop`
  断言这四个数**仍等于** `SkeletonMotion` / `MotionCatalog` 的那几个（漂移 = 红，不是注释）。
* 处置 `loopAdjudication(product:rateWitness:coarseWitness:)`：产品在跑 ⇒ 绿；
  等节拍在跑而产品没跑 ⇒ **产品红**；等节拍也没跑 ⇒ `MOTION_NOT_RUN=loop-clock-not-sustainable-at-product-rate`；
  连粗节拍那颗都整卷没拍到 ⇒ **证人坏**，红（空支票守卫，M439 钉它）。

本机三卷（同一次跑，2×）：

```
%s
%s
%s
%s
```

**这一组数里最有用的是等节拍那颗与产品的接近程度**：产品 20/45 对在变、等节拍证人 21/45 对，
峰值都是 0.015 —— 把节拍与抬升对齐之后，"归属不同"这件事在本机上几乎不产生差别。
所以 runner 上那 2 对 vs 13 对的悬殊，很可能大部分是**参数差**而不是产品差，
下一遍 CI 会给出答案（BACKLOG 114）。

### U-155 · 探针把时刻存在自己身上，两卷连拍就会串卷 —— 而**任何断言都拦不住等长的两卷**

第一版的判据写成了：

```swift
let runningFrames = probe.record(reduceMotion: false)   // 第一卷
let stopped = deltas(probe.record(reduceMotion: true))   // 第二卷，顺手覆盖了 probe.lastStamps
let shape = loopShape(fractions: running, stamps: probe.lastStamps)  // ← 用第二卷的时刻算第一卷
```

本机第一次跑出来是 `coverage=0.000 记录时长=0ms`（两卷碰巧不等长 ⇒ 掉进 guard），
我把它当"探针坏了"来读；而**把它改对的中间那一版**读出来是 `coverage=0.979` ——
数字合理、判据绿、台账上就可以写"本机 0.98"。真正的证据是变异刀：
**M443 第一版把那句话原样改回 `probe.lastStamps`，四条判据全绿**
（`.scratch/motion-audit-2/r82_mutation_battery_v1.log`）。
⇒ 教训不是"记得当场取走"（我确实写了 `let runningStamps = probe.lastStamps`，
    但那只是把错误挪到了一个断言拦不住的距离上），
   而是**让错的那句话在类型上拼不出来**：探针改成返回 `GrabbedFilm(frames:stamps:)`，
   `lastStamps` 从这两个探针上删掉。
这个文件里其实**早就有**这个形状 —— 主场景探针的 `Film(frames:stamps:triggerFrame:)`
与淡入探针的 `FadeClockProbe.Run`；只有我上一轮新加的两个手写探针把时刻存在了对象身上。
**同族前科**：D-139 里"共享布尔 `opened` 让临时文件的第一行以为已经开过卷"是同一件事
（对象的 global 状态把调用方骗了），只不过那次的后果是崩，这次是**安静地给出一个像样的错数**。
TableProbe 还留着同款 `lastStamps`（它的调用点都是当场读）⇒ 记成 BACKLOG **115**。

### U-156 · 形状尺的 guard 把峰值原样报出去 ⇒ 前提故障冒充成"只动了一下"，处置方向跟着翻

`loopShape` 的 guard 分支（时刻与帧对数不匹配 / 只有一帧 / 整卷空白）原来返回 `peak: maximum`。
那一刻 `coverage = 0` 而 `peak = 0.02` ⇒ `verdict = .oneShot` ⇒
"尺没法算"被说成"产品只动了一下"，正好是 `.productRed` 那句话。
改成返回 `peak: 0` ⇒ `.notMoving` ⇒ 点名"没量到"。真值表第⑥格钉形状、
并额外钉一条**方向对照**：`notMoving` 的产品配上活的证人仍然必须红（它没有悄悄变绿）。
M444 就是这一刀。

### U-157 · 结构等式要双向，`>` 不是 `==`

同一根 guard 里的 `stamps.count > fractions.count` 只拦"少一根"，不拦"多一根"
（多一根意味着这列时刻来自另一卷更长的胶片 —— 正是 U-155 的形状）。
换成 `stamps.count == fractions.count + 1`，真值表里两格（少一根 / 多一根）各钉一边，
M443 换成这一刀 ⇒ 等式挪一格，本机每一卷真胶片都算"没量到" ⇒ 两条判据同时红。

### U-158 · 电池的分类器：崩掉的用例与没轮到的用例，不能都算『没跑』，也不能都算『红』

M443 把结构等式挪一格之后，真值表里那一格走进 `loopShape` 的分支去取 `stamps[last + 1]`，
越界 ⇒ `Fatal error` ⇒ 整个测试进程带走。于是那一条用例**既没有 `failed` 行也没有 `passed` 行**，
旧分类器把它归成 `absent`（=『这条没跑』），而排在它前面的 SHIM 确实红了 ⇒
电池报的是 **`ESCAPED 红的不是预期那几条`**。真相是这一刀抓得**最狠**：它把判据崩掉了，不是放过去了。
⇒ 分类器现在认两种新形状，而区分它们的依据必须是**这条用例自己开过口**：
`crashed` = 日志里有它的 `error: -[…方法]` 行却没有结论行（算红）；
`absent` = 从头到尾没提过它 ⇒ **没轮到**（不算红）。
`swift test` 不打 `started` 行，所以『整份日志里有崩溃痕迹』不能当归因依据 ——
用它会把排在崩掉那条**后面的每一条**都签字成红，那是 U-151 的镜像方向
（那次把崩解读成没跑，这次差点把没跑读成崩）。
**分类器只认它见过的形状**，而每一种新形状都必须带着自己的证据被命名。

### 真实看图：这条扫光**第一次**有条带图可看，而它立刻暴露了一件数字看不见的事

判据只读到"覆盖率 0.977、峰值 0.015"，看不出**亮带长在哪儿**。所以本轮给这条判据补了
`writeStrip("skeleton-sweep", …)`（放在所有闸门之前 ⇒ 红了也留一张能看的），
产物 `.scratch/motion-audit-2/r82_skeleton_sweep_strip.png`（24 帧 / 六列 / 4 行，按阅读顺序）。

看下来的结论分两半：

* **好消息，而且与数字一致**：亮带从每根条的左边进、右边出，第四行又从左边重新进来 ⇒
  `advance` 的绕回真的在演（不是"扫到一半卡住再弹回去"那一族），抬升 0.12 在这个尺寸上
  读起来是"有东西在动"而不是"闪"，克制程度符合"不喧宾夺主"。
* **数字看不见的那一半**：三根条上的亮带**不在同一条竖线上**。机制是可推出来的，不用猜 ——
  `SkeletonMotion.unitPoints(phase:)` 给的是 `UnitPoint`，而它被用在**每根条自己的**
  `LinearGradient` 上，`UnitPoint` 是按被填充形状的边界归一化的 ⇒
  同一相位下亮带在三根条上的绝对位置按宽度 0.42 / 0.86 / 0.64 **各自放大**，
  于是它更像"三根条各扫各的"，而不是"一块光从整组骨架上扫过去"。
  系统里的原生骨架（以及 GitHub 那类提交热图的呼吸感）是后者：一条带穿过整组，
  读起来才像"同一个光源"。
  ⇒ 新开 **BACKLOG 117**：先量三根条上亮斑中心的 x（逐帧、带正对照"同一根条两个相位必须不同"），
  再判要不要把渐变挪到**容器**上（那会改到静置画面 ⇒ 124 张帧要同提交 update）。
  本轮**不动产品**：这条是看图看出来的新缺陷，按规矩先量再改（也不许为了它今天改帧基线）。

### U-159 · 同一份代码的**全量卷里，skip 的条数在两次跑之间自己动了**（7 条的幅度，本轮量出来）

| 遍 | 原文 |
|---|---|
| R81 第一遍（`.scratch/motion-audit-2/r81_verify_summary.log`） | `Executed 796 tests, with 38 tests skipped and 0 failures … in 161.868s` |
| R81 另一遍（`/tmp/r81_full.log`，同一提交、同一台机器） | `Executed 796 tests, with 45 tests skipped and 0 failures … in 154.9s` |
| R82（`/tmp/r82/full.log`） | `Executed 799 tests, with 40 tests skipped and 0 failures … in 145.4s` |

⇒ **同一个提交里就有 38 与 45 两个数**（不是记账口径不同：两行的格式一模一样，时长不同 ⇒ 是两次跑）。
R82 的 40 = 799 − 3 条新判据之外还差着同样的抖动。`comm` 出来的差集落在五条 `UICaptureTests`
（`testSettingsHelperTextIsNotClipped`、`testInkDirectionRulerReadsBothEnds`、
`testRowTierProfileSeparatesCaptionFromTitle`、`testSettingsCaptionSitsCloserToItsOwnToggle`、
`testDarkSettingsSidebarTextIsACountedBlindSpot`）—— 同一份代码、同一台机器，
一会儿 skip 一会儿跑，而台账把它们都记成"过了"。
⇒ 记成 **BACKLOG 116**：这五条的 skip 判据必须把"为什么今天没跑"打成一行**有名字的读数**
（像捕获卷那族 `*_NOT_RUN` 一样），否则"这一轮多判了五条"和"上一轮少判了五条"
这两种相反的解释在台账上长得一样 —— 而**判据有没有跑**本身就是需要被审计的量。
本轮不给原因：第一版怀疑是变异电池的临时目录串了，读源码后不成立
（这五条各用 `temporaryDirectory/r28-clip-<UUID>`，互不共享）。**没量出来就别写。**
（顺带纠正我自己：R81 台账里那句"796 例 / 38 skip"引的是其中一遍，
它不是错的，但它被当成了"这一轮的固定属性"—— 一个会抖的数被写成了常量，U-139 同一族。）

### 牙

%s

### 验证（本机，逐条实跑）

```
swift build --build-tests                告警 %s
swift test（全量）                       %s / skipped %s
动效那一步                               %s
捕获闸门                                 %s
frame_baseline.py check --against working %s
python3 -m unittest discover -s scripts  %s
自评曲线                                 %s
扫光那条第一次有的条带图                  .scratch/motion-audit-2/r82_skeleton_sweep_strip.png（24 帧 / 六列）
全量 skipped（同一提交两遍 + 本轮，见 U-159）  38 / 45 / 40 —— 一个会抖的数，不许写成常量
```

### 七维自评

| 维度 | 得分 | 说明 |
|---|---|---|
| 原生感 | 19 / 20 | 零产品改动；扫光的抬升 0.12 与 4pt continuous 圆角都仍在系统语言里，本轮没脸加分也没被扣分 |
| 流畅度 | 18 / 20 | main 上那朵红换了个来源：不再是"判据吃采样"，而是"这一档节拍的循环在 runner 上带不带得动"（114，等 CI 读数）；本机 coverage 0.955 |
| 层次与材质 | 15 / 15 | %s |
| 动效细节 | 13 / 15 | 循环那条判据从"数帧对"换成时间之比 + 两颗证人；证人漂移有钉子 |
| 交互反馈 | 9 / 10 | 反馈本身没变 |
| 可访问性 | 8 / 10 | 减弱动态那一档仍然有判据（峰值 0.000），但真机复核仍欠（批次 72） |
| 性能 | 14 / 15 | 全量 %s；证人每进程一次，多出来的那一卷 2.5s 只在扫光那一条上付 |

**94 / 100**。比 R81 的一分来自"main 上那朵红的来源从我的尺换成了可判定的问题"，
扣的六分写在上面三行里：114 还没有答案，115/116 是本轮量出来但没修的账，
117 是看图看出来的新缺陷（按"先量再改"排到下一轮），批次 72 还没人看。

### 仍未解决

- BACKLOG **114**（本轮开）：runner 那一遍到底带不带得动 30Hz 那一档常驻循环 ——
  等节拍证人与产品那两行 coverage 给答案；若是"带不动" ⇒ `loop-clock-not-sustainable-at-product-rate`
  是一朵**有名字的未覆盖**；若是"带得动而产品没跑" ⇒ 那是第一条真红，回去查接线。
- BACKLOG **115**（本轮开）：`TableProbe` 仍然把抓帧时刻存在对象身上（同款 U-155 风险）。
- BACKLOG **116**（本轮开）：同一提交的全量卷里 skip 条数自己动了 7 条（38 / 45 / 40 三个数），
  而那五条 `UICaptureTests` 没有一行"为什么今天没跑"的读数 ⇒ 判据有没有跑，今天没人审计。
- BACKLOG **117**（本轮看图开出）：骨架扫光的亮带在每根条上**各扫各的**，
  不是一块光穿过整组骨架（`UnitPoint` 落在每根条自己的渐变上）。先量亮斑中心，再判要不要改容器层。
- BACKLOG 111、110 剩下的两格、108 余下、77 路 b、101 ②③、106；真机 68.1 / 68.2 / 69.1 / 70.1 / 71.1 / **72.1 / 72.2**。
''' % (FRAME, SHIM, RATE_WIT, COARSE_WIT, MIRROR,
       u'\n'.join(u'| %s | %s | **%s** |' % (t, n.split('⇒')[0].strip(), m) for t, n, m in KNIVES),
       BUILD_WARN, FULL_TEST, SKIPPED, MOTION_FACTS, GATE, FRAME, SCRIPTS, CURVE,
       FRAME, FULL_TEST)

UI_AUDIT = u'''## 第 84 轮 · R82：单颗证人被上一遍 CI 打回 —— 证人必须与判据同节拍（结案 113 / 新开 114、115 / U-155…U-159 / 新开四条 / D-140）

- 读 R81 的 CI（run 38770024897）：唯一那朵红就是 113 说的那朵（`变化帧对 2 < 3`），
  而那一遍还打出 `MOTION_CONTROL 渐变端点 帧数=21 变化帧对=13` ⇒ 直接换"一颗证人"会把
  `.productRed` 说出口，可那颗证人是 **20Hz / 抬 0.45**，产品是 **30Hz / 抬 0.12** —— 不是同一句话。
- 判据换成 **coverage**（变化覆盖整卷时长的比例，时间之比 ⇒ 与帧数无关），地板 0.5；
  真值表钉"50ms 与 115ms 两档采样下同判定、同 coverage，而旧尺两档给出不同个数"。
- 证人换成**两颗**：等节拍那颗（30Hz、每拍 (1/30)/1.5、0.06→0.18、同一颗 `VisualShape.rounded`）
  决定"产品红 / 环境不行"，粗节拍那颗只守"证人坏没坏"。四个数写死在测试里，
  由新判据 `testTheLoopWitnessStillMirrorsTheProductLoop` 钉住它们**仍等于产品**（漂移就红）。
- U-155：`probe.lastStamps` 会被后一卷覆盖 ⇒ 两卷连拍时用错时刻，而 **M443 第一版把这句话改回去，
  四条判据全绿**（等长的两卷任何断言都分不开）⇒ 修法换层：探针返回 `GrabbedFilm(frames:stamps:)`。
- U-156：guard 分支原来把峰值原样报出去 ⇒ "尺没法算"冒充"产品只动了一下"（处置方向会翻）⇒ 返回 0。
- U-157：`stamps.count > 帧对` 只拦少一根 ⇒ 换成 `== 帧对 + 1`，真值表钉双向，M443 钉这条。
- 牙：M437–M445 九刀，抓到 %d（%s）。
- 零产品改动：%s；全量 %s / skipped %s；脚本 %s；告警 %s。

''' % (CAUGHT, ('其余全 CAUGHT' if not ESCAPED else '未抓到：' + ','.join(ESCAPED)), FRAME, FULL_TEST, SKIPPED,
       SCRIPTS, BUILD_WARN)

BACKLOG_CLOSE_113 = u'''    → **R82 结案（判据形状换了，但 runner 那一问另开 114）**：
    ①"数帧对"换成 **coverage** = 首尾两个还在变的帧对之间的时间 ÷ 整卷时长 ⇒ 与帧数无关，
      地板 0.5（本机真值 **0.955**、一次跳变 **0.05** ⇒ 不在刀尖上）。地板一个数没为哪台机器挪过。
    ②证人从一颗变**两颗**：R81 的 CI 上唯一那颗证人是 20Hz / 抬 0.45，而产品是 30Hz / 抬 0.12，
      所以它当时的 13 对在变**不足以**判产品红。新加的等节拍证人（`GradientTickView.productRate()`，
      四个数写死并由 `testTheLoopWitnessStillMirrorsTheProductLoop` 钉住仍等于产品）
      决定"产品红 vs 环境不行"，粗节拍那颗只守"证人坏没坏"（空支票守卫）。
    本机三卷：产品 coverage **0.955**（20/45 对在变、峰值 0.015）、
    等节拍证人 **1.000**（21/45、峰值 0.015）、粗节拍证人 **1.000**（41/45、峰值 0.026）
    ⇒ 参数对齐之后，"视图归谁"在本机上几乎不产生差别，所以 runner 那 2 对很可能大部分是**参数差**。
    这件事只能由 runner 那一遍回答 ⇒ **新开 114**；113 这条（判据形状）到此结清。

'''

BACKLOG_NEW = u'''114. **runner 那一遍到底带不带得动产品那一档（30Hz / 抬 0.12）的常驻循环**（R82 开 / 113 的续问、与 110、38 同族）：

    R81 的 CI 上并排的两行是本机无法解释的：产品 `变化帧对=2 / 帧数=27 / 峰值=0.015 / 采样≈86ms`，
    而那颗 20Hz、抬 0.45 的证人 `帧数=21 变化帧对=13 峰值=0.029`。
    R82 把证人换成与产品同节拍同抬升之后，本机读到的是 20/45 与 21/45 —— 差一对。
    于是 runner 那悬殊的 2 vs 13 有三种可能，本轮没有依据区分：
    ①**参数**：那一档节拍的 Timer 在无头 runner 上就是带不动（那 13 对属于抬升更高的那颗）；
    ②**归属**：产品的 `SkeletonPreviewView` 那份时钟有它自己的问题（它的 `onReceive` 挂在
      `if let step` 的分支上，而证人挂在 `body` 顶上 —— 这是两者唯一剩下的结构差别）；
    ③**通道**：`coverage` 这把尺在 1× 上有别的性质（与 111 同族）。
    下一遍 CI 的三行 `MOTION_SHIMMER*` 就是分诊表：
    等节拍证人 looping 而产品 not ⇒ 命中 ②，`loopAdjudication` 会**红**，那时才动产品；
    两颗证人都不 looping ⇒ 命中 ①，判据点名 `MOTION_NOT_RUN=loop-clock-not-sustainable-at-product-rate`；
    两颗证人的 coverage 本身算不出来 ⇒ 命中 ③，回到 111 那条路。
    不许的处置：抬 `minCoverage`、把 ①② 合并成"反正都算没跑"、或者在拿到那三行之前先改产品。

115. **`TableProbe` 仍然把抓帧时刻存在对象身上**（R82 开 / 与 U-155 同一条，本轮自己留下的第二处）：

    本轮把 `SkeletonProbe` 与 `StateTickProbe` 改成返回 `GrabbedFilm(frames:stamps:)`，
    因为它们的"时刻"要进一条**时间之比**的判据；而 `TableProbe`（行动画那两条）留着
    `private(set) var lastStamps`，四个调用点都是"record 之后当场读"。
    今天它没有错 —— 但 U-155 的证据是：**当场读这件事，写错了也没有断言会红**
    （M443 第一版四条全绿）。行动画那两条判据吃的是"变化段时长 / 采样间隔"，
    与循环那条同一种性质，所以这里迟早也要绑成一卷。
    修法照抄本轮：探针返回一对，删掉共享的可变时刻。优先级不高，但不许忘掉。

116. **同一提交的全量卷里，skip 的条数会自己动 7 条，而那五条没有一行"为什么今天没跑"**（R82 开 / 与 96、100、111 同族）：

    `Executed 796 tests, with 38 tests skipped`（R81 第一遍）与 `Executed 796 tests, with 45 tests skipped`
    （R81 另一遍，同一提交、同一台机器、时长不同）；R82 是 799 / 40。
    差集是这五条 `UICaptureTests`：`testSettingsHelperTextIsNotClipped`、
    `testInkDirectionRulerReadsBothEnds`、`testRowTierProfileSeparatesCaptionFromTitle`、
    `testSettingsCaptionSitsCloserToItsOwnToggle`、`testDarkSettingsSidebarTextIsACountedBlindSpot`。
    它们 skip 的时候台账上看不见，跑的时候也是绿的 ⇒ **判据有没有跑**这件事今天没人审计。
    要做的一小步：这五条各打一行 `CAPTION_PROBE_NOT_RUN=<原因>`（与捕获卷那族同一个形状，
    闸门那边已经有"已登记的 NOT-RUN 逐条列出"的通道），然后 R83 起用两遍跑对比"跑了几条"。
    本轮**没给原因**：第一版怀疑是变异电池的临时目录串了，读源码不成立
    （这五条各用 `temporaryDirectory/r28-clip-<UUID>`）—— 没量出来就别写。

117. **骨架扫光的亮带是"每根条各扫各的"，不是"一块光穿过整组骨架"**（R82 看图看出 / 逐帧条带图 `r82_skeleton_sweep_strip.png`）：

    `SkeletonMotion.unitPoints(phase:)` 给的是 `UnitPoint`，而它被用在**每根条自己的**
    `LinearGradient` 上；`UnitPoint` 按被填充形状的边界归一化 ⇒ 同一相位下亮带在三根条上的
    绝对位置按 `barFractions = [0.42, 0.86, 0.64]` 各自放大，**不可能落在同一条竖线上**。
    机制这一步是推出来的（读代码即可，不依赖机器），看图与它一致。
    代价是可读性：系统的骨架与 GitHub 那类呼吸感都是"一个光源扫过整组"，
    而这里是三根条以三种速度各自亮一遍 —— 抬升只有 0.12，所以不刺眼，但**不原生**。
    下一轮先量再改：①逐帧量三根条上亮斑中心的 x（正对照：同一根条两个相位必须不同；
    反对照：三根条同一相位的中心必须**不**共线 —— 这条现在是本轮结论的载体）；
    ②若要改，把渐变抬到**容器**层（一个 `LinearGradient` 盖住整组，或按容器宽度换算 `unitPoints`），
    那会改到静置画面 ⇒ 124 张帧必须同提交 `frame_baseline.py update`。
    本轮不动产品：这是看图看出来的新缺陷，按"先 spike 再动仓库"的规矩排在下一次。

'''

DECISION = u'''
### D-140 · 循环那条判据读"覆盖整卷多长时间"，证人必须与产品同节拍同抬升（R82 / BACKLOG 113、114）

**背景**：`testSkeletonSweepActuallySweeps` 在 R80、R81 两遍 CI 上红，报的是
`("2") is less than ("3") — 只读到 2 对在变`。并排读数（原文来自 `gh api .../jobs/<id>/logs`）：

| 机器 | 产品那一卷 | 证人（那颗 20Hz 的） |
|---|---|---|
| 本机 2× | 帧数 46–48，变化帧对 20–23，峰值 0.015，采样 ≈53–55ms | 帧对 36–37，在变 32–33，峰值 0.026 |
| runner 1×（R80 / R81） | 帧数 23 / 27，变化帧对 **2**，峰值 0.015，采样 ≈115 / 86ms | 帧数 21，变化帧对 **13**，峰值 0.029 |

**决定**：
1. 判据不再数帧对，改读 **coverage** —— 首尾两个"还在变"的帧对之间的时间 ÷ 整卷记录时长。
   它是时间之比，所以与采样密度无关；真值表第③格钉的正是这个性质
   （同一种"一直在动"在 50ms 与 115ms 两档下必须同判定同 coverage，而旧尺必须给两个个数）。
   `minCoverage = 0.5` 介于本机真值 0.955 与一次跳变的 0.05 之间，**不许**为哪台机器过线而移动。
2. 证人**必须与它作证的判据同节拍、同抬升**。R81 之前那颗证人是 20Hz / 抬 0.45，
   而产品是 30Hz / 抬 0.12 —— 它当时那 13 对在变不足以判产品红（那是在替另一句话签字）。
   现在 `GradientTickView.productRate()` 用 30Hz、每拍 (1/30)/1.5、0.06→0.18、
   与产品同一颗 `VisualShape.rounded(VisualRadius.chip)`；四个数**写死在测试里**
   （不能读产品常量，否则被告把证人带走 ⇒ 与 `FadeClockView` 写死 150ms 同一条理由），
   漂移由 `testTheLoopWitnessStillMirrorsTheProductLoop` 判红。
   原来那颗高对比证人**留着**，但降级为只回答"这种画法这台机器看得见吗"（空支票守卫）。
3. 一卷胶片 = **帧 + 它们的时刻，绑在一起返回**（`GrabbedFilm`）。
   U-155 的实测是：把错的那句话（用后一卷的时刻算前一卷的形状）写回去，**四条判据全绿**，
   所以"当场取走 + 一条时长断言"不是修法，只是我把错误挪远了一点；
   能用的修法只有让错的话在类型上拼不出来。
4. 三条处置各自有刀：M437/M438（coverage 地板与分母）、M439（空支票那一支）、
   M442（恒过的处置）、M444（前提故障冒充"只动了一下"）、M443（结构等式挪一格）、
   M445（证人与产品分家）。

**代价**：动效那一步多跑一卷 2.5s 的证人（每进程缓存一次）；判据文件里多一个类型。
**被这一条杀掉的东西**：`XCTAssertGreaterThanOrEqual(transitionFrameCount(running), 3)`
那条计数判据 —— 它在两档采样下会说两句不同的话，而"几对在变"从今天起只作为**读数**打印。
'''

CHANGELOG = u'''### Tests（R82：循环那条判据从"数帧对"换成 coverage，证人从一颗换成两颗并要同节拍；结案 113、110 的第一实例 / 新开 114、115 / U-155…U-159 / 新开四条 / D-140）
- `testSkeletonSweepActuallySweeps` 不再数"几对帧在变"，改读 **coverage**
  （变化覆盖了整卷时长的几成；时间之比 ⇒ 与采样密度无关，地板 0.5 不为哪台机器移动）。
- 证人从一颗变**两颗**：新增 `GradientTickView.productRate()`（30Hz、每拍 (1/30)/1.5、0.06→0.18、
  同一颗 `VisualShape.rounded`）决定"产品红 / 环境不行"；原来那颗 20Hz 高对比的降级为
  只守"证人坏没坏"。起因是 R81 的 CI：产品 `变化帧对=2`、那颗证人 `13`，但它问的根本不是同一句话。
- 新判据 `testTheLoopWitnessStillMirrorsTheProductLoop`：证人那四个数**仍等于产品**（写死在测试里，
  漂移就红）；新判据 `testTheLoopShapeClassifierIsATruthTable`：七格合成真值表，含
  "50ms 与 115ms 两档采样同判定"与"时刻少一根/多一根都算没量到"。
- 分辨率那条闸门（BACKLOG 110 的第一个实例）改吃**事件内 P75**而不是"最粗那一次"：
  本机实测 `[50 51 52 53]` 与 `[50 51 52 81]` 的 P75 相同而最大值差 28ms，
  而旧闸门就是被这 28ms 从"判到"推到"判不到"的。
- `SkeletonProbe` / `StateTickProbe` 改成返回 `GrabbedFilm(frames:stamps:)`（U-155：
  两卷连拍时 `probe.lastStamps` 会被后一卷覆盖，而 M443 第一版把它改回去**四条判据全绿** ⇒
  断言拦不住等长的两卷，只能让错的话拼不出来）。
- 电池自己的分类器补第四类（U-158）：跑到一半进程死掉的用例不再被归成『没跑』。
- 牙：M437–M445 九刀，抓到 %d（%s）。

''' % (CAUGHT, ('无遗漏' if not ESCAPED else '未抓到：' + ','.join(ESCAPED)))


def patch_state():
    p = os.path.join(REPO, 'AGENT_STATE.md')
    s = read(p)
    head_marker = u'最后更新：2026-10-16 00:32（本地 · R81 / 第 83 轮收尾：'
    assert s.count(head_marker) == 1, 'STATE 头部锚点不唯一'
    new_head = (u'最后更新：2026-10-16 01:20（本地 · R82 / 第 84 轮收尾：读 R81 的 CI'
                u'（run 38770024897，12m38s）—— 唯一那朵红就是 113 说的那朵，而同一遍打出的'
                u'`MOTION_CONTROL 渐变端点 帧数=21 变化帧对=13` 把"一颗证人"这条路堵死了：'
                u'那颗证人是 20Hz / 抬 0.45，产品是 30Hz / 抬 0.12，它当时那 13 对不足以判产品红。'
                u'**113 结案**：判据换成 **coverage**（时间之比，本机真值 0.955 / 跳变 0.05 / 地板 0.5 不动），'
                u'证人换成两颗，等节拍那颗（30Hz、每拍 (1/30)/1.5、0.06→0.18、同一颗 VisualShape.rounded）'
                u'决定红与不红，四个数写死并由新判据 `testTheLoopWitnessStillMirrorsTheProductLoop` 钉住'
                u'仍等于产品。**110 的第一个实例**：分辨率闸门改吃事件内 P75（'
                u'`[50 51 52 53]` 与 `[50 51 52 81]` 的 P75 相同而最大值差 28ms）。'
                u'**U-155**：`probe.lastStamps` 会被后一卷覆盖 ⇒ 形状吃了别卷的时刻，'
                u'而**把那句话原样写回去，四条判据全绿**（M443 第一版，v1 日志）⇒ 修法换层：'
                u'探针返回 `GrabbedFilm(frames:stamps:)`，同轮再补 U-156（前提故障不许冒充"只动了一下"）'
                u'与 U-157（结构等式要双向）。新开 **114**（runner 上那一档节拍带不带得动，'
                u'由三行 `MOTION_SHIMMER*` 分诊）与 **115**（TableProbe 还留着同款共享时刻）。'
                u'全量 %s / skipped %s，%s，捕获闸门 %s，脚本 %s，告警 %s。'
                u'**下一轮第一件事：读 R82 的 CI 那三行 coverage，按 114 的分诊表走**）\n\n'
                u'> 上一轮（R81 / 第 83 轮收尾）原文开头：' + head_marker)
    s = s.replace(head_marker, new_head, 1)
    write(p, s)


def patch_visual_iteration():
    p = os.path.join(REPO, 'AGENT_VISUAL_ITERATION.md')
    s = read(p)
    assert '## Round 82' not in s, 'Round 82 已经写过了'
    s = s.rstrip('\n') + '\n\n' + ROUND_HEAD + SECTION
    write(p, s)


def patch_ui_audit():
    p = os.path.join(REPO, 'AGENT_UI_AUDIT.md')
    s = read(p)
    assert u'## 第 84 轮' not in s
    anchor = u'## 第 83 轮 · R81：'
    assert s.count(anchor) == 1, 'UI_AUDIT 的 83 轮锚点不唯一'
    s = s.replace(anchor, UI_AUDIT + anchor, 1)
    write(p, s)


def patch_decisions():
    p = os.path.join(REPO, 'AGENT_DECISIONS.md')
    s = read(p)
    assert u'### D-140' not in s
    write(p, s.rstrip('\n') + '\n' + DECISION)


def patch_backlog():
    p = os.path.join(REPO, 'AGENT_BACKLOG.md')
    s = read(p)
    # 1) 113 交作业：在它那一节的末尾（下一条目 112 之前）插结案行
    anchor_112 = u'112. **读数通道在并发下会把两行缝成一行'
    assert s.count(anchor_112) == 1
    assert u'R82 结案' not in s
    s = s.replace(anchor_112, BACKLOG_CLOSE_113 + anchor_112, 1)
    # 2) 新开 114、115 放在最前（113 之前）
    anchor_113 = u'113. **扫光那条"循环 vs 跳变"的判据在数帧对'
    assert s.count(anchor_113) == 1
    s = s.replace(anchor_113, BACKLOG_NEW + anchor_113, 1)
    # 3) 110 标第一个实例已修
    old = u'**R81 加了第二个实例：113**）：'
    assert s.count(old) == 1
    s = s.replace(old, u'**R81 加了第二个实例：113**；**R82 交了第一实例的修法：闸门改吃事件内 P75**）：', 1)
    write(p, s)


def patch_changelog():
    p = os.path.join(REPO, 'CHANGELOG.md')
    s = read(p)
    anchor = u'## [Unreleased]\n'
    assert s.count(anchor) == 1
    assert u'### Tests（R82' not in s
    s = s.replace(anchor, anchor + CHANGELOG, 1)
    write(p, s)


def patch_final_report():
    p = os.path.join(REPO, 'AGENT_FINAL_REPORT.md')
    s = read(p)
    # 计数器
    old = u'| 阶段二 **74 轮**审计（R9–R81，含 29d；'
    assert s.count(old) == 1
    s = s.replace(old, u'| 阶段二 **75 轮**审计（R9–R82，含 29d；', 1)
    old = u'以 `curve_from_ledger.py` 的 `PHASE2 n=73` 为准）'
    assert s.count(old) == 1
    s = s.replace(old, u'以 `curve_from_ledger.py` 的 `PHASE2 n=75` 为准）', 1)
    old = u'| 视觉台账 | U-31 … U-152（122 条；'
    assert s.count(old) == 1
    s = s.replace(old, u'| 视觉台账 | U-31 … U-159（127 条；', 1)
    old = u'**M100–M436**（阶段二 335 支；'
    assert s.count(old) == 1
    s = s.replace(old, u'**M100–M445**（阶段二 344 支；**R82 的 M437–M445 九刀，抓到 %d'
                    u'（U-155：M443 第一版「把用错时刻那句话原样写回去」四条判据全绿 ⇒ '
                    u'断言拦不住等长的两卷，于是修法从「加断言」换成「让错的话拼不出来」：'
                    u'探针返回 `GrabbedFilm(frames:stamps:)`；其余八刀分别钉 coverage 地板与其分母、'
                    u'空支票那一支、恒过的处置、峰值地板漂移、P75 退回 max、前提故障冒充"只动了一下"、'
                    u'结构等式挪一格、证人与产品分家）。' % CAUGHT
                    + ('（未抓到：%s）' % ','.join(ESCAPED) if ESCAPED else '') + u'** —— ', 1)
    old = u'自评曲线（**74 轮**，Round 9–81，含 29d 那一轮边界轮；均值 **92.43**，最低 86，最高 96）：'
    assert s.count(old) == 1
    s = s.replace(old, u'自评曲线（**75 轮**，Round 9–82，含 29d 那一轮边界轮；%s）：' % CURVE, 1)
    # 三条新 U
    anchor = u'U-151 是**变异电池把崩溃读成"编译没过"**（R81）：'
    assert s.count(anchor) == 1
    s = s.replace(anchor, REPORT_U + anchor, 1)
    write(p, s)


REPORT_U = u'''U-155 是**探针把时刻存在对象身上，两卷连拍就会串卷 —— 而等长的两卷任何断言都分不开**（R82）：
第一版把后一卷的 `lastStamps` 拿去算前一卷的形状，本机先读到 `coverage=0.000`（碰巧不等长），
"修好"之后读到 `0.979`（碰巧等长）—— **两个数都是同一个错的**，而后者看起来完全合理、
可以直接写进台账。决定性证据是变异刀：**把那句话原样写回去，四条判据全绿**。
⇒ 这一族的修法不在断言层：让错的那句话在类型上拼不出来（探针返回 `GrabbedFilm(frames:stamps:)`）。
同族前科是 D-139 的共享布尔 `opened`（对象的 global 状态骗了调用方），那次的后果是崩，这次是安静地给一个像样的错数。

U-156 是**"算不出来"不许返回真值的一半**（R82）：`loopShape` 的 guard 分支原来只把 coverage 归零、
峰值照报 ⇒ `verdict` 把"尺没法算"说成"产品只动了一下"，正好落在**判产品红**那一支。
哨兵必须是"整个没量到"（`peak = 0` ⇒ `.notMoving` ⇒ 点名 not-run），
而真值表还要额外钉一条方向对照：`.notMoving` 配上活的证人**仍然红**（它没有悄悄变绿）。

U-157 是**结构等式要双向**（R82）：`stamps.count > fractions.count` 只拦"少一根"，
不拦"多一根"，而"多一根"恰恰是串卷的形状。换成 `== fractions.count + 1` 之后
M443 一挪就两条同时红。**一条只在一个方向上生效的守卫等于没有守卫** —— 与 U-150、U-151
（分类器只认它见过的形状）是同一族，只是这次是索引边界。

U-158 是**崩掉的用例与没轮到的用例，不能都算『没跑』，也不能都算『红』**（R82）：
M443 让真值表那一格越界 `Fatal error`，整个测试进程带走 ⇒ 那条用例既无 `failed` 也无 `passed`，
旧分类器归成 `absent` ⇒ 电池报 `ESCAPED 红的不是预期那几条`，而真相是这一刀抓得**最狠**。
⇒ 分类器现在认两种新形状，归因依据必须是**这条用例自己开过口**：
`crashed` = 有它的 `error: -[…方法]` 行却没有结论行（算红）；`absent` = 没提过它 ⇒ 没轮到（不算红）。
`swift test` 不打 `started` 行，所以"日志里有崩溃痕迹"不能当归因依据 ——
那会把排在崩掉那条后面的每一条都签字成红，是 U-151 的镜像方向。

U-159 是**一个会抖的数被写成了常量**（R82）：同一提交的全量卷，R81 自己就留下两个版本 ——
`Executed 796 tests, with 38 tests skipped`（verify 摘要那一遍）与 `… with 45 tests skipped`
（当轮另一遍，时长不同 ⇒ 是两次跑，不是两种口径），R82 是 799 / 40。
差集是五条 `UICaptureTests`，它们 skip 时台账上看不见、跑过之后也是绿的 ⇒
**"判据今天有没有跑"这件事没人审计**。⇒ BACKLOG 116：这五条各打一行有名字的 `*_NOT_RUN` 读数。
本轮**不给原因**：第一版怀疑是变异电池的临时目录串了，读源码不成立
（它们各用 `temporaryDirectory/r28-clip-<UUID>`，互不共享）—— 没量出来就别写。

'''

REPORT_MANUAL = u'''
### 批次 72 · 加载态骨架屏那条扫光（R82 交给真机的那一问）

机器已经判过的：本机 2× 那一卷 coverage **0.955**（一直在扫）、减弱动态那一档峰值 **0.000**（真的停）、
抬升 0.12 高于产品自己声明的最小可见抬升 0.08。**机器判不了的**是这三条：

72.1 载入一张需要预览的图片（或视频），停在详情区那三根灰条上**看满 3 秒**：
     ① 那条亮带是"一直在扫"还是"扫两下就停了"？（114 说 runner 上只有 2 对在变，本机是 20 对 ——
        两台机器给的到底是同一句话吗，只有眼睛能定）
     ② 亮带抬升 0.12 在你这块屏上读不读得出"在动"？会不会**太亮/太刺眼**（它只有 8pt 高，
        但它是全仓唯一一条常驻动画）？
     ③ 它有没有抢你的注意力 —— 你当时正在等的那个文件，扫光有没有让你更焦虑？
72.2 系统设置 → 辅助功能 → 显示 →「减少动态效果」打开，再走一次 72.1：
     三根灰条必须**完全静止**（机器判了峰值 0.000，这里只复核"静止的骨架"读起来仍然像"在加载"，
     而不是像"卡住了"）。

'''


def patch_manual():
    p = os.path.join(REPO, 'docs/MANUAL_TEST_v1.4.9_round3.md')
    s = read(p)
    assert u'### 批次 72' not in s, '批次 72 已经存在'
    write(p, s.rstrip('\n') + '\n' + REPORT_MANUAL)


STAGES = {
    # A 段只写"本轮做了什么"的那些台账 —— 它们不需要自评曲线的那个 n。
    'A': (patch_visual_iteration, patch_ui_audit, patch_decisions,
          patch_backlog, patch_changelog, patch_manual),
    # B 段写 STATE 与最终报告：它们要引用 `curve_from_ledger.py` 在 A 段落盘之后跑出来的那一行。
    'B': (patch_state, patch_final_report),
    'C': (lambda: fix_curve(),),
}


def fix_curve():
    real = summary('CURVE')
    for rel in ('AGENT_VISUAL_ITERATION.md', 'AGENT_STATE.md', 'AGENT_FINAL_REPORT.md'):
        p = os.path.join(REPO, rel)
        t = read(p)
        if 'CURVE_PLACEHOLDER' not in t:
            print('  %s 里没有占位符（已经换过了？）' % rel)
            continue
        write(p, t.replace('CURVE_PLACEHOLDER', real))
        print('  %s：占位符 → %s' % (rel, real))


def main():
    stage = sys.argv[1] if len(sys.argv) > 1 else 'A'
    for fn in STAGES[stage]:
        fn()
        print('已写 %s' % fn.__name__)
    print('九刀：%s' % ', '.join('%s=%s' % (t, m) for t, _, m in KNIVES))


if __name__ == '__main__':
    main()
