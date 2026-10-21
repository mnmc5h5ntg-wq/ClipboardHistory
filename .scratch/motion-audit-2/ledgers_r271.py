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
knife_early = rd("/tmp/r271_knife.log")
clean = [float(x) for x in re.findall(r"CLEAN \d 用时=[\d.]+ 基线=[\d.]+ 倍率=([\d.]+)", meas)]
mut_ratio_m = re.search(r"读数=倍率=([\d.]+)", knife_early)
if len(clean) < 3 or not mut_ratio_m:
    die("测量不全（干净 %d 跑、坏法 %s）⇒ 两界证人不齐" % (len(clean), "有" if mut_ratio_m else "无"))
cm = clean_max = max(clean)
K = float(re.search(r"static let blockedRatioReference: Double = ([\d.]+)",
                rd(os.path.join(ROOT, "ClipboardHistory/Tests/ClipboardHistoryAppTests/CapturePathWriteBudgetTests.swift"))).group(1))
mut_ratio = float(mut_ratio_m.group(1))
# ---- 时间这条轴没有分辨力：这条"负证人"必须成立，否则本轮的处置就不该是"只印不判" ----
cm = max(clean)
if not (mut_ratio <= cm):
    die("坏法倍率 %.2f 高于干净上界 %.2f ⇒ 相对判据其实是有牙的，本轮不该拆它（该重新设计地板）" % (mut_ratio, cm))
src = rd(os.path.join(ROOT, "ClipboardHistory/Tests/ClipboardHistoryAppTests/CapturePathWriteBudgetTests.swift"))
if re.search(r"XCTAssert\w*\(elapsed", src):
    die("源码里还剩一条以 elapsed 为对象的断言 ⇒ 「只印不判」没做到")
for need in ("blockedQueuePrintOnlyMilliseconds", "blockedRatioReference"):
    if need not in src:
        die("常量没改名（缺 " + need + "）⇒ 注释与符号还在说它是地板")

# ---- 最终那一遍刀 ----
knife = knife_early
kn = re.search(r"R271_MUTATE 刀=(\d+) CAUGHT=(\d+) ESCAPED=(\d+) NOT_RUN=(\d+)", knife)
if not kn or kn.group(1) != kn.group(2) or kn.group(3) != "0" or kn.group(4) != "0" or kn.group(1) != "1":
    die("M831 不是 CAUGHT：" + (kn.group(0) if kn else "无汇总行"))
if "RESTORE_CLEAN=yes" not in knife:
    die("刀没有 RESTORE_CLEAN")
kread = re.search(r"读数=倍率=([\d.]+)", knife)
if not kread:
    die("刀那一跑没有自印倍率读数")
if "XCTAssertFalse" not in knife:
    die("刀没有红在行为断言（XCTAssertFalse）上 ⇒ 硬门不在行为那一侧，本轮结论不成立")

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
    "@@KNR@@": "%.2f" % mut_ratio,
    "@@KNR@@": "%.2f" % mut_ratio, "@@KNK@@": "%.2f" % K,
    "@@RV@@": rv.group(0).strip(),
    "@@RVFR@@": rvd["frames"], "@@RVCHG@@": rvd["baseline_changed"],
    "@@TBL@@": cover.group(1), "@@COV@@": cover.group(2), "@@PARMS@@": cover.group(3),
    "@@GAPT@@": roster.group(2), "@@GAPA@@": roster.group(3), "@@ARMS@@": total.group(2),
    "@@BATT@@": "脚本电池 Ran " + pre_ran + " tests / OK (skipped=" + pre_skip + ")",
    "@@CI1@@": pair("68ab84a"), "@@CI2@@": pair("c0abdec"), "@@CI3@@": pair("c1fe940"),
    "@@CI4@@": pair("7f15e97"), "@@CI5@@": pair("a481ab4"),
}

