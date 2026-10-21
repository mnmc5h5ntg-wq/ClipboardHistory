#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R273 台账生成器（第 272 轮 / Round 270）：把只落了代码半的那一轮补成完整一轮。

数字一律现读：两份同码重捕目录、捕获卷日志、基线 json、电池日志、预检。
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
A_DIR = "/tmp/r273_a"
B_DIR = "/tmp/r273_b"


def die(m):
    sys.stderr.write("LEDGERS_R273 REFUSED: " + m + "\n")
    raise SystemExit(2)


def rd(p):
    with io.open(p, encoding="utf-8", errors="replace") as h:
        return h.read()


def sh(cmd, cwd=None):
    env = dict(os.environ)
    env["PYTHONUTF8"] = "1"
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    pr = subprocess.run(cmd, cwd=(cwd or ROOT), env=env, capture_output=True, text=True)
    return (pr.stdout or "") + (pr.stderr or ""), pr.returncode


def md5(p):
    import hashlib
    with io.open(p, "rb") as h:
        return hashlib.md5(h.read()).hexdigest()


def sha256(p):
    import hashlib
    with io.open(p, "rb") as h:
        return hashlib.sha256(h.read()).hexdigest()


# ---- 同码双跑：证人必须是这两份目录本身（两种摘要各自数一遍，别只认一把尺）----
if not (os.path.isdir(A_DIR) and os.path.isdir(B_DIR)):
    die("两份重捕目录不全 ⇒ 324 的结案没有证人")
fa = sorted(f for f in os.listdir(A_DIR) if f.endswith(".png"))
fb = sorted(f for f in os.listdir(B_DIR) if f.endswith(".png"))
if len(fa) != 170 or len(fb) != 170:
    die("两份目录不是各 170 张：%d / %d" % (len(fa), len(fb)))
bset = set(fb)
diff_md5 = [f for f in fa if f in bset and md5(os.path.join(A_DIR, f)) != md5(os.path.join(B_DIR, f))]
diff_sha = [f for f in fa if f in bset and sha256(os.path.join(A_DIR, f)) != sha256(os.path.join(B_DIR, f))]
if diff_md5 or diff_sha:
    die("同码双跑之间仍有不同（md5 %d / sha256 %d）⇒ 修法没做到，324 不许结案：%s"
        % (len(diff_md5), len(diff_sha), (diff_md5 or diff_sha)[:3]))
if len(fa) != len(bset):
    die("两份目录的名单不一致：A=%d B=%d" % (len(fa), len(bset)))

# ---- 基线：那两张 recording 帧必须已按新捕获确认过 ----
# **这把尺量的是 sha256，不是 md5**：本函数第一版拿 md5 去比基线里的 64 位十六进制摘要，
# 于是「基线没在同一笔里确认」——那是尺读错对象，不是账没做（见 U-914）。
# 现在先问基线自己声明的算法（note 里那串），再按**整条摘要严格相等**比，不用 endswith / 子串。
bl = json.loads(rd(os.path.join(ROOT, "docs/frame_baseline.json")))
frames = bl.get("frames") or {}
if not frames:
    die("基线 json 里没有帧表：键=" + ",".join(list(bl)[:6]))
if "sha256" not in str(bl.get("note") or ""):
    die("基线没自陈 sha256 ⇒ 别拿别的摘要去比：" + str(bl.get("note"))[:80])
if len(frames) != len(fa):
    die("基线帧数 %d 与本轮新捕 %d 不相等" % (len(frames), len(fa)))
rec = sorted(k for k in frames if "settings-shortcuts-recording" in k)
if len(rec) != 2:
    die("基线里那两张 recording 帧数量不是 2：" + str(rec))
for k in rec:
    name = os.path.basename(k) if "/" in k else k
    p = os.path.join(A_DIR, name)
    if not os.path.exists(p):
        die("基线键对不上磁盘文件：" + k)
    dig = str(frames[k])
    if len(dig) != 64 or not re.fullmatch(r"[0-9a-f]{64}", dig):
        die("基线里 %s 的摘要不是 64 位十六进制 sha256：%r" % (name, dig[:24]))
    if dig != sha256(p):
        die("基线里那张 %s 的摘要不是本轮新捕的那份 ⇒ 基线没在同一笔里确认" % name)

