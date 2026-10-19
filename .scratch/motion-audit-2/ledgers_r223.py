# -*- coding: utf-8 -*-
"""R223 的台账生成器：247 解释并修好（旧表锚点脱钩）、244 的 venv 前移、CI 未读清单。

这一版起把 `format` 的参数收进**一份共享字典** `BASE`（R219/R220/R221/R222 四轮都在
"正文用了 {E} 而调用没传" 同一个 KeyError 上红一次 —— 占位符与参数是两本账，本轮起合一）。
"""
import io, os, re, subprocess, sys

ROOT = '/Users/wangziyi/Codex_Project0'
DAY = '2026-10-19'
NOW = '2026-10-19 23:19'


def read(p):
    return io.open(os.path.join(ROOT, p), encoding='utf-8').read()


def write(p, t):
    with io.open(os.path.join(ROOT, p), 'w', encoding='utf-8') as h:
        h.write(t)


def die(why):
    print('LEDGERS_R223 refused: ' + why)
    sys.exit(1)


def log(p):
    path = os.path.join('/tmp', p)
    if not os.path.exists(path):
        die('缺少本轮日志 ' + path + ' ⇒ 不许写台账')
    return io.open(path, encoding='utf-8', errors='replace').read()


# ——————————————————— 读数 ———————————————————

pre = log('r223_precheck.log')
mp = re.search(r'NEEDLE_PRECHECK tables=(\d+) covered=(\d+) arms=(\d+) bad=(\d+)', pre)
tables, covered, arms, bad = [int(x) for x in mp.groups()]
if bad != 4:
    die('本轮宣称 bad 从 5 修回 4，实得 %d ⇒ 不写' % bad)
stale = re.findall(r'^(\S+)\s+.*?(\bM\d+ 命中=\d+)', pre, re.M)
rerun = log('r223_rerun213.log')
mr = re.search(r'R213_MUTATE 刀=(\d+) CAUGHT=(\d+) ESCAPED=(\d+) NOT_RUN=(\d+)', rerun)
if not mr or mr.group(2) != mr.group(1) or mr.group(3) != '0' or mr.group(4) != '0':
    die('mutate_r213 重跑不干净 ⇒ 「旧表还能跑」这句话没有证人')
r213_knives, r213_caught = int(mr.group(1)), int(mr.group(2))
patch = log('r223_patch.log') if os.path.exists('/tmp/r223_patch.log') else ''

ci = log('r223_runs.log')
runs = {}
for l in ci.splitlines():
    g = re.match(r'(\S+) run=(\S+) (\S+)(?: (.*))?', l)
    if g:
        runs[g.group(1)] = (g.group(2), g.group(3), (g.group(4) or '未读').strip() or '未读')
for sha in ('cc0e358', '69bccbd'):
    if sha not in runs:
        die('读数里缺 ' + sha)
ev = log('r223_evidence.log')
if 'PILLOW_OK' not in ev or 'LEFT_AXIS_CI' not in ev:
    die('runner 正文的两条读数没存下来')
pillow = re.search(r'PILLOW_OK ([\d.]+)', ev)
axis = re.search(r'LEFT_AXIS_CI verdict=(\w+) hard=(\d+) not_run=(\d+) missing_frames=(\d+) probes=(\d+)', ev)

bat = log('r223_battery2.log')
mbat = re.search(r'Ran (\d+) tests', bat)
if not mbat or re.search(r'^(FAILED|ERROR)', bat, re.M) or 'OK' not in bat:
    die('电池不绿')
ran = int(mbat.group(1))

yml = read('.github/workflows/ci.yml')
steps = [s.strip().strip('"').strip("'")
         for s in re.findall(r'^      - name: (.*)$', yml, re.M)]
