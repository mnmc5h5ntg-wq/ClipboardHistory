#!/usr/bin/env python3
# -*- coding: utf-8 -*-
u"""R332 的台账生成器（第 331 轮 / Round 329 · 真机缺席分类账 · 产品 0 文件）。

本轮的形状：改动面只有 python（一把尺的**成因分类** + 它的判据卷 + 两支刀），
所以四腿 Swift 验证（build / 判据卷 / 重捕帧 / 帧基线 / 换装）**没有对象**，写成 NOT-RUN 而不是通过；
而真机那一腿**有对象却被挡住** —— 挡它的那一句正是本轮要修的东西。

所有数字都从当场跑的命令里解析；锚点一律整行，命中不是 1 次就在写任何盘之前抱出。
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
TABLE = os.path.join(ROOT, u".scratch", u"motion-audit-2", u"mutate_r332.py")
GATE = os.path.join(ROOT, u"scripts", u"motion_surface_gate.py")
FRESH = os.path.join(ROOT, u".scratch", u"motion-audit-2", u"refresh_report_section1.py")
TESTS = os.path.join(ROOT, u"scripts", u"tests")

ENV = dict(os.environ)
ENV[u"PYTHONUTF8"] = u"1"
ENV[u"PYTHONDONTWRITEBYTECODE"] = u"1"

ROUND = 332
AUDIT_N = 331          # 第 331 轮（R_n = 第 n−1 轮）
ITER_N = 329           # Round 329（R_n = Round n−3）
DATE = u"2026-10-24"
UA, UB, UC = 1102, 1103, 1104
D1 = 326
B1 = 395
ARMS = (u"M963", u"M964")

WRITTEN = []


def rd(p):
    return io.open(p, encoding=u"utf-8").read()


def wr(p, text):
    io.open(p, u"w", encoding=u"utf-8").write(text)
    WRITTEN.append(p)


def sh(cmd, cwd=None):
    p = subprocess.run(cmd, cwd=cwd or ROOT, env=ENV,
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return p.stdout.decode(u"utf-8", u"replace"), p.returncode


def die(msg):
    print(u"LEDGERS_R332_DIED " + msg)
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
vol, vrc = sh([sys.executable, u"-m", u"unittest", u"-v", u"test_real_screen_probe"], cwd=TESTS)
VOL_RAN = (re.findall(r"Ran (\d+) tests", vol) or [None])[-1]
if vrc != 0 or VOL_RAN is None:
    die(u"新判据卷不绿或读不到 Ran：" + vol.strip()[-400:])

# 本轮的中心读数：分类器**现在**怎么说这台机器的通道。
sys.path.insert(0, os.path.join(ROOT, u"scripts"))
import real_screen_sidebar_icons as ruler  # noqa: E402
OWNER = ruler.secure_input_owner()
POWER = u"unknown"
logtxt, _ = sh([u"pmset", u"-g", u"log"])
lo, lf = logtxt.rfind(u"Display is turned on"), logtxt.rfind(u"Display is turned off")
if lf > lo:
    POWER = u"off"
elif lo >= 0:
    POWER = u"on"
ALIVE, WHY = ruler.display_channel_state()
if ALIVE:
    die(u"这一格的前提没了：通道现在**可判**（%s）⇒ 本轮的账要按「缺席分类」重写" % WHY)
if OWNER != u"loginwindow":
    die(u"现读的 SecureInput 属主是 %r，不是 loginwindow ⇒ 本轮那句成因（锁屏）不成立，"
        u"要按现场重写，不许沿用" % (OWNER,))
# 分类器返回的是人话，代码在 classify 里；这里再取一次纯函数结果，保证账里的 code 与话同源。
CODE = ruler.classify_display_channel(POWER, OWNER, False)[1]

kn, krc = sh([sys.executable, TABLE])
if krc != 0:
    die(u"变异表没过关，不落盘：" + kn.strip()[-500:])
KNIFE = (re.findall(r"CAUGHT=(\d+/\d+), RESTORE_CLEAN=(\S+)", kn) or [None])[-1]
if KNIFE is None:
    die(u"读不到变异表自己打的那一行收尾")
KNIFE_LINE = u"CAUGHT=%s, RESTORE_CLEAN=%s" % KNIFE
KNIFE_ARMS = u", ".join(re.findall(r"(M\d{3}) CAUGHT", kn))
if tuple(re.findall(r"(M\d{3}) CAUGHT", kn)) != ARMS:
    die(u"抓到的臂与登记的两把不一致：" + KNIFE_ARMS)

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

bt, brc = sh([sys.executable, u"-m", u"unittest", u"discover", u"-s", u"scripts/tests"])
BATT = (re.findall(r"Ran (\d+) tests", bt) or [None])[-1]
BATT_SKIP = (re.findall(r"skipped=(\d+)", bt) or [u"0"])[-1]
if brc != 0 or BATT is None:
    die(u"脚本电池在落盘之前就是红的（Ran=%s）：%s" % (BATT, bt.strip()[-600:]))

st_this, _ = sh([sys.executable, STREAK, u"--streak-for", s(ROUND)])
st_cell, _ = sh([sys.executable, STREAK, u"--streak-for", s(ROUND - 1)])
st_prev, _ = sh([sys.executable, STREAK, u"--streak-for", s(ROUND - 2)])
STREAK_N = (re.findall(r"streak=(\d+)", st_cell) or [None])[-1]
PREV_STREAK = (re.findall(r"streak=(\d+)", st_prev) or [None])[-1]
STREAK_GIT = (re.findall(r"streak=(\d+)", st_this) or [None])[-1]
if None in (STREAK_N, PREV_STREAK, STREAK_GIT):
    die(u"读不到产品面连读的数：" + st_cell.strip()[-200:])

git_face, grc = sh([u"git", u"status", u"--porcelain"])
if grc != 0:
    die(u"git status 读不到")
CHANGED = [l for l in git_face.splitlines()
           if l.strip() and not l.startswith(u"?? .local/") and not l.startswith(u"?? .scratch/spikes/")]
PRODUCT = [l for l in CHANGED if u"/Sources/" in l]
if PRODUCT:
    die(u"这一支生成器是给零产品文件的分类账写的，改动面里有产品文件：%s" % PRODUCT[:3])

cv, crc = sh([sys.executable, CURVE])
if crc != 0:
    die(u"曲线尺不干净：" + cv.strip()[-300:])

# ──  正文 ───────────────────────────────────────────────────────────────────
UI_TITLE = (u"## 第 %d 轮（R%d · U-%d…U-%d · %s）：真机通道的「读不到」拆成三颗修法相反的缺席 ——"
            u"本轮现场被登录窗锁住（SecureInput 属主=loginwindow），旧句子把它报成了通道坏了"
            u"（U-%d…U-%d · 产品 0 文件，判据账）" % (AUDIT_N, ROUND, UA, UC, DATE, UA, UC))
UI_BODY = u"""
- **U-%d：`display_channel_state()` 现在分得开三种"读不到"** —— `display_off`（电源日志最近一条是关）/
  `screen_locked`（会话的 SecureInput 属主是 loginwindow）/ `capture_failed`（开着、没锁、还是截不出来）。
  本轮现场就是第二种：`pmset` 现读显示器 %s，而 `screencapture -R0,0,64,64` 抛
  CalledProcessError（could not create image from rect），`ioreg` 里
  `kCGSSessionSecureInputPID` 的属主现读 %s ⇒ 分类器给 `(False, %s)`，
  人话句："%s"。旧的那一句只会说"探针截图失败（CalledProcessError）"，
  读起来像**通道坏了** —— 按那句去修尺，就会去动一条没坏的尺。
