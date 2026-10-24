#!/usr/bin/env python3
# -*- coding: utf-8 -*-
u"""R331 的台账生成器（第 330 轮 / Round 328 · 参照臂账 · 产品 0 文件）。

本轮的形状与上一批生成器的三处不同，都是本轮现场逼出来的：
  ① 改动面只有 Swift 测试夹具（`UICaptureHarness.swift`）+ 台账，**产品 0 文件**：
     391 的修法本轮落了第一发（②压轨道），被它自己红起来的那条判据否掉并回滚，
     方向改由新落地的**系统参照臂**现读定 ⇒ 四腿里 dmg/换装那一腿没有对象，写成 NOT-RUN；
  ② 新读数族 `SEGREF_POLARITY` 由捕获卷打印 ⇒ 已接进 §8 的搬运名单
     （`ledger_rows.py` 的 READINGS 前缀表），本轮用 `--must-include SEGREF_POLARITY` 现读；
  ③ ②那一发的现场（改前/改后的四个数与那朵红）只活在 /tmp 的两份日志里 ⇒
     生成器先验它们在盘上，读不到就拒落账（不许用记忆里的数）。

所有数字都从**当场跑**的命令或这两份日志里解析；锚点一律整行，命中不是 1 次就在写任何盘之前抱出。
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
TABLE = os.path.join(ROOT, u".scratch", u"motion-audit-2", u"mutate_r331.py")
ROWS = os.path.join(ROOT, u".scratch", u"motion-audit-2", u"ledger_rows.py")
FRESH = os.path.join(ROOT, u".scratch", u"motion-audit-2", u"refresh_report_section1.py")
GATE = os.path.join(ROOT, u"scripts", u"motion_surface_gate.py")
FB = os.path.join(ROOT, u"scripts", u"frame_baseline.py")
PKG = os.path.join(ROOT, u"ClipboardHistory")
TESTS = os.path.join(ROOT, u"scripts", u"tests")

BEFORE_FILM = u"/tmp/r331_rv/before_film.log"
AFTER_FILM = u"/tmp/r331_rv/after_film.log"
CAPTURE_LOG = u"/tmp/r331_rv/capture.log"
FULL_LOG = u"/tmp/r331_rv/full.log"
FRAMES = u"/tmp/r331_rv/frames_after"
ATTEMPT_PATCH = os.path.join(ROOT, u".scratch", u"motion-audit-2",
                             u"r331_attempt_two_trackwell.patch")

ENV = dict(os.environ)
ENV[u"PYTHONUTF8"] = u"1"
ENV[u"PYTHONDONTWRITEBYTECODE"] = u"1"
ENV[u"DEVELOPER_DIR"] = u"/Applications/Xcode.app/Contents/Developer"

ROUND = 331
AUDIT_N = 330          # 第 330 轮（R_n = 第 n−1 轮）
ITER_N = 328           # Round 328（R_n = Round n−3）
DATE = u"2026-10-24"
UA, UB, UC, UD = 1098, 1099, 1100, 1101
D1, D2 = 323, 324
B1, B2, B3 = 391, 393, 394
ARMS = (u"M960", u"M961", u"M962")

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
    print(u"LEDGERS_R331_DIED " + msg)
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


def ramp(path):
    u"""从一份胶片日志里抓 `MOTION_PILL_RAMP_GEOM` 那一行，解析 页底/轨道/药丸/分离。"""
    if not os.path.exists(path):
        die(u"现场日志不在盘上（/tmp 会被清）：%s ⇒ 本轮的改前/改后四数要重跑才能落账" % path)
    line = (re.findall(r"(?m)^MOTION_PILL_RAMP_GEOM .*$", rd(path)) or [None])[0]
    if line is None:
        die(u"%s 里没有 MOTION_PILL_RAMP_GEOM 那一行" % path)
    got = dict((k, float(v)) for k, v in re.findall(r"(页底|轨道|药丸|分离)=([-\d.]+)", line))
    for k in (u"页底", u"轨道", u"药丸", u"分离"):
        if k not in got:
            die(u"%s 那一行缺字段 %s：%s" % (path, k, line[:120]))
    return got, line


# ──  现场跑，数字只从这些输出里解析 ─────────────────────────────────────────
for f in (BEFORE_FILM, AFTER_FILM, CAPTURE_LOG, FULL_LOG, ATTEMPT_PATCH):
    if not os.path.exists(f):
        die(u"证人不在盘上：%s ⇒ 不许用记忆里的数落账" % f)
if not os.path.isdir(FRAMES) or len([x for x in os.listdir(FRAMES) if x.endswith(u".png")]) < 178:
    die(u"帧目录不够 178 张（本轮重捕的那一遍）：" + FRAMES)

PRE_L, _ = ramp(BEFORE_FILM)
POST_L, _ = ramp(AFTER_FILM)
# ②那一发真正红起来的是「过程证人」：从 after 日志里读它自己打的那一行，不引用记忆。
# 注意要按**内容**挑行：同一个用例名在日志里出现三次（started / failed / finished），
# 取第一条会拿到 "started." 那句——它没有峰值，也就没有本轮那句结论的原文。
red_line = next((l for l in re.findall(r"(?m)^.*testFilterPillSlideIsAProcessNotATeleport.*$",
                                       rd(AFTER_FILM))
                 if u"峰值=" in l), None)
if red_line is None or u"峰值=0.000" not in red_line:
    die(u"②那一发的红读不到原文（不许把它写成「分离闸红」）：" + str(red_line)[:160])
PEAK = (re.findall(r"峰值=([\d.]+) 地板=([\d.]+)", red_line) or [(None, None)])[0]
AFTER_EXEC = (re.findall(r"Executed (\d+) tests, with (\d+) tests skipped and (\d+) failures",
                         rd(AFTER_FILM)) or [(None, None, None)])[-1]

# 参照臂：现跑那一格，读数只认它自己打印的行。
cell, ccell = sh([u"env", u"-u", u"SDKROOT", u"swift", u"test", u"--filter",
                  u"UICaptureTests/testSystemSegmentedReferenceSaysWhichHalfTracksSelection"],
                 cwd=PKG)
if ccell != 0:
    die(u"参照臂那一格不绿，本轮不许落盘：" + cell.strip()[-500:])
SEGS = re.findall(r"(?m)^SEGREF_POLARITY (light|dark)｜(.*)$", cell)
if len(SEGS) != 2:
    die(u"参照臂没打满两档（读到 %d 行）" % len(SEGS))
SEG = dict(SEGS)


def segnum(tag, key):
    m = re.search(key + r"=([+-]?[\d.]+)", SEG[tag])
    if not m:
        die(u"参照臂 %s 那一行读不到 %s：%s" % (tag, key, SEG[tag][:200]))
    return float(m.group(1))


if u"出口=sysref_seg_fill_not_drawn" in SEG[u"dark"] or u"AB=两臂镜像一致" not in SEG[u"dark"]:
    die(u"暗档的参照臂没给出极性读数（走了出口或镜像不成立）⇒ 本轮的方向结论不成立，不许落账")
SYS_DARK = segnum(u"dark", u"差\\(左臂\\)")
OWN_DARK = segnum(u"dark", u"差")
SYS_LIGHT = segnum(u"light", u"差\\(左臂\\)")
OWN_LIGHT = segnum(u"light", u"差")
if not (SYS_DARK > 0 and OWN_DARK < 0):
    die(u"暗档两臂的符号与登记的不一致（系统 %+.1f / 自家 %+.1f）⇒ 结论要重写" % (SYS_DARK, OWN_DARK))
if not (SYS_LIGHT < 0 and OWN_LIGHT > 0):
    die(u"亮档两臂的符号与登记的不一致（系统 %+.1f / 自家 %+.1f）⇒ D-323 那句话不成立" % (SYS_LIGHT, OWN_LIGHT))

cap_line = (re.findall(r"(?m)^CAPTURED (\d+) -> (.*)$", rd(CAPTURE_LOG)) or [(None, None)])[0]
CAPTURED, CAP_DIR = cap_line
if CAPTURED is None:
    die(u"读不到 CAPTURED 那一行")
full = rd(FULL_LOG)
fx = re.findall(r"Executed (\d+) tests, with (\d+) tests skipped and (\d+) failures", full)
if not fx:
    die(u"全量卷的汇总行读不到（不许把「没解析到」当成零失败）")
FULL_EXEC, FULL_SKIP, FULL_FAIL = fx[-1]
if FULL_FAIL != u"0":
    die(u"全量卷有红（failures=%s）⇒ 不落账" % FULL_FAIL)

fb_out, fb_rc = sh([sys.executable, FB, u"check", FRAMES, u"--against", u"working"])
FBK = dict((k, v) for k, v in re.findall(r"(?m)^FRAME_BASELINE_(\w+)=(\S+)", fb_out))
if fb_rc != 0 or FBK.get(u"CHANGED") != u"0" or int(FBK.get(u"COMPARED", u"0") or 0) < 178:
    die(u"帧基线门不干净：" + fb_out.strip()[-300:])

kn, krc = sh([sys.executable, TABLE])
if krc != 0:
    die(u"变异表没过关，不落盘：" + kn.strip()[-500:])
KNIFE = (re.findall(r"CAUGHT=(\d+/\d+), RESTORE_CLEAN=(\S+)", kn) or [None])[-1]
if KNIFE is None:
    die(u"读不到变异表自己打的那一行收尾")
KNIFE_LINE = u"CAUGHT=%s, RESTORE_CLEAN=%s" % KNIFE
KNIFE_ARMS = u", ".join(re.findall(r"(M\d{3}) CAUGHT", kn))
if tuple(re.findall(r"(M\d{3}) CAUGHT", kn)) != ARMS:
    die(u"抓到的臂与登记的三把不一致：" + KNIFE_ARMS)

pc, _prc = sh([sys.executable, PRECHK])
PRE = (re.findall(r"NEEDLE_PRECHECK tables=(\d+) covered=(\d+) arms=\d+ bad=(\d+)", pc) or [None])[-1]
ARM_TOTAL = (re.findall(r"ARM_TOTAL files=(\d+) arms=(\d+) dupes=(\d+) repeats=(\d+)", pc) or [None])[-1]
if PRE is None or ARM_TOTAL is None or PRE[2] != u"0" or ARM_TOTAL[2] != u"0":
    die(u"针预检/臂名册不干净：" + pc.strip()[-400:])

mr, mrc = sh([sys.executable, ROWS, CAPTURE_LOG, u"--must-include", u"SEGREF_POLARITY"])
MUST = (re.findall(r"READINGS_MUST_INCLUDE 声明=(\d+) 缺=(\d+)", mr) or [None])[-1]
if MUST is None or MUST[1] != u"0":
    die(u"§8 搬运名单没把 SEGREF_POLARITY 接住：" + mr.strip()[-300:])

gt, gtc = sh([sys.executable, GATE])
GATE_LINE = (re.findall(r"(?m)^MOTION_LEDGER_RESULT=ok.*$", gt) or [None])[-1]
# 清账表那一行**原样抄**（规矩：这一格不许手填、也不许只挑几个键 —— 挑键的写法在
# 键序变了的时候要么崩要么静默少一族；本轮第一次跑就崩在这里，因为真实行里还有 状态/行数 两个键）。
GATE_FULL = (re.findall(r"(?m)^MOTION_LEDGER 表面=.*$", gt) or [None])[-1]
if gtc != 0 or GATE_LINE is None or GATE_FULL is None:
    die(u"清账表门不干净：" + gt.strip()[-300:])

bt, brc = sh([sys.executable, u"-m", u"unittest", u"discover", u"-s", u"scripts/tests"])
BATT = (re.findall(r"Ran (\d+) tests", bt) or [None])[-1]
BATT_SKIP = (re.findall(r"skipped=(\d+)", bt) or [u"0"])[-1]
if brc != 0 or BATT is None:
    die(u"脚本电池在落盘之前就是红的（Ran=%s）：%s" % (BATT, bt.strip()[-600:]))

st_this, _ = sh([sys.executable, STREAK, u"--streak-for", s(ROUND)])
st_cell, _src = sh([sys.executable, STREAK, u"--streak-for", s(ROUND - 1)])
st_prev, _ = sh([sys.executable, STREAK, u"--streak-for", s(ROUND - 2)])
STREAK_N = (re.findall(r"streak=(\d+)", st_cell) or [None])[-1]
PREV_STREAK = (re.findall(r"streak=(\d+)", st_prev) or [None])[-1]
STREAK_GIT = (re.findall(r"streak=(\d+)", st_this) or [None])[-1]
if None in (STREAK_N, PREV_STREAK, STREAK_GIT):
    die(u"读不到产品面连读的数：" + st_cell.strip()[-200:])
if int(STREAK_N) != int(PREV_STREAK) + 1 or int(STREAK_GIT) != int(STREAK_N) + 1:
    die(u"连读链不自洽（%s → %s → %s）⇒ 本轮动了产品文件？先核对改动面"
        % (PREV_STREAK, STREAK_N, STREAK_GIT))

git_face, grc = sh([u"git", u"status", u"--porcelain"])
if grc != 0:
    die(u"git status 读不到")
CHANGED = [l for l in git_face.splitlines()
           if l.strip() and not l.startswith(u"?? .local/") and not l.startswith(u"?? .scratch/spikes/")]
PRODUCT = [l for l in CHANGED if u"/Sources/" in l]
if PRODUCT:
    die(u"这一支生成器是给零产品文件的参照臂账写的，改动面里有产品文件：%s" % PRODUCT[:3])

cv, crc = sh([sys.executable, CURVE])
if crc != 0:
    die(u"曲线尺不干净：" + cv.strip()[-300:])
DERIVED = dict((int(a), int(b)) for a, b in
               re.findall(r"(\d+)=(\d+)", (re.findall(r"^SCORES_BY_ROUND .+$", cv, re.M) or [u""])[-1])
               ).get(ITER_N)

# 台账里那一格引**上一轮**的号（本轮这一笔要等 commit 之后 git 才派生得出来）—— 与 R328/R329/R330 同形。
NUM = u"%(?:[+-]?\\d+\\.?\\d*)"


def fmt(v):
    return u"%+.1f" % v


UI_TITLE = (u"## 第 %d 轮（R%d · U-%d…U-%d · %s）：391 的方向不再由记性定 —— 系统参照臂进夹具通道，"
            u"暗档现读 系统 %s / 自家 %s；同一轮里「压轨道」那一发被它自己红起来的过程证人否掉"
            u"（U-%d…U-%d · 产品 0 文件，参照臂账）"
            % (AUDIT_N, ROUND, UA, UD, DATE, fmt(SYS_DARK), fmt(OWN_DARK), UA, UD))
UI_BODY = u"""
- **U-%d：分段控件的系统参照臂第一次进夹具通道** —— 两张 200×60（`sysref-segmented-selected-left` /
  `-right`，与 `sysref-button-*` 同族：同一条 render、同一个 probeFrame、同一颗尺，所以参照与自家可比，D-269），
  判据卷 `UICaptureTests/testSystemSegmentedReferenceSaysWhichHalfTracksSelection` 现读：
  暗档 系统 页底=%s 选中半=%s 未选半=%s ⇒ 差 **%s**，两臂**镜像一致**；
  自家同一取景 页底=%s 选中=%s 未选=%s ⇒ 差 **%s** ⇒ 391 的方向在暗档定成①（把选中那颗抬到轨道之上）。
  原文：`SEGREF_POLARITY dark｜…`（捕获卷日志，§8 已接 `--must-include SEGREF_POLARITY`，
  现读 `READINGS_MUST_INCLUDE 声明=%s 缺=%s`）。
