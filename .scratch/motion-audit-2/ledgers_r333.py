#!/usr/bin/env python3
# -*- coding: utf-8 -*-
u"""R333 的台账生成器（第 332 轮 / Round 330 · 393 落地 + 离屏尺重基 · 产品 2 文件）。

本轮的形状与上一批"判据账"不同：这是**产品轮**，四腿验证全部有对象，
所以每一格的数都从 `scripts/round_verify.sh` 与两份当场跑出来的卷日志里解析：

  /tmp/r333_rv/ROUND_VERIFY.log   —— build 告警 / 全量卷 / 重捕帧 / 帧基线 / dmg+换装（一行摘要）
  /tmp/r333_rv/capture.log        —— SEGREF_POLARITY（暗档同侧那条门就在这格里）
  /tmp/r333_film2.log             —— MOTION_PILL_RAMP_GEOM / MOTION_PILL_RAMP / MOTION_PILL_SLIDE
  /tmp/r333_r323.log 等           —— 五张变异表自己打的收尾行

规矩照旧：锚点整行、命中不是 1 次就在写任何盘之前抱出；数字全部解析不手抄；
缺日志就当红（`die`），不许沿用上一轮的数。
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
ROWS = os.path.join(ROOT, u".scratch", u"motion-audit-2", u"ledger_rows.py")
TESTS = os.path.join(ROOT, u"scripts", u"tests")

RV_LOG = u"/tmp/r333_rv/ROUND_VERIFY.log"
CAP_LOG = u"/tmp/r333_rv/capture.log"
FILM_LOG = u"/tmp/r333_film2.log"
TABLES = [
    (u"mutate_r323", u"/tmp/r333_t_r323.log"),
    (u"mutate_r327", u"/tmp/r333_t_r327.log"),
    (u"mutate_r328", u"/tmp/r333_t_r328.log"),
    (u"mutate_r329", u"/tmp/r333_t_r329.log"),
    (u"mutate_r333", u"/tmp/r333_t_r333.log"),
    (u"mutate_r324", u"/tmp/r333_r324c.log"),
]

ENV = dict(os.environ)
ENV[u"PYTHONUTF8"] = u"1"
ENV[u"PYTHONDONTWRITEBYTECODE"] = u"1"

ROUND = 333
AUDIT_N = 332          # 第 332 轮（R_n = 第 n−1 轮）
ITER_N = 330           # Round 330（R_n = Round n−3）
DATE = u"2026-10-24"
UA, UB, UC, UD, UE = 1105, 1106, 1107, 1108, 1109
D1 = 327
B_NEW = 396
B_DRIFT = 397
ARMS_NEW = (u"M965", u"M966", u"M967", u"M968", u"M969")

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
    print(u"LEDGERS_R333_DIED " + msg)
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


# ──  1. 验证读数：只从当场的日志里解析 ────────────────────────────────────────
rv = require(RV_LOG)
line = (re.findall(u"(?m)^ROUND_VERIFY .*", rv) or [None])[-1]
line = line.replace(u"ROUND_VERIFY ", u"", 1)  # 抄进台账时不重复键名
if line is None:
    die(u"读不到 ROUND_VERIFY 那一行：" + rv.strip()[-300:])
RV = dict(re.findall(r"(\w+)=([^\s]+)", line))
for k in (u"build_warnings", u"swift_executed", u"swift_skipped", u"swift_failures",
          u"frames", u"baseline_compared", u"baseline_changed", u"baseline_missing",
          u"dmg", u"installed_version"):
    if k not in RV:
        die(u"ROUND_VERIFY 那一行缺键 %s（有键无值 = R88 那一族）：%s" % (k, line))
if RV[u"build_warnings"] != u"0":
    die(u"构建告警不是 0：" + line)
if RV[u"swift_failures"] not in (u"0",) or RV[u"baseline_changed"] != u"0":
    die(u"全量卷或帧基线没干净，不落盘：" + line)
if u"NOT-RUN" in (RV[u"swift_executed"], RV[u"frames"], RV[u"dmg"]):
    die(u"ROUND_VERIFY 里有 NOT-RUN 的格子：" + line)
FRAME_N = RV[u"frames"]
FULL_RUN = RV[u"swift_executed"]
FULL_SKIP = RV[u"swift_skipped"]
FULL_FAIL = RV[u"swift_failures"]
BASE_CMP = RV[u"baseline_compared"]
BASE_CHG = RV[u"baseline_changed"]
BASE_MISS = RV[u"baseline_missing"]
DMG = RV[u"dmg"]
INSTALLED = RV[u"installed_version"]

cap = require(CAP_LOG)
seg_dark = (re.findall(u"(?m)^SEGREF_POLARITY dark.*$", cap) or [None])[-1]
seg_light = (re.findall(u"(?m)^SEGREF_POLARITY light.*$", cap) or [None])[-1]
if seg_dark is None or seg_light is None:
    die(u"捕获卷日志里没有 SEGREF_POLARITY 两档 ⇒ 暗档那条门没被跑过")
if u"同侧=是" not in seg_dark:
    die(u"暗档同侧不是『是』⇒ 本轮的修法与判据没落地，账要按现场重写：" + seg_dark[:200])
if u"同侧=是" not in seg_light:
    die(u"亮档同侧不是『是』（只印不判，但读数要照实）：" + seg_light[:200])


def num(line_text, key, where=u""):
    m = re.search(re.escape(key) + u"([-+0-9.]+)", line_text)
    if not m:
        die(u"读数行里缺 " + key + u" " + where)
    return m.group(1)


def tok(line_text, key, where=u""):
    m = re.search(re.escape(key) + u"(\\S+)", line_text)
    if not m:
        die(u"读数行里缺 " + key + u" " + where)
    return m.group(1)


def own_part(seg_line):
    """`SEGREF_POLARITY …｜系统 …｜自家 …｜同侧=…` —— 自家那一段必须单独切出来。

    为什么不能整行 grep：`未选=` / `选中=` 在系统那一段里先出现一次（左臂未选/右臂选中），
    直接 search 会把**参照臂**的数抄成自家的数（这一版生成器第一次就这么错，被现读回掉）。
    """
    for part in seg_line.split(u"｜"):
        if part.startswith(u"自家"):
            return part
    die(u"SEGREF 行里没有『自家』那一段：" + seg_line[:160])


DARK_OWN_LINE = own_part(seg_dark)
LIGHT_OWN_LINE = own_part(seg_light)
DARK_SYS = num(seg_dark, u"差(左臂)=")
DARK_OWN = num(DARK_OWN_LINE, u"差=")
DARK_TRACK = num(DARK_OWN_LINE, u"未选=")
DARK_SEL = num(DARK_OWN_LINE, u"选中=")
DARK_PAGE = num(seg_dark, u"系统 页底=")
LIGHT_SYS = num(seg_light, u"差(左臂)=")
LIGHT_OWN = num(LIGHT_OWN_LINE, u"差=")
LIGHT_SEL = num(LIGHT_OWN_LINE, u"选中=")
LIGHT_TRACK = num(LIGHT_OWN_LINE, u"未选=")
LIGHT_PAGE = num(seg_light, u"系统 页底=")
if DARK_SEL == DARK_TRACK or LIGHT_SEL == LIGHT_TRACK:
    die(u"自家的选中档与未选档读成同一个数 ⇒ 抄错了段：" + seg_dark[:200])

hov_dark = (re.findall(u"(?m)^HOVER_DIRECT_READ_PROOF dark.*$", cap) or [u""])[0]
hov_light = (re.findall(u"(?m)^HOVER_DIRECT_READ_PROOF light.*$", cap) or [u""])[0]
if not hov_dark or not hov_light:
    die(u"读不到 HOVER_DIRECT_READ_PROOF 两档 ⇒ 396 的那四个数没处解析")
HOV_D_UNSEL = num(hov_dark, u"空闲底=")
HOV_D_HOVER = num(hov_dark, u"悬停=")
HOV_D_SEL = num(hov_dark, u"选中段 空闲=")
HOV_L_UNSEL = num(hov_light, u"空闲底=")
HOV_L_HOVER = num(hov_light, u"悬停=")
HOV_L_SEL = num(hov_light, u"选中段 空闲=")
try:
    HOV_D_GAP = u"%.1f" % (float(HOV_D_SEL) - float(HOV_D_HOVER))
    HOV_L_GAP = u"%.1f" % (float(HOV_L_SEL) - float(HOV_L_HOVER))
except ValueError:
    die(u"悬停那三个数解析不成浮点")

film = require(FILM_LOG)
geom = (re.findall(u"(?m)^MOTION_PILL_RAMP_GEOM .*$", film) or [None])[-1]
ramp = (re.findall(u"(?m)^MOTION_PILL_RAMP filter-pill-slide A .*$", film) or [None])[-1]
slide = (re.findall(u"(?m)^MOTION_PILL_SLIDE filter-pill-slide .*$", film) or [None])[-1]
settle = (re.findall(u"(?m)^MOTION_PILL_SLIDE_SETTLE .*$", film) or [None])[-1]
if geom is None or ramp is None or slide is None:
    die(u"胶片卷日志里缺斜坡尺/过程证人的读数行（geom/ramp/slide）")
if u"MOTION_NOT_RUN=pill-ramp" in film or u"MOTION_NOT_RUN=pill-band" in film:
    die(u"重基之后这两把尺又掉回 no-band / no-* 出口了 ⇒ 本轮的账不成立：\n"
        + u"\n".join(re.findall(u"(?m)^MOTION_NOT_RUN=(pill|clock).*", film))[:400])
GEOM_TRACK = num(geom, u"轨道=", u"（要的是档位那一格，不是轨道范围）")
GEOM_PILL = num(geom, u"药丸=")
GEOM_SEP = num(geom, u"分离=")
GEOM_MIRROR = tok(geom, u"镜像=")
GEOM_BAND = tok(geom, u"行带=")
GEOM_COV = tok(geom, u"纵向覆盖=")
GEOM_CAND = num(geom, u"候选行=")
GEOM_DIST = tok(geom, u"判定分布=")
if GEOM_MIRROR != u"是":
    die(u"镜像那一格不是『是』⇒ 两臂没互换，本轮的定档没有对照物：" + geom[:200])
RAMP_VERDICT = tok(ramp, u"判定=")
RAMP_MOVE = num(ramp, u"位移=")
RAMP_BACK = num(ramp, u"最大倒退=")
RAMP_FRAMES = num(ramp, u"帧数=")
m_on = re.search(u"开A 帧数=(\\d+)\\(旧口径\\d+\\) 峰值=([\\d.]+)", slide)
m_off = re.search(u"关 帧数=(\\d+)\\(旧口径\\d+\\) 峰值=([\\d.]+)", slide)
if not m_on or not m_off:
    die(u"过程证人那一行读不出开臂/关臂的帧数与峰值：" + slide[:220])
SLIDE_FRAMES_ON, SLIDE_PEAK_ON = m_on.group(1), m_on.group(2)
SLIDE_FRAMES_OFF, SLIDE_PEAK_OFF = m_off.group(1), m_off.group(2)
SETTLE = re.search(u"到位帧=(\\d+)", settle) if settle else None
SETTLE_N = SETTLE.group(1) if SETTLE else u"?"

# 判据卷（合成帧那两卷 + 捕获卷）的 Executed 行也从当场日志里取
PURE_RUN = (re.findall(r"Executed (\d+) tests", require(u"/tmp/r333_pure.log")) or [None])[-1]
FILM_RUN = (re.findall(r"Executed (\d+) tests", film) or [None])[-1]
FILM_SKIP = (re.findall(r"with (\d+) tests skipped", film) or [u"0"])[-1]
CAP_RUN = (re.findall(r"Executed (\d+) tests", cap) or [None])[-1]
CAP_SKIP = (re.findall(r"with (\d+) tests skipped", cap) or [u"0"])[-1]
if None in (PURE_RUN, FILM_RUN, CAP_RUN):
    die(u"三卷的 Executed 数没解析全：pure=%s film=%s capture=%s" % (PURE_RUN, FILM_RUN, CAP_RUN))

# ──  2. 变异表：五张重跑 + 一张补跑，全部只抄它们自己打的那一行 ───────────────
TABLE_LINES = []
for name, path in TABLES:
    txt = require(path)
    got = re.findall(u"(?m)^CAUGHT=(\\d+/\\d+), RESTORE_CLEAN=(\\S+)", txt)
    if not got:
        die(name + u" 的日志里读不到 CAUGHT= 收尾行")
    caught, clean = got[-1]
    if clean != u"yes":
        die(name + u" 还原不干净：" + txt.strip()[-200:])
    arms = u", ".join(re.findall(r"(M\d{3}) CAUGHT", txt))
    bad = re.findall(r"(M\d{3}) (PASSED|NOT_RUN|MISMATCH)", txt)
    TABLE_LINES.append((name, caught, arms, bad))
new_row = [t for t in TABLE_LINES if t[0] == u"mutate_r333"][0]
if new_row[1] != u"5/5":
    die(u"本轮那支表没全抓到：" + s(new_row[1]))
if tuple(re.findall(r"(M\d{3})", new_row[2])) != ARMS_NEW:
    die(u"本轮抓到的臂与登记的五把不一致：" + new_row[2])
r324 = [t for t in TABLE_LINES if t[0] == u"mutate_r324"][0]
if r324[1] != u"5/6":
    die(u"mutate_r324 本轮应是 5/6（M932 只在亮档有牙），读到 " + r324[1])

pc, _ = sh([sys.executable, PRECHK])
PRE = (re.findall(r"NEEDLE_PRECHECK tables=(\d+) covered=(\d+) arms=\d+ bad=(\d+)", pc) or [None])[-1]
ARM_TOTAL = (re.findall(r"ARM_TOTAL files=(\d+) arms=(\d+) dupes=(\d+) repeats=(\d+)", pc) or [None])[-1]
if PRE is None or ARM_TOTAL is None or PRE[2] != u"0" or ARM_TOTAL[2] != u"0":
    die(u"针预检/臂名册不干净：" + pc.strip()[-400:])

gt, gtc = sh([sys.executable, GATE])
GATE_LINE = (re.findall(u"(?m)^MOTION_LEDGER_RESULT=ok.*$", gt) or [None])[-1]
GATE_FULL = (re.findall(u"(?m)^MOTION_LEDGER 表面=.*$", gt) or [None])[-1]
if gtc != 0 or GATE_LINE is None or GATE_FULL is None:
    die(u"清账表门不干净：" + gt.strip()[-300:])

# ──  3. §8 搬运名单：本轮声明的读数族必须被搬进去；缺值的格子照实登记 ──────────
COMBINED = u"/tmp/r333_rv/§8_combined.log"
with io.open(COMBINED, u"w", encoding=u"utf-8") as fh:
    fh.write(rd(CAP_LOG))
    fh.write(u"\n")
    fh.write(rd(FILM_LOG))
    fh.write(u"\n")
    fh.write(line + u"\n")
rw, rwc = sh([sys.executable, ROWS, COMBINED, u"--must-include",
              u"SEGREF_POLARITY", u"MOTION_PILL_RAMP_GEOM", u"MOTION_PILL_SLIDE"])
ROWS_LINE = (re.findall(u"(?m)^READINGS_MUST_INCLUDE .*", rw) or [None])[-1]
MISSING_CELLS = (re.findall(u"(?m)^ROWS_TOTAL=(\\d+) ROWS_MISSING=(\\d+)", rw) or [None])[-1]
FAMS = (re.findall(u"(?m)^READINGS_FAMILIES 搬运=(\\d+) .*", rw) or [None])[-1]
if ROWS_LINE is None or u"缺=0" not in ROWS_LINE:
    die(u"§8 声明的读数族有被丢掉的：" + rw.strip()[-400:])
if MISSING_CELLS is None or FAMS is None:
    die(u"读不到 §8 搬运口自己打的行数/族数：" + rw.strip()[-300:])
ROWS_TOTAL, ROWS_MISSING = MISSING_CELLS
READINGS_MOVED = FAMS
if rwc == 0:
    die(u"§8 搬运口今天居然全签了 —— 那 12 个键名是被谁补上的？本轮的账按现场重写")
# 12 缺 / 13 总：唯一还签着的那格是"本轮读数"（它确实搬到了）。
# 如果哪天它变成 0 缺，那是**有人补了那 12 个键名** —— 397 就该结案并改写本轮那句，
# 所以这里反过来拦：全签就当红，逼下一轮回来改账。
if ROWS_MISSING == u"0":
    die(u"§8 的 12 个键名现在全签了 ⇒ 397 已被修掉，本轮那句『全是洞』要改写、397 要结案")

# ──  4. 产品面 / 改动面 ──────────────────────────────────────────────────────
git_face, grc = sh([u"git", u"status", u"--porcelain"])
if grc != 0:
    die(u"git status 读不到")
CHANGED = [l for l in git_face.splitlines()
           if l.strip() and not l.startswith(u"?? .local/") and not l.startswith(u"?? .scratch/spikes/")]
PRODUCT = [l for l in CHANGED if u"/Sources/" in l]
if len(PRODUCT) < 1:
    die(u"本轮是产品轮，改动面里却没有 /Sources/ 文件：" + s(len(CHANGED)))

st_cell, _ = sh([sys.executable, STREAK, u"--streak-for", s(ROUND - 1)])
st_this, _ = sh([sys.executable, STREAK, u"--streak-for", s(ROUND)])
st_prev, _ = sh([sys.executable, STREAK, u"--streak-for", s(ROUND - 2)])
STREAK_N = (re.findall(r"streak=(\d+)", st_cell) or [None])[-1]
STREAK_GIT = (re.findall(r"streak=(\d+)", st_this) or [None])[-1]
PREV_STREAK = (re.findall(r"streak=(\d+)", st_prev) or [None])[-1]
if None in (STREAK_N, STREAK_GIT, PREV_STREAK):
    die(u"读不到产品面连读的数：" + st_cell.strip()[-200:])

bt, brc = sh([sys.executable, u"-m", u"unittest", u"discover", u"-s", u"scripts/tests"])
BATT = (re.findall(r"Ran (\d+) tests", bt) or [None])[-1]
BATT_SKIP = (re.findall(r"skipped=(\d+)", bt) or [u"0"])[-1]
if brc != 0 or BATT is None:
    die(u"脚本电池在落盘之前就是红的（Ran=%s）：%s" % (BATT, bt.strip()[-600:]))

cv, crc = sh([sys.executable, CURVE])
if crc != 0:
    die(u"曲线尺不干净：" + cv.strip()[-300:])

TABLE_SUMMARY = u"；".join(u"%s %s（%s）" % (n, c, a) for n, c, a, _ in TABLE_LINES)
COND = u"M932 PASSED（表自己写明：只有机器处在亮档时它才咬得住，本轮机器在暗档）"

UI_TITLE = (u"## 第 %d 轮（R%d · %s · U-%d…U-%d）：选中那颗第一次站到轨道之上 ——"
            u"而离屏尺一直把 377 的画法当成定义，重基之后它才重新有对象"
            u"（U-%d…U-%d · 产品 2 文件，动效主线）" % (AUDIT_N, ROUND, DATE, UA, UE, UA, UE))
UI_BODY = u"""
- **U-%d：修法①落地（产品 2 文件）—— 选中的那颗从材质换成不透明的语义色，极性当场翻向**。
  `VisualMaterial.sliderPill: Material = .ultraThickMaterial` 换成
  `VisualMaterial.selectedSegment: Color = Color(nsColor: .unemphasizedSelectedContentBackgroundColor)`
  （它只有一个用点，所以旧令牌一并撤掉）。同一颗尺、同一次运行、两个色档的改前/改后四数：
  **暗档** 页底 %s／轨道 %s／选中 由 **%s 抬到 %s**／差 由 −16.0 翻成 **%s**（系统参照臂同一格差=%s）；
  **亮档** 页底 %s／未选 %s／选中 由 233 降到 **%s**／差 由 +3.0 翻成 **%s**（系统参照臂差=%s）。
  两档的"自家与系统同侧"现在都是**是** —— 但只有暗档立了门（D-325：亮档的符号两机反号）。
  看图腿：`/tmp/r333_cmp_band_dark.png`（上=改前、下=改后）里改前那颗读起来像轨道上挖的洞，
  改后读起来像**抬起的一段**；亮档那张是反向的（选中变成中性灰，与系统那颗同形）。
