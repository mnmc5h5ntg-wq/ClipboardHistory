#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R262 台账生成器（第 261 轮 / Round 259）：三根腐烂针修完 + 名册的可见面按「抽得出来」算。

数字全部现读：预检三行、三张变异表的汇总行、四把新刀的汇总行、写死颗数尺的 SUMMARY 行、
引号放宽前后的臂号差、CI 的 run↔commit 成对号、电池结论行。任何一格读不到就不写盘。
"""
import ast
import glob
import importlib.util
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
SCAN = os.path.join(ROOT, "scripts", "mutation_verdict_scan.py")
MUT_LOG = "/tmp/r262_mutate.log"
KNIFE_LOG = "/tmp/r262_knives.log"
LIST_JSON = "/tmp/r262_list.json"


def die(msg):
    sys.stderr.write("LEDGERS_R262 REFUSED: " + msg + "\n")
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


# ── 1. 预检三行 ────────────────────────────────────────────────────────
ptxt, prc = sh([sys.executable, PRE])
cover = re.search(r"NEEDLE_PRECHECK tables=(\d+) covered=(\d+) arms=(\d+) bad=(\d+)", ptxt)
total = re.search(r"ARM_TOTAL files=(\d+) arms=(\d+) dupes=(\d+) repeats=(\d+)", ptxt)
bash = re.search(r"BASH_ARMS tables=(\d+) arms=(\d+) kinds=(\S+) bad=(\d+)", ptxt)
if not (cover and total and bash):
    die("预检三行读数缺一行：\n" + ptxt[-500:])
if cover.group(4) != "0" or bash.group(4) != "0":
    die("修完还有腐烂针：python bad=" + cover.group(4) + " / manifest bad=" + bash.group(4))
if total.group(3) != "0" or total.group(4) != "0":
    die("撞号或重号不为 0：" + total.group(0))

# ── 2. 三张重跑表的汇总行 + 四把新刀 ────────────────────────────────────
mlog = rd(MUT_LOG)
klog = rd(KNIFE_LOG)
SUMS = {
    "r229": r"R229_MUTATE 刀=(\d+) CAUGHT=(\d+) ESCAPED=(\d+) NOT_RUN=(\d+)",
    "r217": r"R217_MUTATE 刀=(\d+) CAUGHT=(\d+) ESCAPED=(\d+) NOT_RUN=(\d+)",
    "r97": r"MUTATE_TABLE n=(\d+) caught=(\d+) intended_escaped=(\d+) mismatch=(\d+) not_run=(\d+)",
    "r262": r"R262_MUTATE 刀=(\d+) CAUGHT=(\d+) ESCAPED=(\d+) NOT_RUN=(\d+)",
}
S = {}
for key, pat in SUMS.items():
    m = re.search(pat, mlog if key != "r262" else klog)
    if not m:
        die(key + " 那张表的汇总行读不到 ⇒ 不许把它的结论写进账")
    g = m.groups()
    if key == "r97":
        n, caught, esc, mismatch, not_run = g
        esc = str(int(esc) + int(mismatch))
    else:
        n, caught, esc, not_run = g
    if (int(esc) or int(not_run) or int(caught) != int(n)):
        die(key + " 不是全 CAUGHT（刀=" + n + " CAUGHT=" + caught + " ESCAPED=" + esc + " NOT_RUN=" + not_run + "）")
    S[key] = (n, caught)

# ── 3. 写死颗数尺的现读 + 引号放宽前后的臂号差 ─────────────────────────
stxt, src_ = sh([sys.executable, SCAN])
if src_ != 0:
    die("写死颗数尺跑不通 exit=" + str(src_))
sm = re.search(r"MUT_VERDICT_SUMMARY tables=(\d+) offenders=(\d+) named=(\S+) parse_bad=(\d+)", stxt)
if not sm:
    die("写死颗数尺没有 SUMMARY 行")
if sm.group(4) != "0":
    die("有表解析失败：" + sm.group(0))
spec = importlib.util.spec_from_file_location("verdict_scan", SCAN)
ruler = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ruler)
OLD_ARM = re.compile(r'^\s*\("(M\d{3}[a-z]?)"\s*,')
ptxt_src = rd(PRE)
new_rx = re.search(r'ARM_LINE = re\.compile\(r\'(.*?)\'\)', ptxt_src)
if not new_rx:
    die("读不到预检现在的 ARM_LINE 写法 ⇒ 臂号差没法算")
NEW_ARM = re.compile(new_rx.group(1))


def count_with(rx, path):
    out = []
    for line in rd(path).splitlines():
        if "append" in line or "in only" in line:
            continue
        m = rx.match(line)
        if m:
            out.append(m.group(2) if m.re.groups >= 2 else m.group(1))
    return out


hidden_files = 0
hidden_arms = 0
for path in sorted(glob.glob(os.path.join(HERE, "mutate_r*.py"))):
    a = count_with(OLD_ARM, path)
    b = count_with(NEW_ARM, path)
    if len(b) > len(a):
        hidden_files += 1
        hidden_arms += len(b) - len(a)
if hidden_arms <= 0:
    die("引号放宽没有多抽出任何臂 ⇒ 这条结论（123 把刀此前隐形）没被现读支持")

# 被电池 import 的 .scratch 工具里不许有写死的家目录（R262 runner 那一朵红的修法）
for tool in (PRE, os.path.join(HERE, "curve_from_ledger.py"), os.path.join(HERE, "make_surface_ledger.py"), SCAN):
    bad = [s for s in ruler.string_constants(ast.parse(rd(tool))) if "/Users/" in s]
    if bad:
        die(os.path.basename(tool) + " 里还有写死的家目录：" + bad[0][:60])

# ── 4. CI 成对号 ───────────────────────────────────────────────────────
runs = json.loads(rd(LIST_JSON))


def pair(sha):
    hits = [r for r in runs if r["headSha"].startswith(sha)]
    if not hits:
        return sha + " → 未取到（同一次 push 只给 head 那笔建跑，293）"
    r = hits[0]
    return sha + " → " + str(r["databaseId"]) + " / " + r["status"] + " / " + (r["conclusion"] or "未读")


# R261 那句「真账是另外 N 根」要从它自己写下的那行里读，不许我手抄（本轮正是去更正这个数）
m261 = re.search(r"追记（R261）：286 第一次有具体名单 —— 预检现读 (\d+) 根针腐烂", rd(BACK))
if not m261:
    die("读不到 R261 写在 286 之下的那个根数 ⇒ 本轮的更正没有对照物")
rot261 = m261.group(1)
REPAIRED = ["M541", "M750", "M768"]
RETRACTED = ["M684", "M686"]
if int(rot261) != len(REPAIRED) + len(RETRACTED):
    die("更正对不上账：R261 说 " + rot261 + " 根，而本轮 修掉 " + str(len(REPAIRED))
        + " 根 + 撤回 " + str(len(RETRACTED)) + " 根")

# ── 5. 电池（必须在别的账写完之后、commit 之前跑；这里先跑一次拿数，写盘后再跑一次当闸门）──
def battery():
    btxt, brc = sh([sys.executable, "-m", "unittest", "discover", "-s", "scripts/tests"])
    m = re.findall(r"^Ran (\d+) tests", btxt, re.M)
    if not m:
        die("电池结论行读不到：\n" + btxt[-400:])
    if not re.search(r"^OK", btxt, re.M):
        die("电池不是 OK：\n" + btxt[-900:])
    if brc != 0:
        die("电池 exit=" + str(brc))
    skip = re.search(r"skipped=(\d+)", btxt)
    return m[-1], (skip.group(1) if skip else "0")


pre_ran, pre_skip = battery()

with io.open(os.path.join(ROOT, "docs", "frame_baseline.json"), encoding="utf-8") as handle:
    base = json.load(handle)
frames = len(base.get("frames", {}))
if frames < 100:
    die("工作基线只读到 " + str(frames) + " 张帧 ⇒ 帧数不是按目录数出来的，先确认没被清空")

V = {
    "@@DATE@@": "2026-10-21",
    "@@FRAMES@@": str(frames),
    "@@ROT261@@": rot261,
    "@@TABLES@@": bash.group(1),
    "@@BARMS@@": bash.group(2),
    "@@FILES@@": total.group(1),
    "@@ARMS@@": total.group(2),
    "@@ARMS_OLD@@": str(int(total.group(2)) - hidden_arms),
    "@@HIDF@@": str(hidden_files),
    "@@HIDA@@": str(hidden_arms),
    "@@PT@@": cover.group(1),
    "@@PC@@": cover.group(2),
    "@@PA@@": cover.group(3),
    "@@SCAN_T@@": sm.group(1),
    "@@SCAN_O@@": sm.group(2),
    "@@SCAN_N@@": sm.group(3).replace(",", "、"),
    "@@229@@": S["r229"][1] + "/" + S["r229"][0],
    "@@217@@": S["r217"][1] + "/" + S["r217"][0],
    "@@97@@": S["r97"][1] + "/" + S["r97"][0],
    "@@262@@": S["r262"][1] + "/" + S["r262"][0],
    "@@CI9@@": pair("2068301"),
    "@@CI11@@": pair("1bccf7f"),
    "@@CI12@@": pair("6bf6f3e"),
}

UI_NEW = """## 第 261 轮（R262 / 第 261 轮 / Round 259 · @@DATE@@）：三根腐烂针修完并重跑，名册的可见面改成按「抽得出来」算 —— 顺带撤回上一轮的两次假指控（U-858…U-864 / D-248 · 286 结案 · 产品 0 文件）

