# -*- coding: utf-8 -*-
u"""R324 的七本台账（第 323 轮 / Round 321 · 动效主线：形状闸 + 钉色档 + runner 两朵红交账）。

与 r323 的四处不同：
① 改动面仍是**两颗判据文件**（`MotionFilmstripTests.swift` + `MotionPillRampTests.swift`），
   仍不含任何 `ClipboardHistory/Sources/**`；
② 本轮的结论建立在**六行读数**上（`MOTION_PILL_BAND` / `_RAMP` / `_RAMP_GEOM` / `_SLIDE` /
   `_SLIDE_SETTLE` / `MOTION_SCENARIO_APPEAR`），全部从落盘日志解析；正文抄的那几个数逐一对账，
   对不上就拒写；
③ BACKLOG 一次**新开三单**（@BLNUM1@/@BLNUM2@/@BLNUM3@）⇒ 条目数必须 +3，
   并且 376 / 377 各有一条追记要落在**自己那条与下一条之间**（两个插入点，不是一个）；
④ 刀只有一支（本轮 M931…M936，6/6），但**runner 那一跑的两朵红是本轮的靶** ⇒
   runner 日志必须给得出带子原文、页底电平、两行红名，缺任何一条就拒写。

跑法：PYTHONUTF8=1 python3 .scratch/motion-audit-2/ledgers_r324.py --eye "<看图腿正文>"
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
BODIES = os.path.join(ROOT, ".scratch", "motion-audit-2", "r324_bodies.txt")
RV = u"/tmp/r324_rv"
KNIFE_LOG = os.path.join(RV, u"mutate_r324.log")
PILL_LOG = os.path.join(RV, u"pill_final.log")
RUNNER_LOG = os.path.join(RV, u"runner.log")
ROWS_LOG = u"/tmp/r324_rows.log"
FILM = u"ClipboardHistory/Tests/ClipboardHistoryAppTests/MotionFilmstripTests.swift"
WITNESS = u"ClipboardHistory/Tests/ClipboardHistoryAppTests/MotionPillRampTests.swift"
TODAY = u"2026-10-24"
R_TAG, PREV_TAG, R_NEXT = u"R324", u"R323", u"R325"
RTAGNUM = u"324"
PREV_ROUND, ROUND, RDN = 322, 323, 321
RUN_ID = u"40032708615"
RUN_SHA = u"28c8510"
BL_MAX_PREV = 382           # 上一轮账上的最后一条（382 = 本轮「台账形状修一笔」那一笔开的）
NEW_ENTRIES = 3
WROTE, OK_EXIT = [], []


def die(msg):
    sys.stderr.write(u"R324_LEDGERS_REFUSE %s\n" % msg)
    if WROTE:
        for key, text in orig.items():
            wr(FILES[key], text)
        sys.stderr.write(u"R324_RESTORED 七本已整体还原\n")
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
ap = argparse.ArgumentParser(prog="ledgers_r324.py", description=u"R324 的七本台账（形状闸 + 钉色档）")
ap.add_argument(u"--eye", default=os.environ.get(u"R324_EYE", u""),
                help=u"看图腿正文（也可用环境变量 R324_EYE 传）")
ARGS = ap.parse_args()
EYE = ARGS.eye.strip()
if not EYE:
    die(u"看图腿没传 R324_EYE / --eye ⇒ 真实视觉审查不许省略，也不许凭记忆写")

pre, pre_skip = battery(u"写盘前", u"/tmp/r324_battery_pre.log")

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
subj_rows, _ = sh([u"git", u"log", u"-14", u"--format=%h\x1f%s"])
fix_sha = u""
for row in subj_rows.splitlines():
    if u"\x1f" in row and R_TAG in row and u"台账形状修一笔" in row:
        fix_sha = row.split(u"\x1f", 1)[0]
        break
if not fix_sha:
    die(u"读不到本轮「台账形状修一笔」那一笔的 sha ⇒ STATE identity 行与豁免登记没有出处")
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

# —— 本轮的主菜：胶囊两卷 + 缺席点名（本机）——
pill = log_read(PILL_LOG, u"胶囊两卷")
PILL = last(pill, r"(?m)^MOTION_PILL_SLIDE filter-pill-slide .+$", u"MOTION_PILL_SLIDE")
PILL_SETTLE = last(pill, r"(?m)^MOTION_PILL_SLIDE_SETTLE .+$", u"_SLIDE_SETTLE")
BAND = last(pill, r"(?m)^MOTION_PILL_BAND .+$", u"MOTION_PILL_BAND")
RAMP = last(pill, r"(?m)^MOTION_PILL_RAMP filter-pill-slide .+$", u"MOTION_PILL_RAMP")
GEOM = last(pill, r"(?m)^MOTION_PILL_RAMP_GEOM .+$", u"_RAMP_GEOM")
CENSUS = last(pill, r"(?m)^MOTION_SCENARIO_APPEAR .+$", u"MOTION_SCENARIO_APPEAR")
exec_hits = re.findall(r"Executed (\d+) tests?, with (?:(\d+) tests? skipped and )?(\d+) failures?", pill)
if not exec_hits:
    die(u"胶囊两卷读不到汇总行")
big = max(exec_hits, key=lambda t: int(t[0]))
if big[2] != u"0" or (big[1] or u"0") != u"0":
    die(u"胶囊两卷自己不是全绿（Executed=%s skip=%s fail=%s）⇒ 先归因再落账" % big)
PILL_EXEC = u"Executed %s tests, with %s failures（两卷一起跑，skip=0）" % (big[0], big[2])

cm = re.search(r"工厂=(\d+) 钉了=(\d+) 没钉=(\d+) 钉了名单=(\S*) 没钉名单=(\S*)", CENSUS)
if not cm:
    die(u"MOTION_SCENARIO_APPEAR 那行形状变了：%s" % CENSUS[:200])
CENSUS_TOTAL, CENSUS_PIN, CENSUS_UNPIN, CENSUS_PINNED, CENSUS_UNPINNED = cm.groups()
if int(CENSUS_TOTAL) != int(CENSUS_PIN) + int(CENSUS_UNPIN):
    die(u"缺席点名不闭合：工厂=%s 钉了=%s 没钉=%s" % (CENSUS_TOTAL, CENSUS_PIN, CENSUS_UNPIN))
if int(CENSUS_PIN) < 1 or u"filterPillSlide" not in CENSUS_PINNED:
    die(u"钉了色档的名单里没有 filterPillSlide ⇒ 本轮那一钉没落进源码：%s" % CENSUS[:160])

m = re.search(r"开A 帧数=(\d+)\(旧口径(\d+)\) 峰值=([\d.]+).*?关 帧数=(\d+)\(旧口径(\d+)\) 峰值=([\d.]+)"
              r".*?采样≈([\d.]+)ms", PILL)
if not m:
    die(u"MOTION_PILL_SLIDE 那行形状变了：%s" % PILL[:200])
SPAN_A, OLD_A, PEAK_A, SPAN_OFF, OLD_OFF, PEAK_OFF, INTERVAL = m.groups()
if not (int(SPAN_A) > int(SPAN_OFF) and float(PEAK_A) < float(PEAK_OFF)):
    die(u"方向不成立了（开 %s 峰 %s 对 关 %s 峰 %s）⇒ 正文要按新形状重写"
        % (SPAN_A, PEAK_A, SPAN_OFF, PEAK_OFF))
if u"冷闸=true" not in PILL:
    die(u"有一臂是在冷采样下抓的 ⇒ 这一轮的结论今天不成立：%s" % PILL[:200])
SETTLE_MS = (re.findall(r"实测落定≈(\d+)ms", PILL_SETTLE) or [None])[-1]
if not SETTLE_MS:
    die(u"_SLIDE_SETTLE 那行读不到落定毫秒数：%s" % PILL_SETTLE[:160])

bm = re.search(r"带=x([\d.]+)…([\d.]+)pt y([\d.]+)…([\d.]+)pt", BAND)
if not bm:
    die(u"MOTION_PILL_BAND 那行形状变了：%s" % BAND[:160])
BAND_X0, BAND_X1, BAND_Y0, BAND_Y1 = (float(v) for v in bm.groups())
if not (40.0 <= BAND_Y0 <= 62.0 and 50.0 <= BAND_Y1 <= 95.0):
    die(u"量出来的带子不像胶囊那一行（y=%s…%spt）⇒ 定位谓词又坏了，先查再落账" % (BAND_Y0, BAND_Y1))
if u"来源=本卷" not in BAND:
    die(u"带子的出处没写明是本卷量的：%s" % BAND[:160])

gm = re.search(r"行带=([\d.]+)…([\d.]+)pt.*?倍率=([\d.]+) 页底=([\d.-]+) 色档=(\S+)"
               r" 轨道=([\d.-]+) 药丸=([\d.-]+) 分离=([\d.-]+) 容差=([\d.-]+)pt 定位=(.+)$", GEOM)
if not gm:
    die(u"_RAMP_GEOM 那行解析不出来：%s" % GEOM[:240])
(ROW_Y0, ROW_Y1, SCALE_NOW, MARGIN_L, APPEAR, TRACK_L, PILL_L, SEPARATION,
 TOLERANCE, GEOM_TAIL) = gm.groups()
if float(SEPARATION) < 8:
    die(u"本机分离度只有 %s ⇒ 斜坡尺在自己这台机器上都没对象，正文不能说它判到了" % SEPARATION)
if u"胶片暗" not in APPEAR:
    die(u"这一卷没拍在暗档里（色档=%s）⇒ 钉色档那一环没生效，正文整段归因要重写" % APPEAR)
cand = re.search(r"行=(\d+) 候选行=(\d+)", GEOM_TAIL)
if not cand:
    die(u"定位报告里没有 行=/候选行=：%s" % GEOM_TAIL[:160])
CAND_ROWS = cand.group(2)
if int(CAND_ROWS) < 4:
    die(u"候选行只有 %s 颗 ⇒ 带子仍然不稳，正文不能说它量到了" % CAND_ROWS)
narrow = re.search(r"候选段=([^|]+)判=洞太窄", GEOM_TAIL)
NARROWSEG = narrow.group(1).strip() if narrow else u"无"
if narrow is None:
    die(u"报告里没有'洞太窄'那一段 ⇒ 正文那句'字墨把洞切成两半'没有出处：%s" % GEOM_TAIL[:200])

rm = re.search(r"A 判定=(\S+) 首=([\d.-]+)pt 末=([\d.-]+)pt 位移=([\d.-]+)pt 最大倒退=([\d.-]+)pt", RAMP)
if not rm:
    die(u"MOTION_PILL_RAMP 那行解析不出来：%s" % RAMP[:200])
VERDICT, FIRST_PT, LAST_PT, TRAVEL, BACK = rm.groups()
if u"B 判定=" + VERDICT not in RAMP:
    die(u"两遍开臂给的词不同（A=%s）⇒ 这条判据今天没有对照物：%s" % (VERDICT, RAMP[:220]))
if VERDICT != u"单调" or float(BACK) != 0.0 or float(TRAVEL) < 50.0:
    die(u"本轮的产物结论形状变了（判定=%s 位移=%s 倒退=%s）⇒ 那是产品事实，正文与判据都要重写"
        % (VERDICT, TRAVEL, BACK))

# —— runner 交账（@RPREVTAG@ 那一跑的下游；本轮的靶就是这两朵红）——
runner = log_read(RUNNER_LOG, u"runner 读数")
RUN_GEOM = strip_step(last(runner, r"(?m)^.*MOTION_PILL_RAMP_GEOM .+$", u"runner 的 RAMP_GEOM"))
RUN_RAMP = strip_step(last(runner, r"(?m)^.*MOTION_PILL_RAMP filter-pill-slide .+$", u"runner 的 RAMP"))
RUN_PILL = strip_step(last(runner, r"(?m)^.*MOTION_PILL_SLIDE filter-pill-slide .+$", u"runner 的 PILL_SLIDE"))
RUN_BAND = strip_step(last(runner, r"(?m)^.*MOTION_PILL_BAND .+$", u"runner 的 PILL_BAND"))
rgm = re.search(r"行带=([\d.]+)…([\d.]+)pt.*?页底=([\d.-]+)", RUN_GEOM)
if not rgm:
    die(u"runner 的 GEOM 行解析不出来：%s" % RUN_GEOM[:200])
RUN_Y0, RUN_Y1, RUNMARGIN = rgm.groups()
if not (200.0 <= float(RUN_Y0)):
    die(u"runner 那一条带不在列表区（y=%s…%s）⇒ 本轮的归因（框到列表行）说错了对象" % (RUN_Y0, RUN_Y1))
if float(RUNMARGIN) < 120:
    die(u"runner 的页底是 %s（暗档量级）⇒ '那台机器在亮档'这句话没有出处，先重读 U-@UA@" % RUNMARGIN)
rpm = re.search(r"A 判定=(\S+) 首=([\d.-]+)pt 末=([\d.-]+)pt 位移=([\d.-]+)pt 最大倒退=([\d.-]+)pt", RUN_RAMP)
if not rpm:
    die(u"runner 的 RAMP 行解析不出来：%s" % RUN_RAMP[:200])
RUNVERDICT, RUN_FIRST, RUN_LAST, RUN_TRAVEL, RUN_BACK = rpm.groups()
if RUNVERDICT == u"单调":
    die(u"runner 这次判成了单调 ⇒ 那朵红已经不是本轮的形状，正文要重写")
bm2 = re.search(r"带=x([\d.]+)…([\d.]+)pt y([\d.]+)…([\d.]+)pt", RUN_BAND)
if not bm2:
    die(u"runner 的 BAND 行形状变了：%s" % RUN_BAND[:160])
RUNBAND = u"y%s…%spt" % (bm2.group(3), bm2.group(4))
rp_m = re.search(r"开A 帧数=(\d+)\(旧口径\d+\) 峰值=([\d.]+).*?关 帧数=(\d+)\(旧口径\d+\) 峰值=([\d.]+)",
                 RUN_PILL)
if not rp_m:
    die(u"runner 的 PILL_SLIDE 行解析不出来：%s" % RUN_PILL[:200])
RUN_SPAN_A, RUN_PEAK_A, RUN_SPAN_OFF, RUN_PEAK_OFF = rp_m.groups()
RUN_PILL_SHORT = u"开A 帧数=%s 峰值=%s / 关 帧数=%s 峰值=%s" % (
    RUN_SPAN_A, RUN_PEAK_A, RUN_SPAN_OFF, RUN_PEAK_OFF)
reds = re.findall(r"(?m)^ASSERTION_RED 行=(\d+) 去重后=(\d+)", runner)
if not reds:
    die(u"runner 日志里读不到 ASSERTION_RED 那行 ⇒ 两朵红没有出处")
RUN_RED_N = reds[-1][1]
for name in (u"testFilterPillRampIsMonotone", u"testFilterPillSlideIsAProcessNotATeleport"):
    if name not in runner:
        die(u"runner 的红名单里没有 %s ⇒ 本轮的靶读错了用例" % name)

# —— 上一轮那条带子的高度（正文要说覆盖率从多少掉到 7pt）——
prev_ui = rd(FILES[u"UI"])
pm2 = re.search(u"胶囊行带?在 (\\d+)…(\\d+)pt", prev_ui)
if not pm2:
    die(u"在 AGENT_UI_AUDIT 里读不到 @RPREVTAG@ 那条'胶囊行在 49…75pt'的原文 ⇒ 覆盖率那句话没出处")
PREV_BAND_TXT = u"%s…%spt" % (pm2.group(1), pm2.group(2))
PREV_BAND_H = int(pm2.group(2)) - int(pm2.group(1))
if not (15 <= PREV_BAND_H <= 40):
    die(u"上一轮那条带子高 %spt，不像整颗胶囊 ⇒ 出处找错了行" % PREV_BAND_H)
rv_line = last(prev_ui, u"(?m)^- \\*\\*U-1064[：(].*$", u"@RPREVTAG@ 的极性读数")
if u"36" not in rv_line or u"52" not in rv_line:
    die(u"@RPREVTAG@ 的 U-1064 那行读不到 轨道 52 / 药丸 36 ⇒ 亮档对照没基准：%s" % rv_line[:160])

# —— 刀：一支表 ——
KNIFELINE, KNIFEARMS = knife_summary(KNIFE_LOG, u"本轮变异表（M931…M936）", 6)

pc, _rc = sh([sys.executable, PRECHECK])
pre_line = re.findall(r"NEEDLE_PRECHECK tables=(\d+) covered=(\d+) arms=(\d+) bad=(\d+)", pc)
if not pre_line:
    die(u"NEEDLE_PRECHECK 没读到")
TABLES_N, COVERED, _PA, PRE_BAD = (int(x) for x in pre_line[-1])
if PRE_BAD:
    die(u"针预检 bad=%d ⇒ 有 needle 在册上腐烂" % PRE_BAD)
if u"mutate_r324" not in pc:
    die(u"mutate_r324 不在预检名册里（新表出厂第一天就要在册）")
reg_line = re.findall(r"ARM_TOTAL files=(\d+) arms=(\d+) dupes=(\d+) repeats=(\d+)", pc)
if not reg_line:
    die(u"ARM_TOTAL 没读到")
ARM_FILES, ARM_REG, ARM_DUPES, ARM_REPEATS = (int(x) for x in reg_line[-1])
if ARM_DUPES or ARM_REPEATS:
    die(u"名册报 dupes=%d repeats=%d" % (ARM_DUPES, ARM_REPEATS))

# —— 新读数族必须真的进了搬运名单（R107 / U-339 那一族）——
FAMILIES = [u"MOTION_PILL_BAND", u"MOTION_PILL_RAMP", u"MOTION_PILL_RAMP_GEOM",
            u"MOTION_PILL_SLIDE", u"MOTION_PILL_SLIDE_SETTLE", u"MOTION_SCENARIO_APPEAR"]
rm2, rmc = sh([sys.executable, ROWS, PILL_LOG] + [u"--must-include"] + FAMILIES)
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
UA, UB, UC, UD, UE = U_MAX + 1, U_MAX + 2, U_MAX + 3, U_MAX + 4, U_MAX + 5
dec = rd(FILES[u"DEC"])
D0 = max(int(x) for x in re.findall(r"(?m)^\*\*D-(\d{3,4})（", dec)) + 1
D1, D2 = D0, D0 + 1
bl = rd(FILES[u"BL"])
BL_MAX = max(int(x) for x in re.findall(r"(?m)^\*\*(\d{3})\. ", bl))
if BL_MAX != BL_MAX_PREV:
    die(u"BACKLOG 现读最大是 %d，台账准备的最后一条是 %d ⇒ 有人先开了单" % (BL_MAX, BL_MAX_PREV))
B1, B2, B3 = BL_MAX + 1, BL_MAX + 2, BL_MAX + 3

SUBS = {u"@ROUND@": ROUND, u"@RTAG@": R_TAG, u"@RTAGNUM@": RTAGNUM, u"@RPREVTAG@": PREV_TAG,
        u"@RNEXT@": R_NEXT, u"@RDN@": RDN, u"@TODAY@": TODAY, u"@RUNID@": RUN_ID, u"@RUNSHA@": RUN_SHA,
        u"@UA@": UA, u"@UB@": UB, u"@UC@": UC, u"@UD@": UD, u"@UE@": UE,
        u"@D1@": D1, u"@D2@": D2, u"@BLNUM1@": B1, u"@BLNUM2@": B2, u"@BLNUM3@": B3,
        u"@BLNEW1@": B1, u"@BLNEW2@": B2, u"@BLNEW3@": B3, u"@BLMAX@": BL_MAX,
        u"@BATT@": pre, u"@SKIP@": pre_skip, u"@STREAK@": STREAK_N, u"@PREVSTREAK@": PREV_STREAK,
        u"@CI@": CI, u"@HALINE@": HA_LINE, u"@ROT@": ROT_NOW, u"@OPAQUE@": OPAQUE_NOW,
        u"@TABLES@": TABLES_N, u"@COVERED@": COVERED, u"@PREBAD@": PRE_BAD,
        u"@ARMREG@": ARM_REG, u"@ARMFILES@": ARM_FILES,
        u"@WARN@": WARN, u"@FULL@": FULL, u"@CAPT@": CAPT, u"@BASE@": BASE,
        u"@RVLINE@": RVLINE, u"@KNIFELINE@": KNIFELINE, u"@KNIFEARMS@": KNIFEARMS,
        u"@PILL@": PILL, u"@PILL_SETTLE@": PILL_SETTLE, u"@PILL_EXEC@": PILL_EXEC,
        u"@BAND@": BAND, u"@RAMP@": RAMP, u"@GEOM@": GEOM, u"@GEOM_TAIL@": GEOM_TAIL,
        u"@CENSUS@": CENSUS, u"@CENSUS_TOTAL@": CENSUS_TOTAL, u"@CENSUS_PIN@": CENSUS_PIN,
        u"@CENSUS_UNPIN@": CENSUS_UNPIN, u"@CENSUS_PINNED@": CENSUS_PINNED,
        u"@CENSUS_UNPINNED@": CENSUS_UNPINNED, u"@CAND_ROWS@": CAND_ROWS,
        u"@NARROWSEG@": NARROWSEG, u"@APPEAR@": APPEAR, u"@SCALE_NOW@": SCALE_NOW,
        u"@VERDICT@": VERDICT, u"@TRAVEL@": TRAVEL, u"@BACK@": BACK,
        u"@SPAN_A@": SPAN_A, u"@SPAN_OFF@": SPAN_OFF, u"@OLD_A@": OLD_A, u"@OLD_OFF@": OLD_OFF,
        u"@PEAK_A@": PEAK_A, u"@PEAK_OFF@": PEAK_OFF, u"@SETTLE_MS@": SETTLE_MS,
        u"@INTERVAL@": INTERVAL, u"@SEPARATION@": SEPARATION, u"@MARGIN_L@": MARGIN_L,
        u"@TRACK_L@": TRACK_L, u"@PILL_L@": PILL_L,
        u"@ROW_Y0@": ROW_Y0, u"@ROW_Y1@": ROW_Y1,
        u"@BAND_Y0@": s(BAND_Y0), u"@BAND_Y1@": s(BAND_Y1),
        u"@RUN_GEOM@": RUN_GEOM, u"@RUN_RAMP@": RUN_RAMP, u"@RUN_PILL@": RUN_PILL,
        u"@RUN_PILL_SHORT@": RUN_PILL_SHORT, u"@RUNBAND@": RUNBAND, u"@RUNMARGIN@": RUNMARGIN,
        u"@RUNVERDICT@": RUNVERDICT, u"@RUNTRAVEL@": RUN_TRAVEL, u"@RUNBACK@": RUN_BACK,
        u"@RUN_RED_N@": RUN_RED_N, u"@MUST_INCLUDE@": MUST_INCLUDE,
        u"@PREVBAND@": PREV_BAND_TXT, u"@PREVBANDH@": PREV_BAND_H,
        u"@RPREVTRAVELBAND@": PREV_BAND_TXT, u"@HEADSHA@": head_sha,
        u"@BLROSTER@": BL_MAX, u"@FIXSHA@": fix_sha}
EYE = fill(EYE, SUBS)
SUBS[u"@EYE@"] = EYE
SUBS[u"@EYE_SHORT@"] = EYE.split(u"⇒")[0].strip()

if not os.path.exists(BODIES):
    die(u"正文文件 %s 不在盘上" % BODIES)
ns = {}
exec(compile(rd(BODIES), BODIES, u"exec"), ns)
for k in (u"UI_NEW", u"IT_NEW", u"DEC_NEW", u"CH_NEW", u"ST_NEW", u"BL_NEW",
          u"BL_追记_376", u"BL_追记_377"):
    if k not in ns:
        die(u"正文缺 %s" % k)

orig = {k: rd(v) for k, v in FILES.items()}
for key, marker in ((u"UI", u"## 第 %d 轮" % ROUND), (u"IT", u"## Round %d ·" % RDN),
                    (u"ST", u"## %s 状态（" % R_TAG)):
    if marker in orig[key]:
        die(u"%s 里已经有本轮那一节 ⇒ 生成器不许重跑第二遍" % key)

texts = dict((k, fill(ns[k], SUBS)) for k in
             (u"UI_NEW", u"IT_NEW", u"DEC_NEW", u"CH_NEW", u"ST_NEW", u"BL_NEW",
              u"BL_追记_376", u"BL_追记_377"))
for k, t in texts.items():
    hit = STRAY_RX.findall(t)
    if hit:
        die(u"文本 %s 里还有没替换的占位符：%s" % (k, u",".join(sorted(set(hit)))))

heads = [(int(m.group(1)), m.start()) for m in re.finditer(u"(?m)^## 第 (\\d+) 轮", orig[u"UI"])]
top = max(heads)[1]
new_ui = orig[u"UI"][:top] + texts[u"UI_NEW"] + orig[u"UI"][top:]
if new_ui.count(u"## 第 %d 轮" % ROUND) != 1:
    die(u"UI_AUDIT 新节没落在最大轮次标题之上")
nums = [int(m.group(1)) for m in re.finditer(u"(?m)^- \\*\\*U-(\\d{3,4})[：(]", texts[u"UI_NEW"])]
if nums != [UA, UB, UC, UD, UE]:
    die(u"新节的 U 定义行是 %s，要 %s" % (nums, [UA, UB, UC, UD, UE]))
new_it = orig[u"IT"].rstrip(u"\n") + u"\n\n" + texts[u"IT_NEW"].rstrip(u"\n") + u"\n"
if len(re.findall(u"(?m)^\\| (真实视觉审查|判据有效性|假绿防御|产品面推进|台账一致性|交付诚实性|可复核性) \\| (\\d+)/15 \\|$",
                  texts[u"IT_NEW"])) != 7:
    die(u"七维表不是恰好 7 行")
new_dec = orig[u"DEC"].rstrip(u"\n") + u"\n\n" + texts[u"DEC_NEW"].rstrip(u"\n") + u"\n"
d_hits = re.findall(u"(?m)^\\*\\*D-(\\d{3,4})（", texts[u"DEC_NEW"])
if [int(x) for x in d_hits] != [D1, D2]:
    die(u"新决定行是 %s，要 %s" % (d_hits, [D1, D2]))

# BACKLOG：376 / 377 各一条追记，落在"自己那条与下一条之间"；本轮另**新开三单**追加在文件尾。
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


bl_with_add = insert_addition(orig[u"BL"], texts[u"BL_追记_376"], 376, 377)
bl_with_add = insert_addition(bl_with_add, texts[u"BL_追记_377"], 377, 378)
new_bl = bl_with_add.rstrip(u"\n") + u"\n\n" + texts[u"BL_NEW"].rstrip(u"\n") + u"\n"
bl_nums = [int(m.group(1)) for m in re.finditer(u"(?m)^\\*\\*(\\d{3})\\. ", new_bl)]
if bl_nums[-NEW_ENTRIES:] != [B1, B2, B3]:
    die(u"新开的三单没落在尾部或编号不连续：%s" % bl_nums[-6:])
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

fr = orig[u"FR"]
if len(re.findall(u"U-31 … U-\\d+（R\\d+ 现读抬到最新一节）", fr)) != 1:
    die(u"§1 的 U 那一格锚点命中不是 1")
fr = re.sub(u"U-31 … U-\\d+（R\\d+ 现读抬到最新一节）",
            u"U-31 … U-%d（%s 现读抬到最新一节）" % (UE, R_TAG), fr, count=1)
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
        sys.stderr.write(u"R324_CRASH_RESTORED 未捕获异常 ⇒ 七本已整体还原\n")


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

prod_cell = (u"- **产品面（这一节最该被读的部分）**：本轮产品文件 0 个（**动效主线**：git 现读改动面 = %d 个文件，"
             u"产品 0 个、判据 2 个（`MotionFilmstripTests.swift` + `MotionPillRampTests.swift`）；五腿**全部适用且都跑了**：%s；全量卷 %s；"
             u"重捕 %s；基线 %s；四件套 %s。产品面连续零改动轮数 = **%s**"
             u"（唯一取数口 `python3 scripts/product_streak.py --streak-for %s`，`--check` 同形；上一轮那一格是 %s）。"
             u"本轮交的是**上一轮两朵 runner 红的账与修法**：那把逐行像素尺在 runner 上框到了列表里的一行"
             u"（%s、页底 %s ⇒ 那台机器在亮档），判成「%s」与「两臂峰值相等」；本机同一卷在亮档里干脆没有对象"
             u"（三档只差 3 级 < delta 8）。修法两半：三道形状闸（宽度稳 / 贴两端 / 至少一段之宽，D-%d）"
             u"+ 胶片场景第一次能钉色档并把「请求==要求 / 胶片==要求 / 两遍同档」写成红前提压在出口之前（D-%d）。"
             u"改后本机：%s、判定=**%s**、位移 %spt、倒退 %spt、分离 %s 级、带子 %s。"
             u"同一轮一处公开更正：为「去掉极性」设计的 `staticLevel` 锚被真窗口的帧量死了（轨道里没有一列不动），"
             u"已撤回并锚回页底。刀：本轮 %s（逐臂 %s）。"
             % (len(touched), WARN, FULL, CAPT, BASE, RVLINE, STREAK_N, ROUND, PREV_STREAK,
                RUNBAND, RUNMARGIN, RUNVERDICT, D2, D1, GEOM, VERDICT, TRAVEL, BACK, SEPARATION,
                BAND, KNIFELINE, KNIFEARMS))
scale_cell = (u"- **判据与门的规模**：脚本电池现读 **Ran %s**（写盘后同数），"
              u"变异臂在册 **%s** 把 / %s 张表（预检 tables=%s covered=%s bad=%s）；"
              u"腐烂针尺现读 `%s`；U 定义行 **%s 条**、最大 **U-%s**；决定台账最大 **D-%d**，"
              u"BACKLOG 最大 **%d**（本轮新开 %d…%d 三单：12 颗工厂没钉色档、字墨把洞切成两半、"
              u"M932 那把刀的机器相关性）；新读数族搬运名单 `READINGS_MUST_INCLUDE %s`"
              % (pre, ARM_REG, ARM_FILES, TABLES_N, COVERED, PRE_BAD, HA_LINE,
                 len(re.findall(u"(?m)^- \\*\\*U-(\\d{3,4})[：(]", new_ui)), UE, D2, B3, B1, B3,
                 MUST_INCLUDE))
where_cell = (u"- **走到哪了**：阶段二累计 `## Round` 节 **%s** 节，最新一节是 **Round %s**；"
              u"自评曲线按轮现读 %s（现读 `curve_from_ledger.py`）。派生分本轮仍不到 90 以上的那条线，"
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

post, post_skip = battery(u"写盘后", u"/tmp/r324_battery_post.log")
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
if u"U-31 … U-%d" % UE not in rd(FILES[u"FR"]):
    die(u"报告 §1 的 U 上界不是本轮的 U-%d" % UE)

OK_EXIT.append(True)
print(u"LEDGERS_R324 OK batt=Ran " + post + u" (skipped=" + post_skip + u") streak=" + STREAK_N
      + u"(上一轮 " + PREV_STREAK + u") 产品文件=" + s(len(product_touched))
      + u" 改动面=" + s(len(touched)) + u" 帧=" + s(CAPT_N) + u"/" + s(CM) + u" 基线changed=" + s(BC)
      + u" 刀=" + KNIFELINE + u" 斜坡=" + VERDICT + u"/位移" + TRAVEL + u"pt/倒退" + BACK + u"pt"
      + u" 带=" + s(BAND_Y0) + u".." + s(BAND_Y1) + u"pt 分离=" + SEPARATION
      + u" 候选行=" + CAND_ROWS + u" 洞太窄段=" + NARROWSEG
      + u" 点名=" + CENSUS_TOTAL + u"/" + CENSUS_PIN + u"/" + CENSUS_UNPIN
      + u" runner带=" + RUNBAND + u" 页底=" + RUNMARGIN + u" 判定=" + RUNVERDICT + u" 红=" + RUN_RED_N
      + u" 搬运=" + MUST_INCLUDE
      + u" 预检bad=" + s(PRE_BAD) + u" 在册=" + s(ARM_REG) + u"/" + s(ARM_FILES)
      + u"表 rot=" + s(ROT_NOW) + u" 抽不出=" + s(OPAQUE_NOW)
      + u" U=" + s(UA) + u".." + s(UE) + u" D=" + s(D1) + u"," + s(D2) + u" BL=" + s(B1) + u".." + s(B3)
      + u" derived(Round " + s(RDN) + u")=" + s(DERIVED2)
      + u" report尾轮=Round " + s(last_round) + u" 节数=" + s(rounds_after))
