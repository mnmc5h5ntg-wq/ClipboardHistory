#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把 ledgers_r301.py 变成 ledgers_r302.py —— 脚手架（事务、形状自测、现读计数）原样留着，
只换：轮次号、取数口、刀表名、电池路径、以及本轮的正文。

为什么用转换而不是从零写：r301 那份里每一处 `die()` 都是栽过跟头之后加的
（形状自测、锚点唯一、must_preserve、写盘前后电池同数、353 的门、§1 的 Sources 行）。
重写一份最容易丢的正是这些牙。
"""
import ast
import io
import re

SRC = '.scratch/motion-audit-2/ledgers_r301.py'
DST = '.scratch/motion-audit-2/ledgers_r302.py'

t = io.open(SRC, encoding='utf-8').read()

MECH = [
    (u'"""R301（第 300 轮 / Round 298）的七本台账落盘 —— 事务性，与 ledgers_r300 同一形状。',
     u'"""R302（第 301 轮 / Round 299）的七本台账落盘 —— 事务性，与 ledgers_r301 同一形状。'),
    (u'本轮**不动产品**（只动 Tests 与 .scratch），所以 streak 由取数口按 as-of 第 300 轮现读（=1），',
     u'本轮**不动产品**（只动 Tests / scripts / .scratch），所以 streak 由取数口按 as-of 第 301 轮现读（=2），'),
    (u'VERIFY_LOG = "/tmp/r301_verify_run.log"', u'VERIFY_LOG = "/tmp/r302_verify_run.log"'),
    (u'READINGS = "/tmp/r301_frames/capture-readings.log"   # 定向跑的取数口（本轮把它写进账，见 U-@UD@ / @BLN2@）\n'
     u'VERIFY_READINGS = "/tmp/r301_verify/frames/capture-readings.log"',
     u'VERIFY_READINGS = "/tmp/r302_verify/frames/capture-readings.log"\n'
     u'COV_ROLL = os.path.join("scripts", "tests", "test_readings_channel_coverage.py")'),
    (u'KNIVES = os.path.join(ROOT, ".scratch", "motion-audit-2", "mutate_r301.py")',
     u'KNIVES = os.path.join(ROOT, ".scratch", "motion-audit-2", "mutate_r302.py")'),
    (u'SCORES = [11, 13, 14, 4, 13, 14, 14]', u'SCORES = [11, 14, 14, 4, 13, 14, 14]'),
    (u'R_TAG = u"R301"\nR_NEXT = u"R302"\nPREV_TAG = u"R300"',
     u'R_TAG = u"R302"\nR_NEXT = u"R303"\nPREV_TAG = u"R301"'),
    (u'LEDGERS_R301 REFUSED', u'LEDGERS_R302 REFUSED'),
    (u'u"(?m)^R301_MUTATE 刀=', u'u"(?m)^R302_MUTATE 刀='),
    (u'/tmp/r301_battery_pre.log', u'/tmp/r302_battery_pre.log'),
    (u'/tmp/r301_battery_post.log', u'/tmp/r302_battery_post.log'),
    (u'u"LEDGERS_R301 OK batt=Ran ', u'u"LEDGERS_R302 OK batt=Ran '),
    (u'if LAST_ROUND != s(ROUND - 1):', u'if LAST_ROUND != s(ROUND - 2):'),
    (u'⇒ 与本轮（第 %d 轮）不同源，先查', u'⇒ 与本轮（第 %d 轮）差两格，先查'),
    (u'if (U_MAX, D_MAX, BL_MAX) != (984, 281, 357):', u'if (U_MAX, D_MAX, BL_MAX) != (988, 282, 359):'),
    (u'UA, UB, UC, UD = U_MAX + 1, U_MAX + 2, U_MAX + 3, U_MAX + 4',
     u'UA, UB, UC = U_MAX + 1, U_MAX + 2, U_MAX + 3'),
    (u'DN, BLO, BLN2 = D_MAX + 1, BL_MAX + 1, BL_MAX + 2', u'DN, BLO = D_MAX + 1, BL_MAX + 1'),
    (u'    u"@UA@": s(UA), u"@UB@": s(UB), u"@UC@": s(UC), u"@DN@": s(DN),',
     u'    u"@UA@": s(UA), u"@UB@": s(UB), u"@UC@": s(UC), u"@DN@": s(DN),'),
    (u'SUBS2[u"@UDEF@"] = s(U_DEFS + 4)', u'SUBS2[u"@UDEF@"] = s(U_DEFS + 3)'),
    (u'for n in (BLO, BLN2):', u'for n in (BLO,):'),
    (u'startswith(u"**357. ")', u'startswith(u"**358. ")'),
    (u'die(u"357 锚点异常（%d 处）" % len(h357))', u'die(u"358 锚点异常（%d 处）" % len(h357))'),
    (u'die(u"357 已有 %s 的结案追记" % R_TAG)', u'die(u"358 已有 %s 的结案追记" % R_TAG)'),
    (u'sources_row = u"**%s**（commit `%s`）" % (PREV_TAG, LAST_SHA)',
     u'sources_row = u"**%s**（commit `%s`）" % (u"R%d" % (int(LAST_ROUND) + 1), LAST_SHA)'),
    (u'"BL": BACK_357 + ITEM_BLO + ITEM_BLN2, "CH": CHG_NEW, "ST": STATE_NEW,',
     u'"BL": CLOSE_358 + ITEM_BLO, "CH": CHG_NEW, "ST": STATE_NEW,'),
    (u'if nums != [UA, UB, UC, UD]:\n    die(u"节内 U 定义行与标题区间不吻合：%s vs %s" % (nums, [UA, UB, UC, UD]))',
     u'if nums != [UA, UB, UC]:\n    die(u"节内 U 定义行与标题区间不吻合：%s vs %s" % (nums, [UA, UB, UC]))'),
]

