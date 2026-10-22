#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把 ledgers_r302.py 变成 ledgers_r303.py —— 脚手架不动，只换轮次号、取数口、刀表与正文。"""
import ast
import io

SRC = '.scratch/motion-audit-2/ledgers_r302.py'
DST = '.scratch/motion-audit-2/ledgers_r303.py'
t = io.open(SRC, encoding='utf-8').read()

MECH = [
    (u'"""R302（第 301 轮 / Round 299）的七本台账落盘 —— 事务性，与 ledgers_r301 同一形状。',
     u'"""R303（第 302 轮 / Round 300）的七本台账落盘 —— 事务性，与 ledgers_r302 同一形状。'),
    (u'本轮**不动产品**（只动 Tests / scripts / .scratch），所以 streak 由取数口按 as-of 第 301 轮现读（=2），',
     u'本轮**不动产品**（只动 Tests / scripts / .scratch），所以 streak 由取数口按 as-of 第 302 轮现读（=3），'),
    (u'VERIFY_LOG = "/tmp/r302_verify_run.log"', u'VERIFY_LOG = "/tmp/r303_verify_run.log"'),
    (u'VERIFY_READINGS = "/tmp/r302_verify/frames/capture-readings.log"',
     u'VERIFY_READINGS = "/tmp/r303_verify/frames/capture-readings.log"\n'
     u'SWIFT_ROSTER = os.path.join(ROOT, "ClipboardHistory", "Tests", "ClipboardHistoryAppTests",\n'
     u'                               "FrameIntervalBudgetTests.swift")'),
    (u'KNIVES = os.path.join(ROOT, ".scratch", "motion-audit-2", "mutate_r302.py")',
     u'KNIVES = os.path.join(ROOT, ".scratch", "motion-audit-2", "mutate_r303.py")\n'
     u'KNIVES_195 = os.path.join(ROOT, ".scratch", "motion-audit-2", "mutate_r195.py")\n'
     u'KNIVES_196 = os.path.join(ROOT, ".scratch", "motion-audit-2", "mutate_r196.py")'),
    (u'R_TAG = u"R303"\nR_NEXT = u"R304"\nPREV_TAG = u"R302"' if False else u'R_TAG = u"R302"\nR_NEXT = u"R303"\nPREV_TAG = u"R301"',
     u'R_TAG = u"R303"\nR_NEXT = u"R304"\nPREV_TAG = u"R302"'),
    (u'LEDGERS_R302 REFUSED', u'LEDGERS_R303 REFUSED'),
    (u'u"(?m)^R302_MUTATE 刀=', u'u"(?m)^R303_MUTATE 刀='),
    (u'/tmp/r302_battery_pre.log', u'/tmp/r303_battery_pre.log'),
    (u'/tmp/r302_battery_post.log', u'/tmp/r303_battery_post.log'),
    (u'u"LEDGERS_R302 OK batt=Ran ', u'u"LEDGERS_R303 OK batt=Ran '),
    (u'if LAST_ROUND != s(ROUND - 2):', u'if LAST_ROUND != s(ROUND - 3):'),
    (u'⇒ 与本轮（第 %d 轮）差两格，先查', u'⇒ 与本轮（第 %d 轮）差三格，先查'),
    (u'if (U_MAX, D_MAX, BL_MAX) != (988, 282, 359):', u'if (U_MAX, D_MAX, BL_MAX) != (991, 283, 360):'),
    (u'SUBS2[u"@UDEF@"] = s(U_DEFS + 3)', u'SUBS2[u"@UDEF@"] = s(U_DEFS + 3)'),
    (u'startswith(u"**358. ")', u'startswith(u"**360. ")'),
    (u'die(u"358 锚点异常（%d 处）" % len(h357))', u'die(u"360 锚点异常（%d 处）" % len(h357))'),
    (u'die(u"358 已有 %s 的结案追记" % R_TAG)', u'die(u"360 已有 %s 的同轮追记" % R_TAG)'),
    (u'if u"追记（%s 结案）" % R_TAG in orig["BL"]:', u'if u"追记（%s 第一步）" % R_TAG in orig["BL"]:'),
    (u'CLOSE_358 + ITEM_BLO', u'NOTE_360 + ITEM_BLO'),
    (u'CLOSE_358 = u"""', u'NOTE_360 = u"""'),
]
for a, b in MECH:
    n = t.count(a)
    if n != 1:
        raise SystemExit(u'MECH anchor count=%d: %r' % (n, a[:90]))
    t = t.replace(a, b)