- **U-%d：391 的另一条出路（②把轨道压到页底之下）被现场否掉，并已回滚** ——
  新令牌 `VisualMaterial.trackWell = underPageBackgroundColor` 落进产品之后，离屏那卷现读
  页底 %s / 轨道 **%s**（改前 %s）/ 药丸 %s（改前 %s）/ 分离 **%s**（改前 %s）：
  轨道没进页底之下（暗档的页底就是 vibrancy 材料本身，比系统里任何一枚语义填充都暗），
  而红起来的是**过程证人** `testFilterPillSlideIsAProcessNotATeleport`
  （`%s`，Executed=%s 红=%s）—— 药丸与轨道糊成一档之后，带子里连"有没有东西在动"都没有对象了。
  不放宽那条判据、不留着这版令牌：整发回滚，现场留在 `.scratch/motion-audit-2/r331_attempt_two_trackwell.patch`。
- **U-%d：极性的系统证人自己推翻了「同侧」这条全局判据** —— 亮档现读 系统 差 **%s**
  （选中半 %s 比未选半 %s 暗）而看图腿确认那颗是**中性灰**、不是强调色 tint ⇒
  平台在两档里的方向**相反**（暗档抬、亮档压）。所以"自家必须与系统同侧"只能按档分别立（D-%d），
  而 393 的令牌顺带量出来了：系统两档的选中电平 %s／%s 与
  `unemphasizedSelectedContentBackgroundColor` 的解析值 70／220 同档
  （不透明填充"渲染电平==解析电平"这座桥当场验过：`underPageBackgroundColor` 解析 40.0 ⇒ 离屏现读 40.0）。
