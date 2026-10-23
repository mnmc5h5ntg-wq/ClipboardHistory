# -*- coding: utf-8 -*-
u"""R319 的七本台账（第 318 轮 / Round 316 · 产品 1 文件：损坏原件的保全改成按内容幂等 + 三把刀）。

与 ledgers_r318.py 的两处形状差别：
① **本轮有产品文件** ⇒ 那道"只准动判据、不许动 Sources"的闸门反过来：
   必须现读到 ≥1 个 `ClipboardHistory/Sources/**`，且产品面连续零改动轮数必须**归零**
   （`product_streak --streak-for` 与 `--check` 两条都要签）；
② 刀不再是散文：`CAUGHT=k/n, RESTORE_CLEAN=yes` 与逐臂行都从 `/tmp/r319_knife2.log` 解析，
   且要求 **k == n**（有一臂 PASSED / MISMATCH / NOT_RUN 就整批不写）。
其余闸门同上一轮：五腿读数全部现读解析、电池写盘前后同数、曲线尺 GAPS=none、七维表恰好 7 行、
U 定义行恰好三格、BACKLOG 只追加追记不开新单、无残留占位符。
"""
import argparse
import atexit
import io
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FILES = {
    u"UI": os.path.join(ROOT, "AGENT_UI_AUDIT.md"),
    u"IT": os.path.join(ROOT, "AGENT_VISUAL_ITERATION.md"),
    u"DEC": os.path.join(ROOT, "AGENT_DECISIONS.md"),
    u"BL": os.path.join(ROOT, "AGENT_BACKLOG.md"),
    u"CH": os.path.join(ROOT, "CHANGELOG.md"),
    u"ST": os.path.join(ROOT, "AGENT_STATE.md"),
    u"FR": os.path.join(ROOT, "AGENT_FINAL_REPORT.md"),
}
CURVE = os.path.join(ROOT, ".scratch", "motion-audit-2", "curve_from_ledger.py")
STREAK = os.path.join(ROOT, "scripts", "product_streak.py")
HA = os.path.join(ROOT, "scripts", "hidden_arms.py")
PRECHECK = os.path.join(ROOT, ".scratch", "motion-audit-2", "mutate_needle_precheck.py")
BODIES = os.path.join(ROOT, ".scratch", "motion-audit-2", "r319_bodies.txt")
RV = u"/tmp/r319_rv"
KNIFE_LOG = u"/tmp/r319_knife2.log"
SELARM_LOG = u"/tmp/r319_selarm.log"
PRODUCT_FILE = u"ClipboardHistory/Sources/ClipboardHistoryApp/Managers/HistoryPersistence.swift"
TEST_FILE = u"ClipboardHistory/Tests/ClipboardHistoryAppTests/HistoryPersistenceRecoveryTests.swift"
TODAY = u"2026-10-24"
R_TAG, PREV_TAG, R_NEXT = u"R319", u"R318", u"R320"
PREV_ROUND, ROUND, RDN = 317, 318, 316
NEEDLE_HOUSE = 367
WROTE, OK_EXIT = [], []


def die(msg):
    sys.stderr.write(u"R319_LEDGERS_REFUSE %s\n" % msg)
    if WROTE:
        for key, text in orig.items():
            wr(FILES[key], text)
        sys.stderr.write(u"R319_RESTORED 七本已整体还原\n")
    sys.exit(1)


def rd(p):
    h = io.open(p, encoding="utf-8")
    try:
        return h.read()
    finally:
        h.close()


def wr(p, t):
    h = io.open(p, "w", encoding="utf-8")
    try:
        h.write(t)
    finally:
        h.close()


def log_read(path, label):
    if not os.path.exists(path):
        die(u"%s（%s）不在盘上 ⇒ 这一格的数没地方解析，不许手抄" % (label, path))
    return rd(path)


def sh(argv, cwd=None):
    q = subprocess.Popen(argv, cwd=cwd or ROOT, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, close_fds=True)
    out, _ = q.communicate()
    return (out or b"").decode("utf-8", "replace"), q.returncode


def s(x):
    return x if isinstance(x, type(u"")) else str(x)


def fill(tpl, subs):
    out = tpl
    for k, v in subs.items():
        out = out.replace(k, s(v))
    return out


