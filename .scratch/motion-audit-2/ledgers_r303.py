#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R303（第 302 轮 / Round 300）的七本台账落盘 —— 事务性，与 ledgers_r302 同一形状。

本轮**不动产品**（只动 Tests / scripts / .scratch），所以 streak 由取数口按 as-of 第 302 轮现读（=3），
不假设它是 0；`git show HEAD -- Sources` 为空是正常形状。

规矩（栽过之后写死的）：
· 七本的新文本先全部算出来再一次性写盘；写盘前后各跑一次电池，计数变了或不绿 ⇒ 全部还原（R294）。
· 一律 @TOKEN@ 替换（长 token 先换），不往 CJK 正文里写 `%` 格式化。
· 所有计数由仪器现读：电池、曲线、product_streak、帧基线、预检、变异表、round_verify 摘要。
· 写盘之前按守卫的正则原样自测形状（round_batch 前缀、U 区间与节内定义行吻合、七维表 7 行、
  STATE 最后更新行、353 门要求的两格形状、报告 §13 的 bullet 数与 §1 的 Sources 行）。
"""
import io
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FILES = {
    "UI": os.path.join(ROOT, "AGENT_UI_AUDIT.md"),
    "IT": os.path.join(ROOT, "AGENT_VISUAL_ITERATION.md"),
    "DEC": os.path.join(ROOT, "AGENT_DECISIONS.md"),
    "BL": os.path.join(ROOT, "AGENT_BACKLOG.md"),
    "ST": os.path.join(ROOT, "AGENT_STATE.md"),
    "CH": os.path.join(ROOT, "CHANGELOG.md"),
    "FR": os.path.join(ROOT, "AGENT_FINAL_REPORT.md"),
}
VERIFY_LOG = "/tmp/r303_verify_run.log"
VERIFY_READINGS = "/tmp/r303_verify/frames/capture-readings.log"
SWIFT_ROSTER = os.path.join(ROOT, "ClipboardHistory", "Tests", "ClipboardHistoryAppTests",
                               "FrameIntervalBudgetTests.swift")
COV_ROLL = os.path.join("scripts", "tests", "test_readings_channel_coverage.py")
CURVE = os.path.join(ROOT, ".scratch", "motion-audit-2", "curve_from_ledger.py")
STREAK = os.path.join(ROOT, "scripts", "product_streak.py")
PRECHECK = os.path.join(ROOT, ".scratch", "motion-audit-2", "mutate_needle_precheck.py")
KNIVES = os.path.join(ROOT, ".scratch", "motion-audit-2", "mutate_r303.py")
KNIVES_195 = os.path.join(ROOT, ".scratch", "motion-audit-2", "mutate_r195.py")
KNIVES_196 = os.path.join(ROOT, ".scratch", "motion-audit-2", "mutate_r196.py")
REFRESH = os.path.join(ROOT, ".scratch", "motion-audit-2", "refresh_report_section1.py")
DIMS = [u"真实视觉审查", u"判据有效性", u"假绿防御", u"产品面推进", u"台账一致性",
        u"交付诚实性", u"可复核性"]
SCORES = [11, 14, 14, 4, 13, 14, 14]
R_TAG = u"R303"
R_NEXT = u"R304"
PREV_TAG = u"R302"
TODAY = subprocess.check_output([u"date", u"+%Y-%m-%d"]).decode().strip()
# ⓪ 的成对号（本轮现读，只登记不轮询 = R140）
CI_LINE = os.environ.get("R303_CI_LINE", u"CI 通道本轮读到一半就断（`gh run list` ⇒ EOF），成对号未读 ⇒ @RNEXT@ 开场第一件事就是重读 ①②③ 那三件事对应的两跑")


def s(x):
    return str(x)


def die(m):
    sys.stderr.write(u"LEDGERS_R303 REFUSED: " + m + u"\n")
    raise SystemExit(1)


def rd(p):
    with io.open(p, encoding="utf-8") as h:
        return h.read()


def wr(p, t):
    with io.open(p, "w", encoding="utf-8") as h:
        h.write(t)


def sh(argv):
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["PYTHONUTF8"] = "1"
    env["LC_ALL"] = "en_US.UTF-8"
    env["DEVELOPER_DIR"] = "/Applications/Xcode.app/Contents/Developer"
    proc = subprocess.Popen(argv, cwd=ROOT, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, env=env)
    return proc.communicate()[0].decode("utf-8", "replace"), proc.returncode


def battery(tag, path=None):
    txt, rc = sh(["python3", "-W", "ignore", "-m", "unittest", "discover",
                  "-s", "scripts/tests", "-v"])
    if path:
        wr(path, txt)
    ran = re.findall(r"^Ran (\d+) tests", txt, re.M)
    ok = re.findall(r"^OK \(skipped=(\d+)\)", txt, re.M)
    names = len(set(re.findall("skipped '([^']*)'", txt)))
    if rc != 0 or not ran or not ok or ok[-1] != str(names):
        blocks = re.findall(u"(?m)^(?:FAIL|ERROR):.*", txt)
        return None, tag + u" 电池不绿（全文见 %s）：%s" % (path or u"?", u" | ".join(blocks)[:1500])
    return (ran[-1], ok[-1], names), ""


def bullet(text, label):
    rx = re.compile(u"(?m)^- \\*\\*" + label + u"\\*\\*：.*?(?=^- |^\\Z)", re.S)
    hits = list(rx.finditer(text))
    if len(hits) != 1:
        die(u"报告 §13 的「%s」bullet 命中 %d 处（要恰好 1 处）" % (label, len(hits)))
    return hits[0].start(), hits[0].end()


def fill_tpl(t, mapping):
    for k in sorted(mapping, key=len, reverse=True):
        t = t.replace(k, mapping[k])
    return t


# ── 读数 ───────────────────────────────────────────────────────────
dout, drc = sh(["python3", STREAK])
dline = (re.findall(u"^PRODUCT_STREAK (.*)$", dout, re.M) or [u""])[-1]
dk = dict(x.split(u"=", 1) for x in dline.split() if u"=" in x)
if drc != 0 or u"ledger_round" not in dk:
    die(u"product_streak 没出现读（rc=%s）：%s" % (drc, dout.strip()[-300:]))
MAX_ROUND = dk[u"ledger_round"]
ROUND = int(MAX_ROUND) + 1
fout, frc = sh(["python3", STREAK, "--streak-for", s(ROUND)])
fl = (re.findall(u"^PRODUCT_STREAK_FOR (.*)$", fout, re.M) or [u""])[-1]
fk = dict(x.split(u"=", 1) for x in fl.split() if u"=" in x)
if frc != 0 or u"streak" not in fk:
    die(u"--streak-for 第 %d 轮取不到：%s" % (ROUND, fout.strip()[-300:]))
STREAK_N = fk[u"streak"]
LAST_SHA = (re.findall(u"last=(\\S+)", fl) or [u"?"])[-1]
LAST_ROUND = (re.findall(u"last_round=(\\d+)", fl) or [u"?"])[-1]
if LAST_ROUND != s(ROUND - 3):
    die(u"as-of 第 %d 轮读到的最后一笔产品提交是第 %s 轮 ⇒ 与本轮（第 %d 轮）差三格，先查"
        % (ROUND, LAST_ROUND, ROUND))

vlog = rd(VERIFY_LOG) if os.path.exists(VERIFY_LOG) else u""
VSUM = (re.findall(u"(?m)^ROUND_VERIFY (.*)$", vlog, re.M) or [u""])[-1]
vk = dict(x.split(u"=", 1) for x in VSUM.split() if u"=" in x)
for key in (u"build_warnings", u"swift_executed", u"swift_failures", u"frames",
            u"baseline_compared", u"baseline_changed", u"dmg", u"installed_version"):
    if key not in vk:
        die(u"round_verify 摘要缺格 %s（摘要行=%r）⇒ 四件套没跑完" % (key, VSUM[:200]))
if vk[u"baseline_changed"] != u"0" or vk[u"swift_failures"] != u"0" or vk[u"build_warnings"] != u"0":
    die(u"四件套不干净（changed=%s failures=%s warnings=%s）"
        % (vk[u"baseline_changed"], vk[u"swift_failures"], vk[u"build_warnings"]))

# 覆盖率那一卷的自印读数行 —— 本轮进账的所有覆盖率数都必须来自它（现读现取，不算）
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
for part in re.findall(u"(\S+?)=([^ ]*)", rline):
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
RSRC = os.path.join(ROOT, "scripts", "readings_roster_source.py")
router_out, rcrc = sh(["python3", RSRC])
rr = (re.findall(r"^ROSTER_READINGS (.*)$", router_out, re.M) or [u""])[-1]
rrk = dict(x.split(u"=", 1) for x in rr.split() if u"=" in x)
for need in (u"swift_total", u"swift_files", u"probe_lines", u"probe_markers"):
    if need not in rrk:
        die(u"读不到 Swift 名册的 %s（正文=%r）⇒ 那张名册的形状漂了，不许手抄" % (need, rr))
sw_tot = rrk[u"swift_total"]
sw_files = rrk[u"swift_files"]
sw_probe = rrk[u"probe_lines"]
sw_markers = rrk[u"probe_markers"]

kout, krc = sh(["python3", KNIVES])
KS = re.findall(u"(?m)^R303_MUTATE 刀=(\\d+) CAUGHT=(\\d+) ESCAPED=(\\d+) NOT_RUN=(\\d+) "
                u"RESTORE_CLEAN=(\\w+)", kout)
if krc != 0 or not KS:
    die(u"本轮刀表不是全 CAUGHT（rc=%s）：%s" % (krc, kout.strip()[-400:]))
KN, KC, KE, KNR, KREST = KS[-1]
# 被本轮改动弄哑的两张历史表：重钉之后必须真的还能红（DID-NOT-RUN / ESCAPED 都不算修好）
hist = {}
for tag, path in ((u"r195", KNIVES_195), (u"r196", KNIVES_196)):
    hout, hrc = sh(["python3", path])
    hs = re.findall(u"(?m)^%s_MUTATE 刀=(\\d+) CAUGHT=(\\d+) ESCAPED=(\\d+) NOT_RUN=(\\d+) "
                    u"RESTORE_CLEAN=(\\w+)" % tag.upper(), hout)
    if hrc != 0 or not hs or hs[-1][2] != u"0" or hs[-1][3] != u"0" or hs[-1][4] != u"yes":
        die(u"历史刀表 %s 重钉之后仍不干净（rc=%s）：%s" % (tag, hrc, hout.strip()[-300:]))
    hist[tag] = (hs[-1][1], hs[-1][0])

if KE != u"0" or KNR != u"0" or KREST != u"yes" or KC != KN:
    die(u"变异表不干净：刀=%s CAUGHT=%s ESCAPED=%s NOT_RUN=%s RESTORE_CLEAN=%s"
        % (KN, KC, KE, KNR, KREST))

pout, prc = sh(["python3", PRECHECK])
at = re.findall(r"^ARM_TOTAL files=(\d+) arms=(\d+) dupes=(\d+) repeats=(\d+)", pout, re.M)
np_ = re.findall(r"^NEEDLE_PRECHECK tables=(\d+) covered=(\d+) arms=(\d+) bad=(\d+)", pout, re.M)
if prc != 0 or not at or not np_:
    die(u"预检读数缺档（rc=%s）：%s" % (prc, pout.strip()[-300:]))
ARMS, BAD = at[-1][1], np_[-1][3]
if at[-1][2] != u"0" or at[-1][3] != u"0" or BAD != u"0":
    die(u"预检有红（dupes=%s repeats=%s bad=%s）" % (at[-1][2], at[-1][3], BAD))

cv, crc = sh(["python3", CURVE])
if crc != 0:
    die(u"曲线仪器不是 0：" + cv.strip()[-200:])
SECTIONS = (re.findall(r"^ROUNDS=(\d+)", cv, re.M) or [u""])[-1]
LAST_RND = (re.findall(r"\bfirst=\d+\s+last=(\d+)", cv) or [u""])[-1]
BYROUND = (re.findall(u"(?m)^SCORES_BY_ROUND (.*)$", cv, re.M) or [u""])[-1]
pairs = re.findall(u"(\\d{3})=(\\d{2,3})", BYROUND)
if not SECTIONS or not LAST_RND or len(pairs) < 4:
    die(u"曲线读数缺档（ROUNDS=%s last=%s 分数对=%d）" % (SECTIONS, LAST_RND, len(pairs)))
RD_N = int(LAST_RND) + 1
TAIL_OLD = u" · ".join(u"%s=%s" % (a, b) for a, b in pairs[-4:])

# 354 的出现率（本轮现读的 CI 历史，按「同一份 Swift 树」分组）
APPEAR = u"1/17 与 1/7"
RSRC = os.path.join(ROOT, "scripts", "readings_roster_source.py")
router_out, rcrc = sh(["python3", RSRC])
rr = (re.findall(r"^ROSTER_READINGS (.*)$", router_out, re.M) or [u""])[-1]
rrk = dict(x.split(u"=", 1) for x in rr.split() if u"=" in x)
for need in (u"swift_total", u"swift_files", u"probe_lines", u"probe_markers"):
    if need not in rrk:
        die(u"读不到 Swift 名册的 %s（正文=%r）⇒ 那张名册的形状漂了，不许手抄" % (need, rr))
sw_tot = rrk[u"swift_total"]
sw_files = rrk[u"swift_files"]
sw_probe = rrk[u"probe_lines"]
sw_markers = rrk[u"probe_markers"]

ui = rd(FILES["UI"])
U_MAX = max(int(x) for x in re.findall(u"(?m)^- \\*\\*U-(\\d{3})", ui))
D_MAX = max(int(x) for x in re.findall(u"(?m)^\\*\\*D-(\\d{3})", rd(FILES["DEC"])))
BL_MAX = max(int(x) for x in re.findall(u"(?m)^\\*\\*(\\d{3})\\. ", rd(FILES["BL"])))
if (U_MAX, D_MAX, BL_MAX) != (991, 283, 360):
    die(u"最大编号与本轮取靶时不符（读到 U-%d / D-%d / BACKLOG-%d）⇒ 有别的会话先动了账"
        % (U_MAX, D_MAX, BL_MAX))
UA, UB, UC = U_MAX + 1, U_MAX + 2, U_MAX + 3
DN, BLO = D_MAX + 1, BL_MAX + 1
U_DEFS = len(re.findall(u"(?m)^- \\*\\*U-\\d{3}[：(]", ui))

pre, err = battery(u"写盘前", u"/tmp/r303_battery_pre.log")
if pre is None:
    die(err)

TOTAL = sum(SCORES)
ROWS = u"\n".join(u"| %s | %d/15 |" % (d, sc) for d, sc in zip(DIMS, SCORES))

SUBS = {
    u"@RTAG@": R_TAG, u"@PREV@": PREV_TAG, u"@RNEXT@": R_NEXT,
    u"@ROUND@": s(ROUND), u"@RDN@": s(RD_N),
    u"@UA@": s(UA), u"@UB@": s(UB), u"@UC@": s(UC), u"@DN@": s(DN), u"@BLO@": s(BLO),
    u"@STREAK@": STREAK_N, u"@LASTSHA@": LAST_SHA, u"@LASTROUND@": LAST_ROUND,
    u"@MAXROUND@": MAX_ROUND, u"@CM@": vk[u"baseline_compared"], u"@CH@": vk[u"baseline_changed"],
    u"@FRAMES@": vk[u"frames"], u"@SWIFT@": vk[u"swift_executed"], u"@SWFAIL@": vk[u"swift_failures"],
    u"@Dmg@": vk[u"dmg"], u"@VER@": vk[u"installed_version"], u"@WARN@": vk[u"build_warnings"],
    u"@ROWS@": ROWS + u"\n", u"@TOTAL@": s(TOTAL), u"@BATT@": pre[0], u"@SKIP@": pre[1],
    u"@ARMS@": ARMS, u"@KN@": KN, u"@KC@": KC, u"@KREST@": KREST, u"@TODAY@": TODAY,
    u"@SECTIONS@": s(int(SECTIONS) + 1), u"@TAIL@": TAIL_OLD, u"@CI_LINE@": CI_LINE,
    u"@FILES@": FILES_SCANNED, u"@EMITTERS@": EMITTERS, u"@ROSTER@": ROSTER_N,
    u"@BARE@": BARE, u"@CEIL@": CEIL, u"@UNCOVFILES@": UNCOV_FILES, u"@UNCOSUM@": UNCOV_SUM,
    u"@WORSTFILE@": WORST_FILE, u"@WORSTN@": WORST_N,
    u"@VHEAT@": s(VERIFY_HEAT), u"@VLINES@": s(VERIFY_LINES), u"@APPEAR@": APPEAR,
    u"@SWTOT@": sw_tot, u"@SWFILES@": sw_files, u"@SWMARK@": sw_markers,
    u"@SWPROBE@": sw_probe,
    u"@K195@": hist[u"r195"][0] + u"/" + hist[u"r195"][1],
    u"@K196@": hist[u"r196"][0] + u"/" + hist[u"r196"][1],
}


def fill(t):
    return fill_tpl(t, SUBS)


UI_NEW = u"""## 第 @ROUND@ 轮（@RTAG@ · U-@UA@…U-@UC@ · @TODAY@）：搬走一批裸 stdout，然后被自己搬出来的洞红了一次

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

