#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R280 台账生成器（第 279 轮 / Round 277）：数字全现读，缺格拒写。根由 __file__ 推（D-260/334）。"""
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
FRAMES = "/tmp/r279_verify/frames"


def die(m):
    sys.stderr.write("LEDGERS_R280 REFUSED: " + m + "\n")
    raise SystemExit(2)


def rd(p):
    with io.open(p, encoding="utf-8", errors="replace") as h:
        return h.read()


def sh(cmd):
    env = dict(os.environ)
    env["PYTHONUTF8"] = "1"
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env.pop("SDKROOT", None)
    pr = subprocess.run(cmd, cwd=ROOT, env=env, capture_output=True, text=True)
    return (pr.stdout or "") + (pr.stderr or ""), pr.returncode


def ran_of(text):
    m = re.findall(r"^Ran (\d+) tests?", text, re.M)
    return int(m[-1]) if m else 0


# ① 判据卷：这一轮的证人卷必须 9 颗且绿
htxt, hrc = sh([sys.executable, "-W", "ignore", "-m", "unittest", "scripts.tests.test_hover_capture_channel"])
if hrc != 0 or ran_of(htxt) != 9:
    die("悬停名册那一卷不是 9 颗绿：Ran=%s rc=%s\n%s" % (ran_of(htxt), hrc, htxt[-400:]))

# ② 两把刀现跑
ktxt, krc = sh([sys.executable, os.path.join(HERE, "mutate_r280.py")])
km = re.search(r"R280_MUTATE 刀=(\d+) CAUGHT=(\d+) ESCAPED=(\d+) NOT_RUN=(\d+) RESTORE_CLEAN=(\S+)", ktxt)
if not km or krc != 0:
    die("本轮变异表不干净：\n" + ktxt[-400:])
KN, KC, KE, KNR, KREST = km.groups()
if KC != KN or KREST != "yes":
    die("刀没全 CAUGHT 或还原不干净：CAUGHT=%s/%s RESTORE=%s" % (KC, KN, KREST))

# ③ 预检：新表要登记（D-248）
ptxt, _ = sh([sys.executable, os.path.join(HERE, "mutate_needle_precheck.py")])
cover = re.search(r"NEEDLE_PRECHECK tables=(\d+) covered=(\d+) arms=(\d+) bad=(\d+)", ptxt)
total = re.search(r"ARM_TOTAL files=(\d+) arms=(\d+) dupes=(\d+) repeats=(\d+)", ptxt)
roster = re.search(r"TABLE_ROSTER registered=(\d+) unregistered_with_arms=(\d+) hidden_arms=(\d+)", ptxt)
if not (cover and total and roster) or cover.group(4) != "0" or total.group(3) != "0":
    die("预检读数不全或有坏：\n" + ptxt[-300:])
if "mutate_r280" not in ptxt:
    die("mutate_r280 没出现在预检正文 ⇒ 没登记（D-248）")

# ④ 这一轮的主角：热图两态帧在基线里到底有几张、盘上是不是真有两态
bl = json.loads(rd(os.path.join(ROOT, "docs", "frame_baseline.json")))
keys = sorted(os.path.basename(k) for k in (bl.get("frames") or {}))
strip = [k for k in keys if k.startswith("heatmap-cell-strip")]
states = sorted(set(k[len("heatmap-cell-strip"):].lstrip("-").split("-")[0] for k in strip))
if len(states) < 2:
    die("基线里 heatmap-cell-strip 只数到状态 %s ⇒ 本轮那句「两态帧在盘上」不成立，名册不许那样写" % states)
for f in ("heatmap-cell-strip-still-90x140-light.png", "heatmap-cell-strip-hover-90x140-light.png"):
    if not os.path.exists(os.path.join(FRAMES, f)):
        die("看图腿的对象不在盘上：" + f + " ⇒ 这一腿记 NOT-RUN，不许编")
n_frames = len([f for f in os.listdir(FRAMES) if f.endswith(".png")]) if os.path.isdir(FRAMES) else 0

# ⑤ 335 的数：其余名册的理由里还有多少句"可复查的否定"没被结构化
NEG = (u"没有两态", u"从未进过", u"没有独立的两态帧", u"不存在", u"没有帧", u"从未被")
hits = []
for name in sorted(os.listdir(os.path.join(ROOT, "scripts", "tests"))):
    if not name.endswith(".py") or name == "test_hover_capture_channel.py":
        continue
    src = rd(os.path.join(ROOT, "scripts", "tests", name))
    src = "\n".join(l.split("#", 1)[0] for l in src.splitlines())
    n = len(re.findall(r":\s*[uR]?['\"][^'\"]*(?:%s)[^'\"]*['\"]" % "|".join(NEG), src))
    if n:
        hits.append((name, n))