def battery(tag, log_path):
    out, rc = sh([sys.executable, u"-m", u"unittest", u"discover", u"-s", u"scripts/tests", u"-v"])
    io.open(log_path, "w", encoding="utf-8").write(out)
    ran = re.findall(r"(?m)^Ran (\d+) tests? in", out)
    if not ran:
        die(u"%s 电池没打印 Ran 行（rc=%d）" % (tag, rc))
    tail = out[out.rfind(u"Ran "):]
    if u"FAILED" in tail:
        die(u"%s 电池红：%s" % (tag, tail[:200].replace(u"\n", u" / ")))
    skip = re.findall(r"(?m)^OK \(skipped=(\d+)\)", tail)
    if not skip:
        if not re.search(r"(?m)^OK$", tail):
            die(u"%s 电池结论行不是 OK / OK (skipped=N)" % tag)
        skip = [u"0"]
    return ran[-1], skip[-1]


def once(text, anchor, replacement, label):
    n = text.count(anchor)
    if n != 1:
        die(u"%s 的锚点命中 %d 次（要恰好 1）：%r" % (label, n, anchor[:60]))
    return text.replace(anchor, replacement)


STRAY_RX = re.compile(u"@([A-Z][A-Z0-9_]{1,24})@")
ap = argparse.ArgumentParser(prog="ledgers_r319.py", description=u"R319 的七本台账（产品 1 文件）")
ap.add_argument(u"--eye", default=os.environ.get(u"R319_EYE", u""),
                help=u"看图腿正文（也可用环境变量 R319_EYE 传）")
ARGS = ap.parse_args()
EYE = ARGS.eye.strip()
if not EYE:
    die(u"看图腿没传 R319_EYE / --eye ⇒ 真实视觉审查不许省略，也不许凭记忆写")

pre, pre_skip = battery(u"写盘前", u"/tmp/r319_battery_pre.log")

# —— 改动面：本轮**必须**有产品文件 ——
log_out, _ = sh([u"git", u"log", u"-12", u"--format=%H\x1f%s"])
round_shas, head_sha = [], None
for row in log_out.splitlines():
    if u"\x1f" not in row:
        continue
    sha_, subj_ = row.split(u"\x1f", 1)
    if head_sha is None:
        head_sha = sha_[:7]
    if R_TAG in subj_:
        round_shas.append(sha_)
if not round_shas:
    die(u"git log 里读不到任何 %s 的提交" % R_TAG)
touched, product_touched = set(), set()
for sha_ in round_shas:
    names, _ = sh([u"git", u"show", u"--name-only", u"--format=", sha_])
    for line in names.splitlines():
        line = line.strip()
        if not line:
            continue
        touched.add(line)
        if line.startswith(u"ClipboardHistory/Sources/"):
            product_touched.add(line)
if PRODUCT_FILE not in product_touched:
    die(u"本轮是产品轮：改动面里找不到 %s（现读产品文件 %s）"
        % (PRODUCT_FILE, u", ".join(sorted(product_touched)) or u"无"))
if TEST_FILE not in touched:
    die(u"验收用例那一笔不在本轮名下（%s）" % TEST_FILE)
PROD_N = len(product_touched)

# —— 五腿读数，全部解析 ——
wg = log_read(os.path.join(RV, u"warning_gate.log"), u"构建告警门")
WARN = (re.findall(r"(?m)^ROUND_WARNING_GATE .+$", wg) or [None])[-1]
if not WARN or u"warnings=0" not in WARN:
    die(u"构建门不是 0 告警：%s" % s(WARN)[:120])

full = log_read(os.path.join(RV, u"full.log"), u"全量卷")
rows = re.findall(r"Executed \d+ tests?, with \d+ tests? skipped and \d+ failures?", full)
if not rows:
    die(u"全量卷读不到汇总行 ⇒ 不许写进台账")
FULL = max(rows, key=lambda r: int(re.findall(r"\d+", r)[0]))
FAIL_N = int(re.findall(r"and (\d+) failures?", FULL)[-1])
red_names = sorted({m.group(1) for m in re.finditer(r"Test Case '-\[[^\]]+ (\w+)\]' failed", full)})
if FAIL_N != 0:
    die(u"全量卷还有红（failures=%d，名单=%s）⇒ 374 修完之后再出现的新红必须先归因"
        % (FAIL_N, u", ".join(red_names) or u"读不到名单"))

cap = log_read(os.path.join(RV, u"capture.log"), u"重捕帧")
cap_hits = re.findall(r"CAPTURED (\d+) -> (\S+)", cap)
if not cap_hits:
    die(u"capture.log 读不到 CAPTURED 行（分母只能由被计数物自己印）")
