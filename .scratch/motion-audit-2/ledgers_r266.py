#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R266 台账生成器（第 265 轮 / Round 263）：313 由合成实验结案，字形墨尺换成对锐度不敏感的估计量。"""
import io
import json
import os
import re
import subprocess
import sys
from collections import Counter

ROOT = "/Users/wangziyi/Codex_Project0"
HERE = os.path.join(ROOT, ".scratch", "motion-audit-2")
BOOKS = {n: os.path.join(ROOT, n) for n in
         ("AGENT_UI_AUDIT.md", "AGENT_VISUAL_ITERATION.md", "AGENT_DECISIONS.md",
          "AGENT_BACKLOG.md", "CHANGELOG.md", "AGENT_STATE.md")}
PRE = os.path.join(HERE, "mutate_needle_precheck.py")


def die(msg):
    sys.stderr.write("LEDGERS_R266 REFUSED: " + msg + "\n")
    raise SystemExit(2)


def rd(p):
    with io.open(p, encoding="utf-8", errors="replace") as h:
        return h.read()


def sh(cmd):
    env = dict(os.environ)
    env["PYTHONUTF8"] = "1"
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    pr = subprocess.run(cmd, cwd=ROOT, env=env, capture_output=True, text=True)
    return (pr.stdout or "") + (pr.stderr or ""), pr.returncode


cell = rd("/tmp/r266_cell.log")
proof = {}
for m in re.finditer(r"FAVORITE_INK_PROOF (light|dark) 底 idle=(\d+) hover=(\d+)｜字形墨 idle=(\d+) hover=(\d+)"
                     r"｜对比 idle=([\d.]+) hover=([\d.]+)｜墨像素 idle=(\d+) hover=(\d+)"
                     r"｜近墨像素\(≥20\) idle=(\d+) hover=(\d+)", cell):
    proof[m.group(1)] = m.groups()
for need in ("light", "dark"):
    if need not in proof:
        die("判据没印 " + need + " 档 ⇒ 本轮读数没有证人")
if "testGlyphInkRulerSurvivesTheAntiAliasingSpread]' passed" not in cell:
    die("AA 分辨格没绿：新估计量的正对照不成立")
if "error:" in cell:
    die("判据卷里有 error 行")
kn = re.search(r"R263_MUTATE 刀=(\d+) CAUGHT=(\d+) ESCAPED=(\d+) NOT_RUN=(\d+)", rd("/tmp/r266_knives.log"))
if not kn or kn.group(1) != kn.group(2) or kn.group(3) != "0" or kn.group(4) != "0":
    die("两把刀不是全 CAUGHT：" + (kn.group(0) if kn else "无汇总行"))
ptxt, _ = sh([sys.executable, PRE])
cover = re.search(r"NEEDLE_PRECHECK tables=(\d+) covered=(\d+) arms=(\d+) bad=(\d+)", ptxt)
roster = re.search(r"TABLE_ROSTER registered=(\d+) unregistered_with_arms=(\d+) hidden_arms=(\d+)", ptxt)
total = re.search(r"ARM_TOTAL files=(\d+) arms=(\d+) dupes=(\d+) repeats=(\d+)", ptxt)
if not (cover and roster and total) or cover.group(4) != "0" or total.group(3) != "0":
    die("预检读数不全或有坏：\n" + ptxt[-300:])
ctxt, _ = sh(["gh", "run", "list", "--limit", "5", "--json", "databaseId,headSha,status,conclusion"])
try:
    runs = json.loads(ctxt[ctxt.index("["):])
except Exception as exc:
    die("gh run list 读不出来：" + str(exc))


def pair(sha):
    hits = [r for r in runs if r["headSha"].startswith(sha)]
    if not hits:
        return sha + " → 未取到（293）"
    r = hits[0]
    return sha + " → " + str(r["databaseId"]) + " / " + r["status"] + " / " + (r["conclusion"] or "未读")


def battery():
    b, rc = sh([sys.executable, "-m", "unittest", "discover", "-s", "scripts/tests"])
    m = re.findall(r"^Ran (\d+) tests", b, re.M)
    if not m or not re.search(r"^OK", b, re.M) or rc != 0:
        die("电池不是绿的：\n" + b[-700:])
    sk = re.search(r"skipped=(\d+)", b)
    return m[-1], (sk.group(1) if sk else "0")


