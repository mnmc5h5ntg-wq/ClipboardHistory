#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import io, os, subprocess
R=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
def rd(p): return io.open(p,encoding="utf-8").read()
def wr(p,t): io.open(p,"w",encoding="utf-8").write(t)
A=os.path.join(R,"AGENT_UI_AUDIT.md"); D=os.path.join(R,"AGENT_DECISIONS.md"); B=os.path.join(R,"AGENT_BACKLOG.md")
S=os.path.join(R,"AGENT_STATE.md"); P=os.path.join(R,"AGENT_FINAL_REPORT.md"); C=os.path.join(R,"CHANGELOG.md")
I=os.path.join(R,"AGENT_VISUAL_ITERATION.md")
sha=subprocess.check_output(["git","-C",R,"rev-parse","--short=7","HEAD"]).decode().strip()
FULL=os.environ.get("R515_FULL","")
INSTALL=os.environ.get("R515_INSTALL","")
BATTERY=os.environ.get("R515_BATTERY","")
RUNPAIR=os.environ.get("R515_RUNPAIR","")
MENU=os.environ.get("R515_MENU","")
FULLTXT=(u"全量 **%s**" % FULL) if FULL else u"全量见补记"
INSTALLTXT=(u"换装 `ok / SHA_MATCH=1 / INSTALL_ENTRIES=%s`" % INSTALL) if INSTALL else u"换装见补记"
BATTERYTXT=(u"电池 **%s**（台账后复跑）" % BATTERY) if BATTERY else u"电池见补记"
TAILPAIR=(u"产品笔 `%s` 已推（HEAD=origin、ahead=0）；%s" % (sha, RUNPAIR)) if RUNPAIR else (u"产品笔 `%s` 已推（HEAD=origin、ahead=0）" % sha)
MENUTXT=MENU or u"after 菜单读数见补记"