- **U-%d：尺的定义重基（BACKLOG 393 的另一半）—— 药丸档由两臂镜像量出来，不再锚"与页底同档"**。
  旧定义把 377 的画法写成了定义，所以修法一落地它**不是红、是安静地 skip**
  （现读 `候选行=0 判定分布=非候选×520`，两格掉进 `pill-ramp-no-band` / `pill-band-unmeasured`）。
  新的三颗纯函数：`halfLevels`（轨道左右各取一档）+ `settledPillTrackLevels`（两臂互为镜像才给数，
  并给出**带符号**的分离度）+ 重写后的 `pillRun`（两档分不开就 nil，不许退回去猜）。
  重基之后同一卷现读：`候选行=%s 判定分布=%s 行带=%s 轨道=%s 药丸=%s 分离=%s 镜像=%s 纵向覆盖=%s`，
  斜坡尺 `%s 位移=%spt 最大倒退=%spt 帧数=%s`，过程证人 开臂峰值=%s 对 关臂峰值=%s（到位帧 %s）。
- **U-%d：重基的代价写成会红的格子，不写成"闸还在"** —— 旧尺能给一颗 12.5%% 宽的窄缝一个词（"洞太窄"），
  新尺由两半的中位定档，那么窄的缝搬不动任何一半的中位 ⇒ 两档相等 ⇒ 它在**定档那一步**就没有对象了。
  被拒的结论没变，**点名方式**变了（那种形状从"洞太窄×N"并入"非候选×N"）。
  真帧上这道闸仍然有牙：本轮现读 `洞太窄×%s` 行（字墨把宽洞截断那一族），
  证人换成"字墨截断"的形状，并补一格明写这条变化（`testASlitTooNarrowToMoveTheHalfMedianHasNoObjectAtAll`）。