- **U-%d：分类器只许读元数据，不许"再截一张全屏看看"** —— `secure_input_owner()` 只走
  `ioreg` + `ps -o comm=`。这一格拦的是形状而不是正确性：锁屏时全屏截图是**成功**的
  （它拍到的是用户的桌面），所以"能走通"和"该走"是两件事；
  这条仓库的红线是不采集用户屏幕上的内容，隐私红线在这里就是一条判据。
  证人：`test_the_classifier_is_metadata_only`（函数体里出现 screencapture 就红）。
- **U-%d：393 的真机那一半被这一颗挡住了** —— 用户授权退出 App（现读 `already_running` 已解除、
  实例已退），但会话锁着 ⇒ `REALSCREEN_NOT_RUN screen_locked`。
  尺不猜密码、不替用户解锁（D-322 的第三条），所以 393 的改前/改后四数本轮只能取到离屏那一半。
  判据卷 `test_real_screen_probe` 现读 `Ran %s tests` 全绿，刀 `%s`（逐臂 %s）。

""" % (UA, POWER, OWNER, CODE, WHY[:70], UB, UC, VOL_RAN, KNIFE_LINE, KNIFE_ARMS)

ITER_TITLE = (u"## Round %d · R%d（第 %d 轮 · %s）：真机那格的「读不到」从一句话拆成三颗 ——"
              u"本轮的靶被新拆出来的那颗挡住了（产品 0 文件 · 判据账）" % (ITER_N, ROUND, AUDIT_N, DATE))
ITER_BODY = u"""
用户这一轮的授权是"你自己退出 App，这段时间这台 Mac 随便你折腾"。我退了（`already_running` 这一格
因此解除），把显示器从睡眠里唤醒（`caffeinate -disu` 之后 `pmset` 现读 21:51 Display is turned on），
然后真机尺还是拿不到窗口 —— 而它报的是"探针截图失败（CalledProcessError）"。

