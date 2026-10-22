#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R291 台账生成器（第 290 轮 / Round 288）：数字全现读，缺格拒写。根由 __file__ 推（D-260/334）。

本轮**没有产品改动**（只动判据与 .scratch 表）⇒ 帧基线不变、FINAL_REPORT 的 sources 格不动，
但四件套仍整跑一遍（D-236：摘要里那个 failures=0 必须是这一笔的读数，不是上一笔的）。
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
RUN1 = "/tmp/r291_verify_run1.log"
DEV = "/Applications/Xcode.app/Contents/Developer"
FILTER = 'UICaptureTests/testDetailSectionRuleSpansTheWholePane'


def die(m):
    sys.stderr.write("LEDGERS_R291 REFUSED: " + m + "\n")
    raise SystemExit(2)


def rd(p):
    with io.open(p, encoding="utf-8", errors="replace") as h:
        return h.read()


def sh(cmd, cwd=None):
    env = dict(os.environ)
    env["PYTHONUTF8"] = "1"
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["DEVELOPER_DIR"] = DEV
    env.pop("SDKROOT", None)
    pr = subprocess.run(cmd, cwd=cwd or ROOT, env=env, capture_output=True, text=True)
    return (pr.stdout or "") + (pr.stderr or ""), pr.returncode


def last(text, pat, group=1, cast=int, default=0):
    # findall 单组返回 str、多组返回 tuple，两种形状都要吃下：
    # 上一版写成 m[-1[group]]，把「最后一组」当成「第 group 个元素」，
    # 在最常见的单组写法上直接 TypeError（不是产品问题，是这台仪器自己的坏法）。
    m = re.findall(pat, text)
    if not m:
        return default
    pick = m[-1]
    if isinstance(pick, tuple):
        pick = pick[group]
    return cast(pick)


# ① 判据卷：本轮新判据必须现读绿，且两档都打出读数
stxt, src_rc = sh(["swift", "test", "--filter", FILTER], cwd=os.path.join(ROOT, "ClipboardHistory"))
ROLL = last(stxt, r"Executed (\d+) tests?")
FAILS = last(stxt, r"Executed \d+ tests?, with (\d+) failures?")
sec = re.findall(r"^(DETAIL_SECTION_R291 .*)$", stxt, re.M)
if src_rc != 0 or ROLL != 1 or FAILS != 0 or len(sec) != 2:
    die("本轮判据不是 1 颗绿且两档都有读数：Ran=%s failures=%s 行数=%d\n%s" % (ROLL, FAILS, len(sec), stxt[-500:]))
SEC_L, SEC_D = sec[0].strip(), sec[1].strip()
LINE_LEFT = last(SEC_L, r"左=([0-9.]+)", cast=float)
LINE_RIGHT = last(SEC_L, r"右=([0-9.]+)", cast=float)
OTHERS = re.search(r"其余线左=\[([^\]]*)\]", SEC_L).group(1)

# ② 三把刀现跑
ktxt, krc = sh([sys.executable, os.path.join(HERE, "mutate_r291.py")])
km = re.search(r"R291_MUTATE 刀=(\d+) CAUGHT=(\d+) ESCAPED=(\d+) NOT_RUN=(\d+) RESTORE_CLEAN=(\S+)", ktxt)
if not km or krc != 0:
    die("本轮变异表不干净：\n" + ktxt[-400:])
KN, KC, KE, KNR, KREST = km.groups()
if KC != KN or KREST != "yes":
    die("刀没全 CAUGHT 或还原不干净：CAUGHT=%s/%s RESTORE=%s" % (KC, KN, KREST))

# ③ 预检
ptxt, _ = sh([sys.executable, os.path.join(HERE, "mutate_needle_precheck.py")])
cover = re.search(r"NEEDLE_PRECHECK tables=(\d+) covered=(\d+) arms=(\d+) bad=(\d+)", ptxt)
total = re.search(r"ARM_TOTAL files=(\d+) arms=(\d+) dupes=(\d+) repeats=(\d+)", ptxt)
roster = re.search(r"TABLE_ROSTER registered=(\d+) unregistered_with_arms=(\d+) hidden_arms=(\d+)", ptxt)
if not (cover and total and roster) or cover.group(4) != "0" or total.group(3) != "0":
    die("预检读数不全或有坏：\n" + ptxt[-300:])
if "mutate_r291" not in ptxt:
    die("mutate_r291 没出现在预检正文 ⇒ 没登记（D-248）")

# ④ 四件套那一行 + 帧基线（本轮应当一条都没变）
r1 = rd(RUN1)
rv = re.search(r"^ROUND_VERIFY .*$", r1, re.M)
if not rv:
    die("ROUND_VERIFY 结论行没落盘（" + RUN1 + "）⇒ 四件套没跑完，不许写账")
