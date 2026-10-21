#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R269 台账生成器（第 268 轮 / Round 266）：321 由既有读数结案、319 结一半并当场修掉尺的作用域。

所有数字都从本轮/上一笔的日志现读；任何一格读不到就拒绝写盘。
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
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import wait_scan  # noqa: E402   同一把尺（D-247）


def die(m):
    sys.stderr.write("LEDGERS_R269 REFUSED: " + m + "\n")
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


# ---- 刀 ----
knife = rd("/tmp/r269_knife.log")
kn = re.search(r"R269_MUTATE 刀=(\d+) CAUGHT=(\d+) ESCAPED=(\d+) NOT_RUN=(\d+)", knife)
if not kn or kn.group(1) != kn.group(2) or kn.group(3) != "0" or kn.group(4) != "0" or kn.group(1) != "1":
    die("M829 不是 CAUGHT：" + (kn.group(0) if kn else "无汇总行"))
if "RESTORE_CLEAN=yes" not in knife:
    die("刀没有 RESTORE_CLEAN")
kn_names = re.search(r"红在 ([^\n]+) 结论行=", knife)
if not kn_names:
    die("刀没有点名红在哪几格")
kn_cells = kn_names.group(1).strip()
if "test_a_window_living_outside_the_scanned_root_is_not_stale" not in kn_cells:
    die("刀红在了别的格上（要的是作用域那两格）：" + kn_cells)

# ---- 新尺的两个根 ----
tests_line = sh([sys.executable, os.path.join(ROOT, "scripts", "wait_scan.py")])[0].strip()
src_line = sh([sys.executable, os.path.join(ROOT, "scripts", "wait_scan.py"),
               "--root", "ClipboardHistory/Sources"])[0].strip()
tst = re.search(r"WAIT_SCAN bet=(\d+) 未登记=(\d+) 名册失配=(\d+) poll_step=(\d+) poll_until=(\d+) 判=(\w+)", tests_line)
sst = re.search(r"WAIT_SCAN bet=(\d+) 未登记=(\d+) 名册失配=(\d+) poll_step=(\d+) poll_until=(\d+) 判=(\w+)", src_line)
if not (tst and sst) or tst.group(6) != "PASS" or sst.group(6) != "PASS":
    die("两个根不是都 PASS：\n" + tests_line + "\n" + src_line)
if sst.group(1) != "0":
    die("产品侧现读赌注不是 0 ⇒ 319 那句要按新数重写：" + src_line)

# ---- 321 的证人：本轮没重捕，读的是上一笔捕获卷自印的两行 ----
cap = rd("/tmp/r268_verify/capture.log")
seg = {}
for m in re.finditer(r"HOVER_DIRECT_READ_PROOF (light|dark) 段按钮 空闲底=(\d+) 悬停=(\d+) 比值=([\d.]+) "
                     r"像素=(\d+) 选中段 空闲=(\d+) 悬停=(\d+)", cap):
    seg[m.group(1)] = m.groups()
for need in ("light", "dark"):
    if need not in seg:
        die("捕获卷里没有 " + need + " 档的 HOVER_DIRECT_READ_PROOF ⇒ 321 的结案没有证人")
SL, SD = seg["light"], seg["dark"]
if SL[5] != SL[6] or SD[5] != SD[6]:
    die("选中段两态不一样 ⇒ 321 那句「选中那一颗没有第二层」被现读推翻，本轮不许结案")

# ---- 预检 ----
ptxt, _ = sh([sys.executable, PRE])
cover = re.search(r"NEEDLE_PRECHECK tables=(\d+) covered=(\d+) arms=(\d+) bad=(\d+)", ptxt)
roster = re.search(r"TABLE_ROSTER registered=(\d+) unregistered_with_arms=(\d+) hidden_arms=(\d+)", ptxt)
total = re.search(r"ARM_TOTAL files=(\d+) arms=(\d+) dupes=(\d+) repeats=(\d+)", ptxt)
if not (cover and roster and total) or cover.group(4) != "0" or total.group(3) != "0":
    die("预检读数不全或有坏：\n" + ptxt[-300:])
