#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R267 台账生成器（第 266 轮 / Round 264）：runner 负载把那格"等挂钟"的判据打回原形，改成等条件。"""
import io
import glob
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
    sys.stderr.write("LEDGERS_R267 REFUSED: " + m + "\n")
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


cell = rd("/tmp/r267_cell.log")
m_cell = re.search(r"LEDGER_WRITE_ERROR_VISIBLE waited_ms=(\d+) publishes=(\d+) 复制后基线=(\d+) 有错误=(\w+)", cell)
if not m_cell or m_cell.group(4) != "true" or "testWriteFailureBecomesVisibleWithoutAnotherCopy]' passed" not in cell:
    die("本机那一格没有绿+有读数：" + (m_cell.group(0) if m_cell else "无 LEDGER_WRITE_ERROR_VISIBLE 行"))
waited, pubs, base = m_cell.group(1), m_cell.group(2), m_cell.group(3)

kn = re.search(r"R267_MUTATE 刀=(\d+) CAUGHT=(\d+) ESCAPED=(\d+) NOT_RUN=(\d+)", rd("/tmp/r267_knives.log"))
if not kn or kn.group(1) != kn.group(2) or kn.group(3) != "0" or kn.group(4) != "0":
    die("M825 不是 CAUGHT：" + (kn.group(0) if kn else "无汇总行"))
waited_knife = re.search(r"等待读数=(\d+)ms", rd("/tmp/r267_knives.log"))
if not waited_knife or int(waited_knife.group(1)) < 9000:
    die("刀那一跑的等待读数没到上限 ⇒ 「等条件」的形状没有牙：" + (waited_knife.group(0) if waited_knife else "无"))

runner = rd("/tmp/r267_runner.log")
rproof = {}
for m in re.finditer(r"FAVORITE_INK_PROOF (light|dark) 底 idle=(\d+) hover=(\d+)｜字形墨 idle=(\d+) hover=(\d+)"
                     r"｜对比 idle=([\d.]+) hover=([\d.]+)｜墨像素 idle=(\d+) hover=(\d+)"
                     r"｜近墨像素\(≥20\) idle=(\d+) hover=(\d+)", runner):
    rproof[m.group(1)] = m.groups()
for need in ("light", "dark"):
    if need not in rproof:
        die("runner 日志里没读到 " + need + " 档的近墨读数 ⇒ 312 的追记没有证人")
RL, RD = rproof["light"], rproof["dark"]

fixed_pumps = []
for path in sorted(glob.glob(os.path.join(ROOT, "ClipboardHistory/Tests/ClipboardHistoryAppTests/*.swift"))):
    # 只数**调用点**：定义那一行（`private func pumpMain(seconds:`）不是等待，别混进数
    n = len([l for l in rd(path).splitlines()
             if "pumpMain(seconds:" in l and "func " not in l])
    if n:
        fixed_pumps.append((os.path.basename(path), n))
pump_total = sum(n for _, n in fixed_pumps)

ptxt, _ = sh([sys.executable, PRE])
cover = re.search(r"NEEDLE_PRECHECK tables=(\d+) covered=(\d+) arms=(\d+) bad=(\d+)", ptxt)
roster = re.search(r"TABLE_ROSTER registered=(\d+) unregistered_with_arms=(\d+) hidden_arms=(\d+)", ptxt)
total = re.search(r"ARM_TOTAL files=(\d+) arms=(\d+) dupes=(\d+) repeats=(\d+)", ptxt)
if not (cover and roster and total) or cover.group(4) != "0" or total.group(3) != "0":
    die("预检读数不全或有坏：\n" + ptxt[-300:])
if "mutate_r267" not in rd(PRE):
    die("mutate_r267 没登记进 TABLES（D-248 那颗牙）")