本轮次对照：与 R261（把 bash 刀接进名册、交出「@@ROT261@@ 根针腐烂」的名单，自评 79）相比，本轮做三件事：① 把名单里**真的**死了的三根针重钉并把那三张表重跑；② 撤回上一轮名单里的两次假指控；③ 把「什么算登记过」从"文件存在"改成"抽得出来"，于是又现读出一批此前对查重完全隐形的刀（@@HIDA@@ 把 / @@HIDF@@ 张表）。产品 0 文件。

- **U-858：286 结案 —— 三根腐烂针重钉 + 三张表重跑，读数是真的** —— M541（`mutate_r97_card.py`，cardFill 地板 20→0）、M750（`mutate_r217.py`，尺的第一个子句恒假）、M768（`mutate_r229.py`，亮档 hover 那一抬搬进 `HoverInk.opacity` 之后旧锚点命中 0）。重跑现读：r229 @@229@@ CAUGHT、r217 @@217@@ CAUGHT、r97 @@97@@ CAUGHT，全部 RESTORE_CLEAN；预检从 bad=3 变 **bad=0**（`NEEDLE_PRECHECK tables=@@PT@@ covered=@@PC@@ arms=@@PA@@ bad=0`）。D-215 那条规矩（改源码那一轮就把打它的表改到还能跑）这次是**迟到两轮**补上的。
- **U-859：公开更正 —— 上一轮那句「真账是另外 5 根」里有两根是假的** —— M684/M686 不是腐烂，是尺的假指控：`arm_sites` 不认识 R169 那种五字段臂 `(编号, 文件, needle, 变异文, 期望)`，把 needle 当成"文件"、再退回模块默认的 HARNESS 去数 ⇒ 数到 0。修掉形状识别之后 bad 从 5 降到 3，那两根一起消失。**286 的原文（R245 写的）里也点了这两根**，所以这笔假账挂了七轮没被复查。真腐烂只有三根，本轮全修。
- **U-860：`'Executed 4 tests' in text` 这种写法会把"真红了"读成"根本没跑"** —— `mutate_r229.py` 的"跑起来了没"判据写死了上一轮量到的颗数，而那一卷在 R260 从 4 条长到 6 条。改成按结论行的**形状**认（`Executed (\\d+) tests?, with (\\d+) failures?`，取末一条不是首条），并且把 D-243 那一侧一起钉住：**没有结论行一律 NOT_RUN，编译红不许算 CAUGHT**。
- **U-861：新尺 `scripts/mutation_verdict_scan.py` —— 数一数还有几张表把颗数写死** —— 现读 @@SCAN_T@@ 张表里 **@@SCAN_O@@ 张**仍写死：@@SCAN_N@@。只测不判（退出码恒 0），"不许再加新的"由名册那格负责。判据卷 `scripts/tests/test_mutation_verdict_scan.py` 11 格：写死的必须被点名（正对照）、按形状判的不许误伤（负对照）、`Executed 0` 是状态不是读数、**注释与 docstring 里引用这句话不算命中**（只用 `ast` 的字符串常量 ⇒ 本文件上面那句 `'Executed 4 tests' in text` 不会喂饱它）、解析失败要报"没量到"而不是"干净"、目录不存在必须响。
- **U-862：四把 python 刀 M819…M822 全 CAUGHT** —— 对象是尺自己（`scripts/mutation_verdict_scan.py`），走 python 通道、不碰产品 ⇒ 不必重捕帧。四把各砍一颗牙：docstring 不跳过 / 取消 `Executed 0` 豁免 / 匹配串换成永远匹配不上 / 目录不存在却 exit 0。现读 @@262@@ CAUGHT、RESTORE_CLEAN=yes。
- **U-863：名册的可见面按「抽得出来」算 —— 又现读一批隐形刀** —— `ARM_LINE` 旧版只认 `("M6NN",` 双引号形状，而 @@HIDF@@ 张表用 `('M6NN', …` 写 ARMS ⇒ **@@HIDA@@ 把刀对跨表查重完全隐形**（与 306 结掉的那半个洞同源，这次坏在引号上）。放宽成两种引号都认（反向引用锁"两边同种"）后 `ARM_TOTAL arms=@@ARMS_OLD@@ → @@ARMS@@`，dupes 仍 0、repeats 仍 0。这一条与 U-859 是同一颗道理：**登记过 ≠ 抽得出来；抽不出来就等于没登记**。
- **U-864：CI 三笔交账 + 眼睛腿本轮真跑** —— @@CI9@@（STEP[9] 电池红在 `test_the_sources_cell_agrees_with_git`，`Ran 470 / failures=1`，与本机同一朵、同一因，@@CI11@@ 已修并被 runner 验收）；@@CI12@@ —— 这一朵是**新的**：runner 上 `check_manifests` 报 `FileNotFoundError: /Users/wangziyi/.../arms_r245/M802.old`，因为预检把仓库根**写死**成我本机的路径。本轮改成由 `__file__` 推，并加一格守卫（扫 `ast` 字符串常量，四支被电池 import 的工具里不许出现写死的家目录，配人造正对照）。眼睛腿 RUN：看了亮档 `row-favorite` 的 hover 与 press 两张（R259 建夹具以来第一次用眼睛看按下档）—— 两张**肉眼分不出**，差别押在图标缩放而不是那一层墨上；范围只这两张，不外推到段按钮与 modechip。这条读数是 305「相邻台阶要不要 1.20」的一格证人，不是结论。