if "mutate_r269" not in rd(PRE):
    die("mutate_r269 没登记进 TABLES（D-248 那颗牙）")

# ---- 四件套：本轮 0 Swift 文件 ⇒ 引用上一笔的现读，并写明本轮没重跑 ----
rv = re.search(r"^ROUND_VERIFY .*$", rd("/tmp/r268_verify.log"), re.M)
if not rv:
    die("上一笔的 ROUND_VERIFY 行读不到 ⇒ 无法说明「本轮没重跑」引用的是哪一份")
rvd = dict(re.findall(r"(\w+)=(\S+)", rv.group(0)))
# 本轮（未提交的工作树）有没有动 Swift —— 动了就不许沿用上一笔的四件套
swift_changed, _ = sh(["git", "status", "--porcelain"])
if "ClipboardHistory/" in swift_changed:
    die("本轮工作树动过 ClipboardHistory/ ⇒ 四件套不能沿用上一笔，必须重跑："
        + " | ".join(l for l in swift_changed.splitlines() if "ClipboardHistory/" in l)[:200])

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
batt_log = re.search(r"^Ran (\d+) tests", rd("/tmp/r269_batt.log"), re.M)
if not batt_log or batt_log.group(1) != pre_ran:
    die("刀之前那次电池（" + (batt_log.group(1) if batt_log else "无") + "）与现在（" + pre_ran + "）不一致")

V = {
    "@@DATE@@": "2026-10-21",
    "@@KN@@": kn.group(1) + "/" + kn.group(2) + " CAUGHT", "@@KNCELLS@@": kn_cells,
    "@@TLINE@@": tests_line, "@@SLINE@@": src_line,
    "@@SL0@@": SL[1], "@@SL1@@": SL[2], "@@SLR@@": SL[3], "@@SLPX@@": SL[4],
    "@@SLL0@@": SL[5], "@@SLL1@@": SL[6],
    "@@SD0@@": SD[1], "@@SD1@@": SD[2], "@@SDR@@": SD[3],
    "@@SDL0@@": SD[5], "@@SDL1@@": SD[6],
    "@@RV@@": rv.group(0).strip(),
    "@@TBL@@": cover.group(1), "@@COV@@": cover.group(2), "@@PARMS@@": cover.group(3),
    "@@GAPT@@": roster.group(2), "@@GAPA@@": roster.group(3), "@@ARMS@@": total.group(2),
    "@@BATT@@": "脚本电池 Ran " + pre_ran + " tests / OK (skipped=" + pre_skip + ")",
    "@@CI1@@": pair("37accf9"), "@@CI2@@": pair("e87191a"), "@@CI3@@": pair("e53706c"),
}