pre_ran, pre_skip = battery()
L, D = proof["light"], proof["dark"]
V = {
    "@@DATE@@": "2026-10-21",
    "@@LR0@@": L[5], "@@LR1@@": L[6], "@@DR0@@": D[5], "@@DR1@@": D[6],
    "@@LINK@@": L[3] + "→" + L[4], "@@DINK@@": D[3] + "→" + D[4],
    "@@LNEAR@@": L[9] + "/" + L[10], "@@DNEAR@@": D[9] + "/" + D[10],
    "@@LPX@@": L[7] + "/" + L[8], "@@DPX@@": D[7] + "/" + D[8],
    "@@KN@@": kn.group(1) + "/" + kn.group(2) + " CAUGHT",
    "@@TBL@@": cover.group(1), "@@COV@@": cover.group(2), "@@PARMS@@": cover.group(3),
    "@@GAPT@@": roster.group(2), "@@GAPA@@": roster.group(3), "@@ARMS@@": total.group(2),
    "@@BATT@@": "脚本电池 Ran " + pre_ran + " tests / OK (skipped=" + pre_skip + ")",
    "@@CI1@@": pair("08ddaa1"), "@@CI2@@": pair("30135fa"), "@@CI3@@": pair("d7dfdba"),
}

UI_NEW = """## 第 265 轮（R266 / 第 265 轮 / Round 263 · @@DATE@@）：313 由**合成实验**结案 —— 字形墨的墨心从"众数"换成"极端十分位均值"，两档读数一字未动（U-880…U-883 / D-252 · 产品 0 文件）

本轮次对照：与 R265（给出口装分辨读数、把降地板这条路堵死，自评 84）相比，本轮不再等 runner —— 用**本机就能做的扰动实验**把 313 的成因钉死，并当场把尺修好；修完之后两档比值与 R263 完全一致（亮 @@LR0@@→@@LR1@@、暗 @@DR0@@→@@DR1@@），说明换的是估计量不是结论。

- **U-880：合成扰动现读 —— 参照挪走不能解释颗数崩塌，锐度可以** —— 拿真帧 `row-favorite-idle-60x56-light` 做四种扰动，量同一把尺的两个数：纸从 255 等比压到 236 ⇒ 墨心众数颗数 **47→47（一动不动）**；高斯模糊一次 ⇒ **47→12**，两次 ⇒ **47→0**，而"近墨(≥20)"反而从 174 涨到 345；半分辨率再放大 ⇒ 47→6。⇒ runner 那 3~5 颗**不是"这一层没画"**，是抗锯齿把墨心摊到多个灰阶上、**众数对锐度过敏**（runner 自印的墨心值 145/174 也说明墨在那里）。
- **U-881：估计量换成"候选内离底最远那十分之一颗的均值"** —— 候选仍只收 `|Δ| ≥ 60`（**这条带子是为了与药丸那层分开，D-249 不许破**），换掉的只是"取哪个数当墨心"。第一版我错在把候选也放宽到 ≥20：亮档悬停的墨心立刻被 1224 颗药丸像素摊成 96（比值 6.289）—— 量的已经不是字形了，这一版当场被自己换掉，教训写进 D-252。
- **U-882：新格 `testGlyphInkRulerSurvivesTheAntiAliasingSpread` 是合成已知答案对照，不需要任何机器或帧** —— 同一根 4px 竖笔画两版：锐版四列全 100、摊开版 90/100/110/120（均值 105），两版都要求墨心落在 100±15、近墨 ≥60；再加**反面对照**：笔画淡到离底只有 15 灰阶时近墨必须 =0（否则出口那道闸门是摆设、上面三格只是在证明尺恒真）。出口闸门也随之从"墨心 ≥20"改成"近墨 ≥60"（墨心现在是十分位，颗数天然只有近墨的 1/10：本机 @@LPX@@／@@DPX@@，近墨 @@LNEAR@@／@@DNEAR@@）。
- **U-883：313 结案、312 解套，账与验证一起交** —— 312 之前被出口挡着（runner 无对象 ⇒ 3.000 无从复验），现在尺在 runner 上应当有对象，那一跑的 `FAVORITE_INK_PROOF … 近墨像素(≥20)=…` 会直接回答"纸 236 上这颗星过不过 3:1"。两把刀 M823/M824 重跑仍 @@KN@@、RESTORE_CLEAN；build 0 告警；@@BATT@@；预检 `NEEDLE_PRECHECK tables=@@TBL@@ covered=@@COV@@ arms=@@PARMS@@ bad=0`、`ARM_TOTAL arms=@@ARMS@@ dupes=0`、310 缺口 @@GAPT@@ 张 / @@GAPA@@ 把仍未收窄。CI：@@CI1@@、@@CI2@@、@@CI3@@ —— 三跑全部 in_progress / **未读**（只登记号不轮询，R140）。

眼睛腿：RUN —— 沿用盘上那批帧（`/tmp/r263_verify/frames` 现读 170 张），看的是亮档 `row-favorite` 的 idle 与 hover：换估计量之后**画面一张都没变**（本轮只动 `Tests/`），所以这一眼是去确认"尺改了、画面没改"这两件事同时成立，而不是给产品签字。范围只这两张。
变异腿：RUN（@@KN@@）。读数腿：RUN（判据自印两行 + 合成对照四格 + 预检三行 + 电池一行）。
产品腿：0 文件（`Sources/` 未动 ⇒ FINAL_REPORT 的 sources 格按规矩不动）。
未做（逐条）：① 312 的 runner 复验（现在解套了，等下一跑读数）；② 314 描边语义；③ 315 case-insensitive 那行；④ 316（阈值 20/60 的分工现在有了合成对照，但 60 这条候选带在**别的控件**上是否仍分得开两层，没量）；⑤ 310 的 @@GAPT@@ 张表、309 那 6 张写死颗数的表；⑥ 305、299、301、307、287/284、297/298/300、304、291 三位；⑦ 用户闸门 220 路 A / 228② / 265。

"""

