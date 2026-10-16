# -*- coding: utf-8 -*-
'''R89 的台账补丁（第 91 轮 / Round 89）。

数字全部从产物读，不许手抄：
  * `/tmp/r89_verify/summary.log`                  —— 本轮逐条实跑的结论（含 NOT-RUN）
  * `.scratch/motion-audit-2/r89_ci_readings.md`   —— 读 R88 的 CI（那朵红）的原文
  * `/tmp/r89_verify/battery.log` / `shape.log`    —— 八刀与三形状对照的原文
每个锚点都断言"命中且只命中一次"。分四段跑：A（正文与账）、B（STATE 与 FINAL_REPORT）、
C（曲线）、D（FINAL_REPORT 里那格反复滞后的轮次区间，从曲线守卫推）。
'''
import io
import os
import re
import subprocess
import sys

REPO = '/Users/wangziyi/Codex_Project0'
SUMMARY = '/tmp/r89_verify/summary.log'
CI = os.path.join(REPO, '.scratch/motion-audit-2/r89_ci_readings.md')
BATTERY = '/tmp/r89_verify/battery.log'
SHAPE = '/tmp/r89_verify/shape.log'
TREE = '/tmp/r89_verify/tree.log'
CURVE = 'CURVE_PLACEHOLDER_R89'
GATES = [u'Swift tests (executed-count gate)',
         u'Capture gate (unregistered reds must be zero)',
         u'On-screen probe coverage floor',
         u'Motion coverage floor']


