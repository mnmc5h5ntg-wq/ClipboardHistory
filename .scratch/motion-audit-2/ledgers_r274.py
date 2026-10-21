#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R274 台账生成器（第 273 轮 / Round 271）：读自己那一跑的 CI，把 runner 红的一朵归因并修掉。

数字一律现读：/tmp/r274_log.txt（runner STEP[9] 正文）、/tmp/r274_knife.log（M831 重跑）、
磁盘上的工具源码、脚本电池连跑两遍。缺任何一个就拒绝写盘。
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
LOG = "/tmp/r274_log.txt"
KLOG = "/tmp/r274_knife.log"


def die(m):
    sys.stderr.write("LEDGERS_R274 REFUSED: " + m + "\n")
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


# ---- ① runner 那朵红：必须由它自己打印的正文签，不靠记忆 ----
runner = rd(LOG)
step = sorted({l.split("\t")[1] for l in runner.splitlines() if len(l.split("\t")) >= 3})
if step != ["Release script tests"]:
    die("失败正文的步骤名不是预期的那一颗（要按步骤过滤，别跨步骤 grep）：" + str(step)[:120])
ran = re.search(r"Ran (\d+) tests", runner)
concl = re.search(r"FAILED \(errors=(\d+), skipped=(\d+)\)", runner)
if not ran or not concl:
    die("runner 的结论行读不到：\n" + runner[-200:])
errs = int(concl.group(1))
fnf = re.findall(r"FileNotFoundError: \[Errno 2\] No such file or directory: '([^']+)'", runner)
if not fnf or not all(p.startswith("/Users/wangziyi/Codex_Project0") for p in fnf):
    die("归因没有证人：FileNotFoundError 的样本里混着别的成因 " + str(fnf[:2]))
if errs != len(set(fnf)) and not (errs >= 3):
    die("红掉的格数与读数不自洽：errors=" + str(errs))
machine_paths = sorted({p for p in fnf})[:2]

# ---- ② 修法与门：电池 import 的那批工具现在都不许写死本机根 ----
sys.path.insert(0, os.path.join(ROOT, "scripts", "tests"))
import test_mutate_r271_needle as T  # noqa: E402

tools = T.imported_tool_names()
if len(tools) < 2:
    die("抽不出电池 import 的工具名单（名单为空=红）：" + str(tools))
bad_now = [n for n in tools
           if T.loads_machine_root(rd(os.path.join(HERE, n)))]
if bad_now:
    die("这些工具仍然写死本机根：" + ",".join(bad_now))
hard_all = len([p for p in sorted(os.listdir(HERE)) if p.endswith(".py")
                and re.search(r"^ROOT = ['\"]/Users/", rd(os.path.join(HERE, p)), re.M)])
gate_cells = len([m for m in dir(T.NeedleMirrorTests) if m.startswith("test_")])

# ---- ③ 刀重跑（D-215：改了工具的根必须把站在它上面的刀重跑）----
kn = re.search(r"R271_MUTATE 刀=(\d+) CAUGHT=(\d+) ESCAPED=(\d+) NOT_RUN=(\d+) RESTORE_CLEAN=(\w+)", rd(KLOG))
if not kn or kn.group(2) != kn.group(1) or kn.group(3) != "0" or kn.group(4) != "0" or kn.group(5) != "yes":
    die("M831 重跑不是全 CAUGHT 或还原不干净：" + (kn.group(0) if kn else "无汇总行"))

# ---- ④ 电池连跑两遍，颗数必须相等 ----
def battery():
    b, rc = sh([sys.executable, "-m", "unittest", "discover", "-s", "scripts/tests"])
    m = re.findall(r"^Ran (\d+) tests", b, re.M)
    if not m or not re.search(r"^OK", b, re.M) or rc != 0:
        die("电池不是绿的：\n" + b[-700:])
    sk = re.search(r"skipped=(\d+)", b)
    return m[-1], (sk.group(1) if sk else "0")


pre_ran, pre_skip = battery()
if int(pre_ran) <= int(ran.group(1)):
    die("电池颗数没涨（" + pre_ran + " <= runner 那跑的 " + ran.group(1) + "）⇒ 三格新守卫没落上")