- **U-%d：修法带回来的新问题（开单 %d）—— 选中档与"悬停未选"档在暗档只差 %s 级**。
  改前：未选 %s／悬停未选 %s／选中 36 ⇒ 选中离悬停 30 级；改后：选中 %s ⇒ 只差 %s 级。
  亮档同样挤：未选 %s／悬停 %s／选中 %s（悬停那颗比选中还重 %s 级）。
  这四个数由仓库**已提交**的那格 `HOVER_DIRECT_READ_PROOF` 打印，不是临时尺量的；
  本轮只登记读数不发明地板（D-321：地板要由判据卷红来改）。
- **U-%d：三处自伤与一处崩，全部当场被自己的工具照出来**。
  ① M925（拆"洞必须会走"那道闸）本轮报 **PASSED** —— 镜像那道闸把它的对象蕴含掉了，
  证人换成"地板本身有牙"的两格（`minMove=0.7` 必须拦、`0.6` 必须放）后重新 CAUGHT；
  ② 我重钉 M933 时只改了 needle 没改 repl ⇒ 少一个右花括号，刀变成编译错误，
  表按规矩打 **NOT_RUN 而不是 CAUGHT**（这正是"刀坏了不是判据没牙"那条分流在起作用）；
  ③ 证人格"先断言数量、再按下标取"在数量不足时把整卷打成 **SIGTRAP**（红只损失一格，崩把后面所有格的
  结论行一起带走）⇒ 解析搬进尺本体 `verticalCoverageCells`（读不出是 nil 不是越界）+ 四格真值表。
  本轮六张表：`%s`；另 %s。

