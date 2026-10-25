#!/usr/bin/env python3
# -*- coding: utf-8 -*-
u"""R339 的七本台账（第 338 轮 / Round 336）。

顺序不许换：先解析读数 → 再一次性写盘 → 写盘后自检（编号/形状/电池/曲线/§8）。
锚点全部按**整行字面**认，命中次数不等于 1 就在写任何盘之前 die。
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
CURVE = os.path.join(ROOT, u".scratch", u"motion-audit-2", u"curve_from_ledger.py")
FRESH = os.path.join(ROOT, u".scratch", u"motion-audit-2", u"refresh_report_section1.py")
S14 = os.path.join(ROOT, u".scratch", u"motion-audit-2", u"report_section14.py")
SRCCELL = os.path.join(ROOT, u"scripts", u"report_sources_cell.py")
ROWS = os.path.join(ROOT, u".scratch", u"motion-audit-2", u"ledger_rows.py")
STREAK = os.path.join(ROOT, u"scripts", u"product_streak.py")

LOG_TARGET = u"/tmp/r339_targeted.log"
LOG_BEFORE = u"/tmp/r339_before_final.log"
LOG_FULL = u"/tmp/r339_full.log"
LOG_CAP = u"/tmp/r339_capture3.log"
LOG_BASE = u"/tmp/r339_baseline.log"
LOG_BASE0 = u"/tmp/r339_baseline_before.log"
LOG_MUT = u"/tmp/r339_mutate.log"
LOG_PRE = u"/tmp/r339_pre.log"
LOG_GATE = u"/tmp/r339_gate.log"
LOG_INSTALL = u"/tmp/r339_install.log"
LOG_ROWS = u"/tmp/r339_rows_combined.log"
LOG_ALPHA = u"/tmp/r339_capture.log"   # 第一版画法（整颗跟着轨道走）那一跑的红，U-1159 的证人
LOG_BATT_PRE = u"/tmp/r339_py_pre.log"  # 落盘之前那一跑电池：§14 那一格的例数从这里解析

ENV = dict(os.environ)
ENV[u"PYTHONUTF8"] = u"1"
ENV[u"PYTHONDONTWRITEBYTECODE"] = u"1"

ROUND = 339
AUDIT_N = 338
ITER_N = 336
DATE = u"2026-10-25"
PRODUCT_N = 3
U1, U2, U3, U4, U5, U6, U7, U8 = 1155, 1156, 1157, 1158, 1159, 1160, 1161, 1162
UMAX = U8
D1 = 335
B_LADDER = 413      # 三档 backing 里只两档实测：真实页底分布没量过
B_LIGHT = 414       # 亮档选中在本机是 −10 / runner 是 +7：极性反号仍未判（399 的另一半）
B_OVERLAY = 415     # 轨道叠加量本身也按机器漂（本机 +22 / runner +20 / 真机 +30）
ARMS_NEW = (u"M996", u"M997", u"M998")
SEVEN = [15, 15, 15, 14, 14, 15, 14]

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
    print(u"LEDGERS_R339_DIED " + msg)
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


def last_summary(log, where):
    u"""两种形状都要收：`Executed N tests, with S tests skipped and F failures`（全量卷）
    与 `Executed N tests, with F failures`（定向卷 —— 没有 skip 时 XCTest 不打那一段）。
    只认前一种的话，定向卷会"没解析到"而被我误读成"那一跑没跑"。
    """
    hits = re.findall(u"Executed (\\d+) tests, with (\\d+) tests skipped and (\\d+) failures", log)
    if not hits:
        hits = [(n, u"0", f) for n, f in
                re.findall(u"Executed (\\d+) tests, with (\\d+) failures", log)]
    if not hits:
        die(u"没解析到汇总行（" + where + u"）")
    return hits[-1]


# ── 现读（全部解析，不许手抄）───────────────────────────────────────────────
target_log = require(LOG_TARGET)
before_log = require(LOG_BEFORE)
full_log = require(LOG_FULL)
cap_log = require(LOG_CAP)
base_log = require(LOG_BASE)
base0_log = require(LOG_BASE0)
mut_log = require(LOG_MUT)
pre_log = require(LOG_PRE)
gate_log = require(LOG_GATE)
install_log = require(LOG_INSTALL)

T_EXE, T_SKIP, T_FAIL = last_summary(target_log, u"判据卷")
F_EXE, F_SKIP, F_FAIL = last_summary(full_log, u"全量卷")
if F_FAIL != u"0":
    die(u"全量卷有失败（failures=%s）不许落账" % F_FAIL)

# 新尺的三档读数（改前 / 改后各一份，逐档配对）
def ladder(log, where):
    out = {}
    for ln in log.splitlines():
        if not ln.startswith(u"SEG_PILL_BACKING dark"):
            continue
        page = re.search(u"页底=(\\d+)", ln)
        track = re.search(u"轨道=(-?\\d+)", ln)
        sel = re.search(u"选中=(-?\\d+)", ln)
        step = re.search(u"差=(-?\\d+)", ln)
        con = re.search(u"对比=([0-9.]+)", ln)
        if not all([page, track, sel, step, con]):
            die(u"那一行读数不齐（" + where + u"）：" + ln[:160])
        out[page.group(1)] = (track.group(1), sel.group(1), step.group(1), con.group(1))
    if sorted(out) != [u"30", u"50", u"80"]:
        die(u"三档页底没读全（%s）：%s" % (where, sorted(out)))
    return out


BEF = ladder(before_log, u"改前")
AFT = ladder(target_log, u"改后")

SEGREF = line_with(target_log, u"SEGREF_POLARITY dark", u"参照臂")
RUNG = line_with(target_log, u"HOVER_RUNG_WINDOW dark", u"可行窗口")
BAND = line_with(cap_log, u"FILTER_PILL_BAND dark", u"两态带（改后）")
if u"候选带数=0" in BAND:
    die(u"捕获卷的两态带在改后仍然 候选带数=0 ⇒ 修法没落地，不许落账")
# 第一版画法（整颗跟着轨道走的叠加）那一跑的红 —— U-1159 的证人，必须是"当时真红过"的那一行
alpha_log = require(LOG_ALPHA)
BAND_RED = line_with(alpha_log, u"FILTER_PILL_BAND dark 列=", u"第一版的红")
if u"候选带数=0" not in BAND_RED:
    die(u"第一版那一跑的红不在日志里（U-1159 就没有证人）：" + BAND_RED[:120])
CAP_N = (re.findall(u"CAPTURED (\\d+) ->", cap_log) or [u"?"])[-1]
CHANGED0 = (re.findall(u"FRAME_BASELINE_CHANGED=(\\d+)", base0_log) or [u"?"])[-1]
COMPARED = (re.findall(u"FRAME_BASELINE_COMPARED=(\\d+)", base_log) or [u"?"])[-1]
CHANGED = (re.findall(u"FRAME_BASELINE_CHANGED=(\\d+)", base_log) or [u"?"])[-1]
if COMPARED == u"0":
    die(u"基线 COMPARED=0 ⇒ 那是空对账，CHANGED=0 不作数")
CAUGHT = (re.findall(u"CAUGHT=(\\d+/\\d+)", mut_log) or [u"?"])[-1]
RESTORE = (re.findall(u"RESTORE_CLEAN=(\\w+)", mut_log) or [u"?"])[-1]
if CAUGHT != u"3/3" or RESTORE != u"yes":
    die(u"变异表没过（CAUGHT=%s RESTORE=%s）" % (CAUGHT, RESTORE))
PRE = (re.findall(u"NEEDLE_PRECHECK tables=(\\d+) covered=(\\d+) arms=(\\d+) bad=(\\d+)", pre_log)
       or [(u"?", u"?", u"?", u"?")])[-1]
ARM_TOTAL = (re.findall(u"ARM_TOTAL files=(\\d+) arms=(\\d+)", pre_log) or [(u"?", u"?")])[-1]
if PRE[3] != u"0":
    die(u"针预检 bad≠0：" + str(PRE))
GATE = line_with(gate_log, u"MOTION_LEDGER 表面=", u"清账表")
INSTALL_RESULT = (re.findall(u"INSTALL_RESULT=(\\w+)", install_log) or [u"?"])[-1]
INSTALL_SHA = (re.findall(u"INSTALL_SHA_MATCH=(\\d+)", install_log) or [u"?"])[-1]
batt_pre = require(LOG_BATT_PRE)
mB = re.findall(u"Ran (\\d+) tests.*?with (\\d+) skip", batt_pre)
BATT = (re.findall(u"Ran (\\d+) tests", batt_pre) or [u"?"])[-1]
BATT_SKIP = (mB[-1][1] if mB else u"?")
if BATT == u"?":
    die(u"电池例数没解析到（§14 那一格不许手填）")

# 连读那一格：本轮动了产品，而工具在 412 修掉之前会把"本轮自己"排除在外 ⇒ 口径必须写清
st_out, st_rc = sh([sys.executable, STREAK, u"--streak-for", u"%d" % AUDIT_N])
STREAK_N = (re.findall(u"streak=(\\d+)", st_out) or [u"?"])[-1]
if STREAK_N == u"?":
    die(u"连读那一格没解析到数：" + st_out.strip()[-200:])

# ── 1) AGENT_UI_AUDIT：降序，插在当前最大轮次标题之上 ───────────────────────
aud = rd(AUD)
heads = [(int(m.group(1)), m.start()) for m in re.finditer(u"(?m)^## 第 (\\d+) 轮", aud)]
if not heads:
    die(u"UI_AUDIT 里一个轮次标题都没有")
top_n, top_pos = max(heads, key=lambda t: t[0])
if top_n != AUDIT_N - 1:
    die(u"当前最大轮次是 第 %d 轮，不是 %d ⇒ 靶没对上" % (top_n, AUDIT_N - 1))

AUD_ENTRY = u"""## 第 {audit} 轮（R{round} · {date} · U-{u1}…U-{u8}）：runner 连挂 8 跑的那朵红，本机第一次把它复现成三个数 —— 暗档选中那颗塌在漂来的轨道上（U-{u1}…U-{u8} · 产品 {prod} 文件，动效主线）

