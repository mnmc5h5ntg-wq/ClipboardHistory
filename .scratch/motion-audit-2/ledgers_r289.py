#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R289 台账生成器（第 288 轮 / Round 286）：数字全现读，缺格拒写。根由 __file__ 推（D-260/334）。

本轮与 R280 那批的差别：**产品动了 1 个文件** ⇒ FINAL_REPORT 的 sources 格必须在电池之前刷新
（R263 那一课：代码半落地后 sources 格当场变红，它按 git 对账）。顺序因此钉死：
判据卷 → 刀 → 预检 → 四件套读数 → 电池（前）→ 写五本台账 → 刷 headline+sources → 电池（后，颗数必须相等）。
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
# 三跑是有名字的欠账（D-236 的"四件套必须属于这一笔"）：
# 第二跑现读 swift_failures=1 —— 一朵红在**既有名册**上（本轮新尺 changedXSpan 进了只读亮度那张表，
# 名单要收它）。修完名册之后必须有第三跑，摘要里那个 failures=0 才是这一笔的读数，不是上一笔的。
FRAMES = "/tmp/r289_verify3/frames"
RUN1 = "/tmp/r289_verify_run1.log"
RUN2 = "/tmp/r289_verify_run3.log"
BASE1 = "/tmp/r289_verify/baseline.log"
DEV = "/Applications/Xcode.app/Contents/Developer"


def die(m):
    sys.stderr.write("LEDGERS_R289 REFUSED: " + m + "\n")
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


def ran_of(text):
    m = re.findall(r"Executed (\d+) tests?", text)
    return int(m[-1]) if m else 0


def fail_of(text):
    m = re.findall(r"Executed \d+ tests?, with (\d+) failures?", text)
    return int(m[-1]) if m else -1


# ① 判据卷：本轮三格新证人必须现读全绿（尺的对照 + 产品判据）
stxt, src_ = sh(["swift", "test", "--filter",
                 "UICaptureTests/testFlatBandRulerKnowsItsOwnAnswers|"
                 "UICaptureTests/testChangedXSpanRulerKnowsItsOwnAnswers|"
                 "UICaptureTests/testMultiFileRowSeparatorsEndOnThePillRightAxis"],
                cwd=os.path.join(ROOT, "ClipboardHistory"))
ROLL = ran_of(stxt)
FAILS = fail_of(stxt)
if src_ != 0 or ROLL != 3 or FAILS != 0:
    die("本轮判据卷不是 3 颗绿：Ran=%s failures=%s rc=%s\n%s" % (ROLL, FAILS, src_, stxt[-600:]))
axes = re.findall(r"^(RIGHT_AXIS_R289 .*)$", stxt, re.M)
if len(axes) != 2:
    die("判据没打两档读数（现读 %d 行）⇒ 台账里那两个数没有来源" % len(axes))


def cell(line, key):
    m = re.search(key + r"=?([^｜]*)", line)
    return m.group(1).strip() if m else "?"


LIGHT, DARK = axes[0], axes[1]
GAP_L = cell(LIGHT, u"右=")
RULES_L = cell(LIGHT, u"细线数=")


# ② 三把刀现跑，并从 M842 的红话里读回「改前那条缝差多少」
ktxt, krc = sh([sys.executable, os.path.join(HERE, "mutate_r289.py")])
km = re.search(r"R289_MUTATE 刀=(\d+) CAUGHT=(\d+) ESCAPED=(\d+) NOT_RUN=(\d+) RESTORE_CLEAN=(\S+)", ktxt)
if not km or krc != 0:
    die("本轮变异表不干净：\n" + ktxt[-500:])
KN, KC, KE, KNR, KREST = km.groups()
if KC != KN or KREST != "yes":
    die("刀没全 CAUGHT 或还原不干净：CAUGHT=%s/%s RESTORE=%s" % (KC, KN, KREST))
gm = re.search(r"差 ([0-9.]+)pt（地板", ktxt)
if not gm:
    die("M842 的红话里没有差值 ⇒ 「改前读数」这一格没来源，不许手抄（R88）")
BEFORE_GAP = gm.group(1)
ARMCNT = len(re.findall(r"^M84\d CAUGHT", ktxt, re.M))

# ③ 预检：新表要登记（D-248）
ptxt, _ = sh([sys.executable, os.path.join(HERE, "mutate_needle_precheck.py")])
cover = re.search(r"NEEDLE_PRECHECK tables=(\d+) covered=(\d+) arms=(\d+) bad=(\d+)", ptxt)
total = re.search(r"ARM_TOTAL files=(\d+) arms=(\d+) dupes=(\d+) repeats=(\d+)", ptxt)
roster = re.search(r"TABLE_ROSTER registered=(\d+) unregistered_with_arms=(\d+) hidden_arms=(\d+)", ptxt)
if not (cover and total and roster) or cover.group(4) != "0" or total.group(3) != "0":
    die("预检读数不全或有坏：\n" + ptxt[-300:])
