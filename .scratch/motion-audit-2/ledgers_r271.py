#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R271 台账生成器（第 270 轮 / Round 268）：把绝对 ms 地板换成同一次运行内的比值地板。

地板不是拍的：下界来自干净三跑的倍率，上界来自产品刀（把写盘搬回调用线程）的倍率，
两个数都从 /tmp/r271_measure.log 现读；读不到就拒绝写盘。
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
    sys.stderr.write("LEDGERS_R271 REFUSED: " + m + "\n")
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


# ---- 测量：干净倍率分布 + 坏法倍率 ----
meas = rd("/tmp/r271_measure.log")
clean = [float(x) for x in re.findall(r"CLEAN \d 用时=[\d.]+ 基线=[\d.]+ 倍率=([\d.]+)", meas)]
mut = re.search(r"MUTANT 用时=([\d.]+) 基线=([\d.]+) 倍率=([\d.]+)", meas)
if len(clean) < 3 or not mut:
    die("测量不全（干净 %d 跑、坏法 %s）⇒ 地板没有两界证人" % (len(clean), "有" if mut else "无"))
clean_max = max(clean)
mut_ratio = float(mut.group(3))
if mut_ratio <= clean_max:
    die("坏法倍率 %.2f 没超过干净倍率上界 %.2f ⇒ 这把尺没有分辨力，本轮不许结案" % (mut_ratio, clean_max))

# ---- 源码里的地板必须等于测量推出来的那个数（不手抄）----
src = rd(os.path.join(ROOT, "ClipboardHistory/Tests/ClipboardHistoryAppTests/CapturePathWriteBudgetTests.swift"))
k_src = re.search(r"static let blockedRatioBudget: Double = ([\d.]+)", src)
if not k_src:
    die("读不到 blockedRatioBudget ⇒ 地板不在源码里")
K = float(k_src.group(1))
if not (clean_max < K < mut_ratio):
    die("地板 K=%.2f 不在两界之间（干净上界 %.2f ／ 坏法 %.2f）⇒ 要么太松要么会假红" % (K, clean_max, mut_ratio))

# ---- 最终那一遍刀 ----
knife = rd("/tmp/r271_knife.log")
kn = re.search(r"R271_MUTATE 刀=(\d+) CAUGHT=(\d+) ESCAPED=(\d+) NOT_RUN=(\d+)", knife)
if not kn or kn.group(1) != kn.group(2) or kn.group(3) != "0" or kn.group(4) != "0" or kn.group(1) != "1":
    die("M831 不是 CAUGHT：" + (kn.group(0) if kn else "无汇总行"))
if "RESTORE_CLEAN=yes" not in knife:
    die("刀没有 RESTORE_CLEAN")
kread = re.search(r"倍率=([\d.]+) 地板倍率=([\d.]+)", knife)
if not kread:
    die("刀那一跑没有自印倍率读数")

# ---- 定向卷（改完之后）----
cell = rd("/tmp/r271_cell.log")
ex = re.findall(r"Executed (\d+) tests, with (\d+) failures", cell)
if not ex or ex[-1][1] != "0":
    die("定向卷不是 0 failures")
reading = re.search(r"CAPTURE_PATH_BLOCKED add 用时=([\d.]+)ms 空转基线=([\d.]+)ms 倍率=([\d.]+) 地板倍率=([\d.]+)", cell)
if not reading:
    die("定向卷没有 CAPTURE_PATH_BLOCKED 那行读数")

# ---- 预检 ----
ptxt, _ = sh([sys.executable, PRE])
cover = re.search(r"NEEDLE_PRECHECK tables=(\d+) covered=(\d+) arms=(\d+) bad=(\d+)", ptxt)
roster = re.search(r"TABLE_ROSTER registered=(\d+) unregistered_with_arms=(\d+) hidden_arms=(\d+)", ptxt)
total = re.search(r"ARM_TOTAL files=(\d+) arms=(\d+) dupes=(\d+) repeats=(\d+)", ptxt)
if not (cover and roster and total) or cover.group(4) != "0" or total.group(3) != "0":
    die("预检读数不全或有坏：\n" + ptxt[-300:])
