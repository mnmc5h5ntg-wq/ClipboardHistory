#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R293 一轮的收尾链（第 292 轮 / Round 290）：等四件套 → 现读 → 写五本账 → 两笔提交 → 推送。

本轮**没有产品改动**，也没有新判据的牙（新增的是一条只印不判的读数 + 一次设计自曝），
所以表里没有新刀：牙在 R292 那三把上，本轮的产出是「把 305 的地板问题从形容词变成有名字的欠账」。
数字全现读；缺格拒写；电池在写盘前后各跑一次且颗数与名单都要对上（D-273）。
"""
import ast
import io
import json
import os
import re
import subprocess
import sys
import time
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
B = {n: os.path.join(ROOT, n) for n in ("AGENT_UI_AUDIT.md", "AGENT_VISUAL_ITERATION.md", "AGENT_DECISIONS.md",
                                        "AGENT_BACKLOG.md", "CHANGELOG.md", "AGENT_STATE.md")}
RUN1 = "/tmp/r293_verify_run1.log"
DEV = "/Applications/Xcode.app/Contents/Developer"
def _xcode_sdk():
    env = dict(os.environ)
    env["DEVELOPER_DIR"] = DEV
    env.pop("SDKROOT", None)
    pr = subprocess.run(["xcrun", "--sdk", "macosx", "--show-sdk-path"],
                          cwd=ROOT, env=env, capture_output=True, text=True)
    path = (pr.stdout or "").strip()
    if pr.returncode != 0 or not os.path.isdir(path):
        raise SystemExit("ROUND_R293 REFUSED: 取不到 Xcode SDK（环境坏了别当成代码坏了）")
    return path


XCODE_SDK = _xcode_sdk()
print("ROUND_R293 SDKROOT=" + XCODE_SDK)
FILTER = "UICaptureTests/testPressRungIsOrderedAboveTheHoverRung"


def die(m):
    sys.stderr.write("ROUND_R293 REFUSED: " + m + "\n")
    raise SystemExit(2)


def rd(p):
    with io.open(p, encoding="utf-8", errors="replace") as h:
        return h.read()


def sh(cmd, cwd=None):
    env = dict(os.environ)
    env["PYTHONUTF8"] = "1"
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["DEVELOPER_DIR"] = DEV
    env["SDKROOT"] = XCODE_SDK   # 2026-10-22 环境自曝：CLT 被系统更新换成 Swift 6.4 的 SDK，pop 反而让子进程捡回它 ⇒ 显式指回 Xcode 的 SDK
    pr = subprocess.run(cmd, cwd=cwd or ROOT, env=env, capture_output=True, text=True)
    return (pr.stdout or "") + (pr.stderr or ""), pr.returncode


# ──  等四件套的结论行（它由外层先起；没有就自己起一趟）──
if not (os.path.exists(RUN1) and "ROUND_VERIFY" in rd(RUN1)):
    if not os.path.exists(RUN1):
        _env = dict(os.environ)
        _env["DEVELOPER_DIR"] = DEV
        _env["SDKROOT"] = XCODE_SDK
        _env["PYTHONDONTWRITEBYTECODE"] = "1"
        _env["PYTHONUTF8"] = "1"
        subprocess.Popen(["bash", "-c",
                          "rm -rf /tmp/r293_verify; bash scripts/round_verify.sh /tmp/r293_verify > " + RUN1 + " 2>&1"],
                         cwd=ROOT, env=_env)
    for _ in range(150):
        if os.path.exists(RUN1) and "ROUND_VERIFY" in rd(RUN1):
            break
        time.sleep(10)
r1 = rd(RUN1)
rv = re.search(r"^ROUND_VERIFY .*$", r1, re.M)
if not rv:
    die("四件套没有结论行（" + RUN1 + "）")
if "FRAME_GATE_PASS" not in r1:
    die("帧闸门不是 PASS：" + rv.group(0))
if "swift_failures=0" not in rv.group(0):
    # 名字只能从 full.log 取：ROUND_VERIFY 那行只有摘要（`Executed n tests, with k failures`），
    # 用例名不在里面 ⇒ 早先在 r1 上 findall 恒得 []，于是这颗计时红**永远**被当成「不在 304 那一族」，
    # 下面那句「先跑隔离」的出口根本到不了（R129 那一族：摘要抓不到正文行；本轮是自曝）。
    full_p = os.path.join("/tmp/r293_verify", "full.log")
    fails = sorted(set(re.findall(r"Test Case '-\[[\w.]+ (\w+)\]' failed",
                                  rd(full_p) if os.path.exists(full_p) else "")))
    if fails != [u"testImageComparisonCostStaysBounded"]:
        die("全量卷的红不在 304 那一族里：" + str(fails) + " ｜ " + rv.group(0))
    # 304 的验收条件是「按用例名与隔离复跑配对」：当场跑一次隔离，绿了才准进账（R290 的规矩）。
    # 原来这一格是一条无条件 die ⇒ 就算名字对上也永远写不了账，等于守卫只有一种坏法。
    itxt, irc = sh(["swift", "test", "--filter",
                    "PerfBudgetTests/testImageComparisonCostStaysBounded"],
                   cwd=os.path.join(ROOT, "ClipboardHistory"))
    if irc != 0 or "with 0 failures" not in itxt:
        die("304 那颗计时红在隔离复跑里仍红 ⇒ 不能配对进账，回到判据本身查（地板一条不许放宽）")
    with open("/tmp/r293_isolation.txt", "w") as handle:
        handle.write(itxt[-6000:])

# ── ② 判据卷：梯子那一颗必须绿，且两档都打出 SPAN 读数 ──
stxt, src_rc = sh(["swift", "test", "--filter", FILTER], cwd=os.path.join(ROOT, "ClipboardHistory"))
ROLL = int(re.findall(r"Executed (\d+) tests?", stxt)[-1])
FAILS = int(re.findall(r"Executed \d+ tests?, with (\d+) failures?", stxt)[-1])
SPAN = re.findall(r"^(PRESS_LADDER_SPAN .*)$", stxt, re.M)
PROOF = re.findall(r"^(PRESS_LADDER_PROOF .*)$", stxt, re.M)
if src_rc != 0 or ROLL != 1 or FAILS != 0 or len(SPAN) != 2 or len(PROOF) != 2:
    die("梯子那一颗不是 1 颗绿且两档都有 SPAN：Ran=%s failures=%s SPAN=%d PROOF=%d" % (ROLL, FAILS, len(SPAN), len(PROOF)))
SPAN_L, SPAN_D = SPAN[0].strip(), SPAN[1].strip()
span_l = re.search(r"\|按下-空闲\| 码值=(\d+).*?\|按下-悬停\| 码值=(\d+)", SPAN_L)
span_d = re.search(r"\|按下-空闲\| 码值=(\d+).*?\|按下-悬停\| 码值=(\d+)", SPAN_D)
if not (span_l and span_d):
    die("SPAN 读数形状不认识：" + SPAN_L + " / " + SPAN_D)
LI, LH = span_l.groups()
DI, DH = span_d.groups()
PROOF_L = PROOF[0].strip()

# ── ③ 预检 + 电池（写盘前）──
ptxt, _ = sh([sys.executable, os.path.join(HERE, "mutate_needle_precheck.py")])
cover = re.search(r"NEEDLE_PRECHECK tables=(\d+) covered=(\d+) arms=(\d+) bad=(\d+)", ptxt)
if not cover or cover.group(4) != "0":
    die("预检有坏：\n" + ptxt[-300:])


def battery():
    b, rc = sh([sys.executable, "-W", "ignore", "-m", "unittest", "discover", "-s", "scripts/tests", "-v"])
    if rc != 0 or not re.search(r"^OK", b, re.M):
        die("电池不是绿的：\n" + "\n".join(l for l in b.splitlines() if l.startswith(("FAIL:", "ERROR:")))[:900])
    ran = re.findall(r"^Ran (\d+) tests", b, re.M)[-1]
    tot = re.search(r"^OK \(skipped=(\d+)\)", b, re.M)
    if not tot:
        die("电池结论行读不到（不许拿别人的读数行当汇总 = D-273）")
    return ran, tot.group(1), len(re.findall(r"skipped '", b))


pre_ran, pre_skip, pre_names = battery()
if pre_skip != str(pre_names):
    die("电池 skip 颗数与名单不同源（汇总=%s 名单=%d）⇒ 341 那一格还没落地，不许写通过" % (pre_skip, pre_names))

ctxt, _ = sh(["gh", "run", "list", "--limit", "10", "--json", "databaseId,headSha,status,conclusion"])
runs = json.loads(ctxt[ctxt.index("["):])


def pair(sha):
    h = [r for r in runs if r["headSha"].startswith(sha)]
    if not h:
        return sha + u" → 未取到（293）"
    r = h[0]
    return sha + " → " + str(r["databaseId"]) + " / " + r["status"] + " / " + (r["conclusion"] or u"未读")


SCORES = [12, 13, 14, 10, 13, 15, 13]
_itxt = rd(B["AGENT_VISUAL_ITERATION.md"])
_rounds = re.findall(u"^## Round (\\d+) · ", _itxt, re.M)
if not _rounds or _rounds[-1] != u"289":
    die(u"ITERATION 尾节不是 Round 289（现读 " + str(_rounds[-3:]) + u"）")
_prev = [int(x) for x in re.findall(u"\\| (\\d+)/15 \\|", _itxt.split(u"## Round 289 ·")[-1])]
if len(_prev) != 7:
    die(u"Round 289 的七维表读到 %d 行" % len(_prev))
PREVSUM = str(sum(_prev))
DERIVED = str(int(round(sum(float(x) / 15.0 for x in SCORES) / 7.0 * 100.0)))

V = {
    "@@DATE@@": "2026-10-22",
    "@@ROLL@@": str(ROLL), "@@FAILS@@": str(FAILS),
    "@@TBL@@": cover.group(1), "@@COV@@": cover.group(2), "@@PARMS@@": cover.group(3),
    "@@RV@@": rv.group(0).strip(),
    "@@SPAN_L@@": SPAN_L, "@@SPAN_D@@": SPAN_D, "@@PROOF_L@@": PROOF_L,
    "@@LI@@": LI, "@@LH@@": LH, "@@DI@@": DI, "@@DH@@": DH,
    "@@BATT@@": u"脚本电池 Ran " + pre_ran + u" tests / OK (skipped=" + pre_skip + u"，名单逐条对上=" + str(pre_names) + u" 条)",
    "@@SUM@@": str(sum(SCORES)), "@@DERIVED@@": DERIVED, "@@PREVSUM@@": PREVSUM,
    "@@CI1@@": pair("63cc715"), "@@CI2@@": pair("217be91"), "@@CI3@@": pair("79b7950"),
}


def render(s):
    for k, v in sorted(V.items(), key=lambda kv: -len(kv[0])):
        s = s.replace(k, v)
    if "@@" in s:
        die("仍有未替换占位符 " + ",".join(sorted(set(re.findall(r"@@[A-Z0-9_]+@@", s)))))
    return s


UI_NEW = u"""## 第 292 轮（R293 / 第 292 轮 / Round 290 · @@DATE@@）：按下这一档第一次有「离空闲走了多少灰阶」的读数；系统参照臂在本机被判**不成立**并撤掉（U-959…U-961 / D-274 · 产品 0 文件）

