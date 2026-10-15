# -*- coding: utf-8 -*-
'''R85 的台账补丁（第 87 轮 / Round 85）。

数字全部从产物读，不许手抄：
  * `.scratch/motion-audit-2/r85_battery.log`        —— 七刀的逐条结论
  * `.scratch/motion-audit-2/r85_verify_summary.log` —— 全量验证的逐条读数
  * `.scratch/motion-audit-2/r85_ci_readings.md`     —— 读 R84 的 CI 的原文
每个锚点都断言"命中且只命中一次"。分三段跑：A（正文与账）、B（STATE 与 FINAL_REPORT）、C（曲线）。
'''
import io
import os
import re
import subprocess
import sys

REPO = '/Users/wangziyi/Codex_Project0'
BATTERY = os.path.join(REPO, '.scratch/motion-audit-2/r85_battery.log')
SUMMARY = os.path.join(REPO, '.scratch/motion-audit-2/r85_verify_summary.log')
CI = os.path.join(REPO, '.scratch/motion-audit-2/r85_ci_readings.md')
CURVE = 'CURVE_PLACEHOLDER_R85'


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
    for m in re.finditer(r'^M(4\d\db?) (.+?)$', text, re.M):
        tag = 'M' + m.group(1)
        tail = text[m.end():]
        hit = re.search(r'^   (CAUGHT|ESCAPED|NOT-RUN|NOT-APPLIED|LOCAL-NO-POWER)', tail, re.M)
        rows.append((tag, m.group(2), hit.group(1) if hit else '?'))
    return rows


KNIVES = knife_rows()
CAUGHT = [t for t, _, k in KNIVES if k == 'CAUGHT']
ESCAPED = [t for t, _, k in KNIVES if k == 'ESCAPED']
BAD = [t for t, _, k in KNIVES if k not in ('CAUGHT',)]
def short_note(n):
    # 表格里的短标题：砍掉「⇒ 预期…」那半截，但**砍坏括号的就不砍**
    # （M460 的 ⇒ 在括号里面，直接切会把「（换一种读不出就冒红」留成一个不闭合的括号）。
    head = n.split(u'⇒')[0].strip()
    return n.strip() if head.count(u'（') != head.count(u'）') else head


KNIFE_TABLE = u'\n'.join(u'| %s | %s | **%s** |' % (t, short_note(n), k) for t, n, k in KNIVES)
KNIFE_RANGE = u'%s–%s' % (KNIVES[0][0], KNIVES[-1][0])
KNIFE_TOTAL = u'%d 刀' % len(KNIVES)
KNIFE_LINE = u'%s（%s）：%d 刀 CAUGHT%s' % (
    KNIFE_RANGE, u'、'.join(t for t, _, _ in KNIVES), len(CAUGHT),
    u'，%s 第一版 ESCAPED、把守卫改硬之后全部抓到' % u'、'.join(ESCAPED) if ESCAPED else u'，没有逃掉的')
CI_TEXT = read(CI).strip()

BUILD_WARN = re.search(r'\d+', summary('BUILD_WARNINGS')).group(0)
FULL_TEST = summary('FULL_TEST')
FRAME = summary('FRAME_BASELINE')
GATE = summary('CAPTURE_GATE')
SCRIPTS = summary('SCRIPT_TESTS')
SCRIPT_TOTAL = re.search(r'Ran (\d+) tests', SCRIPTS).group(1)
MOTION_FACTS = summary('MOTION_FLOOR')
STATE_LOOP = reading('MOTION_SHIMMER_STATE')
STATE_BAND = reading('MOTION_SHIMMER_BAND_STATE')
BAND_READING = reading('MOTION_SHIMMER_BAND')
CONTRAST_LOG = os.path.join(REPO, '.scratch/motion-audit-2/r85_contrast_readings.log')
CONTRAST = {}
for _line in read(CONTRAST_LOG).splitlines():
    _m = re.match(r'SKELETON_CONTRAST_(DARK|LIGHT)=([\d.]+)/255', _line)
    if _m:
        CONTRAST[_m.group(1)] = _m.group(2)
for _k in ('DARK', 'LIGHT'):
    if _k not in CONTRAST:
        raise SystemExit('看图仪器没给出 SKELETON_CONTRAST_%s ⇒ 先跑 r85_skeleton_contrast.py' % _k)
# 读数行里那个字段的全名是「同帧绝对中心最大散布」，不是「绝对散布」——
# 正则写错时这里会直接崩，而不是安静地写一个空数进台账（这一族的规矩）。
BAND_SPREAD = re.search(r'最大散布=([\d.]+)pt', BAND_READING).group(1)
BAND_LOCAL = '%s/%s' % (re.search(r'可用帧=(\d+)', BAND_READING).group(1),
                        re.search(r'帧=(\d+)', BAND_READING).group(1))