if "mutate_r289" not in ptxt:
    die("mutate_r289 没出现在预检正文 ⇒ 没登记（D-248）")

# ④ 四件套：现读 ROUND_VERIFY 那一行 + 帧基线两笔（改前变了哪 8 张 / 改后 changed=0）
if not os.path.isdir(FRAMES):
    die("看图腿与帧数的对象不在盘上：" + FRAMES + " ⇒ 这一腿记 NOT-RUN，不许编")
N_FRAMES = len([f for f in os.listdir(FRAMES) if f.endswith(".png")])
r2 = rd(RUN2)
rv = re.search(r"^ROUND_VERIFY .*$", r2, re.M)
if not rv:
    die("第二轮 ROUND_VERIFY 结论行没落盘（" + RUN2 + "）⇒ 四件套没跑完，不许写账")
gate = re.search(r"FRAME_GATE_(PASS|RED)", r2)
if not gate or gate.group(1) != "PASS":
    die("帧闸门不是 PASS：" + (gate.group(0) if gate else "无该行"))
r1 = rd(RUN1)
CH8 = re.search(r"FRAME_GATE_RED=changed=(\d+) compared=(\d+)", r1)
if not CH8:
    die("第一轮的 changed 读数不在（" + RUN1 + "）⇒ 「同一笔 update 前后」这一对没了两半")
changed_names = re.findall(r"^  changed  (\S+)$", rd(BASE1), re.M)
if len(changed_names) != int(CH8.group(1)):
    die("changed 名单与 changed 数不符：%d vs %s" % (len(changed_names), CH8.group(1)))
FAMILY = sorted(set(n.split("-720x520")[0] for n in changed_names))
if FAMILY != ["detail-3-files", "detail-3-files-hover", "detail-3-files-row0", "detail-3-files-row0-hover"]:
    die("本轮改的画面越出了多文件详情区那一家：\n" + "\n".join(changed_names))

# ⑤ 产品文件数 —— 从**代码半那一笔**读（跑生成器之前必须先提交代码半，见 R289_CODE_SHA）。
# 为什么不能读工作树：账半跑的时候代码已经进了 HEAD，`git diff` 是空的 ⇒ 那一格会写「产品 0 文件」，
# 而本轮整条主线就是"产品动了 1 个文件"（R100 那一族：数量词要数出来，且要数对对象）。
CODE_SHA = os.environ.get("R289_CODE_SHA", "").strip()
if not re.fullmatch(r"[0-9a-f]{7,40}", CODE_SHA):
    die("R289_CODE_SHA 不是一个真 sha ⇒ sources 格与产品计数不许手抄（先提交代码半，再拿它的号跑本脚本）")
pout, _ = sh(["git", "show", "--numstat", "--format=", CODE_SHA])
MINE = [l.split("\t")[-1] for l in pout.splitlines()
        if "\t" in l and l.split("\t")[-1].startswith("ClipboardHistory/Sources/")]
if not MINE:
    die("代码半那一笔 " + CODE_SHA + " 没动任何 Sources 文件 ⇒ 本轮不是产品轮，sources 格不该刷")
head_now = sh(["git", "rev-parse", "--short", "HEAD"])[0].strip()
if not head_now.startswith(CODE_SHA):
    die("HEAD 不是代码半那一笔（HEAD=" + head_now + " vs " + CODE_SHA + "）⇒ 先提交代码半再跑")

# ⑥ CI：四笔已 push 的配对 + 本轮这一笔（只登记不轮询，R140）
ctxt, _ = sh(["gh", "run", "list", "--limit", "12", "--json", "databaseId,headSha,status,conclusion"])
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
SCORES = [13, 14, 14, 13, 12, 14, 13]
V = {
    "@@DATE@@": "2026-10-21",
    "@@ROLL@@": str(ROLL),
    "@@KN@@": KN, "@@KC@@": KC, "@@KREST@@": KREST, "@@ARMCNT@@": str(ARMCNT),
    "@@TBL@@": cover.group(1), "@@COV@@": cover.group(2), "@@PARMS@@": cover.group(3),
    "@@ARMS@@": total.group(2), "@@GAPT@@": roster.group(2), "@@GAPA@@": roster.group(3),
    "@@FRAMES@@": str(N_FRAMES), "@@CH8@@": CH8.group(1), "@@CM@@": CH8.group(2),
    "@@RV@@": rv.group(0).strip(),
    "@@GAPL@@": GAP_L, "@@RULESL@@": RULES_L, "@@BEFORE@@": BEFORE_GAP,
    "@@LIGHT@@": LIGHT.strip(), "@@DARK@@": DARK.strip(),
    "@@FAMILY@@": "、".join(FAMILY),
    "@@PRODN@@": str(len(MINE)), "@@PRODFILES@@": "、".join(os.path.basename(f) for f in MINE),
    "@@BATT@@": u"脚本电池 Ran " + pre_ran + u" tests / OK (skipped=" + pre_skip + u")",
    "@@SUM@@": str(sum(SCORES)),
    "@@CI1@@": pair("41e1e66"), "@@CI2@@": pair("3403a78"), "@@CI3@@": pair("8d427f3"),
    "@@CI4@@": pair("1f119e0"), "@@CI5@@": pair("88b22cd"),
}


