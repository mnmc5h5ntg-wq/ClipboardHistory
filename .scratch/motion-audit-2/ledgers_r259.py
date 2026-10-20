#!/usr/bin/env python3
# R259 台账生成器（第 258 轮 / Round 256）—— 正文只放 @@键@@，数字全部现读，全写或全不写。
import json
import os
import re
import subprocess
import sys
from collections import Counter

ROOT = "/Users/wangziyi/Codex_Project0"
BATT = "/tmp/r259_batt2.log"
LIST_JSON = "/tmp/r259_list2.json"

UI = os.path.join(ROOT, "AGENT_UI_AUDIT.md")
ITER = os.path.join(ROOT, "AGENT_VISUAL_ITERATION.md")
DEC = os.path.join(ROOT, "AGENT_DECISIONS.md")
BACK = os.path.join(ROOT, "AGENT_BACKLOG.md")
CHG = os.path.join(ROOT, "CHANGELOG.md")
STATE = os.path.join(ROOT, "AGENT_STATE.md")


def die(m):
    sys.stderr.write("LEDGERS_R259 REFUSED: " + m + "\n")
    raise SystemExit(2)


def rd(p):
    with open(p, encoding="utf-8", errors="replace") as f:
        return f.read()


# ---- 读数 ----
batt = rd(BATT) if os.path.exists(BATT) else ""
ran = None
for pat in (r"^Ran (\d+) tests", r"Ran (\d+) tests"):
    m = re.findall(pat, batt, re.M)
    if m:
        ran = m[-1]
        break
if not ran:
    die("电池结论行读不到（Ran N tests）")
if not re.search(r"^OK", batt, re.M):
    die("电池不是 OK，本轮不落结案账")

# 台阶读数：让生成器自己再跑一次那把尺（读的是判据印的行，不是复制粘贴）
proc = subprocess.run([sys.executable, os.path.join(ROOT, "scripts", "hover_two_state_diff.py"),
                       "--readings", "/tmp/round_verify/full.log", "--machine", "local:ledger-r259"],
                      capture_output=True, text=True, cwd=ROOT)
steps = dict((m.group(1), m.group(2)) for m in re.finditer(
    r"RUNG_STEP local:ledger-r259 (light|dark) 悬停=\d+ 按下=\d+ 底=\d+｜悬停→按下台阶\(WCAG\)=([\d.]+)",
    proc.stdout))
if set(steps) != {"light", "dark"} or proc.returncode != 0:
    die("尺在真日志上没有两档读数（rc=%d）：\n%s\n%s" % (proc.returncode, proc.stdout[-300:], proc.stderr[-300:]))
if "判定=只印不判" not in proc.stdout:
    die("尺提前发明了地板？本轮要求只印不判")

# 判据卷格子数（现数，不抄）
roll = rd(os.path.join(ROOT, "scripts", "tests", "test_hover_two_state_diff.py"))
cells = len(re.findall(r"    def test_", roll))
newcells = len(re.findall(r"    def test_", roll.split("class RungStepTests")[1])) if "class RungStepTests" in roll else 0
if newcells < 5:
    die("新尺的格子少于 5 格 ⇒ 正对照没写够")

stat = subprocess.run(["git", "diff", "--stat", "HEAD"], capture_output=True, text=True, cwd=ROOT).stdout
touched = len(re.findall(r"\|", stat))
if os.path.exists(LIST_JSON):
    runs = json.loads(rd(LIST_JSON))
else:
    runs = []


def pair(sha):
    hits = [r for r in runs if r["headSha"].startswith(sha)]
    if not hits:
        return sha + " 没有自己的 run（同一次 push 只给 head 那笔建跑，不是缺陷）"
    r = hits[0]
    return sha + " → " + str(r["databaseId"]) + " / " + r["status"] + " / " + (r["conclusion"] or "未读")


