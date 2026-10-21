#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R275 台账生成器（第 274 轮 / Round 272）：三处 hover 动画的触发条件与画法对齐。

数字一律现读：/tmp/r275_verify.log（四件套）、/tmp/r275_guard2.log（新判据卷自己那行）、
/tmp/r275_knife4.log（两把刀）、预检、脚本电池连跑两遍、git diff 的产品文件清单。
"""
import io
import os
import re
import subprocess
import sys
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
HERE = os.path.join(ROOT, ".scratch", "motion-audit-2")
B = {n: os.path.join(ROOT, n) for n in ("AGENT_UI_AUDIT.md", "AGENT_VISUAL_ITERATION.md", "AGENT_DECISIONS.md",
                                        "AGENT_BACKLOG.md", "CHANGELOG.md", "AGENT_STATE.md")}
PRE = os.path.join(HERE, "mutate_needle_precheck.py")
VERIFY = "/tmp/r275_verify.log"
GUARD = "/tmp/r275_guard2.log"
KNIFE = "/tmp/r275_knife4.log"


def die(m):
    sys.stderr.write("LEDGERS_R275 REFUSED: " + m + "\n")
    raise SystemExit(2)


def rd(p):
    if not os.path.exists(p):
        die("证人文件不在盘上：" + p)
    with io.open(p, encoding="utf-8", errors="replace") as h:
        return h.read()


def sh(cmd):
    env = dict(os.environ)
    env["PYTHONUTF8"] = "1"
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    pr = subprocess.run(cmd, cwd=ROOT, env=env, capture_output=True, text=True)
    return (pr.stdout or "") + (pr.stderr or ""), pr.returncode


# ---- ① 四件套那一行 ----
vline = re.search(r"ROUND_VERIFY build_warnings=(\d+) swift_executed=(\d+) swift_skipped=(\d+) "
                  r"swift_failures=(\d+) frames=(\d+) baseline_compared=(\d+) baseline_changed=(\d+) "
                  r"baseline_missing=(\d+) dmg=(\w+) installed_version=(\S+) dir=(\S+)", rd(VERIFY))
if not vline:
    die("ROUND_VERIFY 那一行读不到（顺序：判据卷→刀→帧→全量卷→换装）：\n" + rd(VERIFY)[-400:])
VW = vline.groups()
if VW[0] != "0":
    die("构建告警不是 0：" + VW[0])
if VW[3] != "0":
    die("全量卷有失败（" + VW[3] + "）⇒ 先分诊，不许写台账")
if VW[7] != "0":
    die("帧基线 changed=" + VW[7] + " —— 本轮改的是动画触发条件，静置画面应当一字不动；"
        "真动了就要当场说明是哪一颗夹具、为什么")

# ---- ② 新判据卷自己那行 ----
g = re.search(r"HOVER_ANIM_ALIGNMENT files=(\d+) sites=(\d+) 免检\(不读取证键\)=(\d+) 裸读=(\d+) 判=(\w+)", rd(GUARD))
if not g or g.group(5) != "PASS" or g.group(4) != "0":
    die("判据卷没有绿+裸读归零：" + (g.group(0) if g else "无 HOVER_ANIM_ALIGNMENT 行"))
if int(g.group(2)) < 6:
    die("扫到的 hover 动画位点少于 6（现读 " + g.group(2) + "）⇒ 扫描面塌了，不是产品变干净")
cells = len(set(re.findall(r"Test Case '-\[[\w.]+ (test\w+)\]' passed", rd(GUARD))))
if cells != 4:
    die("新卷 passed 的格子数不是 4（现读 " + str(cells) + "）")

# ---- ③ 两把刀 ----
kn = re.search(r"R275_MUTATE 刀=(\d+) CAUGHT=(\d+) ESCAPED=(\d+) NOT_RUN=(\d+) RESTORE_CLEAN=(\w+)", rd(KNIFE))
if not kn or kn.group(1) != kn.group(2) or kn.group(3) != "0" or kn.group(4) != "0" or kn.group(5) != "yes":
    die("两把刀不是全 CAUGHT：" + (kn.group(0) if kn else "无汇总行"))
arm_lines = re.findall(r"^(M83\d) CAUGHT\s+(.+?) ｜ 红在 (\w+)\((\w+)\)", rd(KNIFE), re.M)
if len(arm_lines) != 2:
    die("刀的两行明细抽不出（要各钉一条轴 = D-244）：" + str(arm_lines))
# 失败文本自己点名的那颗位点（`文件:行 value=isHovered`）—— 从 M832 那一次的正文现读，不手抄行号
bsrc = rd("/tmp/r275_raw.log")
mbare = re.search(r"([A-Za-z0-9_]+\.swift:\d+ value=isHovered)\b", bsrc)
if not mbare:
    die("读不到 M832 失败文本里那颗被点名的位点 ⇒ 台账里那句『点名到行号』没有证人")
bare_site = mbare.group(1)

# ---- ④ 产品文件清单：本轮改了哪几个 Sources 文件 ----
diff_txt, _ = sh(["git", "show", "--numstat", "--format=", "HEAD", "--", "ClipboardHistory/Sources"])
prod = [l.split("\t")[2] for l in diff_txt.splitlines() if l.strip()]
if len(prod) != 3:
    die("产品文件不是 3 个（现读 " + str(len(prod)) + "：" + ",".join(prod) + "）")
prod_short = "、".join(os.path.basename(p) for p in prod)

# ---- ⑤ 预检 + 电池 ----
ptxt, _ = sh([sys.executable, PRE])
cover = re.search(r"NEEDLE_PRECHECK tables=(\d+) covered=(\d+) arms=(\d+) bad=(\d+)", ptxt)
roster = re.search(r"TABLE_ROSTER registered=(\d+) unregistered_with_arms=(\d+) hidden_arms=(\d+)", ptxt)
total = re.search(r"ARM_TOTAL files=(\d+) arms=(\d+) dupes=(\d+) repeats=(\d+)", ptxt)
if not (cover and roster and total) or cover.group(4) != "0" or total.group(3) != "0":
    die("预检读数不全或有坏：\n" + ptxt[-300:])
if "mutate_r275" not in rd(PRE):
    die("mutate_r275 没登记进 TABLES（D-248 那颗牙）")


def battery():
    b, rc = sh([sys.executable, "-m", "unittest", "discover", "-s", "scripts/tests"])
    m = re.findall(r"^Ran (\d+) tests", b, re.M)
    if not m or not re.search(r"^OK", b, re.M) or rc != 0:
        die("电池不是绿的：\n" + b[-700:])
    sk = re.search(r"skipped=(\d+)", b)
    return m[-1], (sk.group(1) if sk else "0")


pre_ran, pre_skip = battery()

ctxt, _ = sh(["gh", "run", "list", "--limit", "10", "--json", "databaseId,headSha,status,conclusion"])
runs = []
if "[" in ctxt:
    import json
    runs = json.loads(ctxt[ctxt.index("["):])


def pair(sha):
    hits = [r for r in runs if r["headSha"].startswith(sha)]
    if not hits:
        return sha + " → 未取到（293）"
    r = hits[0]
    return sha + " → " + str(r["databaseId"]) + " / " + r["status"] + " / " + (r["conclusion"] or "未读")


V = {
    "@@DATE@@": "2026-10-21",
    "@@FILES@@": str(len(prod)), "@@PROD@@": prod_short,
    "@@FILES_SCANNED@@": g.group(1), "@@SITES@@": g.group(2),
    "@@EXEMPT@@": g.group(3), "@@CELLS@@": str(cells),
    "@@ARM1@@": arm_lines[0][0] + "（红在 " + arm_lines[0][3] + "，钉的是产品轴：动画条件退回裸读）",
    "@@ARM2@@": arm_lines[1][0] + "（红在 " + arm_lines[1][3] + "，钉的是尺轴：把裸读谓词弄瞎）",
    "@@KN@@": kn.group(1) + "/" + kn.group(2) + " CAUGHT、RESTORE_CLEAN=" + kn.group(5),
    "@@BUILD@@": VW[0], "@@EXEC@@": VW[1], "@@SKIP@@": VW[2], "@@FAIL@@": VW[3],
    "@@FRAMES@@": VW[4], "@@CHANGED@@": VW[6], "@@MISSING@@": VW[7],
    "@@DMG@@": VW[8], "@@VER@@": VW[9],
    "@@BATT@@": "脚本电池 Ran " + pre_ran + " tests / OK (skipped=" + pre_skip + ")",
    "@@TBL@@": cover.group(1), "@@COV@@": cover.group(2), "@@PARMS@@": cover.group(3),
    "@@GAPT@@": roster.group(2), "@@GAPA@@": roster.group(3), "@@ARMS@@": total.group(2),
    "@@CIN@@": pair("1c831f2"), "@@CIN2@@": pair("3ec2a97"),
    "@@BARESITE@@": bare_site,
}

UI_NEW = """## 第 274 轮（R275 / 第 274 轮 / Round 272 · @@DATE@@）：三处悬停淡入在取证通道里从来没有过程 —— 画法和动画的触发条件必须问同一句话（U-918…U-920 / D-261 · 产品 @@FILES@@ 文件）

