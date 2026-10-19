# -*- coding: utf-8 -*-
"""R222 的台账生成器：最终报告的活数格对账 + 新守卫 + 两把刀（其中一把第一版被表的解析读错）。

规矩同 R217–R221：数字全部从本轮真实日志解析；插入用切片 + 抠块还原；七维度名从上一节读；
编号从台账正则取 max+1；缺任何一格读数就拒绝写盘。
"""
import io, os, re, subprocess, sys

ROOT = '/Users/wangziyi/Codex_Project0'
DAY = '2026-10-19'
NOW = '2026-10-19 23:10'


def read(p):
    return io.open(os.path.join(ROOT, p), encoding='utf-8').read()


def write(p, t):
    with io.open(os.path.join(ROOT, p), 'w', encoding='utf-8') as h:
        h.write(t)


def die(why):
    print('LEDGERS_R222 refused: ' + why)
    sys.exit(1)


def log(p):
    path = os.path.join('/tmp', p)
    if not os.path.exists(path):
        die('缺少本轮日志 ' + path + ' ⇒ 不许写台账')
    return io.open(path, encoding='utf-8', errors='replace').read()


# ——————————————————— 读数 ———————————————————

gen = log('final_report_r222.stdout') if os.path.exists('/tmp/final_report_r222.stdout') else ''
rep = read('AGENT_FINAL_REPORT.md')
mt = re.search(r'R9–R(\d+)，(\d+) 轮自评', rep.splitlines()[0])
if not mt:
    die('报告标题里没有"R9–R<NNN>，<N> 轮自评"那一格 ⇒ 本轮的刷新没落上')
title_round, phase2_n = int(mt.group(1)), int(mt.group(2))
mu = re.search(r'U-31 … U-(\d+)（(\d+) 条定义行', rep)
if not mu:
    die('§1 的 U 那一格没换成活账')
u_cell, u_rows_cell = int(mu.group(1)), int(mu.group(2))
section12 = len(re.findall(r'^## 12\. R137', rep, re.M))
if section12 != 1:
    die('§12 那一节没进去（命中 %d）' % section12)

it = read('AGENT_VISUAL_ITERATION.md')
last_round = max([int(x) for x in re.findall(r'^## Round (\d+) · ', it, re.M)])
ui = read('AGENT_UI_AUDIT.md')
u_max = max([int(x) for x in re.findall(r'^- \*\*U-(\d+)：', ui, re.M)])
if title_round != last_round or u_cell != u_max:
    die('报告格子与活账不一致（%s vs %s ｜ %s vs %s）⇒ 别写' % (title_round, last_round, u_cell, u_max))

bat_before = log('r222_battery.log')
before_fail = re.search(r'FAIL: (test_\w+) \(([\w.]+)\)', bat_before)
if not before_fail or 'test_final_report_headline' not in before_fail.group(0):
    die('改前的红没有证人（要找新守卫那条 FAIL 行）')
ran_before = int(re.search(r'Ran (\d+) tests', bat_before).group(1))
bat_after = log('r222_battery4.log')
ma = re.search(r'Ran (\d+) tests', bat_after)
if not ma or 'OK' not in bat_after:
    die('改后的电池不绿 ⇒ 不写')
ran_after = int(ma.group(1))
# 三个数不是两个：上一轮（没有这条守卫）400、本轮改报告**之前**（有守卫、报告还旧）403 且红、
# 改完之后 403 且绿。少读一个就会把"新守卫被收进 discover"这件事证歪。
bat_prev = log('r221_battery3.log')
ran_prev = int(re.search(r'Ran (\d+) tests', bat_prev).group(1))
if ran_before != ran_after or ran_after != ran_prev + 3:
    die('电池格数 %d → %d → %d，不是"上一轮 +3 且前后同数" ⇒ 新守卫的三格没全被收进 discover'
        % (ran_prev, ran_before, ran_after))

mut = log('r222_mutate3.log')
mm = re.search(r'R222_MUTATE 刀=(\d+) CAUGHT=(\d+) ESCAPED=(\d+) NOT_RUN=(\d+)', mut)
if not mm:
    die('读不到变异表结论行')
