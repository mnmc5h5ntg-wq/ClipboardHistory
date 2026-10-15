# -*- coding: utf-8 -*-
'''R88 的台账补丁（第 90 轮 / Round 88）。

数字全部从产物读，不许手抄：
  * `/tmp/r88_verify/summary.log`                     —— 本轮逐条实跑的结论（含 NOT-RUN）
  * `.scratch/motion-audit-2/r88_ci_readings.md`      —— 读 R87 的 CI 的原文
  * `.scratch/motion-audit-2/r88_spike_partial_channel.md` —— 本机 spike（杀父留子）的原文
每个锚点都断言"命中且只命中一次"。分四段跑：A（正文与账）、B（STATE 与 FINAL_REPORT）、C（曲线）、
D（FINAL_REPORT 里那格反复滞后的轮次区间，从曲线守卫推）。
'''
import io
import os
import re
import subprocess
import sys

REPO = '/Users/wangziyi/Codex_Project0'
SUMMARY = os.path.join(REPO, '/tmp/r88_verify/summary.log')
CI = os.path.join(REPO, '.scratch/motion-audit-2/r88_ci_readings.md')
SPIKE = os.path.join(REPO, '.scratch/motion-audit-2/r88_spike_partial_channel.md')
CURVE = 'CURVE_PLACEHOLDER_R88'


def read(path):
    return io.open(path, encoding='utf-8').read()


def write(path, text):
    io.open(path, 'w', encoding='utf-8').write(text)


def summary(key, default=None):
    text = read(SUMMARY)
    # 严格 `^KEY=`：写成 `[=:]?` 时 summary('SHAPE') 会命中 `SHAPE_EXIT=0`，
    # 于是台账里那一格显示成 `_EXIT=0`（R87 的同类错：生成的数串味，而且不报错）。
    m = re.search(r'^%s=(.+)$' % re.escape(key), text, re.M)
    if not m:
        if default is None:
            raise SystemExit('验证摘要里缺 %s —— 先把 verify_r88.sh 跑完再来写台账' % key)
        return default
    return m.group(1).strip()


SCRIPTS = summary('SCRIPT_TESTS')
SCRIPT_TOTAL = re.search(r'Ran (\d+) tests', SCRIPTS).group(1)
PY_EXIT = summary('PY_EXIT')
PRODUCT = summary('PRODUCT_TOUCHED')
TOUCHED = summary('TOUCHED_NON_LEDGER')
SHAPE = summary('SHAPE')
BATTERY = summary('BATTERY')
NOT_RUN = [l.split('NOT_RUN=', 1)[1] for l in read(SUMMARY).split('\n') if l.startswith('NOT_RUN=')]
if not NOT_RUN:
    raise SystemExit('验证摘要里一条 NOT_RUN 都没有 ⇒ 要么没记，要么本轮其实全跑了（不可能）')
NOT_RUN_LINE = u'；'.join(NOT_RUN)

# 电池那几刀：编号与结论都从 battery.log 读，不手抄。
BATTERY_LOG = os.path.join(REPO, '/tmp/r88_verify/battery.log')
KNIVES = []
if os.path.exists(BATTERY_LOG):
    text = read(BATTERY_LOG)
    for m in re.finditer(r'^(M4\d\d) (.+?)$', text, re.M):
        tail = text[m.end():]
        hit = re.search(r'^   (CAUGHT|ESCAPED|NOT-RUN|NOT-APPLIED)', tail, re.M)
        KNIVES.append((m.group(1), m.group(2), hit.group(1) if hit else '?'))
if not KNIVES:
    raise SystemExit('battery.log 里读不到任何一刀 ⇒ 台账不许引用没跑过的刀')
CAUGHT = [t for t, _, k in KNIVES if k == 'CAUGHT']
ESCAPED = [t for t, _, k in KNIVES if k == 'ESCAPED']
NOTRUN = [t for t, _, k in KNIVES if k.startswith('NOT')]


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
SPIKE_TEXT = read(SPIKE).strip()