读数腿：RUN（预检三行 + 四张表汇总行 + 尺的 SUMMARY 行 + 臂号差 + 电池一行）。
变异腿：RUN（@@229@@ / @@217@@ / @@97@@ / @@262@@ 四张表全 CAUGHT）。
眼睛腿：RUN（两张，见 U-864；结论范围收窄到那两张）。
产品腿：0 文件 —— 本轮没有画面会变；工作基线现读 @@FRAMES@@ 张（R260 那一笔同一套），本轮**未重捕**（0 产品改动 ⇒ CHANGED 无定义，不写"没变"当证人）。
未做（逐条）：① 305 的地板（本轮那两张只是又添一格"肉眼分不出"）；② 309 那 @@SCAN_O@@ 张写死颗数的表要一张张迁并各自重跑；③ 310 的 TABLES 手写名册（@@PT@@ 登记 vs @@SCAN_T@@ 存在）；④ 299 的执行器半；⑤ 301 + 307；⑥ 291 那四位；⑦ 287/284、297/298/300、304；⑧ 用户闸门 220 路 A / 228② / 265。

"""

ITER_NEW = """## Round 259 · 三根腐烂针修完、撤回上一轮两根假指控，名册改成按「抽得出来」算（R262 / 第 261 轮）/ D-248 · 286 结案 · 产品 0 文件

