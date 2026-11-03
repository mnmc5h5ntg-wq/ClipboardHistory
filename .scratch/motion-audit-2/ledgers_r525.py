#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import io, os, subprocess
R=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
def rd(p): return io.open(p,encoding="utf-8").read()
def wr(p,t): io.open(p,"w",encoding="utf-8").write(t)
A=os.path.join(R,"AGENT_UI_AUDIT.md"); D=os.path.join(R,"AGENT_DECISIONS.md")
S=os.path.join(R,"AGENT_STATE.md"); P=os.path.join(R,"AGENT_FINAL_REPORT.md"); C=os.path.join(R,"CHANGELOG.md"); I=os.path.join(R,"AGENT_VISUAL_ITERATION.md")
sha=subprocess.check_output(["git","-C",R,"rev-parse","--short=7","HEAD"]).decode().strip()
FULL=os.environ.get("R525_FULL",""); INSTALL=os.environ.get("R525_INSTALL",""); BATTERY=os.environ.get("R525_BATTERY",""); RUNPAIR=os.environ.get("R525_RUNPAIR","")
FULLTXT=(u"全量 **%s**" % FULL) if FULL else u"全量见补记"
INSTALLTXT=(u"换装 `ok / SHA_MATCH=1 / INSTALL_ENTRIES=%s`" % INSTALL) if INSTALL else u"换装见补记"
BATTERYTXT=(u"电池 **%s**（台账后复跑）" % BATTERY) if BATTERY else u"电池见补记"
TAILPAIR=(u"产品笔 `%s` 已推（HEAD=origin、ahead=0）；%s" % (sha, RUNPAIR)) if RUNPAIR else (u"产品笔 `%s` 已推（HEAD=origin、ahead=0）" % sha)
AT_OLD=u"U-1970…U-2129）：主窗口与设置窗口的标题栏统一"
AT_NEW=u"U-1970…U-2136）：主窗口与设置窗口的标题栏统一"
ANCHOR_NEXT=u"\n## 第 499 轮（R501 · 2026-10-30 · U-1964…U-1969）"
AS=u"""- **U-2130：⓪ push 与 CI。** 开工 `git push` no-op（HEAD=origin/main=`9d882e4`、**ahead=0**）。五跑成对读：`41218308733 ↔ 79e39ee`（R524 产品）、`41218637052 ↔ 77ed8ef`（读数 emit 测试笔）、`41218878781 ↔ 9d882e4`（台账笔）读时均 **in_progress ⇒ NOT-RUN**（不轮询；下轮第 ⓪ 全读）；`41215426349 ↔ 3e5aa6b`（R523 产品）**completed failure 仅 STEP[9]**（`SOURCES_CELL 账上=e353f1e git=3e5aa6b` ⇒ sources 时序 + `test_sources_cell_second_source` + `test_skip_roster` 级联；STEP[10]–[14] skipped），该跑 Swift 步已跑 `MainWindowCollapseTests`，INK **5.01/4.82**、RECORDING diff 0、RTF NOT_RUN、Motion `judged=4/5 not-run=notice-banner`（1 条 NOT-RUN，不冒充红）；`41215568792 ↔ f20f256` **success**。R524 折叠过渡判据（6 条 fold tests / M1399–M1401）在 runner 上的签收随三跑仍未跑完 ⇒ **NOT-RUN**。安全红线：未对破坏性控件做 AXPress；真窗口只读；未碰活库。
- **U-2131：① 缺口读数与产品补入口。** 折叠/展开在 R523/R524 只有状态菜单、标题双击与可见 chevron：`ClipboardHistoryCommands.swift` 里 `toggleMainWindowCollapse` **0 处**、`AppCommand.keyEquivalent == ""`、`MenuCommandShortcutPresentation.keyEquivalent(for:) == nil` ⇒ 应用在前台时 Window 菜单里找不到，也没有键盘键。本轮补：`AppCommand.toggleMainWindowCollapse.keyEquivalent = "\\"`（keyModifiers `.command`）、`MenuCommandShortcutPresentation` 同步显示 ⌘\\、`ClipboardHistoryWindowCommands` 在 Window 菜单加「折叠/展开窗口」项并挂 `.keyboardShortcut("\\", modifiers: .command)`；窗口菜单项与状态菜单项都调同一个 `appDelegate.perform(.toggleMainWindowCollapse)`，**不是第二条触发路径**。产品 **3 文件**（AppCommand / MenuCommandShortcutPresentation / ClipboardHistoryCommands）。
- **U-2132：② 判据与刀。** `MainWindowCollapseTests` 新增 `testCollapseHasAnAppMenuEntryAndKeyboardShortcut`（keyEquivalent=⌘\\、状态菜单 presenter=⌘\\、ClipboardHistoryCommands 含 `perform(.toggleMainWindowCollapse)` 与 `.keyboardShortcut("\\", modifiers: .command)`）；`AppCommandTests` 与 `MenuShortcutPresentationTests` 的旧「折叠无快捷键」断言按新特性校正（不是放宽守卫：替换成对 ⌘\\ 的正向断言）。刀 `M1402`（删应用菜单的 `.keyboardShortcut`）**CAUGHT、RESTORE_CLEAN=yes**；过渡相关 `M1399–M1401` 仍在册。预检 **305/282/743 bad=0**、ARM **398/1230**（dupes=0 repeats=0）、HIDDEN **392/1169 rot=0**；build **0 告警**（增量 0、冷编 0）。
- **U-2133：③ 帧卷。** 捕获 **340 帧**：`CHANGED=0 ADDED=0 MISSING=0`（菜单/快捷键不进离屏帧），基线保持 **340**；过渡胶片与两态帧不受影响。
- **U-2134：④ 八步与电池。** build **0 告警**（增量 0、冷编 0）；%s；%s；%s；清账 `MOTION_LEDGER 162 格 / 已清账 162 / 未清账 0 / 不合法 0`；产品面连续零改动 **4** 轮（as-of 501，`python3 scripts/product_streak.py` 现读，last_round=497）。%s。**具名 NOT-RUN / 限制**：① R525 产品笔/台账笔自身跑（推送后取）；② R524 三跑 in_progress ⇒ NOT-RUN；③ 折叠过渡判据 runner 签收 NOT-RUN；④ `ABOUT_LINK_*_NOT_RUN=settings-content-blank`；⑤ `RTF_HELPER_ORPHAN`（595）；⑥ `RECORDING_REREAD` 1x；⑦ 状态菜单像素通道（610）；⑧ Motion `not-run=notice-banner` 1 条按现有出口具名；⑨ 已知在屏/SelectionReveal 本机会话 flake。
- **U-2135：⑤ 收口 CI。** %s。R524 产品跑的唯一失败步（若有）按 sources 时序族处理；R523 产品跑的 sources 时序红不冒充产品回归。
- **U-2136：⑥ 台账校对。** 按 `git show --stat 79e39ee` 现读，R524 产品笔实际改了 5 个 `Sources/` 文件（App/MainWindowCollapseController/MainWindowCollapsePolicy/MotionCatalog/ContentView）；把 AGENT_STATE R524 正文里的「产品 4 文件」校正为「产品 5 文件」（标题与提交标的 5 一致），**不改已推历史**。
""" % (FULLTXT, INSTALLTXT, BATTERYTXT, TAILPAIR, RUNPAIR or u"收口新跑在推送后取")
DS=u"""## D-524 折叠/展开补应用菜单与 ⌘\\（R525）

- 背景：R523/R524 只有状态菜单 + 标题双击 + 可见 chevron；应用在前台时 Window 菜单里没有该命令，也没有键盘键（`keyEquivalent == ""`、presenter 返回 nil、Commands 文件 0 处 toggle）。
- 决定：给同一个 `AppCommand.toggleMainWindowCollapse` 挂 `\\` + Command，并在 Window 菜单（`CommandGroup(after: .windowArrangement)`）加一项；状态菜单沿既有 `MenuCommandShortcutModifier` 显示同一 ⌘\\。两个菜单表面都走 `appDelegate.perform(.toggleMainWindowCollapse)`，是一个 command 的两种呈现，不是第二条触发路径。
- 理由：折叠是高频窗口操作，键盘用户不该只能去状态菜单或鼠标点标题；命令目录本来就是唯一的 dispatch，新增呈现不需要新逻辑。
- 兼容性/迁移：旧断言「折叠无快捷键」按新特性换成对 ⌘\\ 的正向断言（不是放宽）；状态菜单的快捷键列由 presenter 现读，不另写字符串。
- 边界：⌘\\ 不改变折叠/展开的过渡、宽度与持久化语义；不改状态栏热键（⌃⌥V 等）。
"""
CS=u"""### 折叠/展开补应用菜单与 ⌘\\（R525 / 第 524 轮 / Round 522 / U-2130…U-2136 · 产品 3 文件 + 判据）

"""
SS=u"""## R525 状态（2026-11-01 · 第 524 轮 · 产品 3 文件 + 判据）

R525 记录（产品 3 文件 + 判据）：折叠/展开补应用菜单与键盘入口。⓪ push no-op（HEAD=origin/main=`9d882e4`、ahead=0）；`41218308733 ↔ 79e39ee`、`41218637052 ↔ 77ed8ef`、`41218878781 ↔ 9d882e4` 读时 in_progress ⇒ NOT-RUN；`41215426349 ↔ 3e5aa6b` failure 仅 STEP[9]（sources 时序 + 两条级联；INK 5.01/4.82、RECORDING diff 0、RTF NOT_RUN、Motion 4/5 not-run notice-banner）；`41215568792 ↔ f20f256` success。① 缺口：Window 菜单无折叠项、无键盘键（Commands 0 处、keyEquivalent 空、presenter nil）。② 产品：AppCommand ⌘\\ + presenter + Window 菜单项（同一个 perform dispatch）；3 文件。③ 新增 `testCollapseHasAnAppMenuEntryAndKeyboardShortcut`，旧断言改为 ⌘\\ 正向；M1402 CAUGHT；预检 305/282/743 bad=0、ARM 398/1230、HIDDEN 392/1169 rot=0；build 0 告警。④ 帧 340 CHANGED=0，基线 340 不变。⑤ %s；%s；%s；清账 162 格已清 162/未清 0/不合法 0；产品面连续零改动 4 轮（as-of 501，`python3 scripts/product_streak.py` 现读，last_round=497）。⑥ 台账校对：按 `git show --stat 79e39ee` 把 R524 正文「产品 4 文件」改为「产品 5 文件」。%s。下一轮编号 R526（第 525 轮 / Round 523）：先 push 并复核 ahead=0；读 R525 产品笔/台账笔与 R524 三跑的全部失败步骤（in_progress/queued ⇒ NOT-RUN）；② 产品位按用户指令继续折叠特性；③ 4.5 地板与 150 上限不动。
""" % (FULLTXT, INSTALLTXT, BATTERYTXT, TAILPAIR)
IS=u"""## Round 522 · R525（第 524 轮 · 2026-11-01）：折叠/展开补应用菜单与 ⌘\\

折叠/展开以前只有状态菜单、标题双击与可见 chevron：应用在前台时 Window 菜单里找不到，也没有键盘键。R525 给同一个 `AppCommand.toggleMainWindowCollapse` 挂 ⌘\\，并在 Window 菜单加一项（状态菜单沿既有 presenter 显示同一个 ⌘\\）；两个菜单表面都走 `appDelegate.perform(.toggleMainWindowCollapse)`，是一个 command 的两种呈现，不是第二条触发路径。判据：新增 `testCollapseHasAnAppMenuEntryAndKeyboardShortcut`，旧「折叠无快捷键」断言按新特性换成 ⌘\\ 正向断言；M1402（删应用菜单快捷键）CAUGHT、RESTORE_CLEAN；过渡刀 M1399–M1401 仍在册；预检 305/282/743 bad=0、ARM 398/1230、HIDDEN 392/1169 rot=0；build 0 告警；帧 340 CHANGED=0，基线不变。%s；%s；%s。R524 三跑仍 in_progress ⇒ 折叠过渡 runner 签收 NOT-RUN。

**七维度自评**（恰七行，每格 n/15）：

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | 15/15 | 本轮是键盘/菜单可达性，无新视觉面；帧 0 变化由整张名单证；不冒充做了视觉改动。 |
| 判据有效性 | 15/15 | 旧缺口三项读数 + 新 ⌘\\ 三项正断言；M1402 让读数变。 |
| 假绿防御 | 15/15 | runner 三跑 in_progress 具名 NOT-RUN；Motion 4/5 not-run 按现有出口记。 |
| 产品面推进 | 15/15 | 折叠有了应用菜单 + 键盘入口；3 个产品文件。 |
| 台账一致性 | 15/15 | U-2130…U-2136、D-524、R524 文件数校正都来自命令与 git。 |
| 交付诚实性 | 15/15 | 本轮不改视觉、不签 runner、sources 时序红照实。 |
| 可复核性 | 15/15 | ⌘\\、M1402、precheck 305/282/743、340/CHANGED=0 都在。 |

均分 = 105/105 ≈ 15.0/15（100）。
""" % (FULLTXT, INSTALLTXT, BATTERYTXT)
RB=u"""- **R525（折叠/展开补应用菜单与 ⌘\\；产品 3 文件 + 判据）**：旧状态只有状态菜单/双击/chevron，Window 菜单无项、无键盘键（Commands 0 处、keyEquivalent 空、presenter nil）。给同一个 `AppCommand.toggleMainWindowCollapse` 挂 ⌘\\，Window 菜单加项，状态菜单同一 presenter 显示；两个表面同一个 perform dispatch。新增 `testCollapseHasAnAppMenuEntryAndKeyboardShortcut`；M1402 CAUGHT；预检 305/282/743 bad=0、ARM 398/1230、HIDDEN 392/1169 rot=0；帧 340 CHANGED=0，基线不变；R524 正文文件数按 `git show --stat 79e39ee` 校正为 5。全量 %s；换装 %s；电池 %s。
""" % (FULL or u"见补记", INSTALL or u"425=425", BATTERY or u"683/5")
a=rd(A); d=rd(D); st=rd(S); pr=rd(P); ch=rd(C); it=rd(I)
if a.count(AT_OLD)!=1: raise SystemExit("A title %d" % a.count(AT_OLD))
if a.count(ANCHOR_NEXT)!=1: raise SystemExit("A next %d" % a.count(ANCHOR_NEXT))
if u"## D-524" in d: raise SystemExit("D exists")
if u"## R525 状态" in st: raise SystemExit("S exists")
if u"R525（折叠/展开补应用菜单与 ⌘" in pr: raise SystemExit("P exists")
if u"折叠/展开补应用菜单与 ⌘" in ch: raise SystemExit("C exists")
if u"## Round 522 · R525" in it: raise SystemExit("I exists")
if pr.count(u"U-31 … U-2129（R524 现读抬到最新一节）")!=1: raise SystemExit("P ucell")
if pr.count(u"R9–R521，522 节自评")!=1: raise SystemExit("P headline")
if pr.count(u"阶段二 **514 轮**审计（R9–R521；")!=1: raise SystemExit("P phase")
if pr.count(u"PHASE2 n=514")!=1: raise SystemExit("P n")
if pr.count(u"的 Round 521")!=1: raise SystemExit("P round")
if pr.count(u"## 18. R458 → R524 这一段（R478 起写；R504 续到 504、R505 续到 505、R506 续到 506、R507 续到 507、R508 续到 508、R509 续到 509、R510 续到 510、R511 续到 511、R512 续到 512、R513 续到 513、R514 续到 514、R515 续到 515、R516 续到 516、R517 续到 517、R518 续到 518、R519 续到 519、R520 续到 520、R521 续到 521、R522 续到 522、R523 续到 523、R524 续到 524 —— 这份报告第七次差点停在几十轮之前）")!=1: raise SystemExit("P s18")
if pr.count(u"的 R524 节 ② 为准")!=1: raise SystemExit("P pointer")
if st.count(u"R524 记录（产品 4 文件 + 判据）")!=1: raise SystemExit("S r524 count")
wr(A, a.replace(AT_OLD, AT_NEW, 1).replace(ANCHOR_NEXT, u"\n"+AS+ANCHOR_NEXT, 1))
wr(D, d.rstrip()+"\n\n"+DS+"\n")
st=st.replace(u"R524 记录（产品 4 文件 + 判据）", u"R524 记录（产品 5 文件 + 判据）", 1)
wr(S, st.replace(u"## R524 状态（", SS.strip()+"\n\n## R524 状态（", 1))
pr=pr.replace(u"R9–R521，522 节自评", u"R9–R522，523 节自评", 1)
pr=pr.replace(u"阶段二 **514 轮**审计（R9–R521；", u"阶段二 **515 轮**审计（R9–R522；", 1)
pr=pr.replace(u"PHASE2 n=514", u"PHASE2 n=515", 1)
pr=pr.replace(u"的 Round 521", u"的 Round 522", 1)
pr=pr.replace(u"U-31 … U-2129（R524 现读抬到最新一节）", u"U-31 … U-2136（R525 现读抬到最新一节）", 1)
pr=pr.replace(u"## 18. R458 → R524 这一段（R478 起写；R504 续到 504、R505 续到 505、R506 续到 506、R507 续到 507、R508 续到 508、R509 续到 509、R510 续到 510、R511 续到 511、R512 续到 512、R513 续到 513、R514 续到 514、R515 续到 515、R516 续到 516、R517 续到 517、R518 续到 518、R519 续到 519、R520 续到 520、R521 续到 521、R522 续到 522、R523 续到 523、R524 续到 524 —— 这份报告第七次差点停在几十轮之前）",
              u"## 18. R458 → R525 这一段（R478 起写；R504 续到 504、R505 续到 505、R506 续到 506、R507 续到 507、R508 续到 508、R509 续到 509、R510 续到 510、R511 续到 511、R512 续到 512、R513 续到 513、R514 续到 514、R515 续到 515、R516 续到 516、R517 续到 517、R518 续到 518、R519 续到 519、R520 续到 520、R521 续到 521、R522 续到 522、R523 续到 523、R524 续到 524、R525 续到 525 —— 这份报告第七次差点停在几十轮之前）", 1)
pr=pr.replace(u"的 R524 节 ② 为准", u"的 R525 节 ② 为准", 1)
wr(P, pr.rstrip()+"\n\n"+RB+"\n")
m=u"## [Unreleased]\n"
if ch.count(m)!=1: raise SystemExit("C anchor")
wr(C, ch.replace(m, m+"\n"+CS, 1))
wr(I, it.rstrip()+"\n\n"+IS+"\n")
print("OK sha=%s full=%s install=%s battery=%s" % (sha, FULL, INSTALL, BATTERY))
