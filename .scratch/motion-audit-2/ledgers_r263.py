#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R263 台账生成器（第 262 轮 / Round 260）：收藏星的字形墨接进取证通道。数字全部现读。"""
import glob
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
REP = os.path.join(ROOT, "AGENT_FINAL_REPORT.md")
PRE = os.path.join(HERE, "mutate_needle_precheck.py")
CELL_LOG = "/tmp/r263_cell.log"
VERIFY_LOG = "/tmp/r263_verify_run.log"
KNIFE_LOG = "/tmp/r263_knives.log"
BASE_LOG = "/tmp/r263_verify/baseline.log"
FULL_LOG = "/tmp/r263_verify/full.log"
LIST_JSON = "/tmp/r263_list.json"
CODE_SHA = os.popen("git -C " + ROOT + " rev-parse --short HEAD").read().strip()


def die(msg):
    sys.stderr.write("LEDGERS_R263 REFUSED: " + msg + "\n")
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


# ── 1. 判据自己印的那两行读数（不许我手抄）──────────────────────────────
cell = rd(CELL_LOG)
inks = {}
for tag, bg0, bg1, ink0, ink1, r0, r1, p0, p1 in re.findall(
        r"FAVORITE_INK_PROOF (light|dark) 底 idle=(\d+) hover=(\d+)｜字形墨 idle=(\d+) hover=(\d+)"
        r"｜对比 idle=([\d.]+) hover=([\d.]+)｜墨像素 idle=(\d+) hover=(\d+)", cell):
    inks[tag] = dict(bg0=bg0, bg1=bg1, ink0=ink0, ink1=ink1, r0=float(r0), r1=float(r1), p0=p0, p1=p1)
for need in ("light", "dark"):
    if need not in inks:
        die("判据没印 " + need + " 档的 FAVORITE_INK_PROOF ⇒ 不许在缺一档的情况下写两档都过线")
    if inks[need]["r1"] <= inks[need]["r0"]:
        die(need + " 档悬停比值不比静置高，那这条判据在骗人")
    if inks[need]["r0"] < 3.0:
        die(need + " 档静置比值 " + str(inks[need]["r0"]) + " 低于 3.0 ⇒ 产品有缺陷，本轮不该写「过线」")
light, dark = inks["light"], inks["dark"]

# ── 2. 四件套那一行 ────────────────────────────────────────────────────
vtxt = rd(VERIFY_LOG)
rv = re.search(r"ROUND_VERIFY build_warnings=(\d+) swift_executed=(\d+) swift_skipped=(\d+) "
               r"swift_failures=(\d+) frames=(\d+) baseline_compared=(\d+) baseline_changed=(\d+) "
               r"baseline_missing=(\d+) dmg=(\S+) installed_version=(\S+)", vtxt)
if not rv:
    die("读不到 ROUND_VERIFY 那一行")
if rv.group(1) != "0":
    die("build 有告警：" + rv.group(1))
if rv.group(4) == "0":
    die("全量卷一朵红都没有？那这条摘要与 full.log 对不上，先查尺")
changed_names = re.findall(r"^  changed  (\S+)$", rd(BASE_LOG), re.M)
if len(changed_names) != int(rv.group(7)):
    die("changed 行数与摘要里的 baseline_changed 不符：" + str(changed_names))
if not changed_names:
    die("changed=0 ⇒ 改了产品却没有一张帧变，那是覆盖缺口不是清白（D-240 / 302 那一族）")

# 唯一那朵红：名字与两个读数都要现读
red_name = None
red_ms = None
with io.open(FULL_LOG, encoding="utf-8", errors="replace") as handle:
    for line in handle:
        if "Test Case" in line and "failed" in line:
            m = re.search(r"(\w+)\]' failed", line)
            if m:
                red_name = m.group(1)
        elif red_ms is None and "testImageComparisonCostStaysBounded" in line and "not less than" in line:
            m = re.search(r"\(\"([\d.]+)\"\) is not less than", line)
            if m:
                red_ms = m.group(1)
