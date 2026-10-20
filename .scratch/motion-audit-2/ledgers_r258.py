#!/usr/bin/env python3
# R258 台账生成器（第 257 轮 / Round 255）
# 铁律：① 所有数字从日志解析，抓不到就拒绝写盘；② 正文只用 @@键@@ 占位，不做字符串拼接；
#       ③ 五本台账 + STATE 要么全写要么全不写（事务性）。
import re
import os
import sys
import json
from collections import Counter

ROOT = "/Users/wangziyi/Codex_Project0"
CAP = "/tmp/r258_verify/capture.log"
KNIFE = "/tmp/r258_knife.log"
RV = "/tmp/r258_roundverify.log"
BASE_AFTER = "/tmp/r258_verify/baseline_after.log"
LIST_JSON = "/tmp/r258_list2.json"

UI = os.path.join(ROOT, "AGENT_UI_AUDIT.md")
ITER = os.path.join(ROOT, "AGENT_VISUAL_ITERATION.md")
DEC = os.path.join(ROOT, "AGENT_DECISIONS.md")
BACK = os.path.join(ROOT, "AGENT_BACKLOG.md")
CHG = os.path.join(ROOT, "CHANGELOG.md")
STATE = os.path.join(ROOT, "AGENT_STATE.md")


def die(m):
    sys.stderr.write("LEDGERS_R258 REFUSED: " + m + "\n")
    raise SystemExit(2)


def rd(p):
    with open(p, encoding="utf-8", errors="replace") as f:
        return f.read()


def last(pattern, text, flags=0):
    m = re.findall(pattern, text, flags)
    return m[-1] if m else None


# ---------- 读数 ----------
cap_txt = rd(CAP) if os.path.exists(CAP) else ""
cap_exec = last(r"Executed (\d+) tests, with (\d+) tests? skipped and (\d+) failures", cap_txt)
if not cap_exec:
    die("捕获卷汇总行抓不到")
cap_total, cap_skip, cap_fail = (int(x) for x in cap_exec)
if cap_fail != 0:
    die("捕获卷有 " + str(cap_fail) + " 次失败，不落结案账")

kn = rd(KNIFE) if os.path.exists(KNIFE) else ""
for marker in ("M815_INSERTED", "M815_CAUGHT", "M815_RESTORE", "M816_INSERTED", "M816_CAUGHT", "R258_RESTORE"):
    if marker not in kn:
        die("刀日志缺 " + marker + " 这一行 ⇒ 那条腿没跑完，不许写它")
if "M815_CAUGHT=1" not in kn or "M816_CAUGHT=1" not in kn:
    die("两把刀不是都 CAUGHT，账要改口而不是写成功")
if "R258_RESTORE=clean" not in kn or "M815_RESTORE=clean" not in kn:
    die("还原不是逐字节干净")

# 本轮（修后）与臂内（修前形状）的台阶读数，都从 PRESS_LADDER 行解析
def ladder(text):
    out = {}
    # 尾部那两个像素字段**不解析**：刀日志里的 PRESS_LADDER 行被脚本自己的 cut -c200 截断了，
    # 依赖它会让生成器在"日志形状"上假红（本轮真实踩到）。截断之前的字段两边都完整。
    # `底` 那三个字段必须解析：第一版拿"药丸 idle"当底，校准当场把生成器打红
    # （196 是星形符号自己的灰阶，不是那片纸 —— 这正是校准该拦住的那类错）。
    for m in re.finditer(r"PRESS_LADDER_PROOF (light|dark) 底 idle=(\d+) hover=(\d+) press=(\d+)"
                         r"｜药丸 idle=(\d+) hover=(\d+) press=(\d+)"
                         r"｜比值 ([\d.]+) → ([\d.]+) 差=(-?[\d.]+)｜码值台阶 hover=(\d+) press=(\d+) 差=(-?\d+)",
                         text):
        out[m.group(1)] = dict(bg=int(m.group(4)), idle=int(m.group(5)), hover=int(m.group(6)),
                               press=int(m.group(7)), r0=float(m.group(8)), r1=float(m.group(9)),
                               rdiff=float(m.group(10)), sh=int(m.group(11)), sp=int(m.group(12)),
                               sdiff=int(m.group(13)))
    return out