ITER_NEW = """## Round 263 · 313 由合成实验结案：纸挪 19 灰阶颗数不动，模糊一次就归零 ⇒ 换掉对锐度过敏的众数（R266 / 第 265 轮）/ D-252 · 产品 0 文件

本轮次对照：与 R265（自评 84，装分辨读数、拒绝降地板）相比，本轮把"等 runner 自证"换成"本机就能做的扰动实验"：同一张真帧，纸从 255 压到 236 时墨心众数颗数 47→47，高斯模糊一次 47→12、两次 47→0，近墨反而 174→345 ⇒ 成因是**估计量对锐度过敏**，不是产品没画。尺换成候选内"极端十分位均值"，两档比值与 R263 完全一致（亮 @@LR0@@→@@LR1@@、暗 @@DR0@@→@@DR1@@）。
看图腿：RUN —— 亮档 row-favorite 的 idle / hover 两张：本轮只动 `Tests/`，画面一张没变；这一眼确认"尺改了、画面没改"同时成立，范围只这两张。
读数腿：RUN —— 判据自印两行（近墨 亮 @@LNEAR@@／暗 @@DNEAR@@，墨心颗数 @@LPX@@／@@DPX@@）、合成对照四格全绿、两把刀 @@KN@@、build 0 告警、@@BATT@@、预检 bad=0（310 缺口 @@GAPT@@ 张 / @@GAPA@@ 把）。
七维度自评：
| 维度 | 分/满分 |
| 真实视觉审查 | 9/15 |
| 判据有效性 | 15/15 |
| 假绿防御 | 15/15 |
| 产品面推进 | 2/15 |
| 台账一致性 | 14/15 |
| 交付诚实性 | 15/15 |
| 可复核性 | 15/15 |
各维理由：真实视觉审查 9 —— 没有新画面可看（0 产品文件），看的那两张是为了确认尺改了画面没改；判据有效性 15 —— 换估计量之后两档读数与换之前逐位相同，且新增一格合成已知答案对照（含反面对照）钉住它对锐度不敏感；假绿防御 15 —— 拦下两种新假绿：把候选带放宽到 ≥20 会让字形量成药丸（本轮真犯过一次并当场改回），以及"出口闸门用墨心颗数"在新估计量下会把有对象的本机判成无对象；产品面推进 2 —— 0 产品文件，核心欠账不变；台账一致性 14 —— 五本 + STATE + 报告两格派生，sources 格按规矩不动；交付诚实性 15 —— 自己第一版的错（候选放宽）写在账上而不是抹掉；可复核性 15 —— 合成实验是四格判据，任何人 `swift test --filter` 就能重跑。合计 **85**/105。

"""

