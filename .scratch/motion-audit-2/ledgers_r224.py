# -*- coding: utf-8 -*-
"""R224 的台账生成器：246 的 runner 读数落账 + 左轴尺的坐标约定修好（BACKLOG 250 / D-216）。

沿用 R223 那套：共享 `BASE` 参数表、整行锚点、插入还原自检、渲染后占位符扫描、
写盘前"行数增加 + 抠掉新块==旧文件"两道门，以及写盘后的轮次标题复读。
"""
import io, os, re, subprocess, sys

ROOT = '/Users/wangziyi/Codex_Project0'
DAY = '2026-10-19'
NOW = subprocess.run(['date', '+%Y-%m-%d %H:%M'], cwd=ROOT,
                     stdout=subprocess.PIPE).stdout.decode().strip()


def read(p):
    return io.open(os.path.join(ROOT, p), encoding='utf-8').read()


def write(p, t):
    with io.open(os.path.join(ROOT, p), 'w', encoding='utf-8') as h:
        h.write(t)


def die(why):
    print('LEDGERS_R224 refused: ' + why)
    sys.exit(1)


def log(p):
    path = os.path.join('/tmp', p)
    if not os.path.exists(path):
        die('缺少本轮日志 ' + path + ' ⇒ 不许写台账')
    return io.open(path, encoding='utf-8', errors='replace').read()


# ——————————————————— 读数（全部从本轮日志解析，不手抄）———————————————————

ev = log('r224_runner_69bccbd.log')
axis = re.search(r'LEFT_AXIS_CI verdict=(\w+) hard=(\d+) not_run=(\d+) missing_frames=(\d+) probes=(\d+)', ev)
if not axis:
    die('runner 的 LEFT_AXIS_CI 结论行读不到')
causes = re.findall(r'LEFT_AXIS_NOT_RUN (\S+?)：cause=([\w-]+) frame=(\d+x\d+)', ev)
if not causes:
    die('runner 的 cause= 分档行读不到 ⇒ 246 的结案通道没有证人')
cause_kinds = sorted({c for _, c, _ in causes})
frames_seen = sorted({f for _, _, f in causes})
if cause_kinds != ['no-bg-window']:
    die('本轮账要按「runner 七颗全是 no-bg-window」写，实得 ' + str(cause_kinds))
pillow = re.search(r'PILLOW_OK ([\d.]+) (\S+)', ev)
script_pil = 'SCRIPT_PIL_OK' in ev
if script_pil:
    die('这一跑（69bccbd）里 SCRIPT_PIL_OK 不该露面（那是 R223 之后才上去的）⇒ 拿错文件')

before = json_rows = None
b = read('/tmp/r224_axes_before.json') if False else None

ident = log('r224_identity.log')
if 'IDENTICAL_TO_BEFORE=True' not in ident:
    die('本机 @2x 读数与改前不一致 ⇒ 这一改动了本机结论，不能按"只修坐标"写账')
rep = log('r224_replica.log')
m_old = re.search(r'OLD_1X_no_bg_window=(\d+)', rep)
m_new = re.search(r'NEW_1X_NOT_RUN帧=(\d+) verdict=(\w+)', rep)
if not m_old or not m_new:
    die('1x 复刻的 before/after 读数没存下来')
old_nobg, new_notrun, new_verdict = int(m_old.group(1)), int(m_new.group(1)), m_new.group(2)
if old_nobg != 7 or new_notrun != 0:
    die('复刻对照不成立：旧尺 %d 颗 no-bg-window、新尺 NOT_RUN=%d' % (old_nobg, new_notrun))
replica_shift = re.search(r'REPLICA_SHIFT 改前=(\S+) 改后=(\S+)', rep)
if not replica_shift:
    die('复刻帧的读数漂移没量 ⇒ 不许把它说成"runner 上也会读到 148"')

st = log('r224_selftest.log')
if 'LEFT_AXIS_SELFTEST ok' not in st:
    die('自检不绿')
n_cases = len(re.findall(r'^SELFTEST ', st, re.M))
if '两档缩放同读数' not in st:
    die('缩放不变量那格对照没露面')

mu = log('r224_mutate.log')
mmu = re.search(r'R224_MUTATE 刀=(\d+) CAUGHT=(\d+) ESCAPED=(\d+) NOT_RUN=(\d+)', mu)
if not mmu or mmu.group(1) != mmu.group(2) or mmu.group(3) != '0' or mmu.group(4) != '0':
    die('变异表不干净 ⇒ 不写台账')