# ---- 「恰好 2 张不同」也现读：与修法之前那笔基线逐键比摘要 ----
prev_txt, prc = sh(["git", "show", "6e810e6^:docs/frame_baseline.json"])
if prc != 0:
    die("读不到修法之前的基线那笔：" + prev_txt[-160:])
prev = json.loads(prev_txt).get("frames") or {}
changed = sorted(k for k in frames if k in prev and str(prev[k]) != str(frames[k]))
added = sorted(k for k in frames if k not in prev)
dropped = sorted(k for k in prev if k not in frames)
if len(prev) != len(frames) or added or dropped:
    die("基线名单本身在动（前=%d 现=%d 增=%d 删=%d）⇒ 不是「只有两帧换摘要」"
        % (len(prev), len(frames), len(added), len(dropped)))
if changed != rec:
    die("与修法之前那笔基线相比，换了摘要的不止那两张 recording：%s" % str(changed)[:160])

settle = re.findall(r"RECORDER_SETTLE waited_ms=(\d+) 动画键=(-?\d+)", rd("/tmp/r273_a.log"))
if len(settle) < 2 or any(k != "0" for _, k in settle):
    die("等待读数不全或动画键没归零：" + str(settle[:4]))
waits = [int(w) for w, _ in settle]

batt = rd("/tmp/r273_batt.log")
ran = re.findall(r"^Ran (\d+) tests", batt, re.M)
if not ran or not re.search(r"^OK", batt, re.M):
    die("电池日志不是绿的")

ptxt, _ = sh([sys.executable, PRE])
cover = re.search(r"NEEDLE_PRECHECK tables=(\d+) covered=(\d+) arms=(\d+) bad=(\d+)", ptxt)
roster = re.search(r"TABLE_ROSTER registered=(\d+) unregistered_with_arms=(\d+) hidden_arms=(\d+)", ptxt)
total = re.search(r"ARM_TOTAL files=(\d+) arms=(\d+) dupes=(\d+) repeats=(\d+)", ptxt)
if not (cover and roster and total) or cover.group(4) != "0" or total.group(3) != "0":
    die("预检读数不全或有坏：\n" + ptxt[-300:])

ctxt, _ = sh(["gh", "run", "list", "--limit", "10", "--json", "databaseId,headSha,status,conclusion"])
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
if pre_ran != ran[-1]:
    die("电池日志（" + ran[-1] + "）与现在（" + pre_ran + "）不一致")

V = {
    "@@DATE@@": "2026-10-21",
    "@@N@@": str(len(fa)), "@@WAITS@@": "/".join(str(w) for w in waits[:4]),
    "@@WMIN@@": str(min(waits)), "@@WMAX@@": str(max(waits)),
    "@@CHG@@": str(len(changed)), "@@RECNAME@@": "、".join(os.path.basename(k) for k in changed),
    "@@DIGLEN@@": str(len(str(frames[rec[0]]))),
    "@@BATT@@": "脚本电池 Ran " + pre_ran + " tests / OK (skipped=" + pre_skip + ")",
    "@@TBL@@": cover.group(1), "@@COV@@": cover.group(2), "@@PARMS@@": cover.group(3),
    "@@GAPT@@": roster.group(2), "@@GAPA@@": roster.group(3), "@@ARMS@@": total.group(2),
    "@@CI1@@": pair("6e810e6"), "@@CI2@@": pair("5a6694b"), "@@CI3@@": pair("cc8cb91"),
}

