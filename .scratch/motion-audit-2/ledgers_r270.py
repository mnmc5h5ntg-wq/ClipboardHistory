#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R270 台账生成器（第 269 轮 / Round 267）：把抄进判据的产品常量换成读常量，并配一把会红的尺。

数字全部现读；任何一格读不到就拒绝写盘。sources 格由调用方在代码半落地后用
report_cells_r258.py sources <sha> 刷新，本脚本只跑 headline 那两格。
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
    sys.stderr.write("LEDGERS_R270 REFUSED: " + m + "\n")
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


# ---- 定向卷（改前改后各一份，用来证"行为没变"） ----
before = rd("/tmp/r268_heatmap2.log")
after = rd("/tmp/r270_heatmap.log")


def plan_ms(text):
    m = re.search(r"WAIT_WINDOW 格子=success-no-republish 观察_ms=(\d+) 计划_ms=(\d+)", text)
    if not m:
        die("读不到 WAIT_WINDOW ⇒ 窗口长度没有证人")
    return int(m.group(1)), int(m.group(2))


obs_b, plan_b = plan_ms(before)
obs_a, plan_a = plan_ms(after)
if plan_a != plan_b:
    die("计划窗口长度从 " + str(plan_b) + " 变成 " + str(plan_a) + " ⇒ 这不是「只换来源」，行为变了")
ex = re.findall(r"Executed (\d+) tests, with (\d+) failures", after)
if not ex or ex[-1][1] != "0":
    die("改后的定向卷不是 0 failures")
exec_n, exec_f = ex[-1]

# ---- 刀 ----
knife = rd("/tmp/r270_knife.log") if os.path.exists("/tmp/r270_knife.log") else ""
kn = re.search(r"R270_MUTATE 刀=(\d+) CAUGHT=(\d+) ESCAPED=(\d+) NOT_RUN=(\d+)", knife)
if not kn or kn.group(1) != kn.group(2) or kn.group(3) != "0" or kn.group(4) != "0":
    die("M830 不是 CAUGHT（先把刀跑到 /tmp/r270_knife.log）：" + (kn.group(0) if kn else "无汇总行"))
if "RESTORE_CLEAN=yes" not in knife:
    die("刀没有 RESTORE_CLEAN")

# ---- 新尺 ----
ts, trc = sh([sys.executable, os.path.join(ROOT, "scripts", "ledger_timing_scan.py")])
tss = re.search(r"TIMING_SCAN product_grace=([\d.]+) windows=(\d+) 读常量=(\d+) 抄值=(\d+) 判=(\w+)", ts)
if not tss or tss.group(5) != "PASS" or trc != 0:
    die("ledger_timing_scan 不是 PASS：\n" + ts)
if tss.group(4) != "0" or tss.group(2) != tss.group(3):
    die("抄值没归零或窗口没全覆盖：" + tss.group(0))

# ---- 预检 ----
ptxt, _ = sh([sys.executable, PRE])
cover = re.search(r"NEEDLE_PRECHECK tables=(\d+) covered=(\d+) arms=(\d+) bad=(\d+)", ptxt)
roster = re.search(r"TABLE_ROSTER registered=(\d+) unregistered_with_arms=(\d+) hidden_arms=(\d+)", ptxt)
total = re.search(r"ARM_TOTAL files=(\d+) arms=(\d+) dupes=(\d+) repeats=(\d+)", ptxt)
if not (cover and roster and total) or cover.group(4) != "0" or total.group(3) != "0":
    die("预检读数不全或有坏：\n" + ptxt[-300:])
if "mutate_r270" not in rd(PRE):
    die("mutate_r270 没登记进 TABLES（D-248 那颗牙）")

# ---- 四件套（本轮动了 Sources ⇒ 必须重跑） ----
rv = re.search(r"^ROUND_VERIFY .*$", rd("/tmp/r270_verify.log"), re.M)
if not rv:
    die("本轮没有 ROUND_VERIFY 行 ⇒ 动了 Sources 却没跑四件套")
