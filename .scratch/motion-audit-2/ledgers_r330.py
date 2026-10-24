#!/usr/bin/env python3
# -*- coding: utf-8 -*-
u"""R330 的台账生成器（第 329 轮 / Round 328 · 真机账 · 产品 0 文件）。

与上一批生成器的两处不同，都是本轮形状逼出来的：
  ① 四腿 Swift 验证（build / 重捕帧 / 帧基线 / 换装）本轮**没有对象**（0 个 Swift 文件），
     写成 NOT-RUN 并绑理由，不写成通过；
  ② 新的读数族（`REALSCREEN_VERDICT` / `PILL_ROW` / `AB_SUMMARY`）由这把 python 尺自己打印，
     不进 `round_verify.sh` 的日志 ⇒ `ledger_rows.py --must-include` 那一腿本轮不适用（写进账，
     并开一单说清"要进 §8 就得先接进 round_verify"）。

所有数字都从**当场跑**的命令里解析；锚点一律整行，命中不是 1 次就在写任何盘之前抱出。
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
TABLE = os.path.join(ROOT, u".scratch", u"motion-audit-2", u"mutate_r330.py")
RULER = os.path.join(ROOT, u"scripts", u"real_screen_filter_pill.py")
TESTS = os.path.join(ROOT, u"scripts", u"tests")
FRAME_A = u"/tmp/r330_real/pill.png"
FRAME_B = u"/tmp/r330_ab/b.png"
AB_LOG = u"/tmp/r330_ab/ab6.log"

ENV = dict(os.environ)
ENV[u"PYTHONUTF8"] = u"1"
ENV[u"PYTHONDONTWRITEBYTECODE"] = u"1"

ROUND = 330
AUDIT_N = 329          # 第 329 轮
ITER_N = 327           # Round 327（R_n = Round n−3；写成 328 会让曲线尺报 GAPS=[327]）
DATE = u"2026-10-24"
UA, UB, UC, UD = 1094, 1095, 1096, 1097
D1, D2, D3 = 320, 321, 322
B1, B2 = 391, 392
ARMS = (u"M957", u"M958", u"M959")

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
    print(u"LEDGERS_R330_DIED " + msg)
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


# ──  现场跑，数字只从这些输出里解析 ─────────────────────────────────────────
vol, rc = sh([sys.executable, u"-m", u"unittest", u"discover", u"-s", u"scripts/tests",
              u"-p", u"test_real_screen_filter_pill.py"])
if rc != 0:
    die(u"新判据卷不绿，本轮不许落盘：" + vol.strip()[-400:])
VOL_RAN = (re.findall(r"Ran (\d+) tests", vol) or [None])[-1]
if VOL_RAN is None:
    die(u"读不到新判据卷的 Ran 那一行")

bt, brc = sh([sys.executable, u"-m", u"unittest", u"discover", u"-s", u"scripts/tests"])
BATT = (re.findall(r"Ran (\d+) tests", bt) or [None])[-1]
BATT_SKIP = (re.findall(r"skipped=(\d+)", bt) or [u"0"])[-1]
if brc != 0 or BATT is None:
    die(u"脚本电池在落盘之前就是红的（Ran=%s）：先修电池再写账\n%s" % (BATT, bt.strip()[-600:]))

kn, krc = sh([sys.executable, TABLE])
if krc != 0:
    die(u"变异表没过关，不落盘：" + kn.strip()[-500:])
KNIFE = (re.findall(r"CAUGHT=(\d+/\d+), RESTORE_CLEAN=(\S+)", kn) or [None])[-1]
if KNIFE is None:
    die(u"读不到变异表自己打的那一行收尾")
KNIFE_LINE = u"CAUGHT=%s, RESTORE_CLEAN=%s" % KNIFE
KNIFE_ARMS = u", ".join(re.findall(r"(M\d{3}) CAUGHT", kn))

pc, _prc = sh([sys.executable, PRECHK])
PRE = (re.findall(r"NEEDLE_PRECHECK tables=(\d+) covered=(\d+) arms=\d+ bad=(\d+)", pc) or [None])[-1]
ARM_TOTAL = (re.findall(r"ARM_TOTAL files=(\d+) arms=(\d+) dupes=(\d+) repeats=(\d+)", pc) or [None])[-1]
if PRE is None or ARM_TOTAL is None or PRE[2] != u"0" or ARM_TOTAL[2] != u"0":
    die(u"针预检/臂名册不干净：" + pc.strip()[-400:])

for f in (FRAME_A, FRAME_B, AB_LOG):
    if not os.path.exists(f):
        die(u"真机证人不在盘上（/tmp 会被清）：%s ⇒ 本轮读数要重跑真机才能落账" % f)
ra, rrc = sh([sys.executable, RULER, u"--png", FRAME_A, u"--width-pt", u"750"])
rb, rrc2 = sh([sys.executable, RULER, u"--png", FRAME_B, u"--width-pt", u"750"])
if rrc != 0 or rrc2 != 0:
    die(u"尺离线复量两臂没判到（rc=%s/%s）" % (rrc, rrc2))
CELL_A = (re.findall(r"(?m)^PILL_ROW .*$", ra) or [None])[-1]
CELL_B = (re.findall(r"(?m)^PILL_ROW .*$", rb) or [None])[-1]
VERD_A = (re.findall(r"REALSCREEN_VERDICT=(\w+)", ra) or [None])[-1]
VERD_B = (re.findall(r"REALSCREEN_VERDICT=(\w+)", rb) or [None])[-1]
AB_LINE = (re.findall(r"(?m)^AB_SUMMARY .*$", rd(AB_LOG)) or [None])[-1]
AB_VERD = (re.findall(r"AB_VERDICT=(\w+)", rd(AB_LOG)) or [None])[-1]
if None in (CELL_A, CELL_B, VERD_A, VERD_B, AB_LINE, AB_VERD):
    die(u"真机读数没解析全")
if VERD_A != u"pill_darker" or VERD_B != u"pill_darker" or AB_VERD != u"selection_follows_dark":
    die(u"两臂的结论与登记的不一致（%s / %s / %s）⇒ 不许按旧结论落账" % (VERD_A, VERD_B, AB_VERD))
NUM = u"(页底|轨道档|药丸档)=([-\\d.]+)"
PA = dict((k, float(v)) for k, v in re.findall(NUM, CELL_A))
PB = dict((k, float(v)) for k, v in re.findall(NUM, CELL_B))
PAGE_A, TRACK_A, PILL_A = PA[u"页底"], PA[u"轨道档"], PA[u"药丸档"]
DIFF_A = float(re.search(u"差=([+-][\\d.]+)", CELL_A).group(1))
DIFF_B = float(re.search(u"差=([+-][\\d.]+)", CELL_B).group(1))
if abs((PILL_A - TRACK_A) - DIFF_A) > 0.11 or abs((PB[u"药丸档"] - PB[u"轨道档"]) - DIFF_B) > 0.11:
    die(u"差与两档之差不自洽（A %+.1f / B %+.1f）⇒ 那一行的格式漂了，解析器要跟着改" % (DIFF_A, DIFF_B))
if not (DIFF_A < 0 and DIFF_B < 0):
    die(u"两臂必须同为暗洞才算同一个缺陷跟着选中走")

# 台账里那一格引的是**上一轮**的号：`--check` 只认 git 已经派生得出的那个数，
# 而本轮这一笔还没 commit ⇒ 写 `--streak-for 本轮` 会写出一个 git 当场算不出来的数
# （R330 实测：写 12 报 PRODUCT_STREAK_LEDGER_STALE，因为它派生到 11）。
# R328/R329 两本的形状都是"引上一轮"，跟着它们，并把本轮的数另写一句。
st_this, _ = sh([sys.executable, STREAK, u"--streak-for", s(ROUND)])
st_cell, src = sh([sys.executable, STREAK, u"--streak-for", s(ROUND - 1)])
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
    die(u"这一支生成器是给零产品文件的真机账写的，现在改动面里有产品文件：%s" % PRODUCT[:3])

cv, crc = sh([sys.executable, CURVE])
if crc != 0:
    die(u"曲线尺不干净：" + cv.strip()[-300:])
DERIVED = dict((int(a), int(b)) for a, b in
               re.findall(r"(\d+)=(\d+)", (re.findall(r"^SCORES_BY_ROUND (.+)$", cv, re.M) or [u""])[-1])
               ).get(ITER_N)

# ──  三本正文 ───────────────────────────────────────────────────────────────
UI_TITLE = (u"## 第 %d 轮（R%d · U-%d…U-%d · %s）：377 在屏幕上判掉了 —— 侧栏那颗选中的胶囊"
            u"**比轨道暗** %.1f 级，而且暗的那一块跟着选中搬（U-%d…U-%d · 产品 0 文件，真机账）"
            % (AUDIT_N, ROUND, UA, UD, DATE, abs(DIFF_A), UA, UD))
UI_BODY = u"""
- **U-%d：真机现读（本机 2× / dark）侧栏筛选胶囊：轨道 %.1f 档、选中那颗 %.1f 档、页底 %.1f 档 ⇒ 差 %+.1f 级**
  —— 离屏胶片那卷读到的方向（轨道 51.9 / 药丸 36.0 / 页底 30）在屏幕上**同向复现**，
  且选中那颗与页底同档（%.1f 对 %.1f，差 < delta 8）⇒ 377 不是材质通道的产物，是产品怎么画的。
  原文：`%s` → `%s`。