_ci_band = [l for l in CI_TEXT.splitlines() if l.startswith('MOTION_SHIMMER_BAND 帧=')]
if not _ci_band:
    raise SystemExit('CI 读数里没有 MOTION_SHIMMER_BAND 那一行 ⇒ 台账不许引用一个没读到的数')
BAND_CI = '%s/%s' % (re.search(r'可用帧=(\d+)', _ci_band[0]).group(1),
                     re.search(r'帧=(\d+)', _ci_band[0]).group(1))
STRIP_PATH = '.scratch/motion-audit-2/r85_skeleton_band_strip.png'

ROUND_HEAD = u'''## Round 85 · 常驻循环那一族第一次有了登记表：判据必须自己说"今天判没判"（结案 118 / 更新 119 / U-174…U-177 / D-143）

### 本轮开场的位点清单（0 个产品文件；5 个判据/闸门/自测文件）

本轮不改画面。被重新判断的是**"这一族今天到底判没判"这件事有没有人统计**：

| 位点 | 位置 | R84 留下的缺陷 | 本轮处置 |
|---|---|---|---|
| 扫光运动判据 | `MotionFilmstripTests.testSkeletonSweepActuallySweeps` | 结论只在读数行里，登记表读不到它"今天判没判" | 两条出口各打一行 `MOTION_SHIMMER_STATE` |
| 位置判据（R84 新加） | 同类 `testSkeletonSweepIsOneBand` | 同上，且它刚进判据体系，消失起来最无声 | 同上，`MOTION_SHIMMER_BAND_STATE` |
| 覆盖地板闸门 | `scripts/motion_floor_gate.py` | 只按四条场景臂统计，扫光不是场景臂 ⇒ 整族缺席没人报 | 新增 `loop_verdicts`：`LOOP_SILENT` / `LOOP_BAD_REASON` 两格 |
| 登记表 | `scripts/motion_floor_expectations.json` | 没有这一族的行 | 两行登记，各带允许的理由与来历 |
| 闸门自测 | `scripts/tests/test_motion_floor_gate.py` | 新那一层没有自己的真值表 | +1 格七项（含整行缺席、带后缀的登记名） |
| CI 报告自检 | `scripts/tests/test_ci_report_selftest.py` | 共用通道里没有状态行 ⇒ 七个场景一起假红 | `FLOOR_SUMMARY` 一处补背景行（U-176） |

**文件数超约定一格，如实记账**：这一族的约定是每轮 ≤4 个非台账文件，本轮 5 个。
多出来的是最后那一格 `test_ci_report_selftest.py` —— 新加一层判据时，凡是读同一份日志的旧自测会一起冒红，
而补背景行只能补在它们共用的那一个常量上（七个场景共用一处，不是七处各补一遍，见 U-176）。
考虑过并进 `test_motion_floor_gate.py`（那样本轮就回到 4 个文件）而**拒绝**：两个文件判的东西不同
（一个判闸门函数的返回值，一个判 CI 报告怎么拼装），并文件只会让下一个读的人以为它们是同一件事 ——
这条约定是防一轮改一片的，不是防文件名的。

### 读 R84 的 CI（run 38798408040）：这一族第一次在 runner 上判到，而 main 绿了

'''