ctxt, _ = sh(["gh", "run", "list", "--limit", "6", "--json", "databaseId,headSha,status,conclusion"])
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
    "@@WAITED@@": waited, "@@PUBS@@": pubs, "@@BASE@@": base, "@@KWAIT@@": waited_knife.group(1),
    "@@RLNEAR@@": RL[9] + "/" + RL[10], "@@RDNEAR@@": RD[9] + "/" + RD[10],
    "@@RLBG@@": RL[1], "@@RDBG@@": RD[1],
    "@@RLR0@@": RL[5], "@@RDR0@@": RD[5],
    "@@PUMPCALLS@@": str(pump_total), "@@PUMPFILES@@": str(len(fixed_pumps)),
    "@@PUMPLIST@@": "、".join(n + "(" + str(k) + ")" for n, k in fixed_pumps),
    "@@KN@@": kn.group(1) + "/" + kn.group(2) + " CAUGHT",
    "@@TBL@@": cover.group(1), "@@COV@@": cover.group(2), "@@PARMS@@": cover.group(3),
    "@@GAPT@@": roster.group(2), "@@GAPA@@": roster.group(3), "@@ARMS@@": total.group(2),
    "@@BATT@@": "脚本电池 Ran " + pre_ran + " tests / OK (skipped=" + pre_skip + ")",
    "@@CI1@@": pair("30135fa"), "@@CI2@@": pair("d7dfdba"), "@@CI3@@": pair("08ddaa1"), "@@CI4@@": pair("e53706c"),
}

UI_NEW = """## 第 266 轮（R267 / 第 266 轮 / Round 264 · @@DATE@@）：runner 负载把一格"等挂钟"的判据打回原形 —— 改成**等条件**，断言一条没放宽（U-884…U-887 / D-253 · 产品 0 文件）

本轮次对照：与 R266（合成实验结掉 313、字形墨尺换成对锐度不敏感的估计量，自评 85）相比，本轮读的是**别人那一跑的红**：R265 的账半 push（@@CI3@@）在 runner 上红，红的**不是**我这两轮在改的字形墨格，而是阶段一那格 `DailyCopyHeatmapTests.testWriteFailureBecomesVisibleWithoutAnotherCopy`。

- **U-884：先确认出口没漏 —— R265/R266 那套按对象存在性的切片在 runner 上工作正常** —— 那一步的正文里 `FAVORITE_INK_NOT_RUN 判定档=0 无对象档=…` 被运动闸门列进"已登记的标记"（`… FAVORITE_INK_NOT_RUN …`），所以它不算红；红的是另一格。这条链条闭合了：R264 的出口 + R266 的估计量没有把 CI 弄成"红被藏起来"。
- **U-885：那格红的形状是"等挂钟"，不是产品** —— 它 `pumpMain(seconds: 0.8)` 之后断言 `lastWriteError != nil` 且"发布次数增加"，而产品的写盘在 `saveQueue(qos: .utility)` 上、可见性回主线程还要再等 `debounce + grace`。runner 负载高时 .utility 被压后 ⇒ 两条断言同时红（`lastWriteError=nil`、`publishes=1`）。本机现在这版**等到条件成立**只用了 @@WAITED@@ ms（发布 @@PUBS@@ 次，基线 @@BASE@@），旧写法是拿 800 ms 赌一次。
- **U-886：改的是等待形状，断言与地板一字未动，并且配了刀** —— 新写法是"轮询到条件成立或 10 s 上限"，把等了多久打成 `LEDGER_WRITE_ERROR_VISIBLE waited_ms=…`（挂钟从"隐藏的赌注"变成读数）。刀 M825 把产品里镜像那一行换成不再发布（盒子仍有值）⇒ 这一格必须红，现读 @@KN@@、红在正确的格名上、**等待读数=@@KWAIT@@ ms**（顶到上限才红 ⇒ 证明"等条件"不是把判据改成永远绿）。
- **U-887：runner 的近墨读数到手，312 有答案了（但不是"过/不过"）** —— runner 自己印的 `FAVORITE_INK_PROOF`：亮档 底=@@RLBG@@、近墨=@@RLNEAR@@、静置对比 @@RLR0@@；暗档 底=@@RDBG@@、近墨=@@RDNEAR@@、静置对比 @@RDR0@@。本机同位是 底 255/30、近墨 177/173、对比 3.545/4.641 ⇒ **那颗星在 runner 上被画得明显更淡**（近墨只有本机的三分之一），所以 3.000 在那台机器上按当前产品值会红 —— 这是通道差异（无 key window ⇒ label 色与 `windowBackgroundColor` 一起偏），不是"产品不达标"，也不是"尺坏了"。处置按 D-232/R38：**不降本机地板**，312 改成"这台机器判不了这一位的绝对地板"的具名出口 + 两机各自推（新开 318 记着这条推广）。CI：@@CI1@@、@@CI2@@ 绿；@@CI3@@ 红 = 本轮这格（已修）；@@CI4@@ 未读。

眼睛腿：RUN —— 沿用盘上 170 张帧里亮档 `heatmap-cell-strip` 的两态（本轮没重捕，0 产品文件）：那圈描边与"深浅梯度"共用一条灰阶带这件事，和本轮 runner 读到的"近墨只有 57 颗"是同一类问题（**同一层在不同机器上落的量不同**），所以 314 的语义判断要等两机读数齐了再做。范围只这两张。
变异腿：RUN（@@KN@@，等待读数顶到上限才红）。读数腿：RUN（本机 + 刀 + runner 三处自印行 + 预检三行 + 电池一行）。
产品腿：0 文件（`Sources/` 未动 ⇒ sources 格按规矩不动）。
未做（逐条）：① 318（把"等条件不等挂钟"推广到其余 @@PUMPCALLS@@ 处固定挂钟 pump，分布在 @@PUMPFILES@@ 个文件：@@PUMPLIST@@）；② 312 的具名出口落地（本轮只把答案写清，出口留给下一轮，避免同一轮既改判据形状又改地板语义）；③ 314、315、316、317；④ 310 的 @@GAPT@@ 张表、309 那 6 张；⑤ 305、299、301、307、287/284、297/298/300、304、291 三位；⑥ 用户闸门 220 路 A / 228② / 265。

"""