def render(s):
    for k, v in sorted(V.items(), key=lambda kv: -len(kv[0])):
        s = s.replace(k, v)
    if "@@" in s:
        die("仍有未替换占位符 " + ",".join(sorted(set(re.findall(r"@@[A-Z0-9]+@@", s)))))
    return s


UI_NEW = u"""## 第 288 轮（R289 / 第 288 轮 / Round 286 · @@DATE@@）：多文件详情区的行分隔线从悬停药丸外面穿出去 @@BEFORE@@pt —— 两条右轴第一次读同一份数，而"改前那个数"由刀读回来（U-939…U-943 / D-268、D-269 · 产品 @@PRODN@@ 文件）

本轮次对照：与 R281（自评 64，两臂只量到尺的前提）相比，本轮是 R275 之后**第一次动产品文件**：量出来一个缺陷、改掉它、把改前改后都换成读数。R276–R288 那十三轮的判据账不再拿来顶替这一维。

- **U-939：那条缝是量出来的，不是看出来的。** 亮档 `detail-3-files-row0-hover-720x520-light` 现读：悬停药丸右沿 **700.0pt**、三条行分隔线右沿 **720.0pt** ⇒ 细线从药丸外面穿出去 **@@BEFORE@@pt**，"一行"同时有两条右边界（暗档同形，@@DARK@@）。病根在 `DetailView.swift`：`MultiFileRow` 自己 `.padding(.horizontal, 20)`，而它下面那条 `Divider()` 只写 `.padding(.leading, 48)`（48 = R31/R104 立的文字轴，不动），**右边没有内缩** ⇒ 一路画到窗口边。修法是把那份内缩升成 `MultiFilePreviewLayout.rowHorizontalInset`，行与分隔线读同一份数；判据 `testMultiFileRowSeparatorsEndOnThePillRightAxis` 从渲染产物里读两档四条轴，地板 1.0pt 由真产物推（改完现读两档都是 700.0 vs 700.0，Δ=0.000pt）。左沿故意保留 48pt（列表通行画法：细线从图标那一列下面穿过），本轮只判**右**轴 —— 同一件事只判一次。新开 337：详情区头部那条跨整幅的段落线（`DetailView.swift:78`）是另一种约定，本轮不判它。
- **U-940：新尺第一次上真产物就红了一条与产品无关的边界 —— 红的是尺。** `changedXSpan` 第一版 `lo` 按比较赋值、`hi` 直接 `hi = x`，于是"右端"读的是**最后一行**的最右变化像素。药丸下沿是圆的，最后一行比中间行短 11px ⇒ 700.0pt 被读成 694.5pt，判据红在产品一条不存在的边界上（两档六条全红）。发现它靠的是仓库外那把临时尺逐行取 max 对账 —— 那种尺不入库，但它否证了判据。处置不是把地板放宽到 6pt，而是：① 两边同形比较；② 造一块"最宽的那行不在最后一行"的合成形状进已知答案的对照；③ 给它配刀 M844（把比较退回 `hi = x` ⇒ 必须红在对照那一格，不是红在产品判据那一格）。⇒ 写进 D-269。
- **U-941：331 的 runner 那一行是外推的，被 runner 自己两跑驳回。** `ROSTER['github-runner']` 里我填的是 `test_app_launches_and_terminates_cleanly`（R276 只读到 `skipped=1` 这个**数**，没读到是谁），而 run @@CI1@@ 与 @@CI2@@ 都打 `SKIP_ROSTER 键=github-runner … 名单外=['test_built_bundle_carries_no_app_delegate_stub'] 名册未跳=['test_app_launches_and_terminates_cleanly']` —— 跳的是端到端读包那一格（runner 的仓库根没有 `时间剪史.app`），启动冒烟那一格在 runner 上是**跑过的**。现在填的是读来的名字（两跑同读才签，R83）。同一次读 CI 还看到：STEP[9] 之外，@@CI2@@ 的 STEP[19] Motion coverage floor 也红（`testNativeRowMoveIsVisibleToTheRuler`：两臂形状一致 开 1 帧/峰值 0.053、关 1 帧/峰值 0.053 ⇒ 那次 `moveRow` 是瞬移），四跑里只这一跑红 —— 负载敏感，按 304 那一族记账，不放宽、不改产品。
- **U-942：一把新尺入库，会立刻撞上两张既有名册 —— 而且两张都红得对。** 全量卷第二跑现读 `swift_failures=1`，那一朵不是产品：`MotionFilmstripTests.testEveryTwoStateRulerReadsBothAxes` 把 `UICaptureHarness.swift#changedXSpan` 扫成"两态相减却不读 alpha"的盲区。处置不是把尺改成读 alpha （它量的是边的**位置**，补那根轴换不出任何一个 x；而这批 PNG 落盘 alpha 恒 255 ⇒ 那根轴没有对象，与 R242 的 `bandChanged` 同一条通道事实），而是带代价登记并归 BACKLOG 108。同一轮另一本名册也被撑长：331 的机器名册里 runner 那一行原本填的是外推，runner 两跑驳回之后改成读数（U-941）。⇒ 规矩：新尺入库要**全量重跑**，两张名册的名单变长都要在同一笔里给出理由，不许留着红等下一轮（R98 那一课）。第三跑的四件套摘要才是这一笔的读数（D-236）。\n- **U-943：STATE 的 R281 那一节标题里留着未替换的 `%s` 与 `%d`。** 日期与自评两格是占位符原文 —— 写盘那条路径没把模板渲染完就落盘，而 `current_round()` 的正则仍能认出轮次号，所以它不红：一格里写着"%d/105"，台账却照过。本轮补回 `2026-10-21` 与 `64/105`（数从 ITERATION Round 278 的合计读回，不手抄），并新开 338：**R282–R288 那六轮的账从没进五本台账**（只有 STATE 顶部那块"预算尽头交接"），要么补记要么显式作废 —— 过期账本比没账本更坏。

眼睛腿：RUN —— 现读 @@FRAMES@@ 张帧在盘上，看的是本轮那一对改前/改后、亮暗各两张（放大到右端 120pt×130pt）：改前两档都能看到细线一路跑到窗口边、从药丸圆角外面穿出去；改后两档的细线右端与药丸右沿对齐，而**上面那条跨整幅的段落线照旧通到边**（那是 337 的第二处，故意没动）。
读数腿：RUN —— 判据卷现读 Executed @@ROLL@@ / failures=@@FAILS@@；两档打印 @@LIGHT@@；变异 @@KC@@/@@KN@@ 全 CAUGHT、RESTORE_CLEAN=@@KREST@@；预检 tables=@@TBL@@ covered=@@COV@@ arms=@@PARMS@@ bad=0、ARM_TOTAL arms=@@ARMS@@ dupes=0；四件套 @@RV@@；改前那一笔 changed=@@CH8@@/compared=@@CM@@（名单就是 @@FAMILY@@ 这一家 × 亮暗），同一笔 update 基线后 changed=0；@@BATT@@。
产品腿：@@PRODN@@ 文件（@@PRODFILES@@）—— 十四轮里第一次。改的是**边界的一致性**，不是动效过程：悬停那一层的墨、过渡、时长本轮一律未动，帧里除那 8 张多文件详情帧外 0 张变化。
未做（逐条）：① 337（详情区头部那条跨整幅段落线 + 其余 `Divider()` 位点的右轴）；② 338（R282–R288 六轮的账）；③ 331 的 runner 行**这次改的是读数，验收仍要下一跑**；④ 333 的 CI 半；⑤ 312 的具名出口（欠第十二轮）；⑥ 335、334、310（@@GAPT@@ 张表 / @@GAPA@@ 把刀静默不覆盖）、291 的墨轴、305、328、323、322、317、314-316；⑦ 用户闸门 220 路 A / 228② / 265。

"""