"""

ITER_NEW = u"""## Round @RDN@ · @RTAG@（第 @ROUND@ 轮 · @TODAY@）：搬走 15 行裸 stdout，刀把搬出来的洞照出来了

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

"""

DEC_NEW = u"""
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
"""

NOTE_360 = u"""  追记（@RTAG@ 第一步，**不结案**）：本轮搬走的是这张表里最大的一处 —— `UIInteractionProbeTests.swift`
  15 行 → 0 行（FOCUS-CHAIN / TAB-KEY-CHAIN / KEYBOARD-UIMODE / AX-VISITED / AX-UNNAMED /
  FOCUSCHAIN-RING / RINGVIEWS / KEYCHAIN / KEYCHAIN_TREE / KEYCHAIN_FKA / FILTER_FOCUS /
  FILTER_PILL_FOCUS_UNCOVERED / NOTE 全部改走 `CaptureReadings.emit`）。
  棘轮跟着降到现读 @BARE@（登记值与 `NAMED_UNCOVERED` 同一轮改，两个方向各有刀：M875 / M876）。
  搬动同时暴露另一件事：按 `print` 写的读数名册会因此瞎掉，M731 先 ESCAPED 后 CAUGHT 才算修好
  （见 D-284），Swift 那张名册现在按通道读、合计 @SWTOT@ 行。
  剩下的 @UNCOVFILES@ 份文件 @UNCOSUM@ 行继续按「一轮搬几份、搬完就降登记值」走，本单不结案。