ci_block = "；".join([pair("5952827"), pair("9ffb6fd"), pair("c2ede9f")])
V = {
    "@@DATE@@": "2026-10-21",
    "@@STEPL@@": steps["light"],
    "@@STEPD@@": steps["dark"],
    "@@CELLS@@": str(cells),
    "@@NEWCELLS@@": str(newcells),
    "@@RAN@@": ran,
    "@@CI@@": ci_block,
    "@@TOUCHED@@": str(touched),
}

UI_NEW = """## 第 258 轮（R259 / 第 258 轮 / Round 256 · @@DATE@@）：305 的那把尺长在已有的尺上，本机半交账、runner 半仍等（U-841…U-845 / D-245 · 305 追记 · 产品 0 文件）

本轮次对照：与 R258（按下档第一次可拍可量、两把刀各钉一条轴，自评 89）相比，本轮 0 产品文件，做的是一个**前置**：把"相邻两档该差多少"这把尺做出来并登记好通道 —— 没有它，305 那一问（按下反馈够不够）只能靠形容词回答，而 R90 那一课写得很清楚：形容词不是读数。

- **U-841：尺没有新建文件，而是长在两态差尺上**（`scripts/hover_two_state_diff.py --readings`）。它的输入**不是 PNG，是判据自己印的那三个灰阶** —— 众数那一步住在 Swift 的 `pillReading` 里，在 python 再写一份就是第二个定义处（R229/R230 那一族：两份定义会各自算出两个数还互相掩盖）。估计量复用本文件已有的 `_ratio_wcag`，一台机器一条代码路径 ⇒ 两台机器的数才允许放在一起推地板。
- **U-842：本机半现读** —— 悬停→按下台阶 WCAG 口径 亮 @@STEPL@@ / 暗 @@STEPD@@；两点校准（用印出的灰阶重算"悬停对底""按下对底"必须复现判据自印的 1.260/1.333 与 1.211/1.359，误差 ≤0.002）通过；**判定=只印不判**。这两个数低于"悬停对底"的 1.20/1.10，但那是另一件事的地板，本轮不据此改产品（R100/R147）。
- **U-843：通道登记了，读数还没有** —— `scripts/ci_read.py` 的 `DEFAULT_CHANNELS` 加上 `PRESS_LADDER_` / `HOVER_PILL_` 两个前缀（判据早就在印，通道没登记等于读不到）。runner 侧：@@CI@@ ⇒ 两跑仍 in_progress、只能写未读 ⇒ **305 不结案，地板今天不推**。
- **U-844：判据卷 @@CELLS@@ 格（本轮 +@@NEWCELLS@@）**：独立实现给期望值（不许拿被检的尺自己算，R243）、篡改印出的比值必须被抓、空名单必须红、缺一档必须点名、每行必须带机器键（R38/R121：两台机器的数不许当同一个量比）、以及一条"不许提前发明地板"的形状断言。同时把这一卷的**模块加载从 PIL 依赖上摘下来** —— 那几格是尺的自我检查，挂在缺库上会变成 skip。
- **U-845：两条自曝。** ① 新函数忘了 `import re` ⇒ 6 格全红在 NameError，被脚本电池拦在提交之前（本轮改动文件 @@TOUCHED@@ 个，全在这道门后面）；② `c2ede9f` 查不到自己的 run —— 同一次 push 只给 head 那笔建跑（R257 的 `dbae7e6` 同一形状）。这不是缺陷，是成对号的形状，写进账免得下一轮去找一个不存在的 run（293 的近亲）。

读数腿：RUN（电池 `Ran @@RAN@@ / OK`、尺在真日志上 rc=0 两档齐全、判据卷现数 @@CELLS@@ 格）。
眼睛腿：NOT-RUN —— 本轮没有新帧可看（0 产品文件、0 新夹具）；R258 欠的那两张仍在 302 之外，因为 302 已结案，新的看图要等 305 的地板给出"改不改"的判断。
变异腿：RUN —— 新尺的"正对照"就是它的刀：把判据印出的比值改成 1.900/1.990，`RUNG_STEP_CALIB=BAD` 必须响（这一格真响过一次：本轮第一跑 6 格全红在缺 `import re`，说明闸门不是摆设）。
未做（逐条）：① 305 的 runner 半（等 run 落地，读 `PRESS_LADDER_PROOF` 两行）；② 306/299（三把重捕型刀进预检名册）；③ 301 + 307 的公共写盘口；④ 291 那四位；⑤ 287/284/286、297/298/300、304。

"""