ITER_NEW = u"""## Round 286 · 行分隔线从悬停药丸外面穿出去 @@BEFORE@@pt：两条右轴读同一份数，"改前那个数"由刀读回来（R289 / 第 288 轮）/ D-268、D-269 · 产品 @@PRODN@@ 文件

本轮次对照：与 R281（自评 64，量到的是尺的前提、产品 0 文件）相比，本轮回到产品面：一个量出来的边界缺陷、一处修法、一条从渲染产物读几何的判据、三把各钉一条轴的刀。
看图腿：RUN —— @@FRAMES@@ 张帧在盘上，放大看右端那 120pt：改前两档都能看到细线穿过药丸右沿跑到窗口边，改后两档对齐；上面那条跨整幅的段落线两版都在（337 的第二处，故意没动）。
读数腿：RUN —— 判据卷 Executed @@ROLL@@ / failures=@@FAILS@@；@@LIGHT@@；变异 @@KC@@/@@KN@@ 全 CAUGHT、RESTORE_CLEAN=@@KREST@@；四件套 @@RV@@；changed 同一笔 @@CH8@@→0；@@BATT@@；预检 tables=@@TBL@@ covered=@@COV@@ bad=0。
七维度自评：
| 维度 | 分/满分 |
| 真实视觉审查 | @@D0@@/15 |
| 判据有效性 | @@D1@@/15 |
| 假绿防御 | @@D2@@/15 |
| 产品面推进 | @@D3@@/15 |
| 台账一致性 | @@D4@@/15 |
| 交付诚实性 | @@D5@@/15 |
| 可复核性 | @@D6@@/15 |
各维理由：真实视觉审查 @@D0@@ —— 真看了四张（亮暗各一对改前/改后），但只看右端那一段，没扫新位点；判据有效性 @@D1@@ —— 判据从渲染产物读几何、两档各判一次、地板由真产物推，扣一分是只覆盖多文件详情区那一列；假绿防御 @@D2@@ —— 三把刀各钉一条轴（产品轴／对象闸门轴／比较轴），其中 M844 钉的是本轮真实撞过的自坏，且"没量到对象"本身是失败（judged 必须 =2，没有免检出口）；产品面推进 @@D3@@ —— 一处真改动、改前改后都有读数、帧基线同一笔，但动效过程仍没动；台账一致性 @@D4@@ —— 五本 + FINAL_REPORT 两格 + 新开 337/338 + 331 追记，扣两分是 R282–R288 的账仍欠（338）；交付诚实性 @@D5@@ —— 撤回自己尺造成的假红、外推的 runner 行被 runner 驳回后公开改、STATE 那格占位符自曝并补回；可复核性 @@D6@@ —— 判据、刀、预检、四件套日志路径与 changed 名单都在账上，runner 那一行还欠一次验收。合计 **@@SUM@@**/105。

"""

