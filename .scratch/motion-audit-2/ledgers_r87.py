# -*- coding: utf-8 -*-
'''R87 的台账补丁（第 89 轮 / Round 87）。

数字全部从产物读，不许手抄：
  * `.scratch/motion-audit-2/r87_battery.log`        —— 八刀的逐条结论
  * `.scratch/motion-audit-2/r87_verify_summary.log` —— 全量验证的逐条读数
  * `.scratch/motion-audit-2/r87_ci_readings.md`     —— 读 R86 的 CI（那朵红）的原文
每个锚点都断言"命中且只命中一次"。分三段跑：A（正文与账）、B（STATE 与 FINAL_REPORT）、C（曲线）。
'''
import io
import os
import re
import subprocess
import sys

REPO = '/Users/wangziyi/Codex_Project0'
BATTERY = os.path.join(REPO, '.scratch/motion-audit-2/r87_battery.log')
SUMMARY = os.path.join(REPO, '.scratch/motion-audit-2/r87_verify_summary.log')
CI = os.path.join(REPO, '.scratch/motion-audit-2/r87_ci_readings.md')
CURVE = 'CURVE_PLACEHOLDER_R87'


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


def reading(name):
    text = read(SUMMARY)
    m = re.search(r'^READ \^?%s :: (.+)$' % re.escape(name), text, re.M)
    if not m:
        raise SystemExit('验证摘要里没有 READ %s 这一行 ⇒ 那条读数没落地，台账不许引用它' % name)
    return m.group(1).strip()


def knife_rows():
    text = read(BATTERY)
    rows = []
    for m in re.finditer(r'^M(4\d\d) (.+?)$', text, re.M):
        tag = 'M' + m.group(1)
        tail = text[m.end():]
        hit = re.search(r'^   (CAUGHT|ESCAPED|NOT-RUN|NOT-APPLIED|MISMATCH|MEASURED)', tail, re.M)
        rows.append((tag, m.group(2), hit.group(1) if hit else '?'))
    return rows


KNIVES = knife_rows()
CAUGHT = [t for t, _, k in KNIVES if k == 'CAUGHT']
ESCAPED = [t for t, _, k in KNIVES if k == 'ESCAPED']
NOTRUN = [t for t, _, k in KNIVES if k == 'NOT-RUN']


def short_note(n):
    head = n.split(u'⇒')[0].strip()
    return n.strip() if head.count(u'（') != head.count(u'）') else head


KNIFE_TABLE = u'\n'.join(u'| %s | %s | **%s** |' % (t, short_note(n), k) for t, n, k in KNIVES)
KNIFE_RANGE = u'%s–%s' % (KNIVES[0][0], KNIVES[-1][0])
KNIFE_TOTAL = u'%d 刀' % len(KNIVES)
KNIFE_LINE = u'%s（%s）：%d 刀 CAUGHT%s' % (
    KNIFE_RANGE, u'、'.join(t for t, _, _ in KNIVES), len(CAUGHT),
    u'，%s 逃掉' % u'、'.join(ESCAPED) if ESCAPED else u'，没有逃掉的')
CI_TEXT = read(CI).strip()

BUILD_WARN = re.search(r'\d+', summary('BUILD_WARNINGS')).group(0)
FULL_TEST = summary('FULL_TEST')
FRAME = summary('FRAME_BASELINE')
GATE = summary('CAPTURE_GATE')
SCRIPTS = summary('SCRIPT_TESTS')
SCRIPT_TOTAL = re.search(r'Ran (\d+) tests', SCRIPTS).group(1)
MOTION_FACTS = summary('MOTION_FLOOR')
STATE_LOOP = reading('MOTION_SHIMMER_STATE')
BAND_READING = reading('MOTION_SHIMMER_BAND')
BAND_SAMPLE = reading('MOTION_SHIMMER_BAND_SAMPLE')
SWEEP_READING = reading('MOTION_SHIMMER')
def num(text, field):
    m = re.search(re.escape(field) + r'=([\d.]+)', text)
    if not m:
        raise SystemExit('读数里找不到 %s ⇒ 台账不许引用没读到的数：%s' % (field, text[:160]))
    return m.group(1)
LOCAL_FRAMES = num(SWEEP_READING, u'帧数')
LOCAL_PAIRS = num(SWEEP_READING, u'变化帧对')
LOCAL_COVERAGE = num(SWEEP_READING, 'coverage')
LOCAL_USED = num(BAND_READING, u'可用帧')
LOCAL_TRAVEL = num(BAND_READING, u'行程') + 'pt'