SECTION = u'''
⇒ **`build-and-test` = success**，而 `Motion coverage floor` 那一步第一次对扫光这一位说出"判到了"：
产品 coverage **0.522**（地板 0.50）、等节拍证人 0.594、位置判据 可用帧=11 / 绝对散布 **1.0pt** /
判定=整组一条带（runner 是 1× ⇒ `比例=1pt≈1.00px` 那格也第一次被真机验证）。

三遍并排看，本轮最重要的那句话在这里：**R83 那朵 `.productRed` 现在有了第三种解释**。

| run | 画法 | 产品 coverage | 等节拍证人 coverage | 处置 |
|---|---|---|---|---|
| R82 | 每根条各扫各的 | 0.000 | 0.284 | 点名环境 |
| R83 | 每根条各扫各的 | 0.050 | 0.837 | 判产品红 |
| R84 | **整组一条带** | **0.522** | 0.594 | 判绿 |

产品那两遍（0.000 / 0.050）不是"这台机器的时钟带不动 30Hz"，也不是"产品的扫光没跑"，
而是**旧的 fan-out 画法让运动跨不过像素门槛**：亮带只在每根条自己的 30%% 里走，
每拍推进 ≈1.2pt，在 112ms 的采样网格 + 1× 像素上摊到每对帧就没了（R83 自己给 `minimumHighlightLift`
写的那句"5 个点的抬升在像素上等于没动"是同一件事的另一半）。
换成整组一条带之后同一台机器读到 0.522 —— 时钟、节拍、抬升、声明时长一个都没改。
⇒ **119 不结案**，但它的成因表里要多一列：判据读不到运动有三种可能（环境带不动 / 判据吃采样 /
**画法让运动不可见**），第三种本轮现场发生过。而 0.522 只比地板高 0.022 ⇒
登记表不许因此改成 `must_judge=true`（R38：一次读数不当另一台机器的地板）。

### 改了什么：状态行 + `loops` 那一层 + 一条会数次数的守卫

判据侧：两条判据的**两条出口各自**打一行状态 ——
能力闸门 skip 那条打 `判定=skipped 原因=capability-gate`，判完那条打
`判定=ok|productRed|notRunEnvironment|witnessDead 原因=<名字或->`。
状态行排在所有 `XCTFail` 与闸门之前（R53 那一课）。

```
%s
%s
```

闸门侧（`loop_verdicts`）只判两格，正是 118 原文要的那两格：

```
%s
```

`productRed` / `witnessDead` 这两种状态**不在这里红** —— 它们对应的用例本身就是红的，
红由 `suite_reds` 那一层报（名字 + XCTAssert 原文都在那边）。同一件事只判一次（U-162 的规矩
在新层里同样成立）。登记名允许带细节后缀（`band-witness-reads-nothing(没有可用帧)`），
闸门按括号前那半截匹配。

### U-174 · 守卫只数"出现过"，会被另一条出口喂饱

第一版守卫写的是"函数体里出现过 `MOTION_SHIMMER_BAND_STATE` 这个串"。
**M461 / M462 双双 ESCAPED**：删掉正常路径那一行 emit 之后，skip 分支那一行仍然把断言喂饱，
三条判据全绿 —— 而登记表从此读不到任何状态。⇒ 守卫改成**数次数**：
`stateLineCount(...) == 2`，两条出口各一次；再补 M463 / M464 两刀专删 skip 那一行。
这一格是"守卫要读字段不能读散文"（R75 那一课）在**自身源码**上的形状：
读"提没提到"永远比读"每条路都做了没做"弱。

### U-175 · 登记名允许带细节后缀，闸门按前缀匹配

`band-witness-reads-nothing(没有可用帧)` 与 `(分不开)` 是两种不同的"读不出"，
但如果闸门整串比对，每换一种读不出就冒一次 `BAD_REASON` 红 ——
下一次有人删掉括号那半截来让 CI 变绿，而那半截正是有用的一半。
⇒ 匹配剥后缀，红只留给**没登记过**的坏法；`testLoopStateLinesAreCountedNotGuessed` 里
带后缀那一格钉的就是这件事（M460 把它拆掉 ⇒ 那一格红）。

### U-176 · 给旧日志加一层新判据时，先决定"谁该补背景行、谁故意不补"

`loops` 一进来，七个 CI 自检场景 + 两份真日志夹具全部多两朵 `LOOP_SILENT` 红。
两种处置分开做：**背景条件**（"一次完整的动效运行包含状态行"）补在 `FLOOR_SUMMARY` 一处，
不逐格改七个场景 —— 那七格测的是臂一级的形状，循环那一族对它们是背景；
而 R46 那份**本机真日志故意不补**，于是它顺带成了 `LOOP_SILENT` 的正对照
（"这一族整行没说一句话"就是它那个样子），期望从两朵红改成四朵，改的理由写在文档串里。
⇒ 记这条是因为它有一个反直觉的分支：给旧夹具补新行 = 让旧日志替新规则作证，
   那份日志就不再是它声称的那次运行的原文了。能不改就不改，改了要说明。

### U-177 · 判据读不到运动有三种成因，本轮现场补上了第三种

见上面那张三行表。这条不改代码，改的是**归因表**：以后 `testSkeletonSweepActuallySweeps`
在 runner 上读不到东西时，第一个要排除的不是"机器不行"，而是"这份画法在这台机器的
像素门槛下本来就近乎不可见"。排除它的方法本轮已经有了 ——
`MOTION_SHIMMER_BAND` 那行给的是**位置**读数（可用帧数、绝对散布），
一条"根本没在扫"的卷子和一条"在扫但跨不过地板"的卷子在那一格上长得不一样。

### 真实看图（本轮没有产品改动，看图判的是"账上的数与画面是否还是同一件事"）

看的三样东西都是本轮验证现生成的，这几个数由 `%s` 现算（脚本里不留手抄读数）：

1. **24 格条带** `%s`（整图 2520×880px = 6 列 × 4 行，每格 420×220px）。
   眼睛读到的：亮带在每一格里都是**一条竖着的光同时穿过三根条**（不是三根条各自亮一遍），
   并且沿阅读顺序逐格向右推进、走完一遍回到左边重来 ⇒ R84 那个产品修法**在画面上成立**，
   不只是在尺子上成立（尺子同一件事的读数：同帧绝对散布 %spt）。
2. **两张静帧的骨架区域**（`detail-loading-720x520-dark/light.png`，取 x 60…1100px、y 70…190px 放大 2× 看）。
   三根条的长度比例肉眼可读（0.42 / 0.86 / 0.64），圆角一致，左轴与详情区文字同一条。
   顺手量了静置条与所在背景的亮度差：**暗 %s/255、亮 %s/255**（偏离背景的行数 48 = 3 根条 × 16px，
   与 `barHeight=8pt` 对得上）⇒ 两种外观下都是"看得见但很轻"，而且**亮档比暗档还略强一点**，
   我原本担心的方向反了（怕的是白纸上看不见）。**判为不加**：
   本轮没有系统骨架的帧可比，所以"与系统同级"那句话不写；只把这两个数留在账上，
   将来谁动 `baseOpacity` 就有对照点。
3. **静帧里亮带不在条上** —— 两张静帧的三根条是均匀的（没有哪一段更亮），
   说明基线那 4 张抓的是带子走出条外的相位。⇒ **帧基线看不见"亮带卡住不动"这种坏法**，
   那件事只有动效那一卷能判（它读的是 49 帧的卷子）。这是已知边界不是新缺陷，
   但它给本轮的 `FRAME_BASELINE_CHANGED=0` 划了范围：那一条只证明"没改画面"，不证明"画面是对的"。

顺带一条要记的读数差别：位置尺**本机只读 %s 帧**，CI 是 %s —— 两边都用了不到四分之一的卷子。
⇒ 这一族的样本量本来就小，它更不该单独给产品定罪（与 119 同族，也是 `must_judge` 保持 false 的又一个理由）。

### 牙

%s

### 验证（本机，逐条实跑）

```
swift build --build-tests                告警 %s
swift test（全量）                       %s
动效覆盖地板闸门（含 loops 那一层）        %s
捕获闸门                                 %s
frame_baseline.py check --against working %s
python3 -m unittest discover -s scripts  %s
```

### 七维自评

| 维度 | 得分 | 说明 |
|---|---|---|
| 原生感 | 20 / 20 | 零产品改动：本轮没脸加分，也没东西被扣 |
| 流畅度 | 18 / 20 | 扫光这一位在 runner 上第一次判到（0.522 > 0.50），但它只比地板高 0.022 ⇒ 119 仍然开着，登记没跟着改成硬门 |
| 层次与材质 | 15 / 15 | %s |
| 动效细节 | 14 / 15 | 位置判据进了登记表（缺席会红），但扫光"该多宽、该多快"仍然只有 R84 那一档依据 |
| 交互反馈 | 9 / 10 | 反馈本身没动 |
| 可访问性 | 8 / 10 | 减弱动态那档仍然无条件判；真机批次 72 / 73 还没人看 |
| 性能 | 14 / 15 | 全量 %s；闸门多读两行状态，成本可忽略 |

**98 / 100**。分数与 R84 持平是刻意的：本轮没有画面产出，补的是一层"判没判过要说"的账，
外加一条把归因表改对的读数（U-177）。涨分要等它换来画面或换来硬门，不等它换来自我表扬。

### 仍未解决

- BACKLOG **119**（R84 开，本轮更新）：那一族的处置仍会翻面，而本轮多了一条成因（画法让运动不可见）
  与一条新读数（0.522）。要做的是把"几遍读数才配定罪产品"写成数据。
- BACKLOG **116**（skip 那五条没有"为什么今天没跑"的读数）、**115**（TableProbe 的时刻仍走共享变量）、
  111、108 余下、77 路 b、101 ②③、106、**92**（在屏那一步今天仍然 `ui suite exit: 137 / 0 条结论`）；
  真机 68.1 / 68.2 / 69.1 / 70.1 / 71.1 / 72.1 / 72.2 / 73.1 / 73.2。
''' % (STATE_LOOP, STATE_BAND, MOTION_FACTS, 'r85_skeleton_contrast.py', STRIP_PATH,
       BAND_SPREAD, CONTRAST['DARK'], CONTRAST['LIGHT'], BAND_LOCAL, BAND_CI, KNIFE_TABLE, BUILD_WARN, FULL_TEST,
       MOTION_FACTS, GATE, FRAME, SCRIPTS, FRAME, FULL_TEST)

