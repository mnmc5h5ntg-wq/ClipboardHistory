#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R279 台账生成器（第 278 轮 / Round 276）：数字全现读，缺格就拒写。

根由 `__file__` 推（D-260 / D-265：本轮新开的 334 就是在数"还剩多少支写死本机根"，
生成器自己不许成为其中一支）。
"""
import io
import json
import os
import re
import subprocess
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
B = {n: os.path.join(ROOT, n) for n in ("AGENT_UI_AUDIT.md", "AGENT_VISUAL_ITERATION.md", "AGENT_DECISIONS.md",
                                        "AGENT_BACKLOG.md", "CHANGELOG.md", "AGENT_STATE.md")}
RUN_DIR = "/tmp/r279_verify"
RUN_LOG = "/tmp/r279_verify_run.log"
# 看图腿的两张对象（本轮 0 产品文件 ⇒ 押在 R273 结案那颗夹具上：324 钉住的两张 recording 帧）
EYE = ["settings-shortcuts-recording-720x540-light.png",
       "settings-shortcuts-recording-720x540-dark.png"]
EYE_PROSE = ("两张都还在画「录制中」那一态：第三行录制器显示占位文案「请输入快捷键」，另两行是 ⌃⌥V／⌃⌥C，"
             "说明段与录制器同基线、没有互相吃掉；暗档侧栏五枚图标是清晰的白墨（R121 那笔 .monochrome 的效果仍在），"
             "亮档同五枚明显更淡 —— 那个淡法早被 172 判成离屏通道限制，本轮不改判也不重复结案。"
             "两帧与基线逐摘要相同（changed=0）⇒ R273 钉住的相位没漂。本轮改动全在脚本侧，画面没有新位点可判，"
             "所以这一维按实记低分，不编一句「看了两张发现更好」。")


def die(m):
    sys.stderr.write("LEDGERS_R279 REFUSED: " + m + "\n")
    raise SystemExit(2)


def rd(p):
    with io.open(p, encoding="utf-8", errors="replace") as h:
        return h.read()


def sh(cmd, cwd=None):
    env = dict(os.environ)
    env["PYTHONUTF8"] = "1"
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env.pop("SDKROOT", None)
    pr = subprocess.run(cmd, cwd=(cwd or ROOT), env=env, capture_output=True, text=True)
    return (pr.stdout or "") + (pr.stderr or ""), pr.returncode


# ---- ① 四件套必须整条绿，且新闸门这一次是**真跑过**的（不是只在合成读数上绿）----
if not os.path.isdir(RUN_DIR):
    die("四件套目录不在：" + RUN_DIR)
runlog = rd(RUN_LOG)
rv = re.search(r"ROUND_VERIFY build_warnings=(\S+) swift_executed=(\S+) swift_skipped=(\S+) swift_failures=(\S+) "
               r"frames=(\S+) baseline_compared=(\S+) baseline_changed=(\S+) baseline_missing=(\S+) dmg=(\S+) "
               r"installed_version=(\S+)", runlog)
if not rv:
    die("读不到 ROUND_VERIFY 那一行 ⇒ 四件套没跑完（不许把缺格写成通过）\n" + runlog[-400:])
if "FRAME_GATE_RED" in runlog:
    die("新闸门本轮就是红的 ⇒ 先按 HOWTO update 基线并重跑，再来写账")
gate = re.search(r"FRAME_GATE_PASS changed=(\d+) compared=(\d+) missing=(\d+)", runlog)
if not gate:
    die("四件套里没有 FRAME_GATE_PASS 那一行 ⇒ 这一轮的结案没有'门真跑过'这个证人")
W, T, S, F, FR, CM, BC, MS, DMG, VER = rv.groups()
if W != "0" or F != "0" or DMG != "ok":
    die("四件套有红：告警=%s 失败=%s dmg=%s" % (W, F, DMG))
if gate.group(1) != BC or gate.group(2) != CM:
    die("闸门行的读数与 ROUND_VERIFY 不一致（gate=%s vs verify changed=%s compared=%s）"
        % (gate.group(0), BC, CM))
n_frames = len([f for f in os.listdir(os.path.join(RUN_DIR, "frames")) if f.endswith(".png")])
if n_frames != int(FR):
    die("盘上帧数 %d 与 ROUND_VERIFY frames=%s 不等" % (n_frames, FR))
for f in EYE:
    if not os.path.exists(os.path.join(RUN_DIR, "frames", f)):
        die("看图腿的对象不在盘上：" + f + " ⇒ 这一腿要记 NOT-RUN，不许编看过的东西")

# ---- ② 两把刀现跑一遍，CAUGHT 必须等于刀数 ----
ktxt, krc = sh([sys.executable, os.path.join(HERE, "mutate_r279.py")])
km = re.search(r"R279_MUTATE 刀=(\d+) CAUGHT=(\d+) ESCAPED=(\d+) NOT_RUN=(\d+) RESTORE_CLEAN=(\S+)", ktxt)
if not km or krc != 0:
    die("本轮变异表不干净：\n" + ktxt[-400:])
KN, KC, KE, KNR, KREST = km.groups()
if KC != KN or KREST != "yes":
    die("刀没全 CAUGHT 或还原不干净：CAUGHT=%s/%s RESTORE=%s" % (KC, KN, KREST))

# ---- ③ 预检：新表必须已登记（D-248），缺口是读数不是印象 ----
ptxt, _ = sh([sys.executable, os.path.join(HERE, "mutate_needle_precheck.py")])
cover = re.search(r"NEEDLE_PRECHECK tables=(\d+) covered=(\d+) arms=(\d+) bad=(\d+)", ptxt)
roster = re.search(r"TABLE_ROSTER registered=(\d+) unregistered_with_arms=(\d+) hidden_arms=(\d+)", ptxt)
total = re.search(r"ARM_TOTAL files=(\d+) arms=(\d+) dupes=(\d+) repeats=(\d+)", ptxt)
if not (cover and roster and total) or cover.group(4) != "0" or total.group(3) != "0":
    die("预检读数不全或有坏：\n" + ptxt[-300:])
if "mutate_r279" not in ptxt:
    die("新表 mutate_r279 没进预检名册（D-248：登记与覆盖是两件事，先要登记）")

# ---- ④ 334 的数：`.scratch` 里还有多少支写死本机根（注释剥掉再判，D-265 的同一条规矩）----
PAT = re.compile(r'^\s*(?:ROOT|REPO)\s*=\s*["\'](/Users/[^"\']+)', re.M)
scanned = 0
hard = []
for p in sorted(os.listdir(HERE)):
    if not p.endswith(".py"):
        continue
    scanned += 1
    src = "\n".join(l.split("#", 1)[0] for l in rd(os.path.join(HERE, p)).splitlines())
    if PAT.search(src):
        hard.append(p)
if not hard:
    die("一把都没扫出来 ⇒ 这把尺要么指错了对象，要么 334 已被做完（那要改判而不是写个 0）")
if "ledgers_r279.py" in hard or "mutate_r279.py" in hard:
    die("本轮新写的两支自己就写死本机根 ⇒ 334 没意义")

# ---- ⑤ CI 成对号现读（只登记不轮询，R140）----
ctxt, _ = sh(["gh", "run", "list", "--limit", "12", "--json", "databaseId,headSha,status,conclusion"])
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

SCORES = [7, 14, 15, 2, 15, 15, 15]
if len(SCORES) != 7:
    die("七维必须 7 行")
V = {
    "@@DATE@@": "2026-10-21",
    "@@W@@": W, "@@T@@": T, "@@S@@": S, "@@F@@": F, "@@FR@@": FR, "@@CM@@": CM, "@@BC@@": BC, "@@MS@@": MS,
    "@@DMG@@": DMG, "@@VER@@": VER,
    "@@KN@@": KN, "@@KC@@": KC, "@@KREST@@": KREST,
    "@@TBL@@": cover.group(1), "@@COV@@": cover.group(2), "@@PARMS@@": cover.group(3),
    "@@ARMS@@": total.group(2), "@@GAPT@@": roster.group(2), "@@GAPA@@": roster.group(3),
    "@@SCAN@@": str(scanned), "@@HARD@@": str(len(hard)), "@@HARDN@@": ",".join(hard[:5]),
    "@@BATT@@": "脚本电池 Ran " + pre_ran + " tests / OK (skipped=" + pre_skip + ")",
    "@@SUM@@": str(sum(SCORES)),
    "@@EYE@@": EYE_PROSE,
    "@@EYEN@@": "、".join(os.path.splitext(f)[0] for f in EYE),
    "@@CI1@@": pair("bfb8acf"), "@@CI2@@": pair("41e5ce0"),
    # ⓪ 里那句"runner 上电池应该跑多少颗"不许我编：只把本机现读值带过去，差额交回 331 那张名册。
    "@@BATTRUN@@": "本机现读 " + pre_ran + " 颗（runner 若少收，差额要由 331 那两张按机器键的名册解释，不许先假设两边同数）",
}

UI_NEW = """## 第 278 轮（R279 / 第 278 轮 / Round 276 · @@DATE@@）：`changed` 从读数变闸门 —— 退出码丢掉的那道门等于不存在（U-924…U-926 / D-263…D-265 · 333 本机半结案 · 产品 0 文件）