# 三张刀表都要跑：本轮把 R195 / R196 的 needle 弄哑过又重钉，必须留读数
kstart = t.index(u'kout, krc = sh(["python3", KNIVES])')
kstop = t.index(u'if KE != u"0" or KNR != u"0" or KREST != u"yes" or KC != KN:')
t = t[:kstart] + (
u'kout, krc = sh(["python3", KNIVES])\n'
u'KS = re.findall(u"(?m)^R303_MUTATE 刀=(\\\\d+) CAUGHT=(\\\\d+) ESCAPED=(\\\\d+) NOT_RUN=(\\\\d+) "\n'
u'                u"RESTORE_CLEAN=(\\\\w+)", kout)\n'
u'if krc != 0 or not KS:\n'
u'    die(u"本轮刀表不是全 CAUGHT（rc=%s）：%s" % (krc, kout.strip()[-400:]))\n'
u'KN, KC, KE, KNR, KREST = KS[-1]\n'
u'# 被本轮改动弄哑的两张历史表：重钉之后必须真的还能红（DID-NOT-RUN / ESCAPED 都不算修好）\n'
u'hist = {}\n'
u'for tag, path in ((u"r195", KNIVES_195), (u"r196", KNIVES_196)):\n'
u'    hout, hrc = sh(["python3", path])\n'
u'    hs = re.findall(u"(?m)^%s_MUTATE 刀=(\\\\d+) CAUGHT=(\\\\d+) ESCAPED=(\\\\d+) NOT_RUN=(\\\\d+) "\n'
u'                    u"RESTORE_CLEAN=(\\\\w+)" % tag, hout)\n'
u'    if hrc != 0 or not hs or hs[-1][2] != u"0" or hs[-1][3] != u"0" or hs[-1][4] != u"yes":\n'
u'        die(u"历史刀表 %s 重钉之后仍不干净（rc=%s）：%s" % (tag, hrc, hout.strip()[-300:]))\n'
u'    hist[tag] = (hs[-1][1], hs[-1][0])\n'
u'\n'
) + t[kstop:]

# Swift 那张按文件的名字名册：总数从源码里现读，不手抄
t = t.replace(u'APPEAR = u"1/17 与 1/7"',
              u'APPEAR = u"1/17 与 1/7"\n'
              u'RSRC = os.path.join(ROOT, "scripts", "readings_roster_source.py")\n'
              u'router_out, rcrc = sh(["python3", RSRC])\n'
              u'rr = (re.findall(r"^ROSTER_READINGS (.*)$", router_out, re.M) or [u""])[-1]\n'
              u'rrk = dict(x.split(u"=", 1) for x in rr.split() if u"=" in x)\n'
              u'for need in (u"swift_total", u"swift_files", u"probe_lines", u"probe_markers"):\n'
              u'    if need not in rrk:\n'
              u'        die(u"读不到 Swift 名册的 %s（正文=%r）⇒ 那张名册的形状漂了，不许手抄" % (need, rr))\n'
              u'sw_tot = rrk[u"swift_total"]\n'
              u'sw_files = rrk[u"swift_files"]\n'
              u'sw_probe = rrk[u"probe_lines"]\n'
              u'sw_markers = rrk[u"probe_markers"]')