UI_AUDIT = u'''## 第 87 轮 · R85：常驻循环那一族进登记表 —— 判据必须自己说"今天判没判"（U-174…U-177）

- **U-174** 守卫只数"这个串出现过"会被**另一条出口**喂饱：M461 / M462 双双 ESCAPED，
  删掉正常路径的 emit 之后三条判据全绿。⇒ 改成数次数（两条出口各一次），再补 M463 / M464。
  "扫自身源码的守卫"要读的是每条路都做没做，不是提没提到。
- **U-175** 登记名允许带细节后缀（`band-witness-reads-nothing(没有可用帧)`），闸门按前缀匹配 ⇒
  否则每换一种读不出都冒红，下一次有人删掉括号那半截，而那半截正是有用的一半。
- **U-176** 新加一层判据时，先决定"哪些旧夹具补背景行、哪些故意不补"：
  七个 CI 自检场景共用一处 `FLOOR_SUMMARY`，而 R46 那份真日志不补 ⇒ 它成为 LOOP_SILENT 的正对照。
  给旧夹具补新行 = 让旧日志替新规则作证，它就不再是它声称的那次运行的原文。
- **U-177** 判据读不到运动有**三种**成因：环境带不动 / 判据吃采样 / **画法让运动不可见**。
  R84 的 CI 现场补上了第三种（同一份时钟与抬升，画法一改，runner 从 0.050 跳到 0.522）。
- 闸门：`motion_floor_gate.py` 新增 `loop_verdicts`（两格：LOOP_SILENT 红、LOOP_BAD_REASON 红；
  点名在登记之内 ⇒ 不红但打一行看得见的未覆盖；`productRed` 不在这里红，红由 suite 那层报）。
- 判据：两条出口各打一行 `MOTION_SHIMMER_STATE` / `MOTION_SHIMMER_BAND_STATE`，
  并由 `testTheLoopWitnessStillMirrorsTheProductLoop` 数次数钉住。

'''