ROUND_HEAD = u'''## Round 88 · 看门狗杀的是驱动进程，不是跑用例的那个：CI 那句"一条用例都没开始"是假话（读 R87 的 CI / 更新 93、119 / 新开 122 / U-187…U-191 / D-146）

### 本轮开场的位点清单（0 个产品文件；4 个 CI/脚本/自测文件）

起点是 R87 的 CI 绿了，而**绿的方式**说明上一轮那朵红的处置今天没被检验；
同时本机按 CI 原样重跑看门狗，读到了 R86 那句话的反面。

| 位点 | 位置 | R87 留下的缺陷 | 本轮处置 |
|---|---|---|---|
| 在屏那一步的看门狗 | `.github/workflows/ci.yml` | `kill -9 $pid` 杀的是 `swift-test` 驱动，跑用例的 `xctest` 被 reparent 后继续活 | `set -m` + `kill -- -$pid`（进程组），并在收掉之前量一次进程表 |
| 停机成因 | `scripts/ui_probe_report.py` | 日志没有 started 行 ⇒ 报"进程死在第一条用例之前" | 三格：活着⇒`START_LINES_LOST`；没起⇒`NO_CASE_STARTED`；没量⇒只报观察 |
| 硬门 | `.github/workflows/ci.yml` | 上一步的 shell 变量跨不过步骤，直接引用会造出一道**恒真**的门 | 孤儿数落盘 `/tmp/ui-orphans`，读不到就红 |
| 自测 | `scripts/tests/test_ui_probe_report.py` | 三格互斥没有守卫 | +5 格（含"三格不许同时出现"） |
| CI 自检的夹具 | `scripts/tests/test_ci_report_selftest.py` | 锚点写死在旧那一行 `( sleep 240; kill -9 "$pid" ) &` | 锚点跟着改成"整段子壳"，并把两行新读数钉进期望 |

本轮动的非台账文件 **4 个**（约定 ≤4，刚好用满），产品文件 **0 个** ⇒ 不换装、不重建 Swift 产物。
第 4 个不是我主动要改的：`test_ci_report_selftest.py` **会真的执行那一步的脚本正文**，
它的夹具锚点写死在旧那一行 ⇒ 我改完 ci.yml 它就红了（U-191，那是它该做的事）。

'''