UI_NEW = """## 第 270 轮（R271 / 第 270 轮 / Round 268 · @@DATE@@）：一条"看起来更聪明"的相对判据，被自己装的刀当场证伪 —— 时间这条轴改成只印不判，硬门留在行为那一侧（U-902…U-906 / D-257 · 产品 0 文件）

本轮次对照：与 R270（自评 89，判据不再抄产品常量）相比，本轮处理 R270 收尾抓到的那朵**正在红的** CI（325：runner 报 `12.1725ms ≥ 10ms`，同一份 Swift 代码两跑绿一跑红）。我按 R142 的路子把绝对 ms 地板换成"同一次运行内的比值地板"，然后**先让刀试一遍**——刀说这条路不通。

- **U-902：相对判据没有分辨力，这是现读出来的，不是推出来的** —— 干净三跑的倍率（被堵那次 ÷ 同一次运行的空转中位数）是 @@CLEAN@@；把写盘搬回调用线程那把刀（M831，needle 从 R51 那张表里读、不手抄）跑出的倍率是 @@MUT@@ —— **比干净还低**。原因与该文件自陈的那句是同一件事：库太小，两个量都在亚毫秒，预热与分配器的噪声比一次同步写还大。于是处置改成：绝对 ms 与倍率**都只印不判**（常量改名 `blockedQueuePrintOnlyMilliseconds` / `blockedRatioReference`），断言只剩行为那两条。
- **U-903：拆掉时间断言之后，硬门确实还在行为那一侧 —— 这一条有刀签** —— 刀那一跑现读：@@KN@@、红在 `testAddingACopyWritesNothingOnTheMainThread(XCTAssertFalse)`、失败=1、自印倍率=@@KNR@@。也就是说这一格仍然抓得住那把坏法，靠的是"被堵期间盘上不许出现 history.json"，不是靠任何计时。生成器把这条钉成闸门：刀若没红在行为断言上，本轮不许写盘。
- **U-904：生成器第一版差点把一件没做成的事记成交了** —— 我原先给它写的闸门是 `clean_max < K < mutant`（地板必须落在两界之间）。第一次跑就拒绝落盘，因为**根本没有两界**（坏法在干净之下）。这把闸门这次的作用不是"防手抄"，是"防我把装饰性判据写成进步"；随后把它改成负证人形状：`mutant ≤ clean_max` 必须成立，且源码里不许再有任何以 `elapsed` 为对象的断言。
- **U-905：CI 交账 —— 一朵红是基建不是判据，一朵仍是那颗地板** —— @@CI1@@ **红在 STEP[2] `Run actions/checkout@v4`**（后续步骤全 skip ⇒ 这不是任何判据的红，是拉取代码的基建红，形状与 R154 那族环境红同科，不记账到产品头上也不"重跑当没看见"）；@@CI3@@、@@CI4@@ 绿；@@CI2@@ 是那朵 :153 的负载敏感红（本轮换了形状）；@@CI5@@ 交接时 in_progress ⇒ **325 的结案条件就是它不再红在 :153**，本机绿不算。
- **U-906：两条没钉住的轴，按名字记账** —— 新开 **326**：比值这条轴可以被弄成恒真（让空转基线去读被测那颗 store 自己的时间）而仓库里没有一把尺会红；新开 **327**：`mutate_r271.py` 的 needle 是**运行时从另一张表读来的**，静态预检抽不出它 ⇒ 表进了名册（tables=@@TBL@@）却没进覆盖（covered=@@COV@@），M831 的唯一性只靠 `ARM_TOTAL dupes=0 repeats=0` 这一层，锚点唯一性没人管（D-248 的又一种形态：登记≠覆盖，覆盖≠锚点可查）。

眼睛腿：NOT-RUN —— 本轮 0 个产品文件、帧未重捕（上一笔基线现读 @@RVFR@@ 张、changed=@@RVCHG@@ 那张是已分辨的翻脸帧，见 324），所以没有新画面可看；本轮**不写**"画面没变"，因为那句没有证人。
读数腿：RUN —— 干净三跑倍率 @@CLEAN@@、坏法倍率 @@MUT@@、刀 @@KN@@（自印倍率 @@KNR@@、红在行为断言）、定向卷 Executed @@EXECN@@/failures=@@EXECF@@ 与读数行（用时 @@BLOCK@@ms、空转基线 @@IDLE@@ms、倍率 @@RATIO@@、两条时间值都标着只印不判）、@@BATT@@、预检 tables=@@TBL@@ covered=@@COV@@ arms=@@PARMS@@ bad=0、ARM_TOTAL arms=@@ARMS@@。
产品腿：0 文件（`Sources/` 未动 ⇒ sources 格按规矩不动；四件套沿用上一笔：@@RV@@）。
未做（逐条）：① **325 的 runner 验收**（等 @@CI5@@ 那一跑）；② 326、327（上面那两条没钉住的轴）；③ **312 的具名出口（欠第五轮）**；④ 324（会同码翻脸的那张帧）、323（抄值的可用估计量）、322、317、314、315、316；⑤ 310 的 @@GAPT@@ 张表 / @@GAPA@@ 把刀、309 那 6 张；305、299、301、307、287/284、297/298/300、304、291 三位；⑥ 用户闸门 220 路 A / 228② / 265。

"""