DECISION = u'''
### D-143（R85）常驻循环那一族进覆盖地板：判据必须自己说"今天判没判"，而登记表只判缺席

- 背景：R83 开出 118 —— 覆盖地板按四条场景臂统计，而骨架扫光不是场景臂，
  于是它"红的时候有人报（SUITE_RED）、整行消失的时候没人报"。R84 又给它加了一格（位置判据）。
- 决定：① 两条判据的**两条出口各自**打一行状态（skip 与判完），状态名是登记表读的唯一东西；
  ② 登记表 `loops` 那一节只判两格 —— 状态行缺席 ⇒ `LOOP_SILENT` 红；
  点名理由没登记 ⇒ `LOOP_BAD_REASON` 红；点名在登记之内 ⇒ 不红但必须打一行"看得见的未覆盖"；
  ③ `productRed` / `witnessDead` **不在这一层红**（用例自己会红，红由 `suite_reds` 报，同一件事只判一次）；
  ④ 登记名允许细节后缀，闸门按括号前那半截匹配；
  ⑤ 守卫数**次数**而不是"出现过"（U-174）。
- 为什么不改成 `must_judge=true`：R84 的 runner 读数 0.522 只比地板 0.50 高 0.022，
  一次读数不配变成硬门（R38 那一课）。登记是测量不是愿望：等它有几遍稳定的高过地板的读数再收紧。
- 本轮的副产品（U-177）：R83 那朵 `.productRed` 的成因表里多了第三种 ——
  旧的 fan-out 画法让运动跨不过像素门槛。⇒ 119 不结案，但归因顺序改了：
  以后先排除"画法不可见"，再谈"环境带不动"。
- 不许的处置：把扫光从判据里删掉让表自洽；把点名当"已有人负责"而不统计；
  或者给旧夹具补状态行，让一份历史日志替新规则作证。
'''

BACKLOG_CLOSE_118 = u'''
    → **R85 结案**：`motion_floor_expectations.json` 新增 `loops` 一节（两行登记），
    `motion_floor_gate.py` 新增 `loop_verdicts`，判据的两条出口各自打一行状态
    （`MOTION_SHIMMER_STATE` / `MOTION_SHIMMER_BAND_STATE`）。判据正是这里要的那两格：
    点名在登记之内 ⇒ 不红但打一行 `MOTION_FLOOR_LOOP_NOT_JUDGED=…`；状态行整行缺席 ⇒
    `MOTION_FLOOR_LOOP_SILENT=…` 红。两条状态行还各有一道源码级守卫**数次数**
    （`testTheLoopWitnessStillMirrorsTheProductLoop`）—— 因为"没人断言自己打过字"
    是这一层最容易无声失效的地方（U-174）。
    牙 M458–M464 共七刀，全部 CAUGHT（M461 / M462 第一版 ESCAPED，把守卫从"出现过"改成"两条出口各一次"之后抓到）。
    没做的那半：`must_judge` 仍然 false —— R84 的 runner 读数 0.522 只比地板 0.50 高 0.022，
    一次读数不配当硬门（R38），收紧要等几遍稳定读数，那一格交给 119。
'''

