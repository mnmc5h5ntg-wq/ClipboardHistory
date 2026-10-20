#!/usr/bin/env python3
# R261 台账生成器（第 260 轮 / Round 258）：五把重捕型刀进名册。数字全部现读。
import json
import os
import re
import subprocess
import sys
from collections import Counter

ROOT = "/Users/wangziyi/Codex_Project0"
BATT = "/tmp/r261_batt2.log"
LIST_JSON = "/tmp/r261_list2.json"
PRE = os.path.join(ROOT, ".scratch", "motion-audit-2", "mutate_needle_precheck.py")

UI = os.path.join(ROOT, "AGENT_UI_AUDIT.md")
ITER = os.path.join(ROOT, "AGENT_VISUAL_ITERATION.md")
DEC = os.path.join(ROOT, "AGENT_DECISIONS.md")
BACK = os.path.join(ROOT, "AGENT_BACKLOG.md")
CHG = os.path.join(ROOT, "CHANGELOG.md")
STATE = os.path.join(ROOT, "AGENT_STATE.md")


def die(m):
    sys.stderr.write("LEDGERS_R261 REFUSED: " + m + "\n")
    raise SystemExit(2)


def rd(p):
    with open(p, encoding="utf-8", errors="replace") as f:
        return f.read()


batt = rd(BATT)
ran = None
m = re.findall(r"^Ran (\d+) tests", batt, re.M)
if not m:
    die("电池结论行读不到")
ran = m[-1]
if not re.search(r"^OK", batt, re.M):
    die("电池不是 OK，不落结案账")

env = dict(os.environ)
env["PYTHONUTF8"] = "1"
pre = subprocess.run([sys.executable, PRE], capture_output=True, text=True, cwd=ROOT, env=env)
ptxt = (pre.stdout or "") + (pre.stderr or "")
bash = re.search(r"BASH_ARMS tables=(\d+) arms=(\d+) kinds=(\S+) bad=(\d+)", ptxt)
total = re.search(r"ARM_TOTAL files=(\d+) arms=(\d+) dupes=(\d+) repeats=(\d+)", ptxt)
cover = re.search(r"NEEDLE_PRECHECK tables=(\d+) covered=(\d+) arms=(\d+) bad=(\d+)", ptxt)
if not (bash and total and cover):
    die("预检三行读数缺一行：\n" + ptxt[-400:])
if bash.group(4) != "0":
    die("manifest 锚点有坏：" + bash.group(4))
if total.group(3) != "0":
    die("跨表撞号不为 0（这正是 306 要拦的事）：" + total.group(3))
rot = re.findall(r"^(\S+)\s+((?:M\d{3}[a-z]? 命中=\d+；?)+)", ptxt, re.M)
rot_named = "; ".join(t + " " + s for t, s in rot if "命中=0" in s or "命中=[2-9]" in s or any(
    x in s for x in re.findall(r"M\d{3}[a-z]? 命中=(?:0|[2-9])", s)))
rot_list = re.findall(r"(M\d{3}[a-z]?) 命中=(\d+)", ptxt)
rot_txt = "、".join(n + "（命中 " + h + "）" for n, h in rot_list) or "无"
if int(cover.group(4)) != len(rot_list):
    die("腐烂针数与摘要 bad=%s 不符（现读 %d）" % (cover.group(4), len(rot_list)))

runs = json.loads(rd(LIST_JSON)) if os.path.exists(LIST_JSON) else []


def pair(sha):
    hits = [r for r in runs if r["headSha"].startswith(sha)]
    if not hits:
        return sha + " → 未取到（同一次 push 只给 head 那笔建跑，293）"
    r = hits[0]
    return sha + " → " + str(r["databaseId"]) + " / " + r["status"] + " / " + (r["conclusion"] or "未读")


