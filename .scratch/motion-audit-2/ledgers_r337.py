#!/usr/bin/env python3
# -*- coding: utf-8 -*-
u"""R337 的台账生成器（第 336 轮 / Round 334 · 全历史回顾 · 产品 0 文件）。

这一轮不修产品，做的是用户点名的那件事：**把这么长时间的工作慢慢回头复核一遍**。
复核量到的东西全部由仪器现读，写盘之前每个锚点先统一验一遍（命中 0 次或多次都在写任何盘
之前抱出）。数字一律从当场跑完的日志里解析，不许手填：

  /tmp/r337_review.log     —— review_full_history.py：全长度扫三本账的 12 行读数
  /tmp/r337_py.log         —— 脚本电池（Ran / skipped / OK）
  /tmp/r337_precheck.log   —— 针预检 tables/covered/arms/bad + ARM_TOTAL files/arms
  /tmp/r337_t_r337.log     —— 本轮四把刀
  /tmp/r337_gate.log       —— 清账表那一行
  /tmp/r337_streak.log     —— product_streak --check 与 --streak-for 337
  /tmp/r337_baseline.log   —— 帧基线（复用上轮 182 张，本轮零产品改动 ⇒ CHANGED 必须 0）
  /tmp/r337_ink.log        —— row_ink_probe.py：暗档左列文字与选中块的两个方向读数
  /tmp/r337_curve.log      —— 曲线仪器 GAPS / PHASE2 / SCORES_BY_ROUND

跑法：PYTHONUTF8=1 python3 .scratch/motion-audit-2/ledgers_r337.py
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
FRESH = os.path.join(ROOT, u".scratch", u"motion-audit-2", u"refresh_report_section1.py")
SRCCELL = os.path.join(ROOT, u"scripts", u"report_sources_cell.py")
ROWS = os.path.join(ROOT, u".scratch", u"motion-audit-2", u"ledger_rows.py")

REVIEW = u"/tmp/r337_review.log"
BATT_LOG = u"/tmp/r337_py.log"
PRECHK_LOG = u"/tmp/r337_precheck.log"
TABLE_LOG = u"/tmp/r337_t_r337.log"
GATE_LOG = u"/tmp/r337_gate.log"
STREAK_LOG = u"/tmp/r337_streak.log"
BASE_LOG = u"/tmp/r337_baseline.log"
INK_LOG = u"/tmp/r337_ink.log"
CURVE_LOG = u"/tmp/r337_curve.log"

ENV = dict(os.environ)
ENV[u"PYTHONUTF8"] = u"1"
ENV[u"PYTHONDONTWRITEBYTECODE"] = u"1"

ROUND = 337
AUDIT_N = 336
ITER_N = 334
DATE = u"2026-10-25"
PRODUCT_N = 0
UA, UB, UC, UD, UE, UF, UG, UH, UI2 = 1137, 1138, 1139, 1140, 1141, 1142, 1143, 1144, 1145
UJ = 1146
UMAX = UJ
D1 = 333
B_STATE = 407          # STATE 的十轮历史空洞
B_CENSUS = 408         # 报告里两格同名「判据与门的规模」
B_INK = 409            # 暗档左列文字 1.23:1：通道还是产品，今天分不开
B_HOLE = 229           # 追记：选中行整块纯黑，两档都黑
B_PARA = 406           # 追记：那一处紧挨的主语就是 alt 那句
ARMS_NEW = (u"M989", u"M990", u"M991", u"M992")
# 七维度自评（ITERATION 那张表必须与它一致；写盘后读回来对账）
SEVEN = [12, 14, 15, 8, 14, 15, 14]
SEVEN_MAX = 15 * 7

WRITTEN = []


def rd(path):
    return io.open(path, encoding=u"utf-8").read()


def wr(path, text):
    io.open(path, u"w", encoding=u"utf-8").write(text)
    WRITTEN.append(path)


def sh(cmd):
    p = subprocess.run(cmd, cwd=ROOT, env=ENV, stdout=subprocess.PIPE,
                       stderr=subprocess.STDOUT)
    return p.stdout.decode(u"utf-8", u"replace"), p.returncode


def die(msg):
    print(u"LEDGERS_R337_DIED " + msg)
    for p in WRITTEN:
        print(u"  已写盘：" + p)
    sys.exit(1)


def once(text, anchor, replacement):
    n = text.count(anchor)
    if n != 1:
        die(u"锚点命中 %d 次（要 1 次）：%s" % (n, anchor[:90]))
    return text.replace(anchor, replacement)


def require(path):
    if not os.path.exists(path):
        die(u"证人日志不在盘上：" + path + u" ⇒ 那一格的数没处解析，不许手填")
    return rd(path)


def line_with(log, key, where):
    for ln in log.splitlines():
        if key in ln:
            return ln
    die(u"日志里找不到含 " + key + u" 的那一行（" + where + u"）")


def num(text, key, where):
    m = re.search(re.escape(key) + u"=([-+0-9.%…未空无/]+)", text)
    if not m:
        die(u"读数里缺 " + key + u"（" + where + u"）：" + text[:160])
    return m.group(1)


# ── 现读 ─────────────────────────────────────────────────────────────────────
rev = require(REVIEW)
batt_log = require(BATT_LOG)
pre = require(PRECHK_LOG)
tbl = require(TABLE_LOG)
gate_log = require(GATE_LOG)
streak_log = require(STREAK_LOG)
base_log = require(BASE_LOG)
ink_log = require(INK_LOG)
curve_log = require(CURVE_LOG)

BATT = (re.findall(u"Ran (\\d+) tests", batt_log) or [None])[-1]
if BATT is None:
    die(u"电池日志里没有 `Ran N tests` ⇒ 例数没出处")
if u"\nOK" not in batt_log or u"FAILED" in batt_log:
    die(u"电池不是绿的，先修再写盘：" + batt_log.strip()[-300:])
BATT_SKIP = (re.findall(u"OK \\(skipped=(\\d+)\\)", batt_log) or [u"0"])[-1]

PRE_LINE = line_with(pre, u"NEEDLE_PRECHECK", u"针预检")
PRE = [num(PRE_LINE, u"tables", u"针预检"), num(PRE_LINE, u"covered", u"针预检"),
       num(PRE_LINE, u"arms", u"针预检"), num(PRE_LINE, u"bad", u"针预检")]
if PRE[3] != u"0":
    die(u"针预检 bad=" + PRE[3] + u" ⇒ 有针命中 0 或 >1，先修针")
ARM_LINE = line_with(pre, u"ARM_TOTAL", u"臂名册")
ARM_TOTAL = [num(ARM_LINE, u"files", u"臂名册"), num(ARM_LINE, u"arms", u"臂名册")]
if u"dupes=0" not in ARM_LINE:
    die(u"臂名册有撞号：" + ARM_LINE)

CAUGHT = num(line_with(tbl, u"CAUGHT=", u"变异表"), u"CAUGHT", u"变异表")
_m = re.search(u"RESTORE_CLEAN=(\\w+)", tbl)
if not _m:
    die(u"变异表没打 RESTORE_CLEAN ⇒ 盘上可能还留着刀：" + tbl.strip()[-200:])
RESTORE = _m.group(1)
if RESTORE != u"yes":
    die(u"变异表没还原干净（RESTORE_CLEAN=" + RESTORE + u"）⇒ 盘上可能还留着刀")

GATE_LINE = line_with(gate_log, u"MOTION_LEDGER ", u"清账表")
STREAK_CHECK = line_with(streak_log, u"PRODUCT_STREAK_LEDGER_OK", u"连读门")
# 取数口**当场调用**，不读旧日志：这一格的口径是「台账的第 N 轮」，不是 R 号。
# 本轮实测两者差一：`--streak-for 336`（=第 336 轮）给 1，`--streak-for 337`（R 号）给 2，
# 而电池里那格守卫读的是前者 ⇒ 台账必须写前者。这是一次"同一个数两个口径"的现场，记进 STATE 自伤。
sk_a, sk_rc = sh([sys.executable, STREAK, u"--streak-for", str(AUDIT_N)])
sk_b, _ = sh([sys.executable, STREAK, u"--streak-for", str(ROUND)])
if sk_rc != 0:
    die(u"--streak-for " + str(AUDIT_N) + u" 跑不通：" + sk_a.strip()[-300:])
STREAK_N = num(line_with(sk_a, u"PRODUCT_STREAK_FOR", u"连读取数口"), u"streak", u"连读(台账口径)")
STREAK_R = num(line_with(sk_b, u"PRODUCT_STREAK_FOR", u"连读取数口"), u"streak", u"连读(R 号口径)")

BASE = [num(base_log, u"FRAME_BASELINE_COMPARED", u"基线"),
        num(base_log, u"FRAME_BASELINE_CHANGED", u"基线"),
        num(base_log, u"FRAME_BASELINE_MISSING", u"基线"),
        num(base_log, u"FRAME_BASELINE_ADDED", u"基线")]
if BASE[0] == u"0":
    die(u"基线 COMPARED=0 ⇒ CHANGED=0 是空对账，这一格只能记 NOT-RUN")
if BASE[1] != u"0" or BASE[2] != u"0" or BASE[3] != u"0":
    die(u"零产品改动的轮子里基线不该动：CHANGED=" + BASE[1] + u" MISSING=" + BASE[2] +
        u" ADDED=" + BASE[3])

INK_DARK_ROW = line_with(ink_log, u"ROW_INK dark 行1文字", u"行墨尺")
INK_LIGHT_ROW = line_with(ink_log, u"ROW_INK light 行1文字", u"行墨尺")
INK_BLOCK_D = line_with(ink_log, u"ROW_INK dark 选中块内", u"行墨尺")
INK_BLOCK_L = line_with(ink_log, u"ROW_INK light 选中块内", u"行墨尺")
INK_DETAIL = line_with(ink_log, u"ROW_INK dark 详情头", u"行墨尺")
# 「落后多少轮」必须取**补写之前**那一份：回顾尺在 §14 落盘之后重跑会报 0（门已经绿了），
# 而 U-1142 讲的是补写之前那件事。出处是 §14 自己那句现读（它由 report_section14.py 生成）。
LAG_BEFORE = (re.findall(u"停在 R298，落后 \\*\\*(\\d+) 轮\\*\\*",
                          rd(FRA)) or [None])[0]
if LAG_BEFORE is None:
    die(u"报告 §14 里没有那句落后读数 ⇒ 落后轮数没出处，不许手填")
# 暗档那一行**两个方向都打**：第一个比是亮侧（暗档左列亮墨=0 ⇒ 0.00:1，意思是「没有亮墨」），
# 第二个才是暗侧（黑字对底）。取错下标 = 把这条 finding 洗成它的反面。
RATIO_DARK_ROW = (re.findall(u"比 ([0-9.]+):1", INK_DARK_ROW) or [None, None])[1]
RATIO_LIGHT_ROW = (re.findall(u"比 ([0-9.]+):1", INK_LIGHT_ROW) or [None, None])[1]
RATIO_DETAIL = (re.findall(u"比 ([0-9.]+):1", INK_DETAIL) or [None, None])[0]
if not (RATIO_DARK_ROW and RATIO_LIGHT_ROW and RATIO_DETAIL):
    die(u"行墨尺的比没解析到")
if RATIO_DARK_ROW == u"0.00":
    die(u"暗侧比读成 0.00 ⇒ 十有八九又取了亮侧那一个（这一族本轮真栽过）")
    die(u"行墨尺的比没解析到：" + INK_DARK_ROW + u" / " + INK_LIGHT_ROW + u" / " + INK_DETAIL)

REVIEW_U = line_with(rev, u"REVIEW_U_RANGE", u"回顾尺")
REVIEW_BL = line_with(rev, u"REVIEW_BL_REF", u"回顾尺")
REVIEW_HOLES = line_with(rev, u"REVIEW_BL_HOLES", u"回顾尺")
REVIEW_STATE = line_with(rev, u"REVIEW_STATE", u"回顾尺")
REVIEW_REPORT = line_with(rev, u"REVIEW_REPORT_RANGE", u"回顾尺")
REVIEW_CLAIMS = line_with(rev, u"REVIEW_COMMIT_CLAIMS", u"回顾尺")
REVIEW_CHANGELOG = line_with(rev, u"REVIEW_CHANGELOG", u"回顾尺")
HOLES = (re.findall(u"空号=\\d*\\s*\\[([^\\]]*)\\]", REVIEW_HOLES) or [None])[0]
if HOLES is None:
    die(u"回顾尺没打空号名单：" + REVIEW_HOLES)
# STATE 缺多少轮：回顾尺打的是「节=N 覆盖 Rlo…Rhi」，缺节 = 区间长度 − 节数（重复=[] 时才成立）
_sec = num(REVIEW_STATE, u"节", u"回顾尺 STATE 行")
_rep = re.findall(u"覆盖 R(\\d+)…R(\\d+)", REVIEW_STATE)
if not _rep or u"重复=[]" not in REVIEW_STATE:
    die(u"回顾尺的 STATE 行缺「覆盖 R…R…」或有重复节 ⇒ 缺节数推不出来：" + REVIEW_STATE)
if u"顺序倒置=0" not in REVIEW_STATE:
    die(u"回顾尺的 STATE 行报了顺序倒置 ⇒ 先修尺再谈写盘：" + REVIEW_STATE)
MISSING_STATE = str(int(_rep[0][1]) - int(_rep[0][0]) + 1 - int(_sec))
print(u"R337_STATE_HOLES 节=%s 覆盖=%s…%s ⇒ 缺=%s" % (_sec, _rep[0][0], _rep[0][1], MISSING_STATE))

PHASE2 = line_with(curve_log, u"PHASE2 n=", u"曲线")
if u"GAPS=none" not in curve_log:
    die(u"曲线尺不干净，先修再写盘：" + curve_log.strip()[-200:])

aud = rd(AUD)
ui_titles = re.findall(u"(?m)^## 第 (\\d+) 轮.*$", aud)
UI_ANCHOR = line_with(aud, u"## 第 %d 轮" % (AUDIT_N - 1), u"UI_AUDIT 顶节")
udefs_before = len(re.findall(u"(?m)^- \\*\\*U-(\\d{3,4})[：(]", aud))

sta = rd(STA)
if (u"## R%d 状态" % ROUND) in sta:
    die(u"STATE 已经有 R%d 那一节 ⇒ 这一笔已经写过，不许重复轮换" % ROUND)
if len(re.findall(u"(?m)^## R%d 状态" % (ROUND - 1), sta)) != 1:
    die(u"STATE 里上一轮的节标题不是恰好一处")
before_layers = sta.count(u"\n> ## ")

fr_pre = rd(FRA)
CENSUS_PAT = u"(?m)^- \\*\\*判据与门的规模\\*\\*：.*$"
census_hits = re.findall(CENSUS_PAT, fr_pre)
if len(census_hits) != 2:
    die(u"报告里「判据与门的规模」现在应是 2 格（§13 历史 + §14 现读），实得 %d 格 ⇒ "
        u"这一轮的写法要跟着改" % len(census_hits))
S13_AT = line_with(fr_pre, u"脚本电池现读 **Ran", u"§13 那一格")
S14_AT = line_with(fr_pre, u"脚本电池 `Ran", u"§14 那一格")
if fr_pre.count(S13_AT) != 1 or fr_pre.count(S14_AT) != 1:
    die(u"两格 census 的定位不唯一：§13=%d §14=%d" % (fr_pre.count(S13_AT), fr_pre.count(S14_AT)))
S14_TITLE = line_with(fr_pre, u"## 14. R299 → R336", u"§14 标题")

blg_pre = rd(BLG)
for bid in (B_HOLE, B_PARA):
    if not re.search(u"(?m)^\\*\\*%d\\. " % bid, blg_pre):
        die(u"BACKLOG %d 找不到，追记无处可挂" % bid)
for bid in (B_STATE, B_CENSUS, B_INK):
    if re.search(u"(?m)^\\*\\*%d\\. " % bid, blg_pre):
        die(u"BACKLOG %d 已经存在 ⇒ 编号被占了，先查再写" % bid)

chg_lines = rd(CHG).splitlines(True)
H3_AT = [i for i, ln in enumerate(chg_lines) if ln.rstrip(u"\n") == u"## [Unreleased]"]
if len(H3_AT) != 1:
    die(u"`## [Unreleased]` 命中 %d 次（要 1 次）" % len(H3_AT))

# ── 正文：UI_AUDIT ───────────────────────────────────────────────────────────
UI_TITLE = (u"## 第 %d 轮（R%d · %s · U-%d…U-%d）：把三本账按**全长度**扫一遍，"
            u"顺手量到看图这条腿自己会美化（U-%d…U-%d · 产品 %d 文件，回顾轮）\n"
            % (AUDIT_N, ROUND, DATE, UA, UMAX, UA, UMAX, PRODUCT_N))

UI_BODY = u"""- **U-%d：报告里那一格被两处同时写，门当场红了 —— 而那两个数**相等**** —— 本轮 §14 的第一版把「产品面连读」\
也抄了一遍，`test_product_streak_cell` 立刻红在「同一格里出现 2 个候选数」。它不管相等不相等：\
相等只是这一次运气，两处权威下一次一定会漂。处置是**把数退回唯一取数口**（`scripts/product_streak.py`），\
§14 只写"这一格不在本节重抄"并把红的理由留在正文里。
- **U-%d：同一份报告里现在有两格同名标签「判据与门的规模」** —— §13 那格（R336 之前每轮刷新）与 §14 那格\
（本轮新写）。R336 生成器的预检写着"这格必须恰好一处"，**今天它已经不成立** —— 下一轮沿用那支预检会当场 die。\
本轮的处置：① 两格定位改成按**内容**而不是按标签（§13 那格带「现读 **Ran」，§14 那格带反引号）；\
② §13 那格**冻结成历史**并写明"R337 起由 §14 接手"，不让它继续冒充最新；③ 登记成 BACKLOG %d ——\
"最新那一格住在哪一节"今天仍靠约定，没做成会红的门。
- **U-%d：回顾尺的第一版报了五百来处"问题"，其中五种都是尺自己的口径病** ——\
  字符串集合与整数集合比较（D 号那条恒不等）、`re.split` 之后拿错索引、把「| 合计 | 82/105 |」那一行当条目、\
  把 CHANGELOG 的子标题（Build / Release / Tests）当轮次条目、以及**拿一把只认 3〜4 位号的尺去判 1〜2 位的老条目不存在**\
  （一次报出 289 处悬空引用）。修完之后真 finding 只剩四类。这一格要留在账上的不是"尺修好了"，\
  而是**它的 0 处与它的 500 处同样不说明任何事** —— 每一格都配了内存正对照之后，那个数才有资格进台账。