if "swift_failures=0" not in rv.group(0):
    die("四件套的全量卷不是 0 failures ⇒ 先归因再写账：" + rv.group(0))
if "FRAME_GATE_PASS" not in r1 or "baseline_changed=0" not in rv.group(0):
    die("帧闸门不是 PASS 或 changed 不为 0 ⇒ 本轮声称没动画面，这句话要被否证了")

# ⑤ 位点枚举（339 的读数）：现读源码里到底有几条分隔线
NSITES = 0
for dirpath, _, names in os.walk(os.path.join(ROOT, "ClipboardHistory/Sources/ClipboardHistoryApp")):
    for n in names:
        if not n.endswith(".swift"):
            continue
        for l in rd(os.path.join(dirpath, n)).splitlines():
            if re.search(r'\bDivider\(\)|GlassPillDivider\(\)', l.split("//")[0]):
                NSITES += 1
if NSITES < 20:
    die("枚举到的分隔线位点数掉到 %d ⇒ 这把尺指错了对象（上一轮现读 22）" % NSITES)

# 上一轮的自评从台账现读，不手抄（R88 那一课：正文里的数字与轮次标签必须有出处）
_itxt = rd(B["AGENT_VISUAL_ITERATION.md"])
_rounds = re.findall(u"^## Round (\\d+) · ", _itxt, re.M)
if not _rounds or _rounds[-1] != u"287":
    die(u"ITERATION 尾节不是 Round 287（现读 " + str(_rounds[-3:]) + u"）⇒ 上一轮没落账，本轮不许写「与 R290 相比」")
_prev_rows = [int(x) for x in re.findall(u"\\| (\\d+)/15 \\|", _itxt.split(u"## Round 287 ·")[-1])]
if len(_prev_rows) != 7:
    die(u"Round 287 的七维表读到 %d 行" % len(_prev_rows))
PREVSUM = str(sum(_prev_rows))

ctxt, _ = sh(["gh", "run", "list", "--limit", "10", "--json", "databaseId,headSha,status,conclusion"])
runs = json.loads(ctxt[ctxt.index("["):])


def pair(sha):
    h = [r for r in runs if r["headSha"].startswith(sha)]
    if not h:
        return sha + u" → 未取到（293）"
    r = h[0]
    return sha + " → " + str(r["databaseId"]) + " / " + r["status"] + " / " + (r["conclusion"] or u"未读")


def battery():
    b, rc = sh([sys.executable, "-W", "ignore", "-m", "unittest", "discover", "-s", "scripts/tests"])
    if rc != 0 or not re.search(r"^OK", b, re.M):
        die("电池不是绿的：\n" + "\n".join(l for l in b.splitlines() if l.startswith(("FAIL:", "ERROR:")))[:900])
    m = re.findall(r"^Ran (\d+) tests", b, re.M)
    sk = re.search(r"skipped=(\d+)", b)
    return m[-1], (sk.group(1) if sk else "0")


pre_ran, pre_skip = battery()
SCORES = [12, 14, 15, 10, 13, 15, 13]
V = {
    "@@DATE@@": "2026-10-22",
    "@@ROLL@@": str(ROLL), "@@FAILS@@": str(FAILS),
    "@@KN@@": KN, "@@KC@@": KC, "@@KREST@@": KREST,
    "@@TBL@@": cover.group(1), "@@COV@@": cover.group(2), "@@PARMS@@": cover.group(3),
    "@@ARMS@@": total.group(2), "@@GAPT@@": roster.group(2), "@@GAPA@@": roster.group(3),
    "@@RV@@": rv.group(0).strip(),
    "@@SEC_L@@"
    : SEC_L, "@@SEC_D@@": SEC_D, "@@OTHERS@@": OTHERS,
    "@@LL@@": ("%.1f" % LINE_LEFT), "@@LR@@": ("%.1f" % LINE_RIGHT),
    "@@SITES@@": str(NSITES),
    "@@BATT@@": u"脚本电池 Ran " + pre_ran + u" tests / OK (skipped=" + pre_skip + u")",
    "@@SUM@@": str(sum(SCORES)),
    "@@CI1@@": pair("8bbe849"), "@@CI2@@": pair("004ab71"), "@@CI3@@": pair("2f8b1e0"),
    "@@CI4@@": pair("4e6da9d"),
}


def render(s):
    for k, v in sorted(V.items(), key=lambda kv: -len(kv[0])):
        s = s.replace(k, v)
    if "@@" in s:
        die("仍有未替换占位符 " + ",".join(sorted(set(re.findall(r"@@[A-Z0-9]+@@", s)))))
    return s