t = t.replace(u"    u\"@VHEAT@\": s(VERIFY_HEAT), u\"@VLINES@\": s(VERIFY_LINES), u\"@APPEAR@\": APPEAR,",
              u"    u\"@VHEAT@\": s(VERIFY_HEAT), u\"@VLINES@\": s(VERIFY_LINES), u\"@APPEAR@\": APPEAR,\n"
              u"    u\"@SWTOT@\": sw_tot, u\"@SWFILES@\": sw_files, u\"@SWMARK@\": sw_markers,\n"
              u"    u\"@SWPROBE@\": sw_probe,\n"
              u"    u\"@K195@\": hist[u\"r195\"][0] + u\"/\" + hist[u\"r195\"][1],\n"
              u"    u\"@K196@\": hist[u\"r196\"][0] + u\"/\" + hist[u\"r196\"][1],")

def block(name, new):
    global t
    head = name + u' = u"""'
    i = t.index(head)
    j = t.index(u'"""', i + len(head) + 3) + 3
    t = t[:i] + head + new + u'"""' + t[j:]

UI = u'''
## 第 @ROUND@ 轮（@RTAG@ · U-@UA@…U-@UC@ · @TODAY@）：搬走一批裸 stdout，然后被自己搬出来的洞红了一次

- **U-@UA@：360 的第一步落地 —— 探针那一卷 15 行读数从裸 stdout 搬进 `CaptureReadings.emit`，棘轮跟着从 57 降到现读 @BARE@。**
  搬的是 `UIInteractionProbeTests.swift` 里那些**已经被写进过台账**的数（FOCUS-CHAIN / TAB-KEY-CHAIN /
  KEYBOARD-UIMODE / AX-VISITED / AX-UNNAMED / KEYCHAIN / KEYCHAIN_TREE / KEYCHAIN_FKA /
  FOCUSCHAIN-RING / RINGVIEWS / FILTER_FOCUS / FILTER_PILL_FOCUS_UNCOVERED / NOTE）。
  同一轮名册由派生集自动抬到 @ROSTER@ 个（这个文件搬完就干净了 ⇒ 必须进名册，不进就红「未纳管」），
  未覆盖名单里它的 15 行退场。三把刀：M875 把其中一行改回裸 stdout ⇒ 红「盘上有 43 行」；
  M876 把**登记值本身**抬到 43（模拟拿登记值容纳现状）⇒ 红「登记值是 43」，这是 R74 那条
  「放宽要成对」在这一格上的落地；M877 把刚进名册的名字删掉 ⇒ 红「未纳管」。刀=@KC@/@KN@ 全 CAUGHT、
  RESTORE_CLEAN=@KREST@。
- **U-@UB@：本轮最值钱的一格是刀 ESCAPED 出来的 —— 按 print 找读数的名册，被「搬进 emit」这件事弄瞎了。**
  `FrameIntervalBudgetTests.testProbeFilePrintReadingsAreARosterNotACount`（R143 建）登记的是
  `UIInteractionProbeTests.swift` 的 print 读数清单。本轮把那 15 行搬走之后，M731（把
  `KEYCHAIN_FKA` 改名）**真的 ESCAPED 了一次**：读数还在、通道更好了，而那格再也不知道它存不存在 ——
  因为它把「读数的名字」和「读数的通道」绑成了同一件事。修法不是把刀删掉，是让名册**按通道读**：
  每个文件登记它现在走哪条腿（搬过的按 `emit("` 数、没搬的按 `print("` 数），并把这张名册的 subject
  从「这个文件还剩几行没搬」改成「这个文件的读数有没有名字」。现读：这张名册覆盖 @SWFILES@ 份文件、
  合计 @SWTOT@ 行，其中探针那份 @SWPROBE@ 行 / @SWMARK@ 种标记全部登记。M731 重跑 ⇒ CAUGHT（`R196_MUTATE 刀=@K196@`）。
- **U-@UC@：历史 needle 又哑了一批，而且是同一轮里第三次（腐烂的不只是 git 锚点，还有源码字面量锚点）。**
  把探针那 15 行改走 emit 之后，预检当场报 `bad=3`：R195 的 M728 / M729 与 R196 的 M731 的 needle
  都写着 `print("FILTER_…` / `print("KEYCHAIN_FKA 开关=` 这种**整行字面量**，源文件一改形状就命中 0 次。
  这一类不会自己响 —— 刀表会一路报绿而那一把刀从未跑过（DID-NOT-RUN 不是通过）。本轮把三根重钉到
  当前形状并重跑两张历史表：`R195_MUTATE 刀=@K195@`、`R196_MUTATE 刀=@K196@`，预检 bad=0、ARM_TOTAL=@ARMS@。
  另记一笔**没做完的**：现在有三张「谁还在用 print / 谁的读数有名字」的名单并存（脚本电池的派生名册、
  脚本电池的棘轮、Swift 的按文件标记名册），分工写在注释里，但合并成一处派生才是终点 —— 新开 @BLO@。

本轮产品文件 0 个（Tests / scripts / .scratch），连续零改动 **@STREAK@** 轮
（现读 `python3 scripts/product_streak.py --streak-for @ROUND@`：as-of 第 @ROUND@ 轮的最后一笔产品提交是
@LASTSHA@ = 第 @LASTROUND@ 轮，即 R300 的代码半；R301 / R302 / 本轮都只动判据与工具）。
四件套现读：全量卷 @SWIFT@ 用例 / 失败 @SWFAIL@、build 告警 @WARN@、帧 @FRAMES@ 张 compared=@CM@ changed=@CH@、
dmg=@Dmg@、换装 @VER@。看图腿：本轮没有新帧（产品 0 文件）⇒ 读的是文件里的读数清单与名册行数，
不是画面；四件套取证目录 @VLINES@ 行里热图 marker 仍 @VHEAT@ 行 ⇒ 359 仍开，没有沿用上一轮的结论。

'''
block(u'UI_NEW', UI.lstrip('\n') if False else UI)

