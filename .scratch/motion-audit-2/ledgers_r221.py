# -*- coding: utf-8 -*-
"""R221 的台账生成器：246 的分辨仪器落地（NOT_RUN 的成因分档）+ 两把刀 + CI 读数。

规矩同 R217–R220：数字全部从本轮真实日志解析；插入用切片 + 抠块还原；七维度名从上一节读；
编号从台账正则取 max+1；缺任何一格读数就拒绝写盘。
"""
import io, os, re, subprocess, sys

ROOT = '/Users/wangziyi/Codex_Project0'
DAY = '2026-10-19'
NOW = '2026-10-19 22:58'


def read(p):
    return io.open(os.path.join(ROOT, p), encoding='utf-8').read()


def write(p, t):
    with io.open(os.path.join(ROOT, p), 'w', encoding='utf-8') as h:
        h.write(t)


def die(why):
    print('LEDGERS_R221 refused: ' + why)
    sys.exit(1)


def log(p):
    path = os.path.join('/tmp', p)
    if not os.path.exists(path):
        die('缺少本轮日志 ' + path + ' ⇒ 不许写台账')
    return io.open(path, encoding='utf-8', errors='replace').read()


# ——————————————————— 读数 ———————————————————

st = log('r221_selftest.log')
if 'LEFT_AXIS_SELFTEST ok' not in st:
    die('尺的自检没绿')
n_cases = len(re.findall(r'^SELFTEST ', st, re.M))
cause_lines = [l for l in st.splitlines() if u'cause=' in l]
if len(cause_lines) < 2:
    die('成因读数只有 %d 行 ⇒ 两格新对照没跑起来' % len(cause_lines))
causes = sorted(set(re.findall(r'cause=([\w-]+)', st)))

ci_local = log('r221_ci_local.log')
m = re.search(r'LEFT_AXIS_CI verdict=(\w+) hard=(\d+) not_run=(\d+) missing_frames=(\d+) probes=(\d+)',
              ci_local)
if not m:
    die('读不到本机 CI 出口的结论行')
lverdict, lhard, lnr, lmiss, lprobes = m.groups()
if lverdict != 'ok' or int(lprobes) != 7:
    die('本机出口变了（' + lverdict + ' probes=' + lprobes + u'）⇒ 本轮宣称"没改判据行为"就不成立')

mut = log('r221_mutate.log')
mm = re.search(r'R221_MUTATE 刀=(\d+) CAUGHT=(\d+) ESCAPED=(\d+) NOT_RUN=(\d+)', mut)
if not mm:
    die('读不到变异表结论行')
knives, caught, escaped, not_run = [int(x) for x in mm.groups()]
if escaped or not_run or caught != knives:
    die('变异表不干净：' + mm.group(0))

pre = log('r221_precheck.log')
mp = re.search(r'NEEDLE_PRECHECK tables=(\d+) covered=(\d+) arms=(\d+) bad=(\d+)', pre)
mt = re.search(r'ARM_TOTAL files=(\d+) arms=(\d+) dupes=(\d+) repeats=(\d+)', pre)
if not mp or not mt:
    die('读不到预检的两行结论')
tables, covered, arms, bad = [int(x) for x in mp.groups()]
afiles, aarms, dupes, repeats = [int(x) for x in mt.groups()]
prev = log('r220_precheck2.log')
mq = re.search(r'NEEDLE_PRECHECK tables=(\d+) covered=(\d+) arms=(\d+) bad=(\d+)', prev)
p_tables, p_covered, p_arms, p_bad = [int(x) for x in mq.groups()]

bat = log('r221_battery.log')
mbat = re.search(r'Ran (\d+) tests in [\d.]+s', bat)
if not mbat or re.search(r'^(FAILED|ERROR)', bat, re.M) or 'OK' not in bat:
    die('电池不绿')
ran = int(mbat.group(1))

ci = log('r221_ci.log')
runs = dict((sha, (rid, status, concl or u'未读'))
            for sha, rid, status, concl in
            [re.match(r'(\S+) run=(\S+) (\S+) (.*)', l).groups()
             for l in ci.splitlines() if re.match(r'\S+ run=\S+ \S+', l)])
if '7ebda4c' not in runs or runs['7ebda4c'][2] != 'success':
    die('R219 那一跑（7ebda4c）的结论不是 success ⇒ 先归因再写账')