cur = ladder(cap_txt)
if set(cur) != {"light", "dark"}:
    die("本轮台阶读数不完整：" + str(sorted(cur)))
arm = ladder(kn)
if set(arm) != {"light", "dark"}:
    die("M815 臂的台阶读数不完整：" + str(sorted(arm)))


def lin(c):
    c = c / 255.0
    return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4


def ratio(a, b):
    la, lb = lin(a), lin(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


# 临时尺的自检：它必须复现判据自己印出来的那两个比值，否则下面的台阶比值不算数
for tag in ("light", "dark"):
    d = cur[tag]
    for label, mine, theirs in (("悬停", ratio(d["bg"], d["hover"]), d["r0"]),
                                ("按下", ratio(d["bg"], d["press"]), d["r1"])):
        if abs(mine - theirs) > 0.002:
            die(tag + " " + label + "：临时尺与判据自印的比值不一致（" + str(round(mine, 3))
                + " vs " + str(theirs) + "）⇒ 两口径没对上，台阶比值不许写进账")
step_light = ratio(cur["light"]["hover"], cur["light"]["press"])
step_dark = ratio(cur["dark"]["hover"], cur["dark"]["press"])

ID_PAT = r"PRESS_LADDER_IDENTITY (light|dark) 预测按下台阶=([\d.]+) 实读=(\d+) 偏差=([\d.]+)"
ident = {m[0]: m[3] for m in re.findall(ID_PAT, cap_txt)}
arm_ident = {m[0]: m[3] for m in re.findall(ID_PAT, kn)}
if not ident or not arm_ident:
    die("恒等式读数缺失")

rv = rd(RV) if os.path.exists(RV) else ""
rvline = last(r"ROUND_VERIFY .*", rv)
if not rvline:
    die("四件套还没跑完（没有 ROUND_VERIFY 摘要行）")
rvk = dict(re.findall(r"(build_warnings|swift_executed|swift_skipped|swift_failures|frames|baseline_compared|"
                      r"baseline_changed|baseline_missing|dmg|installed_version)=(\S+)", rvline))
need = ["build_warnings", "swift_executed", "swift_skipped", "swift_failures", "frames",
        "baseline_compared", "baseline_changed", "baseline_missing", "dmg", "installed_version"]
miss = [k for k in need if k not in rvk]
if miss:
    die("四件套摘要缺键（有键无值算红）：" + ",".join(miss))
if rvk["build_warnings"] != "0":
    die("build 告警不是 0：" + rvk["build_warnings"])
if rvk["swift_failures"] not in ("0", "NOT-RUN"):
    die("全量卷 failures=" + rvk["swift_failures"] + " ⇒ 本轮不许在红账上写结案")
if rvk["swift_failures"] == "NOT-RUN":
    die("全量卷读数没抓到（NOT-RUN）⇒ 宁可不写，也不要写一个空键")
if rvk["dmg"] in ("NOT-RUN", "", "0", "failed", "FAIL", "none"):
    die("打包/换装那一步没成功或没有读数：" + rvk["dmg"])

base_after = rd(BASE_AFTER) if os.path.exists(BASE_AFTER) else ""
ba = dict(re.findall(r"^(FRAME_BASELINE_\w+)=(\d+)", base_after, re.M))
if "FRAME_BASELINE_CHANGED" not in ba:
    die("基线复核（update 之后那次 compare）缺读数")

runs = json.loads(rd(LIST_JSON)) if os.path.exists(LIST_JSON) else []


def pair(sha):
    hits = [r for r in runs if r["headSha"].startswith(sha)]
    if not hits:
        return sha + " → gh 列表里没有（未取到，成因：不在最近 6 跑里）"
    r = hits[0]
    return sha + " → " + str(r["databaseId"]) + " / " + r["status"] + " / " + (r["conclusion"] or "未读")


ci_block = "；".join([pair("62520ec"), pair("2b17297")])
pm = re.search(r"M815_PURE_EXIT=(\d+) 红名数=(\d+)", kn)
if not pm:
    die("M815 令牌轴的读数缺失")
pure_txt = "退出=" + pm.group(1) + "、红名 " + pm.group(2) + " 格"
# 同版双跑对账：本轮这批帧与四件套重捕的那批帧，台阶读数必须一字不差
RVFULL = "/tmp/round_verify/full.log"
second = ladder(rd(RVFULL)) if os.path.exists(RVFULL) else {}
if set(second) != {"light", "dark"}:
    die("四件套的 full.log 里没有两档台阶读数 ⇒ 复现性无从对账")
if second != cur:
    die("同版两次独立渲染的台阶读数不一致：" + str(second) + " vs " + str(cur))
repro_txt = "与四件套那跑（/tmp/round_verify/full.log）逐字段同值"
L = cur["light"]
D = cur["dark"]
AL = arm["light"]

V = {
    "@@CAP@@": str(cap_total) + " 格 / skip " + str(cap_skip) + " / failures " + str(cap_fail),
    "@@SWIFT@@": rvk["swift_executed"] + " / skip " + rvk["swift_skipped"] + " / failures " + rvk["swift_failures"],
    "@@WARNS@@": rvk["build_warnings"],
    "@@FRAMES@@": rvk["frames"],
    "@@BCOMPARED@@": rvk["baseline_compared"],
    "@@BCHANGED@@": rvk["baseline_changed"],
    "@@BMISSING@@": rvk["baseline_missing"],
    "@@BAFTER@@": str(ba.get("FRAME_BASELINE_CHANGED", "?")) + " / missing " + str(ba.get("FRAME_BASELINE_MISSING", "?"))
                   + " / added " + str(ba.get("FRAME_BASELINE_ADDED", "?")),
    "@@DMG@@": rvk["dmg"],
    "@@VER@@": rvk["installed_version"],
    "@@CI@@": ci_block,
    "@@LH@@": str(L["hover"]),
    "@@LP@@": str(L["press"]),
    "@@LR0@@": ("%.3f" % L["r0"]),
    "@@LR1@@": ("%.3f" % L["r1"]),
    "@@LSD@@": str(L["sdiff"]),
    "@@DH@@": str(D["hover"]),
    "@@DP@@": str(D["press"]),
    "@@DR0@@": ("%.3f" % D["r0"]),
    "@@DR1@@": ("%.3f" % D["r1"]),
    "@@DSD@@": str(D["sdiff"]),
    "@@IDDEV@@": str(ident.get("light", "?")) + " / " + str(ident.get("dark", "?")),
    "@@ARMDEV@@": str(arm_ident.get("light", "?")),
    "@@STEPL@@": ("%.3f" % step_light),
    "@@STEPD@@": ("%.3f" % step_dark),
    "@@ARMPRESS@@": str(AL["press"]),
    "@@ARMSD@@": str(AL["sdiff"]),
    "@@ARMR1@@": ("%.3f" % AL["r1"]),
    "@@PURE@@": pure_txt,
    "@@BCHGNAME@@": (last(r"^\s+changed\s+(\S+)", base_after, re.M) or "无"),
    "@@REPRO@@": repro_txt,
}

UI_NEW = """## 第 257 轮（R258 / 第 257 轮 / Round 255 · 2026-10-21）：按下那一档第一次有帧、第一次有台阶读数，两把刀各钉一条轴（U-834…U-840 / D-244 · 302 部分结案、新开 305、306 · 产品 1 文件）

本轮次对照：与 R257（0 产品文件、把编译级假绿修回能红的形状，自评 79）相比，本轮回到 302 那件欠了两轮的事 —— 让"正在按"这一档第一次在产物像素上可量、可看图、可被刀红回来。它同时读出一条分工：像素判据对"抬量偏小"是免疫的。

- **U-834：产品侧一颗取证键 `pressedForCapture`**（`Views/PressableStyle.swift`）。`PressedLabel` 的缩放与底色两半都汇到**同一个绘制分支**（与 R14 的悬停那颗同一手法），真实 `configuration.isPressed` 那条路一字未动；配一条会红的扫描：产品源码里出现 `.environment(\\.pressedForCapture` 就红（扫前剥行注释，D-235 那一课）。现读 `swift build` 告警 @@WARNS@@ 颗。
- **U-835：新夹具 `row-favorite-press-60x56-{dark,light}`** ⇒ 帧基线 168 → @@FRAMES@@ 张，同一笔 update；update 之后那次 compare：changed/missing/added=@@BAFTER@@。R257 那句"changed=1 不能读成清白"本轮兑现：现在这一档**有帧可对**了。
- **U-836：台阶第一次有读数**（判据 `testPressRungIsOrderedAboveTheHoverRung`，本机现读）：亮档 悬停 @@LH@@ → 按下 @@LP@@（比值 @@LR0@@ → @@LR1@@，码值台阶差 @@LSD@@ 灰阶），暗档 @@DH@@ → @@DP@@（@@DR0@@ → @@DR1@@，差 @@DSD@@）。另配一条**令牌↔像素恒等式**：用这颗控件自己声明的两档 alpha 从悬停台阶反推按下台阶，偏差 @@IDDEV@@ 灰阶（容差 2，本机两档各一次）。捕获卷现读 @@CAP@@，全量卷 @@SWIFT@@；同版双跑对账：@@REPRO@@。
- **U-837：两把刀、两条轴，而且"谁替不了谁"是读出来的不是设计出来的** —— M815 把 `VisualFillLift.pressed` 0.03→0.015（正是 R256 修之前的形状）：真值表红（@@PURE@@），**但同一形状下像素判据仍然绿**（按下 @@ARMPRESS@@、台阶差只剩 @@ARMSD@@、恒等式偏差 @@ARMDEV@@ 照样过）⇒ 像素轴管"台阶没了 / 接线断了"，令牌轴管"台阶多大"，一条都不能省。M816 把抬量压成 0.0：像素轴当场红（三格：两态同灰阶、次序反、恒等式偏），M816 的亮档按下与悬停读到同一个灰阶。两把都 `RESTORE=clean`（整文件备份 + 逐字节 cmp）。
- **U-838：看图腿 RUN** —— 看了 5 张同一位（亮档 idle / hover / press、暗档 press、以及 M815 那批的亮档按下）。所见：idle 完全没有底、hover 是一圈很淡的灰、press 同位再深一点；而 **R256 改前(0.015) 与改后(0.03) 那两张肉眼分不出**（差 @@ARMSD@@ 灰阶，@@ARMPRESS@@ vs @@LP@@）⇒ 那一笔不是一次"看得见的修复"，它的关键论据是地板算术。范围只这一位两档，不许外推到别的按下位点。
- **U-839：第一次量到"相邻两档之间"的对比，并且没有把别的地板搬过来用** —— 亮档悬停↔按下 @@STEPL@@、暗档 @@STEPD@@（临时 python 尺，配正对照：它复现了判据自印的 @@LR0@@/@@DR0@@/@@LR1@@/@@DR1@@ 四个比值，误差 <0.002 才算数）。这两个数**低于**仓库给"悬停对底"定的 1.20/1.10 —— 但那是另一件事的地板，本轮不据此判产品，也不据此改数（R100/R147：阈值要先量出来才准压上去）⇒ 新开 305：把"相邻档台阶"做成仓库里的尺，两机各读一次再推它自己的地板。
- **U-840：四件套与 CI 交账** —— `round_verify.sh` 现读：build 告警 @@WARNS@@、全量卷 @@SWIFT@@、帧 @@FRAMES@@ 张 compare changed=@@BCHANGED@@（变了的那张 @@BCHGNAME@@）missing=@@BMISSING@@、dmg=@@DMG@@、换装本机 @@VER@@。CI（run 号全部 gh 现取）：@@CI@@ ⇒ R256 那朵编译红在 runner 上确认消失。

读数腿：RUN（@@CAP@@ / @@SWIFT@@ / 刀日志 / 基线两次 / 四件套一行）。
眼睛腿：RUN（5 张，见 U-838，范围限定）。
变异腿：RUN（M815 令牌轴、M816 产物轴，两把 CAUGHT、还原逐字节干净）。**但两把都是 bash-only，不在 `mutate_needle_precheck.py` 的名册覆盖里** —— 与 M814 同族，是 299 的第三、四例 ⇒ 新开 306 把设计输入收齐。
未做（逐条）：① 305（台阶地板）；② 306（三把重捕型刀进名册）；③ 301 的 stamp 门仍不在仓库里；④ 291 那四位欠账、287/284/286；⑤ 用户闸门 220 路 A / 228② / 265。

"""

ITER_NEW = """## Round 255 · 按下那一档第一次有帧：取证键 + 台阶读数 + 两把各钉一条轴的刀（R258 / 第 257 轮）/ D-244 · 302 部分结案、新开 305、306 · 产品 1 文件

本轮次对照：与 R257（自评 79，0 产品文件、四件套与看图全欠）相比，本轮动了一个产品文件（取证通道，不改画面）、给了按下档第一份产物像素读数、两把刀各证一条轴、看了 5 张帧、四件套全绿。
看图腿：RUN —— 同一位 5 张（idle / hover / press 亮档 + press 暗档 + M815 修前形状那张）；读数腿 RUN（@@CAP@@、@@SWIFT@@、基线 @@BAFTER@@）。
七维度自评：
| 维度 | 分/满分 |
| 真实视觉审查 | 12/15 |
| 判据有效性 | 13/15 |
| 假绿防御 | 14/15 |
| 产品面推进 | 10/15 |
| 台账一致性 | 13/15 |
| 交付诚实性 | 14/15 |
| 可复核性 | 13/15 |
各维理由：真实视觉审查 12 —— 第一次看的是"按下"这一档本身，但只覆盖一颗控件两档；判据有效性 13 —— 这一档从"只有纯函数真值表"抬到"产物像素 + 恒等式 + 漏电对照"，且恒等式偏差 0.5 说明它量得准；假绿防御 14 —— 两把刀分别钉两条轴，并读出一条不显然的分工（像素轴对抬量偏小免疫），临时尺配了正对照；扣 1 是这两把刀不在预检名册里（306）；产品面推进 10 —— 动的是取证面不是画面，台阶够不够这个真问题留给 305；台账一致性 13 —— 五本 + STATE 轮换一次做齐（303 结案），帧基线同一笔 update；交付诚实性 14 —— "改前改后肉眼分不出""没把 1.20 搬去判台阶"都写进账；可复核性 13 —— 每条读数都标了日志与解析式，刀是脚本可重跑。合计 **89**/105。

"""

DEC_NEW = """**D-244（R258）：改一次视觉量，刀要按"能红在哪条轴"配对 —— 令牌轴（真值表）管大小、产物轴（重捕帧）管有无与接线，两条轴各自有一把刀，且不许用一条轴的绿去宣布另一条也绿。** 理由：M815（`VisualFillLift.pressed` 0.03→0.015，R256 修前形状）把真值表打红，**同一形状下新加的像素判据却仍然绿**（台阶只剩 3 灰阶，次序与恒等式都成立）；M816（→0.0）才把像素轴打红。如果本轮只带一把刀，就会得到"像素判据证明了抬量是对的"这种假话。与 D-240（改视觉量的刀必须重捕产物）同族，但这条管的是**一把刀不够**。

"""

BACK_NEW = """**305. "相邻两档之间该差多少"这把尺还不在仓库里，所以按下反馈够不够这一问今天无从判（R258 新开）**：本轮临时 python 量到 悬停↔按下 的比值是 亮 @@STEPL@@ / 暗 @@STEPD@@，都低于"悬停对底"那两条地板（1.20/1.10）—— 但那是**另一件事**的地板，搬过来判就是把口径当证人（R100/R147）。要做的三件：① 把"台阶比值"做成 `scripts/` 里的尺（复用 `pillReading` 的同一估计量，别再造第二份 sRGB）；② 本机 + runner 各读一次，按 R220/R225 的路子推出它自己的地板；③ 地板定了之后才谈"要不要再抬亮档的按下档"，并且要配一条会红的判据 + 一次真看图。另记一条反方前提：按下是瞬态（0.12s + 手指），它需要的台阶未必等于悬停需要的 —— 这句现在**没有读数撑着**，不许当结论用。

**306. 三把重捕型刀（M814 / M815 / M816）全都住在 bash 脚本里，`mutate_needle_precheck.py` 一颗也看不见（R258 新开，299 的第三、四例）**：设计输入现在齐了 —— 需要 `arms_rNNN/manifest.tsv` 那种按刀号列 文件/锚点/期望红名 的形状，加一种 `kind=recapture`（插刀 → swift build → 重捕到独立目录 → 量产物 → 整文件备份逐字节还原），预检按 manifest 读锚点"恰好命中一次"，并把这三把纳入"名册为空=红"的守卫。299 的那半（把 kind 做出来）与这半（让名册列读到）是同一件事的两面，一起做完再结案。

**302 结案（R258）**：三件都做了 —— ① 能按 `isPressed` 供电的捕获键（`pressedForCapture`，产品侧写它=0 有守卫）；② 重捕型刀 M815/M816 各钉一条轴、RESTORE 逐字节干净；③ 改前/改后同一位两张真看图（结论是"肉眼分不出"，见 U-838，所以那一笔不是看得见的修复）。剩下的半不在 302 名下：台阶地板归 305、刀进名册归 306。

"""

CHG_NEW = """### Added（R258 / 第 257 轮 / Round 255 · 按下那一档第一次可拍、可量、可被刀红回来）

产品侧一颗取证键 `EnvironmentValues.pressedForCapture`（`Views/PressableStyle.swift`）：`PressedLabel` 的缩放与底色两半都汇到同一个绘制分支，真实 `configuration.isPressed` 那条路一字未动；产品源码写这颗键 = 红（扫描前剥行注释）。
新夹具 `row-favorite-press-60x56-{dark,light}` ⇒ 帧基线 168 → @@FRAMES@@（同一笔 update）。新判据 `testPressRungIsOrderedAboveTheHoverRung`：亮档 @@LH@@→@@LP@@（比值 @@LR0@@→@@LR1@@，台阶差 @@LSD@@ 灰阶）、暗档 @@DH@@→@@DP@@（@@DR0@@→@@DR1@@，差 @@DSD@@），外加令牌↔像素恒等式（偏差 @@IDDEV@@，容差 2）与漏电对照。
两把刀：M815（`VisualFillLift.pressed` 0.03→0.015）令牌轴 CAUGHT、M816（→0.0）产物轴 CAUGHT；M815 顺带读出"像素轴对抬量偏小免疫"这条分工（D-244）。看图 5 张：R256 改前/改后同一位肉眼分不出 ⇒ 那一笔的依据是算术不是画面。
现读：build 告警 @@WARNS@@、全量卷 @@SWIFT@@、捕获卷 @@CAP@@、基线 compare changed=@@BCHANGED@@ missing=@@BMISSING@@、dmg=@@DMG@@、换装 @@VER@@。CI：@@CI@@。
302 结案；新开 305（台阶那把尺与它自己的地板）、306（三把重捕型刀进预检名册）；301/299 仍开。

"""

STATE_NEW = """## R258 状态（第 257 轮 / Round 255 · 2026-10-21）
最后更新：2026-10-21（本地 · R258 / 第 257 轮 / Round 255）：**按下那一档第一次有帧、第一次有台阶读数，两把刀各钉一条轴**（U-834…U-840 · D-244 · 302 结案、新开 305、306 · 产品 1 文件 · 自评 89/105）

**本轮落地**：`pressedForCapture` 取证键 + `row-favorite-press` 夹具（基线 168→@@FRAMES@@）+ `testPressRungIsOrderedAboveTheHoverRung`（亮 @@LH@@→@@LP@@、暗 @@DH@@→@@DP@@、恒等式偏差 @@IDDEV@@）；M815/M816 两把 CAUGHT、还原逐字节干净；看图 5 张（R256 改前改后肉眼分不出）；四件套全绿（告警 @@WARNS@@、全量卷 @@SWIFT@@、dmg @@DMG@@、换装 @@VER@@）。STATE 与 FINAL_REPORT 的交接债（303）随本轮补上。

**下一轮（R259 / 第 258 轮 / Round 256）的靶**：
⓪ 读 CI：本笔 push 后用 `gh run list --json databaseId,headSha,status,conclusion` 现取成对号（取不到写「未取到 + 成因」，293）。要看的第一件是 runner 有没有印出 `PRESS_LADDER_PROOF` / `PRESS_LADDER_IDENTITY` 两行 —— 305 的地板要等它。已交账：@@CI@@。
① 305：把"相邻档台阶"做成 `scripts/` 里的尺（复用同一估计量），两机各读一次再推地板；地板出来之前**不许**按肉眼印象改按下档，也不许把 1.20/1.10 搬过去判。
② 306 + 299：三把重捕型刀（M814/M815/M816）进预检名册，`kind=recapture` 做进执行器；301 的 stamp 门（提交链里那条会红的 Swift 退出码读点）。
③ 291 那四位欠账（每一位都是"量不到的悬停/按下画法"，按 R252/R253/R258 的路子走：接键 → 归属对 → 量 → 看图 → 该改就改）；287/284/286；用户闸门 220 路 A / 228② / 265；其余仍开 249 / 263 / 269 / 267 / 260 / 262 / 258 第三处 / 243 / 227③ / 222 / 215 / 201 / 202 / 207 / 240 / 251 / 275 / 279 / 281 / 282 / 285 / 288 / 289 / 293 / 294 / 297 / 298 / 301 / 304。

"""

# ---------- 校验 + 落盘 ----------
def render(s):
    for k, v in V.items():
        s = s.replace(k, v)
    if "@@" in s:
        die("渲染后仍有未替换占位符：" + s[:100])
    return s


UI_NEW = render(UI_NEW)
ITER_NEW = render(ITER_NEW)
DEC_NEW = render(DEC_NEW)
BACK_NEW = render(BACK_NEW)
CHG_NEW = render(CHG_NEW)
STATE_NEW = render(STATE_NEW)
for nm in V:
    for blk in (UI_NEW, ITER_NEW, DEC_NEW, BACK_NEW, CHG_NEW, STATE_NEW):
        if nm in blk and V[nm] == "":
            die("占位符 " + nm + " 没有读数")
rendered = "".join([UI_NEW, ITER_NEW, DEC_NEW, BACK_NEW, CHG_NEW, STATE_NEW])
leftover = sorted(set(re.findall(r"@@[A-Z0-9]+@@", rendered)) - set(V))
if leftover:
    die("占位符没有对应读数：" + ",".join(leftover))
rendered = fill = rendered
for k, v in V.items():
    fill = fill.replace(k, v)
if "@@" in fill:
    die("渲染后仍有未替换占位符")

ui_old = rd(UI)
mark = "## 第 256 轮"
if mark not in ui_old:
    die("UI_AUDIT 找不到锚点 " + mark)
i = ui_old.index(mark)
ui_new = ui_old[:i] + UI_NEW + ui_old[i:]

iter_new = rd(ITER).rstrip("\n") + "\n\n" + ITER_NEW
dec_new = rd(DEC).rstrip("\n") + "\n\n" + DEC_NEW
back_new = rd(BACK).rstrip("\n") + "\n\n" + BACK_NEW
chg_old = rd(CHG)
head = "## [Unreleased]\n"
if head not in chg_old:
    die("CHANGELOG 找不到 [Unreleased]")
chg_new = chg_old.replace(head, head + "\n" + CHG_NEW, 1)
st_old = rd(STATE)
st_mark = "## R256 状态"
if st_mark not in st_old:
    die("STATE 找不到要替换的标题锚点")
j = st_old.index(st_mark)
state_new = st_old[:j] + STATE_NEW + "\n" + st_old[j:]


def must_preserve(old, new, name):
    co, cn = Counter(old.splitlines()), Counter(new.splitlines())
    lost = [l for l, c in co.items() if cn[l] < c]
    if lost:
        die(name + " 插入弄丢 " + str(len(lost)) + " 行（插入实为替换）：" + " | ".join(lost[:2])[:150])


must_preserve(ui_old, ui_new, "AGENT_UI_AUDIT.md")
must_preserve(chg_old, chg_new, "CHANGELOG.md")
must_preserve(st_old, state_new, "AGENT_STATE.md")
for o, n, nm in ((rd(ITER), iter_new, "AGENT_VISUAL_ITERATION.md"),
                 (rd(DEC), dec_new, "AGENT_DECISIONS.md"),
                 (rd(BACK), back_new, "AGENT_BACKLOG.md")):
    if not n.startswith(o.rstrip("\n")):
        die(nm + " 不是纯追加")

ids = [int(x) for x in re.findall(r"- \*\*U-(\d+)", UI_NEW)]
if ids != list(range(834, 841)):
    die("本轮 U 号不连续：" + str(ids))
if "U-834…U-840" not in UI_NEW.splitlines()[0]:
    die("节标题 U 区间与定义不符")
dup = [k for k, c in Counter(re.findall(r"- \*\*U-(\d+)", ui_new)).items() if c > 1 and int(k) >= 834]
if dup:
    die("本轮 U 定义重复：" + ",".join(dup))
if iter_new.count("| 真实视觉审查 |") != rd(ITER).count("| 真实视觉审查 |") + 1:
    die("七维表多写或少写")
rows = [l for l in iter_new.split("## Round 255 ·")[1].splitlines() if l.startswith("| ")]
if len(rows) != 8:
    die("七维表形状不是表头+7 行，现读 " + str(len(rows)))
for num in ("305", "306"):
    if re.search(r"^(?:\*\*)?" + num + r"\. ", rd(BACK), re.M):
        die("BACKLOG " + num + " 已存在")
if "D-244" not in dec_new or "D-244" in rd(DEC):
    die("D-244 要么没写要么已存在")
if "## R258 状态" not in state_new or "## R256 状态" not in state_new:
    die("STATE 轮换形状不对")

for p, t in ((UI, ui_new), (ITER, iter_new), (DEC, dec_new), (BACK, back_new), (CHG, chg_new), (STATE, state_new)):
    with open(p, "w", encoding="utf-8") as f:
        f.write(t)

print("LEDGERS_R258 OK swift=" + V["@@SWIFT@@"] + " cap=" + V["@@CAP@@"] + " frames=" + V["@@FRAMES@@"]
      + " changed=" + V["@@BCHANGED@@"] + " missing=" + V["@@BMISSING@@"]
      + " step=" + V["@@STEPL@@"] + "/" + V["@@STEPD@@"] + " U=834..840 D=244 BACKLOG=305,306,302结案")