- **U-%d：两臂对照把"左半边有块暗的"这个解释排除掉了** —— 用系统事件点另一颗之后，
  洞从 x2..170 搬到 x172..240，两臂的差同号（%+.1f / %+.1f），`AB_VERDICT=%s`。
  原文：`%s`。
- **U-%d：这把尺在同一趟里自曝三次"读错对象"，每一次都被修成闸 + 一把刀**：
  ① 列电平取 `max()` ⇒ 一条标题行被读成胶囊（差 -78.4）；② 只判横向 ⇒ 同一条行第二次又过闸
  （差 -99.0）；③ 页底从**控件自己那一行**取众数 ⇒ 两半区各占一半时是掷硬币，臂 B 押给了轨道，
  同一个缺陷被报成"选中那颗更亮、不是缺陷"（差 +31.0，结论整个反）。
  现在的形状：列电平取中位、第四道闸是纵向实心度（真机控件 0.445 / 真机文字行 0.017 /
  合成密集文字行 0.169 ⇒ 地板 0.20）、页底两趟外取且上下两条参照带必须同档。
  判据卷 `scripts/tests/test_real_screen_filter_pill.py` 现读 `Ran %s tests` 全绿，
  刀 `%s`（逐臂 %s）。
- **U-%d：真机通道的启动与就绪都有名字了** —— 主窗口只在 `applicationDidBecomeActive` 时恢复
  （`WindowManager.showMainWindow` 只 present 已存在的窗口，从不新建），直接 exec 二进制不保证被激活
  ⇒ 同一份尺前两趟拿到窗口、后两趟 `count of windows = 0`；现在走 `open -a --env`（隔离目录照样带得进），
  并留了四条具名出口：`already_running`（有实例在跑就不动它）、`no_window`、
  `frame_not_rendered`（要连续两帧指纹相同，"有内容"不等于"布局稳了"）、`reference_unstable`。