V = {
    "@@DATE@@": "2026-10-21",
    "@@BATT@@": "Ran " + ran + " tests / OK",
    "@@TABLES@@": bash.group(1),
    "@@ARMS@@": bash.group(2),
    "@@KINDS@@": bash.group(3),
    "@@TOTALARMS@@": total.group(2),
    "@@FILES@@": total.group(1),
    "@@COVER@@": cover.group(2) + "/" + cover.group(1),
    "@@ROT@@": rot_txt,
    "@@ROTN@@": cover.group(4),
    "@@CI@@": "；".join([pair("1bccf7f"), pair("2068301")]),
}

UI_NEW = """## 第 260 轮（R261 / 第 260 轮 / Round 258 · @@DATE@@）：五把重捕型刀进名册 —— 顺带被自己的新尺骗了一次（U-853…U-857 / D-247 · 306 结案、286 现读名单 · 产品 0 文件）

本轮次对照：与 R260（量出并修掉第二个真产品缺陷，自评 94）相比，本轮 0 产品文件，还的是 R258/R260 连续两轮写在账里的那句"这刀名册看不见"。它还完就交出一份新的坏消息：python 表里有 @@ROTN@@ 根针已经腐烂（286 的现读名单）。

- **U-853：`arms_r*/manifest.tsv` 现在是查重器的一等公民** —— `cross_table_ids` 旧版只扫 `mutate_r*.py` 的 `ARMS` 形状，而重捕型刀住在 bash 里 ⇒ 现读 **@@TABLES@@ 张 manifest、@@ARMS@@ 把刀**（M802…M818，kind=@@KINDS@@）此前对"跨表撞号"完全隐形。今天起 M814…M818 与全部 python 臂一起数：`ARM_TOTAL files=@@FILES@@ arms=@@TOTALARMS@@ dupes=0 repeats=0`。
- **U-854：名册不只会数号，还会验锚点** —— 每把 manifest 刀的 `.old` 必须在目标文件里恰好命中一次，`.new` 必须与 `.old` 不同（否则是空刀）。现读 `BASH_ARMS … bad=0`。
- **U-855：这把新尺第一版说了假话，被自己人抓住** —— 我按"整行相等"数命中，而 `.old` 存的是变异表真正 `text.count(old)` 的那段子串（常常没有行首缩进）⇒ 一次报出 **7 把老刀"针死了"**。那是尺的假指控，不是账的缺陷：改成与变异同一颗计数法（子串计数）之后 16 把全过。D-247 记的就是这一条：**预检必须与被它预检的那把尺共用同一个估计量**。
- **U-856：交出来的真账是 @@ROTN@@ 根腐烂针** —— @@ROT@@。这正是 BACKLOG 286 一直说的那一族，今天第一次有**具体刀号**（不是"某几支可能腐烂"）。286 保持仍开，本轮不修（修锚点要重跑对应的表，而重跑要 swift test 的时间预算）。
- **U-857：电池与 CI** —— 名册卷新增两格（人造撞号 manifest 必须被点名；仓库现状必须 0 撞号、≥5 把 bash 刀、锚点全过），@@BATT@@。CI：@@CI@@（两跑 in_progress ⇒ 只能写未读）。

读数腿：RUN（预检三行 + 电池一行）。
眼睛腿：NOT-RUN —— 本轮 0 产品文件、0 新帧；R260 那两张"改前/改后肉眼分不出"的结论仍在账上等 305 的地板。
变异腿：RUN（不是跑刀，是**让刀可被看见**：五把重捕型刀 + 十一把旧 manifest 刀全部进查重与锚点自检）。
未做（逐条）：① 286 的 @@ROTN@@ 根针要修（现在有名有姓）；② 299 的执行器半（`kind=recapture` 做进执行器，本轮只做了名册半）；③ 305 的地板；④ 301 + 307；⑤ 291 那四位；⑥ 287/284、297/298/300、304。

"""