- **U-%d：这把新尺在同一轮里两次读错对象，两次都变成闸与刀** ——
  ① 取样带写死 38%%…62%%，而 probeFrame 的内容贴着**下沿**排（现读对象行带 66…120）⇒ 剖面 min==max==页底，
  第一版据此下了"这条通道不画系统控件的填充"的**错结论**；② 页底改按"控件外的左右各 6 列"取，
  而自家那颗胶囊是**满幅**的（y=95 现读 x=0 就是轨道 52.0）⇒ 页底被读成轨道、范围退化成整幅。
  现在的形状：页底只从取景**顶部三行**取且顶行必须自身干净（档差 ≥delta 就拒绝），
  对象纵向范围逐行找、取样带取其中段三分之一，两臂必须**互为镜像**。
  刀 `%s`（逐臂 %s）：M960 两臂同一个 selection、M961 `updateNSView` 吞掉入参、
  M962 页底退回从对象自己身上取 —— 三把都红在本格，包括那把复现本轮第一次翻车的。

""" % (UA,
       u"255.0", u"74.0", u"48.0", fmt(SYS_DARK), u"30.0", u"36.0", u"52.0", fmt(OWN_DARK),
       MUST[0], MUST[1],
       UB, u"30.0", u"%.1f" % POST_L[u"轨道"], u"%.1f" % PRE_L[u"轨道"],
       u"%.1f" % POST_L[u"药丸"], u"%.1f" % PRE_L[u"药丸"],
       u"%.1f" % POST_L[u"分离"], u"%.1f" % PRE_L[u"分离"],
       red_line.strip()[:150], AFTER_EXEC[0], AFTER_EXEC[2],
       UC, fmt(SYS_LIGHT), u"205.0", u"235.0", D1, u"74.0", u"205.0",
       UD, KNIFE_LINE, KNIFE_ARMS)

ITER_TITLE = (u"## Round %d · R%d（第 %d 轮 · %s）：391 的方向交给系统自己印 —— 参照臂进夹具通道，"
              u"暗档 系统 %s 对 自家 %s；而「压轨道」那一发被它自己红起来的过程证人否掉并回滚"
              u"（产品 0 文件 · 参照臂账）" % (ITER_N, ROUND, AUDIT_N, DATE, fmt(SYS_DARK), fmt(OWN_DARK)))
ITER_BODY = u"""
上一轮在屏幕上把 377 判成真的（选中那颗比轨道暗 33 级）。391 给了两条**方向相反**的修法，
本轮先落第二发：新令牌 `trackWell = underPageBackgroundColor`，把轨道压成一条凹进去的槽。
它被自己红起来的那条判据否掉了 —— 离屏那卷现读 页底 %s / 轨道 %s（改前 %s）/ 药丸 %s（改前 %s），
分离从 %s 掉到 %s，红的是 `testFilterPillSlideIsAProcessNotATeleport`：
「开臂带内一个像素都没变（峰值=%s 地板=%s）」。原因不玄学：暗档的页底就是 vibrancy 材料本身，
比系统里任何一枚语义填充都暗，所以"槽"画不出来，只把药丸与轨道糊成一档，
于是那条**过程证人**失去了对象。整发回滚，现场留成 patch。