本轮次对照：与 R274（自评 80，runner 那朵红归因到自己头上）相比，本轮回到产品面：R263 结掉 `HistoryRowViews` 那一族时把范围写成"一处 tint + 一条 animation value"，但那是**按文件**记的账 —— 同一形状在另外三个文件里还活着，而且没有任何尺会红。

- **U-918：缺陷本身与修法** —— `.animation(MotionCatalog.animation(for: .hover), value: X)` 在 @@SITES@@ 处位点里（@@FILES_SCANNED@@ 个源码文件现读）有 3 处把 X 直读裸 `@State isHovered`：@@PROD@@。这三颗文件的**画法**早就接了取证键（`hoveredForCapture`），于是离屏渲染时墨会落下、动画却永远不触发（`.onHover` 在无指针的离屏通道恒 false ⇒ value 从不变化 ⇒ 没有中间态可数）。后果不是像素错，是**这条淡入是否存在于可测通道里**这句话没有证人 —— 与 R263 那条"量不到被记成没问题"（D-249）同族，只是这次坏的是动画那一半。修法：三处都改读同一个合取式（`SettingsSidebarRow` 新建 `isHoveredForDrawing`，`HistorySidebarView` 复用既有的 `isHoveredForFill`，`SearchField` 复用既有的 `isHoveredForDrawing`）⇒ 现在 @@SITES@@ 处位点里裸读 @@EXEMPT@@ 处不读取证键、其余全部对齐（判据现读：files=@@FILES_SCANNED@@ sites=@@SITES@@ 免检=@@EXEMPT@@ 裸读=0）。
- **U-919：一把新尺与两把刀，外加刀自己的一次误报** —— 新卷 `HoverAnimationChannelTests`（@@CELLS@@ 格：对齐判据 + `isBare` 真值表 + 剥注释后才数（R76）+ 豁免的**方向性**：不读取证键的文件豁免，一旦接了键同一处写法就必须翻红）。根由 `#filePath` 推（D-260 —— 上一轮刚为同一件事红在 runner 上）。刀 @@KN@@：@@ARM1@@、@@ARM2@@。要单独记一笔的是刀的第一版：它按 `name : XCTAssert… failed` 这种形状找失败格，而 SwiftPM 实际打的是 `-[Module.Class testFoo] : XCTAssertEqual failed` ⇒ 两把刀都被报成 WRONG_CELL —— **刀读不到不等于产品没红**，那是尺的失灵（现读 /tmp/r275_raw.log 的真实形状后重写正则，两把才各自红在正确的格上）。
- **U-920：静置画面一字未动，这一次"画面没变"是读数不是断言** —— 四件套现读：构建告警=@@BUILD@@、全量卷 Executed=@@EXEC@@ skipped=@@SKIP@@ failures=@@FAIL@@、帧 frames=@@FRAMES@@ 基线 compared 后 changed=@@CHANGED@@ missing=@@MISSING@@、dmg=@@DMG@@、换装本机 @@VER@@。改的是动画触发条件而不是任何一档墨 ⇒ changed 必须为 0，而它确实是 0；这条等式本身就是本轮"没有偷偷改外观"的证人（若哪天这里变成非 0，就是有人借"对齐条件"的名义挪了画法）。眼睛腿：RUN —— 三处里只有**一颗**有两态帧可看：`segmented-filter-idle` 与 `segmented-filter-hover`（亮/暗各一对，200x60）—— 悬停那一档确实多出一层灰、且只落在未选中那枚，与 `hoverFill` 的 `guard !isSelected` 一致；另外两处**没有两态帧可看**：`search-field-320x112` 只有单态（没有 hover 孪生帧），设置侧栏行 `SettingsSidebarRow` 根本没有 hover 夹具（`settings-*` 全是整窗、不点亮取证键）⇒ 本轮修的是"条件同式"这件事本身，三处的**过程**与两态对照都还没有产物读数，这就是 330 的真实范围（不是笼统的"缺一把尺"，而是按位点数出来的：两处缺两态夹具、三处缺中间态证人）。

