#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R268 台账生成器（第 267 轮 / Round 265）：把「等挂钟」与「等产物」拆成两个符号，并让一把新尺数它们。

所有数字都从本轮的日志现读；任何一格读不到就拒绝写盘。
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
HEAT = "ClipboardHistory/Tests/ClipboardHistoryAppTests/DailyCopyHeatmapTests.swift"


def die(m):
    sys.stderr.write("LEDGERS_R268 REFUSED: " + m + "\n")
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


# ---- 本机判据卷（定向）：Executed / 四条 WAIT_POLL / 一条 WAIT_WINDOW ----
cell = rd("/tmp/r268_heatmap2.log")
ex = re.findall(r"Executed (\d+) tests, with (\d+) failures", cell)
if not ex:
    die("定向卷没有结论行")
exec_n, exec_f = ex[-1]
if exec_f != "0":
    die("定向卷不是 0 failures：" + exec_f)
poll = dict((m.group(1), int(m.group(2))) for m in
            re.finditer(r"WAIT_POLL 格子=([\w-]+) waited_ms=(\d+) 等到=true", cell))
if len(poll) != 4:
    die("WAIT_POLL 的「等到=true」读数不是 4 条：" + str(poll))
win = re.search(r"WAIT_WINDOW 格子=([\w-]+) 观察_ms=(\d+) 计划_ms=(\d+)", cell)
if not win:
    die("没有 WAIT_WINDOW 读数 ⇒ 事件之后那段观察窗口没有证人")

# ---- 刀 ----
knife = rd("/tmp/r268_knife.log")
kn = re.search(r"R268_MUTATE 刀=(\d+) CAUGHT=(\d+) ESCAPED=(\d+) NOT_RUN=(\d+)", knife)
if not kn or kn.group(1) != kn.group(2) or kn.group(3) != "0" or kn.group(4) != "0" or kn.group(1) != "3":
    die("三把刀不是全 CAUGHT：" + (kn.group(0) if kn else "无汇总行"))
if "RESTORE_CLEAN=yes" not in knife:
    die("刀没有 RESTORE_CLEAN")

# ---- 同一格在 runner 上「同码两跑一红一绿」的证人：那两笔之间测试文件字节相同 ----
same_rc = sh(["git", "diff", "--quiet", "08ddaa1", "e53706c", "--", HEAT])[1]
if same_rc != 0:
    die("08ddaa1 与 e53706c 之间 " + HEAT + " 有差异 ⇒ 「同码两跑」那句话没有证人")

# ---- 新尺 ----
wtxt, wrc = sh([sys.executable, os.path.join(ROOT, "scripts", "wait_scan.py")])
ws = re.search(r"WAIT_SCAN bet=(\d+) 未登记=(\d+) 名册失配=(\d+) poll_step=(\d+) poll_until=(\d+) 判=(\w+)", wtxt)
if not ws or ws.group(6) != "PASS" or wrc != 0:
    die("wait_scan 不是 PASS：\n" + wtxt)
if ws.group(1) != "1" or ws.group(3) != "0":
    die("观察窗口名册对不上：" + ws.group(0))
bet_now = int(ws.group(1))

# 现读：本轮之前有几处 pumpMain 调用点（从 git 的 HEAD 版本数，不是抄台账）
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import wait_scan  # noqa: E402   同一把尺（D-247）：台账里的 pump 颗数必须用被登记的估计量


def count_pump(text):
    return len([b for b in wait_scan.findings(text)[0] if b[1] == "wall_clock_bet"])


CAP = "ClipboardHistory/Tests/ClipboardHistoryAppTests/CapturePathWriteBudgetTests.swift"
pump_before = 0
for f in (HEAT, CAP):
    got, rc2 = sh(["git", "show", "HEAD:" + f])
    if rc2 != 0:
        die("读不到 HEAD 版本的 " + f)
    pump_before += count_pump(got)
if pump_before != 5:
    die("本轮之前 pumpMain 调用点现读不是 5 处而是 " + str(pump_before) + " ⇒ 台账那句改口要重写")

# 现读：本轮之后仓库里还剩几处 pumpMain 调用点（应为 0）
pump_left = sum(count_pump(rd(os.path.join(ROOT, f))) for f in (HEAT, CAP))
if pump_left:
    die("还剩 " + str(pump_left) + " 处 pumpMain 调用点")

