#!/usr/bin/env python3
# -*- coding: utf-8 -*-
u"""R336 的台账生成器（第 335 轮 / Round 333 · 402 用现读关掉 + 401 落地成产品修法 · 产品 1 文件）。

数字全部从**当场跑**的日志里解析；锚点整行；所有锚点在任何写盘之前统一验一遍
（R335 那一轮两次半批已写，教训写进了 Skill）；证人日志缺失即 die，不许沿用上一轮的数。

  /tmp/r336_rv/ROUND_VERIFY.log   —— build 告警 / 全量卷 / 重捕帧 / 帧基线 / dmg+换装
  /tmp/r336_rv/capture.log        —— HTML_INKREAD 四行 / HTML_PAIR_PROOF 两行 / 捕获卷 Executed
  /tmp/r336_html.log              —— MD_RENDER_COST / HTML_ALT / HTML_SANITIZE / 判据卷 Executed
  /tmp/r336_t_r336.log            —— 本轮三把刀
  /tmp/r336_t_r335.log            —— 上一轮那十一把的**回归**（本轮动了同一个文件）

跑法：PYTHONUTF8=1 python3 .scratch/motion-audit-2/ledgers_r336.py
"""
import io
import os
import re
import subprocess
import sys

ROOT = u"/Users/wangziyi/Codex_Project0"
AUD = os.path.join(ROOT, u"AGENT_UI_AUDIT.md")
ITE = os.path.join(ROOT, u"AGENT_VISUAL_ITERATION.md")
DEC = os.path.join(ROOT, u"AGENT_DECISIONS.md")
BLG = os.path.join(ROOT, u"AGENT_BACKLOG.md")
CHG = os.path.join(ROOT, u"CHANGELOG.md")
STA = os.path.join(ROOT, u"AGENT_STATE.md")
FRA = os.path.join(ROOT, u"AGENT_FINAL_REPORT.md")
STREAK = os.path.join(ROOT, u"scripts", u"product_streak.py")
CURVE = os.path.join(ROOT, u".scratch", u"motion-audit-2", u"curve_from_ledger.py")
PRECHK = os.path.join(ROOT, u".scratch", u"motion-audit-2", u"mutate_needle_precheck.py")
GATE = os.path.join(ROOT, u"scripts", u"motion_surface_gate.py")
FRESH = os.path.join(ROOT, u".scratch", u"motion-audit-2", u"refresh_report_section1.py")
SRCCELL = os.path.join(ROOT, u"scripts", u"report_sources_cell.py")
ROWS = os.path.join(ROOT, u".scratch", u"motion-audit-2", u"ledger_rows.py")

RV_DIR = u"/tmp/r336c_rv"
BEFORE_FRAMES = u"/tmp/r336b_rv/frames"   # 规则 ④ 之前的那一跑：行距那两格的"修之前"证人
RULER = os.path.join(ROOT, u".scratch", u"motion-audit-2", u"line_gap_ruler.py")
GAP_BOX = [u"40", u"1240", u"110", u"620"]   # px（@2x）：正文列，右半边住着动作条
ROSTER_OLD_LOG = u"/tmp/r336_rv/full.log"   # 登记前那一跑：名册那三朵红的证人
ROSTER_NEW_LOG = RV_DIR + u"/full.log"
RV_LOG = RV_DIR + u"/ROUND_VERIFY.log"
CAP_LOG = RV_DIR + u"/capture.log"
HTML_LOG = u"/tmp/r336_html.log"
TABLES = [(u"mutate_r336", u"/tmp/r336_t_r336.log", u"5/5"),
          (u"mutate_r335", u"/tmp/r336_t_r335.log", u"11/11")]

ENV = dict(os.environ)
ENV[u"PYTHONUTF8"] = u"1"
ENV[u"PYTHONDONTWRITEBYTECODE"] = u"1"

ROUND = 336
AUDIT_N = 335
ITER_N = 333
DATE = u"2026-10-25"
UA, UB, UC, UD, UE, UF, UG = 1128, 1129, 1130, 1131, 1132, 1133, 1134
UH, UI2 = 1135, 1136
UMAX = UI2
D1 = 332
B_LEAK = 404           # 属性值里含 `>` ⇒ 标签正则先截断，剩下的属性文字漏进正文
B_TITLE = 405          # 回顾时量到的：同一轮的两笔提交在标题里给出两个「产品 K 文件」
B_LIST = 406           # 现状钉：渲染器不给 <ul> 下边距 ⇒ 列表后面那一段没有段前距（行距尺量到的）
B_ALT = 401            # 本轮结案（图被撤、说明留下）
B_MDBUDGET = 402       # 本轮结案（现读关掉：不需要上限）
B_EMPH = 400           # 仍开：CJK 强调在像素层没量
# 七维度自评的七个数（ITERATION 那张表「分/满分」列必须与它一致，写盘后有一格读回来对账）
SEVEN = [14, 14, 14, 13, 13, 14, 13]   # 下半场：看图腿第一次给出一把可数的行距尺 + 一次 before/after
SEVEN_MAX = 15 * 7
ARMS_NEW = (u"M984", u"M985", u"M986", u"M987", u"M988")

WRITTEN = []


def rd(path):
    return io.open(path, encoding=u"utf-8").read()


def wr(path, text):
    io.open(path, u"w", encoding=u"utf-8").write(text)
    WRITTEN.append(path)


