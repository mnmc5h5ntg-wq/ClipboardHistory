#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R304（第 303 轮 / Round 301）的七本台账落盘 —— 事务性，与 ledgers_r303 同一形状。

本轮**不动产品**（只动 Tests / scripts / .scratch），所以 streak 由取数口按 as-of 第 303 轮现读（=4），
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
VERIFY_LOG = "/tmp/r304_verify_run.log"
VERIFY_READINGS = "/tmp/r304_verify/frames/capture-readings.log"
SWIFT_ROSTER = os.path.join(ROOT, "ClipboardHistory", "Tests", "ClipboardHistoryAppTests",
                               "FrameIntervalBudgetTests.swift")
COV_ROLL = os.path.join("scripts", "tests", "test_readings_channel_coverage.py")
CURVE = os.path.join(ROOT, ".scratch", "motion-audit-2", "curve_from_ledger.py")
STREAK = os.path.join(ROOT, "scripts", "product_streak.py")
PRECHECK = os.path.join(ROOT, ".scratch", "motion-audit-2", "mutate_needle_precheck.py")
KNIVES = os.path.join(ROOT, ".scratch", "motion-audit-2", "mutate_r304.py")
KNIVES_R303 = os.path.join(ROOT, ".scratch", "motion-audit-2", "mutate_r303.py")
KNIVES_195 = os.path.join(ROOT, ".scratch", "motion-audit-2", "mutate_r195.py")
KNIVES_196 = os.path.join(ROOT, ".scratch", "motion-audit-2", "mutate_r196.py")
REFRESH = os.path.join(ROOT, ".scratch", "motion-audit-2", "refresh_report_section1.py")
DIMS = [u"真实视觉审查", u"判据有效性", u"假绿防御", u"产品面推进", u"台账一致性",
        u"交付诚实性", u"可复核性"]
SCORES = [11, 14, 14, 4, 14, 14, 14]
R_TAG = u"R304"
R_NEXT = u"R305"
PREV_TAG = u"R303"
TODAY = subprocess.check_output([u"date", u"+%Y-%m-%d"]).decode().strip()
# ⓪ 的成对号（本轮现读，只登记不轮询 = R140）
CI_LINE = os.environ.get("R304_CI_LINE", u"CI 通道本轮读到一半就断（`gh run list` ⇒ EOF），成对号未读 ⇒ @RNEXT@ 开场第一件事就是重读 ①②③ 那三件事对应的两跑")


def s(x):
    return str(x)