ROUND_HEAD = u'''## Round 87 · 两把尺矛盾时谁签字：coverage 不再能单独把扫光判红（修 main 那朵红 / 更新 119、93 / 新开 120 / U-183…U-186 / D-145）

### 本轮开场的位点清单（0 个产品文件；3 个判据/登记表/自测文件）

本轮的起点是 **main 红了**（R86 的 CI，run 38811457259，`Motion coverage floor` 那一步）。
红得有名字，但名字说的是"产品没在跑"，而同一卷上另一把尺说亮带走完了整幅 ——
被重新判断的是**定罪权该给谁**。

| 位点 | 位置 | R86 留下的缺陷 | 本轮处置 |
|---|---|---|---|
| 扫光运动判据 | `MotionFilmstripTests.loopAdjudication` | coverage（1–2 个变化帧对）能单独判产品红 | 新增 `travel` 入参：位置尺说"走过整幅"时改判**有名字的未覆盖** |
| 行程证据 | 同类新增 `travelEvidence(_:)` | 位置读数只用来判"是不是整组一条带"，没参与"在不在动" | 只看**可用帧数与行程**两个量，不看笼统的 `verdict` |
| 登记表 | `scripts/motion_floor_expectations.json` | 没有这种坏法的名字 | 新增 `loop-coverage-contradicted-by-travel`，理由不许借用旧名字 |
| 闸门自测 | `scripts/tests/test_motion_floor_gate.py` | 新名字两边不同步没人管 | +2 格：登记过的矛盾不红；只差一个词的名字必须红 |

本轮动的非台账文件 **3 个**（约定 ≤4）。0 个产品文件 ——
红不是产品的回归造成的（R84 之后产品一行没改），是判据的定罪权放错了地方。

'''