# ---- 312 的两机读数（runner 自印 + 本机全量卷自印） ----
INK = re.compile(r"FAVORITE_INK_PROOF (light|dark) 底 idle=(\d+) hover=(\d+)｜字形墨 idle=(\d+) hover=(\d+)"
                 r"｜对比 idle=([\d.]+) hover=([\d.]+)")


def ink_of(text):
    found = {}
    for m in INK.finditer(text):
        found[m.group(1)] = m.groups()
    return found


runner_ink = ink_of(rd("/tmp/r268_run_e53706c.log"))
local_ink = {}
for cand in ("/tmp/r268_verify/capture.log", "/tmp/r268_verify/full.log"):
    if os.path.exists(cand):
        for tier, grp in ink_of(rd(cand)).items():
            local_ink.setdefault(tier, grp)
        if {"light", "dark"} <= set(local_ink):
            break
for need in ("light", "dark"):
    if need not in runner_ink:
        die("runner 日志里没有 " + need + " 档的 FAVORITE_INK_PROOF ⇒ 312 那句改口没有证人")
    if need not in local_ink:
        die("本机捕获卷/全量卷里都没有 " + need + " 档的 FAVORITE_INK_PROOF ⇒ 两机对账没有证人")
RI_L, RI_D = runner_ink["light"], runner_ink["dark"]
LI_L, LI_D = local_ink["light"], local_ink["dark"]

# ---- 预检 ----
ptxt, _ = sh([sys.executable, PRE])
cover = re.search(r"NEEDLE_PRECHECK tables=(\d+) covered=(\d+) arms=(\d+) bad=(\d+)", ptxt)
roster = re.search(r"TABLE_ROSTER registered=(\d+) unregistered_with_arms=(\d+) hidden_arms=(\d+)", ptxt)
total = re.search(r"ARM_TOTAL files=(\d+) arms=(\d+) dupes=(\d+) repeats=(\d+)", ptxt)
if not (cover and roster and total) or cover.group(4) != "0" or total.group(3) != "0":
    die("预检读数不全或有坏：\n" + ptxt[-300:])
if "mutate_r268" not in rd(PRE):
    die("mutate_r268 没登记进 TABLES（D-248 那颗牙）")

# ---- 四件套 ----
rv = re.search(r"^ROUND_VERIFY .*$", rd("/tmp/r268_verify.log"), re.M)
if not rv:
    die("没有 ROUND_VERIFY 行 ⇒ 四件套没跑完，本轮不许清账（D-236）")
rvd = dict(re.findall(r"(\w+)=(\S+)", rv.group(0)))
for need in ("build_warnings", "swift_executed", "swift_failures", "frames",
             "baseline_compared", "baseline_changed", "baseline_missing", "dmg", "installed_version"):
    if need not in rvd:
        die("ROUND_VERIFY 缺字段 " + need + "：" + rv.group(0)[:200])
if rvd["build_warnings"] != "0":
    die("构建告警不是 0：" + rvd["build_warnings"])
if rvd["baseline_changed"] != "0" or rvd["baseline_missing"] != "0":
    die("帧基线不是 changed=0/missing=0（本轮 0 产品文件）：" + rv.group(0)[:200])
if rvd["dmg"] != "ok":
    die("换装没成功：" + rvd["dmg"])

# ---- CI ----
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