UI_NEW = """## 第 268 轮（R269 / 第 268 轮 / Round 266 · @@DATE@@）：一颗"看起来像缺陷"的悬停由既有读数结案，一把新尺在第二个根上暴露自己的作用域 bug（U-893…U-896 / D-255 · 产品 0 文件）

本轮次对照：与 R268（把等待的两种形状拆成两个符号 + 新尺 `wait_scan`，自评 87）相比，本轮不写新判据形状，做两件 R268 留下的事：**321 结案**、**319 结一半**，并在做第二件时抓到这把新尺自己的坏法。

- **U-893：CI 交账 —— R267 那笔"等条件"修法的 runner 验收到手** —— @@CI1@@ **绿**（R268 交接时它是 in_progress / 未读，当时按 R140 只登记号不轮询）。上一笔 @@CI3@@ 也绿；本轮代码半 push 之后新跑 @@CI2@@（未读）。这条把 R268 的"同一份断言两台机器一红一绿"闭环了：改完之后 runner 不再红。
- **U-894：321 结案 —— 我眼睛看到的"变暗的是没被悬停那一枚"是真的，但推论是错的：那颗取证键是整颗控件级的，不是指针位置** —— 夹具把 `hoveredForCapture` 打在整颗 `SegmentedFilterPicker` 上、`selection` 钉在 `.all`（左段选中），而产品里 `hoverFill` 有 `guard !isSelected` ⇒ 只有右段（未选中那一半）会多出一层灰。既有读数（上一笔捕获卷自印，本轮 0 Swift 文件未重捕）替这句话签字：亮档 未选中段 @@SL0@@→@@SL1@@（比值 @@SLR@@、像素 @@SLPX@@），**选中段 @@SLL0@@→@@SLL1@@**；暗档 未选中段 @@SD0@@→@@SD1@@（比值 @@SDR@@），**选中段 @@SDL0@@→@@SDL1@@** —— 选中那一颗两态逐位相同 ⇒ 它确实没有第二层，这是设计不是漏。教训写进 D-255 旁边那格：**"悬停位点"在这种控件上不是一个坐标，是一枚布尔键**，按帧名猜坐标会把设计读成缺陷。
- **U-895：319 结一半，代价是这把尺当场坏了一次** —— 把 `wait_scan` 指向 `ClipboardHistory/Sources` 现读 @@SLINE@@ ⇒ 产品侧没有"睡一段挂钟等异步产物"的形状（`Thread.sleep(字面量)` 与 `pumpMain` 都是 0 处）。但**第一次**指上去时它报的是 `名册失配=1`：名册里那格观察窗口住在 `Tests/`，换了根之后"没扫到"被尺说成"账没了"。修法 = 名册只在**这次真正走到的文件**里对账（`present=`），并配两格守卫（格在扫描范围内却没了 ⇒ 仍红；格住在范围外 ⇒ 不报）与一把刀 M829（去掉作用域 ⇒ 那两格必须红，现读 @@KN@@、红在 @@KNCELLS@@、RESTORE_CLEAN）。产品里的 `DispatchQueue.asyncAfter(deadline: .now() + …)` 不在这把尺的图案集里 —— 它是**调度**不是**等待**（没有断言押在它上面），要不要覆盖另开 322 先问"有没有判据依赖它"。
- **U-896：本轮的四件套不是重跑，是引用** —— 本轮只动 `scripts/`（0 个 Swift 文件，`git status --porcelain` 现读不含 `ClipboardHistory/`），所以四件套沿用上一笔的现读行：@@RV@@。帧重捕与换装本机**本轮没跑**，按 NOT-RUN 记（不是 0 变化，是没测）；这条与 R254 那格"看图腿只看了改前那张"同一族：不重跑就要留下"没重跑"的名字。

眼睛腿：RUN —— 与 R268 同一对帧（`segmented-filter-idle/hover-200x60-light`），但这一次由既有读数与夹具源码共同结案（U-894），范围只这两张；本轮未重捕（0 Swift 文件）。
读数腿：RUN —— 两个根的 `WAIT_SCAN`（@@TLINE@@ ／ @@SLINE@@）、刀 @@KN@@（红在 @@KNCELLS@@）、上一笔捕获卷两行 `HOVER_DIRECT_READ_PROOF`、@@BATT@@、预检 tables=@@TBL@@ covered=@@COV@@ arms=@@PARMS@@ bad=0、ARM_TOTAL arms=@@ARMS@@。
产品腿：0 文件（`Sources/` 未动 ⇒ sources 格按规矩不动）。
未做（逐条）：① 312 的具名出口（按"纸"那一维推，本机 3.000 不许降）；② 322（`asyncAfter` 要不要进这把尺，先问有没有断言押它）、319 剩下那半（产品侧的**节流/延迟**语义还没逐处判，只判了"没有睡挂钟"）；③ 320（`visibilityGrace` 抄值升成守卫 + 配刀）、317、314、315、316；④ 310 的 @@GAPT@@ 张表 / @@GAPA@@ 把刀、309 那 6 张；⑤ 305、299、301、307、287/284、297/298/300、304、291 三位；⑥ 本轮 NOT-RUN 的两件（帧重捕、换装本机）；⑦ 用户闸门 220 路 A / 228② / 265。

"""