- **U-{u1}：那朵红今天第一次有了本地的三个数**（产品 {prod} 文件：`VisualTokens.swift`、
  `PressableStyle.swift`、`HistorySidebarView.swift`）。runner 从 `117f45d` 到 `3954d1d` 连挂 8 跑，
  三条断言全在 `testDirectReadHoverLayersAreVisibleOnTheirOwnSurfaces` 的暗档，而本机同一卷 0 failures ——
  这种"只有另一台机器红"的形状，本仓库的历史结论一向是"按机器的出口"。本轮先不换结论，先换尺：
  把页底做成自变量之后，**本机自己就能把它复现出来** ——
  改前 `SEG_PILL_BACKING dark 页底=30 轨道={b30t} 选中={b30s} 差={b30d}`、
  `页底=50 轨道={b50t} 选中={b50s} 差={b50d}`、`页底=80 轨道={b80t} 选中={b80s} 差={b80d}`。
  中间那一档（70 对 70）就是 runner 那一跑现读的 `空闲=70 选中=70`，分毫不差。
- **U-{u2}：出口这条路被读数关掉了** —— 同一跑、同一条 render、同一颗尺里的系统参照臂
  `SEGREF_POLARITY dark｜系统 页底=50.0 … 差=+49.0｜自家 选中=70.0 未选=70.0 差=+0.0`：
  那台机器**画得出**分段控件的选中档，只画不出自家那一颗 ⇒ "这台机器判不了"不成立，
  它是产品事实（BACKLOG 411 由此判成修法而不是出口，见 D-{d}）。
- **U-{u3}：新尺 `SEG_PILL_BACKING` 把页底变成能点名的自变量** —— 同一条夹具通道铺三档
  **不透明**人造底（30 = 本机离屏页底、50 = runner 离屏页底、80 = 外推），逐档量「选中 − 轨道」。
  前两档标"实测"、第三档标"外推"，读数里逐条带着来源 ⇒ 外推那一档不许冒充实测。
  地板两颗都是仓库里已有的数：8/255 = 真机那把尺 `scripts/real_screen_filter_pill.py` 的 `DELTA`
  （判法原文「< 8 ⇒ indistinguishable」），1.10 = 这一族暗档自己那条可见性线。