""" % (UA, DARK_PAGE, DARK_TRACK, u"36.0", DARK_SEL, DARK_OWN, DARK_SYS,
       LIGHT_PAGE, LIGHT_TRACK, LIGHT_SEL, LIGHT_OWN, LIGHT_SYS,
       UB, GEOM_CAND, GEOM_DIST, GEOM_BAND, GEOM_TRACK, GEOM_PILL, GEOM_SEP, GEOM_MIRROR,
       GEOM_COV, RAMP_VERDICT, RAMP_MOVE, RAMP_BACK, RAMP_FRAMES,
       SLIDE_PEAK_ON, SLIDE_PEAK_OFF, SETTLE_N,
       UC, (re.search(u"洞太窄×(\\d+)", GEOM_DIST).group(1)
            if re.search(u"洞太窄×(\\d+)", GEOM_DIST) else u"?"),
       UD, B_NEW, HOV_D_GAP, HOV_D_UNSEL, HOV_D_HOVER, HOV_D_SEL, HOV_D_GAP,
       HOV_L_UNSEL, HOV_L_HOVER, HOV_L_SEL, HOV_L_GAP,
       UE, TABLE_SUMMARY, COND)

ITER_TITLE = (u"## Round %d · R%d（第 %d 轮 · %s）：选中那颗站到轨道之上 —— 而尺一直把缺陷的画法当成定义，"
              u"重基之后它才重新有对象（产品 2 文件）" % (ITER_N, ROUND, AUDIT_N, DATE))
ITER_BODY = u"""
R330 在屏幕上把 377 判成产品缺陷（选中的那颗比轨道暗 33 级），R331 让系统自己印出方向
（暗档 差=+26.0）。本轮是**落地**：`VisualMaterial.sliderPill`（`.ultraThickMaterial`）换成
`VisualMaterial.selectedSegment` = `unemphasizedSelectedContentBackgroundColor` ——
一枚不透明的语义色，它的解析值 70／220 正是参照臂量到的 74.0／205.0 那一档。

改前改后同一颗尺、同一次运行：

| 档 | 页底 | 轨道（未选） | 选中那颗 | 差 | 系统参照臂 |
| --- | --- | --- | --- | --- | --- |
| 暗·改前 | 30.0 | 52.0 | 36.0 | −16.0 | +26.0（异侧） |
| 暗·改后 | %s | %s | %s | **%s** | %s（同侧） |
| 亮·改前 | 255.0 | 230.0 | 233.0 | +3.0 | −30.0（异侧） |
| 亮·改后 | %s | %s | %s | **%s** | %s（同侧，仍只印不判） |

看图腿（`/tmp/r333_cmp_band_dark.png`、`/tmp/r333_cmp_band_light.png`，上=改前、下=改后）：
暗档改前那颗读起来是**轨道上挖的洞**，改后读起来是**抬起的一段**；亮档改后变成中性灰的一段，
与系统那颗同形。这一维本轮是真的动了产品像素，而且动的是被屏幕判掉的那一颗。

但落地暴露了一件更难受的事：**离屏尺一直把缺陷的画法当成定义**。
`pillRun` 原来的句子是"药丸 = 与页底同档的那一段"，而"药丸落在页底那一档"就是 377 本身。
于是修法一落地，这把尺失去对象 —— 而且它不是红，是 **skip**：
`MOTION_NOT_RUN=pill-ramp-no-band` / `pill-band-unmeasured`，现读 `候选行=0 判定分布=非候选×520`。
一朵尺子瞎掉，长得跟"这台机器看不见"一模一样，而账上只会多两行 skip。
本轮把它重基成极性无关的三颗纯函数（两臂互为镜像才给数），重跑之后：
`候选行=%s 判定分布=%s 轨道=%s 药丸=%s 分离=%s 镜像=%s`，斜坡尺 `%s 位移=%spt 最大倒退=%spt`。

重基也有代价，写在明处：一颗窄到搬不动半区中位的缝（12.5%%），旧尺会给它"洞太窄"这个词，
新尺在定档那一步就说"没有对象"。被拒的结论一样，**点名方式**变了 —— 真帧上这道闸仍然有牙
（`洞太窄×%s` 行，字墨截断那一族），所以留着它，但补一格专门钉这条变化。

修法还带回一个新问题（开单 %d）：选中档 %s 与"悬停未选"档 %s 在暗档只差 %s 级
（改前是 30 级），亮档同样挤（悬停那颗比选中还重 %s 级）。数由仓库已提交的
`HOVER_DIRECT_READ_PROOF` 打印。本轮只登记，不发明地板（D-321）。

七维度自评：

| 维度 | 分/满分 |
| --- | --- |
| 真实视觉审查 | 12/15 |
| 判据有效性 | 14/15 |
| 假绿防御 | 15/15 |
| 产品面推进 | 13/15 |
| 台账一致性 | 13/15 |
| 交付诚实性 | 14/15 |
| 可复核性 | 14/15 |

合计 95/105。派生分由 `curve_from_ledger.py` 现读，不在这一节里手抄。