这句话**不够**：它把三种修法相反的缺席压成了一句。显示器关着（等它开）、会话被登录窗锁住
（要人来解锁，尺不许猜密码）、屏幕录制授权坏了（要查工具）—— 三者的下一步动作完全不同。
本轮现场是第二种：`ioreg` 的 `kCGSSessionSecureInputPID` 属主现读 loginwindow（PID 与
`ps -o comm=` 对得上），而 `screencapture -R0,0,64,64` 被拒。

于是这一轮真正的产出不是 393 的数，而是那三种缺席各自的名字：
`display_off` / `screen_locked` / `capture_failed`，配三格真值表与两把刀
（M963 拿掉锁屏那一支、M964 拿掉通道那一支 —— 两把都红在本格，说明分类的**顺序**与**每一支**都有牙）。
分类只读元数据：锁屏时全屏截图是成功的，而它拍到的是用户的桌面 —— 那条路能走通但不该走，
所以它也被钉成一格（函数体里出现 `screencapture` 就红）。

看图这条腿本轮**没有新的视觉对象**：改动面只有 python，帧没重捕（四腿记 NOT-RUN），
而真机那一屏被锁屏挡住。这一维因此按"没有对象"给分，不按"看了但没问题"给分。

七维度自评：

| 维度 | 分/满分 |
| --- | --- |
| 真实视觉审查 | 6/15 |
| 判据有效性 | 14/15 |
| 假绿防御 | 15/15 |
| 产品面推进 | 2/15 |
| 台账一致性 | 13/15 |
| 交付诚实性 | 15/15 |
| 可复核性 | 14/15 |

合计 79/105。派生分由 `curve_from_ledger.py` 现读，不在这一节里手抄。

为什么真实视觉审查只有 6：本轮既没有新帧可看（0 个界面文件），也没有真机屏幕可量（锁屏）。
这一维低分不是"没做"，是**这一轮的产出不在视觉上**——而把它记成满分才是这仓库最怕的那种绿。

为什么产品面推进仍是 2 分：本轮 0 个产品文件（连读 %s 轮），而且 393 的靶本轮**没有推进**：
它被一颗新的具名出口挡住了。这不是把靶推迟的借口，是这一轮唯一诚实的读数。