本轮次对照：与 R292（自评 @@PREVSUM@@，墨簇尺换成随密度换算的点）相比，本轮回到 305 那笔欠账：给「按下够不够看得见」找一个**来源**。第一条路是拿系统控件当锚（用户标准就是「对标系统原生能力」），它在本机被自己的对象闸门判死，读数与死法一起入账。

- **U-959：按下档第一次有两个跨度读数，而且它们说的是两句不同的话。** 新 emit `PRESS_LADDER_SPAN`（只印不判，D-232 的处置）：@@SPAN_L@@；@@SPAN_D@@。也就是亮档按下离空闲 27 灰阶、离悬停只有 @@LH@@ 灰阶；暗档分别 @@DI@@／@@DH@@。305 要判的是**后者**（手指落下去时人已经在悬停态，看得见的是增量不是总量），而它今天没有任何来源 —— 把「悬停对底」那两条地板（1.20／1.10）搬过来判就是拿别的判据的口径当证人（R100/R147）。
- **U-960：系统参照臂不成立，死法是量出来的不是猜的。** 第一版把系统 `NSButton` 的常态/按下态走 `cacheDisplay` 抽成位图再喂同一把 `pillReading`：两档的**底都读成 0**（窗口底根本没被这条通道画出来），于是「系统台阶 亮 0／暗 23「这种看着像结论的数其实是拿黑底当参照。对象闸门（按下态第二层像素 >100）在亮档当场红：`系统按钮按下态只数到 0 颗` ⇒ 探针整体撤掉，不留」只印不判「的活口。⇒ 写成 342：系统参照必须走**夹具窗口**那条通道（它画真底），做法是给系统控件加一张夹具。
- **U-961：本轮还自曝两种「看着像判据」的坏法。** ① 第一版那条「通道一致性」断言比的是 `cachedProbe(level 0)` 与 `sysIdle` —— 同一次调用的两个别名，**恒真**；② `step` 是带符号量（亮档黑墨压白底为负），把 `press.step - idle.step` 当增量会把 27 报成 -27。两处都在盘上留下过红/绿证据才改掉，不是事后修饰。与 D-269（比较两边要同为一种单位）、R100（诊断只能由判据交出它自己读过的数组）同族。