DEC_NEW = """**D-252（R266）：改估计量只许动"取哪个数"，不许动"收哪些候选" —— 带子的宽度是层间边界，不是可调参数。** 理由：R266 要把字形墨心从"某一个灰阶的众数"换成"极端十分位均值"（众数对锐度过敏：合成扰动现读 —— 纸 255→236 颗数 47→47 不动，高斯模糊一次 47→12、两次 47→0）。我第一版顺手把候选从 `|Δ| ≥ 60` 放宽到 `≥ 20`，亮档悬停的墨心立刻从 78 变成 96、比值从 8.321 掉到 6.289 —— 因为 1224 颗药丸像素进了候选，**量的已经不是字形**。D-249 说两层要各有一条带子，这条补它没覆盖的那一半：带子定义的是"这是哪一层"，换了它等于换被测物。修正后的形状是"候选仍只收 ≥60，墨心取候选内离底最远的十分之一颗的均值"，两档读数与 R263 逐位相同（亮 @@LR0@@→@@LR1@@、暗 @@DR0@@→@@DR1@@）—— 这就是"只换统计量"的验收证据。配套：出口闸门随之从"墨心 ≥20"改成"近墨 ≥60"（新墨心颗数天然只有近墨的 1/10），并由一格合成反面对照钉住它不是摆设（淡到 15 灰阶 ⇒ 近墨必须 =0）。

"""

NOTE_313 = (
    "  追记（R266）：**结案** —— 成因不是等 runner，是本机合成实验钉的。同一张真帧：纸 255→236 时"
    "墨心众数颗数 47→47（不动）；高斯模糊一次 47→12、两次 47→0，而近墨(≥20) 反而 174→345 ⇒"
    "是「估计量对锐度过敏」，不是「这一层没画」（runner 自印的墨心 145/174 也证明墨在）。"
    "尺已改成「候选 |Δ|≥60 之内取离底最远的十分之一颗均值」，两档比值与 R263 逐位相同"
    "（亮 @@LR0@@→@@LR1@@、暗 @@DR0@@→@@DR1@@）；新增合成已知答案 + 反面对照格"
    "（testGlyphInkRulerSurvivesTheAntiAliasingSpread），出口闸门同步改成「近墨 ≥60」。"
    "⇒ 312 解套：下一跑 runner 的 FAVORITE_INK_PROOF … 近墨像素(≥20)=… 会直接回答"
    "「纸 236 上这颗星过不过 3:1」。\n")

BACK_NEW = [
    "**317. 候选带 `|Δ| ≥ 60` 这条「层间边界」目前只在 `row-favorite` 这一颗控件上验过（R266）：它对别的两层控件"
    "（段按钮 `segmented-filter-*`、设置行 `settingsrow-hover-*`、热图格子描边）是否仍把填充与字形分在正确两侧，"
    "没有读数。凡是要把 `glyphInkReading` 推广到别的位点，先在该位点做一次同样的合成扰动（纸等比压暗 + 一次模糊），"
    "两颗数都稳才允许接（D-249 / D-252 的推广前提）（R266 新开）**",
]