rvd = dict(re.findall(r"(\w+)=(\S+)", rv.group(0)))
for need in ("build_warnings", "swift_executed", "swift_failures", "frames",
             "baseline_compared", "baseline_changed", "baseline_missing", "dmg", "installed_version"):
    if need not in rvd:
        die("ROUND_VERIFY 缺字段 " + need)
if rvd["build_warnings"] != "0":
    die("构建告警不是 0：" + rvd["build_warnings"])
if rvd["baseline_missing"] != "0":
    die("帧基线有 missing：" + rv.group(0)[:200])
# changed 不许被"洗"成 0：要么真的 0，要么逐张分辨、把成因钉在证据上（D-251 同族）。
flaky = json.loads(rd("/tmp/r270_flaky.json"))
if rvd["baseline_changed"] != "0":
    if rvd["baseline_changed"] != "1":
        die("changed 不是 1 张，逐张分辨那套证据不适用：" + rv.group(0)[:160])
    if flaky.get("frame") != "settings-shortcuts-recording-720x540-light.png":
        die("变的那张不是已分辨的那颗：" + str(flaky.get("frame")))
    box = flaky.get("box") or []
    if [int(x) for x in box] != [958, 1213, 503, 550]:
        die("差异包围盒不等于 `frame_recording_proof.py` 量的那块「录制中」 ⇒ 成因没钉住：" + str(box))
    if flaky.get("md5_distinct", 0) < 3 or flaky.get("md5_captures", 0) < 5:
        die("同码翻脸的证据不足：" + str(flaky))
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
    "@@OBSB@@": str(obs_b), "@@OBSA@@": str(obs_a), "@@PLAN@@": str(plan_a),
    "@@GRACE@@": tss.group(1), "@@WINDOWS@@": tss.group(2), "@@READS@@": tss.group(3),
    "@@KN@@": kn.group(1) + "/" + kn.group(2) + " CAUGHT",
    "@@RVWARN@@": rvd["build_warnings"], "@@RVTOT@@": rvd["swift_executed"],
    "@@RVSKIP@@": rvd["swift_skipped"], "@@RVFAIL@@": rvd["swift_failures"],
    "@@RVFR@@": rvd["frames"], "@@RVCMP@@": rvd["baseline_compared"], "@@RVCHG@@": rvd["baseline_changed"],
    "@@RVDmg@@": rvd["dmg"], "@@RVVER@@": rvd["installed_version"],
    "@@RVLINE@@": rv.group(0).strip(),
    "@@TBL@@": cover.group(1), "@@COV@@": cover.group(2), "@@PARMS@@": cover.group(3),
    "@@GAPT@@": roster.group(2), "@@GAPA@@": roster.group(3), "@@ARMS@@": total.group(2),
    "@@BATT@@": "脚本电池 Ran " + pre_ran + " tests / OK (skipped=" + pre_skip + ")",
    "@@CI1@@": pair("e87191a"), "@@CI2@@": pair("c0abdec"), "@@CI3@@": pair("2073b12"), "@@CI4@@": pair("206ddf8"),
    "@@FLPX@@": str(flaky["pixels"]), "@@FLX0@@": str(flaky["box"][0]), "@@FLX1@@": str(flaky["box"][1]),
    "@@FLY0@@": str(flaky["box"][2]), "@@FLY1@@": str(flaky["box"][3]),
    "@@FLCAP@@": str(flaky["md5_captures"]), "@@FLDIS@@": str(flaky["md5_distinct"]),
    "@@TLINE@@": ts.strip().splitlines()[0],
}

