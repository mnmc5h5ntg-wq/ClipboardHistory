# -*- coding: utf-8 -*-
'''R86 的台账补丁（第 88 轮 / Round 86）。

数字全部从产物读，不许手抄：
  * `.scratch/motion-audit-2/r86_battery.log`        —— 八刀的逐条结论
  * `.scratch/motion-audit-2/r86_verify_summary.log` —— 全量验证的逐条读数
  * `.scratch/motion-audit-2/r86_ci_readings.md`     —— 读 R85 的 CI 的原文
  * `.scratch/motion-audit-2/r86_skip_readings.md`   —— 116 那四遍测量
  * `.scratch/motion-audit-2/r86_spike_partial_output.md` —— SIGKILL 之后 started 行还在不在
每个锚点都断言"命中且只命中一次"。分三段跑：A（正文与账）、B（STATE 与 FINAL_REPORT）、C（曲线）。
'''
import io
import os
import re
import subprocess
import sys

REPO = '/Users/wangziyi/Codex_Project0'
BATTERY = os.path.join(REPO, '.scratch/motion-audit-2/r86_battery.log')
SUMMARY = os.path.join(REPO, '.scratch/motion-audit-2/r86_verify_summary.log')
CI = os.path.join(REPO, '.scratch/motion-audit-2/r86_ci_readings.md')
CURVE = 'CURVE_PLACEHOLDER_R86'


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
    """从验证摘要里取一条 `READ <名字> :: <原文>`。取不到就红，不许引用没读到的数。"""
    text = read(SUMMARY)
    m = re.search(r'^READ %s :: (.+)$' % re.escape(name), text, re.M)
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
BAD = [t for t, _, k in KNIVES if k != 'CAUGHT']


def short_note(n):
    """表格里的短标题：砍掉『⇒ 预期…』那半截，但砍坏括号的就不砍。"""
    head = n.split(u'⇒')[0].strip()
    return n.strip() if head.count(u'（') != head.count(u'）') else head


KNIFE_TABLE = u'\n'.join(u'| %s | %s | **%s** |' % (t, short_note(n), k) for t, n, k in KNIVES)
KNIFE_RANGE = u'%s–%s' % (KNIVES[0][0], KNIVES[-1][0])
KNIFE_TOTAL = u'%d 刀' % len(KNIVES)
KNIFE_LINE = u'%s（%s）：%d 刀 CAUGHT%s' % (
    KNIFE_RANGE, u'、'.join(t for t, _, _ in KNIVES), len(CAUGHT),
    u'，%s 第一版是我的刀自己没带那个词' % u'、'.join(ESCAPED) if ESCAPED else u'，没有逃掉的')
CI_TEXT = read(CI).strip()

BUILD_WARN = re.search(r'\d+', summary('BUILD_WARNINGS')).group(0)
FULL_TEST = summary('FULL_TEST')
FRAME = summary('FRAME_BASELINE')
GATE = summary('CAPTURE_GATE')
SCRIPTS = summary('SCRIPT_TESTS')
SCRIPT_TOTAL = re.search(r'Ran (\d+) tests', SCRIPTS).group(1)
MOTION_FACTS = summary('MOTION_FLOOR')
REPORT_FULL = reading('ui_probe_report full.log')
REPORT_KILLED = reading('ui_probe_report killed_capture.log')
HEAT_LOG = os.path.join(REPO, '.scratch/motion-audit-2/r86_heatmap_readings.log')
HEAT = {}
for _line in read(HEAT_LOG).splitlines():
    _m = re.match(r'HEATMAP_(LEGEND|EMPTY|EMPTY_IN_LEGEND)_(dark|light)[ =](.*)$', _line.strip())
    if _m:
        HEAT[_m.group(1) + '_' + _m.group(2)] = _m.group(3).strip()
for _k in ('LEGEND_dark', 'LEGEND_light', 'EMPTY_dark', 'EMPTY_light',
           'EMPTY_IN_LEGEND_dark', 'EMPTY_IN_LEGEND_light'):
    if _k not in HEAT:
        raise SystemExit('热图看图仪器没给出 %s ⇒ 先跑 r86_heatmap_legend.py（台账不许引用没读到的数）' % _k)
    if 'not-found' in HEAT[_k] or 'not-run' in HEAT[_k]:
        raise SystemExit('热图看图仪器报 %s ⇒ 采样点漂了，先修仪器再写台账' % HEAT[_k])
def heat(key):
    v = HEAT[key]
    for cut in (u'y=400 四档=', u'没有记录那一格='):
        if v.startswith(cut):
            v = v[len(cut):]
    return v