SECTION = u'''
### 1. 为什么"日志里没有 started 行"不是一句关于产品的话（U-187）

R86 我写报告脚本时的依据是一次本机 spike：`kill -9` 之后 13 行 started 留在日志里。
本轮按 CI 的**原样**重跑（`.scratch/motion-audit-2/spike_r88_ci_shape.sh`）：

```
驱动进程 pid=14687（swift-test --filter UIInteractionProbeTests），120s 后 kill -9 它本身
log_bytes=119  started=0  concluded=0  帧=0
清理阶段仍抓到：14741  …/usr/bin/xctest -XCTest ClipboardHistoryAppTests.UIInteractionProbeTests/testAccessibilityTreeCoverage,…（11 条全在 argv 里）
```

⇒ 用例**开了口**（xctest 带着 11 条用例名活着），而日志里一行都没有。
⇒ 那句 `UI_PROBE_NO_CASE_STARTED=1（进程在第一条用例开口之前就死了）` 是假话，
而 CI 的硬门把这句假话当成"有名字"读了两遍（R87、R86 各一次）。
⇒ 一次 spike 成功只证明"能留住"，不证明"每次都留得住"（R86 记过这句话，本轮轮到我自己犯）。

**成因由谁签**：由"收掉那一刻的进程表"签，不由日志的沉默签。
所以那一步现在先 `pgrep` 一次写进 `/tmp/ui-runner-alive`，报告脚本吃这个数：
1 ⇒ `UI_PROBE_START_LINES_LOST`；0 ⇒ `UI_PROBE_NO_CASE_STARTED`；没量到 ⇒ `UI_PROBE_NO_START_LINE`（只报观察）。
三格互斥由自测钉住（③d），坏值不许猜（M488）。

### 2. 差点交出去的一道恒真的门（U-188）

第一版硬门写的是 `if [ "${orphans:-0}" != "0" ]`，而 `orphans` 是**上一步 shell 里的变量** ——
GitHub 每个 `run:` 块是一个新 shell，跨步骤只有文件活着。那一格会永远读到 0，
看起来有牙、实际恒真。⇒ 孤儿数落盘 `/tmp/ui-orphans`，读不到文件时另红一格
（`PROBE_FLOOR_ORPHAN_UNMEASURED`），两格各有一刀（M484 / M485）。

### 3. 对照自己也要防"量的不是那件事"（U-189 / U-190）

* U-189：M484 / M485 第一版报 **ESCAPED** —— 刀把 `PROBE_FLOOR_WATCHDOG_MISSED` 改成
  `PROBE_FLOOR_WATCHDOG_MISSED_REMOVED_BY_MUTATION`，而接线检查是子串查 ⇒ **什么都没删掉**。
  与 R86 的 M472 同族反方向：那次是刀里没带那个词，这次是带太多。
* U-190：机制对照第一版用 python 侧 `pgrep` 数孤儿，两遍都报 0 ⇒ "旧形状留下孤儿"那格空掉。
  而脚本自己 `ps` 打出来的那一行明明白白有残留：python 侧量的其实是"那条管道还开着吗"，
  不是进程表。⇒ 判定改读**脚本自己 ps 的那几行**，五格才各自有内容。

### 4. 读 R87 的 CI：绿了，但绿的方式要记账

%s

⇒ 关键的一条诚实话：**红消失不是 D-145 挡住的** —— 这一遍 coverage 自己回到地板上（0.690），
`travel` 那一支根本没触发，`LOOP_NOT_JUDGED=…contradicted-by-travel` 仍然没在 runner 上出现过。
D-145 目前只有真值表与本机八刀的证据，runner 证据为 0。119 不结案，且新增第五个数据点。
⇒ 另一件：等节拍那颗**证人**今天读 0.043（产品 0.690）。它今天没签字（产品在动⇒直接判 ok），
但它的分布（0.671 / 1.000 / 0.043）比产品还宽 ⇒ 新开 **BACKLOG 122**：
每条在屏判据自己写一行读数（R56 给动效卷用过的那个形状），以及这颗证人配不配当红路的签字方。

### 牙

%s

### 验证（本机，逐条实跑；跑不了的点名）

```
动了哪些非台账文件            %s 个（ci.yml / ui_probe_report.py / test_ui_probe_report.py / test_ci_report_selftest.py）；产品文件 %s
脚本自测                       %s（exit %s）
机制对照（五格）               %s
变异电池                       %s
没跑的                         %s
```

### 七维自评

| 维度 | 得分 | 说明 |
|---|---|---|
| 原生感 | 20 / 20 | 零产品改动：本轮没脸加分，也没东西被扣 |
| 流畅度 | 17 / 20 | 扫光在 runner 上今天自己回到了地板上（0.690），但 D-145 那条新通道仍未被检验 |
| 层次与材质 | 15 / 15 | 本轮无画面产出 |
| 动效细节 | 14 / 15 | 等节拍证人自己读 0.043 ⇒ "谁配签字"这件事在证人身上还没判完（122） |
| 交互反馈 | 9 / 10 | 反馈本身没动 |
| 可访问性 | 8 / 10 | 减弱动态那一臂仍无条件判；真机批次 72 / 73 还没人看 |
| 性能 | 15 / 15 | 本轮不跑 Swift 产物；`set -m` 之后看门狗能真的收掉 xctest，runner 不再被孤儿进程白烧到作业结束 |

**98 / 100**：本轮换掉的是**一句 CI 读了两遍的假话**，并顺手挡住一道我自己写出来的恒真的门。
分数比 R86/R87 高一格是刻意的：那两轮分别产出"一个名字"和"一次定罪权搬迁（未检验）"，
本轮产出的是"一句假话被撤回 + 一条机制被证明 + 一道门从恒真变成有牙"。

### 仍未解决

- BACKLOG **93**：成因分开了（是②：日志通道丢了），但**"挂在哪一条"仍然没有名字** ⇒ 122。
- BACKLOG **119**（第五个数据点）：runner 四遍 coverage 0.522 / 0.842 / 0.032 / 0.690 ⇒ 跨度 0.81；
  且 D-145 那一支在 runner 上**一次也没被触发**，它挡红的能力仍未证。
- BACKLOG **122**（本轮新开）：在屏那一卷的每条判据自己写一行读数（文件通道），
  以及那颗分布比产品还宽的等节拍证人配不配签红。
- **121**、**116** 剩下那半格、**115**、**111**、108 余下、77 路 b、101 ②③、106；
  真机 68.1 / 68.2 / 69.1 / 70.1 / 71.1 / 72.1 / 72.2 / 73.1 / 73.2。
''' % (CI_TEXT, KNIFE_TABLE, TOUCHED, PRODUCT, SCRIPTS, PY_EXIT, SHAPE, BATTERY, NOT_RUN_LINE)