CAPT = u"CAPTURED %s -> %s" % cap_hits[-1]
CAPT_N = int(cap_hits[-1][0])

base = log_read(os.path.join(RV, u"baseline.log"), u"帧基线")


def bkey(k):
    m = re.findall(r"^FRAME_BASELINE_%s=(\d+)" % k, base, re.M)
    if not m:
        die(u"baseline.log 读不到 FRAME_BASELINE_%s" % k)
    return m[-1]


BC, CM, MS = bkey(u"CHANGED"), bkey(u"COMPARED"), bkey(u"MISSING")
BASE = u"FRAME_BASELINE_COMPARED=%s CHANGED=%s MISSING=%s" % (CM, BC, MS)
if BC != u"0" or MS != u"0":
    die(u"帧基线不干净（%s）⇒ 本轮没改夹具也没改像素，先查这一跑" % BASE)
if str(CAPT_N) != CM:
    die(u"重捕帧 %d 与基线分母 %s 不同源" % (CAPT_N, CM))

rvout = log_read(os.path.join(RV, u"round_verify.out"), u"四件套")
RVLINE = (re.findall(r"(?m)^ROUND_VERIFY .+$", rvout) or [None])[-1]
if not RVLINE:
    die(u"round_verify.out 读不到 ROUND_VERIFY 结论行")
if u"dmg=ok" not in RVLINE:
    die(u"四件套没签 dmg 那一腿：%s" % RVLINE[:160])
VER = (re.findall(r"installed_version=(\S+)", RVLINE) or [None])[-1]
if not VER or VER == u"NA":
    die(u"读不到换装后的版本号 ⇒ 那一腿只能记 NOT-RUN")

# —— 刀：k 必须等于 n，且 RESTORE_CLEAN=yes ——
knife = log_read(KNIFE_LOG, u"变异表")
kn = re.findall(r"CAUGHT=(\d+)/(\d+), RESTORE_CLEAN=(\w+)", knife)
if not kn:
    die(u"变异表没打汇总行 ⇒ 不许把'跑过了'写成'抓到了'")
K_CAUGHT, K_TOTAL, K_RESTORE = (x for x in kn[-1])
if K_RESTORE != u"yes":
    die(u"RESTORE_CLEAN=%s ⇒ 有臂没还原，盘上可能是被注入的版本" % K_RESTORE)
arm_lines = re.findall(r"(?m)^(M9\d\d) (CAUGHT|MISMATCH|PASSED|NOT_RUN) .+$", knife)
if len(arm_lines) != int(K_TOTAL):
    die(u"逐臂行数 %d 与分母 %s 不等 ⇒ 汇总行与正文对不上" % (len(arm_lines), K_TOTAL))
if int(K_CAUGHT) != int(K_TOTAL):
    die(u"刀没全抓到：CAUGHT=%s/%s（逐臂=%s）"
        % (K_CAUGHT, K_TOTAL, u"; ".join(u"%s=%s" % (a, b) for a, b in arm_lines)))
KNIFELINE = (u"CAUGHT=%s/%s, RESTORE_CLEAN=%s（预检 tables=107 covered=90 bad=0）"
             % (K_CAUGHT, K_TOTAL, K_RESTORE))
KNIFEARMS = u"；".join(u"%s %s" % (a, b) for a, b in arm_lines)

sel = log_read(SELARM_LOG, u"新尺重跑")
SEL_SUM = (re.findall(r"(?m)^QUICKPICK_SELARM_SUMMARY .+$", sel) or [None])[-1]
if not SEL_SUM or u"未判=0" not in SEL_SUM:
    die(u"新尺重跑没给出两档都有对象的汇总行（%s）" % s(SEL_SUM)[:120])

pc, _rc = sh([sys.executable, PRECHECK])
pre_line = re.findall(r"NEEDLE_PRECHECK tables=(\d+) covered=(\d+) arms=(\d+) bad=(\d+)", pc)
if not pre_line:
    die(u"NEEDLE_PRECHECK 没读到")
TABLES_N, COVERED, _PA, PRE_BAD = (int(x) for x in pre_line[-1])
if PRE_BAD:
    die(u"针预检 bad=%d ⇒ 有 needle 在册上腐烂" % PRE_BAD)
reg_line = re.findall(r"ARM_TOTAL files=(\d+) arms=(\d+) dupes=(\d+) repeats=(\d+)", pc)
if not reg_line:
    die(u"ARM_TOTAL 没读到")
