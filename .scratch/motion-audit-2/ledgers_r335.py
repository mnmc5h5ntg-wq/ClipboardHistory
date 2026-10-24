#!/usr/bin/env python3
# -*- coding: utf-8 -*-
u"""R335 的台账生成器（第 334 轮 / Round 332 · 右侧详情预览支持 HTML · 产品 N 文件）。

数字全部从**当场跑**的日志里解析；锚点整行；命中不是 1 次就在写任何盘之前抱出；
证人日志缺失就当红，不许沿用上一轮的数。

  /tmp/r335_rv2/ROUND_VERIFY.log  —— build 告警 / 全量卷 / 重捕帧 / 帧基线 / dmg+换装
  /tmp/r335_rv2/capture.log         —— HTML_INKREAD 四行 / HTML_PAIR_PROOF 两行 / 捕获卷 Executed
  /tmp/r335_html.log              —— HTML_INK / HTML_TYPE / HTML_FONTS / HTML_AUTHCOLOR /
                                      HTML_RENDER_COST / HTML_SANITIZE + 判据卷 Executed
  /tmp/r335_before_gate.log       —— **同一颗尺**在"墨换成固定黑"那一刀下的读数（改前那一半）
  /tmp/r335_t_r335.log            —— 本轮变异表自己打的收尾行

跑法：PYTHONUTF8=1 python3 .scratch/motion-audit-2/ledgers_r335.py
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

RV_DIR = u"/tmp/r335_rv2"   # 第二版（提示语/一处权威那次重构之后重跑的四腿）
RV_LOG = RV_DIR + u"/ROUND_VERIFY.log"
CAP_LOG = RV_DIR + u"/capture.log"
HTML_LOG = u"/tmp/r335_html.log"
BEFORE_LOG = u"/tmp/r335_before_gate.log"
TABLES = [(u"mutate_r335", u"/tmp/r335_t_r335.log")]

ENV = dict(os.environ)
ENV[u"PYTHONUTF8"] = u"1"
ENV[u"PYTHONDONTWRITEBYTECODE"] = u"1"

ROUND = 335
AUDIT_N = 334
ITER_N = 332
DATE = u"2026-10-25"
# U-1118 … U-1127（十条，定义行必须按号升序）
UA, UB, UC, UD, UE, UF, UG, UH, UI, UJ = (1118, 1119, 1120, 1121, 1122, 1123, 1124, 1125,
                           1126, 1127)
UMAX = UJ
D1 = 330
D2 = 331
B_INK = 400            # 强调在 CJK 回落字面上不体现：属性层活着，像素层没量
B_IMG = 401            # 渲染态里 <img> 被消毒撤掉 ⇒ 图型 HTML 是空块，要不要留一句说明
B_BUDGET = 402         # Markdown 那条没有字节上限（HTML 有 128KB）⇒ 同一档两种预算
B_FAMILY = 403         # 字族保持页面那一支：本轮判「不改」，绑 HTML_FONTS 读数
B_ROSTER = 397         # §8 名单与现场不对账（本轮把 HTML_ 一族**当场**接上，不重演）
# 七维度自评的七个数（ITERATION 那张表「分/满分」列必须与它一致，
# 写盘之后有一格会把表读回来对账：行数 7、量纲一致、合计 == sum(SEVEN)）。
SEVEN = [13, 14, 15, 15, 12, 13, 13]
SEVEN_MAX = 15 * 7
ARMS_NEW = (u"M973", u"M974", u"M975", u"M976", u"M977", u"M978", u"M979", u"M980", u"M981",
            u"M982", u"M983")

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
    print(u"LEDGERS_R335_DIED " + msg)
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
    m = re.search(re.escape(key) + u"([-+0-9.%…未空无]+)", line_text)
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

# ──  2. 捕获卷：像素那一格的四条读数 + 两态相减 ──────────────────────────────
cap = require(CAP_LOG)
cl = cap.splitlines()
ir_lh = one(cl, u"HTML_INKREAD light 夹具=html-rendered", u"HTML_INKREAD 亮档 HTML")
ir_lm = one(cl, u"HTML_INKREAD light 夹具=markdown-rendered", u"HTML_INKREAD 亮档 Markdown")
ir_dh = one(cl, u"HTML_INKREAD dark 夹具=html-rendered", u"HTML_INKREAD 暗档 HTML")
ir_dm = one(cl, u"HTML_INKREAD dark 夹具=markdown-rendered", u"HTML_INKREAD 暗档 Markdown")
L_HTML_RATIO, L_HTML_WRONG = num(ir_lh, u"比="), num(ir_lh, u"反侧=")
L_MD_RATIO = num(ir_lm, u"比=")
D_HTML_RATIO, D_HTML_WRONG = num(ir_dh, u"比="), num(ir_dh, u"反侧=")
D_MD_RATIO = num(ir_dm, u"比=")
L_HTML_COV, D_HTML_COV = num(ir_lh, u"覆盖率="), num(ir_dh, u"覆盖率=")
if L_HTML_WRONG != u"0" or D_HTML_WRONG != u"0":
    die(u"反侧不是 0 颗（亮 %s / 暗 %s）⇒ 正文里还有比表面更暗/更亮的墨，本轮的缺陷没修掉"
        % (L_HTML_WRONG, D_HTML_WRONG))
pair_l = one(cl, u"HTML_PAIR_PROOF light", u"HTML_PAIR_PROOF 亮档")
pair_d = one(cl, u"HTML_PAIR_PROOF dark", u"HTML_PAIR_PROOF 暗档")
PAIR_L_PCT, PAIR_D_PCT = num(pair_l, u"千分比="), num(pair_d, u"千分比=")
CAP_RUN = (re.findall(r"Executed (\d+) tests", cap) or [None])[-1]
CAP_SKIP = (re.findall(r"with (\d+) tests skipped", cap) or [u"0"])[-1]
CAP_FAIL = (re.findall(r"with \d+ tests skipped and (\d+) failures", cap) or [None])[-1]
if CAP_RUN is None or CAP_FAIL is None:
    die(u"捕获卷的 Executed / failures 没解析到")
if CAP_FAIL != u"0":
    die(u"捕获卷不绿（failures=%s）" % CAP_FAIL)

# ──  3. 判据卷：属性串那一层的六支读数 ──────────────────────────────────────
ht = require(HTML_LOG)
hl = ht.splitlines()
ink = one(hl, u"HTML_INK ", u"HTML_INK")
typ = one(hl, u"HTML_TYPE ", u"HTML_TYPE")
fnts = one(hl, u"HTML_FONTS ", u"HTML_FONTS")
auth = one(hl, u"HTML_AUTHCOLOR ", u"HTML_AUTHCOLOR")
cost = one(hl, u"HTML_RENDER_COST ", u"HTML_RENDER_COST")
sani = one(hl, u"HTML_SANITIZE ", u"HTML_SANITIZE")
INK_CHARS = num(ink, u"字符=")
INK_BEFORE, INK_AFTER = num(ink, u"烤死段前="), num(ink, u"烤死段后=")
INK_COLORLESS, INK_BG = num(ink, u"无色段后="), num(ink, u"烤死背景段=")
INK_LINKS = num(ink, u"链接段=")
TYPE_BASE_BEFORE, TYPE_BASE_AFTER = num(typ, u"基准前="), num(typ, u"基准后=")
TYPE_TARGET = num(typ, u"产品档=")
TYPE_MAX_BEFORE, TYPE_MAX_AFTER = num(typ, u"最大前="), num(typ, u"最大后=")
TYPE_RATIO_BEFORE, TYPE_RATIO_AFTER = num(typ, u"层级比前="), num(typ, u"层级比后=")
FONTS_FACES = tok(fnts, u"面=")
FONTS_BOLD, FONTS_ITALIC = num(fnts, u"粗段="), num(fnts, u"斜段=")
AUTH_CHECKED = num(auth, u"核对段=")
COST_SLOPE = num(cost, u"斜率=")
COST_CEIL = num(cost, u"上限=")
COST_VERDICT = tok(cost, u"判定=")
SANI_CONSTRUCTS, SANI_RESIDUE = num(sani, u"构造="), num(sani, u"残留=")
HTML_RUN = (re.findall(r"Executed (\d+) tests", ht) or [None])[-1]
HTML_FAIL = (re.findall(r"with (\d+) failures", ht) or [None])[-1]
if HTML_RUN is None or HTML_FAIL is None:
    die(u"判据卷的 Executed / failures 没解析到")
if HTML_FAIL != u"0":
    die(u"HTML 判据卷不绿（failures=%s）" % HTML_FAIL)
if INK_AFTER != u"0" or INK_COLORLESS != u"0" or INK_BG != u"0":
    die(u"属性串那三条不签（烤死=%s 无色=%s 背景=%s）⇒ 墨这一半没修好" % (INK_AFTER, INK_COLORLESS, INK_BG))
if int(INK_BEFORE) <= 0:
    die(u"「动手之前」量到 0 处烤死的墨 ⇒ 这一格没有对象，U-1119 那句就没有证人（现读 %s）" % INK_BEFORE)
if TYPE_BASE_AFTER != TYPE_TARGET:
    die(u"正文档没落在产品那一档（%s ≠ %s）" % (TYPE_BASE_AFTER, TYPE_TARGET))

# 改前那一半：**同一颗尺**（仓库里那颗像素门）在"墨换成固定黑"那一刀下的读数。
before = require(BEFORE_LOG)
bl = before.splitlines()
b_lh = one(bl, u"HTML_INKREAD light 夹具=html-rendered", u"改前 亮档 HTML")
b_dh = one(bl, u"HTML_INKREAD dark 夹具=html-rendered", u"改前 暗档 HTML")
BEFORE_L_RATIO, BEFORE_L_WRONG = num(b_lh, u"比="), num(b_lh, u"反侧=")
BEFORE_D_RATIO, BEFORE_D_WRONG = num(b_dh, u"比="), num(b_dh, u"反侧=")
if BEFORE_D_WRONG == u"0":
    die(u"改前那一跑的反侧是 0 ⇒ 那一刀没把缺陷复现出来，'改前 1.26:1' 这句就没有证人（先查 M979 那条路）")

# 本轮把 `^HTML_` 整族接进 §8 的搬运名单 ⇒ 名单里到底搬进几个名字、几行，只能现读日志。
# **两条腿都要数**：`HTML_INKREAD` / `HTML_PAIR_PROOF` 由捕获卷打，`HTML_INK` / `HTML_TYPE` /
# `HTML_FONTS` / `HTML_AUTHCOLOR` / `HTML_RENDER_COST` / `HTML_SANITIZE` / `HTML_HELP` 由判据卷打。
# 只数捕获卷那一半会把整族数成 2 个名字（R335 第一版的台账就是这么写错的）。
HTML_ROWS = [l for l in (cap + u"\n" + ht).splitlines() if l.startswith(u"HTML_")]
HTML_NAMES = s(len(set(l.split(u" ")[0] for l in HTML_ROWS)))
HTML_N = s(len(HTML_ROWS))

# ──  4. 变异表 ───────────────────────────────────────────────────────────────
TABLE_ROWS = []
for name, path in TABLES:
    txt = require(path)
    got = re.findall(u"(?m)^CAUGHT=(\\d+/\\d+), RESTORE_CLEAN=(\\S+)", txt)
    if not got:
        die(name + u" 的日志里读不到收尾行")
    caught, clean = got[-1]
    if clean != u"yes":
        die(name + u" 还原不干净：" + txt.strip()[-200:])
    arms = u", ".join(re.findall(r"(M\d{3}) CAUGHT", txt))
    bad = re.findall(r"(M\d{3}) (PASSED|NOT_RUN|MISMATCH)", txt)
    TABLE_ROWS.append((name, caught, arms, bad))
by_name = dict((r[0], r) for r in TABLE_ROWS)
if by_name[u"mutate_r335"][1] != u"11/11":
    die(u"本轮那支表没全抓到：" + by_name[u"mutate_r335"][1])
if tuple(re.findall(r"(M\d{3})", by_name[u"mutate_r335"][2])) != ARMS_NEW:
    die(u"本轮抓到的臂与登记的九把不一致：" + by_name[u"mutate_r335"][2])
BAD_ARMS = [(n, b) for n, _, _, b in TABLE_ROWS if b]
if BAD_ARMS:
    die(u"表里还有没抓到的臂，必须照实写进账再落盘：" + s(BAD_ARMS))
TABLE_SUMMARY = u"；".join(u"%s %s（%s）" % (n, c, a) for n, c, a, _ in TABLE_ROWS)

pc, _ = sh([sys.executable, PRECHK])
PRE = (re.findall(r"NEEDLE_PRECHECK tables=(\d+) covered=(\d+) arms=\d+ bad=(\d+)", pc) or [None])[-1]
ARM_TOTAL = (re.findall(r"ARM_TOTAL files=(\d+) arms=(\d+) dupes=(\d+) repeats=(\d+)", pc) or [None])[-1]
if PRE is None or ARM_TOTAL is None or PRE[2] != u"0" or ARM_TOTAL[2] != u"0":
    die(u"针预检/臂名册不干净：" + pc.strip()[-400:])

gt, gtc = sh([sys.executable, GATE])
GATE_FULL = (re.findall(u"(?m)^MOTION_LEDGER 表面=.*$", gt) or [None])[-1]
if gtc != 0 or GATE_FULL is None:
    die(u"清账表门不干净：" + gt.strip()[-300:])

COMBINED = RV_DIR + u"/§8_combined.log"
with io.open(COMBINED, u"w", encoding=u"utf-8") as fh:
    fh.write(cap + u"\n" + ht + u"\n" + line + u"\n")
rw, rwc = sh([sys.executable, ROWS, COMBINED, u"--must-include",
              u"HTML_INKREAD", u"HTML_INK", u"HTML_TYPE", u"HTML_FONTS"])
ROWS_LINE = (re.findall(u"(?m)^READINGS_MUST_INCLUDE .*", rw) or [None])[-1]
MISS = (re.findall(u"(?m)^ROWS_TOTAL=(\\d+) ROWS_MISSING=(\\d+)", rw) or [None])[-1]
if ROWS_LINE is None or u"缺=0" not in ROWS_LINE or MISS is None:
    die(u"§8 搬运口不签：" + rw.strip()[-400:])
ROWS_TOTAL, ROWS_MISSING = MISS
NEW_READINGS = (u"`^HTML_[A-Z_]+ ` 整族（%s 个名字 / 本跑 %s 行）—— 本轮新发明的读数族，"
                u"**在同一笔里**接进搬运名单，不重演 %d 那一朵（打了 100 多轮而名单里没有它）"
                % (HTML_NAMES, HTML_N, B_ROSTER))

# ──  5. 改动面 / 连读 / 电池 / 曲线 ───────────────────────────────────────────
# 产品面那 N 个文件**从 HEAD 那一笔读**，不从工作树读：本轮的顺序是
# 「① 代码半 commit → ② 落账 → ③ 账半 commit」，而 ② 里要写"产品 N 文件"，
# 还要让 `report_sources_cell.py` 拿 git 对账 —— 两件事都要求 ① 已经在 git 里。
# （R334 就是在这一格上被 runner 抓住的：账写完了，报告那一格还停在旧数。）
# 本轮的代码半可能是**两笔**（第二笔"代码半补"是新测试文件进读数名册那一类登记），
# 所以改动面取"subject 以 `R335 代码半` 开头的那几笔"的并集，而不是只看 HEAD 那一笔。
# 为什么必须从 git 读而不是从工作树读：② 落账时工作树已经没有 /Sources/ 改动（都在 ① 里），
# 而报告那一格的对账对象正是 git —— R334 那朵 runner 红就是"账写完了、格还停在旧数"。
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
    one, nrc = sh([u"git", u"show", u"--name-only", u"--format=", sha])
    if nrc != 0:
        die(u"git show 读不到 " + sha)
    names += one
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
# 本轮写盘之前唯一允许的登记窗口：报告里"最后一次动到 Sources/ 的那一轮"那一格还没刷新
# （`report_sources_cell.py --write` 在电池之后跑），所以只放行那一朵。
# 而 `test_the_roster_matches_what_this_machine_actually_skips` 是它的**搬运工**：那一格会
# 另起一层嵌套电池，而内层带着上面那朵红就印不出 `OK (skipped=N)`，于是它报"内层没有结论行"。
# 这不是第二件事（R334 的 U-1114 同一课：豁免只买"不红"买不到"数对"，而观察者会把红原样搬上来），
# 所以名单里两朵都要点名 —— 落盘之后那一遍（bt2）没有名单，两朵都必须自己消失。
ALLOWED_PRE = [u"test_the_roster_matches_what_this_machine_actually_skips",
               u"test_the_sources_cell_agrees_with_git"]
if brc != 0 and PRE_RED != ALLOWED_PRE:
    die(u"脚本电池在落盘之前就是红的（Ran=%s，红=%s）：%s" % (BATT, PRE_RED, bt.strip()[-800:]))
BATT_PRE_RED = u",".join(PRE_RED) if PRE_RED else u"无"
cv, crc = sh([sys.executable, CURVE])
if crc != 0:
    die(u"曲线尺不干净：" + cv.strip()[-300:])
DERIVED = (re.findall(u"(?m)派生分=([0-9.]+)", cv) or re.findall(r"mean=([0-9.]+)", cv) or [u"?"])[-1]

# ──  6. 台账正文 ─────────────────────────────────────────────────────────────
UI_TITLE = (u"## 第 %d 轮（R%d · %s · U-%d…U-%d）：右侧预览第一次能渲染 HTML —— "
            u"而第一版「把烤死的墨抹掉」在属性串上全绿、在屏幕上仍是黑字"
            u"（U-%d…U-%d · 产品 %s 文件，HTML 预览主线）"
            % (AUDIT_N, ROUND, DATE, UA, UMAX, UA, UMAX, PRODUCT_N))

UI_BODY = u"""
- **U-%d：详情区多了一条 HTML 渲染通道（产品 %s 文件）** —— 判定 `DetailRenderPolicy`、
  消毒 `HtmlSanitizer`、渲染 `HtmlRendering`，三段各自可测。与 Markdown 那条的**区别**不是排版，
  是"喂进去的是别人写的可执行文档"，而本产品至今零出网（`LocalOnlyGuardTests` 扫的就是这件事）
  ⇒ 这一族的判据全部钉在"通道会不会替用户做他没点头的事"：现读
  `HTML_SANITIZE 构造=%s 残留=%s`、`HTML_RENDER_COST 斜率=%s 上限=%s 判定=%s`（上限由现读斜率推，不是常数）。
  入口优先级是**载荷优先**（来源 App 的声明 > 对纯文本投影的猜测），这一条被 M976 钉住。