本轮次对照：与 R276（自评 80，门只扫直接 import）相比，本轮收的是 R277/R278 只落台账、没落判据的那笔账：**333**。第 276、277 轮（R277/R278）是 331 两次尝试的回退记账与 333 的机制更正，没有独立小节 ⇒ 本轮标题按轮次映射写 278，缺口留在这里说明，不冒充连续。

- **U-924：333 的本机半结案，证人是四件套真跑过的那一行** —— `scripts/round_verify.sh` 第 [3/4] 步以前把 `frame_baseline.py compare` 的**退出码丢掉**，只把 `FRAME_BASELINE_CHANGED=` 抄进 `ROUND_VERIFY … baseline_changed=`：R252/R253 那两轮能发现 changed=1/2，是因为我恰好在读那个数。现在 changed≠0 直接 `exit 1`，且红话里只有一条正路（`frame_baseline.py update` 之后重跑），不留 `|| true`、不留环境变量后门（豁免一旦能被环境变量关掉就会腐烂成噪声）。三态各有合成读数：changed=3 ⇒ 红、changed=0 ⇒ 绿并仍把 compared/missing 一起打出来、**读不到（NOT-RUN）⇒ 也红**（R99：缺席不许比通过更宽松）。本轮同一笔四件套现读 @@BATT@@、`FRAME_GATE_PASS changed=@@BC@@ compared=@@CM@@ missing=@@MS@@`，即这道门不是只在合成样本上绿过。CI：@@CI1@@、@@CI2@@ 交接时未读 ⇒ 只登记号不轮询（R140），本轮不引用任何 runner 结论。
- **U-925：新守卫第一次红，是红在自己的散文上** —— 门里那行注释写着「故意不留 `|| true`」，而我的证人格用的是**整块子串搜** ⇒ `Ran 6 / failures=1`，一道设计正确的判据恒红。修法按 R76/R100 那条老规矩：判"用没用"要判它出现在**可执行行**里（剥掉行首 `#` 与行尾注释后再搜），并同时留一条正对照 —— 若那块注释哪天被删，`'|| true' in block` 就红，提醒我这把尺剥的已经不是当初那一处。这把刀是 M835（把 `code_lines` 弄瞎 ⇒ 必须红在这一格），与拆门刀 M834（`exit 1` 换成 `true` ⇒ 必须红在"changed=3 要红"那一格）各钉一条轴（D-244）：M834 钉产品轴（门会不会拦），M835 钉尺轴（守卫是不是只在读散文）。现读 @@KN@@ 把全 CAUGHT、RESTORE_CLEAN=@@KREST@@。
- **U-926：D-260 的适用范围划错了一档，缺口是数出来的** —— 闭包门覆盖的是"电池 import 的工具"，而**台账生成器不被 import**（它由人跑）。现读 `.scratch/motion-audit-2/` 下 @@SCAN@@ 支 python，剥注释后仍有 @@HARD@@ 支把仓库根写成 `/Users/wangziyi/…` 字面量（点名 @@HARDN@@…）。⇒ 新开 **334**：按"谁会被别人/别的机器跑"重新划名单，而不是按"谁被 import"。本轮新写的两支（`ledgers_r279.py`、`mutate_r279.py`）自己按 `__file__` 推根，并且生成器里有一条"一把都没扫出来就拒写"的守卫 —— 一把只能读出 0 的尺不配登记结案。