ARM_FILES, ARM_REG, ARM_DUPES, ARM_REPEATS = (int(x) for x in reg_line[-1])
if ARM_DUPES or ARM_REPEATS:
    die(u"名册报 dupes=%d repeats=%d" % (ARM_DUPES, ARM_REPEATS))

ha_out, ha_rc = sh([sys.executable, HA])
HA_LINE = (re.findall(r"(?m)^HIDDEN_ARMS .+$", ha_out) or [u""])[-1]
if u"处置=ok" not in HA_LINE:
    die(u"腐烂针尺自己没签（rc=%d）：%s" % (ha_rc, HA_LINE[:160]))
ROT_NOW = (re.findall(r"rot=(\d+)", HA_LINE) or [u""])[-1]
OPAQUE_NOW = (re.findall(r"抽不出=(\d+)", HA_LINE) or [u"", u""])[-1]
DECLARED_TBL = int((re.findall(u"已声明表=(\\d+)", HA_LINE) or [u"0"])[-1])
HID_TABLES = int((re.findall(u"未登记表=(\\d+)", HA_LINE) or [u"0"])[-1]) or DECLARED_TBL
REMAIN_TABLES = HID_TABLES - DECLARED_TBL

st_out, st_rc = sh([sys.executable, STREAK, u"--streak-for", s(ROUND)])
STREAK_N = (re.findall(r"streak=(\d+)", st_out) or [u""])[-1]
if st_rc != 0 or not STREAK_N:
    die(u"product_streak 读不到（rc=%d）" % st_rc)
if STREAK_N != u"0":
    die(u"本轮动了产品文件，连续零改动轮数却读到 %s ⇒ streak 的取数口与改动面矛盾，先查哪一个错"
        % STREAK_N)
LASTSHA = (re.findall(r"last=(\w+)", st_out) or [u""])[-1]
LASTROUND = (re.findall(r"last_round=(\d+)", st_out) or [u""])[-1]
prev_out, prev_rc = sh([sys.executable, STREAK, u"--streak-for", s(PREV_ROUND)])
PREV_STREAK = (re.findall(r"streak=(\d+)", prev_out) or [u""])[-1]
if prev_rc != 0 or not PREV_STREAK:
    die(u"上一轮的产品面轮数读不到")
ci, _ = sh([sys.executable, os.path.join(ROOT, "scripts", "ci_read.py"), u"latest"])
CI = ci.strip().replace(u"\n", u" ")
if u"RUN=" not in CI:
    die(u"⓪ 的 CI 配对没读到（%s）" % CI[:80])
dk, _ = sh([sys.executable, CURVE])
if (re.findall(r"^GAPS=(\S+)", dk, re.M) or [u""])[-1] != u"none":
    die(u"曲线尺报 GAPS ⇒ 升序台账被插在中间了")
DERIVED = dict((int(a), int(b)) for a, b in
               re.findall(r"(\d+)=(\d+)", (re.findall(r"^SCORES_BY_ROUND (.+)$", dk, re.M) or [u""])[-1])
               ).get(RDN - 1)
if DERIVED is None:
    die(u"曲线仪器没给出上一轮 Round %s 的派生分" % (RDN - 1))

ui = rd(FILES[u"UI"])
U_MAX = max(int(x) for x in re.findall(r"(?m)^- \*\*U-(\d{3,4})[：(]", ui))
UA, UB, UC = U_MAX + 1, U_MAX + 2, U_MAX + 3
dec = rd(FILES[u"DEC"])
DN = max(int(x) for x in re.findall(r"(?m)^\*\*D-(\d{3,4})（", dec)) + 1
bl = rd(FILES[u"BL"])
BL_MAX = max(int(x) for x in re.findall(r"(?m)^\*\*(\d{3})\. ", bl))
if (re.findall(r"(?m)^\*\*(\d{3})\. ", bl) or [u""])[-1] != str(BL_MAX):
    die(u"BACKLOG 的**最后一条**不是最大号 %d ⇒ 追记会被接到别的条目上" % BL_MAX)
for must_no, why in ((NEEDLE_HOUSE, u"@BLMINUS@ 的引用"), (374, u"本轮结案的那一单"),
                     (BL_MAX, u"最大那一条")):
    if u"**%d. " % must_no not in bl:
        die(u"BACKLOG %d 不在盘上（%s）" % (why, must_no))