knives, caught, escaped, not_run = [int(x) for x in mm.groups()]
if escaped or not_run or caught != knives:
    die('变异表不干净：' + mm.group(0))
first_table = log('r222_mutate2.log')
table_was_wrong = 'ESCAPED=2' in first_table

pre = log('r222_precheck.log')
mp = re.search(r'NEEDLE_PRECHECK tables=(\d+) covered=(\d+) arms=(\d+) bad=(\d+)', pre)
tables, covered, arms, bad = [int(x) for x in mp.groups()]

diff = subprocess.run(['git', 'diff', '--name-only', 'HEAD'], cwd=ROOT,
                      stdout=subprocess.PIPE).stdout.decode('utf-8', 'replace')
changed = [p for p in diff.splitlines() if p.strip()]
prod = [p for p in changed if p.startswith('ClipboardHistory/Sources/')]
if len(prod) != 0:
    die('本轮宣称 0 产品文件，实得 ' + str(prod))
report_changed = [p for p in changed if p == 'AGENT_FINAL_REPORT.md']
if len(report_changed) != 1:
    die('报告没在改动清单里 ⇒ 本轮的主对象不明')

# ——————————————————— 编号 ———————————————————

u_ids = [int(x) for x in re.findall(r'^- \*\*U-(\d+)：', ui, re.M)]
U1, U2, U3 = max(u_ids) + 1, max(u_ids) + 2, max(u_ids) + 3
b_max = max([int(x) for x in re.findall(r'^\*\*(\d+)\. ', read('AGENT_BACKLOG.md'), re.M)])
NEW_B = b_max + 1
d_max = max([int(x) for x in re.findall(r'^\*\*D-(\d+)（', read('AGENT_DECISIONS.md'), re.M)])
NEW_D = d_max + 1
this_round = last_round + 1
audit_round = this_round + 2
last_block = it[it.rindex('## Round %d · ' % last_round):]
dim_rows = re.findall(r'^\|([^|]+)\|\s*(\d+)/15\s*\|', last_block, re.M)
if len(dim_rows) != 7:
    die('上一节七维度行数 ' + str(len(dim_rows)))
dims = [d.strip() for d, _ in dim_rows]

TITLE = (u'最终报告的活数格换到对账：标题停在 R136 / §1 停在 94 轮与 U-210，'
         u'本轮起有一条守卫盯着它（并配两把刀）')
SCOPE = u'判据 1 文件 + 报告本体，产品 0 文件'