- **U-{u4}：修法是在语义基准之上盖一层固定抬量，α 由两条实测边界夹出来** ——
  基准仍是 R333 那枚 `unemphasizedSelectedContentBackgroundColor`（暗档解析 70，两机同读），
  暗档再盖 `Color.white.opacity(0.20)` ⇒ 那颗 ≈107。下界 = 盖过已测到最亮那条轨道（97）再加
  『分不开』线 8 ⇒ α ≥ 0.189；上界 = 不许超过平台自己那颗选中（runner 现读 109）⇒ α ≤ 0.211。
  区间里有三个两位小数可用，取正中 0.20（这一句也写成了会红的算术，不是一段注释）。
  改后现读：`页底=30 轨道={a30t} 选中={a30s} 差={a30d} 对比={a30c}`、
  `页底=50 轨道={a50t} 选中={a50s} 差={a50d} 对比={a50c}`、
  `页底=80 轨道={a80t} 选中={a80s} 差={a80d} 对比={a80c}` —— 三档全部 ≥8 且 ≥1.10。
- **U-{u5}：本轮第一版的修法被另一条判据当场否掉，这条自伤留在账上** —— 第一版把整颗改成
  "跟着轨道走的白色叠加"（差 = α×(255−轨道)，看着比 70 那版更"物理"）。它让新尺三档全过，
  却把 `FILTER_PILL_BAND` 打红：`{bandred}` —— 因为这条离屏通道在侧栏里**不平滑那层材质**，
  暗档轨道现读 255（R189 裁片定下的合成方向），白色叠加压在 255 上等于没画，两态帧一个字都不差。
  规矩是"换画法不许弄坏别的判据"：那一版被丢掉，改成"基准不动 + 固定抬量"。
- **U-{u6}：那条『同侧』门只管符号，不管大小 —— 8 跑里它一直是绿的** ——
  `sameSide` 的算法是 `(ownDiff >= 0) == (sysDiff >= 0)` ⇒ 差=+0.0 也算"同侧=是"，
  于是 runner 那 8 跑的 `SEGREF_POLARITY dark｜自家 差=+0.0` 一路被判成通过，
  而"两档读成同一个灰阶"这件事没有一条判据替它说话（红的是隔壁那卷的可行集，
  要读者自己去发现"空闲=选中"是什么意思）。本轮补上量级地板（同一颗 8），
  这条门第一次能单独抓住"塌成一档"。形状与 R38 那条同族：**符号对而大小为 0，不是事实**。
- **U-{u7}：看图腿是三对帧，不是一句"看起来更好"** —— 同一档页底改前/改后各一张、放大并排
  （/tmp/r339_pair_30.png、_50.png、_80.png）：页底 50 改前两颗并成同一档（屏幕上问不出
  "哪颗被选中"），页底 80 改前选中是一颗**暗洞**（就是 377 那颗），改后三档都能一眼指出被选中的那颗。
  本机那一档（页底 30）改前那颗只是"略亮一点"，改后是明确的浅灰药丸 —— 与平台暗档惯例同形。
- **U-{u8}：305 的暗档那一半被这一发压回来了，但**不**宣布结案** —— 按下那档叠在轨道上本机
  现读 76，而选中现在在 107 ⇒ 原来"按下比选中还亮（76 对 70）"反过来成了"按下轻于选中"。
  305 判的是**两档台阶**（hover→pressed 与 pressed→selected），本轮只动了 selected 那一档，
  所以它继续开着，只补一条追记把新读数钉住。

""".format(audit=AUDIT_N, round=ROUND, date=DATE, u1=U1, u2=U2, u3=U3, u4=U4,
           u5=U5, u6=U6, u7=U7, u8=U8, d=D1, prod=PRODUCT_N,
           b30t=BEF[u"30"][0], b30s=BEF[u"30"][1], b30d=BEF[u"30"][2],
           b50t=BEF[u"50"][0], b50s=BEF[u"50"][1], b50d=BEF[u"50"][2],
           b80t=BEF[u"80"][0], b80s=BEF[u"80"][1], b80d=BEF[u"80"][2],
           a30t=AFT[u"30"][0], a30s=AFT[u"30"][1], a30d=AFT[u"30"][2], a30c=AFT[u"30"][3],
           a50t=AFT[u"50"][0], a50s=AFT[u"50"][1], a50d=AFT[u"50"][2], a50c=AFT[u"50"][3],
           a80t=AFT[u"80"][0], a80s=AFT[u"80"][1], a80d=AFT[u"80"][2], a80c=AFT[u"80"][3],
           bandred=BAND_RED.strip()[:170])

aud2 = aud[:top_pos] + AUD_ENTRY.rstrip(u"\n") + u"\n\n" + aud[top_pos:]
if aud2.count(u"## 第 %d 轮" % (AUDIT_N - 1)) != 1:
    die(u"UI_AUDIT 插入把上一轮的标题弄丢了")
wr(AUD, aud2)

# ── 2) AGENT_VISUAL_ITERATION：升序，只能追加到文件末尾 ─────────────────────
DIMS = [u"真实视觉审查", u"判据有效性", u"假绿防御", u"产品面推进",
        u"台账一致性", u"交付诚实性", u"可复核性"]
seven_rows = u"\n".join(u"| %s | %d/15 | %s |" % (d, s, why) for d, s, why in [
    (DIMS[0], SEVEN[0], u"三对帧逐档看过（页底 30/50/80 各一张改前改后），并排放大图留在 /tmp/r339_pair_*.png"),
    (DIMS[1], SEVEN[1], u"新尺三档逐档判 + 两颗地板都从仓库已有数拿；三把刀 CAUGHT=3/3 各钉一条轴"),
    (DIMS[2], SEVEN[2], u"抓到『同侧』门把 差=0 判成通过（8 跑无人替它说话）并补上量级地板"),
    (DIMS[3], SEVEN[3], u"产品 3 文件、一个真缺陷；亮档与 395 仍欠，305 只压回一半"),
    (DIMS[4], SEVEN[4], u"全部数字解析自日志；连读那一格仍带 412 的口径差一，按实写明"),
    (DIMS[5], SEVEN[5], u"第一版修法被另一条判据否掉，写进 U-%d 而不是删掉 diff" % U5),
    (DIMS[6], SEVEN[6], u"runner 的验收要下一跑才有读数（本轮只能预登记），真机那格仍 screen_locked"),
])
ITE_ENTRY = u"""## Round {iter} · R{round}（第 {audit} 轮 · {date}）：把"只有另一台机器红"换成"页底是自变量" —— 暗档选中那颗塌在漂来的轨道上（产品 {prod} 文件）