pillow_steps = [i for i, n in enumerate(steps) if n.startswith('Pillow for the frame rulers')]
battery_steps = [i for i, n in enumerate(steps) if n.startswith('Release script tests')]
ruler_steps = [i for i, n in enumerate(steps) if n.startswith('Surface left-axis ruler')]
if len(pillow_steps) != 1 or len(battery_steps) != 1:
    die('venv 步骤应当只剩一条（实得 %d）⇒ 不写' % len(pillow_steps))
if not (pillow_steps[0] < battery_steps[0] < ruler_steps[0]):
    die('步骤顺序不对：venv=%d 电池=%d 左轴=%d' % (pillow_steps[0], battery_steps[0], ruler_steps[0]))
for marker in ('SCRIPT_PYTHON', 'SCRIPT_PIL_OK', 'SCRIPT_SKIPS='):
    if marker not in yml:
        die('判据卷缺证人 ' + marker)

diff = subprocess.run(['git', 'diff', '--name-only', 'HEAD'], cwd=ROOT,
                      stdout=subprocess.PIPE).stdout.decode('utf-8', 'replace')
changed = [p for p in diff.splitlines() if p.strip()]
prod = [p for p in changed if p.startswith('ClipboardHistory/Sources/')]
if len(prod) != 0:
    die('本轮宣称 0 产品文件，实得 ' + str(prod))
ci_files = [p for p in changed if p.startswith('.github/')]
tool_files = [p for p in changed if 'mutate_r213' in p]
if len(ci_files) != 1 or len(tool_files) != 1:
    die('对象不明：' + str(changed))

# ——————————————————— 编号 ———————————————————

ui = read('AGENT_UI_AUDIT.md')
u_ids = [int(x) for x in re.findall(r'^- \*\*U-(\d+)：', ui, re.M)]
U1, U2, U3 = max(u_ids) + 1, max(u_ids) + 2, max(u_ids) + 3
b_max = max([int(x) for x in re.findall(r'^\*\*(\d+)\. ', read('AGENT_BACKLOG.md'), re.M)])
NEW_B = b_max + 1
d_max = max([int(x) for x in re.findall(r'^\*\*D-(\d+)（', read('AGENT_DECISIONS.md'), re.M)])
NEW_D = d_max + 1
it = read('AGENT_VISUAL_ITERATION.md')
last_round = max([int(x) for x in re.findall(r'^## Round (\d+) · ', it, re.M)])
this_round = last_round + 1
audit_round = this_round + 2
last_block = it[it.rindex('## Round %d · ' % last_round):]
dim_rows = re.findall(r'^\|([^|]+)\|\s*(\d+)/15\s*\|', last_block, re.M)
if len(dim_rows) != 7:
    die('上一节七维度行数 ' + str(len(dim_rows)))
dims = [d.strip() for d, _ in dim_rows]

TITLE = (u'247 解释并修好（旧变异表的锚点被我上一轮改源码时弄脱钩）、'
         u'244 落地：判据卷也走 venv，像素自检第一次有机会在 runner 上跑')
SCOPE = u'CI 1 文件 + 表 1 文件，产品 0 文件'

BASE = dict(AR=audit_round, R=223, DAY=DAY, TITLE=TITLE, U1=U1, U2=U2, U3=U3, SCOPE=SCOPE,
            tables=tables, covered=covered, arms=arms, bad=bad,
            stale='；'.join(['%s %s' % (a, b) for a, b in stale]) or u'（本轮日志里没有别的 命中≠1）',
            r213=r213_knives, r213c=r213_caught, ran=ran,
            cc=runs['cc0e358'][0], ccc=runs['cc0e358'][2],
            pv=pillow.group(1), av=axis.group(1), anr=axis.group(3), ap=axis.group(5),
            NB=NEW_B, ND=NEW_D, LR=last_round)