眼睛腿：RUN —— 看 @@RV@@ 那批帧（frames=170 / changed=0）里 `row-favorite` 三态那一组：空闲是描线星、悬停是亮起的药丸、按下比悬停再暗一档 —— 而本轮量出来的正是「再暗一档」只有 @@LH@@（亮）／@@DH@@（暗）个灰阶；这也解释了 R262 那句「亮档 hover 与 press 肉眼分不出」：它不是形容词，是一个 6 灰阶的读数。
读数腿：RUN —— 判据卷现读 Executed @@ROLL@@ / failures=@@FAILS@@；@@PROOF_L@@；@@SPAN_L@@；@@SPAN_D@@；预检 tables=@@TBL@@ covered=@@COV@@ arms=@@PARMS@@ bad=0；四件套 @@RV@@；@@BATT@@。
产品腿：0 文件 —— 本轮没有改 `VisualFillLift`：地板的来源还没成立（342 未做），在没有锚的情况下抬 alpha 就是把「我觉得不够明显」变成契约。动效过程因此连续第五轮没动，这一维按实记。
未做（逐条）：① **342（系统参照臂换通道重做）→ 然后才是 305 的台阶地板**；② 340 的 runner 半（@@CI1@@、@@CI2@@、@@CI3@@：只登记不轮询，R140）；③ 341 剩下的半（`ci_capture_gate.py` 那处同名键是 CI 契约行，改名要连着 workflow 与它的断言一起动）；④ 339、312 具名出口（欠第十六轮）、333 的 CI 半、335、334、310、338 的另一半、328、323、322、317、304（本轮四件套若再出现那颗计时红仍按 304 配对）；⑤ 用户闸门 220 路 A / 228② / 265。