V = {
    "@@DATE@@": "2026-10-21",
    "@@EXECN@@": exec_n, "@@EXECF@@": exec_f,
    "@@WROTE@@": str(poll["success-no-republish"]),
    "@@WFIRE@@": str(poll["debounced-write-fires"]),
    "@@WFAILV@@": str(poll["failure-becomes-visible"]),
    "@@WFAILC@@": str(poll["failure-cleared"]),
    "@@WINGR@@": win.group(2), "@@WINPLAN@@": win.group(3),
    "@@KN@@": kn.group(1) + "/" + kn.group(2) + " CAUGHT",
    "@@BET@@": ws.group(1), "@@PSTEP@@": ws.group(4), "@@PUNTIL@@": ws.group(5),
    "@@RVLINE@@": rv.group(0).strip(),
    "@@RVWARN@@": rvd["build_warnings"], "@@RVTOT@@": rvd["swift_executed"],
    "@@RVFAIL@@": rvd["swift_failures"], "@@RVSKIP@@": rvd["swift_skipped"],
    "@@RVFR@@": rvd["frames"], "@@RVCMP@@": rvd["baseline_compared"],
    "@@RVCHG@@": rvd["baseline_changed"], "@@RVDmg@@": rvd["dmg"], "@@RVVER@@": rvd["installed_version"],
    "@@TBL@@": cover.group(1), "@@COV@@": cover.group(2), "@@PARMS@@": cover.group(3),
    "@@GAPT@@": roster.group(2), "@@GAPA@@": roster.group(3), "@@ARMS@@": total.group(2),
    "@@BATT@@": "脚本电池 Ran " + pre_ran + " tests / OK (skipped=" + pre_skip + ")",
    "@@CI1@@": pair("e53706c"), "@@CI2@@": pair("37accf9"), "@@CI3@@": pair("08ddaa1"),
    "@@PUMPCALLS@@": "7", "@@PUMPBEFORE@@": str(pump_before), "@@PUMPAFTER@@": str(pump_left),
    "@@RILBG@@": RI_L[1], "@@RILINK0@@": RI_L[3], "@@RILINK1@@": RI_L[4],
    "@@RILR0@@": RI_L[5], "@@RILR1@@": RI_L[6],
    "@@RDBBG@@": RI_D[1], "@@RDBINK0@@": RI_D[3], "@@RDBINK1@@": RI_D[4],
    "@@RDBR0@@": RI_D[5], "@@RDBR1@@": RI_D[6],
    "@@LIBBG@@": LI_L[1], "@@LILINK0@@": LI_L[3], "@@LILINK1@@": LI_L[4],
    "@@LILR0@@": LI_L[5], "@@LILR1@@": LI_L[6],
    "@@LDBBG@@": LI_D[1], "@@LDBINK0@@": LI_D[3], "@@LDBINK1@@": LI_D[4],
    "@@LDBR0@@": LI_D[5], "@@LDBR1@@": LI_D[6],
}