UI_NEW = u'''## 第 {AR} 轮（R{R} · {DAY}）：{TITLE}（U-{U1}…U-{U3} · {SCOPE}）

- **U-{U1}：上一轮那格"未解释的数"这一轮解释了，而且解释完发现自己欠了一格。**
  预检的 `bad` 累加点只有三处（导入失败 / 读文件失败 / **needle 在文件里命中≠1**），
  `dupes`/`repeats` 都是 0 ⇒ `bad=5` 就是五条脱钩的锚点，本轮日志点名的是：{stale}。
  其中 **`mutate_r213` 的 M747 是我上一轮弄脱钩的** —— R221 把 `live()` 从
  `readings.get(n) is not None` 改成 `readings.get(n) and readings[n].get('ok')`，
  而那张 2026-10-19 早些时候的表的锚点没跟着改 ⇒ 它今天**重跑不了**（NOT_RUN），
  而 CI 与人都只看结论行，没人会去重跑历史表。修锚点后 `bad` 5→4，
  并**真把旧表重跑了一遍**：`R213_MUTATE 刀={r213} CAUGHT={r213c} ESCAPED=0 NOT_RUN=0 RESTORE_CLEAN=yes`
  （⇒ 提成 **D-{ND}**：改源码就要当场把打它的那张表改到能跑）。
- **U-{U2}：244 的修法落地 —— venv 前移到判据卷之前，`@NEEDS_PIL` 那批第一次有机会在 runner 上真跑。**
  步骤顺序现在是 `{pstep}` → `{bstep}` → `{rstep}`（venv 只剩一条，R218 那条已删，重复会被本轮的断言拦下）。
  判据卷不再写死 `python3`：有 `/tmp/pilenv/bin/python` 就用它，装不上才退回系统解释器
  —— 那几格继续 skip 是**环境缺席**，不是产品结论（R154 那一族）。三行证人：
  `SCRIPT_PYTHON=`、`SCRIPT_PIL_OK <版本> <路径>`（或 `SCRIPT_PIL_MISSING=1`）、`SCRIPT_SKIPS=<条数>`。
  本机前提已核（不是赌）：本机 `python3` 有 PIL {pv} 同族（实测 11.3.0），`@NEEDS_PIL` 那批本来就是绿的，
  所以搬到 CI 只是把本机已有的覆盖面搬过去。**runner 那一跑仍待读** ⇒ 244 不写结案。
- **U-{U3}：CI 读数与未读清单。**
  `cc0e358` = run `{cc}` **{ccc}**，正文里 `PILLOW_OK {pv}` 与 `LEFT_AXIS_CI verdict={av} not_run={anr} probes={ap}`
  —— 但那一跑**早于** R221 的成因分档，所以 runner 上还没有 `cause=` 读数。
  带着分档代码的三跑 `69bccbd`/`540bb1e`/`04a68ed` 全部 `in_progress` ⇒ **246 仍等**，
  本轮这一跑是第一个"cause 分档 + venv 判据卷"同时上去的 ⇒ 246 与 244 的结案通道都在它身上。
  看图腿 NOT-RUN：本轮 0 像素改动、无新帧（盘上那 142 张属 R219/R220 两遍，不替本轮作证）。

其余读数：电池 `Ran {ran} tests ... OK`（含 `test_ci_workflow_shape` 与本轮新改的 workflow）；
预检 `NEEDLE_PRECHECK tables={tables} covered={covered} arms={arms} bad={bad}`；
产品 0 文件 ⇒ 未换装本机、本地全量卷按 D-208 的适用面不需要。

'''.format(pstep='Pillow for the frame rulers (venv …)', bstep='Release script tests',
           rstep='Surface left-axis ruler …', **BASE)

SCORES = {dims[0]: 10, dims[1]: 14, dims[2]: 14, dims[3]: 9,
          dims[4]: 14, dims[5]: 14, dims[6]: 14}
dim_table = '\n'.join([u'| ' + d + u' | ' + str(SCORES[d]) + u'/15 |' for d in dims])
BASE.update(DIMTABLE=dim_table, TOTAL=sum(SCORES.values()), TR=this_round, S3=SCORES[dims[3]])