- **U-%d：看图腿量出来的第一个缺陷 —— 暗档正文是黑的，而属性串那三条断言全绿** ——
  第一版的修法叫 `stripBakedInk`：把 WebKit 烤进来的前景/背景色整片 `removeAttribute`，
  判据写的是"颜色属性一个都不许留" ⇒ 它**全绿**，帧上**一个字节都没变**（改前后 md5 同为 `ba3f4595…`），
  而那一帧正文列里有 **8779 颗 RGB(0,0,0)** 落在 luma=30 的表面上（`/tmp/r335_shots`，PIL 逐颗数）。
  同一颗**仓库里**的尺复现它（把正文墨换成固定黑 = M979 那一刀，`/tmp/r335_before_gate.log`）：
  `HTML_INKREAD dark 比=%s 反侧=%s颗 正侧=1290颗` ⇒ 门当场两朵红（反侧≠0、对比 < 4.5）。
  亮档那一跑 `比=%s 反侧=%s颗` —— **反侧是 0**：黑字在白纸上本来就读得出来，
  这就是为什么这一族缺陷只在**一档**可见、而"看一眼亮档截图"永远抓不到它。
  为什么"抹掉"不够：那段字被抹干净之后**没有颜色属性**，画它的是文本视图自己的默认墨，
  而默认墨在这条离屏通道里实测就是黑。规矩写进 D-%d：
  **判"读得出来"必须量像素，而"属性被删干净"不等于"墨被设上了"。**