UI_NEW = u'''## 第 {AR} 轮（R222 · {DAY}）：{TITLE}（U-{U1}…U-{U3} · {SCOPE}）

- **U-{U1}：报告里那几格"活数"停得比账本还旧 —— 本轮把它们换到现读，并追加 R137–R{LR} 那一段。**
  改之前：标题写 **R9–R136**、§1 写 **94 轮 / R9–R101**、视觉台账那格写 **U-31 … U-210（179 条）**、
  日期停在 2026-10-14、"本机跑的就是这一版"引的是 **R33 那次**的 PID 与存档数。
  改之后（全部由 `.scratch/motion-audit-2/final_report_r222.py` 现读现写）：标题 **R9–R{LR}，{P2} 轮自评**、
  §1 轮数 **{P2}**（同一把尺 `curve_from_ledger.py` 的 `PHASE2 n`）、U 那一格 **U-31 … U-{UM}（{UR} 条定义行）**、
  日期 {DAY}，本机那一格换成 R219 的实际读数（`INSTALL_RESULT=ok`、条目 172→172），
  并把 R33 那两行**明确标成历史、不许当本轮证人** —— 报告里的 prose 一格没删（跨行的格子走行内替换，
  整行替换会把叙述截断）。新增 §12 记 R137–R{LR}：真正改到画面的只有 R219 那一笔亮档墨，
  其余在判据侧；以及五次**撤回/否证**（1.05 作废、冻住作废、"两台解释器"作废、pillow 之后仍无对象、
  表面账那格的担心是没读过的假设）。
- **U-{U2}：这一格以后停旧数会红 —— 新守卫三格，同一份样本的 before/after 都有证人。**
  `scripts/tests/test_final_report_headline.py`：① 报告标题与 §1 的 U 上界必须等于活账；
  ② 伪造旧值必须点名（`FINAL_REPORT_HEADLINE_STALE` / `FINAL_REPORT_UCELL_STALE`）；
  ③ 形状读不到（换了破折号）必须报 `..._UNPARSEABLE` 而**不许静默通过**。
  before/after：改前电池 `Ran {RB} ... FAILED (failures=1)`，红的就是这条新守卫（它靠报告的旧数才红）；
  写完之后 `Ran {RA} ... OK`（+3 格 = 这条守卫的三格，格数对账也断言过）。
  **本轮同时撞开一个自锁死**：生成器原来写的是"电池不绿就不许写报告"，而电池之所以红正是因为这条新守卫在报旧数 ⇒
  两者互相咬。处置不是把闸门关掉，是**只豁免本轮这一条守卫的名字**（其余红照旧拦），
  并把改前那条 FAIL 打印出来当证人。
- **U-{U3}：两把刀，以及一次"表坏了不是守卫坏了"的分辨。**
  `R222_MUTATE 刀={K} CAUGHT={C} ESCAPED={E} NOT_RUN={N} RESTORE_CLEAN=yes`：
  M759 把标题那格的不等比较改成恒假、M760 把 U 上界那格的改成恒假 ⇒ 伪造对照必须红（两条比较各自要有证人，
  一条坏了另一条还灵，R74/R75 那一族）。
  **第一版这张表报的是 `ESCAPED=2`** —— 手工复现同一种改动，测试确实 `FAILED (failures=1)`，
  所以坏的是**表的解析**：这台机器的 python3.9 在 `-v` 下把失败印成两段（行内 `... ` + 单独一行 `FAIL: 名字`），
  而我只认行内 `... FAIL` ⇒ 真红被读成 ESCAPED（R214 的"单数 failures"同一族：解析器认错了形状）。
  修完解析才拿到这条结论行。

其余读数：预检 `NEEDLE_PRECHECK tables={T} covered={CO} arms={A} bad={B}`；产品 0 文件 ⇒ 未换装本机；
看图腿 NOT-RUN（本轮无新帧、0 像素改动；报告是文字产物，对账由守卫而不是眼睛）。

'''.format(AR=audit_round, DAY=DAY, TITLE=TITLE, U1=U1, U2=U2, U3=U3, SCOPE=SCOPE,
           LR=last_round, P2=phase2_n, UM=u_max, UR=u_rows_cell, RB=ran_before, RA=ran_after,
           K=knives, C=caught, E=escaped, N=not_run, T=tables, CO=covered, A=arms, B=bad)

SCORES = {dims[0]: 11, dims[1]: 14, dims[2]: 14, dims[3]: 9,
          dims[4]: 15, dims[5]: 14, dims[6]: 14}
dim_table = '\n'.join([u'| ' + d + u' | ' + str(SCORES[d]) + u'/15 |' for d in dims])
TOTAL = sum(SCORES.values())