DEC_NEW = u"""**D-268（R289）：判据注释里那句"改前实测多少"必须由**摘掉修法的那把刀**读回来，不许由临时尺或记忆抄进判据。** 理由：本轮的地板 1.0pt 由"改完现读 Δ=0.000pt"推出来（R147：地板由真产物推），而账上还有第二个数 —— 改前那条缝差多少。第一版我把它写成 19.5~20.0pt 的区间，因为仓库外那把临时尺读 699.5/719.5、进判据的尺读 700.0/720.0，两把尺的"最后一列"取整口径差半颗。处置不是挑一个数，而是让 M842 把 `.padding(.trailing, …)` 摘掉再量一次：红话里印出来的就是 @@BEFORE@@pt，判据正文与刀的期望文本互相签字（换了对象会报 WRONG_CELL 而不是 CAUGHT）。这样"改前读数"每次重跑都会被复查一次，注释里的数不再是化石。与 D-240（改产品视觉量的刀必须重捕产物）同族但相反方向：这一格的判据在测试进程里现渲染，所以刀**不必**重捕帧 —— 这条区分写在表头，否则下一轮会以为"改了产品没重捕"。

**D-269（R289）：一把尺的两个方向必须同形；不对称的那一半会把"最后一行"读成"边界"。** 理由：`changedXSpan` 第一版 `lo` 用 `if x < lo` 而 `hi` 直接赋值 —— min 天然是全局的，max 不是：扫描顺序让 `hi` 停在**最后一个有变化的行**的最右像素。真产物上药丸下沿是圆的，最后一行比中间行短 11px，于是右沿 700.0pt 被读成 694.5pt，判据红在产品一条不存在的边界上（两档六条全红）。规矩落成三条：① 同一把尺里成对的方向量（min/max、左/右、开/关）写法必须对称；② 已知答案的对照要专门造一块"**最宽的那行不在最后一行**"的形状，否则对照只是在重复判据已经会红的事；③ 这条对照配一把刀（M844），把比较退回不对称赋值，期望红在**对照**那一格而不是产品那一格。与 R102（临时谓词把背景本身算命中会报出格式像结论的假读数）、R86（自动搜出来的采样点会把量错对象伪装成量到了）同族。

"""

CHG_NEW = u"""### Fixed（R289 / 第 288 轮 / Round 286 · 多文件详情区的两条右轴并成一条）

`DetailView.swift`：多文件列表的行分隔线原来只内缩左端（`.padding(.leading, 48)` = 文字轴），右端一路画到窗口边，而它上面那颗悬停药丸左右各内缩 20pt ⇒ 帧里现读药丸右沿 700.0pt、分隔线右沿 720.0pt，细线从药丸外面穿出去 **@@BEFORE@@pt**（亮暗同形）。新增 `MultiFilePreviewLayout.rowHorizontalInset`，行与分隔线读同一份数；左端 48pt 保留（列表通行画法），本轮只判右轴。新判据 `UICaptureTests/testMultiFileRowSeparatorsEndOnThePillRightAxis` 从渲染产物读几何（两档各一次，地板 1.0pt 由真产物推，改完现读 Δ=0.000pt；"没量到对象"本身就是失败，没有免检出口）+ 两把新尺 `flatBands`／`changedXSpan` 各配一格已知答案的对照。新尺第一次上真产物就红在一条不存在的边界上（`hi` 不按比较赋值 ⇒ 读成最后一行的右沿），已修并升成对照与刀 M844（D-269）。新增 `mutate_r289.py`：M842（产品轴：摘掉 trailing 内缩 —— 红话里印出改前的 @@BEFORE@@pt，D-268）／M843（对象闸门轴：跨度闸门抬到 0.98 ⇒ 必须红在「尺没有对象」）／M844（比较轴），现读 @@KC@@/@@KN@@ 全 CAUGHT、RESTORE_CLEAN=@@KREST@@，并登记进预检（tables=@@TBL@@ covered=@@COV@@ bad=0、ARM_TOTAL arms=@@ARMS@@ dupes=0）。331 的 runner 名册行由外推改成读数：runner 两跑（@@CI1@@／@@CI2@@）同读 `test_built_bundle_carries_no_app_delegate_stub`，而原来填的 `test_app_launches_and_terminates_cleanly` 在 runner 上根本没跳。帧基线同一笔 update：changed @@CH8@@/@@CM@@（@@FAMILY@@ × 亮暗）→ 0。四件套 @@RV@@；@@BATT@@；眼睛腿 RUN（亮暗各一对改前/改后）。新开 337（详情区头部那条跨整幅段落线的右轴）、338（R282–R288 六轮的账从没进五本台账）；STATE 的 R281 那一节留着未替换的 `%s`/`%d`，本轮补回（数从 ITERATION Round 278 读回）。CI：@@CI1@@／@@CI2@@／@@CI3@@／@@CI4@@／@@CI5@@。

"""