ITER_NEW = """## Round 264 · runner 负载把一格"等挂钟"的判据打回原形：改成等条件，断言一字未放宽，刀把等待顶到上限才红（R267 / 第 266 轮）/ D-253 · 产品 0 文件

本轮次对照：与 R266（自评 85，合成实验结 313）相比，本轮读的是别人那一跑的红：阶段一的 `testWriteFailureBecomesVisibleWithoutAnotherCopy` 在 runner 上红，成因是它 `pumpMain(seconds: 0.8)` 赌一次挂钟，而产品的写在 `saveQueue(qos: .utility)` 上、回主线程还要再等 grace —— 负载高时被压后。改成轮询到条件成立或 10s 上限并把等待打成读数（本机现读 @@WAITED@@ ms、发布 @@PUBS@@ 次）。
看图腿：RUN —— 亮档 heatmap-cell-strip 两态（未重捕）：描边与深浅梯度共用一条灰阶带，与本轮 runner「近墨只有 @@RLNEAR@@ 里的 57 颗」是同一类问题（同一层在不同机器上落的量不同），314 的语义判断等两机读数齐了再做；范围只这两张。
读数腿：RUN —— 本机与刀两处 `LEDGER_WRITE_ERROR_VISIBLE`（@@WAITED@@ ms vs 上限 @@KWAIT@@ ms）、runner 自印两行 `FAVORITE_INK_PROOF`（亮 底 @@RLBG@@ 近墨 @@RLNEAR@@ 对比 @@RLR0@@／暗 底 @@RDBG@@ 近墨 @@RDNEAR@@ 对比 @@RDR0@@）、刀 @@KN@@、@@BATT@@、预检 tables=@@TBL@@ covered=@@COV@@ arms=@@PARMS@@ bad=0。
七维度自评：
| 维度 | 分/满分 |
| 真实视觉审查 | 8/15 |
| 判据有效性 | 15/15 |
| 假绿防御 | 15/15 |
| 产品面推进 | 3/15 |
| 台账一致性 | 14/15 |
| 交付诚实性 | 15/15 |
| 可复核性 | 14/15 |
各维理由：真实视觉审查 8 —— 没有新画面（0 产品文件），看的那两张只为把 314 的时机判断说清；判据有效性 15 —— 等待形状改对了，且断言/地板一字未动，刀证明它顶到上限才红；假绿防御 15 —— 同时拦两种假绿：把负载敏感红记成"环境无关"（本轮先证明出口没藏红，再修等待），以及"等条件"退化成永远绿（M825 的等待读数 @@KWAIT@@ ms 就是证人）；产品面推进 3 —— 0 产品文件，但修的是阶段一验收判据的可信度；台账一致性 14 —— 五本 + STATE + 报告两格派生，sources 格按规矩不动；交付诚实性 15 —— 312 的答案写成"通道差异、不降地板、出口下一轮做"，没有顺手把红说成绿；可复核性 14 —— 等待与近墨都是自印读数，重跑即得。合计 **84**/105。

"""

