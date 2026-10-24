#!/usr/bin/env python3
# -*- coding: utf-8 -*-
u"""R338 的台账生成器（第 337 轮 / Round 335 · data-alt 抢走 alt · 产品 1 文件）。

R337 复盘时从源码读出这条形状，今天用**产品入口**量成读数再修：
`altAttr` 用 `\\balt\\s*=`，ICU 的词边界把 `data-alt` 里那个 `alt` 也算起点 ⇒
屏幕上留下的是埋点属性那句话。改前/改后各拍一遍同一份夹具（两份构建），
渲染态 alt 那一行的像素差是本轮的产物证人。

数字全部从当场跑完的日志里解析；所有锚点在任何写盘之前统一验一遍。

  /tmp/r338_html.log            —— HTML_ALT_SOURCE 那一行 + 判据卷 Executed
  /tmp/r338c_rv/ROUND_VERIFY.log —— build 告警 / 全量卷 / 帧 / 基线 / dmg / 换装
  /tmp/r338_capture.log         —— CAPTURED 那一行
  /tmp/r338_pixdiff.log         —— 改前/改后同一夹具两档渲染帧的像素差
  /tmp/r338_t_r338.log          —— 本轮三把刀
  /tmp/r338_pre.log / _curve.log / _gate.log / _streak.log / _py.log / _review.log

跑法：PYTHONUTF8=1 python3 .scratch/motion-audit-2/ledgers_r338.py
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

RV_DIR = u"/tmp/r338c_rv"
RV_LOG = RV_DIR + u"/ROUND_VERIFY.log"
HTML_LOG = u"/tmp/r338_html.log"
CAP_LOG = u"/tmp/r338_capture.log"
PIX_LOG = u"/tmp/r338_pixdiff.log"
FD_LOG = u"/tmp/r338_framesdiff.log"
TABLE_LOG = u"/tmp/r338_t_r338.log"
PRE_LOG = u"/tmp/r338_pre.log"
CURVE_LOG = u"/tmp/r338_curve.log"
GATE_LOG = u"/tmp/r338_gate.log"
STREAK_LOG = u"/tmp/r338_streak.log"
BATT_LOG = u"/tmp/r338_py.log"

ENV = dict(os.environ)
ENV[u"PYTHONUTF8"] = u"1"
ENV[u"PYTHONDONTWRITEBYTECODE"] = u"1"

ROUND = 338
AUDIT_N = 337
ITER_N = 335
DATE = u"2026-10-25"
PRODUCT_N = 1
UA, UB, UC, UD, UE, UF, UG = 1147, 1148, 1149, 1150, 1151, 1152, 1153
UMAX = UG
D1 = 334
B_TOKENIZER = 410      # 属性/标签解析没有真正的 tokenizer（404 与本轮同族的总账）
B_RUNNER = 411         # runner 上那朵没名字的悬停档红（R337 那一跑读到，至少六跑连续）
B_EMPH = 400           # 仍开
ARMS_NEW = (u"M993", u"M994", u"M995")
CI_LOG = u"/tmp/r338_ci.log"
SEVEN = [15, 14, 15, 13, 14, 14, 14]
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
    print(u"LEDGERS_R338_DIED " + msg)
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
        die(u"读数里缺 " + key + u"（" + where + u"）：" + text[:200])
    return m.group(1)


# ── 现读 ─────────────────────────────────────────────────────────────────────
html_log = require(HTML_LOG)
rv_log = require(RV_LOG)
cap_log = require(CAP_LOG)
pix_log = require(PIX_LOG)
fd_raw = require(FD_LOG)
fd_line = line_with(fd_raw, u"FRAME_DIFF 比了", u"逐张比")
FD = [num(fd_line, u"比了", u"逐张比"), num(fd_line, u"变了", u"逐张比")]
# 上一轮→本轮 的差集 bbox（与"改前构建 vs 改后构建"那一份**不是同一件事**，两份都要在）
FDB = {}
for tier in (u"dark", u"light"):
    ln = line_with(fd_raw, u"FRAME_DIFF_BBOX detail-html-rendered-720x520-%s" % tier, u"逐张比的 bbox")
    FDB[tier] = (num(ln, u"变了", u"bbox"),
                 (re.findall(r"bbox=\((-?\d+),(-?\d+)\)\.\.\((-?\d+),(-?\d+)\)", ln)
                  or [(u"",) * 4])[0])
if FDB[u"dark"][1][0] == u"":
    die(u"上一轮→本轮的差集 bbox 没解析到 ⇒ U-1150 那句只能记 NOT-RUN")
tbl = require(TABLE_LOG)
pre_log = require(PRE_LOG)
curve_log = require(CURVE_LOG)
gate_log = require(GATE_LOG)
batt_log = require(BATT_LOG)

SRC = line_with(html_log, u"HTML_ALT_SOURCE", u"判据卷")
SRC_FLAGS = re.findall(u"=([a-z]+)", SRC)
if len(SRC_FLAGS) != 5 or any(f != u"true" for f in SRC_FLAGS):
    die(u"HTML_ALT_SOURCE 不是五颗全 true（现读 " + SRC.strip() + u"）⇒ 修法没兑现，别写账")
ALT_CELLS = (re.findall(u"Executed (\\d+) tests, with (\\d+) failures", html_log) or [None])[-1]

BUILD_W = num(line_with(rv_log, u"build_warnings", u"ROUND_VERIFY"), u"build_warnings", u"告警")
if BUILD_W != u"0":
    die(u"构建有告警（" + BUILD_W + u"）⇒ 本轮不许落账")
SWIFT = [num(rv_log, u"swift_executed", u"全量卷"), num(rv_log, u"swift_skipped", u"全量卷"),
         num(rv_log, u"swift_failures", u"全量卷")]
if SWIFT[2] != u"0":
    die(u"全量卷有红：" + rv_log.strip()[-400:])
FRAMES = num(line_with(rv_log, u"frames=", u"ROUND_VERIFY"), u"frames", u"帧数")
DMG = (re.search(u"dmg=(\\w+)", rv_log) or [None, u""])[1]
if DMG != u"ok":
    die(u"dmg / 换装没签（dmg=" + DMG + u"）")
VER = num(rv_log, u"installed_version", u"换装")
BASE_LINE = line_with(rv_log, u"baseline_compared", u"帧基线")
BASE = [num(BASE_LINE, u"baseline_compared", u"基线"), num(BASE_LINE, u"baseline_changed", u"基线"),
        num(BASE_LINE, u"baseline_missing", u"基线")]

CAPTURED = (re.search(u"CAPTURED (\\d+)", line_with(cap_log, u"CAPTURED", u"捕获"))
                or [None, u""])[1]
if CAPTURED != FRAMES:
    die(u"两遍帧数不同：CAPTURED=%s 而 ROUND_VERIFY frames=%s" % (CAPTURED, FRAMES))

PIX = {}
for tier in (u"dark", u"light"):
    ln = line_with(pix_log, u"FRAME_DIFF_BBOX detail-html-rendered-720x520-%s" % tier,
                   u"像素差")
    PIX[tier] = (num(ln, u"变了", u"像素差"),
                 (re.findall(u"bbox=\\((-?\\d+),(-?\\d+)\\)\\.\\.\\((-?\\d+),(-?\\d+)\\)", ln)
                  or [(u"",) * 4])[0])

CAUGHT = num(line_with(tbl, u"CAUGHT=", u"变异表"), u"CAUGHT", u"变异表")
RESTORE = (re.search(u"RESTORE_CLEAN=(\\w+)", tbl) or [None, u""])[1]
if RESTORE != u"yes":
    die(u"变异表没还原干净（RESTORE_CLEAN=" + RESTORE + u"）")
if CAUGHT != u"3/3":
    die(u"本轮三把刀没全抓到（" + CAUGHT + u"）")

PRE_LINE = line_with(pre_log, u"NEEDLE_PRECHECK", u"针预检")
PRE = [num(PRE_LINE, u"tables", u"针预检"), num(PRE_LINE, u"covered", u"针预检"),
       num(PRE_LINE, u"arms", u"针预检"), num(PRE_LINE, u"bad", u"针预检")]
if PRE[3] != u"0":
    die(u"针预检 bad=" + PRE[3])
ARM_LINE = line_with(pre_log, u"ARM_TOTAL", u"臂名册")
ARM_TOTAL = [num(ARM_LINE, u"files", u"臂名册"), num(ARM_LINE, u"arms", u"臂名册")]
if u"dupes=0" not in ARM_LINE:
    die(u"臂名册撞号：" + ARM_LINE)
if u"mutate_r338" not in pre_log and u"registered=" not in pre_log:
    die(u"预检名册里似乎没有 mutate_r338 ⇒ 这支表对预检静默")

ci_log = require(CI_LOG)
CI_RUN = line_with(ci_log, u"RUN=", u"CI 配对")
CI_SHA = (re.search(u"sha=(\\w+)", CI_RUN) or [None, u""])[1]
CI_CONC = (re.search(u"conclusion=(\\w+)", CI_RUN) or [None, u""])[1]
CI_FAIL_TEST = line_with(ci_log, u"FAILING_TEST", u"CI 失败步骤").split()[-1]
CI_RUN_ID = num(CI_RUN, u"RUN", u"CI 配对")
_msgs = [ln.split(u" ", 1)[1] for ln in ci_log.splitlines() if ln.startswith(u"MSG")]
if len(_msgs) != 2:
    die(u"runner 那两朵红的正文没抄全（现读 %d 条）" % len(_msgs))
CI_MSG1, CI_MSG2 = _msgs
CI_PREV = line_with(ci_log, u"PREV_RUN", u"CI 归因对照")
if CI_CONC != u"failure":
    die(u"这一跑不是 failure，那一格按实改写：" + CI_RUN)
GATE_LINE = line_with(gate_log, u"MOTION_LEDGER ", u"清账表")
BATT = (re.findall(u"Ran (\\d+) tests", batt_log) or [None])[-1]
if BATT is None or u"FAILED" in batt_log:
    die(u"脚本电池不是绿的：" + batt_log.strip()[-300:])
BATT_SKIP = (re.findall(u"OK \\(skipped=(\\d+)\\)", batt_log) or [u"0"])[-1]
if u"GAPS=none" not in curve_log:
    die(u"曲线尺不干净：" + curve_log.strip()[-200:])

sk_a, sk_rc = sh([sys.executable, STREAK, u"--streak-for", str(AUDIT_N)])
if sk_rc != 0:
    die(u"--streak-for 跑不通：" + sk_a.strip()[-200:])
STREAK_N = num(line_with(sk_a, u"PRODUCT_STREAK_FOR", u"连读"), u"streak", u"连读")

CLAIMS_SHORT = (re.findall(u"扫了=[^\n]*", require(u"/tmp/r337_review.log")) or [u"没解析到"])[-1]
RUN_LINE = require(u"/tmp/r337_run.log")
RUN_ID = (re.findall(u"RUN=(\\d+)", RUN_LINE) or [None])[0]
RUN_SHA = (re.findall(u"sha=(\\w+)", RUN_LINE) or [None])[0]
if not (RUN_ID and RUN_SHA):
    die(u"R337 那一跑的 run id / sha 没现读到 ⇒ 第 ⓪ 条只能记「未读」，不许编：" + RUN_LINE[:200])
UI_TITLE_OLD = line_with(rd(AUD), u"## 第 %d 轮" % (AUDIT_N - 1), u"UI_AUDIT 顶节")
aud = rd(AUD)
sta = rd(STA)
if (u"## R%d 状态" % ROUND) in sta:
    die(u"STATE 已经有 R%d 那一节 ⇒ 不许重复轮换" % ROUND)
if len(re.findall(u"(?m)^## R%d 状态" % (ROUND - 1), sta)) != 1:
    die(u"STATE 上一轮节标题不是恰好一处")
before_layers = sta.count(u"\n> ## ")
fr_pre = rd(FRA)
S13_AT = line_with(fr_pre, u"脚本电池现读 **Ran", u"§13 census")
S14_AT = line_with(fr_pre, u"脚本电池 `Ran", u"§14 census")
if fr_pre.count(S13_AT) != 1 or fr_pre.count(S14_AT) != 1:
    die(u"两格 census 定位不唯一")
chg_lines = rd(CHG).splitlines(True)
H3_AT = [i for i, ln in enumerate(chg_lines) if ln.rstrip(u"\n") == u"## [Unreleased]"]
if len(H3_AT) != 1:
    die(u"`## [Unreleased]` 命中 %d 次" % len(H3_AT))
blg_pre = rd(BLG)
if re.search(u"(?m)^\\*\\*%d\\. " % B_TOKENIZER, blg_pre):
    die(u"BACKLOG %d 已被占" % B_TOKENIZER)
for pat, what in ((u"U-31 … U-(\\d+)", u"U 区间那一格"),
                  (u"(决定台账[^\\n]*?D-\\d{3} … \\*\\*)(D-\\d{3})", u"决定台账那一格"),
                  (u"(?m)^- \\*\\*仍开（截至本轮，完整名单以 `AGENT_STATE.md` 的 R\\d+ 节", u"§13 的「仍开」")):
    if len(re.findall(pat, fr_pre)) != 1:
        die(u"报告里 " + what + u" 不是恰好一处")

# ── UI_AUDIT ─────────────────────────────────────────────────────────────────
UI_TITLE = (u"## 第 %d 轮（R%d · %s · U-%d…U-%d）：屏幕上那句说明是**埋点属性**写的 —— "
            u"取 alt 不许在整段标签里搜（U-%d…U-%d · 产品 %d 文件，HTML 通道）\n"
            % (AUDIT_N, ROUND, DATE, UA, UMAX, UA, UMAX, PRODUCT_N))

UI_BODY = u"""- **U-%d：这条缺陷今天第一次变成读数 —— 屏幕上出现的是作者没打算给人读的那一句**（产品 %d 文件：
  `HtmlPreview.swift`）。R337 复盘时它是从源码读出来的（`\\balt` 的词边界在 `data-alt` 里也成立），
  今天用产品入口量：现读 `HTML_ALT_SOURCE 前缀属性没抢=true 值里的假alt没抢=true 带引号的值没抢=true
  重复取第一个=true 单引号认=true`（改前第一颗是 false）。方向与 D-332 相反：那条规矩说"只留作者为
  '图加载不了'准备的那一份"，而这一形状留下的是**埋点属性**的那一份。