ITER = u'''
## Round @RDN@ · @RTAG@（第 @ROUND@ 轮 · @TODAY@）：搬走 15 行裸 stdout，刀把搬出来的洞照出来了

本轮做的事：结掉 360 的第一步 —— 把 `UIInteractionProbeTests.swift` 里 15 行只走 stdout 的读数
改走 `CaptureReadings.emit`，覆盖率棘轮由 57 降到现读 @BARE@（登记值一起改，两个方向都有刀），
名册（派生集）自动抬到 @ROSTER@ 个。搬动弄哑了东西，也当场被抓住两次：
① `FrameIntervalBudgetTests` 那张**按 print** 的读数名册从此看不见搬走的读数 —— 刀 M731 真 ESCAPED，
   于是名册改成按通道读，并把该文件全部 @SWPROBE@ 行 / @SWMARK@ 种标记登记进来（现读合计 @SWTOT@ 行）；
② R195 / R196 的三根 needle（整行字面量锚点）命中 0 次，预检 bad=3 —— 重钉后两张历史表各自全 CAUGHT。
产品文件 0 个 —— 产物是 15 行能活下来的读数、一张不再把「名字」和「通道」绑死的名单、三根复活的针。

七维度自评：
| 维度 | 分/满分 |
| --- | --- |
@ROWS@| 合计 | @TOTAL@/105 |

为什么不是满分（逐条）：真实视觉审查 11 —— 无新帧，读的是清单与行数；产品面推进 4 —— 0 个产品文件、
连续 @STREAK@ 轮（这一维欠的是 347 那条真机证人，门在用户那边）；判据有效性 14 —— 三把新刀 +
三根重钉的针，且 ESCAPED 那一次换来名册换轴；假绿防御 15 —— 本轮唯一一把"红不出来"的刀被当成
产出而不是噪声（M731 先 ESCAPED 后 CAUGHT，两次读数都进了账）；台账一致性 13 —— 棘轮、派生名册、
Swift 名册三处数字全部现读同源（Swift 那张的 total 从源码正则里读，不手抄）；交付诚实性 14 ——
359 每轮重量而不是沿用，@BLO@ 明确写"第一步"而不是"结案"；可复核性 14 —— 三张名单并存这件事
本身被开成一单而不是留在注释里。

派生分由 `curve_from_ledger.py` 现读，不手抄。
未做（逐条）：① **305 的台阶地板**（等 347 的真机证人）；② 354 的第二步（动效地板登记成按机器×按用例的
有名字未覆盖，出现率已量到 @APPEAR@）；③ @BLO@（三张名单合并成一处派生）；④ 360 剩下的 @UNCOVFILES@ 份文件
@UNCOSUM@ 行；⑤ 359（取证目录没有汇聚点）；⑥ 348 的两格、349、350 第二步、351、344、341 的 CI 契约半、
339、312 具名出口、304、291；⑦ 用户闸门 220 路 A / 228② / 265。

'''
block(u'ITER_NEW', ITER)