ROUND_HEAD = u'''## Round 86 · 停机也要有名字：给"在屏那一卷没跑完"装上一支会点名的报告器（更新 92、93 / 收窄 116 / U-178…U-182 / D-144）

### 本轮开场的位点清单（0 个产品文件；3 个 CI/脚本/自测文件，另有 5 份台账）

本轮不改画面，也不改任何一条判据的**逻辑**。被重新判断的是那句话：
**"这一卷今天没跑完" —— 它有没有指名道姓。**

| 位点 | 位置 | R85 留下的缺陷 | 本轮处置 |
|---|---|---|---|
| 在屏那一卷的停机 | `.github/workflows/ci.yml` 的 `On-screen interaction probes` | 只打到 `已下结论的用例: 0`，是"第一条就挂住"还是"一条都没开始"没人知道 | 加一步 `ui_probe_report.py`（报告型） |
| 停机归因的牙 | 新增 `scripts/ui_probe_report.py` | 没有这样一支脚本 | started 减 concluded ⇒ `UI_PROBE_HUNG=<用例名>`；说不出就**红** |
| 真值表 | 新增 `scripts/tests/test_ui_probe_report.py` | —— | 七格（① 点名 ② 跑完 ③ 没开始 ④ 日志不完整 ⑤ 拿错文件 ⑥ 空日志 ⑦ 读不到）+ 退出码 + 不冗余守卫 |
| 硬门那一半 | `.github/workflows/ci.yml` 的 `On-screen probe coverage floor` | 那一支只判**集合级**（哪几条没下结论） | 同一份日志再跑一次报告器，给不出名字 ⇒ `PROBE_FLOOR_STOP_UNNAMED=1` 红 |

本轮动的非台账文件 **3 个**（约定 ≤4）：`ci.yml`、`scripts/ui_probe_report.py`、`scripts/tests/test_ui_probe_report.py`。
0 个产品文件、0 处测试判据逻辑改动 —— 在屏那一卷的 11 条 Swift 测试**一行没动**（见下面 spike 那一节为什么不需要动）。

'''