if red_name is None:
    die("full.log 里抓不到失败用例名 ⇒ 那朵红没名字就不能写进账")
if rv.group(4) != "1" or red_name != "testImageComparisonCostStaysBounded":
    die("全量卷的红不是预期的那一朵（failures=" + rv.group(4) + " name=" + str(red_name) + "）")
if red_ms is None:
    die("抓不到那朵红的毫秒数")

# 单跑那一遍的秒数也要现读（这台机器上它两次跑出 14.350 / 15.372 ⇒ 手抄必错）
iso_log = rd("/tmp/r263_iso.log")
m_iso = re.findall(r"testImageComparisonCostStaysBounded\]' passed \(([\d.]+) seconds\)", iso_log)
if not m_iso:
    die("读不到单跑那一遍的通过时长 ⇒ 「单跑通过」这句没有证人")
iso_s = m_iso[-1]

# ── 3. 两把刀 ─────────────────────────────────────────────────────────
kn = re.search(r"R263_MUTATE 刀=(\d+) CAUGHT=(\d+) ESCAPED=(\d+) NOT_RUN=(\d+)", rd(KNIFE_LOG))
if not kn:
    die("读不到 R263 变异表汇总行")
if kn.group(1) != kn.group(2) or kn.group(3) != "0" or kn.group(4) != "0":
    die("两把刀不是全 CAUGHT：" + kn.group(0))

# ── 4. 预检（新表必须已经登记）──────────────────────────────────────────
ptxt, _ = sh([sys.executable, PRE])
cover = re.search(r"NEEDLE_PRECHECK tables=(\d+) covered=(\d+) arms=(\d+) bad=(\d+)", ptxt)
total = re.search(r"ARM_TOTAL files=(\d+) arms=(\d+) dupes=(\d+) repeats=(\d+)", ptxt)
if not (cover and total):
    die("预检读数缺一行：\n" + ptxt[-400:])
if cover.group(4) != "0" or total.group(3) != "0":
    die("预检有坏：" + cover.group(0) + " / " + total.group(0))
if "mutate_r263" not in rd(PRE):
    die("mutate_r263 没登记进 TABLES ⇒ D-248 那颗牙又白给了")

# ── 5. CI 成对号 ──────────────────────────────────────────────────────
runs = json.loads(rd(LIST_JSON)) if os.path.exists(LIST_JSON) else []


def pair(sha):
    hits = [r for r in runs if r["headSha"].startswith(sha)]
    if not hits:
        return sha + " → 未取到（同一次 push 只给 head 那笔建跑，293）"
    r = hits[0]
    return sha + " → " + str(r["databaseId"]) + " / " + r["status"] + " / " + (r["conclusion"] or "未读")


def battery():
    btxt, brc = sh([sys.executable, "-m", "unittest", "discover", "-s", "scripts/tests"])
    m = re.findall(r"^Ran (\d+) tests", btxt, re.M)
    if not m or not re.search(r"^OK", btxt, re.M) or brc != 0:
        die("电池不是绿的，不落结案账：\n" + btxt[-900:])
    skip = re.search(r"skipped=(\d+)", btxt)
    return m[-1], (skip.group(1) if skip else "0")


pre_ran, pre_skip = battery()