- **U-%d：修法不是"把 `\\b` 换成 `\\s`"—— 那种写法会把第二种形状留在原地** ——
  要求"alt 前面是空白"能挡 `data-alt`，但挡不住 `title='见 alt="假的"'`（那个空格是 title 的值给的）。
  所以改成扫**属性对**：一次取出「名字 + 值」，名字整段（不区分大小写）等于 alt 才算 ⇒
  `data-alt` 的名字是 `data-alt`，`title` 的名字是 `title`。这一族的规矩：**修法的形状要由最刁钻的反例决定，
  不由"最小改动"决定**（R336 那条"打空先怀疑反例"是它的另一半）。
- **U-%d：三条子规矩各钉一把刀，因为三种坏法在屏幕上不一样** —— 现读 `mutate_r338 %s,
  RESTORE_CLEAN=%s`（%s）。M993 把名字判等换成后缀匹配（`data-alt` 又能冒充）；
  M994 把"重复 alt 取第一个"倒过来（与 HTML 规范相反）；M995 只认双引号那一支（单引号 alt 被当成没值 ⇒
  整块删，用户少读一句）。三把都红在同一格 `testAltIsTakenFromTheTagsOwnAttribute…` 上，
  但红的断言各是各的 —— 只钉一条，另外两条会漂过去。
