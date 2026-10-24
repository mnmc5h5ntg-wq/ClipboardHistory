# -*- coding: utf-8 -*-
u"""R327 的七本台账（第 326 轮 / Round 324 · 动效主线：384 的修法①证伪并撤回 + 被拒段洞宽那一格）。

与 r326 的三处不同：
① 主菜不是新读数的**结论**而是一次**证伪** ⇒ 生成器不许把"两版实验的读数"当现读抄进来：
   只有撤回之后留在盘上的那一条 GEOM 行算读数，实验版那两条在正文里被明写成"未留档"；
② 解析对象换成胶囊那两把判据的整跑（`MOTION_PILL_RAMP_GEOM` 的候选段列表）：
   被拒段与通过段的洞宽必须各自解析出数，且要求 被拒 < 通过 —— 这一条就是"降地板是错的修法"的出处；
③  那一半读的是 @RPREVTAG@ 的 runner 跑（新口径的分类 + `_MAGNITUDE` 的方向 + `粒度不可比`），
   三格都要现读，读不到就拒写。

跑法：PYTHONUTF8=1 python3 .scratch/motion-audit-2/ledgers_r327.py --eye "<看图腿正文>"
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
BODIES = os.path.join(ROOT, ".scratch", "motion-audit-2", "r327_bodies.txt")
RV = u"/tmp/r327_rv"
KNIFE_LOG = os.path.join(RV, u"mutate_r327.log")
PILL_LOG = os.path.join(RV, u"pill.log")
WITNESS_LOG = os.path.join(RV, u"pillramp.log")
RUNNER_LOG = os.path.join(RV, u"runner.log")
LOCAB_LOG = u"/tmp/r326_rv/film.log"
ROWS_LOG = u"/tmp/r327_rows.log"
FILM = u"ClipboardHistory/Tests/ClipboardHistoryAppTests/MotionFilmstripTests.swift"
WITNESS = u"ClipboardHistory/Tests/ClipboardHistoryAppTests/MotionPillRampTests.swift"
TODAY = u"2026-10-24"
R_TAG, PREV_TAG, R_NEXT = u"R327", u"R326", u"R328"
RTAGNUM = u"327"
PREV_ROUND, ROUND, RDN = 325, 326, 324
RUN_ID = u"40076227591"
RUN_SHA = u"255354f"
BL_MAX_PREV = 387
NEW_ENTRIES = 1
BL_ADDED = 384
BL_ADDED2 = 387
U_COUNT = 4
WROTE, OK_EXIT = [], []


def die(msg):
    sys.stderr.write(u"R327_LEDGERS_REFUSE %s\n" % msg)
    if WROTE:
        for key, text in orig.items():
            wr(FILES[key], text)
        sys.stderr.write(u"R327_RESTORED 七本已整体还原\n")
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


def last(text, pattern, label):
    hits = re.findall(pattern, text)
    if not hits:
        die(u"读不到 %s（正则 %s）" % (label, pattern[:60]))
    return hits[-1]


def strip_step(line):
    m = re.match(r"^\s*\[[^\]]*\]\s*(.*)$", line)
    return (m.group(1) if m else line).strip()


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


def knife_summary(path, label, want):
    text = log_read(path, label)
    kn = re.findall(r"CAUGHT=(\d+)/(\d+), RESTORE_CLEAN=(\w+)", text)
    if not kn:
        die(u"%s 没打汇总行" % label)
    caught, total, restore = kn[-1]
    if restore != u"yes":
        die(u"%s RESTORE_CLEAN=%s ⇒ 盘上可能是被注入的版本" % (label, restore))
    arms = re.findall(r"(?m)^(M9\d\d) (CAUGHT|MISMATCH|PASSED|NOT_RUN) .+$", text)
    if len(arms) != int(total):
        die(u"%s 逐臂行数 %d 与分母 %s 不等" % (label, len(arms), total))
    if int(caught) != int(total) or int(total) != want:
        die(u"%s 没全抓到：CAUGHT=%s/%s（逐臂=%s）"
            % (label, caught, total, u"; ".join(u"%s=%s" % (a, b) for a, b in arms)))
    return (u"CAUGHT=%s/%s, RESTORE_CLEAN=%s" % (caught, total, restore),
            u"；".join(u"%s %s" % (a, b) for a, b in arms))


STRAY_RX = re.compile(u"@([A-Z][A-Z0-9_]{1,24})@")
ap = argparse.ArgumentParser(prog="ledgers_r327.py", description=u"R327 的七本台账（384 证伪 + 洞宽那一格）")
ap.add_argument(u"--eye", default=os.environ.get(u"R327_EYE", u""),
                help=u"看图腿正文（也可用环境变量 R327_EYE 传）")
ARGS = ap.parse_args()
EYE = ARGS.eye.strip()
if not EYE:
    die(u"看图腿没传 R327_EYE / --eye ⇒ 真实视觉审查不许省略，也不许凭记忆写")

pre, pre_skip = battery(u"写盘前", u"/tmp/r327_battery_pre.log")

# —— 改动面：判据轮（产品 0 文件），且必须含两颗判据文件 ——
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
for need in (FILM, WITNESS):
    if need not in touched:
        die(u"改动面里找不到 %s" % need)
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
if int(re.findall(r"and (\d+) failures?", FULL)[-1]) != 0:
    die(u"全量卷有红：%s ⇒ 先归因再落账" % FULL)

witness_log = log_read(WITNESS_LOG, u"判据卷 MotionPillRampTests")
w_rows = re.findall(r"Executed (\d+) tests?, with (\d+) failures", witness_log)
if not w_rows:
    die(u"判据卷读不到汇总行（0 skip 时那行没有 skipped 段，正则别写死）")
WEXEC = max(int(x[0]) for x in w_rows)
if max(int(x[1]) for x in w_rows) != 0:
    die(u"判据卷有红")
PURE_EXEC = (u"%d 格全绿（本轮新增 1 格：被拒段必须带洞宽，且分母不许是洞自己）" % WEXEC)
if WEXEC <= 27:
    die(u"判据卷还是 %d 格 ⇒ 本轮那格新证人没进卷" % WEXEC)

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

# —— 本轮的主菜：带子定位那一格（撤回之后留档的唯一一条）——
pill = log_read(PILL_LOG, u"胶囊两把判据整跑")
GEOM = last(pill, r"(?m)^MOTION_PILL_RAMP_GEOM .+$", u"MOTION_PILL_RAMP_GEOM")
PILL = last(pill, r"(?m)^MOTION_PILL_SLIDE filter-pill-slide .+$", u"MOTION_PILL_SLIDE")
seg_rx = re.compile(r"y(\d+)\.\.(\d+)px 高(\d+)px 判=(\S+) 洞宽=(\d+)%")
segs = seg_rx.findall(GEOM)
if not segs:
    die(u"GEOM 行里没有一格带洞宽的候选段 ⇒ 本轮那一格没落地（正文全部结论没出处）：\n%s" % GEOM[:260])
rejected = [(int(h), int(p)) for _a, _b, _c, gate, p in segs if gate != u"过" for h in [int(_c)]]
accepted = [(int(h), int(p)) for _a, _b, _c, gate, p in segs if gate == u"过" for h in [int(_c)]]
if not rejected or not accepted:
    die(u"候选段里必须同时有一段被拒与一段通过，才能比'差多少'（读到 %s）" % segs)
REJ_H, REJ_HOLE = max(rejected)
ACC_H, ACC_HOLE = max(accepted)
if REJ_HOLE >= ACC_HOLE:
    die(u"被拒段的洞宽(%d%%) 不小于通过段(%d%%) ⇒ '降地板是错的修法'这句话没出处，"
        u"先查定位是不是换了对象" % (REJ_HOLE, ACC_HOLE))
if ACC_HOLE - REJ_HOLE < 15:
    die(u"两段只差 %d 个百分点 ⇒ 这是'刚过线'，降地板就不是错的修法；正文那句'差一倍'要改写"
        % (ACC_HOLE - REJ_HOLE))
TAKEN = last(GEOM, r"取用=(\S+)", u"取用那一格")
if TAKEN == u"无":
    die(u"撤回之后带子还是读不出来 ⇒ 撤回没做干净（实验版才该读'无'）")
GEOM_SHORT = u"行带=%s 候选段里被拒那一段 高%dpx 洞宽=%d%%，通过那一段 高%dpx 洞宽=%d%%" % (
    last(GEOM, r"行带=(\S+)", u"行带"), REJ_H, REJ_HOLE, ACC_H, ACC_HOLE)
exec_hits = re.findall(r"Executed (\d+) tests?, with (?:(\d+) tests? skipped and )?(\d+) failures?", pill)
if not exec_hits:
    die(u"胶囊整卷读不到汇总行")
big = max(exec_hits, key=lambda t: int(t[0]))
if big[2] != u"0":
    die(u"胶囊两把判据整跑有红（%s）⇒ 先归因再落账" % (big,))
PILL_EXEC = u"Executed %s tests, with %s tests skipped and %s failures（testFilterPill 两格，开 CLIPBOARD_HISTORY_UI_MOTION）" % (
    big[0], big[1] or u"0", big[2])

# —— ⓪：@RPREVTAG@ 那一跑在 runner 上读到什么 ——
runner_txt = log_read(RUNNER_LOG, u"runner 读数（R326 那一跑）")
RUN_AB_SUMMARY = strip_step(last(runner_txt, r"(?m)^.*MOTION_SCENARIO_AB_SUMMARY .+$", u"runner 的 _SUMMARY"))
rm = re.search(r"场景=(\d+) 同=(\d+) 漂=(\d+) 敏感=(\d+) 换对象=(\d+) 粒度不可比=(\d+)", RUN_AB_SUMMARY)
if not rm:
    die(u"runner 的 _SUMMARY 形状变了（要带 粒度不可比=）：%s" % RUN_AB_SUMMARY[:200])
RUN_AB_COUNTS = u"同=%s 漂=%s 敏感=%s 换对象=%s" % rm.group(2, 3, 4, 5)
RUN_SENS_N, RUN_GAP = int(rm.group(4)), int(rm.group(6))
if RUN_GAP != 0:
    die(u"runner 的 粒度不可比=%d ⇒ @RTAG@ 那条容差在第二台机器上误报了，先归因（不许放宽容差）" % RUN_GAP)
RUN_MAG = strip_step(last(runner_txt, r"(?m)^.*MOTION_SCENARIO_AB_MAGNITUDE .+$", u"runner 的 _MAGNITUDE"))
mm = re.search(r"有变化=(\d+) 亮臂更大=(\d+) 暗臂更大=(\d+) 比值暗除亮=(\S+)（", RUN_MAG)
if not mm:
    die(u"runner 的 _MAGNITUDE 形状变了：%s" % RUN_MAG[:200])
RUN_N, RUN_SIDE, RUN_DARK, RUN_RANGE = int(mm.group(1)), int(mm.group(2)), int(mm.group(3)), mm.group(4)
if RUN_SIDE != RUN_N or RUN_DARK != 0:
    die(u"runner 的墨量方向不是单侧（亮 %d / 暗 %d / 共 %d）⇒ '系统偏移'这一条只在**本机**成立，"
        u"387 的追记要改写成'按机器分列'" % (RUN_SIDE, RUN_DARK, RUN_N))
RUN_MAG_SHORT = u"有变化=%d 亮臂更大=%d 暗臂更大=%d 比值暗除亮=%s" % (RUN_N, RUN_SIDE, RUN_DARK, RUN_RANGE)
NOT_RUN_PILL = sorted(set(re.findall(r"(?m)^.*MOTION_NOT_RUN=(pill-[\w-]+) ", runner_txt)))
if u"pill-slide-arms-indistinguishable" not in NOT_RUN_PILL \
        or u"pill-ramp-no-intermediate" not in NOT_RUN_PILL:
    die(u"runner 的两朵命名出口没同时露面（读到 %s）" % NOT_RUN_PILL)
if re.findall(r"(?m)^.*MOTION_FLOOR_SUITE_CLEAN=(\d+)", runner_txt)[-1] != u"0":
    die(u"runner 的 suite-clean 不是 0 ⇒ §8 那一格没归零")
RUN_PILL_BAND = strip_step(last(runner_txt, r"(?m)^.*MOTION_PILL_RAMP_GEOM .+$", u"runner 的 GEOM"))
if u"色档=胶片暗" not in RUN_PILL_BAND:
    die(u"runner 的 GEOM 没有 色档=胶片暗 ⇒ R324 那一钉在第二台机器上没生效")

# 本机对照（@RPREVTAG@ 那一跑留档的那条，不是本轮重跑的）
loc = log_read(LOCAB_LOG, u"@RPREVTAG@ 本机那一跑的胶片卷")
LOC_MAG = last(loc, r"(?m)^MOTION_SCENARIO_AB_MAGNITUDE .+$", u"本机的 _MAGNITUDE")
lm = re.search(r"有变化=(\d+) 亮臂更大=(\d+) 暗臂更大=(\d+) 比值暗除亮=(\S+)（", LOC_MAG)
if not lm:
    die(u"本机 _MAGNITUDE 形状变了：%s" % LOC_MAG[:200])
LOC_N, LOC_SIDE, LOC_DARK, LOC_RANGE = int(lm.group(1)), int(lm.group(2)), int(lm.group(3)), lm.group(4)
LOC_SENS_N = int(re.search(r"敏感=(\d+)", last(loc, r"(?m)^MOTION_SCENARIO_AB_SUMMARY .+$",
                                               u"本机的 _SUMMARY")).group(1))
LOC_AB_COUNTS = last(loc, r"(?m)^MOTION_SCENARIO_AB_SUMMARY .+$", u"本机的 _SUMMARY")
LOC_AB_COUNTS = re.search(r"同=\d+ 漂=\d+ 敏感=\d+ 换对象=\d+", LOC_AB_COUNTS).group(0)
LOC_MAG_SHORT = u"有变化=%d 亮臂更大=%d 暗臂更大=%d 比值暗除亮=%s" % (LOC_N, LOC_SIDE, LOC_DARK, LOC_RANGE)
if (LOC_SIDE, LOC_DARK) != (RUN_SIDE, RUN_DARK):
    die(u"两台的墨量方向不一致（本机 亮%d/暗%d，runner 亮%d/暗%d）⇒ 387 的追记要按机器分列，"
        u"不能写成一条" % (LOC_SIDE, LOC_DARK, RUN_SIDE, RUN_DARK))

# —— 刀：一支表 ——
KNIFELINE, KNIFEARMS = knife_summary(KNIFE_LOG, u"本轮变异表（M949…M951）", 3)

pc, _rc = sh([sys.executable, PRECHECK])
pre_line = re.findall(r"NEEDLE_PRECHECK tables=(\d+) covered=(\d+) arms=(\d+) bad=(\d+)", pc)
if not pre_line:
    die(u"NEEDLE_PRECHECK 没读到")
TABLES_N, COVERED, _PA, PRE_BAD = (int(x) for x in pre_line[-1])
if PRE_BAD:
    die(u"针预检 bad=%d ⇒ 有 needle 在册上腐烂" % PRE_BAD)
if u"mutate_r327" not in pc:
    die(u"mutate_r327 不在预检名册里（新表出厂第一天就要在册）")
reg_line = re.findall(r"ARM_TOTAL files=(\d+) arms=(\d+) dupes=(\d+) repeats=(\d+)", pc)
if not reg_line:
    die(u"ARM_TOTAL 没读到")
ARM_FILES, ARM_REG, ARM_DUPES, ARM_REPEATS = (int(x) for x in reg_line[-1])
if ARM_DUPES or ARM_REPEATS:
    die(u"名册报 dupes=%d repeats=%d" % (ARM_DUPES, ARM_REPEATS))

FAMILIES = [u"MOTION_PILL_RAMP_GEOM", u"MOTION_PILL_SLIDE", u"MOTION_PILL_BAND"]
rm2, rmc = sh([sys.executable, ROWS, PILL_LOG] + [u"--must-include"] + FAMILIES)
io.open(ROWS_LOG, u"w", encoding="utf-8").write(rm2)
must = re.findall(r"READINGS_MUST_INCLUDE 声明=(\d+) 缺=(\d+)", rm2)
if not must:
    die(u"搬运名单那把尺没打结论行（rc=%d）" % rmc)
MUST_DECL, MUST_MISS = (int(x) for x in must[-1])
if MUST_MISS or MUST_DECL != len(FAMILIES):
    die(u"本轮的读数族没被搬走（声明=%d 缺=%d）⇒ 先回 ledger_rows.py 补名单" % (MUST_DECL, MUST_MISS))
MUST_INCLUDE = u"声明=%d 缺=%d" % (MUST_DECL, MUST_MISS)

ha_out, ha_rc = sh([sys.executable, HA])
HA_LINE = (re.findall(r"(?m)^HIDDEN_ARMS .+$", ha_out) or [u""])[-1]
if u"处置=ok" not in HA_LINE:
    die(u"腐烂针尺自己没签（rc=%d）：%s" % (ha_rc, HA_LINE[:160]))
ROT_NOW = (re.findall(r"rot=(\d+)", HA_LINE) or [u""])[-1]
OPAQUE_NOW = (re.findall(r"抽不出=(\d+)", HA_LINE) or [u"", u""])[-1]

st_out, st_rc = sh([sys.executable, STREAK, u"--streak-for", s(ROUND)])
STREAK_N = (re.findall(r"streak=(\d+)", st_out) or [u""])[-1]
if st_rc != 0 or not STREAK_N:
    die(u"product_streak 读不到（rc=%d）" % st_rc)
prev_out, prev_rc = sh([sys.executable, STREAK, u"--streak-for", s(PREV_ROUND)])
PREV_STREAK = (re.findall(r"streak=(\d+)", prev_out) or [u""])[-1]
if prev_rc != 0 or not PREV_STREAK or int(STREAK_N) <= int(PREV_STREAK):
    die(u"连续零改动轮数不对（%s → %s）" % (PREV_STREAK, STREAK_N))

ci, _ = sh([sys.executable, os.path.join(ROOT, "scripts", "ci_read.py"), u"latest"])
CI = ci.strip().replace(u"\n", u" ")
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
D0 = max(int(x) for x in re.findall(r"(?m)^\*\*D-(\d{3,4})（", dec)) + 1
D1, D2 = D0, D0 + 1
bl = rd(FILES[u"BL"])
BL_MAX = max(int(x) for x in re.findall(r"(?m)^\*\*(\d{3})\. ", bl))
if BL_MAX != BL_MAX_PREV:
    die(u"BACKLOG 现读最大是 %d，台账准备的最后一条是 %d ⇒ 有人先开了单" % (BL_MAX, BL_MAX_PREV))
B1 = BL_MAX + 1

SUBS = {u"@ROUND@": ROUND, u"@RTAG@": R_TAG, u"@RTAGNUM@": RTAGNUM, u"@RPREVTAG@": PREV_TAG,
        u"@RNEXT@": R_NEXT, u"@RDN@": RDN, u"@TODAY@": TODAY, u"@RUNID@": RUN_ID, u"@RUNSHA@": RUN_SHA,
        u"@UA@": UA, u"@UB@": UB, u"@UC@": UC, u"@UD@": UD,
        u"@D1@": D1, u"@D2@": D2, u"@BLNUM1@": B1, u"@BLNEW1@": B1,
        u"@BLADDED@": BL_ADDED, u"@BLADDED2@": BL_ADDED2,
        u"@BATT@": pre, u"@SKIP@": pre_skip, u"@STREAK@": STREAK_N, u"@PREVSTREAK@": PREV_STREAK,
        u"@CI@": CI, u"@HALINE@": HA_LINE, u"@ROT@": ROT_NOW, u"@OPAQUE@": OPAQUE_NOW,
        u"@TABLES@": TABLES_N, u"@COVERED@": COVERED, u"@PREBAD@": PRE_BAD,
        u"@ARMREG@": ARM_REG, u"@ARMFILES@": ARM_FILES,
        u"@WARN@": WARN, u"@FULL@": FULL, u"@CAPT@": CAPT, u"@BASE@": BASE, u"@RVLINE@": RVLINE,
        u"@KNIFELINE@": KNIFELINE, u"@KNIFEARMS@": KNIFEARMS, u"@HEADSHA@": head_sha,
        u"@GEOM@": GEOM, u"@GEOM_SHORT@": GEOM_SHORT, u"@PILL@": PILL, u"@PILL_EXEC@": PILL_EXEC,
        u"@PURE_EXEC@": PURE_EXEC, u"@MUST_INCLUDE@": MUST_INCLUDE,
        u"@REJ_H@": REJ_H, u"@REJ_HOLE@": REJ_HOLE, u"@ACC_HOLE@": ACC_HOLE,
        u"@RUN_AB_SUMMARY@": RUN_AB_SUMMARY, u"@RUN_AB_COUNTS@": RUN_AB_COUNTS,
        u"@RUN_MAG@": RUN_MAG, u"@RUN_MAG_SHORT@": RUN_MAG_SHORT, u"@RUN_SIDE@": RUN_SIDE,
        u"@RUN_RANGE@": RUN_RANGE, u"@RUN_SENS_N@": RUN_SENS_N, u"@RUN_GAP@": RUN_GAP,
        u"@LOC_MAG@": LOC_MAG, u"@LOC_MAG_SHORT@": LOC_MAG_SHORT, u"@LOC_RANGE@": LOC_RANGE,
        u"@LOC_SENS_N@": LOC_SENS_N, u"@LOC_AB_COUNTS@": LOC_AB_COUNTS}
EYE = fill(EYE, SUBS)
SUBS[u"@EYE@"] = EYE
SUBS[u"@EYE_SHORT@"] = EYE.split(u"⇒")[0].strip()

if not os.path.exists(BODIES):
    die(u"正文文件 %s 不在盘上" % BODIES)
ns = {}
exec(compile(rd(BODIES), BODIES, u"exec"), ns)
KEYS = (u"UI_NEW", u"IT_NEW", u"DEC_NEW", u"CH_NEW", u"ST_NEW", u"BL_NEW",
        u"BL_ADDED_384", u"BL_ADDED_387")
for k in KEYS:
    if k not in ns:
        die(u"正文缺 %s" % k)

orig = {k: rd(v) for k, v in FILES.items()}
for key, marker in ((u"UI", u"## 第 %d 轮" % ROUND), (u"IT", u"## Round %d ·" % RDN),
                    (u"ST", u"## %s 状态（" % R_TAG)):
    if marker in orig[key]:
        die(u"%s 里已经有本轮那一节 ⇒ 生成器不许重跑第二遍" % key)

texts = dict((k, fill(ns[k], SUBS)) for k in KEYS)
for k, t in texts.items():
    hit = STRAY_RX.findall(t)
    if hit:
        die(u"文本 %s 里还有没替换的占位符：%s" % (k, u",".join(sorted(set(hit)))))
# 证伪的那一半不许被写成"已完成"：正文里必须出现"撤回"与"未留档"
for label, body in ((u"UI_NEW", texts[u"UI_NEW"]), (u"ST_NEW", texts[u"ST_NEW"])):
    for token in (u"撤回", u"未留档"):
        if token not in body:
            die(u"%s 没出现「%s」⇒ 一次证伪被写成了普通改动" % (label, token))

heads = [(int(m.group(1)), m.start()) for m in re.finditer(u"(?m)^## 第 (\\d+) 轮", orig[u"UI"])]
top = max(heads)[1]
new_ui = orig[u"UI"][:top] + texts[u"UI_NEW"] + orig[u"UI"][top:]
if new_ui.count(u"## 第 %d 轮" % ROUND) != 1:
    die(u"UI_AUDIT 新节没落在最大轮次标题之上")
nums = [int(m.group(1)) for m in re.finditer(u"(?m)^- \\*\\*U-(\\d{3,4})[：(]", texts[u"UI_NEW"])]
if nums != [UA, UB, UC, UD]:
    die(u"新节的 U 定义行是 %s，要 %s" % (nums, [UA, UB, UC, UD]))
new_it = orig[u"IT"].rstrip(u"\n") + u"\n\n" + texts[u"IT_NEW"].rstrip(u"\n") + u"\n"
if len(re.findall(u"(?m)^\\| (真实视觉审查|判据有效性|假绿防御|产品面推进|台账一致性|交付诚实性|可复核性) \\| (\\d+)/15 \\|$",
                  texts[u"IT_NEW"])) != 7:
    die(u"七维表不是恰好 7 行")
dim_scores = [int(m) for m in re.findall(
    u"(?m)^\\| (?:真实视觉审查|判据有效性|假绿防御|产品面推进|台账一致性|交付诚实性|可复核性) \\| (\\d+)/15 \\|$",
    texts[u"IT_NEW"])]
stated_total = int(re.findall(u"合计 (\\d+)/105", texts[u"IT_NEW"])[0])
if stated_total != sum(dim_scores):
    die(u"七维表的合计 %d 与七格之和 %d 不等（混分母那一族，R152 / BACKLOG 190）"
        % (stated_total, sum(dim_scores)))
new_dec = orig[u"DEC"].rstrip(u"\n") + u"\n\n" + texts[u"DEC_NEW"].rstrip(u"\n") + u"\n"
d_hits = re.findall(u"(?m)^\\*\\*D-(\\d{3,4})（", texts[u"DEC_NEW"])
if [int(x) for x in d_hits] != [D1, D2]:
    die(u"新决定行是 %s，要 %s" % (d_hits, [D1, D2]))


def insert_addition(text, add_text, this_no, next_no):
    anchor = u"\n**%d. " % next_no
    pos = text.find(anchor)
    if pos < 0:
        die(u"找不到 %s 这一行的位置 ⇒ %d 的追记没有插入点" % (anchor.strip(), this_no))
    head = add_text.rstrip(u"\n").split(u"\n")[0]
    out = text[:pos] + add_text.rstrip(u"\n") + u"\n\n" + text[pos:]
    if out.count(head) != 1:
        die(u"%d 的追记标题命中 %d 次（要 1）⇒ 落点不唯一" % (this_no, out.count(head)))
    if not (out.index(u"**%d. " % this_no) < out.index(head) < pos + len(anchor)):
        die(u"%d 的追记落错了条目（不在 %d 与 %d 之间）" % (this_no, this_no, next_no))
    return out


def append_addition_to_tail_entry(text, add_text, this_no):
    """给账尾那一条追加追记（它后面没有下一个编号，`insert_addition` 那种锚点必然找不到）。"""
    pos = text.rfind(u"**%d. " % this_no)
    if pos < 0:
        die(u"账上找不到 %d 这一条 ⇒ 追记没有对象" % this_no)
    later = [int(m.group(1)) for m in re.finditer(u"(?m)^\\*\\*(\\d{3})\\. ", text) if m.start() > pos]
    if later:
        die(u"%d 后面还有条目 %s ⇒ 该用 insert_addition" % (this_no, later[:3]))
    head = add_text.rstrip(u"\n").split(u"\n")[0]
    out = text.rstrip(u"\n") + u"\n\n" + add_text.rstrip(u"\n") + u"\n"
    if out.count(head) != 1:
        die(u"%d 的追记标题命中 %d 次（要 1）⇒ 落点不唯一" % (this_no, out.count(head)))
    if not (out.rfind(u"**%d. " % this_no) < out.index(head)):
        die(u"%d 的追记落在了原条目之前" % this_no)
    return out


bl_with_add = insert_addition(orig[u"BL"], texts[u"BL_ADDED_384"], BL_ADDED, BL_ADDED + 1)
bl_with_add = append_addition_to_tail_entry(bl_with_add, texts[u"BL_ADDED_387"], BL_ADDED2)
new_bl = bl_with_add.rstrip(u"\n") + u"\n\n" + texts[u"BL_NEW"].rstrip(u"\n") + u"\n"
bl_nums = [int(m.group(1)) for m in re.finditer(u"(?m)^\\*\\*(\\d{3})\\. ", new_bl)]
if bl_nums[-NEW_ENTRIES:] != [B1]:
    die(u"新开的那单没落在尾部或编号不连续：%s" % bl_nums[-6:])
if len(set(bl_nums)) != len(bl_nums):
    die(u"BACKLOG 出现重号")
before = len(re.findall(u"(?m)^\\*\\*(\\d{3})\\. ", orig[u"BL"]))
after = len(re.findall(u"(?m)^\\*\\*(\\d{3})\\. ", new_bl))
if after != before + NEW_ENTRIES:
    die(u"BACKLOG 条目数从 %d 变成 %d（本轮说好新开 %d 单、两条追记不另开号）" % (before, after, NEW_ENTRIES))
new_ch = once(orig[u"CH"], u"## [Unreleased]\n\n", u"## [Unreleased]\n\n" + texts[u"CH_NEW"],
              u"CHANGELOG [Unreleased]")
if sum(1 for line in new_ch.split(u"\n") if line.strip() == u"## [Unreleased]") != 1:
    die(u"CHANGELOG 的 [Unreleased] 不再是恰好 1 行")
new_st = once(orig[u"ST"], u"## %s 状态（" % PREV_TAG,
              texts[u"ST_NEW"] + u"## %s 状态（" % PREV_TAG, u"STATE 轮换")
if u"## %s 状态（" % PREV_TAG not in new_st or u"## %s 状态（" % R_TAG not in new_st:
    die(u"STATE 轮换后上一轮的标记没了")
layers_before = len(re.findall(u"(?m)^## R\\d{3} 状态（", orig[u"ST"]))
layers_after = len(re.findall(u"(?m)^## R\\d{3} 状态（", new_st))
if layers_after != layers_before + 1:
    die(u"STATE 层数从 %d 变成 %d（要 +1）" % (layers_before, layers_after))
this_section = new_st.split(u"## %s 状态（" % R_TAG)[1].split(u"## %s 状态（" % PREV_TAG)[0]
if len(re.findall(u"(?m)^最后更新：%s（本地 · %s / 第 %d 轮 / Round %d）"
                  % (TODAY, R_TAG, ROUND, RDN), this_section)) != 1:
    die(u"本轮 STATE 节里没有那行 identity")
if len(re.findall(u"连续零改动 \\*\\*%s\\*\\* 轮|产品面连续零改动轮数 = \\*\\*%s\\*\\*"
                  % (STREAK_N, STREAK_N), this_section)) > 1:
    die(u"PRODUCT_STREAK_CELL_DUPES 那一格在本轮节里出现不止一次")

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
        sys.stderr.write(u"R327_CRASH_RESTORED 未捕获异常 ⇒ 七本已整体还原\n")


atexit.register(_crash_guard)

txt = rd(FILES[u"FR"])
out, crc = sh([sys.executable, CURVE])
rounds_after = (re.findall(r"^ROUNDS=(\d+)", out, re.M) or [u""])[-1]
last_round = (re.findall(r"^PHASE2 n=\d+ rounds=9\.\.(\d+)", out, re.M) or [u""])[-1]
tail = (re.findall(r"^SCORES_BY_ROUND (.+)$", out, re.M) or [u""])[-1]
if not rounds_after or not last_round or not tail:
    die(u"写盘后曲线尺没给全（rc=%d）：%s" % (crc, out.strip()[-300:]))
lines = txt.split(u"\n")
m2 = re.search(u"R9–R(\\d+)，(\\d+) 节自评", lines[0])
if not m2 or lines[0].count(u"R9–R") != 1:
    die(u"报告标题那一行没找到 `R9–R<NNN>，<NNN> 节自评`")
lines[0] = lines[0][:m2.start()] + u"R9–R%s，%s 节自评" % (last_round, rounds_after) + lines[0][m2.end():]
body = u"\n".join(lines)

prod_cell = (u"- **产品面（这一节最该被读的部分）**：本轮产品文件 0 个（**动效主线**：git 现读改动面 = %d 个文件，"
             u"产品 0 个、判据 2 个（`MotionFilmstripTests.swift` + `MotionPillRampTests.swift`）；五腿**全部适用且都跑了**：%s；全量卷 %s；"
             u"重捕 %s；基线 %s；四件套 %s。产品面连续零改动轮数 = **%s**"
             u"（唯一取数口 `python3 scripts/product_streak.py --streak-for %s`，`--check` 同形；上一轮那一格是 %s）。"
             u"本轮交的是**一次证伪**：384 登记的修法①（把字墨并回洞）落地两版轨道档估计，"
             u"被拒段都没过闸（留档那条读 洞宽=%d%%，通过段 %d%%）⇒ 字墨不是主因；"
             u"第二版还把带子从 14px 弄成「无」⇒ 改动全部撤回，盘上只留「候选段带洞宽」那一格，"
             u"它把 384 的下一步从「改定义」定成「先转储那一段的列电平」（新开 %d）。"
             u"刀：本轮 %s（逐臂 %s）。"
             % (len(touched), WARN, FULL, CAPT, BASE, RVLINE, STREAK_N, ROUND, PREV_STREAK,
                REJ_HOLE, ACC_HOLE, B1, KNIFELINE, KNIFEARMS))
scale_cell = (u"- **判据与门的规模**：脚本电池现读 **Ran %s**（写盘后同数），"
              u"变异臂在册 **%s** 把 / %s 张表（预检 tables=%s covered=%s bad=%s）；"
              u"腐烂针尺现读 `%s`；U 定义行 **%s 条**、最大 **U-%s**；决定台账最大 **D-%d**，"
              u"BACKLOG 最大 **%d**（本轮新开 %d 一单：被拒那 22px 里到底是什么；另追记 %d、%d）；"
              u"新读数族搬运名单 `READINGS_MUST_INCLUDE %s`"
              % (pre, ARM_REG, ARM_FILES, TABLES_N, COVERED, PRE_BAD, HA_LINE,
                 len(re.findall(u"(?m)^- \\*\\*U-(\\d{3,4})[：(]", new_ui)), UD, D2, B1, B1, BL_ADDED, BL_ADDED2,
                 MUST_INCLUDE))
where_cell = (u"- **走到哪了**：阶段二累计 `## Round` 节 **%s** 节，最新一节是 **Round %s**；"
              u"自评曲线按轮现读 %s（现读 `curve_from_ledger.py`）。派生分本轮仍不到收口线，"
              u"而产品面推进仍是绑住的那一维 ⇒ 按目标继续修，不收口。" % (rounds_after, last_round, tail))
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

post, post_skip = battery(u"写盘后", u"/tmp/r327_battery_post.log")
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
print(u"LEDGERS_R327 OK batt=Ran " + post + u" (skipped=" + post_skip + u") streak=" + STREAK_N
      + u"(上一轮 " + PREV_STREAK + u") 产品文件=" + s(len(product_touched))
      + u" 改动面=" + s(len(touched)) + u" 帧=" + s(CAPT_N) + u"/" + s(CM) + u" 基线changed=" + s(BC)
      + u" 刀=" + KNIFELINE
      + u" 被拒段=高%dpx 洞宽=%d%% 通过段洞宽=%d%% 取用=%s" % (REJ_H, REJ_HOLE, ACC_HOLE, TAKEN)
      + u" runner⓪=" + RUN_AB_COUNTS + u" / " + RUN_MAG_SHORT + u" 粒度不可比=" + s(RUN_GAP)
      + u" 出口=" + u",".join(NOT_RUN_PILL)
      + u" 本机对照=" + LOC_MAG_SHORT
      + u" 搬运=" + MUST_INCLUDE + u" 预检bad=" + s(PRE_BAD) + u" 在册=" + s(ARM_REG) + u"/" + s(ARM_FILES)
      + u"表 rot=" + s(ROT_NOW) + u" 抽不出=" + s(OPAQUE_NOW)
      + u" U=" + s(UA) + u".." + s(UD) + u" D=" + s(D1) + u"," + s(D2) + u" BL=" + s(B1)
      + u" derived(Round " + s(RDN) + u")=" + s(DERIVED2)
      + u" report尾轮=Round " + s(last_round) + u" 节数=" + s(rounds_after))