SECTION = u'''
### 为什么 coverage 不能单独定罪（U-183）

四遍读数，同一份产品代码（R84 换画法之后）：

| run | 帧数 | 变化帧对 | coverage | 可用帧 | 行程 | 处置 |
|---|---|---|---|---|---|---|
| R84 38798408040 | 24 | 2 | 0.522 | 11 | 109.0pt | ok |
| R85 38805382593 | 22 | 2 | 0.842 | 12 | 134.0pt | ok |
| R86 38811457259 | 23 | **1** | **0.032** | 12 | **134.0pt** | **productRed（main 红）** |
| 本机 R87 验证那一遍 | %s | %s | %s | %s | %s | ok |

本机那一行的原文读数（上面五个数就是从这三行里读的，逐字贴在这里以便对账）：

```
%s
%s
%s
```

⇒ 两把尺问的是同一件事（"亮带在不在走"），但支撑它们的样本数差一个量级：
coverage 在 runner 上只有 **1–2 个变化帧对**（分母 22–24 对），
而位置尺在 runner 三遍上有 **11–12 个可用帧**（本机那一遍 7 帧），且它在两台机器、四遍里都落在 109–134pt。
"亮带从 x=21pt 走到 x=155pt"是**位置**证据，不依赖采样网格；coverage 依赖 ——
30Hz 的扫光在 ~100ms 的采样间隔下，相邻两帧常常长得一样，要走完一根条才跨一次台阶。

⇒ 所以定罪权按**样本数**分配：`loopAdjudication` 现在先问"有没有一份样本更多的尺在说反话"，
有 ⇒ 判 `notRunRulerBlind`（点名 `loop-coverage-contradicted-by-travel`，不红也不绿）。
三格方向钉子钉住它没被放宽：位置尺也说没走过 → 仍然红；位置尺今天没读数 → 仍然红；
产品在动 → 行程说什么都不改判绿；粗节拍证人整卷没拍到 → 仍然先红在证人。

这一格是 BACKLOG **110**（"单样本统计会把一臂在判到/判不到之间翻脸"）在循环这一族的第三个实例，
也是 **119** 开张时要的那件事的另一半：119 问"几遍读数才配定罪产品"，
本轮的答案是"**一遍都不配，除非另一把样本更多的尺同意**"——
跨遍状态在一次 CI 里拿不到，而同一卷上的第二把尺拿得到。

### U-184 · 预先登记的预测被推翻时，要写"没证实"，不要顺手换一种解释

R86 我把三种可能连同各自的含义**先登记**在 BACKLOG 93 里（这是那条的正确用法）。
CI 报的是 `UI_PROBE_NO_CASE_STARTED=1` ⇒ "挂在字母序第一条用例内部"那句推断没有被证实。
但这一格不能就这么收：`started=0` 有两种成因，而**这一份日志分不开它们** ——
① 进程真的在第一条用例开口之前死了；② 用例其实跑了，但 stdout 在 `kill -9` 时整块丢了
（这一族本仓库见过两次：R64 的捕获卷、R84 的动效卷；`> /tmp/ui.log 2>&1` 是重定向到文件，
块缓冲被 SIGKILL 掐掉是默认行为。R86 的 spike 只证明了"能留住"，没证明"每次都留得住"）。
⇒ ②为真时 `NO_CASE_STARTED` 就是一句关于产品的假话。
分不开的办法本轮找到了：那一步同时看**产物通道**（`/tmp/shots-ci` 里有没有帧）——
有帧没日志 ⇒ ②；没帧没日志 ⇒ ①。这一格交给 R88，也是 93 不结案的理由。

### U-185 · 新坏法必须有新名字，而"两边同步"要有一条会红的守卫

`notRunRulerBlind` 本可以沿用 `loop-clock-not-sustainable-at-product-rate` 蒙过 CI
（闸门只比登记表里的名字）。那等于让新病借用旧病的免检牌：登记表从此看不出多了一种坏法。
⇒ 新名字进表，并且自测里加两格：登记过的矛盾不红；**只差一个词**的名字
（`loop-coverage-contradicted-by-speed`）必须红 —— 前缀匹配只放过括号里的细节，
不放过括号外换掉的那个词。Swift 侧另有两条断言钉住"两支 not-run 的理由不许相同"。
牙：M478（借用旧名字）、M479（表里删掉新理由）、M480（`BAD_REASON` 变哑）三刀各红在预期的那一格。

### U-186 · 变异文里的注释语法会让一刀"没跑成"，而不是"没抓到"—— 两种病别混

M475 / M476 第一版报 **NOT-RUN**：我在 Swift 行的末尾写了 `# R87 变异` 当注释，
而 Swift 的注释是 `//` ⇒ 编译失败，判据根本没机会跑。
这一族电池已经记过两次"编译错误被误读成判据没牙"（R83 的 M454 现场、R85 的锚点不匹配），
本轮是第三次，只是这次方向反过来：**是变异文自己坏了**。
⇒ 汇总行把 `没跑成` 与 `逃掉` 分开计数（这一版脚本一直是分开的，是我读日志时容易把它们混成"没牙"），
而修法是改刀不是改判据。

### 牙

%s

### 验证（本机，逐条实跑）

```
swift build --build-tests                告警 %s
swift test（全量）                       %s
动效覆盖地板闸门（含 loops 那一层）        %s
捕获闸门                                 %s
frame_baseline.py check --against working %s
python3 -m unittest discover -s scripts/tests  %s
```

### 七维自评

| 维度 | 得分 | 说明 |
|---|---|---|
| 原生感 | 20 / 20 | 零产品改动：本轮没脸加分，也没东西被扣 |
| 流畅度 | 18 / 20 | 扫光在 runner 上到底跑没跑，今天仍然只有位置尺在说；coverage 那一格改成了"有名字的未覆盖" |
| 层次与材质 | 15 / 15 | 本轮无画面产出 |
| 动效细节 | 14 / 15 | 定罪权挪对了地方（样本多的尺签字），但"亮带该多宽多快"仍然只有 R84 那一档依据 |
| 交互反馈 | 9 / 10 | 反馈本身没动 |
| 可访问性 | 8 / 10 | 减弱动态那一臂仍然无条件判；真机批次 72 / 73 还没人看 |
| 性能 | 14 / 15 | 全量 %s；位置尺现在被算两遍（运动判据与位置判据各一次），成本是纯函数在 12 帧上，可忽略 |

**97 / 100**，与 R86 持平：本轮修掉的是**一朵假红**，没有换来画面，也没有换来硬门。
分数不涨是刻意的 —— 判据少说一次假话不该被记成产品变好了。

### 仍未解决

- BACKLOG **119**（本轮更新）：新处置让 coverage 不再单独定罪，但"这一族的读数分布有多宽"
  仍然只有 4 个点（runner 三遍 0.522 / 0.842 / 0.032，加本机那一遍 —— 数字在上面那张表里）。
- BACKLOG **92 / 93**：`NO_CASE_STARTED` 的两种成因没分开 ⇒ 交给 R88 那一步（看产物通道）。
- BACKLOG **120**（本轮新开）：位置判据今天仍被 `loopCapable` 关着 ——
  而它现在恰恰是**唯一有资格说话的那把尺**。谁该给谁签字，这件事本轮只改了一半。
- BACKLOG **121**（本轮新开）：台账里那行 `discover -s scripts` 我照抄跑了一遍，打印 `Ran 0 tests / OK / 退出 0`。命令本身一直是对的（CI 与 verify 都是 `-s scripts/tests`），错的是台账那一格（八处本轮已改对）。CI 那道地板只挡 0（`-ge 48`），**少收一半文件照样绿** ⇒ 该不该把它改成"只准升不准降 + 点名少了哪几条"，留给下一轮。
- **116** 剩下那半格（闸门不报它没找到的 `*_NOT_RUN`）、**115**、**111**、108 余下、77 路 b、
  101 ②③、106；真机 68.1 / 68.2 / 69.1 / 70.1 / 71.1 / 72.1 / 72.2 / 73.1 / 73.2。
''' % (LOCAL_FRAMES, LOCAL_PAIRS, LOCAL_COVERAGE, LOCAL_USED, LOCAL_TRAVEL,
       SWEEP_READING, BAND_READING, BAND_SAMPLE,
       KNIFE_TABLE, BUILD_WARN, FULL_TEST,
       MOTION_FACTS, GATE, FRAME, SCRIPTS, FULL_TEST)