为什么可复核性给 14：分类器与它的真值表都在仓库里，任何人解锁之后重跑那条尺都会拿到
`REALSCREEN_VERDICT` 或一个**有名字**的缺席；从"一句话失败"变成"三种失败各自可查"，
就是这一格涨的那几分。
""" % STREAK_N

D_BODY = (u"""
**D-%d（%d）："读不到"必须按**下一步动作**分，不按异常类型分；而分类用的信息只许取元数据**
：真机尺旧句子把 CalledProcessError 直接当成因打印，于是三种修法相反的缺席（等显示器开 / 等人解锁 /
查屏幕录制授权）共用一句话，下一轮就会去修一条没坏的尺。新的形状：
`classify_display_channel(power, secure_owner, region_ok)` 先问电源日志、再问会话属主、最后才问像素，
每一支对应一个动作；而 `secure_input_owner()` 只读 `ioreg` + `ps`，**不截屏** ——
锁屏时全屏截图是成功的（拍到的是用户桌面），"能走通"不等于"该走"，隐私红线在这里就是一条判据。
刀 M963/M964 各拿掉一支 ⇒ 真值表必须红（顺序与每一支都有牙）。
""" % (D1, ROUND))

BL_NEW = u"""**395. 真机通道被登录窗锁住：393 的 before/after 只取得到离屏那一半，屏幕那一半要等用户解锁（R332 现读 SecureInput 属主=loginwindow）**（R332）
    用户已授权退出 App（`already_running` 解除），显示器也被唤醒（`pmset` 现读 turned on），
    但 `screencapture -R0,0,64,64` 仍被拒 ⇒ 分类器给 `screen_locked`。
    尺不猜密码、不替用户解锁（D-322 第三条）。解锁之后要补的三格：
    ① 393 的改前真机四数（R330 那份是**另一趟**，不能当同一运行的改前用，D-318）；
    ② 改后真机四数 + 与离屏那卷同向；③ 392 那三格欠账（347/305 按下档、373 快速选取色、265 菜单栏悬停）。
    这一单不许被"离屏已经够了"结掉：377 的定性就是靠真机才从"通道产物"变成"产品画法"的。
"""

CHG_ENTRY = (u"### 真机通道的「读不到」拆成三颗修法相反的缺席：display_off / screen_locked / capture_failed"
             u"（R%d / U-%d…U-%d · 产品 0 文件，判据账）" % (ROUND, UA, UC)) + u"""

- `scripts/real_screen_sidebar_icons.py` 新增 `secure_input_owner()`（只读 ioreg + ps，不截屏）与
  `classify_display_channel(power, secure_owner, region_ok)`；`display_channel_state()` 改用它，
  人话句里带上"电源日志/属主/探针"三项现读。
- 现场：显示器现读 %s、区域截图抛 CalledProcessError、SecureInput 属主现读 %s ⇒ 分类 %s。
  旧句子"探针截图失败"读起来像通道坏了，而真因是会话锁着。
- 判据卷 `scripts/tests/test_real_screen_probe.py` 现读 `Ran %s tests` 全绿（新增 3 格：三成因真值表、
  属主非 loginwindow 不许算锁屏、分类器只读元数据）；刀 `mutate_r332.py` `%s`（逐臂 %s）。
- 393 的真机那一半因此挡住，开成 395；四腿 Swift 验证本轮没有对象（0 个 Swift/界面文件、帧未重捕），
  写成 NOT-RUN 而不是通过。
- 针预检 tables=%s covered=%s bad=%s、名册 files=%s arms=%s dupes=%s；脚本电池 `Ran %s（skipped=%s）`。
""" % (POWER, OWNER, CODE, VOL_RAN, KNIFE_LINE, KNIFE_ARMS,
       PRE[0], PRE[1], PRE[2], ARM_TOTAL[0], ARM_TOTAL[1], ARM_TOTAL[2], BATT, BATT_SKIP)

STATE_TITLE = u"## R%d 状态（%s · 本地 · 第 %d 轮 / Round %d）：真机那格的「读不到」拆成三颗 —— 本轮的靶被新拆出来的那颗挡住（产品 0 文件，判据账）" % (
    ROUND, DATE, AUDIT_N, ITER_N)
STATE_BODY = u"""
最后更新：%s（本地 · R%d / 第 %d 轮 / Round %d）：真机通道现读 `screen_locked`
（显示器 %s、SecureInput 属主 %s、区域截图被拒）⇒ 393 的屏幕那一半挡住，开成 395；
本轮把"读不到"拆成 display_off / screen_locked / capture_failed 三颗并配三格真值表与两把刀
（产品 0 文件 · 判据账 · 合计 79/105）

本轮做了什么：用户授权退出 App（`already_running` 解除）并唤醒显示器后，真机尺仍拿不到窗口，
而它报的是一句"探针截图失败（CalledProcessError）"。那句话把三种**修法相反**的缺席压成一种，
所以本轮的产出是那三种各自的名字：`classify_display_channel(power, secure_owner, region_ok)` +
`secure_input_owner()`（只读 ioreg/ps，不截屏）+ 三格真值表 + 两支刀。