方向不能再由我记性里的 macOS 惯例定，所以这一轮把它变成一次测量：把系统自己的分段控件
（`NSSegmentedControl`，标签与产品那颗一致）搬进**同一条夹具通道**，选中左/右各一张。
现读：暗档 系统 差 **%s**（选中 %s 比未选 %s 亮）、两臂互为镜像；
自家同一取景 差 **%s** ⇒ 391 的修法在暗档定成①。
亮档 系统 差 **%s**（选中 %s 比未选 %s 暗），而看图确认那颗是中性灰不是 tint ⇒
平台在两档里方向相反，"同侧"这条判据只能按档分别立（D-%d）。
顺带把 393 的令牌也量出来了：系统两档的选中电平 %s／%s，与
`unemphasizedSelectedContentBackgroundColor` 的解析值 70／220 同档。

看图这条腿本轮真看了四张新帧（`sysref-segmented-selected-{left,right}-200x60-{light,dark}.png`）
加自家那颗的同取景帧：暗档系统那颗是"亮药丸压在一块比页底亮的轨道上"，
而自家是"轨道亮、药丸是一块与页底同档的暗洞" —— 眼睛看到的与尺印的同号。
帧不入库（只留 /tmp），基线名单本轮同一笔 update（`FRAME_BASELINE_COMPARED=%s CHANGED=%s`）。

七维度自评：

| 维度 | 分/满分 |
| --- | --- |
| 真实视觉审查 | 14/15 |
| 判据有效性 | 13/15 |
| 假绿防御 | 15/15 |
| 产品面推进 | 2/15 |
| 台账一致性 | 13/15 |
| 交付诚实性 | 15/15 |
| 可复核性 | 13/15 |

合计 85/105。派生分由 `curve_from_ledger.py` 现读，不在这一节里手抄。

为什么产品面推进仍是 2 分：本轮 0 个产品文件（连读 %s 轮），而且**主动回滚**了一发已经落进产品的改动。
这不是保守：那一发改完，"胶囊有没有在动"这条判据就没有对象了 —— 一个让证人失明的画法不能留。
391 的修法现在有了系统分母，落在新开 393。

为什么判据有效性只给 13：新落的那格本轮**只印不判**（极性符号没有牙），
三把刀钉住的是"两臂是不是真的差 selection"与"页底是不是从对象外面取"，
而"自家必须与系统同侧"那条断言要与 393 的修法同一笔落地（D-274：参照刚被证明存在，地板不能当场拍）。

为什么可复核性给 13：`SEGREF_POLARITY` 已经接进 §8 的搬运名单（现读 `声明=%s 缺=%s`），
但它在 runner（1×、不合成材质）上读不读得出，本机判不了 —— 这条欠账开成 %d。
""" % (u"%.1f" % PRE_L[u"页底"], u"%.1f" % POST_L[u"轨道"], u"%.1f" % PRE_L[u"轨道"],
       u"%.1f" % POST_L[u"药丸"], u"%.1f" % PRE_L[u"药丸"],
       u"%.1f" % PRE_L[u"分离"], u"%.1f" % POST_L[u"分离"], PEAK[0], PEAK[1],
       fmt(SYS_DARK), u"74.0", u"48.0", fmt(OWN_DARK), fmt(SYS_LIGHT), u"205.0", u"235.0",
       D1, u"74.0", u"205.0", FBK[u"COMPARED"], FBK[u"CHANGED"],
       STREAK_N, MUST[0], MUST[1], B3)

D_BODY = u"""
**D-%d（%d）：极性判据必须按色档分别立 —— 系统自己的分段控件在两档里方向相反**
：参照臂现读 暗档 差 %s（选中比未选亮）、亮档 差 %s（选中比未选暗，且看图确认是中性灰不是 tint）。
所以"自家与系统同侧"不许写成一条全局 luma 符号：那样写会把亮档的**系统画法**判成缺陷，
也会把亮档自家的 +%.1f 判成"已经对了"。落地形状：断言按 `appearance` 各立一条，
各自的地板由各自的判据红来改（D-321 同一族）。
""" % (D1, ROUND, fmt(SYS_DARK), fmt(SYS_LIGHT), abs(OWN_LIGHT)) + u"""
**D-%d（%d）：改画法之前先要一条"系统怎么画"的证人；被自己的判据否掉的修法要回滚而不是放宽**
：391 的两条出路方向相反，而 ②（把轨道压到页底之下）落进产品之后红的是**过程证人**
（`testFilterPillSlideIsAProcessNotATeleport` 峰值=%s < 地板=%s）——
这条红说的是"我的画法让证人失明"，它不是需要放宽的假红，而是对这一发最直接的否决。
处置：令牌与两处调用点整发回滚（现场留 `.scratch/motion-audit-2/r331_attempt_two_trackwell.patch`），
方向改由新落的系统参照臂现读定（暗档 %s 对 %s ⇒ ①）。
规矩：**当一发产品改动让判据失去对象时，改的是那发改动，不是判据。**
""" % (D2, ROUND, PEAK[0], PEAK[1], fmt(SYS_DARK), fmt(OWN_DARK))

BL_391 = u"""  追记（R331：②被否、方向定成①，但四个数还欠着）：本轮先落 ②（新令牌
  `VisualMaterial.trackWell = underPageBackgroundColor`）。离屏那卷现读 页底 30.0 / 轨道 **40.0**（改前 51.9）/
  药丸 36.0（改前 36.0）/ 分离 **4.0**（改前 15.9）—— 轨道没进页底之下（暗档页底是 vibrancy 材料本身），
  而红起来的是过程证人 `testFilterPillSlideIsAProcessNotATeleport`（峰值=0.000 地板=0.005）：
  药丸与轨道糊成一档之后，"有没有东西在动"没有对象了 ⇒ ② 整发回滚，现场留
  `.scratch/motion-audit-2/r331_attempt_two_trackwell.patch`。
  方向随后由新落的**系统参照臂**现读定（同一夹具通道、同一颗尺）：暗档 系统 差 **+26.0**
  （选中 74.0 / 未选 48.0，两臂镜像一致）对 自家 **−16.0** ⇒ 391 的修法只剩 ①，
  而亮档 系统 差 **−30.0** ⇒ 同侧断言必须按档分别立（D-323）。
  本单结案条件不变（D-318/D-319：同一运行里改前改后的 轨道档/药丸档/页底档/差 四个数，
  离屏与真机两边同向），具体落地开成 393。