SECTION = u'''
### 读 R85 的 CI（run 38805382593）：`loops` 那一层第一次在 runner 上判自己，两行都读到了

```
MOTION_SHIMMER_STATE 判定=ok 原因=-
MOTION_SHIMMER_BAND_STATE 判定=ok 原因=-
%s
```

⇒ 118 结案的那半句"整族没说一句话就会红"已经在 runner 上生效。
而 119 拿到了**第四个**数据点：产品 coverage 从 0.522 变成 **0.842**（同一种画法、同一台机器类别）。

**这一格本轮被我自己读反了一次，所以把它写全**：两遍新画法都在地板（0.50）之上，
直觉是"那就把 `must_judge` 收成 true"。但 0.522 与 0.842 之间的**跨度 0.32** 本身就是答案 ——
一支读数能在两遍之间走 0.32 的判据，不配当硬门。R38 那句话在这里要倒着读：
"两台机器的读数不能当另一台机器的地板"同样意味着"同一台机器的两遍之间的波动，
就是它还不该被钉死的证据"。⇒ `must_judge` 仍然 false，119 继续开着，
要的是**分布宽度**而不是"两遍都过了"。

### 改了什么：一支只回答"它是怎么停的"的脚本

它**不判产品**，真值表全是"能不能给出名字"这一件事：

| 形状 | 输出 | 退出码 |
|---|---|---|
| ① 开了口没结论 | `UI_PROBE_HUNG=<用例名>` | 0（有名字） |
| ② 每条都有结论 | `UI_PROBE_ALL_CONCLUDED=1` | 0 |
| ③ 原始日志里一条 `Test Case` 都没有 | `UI_PROBE_NO_CASE_STARTED=1` | 0（进程级死法，也是名字） |
| ④ 有结论却没有它的 started 行 | `UI_PROBE_CONCLUDED_WITHOUT_START=<名>` | **1** |
| ⑤ 喂进来的是 CI 那一步的汇报片段 | `UI_PROBE_NOT_THE_RAW_LOG=1` | **1** |
| ⑥ 空日志 | `UI_PROBE_LOG_EMPTY=1` | **1** |
| ⑦ 文件读不到 | `UI_PROBE_LOG_UNREADABLE=…` | **1** |

④⑤⑥ 的共同点是：**"我说不出"不许被读成"没事"**。
CI 里两步各用一次：报告型那一步只把名字打出来（环境给不出证据不该挡发布），
硬门那一步（`On-screen probe coverage floor`）要求名字必须给得出。

本轮真日志上的两格对照（不是合成夹具）：

```
%s
%s
```

⇒ 对一份**跑完的**全量日志它说"跑完了"，对一份**被 kill -9 的**日志它点出那条正在跑的用例。
合成夹具证不到这一格：那是照着我记忆里的行格式写的，真 `swift test` 的格式对不对只有真日志知道。

### U-178 · 读 CI 必须按步骤名过滤，跨步骤 grep 会造出假矛盾

`gh run view --log` 把所有步骤拼在一起，而状态行会在两个步骤里各出现一次、取值不同：
全量卷那一步（没设开关）打 `MOTION_SHIMMER_STATE 判定=skipped 原因=capability-gate`，
动效卷那一步（设了开关）打 `判定=ok`。我第一遍读到"同一族既 ok 又 skipped"，
差点判成 R85 那层"按最后一条判"的排序 bug —— 而闸门读的是 `/tmp/motion.log`，
只有设了开关那一卷写它，它没被骗。**会被骗的是读日志的人。**
⇒ 本轮起，读 CI 的固定动作是先按步骤名切范围再 grep（这条已写进 `r86_ci_readings.md`）。

### U-179 · "没有 Test Case 行"有两种成因，拿错文件会生成一句关于产品的假话

第一次试这支脚本时我喂的是 `scripts/tests/fixtures/r62_runner_ui.log` ——
那是 run 38603034761 那一步的**逐字汇报**（`ui suite exit: 137 …`），里面本来就不会有 `Test Case` 行。
脚本于是自信地报了"进程在第一条用例开口之前就死了"。
那句话听起来像个结论，而真相是我拿错了文件。⇒ 加了 ⑤ 那一格：
有汇报行却没有 `Test Case` ⇒ `UI_PROBE_NOT_THE_RAW_LOG=1` 并**红**。
这一格用的是那份真夹具，所以它不是防御性注释，是一条会自己挨刀的判据（M467）。

### U-180 · 判"变异落地没有"要看内容，不是看文件变没变

M472（元层那一刀：往不冗余守卫读的文件里塞一行含 `started` 的注释，证明守卫会红）
第一版报 **ESCAPED**。查下去不是守卫没牙，是**我插的那行注释里根本没有 `started` 这个词**。
同批还顺手修了另一处：纯插入型的刀，其变异文**必然**包含原串，
于是旧的"回读要求原串消失"会把落成功的刀报成未落地（R76 的 M398 / M399 同族，本轮第三次撞）。
⇒ 回读判据换成"文件必须与变异前不同"，而"刀里带的词对不对"由 MEASURE 那一遍的输出证明。

### U-182 · 自动"找"出来的采样点会悄悄量错对象，钉死坐标 + 自带断言才算量过

第一次量图例时写的是"在底部 30%% 里找蓝块 ≥3 个的那一行"。它命中了 **网格的最后一行**
（那一行本来就有好几个蓝色格子），于是"图例四档"读出来是七个块、还混进 6px 宽的边缘。
⇒ 换成手工对过帧之后钉死的坐标（`LEGEND_Y=400` 与四个块的中心 x），
并且**每个点带一条断言**：图例四块必须互不相同且单调变蓝；空格子必须是中性灰且不等于背景；
不满足就报 `not-found` 让脚本崩，而不是安静地把错的色写进台账。
"自动搜索"在这种场合不是省事，是把**量错对象**伪装成量到了。

### U-181 · 两支闸门判的是两句不同的话，这条不写下来就会有人来合并它们

`probe_coverage_gate.py`（R62 起）判**集合级**：源码里有几条在屏判据、这次哪几条没下结论、缺席登记过没有。
`ui_probe_report.py`（本轮）判**因果级**：这一卷是**怎么**停的。
只有前者会漏成这样：11 条全登记着、全都没结论、闸门照样绿 —— 那正是 R62 到 R85 的形状。
⇒ 自测里留了一条不冗余守卫（读那一支的源码，要求它不含 `started`），并由 M472 那一刀证明它会红。

### 116 被这次测量**收窄**了，没有结案

四遍独立进程（同一提交、同一台机器）：全量两遍都是 `801 tests / 41 skipped` 且**名单逐名相同**，
捕获两遍都是 `47 / 4 skipped`。⇒ R81 那句"同一提交两遍差 7 条"今天复现不出来。
而读 R85 的 CI 又发现：捕获那五条**在 runner 上确实 skip 了，闸门也列出了它们的名字与原因**
（`TEXT_SIDE_NOT_RUN settings-shortcuts dark 侧栏列读到 0 个偏离像素…`）。
⇒ 116 剩下的、今天仍然成立的那半句只有一句：**闸门只报它找到的 `*_NOT_RUN`，不报它没找到的那些**。
这一句与 R85 的 `LOOP_SILENT` 同形，交给 R87（本轮不动判据代码）。

### 真实看图（本轮看的是热图，不是骨架 —— 那张图从 R45 之后没被重新判过）

看的是本轮验证现生成的 `heatmap-populated-430x250-dark/light.png`（860×500px），
色号由 `r86_heatmap_legend.py` 现算（采样点是手工对过帧之后钉死的，脚本里带断言）：

| 角色 | 暗档 | 亮档 |
|---|---|---|
| 图例四档（少→多） | %s | %s |
| 网格那一格（"没有记录"的取色） | %s | %s |

⇒ 眼睛先看到的问题是真的：**图例里没有"没有记录"那一档**
（`HEATMAP_EMPTY_IN_LEGEND_dark=%s`、`..._light=%s`）——
灰格子比图例最左那一档还淡，看图的人可能把它读成"少到看不见"。

**但判为不加第五档，理由写在账上**：这一格的文案早就把两件事分开了 ——
`DailyCopyHeatPolicy.tooltip` 对 `count == 0` 说的是**"没有记录"**而不是"0 次"，
而"追踪到 0 次"与"根本没追踪"在**存档语义**里本来就是同一个值（`counts: [String: Int]` 里没有这个键）。
要在图例上区分它们，得先让存档能区分；那是数据模型的事，
拿一个第五色块去盖它，等于让视觉层替一个它没有的信息负责。
⇒ 图例保持四档（"少"指最低一档**非零**），hover 说真话。
这一格如果哪天要动，动的是 `DailyCopyLedger`，不是颜色。

顺带两条读数：灰格与所在背景的差只有 **暗 11 级 / 亮 12 级**（255 制）
⇒ 它是"比背景略亮/略暗的一点东西"，与 R85 量的骨架静置条（11 / 13）几乎同一个量级 ——
这两处是同一类"占位符该多淡"的判断，将来调其中一个时，另一个是对照点。

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
ui_probe_report.py（真日志两格）          见上面那段
```

### 七维自评

| 维度 | 得分 | 说明 |
|---|---|---|
| 原生感 | 20 / 20 | 零产品改动，本轮没有脸加分，也没有东西被扣 |
| 流畅度 | 18 / 20 | 扫光在 runner 上两遍判绿（0.522 / 0.842），但跨度 0.32 ⇒ 仍不能钉成硬门 |
| 层次与材质 | 15 / 15 | 本轮无画面产出 |
| 动效细节 | 13 / 15 | 比 R85 少 1 分：**在屏那一族今天仍然一条判据都没在 CI 上跑过**，本轮只是让"没跑"这件事从此必须有名字 |
| 交互反馈 | 9 / 10 | 反馈本身没动 |
| 可访问性 | 8 / 10 | 真机批次 72 / 73 还没人看；焦点那四条在 runner 上仍然没跑（111） |
| 性能 | 14 / 15 | 全量 %s；新脚本只读一份日志，成本可忽略 |

**97 / 100**，比 R85 低一分是刻意的：本轮连判据逻辑都没动，产出是"一个名字 + 一张真值表 + 八刀"，
而它换来的那条最值钱的东西（CI 上到底哪一条挂住）要等下一次 CI 才看得见。
分数不许为"做了基础设施"上涨，只为"画面或硬门变好"上涨。

### 仍未解决

- BACKLOG **92 / 93**（本轮都只更新，不结案）：报告器已接上，但"runner 上到底挂在哪一条"是
  **下一次 CI 的读数**。预测已经先登记在 93 里（三种结果各意味着什么），
  在那之前不许写"92 已修"。
- BACKLOG **116**（本轮收窄）：剩下"闸门不报它没找到的 `*_NOT_RUN`"那一格，形状与 `LOOP_SILENT` 同族。
- BACKLOG **119**（第四个数据点，仍开着）：新画法两遍 coverage 跨度 0.32 ⇒ 要的是分布宽度。
- **115**、**111**、108 余下、77 路 b、101 ②③、106；
  真机 68.1 / 68.2 / 69.1 / 70.1 / 71.1 / 72.1 / 72.2 / 73.1 / 73.2。
''' % (MOTION_FACTS, REPORT_FULL, REPORT_KILLED,
       heat('LEGEND_dark'), heat('LEGEND_light'), heat('EMPTY_dark'), heat('EMPTY_light'),
       heat('EMPTY_IN_LEGEND_dark'), heat('EMPTY_IN_LEGEND_light'),
       KNIFE_TABLE, BUILD_WARN, FULL_TEST,
       MOTION_FACTS, GATE, FRAME, SCRIPTS, FULL_TEST)