DEC = u'''
**D-284（@RTAG@）：读数名册要登记「读数的名字」，不能把「读数的通道」一起绑进去；换通道的那一轮必须同时重量所有按旧通道写的名单。**
证据是刀而不是形容词：R143 建的 `testProbeFilePrintReadingsAreARosterNotACount` 按 `print("` 找
`UIInteractionProbeTests.swift` 的读数，本轮把这 15 行搬进 `CaptureReadings.emit` 之后，
M731（把标记 `KEYCHAIN_FKA` 改名）**先 ESCAPED 后 CAUGHT** —— 同一条断言，在搬动前后对同一种坏的
可见性变了，因为它问的其实是「有没有一行 print」。修法分两层：① 名册的 subject 换成
「这个文件的读数清单」，通道由名册自己按文件登记（搬过的按 `emit("` 数，没搬的按 `print("` 数）；
② 「谁还没搬」这件事交给另一格（脚本电池的派生名册与棘轮），两格各判一句话，不许互相顶。
同一轮的第二条：needle 用整行字面量做锚点的历史刀表，会在被扫文件改形状时**静默变哑**
（本轮预检 bad=3：R195 的 M728/M729、R196 的 M731）。规矩因此加一句：改判据代码的那一轮，
必须跑一次预检并把「哪几根命中 0 次」当成本轮产出，重钉后重跑该表拿到 CAUGHT 才算完。
'''
block(u'DEC_NEW', DEC)

NOTE = u'''
  追记（@RTAG@ 第一步，**不结案**）：本轮搬走的是这张表里最大的一处 —— `UIInteractionProbeTests.swift`
  15 行 → 0 行（FOCUS-CHAIN / TAB-KEY-CHAIN / KEYBOARD-UIMODE / AX-VISITED / AX-UNNAMED /
  FOCUSCHAIN-RING / RINGVIEWS / KEYCHAIN / KEYCHAIN_TREE / KEYCHAIN_FKA / FILTER_FOCUS /
  FILTER_PILL_FOCUS_UNCOVERED / NOTE 全部改走 `CaptureReadings.emit`）。
  棘轮跟着降到现读 @BARE@（登记值与 `NAMED_UNCOVERED` 同一轮改，两个方向各有刀：M875 / M876）。
  搬动同时暴露另一件事：按 `print` 写的读数名册会因此瞎掉，M731 先 ESCAPED 后 CAUGHT 才算修好
  （见 D-284），Swift 那张名册现在按通道读、合计 @SWTOT@ 行。
  剩下的 @UNCOVFILES@ 份文件 @UNCOSUM@ 行继续按「一轮搬几份、搬完就降登记值」走，本单不结案。

'''
block(u'ITEM_BLO_PLACEHOLDER', NOTE) if False else None
# CLOSE_358 → NOTE_360 的正文整体替换
cstart = t.index(u'NOTE_360 = u"""')
cstop = t.index(u'"""', cstart + len(u'NOTE_360 = u"""')) + 3
t = t[:cstart] + u'NOTE_360 = u"""' + NOTE + u'"""' + t[cstop:]