UI_NEW = """## 第 272 轮（R273 / 第 272 轮 / Round 270 · @@DATE@@）：一张会同码翻脸的帧被钉住了 —— 固定挂钟泵换成等条件，证人是一次同码双跑（U-911…U-914 / D-259 · 产品 0 文件）

本轮次对照：与 R272（自评 80，预检"看得见"与"不抄两份"同时成立）相比，本轮收 R272 收尾定位到病根的那张单子：**324**。

- **U-911：324 结案，三条条件各有读数** —— ① 修法：`performClick` 之后不再睡死 0.35s，改成"等 Core Animation 的动画键清空（1.5s 上限）"，并打 `RECORDER_SETTLE waited_ms=… 动画键=…`；现读动画键全部归 0，等待 @@WAITS@@ ms（旧写法每档一律 350 ms）。② 证人：**同码双跑** @@N@@ 张 vs @@N@@ 张，逐张比 md5 与 sha256 两种摘要 ⇒ 不同都是 0（对比 R270 现读的"盘上 6 份历史捕获 5 种 md5"）。③ 变化范围可指认：**现读**修法之前那笔基线（`git show 6e810e6^:docs/frame_baseline.json`）与当前基线逐键比摘要 ⇒ 换摘要的键数 = @@CHG@@，且恰好就是 @@RECNAME@@（名单增删 0、总键数不变），这两张的新摘要与本轮新捕文件**整条 @@DIGLEN@@ 位十六进制严格相等**，不是看它打过 update 就算。
- **U-912：一次自坏，以及"回退 + 记因"为什么比"硬推"便宜** —— 第一次尝试被我自己写的改注释脚本打断：它按"行首是 `#`"判注释，把同一本 `UICaptureHarness.swift` 里的 `#if arch(...)` 一类 **pound 指令**一起改成 `//` ⇒ `invalid redeclaration of 'arch'`、测试卷编译失败。处置是整本 `git checkout` 还原 + 把成因与顺序写进 BACKLOG 324 的追记二，然后按顺序重做：只改那一处、整行字面锚点、**改完立刻** `swift build --build-tests`（这次干净：0 error 0 告警）、再跑同码双跑。写成 D-259：Swift 里 `#` 开头既可能是注释也可能是指令，批量改注释的脚本必须看 `#` 后面那个 token。
- **U-913：半套账被点名，而不是等下一轮自己想起来** —— 本轮先落代码半（`6e810e6`）与基线，随后单独一笔把"欠哪五本 + 补的时候数字从哪现读"写进 `AGENT_STATE.md`（`5a6694b`），这一笔就是那半本账的补齐。CI：@@CI1@@、@@CI2@@、@@CI3@@ 交接时未读 ⇒ 只登记号不轮询（R140），本轮不引用任何 runner 结论。
- **U-914：补齐台账的那把尺一开始量的是 md5，而基线存的是 sha256 —— 它红在自己的格子（U-911 的③）上，不是红在产品上** —— 生成器第一版写的是 `dig.endswith(md5(p)) or dig == md5(p) or md5(p) in dig`，于是 `settings-shortcuts-recording-…-dark.png` 那一格直接拒绝写盘（LEDGERS_R273 REFUSED）。这不是"账没做"，是**尺读错了对象**：同一份基线的 note 里自陈"离屏帧的 sha256 基线"，`scripts/frame_baseline.py:53` 也是 `sha256_of`。修法按 D-247 的路子走 —— 让守卫与被守卫的尺用同一个估计量：先读基线自己声明的算法与摘要长度（不是 sha256 ⇒ 不比对、直接拒），再按**整条严格相等**比，并把那三种"含糊包容"（endswith / 子串）全删掉；同时给同码双跑配上 md5 与 sha256 **两种**摘要各自数一遍，一把尺说好不算数。这一格留在这里的原因：如果第一版靠 endswith 侥幸通过，"基线同一笔确认"就会变成一条永远绿的话。

眼睛腿：NOT-RUN —— 本轮改的就是那张帧的**相位**，两档 recording 帧的变化由两种摘要对账与基线整条比对签字；人眼侧没有新看别的位点，所以这一维按实记低分，不编一句"看了两张挺稳"。
读数腿：RUN —— `RECORDER_SETTLE`（动画键=0，等待 @@WMIN@@…@@WMAX@@ ms）、同码双跑 @@N@@/@@N@@ 张两种摘要都相同、基线 @@CHG@@ 张换摘要且整条对上、@@BATT@@、预检 tables=@@TBL@@ covered=@@COV@@ arms=@@PARMS@@ bad=0、ARM_TOTAL arms=@@ARMS@@。
产品腿：0 文件（只动 `Tests/` 与 `docs/frame_baseline.json` ⇒ sources 格按规矩不动）。
未做（逐条）：① **312 的具名出口（欠第六轮）**；② 323（抄值的可用估计量）、322、317、314、315、316；③ 310 的 @@GAPT@@ 张表 / @@GAPA@@ 把刀、309 那 6 张；305、299、301、307、287/284、297/298/300、304、291 三位；④ 用户闸门 220 路 A / 228② / 265。

"""