def die(m):
    sys.stderr.write(u"LEDGERS_R304 REFUSED: " + m + u"\n")
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
if LAST_ROUND != s(ROUND - 4):
    die(u"as-of 第 %d 轮读到的最后一笔产品提交是第 %s 轮 ⇒ 与本轮（第 %d 轮）差四格，先查"
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
# 一次「把读数搬进文件通道」要动几处？本轮把这件事数出来（R303 开的 361 的具体尺寸）。
TESTS_DIR = os.path.join(ROOT, "ClipboardHistory", "Tests", "ClipboardHistoryAppTests")
MOVED = ["MotionDriverTests.swift", "PressFeedbackTests.swift", "SettingsFailureReceiptTests.swift"]
emitted = 0
for name in MOVED:
    emitted += rd(os.path.join(TESTS_DIR, name)).count(u"CaptureReadings.emit(")
cov_src = rd(os.path.join(ROOT, "scripts", "tests", "test_readings_channel_coverage.py"))
NAMED_LEFT = len(re.findall(u'^\\s+"[\\w.]+[.]swift": \\d+', cov_src, re.M))
roster_src = rd(FILES["UI"]) if False else rd(os.path.join(TESTS_DIR, "UICaptureHarness.swift"))
CH_ROSTER = len(re.findall(u'"[\\w.]+[.]swift"', roster_src[roster_src.index(u'let roster = ['):roster_src.index(u']\n', roster_src.index(u'let roster = ['))]))
ch_src = rd(os.path.join(TESTS_DIR, "FrameIntervalBudgetTests.swift"))
CH_CHANNEL = len(re.findall(u'"[\\w.]+[.]swift"', ch_src[ch_src.index(u'let emitChannel: Set<String> = ['):ch_src.index(u']\n', ch_src.index(u'let emitChannel: Set<String> = ['))]))
TOUCHES = (u'搬动本身 %d 处调用 + 名册 2 张（Swift 通道名册 %d 个名字、Swift 名字名册的 emitChannel %d 个名字）'
           u'+ 电池那一卷的登记值 1 处与按文件未覆盖名单 %d 条'
           % (emitted, CH_ROSTER, CH_CHANNEL, NAMED_LEFT))
if emitted < 10 or CH_ROSTER < 12 or CH_CHANNEL < 3:
    die(u"同步点的数读不出合理形状（emitted=%s roster=%s channel=%s）⇒ 有几处漂了，先读再写"
        % (emitted, CH_ROSTER, CH_CHANNEL))
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
KS = re.findall(u"(?m)^R304_MUTATE 刀=(\\d+) CAUGHT=(\\d+) ESCAPED=(\\d+) NOT_RUN=(\\d+) "
                u"RESTORE_CLEAN=(\\w+)", kout)
if krc != 0 or not KS:
    die(u"本轮刀表不是全 CAUGHT（rc=%s）：%s" % (krc, kout.strip()[-400:]))
KN, KC, KE, KNR, KREST = KS[-1]
# 被本轮改动弄哑的两张历史表：重钉之后必须真的还能红（DID-NOT-RUN / ESCAPED 都不算修好）
hist = {}
for tag, path in ((u"r195", KNIVES_195), (u"r196", KNIVES_196), (u"r303", KNIVES_R303)):
    hout, hrc = sh(["python3", path])
    hs = re.findall(u"(?m)^%s_MUTATE 刀=(\\d+) CAUGHT=(\\d+) ESCAPED=(\\d+) NOT_RUN=(\\d+) "
                    u"RESTORE_CLEAN=(\\w+)" % tag.upper(), hout)
    if hrc != 0 or not hs or hs[-1][2] != u"0" or hs[-1][3] != u"0" or hs[-1][4] != u"yes":
        die(u"历史刀表 %s 本轮之后仍不干净（rc=%s）：%s" % (tag, hrc, hout.strip()[-300:]))
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
if (U_MAX, D_MAX, BL_MAX) != (994, 284, 361):
    die(u"最大编号与本轮取靶时不符（读到 U-%d / D-%d / BACKLOG-%d）⇒ 有别的会话先动了账"
        % (U_MAX, D_MAX, BL_MAX))
UA, UB, UC = U_MAX + 1, U_MAX + 2, U_MAX + 3
UD = U_MAX + 4
UE = U_MAX + 5
DN, BLO = D_MAX + 1, BL_MAX + 1
U_DEFS = len(re.findall(u"(?m)^- \\*\\*U-\\d{3}[：(]", ui))

pre, err = battery(u"写盘前", u"/tmp/r304_battery_pre.log")
if pre is None:
    die(err)

TOTAL = sum(SCORES)
ROWS = u"\n".join(u"| %s | %d/15 |" % (d, sc) for d, sc in zip(DIMS, SCORES))

SUBS = {
    u"@RTAG@": R_TAG, u"@PREV@": PREV_TAG, u"@RNEXT@": R_NEXT,
    u"@ROUND@": s(ROUND), u"@RDN@": s(RD_N),
    u"@UA@": s(UA), u"@UB@": s(UB), u"@UC@": s(UC), u"@UD@": s(UD), u"@UE@": s(UE),
    u"@DN@": s(DN), u"@BLO@": s(BLO),
    u"@STREAK@": STREAK_N, u"@LASTSHA@": LAST_SHA, u"@LASTROUND@": LAST_ROUND,
    u"@MAXROUND@": MAX_ROUND, u"@CM@": vk[u"baseline_compared"], u"@CH@": vk[u"baseline_changed"],
    u"@FRAMES@": vk[u"frames"], u"@SWIFT@": vk[u"swift_executed"], u"@SWFAIL@": vk[u"swift_failures"],
    u"@Dmg@": vk[u"dmg"], u"@VER@": vk[u"installed_version"], u"@WARN@": vk[u"build_warnings"],
    u"@ROWS@": ROWS + u"\n", u"@TOTAL@": s(TOTAL), u"@BATT@": pre[0], u"@SKIP@": pre[1],
    u"@ARMS@": ARMS, u"@KN@": KN, u"@KC@": KC, u"@KREST@": KREST, u"@TODAY@": TODAY,
    u"@SECTIONS@": s(int(SECTIONS) + 1), u"@TAIL@": TAIL_OLD, u"@CI_LINE@": CI_LINE,
    u"@TOUCH@": TOUCHES, u"@NAMED@": s(NAMED_LEFT),
    u"@FILES@": FILES_SCANNED, u"@EMITTERS@": EMITTERS, u"@ROSTER@": ROSTER_N,
    u"@BARE@": BARE, u"@CEIL@": CEIL, u"@UNCOVFILES@": UNCOV_FILES, u"@UNCOSUM@": UNCOV_SUM,
    u"@WORSTFILE@": WORST_FILE, u"@WORSTN@": WORST_N,
    u"@VHEAT@": s(VERIFY_HEAT), u"@VLINES@": s(VERIFY_LINES), u"@APPEAR@": APPEAR,
    u"@SWTOT@": sw_tot, u"@SWFILES@": sw_files, u"@SWMARK@": sw_markers,
    u"@SWPROBE@": sw_probe,
    u"@K195@": hist[u"r195"][0] + u"/" + hist[u"r195"][1],
    u"@K196@": hist[u"r196"][0] + u"/" + hist[u"r196"][1],
}


# ⓪ 那一栏从 shell 传进来，里面允许带占位符（写它的人想引用本轮的号）——
# 先把它自己填一遍，再塞回 SUBS，否则整条模板替换只做一次，@UE@ 这类二级记号会原样进账
# （R304 的写盘前自扫就是被这一格逼出来的：填不上的洞落进台账后没有任何东西会读）。
CI_LINE = fill_tpl(CI_LINE, SUBS)
SUBS[u"@CI_LINE@"] = CI_LINE

def fill(t):
    return fill_tpl(t, SUBS)


UI_NEW = u"""## 第 @ROUND@ 轮（@RTAG@ · U-@UA@…U-@UE@ · @TODAY@）：第二批裸 stdout 搬完，顺手把「一次搬动要同步几处」数出来

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
- **U-@UD@：台账自己也被同一族的洞咬过，而且洞就在「现读」那两个字后面 —— 本轮数出 11 个并把它们填回。**
  写这一节的生成器自己的键写错一格（注册成复数、正文写单数）就当场抓到一枚没替换的占位符；顺着同一形状
  扫七本台账（`scripts/tests/test_ledger_tokens.py`），另有 **11 处历史洞**是历轮落盘时留下的：
  BACKLOG 346 的「R296 结案」追记 7 处（那道 0 告警门的 warnings / incremental / cold / target 与刀的 CAUGHT / RESTORE_CLEAN），
  305 的「R295」追记 4 处（`pairDelta` 的亮暗两侧自家与系统变颗平均）。也就是说这两格账在落盘之后
  **从来没有被读过** —— 尤其 346 那一格正文写的正是「本机基线现读」。两处的值都从别处的同一批现读记录取回
  （346 ← 同一单上一条「代码半」追记 + UI_AUDIT 第 295 轮的门行；305 ← 347 的追记 + `AGENT_DECISIONS.md` + 报告 §13，
  亮 29 对 52、暗 21 对 18），并在台账里注明是取回而不是补的估计。
  新门四格：正对照（注入三种真实漏法都要数出来）、反对照（`@MainActor` 一类属性标注、`@1x` 倍率写法、邮箱都不算洞，
  冤枉人的门会被绕）、名单不许空转（七本都要在盘上且各大于 20000 字符）、正题（现读 stray=0）。
  这一族归到 348 的第二格（写台账本身没有门）下追记，不另开单。

- **U-@UE@：⓪ 那条「成对号」的取数假设被本轮量穿了 —— 一轮里 push 的中间那几笔 commit 根本没有 run。**
  `811c4fc`（R303 的账半）→ run 39825878608 **completed / failure**，红在 STEP[18] On-screen probe coverage floor，
  正文是 `NOW_RUNS testOffScreenProgrammaticSelectionIsRevealedAndNotJumped：登记说 runner 跑不了，而这次它下结论了（passed）` ⇒
  照 runner 自己的点名把 `scripts/probe_coverage_expectations.json` 那一格翻回 can，并把
  `test_todays_expectations_pair_green_with_todays_fixture` 的「红只许落在这几条」名单从两条抬成三条
  （**不改夹具** —— 让旧读数替现在作证是 R194 那一条；夹具老了就以 NOT_RUN 的身份红出来，登记对了它自己会闭嘴）。
  另一半是取数口：逐笔按 `actions/runs?head_sha=` 查，`b420967` / `4adc04f` / `5713c89` 的 **total_count=0**，
  而 `811c4fc` / `8c63c46` / `ac1ed6b` / `8f6c300` / `f5a563a` 各有 1 跑。也就是说台账连着几轮写的那句
  「不在最近 10 跑里（未读）」是**结构性不存在**而不是待读 —— 成因是 push 边界（一次 push 只给 tip 那笔建 run），
  把它记成未读就是每轮重读一次不存在的东西。⇒ 新开 @BLO@，并把本轮 ⓪ 改写成「按 push 的 tip 列成对号」。
  
本轮产品文件 0 个（Tests / scripts / .scratch），连续零改动 **@STREAK@** 轮
（现读 `python3 scripts/product_streak.py --streak-for @ROUND@`：as-of 第 @ROUND@ 轮的最后一笔产品提交是
@LASTSHA@ = 第 @LASTROUND@ 轮，即 R300 的代码半）。四件套现读：全量卷 @SWIFT@ / 失败 @SWFAIL@、
build 告警 @WARN@、帧 @FRAMES@ 张 compared=@CM@ changed=@CH@、dmg=@Dmg@、换装 @VER@。
看图腿：本轮无新帧（产品 0 文件），读的是通道与名单的数；四件套取证目录 @VLINES@ 行里热图 marker
仍 @VHEAT@ 行 ⇒ 359 仍开（重量，不沿用）。

"""

ITER_NEW = u"""## Round @RDN@ · @RTAG@（第 @ROUND@ 轮 · @TODAY@）：第二批搬进文件通道，同步点第一次被数出来

本轮做的事：把 `MotionDriverTests` / `PressFeedbackTests` / `SettingsFailureReceiptTests` 三份里
13 行只走 stdout 的读数改走 `CaptureReadings.emit`，覆盖率棘轮 42 → 现读 @BARE@，
派生名册 11 → @ROSTER@ 个；给 Swift 那张名字名册补一张**显式通道表**（`emitChannel`），
因为上一轮的「单文件特例」在多搬一份之后就会变成静默失效的洞。
两把新刀 M878 / M879 分别钉「通道表被删名字」与「搬好的读数被写回 print」。
本轮又踩并当场修好的：`R303` 的三根 needle 有两根的期望值是上一轮的数字（42 / 43）、
名册形状也随本轮变化 ⇒ 预检 bad=2、表里 ESCAPED=1 ⇒ 重钉后三张表全 CAUGHT。
还有一件是往回看的：本轮自己的生成器先把一个占位符写漏（键注册成复数、正文写单数），
顺着这个形状去扫七本台账，数出**历史上还有 11 处**没被替换的洞 —— 346 的 R296 结案追记 7 处、
305 的 R295 追记 4 处，两处正文都写着「现读」。两格都就地填回真值并注明来源，
新增 `scripts/tests/test_ledger_tokens.py`（正／反／名单不空转／正题四格）与本生成器的写盘前自扫。

七维度自评：
| 维度 | 分/满分 |
| --- | --- |
@ROWS@| 合计 | @TOTAL@/105 |

为什么不是满分（逐条）：真实视觉审查 11 —— 无新帧，读的是名单与行数；产品面推进 4 —— 0 个产品文件、
连续 @STREAK@ 轮（这一维欠的是 347 的真机证人，门在用户那边）；判据有效性 14 —— 两把新刀各钉一侧，
外加三根被本轮弄哑又复活的针；假绿防御 14 —— 通道表从「一个 if」变成一张名单，删名字会红；
台账一致性 14 —— 棘轮 / 名单 / 通道表三个数全部现读，同步点数量本身也现读成 @TOUCH@；同一轮第一次去读
**台账自己**：数出历史两格留下的 11 个未替换占位符（346 的 7 个、305 的 4 个）并就地填回，
新增 `scripts/tests/test_ledger_tokens.py` 与生成器的写盘前自扫；
交付诚实性 14 —— 359 与「哪几跑 CI 未读」都重量而不沿用；可复核性 14 —— 361 从一句抱怨变成可数的尺寸。

派生分由 `curve_from_ledger.py` 现读，不手抄。
未做（逐条）：① **305 的台阶地板**（等 347 的真机证人）；② 354 的第二步（动效地板登记成按机器×按用例的
有名字未覆盖，出现率 @APPEAR@）；③ 361（同步点已被数出来，合并成一处派生还没做）；④ 360 剩下的
@NAMED@ 份文件 @BARE@ 行；⑤ 359（取证目录没有汇聚点）；⑥ 348 的「数字对不对」那一格、349、350 第二步、351、344、
341 的 CI 契约半、339、312 具名出口、304、291；⑦ 用户闸门 220 路 A / 228② / 265；⑧ @BLO@（⓪ 的成对号要按 push 的 tip 列，本轮量到 3 笔的 total_count=0）。

"""

DEC_NEW = u"""**D-285（@RTAG@）：一次「把读数搬进文件通道」要同步的地点数量，必须是本轮读出来的数字，并且每一处都要有刀。**
理由与尺寸：R303 立的是「名单要登记名字而不是通道」，本轮把它落成一张显式 `emitChannel` 名单；
而这次搬迁实测的同步点是 @TOUCH@（判据源码的调用、Swift 通道名册、Swift 名字名册的通道表、
电池那一卷的登记值与按文件未覆盖名单）。任何一处单独忘记都有两种收场：某一格红（可接受），
或者**那份清单凭空变空而守卫仍绿**（不可接受 —— R303 的 M731 就是这个形状被刀照出来的）。
所以处置固定为三步：① 每搬一份就在同一轮改登记值，让棘轮现读等于登记值；
② 通道表加名字，并配一把「从表里删名字」的刀（M878）；③ 跑预检，把「needle 命中 0 次 / 期望值是上一轮的数字」
当成本轮产出重钉后重跑（本轮 `R303` 的三根里两根正是这种坏法）。
"""

NOTE_360 = u"""  追记（@RTAG@）：361 那句「三张名单并存」在本轮被量成具体尺寸 —— 搬一份判据卷的读数要同步 @TOUCH@。
  本轮把这四处都改了并各配刀（M879 钉「登记值/名单」那一侧，M878 钉「Swift 通道表」那一侧），
  但这只是把漏同步变成「会红」，还没变成「只有一处要改」。
  下一步的顺序因此定下来：先把同步点数量做成读数（@TOUCH@ 就是它），再谈合并成一份上游数据。
  另：本轮把 `R303_MUTATE` 的三根 needle 重钉了一遍 —— 其中两根的期望值写的是**上一轮的数字**，
  这就是「放宽要成对」之外另一种腐烂：刀表的期望值也是台账，也要现读。
"""

ITEM_BLO = u"""\n**@BLO@. ⓪ 的「run ↔ commit 成对号」是按 commit 列的，而一次 push 只给最后那一笔建 run（R304 现读：`b420967` / `4adc04f` / `5713c89` 用 `actions/runs?head_sha=` 查各得 total_count=0，而同轮的 `811c4fc` / `8c63c46` / `ac1ed6b` / `8f6c300` / `f5a563a` 各有一跑）**：连着两轮（R303、R304 之前的 R302）我把这些写成「不在最近 10 跑里（未读）」并交给下一轮继续补读 —— 那是把**结构性不存在**记成**待办**，它永远不会被读到，而每一轮的 ⓪ 都要为它写一行『仍未交』。两条候选修法（都要先量再选，别先写门）：① ⓪ 那一栏只登记**每次 push 的 tip**（git 侧现取：`git log --format=%H origin/main ^(<上一轮 push 的 tip>)` 的最后一笔），列出的号必须逐笔 `head_sha` 查得到 ≥1 跑，查不到就写「不存在（push 边界）」而不是「未读」；② 要逐笔证据就把一轮拆成两次 push（代码半与账半各一次）—— 代价是同轮 CI 次数翻倍，而且要回答「中间那笔的 run 到底证明了什么」（它没带本轮台账，结论本就属于 tip 那一跑）。本轮先按 ① 的写法改 ⓪，门留欠：未读数不许超过 0 条「不存在」的形态，除非每一笔都在 `head_sha` 上量过。\n"""


NOTE_348 = u"""  追记（@RTAG@）：本单的「台账没写上 / 写错了都不会红」那一族，本轮被抓到第三种形状 —— **占位符没被替换**。
  两处都是历史账面：346 的「R296 结案」追记留着 7 个洞（那道 0 告警门的 warnings / incremental / cold / target
  加刀的 CAUGHT 两个数与 RESTORE_CLEAN），本单 305 那位邻居的「R295」追记留着 4 个洞（`pairDelta` 的亮暗×自家系统
  变颗平均）。两处正文都写着「现读」，而现读那两个字后面是模板原文 —— 也就是说这两格落盘之后从没被读过。
  成因与本单 ① ② 同一条：写台账那一次没有任何东西读那一格，插入照常成功、电池照常绿。
  本轮做了三件事：① 两处就地填回真值并注明取值来源（346 ← 同一单上一条「代码半」追记 + UI_AUDIT 第 295 轮的门行；
  305 ← 347 的追记 + `AGENT_DECISIONS.md` + 报告 §13，亮 29 对 52 / 暗 21 对 18），② 新增
  `scripts/tests/test_ledger_tokens.py`（扫七本台账，出现「at 号夹着的大写词」即红；四格里有正对照、反对照、
  名单不许空转），③ 本轮的生成器在写盘**之前**先自扫一遍（洞在插入文本里就直接拒绝，七本一起还原）。
  本单剩下的：subject 那一格已自定位（R298），区间对账已上（R298），**「台账内容有没有被读过」这条仍只覆盖占位符形状**，
  数字对不对仍靠各格自己的取数口 —— 不许把这一格读成「写台账有门了」。
"""





CHG_NEW = (u"### Improved（@RTAG@ / 第 @ROUND@ 轮 / Round @RDN@ · 第二批裸 stdout 搬进文件通道）\n\n"
           u"360 的第二批：`MotionDriverTests`（3 行）、`PressFeedbackTests`（5 行）、`SettingsFailureReceiptTests`（5 行）"
           u"里的读数改走 `CaptureReadings.emit`，覆盖率棘轮 42 → 现读 @BARE@，派生名册 11 → @ROSTER@ 个，"
           u"按文件的未覆盖名单剩 @NAMED@ 条。Swift 那张名字名册补一张**显式通道表** `emitChannel`："
           u"上一轮靠 `file == 某一份` 判断走哪条腿，多搬一份之后那种特例就会让清单凭空变空而守卫仍绿。"
           u"两把新刀：M878 从通道表里删一个名字 ⇒ Swift 侧红在与名册不符；M879 把一行改回裸 stdout ⇒ 电池红在盘上有 30 行。"
           u"同轮把 `R303_MUTATE` 三根 needle 重钉（两根的期望值写的是上一轮的数字 42 / 43，预检 bad=2）⇒ 三张表全 CAUGHT，"
           u"预检 bad=0、ARM_TOTAL=@ARMS@。给 361 补一条实测尺寸：一次搬动要同步 @TOUCH@。"
           u"359 重量：四件套取证目录 @VLINES@ 行里热图 marker 仍 @VHEAT@ 行 ⇒ 仍开。"
           u"另往回查了台账自己：本轮生成器把一个占位符的键注册成复数、正文写单数 ⇒ 顺着这个形状扫七本账，"
           u"数出历史遗留的 11 处未替换洞（346 的 R296 结案追记 7 处、305 的 R295 追记 4 处，两处正文都写着「现读」），"
           u"就地按别处的同一批现读记录填回，并新增 `scripts/tests/test_ledger_tokens.py`（4 格）与生成器的写盘前自扫。"
           u"产品文件 0 个；四件套现读：全量卷 @SWIFT@/失败 @SWFAIL@、告警 @WARN@、帧 @FRAMES@ 张 changed=@CH@、"
           u"dmg=@Dmg@、换装 @VER@；电池 Ran @BATT@ / OK (skipped=@SKIP@)。\n\n")

STATE_NEW = u"""## @RTAG@ 状态（第 @ROUND@ 轮 / Round @RDN@ · @TODAY@）

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
台账自己第一次被读：本轮生成器把一个占位符的键写成复数 ⇒ 顺着形状扫七本账，数出历史遗留 **11 处未替换的洞**
（346 的 R296 结案追记 7 处、305 的 R295 追记 4 处，正文都写着「现读」），按别处的同一批现读记录填回，
并补 `scripts/tests/test_ledger_tokens.py`（4 格）+ 生成器写盘前自扫 —— 这一格归 348，不另开单。
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
@BLO@（⓪ 的成对号按 commit 列；本轮量到 3 笔根本没有 run）、
359（取证目录没有读数汇聚点，本轮重量仍是 @VHEAT@ 行）、356（悬停换形状的三条候选）、348 的「数字对不对」那一格、
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
if nums != [UA, UB, UC, UD, UE]:
    die(u"节内 U 定义行与标题区间不吻合：%s vs %s" % (nums, [UA, UB, UC, UD, UE]))
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
for n in ():
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
h357 = [i for i, l in enumerate(bl_lines) if l.startswith(u"**361. ")]
if len(h357) != 1:
    die(u"361 锚点异常（%d 处）" % len(h357))
k357 = len(bl_lines)
later = [i for i in range(h357[0] + 1, len(bl_lines)) if re.match(u"\\*\\*\\d{3}\\. ", bl_lines[i])]
if later:
    k357 = later[0]
while bl_lines[k357 - 1].strip() == u"":
    k357 -= 1
if u"追记（%s）" % R_TAG in orig["BL"]:
    die(u"361 已有 %s 的同轮追记" % R_TAG)

# ── 报告 §13 三条 bullet + 标题/U 格/Sources 行 ─────────────────────
FR_WALK = (u"- **走到哪了**：阶段二累计 `## Round` 节 **@SECTIONS@** 节，最新一节是 **Round @RDN@**；"
           u"自评曲线末四个 @TAIL@ · @RDN@=@TOTAL@（现读 `curve_from_ledger.py` 的 `SCORES_BY_ROUND` 与 `ROUNDS`）。"
           u"派生分连续多轮低于 90 ⇒ 按目标继续修，不收口。\n")
FR_PRODUCT = (u"- **产品面（这一节最该被读的部分）**：产品面连续零改动轮数 = **@STREAK@**"
              u"（唯一取数口 `python3 scripts/product_streak.py --streak-for @ROUND@`：as-of 第 @ROUND@ 轮的"
              u"最后一笔产品提交是 @LASTSHA@ = 第 @LASTROUND@ 轮 = R300 的代码半（悬停环 0.55→0.30、梯子顶档 0.85→0.92）；"
              u"之后 R301 / R302 / R303 / 本轮都只动判据与工具。这一格不许手抄，`--check` 会拒绝不同源的版本。\n")
FR_DOOR = (u"- **判据与门的规模**：脚本电池 **Ran @BATT@**（现读 `python3 -m unittest discover -s scripts/tests`）；"
           u"变异臂抽到 **@ARMS@** 把（现读预检 `ARM_TOTAL`，bad=0）；U 定义行 **@UDEF@ 条**、最大 **U-@UE@**"
           u"（`AGENT_UI_AUDIT.md`）；决定最大 **D-@DN@**；BACKLOG 最大 **361**。"
           u"最近这几轮立/改的门：0 告警能拦（343）、带窗上界去掉（346）、commit-subject 对账与豁免退场（348）、"
           u"台账区间分箱（350）、产品面轮数只能由 git 派生（353）、交互标记不许比一次数据变化更响（314/D-281）、"
           u"读数必须有能活下来的通道（357/D-282）、名册取值是派生集且棘轮双向（358/D-283）、"
           u"名册登记名字不登记通道（360 第一批/D-284）、**一次搬动的同步点数量要现读且每处配刀（D-285）**。"
           u"本轮现读：判据文件 @FILES@ 份、用文件通道的 @EMITTERS@ 份、名册 @ROSTER@ 个、"
           u"仍在裸 stdout 的读数 **@BARE@ 行**（= 登记值；两批之前是 57）；Swift 名字名册合计 @SWTOT@ 行、"
           u"通道表 @TOUCH@。取证目录本轮重量：@VLINES@ 行里热图 marker 仍 **@VHEAT@ 行** ⇒ 359 仍开。\n")

SUBS2 = dict(SUBS)
# 定义行数量从**渲染后的正文**数，不写魔法数（这一格在 R303 之前是 `+3` 硬编码，加一节就得改一次，
# 忘了改就是报告里那个「U 定义行 N 条」停在旧数上）。
NEW_U_DEFS = len(re.findall(u"(?m)^- \\*\\*U-\\d{3}[：(]", texts["UI"]))
if NEW_U_DEFS != 5:
    die(u"本轮那一节的 U 定义行数=%d（要 5）⇒ 报告那一格会记错" % NEW_U_DEFS)
SUBS2[u"@UDEF@"] = s(U_DEFS + NEW_U_DEFS)
fr = orig["FR"]
repl = []
for label, tpl in ((u"走到哪了", FR_WALK), (u"判据与门的规模", FR_DOOR),
                   (u"产品面（这一节最该被读的部分）", FR_PRODUCT)):
    a, b = bullet(fr, label)
    repl.append((a, b, fill_tpl(tpl, SUBS2)))
a, b = bullet(fr, u"仍开（截至本轮，完整名单以 `AGENT_STATE.md` 的 %s 节 ② 为准）" % PREV_TAG)
fr_still = fr[a:b]
fr_still = fr_still.replace(
    u"360（第一步已做，剩 42 行）、361（三张名单并存，缺一处上游）",
    u"360（已搬两批，剩 %s 行）、361（同步点已数出，尚未合并）、" u"%s（⓪ 的成对号按 commit 列，本轮量到 3 笔根本没有 run）" % (BARE, BLO))
fr_still = fr_still.replace(u"357（判据读数的本地通道）、", u"")   # 过期条目：357 已于 R301 结案
fr_still = re.sub(u"%s 节 ②" % PREV_TAG, u"%s 节 ②" % R_TAG, fr_still)
if u"%s 节 ②" % R_TAG not in fr_still:
    die(u"§13 的仍开 bullet 没指向本轮的 STATE 节 ⇒ 指针过期")
if (u"%s（⓪ 的成对号" % BLO) not in fr_still:
    die(u"§13 的仍开 bullet 没把本轮新开的 @BLO@ 记进去 ⇒ 报告比 STATE 少一单")
if u"360（已搬两批" not in fr_still:
    die(u"§13 的仍开 bullet 没落到本轮的形状（360 的尺寸没更新）")
repl.append((a, b, fr_still))
repl.sort(key=lambda t: t[0], reverse=True)
fr_new = fr
for a, b, txt in repl:
    fr_new = fr_new[:a] + txt + fr_new[b:]

fr_new, n_title = re.subn(u"R9–R\\d+，\\d+ 轮自评",
                          u"R9–R%d，%s 轮自评" % (RD_N, SUBS2[u"@SECTIONS@"]), fr_new, count=1)
if n_title != 1:
    die(u"报告标题那一格没命中（%d 处）" % n_title)
fr_new, n_ucell = re.subn(u"U-31 … U-\\d+（R\\d+ 现读抬到最新一节）*",
                          u"U-31 … U-%d（@RTAG@ 现读抬到最新一节）" % UE,
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

def append_note_to_item(text, item, note):
    """把一段追记插到 **item.** 那一单的末尾（下一个 **NNN. 标题之前，跳过尾随空行）。

    刻意不用「文件末尾」或「上一个追记」当锚点：348 与 361 的追记前缀一模一样，
    按形状找落点才会插进别的单里（R289 一批：按整行相等找落点）。
    """
    lines = text.splitlines(True)
    head = [i for i, l in enumerate(lines) if l.startswith(u"**%d. " % item)]
    if len(head) != 1:
        die(u"%d 锚点异常（%d 处）⇒ 不许插" % (item, len(head)))
    k = len(lines)
    later = [i for i in range(head[0] + 1, len(lines)) if re.match(u"\\*\\*\\d{3}\\. ", lines[i])]
    if later:
        k = later[0]
    while lines[k - 1].strip() == u"":
        k -= 1
    joined = u"".join(lines[:k]).rstrip(u"\n")
    tail = u"".join(lines[k:]).lstrip(u"\n")
    return joined + u"\n" + note.strip(u"\n") + u"\n\n" + tail


new = {
    "UI": orig["UI"].replace(u"## 第 %d 轮" % (ROUND - 1), texts["UI"] + u"## 第 %d 轮" % (ROUND - 1), 1),
    "IT": orig["IT"].rstrip(u"\n") + u"\n\n" + texts["IT"].strip(u"\n") + u"\n",
    "DEC": orig["DEC"].rstrip(u"\n") + u"\n" + texts["DEC"].strip(u"\n") + u"\n",
    "BL": append_note_to_item(
        u"".join(bl_lines[:k357]).rstrip(u"\n") + u"\n\n" + texts["BL"].strip(u"\n")
        + u"\n\n" + u"".join(bl_lines[k357:]).lstrip(u"\n"), 348, fill(NOTE_348)),
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

# 写盘**之前**自扫一遍：没被替换的占位符就是「那一格记的是模板原文而不是读数」。
# 本轮生成器自己就犯过一次（键注册成复数、正文写单数），所以这条不是假想的守卫。
# 判据卷 `scripts/tests/test_ledger_tokens.py` 在事后扫同一形状；这里是事前，两处都要有。
STRAY_RX = re.compile(u"@([A-Z][A-Z0-9_]{1,24})@")
stray = []
for key, text in new.items():
    for number, line in enumerate(text.split(u"\n"), 1):
        for hit in STRAY_RX.finditer(line):
            stray.append(u"%s:%d %s" % (key, number, hit.group(0)))
if stray:
    die(u"写盘前有没被替换的占位符（%d 处）：%s" % (len(stray), u"；".join(stray[:10])))

for key, text in new.items():
    wr(FILES[key], text)

sh(["python3", REFRESH])

post, err = battery(u"写盘后", u"/tmp/r304_battery_post.log")
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
print(u"LEDGERS_R304 OK batt=Ran " + post[0] + u" (skipped=" + post[1] + u", 名单=" + str(post[2])
      + u") streak=" + STREAK_N + u" prod=0 bare=" + BARE + u"/" + CEIL + u" roster=" + ROSTER_N
      + u" bare=" + BARE + u"/" + CEIL + u" roster=" + ROSTER_N + u" swift=" + vk[u"swift_executed"] + u"/" + vk[u"swift_failures"]
      + u" knives=" + KC + u"/" + KN + u" U=" + s(UA) + u".." + s(UE) + u" D=" + s(DN)
      + u" BACKLOG_new=" + s(BLO) + u" derived_score(Round " + s(RD_N) + u")=" + s(score)
      + u" GAPS=" + gaps)