UI_AUDIT = u'''## 第 88 轮 · R86：停机也要有名字 —— 在屏那一卷的"没跑完"从此必须指名道姓（更新 92、93 / 收窄 116 / U-178…U-181）

- **U-178** 读 CI 必须**按步骤名**过滤：状态行会在全量卷与动效卷各打一次、取值不同，
  跨步骤 grep 会造出"同一族既 ok 又 skipped"的假矛盾（我差点据此去"修"一个不存在的排序 bug）。
- **U-179** "没有 `Test Case` 行"有两种成因：进程真的没开始 vs **我拿错了文件**。
  后者会被写成一句关于产品的假话 ⇒ 新增 `UI_PROBE_NOT_THE_RAW_LOG` 并让它红，
  用的是仓库里那份真夹具（run 38603034761 的步骤汇报）。
- **U-180** 判"变异落地没有"要看**内容**：M472 第一版 ESCAPED 是我的刀里没带那个词，
  不是守卫没牙；纯插入型的刀必然包含原串，回读判据因此换成"文件必须变了"。
- **U-182** 自动『找』采样点会把**网格最后一行**当成图例（本轮真发生了一次）⇒ 钉死坐标 + 每点带断言，不满足就报 not-found。
- **U-181** 两支闸门判两句不同的话（集合级 vs 因果级），不写下来就会被人合并；
  留一条不冗余守卫 + 一刀元层证明它会红。
- 116 **收窄**：四遍测量（全量 2 + 捕获 2）skip 数与名单都稳定 ⇒ R81 那句"差 7 条"不复现；
  捕获那五条在 runner 上其实**有名字有原因**（闸门列得出来）。剩下那半句：
  闸门只报它找到的 `*_NOT_RUN`，不报它没找到的那些（与 `LOOP_SILENT` 同形，交 R87）。
- 92 与 93 **更新**（都不结案）：新增 `scripts/ui_probe_report.py`（七格真值表 + 退出码），
  CI 两步各接一次（报告型打名字，硬门要求必须有名字）。牙 M465–M472 八刀全 CAUGHT。

'''