本轮次对照：与 R261（自评 79，把 bash 刀接进名册并交出腐烂针名单）相比，本轮把那份名单**核对了一遍**：三根真的死了（已重钉、三张表重跑全 CAUGHT、bad=0），两根是尺的假指控（`arm_sites` 不认识五字段臂形状，把 needle 当文件去数）；再把"登记"的定义从"文件存在"改成"抽得出来"，于是又现读 @@HIDA@@ 把此前对查重隐形的刀（@@HIDF@@ 张表用单引号写 ARMS）。产品 0 文件。
看图腿：RUN —— 亮档 `row-favorite` 的 hover 与 press 两张，肉眼分不出，差别在缩放不在墨（范围只这两张）。
读数腿：RUN —— 预检 `NEEDLE_PRECHECK tables=@@PT@@ covered=@@PC@@ arms=@@PA@@ bad=0`、`ARM_TOTAL arms=@@ARMS@@ dupes=0`、四张表 @@229@@/@@217@@/@@97@@/@@262@@ 全 CAUGHT、写死颗数尺 @@SCAN_T@@ 张表点名 @@SCAN_O@@ 张、@@BATT@@。
七维度自评：
| 维度 | 分/满分 |
| 真实视觉审查 | 8/15 |
| 判据有效性 | 14/15 |
| 假绿防御 | 15/15 |
| 产品面推进 | 3/15 |
| 台账一致性 | 14/15 |
| 交付诚实性 | 15/15 |
| 可复核性 | 14/15 |
各维理由：真实视觉审查 8 —— 第一次用眼睛看了按下档那两张（R259 建夹具以来头一次），并且老实说"分不出"，但本轮没有新画面可看，所以不给高分；判据有效性 14 —— 三根死针重钉且**重跑了那三张表**（不是只改锚点），另加一把新尺带 11 格；假绿防御 15 —— 拦下三种"看着像登记过"：单引号写法对查重隐形（@@HIDA@@ 把）、写死颗数把真红读成 NOT_RUN、以及上一轮那两次假指控本身（撤回并记账）；产品面推进 3 —— 0 产品文件，连续第二轮，是有意还债；台账一致性 14 —— 五本 + STATE + FINAL_REPORT 两格由脚本派生，286 结案、公开更正写在 286 自己那条之下；交付诚实性 15 —— 撤回了上一轮写进账的假话，并写明它挂了七轮；可复核性 14 —— 预检/尺/四把刀全部一条命令可重跑，正负对照成对。合计 **83**/105。