for a, b in MECH:
    n = t.count(a)
    if n != 1:
        raise SystemExit(u'MECH anchor count=%d: %r' % (n, a[:80]))
    t = t.replace(a, b)

# ── 取数块：热图 marker 那一套换成本轮真正的仪器（覆盖率那一卷的自印读数行）────
start = t.index(u'# 读数通道：本轮的全部意义就是')
stop = t.index(u'kout, krc = sh(["python3", KNIVES])')
COV = u'''# 覆盖率那一卷的自印读数行 —— 本轮进账的所有覆盖率数都必须来自它（现读现取，不算）
cout0, crc0 = sh(["python3", "-W", "ignore", "-m", "unittest", "-v", COV_ROLL])
cov = (re.findall(u"(?m)^READINGS_COVERAGE (.*)$", cout0, re.M) or [u""])[-1]
ck = dict(x.split(u"=", 1) for x in cov.split() if u"=" in x)
if crc0 != 0 or u"bare_print_lines" not in ck or u"ceiling" not in ck:
    die(u"覆盖率那一卷没有可判正文（rc=%s）⇒ 进账的覆盖率数没有取数口" % crc0)
if ck[u"bare_print_lines"] != ck[u"ceiling"]:
    die(u"棘轮不自洽：现读 %s 行 vs 登记 %s ⇒ 那一卷自己就是红的，先把数对齐再落账"
        % (ck[u"bare_print_lines"], ck[u"ceiling"]))
rk = dict()
rline = (re.findall(u"(?m)^READINGS_ROSTER (.*)$", cout0, re.M) or [u""])[-1]
for part in re.findall(u"(\\S+?)=([^ ]*)", rline):
    rk[part[0]] = part[1]
if rk.get(u"未纳管", u"?") != u"无" or rk.get(u"已过期", u"?") != u"无":
    die(u"名册与派生集不同源：未纳管=%s 已过期=%s ⇒ 这一格的牙正对着本轮的改动，不能带红落账"
        % (rk.get(u"未纳管", u"?"), rk.get(u"已过期", u"?")))
FILES_SCANNED = ck[u"files_scanned"]
EMITTERS = ck[u"emitters"]
BARE = ck[u"bare_print_lines"]
CEIL = ck[u"ceiling"]
ROSTER_N = ck[u"roster"]
UNCOV_SUM = ck[u"named_uncovered"]
worst_out, wrc = sh(["python3", "-c",
                     "import sys; sys.path.insert(0, 'scripts/tests');"
                     "import test_readings_channel_coverage as m;"
                     "k, v = max(m.NAMED_UNCOVERED.items(), key=lambda kv: kv[1]);"
                     "print('WORST %s=%d files=%d' % (k, v, len(m.NAMED_UNCOVERED)))"])
wm = (re.findall(r"^WORST (\S+)=(\d+) files=(\d+)", worst_out, re.M) or [None])[0]
if wrc != 0 or not wm:
    die(u"未覆盖名单的最大值取不到（rc=%s）：%s" % (wrc, worst_out.strip()[-200:]))
WORST_FILE, WORST_N, UNCOV_FILES = wm[0], wm[1], wm[2]
if UNCOV_SUM != BARE:
    die(u"未覆盖名单合计 %s 与现读裸 stdout 行数 %s 不等 ⇒ 有文件的行数没登记（漏一行就漏一整格）"
        % (UNCOV_SUM, BARE))
# 取证面（359）本轮重量一次：四件套目录里热图 marker 仍然读不到吗？
if not os.path.exists(VERIFY_READINGS):
    die(u"四件套的读数文件不存在：%s" % VERIFY_READINGS)
vtext = rd(VERIFY_READINGS)
VERIFY_HEAT = len(re.findall(u"(?m)^HEAT", vtext))
VERIFY_LINES = len(vtext.splitlines())
APPEAR = u"1/17 与 1/7"

'''
t = t[:start] + COV + t[stop:]

