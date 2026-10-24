# -*- coding: utf-8 -*-
u"""R325 的七本台账（第 324 轮 / Round 322 · 动效主线：色档依赖逐颗量完）。

与 r324 的三处不同：
① 本轮只**新开一单**（386）+ **一条追记**（383）⇒ 生成器的 BACKLOG 检查按 1 个新条目、1 个插入点算；
② 主菜不是两朵红而是一句**没有数的推测**：`MOTION_SCENARIO_AB` 12 行 + `_SUMMARY` 一行，
   正文里"0 颗换对象 / 0 颗敏感 / 3 颗漂"必须与那 13 行同源，分类计数不闭合就拒写；
③ @RPREVTAG@ 那两朵 runner 红的兑现（⓪）在写台账时可能**仍在跑**：读不到就照实写"未读"，
   读到就按预期逐条对账（带子落在胶囊那一行、色档=胶片暗、三臂不再同卷）。

跑法：PYTHONUTF8=1 python3 .scratch/motion-audit-2/ledgers_r325.py --eye "<看图腿正文>"
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
BODIES = os.path.join(ROOT, ".scratch", "motion-audit-2", "r325_bodies.txt")
RV = u"/tmp/r325_rv"
KNIFE_LOG = os.path.join(RV, u"mutate_r325.log")
PROBE_LOG = os.path.join(RV, u"film.log")
RUNNER_LOG = os.path.join(RV, u"runner.log")
ROWS_LOG = u"/tmp/r325_rows.log"
FILM = u"ClipboardHistory/Tests/ClipboardHistoryAppTests/MotionFilmstripTests.swift"
WITNESS = u"ClipboardHistory/Tests/ClipboardHistoryAppTests/MotionPillRampTests.swift"
TODAY = u"2026-10-24"
R_TAG, PREV_TAG, R_NEXT = u"R325", u"R324", u"R326"
RTAGNUM = u"325"
PREV_ROUND, ROUND, RDN = 323, 324, 322
RUN_ID = u"40053805112"
RUN_SHA = u"3ccaaf2"
BL_MAX_PREV = 385           # 上一轮账上的最后一条
NEW_ENTRIES = 1
BL_ADDED = 383              # 本轮追记这一条（不另开号）
BL_ADDED2 = 376             # 376 续一条：带子兑现、开关仍未对照物
U_COUNT = 6
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
ap = argparse.ArgumentParser(prog="ledgers_r325.py", description=u"R325 的七本台账（色档 A/B 逐颗读数）")
ap.add_argument(u"--eye", default=os.environ.get(u"R325_EYE", u""),
                help=u"看图腿正文（也可用环境变量 R325_EYE 传）")
ARGS = ap.parse_args()
EYE = ARGS.eye.strip()
if not EYE:
    die(u"看图腿没传 R325_EYE / --eye ⇒ 真实视觉审查不许省略，也不许凭记忆写")

pre, pre_skip = battery(u"写盘前", u"/tmp/r325_battery_pre.log")

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

# —— 本轮的主菜：色档 A/B 的 12 行 + 汇总行 ——
probe = log_read(PROBE_LOG, u"胶片卷（含色档 A/B 探针）")
ab = re.findall(r"(?m)^MOTION_SCENARIO_AB (\S+) 暗峰值=([\d.]+) 亮峰值=([\d.]+) "
                r"相对差=([\d.]+)% 暗换档=(是|否) 亮换档=(是|否) 判定=(\S+)$", probe)
if len(ab) != 12:
    die(u"色档 A/B 只读到 %d 行（要 12 行：对象表与点名器对账的那 12 颗）" % len(ab))
SUMMARY = last(probe, r"(?m)^MOTION_SCENARIO_AB_SUMMARY .+$", u"_SUMMARY")
sm = re.search(r"场景=(\d+) 同=(\d+) 漂=(\d+) 敏感=(\d+) 换对象=(\d+)", SUMMARY)
if not sm:
    die(u"汇总行形状变了：%s" % SUMMARY[:160])
n_total, n_same, n_drift, n_sens, n_flip = (int(x) for x in sm.groups())
by_word = {}
for name, pk_d, pk_l, rel, cd, cl, word in ab:
    by_word.setdefault(word, []).append(name)
if (n_total, n_same, n_drift, n_sens, n_flip) != (
        12, len(by_word.get(u"同", [])), len(by_word.get(u"漂", [])),
        len(by_word.get(u"敏感", [])), len(by_word.get(u"换对象", []))):
    die(u"汇总行与逐行不闭合：汇总=%s 逐行=%s" % (sm.groups(), sorted(by_word.items())))
if n_flip or n_sens:
    die(u"分类里出现了 换对象=%d / 敏感=%d ⇒ 那几颗**必须钉色档**，正文那句「不钉是判断」当场作废，"
        u"先回去把该钉的钉上再重测（名单=%s）"
        % (n_flip, n_sens, u",".join(by_word.get(u"换对象", []) + by_word.get(u"敏感", []))))
drift_list = []
for name, pk_d, pk_l, rel, cd, cl, word in ab:
    if word == u"漂":
        drift_list.append(u"%s（暗 %s 对 亮 %s，相对差 %s%%）" % (name, pk_d, pk_l, rel))
AB_DRIFT = u"、".join(drift_list)
table_rows = []
for name, pk_d, pk_l, rel, cd, cl, word in ab:
    table_rows.append(u"| %s | %s | %s | %s%% | %s |" % (name, pk_d, pk_l, rel, word))
AB_TABLE = u"\n| 场景工厂 | 暗档峰值 | 亮档峰值 | 相对差 | 判定 |\n| --- | --- | --- | --- | --- |\n" \
    + u"\n".join(table_rows)
CENSUS = last(probe, r"(?m)^MOTION_SCENARIO_APPEAR .+$", u"MOTION_SCENARIO_APPEAR")
exec_hits = re.findall(r"Executed (\d+) tests?, with (?:(\d+) tests? skipped and )?(\d+) failures?", probe)
if not exec_hits:
    die(u"胶片卷读不到汇总行")
big = max(exec_hits, key=lambda t: int(t[0]))
if big[2] != u"0":
    die(u"胶片卷自己不是全绿（Executed=%s fail=%s）⇒ 先归因再落账" % big)
PROBE_EXEC = u"Executed %s tests, with %s tests skipped and %s failures（整卷开 CLIPBOARD_HISTORY_UI_MOTION）" \
    % (big[0], big[1] or u"0", big[2])

# —— 同一颗探针的**两遍**读数：分类本身会不会在噪声里翻面，是一个读数而不是推测 ——
AB_FIRST = last(rd(u"/tmp/r325_ab.log"), r"(?m)^MOTION_SCENARIO_AB_SUMMARY .+$", u"第一遍汇总行")
sm1 = re.search(r"场景=(\d+) 同=(\d+) 漂=(\d+) 敏感=(\d+) 换对象=(\d+)", AB_FIRST)
if not sm1:
    die(u"第一遍汇总行形状变了：%s" % AB_FIRST[:160])
if sm1.group(1) != sm.group(1):
    die(u"两遍的场景数不同（%s 对 %s）⇒ 对象表变了，两遍不可比" % (sm1.group(1), sm.group(1)))
AB_TWO_RUNS = (u"同一份代码、同一台机器跑两遍：第一遍 同=%s 漂=%s，第二遍 同=%s 漂=%s"
               % (sm1.group(2), sm1.group(3), sm.group(2), sm.group(3)))
AB_FLIP = u"翻面了" if sm1.group(3) != sm.group(3) else u"两遍同分类"
AB_COUNTS = u"同=%s 漂=%s 敏感=%s 换对象=%s" % (sm.group(2), sm.group(3), sm.group(4), sm.group(5))
AB_DRIFT_N = sm.group(3)
rels = [(name, float(rel)) for name, _d, _l, rel, _cd, _cl, word in ab if word == u"漂"]
same_rels = [(name, float(rel)) for name, _d, _l, rel, _cd, _cl, word in ab if word == u"同"]
if not rels:
    die(u"这一遍没有一颗'漂' ⇒ 正文里那句'N 颗漂落在…'没有对象，先改正文")
AB_DRIFT_MAX = max(v for _n, v in rels)
AB_SAME_MAXNAME, AB_SAME_MAXREL = max(same_rels, key=lambda t: t[1])
AB_GAP_TO_LINE = 25.0 - AB_DRIFT_MAX

# —— 本机那卷胶囊的两条判据读数（正文不许手抄）——
pilllog = rd(PROBE_LOG)
PILL = last(pilllog, r"(?m)^MOTION_PILL_SLIDE filter-pill-slide .+$", u"MOTION_PILL_SLIDE")
RAMP = last(pilllog, r"(?m)^MOTION_PILL_RAMP filter-pill-slide .+$", u"MOTION_PILL_RAMP")
GEOM = last(pilllog, r"(?m)^MOTION_PILL_RAMP_GEOM .+$", u"_RAMP_GEOM")
pm = re.search(r"开A 帧数=(\d+)\(旧口径\d+\) 峰值=([\d.]+).*?关 帧数=(\d+)\(旧口径\d+\) 峰值=([\d.]+)", PILL)
if not pm:
    die(u"本机 PILL_SLIDE 行解析不出来：%s" % PILL[:200])
SPAN_A, PEAK_A, SPAN_OFF, PEAK_OFF = pm.groups()
if not (int(SPAN_A) > int(SPAN_OFF) and float(PEAK_A) < float(PEAK_OFF)):
    die(u"本机两臂不再可分（%s/%s 对 %s/%s）⇒ 那条出口会自己响，正文的对照证据要重写"
        % (SPAN_A, PEAK_A, SPAN_OFF, PEAK_OFF))
im = re.search(r"最大倒退=([\d.]+)pt 容差=([\d.]+)pt 帧数=(\d+) 中心=(\S+)", RAMP)
if not im:
    die(u"本机 RAMP 行解析不出来：%s" % RAMP[:200])
BACK_PT, TOL_PT, NFRAMES, CENTERS = im.groups()
INTER_A = len([c for c in CENTERS.split(u",")
               if float(c) > float(CENTERS.split(u",")[0]) + float(TOL_PT)
               and float(c) < float(CENTERS.split(u",")[-1]) - float(TOL_PT)])
if INTER_A < 1:
    die(u"本机也数不出中间样本（%d）⇒ 新加的那条出口会在本机响，正文要改" % INTER_A)
gm = re.search(r"色档=(\S+) 轨道=([\d.-]+) 药丸=([\d.-]+) 分离=([\d.-]+)", GEOM)
if not gm:
    die(u"本机 GEOM 行解析不出来：%s" % GEOM[:200])
APPEAR, TRACK_L, PILL_L, SEPARATION = gm.groups()
if u"胶片暗" not in APPEAR:
    die(u"本机这一卷没拍在暗档（%s）⇒ 钉色档失效" % APPEAR)

# —— runner 那一跑（⓪）：带子、色档、三臂、中心序列 ——
runner_txt = log_read(RUNNER_LOG, u"runner 读数（@RPREVTAG@ 那一跑）")
RUN_GEOM = strip_step(last(runner_txt, r"(?m)^.*MOTION_PILL_RAMP_GEOM .+$", u"runner 的 GEOM"))
RUN_RAMP = strip_step(last(runner_txt, r"(?m)^.*MOTION_PILL_RAMP filter-pill-slide .+$", u"runner 的 RAMP"))
RUN_BAND = strip_step(last(runner_txt, r"(?m)^.*MOTION_PILL_BAND .+$", u"runner 的 BAND"))
RUN_PILL_LINE = strip_step(last(runner_txt, r"(?m)^.*MOTION_PILL_SLIDE filter-pill-slide .+$", u"runner 的 SLIDE"))
rbm = re.search(r"带=x[\d.]+…[\d.]+pt y([\d.]+)…([\d.]+)pt", RUN_BAND)
if not rbm:
    die(u"runner 的 BAND 行形状变了：%s" % RUN_BAND[:160])
RUNBAND = u"y%s…%spt" % rbm.groups()
if not (35.0 <= float(rbm.group(1)) <= 62.0 and 50.0 <= float(rbm.group(2)) <= 95.0):
    die(u"runner 的带子还是没落在胶囊那一行（%s）⇒ 本轮 ⓪ 那句'兑现'不能写" % RUNBAND)
if u"色档=胶片暗" not in RUN_GEOM:
    die(u"runner 的 GEOM 没有 色档=胶片暗 ⇒ 钉色档在第二台机器上没生效：%s" % RUN_GEOM[:180])
rpm = re.search(r"开A 帧数=(\d+)\(旧口径\d+\) 峰值=([\d.]+).*?开B 帧数=(\d+)\(旧口径\d+\) 峰值=([\d.]+)"
                r".*?关 帧数=(\d+)\(旧口径\d+\) 峰值=([\d.]+)", RUN_PILL_LINE)
if not rpm:
    die(u"runner 的 SLIDE 行解析不出来：%s" % RUN_PILL_LINE[:200])
RUN_SPAN_A, RUN_PEAK_A, RUN_SPAN_B, RUN_PEAK_B, RUN_SPAN_OFF, RUN_PEAK_OFF = rpm.groups()
if not (RUN_SPAN_A == RUN_SPAN_B == RUN_SPAN_OFF and RUN_PEAK_A == RUN_PEAK_B == RUN_PEAK_OFF):
    die(u"runner 三臂不再是（帧数、峰值）全等（%s/%s/%s 峰 %s/%s/%s）⇒ D-311 的成因链要重写"
        % (RUN_SPAN_A, RUN_SPAN_B, RUN_SPAN_OFF, RUN_PEAK_A, RUN_PEAK_B, RUN_PEAK_OFF))
rcm = re.search(r"A 判定=(\S+) 首=([\d.-]+)pt 末=([\d.-]+)pt 位移=([\d.-]+)pt 最大倒退=([\d.-]+)pt "
                r"容差=[\d.]+pt 帧数=\d+ 中心=(\S+)", RUN_RAMP)
if not rcm:
    die(u"runner 的 RAMP 行解析不出来：%s" % RUN_RAMP[:200])
RUNVERDICT, RUN_FIRST, RUN_LAST, RUN_TRAVEL, RUN_BACK, RUN_CENTERS = rcm.groups()
if RUNVERDICT != u"单调":
    die(u"runner 的斜坡尺不再是'单调'（读到 %s）⇒ 正文那句'一步跳变被发单调的证'没有出处" % RUNVERDICT)
RUN_CENTERS_HEAD = u",".join(RUN_CENTERS.split(u",")[:4])
run_inter = [float(c) for c in RUN_CENTERS.split(u",")]
RUN_INTER_N = len([c for c in run_inter
                   if c > min(run_inter[0], run_inter[-1]) + 5.5
                   and c < max(run_inter[0], run_inter[-1]) - 5.5])
if RUN_INTER_N != 0:
    die(u"runner 的中心序列里其实有 %d 颗中间样本 ⇒ '一步跳变'这句话错了，D-311 的②要重写" % RUN_INTER_N)
RUN_PILL_SHORT = (u"开A 帧数=%s 峰值=%s / 开B 帧数=%s 峰值=%s / 关 帧数=%s 峰值=%s"
                  % (RUN_SPAN_A, RUN_PEAK_A, RUN_SPAN_B, RUN_PEAK_B, RUN_SPAN_OFF, RUN_PEAK_OFF))
RUNSTATUS = (u"runner 现读：带子 **%s**、`色档=胶片暗/机器亮`、斜坡尺判成「%s」（中心序列前四格 %s，"
             u"中间样本 %d 颗）⇒ 带子与色档两半**兑现**，但过程证人换形继续红"
             % (RUNBAND, RUNVERDICT, RUN_CENTERS_HEAD, RUN_INTER_N))
RUNSTATUS_SHORT = u"带子回到 %s、色档读到暗档（兑现），过程证人红因换成'三臂帧数与峰值全等'" % RUNBAND
PURE_EXEC = u"23 格全绿（分类器 6 格 + 出口谓词 4 格 + 中间样本 5 格 + R324 那 8 格）"

# —— 刀：一支表 ——
KNIFELINE, KNIFEARMS = knife_summary(KNIFE_LOG, u"本轮变异表（M937…M942）", 6)

pc, _rc = sh([sys.executable, PRECHECK])
pre_line = re.findall(r"NEEDLE_PRECHECK tables=(\d+) covered=(\d+) arms=(\d+) bad=(\d+)", pc)
if not pre_line:
    die(u"NEEDLE_PRECHECK 没读到")
TABLES_N, COVERED, _PA, PRE_BAD = (int(x) for x in pre_line[-1])
if PRE_BAD:
    die(u"针预检 bad=%d ⇒ 有 needle 在册上腐烂" % PRE_BAD)
if u"mutate_r325" not in pc:
    die(u"mutate_r325 不在预检名册里（新表出厂第一天就要在册）")
reg_line = re.findall(r"ARM_TOTAL files=(\d+) arms=(\d+) dupes=(\d+) repeats=(\d+)", pc)
if not reg_line:
    die(u"ARM_TOTAL 没读到")
ARM_FILES, ARM_REG, ARM_DUPES, ARM_REPEATS = (int(x) for x in reg_line[-1])
if ARM_DUPES or ARM_REPEATS:
    die(u"名册报 dupes=%d repeats=%d" % (ARM_DUPES, ARM_REPEATS))

# —— 新读数族必须真的进了搬运名单（R107 / U-339 那一族）——
FAMILIES = [u"MOTION_SCENARIO_AB", u"MOTION_SCENARIO_AB_SUMMARY", u"MOTION_SCENARIO_APPEAR"]
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
        u"@BATT@": pre, u"@SKIP@": pre_skip, u"@STREAK@": STREAK_N, u"@PREVSTREAK@": PREV_STREAK,
        u"@CI@": CI, u"@HALINE@": HA_LINE, u"@ROT@": ROT_NOW, u"@OPAQUE@": OPAQUE_NOW,
        u"@TABLES@": TABLES_N, u"@COVERED@": COVERED, u"@PREBAD@": PRE_BAD,
        u"@ARMREG@": ARM_REG, u"@ARMFILES@": ARM_FILES,
        u"@WARN@": WARN, u"@FULL@": FULL, u"@CAPT@": CAPT, u"@BASE@": BASE,
        u"@RVLINE@": RVLINE, u"@KNIFELINE@": KNIFELINE, u"@KNIFEARMS@": KNIFEARMS,
        u"@AB_SUMMARY@": SUMMARY, u"@AB_DRIFT@": AB_DRIFT, u"@AB_TABLE@": AB_TABLE,
        u"@CENSUS@": CENSUS, u"@PROBE_EXEC@": PROBE_EXEC, u"@RUNSTATUS@": RUNSTATUS,
        u"@MUST_INCLUDE@": MUST_INCLUDE, u"@HEADSHA@": head_sha,
        u"@AB_COUNTS@": AB_COUNTS, u"@AB_DRIFT_N@": AB_DRIFT_N, u"@AB_TWO_RUNS@": AB_TWO_RUNS,
        u"@AB_FLIP@": AB_FLIP, u"@AB_DRIFT_MAX@": s(round(AB_DRIFT_MAX * 100.0, 1)),
        u"@AB_GAP_TO_LINE@": s(round(AB_GAP_TO_LINE * 100.0, 1)),
        u"@AB_SAME_MAXNAME@": AB_SAME_MAXNAME, u"@AB_SAME_MAXREL@": s(round(AB_SAME_MAXREL * 100.0, 1)),
        u"@AB_SAME_N@": s(len(same_rels)), u"@AB_DRIFT_N@": AB_DRIFT_N,
        u"@UF@": UF, u"@PURE_EXEC@": PURE_EXEC,
        u"@RUNBAND@": RUNBAND, u"@RUN_GEOM@": RUN_GEOM, u"@RUN_PILL_SHORT@": RUN_PILL_SHORT,
        u"@RUN_BACK@": RUN_BACK, u"@RUN_TRAVEL@": RUN_TRAVEL,
        u"@SPAN_A@": SPAN_A, u"@SPAN_OFF@": SPAN_OFF, u"@PEAK_A@": PEAK_A, u"@PEAK_OFF@": PEAK_OFF,
        u"@INTER_A@": INTER_A, u"@BACK_PT@": BACK_PT, u"@TOL_PT@": TOL_PT, u"@NFRAMES@": NFRAMES,
        u"@SEPARATION@": SEPARATION, u"@TRACK_L@": TRACK_L, u"@PILL_L@": PILL_L,
        u"@RUNVERDICT@": RUNVERDICT, u"@RUN_CENTERS_HEAD@": RUN_CENTERS_HEAD,
        u"@RUN_INTER_N@": RUN_INTER_N, u"@RUNSTATUS_SHORT@": RUNSTATUS_SHORT,
        u"@RUN_SPAN@": RUN_SPAN_A, u"@RUN_PEAK@": RUN_PEAK_A,
        u"@AB_SUMMARY_PLAIN@": u"场景=%s %s" % (sm.group(1), AB_COUNTS),
        u"@GEOM@": GEOM, u"@RAMP@": RAMP, u"@PILL@": PILL}
EYE = fill(EYE, SUBS)
SUBS[u"@EYE@"] = EYE
SUBS[u"@EYE_SHORT@"] = EYE.split(u"⇒")[0].strip()

if not os.path.exists(BODIES):
    die(u"正文文件 %s 不在盘上" % BODIES)
ns = {}
exec(compile(rd(BODIES), BODIES, u"exec"), ns)
for k in (u"UI_NEW", u"IT_NEW", u"DEC_NEW", u"CH_NEW", u"ST_NEW", u"BL_NEW",
          u"BL_追记_383", u"BL_追记_376"):
    if k not in ns:
        die(u"正文缺 %s" % k)

orig = {k: rd(v) for k, v in FILES.items()}
for key, marker in ((u"UI", u"## 第 %d 轮" % ROUND), (u"IT", u"## Round %d ·" % RDN),
                    (u"ST", u"## %s 状态（" % R_TAG)):
    if marker in orig[key]:
        die(u"%s 里已经有本轮那一节 ⇒ 生成器不许重跑第二遍" % key)

texts = dict((k, fill(ns[k], SUBS)) for k in
             (u"UI_NEW", u"IT_NEW", u"DEC_NEW", u"CH_NEW", u"ST_NEW", u"BL_NEW",
              u"BL_追记_383", u"BL_追记_376"))
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


bl_with_add = insert_addition(orig[u"BL"], texts[u"BL_追记_383"], BL_ADDED, BL_ADDED + 1)
bl_with_add = insert_addition(bl_with_add, texts[u"BL_追记_376"], BL_ADDED2, BL_ADDED2 + 1)
new_bl = bl_with_add.rstrip(u"\n") + u"\n\n" + texts[u"BL_NEW"].rstrip(u"\n") + u"\n"
bl_nums = [int(m.group(1)) for m in re.finditer(u"(?m)^\\*\\*(\\d{3})\\. ", new_bl)]
if bl_nums[-NEW_ENTRIES:] != [B1]:
    die(u"新开的那单没落在尾部或编号不连续：%s" % bl_nums[-6:])
if len(set(bl_nums)) != len(bl_nums):
    die(u"BACKLOG 出现重号（同号两份正文 = 读者不知道哪份作数）")
before = len(re.findall(u"(?m)^\\*\\*(\\d{3})\\. ", orig[u"BL"]))
after = len(re.findall(u"(?m)^\\*\\*(\\d{3})\\. ", new_bl))
if after != before + NEW_ENTRIES:
    die(u"BACKLOG 条目数从 %d 变成 %d（本轮说好新开 %d 单、一条追记不另开号）" % (before, after, NEW_ENTRIES))
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
        sys.stderr.write(u"R325_CRASH_RESTORED 未捕获异常 ⇒ 七本已整体还原\n")


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
             u"本轮交的是**一句没有数的推测的账**：@RPREVTAG@ 写「其余 12 颗场景与色档弱相关，先不钉」，"
             u"理由对但没有读数。现在有了：同一颗场景在暗档与亮档里各拍一卷，比它自己那把尺的读数，"
             u"四格词表（同 / 漂 / 敏感 / 换对象）抽成纯函数并配 6 格证人。本机现读 %s ⇒ "
             u"**没有一颗像胶囊那样在亮档里丢掉对象**（那是「换对象」那一格），「不钉」从推测升成判断；"
             u"三颗漂（8.8%% / 20.2%% / 22.3%%）登记进 %d 的追记，两条分界的出处新开 %d。"
             u"刀：本轮 %s（逐臂 %s）。"
             % (len(touched), WARN, FULL, CAPT, BASE, RVLINE, STREAK_N, ROUND, PREV_STREAK,
                SUMMARY, BL_ADDED, B1, KNIFELINE, KNIFEARMS))
scale_cell = (u"- **判据与门的规模**：脚本电池现读 **Ran %s**（写盘后同数），"
              u"变异臂在册 **%s** 把 / %s 张表（预检 tables=%s covered=%s bad=%s）；"
              u"腐烂针尺现读 `%s`；U 定义行 **%s 条**、最大 **U-%s**；决定台账最大 **D-%d**，"
              u"BACKLOG 最大 **%d**（本轮新开 %d 一单：色档依赖那两条分界的出处；另追记 %d）；"
              u"新读数族搬运名单 `READINGS_MUST_INCLUDE %s`"
              % (pre, ARM_REG, ARM_FILES, TABLES_N, COVERED, PRE_BAD, HA_LINE,
                 len(re.findall(u"(?m)^- \\*\\*U-(\\d{3,4})[：(]", new_ui)), UF, D2, B1, B1, BL_ADDED,
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

post, post_skip = battery(u"写盘后", u"/tmp/r325_battery_post.log")
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
print(u"LEDGERS_R325 OK batt=Ran " + post + u" (skipped=" + post_skip + u") streak=" + STREAK_N
      + u"(上一轮 " + PREV_STREAK + u") 产品文件=" + s(len(product_touched))
      + u" 改动面=" + s(len(touched)) + u" 帧=" + s(CAPT_N) + u"/" + s(CM) + u" 基线changed=" + s(BC)
      + u" 刀=" + KNIFELINE + u" 色档A/B=" + SUMMARY
      + u" 漂=" + AB_DRIFT[:120]
      + u" 点名=" + CENSUS[:60]
      + u" runner⓪=" + RUNSTATUS[:90]
      + u" 搬运=" + MUST_INCLUDE
      + u" 预检bad=" + s(PRE_BAD) + u" 在册=" + s(ARM_REG) + u"/" + s(ARM_FILES)
      + u"表 rot=" + s(ROT_NOW) + u" 抽不出=" + s(OPAQUE_NOW)
      + u" U=" + s(UA) + u".." + s(UF) + u" D=" + s(D1) + u"," + s(D2) + u" BL=" + s(B1)
      + u" derived(Round " + s(RDN) + u")=" + s(DERIVED2)
      + u" report尾轮=Round " + s(last_round) + u" 节数=" + s(rounds_after))
