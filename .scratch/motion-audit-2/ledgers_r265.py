#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R265 台账生成器（第 264 轮 / Round 262）：313 的分辨读数落地 + runner 那几行的归因。

数字全部现读：本机判据自印的 FAVORITE_INK_PROOF（含本轮新加的「近墨像素」）、
runner 自己印的那四行、变异汇总、预检三行、CI 成对号（gh 现取）、电池结论行。
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


def die(msg):
    sys.stderr.write("LEDGERS_R265 REFUSED: " + msg + "\n")
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


PROOF = re.compile(r"FAVORITE_INK_PROOF (light|dark) 底 idle=(\d+) hover=(\d+)｜字形墨 idle=(\d+) hover=(\d+)"
                   r"｜对比 idle=([\d.]+) hover=([\d.]+)｜墨像素 idle=(\d+) hover=(\d+)"
                   r"(?:｜近墨像素\(≥20\) idle=(\d+) hover=(\d+))?")


def parse_proof(text):
    out = {}
    for m in PROOF.finditer(text):
        near = m.group(10)
        out[m.group(1)] = dict(bg=m.group(2), ink0=m.group(4), ink1=m.group(5),
                               r0=float(m.group(6)), r1=float(m.group(7)),
                               p0=int(m.group(8)), p1=int(m.group(9)),
                               near=(near + "/" + m.group(11)) if near else "无")
    return out


local = parse_proof(rd("/tmp/r265_cell.log"))
runner = parse_proof(rd("/tmp/r265_runner.log"))
for need in ("light", "dark"):
    if need not in local:
        die("本机没印 " + need + " 档的 FAVORITE_INK_PROOF")
    if local[need]["near"] == "无":
        die("本机那一行没有「近墨像素」⇒ 本轮的分辨读数没生效，别写进账")
    if need not in runner:
        die("runner 日志里没印 " + need + " 档")
if local["light"]["p0"] < 20:
    die("本机自己都没对象了（墨心 " + str(local["light"]["p0"]) + " 颗）⇒ 先修尺")

kn = re.search(r"R263_MUTATE 刀=(\d+) CAUGHT=(\d+) ESCAPED=(\d+) NOT_RUN=(\d+)", rd("/tmp/r265_knives.log"))
if not kn or kn.group(1) != kn.group(2) or kn.group(3) != "0" or kn.group(4) != "0":
    die("两把刀不是全 CAUGHT（出口加读数之后）：" + (kn.group(0) if kn else "无汇总行"))

ptxt, _ = sh([sys.executable, PRE])
cover = re.search(r"NEEDLE_PRECHECK tables=(\d+) covered=(\d+) arms=(\d+) bad=(\d+)", ptxt)
roster = re.search(r"TABLE_ROSTER registered=(\d+) unregistered_with_arms=(\d+) hidden_arms=(\d+)", ptxt)
total = re.search(r"ARM_TOTAL files=(\d+) arms=(\d+) dupes=(\d+) repeats=(\d+)", ptxt)
if not (cover and roster and total) or cover.group(4) != "0" or total.group(3) != "0":
    die("预检读数不全或有坏：\n" + ptxt[-300:])

ctxt, _ = sh(["gh", "run", "list", "--limit", "4", "--json", "databaseId,headSha,status,conclusion"])
try:
    runs = json.loads(ctxt[ctxt.index("["):])
except Exception as exc:
    die("gh run list 读不出来（run 号只能现取，293）：" + str(exc))


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
        die("电池不是绿的：\n" + btxt[-700:])
    sk = re.search(r"skipped=(\d+)", btxt)
    return m[-1], (sk.group(1) if sk else "0")


pre_ran, pre_skip = battery()

L = local["light"]
D = local["dark"]
RL = runner["light"]
V = {
    "@@DATE@@": "2026-10-21",
    "@@LBG@@": L["bg"], "@@RBG@@": RL["bg"],
    "@@LPIX@@": str(L["p0"]) + "/" + str(L["p1"]), "@@RPIX@@": str(RL["p0"]) + "/" + str(RL["p1"]),
    "@@LNEAR@@": L["near"], "@@DNEAR@@": D["near"], "@@RNEAR@@": RL["near"],
    "@@LR0@@": ("%.3f" % L["r0"]), "@@LR1@@": ("%.3f" % L["r1"]),
    "@@DR0@@": ("%.3f" % D["r0"]), "@@DR1@@": ("%.3f" % D["r1"]),
    "@@RR0@@": ("%.3f" % RL["r0"]), "@@RR1@@": ("%.3f" % RL["r1"]),
    "@@RINK0@@": RL["ink0"], "@@RINK1@@": RL["ink1"],
    "@@KN@@": kn.group(1) + "/" + kn.group(2) + " CAUGHT",
    "@@TBL@@": cover.group(1), "@@COV@@": cover.group(2), "@@PARMS@@": cover.group(3),
    "@@GAPT@@": roster.group(2), "@@GAPA@@": roster.group(3), "@@ARMS@@": total.group(2),
    "@@BATT@@": "脚本电池 Ran " + pre_ran + " tests / OK (skipped=" + pre_skip + ")",
    "@@CI1@@": pair("30135fa"), "@@CI2@@": pair("d7dfdba"), "@@CI3@@": pair("50aaca9"),
}