ITER_NEW = """## Round 258 · 五把重捕型刀进名册，新尺第一版说了假话被自己抓住（R261 / 第 260 轮）/ D-247 · 306 结案、286 现读名单 · 产品 0 文件

本轮次对照：与 R260（自评 94，量出并修掉一个真产品缺陷）相比，本轮不碰产品，把连续两轮写在账上的"名册看不见 bash 刀"还掉；还完立刻交出 @@ROTN@@ 根腐烂针与一次自我误判。
看图腿：读数腿 RUN（预检 BASH_ARMS bad=0、ARM_TOTAL dupes=0、@@BATT@@）；眼睛腿 NOT-RUN（0 产品文件、0 新帧）。
七维度自评：
| 维度 | 分/满分 |
| 真实视觉审查 | 6/15 |
| 判据有效性 | 13/15 |
| 假绿防御 | 14/15 |
| 产品面推进 | 4/15 |
| 台账一致性 | 13/15 |
| 交付诚实性 | 15/15 |
| 可复核性 | 14/15 |
各维理由：真实视觉审查 6 —— 本轮没有画面可看，只把"看"的前置（刀可被复查）做齐；判据有效性 13 —— 查重器从今天起覆盖 16 把 manifest 刀并会验锚点与空刀；假绿防御 14 —— 拦住了两种假绿：撞号没人发现、以及**我自己那版按整行数命中的尺误报 7 把老刀死了**（写进 D-247，防止下一个人把尺的假话当账的缺陷修）；产品面推进 4 —— 0 产品文件，是有意还债不是新靶；台账一致性 13 —— 五本 + STATE 一次做齐，286 从"某几支可能腐烂"升级成有名有姓的 @@ROTN@@ 根；交付诚实性 15 —— 自我误判、未修的针、两跑未读全写；可复核性 14 —— 预检一条命令可重跑、两格人造撞号当正对照。合计 **79**/105。

"""

DEC_NEW = """**D-247（R261）：预检必须与被它预检的那把尺共用同一个估计量 —— 否则"针死了"这种指控可能只是尺自己在说谎。** 理由：R261 给 manifest 刀写锚点自检时按"整行相等"数命中，而变异表用的是 `text.count(needle)` 的子串计数，且 `.old` 常常没有行首缩进 —— 结果一次报出 7 把老刀腐烂，全是假指控。改成同一颗计数法后 16 把全过，真账是另外那 @@ROTN@@ 根（在 python 表里，286）。与 R68（证人要与它作证的判据同一颗尺子）、D-245（别造第二份定义处）同族：这一条是"别造第二份**计数法**"。

"""

BACK_NEW = """  追记（R261）：306 结案 —— `cross_table_ids` 现在也吃 `arms_r*/manifest.tsv`（@@TABLES@@ 张表、@@ARMS@@ 把刀，kind=@@KINDS@@），并新增 `check_manifests`：锚点必须恰好命中一次、`.new` 不得等于 `.old`（空刀）。名册卷加两格：人造撞号 manifest 必须被点名（正对照）、仓库现状必须 0 撞号且 ≥5 把 bash 刀。现读 dupes=0、bad=0。
  追记（R261）：286 第一次有具体名单 —— 预检现读 @@ROTN@@ 根针腐烂：@@ROT@@。本轮**没修**（修锚点要重跑对应的表，需要 swift test 的时间预算），也没有把 bad 降成 0：数字照账写。下一轮修的时候注意 D-247 —— 计数法要与变异表一致。

"""