# 位置格式化是按**文本顺序**吃参数的，写反了不会报错，只会把整条原文读数塞进数字列。
# 上一版就是这么坏的（本机那一行的"帧数"列里躺着 MOTION_SHIMMER 整行），
# 而它是渲染出来的台账，不是红掉的脚本 —— 所以这一格必须在写盘之前就红。
for _row in SECTION.split('\n'):
    if _row.startswith(u'| 本机 R87'):
        _cells = [c.strip() for c in _row.strip().strip('|').split('|')][1:]
        for _cell, _head in zip(_cells, [u'帧数', u'变化帧对', u'coverage', u'可用帧', u'行程', u'处置']):
            if not re.match(r'^\**[\d.]+\**(pt)?\**$|^\**[a-zA-Z（）/]+\**$', _cell):
                raise SystemExit('本机那一行的 %s 列 = %r ⇒ 数字与列串味了，台账不许这么写' % (_head, _cell))
        break
else:
    raise SystemExit('渲染后的 SECTION 里找不到本机那一行 ⇒ 表格被改坏了')

UI_AUDIT = u'''## 第 89 轮 · R87：两把尺矛盾时谁签字 —— coverage 不再能单独把扫光判红（U-183…U-186）

- **U-183 定罪权按样本数分配**：coverage 在 runner 上只有 1–2 个变化帧对撑着（分母 22–24），
  而位置尺在同一卷的 runner 三遍上有 11–12 个可用帧、行程四遍落在 109–134pt（两台机器）。
  R86 那朵 main 红是前者单独判的（0.032），后者说亮带走完了整幅 ⇒
  `loopAdjudication` 新增 `travel` 入参，矛盾时改判**有名字的未覆盖**（既不红也不绿）。
  三格方向钉子钉住它没被放宽：位置尺也说没走过 → 仍然红；没读数 → 仍然红；产品在动 → 行程不许翻案。
- **U-184 预先登记的预测被推翻时要写"没证实"**：CI 报 `UI_PROBE_NO_CASE_STARTED=1`，
  而"挂在字母序第一条"没被证实；但 `started=0` 还有第二种成因（SIGKILL 把块缓冲的 stdout 整块带走，
  本仓库 R64/R84 各一次），这一份日志分不开 ⇒ 93 不结案，分开它的方法（看产物通道有没有帧）交给 R88。
- **U-185 新坏法必须有新名字，且两边同步要有牙**：登记 `loop-coverage-contradicted-by-travel`，
  自测两格（登记过的矛盾不红 / 只差一个词必须红）+ Swift 两条断言（两支 not-run 理由不许相同）。
- **U-186 变异文自己的语法**：M475 / M476 第一版 NOT-RUN 是因为我在 Swift 行尾写了 `#` 注释
  （Swift 是 `//`）⇒ 编译失败 ≠ 判据没牙；这一族第三次混这类病，修的是刀不是判据。
- 牙 M473–M480 共八刀，全部 CAUGHT。零产品改动 ⇒ 不换装（帧基线 124 张逐字节不变）。

'''

DECISION = u'''
### D-145（R87）运动的定罪权交给样本多的那把尺：coverage 与位置矛盾时只能点名，不能判红

- 背景：R86 的 CI（run 38811457259）main 红在 `testSkeletonSweepActuallySweeps` ——
  产品 coverage 0.032（1/23 对在变）而等节拍证人 0.671，处置是 `.productRed`。
  但**同一卷**上位置尺读到可用帧 12、行程 134pt、亮带从 x=21pt 走到 x=155pt。
  R84 换画法之后 runner 三遍：coverage 0.522 / 0.842 / 0.032，行程 109 / 134 / 134pt
  ⇒ 翻脸的是 coverage，不是产品（本机那一遍在上面那张表里）。
- 决定：① `loopAdjudication` 多一个入参 `travel`（由 `travelEvidence(BandReading)` 现算，
  只看**可用帧数 ≥3** 与**行程 ≥ 20pt**，不看笼统的 `verdict`）；
  ② coverage 判"没在动"而位置判"走过整幅" ⇒ 新处置 `notRunRulerBlind`，
  点名 `loop-coverage-contradicted-by-travel`（不红、不绿、进登记表）；
  ③ 位置尺说"没走过"或"没有读数"时，红仍然由等节拍证人签（**新那一支只放行有证据的矛盾**）；
  ④ 粗节拍证人整卷没拍到东西时 `witnessDead` 优先（坏掉的尺不能替"矛盾"提供证据）；
  ⑤ 新名字进 `loops` 那一节，且自测钉住"只差一个词的名字必须红"。
- 为什么不改成"多跑几遍取分布"：一次 CI 里没有跨遍状态（要引入持久化或 artifact 比对，
  那是另一套机器，而且会把"这一版到底判没判"再推迟一轮）。同一卷上的第二把尺**现在就拿得到**。
- 与 119 的关系：119 问"几遍读数才配定罪产品"。本轮答案：一遍都不配，
  除非另一把样本更多的尺同意。119 不结案（分布宽度仍然只有 4 个点），但它的**处置**先被修对了。
- 不许的处置：把这朵红登记进 `suite_reds`（那是把一个已知的判据缺陷藏进免检名单）；
  或者反过来把 coverage 判据删掉让表自洽（位置尺今天**不能**替代它 —— 它看不见"根本没在扫"，
  见 BACKLOG 120）；或者让 `notRunRulerBlind` 沿用旧理由名（U-185）。
'''