眼睛腿：RUN —— 现读 @@FR@@ 张帧在 @@EYEN@@ 上按 EYE 名单逐张看过。@@EYE@@
读数腿：RUN —— `ROUND_VERIFY build_warnings=@@W@@ swift_executed=@@T@@ swift_skipped=@@S@@ swift_failures=@@F@@ frames=@@FR@@ baseline_compared=@@CM@@ baseline_changed=@@BC@@ baseline_missing=@@MS@@ dmg=@@DMG@@ installed_version=@@VER@@`；`FRAME_GATE_PASS` 与该行同笔现读且两数互相对账；变异 @@KC@@/@@KN@@ CAUGHT；@@BATT@@；预检 tables=@@TBL@@ covered=@@COV@@ arms=@@PARMS@@ bad=0、ARM_TOTAL arms=@@ARMS@@ dupes=0；334 的数 @@HARD@@/@@SCAN@@。
产品腿：0 文件（只动 `scripts/round_verify.sh` + 新增一格证人卷 + 两张表 ⇒ sources 格按规矩不动，由电池里那条与 git 对账的守卫签）。
未做（逐条）：① **333 的 CI 半**（runner 上 changed==compared 的按机器具名出口 + "真通道差异不误红"那把刀）；② **312 的具名出口（欠第八轮）**；③ 331（观测式名册，两版已回退、正解形状已定）、332、330、328、323、322、317、314-316；④ 310 的 @@GAPT@@ 张表 / @@GAPA@@ 把刀 + 新增的 334；⑤ 305、299、301、307、297/298/300、304、291 三位；⑥ 用户闸门 220 路 A / 228② / 265。

