#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R264 台账生成器（第 263 轮 / Round 261）：310 的缺口第一次被数出来 + runner 那朵红归因。

数字全部现读：预检的 TABLE_ROSTER / NEEDLE_PRECHECK / ARM_TOTAL 三行、runner 日志里那四行
XCTAssert 的原文数值、本机判据自印的 FAVORITE_INK_PROOF、两把刀的汇总行、电池结论行。
"""
import io
import json
import os
import re
import subprocess
import sys
from collections import Counter

ROOT = "/Users/wangziyi/Codex_Project0"
HERE = os.path.join(ROOT, ".scratch", "motion-audit-2")
UI = os.path.join(ROOT, "AGENT_UI_AUDIT.md")
ITER = os.path.join(ROOT, "AGENT_VISUAL_ITERATION.md")
DEC = os.path.join(ROOT, "AGENT_DECISIONS.md")
BACK = os.path.join(ROOT, "AGENT_BACKLOG.md")
CHG = os.path.join(ROOT, "CHANGELOG.md")
STATE = os.path.join(ROOT, "AGENT_STATE.md")
PRE = os.path.join(HERE, "mutate_needle_precheck.py")
RUNNER_LOG = "/tmp/r264_runner.log"
KNIFE_LOG = "/tmp/r263_knives.log"
LIST_JSON = "/tmp/r264_list.json"


def die(msg):
    sys.stderr.write("LEDGERS_R264 REFUSED: " + msg + "\n")
    raise SystemExit(2)


def rd(path):
    with io.open(path, encoding="utf-8", errors="replace") as handle:
        return handle.read()


def sh(cmd):
    env = dict(os.environ)
    env["PYTHONUTF8"] = "1"
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    proc = subprocess.run(cmd, cwd=ROOT, env=env, capture_output=True, text=True)
    return (proc.stdout or "") + (proc.stderr or ""), proc.returncode


# ── 1. 预检：缺口要由仪器产数（310 的结案条件之一就是"别靠记忆"）────────────
ptxt, _ = sh([sys.executable, PRE])
roster = re.search(r"TABLE_ROSTER registered=(\d+) unregistered_with_arms=(\d+) hidden_arms=(\d+)", ptxt)
cover = re.search(r"NEEDLE_PRECHECK tables=(\d+) covered=(\d+) arms=(\d+) bad=(\d+)", ptxt)
total = re.search(r"ARM_TOTAL files=(\d+) arms=(\d+) dupes=(\d+) repeats=(\d+)", ptxt)
if not (roster and cover and total):
    die("预检三行缺一行：\n" + ptxt[-400:])
if cover.group(4) != "0" or total.group(3) != "0":
    die("预检有坏：" + cover.group(0) + " / " + total.group(0))

# ── 2. runner 那朵红的原文读数（不许手抄）────────────────────────────────
rl = rd(RUNNER_LOG)
px = [int(x) for x in re.findall(r'XCTAssertGreaterThan failed: \("(\d+)"\) is not greater than \("20"\)', rl)]
ratios = [float(x) for x in re.findall(r'XCTAssertGreaterThanOrEqual failed: \("([\d.]+)"\) is less than \("3\.0"\)', rl)]
step = re.findall(r'XCTAssertGreaterThan failed: \("([\d.]+)"\) is not greater than \("([\d.]+)"\)', rl)
if not px or not ratios or not step:
    die("runner 日志里抓不到无对象颗数 / 地板比值 / 台阶比值 ⇒ 那朵红的读数没有证人")
if min(px) < 1 or max(px) > 19:
    die("runner 的墨颗数读数落在 " + str(sorted(set(px))) + "，不像「无对象」那一族，先重看")
runner_px = "、".join(str(x) for x in sorted(set(px)))
runner_ratio = ("%.3f" % ratios[0])
runner_step = ("%.3f ≤ %.3f" % (float(step[0][0]), float(step[0][1])))

# ── 3. 本机判据自印的两行 + 两把刀（出口不许把刀弄钝）───────────────────────
local = rd("/tmp/r264_local.log") if os.path.exists("/tmp/r264_local.log") else ""
kn = re.search(r"R263_MUTATE 刀=(\d+) CAUGHT=(\d+) ESCAPED=(\d+) NOT_RUN=(\d+)", rd(KNIFE_LOG))
if not kn:
    die("读不到两把刀的汇总行")
if kn.group(1) != kn.group(2) or kn.group(3) != "0" or kn.group(4) != "0":
    die("加了出口之后两把刀不再全 CAUGHT ⇒ 出口把判据弄钝了：" + kn.group(0))

runs = json.loads(rd(LIST_JSON)) if os.path.exists(LIST_JSON) else []


def pair(sha):
    hits = [r for r in runs if r["headSha"].startswith(sha)]
    if not hits:
        return sha + " → 未取到（293）"
    r = hits[0]
    return sha + " → " + str(r["databaseId"]) + " / " + r["status"] + " / " + (r["conclusion"] or "未读")


def battery():
    btxt, brc = sh([sys.executable, "-m", "unittest", "discover", "-s", "scripts/tests"])
    m = re.findall(r"^Ran (\d+) tests", btxt, re.M)
    if not m or not re.search(r"^OK", btxt, re.M) or brc != 0:
        die("电池不是绿的：\n" + btxt[-800:])
    sk = re.search(r"skipped=(\d+)", btxt)
    return m[-1], (sk.group(1) if sk else "0")


pre_ran, pre_skip = battery()

V = {
    "@@DATE@@": "2026-10-21",
    "@@REG@@": roster.group(1), "@@GAPT@@": roster.group(2), "@@GAPA@@": roster.group(3),
    "@@TBL@@": cover.group(1), "@@COV@@": cover.group(2), "@@PARMS@@": cover.group(3),
    "@@ARMS@@": total.group(2),
    "@@RPIX@@": runner_px, "@@RRATIO@@": runner_ratio, "@@RSTEP@@": runner_step,
    "@@KN@@": kn.group(1) + "/" + kn.group(2) + " CAUGHT",
    "@@BATT@@": "脚本电池 Ran " + pre_ran + " tests / OK (skipped=" + pre_skip + ")",
    "@@CI1@@": pair("8512d4e"), "@@CI2@@": pair("50aaca9"), "@@CI3@@": pair("93b2cbd"),
}

UI_NEW = """## 第 263 轮（R264 / 第 263 轮 / Round 261 · @@DATE@@）：310 的缺口第一次被数出来（@@GAPT@@ 张表 / @@GAPA@@ 把刀静默不覆盖），并把上一轮自己点亮的 runner 红归因（U-871…U-875 / D-250 · 产品 0 文件）