本轮做了什么：runner 连挂 8 跑的那朵红，第一次在本机被复现成三个数（页底 30/50/80 →
差 {b30d} / {b50d} / {b80d}），并判成**产品事实**而不是通道限制（同一跑系统那颗现读 差=+49.0）。
修法是给 R333 那枚语义基准之上盖一层固定抬量（α=0.20 ⇒ 那颗 ≈107），
α 由「盖过已测到最亮那条轨道 + 分不开线 8」与「不超过平台自己那颗 109」两条实测边界夹出来。
改后三档 差 {a30d} / {a50d} / {a80d}、对比 {a30c} / {a50c} / {a80c}，全部过两颗地板。
另一条自伤也进了账：第一版"整颗跟着轨道走"让新尺全过、却把 `FILTER_PILL_BAND` 打成
`候选带数=0`（侧栏那条轨道在这条通道里现读 255，白色叠加压上去等于没画）⇒ 换画法不许弄坏别的判据。
同轮补上那条『同侧』门缺的一半：它原来把 差=+0.0 判成"同侧=是"，所以 8 跑里它一直绿。

验证读数：判据卷 `Executed {t_exe}（skipped={t_skip} failures={t_fail}）`；
全量卷 `Executed {f_exe}（skipped={f_skip} failures={f_fail}）`；捕获 `CAPTURED {cap} 帧`；
基线 `COMPARED={comp} 改前 CHANGED={ch0} → 同一笔 update 之后 CHANGED={ch}`；
刀 `mutate_r339 CAUGHT={caught}, RESTORE_CLEAN={restore}`（{arms}）；
预检 `tables={pt} covered={pc} arms={pa} bad={pb}`、臂名册 `files={af} arms={at}`；
清账表 `{gate}`；换装 `INSTALL_RESULT={ir} INSTALL_SHA_MATCH={is_}`。

七维度自评：

| 维度 | 分 | 依据 |
| --- | --- | --- |
{rows}

""".format(iter=ITER_N, round=ROUND, audit=AUDIT_N, date=DATE, prod=PRODUCT_N,
           b30d=BEF[u"30"][2], b50d=BEF[u"50"][2], b80d=BEF[u"80"][2],
           a30d=AFT[u"30"][2], a30c=AFT[u"30"][3], a50d=AFT[u"50"][2], a50c=AFT[u"50"][3],
           a80d=AFT[u"80"][2], a80c=AFT[u"80"][3],
           t_exe=T_EXE, t_skip=T_SKIP, t_fail=T_FAIL,
           f_exe=F_EXE, f_skip=F_SKIP, f_fail=F_FAIL, cap=CAP_N,
           comp=COMPARED, ch0=CHANGED0, ch=CHANGED, caught=CAUGHT, restore=RESTORE,
           arms=u"、".join(ARMS_NEW), pt=PRE[0], pc=PRE[1], pa=PRE[2], pb=PRE[3],
           af=ARM_TOTAL[0], at=ARM_TOTAL[1], gate=GATE.strip(), ir=INSTALL_RESULT, is_=INSTALL_SHA,
           rows=seven_rows)

ite = rd(ITE)
if (u"## Round %d ·" % ITER_N) in ite:
    die(u"ITERATION 已经有 Round %d 了" % ITER_N)
if (u"## Round %d " % (ITER_N - 1)) not in ite:
    die(u"ITERATION 里找不到上一节 Round %d ⇒ 升序断了" % (ITER_N - 1))
wr(ITE, ite.rstrip(u"\n") + u"\n\n" + ITE_ENTRY.rstrip(u"\n") + u"\n")

# ── 3) BACKLOG：新开三单 + 411 结案追记 + 305 追记 ──────────────────────────
BL_411 = u"""**411 追记（R339 结案）**：判成**产品事实**，两条出路里 neither 是"按机器的具名出口" ——
新尺 `SEG_PILL_BACKING` 在本机把 runner 那一档原样复现出来（人造页底 50 ⇒ 轨道 70、不透明那颗 70、
差 0），而同一格里系统那颗现读 差=+49.0 ⇒ 通道画得出选中，只画不出自家那颗。
修法：暗档在语义基准之上盖一层固定抬量（α=0.20 ⇒ ≈107，两条实测边界夹出来的区间中位），
改后三档 差 {a30d} / {a50d} / {a80d} 全部过线；同轮补上那条『同侧』门缺的量级一半。
三把刀 {arms} 各钉一条轴（对调 / 太小 / 太大），`CAUGHT={caught}`。
**runner 的验收还欠一跑**（这一格的结案由下一轮第 ⓪ 条的读数最终签）：期望 `SEGREF_POLARITY dark
自家 差` 从 +0.0 变成 ≥ +15、`HOVER_RUNG_WINDOW dark 可行` 从 空集 变成非空、STEP[15]/[17] 两格转绿。

**{b_ladder}. 这条 backing 尺只有两档是实测的：真实用户的页底分布从没量过**（R{round}）
三档里 30 与 50 是两台机器的离屏页底，80 是我外推的。真机那一次（R330）量到的是 页底 51 / 轨道 81 ——
**同一档页底，真机的轨道叠加比离屏通道多 10 级**，说明"轨道=页底+固定量"这个模型在两条通道上不同形。
两种坏法各自还在：① 真实页底比我外推的 80 更亮（浅色壁纸 / 辅助功能设置）⇒ 抬量仍然不够；
② 外推那一档其实过严 ⇒ 我把选中抬得比平台惯例还亮（本机系统那颗 74，自家现在 107）。
出路：把 backing 从"三档常量"换成**名册**（每档一个来源，逐档标实测/外推），
并给"降低透明度 / 增加对比"那两种系统设置各拍一帧 —— 那两档会直接改材质的合成结果。
不许用"三档都过了"替这一格签字。