"""

ITER_NEW = """## Round 276 · `changed` 从读数变闸门：丢掉退出码的门等于不存在，而新守卫第一次红在自己的散文上（R279 / 第 278 轮）/ D-263…D-265 · 333 本机半结案 · 产品 0 文件

本轮次对照：与 R276（自评 80）相比，本轮把 R277/R278 只用文字记下、没有任何东西会替它承重的 333，落成本机那道会红的门 + 两把刀。
看图腿：RUN —— @@FR@@ 张帧在盘上（本轮 0 产品改动，基线 changed=@@BC@@），按名单看过 @@EYEN@@。@@EYE@@
读数腿：RUN —— `FRAME_GATE_PASS changed=@@BC@@ compared=@@CM@@ missing=@@MS@@` 与 `ROUND_VERIFY …` 同笔现读、两数互相对账；合成三态（3/0/NOT-RUN）各自跑过 bash；变异 @@KC@@/@@KN@@ 全 CAUGHT、RESTORE_CLEAN=@@KREST@@；@@BATT@@；预检 tables=@@TBL@@ covered=@@COV@@ arms=@@PARMS@@ bad=0；334 的数现读 @@HARD@@/@@SCAN@@。
七维度自评：
| 维度 | 分/满分 |
| 真实视觉审查 | @@D0@@/15 |
| 判据有效性 | @@D1@@/15 |
| 假绿防御 | @@D2@@/15 |
| 产品面推进 | @@D3@@/15 |
| 台账一致性 | @@D4@@/15 |
| 交付诚实性 | @@D5@@/15 |
| 可复核性 | @@D6@@/15 |
各维理由：真实视觉审查 @@D0@@ —— 0 产品文件，看的是 R273 钉住的那颗夹具在闸门之下画面对不对，本轮没有新位点可判；判据有效性 @@D1@@ —— 门有合成三态证人 + 本轮四件套真跑过的一行，扣一分是 CI 侧那半还没接（333 剩余）；假绿防御 @@D2@@ —— 拆门刀与瞎尺刀各钉一条轴，且"读不到 changed"按红不按绿；产品面推进 @@D3@@ —— 0 文件，但改的是"改界面不 update 基线"这条纪律的可执行性；台账一致性 @@D4@@ —— 上一轮没落 UI 小节这件事在标题段明写而不是冒充连续；交付诚实性 @@D5@@ —— 自己的守卫恒红在散文上、以及 D-260 名单划错一档这两笔都当场记账（M835 / 新开 334）；可复核性 @@D6@@ —— 门在 `scripts/`、证人在 `scripts/tests/`、两把刀与日志都在盘上原地可重跑。合计 **@@SUM@@**/105。