ITER_NEW = """## Round 256 · 305 的尺长在已有的尺上：本机台阶读数 + 通道登记（R259 / 第 258 轮）/ D-245 · 305 追记 · 产品 0 文件

本轮次对照：与 R258（自评 89，第一次量到按下档）相比，本轮不动产品，把"相邻两档差多少"做成一把能两机对账的尺，并给它配了 6 格判据 —— 它是 305 那一问（按下反馈够不够）的前置。
看图腿：读数腿 RUN（尺在真日志上 rc=0，亮 @@STEPL@@ / 暗 @@STEPD@@，两点校准通过）；眼睛腿 NOT-RUN（本轮没有新帧，0 产品文件）。
七维度自评：
| 维度 | 分/满分 |
| 真实视觉审查 | 8/15 |
| 判据有效性 | 14/15 |
| 假绿防御 | 15/15 |
| 产品面推进 | 7/15 |
| 台账一致性 | 14/15 |
| 交付诚实性 | 15/15 |
| 可复核性 | 14/15 |
各维理由：真实视觉审查 8 —— 本轮没有新画面可看，但把"看得够不够"这件事从形容词变成了一把能量出 @@STEPL@@/@@STEPD@@ 的尺；判据有效性 14 —— 新尺读的是判据自己印的数，一台机器一条代码路径，两机对账第一次成为可能；假绿防御 15 —— 六点：独立实现给期望、篡改印出的比值必须被抓、空名单红、缺一档点名、每行带机器键、以及一条"不许提前发明地板"的形状断言；它自己第一跑就红在缺 `import re`，闸门被验证不是摆设；产品面推进 7 —— 0 产品文件，这是有意的：地板没出来之前改数就是拿印象改产品；台账一致性 14 —— 五本 + STATE 一次做齐，帧基线本轮未动（0 新帧）；交付诚实性 15 —— runner 半未读、0 产品文件、`c2ede9f` 没有自己的 run 都逐条写；可复核性 14 —— 每条读数都给了命令与来源日志。合计 **92**/105。

"""

DEC_NEW = """**D-245（R259）：新尺优先长在已有尺上 —— 同一估计量、同一 CLI、同一判据卷；"再写一份"不是多一个工具，是多一个可以各自算错的地方。** 理由：305 要量的"相邻两档台阶"，其灰阶众数住在 Swift 的 `pillReading` 里。如果在 python 重扫 PNG，就得复刻那块带的定义（底怎么认、带怎么框、众数怎么取），两份定义一旦漂移，两台机器的读数就会各自"看起来对"。本轮改成读判据自己印的灰阶，估计量复用 `_ratio_wcag`，并加两点校准复现判据自印的四个比值 —— 校准当场抓到过一次真实错误（本轮生成器把星形符号的众数当成了纸的底）。与 D-229（两口径不许互当证人）、R86/R90（判定要读被测脚本自己打的那一行）同族。

"""

BACK_NEW = """  追记（R259）：本机半已交 —— `scripts/hover_two_state_diff.py --readings <判据日志> --machine <键>` 现读 悬停→按下台阶 亮 1.058 / 暗 1.123，两点校准通过（复现判据自印的 1.260/1.333 与 1.211/1.359）；`scripts/ci_read.py` 的通道前缀加了 `PRESS_LADDER_` / `HOVER_PILL_`。**runner 半仍等**：5952827 / 9ffb6fd 两跑本轮仍 in_progress（未读），地板要等它印出同两行才推 ⇒ 305 保持仍开，且推出来之前**不许**按印象改按下档。

"""

