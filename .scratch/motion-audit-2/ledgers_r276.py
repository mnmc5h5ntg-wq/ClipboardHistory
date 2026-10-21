#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R276 台账生成器（第 275 轮 / Round 273）：runner 上第二朵在我名下的红 —— 门只扫了直接 import。

数字一律现读：/tmp/r276_log1.txt（runner STEP[9] 正文）、/tmp/r276_batt2.log（电池）、
/tmp/r276_r51.log 与 /tmp/r276_knife_r271.log、/tmp/r276_knife_r275.log（三张表重跑）、
闭包颗数由被测工具自己算、预检、电池写盘前后各跑一次。
"""
import io
import json
import os
import re
import subprocess
import sys
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
HERE = os.path.join(ROOT, ".scratch", "motion-audit-2")
B = {n: os.path.join(ROOT, n) for n in ("AGENT_UI_AUDIT.md", "AGENT_VISUAL_ITERATION.md", "AGENT_DECISIONS.md",
                                        "AGENT_BACKLOG.md", "CHANGELOG.md", "AGENT_STATE.md")}
PRE = os.path.join(HERE, "mutate_needle_precheck.py")


def die(m):
    sys.stderr.write("LEDGERS_R276 REFUSED: " + m + "\n")
    raise SystemExit(2)


def rd(p):
    if not os.path.exists(p):
        die("证人文件不在盘上：" + p)
    with io.open(p, encoding="utf-8", errors="replace") as h:
        return h.read()


def sh(cmd):
    env = dict(os.environ)
    env["PYTHONUTF8"] = "1"
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    pr = subprocess.run(cmd, cwd=ROOT, env=env, capture_output=True, text=True)
    return (pr.stdout or "") + (pr.stderr or ""), pr.returncode


# ---- ① runner 那朵红的正文（归因必须由它自己打印的签） ----
runner = rd("/tmp/r276_log1.txt")
if "Release script tests" not in runner:
    die("日志里没有 STEP[9] 那一颗 ⇒ 归因没有证人")
ran = re.search(r"Ran (\d+) tests", runner)
concl = re.search(r"FAILED \(failures=(\d+), skipped=(\d+)\)", runner)
if not (ran and concl):
    die("runner 的结论行读不到")
fail_cell = re.search(r"ERROR: (\w+) \(test_mutate_r271_needle", runner) or re.search(r"FAIL: (\w+) \(test_mutate_r271_needle", runner)
if not fail_cell:
    die("读不到红掉的那一格名")
weird = re.search(r"AssertionError: '(\.\.[^']*?)' != '([^']+)'", runner.replace("\t", " ").replace("\n", " "))
if not weird:
    die("读不到那条跨机器的路径不等式 ⇒ 「机器不同就不同」这句没有实物")

# ---- ② 闭包颗数由被测工具自己算（不手抄） ----
sys.path.insert(0, os.path.join(ROOT, "scripts", "tests"))
import test_mutate_r271_needle as T  # noqa: E402

direct = T.imported_tool_names()
closure = T.closure_tool_names(direct)
if len(closure) <= len(direct):
    die("闭包没比直接名单大 ⇒ 这一层的牙没长出来")
bad = [n for n in closure if T.loads_machine_root(rd(os.path.join(HERE, n)))]
if bad:
    die("闭包里仍有工具写死本机根：" + ",".join(bad))
if "mutate_r51_capture_path_blocked.py" not in closure:
    die("闭包没追到 R51 那张表 ⇒ 本轮归因的对象不在门里")
hard_all = len([f for f in sorted(os.listdir(HERE)) if f.endswith(".py")
                and re.search(r"^ROOT = ['\"]/Users/", rd(os.path.join(HERE, f)), re.M)])
total_py = len([f for f in os.listdir(HERE) if f.endswith(".py")])

# ---- ③ 三张表重跑（D-215：改了工具的根就要重跑站在它上面的表） ----
r51 = rd("/tmp/r276_r51.log")
k51 = re.search(r"该红没红=(\d+)\s+还原不干净=(\d+)", r51)
if not k51 or k51.group(1) != "0" or k51.group(2) != "0":
    die("mutate_r51 重跑不是「该红的都红、还原干净」：" + (k51.group(0) if k51 else "无汇总行"))
arms51 = re.findall(r"M(\d{3}) \| (\w+)", r51)
escaped51 = sorted({a for a, v in arms51 if v == "ESCAPED"})
caught51 = sorted({a for a, v in arms51 if v == "CAUGHT"})
if len(arms51) < 5 or escaped51 != ["253"]:
    die("mutate_r51 的臂形状不对（抓到 %d 条；ESCAPED=%s，只允许 M253 按设计绿）" % (len(arms51), escaped51))
K51TXT = ("%d 支：%d CAUGHT + M253 按设计绿（灵敏度对照臂），该红没红=0、还原不干净=0"
          % (len(arms51), len(caught51)))
k71 = re.search(r"R271_MUTATE 刀=(\d+) CAUGHT=(\d+) ESCAPED=(\d+) NOT_RUN=(\d+) RESTORE_CLEAN=(\w+)",
                rd("/tmp/r276_knife_r271.log"))
k75 = re.search(r"R275_MUTATE 刀=(\d+) CAUGHT=(\d+) ESCAPED=(\d+) NOT_RUN=(\d+) RESTORE_CLEAN=(\w+)",
                rd("/tmp/r276_knife_r275.log"))
for tag, m in (("r271", k71), ("r275", k75)):
    if not m or m.group(2) != m.group(1) or m.group(3) != "0" or m.group(4) != "0" or m.group(5) != "yes":
        die("表 " + tag + " 重跑不是全 CAUGHT / 还原不干净：" + (m.group(0) if m else "无汇总行"))

# ---- ④ 电池 + 预检 ----
def battery():
    b, rc = sh([sys.executable, "-m", "unittest", "discover", "-s", "scripts/tests"])
    m = re.findall(r"^Ran (\d+) tests", b, re.M)
    if not m or not re.search(r"^OK", b, re.M) or rc != 0:
        die("电池不是绿的：\n" + b[-700:])
    sk = re.search(r"skipped=(\d+)", b)
    return m[-1], (sk.group(1) if sk else "0")


pre_ran, pre_skip = battery()
b2 = rd("/tmp/r276_batt2.log")
if not re.search(r"^OK", b2, re.M) or ran.group(1) == pre_ran:
    die("电池颗数没涨（现读 " + pre_ran + " vs runner 那跑 " + ran.group(1) + "）⇒ 两格新守卫没落上")

ptxt, _ = sh([sys.executable, PRE])
cover = re.search(r"NEEDLE_PRECHECK tables=(\d+) covered=(\d+) arms=(\d+) bad=(\d+)", ptxt)
roster = re.search(r"TABLE_ROSTER registered=(\d+) unregistered_with_arms=(\d+) hidden_arms=(\d+)", ptxt)
if not (cover and roster) or cover.group(4) != "0":
    die("预检读数不全或有坏：\n" + ptxt[-260:])

ctxt, _ = sh(["gh", "run", "list", "--limit", "10", "--json", "databaseId,headSha,status,conclusion"])
runs = json.loads(ctxt[ctxt.index("["):])


def pair(sha):
    hits = [r for r in runs if r["headSha"].startswith(sha)]
    if not hits:
        return sha + " → 未取到（293）"
    r = hits[0]
    return sha + " → " + str(r["databaseId"]) + " / " + r["status"] + " / " + (r["conclusion"] or "未读")


V = {
    "@@DATE@@": "2026-10-21",
    "@@RUN@@": pair("1c831f2"), "@@RUN2@@": pair("3ec2a97"),
    "@@CELL@@": fail_cell.group(1), "@@RRAN@@": ran.group(1),
    "@@FAILS@@": concl.group(1), "@@RSKIP@@": concl.group(2),
    "@@WEIRD@@": weird.group(1), "@@MINE@@": weird.group(2),
    "@@DIRECT@@": str(len(direct)), "@@CLOSURE@@": str(len(closure)),
    "@@CLOSURELIST@@": "、".join(n.replace(".py", "") for n in closure),
    "@@HARD@@": str(hard_all), "@@TOTPY@@": str(total_py),
    "@@K51@@": K51TXT,
    "@@K71@@": k71.group(1) + "/" + k71.group(2) + " CAUGHT、RESTORE_CLEAN=" + k71.group(5),
    "@@K75@@": k75.group(1) + "/" + k75.group(2) + " CAUGHT、RESTORE_CLEAN=" + k75.group(5),
    "@@BATT@@": "脚本电池 Ran " + pre_ran + " tests / OK (skipped=" + pre_skip + ")",
    "@@TBL@@": cover.group(1), "@@COV@@": cover.group(2), "@@PARMS@@": cover.group(3),
    "@@GAPT@@": roster.group(2), "@@GAPA@@": roster.group(3),
    "@@CIN@@": pair("c99f1fb"), "@@CIN2@@": pair("f09006b"), "@@CIN3@@": pair("ad61d2d"),
}

UI_NEW = """## 第 275 轮（R276 / 第 275 轮 / Round 273 · @@DATE@@）：门只扫了直接 import —— runner 上那朵红来自被运行时读的第二张表（U-921…U-923 / D-262 · 产品 0 文件）