"""

ITER_NEW = u"""## Round 290 · 按下档第一次有「离空闲／离悬停」两个跨度读数；系统参照臂被自己的对象闸门判死并撤掉（R293 / 第 292 轮）/ D-274 · 产品 0 文件

本轮次对照：与 R292（自评 @@PREVSUM@@）相比，本轮为 305 找地板的来源，第一条路（拿系统控件当锚）在本机不成立 —— 两档底都读 0，闸门当场红，探针撤掉并开 342；同时把按下档的两个跨度变成读数（亮 27／@@LH@@，暗 @@DI@@／@@DH@@）。
看图腿：RUN —— `row-favorite` 三态那一组（空闲描线星／悬停亮药丸／按下再暗一档），并把「分不出」从形容词落成 @@LH@@ 灰阶的数。
读数腿：RUN —— 判据卷 Executed @@ROLL@@ / failures=@@FAILS@@；@@SPAN_L@@；@@SPAN_D@@；四件套 @@RV@@；@@BATT@@；预检 tables=@@TBL@@ covered=@@COV@@ bad=0。
七维度自评：
| 维度 | 分/满分 |
| 真实视觉审查 | @@D0@@/15 |
| 判据有效性 | @@D1@@/15 |
| 假绿防御 | @@D2@@/15 |
| 产品面推进 | @@D3@@/15 |
| 台账一致性 | @@D4@@/15 |
| 交付诚实性 | @@D5@@/15 |
| 可复核性 | @@D6@@/15 |
各维理由：真实视觉审查 @@D0@@ —— 看了三态那一组并把「分不出」变成数，但没有新位点、也没重捕（帧与 R292 同一批）；判据有效性 @@D1@@ —— 新增的是只印不判的跨度读数 + 一条会红的对象闸门，地板仍欠（来源未成立）；假绿防御 @@D2@@ —— 本轮的价值主要在这一维：恒真的自比断言与带符号量当增量两种坏法都被抓出来，且系统参照臂是被闸门判死而不是我自己觉得不行；产品面推进 @@D3@@ —— 0 文件，动效连续第五轮没动，按实记；台账一致性 @@D4@@ —— 五本 + 305 追记（两个跨度）+ 新开 342；交付诚实性 @@D5@@ —— 公开一次失败的探针设计与它留下的假数（「系统台阶 亮 0「那种格式像结论的读数）；可复核性 @@D6@@ —— 判据、预检、四件套、电池（颗数与名单同源）都能重跑。合计 **@@SUM@@**/105；曲线仪器派生读 **@@DERIVED@@**，低于 90 ⇒ 本轮按目标规矩不算达标。