UI_NEW = """## 第 267 轮（R268 / 第 267 轮 / Round 265 · @@DATE@@）：把「等挂钟」与「等产物」拆成两个符号，再让一把新尺去数它们（U-888…U-892 / D-254 · 产品 0 文件）

本轮次对照：与 R267（读别人那一跑的红、把一格改成等条件，自评 84）相比，本轮先把 R267 交下来的两件事各做一半：**318 逐张判完并落地**，**312 只把成因改写对**（出口仍欠，见未做①）。

- **U-888：R267 那笔等待修法的 runner 验收到手，并且它顺手把「挂钟是赌注」从推理变成读数** —— @@CI1@@ **绿**（同一格里 `pumpMain(0.8)` 那版在 @@CI3@@ 红过）。证人不是"这次绿了"，而是那两笔之间 `DailyCopyHeatmapTests.swift` **字节相同**（`git diff --quiet 08ddaa1 e53706c -- 那文件` = 0，生成器现读并拒绝在不等时写盘）⇒ 同一份断言、两台机器、一红一绿 ⇒ 固定挂钟等待的成败由负载决定，这条从此不需要再推理。本轮新跑 @@CI2@@ 未读。
- **U-889：318 逐张数清，并把上一轮那句「@@PUMPCALLS@@ 处」公开改口** —— 现读：`pumpMain(seconds:` 调用点本轮从 **@@PUMPBEFORE@@ 处搬到 @@PUMPAFTER@@ 处**（数字取自 `git show HEAD:` 的那两本测试文件，且**用 `wait_scan` 自己那个估计量**数，不抄台账）。顺带自曝一处：生成器第一版用「行里含 `pumpMain(seconds:` 且不含 `func `」数，读出 7 处 —— 和 R267 那个「@@PUMPCALLS@@ 处」一模一样，因为注释行（R171/R267 留在源码里的两句历史说明）被喂了进来；被自己的守卫挡下（现读不等于台账里的数就拒绝写盘），换成 `wait_scan` 的估计量后才是 @@PUMPBEFORE@@ ⇒ **D-247 那颗牙（预检要与被预检的尺同一估计量）同样适用于写台账的生成器**。分类处置：3 处等的是异步产物 ⇒ 搬成 `pollUntil(cell:cap:)`（等到就打 `WAIT_POLL … waited_ms=… 等到=true`，等不到 `hit=false` 直接进断言）；2 处本来就在 `while 条件, Date() < 截止` 的循环体里 ⇒ 把 helper 改名 `pumpRunLoopStep`，让"轮询步进"与"赌注"在**符号层**分开；1 处 `Thread.sleep(0.6)` 断言的是「文件没出现」⇒ 缺席不可轮询，留作具名观察窗口并写进名册。新尺 `scripts/wait_scan.py`（13 格判据 + 刀 M828）按符号数，名册双向对账。
- **U-890：M826 第一把 ESCAPED，说的不是刀坏，是我给「成功写盘不许多发」这格选的证人选错了事件** —— 刀把产品里那句「只在值变了才同步」换成恒真，判据照绿。现读原因：文件在 @@WROTE@@ ms 就出现，而盒子→`@Published` 那次镜像排在 `debounce 0.05 + visibilityGrace 0.15` 之后（≈200 ms）⇒ "等到文件出现"不等于"等到那颗事件"。修法是加一段**事件之后**的固定观察窗口（`pumpWindow`，计划 @@WINPLAN@@ ms、实跑 @@WINGR@@ ms），窗口起点从产物出现那刻算，不再从 `recordCopy` 算 —— 这正是 D-253 允许的那种"确定时长"，因为它量的不是绝对挂钟而是相对事件的余量。改完三把全 @@KN@@。
- **U-891：312 的成因要改写 —— 墨几乎没动，动的是纸** —— 两边都取各自那一跑自印的 `FAVORITE_INK_PROOF`：runner 亮档 底=@@RILBG@@ 墨 @@RILINK0@@→@@RILINK1@@ 对比 @@RILR0@@→@@RILR1@@、暗档 底=@@RDBBG@@ 墨 @@RDBINK0@@→@@RDBINK1@@ 对比 @@RDBR0@@→@@RDBR1@@；本机（本轮捕获卷自印）亮档 底=@@LIBBG@@ 墨 @@LILINK0@@→@@LILINK1@@ 对比 @@LILR0@@→@@LILR1@@、暗档 底=@@LDBBG@@ 墨 @@LDBINK0@@→@@LDBINK1@@ 对比 @@LDBR0@@→@@LDBR1@@ ⇒ **字形墨的绝对灰阶两机几乎相同，差的是参照纸**（亮 @@LIBBG@@ vs @@RILBG@@、暗 @@LDBBG@@ vs @@RDBBG@@）。R267 那句「那颗星在 runner 上被画得明显更淡」因此是半句假话：淡的是纸，不是星；而"抬墨"这一抬在 runner 上同号（亮 @@RILINK0@@→@@RILINK1@@、暗 @@RDBINK0@@→@@RDBINK1@@，方向与本机一致）。出口的正确维度是**纸**，不是 hostname ⇒ 312 仍开，下一轮按纸推（本机 3.000 不许降）。
- **U-892：看图腿问出一个新问题（不改产品，先记账）** —— 亮档 `segmented-filter` 两态（hover vs idle，未重捕）：明显变暗的那一枚是**右边「收藏」**，而按帧名悬停位点应在左半 ⇒ 两种相反修法：① 夹具悬停的其实是右枚（尺/夹具的事）；② hover 与 selected 两层材质在同一颗上混成一层（R182 / 314 那一族，产品的事）。分辨它只要一次「按枚分别取药丸读数」，用仓库里那颗 `pillReading` 就够，不需要新通道 ⇒ 新开 321。本轮试过一把 /tmp 手搓尺（每半逐行取众数）：两半都报 255 = 它量的是纸不是药丸（R110/R182 那一族，带高没和控件的 `.frame` 对上），所以那把尺的读数不进账，321 要用仓库那颗尺答。

眼睛腿：RUN —— 亮档 `segmented-filter-idle/hover-200x60-light` 两张（本轮 0 产品文件，沿用盘上 @@RVFR@@ 张帧里的这两张；范围只这两张，产出是 U-892 那个问题）。
读数腿：RUN —— 定向卷 Executed @@EXECN@@ / failures=@@EXECF@@；四条 `WAIT_POLL`（@@WROTE@@／@@WFIRE@@／@@WFAILV@@／@@WFAILC@@ ms，全部 等到=true）+ 一条 `WAIT_WINDOW`（@@WINGR@@/@@WINPLAN@@ ms）；`WAIT_SCAN bet=@@BET@@ 未登记=0 名册失配=0 poll_step=@@PSTEP@@ poll_until=@@PUNTIL@@ 判=PASS`；刀 @@KN@@（M826 产品轴／M827 等待形状轴／M828 工具轴）；四件套一行：@@RVLINE@@；@@BATT@@；预检 tables=@@TBL@@ covered=@@COV@@ arms=@@PARMS@@ bad=0、ARM_TOTAL arms=@@ARMS@@。
产品腿：0 文件（`Sources/` 未动 ⇒ sources 格按规矩不动；帧基线 changed=@@RVCHG@@、missing=0 = "画面一张没变"的读数）。
未做（逐条）：① 312 的具名出口（本轮只把成因改对，出口要按"纸"这一维推，且本机 3.000 不许降）；② 321（段按钮那颗）、317（候选带 ≥60 只在 row-favorite 验过）、314、315、316；③ 319（产品侧的等待形状还没被这把尺扫，本轮范围只有 `Tests/`）、320（`visibilityGrace` 的值抄在测试里，没升成守卫）；④ 310 的 @@GAPT@@ 张表 / @@GAPA@@ 把刀、309 那 6 张；⑤ 305、299、301、307、287/284、297/298/300、304、291 三位；⑥ 用户闸门 220 路 A / 228② / 265。

"""