ctxt, _ = sh(["gh", "run", "list", "--limit", "8", "--json", "databaseId,headSha,status,conclusion"])
runs = json.loads(ctxt[ctxt.index("["):])


def pair(sha):
    hits = [r for r in runs if r["headSha"].startswith(sha)]
    if not hits:
        return sha + " → 未取到（293）"
    r = hits[0]
    return sha + " → " + str(r["databaseId"]) + " / " + r["status"] + " / " + (r["conclusion"] or "未读")


ptxt, _ = sh([sys.executable, PRE])
cover = re.search(r"NEEDLE_PRECHECK tables=(\d+) covered=(\d+) arms=(\d+) bad=(\d+)", ptxt)
roster = re.search(r"TABLE_ROSTER registered=(\d+) unregistered_with_arms=(\d+) hidden_arms=(\d+)", ptxt)
if not (cover and roster) or cover.group(4) != "0":
    die("预检读数不全或有坏：\n" + ptxt[-260:])

V = {
    "@@DATE@@": "2026-10-21",
    "@@RUN@@": pair("cc8cb91"), "@@STEP@@": step[0],
    "@@RRAN@@": ran.group(1), "@@ERRS@@": str(errs), "@@RSKIP@@": concl.group(2),
    "@@FNF1@@": machine_paths[0], "@@FNFN@@": str(len(set(fnf))),
    "@@TOOLS@@": "、".join(tools), "@@NTOOLS@@": str(len(tools)),
    "@@HARDALL@@": str(hard_all), "@@CELLS@@": str(gate_cells),
    "@@KNIFE@@": kn.group(1) + "/" + kn.group(2) + " CAUGHT、RESTORE_CLEAN=" + kn.group(5),
    "@@BATT@@": "脚本电池 Ran " + pre_ran + " tests / OK (skipped=" + pre_skip + ")",
    "@@TBL@@": cover.group(1), "@@COV@@": cover.group(2), "@@PARMS@@": cover.group(3),
    "@@GAPT@@": roster.group(2), "@@GAPA@@": roster.group(3),
    "@@CI1@@": pair("6e810e6"), "@@CI2@@": pair("3ec2a97"), "@@CI3@@": pair("ecfc012"),
}

UI_NEW = """## 第 273 轮（R274 / 第 273 轮 / Round 271 · @@DATE@@）：runner 把我自己那一卷脚本电池弄红了 —— 三格 FileNotFoundError 的成因是工具写死了本机仓库根（U-915…U-917 / D-260 · 产品 0 文件）

本轮次对照：与 R273（自评 83，324 结案 + 半套账补齐）相比，本轮做的是 R274 的 ⓪ 本身 —— 读自己那一跑的 CI，并且红的那一朵确实在我名下。

- **U-915：归因先于修法，且只准由 runner 自己打印的正文签** —— @@RUN@@ 已 completed / failure，唯一红掉的步骤是 STEP[9]「@@STEP@@」，结论行现读 `Ran @@RRAN@@ tests / FAILED (errors=@@ERRS@@, skipped=@@RSKIP@@)`。三格错误全部是同一形状：`FileNotFoundError` 指向 `@@FNF1@@` 这类**本机绝对路径**（样本 @@FNFN@@ 条、无一例外）。按 read-own-ci 的规矩我没有只盯自己新加的那一步：STEP[10..14] 全 skipped 是被这一步挡住，不是另一朵红。
- **U-916：病根与修法 —— 被电池 import 的工具必须从 `__file__` 推根，和 R262 修预检同一条路** —— `mutate_r271.py` 的 `ROOT` 写死成 `/Users/wangziyi/Codex_Project0`：本机永远绿，runner 的检出目录不是它 ⇒ 站在它上面的三格守卫一起 error。改成由 `__file__` 推；并且当场问了一句「还有谁这样写」：现读 `.scratch/motion-audit-2/` 里 **@@HARDALL@@** 个脚本仍写死本机根，其中被电池 import 的 @@NTOOLS@@ 个（@@TOOLS@@）现已全部干净。刀 M831 按 D-215 重跑（@@KNIFE@@）⇒ 改根没把刀弄哑。
- **U-917：把这一次修升级成会红的门，而不是「我知道该怎么做」** —— `test_mutate_r271_needle.py` 由 3 格长到 @@CELLS@@ 格：① 行为证人 `mod.ROOT` 必须等于由 `mod.__file__` 推出的那一个，且推出来的根下面真有仓库；② 名单**现读**（扫 `scripts/tests/*.py` 正文里 `'motion-audit-2', 'x.py'` 的 import 形状）抽出的每颗工具都不许写死本机根，**名单为空本身要红**；③ 正负对照 —— 旧的写法（含行尾注释那种）必须被谓词判成红、新写法必须判成绿、只在注释里出现那个路径不算（R76：判"用没用"要剥注释）。

眼睛腿：NOT-RUN —— 本轮 0 产品文件、帧未重捕，看图这一维按实记低分。
读数腿：RUN —— runner STEP[9] 正文（`/tmp/r274_log.txt`，@@ERRS@@ errors、@@FNFN@@ 条同形 FileNotFoundError）、M831 重跑（@@KNIFE@@）、@@BATT@@、预检 tables=@@TBL@@ covered=@@COV@@ arms=@@PARMS@@ bad=0。
产品腿：0 文件（`Sources/` 未动 ⇒ sources 格按规矩不动）。
未做（逐条）：① 其余 @@HARDALL@@ 处写死本机根的脚本没搬（新开 329，逐张搬并每张重跑）；② **312 的具名出口（欠第七轮）**；③ 328、323、322、317、314、315、316；④ 310 的 @@GAPT@@ 张表 / @@GAPA@@ 把刀、309 那 6 张、305、291 三位；⑤ 用户闸门 220 路 A / 228② / 265。

"""