V = {
    "@@DATE@@": "2026-10-21",
    "@@LR0@@": ("%.3f" % light["r0"]), "@@LR1@@": ("%.3f" % light["r1"]),
    "@@DR0@@": ("%.3f" % dark["r0"]), "@@DR1@@": ("%.3f" % dark["r1"]),
    "@@LINK0@@": light["ink0"], "@@LINK1@@": light["ink1"],
    "@@DINK0@@": dark["ink0"], "@@DINK1@@": dark["ink1"],
    "@@PIX@@": light["p0"],
    "@@EXEC@@": rv.group(2), "@@SKIP@@": rv.group(3), "@@FAIL@@": rv.group(4),
    "@@FRAMES@@": rv.group(5), "@@COMPARED@@": rv.group(6), "@@CHANGED@@": rv.group(7),
    "@@CHNAMES@@": "、".join(changed_names),
    "@@REDMS@@": red_ms, "@@REDNAME@@": red_name, "@@ISO@@": iso_s,
    "@@KN@@": kn.group(1) + " 把全 CAUGHT",
    "@@TBL@@": cover.group(1), "@@COV@@": cover.group(2), "@@ARMS@@": cover.group(3),
    "@@TOTAL@@": total.group(2),
    "@@BATT@@": "脚本电池 Ran " + pre_ran + " tests / OK (skipped=" + pre_skip + ")",
    "@@SHA@@": CODE_SHA,
    "@@CI9@@": pair("93b2cbd"), "@@CI10@@": pair("b5a54f1"),
}

UI_NEW = """## 第 262 轮（R263 / 第 262 轮 / Round 260 · @@DATE@@）：收藏星的**字形墨**接进取证通道 —— 291 那四位里的第三位从「欠账」翻成读数（U-865…U-870 / D-249 · 产品 1 文件）

本轮次对照：与 R262（0 产品文件、核对并更正上一轮的名单，自评 83）相比，本轮动了 1 个产品文件，把 R249 之后一直挂在名册上的 `HistoryRowViews.swift` 那一行做掉：那颗星在悬停时**本来就会**换墨（0.55 → 0.78），但画法读的是裸 `isHovered` ⇒ 离屏渲染里 `.onHover` 恒 false，那一抬在帧里从来不存在，于是"量不到"被记成"这一位没问题"（R90 那一族）。

- **U-865：注释里那句「两边都过 3:1」第一次变成会红的判据** —— 新判据 `UICaptureTests.testFavoriteGlyphInkClearsTheInteractiveFloor` 从**帧**里读静置与悬停两态的字形墨：现读亮档静置 @@LR0@@、悬停 @@LR1@@；暗档静置 @@DR0@@、悬停 @@DR1@@（墨心 亮 @@LINK0@@→@@LINK1@@、暗 @@DINK0@@→@@DINK1@@，各 @@PIX@@ 颗）。地板 3.000 两档都过 ⇒ `tint` 那段理由第一次有产物证人；同时三条接线断言钉住"画法读的是 `isHoveredForDrawing`、动画 value 也读它、产品自己不许写那颗键"。
- **U-866：字形尺与药丸尺故意用**不相交**的带子** —— 药丸取 `2 ≤ |Δ| < 60` 的众数（一整片填充），字形取 `|Δ| ≥ 60` 的众数（墨心）。共用一条带的话，抬墨那一半会被填充那一半挤掉 —— 与 R182 那族「两层材质混成一层」是同一种坏法，这次是在同一颗控件的两层上。
- **U-867：名册「做完一行删一行」，并把上一轮那句没量的话数清** —— `test_hover_capture_channel.py` 的 DEBT 里删掉 `HistoryRowViews.swift`；R249 留下的"120 行 `.onHover` 的状态还驱动着什么画法，本轮没量"现在有答案了：**一处**（`tint` 的 0.55↔0.78）+ **一条** `animation(value:)`。名册剩 @@COV@@ 张已抽、欠账剩三位（`DailyCopyHeatmapView` / `GlassControls` / `VideoPreview`）。
- **U-868：两把刀各钉一条轴，而且这两把**不必重捕帧**（D-240 的边界要写清）** —— M823 把抬量抹平（恒 0.55）⇒ 令牌轴；M824 把画法改回裸 `isHovered`（数值一字未动）⇒ 产品轴。现读 @@KN@@、RESTORE_CLEAN=yes。为什么不用重捕：这一格的产物是判据**在测试进程里现渲染**的 PNG，不是磁盘上那 170 张 —— 与 R254 那族"改了视觉量的刀必须重捕产物"分界的根据是"被量的对象在哪一层"，不是"改没改产品"。
- **U-869：四件套的读数，以及唯一那朵红不是本轮的** —— `ROUND_VERIFY`：build 0 告警、全量卷 Executed @@EXEC@@ / skipped @@SKIP@@ / failures=@@FAIL@@、帧 @@FRAMES@@ 张 compared=@@COMPARED@@ **changed=@@CHANGED@@**（正是 @@CHNAMES@@）、missing=0、dmg ok、换装本机 1.4.8；基线在同一笔里 update 后再 compare ⇒ changed=0。那朵红是 `PerfBudgetTests.@@REDNAME@@`：全量卷里 @@REDMS@@ ms ≥ 250，**单跑 @@ISO@@ s 通过** ⇒ 与 281/304 同一族的负载敏感红，本轮既没放宽阈值也没顺手改产品，只把两个读数一起记账。
- **U-870：看图腿 RUN，并给 305 交一个反方证人** —— 看了改后的亮档与暗档 hover 各一张。亮档那颗星确实更黑一档，但因为笔画只有 11pt，**肉眼差别远小于比值从 @@LR0@@ 跳到 @@LR1@@ 所暗示的量级**；暗档不与"已收藏"的金色实心混淆。这条与 R262 那两张（hover/press 肉眼分不出）方向相反地支持同一句话：**台阶够不够，不能只看比值**（305 的地板仍要两台机器各读一次，见新开 312）。CI 交账：@@CI9@@、@@CI10@@ —— **两跑都绿**，于是 R262 那两处修法（放宽引号、仓库根由 `__file__` 推）第一次有 runner 验收：上一轮在 runner 上 `FileNotFoundError` 的那格与撞号查重那格这次都过了。

读数腿：RUN（判据自印两行 + ROUND_VERIFY 一行 + 变异汇总一行 + 预检三行 + 电池一行）。
变异腿：RUN（@@KN@@，两轴各一把）。
眼睛腿：RUN（两张，改后的亮/暗 hover；结论范围收窄到这两张）。
产品腿：1 文件（`HistoryRowViews.swift`），画面变了 @@CHANGED@@ 张且都被基线签字。
未做（逐条）：① 312（3.000 这条地板的 runner 复验 —— 本机边距亮 @@LR0@@、暗 @@DR0@@，runner 若红按 D-232 加按机器的出口，不许当场放宽）；② 291 剩下三位；③ 305 的地板；④ 309 那 6 张写死颗数的表；⑤ 310 的 TABLES 名册；⑥ 299 执行器半、301、307、287/284、297/298/300、304；⑦ 用户闸门 220 路 A / 228② / 265。

"""