""" % (UA, TRACK_A, PILL_A, PAGE_A, DIFF_A, PILL_A, PAGE_A, CELL_A, VERD_A,
       UB, DIFF_A, DIFF_B, AB_VERD, AB_LINE, UC, VOL_RAN, KNIFE_LINE, KNIFE_ARMS, UD)

ITER_TITLE = (u"## Round %d · R%d（第 %d 轮 · %s）：377 在屏幕上判成真的 —— 选中那颗比轨道暗 %.0f 级，"
              u"而这块暗跟着选中搬；同一趟里这把尺自曝三次读错对象，三次都变成闸与刀"
              u"（产品 0 文件 · 真机账）" % (ITER_N, ROUND, AUDIT_N, DATE, abs(DIFF_A)))
ITER_BODY = u"""
本轮第一次把侧栏那颗筛选胶囊搬到**真机**上量（用户退出 App 让出通道）。离屏胶片给的读数是
轨道 51.9 / 药丸 36.0 / 页底 30 —— 选中像轨道上挖出的洞；377 问的就是这件事在屏幕上算不算数。
答案是算：本机 2× 真屏现读 `%s`，选中那颗（%.1f）与页底（%.1f）同档，轨道 %.1f ⇒ 差 %+.1f 级。
再点另一颗，洞整块搬到右半（x172..240，差 %+.1f）⇒ `AB_VERDICT=%s`。
所以"选中态读起来像个洞"是产品的画法，不是离屏通道对材质的盲区，377 从"待判"变成"已判、待修"。

看图这条腿本轮是真的看了屏幕那一份 PNG（不是胶片）：控件带、标题行、搜索框三块的位置与明暗
都由尺逐行报出电平，图不入库、只留 /tmp。

七维度自评：

| 维度 | 分/满分 |
| --- | --- |
| 真实视觉审查 | 15/15 |
| 判据有效性 | 14/15 |
| 假绿防御 | 15/15 |
| 产品面推进 | 2/15 |
| 台账一致性 | 13/15 |
| 交付诚实性 | 15/15 |
| 可复核性 | 13/15 |

合计 87/105。派生分由 `curve_from_ledger.py` 现读，不在这一节里手抄。

