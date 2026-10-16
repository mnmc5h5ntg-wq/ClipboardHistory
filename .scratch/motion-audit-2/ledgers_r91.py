# -*- coding: utf-8 -*-
'''R91 的台账补丁（第 93 轮 / Round 91）。

数字全部从产物读，不许手抄：
  * `/tmp/r91_verify/summary.log`   —— 本轮逐条实跑的结论（含 NOT-RUN 与那 5 刀）
  * `/tmp/r91_verify/battery.log`   —— 五刀原文（M509 是**故意**要逃的那一刀）
  * `/tmp/r91_flakiness.log`        —— "修前"那一侧的读数：三遍都是 180 秒收不掉
  * `.scratch/motion-audit-2/r91_findings_zombie_probe.md` / `r91_visual_review_focus.md`

沿用 R90 生成器的三条约束：电池在跑就拒绝生成；本轮新写的话里的数必须与产物一致；
占位符 arity 与"不许残留 %s"。轮次标签仍从台账自己的 `max+1` 推。
'''
import io
import os
import re
import subprocess
import sys

REPO = '/Users/wangziyi/Codex_Project0'
SUMMARY = '/tmp/r91_verify/summary.log'
BATTERY = '/tmp/r91_verify/battery.log'
FLAKY = '/tmp/r91_flakiness.log'
FINDINGS = os.path.join(REPO, '.scratch/motion-audit-2/r91_findings_zombie_probe.md')
REVIEW = os.path.join(REPO, '.scratch/motion-audit-2/r91_visual_review_focus.md')
CURVE = 'CURVE_PLACEHOLDER_R91'