if "mutate_r271" not in rd(PRE):
    die("mutate_r271 没登记进 TABLES（D-248 那颗牙）")

# ---- 本轮没动产品 ⇒ 引用上一笔四件套，并写明没重跑 ----
changed, _ = sh(["git", "status", "--porcelain", "--", "ClipboardHistory/Sources"])
if changed.strip():
    die("工作树动了 Sources ⇒ 必须重跑四件套，不能引用上一笔：" + changed.strip()[:120])
rv = re.search(r"^ROUND_VERIFY .*$", rd("/tmp/r270_verify.log"), re.M)
if not rv:
    die("上一笔的 ROUND_VERIFY 读不到 ⇒ 无法说明引用的是哪一份")
rvd = dict(re.findall(r"(\w+)=(\S+)", rv.group(0)))

ctxt, _ = sh(["gh", "run", "list", "--limit", "10", "--json", "databaseId,headSha,status,conclusion"])
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

V = {
    "@@DATE@@": "2026-10-21",
    "@@CLEAN@@": "/".join("%.2f" % c for c in clean), "@@CLEANMAX@@": "%.2f" % clean_max,
    "@@MUT@@": "%.2f" % mut_ratio, "@@K@@": ("%.2f" % K).rstrip("0").rstrip("."),
    "@@BLOCK@@": reading.group(1), "@@IDLE@@": reading.group(2), "@@RATIO@@": reading.group(3),
    "@@EXECN@@": ex[-1][0], "@@EXECF@@": ex[-1][1],
    "@@KN@@": kn.group(1) + "/" + kn.group(2) + " CAUGHT",
    "@@KNR@@": kread.group(1), "@@KNK@@": kread.group(2),
    "@@RV@@": rv.group(0).strip(),
    "@@RVFR@@": rvd["frames"], "@@RVCHG@@": rvd["baseline_changed"],
    "@@TBL@@": cover.group(1), "@@COV@@": cover.group(2), "@@PARMS@@": cover.group(3),
    "@@GAPT@@": roster.group(2), "@@GAPA@@": roster.group(3), "@@ARMS@@": total.group(2),
    "@@BATT@@": "脚本电池 Ran " + pre_ran + " tests / OK (skipped=" + pre_skip + ")",
    "@@CI1@@": pair("c0abdec"), "@@CI2@@": pair("e87191a"), "@@CI3@@": pair("2073b12"),
    "@@CI4@@": pair("a73c80d"), "@@CI5@@": pair("68ab84a"),
}