变异腿：RUN（@@KN@@、预检已登记 mutate_r275：tables=@@TBL@@ covered=@@COV@@ arms=@@PARMS@@ bad=0、ARM_TOTAL arms=@@ARMS@@ dupes=0、310 缺口 @@GAPA@@ 把）。
产品腿：@@FILES@@ 文件（`SettingsView.swift` / `HistorySidebarView.swift` / `SearchField.swift`，全是动画触发条件一行）⇒ sources 格本轮要刷新。
未做（逐条）：① 330（这三处的**中间态**产物证人，或显式记「源码已接、产物未量」）；② **312 的具名出口（欠第七轮）**；③ 329（206 处写死本机根）、328、323、322、317、314、315、316；④ 310 的 @@GAPT@@ 张表 / @@GAPA@@ 把刀、309 那 6 张、305、299、301、307、291 画法轴那四位；⑤ 用户闸门 220 路 A / 228② / 265。

"""

ITER_NEW = """## Round 272 · 三处悬停淡入在取证通道里从来没有过程：画法与动画的触发条件对齐，并给这条规则一把会红的尺（R275 / 第 274 轮）/ D-261 · 产品 @@FILES@@ 文件

本轮次对照：与 R274（自评 80）相比，本轮动产品（@@FILES@@ 文件），把 R263/D-249 那一族在另外三颗文件里的复发一次修完。
看图腿：RUN —— 三处里只有段按钮那颗有两态帧（`segmented-filter-idle` 对 `segmented-filter-hover`，亮/暗各一对）：悬停确实多出一层灰、只落在未选中那枚；`search-field-320x112` 只有单态、设置侧栏行根本没有 hover 夹具 ⇒ 这两处本轮修的是条件同式，但**没有**两态画面可看，缺口按位点数清写进 330。
读数腿：RUN —— 判据卷现读 files=@@FILES_SCANNED@@ sites=@@SITES@@ 免检=@@EXEMPT@@ 裸读=0 判=PASS（@@CELLS@@ 格全绿）；四件套 build_warnings=@@BUILD@@、全量 Executed=@@EXEC@@ skipped=@@SKIP@@ failures=@@FAIL@@、frames=@@FRAMES@@ changed=@@CHANGED@@ missing=@@MISSING@@、dmg=@@DMG@@、本机 @@VER@@；刀 @@KN@@；@@BATT@@；预检 tables=@@TBL@@ covered=@@COV@@ arms=@@PARMS@@ bad=0。
七维度自评：
| 维度 | 分/满分 |
| 真实视觉审查 | 8/15 |
| 判据有效性 | 14/15 |
| 假绿防御 | 15/15 |
| 产品面推进 | 9/15 |
| 台账一致性 | 14/15 |
| 交付诚实性 | 15/15 |
| 可复核性 | 13/15 |
各维理由：真实视觉审查 8 —— 三处里只有一颗（段按钮）有两态帧可看，看了并确认悬停只多一层灰、落在未选中那枚；搜索框只有一态、设置侧栏行没有 hover 夹具 ⇒ 这一维按实记，不按"看了四张"记；判据有效性 14 —— 新尺能红（M832 现读红在对齐格、失败文本自己点名 `@@BARESITE@@`），扣一分是它只判源码形状、不判产物；假绿防御 15 —— 三件同向：豁免按方向各判一次、真值表钉住谓词自己、刀的第一版误报被写成账而不是藏起来；产品面推进 9 —— @@FILES@@ 个产品文件，但改的是可测性而非观感（不是"为了打破 0 改动而加动效"）；台账一致性 14 —— 五本 + STATE + 报告两格，数字全由脚本现读，sources 格本轮刷新；交付诚实性 15 —— 「源码已接、产物未量」按位点数清写进 330，没有把对齐说成"淡入已验收"；可复核性 13 —— 证人文件在 /tmp（重启即失），重跑命令写进 STATE。合计 **88**/105。