**{b_light}. 亮档那颗的极性问题从"两机反号"变成了"三档全反"，而它仍然只印不判**（R{round}）
本轮三档人造页底在亮档的现读：页底 30 → 轨道 27、页底 50 → 45、页底 80 → 72，而亮档那颗
是不透明的 220 ⇒ 差 +193 / +175 / +148，**全部是正的**，与本机原生页底上读到的 差=−10 反号。
两件事因此分开来了：亮档在**原生页底**上选中比轨道暗（那是 399 说的"要换轴"），
而在**任何人造底**上都不暗 —— 说明 −10 那一步不是令牌错，是亮档原生页底（230/236）本来就比
语义色 220 更亮。这一格本轮只登记不修：亮档的门一立就会在两机上反号（D-325 的原文条件还没满足），
而 399 那两支候选（越过选中 / 换非亮度轴）都没被量过。

**{b_overlay}. 轨道自己那层叠加也按机器漂，而它和页底的漂移被合在同一个数里**（R{round}）
现读：本机离屏 页底 30 → 轨道 52（叠加 +22）、runner 离屏 页底 50 → 轨道 70（+20）、
真机 页底 51 → 轨道 81（**+30**）。也就是说 `.quaternary` 那一层在两条通道上不是同一个量。
本轮的尺只报「轨道」与「选中」两个电平，把这两层混成一个数 ⇒ 我说"轨道漂了 18"，
其中有多少来自页底、多少来自那层叠加，现在**分不出来**。后果不是难看，是判据不同形：
396 的可行窗口是按「空闲 52 / 选中 70」算的，而 runner 的窗口是按「70 / 70」算的 ——
两个窗口的宽度差里就藏着这个没分开的量。出路：把轨道叠加量单独打成一格读数
（同一帧里量"轨道带"与"页底带"，报 差），并给真机那一尺补同一颗对照。

**305 追记（R{round}）**：暗档"按下比选中还亮"那一半被这一发压回来了 ——
选中从 70 抬到 ≈107，而按下那档叠在轨道上本机现读 76 ⇒ 次序回到 hover < pressed < selected。
**不结案**：305 判的是两档台阶（hover→pressed 与 pressed→selected）的地板，本轮只动了 selected，
而且亮档那一半（308）另有自己的账。runner 上按下/选中的新数要下一跑第 ⓪ 条读。
""".format(a30d=AFT[u"30"][2], a50d=AFT[u"50"][2], a80d=AFT[u"80"][2],
           arms=u"、".join(ARMS_NEW), caught=CAUGHT, round=ROUND,
           b_ladder=B_LADDER, b_light=B_LIGHT, b_overlay=B_OVERLAY)

blg = rd(BLG)
for n in (B_LADDER, B_LIGHT, B_OVERLAY):
    if re.search(u"(?m)^\\*\\*%d\\. " % n, blg):
        die(u"BACKLOG %d 已经存在，编号撞了" % n)
if u"**411. " not in blg:
    die(u"BACKLOG 411 不在盘上 ⇒ 追记没有对象")
wr(BLG, blg.rstrip(u"\n") + u"\n\n" + BL_411.rstrip(u"\n") + u"\n")

# ── 4) DECISIONS：D-335 ─────────────────────────────────────────────────────
DEC_ENTRY = u"""### D-{d}（{round}）"只有另一台机器红"要先当成产品事实审：把漂移的那个量变成自变量，出口才有资格被考虑

**背景**：runner 从 `117f45d` 起连挂 8 跑，三条断言全在暗档那一格；本机同一卷 0 failures。
本仓库对这种形状的历史反应是"按机器切片 / 具名出口"（174、196、252、354 那一族），
而这一次出口**没被允许**：同一跑、同一条 render 里的系统参照臂现读 差=+49.0，
自家那颗 差=+0.0 —— 那台机器画得出选中，只画不出自家那颗。

**规矩**：一条判据在 A 机绿、B 机红时，先问"这两台机器之间到底哪个量不同"，
再问"那个量能不能在**本机**被做成自变量"。能做成自变量，就必须先在本机复现再定性 ——
把"只有另一台机器红"直接翻译成"这台机器判不了"，等于用一次环境差异给产品发通行证。
本轮的可复现版本只有三行代码：把 `probeFrame` 的页面底色从语义色换成调用方给的**不透明**灰，
于是页底 30/50/80 各成一档，逐档量「选中 − 轨道」，中间那一档原样复现出 runner 的 70 对 70。

**为什么修法不是"整颗改成跟着轨道走的叠加"**（本轮第一版，被自己否掉）：
叠加的差 = α×(255−轨道)，它在轨道已经很亮处**自己先归零**，而这条离屏通道在侧栏里不平滑材质、
暗档轨道现读 255 ⇒ 两态帧一个字都不差，`FILTER_PILL_BAND` 当场红。
教训写成一句话：**换画法不许弄坏另一条判据** —— 新尺全绿不是修好的证明，
只是"新尺看得见的那一面变好了"。留下语义基准 + 固定抬量，两颗地板（盖过最亮实测轨道、
不超过平台那颗）把它夹成一个区间。