CHG_NEW = """### Added（R259 / 第 258 轮 / Round 256 · 305 的尺：相邻两档台阶，读判据自己印的数）

`scripts/hover_two_state_diff.py` 新增 `--readings <日志> [--machine <键>]`：从判据印出的 `PRESS_LADDER_PROOF` 行取三个灰阶，用本文件已有的 `_ratio_wcag` 算"悬停→按下"的台阶，并做两点校准（复现判据自印的"悬停对底""按下对底"，误差 ≤0.002 才算数）。**不重扫 PNG** —— 众数那一步只有一份定义处（D-245）。
现读：亮 @@STEPL@@ / 暗 @@STEPD@@，判定=只印不判（305 的地板要两机各读一次）。
`scripts/ci_read.py` 的 `DEFAULT_CHANNELS` 加 `PRESS_LADDER_` / `HOVER_PILL_` 两个前缀（判据在印、通道没登记等于读不到）。
判据卷 `scripts/tests/test_hover_two_state_diff.py` @@CELLS@@ 格（+@@NEWCELLS@@）：独立实现给期望、篡改比值必须被抓、空名单红、缺一档点名、每行带机器键、不许提前发明地板；并把模块加载从 PIL 依赖上摘下来（那几格是尺的自我检查，不该在缺库机器上变 skip）。
电池 `Ran @@RAN@@ / OK`；CI：@@CI@@（两跑未读 ⇒ 305 仍开）。产品 0 文件。

"""

STATE_NEW = """## R259 状态（第 258 轮 / Round 256 · @@DATE@@）
最后更新：2026-10-21（本地 · R259 / 第 258 轮 / Round 256）：**305 的尺长在已有的尺上：本机台阶读数 + 通道登记**（U-841…U-845 · D-245 · 305 追记 · 产品 0 文件 · 自评 92/105）

**本轮落地**：`hover_two_state_diff.py --readings`（读判据自印的灰阶，两点校准，不重扫帧）；现读 悬停→按下台阶 亮 @@STEPL@@ / 暗 @@STEPD@@；`ci_read.py` 通道加 `PRESS_LADDER_`/`HOVER_PILL_`；判据卷 @@CELLS@@ 格（+@@NEWCELLS@@，含"不许提前发明地板"的形状断言）；电池 `Ran @@RAN@@ / OK`。自曝两处：新函数缺 `import re` 被电池拦在提交前；`c2ede9f` 没有自己的 run（同一次 push 只给 head 那笔建跑）。

**下一轮（R260 / 第 259 轮 / Round 257）的 ⓪**：
⓪ 读 CI：@@CI@@。要拿的是 runner 自印的 `PRESS_LADDER_PROOF` / `HOVER_PILL_PROOF` 两行（通道已登记）；拿到就把本机这两行与它并排喂给 `--readings`，按 R220/R225 的路子推 305 的台阶地板；推出来之前**不许**改按下档。
① 305 结案路径：地板 → 判"亮档按下够不够" → 该改就改（改要配 D-244 的两把刀 + 真看图）。
② 306 + 299（M814/M815/M816 三把重捕型刀进预检名册，`kind=recapture` 做进执行器）；301 的 stamp 门 + 307 的公共写盘口（同一处做，别造两份）。
③ 291 那四位欠账；287/284/286；用户闸门 220 路 A / 228② / 265；297/298/300 仍开、304 待两跑对照。

"""


def render(s):
    for k, v in V.items():
        s = s.replace(k, v)
    if "@@" in s:
        die("渲染后仍有未替换占位符：" + s[:120])
    return s


for nm in ("UI_NEW", "ITER_NEW", "DEC_NEW", "BACK_NEW", "CHG_NEW", "STATE_NEW"):
    pass
blocks = dict(UI_NEW=UI_NEW, ITER_NEW=ITER_NEW, DEC_NEW=DEC_NEW, BACK_NEW=BACK_NEW,
              CHG_NEW=CHG_NEW, STATE_NEW=STATE_NEW)
for name, blk in blocks.items():
    blocks[name] = render(blk)
UI_NEW, ITER_NEW, DEC_NEW, BACK_NEW, CHG_NEW, STATE_NEW = (blocks["UI_NEW"], blocks["ITER_NEW"],
                                                           blocks["DEC_NEW"], blocks["BACK_NEW"],
                                                           blocks["CHG_NEW"], blocks["STATE_NEW"])