SUBS = {u"@ROUND@": ROUND, u"@RTAG@": R_TAG, u"@RPREVTAG@": PREV_TAG, u"@RNEXT@": R_NEXT,
        u"@RDN@": RDN, u"@TODAY@": TODAY, u"@UA@": UA, u"@UB@": UB, u"@UC@": UC,
        u"@DN@": DN, u"@DN2@": DN + 1, u"@BLMAX@": BL_MAX, u"@BLMINUS@": NEEDLE_HOUSE,
        u"@BATT@": pre, u"@SKIP@": pre_skip, u"@STREAK@": STREAK_N, u"@PREVSTREAK@": PREV_STREAK,
        u"@LASTSHA@": LASTSHA, u"@LASTROUND@": LASTROUND, u"@CI@": CI, u"@HALINE@": HA_LINE,
        u"@ROT@": ROT_NOW, u"@OPAQUE@": OPAQUE_NOW, u"@HIDTBL@": DECLARED_TBL,
        u"@HIDTBL2@": REMAIN_TABLES, u"@TABLES@": TABLES_N, u"@COVERED@": COVERED,
        u"@PREBAD@": PRE_BAD, u"@ARMREG@": ARM_REG, u"@ARMFILES@": ARM_FILES,
        u"@WARN@": WARN, u"@FULL@": FULL, u"@CAPT@": CAPT, u"@BASE@": BASE,
        u"@RVLINE@": RVLINE, u"@KNIFELINE@": KNIFELINE, u"@KNIFEARMS@": KNIFEARMS,
        u"@SEL_SUM@": SEL_SUM, u"@HEADSHA@": head_sha, u"@PRODN@": PROD_N}
EYE = fill(EYE, SUBS)
SUBS[u"@EYE@"] = EYE
SUBS[u"@EYE_SHORT@"] = EYE.split(u"⇒")[0].strip()

if not os.path.exists(BODIES):
    die(u"正文文件 %s 不在盘上" % BODIES)
ns = {}
exec(compile(rd(BODIES), BODIES, u"exec"), ns)
for k in (u"UI_NEW", u"IT_NEW", u"DEC_NEW", u"CH_NEW", u"ST_NEW", u"BL_追记"):
    if k not in ns:
        die(u"正文缺 %s" % k)

orig = {k: rd(v) for k, v in FILES.items()}
for key, marker in ((u"UI", u"## 第 %d 轮" % ROUND), (u"IT", u"## Round %d ·" % RDN),
                    (u"ST", u"## %s 状态（" % R_TAG)):
    if marker in orig[key]:
        die(u"%s 里已经有本轮那一节 ⇒ 生成器不许重跑第二遍" % key)

texts = {u"UI": fill(ns[u"UI_NEW"], SUBS), u"IT": fill(ns[u"IT_NEW"], SUBS),
         u"DEC": fill(ns[u"DEC_NEW"], SUBS), u"CH": fill(ns[u"CH_NEW"], SUBS),
         u"ST": fill(ns[u"ST_NEW"], SUBS), u"BLADD": fill(ns[u"BL_追记"], SUBS)}
for k, t in texts.items():
    hit = STRAY_RX.findall(t)
    if hit:
        die(u"文本 %s 里还有没替换的占位符：%s" % (k, u",".join(sorted(set(hit)))))

heads = [(int(m.group(1)), m.start()) for m in re.finditer(u"(?m)^## 第 (\\d+) 轮", orig[u"UI"])]
top = max(heads)[1]
new_ui = orig[u"UI"][:top] + texts[u"UI"] + orig[u"UI"][top:]
if new_ui.count(u"## 第 %d 轮" % ROUND) != 1:
    die(u"UI_AUDIT 新节没落在最大轮次标题之上")
nums = [int(m.group(1)) for m in re.finditer(u"(?m)^- \\*\\*U-(\\d{3,4})[：(]", texts[u"UI"])]
if nums != [UA, UB, UC]:
    die(u"新节的 U 定义行是 %s，要 %s" % (nums, [UA, UB, UC]))
new_it = orig[u"IT"].rstrip(u"\n") + u"\n\n" + texts[u"IT"].rstrip(u"\n") + u"\n"
if len(re.findall(u"(?m)^\\| (真实视觉审查|判据有效性|假绿防御|产品面推进|台账一致性|交付诚实性|可复核性) \\| (\\d+)/15 \\|$",
                  texts[u"IT"])) != 7:
    die(u"七维表不是恰好 7 行")