"""

ITEM_BLO = u"""
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

"""





CHG_NEW = (u"### Improved（@RTAG@ / 第 @ROUND@ 轮 / Round @RDN@ · 搬走一批裸 stdout，名册换成按通道读）\n\n"
           u"360 的第一步：`UIInteractionProbeTests.swift` 的 15 行读数改走 `CaptureReadings.emit`，"
           u"覆盖率棘轮随之从 57 降到现读 @BARE@（登记值与未覆盖名单同一轮改）。三把新刀：M875 把一行改回裸 stdout ⇒ 红在盘上有，"
           u"M876 把登记值抬到 43 去容纳现状 ⇒ 红在登记值是（R74 的「放宽要成对」在这一格落地），M877 把刚进派生名册的文件删掉 ⇒ 红在未纳管。"
           u"本轮真正的产出是一次 ESCAPED：`FrameIntervalBudgetTests` 那张 R143 建的读数名册是按「print 加左引号」找读数的，"
           u"搬动之后刀 M731（把标记 KEYCHAIN_FKA 改名）红不出来 —— 它把读数的名字和读数的通道绑成了一件事。"
           u"名册因此改成按通道读（该文件现登记 @SWPROBE@ 行 / @SWMARK@ 种标记，整张表合计 @SWTOT@ 行），M731 重跑 CAUGHT（D-284）。"
           u"同轮还复活的三根哑针：R195 的 M728/M729 与 R196 的 M731 因整行字面量锚点漂了命中 0 次（预检 bad=3），"
           u"重钉后 `R195_MUTATE 刀=@K195@`、`R196_MUTATE 刀=@K196@`、`R303_MUTATE 刀=@KC@/@KN@` 三张表全 CAUGHT，预检 bad=0、ARM_TOTAL=@ARMS@。"
           u"新开 @BLO@（三张名单并存，缺一处上游）。359 本轮重量：四件套取证目录 @VLINES@ 行里热图 marker 仍 @VHEAT@ 行 ⇒ 仍开。"
           u"产品文件 0 个；四件套现读：全量卷 @SWIFT@/失败 @SWFAIL@、告警 @WARN@、帧 @FRAMES@ 张 changed=@CH@、"
           u"dmg=@Dmg@、换装 @VER@；电池 Ran @BATT@ / OK (skipped=@SKIP@)。\n\n")

STATE_NEW = u"""## @RTAG@ 状态（第 @ROUND@ 轮 / Round @RDN@ · @TODAY@）

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