- **U-%d：四处 `BACKLOG 166/167/169/170` 悬空引用，成因是条目行的形状而不是引用写错** ——\
  那四条正文写的是 `**166.（…）`，点号后面没有空格，而仓库那支共享正则 `ITEM` 要求空格 ⇒ 条目存在却看不见。\
  修法是把**条目**改到规范形状（四条），不是放宽那支正则：放宽等于让"同一份文件两种认法"合法化。\
  改完 `ITEM` 数出的条目从 296 涨到 300（增量由工作区 diff 现读）。新守卫 `test_ledger_citations.py` **导入** `ITEM` 本身，\
  不另抄一颗 —— 另抄就是第二个权威，而"两处各判一遍然后漂开"正是这次出洞的成因（D-%d）。
- **U-%d：`AGENT_STATE.md` 有 %s 轮没有自己的节**（R257、R277、R278、R282…R288）——\
  Skill 里那句"这一处没有守卫"今天被量到了：STATE 是三本账里唯一没人守的那本，\
  而它恰好是"下一轮的靶是什么"的唯一住处。处置分两半：门按**窗口**判（最近 40 轮必须每轮一节，窗口外的洞不放宽窗口），\
  历史空洞登记成 BACKLOG %d 并明写"不补写历史正文 —— 补=伪造记录"。