ITER_NEW = """## Round 271 · runner 把我自己那一卷脚本电池弄红：三格 FileNotFoundError 的成因是工具写死本机根（R274 / 第 273 轮）/ D-260 · 产品 0 文件

本轮次对照：与 R273（自评 83）相比，本轮第一次把 R274 的 ⓪ 当成正事做 —— 读自己那一跑，红的在名下，先归因再修。
看图腿：NOT-RUN —— 0 产品文件、帧未重捕。
读数腿：RUN —— runner STEP[9]「Release script tests」结论行 `Ran @@RRAN@@ / FAILED (errors=@@ERRS@@, skipped=@@RSKIP@@)`（正文存在 `/tmp/r274_log.txt`）；FileNotFoundError 样本 @@FNFN@@ 条全部指向本机绝对路径；电池 import 的工具名单现读 @@NTOOLS@@ 颗（@@TOOLS@@）改完全干净；刀 M831 重跑 @@KNIFE@@；@@BATT@@；预检 tables=@@TBL@@ covered=@@COV@@ arms=@@PARMS@@ bad=0。
七维度自评：
| 维度 | 分/满分 |
| 真实视觉审查 | 5/15 |
| 判据有效性 | 14/15 |
| 假绿防御 | 15/15 |
| 产品面推进 | 3/15 |
| 台账一致性 | 14/15 |
| 交付诚实性 | 15/15 |
| 可复核性 | 14/15 |
各维理由：真实视觉审查 5 —— 本轮没有画面可读（0 产品文件、未重捕），不编；判据有效性 14 —— 新增的门能红（旧写法被谓词判红），扣一分是门只覆盖电池 import 的那 @@NTOOLS@@ 颗；假绿防御 15 —— 三件同向：名单为空算红、正负对照各测谓词自己、改根后把刀重跑而不是引用旧读数；产品面推进 3 —— 0 产品文件；台账一致性 14 —— 五本 + STATE + 报告两格，数字全由脚本现读，但本轮未跑四件套里的 Swift 全量与帧基线（只动 python 侧，按 R269 的规矩显式记 NOT-RUN）；交付诚实性 15 —— 公开承认这是我自己上一轮写的守卫在 runner 上红；可复核性 14 —— runner 正文存在 /tmp 并写明路径，重启机器会被清掉 ⇒ 不是永久证人。合计 **80**/105。

"""