- **U-%d：夹具改一行，四张帧全变 —— 而变的**不是**那句 alt** —— 逐张对 bbox 才敢说"变了什么"：
  渲染态两档变的是**头部那串字符数**（夹具长了 30 来个字符 ⇒ 现读 R336→R338 的差 bbox 在
  (%s, %s) 一带），alt 那一行**一字未动**（这正是修法的定义：真 alt 本来就该在那儿）；
  原文态两档变的是夹具源码里那一行。两份读数各管一件事：与**上一轮那 182 张**逐张比 = 比了 %s 张、变了 %s 张
  （全是 HTML 那四张）；基线**同一笔更新**之后再对 = `COMPARED=%s CHANGED=%s MISSING=%s`（0 才是这一笔的收尾态）。
- **U-%d：改前/改后是**同一份夹具、两份构建**拍出来的** —— 把产品换回旧实现（夹具保留新形状）重捕一遍，
  捕获卷当场红两格：`detail-html-rendered：消毒之后 alt 就没了 ⇒ 渲染态里那句话不会出现` ——
  那是**产品级**证人，不是判据级。两档渲染帧的像素差：暗 %s 颗 / 亮 %s 颗，
  bbox=(%s,%s)..(%s,%s) —— 恰好是 alt 那一行（y %s〜%s px = %s〜%s pt）。
  两张裁图亲眼看过：改前那句是「埋点属性写的假说明」，改后是「季度趋势图（图片未加载）」。
- **U-%d：没覆盖的形状要写出来，不许顺手扩** —— 无引号的 `alt=foo` 两种实现都不认（旧的新的一样），
  本轮**没**改这个行为，也没为它写断言 ⇒ 记成"已知没覆盖"，与 404（属性值里含 `>` 会让标签正则先截断）
  合到同一张总账上：这条通道没有真正的 HTML 属性/标签解析器，所有形状都是"正则 + 反例"堆出来的。
  要不要请一个真 tokenizer（或自己写一颗带真值表的）= BACKLOG %d。
- **U-%d：runner 上那朵红已经连红好几跑，而三本账里没有它的名字** —— 读 R%d 那一跑
  （现读 `RUN=%s sha=%s conclusion=%s`）：失败步骤两格（STEP[15] 全量卷、STEP[17] 捕获闸），
  正文里三朵红全在 `%s`：「%s」与「%s」。本机同一卷 `0 failures` 而 runner 上 `3 failures`
  ⇒ 这是**只在另一台机器上才判得了**那一类。可它在 BACKLOG 与 STATE 里都没有名字 ——
  「红必须有名字」是 100 那一族立的规矩，这一朵是那条规矩的**复发**：规矩在，名册漏了一格。
  开 BACKLOG %d，并排在下一轮第一件事：要么给它一条按机器的具名出口（skip 带理由），
  要么把暗档悬停档在 runner 上重新标定 —— 二者修法相反，不许用"CI 一直是红的"糊过去。