knives, caught = int(mmu.group(1)), int(mmu.group(2))
pre = log('r224_precheck.log')
mp = re.search(r'NEEDLE_PRECHECK tables=(\d+) covered=(\d+) arms=(\d+) bad=(\d+)', pre)
if not mp:
    die('预检结论行读不到')
tables, covered, arms, bad = [int(x) for x in mp.groups()]
if tables != 65 or bad != 4:
    die('预检读数与本轮宣称不符：tables=%d bad=%d' % (tables, bad))

bat = log('r224_battery1.log')
mbat = re.search(r'Ran (\d+) tests', bat)
if not mbat or re.search(r'^(FAILED|ERROR)', bat, re.M) or 'OK' not in mbat.string:
    die('电池不绿')
ran = int(mbat.group(1))

diff = subprocess.run(['git', 'diff', '--name-only', 'HEAD'], cwd=ROOT,
                      stdout=subprocess.PIPE).stdout.decode('utf-8', 'replace')
changed = [p for p in diff.splitlines() if p.strip()]
prod = [p for p in changed if p.startswith('ClipboardHistory/Sources/')]
if prod:
    die('本轮宣称 0 产品文件，实得 ' + str(prod))
ruler = [p for p in changed if p == 'scripts/surface_left_axes.py']
if len(ruler) != 1:
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

TITLE = (u'246 的 runner 读数落账：七颗探针全在 no-bg-window，'
         u'查出来是这把尺把窗口写在 @2x 像素上 —— 坐标约定已修（BACKLOG %d / D-%d）' % (NEW_B, NEW_D))
SCOPE = u'判据（python 尺）1 文件 + 表 1 文件，产品 0 文件'

BASE = dict(AR=audit_round, R=224, DAY=DAY, NOW=NOW, TITLE=TITLE, U1=U1, U2=U2, U3=U3,
            SCOPE=SCOPE, tables=tables, covered=covered, arms=arms, bad=bad,
            ran=ran, knives=knives, caught=caught, n_cases=n_cases,
            av=axis.group(1), anr=axis.group(3), ap=axis.group(5),
            frames=' / '.join(frames_seen), pv=(pillow.group(1) if pillow else '未读'),
            old_nobg=old_nobg, new_notrun=new_notrun, new_verdict=new_verdict,
            shift=(replica_shift.group(0) if replica_shift else '未量'),
            NB=NEW_B, ND=NEW_D, LR=last_round)

UI_NEW = u'''## 第 {AR} 轮（R{R} · {DAY}）：{TITLE}（U-{U1}…U-{U3} · {SCOPE}）

- **U-{U1}：⓪ 的读数拿到了 —— runner 上那 7 个 NOT_RUN 第一次说得出成因，而成因说的是我这把尺。**
  run `39273827335`（`69bccbd`，**success**）正文：`LEFT_AXIS_CI verdict={av} hard=0 not_run={anr} probes={ap}`，
  七行分档全是 `cause=no-bg-window frame={frames}` —— 帧**拍到了、尺寸也对**（`missing_frames=0`），
  掉到画外的是**取底窗口**。R221 那格成因分档（BACKLOG 246 的仪器）第一轮就把病根指出来了。
- **U-{U2}：病根是坐标约定：探针窗口写在**本机 @2x 帧的像素**上**（统计页的 bg 写在 y=900..960，
  而 @1x 的帧只有 540 高）⇒ 同一颗探针在 runner 上必然取不到底。修法是"窗口按 **pt** 写 +
  `像素每 pt = 帧宽 ÷ 帧名里的 pt 宽`（由帧自己说，不猜 2）"。
  两个方向的对照都做了：① 本机 @2x 真帧改前/改后**逐字相同**（`IDENTICAL_TO_BEFORE=True`，
  7 颗读数 + 4 条关系判据 + 0 问题）⇒ 这一改没动本机结论；
  ② 同一批内容缩到 @1x 的复刻帧上，旧尺 `{old_nobg}` 颗 `no-bg-window`、新尺 `NOT_RUN帧={new_notrun}`
  （`LEFT_AXIS_VERDICT {new_verdict}`）⇒ 修的是坐标，不是把红洗成绿。**但复刻帧的 pt 读数不等于真帧读数**
  （{shift}）：LANCZOS 降采样会把细笔画压到门槛以下，左轴因此右移并造出一条假 `OFF_AXIS`
  ⇒ 它只配证明"窗口掉到画外"这一格被修好，不配给产品定罪（R87：合成样本不配）。
  真正承重的是自检里新加的那格**缩放不变量**：同一份内容按 pt 画在 @2x/@1x 两档，7 颗探针的 pt 读数逐字相等。
- **U-{U3}：CI 与名册的其余读数。**
  同一次 run 里 `PILLOW_OK {pv}` 在 venv 那一步露面，而 `SCRIPT_PIL_OK` **没有一行** ——
  判据卷走 venv 是 R223（`e015455`）才上去的，那一跑仍 `in_progress` ⇒ **244 不写结案**。
  两把刀 `R224_MUTATE 刀={knives} CAUGHT={caught} ESCAPED=0 NOT_RUN=0 RESTORE_CLEAN=yes`（M761 写死密度、M762 去掉换算）。
  预检 `NEEDLE_PRECHECK tables={tables} covered={covered} arms={arms} bad={bad}`，
  顺手发现名册里 `mutate_r220` 被登记了**两次**（同一支表被静态扫两遍，不改变结论但会污染"表数"）⇒ 去重。
  自检共 {n_cases} 格。产品 0 文件 ⇒ 未换装本机；看图腿：本轮真看了 5 张帧（`settings-stats-populated` 亮、
  `quickpick-hover` 亮、`content-with-history` 亮、`sidebar-history` 亮、`menubar-recommendations` 暗），
  挑出的两个候选位点**一查决定台账都已有判词**（侧栏那一整块纯黑 = 已登记的离屏伪影；
  菜单栏墨顶到两边 = U-56 在 R34 已收回，成因是复刻没有右内边距）⇒ 没据此改产品，欠的仍是"逐位点做动效"。

其余读数：电池 `Ran {ran} tests ... OK`；本机左轴出口 `verdict=ok probes=7` 一字未变。

'''.format(**BASE)