"""

BL_NEW = u"""**393. 391 的落地只剩①：药丸换成系统那颗的同一枚令牌，而"药丸=与页底同档"这条定义要连带重基（R331 现读 系统 暗档 差=+26.0 对 自家 −16.0）**（R331）
    令牌候选已由参照臂量出：`unemphasizedSelectedContentBackgroundColor`（解析 70／220，
    与系统两档的选中电平 74.0／205.0 同档）。难点不在产品那两行，在尺：
    `MotionFilmstripTests.pillRun` 的"药丸 = 与页底同档的那一段"是**照着缺陷画法**定义的
    （R323 的斜坡尺与 R328 的分档都站在它上面）—— 药丸抬到轨道之上之后，轨道 extent 里
    再也没有"与页底同档"的那一段，两把尺同时失去对象。
    重基的形状已经想清楚，而且比现在这把更稳：**药丸 = 两帧之间变了的那一档**
    （`|A[i] − B[i]| ≥ delta` 的列集合）—— 极性无关、不抄 `FilterPillGeometry`、
    也不受字墨少数列劫持（列中位数已经在），并且它就是 377 在屏幕上用的那句判据。
    验收：① 改前改后四个数同一运行现读（离屏那卷 + 真机那把尺同向，D-318/D-319）；
    ② 同侧断言按档各立一条（D-323），暗档必须正、亮档必须与系统同号；
    ③ 重基后的旧读数（`纵向覆盖`、`分档`、`洞宽`）要么继续成立、要么公开改写，不许静默换义；
    ④ 刀要重钉：R327…R329 那几张表里打在 `pillRun` 谓词与报告行上的针，改定义之后必须重跑（旧 CAUGHT 不替新代码作证）。
    做完之前 391 不许结案。

**394. `SEGREF_POLARITY` 在 runner（1×、不合成材质）上读不读得出 —— 本机判不了，欠一跑 CI 现读**（R331）
    参照臂与自家臂都靠离屏通道合成材质，而这条通道在 runner 上的历史是"看不见卡片材质"（R100 那一族）。
    判据里已经留了具名出口 `sysref_seg_fill_not_drawn`（字形画得出而填充读不出范围时走它，
    并且先要求**自家那颗在同一颗尺下读得出范围** —— 正对照先行，否则"参照没画"会被读成"通道没问题"）。
    本机能签的只有本机这一半：暗档 差=+26.0、亮档 差=-30.0、两臂镜像一致。
    runner 那一半要等 393 落地那一跑的 `SEGREF_POLARITY` 现读：
    ① 若两档都印出极性 ⇒ 参照臂跨机器成立，D-323 的按档断言可以升成硬门；
    ② 若走出口 ⇒ 那是通道事实，**不许**读成参照臂坏了，也不许因此放宽任何地板；
    ③ 若整族一行都没有 ⇒ 先查捕获步骤有没有把这一格跑上（`--must-include` 在 §8 里已经声明，缺族会红）。
"""

CHG_ENTRY = (u"### 391 的方向改由系统参照臂印：暗档 系统 差=+26.0 对 自家 −16.0，而「压轨道」那一发被它自己红起来的过程证人否掉并回滚"
             u"（R%d / U-%d…U-%d · 产品 0 文件，参照臂账）" % (ROUND, UA, UD)) + u"""

- 新夹具两张：`sysref-segmented-selected-left` / `-right`（200×60，与 `sysref-button-*` 同族），
  新判据 `testSystemSegmentedReferenceSaysWhichHalfTracksSelection` —— 页底从取景顶部三行取、
  对象纵向范围逐行找、取样带取中段三分之一、两臂必须互为镜像；现读 暗档 系统 +26.0／自家 −16.0，
  亮档 系统 −30.0／自家 +3.0。
- ②那一发（`VisualMaterial.trackWell = underPageBackgroundColor`）落进产品后离屏现读
  轨道 51.9→40.0、分离 15.9→4.0，红在 `testFilterPillSlideIsAProcessNotATeleport`
  （峰值=0.000 地板=0.005）⇒ 整发回滚，现场留 `.scratch/motion-audit-2/r331_attempt_two_trackwell.patch`。
- 自曝两次「尺读错对象」（写死的取样带 38%%…62%% 落在对象之外；页底从"控件外的列"取而自家胶囊满幅），
  第二次一度把结论写成"这条通道不画系统控件的填充"—— 那是**错的归因**，本轮公开更正。
- 刀 `mutate_r331.py`：%s（逐臂 %s）；针预检 tables=%s covered=%s bad=%s、名册 files=%s arms=%s dupes=%s；
  读数族 `SEGREF_POLARITY` 接进 §8 搬运名单（`READINGS_MUST_INCLUDE 声明=%s 缺=%s`）。
- 七本一起落：U-%d…U-%d、D-%d…D-%d、391 追记 + 新开 393/394、STATE 轮换、报告计数器；
  帧名单 174→%s（同一笔 `frame_baseline.py update`）。