""" % (UA, PRODUCT_N, UB, UC, CAUGHT, RESTORE, u"、".join(ARMS_NEW), UD,
       FDB[u"dark"][1][0], FDB[u"dark"][1][1], FD[0], FD[1], BASE[0], BASE[1], BASE[2],
       UE, PIX[u"dark"][0], PIX[u"light"][0],
       PIX[u"dark"][1][0], PIX[u"dark"][1][1], PIX[u"dark"][1][2], PIX[u"dark"][1][3],
       PIX[u"dark"][1][1], PIX[u"dark"][1][3],
       str(int(PIX[u"dark"][1][1]) // 2), str(int(PIX[u"dark"][1][3]) // 2), UF, B_TOKENIZER,
       UG, ROUND - 1, CI_RUN_ID, CI_SHA, CI_CONC, CI_FAIL_TEST,
       CI_MSG1, CI_MSG2, B_RUNNER)

# ── ITERATION ────────────────────────────────────────────────────────────────
ITER_TITLE = (u"## Round %d · R%d（第 %d 轮 · %s）：那句「图的说明」是埋点属性写的 —— "
              u"取 alt 换成扫属性对（产品 %d 文件）\n" % (ITER_N, ROUND, AUDIT_N, DATE, PRODUCT_N))

ITER_BODY = u"""
本轮是 R337 那次回顾的**直接产物**：复盘时从源码读出 `altAttr` 用的是 `\\balt`，
而 ICU 的词边界把 `data-alt` 里那个 `alt` 也算起点。上一轮把它留在 STATE 里当"看到但没量"，
这一轮第一件事就是把它量成读数，然后修掉。

先说量到的东西。夹具里那张图本来只有一个 `alt`，本轮给它加了一个前缀属性
（`data-alt="埋点属性写的假说明"`），然后**同一份夹具拍两遍**——一遍旧构建、一遍新构建：

· 旧构建：屏幕上那句说明就是「埋点属性写的假说明」。捕获卷当场红两格
  （`detail-html-rendered / detail-html-source：消毒之后 alt 就没了`）—— 这不是判据的红，
  是**产物**的红，两档都红。
· 新构建：那句回到「季度趋势图（图片未加载）」。两档渲染帧的像素差
  暗 %s 颗 / 亮 %s 颗，bbox=(%s,%s)..(%s,%s) —— 恰好那一行，别处一个点都没动。
· 两张裁图亲眼看过（这是本轮的看图腿）。

修法上有一处值得单独记：最省事的写法是把 `\\b` 换成 `\\s`（要求 alt 前面是空白）。
它能挡 `data-alt`，但挡不住 `title='见 alt="假的"'` —— 那个空格是**别人的值**给的。
所以这一轮没有走最小改动，而是改成扫属性对：一次取出「名字 + 值」，名字整段等于 alt 才算。
判据里两种形状各一格，加上"重复 alt 取第一个""单引号也认"，四颗读数全 true 才算兑现
（现读 `HTML_ALT_SOURCE 前缀属性没抢=true 值里的假alt没抢=true 带引号的值没抢=true 重复取第一个=true 单引号认=true`）。
三把刀 M993/M994/M995 分别把三条子规矩拆掉，现读 `CAUGHT=%s, RESTORE_CLEAN=%s`。

还有一件"看帧"的方法论事：夹具改一行之后 `CHANGED=4`，但如果我只报这个数就会说错话——
渲染态那两张变的**不是** alt 那一行，而是头部那串字符数（夹具长了，"N 个字符"跟着长）。
逐张对差集的 bbox 才分得清这两件事，而"alt 那一行一字未动"恰恰是这条修法的定义。

本轮没做的：无引号的 `alt=foo` 两种实现都不认，我没顺手扩它，而是把它和 404 合到一张总账
（BACKLOG %d：这条通道没有真正的属性/标签解析器）。

七维度自评：

| 维度 | 分/满分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | %d/15 | 同一份夹具两份构建各拍一遍（182 帧），两档渲染帧逐张对差集 bbox，两张裁图亲眼看过改前/改后 |
| 判据有效性 | %d/15 | 新格 5 颗读数 + 4 种反例形状，三把刀各钉一条子规矩；无引号 alt 明确记为没覆盖（不假装有） |
| 假绿防御 | %d/15 | 改前那两格红是**捕获卷自己**报的（产物级证人）；CHANGED=4 被逐张拆成两种成因，没有当成一个数 |
| 产品面推进 | %d/15 | 产品 1 文件（消毒的取属性那一步），连读归零；但这一位只在"页面同时有前缀属性"时才坏，覆盖面窄 |
| 台账一致性 | %d/15 | 七本 + 报告两格 + 基线同一笔；新开 410 并给 404 记同族关系 |
| 交付诚实性 | %d/15 | 没顺手扩无引号形状；"改前红"按实写成产物级红而不是判据胜利 |
| 可复核性 | %d/15 | 全部读数出自仓库里的尺（判据卷 / round_verify / frame_baseline / 像素差脚本写在台账里） |
""" % (PIX[u"dark"][0], PIX[u"light"][0],
       PIX[u"dark"][1][0], PIX[u"dark"][1][1], PIX[u"dark"][1][2], PIX[u"dark"][1][3],
       CAUGHT, RESTORE, B_TOKENIZER,
       SEVEN[0], SEVEN[1], SEVEN[2], SEVEN[3], SEVEN[4], SEVEN[5], SEVEN[6])

# ── DECISIONS ────────────────────────────────────────────────────────────────
DEC_BODY = u"""### D-%d（%d）取一个属性只有一种正确做法：扫「名字 + 值」成对，名字整段相等；修法的形状要由最刁钻的反例决定