CHG_NEW = """### Changed（R261 / 第 260 轮 / Round 258 · 五把重捕型刀进名册）

`mutate_needle_precheck.py`：`cross_table_ids` 除 `mutate_r*.py` 之外也吃 `arms_r*/manifest.tsv`（沿用 R245 起的七列契约，不另造形状 = D-245），新增 `manifest_rows` / `anchor_hits` / `check_manifests` —— 锚点必须恰好命中一次、`.new` 不得等于 `.old`。现读：manifest 表 @@TABLES@@ 张、刀 @@ARMS@@ 把（M802…M818）、`ARM_TOTAL arms=@@TOTALARMS@@ dupes=0`、`BASH_ARMS bad=0`。
名册卷 `scripts/tests/test_mutate_arm_registry.py` +2 格：人造撞号 manifest 必须被点名（正对照）、仓库现状必须 0 撞号且锚点全过。@@BATT@@。
自我误判一次并记进 D-247：锚点计数第一版按整行相等，误报 7 把老刀腐烂 —— 预检必须与变异表共用同一个估计量。
真账：@@ROTN@@ 根针确实死了（@@ROT@@），286 从猜测升级成名单，本轮未修、未把数字改小。306 结案、299 的执行器半仍开。产品 0 文件。

"""

STATE_NEW = """## R261 状态（第 260 轮 / Round 258 · @@DATE@@）
最后更新：2026-10-21（本地 · R261 / 第 260 轮 / Round 258）：**五把重捕型刀进名册，新尺第一版说了假话被自己抓住**（U-853…U-857 · D-247 · 306 结案、286 现读名单 · 产品 0 文件 · 自评 79/105）

**本轮落地**：`cross_table_ids` 吃 manifest（@@TABLES@@ 张 / @@ARMS@@ 把 / dupes=0）+ `check_manifests`（锚点恰好一次、不许空刀、bad=0）；名册卷 +2 格带正对照；@@BATT@@。交出的坏消息：@@ROTN@@ 根 python 表的针已腐烂（@@ROT@@），286 有名有姓了。

**下一轮（R262 / 第 261 轮 / Round 259）的 ⓪**：
⓪ 读 CI：@@CI@@ —— 本笔 push 后再取；要看 runner 在新梯子（R260）下有没有把亮档选中帧判成 changed，以及 `RUNG_STEP`/`PRESS_LADDER` 的两机读数。
① 286：修那 @@ROTN@@ 根针（按 D-247 的计数法修，修完重跑对应的表，别只改锚点不重跑）。
② 305 的地板（两机读数 + 一次真判）；299 的执行器半（`kind=recapture` 做进执行器）；301 + 307。
③ 291 那四位；287/284；297/298/300、304；用户闸门 220 路 A / 228② / 265。

"""


def render(s):
    for key, v in V.items():
        s = s.replace(key, v)
    if "@@" in s:
        die("渲染后仍有未替换占位符：" + s[:120])
    return s


names = ["UI_NEW", "ITER_NEW", "DEC_NEW", "BACK_NEW", "CHG_NEW", "STATE_NEW"]
vals = {n: render(globals()[n]) for n in names}
UI_NEW, ITER_NEW, DEC_NEW, BACK_NEW, CHG_NEW, STATE_NEW = (vals[n] for n in names)

ui_old = rd(UI)
mark = "## 第 259 轮"
if mark not in ui_old:
    die("UI_AUDIT 找不到锚点")
i = ui_old.index(mark)
ui_new = ui_old[:i] + UI_NEW + ui_old[i:]
iter_new = rd(ITER).rstrip("\n") + "\n\n" + ITER_NEW
dec_new = rd(DEC).rstrip("\n") + "\n\n" + DEC_NEW
chg_old = rd(CHG)
head = "## [Unreleased]\n"
if head not in chg_old:
    die("CHANGELOG 找不到 [Unreleased]")
chg_new = chg_old.replace(head, head + "\n" + CHG_NEW, 1)
# 306 / 286 的追记挂在各自那一节之下
back_old = rd(BACK)
blines = back_old.splitlines(True)


def append_after(lines, num, payload):
    idx = [n for n, l in enumerate(lines) if re.match(r"^\*\*" + num + r"\. ", l)]
    if len(idx) != 1:
        die("BACKLOG " + num + " 锚点命中 " + str(len(idx)) + " 次")
    k = idx[0] + 1
    while k < len(lines) and lines[k].strip():
        k += 1
    return lines[:k] + payload.splitlines(True) + lines[k:]