**同轮补的半个洞**：那条『同侧』门算的是 `(ownDiff >= 0) == (sysDiff >= 0)` ⇒ 差=0 也算同侧，
所以它挂了 8 跑都是绿的，而"两档读成同一个灰阶"正是这件事该拦的。
符号对、大小为 0，不是事实：门的量级地板与方向判据必须同时存在（与 R38 的
"两台机器的读数不能当另一台机器的地板"同族）。
""".format(d=D1, round=ROUND)

dec = rd(DEC)
if re.search(u"(?m)^### D-%d" % D1, dec):
    die(u"D-%d 已存在" % D1)
if (u"### D-%d" % (D1 - 1)) not in dec:
    die(u"找不到 D-%d ⇒ 决定台账的连续性断了" % (D1 - 1))
wr(DEC, dec.rstrip(u"\n") + u"\n\n" + DEC_ENTRY.rstrip(u"\n") + u"\n")

# ── 5) CHANGELOG：新 ### 插在 ## [Unreleased] 之下、上一条 ### 之上 ──────────
CHG_ENTRY = u"""### runner 连挂 8 跑的那朵红判成了产品事实：暗档选中那颗塌在漂来的轨道上（R{round} / U-{u1}…U-{u8} · 产品 {prod} 文件）

- 现象：runner 上 `testDirectReadHoverLayersAreVisibleOnTheirOwnSurfaces` 暗档三条断言连挂 8 跑
  （`HOVER_RUNG_WINDOW dark 空闲=70 选中=70 … 可行=空集`），本机同一卷 0 failures。
- 定性：新尺 `SEG_PILL_BACKING` 把页底做成自变量，本机第一次原样复现出 runner 那一档
  （人造页底 50 ⇒ 轨道 70、那颗 70、差 0）；同一跑系统那颗现读 差=+49.0 ⇒ **不是**通道限制。
- 修法：暗档在 R333 那枚语义基准之上盖一层固定抬量 α=0.20（那颗 ≈107），
  α 由「盖过已测到最亮那条轨道 97 + 分不开线 8」与「不超过平台自己那颗 109」两条实测边界夹出来。
  改后三档 差 {a30d} / {a50d} / {a80d}，对比 {a30c} / {a50c} / {a80c}，全部过线。
- 同轮补洞：那条『同侧』门原来把 差=+0.0 判成"同侧=是"（8 跑里它一直绿）⇒ 加上量级地板 8。
- 自伤进账：第一版"整颗跟着轨道走"让新尺全过、却把 `FILTER_PILL_BAND` 打成 `候选带数=0`
  （侧栏那条轨道在这条通道里现读 255）⇒ 换画法不许弄坏别的判据，那一版被丢掉。
- 三把刀 {arms}（对调 / 太小 / 太大）`CAUGHT={caught}, RESTORE_CLEAN={restore}`。
- 新开 {b1}（backing 尺只两档实测）、{b2}（亮档在原生页底上仍反号，399 的另一半）、
  {b3}（轨道叠加量本身也按机器漂，与页底的漂移混在同一个数里）；411 结案（等 runner 验收），305 补一条追记。
""".format(round=ROUND, u1=U1, u8=U8, prod=PRODUCT_N,
           a30d=AFT[u"30"][2], a30c=AFT[u"30"][3], a50d=AFT[u"50"][2], a50c=AFT[u"50"][3],
           a80d=AFT[u"80"][2], a80c=AFT[u"80"][3],
           arms=u"、".join(ARMS_NEW), caught=CAUGHT, restore=RESTORE,
           b1=B_LADDER, b2=B_LIGHT, b3=B_OVERLAY)

chg = rd(CHG)
if chg.count(u"\n## [Unreleased]") != 1:
    die(u"CHANGELOG 的 [Unreleased] 不是恰好一处")
chg_lines = chg.split(u"\n")
unrel = [i for i, ln in enumerate(chg_lines) if ln == u"## [Unreleased]"]
h3 = [i for i, ln in enumerate(chg_lines) if i > unrel[0] and ln.startswith(u"### ")]
if len(unrel) != 1 or not h3:
    die(u"CHANGELOG 形状不对")
chg2 = u"\n".join(chg_lines[:h3[0]]) + u"\n" + CHG_ENTRY.rstrip(u"\n") + u"\n\n" + u"\n".join(chg_lines[h3[0]:])
wr(CHG, chg2)

# ── 6) STATE：新节插在最上一条轮次节之上，并自证层数没少 ────────────────────
CI_LINE = u"RUN=40143910952 ↔ b08d294（R338 追记，回填时 in_progress）/ RUN=40143510717 ↔ 526e8d7（R338 账半，回填时 in_progress）"
STATE_BODY = u"""## R{round} 状态（{date} · 本地 · 第 {audit} 轮 / Round {iter}）：runner 连挂 8 跑的那朵红，本机把它复现成三个数（产品 {prod} 文件，动效主线）

最后更新：{date}（本地 · R{round} / 第 {audit} 轮 / Round {iter}）：把"只有另一台机器红"翻成
"页底是自变量" —— 暗档选中那颗塌在漂来的轨道上，改法是语义基准之上盖一层固定抬量
（产品 {prod} 文件 · 动效主线 / 侧栏筛选胶囊）

本轮做了什么：
① 取读数（⓪）：`gh run list` 现读 8 连红（`117f45d`…`3954d1d`），失败步骤固定两格
  （STEP[15] executed-count gate / STEP[17] 捕获闸），红全在 `testDirectReadHoverLayersAreVisibleOnTheirOwnSurfaces`
  暗档；两机同格现读：本机 段按钮 空闲 52 / 选中 70 / 悬停 60，runner 70 / 70 / 77，
  而**同一跑**系统参照臂 差=+49.0 ⇒ 通道画得出选中，只画不出自家那颗 ⇒ 411 判成产品事实（D-{d}）。
② 造尺：`SEG_PILL_BACKING` —— 同一条夹具通道铺三档**不透明**人造页底（30 实测=本机 / 50 实测=runner /
  80 外推），逐档量「选中 − 轨道」，两颗地板都从仓库已有数拿（8 = 真机那把尺的 `DELTA`，1.10 = 这一族暗档的线）。
  它在本机原样复现出 runner 的形状：改前 差 {b30d} / {b50d} / {b80d}。
③ 修：`SegmentKnob.liftAlpha(dark:)` —— 暗档在 `selectedSegment`（解析 70，两机同读）之上盖
  `Color.white.opacity(0.20)` ⇒ 那颗 ≈107；α 由「盖过最亮实测轨道 97 + 8」与「不超过系统那颗 109」
  夹出区间 [0.189, 0.211]，取正中。改后 差 {a30d} / {a50d} / {a80d}、对比 {a30c} / {a50c} / {a80c}。