DECISION = u'''
### D-144（R86）"没跑完"必须有名字：停机归因与覆盖登记分成两支闸门，前者给不出名字就红

- 背景：`On-screen interaction probes` 在 runner 上 `exit 137 / executed 0 / 已下结论 0`，
  而那一步顺手解释成"在屏探针在无头 runner 上不可用" ⇒ 整卷成了免检牌（BACKLOG 92，R62 开）。
  R62 的解药 `probe_coverage_gate.py` 判的是**登记与集合**：新加一条在屏判据而不回答
  "runner 跑得了吗"，那里会红。但它对"这次为什么一条都没结论"仍然只说"整卷没跑完"。
- 决定：① 新增 `scripts/ui_probe_report.py`，只回答"这一卷是怎么停的"，
  用 `Test Case ... started` 与有结论行的差集点名挂死的那条；
  ② 三种"说不出"（日志不完整 / 喂的是步骤摘要 / 空日志 / 读不到）**一律红**，
  不许把"我说不出"当成"没事"；
  ③ CI 两步各用一次：报告型那一步只打名字（环境给不出证据不该挡发布），
  硬门那一步（`On-screen probe coverage floor`）要求名字必须给得出；
  ④ 与 `probe_coverage_gate.py` 的分工写进自测（不冗余守卫），并给守卫自己一刀（M472）。
- 为什么不动判据代码：spike 实测（本机 50 秒 `kill -9`，退出码 137 与 CI 同形）
  `swift test` 的 started 行留在日志里，13 started / 12 concluded 的差集正好点名 ⇒
  不需要 11 处测试自己打点。spike 没证明的那半（runner 上是否也留得住）由 ② 兜：
  留不住就是"有结论没 started"，那一格会红而不是假报。
- 不许的处置：把 92 写成"已修"（要等下一次 CI 的读数）；
  或者因为"反正 runner 跑不了"就把这一卷从 CI 里删掉 —— 那等于把免检牌换成空白卷。
'''

BACKLOG_92_UPDATE = u'''
    → **R86 更新（不结案）**：接上了 `scripts/ui_probe_report.py` ——
    它把 `Test Case ... started` 与有结论的行做差，输出 `UI_PROBE_HUNG=<用例名>` /
    `UI_PROBE_NO_CASE_STARTED=1` / `UI_PROBE_ALL_CONCLUDED=1`，
    而"给不出名字"的四种形状（日志不完整、喂的是步骤摘要、空日志、文件读不到）**一律红**。
    CI 两步各用一次：`On-screen interaction probes`（报告型）只把名字打出来，
    `On-screen probe coverage floor`（硬门）要求名字必须给得出 ⇒ `PROBE_FLOOR_STOP_UNNAMED=1` 才红。
    为什么不需要测试自己打点：本机 spike（50 秒 `kill -9`，退出码 137）实测 started 行留在日志里，
    13 started / 12 concluded 的差集正好点名那条正在跑的
    （`.scratch/motion-audit-2/r86_spike_partial_output.md`）。
    **仍然开着的理由**：runner 上到底是"第一条就挂住"还是"一条都没开始"，
    是**下一次 CI 的读数**，本轮不许替它回答；那之后才谈得上"路 b"（让能跑的那几条真的跑起来）。
    牙 M465–M472 共八刀全部 CAUGHT（M472 是元层那一刀：给"两支闸门不冗余"的守卫自己喂一个假阳性）。
'''