UI_NEW = """## 第 269 轮（R270 / 第 269 轮 / Round 267 · @@DATE@@）：判据里那个抄来的产品常量换成读常量，并配一把"抄值复活就红"的尺（U-897…U-901 / D-256 · 产品 1 文件）

本轮次对照：与 R269（自评 86，新尺作用域 + 一颗被误读的悬停结案）相比，本轮回到"判据自己会不会腐烂"这件事上，并且**动了产品源码**（连续 7 轮 0 产品文件之后第一笔，改的是可见性不是行为）。

- **U-897：320 结案 —— 窗口长度不再抄值，而是读产品那个常量** —— `DailyCopyLedger.visibilityGrace` 从 `private let` 升成 `static let`（internal），判据里的观察窗口从字面量 `600` 换成 `Int(3 * (0.05 + DailyCopyLedger.visibilityGrace) * 1000)`。行为不变的证人不是"我说没变"，是三个现读：改前 `WAIT_WINDOW 观察=@@OBSB@@ 计划=@@PLAN@@`、改后 `观察=@@OBSA@@ 计划=@@PLAN@@`（同一格定向卷 Executed @@EXECN@@ / failures=@@EXECF@@），以及四件套的帧基线 @@RVFR@@ 张全对过、changed=@@RVCHG@@（那一张已分辨，见 U-900）。产品里以后改这个值，窗口自己跟着长，不需要有人记得去改注释里的数字。
- **U-898：新尺 `ledger_timing_scan.py` 钉的是"抄值不再发生"，9 格判据 + 刀 M830** —— 现读 @@TLINE@@：产品真相 @@GRACE@@、扫到窗口 @@WINDOWS@@ 处、读常量 @@READS@@ 处、裸字面量 0 处。四格方向相反的对照：把窗口写回 `600` ⇒ 红；注释里出现 0.15 ⇒ **不**红（剥注释，D-235 那一族）；常量声明被删 ⇒ 不许报成"没问题"（读不到真相 = 红，不是空 PASS）；抄值出现在 `pumpWindow` 以外的行也要被抓到。刀 M830 现读 @@KN@@、点名「窗口 success-no-republish 没读常量」、RESTORE_CLEAN。同一把尺顺手修了台账工具自己：`report_cells_r258.py sources` 的锚点是按**上一版正文**写的（要求句尾出现「上一笔动源码是 R253」），而那格早在 R263 就被改写 ⇒ 命中 0 次、直接拒绝写盘；改成按行首标签认（与 `live_sources` 闸门读同一个对象 = D-247），刷新后三格自印 SOURCES_CELL_* 全绿。
- **U-899：两把我主动放弃的刀，写在账上而不是被忘掉** —— ① 把产品 `visibilityGrace` 从 @@GRACE@@ 抬到 0.9 ⇒ 判据**照绿是对的**（窗口跟着长到 2850 ms，这正是要的行为），它不满足"坏法必须红"，所以不配当一把刀；② 把排程里的 `+ Self.visibilityGrace` 删掉 ⇒ 现读**不会红**（那次镜像只是提早，成功路径上仍然没有多余发布）—— 那是另一条轴（提早可见性），本轮没钉住它，所以明写"没钉"，不许把 NOT_RUN 说成通过。
- **U-900：动了 Sources 之后帧基线 changed=@@RVCHG@@，而那张帧是基线里一个会同码翻脸的证人 —— 本轮没有更新基线** —— 逐张分辨：唯一变的那张是 `settings-shortcuts-recording-720x540-light`，差异 @@FLPX@@ 颗像素、**一段连续行带**、包围盒 **x @@FLX0@@…@@FLX1@@ / y @@FLY0@@…@@FLY1@@**，与仓库自己那颗 `scripts/frame_recording_proof.py` 量的「录制中」那块**逐位相同** ⇒ 变的是那块指示器，不是这轮改的常量（那条路径上没有 `DailyCopyLedger`）。更硬的证人：这张帧在盘上留了 @@FLCAP@@ 份历史捕获、md5 有 @@FLDIS@@ 种（R263 与 R268 逐字节相同，R255/R257/R258 各不相同）⇒ 它在**同码多捕**之间就会翻脸。处置：**不更新基线**（更新等于把 flaky 洗成契约，D-251 同族），新开 324 二选一：钉住那颗指示器的相位（夹具里把时钟冻成常数，像 R59/R142 那样量时长而不是抓中间态），或者把这张帧从基线换成具名豁免 + 另一条会红的判据（R182/R246：豁免不许写成沉默）。
- **U-901：新开 323 —— 这把尺现在只钉一对常量，抄值这个形状在仓库里有多少对，还没被清点** —— 本轮没数过 ⇒ 323 第一格就是"扫一遍所有 `static let`/`let` 数值常量与测试里的裸字面量，报有几对相等、其中几对是判据的减数"，数出来之前不许推广结论。

CI 交账：@@CI1@@、@@CI2@@、@@CI3@@（三跑交接时都还没落地 ⇒ 只登记号不轮询，R140；本轮新跑同样按号登记）。
眼睛腿：RUN —— 本轮新捕的 @@RVFR@@ 张里看 `row-favorite-hover` 亮/暗两张（动了 Sources 就要看一眼画面；帧基线 changed=@@RVCHG@@ 是"没变"的读数，那一眼确认的是"没变"与"改的确实只是常量来源"同时成立）。范围只这两张。
读数腿：RUN —— 定向卷 Executed @@EXECN@@/failures=@@EXECF@@、`WAIT_WINDOW` 改前 @@OBSB@@ ms vs 改后 @@OBSA@@ ms（计划 @@PLAN@@ ms）、@@TLINE@@、刀 @@KN@@、四件套一行 @@RVLINE@@、@@BATT@@、预检 tables=@@TBL@@ covered=@@COV@@ arms=@@PARMS@@ bad=0、ARM_TOTAL arms=@@ARMS@@。
产品腿：1 文件（`DailyCopyLedger.swift`：常量可见性 private → internal static；调用点 `Self.visibilityGrace`）⇒ sources 格按 git 对账刷新为本轮那笔代码半。
未做（逐条）：① 312 的具名出口（仍欠，第四轮；成因已改写成"纸动了、墨没动"）；② 323（抄值对子还没数）、322（`asyncAfter` 逐处问有没有判据押在那段延迟上）、317；③ 314、315、316；④ 310 的 @@GAPT@@ 张表 / @@GAPA@@ 把刀、309 那 6 张；⑤ 305、299、301、307、287/284、297/298/300、304、291 三位；⑥ 用户闸门 220 路 A / 228② / 265。

"""