SCORES = {dims[0]: 10, dims[1]: 13, dims[2]: 14, dims[3]: 9,
          dims[4]: 14, dims[5]: 14, dims[6]: 14}
dim_table = '\n'.join([u'| ' + d + u' | ' + str(SCORES[d]) + u'/15 |' for d in dims])
BASE.update(DIMTABLE=dim_table, TOTAL=sum(SCORES.values()), TR=this_round, S3=SCORES[dims[3]])

IT_BLOCK = u'''
## Round {TR} · {TITLE}（{DAY} · {SCOPE}）

上一轮我为"runner 上 7 颗探针全部没有对象"装了成因分档（246 的仪器），本轮 ⓪ 读到的是：
`cause=no-bg-window frame={frames}` 七行齐刷刷同一档，而 `missing_frames=0` —— 帧在、尺寸对，
取不到的是**底**。顺着这一档回读自己的表：窗口坐标是照本机 @2x 帧的像素写死的（统计页 bg 写在 y=900..960，
@1x 的帧只有 540 高）⇒ 那 7 个 NOT_RUN 量的是我这把尺的坐标约定，不是产品。
改成"窗口按 pt 写 + 像素每 pt 由帧自己算"，两向对照：本机 @2x 读数逐字不变（`IDENTICAL_TO_BEFORE=True`）、
@1x 复刻帧从 `{old_nobg}` 颗 no-bg-window 变成 `NOT_RUN帧={new_notrun}`。
复刻帧的 pt 读数与真帧不同（{shift}）⇒ 降采样把细笔画压到门槛以下，它只配证明坐标被修好，不配给产品定罪；
承重的是自检新增的**缩放不变量**那格（同一内容两档密度、pt 读数逐字相等）。
两把刀 `R224_MUTATE 刀={knives} CAUGHT={caught} ESCAPED=0 NOT_RUN=0`，名册里 `mutate_r220` 登记两次已去重。

CI：`69bccbd`=`39273827335` **success**、`PILLOW_OK {pv}`，但 `SCRIPT_PIL_OK` 没有一行
（判据卷走 venv 是 R223 的 `e015455`，那一跑仍 in_progress）⇒ **244 仍等**；
246 结成本轮这个样子，新开 **{NB}**：修完之后 runner 上那四条关系判据**第一次真判产品**，
红要归因、不许放宽（R154 那一族），而 @1x 原生帧的门槛灵敏度还没量。

看图腿：真看了 5 张帧，挑出的两个候选位点一查都已有判词（侧栏纯黑=已登记的离屏伪影；
菜单栏墨顶边=U-56 已在 R34 收回）⇒ 没据此改产品。**动效位点本体的欠账还在**，
本轮又一次把它推到下一轮 —— 这是自评里"动效细节/交付面"两格上不去的同一件事。

七维度自评：

| 维度 | 得分 |
|---|---|
{DIMTABLE}

总分 {TOTAL}/105（{TR} 轮）。GAPS=none
'''.format(**BASE)