ITEM = u'''
**@BLO@. 同一个问题现在有三张名单：脚本电池的派生名册（谁进了通道）、脚本电池的棘轮（还剩几行裸 stdout）、Swift 的按文件读数名册（读数有没有名字）—— 三份都各自对账，但没有一处是另一处的上游（@RTAG@ 现读）**：
  本轮把 `UIInteractionProbeTests.swift` 搬进 emit 之后，三张名单各自变红过一次或各自更新过一次：
  棘轮（登记值 57 → @BARE@）、派生名册（3 → @ROSTER@ 个）、Swift 名册（按 print 改成按通道，合计 @SWTOT@ 行）。
  这不是重复劳动那么简单 —— 它们**口径不同**：派生名册问「这个文件的代码里还有没有裸 stdout」，
  棘轮问「全仓库还剩几行」，Swift 名册问「这些读数有没有登记过的名字」。三句话都对，
  但同一次改动要三处手工同步，漏一处就是下一轮的假绿。
  终点形状（先量再选，别先写门）：① 名字清单做成**一份数据**（按文件 → 按标记 → 行数），
  Swift 那格与 python 那格都从同一份读；棘轮只是它的一个求和视图；
  ② 或者明确两张名单的分工并让"漏同步"本身会红：谁没被另一张覆盖到就红（现在靠人记得跑三处）。
  ① 需要先回答一个未知数：Swift 侧能不能读到 python 侧那张表（跨 target 的文件读法已经用过一次，
  见 `UICaptureTests` 读仓库源码），② 只需要一条按文件的双向对账。
  本轮已做的是把三处各自的注释写成「判的是哪一句话」，并把分工写进 D-284。

'''
istart = t.index(u'ITEM_BLO = u"""')
istop = t.index(u'"""', istart + len(u'ITEM_BLO = u"""')) + 3
t = t[:istart] + u'ITEM_BLO = u"""' + ITEM + u'"""' + t[istop:]

CHG = (u'CHG_NEW = (u"### Improved（@RTAG@ / 第 @ROUND@ 轮 / Round @RDN@ · 搬走一批裸 stdout，名册换成按通道读）\\n\\n"\n'
       u'           u"360 的第一步：`UIInteractionProbeTests.swift` 的 15 行读数改走 `CaptureReadings.emit`，"\n'
       u'           u"覆盖率棘轮随之从 57 降到现读 @BARE@（登记值与未覆盖名单同一轮改）。三把新刀：M875 把一行改回裸 stdout ⇒ 红在盘上有，"\n'
       u'           u"M876 把登记值抬到 43 去容纳现状 ⇒ 红在登记值是（R74 的「放宽要成对」在这一格落地），M877 把刚进派生名册的文件删掉 ⇒ 红在未纳管。"\n'
       u'           u"本轮真正的产出是一次 ESCAPED：`FrameIntervalBudgetTests` 那张 R143 建的读数名册是按「print 加左引号」找读数的，"\n'
       u'           u"搬动之后刀 M731（把标记 KEYCHAIN_FKA 改名）红不出来 —— 它把读数的名字和读数的通道绑成了一件事。"\n'
       u'           u"名册因此改成按通道读（该文件现登记 @SWPROBE@ 行 / @SWMARK@ 种标记，整张表合计 @SWTOT@ 行），M731 重跑 CAUGHT（D-284）。"\n'
       u'           u"同轮还复活的三根哑针：R195 的 M728/M729 与 R196 的 M731 因整行字面量锚点漂了命中 0 次（预检 bad=3），"\n'
       u'           u"重钉后 `R195_MUTATE 刀=@K195@`、`R196_MUTATE 刀=@K196@`、`R303_MUTATE 刀=@KC@/@KN@` 三张表全 CAUGHT，预检 bad=0、ARM_TOTAL=@ARMS@。"\n'
       u'           u"新开 @BLO@（三张名单并存，缺一处上游）。359 本轮重量：四件套取证目录 @VLINES@ 行里热图 marker 仍 @VHEAT@ 行 ⇒ 仍开。"\n'
       u'           u"产品文件 0 个；四件套现读：全量卷 @SWIFT@/失败 @SWFAIL@、告警 @WARN@、帧 @FRAMES@ 张 changed=@CH@、"\n'
       u'           u"dmg=@Dmg@、换装 @VER@；电池 Ran @BATT@ / OK (skipped=@SKIP@)。\\n\\n")')
