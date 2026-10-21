#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R272 台账生成器（第 271 轮 / Round 269）：让预检"看得见"与"不抄两份"同时成立。

数字全部现读（电池日志、预检、刀日志）；缺一格就拒绝写盘。
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
B = {n: os.path.join(ROOT, n) for n in ("AGENT_UI_AUDIT.md", "AGENT_VISUAL_ITERATION.md", "AGENT_DECISIONS.md",
                                        "AGENT_BACKLOG.md", "CHANGELOG.md", "AGENT_STATE.md")}
PRE = os.path.join(HERE, "mutate_needle_precheck.py")


def die(m):
    sys.stderr.write("LEDGERS_R272 REFUSED: " + m + "\n")
    raise SystemExit(2)


def rd(p):
    with io.open(p, encoding="utf-8", errors="replace") as h:
        return h.read()


def sh(cmd, cwd=None):
    env = dict(os.environ)
    env["PYTHONUTF8"] = "1"
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    pr = subprocess.run(cmd, cwd=(cwd or ROOT), env=env, capture_output=True, text=True)
    return (pr.stdout or "") + (pr.stderr or ""), pr.returncode


batt = rd("/tmp/r272_batt.log")
ran = re.findall(r"^Ran (\d+) tests", batt, re.M)
if not ran or not re.search(r"^OK", batt, re.M):
    die("电池日志不是绿的")
knife = rd("/tmp/r272_knife.log")
kn = re.search(r"R271_MUTATE 刀=(\d+) CAUGHT=(\d+) ESCAPED=(\d+) NOT_RUN=(\d+)", knife)
if not kn or kn.group(1) != kn.group(2) or kn.group(3) != "0" or kn.group(4) != "0":
    die("M831 不是 CAUGHT：" + (kn.group(0) if kn else "无汇总行"))
kline = re.search(r"红在 (\w+)\((\w+)\).*倍率=([\d.]+)", knife)
if not kline:
    die("刀没有点名红在哪条断言上")
if "RESTORE_CLEAN=yes" not in knife:
    die("刀没有 RESTORE_CLEAN")

ptxt, _ = sh([sys.executable, PRE])
cover = re.search(r"NEEDLE_PRECHECK tables=(\d+) covered=(\d+) arms=(\d+) bad=(\d+)", ptxt)
roster = re.search(r"TABLE_ROSTER registered=(\d+) unregistered_with_arms=(\d+) hidden_arms=(\d+)", ptxt)
total = re.search(r"ARM_TOTAL files=(\d+) arms=(\d+) dupes=(\d+) repeats=(\d+)", ptxt)
if not (cover and roster and total) or cover.group(4) != "0" or total.group(3) != "0":
    die("预检读数不全或有坏：\n" + ptxt[-300:])
if cover.group(2) != "64":
    die("covered 没涨到 64 ⇒ 327 那半步没落地：" + cover.group(0))
if "mutate_r271        M831 ok" not in ptxt:
    die("预检仍然抽不到 mutate_r271 的 needle：" + cover.group(0))

# 镜像与 R51 逐字相同（同一把尺：跑那条判据卷，不重抄断言）
drift, drc = sh([sys.executable, "-m", "unittest", "test_mutate_r271_needle"], cwd=os.path.join(ROOT, "scripts", "tests"))
if drc != 0:
    die("镜像对账格不绿：\n" + drift[-400:])
drift_n = re.findall(r"Ran (\d+) tests", drift)

ctxt, _ = sh(["gh", "run", "list", "--limit", "8", "--json", "databaseId,headSha,status,conclusion"])
runs = json.loads(ctxt[ctxt.index("["):])


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
if pre_ran != ran[-1]:
    die("刀之前那次电池（" + ran[-1] + "）与现在（" + pre_ran + "）不一致")