"""

DEC_NEW = """**D-263（R279）：读 CI 时「按步骤名过滤」不等于拿到执行输出 —— `--log` 的回显段里含 GitHub 打印的脚本正文，任何"某行没打印 / 打印了几次"的判断必须先切到 `##[endgroup]` 之后。** 理由：R278 我先按步骤名过滤，同一步里既看到 `FRAME_BASELINE_SKIPPED=runner-capture-unavailable` 又看到 `CHANGED=170` 却 exit 0，于是写成"硬门在 runner 上等于不存在"——那句话是假的，后来按执行段重数，SKIPPED 出现 0 次。这是 R274 那笔"读 CI 要按步骤名过滤"的下一步：过滤之后还要分回显与执行。本条正文由 BACKLOG 333 的追记（AGent_BACKLOG.md 第 6948 行那族）指认，此前只被引用、没有正文（台账里被引用的 D 号必须有正文，R94 那条）。

**D-264（R279）：读数不是闸门 —— 任何把退出码丢掉、只把数抄进摘要的行，等于那条纪律不存在；新增闸门要同时配"门被拆"那把刀，并且红必须排在交付动作之前。** 理由：`round_verify.sh` 的 [3/4] 步一直打 `baseline_changed=`，`compare` 的非零退出码在子 shell 里被丢掉；CI 那一步用 `check`，按设计只在 missing 时红。两侧合起来，"改了界面没在同一笔 update 基线"从来只靠人记得看那个数。本轮把它改成 `exit 1` 并排在 [4/4]（dmg/换装）之前，红话只给一条正路、不留 `|| true` 也不留环境变量后门；同一笔配 M834（`exit 1`→`true` 必须让"changed=3 要红"那一格红），因为"我加了一道门"这句话在没有拆门刀之前和"门存在"同形。与 D-038（会红的必须是单调量）、R99（缺席不许比通过宽松）、R70（把门变成被量的对象）同族。

**D-265（R279）：「谁能把这台机器当唯一机器」的名单要按**运行对象**划，不是按 import 关系划 —— 现读 `.scratch/motion-audit-2/` 下 @@SCAN@@ 支 python，剥注释后仍有 @@HARD@@ 支把仓库根写成 `/Users/wangziyi/…` 字面量。** 理由：D-260/D-262 的闭包门只覆盖"电池 import 的工具"，而台账生成器与绝大多数一次性变异/清账表是被**人或下一步脚本直接跑**的，不被 import ⇒ 在闸门眼里它们不存在。这一档缺口在 R274 那笔里被我写成"已修完"的口气，实际只修了 2 支。新开 334 按"谁会被别人/别的机器跑"重列名单；本轮新写的两支自己按 `__file__` 推根，且生成器有一条"一把都没扫出来 ⇒ 拒写"的守卫：一把只能读出 0 的尺不配登记结案（R100 那条"名单为空=红"）。