def sh(cmd, cwd=None):
    p = subprocess.run(cmd, cwd=cwd or ROOT, env=ENV,
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return p.stdout.decode(u"utf-8", u"replace"), p.returncode


def die(msg):
    print(u"LEDGERS_R336_DIED " + msg)
    for p in WRITTEN:
        print(u"  已写盘：" + p)
    sys.exit(1)


def once(text, anchor, replacement):
    n = text.count(anchor)
    if n != 1:
        die(u"锚点命中 %d 次（要 1 次）：%s" % (n, anchor[:80]))
    return text.replace(anchor, replacement)


def s(v):
    return str(v)


def require(path):
    if not os.path.exists(path):
        die(u"证人日志不在盘上：" + path + u" ⇒ 那一格的数没处解析，不许手填")
    return rd(path)


def num(line_text, key, where=u""):
    m = re.search(re.escape(key) + u"([-+0-9.%…未空无/]+)", line_text)
    if not m:
        die(u"读数行里缺 " + key + u" " + where + u"：" + line_text[:200])
    return m.group(1)


def tok(line_text, key, where=u""):
    m = re.search(re.escape(key) + u"(\\S+)", line_text)
    if not m:
        die(u"读数行里缺 " + key + u" " + where + u"：" + line_text[:200])
    return m.group(1)


def one(lines, pattern, where):
    got = [l for l in lines if re.match(pattern, l)]
    if not got:
        die(u"日志里读不到 " + where + u"（模式 " + pattern + u"）")
    return got[-1]


BS_N = u"\n"   # 单独一个常量：这一段要写进**另一份源文件**，反斜杠在这里求值就没了
RE_ROSTER_NAMES = u'\("(\[[^)]*MD_RENDER_COST[^)]*\])"\) is not equal to \("(\[[^)]*\])"\)'
RE_ROSTER_ROWS = u'\("(\d+)"\) is not equal to \("(\d+)"\) - PerfBudgetTests'
RE_ROSTER_TOTAL = u'\("(\d+)"\) is not equal to \("(\d+)"\) - 这张名册'
# ──  1. 四腿读数 ─────────────────────────────────────────────────────────────
rv = require(RV_LOG)
line = one(rv.splitlines(), u"ROUND_VERIFY ", u"ROUND_VERIFY 汇总行")
line = line.replace(u"ROUND_VERIFY ", u"", 1)
RV = dict(re.findall(r"(\w+)=([^\s]+)", line))
for k in (u"build_warnings", u"swift_executed", u"swift_skipped", u"swift_failures",
          u"frames", u"baseline_compared", u"baseline_changed", u"baseline_missing",
          u"dmg", u"installed_version"):
    if k not in RV:
        die(u"ROUND_VERIFY 那一行缺键 %s：%s" % (k, line))
if RV[u"build_warnings"] != u"0" or RV[u"swift_failures"] != u"0" or RV[u"baseline_changed"] != u"0":
    die(u"四腿没全签，不落盘：" + line)
FRAME_N = RV[u"frames"]
FULL_RUN, FULL_SKIP, FULL_FAIL = RV[u"swift_executed"], RV[u"swift_skipped"], RV[u"swift_failures"]

# ──  1b. 名册那一朵红（登记之前的那一跑）─────────────────────────────────────────
# 三行断言都在**旧日志**里：那一跑是"我新增了读数而没登记名册"时跑的，它就是这一格的证人。
# 新日志里这一朵红必须消失 —— 否则"我修了"这句话没有出处。
old_roster, orc = sh([u"grep", u"-a", u"-m", u"3",
                      u"testProbeFilePrintReadingsAreARosterNotACount] : XCTAssertEqual failed",
                      ROSTER_OLD_LOG])
if orc != 0 or old_roster.count(BS_N) < 2:
    die(u"旧日志里读不到名册那三行（grep 退出码 %d）：%s" % (orc, old_roster[:200]))
_m = re.search(RE_ROSTER_NAMES, old_roster)
if not _m:
    die(u"名册那三行里读不到「标记名单不符」那一行：" + old_roster[:300])
ROSTER_MEASURED, ROSTER_REGISTERED_OLD = _m.group(1), _m.group(2)
_r = re.search(RE_ROSTER_ROWS, old_roster)
if not _r:
    die(u"读不到 PerfBudgetTests 的行数那行：" + old_roster[:300])
ROSTER_ROWS = u"%s/%s" % (_r.group(1), _r.group(2))
_t = re.search(RE_ROSTER_TOTAL, old_roster)
if not _t:
    die(u"读不到名册总数那行：" + old_roster[:300])
ROSTER_TOTAL = u"%s/%s" % (_t.group(1), _t.group(2))
new_roster, nrc = sh([u"grep", u"-a", u"-c",
                      u"testProbeFilePrintReadingsAreARosterNotACount] failed", ROSTER_NEW_LOG])
if new_roster.strip() != u"0":
    die(u"新日志里这一朵红还在（grep -c = %s）⇒ 登记没生效，账不能按修好写" % new_roster.strip())

# ──  2. 捕获卷：像素那一格 + 两态相减 ────────────────────────────────────────
cap = require(CAP_LOG)
cl = cap.splitlines()
ir_dh = one(cl, u"HTML_INKREAD dark 夹具=html-rendered", u"HTML_INKREAD 暗档 HTML")
ir_lh = one(cl, u"HTML_INKREAD light 夹具=html-rendered", u"HTML_INKREAD 亮档 HTML")
D_RATIO, D_WRONG = num(ir_dh, u"比="), num(ir_dh, u"反侧=")
L_RATIO, L_WRONG = num(ir_lh, u"比="), num(ir_lh, u"反侧=")
D_COV, L_COV = num(ir_dh, u"覆盖率="), num(ir_lh, u"覆盖率=")
if u"0" != D_WRONG or u"0" != L_WRONG:
    die(u"反侧不再是 0（暗 %s / 亮 %s）⇒ alt 那一步把墨带坏了" % (D_WRONG, L_WRONG))
pair_d = one(cl, u"HTML_PAIR_PROOF dark", u"HTML_PAIR_PROOF 暗档")
pair_l = one(cl, u"HTML_PAIR_PROOF light", u"HTML_PAIR_PROOF 亮档")
PAIR_D, PAIR_L = num(pair_d, u"千分比="), num(pair_l, u"千分比=")
CAP_RUN = (re.findall(r"Executed (\d+) tests", cap) or [None])[-1]
CAP_SKIP = (re.findall(r"with (\d+) tests skipped", cap) or [u"0"])[-1]
CAP_FAIL = (re.findall(r"with \d+ tests skipped and (\d+) failures", cap) or [None])[-1]
if CAP_RUN is None or CAP_FAIL is None or CAP_FAIL != u"0":
    die(u"捕获卷不签（Executed=%s failures=%s）" % (CAP_RUN, CAP_FAIL))

# ──  3. 判据卷：Markdown 耗时那一格 + alt 那一格 ─────────────────────────────
ht = require(HTML_LOG)
hl = ht.splitlines()
cost = one(hl, u"MD_RENDER_COST ", u"MD_RENDER_COST")
alt = one(hl, u"HTML_ALT ", u"HTML_ALT")
sani = one(hl, u"HTML_SANITIZE ", u"HTML_SANITIZE")
MD_SMALL = num(cost, u"16k=", u"（ms）")
MD_BIG = num(cost, u"cap=", u"（ms）")
MD_CAP_CHARS = num(cost, u"cap字符=")
MD_MARGINAL = num(cost, u"边际=")
MD_FIXED = num(cost, u"固定=")
MD_MEAN_SLOPE = num(cost, u"平均=")
MD_BUDGET = num(cost, u"预算=")
MD_VERDICT = tok(cost, u"判定=")
ALT_KEPT = tok(alt, u"有alt保留=")
ALT_SILENT = tok(alt, u"空alt静默=")
ALT_NODESC = tok(alt, u"无alt删净=")
ALT_ANGLE = tok(alt, u"尖括号剥掉=")
SANI_CONSTRUCTS, SANI_RESIDUE = num(sani, u"构造="), num(sani, u"残留=")
HTML_RUN = (re.findall(r"Executed (\d+) tests", ht) or [None])[-1]
HTML_FAIL = (re.findall(r"with (\d+) failures", ht) or [None])[-1]
if HTML_RUN is None or HTML_FAIL != u"0":
    die(u"判据卷不签（Executed=%s failures=%s）" % (HTML_RUN, HTML_FAIL))
for flag, where in ((ALT_KEPT, u"有alt保留"), (ALT_SILENT, u"空alt静默"),
                    (ALT_NODESC, u"无alt删净"), (ALT_ANGLE, u"尖括号剥掉")):
    if flag != u"true":
        die(u"alt 那一族的 %s 不是 true（读到 %s）⇒ 产品没修好，账不能按修好写" % (where, flag))
if MD_VERDICT != u"在预算内":
    die(u"Markdown 那条在 cap 上超了预算（判定=%s）⇒ 本轮得先装上限再落账" % MD_VERDICT)
MD_CAP_KB = s(round(int(MD_CAP_CHARS) / 1024.0, 1))

# 读数族：本轮新出现的 `MD_RENDER_COST` 必须接进 §8 的搬运名单（它由判据卷打印）
NEW_ROWS = [l for l in (cap + u"\n" + ht).splitlines()
            if l.startswith(u"HTML_") or l.startswith(u"MD_RENDER_COST")]
NEW_NAMES = s(len(set(l.split(u" ")[0] for l in NEW_ROWS)))
NEW_N = s(len(NEW_ROWS))

# ──  3b. 下半场：alt 那句**自成一段**（结构 + 像素 + before/after）─────────────
ab = one(hl, u"HTML_ALT_BLOCK ", u"HTML_ALT_BLOCK")
BLOCK_STANDALONE, BLOCK_INLINE = tok(ab, u"独占成段="), tok(ab, u"句中不包=")
BLOCK_SAME_SENTENCE = tok(ab, u"句中同句=")
for flag, where in ((BLOCK_STANDALONE, u"独占成段"), (BLOCK_INLINE, u"句中不包"),
                    (BLOCK_SAME_SENTENCE, u"句中同句")):
    if flag != u"true":
        die(u"规则 ④ 的 %s 不是 true（读到 %s）⇒ 产品没修好，账不能按修好写" % (where, flag))

# 像素那一半：两档各一行，期望"紧挨 2 处"（① 列表内部；② 列表→下一块 = BACKLOG 406 的现状）。
# 这一格刻意**不**由"能不能过"来定数：它是从夹具的分块结构推出来的，推导写在判据的注释里。
def para_row(lines, tag):
    row = one(lines, u"HTML_ALT_PARA " + tag + u" ", u"HTML_ALT_PARA " + tag)
    return (num(row, u"带="), num(row, u"紧挨="), num(row, u"行内距="), num(row, u"段距="))

PD_BANDS, PD_TIGHT, PD_LINE, PD_PARA = para_row(cl, u"dark")
PL_BANDS, PL_TIGHT, PL_LINE, PL_PARA = para_row(cl, u"light")
if PD_TIGHT != u"2" or PL_TIGHT != u"2":
    die(u"紧挨的处数不是 2（暗=%s 亮=%s）⇒ 要么规则 ④ 漂了，要么 406 那条现状被修掉了；"
        u"两种都要先去看是哪一种，不许把期望挪到能过的地方" % (PD_TIGHT, PL_TIGHT))

# before/after：同一把尺跑两次（修之前的帧在 r336b，修之后在 r336c），数"紧挨"的处数。
def ruler_tight(frames_dir, tag):
    frame = os.path.join(frames_dir, u"detail-html-rendered-720x520-" + tag + u".png")
    if not os.path.exists(frame):
        die(u"行距尺的帧不在盘上：" + frame)
    out, rc = sh([sys.executable, RULER, frame] + GAP_BOX)
    steps = (re.findall(u"(?m)^LINE_GAP_STEPS_pt (.*)$", out) or [None])[-1]
    if steps is None:
        die(u"行距尺没打结论行（rc=%d）：" % rc + out[-200:])
    vals = [float(v) for v in steps.split(u",")]
    return s(len([v for v in vals if v < 26.0])), u",".join(u"%.1f" % v for v in vals)

GB_D, GS_D = ruler_tight(BEFORE_FRAMES, u"dark")
GB_L, GS_L = ruler_tight(BEFORE_FRAMES, u"light")
GA_D, _ = ruler_tight(RV_DIR + u"/frames", u"dark")
GA_L, _ = ruler_tight(RV_DIR + u"/frames", u"light")
if (GB_D, GB_L) != (u"3", u"3"):
    die(u"修之前那两格读到的紧挨不是 3（暗=%s 亮=%s）⇒ 「修之前」这一半失去了对象，"
        u"before/after 就成了空对账" % (GB_D, GB_L))
if (GA_D, GA_L) != (u"2", u"2"):
    die(u"修之后不是 2（暗=%s 亮=%s）⇒ 屏幕没换，而结构那一格是绿的（判定对了、屏幕没换那一族）"
        % (GA_D, GA_L))

# ──  4. 变异表（本轮五把 + 上一轮十一把的回归）───────────────────────────────
TABLE_ROWS = []
for name, path, want in TABLES:
    txt = require(path)
    got = re.findall(u"(?m)^CAUGHT=(\\d+/\\d+), RESTORE_CLEAN=(\\S+)", txt)
    if not got:
        die(name + u" 的日志里读不到收尾行")
    caught, clean = got[-1]
    if clean != u"yes":
        die(name + u" 还原不干净：" + txt.strip()[-200:])
    if caught != want:
        die(name + u" 没全抓到（要 %s，实得 %s）：%s" % (want, caught, txt.strip()[-400:]))
    arms = u", ".join(re.findall(r"(M\d{3}) CAUGHT", txt))
    bad = re.findall(r"(M\d{3}) (PASSED|NOT_RUN|MISMATCH)", txt)
    if bad:
        die(name + u" 里还有没抓到的臂：" + s(bad))
    TABLE_ROWS.append((name, caught, arms))
by_name = dict((r[0], r) for r in TABLE_ROWS)
TABLE_SUMMARY = u"；".join(u"%s %s（%s）" % r for r in TABLE_ROWS)

pc, _ = sh([sys.executable, PRECHK])
PRE = (re.findall(r"NEEDLE_PRECHECK tables=(\d+) covered=(\d+) arms=\d+ bad=(\d+)", pc) or [None])[-1]
ARM_TOTAL = (re.findall(r"ARM_TOTAL files=(\d+) arms=(\d+) dupes=(\d+) repeats=(\d+)", pc) or [None])[-1]
if PRE is None or ARM_TOTAL is None or PRE[2] != u"0" or ARM_TOTAL[2] != u"0":
    die(u"针预检/臂名册不干净：" + pc.strip()[-400:])

TITLE_SCAN_PY = os.path.join(ROOT, u".scratch", u"motion-audit-2", u"review_round_claims.py")
ts_out, ts_rc = sh([sys.executable, TITLE_SCAN_PY, u"200"])
_tm = re.search(u"扫了=(\\d+) 笔 / (\\d+) 轮 内部不一致=(\\d+)", ts_out)
if not _tm:
    die(u"回顾那把尺的第一行解析不了（退出码 %s）：" + ts_out[:200])
TITLE_SCAN = _tm.groups()   # (笔数, 轮数, 不一致的轮数) —— 退出码 1 是现状，不是坏，故不判
print(u"R336_TITLE_SCAN " + u"/".join(TITLE_SCAN))

gt, gtc = sh([sys.executable, GATE])
GATE_FULL = (re.findall(u"(?m)^MOTION_LEDGER 表面=.*$", gt) or [None])[-1]
if gtc != 0 or GATE_FULL is None:
    die(u"清账表门不干净：" + gt.strip()[-300:])

COMBINED = RV_DIR + u"/§8_combined.log"
with io.open(COMBINED, u"w", encoding=u"utf-8") as fh:
    fh.write(cap + u"\n" + ht + u"\n" + line + u"\n")
rw, rwc = sh([sys.executable, ROWS, COMBINED, u"--must-include",
              u"HTML_INKREAD", u"HTML_ALT", u"MD_RENDER_COST", u"HTML_TYPE",
              u"HTML_ALT_BLOCK", u"HTML_ALT_PARA"])
ROWS_LINE = (re.findall(u"(?m)^READINGS_MUST_INCLUDE .*", rw) or [None])[-1]
MISS = (re.findall(u"(?m)^ROWS_TOTAL=(\\d+) ROWS_MISSING=(\\d+)", rw) or [None])[-1]
if ROWS_LINE is None or u"缺=0" not in ROWS_LINE or MISS is None:
    die(u"§8 搬运口不签：" + rw.strip()[-400:])
ROWS_TOTAL, ROWS_MISSING = MISS
NEW_READINGS = (u"`MD_RENDER_COST` / `HTML_ALT` / `HTML_ALT_BLOCK` / `HTML_ALT_PARA` 第一次进 §8 —— 新读数族在它被打印的同一笔里接上，"
                u"整族前缀 %s 个名字 / 本跑 %s 行" % (NEW_NAMES, NEW_N))

# ──  5. 改动面（从本轮那几笔代码半读）/ 连读 / 电池 / 曲线 ───────────────────
MARK = u"R%d 代码半" % ROUND
log, lrc = sh([u"git", u"log", u"-n", u"8", u"--format=%H%x09%s"])
if lrc != 0:
    die(u"git log 读不到")
code_shas = [l.split(u"\t")[0] for l in log.splitlines()
             if l.split(u"\t")[-1].startswith(MARK)]
if not code_shas:
    die(u"最近 8 笔里没有以「" + MARK + u"」开头的提交 ⇒ 顺序错了，账必须在代码半之后落")
names = u""
for sha in code_shas:
    one_out, nrc = sh([u"git", u"show", u"--name-only", u"--format=", sha])
    if nrc != 0:
        die(u"git show 读不到 " + sha)
    names += one_out
PRODUCT = sorted(set(l for l in names.splitlines() if u"/Sources/" in l))
CHANGED = sorted(set(l for l in names.splitlines() if l.strip()))
if len(PRODUCT) < 1:
    die(u"本轮是产品轮，那几笔代码半里没有 /Sources/ 文件：" + s(len(CHANGED)))
PRODUCT_N = s(len(PRODUCT))

st_cell, _ = sh([sys.executable, STREAK, u"--streak-for", s(ROUND - 1)])
st_this, _ = sh([sys.executable, STREAK, u"--streak-for", s(ROUND)])
STREAK_N = (re.findall(r"streak=(\d+)", st_cell) or [None])[-1]
STREAK_GIT = (re.findall(r"streak=(\d+)", st_this) or [None])[-1]
if None in (STREAK_N, STREAK_GIT):
    die(u"读不到产品面连读的数：" + st_cell.strip()[-200:])

bt, brc = sh([sys.executable, u"-m", u"unittest", u"discover", u"-s", u"scripts/tests"])
BATT = (re.findall(r"Ran (\d+) tests", bt) or [None])[-1]
BATT_SKIP = (re.findall(r"skipped=(\d+)", bt) or [u"0"])[-1]
if BATT is None:
    die(u"写盘前的电池连 Ran 几例都没解析到：" + bt.strip()[-300:])
PRE_RED = sorted(set(re.findall(u"(?m)^(?:FAIL|ERROR): (\\w+)", bt)))
# 登记窗口（与 R335 同一对）：报告里 Sources 那一格要到 --write 才刷新，
# 而 skip 名册那一格会另起一层嵌套电池、把同一朵红原样搬上来。
ALLOWED_PRE = [u"test_the_roster_matches_what_this_machine_actually_skips",
               u"test_the_sources_cell_agrees_with_git"]
if brc != 0 and PRE_RED != ALLOWED_PRE:
    die(u"脚本电池在落盘之前就是红的（Ran=%s，红=%s）：%s" % (BATT, PRE_RED, bt.strip()[-800:]))
cv, crc = sh([sys.executable, CURVE])
if crc != 0:
    die(u"曲线尺不干净：" + cv.strip()[-300:])

# ──  6. 台账正文 ─────────────────────────────────────────────────────────────
UI_TITLE = (u"## 第 %d 轮（R%d · %s · U-%d…U-%d）：撤掉一张图之后，作者为「它加载不了」"
            u"写的那句话必须留下 —— 而 Markdown 那条通道要不要上限，这一次是量出来的"
            u"（U-%d…U-%d · 产品 %s 文件，HTML 通道收尾）"
            % (AUDIT_N, ROUND, DATE, UA, UMAX, UA, UMAX, PRODUCT_N))

UI_BODY = u"""
- **U-%d：401 落地成产品修法 —— `<img>` 换成它的 `alt` 文字**（产品 %s 文件：`HtmlPreview.swift`）。
  R335 的消毒把 `<img>` 整块删掉是对的（产品零出网），但**后果**没人登记：以图为主的页面复制下来，
  渲染态是一块空白，屏幕上没有一句话说明"这里原本有东西"。修法不是发明占位符，
  是照抄 HTML 自己为这件事准备的字段。三条规则各钉一发（现读 `HTML_ALT 有alt保留=%s
  空alt静默=%s 无alt删净=%s 尖括号剥掉=%s`）：有 alt ⇒ 留那句；`alt=""` 或没有 alt ⇒ **静默删**
  （空 alt 是作者声明的装饰图，而 1×1 埋点像素通常根本没有 alt —— 给它们写"〔图片〕"
  等于替追踪像素在屏幕上占位）；alt 里的 `<` `>` 一律剥掉（属性值会变成正文，不剥就是
  "从属性里爬回文档"）。幂等：替换之后不再有 `<img>`，第二遍一个字节都不动。
- **U-%d：402 用一次现读关掉 —— 结论是「不需要上限」，而"不需要"从今天起是有数的判断** ——
  `MD_RENDER_COST 16k=%sms cap=%sms cap字符=%s 边际=%sms/KB 固定=%sms 平均=%sms/KB 预算=%sms 判定=%s`。
  分解成"固定 + 边际"再报是必要的：平均斜率（cap ÷ 总耗时）会把启动那一份摊到每一 KB 上，
  于是"16k 要 %sms"被读成"这条通道很慢"，而决定"最大的那条要不要装上限"的只有边际那一份。
  存档侧允许的最大条目（%s 字符 ≈ %sKB）渲染要 %sms，在 250ms 预算内 ⇒ Markdown 那条**不装**上限；
  R335 那句"没证据的默认"就此换成读数。
- **U-%d：前提取产品自己的上限，不是我挑的一个数** —— 语料长度取自
  `ClipboardIntake.maxTextCharacters`（超过就被截断并留标记），不是随手写的 1MB：
  问"最大的那条要多久"，"最大"必须来自被问的那个系统。判据里同时钉着
  `XCTAssertEqual(big.count, cap)`（语料没造到上限 ⇒ 那一格量的就不是 cap）与
  边际斜率 > 0（斜率为 0 ⇒ "在预算内"是空对账）。
- **U-%d：三把刀，其中一把第一版**打空**，而打空的原因是反例走不到那一行** ——
  M985（不剥尖括号）在 `<img … alt="<script>alert(1)</script>">` 上报 PASSED。
  查下去：标签正则 `<img[^>]*/?>` 到**第一个** `>` 就停，而那个 `>` 在 alt 值里面 ⇒
  alt 根本没被捕获 ⇒ 这一刀改的是走不到的分支。处置是**换反例**（`alt="甲<script乙"`，
  只含 `<` 不含 `>`），不是放宽判据；换完 3/3 CAUGHT。这一族有名字：
  **刀打空先怀疑反例，再怀疑判据**。那条走不到的形状本身登记成 %d（见 U-%d）。
- **U-%d：已知限制钉成**现状断言**，而不是写成注释** —— 属性值里含 `>` 会让标签正则先截断，
  剩下的属性文字漏进正文（`alt="a>b"` → 正文里出现 `b">`）。本轮不修（要修得换一个真正的
  属性 tokenizer，代价与收益不成比例），但断言今天就是这样，并断言它**没有**顺带打开出网通道：
  将来有人修掉，那一格会红，而他必须同时去改 %d —— 一条被钉住的限制不会悄悄变成"从来没存在过"。
- **U-%d：看图腿（四张帧全变了，而且只该是这四张）** —— 现读
  `FRAME_BASELINE_COMPARED=%s CHANGED=4 MISSING=0 ADDED=0`，变的是
  `detail-html-rendered` × 两档（alt 那句话出现在正文里）与 `detail-html-source` × 两档
  （夹具源码多了一行 `<img>`）。暗档那张亲眼看过：「季度趋势图（图片未加载）」以正文墨出现，
  而那只有 src 没有 alt 的埋点像素**没有留下任何痕迹**；两态相减
  `HTML_PAIR_PROOF 千分比 暗=%s 亮=%s`（R335 是 %s/%s —— 多了 alt 那一句，差得更多，方向一致）。
  像素可读性那两把尺照旧签：暗档 %s:1、亮档 %s:1，反侧两档都是 0 颗。
- **U-%d：新读数必须**当场**登记进「按文件按标记」那份名册 —— 它替我红了一次（三朵）** ——
  `PerfBudgetTests.swift` 里新增 `MD_RENDER_COST` 之后，全量卷第一次跑就红在
  `testProbeFilePrintReadingsAreARosterNotACount`：现读 量到的标记名单=%s 对 登记的=%s、
  本文件行数 %s（量/登记）、全表总数 %s（量/登记）。这一格问的问题与"走哪条通道"无关：
  **这些读数有没有名字**。三份名单并存挂在 361，本轮不动它们，只把该登记的登记上，
  而且**同一笔**改三格（名单 / 本文件行数 / 全表总数）—— 分两笔改会让中间那一跑是红的，
  而那一跑谁都不能引用。修完的新日志里这一朵红必须消失（脚本现读 `grep -c`），"我修了"才有出处。
- **U-%d：说明留下了之后还要**自成一段** —— 看图腿量出上半场的修法只做了一半** ——
  同一把行距尺跑两遍（修之前的帧 / 修之后的帧，两档各一张）：紧挨着的两行从
  暗档 %s 处、亮档 %s 处（修之前暗档那串间距 %s pt）降到 %s 处与 %s 处。
  捕获卷那两把尺现读：`HTML_ALT_PARA dark 带=%s 紧挨=%s 行内距=%s 段距=%s`、
  `HTML_ALT_PARA light 带=%s 紧挨=%s 行内距=%s 段距=%s`。
  裸的行内文字会被并进**上一个块的行节奏**（20.0 对 31.5），所以规则 ④ 是：
  独占一行的图 ⇒ alt 包成 `<p>`；句中的图 ⇒ 就地替换（结构那一半现读
  `HTML_ALT_BLOCK 独占成段=%s 句中不包=%s 句中同句=%s`）。仓库外的 spike 顺手否掉
  一个看着更"保守"的选择：包 `<div>` **不产生段落距**（裸文字 17.0 / `<p>` 29.0 /
  `<div>` 17.0）⇒ 选 `<p>` 是量出来的，不是"随便挑一个块级标签"。
  两半各一把刀（M987 永远包段、M988 永远不包）—— 这两种坏法在屏幕上是相反的。
- **U-%d：期望值先写错了一次，而修的是**我的推导**，不是地板** ——
  那条像素门第一版写"紧挨必须 1 处"（我以为夹具里只剩列表内部那一档）。基线一跑就红在
  2 处：`乙项→alt` 也是 20.0。查下去**不是**规则 ④ 没生效（`alt→下一段` 已经从 20.0
  变成 31.5），而是这个渲染器**不给 `<ul>` 下边距** —— 列表后面紧跟的那一块本来就没有段前距。
  处置：期望换成从分块结构推出来的 2 处，把多出来那一处登记成现状（BACKLOG %d），
  并在同一格钉"两群分不开（差 <6pt）就必须红" —— 而不是把 26pt 的地板挪到 34pt 让它过。

""" % (UA, PRODUCT_N, ALT_KEPT, ALT_SILENT, ALT_NODESC, ALT_ANGLE,
       UB, MD_SMALL, MD_BIG, MD_CAP_CHARS, MD_MARGINAL, MD_FIXED, MD_MEAN_SLOPE,
       MD_BUDGET, MD_VERDICT, MD_SMALL, MD_CAP_CHARS, MD_CAP_KB, MD_BIG,
       UC,
       UD, B_LEAK, UF,
       UE, B_LEAK,
       UF, RV[u"baseline_compared"], PAIR_D, PAIR_L, u"74", u"68", D_RATIO, L_RATIO,
       UG, ROSTER_MEASURED, ROSTER_REGISTERED_OLD, ROSTER_ROWS, ROSTER_TOTAL,
       UH, GB_D, GB_L, GS_D, GA_D, GA_L,
       PD_BANDS, PD_TIGHT, PD_LINE, PD_PARA,
       PL_BANDS, PL_TIGHT, PL_LINE, PL_PARA,
       BLOCK_STANDALONE, BLOCK_INLINE, BLOCK_SAME_SENTENCE,
       UI2, B_LIST)

ITER_TITLE = (u"## Round %d · R%d（第 %d 轮 · %s）：撤掉一张图之后，作者写的那句 alt 必须留下 —— "
              u"而 Markdown 要不要上限，这一次是量出来的（产品 %s 文件）"
              % (ITER_N, ROUND, AUDIT_N, DATE, PRODUCT_N))

ITER_BODY = u"""
上一轮开出来的四条里，本轮关掉两条，并且给第三条留下了钉子。

**402：先量，再决定要不要修。** Markdown 那条通道一直没有字节上限（HTML 那条 R335 装了 128KB，
由现读斜率推）。"Markdown 不需要"这句话听起来合理，但它当时是**没证据的默认**。
于是量了一次，语料长度取 `ClipboardIntake.maxTextCharacters`（存档侧真正允许的最大条目），
不是随手挑的 1MB：

| 档 | 字符数 | 最快 | 说明 |
| --- | --- | --- | --- |
| 小 | 16,000 | %sms | 固定开销占绝大多数 |
| 存档上限 | %s | %sms | 边际只多 %sms |

分解成 **固定 %sms + 边际 %sms/KB** 才看得清：平均斜率（%sms/KB）里有一大半是启动成本，
把它当"每 KB 多少钱"会得出"这条通道慢"的错结论。按边际算，就算条目比上限还大十倍也才
~250ms 量级 ⇒ **不装上限**，而这一句现在背后有数了。

**401：图被撤掉之后，屏幕上不该是一片空白。** 消毒删 `<img>` 是对的（产品零出网），
但代价静默转嫁给了用户。修法不是发明"〔图片〕"，是照抄 HTML 自己的字段 —— `alt`
本来就是"这张图加载不了时该显示什么"。三条规则：有 alt 留文字；`alt=""` 或没有 alt **静默删**
（空 alt 是作者声明的装饰图，而埋点像素通常压根没有 alt —— 替它们占位等于替追踪像素占位）；
alt 里的尖括号剥掉（属性值会变成正文，不剥就是"从属性里爬回文档"）。

三把刀里有一把值得单独说：M985（不剥尖括号）第一版报 **PASSED** —— 刀打空。
原因是我挑的反例 `alt="<script>alert(1)</script>"` 里那个 `>` 会让标签正则先截断，
alt 根本没被捕获，于是那一刀改的是一个**走不到的分支**。处置是换反例（`alt="甲<script乙"`），
不是放宽判据。换完 3/3 CAUGHT。

而那个走不到的形状不是"我的反例写错了"就完了 —— 它是产品的一条**真限制**：
属性值里含 `>` 时标签正则先截断，剩下的属性文字会漏进正文（`alt="a>b"` → 正文出现 `b">`）。
本轮不修（要修得换真正的属性 tokenizer），但把它钉成**现状断言**：将来有人修掉，
那一格会红，他必须同时去改 %d。一条被钉住的限制不会悄悄变成"从来没存在过"。

看图腿：四张帧变了，而且只该是这四张（`CHANGED=4 / COMPARED=%s / MISSING=0 / ADDED=0`）——
渲染态两档多了「季度趋势图（图片未加载）」那一句，原文态两档多了夹具里那一行 `<img>`。
暗档那张亲眼看了：那句话以正文墨出现，而那只有 src 没有 alt 的像素**没有留下任何痕迹**。
可读性那两把尺照旧签（暗 %s:1 / 亮 %s:1，反侧两档 0 颗）。

还有一件**我自己的**事值得写下来：新增 `MD_RENDER_COST` 那一行时没同时登记
「按文件按标记」那份名册，于是全量卷第一次跑就红在三格（数与出处都在 U-1134）。这一格问的
从来不是"读数走哪条通道"，而是"这些读数有没有名字" —— 我把它当成捕获卷那份名册而漏了它，
红得完全正确。三格同一笔改到现读，而不是分三笔（分笔会让中间那一跑是红的，谁都不能引用）。

下半场是看图腿逼出来的：第一版把"图被撤之后说明要留下"做完了，看帧时觉得那句"好像跟下一段
挤在一起" —— 而**形容词不许进台账**，于是现造一把行距尺（复用这一卷已有的 `rowTierProfile`
+ `textBands`，不新造尺），把"挤在一起"量成"紧挨着的两行有几处"：修之前 3 处、修之后 2 处，
两档同向。修法就是规则 ④（独占一行的图 ⇒ alt 包成 `<p>`；句中的图 ⇒ 就地替换），
而 spike 顺手否掉了"包 `<div>`"这个看着更保守的选择 —— 它不产生段落距。
还有一次自曝：那条像素门我把期望写成 1 处，基线红在 2 处。查下去是渲染器不给 `<ul>` 下边距
（列表后面那一段本来就没有段前距），**不是**修法没生效。期望换成推导出来的 2，多出来那一处
登记成 BACKLOG 406 的现状 —— 挪地板是这一族里最便宜也最坏的那种修法。

七维度自评：

| 维度 | 分/满分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | 14/15 | 看图腿这次不只是"看了"：把"好像挤在一起"量成行距尺（修之前 3 处紧挨 / 修之后 2 处），两档各一张 before/after；但仍未给"图很多"的页面做夹具 |
| 判据有效性 | 14/15 | 新增 2 格（alt 三条规则 + Markdown 耗时分解），每条都有对象证人；M985 第一版打空被换成能走到的反例 |
| 假绿防御 | 14/15 | "刀打空先怀疑反例"这一族抓到了自己；已知限制钉成现状断言而不是注释；但 400（CJK 强调）那一半仍然没量 |
| 产品面推进 | 13/15 | 产品 %s 文件（alt 通道），两单结案（401 修、402 判"不修"并绑读数）；本轮没有动动效主线 |
| 台账一致性 | 13/15 | 七本 + 报告计数器 + Sources 那一格由脚本派生；§8 名单当场接上 `MD_RENDER_COST`；但本轮又用了一次"写完再补"的生成器调试（见 STATE 的工具面） |
| 交付诚实性 | 14/15 | 不修的三条都写了为什么不修 + 绑读数；"没量"的仍挂在 400，没写成没问题 |
| 可复核性 | 13/15 | 全部读数出自仓库里的尺；反例串写在判据里，任何人可以重跑 M985 |

""" % (MD_SMALL, MD_CAP_CHARS, MD_BIG, s(round(float(MD_BIG) - float(MD_SMALL), 2)),
       MD_FIXED, MD_MARGINAL, MD_MEAN_SLOPE, B_LEAK,
       RV[u"baseline_compared"], D_RATIO, L_RATIO, PRODUCT_N)

DEC_BODY = u"""
**D-%d（%d）：撤掉一个构造之后，作者为「它不可用」准备的那份文字必须留下；而装饰图不许获得占位符**
消毒的默认动作是"删掉"，而删掉的代价由屏幕上看的人付：一张以图为主的页面在渲染态变成一块空白，
没有任何一句话说明这里原本有东西。HTML 早就为这件事准备了字段 —— `alt` 的语义就是
"这张图加载不了时该显示什么"，所以照抄它不是发明，是把作者的意图保留下来。
反过来，`alt=""` 与没有 alt 必须**静默消失**：前者是作者明确声明的装饰图，后者多半是 1×1 埋点像素，
替它们写"〔图片〕"等于给追踪像素在屏幕上要了一个位置 —— 那正是这条通道存在的理由要防的事。
第三条是安全边界：alt 的值会变成**正文**，不剥尖括号就是 `alt="…<script…"` 这种从属性爬回文档的通道。
登记：这条规矩由 M984/M985/M986 三把刀钉住（三种坏法在屏幕上长得都不一样），
而它暴露出的属性截断限制单独开在 %d。
""" % (D1, ROUND, B_LEAK)

BL_NEW = u"""
**%d. 属性值里含 `>` 会让标签正则先截断，剩下的属性文字漏进正文（R%d 现读复现）**（R%d）
复现串：`<img src="https://x/1.png" alt="a>b"><p>后</p>` —— `<img[^>]*/?>` 到第一个 `>` 就停，
于是 alt 没被捕获、标签被删成 `<img src="https://x/1.png" alt="a>`，
剩下的 `b">` 以正文形式留下。它不是隐私洞（`residualFetchableReferences` 现读为空，
判据里钉着这一条），是**内容脏**。R%d 没修：要修得把"正则删标签"换成一个真正的
属性 tokenizer（引号内的 `>` 不算标签结束），那是另一个量级的改动。
本轮的处理是**把现状钉住**：`testImageAltTextSurvivesWhileTheImageItselfDoesNot` 里
断言今天确实漏（`b">` 在输出里）且没有打开出网通道 —— 将来有人修掉，那一格会红，
他必须同时改这一条。同一族形状对 `title=` / `data-*` 等任何带引号属性都成立。

""" % (B_LEAK, ROUND, ROUND, ROUND)

BL_TITLE = u"""
**%d. 标题里那半句「产品 K 文件」在同一轮的两笔提交里给出两个数（R%d 回顾时现读）**（R%d）
`python3 .scratch/motion-audit-2/review_round_claims.py 200` 现读：扫了 **%s 笔 / %s 轮**，
其中 **%s 轮内部不一致** —— R335 是 `代码半=7 / 账半=7 / 代码半补=0`，R334 是 `代码半=2 / 账半=0`。
两种语义都在被使用：K = **这一轮**的产品面文件数（台账那一格引用的就是它，也是
`scripts/product_streak.py` 从"代码半"那一笔并集派生的数），或 K = **这一笔提交**改的文件数。
读 `git log` 的人无从判断哪一句作数；而标题已经带着「第 N 轮 / Round M」这一串**轮次级**身份，
所以混用是自我矛盾的形状。
下一轮要做两件事：① 立一条 D 定义"轮次级 —— 本轮每一笔重复同一个数"；
② 把 `review_round_claims.py` 变成电池里会红的门，并把 R334/R335 这两轮写进**显式豁免名单**
（按扫描作用域对账；不许把窗口整体放宽 —— 放宽窗口 = 把已经发生的不一致洗成看不见）。
本条不是隐私洞也不是渲染缺陷，是审计链自己的可读性。

""" % (B_TITLE, ROUND, ROUND, TITLE_SCAN[0], TITLE_SCAN[1], TITLE_SCAN[2])

BL_LIST_ENTRY = u"""
**%d. 这个渲染器不给 `<ul>` 下边距：列表后面紧跟的那一段没有段前距（R%d 行距尺现读）**（R%d）
`HTML_ALT_PARA dark 带=%s 紧挨=%s 行内距=%s 段距=%s`、
`light 带=%s 紧挨=%s 行内距=%s 段距=%s`：
夹具里"乙项→它下面那一段"这一对的间距是 %s pt，而两个 `<p>` 之间是 %s / %s pt。
也就是说**列表块之后**的边界在屏幕上是隐形的 —— 与 R336 规则 ④ 修掉的那一半同族
（块边界读不出来），但成因不同：④ 是我们自己把文字塞成了行内，这一条是
`NSAttributedString(html:)` 的排版表。R%d 不修（修它要动整条 HTML 通道的段落样式），
处置是**把现状钉进判据**：`testHtmlAltLineIsItsOwnParagraphOnTheSurface` 的期望
"紧挨 2 处"里就有这一处 —— 将来谁给列表加了下边距，那一格会红，而他必须同时来改这条。

""" % (B_LIST, ROUND, ROUND,
       PD_BANDS, PD_TIGHT, PD_LINE, PD_PARA, PL_BANDS, PL_TIGHT, PL_LINE, PL_PARA,
       PD_LINE, PD_PARA, PL_PARA, ROUND)

# 401 / 402 的结案写进**它们自己那条**的追记（同号两份正文 = 读者不知道哪份作数）
BL_CLOSE_401 = u"""

追记（R%d）：**结案 —— 按 D-%d 的三条规则落地。** `<img>` 现在先换成它的 `alt` 文字再删标签
（`HtmlSanitizer.imagesReplacedWithAlt`）：有 alt 留那句、`alt=""` 或没有 alt 静默删、
alt 里的 `<` `>` 剥掉。现读 `HTML_ALT 有alt保留=%s 空alt静默=%s 无alt删净=%s 尖括号剥掉=%s`；
三把刀 M984/M985/M986 全 CAUGHT（`CAUGHT=3/3, RESTORE_CLEAN=yes`）；
渲染态帧上亲眼确认「季度趋势图（图片未加载）」以正文墨出现，而埋点像素没留痕迹。
当时点名的"要先量缺席计数"这一半改成了**量构造本身**：本轮没有真存档的分布可读（红线），
所以留下的可复查物是夹具与判据，不是覆盖率。
""" % (ROUND, D1, ALT_KEPT, ALT_SILENT, ALT_NODESC, ALT_ANGLE)

BL_CLOSE_402 = u"""

追记（R%d）：**结案 —— 量完之后判「不需要上限」。** `MD_RENDER_COST 16k=%sms cap=%sms
cap字符=%s 边际=%sms/KB 固定=%sms 平均=%sms/KB 预算=%sms 判定=%s`：
存档侧允许的最大条目（`ClipboardIntake.maxTextCharacters` = %s 字符）渲染要 %sms，
在仓库自己那条 250ms 预算内 ⇒ Markdown 那条**不装**字节上限。
这一格特意把平均斜率与边际斜率并排放：只报平均会把固定开销摊进每一 KB，
读出来像"这条通道慢"，而那不是决定"要不要上限"的那个数。
判据 `PerfBudgetTests/testMarkdownRenderCostAtTheArchiveCap` 同时钉"不许超线性"与"cap 必须在预算内"，
所以将来解析器退化（O(n²)）或有人把预算改松，都会先在这里红。
""" % (ROUND, MD_SMALL, MD_BIG, MD_CAP_CHARS, MD_MARGINAL, MD_FIXED, MD_MEAN_SLOPE,
       MD_BUDGET, MD_VERDICT, MD_CAP_CHARS, MD_BIG)

CHG_ENTRY = u"""### 图被消毒撤掉之后，它自己的说明文字留下了；Markdown 那条要不要上限改成量出来的（R%d / U-%d…U-%d · 产品 %s 文件）

- `<img>` 不再整块消失：先换成它的 `alt` 文字，再删标签。`alt=""` 或没有 alt 的（装饰图 /
  1×1 埋点像素）**静默删除**，不发明占位文字；alt 值里的 `<` `>` 一律剥掉。
- 新增判据 1 格（三条规则 + 幂等 + 残留为空）、变异刀 M984…M986 三把（`CAUGHT=3/3, RESTORE_CLEAN=yes`）。
- BACKLOG 402 结案：Markdown 渲染耗时现读 固定 %sms + 边际 %sms/KB，
  在存档上限（%s 字符）上是 %sms，预算 250ms ⇒ **不装**字节上限，判据把"不许超线性"与
  "cap 必须在预算内"同时钉住。
- BACKLOG 401 结案（见那条的追记）。新开 %d：属性值含 `>` 会让标签正则先截断（现状断言钉住）。
- 帧基线同一笔更新：`CHANGED=4`（只有 HTML 夹具那两张 × 两档），`MISSING=0 ADDED=0`。
- 自曝一条工具面（U-%d）：新增 `MD_RENDER_COST` 而没登记「按文件按标记」那份名册 ⇒ 全量卷红三朵
  （量到的名单=%s 对 登记的=%s、本文件行数 %s、全表总数 %s），同一笔改到现读并把"红消失"钉成现读。
- 回顾时量到并新开 %d：同一轮的两笔提交在标题里给出两个「产品 K 文件」（现读 %s 轮里 %s 轮不一致），修法与豁免名单一起写在条目里。
- 下半场（看图腿量出来的，不是新特性）：独占一行的 `<img>` 被撤之后 alt 包成 `<p>`，句中的图仍就地替换。
  行距尺现读 紧挨处数 修之前 暗/亮 = %s/%s → 修之后 = %s/%s；像素门 `HTML_ALT_PARA 行内距=%s 段距=%s`。
  新增判据 2 格（结构 + 像素）、刀 M987/M988；新开 %d：渲染器不给 `<ul>` 下边距（现状钉进判据）。

""" % (ROUND, UA, UMAX, PRODUCT_N, MD_FIXED, MD_MARGINAL, MD_CAP_CHARS, MD_BIG, B_LEAK,
       UG, ROSTER_MEASURED, ROSTER_REGISTERED_OLD, ROSTER_ROWS, ROSTER_TOTAL,
       B_TITLE, TITLE_SCAN[1], TITLE_SCAN[2],
       GB_D, GB_L, GA_D, GA_L, PD_LINE, PD_PARA, B_LIST)

# ──  7. 写盘（先做**全部**锚点预检，再写第一块盘）─────────────────────────────
aud = rd(AUD)
UI_ANCHOR = (u"## 第 %d 轮" % (AUDIT_N - 1))
if aud.count(UI_ANCHOR) != 1:
    die(u"UI_AUDIT 的插入锚命中 %d 次（要 1 次）：" % aud.count(UI_ANCHOR) + UI_ANCHOR)
chg = rd(CHG)
chg_lines = chg.splitlines(True)
unrel = [i for i, l in enumerate(chg_lines) if l.rstrip(u"\n") == u"## [Unreleased]"]
if len(unrel) != 1:
    die(u"CHANGELOG 里整行等于 `## [Unreleased]` 的行有 %d 行（要 1 行）" % len(unrel))
first_h3 = [i for i in range(unrel[0] + 1, len(chg_lines)) if chg_lines[i].startswith(u"### ")]
if not first_h3:
    die(u"CHANGELOG 的 [Unreleased] 之后找不到第一条 ###")
H3_AT = first_h3[0]
blg = rd(BLG)
m401 = re.search(u"(?m)^\\*\\*%d\\. .*?(?=^\\*\\*\\d{3}\\. |\\Z)" % B_ALT, blg, re.S)
if not m401:
    die(u"BACKLOG %d 找不到，结案追记无处可挂" % B_ALT)
m402 = re.search(u"(?m)^\\*\\*%d\\. .*?(?=^\\*\\*\\d{3}\\. |\\Z)" % B_MDBUDGET, blg, re.S)
if not m402:
    die(u"BACKLOG %d 找不到，结案追记无处可挂" % B_MDBUDGET)
sta = rd(STA)
if (u"## R%d 状态" % ROUND) in sta:
    die(u"STATE 已经有 R%d 那一节 ⇒ 这一笔已经写过，不许重复轮换" % ROUND)
prev_titles = re.findall(u"(?m)^## R%d 状态" % (ROUND - 1), sta)
if len(prev_titles) != 1:
    die(u"STATE 里上一轮的节标题命中 %d 次" % len(prev_titles))
before_layers = sta.count(u"\n> ## ")
fr_pre = rd(FRA)
for pat, what in ((u"U-31 … U-(\\d+)", u"U 区间那一格"),
                  (u"(决定台账[^\\n]*?D-\\d{3} … \\*\\*)(D-\\d{3})", u"决定台账那一格的区间"),
                  (u"(?m)^- \\*\\*判据与门的规模\\*\\*：.*$", u"§13 的「判据与门的规模」"),
                  (u"(?m)^- \\*\\*产品面（这一节最该被读的部分）\\*\\*：.*$", u"§13 的「产品面」"),
                  (u"(?m)^- \\*\\*仍开（截至本轮，完整名单以 `AGENT_STATE.md` 的 R\\d+ 节", u"§13 的「仍开」")):
    if len(re.findall(pat, fr_pre)) != 1:
        die(u"报告里 " + what + u" 不是恰好一处，先修锚点再谈写盘")

wr(AUD, aud[:aud.index(UI_ANCHOR)] + UI_TITLE + u"\n" + UI_BODY + u"\n" + UI_ANCHOR
   + aud[aud.index(UI_ANCHOR) + len(UI_ANCHOR):])

wr(ITE, rd(ITE).rstrip(u"\n") + u"\n\n" + ITER_TITLE + u"\n" + ITER_BODY.rstrip() + u"\n")

wr(DEC, rd(DEC).rstrip(u"\n") + u"\n\n" + DEC_BODY.rstrip(u"\n") + u"\n")

blg = rd(BLG)
# 两条结案追记先挂到**各自那条**上（从文件尾往前做，避免前面的偏移让后面的锚点漂）
for bid, body in ((B_MDBUDGET, BL_CLOSE_402), (B_ALT, BL_CLOSE_401)):
    m = re.search(u"(?m)^\\*\\*%d\\. .*?(?=^\\*\\*\\d{3}\\. |\\Z)" % bid, blg, re.S)
    if not m:
        die(u"BACKLOG %d 在追加过程中找不到了" % bid)
    blg = blg[:m.end()].rstrip(u"\n") + body.rstrip(u"\n") + u"\n" + blg[m.end():].lstrip(u"\n")
blg = blg.rstrip(u"\n") + u"\n\n" + BL_NEW.rstrip(u"\n") + u"\n"
blg = blg.rstrip(u"\n") + u"\n\n" + BL_TITLE.rstrip(u"\n") + u"\n"
blg = blg.rstrip(u"\n") + u"\n\n" + BL_LIST_ENTRY.rstrip(u"\n") + u"\n"
wr(BLG, blg.rstrip(u"\n") + u"\n")

wr(CHG, u"".join(chg_lines[:H3_AT]) + CHG_ENTRY.rstrip(u"\n") + u"\n\n"
   + u"".join(chg_lines[H3_AT:]))

STATE_BODY = u"""## R%d 状态（%s · 本地 · 第 %d 轮 / Round %d）：撤掉一张图之后作者写的 alt 必须留下，而 Markdown 要不要上限改成量出来的（产品 %s 文件，HTML 通道收尾）

最后更新：%s（本地 · R%d / 第 %d 轮 / Round %d）：BACKLOG 401 落地成产品修法（`<img>` 换成它的 alt 文字），
402 用一次现读关掉（Markdown 那条**不需要**字节上限），新开 404 把一条已知限制钉成现状断言（产品 %s 文件 · HTML 通道收尾）

本轮做了什么：两件事都不是"加功能"，是把上一轮**留下的说法**换成数。
① 402：`MD_RENDER_COST` 现读 固定 %sms + 边际 %sms/KB，存档上限（%s 字符）那一档要 %sms，
预算 250ms ⇒ 不装上限。之前那句"Markdown 不需要"是没证据的默认，现在它有出处。
② 401：消毒撤掉 `<img>` 之后，屏幕上不该是一片空白 —— 照抄 HTML 自己的 `alt` 字段：
有 alt 留文字、空/缺 alt 静默删（装饰图与埋点像素不配占位）、alt 里的尖括号剥掉。
③ M985 第一版**打空**（PASSED）：反例 `alt="<script>…</script>"` 里那个 `>` 让标签正则先截断，
alt 根本没被捕获 ⇒ 那一刀改的是走不到的分支。换反例（只含 `<` 不含 `>`）之后 3/3 CAUGHT。
那个走不到的形状登记成 %d 并**断言现状**（将来修掉会红，改的人必须同时更正那条）。

验证读数（现读）：`MD_RENDER_COST 16k=%sms cap=%sms cap字符=%s 边际=%sms/KB 固定=%sms 平均=%sms/KB 预算=%sms 判定=%s`；
`HTML_ALT 有alt保留=%s 空alt静默=%s 无alt删净=%s 尖括号剥掉=%s`；
`HTML_INKREAD dark 比=%s 反侧=%s颗`、`light 比=%s 反侧=%s颗`（覆盖率 暗=%s 亮=%s）；
两态相减 `HTML_PAIR_PROOF 千分比 暗=%s 亮=%s`；`HTML_SANITIZE 构造=%s 残留=%s`；
判据卷 `Executed %s（failures=%s）`、捕获卷 `Executed %s（skipped=%s, failures=%s）`；
`ROUND_VERIFY %s`；变异表 `%s`；针预检 tables=%s covered=%s bad=%s、名册 files=%s arms=%s dupes=%s；
清账表 `%s`；脚本电池 `Ran %s（skipped=%s）`；产品面连续零改动 **%s** 轮（现读 `scripts/product_streak.py` 的 streak —— 这一整句必须在同一行里：`_cells` 问的是"那一格有没有引用取数口"，分两行写就等于没引用）。唯一取数口 `python3 scripts/product_streak.py --streak-for %d`；本轮这一笔 `--streak-for %d` 现读 %s。
§8 搬运：`%s`，本轮新族 %s

NOT-RUN（三种缺席分开写，不许省略）：① **只在人身上判得了**：真窗口里 alt 那句话与上下文的
呼吸感（离屏帧能证它出现，不能证它在真表面上好不好读）；
② **只在 runner 上判得了**：`testMarkdownRenderCostAtTheArchiveCap` 在 runner 上的数
（它带 R56 那族"同操作样本跨度超阈值就 skip"的闸门 —— runner 上很可能记为未运行，
那不是坏，但也不是签）；本轮新像素证据在 runner 的字族上是否同数；
③ **这条通道看不见**的：400（CJK 强调在像素层体不体现）本轮**仍然没量** —— 它需要一颗
笔画粗细/墨量尺，不是"再看一眼帧"能给的。

下一轮（R%d）的靶：⓪ 读 CI 配对（成对：run id ↔ commit，现读自 `scripts/ci_read.py latest`），
并答 R335 那一跑欠的三问（新像素门在 runner 上签不签、`HTML_` 那族在 runner 日志里打几行、
判据卷格数与 §8 行数的两机对账）→ ① **回到动效主线**：399（亮档悬停换轴，A 案描边 / B 案提亮，
先量系统那颗的方向再选）、390 的 before/after、389 的时长、384 的横轴、387①、376、
367/360/361/364 → ② 400 那条要动就得先造尺（笔画墨量），不许用形容词结案 → ④ 405：把"标题里那半句产品数"立成定义并变成电池里会红的门（R334/R335 走显式豁免），它比动效那一串便宜得多，而且是审计链自己的可读性 →
③ 本轮复盘时**看到但没量**的一条：`altAttr` 用的是 `\\balt`，而 ICU 的词边界把 `data-alt`
里那个 `alt` 也算起点 —— 于是 `<img data-alt="埋点说明" alt="真说明">`（data- 在前）取到的
是**埋点那个属性**的文字。这是"屏幕上出现作者没打算给人读的一句话"，与 401 那条规矩
（只留作者为"图加载不了"准备的那一份）方向相反。**R337 第一件事是用产品入口把它量出来**
（一条打印 `HTML_ALT_SOURCE` 的判据），量到了再修：把 `\\b` 换成 `(?:\A|\s)`，并给"属性名前缀
不许冒充属性名"这一族配刀。Python 的 `re` 只是我自己在本机的猜测，**不算读数**。

本轮的自伤（写成出处，不写成缺陷）：新增读数 `MD_RENDER_COST` 时没同时登记那张
「按文件按标记」的名册，全量卷第一次跑就红三朵 —— 现读 量到的名单=%s 对 登记的=%s、
本文件行数 %s（量/登记）、全表总数 %s（量/登记）；同一笔把三格改到现读，
新日志里这一朵红消失（`grep -c` 现读 0）⇒ 登记生效（U-%d）。

下半场（同一轮里加的，因为它是**看图腿量出来的**，不是新特性）：规则 ④ —— 独占一行的图，
它的 alt 包成 `<p>`；句中的图就地替换。行距尺现读 紧挨处数 修之前 暗/亮 = %s/%s →
修之后 = %s/%s；`HTML_ALT_PARA dark 带=%s 行内距=%s 段距=%s`、
`light 带=%s 行内距=%s 段距=%s`；
`HTML_ALT_BLOCK 独占成段=%s 句中不包=%s 句中同句=%s`；刀加到 M984…M988（`CAUGHT=5/5`）。
另一次自曝：那条像素门的期望我先写成"紧挨 1 处"，基线红在 2 处 —— 多出来那一处是
**渲染器不给 `<ul>` 下边距**（登记成 %d 的现状，判据里同时钉"两群分不开就必须红"），
修的是我的推导，不是地板（U-%d）。

""" % (ROUND, DATE, AUDIT_N, ITER_N, PRODUCT_N,
       DATE, ROUND, AUDIT_N, ITER_N, PRODUCT_N,
       MD_FIXED, MD_MARGINAL, MD_CAP_CHARS, MD_BIG, B_LEAK,
       MD_SMALL, MD_BIG, MD_CAP_CHARS, MD_MARGINAL, MD_FIXED, MD_MEAN_SLOPE, MD_BUDGET, MD_VERDICT,
       ALT_KEPT, ALT_SILENT, ALT_NODESC, ALT_ANGLE,
       D_RATIO, D_WRONG, L_RATIO, L_WRONG, D_COV, L_COV, PAIR_D, PAIR_L,
       SANI_CONSTRUCTS, SANI_RESIDUE, HTML_RUN, HTML_FAIL, CAP_RUN, CAP_SKIP, CAP_FAIL,
       line, TABLE_SUMMARY, PRE[0], PRE[1], PRE[2], ARM_TOTAL[0], ARM_TOTAL[1], ARM_TOTAL[2],
       GATE_FULL, BATT, BATT_SKIP, STREAK_N, ROUND - 1, ROUND, STREAK_GIT,
       ROWS_LINE, NEW_READINGS, ROUND + 1,
       ROSTER_MEASURED, ROSTER_REGISTERED_OLD, ROSTER_ROWS, ROSTER_TOTAL, UG,
       GB_D, GB_L, GA_D, GA_L, PD_BANDS, PD_LINE, PD_PARA, PL_BANDS, PL_LINE, PL_PARA,
       BLOCK_STANDALONE, BLOCK_INLINE, BLOCK_SAME_SENTENCE, B_LIST, UI2)

sta = rd(STA)
pos = sta.index(prev_titles[0])
wr(STA, sta[:pos] + STATE_BODY.rstrip(u"\n") + u"\n\n" + sta[pos:])
after = rd(STA)
if after.count(u"\n> ## ") != before_layers:
    die(u"STATE 轮换改动了 `> ##` 层数：%d → %d ⇒ 这一支不该顺手重排整本文件"
        % (before_layers, after.count(u"\n> ## ")))
if (u"## R%d 状态" % (ROUND - 1)) not in after:
    die(u"轮换之后上一轮那一节的标记没了")
if (u"最后更新：%s（本地 · R%d" % (DATE, ROUND)) not in after:
    die(u"本轮的 identity 行没落在 expected 形状上 ⇒ `current_round()` 那把尺读不到本轮")

# ──  FINAL_REPORT：只改 §13 之外那两格 + §13 两行由现读数组重拼 ──────────────
fr = rd(FRA)
mUD = re.search(u"U-31 … U-(\\d+)", fr)
udefs = len(re.findall(u"(?m)^- \\*\\*U-(\\d{3,4})[：(]", rd(AUD)))
fr = once(fr, mUD.group(0), u"U-31 … U-%d" % UMAX)
m = re.search(u"(决定台账[^\\n]*?D-\\d{3} … \\*\\*)(D-\\d{3})", fr)
OLD_D_TOP = m.group(2)
fr = fr[:m.start(2)] + (u"D-%d" % D1) + fr[m.end(2):]
print(u"REPORT_D_CELL %s → D-%d" % (OLD_D_TOP, D1))

scale_old = re.findall(u"(?m)^- \\*\\*判据与门的规模\\*\\*：.*$", fr)
new_scale = (u"- **判据与门的规模**：脚本电池现读 **Ran %s**（写盘前同数），变异臂在册 **%s** 把 / %s 张表"
             u"（预检 tables=%s covered=%s bad=%s）；U 定义行 **%s 条**、最大 **U-%d**；"
             u"决定台账最大 **D-%d**，BACKLOG 最大 **%d**（本轮新开三单：%d 属性值含 `>` 的截断限制、%d 标题内两个产品数、%d 列表后面没有段前距；"
             u"结案两单：%d 图被撤、说明留下，%d Markdown 要不要上限）；"
             u"本轮刀 `mutate_r336.py CAUGHT=%s, RESTORE_CLEAN=yes`（%s），"
             u"并把上一轮那十一把在同一文件上重跑（`mutate_r335 %s`）。"
             u"§8 的读数搬运名单本轮**当场接上**：`%s`（%s 个名字 / 本跑 %s 行），%s。"
             u"而它自己的键名仍有 %s/%s 格没日志可解析（%d 那一向仍在）。"
             % (BATT, ARM_TOTAL[1], ARM_TOTAL[0], PRE[0], PRE[1], PRE[2], udefs, UMAX, D1, B_LIST,
                B_LEAK, B_TITLE, B_LIST, B_ALT, B_MDBUDGET,
                by_name[u"mutate_r336"][1], ARMS_NEW[0] + u"…" + ARMS_NEW[-1],
                by_name[u"mutate_r335"][1], NEW_READINGS, NEW_NAMES, NEW_N, ROWS_LINE,
                ROWS_MISSING, ROWS_TOTAL, B_ALT))
fr = fr.replace(scale_old[0], new_scale)

prod_old = re.findall(u"(?m)^- \\*\\*产品面（这一节最该被读的部分）\\*\\*：.*$", fr)
new_prod = (u"- **产品面（这一节最该被读的部分）**：本轮产品文件 **%s** 个（**HTML 通道收尾**："
            u"`HtmlPreview.swift` 的消毒多了一步 `imagesReplacedWithAlt` —— 图被撤之后它的 alt 文字"
            u"留在正文里，而 `alt=\"\"` / 没有 alt 的静默删除）。"
            u"另有一条**判「不修」**绑着读数：Markdown 那条不需要字节上限"
            u"（固定 %sms + 边际 %sms/KB，存档上限 %s 字符那一档 %sms，预算 %sms）。"
            u"帧基线同一笔更新：累计 4 张变了（alt 那句 + 它自成一段），每张都只该是 HTML 夹具那两档。"
            u"产品面连续零改动轮数 = **%s**（现读 `python3 scripts/product_streak.py`）。"
            u"401/402 结案，新开 %d 与 %d；400 仍开（要动先得有笔画墨量尺）。"
            % (PRODUCT_N, MD_FIXED, MD_MARGINAL, MD_CAP_CHARS, MD_BIG, MD_BUDGET,
               STREAK_N, B_LEAK, B_TITLE))
fr = fr.replace(prod_old[0], new_prod)
fr = re.sub(u"(?m)^(- \\*\\*仍开（截至本轮，完整名单以 `AGENT_STATE.md` 的 R)\\d+( 节)",
            u"\\g<1>%d\\g<2>" % ROUND, fr, count=1)
if re.search(u"@\\w+@", fr):
    die(u"报告里还有没替换的占位符")
wr(FRA, fr)

sc, src_rc = sh([sys.executable, SRCCELL, u"--write"])
if src_rc != 0:
    die(u"报告里 Sources 那一格刷新失败：" + sc.strip()[-300:])
SRC_LINE = (re.findall(u"(?m)^SOURCES_CELL .*", sc) or [None])[-1]
if SRC_LINE is None:
    die(u"report_sources_cell 没打结论行：" + sc.strip()[-300:])

# ──  写盘之后：§1 刷新 → 电池（不带名单）→ 连读门 → 曲线 → 七维表对账 → 标题格 ─
rf0, rfc0 = sh([sys.executable, FRESH])
if rfc0 != 0 or u"REFUSED" in rf0:
    die(u"报告 §1 的刷新器没签：%s" % rf0.strip()[-300:])

ite_after = rd(ITE)
rows = re.findall(u"(?m)^\\| ([^|]+) \\| (\\d+)/(\\d+) \\|", ite_after.split(ITER_TITLE)[-1])
if len(rows) != 7:
    die(u"本轮七维表读到 %d 行（要 7 行）⇒ 曲线仪器不会给数" % len(rows))
if any(mx != u"15" for _, _, mx in rows):
    die(u"七维表里出现了非 /15 的量纲：%s" % [r[2] for r in rows])
if [int(v) for _, v, _ in rows] != SEVEN:
    die(u"七维表与 SEVEN 不一致：%s vs %s" % ([int(v) for _, v, _ in rows], SEVEN))
print(u"R336_SEVEN 合计=%d/%d 行=%d" % (sum(SEVEN), SEVEN_MAX, len(rows)))

bt2, brc2 = sh([sys.executable, u"-m", u"unittest", u"discover", u"-s", u"scripts/tests"])
BATT2 = (re.findall(r"Ran (\d+) tests", bt2) or [u"?"])[-1]
BATT2_SKIP = (re.findall(r"skipped=(\d+)", bt2) or [u"0"])[-1]
POST_RED = sorted(set(re.findall(u"(?m)^(?:FAIL|ERROR): (\\w+)", bt2)))
if brc2 != 0:
    die(u"落盘之后脚本电池仍是红的（Ran=%s，红=%s）—— 登记窗口那两朵必须自己消失：%s"
        % (BATT2, POST_RED, bt2.strip()[-900:]))

ck, ckc = sh([sys.executable, STREAK, u"--check"])
if ckc != 0:
    die(u"连读门不认这版台账：" + ck.strip()[-500:])
STREAK_LINE = ck.strip().splitlines()[-1]

cvc, cvc_rc = sh([sys.executable, CURVE])
if cvc_rc != 0 or u"GAPS=none" not in cvc:
    die(u"落盘之后曲线尺不干净：" + cvc.strip()[-300:])
scores = dict((int(k), int(v)) for k, v in
              re.findall(r"(\\d+)=(\\d+)", (re.findall(r"(?m)^SCORES_BY_ROUND .*$", cvc) or [u""])[-1]))
DERIVED = s(scores.get(ITER_N, u"没解析到"))

rf, rfc = sh([sys.executable, FRESH])
if rfc != 0 or u"REFUSED" in rf:
    die(u"报告 §1 刷新器第二遍不干净：%s" % rf.strip()[-300:])
chk, chkc = sh([sys.executable, u"-m", u"unittest", u"-v",
                u"test_final_report_headline.FinalReportHeadlineTests."
                u"test_the_headline_cells_agree_with_the_live_ledgers"],
               cwd=os.path.join(ROOT, u"scripts", u"tests"))
if chkc != 0:
    die(u"报告标题那几格与台账不同源：" + chk.strip()[-400:])

print(u"R336_LEDGERS_OK 产品=%s 文件 U=%d…%d(%d 条) D=%d BACKLOG 最大=%d 刀=%s(%s) "
      u"电池=%s→%s(skip %s) 帧=%s 全量卷=%s/%s/%s 派生=%s"
      % (PRODUCT_N, UA, UMAX, udefs, D1, B_TITLE,
         by_name[u"mutate_r336"][1], ARMS_NEW[-1], BATT, BATT2, BATT2_SKIP,
         FRAME_N, FULL_RUN, FULL_SKIP, FULL_FAIL, DERIVED))
print(u"R336_ROWS " + ROWS_LINE)
print(u"R336_GATE " + GATE_FULL)
print(u"R336_TABLE " + TABLE_SUMMARY)
print(u"R336_PRECHECK tables=%s covered=%s bad=%s arms(files=%s,arms=%s,dupes=%s)"
      % (PRE[0], PRE[1], PRE[2], ARM_TOTAL[0], ARM_TOTAL[1], ARM_TOTAL[2]))
print(u"R336_STREAK 上一轮格=%s 本轮格=%s 门=%s" % (STREAK_N, STREAK_GIT, STREAK_LINE))
print(u"R336_SOURCES " + SRC_LINE)
print(u"R336_MD 固定=%s 边际=%s cap字符=%s cap耗时=%s 判定=%s"
      % (MD_FIXED, MD_MARGINAL, MD_CAP_CHARS, MD_BIG, MD_VERDICT))
print(u"R336_ALT 保留=%s 静默=%s 无alt删净=%s 尖括号=%s"
      % (ALT_KEPT, ALT_SILENT, ALT_NODESC, ALT_ANGLE))