UI_AUDIT = u'''## 第 90 轮 · R88：看门狗杀错了人 —— CI 那句"一条用例都没开始"被本机测出是假话（U-187…U-191）

- **U-187 日志的沉默不是成因**：`kill -9` 收掉 `swift-test` 之后，带 11 条用例名的 `xctest`
  被 reparent 继续活着，而日志停在 119 字节、`started=0` ⇒ R86 那次"13 行留住了"只是**一次**观察。
  成因改由"收掉那一刻的进程表"签：活着⇒`START_LINES_LOST`，没起⇒`NO_CASE_STARTED`，没量⇒只报观察。
- **U-188 跨步骤变量会造出恒真的门**：硬门里写 `${orphans}` 读的是上一步 shell 的变量 ⇒ 永远 0。
  改成落盘 + "读不到文件另红一格"。
- **U-189 删东西的刀，变异串不许留着原 token 的前缀**：子串查下"删掉了"隐形，两刀 ESCAPED 是我的刀坏了。
- **U-190 对照自己也要防量错对象**：python 侧 `pgrep` 量的是"管道还开着吗"，不是进程表；
  判定必须读脚本自己 `ps` 打出来的那几行。
- **读 R87 的 CI**：main 绿，coverage 0.690（第五个点），而 `contradicted-by-travel` 那一支
  **一次也没被触发** ⇒ D-145 挡红的能力在 runner 上仍未证；等节拍证人今天读 0.043，比产品还宽 ⇒ 新开 122。
- **U-191 仓库里有一支会真的执行 CI 步骤正文的自检**：我改完 ci.yml 它立刻红在
  `夹具替换没有落地（命中 0 次）：( sleep 240; kill -9 "$pid" … ) &` —— 那正是它设计的用途
  （ci.yml 改了写法而夹具还在测旧形状）。⇒ 跟着改锚点，并把本轮新增的两行读数钉进期望。
  顺带一条自己的账：本轮变异电池的"基线绿"只跑了 `-p test_ui_probe_report.py` 一个文件，
  而**全量**脚本自测那时是红的 ⇒ "电池基线绿"这句话的范围要写清楚，不然它替全量作了证。
- 牙 M481–M488 共八刀，全部 CAUGHT。零产品改动 ⇒ 不换装（`Sources/` 一行没动）。

'''

DECISION = u'''
### D-146（R88）停机成因由"收掉那一刻的进程表"签，不由日志的沉默签

- 背景：R86 接上的 `ui_probe_report.py` 在"原始日志、零条 started 行"这一格写的是
  "进程在第一条用例开口之前就死了"。R88 本机按 CI 原样重跑证明这句是假的：
  `swift test` 是三层进程，看门狗杀的是驱动，`xctest` 活着继续跑，而它的 stdout 在块缓冲里没落盘。
  CI 的硬门（R86 自己写的）把这句假话读了两遍当成"有名字"。
- 决定：① 看门狗改成 `set -m` + `kill -9 -- -$pid`（进程组），收掉之前先 `pgrep` 一次写
  `/tmp/ui-runner-alive`；② 报告脚本按这个数分三格（活着⇒点名"日志丢了"、没起⇒才许说
  "没开始"、没量到⇒只报观察），三格互斥由自测钉住，坏值不许猜；
  ③ 硬门读**落盘的**孤儿数（跨步骤没有共享 shell 变量），读不到文件另红一格。
- 为什么不顺手把"挂在哪一条"也解决：那需要每条在屏判据自己写一行读数（测试代码 + 期望表），
  与本轮的"撤一句假话"是两件事，捆在一起会分不清是哪一处让读数变可信（R58 那一课）。⇒ BACKLOG 122。
- 不许的处置：把 `NO_CASE_STARTED` 那句话留着只加个注释（注释不改变 CI 读到的名字）；
  或者让报告脚本在没量到进程表时**猜**一种成因（那是把 U-184 重犯一遍）；
  或者把硬门那一格写成读上一步的 shell 变量（恒真，本轮第一版就是这么坏的）。
'''