IT_BLOCK = u'''
## Round {TR} · {TITLE}（{DAY} · {SCOPE}）

`AGENT_FINAL_REPORT.md` 是目标点名的最终产物，而它的标题停在 **R136**、§1 停在 **94 轮 / U-210 / 179 条**、
日期停在 2026-10-14、"本机跑的就是这一版"引的还是 **R33** 那一次的 PID。
这一族 U-264 记过一次（那次停在 R46，靠人眼发现）。本轮不再靠眼睛：
`.scratch/motion-audit-2/final_report_r222.py` 现读现写（曲线工具的 `PHASE2 n`、两本账的 max、闸门的 verdicts、
帧基线的条数），写之前先跑一遍电池、写之后守卫必须绿；跨行的那两格走**行内替换**，
因为整行替换会把报告里的叙述截断 —— prose 是资产，不是占位。
R33 那两行没删，改成明确标注"历史读数，别当本轮证人"。

新守卫 `test_final_report_headline.py` 三格：与活账一致 / 伪造旧值必须点名 / 形状读不到不许静默通过。
before/after 同一份样本：改前 `Ran {RB} FAILED(failures=1)`（红的就是这条新守卫），
改后 `Ran {RA} OK`（+3 格，格数也断言过）。本轮还撞开一个自锁死：生成器"电池不绿不写"与新守卫
"靠报告旧数才红"互相咬 —— 处置是只豁免这一条守卫的名字、其余红照旧拦，并把改前的 FAIL 打印出来当证人。

两把刀 `R221→R222_MUTATE 刀={K} CAUGHT={C} ESCAPED={E} NOT_RUN={N}`：M759/M760 各打一条 staleness 比较。
**第一版这张表报 `ESCAPED=2`**，手工复现证明测试其实 `FAILED` ⇒ 坏的是表的解析：
python3.9 在 `-v` 下把失败印成两段（行内 `... ` 与单独一行 `FAIL: 名字`），我只认了行内那一种
（R214 的"单数 failures"同一族）。**"刀没咬到"与"我看刀的口型错了"是两件事**，这一轮又分开了一次。

看图腿 NOT-RUN：本轮 0 像素改动、无新帧；报告是文字产物，它的新旧由守卫盯，不由眼睛盯。
分数最高的两格是给"台账一致性/可复核性"—— 本轮的产出确实就在这两处；产品面推进照旧低（{S3}/15）。

七维度自评：

| 维度 | 得分 |
|---|---|
{DIMTABLE}

总分 {TOTAL}/105（{TR} 轮）。GAPS=none
'''.format(TR=this_round, TITLE=TITLE, DAY=DAY, SCOPE=SCOPE, RB=ran_before, RA=ran_after,
           K=knives, C=caught, E=escaped, N=not_run, TOTAL=TOTAL, DIMTABLE=dim_table, S3=SCORES[dims[3]])

CH_BLOCK = u'''### 最终报告的活数格对账 + 一条会红的守卫（R{R} / U-{U1}…U-{U3} · {SCOPE}）

- 刷新：标题 **R9–R{LR}，{P2} 轮自评**、§1 轮数 **{P2}**、视觉台账 **U-31 … U-{UM}（{UR} 条定义行）**、
  日期、本机 install（R219 实际读数；R33 那两行标为历史）。全部由生成器现读，不手抄。
- 新增 §12：R137–R{LR} 这一段做了什么 / 撤回了什么 / 还欠什么（含五次否证与两次自曝量错对象）。
- 新守卫 `scripts/tests/test_final_report_headline.py`（三格：与活账一致、伪造旧值必须点名、
  形状读不到不许静默通过）。before/after：`Ran {RB} FAILED` → `Ran {RA} OK`（+3 格）。
- 刀：`R222_MUTATE 刀={K} CAUGHT={C} ESCAPED={E} NOT_RUN={N}`（M759/M760 各打一条比较）；
  第一版报 ESCAPED 是**表的解析坏了**（python3.9 `-v` 把失败印成两段），手工复现分开之后修解析。
- 自锁死记录：生成器"电池不绿不写"与新守卫"靠报告旧数才红"互相咬 ⇒ 只豁免这一条守卫的名字，其余红照旧拦。
- 新开 {NB}：§1 剩下的格子（位点清单 179 行、人工批次、swift/脚本计数）还没纳入对账。
  立 **D-{ND}**：报告里的活数格必须有守卫对账，一次性叙述要标"历史，别当本轮证人"。

'''.format(R=222, U1=U1, U3=U3, SCOPE=SCOPE, LR=last_round, P2=phase2_n, UM=u_max, UR=u_rows_cell,
           RB=ran_before, RA=ran_after, K=knives, C=caught, E=escaped, N=not_run, NB=NEW_B, ND=NEW_D)