验证读数（现读）：分类器 `(False, %s)`，人话句 `%s`；
判据卷 `Ran %s tests OK`；刀 `%s`（逐臂 %s）；
针预检 tables=%s covered=%s bad=%s、名册 files=%s arms=%s dupes=%s；
清账表 `%s`；脚本电池 `Ran %s（skipped=%s）`；
产品面连续零改动 **%s** 轮（唯一取数口 `python3 scripts/product_streak.py --streak-for %d`，`--check` 同形；
本轮这一笔按 `--streak-for %d` 现读是 %s，要等 commit 之后 git 才派生得出来；上一轮那一格是 %s）。

NOT-RUN（三种缺席分开写，不许省略）：① **本轮没有对象**的四腿 —— build 0 告警 / swift 判据卷 /
重捕帧 / 帧基线对账 / 换装本机：改动面 %s 个文件全是 python 与台账，0 个 Swift 文件，帧也没重捕；
② **只在人身上判得了**的：393 的改前/改后真机四数（会话锁着，尺不猜密码也不替用户解锁）⇒ 开成 395；
③ **命令没跑成**的：本轮没有 —— CI 对平留到 R%d 第 ⓪ 条现读。

下一轮（R%d）的靶，按顺序：⓪ 读 CI 配对（本轮 push 的 run↔commit 成对写回）→
① **393**：391 的落地只剩①—— 药丸换成 `unemphasizedSelectedContentBackgroundColor`
（参照臂量出的分母：解析 70／220 ≈ 系统实测 74.0／205.0），并把 `pillRun` 的
"药丸=与页底同档"重基成"药丸=两帧之间变了的那一档"（极性无关、不抄 `FilterPillGeometry`）；
硬断言只立**暗档同侧**（D-325：亮档的两机反号），R327…R329 打在 `pillRun` 与报告行上的针重钉重跑；
② 若用户已解锁：补 395 的三格（393 的改前/改后真机四数 + 392 的按下档/取色/菜单栏悬停）；
③ 390 的 before/after；④ 389 的时长；⑤ 384 的横轴那半；⑥ 387 的①；⑦ 376 剩那一半；
⑧ 367 迁移 / 360 最后一批 / 361 合并 / 364 六把抽不出的刀。
""" % (DATE, ROUND, AUDIT_N, ITER_N, POWER, OWNER, CODE, WHY[:90], VOL_RAN, KNIFE_LINE, KNIFE_ARMS,
       PRE[0], PRE[1], PRE[2], ARM_TOTAL[0], ARM_TOTAL[1], ARM_TOTAL[2],
       GATE_FULL.strip(), BATT, BATT_SKIP, STREAK_N, ROUND - 1, ROUND, STREAK_GIT, PREV_STREAK,
       s(len(CHANGED)), ROUND + 1, ROUND + 1)

# ──  落盘 ───────────────────────────────────────────────────────────────────
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
if BL_NEW.split(u"（R332）")[0] in blg:
    die(u"BACKLOG 已经有本轮那一单了")
wr(BLG, blg.rstrip(u"\n") + u"\n" + BL_NEW)

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
wr(STA, sta[:pos] + STATE_TITLE + u"\n" + STATE_BODY + u"\n" + sta[pos:])

fr = rd(FRA)
mUD = re.search(u"U-31 … U-(\\d+)", fr)
if not mUD:
    die(u"报告里找不到 U 区间那一格")
fr = once(fr, mUD.group(0), u"U-31 … U-%d" % UC)
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
             u"决定台账最大 **D-%d**，BACKLOG 最大 **%d**（本轮新开 %d：真机通道被锁屏挡住的那三格欠账）；"
             u"本轮刀 `%s`（%s）。§8 的读数搬运名单本轮**不适用** —— 改动面 0 个 Swift 文件，"
             u"新读数只在 python 尺里打印，没接进 `round_verify.sh`。"
             % (BATT, ARM_TOTAL[1], ARM_TOTAL[0], PRE[0], PRE[1], PRE[2], udefs, UC, D1, B1, B1,
                KNIFE_LINE, KNIFE_ARMS))
fr = fr.replace(scale_old[0], new_scale)
prod_old = re.findall(u"(?m)^- \\*\\*产品面（这一节最该被读的部分）\\*\\*：.*$", fr)
if len(prod_old) != 1:
    die(u"§13 的「产品面」命中 %d 行" % len(prod_old))
new_prod = (u"- **产品面（这一节最该被读的部分）**：本轮产品文件 0 个（**判据账**：改动面 %s 个文件，"
            u"产品 0 个、python 尺 1 个（`scripts/real_screen_sidebar_icons.py` 的成因分类）、判据卷 3 格、刀 2 把；"
            u"四腿 Swift 验证本轮没有对象，写成 NOT-RUN。"
            u"产品面连续零改动 **%s** 轮（唯一取数口 `python3 scripts/product_streak.py --streak-for %s`，"
            u"`--check` 同形；本轮这一笔按 `--streak-for %s` 现读是 %s，要等 commit 之后 git 才派生得出来）。"
            u"产品面连续零改动轮数 = **%s**。393 的屏幕那一半被 `screen_locked` 挡住，欠账开成 %d。"
            % (s(len(CHANGED)), STREAK_N, s(ROUND - 1), s(ROUND), STREAK_GIT, STREAK_N, B1))
fr = fr.replace(prod_old[0], new_prod)
fr = re.sub(u"(?m)^(- \\*\\*仍开（截至本轮，完整名单以 `AGENT_STATE.md` 的 R)\\d+( 节)",
            u"\\g<1>%d\\g<2>" % ROUND, fr, count=1)
if re.search(u"@\\w+@", fr):
    die(u"报告里还有没替换的占位符")
wr(FRA, fr)

# ──  写盘之后 ───────────────────────────────────────────────────────────────
rf0, rfc0 = sh([sys.executable, FRESH])
if rfc0 != 0 or u"REFUSED" in rf0:
    die(u"报告 §1 的刷新器没签：%s" % rf0.strip()[-300:])
print(u"SECTION1 " + rf0.strip().splitlines()[-1])
bt2, rc2 = sh([sys.executable, u"-m", u"unittest", u"discover", u"-s", u"scripts/tests"])
RAN2 = (re.findall(r"Ran (\d+) tests", bt2) or [None])[-1]
if rc2 != 0 or RAN2 != BATT:
    die(u"写盘后电池变了或红了（%s → %s）\n%s" % (BATT, RAN2, bt2.strip()[-900:]))
ck, ckc = sh([sys.executable, STREAK, u"--check"])
if ckc != 0:
    die(u"连读门不认这版台账：" + ck.strip()[-500:])
cv2, _ = sh([sys.executable, CURVE])
if (re.findall(r"^GAPS=(\S+)", cv2, re.M) or [u""])[-1] != u"none":
    die(u"写盘后曲线尺报缺口：" + cv2.strip()[-300:])
DERIVED = (re.findall(r"^DERIVED=(\S+)", cv2, re.M) or [None])[-1]
rf, rfc = sh([sys.executable, FRESH])
if rfc != 0 or u"REFUSED" in rf or u"未动" not in rf:
    die(u"报告 §1 刷新器第二遍不干净：%s" % rf.strip()[-300:])
chk, chkc = sh([sys.executable, u"-m", u"unittest", u"-v",
                u"test_final_report_headline.FinalReportHeadlineTests.test_the_headline_cells_agree_with_the_live_ledgers"],
               cwd=TESTS)
if chkc != 0:
    die(u"报告标题那几格与台账不同源：" + chk.strip()[-400:])

print(u"LEDGERS_R332 OK batt=Ran " + BATT + u" (skipped=" + BATT_SKIP + u") streak=" + STREAK_N
      + u"(上一轮 " + PREV_STREAK + u") 产品文件=0 改动面=" + s(len(CHANGED))
      + u" 刀=" + KNIFE_LINE + u" 臂=" + KNIFE_ARMS
      + u" 判据卷=Ran " + VOL_RAN + u" 成因=" + CODE + u" 属主=" + str(OWNER) + u" 电源=" + POWER
      + u" 预检 tables=" + PRE[0] + u" covered=" + PRE[1] + u" bad=" + PRE[2]
      + u" 在册=" + ARM_TOTAL[1] + u"/" + ARM_TOTAL[0]
      + u" U=" + s(UA) + u".." + s(UC) + u" D=" + s(D1) + u" BL=" + s(B1))