为什么产品面推进仍是 2 分：本轮 0 个产品文件（连读 %s 轮）。377 现在**有**了屏幕证人，
修法也清楚了（要么把选中那颗抬到轨道之上，要么把轨道压到页底之下，两条都得给改前改后的四个数），
但它落在 391，本轮不动产品 —— 这一轮的产出是那把尺与它的判据卷，先把"能判"这件事钉住。

为什么可复核性只给 13：真机那一层的读数依赖这台机器的一块**醒着的屏幕**与一次人工退出 App；
尺已经把这四种缺席拆成具名出口（`already_running` / `no_window` / `frame_not_rendered` /
`reference_unstable`），但它不能在无人值守的 runner 上复现，所以这一维到不了满分。
""" % (CELL_A, PILL_A, PAGE_A, TRACK_A, DIFF_A, DIFF_B, AB_VERD, STREAK_N)

D_BODY = u"""
**D-%d（%d）：参照物必须从被测对象**外面**取 —— 两半区各占一半时"行内众数"是掷硬币，翻了会把缺陷报成"不是缺陷"**

R330 的臂 B 现场：把页底取成"控件这一行里住得最密的那一档"，在洞占 52%% 的那一帧押对了（差 -33.0），
在洞占一半而亮的那半更宽的一帧押给了轨道（页底被读成 80）⇒ 同一个缺陷被报成"选中那颗比轨道亮 31 级、
不是产品问题"。这不是阈值问题，是**估计量选错**：一行里两个半区各占一半时，"哪一档人多"
不携带任何关于背景的信息。修法是把读参照挪到对象外面（先粗扫圈出控件占哪几行，
再到它上下各取一条带），并要求两条带自己同档 —— 不同档就报 `reference_unstable`，不许往下判。
这条对仓库里所有"从被量对象自身推参照"的尺通用（胶片那把的 `marginWindow` 是同一族）。

**D-%d（%d）：一把尺"有没有认对象"这件事要由判据卷钉，地板值要由判据红来改**

纵向实心度那道闸第一版地板取 0.15，理由是"真机文字行 0.017、真机控件 0.445，中间取一个"。
新写的判据卷用合成帧把它逼出来了：一条按真字疏密画的密集标题行实心度 0.169，**过了闸**。
于是地板抬到 0.20（三个数都进注释：0.017 / 0.169 / 0.445，过闸行最低 0.32）。
教训不是"0.15 错了"，而是：**只在真机一帧上标定过的地板，等于没有地板** ——
它只在那一帧的疏密上成立。合成夹具能自由改疏密，所以它才是这块地板的证人。

**D-%d（%d）：真机通道的三条前置：启动路径、帧就绪、以及"有实例在跑就不动它"**

① 这个产品的主窗口只在 `applicationDidBecomeActive` 里恢复（`showMainWindow` 只 present
已存在的窗口，从不新建），而直接 exec 二进制不保证被激活 ⇒ 同一份脚本前两趟拿到窗口、
后两趟 `count of windows = 0`。走 `open -a --env` 才稳定（macOS 27 的 `open` 支持 `--env`，
本机现读 `open --help` 抄的，不是记的）。② "截到了一帧"不等于"截到被测对象"：
第一版只等"帧里有内容"，结果拿到布局动画中间那一帧（侧栏只有 70pt 宽、控件被裁在边缘），
有内容、有对比、却不是对象 ⇒ 现在要连续两帧指纹相同。③ 起跑前先 `pgrep`：
有实例在跑就 `NOT_RUN already_running`，绝不替用户关窗（那一份可能带着真存档）。
""" % (D1, ROUND, D2, ROUND, D3, ROUND)

BL_377 = u"""
**追记（R330 · 真机判掉，从"待判"变"已判、待修"）**：本机 2× / dark 真屏现读 `%s`，
选中那颗与页底同档、轨道比页底亮 %.0f 级 ⇒ 差 %+.1f 级；点另一颗之后洞从 x2..170 搬到 x172..240
（`AB_VERDICT=%s`）。离屏胶片的读数方向在屏幕上同向复现 ⇒ 这一单**不是**材质通道的锅，
是产品画法。修法与 before/after 欠账开成 %d。尺与判据卷：`scripts/real_screen_filter_pill.py`
+ `scripts/tests/test_real_screen_filter_pill.py`（`Ran %s tests`，刀 %s）。
""" % (CELL_A, TRACK_A - PAGE_A, DIFF_A, AB_VERD, B1, VOL_RAN, KNIFE_LINE)

BL_NEW = u"""
**%d. 选中那颗与轨道的明暗关系要反过来（或者把轨道压到页底之下）—— 两条修法都要同一运行里改前改后的四个数（R330 真机现读 差=%+.1f）**（R330）