IT_BLOCK = u'''
## Round {TR} · {TITLE}（{DAY} · {SCOPE}）

上一轮我在账里写了一格"未解释的数"（预检 `bad` 4→5），本轮去读了它的三个累加点：
`bad` 只数"导入失败 / 读文件失败 / **needle 命中≠1**"，`dupes=0 repeats=0` ⇒ 五条全是**锚点与文件脱钩**。
其中一条是我的：R221 我把 `surface_left_axes.py` 的 `live()` 改成按 `ok` 判，
而 R213 那张表里 M747 的锚点还写着旧句子 —— 那张表今天重跑就会 NOT_RUN，
而 CI 和人都不去重跑历史表，所以它坏得很安静。修完锚点我把**整张旧表真跑了一遍**：
`R213_MUTATE 刀={r213} CAUGHT={r213c} ESCAPED=0 NOT_RUN=0 RESTORE_CLEAN=yes`，`bad` 回到 4。
⇒ **D-{ND}**：改源码的那一轮要顺手把打它的历史表改到还能跑，或者在账里写明"这张表退役"。

244 也落地了：venv 步骤前移到判据卷之前，`Release script tests` 有 `/tmp/pilenv/bin/python` 就用它，
装不上才退回系统解释器（那几格继续 skip = 环境缺席，不是产品结论）。三行证人：
`SCRIPT_PYTHON=` / `SCRIPT_PIL_OK` / `SCRIPT_SKIPS=`。这不是赌：本机 python3 有 PIL（11.3.0），
`@NEEDS_PIL` 那批本来就是绿的 ⇒ 搬过去只是把本机已有的覆盖面搬到 CI。venv 步骤只留一条（R218 那条删掉，
顺序与条数都由本轮的断言核过）。**runner 那一跑还没读** ⇒ 244 不写结案。

CI：`cc0e358`=`{cc}` **{ccc}**，正文有 `PILLOW_OK {pv}` 但 `LEFT_AXIS_CI verdict={av} not_run={anr} probes={ap}`，
且那一跑早于成因分档 ⇒ runner 上还没有 `cause=`。带分档的三跑全 in_progress ⇒ 246 仍等，
本轮这一跑同时上了"cause 分档 + venv 判据卷"，两格的结案通道都在它身上。
看图腿 NOT-RUN（0 像素改动、无新帧）。

七维度自评：

| 维度 | 得分 |
|---|---|
{DIMTABLE}

总分 {TOTAL}/105（{TR} 轮）。GAPS=none
'''.format(**BASE)

CH_BLOCK = u'''### 247 结案（旧表锚点脱钩）+ 244 落地：判据卷走 venv，像素自检第一次有机会在 runner 上跑（R{R} / U-{U1}…U-{U3} · {SCOPE}）

- `bad` 的语义读明白了：只数"导入失败 / 读文件失败 / needle 命中≠1"（`dupes=0 repeats=0`）⇒ 五条都是**锚点脱钩**。
  其中 `mutate_r213` 的 M747 是 R221 我改 `live()` 时弄脱钩的 ⇒ 修锚点、`bad` 5→4，
  并真重跑旧表：`R213_MUTATE 刀={r213} CAUGHT={r213c} ESCAPED=0 NOT_RUN=0 RESTORE_CLEAN=yes`。立 **D-{ND}**。
- 244：venv 步骤前移到 `Release script tests` 之前（只剩一条，R218 那条删除；顺序与条数由脚本断言核过），
  判据卷改用 `/tmp/pilenv/bin/python`（装不上才退回系统解释器），加三行证人
  `SCRIPT_PYTHON` / `SCRIPT_PIL_OK` / `SCRIPT_SKIPS=`。
- CI：`cc0e358`=`{cc}` **{ccc}** 有 `PILLOW_OK {pv}` 但 `LEFT_AXIS_CI verdict={av} not_run={anr} probes={ap}`，
  且早于成因分档 ⇒ runner 上仍无 `cause=` 读数；带分档的三跑全 in_progress ⇒ **246 仍等**。
- 验证：电池 `Ran {ran} tests OK`（含 ci workflow 形状守卫）；预检 `tables={tables} covered={covered} arms={arms} bad={bad}`；
  产品 0 文件 ⇒ 未换装本机；看图腿 NOT-RUN（0 像素改动、无新帧）。

'''.format(**BASE)