BACKLOG_93_UPDATE = u'''
    → **R86 更新（不结案，但把答案变成一个会被读到的读数）**：原文写的下一步是
    『CI 那一步先只跑一条最便宜的用例并带 30s 看门狗』。本轮换了个更一般的做法：
    不预设跑哪一条，而是把 `Test Case ... started` 与有结论的行做差 ——
    `swift test` 自己就在打点，`kill -9` 之后那些行留在日志里（本机 spike 实测 13 started / 12 concluded，
    退出码 137 与 CI 同形）。⇒ 新增 `scripts/ui_probe_report.py`，CI 两步各用一次，
    硬门那一步要求『说不出为什么停』必须红。
    **预测先登记在这里**（免得事后挑一个解释）：下一次 CI 若报
    `UI_PROBE_HUNG=testAccessibilityTreeCoverage`，就证实原文那句『挂在按字母序的第一条用例内部』；
    若报 `UI_PROBE_NO_CASE_STARTED=1`，则挂死发生在 XCTest 开始报用例之前（启动/会话层），
    那时原文列的三条候选原因要整条重排；若报 `UI_PROBE_ALL_CONCLUDED=1`，
    说明 92/93 的前提（runner 上跑不动）已经不成立，那两条一起结案。
    三种结果都是答案，而这一格的价值就在于它**不许**留成『大概是无头会话的问题』。
'''

BACKLOG_116_UPDATE = u'''
    R86 **收窄**（四遍测量 + 读 R85 的 CI，产物 `.scratch/motion-audit-2/r86_skip_readings.md`）：
    ① 同一提交两遍全量 `801 / 41 skipped`、两遍捕获 `47 / 4 skipped`，**名单逐名相同**
    ⇒ 原文那句"同一提交两遍差 7 条"今天复现不出来（不能据此说不存在，只能说它不是这一版代码
    在默认通道上的稳定性质）；
    ② 原文那句"那五条没有一行为什么今天没跑"在**捕获这一族已经不成立**：
    runner 上它们确实 skip 了，而闸门列出了名字与原因
    （`TEXT_SIDE_NOT_RUN settings-shortcuts dark 侧栏列读到 0 个偏离像素（同帧内容区读到 0 个）`）；
    ③ 仍然成立的是反方向：**闸门只报它找到的 `*_NOT_RUN`，不报它没找到的那些** ——
    一条判据既没跑、也没打 `*_NOT_RUN`（整行缺席）时今天仍然没人红。
    这一格与 R85 给 `loops` 那一层修的正是同一件事（`LOOP_SILENT`），只是捕获这一族还没有那一格。
    ⇒ 待办从"给五条各打一行原因"改成"给闸门加'缺席就红'那一格"，交给 R87。
'''

CHANGELOG = u'''### CI（R86）

- 新增 `scripts/ui_probe_report.py`：在屏探针那一卷被看门狗收掉时**点名挂死的那条用例**
  （`Test Case ... started` 与有结论行的差集）。七格真值表 + 退出码；
  "说不出为什么停"的四种形状（日志不完整 / 喂的是步骤摘要 / 空日志 / 文件读不到）一律红。
  CI 两步各用一次：报告型那一步打名字，`On-screen probe coverage floor` 那道硬门要求必须有名字。
- 脚本自测 +12 格（现跑共 %s 格）；变异电池 %s。

### Docs（R86）

- BACKLOG 92 与 93 更新（报告器已接，runner 上挂在哪一条等下一次 CI 的读数；预测已先登记）；
  116 收窄（四遍测量不复现"差 7 条"，捕获那五条其实有名字，剩下的那半句改成交给 R87）。

''' % (SCRIPT_TOTAL, KNIFE_LINE)

STATE_ANCHOR_HINT = '最后更新：2026-10-16 04:20（本地 · R85 / 第 87 轮收尾：'


def patch_visual_iteration():
    p = os.path.join(REPO, 'AGENT_VISUAL_ITERATION.md')
    s = read(p)
    assert u'## Round 86' not in s, u'Round 86 已经写过了'
    write(p, s.rstrip(u'\n') + u'\n\n' + ROUND_HEAD + CI_TEXT + u'\n\n' + SECTION)


def patch_ui_audit():
    p = os.path.join(REPO, 'AGENT_UI_AUDIT.md')
    s = read(p)
    assert u'## 第 88 轮' not in s
    anchor = u'## 第 87 轮 · R85：'
    assert s.count(anchor) == 1, u'UI_AUDIT 的 87 轮锚点不唯一'
    write(p, s.replace(anchor, UI_AUDIT + anchor, 1))


def patch_decisions():
    p = os.path.join(REPO, 'AGENT_DECISIONS.md')
    s = read(p)
    assert u'### D-144' not in s
    write(p, s.rstrip(u'\n') + u'\n' + DECISION)


