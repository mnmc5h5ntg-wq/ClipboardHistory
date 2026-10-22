#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把 ledgers_r303.py 变成 ledgers_r304.py：脚手架不动，只换轮次号、取数口、刀表与正文。

R303 学到的两条生成器规矩（都写在这里）：
· 锚点只用**全文唯一**的字面串，不许按行号做手术（上一轮按行号替换把相邻的 re.sub 一起切掉了）；
· `block()` 直接 lstrip 掉正文开头的换行 —— 标题那一行必须是第一节的第一行（round_batch 的前缀检查靠它）。
"""
import ast
import io
import re

SRC = '.scratch/motion-audit-2/ledgers_r303.py'
DST = '.scratch/motion-audit-2/ledgers_r304.py'
t = io.open(SRC, encoding='utf-8').read()

MECH = [
    (u'"""R303（第 302 轮 / Round 300）的七本台账落盘 —— 事务性，与 ledgers_r302 同一形状。',
     u'"""R304（第 303 轮 / Round 301）的七本台账落盘 —— 事务性，与 ledgers_r303 同一形状。'),
    (u'本轮**不动产品**（只动 Tests / scripts / .scratch），所以 streak 由取数口按 as-of 第 302 轮现读（=3），',
     u'本轮**不动产品**（只动 Tests / scripts / .scratch），所以 streak 由取数口按 as-of 第 303 轮现读（=4），'),
    (u'VERIFY_LOG = "/tmp/r303_verify_run.log"', u'VERIFY_LOG = "/tmp/r304_verify_run.log"'),
    (u'VERIFY_READINGS = "/tmp/r303_verify/frames/capture-readings.log"',
     u'VERIFY_READINGS = "/tmp/r304_verify/frames/capture-readings.log"'),
    (u'KNIVES = os.path.join(ROOT, ".scratch", "motion-audit-2", "mutate_r303.py")',
     u'KNIVES = os.path.join(ROOT, ".scratch", "motion-audit-2", "mutate_r304.py")\n'
     u'KNIVES_R303 = os.path.join(ROOT, ".scratch", "motion-audit-2", "mutate_r303.py")'),
    (u'for tag, path in ((u"r195", KNIVES_195), (u"r196", KNIVES_196)):',
     u'for tag, path in ((u"r195", KNIVES_195), (u"r196", KNIVES_196), (u"r303", KNIVES_R303)):'),
    (u'    die(u"历史刀表 %s 重钉之后仍不干净（rc=%s）：%s" % (tag, hrc, hout.strip()[-300:]))',
     u'    die(u"历史刀表 %s 本轮之后仍不干净（rc=%s）：%s" % (tag, hrc, hout.strip()[-300:]))'),
    (u'R_TAG = u"R303"\nR_NEXT = u"R304"\nPREV_TAG = u"R302"',
     u'R_TAG = u"R304"\nR_NEXT = u"R305"\nPREV_TAG = u"R303"'),
    (u'LEDGERS_R303 REFUSED', u'LEDGERS_R304 REFUSED'),
    (u'u"(?m)^R303_MUTATE 刀=', u'u"(?m)^R304_MUTATE 刀='),
    (u'/tmp/r303_battery_pre.log', u'/tmp/r304_battery_pre.log'),
    (u'/tmp/r303_battery_post.log', u'/tmp/r304_battery_post.log'),
    (u'u"LEDGERS_R303 OK batt=Ran ', u'u"LEDGERS_R304 OK batt=Ran '),
    (u'if LAST_ROUND != s(ROUND - 3):', u'if LAST_ROUND != s(ROUND - 4):'),
    (u'⇒ 与本轮（第 %d 轮）差三格，先查', u'⇒ 与本轮（第 %d 轮）差四格，先查'),
    (u'if (U_MAX, D_MAX, BL_MAX) != (991, 283, 360):', u'if (U_MAX, D_MAX, BL_MAX) != (994, 284, 361):'),
    (u'SUBS2[u"@UDEF@"] = s(U_DEFS + 3)', u'SUBS2[u"@UDEF@"] = s(U_DEFS + 3)'),
    (u'R303_CI_LINE', u'R304_CI_LINE'),
    (u'startswith(u"**360. ")', u'startswith(u"**361. ")'),
    (u'die(u"360 锚点异常（%d 处）" % len(h357))', u'die(u"361 锚点异常（%d 处）" % len(h357))'),
    (u'if u"追记（%s 第一步）" % R_TAG in orig["BL"]:', u'if u"追记（%s）" % R_TAG in orig["BL"]:'),
    (u'die(u"360 已有 %s 的同轮追记" % R_TAG)', u'die(u"361 已有 %s 的同轮追记" % R_TAG)'),
    (u'    u"@SECTIONS@": s(int(SECTIONS) + 1), u"@TAIL@": TAIL_OLD, u"@CI_LINE@": CI_LINE,',
     u'    u"@SECTIONS@": s(int(SECTIONS) + 1), u"@TAIL@": TAIL_OLD, u"@CI_LINE@": CI_LINE,\n'
     u'    u"@TOUCHES@": TOUCHES, u"@NAMED@": s(NAMED_LEFT),'),
]
for a, b in MECH:
    n = t.count(a)
    if n != 1:
        raise SystemExit(u'MECH anchor count=%d: %r' % (n, a[:90]))
    t = t.replace(a, b)