- **U-%d：报告的叙述节停在 R298，而账已经写到第 %d 轮** —— 落后 %s 轮（`review_full_history.py` 现读），\
  这是这份报告第三次停在几十轮之前。§1 与标题那两格早有守卫（U-264 那一族），**没人守叙述节** ——\
  而读者真正会读的恰恰是叙述节。本轮补了 §14（R299→R336，数字全部现读），并新加一格落后门：\
  地板取 20 轮，**不**放宽到本轮现读的 38 —— 放宽窗口 = 把已经发生的事洗成看不见。
- **U-%d：四把刀，三把钉"检查恒返回空"，一把钉"不共享那颗尺"** —— 现读 `%s`。\
  M989/M990/M991 分别把三格新守卫改成"永远说没问题"，正对照必须点名（不点名 ⇒ 守卫报的 0 处是空的）；\
  M992 把 `test_ledger_citations` 里 `from test_ledger_ids import ITEM` 换成一颗只认四位的本地正则 ⇒\
  引用格与"同一颗尺"那格一起红。这一族的名字：**会红的守卫要有正对照，正对照自己也要能被废掉**。
- **U-%d：看图这条腿第一次量到自己会美化** —— 逐张看已提交的帧时，暗档主列表那几行\
  在我眼里是"可读的灰字"；同一张 PNG 用像素尺读是：文字最暗 %s、底 %s ⇒ **比 %s:1**，\
  而亮档同一块盒子是 %s:1，同一张暗帧的详情区标题是 %s:1（`row_ink_probe.py` 现读，两个方向都数）。\
  预览通道会做增强，所以它能把 1.2:1 画成能读的样子 —— 这条腿**不能替像素尺作证**，反过来也一样。\
  两种解释（注入的 appearance 没进左列 / 产品真的黑字）今天分不开 ⇒ BACKLOG %d，\
  区分它的那一格写清楚了：同一段 Text 走两条路径画出来的参照臂，或者真机眼。
- **U-%d：BACKLOG 229 那个"选中行整块画成纯黑"在已提交的夹具上重现了，而且两档都黑** ——\
  现读 暗档块内 `%s`、亮档块内 `%s`（底都是 0 ⇒ 两档同形）。\
  "是谁"这一半今天答了：它是 `selectOnly` 选中的那一条（`ghp_…`，40 个字符），\
  因为同一张帧的详情区把同一条记录画得清清楚楚（%s:1）⇒ **不是没有内容，是内容没画出来**。\
  "为什么黑"仍欠真机眼，与 373（浮层选中行纯灰）同族但表面不同：这一格在**主窗口列表**。