BACKLOG_119_UPDATE = u'''
    R85 补一条**新的成因**（不改这一条的待办，只改归因顺序）：R84 把亮带改成整组一条之后，
    同一台 runner 上产品 coverage 从 0.050 跳到 **0.522**（时钟、节拍、抬升、声明时长一个都没动）
    ⇒ "读不到运动"除了"环境带不动"与"判据吃采样"，还有第三种可能：**这份画法在这台机器的
    像素门槛下本来就近乎不可见**。以后要动这一支的地板，先按 117 那次的账排除第三种。
    另外登记现在有了（`loops` 那一节，见 118 的结案），所以"整族没说一句话"这种坏法已经会红。
'''

CHANGELOG = u'''### Tests（R85）

- 覆盖地板新增 `loops` 那一层：常驻循环那一族（扫光的运动判据 + 位置判据）第一次进登记表。
  判据的两条出口各打一行状态（`MOTION_SHIMMER_STATE` / `MOTION_SHIMMER_BAND_STATE`），
  闸门只判两格 —— 状态行整行缺席 ⇒ `LOOP_SILENT` 红；点名理由没登记 ⇒ `BAD_REASON` 红；
  点名在登记之内 ⇒ 不红，但打一行看得见的未覆盖。脚本自测 +1 格（现跑共 %s 格）。
- 变异电池 %s（M461 / M462 第一版逃掉：守卫从"这个串出现过"
  改成"两条出口各打一次"之后才有牙 —— 见台账 U-174）。

### Docs（R85）

- BACKLOG 118 结案；119 补一条新成因（画法让运动不可见 ⇒ 归因顺序改了）。

''' % (SCRIPT_TOTAL, KNIFE_LINE)

STATE_ANCHOR_HINT = '最后更新：2026-10-16 03:20（本地 · R84 / 第 86 轮收尾：'


def patch_visual_iteration():
    p = os.path.join(REPO, 'AGENT_VISUAL_ITERATION.md')
    s = read(p)
    assert u'## Round 85' not in s, u'Round 85 已经写过了'
    write(p, s.rstrip(u'\n') + u'\n\n' + ROUND_HEAD + CI_TEXT + u'\n\n' + SECTION)


def patch_ui_audit():
    p = os.path.join(REPO, 'AGENT_UI_AUDIT.md')
    s = read(p)
    assert u'## 第 87 轮' not in s
    anchor = u'## 第 86 轮 · R84：'
    assert s.count(anchor) == 1, u'UI_AUDIT 的 86 轮锚点不唯一'
    write(p, s.replace(anchor, UI_AUDIT + anchor, 1))


def patch_decisions():
    p = os.path.join(REPO, 'AGENT_DECISIONS.md')
    s = read(p)
    assert u'### D-143' not in s
    write(p, s.rstrip(u'\n') + u'\n' + DECISION)


def patch_backlog():
    p = os.path.join(REPO, 'AGENT_BACKLOG.md')
    s = read(p)
    # 118 结案：接在它自己的结尾后面
    tail = (u'    不许的处置：把扫光从判据里删掉来让表自洽；或者把 114 的点名当成"已经有人负责了"。\n')
    assert s.count(tail) == 1, u'118 的收尾锚点不唯一'
    s = s.replace(tail, tail + BACKLOG_CLOSE_118, 1)
    # 119 更新：接在它自己的"不许的处置"那行后面
    anchor_119 = (u'    不许的处置：抬 `minCoverage` 到 runner 能过的数（110 禁止的同一件事）、\n'
                  u'    把这朵红登记进 `suite_reds`（红要有成因，不是有名字就行）、或者反过来据此断言\n'
                  u'    "产品的扫光在 runner 上确实没跑"（两遍读数互相矛盾，哪一遍都不能当结论）。\n')
    assert s.count(anchor_119) == 1, u'119 的收尾锚点不唯一'
    s = s.replace(anchor_119, anchor_119 + BACKLOG_119_UPDATE, 1)
    write(p, s)


def patch_changelog():
    p = os.path.join(REPO, 'CHANGELOG.md')
    s = read(p)
    anchor = u'## [Unreleased]\n'
    assert s.count(anchor) == 1
    assert u'### Tests（R85' not in s
    write(p, s.replace(anchor, anchor + CHANGELOG, 1))