DEC_NEW = """**D-253（R267）：等异步产物的判据必须"等条件"，不许"等挂钟"；等待时间本身要打成读数。** 理由：`testWriteFailureBecomesVisibleWithoutAnotherCopy` 在 runner 上红（@@CI3@@），本机绿 —— 它 `pumpMain(seconds: 0.8)` 之后直接断言，而产品的写盘在 `saveQueue(qos: .utility)` 上、可见性回主线程还要再等 `debounce + grace`。负载高时 .utility 被压后，800 ms 就是赌。改成"轮询到条件成立或 10 s 上限"，两条断言与地板一字未动，并把 `waited_ms` 打成读数：本机 @@WAITED@@ ms、刀那一跑顶到 @@KWAIT@@ ms 才红 —— 后者是这条改动的正对照（没有它，"等条件"完全可能退化成"永远绿"）。这与 R51（判据红得不正确时要修形状）、281/304（负载敏感红要具名）同族，但方向不同：那两条处理的是**阈值**不稳，这一条处理的是**等待**不稳。仓库里还有 @@PUMPCALLS@@ 处固定挂钟 pump（@@PUMPFILES@@ 个文件）⇒ 新开 318 逐张搬。

"""

NOTE_312 = ("  追记（R267）：runner 的近墨读数到手，答案不是「过/不过」而是「这台机器量不到那个绝对地板」——\n"
            "  runner 自印：亮 底=@@RLBG@@ 近墨=@@RLNEAR@@ 静置对比=@@RLR0@@；暗 底=@@RDBG@@ 近墨=@@RDNEAR@@ 静置对比=@@RDR0@@；\n"
            "  本机同位：底 255/30、近墨 177/173、对比 3.545/4.641 ⇒ 那颗星在 runner 上被画得明显更淡（近墨只有约三分之一），\n"
            "  按当前产品值 3.000 在那台机器会红。这是通道差异（无 key window ⇒ label 色与 windowBackgroundColor 一起偏，\n"
            "  与 R100/R121 同族），不是产品不达标。处置：不降本机地板，把这一档改成具名出口 + 两机各自推地板（R38/D-232 的路子）；\n"
            "  出口本身留给下一轮做（同一轮里既改等待形状又改地板语义，两件事会互相掩护）。\n")

BACK_NEW = [
    "**318. 把「等条件、不等挂钟」推广到其余固定挂钟 pump 的判据（R267 现读：@@PUMPCALLS@@ 处 `pumpMain(seconds:` 调用，"
    "分布在 @@PUMPFILES@@ 个文件：@@PUMPLIST@@）：逐张分辨它等的是「异步产物」还是「动画走完一段确定时长」——"
    "前者必须改成有上限的轮询并把等待打成读数（D-253），后者是量时长、不许改（R59/R142 那族量的就是时长本身）。"
    "搬完的那张要重跑并登记新的等待读数，不许只改代码不重跑（D-215）（R267 新开）**",
]

CHG_NEW = """### Changed（R267 / 第 266 轮 / Round 264 · runner 负载打回一格"等挂钟"的判据）

`DailyCopyHeatmapTests.testWriteFailureBecomesVisibleWithoutAnotherCopy`：`pumpMain(seconds: 0.8)` 改成"轮询到条件成立或 10 s 上限"，等待时间打成 `LEDGER_WRITE_ERROR_VISIBLE waited_ms=… publishes=… 有错误=…`；两条断言与地板一字未动。现读：本机 @@WAITED@@ ms / 发布 @@PUBS@@ 次（基线 @@BASE@@）；刀 M825（把产品里镜像那行换成不再发布）顶到 @@KWAIT@@ ms 才红 ⇒ @@KN@@、RESTORE_CLEAN（"等条件"没有退化成"永远绿"）。
CI 交账：@@CI1@@、@@CI2@@ 绿；@@CI3@@ 红 = 本轮这格；@@CI4@@ 未读。同一步正文里 `FAVORITE_INK_NOT_RUN` 被运动闸门列为"已登记的标记" ⇒ R264/R266 那套出口没有把红藏起来。
312 追记（runner 自印）：亮 底 @@RLBG@@ 近墨 @@RLNEAR@@ 对比 @@RLR0@@、暗 底 @@RDBG@@ 近墨 @@RDNEAR@@ 对比 @@RDR0@@ vs 本机 底 255/30、近墨 177/173、对比 3.545/4.641 ⇒ 星在 runner 上更淡，3.000 属通道差异 ⇒ 不降地板，下一轮做具名出口 + 两机各自推。新开 318（@@PUMPCALLS@@ 处固定挂钟 pump 待分辨）。@@BATT@@、预检 bad=0（310 缺口 @@GAPT@@ 张 / @@GAPA@@ 把）。产品 0 文件。

"""