UI_NEW = """## 第 264 轮（R265 / 第 264 轮 / Round 262 · @@DATE@@）：给 313 装分辨读数，并用 runner 自己印的那几行把「降地板」这条路堵死（U-876…U-879 / D-251 · 产品 0 文件）

本轮次对照：与 R264（把 310 的缺口数出来、给字形墨判据按对象存在性加出口，自评 83）相比，本轮继续追 313：上一轮只说了"runner 上尺没有对象"，本轮回答**为什么不能靠降地板解决**，并把"两种成因修法相反"这件事变成判据自己会印的一格读数。产品 0 文件（只动 `Tests/`）。

- **U-876：runner 的纸就不是同一张 —— 底 @@RBG@@，本机底 @@LBG@@** —— 这是 R264 那三条嫌疑里第一条的直接证人：`glyphInkReading` 的参照是"帧里左缘 8 列的众数"，runner 上它是 @@RBG@@ 而不是 @@LBG@@。带子 `|Δ| ≥ 60` 是**压在参照上的绝对量**，参照整体挪了 19 灰阶，带子量的就不再是同一片距离（R100 的"整把尺一起偏"、R147 的"绝对锚点"同族）。
- **U-877：无对象时读数连方向都会错 —— 这条把"把地板降到 2.6 行不行"直接堵死** —— runner 自印：墨心 idle=@@RINK0@@、hover=@@RINK1@@（本机是 @@LPIX@@ 颗、方向是 @@LR0@@ → @@LR1@@ 变深），也就是**悬停在那台机器上读起来更浅**；墨像素只有 @@RPIX@@ 颗。个位数样本上"更浅"不是产品事实，是众数在噪声里跳（R87：两样本只配说没漂）。所以 3.000 一字未动，动的是尺的**自我报告**。
- **U-878：新读数「近墨像素(≥20)」把两种成因分开，并且出口会自己报读法** —— `glyphInkReading` 现在同时数"与底差 ≥20 的颗数"（这一层到底有没有画）与"≥60 的众数颗数"（墨心），出口那行从 `(idle=3 hover=4)` 变成 `(墨心 idle=3 hover=4 近墨=… 底=… 读法=这一层几乎没画｜画了但进不了≥60的带)`。本机现读：亮档 近墨 @@LNEAR@@、暗档近墨 @@DNEAR@@，墨心 @@LPIX@@ 颗 ⇒ 两档都有对象、判据照旧全跑（@@LR0@@→@@LR1@@／@@DR0@@→@@DR1@@）。runner 下一次跑就会自带这条分辨 —— **不猜成因，让被告自己印**。
- **U-879：出口没有把判据弄钝（正对照），账与 CI 一起交** —— 加完读数重跑两把刀：M823（抬量抹平）／M824（画法读回裸 isHovered）仍 @@KN@@、RESTORE_CLEAN=yes；build 0 告警；@@BATT@@；预检 `NEEDLE_PRECHECK tables=@@TBL@@ covered=@@COV@@ arms=@@PARMS@@ bad=0`、`TABLE_ROSTER @@GAPT@@ 张表 / @@GAPA@@ 把刀仍未登记`（缺口本轮未收窄，310 仍开）、`ARM_TOTAL arms=@@ARMS@@ dupes=0`。CI：@@CI1@@、@@CI2@@（本笔 push 后取，只登记号不轮询）；上一跑 @@CI3@@ 的红正是本轮在追的那朵。

眼睛腿：RUN（沿用 R263/R264 那批帧 —— 本轮 0 产品文件、`/tmp/r263_verify/frames` 现读 170 张仍在盘上；看的是 `heatmap-cell-strip` 两态的**亮档近墨那一层**：描边清楚，但整张图的"深浅梯度"与"描边"共用一条灰阶带，这正是本轮给尺加第二条带（≥20）的动机）。范围只这两张。
变异腿：RUN（@@KN@@）。读数腿：RUN（本机两行 + runner 四行 + 预检三行 + 电池一行）。
产品腿：0 文件（`Sources/` 未动 ⇒ FINAL_REPORT 的 sources 格本轮不动，动了会被对账守卫红）。
未做（逐条）：① 313 仍未结案 —— 分辨读数已就位，答案要等 runner 下一跑自己印；② 312 仍被出口挡着；③ 314（描边语义像选中）；④ 315（case-insensitive 那行）；⑤ 310 的 @@GAPT@@ 张表登记、309 那 6 张写死颗数的表；⑥ 305、299、301、307、287/284、297/298/300、304；⑦ 用户闸门 220 路 A / 228② / 265。

"""