`\\balt\\s*=` 与 `\\salt\\s*=` 都**不是**"取 alt"，它们只是"在标签那串字符里找一个长得像 alt 的地方"。
前者被 `data-alt` 骗（词边界在 `-` 后面成立），后者被 `title='见 alt="假的"'` 骗（那个空格是值给的）。
正确的问法是：这个标签**有哪些属性**？逐个把名字与值成对取出，名字整段等于 alt 的那个才是它的值。

两条可迁移的规矩：

① **修法的形状要由最刁钻的反例决定，不由"最小改动"决定。** 如果本轮只把 `\\b` 换成 `\\s`，
   现读的两种形状里只有一种被修掉，而判据会因为只写了那一种反例而全绿。
   这一族与 R336 那条"刀打空先怀疑反例"是同一枚硬币的两面：**反例的覆盖面决定修法的上限**。
② **属性名匹配要写成"整段相等"，重复属性要有取舍。** 名字整段等于 alt 才算 ⇒
   `data-alt` / `x-alt` / `alt2` 全部出局；重复 alt 取第一个（与 HTML 一致）。
   这两半各配一把刀（M993 后缀匹配、M994 倒序取最后一个、M995 只认双引号），
   因为三种坏法在屏幕上不一样：抢错句、取错句、整句消失。

登记：这条规矩由 M993/M994/M995 三把刀钉住，判据是
`testAltIsTakenFromTheTagsOwnAttributeNotFromAPrefixedNameOrAnotherValue`（五颗读数）；
它没覆盖的形状（无引号 `alt=foo`）与 404 合在 BACKLOG %d 那张总账上 ——
**这条通道没有真正的 HTML 解析器**，所有形状都是"正则 + 反例"堆出来的。
""" % (D1, ROUND, B_TOKENIZER)

# ── BACKLOG ──────────────────────────────────────────────────────────────────
BL_410 = u"""**%d. 这条 HTML 通道没有真正的属性/标签解析器：404（值里含 `>` 先截断）与 R338（属性名前缀冒充 alt）\
是同一件事的两种形状 —— 要不要请一个真 tokenizer（或自己写一颗带真值表的）**（R%d）
现在有的是一排正则：`<img[^>]*/?>` 认标签、`tagAttrs` 认属性对、`\\b`/`\\s` 的历史告诉我们
"在字符串里找长得像的地方"迟早会被新形状击穿。已经量到的三种击穿形状：
① `alt="a>b"` ⇒ 标签正则先截断，剩下的属性文字漏进正文（404，今天由断言钉成现状）；
② `data-alt="…"` ⇒ 词边界把前缀属性当成 alt（R338 已修，修法是扫属性对）；
③ `alt=foo`（无引号）⇒ 两种实现都不认 ⇒ 那句说明**整块消失**（本轮没修，也没写断言，按实记在这里）。
要做的决定不是"再补一条正则"，而是二选一：① 引入一颗真正的解析器（代价：新依赖或一段自己维护的
状态机，收益：这三族一次归零，且 404 那条现状断言可以换成"修好了"）；② 明确决定**不做**，
把"这条通道只处理常见形状"写进产品文档并让每一族反例都有名字（今天的形状）。
判"不做"要有读数：这一族再被量出**第四种**形状，就按①走。
""" % (B_TOKENIZER, ROUND)

BL_CLOSE_404 = u"""

**R%d 追记（同族第二种形状已经出现过一次，并修掉了）**：`data-alt="…" alt="…"` 会让
`\\balt` 取到**前缀属性**的值 ⇒ 屏幕上出现作者没打算给人读的一句话（现读改前
`HTML_ALT_SOURCE 前缀属性没抢=false`，改后五颗全 true）。修法不是再补一条正则，而是换成
**扫属性对**（名字整段相等才算），见 D-%d 与 U-%d。这一条与本条（值里含 `>` 的截断）合到
BACKLOG %d 那张总账上：三种形状都指向"这里没有真正的解析器"。
""" % (ROUND, D1, UA, B_TOKENIZER)

BL_411 = u"""**%d. runner 上 `%s` 连着红，而三本账里没有它的名字：先决定"按机器的具名出口"还是"在 runner 上重新标定暗档悬停"—— 两条修法相反**（R%d 读 R%d 那一跑现读）`RUN=%s sha=%s conclusion=%s`，失败步骤 STEP[15]（全量卷）与 STEP[17]（捕获闸），正文三朵红全在这一格上：「%s」、「%s」。本机同一卷 `0 failures`，runner 上 `3 failures`，且**上一跑（%s）同名的红有 11 行** ⇒ 不是本轮引入的，是挂着没人登记。这一族的规矩早就写过了（BACKLOG 100：动效那一步的红必须有名字），所以本条不是新病，是**旧规矩的洞**：名册按机器切片之后，"runner 独有且长期红"这一类没有落点。两条出路（各自能被一条读数分辨，别混着试）：① 按机器的具名出口 —— 像 174/196 那样给这一档一个 `..._NOT_RUN=RUNNER_LEVELS_COLLAPSE` 的 skip，前提是先证明 runner 上那两档**确实**读成同一个灰阶（现读 70 对 70），而不是矩形打偏；② 重新标定 —— 若 R334 那颗"悬停与选中只差 4 级"的余量在 runner 的字族/材质上被吃掉，那是**产品**的余量不够，该抬的是令牌，不是判据。先做①还是②由一格实验决定：同一份夹具在 runner 上打两档的取样矩形与灰阶读数（本轮没做，记在这里）。
""" % (B_RUNNER, CI_FAIL_TEST, ROUND, ROUND - 1, CI_RUN_ID, CI_SHA, CI_CONC,
       CI_MSG1, CI_MSG2, (re.findall(u"PREV_RUN_(\d+)", rd(CI_LOG)) or [u"未读"])[0])

# ── CHANGELOG ────────────────────────────────────────────────────────────────
CHG_ENTRY = u"""### 屏幕上那句"图的说明"差点是埋点属性写的：取 alt 换成扫属性对（R%d / U-%d…U-%d · 产品 %d 文件）