ITER_NEW = """## Round 268 · 一条相对判据在被采纳之前先被自己的刀证伪：时间这条轴改成只印不判，硬门留在行为那一侧（R271 / 第 270 轮）/ D-257 · 产品 0 文件

本轮次对照：与 R270（自评 89）相比，本轮只做 325 一件事，但把它做成了负结果：换相对判据 → 刀试 → 倍率 @@MUT@@ 低于干净上界 @@CLEANMAX@@ → 拆回只印不判，硬门交给行为断言（刀现读 @@KN@@、红在 XCTAssertFalse）。
看图腿：NOT-RUN —— 0 产品文件、帧未重捕，没有新画面可看；也没把"画面没变"当成结论写。
读数腿：RUN —— 干净三跑倍率 @@CLEAN@@、坏法倍率 @@MUT@@、刀 @@KN@@（自印倍率 @@KNR@@）、定向卷 Executed @@EXECN@@/failures=@@EXECF@@、@@BATT@@、预检 tables=@@TBL@@ covered=@@COV@@ arms=@@PARMS@@ bad=0。
七维度自评：
| 维度 | 分/满分 |
| 真实视觉审查 | 5/15 |
| 判据有效性 | 14/15 |
| 假绿防御 | 15/15 |
| 产品面推进 | 2/15 |
| 台账一致性 | 14/15 |
| 交付诚实性 | 15/15 |
| 可复核性 | 15/15 |
各维理由：真实视觉审查 5 —— 本轮没有可看的画面，按实记低分而不是编一句"看了两张没变"；判据有效性 14 —— 结论是"这条轴不该判"，有刀签，扣一分是 325 的 runner 验收还没回来；假绿防御 15 —— 拦住的正是最像进步的那种假绿（把没分辨力的比值写成断言），并且生成器闸门第一次运行就拒绝落盘；产品面推进 2 —— 0 产品文件，本轮连可见性都没改；台账一致性 14 —— 五本 + STATE + 报告两格派生，sources 格按规矩不动；交付诚实性 15 —— 负结果、两把没钉住的轴、基建红都写在账上；可复核性 15 —— 三跑倍率、坏法倍率、刀读数、只印不判的读数行全是自印行。合计 **80**/105。

"""