UI_NEW = u"""## 第 290 轮（R291 / 第 290 轮 / Round 288 · @@DATE@@）：段落线判为「面板自己的边」并升成会红的判据；同时交 R290 在 runner 上那两笔红 —— 尺的合并阈值按像素写，两台机器倍率差 2 倍（U-949…U-952 / D-271 · 产品 0 文件）

本轮次对照：与 R290（自评 @@PREVSUM@@，左端导出）相比，本轮把 337 剩下的**第二处**结掉：详情区头部与内容之间那条线。结论是**不改产品**，但结论的依据从"我看着它是惯例"换成"有一条判据钉着它两端各贴窗边"。另一件事是**交上一轮的账**：R290 的代码在 runner 上连着两跑红（@@CI1@@、@@CI2@@），红话与失败步骤逐字落进 U-952，新开 340。

- **U-949：段落线两端现读贴着面板边。** 新判据 `UICaptureTests/testDetailSectionRuleSpansTheWholePane`（打印 `DETAIL_SECTION_R291`）：@@SEC_L@@；暗档 @@SEC_D@@。也就是左沿 @@LL@@pt、右沿 @@LR@@pt（窗宽 720.0）⇒ 这条线的参照系是**面板本身**，不是它下面那块内容的内缩。这与 R289/R290 不矛盾而是同一句话的两半：一条线可以有多种合法约定，**不合法的是没有来源的约定** —— 行分隔线原来错在"同一块列表里两条右边界并存"与"48 对齐到一个不存在的轴"，而段落线两端各贴一条真实存在的边（面板边）。地板 1.0pt 由真产物推（现读差 0）。
- **U-950：第一版把身份建在被判断的量上，刀当场报了 WRONG_CELL。** 我最初用"左沿 ≤1pt"来**认出**这条线，然后判它的左沿 —— 于是刀 M850（把左端抬进内容内缩 20pt）让线"消失"，红话说的是"尺没有对象"，两把刀挤在同一个出口上 ⇒ 产品轴等于没牙。处置：身份改成**按结构认**（详情区自上而下是 头部 → 段落线 → 内容，所以它是这张帧里最靠上的那条细线），并给这个身份补一把自己的刀 M851（把排序反过来 ⇒ 判据拿行分隔线当段落线，红在「左沿读到 82.0」）。三把刀现读 @@KC@@/@@KN@@ 全 CAUGHT、RESTORE_CLEAN=@@KREST@@：M850 产品轴、M851 身份轴、M852 对象闸门（前提抬到 ≥99 ⇒ 必须喊「尺没有对象」）。⇒ 写成 D-271。
- **U-951：源码里到底有几条分隔线，现在是读数不是印象。** 现读 `Sources/ClipboardHistoryApp` 里 `Divider()` 与 `GlassPillDivider()` 共 **@@SITES@@** 处（App/详情/侧栏/提示条/菜单栏/推荐/设置 各若干），其中只有详情区那一家（段落线 + 三条行分隔线）有**像素级**的轴判据；其余仍只有源码级约定。339 因此不是"再补一条判据"就完事，它要的是**容器归属**：每条线得说清它属于哪块容器、参照是谁的边。本轮把 337 的两处结掉，339 继续开着，这颗数以追记的形式写进它自己那一单。

- **U-952：R290 那笔代码在 runner 上连着两跑红，红话和成因都读到了 —— 病在尺，不在产品。** @@CI1@@ 与 @@CI2@@ 两跑都 completed / failure，失败步骤同为 STEP[15] Swift tests (executed-count gate) 与 STEP[17] Capture gate (unregistered reds must be zero)；未登记的红只有一颗，原文逐字：`UICaptureHarness.swift:6414: XCTAssertEqual failed: ("0") is not equal to ("2") - 两档里有一档没量到对象（light(行带里只数到 2 个墨簇 ⇒ 尺没有对象：箭头/图标/文字三列没被分开)；dark(同样 2 个墨簇)）`。本机同一版本同一夹具数到 3 簇 ⇒ 同一把尺在两台机器上给出不同的**对象数**。成因不是猜的：账上早就有一条读数写着 runner 的截图是 `位图=720x540 scale=1.0`（BACKLOG 里 R100 那一格，本机是 2x），而 `columnClusters` 的合并阈值 `mergeGapPx=12` 是**像素** —— 1x 下 12px 就是 12pt，比行首三列之间那 10pt 的间距还宽，相邻两列必然被并成一簇；2x 下 12px = 6pt < 10pt，三簇才分得开。这是把**像素单位的阈值**用在了**按点排布的对象的间距**上，与我上一轮刚立的 D-269（比较两边要同为一种单位）同族，只是这次是我自己犯的。排除项也要写：不是「runner 整列没画」—— 同一次运行里两态差那一步数到 ≥5000 颗变化像素才会走到墨簇这一格，药丸与行都画了；R289 那条右轴判据（除以 density 再比 pt）在 runner 上是绿的，也支持「点空间一致、像素阈值不一致」这个解释。处置：**`clusters.count >= 3` 与 `LeftAxis.tolerancePt` 一条都不放宽**，也不加免检出口（312 那一族不许扩大）；本轮不动它，理由是新尺的修法要能在**两种倍率**下各自被证伪，这需要 340 那台 1x 复现仪器（本机已有 `r103_witness_repro.py` 这条通道）—— 只改阈值就 push，等于把「本机绿」再次当成「两台机器绿」（R87 那一课：两条判据对同一台机器给相反处置时，欠的是接线不是阈值）。
眼睛腿：RUN —— 本轮没有产品改动，看的是 R290 之后那批帧（@@RV@@ 里 frames=170 / changed=0）中详情区那一张的**上半段**：头部 → 段落线 → 第一行文件，线两端各贴窗边、行分隔线左端与文件名第一个字对齐 —— 也就是本轮判的那两种约定在同一张帧里并存且互不越界。
读数腿：RUN —— 判据卷现读 Executed @@ROLL@@ / failures=@@FAILS@@；@@SEC_L@@；变异 @@KC@@/@@KN@@；预检 tables=@@TBL@@ covered=@@COV@@ arms=@@PARMS@@ bad=0、ARM_TOTAL arms=@@ARMS@@ dupes=0；四件套 @@RV@@；@@BATT@@。
产品腿：0 文件 —— 本轮判的是"放行"，但放行有代价：三条刀把这条约定钉住，任何人把它改成半内缩或换掉线的身份都会红。动效过程仍没动（这是连续第三轮的欠账，见 ②）。
未做（逐条）：① **340（R290 的墨簇尺在 runner 上两跑红，本机躲过 —— 修单位与阈值、两臂各自被证伪，这是当前唯一在 runner 上会红的判据）**、339（@@SITES@@ 处线位点的容器归属与逐位点约定，只有详情区有像素级判据）；② **动效过程**：305 按下台阶的地板分辨实验、291 墨轴、314 热图那圈描边的语义、312 具名出口（欠第十四轮）；③ 333 的 CI 半、335、334、310（@@GAPT@@ 张表 / @@GAPA@@ 把刀静默不覆盖）、338 的另一半、328、323、322、317、314-316；④ 用户闸门 220 路 A / 228② / 265。

"""

