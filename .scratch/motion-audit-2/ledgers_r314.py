# -*- coding: utf-8 -*-
u"""R314 的七本台账（第 313 轮 / Round 311 · 判据轮：空态补组合状态臂 + 自曝重复臂）。

形状照 `ledgers_r313.py`：所有数**现读**、锚点**整行命中恰好一次**、要么全写要么全不写、
写盘前后电池同数、曲线尺 GAPS=none、`product_streak --check` 必须签。
正文不在这里 —— 它在 `r314_bodies.txt`（整块 exec，占位符由 SUBS 填）。
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
BODIES = os.path.join(ROOT, ".scratch", "motion-audit-2", "r314_bodies.txt")
CHAIN = u"/tmp/r314_chain.log"
TODAY = u"2026-10-23"
R_TAG, PREV_TAG, R_NEXT = u"R314", u"R313", u"R315"
PREV_ROUND, ROUND, RDN = 312, 313, 311

WROTE = []
OK_EXIT = []

ap = argparse.ArgumentParser(prog="ledgers_r314.py",
                             description=u"R314 的七本台账（判据轮）")
ap.add_argument(u"--eye", default=os.environ.get(u"R314_EYE", u""),
                help=u"看图腿正文（也可用环境变量 R314_EYE 传）")
ARGS = ap.parse_args()


def die(msg):
    sys.stderr.write(u"R314_LEDGERS_REFUSE %s\n" % msg)
    if WROTE:
        for key, text in orig.items():
            wr(FILES[key], text)
        sys.stderr.write(u"R314_RESTORED 七本已整体还原\n")
    sys.exit(1)


def rd(path):
    h = io.open(path, encoding="utf-8")
    try:
        return h.read()
    finally:
        h.close()


def wr(path, text):
    h = io.open(path, "w", encoding="utf-8")
    try:
        h.write(text)
    finally:
        h.close()


def sh(argv, cwd=None):
    p = subprocess.Popen(argv, cwd=cwd or ROOT, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, close_fds=True)
    out, _ = p.communicate()
    return (out or b"").decode("utf-8", "replace"), p.returncode


def s(x):
    return x if isinstance(x, type(u"")) else str(x)


def fill(tpl, subs):
    out = tpl
    for k, v in subs.items():
        out = out.replace(k, s(v))
    return out


def battery(tag, log_path):
    out, rc = sh([sys.executable, u"-m", u"unittest", u"discover", u"-s", u"scripts/tests", u"-v"],
                 cwd=ROOT)
    h = io.open(log_path, "w", encoding="utf-8")
    try:
        h.write(out)
    finally:
        h.close()
    ran = re.findall(r"(?m)^Ran (\d+) tests? in", out)
    if not ran:
        die(u"%s 电池没打印 Ran 行（rc=%d）⇒ 按红处理，不许当绿" % (tag, rc))
    tail = out[out.rfind(u"Ran "):]
    if u"FAILED" in tail:
        die(u"%s 电池红：%s" % (tag, tail.splitlines()[1][:200] if len(tail.splitlines()) > 1 else tail[:200]))
    skip = re.findall(r"(?m)^OK \(skipped=(\d+)\)", tail)
    if not skip:
        if not re.search(r"(?m)^OK$", tail):
            die(u"%s 电池结论行既不是 OK 也不是 OK (skipped=N)：%s" % (tag, tail[:160].replace(u"\n", u" / ")))
        skip = [u"0"]
    return ran[-1], skip[-1]


def once(text, anchor, replacement, label):
    n = text.count(anchor)
    if n != 1:
        die(u"%s 的锚点命中 %d 次（要恰好 1）：%r" % (label, n, anchor[:60]))
    return text.replace(anchor, replacement)


STRAY_RX = re.compile(u"@([A-Z][A-Z0-9_]{1,24})@")
EYE = ARGS.eye.strip()
if not EYE:
    die(u"看图腿没传 R314_EYE / --eye ⇒ 真实视觉审查不许省略，也不许凭记忆写")

# ---------------------------------------------------------------- 现读
pre, pre_skip = battery(u"写盘前", u"/tmp/r314_battery_pre.log")

head_sub, _ = sh([u"git", u"log", u"-1", u"--format=%s"])
if R_TAG not in head_sub:
    die(u"HEAD 的 subject 不含 %s ⇒ 代码半还没提交，账不许先落（%s）" % (R_TAG, head_sub.strip()[:80]))

books = set(os.path.relpath(v, ROOT) for v in FILES.values())
log_out, _ = sh([u"git", u"log", u"-8", u"--format=%H\x1f%s"])
prod, swift_files, others, surface = [], [], [], []
for row in log_out.splitlines():
    if u"\x1f" not in row:
        continue
    sha_, subj_ = row.split(u"\x1f", 1)
    if R_TAG not in subj_:
        continue
    surface.append(sha_[:7])
    names, _ = sh([u"git", u"show", u"--name-only", u"--format=", sha_])
    for line in names.splitlines():
        line = line.strip()
        if not line or line in books:
            continue
        if line.startswith("ClipboardHistory/Sources/"):
            prod.append(line)
        elif line.startswith("ClipboardHistory/"):
            swift_files.append(line)
        else:
            others.append(line)
others = sorted(set(others))
if prod:
    die(u"本轮是判据轮：`Sources/` 应当 0 个文件，现读 %d（%s）" % (len(prod), u", ".join(prod)))
if not swift_files:
    die(u"本轮的改动就在捕获夹具里 ⇒ Swift 测试文件至少 1 个，现读 0")
if not any(o.startswith(u"docs/") for o in others):
    die(u"新增帧必须在同一笔里 update 帧基线（docs/frame_baseline.json 不在改动面：%s）"
        % u", ".join(others))

if not os.path.exists(CHAIN):
    die(u"证据链 %s 不在盘上 ⇒ 先跑 append_chain_r314.py，不许手填读数" % CHAIN)
chain = rd(CHAIN)
for needle, label in ((u"### BUILD", u"构建"), (u"### CAPTURE", u"两次捕获"),
                      (u"### FRAMES", u"帧目录计数"), (u"### MD5", u"重复臂对拍"),
                      (u"### EMPTY_INK", u"空态墨带"), (u"### PRECHECK", u"针预检"),
                      (u"### NEEDLE_PROBE", u"366 探针"), (u"### HIDDEN_ARMS", u"腐烂针尺"),
                      (u"### FRAME_BASELINE", u"帧基线对账"), (u"### SWIFT_SUMMARY", u"全量卷总结行"),
                      (u"### SWIFT_LEGS", u"捕获卷"), (u"### LOAD_RED", u"负载红")):
    if needle not in chain:
        die(u"验证链日志里没有「%s」那一节 ⇒ 那条腿没跑或没写清" % label)

warn = re.findall(r"WARNINGS=(\d+)", chain)
if not warn or warn[-1] != u"0":
    die(u"构建告警不是 0（现读 %s）" % (warn[-1] if warn else u"没解析到"))
FRAMES = (re.findall(r"FRAMES_ON_DISK=(\d+)", chain) or [u""])[-1]
if not FRAMES:
    die(u"没读到帧目录在盘上的张数 ⇒ 看图腿不许凭记忆说「帧还在」")

# 本轮 0 把新刀：证人不是刀，是**同一轮里的两次捕获**（第一跑红 → 登记后第二跑绿）。
# 所以这道门判的是「两次捕获都在，且第一次确实红过、第二次确实零红」。
cap_block = chain[chain.find(u"### CAPTURE"):chain.find(u"### FRAMES")]
m1 = re.search(u"R314_CAPTURE1 红=(\\d+)", cap_block)
m2 = re.search(u"R314_CAPTURE2 (.+?) 红=(\\d+)", cap_block, re.S)
if not m1 or not m2:
    die(u"读不到两次捕获的结论行 ⇒ 本轮的证人不在盘上：%s" % cap_block[:160])
CAP1_REDS, CAP2_REDS = int(m1.group(1)), int(m2.group(2))
CAP2_LINE = (re.findall(r"(?m)^CAPTURED .+$", cap_block) or [u"没读到 CAPTURED 行"])[-1]
if CAP1_REDS < 1:
    die(u"第一跑零红 ⇒ 那两处名册缺口根本没被顶出来，第二跑的绿不说明任何事")
if CAP2_REDS:
    die(u"登记之后仍红 %d 朵 ⇒ 不许出账" % CAP2_REDS)
ICONS = (re.findall(u"R314_CAPTURE1_ICON_FIRST=(\\d+) 行", cap_block) or [u"0"])[-1]
KNIFE_SUM = (u"本轮 0 把新刀（判断，不是遗漏）：证人 = 同一轮两次捕获，第一跑红 %d 朵 → 登记后第二跑零红且 %s；"
             u"名册被删任何一条，下一次就红" % (CAP1_REDS, CAP2_LINE))

MD5_SAME = (re.findall(u"两档全等=(\\w+)", chain) or [u"no"])[-1]
if MD5_SAME != u"yes":
    die(u"重复臂对拍没给出「两档全等=yes」⇒ U 里那句自曝没有证人（现读 %s）" % MD5_SAME)
INK_ROWS = [l for l in chain.splitlines() if l.startswith(u"EMPTY_INK ")]
if len(INK_ROWS) < 3:
    die(u"空态墨带读数不足 3 行 ⇒ 0.533 / 0.252 那两个数没有证人")
INK_PAIR = (re.findall(u"R314_INK_PAIR .+$", chain) or [u""])[-1]

RD_LINE = (re.findall(r"(?m)^SWIFT_SUMMARY .+$", chain) or [u""])[-1]
_sum = re.findall(u"Executed (\\d+) tests?, with (\\d+) tests? skipped and (\\d+) failures", RD_LINE)
if not _sum:
    die(u"SWIFT_SUMMARY 那行解析不出三个数（或被多条总结行污染）：%s" % RD_LINE[:160])
if len(re.findall(u"Executed \\d+ tests?, with", chain[chain.find(u"### SWIFT_SUMMARY"):
                                                 chain.find(u"### SWIFT_LEGS")])) != 1:
    die(u"SWIFT_SUMMARY 那一节不止一条总结行 ⇒ 不知道哪一条是全量卷")
FULL_LINE = u"Executed %s tests, with %s skipped and %s failures" % _sum[-1]
FULL_FAILS = int(_sum[-1][2])
LOAD_RED = (re.findall(r"(?m)^R314_LOAD_RED .+$", chain) or [u""])[-1]
_hits = re.findall(u"R314_LOAD_RED 命中=(\\d+)", LOAD_RED)
LOAD_HITS = int(_hits[-1]) if _hits else -1
if LOAD_HITS < 0:
    die(u"负载红那一格没读数：%s" % LOAD_RED[:120])
if FULL_FAILS and LOAD_HITS == 0:
    die(u"全量卷有 %d 朵红，而 `testImageComparisonCostStaysBounded` 那一格命中=0 ⇒ 红必须有名"
        % FULL_FAILS)
if not FULL_FAILS and LOAD_HITS:
    die(u"全量卷 0 失败却还登记着 %d 条负载红 ⇒ 那一格的正文与读数不同源" % LOAD_HITS)

_j = re.search(u"UICAPTURE_TESTS ran=(\\d+) failed=(\\d+)", chain)
if not _j:
    die(u"读不到捕获卷的 ran/failed ⇒ 那一格不许写")
JUDGE_RUN, JUDGE_FAIL = _j.group(1), _j.group(2)
if JUDGE_FAIL != u"0":
    die(u"捕获卷 UICaptureTests 是 %s 朵红 ⇒ 拒绝出账" % JUDGE_FAIL)

BASE_ROWS = chain[chain.find(u"### FRAME_BASELINE"):chain.find(u"### SWIFT_SUMMARY")]
BASE_LINE = u" ".join(re.findall(u"FRAME_BASELINE_(?:UPDATED|COMPARED|CHANGED|MISSING|ADDED)=\\d+", BASE_ROWS))
if u"FRAME_BASELINE_COMPARED=176" not in BASE_ROWS or u"FRAME_BASELINE_CHANGED=0" not in BASE_ROWS:
    die(u"帧基线对账没给出 COMPARED=176 / CHANGED=0 ⇒ 新增那两张帧没有同一笔基线证人：%s"
        % BASE_ROWS.strip()[:200])
INSTALL_LINE = (re.findall(r"(?m)^INSTALL_RESULT=.+$", chain) or [u"没读到换装结论行"])[-1]
RUNNER_LINE = (re.findall(r"(?m)^NEEDLE_RANGE .+$", chain) or [u"没读到 366 探针现读"])[-1]

pre_line = re.findall(r"NEEDLE_PRECHECK tables=(\d+) covered=(\d+) arms=(\d+) bad=(\d+)", chain)
if not pre_line:
    die(u"NEEDLE_PRECHECK 没读到 ⇒ 预检那条腿没跑")
TABLES_N, COVERED, PRE_ARMS, PRE_BAD = (int(x) for x in pre_line[-1])
if PRE_BAD:
    die(u"针预检 bad=%d ⇒ 有 needle 在册上腐烂" % PRE_BAD)
reg_line = re.findall(r"ARM_TOTAL files=(\d+) arms=(\d+) dupes=(\d+) repeats=(\d+)", chain)
if not reg_line:
    die(u"ARM_TOTAL 没读到 ⇒ 在册刀数不许手抄")
ARM_FILES, ARM_REG, ARM_DUPES, ARM_REPEATS = (int(x) for x in reg_line[-1])
if ARM_DUPES or ARM_REPEATS:
    die(u"名册报 dupes=%d repeats=%d ⇒ 先修跨表撞号" % (ARM_DUPES, ARM_REPEATS))
roster = re.findall(r"TABLE_ROSTER registered=(\d+) unregistered_with_arms=(\d+) hidden_arms=(\d+)", chain)
HID_TABLES, HID_ARMS = (int(roster[-1][1]), int(roster[-1][2])) if roster else (0, 0)

ha_out, ha_rc = sh([sys.executable, os.path.join(ROOT, "scripts", "hidden_arms.py")])
HA_LINE = (re.findall(r"(?m)^HIDDEN_ARMS .+$", ha_out) or [u""])[-1]
if u"处置=ok" not in HA_LINE:
    die(u"腐烂针那把尺自己没签（rc=%d）：%s" % (ha_rc, HA_LINE[:160]))
ROT_NOW = (re.findall(r"rot=(\d+)", HA_LINE) or [u""])[-1]
OPAQUE_NOW = (re.findall(r"抽不出=(\d+)", HA_LINE) or [u"", u""])[-1]
JUDGED_NOW = (re.findall(r"可判=(\d+)", HA_LINE) or [u""])[-1]
DECLARED_TBL = int((re.findall(u"已声明表=(\\d+)", HA_LINE) or [u"0"])[-1])
REMAIN_TABLES = int(HID_TABLES) - DECLARED_TBL if str(HID_TABLES).isdigit() else 0
TABLES_SCANNED = (re.findall(r"表=(\d+)", HA_LINE) or [u""])[-1]

st_out, st_rc = sh([sys.executable, STREAK, u"--streak-for", s(ROUND)])
STREAK_N = (re.findall(r"streak=(\d+)", st_out) or [u""])[-1]
if st_rc != 0 or not STREAK_N:
    die(u"product_streak 读不到（rc=%d）：%s" % (st_rc, st_out.strip()[-160:]))
LASTSHA = (re.findall(r"last=(\w+)", st_out) or [u""])[-1]
LASTROUND = (re.findall(r"last_round=(\d+)", st_out) or [u""])[-1]
prev_out, prev_rc = sh([sys.executable, STREAK, u"--streak-for", s(PREV_ROUND)])
PREV_STREAK = (re.findall(r"streak=(\d+)", prev_out) or [u""])[-1]
if prev_rc != 0 or not PREV_STREAK:
    die(u"上一轮的产品面轮数读不到（rc=%d）" % prev_rc)

ci, _ = sh([sys.executable, os.path.join(ROOT, "scripts", "ci_read.py"), u"latest"])
CI = ci.strip().replace(u"\n", u" ")
if u"RUN=" not in CI:
    die(u"⓪ 的 CI 配对没读到（ci_read latest 给的是「%s」）" % CI[:80])

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
BLNEW, BLNEW2, BLNEW3 = BL_MAX + 1, BL_MAX + 2, BL_MAX + 3
if u"**368. " not in bl:
    die(u"BACKLOG 368 不在盘上 ⇒ 本轮的追记无处可挂")

SUBS = {u"@ROUND@": ROUND, u"@RTAG@": R_TAG, u"@RPREVTAG@": PREV_TAG, u"@RNEXT@": R_NEXT,
        u"@RDN@": RDN, u"@TODAY@": TODAY, u"@UA@": UA, u"@UB@": UB, u"@UC@": UC, u"@UD@": UD,
        u"@DN@": DN, u"@BLNEW@": BLNEW, u"@BLNEW2@": BLNEW2, u"@BLNEW3@": BLNEW3,
        u"@BLMAX@": BLNEW3, u"@BLMINUS@": BL_MAX,
        u"@BATT@": pre, u"@SKIP@": pre_skip, u"@STREAK@": STREAK_N, u"@PREVSTREAK@": PREV_STREAK,
        u"@LASTSHA@": LASTSHA, u"@LASTROUND@": LASTROUND, u"@CI@": CI, u"@NOFILES@": len(others),
        u"@JUDGERUN@": JUDGE_RUN, u"@JUDGEFAIL@": JUDGE_FAIL, u"@WARN@": warn[-1],
        u"@PREBAD@": PRE_BAD, u"@TABLES@": TABLES_N, u"@COVERED@": COVERED,
        u"@ARMREG@": ARM_REG, u"@ARMFILES@": ARM_FILES, u"@FRAMES@": FRAMES,
        u"@RDLINE@": RD_LINE, u"@HALINE@": HA_LINE, u"@ROT@": ROT_NOW, u"@OPAQUE@": OPAQUE_NOW,
        u"@JUDGED@": JUDGED_NOW, u"@TSCANNED@": TABLES_SCANNED,
        u"@HIDTABLES@": HID_TABLES, u"@HIDARMS@": HID_ARMS,
        u"@HIDTBL@": DECLARED_TBL, u"@HIDTBL2@": REMAIN_TABLES,
        u"@PROBE@": RUNNER_LINE, u"@RUNNER@": RUNNER_LINE, u"@FULL@": FULL_LINE,
        u"@CAP@": CAP2_LINE, u"@BASE@": BASE_LINE, u"@INSTALL@": INSTALL_LINE,
        u"@KNIFESUM@": KNIFE_SUM, u"@INKPAIR@": INK_PAIR}
EYE = fill(EYE, SUBS)
SUBS[u"@EYE@"] = EYE
SUBS[u"@EYE_SHORT@"] = EYE.split(u"⇒")[0].strip()

# ---------------------------------------------------------------- 七本正文（外置）
if not os.path.exists(BODIES):
    die(u"正文文件 %s 不在盘上" % BODIES)
ns = {}
exec(compile(rd(BODIES), BODIES, u"exec"), ns)
for k in (u"UI_NEW", u"IT_NEW", u"DEC_NEW", u"BL_368", u"BL_NEW", u"BL_NEW2", u"BL_NEW3",
          u"CH_NEW", u"ST_NEW"):
    if k not in ns:
        die(u"正文缺 %s" % k)

# ---------------------------------------------------------------- 组装与落盘
orig = {k: rd(v) for k, v in FILES.items()}
for key, marker in ((u"UI", u"## 第 %d 轮" % ROUND), (u"IT", u"## Round %d ·" % RDN),
                    (u"ST", u"## %s 状态（" % R_TAG)):
    if marker in orig[key]:
        die(u"%s 里已经有本轮那一节 ⇒ 生成器不许重跑第二遍" % key)

texts = {u"UI": fill(ns[u"UI_NEW"], SUBS), u"IT": fill(ns[u"IT_NEW"], SUBS),
         u"DEC": fill(ns[u"DEC_NEW"], SUBS), u"BL368": fill(ns[u"BL_368"], SUBS),
         u"BLNEW": fill(ns[u"BL_NEW"], SUBS), u"BLNEW2": fill(ns[u"BL_NEW2"], SUBS),
         u"BLNEW3": fill(ns[u"BL_NEW3"], SUBS), u"CH": fill(ns[u"CH_NEW"], SUBS),
         u"ST": fill(ns[u"ST_NEW"], SUBS)}
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
    die(u"七维表不是恰好 7 行 ⇒ 曲线仪器会拒绝推导")

new_dec = orig[u"DEC"].rstrip(u"\n") + u"\n\n" + texts[u"DEC"].rstrip(u"\n") + u"\n"


def append_into_item(text, header_prefix, note, label):
    lines = text.split(u"\n")
    hits = [i for i, l in enumerate(lines) if l.startswith(header_prefix)]
    if len(hits) != 1:
        die(u"%s 的条目头命中 %d 行（要恰好 1）" % (label, len(hits)))
    h = hits[0]
    nxt = [i for i in range(h + 1, len(lines)) if re.match(u"\\*\\*\\d{3}\\. ", lines[i])]
    k = nxt[0] if nxt else len(lines)
    while lines[k - 1].strip() == u"":
        k -= 1
    head = u"\n".join(lines[:k])
    if not head.endswith(u"\n"):
        head += u"\n"
    out = head + note.rstrip(u"\n") + u"\n" + u"\n".join(lines[k:]).lstrip(u"\n")
    if not (0 <= out.find(header_prefix) < out.find(note.split(u"\n")[0].strip())):
        die(u"%s 的追记落点不对" % label)
    return out


new_bl = append_into_item(orig[u"BL"], u"**368. ", texts[u"BL368"], u"368")
for key in (u"BLNEW", u"BLNEW2", u"BLNEW3"):
    n = SUBS[u"@%s@" % key]
    if re.search(u"(?m)^\\*\\*%d\\. " % n, new_bl):
        die(u"BACKLOG %d 已存在 ⇒ 不许开第二张同题单，去追记原条目" % n)
    new_bl = new_bl.rstrip(u"\n") + u"\n\n" + texts[key].rstrip(u"\n") + u"\n"
if len(re.findall(u"(?m)^\\*\\*\\d{3}\\. ", new_bl)) != \
        len(re.findall(u"(?m)^\\*\\*\\d{3}\\. ", orig[u"BL"])) + 3:
    die(u"BACKLOG 条目头数量不是「原数 +3」⇒ 三张新单没落成三条")

new_ch = once(orig[u"CH"], u"## [Unreleased]\n\n", u"## [Unreleased]\n\n" + texts[u"CH"],
              u"CHANGELOG [Unreleased]")
if sum(1 for line in new_ch.split(u"\n") if line.strip() == u"## [Unreleased]") != 1:
    die(u"CHANGELOG 的 [Unreleased] 标题行不再是恰好 1 行")

new_st = once(orig[u"ST"], u"## %s 状态（" % PREV_TAG,
              texts[u"ST"] + u"## %s 状态（" % PREV_TAG, u"STATE 轮换")
if u"## %s 状态（" % PREV_TAG not in new_st or u"## %s 状态（" % R_TAG not in new_st:
    die(u"STATE 轮换后上一轮的标记没了")

fr = orig[u"FR"]
if len(re.findall(u"U-31 … U-\\d+（R\\d+ 现读抬到最新一节）", fr)) != 1:
    die(u"§1 的 U 那一格锚点命中不是 1")
fr = re.sub(u"U-31 … U-\\d+（R\\d+ 现读抬到最新一节）",
            u"U-31 … U-%d（%s 现读抬到最新一节）" % (UD, R_TAG), fr, count=1)
fr = once(fr, u"完整名单以 `AGENT_STATE.md` 的 %s 节 ② 为准" % PREV_TAG,
          u"完整名单以 `AGENT_STATE.md` 的 %s 节 ② 为准" % R_TAG, u"§13 仍开指针")

new = {u"UI": new_ui, u"IT": new_it, u"DEC": new_dec, u"BL": new_bl,
       u"CH": new_ch, u"ST": new_st, u"FR": fr}
for key in new:
    if key != u"FR" and len(new[key]) <= len(orig[key]):
        die(u"%s 写后不比写前长 ⇒ 可能是替换而不是插入" % key)
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
        sys.stderr.write(u"R314_CRASH_RESTORED 未捕获异常 ⇒ 七本已整体还原\n")


atexit.register(_crash_guard)

txt = rd(FILES[u"FR"])
out, crc = sh([sys.executable, CURVE])
rounds_after = (re.findall(r"^ROUNDS=(\d+)", out, re.M) or [u""])[-1]
last_round = (re.findall(r"^PHASE2 n=\d+ rounds=9\.\.(\d+)", out, re.M) or [u""])[-1]
tail = (re.findall(r"^SCORES_BY_ROUND (.+)$", out, re.M) or [u""])[-1]
if not rounds_after or not last_round or not tail:
    die(u"写盘后曲线尺没给出 ROUNDS= / rounds=9..N / SCORES_BY_ROUND（rc=%d）" % crc)
lines = txt.split(u"\n")
m = re.search(u"R9–R(\\d+)，(\\d+) 节自评", lines[0])
if not m or lines[0].count(u"R9–R") != 1:
    die(u"报告标题那一行没找到 `R9–R<NNN>，<NNN> 节自评` ⇒ 不敢整行改写")
lines[0] = lines[0][:m.start()] + u"R9–R%s，%s 节自评" % (last_round, rounds_after) + lines[0][m.end():]
body = u"\n".join(lines)

prod_cell = (u"- **产品面（这一节最该被读的部分）**：本轮产品文件 0 个（判据轮：改动面 %d 个文件，"
             u"其中 %d 份 Swift 捕获夹具、其余在 `docs/` 与 `.scratch/`），产品面连续零改动轮数 = **%s**"
             u"（唯一取数口 `python3 scripts/product_streak.py --streak-for %s`，as-of 第 %s 轮的最后一笔"
             u"产品提交是 %s = 第 %s 轮；上一轮那一格是 %s）。看图腿 RUN：重捕 %s 张、帧基线 %s"
             u"（新增两张 empty 帧，**同一笔 update**）；换装 %s。本轮最该被读的一格是自曝："
             u"补的那一臂与既有 `settings-stats` 两档 md5 全等 ⇒ 空态的真入口臂早就存在，"
             u"净产出是那一对能判产品的数（底部留白 0.533 vs 0.252）与新开的产品侧缺席单 %s。"
             % (1 + len(others) + len(swift_files), len(swift_files), STREAK_N, ROUND, ROUND,
                LASTSHA, LASTROUND, PREV_STREAK, FRAMES, BASE_LINE, INSTALL_LINE, BLNEW3))
scale_cell = (u"- **判据与门的规模**：脚本电池现读 **Ran %s**（写盘后同数），"
              u"变异臂在册 **%s** 把 / %s 张表（预检 tables=%s covered=%s bad=%s，"
              u"未登记表 %s 张 / 隐藏臂 %s 把 ⇒ 364）；腐烂针尺现读 `%s`；"
              u"U 定义行 **%s 条**、最大 **U-%s**；决定台账最大 **D-%s**，BACKLOG 最大 **%s**"
              u"（本轮追记 %s、新开 %s/%s/%s）"
              % (pre, ARM_REG, ARM_FILES, TABLES_N, COVERED, PRE_BAD, HID_TABLES, HID_ARMS, HA_LINE,
                 len(re.findall(u"(?m)^- \\*\\*U-(\\d{3,4})[：(]", new_ui)), UD, DN, BLNEW3,
                 BL_MAX, BLNEW, BLNEW2, BLNEW3))
where_cell = (u"- **走到哪了**：阶段二累计 `## Round` 节 **%s** 节，最新一节是 **Round %s**；"
              u"自评曲线按轮现读 %s（现读 `curve_from_ledger.py`）。派生分连续多轮低于 90 "
              u"⇒ 按目标继续修，不收口。" % (rounds_after, last_round, tail))
for label, cell in ((u"产品面（这一节最该被读的部分）", prod_cell),
                    (u"判据与门的规模", scale_cell), (u"走到哪了", where_cell)):
    parts = body.split(u"\n")
    hits = [i for i, l in enumerate(parts) if l.startswith(u"- **%s**：" % label)]
    if len(hits) != 1:
        die(u"§13 的「%s」那一格命中 %d 行（要恰好 1）" % (label, len(hits)))
    parts[hits[0]] = fill(cell, SUBS)
    body = u"\n".join(parts)

gout, _ = sh([u"git", u"log", u"-40", u"--format=%h\x1f%s", u"--",
              os.path.join("ClipboardHistory", "Sources")])
src_rows = []
for line in gout.splitlines():
    if u"\x1f" not in line:
        continue
    sha_, subj_ = line.split(u"\x1f", 1)
    mb = re.match(u"^R(\\d+)", subj_.strip())
    src_rows.append((sha_.strip(), int(mb.group(1)) if mb else None, subj_.strip()))
picked = [r for r in src_rows if r[1] is not None and r[1] <= int(R_TAG[1:])]
if not picked:
    die(u"标签 ≤ %s 的源码提交一笔都没有 ⇒ 那一格不许拿「此刻最新」凑数" % R_TAG)
live_sha, live_src_round, _ = picked[0]
older = [r for r in src_rows if r[0] != live_sha and r[1] is not None]
prev_txt = (u"上一笔动 `Sources/` 的是 R%d（`%s`）。" % (older[0][1], older[0][0])) if older else u""
src_cell = (u"| 最后一次动到 `Sources/` 的轮次 | **R%d**（commit `%s`）—— 本轮是判据轮"
            u"（`Sources/` 0 个文件、Swift 捕获夹具 %d 份、其余 %d 个在 `docs/` 与 `.scratch/`）；"
            u"这一格登记的是仓库里**最近一笔动过源码的提交**，"
            u"改了什么以 `AGENT_UI_AUDIT.md` 里 R%d 那一节为准（这一格只登记号与数，不复述结论）。%s|"
            % (live_src_round, live_sha, len(swift_files), len(others), live_src_round, prev_txt))
parts = body.split(u"\n")
hits = [i for i, l in enumerate(parts) if l.startswith(u"| 最后一次动到 `Sources/` 的轮次 |")]
if len(hits) != 1:
    die(u"报告「最后一次动到 Sources/」那一格命中 %d 行" % len(hits))
parts[hits[0]] = src_cell
body = u"\n".join(parts)
if STRAY_RX.search(body):
    die(u"报告刷新后还有没替换的占位符：%s" % STRAY_RX.findall(body)[:4])
wr(FILES[u"FR"], body)
rf, rfc = sh([sys.executable, os.path.join(ROOT, ".scratch", "motion-audit-2",
                                           "refresh_report_section1.py")])
if rfc != 0 or u"REFUSED" in rf:
    die(u"§1 那一格的刷新器没签（rc=%d）：%s" % (rfc, rf.strip()[-200:]))

post, post_skip = battery(u"写盘后", u"/tmp/r314_battery_post.log")
if (post, post_skip) != (pre, pre_skip):
    die(u"电池计数变了（%s/%s → %s/%s）" % (pre, pre_skip, post, post_skip))
ck, crc = sh([sys.executable, STREAK, u"--check"])
if crc != 0:
    die(u"353 的门不认这版台账：" + (ck + u"\n").strip()[-400:])
cv2, _ = sh([sys.executable, CURVE])
if (re.findall(r"^GAPS=(\S+)", cv2, re.M) or [u""])[-1] != u"none":
    die(u"写盘后曲线尺报缺口 ⇒ 升序台账被插在中间")
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
print(u"LEDGERS_R314 OK batt=Ran " + post + u" (skipped=" + post_skip + u") streak=" + STREAK_N
      + u"(上一轮 " + PREV_STREAK + u") 改动面=" + s(1 + len(others) + len(swift_files))
      + u" 捕获1红=" + s(CAP1_REDS) + u" 捕获2红=" + s(CAP2_REDS)
      + u" 在册=" + s(ARM_REG) + u"/" + s(ARM_FILES) + u"表 rot=" + s(ROT_NOW)
      + u" 抽不出=" + s(OPAQUE_NOW) + u" 可判=" + s(JUDGED_NOW)
      + u" U=" + s(UA) + u".." + s(UD) + u" D=" + s(DN) + u" BL=" + s(BLNEW) + u".." + s(BLNEW3)
      + u" 捕获卷=" + s(JUDGE_RUN) + u" 全量=" + FULL_LINE + u" 帧=" + FRAMES
      + u" derived(Round " + s(RDN) + u")=" + s(DERIVED2)
      + u" report尾轮=Round " + s(last_round) + u" 节数=" + s(rounds_after))