if not hits:
    die("一支都没扫出来 ⇒ 这把尺指错了对象（只能读出 0 的尺不配登记结案）")

ctxt, _ = sh(["gh", "run", "list", "--limit", "12", "--json", "databaseId,headSha,status,conclusion"])
runs = json.loads(ctxt[ctxt.index("["):])


def pair(sha):
    h = [r for r in runs if r["headSha"].startswith(sha)]
    if not h:
        return sha + " → 未取到（293）"
    r = h[0]
    return sha + " → " + str(r["databaseId"]) + " / " + r["status"] + " / " + (r["conclusion"] or "未读")


def battery():
    b, rc = sh([sys.executable, "-W", "ignore", "-m", "unittest", "discover", "-s", "scripts/tests"])
    if rc != 0 or not re.search(r"^OK", b, re.M):
        die("电池不是绿的：\n" + "\n".join(l for l in b.splitlines() if l.startswith(("FAIL:", "ERROR:")))[:900])
    m = re.findall(r"^Ran (\d+) tests", b, re.M)
    sk = re.search(r"skipped=(\d+)", b)
    return m[-1], (sk.group(1) if sk else "0")


pre_ran, pre_skip = battery()
SCORES = [9, 14, 14, 3, 14, 15, 15]
HITN = sum(n for _, n in hits)
V = {
    "@@DATE@@": "2026-10-21", "@@ROLL@@": str(ran_of(htxt)), "@@KN@@": KN, "@@KC@@": KC, "@@KREST@@": KREST,
    "@@TBL@@": cover.group(1), "@@COV@@": cover.group(2), "@@PARMS@@": cover.group(3),
    "@@ARMS@@": total.group(2), "@@GAPT@@": roster.group(2), "@@GAPA@@": roster.group(3),
    "@@STRIP@@": str(len(strip)), "@@STATES@@": "、".join(states), "@@FRAMES@@": str(n_frames),
    "@@HITF@@": str(len(hits)), "@@HITN@@": str(HITN), "@@HITNAMES@@": "、".join(n for n, _ in hits[:5]),
    "@@BATT@@": "脚本电池 Ran " + pre_ran + " tests / OK (skipped=" + pre_skip + ")",
    "@@SUM@@": str(sum(SCORES)),
    "@@CI1@@": pair("8a972d0"), "@@CI2@@": pair("8717741"), "@@CI3@@": pair("f7205b6"),
}

