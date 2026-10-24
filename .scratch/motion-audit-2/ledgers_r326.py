# -*- coding: utf-8 -*-
u"""R326 的七本台账（第 325 轮 / Round 323 · 动效主线：色档 A/B 换成三颗通道无关的尺）。

与 r325 的四处不同：
① 主菜是**一次公开更正**：@RPREVTAG@ 那份「12 颗都不必钉」用的峰值是采样通道的量
   （本机 敏感=0 对 runner 敏感=2，两台那一跑的胶片帧数同为 30）。本轮分类器改收三颗通道无关的量，
   所以正文里的分类计数必须来自**新口径那 12 行**，而峰值那一口要另存成 `_CHANNEL` 两行给对账；
② 同一批场景在**一次运行里有三份口径的数**（三颗 / 只面积两颗 / 只印不判的峰值），
   生成器逐条解析并要求三者各自的计数自闭合 —— 少解析一口，正文那句"三口径三份数"就没出处；
③ 「敏感>0 就必须钉」这条 @RPREVTAG@ 写的守卫**不许删**，本轮换成一条更宽的放行：
   只有当墨量那一格被证明是**单侧系统偏移**（亮臂更大 == 有变化，或反之）并且本轮为它开了单
   （正文里必须出现新条目号），才许写"本轮不钉"。否则照旧拒写、回去钉；
④ BACKLOG 本轮新开 1 单（@BLNEW1@）+ 两条追记（383 更正 / 386 换问句），
   所以插入点是两处、新条目一处。

跑法：PYTHONUTF8=1 python3 .scratch/motion-audit-2/ledgers_r326.py --eye "<看图腿正文>"
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
BODIES = os.path.join(ROOT, ".scratch", "motion-audit-2", "r326_bodies.txt")
RV = u"/tmp/r326_rv"
KNIFE_LOG = os.path.join(RV, u"mutate_r326.log")
PROBE_LOG = os.path.join(RV, u"film.log")
AREA_ONLY_LOG = os.path.join(RV, u"ab.log")
WITNESS_LOG = os.path.join(RV, u"pillramp.log")
RUNNER_LOG = os.path.join(RV, u"runner.log")
ROWS_LOG = u"/tmp/r326_rows.log"
FILM = u"ClipboardHistory/Tests/ClipboardHistoryAppTests/MotionFilmstripTests.swift"
WITNESS = u"ClipboardHistory/Tests/ClipboardHistoryAppTests/MotionPillRampTests.swift"
TODAY = u"2026-10-24"
R_TAG, PREV_TAG, R_NEXT = u"R326", u"R325", u"R327"
RTAGNUM = u"326"
PREV_ROUND, ROUND, RDN = 324, 325, 323
RUN_ID = u"40057803215"
RUN_SHA = u"929c084"
BL_MAX_PREV = 386           # 上一轮账上的最后一条
NEW_ENTRIES = 1
BL_ADDED = 383              # 本轮更正这一条（不另开号）
BL_ADDED2 = 386             # 386 续一条：换统计量之后"线在哪"前面还有"线画在哪颗尺上"
U_COUNT = 6
WROTE, OK_EXIT = [], []


def die(msg):
    sys.stderr.write(u"R326_LEDGERS_REFUSE %s\n" % msg)
    if WROTE:
        for key, text in orig.items():
            wr(FILES[key], text)
        sys.stderr.write(u"R326_RESTORED 七本已整体还原\n")
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


def last(text, pattern, label, strip_step=False):
    hits = re.findall(pattern, text)
    if not hits:
        die(u"读不到 %s（正则 %s）" % (label, pattern[:60]))
    line = hits[-1]
    return strip_step(line) if strip_step else line


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
ap = argparse.ArgumentParser(prog="ledgers_r326.py", description=u"R326 的七本台账（色档 A/B 换统计量）")
ap.add_argument(u"--eye", default=os.environ.get(u"R326_EYE", u""),
                help=u"看图腿正文（也可用环境变量 R326_EYE 传）")
ARGS = ap.parse_args()
EYE = ARGS.eye.strip()
if not EYE:
    die(u"看图腿没传 R326_EYE / --eye ⇒ 真实视觉审查不许省略，也不许凭记忆写")

pre, pre_skip = battery(u"写盘前", u"/tmp/r326_battery_pre.log")

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
FAIL_N = int(re.findall(r"and (\d+) failures?", FULL)[-1])
EXEC_N = int(re.findall(r"Executed (\d+) tests?", FULL)[-1])
red_names = sorted({m.group(1) for m in re.finditer(r"Test Case '-\[[^\]]+ (\w+)\]' failed", full)})
if FAIL_N != 0:
    die(u"全量卷有红（failures=%d，名单=%s）⇒ 先归因再落账" % (FAIL_N, u", ".join(red_names) or u"读不到"))
witness_log = log_read(WITNESS_LOG, u"判据卷 MotionPillRampTests")
w_rows = re.findall(r"Executed (\d+) tests?(?:, with (?:\d+ tests? skipped and )?(\d+) failures)?", witness_log)
w_rows = [(a, b) for a, b in w_rows if b is not None]
if not w_rows:
    die(u"判据卷读不到汇总行（这台机器 0 skip 时那一行是「Executed 27 tests, with 0 failures」，"
        u"没有 skipped 那一段 —— 正则不许把它写成必填）")
WEXEC = max(int(x[0]) for x in w_rows)
WFIX = max(int(x[1]) for x in w_rows)
if WFIX:
    die(u"判据卷有红（failures=%d）⇒ 先归因再落账" % WFIX)

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

# —— 本轮的主菜：三颗口径的逐颗读数 + 两份汇总 + 墨量那一格 ——
probe = log_read(PROBE_LOG, u"胶片卷（含色档 A/B 探针）")
AB_RX = (r"(?m)^MOTION_SCENARIO_AB (\S+) 判定=(\S+) 首末暗=([\d.]+) 首末亮=([\d.]+) "
         r"并集暗=([\d.]+) 并集亮=([\d.]+) 墨暗=([\d.]+) 墨亮=([\d.]+) "
         r"暗换档=(是|否) 亮换档=(是|否)$")
ab = re.findall(AB_RX, probe)
if len(ab) != 12:
    die(u"色档 A/B（新口径）只读到 %d 行（要 12 行：对象表与点名器对账的那 12 颗）" % len(ab))
SUMMARY = last(probe, r"(?m)^MOTION_SCENARIO_AB_SUMMARY .+$", u"_SUMMARY")
sm = re.search(r"场景=(\d+) 同=(\d+) 漂=(\d+) 敏感=(\d+) 换对象=(\d+) 粒度不可比=(\d+)", SUMMARY)
if not sm:
    die(u"汇总行形状变了（要带 粒度不可比=）：%s" % SUMMARY[:200])
n_total, n_same, n_drift, n_sens, n_flip, n_gap = (int(x) for x in sm.groups())
by_word = {}
for row in ab:
    by_word.setdefault(row[1], []).append(row[0])
if (n_total, n_same, n_drift, n_sens, n_flip) != (
        12, len(by_word.get(u"同", [])), len(by_word.get(u"漂", [])),
        len(by_word.get(u"敏感", [])), len(by_word.get(u"换对象", []))):
    die(u"汇总行与逐行不闭合：汇总=%s 逐行=%s" % (sm.groups(), sorted(by_word.items())))
CH_SUMMARY = last(probe, r"(?m)^MOTION_SCENARIO_AB_SUMMARY_CHANNEL .+$", u"_SUMMARY_CHANNEL")
chm = re.search(r"峰值口径 同=(\d+) 漂=(\d+) 敏感=(\d+) 换对象=(\d+) 与通道无关口径判定不同=(\d+)", CH_SUMMARY)
if not chm:
    die(u"_SUMMARY_CHANNEL 形状变了：%s" % CH_SUMMARY[:200])
c_same, c_drift, c_sens, c_flip, c_mismatch = (int(x) for x in chm.groups())
if c_same + c_drift + c_sens + c_flip != 12 or (c_same + c_drift + c_sens + c_flip) != n_total:
    die(u"峰值口径的计数不闭合（%s）⇒ 那一口也是 12 颗，正文那句'三口径三份数'就没出处" % chm.groups())
ab_ch = re.findall(r"(?m)^MOTION_SCENARIO_AB_CHANNEL (\S+) 峰值口径判定=(\S+) 峰值暗=([\d.]+) "
                   r"峰值亮=([\d.]+) 峰值相对差=([\d.]+)% 帧数=(\d+)$", probe)
if len(ab_ch) != 12:
    die(u"峰值口径逐颗行只读到 %d 行（要 12）" % len(ab_ch))
by_ch_word = {}
for row in ab_ch:
    by_ch_word.setdefault(row[1], []).append(row[0])
# 本机这一跑的两臂帧数（正文那句"帧数本身随跑动"的出处，不许手抄）
LOCAL_FRAMES = u"/".join(sorted({str(int(r[5])) for r in ab_ch}))
if c_same != len(by_ch_word.get(u"同", [])) or c_sens != len(by_ch_word.get(u"敏感", [])) \
        or c_drift != len(by_ch_word.get(u"漂", [])) or c_flip != len(by_ch_word.get(u"换对象", [])):
    die(u"峰值口径的汇总与逐行不闭合：汇总=%s 逐行=%s"
        % (chm.groups(), {k: len(v) for k, v in by_ch_word.items()}))
# 判定不同的那一格必须是"逐颗数出来的"，不是汇总行自己说的
counted_mismatch = len([name for name, word, _a, _b, _c, _d, _e, _f, _g, _h in ab
                        if word != dict((r[0], r[1]) for r in ab_ch).get(name, u"?)")])
if counted_mismatch != c_mismatch:
    die(u"逐颗对出来的判定不同=%d 与汇总行 %d 不同 ⇒ 那一格是手抄的（R106 一族）"
        % (counted_mismatch, c_mismatch))

MAG = last(probe, r"(?m)^MOTION_SCENARIO_AB_MAGNITUDE .+$", u"_MAGNITUDE")
mg = re.search(r"有变化=(\d+) 亮臂更大=(\d+) 暗臂更大=(\d+) 比值暗除亮=(\S+)（", MAG)
if not mg:
    die(u"_MAGNITUDE 形状变了：%s" % MAG[:200])
mag_n, mag_light, mag_dark, mag_range = mg.group(1), int(mg.group(2)), int(mg.group(3)), mg.group(4)
if mag_light + mag_dark > int(mag_n):
    die(u"墨量方向那一格自相矛盾：有变化=%s 而 亮大=%d 暗大=%d" % (mag_n, mag_light, mag_dark))
one_sided = (mag_light == int(mag_n) and mag_light > 1) or (mag_dark == int(mag_n) and mag_dark > 1)

CENSUS = last(probe, r"(?m)^MOTION_SCENARIO_APPEAR .+$", u"MOTION_SCENARIO_APPEAR")
exec_hits = re.findall(r"Executed (\d+) tests?, with (?:(\d+) tests? skipped and )?(\d+) failures?", probe)
if not exec_hits:
    die(u"胶片卷读不到汇总行")
big = max(exec_hits, key=lambda t: int(t[0]))
if big[2] != u"0":
    die(u"胶片卷自己不是全绿（Executed=%s fail=%s）⇒ 先归因再落账" % big)
PROBE_EXEC = u"Executed %s tests, with %s tests skipped and %s failures（开 CLIPBOARD_HISTORY_UI_MOTION 跑 testFilmScenario 那两格）" \
    % (big[0], big[1] or u"0", big[2])

# —— 只留面积两颗的那一遍（本轮的"少第三颗会得到什么"，必须有出处）——
area_only = log_read(AREA_ONLY_LOG, u"面积两颗那一遍")
AREA_ONLY_SUMMARY = last(area_only, r"(?m)^MOTION_SCENARIO_AB_SUMMARY .+$", u"面积两颗的汇总行")
ao = re.search(r"场景=(\d+) 同=(\d+) 漂=(\d+) 敏感=(\d+) 换对象=(\d+)", AREA_ONLY_SUMMARY)
if not ao:
    die(u"面积两颗那遍的汇总行形状变了：%s" % AREA_ONLY_SUMMARY[:200])
if ao.group(1) != sm.group(1):
    die(u"两遍的场景数不同（%s 对 %s）⇒ 对象表变了，两遍不可比" % (ao.group(1), sm.group(1)))
AREA_ONLY_SAME = ao.group(2)
AREA_ONLY_SHORT = u"同=%s 漂=%s 敏感=%s 换对象=%s" % (ao.group(2), ao.group(3), ao.group(4), ao.group(5))
if int(ao.group(4)) == n_sens and int(ao.group(2)) == n_same:
    die(u"面积两颗与三颗口径读出**同一份**分类 ⇒ 第三颗墨量尺没有改变任何东西，"
        u"那正文那句'少它就全读成同'是编的（现读 两颗=%s 三颗=%s）" % (AREA_ONLY_SHORT, SUMMARY[:120]))

AB_SUMMARY_SHORT = u"场景=%d 同=%d 漂=%d 敏感=%d 换对象=%d 粒度不可比=%d（三颗口径）" % (
    n_total, n_same, n_drift, n_sens, n_flip, n_gap)
AB_COUNTS = u"同=%d 漂=%d 敏感=%d 换对象=%d" % (n_same, n_drift, n_sens, n_flip)
AB_COUNTS_SHORT = u"同=%d 漂=%d 敏感=%d 换对象=%d 粒度不可比=%d" % (n_same, n_drift, n_sens, n_flip, n_gap)
CH_COUNTS_SHORT = u"同=%d 漂=%d 敏感=%d 换对象=%d 判定不同=%d" % (c_same, c_drift, c_sens, c_flip, c_mismatch)
MAG_SHORT = u"有变化=%s 亮臂更大=%d 暗臂更大=%d 比值暗除亮=%s" % (mag_n, mag_light, mag_dark, mag_range)
SENS_LIST = u"、".join(by_word.get(u"敏感", [])) or u"无"
DRIFT_LIST = u"、".join(by_word.get(u"漂", [])) or u"无"
SAME_LIST = u"、".join(by_word.get(u"同", [])) or u"无"

# —— 那条守卫不许删：换对象>0 一律拒写；敏感>0 只在"偏移未标定且已开单"时放行 ——
if n_flip:
    die(u"分类里出现了 换对象=%d ⇒ 那几颗**必须钉色档**（那是前提翻脸，与阈值无关），"
        u"先回去把该钉的钉上再重测（名单=%s）" % (n_flip, u",".join(by_word.get(u"换对象", []))))
if n_sens and not one_sided:
    die(u"敏感=%d 而墨量方向**不是**单侧（有变化=%s 亮大=%d 暗大=%d）⇒ 那条系统偏移的解释不成立，"
        u"这 %d 颗现在就得钉，正文那句'本轮不钉'当场作废" % (n_sens, mag_n, mag_light, mag_dark, n_sens))

# —— 两台的矛盾（U-@UA@ 的原始形状）：runner 那两行必须还能读出来 ——
runner_txt = log_read(RUNNER_LOG, u"runner 读数（R325 那一跑）")
RUN_AB_SUMMARY = strip_step(last(runner_txt, r"(?m)^.*MOTION_SCENARIO_AB_SUMMARY .+$", u"runner 的 _SUMMARY"))
run_ab = re.findall(r"(?m)^.*MOTION_SCENARIO_AB (\S+) 暗峰值=([\d.]+) 亮峰值=([\d.]+) "
                    r"相对差=([\d.]+)% 暗换档=(是|否) 亮换档=(是|否) 判定=(\S+)$", runner_txt)
if len(run_ab) != 12:
    die(u"runner 的旧口径逐颗行只读到 %d 行（要 12 行）⇒ U-@UA@ 那句'两台读成相反动作'没出处" % len(run_ab))
run_by_name = dict((r[0], r) for r in run_ab)
local_ch = dict((r[0], r) for r in ab_ch)
CONTRA = []
for name in (u"noticeBanner", u"noticeBannerDismiss"):
    if name not in run_by_name or name not in local_ch:
        die(u"两台的对照缺 %s（runner=%s 本机=%s）" % (name, sorted(run_by_name)[:3], sorted(local_ch)[:3]))
    CONTRA.append(u"%s：runner 暗峰值=%s 亮峰值=%s 判%s，本机同颗 暗峰值=%s 亮峰值=%s 判%s"
                  % (name, run_by_name[name][1], run_by_name[name][2], run_by_name[name][6],
                     local_ch[name][2], local_ch[name][3], local_ch[name][1]))
run_words = {}
for r in run_ab:
    run_words.setdefault(r[6], []).append(r[0])
run_sens = sorted(run_words.get(u"敏感", []) + run_words.get(u"换对象", []))
if not run_sens:
    die(u"runner 那份旧分类里没有 敏感/换对象（读到 %s）⇒ 本轮 ⓪ 那句'两台动作相反'没有出处" % sorted(run_words))
if [int(x) for x in re.search(r"场景=(\d+) 同=(\d+) 漂=(\d+) 敏感=(\d+) 换对象=(\d+)", RUN_AB_SUMMARY).groups()] \
        != [12, len(run_words.get(u"同", [])), len(run_words.get(u"漂", [])),
            len(run_words.get(u"敏感", [])), len(run_words.get(u"换对象", []))]:
    die(u"runner 的汇总行与逐行不闭合 ⇒ 那份'另一台机器的分类'不可信，别拿它当对照")
RUN_SENS = u",".join(run_sens)
# runner 那一跑的胶片帧数（同一颗探针的 MOTION_GRAB 行）：正文那句"两台帧数相同"的出处
_run_frames = sorted({int(m.group(1)) for m in re.finditer(r"MOTION_GRAB \S+ 帧数=(\d+)", runner_txt)})
if not _run_frames:
    die(u"runner 日志里没有 MOTION_GRAB 帧数行 ⇒ 「两台的帧数相同」这句只能记 NOT-RUN，不许写进正文")
RUN_FRAMES = u"/".join(str(x) for x in _run_frames)
RUN_PILL_GEOM = strip_step(last(runner_txt, r"(?m)^.*MOTION_PILL_RAMP_GEOM .+$", u"runner 的 _RAMP_GEOM"))
gm = re.search(r"行带=([\d.]+…[\d.]+)pt .*?色档=(\S+)", RUN_PILL_GEOM)
if not gm:
    die(u"runner 的 GEOM 行解析不出来：%s" % RUN_PILL_GEOM[:200])
RUN_BAND_PT, RUN_APPEAR = gm.groups()
if u"胶片暗" not in RUN_APPEAR:
    die(u"runner 的 GEOM 没有 色档=胶片暗 ⇒ R324 钉的那一档在第二台机器上没生效：%s" % RUN_PILL_GEOM[:180])
NOT_RUN_PILL = re.findall(r"(?m)^.*MOTION_NOT_RUN=(pill-[\w-]+) ", runner_txt)
if u"pill-slide-arms-indistinguishable" not in NOT_RUN_PILL \
        or u"pill-ramp-no-intermediate" not in NOT_RUN_PILL:
    die(u"runner 的两朵命名出口没同时露面（读到 %s）⇒ ①那条兑现不能写" % NOT_RUN_PILL)
if re.search(r"(?m)^.*MOTION_FLOOR_SUITE_CLEAN=(\d+)", runner_txt) is None:
    die(u"runner 读不到 MOTION_FLOOR_SUITE_CLEAN ⇒ §8 归零那一格没出处")
FLOOR_CLEAN = re.findall(r"(?m)^.*MOTION_FLOOR_SUITE_CLEAN=(\d+)", runner_txt)[-1]
if FLOOR_CLEAN != u"0":
    die(u"runner 的 suite-clean 不是 0（读到 %s）⇒ 先读名单再落账" % FLOOR_CLEAN)
RUN_ASSERTION_RED = len(re.findall(r"(?m)^ASSERTION_RED\t.*$", runner_txt))
if RUN_ASSERTION_RED:
    die(u"runner 有 %d 行断言红 ⇒ 本轮 ⓪ 那句'红修完了'不能写" % RUN_ASSERTION_RED)
RUN_GEOM_SHORT = u"行带=%spt、色档=%s" % (RUN_BAND_PT, RUN_APPEAR)
RUN_AB_SUMMARY_SHORT = u"场景=12 同=%d 漂=%d 敏感=%d 换对象=%d（峰值口径）" % (
    len(run_words.get(u"同", [])), len(run_words.get(u"漂", [])),
    len(run_words.get(u"敏感", [])), len(run_words.get(u"换对象", [])))

PURE_EXEC = (u"%d 格全绿（本轮新增 4 格：采样粒度、面积盲区、并集分母同一性、粒度容差；"
             u"分类器那格从 6 条加到 7 条）" % WEXEC)
if WEXEC <= 23:
    die(u"判据卷还是 %d 格 ⇒ 本轮那 4 格新证人没进卷" % WEXEC)

# —— 刀：一支表 ——
KNIFELINE, KNIFEARMS = knife_summary(KNIFE_LOG, u"本轮变异表（M943…M948）", 6)

pc, _rc = sh([sys.executable, PRECHECK])
pre_line = re.findall(r"NEEDLE_PRECHECK tables=(\d+) covered=(\d+) arms=(\d+) bad=(\d+)", pc)
if not pre_line:
    die(u"NEEDLE_PRECHECK 没读到")
TABLES_N, COVERED, _PA, PRE_BAD = (int(x) for x in pre_line[-1])
if PRE_BAD:
    die(u"针预检 bad=%d ⇒ 有 needle 在册上腐烂（本轮抽公共函数会顶到 @RPREVTAG@ 的 M938/M940，"
        u"要重钉那两根针而不是放宽查重）")
if u"mutate_r326" not in pc:
    die(u"mutate_r326 不在预检名册里（新表出厂第一天就要在册）")
reg_line = re.findall(r"ARM_TOTAL files=(\d+) arms=(\d+) dupes=(\d+) repeats=(\d+)", pc)
if not reg_line:
    die(u"ARM_TOTAL 没读到")
ARM_FILES, ARM_REG, ARM_DUPES, ARM_REPEATS = (int(x) for x in reg_line[-1])
if ARM_DUPES or ARM_REPEATS:
    die(u"名册报 dupes=%d repeats=%d" % (ARM_DUPES, ARM_REPEATS))

# —— 新读数族必须真的进了搬运名单（R107 / U-339 那一族）——
FAMILIES = [u"MOTION_SCENARIO_AB", u"MOTION_SCENARIO_AB_CHANNEL", u"MOTION_SCENARIO_AB_MAGNITUDE",
            u"MOTION_SCENARIO_AB_SUMMARY", u"MOTION_SCENARIO_AB_SUMMARY_CHANNEL",
            u"MOTION_SCENARIO_APPEAR"]
rm2, rmc = sh([sys.executable, ROWS, PROBE_LOG] + [u"--must-include"] + FAMILIES)
io.open(ROWS_LOG, u"w", encoding="utf-8").write(rm2)
must = re.findall(r"READINGS_MUST_INCLUDE 声明=(\d+) 缺=(\d+)", rm2)
if not must:
    die(u"搬运名单那把尺没打结论行（rc=%d）" % rmc)
MUST_DECL, MUST_MISS = (int(x) for x in must[-1])
if MUST_MISS or MUST_DECL != len(FAMILIES):
    die(u"本轮的新读数族没被搬走（声明=%d 缺=%d）⇒ 先回 ledger_rows.py 补名单" % (MUST_DECL, MUST_MISS))
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
if int(STREAK_N) < 1:
    die(u"本轮没动产品，连续零改动轮数却读到 %s ⇒ 取数口与改动面矛盾，先查哪一个错" % STREAK_N)
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
UE, UF = U_MAX + 5, U_MAX + 6
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
        u"@UA@": UA, u"@UB@": UB, u"@UC@": UC, u"@UD@": UD, u"@UE@": UE,
        u"@D1@": D1, u"@D2@": D2, u"@BLNUM1@": B1, u"@BLNEW1@": B1, u"@BLADDED@": BL_ADDED,
        u"@BLADDED2@": BL_ADDED2,
        u"@BATT@": pre, u"@SKIP@": pre_skip, u"@STREAK@": STREAK_N, u"@PREVSTREAK@": PREV_STREAK,
        u"@CI@": CI, u"@HALINE@": HA_LINE, u"@ROT@": ROT_NOW, u"@OPAQUE@": OPAQUE_NOW,
        u"@TABLES@": TABLES_N, u"@COVERED@": COVERED, u"@PREBAD@": PRE_BAD,
        u"@ARMREG@": ARM_REG, u"@ARMFILES@": ARM_FILES,
        u"@WARN@": WARN, u"@FULL@": FULL, u"@EXEC@": EXEC_N, u"@CAPT@": CAPT, u"@BASE@": BASE,
        u"@RVLINE@": RVLINE, u"@KNIFELINE@": KNIFELINE, u"@KNIFEARMS@": KNIFEARMS,
        u"@AB_SUMMARY@": SUMMARY, u"@CH_SUMMARY@": CH_SUMMARY,
        u"@AB_SUMMARY_SHORT@": AB_SUMMARY_SHORT,
        u"@CENSUS@": CENSUS, u"@PROBE_EXEC@": PROBE_EXEC,
        u"@MUST_INCLUDE@": MUST_INCLUDE, u"@HEADSHA@": head_sha,
        u"@AB_COUNTS@": AB_COUNTS, u"@AB_COUNTS_SHORT@": AB_COUNTS_SHORT,
        u"@CH_COUNTS_SHORT@": CH_COUNTS_SHORT, u"@MAG_SHORT@": MAG_SHORT, u"@MAG@": MAG,
        u"@AREA_ONLY_SUMMARY@": AREA_ONLY_SUMMARY, u"@AREA_ONLY_SHORT@": AREA_ONLY_SHORT,
        u"@AREA_ONLY_SAME@": AREA_ONLY_SAME,
        u"@AB_SENS_LIST@": SENS_LIST, u"@AB_DRIFT_LIST@": DRIFT_LIST, u"@AB_SAME_LIST@": SAME_LIST,
        u"@SAME_N@": n_same, u"@DRIFT_N@": n_drift, u"@SENS_N@": n_sens, u"@GAP_N@": n_gap,
        u"@MAG_N@": mag_n, u"@MAG_SIDE@": mag_light, u"@MAG_RANGE@": mag_range,
        u"@CH_MISMATCH@": c_mismatch,
        u"@RUN_SENS@": RUN_SENS, u"@RUN_AB_SUMMARY@": RUN_AB_SUMMARY_SHORT,
        u"@RUN_GEOM_SHORT@": RUN_GEOM_SHORT, u"@CONTRA@": u"；".join(CONTRA),
        u"@LOCALFRAMES@": LOCAL_FRAMES, u"@RUNFRAMES@": RUN_FRAMES,
        u"@UF@": UF, u"@PURE_EXEC@": PURE_EXEC}
EYE = fill(EYE, SUBS)
SUBS[u"@EYE@"] = EYE
SUBS[u"@EYE_SHORT@"] = EYE.split(u"⇒")[0].strip()

if n_sens:
    SUBS[u"@SENS_CLAUSE@"] = (u"本轮**不据 敏感=%d 去钉**：墨量那颗尺带色档级系统偏移"
                              u"（%s，%d/%s 全在亮臂一侧），阈值在它身上没有出处 ⇒ 新开 %d"
                              % (n_sens, MAG_SHORT, mag_light, mag_n, B1))
else:
    SUBS[u"@SENS_CLAUSE@"] = u"敏感=0 ⇒ 没有一颗需要按这条规则钉"

if not os.path.exists(BODIES):
    die(u"正文文件 %s 不在盘上" % BODIES)
ns = {}
exec(compile(rd(BODIES), BODIES, u"exec"), ns)
for k in (u"UI_NEW", u"IT_NEW", u"DEC_NEW", u"CH_NEW", u"ST_NEW", u"BL_NEW",
          u"BL_ADDED_383", u"BL_ADDED_386"):
    if k not in ns:
        die(u"正文缺 %s" % k)

orig = {k: rd(v) for k, v in FILES.items()}
for key, marker in ((u"UI", u"## 第 %d 轮" % ROUND), (u"IT", u"## Round %d ·" % RDN),
                    (u"ST", u"## %s 状态（" % R_TAG)):
    if marker in orig[key]:
        die(u"%s 里已经有本轮那一节 ⇒ 生成器不许重跑第二遍" % key)

texts = dict((k, fill(ns[k], SUBS)) for k in
             (u"UI_NEW", u"IT_NEW", u"DEC_NEW", u"CH_NEW", u"ST_NEW", u"BL_NEW",
              u"BL_ADDED_383", u"BL_ADDED_386"))
for k, t in texts.items():
    hit = STRAY_RX.findall(t)
    if hit:
        die(u"文本 %s 里还有没替换的占位符：%s" % (k, u",".join(sorted(set(hit)))))

# 「不钉」这句话必须有对象：正文里要出现新条目号，而且出现敏感名单本身
if n_sens:
    for label, body in ((u"UI_NEW", texts[u"UI_NEW"]), (u"ST_NEW", texts[u"ST_NEW"])):
        if s(B1) not in body:
            die(u"%s 写着不钉 %d 颗却没引用新开的那单 %d ⇒ 动作没登记就成了结论" % (label, n_sens, B1))
    for name in by_word.get(u"敏感", []):
        if name not in texts[u"UI_NEW"] and name not in texts[u"BL_NEW"]:
            die(u"敏感名单里的 %s 在正文里一次都没出现 ⇒ 读者查不到它" % name)

heads = [(int(m.group(1)), m.start()) for m in re.finditer(u"(?m)^## 第 (\\d+) 轮", orig[u"UI"])]
top = max(heads)[1]
new_ui = orig[u"UI"][:top] + texts[u"UI_NEW"] + orig[u"UI"][top:]
if new_ui.count(u"## 第 %d 轮" % ROUND) != 1:
    die(u"UI_AUDIT 新节没落在最大轮次标题之上")
nums = [int(m.group(1)) for m in re.finditer(u"(?m)^- \\*\\*U-(\\d{3,4})[：(]", texts[u"UI_NEW"])]
if nums != [UA, UB, UC, UD, UE, UF]:
    die(u"新节的 U 定义行是 %s，要 %s" % (nums, [UA, UB, UC, UD, UE, UF]))
new_it = orig[u"IT"].rstrip(u"\n") + u"\n\n" + texts[u"IT_NEW"].rstrip(u"\n") + u"\n"
if len(re.findall(u"(?m)^\\| (真实视觉审查|判据有效性|假绿防御|产品面推进|台账一致性|交付诚实性|可复核性) \\| (\\d+)/15 \\|$",
                  texts[u"IT_NEW"])) != 7:
    die(u"七维表不是恰好 7 行")
new_dec = orig[u"DEC"].rstrip(u"\n") + u"\n\n" + texts[u"DEC_NEW"].rstrip(u"\n") + u"\n"
d_hits = re.findall(u"(?m)^\\*\\*D-(\\d{3,4})（", texts[u"DEC_NEW"])
if [int(x) for x in d_hits] != [D1, D2]:
    die(u"新决定行是 %s，要 %s" % (d_hits, [D1, D2]))


def insert_addition(text, add_text, this_no, next_no):
    """把一条追记插在 `**<this>. ` 与 `**<next>. ` 之间，并用**行位置**自证落对了条目。"""
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
    """给**账尾那一条**追加追记 —— 它后面没有下一个编号，`insert_addition` 那种
    "找 `**<next>. `" 的锚点在这里必然找不到（本轮的 386 就是这一形状）。
    所以改用另一组断言：这一条必须是文件里最后一条，追记必须落在它之后、新单之前。"""
    pos = text.rfind(u"**%d. " % this_no)
    if pos < 0:
        die(u"账上找不到 %d 这一条 ⇒ 追记没有对象" % this_no)
    later = [int(m.group(1)) for m in re.finditer(u"(?m)^\\*\\*(\\d{3})\\. ", text)
             if m.start() > pos]
    if later:
        die(u"%d 后面还有条目 %s ⇒ 该用 insert_addition 而不是尾部追加" % (this_no, later[:3]))
    head = add_text.rstrip(u"\n").split(u"\n")[0]
    out = text.rstrip(u"\n") + u"\n\n" + add_text.rstrip(u"\n") + u"\n"
    if out.count(head) != 1:
        die(u"%d 的追记标题命中 %d 次（要 1）⇒ 落点不唯一" % (this_no, out.count(head)))
    if not (out.rfind(u"**%d. " % this_no) < out.index(head)):
        die(u"%d 的追记落在了原条目之前 ⇒ 读者会以为它是另一条" % this_no)
    return out


bl_with_add = insert_addition(orig[u"BL"], texts[u"BL_ADDED_383"], BL_ADDED, BL_ADDED + 1)
bl_with_add = append_addition_to_tail_entry(bl_with_add, texts[u"BL_ADDED_386"], BL_ADDED2)
new_bl = bl_with_add.rstrip(u"\n") + u"\n\n" + texts[u"BL_NEW"].rstrip(u"\n") + u"\n"
bl_nums = [int(m.group(1)) for m in re.finditer(u"(?m)^\\*\\*(\\d{3})\\. ", new_bl)]
if bl_nums[-NEW_ENTRIES:] != [B1]:
    die(u"新开的那单没落在尾部或编号不连续：%s" % bl_nums[-6:])
if len(set(bl_nums)) != len(bl_nums):
    die(u"BACKLOG 出现重号（同号两份正文 = 读者不知道哪份作数）")
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
# 本轮那一节必须自带 identity 行（R323 缺它把 R324 顶成了 COMMIT_SUBJECT_ROUND_OFF）
this_section = new_st.split(u"## %s 状态（" % R_TAG)[1].split(u"## %s 状态（" % PREV_TAG)[0]
if len(re.findall(u"(?m)^最后更新：%s（本地 · %s / 第 %d 轮 / Round %d）"
                  % (TODAY, R_TAG, ROUND, RDN), this_section)) != 1:
    die(u"本轮 STATE 节里没有那行 identity（R323 那一课：缺它 = 上一轮的提交信息被顶成越界）")
if len(re.findall(u"连续零改动 \\*\\*%s\\*\\* 轮|产品面连续零改动轮数 = \\*\\*%s\\*\\*"
                  % (STREAK_N, STREAK_N), this_section)) > 1:
    die(u"PRODUCT_STREAK_CELL_DUPES 那一格在本轮节里出现不止一次")

fr = orig[u"FR"]
if len(re.findall(u"U-31 … U-\\d+（R\\d+ 现读抬到最新一节）", fr)) != 1:
    die(u"§1 的 U 那一格锚点命中不是 1")
fr = re.sub(u"U-31 … U-\\d+（R\\d+ 现读抬到最新一节）",
            u"U-31 … U-%d（%s 现读抬到最新一节）" % (UF, R_TAG), fr, count=1)
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
        sys.stderr.write(u"R326_CRASH_RESTORED 未捕获异常 ⇒ 七本已整体还原\n")


atexit.register(_crash_guard)

txt = rd(FILES[u"FR"])
out, crc = sh([sys.executable, CURVE])
rounds_after = (re.findall(r"^ROUNDS=(\d+)", out, re.M) or [u""])[-1]
last_round = (re.findall(r"^PHASE2 n=\d+ rounds=9\.\.(\d+)", out, re.M) or [u""])[-1]
tail = (re.findall(r"^SCORES_BY_ROUND (.+)$", out, re.M) or [u""])[-1]
if not rounds_after or not last_round or not tail:
    die(u"写盘后曲线尺没给全（rc=%d）：%s" % (crc, out.strip()[-400:] or u"（没打印任何行）"))
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
             u"本轮交的是**上一轮那份结论的账**：@RPREVTAG@ 用逐帧峰值判「这条判据的读数随不随色档走」，"
             u"而峰值是采样通道的量 —— 同一笔 commit 本机读 敏感=0、runner 读 敏感=2（两台那一跑的胶片帧数同为 30），"
             u"那句「12 颗都不必钉」是拿一把读错对象的尺量的。现在分类器收三颗通道无关的量"
             u"（首末面积 / 动过的并集 / 首末墨量差，取较大者），峰值降为只印不判；"
             u"本机现读 @AB_COUNTS_SHORT@，只留面积两颗是 @AREA_ONLY_SHORT@，"
             u"墨量那颗带系统偏移（@MAG_SHORT@）⇒ @SENS_CLAUSE@。"
             u"刀：本轮 %s（逐臂 %s）。"
             % (len(touched), WARN, FULL, CAPT, BASE, RVLINE, STREAK_N, ROUND, PREV_STREAK,
                KNIFELINE, KNIFEARMS))
scale_cell = (u"- **判据与门的规模**：脚本电池现读 **Ran %s**（写盘后同数），"
              u"变异臂在册 **%s** 把 / %s 张表（预检 tables=%s covered=%s bad=%s）；"
              u"腐烂针尺现读 `%s`；U 定义行 **%s 条**、最大 **U-%s**；决定台账最大 **D-%d**，"
              u"BACKLOG 最大 **%d**（本轮新开 %d 一单：通道无关尺上的两条分界没有出处；另追记 %d、%d）；"
              u"新读数族搬运名单 `READINGS_MUST_INCLUDE %s`"
              % (pre, ARM_REG, ARM_FILES, TABLES_N, COVERED, PRE_BAD, HA_LINE,
                 len(re.findall(u"(?m)^- \\*\\*U-(\\d{3,4})[：(]", new_ui)), UF, D2, B1, B1, BL_ADDED, BL_ADDED2,
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

post, post_skip = battery(u"写盘后", u"/tmp/r326_battery_post.log")
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
if u"U-31 … U-%d" % UF not in rd(FILES[u"FR"]):
    die(u"报告 §1 的 U 上界不是本轮的 U-%d" % UF)

OK_EXIT.append(True)
print(u"LEDGERS_R326 OK batt=Ran " + post + u" (skipped=" + post_skip + u") streak=" + STREAK_N
      + u"(上一轮 " + PREV_STREAK + u") 产品文件=" + s(len(product_touched))
      + u" 改动面=" + s(len(touched)) + u" 帧=" + s(CAPT_N) + u"/" + s(CM) + u" 基线changed=" + s(BC)
      + u" 刀=" + KNIFELINE + u" 色档A/B=" + SUMMARY
      + u" 面积两颗=" + AREA_ONLY_SHORT
      + u" 峰值口径=" + CH_COUNTS_SHORT
      + u" 墨量=" + MAG_SHORT
      + u" 敏感名单=" + SENS_LIST[:120]
      + u" 点名=" + CENSUS[:60]
      + u" runner⓪=" + RUN_AB_SUMMARY_SHORT + u" / " + RUN_GEOM_SHORT
      + u" 出口=" + u",".join(sorted(set(NOT_RUN_PILL)))
      + u" 搬运=" + MUST_INCLUDE
      + u" 预检bad=" + s(PRE_BAD) + u" 在册=" + s(ARM_REG) + u"/" + s(ARM_FILES)
      + u"表 rot=" + s(ROT_NOW) + u" 抽不出=" + s(OPAQUE_NOW)
      + u" U=" + s(UA) + u".." + s(UF) + u" D=" + s(D1) + u"," + s(D2) + u" BL=" + s(B1)
      + u" derived(Round " + s(RDN) + u")=" + s(DERIVED2)
      + u" report尾轮=Round " + s(last_round) + u" 节数=" + s(rounds_after))