ITER_NEW = """## Round 270 · 一张会同码翻脸的帧被钉住：固定挂钟泵换成等条件，验收证人是一次同码双跑（R273 / 第 272 轮）/ D-259 · 产品 0 文件

本轮次对照：与 R272（自评 80）相比，本轮把 R272 定位到病根的 324 做完，并补上自己欠的那半本账。
看图腿：NOT-RUN —— 改的就是那张帧的相位，变化由两种摘要对账与基线整条比对签；没有另看新位点，这一维按实记低分。
读数腿：RUN —— `RECORDER_SETTLE` 动画键全部为 0、等待 @@WMIN@@…@@WMAX@@ ms（旧写法一律睡 350 ms）；同码双跑 @@N@@ 张 vs @@N@@ 张，md5 与 sha256 两种摘要各自数一遍都是不同 0；与修法之前那笔基线逐键比摘要 ⇒ 换摘要的键数 @@CHG@@（就是 @@RECNAME@@，名单增删 0），其新摘要与本轮新捕文件整条 @@DIGLEN@@ 位严格相等；@@BATT@@；预检 tables=@@TBL@@ covered=@@COV@@ arms=@@PARMS@@ bad=0。
七维度自评：
| 维度 | 分/满分 |
| 真实视觉审查 | 6/15 |
| 判据有效性 | 14/15 |
| 假绿防御 | 15/15 |
| 产品面推进 | 3/15 |
| 台账一致性 | 15/15 |
| 交付诚实性 | 15/15 |
| 可复核性 | 15/15 |
各维理由：真实视觉审查 6 —— 本轮确实动了画面（两档 recording 帧的相位），但结论由字节对账签，人眼侧没另看位点；判据有效性 14 —— 帧基线从此是可信证人，扣一分是这条只覆盖一颗夹具；假绿防御 15 —— 结案三条各有读数，且"跑过一次 update"不算数（生成器把 endswith/子串那三种含糊包容删掉、按整条摘要比），本轮自己的尺先红在自己身上（U-914）而不是被绕过去；产品面推进 3 —— 0 产品文件，但改的是取证通道的可信度；台账一致性 15 —— 半套账被点名并补齐，"恰好 2 张不同"这类句子改成从 `git show 6e810e6^` 现读，不再照抄提交信息；交付诚实性 15 —— 自坏（pound 指令被吃掉）与自己那把 md5 尺的错都写在账上；可复核性 15 —— 两份目录、两份日志、两笔基线 json 都在原地可重跑。合计 **83**/105。

"""

DEC_NEW = """**D-259（R273）：批量改 Swift 注释的脚本必须区分 `#` 注释与 `#` 指令；一次自坏的正确代价是"整本还原 + 把成因与顺序写进账 + 按顺序重做"，不是当场放宽检查或硬推。** 理由：修 324 时我用一个"行首是 `#` 就换成 `//`"的脚本去补注释标记，结果把同一本 `UICaptureHarness.swift` 里的 `#if arch(...)` 一起改掉 ⇒ `invalid redeclaration of 'arch'`、测试卷编译失败（`swift build --build-tests` 现读）。回退之后按自己写进 BACKLOG 324 追记二的顺序重做：只改那一处、用整行字面锚点、**改完立刻编译**、再跑同码双跑当证人 —— 于是 324 今天能结案（动画键归 0、等待 @@WMIN@@…@@WMAX@@ ms、双跑 @@N@@/@@N@@ 张两种摘要都相同、基线现读换摘要键数=@@CHG@@ 且整条对上）。与 R245（电池跑着时别碰它读写的文件）、D-247（守卫要与被守卫的尺同一估计量）同族，但这条管的是**改代码的脚本自己**：它同样需要"看下一个 token"这种最小分辨力，否则它会以修注释的名义改语义。

"""