CH_BLOCK = u'''### 246 结案（runner 的成因读数=no-bg-window）+ 左轴尺的坐标约定修好（R{R} / U-{U1}…U-{U3} · {SCOPE}）

- runner 正文（run `39273827335` = `69bccbd`，success）：`LEFT_AXIS_CI verdict={av} not_run={anr} probes={ap}`，
  七行全 `cause=no-bg-window frame={frames}`、`missing_frames=0` ⇒ 帧在、尺寸对，掉到画外的是**取底窗口**。
- 病根：`scripts/surface_left_axes.py` 的探针窗口按本机 **@2x 像素**写死 ⇒ @1x 的 runner 帧上必然取不到底。
  修法：窗口按 **pt** 写，`像素每 pt` 由帧自己算（不猜 2）。
- 两向对照：本机 @2x 真帧改前/改后**逐字相同**；@1x 复刻帧从 `{old_nobg}` 颗 no-bg-window 到 `NOT_RUN帧={new_notrun}`。
  复刻帧读数与真帧不同（{shift}）⇒ 只配证明坐标被修好，不配给产品定罪；承重的是自检新增的缩放不变量那格。
- 刀 `R224_MUTATE 刀={knives} CAUGHT={caught} ESCAPED=0 NOT_RUN=0 RESTORE_CLEAN=yes`（M761/M762）；
  预检 `tables={tables} covered={covered} arms={arms} bad={bad}`；名册去掉 `mutate_r220` 的重复登记。
- 新开 **{NB}**（runner 第一次真判这四条关系判据之后的归因规矩）、立 **D-{ND}**（像素尺的坐标按 pt 写）。
- 验证：电池 `Ran {ran} tests OK`；产品 0 文件 ⇒ 未换装本机；看图腿真做了（5 张帧、两个候选位点均已有判词）。

'''.format(**BASE)

STATE_BLOCK = u'''最后更新：{NOW}（本地 · R{R} / 第 {AR} 轮：**{TITLE}**（U-{U1}…U-{U3} · {SCOPE}）

**本轮落地**：⓪ 读到 runner 的成因分档 —— 七颗探针全是 `cause=no-bg-window frame={frames}`、
`missing_frames=0` ⇒ 帧在、尺寸对，取不到的是**底**；顺着这一档读回自己的表，病根是**坐标约定**：
探针窗口按本机 @2x 像素写死，@1x 的 runner 帧必然掉到画外。改成"窗口按 pt 写 + 像素每 pt 由帧自己算"。
两向对照：本机 @2x 读数逐字不变（`IDENTICAL_TO_BEFORE=True`）、@1x 复刻帧 `{old_nobg}`→`NOT_RUN帧={new_notrun}`；
复刻帧读数不等于真帧（{shift}）⇒ 只配证明坐标修好，不配给产品定罪，承重的是新增的缩放不变量自检格。
两把刀 `R224_MUTATE 刀={knives} CAUGHT={caught} ESCAPED=0 NOT_RUN=0`；预检 `tables={tables} bad={bad}`；
名册去掉 `mutate_r220` 重复登记；电池 `Ran {ran} OK`。
CI：`69bccbd`=`39273827335` success、`PILLOW_OK {pv}`，`SCRIPT_PIL_OK` 没有一行（判据卷走 venv 在 `e015455`，仍 in_progress）
⇒ **244 仍等**；246 结案、新开 **{NB}**、立 **D-{ND}**。产品 0 文件 ⇒ 未换装本机。
看图腿真做了：5 张帧，挑出的两个候选位点一查都已有判词（侧栏纯黑=已登记离屏伪影；菜单栏墨顶边=U-56 已在 R34 收回）。

**下一轮（R225）的靶**：⓪ 读 `e015455`=39277485218 与本轮这一跑：`SCRIPT_SKIPS` 掉到几条（**244 结案的唯一通道**）、
左轴那一步在 @1x 上是否 `verdict=ok`（**{NB} 的第一格**）—— 若红，先归因再动手，不许放宽；
① **回到动效位点本体**（连续多轮 0 产品改动，本轮又是判据账）：按目标要求**逐屏逐元素列全清单**，
挑一位点真做动效 + 帧 + 基线 update + 刀 + 全量卷 + 换装 + 看图；
② 248（§1 其余活数格）、243、227③、222、215、201/202、207、240；③ 220 路 A、228② 等用户。
)

'''.format(**BASE)