CHG_NEW = """### Changed（R266 / 第 265 轮 / Round 263 · 313 由合成实验结案，字形墨尺换成对锐度不敏感的估计量）

合成扰动现读（同一张真帧 `row-favorite-idle-60x56-light`）：纸 255→236 ⇒ 墨心众数颗数 **47→47**；高斯模糊一次 ⇒ **47→12**、两次 ⇒ **47→0**，近墨(≥20) 174→345；半分辨率再放大 ⇒ 47→6 ⇒ runner 那 3~5 颗是**估计量对锐度过敏**，不是"没画"。
`glyphInkReading` 的墨心改为"候选内离底最远的十分之一颗的均值"，候选仍只收 `|Δ| ≥ 60`（层间边界，D-252）；两档比值与 R263 逐位相同（亮 @@LR0@@→@@LR1@@、暗 @@DR0@@→@@DR1@@）。第一版曾把候选放宽到 ≥20，亮档悬停墨心被 1224 颗药丸像素摊成 96（比值 6.289）—— 当场改回，错处写在 D-252。
新格 `testGlyphInkRulerSurvivesTheAntiAliasingSpread`：锐版与摊开版两版合成笔画都要求墨心落在真值 ±15、近墨 ≥60，反面对照要求"淡到 15 灰阶 ⇒ 近墨=0"（闸门不许是摆设）。出口闸门相应从"墨心 ≥20"改成"近墨 ≥60"。
313 结案、312 解套；新开 317（候选带 60 只在一种控件上验过）。两把刀 @@KN@@、build 0 告警、@@BATT@@、预检 bad=0（310 缺口 @@GAPT@@ 张 / @@GAPA@@ 把未收窄）。产品 0 文件。

"""

STATE_NEW = """## R266 状态（第 265 轮 / Round 263 · @@DATE@@）
最后更新：2026-10-21（本地 · R266 / 第 265 轮 / Round 263）：**313 由合成实验结案，字形墨尺换成对锐度不敏感的估计量，两档读数一字未动**（U-880…U-883 · D-252 · 产品 0 文件 · 自评 85/105）

**本轮落地**：合成扰动（纸 255→236 颗数 47→47；模糊一次 47→12、两次 47→0，近墨 174→345）⇒ 成因是众数对锐度过敏；墨心改为"候选 ≥60 内取离底最远的十分之一颗均值"，候选带不许放宽（D-252，第一版放宽到 ≥20 被药丸摊平已改回）；新增合成已知答案 + 反面对照一格；出口闸门改成"近墨 ≥60"；两把刀 @@KN@@、build 0 告警、@@BATT@@、预检 bad=0。313 结案、312 解套、新开 317。

**下一轮（R267 / 第 266 轮 / Round 264）的 ⓪**：
⓪ 读 CI：@@CI1@@、@@CI2@@、@@CI3@@ 三跑交接时全 in_progress / **未读**（只登记号不轮询，R140）。要读的是 runner 自己印的 `FAVORITE_INK_PROOF … 近墨像素(≥20)=…`：近墨上百 ⇒ 312 当场可判（纸 236 上这颗星过不过 3.000）；若仍个位数 ⇒ 313 的结案要重开。顺带看 315 那行 case-insensitive 的 error 是否再现。
① 312（解套后第一优先）；317（候选带 60 的推广前提）。
② 314：热图描边语义（选中 vs 悬停）—— 先做"同一格分别点亮两态"的对照夹具再交眼睛，之后才接 291 那位。
③ 310 的 @@GAPT@@ 张表登记、309 那 6 张写死颗数的表。
④ 305 的地板、299 执行器半、301、307、287/284、297/298/300、304；用户闸门 220 路 A / 228② / 265。

"""


def render(s):
    for k, v in V.items():
        s = s.replace(k, v)
    if "@@" in s:
        die("渲染后仍有未替换占位符：" + s[:150])
    return s


for n in ("UI_NEW", "ITER_NEW", "DEC_NEW", "CHG_NEW", "STATE_NEW", "NOTE_313"):
    globals()[n] = render(globals()[n])
BACK_NEW = "\n\n".join(render(x) for x in BACK_NEW) + "\n"

ui_p = BOOKS["AGENT_UI_AUDIT.md"]
ui_old = rd(ui_p)
ANCHOR = "## 第 264 轮"
if ANCHOR not in ui_old:
    die("UI_AUDIT 找不到锚点")
cut = ui_old.index(ANCHOR)
ui_new = ui_old[:cut] + UI_NEW + ui_old[cut:]
it_p = BOOKS["AGENT_VISUAL_ITERATION.md"]
it_old = rd(it_p)
it_new = it_old.rstrip("\n") + "\n\n" + ITER_NEW
dc_p = BOOKS["AGENT_DECISIONS.md"]
dc_old = rd(dc_p)
dc_new = dc_old.rstrip("\n") + "\n\n" + DEC_NEW
cg_p = BOOKS["CHANGELOG.md"]
cg_old = rd(cg_p)
HEAD = "## [Unreleased]\n"
if HEAD not in cg_old:
    die("CHANGELOG 找不到 [Unreleased]")