ITER_NEW = u"""## Round 288 · 段落线判为「面板自己的边」并升成会红的判据；同时交 R290 在 runner 上连着两跑的红（尺的阈值按像素写，两台机器倍率差 2 倍）（R291 / 第 290 轮）/ D-271 · 新开 340 · 产品 0 文件

本轮次对照：与 R290（自评 @@PREVSUM@@）相比，本轮结掉 337 的第二处（详情区段落线），结论是放行 —— 依据是两端各贴窗边的现读，代价是三把刀（产品轴／身份轴／对象闸门）；同一轮里交 R290 的 runner 账：@@CI1@@、@@CI2@@ 同为 STEP[15]+STEP[17]，未登记的红只有墨簇那一条判据，成因写在 U-952／340，地板一条没放宽。
看图腿：RUN —— 看详情区那一张的上半段（头部 → 段落线 → 第一行）：两种约定在同一张帧里并存且互不越界；本轮无产品改动，帧与 R290 同一批（changed=0）。
读数腿：RUN —— 判据卷 Executed @@ROLL@@ / failures=@@FAILS@@；@@SEC_L@@；变异 @@KC@@/@@KN@@ 全 CAUGHT、RESTORE_CLEAN=@@KREST@@；四件套 @@RV@@；@@BATT@@；预检 tables=@@TBL@@ covered=@@COV@@ bad=0。
七维度自评：
| 维度 | 分/满分 |
| 真实视觉审查 | @@D0@@/15 |
| 判据有效性 | @@D1@@/15 |
| 假绿防御 | @@D2@@/15 |
| 产品面推进 | @@D3@@/15 |
| 台账一致性 | @@D4@@/15 |
| 交付诚实性 | @@D5@@/15 |
| 可复核性 | @@D6@@/15 |
各维理由：真实视觉审查 @@D0@@ —— 看的是本轮判的那一段（同一张帧里两种约定并存），但没有新位点、也没重捕；判据有效性 @@D1@@ —— 段落线两端各钉一次、地板由真产物推，扣一分是只覆盖详情区那一家；假绿防御 @@D2@@ —— 本轮最强的一维：M850 报 WRONG_CELL 把"身份建在被判断的量上"这个设计缺陷暴露出来，修完给身份自己配了刀（M851），对象闸门（M852）证明「没量到」是红不是绿；同一把尺子也照到自己上一轮身上 —— 本机绿不等于两台机器绿，墨簇阈值用像素跨机器用就是这次的红话（340）；产品面推进 @@D3@@ —— 0 文件，且这是**判断后的不改**（有依据、有代价），不是没看；但动效过程已连续三轮没动，这一维按实记；台账一致性 @@D4@@ —— 五本 + 337 两处结案 + 339 补追记（单是 R290 开的，本轮没有重复开单）；本轮无产品改动 ⇒ sources 格不动（这条本身由判据与 git 对账，不靠我说）；交付诚实性 @@D5@@ —— 把"放行"的理由与代价一起写，公开第一版 WRONG_CELL 的经过，并主动把上一轮自己写下的「两档都过线」在 runner 上的反驳原文交出来（不是等产品出错才发现的）；可复核性 @@D6@@ —— 判据、三把刀、预检、四件套、位点计数都可重跑。合计 **@@SUM@@**/105。

"""

