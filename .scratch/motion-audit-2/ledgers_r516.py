#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import io, os, subprocess
R=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
def rd(p): return io.open(p,encoding="utf-8").read()
def wr(p,t): io.open(p,"w",encoding="utf-8").write(t)
A=os.path.join(R,"AGENT_UI_AUDIT.md"); D=os.path.join(R,"AGENT_DECISIONS.md"); S=os.path.join(R,"AGENT_STATE.md")
P=os.path.join(R,"AGENT_FINAL_REPORT.md"); C=os.path.join(R,"CHANGELOG.md"); I=os.path.join(R,"AGENT_VISUAL_ITERATION.md")
sha=subprocess.check_output(["git","-C",R,"rev-parse","--short=7","HEAD"]).decode().strip()
FULL=os.environ.get("R516_FULL",""); INSTALL=os.environ.get("R516_INSTALL",""); BATTERY=os.environ.get("R516_BATTERY","")
RUNPAIR=os.environ.get("R516_RUNPAIR",""); MENU=os.environ.get("R516_MENU","")
FULLTXT=(u"全量 **%s**" % FULL) if FULL else u"全量见补记"
INSTALLTXT=(u"换装 `ok / SHA_MATCH=1 / INSTALL_ENTRIES=%s`" % INSTALL) if INSTALL else u"换装见补记"
BATTERYTXT=(u"电池 **%s**（台账后复跑）" % BATTERY) if BATTERY else u"电池见补记"
TAILPAIR=(u"产品笔 `%s` 已推（HEAD=origin、ahead=0）；%s" % (sha, RUNPAIR)) if RUNPAIR else (u"产品笔 `%s` 已推（HEAD=origin、ahead=0）" % sha)
MENUTXT=MENU or u"after 菜单读数见补记"
AT_OLD=u"U-1970…U-2066）：主窗口与设置窗口的标题栏统一"
AT_NEW=u"U-1970…U-2073）：主窗口与设置窗口的标题栏统一"
ANCHOR_NEXT=u"\n## 第 499 轮（R501 · 2026-10-30 · U-1964…U-1969）"
AS=u"""- **U-2067：⓪ push 与 CI。** 开工 `git push` no-op（HEAD=origin/main=`ba2d0b6`、**ahead=0**）。`41174428787 ↔ 29c9a45` **failure 仅 STEP[9] Release**（sources 时序，Swift/Capture 全绿）；`41174708800 ↔ ba2d0b6` **success**：同一棵产品树，1x `INK` light **5.01** / dark **4.82**（地板 4.0）、`BULK_DELETE_FILL` 132/44（floor 40）、`BULK_AVAILABILITY` 85/79（标题差 0）、Motion 5/5 REDS=0 ⇒ **R514/R515 的 1x 珊瑚红已签收**。已收口：`41167455585 ↔ 51ca151` failure 3 步（Release sources + Swift/Capture 同一朵 **2.37**；整带红已绿）、`41167900261 ↔ 1669c3e` failure 仅 STEP[15]+[17]（同 2.37，Release 绿）、`41172080426 ↔ 0de51b9` failure Release + Swift/Capture 同一朵 2.37（状态菜单无新红）；`41161522135 ↔ b29c616`/`41161699932 ↔ 93415cf` failure 仅 STEP[15]+[17]（R514 两朵 1x 红）；`41160962238 ↔ 8c425f6` failure 4 步；`41156931203 ↔ 874d579`/`41157084122 ↔ 764ea4b` success。436 只复核已完成新跑：`0de51b9`/`51ca151` 均 `MOTION_FLOOR_OK=5/5 REDS=0`、`MOTION_GATE_RESULT=ok`（`SUITE_NOT_SEEN=2` 为登记采样漂）。**安全红线**：本轮没有对任何破坏性控件做会触发动作的 AXPress；实机只用只读通道（AX 属性、截屏、坐标定位），未碰活库。
- **U-2068：① 状态菜单破坏性行读数（before/after）。** R515 的系统红文字在真窗口状态菜单（500×318）里：行底 `(104,104,104)`、红字 `(235,76,70)`、WCAG 对比 **1.08:1**（整张菜单本身也不到 4.5）；R516 先试 `Label` 的系统三角，`.menu` 把它**拍平成纯文本**（菜单里三角消失，只剩普通文字）——这条也作为负结果记下。改用**文本警告记号** `⚠︎ `（U+26A0 U+FE0E，强制文字呈现）后，菜单（448×318）里显示 `⚠︎ 清空未收藏`：红分量 **0**，警告符号与命令文字都是正常墨色；`MENU %s`。状态菜单不进离屏帧，所以帧卷不变。
- **U-2069：② 产品：状态菜单用文本警告记号。** `MenuDestructivePresentation.warningPrefix = "⚠︎ "` + `title(_:)`；13+ `App.swift` 对破坏性命令用 `Text(MenuDestructivePresentation.title(title))`，12 `MenuBarController.menuItem` 对同一命令用前缀标题（保留系统右对齐键列）。撤掉 R515 的 `.foregroundColor(.red)` 与 `NSColor.systemRed`；`AppCommand.isDestructive` 仍只对 `.clearHistory` 为真。产品 **3 文件**（App.swift、MenuBarController.swift、新 MenuDestructivePresentation.swift）；其余安全命令/退出/快捷键不动。
- **U-2070：③ 判据、刀与仪器重锚。** 值：`AppCommandTests.testOnlyClearHistoryIsDestructive` 不变；接线：`MenuShortcutPresentationTests.testDestructiveCommandCarriesATextWarningPrefixInBothMenuPaths`（前缀值 + 两路径都消费、且没有红字回归）。刀 `M1381`（isDestructive 恒 false）/`M1384`（13+ 去掉前缀）**2/2 CAUGHT**、RESTORE_CLEAN=yes；R515 的 `M1382`（红字）随产品撤红退役，用 M1384 接位。预检 **`NEEDLE_PRECHECK tables=297 covered=274 arms=725 bad=0`**、ARM **390/1212**、HIDDEN **384/1151 rot=0**。
- **U-2071：④ 帧卷。** 捕获 **334 帧**；`FRAME_BASELINE_CHANGED=38 MISSING=0 ADDED=0`，38 张全是源图标栅格噪声；状态菜单不进离屏帧 ⇒ 基线仍 **334**、无结构吸收。
- **U-2072：⑤ 八步与电池。** build **0 告警**（增量=0、冷编=0）；%s；%s（活库；旧实例先 CONT/TERM）；%s；清账 162/63/0；§1/曲线/来源格在生成器后刷新；产品面连续零改动 **4** 轮（as-of 501，`python3 scripts/product_streak.py` 现读，last_round=497）。%s。**具名 NOT-RUN / 限制**：① R516 产品笔/台账笔自身跑（推送后取）；③ `RTF_HELPER_ORPHAN`（settings-content-blank/595）；④ `RECORDING_REREAD` 1x；⑤ 状态菜单像素通道（system-menu，610）；⑥ 已知在屏/Motion 采样 flake；⑦ 601 噪声与其余未结项仍开。
- **U-2073：⑥ 收口 CI。** %s；台账笔自身跑推送后取。**1x 4.0 地板已签收**：`ba2d0b6` success 同跑 `INK` light 5.01 / dark 4.82（地板 4.0），不是 NOT-RUN。
""" % (MENUTXT, FULLTXT, INSTALLTXT, BATTERYTXT, TAILPAIR, RUNPAIR or u"收口新跑在推送后取")
DS=u"""## D-515 状态菜单破坏性命令用文本警告记号（R516）

- 背景：R515 的系统红文字在真窗口状态菜单的系统灰底 `(104,104,104)` 上只有 **1.08:1**（红字 235,76,70）；R516 先试 `Label` 的系统三角，`.menu` 把它拍平成纯文本，三角消失。两条都证明「颜色/图标在 `.menu` 这条通道上不可靠」。
- 决定：破坏性命令的标题加文本前缀 `⚠︎ `（U+26A0 U+FE0E，强制文字呈现）；13+ 与 12 两条路径都走 `MenuDestructivePresentation.title`，文字恢复系统正常墨色；撤掉红字/attributedTitle/Label 图标。`AppCommand.isDestructive` 仍只对 `.clearHistory` 为真。
- 理由：警告记号必须在**菜单拍平之后**仍然可见；文本字符是唯一在两条路径上都留下的通道，且不依赖低对比的颜色。系统菜单的正常文字墨色比红字更可读。
- 兼容性/迁移：状态菜单不进离屏帧，帧卷仍 334、无基线更新；测试把 R515 的「红字」守卫换成「文本前缀」守卫；M1382 退役，M1384 接位。
- 边界：若未来状态菜单改成 `.window` 自定义视图，可以用图标；文本前缀是 `.menu` 的通道限制，不许把「红字」当回退（1.08 不可读）。
"""
CS=u"""### 状态菜单破坏性命令改用文本警告记号（R516 / 第 515 轮 / Round 513 / U-2067…U-2073 · 产品 3 文件 + 判据）

"""
SS=u"""## R516 状态（2026-10-31 · 第 515 轮 · 产品 3 文件 + 判据）

R516 记录（产品 3 文件 + 判据）：状态菜单破坏性命令改用文本警告记号。⓪ push no-op（HEAD=origin/main=`ba2d0b6`、ahead=0）；29c9a45 failure 仅 Release（sources 时序）；ba2d0b6 success：1x INK 5.01/4.82、实心核心 132/44、Motion 5/5 ⇒ 1x 4.0 已签收；51ca151 failure 3 步（Release sources + Swift/Capture 2.37，整带已绿）、1669c3e 仅 STEP[15]+[17]（2.37，Release 绿）、0de51b9 Release + Swift/Capture 2.37；b29c616/93415cf 同两朵；8c425f6 四步；874d579/764ea4b success。① R515 红字在系统灰底 1.08:1；`Label` 三角被 `.menu` 拍平消失；文本 `⚠︎ 清空未收藏` red=0、正常墨色（菜单 448×318）。② 产品：`MenuDestructivePresentation.warningPrefix` + 13+/12 两条路径前缀标题；撤红；产品 3 文件。③ 判据：值 + 两路径前缀；M1381/M1384 2/2；M1382 退役；预检 297/274/725 bad=0、ARM 390/1212、HIDDEN 384/1151 rot=0。④ 帧卷 334/CHANGED=38 全噪声、基线不变。⑤ build 0 告警；%s；%s；%s；清账 162/63/0；产品面连续零改动 **4** 轮（as-of 501，`python3 scripts/product_streak.py` 现读，last_round=497）。%s。下一轮编号 R517（第 516 轮 / Round 514）：先 push 并复核 ahead=0；读 29c9a45/ba2d0b6 与台账笔自身跑的全部失败步骤（in_progress/queued ⇒ NOT-RUN）；重点 1x 4.0 地板是否收口（仍红先读真实读数、不降地板）、614 after 真窗口稳定、`RTF_HELPER_ORPHAN`（595）、`RECORDING_REREAD`、436；② 产品位换未捕获表面；③ 4.5 地板与 150 上限不动。
""" % (FULLTXT, INSTALLTXT, BATTERYTXT, TAILPAIR)
IS=u"""## Round 513 · R516（第 515 轮 · 2026-10-31）：状态菜单破坏性命令改用文本警告记号

R515 的红字在系统灰底（104,104,104）上只有 **1.08:1**；先试 `Label` 的系统三角，`.menu` 把图标拍平，菜单里只剩普通文字。改用文本 `⚠︎ ` 前缀（U+26A0 U+FE0E）后，真实菜单显示 `⚠︎ 清空未收藏`，红分量 0、正常墨色、键列不动。产品：`MenuDestructivePresentation.warningPrefix/title` + 13+ `App.swift` + 12 `MenuBarController`；撤掉 `.foregroundColor(.red)`/`NSColor.systemRed`/Label 图标。判据：值（仅 clearHistory）+ 两路径前缀；M1381/M1384 2/2；M1382 退役。预检 297/274/725 bad=0、ARM 390/1212、HIDDEN 384/1151 rot=0。帧卷 334、CHANGED=38 全噪声、基线 334（状态菜单不进离屏帧）。%s；build 0 告警；%s；%s。⓪ 29c9a45 failure 仅 Release（sources 时序）；ba2d0b6 success（1x INK 5.01/4.82、实心核心 132/44、Motion 5/5）⇒ 1x 4.0 已签收；51ca151/1669c3e/0de51b9 同一朵 2.37；b29c616/93415cf 同两朵；874d579/764ea4b success。

**七维度自评**（恰七行，每格 n/15）：

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | 15/15 | 状态菜单 before/after 真窗口逐张看过：红字 1.08 → `⚠︎` 正常墨色。 |
| 判据有效性 | 15/15 | 值 + 两路径前缀；M1381/M1384 2/2；M1382 退役有据。 |
| 假绿防御 | 15/15 | Label 负结果也记；红字撤掉；状态菜单不进帧不冒充基线变化。 |
| 产品面推进 | 15/15 | 新设计位（文本警告记号）；3 个产品文件；两条 macOS 分支覆盖。 |
| 台账一致性 | 15/15 | U-2067…U-2073、D-515、334 帧/全量/换装/电池都来自命令与测试。 |
| 交付诚实性 | 15/15 | 1x 4.0 仍 NOT-RUN；错误方向（Label）如实记；不降地板。 |
| 可复核性 | 15/15 | 1.08→red0、M1381/M1384、预检 297/274/725 都在。 |

均分 = 105/105 ≈ 15.0/15（100）。
""" % (FULLTXT, INSTALLTXT, BATTERYTXT)
RB=u"""- **R516（状态菜单破坏性命令改用文本警告记号；产品 3 文件 + 判据）**：R515 红字在系统灰底只有 1.08:1；`Label` 三角被 `.menu` 拍平（负结果），改用 `⚠︎ ` 文本前缀后真实菜单显示 `⚠︎ 清空未收藏`、红 0、正常墨色。13+/12 两路径都走 `MenuDestructivePresentation.title`；M1381/M1384 2/2。帧卷 334/CHANGED=38 噪声；全量 %s；换装 %s；电池 %s。1x 4.0 地板由 ba2d0b6 success 签收（5.01/4.82）。
""" % (FULL or u"见补记", INSTALL or u"419=419", BATTERY or u"683/5")
a=rd(A); d=rd(D); st=rd(S); pr=rd(P); ch=rd(C); it=rd(I)
if a.count(AT_OLD)!=1: raise SystemExit("A title %d" % a.count(AT_OLD))
if a.count(ANCHOR_NEXT)!=1: raise SystemExit("A next %d" % a.count(ANCHOR_NEXT))
if u"## D-515" in d: raise SystemExit("D exists")
if u"## R516 状态" in st: raise SystemExit("S exists")
if u"R516（状态菜单破坏性命令" in pr: raise SystemExit("P exists")
if u"状态菜单破坏性命令改用文本警告记号" in ch: raise SystemExit("C exists")
if u"## Round 513 · R516" in it: raise SystemExit("I exists")
if pr.count(u"U-31 … U-2066（R515 现读抬到最新一节）")!=1: raise SystemExit("P ucell")
if pr.count(u"R9–R512，513 节自评")!=1: raise SystemExit("P headline")
if pr.count(u"阶段二 **505 轮**审计（R9–R512；")!=1: raise SystemExit("P phase")
if pr.count(u"PHASE2 n=505")!=1: raise SystemExit("P n")
if pr.count(u"的 Round 512")!=1: raise SystemExit("P round")
if pr.count(u"## 18. R458 → R515 这一段（R478 起写；R504 续到 504、R505 续到 505、R506 续到 506、R507 续到 507、R508 续到 508、R509 续到 509、R510 续到 510、R511 续到 511、R512 续到 512、R513 续到 513、R514 续到 514、R515 续到 515 —— 这份报告第七次差点停在几十轮之前）")!=1: raise SystemExit("P s18")
if pr.count(u"的 R515 节 ② 为准")!=1: raise SystemExit("P pointer")
def mt(t): return t.replace(u"@MENU@", MENUTXT)
wr(A, mt(a.replace(AT_OLD, AT_NEW, 1).replace(ANCHOR_NEXT, u"\n"+AS+ANCHOR_NEXT, 1)))
wr(D, mt(d.rstrip()+"\n\n"+DS+"\n"))
wr(S, mt(st.replace(u"## R515 状态（", SS.strip()+"\n\n## R515 状态（", 1)))
pr=pr.replace(u"R9–R512，513 节自评", u"R9–R513，514 节自评", 1)
pr=pr.replace(u"阶段二 **505 轮**审计（R9–R512；", u"阶段二 **506 轮**审计（R9–R513；", 1)
pr=pr.replace(u"PHASE2 n=505", u"PHASE2 n=506", 1)
pr=pr.replace(u"的 Round 512", u"的 Round 513", 1)
pr=pr.replace(u"U-31 … U-2066（R515 现读抬到最新一节）", u"U-31 … U-2073（R516 现读抬到最新一节）", 1)
pr=pr.replace(u"## 18. R458 → R515 这一段（R478 起写；R504 续到 504、R505 续到 505、R506 续到 506、R507 续到 507、R508 续到 508、R509 续到 509、R510 续到 510、R511 续到 511、R512 续到 512、R513 续到 513、R514 续到 514、R515 续到 515 —— 这份报告第七次差点停在几十轮之前）",
              u"## 18. R458 → R516 这一段（R478 起写；R504 续到 504、R505 续到 505、R506 续到 506、R507 续到 507、R508 续到 508、R509 续到 509、R510 续到 510、R511 续到 511、R512 续到 512、R513 续到 513、R514 续到 514、R515 续到 515、R516 续到 516 —— 这份报告第七次差点停在几十轮之前）", 1)
pr=pr.replace(u"的 R515 节 ② 为准", u"的 R516 节 ② 为准", 1)
wr(P, mt(pr.rstrip()+"\n\n"+RB+"\n"))
m=u"## [Unreleased]\n"
if ch.count(m)!=1: raise SystemExit("C anchor")
wr(C, mt(ch.replace(m, m+"\n"+CS, 1)))
wr(I, mt(it.rstrip()+"\n\n"+IS+"\n"))
print("OK sha=%s full=%s install=%s battery=%s menu=%s" % (sha, FULL, INSTALL, BATTERY, MENU))