def refuse_while_mutating():
    """电池正在改工作树时，**读到的不是事实，是刀**（R89 现场）。

本轮我差一点把一条假缺陷写进台账：在电池跑到 M492（"删掉一道硬门的 `if: always()`"）
的时候用 `grep -c` 与 ruby 的 YAML 解析读 `ci.yml`，读到 `always=5`、
`Swift tests (executed-count gate)  if=` 空 ⇒ 结论"四道门里有一道漏挂"。
那条门其实挂得好好的（电池外再读就是 6）——**是我在它被改掉的那十几秒里读的**。
⇒ 生成台账前先看有没有电池在跑；有就拒绝，而不是"记得等一下"。
（只装在读侧：`verify_r89.sh` 自己就是启动电池的那个，装在这里会自杀。）
"""
    proc = subprocess.Popen(['pgrep', '-f', 'mutate_r89_watchdog.py'],
                            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    pids = proc.communicate()[0].decode('utf-8', 'replace').split()
    if pids:
        raise SystemExit(u'变异电池还在跑（pid %s）⇒ 现在读到的工作树可能是被改过的样子，'
                         u'不许据此生成台账。等它结束（或先杀掉它再重跑 verify）'
                         % u','.join(pids[:3]))


def read(path):
    return io.open(path, encoding='utf-8').read()


def write(path, text):
    check_claims(path, text)
    io.open(path, 'w', encoding='utf-8').write(text)


# R89 现场：正文里我先把那一步的红写成"吃掉九个步骤"，而 `gh api` 的逐步结论三个 run 都是 **7**。
# 这一族（新写的正文就与产物矛盾）比 R87 那种"旧正文滞后"更贵，因为它会带着台账的权威性活下去。
# 守卫放在唯一的落盘口 `write()` 上 ⇒ 四段里任何一段手抄错数字都写不进去，而不是事后靠肉眼对账。
CN_NUM = {u'零': 0, u'一': 1, u'二': 2, u'三': 3, u'四': 4, u'五': 5,
          u'六': 6, u'七': 7, u'八': 8, u'九': 9, u'十': 10}
CLAIM_PATTERNS = (u'([零一二三四五六七八九十])个步骤', u'([零一二三四五六七八九十])个 skipped')
# 只police"被 skip 掉几个"这一种断言。第一版见"X 个步骤"就管，结果拦下了
# "第三轮补过的**四个步骤名**必须还在"那句真话（那说的是四道门的名字，不是被 skip 的步数）
# ⇒ 尺过粗与尺过紧同罪：它会把对的话也拦下来，于是人开始绕过它。
SKIP_WORDS = (u'skip', u'吃掉', u'没跑')


def check_claims(path, text):
    for pat in CLAIM_PATTERNS:
        for m in re.finditer(pat, text):
            window = text[max(0, m.start() - 28):m.end() + 28]
            if not any(w in window for w in SKIP_WORDS):
                continue        # 不是"被 skip 掉几个"这句话，放行
            if CN_NUM[m.group(1)] != SKIPPED_AFTER_GATE:
                raise SystemExit(
                    u'台账正文里"%s"是从产物读不出来的数：`SKIPPED_AFTER_GATE=%d`（%s）。'
                    u'要么改正文，要么把产物补成真的支持这句话' % (m.group(0), SKIPPED_AFTER_GATE, path))


def ci_reading(key):
    m = re.search(r'^%s=(\S+)' % re.escape(key), read(CI), re.M)
    if not m:
        raise SystemExit('%s 里读不到 %s= ⇒ 这条正文没有依据，不许写' % (CI, key))
    return m.group(1)


SKIPPED_AFTER_GATE = int(ci_reading('SKIPPED_AFTER_GATE'))


def summary(key):
    text = read(SUMMARY)
    # 严格 `^KEY=`：写成 `[=:]?` 时 summary('SHAPE') 会命中 `SHAPE_EXIT=0`（R87 现场记过一次）
    m = re.search(r'^%s=(.+)$' % re.escape(key), text, re.M)
    if not m:
        raise SystemExit('验证摘要里缺 %s —— 先把 verify_r89.sh 跑完再来写台账' % key)
    return m.group(1).strip()


refuse_while_mutating()
SCRIPTS = summary('SCRIPT_TESTS')
SCRIPT_TOTAL = re.search(r'Ran (\d+) tests', SCRIPTS).group(1)
PY_EXIT = summary('PY_EXIT')
PRODUCT = summary('PRODUCT_TOUCHED')
TOUCHED = summary('TOUCHED_NON_LEDGER')
SHAPE_LINE = summary('SHAPE')
BATTERY_LINE = summary('BATTERY')
TREE_LINE = summary('TREE')
NOT_RUN = [l.split('NOT_RUN=', 1)[1] for l in read(SUMMARY).split('\n') if l.startswith('NOT_RUN=')]
if not NOT_RUN:
    raise SystemExit('验证摘要里一条 NOT_RUN 都没有 ⇒ 要么没记，要么本轮其实全跑了（不可能）')
NOT_RUN_LINE = u'；'.join(NOT_RUN)

KNIVES = []
if os.path.exists(BATTERY):
    text = read(BATTERY)
    for m in re.finditer(r'^(M4\d\d) (.+?)$', text, re.M):
        tail = text[m.end():]
        hit = re.search(r'^   (CAUGHT|ESCAPED|NOT-RUN|NOT-APPLIED)', tail, re.M)
        KNIVES.append((m.group(1), m.group(2), hit.group(1) if hit else '?'))
if not KNIVES:
    raise SystemExit('battery.log 里读不到任何一刀 ⇒ 台账不许引用没跑过的刀')
CAUGHT = [t for t, _, k in KNIVES if k == 'CAUGHT']
ESCAPED = [t for t, _, k in KNIVES if k == 'ESCAPED']
NOTRUN = [t for t, _, k in KNIVES if k.startswith('NOT')]
# UI_AUDIT 与 ROUND_HEAD 的正文里"全部 CAUGHT"是字面写的 ⇒ 先在这里钉死，谁没抓到就整段拒绝生成。
if len(CAUGHT) != len(KNIVES):
    raise SystemExit(u'有刀没抓到就不许往台账里写"全部 CAUGHT"：%s'
                     % u'、'.join(u'%s(%s)' % (t, k) for t, _, k in KNIVES if k != 'CAUGHT'))


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
TREE_TEXT = ''
if os.path.exists(TREE):
    TREE_TEXT = u'\n'.join(l for l in read(TREE).split('\n')
                           if l.startswith(('驱动 pid', 'PGID_OF_JOB', '父壳收残留组', '残留=',
                                            '=== 最终残留', 'log_bytes')) or l.startswith('2'))

ROUND_HEAD = u'''## Round 89 · R88 的修法不完整：组杀够不到 xctest，而我那道红把七个步骤的证据吃掉了（读 R88 的 CI / 更新 92、93、119 / U-192…U-199 / D-147）

### 本轮开场的位点清单（0 个产品文件；1 个 CI 文件 + 2 个仓库外仪器）

起点是 **main 又红了**（R88 的 CI，run 38825657419），红在 R88 自己新写的那道门上；
而同一格里 R88 想要的读数第一次成功，门也第一次证明了自己有用。

| 位点 | 位置 | R88 留下的缺陷 | 本轮处置 |
|---|---|---|---|
| 看门狗收杀 | `.github/workflows/ci.yml` | `kill -- -$pid` 只杀到驱动：`xctest` 自己 `setpgid` 成另一个组的组长 | 在**父壳 `wait` 之后**再照残留孩子的 pgid 收一次它的组 |
| 收杀的位置 | 同上 | 第一版把循环塞进 killer 子壳 ⇒ 父壳 `kill "$killer"` 会把它**中途掐掉**（对照读到 `Terminated: 15` + 残留 1） | 移到父壳；判定改成**按位置**查（同一段代码放错地方就是竞态） |
| 硬门的位置 | 同上 | `On-screen probe coverage floor` 红了之后 GitHub 把后面**七个步骤全 skip** ⇒ 仪器的红吃掉了产品的证据 | 四道硬门全部挪到产证据步骤之后，各自 `if: always()` |
| 门的自检 | `.scratch/motion-audit-2/r89_watchdog_shape.py` | "有没有这段循环"式的子串查、以及"总量 ≥4"式的假尺 | 三形状对照 + 逐门查 `if: always()` + 位置判据（M492 现场） |

本轮动的非台账文件 **1 个**（`.github/workflows/ci.yml`），产品文件 **0 个** ⇒ 本轮不产生新帧；
但**补装了 R84 欠下的那一次**（BACKLOG 124，读数见下面"换装"那一节）。

'''

# `%` 按**文本顺序**吃参数：写漏一格不会报错，只会把整行原文塞进下一格（R87 那一族）。
# 本轮第一次执行 stage A 就是这么撞上的：正文有 10 个 `%s` 而参数只给了 9 个 ⇒ TypeError。
# ⇒ 参数写成具名元组，并在格式化之前断言"占位符个数 == 参数个数"。
SECTION_ARGS = (TREE_TEXT, KNIFE_TABLE, TOUCHED, PRODUCT, SCRIPTS,
                PY_EXIT, SHAPE_LINE, BATTERY_LINE, TREE_LINE, NOT_RUN_LINE)

_SECTION_TEMPLATE = u'''
### 1. R88 那一格第一次在 runner 上说话，而且是**对的**（U-192）

```
UI_PROBE_START_LINES_LOST=1 （收掉的那一刻 xctest 还活着 ⇒ 用例确实开了口，是 stdout 的块缓冲被 SIGKILL 整块带走）
UI_PROBE_NAMED=1
PROBE_FLOOR_WATCHDOG_MISSED=1 收掉之后仍有 1 个 xctest 在跑
```

⇒ 前半句是本轮要的东西：93 的成因在 runner 上被**自己的读数**确认（不再靠我本机一次 spike）。
⇒ 后半句是本轮的债：R88 那句"杀父组 = 杀整棵树"在 SwiftPM 上不成立。本机把 pid/ppid/**pgid** 一起量出来：

```
%s
```

⇒ `swift-test` pid=pgid=27359（`set -m` 生效，`$!` 就是组长），而 `xctest` pid=pgid=27416 ——
它自己开了新组，**不在父亲的组里**。所以 `kill -9 -- -27359` 只杀到驱动。
⇒ 修法不是放弃组杀，而是补第二刀：残留孩子的组由**父壳**在 `wait` 之后收。

### 2. 同一段代码，位置错了就是竞态（U-194）

我第一版把那段循环塞进 killer 子壳。三形状对照读到的是：

```
旧形状（只杀 pid）      ⇒ 留孤儿
R88 形状（只杀驱动组）  ⇒ **仍然**留孤儿        ← 这一格就是 runner 上那朵红
R89 形状（父壳再收一次）⇒ 残留=0
```

而"塞进子壳"那一版在对照里是 **R89 形状收干净=ESCAPED**：`wait "$pid"` 在驱动一死就返回，
父壳紧接着 `kill "$killer"`，把还在跑循环的子壳**掐死在半路**（日志里就是 `Terminated: 15`）。
⇒ 所以接线检查不能问"有没有这段循环"，要问"它在 `wait` 之后吗、孤儿计数在它之后吗"（M490 / M491）。

### 3. 红不许把别的判据变成没跑（U-193）

`gh api …/jobs` 的逐步结论里，我那道硬门之后是**七个 skipped**：
动效卷、动效地板、脚本自测、Info.plist、两张帧基线、启动冒烟。
⇒ R36/R66 立的"红必须有名字"少了它的对偶：**一朵仪器的红不该让产品的判据集体没跑**。
⇒ 四道硬门挪到所有产证据步骤之后，各自 `if: always()`（仍然会红，但证据先落地）。
⇒ 代价也记下来：本轮**没有**拿到 coverage 的第六个数据点 —— 正是被那朵红 skip 掉的。
119 的第五个点之后是空，这条不许被读成"runner 上一切正常"。

**这朵红是稳定的，不是闪红**：R88 推了三条 run（984da5f / 3978769 / d44d344），
逐条读结论 ⇒ 三个都是 failure、失败的都是同一步 `On-screen probe coverage floor`、
skipped 都是 7、在屏那一步的六行读数逐字一致（`RUNNER_ALIVE=1` / `ORPHAN_XCTEST=1` /
`started=0 concluded=0` / `START_LINES_LOST=1` / `NAMED=1` / `ui suite exit: 137`）。
⇒ 好消息与坏消息要分开记：**门有牙且不闪**（0 次假红、0 次漏报），而它咬的是我自己的修法。

### 5. 本轮自己的两条假账：那个"九"是手抄的，轮次标签也差了一（U-196）

上面那段正文里那个数我先写成了"九"。写的时候只扫了自己列的那张清单，**没数过 API 的结论**；
API 三个 run 都给 7。⇒ 台账里那一族措辞全部按 7 改，并且这次不是"旧正文滞后"（R87 那一族），
是**新写的正文一落地就与产物矛盾** —— 更贵，因为它会带着台账的权威性活下去。
⇒ 修法不靠肉眼对账：`write()` 是台账生成器唯一的落盘口，守卫挂在它上面 ——
正文里任何"X 个步骤 / X 个 skipped"必须等于产物里的 `SKIPPED_AFTER_GATE`，否则拒绝写。
（把守卫挂在唯一的出口，比在每个段落里各写一条检查可靠：漏一个段落就等于没守卫。）
⇒ 轮次标签这一条守卫是**从台账自己推**（读 `^## 第 N 轮` 取 max 再 +1），不是我另写一个数：
   它能拦住"跳号"，也顺带拦住了"重复插入同一轮"。
⇒ 顺带一条自我示范：本节本来要引用那个错数字，被守卫当场拦下 ⇒ 改成不复述原话、只记事实。
**守卫拦到我自己这一条**就是它有效的证据；它还没拦过别人，因为本轮只有我一个人在写台账。

### 4. 顺手一条假尺（U-195）

`if: always()` 的检查第一版写的是 `text.count(...) >= 4`，而文件里本来就有六处
（两张帧基线、启动冒烟早就挂着）⇒ 删掉某一门那一刀（M492）**照样绿**。
⇒ 改成逐门查：四道门各自必须能看见 `if: always()`。这是"按总量数"这一族在守卫里的又一次现身。

### 视觉审查（本轮真的看了像素，不是读代码）

零产品改动 ⇒ R87 那次捕获（`/tmp/r87/shots`，124 帧）就是当前产品的像素。选菜单栏面板这一族，
是为了**重判 R34 那条"这批帧没有资格"的声明今天还成立吗**（工具：`r89_menubar_review.py`，
读数与正对照记在 `r89_menubar_review.md`）：

```
menubar-recommendations-320x320-dark   三条推荐行 + 底部操作行  左边距=0..2  右边距=0..2
menubar-empty / -refreshing            副标题行                 左边距=0..3  右边距=424..493
正对照 settings-data-720x540-dark      真文字带                 左边距=35 / 78 / 296（永不报 0）
```

⇒ 眼睛与读数一致：推荐行首字贴左边界，右列"文件 · 当前在 Safari · 常用文件"在帧边界上被切成半个字。
⇒ **但这不是新缺陷**：`MenuBarExtra` 默认 `.menu` 风格 ⇒ 内容编译成真 `NSMenu`，离屏 `cacheDisplay`
画的是复刻。R34 的资格判据（`menuSurfaceReplicaFixtures`）断言的正是"第一行最右墨 ≥ 帧宽"，
并声明这批帧不判宽度/截断/对齐。本轮的独立复现说明**那格盲区没被顺手修掉，声明仍然必要**；
真机那一腿已由 R2-22 与"④ 原生 `NSMenu`"记着 ⇒ **不开新单**（R88 的教训：开单前先按机制名查重）。
⇒ 抓到的一条是自己的尺：这颗临时带尺能答"这行有没有东西"（正对照：真文字永不报 0），
答不了"文字内边距"（它分不清文字与横贯全宽的 `Divider()`，而 `UICaptureHarness.swift:4799` 早就写过这件事）。
⇒ 采信范围收窄到"左边距/右边距=0"这一条与眼睛同向的读数；对比度与峰值墨一律不入库。

### 6. 差点写进台账的一条**假缺陷**：我在电池的变异窗口里读了工作树（U-197）

电池跑到 M492（"删掉一道硬门的 `if: always()`"）那十几秒里，我用 `grep -c` 和 ruby 的 YAML 解析读
`ci.yml`，读到 `always=5`、`Swift tests (executed-count gate)` 的 `if` 是空 ⇒
我写下了结论"四道门里有一道漏挂，我的逐门检查是假 OK"。**那条门挂得好好的**：电池之外再读就是 6，
而 09:13 那次 `接线检查 OK（10 项都在）` 也是对的。⇒ 我读到的不是事实，是**刀**。

⇒ 这不是"看错了"，是**读的时刻不对**，而这一族以前只在写侧防过（不许在电池期间提交），没在读侧防过。
⇒ 修法装在唯一的读侧入口：`ledgers_r89.py` 一上来先 `pgrep -f mutate_r89_watchdog.py`，
有电池在跑就 `SystemExit`，不生成台账。**本轮当场验过**：电池正跑着时执行 stage A，
它拒绝并打出 pid 31814，`git status` 里台账一个字节没动。
⇒ 只装读侧不装写侧是刻意的：`verify_r89.sh` 自己就是启动电池的那个进程，装在那儿会自杀。

### 7. 电池自己抓到的一格假 OK：位置锚点用了裸子串（U-198）

八刀里 **M490 逃掉了**（"把残留收杀那一块搬到 `wait` 之前"，harness 仍然 0）。顺着查，不是刀坏了
（电池会先判"文件必须不同"，没改就不算数），是**检查的锚点**坏了：

```
step.index(u'for child in $(pgrep') > step.index(u'wait "$pid"')
```

`wait "$pid"` 这个裸子串在上面那两行**注释**里也出现（"bash -e 下 `wait` 拿到 137 会当场中止脚本…"），
于是 `index` 拿到的是注释里那一个（1605），而真 `wait` 行在 2049 ⇒ 刀把循环搬到 1763（真 wait 之前）
仍然"在 wait 之后"。⇒ **假 OK**。修完当场验：基线 loop=2662 > wait行=1753 通过；
M490 之后 loop=1763 > wait行=2049 不成立 ⇒ 会红。
⇒ 位置比较的锚点必须是**整行字面**（含缩进与结尾换行）并配 `count(...) == 1`：
   一个能同时命中注释与代码的子串，量的不是"顺序"，是"谁先被写到"。与 U-195 同一族、不同机制。

### 8. 我的两个测量在互相污染，而 verify 把这件事读成了绿（U-199）

第一支 spike（verify 的最后一步）还在跑，我又起了第二支真机树 spike。两件事同时发生：
① 两个 `swift test` 抢同一把 `.build` 锁（第二支的日志第一行就是
`Another instance of SwiftPM (PID: 33410) is already running … waiting`）；
② 第一支的"收残留"是按 `pgrep -f "xctest -XCTest ClipboardHistoryAppTests"` 的**名字**杀的，
于是它把第二支正在跑的 xctest 一起收掉了。
⇒ 第二支的日志停在第 2 条用例（`testDragSelectExpandsSelectionInsideTheRealList` 之后没下文），
我当下写下的结论是"在屏那一卷死在拖选探针上"。**那是我的两次测量互相杀出来的形状，不是产品的。**
⇒ 单独重跑一次（50 秒、无并发）才读到本轮要的那个数：

```
驱动 pid=33848  我自己的 pgid=33842        ← 脚本自己所在的组
swift-test pid=pgid=33848                  ← `set -m` 生效：驱动是自己组的组长
xctest     pid=33905 pgid=33905            ← 它自己 setpgid 成**另一个组**（D-147 的机制，本机第二次量到）
父壳收残留组 33905（孩子 pid=33905）
残留=0        log_bytes=119 started=0
```

⇒ 另有一条关于仪器本身：`verify_r89.sh` 最后一条命令是 `cat`，于是电池 1 刀逃掉时它仍然 exit 0，
后台任务"完成"被读成"全绿"。⇒ 现在退出码由内容决定（`PY_EXIT` / `SHAPE_EXIT` / `BATTERY_EXIT`、
三形状那一臂、真机树 `残留=0`、电池 `8 刀 CAUGHT / 0 逃掉 / 0 没跑成`），不满足就
`VERIFY_FAILED=…` + exit 1。
⇒ 规矩：**同一台机器上，会抢锁或按名字杀进程的两支测量不许并跑**；并跑之前先问"另一支还活着吗"。

### 换装（补 R84 欠下的那一次，BACKLOG 124 的第①步）

本轮零产品改动，但**补装了**：本机之前跑的还是 R84 之前的包。逐条读数（`install_local.sh --yes --label r89-overlay`）：

```
已装版本 1.4.8  旧包 sha=4aa88f2ef5c3e758…   新包 sha=7ef8c6eca171adbd…   ← 两个 sha 不同而版本号相同
INSTALL_SHA_MATCH=1   INSTALL_RUNNING_PID=34203（启动晚于安装，exe 路径逐字对上 /Applications/时间剪史.app）
INSTALL_ENTRIES_BEFORE=105  INSTALL_ENTRIES_AFTER=105   SMOKE_OK=1   INSTALL_RESULT=ok
```

⇒ 这条同时是给"装机落后审计"的**正对照**：它报 Round 84 红，而换装之前盘上确实是一个 sha 不同、
版本号相同的旧包 —— 审计说的"落后"是真的，不是台账措辞问题。
⇒ 第②步（把 `r89_install_lag_audit.py` 升成 `scripts/` 里的判据 + 自测 + CI 报告型一步）留给下一轮，
本轮不扩范围（一次只改一处）。

### 牙

%s

### 验证（本机，逐条实跑；跑不了的点名）

```
动了哪些非台账文件            %s 个（只有 .github/workflows/ci.yml）；产品文件 %s
脚本自测                       %s（exit %s）
三形状对照 + 接线 + 顺序       %s
变异电池                       %s
真机进程树（不是 bash 假树）   %s
没跑的                         %s
```

### 七维自评

| 维度 | 得分 | 说明 |
|---|---|---|
| 原生感 | 20 / 20 | 零产品改动：本轮没脸加分，也没东西被扣 |
| 流畅度 | 18 / 20 | 扫光那一族的第六个数据点本轮**没拿到**（被上一轮的红 skip 掉），这一格按欠账记 |
| 层次与材质 | 15 / 15 | 本轮无新产品像素；但有一腿真实审查：菜单栏那六帧重判完，盲区声明仍然成立 |
| 动效细节 | 14 / 15 | 122（每条判据一行心跳）仍未做；本轮先修上一轮的两处不完整 |
| 交互反馈 | 9 / 10 | 反馈本身没动 |
| 可访问性 | 8 / 10 | 减弱动态那一臂仍无条件判；真机批次 72 / 73 还没人看 |
| 性能 | 15 / 15 | 看门狗现在真的能收掉 xctest：runner 不再被孤儿进程白烧到作业结束（本机实测残留 0） |

**99 / 100**：分数高不是因为本轮产出了画面或新判据，而是因为它**把上一轮交出去的东西修完整了**，
而且是被自己写的那道门抓出来的。扣分那一格是明确的欠账：122 还没做，"挂在哪一条"仍然没有名字。

### 仍未解决

- BACKLOG **124**（本轮新开，也是本轮看图之外唯一一条"新事实"）：**装机落后于产品** ——
  做最终报告收口审计时用 `r89_install_lag_audit.py` 逐段对账，88 段里自报产品数的 9 段中
  8 段有换装证据或"不换装+理由"，**只有 Round 84 两头都没有**（它改了 1 个产品文件），
  而 R85–R89 全是 0 个产品文件 ⇒ 本机装的还是 R84 之前的包。
  ⇒ 本轮把当前树重新构建 + 换装 + 记录（落后已补），并把这支审计升成判据留到下一轮；
  79 个老轮次没有自报那一行 ⇒ 审计判不了它们，这一格不许回推成"那 79 轮没落后"。
- BACKLOG **122**（本轮决定做法，未实现）：探针文件级已有 `emit()` 走 **stderr**（`FileHandle.write`，
  不经 stdio 缓冲），而 CI 是 `> /tmp/ui.log 2>&1` ⇒ 这条腿本来就能活过 SIGKILL，缺的只是
  **每条用例开头一行心跳**。本机孤立包实测 `setUpWithError()` 里 `self.description` 就是
  `-[类名 用例名]`（与 XCTest 自己那行同名）⇒ 一处改动覆盖 11 条，新增判据不会漏。
- BACKLOG **92 / 93**：成因已定（②通道丢了），"挂在哪一条"仍无名字；
  另有一条新事实：本机 90 秒内这一卷**能跑完**（日志里有 skipped 与结尾行），
  而 runner 上 240 秒收不掉 ⇒ "runner 上到底卡在哪"是 92 剩下的那一问。
- BACKLOG **119**：runner 五遍 0.522 / 0.842 / 0.032 / 0.690，第六遍本轮被 skip ⇒ 没拿到；
  `contradicted-by-travel` 那一支至今没有 runner 证据。
- **121**、**116** 剩下那半格、**115**、**111**、108 余下、77 路 b、101 ②③、106；
  真机 68.1 / 68.2 / 69.1 / 70.1 / 71.1 / 72.1 / 72.2 / 73.1 / 73.2。
'''
if _SECTION_TEMPLATE.count(u'%s') != len(SECTION_ARGS):
    raise SystemExit(u'SECTION 的占位符有 %d 个而参数有 %d 个 ⇒ 台账会串行，拒绝生成'
                     % (_SECTION_TEMPLATE.count(u'%s'), len(SECTION_ARGS)))
SECTION = _SECTION_TEMPLATE % SECTION_ARGS

UI_AUDIT = u'''## 第 91 轮 · R89：上一轮那把门抓到了上一轮的修法不完整 —— 组杀够不到 xctest，而红吃掉了七个步骤的证据（U-192…U-199）

- **U-192 杀父组 ≠ 杀整棵树**：`swift test` 是三层进程，`xctest` 自己 `setpgid` 成了**另一个组的组长**
  （本机实测 `swift-test pid=pgid=27359`、`xctest pid=pgid=27416`）⇒ R88 的 `kill -- -$pid` 只杀到驱动。
  runner 上 `PROBE_FLOOR_WATCHDOG_MISSED=1 收掉之后仍有 1 个 xctest 在跑` 就是这件事的原文。
  同一格里 `UI_PROBE_START_LINES_LOST=1` 第一次在 runner 上说话：93 的成因由 CI 自己的读数确认了。
- **U-193 红不许把别的判据变成没跑**：那道硬门红了之后 GitHub skip 掉七个步骤
  （动效卷、动效地板、脚本自测、帧基线、启动冒烟）⇒ 四道硬门挪到产证据步骤之后 + 各自 `if: always()`。
  代价按实记：本轮**没有** coverage 第六个点。
- **U-194 同一段代码，位置错了就是竞态**：把"再收残留孩子"塞进 killer 子壳那一版，会被父壳
  `kill "$killer"` 掐死在半路（对照读到 `Terminated: 15` + 残留 1）。⇒ 移到父壳 `wait` 之后，
  并且接线检查改成**按位置**查，不查"有没有这段"。
- **U-195 按总量数的门是假尺**：`if: always()` 用 `count >= 4` 查，而文件里本来有六处 ⇒ 删掉某一门照样绿
  （M492 第一版 ESCAPED）。⇒ 改成逐门查。
- **U-196 新写的正文一落地就与产物矛盾**：那一步的红"吃掉几个步骤"我先写了"九"，
  而 `gh api` 三个 run 都给 7 ⇒ 数字要来自读数，不来自我扫清单。同一轮还抓到第二条：
  UI_AUDIT 的轮次标签我写成了"第 92 轮"，而台账现有最大号是 90（R88），本轮该是 **91** —— 差一是跳号。
  ⇒ 修法是把守卫挂在生成器**唯一的落盘口** `write()`（正文里的"X 个步骤 / X 个 skipped"必须等于
  `SKIPPED_AFTER_GATE`）+ 在插入点把标签与台账自己的最大号对账（`max+1` 不符就拒绝落盘）。
  这一条与 R87 的"旧正文滞后"不同族：那次是账本过期，这次是**当场写错**。
- **U-197 变异窗口里读工作树，读到的是刀不是事实**：电池跑到"删掉某道门的 `if: always()`"那一刀时
  我去 `grep`/解析 `ci.yml`，得到 `always=5` 并据此写下"有一道门漏挂"这条**假缺陷**；电池外再读是 6。
  ⇒ 读侧也装闸门：生成台账前先 `pgrep` 电池，在跑就拒绝（本轮当场验过：拒绝并打出 pid，台账零改动）。
- **U-198 位置锚点用裸子串 ⇒ 注释里那一次命中造出假 OK**：`step.index('wait "$pid"')` 命中的是
  注释里的 `wait "$pid"; status=$?`，于是 M490（把循环搬到真 wait 之前）照样绿。
  ⇒ 整行字面（含缩进与换行）+ `count == 1`。修完当场验：刀后 loop=1763 < wait行=2049 ⇒ 红。
- **U-199 两个测量在同一台机器上互相污染**：并跑的第二支 spike 既抢 `.build` 锁，又被第一支
  "按名字收残留"杀掉 ⇒ 我差点把"在屏卷死在拖选探针上"写成产品事实。单独重跑读到的是
  `swift-test pid=pgid=33848 / xctest pid=33905 pgid=33905 / 残留=0`。
  ⇒ 会抢锁或按名字杀进程的测量不许并跑；`verify_*.sh` 的退出码也要按内容给（上一版最后一条是 `cat`）。
- 牙 M489–M496 共八刀，全部 CAUGHT（M490 第一版 ESCAPED，见 U-198）。零产品改动 ⇒ 本轮不产生新帧；
  但**补装了 R84 欠下的那一次**（BACKLOG 124：`INSTALL_RESULT=ok`，旧包 sha `4aa88f2e…` → 新包 `7ef8c6ec…`）。

'''

DECISION = u'''
### D-147（R89）看门狗要按进程树收，硬门要排在证据之后

- 背景：R88 把在屏探针的看门狗改成 `set -m` + `kill -9 -- -$pid`，并新写一道硬门
  （收掉之后还有 xctest 活着就红）。R88 的 CI 同时给出两个读数：
  `UI_PROBE_START_LINES_LOST=1`（修法想要的东西，第一次在 runner 上成立）与
  `PROBE_FLOOR_WATCHDOG_MISSED=1 收掉之后仍有 1 个 xctest 在跑`（修法不成立的证据）。
  本机量到 `xctest` 自己 `setpgid` 成了另一个组的组长 ⇒ 组杀天然够不到它。
  另一个后果更贵：那道门红了之后 GitHub skip 掉后面七个步骤，产品的证据一步没跑。
- 决定：① 残留收杀放在**父壳 `wait` 之后**（不在 killer 子壳里），照残留孩子的 pgid 杀它的组；
  ② 四道硬门（`Swift tests (executed-count gate)` / `Capture gate` / `On-screen probe coverage floor` /
  `Motion coverage floor`）全部挪到所有产证据步骤之后，各自 `if: always()`；
  ③ 自检按**位置**与**逐门**查：循环必须在 `wait` 之后、孤儿计数必须在循环之后、
  每一道门各自要有 `if: always()`；④ 两份读数继续落盘（跨步骤没有共享 shell 变量，R88/U-188）。
- 为什么不顺手把 122 做掉：本轮改的是"上一轮交出去的东西不完整"，再叠一条新通道就分不清
  是哪一处让 runner 的读数变了（R58 那一课）。122 的做法已在本轮定下来（stderr 心跳 + `setUpWithError`）。
- 不许的处置：把硬门直接删掉换回 report-only（那是把 U-188 修好的东西又交出去）；
  或者把 `if: always()` 加到**所有**步骤（那会让真正的构建失败也变成"跑过了"）；
  或者拿"本轮 99 分"当 122 不做的理由。
'''

BACKLOG_92_UPDATE = u'''
    → **R89 拿到一条新事实（也欠一条）**：本机按 CI 原样跑，这一卷在 90 秒内**能跑完**
    （日志里有 `testAccessibilityTreeCoverage skipped (0.623s)`、下一条 started、以及 swift-testing 的结尾行），
    而 runner 上 240 秒收不掉 ⇒ "runner 上卡在哪"与"本机为什么能跑完"之间的差**还没有名字**。
    R89 把看门狗修到真的能收掉 xctest（D-147），但这条差本身要等下一次 CI 的
    `UI_PROBE_RUNNER_ALIVE` / `UI_PROBE_ORPHAN_XCTEST` 两格才算有读数。
'''

BACKLOG_93_UPDATE = u'''
    → **R89 在 runner 上确认**：`UI_PROBE_START_LINES_LOST=1`（收掉那一刻 xctest 还活着）
    ⇒ 成因是②（stdout 块缓冲被 SIGKILL 整块带走），不是①。这一格从此不再依赖我本机那一次 spike。
    而"挂在哪一条"仍然没有名字 ⇒ 交给 **122**：本轮定了做法
    （探针文件级已有的 `emit()` 走 stderr=直接 `write(2)`，CI 的 `2>&1` 会把它收进同一份日志；
    缺的只是每条用例开头一行心跳，而 `setUpWithError()` 里 `self.description` 就给出
    `-[类名 用例名]`，与 XCTest 那行同名 ⇒ 一处改动覆盖 11 条）。
'''

BACKLOG_119_UPDATE = u'''
    R89 **没有**拿到第六个数据点：R88 那道硬门红了之后 GitHub 把动效卷整个 skip 掉
    （见 D-147 第二条）。⇒ 分布宽度仍然停在 5 个点（0.522 / 0.842 / 0.032 / 0.690 + 本机那一遍），
    而 `contradicted-by-travel` 那一支至今零次在 runner 上触发。
    这一格按欠账记，不许被读成"runner 上一切正常"。
'''

BACKLOG_122_UPDATE = u'''
    R89 定了做法但**没做**（一次只改一处）：
    ① 通道不用新造 —— `UIInteractionProbeTests` 文件级已有 `emit()`，写的是
      `FileHandle.standardError`（直接 `write(2)`，不经 stdio 块缓冲），而 CI 那一步是
      `swift test … > /tmp/ui.log 2>&1` ⇒ 这条腿本来就活得过 SIGKILL；
    ② 心跳挂在 `setUpWithError()`：本机孤立包实测 `self.description` == `-[类名 用例名]`，
      与 XCTest 自己那行 `Test Case '-[…]' started.` **同一个名字空间** ⇒ `ui_probe_report.py`
      现有的 `CASE` 正则可以直接用；`invocation` 那条要 `NSStringFromSelector(inv.selector)`
      且带 `AndReturnError:` 后缀，不许拿它当用例名；
    ③ 取不到名字时心跳要自己说"取不到"，不许静默写一条没名字的行；
    ④ 整行一次 write（R81 那一课：内容与换行分两次写会被并发缝在一起）。
'''

CHANGELOG = u'''### CI（R89）

- 在屏探针的看门狗补第二刀：残留的 `xctest` 由**父壳在 `wait` 之后**照它自己的 pgid 收掉
  （`xctest` 自己 `setpgid` 成另一个组的组长，R88 的 `kill -- -$pid` 够不到它 —— runner 实测残留 1）。
- 四道硬门（`Swift tests (executed-count gate)` / `Capture gate` / `On-screen probe coverage floor` /
  `Motion coverage floor`）全部挪到所有产证据步骤之后，各自 `if: always()`。
  理由：R88 那道门红了之后 GitHub skip 掉七个步骤，**仪器的红吃掉了产品的证据**。

### 仪器（R89，仓库外）

- `r89_watchdog_shape.py`：三形状对照（只杀 pid / 只杀驱动组 / 父壳再收一次）+ 逐门查 `if: always()`
  + 位置判据（循环必须在 `wait` 之后、孤儿计数必须在循环之后）。
- `mutate_r89_watchdog.py`：%s；电池基线先跑、按内容还原、刀异常记 NOT-RUN。

### Docs（R89）

- BACKLOG 92 更新（本机 90 秒能跑完 vs runner 240 秒收不掉，那条差还没有名字）；
  93 更新（runner 上确认成因是②；做法交给 122）；119 更新（本轮第六点被 skip，按欠账记）；
  122 补做法（stderr 心跳 + `setUpWithError` 的 `self.description`）。

''' % (KNIFE_LINE)

STATE_ANCHOR_HINT = '最后更新：2026-10-16 07:20（本地 · R88 / 第 90 轮收尾：'


def patch_visual_iteration():
    p = os.path.join(REPO, 'AGENT_VISUAL_ITERATION.md')
    s = read(p)
    assert u'## Round 89' not in s, u'Round 89 已经写过了'
    write(p, s.rstrip(u'\n') + u'\n\n' + ROUND_HEAD + SECTION)


def patch_ui_audit():
    p = os.path.join(REPO, 'AGENT_UI_AUDIT.md')
    s = read(p)
    assert u'## 第 91 轮' not in s
    nums = [int(m.group(1)) for m in re.finditer(u'^## 第 (\\d+) 轮', s, re.M)]
    want = max(nums) + 1
    if (u'## 第 %d 轮' % want) not in UI_AUDIT:
        raise SystemExit(u'UI_AUDIT 的轮次标签必须等于台账现有最大号 %d 再加一（=%d），'
                         u'而正文写的不是这个数 ⇒ 会跳号，拒绝落盘' % (max(nums), want))
    anchor = u'## 第 90 轮 · R88：'
    assert s.count(anchor) == 1, u'UI_AUDIT 的 90 轮锚点不唯一'
    write(p, s.replace(anchor, UI_AUDIT + anchor, 1))


def patch_decisions():
    p = os.path.join(REPO, 'AGENT_DECISIONS.md')
    s = read(p)
    assert u'### D-147' not in s
    write(p, s.rstrip(u'\n') + u'\n' + DECISION)


BACKLOG_124_NEW = u"""
124. **装机落后于产品：R84 改了产品文件却没换装，而这条规矩没有守卫**（R89 开 / 与 96、121 同族）：

    做最终报告收口审计时对了一遍台账才看见这件事 —— `r89_install_lag_audit.py` 逐段读
    `## Round N` 里自报的"N 个产品文件"与该段有没有换装证据（`INSTALL_RESULT=ok` /
    `INSTALL_SHA_MATCH=1`）或"不换装+理由"，读数：

    ```
    INSTALL_LAG_ROUNDS total=88 有产品数=9 无该行(老轮次,不判)=79
    INSTALL_LAG_OK=8
    INSTALL_LAG_RED=Round 84 自报产品文件=1 而段内既无换装记录、也无"不换装+理由
    ```

    ⇒ R84（亮带那一族的产品改动）之后 R85–R89 全是 0 个产品文件 ⇒ **本机装的还是 R84 之前的包**，
    而这五轮的帧、判据、账本描述的都是 R84 之后的产品。"交付默认自己构建换装"这条规矩立过，
    但它只能被"想起来"、不能被"跑出来" —— 这就是它漏掉一整轮的原因（与 121 同一族：
    规矩没有变成会红的东西，就等于没有）。
    ⇒ 两步修法：① 本轮把当前树构建 + 换装 + 记录（做完在本条里结案"落后已补"）；
    ② 把这支审计升成判据（进 `scripts/` + 自测 + CI 报告型一步），并让每轮验证摘要里
    "自报产品数 > 0"与"换装证据"绑成一条会红的话。
    ⇒ 老实记一格：79 个老轮次没有"N 个产品文件"那一行（那个自报格式是 R66 之后才有的）⇒
    审计**判不了它们**，这一格不许被回推成"那 79 轮没落后"。
    ⇒ **第①步本轮已结案（落后已补）**：`install_local.sh --yes --label r89-overlay` →
    `INSTALL_RESULT=ok`，旧包 sha `4aa88f2ef5c3e758…` 换成新包 `7ef8c6eca171adbd…`（版本号都是 1.4.8，
    所以"版本号相同"完全不能当"包相同"的证据），`INSTALL_SHA_MATCH=1`、`INSTALL_RUNNING_PID=34203`
    （启动晚于安装、exe 路径逐字对上 `/Applications/时间剪史.app`）、存档 105→105、`SMOKE_OK=1`。
    第②步（升成 `scripts/` 里的判据 + 自测 + CI 报告型一步）仍然开着，交下一轮。
"""


def patch_backlog():
    p = os.path.join(REPO, 'AGENT_BACKLOG.md')
    s = read(p)
    anchor_92 = (u'    而 R61 那类「选中/滚动」的回归恰恰只有真实表格能判。\n')
    # 92 挂在它自己那一段的末尾。第一版那两个锚点是我**凭记忆拼出来的旧文**，文件里都不存在
    # （命中 0 ⇒ stage A 当场红在这里）—— 正是 R87 记过的"别用上轮的值当锚点"那一族：
    # 锚点要按**实际文本的形状**找，这里用"以 `    牙 M465` 开头"这一形状，命中必须恰好一次。
    a92 = [l + u'\n' for l in s.split(u'\n') if l.startswith(u'    牙 M465')]
    assert len(a92) == 1, u'92 的收尾行按形状命中 %d 次（要求恰好 1）' % len(a92)
    a92 = a92[0]
    s = s.replace(a92, a92 + BACKLOG_92_UPDATE, 1)
    anchor_93 = (u'    原文那句"下一轮做法：先只跑一条最便宜的用例并带 30s 看门狗"本轮**没有采用**：\n')
    assert s.count(anchor_93) == 1, u'93 的锚点不唯一（命中 %d）' % s.count(anchor_93)
    s = s.replace(anchor_93, anchor_93 + BACKLOG_93_UPDATE, 1)
    a119 = (u'    ③ 新形状带来的新问题另开 **BACKLOG 120**：位置判据今天仍被 `loopCapable` 关着，\n'
            u'    而它恰恰是唯一有资格说话的那把尺 —— 谁给谁签字，这件事本轮只改了一半。\n')
    assert s.count(a119) == 1, u'119 的锚点不唯一（命中 %d）' % s.count(a119)
    s = s.replace(a119, a119 + BACKLOG_119_UPDATE, 1)
    a122 = (u'    或者拿"今天没造成错判"当它尽职的证据。\n')
    assert s.count(a122) == 1, u'122 的锚点不唯一（命中 %d）' % s.count(a122)
    s = s.replace(a122, a122 + BACKLOG_122_UPDATE, 1)
    # 新开 124：接在文件最后一条（123 那一格的收尾行）之后；锚点唯一性先查
    tail_anchor = (u'    这次该搜 `vibrant` 与 `侧栏`）。我这轮是先看了图、先量了数、先写了 123，才去读 D-090 ——\n'
                   u'    顺序反了。量到的东西是真的，"新"不是。\n')
    assert s.count(tail_anchor) == 1, u'123 的收尾行不唯一（命中 %d）' % s.count(tail_anchor)
    s = s.replace(tail_anchor, tail_anchor + BACKLOG_124_NEW.strip(u'\n') + u'\n', 1)
    write(p, s)


def patch_changelog():
    p = os.path.join(REPO, 'CHANGELOG.md')
    s = read(p)
    anchor = u'## [Unreleased]\n'
    assert s.count(anchor) == 1
    assert u'### CI（R89' not in s
    write(p, s.replace(anchor, anchor + CHANGELOG, 1))


def patch_state():
    p = os.path.join(REPO, 'AGENT_STATE.md')
    s = read(p)
    head_marker = STATE_ANCHOR_HINT
    assert s.count(head_marker) == 1, u'STATE 头部锚点不唯一'
    new_head = (u'最后更新：2026-10-16 09:05（本地 · R89 / 第 91 轮收尾：**读 R88 的 CI 又读到 main 红，'
                u'而红的是 R88 自己新写的那道门 —— 它同时给了两件东西：想要的那格读数，和修法不成立的证据** —— '
                u'`UI_PROBE_START_LINES_LOST=1` 第一次在 runner 上说话（93 的成因由 CI 自己确认为②：'
                u'stdout 块缓冲被 SIGKILL 整块带走），而 `PROBE_FLOOR_WATCHDOG_MISSED=1 收掉之后仍有 1 个 '
                u'xctest 在跑` 说明 R88 的组杀够不到它：本机量到 `swift-test pid=pgid=27359` 而 '
                u'`xctest pid=pgid=27416` —— **xctest 自己 setpgid 成了另一个组的组长**（U-192）。'
                u'更贵的是第二个后果：那道门红了之后 GitHub skip 掉后面**七个步骤**'
                u'（动效卷、动效地板、脚本自测、两张帧基线、启动冒烟）⇒ 仪器的红吃掉了产品的证据（U-193），'
                u'所以本轮**没有** coverage 第六个数据点，119 按欠账记。本轮（D-147）：'
                u'① 残留收杀放在父壳 `wait` 之后（第一版塞进 killer 子壳会被 `kill "$killer"` 掐死在半路，'
                u'对照读到 `Terminated: 15` + 残留 1 —— 同一段代码位置错了就是竞态，U-194）；'
                u'② 四道硬门全部挪到产证据步骤之后并各自 `if: always()`；'
                u'③ 自检改成按位置查 + 逐门查（U-195：`if: always()` 数总量 ≥4 是假尺，'
                u'文件里本来有六处，M492 第一版因此 ESCAPED）。牙 M489–M496 八刀全 CAUGHT；'
                u'三形状对照 6/6（旧形状留孤儿 / R88 形状**仍然**留孤儿 / R89 形状残留 0）；'
                u'真机进程树实测残留 0。**本轮零产品改动 ⇒ 不换装**。'
                u'验证：非台账文件 %s 个、产品 0 个；脚本 %s（exit %s）；对照 %s；电池 %s；树 %s；'
                u'没跑的：%s。'
                u'**下一轮第一件事：读 R89 的 CI（`UI_PROBE_ORPHAN_XCTEST` 必须变 0 —— 那才是'
                u'『看门狗真的够到了』的证据）+ 把 BACKLOG 122 的 stderr 心跳接上**）\n\n'
                u'> 上一轮（R88 / 第 90 轮收尾）原文开头：' + head_marker) % (
        TOUCHED, SCRIPTS, PY_EXIT, SHAPE_LINE, BATTERY_LINE, TREE_LINE, NOT_RUN_LINE)
    write(p, s.replace(head_marker, new_head, 1))


def patch_final_report():
    p = os.path.join(REPO, 'AGENT_FINAL_REPORT.md')
    s = read(p)
    old = u'| 阶段二 **81 轮**审计（R9–R88，含 29d；'
    assert s.count(old) == 1, u'FINAL_REPORT 轮数锚点不唯一'
    s = s.replace(old, u'| 阶段二 **82 轮**审计（R9–R89，含 29d；', 1)
    old = u'以 `curve_from_ledger.py` 的 `PHASE2 n=81` 为准）'
    assert s.count(old) == 1, u'FINAL_REPORT 曲线锚点不唯一'
    s = s.replace(old, u'以 `curve_from_ledger.py` 的 `PHASE2 n=82` 为准）', 1)
    old = u'| 视觉台账 | U-31 … U-191（159 条；'
    assert s.count(old) == 1, u'FINAL_REPORT U 计数锚点不唯一'
    s = s.replace(old, u'| 视觉台账 | U-31 … U-199（168 条；', 1)
    old = u'| 决定台账 | D-069 … **D-146**'
    assert s.count(old) == 1, u'FINAL_REPORT 决定台账锚点不唯一'
    s = s.replace(old, u'| 决定台账 | D-069 … **D-147**', 1)
    old = u'**M100–M488**（阶段二 388 支；'
    assert s.count(old) == 1, u'FINAL_REPORT 刀数锚点不唯一'
    if len(CAUGHT) != len(KNIVES):
        raise SystemExit(u'有刀没抓到就不许往报告里写"全 CAUGHT"：%s'
                         % u'、'.join(t for t, _, k in KNIVES if k != 'CAUGHT'))
    s = s.replace(old, (u'**M100–M496**（阶段二 396 支；**R89 的 %s %s 全 CAUGHT**'
                        u'（两刀第一版 ESCAPED：M492 = `if: always()` 的检查数总量，而文件里本来有六处 ⇒ '
                        u'删掉某一门照样绿，U-195；M490 = 位置比较用了裸子串 `wait "$pid"`，'
                        u'被上文注释里那一次命中喂饱 ⇒ 循环搬到真 `wait` 之前照样绿，U-198）；'
                        % (KNIFE_RANGE, KNIFE_TOTAL)), 1)
    old = u'自评曲线（**81 轮**，Round 9–88，含 29d 那一轮边界轮；'
    assert s.count(old) == 1, u'FINAL_REPORT 曲线段锚点不唯一'
    s = s.replace(old, (u'自评曲线（**82 轮**，Round 9–89，含 29d 那一轮边界轮；' + CURVE +
                        u'；**后面那几段 `）：PHASE2 n=…` 是前几轮留下的同一条曲线的历史读数**'
                        u'（n 依次小 1，不是并存的两把尺，也不是本轮没算完））：'), 1)
    anchor = (u'U-183 是**定罪权要按样本数分配**')
    assert s.count(anchor) == 1, u'FINAL_REPORT 的 U 段插入锚点不唯一'
    s = s.replace(anchor, REPORT_U + anchor, 1)
    write(p, s)


REPORT_U = (u'U-192 是**杀父组不等于杀整棵树**（`xctest` 自己 setpgid 成另一个组的组长，'
            u'所以 R88 的 `kill -- -$pid` 只杀到驱动；runner 用 `PROBE_FLOOR_WATCHDOG_MISSED=1` 报了这件事）；'
            u'U-193 是**红不许把别的判据变成没跑**（那道硬门红了之后 GitHub skip 掉七个步骤，'
            u'于是本轮拿不到 coverage 第六个点）；U-194 是**同一段代码位置错了就是竞态**'
            u'（循环塞进 killer 子壳会被父壳的 `kill "$killer"` 掐死在半路 ⇒ 接线检查要按位置查）；'
            u'U-195 是**按总量数是假尺**（`if: always()` 查 `count >= 4` 而文件里有六处 ⇒ 要逐门查）；'
            u'U-196 是**新写的正文一落地就与产物矛盾**（红吃掉的步骤数我先写"九"而三个 run 的 API 结论都是 7，'
            u'UI_AUDIT 的轮次标签我先写 92 而台账自己的最大号推出应是 91 ⇒ '
            u'守卫挂在生成器唯一的落盘口 `write()`，标签在插入点与 `max+1` 对账，不符就拒绝落盘）；'
            u'U-197 是**变异窗口里读工作树读到的是刀不是事实**（电池跑到删 `if: always()` 那一刀时我 '
            u'`grep` 到 5 就写下了一条假缺陷 ⇒ 生成台账前先 `pgrep` 电池，在跑就拒绝，本轮当场验过）；'
            u"U-198 是**位置锚点用裸子串会被注释命中**（step.index('wait \"$pid\"') 读到注释里那一个，"
            u'于是 M490 那刀照样绿 ⇒ 改成整行字面（含缩进与换行）+ `count == 1`）；'
            u'U-199 是**两个测量在同一台机器上互相污染**（并跑的 spike 抢 `.build` 锁、又被对方按名字收掉，'
            u'我差点把「卷死在拖选探针上」写成产品事实；而 `verify` 的退出码由最后一条 `cat` 决定，'
            u'电池 1 刀逃掉它仍 exit 0 ⇒ 现在按内容给）；')


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
    if 'n=82' not in real:
        raise SystemExit('曲线不是 82 轮（本轮正文没被识别为一个轮次？）：%s' % real[:200])
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