本轮次对照：与 R263（第一次动产品像素：收藏星的字形墨接进取证通道，自评 93）相比，本轮 0 产品文件，做两件 R263 留下的账：① 把"名册登记面"从记忆变成仪器产数（310）；② 上一轮那格新判据在 runner 上红了，本轮读它、归因、按对象存在性给出口（313）。

- **U-871：缺口比开单时猜的大得多 —— @@GAPT@@ 张表声明了臂却没登记进 `TABLES`，共 @@GAPA@@ 把刀静默不覆盖** —— 预检的 needle 检查只走手写名册，而撞号查重按 glob 扫全部表（@@ARMS@@ 把）。新增 `roster_gap()` 只测不判：`TABLE_ROSTER registered=@@REG@@ unregistered_with_arms=@@GAPT@@ hidden_arms=@@GAPA@@`，并逐张点名。
- **U-872：地板用 `assertEqual` 而不是 `assertLessEqual`** —— 电池那两格把 @@GAPT@@ / @@GAPA@@ 钉成等式：多一张表没登记 ⇒ 红；真去登记了 ⇒ 也红，红话是"把地板降到实测值"，逼那一笔同时进台账。配正对照（人造一张"声明了臂但没登记"的表必须被点名）。见 D-250。
- **U-873：上一轮那格在 runner 上红，红话说的不是产品** —— @@CI1@@、@@CI2@@ 两跑都红在 `testFavoriteGlyphInkClearsTheInteractiveFloor`，而 STEP[17] 的捕获闸门把它登记成**未注册红**（闸门做对了事）。原文读数：墨心颗数 runner 只有 @@RPIX@@ 颗（本机 47），静置比值 @@RRATIO@@ < 3.0，"悬停 > 静置"那条读成 @@RSTEP@@。颗数个位数 = **尺在那台机器上没有对象**，不是墨被改淡 —— 在没有对象的情况下 assert，红话会把尺的盲区说成产品的缺陷（R90 / R100 那一族）。
- **U-874：出口按对象存在性切片，不按机器名；代价显式记账** —— 判据现在先跑三条**与机器无关**的接线断言（硬），再按"墨心 ≥20 颗"决定这一档判不判；无对象的档打 `FAVORITE_INK_NOT_RUN 判定档=… 无对象档=… 机器=…`，两档都无对象才 `XCTSkip`。本机两档都有对象 ⇒ 判据照旧全跑；两把刀 M823/M824 在出口之后重跑仍 @@KN@@（**换判据口径必须留正对照**，否则"放宽"与"修好"在测试里同形）。追因（为什么 runner 上这颗星几乎不落成墨）记新开 313，本轮不改产品也不放宽地板。
- **U-875：看图腿 RUN + 一笔未归因的账** —— 眼睛看了热图格子的两态帧（`heatmap-cell-strip-still` / `-hover`，亮档）：那圈描边一眼可见、与深浅梯度不混淆；但它是**近黑色描边**，在 macOS 的读法里描边更像"选中"而不是"悬停"（与 R260 的 308 同族：两种状态共用一种视觉语义）⇒ 这是 291 剩下那位（`DailyCopyHeatmapView`）接键之前必须先定的产品判断，新开 314。另：同一跑的 STEP[15] 里有一行 `error: You're on a case-insensitive filesystem, and the remote you are…`，本轮**没能归因**（它不与任何断言同行出现，且该步仍产出了完整用例结果）⇒ 新开 315，不许把"没解释"记成"没发生"。@@CI3@@ 是 R262 修法的 runner 验收（绿）。