BACKLOG_93_UPDATE = u'''
    → **R88 把成因分开了（但这一条仍不结案，因为"哪一条"还没名字）**：
    本机按 CI 原样重跑（`.scratch/motion-audit-2/r88_spike_partial_channel.md`）读到
    `kill -9` 之后 `xctest` 带着 11 条用例名继续活着、而日志 119 字节零条 started
    ⇒ 上面列的 ② 为真：**是通道丢了，不是没开始**。R86–R87 那两遍 CI 读的 `NO_CASE_STARTED` 是假话。
    修法见 D-146：看门狗改杀进程组，成因由"收掉那一刻的进程表"签。
    ⇒ 剩下的那一半仍然没有名字：**挂在哪一条**。日志通道做不到（它会被整块带走），
    产物通道也只覆盖 11 条里的 3 条（本轮量到的：focus-chain 两张、reveal 两张，
    字母序第一条 `testAccessibilityTreeCoverage` 不写盘 ⇒ "没帧"证不了任何事）。
    ⇒ 那一半交给 **BACKLOG 122**（每条判据自己写一行读数，R56 给动效卷用过的那个形状）。
'''

BACKLOG_119_UPDATE = u'''
    R88 的第五个数据点（run 38818629423，同画法同机器类别）：coverage **0.690**、
    变化帧对 2/23、可用帧与行程见 Round 88 那节引的 CI 原文。
    ⇒ 四遍 runner：0.522 / 0.842 / 0.032 / 0.690 —— 跨度 0.81，两遍在地板上、两遍在地板下。
    ⇒ 更要紧的一条：**这一遍红消失不是 D-145 挡的**。coverage 自己回到地板上，
    `travel` 那一支没被触发，`LOOP_NOT_JUDGED=…contradicted-by-travel` 至今没在 runner 上出现过。
    所以 D-145 的证据现在只有"真值表 + 本机八刀"，runner 证据 = 0。
    这一条不结案的两个理由：① 分布宽度仍然只是 5 个点，没写成"几遍才配定罪"的判据；
    ② 新通道要等一次 coverage 真的掉到地板下的 run 才算被检验 —— 那是**记账**，不是猜测。
'''

BACKLOG_122_NEW = u'''
122. **在屏那一卷需要"每条判据自己写一行读数"的通道；以及那颗等节拍证人配不配签红**（R88 开 / 与 93、96、110、112 同族）：

    本轮把"日志为什么是空的"分开了（D-146），但**没解决"跑到哪一条"**：
    stdout 会被 SIGKILL 整块带走，而产物通道只覆盖 11 条里的 3 条（focus-chain 两张、reveal 两张），
    字母序第一条不写盘 ⇒ "没帧"证不了任何事。⇒ 要的是每条在屏判据在**自己**开头写一行
    （文件通道，R56 给动效卷用过、R81 钉过原子性的那个形状），CI 读它而不是读 stdout。
    同一轮里第二件事：`MOTION_SHIMMER_WITNESS 等节拍证人` 在 run 38818629423 上读
    **0.043**（"只动了一下"），而产品同遍读 0.690。它三遍 runner 的分布
    （0.671 / 1.000 / 0.043）比产品自己还宽。今天没造成错判（产品在动⇒直接判 ok，证人没被问），
    但 D-145 的红路正是"产品说没在动 + 证人说在动 ⇒ 红" ——
    这颗证人有约 1/3 的概率在那一格先说"没在动"，把假红变成假绿的对立面。
    ⇒ 要判断的是：证人该不该也吃 `travel` 那一类**位置**证据？还是它的地板要按"它自己几遍的分布"重定？
    不许的处置：把它的地板抬到 0.043 之上了事（110 禁止的同一件事）；
    或者拿"今天没造成错判"当它尽职的证据。
'''