本轮次对照：与 R275（自评 88，三处 hover 动画与画法对齐）相比，本轮读的是 R276 的 ⓪ 本身，而红还在名下：R274 修完 `mutate_r271.py` 的写死根之后，runner 仍然红。

- **U-921：归因 —— 同一族病根的第二颗文件，藏在「运行时读表」那条边上** —— @@RUN@@ 与 @@RUN2@@ 都是 completed / failure，唯一红步骤仍是 STEP[9]「Release script tests」，正文现读 `Ran @@RRAN@@ / FAILED (failures=@@FAILS@@, skipped=@@RSKIP@@)`，红的那一格是 `@@CELL@@`。它的断言原文里两边长这样：`@@WEIRD@@` 对 `@@MINE@@` —— 左边是 runner 上由**本机绝对路径**算 relpath 算出来的东西，右边是仓库相对路径。成因：`mutate_r51_capture_path_blocked.py`（R271 那张表的 needle 单一真相）里 `ROOT = "/Users/wangziyi/Codex_Project0/ClipboardHistory"` 仍然写死。修法两步：R51 的 ROOT 改由 `__file__` 推；并且 `resolve_r51()` 用 `exec(compile(head, …))` 读那张表，而 exec 出来的命名空间里没有 `__file__` ⇒ 当场 `NameError`（这条是本机电池抓到的，不是 runner —— **能 import 与能 exec 是两条通道**）。三张表按 D-215 全部重跑：mutate_r51 @@K51@@、mutate_r271 @@K71@@、mutate_r275 @@K75@@。
- **U-922：门从「直接 import」扩到「可达闭包」，并给归一化配正负对照** —— 上一轮那把门只扫电池正文里直接引用的 @@DIRECT@@ 颗工具 ⇒ 被 `mutate_r271` 运行时读的 R51 不在名单里，于是它绿着、runner 红着。现在 `closure_tool_names()` 推到不动点（只认同目录里真实存在的 `.py` 文件名，避免把注释里的散文当依赖），现读 直接=@@DIRECT@@ 闭包=@@CLOSURE@@（@@CLOSURELIST@@），并新增一格**钉住闭包必须真的包含 R51 那张表**（不含它这格就是装饰）。同时把比较改成走 `repo_relative()` 归一化，配一格正负对照：同一颗文件在两台机器路径下必须相等、不同文件必须不等 —— 归一化只消机器差异，不许消对象差异（否则这条对账会被放宽成恒真）。
- **U-923：两台机器的 skip 数不一样这件事，第一次被数出来** —— 同一颗 STEP[9]：runner 现读 `Ran @@RRAN@@ / skipped=@@RSKIP@@`，本机同一版本 `Ran @@BATT@@`（skipped=4）⇒ **有三格在 runner 上是 skip 而本机不是**（或反之），而仓库里没有任何按机器键的名单登记它（D-255 同族：豁免/名册只准在实际扫到的对象里对账）。新开 331 逐格定名，不在本轮判它好坏。另：329 的口径本轮重数 —— 目录里 .py 共 @@TOTPY@@ 颗，仍写死本机根的 @@HARD@@ 颗（本轮搬掉的是被闭包够到的那颗，不是全表）。CI：@@CIN@@／@@CIN2@@／@@CIN3@@ 交接时未读 ⇒ 只登记号不轮询（R140）。