# ── 本轮新增的测量：一次搬动到底要手工同步几处（数出来，不形容词）──────────
anchor = u'# 结构读数（本轮量，不猜）'
assert t.count(anchor) == 0 or True
ins_anchor = u'if not os.path.exists(VERIFY_READINGS):'
assert t.count(ins_anchor) == 1
TOUCH = (
u'# 一次「把读数搬进文件通道」要动几处？本轮把这件事数出来（R303 开的 361 的具体尺寸）。\n'
u'TESTS_DIR = os.path.join(ROOT, "ClipboardHistory", "Tests", "ClipboardHistoryAppTests")\n'
u'MOVED = ["MotionDriverTests.swift", "PressFeedbackTests.swift", "SettingsFailureReceiptTests.swift"]\n'
u'emitted = 0\n'
u'for name in MOVED:\n'
u'    emitted += rd(os.path.join(TESTS_DIR, name)).count(u"CaptureReadings.emit(")\n'
u'cov_src = rd(os.path.join(ROOT, "scripts", "tests", "test_readings_channel_coverage.py"))\n'
u'NAMED_LEFT = len(re.findall(u\'^\\\\s+"[\\\\w.]+[.]swift": \\\\d+\', cov_src, re.M))\n'
u'roster_src = rd(FILES["UI"]) if False else rd(os.path.join(TESTS_DIR, "UICaptureHarness.swift"))\n'
u'CH_ROSTER = len(re.findall(u\'"[\\\\w.]+[.]swift"\', roster_src[roster_src.index(u\'let roster = [\'):roster_src.index(u\']\\n\', roster_src.index(u\'let roster = [\'))]))\n'
u'ch_src = rd(os.path.join(TESTS_DIR, "FrameIntervalBudgetTests.swift"))\n'
u'CH_CHANNEL = len(re.findall(u\'"[\\\\w.]+[.]swift"\', ch_src[ch_src.index(u\'let emitChannel: Set<String> = [\'):ch_src.index(u\']\\n\', ch_src.index(u\'let emitChannel: Set<String> = [\'))]))\n'
u'TOUCHES = (u\'搬动本身 %d 处调用 + 名册 2 张（Swift 通道名册 %d 个名字、Swift 名字名册的 emitChannel %d 个名字）\'\n'
u'           u\'+ 电池那一卷的登记值 1 处与按文件未覆盖名单 %d 条\'\n'
u'           % (emitted, CH_ROSTER, CH_CHANNEL, NAMED_LEFT))\n'
u'if emitted < 10 or CH_ROSTER < 12 or CH_CHANNEL < 3:\n'
u'    die(u"同步点的数读不出合理形状（emitted=%s roster=%s channel=%s）⇒ 有几处漂了，先读再写"\n'
u'        % (emitted, CH_ROSTER, CH_CHANNEL))\n')
t = t.replace(ins_anchor, TOUCH + ins_anchor)