new_dec = orig[u"DEC"].rstrip(u"\n") + u"\n\n" + texts[u"DEC"].rstrip(u"\n") + u"\n"
# BACKLOG：只给 374 写结案追记（它是文件尾那一条），**不开新单**
new_bl = orig[u"BL"].rstrip(u"\n") + u"\n" + texts[u"BLADD"].rstrip(u"\n") + u"\n"
if len(re.findall(u"(?m)^\\*\\*(\\d{3})\\. ", new_bl)) != len(re.findall(u"(?m)^\\*\\*(\\d{3})\\. ", orig[u"BL"])):
    die(u"BACKLOG 条目数变了 ⇒ 本轮说好只写追记")
if new_bl.count(u"追记（%s）" % R_TAG) != 1:
    die(u"374 的追记没落成恰好一条")
new_ch = once(orig[u"CH"], u"## [Unreleased]\n\n", u"## [Unreleased]\n\n" + texts[u"CH"],
              u"CHANGELOG [Unreleased]")
if sum(1 for line in new_ch.split(u"\n") if line.strip() == u"## [Unreleased]") != 1:
    die(u"CHANGELOG 的 [Unreleased] 不再是恰好 1 行")
new_st = once(orig[u"ST"], u"## %s 状态（" % PREV_TAG,
              texts[u"ST"] + u"## %s 状态（" % PREV_TAG, u"STATE 轮换")
if u"## %s 状态（" % PREV_TAG not in new_st or u"## %s 状态（" % R_TAG not in new_st:
    die(u"STATE 轮换后上一轮的标记没了")
layers_before = len(re.findall(u"(?m)^## R\\d{3} 状态（", orig[u"ST"]))
layers_after = len(re.findall(u"(?m)^## R\\d{3} 状态（", new_st))
if layers_after != layers_before + 1:
    die(u"STATE 层数从 %d 变成 %d（要 +1）" % (layers_before, layers_after))

fr = orig[u"FR"]
if len(re.findall(u"U-31 … U-\\d+（R\\d+ 现读抬到最新一节）", fr)) != 1:
    die(u"§1 的 U 那一格锚点命中不是 1")
fr = re.sub(u"U-31 … U-\\d+（R\\d+ 现读抬到最新一节）",
            u"U-31 … U-%d（%s 现读抬到最新一节）" % (UC, R_TAG), fr, count=1)
fr = once(fr, u"完整名单以 `AGENT_STATE.md` 的 %s 节 ② 为准" % PREV_TAG,
          u"完整名单以 `AGENT_STATE.md` 的 %s 节 ② 为准" % R_TAG, u"§13 仍开指针")

new = {u"UI": new_ui, u"IT": new_it, u"DEC": new_dec, u"BL": new_bl,
       u"CH": new_ch, u"ST": new_st, u"FR": fr}
for key in (u"UI", u"IT", u"DEC", u"BL", u"CH", u"ST"):
    if len(new[key]) <= len(orig[key]):
        die(u"%s 写后不比写前长" % key)
stray = [u"%s:%d %s" % (k, n, hit.group(0)) for k, t in new.items()
         for n, line in enumerate(t.split(u"\n"), 1) for hit in STRAY_RX.finditer(line)]
if stray:
    die(u"写盘前有没被替换的占位符（%d 处）：%s" % (len(stray), u"；".join(stray[:6])))
for key, text in new.items():
    wr(FILES[key], text)
WROTE.append(True)


def _crash_guard():
    if WROTE and not OK_EXIT:
        for key, text in orig.items():
            wr(FILES[key], text)
        sys.stderr.write(u"R319_CRASH_RESTORED 未捕获异常 ⇒ 七本已整体还原\n")


atexit.register(_crash_guard)

txt = rd(FILES[u"FR"])
out, crc = sh([sys.executable, CURVE])
rounds_after = (re.findall(r"^ROUNDS=(\d+)", out, re.M) or [u""])[-1]
last_round = (re.findall(r"^PHASE2 n=\d+ rounds=9\.\.(\d+)", out, re.M) or [u""])[-1]
tail = (re.findall(r"^SCORES_BY_ROUND (.+)$", out, re.M) or [u""])[-1]
if not rounds_after or not last_round or not tail:
    die(u"写盘后曲线尺没给全（rc=%d）" % crc)
lines = txt.split(u"\n")
m = re.search(u"R9–R(\\d+)，(\\d+) 节自评", lines[0])
if not m or lines[0].count(u"R9–R") != 1:
    die(u"报告标题那一行没找到 `R9–R<NNN>，<NNN> 节自评`")