"""

DEC_NEW = """**D-261（R275）：取证通道的接线要按「条件」名册化，而不是按「通道接没接」——同一个视图里驱动画法的合取式与 `.animation(..., value:)` 的表达式必须是同一个。** 理由：R263 结掉 `HistoryRowViews` 时把这件事写成"一处 tint + 一条 animation value"，但按文件记的账追不上按形状长的东西：本轮现读 @@SITES@@ 处 hover 动画位点里，另有 3 处（@@PROD@@）画法早就读 `hoveredForCapture`、动画 value 仍直读裸 `isHovered`。后果不是像素，而是**这条淡入在离屏通道里从来没有过程**（无指针 ⇒ `.onHover` 恒 false ⇒ value 从不变化），于是"它到底是不是淡进来的"这句话在该通道里连一个能被打红的证人都不配称。规矩：凡接了取证键的视图，其 `.hover`/`.press` 动画 value 必须读同一个合取式（`isHoveredForDrawing` / `isHoveredForFill` / `isPressedForDrawing`），由 `HoverAnimationChannelTests` 钉住 —— 它问"两半是不是同一句话"，不问"演没演"；后者要产物证人 ⇒ BACKLOG 330。与 D-249（按形状漏读）、D-255（名册只在该次扫到的对象里对账）、D-244（一把刀只钉一条轴）同族。