ITER_NEW = """## Round 267 · 判据里抄来的产品常量换成读常量，配一把"抄值复活就红"的尺；两把不配当刀的刀写在账上（R270 / 第 269 轮）/ D-256 · 产品 1 文件（只改可见性）

本轮次对照：与 R269（自评 86）相比，本轮把 R268 留下的 320 做掉：`visibilityGrace` 从 private 升成 internal static，观察窗口从字面量 600 换成 `Int(3 * (0.05 + DailyCopyLedger.visibilityGrace) * 1000)`，新尺 `ledger_timing_scan.py`（9 格）+ 刀 M830 钉住"以后不许再抄"。
看图腿：RUN —— 本轮新捕帧里看 `row-favorite-hover` 亮/暗两张（动了 Sources 就要看一眼；基线 changed=@@RVCHG@@ 与那一眼同时成立）。
读数腿：RUN —— 定向卷 Executed @@EXECN@@/@@EXECF@@、WAIT_WINDOW 改前 @@OBSB@@ ms vs 改后 @@OBSA@@ ms（计划 @@PLAN@@ ms）、@@TLINE@@、刀 @@KN@@、四件套 @@RVWARN@@ 告警／全量 @@RVTOT@@（skipped=@@RVSKIP@@、failures=@@RVFAIL@@）／帧 @@RVFR@@ compared=@@RVCMP@@ changed=@@RVCHG@@ missing=0／dmg=@@RVDmg@@／@@RVVER@@、@@BATT@@、预检 bad=0。
七维度自评：
| 维度 | 分/满分 |
| 真实视觉审查 | 9/15 |
| 判据有效性 | 15/15 |
| 假绿防御 | 15/15 |
| 产品面推进 | 6/15 |
| 台账一致性 | 14/15 |
| 交付诚实性 | 15/15 |
| 可复核性 | 15/15 |
各维理由：真实视觉审查 9 —— 动了产品文件所以看了两张，但那一眼的任务是确认"没变"，不是评估新效果（产品动效面仍欠，这是最弱一维）；判据有效性 15 —— 窗口长度从此由产品日程推，抄值这条路被尺堵死；假绿防御 15 —— 四格方向相反的对照 + 刀 M830 点名"没读常量"，且"读不到真相"不许报成空 PASS；产品面推进 6 —— 1 个产品文件但改的是可见性，画面一张没变（比 0 文件好，比真动效差）；台账一致性 14 —— 五本 + STATE + sources 格按 git 刷新；交付诚实性 15 —— 两把我主动放弃的刀连理由一起记账，没有把 NOT_RUN 说成通过；可复核性 15 —— 改前/改后同一格两份读数 + 四件套一行。合计 **89**/105。

"""