"""

DEC_NEW = """**D-248（R262）：名册的可见面按「抽得出来」算，不按「存在」算 —— 抽不出的写法等于没登记，而且会造出假指控。** 理由：R262 一次撞上两回同一颗错。① `arm_ids` 的正则只认 `("M6NN",` 双引号形状 ⇒ @@HIDF@@ 张用 `('M6NN', …` 写 ARMS 的表、共 @@HIDA@@ 把刀，对跨表查重完全隐形（放宽后 `ARM_TOTAL arms=@@ARMS_OLD@@ → @@ARMS@@`，dupes 仍 0）。② `arm_sites` 不认识 R169 的五字段臂形状 ⇒ 把 needle 当文件、退回默认路径去数，数到 0，于是上一轮把两把好刀报成"腐烂"，那两句假话还写进了 286 的正文（R245 起挂了七轮）。两次都不是"账错了"，是**尺的覆盖面被书写风格决定**。与 D-247（预检要与被它预检的尺共用同一个估计量）、R68（证人与判据同一颗尺）同族；这条是它的加强版：登记面要由"抽出来的数"签，不许由"我以为通配到了"签。配套三件：新尺 `scripts/mutation_verdict_scan.py`（只测不判）+ 名册那格把地板从猜的 400 改成量出来的 600（现读 @@ARMS@@）+ 四把刀 M819…M822 各砍一颗牙。