UI_NEW = """## 第 279 轮（R280 / 第 279 轮 / Round 277 · @@DATE@@）：名册理由里那句「没有两态帧」是假的，挂了三十几轮 —— 可复查的断言必须结构化，不许只写在散文里（U-933…U-935 / D-266 · 产品 0 文件）

本轮次对照：与 R279（自评 @@PREVSUM@@，changed 从读数变闸门）相比，本轮把"闸门"这条线挪回它该照的对象上：**名册自己的理由文本**。R279 修的是"读数不拦人"，本轮修的是"理由不接对象"。

- **U-933：`DailyCopyHeatmapView` 那行豁免理由，盘上一直有反证。** 它写的是"hover 那一档没有独立的两态帧"，而 `docs/frame_baseline.json` 现读有 @@STRIP@@ 张 `heatmap-cell-strip-*` 帧、覆盖 @@STATES@@ 两种状态（亮暗各两张），判据是 `HeatmapHoverEvidenceTests` 那五格（逐档可辨、只动圈带、不许盖过数据深浅）。双向守卫看不见它，因为它比的是"文件读没读取证键"，不是"理由里那句可复查的话"。⇒ 名册新增 `TWO_STATE_CLAIMS`：每个未接键的悬停文件必须声明它靠哪组前缀被看见（或显式声明 `NO_INK`／`None`），前缀要在**帧名单**里真的数到 ≥2 种状态，理由文本里也不许再出现与它对撞的否定句。
- **U-934：更正之后我自己撞了一次镜像。** 新写的理由里我引用了旧那句假话（"这一行原来写的是「…没有独立的两态帧」"），守卫**按字面**读否定词，于是真产物那一格反而红（Ran @@ROLL@@ / failures=1）。处置不是放宽守卫，而是把规矩写进理由本身：这张表的否定词被字面读，分不清引用与断言，所以旧原话只进台账、不进表。两把刀各钉一条轴（D-244）：M836 把声明前缀换成名单里不存在的东西 ⇒ 必须红在"声明不成立"那一格（对象轴）；M837 把否定词扫描弄瞎 ⇒ 必须红在正对照那一格（尺轴）。现读 @@KC@@/@@KN@@ 全 CAUGHT、RESTORE_CLEAN=@@KREST@@。
- **U-935：同一族还有 @@HITN@@ 句没被结构化（新开 335）。** 扫 `scripts/tests/` 其余名册（剥注释后按"字典值里含否定词"数），@@HITF@@ 个文件共 @@HITN@@ 句这样的理由（点名 @@HITNAMES@@…）。它们每一条都是"散文说没有，而没人去数过有没有"——本轮只把悬停这一本做了，其余按 335 逐本处理，不许顺手结案成"名册都结构化了"。310 那 @@GAPT@@ 张表 / @@GAPA@@ 把刀的静默不覆盖仍在原单。

眼睛腿：RUN —— 现读 @@FRAMES@@ 张帧在盘上，看的就是本轮声明的那一对：`heatmap-cell-strip-still-90x140-light` 与 `-hover-90x140-light`。静置那张是一整片无描边的圆角方块（深浅按档分布）；悬停那张只有第四行第二列多了一圈**深色硬边**，其余格子一格未动 ⇒ 两态差别确实存在、且只落在那一圈上，与 `testHoverChangesOnlyTheRingBand` 那条判据同形。旧理由那句"拍不到"就此被眼睛与名单两头各自否证。
读数腿：RUN —— 基线现读 heatmap-cell-strip @@STRIP@@ 张、状态集合 @@STATES@@；判据卷 Ran @@ROLL@@ OK；变异 @@KC@@/@@KN@@ CAUGHT；预检 tables=@@TBL@@ covered=@@COV@@ arms=@@PARMS@@ bad=0、ARM_TOTAL arms=@@ARMS@@ dupes=0；@@BATT@@。
产品腿：0 文件（只动 `scripts/tests/` 与两张 .scratch 表 ⇒ sources 格不动）。热图那一位的**画法**本轮没改，改的是"它的两态帧被说成不存在"这笔假账。
未做（逐条）：① 335（其余 @@HITN@@ 句未结构化的理由）；② 333 的 CI 半；③ 312 的具名出口（欠第九轮）；④ 331、332、330、328、323、322、317、314-316；⑤ 310 的 @@GAPT@@ 张表、334 的 @@HITN@@ 支写死本机根那族（现读 280 支，见 R279）；⑥ 291 的墨轴、305、299、301、307；⑦ 用户闸门 220 路 A / 228② / 265。

"""

ITER_NEW = """## Round 277 · 名册理由里那句「没有两态帧」是假的：可复查的断言必须结构化，不能只写在散文里（R280 / 第 279 轮）/ D-266 · 产品 0 文件

本轮次对照：与 R279（自评 83，读数变闸门）相比，本轮把同一族规矩用到名册的理由文本上 —— 上一轮量的是"数不拦人"，这一轮量的是"理由不接对象"。
看图腿：RUN —— 现读 @@FRAMES@@ 张帧，看的就是被声明的那一对静置／悬停：静置无描边，悬停只有第四行第二列多一圈深色硬边、其余格子未动 ⇒ 两态确实拍得到，旧那句"拍不到"被眼睛与帧名单两头各自否证。
读数腿：RUN —— 基线现读 heatmap-cell-strip @@STRIP@@ 张、状态 @@STATES@@；判据卷 Ran @@ROLL@@ OK；变异 @@KC@@/@@KN@@ 全 CAUGHT、RESTORE_CLEAN=@@KREST@@；@@BATT@@；预检 tables=@@TBL@@ covered=@@COV@@ arms=@@PARMS@@ bad=0。
七维度自评：
| 维度 | 分/满分 |
| 真实视觉审查 | @@D0@@/15 |
| 判据有效性 | @@D1@@/15 |
| 假绿防御 | @@D2@@/15 |
| 产品面推进 | @@D3@@/15 |
| 台账一致性 | @@D4@@/15 |
| 交付诚实性 | @@D5@@/15 |
| 可复核性 | @@D6@@/15 |
各维理由：真实视觉审查 @@D0@@ —— 本轮第一次把"看"对准自己刚声明的对象（两态帧各一张），但没看新位点；判据有效性 @@D1@@ —— 声明现在要在帧名单里数得到才算数，扣一分是只覆盖悬停这一本名册；假绿防御 @@D2@@ —— 两把刀各钉一条轴，且守卫被自家引用喂饱那次是真红（不是事后编的）；产品面推进 @@D3@@ —— 0 文件，热图悬停画法未动，动的是那笔假账；台账一致性 @@D4@@ —— U/D/BACKLOG 三处编号都由脚本现读对账；交付诚实性 @@D5@@ —— 三十几轮前的假话被点名撤回，且旧原话留在 UI 台账而不是偷偷改写；可复核性 @@D6@@ —— 名单、判据卷、刀、日志都在原地可重跑。合计 **@@SUM@@**/105。

"""