note306 = ("  追记（R261）：306 结案 —— `cross_table_ids` 现在也吃 `arms_r*/manifest.tsv`（" + V["@@TABLES@@"] +
           " 张表、" + V["@@ARMS@@"] + " 把刀，kind=" + V["@@KINDS@@"] + "），并新增 `check_manifests`："
           "锚点必须恰好命中一次、`.new` 不得等于 `.old`（空刀）。名册卷加两格：人造撞号 manifest 必须被点名（正对照）、"
           "仓库现状必须 0 撞号且 ≥5 把 bash 刀。现读 dupes=0、bad=0。\n")
note286 = ("  追记（R261）：286 第一次有具体名单 —— 预检现读 " + V["@@ROTN@@"] + " 根针腐烂：" + V["@@ROT@@"] +
           "。本轮**没修**（修锚点要重跑对应的表，需要 swift test 的时间预算），也没有把 bad 降成 0：数字照账写。"
           "下一轮修的时候注意 D-247 —— 计数法要与变异表一致。\n")
lines306 = append_after(blines, "306", note306)
lines_both = append_after(lines306, "286", note286)
back_new = "".join(lines_both)
st_old = rd(STATE)
st_mark = "## R260 状态"
if st_mark not in st_old:
    die("STATE 找不到锚点")
state_new = st_old.replace(st_mark, STATE_NEW + st_mark, 1)


def must_preserve(old, new, name):
    co, cn = Counter(old.splitlines()), Counter(new.splitlines())
    lost = [l for l, c in co.items() if cn[l] < c]
    if lost:
        die(name + " 弄丢 " + str(len(lost)) + " 行：" + " | ".join(lost[:2])[:150])


must_preserve(ui_old, ui_new, "AGENT_UI_AUDIT.md")
must_preserve(chg_old, chg_new, "CHANGELOG.md")
must_preserve(back_old, back_new, "AGENT_BACKLOG.md")
must_preserve(st_old, state_new, "AGENT_STATE.md")
for o, n_, nm in ((rd(ITER), iter_new, "AGENT_VISUAL_ITERATION.md"), (rd(DEC), dec_new, "AGENT_DECISIONS.md")):
    if not n_.startswith(o.rstrip("\n")):
        die(nm + " 不是纯追加")
ids = [int(x) for x in re.findall(r"- \*\*U-(\d+)", UI_NEW)]
if ids != list(range(853, 858)):
    die("本轮 U 号不连续：" + str(ids))
if "U-853…U-857" not in UI_NEW.splitlines()[0]:
    die("节标题 U 区间与定义不符")
if iter_new.count("| 真实视觉审查 |") != rd(ITER).count("| 真实视觉审查 |") + 1:
    die("七维表多写或少写")
rows = [l for l in iter_new.split("## Round 258 ·")[1].splitlines() if l.startswith("| ")]
if len(rows) != 8:
    die("七维表形状不对：" + str(len(rows)))
if "D-247" in rd(DEC):
    die("D-247 已存在")
if back_new.count("追记（R261）") != 2:
    die("306/286 的追记没写够两条：" + str(back_new.count("追记（R261）")))
if "## R261 状态" not in state_new:
    die("STATE 没轮换")

for p, t in ((UI, ui_new), (ITER, iter_new), (DEC, dec_new), (BACK, back_new), (CHG, chg_new), (STATE, state_new)):
    with open(p, "w", encoding="utf-8") as f:
        f.write(t)
print("LEDGERS_R261 OK batt=" + V["@@BATT@@"] + " manifest_arms=" + V["@@ARMS@@"] + " rot=" + V["@@ROTN@@"]
      + " U=853..857 D=247")