BACK_337 = (u"**337. 详情区里还有别的右边界没判：头部与内容之间那条跨整幅的段落线，以及其余 `Divider()` 位点（R289 现读：`DetailView.swift:78` 那条右沿 720.0pt，而本轮只把多文件列表的行分隔线接进同一份内缩）**"
            u"：R289 故意把范围收在「列表自己的行分隔线」—— 头部那条是段落线、约定不同（通到窗边是常见画法），但"
            u"**不同不等于没判**。做法照 R289：① 用 `flatBands` 现读每个位点的左右沿（不猜坐标）；② 逐个位点写进名册并给出"
            u"「通到边 / 收到右轴 / 收到文字轴」三选一的**理由**（理由要能被盘上对象否证，D-266 同族）；③ 每改一处配一把产品轴的刀，"
            u"红话里要印出差值（D-268）；④ 没判的位点显式留在本单里，不许把「本轮只做了多文件」写成「右轴都判完了」")

BACK_338 = (u"**338. R282–R288 那六轮的账从没进五本台账，只在 STATE 顶部留了一块「预算尽头交接」（R289 现读：UI_AUDIT 最大节仍是第 280 轮 / R281，ITERATION 尾节 Round 278）**"
            u"：那六轮里落了 336 的开单与结案、M838/M839/M840/M841 四把刀、331 本机半（一卷新证人 + 名册）、330 收成具名通道限制、"
            u"以及三次「上一笔提交信息写着追记而追记没写进去」的自曝 —— 全都在 git 与 .scratch 里，台账里查不到。"
            u"两种诚实收场，二选一：① 按轮补记（每轮一节，读数从当轮的 /tmp 日志与 git 里读，读不到的格子写 NOT-RUN，不许编）；"
            u"② 在 UI_AUDIT/ITERATION 各写一节「这几轮合并申报」，并把它们从自评曲线里显式排除（曲线尺按文件顺序认尾轮，R279 那一课）。"
            u"不许保持现状：现在曲线里 279…285 是空的，而 BACKLOG 里那些单号都写着「R28x 现读」—— 读者会以为账是全的。**")

STATE_NEW = u"""## R289 状态（第 288 轮 / Round 286 · @@DATE@@）
最后更新：2026-10-21（本地 · R289 / 第 288 轮 / Round 286）：**回到产品面：多文件详情区的行分隔线从悬停药丸外面穿出去 @@BEFORE@@pt，两条右轴现在读同一份数，判据从渲染产物里量**（U-939…U-943 · D-268、D-269 · 产品 @@PRODN@@ 文件 · 自评 @@SUM@@/105）

**本轮落地**：`DetailView.swift` 新增 `MultiFilePreviewLayout.rowHorizontalInset`（行与分隔线共用）；`UICaptureHarness.swift` 新增两把尺（`flatBands`／`changedXSpan`）+ 三格判据（两格已知答案对照 + 一格产品判据，Executed @@ROLL@@ / failures=@@FAILS@@）；`mutate_r289.py` M842/M843/M844（@@KC@@/@@KN@@ 全 CAUGHT、RESTORE_CLEAN=@@KREST@@，已登记进预检 tables=@@TBL@@ covered=@@COV@@ bad=0）；`test_skip_roster.py` 的 runner 行由外推改成两跑同读的读数；STATE 的 R281 那一节补回未替换的 `%s`/`%d`。现读：@@LIGHT@@；改前 changed=@@CH8@@/compared=@@CM@@ → 同一笔 update 后 0；四件套 @@RV@@；@@BATT@@。自己撞的尺坏法入账：`hi` 不按比较赋值 ⇒ 右沿读成最后一行（694.5pt），红在产品一条不存在的边界上 —— 由仓库外那把临时尺逐行取 max 否证，处置是对称化 + 造"最宽的行不在最后一行"的对照 + 配刀 M844（D-269）。新开 337、338。

**下一轮（R290 / 第 289 轮 / Round 287）的 ⓪**：
⓪ 读 CI：@@CI1@@、@@CI2@@、@@CI3@@、@@CI4@@、@@CI5@@（四跑 STEP[9] 红在 331 那一格，本笔把它改成读数 —— 要验的就是 STEP[9] 的 failures=0；只登记不轮询，R140）。若 runner 仍红在 `SKIP_ROSTER`，读它自己打的那一行（`名单外=[…] 名册未跳=[…]`），按主语是机器名册解释，不许改产品也不许放宽闸门。
① **338（六轮的账）**：补记或显式作废，二选一，别保持"看起来是全的"。
② **337**：详情区其余右边界位点逐个判（现读左右沿 → 三选一理由 → 配刀），做完删一行。
③ **回到动效过程**：330 已收成具名通道限制，但清账表里"悬停淡入的过程没有产物证人"那几位仍开；305（按下台阶的地板分辨实验）、291 的墨轴、312 的具名出口（欠第十二轮，本机 3.000 不许降，D-251）。
④ 333 的 CI 半、335、334、310（@@GAPT@@ 张表 / @@GAPA@@ 把刀静默不覆盖）、328、323、322、317、314-316。
⑤ 用户闸门 220 路 A / 228② / 265。

"""