# ── SUBS：本轮的 token ─────────────────────────────────────────────
sstart = t.index(u'SUBS = {')
sstop = t.index(u'\n}\n', sstart) + 3
NEW_SUBS = (u'SUBS = {\n'
u'    u"@RTAG@": R_TAG, u"@PREV@": PREV_TAG, u"@RNEXT@": R_NEXT,\n'
u'    u"@ROUND@": s(ROUND), u"@RDN@": s(RD_N),\n'
u'    u"@UA@": s(UA), u"@UB@": s(UB), u"@UC@": s(UC), u"@DN@": s(DN), u"@BLO@": s(BLO),\n'
u'    u"@STREAK@": STREAK_N, u"@LASTSHA@": LAST_SHA, u"@LASTROUND@": LAST_ROUND,\n'
u'    u"@MAXROUND@": MAX_ROUND, u"@CM@": vk[u"baseline_compared"], u"@CH@": vk[u"baseline_changed"],\n'
u'    u"@FRAMES@": vk[u"frames"], u"@SWIFT@": vk[u"swift_executed"], u"@SWFAIL@": vk[u"swift_failures"],\n'
u'    u"@Dmg@": vk[u"dmg"], u"@VER@": vk[u"installed_version"], u"@WARN@": vk[u"build_warnings"],\n'
u'    u"@ROWS@": ROWS + u"\\n", u"@TOTAL@": s(TOTAL), u"@BATT@": pre[0], u"@SKIP@": pre[1],\n'
u'    u"@ARMS@": ARMS, u"@KN@": KN, u"@KC@": KC, u"@KREST@": KREST, u"@TODAY@": TODAY,\n'
u'    u"@SECTIONS@": s(int(SECTIONS) + 1), u"@TAIL@": TAIL_OLD,\n'
u'    u"@FILES@": FILES_SCANNED, u"@EMITTERS@": EMITTERS, u"@ROSTER@": ROSTER_N,\n'
u'    u"@BARE@": BARE, u"@CEIL@": CEIL, u"@UNCOVFILES@": UNCOV_FILES, u"@UNCOSUM@": UNCOV_SUM,\n'
u'    u"@WORSTFILE@": WORST_FILE, u"@WORSTN@": WORST_N,\n'
u'    u"@VHEAT@": s(VERIFY_HEAT), u"@VLINES@": s(VERIFY_LINES), u"@APPEAR@": APPEAR,\n'
u'}\n')
t = t[:sstart] + NEW_SUBS + t[sstop:]

# ── 正文块（三引号那一类）──────────────────────────────────────────
def block(name, new, prefix=u'u"""'):
    global t
    head = name + u' = ' + prefix
    i = t.index(head)
    j = t.index(u'"""', i + len(head) + 3) + 3
    return t[:i] + name + u' = ' + prefix + new + u'"""' + t[j:]