DEC_NEW = """**D-266（R280）：名册理由里凡是能被盘上对象否证的句子，必须抽成结构化字段并与那个对象对账；写在散文里的"没有 / 从未 / 不存在"等于没有做过判定。** 理由：悬停取证名册里 `DailyCopyHeatmapView` 那行豁免写着"hover 那一档没有独立的两态帧"，而 `docs/frame_baseline.json` 一直有 `heatmap-cell-strip-still/-hover` 亮暗四张，判据（`HeatmapHoverEvidenceTests` 五格）也一直在跑 —— 这句假话挂了三十几轮。原有守卫是双向的，但双向的是"文件读没读取证键"这一轴，理由文本从来没人拿去和帧名单比。现在 `TWO_STATE_CLAIMS` 把三种情形分开：有前缀 ⇒ 前缀必须在名单里数到 ≥2 种状态，且理由不许再出现否定句；`None` ⇒ 理由必须点名那份缺席；`NO_INK` ⇒ 理由必须点名画法搬去哪了（撤项要有去处，R177 同族）。与 D-255（名册只在实际扫到的对象里对账）、R100（有键无值算红）、R177（撤项做成显式通道）同族，但这条管的是**理由本身**：豁免表可以是对的，也可以是一堵没人查的墙。

"""

CHG_NEW = """### Fixed（R280 / 第 279 轮 / Round 277 · 名册理由接上对象）

`scripts/tests/test_hover_capture_channel.py` 新增第二条轴 `TWO_STATE_CLAIMS` + `claim_problems()`：每个未接取证键的悬停文件必须声明它靠哪组两态帧被看见（或显式 `None`／`NO_INK`），声明的前缀要在 `docs/frame_baseline.json` 的名单里真的数到 ≥2 种状态；理由文本里出现与声明对撞的否定句 ⇒ 红；声明为"没有"而理由没点名缺席 ⇒ 也红。修掉的假账：`DailyCopyHeatmapView` 那行"hover 那一档没有独立的两态帧"——基线现读有 `heatmap-cell-strip-{still,hover}` 亮暗 @@STRIP@@ 张、判据五格一直在跑，这句挂了三十几轮。新增 `mutate_r280.py`：M836（前缀指向不存在的帧 = 对象轴）／M837（否定词扫描弄瞎 = 尺轴）现读 @@KC@@/@@KN@@ 全 CAUGHT、RESTORE_CLEAN=@@KREST@@，并登记进预检（tables=@@TBL@@ covered=@@COV@@ bad=0、ARM_TOTAL arms=@@ARMS@@ dupes=0）。本轮自己撞的镜像也入账：更正后的理由引用了旧假话原句，守卫按字面读否定词 ⇒ 真产物那一格反而红（Ran @@ROLL@@/failures=1），处置是把"否定词被字面读、旧原话只进台账"写进理由本身（U-934）。新开 335：其余 @@HITF@@ 个文件共 @@HITN@@ 句同形理由仍未结构化（点名 @@HITNAMES@@…）。@@BATT@@；眼睛腿 RUN（静置／悬停各一张，圈只在那一格）。产品 0 文件 ⇒ sources 格不动。CI：@@CI1@@／@@CI2@@／@@CI3@@。

"""

BACK_NEW = ("**335. 其余名册的「理由文本」里还有 @@HITN@@ 句可被盘上对象否证的否定句，没有结构化（R280 现读：扫 `scripts/tests/` 剥注释后的字典值，"
            "@@HITF@@ 个文件命中，点名 @@HITNAMES@@…）**：R280 只把悬停那一本做了（`TWO_STATE_CLAIMS` 与帧名单对账），其余每一本都要回答同一句话 —— "
            "这条豁免/红名单/未覆盖声明里的「没有 / 从未 / 不存在」，是量出来的还是写上去的？做法照 R280：① 把可复查的那半句抽成字段（指向一个能现读的名单：帧基线、臂表、名册、日志）；"
            "② 声明与名单双向对账（指向不存在的对象要红、真缺席而理由没点名也要红）；③ 每本配一把「把声明指向不存在对象」的刀；"
            "④ 做完一本就从待办里删一行，不许把 @@HITN@@ 抄成下一次的起点（D-266 同族，R280 新开）**")