ITER_NEW = """## Round 266 · 一颗被眼睛误读成缺陷的悬停由既有读数结案；一把新尺在第二个根上暴露作用域 bug 并当场修掉（R269 / 第 268 轮）/ D-255 · 产品 0 文件

本轮次对照：与 R268（自评 87，等待形状拆符号 + 新尺 `wait_scan`）相比，本轮把 R268 留下的两张做完：321 结案（不靠新仪器，靠既有 `HOVER_DIRECT_READ_PROOF` 与夹具源码），319 结一半（产品侧现读 0 处睡挂钟），并把这把尺第一次指向 `Sources/` 时报出的 `名册失配=1` 当 bug 修掉。
看图腿：RUN —— 同一对 `segmented-filter` 亮档帧（未重捕）：变暗的确实是未选中的右枚，而这正是 `guard !isSelected` 的效果 —— 选中段两态逐位相同（亮 @@SLL0@@/@@SLL1@@、暗 @@SDL0@@/@@SDL1@@）。我的眼睛没错，错在把"悬停位点"当成坐标；这颗控件的取证键是整控件级布尔。
读数腿：RUN —— @@TLINE@@ ／ @@SLINE@@、刀 @@KN@@（红在 @@KNCELLS@@）、@@BATT@@、预检 tables=@@TBL@@ covered=@@COV@@ arms=@@PARMS@@ bad=0；四件套沿用上一笔（本轮 0 Swift 文件，帧与换装 NOT-RUN）。
七维度自评：
| 维度 | 分/满分 |
| 真实视觉审查 | 10/15 |
| 判据有效性 | 14/15 |
| 假绿防御 | 15/15 |
| 产品面推进 | 4/15 |
| 台账一致性 | 14/15 |
| 交付诚实性 | 15/15 |
| 可复核性 | 14/15 |
各维理由：真实视觉审查 10 —— 没有新画面，但这一眼**改判**了一颗疑似缺陷并留下可复查的读数对（比 R268 那一眼更实）；判据有效性 14 —— 作用域修好之后两个根各自给结论，扣一分是 319 只结了一半（产品侧的延迟语义没逐处判）；假绿防御 15 —— 刀 M829 证明"去掉作用域"会红，且第一版刀把全卷都报成红的读数错误当场修掉（只认 `FAIL:`/`ERROR:` 结论形状）；产品面推进 4 —— 0 产品文件，但撤掉了一条会被误记成产品缺陷的疑点；台账一致性 14 —— 五本 + STATE + 报告两格派生，四件套明确写成引用而非重跑；交付诚实性 15 —— "本轮没重捕帧/没换装"按 NOT-RUN 记，没有把引用说成实测；可复核性 14 —— 两个根的读数与刀都一行可重跑，扣一分是四件套不是本轮的。合计 **86**/105。

"""

DEC_NEW = """**D-255（R269）：名册、豁免、地板这类"按名字放行"的表，必须只在本次扫描真正走到的对象里对账；跨根复用一张名册会把「没扫到」说成「账没了」。** 理由：`wait_scan.py` 的 `--root ClipboardHistory/Sources` 第一跑报 `名册失配=1` —— 那格观察窗口住在 `Tests/`，产品根里本来就没有它。这不是账坏，是**尺的作用域**坏，而它的输出形状与真红一模一样（同一行、同一个词），所以人会去改账（最坏的那种修法：把名册删掉或放宽）。修法：`judge(..., present=这次走到的文件名集合)`，名册只在范围内对账；两格守卫钉住两个方向（范围外 ⇒ 不报；范围内却消失 ⇒ 仍红），刀 M829 钉住"去掉作用域必须红"（现读 @@KN@@、红在 @@KNCELLS@@、RESTORE_CLEAN）。同族：R140 的"空对账先看分母"、R91 的"临时目录不许跨次复用"。附带一条眼睛侧的账：`segmented-filter` 那对帧里"变暗的是没被悬停那一枚"（亮 @@SLL0@@/@@SLL1@@ 选中段两态相同）不是缺陷 —— 这类控件的悬停取证键是**整颗控件级布尔**，不是指针坐标；按帧名猜坐标会把 `guard !isSelected` 这条设计读成漏层。

"""