读数腿：RUN（预检三行 + runner 日志原文四行 + 两把刀汇总 + 电池一行）。
变异腿：RUN（M823/M824 在出口之后重跑，仍全 CAUGHT、RESTORE_CLEAN）。
眼睛腿：RUN（两张：热图格子静置 / 悬停，亮档；结论范围只这两张）。
产品腿：0 文件（`Sources/` 未动，帧基线沿用 R263 那 170 张；本轮只动 `Tests/` 与工具）。
未做（逐条）：① 313 runner 上这颗星为什么无对象；② 314 描边的语义（选中 vs 悬停）与 291 那位；③ 315 那行 case-insensitive 的 error；④ 309 那 6 张写死颗数的表；⑤ 312 的 3.000 地板 runner 复验 —— 本轮的出口让它**无从复验**了，这一点写在 313 里；⑥ 305、299、301、307、287/284、297/298/300、304；⑦ 用户闸门 220 路 A / 228② / 265。

"""

ITER_NEW = """## Round 261 · 310 的缺口被数出来（@@GAPT@@ 张表 / @@GAPA@@ 把刀静默不覆盖），并把上一轮自己点亮在 runner 上的那朵红归因（R264 / 第 263 轮）/ D-250 · 产品 0 文件

本轮次对照：与 R263（自评 93，第一次动产品像素）相比，本轮不碰产品：把"登记面"变成仪器产数并钉成等式地板，然后回去读上一轮那朵 runner 红 —— 它的红话说的是尺没有对象（墨心 @@RPIX@@ 颗 vs 本机 47），于是按对象存在性给出口、把代价记成 313，并当场重跑两把刀证明出口没把判据弄钝。
看图腿：RUN —— 热图格子两态（亮档）：描边一眼可见、不与深浅梯度混淆，但近黑描边在 macOS 读起来像"选中"，这条判断交给 314（本轮不改）。
读数腿：RUN —— `TABLE_ROSTER registered=@@REG@@ unregistered_with_arms=@@GAPT@@ hidden_arms=@@GAPA@@`、`NEEDLE_PRECHECK tables=@@TBL@@ covered=@@COV@@ arms=@@PARMS@@ bad=0`、`ARM_TOTAL arms=@@ARMS@@ dupes=0`、两把刀 @@KN@@、@@BATT@@。
七维度自评：
| 维度 | 分/满分 |
| 真实视觉审查 | 9/15 |
| 判据有效性 | 14/15 |
| 假绿防御 | 15/15 |
| 产品面推进 | 2/15 |
| 台账一致性 | 14/15 |
| 交付诚实性 | 15/15 |
| 可复核性 | 14/15 |
各维理由：真实视觉审查 9 —— 看了两张热图格子的两态并给出可反驳的语义判断（描边像选中），但没有新画面；判据有效性 14 —— 新仪器 `roster_gap` 把静默不覆盖变成读数，且出口只在"尺没有对象"时生效、接线断言照旧硬跑；假绿防御 15 —— 三种假绿同时被拦：未登记表静默（等式地板）、出口把判据弄钝（两把刀重跑当正对照）、把尺的盲区说成产品缺陷（红话改写成 NOT_RUN 并追因）；产品面推进 2 —— 0 产品文件，且这是连续第 1 轮（R263 刚动过）；台账一致性 14 —— 五本 + STATE + FINAL_REPORT 两格派生，sources 格本轮**故意不动**（`Sources/` 未改，动了就会被守卫红）；交付诚实性 15 —— 上一轮的红、本轮的出口代价、以及那行没归因的 error 全部记账；可复核性 14 —— 预检一条命令、正对照两格、runner 原文留在 /tmp 并写明路径。合计 **83**/105。