V = {
    "@@DATE@@": "2026-10-21",
    "@@TBL@@": cover.group(1), "@@COV@@": cover.group(2), "@@PARMS@@": cover.group(3),
    "@@GAPT@@": roster.group(2), "@@GAPA@@": roster.group(3), "@@ARMS@@": total.group(2),
    "@@KN@@": kn.group(1) + "/" + kn.group(2) + " CAUGHT",
    "@@KNCELL@@": kline.group(1), "@@KNASSERT@@": kline.group(2), "@@KNR@@": kline.group(3),
    "@@BATT@@": "脚本电池 Ran " + pre_ran + " tests / OK (skipped=" + pre_skip + ")",
    "@@DRIFTN@@": drift_n[-1] if drift_n else "?",
    "@@CI1@@": pair("3f8050b"), "@@CI2@@": pair("da00b70"), "@@CI3@@": pair("fbbf530"),
}

UI_NEW = """## 第 271 轮（R272 / 第 271 轮 / Round 269 · @@DATE@@）：让静态预检"看得见"一把运行时取 needle 的刀，同时不抄第二份（U-907…U-910 / D-258 · 产品 0 文件）

本轮次对照：与 R271（自评 80，相对判据被自己的刀证伪 ⇒ 时间轴只印不判）相比，本轮收的是 R271 自己留下的两张：327（预检看不见运行时 needle）与 326（比值恒真这条轴没尺会红）。

- **U-907：327 结一半 —— `mutate_r271` 的 needle 从运行时读表改成静态字面量，预检从此看得见它** —— 现读 `NEEDLE_PRECHECK tables=@@TBL@@ covered=@@COV@@ arms=@@PARMS@@ bad=0`（covered 63 → 64），且预检那一行现在打的是 `mutate_r271  M831 ok`（上一笔还是"静态抽不出 needle ⇒ 不在覆盖里"）。刀重跑仍 @@KN@@、红在 `@@KNCELL@@(@@KNASSERT@@)`、倍率=@@KNR@@、RESTORE_CLEAN。
- **U-908：字面量的代价（会腐烂）当场配了解药，而不是留成债** —— 新增 `scripts/tests/test_mutate_r271_needle.py`（@@DRIFTN@@ 格）：镜像的 TARGET/NEEDLE/REPL 必须与 R51 那张表**运行时解析出来的**逐字相同、锚点在被测文件里恰好一次、再加一条正对照（把镜像改一个字符必须红）。于是"单一真相在 R51"与"预检能看见"同时成立 —— 少任何一半都会坏：只留对账 ⇒ 预检看不见（登记≠覆盖）；只留镜像 ⇒ 两表悄悄分叉（D-247 那一族）。写成 D-258。
- **U-909：326 按实改判为"前提消失"，并留下复活条件** —— R271 之后比值已经不是判据（只印不判），"把基线读成被测值 ⇒ 永远绿"这条坏法没有对象；现在会红的只有行为那两侧，其非恒真由刀 M831 现读签（@@KN@@、红在 `@@KNASSERT@@`）。账上写明：**若哪天把比值升回判据，326 立刻复活** —— 免得下一轮把它当成新发现重新推一遍。
- **U-910：CI 交账 —— 325 的结案读数与本轮那一跑** —— @@CI1@@（R271 台账半）与 @@CI2@@（325 收尾）交接时未读；本轮代码半 push 之后新跑 @@CI3@@。325 已在上笔记成结案（runner 不再红在 :153、坏法仍被行为断言抓住），本轮没有新的判据红。

眼睛腿：NOT-RUN —— 本轮 0 个产品文件、帧未重捕（沿用 R270 那一份 170 张的基线），所以没有新画面可看，也不写"画面没变"。
读数腿：RUN —— 预检三行（tables=@@TBL@@ covered=@@COV@@ arms=@@PARMS@@ bad=0、ARM_TOTAL arms=@@ARMS@@ dupes=0、310 缺口 @@GAPT@@ 张 / @@GAPA@@ 把）、刀 @@KN@@（红在 @@KNCELL@@ 的 @@KNASSERT@@、倍率 @@KNR@@）、对账卷 @@DRIFTN@@ 格、@@BATT@@。
产品腿：0 文件（`Sources/` 未动 ⇒ sources 格按规矩不动；四件套沿用 R270 那一份，本轮没重跑）。
未做（逐条）：① 327 剩下那半（预检还没有"运行时取 needle"这类表的通用形状，现在靠每轮手写镜像格 + 对账格撑着，等第三张这种表出现再抽象）；② **312 的具名出口（欠第六轮）**；③ 324（会同码翻脸的那张帧）、323（抄值的可用估计量）、322、317、314、315、316；④ 310 的 @@GAPT@@ 张表 / @@GAPA@@ 把刀、309 那 6 张；305、299、301、307、287/284、297/298/300、304、291 三位；⑤ 用户闸门 220 路 A / 228② / 265。

"""