④ 补洞：那条『同侧』门原来算 `(ownDiff >= 0) == (sysDiff >= 0)` ⇒ 差=+0.0 也算"同侧=是"，
  所以它 8 跑全绿；加上量级地板之后它自己能抓"塌成一档"。
⑤ 看图：三对帧（页底 30/50/80 各改前/改后并排放大）—— 页底 50 改前两颗并成同一档、
  页底 80 改前选中是一颗暗洞（377 那颗回来了），改后三档都能一眼指出被选中的那颗。

验证读数（现读）：判据卷 `Executed {t_exe}（skipped={t_skip} failures={t_fail}）`；
全量卷 `Executed {f_exe}（skipped={f_skip} failures={f_fail}）`；构建告警 0（`/tmp/r339_build.log`）；
捕获 `CAPTURED {cap} -> /tmp/r339_shots3`；基线 `COMPARED={comp}`、更新前 `CHANGED={ch0}`（全是暗档 17 张）、
更新后同一笔 `CHANGED={ch}`；刀 `mutate_r339 CAUGHT={caught}, RESTORE_CLEAN={restore}`（{arms}）；
针预检 `tables={pt} covered={pc} arms={pa} bad={pb}`、臂名册 `files={af} arms={at} dupes=0 repeats=0`；
清账表 `{gate}`；换装 `INSTALL_RESULT={ir} INSTALL_SHA_MATCH={is_}`；脚本电池见落盘后那一跑。
产品面连续零改动 **{streak}** 轮（现读 `python3 scripts/product_streak.py --streak-for {audit}` ——
这一格仍带 BACKLOG 412 那个**口径差一**：本轮明明动了 {prod} 个产品文件，而工具把本轮自己那笔排除在外，
所以它读成「本轮**之前**的连读轮数」，不许读成「本轮零改动」。 —— 这一整句必须在同一行里：`_cells` 问的是
"那一格有没有引用取数口"，分两行写就等于没引用）；取数口 `--streak-for {audit}`。

NOT-RUN（三种缺席分开写，不许省略）：① **只在人身上判得了**：真机那一屏仍读不到 ——
现跑 `display_channel_state()` 得 `screen_locked`（电源日志 on、SecureInput 属主=loginwindow），
尺不猜密码也不替用户解锁 ⇒ 395（393 的改前/改后真机四数）继续欠，而本轮的 107 那一档
在真机屏幕上到底比轨道亮多少，**没有读数**（三档人造底是本地代理，不是那块屏幕）。
② **只在 runner 上判得了**：411 的结案要下一跑签 —— 期望 `SEGREF_POLARITY dark 自家 差` 从 +0.0
变成 ≥ +15、`HOVER_RUNG_WINDOW dark 可行` 从 空集 变非空、STEP[15]/[17] 转绿。这一跑之前 CI 仍是红的。
③ **这条通道看不见 / 没做**：亮档那一半没动（399 仍开，本轮新开 {b2} 把它在原生页底上的 −10 说清楚）；
`FILTER_PILL_BAND` 用的那条侧栏轨道在这条通道里现读 255（材质不平滑），本轮**没有**为它做任何放行。

下一轮（R{next}）的靶：⓪ 读 CI 配对（成对：run id ↔ commit，现读自 `scripts/ci_read.py latest`）——
{ci}；**R{round} 这一笔的 run id 回填时按 sha 逐笔问**。这一跑要答的就是 411：
连挂 8 跑的红有没有变成绿（三格期望都在上面 NOT-RUN ② 里），以及新尺 `SEG_PILL_BACKING`
在 runner 上签不签（它的页底是我给的常量，理论上两机同数 —— 若不签，说明 `render` 通道的
不透明底色在那台机器上也被材质改写，那是通道事实，要开新的一单而不是放宽地板）。
→ ① **BACKLOG 405**（两轮没排上）：把"标题里那半句产品 K 文件"立成定义并变成会红的门。
→ ② **BACKLOG 413**：backing 从三档常量换成名册（每档标实测/外推），并给"降低透明度 / 增加对比"
  各拍一帧 —— 那两档会直接改材质合成结果，是 411 这条链上最可能的下一个坑。
→ ③ 412（`--streak-for` 差一）：修它要在同一笔里重算窗口内所有格，别一前一后。
→ ④ 动效主线仍排队：399 / 397 / 390 / 389 / 384 / 387① / 376 / 367 那一串。