- `<img>` 的 alt 不再用 `\\balt\\s*=` 在整段标签里搜（ICU 的词边界把 `data-alt` 里那个 `alt` 也算起点）。
  现在扫「属性名 + 值」成对，名字整段等于 alt 才算；重复 alt 取第一个（与 HTML 一致），单双引号都认。
- 新判据 `testAltIsTakenFromTheTagsOwnAttributeNotFromAPrefixedNameOrAnotherValue`：
  前缀属性 / 别人的值里含 `alt="…"` / 重复属性 / 单引号 四种形状，五颗读数
  `HTML_ALT_SOURCE 前缀属性没抢=true 值里的假alt没抢=true 带引号的值没抢=true 重复取第一个=true 单引号认=true`。
- 刀 M993/M994/M995 三把（后缀匹配 / 倒序取最后一个 / 只认双引号），现读 `%s`。
- 产物证人：同一份夹具两份构建各拍一遍，两档渲染帧的 alt 那一行差 %s（暗）/ %s（亮）个像素，
  别处一个点没动；改前那一跑由捕获卷自己报红两格。基线同一笔更新（`COMPARED=%s CHANGED=%s`）。
- 新开 %d（这条通道没有真正的解析器：404 / R338 / 无引号 alt 三族合账），404 收到一条追记。
""" % (ROUND, UA, UMAX, PRODUCT_N, CAUGHT, PIX[u"dark"][0], PIX[u"light"][0],
       BASE[0], BASE[1], B_TOKENIZER)

# ── STATE ────────────────────────────────────────────────────────────────────
STATE_BODY = u"""## R%d 状态（%s · 本地 · 第 %d 轮 / Round %d）：屏幕上那句说明是埋点属性写的 —— 取 alt 换成扫属性对（产品 %d 文件，HTML 通道）

最后更新：%s（本地 · R%d / 第 %d 轮 / Round %d）：把 R337 复盘时"看到但没量"的那条形状量成读数并修掉 ——
`\\balt` 会被 `data-alt` 冒充 ⇒ 消毒留下的是埋点属性那句话（产品 %d 文件 · HTML 通道）

本轮做了什么：一轮回顾的**直接产物**。
① 量：给 HTML 夹具那张图加一个前缀属性（`data-alt="埋点属性写的假说明"`），**同一份夹具拍两遍**
  （旧构建 / 新构建）。旧构建那一跑由捕获卷自己红两格（`消毒之后 alt 就没了`）—— 产物级证人；
  两档渲染帧的 alt 那一行差 %s（暗）/ %s（亮）个像素，bbox=(%s,%s)..(%s,%s)，别处一个点没动。
② 修：不再"在标签串里找长得像 alt 的地方"，改成扫「属性名 + 值」成对、名字整段等于 alt 才算
  （重复取第一个、单双引号都认）。**没走最小改动**：`\\b`→`\\s` 挡得住 `data-alt`，
  挡不住 `title='见 alt="假的"'`（那个空格是值给的）⇒ 修法的形状由最刁钻的反例决定（D-%d）。
③ 钉：新判据五颗读数 + 四种反例；三把刀 M993/M994/M995 各拆一条子规矩，现读 `%s`。
④ 边界：无引号的 `alt=foo` 两种实现都不认 ⇒ **没顺手扩**，与 404 合到 BACKLOG %d（这条通道没有真正的解析器）。

验证读数（现读）：`HTML_ALT_SOURCE 前缀属性没抢=true 值里的假alt没抢=true 带引号的值没抢=true 重复取第一个=true 单引号认=true`；
判据卷 `Executed %s（failures=%s）`；`ROUND_VERIFY build_warnings=%s swift_executed=%s swift_skipped=%s swift_failures=%s frames=%s baseline_compared=%s baseline_changed=%s baseline_missing=%s dmg=%s installed_version=%s dir=%s`；
捕获 `CAPTURED %s -> /tmp/r338_rv/frames`（改前那一跑在 /tmp/r338b_before）；
变异表 `mutate_r338 %s, RESTORE_CLEAN=%s`（%s）；针预检 `tables=%s covered=%s arms=%s bad=%s`、
臂名册 `files=%s arms=%s dupes=0`；清账表 `%s`；脚本电池 `Ran %s（skipped=%s）`；
产品面连续零改动 **%s** 轮（现读 `scripts/product_streak.py` 的 streak —— 这一整句必须在同一行里：`_cells` 问的是"那一格有没有引用取数口"，分两行写就等于没引用）；取数口 `--streak-for %d`。
§8 搬运：本轮新读数族 `HTML_ALT_SOURCE` 在它被打印的同一笔里接进名单
（`READINGS_MUST_INCLUDE` 见下方结论行）。

NOT-RUN（三种缺席分开写，不许省略）：① **只在人身上判得了**：真窗口里复制一段带 `data-alt` 的网页，
渲染态那句说明是不是"季度趋势图"这一类作者原文（离屏帧已证像素级改前/改后，但真机眼仍欠一次）。
② **只在 runner 上判得了**：`HTML_ALT_SOURCE` 五颗在 runner 上签不签（它不读字体度量，理论上两机同数）、
本轮随基线更新的那几张（与上一轮逐张比 = 变了 %s 张，全是 HTML 两档）在 runner 上会不会被判成 changed。
③ **这条通道看不见 / 没做**的：无引号 `alt=foo` 没修也没断言（按实挂在 BACKLOG %d）；
400（CJK 强调的墨量尺）本轮**仍然没量**。

下一轮（R%d）的靶：⓪ 读 CI 配对（成对：run id ↔ commit，现读自 `scripts/ci_read.py latest`）——
**R%d 那一跑已读完**：`RUN=%s sha=%s conclusion=%s`，失败步骤两格（STEP[15] 全量卷 / STEP[17] 捕获闸），
三朵红全在 `%s` 这一格上（「%s」/「%s」）—— 本机同一卷 0 failures ⇒ 它是**按机器才判得了**那一类，
而它在三本账里没有名字 ⇒ 第一件事是 %d：先决定"按机器的具名出口"还是"在 runner 上重新标定"，
两条修法相反，不许用"CI 一直是红的"糊过去。R%d 代码半 b232c9a 的 run id 按 sha 逐笔问。
这一跑还要答：⓪a 新守卫 `test_ledger_citations.py` 三格在 runner 上签不签（它读台账本身 ⇒ 该同数）；
⓪b 本轮新基线（`CHANGED=%s` 那四张）在 runner 上是不是 changed；⓪c 电池例数两机对账（本机现读 %s）。
→ ① **BACKLOG 405**：把"标题里那半句产品 K 文件"立成定义并变成电池里会红的门
  （回顾尺现读 `%s`；R334/R335 走显式豁免）。它比动效那一串便宜，而且是审计链自己的可读性。