"""

DEC_NEW = u"""**D-274（R293）：造一条「参照系」判据之前，先证明这条通道画得出参照系自己；否则它给出的数越是像结论越危险。** 理由：305 欠的是「按下这一档该比悬停多走多少」的来源，第一条路是拿 AppKit 自己的按钮当锚（用户的标准就是对标系统原生能力）。把系统 `NSButton` 的常态/按下态走 `cacheDisplay` 抽成位图、喂同一把 `pillReading`，得到「系统台阶 亮 0／暗 23「——看着正好是能进台账的结论。真相是这条通道**不画窗口底**：两档的 `background` 都读成 0，于是所有台阶都是拿黑底当参照，亮档那颗甚至按下态第二层像素=0（对象闸门当场红）。处置：整条探针撤掉，改开 342（系统控件必须走夹具窗口那条画真底的通道，做法是给它加一张夹具），并把这条规矩写死：**任何」参照系「判据上岗前，必须先有一条会红的闸门证明参照系自己存在**（底 ≥0 且第二层像素 >100 这种形状），否则它输出的每个数都是零的幻觉。同族：R100（会打印的读数要有形状分隔、缺席打「无」不打空串）、R121（整体读数为 0 不证明」是通道不是产品「，要按符号拆开）、R140（空对账：先看分母是不是 0）。本轮另两种坏法一起记：① 通道一致性断言比的是同一次调用的两个别名 ⇒ 恒真；② `step` 是带符号量，把两态相减当增量会把 27 报成 −27。

"""

CHG_NEW = u"""### Improved（R293 / 第 292 轮 / Round 290 · 按下档的跨度读数与系统参照臂的死法）

`UICaptureTests/testPressRungIsOrderedAboveTheHoverRung` 里新增一条**只印不判**的 `PRESS_LADDER_SPAN`：按下离空闲走多少灰阶、离悬停走多少灰阶 —— 现读亮 27／@@LH@@、暗 @@DI@@／@@DH@@（@@SPAN_L@@）。这一格把 R262 那句「亮档 hover 与 press 肉眼分不出」从形容词变成数（@@LH@@ 灰阶），也把 305 真正要判的对象钉清楚：是**离悬停的增量**，不是离空闲的总量。为它试过一条系统参照臂（AppKit 按钮走 `cacheDisplay`），本机现读两档底都=0 ⇒ 台阶全是拿黑底当参照，对象闸门在亮档红（按下态第二层像素=0）⇒ 探针撤掉，另开 342 走夹具窗口重做。本轮**没有产品改动**：地板的来源未成立之前抬 alpha 就是把「我觉得不够明显」写成契约。四件套 @@RV@@；@@BATT@@；预检 tables=@@TBL@@ covered=@@COV@@ bad=0；CI：@@CI1@@／@@CI2@@／@@CI3@@（只登记不轮询）。