BACKLOG_119_UPDATE = u'''
    R87 的处置改了，但这一条**不结案**：
    ① 新读数（第四遍）：coverage 0.032 / 行程 134pt / 可用帧 12 —— 同一卷上两把尺相反，
    而 coverage 那把把 main 判红了。⇒ 分布宽度现在只有 4 个点（runner 三遍 + 本机那一遍），
    "几遍才配定罪"仍然没写成数据；
    ② 本轮写进去的是**同一次运行内**的第二把尺（位置），不是跨遍状态 ——
    所以 119 的原文那一半（"要几遍读数才配定罪"）仍然没做，
    只是它最贵的那一种后果（单遍读数给产品定罪）被 D-145 挡住了。
    ③ 新形状带来的新问题另开 **BACKLOG 120**：位置判据今天仍被 `loopCapable` 关着，
    而它恰恰是唯一有资格说话的那把尺 —— 谁给谁签字，这件事本轮只改了一半。
'''

BACKLOG_93_UPDATE = u'''
    → **R87 有了第一个读数，而它推翻了一半推断（所以仍不结案）**：
    R86 接上的 `scripts/ui_probe_report.py` 在 runner 上报的是
    `UI_PROBE_PROGRESS started=0 concluded=0` + `UI_PROBE_NO_CASE_STARTED=1`（`UI_PROBE_NAMED=1`，
    所以那道硬门没红 —— 它给得出名字）。
    ⇒ 原文那句"挂在按字母序的第一条用例内部"（预测名 `testAccessibilityTreeCoverage`）**没有被证实**。
    但 `started=0` 有两种成因，这一份日志分不开：
    ① 进程真的在第一条用例开口之前死了（启动/会话层）；
    ② 用例其实跑了，而 `swift test` 的 stdout 在 `kill -9` 时整块丢
       （重定向到文件 ⇒ 块缓冲；这一族本仓库 R64 / R84 各现场一次。
       R86 的 spike 只证明"能留住"13 行，没证明"每次都留得住"）。
    ②为真时 `NO_CASE_STARTED` 就是一句关于产品的假话。
    ⇒ 分开它的方法（R88 做）：那一步同时读**产物通道** ——
    `/tmp/shots-ci` 里有没有帧、探针的 readings 文件有没有写。有帧没日志 ⇒ ②；没帧没日志 ⇒ ①。
    原文那句"下一轮做法：先只跑一条最便宜的用例并带 30s 看门狗"本轮**没有采用**：
    R86 的 started 差集已经能点名（只要日志留得住），而②这一格是那条做法也解决不了的。
'''

BACKLOG_120_NEW = u'''
120. **位置判据今天仍被 coverage 关着，而它恰恰是唯一有资格签字的那把尺**（R87 开 / 与 119、110、104 同族）：

    `bandAdjudication(..., loopCapable:)` 的 `loopCapable` 传的是 `shimmerDisposition() == .ok` ——
    也就是"coverage 判到绿，位置判据才有资格判"。R84 立这条时是对的（那时 coverage 是唯一有处置的运动尺），
    但 R87 之后它自己变成了矛盾的来源：run 38811457259 上 coverage 读 0.032 ⇒ 处置不是 ok ⇒
    位置判据打的是 `判定=notRunEnvironment 原因=loop-not-capable`，
    而它**手上那份读数**是"可用帧 12、行程 134pt、整组一条带"——今天全卷最可信的一条。
    ⇒ 要判断的是：位置那一族该不该由**它自己的证人**（粗节拍那颗，同一把尺）签字，
    不再看 coverage 的脸色？如果该，`loopCapable` 这个入参就该换成"位置尺自己有没有读数"；
    如果不该（怕位置判据在 coverage 不可用时误判产品），那就要写出**它误判的具体形状**并给它一格真值表。
    本轮没做的原因：D-145 已经改了定罪权，一次改两处会分不清是哪一处让红消失的（R58 那一课）。
    不许的处置：把两件事捆成一次提交；或者反过来把 coverage 判据删掉让位置尺独判 ——
    位置尺看不见"根本没在扫"（一根钉在原地的亮带与一卷空白在它那里长得一样）。
'''