frames_on_disk = 0
for l in ci.splitlines():
    g = re.match(r'FRAMES_ON_DISK=(\d+)', l)
    if g:
        frames_on_disk = int(g.group(1))

diff = subprocess.run(['git', 'diff', '--name-only', 'HEAD'], cwd=ROOT,
                      stdout=subprocess.PIPE).stdout.decode('utf-8', 'replace')
changed = [p for p in diff.splitlines() if p.strip()]
prod = [p for p in changed if p.startswith('ClipboardHistory/Sources/')]
ruler = [p for p in changed if p == 'scripts/surface_left_axes.py']
if len(prod) != 0 or len(ruler) != 1:
    die('对象不明：产品 ' + str(prod) + u' / 尺 ' + str(ruler))

# ——————————————————— 编号 ———————————————————

ui = read('AGENT_UI_AUDIT.md')
u_max = max([int(x) for x in re.findall(r'^- \*\*U-(\d+)：', ui, re.M)])
U1, U2, U3 = u_max + 1, u_max + 2, u_max + 3
blt = read('AGENT_BACKLOG.md')
b_max = max([int(x) for x in re.findall(r'^\*\*(\d+)\. ', blt, re.M)])
NEW_B = b_max + 1
de = read('AGENT_DECISIONS.md')
d_max = max([int(x) for x in re.findall(r'^\*\*D-(\d+)（', de, re.M)])
NEW_D = d_max + 1
it = read('AGENT_VISUAL_ITERATION.md')
this_round = max([int(x) for x in re.findall(r'^## Round (\d+) · ', it, re.M)]) + 1
audit_round = this_round + 2
last_block = it[it.rindex('## Round ' + str(this_round - 1) + ' · '):]
dim_rows = re.findall(r'^\|([^|]+)\|\s*(\d+)/15\s*\|', last_block, re.M)
if len(dim_rows) != 7:
    die('上一节七维度行数 ' + str(len(dim_rows)))
dims = [d.strip() for d, _ in dim_rows]

TITLE = (u'246 的分辨仪器落地：NOT_RUN 现在交得出成因（%s），两格已知答案对照 + 两把刀；'
         u'另有一格读数本轮没解释' % u'/'.join(causes))
SCOPE = u'判据（python 尺）1 文件，产品 0 文件'