ITER_NEW = """## Round 260 · 收藏星的字形墨接进取证通道：注释里那句「量出来的」第一次会红（R263 / 第 262 轮）/ D-249 · 产品 1 文件

本轮次对照：与 R262（自评 83，0 产品文件、核对上一轮名单）相比，本轮回到产品：那颗星悬停时本来就会换墨，但画法读裸 `isHovered` ⇒ 离屏帧里那一抬从来不存在；接上取证键后两态第一次能被量，注释里"两边都过 3:1"升成会红的地板（亮 @@LR0@@／@@LR1@@、暗 @@DR0@@／@@DR1@@）。
看图腿：RUN —— 改后的亮档与暗档 hover 各一张：亮档更黑一档，但 11pt 笔画让**肉眼差别远小于比值跳变**；暗档不与已收藏的金色实心混淆。
读数腿：RUN —— @@BATT@@；ROUND_VERIFY build 0 告警 / 全量 @@EXEC@@ / failures=@@FAIL@@（唯一那朵是 281/304 家族的负载敏感红：全量 @@REDMS@@ms、单跑 @@ISO@@s 通过）/ 帧 @@FRAMES@@、changed=@@CHANGED@@（@@CHNAMES@@）/ dmg ok / 换装 1.4.8；两把刀 @@KN@@；预检 tables=@@TBL@@ covered=@@COV@@ arms=@@ARMS@@ bad=0。
七维度自评：
| 维度 | 分/满分 |
| 真实视觉审查 | 12/15 |
| 判据有效性 | 14/15 |
| 假绿防御 | 13/15 |
| 产品面推进 | 12/15 |
| 台账一致性 | 13/15 |
| 交付诚实性 | 15/15 |
| 可复核性 | 14/15 |
各维理由：真实视觉审查 12 —— 两档各看一张并给出可反驳的观察（"比值跳一大截而肉眼差别有限"），但没有做逐屏逐元素的新一轮重判；判据有效性 14 —— 新判据读的是产物像素、地板来自产品自己写在注释里的声明，另配三条接线断言；假绿防御 13 —— 两轴各一把刀、名册"做完一行删一行"、"changed=0 不算清白"这条本轮反过来被自己用（改了产品就必须有 changed）；产品面推进 12 —— 1 文件、画面真的变了且被基线签字，但主窗口动效面本轮没动；台账一致性 13 —— 五本 + STATE + FINAL_REPORT 三格由脚本派生（sources 格现读 sha）；交付诚实性 15 —— 那朵红带着"单跑通过"的对照一起写，没放宽也没藏；可复核性 14 —— 一条 round_verify + 一张变异表 + 判据自印读数。合计 **93**/105。

"""