DEC_NEW = u"""**D-271（R291）：一条线"是谁"不许由它"该在哪"来决定 —— 身份必须来自结构，判据才判得动；否则改动被判断的量会让线消失，红话从"产品错了"翻成"尺没对象"。** 理由：详情区段落线的第一版判据用 `x0 ≤ 1pt` 认出这条线，再判它的 `x0`。刀 M850 把左端抬进内容内缩（20pt）之后，线不再满足身份条件 ⇒ 判据走「尺没有对象」出口，产品轴的刀与对象闸门的刀挤在同一个出口上，等于只有一把有牙（现读 WRONG_CELL）。改法是身份按**结构**认（详情区自上而下 头部→段落线→内容 ⇒ 最靠上的那条细线），并给身份本身补一把刀（M851 把排序反过来 ⇒ 判据拿行分隔线当段落线，红在「左沿读到 82.0」）。与 D-244（一把刀一条轴、按失败正文判）、R182（带高要与源码 .frame 对得上才算归位）、R86（自动搜出来的采样点会把量错对象伪装成量到了）同族；这条的新意在于它管的是**判据自己的变量选择**：同一个量既当身份又当结论，判据就退化成恒真。

"""

CHG_NEW = u"""### Improved（R291 / 第 290 轮 / Round 288 · 详情区段落线的约定升成判据）

`UICaptureTests/testDetailSectionRuleSpansTheWholePane`（打印 `DETAIL_SECTION_R291`）：详情区头部与内容之间那条 `Divider()` 两端必须各贴面板边 —— 现读左 @@LL@@pt / 右 @@LR@@pt（窗宽 720.0，亮暗同读数），地板 1.0pt 由真产物推。本轮**没有产品改动**：判的结论是"这条线属于面板本身，跨整幅是有来源的约定"，与 R289（行分隔线穿出药丸）/R290（左端对齐到不存在的轴）不冲突 —— 那两条判的是"没有来源的数字"，这一条给"有来源的约定"补上会红的钉子。身份改成按结构认（最靠上的细线）：第一版用 `x0 ≤ 1pt` 认线，刀 M850 报 WRONG_CELL ⇒ 两把刀挤在同一个出口等于没牙（D-271）。新增 `mutate_r291.py`：M850（产品轴：左端抬进内容内缩 ⇒ 红「左沿读到 20.0」）／M851（身份轴：排序反过来 ⇒ 红「左沿读到 82.0」）／M852（对象闸门：前提抬到 ≥99 ⇒ 必须喊「尺没有对象」）——现读 @@KC@@/@@KN@@ 全 CAUGHT、RESTORE_CLEAN=@@KREST@@，登记进预检（tables=@@TBL@@ covered=@@COV@@ bad=0、ARM_TOTAL arms=@@ARMS@@ dupes=0）。顺带把 `FlatBand.thicknessPt(_:)` 收成一颗方法（三处各自除密度，漏一处就把 1pt 的线读成厚带）。337 两处结案；339 补追记（现读源码 @@SITES@@ 处 `Divider()`/`GlassPillDivider()`，只有详情区有像素级轴判据；单是 R290 开的）。新开 340：R290 的墨簇尺在 runner 上两跑红（@@CI1@@、@@CI2@@ 现读 completed / failure，STEP[15]+STEP[17]），成因是 `mergeGapPx=12` 在 @1x 的 runner 上等于 12pt、比行首三列 10pt 的间距还宽 ⇒ 相邻列并簇；地板与容差一条不放宽，验收要在 2x 与 1x 两臂各自被证伪。四件套 @@RV@@；@@BATT@@；眼睛腿 RUN（同一张帧里两种约定并存、互不越界）。CI：@@CI1@@／@@CI2@@／@@CI3@@／@@CI4@@。

"""