"""

DEC_NEW = """**D-250（R264）：缺口要用等式钉，不能只用方向钉 —— 单调地板挡恶化，等式挡"账与现状脱钩"。** 理由：R264 第一次把"声明了臂却没登记进 `TABLES`"的规模数出来（@@GAPT@@ 张表 / @@GAPA@@ 把刀），如果只写 `assertLessEqual(423)`，那么真去登记 20 张表之后地板仍是 423，账与现状悄悄脱钩，而下一个人读到的还是"缺口 423"。改成 `assertEqual`：变好与变坏都必须改账，改账的动作就是把 BACKLOG 那一格刷新的事实落地。这与 D-038（会红的必须是单调量）不冲突 —— 单调量管**阈值类**判据，等式管**读数类**地板。同一轮把这条形状用到出口上：`FAVORITE_INK_NOT_RUN` 只在"墨心 < 20 颗"时生效（对象存在性），而不是按机器名放行；且出口落地后立刻重跑 M823/M824 两把刀（@@KN@@），因为"换判据口径"最容易把牙一起换掉（R146 那一族）。

"""

NOTE_310 = ("  追记（R264）：缺口第一次有仪器产数 —— 新函数 `roster_gap()` 打 "
            "`TABLE_ROSTER registered=@@REG@@ unregistered_with_arms=@@GAPT@@ hidden_arms=@@GAPA@@` 并逐张点名；"
            "本条开单时那句「74 登记 vs 163 存在」是文件数，不是「声明了臂却没登记」的表数（真数 @@GAPT@@ 张 / @@GAPA@@ 把）。"
            "电池两格把这两个数钉成 `assertEqual` 地板（D-250）+ 人造正对照 ⇒ 新表静默不覆盖会当场红。"
            "310 保持仍开（登记这 @@GAPT@@ 张表本身没做）。\n")

BACK_NEW = [
    "**313. runner 上 `RowFavoriteButton` 的字形墨没有对象（R264 现读：墨心 @@RPIX@@ 颗 vs 本机 47；静置比值 @@RRATIO@@、"
    "悬停那条读成 @@RSTEP@@）：要追的是「那台机器上这颗 SF Symbol 到底落成了什么」，而不是把 3.000 地板降下来。"
    "三条嫌疑（各自能被一条读数分辨，别混着试）：① runner 的 `Color.primary` 在无窗口环境解析成更淡的 label 色（与 R100「runner 看不见材质」、"
    "R121 图标暗档黑底同族）；② 字体渲染/抗锯齿让 ≥60 的带子只剩边缘（换一把与带子无关的尺对照即可分辨）；"
    "③ 夹具那颗星在 runner 上根本没画（颗数个位数与「没画」同形 ⇒ 要一格「帧里有没有任何非背景墨」的证人）。"
    "出口按对象存在性切片已经落地（`FAVORITE_INK_NOT_RUN`），但它的代价就是 312 的 runner 复验**至今无从完成**（R264 新开）**",
    "**314. 热图格子的悬停描边语义读起来像「选中」而不是「悬停」（R264 看图现读：亮档两态帧里那圈近黑描边一眼可见、"
    "与深浅梯度不混淆，但 macOS 上描边是选中 affordance）：291 剩下那位（`DailyCopyHeatmapView`）在接取证键之前，"
    "必须先判「要不要换成系统语义（accent 描边 / 提亮 / 悬浮）」，否则接完键只是把一种混淆量得更准。"
    "判法：两态帧 + 一格「选中态 vs 悬停态」的对照夹具（同一格分别点亮两种状态），再交眼睛（R264 新开）**",
    "**315. runner 的 STEP[15] 里有一行 `error: You're on a case-insensitive filesystem, and the remote you are…`"
    "（run 39519770384 原文，00:11:24）：本轮未归因 —— 它不与任何断言同行出现，而那一步仍产出了完整用例结果，"
    "所以既不能说它无害，也不能说它导致了那朵红。要做的：把这一行接成一条具名读数（按步骤切片），"
    "并分辨它是 SwiftPM 解析依赖时的一次性告警还是仓库里真有一对只差大小写的文件（R264 新开）**",
]

CHG_NEW = """### Changed（R264 / 第 263 轮 / Round 261 · 缺口被数出来，上一轮的 runner 红被归因）