def block(name, new):
    """整块替换 NAME = u\"\"\"…\"\"\"。只 lstrip：正文**结尾**的空行必须留着 ——
    把它 strip 掉会让新节与下一节的标题粘成一行（R304 试过，round_batch 与区间对账两格同时红）。"""
    global t
    head = name + u' = u"""'
    i = t.index(head)
    j = t.index(u'"""', i + len(head) + 3) + 3
    t = t[:i] + head + new.lstrip(u'\n') + u'"""' + t[j:]

UI = u'''
## 第 @ROUND@ 轮（@RTAG@ · U-@UA@…U-@UC@ · @TODAY@）：第二批裸 stdout 搬完，顺手把「一次搬动要同步几处」数出来

- **U-@UA@：360 的第二批 —— 又搬掉三份判据卷的 13 行，覆盖率棘轮 42 → 现读 @BARE@。**
  搬的是 `MotionDriverTests`（3：`RECEIPT_DRIVE` / `DERIVED_KEY_EXPANSION` / `BANNER_DRIVE`）、
  `PressFeedbackTests`（5：`PRESS_AXIS` / `FILL_STEP`）、`SettingsFailureReceiptTests`
  （5：`FEEDBACK_EXPORT_RECEIPT_TRUTH_TABLE` / `EXPORT_FEEDBACK_CHANNEL` / `ARCHIVE_TRANSFER_RECEIPT`
  / `ARCHIVE_ACTION_CHANNEL` / `RECEIPT_FIXTURE_COPY`）—— 都是历轮写进过台账的数（按下台阶、
  回执真值表、驱动调用点）。派生名册由 11 抬到 @ROSTER@ 个（这三份搬完就干净了 ⇒ 不进名册就红「未纳管」），
  按文件的未覆盖名单剩 @NAMED@ 条 / @BARE@ 行。两把新刀：M879 把 `BANNER_DRIVE` 那一行改回裸 stdout
  ⇒ 红「盘上有 30 行」；M878 把 `MotionDriverTests.swift` 从下面那张通道表里删掉 ⇒
  Swift 侧名字名册红「与名册不符」。刀表 @KC@/@KN@ 全 CAUGHT、RESTORE_CLEAN=@KREST@。
- **U-@UB@：本轮新增的那处账是**通道表**，不是第四张名单 —— 它是 R303 那格教训的制度化。**
  `FrameIntervalBudgetTests` 的名字名册原来靠 `file == "UIInteractionProbeTests.swift"` 判断走哪条腿；
  第二批搬完，那种单文件特例就会变成"漏一个文件 = 那份清单凭空消失而守卫仍绿"。
  现在是一张显式 `emitChannel` 名单，M878 钉的正是「从名单里删一个名字」这件事必须红。
  历史刀表也被本轮改动弄哑过一次：`R303` 的 M875/M876/M877 三根 needle 里，前两根的期望值写的是
  **上一轮的数字**（43 / 42），名册形状也变了 ⇒ 预检 `bad=2`、表里 ESCAPED=1。重钉之后
  `R303_MUTATE 刀=3 CAUGHT=3`、`R195/R196` 各自全 CAUGHT、预检 bad=0、ARM_TOTAL=@ARMS@。
  这正是 D-284 第二条说的事：改判据代码的那一轮必须跑预检，并把「命中 0 次 / 期望值过期」当本轮产出。
- **U-@UC@：361 被本轮量成了具体的数字 —— 一次搬动要同步 @TOUCH@。**
  也就是说「谁还在走会死的通道」这句话现在由**四处**各自记一份：判据源码的调用、Swift 通道名册、
  Swift 名字名册的通道表、电池那一卷的登记值与按文件名单。四处都对，但没有一处是另一处的上游 ⇒
  漏同步只会以「某一格红」或更糟的「某一格静默变空」出现。本轮把 361 的追记写成这个尺寸，
  并给下一步定了形状：**先把「同步点数量」变成读数**（就是 @TOUCH@ 这句），再谈合并成一份数据。

本轮产品文件 0 个（Tests / scripts / .scratch），连续零改动 **@STREAK@** 轮
（现读 `python3 scripts/product_streak.py --streak-for @ROUND@`：as-of 第 @ROUND@ 轮的最后一笔产品提交是
@LASTSHA@ = 第 @LASTROUND@ 轮，即 R300 的代码半）。四件套现读：全量卷 @SWIFT@ / 失败 @SWFAIL@、
build 告警 @WARN@、帧 @FRAMES@ 张 compared=@CM@ changed=@CH@、dmg=@Dmg@、换装 @VER@。
看图腿：本轮无新帧（产品 0 文件），读的是通道与名单的数；四件套取证目录 @VLINES@ 行里热图 marker
仍 @VHEAT@ 行 ⇒ 359 仍开（重量，不沿用）。

'''
block(u'UI_NEW', UI)