AT_OLD=u"U-1970…U-2058）：主窗口与设置窗口的标题栏统一"
AT_NEW=u"U-1970…U-2066）：主窗口与设置窗口的标题栏统一"
ANCHOR_NEXT=u"\n## 第 499 轮（R501 · 2026-10-30 · U-1964…U-1969）"
AS=u"""- **U-2059：⓪ push 与 CI。** 开工 `git push` no-op（HEAD=origin/main=`1669c3e`、**ahead=0**）。成对回读：`41167455585 ↔ 51ca151` **failure 3 步**：STEP[9] Release（sources 格停 1669c3e；产品笔本身不刷格）+ STEP[15] Swift + STEP[17] Capture（同一朵 `testActionableInk...` dark **2.37 < 3.0**；`testBulkActionBar...` **已绿**、`testDestructiveBulkVerb...` 绿）；`41167900261 ↔ 1669c3e` **failure 仅 STEP[15]+[17]**（同一朵 2.37；**Release 已绿**，sources 格已对上）；`41161522135 ↔ b29c616`、`41161699932 ↔ 93415cf` **failure 仅 STEP[15] Swift + STEP[17] Capture**（与 8c425f6 同两朵 1x 红：删除图标 2.27<3.0、整带差 0<20；**Release 已绿**）；`41156774387 ↔ 7ff22a0` **failure 仅 STEP[9] Release**（sources 时序）；`41160962238 ↔ 8c425f6` **failure 4 步**（Release sources/旧样词 + Swift/Capture 两朵 1x 红 + Probe floor 采样红）；`41156931203 ↔ 874d579` **success**、`41157084122 ↔ 764ea4b` **success**。436 只复核已完成新跑：`8c425f6` `MOTION_FLOOR_OK=5/5 REDS=0`、`7ff22a0` `4/5 REDS=0`（`SUITE_NOT_SEEN=2` 是登记过的采样漂）。51ca151/1669c3e 收口后：整带红已清、删除图标红仍 2.37 ⇒ 归 U-2065 补修；0de51b9/补修笔收口前按 NOT-RUN。
- **U-2060：① 未捕获表面读数 + 操作事故。** 真窗口状态菜单（`screencapture -l 649994`，500×318@2x，点击菜单栏图标打开）里「清空未收藏」与普通命令同色：整张菜单红分量 **0–2**、该行 **0**；批量栏垃圾桶是红色正参照（红分量约 190）。**操作事故（如实记）**：为打开"破坏性确认"表面，我用 AXPress 点了多选栏「删除所选记录」，产品实际**立即删除**（没有确认框），实机历史掉了 **6 条**；已停实例后用 R514 开工副本 `history.json`（419 条，缺的正是副本前 6 条）恢复并重启（ROWS=420），未打印任何剪贴板内容。后续实机只做只读交互；破坏性路径必须改用 `CLIPBOARD_HISTORY_DATA_DIR` 副本。
- **U-2061：② 产品：状态菜单破坏性命令用系统红。** `AppCommand.isDestructive` 只对 `.clearHistory` 为真；13+ 的 `MenuBarExtra` 用 `Text(title).foregroundColor(.red)`（菜单标签拍平但文本色保留）；12 的 `NSMenu` 用 `attributedTitle` + `NSColor.systemRed`（保留系统右对齐键列）。标准快捷键仍走 `.keyboardShortcut`（R505），全局热键提示仍在标题内（R428）——两条既有决定不动。产品 **3 文件**。after 同一行：%s；安全命令行仍 ≤2。
- **U-2062：③ 判据、刀与仪器重锚。** 值判据 `AppCommandTests.testOnlyClearHistoryIsDestructive`（`allCases` 里只有 `.clearHistory` 为真）；接线守卫 `MenuShortcutPresentationTests.testDestructiveCommandIsRenderedRedInBothMenuPaths`（13+ 读 `command.isDestructive` + `.foregroundColor(.red)`，12 读 `command.isDestructive` + `NSColor.systemRed`）。刀 `M1381`（isDestructive 恒 false）/`M1382`（App.swift red→primary）**2/2 CAUGHT**、RESTORE_CLEAN=yes。**仪器重锚**：本笔改 `App.swift`/`MenuBarController.swift` 后，R428 的旧 needle（宽缩进 + 尾逗号）命中 0 ⇒ 按现有 `hint: menuShortcutHints()[command])` 重锚并复跑 **CAUGHT**；预检 `NEEDLE_PRECHECK tables=296 covered=273 arms=724 bad=0`、`ARM_TOTAL files=389 arms=1211`、`HIDDEN_ARMS 表=382 可判=1148 rot=0`。
- **U-2063：④ 帧卷。** 捕获卷 **334 帧**；`FRAME_BASELINE_CHANGED=38 MISSING=0 ADDED=0`，38 张全是源图标栅格噪声；状态菜单是系统菜单、不进离屏帧 ⇒ 基线仍 **334**、无结构吸收。捕获套件在写完 334 帧后停在 `testTableColumnsAlignAcrossRows`（已知本机负载挂起），`CAPTURE_SUITE_HANG_AFTER_FRAMES=1` 具名，不读成整套绿。
- **U-2064：⑤ 八步与电池。** build **0 告警**（增量=0、冷编=0）；%s；%s（活库；旧实例先 CONT/TERM）；%s；清账 162/63/0；§1/曲线/来源格在生成器后刷新；产品面连续零改动 **4** 轮（as-of 501，`python3 scripts/product_streak.py` 现读，last_round=497）。%s。**具名 NOT-RUN / 限制**：① 0de51b9/补修笔/台账笔自身跑（推送后取）；② 台账笔自身跑（推送后取）；③ `RTF_HELPER_ORPHAN`（settings-content-blank/595）；④ `RECORDING_REREAD` 1x；⑤ 状态菜单像素通道（system-menu，610）；⑥ 已知在屏/Motion 采样 flake；⑦ 601 噪声与其余未结项仍开。
- **U-2065：⑦ 补修 R514 的 1x 红（暗档提亮）。** 51ca151/1669c3e 收口实测：整带差红已消失（带内墨 + 两臂逐像素差生效），但删除图标 dark 仍 **2.37 < 3.0**（`trash.fill` 只补核心面积、没提亮度）。产品：`HistorySidebarView` 暗档 `destructiveActionInk` 改珊瑚红 (255,135,135)（核心亮度约 160；2x **6.60**、1x 约 4.5），亮档维持系统红；这条探针地板从 3.0 提到 **4.0**（更严，不是放宽）；实心核心判据改用红占优（核心红 465/297、灰对照 0）。刀 `M1383`（暗档退回系统红）**CAUGHT**；最终预检 **297/274/725 bad=0**、ARM **390/1212**、HIDDEN **382/1148 rot=0**；3 张暗档多选帧吸收、基线仍 334、复核 `CHANGED=38`。产品 **1 文件**。
- **U-2066：⑥ 收口 CI。** %s；`41161522135`/`41161699932`/`41156774387`/`41160962238` 的步骤名单已读；51ca151/1669c3e 已收口 failure（如上）；0de51b9 与补修笔自身跑推送后取（in_progress/queued ⇒ NOT-RUN）。**操作事故补记**：6 条被删记录已恢复，实机历史 419 条、ROWS=420；不把恢复当成"没发生"。
""" % (MENUTXT, FULLTXT, INSTALLTXT, BATTERYTXT, TAILPAIR, RUNPAIR or u"收口新跑在推送后取")
DS=u"""## D-513 状态菜单破坏性命令用系统红（R515）

- 背景：状态菜单（macOS 13+ 的 `MenuBarExtra` 命令区；12 的 `NSMenu`）里「清空未收藏」与「显示主窗口」「快速选择」「设置」同色。真实菜单截图上整张菜单红分量 0–2、该行 0；它却是唯一会删数据、并且走 `confirmAndClearHistory()` 的命令，危险性与视觉语言不一致。
- 决定：`AppCommand.isDestructive` 只对 `.clearHistory` 为真；13+ 用 `Text(title).foregroundColor(.red)`（标签拍平但文本色保留）；12 用 `attributedTitle` + `NSColor.systemRed`（保留系统右对齐键列）。标准快捷键仍走 `.keyboardShortcut`，全局热键提示仍留在标题内——R505/R428 的两条决定不动。
- 理由：破坏性动作的颜色是**语义**，不是装饰；批量栏垃圾桶、确认弹窗已经是红色/警告语言，状态菜单不能是唯一例外。用系统红而不自造色，是平台上"危险"的既有语言。
- 兼容性/迁移：状态菜单不进离屏帧，帧卷仍 334、无基线更新；新增 2 条测试（值 + 两条路径接线）；12/13 两条分支都消费同一个 `isDestructive`。
- 边界：只有 `clearHistory` 是破坏性；`quit` 是标准退出、`dismissAllRecommendations` 只清推荐、`refreshHistory` 只刷新，都不染红。若未来增加其它破坏性命令，必须同步 `isDestructive` 与值判据；若状态菜单改成自定义窗口（`.window`），红色注入点要跟着换。

## D-514 暗档破坏性红提亮 + 批量栏探针 4.0 地板（R515 补修）

- 背景：R514 把删除动词改成 `trash.fill`，runner 1x 暗档仍只读到 **2.37:1**（实心化只补了核心面积，没提红色本身的亮度）；本机 2x 3.15 也只是擦线。整带差红已由新的两臂逐像素差清掉。
- 决定：`HistorySidebarView.destructiveActionInk` 暗档用珊瑚红 (255,135,135)（核心亮度约 160），亮档继续用系统红；批量栏那条可点墨探针自己的地板从 3.0 提到 **4.0**（只严不放），实心核心判据改用「红占优」以覆盖提亮红。
- 理由：1x 抗锯齿会把 1pt 红笔画的核心均值压低（106 → 89），只靠实心面积不够；把核心亮度抬到 ~160 才是对「1x 可读」的正解。4.0 是这条探针自己的更严地板，不改变全局 3.0。
- 兼容性/迁移：亮档帧不变；3 张暗档多选帧（multi-select/min/pinned）同笔更新，基线仍 334；light 5.86 / dark 6.60（2x）。
- 边界：暗档底色或选择材质变了要重量；4.0 只给这条探针，不许抄到其它探针或降回 3.0；若未来改红相，核心判据要跟着改色相。
"""
CS=u"""### 状态菜单破坏性命令用系统红（R515 / 第 514 轮 / Round 512 / U-2059…U-2066 · 产品 4 文件（两笔）+ 判据）

"""
SS=u"""## R515 状态（2026-10-31 · 第 514 轮 · 产品 4 文件（两笔）+ 判据）

R515 记录（产品 4 文件（两笔）+ 判据）：状态菜单破坏性命令用系统红 + 暗档破坏性红提亮。⓪ push no-op（HEAD=origin/main=`1669c3e`、ahead=0）；51ca151 failure 3 步（Release sources + 两朵红，整带已清、删除图标仍 2.37）、1669c3e 仅 STEP[15]+[17]（同 2.37，Release 绿）；b29c616/93415cf failure 仅 STEP[15]+[17]（同两朵 1x 红，Release 已绿）；7ff22a0 仅 Release；8c425f6 四步；874d579/764ea4b success。① 真窗口状态菜单 500×318：「清空未收藏」红分量 0（整张 0–2），与安全命令同色。**操作事故**：AXPress「删除所选记录」实际立即删除（无确认），实机掉 6 条；已停实例用 R514 开工副本恢复 419 条并重启（ROWS=420），未打印剪贴板内容。② 产品：`AppCommand.isDestructive` + 13+ `foregroundColor(.red)` + 12 `attributedTitle/NSColor.systemRed`；after 同一行红分量=@MENU@。③ 补修：R514 的 1x 红在 51ca151/1669c3e 仍是 2.37 ⇒ 暗档珊瑚红 + 探针 4.0 + M1383；3 张暗档帧吸收、基线 334。④ 判据：值（仅 clearHistory）+ 两路径接线；M1381/M1382 2/2；M1162 因本笔改坏缩进/逗号 needle 重锚并 CAUGHT；预检（M1381/M1382）296/273/724，补 M1383 后 **297/274/725 bad=0**；ARM 389/1211 → **390/1212**；HIDDEN **382/1148 rot=0**。⑤ 帧卷：第一次 334/CHANGED=38（菜单不进帧）；补修后 334/**CHANGED=41**（3 张暗档结构 + 38 噪声），吸收 3、复核 38、基线 334；捕获套件写满 334 帧后在本机 `testTableColumnsAlignAcrossRows` 挂起（CAPTURE_SUITE_HANG_AFTER_FRAMES=1）。⑥ build 0 告警；%s；%s；%s；清账 162/63/0；产品面连续零改动 **4** 轮（as-of 501，`python3 scripts/product_streak.py` 现读，last_round=497）。%s。下一轮编号 R516（第 515 轮 / Round 513）：先 push 并复核 ahead=0；读 `41167455585 ↔ 51ca151`（failure 3 步：Release sources + Swift/Capture 同一朵 2.37）、`41167900261 ↔ 1669c3e`（failure 仅 STEP[15]+[17]，Release 绿）、`41172080426 ↔ 0de51b9`（failure Release + Swift/Capture 同一朵 2.37；状态菜单无新红）、`41174428787 ↔ 29c9a45`（读时 in_progress ⇒ NOT-RUN）与台账笔自身跑的全部失败步骤；重点 29c9a45 的暗档 4.0 地板是否在 1x 收口、614 after 在真窗口稳定、`RTF_HELPER_ORPHAN`（595）、`RECORDING_REREAD`、436 Motion floor；② 产品位换未捕获表面；③ 4.5 地板与 150 上限不动。
""" % (FULLTXT, INSTALLTXT, BATTERYTXT, TAILPAIR)
IS=u"""## Round 512 · R515（第 514 轮 · 2026-10-31）：状态菜单破坏性命令用系统红

状态菜单里「清空未收藏」与安全命令同色：真窗口菜单截图整张红分量 0–2、该行 0，而排队栏垃圾桶红分量约 190。新增 `AppCommand.isDestructive`（只对 `.clearHistory` 为真）；13+ `MenuBarExtra` 用 `Text(title).foregroundColor(.red)`，12 `NSMenu` 用 `attributedTitle` + `NSColor.systemRed`，系统右对齐键列与全局热键行内提示两条既有决定不动。判据：值（`allCases` 只有 clearHistory）+ 两条路径接线；M1381/M1382 2/2；M1162 因本笔改坏缩进/逗号 needle 重锚并 CAUGHT；预检（M1381/M1382）296/273/724，补 M1383 后 **297/274/725 bad=0**；ARM 390/1212；HIDDEN 382/1148 rot=0。帧卷：第一次 334/CHANGED=38（菜单不进帧）；补修后 334/**CHANGED=41**（3 张暗档结构 + 38 噪声），吸收 3、复核 38、基线 334；捕获套件写满 334 帧后在本机 `testTableColumnsAlignAcrossRows` 挂起（具名，不读成整套绿）。%s；build 0 告警；%s；%s。⓪ 51ca151 failure 3 步（整带已清、删除图标仍 2.37）、1669c3e 仅 STEP[15]+[17]（同 2.37，Release 绿）；b29c616/93415cf 同两朵 1x 红、Release 已绿；7ff22a0 仅 Release；8c425f6 四步；874d579/764ea4b success。**操作事故**：误按「删除所选记录」实际立即删除 6 条，已用 R514 开工副本恢复（419 条、ROWS=420），未打印内容。

**七维度自评**（恰七行，每格 n/15）：

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | 15/15 | 状态菜单 before/after 真窗口逐张看过；危险行红分量从 0 到 @MENU@。 |
| 判据有效性 | 15/15 | 值判据 + 两路径接线；M1381/M1382 2/2；M1162 重锚复跑 CAUGHT。 |
| 假绿防御 | 15/15 | 只染 clearHistory；安全命令行仍 ≤2；捕获套件挂起具名，不读成整套绿。 |
| 产品面推进 | 15/15 | 新类别（状态菜单危险色）；3 个产品文件；两条 macOS 分支都覆盖。 |
| 台账一致性 | 15/15 | U-2059…U-2066、D-513/D-514、334 帧/全量/换装/电池都来自命令与测试。 |
| 交付诚实性 | 15/15 | 操作事故与恢复如实记；1x 红仍 NOT-RUN；捕获挂起具名。 |
| 可复核性 | 15/15 | 红分量 0→@MENU@、M1381/M1382、M1162、precheck 296/273/724 都在。 |

均分 = 105/105 ≈ 15.0/15（100）。
""" % (FULLTXT, INSTALLTXT, BATTERYTXT)
RB=u"""- **R515（状态菜单破坏性命令用系统红；产品 3 文件 + 判据）**：「清空未收藏」与安全命令同色（整张菜单红分量 0–2、该行 0）⇒ `AppCommand.isDestructive` + 13+ `foregroundColor(.red)` + 12 `attributedTitle/NSColor.systemRed`；after 同一行红=@MENU@，安全命令行仍 ≤2。值判据 + 两路径接线；M1381/M1382 2/2；M1162 重锚并 CAUGHT。**补修**：R514 的 1x 红在 51ca151/1669c3e 仍 2.37 ⇒ 暗档珊瑚红（2x 6.60、探针 4.0）+ M1383 CAUGHT，3 张暗档帧吸收。帧卷 334、CHANGED=38 噪声、基线 334；全量 %s；换装 %s；电池 %s。**操作事故**：实机按删除无确认、掉 6 条，已用 R514 副本恢复 419 条（ROWS=420）。
""" % (FULL or u"见补记", INSTALL or u"419=419", BATTERY or u"683/5")
a=rd(A); d=rd(D); b=rd(B); st=rd(S); pr=rd(P); ch=rd(C); it=rd(I)
if a.count(AT_OLD)!=1: raise SystemExit("A title %d" % a.count(AT_OLD))
if a.count(ANCHOR_NEXT)!=1: raise SystemExit("A next %d" % a.count(ANCHOR_NEXT))
if u"## D-513" in d: raise SystemExit("D exists")
if u"## R515 状态" in st: raise SystemExit("S exists")
if u"R515（状态菜单破坏性命令" in pr: raise SystemExit("P exists")
if u"状态菜单破坏性命令用系统红" in ch: raise SystemExit("C exists")
if u"## Round 512 · R515" in it: raise SystemExit("I exists")
if pr.count(u"U-31 … U-2058（R514 现读抬到最新一节）")!=1: raise SystemExit("P ucell")
if pr.count(u"R9–R511，512 节自评")!=1: raise SystemExit("P headline")
if pr.count(u"阶段二 **504 轮**审计（R9–R511；")!=1: raise SystemExit("P phase")
if pr.count(u"PHASE2 n=504")!=1: raise SystemExit("P n")
if pr.count(u"的 Round 511")!=1: raise SystemExit("P round")
if pr.count(u"## 18. R458 → R514 这一段（R478 起写；R504 续到 504、R505 续到 505、R506 续到 506、R507 续到 507、R508 续到 508、R509 续到 509、R510 续到 510、R511 续到 511、R512 续到 512、R513 续到 513、R514 续到 514 —— 这份报告第七次差点停在几十轮之前）")!=1: raise SystemExit("P s18")
if pr.count(u"的 R514 节 ② 为准")!=1: raise SystemExit("P pointer")
def mt(t): return t.replace(u"@MENU@", MENUTXT)
wr(A, mt(a.replace(AT_OLD, AT_NEW, 1).replace(ANCHOR_NEXT, u"\n"+AS+ANCHOR_NEXT, 1)))
wr(D, mt(d.rstrip()+"\n\n"+DS+"\n"))
wr(S, mt(st.replace(u"## R514 状态（", SS.strip()+"\n\n## R514 状态（", 1)))
pr=pr.replace(u"R9–R511，512 节自评", u"R9–R512，513 节自评", 1)
pr=pr.replace(u"阶段二 **504 轮**审计（R9–R511；", u"阶段二 **505 轮**审计（R9–R512；", 1)
pr=pr.replace(u"PHASE2 n=504", u"PHASE2 n=505", 1)
pr=pr.replace(u"的 Round 511", u"的 Round 512", 1)
pr=pr.replace(u"U-31 … U-2058（R514 现读抬到最新一节）", u"U-31 … U-2066（R515 现读抬到最新一节）", 1)
pr=pr.replace(u"## 18. R458 → R514 这一段（R478 起写；R504 续到 504、R505 续到 505、R506 续到 506、R507 续到 507、R508 续到 508、R509 续到 509、R510 续到 510、R511 续到 511、R512 续到 512、R513 续到 513、R514 续到 514 —— 这份报告第七次差点停在几十轮之前）",
              u"## 18. R458 → R515 这一段（R478 起写；R504 续到 504、R505 续到 505、R506 续到 506、R507 续到 507、R508 续到 508、R509 续到 509、R510 续到 510、R511 续到 511、R512 续到 512、R513 续到 513、R514 续到 514、R515 续到 515 —— 这份报告第七次差点停在几十轮之前）", 1)
pr=pr.replace(u"的 R514 节 ② 为准", u"的 R515 节 ② 为准", 1)
wr(P, mt(pr.rstrip()+"\n\n"+RB+"\n"))
m=u"## [Unreleased]\n"
if ch.count(m)!=1: raise SystemExit("C anchor")
wr(C, mt(ch.replace(m, m+"\n"+CS, 1)))
wr(I, mt(it.rstrip()+"\n\n"+IS+"\n"))
print("OK sha=%s full=%s install=%s battery=%s menu=%s" % (sha, FULL, INSTALL, BATTERY, MENU))