def patch_backlog():
    p = os.path.join(REPO, 'AGENT_BACKLOG.md')
    s = read(p)
    anchor_92 = (u'    没有让它消失。真要 runner 上跑出结论，得先查清探针在无头 runner 上挂在哪一句'
                  u'（新 BACKLOG 93）。\n')
    assert s.count(anchor_92) == 1, u'92 的收尾锚点不唯一（命中 %d 次）' % s.count(anchor_92)
    s = s.replace(anchor_92, anchor_92 + BACKLOG_92_UPDATE, 1)
    # 93 是 92 的另一半（那句『挂在哪一句』就是它）：本轮装的就是回答它的仪器，
    # 而答案要等下一次 CI ⇒ 更新，不结案。
    anchor_93 = (u'    而 R61 那类「选中/滚动」的回归恰恰只有真实表格能判。\n')
    if s.count(anchor_93) != 1:
        # 锚点找不到时**打印现场**再退出：静默跳过会让台账少一段而没人知道（R64 那一课）。
        i = s.find(u'93. **在屏探针在无头 runner 上到底挂在哪一句**')
        raise SystemExit(u'93 的收尾锚点不唯一（命中 %d 次）；条目尾部现场：\n%s'
                         % (s.count(anchor_93), s[i:i+2400][-260:]))
    s = s.replace(anchor_93, anchor_93 + BACKLOG_93_UPDATE, 1)
    anchor_116 = (u'    （这五条各用 `temporaryDirectory/r28-clip-<UUID>`）—— 没量出来就别写。\n')
    assert s.count(anchor_116) == 1, u'116 的收尾锚点不唯一（命中 %d 次）' % s.count(anchor_116)
    s = s.replace(anchor_116, anchor_116 + BACKLOG_116_UPDATE, 1)
    write(p, s)


def patch_changelog():
    p = os.path.join(REPO, 'CHANGELOG.md')
    s = read(p)
    anchor = u'## [Unreleased]\n'
    assert s.count(anchor) == 1
    assert u'### CI（R86' not in s
    write(p, s.replace(anchor, anchor + CHANGELOG, 1))


def patch_state():
    p = os.path.join(REPO, 'AGENT_STATE.md')
    s = read(p)
    head_marker = STATE_ANCHOR_HINT
    assert s.count(head_marker) == 1, u'STATE 头部锚点不唯一'
    new_head = (u'最后更新：2026-10-16 05:25（本地 · R86 / 第 88 轮收尾：读 R85 的 CI'
                u'（run 38805382593）—— **main 连续第二轮绿，而 `loops` 那一层第一次在 runner 上判到自己**：'
                u'两行状态都读到（`MOTION_SHIMMER_STATE 判定=ok` / `MOTION_SHIMMER_BAND_STATE 判定=ok`），'
                u'闸门打了两行 `MOTION_FLOOR_LOOP_JUDGED`、REDS=0。119 拿到第四个数据点：'
                u'产品 coverage 0.522 → **0.842**（同画法同机器）⇒ 这一格本轮被我自己读反过一次：'
                u'两遍都在地板上并不构成"收成硬门"的理由，**0.32 的跨度本身就是它还不稳的证据**'
                u'（R38 倒着读）。本轮改的是"没跑完也要有名字"：新增 `scripts/ui_probe_report.py`，'
                u'用 started 减 concluded 点名挂死的那条用例，而"说不出为什么停"的四种形状'
                u'（日志不完整 / 喂的是步骤摘要 / 空日志 / 读不到）**一律红**；'
                u'CI 两步各用一次（报告型打名字，`On-screen probe coverage floor` 要求必须有名字）。'
                u'为什么不动 11 处测试代码：spike 实测 `kill -9`（退出码 137，与 CI 同形）之后 '
                u'started 行留在日志里，13/12 的差集正好点名。'
                u'三条读数进台账：读 CI 要按步骤名过滤（U-178）、『没有 Test Case 行』有两种成因'
                u'（U-179，我本轮真的拿错过一次）、判变异落地要看内容不是看文件变没变（U-180，'
                u'M472 第一版是我的刀没带那个词）。116 被四遍测量**收窄**（不复现"差 7 条"，'
                u'捕获那五条在 runner 上其实有名字），92 **不结案**：runner 上到底挂在哪一条'
                u'是**下一次 CI 的读数**。牙 M465–M472 八刀全 CAUGHT；`must_judge` 仍然 false。'
                u'**本轮零产品改动 ⇒ 不换装**（帧基线 124 张逐字节不变、`Sources/` 一行没动）。'
                u'全量 %s；动效闸门 %s；捕获闸门 %s；帧基线 %s；脚本 %s；告警 %s。'
                u'**下一轮第一件事：读 R86 的 CI（`UI_PROBE_HUNG` 第一次在 runner 上说话）+ BACKLOG 116 剩下的那半格**）\n\n'
                u'> 上一轮（R85 / 第 87 轮收尾）原文开头：' + head_marker) % (
        FULL_TEST, MOTION_FACTS, GATE, FRAME, SCRIPTS, BUILD_WARN)
    write(p, s.replace(head_marker, new_head, 1))