CHG_NEW = """### Fixed（R273 / 第 272 轮 / Round 270 · 一张会同码翻脸的帧被钉住）

`UICaptureHarness.swift` 的录制态夹具：`performClick` 之后的固定 `RunLoop.run(until: +0.35s)` 换成"等 Core Animation 动画键清空（1.5s 上限）"+ 读数 `RECORDER_SETTLE waited_ms=… 动画键=…`。现读：动画键全部 0，等待 @@WAITS@@ ms。验收证人 = 同码双跑：@@N@@ 张 vs @@N@@ 张逐张比 md5 与 sha256，两种摘要都是不同 0（此前是"盘上 6 份历史捕获 5 种 md5"）；与 `git show 6e810e6^:docs/frame_baseline.json` 逐键比摘要 ⇒ 换摘要的键数 @@CHG@@（@@RECNAME@@，名单增删 0），且这两张的新摘要与本轮新捕文件**整条严格相等**（不是 endswith / 子串）。**324 结案**。过程里自坏两次并都留在账上：批量改注释的脚本吃掉了 `#if arch` 指令 ⇒ 编译失败 ⇒ 整本还原并记因（D-259）；补齐台账的生成器第一版拿 md5 比 sha256 基线 ⇒ 它拒绝写盘（U-914，新开 328 去扫其余同形尺）。@@BATT@@、预检 tables=@@TBL@@ covered=@@COV@@ arms=@@PARMS@@ bad=0。CI：@@CI1@@／@@CI2@@／@@CI3@@ 交接时未读（只登记号不轮询，R140）。产品 0 文件 ⇒ sources 格不动；看图腿 NOT-RUN。

"""

BACK_NEW = [
    "**328. 把「比摘要」这类对账统一成一条会红的尺（R273 现读：`docs/frame_baseline.json` 的 note 自陈 sha256、"
    "`scripts/frame_baseline.py:53` 是 `sha256_of`，而本轮台账生成器第一版拿 **md5** 去比它，还允许 `endswith`/子串这两种含糊包容 ⇒ "
    "它红在自己的格子上，侥幸方向是「永远绿」）。逐处扫 `scripts/` 与 `.scratch/motion-audit-2/` 里所有比对帧/产物摘要的地方："
    "每处要回答①用的是哪种摘要、②是不是整条严格相等、③算法是否从被比对对象自己声明（note/schema）推出来而不是写在比较式里。"
    "含糊包容一律删掉；扫完要把「拿 md5 比 sha256」做成一把刀（喂错的摘要 ⇒ 必须拒），别只改生成器不配证人（R273 新开）**",
]