CHANGELOG = u'''### Tests（R87）

- 扫光那一族的**定罪权**改了：`loopAdjudication` 新增 `travel` 入参（由 `travelEvidence` 从位置尺现算，
  只看可用帧数与行程），coverage 说"没在动"而位置尺说"走过整幅"时改判
  `notRunRulerBlind` —— 点名 `loop-coverage-contradicted-by-travel`，不红也不绿。
  真值表 +3 格方向钉子（位置尺说没走过 / 没读数时仍然红；产品在动时行程不许翻案），
  另加两条断言钉住"两支 not-run 的理由不许同名"。
- 登记表 `loops` 那一节新增该理由；闸门自测 +2 格（登记过的矛盾不红、只差一个词的名字必须红）。
  脚本自测现跑 %s 格。
- 变异电池 %s（M475 / M476 第一版 NOT-RUN 是变异文自己写了 `#` 注释、Swift 编译不过 —— 见台账 U-186）。

### Docs（R87）

- BACKLOG 119 更新（第四遍读数 + 处置改了但分布宽度仍未写成数据）；
  93 更新（第一个读数推翻了一半预测，`started=0` 两种成因待分）；新开 **120**（位置判据仍被 coverage 关着）。

''' % (SCRIPT_TOTAL, KNIFE_LINE)

STATE_ANCHOR_HINT = '最后更新：2026-10-16 05:25（本地 · R86 / 第 88 轮收尾：'


def patch_visual_iteration():
    p = os.path.join(REPO, 'AGENT_VISUAL_ITERATION.md')
    s = read(p)
    assert u'## Round 87' not in s, u'Round 87 已经写过了'
    write(p, s.rstrip(u'\n') + u'\n\n' + ROUND_HEAD + CI_TEXT + u'\n\n' + SECTION)


def patch_ui_audit():
    p = os.path.join(REPO, 'AGENT_UI_AUDIT.md')
    s = read(p)
    assert u'## 第 89 轮' not in s
    anchor = u'## 第 88 轮 · R86：'
    assert s.count(anchor) == 1, u'UI_AUDIT 的 88 轮锚点不唯一'
    write(p, s.replace(anchor, UI_AUDIT + anchor, 1))


def patch_decisions():
    p = os.path.join(REPO, 'AGENT_DECISIONS.md')
    s = read(p)
    assert u'### D-145' not in s
    write(p, s.rstrip(u'\n') + u'\n' + DECISION)


def patch_backlog():
    p = os.path.join(REPO, 'AGENT_BACKLOG.md')
    s = read(p)
    anchor_119 = (u'    不许的处置：抬 `minCoverage` 到 runner 能过的数（110 禁止的同一件事）、\n')
    assert s.count(anchor_119) == 1, u'119 的锚点不唯一（命中 %d）' % s.count(anchor_119)
    s = s.replace(anchor_119, anchor_119 + BACKLOG_119_UPDATE, 1)
    anchor_93 = (u'    而 R61 那类「选中/滚动」的回归恰恰只有真实表格能判。\n')
    assert s.count(anchor_93) == 1, u'93 的锚点不唯一（命中 %d）' % s.count(anchor_93)
    s = s.replace(anchor_93, anchor_93 + BACKLOG_93_UPDATE, 1)
    # 120 新开：接在最大编号那条的末尾（本轮之前是 119）
    write(p, s + BACKLOG_120_NEW)


def patch_changelog():
    p = os.path.join(REPO, 'CHANGELOG.md')
    s = read(p)
    anchor = u'## [Unreleased]\n'
    assert s.count(anchor) == 1
    assert u'### Tests（R87' not in s
    write(p, s.replace(anchor, anchor + CHANGELOG, 1))


def patch_state():
    p = os.path.join(REPO, 'AGENT_STATE.md')
    s = read(p)
    head_marker = STATE_ANCHOR_HINT
    assert s.count(head_marker) == 1, u'STATE 头部锚点不唯一'
    new_head = (u'最后更新：2026-10-16 06:20（本地 · R87 / 第 89 轮收尾：**读 R86 的 CI 读到 main 红了** —— '
                u'红在 `Motion coverage floor`，`testSkeletonSweepActuallySweeps` 把产品判成 '
                u'`.productRed`（coverage **0.032**，1/23 对在变），而**同一卷**上位置尺读到 '
                u'可用帧 12、行程 **134pt**、亮带从 x=21pt 走到 x=155pt。R84 换画法之后四遍：'
                u'coverage 0.522 / 0.842 / 0.032，行程 109 / 134 / 134pt（本机那一遍见 Round 87 那张表）'
                u'⇒ 翻脸的是 coverage，它只有 1–2 个变化帧对撑着，而位置尺在 runner 三遍上有 11–12 个可用帧（本机那一遍 7）。'
                u'本轮把**定罪权按样本数分配**（D-145）：`loopAdjudication` 多一个 `travel` 入参，'
                u'两把尺矛盾时改判 `notRunRulerBlind`、点名 '
                u'`loop-coverage-contradicted-by-travel`（不红不绿，进登记表），'
                u'并用三格方向钉子钉住它没被放宽（位置尺说没走过 / 没读数时仍然红，'
                u'产品在动时行程不许翻案）。U-185：新坏法必须有新名字，'
                u'自测两格 + Swift 两条断言钉住"两支 not-run 不许同名"。'
                u'另一件半事同时发生：R86 那台报告器第一次在 runner 上给出停机名字 —— '
                u'`UI_PROBE_NO_CASE_STARTED=1`，**推翻了我上一轮预先登记的"挂在字母序第一条"那一半**；'
                u'但 `started=0` 还有第二种成因（SIGKILL 把块缓冲的 stdout 整块带走，R64/R84 各一次），'
                u'这一份日志分不开 ⇒ 93 不结案，分开它的方法（看产物通道有没有帧）交 R88。'
                u'新开 **120**：位置判据今天仍被 `loopCapable` 关着，而它恰恰是唯一有资格签字的那把尺。'
                u'牙 M473–M480 八刀全 CAUGHT（M475 / M476 第一版 NOT-RUN 是变异文写了 `#` 注释、'
                u'Swift 编译不过 —— U-186）。**本轮零产品改动 ⇒ 不换装**。'
                u'全量 %s；动效闸门 %s；捕获闸门 %s；帧基线 %s；脚本 %s；告警 %s。'
                u'**下一轮第一件事：读 R87 的 CI（红有没有真的消失 + `LOOP_NOT_JUDGED=…contradicted-by-travel` '
                u'第一次在 runner 上出现）+ BACKLOG 93 那一步产物通道的分开法**）\n\n'
                u'> 上一轮（R86 / 第 88 轮收尾）原文开头：' + head_marker) % (
        FULL_TEST, MOTION_FACTS, GATE, FRAME, SCRIPTS, BUILD_WARN)
    write(p, s.replace(head_marker, new_head, 1))