→ ② 动效主线仍排队：399（亮档悬停换轴，先量系统那颗的方向）、390 的 before/after、389 的时长、
  384 的横轴、387①、376、367/360/361/364 → ③ 409（暗档左列 %s:1 是通道还是产品：两臂参照判据或真机眼）
  与 410（要不要真 tokenizer）都**不**该被"再补一条正则"糊过去 → ④ 400 要先造笔画墨量尺。

本轮的自伤（写成出处，不写成缺陷）：给夹具加那一行之前，我先拍了"改前"那一跑并**忘了夹具已经改过**——
第一版"改前"其实是新夹具 + 旧实现（正是我要的那一份，纯属运气）。教训是：before/after 的两遍
必须各自写下**当时的工作树状态**（本轮靠 `git diff --stat` 现读留了痕），否则"改前"两个字
可能指着一份没人知道的东西。
""" % (ROUND, DATE, AUDIT_N, ITER_N, PRODUCT_N, DATE, ROUND, AUDIT_N, ITER_N, PRODUCT_N,
       PIX[u"dark"][0], PIX[u"light"][0],
       PIX[u"dark"][1][0], PIX[u"dark"][1][1], PIX[u"dark"][1][2], PIX[u"dark"][1][3],
       D1, CAUGHT, B_TOKENIZER, ALT_CELLS[0], ALT_CELLS[1], BUILD_W, SWIFT[0], SWIFT[1],
       SWIFT[2], FRAMES, BASE[0], BASE[1], BASE[2], DMG, VER, RV_DIR, CAPTURED,
       CAUGHT, RESTORE, u"、".join(ARMS_NEW), PRE[0], PRE[1], PRE[2], PRE[3],
       ARM_TOTAL[0], ARM_TOTAL[1], GATE_LINE, BATT, BATT_SKIP, STREAK_N, AUDIT_N,
       FD[1], B_TOKENIZER,
       ROUND + 1, ROUND - 1, CI_RUN_ID, CI_SHA, CI_CONC, CI_FAIL_TEST, CI_MSG1, CI_MSG2,
       B_RUNNER, ROUND - 1, BASE[1], BATT, CLAIMS_SHORT, u"1.23")

sta2 = rd(STA)
pos = sta2.index(line_with(sta2, u"## R%d 状态" % (ROUND - 1), u"STATE 上一轮节标题"))

# ── 写盘（七本一起，锚点已在上面统一验过） ──────────────────────────────────
wr(AUD, aud[:aud.index(UI_TITLE_OLD)] + UI_TITLE + u"\n" + UI_BODY.rstrip(u"\n") + u"\n\n"
   + UI_TITLE_OLD + aud[aud.index(UI_TITLE_OLD) + len(UI_TITLE_OLD):])
wr(ITE, rd(ITE).rstrip(u"\n") + u"\n\n" + ITER_TITLE + ITER_BODY.rstrip(u"\n") + u"\n")
wr(DEC, rd(DEC).rstrip(u"\n") + u"\n\n" + DEC_BODY.rstrip(u"\n") + u"\n")

blg = rd(BLG)
m404 = re.search(u"(?m)^\\*\\*404\\. .*?(?=^\\*\\*\\d{3}\\. |\\Z)", blg, re.S)
if not m404:
    die(u"BACKLOG 404 找不到，追记无处可挂")
blg = blg[:m404.end()].rstrip(u"\n") + BL_CLOSE_404.rstrip(u"\n") + u"\n" + blg[m404.end():].lstrip(u"\n")
blg = blg.rstrip(u"\n") + u"\n\n" + BL_410.rstrip(u"\n") + u"\n"
blg = blg.rstrip(u"\n") + u"\n\n" + BL_411.rstrip(u"\n") + u"\n"
wr(BLG, blg.rstrip(u"\n") + u"\n")

wr(CHG, u"".join(chg_lines[:H3_AT[0] + 1]) + u"\n" + CHG_ENTRY.rstrip(u"\n") + u"\n\n"
   + u"".join(chg_lines[H3_AT[0] + 1:]))
wr(STA, sta2[:pos] + STATE_BODY.rstrip(u"\n") + u"\n\n" + sta2[pos:])
after = rd(STA)
if after.count(u"\n> ## ") != before_layers:
    die(u"STATE 轮换改动了 `> ##` 层数：%d → %d" % (before_layers, after.count(u"\n> ## ")))
if (u"## R%d 状态" % (ROUND - 1)) not in after:
    die(u"STATE 轮换把上一轮的节标题弄丢了")

# ── FINAL_REPORT：计数器两格 + §14 census + 「仍开」轮次 ────────────────────
fr = rd(FRA)
U_MAX_NOW = max(int(x) for x in re.findall(u"(?m)^- \\*\\*U-(\\d{3,4})[：(]", rd(AUD)))
D_MAX_NOW = max(int(x) for x in re.findall(u"(?m)^### D-(\\d{3})", rd(DEC)))
B_MAX_NOW = max(int(x) for x in re.findall(u"(?m)^\\*\\*(\\d{2,4})\\. ", rd(BLG)))
if (U_MAX_NOW, D_MAX_NOW, B_MAX_NOW) != (UMAX, D1, B_RUNNER):
    die(u"落盘后最大号与计划不一致：%d/%d/%d" % (U_MAX_NOW, D_MAX_NOW, B_MAX_NOW))
mUD = re.search(u"U-31 … U-(\\d+)", fr)
fr = once(fr, mUD.group(0), u"U-31 … U-%d" % U_MAX_NOW)
m = re.search(u"(决定台账[^\\n]*?D-\\d{3} … \\*\\*)(D-\\d{3})", fr)
fr = fr[:m.start(2)] + (u"D-%d" % D_MAX_NOW) + fr[m.end(2):]
prod_hits = [ln for ln in re.findall(u"(?m)^- \\*\\*产品面（这一节最该被读的部分）\\*\\*：.*$", fr)
             if u"产品面连续零改动轮数" in ln]
if len(prod_hits) != 1:
    die(u"带连读那一格的「产品面」行应为恰好一处，实得 %d" % len(prod_hits))
new_prod = (u"- **产品面（这一节最该被读的部分）**：本轮产品文件 **%d** 个（**HTML 通道**："
            u"`HtmlPreview.swift` 取 alt 换成扫属性对 —— `\\balt` 会被 `data-alt` 冒充，"
            u"屏幕上留下埋点那句话）。产物证人：同一份夹具两份构建，两档渲染帧 alt 那一行差 "
            u"%s（暗）/ %s（亮）个像素，别处没动；基线同一笔更新。"
            u"产品面连续零改动轮数 = **%s**（现读 `python3 scripts/product_streak.py`）。"
            u"新开 %d（这条通道没有真正的解析器：404 / 本轮 / 无引号 alt 三族合账）"
            u"与 %d（runner 上那朵没名字的悬停档红）；404 收到一条追记。"
            % (PRODUCT_N, PIX[u"dark"][0], PIX[u"light"][0], STREAK_N, B_TOKENIZER, B_RUNNER))
fr = once(fr, prod_hits[0], new_prod)
new_s14_line = (u"- **判据与门的规模**（R%d 现读，这一格是最新的权威，§13 那格已冻结成历史）："
                u"脚本电池 `Ran %s`（skipped=%s）；变异臂在册 **%s** 把 / 扫了 **%s** 个表文件"
                u"（预检 tables=%s covered=%s arms=%s bad=%s）；"
                u"U 定义行最大 **U-%d**、决定最大 **D-%d**、BACKLOG 最大 **%d**；"
                u"本轮刀 `mutate_r338.py CAUGHT=%s, RESTORE_CLEAN=%s`（%s）。"
                % (ROUND, BATT, BATT_SKIP, ARM_TOTAL[1], ARM_TOTAL[0],
                   PRE[0], PRE[1], PRE[2], PRE[3], U_MAX_NOW, D_MAX_NOW, B_MAX_NOW,
                   CAUGHT, RESTORE, u"、".join(ARMS_NEW)))
fr = once(fr, S14_AT, new_s14_line)
fr = re.sub(u"(?m)^(- \\*\\*仍开（截至本轮，完整名单以 `AGENT_STATE.md` 的 R)\\d+( 节)",
            u"\\g<1>%d\\g<2>" % ROUND, fr, count=1)
if re.search(u"@\\w+@", fr):
    die(u"报告里还有没替换的占位符或空操作")
wr(FRA, fr)

sc, src_rc = sh([sys.executable, SRCCELL, u"--write"])
if src_rc != 0:
    die(u"Sources 那一格刷新失败：" + sc.strip()[-300:])

# ── 写盘之后：§1 刷新 → 电池 → 连读门 → 曲线 → 七维表 → §8 名单 ─────────────
rf0, rfc0 = sh([sys.executable, FRESH])
if rfc0 != 0 or u"REFUSED" in rf0:
    die(u"报告 §1 的刷新器没签：%s" % rf0.strip()[-300:])
ite_after = rd(ITE)
rows = re.findall(u"(?m)^\\| ([^|]+) \\| (\\d+)/(\\d+) \\|",
                  ite_after.split(u"## Round %d · R%d" % (ITER_N, ROUND))[-1])
if len(rows) != 7 or any(mx != u"15" for _, _, mx in rows):
    die(u"七维表形状不对：行=%d 量纲=%s" % (len(rows), [r[2] for r in rows]))
if [int(v) for _, v, _ in rows] != SEVEN:
    die(u"七维表与 SEVEN 不一致：%s" % ([int(v) for _, v, _ in rows],))
bt2, brc2 = sh([sys.executable, u"-m", u"unittest", u"discover", u"-s", u"scripts/tests"])
BATT2 = (re.findall(u"Ran (\\d+) tests", bt2) or [u"?"])[-1]
if brc2 != 0:
    die(u"落盘之后脚本电池红了（Ran=%s）：%s" % (BATT2, bt2.strip()[-1200:]))
if BATT2 != BATT:
    die(u"落盘前后例数不同：%s → %s" % (BATT, BATT2))
ck, ckc = sh([sys.executable, STREAK, u"--check"])
if ckc != 0:
    die(u"连读门不认这版台账：" + ck.strip()[-500:])
cvc, cvc_rc = sh([sys.executable, CURVE])
if cvc_rc != 0 or u"GAPS=none" not in cvc:
    die(u"落盘之后曲线尺不干净：" + cvc.strip()[-300:])
scores = dict((int(k), int(v)) for k, v in
              re.findall(r"(\d+)=(\d+)", (re.findall(r"(?m)^SCORES_BY_ROUND .*$", cvc) or [u""])[-1]))
DERIVED = scores.get(ITER_N, u"没解析到")
rl, rlc = sh([sys.executable, ROWS, RV_DIR + u"/full.log", u"--must-include", u"HTML_ALT_SOURCE"])
if rlc != 0:
    die(u"§8 名单没签（本轮新族 HTML_ALT_SOURCE）：" + rl.strip()[-500:])
ROWS_LINE = (re.findall(u"(?m)^READINGS_MUST_INCLUDE .*$", rl) or [u"没解析到结论行"])[-1]
print(u"R338_ROWS " + ROWS_LINE)
print(u"R338_LEDGERS_OK 七本=%d 电池=%s 连读=%s 派生分=%s 刀=%s 臂=%s/%s U=%d D=%d B=%d 帧=%s 基线变=%s"
      % (len(WRITTEN), BATT2, STREAK_N, DERIVED, CAUGHT, ARM_TOTAL[1], ARM_TOTAL[0],
         U_MAX_NOW, D_MAX_NOW, B_MAX_NOW, FRAMES, BASE[1]))