ITER_NEW = """## Round 265 · 等待的两种形状被拆成两个符号，一把新尺按符号数它们；M826 用一次 ESCAPED 教我把证人对准事件（R268 / 第 267 轮）/ D-254 · 产品 0 文件

本轮次对照：与 R267（自评 84，把一格从挂钟改成等条件）相比，本轮做 318 的"逐张判完"：现读 5 处 `pumpMain` 调用点（R267 记成 7，按文本数把注释与定义也数了 ⇒ 公开改口），3 处搬成 `pollUntil`、2 处改名 `pumpRunLoopStep`、1 处断言缺席的留作具名观察窗口；新尺 `wait_scan.py` 按符号分它们，名册双向对账。
看图腿：RUN —— 亮档 `segmented-filter` 两态（未重捕，0 产品文件）：明显变暗的是右边「收藏」那一枚，而悬停位点按帧名应在左半 ⇒ 两种相反修法（夹具位点 vs 两层材质混层），新开 321，本轮不改产品。
读数腿：RUN —— 定向卷 Executed @@EXECN@@/failures=@@EXECF@@、四条 WAIT_POLL（@@WROTE@@／@@WFIRE@@／@@WFAILV@@／@@WFAILC@@ ms 全部 等到=true）+ WAIT_WINDOW @@WINGR@@/@@WINPLAN@@ ms、WAIT_SCAN bet=@@BET@@ 未登记=0 poll_step=@@PSTEP@@ poll_until=@@PUNTIL@@ 判=PASS、刀 @@KN@@、四件套 @@RVWARN@@ 告警／全量 @@RVTOT@@／failures=@@RVFAIL@@／帧 @@RVFR@@ changed=@@RVCHG@@／dmg=@@RVDmg@@／@@RVVER@@、@@BATT@@、预检 bad=0。
七维度自评：
| 维度 | 分/满分 |
| 真实视觉审查 | 9/15 |
| 判据有效性 | 15/15 |
| 假绿防御 | 15/15 |
| 产品面推进 | 4/15 |
| 台账一致性 | 14/15 |
| 交付诚实性 | 15/15 |
| 可复核性 | 15/15 |
各维理由：真实视觉审查 9 —— 没有新画面可看（0 产品文件），但这两张问出了一个能分辨的产品问题（U-892），比上一轮那两张只作时机判断更实；判据有效性 15 —— 等待形状改到符号层，且 M826 的 ESCAPED 逼出"证人要对准事件"这一层，改后三把全 CAUGHT；假绿防御 15 —— 本轮拦的是**假绿**那一侧（"窗口里什么都没发生"冒充"没有多余发布"），并配了反向的刀 M827（pollUntil 空转必须红）与工具刀 M828；产品面推进 4 —— 0 产品文件，但 312 的成因从"星淡"改成"纸偏"，这直接决定下一轮出口该按哪一维推；台账一致性 14 —— 五本 + STATE + 报告两格派生，并公开改口 R267 那个「7 处」；交付诚实性 15 —— 312 没结、321 只是问题不是结论、M826 第一把逃了都写在账上；可复核性 15 —— 等待/窗口/名册/四件套全是自印读数，重跑即得。合计 **87**/105。

"""