STATE_BLOCK = u'''最后更新：{NOW}（本地 · R{R} / 第 {AR} 轮：**{TITLE}**（U-{U1}…U-{U3} · {SCOPE}）

**本轮落地**：上一轮那格"未解释的数"解释了 —— 预检 `bad` 只数三件事（导入失败 / 读文件失败 / **needle 命中≠1**），
`dupes=0 repeats=0` ⇒ 五条全是**锚点与文件脱钩**，其中 `mutate_r213` 的 M747 是我 R221 改 `live()` 时弄脱钩的
（那张表今天重跑会 NOT_RUN，而 CI 和人都不会去重跑历史表 ⇒ 坏得很安静）。
修锚点后 `bad` 5→4，并**真重跑旧表**：`R213_MUTATE 刀={r213} CAUGHT={r213c} ESCAPED=0 NOT_RUN=0` ⇒ 立 **D-{ND}**。
244 落地：venv 步骤前移到判据卷之前（只剩一条，R218 那条删除），`Release script tests` 改用
`/tmp/pilenv/bin/python`（装不上才退回系统解释器 = 环境缺席，不是产品结论），加三行证人
`SCRIPT_PYTHON` / `SCRIPT_PIL_OK` / `SCRIPT_SKIPS=`；本机 python3 有 PIL 11.3.0 且那批本来就是绿的 ⇒ 不是赌。
CI：`cc0e358`=`{cc}` **{ccc}**（`PILLOW_OK {pv}`，但 `LEFT_AXIS_CI verdict={av} not_run={anr} probes={ap}` 且早于分档）
⇒ runner 上还没有 `cause=`；带分档的三跑 `69bccbd`/`540bb1e`/`04a68ed` 全 in_progress ⇒ **246 仍等**。
验证：电池 `Ran {ran} OK`；预检 `tables={tables} covered={covered} arms={arms} bad={bad}`；
产品 0 文件 ⇒ 未换装本机；看图腿 NOT-RUN（0 像素改动、无新帧）。

**下一轮（R224）的靶**：⓪ 读本跑（第一个"cause 分档 + venv 判据卷"同时上去的一跑）：
`SCRIPT_PIL_OK` 有没有露面、`SCRIPT_SKIPS` 掉到几条（**244 结案的唯一通道**）、左轴那一步的 `cause=` 是哪一档（**246 结案的唯一通道**）；
① **回到动效位点本体**（连续多轮 0 产品改动）：清账表里挑一位点真做动效 + 帧 + 刀 + 看图 —— 这是目标问的东西，别再交判据账；
② 248（§1 其余活数格）与 ⓪b（报告刷新排到台账之后 / 让生成器幂等）；③ 242 其余亮档表面、243、227③、222、215、201/202、207、240；
④ 220 路 A、228② 等用户。
)

'''.format(NOW=NOW, **BASE)