"""

CHG_NEW = """### Changed（R275 / 第 274 轮 / Round 272 · 三处悬停淡入接进取证通道）

`SettingsView.swift` 的 `SettingsSidebarRow`、`HistorySidebarView.swift` 的筛选段按钮、`SearchField.swift`：`.animation(MotionCatalog.animation(for: .hover), value:)` 从直读裸 `isHovered` 改成与该视图**画法同一个合取式**（`isHoveredForDrawing` / `isHoveredForFill`）⇒ 离屏取证时这条淡入第一次有触发条件（此前 value 永不变化，墨落下但没有过程）。判据现读：files=@@FILES_SCANNED@@ 源码文件、hover 动画位点 @@SITES@@ 处、免检（不读取证键）=@@EXEMPT@@、裸读=0 判=PASS；新卷 `HoverAnimationChannelTests` @@CELLS@@ 格（对齐 + 真值表 + 剥注释 + 豁免方向性），根由 `#filePath` 推（D-260）。刀 @@KN@@：@@ARM1@@、@@ARM2@@（第一版按错的行形状找失败格 ⇒ 两把都误报 WRONG_CELL，刀读不到不等于产品没红）。四件套：告警 @@BUILD@@、全量 Executed=@@EXEC@@ failures=@@FAIL@@ skipped=@@SKIP@@、帧 @@FRAMES@@ changed=@@CHANGED@@ missing=@@MISSING@@、dmg=@@DMG@@、本机 @@VER@@；@@BATT@@；预检 tables=@@TBL@@ covered=@@COV@@ arms=@@PARMS@@ bad=0。新开 330（这三处的中间态产物证人）。写成 D-261。CI：@@CIN@@、@@CIN2@@ 交接时未读 ⇒ 只登记号不轮询（R140）。

"""

BACK_NEW = [
    "**330. 三处 hover 淡入的『过程』还没有产物证人（R275）：本轮把 `SettingsSidebarRow` / 筛选段按钮 / `SearchField` 的动画 value 与画法对齐，"
    "判据只证明了两半是同一句话（源码形状），**没有**证明这条淡入在离屏通道里真的被切成可数的中间态。要么给这三处各配一条 `MotionFilmstripTests` 那条路的中间态证人"
    "（`Scenario` 得能在触发时翻 `hoveredForCapture`，并处理「新场景会改变别的守卫的对象数」⇒ 加一卷要全量重跑并登记名单为何变长，R98 那一课），"
    "要么显式记「源码已接、产物未量」并把它留在未交付清单上 —— 不许把对齐本身写成「淡入已验收」（R275 新开）**",
]

STATE_NEW = """## R275 状态（第 274 轮 / Round 272 · @@DATE@@）
最后更新：2026-10-21（本地 · R275 / 第 274 轮 / Round 272）：**三处悬停淡入在取证通道里从来没有过程 —— 画法与动画的触发条件对齐，并给这条规则一把会红的尺**（U-918…U-920 · D-261 · 产品 @@FILES@@ 文件 · 自评 88/105）

**本轮落地**：`SettingsView.swift` / `HistorySidebarView.swift` / `SearchField.swift` 的 hover 动画 value 改读合取式；新卷 `HoverAnimationChannelTests`（@@CELLS@@ 格，根由 `#filePath` 推）现读 files=@@FILES_SCANNED@@ sites=@@SITES@@ 裸读=0 判=PASS；刀 @@KN@@（@@ARM1@@、@@ARM2@@）；四件套 告警=@@BUILD@@ 全量 Executed=@@EXEC@@ failures=@@FAIL@@ skipped=@@SKIP@@ 帧=@@FRAMES@@ changed=@@CHANGED@@ missing=@@MISSING@@ dmg=@@DMG@@ 本机=@@VER@@；@@BATT@@；预检 tables=@@TBL@@ covered=@@COV@@ arms=@@PARMS@@ bad=0、310 缺口 @@GAPT@@ 张 / @@GAPA@@ 把。新开 330。

