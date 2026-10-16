# -*- coding: utf-8 -*-
'''R90 的台账补丁（第 92 轮 / Round 90）。

数字全部从产物读，不许手抄：
  * `/tmp/r90_verify/summary.log`                     —— 本轮逐条实跑的结论（含 NOT-RUN）
  * `/tmp/r90_verify/battery.log`                     —— 八刀原文
  * `.scratch/motion-audit-2/r90_ci_readings.md`      —— 读 R89 的 CI 的原文
  * `.scratch/motion-audit-2/r90_stats_readings.log`  —— 本轮真实看图的像素读数
  * `scripts/tests/fixtures/r90_pulse_real.log`       —— 产品自己写出的心跳（正对照的原件）

每个锚点都断言"命中且只命中一次"。分四段跑：A（正文与账）、B（STATE 与 FINAL_REPORT）、
C（曲线）、D（FINAL_REPORT 里那格反复滞后的轮次区间，从曲线守卫推）。

**这一轮没把 R89 那条"X 个 skipped"守卫搬过来**，是刻意的：本轮正文里既要写"R88 是 7 个 skipped"
（历史事实）又要写"本轮 0 个"（今天的读数），而那条守卫只看窗口里有没有"skip"这个词，
分不出"谁家的数" —— 它会把真话拦下来（正是 R89/U-196 记过的"尺过粗与尺过紧同罪"）。
本轮改police 三类**只属于本轮**的数：非台账文件个数、刀数、帧数，外加轮次标签 `max+1`。
'''
import io
import os
import re
import subprocess
import sys

REPO = '/Users/wangziyi/Codex_Project0'
SUMMARY = '/tmp/r90_verify/summary.log'
BATTERY = '/tmp/r90_verify/battery.log'
CI = os.path.join(REPO, '.scratch/motion-audit-2/r90_ci_readings.md')
VISUAL = os.path.join(REPO, '.scratch/motion-audit-2/r90_stats_readings.log')
PULSE_FIXTURE = os.path.join(REPO, 'scripts/tests/fixtures/r90_pulse_real.log')
FINDINGS = os.path.join(REPO, '.scratch/motion-audit-2/r90_findings_drag_hang_and_channel.md')
REVIEW = os.path.join(REPO, '.scratch/motion-audit-2/r90_visual_review_stats.md')
CURVE = 'CURVE_PLACEHOLDER_R90'