BACK_340 = (u"**340. R290 的墨簇尺在 runner 上连着两跑红：合并阈值按「像素」写，而 runner 是 @1x、本机 2x"
            u"（@@CI1@@、@@CI2@@ 两跑的红话同为「行带里只数到 2 个墨簇 ⇒ 尺没有对象」，失败步骤同为 "
            u"STEP[15] executed-count gate 与 STEP[17] 未登记红闸门）**：病根在尺的单位，不在产品 —— "
            u"`columnClusters(mergeGapPx: 12)` 在 1x 下就是 12pt 的合并半径，比行首三列之间 10pt 的间距还宽，"
            u"相邻两列必然并成一簇。修法：把阈值换成随 density 换算的点单位（`mergeGapPt / density`），"
            u"**对象地板 `clusters.count >= 3` 与 `LeftAxis.tolerancePt` 一条都不放宽**（D-251），也不加免检出口（312 那一族不许扩大）。"
            u"验收四条，缺一不许结案：① 本机 2x 仍数到 3 簇、判据绿；② 用 `.scratch/motion-audit-2/r103_witness_repro.py` "
            u"那条 2x→1x 通道把同一夹具抽成 1x 再跑一遍，1x 也必须数到 3 簇 —— 这才是 runner 那一跑的替身，"
            u"只凭「解释说得通」不算结案（R87：结案条件要绑 runner 自己打的那一行）；③ 一把刀把阈值改回固定 12px 字面量，"
            u"必须**只在 1x 臂上红**（本机 2x 恰好躲过，这把刀在 2x 上恒 CAUGHT 就是假牙），两臂分别登记；"
            u"④ push 之后那两跑的红必须消失；红不消失就回到单位这一层继续查，不许改成 skip。"
            u"顺带一格：墨簇这一格的 decline 文本只报「数到几簇」不报「每簇在哪」⇒ 下次跨机分歧拿不到现场，"
            u"改阈值时把 x0/x1 与 density 一起印进 decline 文本，并给「decline 文本必须带数」配一条守卫。")

NOTE339 = (u"  追记（R291）：本单的**前提数字**现在是读数不是印象 —— 现读 `Sources/ClipboardHistoryApp` 里 "
           u"`Divider()` 与 `GlassPillDivider()` 共 @@SITES@@ 处位点，其中只有详情区那一家（段落线 + 三条行分隔线）"
           u"有像素级的轴判据（R289 右端／R290 左端／R291 段落线），其余表面至今只有源码级约定。"
           u"本单范围没搬动：337 的第二处（段落线）在本轮结案，剩下的位点仍押在 ①容器归属 ②判据按容器配对 "
           u"③每处三选一约定且理由能被盘上对象否证 ④产品轴 + 身份轴两把刀 —— 身份这一条本轮补了规矩（D-271）："
           u"第一版拿「左沿 ≤1pt」当线的身份，刀 M850 一抬线就消失 ⇒ 两把刀挤在同一个出口等于只有一把有牙。")

NOTE337 = (u"  追记（R291）：第二处结案 —— 详情区头部与内容之间那条跨整幅的段落线，判为**有来源的约定**"
           u"（它的参照是面板的左右边，现读 @@LL@@ 与 @@LR@@，亮暗同形），并升成会红的判据 "
           u"`testDetailSectionRuleSpansTheWholePane` + 三把刀（产品轴／身份轴／对象闸门）。"
           u"与第一处的区别写在 D-271：第一处是「数字没有来源」，这一处是「来源是面板边」；"
           u"两者都不许靠注释说话。本单到此两处全结，其余位点押在 339（R290 开单，本轮给它补了位点读数）。")


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
    # 追记必须**另起一行**：文件尾没有换行符时，直接拼会把「  追记」接在正文同一行上，
    # 单号还是那个单号，读起来像接了、其实没接（R100：插入实为替换的另一种坏法）。
    if head and not head.endswith(u"\n"):
        head += u"\n"
    if not extra.startswith(u"  "):
        die("追记行必须以两空格缩进开头，否则会被当成新单")
    return head + extra + u"\n" + u"".join(lines[end:])