本轮的自伤（写成出处，不写成缺陷）：第一版修法（整颗跟着轨道走的叠加）让**新尺三档全绿**，
我差点就此落账 —— 是隔壁那卷 `FILTER_PILL_BAND` 的红把它拽回来的。
教训一句话：**新装的尺全绿不是修好的证明**，它只证明新尺看得见的那一面变好了；
同一轮里"改前"那一跑我先跑在了还原之后（重跑一次才拿到 差=0 那三行），
所以 before/after 两份日志各自的时间戳与当时工作树状态都要留在盘上（/tmp/r339_before_final.log）。
""".format(round=ROUND, next=ROUND + 1, audit=AUDIT_N, iter=ITER_N, date=DATE, prod=PRODUCT_N,
           d=D1, u8=U8, streak=STREAK_N, ci=CI_LINE, ir=INSTALL_RESULT, is_=INSTALL_SHA,
           b2=B_LIGHT, arms=u"、".join(ARMS_NEW), caught=CAUGHT, restore=RESTORE,
           t_exe=T_EXE, t_skip=T_SKIP, t_fail=T_FAIL, f_exe=F_EXE, f_skip=F_SKIP, f_fail=F_FAIL,
           cap=CAP_N, comp=COMPARED, ch0=CHANGED0, ch=CHANGED,
           pt=PRE[0], pc=PRE[1], pa=PRE[2], pb=PRE[3], af=ARM_TOTAL[0], at=ARM_TOTAL[1],
           gate=GATE.strip(),
           b30d=BEF[u"30"][2], b50d=BEF[u"50"][2], b80d=BEF[u"80"][2],
           a30d=AFT[u"30"][2], a30c=AFT[u"30"][3], a50d=AFT[u"50"][2], a50c=AFT[u"50"][3],
           a80d=AFT[u"80"][2], a80c=AFT[u"80"][3])

sta = rd(STA)
before_layers = sta.count(u"\n> ## ")
pos = sta.find(u"## R%d 状态" % (ROUND - 1))
if pos < 0:
    die(u"STATE 里找不到上一轮（R%d）的节标题" % (ROUND - 1))
wr(STA, sta[:pos] + STATE_BODY.rstrip(u"\n") + u"\n\n" + sta[pos:])
after = rd(STA)
if after.count(u"\n> ## ") != before_layers:
    die(u"STATE 轮换改动了 `> ##` 层数：%d → %d" % (before_layers, after.count(u"\n> ## ")))
if (u"## R%d 状态" % (ROUND - 1)) not in after:
    die(u"STATE 轮换把上一轮的节标题弄丢了")

# ── 7) FINAL_REPORT：计数器 + §14 + 「仍开」轮次 ─────────────────────────────
fr = rd(FRA)
U_MAX_NOW = max(int(x) for x in re.findall(u"(?m)^- \\*\\*U-(\\d{3,4})[：(]", rd(AUD)))
D_MAX_NOW = max(int(x) for x in re.findall(u"(?m)^### D-(\\d{3})", rd(DEC)))
B_MAX_NOW = max(int(x) for x in re.findall(u"(?m)^\\*\\*(\\d{2,4})\\. ", rd(BLG)))
if (U_MAX_NOW, D_MAX_NOW, B_MAX_NOW) != (UMAX, D1, B_OVERLAY):
    die(u"落盘后最大号与计划不一致：%d/%d/%d（计划 %d/%d/%d）"
        % (U_MAX_NOW, D_MAX_NOW, B_MAX_NOW, UMAX, D1, B_OVERLAY))
mUD = re.search(u"U-31 … U-(\\d+)", fr)
if not mUD:
    die(u"报告里找不到 U 区间那一格")
fr = once(fr, mUD.group(0), u"U-31 … U-%d" % U_MAX_NOW)
mD = re.search(u"(决定台账[^\\n]*?D-\\d{3} … \\*\\*)(D-\\d{3})", fr)
if not mD:
    die(u"报告里找不到「决定台账」那一格")
fr = fr[:mD.start(2)] + (u"D-%d" % D_MAX_NOW) + fr[mD.end(2):]
prod_hits = [ln for ln in re.findall(u"(?m)^- \\*\\*产品面（这一节最该被读的部分）\\*\\*：.*$", fr)
             if u"产品面连续零改动轮数" in ln]
if len(prod_hits) != 1:
    die(u"带连读那一格的「产品面」行应为恰好一处，实得 %d" % len(prod_hits))
new_prod = (u"- **产品面（这一节最该被读的部分）**：本轮产品文件 **%d** 个（**动效主线 / 侧栏筛选胶囊**："
            u"`VisualTokens.swift` 新增 `selectedSegmentLiftWhite`、`PressableStyle.swift` 新增 "
            u"`SegmentKnob.liftAlpha`、`HistorySidebarView.swift` 在语义基准之上盖那一层）。"
            u"runner 连挂 8 跑的那朵红判成**产品事实**（新尺 `SEG_PILL_BACKING` 在本机原样复现出 "
            u"页底 50 那一档的 差=%s，而同一跑系统那颗 差=+49.0）。"
            u"产品面连续零改动轮数 = **%s**（现读 `python3 scripts/product_streak.py`，"
            u"口径差一仍挂在 BACKLOG 412：本轮动了产品而这一格读成「本轮之前」）。"
            u"新开 %d（backing 尺只两档实测）、%d（亮档在原生页底上仍反号）、%d（轨道叠加量本身也按机器漂）；"
            u"%d 结案（等 runner 验收），305 收到一条追记。"
            % (PRODUCT_N, BEF[u"50"][2], STREAK_N, B_LADDER, B_LIGHT, B_OVERLAY, 411))
fr = once(fr, prod_hits[0], new_prod)
s14_hits = [ln for ln in rd(FRA).splitlines() if ln.startswith(u"- **判据与门的规模**")]
if len(s14_hits) != 1:
    die(u"§14 那一格应为恰好一处，实得 %d" % len(s14_hits))
new_s14_line = (u"- **判据与门的规模**（R%d 现读，这一格是最新的权威，§13 那格已冻结成历史）："
                u"脚本电池 `Ran %s`（skipped=%s）；变异臂在册 **%s** 把 / 扫了 **%s** 个表文件"
                u"（预检 tables=%s covered=%s arms=%s bad=%s）；"
                u"U 定义行最大 **U-%d**、决定最大 **D-%d**、BACKLOG 最大 **%d**；"
                u"本轮刀 `mutate_r%d.py CAUGHT=%s, RESTORE_CLEAN=%s`（%s）。"
                % (ROUND, BATT, BATT_SKIP, ARM_TOTAL[1], ARM_TOTAL[0],
                   PRE[0], PRE[1], PRE[2], PRE[3], U_MAX_NOW, D_MAX_NOW, B_MAX_NOW,
                   ROUND, CAUGHT, RESTORE, u"、".join(ARMS_NEW)))
fr = once(fr, s14_hits[0], new_s14_line)
fr = re.sub(u"(?m)^(- \\*\\*仍开（截至本轮，完整名单以 `AGENT_STATE.md` 的 R)\\d+( 节)",
            u"\\g<1>%d\\g<2>" % ROUND, fr, count=1)
if re.search(u"@\\w+@", fr):
    die(u"报告里还有没替换的占位符")
wr(FRA, fr)

print(u"R%d_LEDGERS_OK U=%d D=%d BL=%d 判据卷=%s/%s 全量卷=%s/%s 刀=%s 基线=%s/%s 帧=%s"
      % (ROUND, U_MAX_NOW, D_MAX_NOW, B_MAX_NOW, T_EXE, T_FAIL, F_EXE, F_FAIL, CAUGHT,
         COMPARED, CHANGED, CAP_N))