UI = u'''
## 第 @ROUND@ 轮（@RTAG@ · U-@UA@…U-@UC@ · @TODAY@）：两份「两条腿」合成一份，覆盖率第一次是一个会红的数

- **U-@UA@：@PREV@ 新开的那份重复实现（@BLO@ 之外的 358）本轮删掉了 —— 不是整理，是缺陷。**
  `MotionFilmstripTests` 自己实现了一遍读数落盘：stdout 一条腿、`FileHandle` 追加一条腿，
  外加一颗**共享布尔**做「每个进程第一次写整份重写」。问题是这三样里被锤过的那两样
  （按 URL 记首次、进程内一把锁）只长在 `CaptureReadings` 那一侧 —— R79 / BACKLOG 112 在 CI 日志里
  抓到过「两个线程同时看见没开过 ⇒ 两边都做整份重写 ⇒ 后写的那一份把前一份整卷抹掉」，
  而没锁的那份每天在写动效卷的全部读数。现在这里只剩一层壳
  `CaptureReadings.emit(line, to: readingsURL)`；同一轮把 `TableProbe` 里两处
  `NATIVE_PROBE_STATE`（探针「这一趟到底看不看得见运动」的前提读数）也接进同一条通道 ——
  它们原来只走 stdout，也就是三条腿里已知会整块丢的那条。刀 M874 把壳换回裸 stdout
  ⇒ Swift 守卫红「捕获/动效卷里有 1 行读数只走 stdout」，CAUGHT=@KC@/@KN@、RESTORE_CLEAN=@KREST@。
- **U-@UB@：覆盖率第一次不是形容词，是一个双向棘轮的数；名册的合法取值改成「派生集」。**
  新卷 `scripts/tests/test_readings_channel_coverage.py`（5 格，进脚本电池）现读：
  扫描 **@FILES@** 份判据 Swift 文件、其中 **@EMITTERS@** 份在用文件通道、
  代码里裸 stdout 读数 **@BARE@** 行 = 登记值 @CEIL@。名册由手挑的 3 个名字扩成
  **@ROSTER@** 个（= 派生集：用了 `emit(` 且代码里零裸 stdout 的文件），
  两个方向各一格断言：干净的发射器没进名册 ⇒ 红「未纳管」，名册里的名字已经不干净 ⇒ 红「已过期」。
  **未覆盖是有名字的名单**：@UNCOVFILES@ 份文件共 @UNCOSUM@ 行，最大一处 `@WORSTFILE@` @WORSTN@ 行。
  棘轮为什么要有**下界**：只压上界的地板在有人修好一批之后会静默过期 —— 登记值仍 57、盘上已 40，
  于是下一行新违规照样绿。刀 M872 往名册内的一份文件贴一行裸 stdout ⇒ 红「盘上有 58 行」；
  刀 M873 把名册改短一个名字 ⇒ 红「未纳管=FrameIntervalBudgetTests.swift」，
  **而这一格 Swift 侧是瞎的**（守卫只扫名册里还写着的那些文件）——
  这就是「把名册改短」必须由第三方来看的理由，也是 @DN@ 的下半句。
- **U-@UC@：本轮我自己写的两样东西，各自坏了一次，都是当场被仪器抓住的（记下来是因为形状新）。**
  ① R301 的刀 M871 的 needle 写的是**上一版名册的字面量**；本轮把名册从 3 个名字扩到 @ROSTER@ 个，
  needle 命中 0 次 ⇒ 预检当场 `bad=1（M871 命中=0）`。不改的话这张表会一路报绿，
  而那一把刀其实从未跑过（DID-NOT-RUN 不是通过，D-234 同一族）—— 已把 needle 重钉到当前形状并重跑，
  `R301_MUTATE 刀=2 CAUGHT=2`。② 新刀表第一版按**单行正则**抓「哪一格红了」
  （`test_x (模块) ... FAIL`），而 `unittest -v` 会把格子的 docstring 打在头行、把 `... FAIL` 落在另一行
  ⇒ 明明红了 2 格却报成 `WRONG_CELL`（假阴性那一侧）。R277 记过同一个形状，我照样踩了一遍；
  修法是「头行 + 结果行」配对，与 `test_skip_roster` 用同一个估计量。

本轮产品文件 0 个（Tests / scripts / .scratch），连续零改动 **@STREAK@** 轮
（现读 `python3 scripts/product_streak.py --streak-for @ROUND@`：as-of 第 @ROUND@ 轮的最后一笔产品提交是
@LASTSHA@ = 第 @LASTROUND@ 轮，也就是 @PREV@ 之前那轮（R300）的代码半；R300 动了 2 个文件把纪录归零，
之后 @PREV@ 与本轮都只动判据 ⇒ 从 0 开始又数了两轮）。
四件套现读：全量卷 @SWIFT@ 用例 / 失败 @SWFAIL@、build 告警 @WARN@、帧 @FRAMES@ 张 compared=@CM@ changed=@CH@、
dmg=@Dmg@、换装 @VER@；预检 ARM_TOTAL=@ARMS@ bad=0。
看图腿：本轮没有新帧（产品 0 文件，changed=0 ⇒ 沿用 @PREV@ 那批基线），读的是**画面之外的两个数** ——
覆盖率那卷自印的 @BARE@ 行未覆盖清单，与四件套取证目录里的读数行数（见下一条）。
359 本轮重量一次：四件套目录 @VLINES@ 行读数里热图 marker 仍是 **@VHEAT@ 行** ⇒ 那格没被顺手修掉，仍开。

'''
t = block(u'UI_NEW', UI)