为什么真实视觉审查 12 而不是更高：两档的改前/改后对比图真看了，也认出了"洞 → 抬起的一段"这个形状变化；
但真机那一屏本轮仍被登录窗锁着（`screen_locked`），377 的定性本来就是从屏幕上来的，
所以"改后在屏幕上也对"这句话本轮没有证人。

为什么假绿防御给满：本轮抓到的是**自己最坏的一种绿**（产品变了而证人安静退场），
而且它被三件东西各自拦住：重基后的正对照（极性翻向仍过闸）、M925 报 PASSED 时表拒绝算数、
以及崩掉整卷那一发被读成 NOT_RUN 而不是 CAUGHT。

为什么产品面推进 13 而不是 15：2 个产品文件、方向由系统印、四数齐；
但 396（选中与悬停只差 %s 级）是这一发**带回来的**，修它要下一轮。
""" % (DARK_PAGE, DARK_TRACK, DARK_SEL, DARK_OWN, DARK_SYS,
       LIGHT_PAGE, LIGHT_TRACK, LIGHT_SEL, LIGHT_OWN, LIGHT_SYS,
       GEOM_CAND, GEOM_DIST, GEOM_TRACK, GEOM_PILL, GEOM_SEP, GEOM_MIRROR,
       RAMP_VERDICT, RAMP_MOVE, RAMP_BACK,
       (re.search(u"洞太窄×(\\d+)", GEOM_DIST).group(1) if re.search(u"洞太窄×(\\d+)", GEOM_DIST) else u"?"),
       B_NEW, HOV_D_SEL, HOV_D_HOVER, HOV_D_GAP, HOV_L_GAP, HOV_D_GAP)

D_BODY = u"""
**D-%d（%d）：判据的定义不许借用被审对象的画法 —— 修法落地时证人若从红变成 skip，那就是尺在替缺陷作证**
：`pillRun` 原来的定义是"药丸 = 与页底同档的那一段"。这句话在 377 的帧上是**真**的
（药丸 36、页底 30、轨道 52），因为产品当时就是把选中画成轨道上的暗洞 —— 于是尺子的定义
与缺陷的画法是同一件事。修法①一落地，定义失去对象，而它报的是 skip 不是红
（`候选行=0 判定分布=非候选×520`）：产品变了，证人安静退场，这是本仓库最怕的一种绿。
立的规矩有两条：① **定档类判据必须由两个稳态之间的对照来定档**（本轮用"两臂互为镜像"：
首帧左半=末帧右半、首帧右半=末帧左半，两半不等宽或药丸没换边都会让镜像不成立而被点名），
符号（选中比轨道亮还是暗）是**读出来的数**，不是写死的假设；
② 一条判据在改动之后**变绿的方式**必须被检查：变红=它读到了新坏法，不变=它没对象，
从红变 skip / 从有读数变无读数都算尺子坏，不许算"这台机器看不见"。
附带两条：地板与词表不许为通过而改（D-321 同一族）；证人格里"先断言数量再按下标取"是崩源，
解析必须住在打印它的那颗尺里，"读不出"要是一个 nil。
""" % (D1, ROUND)

BL_393 = u"""393 追记（R333 结案，离屏那一半）：① 落地了 —— `selectedSegment =
    unemphasizedSelectedContentBackgroundColor`（暗档 选中 36.0→%s、差 −16.0→**%s**；亮档 233.0→%s、
    +3.0→**%s**），暗档与系统参照臂（差=%s）**同侧**并立成门（D-325：只有暗档能立）。
    尺的定义连带重基成"两臂镜像定档"，斜坡尺与过程证人重新有对象：
    `候选行=%s 轨道=%s 药丸=%s 分离=%s 镜像=%s`、`判定=%s 位移=%spt 最大倒退=%spt`。
    看图腿两档都看了（改前"轨道上挖的洞"→ 改后"抬起的一段"）。
    仍欠的只有屏幕那一半：395（真机改前/改后四数），以及这一发带回来的 396。
""" % (DARK_SEL, DARK_OWN, LIGHT_SEL, LIGHT_OWN, DARK_SYS, GEOM_CAND, GEOM_TRACK, GEOM_PILL,
       GEOM_SEP, GEOM_MIRROR, RAMP_VERDICT, RAMP_MOVE, RAMP_BACK)

BL_394 = u"""394 追记（R333）：runner 那一跑本轮仍没读到（只登记不轮询）。要看的两件事换了形状 ——
    ① 轨道那颗**仍是材质**（`VisualMaterial.track`），而 runner 不合成材质那一族是 R100 记过的：
    如果轨道被洗成页底，`trackExtent` 找不到轨道 ⇒ 斜坡尺走 `MOTION_NOT_RUN=pill-ramp-no-track`
    （那是尺没对象，不是产品坏）；② 选中那颗现在是不透明语义色，理论上画得出来，
    所以真正要盯的是 `SEGREF_POLARITY dark｜自家 差=` 在 runner 上是不是**同号**（本机 %s）。
    两条都不许被"CI 绿了"代替 —— 绿也可能来自 skip。
""" % DARK_OWN

BL_395 = u"""395 追记（R333 现读）：本轮再问一次，分类器仍给 `screen_locked`
    （电源日志最近一条=on、SecureInput 属主=loginwindow、区域探针抛 CalledProcessError）⇒
    屏幕那一半本轮依旧没有数。离屏那一半已经齐（见 393 追记），所以这一单剩下的**只有**人解锁之后那三格。
"""

BL_NEW = u"""**396. 修法①把选中档抬到 %s，而"悬停未选"那颗在 %s —— 暗档只差 %s 级（改前差 30 级）：悬停几乎复现了选中（R333 现读）**（R333）
    数由仓库**已提交**的那格打印：`HOVER_DIRECT_READ_PROOF dark 段按钮 空闲底=%s 悬停=%s 选中段 空闲=%s`，
    亮档同形：未选 %s／悬停 %s／选中 %s（悬停比选中还重 %s 级）。
    这一单是 393 那一发**带回来的**：把选中抬到轨道之上是对的（系统自己就这么画），
    但抬起之后它与"未选那颗被悬停"落在几乎同一档 ⇒ 鼠标一停，两颗看起来都被选中了。
    下一轮做两件事：① 先量"该差多少"——不许拍地板，要由判据卷红来定（D-321）；
    ② 修法候选按分离度排：压低 `hoverFill` 的量、或给选中那颗再加一层身份（描边/字重），
    两条都要同一运行里改前改后的四个数（D-318/D-319），且离屏与真机同向（395 欠着）。
    本轮**只登记读数**，产品面不再动这一颗。