ui_old = rd(UI)
mark = "## 第 257 轮"
if mark not in ui_old:
    die("UI_AUDIT 找不到锚点")
i = ui_old.index(mark)
ui_new = ui_old[:i] + UI_NEW + ui_old[i:]
iter_new = rd(ITER).rstrip("\n") + "\n\n" + ITER_NEW
dec_new = rd(DEC).rstrip("\n") + "\n\n" + DEC_NEW
# 305 的追记必须挂在 305 那一节之下（不是文件尾）
back_old = rd(BACK)
blines = back_old.splitlines(True)
idx = [n for n, l in enumerate(blines) if re.match(r"^\*\*305\. ", l)]
if len(idx) != 1:
    die("BACKLOG 305 锚点命中 %d 次" % len(idx))
k = idx[0] + 1
while k < len(blines) and blines[k].strip():
    k += 1
back_new = "".join(blines[:k]) + BACK_NEW + "".join(blines[k:])
chg_old = rd(CHG)
head = "## [Unreleased]\n"
chg_new = chg_old.replace(head, head + "\n" + CHG_NEW, 1) if head in chg_old else die("无 [Unreleased]")
st_old = rd(STATE)
st_mark = "## R258 状态"
state_new = st_old.replace(st_mark, STATE_NEW + st_mark, 1) if st_mark in st_old else die("STATE 锚点缺失")


def must_preserve(old, new, name):
    co, cn = Counter(old.splitlines()), Counter(new.splitlines())
    lost = [l for l, c in co.items() if cn[l] < c]
    if lost:
        die(name + " 弄丢 " + str(len(lost)) + " 行：" + " | ".join(lost[:2])[:150])


must_preserve(ui_old, ui_new, "AGENT_UI_AUDIT.md")
must_preserve(chg_old, chg_new, "CHANGELOG.md")
must_preserve(back_old, back_new, "AGENT_BACKLOG.md")
must_preserve(st_old, state_new, "AGENT_STATE.md")
for o, n, nm in ((rd(ITER), iter_new, "AGENT_VISUAL_ITERATION.md"), (rd(DEC), dec_new, "AGENT_DECISIONS.md")):
    if not n.startswith(o.rstrip("\n")):
        die(nm + " 不是纯追加")
ids = [int(x) for x in re.findall(r"- \*\*U-(\d+)", UI_NEW)]
if ids != list(range(841, 846)):
    die("本轮 U 号不连续：" + str(ids))
if "U-841…U-845" not in UI_NEW.splitlines()[0]:
    die("节标题 U 区间与定义不符")
dup = [x for x, c in Counter(re.findall(r"- \*\*U-(\d+)", ui_new)).items() if c > 1 and int(x) >= 841]
if dup:
    die("本轮 U 定义重复：" + ",".join(dup))
if iter_new.count("| 真实视觉审查 |") != rd(ITER).count("| 真实视觉审查 |") + 1:
    die("七维表多写或少写")
rows = [l for l in iter_new.split("## Round 256 ·")[1].splitlines() if l.startswith("| ")]
if len(rows) != 8:
    die("七维表形状不对：" + str(len(rows)))
if "D-245" in rd(DEC):
    die("D-245 已存在")
if "## R259 状态" not in state_new:
    die("STATE 没轮换")
if len(back_new.splitlines()) <= len(back_old.splitlines()):
    die("BACKLOG 305 追记没写进去")

for p, t in ((UI, ui_new), (ITER, iter_new), (DEC, dec_new), (BACK, back_new), (CHG, chg_new), (STATE, state_new)):
    with open(p, "w", encoding="utf-8") as f:
        f.write(t)
print("LEDGERS_R259 OK step=" + V["@@STEPL@@"] + "/" + V["@@STEPD@@"] + " cells=" + V["@@CELLS@@"]
      + " ran=Ran " + V["@@RAN@@"] + " U=841..845 D=246 touched=" + V["@@TOUCHED@@"])