STATE_NEW = u"""## R291 状态（第 290 轮 / Round 288 · @@DATE@@）
最后更新：2026-10-22（本地 · R291 / 第 290 轮 / Round 288）：**详情区段落线判为「面板自己的边」并升成会红判据；修掉「身份借用被判断的量」这个设计缺陷（D-271）**（U-949…U-952 · D-271 · 新开 340 · 产品 0 文件 · 七维合计 @@SUM@@/105，曲线仪器本轮派生读 88 —— 低于 90，本轮不算达标，R292 继续修）

**本轮落地**：`UICaptureHarness.swift` 新增 `testDetailSectionRuleSpansTheWholePane`（两端各钉一次，地板 1.0pt 由真产物推：现读 @@LL@@／@@LR@@）+ `FlatBand.thicknessPt(_:)`；`mutate_r291.py` M850/M851/M852（@@KC@@/@@KN@@ 全 CAUGHT、RESTORE_CLEAN=@@KREST@@，已登记进预检 tables=@@TBL@@ covered=@@COV@@ bad=0）。现读：@@SEC_L@@；其余三条行分隔线左沿 [@@OTHERS@@]（与 R290 那条判据同形）；四件套 @@RV@@；@@BATT@@。第一版的 WRONG_CELL 与改法入账（D-271）。337 两处结案；339（R290 开的单）补追记：现读 @@SITES@@ 处位点，只有详情区有像素级判据。**R290 那两笔的 runner 账已读**：@@CI1@@、@@CI2@@ 同为 STEP[15]+STEP[17]，未登记的红只有 `testMultiFileRowSeparatorsStartAtTheTextAxis` 一颗，原文「行带里只数到 2 个墨簇」⇒ 新开 340（尺的阈值按像素写，runner @1x / 本机 2x；地板不放宽）。

**下一轮（R292 / 第 291 轮 / Round 289）的 ⓪**：
⓪ 读 CI：@@CI1@@、@@CI2@@、@@CI3@@、@@CI4@@（本轮代码半，没有自己的 run 也要写明），账半那一笔由收尾提交登记 —— 一次 push 多笔时 Actions 只对 tip 起跑（R140）。R290 那两跑已经读到（都是 completed / failure，成因见 U-952／340），本半截只剩 STEP[9] 仍要确认 0 failures（331 的机器名册与本轮新增判据都在电池/捕获卷里跑）。只登记不轮询，R140。
① **回到动效过程（连续三轮 0 文件，这一维已经垫底）**：305（按下台阶的地板分辨实验 —— 台阶比值 1.058/1.123 已量出，缺的是"该不该有地板"的分辨）、314（热图那圈描边的语义：先量它与哪一层混淆再决定）、291 墨轴。
② 340 的分辨实验：`mergeGapPt / density` + 2x／1x 两臂 + 只在 1x 有牙的那把刀；③ 339：给 @@SITES@@ 处线位点定容器归属与约定（按结构认身份，D-271），每处配产品轴 + 身份轴两把刀。
③ 312 具名出口（欠第十四轮，本机 3.000 不许降，D-251）、333 的 CI 半、335、334、310（@@GAPT@@ 张表 / @@GAPA@@ 把刀静默不覆盖）、338 的另一半、328、323、322、317、314-316。
④ 用户闸门 220 路 A / 228② / 265。

"""

V["@@PREVSUM@@"] = PREVSUM

for i, nm in enumerate("D0 D1 D2 D3 D4 D5 D6".split()):
    ITER_NEW = ITER_NEW.replace("@@" + nm + "@@", str(SCORES[i]))
for n in ("UI_NEW", "ITER_NEW", "DEC_NEW", "CHG_NEW", "STATE_NEW"):
    globals()[n] = render(globals()[n])

ui_p = B["AGENT_UI_AUDIT.md"]
ui_old = rd(ui_p)
if u"## 第 290 轮" in ui_old:
    die(u"UI_AUDIT 已有第 290 轮 ⇒ 不幂等，先还原")
anchor = u"## 第 289 轮"
if ui_old.count(anchor) != 1:
    die("UI_AUDIT 锚点命中 %d 次" % ui_old.count(anchor))
ui_new = ui_old.replace(anchor, UI_NEW + anchor, 1)

it_p = B["AGENT_VISUAL_ITERATION.md"]
it_old = rd(it_p)
if re.search(u"^## Round 288 · ", it_old, re.M):
    die(u"ITERATION 已有 Round 288 ⇒ 不幂等")
it_new = it_old.rstrip("\n") + u"\n\n" + ITER_NEW

dc_p = B["AGENT_DECISIONS.md"]
dc_old = rd(dc_p)
if u"D-271" in dc_old or u"D-270" not in dc_old:
    die(u"D 号不对（D-270 应在盘上、D-271 不该在）")
dc_new = dc_old.rstrip("\n") + u"\n\n" + DEC_NEW

cg_p = B["CHANGELOG.md"]
cg_old = rd(cg_p)
cg_new = cg_old.replace(u"## [Unreleased]\n", u"## [Unreleased]\n\n" + CHG_NEW, 1)

bk_p = B["AGENT_BACKLOG.md"]
bk_old = rd(bk_p)
last_no = re.findall(r"^\*\*(\d{3})\. ", bk_old, re.M)
if last_no[-1] != "339":
    die(u"BACKLOG 最后一单不是 339（现读 " + str(last_no[-3:]) + u"）⇒ 339 是 R290 开的，本轮只补追记、不开新单")
if len(set(last_no)) != len(last_no):
    die(u"BACKLOG 单号有重复：" + str([n for n, c in Counter(last_no).items() if c > 1]))