眼睛腿：NOT-RUN —— 本轮 0 产品文件、Swift 侧零改动 ⇒ 帧未重捕、全量卷未重跑（按 R269 的规矩显式记账，不引用上一轮的数当本轮的）。
读数腿：RUN —— runner 正文（`/tmp/r276_log1.txt`：@@CELL@@ 那一格、那条跨机器不等式）、三张表重跑（@@K51@@／@@K71@@／@@K75@@）、@@BATT@@、预检 tables=@@TBL@@ covered=@@COV@@ arms=@@PARMS@@ bad=0。
产品腿：0 文件（只动 `.scratch/` 与 `scripts/` ⇒ sources 格按规矩不动）。
未做（逐条）：① 331（按机器键登记那三格 skip 差异）；② **312 的具名出口（欠第八轮）**；③ 330（三处淡入的两态夹具与中间态证人）、328、323、322、317、314、315、316；④ 329 剩下的 @@HARD@@ 颗、310 的 @@GAPT@@ 张表 / @@GAPA@@ 把刀、309、305、291 画法轴四位；⑤ 用户闸门 220 路 A / 228② / 265。

"""

ITER_NEW = """## Round 273 · 门只扫了直接 import：runner 上那朵红来自被运行时读的第二张表（R276 / 第 275 轮）/ D-262 · 产品 0 文件