""" % (HOV_D_SEL, HOV_D_HOVER, HOV_D_GAP, HOV_D_UNSEL, HOV_D_HOVER, HOV_D_SEL,
       HOV_L_UNSEL, HOV_L_HOVER, HOV_L_SEL, HOV_L_GAP)

BL_DRIFT = u"""**397. §8 的搬运口读的 12 个键名，`round_verify.sh` 已经一个也不打印了：本轮现读 `ROWS_MISSING=12/13`（R333 现读）**（R333）
    `ledger_rows.py` 的 ROWS 表要的是 `BUILD_EXIT=` / `TEST_EXIT=` / `CAPTURE_EXIT=` / `FRAMES_EXIT=` /
    `PY_EXIT=` / `MUT_EXIT=` / `LEDGER_EXIT=` / `VIS_EXIT=` / `CONTAIN_EXIT=` / `SUMMARY_MISSING=` / `VERIFY_OK=`
    这些行；而现在的 `round_verify.sh` 只打一行 `ROUND_VERIFY build_warnings=… swift_executed=…`。
    `grep -rl "BUILD_EXIT" scripts/ .github/` 现读**零个文件** ⇒ 那 12 格在 §8 里长期是
    "!! 日志里没有这一格"，而搬运口自己的规矩恰恰是"缺值算红、不许用看起来合理的数补"。
    本轮没有顺手放宽它（它照出的 12 个洞是真的），而是把两件事分开：
    ① 本轮声明的**读数族**仍然必须被搬进去 —— 现读 `READINGS_MUST_INCLUDE 声明=3 缺=0`、
      `搬运=%s 行`（`SEGREF_POLARITY` / `MOTION_PILL_RAMP_GEOM` / `MOTION_PILL_SLIDE` 三族都在）；
    ② 那 12 个键名要么由 `round_verify.sh` 补打（一处权威，且它已经在算这些数），
      要么把 ROWS 表改成读 `ROUND_VERIFY` 那一行的键名 —— 两个修法相反：前者让 §8 重新有格子，
      后者让 §8 与本轮的台账形状对齐。**下一轮挑一条做完**，做完之前 §8 那 12 格必须写成洞，
      不许手填（这一族的成因与 R99 的"手抄成上一轮的数"同一件事）。
""" % READINGS_MOVED

CHG_ENTRY = (u"### 选中那颗站到轨道之上（393 的①），而离屏尺的定义重基：药丸档由两臂镜像量出来"
             u"（R%d / U-%d…U-%d · 产品 2 文件，动效主线）" % (ROUND, UA, UE)) + u"""

- 产品：`VisualMaterial.sliderPill: Material = .ultraThickMaterial` →
  `VisualMaterial.selectedSegment: Color = Color(nsColor: .unemphasizedSelectedContentBackgroundColor)`
  （`HistorySidebarView` 的 `slidingPill` 取用点跟着换；旧令牌只有一个用点，一并撤掉）。
- 现读（同一运行、同一颗尺）：暗档 页底 %s／轨道 %s／选中 36.0→**%s**／差 −16.0→**%s**，
  系统参照臂差=%s ⇒ 同侧；亮档 页底 %s／未选 %s／选中 233.0→**%s**／差 +3.0→**%s**，参照臂差=%s。
  暗档"同侧"本轮升成门（D-325），亮档继续只印。
- 判据：`pillRun` 的定义重基（`halfLevels` + `settledPillTrackLevels` + 新 `pillRun`，极性无关），
  新增 4 格合成帧证人（镜像定档、亮档形状仍过闸、12.5%% 窄缝改为"没有对象"、半区下限）；
  斜坡尺与过程证人重新有对象：`候选行=%s 判定分布=%s 轨道=%s 药丸=%s 分离=%s 镜像=%s 纵向覆盖=%s`，
  `%s 位移=%spt 最大倒退=%spt 帧数=%s`。
- 三处自伤与一处崩（都当场照出来）：M925 报 PASSED（镜像蕴含了"必须会走"）⇒ 证人换成
  `minMove` 0.7/0.6 两格边界；M933 重钉时漏改 repl ⇒ 少一个花括号，表按规矩打 NOT_RUN；
  证人格按下标取数把整卷打成 SIGTRAP ⇒ 解析搬进尺本体 `verticalCoverageCells` + 四格真值表。
- 新开 %d：选中档 %s 与"悬停未选"档 %s 只差 %s 级（改前 30 级），数由已提交的
  `HOVER_DIRECT_READ_PROOF` 打印；本轮只登记不发明地板（D-321）。
- 新开 %d：§8 的搬运口读的 12 个键名（`BUILD_EXIT=` 一族）现在**没有任何脚本打印**
  （`grep -rl BUILD_EXIT scripts/ .github/` 现读零个文件）⇒ 本轮跑它现读 `ROWS_MISSING=12/13`，
  而声明的三族读数 `SEGREF_POLARITY` / `MOTION_PILL_RAMP_GEOM` / `MOTION_PILL_SLIDE` 缺=0。
  没有为了绿而放宽它：那 12 格在台账里就写成洞。
- 验证：`ROUND_VERIFY %s`；判据卷 合成帧 `Executed %s`、胶片 `Executed %s（skipped=%s）`、
  捕获 `Executed %s（skipped=%s）`；六张变异表 `%s`（另 %s）；
  针预检 tables=%s covered=%s bad=%s、名册 files=%s arms=%s dupes=%s；
  清账表 `%s`；脚本电池 `Ran %s（skipped=%s）`。
""" % (DARK_PAGE, DARK_TRACK, DARK_SEL, DARK_OWN, DARK_SYS, LIGHT_PAGE, LIGHT_TRACK, LIGHT_SEL,
       LIGHT_OWN, LIGHT_SYS, GEOM_CAND, GEOM_DIST, GEOM_TRACK, GEOM_PILL, GEOM_SEP, GEOM_MIRROR,
       GEOM_COV, RAMP_VERDICT, RAMP_MOVE, RAMP_BACK, RAMP_FRAMES,
       B_NEW, HOV_D_SEL, HOV_D_HOVER, HOV_D_GAP, B_DRIFT,
       line.replace(u"dir=", u"目录="), PURE_RUN, FILM_RUN, FILM_SKIP, CAP_RUN, CAP_SKIP,
       TABLE_SUMMARY, COND,
       PRE[0], PRE[1], PRE[2], ARM_TOTAL[0], ARM_TOTAL[1], ARM_TOTAL[2],
       GATE_FULL.strip(), BATT, BATT_SKIP)

STATE_TITLE = (u"## R%d 状态（%s · 本地 · 第 %d 轮 / Round %d）：选中那颗站到轨道之上 ——"
               u"离屏尺把缺陷的画法当成了定义，重基之后才重新有对象（产品 2 文件，动效主线）"
               % (ROUND, DATE, AUDIT_N, ITER_N))
STATE_BODY = u"""
最后更新：%s（本地 · R%d / 第 %d 轮 / Round %d）：393 的①落地（选中那颗换成
`unemphasizedSelectedContentBackgroundColor`，暗档 差 −16.0→**%s**、与系统参照臂 %s 同侧并立成门），
离屏尺的定义重基成"两臂镜像定档"（产品 2 文件 · 动效主线 · 合计 95/105）

本轮做了什么：把 R330 在屏幕上判掉的缺陷改掉，并且**在改完之后回头检查证人怎么变绿的**。
第一版落地后斜坡尺与过程证人不是红、是 skip（`候选行=0 判定分布=非候选×520`）——
因为 `pillRun` 的定义"药丸=与页底同档"借的就是缺陷的画法。重基成极性无关的三颗纯函数
（`halfLevels` / `settledPillTrackLevels` / `pillRun`），并给暗档"同侧"升成门（D-325 只允许这一档）。