ITER_NEW = """## Round 269 · 一把运行时取 needle 的刀被改成静态可读，同时配了"不许抄两份"的对账格；一张没了对象的单子按实改判（R272 / 第 271 轮）/ D-258 · 产品 0 文件

本轮次对照：与 R271（自评 80）相比，本轮收 R271 留下的 327 与 326 两张，不新开题。
看图腿：NOT-RUN —— 0 产品文件、帧未重捕（沿用上一笔 170 张的基线），本轮没有可看的画面。
读数腿：RUN —— 预检 tables=@@TBL@@ covered=@@COV@@ arms=@@PARMS@@ bad=0（covered 63→64，`mutate_r271  M831 ok`）、刀 @@KN@@（红在 @@KNCELL@@ 的 @@KNASSERT@@、倍率 @@KNR@@、RESTORE_CLEAN）、对账卷 @@DRIFTN@@ 格、@@BATT@@、ARM_TOTAL arms=@@ARMS@@ dupes=0。
七维度自评：
| 维度 | 分/满分 |
| 真实视觉审查 | 5/15 |
| 判据有效性 | 14/15 |
| 假绿防御 | 15/15 |
| 产品面推进 | 2/15 |
| 台账一致性 | 15/15 |
| 交付诚实性 | 15/15 |
| 可复核性 | 14/15 |
各维理由：真实视觉审查 5 —— 没有新画面可看，按实记低分；判据有效性 14 —— 预检的覆盖真的涨了一格且刀重跑仍 CAUGHT，扣一分是 327 只结一半；假绿防御 15 —— 静态镜像带来的腐烂风险当场配了对账格与漂移正对照，不是留成债；产品面推进 2 —— 0 产品文件；台账一致性 15 —— 326 的改判写明"若比值升回判据则复活"，避免下一轮重推；交付诚实性 15 —— 半张单子写明只结一半、看图腿 NOT-RUN；可复核性 14 —— 全部是自印行与可重跑卷，扣一分是四件套沿用上一笔。合计 **80**/105。

"""

DEC_NEW = """**D-258（R272）：要"静态可读见"就要字面量，要"单一真相"就要运行时解析 —— 两者必须同时成立：字面量 + 一格逐字对账（外加一条漂移正对照）。** 理由：`mutate_r271.py` 原先在运行时从 R51 那张表读 needle（好处是同一把坏法只存一份），代价是静态预检抽不出来 ⇒ 表进了名册（tables=@@TBL@@）却没进覆盖（covered=@@COV@@ 之前是 63），M831 的锚点唯一性没人管（BACKLOG 327）。改成静态字面量之后预检看见了（covered 63 → 64、`mutate_r271  M831 ok`），但字面量会腐烂 —— 于是新增 `scripts/tests/test_mutate_r271_needle.py`（@@DRIFTN@@ 格：与 R51 运行时解析出来的值逐字对账、锚点在被测文件里恰好一次、镜像改一个字符必须红）。只留对账 ⇒ 预检看不见；只留镜像 ⇒ 两表悄悄分叉（D-247 那一族）。同族：R270 的 D-256（判据不许抄产品常量）—— 这次的对象是工具抄工具。

"""