"""

NOTE_286 = ("  追记（R262）：**结案**。三根真腐烂针重钉 + 三张表重跑：M541（r97_card，@@97@@ CAUGHT）、"
            "M750（r217，@@217@@ CAUGHT）、M768（r229，@@229@@ CAUGHT），全部 RESTORE_CLEAN；"
            "预检现读 `NEEDLE_PRECHECK tables=@@PT@@ covered=@@PC@@ arms=@@PA@@ bad=0`。\n"
            "  追记（R262）：**公开更正上一轮那句「真账是另外 5 根」** —— 其中 M684/M686 是尺的假指控："
            "`arm_sites` 不认识 R169 那种五字段臂 `(编号, 文件, needle, 变异文, 期望)`，把 needle 当成文件、"
            "再退回模块默认的 HARNESS 去数 ⇒ 数到 0。修掉形状识别后 bad 由 5 降到 3，这两根一起消失；"
            "它们在本条 R245 的原文里也被点过一次，所以这笔假账挂了七轮。真腐烂只有三根，本轮全修（D-248）。\n")

NOTE_305 = ("  追记（R262）：眼睛腿添一格证人 —— 亮档 `row-favorite` 的 hover 与 press 两张（R259 建按下夹具以来第一次用眼睛看）"
            "**肉眼分不出**，能看出来的差别是图标缩放而不是那一层墨。范围只这两张，不外推。\n")

BACK_NEW = [
    "**309. 写死颗数的变异表一张张迁到形状判据（R262 现读 @@SCAN_O@@ 张：@@SCAN_N@@）：每迁一张要**重跑那张表**并登记新的 CAUGHT，"
    "不许只改代码不重跑（D-215）；迁完把 `scripts/tests/test_mutation_verdict_scan.py` 的 ROSTER 删一行，"
    "名册双向相等那格会当场要求它（R262 新开）**",
    "**310. 预检的 `TABLES` 是手写名册（R262 现读：登记 @@PT@@ 张、静态抽得出 needle 的 @@PC@@ 张，而 `.scratch/motion-audit-2/` 下"
    "有 @@SCAN_T@@ 张 `mutate_*.py`）⇒ 新写的表忘了登记就**静默不覆盖**，与 285/306 同一族。处置二选一："
    "按 glob 全量抽并把抽不出 needle 的逐张点名，或加一条会红的守卫要求「未登记表 = 有名有姓的白名单」（R262 新开）**",
    "**311. `.scratch/motion-audit-2/` 里其余变异表仍写死 `ROOT = '/Users/wangziyi/...'`：本轮只把**被电池 import 的"
    "四支**钉进守卫（预检 + 曲线 + 表面账 + 新尺），其余由我手工跑、不进 CI，所以今天不会咬人 ——"
    "但这是范围收窄不是修完。要接进 CI 的那一支（`round_verify.sh` 那条链）之前，先把这条扫遍 `.scratch`（R262 新开）**",
]

CHG_NEW = """### Changed（R262 / 第 261 轮 / Round 259 · 三根腐烂针修完，名册改成按「抽得出来」算）

三根真腐烂针重钉并把那三张表重跑：M541（@@97@@ CAUGHT）、M750（@@217@@ CAUGHT）、M768（@@229@@ CAUGHT），RESTORE_CLEAN；预检 `NEEDLE_PRECHECK tables=@@PT@@ covered=@@PC@@ arms=@@PA@@ bad=0` ⇒ **286 结案**。
撤回上一轮的两次假指控：M684/M686 不是腐烂，是 `arm_sites` 不认识五字段臂形状（把 needle 当文件去数）⇒ 假账挂在 286 正文里七轮，本轮公开更正。
`mutate_r229.py` 的"跑起来了没"从写死 `'Executed 4 tests'` 改成按结论行形状认，并钉住 D-243 那一侧：没有结论行一律 NOT_RUN，编译红不算 CAUGHT。
新尺 `scripts/mutation_verdict_scan.py`（只测不判）+ 判据卷 11 格（正/负对照、`Executed 0` 是状态、注释与 docstring 不喂守卫、解析失败要响、缺目录必须红）+ 四把 python 刀 M819…M822（@@262@@ CAUGHT）。
`ARM_LINE` 放宽到两种引号 ⇒ 现读 @@HIDA@@ 把刀 / @@HIDF@@ 张表此前对跨表查重隐形；`ARM_TOTAL arms=@@ARMS_OLD@@ → @@ARMS@@`、dupes=0；名册那格地板由猜的 400 改成量出来的 600。
runner 那一朵新红（@@CI12@@ / STEP[9]）成因是预检把仓库根写死成我本机的路径 ⇒ 改成由 `__file__` 推，并加一格守卫（四支被电池 import 的工具里不许出现写死的家目录，配人造正对照）。
眼睛腿 RUN：亮档 `row-favorite` 的 hover 与 press 两张肉眼分不出（差别押在缩放不在墨），范围只这两张。产品 0 文件、帧未重捕。@@BATT@@。新开 309/310/311。