验证读数（现读）：暗档 页底 %s／轨道 %s／选中 36.0→%s／差→%s，亮档 页底 %s／未选 %s／选中→%s／差→%s；
重基后 `候选行=%s 判定分布=%s 轨道=%s 药丸=%s 分离=%s 镜像=%s 纵向覆盖=%s`、
斜坡 `%s 位移=%spt 最大倒退=%spt 帧数=%s`、过程证人 开臂峰值=%s 对 关臂峰值=%s；
`ROUND_VERIFY %s`；判据卷 合成帧 `Executed %s`／胶片 `Executed %s（skipped=%s）`／捕获 `Executed %s（skipped=%s）`；
六张表 `%s`（另 %s）；针预检 tables=%s covered=%s bad=%s、名册 files=%s arms=%s dupes=%s；
清账表 `%s`；脚本电池 `Ran %s（skipped=%s）`；
产品面连续零改动 **%s** 轮（唯一取数口 `python3 scripts/product_streak.py --streak-for %d`，`--check` 同形；
本轮这一笔按 `--streak-for %d` 现读是 %s —— 本轮动了 2 个产品文件，commit 之后 git 会把它归零；上一轮那一格是 %s）。

NOT-RUN（三种缺席分开写，不许省略）：① **只在人身上判得了**的：393/395 的真机改前改后四数 ——
本轮现读分类器仍是 `screen_locked`（电源 on、SecureInput 属主 loginwindow、区域探针被拒），
尺不猜密码也不替用户解锁（D-322）；② **只在 runner 上判得了**的：394 的两问
（轨道那颗仍是材质 ⇒ 会不会走 `pill-ramp-no-track`；不透明语义色在 runner 上同号吗）——
本轮 push 的那跑只登记不轮询；③ **命令没跑成**的：本轮没有（四腿全部有对象且都跑完，见上面 ROUND_VERIFY）。

下一轮（R%d）的靶，按顺序：⓪ 读 CI 配对（本轮 push 的 run↔commit 成对写回，并答 394 那两问）→
① **396**：选中档与悬停档只差 %s 级 —— 先量"该差多少"（不许拍地板，D-321），再按分离度排修法，
改前改后四个数同一运行（D-318/D-319）；② 390 的 before/after（`纵向覆盖=%s` 那半）；
③ 389 的时长（到位帧 %s 对 声明 200ms）；④ 384 的横轴那半；⑤ 387 的①；
⑥ 若用户已解锁：395 的三格（真机改前/改后 + 392 的按下档/取色/菜单栏悬停）；
⑦ 376 剩那一半；⑧ **397**：§8 那 12 个键名要么由 `round_verify.sh` 补打、要么把 ROWS 表改成读
   `ROUND_VERIFY` 的键名 —— 两条修法相反，挑一条做完（做完之前那 12 格在台账里必须写成洞）；