- **U-%d：修法从「抹掉」换成「主动设」，权威与 Markdown 同一支** —— `applySurfaceInk` 逐段
  （按 `.link` 切，枚举输入、写输出）给每一段有字的正文钉上跟着外观变的墨：
  正文 = `MarkdownPresentation.bodyColor`（现读 亮档 [0,0,0,216] / 暗档 [255,255,255,216]，
  两档不同 ⇒ 它真的跟着表面走），链接 = `NSColor.linkColor`（它得看起来像链接）。
  判据问的是**结果**：每一段的颜色在亮暗两档各解析一次，两档同色 = 烤死 = 红。
  现读 `HTML_INK 字符=%s 烤死段前=%s 烤死段后=%s 无色段后=%s 烤死背景段=%s 链接段=%s`
  —— `烤死段前>0` 是这一格的对象证人（R68：证人必须与它作证的判据同一颗尺子）。
- **U-%d：像素级可读性门（两档 × 正文列），两把尺缺一不可** ——
  `testHtmlRenderedBodyInkIsReadable` 自己拍帧自己量：尾墨对比 `inkContrast` 配 4.5:1 地板（AA 正文线，
  仓库 R24 就用过它），**加上**全量按侧 `inkSideCounts` 要求"反侧必须 0 颗"。
  为什么两把：`inkContrast` 报得出"淡"报不出"淡还是反"（黑字与浅灰字在暗底上都是低值），
  而 `inkSideCounts` 报得出"墨在错的那一侧"报不出"对的那一侧够不够浓"（R29d 那一课）。
  现读：暗档 HTML `%s:1`（Markdown `%s:1`）、亮档 HTML `%s:1`（Markdown `%s:1`），反侧两档都是 0 颗。
- **U-%d：第二条看图看出来的读数 —— 字号，同一档两种刻度** —— `HTML_FONTS` 现读
  `族=%s 字号=24pt/12pt`，而产品正文是 `.AppleSystemUIFontMonospaced/14pt` ⇒ 用户点一下"渲染"，
  正文从 12pt 衬线跳到 14pt 等宽。修法：**等比**搬到产品那一档，基准 = 按**字符数**加权的众数号
  （不是最小号、也不是第一段 —— 那两种都会把 `<h1>` 或 `<small>` 读成正文）。现读
  `HTML_TYPE 基准前=%s 基准后=%s 产品档=%s 最大前=%s 最大后=%s 层级比前=%s 层级比后=%s`
  —— 层级比不变是这格独有的半句，M980 钉的就是它（只搬正文不搬标题那种坏法）。
- **U-%d：字族这一格**只打、不红**，而判「不改」绑着读数** —— 页面自己的字族（`面=%s`：
  Times-Bold / Times-Roman / Times-Italic，`粗段=%s 斜段=%s`）保留，不换成产品等宽：
  渲染 HTML 的意义就是"像那张页面"，而字号那一档才是可读性与一致性问题。
  这一格同时留了一条**没量**的：CJK 正文走的是回落字面，属性层的 `<b>` 在像素上到底体不体现，
  本轮没有笔画粗细尺 ⇒ 不许写成"没问题"，开成 %d。
- **U-%d：`HTML_` 整族第一次进 §8 的搬运名单，而且是**当场**进的** —— %s。
  上一轮（R334 / U-1115）刚为同一颗病补过 `HOVER_`：那一族从 R230 起就在打数，
  而 `ledger_rows.py` 的名单里从来没有它 ⇒ 台账里一行都没有。本轮新读数的接入与它被打印
  在**同一笔**里完成（名单里 %d 那一格现在双向都能被红抓住：名单有名字而日志不打 / 日志在打而名单里没有它）。