"""

STATE_NEW = """## R262 状态（第 261 轮 / Round 259 · @@DATE@@）
最后更新：2026-10-21（本地 · R262 / 第 261 轮 / Round 259）：**三根腐烂针修完并重跑，名册改成按「抽得出来」算，撤回上一轮两次假指控**（U-858…U-864 · D-248 · 286 结案 · 产品 0 文件 · 自评 83/105）

**本轮落地**：M541/M750/M768 重钉 + 三张表重跑全 CAUGHT、预检 bad=0；M684/M686 公开撤回（`arm_sites` 少认一种臂形状）；`mutate_r229.py` 的颗数写死换成形状判据；新尺 `scripts/mutation_verdict_scan.py` + 11 格 + 四把刀 M819…M822；`ARM_LINE` 放宽 ⇒ @@HIDA@@ 把此前隐形的刀进查重（@@ARMS_OLD@@ → @@ARMS@@）；预检仓库根由 `__file__` 推（runner 那朵 FileNotFoundError 的修法）+ 一格绝对路径守卫；@@BATT@@。

**下一轮（R263 / 第 262 轮 / Round 260）的 ⓪**：
⓪ 读 CI：@@CI12@@ 已读（那朵 runner 红本轮修）；本笔 push 后再取新跑 —— 要验的是**放宽引号 + 根路径改派生之后 runner 上 `test_the_repo_manifests…` 与 `test_the_tools_derive…` 两格是否绿**，以及 `RUNG_STEP`/`PRESS_LADDER` 有没有新读数。取不到就写「未取到 + 成因」（293）。
① 309：那 @@SCAN_O@@ 张写死颗数的表一张张迁并各自重跑（迁完删名册一行）。
② 310：`TABLES` 手写名册（@@PT@@ 登记 vs @@SCAN_T@@ 存在）⇒ 未登记表静默不覆盖。
③ 305 的地板（本轮那两张"肉眼分不出"是新证人）；299 的执行器半；301 + 307；311。
④ 291 那四位；287/284；297/298/300、304；用户闸门 220 路 A / 228② / 265。