DEC_NEW = """**D-260（R274）：任何被脚本电池 import 的工具，仓库根一律由 `__file__` 推；写死本机绝对路径的守卫等于一台机器上的私货。** 理由：`mutate_r271.py` 的 `ROOT = '/Users/wangziyi/Codex_Project0'` 在本机永远绿，而 runner 的检出目录不是它 ⇒ R273 那一跑 STEP[9]「Release script tests」`FAILED (errors=@@ERRS@@)`，红的正是我上一轮为 327 写的三格漂移守卫（@@FNF1@@ 这类 FileNotFoundError）。这与 R262 修预检（同一形状、另一个工具）、R91/R92 修夹具覆盖共享路径同族，但这次多两件事：① **门要现读名单** —— 从 `scripts/tests/*.py` 的正文里抽出被 import 的工具，逐个判它有没有写死根，名单为空本身要红；② **谓词要有牙** —— 正对照喂旧写法（含行尾注释）必须红、负对照喂 `__file__` 推导必须绿、只在注释里出现那个路径不算（R76）。盘上还剩 @@HARDALL@@ 处写死根（多是一轮性的生成器与刀表，不在 CI 里跑）⇒ 新开 329 逐张搬，每张搬完要重跑它自己那张表（D-215）。

"""

CHG_NEW = """### Fixed（R274 / 第 273 轮 / Round 271 · runner 上那一朵在我名下的红）

`.scratch/motion-audit-2/mutate_r271.py` 的仓库根从写死 `/Users/wangziyi/Codex_Project0` 改成由 `__file__` 推 —— 它是被脚本电池 import 的工具，runner 的检出目录不是本机路径 ⇒ R273 的账半那一跑 STEP[9]「Release script tests」`Ran @@RRAN@@ / FAILED (errors=@@ERRS@@, skipped=@@RSKIP@@)`，三格全是我上一轮为 327 写的漂移守卫（FileNotFoundError 样本 @@FNFN@@ 条同形）。同轮把这一次修升成会红的门：`test_mutate_r271_needle.py` 3 格 → @@CELLS@@ 格（`mod.ROOT` 必须等于由 `__file__` 推的那一个；电池 import 的工具名单**现读**、逐个不许写死本机根、**名单为空=红**；正负对照测谓词自己）。刀 M831 重跑 @@KNIFE@@（D-215）；@@BATT@@；预检 tables=@@TBL@@ covered=@@COV@@ arms=@@PARMS@@ bad=0。新开 329：其余 @@HARDALL@@ 处写死本机根的脚本逐张搬。CI：@@CI1@@、@@CI2@@、@@CI3@@ 交接时未读 ⇒ 只登记号不轮询（R140）。产品 0 文件；Swift 全量卷与帧基线本轮未跑 ⇒ NOT-RUN。

"""

BACK_NEW = [
    "**329. 把 `.scratch/motion-audit-2/` 里其余写死本机仓库根的脚本改成由 `__file__` 推（R274 现读：@@HARDALL@@ 处 "
    "`^ROOT = ['/\\\"]Users/` 形状；其中被脚本电池 import 的 @@NTOOLS@@ 颗已在 R274 修好并由门钉住，剩下的是单轮生成器与刀表，"
    "它们今天不在 CI 里跑 ⇒ 本机绿不代表别人能重跑）。每张搬完要重跑它自己那张表并登记读数（D-215），"
    "不许只改不跑；搬完的颗数要现读，别把 @@HARDALL@@ 这个数抄成下一次的起点（R274 新开）**",
]