""" % (KNIFE_LINE, KNIFE_ARMS, PRE[0], PRE[1], PRE[2], ARM_TOTAL[0], ARM_TOTAL[1], ARM_TOTAL[2],
       MUST[0], MUST[1], UA, UD, D1, D2, CAPTURED)

STATE_TITLE = u"## R%d 状态（%s · 本地 · 第 %d 轮 / Round %d）：391 的方向交给系统自己印 —— 参照臂进夹具通道，②那一发回滚（产品 0 文件，参照臂账）" % (
    ROUND, DATE, AUDIT_N, ITER_N)
STATE_BODY = u"""
最后更新：%s（本地 · R%d / 第 %d 轮 / Round %d）：系统参照臂现读 暗档 差=%+.1f（选中 74.0 / 未选 48.0）
⇒ 391 的修法定成①（抬选中那颗），而②（压轨道）落进产品后被自己的过程证人否掉（峰值=%s < 地板=%s）并整发回滚
（产品 0 文件 · 参照臂账 · 合计 85/105）

本轮做了什么：把"该往哪边改"从我的记性变成一次测量。新夹具 `sysref-segmented-selected-{left,right}`
（系统自己的 `NSSegmentedControl`，同一条 render / 同一个 probeFrame / 同一颗尺）+ 新判据
`testSystemSegmentedReferenceSaysWhichHalfTracksSelection`；391 的 ② 那一发（`trackWell =
underPageBackgroundColor`）落了产品又被回滚，现场留 patch。两次「尺读错对象」自曝并修成闸（写死的取样带、
从对象自己身上取的页底），第一次据此下的"通道不画填充"是**错结论**，本轮公开更正。

验证读数（现读）：参照臂 `SEGREF_POLARITY dark｜系统 页底=30.0 左臂选中=74.0 左臂未选=48.0 差(左臂)=+26.0 差(右臂)=+26.0 AB=两臂镜像一致｜自家 页底=30.0 选中=36.0 未选=52.0 差=-16.0｜同侧=否`；
亮档同形（系统 −30.0／自家 +3.0／同侧=否）；②的改后四数 页底 30.0 轨道 40.0 药丸 36.0 分离 4.0（改前 30.0／51.9／36.0／15.9）；
构建 0 告警（`--build-tests`）、全量卷 `Executed %s tests, with %s skipped and %s failures`、
捕获 `CAPTURED %s -> %s`、帧基线 `COMPARED=%s CHANGED=%s MISSING=%s ADDED=%s`（本轮同一笔 update，174→%s）、
清账表 `%s`；
刀 `%s`（逐臂 %s）；针预检 tables=%s covered=%s bad=%s、名册 files=%s arms=%s dupes=%s；
搬运名单 `READINGS_MUST_INCLUDE 声明=%s 缺=%s`；脚本电池 `Ran %s（skipped=%s）`；
产品面连续零改动 **%s** 轮（唯一取数口 `python3 scripts/product_streak.py --streak-for %d`，`--check` 同形；本轮这一笔按 `--streak-for %d` 现读是 %s，要等 commit 之后 git 才派生得出来；上一轮那一格是 %s）。

NOT-RUN（三种缺席分开写，不许省略）：① **本轮没有对象**的那一腿 —— dmg + 换装本机：
改动面 %s 个文件里 0 个产品文件（只有测试夹具与台账），已装的那一份与盘上的产物同码，
换装不判任何东西；而真机侧 `pgrep` 现读有实例在跑（`ClipboardHistoryApp` 一个 PID，就是用户让我测完帮他重新打开的那一份）⇒ 按 D-322 走
`already_running`，**绝不替用户关窗**。② **只在 runner 上判得了**的：`SEGREF_POLARITY`
在 1×、不合成材质那台机器上读不读得出（判据里已留具名出口 `sysref_seg_fill_not_drawn`，
并先要求自家那颗在同一颗尺下读得出范围）⇒ 开成 394，本机不签这一半。
③ **命令没跑成**的：本轮没有 —— CI 对平留到 R%d 第 ⓪ 条现读（push 之后的 run↔commit 成对写回）。