STATE_NEW = """## R280 状态（第 279 轮 / Round 277 · @@DATE@@）
最后更新：2026-10-21（本地 · R280 / 第 279 轮 / Round 277）：**名册理由接上对象：热图那行「没有两态帧」是挂了三十几轮的假话，现由 `TWO_STATE_CLAIMS` 与帧名单双向对账钉住**（U-933…U-935 · D-266 · 产品 0 文件 · 自评 @@SUM@@/105）

**本轮落地**：`test_hover_capture_channel.py` 加第二条轴（前缀必须在 `docs/frame_baseline.json` 里数到 ≥2 种状态；`None` 要理由点名缺席；`NO_INK` 要写明画法搬去哪）+ 4 格新证人（合计 Ran @@ROLL@@）+ `mutate_r280.py` M836/M837（@@KC@@/@@KN@@ 全 CAUGHT、RESTORE_CLEAN=@@KREST@@，已登记进预检 tables=@@TBL@@ covered=@@COV@@ bad=0）。基线现读 `heatmap-cell-strip` @@STRIP@@ 张、状态 @@STATES@@；@@BATT@@；ARM_TOTAL arms=@@ARMS@@ dupes=0。自己撞的镜像入账：更正后的理由引用旧假话原句 ⇒ 守卫按字面读否定词，真产物那一格反而红（U-934）—— 不放宽守卫，把规矩写进理由文本。新开 335（其余 @@HITN@@ 句同形理由）。眼睛腿 RUN（静置／悬停各一张，圈只落在那一格）。产品 0 文件。

**下一轮（R281 / 第 280 轮 / Round 278）的 ⓪**：
⓪ 读 CI：@@CI1@@、@@CI2@@、@@CI3@@ 加上本笔触发的那一跑（`gh run list --limit 4 --json databaseId,headSha,status,conclusion` 现取配对，别编号；只登记不轮询，R140）。要验的是 STEP[9] 的 failures=0 —— 本轮那 4 格新证人里有一格会读 `docs/frame_baseline.json` 并按前缀数状态，runner 上基线是同一份文件，理论上同结论；若颗数或名单不同，按 331 那两张机器名册解释，不许先假设相等。
① **回到产品动效面（连续七轮是最弱一维）**：330（三处 hover 淡入的"过程"还没有产物证人 —— `MotionFilmstripTests` 那条路，`Scenario` 要能在触发时翻 `hoveredForCapture`；加一卷要全量重跑并登记名单为何变长，R98 那一课）、305（按下台阶的地板分辨实验）。
② 335（其余 @@HITN@@ 句未结构化的理由，逐本做、做完删一行）、333 的 CI 半（changed 的按机器具名出口 + 不误红那把刀）。
③ **312 的具名出口（欠第九轮）**：本机 3.000 不许降（D-251）。
④ 331、332、330、328、323、322、317、314-316；310 的 @@GAPT@@ 张表、334 的写死本机根那一族。
⑤ 用户闸门 220 路 A / 228② / 265。

"""

PREVSUM = "83"
V["@@PREVSUM@@"] = PREVSUM


def render(s):
    for k, v in V.items():
        s = s.replace(k, v)
    if "@@" in s:
        die("仍有未替换占位符 " + ",".join(sorted(set(re.findall(r"@@[A-Z0-9]+@@", s)))))
    return s


for i, nm in enumerate("D0 D1 D2 D3 D4 D5 D6".split()):
    ITER_NEW = ITER_NEW.replace("@@" + nm + "@@", str(SCORES[i]))
for n in ("UI_NEW", "ITER_NEW", "DEC_NEW", "CHG_NEW", "STATE_NEW"):
    globals()[n] = render(globals()[n])
BACK_NEW = render(BACK_NEW) + "\n"

ui_p = B["AGENT_UI_AUDIT.md"]
ui_old = rd(ui_p)
if "## 第 279 轮" in ui_old:
    die("UI_AUDIT 已有第 279 轮 ⇒ 生成器不幂等，先还原")