ITER = u'''
## Round @RDN@ · @RTAG@（第 @ROUND@ 轮 · @TODAY@）：第二批搬进文件通道，同步点第一次被数出来

本轮做的事：把 `MotionDriverTests` / `PressFeedbackTests` / `SettingsFailureReceiptTests` 三份里
13 行只走 stdout 的读数改走 `CaptureReadings.emit`，覆盖率棘轮 42 → 现读 @BARE@，
派生名册 11 → @ROSTER@ 个；给 Swift 那张名字名册补一张**显式通道表**（`emitChannel`），
因为上一轮的「单文件特例」在多搬一份之后就会变成静默失效的洞。
两把新刀 M878 / M879 分别钉「通道表被删名字」与「搬好的读数被写回 print」。
本轮又踩并当场修好的：`R303` 的三根 needle 有两根的期望值是上一轮的数字（42 / 43）、
名册形状也随本轮变化 ⇒ 预检 bad=2、表里 ESCAPED=1 ⇒ 重钉后三张表全 CAUGHT。

七维度自评：
| 维度 | 分/满分 |
| --- | --- |
@ROWS@| 合计 | @TOTAL@/105 |

为什么不是满分（逐条）：真实视觉审查 11 —— 无新帧，读的是名单与行数；产品面推进 4 —— 0 个产品文件、
连续 @STREAK@ 轮（这一维欠的是 347 的真机证人，门在用户那边）；判据有效性 14 —— 两把新刀各钉一侧，
外加三根被本轮弄哑又复活的针；假绿防御 14 —— 通道表从「一个 if」变成一张名单，删名字会红；
台账一致性 13 —— 棘轮 / 名单 / 通道表三个数全部现读，同步点数量本身也现读成 @TOUCH@；
交付诚实性 14 —— 359 与「哪几跑 CI 未读」都重量而不沿用；可复核性 14 —— 361 从一句抱怨变成可数的尺寸。

派生分由 `curve_from_ledger.py` 现读，不手抄。
未做（逐条）：① **305 的台阶地板**（等 347 的真机证人）；② 354 的第二步（动效地板登记成按机器×按用例的
有名字未覆盖，出现率 @APPEAR@）；③ 361（同步点已被数出来，合并成一处派生还没做）；④ 360 剩下的
@NAMED@ 份文件 @BARE@ 行；⑤ 359（取证目录没有汇聚点）；⑥ 348 的两格、349、350 第二步、351、344、
341 的 CI 契约半、339、312 具名出口、304、291；⑦ 用户闸门 220 路 A / 228② / 265。

'''
block(u'ITER_NEW', ITER)

DEC = u'''
**D-285（@RTAG@）：一次「把读数搬进文件通道」要同步的地点数量，必须是本轮读出来的数字，并且每一处都要有刀。**
理由与尺寸：R303 立的是「名单要登记名字而不是通道」，本轮把它落成一张显式 `emitChannel` 名单；
而这次搬迁实测的同步点是 @TOUCH@（判据源码的调用、Swift 通道名册、Swift 名字名册的通道表、
电池那一卷的登记值与按文件未覆盖名单）。任何一处单独忘记都有两种收场：某一格红（可接受），
或者**那份清单凭空变空而守卫仍绿**（不可接受 —— R303 的 M731 就是这个形状被刀照出来的）。
所以处置固定为三步：① 每搬一份就在同一轮改登记值，让棘轮现读等于登记值；
② 通道表加名字，并配一把「从表里删名字」的刀（M878）；③ 跑预检，把「needle 命中 0 次 / 期望值是上一轮的数字」
当成本轮产出重钉后重跑（本轮 `R303` 的三根里两根正是这种坏法）。
'''
block(u'DEC_NEW', DEC)