CHG_NEW = """### Changed（R272 / 第 271 轮 / Round 269 · 预检看得见这把刀了）

`.scratch/motion-audit-2/mutate_r271.py`：`TARGET`/`NEEDLE`/`REPL` 从运行时读 R51 表改成静态字面量 ⇒ `mutate_needle_precheck.py` 抽得到（现读 tables=@@TBL@@ covered=@@COV@@ arms=@@PARMS@@ bad=0，covered 63 → 64，表行从"静态抽不出"变成 `M831 ok`）；刀重跑仍 @@KN@@、红在 `@@KNCELL@@(@@KNASSERT@@)`、倍率=@@KNR@@、RESTORE_CLEAN。新增 `scripts/tests/test_mutate_r271_needle.py`（@@DRIFTN@@ 格）把字面量钉回 R51 那颗 needle（逐字对账 + 锚点恰好一次 + 漂移正对照）⇒ 单一真相不变、预检同时看得见（D-258）。327 结一半（通用形状等第三张这种表）、326 改判为"前提消失"并写明复活条件（比值若升回判据立刻复活）。@@BATT@@、ARM_TOTAL arms=@@ARMS@@ dupes=0、310 缺口 @@GAPT@@ 张 / @@GAPA@@ 把本轮未收窄。CI：@@CI1@@／@@CI2@@ 交接时未读、本轮新跑 @@CI3@@；325 已结案。产品 0 文件、帧未重捕 ⇒ 四件套沿用上一笔、看图腿 NOT-RUN。

"""

STATE_NEW = """## R272 状态（第 271 轮 / Round 269 · @@DATE@@）
最后更新：2026-10-21（本地 · R272 / 第 271 轮 / Round 269）：**327 结一半：一把运行时取 needle 的刀改成静态可读，并配"逐字对账 + 漂移正对照"钉住不抄两份（D-258）；326 改判为前提消失并留复活条件**（U-907…U-910 · 产品 0 文件 · 自评 80/105）

**本轮落地**：`mutate_r271` 静态化 ⇒ 预检 covered 63 → 64、bad=0、`M831 ok`；刀重跑 @@KN@@（红在 @@KNCELL@@ 的 @@KNASSERT@@、倍率 @@KNR@@、RESTORE_CLEAN）；新判据卷 `test_mutate_r271_needle.py` @@DRIFTN@@ 格；@@BATT@@；ARM_TOTAL arms=@@ARMS@@ dupes=0、310 缺口 @@GAPT@@ 张 / @@GAPA@@ 把。本轮 0 产品文件 ⇒ sources 格不动、四件套沿用上一笔、看图腿 NOT-RUN。

**下一轮（R273 / 第 272 轮 / Round 270）的 ⓪**：
⓪ 读 CI：@@CI1@@、@@CI2@@、@@CI3@@ 与本轮新跑（只登记号不轮询，R140）。要验的是 **runner 上 `test_mutate_r271_needle` 这类静态对账格有没有进电池那一跑、以及 :153 那颗是否仍然不红**。
① **312 的具名出口（欠第六轮）**：按"纸"那一维推，本机 3.000 不许降（D-251）。这是最久的一条。
② 324（会同码翻脸的那张帧：冻相位或具名豁免 + 会红判据）、323（把"抄值"的可用估计量搬进 scripts/ 并逐处判）、322、317。
③ 314、315、316；310 的 @@GAPT@@ 张表、309 那 6 张；305、299、301、307、287/284、297/298/300、304、291 三位。
④ 产品动效面连续多轮是最弱一维（本轮看图腿 NOT-RUN、5/15）：按清账表点一个位真做动效或撤声明。
⑤ 用户闸门 220 路 A / 228② / 265。

"""


def render(s):
    for k, v in V.items():
        s = s.replace(k, v)
    if "@@" in s:
        die("渲染后仍有未替换占位符：" + s[:150])
    return s


for n in ("UI_NEW", "ITER_NEW", "DEC_NEW", "CHG_NEW", "STATE_NEW"):
    globals()[n] = render(globals()[n])