anchor = "## 第 278 轮"
if ui_old.count(anchor) != 1:
    die("UI_AUDIT 锚点命中 %d 次" % ui_old.count(anchor))
ui_new = ui_old.replace(anchor, UI_NEW + anchor, 1)

it_p = B["AGENT_VISUAL_ITERATION.md"]
it_old = rd(it_p)
if re.search(r"^## Round 277 · ", it_old, re.M):
    die("ITERATION 已有 Round 277 ⇒ 不幂等")
# 升序那本：尾轮必须是**最大号**（曲线尺按文件顺序认尾轮 —— R279 补记时撞过一次，这次别再撞）
it_new = it_old.rstrip("\n") + "\n\n" + ITER_NEW

dc_p = B["AGENT_DECISIONS.md"]
dc_old = rd(dc_p)
if "D-266" in dc_old or "D-265" not in dc_old:
    die("D 号不对（D-265 应在盘上、D-266 不该在）")
dc_new = dc_old.rstrip("\n") + "\n\n" + DEC_NEW
cg_p = B["CHANGELOG.md"]
cg_old = rd(cg_p)
cg_new = cg_old.replace("## [Unreleased]\n", "## [Unreleased]\n\n" + CHG_NEW, 1)
bk_p = B["AGENT_BACKLOG.md"]
bk_old = rd(bk_p)
last = re.findall(r"^\*\*(\d{3})\. ", bk_old, re.M)
if last[-1] != "334":
    die("BACKLOG 最后一单不是 334（现读 " + str(last[-3:]) + "）")
bk_new = bk_old.rstrip("\n") + "\n\n" + BACK_NEW
st_p = B["AGENT_STATE.md"]
st_old = rd(st_p)
if "## R279 状态" not in st_old:
    die("STATE 找不到 R279 锚点")
st_new = st_old.replace("## R279 状态", STATE_NEW + "## R279 状态", 1)


def must_preserve(old, new, name):
    cn = Counter(new.splitlines())
    lost = [l for l, c in Counter(old.splitlines()).items() if cn[l] < c]
    if lost:
        die(name + " 弄丢 " + str(len(lost)) + " 行：" + " | ".join(lost[:2])[:140])


for o, n, name in ((ui_old, ui_new, "AGENT_UI_AUDIT.md"), (cg_old, cg_new, "CHANGELOG.md"),
                   (bk_old, bk_new, "AGENT_BACKLOG.md"), (st_old, st_new, "AGENT_STATE.md"),
                   (it_old, it_new, "AGENT_VISUAL_ITERATION.md")):
    must_preserve(o, n, name)

ids = [int(x) for x in re.findall(r"- \*\*U-(\d+)", UI_NEW)]
if ids != list(range(933, 936)):
    die("U 号不连续：" + str(ids))
if "U-933…U-935" not in UI_NEW.splitlines()[0]:
    die("节标题 U 区间与定义不符")
rows = [l for l in ITER_NEW.splitlines() if re.match(r"\| .* \| \d+/15 \|$", l)]
scores = [int(re.search(r"\| (\d+)/15 \|", l).group(1)) for l in rows]
if len(scores) != 7 or sum(scores) != sum(SCORES):
    die("七维表形状或合计不对：" + str(scores))
if not it_new.startswith(it_old.rstrip("\n")) or "## Round 276 · " not in it_new:
    die("ITERATION 不是纯追加")
tail = re.findall(r"^## Round (\d+) · ", it_new, re.M)
if int(tail[-1]) != 277:
    die("ITERATION 的**文件尾轮次**必须是本轮（现读 " + str(tail[-3:]) + "）⇒ 曲线尺按文件顺序认尾轮，"
        "把新节插在最大号之前会被判 CURVE_DROPS_TAIL（R279 补记撞过，这轮又差点撞第二次）")
if it_new.count("| 真实视觉审查 |") != it_old.count("| 真实视觉审查 |") + 1:
    die("七维表数量不对")
if bk_new.count("\n**335. ") != 1:
    die("新开 335 没落上")
if "## R280 状态" not in st_new:
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
print("LEDGERS_R280 OK batt=Ran " + ran2 + " (skipped=" + skip2 + ") roll=" + str(ran_of(htxt))
      + " knives=" + KC + "/" + KN + " strip_frames=" + V["@@STRIP@@"] + " states=" + V["@@STATES@@"]
      + " prose_negations=" + V["@@HITN@@"] + "/" + V["@@HITF@@"] + "files U=933..935 D=266 new=335")
print(out.strip().splitlines()[-1])