cstart = t.index(u'CHG_NEW = (')
cstop = t.index(u'\\n\\n")', cstart) + len(u'\\n\\n")')
t = t[:cstart] + CHG + t[cstop:]

STATE = u'''## @RTAG@ 状态（第 @ROUND@ 轮 / Round @RDN@ · @TODAY@）

⓪ 读 CI（@RNEXT@ 的开场取数，只登记不轮询 = R140）：@CI_LINE@
要验的四件事：① `4adc04f` / `ac1ed6b`（@PREV@ 的代码半与账半）与本轮两笔的成对号；
② 名册派生化之后 `testCaptureReadingsUseTheFileChannel` 在 runner 上是否与本机同为 @ROSTER@ 个名字
（同一棵树同一批文件 ⇒ 不同就是接线）；③ `test_readings_channel_coverage` 那 5 格在 runner 上的
裸 stdout 计数是否同为 @BARE@；④ STEP[19] 的动效地板若再现 ⇒ 按 354 的②登记成有名字的未覆盖（出现率已量到 @APPEAR@）。

最后更新：@TODAY@（本地 · @RTAG@ / 第 @ROUND@ 轮 / Round @RDN@）：**360 的第一步 + 一次刀教出来的换轴** ——
`UIInteractionProbeTests.swift` 那 15 行裸 stdout 改走 `CaptureReadings.emit`，棘轮由 57 降到现读 @BARE@，
派生名册抬到 @ROSTER@ 个；刀 M875/M876/M877 全 CAUGHT（M876 钉的是「拿登记值容纳现状」那一侧）。
本轮最值钱的是 M731 先 ESCAPED 后 CAUGHT：按 `print` 写的读数名册在搬动之后对「标记被改名」失去可见性，
说明它把名字和通道绑死了 ⇒ 名册改成按通道读（合计 @SWTOT@ 行，探针那份 @SWPROBE@ 行 / @SWMARK@ 种标记全登记，D-284）。
同轮复活三根哑针（R195 的 M728/M729、R196 的 M731，needle 命中 0 次 ⇒ 预检 bad=3）⇒ 两张历史表重跑各自全 CAUGHT。
四件套：全量卷 @SWIFT@/失败 @SWFAIL@、build 告警 @WARN@、帧 @FRAMES@ 张 changed=@CH@、dmg=@Dmg@、换装 @VER@；
预检 ARM_TOTAL=@ARMS@ bad=0；电池 Ran @BATT@ / OK (skipped=@SKIP@)。
产品文件 0 个，连续零改动 **@STREAK@** 轮（现读 `python3 scripts/product_streak.py --streak-for @ROUND@`：
as-of 第 @ROUND@ 轮的最后一笔产品提交是 @LASTSHA@ = 第 @LASTROUND@ 轮，即 R300 的代码半）。

① 下一轮（@RNEXT@）的靶：**354 的第二步** —— 把动效地板那两朵红登记成按机器×按用例切片的
有名字未覆盖（名册要能退场、红话要打印键；出现率已有数 @APPEAR@，覆盖率名单这一族的对账形状本轮已经建好）。
顺带 @BLO@（三张名单合并成一处派生，先做②那条双向对账，别先写门）；360 剩下的 @UNCOVFILES@ 份文件继续搬。
产品面：347/305 仍挡在用户那一边（要退出 App 或回答一句「收藏星按下够不够明显」）。

② 仍开：347（真机证人）、305（等 347）、354 的第二步（登记成有名字的未覆盖）、
360（第一步已完成，剩 @UNCOSUM@ 行）、@BLO@（三张名单并存，缺一处上游）、
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
                  u'              u"最后一笔产品提交是 @LASTSHA@ = 第 @LASTROUND@ 轮，即 R300 的代码半（那一笔改了 2 个文件：悬停环 0.55→0.30、"\n'
                  u'              u"梯子顶档 0.85→0.92）；R301 / @PREV@ / 本轮都只动判据与工具。"\n'
                  u'              u"这一格不许手抄：`--check` 会在台账与派生值不同源时拒绝这一版。\\n")')),
 (u'FR_DOOR', (u'FR_DOOR = (u"- **判据与门的规模**：脚本电池 **Ran @BATT@**（现读 `python3 -m unittest discover -s scripts/tests`）；"\n'
               u'           u"变异臂抽到 **@ARMS@** 把（现读预检 `ARM_TOTAL`，bad=0）；U 定义行 **@UDEF@ 条**、最大 **U-@UC@**"\n'
               u'           u"（`AGENT_UI_AUDIT.md`）；决定最大 **D-@DN@**；BACKLOG 最大 **@BLO@**。"\n'
               u'           u"最近这几轮立/改的门：0 告警能拦（343）、`pillReading` 带窗上界去掉（346）、commit-subject 对账与豁免退场（348）、"\n'
               u'           u"台账区间分箱（350）、产品面轮数只能由 `scripts/product_streak.py` 派生（353）、交互标记不许比一次数据变化更响（314/D-281）、"\n'
               u'           u"判据读数必须有能活下来的通道且名册不许空转（357/D-282）、名册的合法取值是派生集且棘轮双向（358/D-283）、"\n'
               u'           u"**读数名册登记的是名字不是通道；换通道那一轮要重量所有按旧通道写的名单（D-284）**。"\n'
               u'           u"本轮现读：判据文件 @FILES@ 份、用文件通道的 @EMITTERS@ 份、名册 @ROSTER@ 个、"\n'
               u'           u"仍在裸 stdout 的读数 **@BARE@ 行**（= 登记值；上一轮 57，本轮搬走 15 行 ⇒ 360 的第一步）；"\n'
               u'           u"Swift 那张按文件的读数名册合计 **@SWTOT@ 行**（探针那份 @SWPROBE@ 行 / @SWMARK@ 种标记，已改成按通道读）；"\n'
               u'           u"三张名单并存缺一处上游 ⇒ 新开 @BLO@。取证目录本轮重量：@VLINES@ 行里热图 marker 仍 **@VHEAT@ 行** ⇒ 359 仍开。\\n")')),
]
for name, new in FRS:
    i = t.index(name + u' = (')
    j = t.index(u'\\n")', i) + len(u'\\n")')
    t = t[:i] + new + t[j:]

# 上一轮插在 §13「仍开」里的那一格：本轮要把 360 标成第一步、把 361 加进去
t = t.replace(u'    u"%d（%s 行裸 stdout 按文件搬进通道）、359（取证目录没有读数汇聚点）" % (BLO, UNCOV_SUM))',
              u'    u"360（第一步已做，剩 %s 行）、359（取证目录没有读数汇聚点）、%d（三张名单并存）" % (UNCOV_SUM, BLO))')
t = t.replace(u'if u"%d（" % BLO not in fr_still:', u'if u"%d（三张名单并存）" % BLO not in fr_still:')
t = t.replace(u'R302_CI_LINE', u'R303_CI_LINE')

ast.parse(t)
io.open(DST, 'w', encoding='utf-8').write(t)
bad = [(i, l[:70]) for i, l in enumerate(t.split(u'\n'), 1) if l.count(u'「') != l.count(u'」')]
print('WROTE %s unbalanced=%d %s' % (DST, len(bad), bad[:3]))