ITER = u'''
## Round @RDN@ · @RTAG@（第 @ROUND@ 轮 · @TODAY@）：两份实现合成一份，覆盖率从形容词变成棘轮

本轮做的事：结掉 358（`MotionFilmstripTests` 自己那份读数落盘删成一层壳，另加两处
`NATIVE_PROBE_STATE` 接进同一条通道），把「零裸 stdout」的名册从手挑的 3 个名字改成**派生集**（@ROSTER@ 个），
并新建 `scripts/tests/test_readings_channel_coverage.py`（5 格）把覆盖率钉成一个**双向棘轮**的数：
盘上裸 stdout 读数 = 登记值，变多变少都红；名册 = 派生集，两个方向都红。
三把刀 M872 / M873 / M874 全 CAUGHT，另把 R301 被本轮改动弄哑的 M871 重钉并重跑（2/2 CAUGHT）。
产品文件 0 个 —— 产物是一条被锤过的通道、一个能复查的覆盖率数、一份有名字的未覆盖清单。

七维度自评：
| 维度 | 分/满分 |
| --- | --- |
@ROWS@| 合计 | @TOTAL@/105 |

为什么不是满分（逐条）：真实视觉审查 11 —— 本轮没有新帧，看的是文件里的行数与清单，
不是新的画面证据；产品面推进 4 —— 0 个产品文件、连续 @STREAK@ 轮（这一维已经连着十几轮低分，
它欠的是 347 那条真机证人，而那道门在用户那边）；判据有效性 14 —— 覆盖率那卷五格各自能被打红，
三把刀 + 一把重钉；假绿防御 14 —— 名册改短这件事 Swift 侧看不见，本轮第一次有第三方能看见；
台账一致性 13 —— 覆盖率数由那一卷自印的结论行现读，`READINGS_COVERAGE` 里 bare 与 ceiling 不等就拒绝落账；
交付诚实性 14 —— 359 本轮重量（四件套目录热图 marker 仍 @VHEAT@ 行），没把「上一轮量过」当成「已经修好」；
可复核性 14 —— 未覆盖到**文件**粒度登记（@UNCOVFILES@ 份 / @UNCOSUM@ 行），最大一处 @WORSTFILE@ @WORSTN@ 行。

派生分由 `curve_from_ledger.py` 现读，不手抄。
未做（逐条）：① **305 的台阶地板**（等 347 的真机证人 —— 要用户退出 App 或回答一句）；
② 354 的第二步（动效地板登记成按机器×按用例切片的有名字未覆盖；出现率已量到 @APPEAR@）；
③ @BLO@（把剩下 @UNCOSUM@ 行裸 stdout 读数按文件搬进通道，每搬一份就把棘轮的登记值降下来）；
④ 359（一轮的证据目录没有读数汇聚点）；⑤ 348 的两格、349、350 第二步、351、344、341 的 CI 契约半、
339、312 具名出口、304、291；⑥ 用户闸门 220 路 A / 228② / 265。

'''
t = block(u'ITER_NEW', ITER)

DEC = u'''
**D-283（@RTAG@）：覆盖率类的登记值必须写成**双向棘轮**（现读等于登记值），名册的合法取值只能由**派生集**给出，
而且这条等式的权威不能放在被它约束的那份守卫里。**
三条都在本轮有读数：
① 只压上界的地板会在「有人修好一批」之后静默过期 —— 登记值 57、盘上 40，下一行新违规照样绿；
   所以 `test_readings_channel_coverage.py` 断的是相等，两个方向都红，
   刀 M872 证明上界有牙（贴一行进去 ⇒ 「盘上有 58 行」）。
② 名册原来是一张手挑名单，手挑的名单可以悄悄变短；派生集 = 「用了 `emit(` 且代码里零裸 stdout 的文件」，
   本轮由 3 个名字抬到 @ROSTER@ 个，未纳管与已过期各一格断言。
③ 「把名册改短」这一种坏法，Swift 侧那条守卫**结构上看不见**（它只遍历名册里还写着的名字），
   所以等式的权威必须放在第三方（脚本电池）：刀 M873 把名册改短一个名字，
   Swift 侧那格仍绿，而新卷红在「未纳管=FrameIntervalBudgetTests.swift」——
   一条只有被约束者自己监督的规矩，等于把规矩交给想破它的人（与 D-282 名册不许空转是同族，
   这次补的是「谁来发现名册变短」）。
'''
t = block(u'DEC_NEW', DEC)

# BACK_357 → CLOSE_358（变量名一起换）
CLOSE = u'''
  追记（@RTAG@ 结案）：本轮把重复的那一份**删掉**，而不是给守卫开白名单。
  `MotionFilmstripTests.emit` 现在只是 `CaptureReadings.emit(line, to: readingsURL)` 的一层壳：
  按 URL 记首次、进程内一把锁、一整行一次 write 这三样从此只有一份实现，而动效卷那 44+ 条读数
  第一次站在被锤过的那条通道上（`testMotionReadingsUseTheFileChannel` 仍在，正负对照未动）。
  同轮把 `TableProbe` 两处 `NATIVE_PROBE_STATE` 也接进来（那是探针「这一趟看不看得见运动」的前提读数，
  原来只走会整块丢的 stdout）。名册因此能扫这个文件：从手挑 3 个名字改成派生集 @ROSTER@ 个，
  并把「名册 = 派生集」与「裸 stdout 行数 = @BARE@」两条接进脚本电池（@UB@ / @DN@）。
  刀 M874（壳换回裸 stdout ⇒ Swift 侧红）与 M872（名册内文件长出一行 ⇒ 电池红）两侧各有牙。

'''
t = block(u'BACK_357', CLOSE)
t = t.replace(u'BACK_357 = u"""', u'CLOSE_358 = u"""')