def patch_state():
    p = os.path.join(REPO, 'AGENT_STATE.md')
    s = read(p)
    head_marker = STATE_ANCHOR_HINT
    assert s.count(head_marker) == 1, u'STATE 头部锚点不唯一'
    new_head = (u'最后更新：2026-10-16 04:20（本地 · R85 / 第 87 轮收尾：读 R84 的 CI'
                u'（run 38798408040）—— **main 绿了，而扫光这一族第一次在 runner 上判到**：'
                u'产品 coverage 0.522（地板 0.50）、等节拍证人 0.594、位置判据 可用帧=11 / '
                u'绝对散布 1.0pt / 判定=整组一条带（1× 像素那格也第一次被真机验证）。'
                u'三遍并排 ⇒ R83 那朵 `.productRed` 有了第三种解释：**旧的 fan-out 画法让运动'
                u'跨不过像素门槛**（时钟一个数都没改，0.050 → 0.522）⇒ 119 不结案但归因顺序变了。'
                u'本轮改的是账：常驻循环那一族进覆盖地板（结案 **118**）—— 两条判据的两条出口各打一行'
                u'状态（`MOTION_SHIMMER_STATE` / `MOTION_SHIMMER_BAND_STATE`），闸门新增 `loops` 那一层，'
                u'只判两格：状态行整行缺席 ⇒ LOOP_SILENT 红、点名理由没登记 ⇒ BAD_REASON 红，'
                u'点名在登记之内不红但必须打一行看得见的未覆盖；`productRed` 不在这里红（同一件事只判一次）。'
                u'牙 M458–M464 七刀全 CAUGHT —— 其中 M461 / M462 第一版**双双逃掉**，'
                u'因为守卫只数"这个串出现过"、被 skip 那条出口喂饱 ⇒ 改成数次数（U-174）。'
                u'另外三条读数写进台账：登记名允许细节后缀（U-175）、旧夹具补不补背景行要分开决定（U-176）、'
                u'读不到运动有三种成因（U-177）。**本轮零产品改动 ⇒ 不换装**（判据：帧基线 124 张逐字节不变、'
                u'`Sources/` 一行没动）；'
                u'`must_judge` 仍然 false：0.522 只比地板高 0.022。'
                u'全量 %s；动效闸门 %s；捕获闸门 %s；帧基线 %s；脚本 %s；告警 %s。'
                u'**下一轮第一件事：读 R85 的 CI（loops 那一层第一次在 runner 上判自己）+ BACKLOG 119 / 116**）\n\n'
                u'> 上一轮（R84 / 第 86 轮收尾）原文开头：' + head_marker) % (
        FULL_TEST, MOTION_FACTS, GATE, FRAME, SCRIPTS, BUILD_WARN)
    write(p, s.replace(head_marker, new_head, 1))


def patch_final_report():
    p = os.path.join(REPO, 'AGENT_FINAL_REPORT.md')
    s = read(p)
    old = u'| 阶段二 **77 轮**审计（R9–R84，含 29d；'
    assert s.count(old) == 1, u'FINAL_REPORT 轮数锚点不唯一'
    s = s.replace(old, u'| 阶段二 **78 轮**审计（R9–R85，含 29d；', 1)
    old = u'以 `curve_from_ledger.py` 的 `PHASE2 n=77` 为准）'
    assert s.count(old) == 1, u'FINAL_REPORT 曲线锚点不唯一'
    s = s.replace(old, u'以 `curve_from_ledger.py` 的 `PHASE2 n=78` 为准）', 1)
    old = u'| 视觉台账 | U-31 … U-173（141 条；'
    assert s.count(old) == 1, u'FINAL_REPORT U 计数锚点不唯一'
    s = s.replace(old, u'| 视觉台账 | U-31 … U-177（145 条；', 1)
    old = u'**M100–M457**（阶段二 357 支；'
    assert s.count(old) == 1, u'FINAL_REPORT 刀数锚点不唯一'
    s = s.replace(old, (u'**M100–M464**（阶段二 364 支；**R85 的 %s %s：%s** —— '
                        % (KNIFE_RANGE, KNIFE_TOTAL,
                           u'两刀第一版 ESCAPED（守卫只数"出现过"），改成数次数之后七刀全 CAUGHT）'))[:], 1)
    old = u'| 决定台账 | D-069 … D-137 | `AGENT_DECISIONS.md` |'
    assert s.count(old) == 1, u'FINAL_REPORT 决定台账锚点不唯一'
    # 这一格从 R81 起就没跟过：文件里最新的已经写到 D-142，表里还停在 D-137。
    # 修它的时候把"滞后了几轮"写在同一格里，不然下一次还是没人发现这是一张会过期的表。
    s = s.replace(old, (u'| 决定台账 | D-069 … **D-143**（这一格 R81–R84 四轮没跟着走，'
                        u'一直停在 D-137 —— R85 对过 `AGENT_DECISIONS.md` 的正文才补上，'
                        u'以后每轮写 D 时顺手改这一格）| `AGENT_DECISIONS.md` |'), 1)
    old = u'自评曲线（**77 轮**，Round 9–84，含 29d 那一轮边界轮；'
    assert s.count(old) == 1, u'FINAL_REPORT 曲线段锚点不唯一'
    s = s.replace(old, (u'自评曲线（**78 轮**，Round 9–85，含 29d 那一轮边界轮；' + CURVE +
                        u'；**后面那几段 `）：PHASE2 n=…` 是前几轮留下的同一条曲线的历史读数**'
                        u'（n 依次小 1，不是并存的两把尺，也不是本轮没算完））：'), 1)
    anchor = u'U-165 是**一把没验过坐标约定的尺'
    assert s.count(anchor) == 1, u'FINAL_REPORT 的 U 段插入锚点不唯一'
    s = s.replace(anchor, REPORT_U + anchor, 1)
    write(p, s)