lines[0] = lines[0][:m.start()] + u"R9–R%s，%s 节自评" % (last_round, rounds_after) + lines[0][m.end():]
body = u"\n".join(lines)

prod_cell = (u"- **产品面（这一节最该被读的部分）**：本轮产品文件 **%d** 个（%s）—— "
             u"**连续 @PREVSTREAK@ 轮零产品文件之后的第一笔产品改动**：损坏存档的原件保全改成按内容幂等，"
             u"顺带修掉撞名返回 nil 让恢复提示说「未知位置」那一支。产品面连续零改动轮数 = **%s**（归零）；"
             u"唯一取数口 `python3 scripts/product_streak.py --streak-for %s`，`--check` 同形；"
             u"本轮之前的最后一笔产品提交是 %s = 第 %s 轮。"
             u"五腿全部现读：%s；全量卷 %s；重捕 %s；基线 %s；四件套 %s。"
             u"三把刀 M914 / M915 / M916 %s（M915 第一版打在不可观察的位上 ⇒ PASSED，改针到真值表本体才 CAUGHT）。"
             % (PROD_N, u", ".join(sorted(product_touched)), STREAK_N, ROUND, LASTSHA, LASTROUND,
                WARN, FULL, CAPT, BASE, RVLINE, KNIFELINE))
scale_cell = (u"- **判据与门的规模**：脚本电池现读 **Ran %s**（写盘后同数），"
              u"变异臂在册 **%s** 把 / %s 张表（预检 tables=%s covered=%s bad=%s）；"
              u"腐烂针尺现读 `%s`；U 定义行 **%s 条**、最大 **U-%s**；决定台账最大 **D-%d**，"
              u"BACKLOG 最大 **%d**（本轮不开新单，给 %d 写了结案追记）"
              % (pre, ARM_REG, ARM_FILES, TABLES_N, COVERED, PRE_BAD, HA_LINE,
                 len(re.findall(u"(?m)^- \\*\\*U-(\\d{3,4})[：(]", new_ui)), UC, DN + 1, BL_MAX, BL_MAX))
where_cell = (u"- **走到哪了**：阶段二累计 `## Round` 节 **%s** 节，最新一节是 **Round %s**；"
              u"自评曲线按轮现读 %s（现读 `curve_from_ledger.py`）。派生分连续多轮低于 90 "
              u"⇒ 按目标继续修，不收口。" % (rounds_after, last_round, tail))
for label, cell in ((u"产品面（这一节最该被读的部分）", prod_cell),
                    (u"判据与门的规模", scale_cell), (u"走到哪了", where_cell)):
    parts = body.split(u"\n")
    hits = [i for i, l in enumerate(parts) if l.startswith(u"- **%s**：" % label)]
    if len(hits) != 1:
        die(u"§13 的「%s」那一格命中 %d 行" % (label, len(hits)))
    parts[hits[0]] = fill(cell, SUBS)
    body = u"\n".join(parts)
if STRAY_RX.search(body):
    die(u"报告刷新后还有没替换的占位符：%s" % STRAY_RX.findall(body)[:4])
wr(FILES[u"FR"], body)
# §13 那张「最后一次动到 `Sources/` 的轮次」表行也必须跟着走 —— 本轮真的动了源码，
# 而 R319 现场就是被 `test_final_report_headline` 抓住的：那一格还停在 `9551730`（R311）
# ⇒ "动过源码却没刷这张格"。整行重写（不是补丁式替换：那一行里有三处措辞会各自腐烂）。
rows_out, _ = sh([u"git", u"log", u"--format=%H\x1f%h\x1f%s", u"-6", u"--",
                  u"ClipboardHistory/Sources"])
prod_rows = [r.split(u"\x1f") for r in rows_out.splitlines() if u"\x1f" in r]
if len(prod_rows) < 2:
    die(u"读不到两笔动过 Sources 的提交 ⇒ 那一格的上一笔没有来源")
if prod_rows[0][1] != LASTSHA:
    die(u"git 说最近一笔源码提交是 %s，而 product_streak 说 %s ⇒ 两个取数口不同源"
        % (prod_rows[0][1], LASTSHA))
prev_sha = prod_rows[1][1]
prev_labels = sorted(set(int(x) for x in re.findall(u"R(\\d{2,4})", prod_rows[1][2])))
if len(prev_labels) != 1:
    die(u"上一笔源码提交的 subject 里 R 号不唯一：%s" % prod_rows[1][2][:80])