DEC_NEW = """**D-256（R270）：判据不许把产品常量抄成字面量 —— 要么读那个常量（必要时把可见性从 private 升上来），要么配一把"抄值复活就红"的尺。** 理由：R268 给 `testASuccessfulWriteDoesNotRepublish` 加观察窗口时，把 `visibilityGrace` 的 0.15 抄进了测试（当时就写明"抄值会腐烂 ⇒ BACKLOG 320"）。这一轮的修法是**产品侧让出真相**：`private let` → `internal static let`，测试写 `Int(3 * (0.05 + DailyCopyLedger.visibilityGrace) * 1000)`；配套 `scripts/ledger_timing_scan.py`（9 格，含"注释里的 0.15 不算"与"常量声明被删不许报空 PASS"两格反方向对照）与刀 M830（写回裸 600 ⇒ @@KN@@、RESTORE_CLEAN）。行为不变的证据是同一格改前改后两份读数（@@OBSB@@ ms vs @@OBSA@@ ms，计划 @@PLAN@@ ms）加帧基线 @@RVFR@@ 张里除那张已分辨的翻脸帧之外 changed=0。与 R94（注释里的"实测"要么升成判据要么删掉）同族，但对象从散文换成数字：**抄进判据的常量是一条会静默腐烂的边，它不会红，只会等到某天把真红读成假绿。** 同轮另记两把不配当刀的刀（抬常量值判据照绿是正确行为；删掉排程里的 +grace 现读不红 ⇒ 那是"提早可见性"另一条轴，本轮没钉）。

"""

NOTE_320 = ("  追记（R270）：结案 —— 产品侧 `visibilityGrace` 从 private let 升成 internal static let，\n"
            "  判据窗口从字面量 600 换成 Int(3 * (0.05 + DailyCopyLedger.visibilityGrace) * 1000)；\n"
            "  新尺 scripts/ledger_timing_scan.py（9 格）现读 product_grace=@@GRACE@@ windows=@@WINDOWS@@ 读常量=@@READS@@ 抄值=0 判=PASS，\n"
            "  刀 M830（写回裸 600）⇒ @@KN@@、RESTORE_CLEAN。行为不变由两份读数签字：改前 @@OBSB@@ ms、改后 @@OBSA@@ ms（计划 @@PLAN@@ ms）、帧基线 changed=@@RVCHG@@。\n"
            "  推广面另开 323（其余「测试抄产品常量」的对子还没数过）。\n")