# ITEM_BLO → 新单 360；ITEM_BLN2 整块删除
ITEM = u'''
**@BLO@. 判据读数还有一多半只走会死的那条通道：本轮现读 @UNCOSUM@ 行裸 stdout 散在 @UNCOVFILES@ 份判据文件里，最大一处 `@WORSTFILE@` @WORSTN@ 行（R302 现读，@DN@ 的另一半）**：
  数出来的形状（不是形容词）：扫描 @FILES@ 份判据 Swift 文件，其中 @EMITTERS@ 份已经在用文件通道；
  代码里（剥掉注释后）仍有 @BARE@ 行写着裸 stdout，登记在 `test_readings_channel_coverage.py` 的
  `NAMED_UNCOVERED` 里，**按文件**给数 —— 这一条是 357 / 358 的续集，不是新开一件同样的事：
  357 修的是「守卫只扫自己那个文件」，358 修的是「同一件事写了两遍」，本单修的是「还有一多半发射器没进通道」。
  为什么不能一次搬完：每搬一份都要重跑那一份的判据（很多是胶片/探针类，跑一次几分钟），
  而把 @BARE@ 一次写成 0 会让棘轮失去**现读同源**这个性质（登记值必须等于盘上的数）。
  做法（一轮搬几份，按最大一处优先）：① 从 `@WORSTFILE@`（@WORSTN@ 行）起，把它里面的裸 stdout
  调用改成 `CaptureReadings.emit`（或该卷自己的 `emit` 壳）；② 同一轮把 `NAMED_UNCOVERED` 与
  `BARE_PRINT_LINE_CEILING` 两个数一起降到现读值，并让棘轮那一格重新相等；
  ③ 搬干净的自动进名册（派生集那一格会把它拉进去，不需要手工加名字）。
  不许的做法：把登记值抬高来「容纳」新增的裸 stdout（那等于把规矩换成现状的抄本），
  或者给某个文件开白名单（R55 的 M276 就是白名单腐烂的样子）。

'''
t = block(u'ITEM_BLO', ITEM)
istart = t.index(u'ITEM_BLN2 = u"""')
istop = t.index(u'"""', istart + len(u'ITEM_BLN2 = u"""') + 3) + 3
t = t[:istart] + t[istop:]

CHG = (u'CHG_NEW = (u"### Improved（@RTAG@ / 第 @ROUND@ 轮 / Round @RDN@ · 读数的两条腿合成一份，覆盖率进电池）\\n\\n"\n'
       u'           u"358 结案：`MotionFilmstripTests` 自己那份读数落盘（裸 stdout + FileHandle 追加 + 共享布尔做首次整份重写）"\n'
       u'           u"删成一层 `CaptureReadings.emit(line, to: readingsURL)` 的壳 —— 被锤过的「按 URL 记首次 + 进程内锁 + 整行一次 write」"\n'
       u'           u"原来只长在 `CaptureReadings` 那一侧，而这份没锁的实现每天在写动效卷的全部读数（R79 / BACKLOG 112 抓过「后写的把前一份整卷抹掉」）。"\n'
       u'           u"`TableProbe` 里两处 `NATIVE_PROBE_STATE` 同轮接进同一通道。名册由手挑 3 个名字改成**派生集**（@ROSTER@ 个），"\n'
       u'           u"新卷 `scripts/tests/test_readings_channel_coverage.py` 5 格把覆盖率钉成**双向棘轮**：现读 @BARE@ 行 = 登记值，"\n'
       u'           u"变多=新写会死的通道、变少=修好了没重登，两种都红；未覆盖 @UNCOVFILES@ 份文件按文件名登记（最大一处 @WORSTFILE@ @WORSTN@ 行）。"\n'
       u'           u"刀 M872 / M873 / M874 全 CAUGHT=@KC@/@KN@、RESTORE_CLEAN=@KREST@；R301 被本轮改动弄哑的 M871 重钉后重跑 2/2 CAUGHT（预检 bad=0、ARM_TOTAL=@ARMS@）。"\n'
       u'           u"新开 @BLO@（剩下的裸 stdout 读数按文件搬进通道）。359 本轮重量：四件套取证目录 @VLINES@ 行读数里热图 marker 仍 @VHEAT@ 行 ⇒ 仍开。"\n'
       u'           u"产品文件 0 个；四件套现读：全量卷 @SWIFT@/失败 @SWFAIL@、告警 @WARN@、帧 @FRAMES@ 张 changed=@CH@、"\n'
       u'           u"dmg=@Dmg@、换装 @VER@；电池 Ran @BATT@ / OK (skipped=@SKIP@)。\\n\\n")')
cstart = t.index(u'CHG_NEW = (')
cstop = t.index(u'\\n\\n")', cstart) + len(u'\\n\\n")')
t = t[:cstart] + CHG + t[cstop:]