NOTE = u'''
  追记（@RTAG@）：361 那句「三张名单并存」在本轮被量成具体尺寸 —— 搬一份判据卷的读数要同步 @TOUCH@。
  本轮把这四处都改了并各配刀（M879 钉「登记值/名单」那一侧，M878 钉「Swift 通道表」那一侧），
  但这只是把漏同步变成「会红」，还没变成「只有一处要改」。
  下一步的顺序因此定下来：先把同步点数量做成读数（@TOUCH@ 就是它），再谈合并成一份上游数据。
  另：本轮把 `R303_MUTATE` 的三根 needle 重钉了一遍 —— 其中两根的期望值写的是**上一轮的数字**，
  这就是「放宽要成对」之外另一种腐烂：刀表的期望值也是台账，也要现读。

'''
cstart = t.index(u'NOTE_360 = u"""')
cstop = t.index(u'"""', cstart + len(u'NOTE_360 = u"""')) + 3
t = t[:cstart] + u'NOTE_360 = u"""' + NOTE.strip(u'\n') + u'\n"""' + t[cstop:]

ITEM = u''
istart = t.index(u'ITEM_BLO = u"""')
istop = t.index(u'"""', istart + len(u'ITEM_BLO = u"""')) + 3
t = t[:istart] + u'ITEM_BLO = u"""' + ITEM + u'"""' + t[istop:]
t = t.replace(u'for n in (BLO,):', u'for n in ():')

CHG = (u'CHG_NEW = (u"### Improved（@RTAG@ / 第 @ROUND@ 轮 / Round @RDN@ · 第二批裸 stdout 搬进文件通道）\\n\\n"\n'
       u'           u"360 的第二批：`MotionDriverTests`（3 行）、`PressFeedbackTests`（5 行）、`SettingsFailureReceiptTests`（5 行）"\n'
       u'           u"里的读数改走 `CaptureReadings.emit`，覆盖率棘轮 42 → 现读 @BARE@，派生名册 11 → @ROSTER@ 个，"\n'
       u'           u"按文件的未覆盖名单剩 @NAMED@ 条。Swift 那张名字名册补一张**显式通道表** `emitChannel`："\n'
       u'           u"上一轮靠 `file == 某一份` 判断走哪条腿，多搬一份之后那种特例就会让清单凭空变空而守卫仍绿。"\n'
       u'           u"两把新刀：M878 从通道表里删一个名字 ⇒ Swift 侧红在与名册不符；M879 把一行改回裸 stdout ⇒ 电池红在盘上有 30 行。"\n'
       u'           u"同轮把 `R303_MUTATE` 三根 needle 重钉（两根的期望值写的是上一轮的数字 42 / 43，预检 bad=2）⇒ 三张表全 CAUGHT，"\n'
       u'           u"预检 bad=0、ARM_TOTAL=@ARMS@。给 361 补一条实测尺寸：一次搬动要同步 @TOUCH@。"\n'
       u'           u"359 重量：四件套取证目录 @VLINES@ 行里热图 marker 仍 @VHEAT@ 行 ⇒ 仍开。"\n'
       u'           u"产品文件 0 个；四件套现读：全量卷 @SWIFT@/失败 @SWFAIL@、告警 @WARN@、帧 @FRAMES@ 张 changed=@CH@、"\n'
       u'           u"dmg=@Dmg@、换装 @VER@；电池 Ran @BATT@ / OK (skipped=@SKIP@)。\\n\\n")')
cstart = t.index(u'CHG_NEW = (')
cstop = t.index(u'\\n\\n")', cstart) + len(u'\\n\\n")')
t = t[:cstart] + CHG + t[cstop:]