UI_NEW = """## 第 270 轮（R271 / 第 270 轮 / Round 268 · @@DATE@@）：那朵会翻脸的绝对 ms 红，换成同一次运行里的比值地板 —— 顺手让这把新尺抓住了旧尺抓不住的坏法（U-902…U-905 / D-257 · 产品 0 文件）

本轮次对照：与 R270（自评 89，判据不再抄产品常量）相比，本轮处理的是 R270 收尾抓到的那朵**正在红的** CI（325）：`CapturePathWriteBudgetTests.testAddingACopyWritesNothingOnTheMainThread` 在 runner 上报 `12.1725ms ≥ 10ms`，而同一份 Swift 代码两跑绿一跑红 ⇒ 绝对挂钟地板在负载前不是判据。

- **U-902：地板由两界证人推出来，不是拍的** —— 干净三跑的倍率（被堵那次 ÷ 同一次运行的空转中位数）是 @@CLEAN@@（上界 @@CLEANMAX@@），把写盘搬回调用线程那把刀的倍率是 @@MUT@@ ⇒ 取 **@@K@@** 落在两界之间；生成器把这条不等式钉成写盘前的闸门（`clean_max < K < mutant`），所以"以后有人把 K 挪出两界"这件事会让清账脚本拒绝落盘，而不是让判据悄悄失去分辨力。
- **U-903：新尺比旧尺更有牙，这是现读的** —— 旧的那颗 10 ms 地板按该文件自己的注释就没有分辨率（M249 形状只值 2.54ms，照样绿）；换成比值之后同一把坏法被 @@KN@@（刀那一跑自印 倍率=@@KNR@@、地板倍率=@@KNK@@）。也就是说：这**不是**"把红放宽成绿"的第四种写法，而是同一件事换成了既抗负载又更灵敏的判据。
- **U-904：绝对值没有删，改成只印不判，并把理由留在原地** —— 读数行现在是 `CAPTURE_PATH_BLOCKED add 用时=@@BLOCK@@ms 空转基线=@@IDLE@@ms 倍率=@@RATIO@@ 地板倍率=@@K@@ 绝对值=10.00ms（只印不判）`；那颗常量改名 `blockedQueuePrintOnlyMilliseconds`。**唯一被禁止的修法（把 10 放宽到 20）没做**，而且写进了注释与 D-257。
- **U-905：一条没钉住的轴，按名字记下来** —— 本轮只有一把刀（产品轴）。"把比值地板改成恒真"（例如让空转基线去读被堵那颗 store 自己的时间）这一类坏法**没有**被钉住：仓库里现在没有一把尺会因为"基线 = 被测值"而红。新开 326 记它（形状与 D-254 的"证人要对准事件"同族：基线必须来自**另一个对象**，否则比值恒为 1）。

眼睛腿：NOT-RUN —— 本轮 0 个产品文件、帧未重捕（上一笔基线现读 @@RVFR@@ 张、changed=@@RVCHG@@ 那张是已分辨的翻脸帧，见 324），所以没有新画面可看；这一眼本轮不记账，也不说"画面没变"。
读数腿：RUN —— 干净三跑倍率 @@CLEAN@@、坏法倍率 @@MUT@@、地板 @@K@@（源码现读）、定向卷 Executed @@EXECN@@/failures=@@EXECF@@、刀 @@KN@@、@@BATT@@、预检 tables=@@TBL@@ covered=@@COV@@ arms=@@PARMS@@ bad=0、ARM_TOTAL arms=@@ARMS@@。
产品腿：0 文件（`Sources/` 未动 ⇒ sources 格按规矩不动；四件套沿用上一笔：@@RV@@）。
CI 交账：@@CI1@@ **红** = 本轮这颗地板（已换形状）；@@CI2@@、@@CI3@@ 绿；@@CI4@@、@@CI5@@ 交接时未读（只登记号不轮询，R140）。
未做（逐条）：① 325 的**runner 验收**（要等本轮这一跑绿/红才算结案，本机绿不算）；② 326（比值地板被弄成恒真的那把尺）、324（那颗会同码翻脸的帧）、323（抄值对子的可用估计量）、322、317；③ **312 的具名出口（欠第五轮）**；④ 314、315、316；310 的 @@GAPT@@ 张表 / @@GAPA@@ 把刀、309 那 6 张；305、299、301、307、287/284、297/298/300、304、291 三位；⑤ 用户闸门 220 路 A / 228② / 265。

"""