STATE_NEW = """## R273 状态（第 272 轮 / Round 270 · @@DATE@@）
最后更新：2026-10-21（本地 · R273 / 第 272 轮 / Round 270）：**324 结案：固定挂钟泵换成等动画键清空，同码双跑 170/170 两种摘要都相同当证人；半套账点名后补齐**（U-911…U-914 · D-259 · 产品 0 文件 · 自评 83/105）

**本轮落地**：夹具等条件 + `RECORDER_SETTLE` 读数（动画键=0、等待 @@WMIN@@…@@WMAX@@ ms）；同码双跑 @@N@@/@@N@@ 张（md5 与 sha256 各自数一遍）不同 0；基线与修法之前那笔逐键比摘要 ⇒ 换摘要键数=@@CHG@@（@@RECNAME@@）、整条 @@DIGLEN@@ 位严格相等；@@BATT@@；预检 tables=@@TBL@@ covered=@@COV@@ arms=@@PARMS@@ bad=0、310 缺口 @@GAPT@@ 张 / @@GAPA@@ 把。上一笔的"欠账登记"由本笔补齐。两处自坏都留在账上：D-259（批量改注释吃掉 `#if` 指令）、U-914（台账生成器拿 md5 比 sha256 基线 ⇒ 拒绝写盘；新开 328 去扫其余同形尺）。

**下一轮（R274 / 第 273 轮 / Round 271）的 ⓪**：
⓪ 读 CI：@@CI1@@、@@CI2@@ 与本轮新跑（只登记号不轮询，R140）。要验的是 **runner 上那两张 recording 帧在新相位下是否稳定**（基线已按本机新捕整条摘要确认 ⇒ runner 若报 changed=@@CHG@@ 就是"这台机器判不了这颗夹具的相位"，按 D-251 具名出口处理，不许改基线迁就）。
① **312 的具名出口（欠第六轮）**：按"纸"那一维推，本机 3.000 不许降（D-251）。
② 328（把"比摘要"统一成一条会红的尺 + 一把喂错摘要的刀）、323（把抄值的可用估计量搬进 scripts/ 并逐处判）、322、317、314、315、316。
③ 310 的 @@GAPT@@ 张表、309 那 6 张；305、299、301、307、287/284、297/298/300、304、291 三位。
④ 产品动效面连续多轮是最弱一维（本轮看图腿 NOT-RUN）：按清账表点一个位真做动效或撤声明。
⑤ 用户闸门 220 路 A / 228② / 265。

"""


def render(s):
    for k, v in V.items():
        s = s.replace(k, v)
    if "@@" in s:
        die("渲染后仍有未替换占位符：" + s[:150])
    return s


for n in ("UI_NEW", "ITER_NEW", "DEC_NEW", "CHG_NEW", "STATE_NEW"):
    globals()[n] = render(globals()[n])
BACK_NEW = "\n\n".join(render(x) for x in BACK_NEW) + "\n"

ui_p = B["AGENT_UI_AUDIT.md"]
ui_old = rd(ui_p)
if "## 第 271 轮" not in ui_old:
    die("UI_AUDIT 找不到锚点")
cut = ui_old.index("## 第 271 轮")
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
        die(name + " 弄丢 " + str(len(lost)) + " 行：" + " | ".join(lost[:2])[:140])


must_preserve(ui_old, ui_new, "AGENT_UI_AUDIT.md")
must_preserve(cg_old, cg_new, "CHANGELOG.md")
must_preserve(bk_old, bk_new, "AGENT_BACKLOG.md")
st_p = B["AGENT_STATE.md"]
st_old = rd(st_p)
if "## R272 状态" not in st_old:
    die("STATE 找不到锚点")
st_new = st_old.replace("## R272 状态", STATE_NEW + "## R272 状态", 1)
must_preserve(st_old, st_new, "AGENT_STATE.md")

ids = [int(x) for x in re.findall(r"- \*\*U-(\d+)", UI_NEW)]
if ids != list(range(911, 915)):
    die("U 号不连续：" + str(ids))
if "U-911…U-914" not in UI_NEW.splitlines()[0]:
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
if "D-259" in dc_old or "D-258" not in dc_old:
    die("D 号不对")
if bk_new.count("\n**328. ") != 1:
    die("新开 328 没落上")
# 「324 结案」这句话必须由 BACKLOG 自己那一单签掉，不是台账里随口一说
seg324 = re.search(r"^\*\*324\. .*?(?=^\*\*\d{3}\. )", bk_new, re.M | re.S)
if not seg324 or "追记三（R273 落地）" not in seg324.group(0) or "324 结案" not in seg324.group(0):
    die("BACKLOG 324 里没有本轮那条结案追记 ⇒ 台账那句「324 结案」没有出处")
if "## R273 状态" not in st_new:
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
print("LEDGERS_R273 OK batt=Ran " + ran2 + " (skipped=" + skip2 + ") double=" + V["@@N@@"] + "/170 两种摘要都相同"
      + " baseline_changed_keys=" + V["@@CHG@@"] + " waits=" + V["@@WAITS@@"]
      + " dig=" + V["@@DIGLEN@@"] + "hex  U=911..914 D=259 new=328")
print(out.strip().splitlines()[-1])