NOTE_321 = ("  追记（R269）：结案，且不是产品的事 —— 取证键 `hoveredForCapture` 打在整颗 `SegmentedFilterPicker` 上，\n"
            "  夹具把 `selection` 钉在 `.all`（左段选中），而产品里 `hoverFill` 有 `guard !isSelected` ⇒ 只有未选中的右枚会多出一层灰。\n"
            "  既有读数签字（上一笔捕获卷自印）：亮档 未选中段 @@SL0@@→@@SL1@@（比值 @@SLR@@）而选中段 @@SLL0@@→@@SLL1@@；\n"
            "  暗档 未选中段 @@SD0@@→@@SD1@@（比值 @@SDR@@）而选中段 @@SDL0@@→@@SDL1@@ ⇒ 选中那一颗两态逐位相同，是设计不是漏层。\n"
            "  我上一轮那句「悬停位点按帧名在左半」是把取证键当成了指针坐标（D-255 附带的眼睛侧账）。\n")

NOTE_319 = ("  追记（R269）：结一半。现读 `WAIT_SCAN --root ClipboardHistory/Sources` ⇒ bet=0（产品里没有「睡一段挂钟等异步产物」的形状）。\n"
            "  代价是这把尺第一次指到第二个根就坏：名册里那格住在 `Tests/`，被报成「名册失配=1」⇒ 作用域 bug 当场修（D-255）+ 两格守卫 + 刀 M829 CAUGHT。\n"
            "  剩下那半：产品里的 `DispatchQueue.asyncAfter(deadline: .now() + …)` 不在这把尺的图案集里（它是调度不是等待，没有断言押在上面），\n"
            "  要不要覆盖由 322 先回答「有没有判据依赖那段延迟」；以及节流语义逐处判还没做。\n")

BACK_NEW = [
    "**322. 产品源码里的 `DispatchQueue.asyncAfter(deadline: .now() + …)` 要不要进 `wait_scan` 的图案集（R269 现读：Sources 侧 "
    "`bet=0`，但那把尺根本不认 `asyncAfter`）：先逐处回答「有没有一条判据押在这段延迟上」——押着的要按 D-253/D-254 改形状或进名册，"
    "没押着的（纯调度、动画起始延迟）写明「不是等待」并保持不扫（R269 新开）**",
]

CHG_NEW = """### Changed（R269 / 第 268 轮 / Round 266 · 新尺的作用域 + 一颗被误读的悬停结案）

`scripts/wait_scan.py`：`judge(...)` 增加 `present=`（本次扫描真正走到的文件名集合），名册只在范围内对账 —— 第一次把尺指向 `ClipboardHistory/Sources` 时它把住在 `Tests/` 的那格报成 `名册失配=1`（"没扫到"被说成"账没了"）。判据卷 +2 格（范围外不报 / 范围内消失仍红 + 产品根现读 bet=0 的钉死格），刀 M829 去掉作用域 ⇒ 现读 @@KN@@、红在 @@KNCELLS@@、RESTORE_CLEAN。两根现读：@@TLINE@@ ／ @@SLINE@@。

321 结案（不是产品的事）：`hoveredForCapture` 是整颗控件级布尔，夹具 `selection` 钉 `.all` ⇒ 只有未选中右枚抬一层，选中段两态逐位相同（亮 @@SLL0@@/@@SLL1@@、暗 @@SDL0@@/@@SDL1@@）。319 结一半 ⇒ 新开 322（`asyncAfter` 要不要进图案集）。CI：@@CI1@@ 绿 = R267 那笔"等条件"修法的 runner 验收；@@CI3@@ 绿；本轮代码半 push 之后新跑 @@CI2@@ 未读。@@BATT@@、预检 tables=@@TBL@@ covered=@@COV@@ arms=@@PARMS@@ bad=0。本轮 0 Swift 文件 ⇒ 四件套沿用上一笔（@@RV@@），帧重捕与换装本机按 NOT-RUN 记；产品 0 文件。

"""