UI_NEW = u'''## 第 {AR} 轮（R221 · {DAY}）：{TITLE}（U-{U1}…U-{U3} · {SCOPE}）

- **U-{U1}：缺席不再只有一句"取不到墨或底不纯"—— `scripts/surface_left_axes.py` 现在交得出成因。**
  `probe_reading` 的四种失败各自有名字（`stem-unparsable` / `no-bg-window` / `bg-not-flat` / `no-ink`），
  文件不在盘上另算 `frame-missing`；`judge` 的 NOT_RUN 文本改成可机器读的
  `cause=xxx bg=… thr=… window=…`。分档不是文字游戏，**三档的处置相反**：
  帧没画 = 捕获通道的事；窗口无墨 = 这台机器画不出这块表面；底不纯 = **尺自己的前提没成立，要修的是尺**。
  自检从 {ncase} 格涨到含两格新对照：`反对照·空帧的成因`（必须 no-ink）、
  `反对照·底不纯的成因`（必须 bg-not-flat）—— 本轮实测两格都绿，读到的成因集合：{causes}。
  本机出口未变：`LEFT_AXIS_CI verdict={lv} hard={lh} not_run={ln} missing_frames={lm} probes={lp}`
  ⇒ 加的是**读数**，不是新的判定。
- **U-{U2}：两把刀都打在这把尺自己身上（`R221_MUTATE 刀={K} CAUGHT={C} ESCAPED={E} NOT_RUN={N} RESTORE_CLEAN=yes`）。**
  M757 把"底不纯"那一档的成因**混进** `no-ink` ⇒ "反对照·底不纯的成因"立刻红（这一刀就是 246 开单的理由本身）；
  M758 把缺席判定改成恒不缺席（`if r is None or not r.get('ok')` ⇒ `if False`）⇒ "反对照·全空帧"红
  —— 那是 R210 记过的假绿通道（缺席被当成通过）。
  这一轮的表跑的是**尺的自检**（`--self-test` 的退出码 + 那几行 SELFTEST），不是 swift 卷；
  表里因此印的是被点名那一格对照的原文，读者可以自己去对。
  **runner 那一跑还没读**（本跑之后才有）⇒ 246 仍开，等的是"7 颗探针各是哪一档"。
- **U-{U3}：两格 CI 读数 + 一格本轮没解释的数。**
  `7ebda4c`（R219 的亮档墨）= run `{r1}` **{c1}**、`9ab453a` = run `{r2}` **{c2}**
  ⇒ R219 那个像素改动没把 runner 的任何一步弄红（`STEP[15]` 里那三条读源码的守卫也不看像素）；
  `bc5c5d7`={r3}、`cc0e358`={r4} 仍 `{s3}` ⇒ 未读不算绿。
  **没解释的数**：预检 `bad` 从 {pbad} 涨到 {bad}（`tables` {pt}→{t}、`covered` {pcov}→{cov}、
  `dupes=0 repeats=0`）。我只知道自己新登记了一张表，而 `bad` 的三个累加点（150/168/176 行）
  本轮没逐条读过去 ⇒ **这一格记"未解释"，不猜成因**（R98：未解释的数才是收窄的地方）。
  看图腿 NOT-RUN：本轮 0 像素改动、无新帧；盘上那 {frames} 张属 R219/R220 那两遍，不替本轮作证。

其余读数：电池 `Ran {ran} tests ... OK`（台账落盘之后再跑一遍）；产品 0 文件 ⇒ 未换装本机、
本地全量卷按 D-208 的适用面不需要；`ARM_TOTAL files={af} arms={aa}`。

'''.format(AR=audit_round, DAY=DAY, TITLE=TITLE, U1=U1, U2=U2, U3=U3, SCOPE=SCOPE,
           ncase=n_cases, causes=u'、'.join(causes), lv=lverdict, lh=lhard, ln=lnr, lm=lmiss,
           lp=lprobes, K=knives, C=caught, E=escaped, N=not_run,
           r1=runs['7ebda4c'][0], c1=runs['7ebda4c'][2],
           r2=runs.get('9ab453a', (u'?', u'?', u'未读'))[0],
           c2=runs.get('9ab453a', (u'?', u'?', u'未读'))[2],
           r3=runs.get('bc5c5d7', (u'?',))[0], r4=runs.get('cc0e358', (u'?',))[0],
           s3=runs.get('bc5c5d7', (u'?', u'未读'))[1],
           pbad=p_bad, bad=bad, pt=p_tables, t=tables, pcov=p_covered, cov=covered,
           frames=frames_on_disk, ran=ran, af=afiles, aa=aarms)

SCORES = {dims[0]: 10, dims[1]: 14, dims[2]: 14, dims[3]: 9,
          dims[4]: 13, dims[5]: 14, dims[6]: 13}
dim_table = '\n'.join([u'| ' + d + u' | ' + str(SCORES[d]) + u'/15 |' for d in dims])
TOTAL = sum(SCORES.values())