"""

CHG_NEW = """### Fixed（R279 / 第 278 轮 / Round 276 · `changed` 从读数变闸门）

`scripts/round_verify.sh` 第 [3/4] 步：`frame_baseline.py compare` 的退出码以前被丢掉，只把 `FRAME_BASELINE_CHANGED=` 抄进 `ROUND_VERIFY` 摘要 ⇒ "改了界面没在同一笔 update 基线"这条纪律在任何一侧都不是红。现在 changed≠0 直接 `exit 1`（排在 dmg/换装之前），红话里只给一条正路（`frame_baseline.py update` 之后重跑），不留 `|| true`、不留环境变量后门；`changed` 读不到（NOT-RUN）同样拦。新增证人卷 `scripts/tests/test_round_verify_frame_gate.py`（6 格：接线 + 顺序 + 合成三态 3/0/NOT-RUN + 空名单仍印 missing），两把刀 `mutate_r279.py` M834（拆门 = 产品轴）／M835（守卫不剥注释 = 尺轴）现读 @@KC@@/@@KN@@ 全 CAUGHT、RESTORE_CLEAN=@@KREST@@，并已登记进预检名册（tables=@@TBL@@ covered=@@COV@@ bad=0）。**333 的本机半结案**，CI 半（runner 上 changed==compared 的按机器具名出口）留在原单。本轮另两处自曝入账：守卫第一次恒红是红在自己门里的散文上（D-263 那族的镜像，U-925）；D-260 的闭包只盖住被 import 的工具，现读 @@HARD@@/@@SCAN@@ 支脚本仍写死本机根 ⇒ 新开 334（D-265）。@@BATT@@；四件套现读 build_warnings=@@W@@ swift_executed=@@T@@ skipped=@@S@@ failures=@@F@@ frames=@@FR@@ changed=@@BC@@ missing=@@MS@@ dmg=@@DMG@@ installed=@@VER@@。CI：@@CI1@@／@@CI2@@ 交接时未读（只登记号不轮询，R140）。产品 0 文件 ⇒ sources 格不动；看图腿 RUN（@@EYEN@@）。

"""

BACK_NEW = "**334. 把「写死本机根」的名单按运行对象重列，而不是按 import 关系（R279 现读：`.scratch/motion-audit-2/` 下 @@SCAN@@ 支 python，剥注释后 @@HARD@@ 支仍有 `ROOT = \"/Users/wangziyi/…\"` 字面量，点名 @@HARDN@@…；而 D-260/D-262 的闭包门只覆盖\"电池 import 的工具\"⇒ 台账生成器与一次性清账表在闸门眼里不存在）。做法：① 先数出**会被别的机器或下一步脚本跑**的那几支（变异表、预检、台账生成器、report_cells），按名单而不是按 import 收；② 逐支改由 `__file__` 推根（照 `mutate_r279.py` 的形状）；③ 门改成读那份名单，名单为空要红、改完一支就从名单里删一行（做完一行删一行，R249）；④ 一刀证明\"写死根\"能被红抓到（把已修好的一支改回字面量 ⇒ 必须红）。不许把这单结案成\"闭包门已经绿了\"—— 它绿的是另一份名单（D-265，R279 新开）**"

STATE_NEW = """## R279 状态（第 278 轮 / Round 276 · @@DATE@@）
最后更新：2026-10-21（本地 · R279 / 第 278 轮 / Round 276）：**333 本机半结案：`changed` 从读数变闸门，退出码不再被丢掉；两把刀各钉一条轴（拆门 / 瞎尺）**（U-924…U-926 · D-263…D-265 · 产品 0 文件 · 自评 @@SUM@@/105）