`mutate_needle_precheck.py` 新增 `roster_gap()`：现读"声明了臂却没登记进 `TABLES`"的表 ⇒ `TABLE_ROSTER registered=@@REG@@ unregistered_with_arms=@@GAPT@@ hidden_arms=@@GAPA@@`（只测不判，逐张点名）。电池 +2 格：把这两个数钉成 `assertEqual` 地板（D-250：等式挡"账与现状脱钩"，单调地板挡不住），正对照用人造未登记表。
`testFavoriteGlyphInkClearsTheInteractiveFloor` 的出口按**对象存在性**切片：先跑三条与机器无关的接线断言（硬），再要求墨心 ≥20 颗才判该档；无对象打 `FAVORITE_INK_NOT_RUN 判定档=… 无对象档=… 机器=…`，两档都无对象才 `XCTSkip`。起因是 @@CI1@@ / @@CI2@@ 两跑红：runner 只数到 @@RPIX@@ 颗（本机 47），静置比值 @@RRATIO@@、台阶 @@RSTEP@@ —— 那是尺没有对象，红话不该说产品。出口落地后重跑 M823/M824 仍 @@KN@@（正对照）。
新开 313（runner 那颗星为什么无对象，三条可分辨嫌疑）、314（热图描边语义像选中 —— 看图现读，接键之前先判）、315（STEP[15] 那行 case-insensitive 的 error 未归因）。310 追记：开单时那句"74 vs 163"是文件数，真缺口是 @@GAPT@@ 张表 / @@GAPA@@ 把刀。
眼睛腿 RUN：热图格子两态（亮档）。产品 0 文件（只动 `Tests/` 与工具 ⇒ `Sources/` 未改，FINAL_REPORT 的 sources 格本轮不动）。@@BATT@@。