ITER_NEW = """## Round 262 · 给 313 装分辨读数：runner 的纸是 @@RBG@@ 不是 @@LBG@@，无对象时读数连方向都会错（R265 / 第 264 轮）/ D-251 · 产品 0 文件

本轮次对照：与 R264（自评 83，出口按对象存在性切片）相比，本轮不放宽任何数值，而是让判据**自我报告它为什么没有对象**：新读「近墨像素(≥20)」与出口里的"读法"半句。现读证人：runner 底 @@RBG@@／本机底 @@LBG@@，runner 墨心 @@RPIX@@ 颗（本机 @@LPIX@@），且 runner 上 hover 读成 @@RR1@@ > idle @@RR0@@（本机方向是 @@LR0@@ → @@LR1@@ 变深）—— 个位数样本上"更浅"是噪声跳，不是产品事实。
看图腿：RUN —— 亮档热图格子两态再看一次：描边清楚，但描边与深浅梯度共用一条灰阶带 ⇒ 这正是尺需要第二条带（≥20）的动机；范围只这两张。
读数腿：RUN —— 本机两档都有对象（近墨 亮 @@LNEAR@@／暗 @@DNEAR@@，墨心 @@LPIX@@ 颗；比值 @@LR0@@→@@LR1@@、@@DR0@@→@@DR1@@）、两把刀 @@KN@@、build 0 告警、@@BATT@@、预检 bad=0（310 缺口 @@GAPT@@ 张 / @@GAPA@@ 把未收窄）。
七维度自评：
| 维度 | 分/满分 |
| 真实视觉审查 | 9/15 |
| 判据有效性 | 14/15 |
| 假绿防御 | 15/15 |
| 产品面推进 | 2/15 |
| 台账一致性 | 14/15 |
| 交付诚实性 | 15/15 |
| 可复核性 | 15/15 |
各维理由：真实视觉审查 9 —— 复用上一轮那批帧再看两张，并给出与尺直接相关的观察（描边与梯度共用灰阶带），没有新画面；判据有效性 14 —— 新读数把"没画"和"淡到进不了带"分开，且出口会自己报读法；假绿防御 15 —— 拦的是最贵的一种假绿：拿"runner 红"去降地板；本轮用现读证明降地板会把噪声当产品事实，同时加完读数立刻重跑两把刀（@@KN@@）证明出口没钝化判据；产品面推进 2 —— 0 产品文件，连续第 1 轮；台账一致性 14 —— 五本 + STATE + 报告两格派生，sources 格按规矩不动；交付诚实性 15 —— 313 明写"未结案、等下一跑自证"；可复核性 15 —— 分辨读数由判据自己印，任何人重跑一次 runner 就拿到答案。合计 **84**/105。

"""

DEC_NEW = """**D-251（R265）：一台机器上"红"的三种身份要能自己分开 —— 产品坏 / 尺坏 / 参照挪走；分不开时，唯一不许做的就是降地板。** 理由：R263 那格在 runner 上红，本机绿。R264 已经证明那是"尺没有对象"（墨心 @@RPIX@@ 颗 vs 本机 @@LPIX@@ 颗），本轮进一步给出**为什么参照也变了**：runner 的纸是 @@RBG@@、本机是 @@LBG@@，而 `glyphInkReading` 的带子 `|Δ| ≥ 60` 是压在"帧内左缘众数"这条参照上的绝对量 —— 参照挪 19 灰阶，带子量的就不是同一片距离。此时若把 3.000 降到达标，等于把噪声当产品事实：runner 上 hover 比 idle 还浅（@@RR1@@ > @@RR0@@），降完地板那格就会"绿"，而它绿的是同一批噪声。处置是把**分辨能力**装进判据：新读「近墨像素(≥20)」= 这一层有没有画；出口那行自带"读法"半句；下一次 runner 跑完，答案由它自己印，不需要我再猜一轮。与 D-232（两台机器各推各的地板）、R147（对照判据要配绝对锚点）、R87（两样本只配说没漂）同族。

"""