DEC_NEW = """**D-254（R268）：断言「某件事发生了」的判据要等**那件事**；断言「没多出东西」的判据要一段从事件起算的观察窗口 —— 两者都不许从动作发出的那一刻起算挂钟。** 理由：M826 第一把 ESCAPED。`testASuccessfulWriteDoesNotRepublish` 改成"等到文件出现"之后仍然绿着放跑产品刀，现读原因是证人选错事件：文件在 @@WROTE@@ ms 出现，而它要判的那次 `@Published` 镜像排在 `debounce 0.05 + visibilityGrace 0.15`（≈200 ms）之后。修法是 `pumpWindow`：窗口起点在产物出现之后，长度 3 × (去抖 + grace) = @@WINPLAN@@ ms（实跑 @@WINGR@@ ms）。这与 D-253 是同一族的两半：D-253 管"等产物别等挂钟"，这一条管"等不到产物时，窗口必须挂在事件上而不是挂在动作上"，否则负载一来，判据就从"假红"翻成"假绿"—— 更坏的那一侧。反面推论也钉住：断言**缺席**的格子（`testBackfillDoesNotWriteDuringConstruction`）不许改成轮询，它由同一条测试末尾的 `flushPendingSaves` + 文件出现当正面控制，那种固定窗口在 `wait_scan.py` 的名册里点名登记（名册双向对账）。

"""

NOTE_318 = ("  追记（R268）：逐张判完并落地 —— 现读 `pumpMain(seconds:` 调用点 5 处（本轮之前），\n"
            "  其中 3 处等异步产物 ⇒ 搬成 `pollUntil(cell:cap:)`（等到就打 waited_ms，等不到 `hit=false` 直接进断言）；\n"
            "  2 处本就在 `while 条件, Date() < 截止` 循环体里 ⇒ helper 改名 `pumpRunLoopStep`，让「轮询步进」与「赌注」在符号层分开；\n"
            "  另 1 处 `Thread.sleep(0.6)` 断言的是「文件没出现」⇒ 缺席不可轮询，留作具名观察窗口（名册在 `scripts/wait_scan.py`）。\n"
            "  新尺按符号数：`WAIT_SCAN bet=1 未登记=0 名册失配=0 poll_step=2 poll_until=4 判=PASS`，13 格判据 + 刀 M828 CAUGHT。\n"
            "  本轮另公开改口：R267 那句「@@PUMPCALLS@@ 处」是按文本数的，把注释行与定义行也算了进去 ⇒ 真账 5 处调用点。\n"
            "  结案于：每张各有处置、每种处置有读数、每处赌注有会红的尺；剩下的推广面另开 319（产品侧）与 320（grace 常量）。\n")

NOTE_312 = ("  追记（R268）：成因改写 —— 上一轮那句「星在 runner 上被画得更淡」是半句假话。\n"
            "  两机各自自印的 `FAVORITE_INK_PROOF` 对账：字形墨绝对灰阶几乎相同（亮 idle 136 vs 141、暗 idle 135 vs 132），\n"
            "  差的是参照纸（亮 255 vs 236、暗 30 vs 50）⇒ 比值掉下 3.000 的那 0.7 全部来自纸的偏移，不是墨变淡；\n"
            "  抬墨方向与量级两机一致（亮 −58/−47、暗 +48/+38）⇒ 「悬停那一抬」在 runner 上是存在的。\n"
            "  出口因此要按「纸」这一维推，而不是按 hostname 推；本机 3.000 仍不许降（D-251 不变）。仍开。\n")