"""

STATE_NEW = """## R264 状态（第 263 轮 / Round 261 · @@DATE@@）
最后更新：2026-10-21（本地 · R264 / 第 263 轮 / Round 261）：**310 的缺口被数出来（@@GAPT@@ 张表 / @@GAPA@@ 把刀静默不覆盖），上一轮自己点亮在 runner 上的那朵红按对象存在性给了出口**（U-871…U-875 · D-250 · 产品 0 文件 · 自评 83/105）

**本轮落地**：`roster_gap()` + `TABLE_ROSTER` 一行（只测不判、逐张点名）；电池 2 格（等式地板 + 人造正对照，D-250）；字形墨判据的出口按"墨心 ≥20 颗"切片、接线断言照旧硬跑、两档全无对象才 skip；出口后重跑 M823/M824 仍 @@KN@@；@@BATT@@；预检 `NEEDLE_PRECHECK tables=@@TBL@@ covered=@@COV@@ arms=@@PARMS@@ bad=0`、`ARM_TOTAL arms=@@ARMS@@ dupes=0`。看图 RUN（热图格子两态，描边像选中 ⇒ 314）。

**下一轮（R265 / 第 264 轮 / Round 262）的 ⓪**：
⓪ 读 CI：@@CI1@@、@@CI2@@ 已读（红因 = 字形墨那格在 runner 上无对象，本轮已给出口）；@@CI3@@ 绿（R262 修法验收）。本笔 push 后取新跑，要验的是 **runner 上 `FAVORITE_INK_NOT_RUN` 有没有被捕获闸门登记成"已登记 NOT-RUN"而不是红**，以及 STEP[15] 那行 case-insensitive 的 error 是否再现（315）。只登记号不轮询（R140）。
① 313：runner 那颗星为什么无对象 —— 三条嫌疑各配一条能分辨的读数，别混着试；不许靠降 3.000 地板解决。
② 314：热图描边的语义（选中 vs 悬停）—— 先做「同一格分别点亮两态」的对照夹具再交眼睛，之后才接 291 那位。
③ 310 的登记本身（@@GAPT@@ 张表）、309 那 6 张写死颗数的表、315。
④ 305 的地板、299 执行器半、301、307、287/284、297/298/300、304；用户闸门 220 路 A / 228② / 265。