- **U-%d：上一轮那处「紧挨」的主语，就是上一轮刚修的那句话** —— 看图腿逐张复看 HTML 那两档时读到：\
  「季度趋势图（图片未加载）」这一句在屏幕上**贴着上面那个列表**，而不是贴着下一段。\
  回夹具对源码：`<ul>…</ul>` 之后紧跟的就是那张带 alt 的图 ⇒ R%d 判据里"紧挨 2 处"的第 ② 处\
  量的正是这一对（20.0pt，而两个 `<p>` 之间 31.5pt）。也就是说规则 ④ 兑现了"自成一段"，\
  但块边界仍然读不出来 —— 406 那条"渲染器不给 `<ul>` 下边距"的现状，落点不在无关文字上，\
  而在这条刚上线的通道上。本轮**不改**（改它要动整条 HTML 通道的段落样式），\
  但把 406 的优先级按实抬起来，并留一条：下一次动这条通道之前，先问这一处值不值得顺手做。
""" % (UA, UB, B_CENSUS, UC, UD, D1, UE, MISSING_STATE, B_STATE, UF, AUDIT_N - 1,
       LAG_BEFORE, UG, CAUGHT,
       UH, (re.findall(u"最暗 (\\d+)", INK_DARK_ROW) or [u"?"])[0],
       (re.findall(u"底=\\s*(\\d+)", INK_DARK_ROW) or [u"?"])[0], RATIO_DARK_ROW,
       RATIO_LIGHT_ROW, RATIO_DETAIL, B_INK, UI2,
       INK_BLOCK_D.strip(), INK_BLOCK_L.strip(), RATIO_DETAIL,
       UJ, ROUND - 1)

# ── ITERATION ────────────────────────────────────────────────────────────────
ITER_TITLE = (u"## Round %d · R%d（第 %d 轮 · %s）：全历史回顾 —— 三本账第一次被按全长度扫，"
              u"而看图这条腿量到自己会美化（产品 %d 文件）\n" % (ITER_N, ROUND, AUDIT_N, DATE, PRODUCT_N))

ITER_BODY = u"""
这一轮不做新东西，做的是"回头看"。用户那句话是这么说的：做完了也要回过头去完整地、慢慢地\
回顾一遍自己这么长时间以来的工作和无数个提交。于是本轮的靶不是某个缺陷，而是**这套账本身**：\
把三本大账按全长度扫一遍（不是按窗口），把提交标题里的声明拿回来对账，把报告接上它停住的那一段。

先说不是好消息的那半：**这一轮没有重捕帧。** 产品 0 文件，四件套里只有基线那一腿能跑，\
而且是拿上一轮的 182 张去对 —— 现读 `FRAME_BASELINE_COMPARED=%s CHANGED=%s MISSING=%s ADDED=%s`。\
这一格只该读成"这一轮没有移动任何像素"，不该读成"这一轮看过图了"。看图那条腿本轮确实看了\
（复用上轮的帧逐张看），但它看的方式变了：看之前我以为自己在看"画面"，看之后我用像素尺重读了一遍\
同一张 PNG，两个读数差着一个数量级（下面那段）。

回顾尺（`review_full_history.py`）扫出来的东西里，只有四类是真的，其余五百来处是尺自己的病：\
`REVIEW_U_RANGE 发现=0`、`REVIEW_D_REF 发现=0`（333 处引用全部落地）、\
`REVIEW_BL_REF 发现=0`（改完条目形状之后）、`REVIEW_SEVEN_AFTER 发现=0`（Round 92 起 204 节的七维表）、\
`REVIEW_PAIR 发现=0`（轮次↔Round 映射）、`REVIEW_COMMIT_CLAIMS 内部不一致=2`（就是 405 那一单）。\
真的那四类是：① 四条 `BACKLOG 16x` 悬空引用（成因是条目行缺点号后那个空格）；\
② STATE 有 %s 轮没有自己的节；③ 报告的叙述节停在 R298、落后 %s 轮；④ 报告里现在有两格同名标签。\
每一条都从"没人看过"变成了"有一格会红的门看着"，而门都配了正对照。

然后是本轮最贵的一条，关于**我自己这条看图腿**：暗档主列表那几行文字，我看的时候是"可读的灰字"，\
像素尺读出来是 最暗 0 / 底 28 ⇒ 比 %s:1（亮档同一块盒子 %s:1，同一张暗帧的详情区标题 %s:1）。\
预览通道会做增强 —— 它能把 1.2:1 画成能读的样子。所以"我看过了"这句话从今天起要拆成两半：\
**我看到了什么**（可能被美化）与**尺读到了什么**（不会被美化）。这一格不改产品，因为它同时暴露了\
两种相反的解释：注入的 appearance 没进左列（通道），或者产品真的黑字（缺陷）。\
本轮没有拿任何一种解释结案，而是把区分它们的那一格写进 BACKLOG %d。

同一张帧里还有一件旧事：BACKLOG 229（R206 那次"给回执补帧，选中行整块纯黑"）在**已提交的夹具**上\
重现了，而且两档都黑（块底=0）。本轮答掉了"是谁"：它是 `selectOnly` 选中的那一条，\
因为详情区把同一条记录画得清清楚楚 ⇒ 不是没内容，是内容没画出来。"为什么黑"仍欠，挂在原条目上，\
不另开同号（373 那一族欠的是同一只眼）。

下半场是台账与报告：§14 补上 R299→R336 这一段（数字全部由 `report_section14.py` 现读），\
STATE 轮换，报告的 U/D 两格抬到最新，§13 那格 census 显式冻结成历史。

七维度自评：

| 维度 | 分/满分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | %d/15 | 逐张看了已提交的帧，并第一次给看图这条腿本身配了一把两向像素尺（%s:1 对 %s:1）；但本轮没重捕帧，基线只证"没移动像素" |
| 判据有效性 | %d/15 | 三格新守卫（悬空引用 / STATE 缺节 / 报告落后）各配正对照，四把刀全 CAUGHT；但 408 那一格只做了书面标记，没做成门 |
| 假绿防御 | %d/15 | 本轮整本就是防假绿：全长度扫描、单一权威（导入 ITEM）、"0 处什么也不说明"、预览通道会美化这件事被量出来而不是被相信 |
| 产品面推进 | %d/15 | 产品 0 文件，连读 %s 轮；量到的两个像素问题（%d、%d）都没在本轮修，因为它们的成因还没被分辨出来 |
| 台账一致性 | %d/15 | 七本 + 报告两格 + §14 补写 + 四条条目形状改规范；census 标签现在有两格，本轮按内容定位并显式冻结旧格 |
| 交付诚实性 | %d/15 | 报告第三次停在几十轮之前这件事，写进了报告自己那一节；回顾尺第一版五百处假警报按实登记；没拿"通道"或"产品"任一种解释结案 |
| 可复核性 | %d/15 | 全部读数出自仓库里的尺（review_full_history / row_ink_probe / test_ledger_citations / report_section14），命令写在台账与 STATE |
""" % (BASE[0], BASE[1], BASE[2], BASE[3], MISSING_STATE,
       LAG_BEFORE,
       RATIO_DARK_ROW, RATIO_LIGHT_ROW, RATIO_DETAIL, B_INK,
       SEVEN[0], RATIO_DARK_ROW, RATIO_LIGHT_ROW,
       SEVEN[1], SEVEN[2], SEVEN[3], STREAK_N, B_INK, B_CENSUS,
       SEVEN[4], SEVEN[5], SEVEN[6])

# ── DECISIONS ────────────────────────────────────────────────────────────────
DEC_BODY = u"""### D-%d（%d）回顾要有两种仪器：窗口守卫 + 一次性全长度尺；而扫描用的正则只许有一份权威