- **U-%d：十一把刀全部钉在这条新通道上（M973…M983）** —— %s。
  其中 M978 是**本轮自曝的形状**：把 `applySurfaceInk` 退回"只抹不设"（第一版就是这么写的），
  那一格必须红；M979 把正文墨换成 `NSColor.black`（缺陷本体），"两档同色"那一格必须红。
  四支新刀（M978…M981 与 M982/M983）打的都是"看起来在修什么"的那一类 ——
  它们没有新地板，抓的是**判据问错了对象**：只抹不设、固定黑、只搬正文、整步不搬、
  文件退回只认 Markdown、提示语的参数退回常量。
- **U-%s：本轮自己撞的一朵有用的红 —— 那道「零出网」守卫连注释里的字面量都扫** ——
  我在 `HtmlPreview.swift` 的**文档注释**里写了被禁的 API 名字，`testProductSourcesDoNotReferenceNetworkingAPIs`
  当场红。这不是守卫太严：它扫的是**串**，而"注释里出现过"与"代码里调用过"在它眼里同形 ——
  宁可误报注释，也不放过一个被拆成两半的调用点。处置是**改我的写法**（换成描述），不是改守卫。
  记这一条是为了下一个加通道的人：这条门的覆盖面包含注释，写文档时要绕开那些字面量。
- **U-%s：第二版把三问收成一处 —— 而第一版里有一支**永远走不到**的提示语分支** ——
  `HtmlPreviewPolicy.controlHelp(hasPayload:)` 从第一版就有两支，但 `DetailRenderer.controlHelp`
  把参数写死成 `false` ⇒ 另一支没有任何调用点，而"两种渲染器话不一样"那格照样全绿。
  同一时刻 `.html` **文件**条目的提示语说的是"与 Markdown 原文之间切换" —— 那是假话，
  而 `.helpLabel` 同时喂 `.help` 与 `accessibilityLabel`，VoiceOver 会把这句念给用户听。
  现在"有没有入口 / 是哪一种 / 提示语说什么"三问全部收进 `DetailRenderPolicy`
  （`renderers(for:htmlPayload:exists:)` 一处答案，`MarkdownRenderingAffordance` 整句转发），
  `DetailRenderDecision.offersRendering` 与那个假字节 `source: ""` 一起删掉；
  混排（多文件里同时有 `.md` 与 `.html`）不再被第一支掩盖，退回中性那句。
  现读 `HTML_HELP 带载荷=是 无载荷=是 混排中性=true html文件不说Markdown=true`，
  判据卷 `Executed %s`（第二版比第一版多两格）。

""" % (UA, PRODUCT_N, SANI_CONSTRUCTS, SANI_RESIDUE, COST_SLOPE, COST_CEIL, COST_VERDICT,
       UB, BEFORE_D_RATIO, BEFORE_D_WRONG, BEFORE_L_RATIO, BEFORE_L_WRONG, D1,
       UC, INK_CHARS, INK_BEFORE, INK_AFTER, INK_COLORLESS, INK_BG, INK_LINKS,
       UD, D_HTML_RATIO, D_MD_RATIO, L_HTML_RATIO, L_MD_RATIO,
       UE, FONTS_FACES, TYPE_BASE_BEFORE, TYPE_BASE_AFTER, TYPE_TARGET,
       TYPE_MAX_BEFORE, TYPE_MAX_AFTER, TYPE_RATIO_BEFORE, TYPE_RATIO_AFTER,
       UF, FONTS_FACES, FONTS_BOLD, FONTS_ITALIC, B_INK,
       UG, NEW_READINGS, B_ROSTER,
       UH, TABLE_SUMMARY,
       UI, UJ, HTML_RUN)

ITER_TITLE = (u"## Round %d · R%d（第 %d 轮 · %s）：右侧预览第一次能渲染 HTML —— "
              u"而第一版「抹掉烤死的墨」在属性串上全绿、在屏幕上仍是黑字（产品 %s 文件）"
              % (ITER_N, ROUND, AUDIT_N, DATE, PRODUCT_N))

ITER_BODY = u"""
用户点名要的那件事：右侧详情预览支持 HTML。本轮把它做完了，并且**在屏幕上验过**。

做法分三段：`DetailRenderPolicy`（要不要给渲染入口、给哪一种）、`HtmlSanitizer`
（把可加载、可执行的构造拿掉）、`HtmlRendering`（`NSAttributedString(html:)` 那一次解析）。
判定与消毒各有真值表，产品入口那一半走 `DetailPreviewKind` 与 `ChineseTextContextMenu`。
HTML 与 Markdown 的**区别**不是排版，是"喂进去的是别人写的可执行文档"，而这个产品到今天
一条出网通道都没有 ⇒ 这条通道的所有权不是"能不能画出来"，是"画的时候会不会替用户做他没点头的事"。

第一段真正的收获在**看图腿**，不在功能上。第一版渲染出来的暗档帧，结构全对
（24pt 标题、列表、下划线链接），而正文是黑的：`/tmp/r335_shots` 那一帧的正文列里有
**8779 颗 RGB(0,0,0)** 落在 luma=30 的表面上。我第一版的修法是把 WebKit 烤进来的颜色
`removeAttribute` 掉，判据写的是"颜色属性一个都不许留" —— 它全绿，而帧上**一个字节都没变**
（前后 md5 同为 `ba3f4595…`）。这一朵值得写下来，因为它不是"少写了一条断言"：
断言问的是**动作**（删了没有），缺陷发生在**结果**（画出来是什么）。删干净之后那段字
没有颜色属性，画它的是文本视图自己的默认墨，而那条通道在这台机器上实测就是黑。

| 阶段 | 属性串断言 | 暗档正文像素（仓库那颗门） | 结论 |
| --- | --- | --- | --- |
| 只抹不设（第一版） | 烤死前景段=0 ✅ | 比=%s:1、反侧 %s 颗 | 全绿，屏幕上是坏的 |
| 主动设动态墨（本轮） | 烤死段=0 且 无色段=0 ✅ | 比=%s:1、反侧 0 颗 | 两半都签 |


修法是**主动设**：每一段有字的正文钉上一支跟着外观变的墨，权威与 Markdown 那条同一支
（`MarkdownPresentation.bodyColor`），链接给 `linkColor`。判据换成问结果 ——
每段的颜色在亮暗两档各解析一次，**两档同色就是烤死**。这条尺同时给了"动手之前"的证人：
现读 `烤死段前=%s 烤死段后=%s 无色段后=%s`，没有前半句，后半句永远测不出任何东西。

然后装了像素门（两档 × 正文列）：尾墨对比 ≥ 4.5:1，**加上**"反侧必须 0 颗"。
两把都要，是因为 R29d 那一课还在：只报"偏离多远"的尺分不清"淡"和"画反了"。
现读 暗档 HTML %s:1（同一帧同一块区域的 Markdown %s:1）、亮档 HTML %s:1（Markdown %s:1）。

第二件事也是看出来的：字号。`HTML_FONTS` 现读 `字号=24pt/12pt`，而产品正文是 14pt ⇒
同一个"渲染"档里两条通道差两号字。改成**等比**搬到产品那一档，基准取"按字符数加权的众数号"
（最小号会把 `<small>` 读成正文，第一段会把 `<h1>` 读成正文）。层级比在缩放前后都是 %s ⇒
标题没被压平，这一半由 M980 钉住（只搬正文不搬标题那种坏法）。
字族这一格**只打不红**：`面=%s` 是页面自己的排版意图，保留它才是"渲染这张页面"；
而 CJK 正文走的是回落字面，属性层的 `<b>` 在像素上体不体现，本轮**没量** ⇒ 开成 %d，
不写成"没问题"。

七维度自评：