STATE = u'''## @RTAG@ 状态（第 @ROUND@ 轮 / Round @RDN@ · @TODAY@）

⓪ 读 CI（@RNEXT@ 的开场取数，只登记不轮询 = R140）：@CI_LINE@
要验的四件事：① @PREV@ 两笔（`b420967` / `811c4fc`）与本轮两笔的成对号；
② 派生名册抬到 @ROSTER@ 个之后，`testCaptureReadingsUseTheFileChannel` 在 runner 上是否与本机同数
（同一棵树同一批文件 ⇒ 不同就是接线）；③ `test_readings_channel_coverage` 那 6 格在 runner 上的
裸 stdout 计数是否同为 @BARE@、Swift 名字名册的 total 是否同为 @SWTOT@；④ STEP[19] 若再现 ⇒
按 354 的②登记成有名字的未覆盖（出现率已量到 @APPEAR@）。

最后更新：@TODAY@（本地 · @RTAG@ / 第 @ROUND@ 轮 / Round @RDN@）：**360 第二批搬完 + 同步点第一次被数出来** ——
三份判据卷共 13 行改走 `CaptureReadings.emit`，棘轮 42 → 现读 @BARE@，派生名册 11 → @ROSTER@，
Swift 名字名册新增显式 `emitChannel` 表（M878 钉「从表里删名字」，M879 钉「写回 print」，两把都 CAUGHT）。
361 从抱怨变成尺寸：一次搬动要同步 @TOUCH@ ⇒ D-285 把「每一处都要有刀 + 登记值现读等于盘上」定成规矩。
本轮又当场修一次自己的腐烂：`R303_MUTATE` 三根 needle 里两根的期望值是上一轮的数字（预检 bad=2、ESCAPED=1），
重钉后 R303 / R195 / R196 三张表全 CAUGHT、预检 bad=0、ARM_TOTAL=@ARMS@。
四件套：全量卷 @SWIFT@/失败 @SWFAIL@、build 告警 @WARN@、帧 @FRAMES@ 张 changed=@CH@、dmg=@Dmg@、换装 @VER@；
电池 Ran @BATT@ / OK (skipped=@SKIP@)；353 的门绿（streak 两格同源）。
产品文件 0 个，连续零改动 **@STREAK@** 轮（现读 `python3 scripts/product_streak.py --streak-for @ROUND@`：
as-of 第 @ROUND@ 轮的最后一笔产品提交是 @LASTSHA@ = 第 @LASTROUND@ 轮，即 R300 的代码半）。

① 下一轮（@RNEXT@）的靶：**354 的第二步** —— 动效地板那两朵红登记成按机器×按用例切片的有名字未覆盖
（出现率 @APPEAR@；名册要能退场、红话要打印键；对账形状复用本轮的派生名册）。
顺带 360 的第三批（从 `OffscreenSymbolInkProbeTests` 的 3 行与 `WindowChromeLayoutTests` 的 3 行起，
搬完把登记值降到现读）与 361（先让同步点数量成为读数，再谈合并）。
产品面：347/305 仍挡在用户那一边（要退出 App 或回答一句「收藏星按下够不够明显」）。

② 仍开：347（真机证人）、305（等 347）、354 的第二步（登记成有名字的未覆盖）、
360（已搬两批，剩 @NAMED@ 份文件 @BARE@ 行）、361（同步点已数出，尚未合并）、
359（取证目录没有读数汇聚点，本轮重量仍是 @VHEAT@ 行）、356（悬停换形状的三条候选）、348 的两格、
349、350 第二步、351、344、341 的 CI 契约半、339、312 具名出口、333、335、334、310、
338 的另一半、328、323、322、317、304、291。

③ 用户闸门：220 路 A / 228② / 265。

'''
block(u'STATE_NEW', STATE)