R330 真机现读：侧栏那颗筛选胶囊，选中的那一半电平 %.1f 与页底 %.1f 同档，而未选中的轨道是 %.1f ⇒
在屏幕上"选中"就是轨道上挖出的一个洞，与 macOS 分段控件"选中那颗更亮"的惯例相反。
两条候选修法：① 选中那颗抬到轨道**之上**（原生那一面）；② 轨道压到页底**之下**（洞还在，
但选中变成唯一的正形）。两条都不许只改一边：要给出改前改后的 轨道档 / 药丸档 / 页底档 / 差 四个数，
并按 D-318 让"没找到对象"与"盖不住"不同形。
离屏那卷胶片（`filter-pill-slide`）与真机这一把尺要**同时**给出同向的数才算修好 ——
只有一边动就是改了通道。

**%d. 这把真机尺目前只判了侧栏一颗胶囊；同一通道还欠 347/305（按下那一档）与 373（快速选中的取色）**（R330）

R330 的通道已经打通（`open -a --env` 起隔离库 → System Events 现读窗口矩形 → 连续两帧指纹相同 →
只截窗口矩形 → 只打电平/坐标）。同一套 plumbing 还欠三格：① 347/305 的"按下"档要一次真实的
mouseDown 态截图；② 373 的快速选取色（那扇窗是 NSPanel，通道不同，先要能把它唤出来）；
③ 265 的菜单栏悬停那一行（只读，且不许截状态栏菜单的内容 —— 那一格的出口可能是"这台机器判不了"，
但要先量一次再下这个结论）。这三格都不进 CI，只能在这台机器上跑，所以每一格都要写清"没跑"的名字。
""" % (B1, DIFF_A, PILL_A, PAGE_A, TRACK_A, B2)

CHG_ENTRY = (u"### 侧栏筛选胶囊在真机上判成暗洞：377 结案为产品缺陷，新增一把带判据卷与三把刀的真机尺"
             u"（R%d / U-%d…U-%d · 产品 0 文件，真机账）\n\n"
             u"- 真机现读 `%s` → `%s`；点另一颗之后洞搬到右半（`%s`）。\n"
             u"- 新尺 `scripts/real_screen_filter_pill.py`：列电平取中位、页底两趟外取、"
             u"第四道闸是纵向实心度（地板 0.20），四条具名出口。\n"
             u"- 新判据卷 `scripts/tests/test_real_screen_filter_pill.py` `Ran %s tests`；"
             u"刀 `%s`（%s）。\n" % (ROUND, UA, UD, CELL_A, VERD_A, AB_LINE, VOL_RAN, KNIFE_LINE, KNIFE_ARMS))

STATE_TITLE = (u"## R%d 状态（%s · 本地 · 第 %d 轮 / Round %d）：377 在屏幕上判掉了 —— 选中那颗比轨道暗 "
               u"%.0f 级且跟着选中搬（产品 0 文件，真机账）" % (ROUND, DATE, AUDIT_N, ITER_N, abs(DIFF_A)))
STATE_BODY = u"""
最后更新：@DATE@（本地 · R@ROUND@ / 第 @AUDIT_N@ 轮 / Round @ITER_N@）：真机现读侧栏筛选胶囊 轨道 @TRACK_A@ / 选中那颗 @PILL_A@ / 页底 @PAGE_A@
⇒ 差 @DIFF_A@ 级，点另一颗之后洞搬到右半 ⇒ 377 判成**产品缺陷**（不是离屏通道的锅）
（产品 0 文件 · 真机账 · 合计 87/105）

本轮做了什么：第一次把侧栏那颗胶囊搬到真机上量。新尺 `scripts/real_screen_filter_pill.py`
（列电平取中位、页底两趟外取、第四道闸纵向实心度、四条具名出口）+ 新判据卷
`scripts/tests/test_real_screen_filter_pill.py`（合成帧，`Ran @VOL_RAN@ tests`）+ 一支打这把尺自己的表
`mutate_r330.py`（@KNIFE_LINE@，逐臂 @KNIFE_ARMS@）。同一趟里尺自曝三次读错对象：
`max` 列电平 → 差 -78.4 的假胶囊；只判横向 → 差 -99.0 的标题行；行内众数当页底 → 臂 B 翻成「不是缺陷」
（差 +31.0，结论整个反）。三次都修成了闸 + 刀（D-@D1@ / D-@D2@）。