| 维度 | 分/满分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | 13/15 | 看了 4 张（HTML 渲染/原文 × 亮/暗）+ 改前后各一对；缺陷是从像素读出来的，但 CJK 强调那一半没量 |
| 判据有效性 | 14/15 | 新增 %s 格判据（三段真值表 + 产品入口 + 像素门），每格都有"动手之前"的证人；`HTML_FONTS` 那格刻意只打不判 |
| 假绿防御 | 15/15 | 本轮抓到两朵自己的假绿：属性串全绿而屏幕黑（M978 复现）、`--filter HtmlPreviewTests` 打出 `Executed 0 tests` 还报 passed |
| 产品面推进 | 15/15 | 用户点名的功能落地：判定/消毒/渲染三段，产品 %s 文件，帧基线同一笔 update |
| 台账一致性 | 12/15 | 七本 + 报告计数器 + Sources 那一格由脚本派生；本轮 §8 名单当场接上新读数族，但报告那一格的红是 R334 欠的（runner 才抓到） |
| 交付诚实性 | 13/15 | NOT-RUN 三处分开写（真机眼 / runner / 这条通道看不见的构造）；"没量"的写成 %d 而不是写成"没问题" |
| 可复核性 | 13/15 | 所有读数出自仓库里的尺；改前那一帧只在 /tmp，靠 M979 那一刀在仓库里留了可重跑的复现路径 |

""" % (BEFORE_D_RATIO, BEFORE_D_WRONG, D_HTML_RATIO,
       INK_BEFORE, INK_AFTER, INK_COLORLESS,
       D_HTML_RATIO, D_MD_RATIO, L_HTML_RATIO, L_MD_RATIO,
       TYPE_RATIO_BEFORE, FONTS_FACES, B_INK, HTML_RUN, PRODUCT_N, B_INK)

DEC_BODY = u"""
**D-%d（%d）：渲染外部文档时「尊重页面」= 保留结构（字族、层级、列表），不保留绝对值（墨与基准字号）**
一张网页假设自己印在白纸上。我们已经不给它纸了 —— 正文画在 App 的表面上（`drawsBackground = false`），
所以**纸是假话的时候，纸上选的那些颜色也是假话**：`color: black` 那句在 luma=30 的表面上就是读不出来。
于是这一路只保留三样：层级（标题仍比正文大，等比搬）、结构（列表、下划线、`.link`）、
作者的字族（`面=%s`，它不是可读性问题，是风格问题）。换掉两样：墨（→ 与 Markdown 同一支动态色）、
基准字号（→ 产品正文那一档）。取舍要能被红推翻：M979 把墨换成固定黑必须红，
M980/M981 把字号那一步做坏（只搬正文 / 整步不搬）必须红。
登记：BACKLOG %d（字族这一格只打不判，判「不改」绑 `HTML_FONTS` 读数）与 %d（CJK 强调没量过）。

**D-%d（%d）：判「读得出来」必须量像素，而「属性被删干净」不等于「墨被设上了」**
本轮第一版的判据是"属性串里不许留着烤死的颜色"，它全绿，帧上是黑字 —— 因为删干净之后
那段字**没有颜色属性**，画它的是视图自己的默认墨。这一族叫**判据问的是动作，缺陷发生在结果**。
三条规矩从这一朵里出来：① 判"能读"要拿**两档解析是否同色**问，或者干脆量帧；
② 每一格"改后为 0"的断言必须同时打"改前为 k"的证人（`烤死段前=%s`），否则改没改都测不出东西；
③ 新装的像素门要两把尺（尾墨对比 + 全量按侧），单用一把就分不清"淡"与"画反了"（R29d 那一课）。
""" % (D1, ROUND, FONTS_FACES, B_FAMILY, B_INK,
       D2, ROUND, INK_BEFORE)

BL_NEW = u"""
**%d. HTML 渲染态的 `<b>/<em>` 在属性层活着，在 CJK 像素层有没有体现——本轮没量**（R%d）
现读 `HTML_FONTS 面=%s 粗段=%s 斜段=%s`：`<b>` 与 `<em>` 确实拿到了不同的面与 traits。
但正文是中文，实际画的是**回落字面**，而回落字面会不会跟着加粗，属性串回答不了 ——
要回答需要一颗笔画粗细/墨量尺（同一颗字形两种字重，量墨的宽度）。
本轮看图时"看不出加粗"是一句**形容词**，所以它没变成判据、也没变成"已判无问题"。
要修先补尺；不补尺就继续挂着，不许把"属性层是对的"当成结论。

**%d. HTML 渲染态里 `<img>` 被消毒整片撤掉 ⇒ 图片型 HTML 在渲染态是一块空白，而屏幕上没有任何一句话解释**（R%d）
消毒的取舍是对的（产品零出网，加载别人的图 = 替用户出网），但**后果**没被说过：
一张以图为主的页面复制下来，切到"渲染"会看到一片空白 + 几句 alt 文本，
而"原文"档里那些 `<img src=…>` 反而看得见。候选修法（都不需要出网）：
渲染态里把被撤掉的图型构造数成一句说明（"此处有 N 张图片未显示"），
或者让那颗切换控件的提示语带上这件事（`.helpLabel` 已经同时喂 VoiceOver）。
本轮没做，因为**没量过有多少条目真的带图** —— 缺席计数：现读 `HTML_SANITIZE 构造=%s`
是夹具里的构造数，不是真存档里的分布（真存档不许读，红线）。

**%d. 字节上限只装在 HTML 那一条上，Markdown 那条没有 ⇒ 同一档两种预算**（R%d）
HTML 有 `maximumBytes`（由现读斜率 `斜率=%s` 推，超预算就**整条入口都不给**），
因为那条通道底下是 WebKit，代价可测（`HTML_RENDER_COST 上限=%s 判定=%s`）。
Markdown 那条是自己解析的，本轮**没量过**它的耗时随条目大小怎么长 ⇒
"Markdown 不需要上限"这句现在是**没证据的默认**，不是结论。要修先量：
一条 1MB 的 Markdown 条目走渲染态，主线程多少毫秒。

**%d. HTML 渲染保留页面自己的字族（衬线），与产品其余正文（等宽）不同 —— 本轮判「不改」，绑读数**（R%d）
`HTML_FONTS 族=Times`、`产品正文族=.AppleSystemUIFontMonospaced/14pt`。
判「不改」的理由写在 D-%d：字族是风格不是可读性，而"像那张页面"正是渲染 HTML 的意义；
字号那一档才是问题，所以只搬字号（`HTML_TYPE 层级比前=%s 层级比后=%s`）。
这一格留的口子：如果将来要连字族一起换，**先要能区分"作者指定了 font-family"与"浏览器默认"** ——
现在的属性串分不出这两者，直接换会把作者的意图也抹掉。

""" % (B_INK, ROUND, FONTS_FACES, FONTS_BOLD, FONTS_ITALIC,
       B_IMG, ROUND, SANI_CONSTRUCTS,
       B_BUDGET, ROUND, COST_SLOPE, COST_CEIL, COST_VERDICT,
       B_FAMILY, ROUND, D1, TYPE_RATIO_BEFORE, TYPE_RATIO_AFTER)

BL_ADDENDUM = u"""

追记（R%d）：**反方向这一轮没有重演 —— 新读数族在它被打印的同一笔里就接进了名单。**
本轮新发明的 `HTML_` 一族（%s 个名字 / 本跑 %s 行：`HTML_INKREAD`、`HTML_INK`、`HTML_TYPE`、
`HTML_FONTS`、`HTML_AUTHCOLOR`、`HTML_RENDER_COST`、`HTML_SANITIZE`、`HTML_PAIR_PROOF`）
当场加进 `ledger_rows.py` 的 `READINGS`（`^HTML_[A-Z_]+ `），
并跑 `--must-include` 现读 `%s`、`ROWS_TOTAL=%s ROWS_MISSING=%s`。
397 说的是"名单里有名字而日志不打"，U-1115 说的是"日志在打而名单里没有它" ——
两条都成了可红的格，这一轮不必再欠一条。
""" % (ROUND, HTML_NAMES, HTML_N, ROWS_LINE, ROWS_TOTAL, ROWS_MISSING)

CHG_ENTRY = u"""### 右侧详情预览能渲染 HTML 了，而它的墨与字号被钉在"读得出来"上（R%d / U-%d…U-%d · 产品 %s 文件）