STATE_BLOCK = u'''最后更新：{NOW}（本地 · R222 / 第 {AR} 轮：**{TITLE}**（U-{U1}…U-{U3} · {SCOPE}）

**本轮落地**：`AGENT_FINAL_REPORT.md` 的活数格换到现读现写 —— 标题从 **R136** 到 **R{LR}**、
§1 轮数从 **94** 到 **{P2}**（`PHASE2 n`）、视觉台账从 **U-210 / 179 条** 到 **U-{UM} / {UR} 条**、
日期与本机 install 那格换成 R219 的实际读数（R33 那两行标为历史，不删 prose 只走行内替换），
并追加 §12（R137–R{LR} 做了什么 / 撤回了什么 / 还欠什么，含五次否证与两次自曝量错对象）。
新守卫 `test_final_report_headline.py` 三格（与活账一致 / 伪造旧值必须点名 / 形状读不到不许静默通过）；
before/after 同一份样本：`Ran {RB} FAILED(failures=1)` → `Ran {RA} OK`。
两把刀 `R222_MUTATE 刀={K} CAUGHT={C} ESCAPED={E} NOT_RUN={N}`（M759/M760 各打一条 staleness 比较）；
**第一版报 ESCAPED 是表的解析坏了**（python3.9 `-v` 把失败印成两段，只认行内 `... FAIL` 会读漏）⇒ 修解析。
自锁死记录：生成器"电池不绿不写"与新守卫"靠报告旧数才红"互相咬 ⇒ 只豁免这一条守卫的名字，其余红照旧拦。
新开 {NB}（§1 其余格子纳入对账或删掉）、立 **D-{ND}**。
验证：产品 0 文件 ⇒ 未换装本机、无新帧 ⇒ 看图腿 NOT-RUN；预检 `tables={T} covered={CO} arms={A} bad={B}`。
CI：`bc5c5d7`=39272702346、`cc0e358`=39272745719 与本轮这一跑仍待读（246 的成因读数要看 runner 正文）。

**下一轮（R223）的靶**：⓪ 读上面几跑：左轴那一步现在打的 `cause=` 是哪一档（**246 结案的唯一通道**）、
`STEP[8]`/`STEP[15]` 是否仍绿、预检 `bad` 那一格顺手读明白（247）；
① **回到动效位点本体**（连续多轮 0 产品改动）：清账表未判的格子挑一位点真做动效 + 帧 + 刀 + 看图；
② {NB}：§1 剩下的格子对账；③ 242 其余亮档表面、243、227③、222、215、201/202、207、244、240；
④ 220 路 A、228② 等用户。
)

'''.format(NOW=NOW, AR=audit_round, TITLE=TITLE, U1=U1, U3=U3, SCOPE=SCOPE, LR=last_round,
           P2=phase2_n, UM=u_max, UR=u_rows_cell, RB=ran_before, RA=ran_after,
           K=knives, C=caught, E=escaped, N=not_run, NB=NEW_B, ND=NEW_D, T=tables, CO=covered, A=arms, B=bad)

BL_BLOCK = u'''
**{NB}. §1 交付清单剩下的格子还没纳入对账：位点清单 179 行、人工批次、swift/脚本计数（R222 开，配 D-{ND}）**

R222 只对账了三格（标题的轮次区间、§1 的阶段二轮数、视觉台账的 U 区间）—— 因为那三格是**这次真的停在旧数**上被抓到的。
§1 其余行同样是活数：`全量位点清单 179 行`、`人工验收批次 …`、以及散在正文里的 swift 例数 / 脚本条数 / 帧数。
今天没有任何断言会替我盯它们（`test_final_report_claims.py` 管的是 §9.3 那三条声明，`test_final_report_headline.py` 管的是本轮这三格）。
要做的：每加一格对账就配一格伪造对照（同一族的形状），或者干脆把这些格改成"由生成器现读"的模板行；
**不许**留着旧数只在正文里写一句"可能会过期" —— 那正是 U-264 那族"报告格子停在旧数"的成因。
适用面：`AGENT_FINAL_REPORT.md` §1 与任何被引用的活数格；不适用：明确标注为历史的段落
（R222 把 R33 那两行就是这样处理的：留着、标成历史、不许当本轮证人）。

'''.format(NB=NEW_B, ND=NEW_D)