PREVSUM = "64"
V["@@PREVSUM@@"] = PREVSUM
V["@@FAILS@@"] = str(FAILS)

for i, nm in enumerate("D0 D1 D2 D3 D4 D5 D6".split()):
    ITER_NEW = ITER_NEW.replace("@@" + nm + "@@", str(SCORES[i]))
for n in ("UI_NEW", "ITER_NEW", "DEC_NEW", "CHG_NEW", "STATE_NEW"):
    globals()[n] = render(globals()[n])
BACK_NEW = render(BACK_337) + "\n\n" + render(BACK_338) + "\n"

ui_p = B["AGENT_UI_AUDIT.md"]
ui_old = rd(ui_p)
if u"## 第 288 轮" in ui_old:
    die(u"UI_AUDIT 已有第 288 轮 ⇒ 生成器不幂等，先还原")
anchor = u"## 第 280 轮"
if ui_old.count(anchor) != 1:
    die("UI_AUDIT 锚点命中 %d 次" % ui_old.count(anchor))
ui_new = ui_old.replace(anchor, UI_NEW + anchor, 1)

it_p = B["AGENT_VISUAL_ITERATION.md"]
it_old = rd(it_p)
if re.search(u"^## Round 286 · ", it_old, re.M):
    die(u"ITERATION 已有 Round 286 ⇒ 不幂等")
it_new = it_old.rstrip("\n") + u"\n\n" + ITER_NEW

dc_p = B["AGENT_DECISIONS.md"]
dc_old = rd(dc_p)
if u"D-268" in dc_old or u"D-267" not in dc_old:
    die(u"D 号不对（D-267 应在盘上、D-268 不该在）")
dc_new = dc_old.rstrip("\n") + u"\n\n" + DEC_NEW
cg_p = B["CHANGELOG.md"]
cg_old = rd(cg_p)
cg_new = cg_old.replace(u"## [Unreleased]\n", u"## [Unreleased]\n\n" + CHG_NEW, 1)
bk_p = B["AGENT_BACKLOG.md"]
bk_old = rd(bk_p)
last = re.findall(r"^\*\*(\d{3})\. ", bk_old, re.M)
if last[-1] != "336":
    die(u"BACKLOG 最后一单不是 336（现读 " + str(last[-3:]) + u"）")
# 331 的追记必须落在**那一单内部**（两空格缩进的 `追记` 行），不是接在文件尾 ——
# 追到文件尾等于换了主语：读者会以为它在说 338（BACKLOG 的规矩：追记追加、不替换原文）。
NOTE331 = (u"  追记（R289）：331 的 runner 那一行由 R276 的外推改成读数 —— runner 两跑（"
           + V["@@CI1@@"] + u"／" + V["@@CI2@@"] + u"）同读 `test_built_bundle_carries_no_app_delegate_stub`，"
           u"而名册里原来填的 `test_app_launches_and_terminates_cleanly` 在 runner 上根本没跳"
           u"（它在那台机器上是跑过的）。这一格从此是**读来的**，两跑同读才签（R83）；"
           u"验收仍欠下一跑 —— 见 R290 的 ⓪。")


def append_into_item(text, num, extra):
    lines = text.splitlines(True)
    start = None
    for i, l in enumerate(lines):
        if l.startswith("**" + num + ". "):
            if start is not None:
                die("BACKLOG 里 " + num + " 出现两次 ⇒ 锚点不唯一，不许插")
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
    return u"".join(lines[:end]) + extra + u"\n" + u"".join(lines[end:])


bk_new = append_into_item(bk_old, "331", NOTE331)
bk_new = bk_new.rstrip("\n") + u"\n\n" + BACK_NEW