DEC_NEW = """**D-257（R271）：负载敏感的绝对时间地板既不许"放宽到达标"，也不许顺手换成"看起来更聪明"的相对判据 —— 换之前必须先用同一把刀量出两界；量不出两界，就只印不判。** 理由：`blockedQueueBudgetMilliseconds = 10` 在 runner 上报 `12.1725ms ≥ 10ms`（@@CI2@@），而同一份 Swift 代码两跑绿一跑红。第一步我按 R142 换成"被堵那次 ≤ K × 同一次运行的空转中位数"，并给清账脚本写了闸门 `clean_max < K < mutant` —— 它第一次跑就拒绝落盘，因为**两界不存在**：干净三跑倍率 @@CLEAN@@，而把写盘搬回调用线程那把刀（M831）跑出的倍率是 @@MUT@@，比干净还低（亚毫秒的两个量，噪声比一次同步写大）。于是正确处置不是调 K，而是承认这条轴在此刻的库尺寸上没有分辨力：绝对值与倍率都改成只印不判，判交给行为断言（被堵期间盘上不许出现 `history.json` / `daily-copy.json`；放开闸门之后必须出现），并由刀 M831 现读 @@KN@@、红在 `XCTAssertFalse` 签住"硬门还在"。与 D-251（不许降地板达标）、R142（绝对阈值换相对判据要配同一次运行的对照）、D-254（证人要对准事件）同族；新的一条是：**相对判据也不是自动更对的，它同样要先过刀**。没钉住的轴按名字记账（326 比值恒真、327 运行时 needle 抽不出 ⇒ 登记≠覆盖）。

"""

NOTE_325 = ("  追记（R271）：形状已定，但结论是「这条轴不该判」 —— 相对判据被自己的刀证伪（干净三跑倍率 @@CLEAN@@、"
            "  坏法 M831 倍率 @@MUT@@，比干净还低）⇒ 绝对 ms 与倍率都改成只印不判，硬门留在行为断言那两侧；"
            "  刀现读 @@KN@@、红在 XCTAssertFalse、RESTORE_CLEAN。结案仍等 runner：@@CI5@@ 那一跑不再红在 :153 才算。"
            "  被禁止的两种自欺记名：① 把 10ms 放宽到达标；② 把一条抓不住坏法的比值写成判据。\n")

BACK_NEW = [
    "**326. 「比值地板」可以被弄成恒真而没有一把尺会红（R271 现读：本轮只钉了产品轴 M831）：让空转基线去读被堵那颗 store 自己的时间，"
    "倍率恒为 1 ⇒ 判据永远绿。修法方向与 D-254 同族 —— 基线必须来自另一个对象，并且要有一条会红的证人（例如断言两次的原始 ms 读数不逐位相同，"
    "或让坏法那一跑的倍率读数必须显著不等于 1）（R271 新开）**",
    "**327. `mutate_r271.py` 的 needle 是运行时从 R51 那张表读来的 ⇒ 静态预检抽不出它：表进了名册（tables=@@TBL@@）却没进覆盖（covered=@@COV@@），"
    "M831 只被 ARM_TOTAL 的 dupes/repeats 管到，锚点唯一性没人管。要么把这类「跨表复用 needle」的表做成预检认识的第二种形状"
    "（读表时跟着解析 load_arm() 的来源），要么规定表不许在运行时取 needle —— 但别让它看起来已被覆盖（D-248 的又一种形态）（R271 新开）**",
]