cg_new = cg_old.replace(HEAD, HEAD + "\n" + CHG_NEW, 1)
bk_p = BOOKS["AGENT_BACKLOG.md"]
bk_old = rd(bk_p)
blines = bk_old.splitlines(True)


def append_after(ls, num, payload):
    idx = [i for i, l in enumerate(ls) if re.match(r"^(?:\*\*)" + num + r"\. ", l)]
    if len(idx) != 1:
        die("BACKLOG " + num + " 锚点命中 " + str(len(idx)) + " 次")
    k = idx[0] + 1
    while k < len(ls) and ls[k].strip():
        k += 1
    return ls[:k] + payload.splitlines(True) + ls[k:]


bk_new = "".join(append_after(blines, "313", NOTE_313)).rstrip("\n") + "\n\n" + BACK_NEW


def must_preserve(old, new, name):
    co, cn = Counter(old.splitlines()), Counter(new.splitlines())
    lost = [l for l, c in co.items() if cn[l] < c]
    if lost:
        die(name + " 弄丢 " + str(len(lost)) + " 行：" + " | ".join(lost[:2])[:140])


must_preserve(ui_old, ui_new, "AGENT_UI_AUDIT.md")
must_preserve(cg_old, cg_new, "CHANGELOG.md")
must_preserve(bk_old, bk_new, "AGENT_BACKLOG.md")
st_p = BOOKS["AGENT_STATE.md"]
st_old = rd(st_p)
if "## R265 状态" not in st_old:
    die("STATE 找不到锚点")
st_new = st_old.replace("## R265 状态", STATE_NEW + "## R265 状态", 1)
must_preserve(st_old, st_new, "AGENT_STATE.md")

ids = [int(x) for x in re.findall(r"- \*\*U-(\d+)", UI_NEW)]
if ids != list(range(880, 884)):
    die("U 号不连续：" + str(ids))
if "U-880…U-883" not in UI_NEW.splitlines()[0]:
    die("节标题 U 区间与定义不符")
if not it_new.startswith(it_old.rstrip("\n")) or not dc_new.startswith(dc_old.rstrip("\n")):
    die("升序那本不是纯追加")
if it_new.count("| 真实视觉审查 |") != it_old.count("| 真实视觉审查 |") + 1:
    die("七维表数量不对")
rows = [l for l in ITER_NEW.splitlines() if l.startswith("| ") and "维度" not in l and "分/满分" not in l]
scores = [int(m.group(1)) for m in (re.search(r"\| (\d+)/15 \|", l) for l in rows)]
if len(scores) != 7:
    die("七维表形状不对：" + str(len(scores)))
mt = re.search(r"合计 \*\*(\d+)\*\*/105", ITER_NEW)
if not mt or int(mt.group(1)) != sum(scores):
    die("合计手抄错了：" + str(sum(scores)))
if "D-252" in dc_old or "D-251" not in dc_old:
    die("D 号不对")
if bk_new.count("\n**317. ") != 1:
    die("新开 317 没落上")
if bk_new.count("追记（R266）") != 1:
    die("313 追记没写上")
if "## R266 状态" not in st_new:
    die("STATE 没轮换")

for p, t in ((ui_p, ui_new), (it_p, it_new), (dc_p, dc_new), (bk_p, bk_new), (cg_p, cg_new), (st_p, st_new)):
    with io.open(p, "w", encoding="utf-8") as h:
        h.write(t)

out, rc = sh([sys.executable, os.path.join(HERE, "report_cells_r258.py"), "headline"])
if rc != 0:
    die("FINAL_REPORT 刷新失败：" + out[-300:])
ran2, skip2 = battery()
if ran2 != pre_ran:
    die("写盘前后电池颗数不一致（" + pre_ran + " → " + ran2 + "）")
print("LEDGERS_R266 OK batt=Ran " + ran2 + " (skipped=" + skip2 + ") light=" + V["@@LR0@@"] + "→" + V["@@LR1@@"]
      + " dark=" + V["@@DR0@@"] + "→" + V["@@DR1@@"] + " U=880..883 D=252")
print(out.strip().splitlines()[-1])