⑨ 367 迁移 / 360 最后一批 / 361 合并 / 364 六把抽不出的刀。
""" % (DATE, ROUND, AUDIT_N, ITER_N, DARK_OWN, DARK_SYS,
       DARK_PAGE, DARK_TRACK, DARK_SEL, DARK_OWN, LIGHT_PAGE, LIGHT_TRACK, LIGHT_SEL, LIGHT_OWN,
       GEOM_CAND, GEOM_DIST, GEOM_TRACK, GEOM_PILL, GEOM_SEP, GEOM_MIRROR, GEOM_COV,
       RAMP_VERDICT, RAMP_MOVE, RAMP_BACK, RAMP_FRAMES, SLIDE_PEAK_ON, SLIDE_PEAK_OFF,
       line.replace(u"dir=", u"目录="), PURE_RUN, FILM_RUN, FILM_SKIP, CAP_RUN, CAP_SKIP,
       TABLE_SUMMARY, COND, PRE[0], PRE[1], PRE[2], ARM_TOTAL[0], ARM_TOTAL[1], ARM_TOTAL[2],
       GATE_FULL.strip(), BATT, BATT_SKIP,
       STREAK_N, ROUND - 1, ROUND, STREAK_GIT, PREV_STREAK,
       ROUND + 1, HOV_D_GAP, GEOM_COV, SETTLE_N)

# ──  落盘（七本）─────────────────────────────────────────────────────────────
if UI_TITLE.split(u"（")[0] in rd(AUD):
    die(u"UI_AUDIT 已经有本轮那一节了")
ui = rd(AUD)
m = re.search(u"(?m)^## 第 \\d+ 轮", ui)
if not m:
    die(u"UI_AUDIT 里找不到轮次标题")
wr(AUD, ui[:m.start()] + UI_TITLE + u"\n" + UI_BODY + u"\n" + ui[m.start():])

ite = rd(ITE)
if u"\n## Round %d · " % ITER_N in ite:
    die(u"ITERATION 已经有本轮那一节了")
wr(ITE, ite.rstrip(u"\n") + u"\n\n" + ITER_TITLE + u"\n" + ITER_BODY)

dec = rd(DEC)
if u"**D-%d（%d）" % (D1, ROUND) in dec:
    die(u"DECISIONS 已经有本轮那条了")
wr(DEC, dec.rstrip(u"\n") + u"\n\n" + D_BODY)

blg = rd(BLG)
if BL_NEW.split(u"（R333）")[0] in blg:
    die(u"BACKLOG 已经有本轮那一单了")
blg = insert_addition(blg, BL_393 + u"\n", 393, 394)
blg = insert_addition(blg, BL_394 + u"\n", 394, 395)
blg = append_addition_to_tail_entry(blg, BL_395 + u"\n", 395)
blg = blg.rstrip(u"\n") + u"\n" + BL_NEW
blg = blg.rstrip(u"\n") + u"\n" + BL_DRIFT
wr(BLG, blg)

chg = rd(CHG)
if len(re.findall(u"(?m)^## \\[Unreleased\\]$", chg)) != 1:
    die(u"CHANGELOG 的 [Unreleased] 不是恰好一次")
if CHG_ENTRY.split(u"（R")[0] in chg:
    die(u"CHANGELOG 已经有本轮那一笔了")
parts = chg.split(u"\n")
at = [i for i, l in enumerate(parts) if l == u"## [Unreleased]"][0]
parts[at + 1:at + 1] = [u"", CHG_ENTRY.rstrip(u"\n")]
wr(CHG, u"\n".join(parts))

sta = rd(STA)
if u"## R%d 状态" % ROUND in sta:
    die(u"STATE 已经有本轮那一节了")
anchor = re.findall(u"(?m)^## R%d 状态" % (ROUND - 1), sta)
if len(anchor) != 1:
    die(u"STATE 里上一轮的节标题命中 %d 次" % len(anchor))
pos = sta.index(anchor[0])
before_layers = sta.count(u"\n> ## ")
wr(STA, sta[:pos] + STATE_TITLE + u"\n" + STATE_BODY + u"\n" + sta[pos:])
after = rd(STA)
if after.count(u"\n> ## ") != before_layers:
    die(u"STATE 轮换把加粗的层数改动了：%d → %d" % (before_layers, after.count(u"\n> ## ")))
if u"## R%d 状态" % (ROUND - 1) not in after:
    die(u"STATE 轮换之后上一轮的标记没了")

fr = rd(FRA)
mUD = re.search(u"U-31 … U-(\\d+)", fr)
if not mUD:
    die(u"报告里找不到 U 区间那一格")
fr = once(fr, mUD.group(0), u"U-31 … U-%d" % UE)
mt = re.search(u"R9–R(\\d+)，(\\d+) 节自评", fr)
if not mt:
    die(u"报告标题里找不到 `R9–R<NNN>，<M> 节自评` 那一格")
n_rounds = len(re.findall(u"(?m)^## Round ", rd(ITE)))
fr = once(fr, mt.group(0), u"R9–R%d，%d 节自评" % (ITER_N, n_rounds))
scale_old = re.findall(u"(?m)^- \\*\\*判据与门的规模\\*\\*：.*$", fr)
if len(scale_old) != 1:
    die(u"§13 的「判据与门的规模」命中 %d 行" % len(scale_old))
udefs = len(re.findall(u"(?m)^- \\*\\*U-(\\d{3,4})[：(]", rd(AUD)))
new_scale = (u"- **判据与门的规模**：脚本电池现读 **Ran %s**（写盘前同数），变异臂在册 **%s** 把 / %s 张表"
             u"（预检 tables=%s covered=%s bad=%s）；U 定义行 **%s 条**、最大 **U-%d**；"
             u"决定台账最大 **D-%d**，BACKLOG 最大 **%d**（本轮新开两单：%d 选中档与悬停档只差 %s 级、%d §8 搬运口那 12 个键名已经没人打印）；"
             u"本轮刀 `mutate_r333.py CAUGHT=5/5, RESTORE_CLEAN=yes`（%s），"
             u"并把 R323/R324 两针重钉（M925 换证人、M933 补 repl）后重跑六张表。"
             u"§8 的读数搬运名单本轮**只搬到了读数族**：`%s`，而它自己的 12 格键名全缺（开单 %d）。"
             % (BATT, ARM_TOTAL[1], ARM_TOTAL[0], PRE[0], PRE[1], PRE[2], udefs, UE, D1, B_DRIFT, B_NEW,
                HOV_D_GAP, B_DRIFT, ARMS_NEW[0] + u"…" + ARMS_NEW[-1], ROWS_LINE, B_DRIFT))
fr = fr.replace(scale_old[0], new_scale)
prod_old = re.findall(u"(?m)^- \\*\\*产品面（这一节最该被读的部分）\\*\\*：.*$", fr)
if len(prod_old) != 1:
    die(u"§13 的「产品面」命中 %d 行" % len(prod_old))
new_prod = (u"- **产品面（这一节最该被读的部分）**：本轮产品文件 **%d** 个（**动效主线**："
            u"`VisualTokens.swift` 换掉选中的那颗（材质 → 不透明语义色）、`HistorySidebarView.swift` 的取用点跟着换；"
            u"暗档 差 由 −16.0 翻成 %s 并与系统参照臂（%s）同侧，亮档由 +3.0 翻成 %s。"
            u"产品面连续零改动 **%s** 轮（唯一取数口 `python3 scripts/product_streak.py --streak-for %s`，"
            u"`--check` 同形；本轮这一笔按 `--streak-for %s` 现读是 %s，commit 之后 git 会把它归零）。"
            u"产品面连续零改动轮数 = **%s**（这一格按仓库惯例写**上一轮**的派生值，本轮 commit 之后 git 归零）。"
            u"393 的离屏那一半结案，屏幕那一半欠在 %d，"
            u"这一发带回来的新缺陷开成 %d。"
            % (len(PRODUCT), DARK_OWN, DARK_SYS, LIGHT_OWN, STREAK_N, s(ROUND - 1),
               s(ROUND), STREAK_GIT, STREAK_N, 395, B_NEW))
fr = fr.replace(prod_old[0], new_prod)
fr = re.sub(u"(?m)^(- \\*\\*仍开（截至本轮，完整名单以 `AGENT_STATE.md` 的 R)\\d+( 节)",
            u"\\g<1>%d\\g<2>" % ROUND, fr, count=1)
if re.search(u"@\\w+@", fr):
    die(u"报告里还有没替换的占位符")
wr(FRA, fr)

# ──  写盘之后 ────────────────────────────────────────────────────────────────
rf0, rfc0 = sh([sys.executable, FRESH])
if rfc0 != 0 or u"REFUSED" in rf0:
    die(u"报告 §1 的刷新器没签：%s" % rf0.strip()[-300:])
print(u"SECTION1 " + rf0.strip().splitlines()[-1])
bt2, rc2 = sh([sys.executable, u"-m", u"unittest", u"discover", u"-s", u"scripts/tests"])
RAN2 = (re.findall(r"Ran (\d+) tests", bt2) or [None])[-1]
if rc2 != 0:
    die(u"写盘后电池红了（台账守卫读的就是这些文件）：\n" + bt2.strip()[-1500:])
print(u"BATTERY_AFTER 写盘前=Ran %s 写盘后=Ran %s" % (BATT, RAN2))
ck, ckc = sh([sys.executable, STREAK, u"--check"])
if ckc != 0:
    die(u"连读门不认这版台账：" + ck.strip()[-500:])
cv2, _ = sh([sys.executable, CURVE])
if (re.findall(r"^GAPS=(\S+)", cv2, re.M) or [u""])[-1] != u"none":
    die(u"写盘后曲线尺报缺口：" + cv2.strip()[-300:])
DERIVED = (re.findall(r"^DERIVED=(\S+)", cv2, re.M) or [None])[-1]
rf, rfc = sh([sys.executable, FRESH])
if rfc != 0 or u"REFUSED" in rf:
    die(u"报告 §1 刷新器第二遍不干净：%s" % rf.strip()[-300:])
chk, chkc = sh([sys.executable, u"-m", u"unittest", u"-v",
                u"test_final_report_headline.FinalReportHeadlineTests.test_the_headline_cells_agree_with_the_live_ledgers"],
               cwd=TESTS)
if chkc != 0:
    die(u"报告标题那几格与台账不同源：" + chk.strip()[-400:])

print(u"LEDGERS_R333 OK batt=Ran " + BATT + u"→" + (RAN2 or u"?") + u" (skipped=" + BATT_SKIP
      + u") streak=" + STREAK_N + u"(上一轮 " + PREV_STREAK + u") 产品文件=" + s(len(PRODUCT))
      + u" 改动面=" + s(len(CHANGED))
      + u" 暗档差=" + DARK_OWN + u" 系统=" + DARK_SYS + u" 亮档差=" + LIGHT_OWN
      + u" 轨道=" + GEOM_TRACK + u" 药丸=" + GEOM_PILL + u" 分离=" + GEOM_SEP + u" 镜像=" + GEOM_MIRROR
      + u" 候选行=" + GEOM_CAND + u" 纵向覆盖=" + GEOM_COV
      + u" 斜坡=" + RAMP_VERDICT + u" 位移=" + RAMP_MOVE
      + u" 全量卷=" + FULL_RUN + u"/skip" + FULL_SKIP + u"/fail" + FULL_FAIL
      + u" 帧=" + FRAME_N + u" 基线=" + BASE_CMP + u"/chg" + BASE_CHG + u"/miss" + BASE_MISS
      + u" dmg=" + DMG + u" 装机=" + INSTALLED
      + u" 刀=" + new_row[1] + u" 臂=" + new_row[2] + u" 预检 tables=" + PRE[0] + u" bad=" + PRE[2]
      + u" 在册=" + ARM_TOTAL[1] + u"/" + ARM_TOTAL[0]
      + u" U=" + s(UA) + u".." + s(UE) + u" D=" + s(D1) + u" BL=" + s(B_NEW)
      + u" 派生=" + (DERIVED or u"?"))