"""

NOTE305 = (u"  追记（R293）：这一单要的数第一次进盘 —— `PRESS_LADDER_SPAN` 现读按下**离空闲** 亮 27／暗 @@DI@@ 灰阶、"
           u"按下**离悬停** 亮 @@LH@@／暗 @@DH@@ 灰阶（@@SPAN_L@@）。305 要判的是后者：手指落下时人已经在悬停态，"
           u"总量不是证据。地板仍**没有来源**：想拿系统控件当锚，第一次尝试（`cacheDisplay` 抽位图）被自己的对象闸门判死 —— "
           u"两档的底都读成 0（这条通道不画窗口底），于是「系统台阶 亮 0「是零的幻觉而不是系统不动。"
           u"⇒ 本单继续开着，前置换成新开 342；本轮不抬 alpha（没锚的抬就是拍脑袋，D-274）。")

BACK_342 = (u"**342. 系统参照臂要走画真底的通道重做：`cacheDisplay` 抽出来的位图两档底都读 0，"
            u"所以它给出的「系统按下台阶 亮 0／暗 23」全部是拿黑底当参照（R293 现读 + 对象闸门在亮档红：按下态第二层像素=0）**："
            u"305 的地板缺的就是一个非自己的锚，而用户标准本来就是「对标系统原生能力」。做法：① 给系统控件加一张**夹具**"
            u"（和 `row-favorite-*` 同一条渲染路径：窗口画真底、探针框同尺寸），常态/按下态各一张；"
            u"② 上岗前先加一条会红的闸门证明参照系自己存在（底 ≥0 且第二层像素 >100，两档各自验），"
            u"没这条闸门就不许打印任何「系统台阶」（D-274）；③ 参照成立之后，地板按「我们 ≥ 系统的某个分数」写，"
            u"两机各读一次才升硬门（D-232/R147 的规矩，别在本机当场定）；④ 配一把刀：把系统夹具换成我们自己的控件 ⇒ "
            u"参照臂必须红在「底不是真底」或「两臂同物「，不能安静通过。做完之前 305 不许结案。")


def append_into_item(text, num, extra):
    lines = text.splitlines(True)
    start = None
    for i, l in enumerate(lines):
        if l.startswith("**" + num + ". "):
            if start is not None:
                die("BACKLOG 里 " + num + " 出现两次 ⇒ 锚点不唯一")
            start = i
    if start is None:
        die("BACKLOG 找不到 " + num + " 那一单")
    end = len(lines)
    for j in range(start + 1, len(lines)):
        if re.match(r"^\*\*\d{3}\. ", lines[j]):
            end = j
            break
    while end > start and not lines[end - 1].strip():
        end -= 1
    head = u"".join(lines[:end])
    if head and not head.endswith(u"\n"):
        head += u"\n"
    if not extra.startswith(u"  "):
        die("追记行必须以两空格缩进开头")
    return head + extra + u"\n" + u"".join(lines[end:])


STATE_NEW = u"""## R293 状态（第 292 轮 / Round 290 · @@DATE@@）
最后更新：2026-10-22（本地 · R293 / 第 292 轮 / Round 290）：**按下档第一次有「离空闲／离悬停」两个跨度读数；系统参照臂被自己的对象闸门判死并撤掉**（U-959…U-961 · D-274 · 新开 342 · 产品 0 文件 · 七维合计 @@SUM@@/105，曲线派生 @@DERIVED@@ —— 低于 90，本轮不算达标）

**本轮落地**：`UICaptureHarness.swift` 的梯子那一格里新增 `PRESS_LADDER_SPAN`（只印不判）：@@SPAN_L@@；@@SPAN_D@@。系统参照臂（`cacheDisplay` 抽系统按钮）本机现读两档底都=0 ⇒ 撤探针，另开 342；两种坏法自曝（恒真的自比断言、带符号量当增量）→ D-274。判据卷现读 Executed @@ROLL@@ / failures=@@FAILS@@；@@PROOF_L@@；预检 tables=@@TBL@@ covered=@@COV@@ bad=0；四件套 @@RV@@；@@BATT@@。305 追记进场、地板仍不定。

**下一轮（R294 / 第 293 轮 / Round 291）的 ⓪**：
⓪ 读 CI：@@CI1@@、@@CI2@@、@@CI3@@ 加本两笔（只登记不轮询，R140）。要验的是 R292 那笔修完之后 **STEP[15]/STEP[17] 那三跑同形红是否消失**（红话「行带里只数到 2 个墨簇」不该再出现）；若仍在，回到单位这一层继续查，不许改成 skip。
① **342 → 305**：给系统控件加夹具（画真底那条路），先让「参照系存在」的闸门绿，再谈台阶地板；两机各读一次才升硬门。
② 动效过程（连续五轮 0 文件，垫底那一维）：314 热图那圈描边的语义、291 墨轴。
③ 341 剩下的半（`ci_capture_gate.py` 的 `skipped=` 是 CI 契约行，改名要连 workflow 与它的断言一起动）、339、312 具名出口（欠第十六轮，本机 3.000 不许降，D-251）、333、335、334、310、338 的另一半、328、323、322、317、304。
④ 用户闸门 220 路 A / 228② / 265。