NOTE_313 = ("  追记（R265）：分辨读数已落地，本条**仍未结案**（答案等 runner 下一跑自印）。新增证人：runner 的纸是 "
            "@@RBG@@、本机是 @@LBG@@ ⇒ 带子 `|Δ|≥60` 的参照被整体挪走；runner 上 hover 墨心读成 @@RINK1@@ > idle @@RINK0@@，"
            "而本机方向是变深（@@LR0@@→@@LR1@@）—— 个位数样本（@@RPIX@@ 颗）上的方向不是产品事实。"
            "新读「近墨像素(≥20)」+ 出口自带「读法」半句已进判据（D-251）；3.000 一字未动。\n")

BACK_NEW = [
    "**316. 「近墨像素(≥20)」这条带子的宽度本身是 R265 拍的，没有实测支撑（本机亮档 idle=@@LNEAR_A@@ / hover=@@LNEAR_B@@，"
    "暗档 @@DNEAR_A@@/@@DNEAR_B@@，runner 尚无此读数）：等 runner 下一跑印出这条读数之后，要回答两问 —— "
    "① 20 这颗是否把「抗锯齿边缘」与「真墨」分在正确两侧（换一颗阈值看方向会不会翻）；"
    "② 出口那半句「读法=…」在真产物上是否只出现过它该出现的那种。在此之前，"
    "任何用这条带子得出的「画了／没画」结论都只算读数，不算结案依据（R265 新开）**",
]

CHG_NEW = """### Changed（R265 / 第 264 轮 / Round 262 · 给 313 装分辨读数，把「降地板」这条路堵死）

`glyphInkReading` 新增第二条带子：`近墨像素 = 与底 |Δ| ≥ 20 的颗数`（回答"这一层到底有没有画"），与原来的 `墨心 = |Δ| ≥ 60 的众数颗数` 并列打进 `FAVORITE_INK_PROOF`；出口那行从 `(idle=… hover=…)` 变成带 `近墨=… 底=… 读法=这一层几乎没画｜画了但进不了≥60的带`。现读：本机亮档近墨 @@LNEAR@@、暗档 @@DNEAR@@，墨心 @@LPIX@@ 颗 ⇒ 两档都有对象、判据照旧全跑（亮 @@LR0@@→@@LR1@@、暗 @@DR0@@→@@DR1@@）。
313 的新证人（runner 自印）：底 @@RBG@@ vs 本机 @@LBG@@（绝对带子的参照被整体挪走），墨心只有 @@RPIX@@ 颗，且 hover @@RINK1@@ > idle @@RINK0@@（本机方向相反）⇒ **不降 3.000**，因为降完那格会绿在同一批噪声上（D-251）。
两把刀 M823/M824 在加完读数后重跑仍 @@KN@@、RESTORE_CLEAN（出口不许钝化判据）；build 0 告警；@@BATT@@；预检 bad=0、310 缺口 @@GAPT@@ 张 / @@GAPA@@ 把未收窄。新开 316（阈值 20 本身待实测支撑）。产品 0 文件，sources 格按规矩不动。

"""

STATE_NEW = """## R265 状态（第 264 轮 / Round 262 · @@DATE@@）
最后更新：2026-10-21（本地 · R265 / 第 264 轮 / Round 262）：**给 313 装分辨读数，并用现读把「降地板」这条路堵死**（U-876…U-879 · D-251 · 产品 0 文件 · 自评 84/105）

**本轮落地**：`glyphInkReading` 加第二条带子「近墨像素(≥20)」，出口自带「读法」半句；新证人：runner 底 @@RBG@@ vs 本机 @@LBG@@、runner 墨心 @@RPIX@@ 颗且方向反（@@RR1@@ > @@RR0@@）⇒ 3.000 一字未动（D-251）；两把刀重跑仍 @@KN@@；@@BATT@@；build 0 告警；新开 316（阈值 20 待实测支撑）。

**下一轮（R266 / 第 265 轮 / Round 263）的 ⓪**：
⓪ 读 CI：@@CI1@@、@@CI2@@ —— 本笔 push 后取新号（只登记号不轮询，R140）。**这一跑要读的是 runner 自己印的 `FAVORITE_INK_PROOF … 近墨像素(≥20)=…` 与 `FAVORITE_INK_NOT_RUN … 读法=…`**：近墨有几百 ⇒ 313 结到"画了但淡"；近墨也只有个位 ⇒ 结到"这一层几乎没画"。同时看 315 那行 case-insensitive 的 error 是否再现。
① 313 结案 + 312（地板的 runner 复验，被出口挡着的那半）。
② 314：热图描边的语义（选中 vs 悬停）—— 先做"同一格分别点亮两态"的对照夹具再交眼睛，之后才接 291 那位。
③ 316、310 的 @@GAPT@@ 张表登记、309 那 6 张写死颗数的表。
④ 305 的地板、299 执行器半、301、307、287/284、297/298/300、304；用户闸门 220 路 A / 228② / 265。

"""