**本轮落地**：`round_verify.sh` [3/4] 的帧基线门改成 changed≠0 ⇒ `exit 1`（排在 dmg/换装之前，红话只给一条正路、无 `|| true`、无环境变量后门；NOT-RUN 同样拦）+ 证人卷 `scripts/tests/test_round_verify_frame_gate.py` 6 格 + `mutate_r279.py` M834/M835（@@KC@@/@@KN@@ 全 CAUGHT、RESTORE_CLEAN=@@KREST@@，已登记进预检 tables=@@TBL@@ covered=@@COV@@ bad=0）。四件套现读 build_warnings=@@W@@ swift_executed=@@T@@ skipped=@@S@@ failures=@@F@@ frames=@@FR@@ changed=@@BC@@ missing=@@MS@@ dmg=@@DMG@@ installed=@@VER@@；@@BATT@@。两处自坏入账：守卫恒红在自己门里的散文上（剥注释后才判"用没用"，U-925）；D-260 的闭包只盖被 import 的工具 ⇒ 现读 @@HARD@@/@@SCAN@@ 支脚本仍写死本机根，新开 334（D-265）。R277/R278 两笔只落台账、没有 UI 小节，本轮标题按轮次映射写第 278 轮并把缺口明写。

**下一轮（R280 / 第 279 轮 / Round 277）的 ⓪**：
⓪ 读 CI：@@CI1@@、@@CI2@@ 加上本笔推送自动触发的那一跑（用 `gh run list --limit 3 --json databaseId,headSha,status,conclusion` 现取配对，别编号；只登记号不轮询，R140）。要验的是 **STEP[9]「Release script tests」的 failures 必须为 0**：本轮新增那 6 格证人卷里有一格会把闸门那段真跑一遍 bash，runner 上没有 `bash` 或抽不出那一段就会红 —— 那是尺的缺席不是产品。颗数与本机是否相等按 331 的名册回答，不许先假设：@@BATTRUN@@。
① **333 的 CI 半**：runner 那次捕获 COMPARED=170 CHANGED=170 ⇒ 按机器键的具名出口（`FRAME_CHANGED_CHANNEL_DIFF=runner`，计入读数、不红不静默，D-251）+ 一把"真通道差异不误红"的刀；本机这半的 M834 不能替它作证。
② **312 的具名出口（欠第八轮）**：按"纸"那一维推，本机 3.000 不许降（D-251）。
③ 331（观测式名册：按"表头行 + 结果行"配对归属 + 恒等式闸门，两版已回退）、332、330、328、323、322、317、314-316。
④ 334（@@HARD@@ 支写死本机根按运行对象重列名单 + 一把改回字面量的刀）、310 的 @@GAPT@@ 张表、309 那 6 张；305、299、301、307、297/298/300、304、291 三位。
⑤ 产品动效面连续多轮是最弱一维（本轮 0 文件）：按清账表点一个位真做动效或撤声明。
⑥ 用户闸门 220 路 A / 228② / 265。