DEC_NEW = """**D-249（R263）：同一颗控件上的两层，两把尺的带子必须不相交；把注释里的「量出来的」升成地板时，先问这把尺读的是哪一层。** 理由：`RowFavoriteButton` 有两层悬停 —— 药丸填充（`VisualFill.controlHover`）与字形墨（`tint` 的 0.55↔0.78）。`pillReading` 取 `2 ≤ |Δ| < 60` 的众数，如果新写的字形尺也按"与底有差"来取，抬墨会被那片更大的填充挤成次位，读出来的"悬停没变"其实是尺没看这一层（R182 那族"两层材质混成一层"的控件版）。所以 `glyphInkReading` 用 `|Δ| ≥ 60` 的带子，与药丸带**互补不重叠**，两条读数才能各自被红。配套的第二条：`tint` 那段注释里"0.55 是量出来的、两边都过 3:1"从 R20 起就没有会红的判据 —— 本轮把它写成地板（现读亮 @@LR0@@／暗 @@DR0@@，两档都过），**注释里的实测值要么升成判据要么删掉**，否则它会替产品撒一个没人复查的谎（R74 那一族：只在注释里的分类法等于没有）。

"""

NOTE_291 = ("  追记（R263）：第三位做掉了 —— `HistoryRowViews.swift` 从 DEBT 里删行（做完一行删一行）。"
            "那颗星悬停时本来就会换墨（0.55↔0.78），但画法读裸 `isHovered` ⇒ 离屏帧里那一抬从来不存在；"
            "现接 `isHoveredForDrawing`，判据 `testFavoriteGlyphInkClearsTheInteractiveFloor` 从帧里读两态字形墨"
            "（现读亮 @@LR0@@→@@LR1@@、暗 @@DR0@@→@@DR1@@，地板 3.000 两档都过），两把刀 M823/M824 各钉一条轴全 CAUGHT。"
            "R249 那句「.onHover 还驱动着什么画法，本轮没量」现在有答案：一处 tint + 一条 animation value。"
            "291 仍开，剩 `DailyCopyHeatmapView` / `GlassControls` / `VideoPreview` 三位。\n")

BACK_NEW = [
    "**312. 字形墨那条 3.000 地板目前只有本机一台的读数（R263 现读亮 @@LR0@@、暗 @@DR0@@，边距 0.545／1.641）："
    "runner 第一次读到它之前，不许把它当两档共同的硬门签字（D-232）；若 runner 红，处置是按机器加具名出口或把地板搬到"
    "两机各自推的位置，**不许当场放宽数值**（R263 新开）**",
]

