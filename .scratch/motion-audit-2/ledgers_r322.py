# -*- coding: utf-8 -*-
u"""R322 的七本台账（第 321 轮 / Round 319 · 动效主线：胶囊横移的过程证人 + runner 交账）。

与 r321 的四处不同：
① 改动面必须含 `MotionFilmstripTests.swift`（判据文件），仍不含任何 `ClipboardHistory/Sources/**`；
② 本轮的结论建立在**三行新读数**上（`MOTION_PILL_SLIDE` / `_SETTLE` 本机 + runner 的 SELARM 三行），
   它们必须从落盘日志里解析出来；正文里抄的那几个数（3 / 1 / 0.09 / 0.354 / 64ms）逐一对账，
   对不上就拒写；
③ BACKLOG 一次动**两处追记**（373 与 375），都不新开单 ⇒ 条目数必须**不变**；
④ 新读数族必须先进 `ledger_rows.py` 的搬运名单，且 `READINGS_MUST_INCLUDE` 的"缺"必须为 0。
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
ROWS = os.path.join(ROOT, ".scratch", "motion-audit-2", "ledger_rows.py")
BODIES = os.path.join(ROOT, ".scratch", "motion-audit-2", "r322_bodies.txt")
RV = u"/tmp/r322_rv"
KNIFE_LOG = u"/tmp/r322_mutate.log"
PILL_LOG = u"/tmp/r322_pill_final.log"
RUNNER_LOG = u"/tmp/r322_runner_selarm.log"
ROWS_LOG = u"/tmp/r322_rows.log"
FILM = u"ClipboardHistory/Tests/ClipboardHistoryAppTests/MotionFilmstripTests.swift"
TODAY = u"2026-10-24"
R_TAG, PREV_TAG, R_NEXT = u"R322", u"R321", u"R323"
PREV_ROUND, ROUND, RDN = 320, 321, 319
NEEDLE_HOUSE = 367
GUT_HOUSE = 375            # 上一轮新开的单，本轮写追记
ENTRY_373 = 373            # 另一处追记
ANCHOR_AFTER_373 = 374     # 373 的追记必须插在它之前
WROTE, OK_EXIT = [], []


def die(msg):
    sys.stderr.write(u"R322_LEDGERS_REFUSE %s\n" % msg)
    if WROTE:
        for key, text in orig.items():
            wr(FILES[key], text)
        sys.stderr.write(u"R322_RESTORED 七本已整体还原\n")
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


def strip_step(line):
    m = re.match(r"^\s*\[[^\]]*\]\s*(.*)$", line)
    return (m.group(1) if m else line).strip()


STRAY_RX = re.compile(u"@([A-Z][A-Z0-9_]{1,24})@")
ap = argparse.ArgumentParser(prog="ledgers_r322.py", description=u"R322 的七本台账（动效主线）")
ap.add_argument(u"--eye", default=os.environ.get(u"R322_EYE", u""),
                help=u"看图腿正文（也可用环境变量 R322_EYE 传）")
ARGS = ap.parse_args()
EYE = ARGS.eye.strip()
if not EYE:
    die(u"看图腿没传 R322_EYE / --eye ⇒ 真实视觉审查不许省略，也不许凭记忆写")

pre, pre_skip = battery(u"写盘前", u"/tmp/r322_battery_pre.log")

# —— 改动面：判据轮（产品 0 文件），且必须含胶片卷 ——
log_out, _ = sh([u"git", u"log", u"-14", u"--format=%H\x1f%s"])
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
    die(u"git log 里读不到任何 %s 的提交 ⇒ 代码半还没落" % R_TAG)
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
if FILM not in touched:
    die(u"改动面里找不到 %s" % FILM)
if product_touched:
    die(u"本轮是判据轮：动了产品文件就得改台账形状（现读 %s）"
        % u", ".join(sorted(product_touched))[:200])

# —— 五腿读数 ——
wg = log_read(os.path.join(RV, u"warning_gate.log"), u"构建告警门")
WARN = (re.findall(r"(?m)^ROUND_WARNING_GATE .+$", wg) or [None])[-1]
if not WARN or u"warnings=0" not in WARN:
    die(u"构建门不是 0 告警：%s" % s(WARN)[:120])

full = log_read(os.path.join(RV, u"full.log"), u"全量卷")
rows = re.findall(r"Executed \d+ tests?, with \d+ tests? skipped and \d+ failures?", full)
if not rows:
    die(u"全量卷读不到汇总行")
FULL = max(rows, key=lambda r: int(re.findall(r"\d+", r)[0]))
FAIL_N = int(re.findall(r"and (\d+) failures?", FULL)[-1])
red_names = sorted({m.group(1) for m in re.finditer(r"Test Case '-\[[^\]]+ (\w+)\]' failed", full)})
if FAIL_N != 0:
    die(u"全量卷有红（failures=%d，名单=%s）⇒ 先归因再落账" % (FAIL_N, u", ".join(red_names) or u"读不到"))

cap = log_read(os.path.join(RV, u"capture.log"), u"重捕帧")
cap_hits = re.findall(r"CAPTURED (\d+) -> (\S+)", cap)
if not cap_hits:
    die(u"capture.log 读不到 CAPTURED 行")
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
    die(u"帧基线不干净（%s）⇒ 本轮没改夹具也没改像素" % BASE)
if str(CAPT_N) != CM:
    die(u"重捕帧 %d 与基线分母 %s 不同源" % (CAPT_N, CM))

rvout = log_read(os.path.join(RV, u"round_verify.out"), u"四件套")
RVLINE = (re.findall(r"(?m)^ROUND_VERIFY .+$", rvout) or [None])[-1]
if not RVLINE or u"dmg=ok" not in RVLINE:
    die(u"四件套没签完：%s" % s(RVLINE)[:160])

# —— 本轮的主菜：过程证人的三行读数（本机）——
pill = log_read(PILL_LOG, u"过程证人卷")
PILL = (re.findall(r"(?m)^MOTION_PILL_SLIDE filter-pill-slide .+$", pill) or [None])[-1]
PILL_SETTLE = (re.findall(r"(?m)^MOTION_PILL_SLIDE_SETTLE .+$", pill) or [None])[-1]
if not PILL or not PILL_SETTLE:
    die(u"读不到 MOTION_PILL_SLIDE / _SETTLE ⇒ 本轮结论没有出处")
exec_hits = re.findall(r"Executed 1 test, with (?:\d+ tests? skipped and )?(\d+) failures?", pill)
if not exec_hits or exec_hits[-1] != u"0":
    die(u"过程证人卷自己是红的或读不到汇总行（%s）" % (exec_hits[-1] if exec_hits else u"无"))
PILL_EXEC = u"Executed 1 test, with 0 failures（不设 CLIPBOARD_HISTORY_UI_MOTION 时整卷 skip）"
# 条带与读数必须同源：这一卷真的跑了，才会有 MOTION_PILL_SLIDE 那行（skip 的时候什么都没有）
# 正文抄的那几个数必须与这行一致（共用线 / 旧口径 / 两臂峰值 / 落定毫秒 / 采样间隔）
m = re.search(r"开A 帧数=(\d+)\(旧口径(\d+)\) 峰值=([\d.]+).*?关 帧数=(\d+)\(旧口径(\d+)\) 峰值=([\d.]+)"
              r".*?采样≈([\d.]+)ms", PILL)
if not m:
    die(u"MOTION_PILL_SLIDE 那行形状变了，解析不出来：%s" % PILL[:200])
SPAN_A, OLD_A, PEAK_A, SPAN_OFF, OLD_OFF, PEAK_OFF, INTERVAL = m.groups()
settle_ms = re.findall(r"实测落定≈(\d+)ms", PILL_SETTLE)
if not settle_ms:
    die(u"_SETTLE 那行读不到落定毫秒数：%s" % PILL_SETTLE[:160])
SETTLE_MS = settle_ms[-1]
if not (int(SPAN_A) > int(SPAN_OFF) and int(OLD_A) > int(OLD_OFF) and float(PEAK_A) < float(PEAK_OFF)):
    die(u"三条方向里有一条不成立了（开 %s/%s 峰 %s 对 关 %s/%s 峰 %s）⇒ 正文要按新形状重写"
        % (SPAN_A, OLD_A, PEAK_A, SPAN_OFF, OLD_OFF, PEAK_OFF))
if u"可分帧=" not in PILL_SETTLE:
    die(u"_SETTLE 那行没带可分帧 ⇒ 出口谓词的数没地方解析：%s" % PILL_SETTLE[:160])
if u"冷闸=true" not in PILL:
    die(u"有一臂是在冷采样下抓的 ⇒ 这一轮的结论今天不成立：%s" % PILL[:200])

# —— runner 交账（R321 那笔的下游）——
runner = log_read(RUNNER_LOG, u"runner 的 SELARM 读数")
RUN_SUM = strip_step((re.findall(r"(?m)^.*QUICKPICK_SELARM_SUMMARY .+$", runner) or [None])[-1])
RUN_BANDS = strip_step((re.findall(r"(?m)^.*QUICKPICK_SELARM_BANDS dark .+$", runner) or [None])[-1])
if u"有对象=2" not in RUN_SUM or u"未判=0" not in RUN_SUM:
    die(u"runner 那一跑还没兑现（%s）⇒ 373 的追记不能这么写" % RUN_SUM[:160])
if u"落点=light=系统nonKey dark=系统nonKey" not in RUN_SUM:
    die(u"runner 两档落点不是都 nonKey：%s" % RUN_SUM[:200])
if u"选择=前导" not in RUN_BANDS:
    die(u"runner 的页底选择不是前导 ⇒ R321 的修没生效：%s" % RUN_BANDS[:200])
RUN_SELARM_DARK = strip_step((re.findall(r"(?m)^.*QUICKPICK_SELARM dark .+$", runner) or [None])[-1])
if u"页底来源=前导" not in RUN_SELARM_DARK or u"判定=系统nonKey" not in RUN_SELARM_DARK:
    die(u"runner 暗档那一行不像是修好之后的形状：%s" % RUN_SELARM_DARK[:220])
SEL_BANDS = (re.findall(r"(?m)^QUICKPICK_SELARM_BANDS light .+$", cap) or [None])[-1]
if not SEL_BANDS or u"页底档=252" not in SEL_BANDS:
    die(u"本机这一跑的 BANDS 行读不到或页底档变了（%s）⇒ 375 追记里那两个数没有出处"
        % s(SEL_BANDS)[:160])
if u"页底档=52" not in RUN_BANDS:
    die(u"runner 的页底档不是 52 ⇒ 那条机器差异的数要重写：%s" % RUN_BANDS[:200])

# —— 刀 ——
knife = log_read(KNIFE_LOG, u"变异表")
kn = re.findall(r"CAUGHT=(\d+)/(\d+), RESTORE_CLEAN=(\w+)", knife)
if not kn:
    die(u"变异表没打汇总行")
K_CAUGHT, K_TOTAL, K_RESTORE = (x for x in kn[-1])
if K_RESTORE != u"yes":
    die(u"RESTORE_CLEAN=%s ⇒ 盘上可能是被注入的版本" % K_RESTORE)
arm_lines = re.findall(r"(?m)^(M9\d\d) (CAUGHT|MISMATCH|PASSED|NOT_RUN) .+$", knife)
if len(arm_lines) != int(K_TOTAL):
    die(u"逐臂行数 %d 与分母 %s 不等" % (len(arm_lines), K_TOTAL))
if int(K_CAUGHT) != int(K_TOTAL) or int(K_TOTAL) != 3:
    die(u"刀没全抓到：CAUGHT=%s/%s（逐臂=%s）"
        % (K_CAUGHT, K_TOTAL, u"; ".join(u"%s=%s" % (a, b) for a, b in arm_lines)))
KNIFELINE = (u"CAUGHT=%s/%s, RESTORE_CLEAN=%s" % (K_CAUGHT, K_TOTAL, K_RESTORE))
KNIFEARMS = u"；".join(u"%s %s" % (a, b) for a, b in arm_lines)

pc, _rc = sh([sys.executable, PRECHECK])
pre_line = re.findall(r"NEEDLE_PRECHECK tables=(\d+) covered=(\d+) arms=(\d+) bad=(\d+)", pc)
if not pre_line:
    die(u"NEEDLE_PRECHECK 没读到")
TABLES_N, COVERED, _PA, PRE_BAD = (int(x) for x in pre_line[-1])
if PRE_BAD:
    die(u"针预检 bad=%d ⇒ 有 needle 在册上腐烂" % PRE_BAD)
if u"mutate_r322" not in pc:
    die(u"本轮的表没进预检名册（新表出厂第一天就要在册）")
reg_line = re.findall(r"ARM_TOTAL files=(\d+) arms=(\d+) dupes=(\d+) repeats=(\d+)", pc)
if not reg_line:
    die(u"ARM_TOTAL 没读到")
ARM_FILES, ARM_REG, ARM_DUPES, ARM_REPEATS = (int(x) for x in reg_line[-1])
if ARM_DUPES or ARM_REPEATS:
    die(u"名册报 dupes=%d repeats=%d" % (ARM_DUPES, ARM_REPEATS))

# —— 新读数族必须真的进了搬运名单（R107 / U-339 那一族）——
rm, rmc = sh([sys.executable, ROWS, PILL_LOG, u"--must-include",
              u"MOTION_PILL_SLIDE", u"MOTION_PILL_SLIDE_SETTLE"])
io.open(ROWS_LOG, u"w", encoding="utf-8").write(rm)
must = re.findall(r"READINGS_MUST_INCLUDE 声明=(\d+) 缺=(\d+)", rm)
if not must:
    die(u"搬运名单那把尺没打结论行（rc=%d）" % rmc)
MUST_DECL, MUST_MISS = (int(x) for x in must[-1])
if MUST_MISS or MUST_DECL != 2:
    die(u"本轮的新读数族没被搬走（声明=%d 缺=%d）⇒ 先回 ledger_rows.py 补名单" % (MUST_DECL, MUST_MISS))
MUST_INCLUDE = u"声明=%d 缺=%d" % (MUST_DECL, MUST_MISS)

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
if int(STREAK_N) < 1:
    die(u"本轮没动产品，连续零改动轮数却读到 %s ⇒ 取数口与改动面矛盾，先查哪一个错" % STREAK_N)
LASTSHA = (re.findall(r"last=(\w+)", st_out) or [u""])[-1]
LASTROUND = (re.findall(r"last_round=(\d+)", st_out) or [u""])[-1]
prev_out, prev_rc = sh([sys.executable, STREAK, u"--streak-for", s(PREV_ROUND)])
PREV_STREAK = (re.findall(r"streak=(\d+)", prev_out) or [u""])[-1]
if prev_rc != 0 or not PREV_STREAK:
    die(u"上一轮的产品面轮数读不到")
if int(STREAK_N) <= int(PREV_STREAK):
    die(u"连续零改动轮数没往上走（%s → %s）⇒ 取数口与本轮不同源" % (PREV_STREAK, STREAK_N))
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
UA, UB, UC, UD = U_MAX + 1, U_MAX + 2, U_MAX + 3, U_MAX + 4
dec = rd(FILES[u"DEC"])
DN = max(int(x) for x in re.findall(r"(?m)^\*\*D-(\d{3,4})（", dec)) + 1
bl = rd(FILES[u"BL"])
BL_MAX = max(int(x) for x in re.findall(r"(?m)^\*\*(\d{3})\. ", bl))
if BL_MAX != GUT_HOUSE:
    die(u"BACKLOG 现读最大是 %d，台账准备的最后一条是 %d ⇒ 有人先开了单" % (BL_MAX, GUT_HOUSE))
for need in (ENTRY_373, ANCHOR_AFTER_373, GUT_HOUSE):
    if u"**%d. " % need not in bl:
        die(u"BACKLOG %d 不在盘上 ⇒ 追记的锚点没有出处" % need)
if bl.index(u"**%d. " % ENTRY_373) > bl.index(u"**%d. " % ANCHOR_AFTER_373):
    die(u"%d 在 %d 之后 ⇒ 373 的追记插入点算错了" % (ENTRY_373, ANCHOR_AFTER_373))

SUBS = {u"@ROUND@": ROUND, u"@RTAG@": R_TAG, u"@RPREVTAG@": PREV_TAG, u"@RNEXT@": R_NEXT,
        u"@RDN@": RDN, u"@TODAY@": TODAY, u"@UA@": UA, u"@UB@": UB, u"@UC@": UC, u"@UD@": UD,
        u"@DN@": DN, u"@BLMAX@": BL_MAX, u"@BLMINUS@": GUT_HOUSE, u"@BLPREV@": NEEDLE_HOUSE,
        u"@BATT@": pre, u"@SKIP@": pre_skip, u"@STREAK@": STREAK_N, u"@PREVSTREAK@": PREV_STREAK,
        u"@LASTSHA@": LASTSHA, u"@LASTROUND@": LASTROUND, u"@CI@": CI, u"@HALINE@": HA_LINE,
        u"@ROT@": ROT_NOW, u"@OPAQUE@": OPAQUE_NOW, u"@HIDTBL@": DECLARED_TBL,
        u"@HIDTBL2@": REMAIN_TABLES, u"@TABLES@": TABLES_N, u"@COVERED@": COVERED,
        u"@PREBAD@": PRE_BAD, u"@ARMREG@": ARM_REG, u"@ARMFILES@": ARM_FILES,
        u"@WARN@": WARN, u"@FULL@": FULL, u"@CAPT@": CAPT, u"@BASE@": BASE,
        u"@RVLINE@": RVLINE, u"@KNIFELINE@": KNIFELINE, u"@KNIFEARMS@": KNIFEARMS,
        u"@PILL@": PILL, u"@PILL_SETTLE@": PILL_SETTLE, u"@PILL_EXEC@": PILL_EXEC,
        u"@SPAN_A@": SPAN_A, u"@SPAN_OFF@": SPAN_OFF, u"@OLD_A@": OLD_A, u"@OLD_OFF@": OLD_OFF,
        u"@PEAK_A@": PEAK_A, u"@PEAK_OFF@": PEAK_OFF, u"@SETTLE_MS@": SETTLE_MS,
        u"@INTERVAL@": INTERVAL,
        u"@RUN_SUM@": RUN_SUM, u"@RUN_BANDS@": RUN_BANDS, u"@SEL_BANDS@": SEL_BANDS,
        u"@MUST_INCLUDE@": MUST_INCLUDE, u"@HEADSHA@": head_sha}
EYE = fill(EYE, SUBS)
SUBS[u"@EYE@"] = EYE
SUBS[u"@EYE_SHORT@"] = EYE.split(u"⇒")[0].strip()

if not os.path.exists(BODIES):
    die(u"正文文件 %s 不在盘上" % BODIES)
ns = {}
exec(compile(rd(BODIES), BODIES, u"exec"), ns)
for k in (u"UI_NEW", u"IT_NEW", u"DEC_NEW", u"CH_NEW", u"ST_NEW", u"BL_追记_373", u"BL_追记_375"):
    if k not in ns:
        die(u"正文缺 %s" % k)

orig = {k: rd(v) for k, v in FILES.items()}
for key, marker in ((u"UI", u"## 第 %d 轮" % ROUND), (u"IT", u"## Round %d ·" % RDN),
                    (u"ST", u"## %s 状态（" % R_TAG)):
    if marker in orig[key]:
        die(u"%s 里已经有本轮那一节 ⇒ 生成器不许重跑第二遍" % key)

texts = {u"UI": fill(ns[u"UI_NEW"], SUBS), u"IT": fill(ns[u"IT_NEW"], SUBS),
         u"DEC": fill(ns[u"DEC_NEW"], SUBS), u"CH": fill(ns[u"CH_NEW"], SUBS),
         u"ST": fill(ns[u"ST_NEW"], SUBS),
         u"ADD373": fill(ns[u"BL_追记_373"], SUBS), u"ADD375": fill(ns[u"BL_追记_375"], SUBS)}
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
if nums != [UA, UB, UC, UD]:
    die(u"新节的 U 定义行是 %s，要 %s" % (nums, [UA, UB, UC, UD]))
new_it = orig[u"IT"].rstrip(u"\n") + u"\n\n" + texts[u"IT"].rstrip(u"\n") + u"\n"
if len(re.findall(u"(?m)^\\| (真实视觉审查|判据有效性|假绿防御|产品面推进|台账一致性|交付诚实性|可复核性) \\| (\\d+)/15 \\|$",
                  texts[u"IT"])) != 7:
    die(u"七维表不是恰好 7 行")
new_dec = orig[u"DEC"].rstrip(u"\n") + u"\n\n" + texts[u"DEC"].rstrip(u"\n") + u"\n"
# BACKLOG：两处追记 —— 373 的插在 `**374. ` 之前，375 的（最后一条）追加在文件尾
anchor = u"\n**%d. " % ANCHOR_AFTER_373
pos = orig[u"BL"].find(anchor)
if pos < 0:
    die(u"找不到 %s 这一行的位置 ⇒ 373 的追记没有插入点" % (anchor.strip()))
new_bl = (orig[u"BL"][:pos] + u"\n" + texts[u"ADD373"].rstrip(u"\n") + orig[u"BL"][pos:])
new_bl = new_bl.rstrip(u"\n") + u"\n\n" + texts[u"ADD375"].rstrip(u"\n") + u"\n"
for house in (ENTRY_373, GUT_HOUSE):
    if u"**%d. " % house not in new_bl:
        die(u"追记之后 %d 那一单反而不见了" % house)
if new_bl.count(u"追记（%s）" % R_TAG) != 2:
    die(u"本轮说好两处追记，现读 %d 处" % new_bl.count(u"追记（%s）" % R_TAG))
# 373 的追记必须落在 373 与 374 之间；375 是最后一条，它的追记必须在文件尾
if not (new_bl.index(u"**%d. " % ENTRY_373) < new_bl.index(u"追记（%s）" % R_TAG)
        < new_bl.index(u"**%d. " % ANCHOR_AFTER_373)):
    die(u"%d 的追记落错了条目（不在 %d 与 %d 之间）" % (ENTRY_373, ENTRY_373, ANCHOR_AFTER_373))
if not (new_bl.index(u"**%d. " % GUT_HOUSE) < new_bl.rindex(u"追记（%s）" % R_TAG)):
    die(u"%d 的追记没接在最后一条之后" % GUT_HOUSE)
before = len(re.findall(u"(?m)^\\*\\*(\\d{3})\\. ", orig[u"BL"]))
after = len(re.findall(u"(?m)^\\*\\*(\\d{3})\\. ", new_bl))
if after != before:
    die(u"BACKLOG 条目数从 %d 变成 %d（本轮说好只写追记、不开新单）" % (before, after))
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
            u"U-31 … U-%d（%s 现读抬到最新一节）" % (UD, R_TAG), fr, count=1)
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
        sys.stderr.write(u"R322_CRASH_RESTORED 未捕获异常 ⇒ 七本已整体还原\n")


atexit.register(_crash_guard)

txt = rd(FILES[u"FR"])
out, crc = sh([sys.executable, CURVE])
rounds_after = (re.findall(r"^ROUNDS=(\d+)", out, re.M) or [u""])[-1]
last_round = (re.findall(r"^PHASE2 n=\d+ rounds=9\.\.(\d+)", out, re.M) or [u""])[-1]
tail = (re.findall(r"^SCORES_BY_ROUND (.+)$", out, re.M) or [u""])[-1]
if not rounds_after or not last_round or not tail:
    die(u"写盘后曲线尺没给全（rc=%d）" % crc)
lines = txt.split(u"\n")
m2 = re.search(u"R9–R(\\d+)，(\\d+) 节自评", lines[0])
if not m2 or lines[0].count(u"R9–R") != 1:
    die(u"报告标题那一行没找到 `R9–R<NNN>，<NNN> 节自评`")
lines[0] = lines[0][:m2.start()] + u"R9–R%s，%s 节自评" % (last_round, rounds_after) + lines[0][m2.end():]
body = u"\n".join(lines)

prod_cell = (u"- **产品面（这一节最该被读的部分）**：本轮产品文件 0 个（**判据轮**：git 现读改动面 = %d 个文件，"
             u"产品 0 个、判据 1 个（`MotionFilmstripTests.swift`）；五腿**全部适用且都跑了**：%s；全量卷 %s；"
             u"重捕 %s；基线 %s；四件套 %s。产品面连续零改动轮数 = **%s**"
             u"（R%d 那笔产品改动之后重新起算；唯一取数口 `python3 scripts/product_streak.py --streak-for %s`，"
             u"`--check` 同形；上一轮那一格是 %s）。"
             u"本轮是**动效主线**：全仓唯一一条位移档（`.slider`）第一次有过程证人 —— %s；%s"
             u"（开臂中间态帧数 %s 对关臂 %s、旧口径 %s 对 %s、峰值 %s 对 %s）⇒ 看得见，当场升成硬判据。"
             u"摔过一次并记账：第一版根视图是手搭 Binding 的替身（没人观察 store）⇒ 两臂峰值 0.000，"
             u"是前提闸门把它拦成红而不是绿（D-@DN@）。三把刀：%s。"
             % (len(touched), WARN, FULL, CAPT, BASE, RVLINE, STREAK_N, ROUND - 1, ROUND,
                PREV_STREAK, PILL, PILL_SETTLE, SPAN_A, SPAN_OFF, OLD_A, OLD_OFF,
                PEAK_A, PEAK_OFF, KNIFELINE))
scale_cell = (u"- **判据与门的规模**：脚本电池现读 **Ran %s**（写盘后同数），"
              u"变异臂在册 **%s** 把 / %s 张表（预检 tables=%s covered=%s bad=%s）；"
              u"腐烂针尺现读 `%s`；U 定义行 **%s 条**、最大 **U-%s**；决定台账最大 **D-%d**，"
              u"BACKLOG 最大 **%d**（本轮不开新单，给 %d 与 %d 各写一处追记）；"
              u"新读数族搬运名单 `READINGS_MUST_INCLUDE %s`"
              % (pre, ARM_REG, ARM_FILES, TABLES_N, COVERED, PRE_BAD, HA_LINE,
                 len(re.findall(u"(?m)^- \\*\\*U-(\\d{3,4})[：(]", new_ui)), UD, DN, BL_MAX,
                 ENTRY_373, GUT_HOUSE, MUST_INCLUDE))
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
chk_out, chk = sh([sys.executable, u"-m", u"unittest", u"-v",
                   u"test_final_report_headline.FinalReportSourcesCellTests.test_the_sources_cell_agrees_with_git"],
                  cwd=os.path.join(ROOT, "scripts", "tests"))
if chk != 0:
    die(u"§13 的 Sources 那一格与 git 不同源（rc=%d）：%s" % (chk, chk_out.strip()[-300:]))
rf, rfc = sh([sys.executable, os.path.join(ROOT, ".scratch", "motion-audit-2",
                                           "refresh_report_section1.py")])
if rfc != 0 or u"REFUSED" in rf:
    die(u"§1 那一格的刷新器没签（rc=%d）：%s" % (rfc, rf.strip()[-200:]))

post, post_skip = battery(u"写盘后", u"/tmp/r322_battery_post.log")
if (post, post_skip) != (pre, pre_skip):
    die(u"电池计数变了（%s/%s → %s/%s）" % (pre, pre_skip, post, post_skip))
ck2, crc = sh([sys.executable, STREAK, u"--check"])
if crc != 0:
    die(u"353 的门不认这版台账：" + (ck2 + u"\n").strip()[-400:])
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
if u"U-31 … U-%d" % UD not in rd(FILES[u"FR"]):
    die(u"报告 §1 的 U 上界不是本轮的 U-%d" % UD)

OK_EXIT.append(True)
print(u"LEDGERS_R322 OK batt=Ran " + post + u" (skipped=" + post_skip + u") streak=" + STREAK_N
      + u"(上一轮 " + PREV_STREAK + u") 产品文件=" + s(len(product_touched))
      + u" 改动面=" + s(len(touched)) + u" 帧=" + s(CAPT_N) + u"/" + s(CM) + u" 基线changed=" + s(BC)
      + u" 刀=" + K_CAUGHT + u"/" + K_TOTAL + u" restore=" + K_RESTORE
      + u" 过程证人=开" + SPAN_A + u"/关" + SPAN_OFF + u" 峰" + PEAK_A + u"vs" + PEAK_OFF
      + u" 搬运=" + MUST_INCLUDE + u" 预检bad=" + s(PRE_BAD) + u" 在册=" + s(ARM_REG) + u"/"
      + s(ARM_FILES) + u"表 rot=" + s(ROT_NOW) + u" 抽不出=" + s(OPAQUE_NOW)
      + u" U=" + s(UA) + u".." + s(UD) + u" D=" + s(DN) + u" BL最大=" + s(BL_MAX)
      + u" derived(Round " + s(RDN) + u")=" + s(DERIVED2)
      + u" report尾轮=Round " + s(last_round) + u" 节数=" + s(rounds_after))