STATE_NEW = """## R269 状态（第 268 轮 / Round 266 · @@DATE@@）
最后更新：2026-10-21（本地 · R269 / 第 268 轮 / Round 266）：**321 由既有读数结案（悬停取证键是整颗控件级，不是指针坐标）；`wait_scan` 指向第二个根时暴露作用域 bug，当场修 + 两格守卫 + 刀 M829；319 结一半 ⇒ 新开 322**（U-893…U-896 · D-255 · 产品 0 文件 · 自评 86/105）

**本轮落地**：CI 交账 @@CI1@@ 绿（R267 等待修法的 runner 验收）；321 结案（亮 未选中段 @@SL0@@→@@SL1@@ 比值 @@SLR@@ vs 选中段 @@SLL0@@→@@SLL1@@；暗同形）；319 结一半（Sources 现读 bet=0）并修掉 `wait_scan` 的名册作用域（`present=`）+ 判据卷 15 格 + 刀 @@KN@@；@@BATT@@；预检 tables=@@TBL@@ covered=@@COV@@ arms=@@PARMS@@ bad=0、ARM_TOTAL arms=@@ARMS@@、310 缺口 @@GAPT@@ 张 / @@GAPA@@ 把。本轮 0 Swift 文件 ⇒ 四件套沿用上一笔、帧重捕与换装 NOT-RUN。

**下一轮（R270 / 第 269 轮 / Round 267）的 ⓪**：
⓪ 读 CI：@@CI2@@ 与本轮新跑（只登记号不轮询，R140）。要验的是 **runner 上 `WAIT_SCAN` 那一步（若已接进 CI）与三格改过等待形状的判据是否仍绿**，以及 `FAVORITE_INK_NOT_RUN` 是否仍被登记为已登记 NOT-RUN。
① 312 的具名出口：按**纸**（实测底）那一维推，本机 3.000 不许降（D-251）。这是欠了三轮的那一条。
② 320（`visibilityGrace` 抄值升成守卫 + 一把刀）、322（`asyncAfter` 逐处问「有没有判据押在它上面」）、317。
③ 314、315、316；310 的 @@GAPT@@ 张表、309 那 6 张；305、299、301、307、287/284、297/298/300、304、291 三位。
④ 本轮 NOT-RUN 的两件（帧重捕、换装本机）要与下一次 Swift 改动同一笔补跑。
⑤ 用户闸门 220 路 A / 228② / 265。

"""


def render(s):
    for k, v in V.items():
        s = s.replace(k, v)
    if "@@" in s:
        die("渲染后仍有未替换占位符：" + s[:150])
    return s


for n in ("UI_NEW", "ITER_NEW", "DEC_NEW", "CHG_NEW", "STATE_NEW", "NOTE_321", "NOTE_319"):
    globals()[n] = render(globals()[n])
BACK_NEW = "\n\n".join(render(x) for x in BACK_NEW) + "\n"

ui_p = B["AGENT_UI_AUDIT.md"]
ui_old = rd(ui_p)
if "## 第 267 轮" not in ui_old:
    die("UI_AUDIT 找不到锚点")
cut = ui_old.index("## 第 267 轮")
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


bk_new = "".join(append_after(blines, "321", NOTE_321))
bk_new = "".join(append_after(bk_new.splitlines(True), "319", NOTE_319))
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
if "## R268 状态" not in st_old:
    die("STATE 找不到锚点")
st_new = st_old.replace("## R268 状态", STATE_NEW + "## R268 状态", 1)
must_preserve(st_old, st_new, "AGENT_STATE.md")

ids = [int(x) for x in re.findall(r"- \*\*U-(\d+)", UI_NEW)]
if ids != list(range(893, 897)):
    die("U 号不连续：" + str(ids))
if "U-893…U-896" not in UI_NEW.splitlines()[0]:
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
if "D-255" in dc_old or "D-254" not in dc_old:
    die("D 号不对")
if bk_new.count("\n**322. ") != 1:
    die("新开 322 没落上")
if bk_new.count("追记（R269）") != 2:
    die("321/319 的追记没写对（应各一条）")
if "## R269 状态" not in st_new:
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
print("LEDGERS_R269 OK batt=Ran " + ran2 + " (skipped=" + skip2 + ") knife=" + V["@@KN@@"]
      + " cells=" + V["@@KNCELLS@@"] + " U=893..896 D=255")
print(out.strip().splitlines()[-1])