BACK_NEW = [
    "**324. `settings-shortcuts-recording-720x540-light` 在基线里会同码翻脸（R270 现读：盘上 @@FLCAP@@ 份捕获、md5 @@FLDIS@@ 种；"
    "本轮那张差异 @@FLPX@@ 颗像素、连续一段行带，包围盒 x @@FLX0@@…@@FLX1@@ / y @@FLY0@@…@@FLY1@@ 与 `frame_recording_proof.py` 量的「录制中」那块逐位相同）。"
    "二选一，不许留成会翻脸的基线：① 夹具里把那颗指示器的时钟相位冻成常数（像 R59/R142 那样量时长而不是抓中间态），重捕之后 changed 必须归 0；"
    "② 若确实不可冻结，就把这张帧换成具名豁免 + 另一条会红的判据（R182/R246：豁免不许写成沉默），并配一把刀证明那条豁免是活的（R270 新开）**",
    "**323. 把 `ledger_timing_scan.py` 从「只钉 grace 一对」推广成「数出有几对」（R270 现读：本轮只扫了一对常量，"
    "仓库里还有多少处把产品常量抄成裸字面量 —— 没数过）。第一格要报：产品侧数值常量颗数、测试侧等于其中某个值的裸字面量处数、"
    "其中几处是判据的减数或窗口长度；数出来之前不许把结论推广到「抄值问题已解决」（R270 新开）**",
]

CHG_NEW = """### Changed（R270 / 第 269 轮 / Round 267 · 判据不再抄产品常量）

`DailyCopyLedger.visibilityGrace`：`private let` → `internal static let`（值不变，@@GRACE@@ s），调用点 `Self.visibilityGrace`。`DailyCopyHeatmapTests.testASuccessfulWriteDoesNotRepublish` 的观察窗口从字面量 `600` 换成 `Int(3 * (0.05 + DailyCopyLedger.visibilityGrace) * 1000)` —— 计划长度仍是 @@PLAN@@ ms，改前/改后实跑 @@OBSB@@ ms / @@OBSA@@ ms（同一格定向卷 Executed @@EXECN@@、failures=@@EXECF@@）。新工具 `scripts/ledger_timing_scan.py` + 判据卷 9 格 + 刀 M830（@@KN@@、RESTORE_CLEAN）：窗口表达式必须出现常量名，判据文件里（剥行注释后）不许再出现等于该值的裸字面量，产品常量读不到时不许报空 PASS。320 结案 ⇒ 新开 323（其余抄值对子还没数）。四件套（本轮动了 Sources ⇒ 重跑）：@@RVWARN@@ 告警、全量 @@RVTOT@@（skipped=@@RVSKIP@@、failures=@@RVFAIL@@）、帧 @@RVFR@@ compared=@@RVCMP@@ changed=@@RVCHG@@ missing=0、dmg=@@RVDmg@@、本机 @@RVVER@@。@@BATT@@、预检 tables=@@TBL@@ covered=@@COV@@ arms=@@PARMS@@ bad=0。CI：@@CI1@@、@@CI2@@、@@CI3@@（交接时未读，只登记号）。

"""