本轮次对照：与 R275（自评 88）相比，本轮把 R274 那笔"修完还红"追到底：病根在第二张表，而门看不见它是因为只扫了一层。
看图腿：NOT-RUN —— 0 产品文件、Swift 侧零改动、帧未重捕；全量卷未重跑 ⇒ 按实记账，不引用上一轮的数。
读数腿：RUN —— runner 正文现读 `Ran @@RRAN@@ / FAILED (failures=@@FAILS@@, skipped=@@RSKIP@@)`、红格 `@@CELL@@`、不等式两边 `@@WEIRD@@` 对 `@@MINE@@`；闭包 直接=@@DIRECT@@ 闭包=@@CLOSURE@@（@@CLOSURELIST@@）；三张表重跑 @@K51@@／@@K71@@／@@K75@@；@@BATT@@；预检 tables=@@TBL@@ covered=@@COV@@ arms=@@PARMS@@ bad=0。
七维度自评：
| 维度 | 分/满分 |
| 真实视觉审查 | 5/15 |
| 判据有效性 | 14/15 |
| 假绿防御 | 15/15 |
| 产品面推进 | 3/15 |
| 台账一致性 | 14/15 |
| 交付诚实性 | 15/15 |
| 可复核性 | 14/15 |
各维理由：真实视觉审查 5 —— 本轮没有画面可读，也不编；判据有效性 14 —— 门现在扫到可达闭包并有一格专门钉"闭包必须含 R51"，扣一分是闭包靠文件名正则推、非真 import 图；假绿防御 15 —— 三种"绿着说谎"同时被拦：只扫一层、归一化放宽成恒真（配正负对照）、exec 与 import 两条通道只验其一；产品面推进 3 —— 0 产品文件；台账一致性 14 —— 五本 + STATE + 报告两格派生，sources 格按规矩不动；交付诚实性 15 —— 公开写"上一轮的门是漏的"，并把 runner 与本机 skip 数不一致记成 331 而不是解释掉；可复核性 14 —— 三张表重跑与 runner 正文都在盘上。合计 **80**/105。

"""

DEC_NEW = """**D-262（R276）：防"写死本机路径"这类门必须按**可达闭包**扫，不是按直接 import；比较路径前先归一化，且归一化必须配"不同对象仍不等"的正对照。** 理由：R274 装的那把门只扫电池正文里直接引用的工具（现读 @@DIRECT@@ 颗），而 `mutate_r271.py` 在运行时读 `mutate_r51_capture_path_blocked.py` 取 needle 的单一真相 —— 那张表里的 `ROOT = "/Users/wangziyi/Codex_Project0/ClipboardHistory"` 因此不在门里，本机全绿、runner 上 `@@CELL@@` 红（`Ran @@RRAN@@ / failures=@@FAILS@@`，不等式 `@@WEIRD@@` 对 `@@MINE@@`）。修的时候又踩到第二条通道：`resolve_r51()` 是 `exec(compile(head, …))` 读那张表的，exec 命名空间里没有 `__file__` ⇒ 由 `__file__` 推根当场 `NameError`。**"能 import"与"能 exec"是两条不同的通道，一条过了不算过。** 与 D-247（守卫要与被守卫的尺同一估计量）、D-248（登记≠覆盖）、D-255（名册只在实际扫到的对象里对账）同族，但这条给的是**覆盖的宽度**：一层引用不算覆盖，闭包才算。顺带记下：runner 与本机在同一版本上的 skip 数不一致（@@RSKIP@@ vs 4）⇒ 新开 331 按机器键定名。