带回看窗口的守卫是对的（每轮全量重扫三本大账太慢），但它的副作用是**窗口之外从来没人看过**：\
本轮把三本账按全长度扫一遍，量出 STATE 有 %s 轮没有自己的节、四条 `BACKLOG 16x` 引用查无条目、\
报告的叙述节停在 R298 而账已经写到第 %d 轮。三条都不是新坏的，是**从来没被看过**。

两条规矩：

① **窗口守卫与一次性全长度尺要配对**。一次性仪器用完就撤（它不进电池，跑太慢），\
但它照出来的每一个洞必须当场变成两样东西：一格按窗口判的会红的门（守住"从现在起不再漂"），\
和一条写清楚"历史那半为什么不补"的工单（BACKLOG %d 就是这个形状：不补写历史正文，因为补=伪造记录）。

② **扫描用的正则必须导入被审系统自己那颗，不许另抄**。`test_ledger_citations.py` 里写的是\
`from test_ledger_ids import ITEM`。这不是风格：那四条悬空引用的成因就是"同一件事有两处各判一遍"\
—— 一处认条目、一处不认。另抄一颗正则 = 第二个权威，而两个权威之间的漂移只会在没人看的时候发生。\
这一条自己配了一刀（M992：把 import 换成本地只认四位的尺 ⇒ 引用格与"同一颗尺"那格一起红）。

登记：三格新守卫由 M989/M990/M991 三把刀钉住（三格各一把"恒返回空"），\
②这一半由 M992 钉住；正对照本身不是免检牌 —— 每一格都要求"把检查改成恒空 ⇒ 正对照必须点名"。
""" % (D1, ROUND, MISSING_STATE, AUDIT_N, B_STATE)

# ── BACKLOG ──────────────────────────────────────────────────────────────────
BL_407 = u"""**%d. `AGENT_STATE.md` 有 %s 轮没有自己的节（R257、R277、R278、R282…R288）：\
要不要用「由 git 派生、显式标注」的方式把那几轮的靶补出来？**（R%d）
STATE 是三本账里唯一没有守卫的那本（Skill 里就写着这句），而它恰好住着"下一轮的靶是什么"。\
本轮新加的窗口门只守最近 40 轮（`STATE_WINDOW=40`），**历史那 %s 轮按实留着**，理由写进决定台账 D-%d ①：\
不补写历史正文 —— 事后补出来的"当时在想什么"是伪造记录，比空着更坏。
这一单问的是另一条路：那几轮的 commit message 与台账标题是真存在过的，\
可以**派生**出一节并**在标题里明写"由 git 派生、非当时所写"**（本轮 §14 与 `product_streak.py` 用的就是这个形状）。\
要不要走、值不值得占一格守卫，等这一族再坏一次再定；在此之前它是一格有名字的缺席。
""" % (B_STATE, MISSING_STATE, ROUND, MISSING_STATE, D1)

BL_408 = u"""**%d. 报告里现在有两格同名标签「判据与门的规模」（§13 历史 / §14 现读）：\
"最新那一格住在哪一节"仍靠约定，没做成会红的门**（R%d）
R336 的生成器预检写着"这一格必须恰好一处"，本轮它变成两处，那支预检会当场 die。\
本轮做的两件事都是**书面**的：① 定位改成按内容而不是按标签；② §13 那格冻结成历史并写明接手关系。\
没做的那件是门：报告里可以再加第三格、第四格同名标签，而"哪一格是最新的"仍然只写在正文里。\
要修的形状大概是：每格 census 自带轮次徽章，守卫判"带徽章的最新那一格必须与仪器同数" ——\
这与 U-264 那一族（报告格子停在旧数）是同一个病的另一半。
""" % (B_CENSUS, ROUND)

BL_409 = u"""**%d. 暗档主列表的行文字在帧里比底还暗（最暗 0 / 底 28 ⇒ %s:1），\
而同一张帧的详情区标题是 %s:1：先分辨"通道按 aqua 取色"还是"产品真黑字"，再谈修**（R%d 看图腿现读）
两种解释的修法相反，不许混着试。指向**通道**的证据：亮档同一块盒子 %s:1 完全正常，\
而捕获夹具的文档串里写着第 3 条规矩 —— 拍暗色时若只注入 `colorScheme`，\
`List` 这类 AppKit 承载控件仍按 aqua 取色，会拍出"深底黑字"的**假不可读帧**；\
本轮读到的形状与那句话一字不差（文字黑、底按真实窗口底色铺成 28）。指向**产品**的证据：今天没有。\
要补的那一格是**参照臂**：同一段文字用两条路径各画一次（SwiftUI `Text` 直接进探针框 vs 走 `List` 行），\
两臂的墨向必须一致才算"通道没问题"；不一致 ⇒ 是捕获通道的洞，且暗档所有左列读数都要重读一遍。\
真机眼能一次判完，但它要用户退出 App（本轮用户已授权，可下一次不一定）。
**这一格同时给看图腿记了一条**：预览通道会做增强，1.2:1 的黑字在眼里是"可读的灰字" ⇒\
"我看过了"不能替像素尺作证（U-%d）。
""" % (B_INK, RATIO_DARK_ROW, RATIO_DETAIL, ROUND, RATIO_LIGHT_ROW, UH)

BL_CLOSE_229 = u"""

**R%d 追记（这一族在已提交的夹具上重现，而且两档都黑）**：`row_ink_probe.py` 现读\
`%s`、`%s` —— 块底两档都是 0，块内亮墨 ≤20 颗。"是谁"这一半今天答了：\
它是 `selectOnly` 选中的那一条（`ghp_…`，40 个字符），因为同一张帧的详情区把同一条记录\
画得清清楚楚（%s:1）⇒ **不是没有内容，是内容没画出来**。"为什么黑"仍欠，且与 373 欠的是同一只眼；\
本轮不结案、不另开同号（见 U-%d）。
""" % (ROUND, INK_BLOCK_D.strip(), INK_BLOCK_L.strip(), RATIO_DETAIL, UI2)

BL_CLOSE_406 = u"""

**R%d 追记（看图腿量到：那一处紧挨的主语就是 alt 那句）**：夹具里 `<ul>` 之后紧跟的就是那张带 alt 的图（`UICaptureHarness.swift` 的 HTML 夹具），所以"紧挨 2 处"里的第 ② 处\
读的是「乙项 → 季度趋势图（图片未加载）」这一对（20.0pt，而两个 `<p>` 之间是 31.5pt）。\
也就是说 R%d 规则 ④ 兑现了"自成一段"，但**块边界仍然读不出来**：那句话在屏幕上贴的是上面那个列表。\
本轮不改（改它要动整条 HTML 通道的段落样式），但把优先级记实：它落在刚上线的通道上，\
不是落在无关文字上（见 U-%d；"形容词不许进台账"那条老规矩在这一处同样成立——\
本轮没有把"看着挤"写成结论，而是回夹具对源码确认了主语）。
""" % (ROUND, ROUND - 1, UJ)

# ── CHANGELOG ────────────────────────────────────────────────────────────────
CHG_ENTRY = u"""### 三本账第一次被按全长度扫了一遍；看图这条腿量到自己会美化（R%d / U-%d…U-%d · 产品 %d 文件，回顾轮）