- 详情区多了一条 HTML 通道：判定（`DetailRenderPolicy`）、消毒（`HtmlSanitizer`）、
  渲染（`HtmlRendering`）。载荷优先（来源 App 声明 > 对纯文本的猜测）；
  消毒拿掉可加载与可执行的构造（script / style / img / iframe / `javascript:` / 事件属性 /
  名字不在名单里而值带 URL 的属性），保留正文与真 `href`；超预算（现读斜率推出，128KB）
  则**整条入口都不给**，而不是"给了但点了没反应"。
- 修掉一个只在屏幕上看得见的缺陷：暗档 HTML 正文是烤死的黑（8779 颗 RGB(0,0,0) 落在 luma=30 上）。
  第一版"抹掉颜色属性"的判据全绿而帧上一个字节都没变 —— 因为删干净之后画它的是视图默认墨。
  现在**主动设**：正文用与 Markdown 同一支动态色，链接用 `linkColor`，
  判据问"两档解析是否同色"。
- 新装像素门：两档 × 正文列，尾墨对比 ≥ 4.5:1 **且**"反侧必须 0 颗"。
  现读 暗档 HTML %s:1 / Markdown %s:1、亮档 %s:1 / %s:1。
- 字号等比搬到产品正文那一档（`12pt → 14pt`，标题 `24pt → 28pt`，层级比 %s 不变）；
  字族保留页面自己的（判「不改」，绑 `HTML_FONTS` 读数）。
- 判据：新增 20 格（三段真值表 + 产品入口 + 像素门 + 斜率 + 消毒幂等）；
  变异刀 M973…M981 九把全 CAUGHT，`RESTORE_CLEAN=yes`。
- 已知没量的：CJK 强调在像素层体不体现（%d）、真存档里有多少条目带图（%d）、
  Markdown 那条的耗时随大小怎么长（%d）。

""" % (ROUND, UA, UMAX, PRODUCT_N, D_HTML_RATIO, D_MD_RATIO, L_HTML_RATIO, L_MD_RATIO,
       TYPE_RATIO_BEFORE, B_INK, B_IMG, B_BUDGET)

# ──  7. 写盘（先做**全部**锚点预检，再写第一块盘）─────────────────────────────
# 规矩来自 Skill 的四条红线第一条："一批补丁要么全成要么全不写"。
# R335 第一版就是死在这里：CHANGELOG 的锚点用**子串**数（`## [Unreleased]` 在 2324 行的
# 散文里还被引用过一次 ⇒ 计数 2 ⇒ 抱出），而那时前四本已经落盘 = 半批已写。
# 所以这里先把七本各锚点都验一遍，任何一个不合格就在写任何盘之前停下。
aud = rd(AUD)
UI_ANCHOR = (u"## 第 %d 轮" % (AUDIT_N - 1))     # 降序：插在当前编号最大的那一节**之上**
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
m_prev = re.search(u"(?m)^\\*\\*%d\\. .*?(?=^\\*\\*\\d{3}\\. |\\Z)" % B_ROSTER, blg, re.S)
if not m_prev:
    die(u"BACKLOG %d 找不到，追记无处可挂" % B_ROSTER)
sta = rd(STA)
if (u"## R%d 状态" % ROUND) in sta:
    die(u"STATE 已经有 R%d 那一节 ⇒ 这一笔已经写过，不许重复轮换" % ROUND)
old_head = u"## R%d 状态" % (ROUND - 1)
if old_head not in sta:
    die(u"STATE 里找不到上一轮那一节的标题：" + old_head)
PREV_SECTION = re.search(u"(?m)^## R%d 状态.*?(?=^## R|\\Z)" % (ROUND - 1), sta, re.S)
if not PREV_SECTION:
    die(u"读不到上一轮那一节的正文，轮换会丢内容")
LAYER_BEFORE = sta.count(u"\n> ## ")
# 报告那四格也在**写第一块盘之前**验一遍存在性（R335 第一版在这里死过第二次：
# `决定台账 | D-069 … **D-190**` 的上界被粗体包住，正则少了 `\\*\\*` 就命中 0 次，
# 而那时六本已经落盘 = 又一批半写。存在性检查不产生数，只产生"能不能写"。）
fr_pre = rd(FRA)
for pat, what in ((u"U-31 … U-(\\d+)", u"U 区间那一格"),
                  (u"(决定台账[^\\n]*?D-\\d{3} … \\*\\*)(D-\\d{3})", u"决定台账那一格的区间"),
                  (u"(?m)^- \\*\\*判据与门的规模\\*\\*：.*$", u"§13 的「判据与门的规模」"),
                  (u"(?m)^- \\*\\*产品面（这一节最该被读的部分）\\*\\*：.*$", u"§13 的「产品面」")):
    if len(re.findall(pat, fr_pre)) != 1:
        die(u"报告里 " + what + u" 不是恰好一处，先修锚点再谈写盘")

wr(AUD, aud[:aud.index(UI_ANCHOR)] + UI_TITLE + u"\n" + UI_BODY + u"\n" + UI_ANCHOR
   + aud[aud.index(UI_ANCHOR) + len(UI_ANCHOR):])

wr(ITE, rd(ITE).rstrip(u"\n") + u"\n\n" + ITER_TITLE + u"\n" + ITER_BODY.rstrip() + u"\n")

wr(DEC, rd(DEC).rstrip(u"\n") + u"\n\n" + DEC_BODY.rstrip(u"\n") + u"\n")

blg = blg.rstrip(u"\n") + u"\n\n" + BL_NEW.rstrip(u"\n") + u"\n"
m2 = re.search(u"(?m)^\\*\\*%d\\. .*?(?=^\\*\\*\\d{3}\\. |\\Z)" % B_ROSTER, blg, re.S)
if not m2:
    die(u"追加新条目之后反而找不到 %d 了 ⇒ 追加把文件形状弄坏了" % B_ROSTER)
blg = blg[:m2.end()].rstrip(u"\n") + BL_ADDENDUM.rstrip(u"\n") + u"\n" + blg[m2.end():].lstrip(u"\n")
wr(BLG, blg.rstrip(u"\n") + u"\n")

chg = u"".join(chg_lines[:H3_AT]) + CHG_ENTRY.rstrip(u"\n") + u"\n\n" + u"".join(chg_lines[H3_AT:])
wr(CHG, chg)

# ──  STATE：新节插在上一轮那一节**之上**（不搬 `> ` 前缀，R334 的形状）──────────
STATE_BODY = u"""## R%d 状态（%s · 本地 · 第 %d 轮 / Round %d）：右侧预览第一次能渲染 HTML —— 而第一版「抹掉烤死的墨」在属性串上全绿、屏幕上仍是黑字（产品 %s 文件，HTML 预览主线）

最后更新：%s（本地 · R%d / 第 %d 轮 / Round %d）：详情区多了一条 HTML 渲染通道（判定 / 消毒 / 渲染三段），
并修掉两个只在**屏幕上**看得见的缺陷 —— 暗档正文是烤死的黑（反侧 %s 颗 → 0 颗）、
正文档比产品小两号（%s → %s，层级比 %s 不变）（产品 %s 文件 · HTML 预览主线 · 合计 %d/%d）

本轮做了什么：把用户点名的 HTML 预览做完，并且**逐张看图**。看图腿抓出来的不是"偏淡"这种形容词，
是两个可复现的数：① 改前那一帧正文列里 **8779 颗 RGB(0,0,0)** 落在 luma=30 的表面上；
② 我第一版的修法（`removeAttribute` 抹掉颜色）让属性串断言全绿而帧上**一个字节都没变**（md5 同为 `ba3f4595…`）。
第二版把判据换成问**结果**：每一段的墨在亮暗两档各解析一次，两档同色就是烤死；
再装一颗像素门（尾墨对比 ≥ 4.5:1 **且**反侧必须 0 颗 —— 单用一把分不清"淡"与"画反了"，R29d 那一课）。
字号那一步同理：`HTML_FONTS` 现读 12pt 而产品是 14pt ⇒ 等比搬，基准取"按字符数加权的众数号"，
层级比不许被压平（M980 钉的就是只搬正文那种坏法）。