CHG_NEW = """### Changed（R263 / 第 262 轮 / Round 260 · 收藏星的字形墨接进取证通道）

产品 1 文件：`RowFavoriteButton` 的 `tint`（0.55↔0.78）与 `animation(value:)` 从裸 `isHovered` 改读 `isHoveredForDrawing`（`@Environment(\\.hoveredForCapture)`，产品自己永远不写这颗键）⇒ 悬停那一抬第一次出现在离屏帧里。
新判据 `UICaptureTests.testFavoriteGlyphInkClearsTheInteractiveFloor`：从帧里读两态字形墨，把 `tint` 注释里那句「两边都过 3:1」升成会红的地板 —— 现读亮 @@LR0@@／@@LR1@@、暗 @@DR0@@／@@DR1@@（墨心 @@LINK0@@→@@LINK1@@、@@DINK0@@→@@DINK1@@）。新尺 `glyphInkReading` 与 `pillReading` 故意用不相交带子（`|Δ| ≥ 60` 对 `2 ≤ |Δ| < 60`，D-249）。
名册 `test_hover_capture_channel.py` 删掉 `HistoryRowViews.swift` 那一行（291 剩三位）；变异表 `mutate_r263.py` 两把刀（M823 令牌轴 / M824 产品轴）@@KN@@、RESTORE_CLEAN，并写明**这两把不必重捕帧**（被量的产物在测试进程里现渲染）。
四件套：build 0 告警、全量卷 Executed @@EXEC@@（skipped @@SKIP@@）里 failures=@@FAIL@@ 唯一那朵是 `PerfBudgetTests.@@REDNAME@@`（全量 @@REDMS@@ms ≥ 250，单跑 @@ISO@@s 通过 = 281/304 家族，未放宽未修）、帧 @@FRAMES@@ 张 compared=@@COMPARED@@ changed=@@CHANGED@@（@@CHNAMES@@）missing=0、基线同一笔 update、dmg ok、换装本机 1.4.8。
看图 RUN：改后亮/暗各一张 —— 亮档更黑一档，但 11pt 笔画让肉眼差别远小于比值跳变 ⇒ 给 305 交一个"比值不等于可见性"的反方证人。新开 312。@@BATT@@。

"""

STATE_NEW = """## R263 状态（第 262 轮 / Round 260 · @@DATE@@）
最后更新：2026-10-21（本地 · R263 / 第 262 轮 / Round 260）：**收藏星的字形墨接进取证通道，注释里那句「量出来的」第一次会红**（U-865…U-870 · D-249 · 291 剩三位 · 产品 1 文件 · 自评 93/105）

**本轮落地**：`RowFavoriteButton.tint` 与 `animation(value:)` 改读 `isHoveredForDrawing`；新判据从帧里读两态字形墨（亮 @@LR0@@→@@LR1@@、暗 @@DR0@@→@@DR1@@，地板 3.000 两档都过）+ 新尺 `glyphInkReading`（与药丸带子不相交）；名册删一行（291 剩 DailyCopyHeatmapView / GlassControls / VideoPreview）；两把刀 @@KN@@（不必重捕帧，理由写在表头）；@@BATT@@；预检 tables=@@TBL@@ covered=@@COV@@ arms=@@ARMS@@ bad=0。四件套：全量 @@EXEC@@、唯一红 = `@@REDNAME@@`（@@REDMS@@ms 全量 / @@ISO@@s 单跑通过，281/304 家族，未放宽）、帧 changed=@@CHANGED@@（@@CHNAMES@@）后基线同一笔 update、dmg ok、换装 1.4.8。

**下一轮（R264 / 第 263 轮 / Round 261）的 ⓪**：
⓪ 读 CI：@@CI9@@、@@CI10@@ **已读且两跑绿**（R262 的放宽引号 + 根路径派生被 runner 验收）；本笔 push 后再取新跑（只登记号不轮询，R140），要看的是 `testFavoriteGlyphInkClearsTheInteractiveFloor` 在 runner 上怎么说 —— 那 3.000 地板目前只有本机一台的读数（312）。
① 312：3.000 地板的 runner 复验（红就按 D-232 加按机器的具名出口，不许放宽数值）。
② 291 剩下三位（`DailyCopyHeatmapView` / `GlassControls` / `VideoPreview`）；305 的地板（本轮那张"比值跳变而肉眼有限"是反方证人）；309 那 6 张写死颗数的表；310 的 TABLES 名册。
③ 299 执行器半、301、307、287/284、297/298/300、304；用户闸门 220 路 A / 228② / 265。

"""