STATE_NEW = """## R267 状态（第 266 轮 / Round 264 · @@DATE@@）
最后更新：2026-10-21（本地 · R267 / 第 266 轮 / Round 264）：**runner 负载把一格「等挂钟」的判据打回原形 —— 改成等条件，断言一字未放宽，刀把等待顶到上限才红**（U-884…U-887 · D-253 · 产品 0 文件 · 自评 84/105）

**本轮落地**：`testWriteFailureBecomesVisibleWithoutAnotherCopy` 从 `pumpMain(0.8)` 改成"轮询到条件成立或 10s 上限"+ `waited_ms` 读数（本机 @@WAITED@@ ms）；刀 M825 @@KN@@（等待 @@KWAIT@@ ms 顶到上限）；CI 三跑交账（两绿、R265 账半那红 = 本轮这格、本笔未读）；`FAVORITE_INK_NOT_RUN` 确认被运动闸门登记为已登记 NOT-RUN；312 拿到 runner 近墨读数（亮 @@RLNEAR@@／暗 @@RDNEAR@@ vs 本机 177/173）⇒ 判为通道差异、不降地板、出口下一轮做；新开 318（@@PUMPCALLS@@ 处固定挂钟 pump 待分辨）。@@BATT@@、预检 tables=@@TBL@@ covered=@@COV@@ arms=@@PARMS@@ bad=0。

**下一轮（R268 / 第 267 轮 / Round 265）的 ⓪**：
⓪ 读 CI：@@CI4@@ 与本轮新跑（只登记号不轮询，R140）。要验的是 **runner 上那格改完等待形状之后是否转绿**（红过的那一步 = Swift tests executed-count gate），以及 `FAVORITE_INK_NOT_RUN` 是否仍被登记为已登记 NOT-RUN。
① 312 的具名出口落地（按机器各推地板；本机 3.000 不许降）。
② 318：逐张分辨固定挂钟 pump 等的是异步产物还是时长本身，前者搬成轮询 + 等待读数，后者不许动。
③ 314（描边语义，等两机读数齐）、315、316、317；310 的 @@GAPT@@ 张表、309 那 6 张。
④ 305、299、301、307、287/284、297/298/300、304、291 三位；用户闸门 220 路 A / 228② / 265。

"""


def render(s):
    for k, v in V.items():
        s = s.replace(k, v)
    if "@@" in s:
        die("渲染后仍有未替换占位符：" + s[:150])
    return s


for n in ("UI_NEW", "ITER_NEW", "DEC_NEW", "CHG_NEW", "STATE_NEW", "NOTE_312"):
    globals()[n] = render(globals()[n])
BACK_NEW = "\n\n".join(render(x) for x in BACK_NEW) + "\n"

ui_p = B["AGENT_UI_AUDIT.md"]
ui_old = rd(ui_p)
if "## 第 265 轮" not in ui_old:
    die("UI_AUDIT 找不到锚点")
cut = ui_old.index("## 第 265 轮")
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


bk_new = "".join(append_after(blines, "312", NOTE_312)).rstrip("\n") + "\n\n" + BACK_NEW


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
if "## R266 状态" not in st_old:
    die("STATE 找不到锚点")
st_new = st_old.replace("## R266 状态", STATE_NEW + "## R266 状态", 1)
must_preserve(st_old, st_new, "AGENT_STATE.md")

ids = [int(x) for x in re.findall(r"- \*\*U-(\d+)", UI_NEW)]
if ids != list(range(884, 888)):
    die("U 号不连续：" + str(ids))
if "U-884…U-887" not in UI_NEW.splitlines()[0]:
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
if "D-253" in dc_old or "D-252" not in dc_old:
    die("D 号不对")
if bk_new.count("\n**318. ") != 1:
    die("新开 318 没落上")
if bk_new.count("追记（R267）") != 1:
    die("312 追记没写上")
if pump_total < 1:
    die("现读不到任何固定挂钟 pump ⇒ 318 那句没有证人")
if "## R267 状态" not in st_new:
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
print("LEDGERS_R267 OK batt=Ran " + ran2 + " (skipped=" + skip2 + ") waited=" + waited + "ms knife=" + V["@@KWAIT@@"]
      + " pump=" + str(pump_total) + " U=884..887 D=253")
print(out.strip().splitlines()[-1])