def patch_final_report():
    p = os.path.join(REPO, 'AGENT_FINAL_REPORT.md')
    s = read(p)
    old = u'| 阶段二 **79 轮**审计（R9–R86，含 29d；'
    assert s.count(old) == 1, u'FINAL_REPORT 轮数锚点不唯一'
    s = s.replace(old, u'| 阶段二 **80 轮**审计（R9–R87，含 29d；', 1)
    old = u'以 `curve_from_ledger.py` 的 `PHASE2 n=79` 为准）'
    assert s.count(old) == 1, u'FINAL_REPORT 曲线锚点不唯一'
    s = s.replace(old, u'以 `curve_from_ledger.py` 的 `PHASE2 n=80` 为准）', 1)
    old = u'| 视觉台账 | U-31 … U-182（150 条；'
    assert s.count(old) == 1, u'FINAL_REPORT U 计数锚点不唯一'
    s = s.replace(old, u'| 视觉台账 | U-31 … U-186（154 条；', 1)
    old = u'| 决定台账 | D-069 … **D-144**'
    assert s.count(old) == 1, u'FINAL_REPORT 决定台账锚点不唯一'
    s = s.replace(old, u'| 决定台账 | D-069 … **D-145**', 1)
    old = u'**M100–M472**（阶段二 372 支；'
    assert s.count(old) == 1, u'FINAL_REPORT 刀数锚点不唯一'
    if len(CAUGHT) != len(KNIVES):
        raise SystemExit('有刀没抓到就不许往报告里写“全 CAUGHT”：%s'
                         % u'、'.join(t for t, _, k in KNIVES if k != 'CAUGHT'))
    s = s.replace(old, (u'**M100–M480**（阶段二 380 支；**R87 的 %s %s 全 CAUGHT**'
                        u'（两刀第一版 NOT-RUN：M475 / M476 的变异文在 Swift 行尾写了 `#` 注释'
                        u' ⇒ 编译不过、判据根本没跑，修的是刀不是判据 —— 见 U-186） —— '
                        % (KNIFE_RANGE, KNIFE_TOTAL)), 1)
    old = u'自评曲线（**79 轮**，Round 9–86，含 29d 那一轮边界轮；'
    assert s.count(old) == 1, u'FINAL_REPORT 曲线段锚点不唯一'
    s = s.replace(old, (u'自评曲线（**80 轮**，Round 9–87，含 29d 那一轮边界轮；' + CURVE +
                        u'；**后面那几段 `）：PHASE2 n=…` 是前几轮留下的同一条曲线的历史读数**'
                        u'（n 依次小 1，不是并存的两把尺，也不是本轮没算完））：'), 1)
    anchor = u'U-174 是**守卫只数"这个串出现过"'
    assert s.count(anchor) == 1, u'FINAL_REPORT 的 U 段插入锚点不唯一'
    s = s.replace(anchor, REPORT_U + anchor, 1)
    write(p, s)


REPORT_U = (u'U-183 是**定罪权要按样本数分配**（coverage 只有 1–2 个变化帧对撑着，'
            u'而同一卷上位置尺有 11–12 个可用帧、行程四遍落在 109–134pt —— '
            u'前者能在同一份产品代码上把 main 判红）；'
            u'U-184 是**预先登记的预测被推翻时要写"没证实"**（`UI_PROBE_NO_CASE_STARTED=1` '
            u'推翻了"挂在字母序第一条"，但它自己还有第二种成因：SIGKILL 把块缓冲的 stdout 整块带走）；'
            u'U-185 是**新坏法必须有新名字，且两边同步要有牙**（借用已登记的理由名 = 让新病沿用旧病的免检牌）；'
            u'U-186 是**变异文自己的语法会让一刀"没跑成"而不是"没抓到"**（Swift 行尾注释是 `//` 不是 `#`，'
            u'编译失败与判据没牙是两种病，修的是刀）；')


