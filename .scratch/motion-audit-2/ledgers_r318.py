# -*- coding: utf-8 -*-
u"""R318 的七本台账（第 317 轮 / Round 315 · 判据轮：373② 的两枚系统参照臂进尺）。

与 ledgers_r317.py 最大的不同：**本轮有可编译改动**（判据侧一个文件），
所以构建 / 全量卷 / 重捕帧 / 帧基线 / 换装这五腿**全部适用**，每一个数都必须从
`/tmp/r318_rv/*` 与 `/tmp/r318_probe.log` 里**解析**出来，解析不到就整批不写。
闸门：① 改动面现读必须含那个判据文件且**不含任何 `ClipboardHistory/Sources/` 文件**
（产品 0 文件这条也是读出来的，不是我说的）；② 电池写盘前后同数；③ 曲线尺 GAPS=none 且给出本轮派生分；
④ `product_streak --check` 必须签；⑤ 腐烂尺与针预检必须自己签；⑥ 七维表恰好 7 行、
U 定义行恰好三格、新 BACKLOG 条目号 = 现读最大 +1、无残留占位符。
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
BODIES = os.path.join(ROOT, ".scratch", "motion-audit-2", "r318_bodies.txt")
RV = u"/tmp/r318_rv2"
PROBE_LOG = u"/tmp/r318_probe4.log"
HARNESS = u"ClipboardHistory/Tests/ClipboardHistoryAppTests/UICaptureHarness.swift"
TODAY = u"2026-10-24"
R_TAG, PREV_TAG, R_NEXT = u"R318", u"R317", u"R319"
PREV_ROUND, ROUND, RDN = 316, 317, 315
NEEDLE_HOUSE = 367
WROTE, OK_EXIT = [], []


def die(msg):
    sys.stderr.write(u"R318_LEDGERS_REFUSE %s\n" % msg)
    if WROTE:
        for key, text in orig.items():
            wr(FILES[key], text)
        sys.stderr.write(u"R318_RESTORED 七本已整体还原\n")
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
ap = argparse.ArgumentParser(prog="ledgers_r318.py", description=u"R318 的七本台账（判据轮）")
ap.add_argument(u"--eye", default=os.environ.get(u"R318_EYE", u""),
                help=u"看图腿正文（也可用环境变量 R318_EYE 传）")
ARGS = ap.parse_args()
EYE = ARGS.eye.strip()
if not EYE:
    die(u"看图腿没传 R318_EYE / --eye ⇒ 真实视觉审查不许省略，也不许凭记忆写")

pre, pre_skip = battery(u"写盘前", u"/tmp/r318_battery_pre.log")

# 本轮的改动面：**读**出来，而不是声明。代码半那一笔必须动过判据文件，且不许动产品。
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
    die(u"改动面里找不到 %s ⇒ 代码半不在本轮名下（现读 %s）" % (HARNESS, u", ".join(sorted(touched))[:200]))
if product_touched:
    die(u"本轮是判据轮：动了产品文件就得改台账形状（现读 %s）" % u", ".join(sorted(product_touched))[:200])
# 代码半那一笔的短 sha（正文里要指着它）
CODE_SHA = None
for sha_ in round_shas:
    subj, _ = sh([u"git", u"log", u"-1", u"--format=%s", sha_])
    names, _ = sh([u"git", u"show", u"--name-only", u"--format=", sha_])
    if HARNESS in [n.strip() for n in names.splitlines()]:
        CODE_SHA = sha_[:7]
        break
if not CODE_SHA:
    die(u"读不到动过判据文件那一笔的 sha")

# —— 五腿读数，全部解析 ——
wg = log_read(os.path.join(RV, "warning_gate.log"), u"构建告警门")
WARN = (re.findall(r"(?m)^ROUND_WARNING_GATE .+$", wg) or [None])[-1]
if not WARN:
    die(u"warning_gate.log 里没有 ROUND_WARNING_GATE 行")
if u"warnings=0" not in WARN:
    die(u"构建门不是 0 告警：%s" % WARN[:120])

full = log_read(os.path.join(RV, "full.log"), u"全量卷")
rows = []
for m in re.finditer(r"Executed (\d+) tests?, with (\d+) tests? skipped and (\d+) failures?", full):
    rows.append(m.group(0))
if not rows:
    for m in re.finditer(r"Executed (\d+) tests?, and (\d+) failures?", full):
        rows.append(m.group(0))
if not rows:
    die(u"全量卷读不到汇总行 ⇒ 不许写进台账（也说明那一跑没跑完）")
counts = [(int(re.findall(r"\d+", r)[0]), r) for r in rows]
FULL = max(counts, key=lambda t: t[0])[1]
FAIL_N = int(re.findall(r"and (\d+) failures?", FULL)[-1])
red_names = sorted({m.group(1) for m in re.finditer(
    r"Test Case '-\[[^\]]+ (\w+)\]' failed", full)})
# 全量卷那一朵红**必须是已知的那一朵、且有归因**才允许按绿之外的形状落账：
# 归因写在 U-@UD@ 与新单 @BLNEW2@ 里（`preserveCorruptFile` 的秒级命名 + 一次启动走两遍 load()）。
KNOWN_RED = u"testCorruptHistoryWithoutBackupPreservesOriginalAndReferencedImages"
if FAIL_N == 1 and red_names == [KNOWN_RED]:
    print(u"FULL_RED_ACCEPTED 只有那一朵已归因的红：%s" % KNOWN_RED)
elif FAIL_N != 0:
    die(u"全量卷的红不是已归因那一朵（failures=%d，现读名单=%s）⇒ 先归因再落账"
        % (FAIL_N, u", ".join(red_names) or u"读不到名单"))
elif len(red_names) != 0:
    die(u"汇总行说 0 失败但名单里有红（%s）⇒ 读数通道自己矛盾" % u", ".join(red_names)[:120])

cap = log_read(os.path.join(RV, "capture.log"), u"重捕帧")
cap_hits = re.findall(r"CAPTURED (\d+) -> (\S+)", cap)
if not cap_hits:
    die(u"capture.log 读不到 CAPTURED 行（被计数物自己打印的那一行才是分母，不能 ls 数）")
CAPT = u"CAPTURED %s -> %s" % cap_hits[-1]
CAPT_N = int(cap_hits[-1][0])

base = log_read(os.path.join(RV, "baseline.log"), u"帧基线")
def bkey(k):
    m = re.findall(r"^FRAME_BASELINE_%s=(\d+)" % k, base, re.M)
    if not m:
        die(u"baseline.log 读不到 FRAME_BASELINE_%s" % k)
    return m[-1]
BC, CM, MS, AD = bkey(u"CHANGED"), bkey(u"COMPARED"), bkey(u"MISSING"), bkey(u"ADDED")
BASE = u"FRAME_BASELINE_COMPARED=%s CHANGED=%s MISSING=%s ADDED=%s" % (CM, BC, MS, AD)
if BC != u"0" or MS != u"0":
    die(u"帧基线不干净（changed=%s missing=%s）⇒ 本轮没改夹具，先查这一跑是不是撞上了别的改动" % (BC, MS))
if str(CAPT_N) != CM:
    die(u"重捕帧 %d 与基线分母 %s 不同源 ⇒ 两把尺量的不是同一堆东西" % (CAPT_N, CM))

rvout = log_read(os.path.join(RV, "round_verify.out"), u"四件套")
RVLINE = (re.findall(r"(?m)^ROUND_VERIFY .+$", rvout) or [None])[-1]
if not RVLINE:
    die(u"round_verify.out 读不到 ROUND_VERIFY 结论行（换装那一腿没落盘）")
# 换装那一腿只认 `round_verify.sh` **自己印**的那两个字段。
# （R318 现场自曝：我先按记忆要求 `INSTALL_RESULT=ok` —— 那是 `install_local.sh` 的结论行，
#   而四件套脚本打的是 `dmg=ok installed_version=<版本>` ⇒ 门按一个不存在的通道要数，整批拒写。
#   记在这里是因为这正是本仓库反复教的那一课：**命令与字段要现场抄**。）
if u"dmg=ok" not in RVLINE:
    die(u"四件套没签 dmg 那一腿：%s" % RVLINE[:160])
VER = (re.findall(r"installed_version=(\S+)", RVLINE) or [None])[-1]
if not VER or VER == u"NA":
    die(u"读不到换装后的版本号（installed_version=%s）⇒ 那一腿只能记 NOT-RUN" % s(VER))

probe = log_read(PROBE_LOG, u"新判据定向卷")
SEL_LIGHT = (re.findall(r"(?m)^QUICKPICK_SELARM light .+$", probe) or [None])[-1]
SEL_DARK = (re.findall(r"(?m)^QUICKPICK_SELARM dark .+$", probe) or [None])[-1]
SEL_SUM = (re.findall(r"(?m)^QUICKPICK_SELARM_SUMMARY .+$", probe) or [None])[-1]
for nm, v in ((u"light", SEL_LIGHT), (u"dark", SEL_DARK), (u"SUMMARY", SEL_SUM)):
    if not v:
        die(u"probe.log 读不到 QUICKPICK_SELARM_%s / _%s 行" % (nm, nm))
shares = re.findall(u"底色占比=药丸(\\d+)%/页底(\\d+)%", probe)
if len(shares) != 2:
    die(u"probe.log 里的占比读数不是两档（现读 %d 条）" % len(shares))
SEL_SHARE = (u"药丸 %s%%（亮）/ %s%%（暗），页底 %s%% / %s%%，闸门 60%%"
             % (shares[0][0], shares[1][0], shares[0][1], shares[1][1]))
SEL_SUM_SHORT = (re.findall(u"落点=(\\S+)", SEL_SUM) or [None])[-1]
if not SEL_SUM_SHORT:
    die(u"汇总行里读不到落点")
PROBE_FAIL = (re.findall(r"Executed 1 test, with (\d+) failures?", probe) or [None])
if not PROBE_FAIL:
    die(u"probe.log 读不到定向卷的 Executed 行")
PROBE_FAIL = PROBE_FAIL[0]
PROBE_EXEC = u"Executed 1 test, with %s failures（新判据两档都有对象）" % PROBE_FAIL
if PROBE_FAIL != u"0":
    die(u"新判据自己是红的（%s failures）⇒ 台账不能按绿落" % PROBE_FAIL)
if u"未判=0" not in SEL_SUM:
    die(u"新判据有档没读出对象（%s）⇒ 落点行不能当成两档都判过" % SEL_SUM[:120])

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
UA, UB, UC, UD = U_MAX + 1, U_MAX + 2, U_MAX + 3, U_MAX + 4
dec = rd(FILES[u"DEC"])
DN = max(int(x) for x in re.findall(r"(?m)^\*\*D-(\d{3,4})（", dec)) + 1
bl = rd(FILES[u"BL"])
BL_MAX = max(int(x) for x in re.findall(r"(?m)^\*\*(\d{3})\. ", bl))
BL_NEW, BL_NEW2 = BL_MAX + 1, BL_MAX + 2
for must_no, why in ((NEEDLE_HOUSE, u"@BLMINUS@ 的引用"), (373, u"本轮要追记的那一单"),
                     (BL_MAX, u"最大那一条")):
    if u"**%d. " % must_no not in bl:
        die(u"BACKLOG %d 不在盘上（%s）" % (why, must_no))
for no in (BL_NEW, BL_NEW2):
    if u"**%d. " % no in bl:
        die(u"BACKLOG %d 已经在盘上 ⇒ 新单号撞了，不能复用" % no)

KNIFE_SUM = (u"本轮 0 把刀（新尺刚出厂，容差还是探针刻度）：两把刀的锚点已现场 grep 各命中恰好 1"
             u"（M914 钉参照臂解析那一行、M915 钉 `fill.isHidden = !showsHoverTint(isSelected: isSelected,` 那一行），"
             u"表与跑归 %s —— 没有刀的判据今天只是尺，不是牙" % R_NEXT)

SUBS = {u"@ROUND@": ROUND, u"@RTAG@": R_TAG, u"@RPREVTAG@": PREV_TAG, u"@RNEXT@": R_NEXT,
        u"@RDN@": RDN, u"@TODAY@": TODAY, u"@UA@": UA, u"@UB@": UB, u"@UC@": UC, u"@UD@": UD,
        u"@DN@": DN, u"@DN2@": DN + 1, u"@BLNEW@": BL_NEW, u"@BLMINUS@": NEEDLE_HOUSE,
        u"@SEL_SHARE@": SEL_SHARE, u"@SEL_SUM_SHORT@": SEL_SUM_SHORT,
        u"@BATT@": pre, u"@SKIP@": pre_skip,
        u"@STREAK@": STREAK_N, u"@PREVSTREAK@": PREV_STREAK, u"@LASTSHA@": LASTSHA,
        u"@LASTROUND@": LASTROUND, u"@CI@": CI, u"@HALINE@": HA_LINE, u"@ROT@": ROT_NOW,
        u"@OPAQUE@": OPAQUE_NOW, u"@HIDTBL@": DECLARED_TBL, u"@HIDTBL2@": REMAIN_TABLES,
        u"@TABLES@": TABLES_N, u"@COVERED@": COVERED, u"@PREBAD@": PRE_BAD,
        u"@ARMREG@": ARM_REG, u"@ARMFILES@": ARM_FILES, u"@KNIFESUM@": KNIFE_SUM,
        u"@WARN@": WARN, u"@FULL@": FULL, u"@CAPT@": CAPT, u"@BASE@": BASE,
        u"@RVLINE@": RVLINE, u"@PROBE_EXEC@": PROBE_EXEC, u"@HEADSHA@": CODE_SHA,
        u"@SEL_LIGHT@": SEL_LIGHT, u"@SEL_DARK@": SEL_DARK, u"@SEL_SUM@": SEL_SUM}
EYE = fill(EYE, SUBS)
SUBS[u"@EYE@"] = EYE
SUBS[u"@EYE_SHORT@"] = EYE.split(u"⇒")[0].strip()

if not os.path.exists(BODIES):
    die(u"正文文件 %s 不在盘上" % BODIES)
ns = {}
exec(compile(rd(BODIES), BODIES, u"exec"), ns)
for k in (u"UI_NEW", u"IT_NEW", u"DEC_NEW", u"CH_NEW", u"ST_NEW", u"BL_追记", u"BL_NEW"):
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
         u"BLADD": fill(ns[u"BL_追记"], SUBS) + fill(ns[u"BL_NEW"], SUBS)}
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
# BACKLOG：373 的追记写在**原条目尾部**，新单 @BLNEW@ 紧随其后（373 是文件尾那一条）
if not orig[u"BL"].rstrip().endswith(u"也不许照着 181 去改产品配色。"):
    die(u"BACKLOG 的尾巴不再是 373 那一条 ⇒ 追记会被接到别的条目上，先看清文件尾")
new_bl = orig[u"BL"].rstrip(u"\n") + u"\n" + texts[u"BLADD"].rstrip(u"\n") + u"\n"
for no in (BL_NEW,):
    if new_bl.count(u"**%d. " % no) != 1:
        die(u"新单 %d 没落成恰好一条（命中 %d）" % (no, new_bl.count(u"**%d. " % no)))
if u"**%d. " % (BL_NEW + 1) in new_bl:
    die(u"新单跳号了：%d 还没开就先出现 %d" % (BL_NEW, BL_NEW + 1))
if new_bl.count(u"追记（%s）" % R_TAG) != 1:
    die(u"373 的追记没落成恰好一条")
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
        sys.stderr.write(u"R318_CRASH_RESTORED 未捕获异常 ⇒ 七本已整体还原\n")


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
             u"其中产品 0 个、判据 1 个（`UICaptureHarness.swift`）⇒ 构建 / 全量卷 / 重捕帧 / 帧基线 / 换装五腿**全部适用且都跑了**："
             u"%s；全量卷 %s；重捕 %s；基线 %s；四件套 %s。产品面连续零改动轮数 = **%s**"
             u"（唯一取数口 `python3 scripts/product_streak.py --streak-for %s`，as-of 第 %s 轮的最后一笔产品提交是 %s = 第 %s 轮；"
             u"上一轮那一格是 %s）。新落点：浮层选中药丸第一次被放到两枚系统参照色之间判，"
             u"新落点：浮层选中药丸第一次被放到两枚系统参照色之间判，@SEL_SUM_SHORT@（残差 0、容差 2）"
             u"⇒ 373 的②号出口结案：帧上那颗灰是系统的非 key 选中档，不是产品挑的配色；①号真机眼仍开。"
             u"全量卷那一朵红归到产品侧（failures=%d，名单现读 = %s）：`history.corrupt-<秒级时间戳>.json` 的保全不幂等"
             u"⇒ 新开 BACKLOG %d，修法（按内容幂等 + 用例等条件跨秒界）与刀都写进那一单。"
             % (len(touched), WARN, FULL, CAPT, BASE, RVLINE, STREAK_N, ROUND, ROUND, LASTSHA,
                LASTROUND, PREV_STREAK, FAIL_N, u", ".join(red_names) or u"空", BL_NEW))
scale_cell = (u"- **判据与门的规模**：脚本电池现读 **Ran %s**（写盘后同数），"
              u"变异臂在册 **%s** 把 / %s 张表（预检 tables=%s covered=%s bad=%s）；"
              u"腐烂针尺现读 `%s`；U 定义行 **%s 条**、最大 **U-%s**；决定台账最大 **D-%s**，"
              u"BACKLOG 最大 **%d**（本轮开一条新单：不幂等的 corrupt 原件保全；并给 373 写了结案追记）。"
              u"本轮新落两条决定：D-%d 与 D-%d"
              % (pre, ARM_REG, ARM_FILES, TABLES_N, COVERED, PRE_BAD, HA_LINE,
                 len(re.findall(u"(?m)^- \\*\\*U-(\\d{3,4})[：(]", new_ui)), UD, DN + 1, BL_NEW, DN, DN + 1))
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
rf, rfc = sh([sys.executable, os.path.join(ROOT, ".scratch", "motion-audit-2",
                                           "refresh_report_section1.py")])
if rfc != 0 or u"REFUSED" in rf:
    die(u"§1 那一格的刷新器没签（rc=%d）：%s" % (rfc, rf.strip()[-200:]))

post, post_skip = battery(u"写盘后", u"/tmp/r318_battery_post.log")
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
if u"U-31 … U-%d" % UD not in rd(FILES[u"FR"]):
    die(u"报告 §1 的 U 上界不是本轮的 U-%d" % UD)

OK_EXIT.append(True)
print(u"LEDGERS_R318 OK batt=Ran " + post + u" (skipped=" + post_skip + u") streak=" + STREAK_N
      + u"(上一轮 " + PREV_STREAK + u") 改动面=" + s(len(touched)) + u" 产品=" + s(len(product_touched))
      + u" 帧=" + s(CAPT_N) + u"/" + s(CM) + u" 基线changed=" + s(BC)
      + u" 预检bad=" + s(PRE_BAD) + u" 在册=" + s(ARM_REG) + u"/" + s(ARM_FILES) + u"表 rot=" + s(ROT_NOW)
      + u" 抽不出=" + s(OPAQUE_NOW) + u" U=" + s(UA) + u".." + s(UD) + u" D=" + s(DN)
      + u" BL新=" + s(BL_NEW) + u" 全量红=" + s(FAIL_N)
      + u" 代码半=" + CODE_SHA
      + u" derived(Round " + s(RDN) + u")=" + s(DERIVED2)
      + u" report尾轮=Round " + s(last_round) + u" 节数=" + s(rounds_after))