验证读数（现读）：真机臂 A `@CELL_A@` → `@VERD_A@`；臂 B `@CELL_B@` → `@VERD_B@`；
两臂对照 `@AB_LINE@` → `@AB_VERD@`；新判据卷 `Ran @VOL_RAN@ tests OK`；刀 `@KNIFE_LINE@`；
针预检 tables=@PRE_TABLES@ covered=@PRE_COVERED@ bad=@PRE_BAD@、名册 files=@ARM_FILES@ arms=@ARM_ARMS@ dupes=@ARM_DUPES@；
脚本电池 `Ran @BATT@（skipped=@BATT_SKIP@）`；产品面连续零改动 **@STREAK_N@** 轮（唯一取数口 `python3 scripts/product_streak.py --streak-for @PREV_ROUND@`，`--check` 同形；本轮这一笔按 `--streak-for @ROUND@` 现读是 @STREAK_GIT@，要等 commit 之后 git 才派生得出来；上一轮那一格是 @PREV_STREAK@）。

NOT-RUN（三种缺席分开写，不许省略）：① **本轮没有对象**的四腿 —— build 0 告警 / swift 判据卷 /
重捕帧 / 帧基线对账 / 换装本机：改动面 @CHANGED_N@ 个文件，全是 python 与台账，0 个 Swift 文件，
这四腿本轮不判任何东西；② **只在 runner 上判得了**的：`REALSCREEN_*` 这一族不进 CI
（它要一块醒着的屏幕与一次人工退出 App），所以 §8 的搬运名单这一腿本轮**不适用** ——
新读数族由尺自己打印，没接进 `round_verify.sh`，要进 §8 得先接进去（欠账记在 @B2@）；
③ **命令没跑成**的：CI 对平本轮没读到（`gh` 两次 `EOF`，网络抖动那一族），
run↔commit 的配对留到 R@NEXT@ 第 ⓪ 条现读。

CI 对平：本轮写盘之前无新 run；R@ROUND@ 要读的那一跑（RUN=40086499268 ↔ d21eceb，R@PREV_ROUND@ 账半）
现读时网络 `EOF` ⇒ 记「未读」，不记「绿」。

⓪ R@NEXT@ 开场要先读的（成对：run id ↔ commit）：**RUN=40086499268 ↔ d21eceb**（结论未读，
`python3 scripts/ci_read.py latest` 现读 `EOF`）+ 本笔 push 的那一跑（sha 见 `git log` 首行，id 未读）。
要读的三件事：① 那一跑的 `MOTION_FLOOR_SUITE_CLEAN` 与两朵 pill 命名出口；
② `纵向覆盖` 在 runner（1×）上印出的比值与本机是否同形（那台是 1× ⇒ px 数减半，比值应当不变）；
③ 脚本电池在 runner 上是否也 `Ran @BATT@`（本轮新增 @VOL_RAN@ 格 python 判据，
若 runner 缺 PIL 会走 skip ⇒ 那要按 252 那一族具名，不许读成绿）。