ITER_NEW = """## Round 268 · 会翻脸的绝对 ms 红换成同一次运行内的比值地板；新尺抓住了旧尺抓不住的坏法（R271 / 第 270 轮）/ D-257 · 产品 0 文件

本轮次对照：与 R270（自评 89）相比，本轮只做一件事但做完整：325 那朵负载敏感红 —— 地板从"10 ms 绝对值"换成"被堵那次 ≤ @@K@@ × 同一次运行的空转中位数"，两界都是现读（干净 @@CLEAN@@、坏法 @@MUT@@）。
看图腿：NOT-RUN —— 0 产品文件、帧未重捕，本轮没有新画面可看；不说"画面没变"，因为那句本轮没有证人。
读数腿：RUN —— 干净三跑倍率 @@CLEAN@@（上界 @@CLEANMAX@@）、坏法倍率 @@MUT@@、源码里的地板 @@K@@、定向卷 Executed @@EXECN@@/@@EXECF@@ 与读数行（用时 @@BLOCK@@ ms、基线 @@IDLE@@ ms、倍率 @@RATIO@@）、刀 @@KN@@（自印 倍率=@@KNR@@ 地板=@@KNK@@）、@@BATT@@、预检 bad=0。
七维度自评：
| 维度 | 分/满分 |
| 真实视觉审查 | 5/15 |
| 判据有效性 | 15/15 |
| 假绿防御 | 14/15 |
| 产品面推进 | 3/15 |
| 台账一致性 | 15/15 |
| 交付诚实性 | 15/15 |
| 可复核性 | 15/15 |
各维理由：真实视觉审查 5 —— 本轮没有可看的画面（0 产品文件、未重捕），这一维按实记低分而不是编一个"看了两张没变"；判据有效性 15 —— 地板由两界推出且被生成器钉成不等式；假绿防御 14 —— 刀证明新尺抓住了 10 ms 抓不住的坏法，但"基线读成被测值 ⇒ 比值恒真"这一类还没尺会红（326 记名）；产品面推进 3 —— 0 产品文件；台账一致性 15 —— 数字全解析、两界不等式在写盘之前；交付诚实性 15 —— 没把"本机绿"说成 325 结案，runner 验收显式挂在未做①；可复核性 15 —— 三跑倍率、坏法倍率、地板、刀读数全是自印行。合计 **82**/105。

"""

DEC_NEW = """**D-257（R271）：负载敏感的绝对时间地板不许"放宽到达标"，要换成同一次运行内的相对判据；换完必须用同一把旧刀证明新尺更有牙，并把地板的两界钉成写盘前的闸门。** 理由：`blockedQueueBudgetMilliseconds = 10` 在 runner 上报 `12.1725ms ≥ 10ms`（@@CI1@@），而同一份 Swift 代码两跑绿一跑红 —— 这颗地板既没有分辨率（该文件注释自陈：M249 形状只值 2.54ms，照样绿），又会在负载前假红。放宽到 20ms 是第三种假绿，被禁止。改法：判据里加一颗**同一次运行**的空转基线（另一 store、同一 `add`、三样本取中位数），断言换成 `被堵 ≤ @@K@@ × 基线`，绝对值改名 `blockedQueuePrintOnlyMilliseconds` 只印不判。两界现读：干净三跑 @@CLEAN@@（上界 @@CLEANMAX@@）、坏法 @@MUT@@ ⇒ @@K@@ 落在中间；`ledgers_r271.py` 把 `clean_max < K < mutant` 钉成闸门。刀 M831（needle 从 R51 那张表里读，不手抄）现读 @@KN@@、RESTORE_CLEAN ⇒ **新尺抓住了旧尺抓不住的坏法**，这条改动因此不是"把红洗成绿"。没钉住的轴按名字记账（326：让基线去读被测对象自己 ⇒ 比值恒真，现在没有尺会红）。与 R142（p95 换成同一次运行的相对判据）、D-253（等条件不等挂钟）、D-251（不许降地板达标）同族，但这是第一次把"两界都要现读"写成清账闸门。

"""

NOTE_325 = ("  追记（R271）：形状已换、**结案要等 runner** —— 绝对 ms 地板改成 `被堵 ≤ @@K@@ × 同一次运行的空转中位数`，\n"
            "  两界现读：干净三跑 @@CLEAN@@、坏法（M831）@@MUT@@；刀 @@KN@@、RESTORE_CLEAN；绝对值只印不判。\n"
            "  本机绿不算结案：这一条本来就是 runner 上才红的，验收要读本轮那一跑（@@CI5@@ 之后新的一笔）。\n")