- 新增电池守卫 `scripts/tests/test_ledger_citations.py` 三格：`BACKLOG` 引用必须落到 `ITEM` 认得的条目、
  最近 %s 轮 STATE 必须每轮一节、报告叙述节落后不得超过 20 轮。三格各配内存正对照，刀 M989…M992 四把
  现读 `%s`。
- 四处条目行形状改到规范（`**166.（` → `**166. （`）：那四条引用不是写错，是**尺看不见它们**。
- 报告补 §14（R299→R336，数字全部由 `report_section14.py` 现读）；§13 那格 census 显式冻结成历史。
- 新开 %d（STATE 的十轮历史空洞）、%d（报告两格同名 census 标签）、%d（暗档左列文字 %s:1，
  通道还是产品未分辨）；229 与 %d 各一条追记（选中行两档都黑 / 那处紧挨的主语是 alt 那句）。
- 产品 0 文件：本轮没有重捕帧，基线 `COMPARED=%s CHANGED=%s` 只证"没移动像素"，不证"看过图"。
""" % (ROUND, UA, UMAX, PRODUCT_N, u"40", CAUGHT, B_STATE, B_CENSUS, B_INK,
       RATIO_DARK_ROW, B_PARA, BASE[0], BASE[1])

# ── 预检：所有锚点在任何写盘之前统一验一遍 ─────────────────────────────────
for name, txt, anc in ((u"UI 顶节", aud, UI_ANCHOR), (u"报告 §14 标题", fr_pre, S14_TITLE)):
    if txt.count(anc) != 1:
        die(u"预检：" + name + u" 命中 %d 次" % txt.count(anc))
for pat, what in ((u"U-31 … U-(\\d+)", u"U 区间那一格"),
                  (u"(决定台账[^\\n]*?D-\\d{3} … \\*\\*)(D-\\d{3})", u"决定台账那一格的区间"),
                  (u"(?m)^- \\*\\*仍开（截至本轮，完整名单以 `AGENT_STATE.md` 的 R\\d+ 节", u"§13 的「仍开」")):
    if len(re.findall(pat, fr_pre)) != 1:
        die(u"报告里 " + what + u" 不是恰好一处，先修锚点再谈写盘")

wr(AUD, aud[:aud.index(UI_ANCHOR)] + UI_TITLE + u"\n" + UI_BODY.rstrip(u"\n") + u"\n\n" + UI_ANCHOR
   + aud[aud.index(UI_ANCHOR) + len(UI_ANCHOR):])
wr(ITE, rd(ITE).rstrip(u"\n") + u"\n\n" + ITER_TITLE + ITER_BODY.rstrip(u"\n") + u"\n")
wr(DEC, rd(DEC).rstrip(u"\n") + u"\n\n" + DEC_BODY.rstrip(u"\n") + u"\n")

blg = rd(BLG)
for bid, body in ((B_PARA, BL_CLOSE_406), (B_HOLE, BL_CLOSE_229)):
    m = re.search(u"(?m)^\\*\\*%d\\. .*?(?=^\\*\\*\\d{3}\\. |\\Z)" % bid, blg, re.S)
    if not m:
        die(u"BACKLOG %d 在追加过程中找不到了" % bid)
    blg = blg[:m.end()].rstrip(u"\n") + body.rstrip(u"\n") + u"\n" + blg[m.end():].lstrip(u"\n")
blg = blg.rstrip(u"\n") + u"\n\n" + BL_407.rstrip(u"\n") + u"\n"
blg = blg.rstrip(u"\n") + u"\n\n" + BL_408.rstrip(u"\n") + u"\n"
blg = blg.rstrip(u"\n") + u"\n\n" + BL_409.rstrip(u"\n") + u"\n"
wr(BLG, blg.rstrip(u"\n") + u"\n")

wr(CHG, u"".join(chg_lines[:H3_AT[0] + 1]) + u"\n" + CHG_ENTRY.rstrip(u"\n") + u"\n\n"
   + u"".join(chg_lines[H3_AT[0] + 1:]))

# ── 写盘之后再算最大号（数字从盘上解析，不手填） ──────────────────────────
aud_after = rd(AUD)
U_MAX_NOW = max(int(x) for x in re.findall(u"(?m)^- \\*\\*U-(\\d{3,4})[：(]", aud_after))
D_MAX_NOW = max(int(x) for x in re.findall(u"(?m)^### D-(\\d{3})", rd(DEC)))
B_MAX_NOW = max(int(x) for x in re.findall(u"(?m)^\\*\\*(\\d{2,4})\\. ", rd(BLG)))
if (U_MAX_NOW, D_MAX_NOW, B_MAX_NOW) != (UMAX, D1, B_INK):
    die(u"落盘后的最大号与本轮计划不一致：U=%d D=%d B=%d（要 %d/%d/%d）"
        % (U_MAX_NOW, D_MAX_NOW, B_MAX_NOW, UMAX, D1, B_INK))
print(u"R337_IDS U=%d D=%d B=%d 条目=%d" % (U_MAX_NOW, D_MAX_NOW, B_MAX_NOW,
      len(re.findall(u"(?m)^- \\*\\*U-(\\d{3,4})[：(]", aud_after))))

# ── STATE 轮换 ───────────────────────────────────────────────────────────────
# 曲线那一格必须取**本轮 ITERATION 落盘之后**的那一份：ITERATION 已经写了 Round %d，
# 而 现读 段里那份是写盘之前跑的 ⇒ 用它会把"少一轮"的数登记成现状。
cvc0, cvc0_rc = sh([sys.executable, CURVE])
if cvc0_rc != 0 or u"GAPS=none" not in cvc0:
    die(u"STATE 写之前曲线尺不干净：" + cvc0.strip()[-200:])
PHASE2 = line_with(cvc0, u"PHASE2 n=", u"曲线（ITERATION 落盘之后）")
REVIEW_CLAIMS = REVIEW_CLAIMS.replace(u"REVIEW_COMMIT_CLAIMS ", u"", 1)
STATE_BODY = u"""## R%d 状态（%s · 本地 · 第 %d 轮 / Round %d）：把三本账按全长度扫一遍，顺手量到看图这条腿自己会美化（产品 %d 文件，回顾轮）

最后更新：%s（本地 · R%d / 第 %d 轮 / Round %d）：全历史回顾 —— 三格新守卫进电池（悬空引用 / STATE 缺节 / 报告落后）\
+ 四把刀 + 报告补 §14 + 四条条目形状改规范（产品 %d 文件，判据账）

本轮做了什么：不做新东西，回头把这套账本身当被审对象。
① `review_full_history.py` 把三本大账按**全长度**扫了一遍（守卫都带回看窗口，窗口之外从来没没人看过）；
   第一版报五百来处，五种口径病修完只剩四类真 finding：四条 `BACKLOG 16x` 悬空、STATE 缺 %s 轮、
   报告叙述节停在 R298（落后 %s）、报告里两格同名 census 标签。
② 那四类各拿到一格会红的门或一条工单：新守卫 `scripts/tests/test_ledger_citations.py`（三格、三把正对照、
   共享 `ITEM` 不另抄），历史空洞进 BACKLOG %d，两格标签进 %d。
③ 报告补 §14（R299→R336，数字全部现读），§13 那格 census **显式冻结成历史**。
④ 看图腿本轮第一次量到自己：暗档主列表行文字 最暗 0 / 底 28 ⇒ 比 %s:1，
   亮档同一盒子 %s:1，同一张暗帧详情头 %s:1 —— 预览通道会增强，把 1.2:1 画成"可读的灰字"。
   两种解释（appearance 没进左列 / 产品真黑字）没被分辨 ⇒ BACKLOG %d 写清了那格参照臂怎么造。
   同一张帧里 229 那个"选中行整块纯黑"在已提交夹具上重现（两档都黑），"是谁"答了、"为什么黑"仍欠。