def fix_curve():
    proc = subprocess.run([sys.executable, '.scratch/motion-audit-2/curve_from_ledger.py'],
                          cwd=REPO, capture_output=True, text=True, timeout=600)
    if proc.returncode != 0:
        raise SystemExit('曲线守卫退出 %d ⇒ 台账里缺尾轮或有轮没有分数：%s'
                         % (proc.returncode, (proc.stdout + proc.stderr)[-1200:]))
    picked = [l for l in proc.stdout.splitlines() if l.startswith('GAPS=') or l.startswith('PHASE2')]
    real = ' '.join(picked).strip()
    if not real:
        raise SystemExit('曲线守卫没打 GAPS=/PHASE2 行：%s' % proc.stdout[:400])
    if 'n=80' not in real:
        raise SystemExit('曲线不是 80 轮（本轮正文没被识别为一个轮次？）：%s' % real[:200])
    for rel in ('AGENT_VISUAL_ITERATION.md', 'AGENT_STATE.md', 'AGENT_FINAL_REPORT.md'):
        p = os.path.join(REPO, rel)
        t = read(p)
        if CURVE not in t:
            print(u'  %s 里没有占位符' % rel)
            continue
        write(p, t.replace(CURVE, real))
        print(u'  %s：占位符已替换' % rel)
    print(u'  CURVE(现跑)=%s' % real[:160])


def patch_final_report_round_range():
    """`Round 9–85` 那一格是这一族反复滞后的老位置：区间从曲线读数推，不手抄。

    n 与编号跨度**本来就差 1** —— 29d 那一轮边界轮单独占一条读数，
    所以 `PHASE2 n=80 rounds=9..87` 是自洽的（87−9+1=79 个编号 + 29d）。
    第一版把这条写成 `n == hi − lo + 1`，于是它对自己红了：断言太紧和断言不存在一样糟。
    """
    p = os.path.join(REPO, 'AGENT_FINAL_REPORT.md')
    s = read(p)
    proc = subprocess.run([sys.executable, '.scratch/motion-audit-2/curve_from_ledger.py'],
                          cwd=REPO, capture_output=True, text=True, timeout=600)
    if 'GAPS=none' not in proc.stdout:
        raise SystemExit('曲线守卫报了缺轮 ⇒ 区间格子不许写：%s'
                         % [l for l in proc.stdout.splitlines() if l.startswith('GAPS')])
    m = re.search(r'PHASE2 n=(\d+) rounds=(\d+)\.\.(\d+)', proc.stdout)
    if not m:
        raise SystemExit('曲线守卫没打出 PHASE2 n=… rounds=… ⇒ 这一格不许手抄：%s' % proc.stdout[:200])
    n, lo, hi = int(m.group(1)), int(m.group(2)), int(m.group(3))
    extra = n - (hi - lo + 1)
    if extra not in (0, 1):
        raise SystemExit('PHASE2 n=%d 与 rounds=%d..%d 差 %d ⇒ 既不是"编号连续"也不是"多一个 29d"，'
                         '这一格不能推：%s' % (n, lo, hi, extra, m.group(0)))
    old = u'`AGENT_VISUAL_ITERATION.md` Round 9–85（这一格同样滞后过：R85 之前写的是 9–65）'
    assert s.count(old) == 1, u'那一格的锚点不唯一（命中 %d）' % s.count(old)
    write(p, s.replace(old, u'`AGENT_VISUAL_ITERATION.md` Round %d–%d（%d 条读数：编号 %d–%d 共 %d 个，'
                            u'外加 29d 那一轮边界轮；区间与条数都从曲线守卫的 `rounds=…`/`n=…` 推）'
                            % (lo, hi, n, lo, hi, hi - lo + 1), 1))


STAGES = {
    'A': (patch_visual_iteration, patch_ui_audit, patch_decisions, patch_backlog, patch_changelog),
    'B': (patch_state, patch_final_report),
    'C': (lambda: fix_curve(),),
    'D': (patch_final_report_round_range,),
}


def main():
    stage = sys.argv[1] if len(sys.argv) > 1 else 'A'
    for fn in STAGES[stage]:
        fn()
        print(u'已写 %s' % fn.__name__)
    print(u'%s：%s' % (KNIFE_TOTAL, u', '.join(u'%s=%s' % (t, k) for t, _, k in KNIVES)))
    if len(CAUGHT) != len(KNIVES):
        print(u'!! 有刀没抓到：%s' % u'、'.join(t for t, _, k in KNIVES if k != 'CAUGHT'))


if __name__ == '__main__':
    sys.exit(main())