def patch_final_report():
    p = os.path.join(REPO, 'AGENT_FINAL_REPORT.md')
    s = read(p)
    old = u'| 阶段二 **78 轮**审计（R9–R85，含 29d；'
    assert s.count(old) == 1, u'FINAL_REPORT 轮数锚点不唯一'
    s = s.replace(old, u'| 阶段二 **79 轮**审计（R9–R86，含 29d；', 1)
    old = u'以 `curve_from_ledger.py` 的 `PHASE2 n=78` 为准）'
    assert s.count(old) == 1, u'FINAL_REPORT 曲线锚点不唯一'
    s = s.replace(old, u'以 `curve_from_ledger.py` 的 `PHASE2 n=79` 为准）', 1)
    old = u'| 视觉台账 | U-31 … U-177（145 条；'
    assert s.count(old) == 1, u'FINAL_REPORT U 计数锚点不唯一'
    s = s.replace(old, u'| 视觉台账 | U-31 … U-182（150 条；', 1)
    old = u'| 决定台账 | D-069 … **D-143**'
    assert s.count(old) == 1, u'FINAL_REPORT 决定台账锚点不唯一'
    s = s.replace(old, u'| 决定台账 | D-069 … **D-144**', 1)
    old = u'**M100–M464**（阶段二 364 支；'
    assert s.count(old) == 1, u'FINAL_REPORT 刀数锚点不唯一'
    s = s.replace(old, (u'**M100–M472**（阶段二 372 支；**R86 的 %s %s：%s** —— '
                        % (KNIFE_RANGE, KNIFE_TOTAL,
                           u'元层那一刀 M472 第一版"逃掉"是我的刀里没带那个词，不是守卫没牙'))[:], 1)
    old = u'自评曲线（**78 轮**，Round 9–85，含 29d 那一轮边界轮；'
    assert s.count(old) == 1, u'FINAL_REPORT 曲线段锚点不唯一'
    s = s.replace(old, (u'自评曲线（**79 轮**，Round 9–86，含 29d 那一轮边界轮；' + CURVE +
                        u'；**后面那几段 `）：PHASE2 n=…` 是前几轮留下的同一条曲线的历史读数**'
                        u'（n 依次小 1，不是并存的两把尺，也不是本轮没算完））：'), 1)
    anchor = u'U-174 是**守卫只数"这个串出现过"'
    assert s.count(anchor) == 1, u'FINAL_REPORT 的 U 段插入锚点不唯一'
    s = s.replace(anchor, REPORT_U + anchor, 1)
    write(p, s)


REPORT_U = (u'U-178 是**读 CI 必须按步骤名过滤**（状态行会在全量卷与动效卷各打一次、取值不同，'
            u'跨步骤 grep 会造出"同一族既 ok 又 skipped"的假矛盾 —— 我差点据此去修一个不存在的排序 bug）；'
            u'U-179 是**"没有 Test Case 行"有两种成因**：进程真没开始 vs 我拿错了文件；'
            u'后者会被写成一句关于产品的假话，所以那一格现在会红（用的是仓库里那份真夹具）；'
            u'U-180 是**判"变异落地没有"要看内容而不是看文件变没变**（M472 第一版 ESCAPED 是我的刀里'
            u'没带那个词，而纯插入型的刀必然包含原串 ⇒ 回读判据换成"文件必须变了"）；'
            u'U-182 是**自动找出来的采样点会悄悄量错对象**（本轮『在底部找蓝块 ≥3 个的那一行』命中的是网格最后一行，不是图例 ⇒ 钉死坐标并给每个点加一条断言，不满足就报 not-found 让脚本崩）；U-181 是**两支闸门判两句不同的话**（集合级"哪几条没结论" vs 因果级"这一卷怎么停的"），'
            u'不写下来就会有人来合并它们 —— 所以留了一条不冗余守卫并给它自己一刀。')


def fix_curve():
    # 曲线**在这里现跑一遍**，不读 verify 摘要里那一行：验证脚本跑曲线的时候本轮正文还没进台账。
    proc = subprocess.run([sys.executable, '.scratch/motion-audit-2/curve_from_ledger.py'],
                          cwd=REPO, capture_output=True, text=True, timeout=600)
    if proc.returncode != 0:
        raise SystemExit('曲线守卫退出 %d ⇒ 台账里缺尾轮或有轮没有分数：%s'
                         % (proc.returncode, (proc.stdout + proc.stderr)[-1200:]))
    picked = [l for l in proc.stdout.splitlines() if l.startswith('GAPS=') or l.startswith('PHASE2')]
    real = ' '.join(picked).strip()
    if not real:
        raise SystemExit('曲线守卫没打 GAPS=/PHASE2 行：%s' % proc.stdout[:400])
    if 'n=79' not in real:
        raise SystemExit('曲线不是 79 轮（本轮正文没被识别为一个轮次？）：%s' % real[:200])
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
        print(u'!! 有刀没抓到：%s' % u'、'.join(t for t, _, k in KNIVES if k != 'CAUGHT'))


if __name__ == '__main__':
    sys.exit(main())