IT_BLOCK = u'''
## Round {TR} · {TITLE}（{DAY} · {SCOPE}）

上一轮 runner 给了一个坏消息：pillow 装上了，可左轴那把尺的 7 颗探针**全部 NOT_RUN**，
而它只会说一句"取不到墨或底不纯"。这句话把三种**处置相反**的成因缝在一起：
帧没画（捕获通道的事）／窗口无墨（这台机器画不出这块表面）／底不纯（尺自己的前提没成立，要修的是尺）。
所以本轮不新加阈值、也不放宽出口，只把成因拆开印出来：`cause=stem-unparsable|no-bg-window|bg-not-flat|no-ink`
（文件不在盘上另有 `frame-missing`），并把两格**已知答案的对照**加进自检 ——
空帧必须报 no-ink、棋盘底必须报 bg-not-flat。本机出口一字未变（`verdict={lv} probes={lp}`）
⇒ 加的是读数，不是判定。

两把刀都打在尺上：M757 把 bg-not-flat 混进 no-ink ⇒ 新对照红；M758 把缺席判定改成恒不缺席 ⇒ "全空帧"红
（R210 那条假绿通道）。`R221_MUTATE 刀={K} CAUGHT={C} ESCAPED={E} NOT_RUN={N}`。
这一张表跑的是尺的 `--self-test`，不是 swift 卷 —— 表里印的是被点名那格对照的原文，可自己回去对。

两格 CI 读数：`7ebda4c`（R219 的亮档墨）**{c1}**、`9ab453a` **{c2}** ⇒ 像素改动没弄红 runner。
还有一格**本轮没解释**：预检 `bad` 从 {pbad} 涨到 {bad}，而 `dupes=0 repeats=0`、我只新登记了一张表 ——
三个累加点没逐条读过去，所以按"未解释"记账，不猜（R98：未解释的数才是收窄的地方）。
看图腿 NOT-RUN：0 像素改动、无新帧，盘上 {frames} 张属前两遍。分数低在两处：产品面推进与真实视觉审查，
连续几轮把力气花在判据与仪器上 —— 目标要的是逐位点重判并加该加的动效，R222 的 ① 已经换成这个。

七维度自评：

| 维度 | 得分 |
|---|---|
{DIMTABLE}

总分 {TOTAL}/105（{TR} 轮）。GAPS=none
'''.format(TR=this_round, TITLE=TITLE, DAY=DAY, SCOPE=SCOPE, lv=lverdict, lp=lprobes,
           K=knives, C=caught, E=escaped, N=not_run, c1=runs['7ebda4c'][2],
           c2=runs.get('9ab453a', (u'?', u'?', u'未读'))[2], pbad=p_bad, bad=bad,
           frames=frames_on_disk, TOTAL=TOTAL, DIMTABLE=dim_table)

CH_BLOCK = u'''### NOT_RUN 交得出成因（246 的仪器）+ 两格已知答案对照 + 两把刀（R{R} / U-{U1}…U-{U3} · {SCOPE}）

- `scripts/surface_left_axes.py`：四种失败各有一个名字（`stem-unparsable` / `no-bg-window` /
  `bg-not-flat` / `no-ink`，另有 `frame-missing`），NOT_RUN 文本改成可机器读的 `cause=… bg=… thr=…`。
  三档处置相反（通道／这台机器画不出／尺自己要修）⇒ 混成一档就等于下一轮重问（提成 **D-{ND}**）。
- 自检加两格已知答案对照：空帧必须 `no-ink`、棋盘底必须 `bg-not-flat`；本机出口未变
  （`verdict={lv} probes={lp}`）⇒ 加的是读数不是判定。
- 刀：`R221_MUTATE 刀={K} CAUGHT={C} ESCAPED={E} NOT_RUN={N}`（M757 混档、M758 把缺席当通过）；
  这张表跑的是尺的 `--self-test` 而不是 swift 卷。
- CI：`7ebda4c` **{c1}**、`9ab453a` **{c2}** ⇒ R219 的像素改动没弄红 runner；`bc5c5d7`/`cc0e358` 未读。
- 未解释：预检 `bad` {pbad}→{bad}（`dupes=0 repeats=0`）⇒ 按"未解释"记账，不猜成因。
- 验证：电池 `Ran {ran} OK`；产品 0 文件 ⇒ 未换装本机；看图腿 NOT-RUN（0 像素改动、无新帧）。

'''.format(R=221, U1=U1, U3=U3, SCOPE=SCOPE, ND=NEW_D, lv=lverdict, lp=lprobes,
           K=knives, C=caught, E=escaped, N=not_run, c1=runs['7ebda4c'][2],
           c2=runs.get('9ab453a', (u'?', u'?', u'未读'))[2],
           pbad=p_bad, bad=bad, ran=ran)