验证读数（现读）：脚本电池 `Ran %s（skipped=%s）`；针预检 `tables=%s covered=%s arms=%s bad=%s`、
臂名册 `files=%s arms=%s dupes=0`；变异表 `mutate_r337 %s, RESTORE_CLEAN=%s`（%s）；
清账表 `%s`；产品面连续零改动 **%s** 轮（现读 `scripts/product_streak.py` 的 streak —— 这一整句必须在同一行里：`_cells` 问的是"那一格有没有引用取数口"，分两行写就等于没引用）；
帧基线（复用上轮 182 张，零产品改动）`COMPARED=%s CHANGED=%s MISSING=%s ADDED=%s`；
连读取数口两份都现读：`--streak-for %d` → streak=%s（**台账「第 N 轮」口径，电池里那格守卫读的就是它**）、
`--streak-for %d` → streak=%s（R 号口径，差一 ⇒ 拿它填格会与守卫漂开，见本轮自伤）；
回顾尺 `REVIEW_U_RANGE 发现=0`、`REVIEW_D_REF 发现=0`、
`REVIEW_BL_REF 发现=0`、`REVIEW_SEVEN_AFTER 发现=0`、`REVIEW_PAIR 发现=0`、
`REVIEW_COMMIT_CLAIMS %s`；曲线 `GAPS=none`、`%s`。
§8 搬运：本轮**没有新读数族进判据卷**（三格新守卫在 python 侧、`row_ink_probe.py` 是 `.scratch` 里的一次性仪器，
两者都不进 §8 的搬运名单），而本轮没跑判据卷 ⇒ §8 那一格按实记 **NOT-RUN**（没有本轮日志可解析，
不写"沿用上一遍"）。

NOT-RUN（三种缺席分开写，不许省略）：① **本轮没跑的产品验证腿**：构建告警、Swift 判据卷、全量卷、
重捕帧、换装本机 —— 产品 0 文件、`Sources` 与 Swift 测试一字未动，跑它们不会新增证据；
基线那一腿只复用上轮的帧对账（`CHANGED=%s` 的含义是"没移动像素"，不是"看过图"）。
② **只在人身上判得了**：暗档左列那 %s:1 到底是通道还是产品 —— 要真机眼，
或者 409 里写的那条两臂参照判据（本轮没造，所以两种解释都没结案）。
③ **这条通道看不见**的：STATE 那 %s 轮历史空洞按实留着（窗口门只守最近 40 轮），
补写等于伪造记录。

下一轮（R%d）的靶：⓪ 读 CI 配对（成对：run id ↔ commit，现读自 `scripts/ci_read.py latest`）——
**R%d 追记现读**：本笔 push 之后按 sha 逐笔问，别只读 tip 那一跑。
这一跑要答的：⓪a 新守卫 `test_ledger_citations.py` 三格在 runner 上签不签（它读的是台账本身，
两机同仓同内容 ⇒ 该同数；不同 ⇒ 说明有一台在跑旧工作树）；⓪b 电池例数两机对账（本机现读 %s）。
→ ① **回到产品面**：`altAttr` 用的是 `\\balt`，而 ICU 的词边界把 `data-alt` 里那个 `alt` 也算起点 ⇒
`<img data-alt="埋点说明" alt="真说明">` 取到的是**埋点那个属性**的文字 ——
屏幕上出现作者没打算给人读的一句话，与 401 那条规矩方向相反（R%d 复盘时读到源码，Python 的 `re` 只是我本机的猜测，
**不算读数**）。第一件事：用产品入口量出它（一条打印 `HTML_ALT_SOURCE` 的判据），量到了再把 `\\b` 换成
`(?:\\A|\\s)`，并给"属性名前缀不许冒充属性名"这一族配刀。
→ ② 顺手把 405（标题里那半句产品数）立成定义并变成门：回顾尺现读 `%s`，它比动效那一串便宜得多。
→ ③ 动效主线仍排队：399 / 390 的 before/after / 389 的时长 / 384 的横轴 / 387① / 376 / 367；
400 要先造笔画墨量尺；409 的参照臂可以插在 ① 之后做（同一批像素尺工作）。