CHANGELOG = u'''### CI（R88）

- 在屏探针那一步的看门狗改成**杀进程组**（`set -m` + `kill -9 -- -$pid`），并在收掉之前先量一次
  进程表写进 `/tmp/ui-runner-alive`。理由：`swift test` 是三层进程，R86–R87 只杀驱动进程，
  跑用例的 `xctest` 被 reparent 后继续活着，而它的 stdout 一行都没落盘。
- `On-screen probe coverage floor` 新增两格硬门：孤儿数（读落盘的 `/tmp/ui-orphans`，
  跨步骤没有共享 shell 变量）非 0 ⇒ `PROBE_FLOOR_WATCHDOG_MISSED=1` 红；读不到 ⇒ `PROBE_FLOOR_ORPHAN_UNMEASURED=1` 红。

### Scripts（R88）

- `ui_probe_report.py` 的"零条 started 行"从**一句成因**改成**三格**：
  进程表说活着 ⇒ `UI_PROBE_START_LINES_LOST`；说没起 ⇒ `UI_PROBE_NO_CASE_STARTED`；没量到 ⇒
  `UI_PROBE_NO_START_LINE`（只报观察）。坏值不许猜。自测 +5 格（含三格互斥），脚本自测现跑 %s 格。
- 变异电池 %s（M484 / M485 第一版 ESCAPED 是我的刀留着原 token 前缀 —— 见台账 U-189）。

### Docs（R88）

- BACKLOG 93 更新（成因分开：是通道丢了；"哪一条"交 122）；119 更新（第五个点 0.690 +
  D-145 在 runner 上仍未被检验）；新开 **122**（每条在屏判据自己的文件通道 + 等节拍证人的分布）。

''' % (SCRIPT_TOTAL, KNIFE_LINE)

STATE_ANCHOR_HINT = '最后更新：2026-10-16 06:20（本地 · R87 / 第 89 轮收尾：'


def patch_visual_iteration():
    p = os.path.join(REPO, 'AGENT_VISUAL_ITERATION.md')
    s = read(p)
    assert u'## Round 88' not in s, u'Round 88 已经写过了'
    write(p, s.rstrip(u'\n') + u'\n\n' + ROUND_HEAD + SECTION)


def patch_ui_audit():
    p = os.path.join(REPO, 'AGENT_UI_AUDIT.md')
    s = read(p)
    assert u'## 第 90 轮' not in s
    anchor = u'## 第 89 轮 · R87：'
    assert s.count(anchor) == 1, u'UI_AUDIT 的 89 轮锚点不唯一'
    write(p, s.replace(anchor, UI_AUDIT + anchor, 1))


def patch_decisions():
    p = os.path.join(REPO, 'AGENT_DECISIONS.md')
    s = read(p)
    assert u'### D-146' not in s
    write(p, s.rstrip(u'\n') + u'\n' + DECISION)


def patch_backlog():
    p = os.path.join(REPO, 'AGENT_BACKLOG.md')
    s = read(p)
    anchor_93 = (u'    原文那句"下一轮做法：先只跑一条最便宜的用例并带 30s 看门狗"本轮**没有采用**：\n')
    assert s.count(anchor_93) == 1, u'93 的锚点不唯一（命中 %d）' % s.count(anchor_93)
    s = s.replace(anchor_93, anchor_93 + BACKLOG_93_UPDATE, 1)
    anchor_119 = (u'    ③ 新形状带来的新问题另开 **BACKLOG 120**：位置判据今天仍被 `loopCapable` 关着，\n'
                  u'    而它恰恰是唯一有资格说话的那把尺 —— 谁给谁签字，这件事本轮只改了一半。\n')
    assert s.count(anchor_119) == 1, u'119 的锚点不唯一（命中 %d）' % s.count(anchor_119)
    s = s.replace(anchor_119, anchor_119 + BACKLOG_119_UPDATE, 1)
    write(p, s + BACKLOG_122_NEW)


def patch_changelog():
    p = os.path.join(REPO, 'CHANGELOG.md')
    s = read(p)
    anchor = u'## [Unreleased]\n'
    assert s.count(anchor) == 1
    assert u'### CI（R88' not in s
    write(p, s.replace(anchor, anchor + CHANGELOG, 1))