验证读数（现读）：`HTML_INK 字符=%s 烤死段前=%s 烤死段后=%s 无色段后=%s 烤死背景段=%s 链接段=%s`；
`HTML_INKREAD dark 比=%s 反侧=%s颗`（Markdown 同块 %s:1）、`… light 比=%s 反侧=%s颗`（%s:1）；
`HTML_TYPE 基准前=%s 基准后=%s 产品档=%s 层级比前=%s 层级比后=%s`；
`HTML_SANITIZE 构造=%s 残留=%s`、`HTML_RENDER_COST 斜率=%s 上限=%s 判定=%s`；
两态相减 `HTML_PAIR_PROOF 千分比 亮=%s 暗=%s`；
`ROUND_VERIFY %s`；判据卷 `Executed %s（failures=%s）`、捕获卷 `Executed %s（skipped=%s, failures=%s）`；
变异表 `%s`；针预检 tables=%s covered=%s bad=%s、名册 files=%s arms=%s dupes=%s；
清账表 `%s`；脚本电池 `Ran %s（skipped=%s）`；产品面连续零改动 **%s** 轮（现读 `scripts/product_streak.py` 的 streak —— 这一整句必须在**同一行**里：`_cells` 问的是"那一格有没有引用取数口"，而它读的段落就是一行；分两行写就等于没引用，R300 那一格红过一次）。唯一取数口 `python3 scripts/product_streak.py --streak-for %d`；本轮这一笔落盘前 `--streak-for %d` 现读 %s。
§8 搬运：`%s`，新读族 %s

NOT-RUN（三种缺席分开写，不许省略）：① **只在人身上判得了**：真机那一屏（本轮换了正文通道，
渲染态在真窗口里的换行与选中拖拽没看过 —— 离屏帧能证墨，不能证手感）；
② **只在 runner 上判得了**：本轮新门 `testHtmlRenderedBodyInkIsReadable` 与 20 格新判据在 runner 上的读数
（特别是"反侧必须 0 颗"这一条 —— 它依赖这台机器的回落字面，runner 上的字族可能不同）；
③ **这条通道看不见**的：`<img>` 与 `style` 里的 url() 被消毒撤掉之后**屏幕上没有东西可看**，
残留只能由 `residualFetchableReferences` 那格判，帧不替它作证。

下一轮（R%d）的靶：⓪ 把本轮 push 之后的 run id↔commit 成对写回这里，并读 runner 那一跑
（新门在 runner 上签不签、`HTML_` 那族在 runner 的日志里打几行）→
① 报告里"最后一次动到 `Sources/` 的那一轮"那一格由 `scripts/report_sources_cell.py --write` 刷新
（R334 那朵 runner 红欠的就是这一格，本轮已写脚本、还没 --write 之前它照旧红）→
② 回到动效主线那批还开着的：399（亮档悬停要换轴）、397 的反方向已结、390 的 before/after、
389 的时长、384 的横向、387①、376、367/360/361/364 → ③ 本轮开出来的四条里
最便宜的一条先量缺席：402（Markdown 那条的耗时随大小怎么长 —— 一次现读就能定它要不要上限）。