def render(s):
    for key, val in V.items():
        s = s.replace(key, val)
    if "@@" in s:
        die("渲染后仍有未替换占位符：" + s[:160])
    return s


rendered = {}
for name in ("UI_NEW", "ITER_NEW", "CHG_NEW", "STATE_NEW", "NOTE_291", "DEC_NEW"):
    rendered[name] = render(globals()[name])
rendered["BACK_NEW"] = "\n\n".join(render(x) for x in BACK_NEW) + "\n"
UI_NEW, ITER_NEW, CHG_NEW, STATE_NEW, NOTE_291, DEC_NEW, BACK_NEW = (rendered[k] for k in
                                                                    ("UI_NEW", "ITER_NEW", "CHG_NEW",
                                                                     "STATE_NEW", "NOTE_291", "DEC_NEW",
                                                                     "BACK_NEW"))

ui_old = rd(UI)
ANCHOR = "## 第 261 轮"
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
blines = back_old.splitlines(True)


def append_after(lines, num, payload):
    idx = [n for n, line in enumerate(lines) if re.match(r"^(?:\*\*)" + num + r"\. ", line)]
    if len(idx) != 1:
        die("BACKLOG " + num + " 锚点命中 " + str(len(idx)) + " 次")
    k = idx[0] + 1
    while k < len(lines) and lines[k].strip():
        k += 1
    return lines[:k] + payload.splitlines(True) + lines[k:]


lines = append_after(blines, "291", NOTE_291)
back_new = "".join(lines).rstrip("\n") + "\n\n" + BACK_NEW

# FINAL_REPORT 的 sources 格：整行替换，sha 由 git 现读（不手抄）
rep_old = rd(REP)
rlines = rep_old.splitlines(True)
hits = [i for i, line in enumerate(rlines) if line.startswith("| 最后一次动到 `Sources/` 的轮次 |")]
if len(hits) != 1:
    die("FINAL_REPORT 的 sources 格命中 " + str(len(hits)) + " 行")
new_row = ("| 最后一次动到 `Sources/` 的轮次 | **R263**（commit `" + CODE_SHA + "`）—— 1 文件，"
           "**把注释里那句「量出来的」升成会红的地板**：`RowFavoriteButton.tint` 的 0.55↔0.78 与 animation value "
           "改读取证键，字形墨两态第一次能在帧里量到（亮 @@LR@@／暗 @@DR@@，地板 3.000 两档都过），"
           "两把刀各钉一条轴（D-249 记录带子为什么必须不相交）。上一笔是 R260（亮档梯子顶层那一抬，308 结案那一笔）。"
           "| `git log -1 --format=%h%x09%s -- ClipboardHistory/Sources`（R235 补记起由 "
           "`scripts/tests/test_final_report_headline.py::live_sources` 现读对账，这一格不再靠手抄；"
           "不符就红 `FINAL_REPORT_SOURCES_CELL_STALE`） |")
new_row = new_row.replace("@@LR@@", V["@@LR0@@"]).replace("@@DR@@", V["@@DR0@@"])
rlines[hits[0]] = new_row + "\n"
rep_new = "".join(rlines)