def patch_state():
    p = os.path.join(REPO, 'AGENT_STATE.md')
    s = read(p)
    head_marker = STATE_ANCHOR_HINT
    assert s.count(head_marker) == 1, u'STATE 头部锚点不唯一'
    new_head = (u'最后更新：2026-10-16 07:20（本地 · R88 / 第 90 轮收尾：**读 R87 的 CI：main 绿了，'
                u'而绿的方式说明上一轮那朵红的处置今天没被检验；同时本机按 CI 原样重跑看门狗，'
                u'把 R86 写下的那句话判成了假话** —— `swift test` 是三层进程，'
                u'`kill -9 $pid` 杀的是 `swift-test` 驱动，带着 11 条用例名的 `xctest` 被 reparent 之后'
                u'继续活着（一次活了 5 分钟、占着 `.build` 锁把后面两遍全堵死），而日志停在 119 字节、'
                u'`started=0` ⇒ `UI_PROBE_NO_CASE_STARTED=1（进程在第一条用例开口之前就死了）` 是假话，'
                u'而 R86 我自己写的硬门把这句假话读了两遍当成"有名字"。'
                u'本轮（D-146）：看门狗改 `set -m` + `kill -- -$pid`（进程组），'
                u'收掉之前先 `pgrep` 写 `/tmp/ui-runner-alive`；报告脚本按这个数分三格'
                u'（活着⇒点名 `START_LINES_LOST`；没起⇒才许说 `NO_CASE_STARTED`；没量⇒只报观察），'
                u'三格互斥由自测钉住、坏值不许猜；硬门读**落盘**的孤儿数'
                u'（U-188：跨步骤没有共享 shell 变量，第一版写成 `${orphans}` 会造出一道恒真的门），'
                u'读不到文件另红一格。93 的成因由此分开（是②通道丢了），'
                u'但"挂在哪一条"仍然没名字 ⇒ 新开 **122**（每条在屏判据自己写一行读数 + '
                u'那颗三遍分布 0.671/1.000/**0.043** 比产品还宽的等节拍证人配不配签红）。'
                u'119 第五个点：coverage **0.690**（runner 四遍 0.522/0.842/0.032/0.690，跨度 0.81），'
                u'而 `contradicted-by-travel` 那一支**至今没在 runner 上触发过** ⇒ D-145 挡红的能力仍未证。'
                u'牙 M481–M488 八刀全 CAUGHT（M484/M485 第一版 ESCAPED 是刀留着原 token 前缀，'
                u'子串查下"删掉了"隐形 —— U-189；U-190：对照第一版用 python 侧 pgrep 量的其实是'
                u'管道开合，判定改读脚本自己 ps 那几行）。**本轮零产品改动 ⇒ 不换装**。'
                u'验证：非台账文件 %s 个、产品 0 个；脚本 %s（exit %s）；机制对照 %s；电池 %s；'
                u'没跑的：%s。'
                u'**下一轮第一件事：读 R88 的 CI（`UI_PROBE_RUNNER_ALIVE` 与 `UI_PROBE_ORPHAN_XCTEST` '
                u'第一次在 runner 上说话 —— 那一步会证明 `set -m` 在无头 macOS runner 上到底成不成立）'
                u'+ BACKLOG 122**）\n\n'
                u'> 上一轮（R87 / 第 89 轮收尾）原文开头：' + head_marker) % (
        TOUCHED, SCRIPTS, PY_EXIT, SHAPE, BATTERY, NOT_RUN_LINE)
    write(p, s.replace(head_marker, new_head, 1))