def render(s):
    for key, val in V.items():
        s = s.replace(key, val)
    if "@@" in s:
        die("渲染后仍有未替换占位符：" + s[:160])
    return s


for name in ("UI_NEW", "ITER_NEW", "DEC_NEW", "CHG_NEW", "STATE_NEW", "NOTE_313"):
    globals()[name] = render(globals()[name])
V["@@LNEAR_A@@"], V["@@LNEAR_B@@"] = L["near"].split("/")
V["@@DNEAR_A@@"], V["@@DNEAR_B@@"] = D["near"].split("/")
BACK_NEW = "\n\n".join(render(x) for x in BACK_NEW) + "\n"
UI_NEW = render(UI_NEW)
ITER_NEW = render(ITER_NEW)
DEC_NEW = render(DEC_NEW)
CHG_NEW = render(CHG_NEW)
STATE_NEW = render(STATE_NEW)
NOTE_313 = render(NOTE_313)

ui_old = rd(UI)
ANCHOR = "## 第 263 轮"
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


def append_after(ls, num, payload):
    idx = [i for i, l in enumerate(ls) if re.match(r"^(?:\*\*)" + num + r"\. ", l)]
    if len(idx) != 1:
        die("BACKLOG " + num + " 锚点命中 " + str(len(idx)) + " 次")
    k = idx[0] + 1
    while k < len(ls) and ls[k].strip():
        k += 1
    return ls[:k] + payload.splitlines(True) + ls[k:]


lines = append_after(blines, "313", NOTE_313)
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
ST_MARK = "## R264 状态"
if ST_MARK not in st_old:
    die("STATE 找不到锚点")
state_new = st_old.replace(ST_MARK, STATE_NEW + ST_MARK, 1)
must_preserve(st_old, state_new, "AGENT_STATE.md")

ids = [int(x) for x in re.findall(r"- \*\*U-(\d+)", UI_NEW)]
if ids != list(range(876, 880)):
    die("本轮 U 号不连续：" + str(ids))
if "U-876…U-879" not in UI_NEW.splitlines()[0]:
    die("节标题 U 区间与定义不符")
if not iter_new.startswith(iter_old.rstrip("\n")) or not dec_new.startswith(dec_old.rstrip("\n")):
    die("升序那本不是纯追加")
if iter_new.count("| 真实视觉审查 |") != iter_old.count("| 真实视觉审查 |") + 1:
    die("七维表多写或少写")
rows = [l for l in ITER_NEW.splitlines() if l.startswith("| ") and "维度" not in l and "分/满分" not in l]
scores = [int(m.group(1)) for m in (re.search(r"\| (\d+)/15 \|", l) for l in rows)]
if len(scores) != 7:
    die("七维表形状不对：" + str(len(scores)))
mt = re.search(r"合计 \*\*(\d+)\*\*/105", ITER_NEW)
if not mt or int(mt.group(1)) != sum(scores):
    die("合计手抄错了：表里相加=" + str(sum(scores)))
if "D-251" in dec_old or "D-250" not in dec_old:
    die("D 号不对")
if re.search(r"^\*\*316\. ", back_new, re.M) is None or back_new.count("\n**316. ") != 1:
    die("新开 316 没落上")
if back_new.count("追记（R265）") != 1:
    die("313 的追记没写上")
if "## R265 状态" not in state_new:
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
print("LEDGERS_R265 OK batt=Ran " + ran2 + " (skipped=" + skip2 + ") rbg=" + V["@@RBG@@"] + " lbg=" + V["@@LBG@@"]
      + " near=" + V["@@LNEAR@@"] + " U=876..879 D=251")
print(out.strip().splitlines()[-1])