本轮的自伤（写成出处，不写成缺陷）：回顾尺第一版报五百来处"问题"，五种口径病全是我自己写的
（字符串集合 vs 整数集合、`re.split` 索引、合计行、CHANGELOG 子标题、拿只认 3〜4 位的尺判 1〜2 位的老条目）。
**它的 500 处与它的 0 处同样不说明任何事** —— 配完正对照之后那个数才有资格进台账（U-%d）。
另一处自伤是**取数口的口径**：`--streak-for %d`（R 号）给 %s，而 `--streak-for %d`（台账「第 N 轮」口径）给 %s ——
电池里那格守卫读的是**后者**，我第一版按 R 号填了报告与 STATE 两格，落盘之后当场红两朵
（`test_product_streak_cell`）。规矩：**台账那一格写的必须是守卫自己派生那份数，不是我以为的口径**；
两份都现读、并在同一行里写清哪一份作数，下一次换口径的人就看得见差一从哪来。
""" % (ROUND, DATE, AUDIT_N, ITER_N, PRODUCT_N, DATE, ROUND, AUDIT_N, ITER_N, PRODUCT_N,
       MISSING_STATE, LAG_BEFORE,
       B_STATE, B_CENSUS, RATIO_DARK_ROW, RATIO_LIGHT_ROW, RATIO_DETAIL, B_INK,
       BATT, BATT_SKIP, PRE[0], PRE[1], PRE[2], PRE[3], ARM_TOTAL[0], ARM_TOTAL[1],
       CAUGHT, RESTORE, u"、".join(ARMS_NEW), GATE_LINE, STREAK_N,
       BASE[0], BASE[1], BASE[2], BASE[3], AUDIT_N, STREAK_N, ROUND, STREAK_R,
       REVIEW_CLAIMS.replace(u"ROUND_CLAIM_REVIEW ", u""),
       PHASE2, BASE[1], RATIO_DARK_ROW, MISSING_STATE, ROUND + 1, ROUND, BATT,
       ROUND, REVIEW_CLAIMS.replace(u"ROUND_CLAIM_REVIEW ", u""), UA,
       ROUND, STREAK_R, AUDIT_N, STREAK_N)

sta2 = rd(STA)
pos = sta2.index(line_with(sta2, u"## R%d 状态" % (ROUND - 1), u"STATE 上一轮节标题"))
wr(STA, sta2[:pos] + STATE_BODY.rstrip(u"\n") + u"\n\n" + sta2[pos:])
after = rd(STA)
if after.count(u"\n> ## ") != before_layers:
    die(u"STATE 轮换改动了 `> ##` 层数：%d → %d" % (before_layers, after.count(u"\n> ## ")))
if (u"## R%d 状态" % (ROUND - 1)) not in after:
    die(u"STATE 轮换把上一轮的节标题弄丢了")

# ── FINAL_REPORT：计数器两格 + §14 census + §13 冻结 + 「仍开」轮次 ─────────
fr = rd(FRA)
mUD = re.search(u"U-31 … U-(\\d+)", fr)
fr = once(fr, mUD.group(0), u"U-31 … U-%d" % U_MAX_NOW)
m = re.search(u"(决定台账[^\\n]*?D-\\d{3} … \\*\\*)(D-\\d{3})", fr)
fr = fr[:m.start(2)] + (u"D-%d" % D_MAX_NOW) + fr[m.end(2):]
fr = once(fr, S14_TITLE, S14_TITLE.replace(u"R%d 补写" % (ROUND - 1), u"R%d 补写" % ROUND))
fr = once(fr, u"写它的那一轮是 R%d。" % (ROUND - 1),
          u"写它的那一轮是 R%d；这一节覆盖的区间仍停在 R%d（R%d 自己的账由下一节接手）。"
          % (ROUND, ROUND - 1, ROUND))
new_s14 = (u"- **判据与门的规模**（R%d 现读，这一格是最新的权威，§13 那格已冻结成历史）："
           u"脚本电池 `Ran %s`（skipped=%s）；变异臂在册 **%s** 把 / 扫了 **%s** 个表文件"
           u"（预检 tables=%s covered=%s arms=%s bad=%s —— 这四个数各是各的分母）；"
           u"U 定义行最大 **U-%d**、决定最大 **D-%d**、BACKLOG 最大 **%d**"
           u"（本轮新开 %d / %d / %d 三单，两条旧条目各收到一条追记：%d、%d）；"
           u"本轮刀 `mutate_r337.py CAUGHT=%s, RESTORE_CLEAN=%s`（%s）。"
           % (ROUND, BATT, BATT_SKIP, ARM_TOTAL[1], ARM_TOTAL[0],
              PRE[0], PRE[1], PRE[2], PRE[3], U_MAX_NOW, D_MAX_NOW, B_MAX_NOW,
              B_STATE, B_CENSUS, B_INK, B_HOLE, B_PARA, CAUGHT, RESTORE,
              u"、".join(ARMS_NEW)))
fr = once(fr, S14_AT, new_s14)
new_s13 = S13_AT.replace(u"（写盘前同数）",
                         u"（R%d 写盘前同数；**这一格从今天起冻结成历史** —— 报告里出现了第二格同名标签，"
                         u"同一个数不许有两处权威，最新那格在 §14，见 BACKLOG %d）" % (ROUND - 1, B_CENSUS))
if new_s13 == S13_AT:
    die(u"§13 那格里没找到「（写盘前同数）」⇒ 冻结标记无处可挂，先读那一格再写")
fr = once(fr, S13_AT, new_s13)

# §13 的「产品面」那一格是**活格**（连读门读的就是它）：本轮产品 0 文件，
# R336 那一段的产品叙述已经由 §14 接手（那里写着 R299…R336 有 %d 轮动了产品）。
prod_hits = [ln for ln in re.findall(u"(?m)^- \\*\\*产品面（这一节最该被读的部分）\\*\\*：.*$", fr)
             if u"产品面连续零改动轮数" in ln]
if len(prod_hits) != 1:
    die(u"报告里带连读那一格的「产品面」行应为恰好一处，实得 %d 处 ⇒ 又一处权威，先对账"
        % len(prod_hits))
new_prod = (u"- **产品面（这一节最该被读的部分）**：本轮产品文件 **%d** 个（**回顾轮**："
            u"三本账按全长度扫一遍、三格新守卫进电池、四把刀、报告补 §14）。"
            u"量到两个像素问题但**都没有修**，因为成因还没被分辨："
            u"暗档主列表行文字 最暗 0 / 底 28 ⇒ 比 %s:1（亮档同一盒子 %s:1、同一张暗帧详情头 %s:1，"
            u"`row_ink_probe.py` 现读）⇒ BACKLOG %d；"
            u"BACKLOG 229 那个「选中行整块纯黑」在已提交夹具上重现且两档都黑（块底=0）⇒ 追记挂在原条目上。"
            u"产品面连续零改动轮数 = **%s**（现读 `python3 scripts/product_streak.py`）。"
            u"本轮新开 %d / %d / %d 三单，两条旧条目各收到一条追记（%d、%d）。"
            % (PRODUCT_N, RATIO_DARK_ROW, RATIO_LIGHT_ROW, RATIO_DETAIL, B_INK,
               STREAK_N, B_STATE, B_CENSUS, B_INK, B_HOLE, B_PARA))
fr = once(fr, prod_hits[0], new_prod)
fr = re.sub(u"(?m)^(- \\*\\*仍开（截至本轮，完整名单以 `AGENT_STATE.md` 的 R)\\d+( 节)",
            u"\\g<1>%d\\g<2>" % ROUND, fr, count=1)
if re.search(u"@\\w+@", fr):
    die(u"报告里还有没替换的占位符")
wr(FRA, fr)

sc, src_rc = sh([sys.executable, SRCCELL, u"--write"])
if src_rc != 0:
    die(u"报告里 Sources 那一格刷新失败：" + sc.strip()[-300:])

# ── 写盘之后：§1 刷新 → 电池 → 连读门 → 曲线 → 七维表对账 → §8 名单 ──────────
rf0, rfc0 = sh([sys.executable, FRESH])
if rfc0 != 0 or u"REFUSED" in rf0:
    die(u"报告 §1 的刷新器没签：%s" % rf0.strip()[-300:])

ite_after = rd(ITE)
rows = re.findall(u"(?m)^\\| ([^|]+) \\| (\\d+)/(\\d+) \\|", ite_after.split(ITER_TITLE[:20])[-1])
if len(rows) != 7:
    die(u"本轮七维表读到 %d 行（要 7 行）⇒ 曲线仪器不会给数" % len(rows))
if any(mx != u"15" for _, _, mx in rows):
    die(u"七维表里出现了非 /15 的量纲：%s" % [r[2] for r in rows])
if [int(v) for _, v, _ in rows] != SEVEN:
    die(u"七维表与 SEVEN 不一致：%s vs %s" % ([int(v) for _, v, _ in rows], SEVEN))
print(u"R337_SEVEN 合计=%d/%d 行=%d" % (sum(SEVEN), SEVEN_MAX, len(rows)))

bt2, brc2 = sh([sys.executable, u"-m", u"unittest", u"discover", u"-s", u"scripts/tests"])
BATT2 = (re.findall(u"Ran (\\d+) tests", bt2) or [u"?"])[-1]
POST_RED = sorted(set(re.findall(u"(?m)^(?:FAIL|ERROR): (\\w+)", bt2)))
if brc2 != 0:
    die(u"落盘之后脚本电池仍是红的（Ran=%s，红=%s）⇒ 台账里那一格必须自己消失：%s"
        % (BATT2, POST_RED, bt2.strip()[-1200:]))
if BATT2 != BATT:
    die(u"落盘前后电池例数不同：%s → %s ⇒ 台账里那一格是假的" % (BATT, BATT2))

ck, ckc = sh([sys.executable, STREAK, u"--check"])
if ckc != 0:
    die(u"连读门不认这版台账：" + ck.strip()[-500:])
cvc, cvc_rc = sh([sys.executable, CURVE])
if cvc_rc != 0 or u"GAPS=none" not in cvc:
    die(u"落盘之后曲线尺不干净：" + cvc.strip()[-300:])
scores = dict((int(k), int(v)) for k, v in
              re.findall(r"(\d+)=(\d+)", (re.findall(r"(?m)^SCORES_BY_ROUND .*$", cvc) or [u""])[-1]))
DERIVED = scores.get(ITER_N, u"没解析到")

rl, rlc = 0, 0

print(u"R337_LEDGERS_OK 七本=%d 电池=%s 连读=%s 派生分=%s 刀=%s 臂=%s/%s U=%d D=%d B=%d 基线=%s/%s"
      % (len(WRITTEN), BATT2, STREAK_N, DERIVED, CAUGHT, ARM_TOTAL[1], ARM_TOTAL[0],
         U_MAX_NOW, D_MAX_NOW, B_MAX_NOW, BASE[0], BASE[1]))