**下一轮（R276 / 第 275 轮 / Round 273）的 ⓪**：
⓪ 读 CI：@@CIN@@、@@CIN2@@ 与本轮新跑（只登记号不轮询，R140）。要验的两件：STEP[9]「Release script tests」在新门上转绿（errors 归 0 且 `Ran` 颗数不低于本笔），以及 STEP[11] 那两张 recording 帧在 runner 上是否仍报 changed —— 若 changed≠0 按 D-251 开具名出口，**不许改基线迁就**。
① **312 的具名出口（欠第七轮）**：按「纸」那一维推，本机 3.000 不许降（D-251）。
② 330（三处淡入的中间态产物证人）、329（206 处写死本机根，每张搬完重跑那张表）、328、323、322、317、314、315、316。
③ 310 的 @@GAPT@@ 张表、309 那 6 张；305、299、301、307、287/284、297/298/300、304、291 画法轴那四位。
④ 产品动效面：本轮 @@FILES@@ 个产品文件，但都是可测性；仍需按清账表点一个位真做动效或撤声明。
⑤ 用户闸门 220 路 A / 228② / 265。

"""


def render(s):
    for k, val in V.items():
        s = s.replace(k, val)
    if "@@" in s:
        die("渲染后仍有未替换占位符：" + s[:160])
    return s


for n in ("UI_NEW", "ITER_NEW", "DEC_NEW", "CHG_NEW", "STATE_NEW"):
    globals()[n] = render(globals()[n])
BACK_NEW = "\n\n".join(render(x) for x in BACK_NEW) + "\n"

ui_p = B["AGENT_UI_AUDIT.md"]
ui_old = rd(ui_p)
if "## 第 273 轮" not in ui_old:
    die("UI_AUDIT 找不到锚点")
cut = ui_old.index("## 第 273 轮")
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
        die(name + " 弄丢 " + str(len(lost)) + " 行：" + " | ".join(lost[:2])[:150])


for o, n, nm in ((ui_old, ui_new, "AGENT_UI_AUDIT.md"), (cg_old, cg_new, "CHANGELOG.md"),
                 (bk_old, bk_new, "AGENT_BACKLOG.md")):
    must_preserve(o, n, nm)

st_p = B["AGENT_STATE.md"]
st_old = rd(st_p)
if "## R274 状态" not in st_old:
    die("STATE 找不到锚点")
st_new = st_old.replace("## R274 状态", STATE_NEW + "## R274 状态", 1)
must_preserve(st_old, st_new, "AGENT_STATE.md")

ids = [int(x) for x in re.findall(r"- \*\*U-(\d+)", UI_NEW)]
if ids != list(range(918, 921)):
    die("U 号不连续：" + str(ids))
if "U-918…U-920" not in UI_NEW.splitlines()[0]:
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
if "D-261" in dc_old or "D-260" not in dc_old:
    die("D 号不对")
if bk_new.count("\n**330. ") != 1:
    die("新开 330 没落上")
if "## R275 状态" not in st_new:
    die("STATE 没轮换")

for p, t in ((ui_p, ui_new), (it_p, it_new), (dc_p, dc_new), (bk_p, bk_new), (cg_p, cg_new), (st_p, st_new)):
    with io.open(p, "w", encoding="utf-8") as h:
        h.write(t)

out, rc = sh([sys.executable, os.path.join(HERE, "report_cells_r258.py"), "headline"])
if rc != 0:
    die("FINAL_REPORT headline 刷新失败：" + out[-300:])
_sha, _ = sh(["git", "rev-parse", "HEAD"])
head_sha = _sha.strip().splitlines()[-1] if _sha.strip() else ""
out2, rc2 = sh([sys.executable, os.path.join(HERE, "report_cells_r258.py"), "sources", head_sha])
if rc2 != 0:
    die("FINAL_REPORT sources 格刷新失败：" + out2[-300:])
ran2, skip2 = battery()
if ran2 != pre_ran:
    die("写盘前后电池颗数不一致（" + pre_ran + " → " + ran2 + "）")
print("LEDGERS_R275 OK batt=Ran " + ran2 + " (skipped=" + skip2 + ") prod=" + str(len(prod))
      + " sites=" + g.group(2) + " 裸读=0 frames_changed=" + VW[6] + " knife=" + V["@@KN@@"]
      + " U=918..920 D=261 new=330")
print(out.strip().splitlines()[-1])