def refuse_while_mutating():
    """电池正在改工作树时，**读到的不是事实，是刀**（R89 / U-197 那一课）。

    本轮的刀改的是 `scripts/ui_probe_report.py`、`ci.yml`、两个 Swift 测试文件 ——
    也就是本轮正文要引用的那些东西。生成台账前先看有没有电池在跑，有就拒绝。
    （只装在读侧：`verify_r90.sh` 自己就是启动电池的那个。）
    """
    proc = subprocess.Popen(['pgrep', '-f', 'mutate_r90_pulse.py'],
                            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    pids = proc.communicate()[0].decode('utf-8', 'replace').split()
    if pids:
        raise SystemExit(u'变异电池还在跑（pid %s）⇒ 现在读到的工作树可能是被改过的样子，'
                         u'不许据此生成台账。等它结束再重跑' % u','.join(pids[:3]))


def read(path):
    return io.open(path, encoding='utf-8').read()


def write(path, text):
    check_claims(path, text)
    io.open(path, 'w', encoding='utf-8').write(text)


CN = u'零一二三四五六七八九十'
CLAIM_PATTERNS = (
    (re.compile(u'非台账文件 \\*\\*(\\d+) 个\\*\\*'), 'TOUCHED_NON_LEDGER'),
    (re.compile(u'非台账文件 (\\d+) 个'), 'TOUCHED_NON_LEDGER'),
    (re.compile(u'本轮动的非台账文件 \\*\\*(\\d+)\\*\\*'), 'TOUCHED_NON_LEDGER'),
    (re.compile(u'^(M?\\S*)?(\\d+) 刀', re.M), 'KNIFE_COUNT'),
    (re.compile(u'(\\d+) 张帧'), 'FRAMES'),
)


def check_claims(path, text):
    """台账里那几个"只属于本轮"的数必须能从产物读出来。

    **只管新写的话**：`write()` 拿到的是整份文件，而里面还有前 80 多轮的正文
    （"82 张帧""八刀"这类历史句子）。第一版没做这个区分，守卫就会拿本轮的数去判
    上一轮的账 —— 那是把"过粗"当成"严格"（R89/U-196 同一课）。
    """
    old = read(path) if os.path.exists(path) else u''
    for pat, key in CLAIM_PATTERNS:
        for m in pat.finditer(text):
            window = text[max(0, m.start() - 60):m.end() + 60]
            if window in old:
                continue          # 上一轮就写过的话，不由本轮负责
            want = CLAIM_VALUES[key]
            got = m.group(m.lastindex or 1)
            if got != want:
                raise SystemExit(
                    u'台账正文里的"%s"与产物矛盾：%s=%s（%s）。'
                    u'要么改正文，要么把产物补成真的支持这句话' % (m.group(0), key, want, path))


def product_value(key):
    text = read(SUMMARY)
    m = re.search(r'^%s=(.+)$' % re.escape(key), text, re.M)
    if not m:
        raise SystemExit(u'验证摘要里缺 %s —— 先把 verify_r90.sh 跑完再来写台账' % key)
    return m.group(1).strip()


def ci_value(pattern, what):
    m = re.search(pattern, read(CI), re.M)
    if not m:
        raise SystemExit(u'CI 读数原文里读不到 %s（模式 %s）⇒ 这条正文没有依据，不许写' % (what, pattern))
    return m.group(1)


def visual(pattern, what):
    m = re.search(pattern, read(VISUAL))
    if not m:
        raise SystemExit(u'看图读数里读不到 %s（模式 %s）⇒ 视觉审查的这条正文不许凭记忆写' % (what, pattern))
    return m.group(1)


refuse_while_mutating()

TOUCHED = product_value('TOUCHED_NON_LEDGER')
PRODUCT = product_value('PRODUCT_TOUCHED')
SCRIPTS = product_value('SCRIPT_TESTS')
PY_EXIT = product_value('PY_EXIT')
BATTERY_LINE = product_value('BATTERY')
BUILD_WARNINGS = product_value('BUILD_WARNINGS')
SWIFT_TAIL = product_value('SWIFT_TEST_TAIL')
SWIFT_EXIT = product_value('SWIFT_TEST_EXIT')
FRAMES = product_value('CAPTURE_FRAMES')
BASELINE = product_value('BASELINE')
VISUAL_SELFTEST = product_value('VISUAL_SELFTEST')
HEAT_EMPTY = product_value('HEAT_EMPTY_CELL')
SIDEBAR_ROWS = product_value('SIDEBAR_ROWS')
PULSE_SPIKE = product_value('PULSE_SPIKE')
PULSE_FIXTURE_LINES = product_value('pulse_fixture_lines')

NOT_RUN = [l.split('NOT_RUN=', 1)[1] for l in read(SUMMARY).split('\n') if l.startswith('NOT_RUN=')]
if len(NOT_RUN) < 4:
    raise SystemExit(u'验证摘要里只有 %d 条 NOT_RUN ⇒ 本轮不可能什么都没欠，先检查 verify 脚本'
                     % len(NOT_RUN))
NOT_RUN_LINE = u'；'.join(NOT_RUN)

# CI 那一格：R89 的修法在 runner 上的两条结论 + 顺序修复的效果。
ORPHAN = ci_value(r'^UI_PROBE_ORPHAN_XCTEST=(\S+)', 'UI_PROBE_ORPHAN_XCTEST')
ALIVE = ci_value(r'^UI_PROBE_RUNNER_ALIVE=(\S+)', 'UI_PROBE_RUNNER_ALIVE')
SKIPPED = ci_value(r'skipped 步骤数 = (\d+)', 'skipped 步骤数')
_m = re.search(r'passed=(\d+) NOT_RUN=(\d+)', read(CI))
if not _m:
    raise SystemExit(u'CI 读数原文里读不到 `Capture gate` 那一行 ⇒ 本轮正文不许凭记忆写')
GATE_RED = u'passed=%s NOT_RUN=%s' % (_m.group(1), _m.group(2))

# 看图读数（全部从 r90_stats_readings.log 现读，不抄）。
def visual_counts(label):
    """把 `ROW <label>` 那一行的四档阈值读数原样取出来（≥2/≥8/≥16/≥40）。"""
    m = re.search(u'ROW %s.*?图标 ≥2:(\\d+)\\s+≥8:(\\d+)\\s+≥16:(\\d+)\\s+≥40:(\\d+)' % label,
                  read(VISUAL))
    if not m:
        raise SystemExit(u'看图读数里读不到"%s"那一行的图标四档 ⇒ 视觉审查的这条正文不许凭记忆写' % label)
    return m.groups()


def first_in_frame(frame, pattern, what):
    """在**指定那一帧**的段落里取第一条匹配 —— 不然"最后一条 0 计数格"会是图例那一带的数
    （它的参照点被脚本自己标成 CARD_SAMPLE_CONTAMINATED，不许引用）。"""
    text = read(VISUAL)
    parts = re.split(u'(?m)^=== ', text)
    section = [p for p in parts if p.startswith(frame + u' ')]
    if len(section) != 1:
        raise SystemExit(u'看图读数里"%s"这一段命中 %d 次 ⇒ 不许据此引用 %s'
                         % (frame, len(section), what))
    m = re.search(pattern, section[0])
    if not m:
        raise SystemExit(u'看图读数里 %s 帧读不到 %s ⇒ 视觉审查的这条正文不许凭记忆写' % (frame, what))
    return m.group(1)


GRID_EMPTY = r'0 计数格（离卡片底最近的非蓝簇）rgb\(\d+,\d+,\d+\) 像素=\d+ 距卡片底=(\d+)'
EMPTY_LIGHT = first_in_frame('settings-stats-populated-720x540-light.png', GRID_EMPTY, '亮档网格 0 计数格')
EMPTY_DARK = first_in_frame('settings-stats-populated-720x540-dark.png', GRID_EMPTY, '暗档网格 0 计数格')
LABEL_LIGHT_MAX = visual(r'ROW 快捷键.*?标签 ≥2:\d+\s+≥8:\d+\s+≥16:\d+\s+≥40:\d+\s+最远=(\d+)',
                         '亮档侧栏标签最远距')
# 承重的那个数是 **≥8 那一档**（"偏淡"与"不存在"的分别就在这儿），不是 ≥2。
ICON_LIGHT_INK = visual_counts(u'快捷键')[1]
ICON_RECOMMEND = visual_counts(u'推荐')[3]

KNIVES = []
if os.path.exists(BATTERY):
    text = read(BATTERY)
    for m in re.finditer(r'^(M\d{3}) (.+?)$', text, re.M):
        tail = text[m.end():]
        hit = re.search(r'^   (CAUGHT|ESCAPED|NOT-RUN|NOT-APPLIED)', tail, re.M)
        KNIVES.append((m.group(1), m.group(2), hit.group(1) if hit else '?'))
if not KNIVES:
    raise SystemExit(u'battery.log 里读不到任何一刀 ⇒ 台账不许引用没跑过的刀')
CAUGHT = [t for t, _, k in KNIVES if k == 'CAUGHT']
ESCAPED = [t for t, _, k in KNIVES if k == 'ESCAPED']
if len(CAUGHT) != len(KNIVES):
    raise SystemExit(u'有刀没抓到就不许往台账里写"全部 CAUGHT"：%s'
                     % u'、'.join(u'%s(%s)' % (t, k) for t, _, k in KNIVES if k != 'CAUGHT'))
KNIFE_BY_TAG = dict((t, (n, k)) for t, n, k in KNIVES)
for tag in (u'M497', u'M504'):
    if tag not in KNIFE_BY_TAG:
        raise SystemExit(u'本轮正文要引用 %s，而电池里读不到它 ⇒ 要么补读要么改正文' % tag)


def short_note(n):
    head = n.split(u'⇒')[0].strip()
    return n.strip() if head.count(u'（') != head.count(u'）') else head


def knife_with(keyword):
    """按**描述的形状**找那一刀的编号 —— 命中必须恰好一次（与 U-198 同一课：
    凭记忆写编号，或者把描述当编号用，都会让台账指错刀）。"""
    hits = [t for t, n, _k in KNIVES if keyword in n]
    if len(hits) != 1:
        raise SystemExit(u'按"%s"找刀命中 %d 次（要求恰好 1）⇒ 正文不许引用一条对不上的刀号'
                         % (keyword, len(hits)))
    return hits[0]


def tidy(value):
    """把 verify 摘要里 `a|b|a|` 这种重复读数折成 `a（×2）`：
    两遍 `Executed 801 tests` 是同一条读数的两个出口，四张空态帧各报一次正对照也是。"""
    parts = [p.strip() for p in value.split(u'|') if p.strip()]
    seen, order = {}, []
    for p in parts:
        if p not in seen:
            seen[p] = 0
            order.append(p)
        seen[p] += 1
    return u' ；'.join(p if seen[p] == 1 else u'%s（×%d）' % (p, seen[p]) for p in order)


KNIFE_TABLE = u'\n'.join(u'| %s | %s | **%s** |' % (t, short_note(n), k) for t, n, k in KNIVES)
KNIFE_RANGE = u'%s–%s' % (KNIVES[0][0], KNIVES[-1][0])
KNIFE_TOTAL = u'%d 刀' % len(KNIVES)
KNIFE_LINE = u'%s（%s）：%d 刀 CAUGHT%s' % (
    KNIFE_RANGE, u'、'.join(t for t, _, _ in KNIVES), len(CAUGHT),
    u'，%s 逃掉' % u'、'.join(ESCAPED) if ESCAPED else u'，没有逃掉的')

CLAIM_VALUES = {u'TOUCHED_NON_LEDGER': TOUCHED, u'KNIFE_COUNT': str(len(KNIVES)), u'FRAMES': FRAMES}

ROUND_HEAD = u'''## Round 90 · 心跳通道落地了，但它落地之前先量掉了我自己的设计前提（读 R89 的 CI / 结案 122 / 更新 92、93、124 / 新开 125、126 / U-200…U-205 / D-148）

### 本轮开场的位点清单（0 个产品文件；本轮动的非台账文件 **%s 个**）

起点是 R89 交出去的两件事：**读它的 CI**，以及把 **BACKLOG 122**（每条判据一行心跳）做掉。
CI 那两条都成了，122 的做法在做的过程中被我自己的测量**推翻了一半**。

| 位点 | 位置 | 本轮判断 | 处置 |
|---|---|---|---|
| 看门狗收杀 | `.github/workflows/ci.yml` | R89 的修法在 runner 上被证实 | 只读：`UI_PROBE_ORPHAN_XCTEST=%s`（R88 三条 run 连着是 1） |
| 硬门顺序 | 同上 | R89 挪门之后 skipped 从 7 变 **%s** | 只读，不重做 |
| 探针"挂在哪一条" | `UIInteractionProbeTests.setUpWithError` | 122：心跳必须**每条用例都发**，且要活过 SIGKILL | 落地，但通道从 stderr 换成**自己 open 的文件**（见 §1） |
| 报告器 | `scripts/ui_probe_report.py` | 第二通道要与第一通道**互相签字**，不一致时降级成"只报观察" | 新增 `--pulse` 与 4 条新结论行 |
| 读数文件归属 | `CaptureReadings.swift` + CI 环境变量 | 两卷共用一份文件 ⇒ CI 新红是我造的（见 §3） | 探针改独立目录 + 一条会红的接线判据 |

''' % (TOUCHED, ORPHAN, SKIPPED)

_SECTION_TEMPLATE = u'''
### 1. 122 的心跳落地了，前提是那条我**量错了**（U-201）

R89 给 122 定的做法是："文件级已有 `emit()` 走 stderr（`FileHandle.write`，不经 stdio 缓冲），
而 CI 是 `> /tmp/ui.log 2>&1` ⇒ 这条腿本来就活得过 SIGKILL"。这句话读起来像事实，其实是我
从**源码形状**推出来的。本轮先量（`spike_r90_heartbeat.sh` / `spike_r90_channel_diag.sh`）：

```
%s
```

⇒ 在 `swift test` 下面，fd1 与 fd2 **都指向 SwiftPM 驱动自己的管道**（不是 CI 那个文件）。
驱动被 SIGKILL 时，它管道里没被读走的东西一起丢 —— stdout 的 `Test Case … started` 与 stderr
**一块儿丢**。所以"stderr 那条腿活得过 SIGKILL"是**假的**，而它正是 R89 那段设计的承重墙。
⇒ 心跳改走**自己 open 的文件**（`CLIPBOARD_HISTORY_PROBE_PULSE` → `probe-pulse.log`），
复用 `CaptureReadings` 那套锁与整行原子写。正对照不是我自己造的字符串：
`scripts/tests/fixtures/r90_pulse_real.log` 是产品写出来的原件，判据直接读它。

### 2. 两个独立证人第一次同意：挂死的那一条有名字了（93 → 新开 125）

```
UI_PROBE_HUNG=testDragSelectExpandsSelectionInsideTheRealList   ← 心跳：开了口、没有结论
sample 栈：MouseSynthesizer.drag → sendEvent: → NSCoreDragManager _dragUntilMouseUp
            → CoreDragStartDraggingAsync → _BlockUntilNextEventMatchingListInMode → mach_msg
```

⇒ 两条通道互相独立（一条是产品自己打的点，一条是 OS 采的栈），指向同一条用例、同一个机制：
**CoreDrag 的模态循环在等一个不会来的 mouseUp**。本机可复现，不是 runner 专属。
⇒ 于是 93 剩下的问题从"挂在哪"变成"怎么让它在 CI 里跑完" —— 那是**修法**，本轮没做，
开成 **BACKLOG 125**（两条路：给拖选探针自己加看门狗并让它报"我掐掉了自己" / 绕开
`sendEvent` 直接调手势逻辑）。⇒ 顺带一条对自己措辞的更正：R89 说"93 的成因在 runner 上被确认"，
确认的是**通道为什么丢日志**，不是**为什么挂死**；这两件事以前被我混在 93 一格写过。

### 3. CI 那朵新红是我自己造的：两卷共用一份读数文件（U-202）

```
Capture gate（%s）
```

⇒ 根因：`CaptureReadings` 的路径是从 `CLIPBOARD_HISTORY_UI_SHOTS` 派生的，而"第一写整份重写"
是**按 URL** 记的。探针卷与捕获卷在 CI 里指到同一个目录 ⇒ 探针把捕获卷**抹掉**了。
⇒ 修法两半：① CI 里探针改独立目录（`/tmp/shots-probe`）；② 光改目录不够，因为"两个卷共用一个文件"
这件事本身没有守卫 ⇒ 新增 `PulseWiringTests`：按**步骤**切片查（不许跨步骤 grep），
断言探针那一步的 `UI_SHOTS` 与捕获那一步不同名，且 `--pulse` 真的传给了两次报告器。
牙 **%s**（把在屏卷的 shots 目录改回与捕获卷共用，harness 必须红）就是这一条。

### 4. 真实看图：设置「统计」这一屏第一次有**可信**读数

零产品改动 ⇒ 当前帧就是产品像素。逐元素清单、坐标与"加不加"的判断写在
`.scratch/motion-audit-2/r90_visual_review_stats.md`；结论是**这一屏不加任何新动效**，
理由分三层（深浅是唯一信息通道 / 原生对照物都是静置的 / 唯一该动的 hover 已经有了且有判据）。

像素读数（`r90_stats_readings.log`）：

```
%s
%s
%s
```
⇒ 相邻档色相间距 亮 24→44→72→112、暗 24→44→76→112（最小一步 20），
0 计数格与卡片底只差 %s/%s（亮/暗，单位 /255）—— 这一格是**对的**：空格子要能看出网格，
但不能和最低一档抢。
⇒ 本轮看图真正的产出不是产品的缺陷，是**仪器的三处失效**（U-203）：
① R88 那把侧栏尺写的是 `maxc(p) - bg >= 40`，**只认比背景亮的墨** ⇒ 亮档黑字一颗带都切不出来，
于是"亮色侧栏没问题"从来不是读数，是没量到；
② 它的列常量（图标 88–150 / 文字 170–420）与本轮按结构扫出来的真实位置
（图标 35–68 / 标签 79–153 / 分隔线 296）**错位一整列** —— 它那个"文字框"整个落在内容区里。
⇒ R88 那句"图标里推荐与统计两行也只有 28"的主语应该是**标签**（内容仍然成立，标签写错了）；
③ 新仪器在暗档上 `COLUMN_SEGMENTS=1` ⇒ **NOT-RUN**：它今天没赢过旧仪器，暗档逐行读数仍只有一份。
⇒ 另有一条关于我自己眼睛的（U-205）：我先写下"侧栏图标偏淡"，量出来是
`≥8/255 的像素 %s 颗、最远 4/255、极值色号纯白` —— **淡是错的，是不存在**。
形容词不是读数。

### 5. 本轮超了约定：非台账文件 %s 个（约定是 ≤4）

一次说清楚，免得下一轮拿"上轮也这样"当依据：本轮的 7 个是
`ci.yml`、两个 Swift 测试文件、`ui_probe_report.py`、两份它的测试、一份真产物夹具。
其中**只有 4 个是计划内的**（心跳三件 + 报告器），另外 3 个是 §3 那朵红逼出来的
（换目录 + 接线判据 + 把自检的夹具正则放宽以接住新增的 env 行）。
⇒ 代价：本轮的"一次只改一处"被破了，于是 §1（通道）与 §3（目录归属）两件事的证据混在同一次推送里 ——
下一次 CI 若还红，我得先分辨是哪一件。这条记在 D-148 的"不许的处置"里：**下一轮不许把
"本轮 7 个"当默认值**，除非又能同时说出两件独立的事。

### 牙（%s，全部 CAUGHT）

%s

### 验证（本机，逐条实跑；跑不了的点名）

```
动了哪些非台账文件            %s 个；产品文件 %s
构建告警                       %s 条（0 才算过）
全量 Swift 测试                %s（exit %s）
脚本自测                       %s（exit %s）
捕获卷 + 帧基线                %s 张帧；对账 %s
变异电池                       %s
看图仪器自检                   %s
心跳通道本机实测               %s；产品原件 %s 行
没跑的                         %s
```

### 七维自评

| 维度 | 得分 | 说明 |
|---|---|---|
| 原生感 | 19 / 20 | 零产品改动；热图那一屏按"禁止假设现有动效合理"重判一遍，结论是不加任何东西 |
| 流畅度 | 17 / 20 | 拖选那条交互路径在 runner 上**仍然没有一次完整跑过**（125 未修），这一格按欠账记 |
| 层次与材质 | 14 / 15 | 亮档侧栏/热图第一次有可信读数；但暗档侧栏逐行新仪器 NOT-RUN，那一格仍只有一份旧读数 |
| 动效细节 | 15 / 15 | 122 结案：每条判据一行心跳，且两个通道互相签字；不一致时降级成"只报观察"而不是猜 |
| 交互反馈 | 9 / 10 | 反馈本身没动；hover 那一圈重看一遍，判"不加缩放/发光"并写了理由 |
| 可访问性 | 8 / 10 | 减弱动态那一臂仍无条件判；真机批次 72 / 73 还没人看 |
| 性能 | 15 / 15 | R89 的收杀在 runner 上被证实（`ORPHAN_XCTEST=%s`），skipped 从 7 变 %s |

**97 / 100**：本轮值钱的不是分数，是两件事 —— 93 第一次有了**被两个独立证人同意**的名字，
以及我自己的设计前提（stderr 那条腿）在动手之前被测量推翻。
扣的三分全部是有名字的欠账：125 没修、暗档侧栏读数没第二种、以及"7 个文件"那一次破例。

### 仍未解决

- BACKLOG **125**（本轮新开）：拖选探针挂在 CoreDrag 模态循环里 —— 现在能点名，还没修。
- BACKLOG **126**（本轮新开）：离屏捕获对侧栏语义色图标的解析**在同一列里不一致**
  （亮档四枚图标 0 墨、"推荐"那一枚 %s 颗 ≥40 且极值纯黑），而暗档侧栏逐行读数只有一份；
  修法第一步是**同一屏拿真机窗口截图与离屏帧对一次**（这台机器就能做，不该挂在"等真机"那栏）。
- BACKLOG **92 / 93**：93 的名字有了（见 §2），92 剩下的那一问（本机 90 秒能跑完 vs runner 240 秒收不掉）
  仍然没有名字。
- BACKLOG **124** 第②步（装机落后审计升成 `scripts/` 判据 + CI 一步）：本轮没做，理由见 §5。
- BACKLOG **119**：runner 分布仍停在 5 个点；本轮 CI 的动效地板是绿的，但**没给新数据点**
  （它只判"掉没掉臂"）。
- **121**、**116** 剩下那半格、**115**、**111**、108 余下、77 路 b、101 ②③、106；
  真机 68.1 / 68.2 / 69.1 / 70.1 / 71.1 / 72.1 / 72.2 / 73.1 / 73.2。
'''

# 摘要里那格是**逐带**的原始读数：图例那一带的参照点被脚本自己标成 CARD_SAMPLE_CONTAMINATED，
# 所以正文只引用"各取网格第一行"那两个数，原始串留在下面作留档。
HEAT_SUMMARY = (u'0 计数格 vs 卡片底：亮 %s/255、暗 %s/255（各取网格第一行）\n'
                u'原始逐带读数（含图例那一带，其参照点被脚本自己标了污染，只留档不引用）：\n%s'
                % (EMPTY_LIGHT, EMPTY_DARK, tidy(HEAT_EMPTY)))

_SECTION_ARGS = (
    PULSE_SPIKE, GATE_RED, knife_with(u'shots 目录改回'),
    HEAT_SUMMARY, tidy(SIDEBAR_ROWS), tidy(VISUAL_SELFTEST),
    EMPTY_LIGHT, EMPTY_DARK,
    ICON_LIGHT_INK, TOUCHED, KNIFE_TOTAL, KNIFE_TABLE,
    TOUCHED, PRODUCT, BUILD_WARNINGS, tidy(SWIFT_TAIL), SWIFT_EXIT, SCRIPTS, PY_EXIT,
    FRAMES, BASELINE, BATTERY_LINE, tidy(VISUAL_SELFTEST), PULSE_SPIKE, PULSE_FIXTURE_LINES,
    NOT_RUN_LINE, ORPHAN, SKIPPED, ICON_RECOMMEND)
if _SECTION_TEMPLATE.count(u'%s') != len(_SECTION_ARGS):
    raise SystemExit(u'SECTION 的占位符有 %d 个而参数有 %d 个 ⇒ 台账会串行，拒绝生成'
                     % (_SECTION_TEMPLATE.count(u'%s'), len(_SECTION_ARGS)))
SECTION = _SECTION_TEMPLATE % _SECTION_ARGS

UI_AUDIT = u'''## 第 92 轮 · R90：心跳通道落地，但那条设计前提被自己的测量推翻了（结案 122 / 新开 125、126 / U-200…U-205）

- **U-200 退出码与尺的身份都要当场核对**：`swift test … | tail -40` 之后拿到的 `SWIFT_TEST_EXIT=0`
  量的是**管道尾端 `tail`** 的退出码，不是测试的；同一次还把 `frame_baseline.py compare`
  （对 **v1.4.8 发布快照**）当成 CI 用的 `check --against working` 来引用 —— 两把尺，两个结论。
  ⇒ 改成 `> log; echo REAL_EXIT=$?`，并重新按 CI 那条命令跑一遍（`%s`）。
  ⇒ 同一族第三条（本轮自己又踩了一次）：新写的 verify 用 `grep -aE "^Executed"` 取汇总行，
  而 SwiftPM 那两行前面带制表符缩进 ⇒ `SWIFT_TEST_TAIL=` **静默为空**。
  空值不会喊，是我去对摘要才发现的 —— 摘要里每一格"有键无值"都该被当成红。
- **U-201 从源码形状推出来的"通道事实"要量**：R89 给 122 定的承重墙是"stderr 走 `FileHandle.write`
  所以活得过 SIGKILL"。实测：`swift test` 下 **fd1 与 fd2 都指向 SwiftPM 驱动的管道**，
  驱动被杀时两块一起丢 ⇒ 那句话是假的。⇒ 心跳改走**自己 open 的文件**，正对照用产品原件。
- **U-202 一个共享文件能让另一卷的读数整份消失**：`CaptureReadings` 的路径派生自
  `CLIPBOARD_HISTORY_UI_SHOTS`，而"第一写整份重写"按 URL 记 ⇒ 探针与捕获卷在 CI 里指同一目录时，
  探针把捕获卷抹掉（`%s`）。⇒ 换目录 + **一条会红的接线判据**（按步骤切片，不许跨步骤 grep）。
- **U-203 尺会同时坏在两个地方，而且坏得让人安心**：R88 那把侧栏尺 ① 只认比背景亮的墨
  （亮档黑字切不出带 ⇒ "亮色没问题"其实是"没量到"）；② 列常量与实测错位一整列
  （图标 35–68 / 标签 79–153 / 分隔线 296，而它写的是 88–150 / 170–420）。
  ⇒ R88 那句"图标里推荐与统计两行也只有 28"主语应是**标签**：内容成立，标签写错。
  本轮的新尺改成双边距离 + **按结构推列**（先扫分隔线再切列段），亮档第一次量到标签 %s/255。
- **U-204 我自己写的测试期望是错的**：以为"心跳只点名最后一条"，而语义是
  **每一条有心跳、没有结论的用例都要被点名**。⇒ 期望改成两条都点名，并把这段推理写进测试注释。
  真值表要先于期望。
- **U-205 形容词不是读数**：看图第一句写的是"侧栏图标偏淡"，量出来是
  `≥8/255 的像素 %s 颗、最远 4/255、极值色号纯白 (255,255,255)` —— 淡是错的，是不存在。
  ⇒ 本轮起，视觉审查里每条缺陷描述必须挂一个可证伪的数（`r90_stats_visual.py` 的四档阈值就是为这个）。
- 牙 %s 共八刀全部 CAUGHT。零产品改动 ⇒ 帧按构造不变，仍实测：`%s`。
  122 **结案**；93 第一次有了被两个独立证人同意的名字（心跳 + `sample` 的 CoreDrag 栈），
  修法开成 **125**；离屏/真机那一次对照开成 **126**。

''' % (BASELINE, GATE_RED, LABEL_LIGHT_MAX, ICON_LIGHT_INK, KNIFE_RANGE, BASELINE)

DECISION = u'''
### D-148（R90）心跳走自己 open 的文件；共享读数文件的归属要由会红的判据管

- 背景：122 要的是"每条判据自己发一行读数"，好让看门狗收掉之后还能说出挂在哪一条。
  R89 定的通道是 stderr，理由写在台账里（`FileHandle.write` 不经 stdio 缓冲）。
  本轮动手前先量：`swift test` 下 fd1/fd2 都是 SwiftPM 驱动的**管道**，驱动被 SIGKILL 时
  stdout 与 stderr 一起丢 ⇒ 那条理由不成立。同时 CI 里两卷共用一份 `capture-readings.log`
  （路径派生自同一个环境变量），"第一写整份重写"把另一卷抹掉，`Capture gate` 因此红。
- 决定：① 心跳写**自己 open 的文件**（`CLIPBOARD_HISTORY_PROBE_PULSE` → `probe-pulse.log`），
  复用 `CaptureReadings` 的锁与"整行一次 write"；② 报告器同时读两条通道，
  **一致**才报 `UI_PROBE_CHANNELS_AGREE=1` 并点名，**不一致**报
  `UI_PROBE_CHANNELS_CONTRADICT` 并退回"只报观察不报成因"；③ 探针在 CI 里用独立目录，
  并且这条归属由 `PulseWiringTests` 钉住（按步骤切片，跨步骤 grep 不算）；
  ④ 93 的挂死本身不在本轮修，开成 125 —— 一次只改一处，本轮已经有两处。
- 为什么"两个通道"而不是"换个通道就完事"：任何一条单独都可能骗人（stdout 会丢、文件路径会撞），
  而它们**互相不一致**这件事本身是可判的。骗人的通道不能当唯一证人（与 U-200 同一族）。
- 不许的处置：把心跳退回 stderr（本轮已量掉）；为了过 `Capture gate` 把捕获卷的读数改成
  追加而不重写（那是拿产品行为讨好夹具）；拿"本轮 7 个非台账文件"当下一轮的默认值；
  或者把 125 与 126 混成一条"探针不稳定"—— 一条是挂死机制，一条是捕获通道可信度。
'''

BACKLOG_92_UPDATE = u'''
    → **R90 的读数**：`UI_PROBE_ORPHAN_XCTEST=%s`（R88 三条 run 连着是 1）⇒ R89 的收杀够到了；
    `skipped 步骤数 = %s`（R88 是 7）⇒ 四道硬门挪位置生效，仪器的红不再吃掉产品的证据。
    92 剩下的那一问仍然是：**本机 90 秒能跑完 vs runner 240 秒收不掉**，这一格还没有名字。
''' % (ORPHAN, SKIPPED)

BACKLOG_93_UPDATE = u'''
    → **R90：这一格第一次有名字，而且是两个独立证人同意的**。
    ① 产品自己发的心跳（`probe-pulse.log`，`setUpWithError` 每条用例一行）点名
    `testDragSelectExpandsSelectionInsideTheRealList`：开了口、没有结论；
    ② `sample` 采到的栈：`MouseSynthesizer.drag → NSWindow sendEvent: → _NSGFGestureEnvironment
    → NSCoreDragManager _dragUntilMouseUp → CoreDragStartDraggingAsync
    → _BlockUntilNextEventMatchingListInMode → mach_msg`（0% CPU，在睡，不是在转）。
    ⇒ 机制：**CoreDrag 的模态循环在等一个不会来的 mouseUp**，本机可复现，不是 runner 专属。
    ⇒ 一条措辞更正：R89 说"93 的成因在 runner 上被确认"，确认的是**通道为什么丢日志**，
    不是**为什么挂死**。修法（加看门狗 vs 绕开 `sendEvent` 直接调手势逻辑）开成 **BACKLOG 125**。
'''

BACKLOG_122_CLOSE = u'''
    → **R90 结案**，但**通道与 R89 定的不一样**：先量再动手，结果量掉了自己写的前提 ——
    `swift test` 下 fd1/fd2 都指向 SwiftPM 驱动的管道，驱动被 SIGKILL 时 stdout 与 stderr
    **一起丢**（`spike_r90_channel_diag.sh`），所以"stderr 那条腿活得过 SIGKILL"是假的。
    实际落地：心跳写**自己 open 的文件**（`CLIPBOARD_HISTORY_PROBE_PULSE` → `probe-pulse.log`，
    复用 `CaptureReadings` 的锁与整行原子写），`ui_probe_report.py --pulse` 把它与 stdout
    的 started/concluded 做**双通道对照**：一致才点名（`UI_PROBE_CHANNELS_AGREE=1`），
    不一致就退回"只报观察不报成因"（`UI_PROBE_CHANNELS_CONTRADICT`）。
    正对照用的是产品写出的原件（`scripts/tests/fixtures/r90_pulse_real.log`），不是我造的字符串。
    牙 %s 共八刀全 CAUGHT；其中「%s」与「%s」两刀管的就是通道本身
    （一刀把心跳退回 print ⇒ 它又变成会被驱动吞掉的装饰；一刀把 `PULSE_EMPTY` 改成绿 ⇒
    通道坏了却宣布"有名字"）。
''' % (KNIFE_RANGE, KNIFE_BY_TAG[u'M498'][0], KNIFE_BY_TAG[u'M503'][0])

BACKLOG_124_UPDATE = u'''
    R90 **没做第②步**：本轮非台账文件已到 %s 个（约定 ≤4），再叠一步会让"哪一处让 CI 变了"分不清
    （见 D-148 与本轮正文 §5）。这条欠账继续挂着，不许被读成"已经升成判据了"。
''' % (TOUCHED,)

BACKLOG_125_NEW = u"""
125. **拖选探针挂在 CoreDrag 的模态循环里：现在能点名，还没修**（R90 开 / 与 92、93、122 同族）：

    R90 把 122 做完之后，93 第一次有了名字 —— 心跳点名
    `testDragSelectExpandsSelectionInsideTheRealList`，`sample` 的栈独立同意机制：
    `NSCoreDragManager _dragUntilMouseUp → CoreDragStartDraggingAsync →
    _BlockUntilNextEventMatchingListInMode → mach_msg`（0% CPU 在睡）。
    ⇒ 这是**合成 mouseDown 之后系统进了拖拽模态循环，而合成的 mouseUp 永远送不进去**。
    本机可复现（不是 runner 专属），所以它不是"CI 慢"，是这条探针的结构问题。
    ⇒ 两条路，都要先 spike 再动仓库：
    ① 给这条探针自己加一层超时：到点就 `NSApp.stopModal`/直接结束拖拽会话，并**主动打一行
    "我掐掉了自己"** —— 宁可少一条判据，也不要一条会挂死的判据；
    ② 绕开 `sendEvent`：直接调手势/选择逻辑（`List` 的 selection 变更那条），
    代价是它不再经过真实事件路径 ⇒ 判据资格要重谈（与 104"证人必须与判据同一颗尺子"同族）。
    ⇒ 不许的处置：把这条探针删掉（那是删测试绕开检查）；或者把它标成"已知会挂"就完事 ——
    看门狗现在能收尸、报告器能点名，但**收尸不等于修好**。
"""

BACKLOG_126_NEW = u"""
126. **离屏捕获对侧栏语义色图标的解析在同一列里不一致；暗档侧栏逐行读数只有一份**（R90 开 / 与 96、116、123 同族）：

    R90 重做设置「统计」这一屏的看图时，第一次用**双边**尺量到两件事：

    ```
    亮档侧栏：标签 最远 251/255（六行都可读）
    亮档图标：快捷键/通用/隐私/数据 ≥8/255 的像素 **0 颗**，最远 4/255，极值色号纯白 (255,255,255)
              推荐 ≥40 的 143 颗，极值纯黑 (0,0,0)      ← 同一列里两种解析结果
    ```

    ⇒ 与 `SettingsView.swift:808–815` 里 R30 记下的那条（`OffscreenSymbolInkProbeTests`
    量到未选中行墨水比 0.0000，换成固定 `Color.black` 能到 0.175–0.402）是**同一族**：
    离屏管线解析语义色。**但不是同一份读数**：R30 那份是"未选中四行全 0"，
    今天这张帧是"四枚 0、`wand.and.stars` 那一枚纯黑" ⇒ 解析结果取决于**符号本身**。
    ⇒ 三步：① **同一屏拿真机窗口截图（`screencapture`）与离屏帧对一次** ——
    这件事这台机器就能做，以前被挂在"等用户真机"那一栏是记账错误；
    ② 若真机可见 ⇒ 把"离屏帧不判图标可辨性"写成一格**声明**（与 `menuSurfaceReplicaFixtures` 同形状），
    而不是每次看图时靠人记得；③ 若真机也不可见 ⇒ 那是产品缺陷，改着色路径。
    ⇒ 顺带一条仪器欠账：本轮新写的 `r90_stats_visual.py` 在**暗档**上
    `COLUMN_SEGMENTS=1 ⇒ NOT-RUN`（分隔线只有 ~10/255，门槛降到 8 之后 vibrancy 噪声把两列连成一段）。
    修法是把列位置从**同主题亮档帧**推，或改用行投影切列。在那之前，暗档侧栏逐行读数只有 R88 那一份，
    而那一份的**列身份**已被本轮证明错位（见 U-203）。
"""


def patch_visual_iteration():
    p = os.path.join(REPO, 'AGENT_VISUAL_ITERATION.md')
    s = read(p)
    assert u'## Round 90' not in s, u'Round 90 已经写过了'
    for artifact, what in ((REVIEW, '视觉审查'), (FINDINGS, '挂死与通道结论')):
        if not os.path.exists(artifact):
            raise SystemExit(u'%s 的原件不在（%s）⇒ 正文引用了不存在的东西' % (what, artifact))
    write(p, s.rstrip(u'\n') + u'\n\n' + ROUND_HEAD + SECTION)


def patch_ui_audit():
    p = os.path.join(REPO, 'AGENT_UI_AUDIT.md')
    s = read(p)
    assert u'## 第 92 轮' not in s
    nums = [int(m.group(1)) for m in re.finditer(u'^## 第 (\\d+) 轮', s, re.M)]
    want = max(nums) + 1
    if (u'## 第 %d 轮' % want) not in UI_AUDIT:
        raise SystemExit(u'UI_AUDIT 的轮次标签必须等于台账现有最大号 %d 再加一（=%d），'
                         u'而正文写的不是这个数 ⇒ 会跳号，拒绝落盘' % (max(nums), want))
    anchor = u'## 第 91 轮 · R89：'
    assert s.count(anchor) == 1, u'UI_AUDIT 的 91 轮锚点不唯一'
    write(p, s.replace(anchor, UI_AUDIT + anchor, 1))


def patch_decisions():
    p = os.path.join(REPO, 'AGENT_DECISIONS.md')
    s = read(p)
    assert u'### D-148' not in s
    write(p, s.rstrip(u'\n') + u'\n' + DECISION)


def patch_backlog():
    p = os.path.join(REPO, 'AGENT_BACKLOG.md')
    s = read(p)
    a92 = u'    `UI_PROBE_RUNNER_ALIVE` / `UI_PROBE_ORPHAN_XCTEST` 两格才算有读数。\n'
    assert s.count(a92) == 1, u'92 的锚点不唯一（命中 %d）' % s.count(a92)
    s = s.replace(a92, a92 + BACKLOG_92_UPDATE, 1)
    a93 = u'    三种结果都是答案，而这一格的价值就在于它**不许**留成『大概是无头会话的问题』。\n'
    assert s.count(a93) == 1, u'93 的锚点不唯一（命中 %d）' % s.count(a93)
    s = s.replace(a93, a93 + BACKLOG_93_UPDATE, 1)
    a122 = u'    ④ 整行一次 write（R81 那一课：内容与换行分两次写会被并发缝在一起）。\n'
    assert s.count(a122) == 1, u'122 的锚点不唯一（命中 %d）' % s.count(a122)
    s = s.replace(a122, a122 + BACKLOG_122_CLOSE, 1)
    a124 = u'    第②步（升成 `scripts/` 里的判据 + 自测 + CI 报告型一步）仍然开着，交下一轮。\n'
    assert s.count(a124) == 1, u'124 的锚点不唯一（命中 %d）' % s.count(a124)
    s = s.replace(a124, a124 + BACKLOG_124_UPDATE, 1)
    # 新开 125 / 126：接在文件末尾（124 那一段之后）。锚点=文件最后一行，唯一性先查。
    tail = s.rstrip(u'\n').split(u'\n')[-1] + u'\n'
    assert s.count(tail) >= 1
    s = s.rstrip(u'\n') + u'\n' + BACKLOG_125_NEW.strip(u'\n') + u'\n' + BACKLOG_126_NEW.strip(u'\n') + u'\n'
    write(p, s)


def patch_changelog():
    p = os.path.join(REPO, 'CHANGELOG.md')
    s = read(p)
    anchor = u'## [Unreleased]\n'
    assert s.count(anchor) == 1
    assert u'### CI（R90' not in s
    write(p, s.replace(anchor, anchor + CHANGELOG, 1))


CHANGELOG = u'''### CI（R90）

- 在屏探针的读数文件与捕获卷**分家**（`CLIPBOARD_HISTORY_UI_SHOTS` 换成 `/tmp/shots-probe`）：
  两卷共用一份 `capture-readings.log` 时，"第一写整份重写"会把另一卷整份抹掉，
  `Capture gate` 因此读到 `%s`。
- 探针新增**每条用例一行心跳**：`CLIPBOARD_HISTORY_PROBE_PULSE` → `probe-pulse.log`，
  由 `UIInteractionProbeTests.setUpWithError()` 发；CI 两次调用报告器都带 `--pulse`。

### 判据与仪器（R90）

- `scripts/ui_probe_report.py`：新增第二通道（`PULSE` 正则 + `--pulse`）。两条通道**一致**才点名
  （`UI_PROBE_CHANNELS_AGREE=1`），不一致报 `UI_PROBE_CHANNELS_CONTRADICT` 并退回"只报观察不报成因"；
  心跳文件读不到时打 `UI_PROBE_PULSE_UNREADABLE=`（仪器坏了必须红，不许静默绿）。
- `scripts/tests/test_ui_probe_report.py`：`PulseChannelTests`（含用产品原件做正对照）+
  `PulseWiringTests`（按步骤切片查接线与目录归属，跨步骤 grep 不算）。
- `scripts/tests/fixtures/r90_pulse_real.log`：产品自己写出的心跳原件，判据直接读它。
- `.scratch/motion-audit-2/`：`r90_stats_visual.py`（双边侧栏尺 + 按结构推列 + 四档阈值 +
  格式串 arity 自检）、`mutate_r90_pulse.py`（%s）、三支 spike（心跳 / 通道诊断 / 脉搏接线）。

### Docs（R90）

- BACKLOG **122 结案**（心跳落地，通道从 stderr 改成自己 open 的文件 —— 原前提被测量推翻）；
  93 更新（第一次有名字，两个独立证人同意）；92 更新（`ORPHAN_XCTEST=%s`、skipped %s）；
  124 更新（第②步仍欠）；新开 **125**（拖选探针挂在 CoreDrag 模态循环）与
  **126**（离屏捕获对侧栏语义色图标解析不一致 + 暗档逐行读数只有一份）。

''' % (GATE_RED, KNIFE_LINE, ORPHAN, SKIPPED)

STATE_ANCHOR_HINT = '最后更新：2026-10-16 09:05（本地 · R89 / 第 91 轮收尾：'


def patch_state():
    p = os.path.join(REPO, 'AGENT_STATE.md')
    s = read(p)
    head_marker = STATE_ANCHOR_HINT
    assert s.count(head_marker) == 1, u'STATE 头部锚点不唯一'
    new_head = (u'最后更新：2026-10-16 11:20（本地 · R90 / 第 92 轮收尾：**读 R89 的 CI 两条都成了，'
                u'而 BACKLOG 122 的承重墙在动手前被自己的测量推翻** —— '
                u'`UI_PROBE_ORPHAN_XCTEST=%s`（R88 三条 run 连着是 1）与 `skipped 步骤数 = %s`'
                u'（R88 是 7）⇒ U-192 / U-193 两条修法在 runner 上被证实，而且是那道门自己从红变绿。'
                u'122 结案，但通道换了：R89 写的"stderr 活得过 SIGKILL"实测是假的 —— '
                u'`swift test` 下 fd1/fd2 都是 SwiftPM 驱动的管道，驱动被杀时两块一起丢（U-201）'
                u'⇒ 心跳改走**自己 open 的文件**，报告器加 `--pulse` 做**双通道对照**，'
                u'一致才点名、不一致退回"只报观察"。93 第一次有名字：心跳点名 '
                u'`testDragSelectExpandsSelectionInsideTheRealList`，`sample` 的栈独立同意'
                u'（CoreDrag 模态循环等一个不会来的 mouseUp，本机可复现）⇒ 修法开成 **125**。'
                u'CI 那朵新红是我自己造的：两卷共用一份读数文件，"第一写整份重写"把捕获卷抹掉'
                u'（`%s`）⇒ 换目录 + `PulseWiringTests` 按步骤钉住归属（U-202）。'
                u'真实看图这一腿：设置「统计」整屏重判，结论**不加任何新动效**；顺带量出 R88 那把'
                u'侧栏尺的两处失效（只认比背景亮的墨 + 列常量错位一整列）⇒ "亮色侧栏没问题"'
                u'从来不是读数而是没量到（U-203），本轮新尺第一次量到亮档标签 %s/255；'
                u'新尺在暗档 NOT-RUN，那一格仍只有一份旧读数（U-205 与 126）。'
                u'**本轮破例：非台账文件 %s 个（约定 ≤4）**，理由与代价写在正文 §5 与 D-148。'
                u'验证：产品 %s；构建告警 %s；全量 %s（exit %s）；脚本 %s（exit %s）；'
                u'帧 %s 张 + 对账 %s；电池 %s；没跑的：%s。'
                u'**下一轮第一件事：读 R90 的 CI（`Capture gate` 必须复绿 + 心跳通道第一次在 runner 上落盘）'
                u'，然后 BACKLOG 125 先 spike 再动仓库**）\n\n'
                u'> 上一轮（R89 / 第 91 轮收尾）原文开头：' + head_marker) % (
        ORPHAN, SKIPPED, GATE_RED, LABEL_LIGHT_MAX, TOUCHED, PRODUCT, BUILD_WARNINGS,
        tidy(SWIFT_TAIL), SWIFT_EXIT, SCRIPTS, PY_EXIT, FRAMES, BASELINE, BATTERY_LINE, NOT_RUN_LINE)
    write(p, s.replace(head_marker, new_head, 1))


def patch_final_report():
    p = os.path.join(REPO, 'AGENT_FINAL_REPORT.md')
    s = read(p)
    old = u'| 阶段二 **82 轮**审计（R9–R89，含 29d；'
    assert s.count(old) == 1, u'FINAL_REPORT 轮数锚点不唯一'
    s = s.replace(old, u'| 阶段二 **83 轮**审计（R9–R90，含 29d；', 1)
    old = u'以 `curve_from_ledger.py` 的 `PHASE2 n=82` 为准）'
    assert s.count(old) == 1, u'FINAL_REPORT 曲线锚点不唯一'
    s = s.replace(old, u'以 `curve_from_ledger.py` 的 `PHASE2 n=83` 为准）', 1)
    old = u'| 视觉台账 | U-31 … U-199（168 条；'
    assert s.count(old) == 1, u'FINAL_REPORT U 计数锚点不唯一'
    s = s.replace(old, u'| 视觉台账 | U-31 … U-205（174 条；', 1)
    old = u'| 决定台账 | D-069 … **D-147**'
    assert s.count(old) == 1, u'FINAL_REPORT 决定台账锚点不唯一'
    s = s.replace(old, u'| 决定台账 | D-069 … **D-148**', 1)
    old = u'**M100–M496**（阶段二 396 支；'
    assert s.count(old) == 1, u'FINAL_REPORT 刀数锚点不唯一'
    s = s.replace(old, (u'**M100–M504**（阶段二 404 支；**R90 的 %s %s 全 CAUGHT**'
                        u'（两刀测的是"通道会不会自己骗自己"：「%s」把心跳退回 print ⇒ 它又被驱动吞掉；'
                        u'「%s」把 `PULSE_EMPTY` 改成绿 ⇒ 通道坏了却宣布有名字。另两刀测归属：'
                        u'「%s」与「%s」）；'
                        % (KNIFE_RANGE, KNIFE_TOTAL, KNIFE_BY_TAG[u'M498'][0],
                           KNIFE_BY_TAG[u'M503'][0], KNIFE_BY_TAG[u'M500'][0],
                           KNIFE_BY_TAG[u'M504'][0])), 1)
    old = u'自评曲线（**82 轮**，Round 9–89，含 29d 那一轮边界轮；'
    assert s.count(old) == 1, u'FINAL_REPORT 曲线段锚点不唯一'
    s = s.replace(old, (u'自评曲线（**83 轮**，Round 9–90，含 29d 那一轮边界轮；' + CURVE +
                        u'；**后面那几段 `）：PHASE2 n=…` 是前几轮留下的同一条曲线的历史读数**'
                        u'（n 依次小 1，不是并存的两把尺，也不是本轮没算完））：'), 1)
    anchor = (u'U-192 是**杀父组不等于杀整棵树**')
    assert s.count(anchor) == 1, u'FINAL_REPORT 的 U 段插入锚点不唯一'
    s = s.replace(anchor, REPORT_U + anchor, 1)
    write(p, s)


REPORT_U = (u'U-200 是**退出码与尺的身份都要当场核对**（`swift test | tail` 之后拿到的 0 是 `tail` 的，'
            u'而 `frame_baseline compare` 被当成 CI 用的 `check --against working`）；'
            u'U-201 是**从源码形状推出来的"通道事实"必须量**（R89 给 122 定的"stderr 活得过 SIGKILL"'
            u'实测是假的：`swift test` 下 fd1/fd2 都是驱动的管道，一起丢）；'
            u'U-202 是**共享读数文件能让另一卷的读数整份消失**（两卷指同一目录时"第一写整份重写"'
            u'把捕获卷抹掉 ⇒ 换目录 + 按步骤钉归属的接线判据）；'
            u'U-203 是**尺会同时坏在阈值与坐标两处，而且坏得让人安心**'
            u'（只认比背景亮的墨 ⇒ 亮档黑字切不出带；列常量错位一整列 ⇒ "文字框"落在内容区，'
            u'于是 R88 那句"图标也只有 28"的主语应是标签）；'
            u'U-204 是**我自己写的测试期望是错的**（心跳的语义是"每条有心跳、无结论的都点名"，'
            u'不是"最后一条"⇒ 真值表要先于期望）；'
            u'U-205 是**形容词不是读数**（"图标偏淡"量出来是"不存在"：≥8/255 零颗、极值纯白）；')


def fix_curve():
    proc = subprocess.run([sys.executable, '.scratch/motion-audit-2/curve_from_ledger.py'],
                          cwd=REPO, capture_output=True, text=True, timeout=600)
    if proc.returncode != 0:
        raise SystemExit(u'曲线守卫退出 %d ⇒ 台账里缺尾轮或有轮没有分数：%s'
                         % (proc.returncode, (proc.stdout + proc.stderr)[-1200:]))
    picked = [l for l in proc.stdout.splitlines() if l.startswith('GAPS=') or l.startswith('PHASE2')]
    real = ' '.join(picked).strip()
    if not real:
        raise SystemExit(u'曲线守卫没打 GAPS=/PHASE2 行：%s' % proc.stdout[:400])
    if 'n=83' not in real:
        raise SystemExit(u'曲线不是 83 轮（本轮正文没被识别为一个轮次？）：%s' % real[:200])
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
    """轮次区间那一格从曲线守卫推，不手抄（R87 现场：它连续多轮滞后）。"""
    p = os.path.join(REPO, 'AGENT_FINAL_REPORT.md')
    s = read(p)
    proc = subprocess.run([sys.executable, '.scratch/motion-audit-2/curve_from_ledger.py'],
                          cwd=REPO, capture_output=True, text=True, timeout=600)
    if 'GAPS=none' not in proc.stdout:
        raise SystemExit(u'曲线守卫报了缺轮 ⇒ 区间格子不许写：%s'
                         % [l for l in proc.stdout.splitlines() if l.startswith('GAPS')])
    m = re.search(r'PHASE2 n=(\d+) rounds=(\d+)\.\.(\d+)', proc.stdout)
    if not m:
        raise SystemExit(u'曲线守卫没打出 PHASE2 n=… rounds=… ⇒ 这一格不许手抄：%s' % proc.stdout[:200])
    n, lo, hi = int(m.group(1)), int(m.group(2)), int(m.group(3))
    extra = n - (hi - lo + 1)
    if extra not in (0, 1):
        raise SystemExit(u'PHASE2 n=%d 与 rounds=%d..%d 差 %d ⇒ 既不是"编号连续"也不是"多一个 29d"：%s'
                         % (n, lo, hi, extra, m.group(0)))
    fresh = (u'`AGENT_VISUAL_ITERATION.md` Round %d–%d（%d 条读数：编号 %d–%d 共 %d 个，'
             u'外加 29d 那一轮边界轮；区间与条数都从曲线守卫的 `rounds=…`/`n=…` 推）'
             % (lo, hi, n, lo, hi, hi - lo + 1))
    pattern = re.compile(u'`AGENT_VISUAL_ITERATION\\.md` Round \\d+–\\d+（\\d+ 条读数：[^）]*）')
    hits = pattern.findall(s)
    if len(hits) != 1:
        raise SystemExit(u'那一格按形状命中 %d 次（要求 1）⇒ 不许盲改：%s' % (len(hits), hits[:3]))
    if hits[0] == fresh:
        print(u'  区间格子已经是最新值（%d–%d，%d 条）' % (lo, hi, n))
        return
    write(p, pattern.sub(lambda _m: fresh, s, count=1))


def refuse_stray_placeholders():
    """任何一段要落盘的正文里**不许还剩 `%s`**：那说明某段忘了格式化，
    于是台账里会出现字面的"牙 %s 共八刀"（本轮 stage A 第一次跑就撞上两处）。
    这一条比"数占位符个数"更兜底：个数对得上也可能整段没被格式化。
    """
    bad = []
    for name, blob in sorted(globals().items()):
        if not isinstance(blob, str):
            continue
        if not name.startswith(('BACKLOG_', 'CHANGELOG', 'UI_AUDIT', 'DECISION',
                                'SECTION', 'ROUND_HEAD', 'REPORT_U')):
            continue
        if u'%s' in blob or u'%d' in blob:
            bad.append(name)
    if bad:
        raise SystemExit(u'这些正文里还留着没被格式化的占位符：%s ⇒ 台账会写出字面 %%s，拒绝落盘'
                         % u'、'.join(bad))


refuse_stray_placeholders()

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