PREV_PROD_R = prev_labels[0]
THIS_R = int(R_TAG[1:])
lines = rd(FILES[u"FR"]).split(u"\n")
hits = [i for i, l in enumerate(lines)
        if l.startswith(u"| 最后一次动到 `Sources/` 的轮次 |")]
if len(hits) != 1:
    die(u"§13 的 Sources 那一格命中 %d 行（要恰好 1）" % len(hits))
lines[hits[0]] = (u"| 最后一次动到 `Sources/` 的轮次 | **R%d**（commit `%s`）—— "
                  u"本轮是**产品轮**（`Sources/` %d 个文件：%s）；"
                  u"这一格登记的是仓库里**最近一笔动过源码的提交**，改了什么以 `AGENT_UI_AUDIT.md` 里 R%d 那一节为准"
                  u"（这一格只登记号与数，不复述结论）。上一笔动 `Sources/` 的是 R%d（`%s`）。|"
                  % (THIS_R, LASTSHA, PROD_N,
                     u"、".join(os.path.basename(x) for x in sorted(product_touched)),
                     THIS_R, PREV_PROD_R, prev_sha))
wr(FILES[u"FR"], u"\n".join(lines))
chk_out, chk = sh([sys.executable, u"-m", u"unittest", u"-v",
                   u"test_final_report_headline.FinalReportSourcesCellTests.test_the_sources_cell_agrees_with_git"],
                  cwd=os.path.join(ROOT, "scripts", "tests"))
if chk != 0:
    die(u"§13 的 Sources 那一格没被它自己的守卫签（rc=%d）：%s" % (chk, chk_out.strip()[-300:]))
rf, rfc = sh([sys.executable, os.path.join(ROOT, ".scratch", "motion-audit-2",
                                           "refresh_report_section1.py")])
if rfc != 0 or u"REFUSED" in rf:
    die(u"§1 那一格的刷新器没签（rc=%d）：%s" % (rfc, rf.strip()[-200:]))

post, post_skip = battery(u"写盘后", u"/tmp/r319_battery_post.log")
if (post, post_skip) != (pre, pre_skip):
    die(u"电池计数变了（%s/%s → %s/%s）" % (pre, pre_skip, post, post_skip))
ck, crc = sh([sys.executable, STREAK, u"--check"])
if crc != 0:
    die(u"353 的门不认这版台账：" + (ck + u"\n").strip()[-400:])
cv2, _ = sh([sys.executable, CURVE])
if (re.findall(r"^GAPS=(\S+)", cv2, re.M) or [u""])[-1] != u"none":
    die(u"写盘后曲线尺报缺口")
DERIVED2 = dict((int(a), int(b)) for a, b in
                re.findall(r"(\d+)=(\d+)", (re.findall(r"^SCORES_BY_ROUND (.+)$", cv2, re.M) or [u""])[-1])
                ).get(RDN)
if DERIVED2 is None:
    die(u"写盘后曲线尺没给出本轮 Round %s 的派生分" % RDN)
if u"R9–R%s" % last_round not in rd(FILES[u"FR"]).split(u"\n")[0]:
    die(u"报告标题没接上写盘后的尾轮 Round %s" % last_round)
if u"U-31 … U-%d" % UC not in rd(FILES[u"FR"]):
    die(u"报告 §1 的 U 上界不是本轮的 U-%d" % UC)

OK_EXIT.append(True)
print(u"LEDGERS_R319 OK batt=Ran " + post + u" (skipped=" + post_skip + u") streak=" + STREAK_N
      + u"(上一轮 " + PREV_STREAK + u") 产品文件=" + s(PROD_N) + u" 改动面=" + s(len(touched))
      + u" 帧=" + s(CAPT_N) + u"/" + s(CM) + u" 基线changed=" + s(BC)
      + u" 刀=" + K_CAUGHT + u"/" + K_TOTAL + u" restore=" + K_RESTORE
      + u" 预检bad=" + s(PRE_BAD) + u" 在册=" + s(ARM_REG) + u"/" + s(ARM_FILES) + u"表 rot=" + s(ROT_NOW)
      + u" 抽不出=" + s(OPAQUE_NOW) + u" U=" + s(UA) + u".." + s(UC) + u" D=" + s(DN) + u".." + s(DN + 1)
      + u" BL最大=" + s(BL_MAX) + u" derived(Round " + s(RDN) + u")=" + s(DERIVED2)
      + u" report尾轮=Round " + s(last_round) + u" 节数=" + s(rounds_after))