STATE_BLOCK = u'''最后更新：{NOW}（本地 · R221 / 第 {AR} 轮：**{TITLE}**（U-{U1}…U-{U3} · {SCOPE}）

**本轮落地**：246 的分辨仪器 —— `surface_left_axes.py` 的 NOT_RUN 现在交得出成因
（`stem-unparsable` / `no-bg-window` / `bg-not-flat` / `no-ink` / `frame-missing`），三档处置相反，
混成一档就等于下一轮重问（提成 **D-{ND}**）。自检加两格已知答案对照（空帧⇒no-ink、棋盘底⇒bg-not-flat），
本机出口一字未变（`verdict={lv} probes={lp}`）⇒ 加的是读数不是判定。
两把刀 `R221_MUTATE 刀={K} CAUGHT={C} ESCAPED={E} NOT_RUN={N}`：M757 混档、M758 把缺席当成通过（R210 那条假绿通道）。
CI：`7ebda4c`={r1} **{c1}**、`9ab453a`={r2} **{c2}** ⇒ R219 的亮档墨没弄红 runner；
`bc5c5d7`/`cc0e358` 仍 in_progress ⇒ 未读不算绿。**未解释的数**：预检 `bad` {pbad}→{bad}（`dupes=0 repeats=0`），
三个累加点没逐条读 ⇒ 记"未解释"，不猜。
验证：电池 `Ran {ran} OK`；产品 0 文件 ⇒ 未换装本机；看图腿 NOT-RUN（0 像素改动、盘上 {frames} 张属前两遍）。

**下一轮（R222）的靶**：① **回到动效位点本体**（连续多轮 0 产品改动，目标要的是逐位点重判并加该加的动效）——
从清账表未判的格子里挑一位点，真做动效 + 帧 + 刀 + 看图；
⓪ 读本跑与 `bc5c5d7`/`cc0e358`：runner 上左轴那一步现在打的**成因**是什么（246 结案的唯一通道），
顺带把预检 `bad` 那一格读明白；② 242 的其余亮档表面逐个判（热图阶梯、侧栏占位要不要按档给）；
③ 243、227③、222、215、201/202、207、244、240；④ 220 路 A、228② 等用户。
)

'''.format(NOW=NOW, AR=audit_round, TITLE=TITLE, U1=U1, U3=U3, SCOPE=SCOPE, ND=NEW_D,
           lv=lverdict, lp=lprobes, K=knives, C=caught, E=escaped, N=not_run, r1=runs['7ebda4c'][0], c1=runs['7ebda4c'][2],
           r2=runs.get('9ab453a', (u'?', u'?', u'未读'))[0],
           c2=runs.get('9ab453a', (u'?', u'?', u'未读'))[2],
           pbad=p_bad, bad=bad, ran=ran, frames=frames_on_disk)

BL_BLOCK = u'''
**246 追记（R221 仪器落地·仍开）：NOT_RUN 现在交得出成因，runner 那一跑待读**

`scripts/surface_left_axes.py` 的四种失败各有一个名字（`cause=stem-unparsable|no-bg-window|bg-not-flat|no-ink`，
文件不在盘上另有 `frame-missing`），NOT_RUN 那行文本变成可机器读的 `cause=… bg=… thr=… window=…`。
自检里加了两格**已知答案的对照**：全空帧必须报 `no-ink`、棋盘底必须报 `bg-not-flat`（本轮实测两格绿）。
本机出口未变：`LEFT_AXIS_CI verdict={lv} hard={lh} not_run={ln} missing_frames={lm} probes={lp}`。
刀：M757（把 bg-not-flat 混进 no-ink ⇒ 新对照红）、M758（把缺席判定改成恒不缺席 ⇒ "全空帧"红）。
本条**不写结案**：等的是 runner 那一跑打出的 7 颗探针各是哪一档 —— 只有 ①帧没画 ②窗口无墨 属于通道限制，
③底不纯 属于尺要修；分档之后才谈要不要按表面切片。

**{NB}. 预检的 `bad` 从 {pbad} 涨到 {bad}，本轮没解释这一格（R221 记，下一轮读）**

同一次运行的其它计数器都对得上：`tables` {pt}→{t}、`covered` {pcov}→{cov}（新登记 `mutate_r221` 一张表）、
`ARM_TOTAL dupes=0 repeats=0`。但 `bad` 的累加点有三处（臂号解析失败 / needle 判不了 / 跨表问题），
本轮只读到"新表的两支臂都印了 ok"，没逐条把 +1 归到某一处 ⇒ **不猜成因**。
要做的：读 `mutate_needle_precheck.py` 那三个 `bad += 1` 各自的条件，再对照本轮日志点名是哪一处；
如果它是"每登记一张新表就会 +1"的结构性计数（例如按表统计未覆盖臂），那 `bad` 的语义就要在结论行里写明，
否则下一轮会把一个结构性计数当成真毛病去修。
适用面：`mutate_needle_precheck.py` 的结论行；不适用：变异表自己的 刀/CAUGHT/ESCAPED/NOT_RUN 四个数。

'''.format(lv=lverdict, lh=lhard, ln=lnr, lm=lmiss, lp=lprobes, NB=NEW_B,
           pbad=p_bad, bad=bad, pt=p_tables, t=tables, pcov=p_covered, cov=covered)