BACK_NEW = [
    "**326. 「比值地板」可以被弄成恒真而没有一把尺会红（R271 现读：本轮只钉了产品轴 M831）：把空转基线改成去读被堵那颗 store 自己的时间，"
    "倍率恒为 1 ⇒ 判据永远绿。修法方向与 D-254 同族 —— 基线必须来自**另一个对象**，并且要有一条会红的证人（例如断言两次的原始 ms 读数不逐位相同、"
    "或让刀 M831 的倍率读数必须显著大于 1）。本轮没做，按名字记（R271 新开）**",
]

CHG_NEW = """### Changed（R271 / 第 270 轮 / Round 268 · 负载敏感的 ms 地板换成同一次运行内的比值地板）

`CapturePathWriteBudgetTests.testAddingACopyWritesNothingOnTheMainThread`：新增一颗同一次运行的空转基线（另一 store、同一 `add`、三样本取中位数），断言从 `XCTAssertLessThan(elapsed, 10ms)` 换成 `elapsed ≤ @@K@@ × 基线`；那颗常量改名 `blockedQueuePrintOnlyMilliseconds` 并**只印不判**。读数行现在是 `用时=@@BLOCK@@ms 空转基线=@@IDLE@@ms 倍率=@@RATIO@@ 地板倍率=@@K@@`。地板由两界推出（干净三跑 @@CLEAN@@、坏法 @@MUT@@），且 `ledgers_r271.py` 把 `clean_max < K < mutant` 钉成写盘闸门。刀 M831（needle 从 R51 那张表读，把写盘搬回调用线程）@@KN@@、RESTORE_CLEAN ⇒ 旧那颗 10 ms 地板抓不住的坏法（其自陈：只值 2.54ms）现在会被抓住；**没有把 10 放宽到达标**。CI：@@CI1@@ 红 = 本轮这颗地板、@@CI2@@／@@CI3@@ 绿、@@CI4@@／@@CI5@@ 未读。新开 326（比值地板被弄成恒真的那条轴没钉）。@@BATT@@、预检 tables=@@TBL@@ covered=@@COV@@ arms=@@PARMS@@ bad=0。产品 0 文件、帧未重捕 ⇒ 四件套沿用上一笔、看图腿本轮 NOT-RUN。

"""

STATE_NEW = """## R271 状态（第 270 轮 / Round 268 · @@DATE@@）
最后更新：2026-10-21（本地 · R271 / 第 270 轮 / Round 268）：**325 那朵负载敏感红换形状：绝对 ms 地板 → 同一次运行内的比值地板（两界现读、闸门钉死），新尺比旧尺更有牙**（U-902…U-905 · D-257 · 产品 0 文件 · 自评 82/105）

**本轮落地**：空转基线 + 比值地板 @@K@@（干净三跑 @@CLEAN@@、坏法 @@MUT@@，`clean_max < K < mutant` 是清账闸门）；绝对值只印不判（改名 `blockedQueuePrintOnlyMilliseconds`）；刀 M831 @@KN@@、RESTORE_CLEAN；定向卷 Executed @@EXECN@@/failures=@@EXECF@@；@@BATT@@；预检 tables=@@TBL@@ covered=@@COV@@ arms=@@PARMS@@ bad=0、ARM_TOTAL arms=@@ARMS@@、310 缺口 @@GAPT@@ 张 / @@GAPA@@ 把。本轮 0 产品文件 ⇒ sources 格不动、四件套沿用上一笔、看图腿 NOT-RUN。

**下一轮（R272 / 第 271 轮 / Round 269）的 ⓪**：
⓪ 读 CI：@@CI4@@、@@CI5@@ 与本轮新跑（只登记号不轮询，R140）。**325 的结案条件就是本轮那一跑在 runner 上不再红在 :153** —— 本机绿不算（它本来就只在 runner 红）。
① 326（比值地板被弄成恒真这条轴：基线必须来自另一个对象，并配一把会红的刀）。
② **312 的具名出口（欠第五轮）**：按"纸"那一维推，本机 3.000 不许降（D-251）。
③ 324（那颗会同码翻脸的帧）、323（抄值的可用估计量）、322、317、314、315、316。
④ 310 的 @@GAPT@@ 张表、309 那 6 张；305、299、301、307、287/284、297/298/300、304、291 三位。
⑤ 产品动效面仍是最弱一维（本轮看图腿直接 NOT-RUN 记分 5/15）：按清账表点一个位真做动效或撤声明。
⑥ 用户闸门 220 路 A / 228② / 265。

"""