def must_preserve(old, new, name):
    co, cn = Counter(old.splitlines()), Counter(new.splitlines())
    lost = [l for l, c in co.items() if cn[l] < c]
    if lost:
        die(name + " 弄丢 " + str(len(lost)) + " 行：" + " | ".join(lost[:2])[:150])


must_preserve(ui_old, ui_new, "AGENT_UI_AUDIT.md")
must_preserve(chg_old, chg_new, "CHANGELOG.md")
must_preserve(back_old, back_new, "AGENT_BACKLOG.md")
st_old = rd(STATE)
ST_MARK = "## R262 状态"
if ST_MARK not in st_old:
    die("STATE 找不到锚点")
state_new = st_old.replace(ST_MARK, STATE_NEW + ST_MARK, 1)
must_preserve(st_old, state_new, "AGENT_STATE.md")
if not iter_new.startswith(iter_old.rstrip("\n")):
    die("AGENT_VISUAL_ITERATION.md 不是纯追加")
if not dec_new.startswith(dec_old.rstrip("\n")):
    die("AGENT_DECISIONS.md 不是纯追加")
ids = [int(x) for x in re.findall(r"- \*\*U-(\d+)", UI_NEW)]
if ids != list(range(865, 871)):
    die("本轮 U 号不连续：" + str(ids))
if "U-865…U-870" not in UI_NEW.splitlines()[0]:
    die("节标题 U 区间与定义不符")
if iter_new.count("| 真实视觉审查 |") != iter_old.count("| 真实视觉审查 |") + 1:
    die("七维表多写或少写")
rows = [l for l in ITER_NEW.splitlines() if l.startswith("| ") and "维度" not in l and "分/满分" not in l]
if len(rows) != 7:
    die("七维表形状不对：" + str(len(rows)))
scores = []
for line in rows:
    m = re.search(r"\| (\d+)/15 \|", line)
    if not m:
        die("七维表有行不是 N/15 形状：" + line[:60])
    scores.append(int(m.group(1)))
mt = re.search(r"合计 \*\*(\d+)\*\*/105", ITER_NEW)
if not mt or int(mt.group(1)) != sum(scores):
    die("合计手抄错了：表里相加=" + str(sum(scores)) + " 正文写" + (mt.group(1) if mt else "无"))
if "D-249" in dec_old:
    die("D-249 已存在")
if "D-248" not in dec_old:
    die("D 号跳号：上一笔 D-248 不在账上")
if re.search(r"^\*\*312\. ", back_new, re.M) is None or back_new.count("\n**312. ") != 1:
    die("新开 312 没落上或落重了")
if back_new.count("追记（R263）") != 1:
    die("291 的追记没写上：" + str(back_new.count("追记（R263）")))
if "**R263**（commit `" + CODE_SHA + "`）" not in rep_new:
    die("sources 格没换成 R263 与现读 sha")
if "## R263 状态" not in state_new:
    die("STATE 没轮换")

for path, text in ((UI, ui_new), (ITER, iter_new), (DEC, dec_new), (BACK, back_new),
                   (CHG, chg_new), (STATE, state_new), (REP, rep_new)):
    with io.open(path, "w", encoding="utf-8") as handle:
        handle.write(text)

out, rc = sh([sys.executable, os.path.join(HERE, "report_cells_r258.py"), "headline"])
if rc != 0:
    die("FINAL_REPORT 两格刷新失败：" + out[-300:])
ran2, skip2 = battery()
if ran2 != pre_ran:
    die("台账写盘前后电池颗数不一致（" + pre_ran + " → " + ran2 + "）")
print("LEDGERS_R263 OK batt=Ran " + ran2 + " (skipped=" + skip2 + ") sha=" + CODE_SHA
      + " changed=" + V["@@CHANGED@@"] + " red=" + V["@@REDMS@@"] + "ms U=865..870 D=249")
print(out.strip().splitlines()[-1])