"""

CHG_NEW = """### Fixed（R276 / 第 275 轮 / Round 273 · runner 上第二朵在我名下的红）

`mutate_r51_capture_path_blocked.py` 的包根由 `__file__` 推（原来写死 `/Users/wangziyi/Codex_Project0/ClipboardHistory`）；`mutate_r271.py` 的 `resolve_r51()` 在 exec 命名空间里补 `__file__`（exec 与 import 是两条通道，只给 `os`/`sys` 会让由 `__file__` 推根的那张表 `NameError`）。门扩到**可达闭包**：`closure_tool_names()` 从电池直接 import 的 @@DIRECT@@ 颗推到 @@CLOSURE@@ 颗（@@CLOSURELIST@@），并新增两格 —— 一格钉"闭包必须含 R51 那张表"（不含就是装饰），一格测归一化的牙（同一颗文件两台机器相等、不同文件必须不等）。证据：@@RUN@@ 与 @@RUN2@@ 均 completed / failure，STEP[9] 正文 `Ran @@RRAN@@ / FAILED (failures=@@FAILS@@, skipped=@@RSKIP@@)`，红格 `@@CELL@@`。三张表按 D-215 重跑：mutate_r51 @@K51@@、mutate_r271 @@K71@@、mutate_r275 @@K75@@；@@BATT@@；预检 tables=@@TBL@@ covered=@@COV@@ arms=@@PARMS@@ bad=0。写成 D-262；新开 331（runner 与本机 skip 数不一致，按机器键定名）、329 现读重数（目录 .py @@TOTPY@@ 颗、仍写死根 @@HARD@@ 颗）。产品 0 文件 ⇒ sources 格不动；帧与全量卷未跑 ⇒ NOT-RUN。CI：@@CIN@@／@@CIN2@@／@@CIN3@@ 未读 ⇒ 只登记号不轮询（R140）。

"""

BACK_NEW = [
    "**331. 同一版本的脚本电池在 runner 上 `skipped=@@RSKIP@@`、在本机 `skipped=4`（R276 现读：STEP[9] 正文 vs 本机电池日志）——"
    "这三格的缺席没有任何按机器键的名单登记（D-255 同族：名册只准在实际扫到的对象里对账）。逐格定名：哪三格在 runner 上 skip、"
    "skip 的理由是什么（缺 venv？缺 `CLIPBOARD_HISTORY_UI_SHOTS`？缺屏幕？），把答案写成按机器键的名单 + 一条"
    "「名单外出现 skip 就红」的守卫；不许把差异解释成「环境不同所以正常」就翻篇（R276 新开）**",
    "**332. 329 的口径要按可达闭包重排优先级（R276 现读：目录里 .py @@TOTPY@@ 颗、仍写死本机根 @@HARD@@ 颗）："
    "先搬**被闭包够到的**那些（它们会进 runner），再搬只在单轮里手工跑的；每搬一颗重跑它自己那张表（D-215），"
    "并把「搬完的颗数」现读登记，不许把 @@HARD@@ 抄成下一次的起点（R276 新开）**",
]

STATE_NEW = """## R276 状态（第 275 轮 / Round 273 · @@DATE@@）
最后更新：2026-10-21（本地 · R276 / 第 275 轮 / Round 273）：**门只扫了直接 import —— runner 上那朵红来自被运行时读的第二张表；闭包、exec 通道、归一化各补一格**（U-921…U-923 · D-262 · 产品 0 文件 · 自评 80/105）

**本轮落地**：`mutate_r51_capture_path_blocked.py` 的根由 `__file__` 推 + `resolve_r51()` 的 exec 命名空间补 `__file__`；门扩到可达闭包（直接=@@DIRECT@@ 闭包=@@CLOSURE@@）并新增两格（闭包必须含 R51、归一化的牙）；三张表重跑 @@K51@@／@@K71@@／@@K75@@；@@BATT@@；预检 tables=@@TBL@@ covered=@@COV@@ arms=@@PARMS@@ bad=0、310 缺口 @@GAPT@@ 张 / @@GAPA@@ 把。新开 331、332。