STATE = u'''## @RTAG@ 状态（第 @ROUND@ 轮 / Round @RDN@ · @TODAY@）

⓪ 读 CI（@RNEXT@ 的开场取数，只登记不轮询 = R140）：@CI_LINE@
本轮两笔（代码半 + 账半）由 @RNEXT@ 现取。要验的三件事：
① 名册从 3 个名字扩到派生集 @ROSTER@ 个之后，`testCaptureReadingsUseTheFileChannel` 在 runner 上是否**同数**
（它扫的是仓库里的文件，与机器无关；红在「不存在」= 名册与文件树不一致，红在「未纳管/已过期」= 电池那一卷先红）；
② `scripts/tests/test_readings_channel_coverage.py` 那 5 格在 runner 上是否与本机同为 @BARE@（同一棵树同一批文件 ⇒
不同就是接线，不是阈值）；③ STEP[19] 的动效地板若再现 ⇒ 按 354 的②登记成有名字的未覆盖（出现率已量到 @APPEAR@）。

最后更新：@TODAY@（本地 · @RTAG@ / 第 @ROUND@ 轮 / Round @RDN@）：**358 结案 + 覆盖率第一次是一个会红的数** ——
动效卷自己那份「两条腿」的实现删成一层壳（按 URL 记首次与那把锁从此只有一份），两处 `NATIVE_PROBE_STATE` 接进通道；
名册改成派生集（3 → @ROSTER@ 个），新卷 `test_readings_channel_coverage.py` 5 格钉住
「名册 = 派生集（双向）」与「裸 stdout 行数 = @BARE@ = 登记值（双向棘轮）」，
未覆盖 @UNCOVFILES@ 份文件 @UNCOSUM@ 行按文件登记（最大一处 @WORSTFILE@ @WORSTN@ 行）。
刀 M872/M873/M874 全 CAUGHT；R301 的 M871 被本轮名册改动弄哑（needle 命中 0 次，预检 bad=1 当场报），重钉后重跑 2/2。
四件套：全量卷 @SWIFT@/失败 @SWFAIL@、build 告警 @WARN@、帧 @FRAMES@ 张 changed=@CH@、dmg=@Dmg@、换装 @VER@；
预检 ARM_TOTAL=@ARMS@ bad=0；电池 Ran @BATT@ / OK (skipped=@SKIP@)。
产品文件 0 个，连续零改动 **@STREAK@** 轮（现读 `product_streak --streak-for @ROUND@`：
as-of 第 @ROUND@ 轮的最后一笔产品提交是 @LASTSHA@ = 第 @LASTROUND@ 轮，即 R300 的代码半）。

① 下一轮（@RNEXT@）的靶：**354 的第二步** —— 把动效地板那两朵红登记成按机器×按用例切片的
有名字未覆盖（照 155/166/171 那一族：名册要能退场、红话要打印键；出现率已有数 @APPEAR@，
而「覆盖率名单」这一族的形状本轮刚建好，可以直接复用它的对账写法）。
顺带 @BLO@（从 @WORSTFILE@ 那 @WORSTN@ 行开始搬，搬一份就把登记值降到现读）。
产品面：347/305 仍挡在用户那一边（要退出 App 或回答一句「收藏星按下够不够明显」）。

② 仍开：347（真机证人）、305（等 347）、354 的第二步（登记成有名字的未覆盖）、
@BLO@（@UNCOSUM@ 行裸 stdout 按文件搬进通道）、359（取证目录没有读数汇聚点，本轮重量仍是 @VHEAT@ 行）、
356（悬停换形状的三条候选）、348 的两格、349、350 第二步、351、344、341 的 CI 契约半、339、
312 具名出口、333、335、334、310、338 的另一半、328、323、322、317、304、291。

③ 用户闸门：220 路 A / 228② / 265。

'''
t = block(u'STEVE_NEW_PLACEHOLDER', STATE) if False else t
# STATE_NEW 是 u""" 开头且以 """ 结尾（与 UI 同法）
t = block(u'STATE_NEW', STATE)