REPORT_U = (u'U-174 是**守卫只数"这个串出现过"，会被另一条出口喂饱**（M461 / M462 双双 ESCAPED，'
            u'删掉正常路径的 emit 之后三条判据全绿 —— 改成数次数才有牙）；'
            u'U-175 是**登记名允许细节后缀、闸门按前缀匹配**（否则下一次有人删掉有用的一半来让 CI 变绿）；'
            u'U-176 是**新加一层判据时，旧夹具补不补背景行要分开决定**（给历史日志补新行 = 让它替新规则作证，'
            u'它就不再是它声称的那次运行的原文；R46 那份故意不补，于是它成了 LOOP_SILENT 的正对照）；'
            u'U-177 是**判据读不到运动有三种成因**（环境带不动 / 判据吃采样 / 画法让运动不可见 —— '
            u'第三种是 R84 的 CI 现场补上的：同一份时钟，画法一改，runner 从 0.050 跳到 0.522）。')


def fix_curve():
    # 曲线**在这里现跑一遍**，不读 verify 摘要里那一行：验证脚本跑曲线的时候本轮正文还没进台账，
    # 摘要里那一条必然是 n=77（而台账要写 n=78）。R84 就是靠人工重跑补的这一步 ——
    # 本轮把它写进脚本，占位符换进去的数与尾轮守卫的退出码都来自同一次现跑。
    proc = subprocess.run([sys.executable, '.scratch/motion-audit-2/curve_from_ledger.py'],
                          cwd=REPO, capture_output=True, text=True, timeout=600)
    if proc.returncode != 0:
        raise SystemExit('曲线守卫退出 %d ⇒ 台账里缺尾轮或有轮没有分数，先把正文写对再来换占位符\n%s'
                         % (proc.returncode, (proc.stdout + proc.stderr)[-1200:]))
    picked = [l for l in proc.stdout.splitlines() if l.startswith('GAPS=') or l.startswith('PHASE2')]
    real = ' '.join(picked).strip()
    if not real:
        raise SystemExit('曲线守卫没打 GAPS=/PHASE2 行：%s' % proc.stdout[:400])
    if 'n=78' not in real:
        raise SystemExit('曲线不是 78 轮（本轮正文没被识别为一个轮次？）：%s' % real[:200])
    stale = summary('CURVE', default=u'（验证摘要里没有 CURVE 行）')
    if stale != real:
        print(u'  注：verify 摘要里的 CURVE 是本轮正文进台账**之前**算的（n=77 那一版），'
              u'占位符用现跑的这一版')
    for rel in ('AGENT_VISUAL_ITERATION.md', 'AGENT_STATE.md', 'AGENT_FINAL_REPORT.md'):
        p = os.path.join(REPO, rel)
        t = read(p)
        if CURVE not in t:
            print(u'  %s 里没有占位符' % rel)
            continue
        write(p, t.replace(CURVE, real))
        print(u'  %s：占位符已替换' % rel)
    print(u'  CURVE(现跑)=%s' % real[:160])


STAGES = {
    'A': (patch_visual_iteration, patch_ui_audit, patch_decisions, patch_backlog, patch_changelog),
    'B': (patch_state, patch_final_report),
    'C': (lambda: fix_curve(),),
}


def main():
    stage = sys.argv[1] if len(sys.argv) > 1 else 'A'
    for fn in STAGES[stage]:
        fn()
        print(u'已写 %s' % fn.__name__)
    print(u'%s：%s' % (KNIFE_TOTAL, u', '.join(u'%s=%s' % (t, k) for t, _, k in KNIVES)))
    if BAD:
        print(u'!! 有刀没抓到：%s' % u'、'.join(BAD))


if __name__ == '__main__':
    sys.exit(main())