"""

texts = {k: fill(v) for k, v in {
    "UI": UI_NEW, "IT": ITER_NEW, "DEC": DEC_NEW,
    "BL": NOTE_360 + ITEM_BLO, "CH": CHG_NEW, "ST": STATE_NEW,
}.items()}

# ── 形状自测 ───────────────────────────────────────────────────────
ui_new = texts["UI"]
title = ui_new.splitlines()[0]
if u"（%s ·" % R_TAG not in title:
    die(u"标题缺 round_batch 要的前缀")
nums = [int(x) for x in re.findall(u"(?m)^- \\*\\*U-(\\d{3})：", ui_new)]
if nums != [UA, UB, UC]:
    die(u"节内 U 定义行与标题区间不吻合：%s vs %s" % (nums, [UA, UB, UC]))
if len(re.findall(u"(?m)^\\| .+ \\| \\d+/15 \\|$", texts["IT"])) != 7:
    die(u"七维格子不是 7 行 n/15")
if u"七维度自评：" not in texts["IT"]:
    die(u"ITERATION 缺锚点")
if not re.search(u"^最后更新：\\d{4}-\\d{2}-\\d{2}（本地 · %s / 第 \\d+ 轮 / Round \\d+）" % R_TAG,
                 texts["ST"], re.M):
    die(u"STATE 缺「最后更新」行形状")
if len(re.findall(u"连续零改动 \\*\\*%s\\*\\* 轮" % STREAK_N, texts["ST"])) != 1:
    die(u"STATE 那一格形状不满足 353 的门（要「连续零改动 **%s** 轮」）" % STREAK_N)

orig = {k: rd(v) for k, v in FILES.items()}
if u"## 第 %d 轮" % ROUND in orig["UI"]:
    die(u"UI_AUDIT 已有第 %d 轮" % ROUND)
if re.search(u"(?m)^## Round %d · " % RD_N, orig["IT"]):
    die(u"ITERATION 已有 Round %d" % RD_N)
if u"**D-%d" % DN in orig["DEC"]:
    die(u"D-%d 已存在" % DN)
for n in (BLO,):
    if re.search(u"(?m)^\\*\\*%d\\. " % n, orig["BL"]):
        die(u"%d 已存在" % n)
if u"## %s 状态（" % R_TAG in orig["ST"]:
    die(u"STATE 已有 %s 节" % R_TAG)
if u"%s / 第 %d 轮" % (R_TAG, ROUND) in orig["CH"]:
    die(u"CHANGELOG 已有 %s" % R_TAG)
if orig["UI"].count(u"## 第 %d 轮" % (ROUND - 1)) != 1:
    die(u"UI_AUDIT 锚点不符")
if orig["ST"].count(u"## %s 状态（" % PREV_TAG) != 1:
    die(u"STATE 锚点不符（%s 节不唯一）" % PREV_TAG)
if orig["CH"].count(u"## [Unreleased]\n\n") != 1:
    die(u"CHANGELOG 锚点不符")

bl_lines = orig["BL"].splitlines(True)
h357 = [i for i, l in enumerate(bl_lines) if l.startswith(u"**360. ")]
if len(h357) != 1:
    die(u"360 锚点异常（%d 处）" % len(h357))
k357 = len(bl_lines)
later = [i for i in range(h357[0] + 1, len(bl_lines)) if re.match(u"\\*\\*\\d{3}\\. ", bl_lines[i])]
if later:
    k357 = later[0]
while bl_lines[k357 - 1].strip() == u"":
    k357 -= 1
if u"追记（%s 第一步）" % R_TAG in orig["BL"]:
    die(u"360 已有 %s 的同轮追记" % R_TAG)

# ── 报告 §13 三条 bullet + 标题/U 格/Sources 行 ─────────────────────
FR_WALK = (u"- **走到哪了**：阶段二累计 `## Round` 节 **@SECTIONS@** 节，最新一节是 **Round @RDN@**；"
           u"自评曲线末四个 @TAIL@ · @RDN@=@TOTAL@（现读 `curve_from_ledger.py` 的 `SCORES_BY_ROUND` 与 `ROUNDS`）。"
           u"派生分连续多轮低于 90 ⇒ 按目标继续修，不收口。\n")
FR_PRODUCT = (u"- **产品面（这一节最该被读的部分）**：产品面连续零改动轮数 = **@STREAK@**"
              u"（唯一取数口 `python3 scripts/product_streak.py --streak-for @ROUND@`：as-of 第 @ROUND@ 轮的"
              u"最后一笔产品提交是 @LASTSHA@ = 第 @LASTROUND@ 轮，即 R300 的代码半（那一笔改了 2 个文件：悬停环 0.55→0.30、"
              u"梯子顶档 0.85→0.92）；R301 / @PREV@ / 本轮都只动判据与工具。"
              u"这一格不许手抄：`--check` 会在台账与派生值不同源时拒绝这一版。\n")
FR_DOOR = (u"- **判据与门的规模**：脚本电池 **Ran @BATT@**（现读 `python3 -m unittest discover -s scripts/tests`）；"
           u"变异臂抽到 **@ARMS@** 把（现读预检 `ARM_TOTAL`，bad=0）；U 定义行 **@UDEF@ 条**、最大 **U-@UC@**"
           u"（`AGENT_UI_AUDIT.md`）；决定最大 **D-@DN@**；BACKLOG 最大 **@BLO@**。"
           u"最近这几轮立/改的门：0 告警能拦（343）、`pillReading` 带窗上界去掉（346）、commit-subject 对账与豁免退场（348）、"
           u"台账区间分箱（350）、产品面轮数只能由 `scripts/product_streak.py` 派生（353）、交互标记不许比一次数据变化更响（314/D-281）、"
           u"判据读数必须有能活下来的通道且名册不许空转（357/D-282）、名册的合法取值是派生集且棘轮双向（358/D-283）、"
           u"**读数名册登记的是名字不是通道；换通道那一轮要重量所有按旧通道写的名单（D-284）**。"
           u"本轮现读：判据文件 @FILES@ 份、用文件通道的 @EMITTERS@ 份、名册 @ROSTER@ 个、"
           u"仍在裸 stdout 的读数 **@BARE@ 行**（= 登记值；上一轮 57，本轮搬走 15 行 ⇒ 360 的第一步）；"
           u"Swift 那张按文件的读数名册合计 **@SWTOT@ 行**（探针那份 @SWPROBE@ 行 / @SWMARK@ 种标记，已改成按通道读）；"
           u"三张名单并存缺一处上游 ⇒ 新开 @BLO@。取证目录本轮重量：@VLINES@ 行里热图 marker 仍 **@VHEAT@ 行** ⇒ 359 仍开。\n")

SUBS2 = dict(SUBS)
SUBS2[u"@UDEF@"] = s(U_DEFS + 3)
fr = orig["FR"]
repl = []
for label, tpl in ((u"走到哪了", FR_WALK), (u"判据与门的规模", FR_DOOR),
                   (u"产品面（这一节最该被读的部分）", FR_PRODUCT)):
    a, b = bullet(fr, label)
    repl.append((a, b, fill_tpl(tpl, SUBS2)))
a, b = bullet(fr, u"仍开（截至本轮，完整名单以 `AGENT_STATE.md` 的 %s 节 ② 为准）" % PREV_TAG)
fr_still = fr[a:b]
fr_still = fr_still.replace(
    u"360（57 行裸 stdout 按文件搬进通道）",
    u"360（第一步已做，剩 %s 行）、%d（三张名单并存，缺一处上游）" % (BARE, BLO))
fr_still = fr_still.replace(u"357（判据读数的本地通道）、", u"")   # 过期条目：357 已于 R301 结案
fr_still = re.sub(u"%s 节 ②" % PREV_TAG, u"%s 节 ②" % R_TAG, fr_still)
if u"%s 节 ②" % R_TAG not in fr_still:
    die(u"§13 的仍开 bullet 没指向本轮的 STATE 节 ⇒ 指针过期")
if u"%d（三张名单并存" % BLO not in fr_still or u"357（判据读数的本地通道）" in fr_still:
    die(u"§13 的仍开 bullet 没落到本轮的形状（缺 361，或 357 的过期条目没清）")
repl.append((a, b, fr_still))
repl.sort(key=lambda t: t[0], reverse=True)
fr_new = fr
for a, b, txt in repl:
    fr_new = fr_new[:a] + txt + fr_new[b:]

fr_new, n_title = re.subn(u"R9–R\\d+，\\d+ 轮自评",
                          u"R9–R%d，%s 轮自评" % (RD_N, SUBS2[u"@SECTIONS@"]), fr_new, count=1)
if n_title != 1:
    die(u"报告标题那一格没命中（%d 处）" % n_title)
fr_new, n_ucell = re.subn(u"U-31 … U-\\d+（R\\d+ 现读抬到最新一节）（?:R\\d+ 现读抬到最新一节）*|U-31 … U-\\d+",
                          u"U-31 … U-%d（@RTAG@ 现读抬到最新一节）" % UC,
                          fr_new, count=1)
if n_ucell != 1:
    die(u"§1 的 U 上界那一格没命中（%d 处）" % n_ucell)
fr_new = fill_tpl(fr_new, SUBS2)
# Sources 那一格本轮不刷（产品没动）——但必须确认它仍然指向 as-of 的那一笔，否则说明 §1 在说谎
sources_row = u"**%s**（commit `%s`）" % (u"R%d" % (int(LAST_ROUND) + 1), LAST_SHA)
if sources_row not in fr_new:
    die(u"§1 的 Sources 那一格不指向 as-of 读到的 @LASTSHA@ ⇒ 要么账错了，要么取数口错了"
        .replace(u"@LASTSHA@", LAST_SHA))
if u"scripts/product_streak.py" not in fr_new:
    die(u"报告里找不到取数口引用 ⇒ 353 的修法被回退了，先查")

new = {
    "UI": orig["UI"].replace(u"## 第 %d 轮" % (ROUND - 1), texts["UI"] + u"## 第 %d 轮" % (ROUND - 1), 1),
    "IT": orig["IT"].rstrip(u"\n") + u"\n\n" + texts["IT"].strip(u"\n") + u"\n",
    "DEC": orig["DEC"].rstrip(u"\n") + u"\n" + texts["DEC"].strip(u"\n") + u"\n",
    "BL": (u"".join(bl_lines[:k357]).rstrip(u"\n") + u"\n\n" + texts["BL"].strip(u"\n")
           + u"\n\n" + u"".join(bl_lines[k357:]).lstrip(u"\n")),
    "ST": orig["ST"].replace(u"## %s 状态（" % PREV_TAG, texts["ST"] + u"## %s 状态（" % PREV_TAG, 1),
    "CH": orig["CH"].replace(u"## [Unreleased]\n\n", u"## [Unreleased]\n\n" + texts["CH"], 1),
    "FR": fr_new,
}
for key in new:
    if key != u"FR" and len(new[key]) <= len(orig[key]):
        die(u"%s 写后不比写前长 ⇒ 可能是替换而不是插入" % key)
sec = re.compile(u"(?m)^## 13\\. .*?(?=^## |\\Z)", re.S)
old_sec, new_sec = sec.search(orig["FR"]), sec.search(new["FR"])
if not (old_sec and new_sec):
    die(u"§13 那一节在写前或写后不见了")
n_old = len(re.findall(u"(?m)^- \\*\\*", old_sec.group(0)))
n_new = len(re.findall(u"(?m)^- \\*\\*", new_sec.group(0)))
if n_new < n_old:
    die(u"§13 的 bullet 从 %d 条变成 %d 条 ⇒ 有内容被吞了" % (n_old, n_new))
if (u"产品面连续零改动轮数 = **%s**" % STREAK_N) not in new["FR"]:
    die(u"报告的 streak 那一格没落成本轮的值")

for key, text in new.items():
    wr(FILES[key], text)

sh(["python3", REFRESH])

post, err = battery(u"写盘后", u"/tmp/r303_battery_post.log")
if post is None:
    for key, text in orig.items():
        wr(FILES[key], text)
    die(u"写盘后电池不绿 ⇒ 七本已整体还原：" + err)
if post != pre:
    for key, text in orig.items():
        wr(FILES[key], text)
    die(u"电池计数变了（" + str(pre) + u" → " + str(post) + u"）⇒ 七本已还原")

cout, crc2 = sh(["python3", STREAK, u"--check"])
if crc2 != 0:
    for key, text in orig.items():
        wr(FILES[key], text)
    die(u"353 的门不认这版台账 ⇒ 七本已还原：" + (cout + u"\n").strip()[-400:])

cv2, _ = sh(["python3", CURVE])
byround2 = (re.findall(u"(?m)^SCORES_BY_ROUND (.*)$", cv2, re.M) or [u""])[-1]
score = dict(re.findall(u"(\\d{3})=(\\d{2,3})", byround2)).get(s(RD_N), u"?")
if score == u"?":
    die(u"曲线里没有 Round %d 的分数 ⇒ ITERATION 那一节没落地" % RD_N)
gaps = (re.findall(r"^GAPS=(\S+)", cv2, re.M) or [u"?"])[-1]
print(u"LEDGERS_R303 OK batt=Ran " + post[0] + u" (skipped=" + post[1] + u", 名单=" + str(post[2])
      + u") streak=" + STREAK_N + u" prod=0 bare=" + BARE + u"/" + CEIL + u" roster=" + ROSTER_N
      + u" bare=" + BARE + u"/" + CEIL + u" roster=" + ROSTER_N + u" swift=" + vk[u"swift_executed"] + u"/" + vk[u"swift_failures"]
      + u" knives=" + KC + u"/" + KN + u" U=" + s(UA) + u".." + s(UC) + u" D=" + s(DN)
      + u" BACKLOG_new=" + s(BLO) + u" derived_score(Round " + s(RD_N) + u")=" + s(score)
      + u" GAPS=" + gaps)