STATE_NEW = """## R274 状态（第 273 轮 / Round 271 · @@DATE@@）
最后更新：2026-10-21（本地 · R274 / 第 273 轮 / Round 271）：**runner 那一朵红归因到我自己的守卫上：被电池 import 的工具写死本机根 ⇒ 由 `__file__` 推，并把这一次修升成会红的门**（U-915…U-917 · D-260 · 产品 0 文件 · 自评 80/105）

**本轮落地**：`mutate_r271.py` 的 ROOT 由 `__file__` 推；`test_mutate_r271_needle.py` 由 3 格长到 @@CELLS@@ 格（行为证人 + 名单现读 + 正负对照）；刀 M831 重跑 @@KNIFE@@；@@BATT@@；预检 tables=@@TBL@@ covered=@@COV@@ arms=@@PARMS@@ bad=0、310 缺口 @@GAPT@@ 张 / @@GAPA@@ 把。runner 证人正文留在 `/tmp/r274_log.txt`（重启即失，重跑 `gh run view 39579621207 --log-failed` 可再取）。

**下一轮（R275 / 第 274 轮 / Round 272）的 ⓪**：
⓪ 读 CI：@@CI1@@、@@CI2@@、@@CI3@@ 与本轮新跑（只登记号不轮询，R140）。本轮**要验的具体一件**：STEP[9]「Release script tests」在新门上转绿（errors 必须归 0，且 `Ran` 颗数 >= @@BATTNUM@@），而 R273 那两张 recording 帧在 STEP[11] 的相位稳定性仍未读 —— 若报 changed=2 按 D-251 开具名出口，不许改基线迁就。
① **312 的具名出口（欠第七轮）**：按「纸」那一维推，本机 3.000 不许降（D-251）。
② 329（其余 @@HARDALL@@ 处写死根，每张搬完重跑那张表）、328（比摘要的尺统一成一条会红的 + 一把喂错摘要的刀）、323、322、317、314、315、316。
③ 310 的 @@GAPT@@ 张表、309 那 6 张；305、299、301、307、287/284、297/298/300、304、291 三位。
④ 产品动效面连续多轮是最弱一维（本轮看图腿 5/15）：按清账表点一个位真做动效或撤声明。
⑤ 用户闸门 220 路 A / 228② / 265。

"""


def render(s):
    for k, v in V.items():
        s = s.replace(k, v)
    if "@@" in s:
        die("渲染后仍有未替换占位符：" + s[:160])
    return s


V["@@BATTNUM@@"] = pre_ran
for n in ("UI_NEW", "ITER_NEW", "DEC_NEW", "CHG_NEW", "STATE_NEW"):
    globals()[n] = render(globals()[n])
BACK_NEW = "\n\n".join(render(x) for x in BACK_NEW) + "\n"

ui_p = B["AGENT_UI_AUDIT.md"]
ui_old = rd(ui_p)
if "## 第 272 轮" not in ui_old:
    die("UI_AUDIT 找不到锚点")
cut = ui_old.index("## 第 272 轮")
ui_new = ui_old[:cut] + UI_NEW + ui_old[cut:]

it_p = B["AGENT_VISUAL_ITERATION.md"]
it_old = rd(it_p)
it_new = it_old.rstrip("\n") + "\n\n" + ITER_NEW

dc_p = B["AGENT_DECISIONS.md"]
dc_old = rd(dc_p)
dc_new = dc_old.rstrip("\n") + "\n\n" + DEC_NEW

cg_p = B["CHANGELOG.md"]
cg_old = rd(cg_p)
if "## [Unreleased]\n" not in cg_old:
    die("CHANGELOG 找不到 [Unreleased]")
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
if "## R273 状态" not in st_old:
    die("STATE 找不到锚点")
st_new = st_old.replace("## R273 状态", STATE_NEW + "## R273 状态", 1)
must_preserve(st_old, st_new, "AGENT_STATE.md")

ids = [int(x) for x in re.findall(r"- \*\*U-(\d+)", UI_NEW)]
if ids != list(range(915, 918)):
    die("U 号不连续：" + str(ids))
if "U-915…U-917" not in UI_NEW.splitlines()[0]:
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
if "D-260" in dc_old or "D-259" not in dc_old:
    die("D 号不对")
if bk_new.count("\n**329. ") != 1:
    die("新开 329 没落上")
if "## R274 状态" not in st_new:
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
print("LEDGERS_R274 OK batt=Ran " + ran2 + " (skipped=" + skip2 + ") runner_errors=" + str(errs)
      + " fnf=" + V["@@FNFN@@"] + " tools=" + V["@@NTOOLS@@"] + " hardcoded_left=" + V["@@HARDALL@@"]
      + " knife=" + V["@@KNIFE@@"] + " U=915..917 D=260 new=329")
print(out.strip().splitlines()[-1])