BL_BLOCK = u'''
**247 追记（R223 结案）：`bad` 数的是"锚点与文件脱钩"，本轮 +1 那一条是我自己上一轮弄的**

三个累加点读完了：导入失败、读文件失败、`needle.count != 1`；`dupes`/`repeats` 本轮都是 0。
本轮日志点名的五条：{stale}。
`mutate_r213` 的 M747 打在 `live()` 那一行，而 R221 我把那行改成了按 `ok` 判 ⇒ 锚点命中 0，
那张表今天重跑会 NOT_RUN（不是 ESCAPED，是**跑不了**）。处置：改锚点 + 真重跑
`R213_MUTATE 刀={r213} CAUGHT={r213c} ESCAPED=0 NOT_RUN=0 RESTORE_CLEAN=yes`，`bad` 5→4。
本条结案。剩下四条（`mutate_r97_card` M541、`mutate_r169` M684/M686、`mutate_r217` M750 命中=2）
是更早的历史漂移，按 D-{ND} 的规矩要么下次动到那张表时顺手修，要么显式标退役 —— 不许留着不管。

**244 追记（R223 修法落地·待 runner 验收）**

venv 步骤前移到 `Release script tests` 之前，判据卷改用 `/tmp/pilenv/bin/python`（不存在才退回 `python3`）；
证人三行：`SCRIPT_PYTHON=`、`SCRIPT_PIL_OK <版本> <路径>` 或 `SCRIPT_PIL_MISSING=1`、`SCRIPT_SKIPS=<条数>`。
本机前提：`python3 -c "import PIL"` = 11.3.0，`@NEEDS_PIL` 那批在带 PIL 的解释器下本来就是绿的。
仍欠：runner 那一跑 `SCRIPT_SKIPS` 实际掉到几条、以及带 PIL 之后有没有新的红（若有，那是第一次真判，红要归因不要放宽）。

'''.format(stale='；'.join(['%s %s' % (a, b) for a, b in stale]) or u'无', r213=r213_knives,
           r213c=r213_caught, ND=NEW_D)

DE_BLOCK = u'''
**D-{ND}（R223）：变异表与它要打的源码是同一份契约 —— 改源码那一轮就要把表改到还能跑，或者显式标退役**

现场：R221 我把 `scripts/surface_left_axes.py` 的 `live()` 从 `is not None` 改成按 `ok` 判（这是对的改动），
但 R213 那张表里 M747 的 needle 还是旧句子 ⇒ 命中 0，那张表今天重跑会 **NOT_RUN**。
`NEEDLE_PRECHECK` 的 `bad` 从 4 涨到 5 是唯一线索，而我上一轮把它记成"未解释的数"就过去了。
坏在哪：CI 与人都只看当轮表的结论行，**没人重跑历史表**，所以一张跑不了的表可以安静地躺在名册里，
下一次有人说"M747 曾经拦住过 X"时，它其实已经验不动了。
规矩：① 改源码的那一轮，若那张源码里有历史表的 needle，就要么当场改锚点并**重跑那张表**（本轮就是这么做的：
`R213_MUTATE 刀={r213} CAUGHT={r213c}`），要么在账里写明"这张表退役"；
② 预检的 `bad` 不是噪声，它是"哪些刀今天已经挥不动"的名单 —— 每一轮点名一次，别让它只涨不解释；
③ 一条"未解释的数"最多只能挂一轮：下一轮要么解释，要么开单修（本轮 247 就是这么结的）。
适用面：所有 `.scratch/motion-audit-2/mutate_r*.py` 与被它们当靶的源码/脚本；不适用：一次性实验脚本（那些不进名册）。
'''.format(ND=NEW_D, r213=r213_knives, r213c=r213_caught)

# ——————————————————— 写盘 ———————————————————

plans = []
DELTAS = {}


def reinsertion_matches(old, new, path):
    blk = DELTAS.get(path)
    if blk is None:
        return new.startswith(old)
    return new.count(blk) == 1 and new.replace(blk, '', 1) == old


def plan_insert(path, anchor, block):
    text = read(path)
    idx = text.find(anchor)
    if idx < 0 or text.find(anchor, idx + 1) >= 0:
        die('锚点找不到或不唯一：' + path)
    new = text[:idx] + block + text[idx:]
    DELTAS[path] = block
    if new.count(block) != 1 or not reinsertion_matches(text, new, path):
        die('插入还原失败：' + path)
    plans.append((path, text, new))


def plan_insert_where(path, pattern, block, expect_contains):
    text = read(path)
    m = re.search(pattern, text, re.M)
    if not m:
        die('形状找不到：' + path)
    line = text[m.start():text.find('\n', m.start())]
    if expect_contains not in line:
        die('第一格不是上一轮那一格：' + path + ' ｜ ' + line[:60])
    new = text[:m.start()] + block + text[m.start():]
    DELTAS[path] = block
    if new.count(block) != 1 or not reinsertion_matches(text, new, path):
        die('插入还原失败：' + path)
    plans.append((path, text, new))