FRS = [
 (u'FR_WALK', (u'FR_WALK = (u"- **走到哪了**：阶段二累计 `## Round` 节 **@SECTIONS@** 节，最新一节是 **Round @RDN@**；"\n'
              u'           u"自评曲线末四个 @TAIL@ · @RDN@=@TOTAL@（现读 `curve_from_ledger.py` 的 `SCORES_BY_ROUND` 与 `ROUNDS`）。"\n'
              u'           u"派生分连续多轮低于 90 ⇒ 按目标继续修，不收口。\\n")')),
 (u'FR_PRODUCT', (u'FR_PRODUCT = (u"- **产品面（这一节最该被读的部分）**：产品面连续零改动轮数 = **@STREAK@**"\n'
                  u'              u"（唯一取数口 `python3 scripts/product_streak.py --streak-for @ROUND@`：as-of 第 @ROUND@ 轮的"\n'
                  u'              u"最后一笔产品提交是 @LASTSHA@ = 第 @LASTROUND@ 轮，也就是 R300 的代码半（改了 2 个文件，把那条纪录归零）；"\n'
                  u'              u"@PREV@ 与本轮都只动判据与工具 ⇒ 归零之后又数了两轮。真动产品仍是收藏星字形墨那一笔。"\n'
                  u'              u"这一格不许手抄：`--check` 会在台账与派生值不同源时拒绝这一版。\\n")')),
 (u'FR_DOOR', (u'FR_DOOR = (u"- **判据与门的规模**：脚本电池 **Ran @BATT@**（现读 `python3 -m unittest discover -s scripts/tests`）；"\n'
               u'           u"变异臂抽到 **@ARMS@** 把（现读预检 `ARM_TOTAL`，bad=0）；U 定义行 **@UDEF@ 条**、最大 **U-@UC@**"\n'
               u'           u"（`AGENT_UI_AUDIT.md`）；决定最大 **D-@DN@**；BACKLOG 最大 **@BLO@**。"\n'
               u'           u"最近这几轮立/改的门：0 告警能拦（343）、`pillReading` 带窗上界去掉（346）、commit-subject 对账与豁免退场（348）、"\n'
               u'           u"台账区间分箱（350）、产品面轮数只能由 `scripts/product_streak.py` 派生（353）、"\n'
               u'           u"交互标记不许比一次数据变化更响（314 结案，D-281）、判据读数必须有能活下来的通道且名册不许空转（357 结案，D-282）、"\n'
               u'           u"**名册的合法取值是派生集、覆盖率登记值是双向棘轮，且这条等式的权威不能放在被约束的守卫里（358 结案，D-283）**。"\n'
               u'           u"本轮现读：判据文件 @FILES@ 份、用文件通道的 @EMITTERS@ 份、名册 @ROSTER@ 个、"\n'
               u'           u"仍在裸 stdout 的读数 **@BARE@ 行**（= 登记值，@UNCOVFILES@ 份文件按名登记，最大一处 @WORSTFILE@ @WORSTN@ 行）⇒ 新开 @BLO@；"\n'
               u'           u"取证目录那一格本轮重量：四件套目录 @VLINES@ 行读数里热图 marker 仍 **@VHEAT@ 行** ⇒ 359 仍开。\\n")')),
]
for name, new in FRS:
    i = t.index(name + u' = (')
    j = t.index(u'\\n")', i) + len(u'\\n")')
    t = t[:i] + new + t[j:]

# §13 的「仍开」bullet：上一轮插进去的是「358（两份 emit 实现）」，本轮 358 已结案 ⇒ 必须改写而不是再插一次
fstart = t.index(u'fr_still = fr_still.replace(u"348 剩余格、349",')
fstop = t.index(u'% BLO)\n', fstart) + len(u'% BLO)\n')
t = t[:fstart] + (u'fr_still = fr_still.replace(\n'
                  u'    u"358（两份 emit 实现）",\n'
                  u'    u"%d（%s 行裸 stdout 按文件搬进通道）、359（取证目录没有读数汇聚点）" % (BLO, UNCOV_SUM))\n'
                  u'if u"%d（" % BLO not in fr_still:\n'
                  u'    die(u"§13 的仍开 bullet 里没有本轮那一格 ⇒ 上一轮的插入形状漂了，先读再写")\n') + t[fstop:]

# ⓪ 那一行的成对号由环境变量给（避免把没读到的东西写成读到的）
t = t.replace(u'CI_PAIRS = [(u"f5a563a", u"39806766619", u"success"),\n'
              u'            (u"8f6c300", u"39814465153", u"queued/未判")]',
              u'CI_LINE = os.environ.get("R302_CI_LINE", u"CI 通道本轮读到一半就断（`gh run list` ⇒ EOF），'
              u'成对号未读 ⇒ @RNEXT@ 开场第一件事就是重读 ①②③ 那三件事对应的两跑")')
t = t.replace(u'    u"@SECTIONS@": s(int(SECTIONS) + 1), u"@TAIL@": TAIL_OLD,',
              u'    u"@SECTIONS@": s(int(SECTIONS) + 1), u"@TAIL@": TAIL_OLD, u"@CI_LINE@": CI_LINE,')

# `UD` 这个变量本轮不存在（只有三条 U）：任何残留的引用统一收回给 UC，随后由 ast.parse 与形状自测把关
t = t.replace(u's(UD)', u's(UC)')
ast.parse(t)
io.open(DST, 'w', encoding='utf-8').write(t)
bad = [(i, l[:70]) for i, l in enumerate(t.split(u'\n'), 1) if l.count(u'「') != l.count(u'」')]
print('WROTE %s  unbalanced_bracket_lines=%d %s' % (DST, len(bad), bad[:4]))