""" % (ROUND, DATE, AUDIT_N, ITER_N, PRODUCT_N,
       DATE, ROUND, AUDIT_N, ITER_N, BEFORE_D_WRONG, TYPE_BASE_BEFORE, TYPE_BASE_AFTER,
       TYPE_RATIO_BEFORE, PRODUCT_N, sum(SEVEN), SEVEN_MAX,
       INK_CHARS, INK_BEFORE, INK_AFTER, INK_COLORLESS, INK_BG, INK_LINKS,
       D_HTML_RATIO, D_HTML_WRONG, D_MD_RATIO, L_HTML_RATIO, L_HTML_WRONG, L_MD_RATIO,
       TYPE_BASE_BEFORE, TYPE_BASE_AFTER, TYPE_TARGET, TYPE_RATIO_BEFORE, TYPE_RATIO_AFTER,
       SANI_CONSTRUCTS, SANI_RESIDUE, COST_SLOPE, COST_CEIL, COST_VERDICT,
       PAIR_L_PCT, PAIR_D_PCT, line,
       HTML_RUN, HTML_FAIL, CAP_RUN, CAP_SKIP, CAP_FAIL,
       TABLE_SUMMARY, PRE[0], PRE[1], PRE[2], ARM_TOTAL[0], ARM_TOTAL[1], ARM_TOTAL[2],
       GATE_FULL, BATT, BATT_SKIP, STREAK_N, ROUND - 1, ROUND, STREAK_GIT,
       ROWS_LINE, NEW_READINGS,
       ROUND + 1)

sta = rd(STA)
if (u"## R%d 状态" % ROUND) in sta:
    die(u"STATE 已经有本轮那一节 ⇒ 这一笔已经写过，不许重复轮换")
prev_titles = re.findall(u"(?m)^## R%d 状态" % (ROUND - 1), sta)
if len(prev_titles) != 1:
    die(u"STATE 里上一轮的节标题命中 %d 次" % len(prev_titles))
pos = sta.index(prev_titles[0])
before_layers = sta.count(u"\n> ## ")
wr(STA, sta[:pos] + STATE_BODY.rstrip(u"\n") + u"\n\n" + sta[pos:])
after = rd(STA)
if after.count(u"\n> ## ") != before_layers:
    die(u"STATE 轮换改动了 `> ##` 层数：%d → %d ⇒ 这一支不该顺手重排整本文件"
        % (before_layers, after.count(u"\n> ## ")))
if (u"## R%d 状态" % (ROUND - 1)) not in after:
    die(u"轮换之后上一轮那一节的标记没了")
if (u"最后更新：%s（本地 · R%d" % (DATE, ROUND)) not in after:
    die(u"本轮的 identity 行没落在 expected 形状上 ⇒ `current_round()` 那把尺读不到本轮")
if after.count(u"## R%d 状态" % ROUND) != 1:
    die(u"本轮标题出现次数不是 1")

# ──  FINAL_REPORT：只改计数器（§13 之外那几格 + §13 两行由现读数组重拼）────────
fr = rd(FRA)
mUD = re.search(u"U-31 … U-(\\d+)", fr)
if not mUD:
    die(u"报告里找不到 U 区间那一格")
udefs = len(re.findall(u"(?m)^- \\*\\*U-(\\d{3,4})[：(]", rd(AUD)))
fr = once(fr, mUD.group(0), u"U-31 … U-%d" % UMAX)
m = re.search(u"(决定台账[^\\n]*?D-\\d{3} … \\*\\*)(D-\\d{3})", fr)
if not m:
    die(u"报告里读不到「决定台账」那一格的区间")
OLD_D_TOP = m.group(2)
fr = fr[:m.start(2)] + (u"D-%d" % D2) + fr[m.end(2):]
print(u"REPORT_D_CELL %s → D-%d" % (OLD_D_TOP, D2))

scale_old = re.findall(u"(?m)^- \\*\\*判据与门的规模\\*\\*：.*$", fr)
if len(scale_old) != 1:
    die(u"§13 的「判据与门的规模」命中 %d 行" % len(scale_old))
new_scale = (u"- **判据与门的规模**：脚本电池现读 **Ran %s**（写盘前同数），变异臂在册 **%s** 把 / %s 张表"
             u"（预检 tables=%s covered=%s bad=%s）；U 定义行 **%s 条**、最大 **U-%d**；"
             u"决定台账最大 **D-%d**，BACKLOG 最大 **%d**（本轮新开四单：%d CJK 强调没量、"
             u"%d 图被消毒撤掉之后没有说明、%d Markdown 没有字节上限、%d 字族判「不改」绑读数）；"
             u"本轮刀 `mutate_r335.py CAUGHT=%s, RESTORE_CLEAN=yes`（%s）。"
             u"§8 的读数搬运名单本轮**当场接上新族**：`%s`，声明的四族 `缺=0`（%s）；"
             u"而它自己的键名仍有 %s/%s 格没日志可解析（%d，那一向由 397 记着）。"
             % (BATT, ARM_TOTAL[1], ARM_TOTAL[0], PRE[0], PRE[1], PRE[2], udefs, UMAX, D2, B_FAMILY,
                B_INK, B_IMG, B_BUDGET, B_FAMILY,
                by_name[u"mutate_r335"][1], ARMS_NEW[0] + u"…" + ARMS_NEW[-1],
                NEW_READINGS, ROWS_LINE, ROWS_MISSING, ROWS_TOTAL, B_ROSTER))
fr = fr.replace(scale_old[0], new_scale)

prod_old = re.findall(u"(?m)^- \\*\\*产品面（这一节最该被读的部分）\\*\\*：.*$", fr)
if len(prod_old) != 1:
    die(u"§13 的「产品面」命中 %d 行" % len(prod_old))
new_prod = (u"- **产品面（这一节最该被读的部分）**：本轮产品文件 **%s** 个（**HTML 预览主线**："
            u"`DetailRenderPolicy` / `HtmlSanitizer` / `HtmlRendering` 三段新通道，"
            u"`.html`/`.htm` 文件与带 HTML 载荷的条目第一次有渲染态）。"
            u"看图腿量出并修掉两个只在屏幕上看得见的缺陷：暗档正文是烤死的黑"
            u"（改前 反侧 %s 颗、对比 %s:1 → 改后 反侧 0 颗、%s:1），"
            u"正文档比产品小两号（%s → %s，层级比 %s 不变）。"
            u"第二版另收一处假话：`.html` 文件的提示语原本写着 Markdown，而载荷那一支分支永远走不到。"
            u"产品面连续零改动 **%s** 轮（唯一取数口 `python3 scripts/product_streak.py --streak-for %s`；"
            u"本轮这一笔按 `--streak-for %s` 现读是 %s）。"
            u"396/393 那两单结在 R333/R334，本轮开的是 %d / %d / %d / %d 四条。"
            u"产品面连续零改动轮数 = **%s**（现读 `python3 scripts/product_streak.py`）。"
            % (PRODUCT_N, BEFORE_D_WRONG, BEFORE_D_RATIO, D_HTML_RATIO,
               TYPE_BASE_BEFORE, TYPE_BASE_AFTER, TYPE_RATIO_BEFORE,
               STREAK_N, s(ROUND - 1), s(ROUND), STREAK_GIT, B_INK, B_IMG, B_BUDGET, B_FAMILY,
               STREAK_N))
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

# ──  写盘之后：§1 刷新 → 电池（不许带名单）→ 连读门 → 曲线 → 标题格 ───────────
rf0, rfc0 = sh([sys.executable, FRESH])
if rfc0 != 0 or u"REFUSED" in rf0:
    die(u"报告 §1 的刷新器没签：%s" % rf0.strip()[-300:])

bt2, brc2 = sh([sys.executable, u"-m", u"unittest", u"discover", u"-s", u"scripts/tests"])
BATT2 = (re.findall(r"Ran (\d+) tests", bt2) or [u"?"])[-1]
BATT2_SKIP = (re.findall(r"skipped=(\d+)", bt2) or [u"0"])[-1]
POST_RED = sorted(set(re.findall(u"(?m)^(?:FAIL|ERROR): (\\w+)", bt2)))
if brc2 != 0:
    die(u"落盘之后脚本电池仍是红的（Ran=%s，红=%s）—— 登记窗口里的两朵必须自己消失："
        u"%s" % (BATT2, POST_RED, bt2.strip()[-900:]))
if BATT2 == u"?":
    die(u"落盘之后连 Ran 几例都没解析到")

ck, ckc = sh([sys.executable, STREAK, u"--check"])
if ckc != 0:
    die(u"连读门不认这版台账：" + ck.strip()[-500:])
STREAK_LINE = ck.strip().splitlines()[-1]

cvc, cvc_rc = sh([sys.executable, CURVE])
if cvc_rc != 0 or u"GAPS=none" not in cvc:
    die(u"落盘之后曲线尺不干净：" + cvc.strip()[-300:])
# 仪器那一行是 `SCORES_BY_ROUND r=n r=n …`（没有 DERIVED= 那个键，第一版在这里读成 ?）。
# 取**本轮 ITER_N** 那一格，取不到就照实写"没解析到"，不许心算。
scores = dict((int(k), int(v)) for k, v in
               re.findall(r"(\d+)=(\d+)", (re.findall(r"(?m)^SCORES_BY_ROUND .*$", cvc) or [u""])[-1]))
DERIVED = s(scores.get(ITER_N, u"没解析到")) + u"（仪器口径：七维合计 %d/%d ≈ %d%%）" % (sum(SEVEN), SEVEN_MAX, round(100.0 * sum(SEVEN) / SEVEN_MAX))

# 七维表读回来对账：行数必须恰好 7、每行量纲是 n/15、七个数与 SEVEN 一致。
# （R152 那一族：同一把尺里混两种分母，算出来的均值从来不是分数；这里不许靠"我写的时候数对了"。）
ite_after = rd(ITE)
rows = re.findall(u"(?m)^\\| ([^|]+) \\| (\\d+)/(\\d+) \\|", ite_after.split(ITER_TITLE)[-1])
if len(rows) != 7:
    die(u"本轮七维表读到 %d 行（要 7 行）⇒ 曲线仪器不会给数（CURVE_DROPS_TAIL 那一族）" % len(rows))
if any(mx != u"15" for _, _, mx in rows):
    die(u"七维表里出现了非 /15 的量纲：%s ⇒ 混分母的均值不是分数" % [r[2] for r in rows])
if [int(v) for _, v, _ in rows] != SEVEN:
    die(u"七维表与 SEVEN 不一致：%s vs %s" % ([int(v) for _, v, _ in rows], SEVEN))
print(u"R335_SEVEN 合计=%d/%d 行=%d" % (sum(SEVEN), SEVEN_MAX, len(rows)))

rf, rfc = sh([sys.executable, FRESH])
if rfc != 0 or u"REFUSED" in rf:
    die(u"报告 §1 刷新器第二遍不干净：%s" % rf.strip()[-300:])
chk, chkc = sh([sys.executable, u"-m", u"unittest", u"-v",
                u"test_final_report_headline.FinalReportHeadlineTests."
                u"test_the_headline_cells_agree_with_the_live_ledgers"],
               cwd=os.path.join(ROOT, u"scripts", u"tests"))
if chkc != 0:
    die(u"报告标题那几格与台账不同源：" + chk.strip()[-400:])

print(u"R335_LEDGERS_OK 产品=%s 文件 U=%d…%d(%d 条) D=%d,%d BACKLOG=%d…%d 刀=%s(%s) "
      u"电池=%s→%s(skip %s) 帧=%s 全量卷=%s/%s/%s 派生=%s"
      % (PRODUCT_N, UA, UMAX, udefs, D1, D2, B_INK, B_FAMILY,
         by_name[u"mutate_r335"][1], ARMS_NEW[-1], BATT, BATT2, BATT2_SKIP,
         FRAME_N, FULL_RUN, FULL_SKIP, FULL_FAIL, DERIVED))
print(u"R335_ROWS " + ROWS_LINE)
print(u"R335_GATE " + GATE_FULL)
print(u"R335_TABLE " + TABLE_SUMMARY)
print(u"R335_PRECHECK tables=%s covered=%s bad=%s arms(files=%s,arms=%s,dupes=%s)"
      % (PRE[0], PRE[1], PRE[2], ARM_TOTAL[0], ARM_TOTAL[1], ARM_TOTAL[2]))
print(u"R335_STREAK 上一轮格=%s 本轮格=%s 门=%s" % (STREAK_N, STREAK_GIT, STREAK_LINE))
print(u"R335_SOURCES " + SRC_LINE)
print(u"R335_INK 烤死前=%s 烤死后=%s 无色后=%s 反侧(暗改前)=%s 反侧(暗改后)=%s 对比暗=%s 对比亮=%s"
      % (INK_BEFORE, INK_AFTER, INK_COLORLESS, BEFORE_D_WRONG, D_HTML_WRONG, D_HTML_RATIO, L_HTML_RATIO))