"""


def render(s):
    for k, v in V.items():
        s = s.replace(k, v)
    if "@@" in s:
        # 失败文本要点名是哪个键没喂到 —— 只截 150 字的话，下一轮还得再猜一次（R100：有键无值）
        missing = sorted(set(re.findall(r"@@[A-Z0-9]+@@", s)))
        die("渲染后仍有未替换占位符 " + ",".join(missing) + "（V 里没有这些键）")
    return s


for i, name in enumerate("D0 D1 D2 D3 D4 D5 D6".split()):
    ITER_NEW = ITER_NEW.replace("@@" + name + "@@", str(SCORES[i]))
for n in ("UI_NEW", "ITER_NEW", "DEC_NEW", "CHG_NEW", "STATE_NEW"):
    globals()[n] = render(globals()[n])
BACK_NEW = render(BACK_NEW) + "\n"

ui_p = B["AGENT_UI_AUDIT.md"]
ui_old = rd(ui_p)
if "## 第 275 轮" not in ui_old:
    die("UI_AUDIT 找不到锚点（当前最大小节应仍是第 275 轮）")
if "## 第 278 轮" in ui_old:
    die("UI_AUDIT 已经有第 278 轮 ⇒ 生成器不幂等，先还原再重跑")
cut = ui_old.index("## 第 275 轮")
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
last_item = re.findall(r"^\*\*(\d{3})\. ", bk_old, re.M)
if not last_item or last_item[-1] != "333":
    die("BACKLOG 最后一单不是 333（现读 " + str(last_item[-3:]) + "）⇒ 追记会挂错单，334 也要重找位置")
# 333 的追记四（结案本机半）追加在该单段末尾，再追加新开 334
bk_new = bk_old.rstrip("\n") + "\n\n  追记四（R279 本机半落地）：真机制确认是 `check` 按设计只管 missing（不是吞红），而这道纪律在**本机**也没有闸门 —— `round_verify.sh` 把 `compare` 的退出码丢掉、只抄 `baseline_changed=` 进摘要。R279 把本机这半修成会红的门（changed≠0 ⇒ exit 1，排在 dmg/换装之前；NOT-RUN 同样拦），配 M834/M835 两把刀并登记进预检，6 格证人卷进电池 ⇒ **333 的本机半结案**。剩下的仍是 runner 那半：捕获整片不同（COMPARED=170 CHANGED=170）时要按机器键开具名出口（D-251），并补一把「真通道差异不误红」的刀 —— 那把刀没落地之前本单不许结案。\n\n" + BACK_NEW


def must_preserve(old, new, name):
    cn = Counter(new.splitlines())
    lost = [l for l, c in Counter(old.splitlines()).items() if cn[l] < c]
    if lost:
        die(name + " 弄丢 " + str(len(lost)) + " 行：" + " | ".join(lost[:2])[:140])


must_preserve(ui_old, ui_new, "AGENT_UI_AUDIT.md")
must_preserve(cg_old, cg_new, "CHANGELOG.md")
must_preserve(bk_old, bk_new, "AGENT_BACKLOG.md")
st_p = B["AGENT_STATE.md"]
st_old = rd(st_p)
if "## R276 状态" not in st_old:
    die("STATE 找不到 R276 锚点（现读轮换停在 " + str(re.findall(r'^## (R\\d+) 状态', st_old, re.M)[:3]) + "）")
st_new = st_old.replace("## R276 状态", STATE_NEW + "## R276 状态", 1)
must_preserve(st_old, st_new, "AGENT_STATE.md")

ids = [int(x) for x in re.findall(r"- \*\*U-(\d+)", UI_NEW)]
if ids != list(range(924, 927)):
    die("U 号不连续：" + str(ids))
if "U-924…U-926" not in UI_NEW.splitlines()[0]:
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
for d in ("D-263", "D-264", "D-265"):
    if d in dc_old:
        die(d + " 已有正文 ⇒ 本轮不该再写")
if "D-262" not in dc_old:
    die("D-262 不在盘上，号段判断失效")
if bk_new.count("\n**334. ") != 1:
    die("新开 334 没落上")
if "追记四（R279" not in bk_new:
    die("333 的结案追记没落上")
seg333 = re.search(r"^\*\*333\. .*?(?=^\*\*\d{3}\. |\Z)", bk_new, re.M | re.S)
if not seg333 or "本机半结案" not in seg333.group(0):
    die("BACKLOG 333 段里没有本轮那句结案 ⇒ 台账那句「本机半结案」没有出处")
if "D-263" not in DEC_NEW:
    die("333 追记引用的 D-263 本轮必须给出正文")
if "## R279 状态" not in st_new:
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
print("LEDGERS_R279 OK batt=Ran " + ran2 + " (skipped=" + skip2 + ") gate=FRAME_GATE_PASS changed=" + BC
      + " compared=" + CM + " missing=" + MS + " knives=" + KC + "/" + KN + " frames=" + FR
      + " hardcoded_roots=" + str(len(hard)) + "/" + str(scanned) + " U=924..926 D=263..265 new=334")
print(out.strip().splitlines()[-1])