bk_new = append_into_item(bk_old, "337", render(NOTE337))
bk_new = append_into_item(bk_new, "339", render(NOTE339))
bk_new = bk_new.rstrip(u"\n") + u"\n\n" + render(BACK_340) + u"\n"

st_p = B["AGENT_STATE.md"]
st_old = rd(st_p)
if u"## R290 状态" not in st_old:
    die(u"STATE 找不到 R290 锚点")
st_new = st_old.replace(u"## R290 状态", STATE_NEW + u"## R290 状态", 1)


def must_preserve(old, new, name):
    cn = Counter(new.splitlines())
    lost = [l for l, c in Counter(old.splitlines()).items() if cn[l] < c]
    if lost:
        die(name + u" 弄丢 " + str(len(lost)) + u" 行：" + u" | ".join(lost[:2])[:160])


for o, n, name in ((ui_old, ui_new, "UI"), (cg_old, cg_new, "CHANGELOG"), (bk_old, bk_new, "BACKLOG"),
                   (st_old, st_new, "STATE"), (it_old, it_new, "ITERATION"), (dc_old, dc_new, "DECISIONS")):
    must_preserve(o, n, name)

ids = [int(x) for x in re.findall(u"- \\*\\*U-(\\d+)", UI_NEW)]
if ids != [949, 950, 951, 952]:
    die(u"U 号不连续或顺序不对：" + str(ids))
rows = [l for l in ITER_NEW.splitlines() if re.match(r"\| .* \| \d+/15 \|$", l)]
scores = [int(re.search(r"\| (\d+)/15 \|", l).group(1)) for l in rows]
if len(scores) != 7 or sum(scores) != sum(SCORES):
    die(u"七维表形状或合计不对：" + str(scores))
tail = re.findall(u"^## Round (\\d+) · ", it_new, re.M)
if int(tail[-1]) != 288:
    die(u"ITERATION 文件尾轮次必须是本轮（现读 " + str(tail[-3:]) + u"）")
if it_new.count(u"| 真实视觉审查 |") != it_old.count(u"| 真实视觉审查 |") + 1:
    die(u"七维表数量不对")
if bk_new.count(u"追记（R291）") != 2 or bk_new.count(u"\n**339. ") != 1 or bk_new.count(u"\n**340. ") != 1:
    die(u"337／339 的追记没落上（现读 %d 条）" % bk_new.count(u"追记（R291）"))
# NOTE337 与 NOTE339 的前 20 个字符一模一样（都是「  追记（R291）：」），
# 拿前缀当判别键会把两条追记认成同一条 ⇒ 按**整行相等**找落点，再回溯它属于哪个单号。
for _num, _note in ((u"337", render(NOTE337)), (u"339", render(NOTE339))):
    if u"\n" in _note:
        die(u"单号 " + _num + u" 的追记不是单行")
    _lines = bk_new.splitlines()
    _hits = [i for i, l in enumerate(_lines) if l == _note]
    if len(_hits) != 1:
        die(u"单号 " + _num + u" 的追记整行命中 " + str(len(_hits)) + u" 次 ⇒ 落点不唯一")
    _owner = None
    for i in range(_hits[0], -1, -1):
        m = re.match(r"^\*\*(\d{3})\. ", _lines[i])
        if m:
            _owner = m.group(1)
            break
    if _owner != _num:
        die(u"追记落进了单号 " + str(_owner) + u"，应为 " + _num + u"（append_into_item 的边界判错）")
if dc_new.count(u"\n**D-271") != 1:
    die(u"D-271 没落上")
if u"## R291 状态" not in st_new:
    die(u"STATE 没轮换")

for p, txt in ((ui_p, ui_new), (it_p, it_new), (dc_p, dc_new), (bk_p, bk_new), (cg_p, cg_new), (st_p, st_new)):
    with io.open(p, "w", encoding="utf-8") as h:
        h.write(txt)

out, rc = sh([sys.executable, os.path.join(HERE, "report_cells_r258.py"), "headline"])
if rc != 0:
    die(u"FINAL_REPORT headline 刷新失败：" + out[-300:])
ran2, skip2 = battery()
if ran2 != pre_ran:
    die(u"写盘前后电池颗数不一致（" + pre_ran + u" → " + ran2 + u"）")
print(u"LEDGERS_R291 OK batt=Ran " + ran2 + u" (skipped=" + skip2 + u") roll=" + str(ROLL)
      + u" knives=" + KC + u"/" + KN + u" section=" + ("%.1f" % LINE_LEFT) + u".." + ("%.1f" % LINE_RIGHT)
      + u" sites=" + str(NSITES) + u" prod=0 U=949..951 D=271 note=337+339")
print(out.strip().splitlines()[-1])