CHG_NEW = """### Changed（R271 / 第 270 轮 / Round 268 · 时间这条轴改成只印不判，硬门交给行为）

`CapturePathWriteBudgetTests.testAddingACopyWritesNothingOnTheMainThread`：新增一颗同一次运行的空转基线（另一 store、同一 `add`、三样本取中位数）**只为把噪声打成读数**；绝对地板改名 `blockedQueuePrintOnlyMilliseconds`、比值参考改名 `blockedRatioReference`，两条都只印不判；断言只剩行为那两侧。为什么不用比值当判据：干净三跑倍率 @@CLEAN@@，而把写盘搬回调用线程的刀（M831）跑出倍率 @@MUT@@ —— 比干净还低 ⇒ 这条轴在此刻的库尺寸上没有分辨力（该文件早就自陈 M249 只值 2.54ms 照样绿）。刀现读 @@KN@@、红在 `XCTAssertFalse`、RESTORE_CLEAN ⇒ 拆掉时间断言没有拆掉判据。定向卷 Executed @@EXECN@@/failures=@@EXECF@@，读数行 `用时=@@BLOCK@@ms 空转基线=@@IDLE@@ms 倍率=@@RATIO@@ 地板倍率=25.00 绝对值=10.00ms（只印不判）`。清账脚本的闸门从 `clean_max < K < mutant` 改成负证人（`mutant ≤ clean_max` 且源码里不许再有以 `elapsed` 为对象的断言）。CI：@@CI1@@ 红在 STEP[2] checkout（基建红，后续全 skip，不记到判据头上）、@@CI3@@／@@CI4@@ 绿、@@CI2@@ 是那朵 :153、@@CI5@@ 未读 ⇒ 325 结案等它。新开 326（比值恒真没尺会红）、327（运行时 needle 让预检看不见 ⇒ 登记≠覆盖）。@@BATT@@、预检 tables=@@TBL@@ covered=@@COV@@ arms=@@PARMS@@ bad=0。产品 0 文件、帧未重捕 ⇒ 四件套沿用上一笔、看图腿 NOT-RUN。

"""

STATE_NEW = """## R271 状态（第 270 轮 / Round 268 · @@DATE@@）
最后更新：2026-10-21（本地 · R271 / 第 270 轮 / Round 268）：**325：相对判据被自己的刀证伪 ⇒ 时间这条轴只印不判，硬门留在行为那一侧（M831 CAUGHT 红在 XCTAssertFalse）**（U-902…U-906 · D-257 · 产品 0 文件 · 自评 80/105）

**本轮落地**：空转基线只为把噪声打成读数；`blockedQueuePrintOnlyMilliseconds` / `blockedRatioReference` 只印不判；刀 M831（needle 从 R51 表读）@@KN@@、RESTORE_CLEAN；定向卷 Executed @@EXECN@@/failures=@@EXECF@@；@@BATT@@；预检 tables=@@TBL@@ covered=@@COV@@ arms=@@PARMS@@ bad=0、ARM_TOTAL arms=@@ARMS@@、310 缺口 @@GAPT@@ 张 / @@GAPA@@ 把。本轮 0 产品文件 ⇒ sources 格不动、四件套沿用上一笔、看图腿 NOT-RUN。

**下一轮（R272 / 第 271 轮 / Round 269）的 ⓪**：
⓪ 读 CI：**@@CI5@@（本轮代码半那一笔）是 325 的结案条件** —— 它不再红在 `CapturePathWriteBudgetTests.swift:153` 才算；@@CI1@@ 那一跑红在 STEP[2] checkout 属基建红，重跑一次看它是否自己消失（基建红也不许长期挂着）。只登记号不轮询（R140）。
① 326（比值恒真这条轴：基线必须来自另一个对象 + 一把会红的刀）、327（运行时 needle 让静态预检看不见）。
② **312 的具名出口（欠第五轮）**：按"纸"那一维推，本机 3.000 不许降（D-251）。
③ 324（会同码翻脸的那张帧）、323（抄值的可用估计量）、322、317、314、315、316。
④ 310 的 @@GAPT@@ 张表、309 那 6 张；305、299、301、307、287/284、297/298/300、304、291 三位。
⑤ 产品动效面仍是最弱一维（本轮看图腿直接 NOT-RUN，5/15）：按清账表点一个位真做动效或撤声明。
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
if ids != list(range(902, 907)):
    die("U 号不连续：" + str(ids))
if "U-902…U-906" not in UI_NEW.splitlines()[0]:
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
if bk_new.count("\n**326. ") != 1 or bk_new.count("\n**327. ") != 1:
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
      + " clean=" + V["@@CLEAN@@"] + " mutant=" + V["@@MUT@@"] + " knife=" + V["@@KN@@"] + " U=902..906 D=257")
print(out.strip().splitlines()[-1])