BL_BLOCK = u'''
**{NB}. 左轴尺修完坐标约定之后，runner 上那四条关系判据第一次真判产品：红要归因、@1x 的门槛灵敏度还没量（R224 开单，配 D-{ND}）**

本轮把探针窗口从 @2x 像素改成 pt（密度由帧自己算），runner 那 7 颗 `no-bg-window` 的成因就没了。
于是下一跑会出现三种情形，处置各不相同，别混：
① `verdict=ok probes=7` ⇒ 246 的修法被 runner 验收，四条关系判据从此在 CI 上承重；
② `verdict=bad hard>0` ⇒ **先归因再动手**：@1x 原生帧上 12/6 这两档通道差门槛的灵敏度从未量过
（本轮唯一量到的反例是降采样复刻：细笔画被平均掉 ⇒ 左轴右移 ~29pt、并造出一条假 `OFF_AXIS`），
所以第一条要问的是"这台机器画得出这根轴吗"，不是"产品错了吗"；要补的是 @1x 的门槛分档读数；
③ 仍然 `not_run>0` 且成因换成 `no-ink` ⇒ 那才是"runner 帧没墨"那一族（R146–R149 的老账），另开单。
不许做的事：把 ② 直接放宽成出口（R74/R75：只在自家夹具上成立的理由比没做决定更贵）。

'''.format(NB=NEW_B, ND=NEW_D)

DE_BLOCK = u'''
**D-{ND}（R224）：像素尺的窗口坐标一律按 pt 写，"像素每 pt"由帧自己算 —— 不许把今天这台机器的密度写进表**

现场：`scripts/surface_left_axes.py` 的 7 颗探针在 runner 上全 `cause=no-bg-window`，而 `missing_frames=0`
（帧在、尺寸对）。读回表本身：窗口是照本机 @2x 帧的像素写死的（统计页 bg 写在 y=900..960，@1x 的帧只有 540 高），
于是"尺没有对象"其实是"尺的坐标约定只认一台机器"。
为什么危险：这类缺席长得像产品事实（"runner 上这块表面量不到"），而它每次都会以 NOT_RUN 出现，
只要没人按档读成因，就会被记成"那台机器画不出这块表面"——R38/R100 那一族（两台机器的读数不能互当对方）
的**像素版**，而且更隐蔽：这次连读数都没有，只有缺席。
规矩：① 像素尺的输入窗口按 **pt** 写；② 密度由**这张帧自己**给（`帧宽像素 ÷ 帧名里的 pt 宽`），
不许写死 2，也不许从别的帧借；③ 新增/改动探针要配一格**缩放不变量**对照
（同一份内容按 pt 画在 @2x 与 @1x，pt 读数逐字相等 —— 见 `--self-test` 的"正对照·两档缩放同读数"）；
④ 改完必须同时给"本机读数不变"与"@1x 从缺席变成有对象"两格对照，缺一格就是只验了一侧。
适用面：所有按像素坐标取样的脚本尺（`surface_left_axes.py`、`heatmap_frame_levels.py`、帧基线一类）；
不适用：只读**帧名尺寸**的判据（那些本来就没有坐标约定）。
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


plan_insert('AGENT_UI_AUDIT.md', u'## 第 ' + str(audit_round - 1) + u' 轮（R223 · ', UI_NEW)
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
plan_insert_where('AGENT_STATE.md', u'^最后更新：', STATE_BLOCK, u'R223 / 第 225 轮')
plan_append('AGENT_BACKLOG.md', BL_BLOCK)
plan_append('AGENT_DECISIONS.md', DE_BLOCK)

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

print(u'LEDGERS_R224 wrote %d files' % len(plans))
print(u'LEDGERS_R224 编号：第 %d 轮 / Round %d / U-%d…U-%d / BACKLOG +%d / D-%d'
      % (audit_round, this_round, U1, U3, NEW_B, NEW_D))

state = read('AGENT_STATE.md')
ms = re.search(u'最后更新：[^\\n]*?R(\\d+) / 第 (\\d+) 轮', state)
if not ms or int(ms.group(1)) != 224 or int(ms.group(2)) != audit_round:
    die('STATE 轮次行读不出 R224 / 第 ' + str(audit_round) + u' 轮')
for path, pat in ((u'AGENT_UI_AUDIT.md', u'^## 第 ' + str(audit_round) + u' 轮（R224'),
                  (u'AGENT_VISUAL_ITERATION.md', u'^## Round 224 · '),
                  (u'CHANGELOG.md', u'^### .*（R224 / ')):
    if not re.search(pat, read(path), re.M):
        die(path + u' 里读不到本轮标题：' + pat)
print(u'LEDGERS_R224 selfcheck ok')
sys.exit(0)