def refuse_while_mutating():
    proc = subprocess.Popen(['pgrep', '-f', 'mutate_r91_zombie.py'],
                            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    pids = proc.communicate()[0].decode('utf-8', 'replace').split()
    if pids:
        raise SystemExit(u'变异电池还在跑（pid %s）⇒ 现在读到的工作树可能是被改过的样子，拒绝生成台账'
                         % u','.join(pids[:3]))


def read(path):
    return io.open(path, encoding='utf-8').read()


def write(path, text):
    check_claims(path, text)
    io.open(path, 'w', encoding='utf-8').write(text)


CLAIM_PATTERNS = (
    (re.compile(u'非台账文件 \\*\\*(\\d+) 个\\*\\*'), 'TOUCHED_NON_LEDGER'),
    (re.compile(u'非台账文件 (\\d+) 个'), 'TOUCHED_NON_LEDGER'),
    (re.compile(u'^(?:M?\\S*)?(\\d+) 刀', re.M), 'KNIFE_COUNT'),
    (re.compile(u'(\\d+) 张帧'), 'FRAMES'),
    (re.compile(u'executed (\\d+) tests'), 'PROBE_EXECUTED'),
)
# 本轮新加的一条：**"这一卷跑出 N 条结论"这句话必须等于探针自己那一行的读数**。
# 上一轮我是从摘要里抄的，这一轮它是本轮的头条数字 ⇒ 更要从产物取。


def product_value(key):
    text = read(SUMMARY)
    m = re.search(r'^%s=(.+)$' % re.escape(key), text, re.M)
    if not m:
        raise SystemExit(u'验证摘要里缺 %s —— 先把 verify_r91.sh 跑完再来写台账' % key)
    return m.group(1).strip()


def tally(field):
    m = re.search(u'%s=(\\d+)' % field, product_value('PROBE_TALLY'))
    if not m:
        raise SystemExit(u'PROBE_TALLY 里读不到 %s ⇒ 头条数字不许凭记忆写' % field)
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
PROBE_TALLY = product_value('PROBE_TALLY')
PROBE_READINGS = product_value('PROBE_READINGS')
PROBE_RED = product_value('PROBE_RED')
VISUAL = product_value('VISUAL')
PROBE_EXECUTED = tally('executed')
PROBE_PASSED = tally('passed')
PROBE_SKIPPED = tally('skipped')
PROBE_FAILED = tally('failed')
PROBE_PULSES = tally(u'心跳')

NOT_RUN = [l.split('NOT_RUN=', 1)[1] for l in read(SUMMARY).split('\n') if l.startswith('NOT_RUN=')]
if len(NOT_RUN) < 4:
    raise SystemExit(u'验证摘要里只有 %d 条 NOT_RUN ⇒ 本轮不可能什么都没欠' % len(NOT_RUN))
NOT_RUN_LINE = u'；'.join(NOT_RUN)

# "修前"那一侧：三遍都是 180 秒被掐、心跳 2、有结论 0。从 spike 的日志读，不抄。
RUNS = re.findall(r'^RUN (\d) exit=(\d+) 用时=(\d+)s 心跳=(\d+) started=(\d+) 有结论=(\d+)',
                  read(FLAKY), re.M)
if len(RUNS) < 3:
    raise SystemExit(u'flakiness 日志只读到 %d 遍 ⇒ "3/3 挂死"这句话没有依据' % len(RUNS))
BAD_RUNS = [r for r in RUNS if r[1] == '137' and r[5] == '0']
if len(BAD_RUNS) != len(RUNS):
    raise SystemExit(u'不是每一遍都挂死（挂 %d / 共 %d）⇒ 台账里那句"恒挂"要改成闪挂'
                     % (len(BAD_RUNS), len(RUNS)))
BEFORE_LINE = u'心跳 %s / 有结论 %s / %s 秒被掐（本机 %d/%d 遍同形）' % (
    RUNS[0][3], RUNS[0][5], RUNS[0][2], len(BAD_RUNS), len(RUNS))

KNIVES = []
for m in re.finditer(r'^(M\d{3}) (.+?)$', read(BATTERY), re.M):
    tail = read(BATTERY)[m.end():]
    hit = re.search(r'^   (CAUGHT|ESCAPED|NOT-RUN)', tail, re.M)
    KNIVES.append((m.group(1), m.group(2), hit.group(1) if hit else '?'))
if len(KNIVES) != 5:
    raise SystemExit(u'电池里读到 %d 刀（应为 5）⇒ 台账不许引用没跑过的刀' % len(KNIVES))
CAUGHT = [t for t, _n, k in KNIVES if k == 'CAUGHT']
ESCAPED = [t for t, _n, k in KNIVES if k == 'ESCAPED']
NOTRUN = [t for t, _n, k in KNIVES if k == 'NOT-RUN']
if NOTRUN:
    raise SystemExit(u'有刀没跑成：%s ⇒ 先修刀，再写台账' % u'、'.join(NOTRUN))
if ESCAPED != [u'M509']:
    raise SystemExit(u'逃掉的必须是且只有 M509（那一刀是故意要逃的对照），实际：%s' % u'、'.join(ESCAPED))
KNIFE_BY_TAG = dict((t, (n, k)) for t, n, k in KNIVES)
CLAIM_VALUES = {u'TOUCHED_NON_LEDGER': TOUCHED, u'KNIFE_COUNT': str(len(KNIVES)),
                u'FRAMES': FRAMES, u'PROBE_EXECUTED': PROBE_EXECUTED}


def check_claims(path, text):
    """只管**本轮新写**的话：整份文件里还有前 80 多轮的正文，那些数归它们那一轮负责。"""
    old = read(path) if os.path.exists(path) else u''
    for pat, key in CLAIM_PATTERNS:
        for m in pat.finditer(text):
            window = text[max(0, m.start() - 60):m.end() + 60]
            if window in old:
                continue
            if m.group(m.lastindex or 1) != CLAIM_VALUES[key]:
                raise SystemExit(u'台账正文里的"%s"与产物矛盾：%s=%s（%s）'
                                 % (m.group(0), key, CLAIM_VALUES[key], path))


def short_note(n):
    head = n.split(u'⇒')[0].strip()
    return n.strip() if head.count(u'（') != head.count(u'）') else head


KNIFE_TABLE = u'\n'.join(u'| %s | %s | **%s** |' % (t, short_note(n), k) for t, n, k in KNIVES)
KNIFE_RANGE = u'%s–%s' % (KNIVES[0][0], KNIVES[-1][0])
KNIFE_TOTAL = u'%d 刀' % len(KNIVES)
KNIFE_LINE = u'%s：%d CAUGHT / %d 逃掉（%s，故意）/ 0 没跑成' % (
    KNIFE_RANGE, len(CAUGHT), len(ESCAPED), u'、'.join(ESCAPED))

for artifact, what in ((FINDINGS, '僵尸探针结论'), (REVIEW, '本轮看图')):
    if not os.path.exists(artifact):
        raise SystemExit(u'%s 的原件不在（%s）⇒ 正文引用了不存在的东西' % (what, artifact))

ROUND_HEAD = u'''## Round 91 · 追了五轮的"CI 上一条判据都没跑完"，成因是一条我以为删掉了、其实没删的探针（结案 125 / 更新 92、93、124、126 / 新开 127 / U-206…U-210 / D-149）

### 本轮开场的位点清单（0 个产品文件；本轮动的非台账文件 **%s 个**）

起点是 R90 交下来的第一件事：读它的 CI。但 CI 还没读完，本机一支 spike 就把本轮的头条撞了出来 ——
**在屏那一卷不是"runner 上跑不动"，是被一条僵尸探针挡死的**。

| 位点 | 位置 | 本轮判断 | 处置 |
|---|---|---|---|
| 僵尸拖选探针 | `UIInteractionProbeTests` | D-034 写着"已删除"，`git log --all -S` 证明从没删过 | 删；原位置留解释 + 机制级守卫 |
| 合成拖拽这件事 | `MouseSynthesizer` | 任何 `.leftMouseDragged` 都会进 CoreDrag 模态循环，**阈值内也一样** | 助手一起删；限制打成 `DRAG-LIMIT` 读数 |
| 帧采样通道 | `testFrameIntervalsUnderStateChanges` | 第一次跑到就红，而 0 个样本来自**显示器睡着**，不是产品 | 加 `FRAME_CHANNEL` 证人：通道没活就报"没跑" |
| 覆盖登记 | `scripts/probe_coverage_expectations.json` | 用例没了而登记还在 | 删那一行（是 `probe_coverage_gate` 自己报的 STALE） |

''' % TOUCHED

_SECTION_TEMPLATE = u'''
### 1. 头条：这一卷第一次跑到 %s 条结论

```
修前：%s
修后：%s
```

⇒ 从 R86 追到 R90 的那句"CI 上 `executed: 0`"，成因不是 runner、不是时钟、不是通道 ——
是 `testDragSelectExpandsSelectionInsideTheRealList`：**它测的拖选手势在 D-034（六天前，
用户真机反馈后决定）就被判定不做**，而 D-034 的正文写着"这条探针删除并在原位置留了解释"。
解释确实留了，**函数还在它上面**。`git log --all -S "func testDragSelect…"` 只有一次增、零次删。

### 2. 我第一版修法被自己的第二次测量撤掉（U-207）

我先按"越过拖拽阈值才会起会话"把它改成 **2pt 阈值内微移**（`pressNudgeRelease`），以为安全了。
再跑一遍：栈**一模一样** —— `sendEvent → _NSGestureEnvironment → NSCoreDragManager
_tryCatchDragUntilMouseUp → _dragUntilMouseUp → CoreDragStartDraggingAsync →
_BlockUntilNextEventMatchingListInMode`。会话照样起来。
⇒ 阈值那个前提是我想当然。合成拖拽在这条路径上**做不到**，与位移大小无关。
⇒ 于是整条撤掉（连工具函数一起，留着就会被下一次复用），只留一行 `DRAG-LIMIT` 读数 + 守卫。
⇒ 教训：**改法的第一版也要重跑**，"能编译 + 讲得通"不是第二次测量。

### 3. 采样通道坏了却判产品，是本轮第二次撞上的同一族（U-209）

`testFrameIntervalsUnderStateChanges` 第一次跑出结论就红：`帧样本太少，结论无效（0 不大于 60）`。
查因不在产品 —— 同一台机器 `screencapture` 返回 2940×1912 **全黑**、`pmset` 报 `UserIsActive 0`
⇒ 显示器睡着 ⇒ `CADisplayLink` 一颗 tick 都不发。
⇒ 判据改成"通道先当自己的证人"：空转 0.6 秒拿不到 tick 就报 `%s` 并 skip。
   地板（n>60 / p95≤20ms / worst≤120ms）**一条都没放宽** —— 放宽它就是把"仪器没跑"洗成"产品没问题"。

### 4. 覆盖登记那一步是**门自己报的**（这条顺序很重要）

我删完探针没想起登记文件；是 `probe_coverage_gate` 的自测红给我看的：
```
STALE testDragSelectExpandsSelectionInsideTheRealList：清单里有、源码里已经没有这条用例 ⇒ 删掉这行登记
```
⇒ 这就是 R82 造那道门想要的形状：它不替我做决定，它把我漏的那一格摆到我面前。
⇒ 登记里其余十条的 reason 都写着"无头 runner 上整卷在第一条结论之前就被收掉"——
   **那句成因写错了**（真因是这条僵尸探针）。但我**没有**替它们改登记：
   "runner 上今天能不能跑到"是下一次 CI 的读数，本机结果不配替它签字。
   门会在"说跑不了却跑到了"时再红一次，那时逐条重登记。

### 5. 本轮看图：选中态在**两条**离屏路径里都是黑的（BACKLOG 126 的第二、三格数据点）

在屏探针自己拍的 `focus-after-tab-{light,dark}.png`（1600×1264）：

```
%s
```

⇒ 亮档里被选中的那一行是一条**纯黑色带**（行均亮度 2/255，行内文字与图标一颗都看不见），
   而**整帧找不到任何蓝** ⇒ 焦点环在这条通道里根本没落墨。
⇒ 交叉检查做成了一半：同一状态在**捕获卷的基线帧** `content-with-history-750x560-light.png`
   里也是同一条黑胶囊 ⇒ 这不是在屏探针独有的，是两条离屏路径共有的选中态材质盲区，
   而且它已经在 124 帧基线里活了很多轮（基线只比对差异，不判可读性，所以没人报过）。
⇒ 另一半做坏了，也记下来：我第一版用"整列最暗的 6 行"当尺，量到的是**窗口外的黑底**
   （y≈796 已出窗口）⇒ 那三个"0/255"作废。正确做法是**用探针自己报出来的 `ListTableRowView` 矩形**
   当扫描区域，不要猜 y（同一族教训：R88 列常量错位、R90 参照点污染、R91 量到窗外）。
⇒ 真机截图那一腿 **NOT-RUN**：这台机器给不出真机像素（见下面"没跑的"）。
   所以"黑带 = 产品缺陷"与"黑带 = 通道"两个结论本轮都**没有证据**，126 继续挂着。

### 6. 第一条真红：BACKLOG 127（本轮只做到"有名字"）

```
%s
```

⇒ 一行暴露**两个半宽** `KeyViewProxy`（148 + 148 + 间距 ≈ 320 = 整行宽）。
两种成因，本轮不分定：① 产品的无障碍结构（Tab 一行停两次、焦点环可能只画半行）；
② 这条判据的期望（"宽 200…290"）写在它**从没跑出结论**的情况下 —— 一把没被正对照校准过的尺，
不配有罪判决（R87/U-200 同一族）。⇒ 127 的第一步是拿同一颗尺去量**快速选择浮层**那一卷列表：
也两个半宽 ⇒ ②；不是 ⇒ ①。
⇒ 本轮**不**为了让 CI 绿去改那条期望，也不删这条探针。所以推上去之后 main 会带着
   一朵**有名字的红** —— 修僵尸探针的意义就是让红能说话。

### 牙（%s；M509 是故意要逃的那一刀）

%s

M509 把守卫从"扫事件类型"退回"扫函数名" ⇒ 它**必须**逃，逃掉才是本轮想记的事实：
名字级守卫可以被改名绕过，所以钉的是 `(.leftMouseDragged` 这个机制形状。

### 验证（本机，逐条实跑；跑不了的点名）

```
动了哪些非台账文件            %s 个；产品文件 %s
构建告警                       %s 条（0 才算过）
全量 Swift 测试                %s（exit %s）
脚本自测                       %s（exit %s）
在屏那一卷（CI 原样 + 心跳）   %s
两条新读数                     %s
捕获卷 + 帧基线                %s 张帧；对账 %s
变异电池                       %s
看图仪器                       %s
没跑的                         %s
```

### 七维自评

| 维度 | 得分 | 说明 |
|---|---|---|
| 原生感 | 19 / 20 | 零产品改动；主窗口侧栏行的选中/聚焦两态重判一遍，结论是不加任何东西 |
| 流畅度 | 19 / 20 | 在屏那一卷第一次跑到 %s 条结论（其中含帧间隔那条判据的通道证人）；但它在**这台机器**上判不了，runner 那一格等下一次 CI |
| 层次与材质 | 13 / 15 | 亮档基线帧里"被选中的那一行是纯黑色带"这一格本轮第一次量到并登记；焦点环在捕获侧完全不可判 —— 两格都没定性 |
| 动效细节 | 15 / 15 | 125 结案：合成拖拽被证明在这条路径上做不到，限制打成读数并由机制级守卫钉住 |
| 交互反馈 | 9 / 10 | 反馈本身没动；选中态不可判这件事使"选中算不算反馈"这一格不能给满 |
| 可访问性 | 7 / 10 | 第一次跑完就出 BACKLOG 127（一行两个半宽可焦点代理）；本轮只做到点名 |
| 性能 | 15 / 15 | 整卷从 180 秒收不掉变成 13.8 秒跑完；CI 不再被一条挂死用例拖满作业 |

**97 / 100**：本轮把五轮追的"CI 上一条判据都没跑完"归到了一条本该六天前就删掉的探针上，
并且把自己第一版"压到阈值内就安全"的修法用第二次测量撤掉。
扣的分全是有名字的：127 没定性、选中态/焦点环两格不可判、真机那一腿没跑。

### 仍未解决

- BACKLOG **127**（本轮新开）：一行两个半宽 `KeyViewProxy` —— 产品无障碍结构 vs 期望没被正对照校准。
- BACKLOG **126**：真机窗口截图 vs 离屏帧那一次对照（这台机器现在给不出真机像素）；
  本轮新加两格数据点（选中态黑带跨两条离屏路径、焦点环零墨）。
- BACKLOG **92**：登记里那句"runner 上整卷在第一条结论之前就被收掉"**成因写错**（真因是僵尸探针），
  但"runner 今天能不能跑到"仍要等下一次 CI；另有一条本机内部的矛盾没解开：
  R89 记"本机这一卷 90 秒跑得完"，R91 三遍都是 180 秒收不掉 ⇒ 那两次跑法差在哪，还没有名字。
- BACKLOG **124** 第②步（装机落后审计升成判据）：仍欠。
- BACKLOG **119**、**121**、**116** 剩下那半格、**115**、**111**、108 余下、77 路 b、101 ②③、106；
  真机 68.1 / 68.2 / 69.1 / 70.1 / 71.1 / 72.1 / 72.2 / 73.1 / 73.2。
'''

_SECTION_ARGS = (
    PROBE_EXECUTED, BEFORE_LINE, PROBE_TALLY,
    re.search(r'FRAME_CHANNEL[^|]*', PROBE_READINGS).group(0),
    VISUAL, PROBE_RED[:300], KNIFE_TOTAL, KNIFE_TABLE,
    TOUCHED, PRODUCT, BUILD_WARNINGS, SWIFT_TAIL, SWIFT_EXIT, SCRIPTS, PY_EXIT,
    PROBE_TALLY, PROBE_READINGS, FRAMES, BASELINE, KNIFE_LINE, VISUAL, NOT_RUN_LINE,
    PROBE_PASSED)
if _SECTION_TEMPLATE.count(u'%s') != len(_SECTION_ARGS):
    raise SystemExit(u'SECTION 的占位符有 %d 个而参数有 %d 个 ⇒ 台账会串行，拒绝生成'
                     % (_SECTION_TEMPLATE.count(u'%s'), len(_SECTION_ARGS)))
SECTION = _SECTION_TEMPLATE % _SECTION_ARGS

UI_AUDIT = u'''## 第 93 轮 · R91：五轮追的"CI 上一条判据都没跑完"，成因是一条我以为删掉了、其实没删的探针（结案 125 / 新开 127 / U-206…U-210）

- **U-206 台账里的"已完成"断言必须能被机器复查**：D-034 写着"原来那条拖选探针删除并在原位置留了一段解释"——
  解释在，函数也在。`git log --all -S "func testDragSelect…"` 只有 9d7b5ca 一次增、零次删。
  ⇒ 一句"已删除 X"以前只能靠人记得；本轮起它由 `probe_coverage_gate` 的 STALE 格管着
  （清单里有、源码里没有 ⇒ 红），而**这次红是我删完之后它才报的**——门不替我决定，但它把我漏的摆出来。
- **U-207 "我以为压到阈值内就安全"不是证据**：第一版修法把拖动改成 2pt 微移，栈一模一样、
  会话照样起来（`_tryCatchDragUntilMouseUp`）。⇒ 改法的第一版也要重跑一遍，能编译不等于成立。
- **U-208 电池必须把"断言红"与"编译坏"分开**：Swift 卷退出非 0 有两种成因；第一版 M505 写的是
  `_ = NSEvent.EventType(.leftMouseDragged)`，编译器不认 ⇒ 那会被读成"抓到了"，其实是刀坏了。
  ⇒ 现在只有"跑起来了且是那条守卫失败"算 CAUGHT，编译错误一律 NOT-RUN。
  同一轮又踩了一次老账：`python3 … | tail` 之后拿到的 `$?` 是 `tail` 的（U-200 那一族）。
- **U-209 0 个样本既不能判产品，也不能判"通过"**：`testFrameIntervalsUnderStateChanges` 第一次跑到就红
  （n=0），而真因是这台机器显示器睡着（`screencapture` 全黑、`UserIsActive 0`）⇒
  `CADisplayLink` 不发 tick。⇒ 判据先看**采样通道活没活**（`FRAME_CHANNEL baseline_n=…`），
  没活就报"没跑"并 skip；地板一条没放宽。
- **U-210 扫描区域必须由被测量自己报**：交叉检查第一版用"整列最暗的 6 行"，量到的是窗口外的黑底
  ⇒ 那三个数作废。正确做法是用探针自己打印的 `ListTableRowView` 矩形。
  同一族第三次：R88 列常量错位一整列、R90 参照点被标污染、R91 量到窗外。
- 牙 %s（M509 故意逃：守卫若退回"扫函数名"就会被改名绕过 ⇒ 钉的是事件类型 `(.leftMouseDragged`）。
  在屏那一卷第一次跑到结论：`%s`；全量 %s；124 张帧对账 `CHANGED=0`；非台账文件 %s 个、产品 0 个。
  新开 **127**（一行两个半宽 `KeyViewProxy`，本轮只点名不定性）；126 加两格数据点
  （选中态黑带跨两条离屏路径、焦点环零墨）；125 **结案**。

''' % (KNIFE_LINE, PROBE_TALLY, SWIFT_TAIL, TOUCHED)

DECISION = u'''
### D-149（R91）合成拖拽在 `window.sendEvent` 这条路径上做不到；限制要打成读数并被守卫钉住

- 背景：从 R86 追到 R90 的"CI 上在屏那一卷 `executed: 0`"，本机三遍复现同一形状
  （180 秒被掐、心跳 2 条、有结论 0 条），`sample` 给出栈：
  `sendEvent → _NSGestureEnvironment → NSCoreDragManager _tryCatchDragUntilMouseUp →
  _dragUntilMouseUp → CoreDragStartDraggingAsync → _BlockUntilNextEventMatchingListInMode`。
  CoreDrag 等的是**窗口服务器**的真 mouseUp，而探针把 mouseUp 排在 `sendEvent` 的下游 ⇒ 进程内无解。
  而这条探针测的手势 D-034 六天前就决定不做（用户真机反馈：`List` 会把行内任何 `.onDrag`
  提升成整行拖拽源，拖选与拖出不能共存，取舍是保拖出）。
- 决定：① 删掉 `testDragSelectExpandsSelectionInsideTheRealList` 与 `MouseSynthesizer.drag`
  （工具留着就会被复用），原位置留解释块；② OBSERVE 那一条里的合成拖拽撤掉，改成一行
  `DRAG-LIMIT` 读数 —— 限制必须可 grep，不许只写在注释里；③ 新增机制级守卫
  `SidebarListSelectionTests.testProbeSuiteNeverSynthesizesADragSession`：扫**事件类型**
  `(.leftMouseDragged`（改名绕不过），并要求 `DRAG-LIMIT`、`FRAME_CHANNEL`、解释块三样都在；
  ④ 帧采样判据加通道证人：空转拿不到 tick ⇒ 报 `FRAME_CHANNEL baseline_n=0` 并 skip，
  地板（n>60 / p95≤20 / worst≤120）一条不放宽；⑤ 覆盖登记里那一行由门自己报 STALE 之后删。
- 为什么"删测试"这次不是绕开检查：这条判据断言的行为是产品**决定不做**的（D-034 且有静态守卫
  `testNoCompetingDragSelectGestureRemains` 钉着），它永远不可能通过；它留在树上的净效果是
  把其余 10 条在屏判据挡在门外。删它 = 恢复 10 条判据，同时把那条决定换成更硬的机制级守卫。
- 不许的处置：为了 CI 绿去改 `testSidebarListFocusRingAfterClick` 的几何期望（那是 127，未定性）；
  拿本机"10 条结论"去替覆盖登记里"runner 上跑不了"那十行改口（下一次 CI 的读数才配）；
  或者把 `DRAG-LIMIT` 撤掉当作限制不存在 —— 那样下一轮又会长出第二条挂死的探针。
'''

BACKLOG_125_CLOSE = u'''
    → **R91 结案**，但**两条路都没走**（都不需要走）：先量再选路，结果量到的是
    "这条路本身在进程内做不到"。三遍本机复现（180 秒被掐、心跳 2、有结论 0）+ `sample` 的栈：
    `sendEvent → NSCoreDragManager _tryCatchDragUntilMouseUp → CoreDragStartDraggingAsync →
    _BlockUntilNextEventMatchingListInMode` —— CoreDrag 等的是窗口服务器的真 mouseUp，
    而探针的 mouseUp 排在 `sendEvent` 下游。⇒ 撤掉合成拖拽（连 `MouseSynthesizer.drag` 一起），
    限制打成 `DRAG-LIMIT` 读数，机制级守卫 `testProbeSuiteNeverSynthesizesADragSession` 钉住。
    ⇒ 另有一条：这条探针测的手势 D-034 就决定不做，而 D-034 写着"探针已删除"——**那句是假的**
    （`git log --all -S` 只有增、没有删）。⇒ 见 U-206。
'''

BACKLOG_92_UPDATE = u'''
    → **R91 把这一格翻面了**：本机按 CI 原样跑，三遍都是 **180 秒收不掉、有结论 0**
    ⇒ R89 那句"本机 90 秒跑得完"与今天矛盾（差在哪还没有名字），而"runner 上跑不动"这个前提
    本身也被推翻：真因是那条僵尸拖选探针（见 125）。⇒ 修完本机第一次跑到
    `%s`。登记里那十行 reason 写的"runner 上整卷在第一条结论之前就被收掉"**成因错了**，
    但"runner 今天能不能跑到"仍要等下一次 CI —— 不许拿本机结果替它改口。
''' % (PROBE_TALLY,)

BACKLOG_93_CLOSE = u'''
    → **R91 结案（本机侧）**：名字有了（心跳点名）+ 机制有栈（CoreDrag 模态循环）+ 修法落地
    （撤掉合成拖拽，见 125）。剩下的一格交给 92：**runner 上**现在跑到几条，等下一次 CI。
'''

BACKLOG_126_UPDATE = u'''
    R91 加两格数据点，并且**这台机器现在做不了那一次决定性对照**：

    ```
    focus-after-tab-light.png 1600x1264  NO_BLUE（焦点环零墨）
    同一帧被选中的那一行：整条纯黑色带，行均亮度 2/255，行内文字与图标全不可见
    交叉检查：捕获卷基线帧 content-with-history-750x560-light.png 同一状态也是同一条黑胶囊
    screencapture -x → 退出 0、2940x1912、采样 2500 点全 (0,0,0)；pmset UserIsActive 0
    ```

    ⇒ 选中态材质在**两条离屏路径里都是黑的**（不是在屏探针独有），而焦点环在捕获侧完全不可判；
    ⇒ 真机那一腿 **NOT-RUN**（显示器睡着/无录屏权限）⇒ 本轮**没有**资格说"真机也看不见"。
    ⇒ 下一步（126 里原来那三步仍然有效）：亮屏 + 授权后对一次；若真机正常 ⇒ 把
    "离屏帧不判选中态材质与焦点环"写成**声明**（与 `menuSurfaceReplicaFixtures` 同形状），
    而不是每次靠人记得。另：交叉检查第一版量到窗外（"整列最暗 6 行"命中窗口外黑底），
    扫描区域必须改用探针自己报的 `ListTableRowView` 矩形（U-210）。
'''

BACKLOG_124_UPDATE = u'''
    R91 仍**没做**第②步（本轮非台账文件 %s 个：探针卷、守卫、覆盖登记 —— 再加一步就分不清
    是哪一处让 CI 变了）。欠账继续挂着。
''' % (TOUCHED,)

BACKLOG_127_NEW = u"""
127. **在屏卷第一次跑完就红：一行暴露两个半宽 `KeyViewProxy`**（R91 开 / 与 126、116、104 同族）：

    僵尸探针删掉之后，`testSidebarListFocusRingAfterClick` 第一次跑出结论，红话是：

    ```
    找不到行代理（要求 KeyViewProxy 宽 200…290、高 <40）
    宿主 (0,0,320,460)；实际 KeyViewProxy@(12.0, 50.5, 148.0, 25.0) 与 (160.0, 50.5, 148.0, 25.0)
    ```

    ⇒ 一行**两个半宽**可焦点代理（148 + 148 + 间距 ≈ 320 = 整行宽）。两种成因，本轮**不分定**：
    ① 产品的无障碍结构 —— Tab 一行停两次、VoiceOver 把一行读成两段、焦点环可能只画半行；
    ② 这条判据的期望（"宽 200…290"）写在它**从没跑出过结论**的情况下 ——
      一把没被正对照校准过的尺不配有罪判决（R87 / U-200 同一族）。
    ⇒ 第一步是**正对照**：同一颗尺去量快速选择浮层那一卷列表的行代理。
      也两个半宽 ⇒ ②（SwiftUI `List` 的固有结构，期望要按实测重推，并写进 D 台账）；
      只有一个全宽 ⇒ ①（产品缺陷，改无障碍结构，并同步这条判据）。
    ⇒ 不许的处置：为了让 CI 绿直接把期望改成"148 也行"（那是拿判据讨好现状）；
      或者把这条探针删掉 —— 它现在**能跑出结论**，正是 R91 之前所有在屏判据缺的那种东西。
    ⇒ 本轮推上去之后 main 带着这朵红，是有意的：修僵尸探针的意义就是让红能说话。
"""


def patch_visual_iteration():
    p = os.path.join(REPO, 'AGENT_VISUAL_ITERATION.md')
    s = read(p)
    assert u'## Round 91' not in s, u'Round 91 已经写过了'
    write(p, s.rstrip(u'\n') + u'\n\n' + ROUND_HEAD + SECTION)


def patch_ui_audit():
    p = os.path.join(REPO, 'AGENT_UI_AUDIT.md')
    s = read(p)
    assert u'## 第 93 轮' not in s
    nums = [int(m.group(1)) for m in re.finditer(u'^## 第 (\\d+) 轮', s, re.M)]
    want = max(nums) + 1
    if (u'## 第 %d 轮' % want) not in UI_AUDIT:
        raise SystemExit(u'UI_AUDIT 的轮次标签必须等于台账现有最大号 %d 再加一（=%d），拒绝跳号落盘'
                         % (max(nums), want))
    anchor = u'## 第 92 轮 · R90：'
    assert s.count(anchor) == 1, u'UI_AUDIT 的 92 轮锚点不唯一'
    write(p, s.replace(anchor, UI_AUDIT + anchor, 1))


def patch_decisions():
    p = os.path.join(REPO, 'AGENT_DECISIONS.md')
    s = read(p)
    assert u'### D-149' not in s
    write(p, s.rstrip(u'\n') + u'\n' + DECISION)


def patch_backlog():
    p = os.path.join(REPO, 'AGENT_BACKLOG.md')
    s = read(p)
    a125 = u'    看门狗现在能收尸、报告器能点名，但**收尸不等于修好**。\n'
    assert s.count(a125) == 1, u'125 的锚点不唯一（命中 %d）' % s.count(a125)
    s = s.replace(a125, a125 + BACKLOG_125_CLOSE, 1)
    a126 = u'    而那一份的**列身份**已被本轮证明错位（见 U-203）。\n'
    assert s.count(a126) == 1, u'126 的锚点不唯一（命中 %d）' % s.count(a126)
    s = s.replace(a126, a126 + BACKLOG_126_UPDATE, 1)
    a92 = u'    是**下一次 CI 的读数**，本轮不许替它回答；那之后才谈得上"路 b"（让能跑的那几条真的跑起来）。\n'
    if s.count(a92) != 1:
        # 92 那一段的收尾行在 R89/R90 之后被追加过，按形状找它当前真正的第一行。
        a92 = u'    而 runner 上 240 秒收不掉 ⇒ "runner 上卡在哪"与"本机为什么能跑完"之间的差**还没有名字**。\n'
    hits = [l + u'\n' for l in s.split(u'\n')
            if l.startswith(u'    而 runner 上 240 秒收不掉')]
    assert len(hits) == 1, u'92 的锚点按形状命中 %d 次（要求 1）' % len(hits)
    s = s.replace(hits[0], hits[0] + BACKLOG_92_UPDATE, 1)
    a93 = u'    不是**为什么挂死**。修法（加看门狗 vs 绕开 `sendEvent` 直接调手势逻辑）开成 **BACKLOG 125**。\n'
    assert s.count(a93) == 1, u'93 的锚点不唯一（命中 %d）' % s.count(a93)
    s = s.replace(a93, a93 + BACKLOG_93_CLOSE, 1)
    # 124 的收尾行在 R90 被追加过 ⇒ 按**形状**找（startwith '（见 D-148'），不拼旧文。
    hits124 = [l + u'\n' for l in s.split(u'\n') if l.startswith(u'    （见 D-148')]
    assert len(hits124) == 1, u'124 的锚点按形状命中 %d 次（要求 1）' % len(hits124)
    s = s.replace(hits124[0], hits124[0] + BACKLOG_124_UPDATE, 1)
    s = s.rstrip(u'\n') + u'\n' + BACKLOG_127_NEW.strip(u'\n') + u'\n'
    write(p, s)


def patch_changelog():
    p = os.path.join(REPO, 'CHANGELOG.md')
    s = read(p)
    anchor = u'## [Unreleased]\n'
    assert s.count(anchor) == 1
    assert u'### 测试（R91' not in s
    write(p, s.replace(anchor, anchor + CHANGELOG, 1))


CHANGELOG = u'''### 测试（R91）

- 删掉 `UIInteractionProbeTests.testDragSelectExpandsSelectionInsideTheRealList` 与
  `MouseSynthesizer.drag`：它测的拖选手势在 D-034 就被决定不做，而它把整卷在屏判据挡在门外 ——
  合成 `.leftMouseDragged` 一进 `window.sendEvent` 就进 `NSCoreDragManager _dragUntilMouseUp`
  的模态循环（等窗口服务器的真 mouseUp，抬起排在下游），本机 3/3 次 180 秒收不掉、有结论 0。
  ⇒ 修完第一次跑到 `%s`。
- 帧间隔判据加**通道证人**：`CADisplayLink` 空转拿不到 tick 就报 `FRAME_CHANNEL baseline_n=…` 并 skip
  （这台机器现在显示器睡着 ⇒ 0 个样本不配判产品掉帧，也不配判通过）。地板一条没放宽。
- 新增机制级守卫 `SidebarListSelectionTests.testProbeSuiteNeverSynthesizesADragSession`
  （扫事件类型 `(.leftMouseDragged`，并要求 `DRAG-LIMIT` / `FRAME_CHANNEL` / 解释块三样都在）。
- `scripts/probe_coverage_expectations.json` 删掉那条 STALE 登记（是 `probe_coverage_gate` 自己报的）。

### 仪器（R91，仓库外）

- `r91_focus_visual.py`（焦点环/选中带在捕获帧里的可见性）、`mutate_r91_zombie.py`（%s）、
  `verify_r91.sh`（在屏卷按 CI 原样跑并断言"必须跑到 %s 条结论"）。

### Docs（R91）

- BACKLOG **125 结案**（合成拖拽在进程内做不到：撤 + 读数 + 守卫）；93 本机侧结案；
  92 更新（登记里那句 runner 成因写错，但改口要等下一次 CI）；126 加两格数据点
  （选中态黑带跨两条离屏路径、焦点环零墨；真机那一腿 NOT-RUN）；新开 **127**
  （一行两个半宽 `KeyViewProxy`，第一次跑完就红，本轮只点名不定性）。

''' % (PROBE_TALLY, KNIFE_LINE, PROBE_EXECUTED)

STATE_ANCHOR_HINT = '最后更新：2026-10-16 11:20（本地 · R90 / 第 92 轮收尾：'


def patch_state():
    p = os.path.join(REPO, 'AGENT_STATE.md')
    s = read(p)
    assert s.count(STATE_ANCHOR_HINT) == 1, u'STATE 头部锚点不唯一'
    new_head = (u'最后更新：2026-10-16 12:25（本地 · R91 / 第 93 轮收尾：**追了五轮的'
                u'"CI 上一条在屏判据都没跑完"，成因是一条我以为删掉了、其实没删的探针** —— '
                u'D-034 的正文写着"原来那条拖选探针删除并在原位置留了一段解释"，解释在，'
                u'函数也在：`git log --all -S "func testDragSelect…"` 只有 9d7b5ca 一次增、零次删'
                u'（U-206）。它这六天做的事是把整卷挡死：本机三遍都是 180 秒被掐、心跳 2、有结论 0，'
                u'`sample` 给出栈 `sendEvent → NSCoreDragManager _tryCatchDragUntilMouseUp → '
                u'CoreDragStartDraggingAsync → _BlockUntilNextEventMatchingListInMode` —— '
                u'CoreDrag 等的是窗口服务器的真 mouseUp，而探针把 mouseUp 排在 `sendEvent` 下游 ⇒ '
                u'进程内无解。我第一版"压到 2pt 阈值内"的修法被**第二次测量**撤掉（栈一模一样，'
                u'U-207）。⇒ 撤掉合成拖拽（连工具函数），限制打成 `DRAG-LIMIT` 读数，'
                u'机制级守卫 `testProbeSuiteNeverSynthesizesADragSession` 钉住事件类型（牙 %s）。'
                u'**修完第一次跑到 %s**。另两格：帧间隔判据加了 `FRAME_CHANNEL` 通道证人'
                u'（这台机器显示器睡着 ⇒ 0 个样本不配判产品，地板一条没放宽，U-209）；'
                u'看图发现**亮档基线帧里被选中的那一行是纯黑色带（2/255）且整帧零蓝**，'
                u'与在屏探针自己拍的帧同形 ⇒ 两条离屏路径共有的盲区，进 126；'
                u'真机截图那一腿 NOT-RUN（`screencapture` 全黑、`UserIsActive 0`）。'
                u'新开 **127**：一行两个半宽 `KeyViewProxy` —— 第一次跑完就红，本轮只点名不定性，'
                u'所以推上去之后 main 带着一朵**有名字的红**。'
                u'验证：非台账文件 %s 个、产品 0 个；构建告警 %s；全量 %s（exit %s）；脚本 %s（exit %s）；'
                u'电池 %s；帧 %s 张 + 对账 %s；没跑的：%s。'
                u'**下一轮第一件事：读 R91 的 CI（在屏那一卷第一次在 runner 上跑到几条 + '
                u'coverage 门会不会报"说跑不了却跑到了"）+ BACKLOG 127 的正对照**）\n\n'
                u'> 上一轮（R90 / 第 92 轮收尾）原文开头：' + STATE_ANCHOR_HINT) % (
        KNIFE_LINE, PROBE_TALLY, TOUCHED, BUILD_WARNINGS, SWIFT_TAIL, SWIFT_EXIT,
        SCRIPTS, PY_EXIT, KNIFE_LINE, FRAMES, BASELINE, NOT_RUN_LINE)
    write(p, s.replace(STATE_ANCHOR_HINT, new_head, 1))


REPORT_U = (u'U-206 是**台账里的"已完成"断言必须能被机器复查**（D-034 写着探针已删除，'
            u'`git log --all -S` 证明从没删过 ⇒ 覆盖登记的 STALE 格现在管着这件事，而它是本轮我自己漏的）；'
            u'U-207 是**"我以为压到阈值内就安全"不是证据**（第一版修法被第二次测量撤掉，栈一模一样）；'
            u'U-208 是**电池要把"断言红"与"编译坏"分开**（刀坏了也会被读成判据有牙），'
            u'同一轮还复发了一次 `| tail` 的退出码；'
            u'U-209 是**0 个样本既不能判产品也不能判通过**（采样通道要先当证人）；'
            u'U-210 是**扫描区域必须由被测量自己报**（"整列最暗 6 行"量到窗口外的黑底 ⇒ 那三个数作废）；')


def patch_final_report():
    p = os.path.join(REPO, 'AGENT_FINAL_REPORT.md')
    s = read(p)
    old = u'| 阶段二 **83 轮**审计（R9–R90，含 29d；'
    assert s.count(old) == 1, u'FINAL_REPORT 轮数锚点不唯一'
    s = s.replace(old, u'| 阶段二 **84 轮**审计（R9–R91，含 29d；', 1)
    old = u'以 `curve_from_ledger.py` 的 `PHASE2 n=83` 为准）'
    assert s.count(old) == 1, u'FINAL_REPORT 曲线锚点不唯一'
    s = s.replace(old, u'以 `curve_from_ledger.py` 的 `PHASE2 n=84` 为准）', 1)
    old = u'| 视觉台账 | U-31 … U-205（174 条；'
    assert s.count(old) == 1, u'FINAL_REPORT U 计数锚点不唯一'
    s = s.replace(old, u'| 视觉台账 | U-31 … U-210（179 条；', 1)
    old = u'| 决定台账 | D-069 … **D-148**'
    assert s.count(old) == 1, u'FINAL_REPORT 决定台账锚点不唯一'
    s = s.replace(old, u'| 决定台账 | D-069 … **D-149**', 1)
    old = u'**M100–M504**（阶段二 404 支；'
    assert s.count(old) == 1, u'FINAL_REPORT 刀数锚点不唯一'
    s = s.replace(old, (u'**M100–M509**（阶段二 409 支；**R91 的 %s**'
                        u'（M509 那一刀**故意要逃**：它把守卫从"扫事件类型"退回"扫函数名"，'
                        u'逃掉才说明名字级守卫能被改名绕过）；'
                        % KNIFE_LINE), 1)
    old = u'自评曲线（**83 轮**，Round 9–90，含 29d 那一轮边界轮；'
    assert s.count(old) == 1, u'FINAL_REPORT 曲线段锚点不唯一'
    s = s.replace(old, (u'自评曲线（**84 轮**，Round 9–91，含 29d 那一轮边界轮；' + CURVE +
                        u'；**后面那几段 `）：PHASE2 n=…` 是前几轮留下的同一条曲线的历史读数**'
                        u'（n 依次小 1，不是并存的两把尺，也不是本轮没算完））：'), 1)
    anchor = u'U-200 是**退出码与尺的身份都要当场核对**'
    assert s.count(anchor) == 1, u'FINAL_REPORT 的 U 段插入锚点不唯一'
    s = s.replace(anchor, REPORT_U + anchor, 1)
    write(p, s)


def fix_curve():
    proc = subprocess.run([sys.executable, '.scratch/motion-audit-2/curve_from_ledger.py'],
                          cwd=REPO, capture_output=True, text=True, timeout=600)
    if proc.returncode != 0:
        raise SystemExit(u'曲线守卫退出 %d：%s' % (proc.returncode, (proc.stdout + proc.stderr)[-1200:]))
    picked = [l for l in proc.stdout.splitlines() if l.startswith('GAPS=') or l.startswith('PHASE2')]
    real = ' '.join(picked).strip()
    if not real:
        raise SystemExit(u'曲线守卫没打 GAPS=/PHASE2 行：%s' % proc.stdout[:400])
    if 'n=84' not in real:
        raise SystemExit(u'曲线不是 84 轮（本轮正文没被识别为一个轮次？）：%s' % real[:200])
    for rel in ('AGENT_VISUAL_ITERATION.md', 'AGENT_STATE.md', 'AGENT_FINAL_REPORT.md'):
        path = os.path.join(REPO, rel)
        t = read(path)
        if CURVE not in t:
            print(u'  %s 里没有占位符' % rel)
            continue
        write(path, t.replace(CURVE, real))
        print(u'  %s：占位符已替换' % rel)
    print(u'  CURVE(现跑)=%s' % real[:160])


def patch_final_report_round_range():
    p = os.path.join(REPO, 'AGENT_FINAL_REPORT.md')
    s = read(p)
    proc = subprocess.run([sys.executable, '.scratch/motion-audit-2/curve_from_ledger.py'],
                          cwd=REPO, capture_output=True, text=True, timeout=600)
    if 'GAPS=none' not in proc.stdout:
        raise SystemExit(u'曲线守卫报了缺轮 ⇒ 区间格子不许写：%s'
                         % [l for l in proc.stdout.splitlines() if l.startswith('GAPS')])
    m = re.search(r'PHASE2 n=(\d+) rounds=(\d+)\.\.(\d+)', proc.stdout)
    if not m:
        raise SystemExit(u'曲线守卫没打出 PHASE2 n=… rounds=… ⇒ 这一格不许手抄')
    n, lo, hi = int(m.group(1)), int(m.group(2)), int(m.group(3))
    if n - (hi - lo + 1) not in (0, 1):
        raise SystemExit(u'PHASE2 n=%d 与 rounds=%d..%d 对不上：%s' % (n, lo, hi, m.group(0)))
    fresh = (u'`AGENT_VISUAL_ITERATION.md` Round %d–%d（%d 条读数：编号 %d–%d 共 %d 个，'
             u'外加 29d 那一轮边界轮；区间与条数都从曲线守卫的 `rounds=…`/`n=…` 推）'
             % (lo, hi, n, lo, hi, hi - lo + 1))
    pattern = re.compile(u'`AGENT_VISUAL_ITERATION\\.md` Round \\d+–\\d+（\\d+ 条读数：[^）]*）')
    hits = pattern.findall(s)
    if len(hits) != 1:
        raise SystemExit(u'那一格按形状命中 %d 次（要求 1）⇒ 不许盲改' % len(hits))
    if hits[0] == fresh:
        print(u'  区间格子已经是最新值')
        return
    write(p, pattern.sub(lambda _m: fresh, s, count=1))


def refuse_stray_placeholders():
    bad = [name for name, blob in sorted(globals().items())
           if isinstance(blob, str) and name.startswith(
               ('BACKLOG_', 'CHANGELOG', 'UI_AUDIT', 'DECISION', 'SECTION', 'ROUND_HEAD', 'REPORT_U'))
           and (u'%s' in blob or u'%d' in blob)]
    if bad:
        raise SystemExit(u'这些正文里还留着没被格式化的占位符：%s ⇒ 拒绝落盘' % u'、'.join(bad))


refuse_stray_placeholders()

STAGES = {
    'A': (patch_visual_iteration, patch_ui_audit, patch_decisions, patch_backlog, patch_changelog),
    'B': (patch_state, patch_final_report),
    'C': (lambda: fix_curve(),),
    'D': (patch_final_report_round_range,),
    # E：只补 A 里被锚点拦下的那两步（stage A 重跑会撞 `## Round 91 已经写过了`，那是故意的）。
    'E': (patch_backlog, patch_changelog),
}


def main():
    stage = sys.argv[1] if len(sys.argv) > 1 else 'A'
    for fn in STAGES[stage]:
        fn()
        print(u'已写 %s' % fn.__name__)
    print(u'%s：%s' % (KNIFE_TOTAL, u', '.join(u'%s=%s' % (t, k) for t, _n, k in KNIVES)))


if __name__ == '__main__':
    sys.exit(main())