st_p = B["AGENT_STATE.md"]
st_old = rd(st_p)
if u"## R281 状态" not in st_old:
    die(u"STATE 找不到 R281 锚点")
st_new = st_old.replace(u"## R281 状态", STATE_NEW + u"## R281 状态", 1)


def must_preserve(old, new, name):
    cn = Counter(new.splitlines())
    lost = [l for l, c in Counter(old.splitlines()).items() if cn[l] < c]
    if lost:
        die(name + u" 弄丢 " + str(len(lost)) + u" 行：" + u" | ".join(lost[:2])[:140])


for o, n, name in ((ui_old, ui_new, "AGENT_UI_AUDIT.md"), (cg_old, cg_new, "CHANGELOG.md"),
                   (bk_old, bk_new, "AGENT_BACKLOG.md"), (st_old, st_new, "AGENT_STATE.md"),
                   (it_old, it_new, "AGENT_VISUAL_ITERATION.md"), (dc_old, dc_new, "AGENT_DECISIONS.md")):
    must_preserve(o, n, name)

ids = [int(x) for x in re.findall(u"- \\*\\*U-(\\d+)", UI_NEW)]
if ids != list(range(939, 944)):
    die(u"U 号不连续：" + str(ids))
if u"U-939…U-943" not in UI_NEW.splitlines()[0]:
    die(u"节标题 U 区间与定义不符")
rows = [l for l in ITER_NEW.splitlines() if re.match(r"\| .* \| \d+/15 \|$", l)]
scores = [int(re.search(r"\| (\d+)/15 \|", l).group(1)) for l in rows]
if len(scores) != 7 or sum(scores) != sum(SCORES):
    die(u"七维表形状或合计不对：" + str(scores))
if not it_new.startswith(it_old.rstrip("\n")) or u"## Round 278 · " not in it_new:
    die(u"ITERATION 不是纯追加")
tail = re.findall(u"^## Round (\\d+) · ", it_new, re.M)
if int(tail[-1]) != 286:
    die(u"ITERATION 的**文件尾轮次**必须是本轮（现读 " + str(tail[-3:]) + u"）⇒ 曲线尺按文件顺序认尾轮")
if it_new.count(u"| 真实视觉审查 |") != it_old.count(u"| 真实视觉审查 |") + 1:
    die(u"七维表数量不对")
if bk_new.count(u"\n**337. ") != 1 or bk_new.count(u"\n**338. ") != 1:
    die(u"新开 337/338 没落上")
if bk_new.count(u"追记（R289）") != 1:
    die(u"331 的追记没落上或落了两遍")
# 位置判据要问"插进 331 之内了吗"，不是"后面还有没有别的单号"（后面本来就有 332…338）。
_seg331 = bk_new.split(u"**331. ", 1)[1].split(u"追记（R289）", 1)[0]
if re.search(r"^\*\*\d{3}\. ", _seg331, re.M):
    die(u"331 的追记前面已经出现别的单号 ⇒ 插错位置（主语会换）")
if u"\n  追记（R289）" not in bk_new:
    die(u"331 的追记没有以两空格缩进落在那一单里 ⇒ 形状不对")
if dc_new.count(u"\n**D-268") != 1 or dc_new.count(u"\n**D-269") != 1:
    die(u"D-268/D-269 没落上")
if u"## R289 状态" not in st_new:
    die(u"STATE 没轮换")

for p, t in ((ui_p, ui_new), (it_p, it_new), (dc_p, dc_new), (bk_p, bk_new), (cg_p, cg_new), (st_p, st_new)):
    with io.open(p, "w", encoding="utf-8") as h:
        h.write(t)

out, rc = sh([sys.executable, os.path.join(HERE, "report_cells_r258.py"), "headline"])
if rc != 0:
    die(u"FINAL_REPORT headline 刷新失败：" + out[-300:])
# 产品动了文件 ⇒ sources 格必须在电池之前刷新（R263 那一课：它按 git 对账，代码半一落地就变红）
out2, rc2 = sh([sys.executable, os.path.join(HERE, "report_cells_r258.py"), "sources", CODE_SHA])
if rc2 != 0:
    die(u"FINAL_REPORT sources 刷新失败：" + out2[-300:])
ran2, skip2 = battery()
if ran2 != pre_ran:
    die(u"写盘前后电池颗数不一致（" + pre_ran + u" → " + ran2 + u"）")
print(u"LEDGERS_R289 OK batt=Ran " + ran2 + u" (skipped=" + skip2 + u") roll=" + str(ROLL)
      + u" knives=" + KC + u"/" + KN + u" before_gap=" + BEFORE_GAP + u" frames=" + str(N_FRAMES)
      + u" changed=" + CH8.group(1) + u" prod=" + str(len(MINE)) + u" U=939..943 D=268,269 new=337,338")
print(out.strip().splitlines()[-1])
print(out2.strip().splitlines()[-1])