DE_BLOCK = u'''
**D-{ND}（R222）：报告里的"活数格"必须有守卫对账；对不上账的旧数要么改现读、要么明确标成历史，不许只写一句"可能会过期"**

现场：目标的最终产物 `AGENT_FINAL_REPORT.md` 标题停在 R136、§1 停在 94 轮 / U-210 / 179 条、
"本机跑的就是这一版"引的还是 R33 那一次的 PID —— 而账本已经写到 R{LR}。
同一族在 U-264 记过一次（那次停在 R46，靠人眼发现）。**人会忘，格子不会自己红**，所以：
① 凡是"当前状态"含义的数（轮次、条目数、判据数、帧数、装机证据），要么由生成器现读，
   要么由一条守卫对活账（伪造旧值必须点名 + 形状读不到不许静默通过）；
② 做不到对账的叙述就**明确标注为历史**并写清"别当本轮证人"（本轮对 R33 那两行的处置），
   而不是留着让它冒充现状；
③ 改报告只准**行内替换**跨行的格子：整行替换会把报告里的叙述与续行截断 —— prose 是资产，不是占位；
④ 生成器的"电池不绿就不写"这类前置闸门，遇到"本轮新增的守卫正是因为旧数才红"时，
   处置是**只豁免那一条守卫的名字**并把改前的红打印出来当证人，而不是关掉闸门或改断言。
适用面：所有会被引用的"现状格"；不适用：轮次台账本身（那些由 `test_round_batch_consistency.py` 与曲线工具盯）。
'''.format(ND=NEW_D, LR=last_round)

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


plan_insert('AGENT_UI_AUDIT.md', u'## 第 ' + str(audit_round - 1) + u' 轮（R221 · ', UI_NEW)
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
plan_insert_where('AGENT_STATE.md', u'^最后更新：', STATE_BLOCK, u'R221 / 第 223 轮')
plan_append('AGENT_BACKLOG.md', BL_BLOCK)
plan_append('AGENT_DECISIONS.md', DE_BLOCK)

for path, old, new in plans:
    if len(new.splitlines()) <= len(old.splitlines()):
        die('写盘前最后一道：' + path + u' 行数没增加')
    if not reinsertion_matches(old, new, path):
        die('写盘前最后一道：' + path + u' 抠掉新块后不等于旧文件')

for path, old, new in plans:
    write(path, new)

print(u'LEDGERS_R222 wrote %d files' % len(plans))
print(u'LEDGERS_R222 编号：第 %d 轮 / Round %d / U-%d…U-%d / BACKLOG +%d / D-%d'
      % (audit_round, this_round, U1, U3, NEW_B, NEW_D))
print(u'LEDGERS_R222 读数：报告 R%d/%d 轮、U-%d(%d 条)、电池 %d→%d、刀 %d/%d、表解析修过=%s'
      % (title_round, phase2_n, u_cell, u_rows_cell, ran_before, ran_after, caught, knives,
         'yes' if table_was_wrong else 'no'))

state = read('AGENT_STATE.md')
ms = re.search(u'最后更新：[^\\n]*?R(\\d+) / 第 (\\d+) 轮', state)
if not ms or int(ms.group(1)) != 222 or int(ms.group(2)) != audit_round:
    die('STATE 轮次行读不出 R222 / 第 ' + str(audit_round) + u' 轮')
for path, pat in ((u'AGENT_UI_AUDIT.md', u'^## 第 ' + str(audit_round) + u' 轮（R222'),
                  (u'AGENT_VISUAL_ITERATION.md', u'^## Round 222 · '),
                  (u'CHANGELOG.md', u'^### .*（R222 / ')):
    if not re.search(pat, read(path), re.M):
        die(path + u' 里读不到本轮标题：' + pat)
print(u'LEDGERS_R222 selfcheck ok')
sys.exit(0)
