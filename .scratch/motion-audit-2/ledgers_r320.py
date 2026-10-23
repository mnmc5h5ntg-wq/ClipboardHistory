# -*- coding: utf-8 -*-
u"""R320 的七本台账（第 319 轮 / Round 317 · 判据轮：368 判到通道边界）。

形状是 r318（产品 0 文件 ⇒ 那道"不许动 Sources"的闸门回来）与 r319（刀不再是散文）的合体：
① 改动面必须含 harness 那个判据文件、且**不含任何 `ClipboardHistory/Sources/**`**；
② 连续零改动轮数必须 ≥1（R319 归零之后重新起算，这一格也是读出来的）；
③ 本轮的结论是"全 0"，所以**正对照必须先签**：`HEATMAP_TOOLTIP_CONTROL` 那一行里
   toolTip 与无障碍都必须 ≥1，否则产品那侧的 0 不许进台账（D-303 的自证）；
④ 刀必须 k==n 且 RESTORE_CLEAN=yes，逐臂行数等于分母；
⑤ 368 的追记写在**原条目内部**（锚点是 `**369. ` 那一行之前），不是文件尾 ——
   文件尾那一条现在是 374，追加到底会把追记接错条目。
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
BODIES = os.path.join(ROOT, ".scratch", "motion-audit-2", "r320_bodies.txt")
RV = u"/tmp/r320_rv"
KNIFE_LOG = u"/tmp/r320_chain.log"
PROBE_LOG = u"/tmp/r320_probe_final.log"
HARNESS = u"ClipboardHistory/Tests/ClipboardHistoryAppTests/UICaptureHarness.swift"
TODAY = u"2026-10-24"
R_TAG, PREV_TAG, R_NEXT = u"R320", u"R319", u"R321"
PREV_ROUND, ROUND, RDN = 318, 319, 317
NEEDLE_HOUSE = 367
ENTRY_HOUSE = 368          # 本轮追记要落进的那一单
NEXT_ENTRY = 369           # 它的下一条（锚点：追记必须插在它之前）
WROTE, OK_EXIT = [], []


def die(msg):
    sys.stderr.write(u"R320_LEDGERS_REFUSE %s\n" % msg)
    if WROTE:
        for key, text in orig.items():
            wr(FILES[key], text)
        sys.stderr.write(u"R320_RESTORED 七本已整体还原\n")
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
ap = argparse.ArgumentParser(prog="ledgers_r320.py", description=u"R320 的七本台账（判据轮）")
ap.add_argument(u"--eye", default=os.environ.get(u"R320_EYE", u""),
                help=u"看图腿正文（也可用环境变量 R320_EYE 传）")
ARGS = ap.parse_args()
EYE = ARGS.eye.strip()
if not EYE:
    die(u"看图腿没传 R320_EYE / --eye ⇒ 真实视觉审查不许省略，也不许凭记忆写")

pre, pre_skip = battery(u"写盘前", u"/tmp/r320_battery_pre.log")

# —— 改动面：本轮必须是判据轮（产品 0 文件）——
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
if HARNESS not in touched:
    die(u"改动面里找不到 %s" % HARNESS)
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
VER = (re.findall(r"installed_version=(\S+)", RVLINE) or [None])[-1]
if not VER or VER == u"NA":
    die(u"读不到换装后的版本号 ⇒ 那一腿只能记 NOT-RUN")

# —— 探针与正对照 ——
probe = log_read(PROBE_LOG, u"探针卷")
CTRL = (re.findall(r"(?m)^HEATMAP_TOOLTIP_CONTROL .+$", probe) or [None])[-1]
CHAN = (re.findall(r"(?m)^HEATMAP_TOOLTIP_CHANNELS .+$", probe) or [None])[-1]
if not CTRL or not CHAN:
    die(u"探针日志里读不到 CONTROL / CHANNELS 两行 ⇒ 这一轮的结论没有出处")
ct = int((re.findall(u"热图型toolTip=(\\d+)", CTRL) or [None])[-1])
ca = int((re.findall(u"热图型无障碍=(\\d+)", CTRL) or [None])[-1])
cv = int((re.findall(u"视图=(\\d+)", CTRL) or [None])[-1])
if ct < 1 or ca < 1:
    die(u"正对照没签（toolTip=%d 无障碍=%d）⇒ 产品那侧的 0 不许进台账（D-303 的自证）" % (ct, ca))
if cv != 3:
    die(u"正对照的遍历数不是 3（现读 %d）⇒ 对照树形状变了，先修尺" % cv)
prod_tips = int((re.findall(u"热图型toolTip合计=(\\d+)", CHAN) or [None])[-1])
prod_a11y = int((re.findall(u"热图型无障碍合计=(\\d+)", CHAN) or [None])[-1])
if prod_tips != 0 or prod_a11y != 0:
    die(u"产品那侧不再是 0（toolTip=%d 无障碍=%d）⇒ 结论变了，正文要重写而不是改数字"
        % (prod_tips, prod_a11y))
exec_hits = re.findall(r"Executed 1 test, with (\d+) failures?", probe)
if not exec_hits:
    die(u"探针卷读不到 Executed 行")
if exec_hits[-1] != u"0":
    die(u"探针卷自己是红的（%s failures）" % exec_hits[-1])
PROBE_EXEC = (u"Executed 1 test, with 0 failures（正对照 toolTip=%d / 无障碍=%d / 视图=%d 已签；"
              u"产品四屏×档合计 toolTip=%d 无障碍=%d）"
              % (ct, ca, cv, prod_tips, prod_a11y))

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
if int(K_CAUGHT) != int(K_TOTAL):
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
if int(STREAK_N) < 1:
    die(u"本轮没动产品，连续零改动轮数却读到 %s ⇒ 取数口与改动面矛盾，先查哪一个错" % STREAK_N)
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
if u"**%d. " % ENTRY_HOUSE not in bl or u"**%d. " % NEXT_ENTRY not in bl:
    die(u"BACKLOG %d 或 %d 不在盘上 ⇒ 追记的锚点没有出处" % (ENTRY_HOUSE, NEXT_ENTRY))
if bl.index(u"**%d. " % ENTRY_HOUSE) > bl.index(u"**%d. " % NEXT_ENTRY):
    die(u"%d 在 %d 之后 ⇒ 追记的插入点算错了（会接到别的条目上）" % (ENTRY_HOUSE, NEXT_ENTRY))

SUBS = {u"@ROUND@": ROUND, u"@RTAG@": R_TAG, u"@RPREVTAG@": PREV_TAG, u"@RNEXT@": R_NEXT,
        u"@RDN@": RDN, u"@TODAY@": TODAY, u"@UA@": UA, u"@UB@": UB, u"@UC@": UC,
        u"@DN@": DN, u"@BLMAX@": BL_MAX, u"@BLMINUS@": NEEDLE_HOUSE,
        u"@BATT@": pre, u"@SKIP@": pre_skip, u"@STREAK@": STREAK_N, u"@PREVSTREAK@": PREV_STREAK,
        u"@LASTSHA@": LASTSHA, u"@LASTROUND@": LASTROUND, u"@CI@": CI, u"@HALINE@": HA_LINE,
        u"@ROT@": ROT_NOW, u"@OPAQUE@": OPAQUE_NOW, u"@HIDTBL@": DECLARED_TBL,
        u"@HIDTBL2@": REMAIN_TABLES, u"@TABLES@": TABLES_N, u"@COVERED@": COVERED,
        u"@PREBAD@": PRE_BAD, u"@ARMREG@": ARM_REG, u"@ARMFILES@": ARM_FILES,
        u"@WARN@": WARN, u"@FULL@": FULL, u"@CAPT@": CAPT, u"@BASE@": BASE,
        u"@RVLINE@": RVLINE, u"@PROBE_EXEC@": PROBE_EXEC,
        u"@TOOLTIP_CONTROL@": CTRL, u"@TOOLTIP_CHANNELS@": CHAN,
        u"@KNIFELINE@": KNIFELINE, u"@KNIFEARMS@": KNIFEARMS, u"@HEADSHA@": head_sha}
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
# BACKLOG：追记插在 368 那一条的**末尾**（= 下一条 `**369. ` 之前）
anchor = u"\n**%d. " % NEXT_ENTRY
pos = orig[u"BL"].find(anchor)
if pos < 0:
    die(u"找不到 %s 这一行的位置 ⇒ 追记没有插入点" % (anchor.strip()))
new_bl = (orig[u"BL"][:pos] + u"\n" + texts[u"BLADD"].rstrip(u"\n")
          + orig[u"BL"][pos:])
if new_bl.count(u"追记（%s）" % R_TAG) != 1:
    die(u"%d 的追记没落成恰好一条" % ENTRY_HOUSE)
if len(re.findall(u"(?m)^\\*\\*(\\d{3})\\. ", new_bl)) != len(re.findall(u"(?m)^\\*\\*(\\d{3})\\. ", orig[u"BL"])):
    die(u"BACKLOG 条目数变了 ⇒ 本轮说好只写追记")
# 追记必须落在 368 与 369 之间
if not (new_bl.index(u"**%d. " % ENTRY_HOUSE) < new_bl.index(u"追记（%s）" % R_TAG)
        < new_bl.index(u"**%d. " % NEXT_ENTRY)):
    die(u"追记落错了条目（不在 %d 与 %d 之间）" % (ENTRY_HOUSE, NEXT_ENTRY))
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
        sys.stderr.write(u"R320_CRASH_RESTORED 未捕获异常 ⇒ 七本已整体还原\n")


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

prod_cell = (u"- **产品面（这一节最该被读的部分）**：本轮产品文件 0 个（**判据轮**：git 现读改动面 = %d 个文件，"
             u"产品 0 个、判据 1 个（`UICaptureHarness.swift`）；五腿**全部适用且都跑了**：%s；全量卷 %s；"
             u"重捕 %s；基线 %s；四件套 %s。产品面连续零改动轮数 = **%s**"
             u"（R%d 那笔产品改动之后重新起算；唯一取数口 `python3 scripts/product_streak.py --streak-for %s`，"
             u"`--check` 同形；上一轮那一格是 %s）。本轮的结论是**一条带正对照签名的全 0**："
             u"%s；%s ⇒ 热图 hover 提示在离屏产物里没有可读通道（368 收成具名出口，剩真机眼那半）。"
             u"两把刀钉在证人上：%s。"
             % (len(touched), WARN, FULL, CAPT, BASE, RVLINE, STREAK_N, ROUND - 1, ROUND,
                PREV_STREAK, CTRL, CHAN, KNIFELINE))
scale_cell = (u"- **判据与门的规模**：脚本电池现读 **Ran %s**（写盘后同数），"
              u"变异臂在册 **%s** 把 / %s 张表（预检 tables=%s covered=%s bad=%s）；"
              u"腐烂针尺现读 `%s`；U 定义行 **%s 条**、最大 **U-%s**；决定台账最大 **D-%d**，"
              u"BACKLOG 最大 **%d**（本轮不开新单，给 %d 写了判到头的追记）"
              % (pre, ARM_REG, ARM_FILES, TABLES_N, COVERED, PRE_BAD, HA_LINE,
                 len(re.findall(u"(?m)^- \\*\\*U-(\\d{3,4})[：(]", new_ui)), UC, DN, BL_MAX, ENTRY_HOUSE))
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
# §13 那张「最后一次动到 Sources/ 的轮次」本轮**不该动**（没动源码），但要确认它仍与 git 同源。
chk_out, chk = sh([sys.executable, u"-m", u"unittest", u"-v",
                   u"test_final_report_headline.FinalReportSourcesCellTests.test_the_sources_cell_agrees_with_git"],
                  cwd=os.path.join(ROOT, "scripts", "tests"))
if chk != 0:
    die(u"§13 的 Sources 那一格与 git 不同源（rc=%d）：%s" % (chk, chk_out.strip()[-300:]))
rf, rfc = sh([sys.executable, os.path.join(ROOT, ".scratch", "motion-audit-2",
                                           "refresh_report_section1.py")])
if rfc != 0 or u"REFUSED" in rf:
    die(u"§1 那一格的刷新器没签（rc=%d）：%s" % (rfc, rf.strip()[-200:]))

post, post_skip = battery(u"写盘后", u"/tmp/r320_battery_post.log")
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
if u"U-31 … U-%d" % UC not in rd(FILES[u"FR"]):
    die(u"报告 §1 的 U 上界不是本轮的 U-%d" % UC)

OK_EXIT.append(True)
print(u"LEDGERS_R320 OK batt=Ran " + post + u" (skipped=" + post_skip + u") streak=" + STREAK_N
      + u"(上一轮 " + PREV_STREAK + u") 产品文件=" + s(len(product_touched))
      + u" 改动面=" + s(len(touched)) + u" 帧=" + s(CAPT_N) + u"/" + s(CM) + u" 基线changed=" + s(BC)
      + u" 刀=" + K_CAUGHT + u"/" + K_TOTAL + u" restore=" + K_RESTORE
      + u" 对照=" + s(ct) + u"/" + s(ca) + u" 产品0=" + s(prod_tips) + u"/" + s(prod_a11y)
      + u" 预检bad=" + s(PRE_BAD) + u" 在册=" + s(ARM_REG) + u"/" + s(ARM_FILES) + u"表 rot=" + s(ROT_NOW)
      + u" 抽不出=" + s(OPAQUE_NOW) + u" U=" + s(UA) + u".." + s(UC) + u" D=" + s(DN)
      + u" BL最大=" + s(BL_MAX) + u" derived(Round " + s(RDN) + u")=" + s(DERIVED2)
      + u" report尾轮=Round " + s(last_round) + u" 节数=" + s(rounds_after))