STATE_NEW = """## R270 状态（第 269 轮 / Round 267 · @@DATE@@）
最后更新：2026-10-21（本地 · R270 / 第 269 轮 / Round 267）：**判据里抄来的产品常量换成读常量（visibilityGrace 让出真相），新尺 ledger_timing_scan 钉住"抄值复活就红"；320 结案、新开 323**（U-897…U-900 · D-256 · 产品 1 文件·仅可见性 · 自评 89/105）

**本轮落地**：`DailyCopyLedger.visibilityGrace` private → internal static + 调用点 `Self.`；观察窗口 `Int(3 * (0.05 + DailyCopyLedger.visibilityGrace) * 1000)`（计划 @@PLAN@@ ms，改前 @@OBSB@@／改后 @@OBSA@@ ms 两份读数 + 帧基线 changed=@@RVCHG@@ 证明行为没变）；`scripts/ledger_timing_scan.py`（9 格）现读 @@TLINE@@；刀 @@KN@@、RESTORE_CLEAN；四件套重跑（@@RVWARN@@ 告警／全量 @@RVTOT@@ failures=@@RVFAIL@@／帧 @@RVFR@@ changed=@@RVCHG@@／dmg=@@RVDmg@@／@@RVVER@@）；@@BATT@@；预检 tables=@@TBL@@ covered=@@COV@@ arms=@@PARMS@@ bad=0、310 缺口 @@GAPT@@ 张 / @@GAPA@@ 把。CI 三跑（@@CI1@@／@@CI2@@／@@CI3@@）交接时未读。

**下一轮（R271 / 第 270 轮 / Round 268）的 ⓪**：
⓪ 读 CI：@@CI1@@、@@CI2@@、@@CI3@@ 与本轮新跑（只登记号不轮询，R140）。要验的是 **runner 上 `DailyCopyLedger` 那格改完常量来源之后是否仍绿**，以及 ledger_timing_scan 这类静态尺在 runner 上有没有被接进 CI（没接就照 309/253 那族记账）。
① 312 的具名出口（第四轮欠账）：按**纸**那一维推，本机 3.000 不许降（D-251）。
② 323（数出还有几处抄值）、322（`asyncAfter` 逐处问有没有判据押在那段延迟上）、317（候选带 ≥60 推广前先做同样的合成扰动）。
③ 314、315、316；310 的 @@GAPT@@ 张表、309 那 6 张；305、299、301、307、287/284、297/298/300、304、291 三位。
④ 产品动效面仍是最弱一维（本轮产品文件只改可见性）：按 173/242 那张清账表点一个位真做动效或撤声明。
⑤ 用户闸门 220 路 A / 228② / 265。

"""


def render(s):
    for k, v in V.items():
        s = s.replace(k, v)
    if "@@" in s:
        die("渲染后仍有未替换占位符：" + s[:150])
    return s


for n in ("UI_NEW", "ITER_NEW", "DEC_NEW", "CHG_NEW", "STATE_NEW", "NOTE_320"):
    globals()[n] = render(globals()[n])
BACK_NEW = "\n\n".join(render(x) for x in BACK_NEW) + "\n"

ui_p = B["AGENT_UI_AUDIT.md"]
ui_old = rd(ui_p)
if "## 第 268 轮" not in ui_old:
    die("UI_AUDIT 找不到锚点")
cut = ui_old.index("## 第 268 轮")
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


bk_new = "".join(append_after(blines, "320", NOTE_320)).rstrip("\n") + "\n\n" + BACK_NEW


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
if "## R269 状态" not in st_old:
    die("STATE 找不到锚点")
st_new = st_old.replace("## R269 状态", STATE_NEW + "## R269 状态", 1)
must_preserve(st_old, st_new, "AGENT_STATE.md")

ids = [int(x) for x in re.findall(r"- \*\*U-(\d+)", UI_NEW)]
if ids != list(range(897, 902)):
    die("U 号不连续：" + str(ids))
if "U-897…U-901" not in UI_NEW.splitlines()[0]:
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
if "D-256" in dc_old or "D-255" not in dc_old:
    die("D 号不对")
if bk_new.count("\n**323. ") != 1 or bk_new.count("\n**324. ") != 1:
    die("新开 323 没落上")
if bk_new.count("追记（R270）") != 1:
    die("320 的追记没写上")
if "## R270 状态" not in st_new:
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
print("LEDGERS_R270 OK batt=Ran " + ran2 + " (skipped=" + skip2 + ") window=" + str(obs_b) + "->" + str(obs_a)
      + " plan=" + str(plan_a) + " knife=" + V["@@KN@@"] + " U=897..901 D=256")
print(out.strip().splitlines()[-1])