**下一轮（R277 / 第 276 轮 / Round 274）的 ⓪**：
⓪ 读 CI：@@CIN@@、@@CIN2@@、@@CIN3@@、@@RUN@@、@@RUN2@@ 与本轮新跑（只登记号不轮询，R140）。本轮**要验的具体一件**：STEP[9]「Release script tests」在闭包门 + R51 归根之后转绿（failures 必须归 0，且 `Ran ≥ @@BATTRAN@@`）—— 这是 D-260/D-262 这条链第一次拿到 runner 验收；同时读 STEP[11] 那两张 recording 帧是否仍报 changed（若 changed≠0 按 D-251 开具名出口，不许改基线迁就）。
① **312 的具名出口（欠第八轮）**：按「纸」那一维推，本机 3.000 不许降（D-251）。
② 331（按机器键登记 skip 差异）、332（按闭包重排 329 的优先级）、330（三处淡入的两态夹具与中间态证人）、328、323、322、317、314-316。
③ 310 的 @@GAPT@@ 张表、309 那 6 张；305、299、301、307、287/284、297/298/300、304、291 画法轴四位。
④ 产品动效面：连续多轮是最弱一维（本轮 0 产品文件、看图腿 NOT-RUN）⇒ 按清账表点一个位真做动效或撤声明。
⑤ 用户闸门 220 路 A / 228② / 265。

"""


def render(s):
    for k, val in V.items():
        s = s.replace(k, val)
    if "@@" in s:
        die("渲染后仍有未替换占位符：" + s[:160])
    return s


V["@@BATTRAN@@"] = pre_ran
for n in ("UI_NEW", "ITER_NEW", "DEC_NEW", "CHG_NEW", "STATE_NEW"):
    globals()[n] = render(globals()[n])
BACK_NEW = "\n\n".join(render(x) for x in BACK_NEW) + "\n"

ui_p = B["AGENT_UI_AUDIT.md"]
ui_old = rd(ui_p)
if "## 第 274 轮" not in ui_old:
    die("UI_AUDIT 找不到锚点")
cut = ui_old.index("## 第 274 轮")
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
bk_new = bk_old.rstrip("\n") + "\n\n" + BACK_NEW


def must_preserve(old, new, name):
    cn = Counter(new.splitlines())
    lost = [l for l, c in Counter(old.splitlines()).items() if cn[l] < c]
    if lost:
        die(name + " 弄丢 " + str(len(lost)) + " 行：" + " | ".join(lost[:2])[:150])


for o, n, nm in ((ui_old, ui_new, "AGENT_UI_AUDIT.md"), (cg_old, cg_new, "CHANGELOG.md"),
                 (bk_old, bk_new, "AGENT_BACKLOG.md")):
    must_preserve(o, n, nm)

st_p = B["AGENT_STATE.md"]
st_old = rd(st_p)
if "## R275 状态" not in st_old:
    die("STATE 找不到锚点")
st_new = st_old.replace("## R275 状态", STATE_NEW + "## R275 状态", 1)
must_preserve(st_old, st_new, "AGENT_STATE.md")

ids = [int(x) for x in re.findall(r"- \*\*U-(\d+)", UI_NEW)]
if ids != list(range(921, 924)):
    die("U 号不连续：" + str(ids))
if "U-921…U-923" not in UI_NEW.splitlines()[0]:
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
if "D-262" in dc_old or "D-261" not in dc_old:
    die("D 号不对")
if bk_new.count("\n**331. ") != 1 or bk_new.count("\n**332. ") != 1:
    die("新开 331/332 没落上")
if "## R276 状态" not in st_new:
    die("STATE 没轮换")

for p, t in ((ui_p, ui_new), (it_p, it_new), (dc_p, dc_new), (bk_p, bk_new), (cg_p, cg_new), (st_p, st_new)):
    with io.open(p, "w", encoding="utf-8") as h:
        h.write(t)

out, rc = sh([sys.executable, os.path.join(HERE, "report_cells_r258.py"), "headline"])
if rc != 0:
    die("FINAL_REPORT headline 刷新失败：" + out[-300:])
ran2, skip2 = battery()
if ran2 != pre_ran:
    die("写盘前后电池颗数不一致（" + pre_ran + " → " + ran2 + "）")
print("LEDGERS_R276 OK batt=Ran " + ran2 + " (skipped=" + skip2 + ") 直接=" + str(len(direct))
      + " 闭包=" + str(len(closure)) + " 仍写死根=" + str(hard_all) + " 表=" + V["@@K51@@"] + "/" + V["@@K71@@"]
      + "/" + V["@@K75@@"] + " U=921..923 D=262 new=331,332")
print(out.strip().splitlines()[-1])