"""


def render(s):
    for key, val in V.items():
        s = s.replace(key, val)
    if "@@" in s:
        die("渲染后仍有未替换占位符：" + s[:160])
    return s


V["@@BATT@@"] = "脚本电池 Ran " + pre_ran + " tests / OK (skipped=" + pre_skip + ")"

rendered = {}
for name in ("UI_NEW", "ITER_NEW", "CHG_NEW", "STATE_NEW", "NOTE_286", "NOTE_305"):
    rendered[name] = render(globals()[name])
rendered["BACK_NEW"] = "\n\n".join(render(x) for x in BACK_NEW) + "\n"
rendered["DEC_NEW"] = render(DEC_NEW)
UI_NEW = rendered["UI_NEW"]
ITER_NEW = rendered["ITER_NEW"]
DEC_NEW = rendered["DEC_NEW"]
CHG_NEW = rendered["CHG_NEW"]
STATE_NEW = rendered["STATE_NEW"]
NOTE_286 = rendered["NOTE_286"]
NOTE_305 = rendered["NOTE_305"]
BACK_NEW = rendered["BACK_NEW"]

ui_old = rd(UI)
ANCHOR = "## 第 260 轮"
if ANCHOR not in ui_old:
    die("UI_AUDIT 找不到锚点 " + ANCHOR)
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


def append_after(lines, num, payload):
    idx = [n for n, line in enumerate(lines) if re.match(r"^(?:\*\*)" + num + r"\. ", line)]
    if len(idx) != 1:
        die("BACKLOG " + num + " 锚点命中 " + str(len(idx)) + " 次")
    k = idx[0] + 1
    while k < len(lines) and lines[k].strip():
        k += 1
    return lines[:k] + payload.splitlines(True) + lines[k:]


lines = append_after(blines, "286", NOTE_286)
lines = append_after(lines, "305", NOTE_305)
back_new = "".join(lines).rstrip("\n") + "\n\n" + BACK_NEW


def must_preserve(old, new, name):
    co, cn = Counter(old.splitlines()), Counter(new.splitlines())
    lost = [l for l, c in co.items() if cn[l] < c]
    if lost:
        die(name + " 弄丢 " + str(len(lost)) + " 行：" + " | ".join(lost[:2])[:150])


must_preserve(ui_old, ui_new, "AGENT_UI_AUDIT.md")
must_preserve(chg_old, chg_new, "CHANGELOG.md")
must_preserve(back_old, back_new, "AGENT_BACKLOG.md")

ids = [int(x) for x in re.findall(r"- \*\*U-(\d+)", UI_NEW)]
if ids != list(range(858, 865)):
    die("本轮 U 号不连续：" + str(ids))
if "U-858…U-864" not in UI_NEW.splitlines()[0]:
    die("节标题 U 区间与定义不符")
if not iter_new.startswith(iter_old.rstrip("\n")):
    die("AGENT_VISUAL_ITERATION.md 不是纯追加")
if not dec_new.startswith(dec_old.rstrip("\n")):
    die("AGENT_DECISIONS.md 不是纯追加")
if iter_new.count("| 真实视觉审查 |") != iter_old.count("| 真实视觉审查 |") + 1:
    die("七维表多写或少写")
rows = [l for l in ITER_NEW.splitlines() if l.startswith("| ") and "维度" not in l and "分/满分" not in l]
if len(rows) != 7:
    die("七维表形状不对：" + str(len(rows)))
# 合计不许手抄：从表里那七行解析出分数相加，与正文那句「合计 **N**/105」对账
scores = [int(m.group(1)) for m in (re.search(r"\| (\d+)/15 \|", l) for l in rows)]
if any(s is None for s in scores) or len(scores) != 7:
    die("七维表里有行不是 `N/15` 的形状：" + str(rows))
total_score = sum(scores)
m_tot = re.search(r"合计 \*\*(\d+)\*\*/105", ITER_NEW)
if not m_tot:
    die("七维自评的合计行读不到")
if int(m_tot.group(1)) != total_score:
    die("合计手抄错了：表里相加=" + str(total_score) + " 正文写" + m_tot.group(1))
if "D-248" in dec_old:
    die("D-248 已存在")
if "D-247" not in dec_old:
    die("D 号跳号：上一笔 D-247 不在账上")
for num in ("309", "310", "311"):
    if re.search(r"^\*\*" + num + r"\. ", back_new, re.M) is None:
        die("新开 " + num + " 没落上")
    if back_new.count("\n**" + num + ". ") != 1:
        die(num + " 出现不止一次")
if back_new.count("追记（R262）") != 3:
    die("286/305 的追记没写够三条：" + str(back_new.count("追记（R262）")))
if "结案" not in back_new.split("**286. ")[1].split("**287.")[0]:
    die("286 那条之下读不到「结案」")

st_old = rd(STATE)
ST_MARK = "## R261 状态"
if ST_MARK not in st_old:
    die("STATE 找不到锚点")
state_new = st_old.replace(ST_MARK, STATE_NEW + ST_MARK, 1)
must_preserve(st_old, state_new, "AGENT_STATE.md")
if "## R262 状态" not in state_new:
    die("STATE 没轮换")

for path, text in ((UI, ui_new), (ITER, iter_new), (DEC, dec_new), (BACK, back_new), (CHG, chg_new), (STATE, state_new)):
    with io.open(path, "w", encoding="utf-8") as handle:
        handle.write(text)

out, rc = sh([sys.executable, os.path.join(HERE, "report_cells_r258.py"), "headline"])
if rc != 0:
    die("FINAL_REPORT 两格刷新失败：" + out[-300:])

ran2, skip2 = battery()
if ran2 != pre_ran:
    die("台账写盘前后电池颗数不一致（" + pre_ran + " → " + ran2 + "）⇒ 这一笔弄坏了什么，先查再提交")

print("LEDGERS_R262 OK batt=Ran " + ran2 + " (skipped=" + skip2 + ") arms=" + V["@@ARMS@@"]
      + " hidden=" + V["@@HIDA@@"] + "/" + V["@@HIDF@@"] + " offenders=" + V["@@SCAN_O@@"]
      + " U=858..864 D=248")
print(out.strip().splitlines()[-1])