"""

for i, nm in enumerate("D0 D1 D2 D3 D4 D5 D6".split()):
    ITER_NEW = ITER_NEW.replace("@@" + nm + "@@", str(SCORES[i]))
for n in ("UI_NEW", "ITER_NEW", "DEC_NEW", "CHG_NEW", "STATE_NEW"):
    globals()[n] = render(globals()[n])
NOTE305 = render(NOTE305)
BACK_342 = render(BACK_342)

ui_p = B["AGENT_UI_AUDIT.md"]
ui_old = rd(ui_p)
if u"## 第 292 轮" in ui_old:
    die(u"UI_AUDIT 已有第 292 轮 ⇒ 不幂等")
anchor = u"## 第 291 轮"
if ui_old.count(anchor) != 1:
    die("UI_AUDIT 锚点命中 %d 次" % ui_old.count(anchor))
ui_new = ui_old.replace(anchor, UI_NEW + anchor, 1)

it_p = B["AGENT_VISUAL_ITERATION.md"]
it_old = rd(it_p)
if re.search(u"^## Round 290 · ", it_old, re.M):
    die(u"ITERATION 已有 Round 290 ⇒ 不幂等")
it_new = it_old.rstrip("\n") + u"\n\n" + ITER_NEW

dc_p = B["AGENT_DECISIONS.md"]
dc_old = rd(dc_p)
if u"D-274" in dc_old or u"D-273" not in dc_old:
    die(u"D 号不对（D-273 应在盘上、D-274 不该在）")
dc_new = dc_old.rstrip("\n") + u"\n\n" + DEC_NEW

cg_p = B["CHANGELOG.md"]
cg_old = rd(cg_p)
cg_new = cg_old.replace(u"## [Unreleased]\n", u"## [Unreleased]\n\n" + CHG_NEW, 1)

bk_p = B["AGENT_BACKLOG.md"]
bk_old = rd(bk_p)
last_no = re.findall(r"^\*\*(\d{3})\. ", bk_old, re.M)
if last_no[-1] != "341":
    die(u"BACKLOG 最后一单不是 341（现读 " + str(last_no[-3:]) + u"）")
if len(set(last_no)) != len(last_no):
    die(u"BACKLOG 单号有重复：" + str([n for n, c in Counter(last_no).items() if c > 1]))
bk_new = append_into_item(bk_old, "305", NOTE305)
bk_new = bk_new.rstrip(u"\n") + u"\n\n" + BACK_342 + u"\n"

st_p = B["AGENT_STATE.md"]
st_old = rd(st_p)
if u"## R292 状态" not in st_old:
    die(u"STATE 找不到 R292 锚点")
st_new = st_old.replace(u"## R292 状态", STATE_NEW + u"## R292 状态", 1)
if u"U-961" not in st_new or u"U-961" not in ui_new or u"\n**342. " not in bk_new:
    die(u"STATE／UI_AUDIT/BACKLOG 没带上 U-961 或 342 ⇒ 交账的半截丢了")


def must_preserve(old, new, name, allow=0):
    cn = Counter(new.splitlines())
    lost = [l for l, c in Counter(old.splitlines()).items() if cn[l] < c]
    if len(lost) > allow:
        die(name + u" 弄丢 " + str(len(lost)) + u" 行（只允许 " + str(allow) + u" 行）：" + u" | ".join(lost[:2])[:160])


for o, n, name in ((ui_old, ui_new, "UI"), (cg_old, cg_new, "CHANGELOG"), (bk_old, bk_new, "BACKLOG"),
                   (st_old, st_new, "STATE"), (it_old, it_new, "ITERATION"), (dc_old, dc_new, "DECISIONS")):
    must_preserve(o, n, name)

ids = [int(x) for x in re.findall(u"- \\*\\*U-(\\d+)", UI_NEW)]
if ids != [959, 960, 961]:
    die(u"U 号不连续或顺序不对：" + str(ids))
rows = [l for l in ITER_NEW.splitlines() if re.match(r"\| .* \| \d+/15 \|$", l)]
sc = [int(re.search(r"\| (\d+)/15 \|", l).group(1)) for l in rows]
if len(sc) != 7 or sum(sc) != sum(SCORES):
    die(u"七维表形状或合计不对：" + str(sc))
tail = re.findall(u"^## Round (\\d+) · ", it_new, re.M)
if int(tail[-1]) != 290:
    die(u"ITERATION 文件尾轮次必须是本轮（现读 " + str(tail[-3:]) + u"）")
if bk_new.count(u"追记（R293）") != 1 or bk_new.count(u"\n**342. ") != 1:
    die(u"305 追记或 342 没落上")
if dc_new.count(u"\n**D-274") != 1 or u"## R293 状态" not in st_new:
    die(u"D-274 或 STATE 轮换没落上")

for p, txt in ((ui_p, ui_new), (it_p, it_new), (dc_p, dc_new), (bk_p, bk_new), (cg_p, cg_new), (st_p, st_new)):
    with io.open(p, "w", encoding="utf-8") as h:
        h.write(txt)

out, rc = sh([sys.executable, os.path.join(HERE, "report_cells_r258.py"), "headline"])
if rc != 0:
    die(u"FINAL_REPORT headline 刷新失败：" + out[-300:])
ran2, skip2, names2 = battery()
if (ran2, skip2) != (pre_ran, pre_skip) or names2 != pre_names:
    die(u"写盘前后电池不一致（" + pre_ran + u"/" + pre_skip + u"/" + str(pre_names) + u" → "
        + ran2 + u"/" + skip2 + u"/" + str(names2) + u"）")

msg1 = (u"R293 代码半（第 292 轮 / Round 290）：按下档第一次有「离空闲／离悬停」两个跨度读数（PRESS_LADDER_SPAN，只印不判）；"
        u"系统参照臂在本机被判不成立并撤掉 —— cacheDisplay 抽出来的位图两档底都读 0 ⇒ 台阶全是拿黑底当参照（D-274）\n\n"
        u"现读：" + SPAN_L + u"；" + SPAN_D + u"。对象闸门在亮档当场红（按下态第二层像素=0）才把这条探针撤干净，"
        u"没留「只印不判」的活口；另开 342 走夹具窗口重做。两种坏法一起认：通道一致性断言比的是同一次调用的两个别名（恒真）、"
        u"带符号的 step 相减当增量会把 27 报成 -27。判据卷 Executed " + str(ROLL) + u" / failures=" + str(FAILS)
        + u"；四件套 " + rv.group(0).strip() + u"；预检 " + cover.group(0) + u"。")
msg2 = (u"R293 账半（第 292 轮 / Round 290）：五本台账 + STATE 轮换 + FINAL_REPORT headline —— 数字全由 round_r293.py 现读："
        u"两条 SPAN（亮 27／" + LH + u"、暗 " + DI + u"／" + DH + u"）、梯子 PROOF 原文、预检 " + cover.group(0)
        + u"、四件套 " + rv.group(0).strip() + u"、电池 Ran " + ran2 + u" / skipped=" + skip2
        + u"（名单 " + str(names2) + u" 条，同源才准写）。U-959…U-961／D-274；305 追记（地板仍无来源，前置换成 342）；"
        u"新开 342（系统参照臂走画真底的通道重做，上岗前先让「参照系存在」的闸门绿）。产品 0 文件 ⇒ 帧基线与 sources 格不动。"
        u"七维合计 " + str(sum(SCORES)) + u"/105、曲线派生 " + DERIVED + u" ⇒ 不算达标，R294 先做 342 再回 305。")

for m, files in ((msg1, ["ClipboardHistory/Tests/ClipboardHistoryAppTests/UICaptureHarness.swift"]),
                 (msg2, ["AGENT_UI_AUDIT.md", "AGENT_VISUAL_ITERATION.md", "AGENT_DECISIONS.md", "AGENT_BACKLOG.md",
                         "CHANGELOG.md", "AGENT_STATE.md", "AGENT_FINAL_REPORT.md",
                         ".scratch/motion-audit-2/round_r293.py"])):
    if "`" in m or m.count("\n\n") > 1:
        die(u"提交正文不许带反引号，且只准一个标题空行")
    sh(["git", "add"] + files)
    pr = subprocess.run(["git", "commit", "-q", "-m", m], cwd=ROOT, capture_output=True, text=True)
    if pr.returncode != 0:
        die(u"提交失败：" + (pr.stdout + pr.stderr)[-400:])
    print(u"COMMITTED " + m[:48])
pr = subprocess.run(["git", "push", "-q", "origin", "main"], cwd=ROOT, capture_output=True, text=True)
print("PUSH_RC=%d %s" % (pr.returncode, (pr.stdout + pr.stderr)[:200]))
print(u"ROUND_R293 OK batt=Ran " + ran2 + u" (skipped=" + skip2 + u", 名单=" + str(names2) + u")"
      + u" span=light " + LI + u"/" + LH + u" dark " + DI + u"/" + DH + u" prod=0 U=959..961 D=274 new=342")