def render(s):
    for k, v in V.items():
        s = s.replace(k, v)
    if "@@" in s:
        die("渲染后仍有未替换占位符：" + s[:150])
    return s


for n in ("UI_NEW", "ITER_NEW", "DEC_NEW", "CHG_NEW", "STATE_NEW", "NOTE_325"):
    globals()[n] = render(globals()[n])
BACK_NEW = "\n\n".join(render(x) for x in BACK_NEW) + "\n"

ui_p = B["AGENT_UI_AUDIT.md"]
ui_old = rd(ui_p)
if "## 第 269 轮" not in ui_old:
    die("UI_AUDIT 找不到锚点")
cut = ui_old.index("## 第 269 轮")
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
blines = bk_old.splitlines(True)


def append_after(ls, num, payload):
    idx = [i for i, l in enumerate(ls) if re.match(r"^(?:\*\*)" + num + r"\. ", l)]
    if len(idx) != 1:
        die("BACKLOG " + num + " 锚点命中 " + str(len(idx)) + " 次")
    k = idx[0] + 1
    while k < len(ls) and ls[k].strip():
        k += 1
    return ls[:k] + payload.splitlines(True) + ls[k:]


bk_new = "".join(append_after(blines, "325", NOTE_325)).rstrip("\n") + "\n\n" + BACK_NEW


def must_preserve(old, new, name):
    co, cn = Counter(old.splitlines()), Counter(new.splitlines())
    lost = [l for l, c in co.items() if cn[l] < c]
    if lost:
        die(name + " 弄丢 " + str(len(lost)) + " 行：" + " | ".join(lost[:2])[:140])


must_preserve(ui_old, ui_new, "AGENT_UI_AUDIT.md")
must_preserve(cg_old, cg_new, "CHANGELOG.md")
must_preserve(bk_old, bk_new, "AGENT_BACKLOG.md")
st_p = B["AGENT_STATE.md"]
st_old = rd(st_p)
if "## R270 状态" not in st_old:
    die("STATE 找不到锚点")
st_new = st_old.replace("## R270 状态", STATE_NEW + "## R270 状态", 1)
must_preserve(st_old, st_new, "AGENT_STATE.md")

ids = [int(x) for x in re.findall(r"- \*\*U-(\d+)", UI_NEW)]
if ids != list(range(902, 906)):
    die("U 号不连续：" + str(ids))
if "U-902…U-905" not in UI_NEW.splitlines()[0]:
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
if "D-257" in dc_old or "D-256" not in dc_old:
    die("D 号不对")
if bk_new.count("\n**326. ") != 1:
    die("新开 326 没落上")
if bk_new.count("追记（R271）") != 1:
    die("325 的追记没写上")
if "## R271 状态" not in st_new:
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
print("LEDGERS_R271 OK batt=Ran " + ran2 + " (skipped=" + skip2 + ") K=" + V["@@K@@"]
      + " clean=" + V["@@CLEAN@@"] + " mutant=" + V["@@MUT@@"] + " knife=" + V["@@KN@@"] + " U=902..905 D=257")
print(out.strip().splitlines()[-1])