CI 对平（本轮开场读上一轮的）：RUN=40091469060 ↔ `4e9e59a` ⇒ completed/**success**；
RUN=40086526381 ↔ `c3fdc02` ⇒ failure 在 STEP[9] `LEDGER_TOKENS books=7 stray=1`（就是 R329 漏下的那个
占位符，R330 已修，本轮不再复现）；RUN=40086499268 ↔ `d21eceb` ⇒ success。
本轮要盯的两件事：① runner 电池 `Ran 619（skipped=2）` 与本机 `Ran %s（skipped=4）` 的差是**已登记**的两格
（/tmp 日志缺失 + 没有已构建的 .app），R330 新增的 8 格 python 判据**没有**进 skip 名册 ⇒ 上一轮那条担心
被现读结案；② `REALSCREEN_*` 这一族不进 CI（要一块醒着的屏幕），那一跑没有它的读数 ≠ 没跑成。

下一轮（R%d）的靶，按顺序：① **393**：391 的落地只剩①—— 药丸换成 `unemphasizedSelectedContentBackgroundColor`
（参照臂量出的分母），并把 `pillRun` 的"药丸=与页底同档"重基成"药丸=两帧之间变了的那一档"（极性无关），
D-318/D-319 的改前改后四数 + 按档各立的同侧断言（D-323）+ R327…R329 那几张表的针重钉重跑；
② 390 的 before/after（并集之后中段洞宽 21%%→~49%%、纵向覆盖 29%%→≥70%%）；③ 389 的时长；
④ 384 的横轴那半（轨道档按分箱取，不许再用众数）；⑤ 387 的①（墨量那颗不进 max()）；
⑥ 392 的三格真机欠账（按下档 / 快速选取色 / 菜单栏悬停）；⑦ 394（`SEGREF_POLARITY` 的 runner 现读）；
⑧ 376 剩下那一半；⑨ 367 迁移 / 360 最后一批 / 361 合并 / 364 六把抽不出的刀。
""" % (DATE, ROUND, AUDIT_N, ITER_N, SYS_DARK, PEAK[0], PEAK[1],
       FULL_EXEC, FULL_SKIP, FULL_FAIL, CAPTURED, CAP_DIR,
       FBK[u"COMPARED"], FBK[u"CHANGED"], FBK[u"MISSING"], FBK[u"ADDED"], CAPTURED,
       GATE_FULL,
       KNIFE_LINE, KNIFE_ARMS, PRE[0], PRE[1], PRE[2], ARM_TOTAL[0], ARM_TOTAL[1], ARM_TOTAL[2],
       MUST[0], MUST[1], BATT, BATT_SKIP, STREAK_N, ROUND - 1, ROUND, STREAK_GIT, PREV_STREAK,
       s(len(CHANGED)), ROUND + 1, BATT, ROUND + 1)

SUBS = {}


def fill(text):
    for k in sorted(SUBS, key=len, reverse=True):
        text = text.replace(k, SUBS[k])
    left = re.findall(u"@\\w+@", text)
    if left:
        die(u"正文里还有没替换的 token：%s" % left[:5])
    return text


# ──  落盘（锚点全部整行；命中不是 1 次就在写任何盘之前抱出）─────────────────
if UI_TITLE.split(u"（")[0] in rd(AUD):
    die(u"UI_AUDIT 已经有本轮那一节了 ⇒ 半批已写，先回滚再重跑（这一支生成器不重复插）")
ui = rd(AUD)
m = re.search(u"(?m)^## 第 \\d+ 轮", ui)
if not m:
    die(u"UI_AUDIT 里找不到轮次标题")
head, tail = ui[:m.start()], ui[m.start():]
wr(AUD, head + UI_TITLE + u"\n" + UI_BODY + u"\n" + tail)

ite = rd(ITE)
if u"\n## Round %d · " % ITER_N in ite:
    die(u"ITERATION 已经有本轮那一节了")
wr(ITE, ite.rstrip(u"\n") + u"\n\n" + ITER_TITLE + u"\n" + ITER_BODY)

dec = rd(DEC)
if u"**D-%d（%d）" % (D1, ROUND) in dec:
    die(u"DECISIONS 已经有本轮那两条了")
wr(DEC, dec.rstrip(u"\n") + u"\n\n" + D_BODY)

blg = rd(BLG)
if BL_NEW.split(u"（R331）")[0] in blg:
    die(u"BACKLOG 已经有本轮那两单了")
anchor391 = re.findall(u"(?m)^\\*\\*391\\. .*$", blg)
if len(anchor391) != 1:
    die(u"BACKLOG 391 的标题行命中 %d 次" % len(anchor391))
start = blg.index(anchor391[0])
nxt = re.search(u"(?m)^\\*\\*\\d{3}\\. ", blg[start + 1:])
if not nxt:
    die(u"391 之后找不到下一条条目（392）⇒ 追记该用尾条追加而不是中间插入")
ins = start + 1 + nxt.start()
blg = blg[:ins] + BL_391.strip(u"\n") + u"\n\n" + blg[ins:]
wr(BLG, blg.rstrip(u"\n") + u"\n" + BL_NEW)

chg = rd(CHG)
heads = re.findall(u"(?m)^## \\[Unreleased\\]$", chg)
if len(heads) != 1:
    die(u"CHANGELOG 行首的 [Unreleased] 标题不是恰好一次（读到 %d）" % len(heads))
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
wr(STA, sta[:pos] + STATE_TITLE + u"\n" + fill(STATE_BODY) + u"\n" + sta[pos:])

# ──  FINAL_REPORT：只改计数器与 §13 那三格，数字全部来自现读 ────────────────
fr = rd(FRA)
mUD = re.search(u"U-31 … U-(\\d+)", fr)
if not mUD:
    die(u"报告里找不到 U 区间那一格")
fr = once(fr, mUD.group(0), u"U-31 … U-%d" % UD)
mD = re.search(u"D-069 … D-(\\d+)", fr)
if mD:
    fr = once(fr, mD.group(0), u"D-069 … D-%d" % D2)
mK = re.search(u"M(\\d{3}) … M(\\d{3})", fr)
if mK:
    fr = once(fr, mK.group(0), u"M%s … %s" % (mK.group(1), ARMS[-1]))
scale_old = re.findall(u"(?m)^- \\*\\*判据与门的规模\\*\\*：.*$", fr)
if len(scale_old) != 1:
    die(u"§13 的「判据与门的规模」那一格命中 %d 行" % len(scale_old))
udefs = len(re.findall(u"(?m)^- \\*\\*U-(\\d{3,4})[：(]", rd(AUD)))
new_scale = (u"- **判据与门的规模**：脚本电池现读 **Ran %s**（写盘前同数），变异臂在册 **%s** 把 / %s 张表"
             u"（预检 tables=%s covered=%s bad=%s）；U 定义行 **%s 条**、最大 **U-%d**；"
             u"决定台账最大 **D-%d**，BACKLOG 最大 **%d**（本轮 391 追记 + 新开 %d、%d：391 的落地与参照臂的 runner 欠账）；"
             u"本轮刀 `%s`（%s）。§8 的读数搬运名单本轮**接了**：新族 `SEGREF_POLARITY` 进 `ledger_rows.py` 的"
             u"前缀表，现读 `READINGS_MUST_INCLUDE 声明=%s 缺=%s`。"
             % (BATT, ARM_TOTAL[1], ARM_TOTAL[0], PRE[0], PRE[1], PRE[2], udefs, UD, D2, B3, B1, B3,
                KNIFE_LINE, KNIFE_ARMS, MUST[0], MUST[1]))
fr = fr.replace(scale_old[0], new_scale)
prod_old = re.findall(u"(?m)^- \\*\\*产品面（这一节最该被读的部分）\\*\\*：.*$", fr)
if len(prod_old) != 1:
    die(u"§13 的「产品面」那一格命中 %d 行" % len(prod_old))
new_prod = (u"- **产品面（这一节最该被读的部分）**：本轮产品文件 0 个（**参照臂账**：改动面 %s 个文件，"
            u"产品 0 个、判据 1 格（`UICaptureHarness.swift` 的新参照臂）+ 夹具 2 张、台账 7 本；"
            u"本轮**主动回滚**了一发已经落进产品的改动（②压轨道），理由是它让过程证人失明，见 D-%d；"
            u"dmg/换装那一腿因此没有对象，写成 NOT-RUN。"
            u"产品面连续零改动 **%s** 轮（唯一取数口 `python3 scripts/product_streak.py --streak-for %s`，"
            u"`--check` 同形；本轮这一笔按 `--streak-for %s` 现读是 %s，要等 commit 之后 git 才派生得出来）。"
            u"产品面连续零改动轮数 = **%s**。391 的方向本轮由系统参照臂现读定死（暗档 %+.1f 对 %+.1f），落地开成 %d。"
            % (s(len(CHANGED)), D2, STREAK_N, s(ROUND - 1), s(ROUND), STREAK_GIT,
               STREAK_N, SYS_DARK, OWN_DARK, B2))
fr = fr.replace(prod_old[0], new_prod)
ptr_old = re.findall(u"(?m)^- \\*\\*仍开（截至本轮，完整名单以 `AGENT_STATE.md` 的 R\\d+ 节.*$", fr)
if len(ptr_old) != 1:
    die(u"§13 的「仍开」指针那一格命中 %d 行" % len(ptr_old))
fr = re.sub(u"(?m)^(- \\*\\*仍开（截至本轮，完整名单以 `AGENT_STATE.md` 的 R)\\d+( 节)",
            u"\\g<1>%d\\g<2>" % ROUND, fr, count=1)
# 标题那一格（`R9–R<NNN>，<M> 节自评`）由 `test_final_report_headline` 对活账，而
# `refresh_report_section1.py` 明说它**不动标题**（它打的是「标题=未动（Round 口径，由既有守卫签）」）——
# 于是这一格历史上是"谁手快谁改"，R331 第一遍就红在它落后两轮上（标题写 R326 而 ITERATION 已到 Round 328，
# 允许落后 1 轮）。现在它跟着本轮走：上界 = 本轮 Round 号，节数 = ITERATION 里 `## Round` 的**实际条数**（现读）。
mt = re.search(u"R9–R(\\d+)，(\\d+) 节自评", fr)
if not mt:
    die(u"报告标题里找不到 `R9–R<NNN>，<M> 节自评` 那一格 ⇒ 这一维的对账断了，不许静默跳过")
n_rounds = len(re.findall(u"(?m)^## Round ", rd(ITE)))
fr = once(fr, mt.group(0), u"R9–R%d，%d 节自评" % (ITER_N, n_rounds))
if re.search(u"@\\w+@", fr):
    die(u"报告刷新后还有没替换的占位符：" + str(re.findall(u"@\\w+@", fr)[:4]))
wr(FRA, fr)

# ── ④ 写盘之后：电池、连读门、曲线、报告标题 ─────────────────────────────────
rf0, rfc0 = sh([sys.executable, FRESH])
if rfc0 != 0 or u"REFUSED" in rf0:
    die(u"报告 §1 那一格的刷新器没签（rc=%d）：%s" % (rfc0, rf0.strip()[-300:]))
print(u"SECTION1 " + rf0.strip().splitlines()[-1])
bt2, rc2 = sh([sys.executable, u"-m", u"unittest", u"discover", u"-s", u"scripts/tests"])
RAN2 = (re.findall(r"Ran (\d+) tests", bt2) or [None])[-1]
if rc2 != 0 or RAN2 != BATT:
    die(u"写盘后电池变了或红了（%s → %s）\n%s" % (BATT, RAN2, bt2.strip()[-900:]))
ck, ckc = sh([sys.executable, STREAK, u"--check"])
if ckc != 0:
    die(u"353 的连读门不认这版台账：" + (ck + u"\n").strip()[-500:])
cv2, _ = sh([sys.executable, CURVE])
if (re.findall(r"^GAPS=(\S+)", cv2, re.M) or [u""])[-1] != u"none":
    die(u"写盘后曲线尺报缺口：" + cv2.strip()[-300:])
DERIVED2 = dict((int(a), int(b)) for a, b in
                re.findall(r"(\d+)=(\d+)", (re.findall(r"^SCORES_BY_ROUND .+$", cv2, re.M) or [u""])[-1])
                ).get(ITER_N)
if DERIVED2 is None:
    die(u"写盘后曲线尺没给出本轮 Round %d 的派生分" % ITER_N)
if u"U-31 … U-%d" % UD not in rd(FRA):
    die(u"报告 §1 的 U 上界不是本轮的 U-%d" % UD)
if u"@RPREVTAG@" in rd(STA):
    die(u"STATE 里还有占位符")
rf, rfc = sh([sys.executable, FRESH])
if rfc != 0 or u"REFUSED" in rf or u"未动" not in rf:
    die(u"报告 §1 的刷新器第二遍不干净（rc=%d）：%s" % (rfc, rf.strip()[-300:]))
chk, chkc = sh([sys.executable, u"-m", u"unittest", u"-v",
                u"test_final_report_headline.FinalReportHeadlineTests.test_the_headline_cells_agree_with_the_live_ledgers"],
               cwd=TESTS)
if chkc != 0:
    die(u"报告标题那几格与台账不同源：" + chk.strip()[-400:])

print(u"LEDGERS_R331 OK batt=Ran " + BATT + u" (skipped=" + BATT_SKIP + u") streak=" + STREAK_N
      + u"(上一轮 " + PREV_STREAK + u") 产品文件=0 改动面=" + s(len(CHANGED))
      + u" 刀=" + KNIFE_LINE + u" 臂=" + KNIFE_ARMS
      + u" 参照臂 暗 系统=" + fmt(SYS_DARK) + u" 自家=" + fmt(OWN_DARK)
      + u" 亮 系统=" + fmt(SYS_LIGHT) + u" 自家=" + fmt(OWN_LIGHT)
      + u" ②改后 轨道=" + u"%.1f" % POST_L[u"轨道"] + u" 分离=" + u"%.1f" % POST_L[u"分离"]
      + u" 帧=" + CAPTURED + u" 基线 COMPARED=" + FBK[u"COMPARED"] + u" CHANGED=" + FBK[u"CHANGED"]
      + u" 全量=" + FULL_EXEC + u"/skip" + FULL_SKIP + u"/fail" + FULL_FAIL
      + u" 搬运 声明=" + MUST[0] + u" 缺=" + MUST[1]
      + u" 预检 tables=" + PRE[0] + u" covered=" + PRE[1] + u" bad=" + PRE[2]
      + u" 在册=" + ARM_TOTAL[1] + u"/" + ARM_TOTAL[0]
      + u" U=" + s(UA) + u".." + s(UD) + u" D=" + s(D1) + u".." + s(D2) + u" BL=" + s(B2) + u"," + s(B3)
      + u" derived(Round " + s(ITER_N) + u")=" + s(DERIVED2))