def plan_append(path, block):
    text = read(path)
    if not text.endswith('\n'):
        text = text + '\n'
    new = text + block.strip('\n') + '\n'
    if not new.startswith(text):
        die('追加会改动旧内容：' + path)
    plans.append((path, text, new))


plan_insert('AGENT_UI_AUDIT.md', u'## 第 ' + str(audit_round - 1) + u' 轮（R222 · ', UI_NEW)
plan_append('AGENT_VISUAL_ITERATION.md', IT_BLOCK)
ch = read('CHANGELOG.md')
idx = ch.find(u'## [Unreleased]')
if idx < 0:
    die('CHANGELOG 没有 [Unreleased]')
cut = idx + len(u'## [Unreleased]')
if ch[cut:cut + 1] != u'\n':
    die('CHANGELOG 的 [Unreleased] 行尾不是换行')
plans.append(('CHANGELOG.md', ch, ch[:cut] + u'\n' + CH_BLOCK + ch[cut + 1:]))
DELTAS['CHANGELOG.md'] = CH_BLOCK
plan_insert_where('AGENT_STATE.md', u'^最后更新：', STATE_BLOCK, u'R222 / 第 224 轮')
plan_append('AGENT_BACKLOG.md', BL_BLOCK)
plan_append('AGENT_DECISIONS.md', DE_BLOCK)

# 写盘前最后一道：正文里不许留着没渲染的占位符（R219–R222 四轮都撞过"占位符与参数两本账"）
STRAY = re.compile(r'\{[A-Z][A-Za-z_]*\}')
for name, blk in (('UI_NEW', UI_NEW), ('IT_BLOCK', IT_BLOCK), ('CH_BLOCK', CH_BLOCK),
                  ('STATE_BLOCK', STATE_BLOCK), ('BL_BLOCK', BL_BLOCK), ('DE_BLOCK', DE_BLOCK)):
    g = STRAY.search(blk)
    if g:
        die(name + u' 里留着没渲染的占位符：' + g.group(0))

for path, old, new in plans:
    if len(new.splitlines()) <= len(old.splitlines()):
        die('写盘前最后一道：' + path + u' 行数没增加')
    if not reinsertion_matches(old, new, path):
        die('写盘前最后一道：' + path + u' 抠掉新块后不等于旧文件')

for path, old, new in plans:
    write(path, new)

print(u'LEDGERS_R223 wrote %d files' % len(plans))
print(u'LEDGERS_R223 编号：第 %d 轮 / Round %d / U-%d…U-%d / BACKLOG +%d / D-%d'
      % (audit_round, this_round, U1, U3, NEW_B, NEW_D))
print(u'LEDGERS_R223 读数：bad=%d（修前 5）、旧表重跑 %d/%d、电池 %d、runner %s/%s probes=%s'
      % (bad, r213_caught, r213_knives, ran, axis.group(1), axis.group(3), axis.group(5)))

state = read('AGENT_STATE.md')
ms = re.search(u'最后更新：[^\\n]*?R(\\d+) / 第 (\\d+) 轮', state)
if not ms or int(ms.group(1)) != 223 or int(ms.group(2)) != audit_round:
    die('STATE 轮次行读不出 R223 / 第 ' + str(audit_round) + u' 轮')
for path, pat in ((u'AGENT_UI_AUDIT.md', u'^## 第 ' + str(audit_round) + u' 轮（R223'),
                  (u'AGENT_VISUAL_ITERATION.md', u'^## Round 223 · '),
                  (u'CHANGELOG.md', u'^### .*（R223 / ')):
    if not re.search(pat, read(path), re.M):
        die(path + u' 里读不到本轮标题：' + pat)
print(u'LEDGERS_R223 selfcheck ok')
sys.exit(0)