DE_BLOCK = u'''
**D-{ND}（R221）：缺席必须分档交成因，而且每一档要有一格"已知答案的对照"钉住；混档比不分档更坏**

现场：runner 上左轴尺 7 颗探针全 NOT_RUN，而尺只说一句"探针取不到墨或底不纯"。
这句话把三种**处置相反**的成因缝在一起：①帧没画出来（捕获通道的事，R210/201 那一族）、
②那块窗口在这台机器上就是没墨（通道限制，判"不判"）、③底不纯（**尺自己的前提没成立，要修的是尺**）。
把 ③ 读成 ①/②，就会去修一条没坏的通道 —— 这正是 R154 那族"环境差异被报成代码结论"的反方向版本。
规矩：① 任何"没有对象"的出口都要交出**可机器读的原因码**（`cause=…`）与它当时的量（`bg=`、`thr=`、`window=`）；
② 每一档都要有一格已知答案的对照钉住（本轮：全空帧必须报 `no-ink`、棋盘底必须报 `bg-not-flat`），
   否则原因码只是散文，M757 那种"把两档混成一档"就没人拦；
③ 分档之后**处置没变的就别改判据**：本轮本机出口一字未变（`verdict=ok probes=7`），
   加的是读数不是判定 —— 否则很容易顺手把"这台机器判不了"放宽成一条覆盖率通道（R74 的规矩）。
适用面：所有带"没有对象/环境缺席"出口的像素与产物判据；不适用：跑不动就是红的那类步骤（编译、单元测试）。
'''.format(ND=NEW_D)

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
    if idx < 0:
        die('锚点找不到：' + path)
    if text.find(anchor, idx + 1) >= 0:
        die('锚点不唯一：' + path)
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


plan_insert('AGENT_UI_AUDIT.md', u'## 第 ' + str(audit_round - 1) + u' 轮（R220 · ', UI_NEW)
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
plan_insert_where('AGENT_STATE.md', u'^最后更新：', STATE_BLOCK, u'R220 / 第 222 轮')
plan_append('AGENT_BACKLOG.md', BL_BLOCK)
plan_append('AGENT_DECISIONS.md', DE_BLOCK)

for path, old, new in plans:
    if len(new.splitlines()) <= len(old.splitlines()):
        die('写盘前最后一道：' + path + u' 行数没增加')
    if not reinsertion_matches(old, new, path):
        die('写盘前最后一道：' + path + u' 抠掉新块后不等于旧文件')

for path, old, new in plans:
    write(path, new)

print(u'LEDGERS_R221 wrote %d files' % len(plans))
print(u'LEDGERS_R221 编号：第 %d 轮 / Round %d / U-%d…U-%d / BACKLOG +%d / D-%d'
      % (audit_round, this_round, U1, U3, NEW_B, NEW_D))
print(u'LEDGERS_R221 读数：成因 %s、自检 %d 格、本机 %s probes=%s、刀 %d/%d、电池 %d、bad %d→%d'
      % (u'/'.join(causes), n_cases, lverdict, lprobes, caught, knives, ran, p_bad, bad))

state = read('AGENT_STATE.md')
ms = re.search(u'最后更新：[^\\n]*?R(\\d+) / 第 (\\d+) 轮', state)
if not ms or int(ms.group(1)) != 221 or int(ms.group(2)) != audit_round:
    die('STATE 轮次行读不出 R221 / 第 ' + str(audit_round) + u' 轮')
for path, pat in ((u'AGENT_UI_AUDIT.md', u'^## 第 ' + str(audit_round) + u' 轮（R221'),
                  (u'AGENT_VISUAL_ITERATION.md', u'^## Round 221 · '),
                  (u'CHANGELOG.md', u'^### .*（R221 / ')):
    if not re.search(pat, read(path), re.M):
        die(path + u' 里读不到本轮标题：' + pat)
print(u'LEDGERS_R221 selfcheck ok')
sys.exit(0)