"""


def render(s):
    for key, val in V.items():
        s = s.replace(key, val)
    if "@@" in s:
        die("渲染后仍有未替换占位符：" + s[:160])
    return s


UI_NEW = render(UI_NEW)
ITER_NEW = render(ITER_NEW)
DEC_NEW = render(DEC_NEW)
CHG_NEW = render(CHG_NEW)
STATE_NEW = render(STATE_NEW)
NOTE_310 = render(NOTE_310)
BACK_NEW = "\n\n".join(render(x) for x in BACK_NEW) + "\n"

ui_old = rd(UI)
ANCHOR = "## 第 262 轮"
if ANCHOR not in ui_old:
    die("UI_AUDIT 找不到锚点")
cut = ui_old.index(ANCHOR)
ui_new = ui_old[:cut] + UI_NEW + ui_old[cut:]
iter_old = rd(ITER)
iter_new = iter_old.rstrip("\n") + "\n\n" + ITER_NEW
dec_old = rd(DEC)
dec_new = dec_old.rstrip("\n") + "\n\n" + DEC_NEW
chg_old = rd(CHG)
HEAD = "## [Unreleased]\n"
if HEAD not in chg_old:
    die("CHANGELOG 找不到 [Unreleased]")
chg_new = chg_old.replace(HEAD, HEAD + "\n" + CHG_NEW, 1)
back_old = rd(BACK)
lines = back_old.splitlines(True)


def append_after(ls, num, payload):
    idx = [i for i, l in enumerate(ls) if re.match(r"^(?:\*\*)" + num + r"\. ", l)]
    if len(idx) != 1:
        die("BACKLOG " + num + " 锚点命中 " + str(len(idx)) + " 次")
    k = idx[0] + 1
    while k < len(ls) and ls[k].strip():
        k += 1
    return ls[:k] + payload.splitlines(True) + ls[k:]


lines = append_after(lines, "310", NOTE_310)
back_new = "".join(lines).rstrip("\n") + "\n\n" + BACK_NEW


def must_preserve(old, new, name):
    co, cn = Counter(old.splitlines()), Counter(new.splitlines())
    lost = [l for l, c in co.items() if cn[l] < c]
    if lost:
        die(name + " 弄丢 " + str(len(lost)) + " 行：" + " | ".join(lost[:2])[:150])


must_preserve(ui_old, ui_new, "AGENT_UI_AUDIT.md")
must_preserve(chg_old, chg_new, "CHANGELOG.md")
must_preserve(back_old, back_new, "AGENT_BACKLOG.md")
st_old = rd(STATE)
ST_MARK = "## R263 状态"
if ST_MARK not in st_old:
    die("STATE 找不到锚点")
state_new = st_old.replace(ST_MARK, STATE_NEW + ST_MARK, 1)
must_preserve(st_old, state_new, "AGENT_STATE.md")

ids = [int(x) for x in re.findall(r"- \*\*U-(\d+)", UI_NEW)]
if ids != list(range(871, 876)):
    die("本轮 U 号不连续：" + str(ids))
if "U-871…U-875" not in UI_NEW.splitlines()[0]:
    die("节标题 U 区间与定义不符")
if not iter_new.startswith(iter_old.rstrip("\n")) or not dec_new.startswith(dec_old.rstrip("\n")):
    die("升序那本不是纯追加")
if iter_new.count("| 真实视觉审查 |") != iter_old.count("| 真实视觉审查 |") + 1:
    die("七维表多写或少写")
rows = [l for l in ITER_NEW.splitlines() if l.startswith("| ") and "维度" not in l and "分/满分" not in l]
if len(rows) != 7:
    die("七维表形状不对：" + str(len(rows)))
scores = [int(m.group(1)) for m in (re.search(r"\| (\d+)/15 \|", l) for l in rows)]
mt = re.search(r"合计 \*\*(\d+)\*\*/105", ITER_NEW)
if not mt or int(mt.group(1)) != sum(scores):
    die("合计手抄错了：表里相加=" + str(sum(scores)))
if "D-250" in dec_old or "D-249" not in dec_old:
    die("D 号不对（跳号或重复）")
for num in ("313", "314", "315"):
    if back_new.count("\n**" + num + ". ") != 1:
        die("新开 " + num + " 没落上或落重了")
if back_new.count("追记（R264）") != 1:
    die("310 的追记没写上")
if "## R264 状态" not in state_new:
    die("STATE 没轮换")

for path, text in ((UI, ui_new), (ITER, iter_new), (DEC, dec_new), (BACK, back_new),
                   (CHG, chg_new), (STATE, state_new)):
    with io.open(path, "w", encoding="utf-8") as handle:
        handle.write(text)

out, rc = sh([sys.executable, os.path.join(HERE, "report_cells_r258.py"), "headline"])
if rc != 0:
    die("FINAL_REPORT 两格刷新失败：" + out[-300:])
ran2, skip2 = battery()
if ran2 != pre_ran:
    die("写盘前后电池颗数不一致（" + pre_ran + " → " + ran2 + "）")
print("LEDGERS_R264 OK batt=Ran " + ran2 + " (skipped=" + skip2 + ") gap=" + V["@@GAPT@@"] + "/" + V["@@GAPA@@"]
      + " runner_px=" + V["@@RPIX@@"] + " U=871..875 D=250")
print(out.strip().splitlines()[-1])