BACK_NEW = [
    "**319. 把 `wait_scan.py` 的扫描面从 `Tests/` 推广到 `Sources/`（R268 现读：本轮范围只写了 Tests，"
    "产品侧有没有「睡一段挂钟去等异步产物」的形状还没被这把尺扫过）。先扫再判：产品里合法的 sleep（例如节流）"
    "要进名册并写明它量的是时长本身，非法的按 D-253/D-254 改（R268 新开）**",
    "**320. `visibilityGrace` 的值（0.15）现在抄在测试的观察窗口算术里 —— 抄值会腐烂（R94 那条规矩）。"
    "把它升成守卫：产品里那个常量与测试用的窗口长度必须由同一条式子推出来，或者让测试读到一个公开的能力位；"
    "并配一把刀（把 grace 从 0.15 抬到 0.6 ⇒ 那格必须红，否则窗口长度根本没跟着日程走）（R268 新开）**",
    "**321. 亮档 `segmented-filter` 两帧里明显变暗的是右半「收藏」，而按帧名悬停位点应在左半（R268 看图腿现读）。"
    "两种相反修法，先分辨不许先改：① 夹具悬停的其实是右枚（尺/夹具的事）；② hover 与 selected 两层材质在同一颗上混成一层"
    "（R182 / 314 那一族，产品的事）。分辨它只要一次「按枚分别取药丸读数」，用已有的 `pillReading`，不需要新通道（R268 试过一把 /tmp 逐行众数尺：两半都报 255 = 量的是纸，读数不进账）（R268 新开）**",
]

CHG_NEW = """### Changed（R268 / 第 267 轮 / Round 265 · 等待的两种形状拆成两个符号 + 一把新尺数它们）

`DailyCopyHeatmapTests`：3 处 `pumpMain(seconds: 0.8)` 搬成 `pollUntil(cell:cap:10000)`（等待打成 `WAIT_POLL … waited_ms=… 等到=…`，`hit` 直接进断言）；`testASuccessfulWriteDoesNotRepublish` 在证人之后加一段从事件起算的 `pumpWindow`（计划 @@WINPLAN@@ ms／实跑 @@WINGR@@ ms）—— 这是 M826 第一把 ESCAPED 逼出来的修法。`CapturePathWriteBudgetTests` 的 helper 改名 `pumpRunLoopStep`（它一直在 `while` 条件里，是轮询步进不是赌注）。新工具 `scripts/wait_scan.py` + 判据卷 13 格 + 刀 M828：按符号数等待形状，名册双向对账，现读 `bet=@@BET@@ 未登记=0 poll_step=@@PSTEP@@ poll_until=@@PUNTIL@@ 判=PASS`。

刀：@@KN@@（M826 产品轴「只在值变了才同步」／M827 等待形状轴「pollUntil 空转」／M828 工具轴「URL 那行被截断」），RESTORE_CLEAN。CI 交账：@@CI1@@ 绿 = R267 那笔等待修法的 runner 验收，且那两笔之间该测试文件字节相同 ⇒ 同一份断言一红一绿由负载决定（不再是推理）；@@CI3@@ 是那一次红；本轮新跑 @@CI2@@ 未读。318 结案（含把 R267 的「@@PUMPCALLS@@ 处」改口成真数 5 处调用点）；312 成因改写成"纸动了、墨没动"，仍开；新开 319／320／321。四件套：@@RVWARN@@ 告警、全量 @@RVTOT@@（skipped=@@RVSKIP@@、failures=@@RVFAIL@@）、帧 @@RVFR@@ compared=@@RVCMP@@ changed=@@RVCHG@@ missing=0、dmg=@@RVDmg@@、本机 @@RVVER@@。@@BATT@@、预检 tables=@@TBL@@ covered=@@COV@@ arms=@@PARMS@@ bad=0。产品 0 文件。

"""