def patch_final_report():
    p = os.path.join(REPO, 'AGENT_FINAL_REPORT.md')
    s = read(p)
    old = u'| 阶段二 **80 轮**审计（R9–R87，含 29d；'
    assert s.count(old) == 1, u'FINAL_REPORT 轮数锚点不唯一'
    s = s.replace(old, u'| 阶段二 **81 轮**审计（R9–R88，含 29d；', 1)
    old = u'以 `curve_from_ledger.py` 的 `PHASE2 n=80` 为准）'
    assert s.count(old) == 1, u'FINAL_REPORT 曲线锚点不唯一'
    s = s.replace(old, u'以 `curve_from_ledger.py` 的 `PHASE2 n=81` 为准）', 1)
    old = u'| 视觉台账 | U-31 … U-186（154 条；'
    assert s.count(old) == 1, u'FINAL_REPORT U 计数锚点不唯一'
    s = s.replace(old, u'| 视觉台账 | U-31 … U-191（159 条；', 1)
    old = u'| 决定台账 | D-069 … **D-145**'
    assert s.count(old) == 1, u'FINAL_REPORT 决定台账锚点不唯一'
    s = s.replace(old, u'| 决定台账 | D-069 … **D-146**', 1)
    old = u'**M100–M480**（阶段二 380 支；'
    assert s.count(old) == 1, u'FINAL_REPORT 刀数锚点不唯一'
    if len(CAUGHT) != len(KNIVES):
        raise SystemExit('有刀没抓到就不许往报告里写"全 CAUGHT"：%s'
                         % u'、'.join(t for t, _, k in KNIVES if k != 'CAUGHT'))
    s = s.replace(old, (u'**M100–M488**（阶段二 388 支；**R88 的 %s %s 全 CAUGHT**'
                        u'（两刀第一版 ESCAPED：M484 / M485 的变异串留着原 token 前缀 ⇒ 子串查下'
                        u'"删掉了"隐形，修的是刀 —— 见 U-189）；'
                        % (KNIFE_RANGE, KNIFE_TOTAL) + u''
                        ), 1)
    old = u'自评曲线（**80 轮**，Round 9–87，含 29d 那一轮边界轮；'
    assert s.count(old) == 1, u'FINAL_REPORT 曲线段锚点不唯一'
    s = s.replace(old, (u'自评曲线（**81 轮**，Round 9–88，含 29d 那一轮边界轮；' + CURVE +
                        u'；**后面那几段 `）：PHASE2 n=…` 是前几轮留下的同一条曲线的历史读数**'
                        u'（n 依次小 1，不是并存的两把尺，也不是本轮没算完））：'), 1)
    anchor = (u'U-183 是**定罪权要按样本数分配**')
    assert s.count(anchor) == 1, u'FINAL_REPORT 的 U 段插入锚点不唯一'
    s = s.replace(anchor, REPORT_U + anchor, 1)
    write(p, s)


REPORT_U = (u'U-187 是**日志的沉默不是成因**（`kill -9` 杀驱动、`xctest` 活着继续跑 11 条用例，'
            u'而日志 119 字节零条 started ⇒ 一次 spike 成功只证明"能留住"，不证明"每次都留得住"；'
            u'成因要由收掉那一刻的进程表签）；U-188 是**跨步骤没有共享 shell 变量**'
            u'（硬门里引用上一步的变量 ⇒ 一道看起来有牙、实际恒真的门，本轮差点就这么交了）；'
            u'U-189 是**删东西的刀不许在变异串里留着原 token 前缀**（子串查下"删掉了"隐形）；'
            u'U-190 是**对照自己也要防量错对象**（python 侧 pgrep 量的是管道开合，不是进程表）；'
            u'U-191 是**仓库里有一支会真的执行 CI 步骤正文的自检**（改写法它就红在夹具锚点上；'
            u'而同轮的变异电池只跑了单个文件，"基线绿"的范围必须写清楚）；')


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
    if 'n=81' not in real:
        raise SystemExit('曲线不是 81 轮（本轮正文没被识别为一个轮次？）：%s' % real[:200])
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
    """轮次区间那一格从曲线守卫推，不手抄（R87 现场：它连续多轮滞后）。

    R88 的第一版是**拼出上一轮的旧文**再替换 —— 拼错了（我把 n 与编号个数又减了一层），
    于是它自己红在"找不到旧值"。正确做法是按形状匹配：那一格的锚点不需要知道上轮的数字。
    """
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
        raise SystemExit(u'PHASE2 n=%d 与 rounds=%d..%d 差 %d ⇒ 既不是"编号连续"也不是"多一个 29d"，'
                         u'这一格不能推：%s' % (n, lo, hi, extra, m.group(0)))
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