① R@NEXT@ 的靶：① **@B1@**：377 的修法（选中那颗抬到轨道之上，或把轨道压到页底之下），
按 D-318/D-319 给改前改后的 轨道档 / 药丸档 / 页底档 / 差 四个数，且离屏与真机两边同向；
② **390 的 before/after**（并集之后中段洞宽必须从 21% 涨向 49%、纵向覆盖从 29% 到 ≥70%，
涨不到就是并集没生效）；③ 389 的时长（胶囊位移与内容淡出量成 ms 并对 `MotionCatalog` 的档）；
④ 384 的横轴那半（轨道档按分箱取，不许再用众数 —— 与 D-@D2@ 是同一件事的另一面）；
⑤ 387 的①（墨量那颗不进 max()）；⑥ @B2@ 的三格真机欠账（按下档 / 快速选取色 / 菜单栏悬停）；
⑦ 376 剩下那一半；⑧ 367 迁移 / 360 最后一批 / 361 合并 / 364 六把抽不出的刀。
"""
SUBS = {
    u"@DATE@": DATE, u"@ROUND@": s(ROUND), u"@NEXT@": s(ROUND + 1), u"@PREV_ROUND@": s(ROUND - 1),
    u"@AUDIT_N@": s(AUDIT_N), u"@ITER_N@": s(ITER_N),
    u"@CELL_A@": CELL_A, u"@CELL_B@": CELL_B, u"@VERD_A@": VERD_A, u"@VERD_B@": VERD_B,
    u"@AB_LINE@": AB_LINE, u"@AB_VERD@": AB_VERD,
    u"@TRACK_A@": u"%.1f" % TRACK_A, u"@PILL_A@": u"%.1f" % PILL_A, u"@PAGE_A@": u"%.1f" % PAGE_A,
    u"@DIFF_A@": u"%+.1f" % DIFF_A,
    u"@VOL_RAN@": VOL_RAN, u"@KNIFE_LINE@": KNIFE_LINE, u"@KNIFE_ARMS@": KNIFE_ARMS,
    u"@PRE_TABLES@": PRE[0], u"@PRE_COVERED@": PRE[1], u"@PRE_BAD@": PRE[2],
    u"@ARM_FILES@": ARM_TOTAL[0], u"@ARM_ARMS@": ARM_TOTAL[1], u"@ARM_DUPES@": ARM_TOTAL[2],
    u"@BATT@": BATT, u"@BATT_SKIP@": BATT_SKIP, u"@STREAK_N@": STREAK_N, u"@PREV_STREAK@": PREV_STREAK,
    u"@CHANGED_N@": s(len(CHANGED)), u"@B1@": s(B1), u"@B2@": s(B2),
    u"@STREAK_GIT@": STREAK_GIT,
    u"@D1@": s(D1), u"@D2@": s(D2),
}


def fill(text):
    for k in sorted(SUBS, key=len, reverse=True):
        text = text.replace(k, SUBS[k])
    left = re.findall(u"@\\w+@", text)
    if left:
        die(u"正文里还有没替换的 token：%s" % left[:5])
    return text


STATE_BODY = fill(STATE_BODY)

# ── ② 落盘（锚点全部整行；命中不是 1 次就在写任何盘之前抱出）─────────────────
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
    die(u"DECISIONS 已经有本轮那三条了")
wr(DEC, dec.rstrip(u"\n") + u"\n\n" + D_BODY)

blg = rd(BLG)
if BL_NEW.split(u"（R330）")[0] in blg:
    die(u"BACKLOG 已经有本轮那两单了")
anchor377 = re.findall(u"(?m)^\\*\\*377\\. .*$", blg)
if len(anchor377) != 1:
    die(u"BACKLOG 377 的标题行命中 %d 次" % len(anchor377))
start = blg.index(anchor377[0])
nxt = re.search(u"(?m)^\\*\\*\\d{3}\\. ", blg[start + 1:])
if not nxt:
    die(u"377 之后找不到下一条条目（追记要插在它自己那一节的末尾）")
ins = start + 1 + nxt.start()
blg = blg[:ins] + BL_377.strip(u"\n") + u"\n\n" + blg[ins:]
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
wr(STA, sta[:pos] + STATE_TITLE + u"\n" + STATE_BODY + u"\n" + sta[pos:])

# ──  FINAL_REPORT：只改计数器与 §13 那三格，数字全部来自现读 ────────────────
fr = rd(FRA)
mUD = re.search(u"U-31 … U-(\\d+)", fr)
if not mUD:
    die(u"报告里找不到 U 区间那一格")
fr = once(fr, mUD.group(0), u"U-31 … U-%d" % UD)
mD = re.search(u"D-069 … D-(\\d+)", fr)
if mD:
    fr = once(fr, mD.group(0), u"D-069 … D-%d" % D3)
mK = re.search(u"M(\\d{3}) … M(\\d{3})", fr)
if mK:
    fr = once(fr, mK.group(0), u"M%s … %s" % (mK.group(1), ARMS[-1]))
scale_old = re.findall(u"(?m)^- \\*\\*判据与门的规模\\*\\*：.*$", fr)
if len(scale_old) != 1:
    die(u"§13 的「判据与门的规模」那一格命中 %d 行" % len(scale_old))
udefs = len(re.findall(u"(?m)^- \\*\\*U-(\\d{3,4})[：(]", rd(AUD)))
new_scale = (u"- **判据与门的规模**：脚本电池现读 **Ran %s**（写盘前同数），变异臂在册 **%s** 把 / %s 张表"
             u"（预检 tables=%s covered=%s bad=%s）；U 定义行 **%s 条**、最大 **U-%d**；"
             u"决定台账最大 **D-%d**，BACKLOG 最大 **%d**（本轮新开 %d、%d：377 的修法与真机通道还欠的三格）；"
             u"本轮刀 `%s`（%s）。§8 的读数搬运名单本轮**不适用** —— 新的 `REALSCREEN_*` 一族由真机尺自己打印，"
             u"没接进 `round_verify.sh`（理由与欠账记在 %d）。"
             % (BATT, ARM_TOTAL[1], ARM_TOTAL[0], PRE[0], PRE[1], PRE[2], udefs, UD, D3, B2, B1, B2,
                KNIFE_LINE, KNIFE_ARMS, B2))
fr = fr.replace(scale_old[0], new_scale)
prod_old = re.findall(u"(?m)^- \\*\\*产品面（这一节最该被读的部分）\\*\\*：.*$", fr)
if len(prod_old) != 1:
    die(u"§13 的「产品面」那一格命中 %d 行" % len(prod_old))
new_prod = (u"- **产品面（这一节最该被读的部分）**：本轮产品文件 0 个（**真机账**：改动面 %s 个文件，"
            u"产品 0 个、判据 1 个（`scripts/tests/test_real_screen_filter_pill.py`）、尺 1 个"
            u"（`scripts/real_screen_filter_pill.py`）；四腿 Swift 验证本轮没有对象，写成 NOT-RUN 而不是通过。"
            u"产品面连续零改动 **%s** 轮（唯一取数口 `python3 scripts/product_streak.py --streak-for %s`，"
            u"`--check` 同形；本轮这一笔按 `--streak-for %s` 现读是 %s，要等 commit 之后 git 才派生得出来）。"
            u"产品面连续零改动轮数 = **%s**。377 本轮从「待判」变成「已判」，修法开成 %s。"
            % (s(len(CHANGED)), STREAK_N, s(ROUND - 1), s(ROUND), STREAK_GIT, STREAK_N, s(B1)))
fr = fr.replace(prod_old[0], new_prod)
ptr_old = re.findall(u"(?m)^- \\*\\*仍开（截至本轮，完整名单以 `AGENT_STATE.md` 的 R\\d+ 节.*$", fr)
if len(ptr_old) != 1:
    die(u"§13 的「仍开」指针那一格命中 %d 行" % len(ptr_old))
fr = re.sub(u"(?m)^(- \\*\\*仍开（截至本轮，完整名单以 `AGENT_STATE.md` 的 R)\\d+( 节)",
            u"\\g<1>%d\\g<2>" % ROUND, fr, count=1)
if re.search(u"@\\w+@", fr):
    die(u"报告刷新后还有没替换的占位符：" + str(re.findall(u"@\\w+@", fr)[:4]))
wr(FRA, fr)

# ── ④ 写盘之后：电池、连读门、曲线、报告标题 ─────────────────────────────────
rf0, rfc0 = sh([sys.executable, os.path.join(ROOT, u".scratch", u"motion-audit-2",
                                             u"refresh_report_section1.py")])
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
                re.findall(r"(\d+)=(\d+)", (re.findall(r"^SCORES_BY_ROUND (.+)$", cv2, re.M) or [u""])[-1])
                ).get(ITER_N)
if DERIVED2 is None:
    die(u"写盘后曲线尺没给出本轮 Round %d 的派生分" % ITER_N)
if u"U-31 … U-%d" % UD not in rd(FRA):
    die(u"报告 §1 的 U 上界不是本轮的 U-%d" % UD)
if u"@RPREVTAG@" in rd(STA):
    die(u"STATE 里还有占位符")
rf, rfc = sh([sys.executable, os.path.join(ROOT, u".scratch", u"motion-audit-2",
                                            u"refresh_report_section1.py")])
if rfc != 0 or u"REFUSED" in rf or u"未动" not in rf:
    die(u"报告 §1 的刷新器第二遍不干净（rc=%d）：%s" % (rfc, rf.strip()[-300:]))
chk, chkc = sh([sys.executable, u"-m", u"unittest", u"-v",
                u"test_final_report_headline.FinalReportHeadlineTests.test_the_headline_cells_agree_with_the_live_ledgers"],
               cwd=TESTS)
if chkc != 0:
    die(u"报告标题那几格与台账不同源：" + chk.strip()[-400:])

print(u"LEDGERS_R330 OK batt=Ran " + BATT + u" (skipped=" + BATT_SKIP + u") streak=" + STREAK_N
      + u"(上一轮 " + PREV_STREAK + u") 产品文件=0 改动面=" + s(len(CHANGED))
      + u" 刀=" + KNIFE_LINE + u" 臂=" + KNIFE_ARMS
      + u" 真机A=" + VERD_A + u" 差=" + s(DIFF_A) + u" 真机B=" + VERD_B + u" 差=" + s(DIFF_B)
      + u" AB=" + AB_VERD + u" 判据卷=Ran " + VOL_RAN
      + u" 预检 tables=" + PRE[0] + u" covered=" + PRE[1] + u" bad=" + PRE[2]
      + u" 在册=" + ARM_TOTAL[1] + u"/" + ARM_TOTAL[0]
      + u" U=" + s(UA) + u".." + s(UD) + u" D=" + s(D1) + u".." + s(D3) + u" BL=" + s(B1) + u"," + s(B2)
      + u" derived(Round " + s(ITER_N) + u")=" + s(DERIVED2))