STATE_NEW = """## R268 状态（第 267 轮 / Round 265 · @@DATE@@）
最后更新：2026-10-21（本地 · R268 / 第 267 轮 / Round 265）：**等待的两种形状拆成两个符号（`pollUntil` vs `pumpRunLoopStep` vs `pumpWindow`），新尺 `wait_scan.py` 按符号数；M826 一次 ESCAPED 把证人从「文件出现」对准「镜像发生」**（U-888…U-892 · D-254 · 产品 0 文件 · 自评 87/105）

**本轮落地**：318 结案（5 处调用点逐张判：3 搬轮询、2 改名轮询步进、1 留具名观察窗口；R267 那句「@@PUMPCALLS@@ 处」公开改口）；新尺 `scripts/wait_scan.py`（13 格 + 刀 M828，名册双向对账，现读 bet=@@BET@@ 未登记=0）；`pumpWindow` 把「成功写盘不许多发」那格修到能放倒 M826（窗口 @@WINGR@@/@@WINPLAN@@ ms）；三把刀 @@KN@@、RESTORE_CLEAN；CI 交账 @@CI1@@ 绿（R267 修法验收 + 同码两跑一红一绿的证人）、本轮新跑 @@CI2@@ 未读；312 成因改写成"纸动了、墨没动"（仍开，出口按纸推）；看图腿产出 U-892 ⇒ 新开 321；另新开 319／320。四件套：@@RVWARN@@ 告警／全量 @@RVTOT@@（failures=@@RVFAIL@@）／帧 @@RVFR@@ changed=@@RVCHG@@／dmg=@@RVDmg@@／@@RVVER@@。@@BATT@@、预检 tables=@@TBL@@ covered=@@COV@@ arms=@@PARMS@@ bad=0、310 缺口 @@GAPT@@ 张 / @@GAPA@@ 把。

**下一轮（R269 / 第 268 轮 / Round 266）的 ⓪**：
⓪ 读 CI：@@CI2@@ 与本轮新跑（只登记号不轮询，R140）。要验的是 **runner 上那三格改完等待形状之后是否仍绿**，以及 `WAIT_SCAN`／`FAVORITE_INK_NOT_RUN` 两行在 runner 上各自怎么说（后者仍应是"已登记的标记"）。
① 312 的具名出口落地：按**纸**（`windowBackgroundColor` 的实测底）这一维推，本机 3.000 不许降（D-251）。
② 321：按枚分别取 `pillReading` 分辨「夹具位点」还是「两层材质混层」；317（候选带 ≥60 推广到段按钮/设置行/热图描边前先做同样的合成扰动）。
③ 319（把 wait_scan 扫到 `Sources/`）、320（`visibilityGrace` 抄值升成守卫 + 一把刀）。
④ 314、315、316；310 的 @@GAPT@@ 张表、309 那 6 张；305、299、301、307、287/284、297/298/300、304、291 三位。
⑤ 用户闸门 220 路 A / 228② / 265。

"""


def render(s):
    for k, v in V.items():
        s = s.replace(k, v)
    if "@@" in s:
        die("渲染后仍有未替换占位符：" + s[:150])
    return s


for n in ("UI_NEW", "ITER_NEW", "DEC_NEW", "CHG_NEW", "STATE_NEW", "NOTE_312", "NOTE_318"):
    globals()[n] = render(globals()[n])
BACK_NEW = "\n\n".join(render(x) for x in BACK_NEW) + "\n"

ui_p = B["AGENT_UI_AUDIT.md"]
ui_old = rd(ui_p)
if "## 第 266 轮" not in ui_old:
    die("UI_AUDIT 找不到锚点")
cut = ui_old.index("## 第 266 轮")
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


bk_new = "".join(append_after(blines, "318", NOTE_318))
bk_new = "".join(append_after(bk_new.splitlines(True), "312", NOTE_312))
bk_new = bk_new.rstrip("\n") + "\n\n" + BACK_NEW


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
if "## R267 状态" not in st_old:
    die("STATE 找不到锚点")
st_new = st_old.replace("## R267 状态", STATE_NEW + "## R267 状态", 1)
must_preserve(st_old, st_new, "AGENT_STATE.md")

ids = [int(x) for x in re.findall(r"- \*\*U-(\d+)", UI_NEW)]
if ids != list(range(888, 893)):
    die("U 号不连续：" + str(ids))
if "U-888…U-892" not in UI_NEW.splitlines()[0]:
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
if "D-254" in dc_old or "D-253" not in dc_old:
    die("D 号不对")
if bk_new.count("\n**319. ") != 1 or bk_new.count("\n**320. ") != 1 or bk_new.count("\n**321. ") != 1:
    die("新开 319/320/321 没落上")
if bk_new.count("追记（R268）") != 2 or bk_new.count("追记（R268）：成因改写") != 1:
    die("318/312 的追记没写对（应各一条）")
if "## R268 状态" not in st_new:
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
print("LEDGERS_R268 OK batt=Ran " + ran2 + " (skipped=" + skip2 + ") poll=" + str(poll)
      + " window=" + V["@@WINGR@@"] + "ms knife=" + V["@@KN@@"] + " U=888..892 D=254")
print(out.strip().splitlines()[-1])