FRS = [
 (u'FR_WALK', (u'FR_WALK = (u"- **走到哪了**：阶段二累计 `## Round` 节 **@SECTIONS@** 节，最新一节是 **Round @RDN@**；"\n'
              u'           u"自评曲线末四个 @TAIL@ · @RDN@=@TOTAL@（现读 `curve_from_ledger.py` 的 `SCORES_BY_ROUND` 与 `ROUNDS`）。"\n'
              u'           u"派生分连续多轮低于 90 ⇒ 按目标继续修，不收口。\\n")')),
 (u'FR_PRODUCT', (u'FR_PRODUCT = (u"- **产品面（这一节最该被读的部分）**：产品面连续零改动轮数 = **@STREAK@**"\n'
                  u'              u"（唯一取数口 `python3 scripts/product_streak.py --streak-for @ROUND@`：as-of 第 @ROUND@ 轮的"\n'
                  u'              u"最后一笔产品提交是 @LASTSHA@ = 第 @LASTROUND@ 轮 = R300 的代码半（悬停环 0.55→0.30、梯子顶档 0.85→0.92）；"\n'
                  u'              u"之后 R301 / R302 / R303 / 本轮都只动判据与工具。这一格不许手抄，`--check` 会拒绝不同源的版本。\\n")')),
 (u'FR_DOOR', (u'FR_DOOR = (u"- **判据与门的规模**：脚本电池 **Ran @BATT@**（现读 `python3 -m unittest discover -s scripts/tests`）；"\n'
               u'           u"变异臂抽到 **@ARMS@** 把（现读预检 `ARM_TOTAL`，bad=0）；U 定义行 **@UDEF@ 条**、最大 **U-@UC@**"\n'
               u'           u"（`AGENT_UI_AUDIT.md`）；决定最大 **D-@DN@**；BACKLOG 最大 **361**。"\n'
               u'           u"最近这几轮立/改的门：0 告警能拦（343）、带窗上界去掉（346）、commit-subject 对账与豁免退场（348）、"\n'
               u'           u"台账区间分箱（350）、产品面轮数只能由 git 派生（353）、交互标记不许比一次数据变化更响（314/D-281）、"\n'
               u'           u"读数必须有能活下来的通道（357/D-282）、名册取值是派生集且棘轮双向（358/D-283）、"\n'
               u'           u"名册登记名字不登记通道（360 第一批/D-284）、**一次搬动的同步点数量要现读且每处配刀（D-285）**。"\n'
               u'           u"本轮现读：判据文件 @FILES@ 份、用文件通道的 @EMITTERS@ 份、名册 @ROSTER@ 个、"\n'
               u'           u"仍在裸 stdout 的读数 **@BARE@ 行**（= 登记值；两批之前是 57）；Swift 名字名册合计 @SWTOT@ 行、"\n'
               u'           u"通道表 @TOUCH@。取证目录本轮重量：@VLINES@ 行里热图 marker 仍 **@VHEAT@ 行** ⇒ 359 仍开。\\n")')),
]
for name, new in FRS:
    i = t.index(name + u' = (')
    j = t.index(u'\\n")', i) + len(u'\\n")')
    t = t[:i] + new + t[j:]

t = t.replace(u'fr_still = fr_still.replace(\n    u"UIInteractionProbeTests.swift",\n',
              u'fr_still = fr_still.replace(\n    u"UIInteractionProbeTests.swift",\n') if False else t
old_still = (u'fr_still = fr_still.replace(\n'
             u'    u"360（57 行裸 stdout 按文件搬进通道）",\n'
             u'    u"360（第一步已做，剩 %s 行）、%d（三张名单并存，缺一处上游）" % (BARE, BLO))')
new_still = (u'fr_still = fr_still.replace(\n'
             u'    u"360（第一步已做，剩 42 行）、361（三张名单并存，缺一处上游）",\n'
             u'    u"360（已搬两批，剩 %s 行）、361（同步点已数出，尚未合并）" % BARE)')
if old_still in t:
    t = t.replace(old_still, new_still)
else:
    raise SystemExit(u'§13 仍开 bullet 的锚点不匹配：先读现文再改，不许静默跳过')
t = t.replace(u'if u"%d（三张名单并存" % BLO not in fr_still or u"357（判据读数的本地通道）" in fr_still:',
              u'if u"360（已搬两批" not in fr_still:')
t = t.replace(u'    die(u"§13 的仍开 bullet 没落到本轮的形状（缺 361，或 357 的过期条目没清）")',
              u'    die(u"§13 的仍开 bullet 没落到本轮的形状（360 的尺寸没更新）")')
t = t.replace(u'u"本轮现读：判据文件 @FILES@', u'u"本轮现读：判据文件 @FILES@')

ast.parse(t)
io.open(DST, 'w', encoding='utf-8').write(t)
bad = [(i, l[:70]) for i, l in enumerate(t.split(u'\n'), 1) if l.count(u'「') != l.count(u'」')]
print('WROTE %s unbalanced=%d %s' % (DST, len(bad), bad[:3]))