ui_p = B["AGENT_UI_AUDIT.md"]
ui_old = rd(ui_p)
if "## 第 270 轮" not in ui_old:
    die("UI_AUDIT 找不到锚点")
cut = ui_old.index("## 第 270 轮")
ui_new = ui_old[:cut] + UI_NEW + ui_old[cut:]
it_p = B["AGENT_VISUAL_ITERATION.md"]
it_old = rd(it_p)
it_new = it_old.rstrip("\n") + "\n\n" + ITER_NEW
dc_p = B["AGENT_DECISIONS.md"]
dc_old = rd(dc_p)
dc_new = dc_old.rstrip("\n") + "\n\n" + DEC_NEW
cg_p = B["CHANGELOG.md"]
cg_old = rd(cg_p)
cg_new = cg_old.replace("## [Unreleased]\n", "## [Unreleased]\n\n" + CHG_NEW, 1)
bk_p = B["AGENT_BACKLOG.md"]
bk_old = rd(bk_p)
bk_new = bk_old


def must_preserve(old, new, name):
    co = Counter(old.splitlines())
    cn = Counter(new.splitlines())
    lost = [l for l, c in Counter(old.splitlines()).items() if cn[l] < c]
    if lost:
        die(name + " 弄丢 " + str(len(lost)) + " 行：" + " | ".join(lost[:2])[:140])


must_preserve(ui_old, ui_new, "AGENT_UI_AUDIT.md")
must_preserve(cg_old, cg_new, "CHANGELOG.md")
st_p = B["AGENT_STATE.md"]
st_old = rd(st_p)
if "## R271 状态" not in st_old:
    die("STATE 找不到锚点")
st_new = st_old.replace("## R271 状态", STATE_NEW + "## R271 状态", 1)
must_preserve(st_old, st_new, "AGENT_STATE.md")

ids = [int(x) for x in re.findall(r"- \*\*U-(\d+)", UI_NEW)]
if ids != list(range(907, 911)):
    die("U 号不连续：" + str(ids))
if "U-907…U-910" not in UI_NEW.splitlines()[0]:
    die("节标题 U 区间与定义不符")
if not it_new.startswith(it_old.rstrip("\n")) or not dc_new.startswith(dc_old.rstrip("\n")):
    die("升序那本不是纯追加")
if it_new.count("| 真实视觉审查 |") != it_old.count("| 真实视觉审查 |") + 1:
    die("七维表数量不对")
rows = [l for l in ITER_NEW.splitlines() if l.startswith("| ") and "维度" not in l and "分/满分" not in l]
scores = [int(mm.group(1)) for mm in (re.search(r"\| (\d+)/15 \|", l) for l in rows)]
if len(scores) != 7:
    die("七维表形状不对：" + str(len(scores)))
mt = re.search(r"合计 \*\*(\d+)\*\*/105", ITER_NEW)
if not mt or int(mt.group(1)) != sum(scores):
    die("合计手抄错了：" + str(sum(scores)))
if "D-258" in dc_old or "D-257" not in dc_old:
    die("D 号不对")
if "## R272 状态" not in st_new:
    die("STATE 没轮换")

for p, t in ((ui_p, ui_new), (it_p, it_new), (dc_p, dc_new), (cg_p, cg_new), (st_p, st_new)):
    with io.open(p, "w", encoding="utf-8") as h:
        h.write(t)

out, rc = sh([sys.executable, os.path.join(HERE, "report_cells_r258.py"), "headline"])
if rc != 0:
    die("FINAL_REPORT 刷新失败：" + out[-300:])
ran2, skip2 = battery()
if ran2 != pre_ran:
    die("写盘前后电池颗数不一致（" + pre_ran + " → " + ran2 + "）")
print("LEDGERS_R272 OK batt=Ran " + ran2 + " (skipped=" + skip2 + ") covered=" + V["@@COV@@"]
      + " knife=" + V["@@KN@@"] + " drift=" + V["@@DRIFTN@@"] + " U=907..910 D=258")
print(out.strip().splitlines()[-1])
