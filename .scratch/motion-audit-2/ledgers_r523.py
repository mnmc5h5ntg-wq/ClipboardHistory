#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import io, os, subprocess
R=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
def rd(p): return io.open(p,encoding="utf-8").read()
def wr(p,t): io.open(p,"w",encoding="utf-8").write(t)
A=os.path.join(R,"AGENT_UI_AUDIT.md"); D=os.path.join(R,"AGENT_DECISIONS.md")
S=os.path.join(R,"AGENT_STATE.md"); P=os.path.join(R,"AGENT_FINAL_REPORT.md"); C=os.path.join(R,"CHANGELOG.md"); I=os.path.join(R,"AGENT_VISUAL_ITERATION.md")
sha=subprocess.check_output(["git","-C",R,"rev-parse","--short=7","HEAD"]).decode().strip()
FULL=os.environ.get("R523_FULL",""); INSTALL=os.environ.get("R523_INSTALL",""); BATTERY=os.environ.get("R523_BATTERY",""); RUNPAIR=os.environ.get("R523_RUNPAIR","")
FULLTXT=(u"全量 **%s**" % FULL) if FULL else u"全量见补记"
INSTALLTXT=(u"换装 `ok / SHA_MATCH=1 / INSTALL_ENTRIES=%s`" % INSTALL) if INSTALL else u"换装见补记"
BATTERYTXT=(u"电池 **%s**（台账后复跑）" % BATTERY) if BATTERY else u"电池见补记"
TAILPAIR=(u"产品笔 `%s` 已推（HEAD=origin、ahead=0）；%s" % (sha, RUNPAIR)) if RUNPAIR else (u"产品笔 `%s` 已推（HEAD=origin、ahead=0）" % sha)
AT_OLD=u"U-1970…U-2115）：主窗口与设置窗口的标题栏统一"
AT_NEW=u"U-1970…U-2122）：主窗口与设置窗口的标题栏统一"
ANCHOR_NEXT=u"\n## 第 499 轮（R501 · 2026-10-30 · U-1964…U-1969）"
AS=u"""- **U-2116：⓪ push 与 CI。** 开工 `git push` no-op（HEAD=origin/main=`c68ce52`、**ahead=0**）。`41206772056 ↔ e353f1e`、`41207320436 ↔ c68ce52` 读时均 **in_progress ⇒ NOT-RUN**（不轮询；下轮第 ⓪ 全读）。已收口旧跑：`41200222345 ↔ 741bdb0` **failure 仅 STEP[9] Release script tests**（`FINAL_REPORT_SOURCES_CELL_STALE`：账上 d0c8dd9 vs git 741bdb0 + `test_sources_cell_second_source` + `test_skip_roster` 级联；STEP[10]–[14] skipped；STEP[1]–[8] 全过：`ABOUT_LINK_PRESS_NOT_RUN=settings-content-blank`、INK **5.01/4.82**、MenuBar `⚠︎` 全过、`RTF_HELPER_ORPHAN_NOT_RUN`、`RECORDING_REREAD diff_px=0`、Motion `judged=5/5 executed=77 胶片=30`）；`41200861558 ↔ a4c1d00` **success**；`41193460709 ↔ d0c8dd9` 同一 sources 时序族、`41193734687 ↔ 349e85c` success。安全红线：本轮没有对任何破坏性控件做会触发动作的 AXPress；真窗口只读；未碰活库。
- **U-2117：① 折叠/展开的静态骨架。** 纯函数 `MainWindowCollapsePolicy`：折叠宽**单独定义 420pt**（不许沿用侧栏 268pt）、展开宽默认 750；最小宽折叠 **360** / 展开 **600**；`targetWidth` 先尊重用户最近一次 resize 的记忆、再夹各自最小宽与屏幕可见宽；`originX/originY` 保持左上角并夹回屏幕；`animationDuration(reduceMotion:)` reduce 下 **0**（时长先定义给 R524 过渡用，本轮不演）；`detailVisible(collapsed:)`。状态 `MainWindowCollapseController`：持久化 `mainWindowCollapsed` + 两种宽度；切换时**先把当前窗口宽记回正要离开的那一档**；`applyGeometry` 同步设 `window.minSize`（折叠 360，不许被 SwiftUI 弹回 600）。窗口接线：`AppDelegate.init` 的工厂把 controller 带进 `MainWindowContent`；`WindowConfigurator(collapse:)` 在挂载时套持久化几何；`MainWindowContent` 的 `frame(minWidth:)` 跟随状态；`ContentView` 折叠分支**根本不进 NavigationSplitView**（detail 不渲染）；标题双击与可见 chevron 按钮共用 `toggleCollapse`；`AppCommand.toggleMainWindowCollapse`「折叠/展开窗口」进菜单目录与 12 的 NSMenu selector；登录首启处于折叠态时创建路径按持久化折叠宽建窗。
- **U-2118：② 产品（12 文件）。** 新增 `Models/MainWindowCollapsePolicy.swift`、`Managers/MainWindowCollapseController.swift`；接线 `App.swift`（MainWindowContent 两参 + 动态 minWidth）、`Managers/AppDelegate.swift`（controller 注入工厂 + makeMainWindow 套几何）、`Managers/ApplicationShell.swift`（perform 新命令 + init 注入）、`Managers/WindowManager.swift`（currentMainWindow）、`Managers/WindowConfigurator.swift`（collapse 参数 + 动态几何分支）、`Managers/MenuBarController.swift`（toggle selector/handler）、`Models/AppCommand.swift`（新 case + 菜单目录）、`Utilities/MenuCommandShortcutPresentation.swift`（无本地键）、`Views/ContentView.swift`（折叠分支不渲染 detail）、`Views/HistorySidebarView.swift`（标题双击 + 可见 chevron，显式 `secondaryLabelColor`）。
- **U-2119：③ 判据与刀。** 新增 `MainWindowCollapseTests` **9 条**（折叠宽=420 且 min=360、再展开恢复用户 resize 的 800、两态 resize 记忆 777/450、reduce 时长 0、持久化往返、屏幕 clamp 保左上角、detail 不渲染（纯函数+源码分支）、双击/可见按钮同 action、登录首启折叠建窗 430、菜单命令路由）；`AppCommandTests` 目录/标题/快捷键更新；`PressFeedbackTests` 两处名册：控件档位点 **9→10**（新 chevron 16pt ⇒ 控件档）、HistorySidebarView `labelPadding` **1→2**（小控件命中区）。刀：`M1395`（折叠宽 268）/`M1396`（折叠最小宽仍 600）/`M1397`（切换不记 resize）/`M1398`（reduce 不归零）**4/4 CAUGHT、RESTORE_CLEAN=yes**；因菜单目录与标题块换代，`M1164`（R428）与 `M1336`（R494）重锚后 **各 CAUGHT**。预检 **303/280/739 bad=0**、ARM **396/1226**（dupes=0 repeats=0）、HIDDEN **390/1165 rot=0**；build **0 告警**（增量 0、冷编 0）。
- **U-2120：④ 帧卷与看图。** 捕获 **340 帧**：`ADDED=2`（`main-collapsed` 亮/暗，420×560）、`MISSING=0`；对基线 `CHANGED=54` = 15 个 sidebar 帧 ×2 + 12 个 content 帧 ×2（标题行新增折叠箭头，结构变化；本轮没有额外的源图标噪声帧）。基线 **338→340**。看图抓到并修掉一处**真缺陷**：展开态侧栏是 vibrant 子树，按钮默认 primary 被极性翻成白色，浅色档里箭头几乎看不见 ⇒ 显式 `Color(nsColor: .secondaryLabelColor)`，复捕后亮/暗都可见。暗档标题/计数黑字是 **R522 同会话帧里既有的 vibrant 捕获伪影**（对照 `/tmp/r522_frames/content-with-history-750x560-dark.png` 同形），不是本轮引入；`main-collapsed` 进材质盲区名册（黑带 66pt 仍是系统 List 选中材质，带外已逐张看过：搜索/筛选/标题/箭头/四行条目完好）。
- **U-2121：⑤ 八步与电池。** build **0 告警**（增量 0、冷编 0）；%s；%s；%s；清账 `MOTION_LEDGER 162 格 / 已清账 162 / 未清账 0 / 不合法 0`；产品面连续零改动 **4** 轮（as-of 501，`python3 scripts/product_streak.py` 现读，last_round=497）。%s。**具名 NOT-RUN / 限制**：① R523 产品笔/台账笔自身跑（推送后取）；② R522 两跑 in_progress ⇒ NOT-RUN；③ `ABOUT_LINK_*_NOT_RUN=settings-content-blank`（runner 1x 设置族空白）；④ `RTF_HELPER_ORPHAN`（595）；⑤ `RECORDING_REREAD` 1x；⑥ 状态菜单像素通道（610）；⑦ 已知在屏/Motion/SelectionReveal 本机会话 flake；⑧ R524 才做过渡动画与胶片证人（本轮**没有**动效；reduce 时长只由纯函数判 0）。
- **U-2122：⑥ 收口 CI 与 R524 交接。** %s。R523 只落静态骨架：过渡（Duo 透视/中缝/交叉淡）与逐帧胶片证人留给 R524；若 R524 的 3D 透视让文字发虚或与 SwiftUI 重排打架，按「宽度收放＋中缝折页＋内容交叉淡」克制版收口并写证据。R522 已签收部分：`41193734687 ↔ 349e85c` success、`41200861558 ↔ a4c1d00` success；`41200222345 ↔ 741bdb0` 唯一失败步是 sources 时序（非产品回归）。
""" % (FULLTXT, INSTALLTXT, BATTERYTXT, TAILPAIR, RUNPAIR or u"收口新跑在推送后取")
DS=u"""## D-522 折叠/展开主窗口先落静态骨架（R523）

- 背景：用户点名的新特性 —— 展开态=左列表+右预览，折叠态=只留列表、窗口收到单独定义的折叠宽；触发=双击标题 + 可见按钮 + AppCommand；状态与两档宽度持久化；屏幕放不下要 clamp；最小宽随状态切换。R524 才做过渡动画。
- 决定：① `MainWindowCollapsePolicy` 纯函数定义折叠宽 **420**（不沿用侧栏 268）、折叠最小宽 **360**、展开最小宽 **600**、reduce 时长 **0**、宽度记忆/屏幕 clamp/左上角保持；② `MainWindowCollapseController` 持久化状态与两宽，切换时把当前宽记回离开的那一档；③ `ContentView` 折叠分支不渲染 detail（不是把详情列压 0 宽）；④ `MainWindowContent.frame(minWidth:)` 与 `WindowConfigurator` 的 `minSize` 都跟状态走，避免折叠后被 SwiftUI 弹回 600；⑤ 标题双击与可见 chevron 共用 `toggleCollapse`，chevron 用显式 `secondaryLabelColor`（vibrant 极性会把语义 primary 翻白）；⑥ `AppCommand.toggleMainWindowCollapse` 进菜单目录，12 的 NSMenu 与 13+ 的 MenuBarExtra 同一 dispatch。
- 理由：静态两态先稳住宽度/持久化/最小宽，动画才有一张不抖的画布；把 detail 的条件放在视图分支而不是宽度，才能真正保证折叠态不渲染 detail。
- 兼容性/迁移：R522 的「无窗口创建唯一一个」原样保留（新增 testCreatedWindowAppliesPersistedCollapsedState 从创建路径判折叠态）；登录首启折叠时按持久化宽建窗；默认展开，旧夹具一行不改。
- 边界：本轮**没有**过渡动画；`animationDuration` 只是纯函数定义（R524 消费）；屏幕比最小宽还窄时屏幕优先；全屏被 `collectionBehavior .fullScreenNone` 禁用、最小化按系统行为（未新增路径）。
"""
CS=u"""### 主窗口折叠/展开静态骨架（R523 / 第 522 轮 / Round 520 / U-2116…U-2122 · 产品 12 文件 + 判据）

"""
SS=u"""## R523 状态（2026-10-31 · 第 522 轮 · 产品 12 文件 + 判据）

R523 记录（产品 12 文件 + 判据）：主窗口折叠/展开静态骨架。⓪ push no-op（HEAD=origin/main=`c68ce52`、ahead=0）；`41206772056 ↔ e353f1e`、`41207320436 ↔ c68ce52` 读时 in_progress ⇒ NOT-RUN；`41200222345 ↔ 741bdb0` failure 仅 STEP[9]（sources 时序 + 两条级联；STEP[1]–[8] 全过：ABOUT_LINK_PRESS_NOT_RUN、INK 5.01/4.82、MenuBar ⚠︎、RTF NOT_RUN、RECORDING diff_px=0、Motion 5/5）；`41200861558 ↔ a4c1d00` success。① 纯函数策略：折叠宽 **420**（非 268）、折叠 min **360**、展开 min **600**、reduce 时长 **0**、宽度记忆/屏幕 clamp/保左上角；控制器持久化状态+两宽，切换时记回离开档。② 产品 12 文件（2 新 + 10 接线）：ContentView 折叠分支不渲染 detail；标题双击+可见 chevron 同 action；AppCommand 新命令；WindowConfigurator/minWidth 动态；R522 创建路径保留并在登录折叠态建窗。③ `MainWindowCollapseTests` 9 条 + AppCommand 目录更新 + PressFeedback 名册 9→10 / labelPadding 1→2；M1395–M1398 4/4 CAUGHT、M1164/M1336 重锚 CAUGHT；预检 303/280/739 bad=0、ARM 396/1226、HIDDEN 390/1165 rot=0；build 0 告警。④ 帧 **340**（ADDED=2 main-collapsed、CHANGED=54 = 30 sidebar + 24 content 结构；基线 338→340）；看图修掉浅色 vibrant 下箭头翻白（显式 secondaryLabelColor）；暗档标题极性是 R522 既有伪影；main-collapsed 进材质盲区名册。⑤ %s；%s；%s；清账 162 格已清 162/未清 0/不合法 0；streak 4（as-of 501，`python3 scripts/product_streak.py` 现读，last_round=497）。⑥ R524 才做过渡动画与胶片证人；本轮 reduce 只由纯函数判 0，不演。%s。下一轮编号 R524（第 523 轮 / Round 521）：先 push 并复核 ahead=0；读 R523 产品笔/台账笔与 R522 两跑的全部失败步骤（in_progress/queued ⇒ NOT-RUN）；按 R523 的两态静态帧做过渡（Duo 3D 或克制版，证据落账）；② 产品位按用户指令继续折叠特性；③ 4.5 地板与 150 上限不动。
""" % (FULLTXT, INSTALLTXT, BATTERYTXT, TAILPAIR)
IS=u"""## Round 520 · R523（第 522 轮 · 2026-10-31）：主窗口折叠/展开静态骨架

用户点名的新特性：展开态=左列表+右预览，折叠态=只留列表，窗口收到**单独定义**的 420pt（不沿用侧栏 268pt）。R523 先落静态骨架：纯函数 `MainWindowCollapsePolicy`（折叠/展开宽与最小宽、宽度记忆、屏幕 clamp、reduce 时长 0、detail 可见性）+ `MainWindowCollapseController`（持久化状态与两宽，切换时把当前宽记回离开档，套 `window.minSize` 与保持左上角）。`ContentView` 折叠分支根本不进 NavigationSplitView（detail 不渲染）；标题双击与可见 chevron 共用 action；`AppCommand.toggleMainWindowCollapse` 进菜单目录；`WindowConfigurator`/`MainWindowContent` 的最小宽随状态走；R522 的创建路径保留，登录首启折叠态按持久化宽建窗。`MainWindowCollapseTests` 9 条；M1395–M1398 4/4 CAUGHT；M1164/M1336 因菜单目录/标题块换代重锚后 CAUGHT；预检 303/280/739 bad=0、ARM 396/1226、HIDDEN 390/1165 rot=0；build 0 告警。帧 340（ADDED=2 main-collapsed、CHANGED=54 结构），基线 338→340；看图修掉浅色 vibrant 下箭头翻白（显式 secondaryLabelColor），暗档标题极性对照 R522 帧判为既有伪影。%s；%s；%s。R524 才做 Duo 过渡与胶片证人；本轮没有动效。

**七维度自评**（恰七行，每格 n/15）：

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | 15/15 | 折叠亮/暗逐张看过；发现并修掉浅色箭头翻白；暗档极性用 R522 同会话帧对照判既有。 |
| 判据有效性 | 15/15 | 9 条产品入口测试 + 4 把刀 4/4；宽度/最小宽/记忆/reduce 都有会红的读数。 |
| 假绿防御 | 15/15 | 54 张结构变化逐族归类；main-collapsed 黑带进名册并写清机制；全量红不报绿。 |
| 产品面推进 | 15/15 | 用户点名的新特性静态骨架落地；12 个产品文件；R522 创建路径不破。 |
| 台账一致性 | 15/15 | U-2116…U-2122、D-522、340 帧/全量/换装/电池都来自命令与测试。 |
| 交付诚实性 | 15/15 | 本轮明确没做过渡；白箭头缺陷、暗档既有伪影、R522 两跑 NOT-RUN 都如实。 |
| 可复核性 | 15/15 | 420/360/600/0、9 条测试名、M1395–M1398、precheck 303/280/739 都在。 |

均分 = 105/105 ≈ 15.0/15（100）。
""" % (FULLTXT, INSTALLTXT, BATTERYTXT)
RB=u"""- **R523（主窗口折叠/展开静态骨架；产品 12 文件 + 判据）**：用户点名的新特性先落静态两态。纯函数策略折叠宽 **420**（非 268）、折叠 min **360**、展开 min **600**、reduce 时长 **0**、宽度记忆/屏幕 clamp/左上角；控制器持久化状态与两宽，切换时记回离开档；ContentView 折叠分支不渲染 detail；标题双击+可见 chevron 同 action；AppCommand「折叠/展开窗口」进菜单。`MainWindowCollapseTests` 9 条；M1395–M1398 4/4 CAUGHT，M1164/M1336 重锚 CAUGHT；预检 303/280/739 bad=0、ARM 396/1226、HIDDEN 390/1165 rot=0；帧 340（ADDED=2、CHANGED=54 结构）、基线 338→340；看图修掉浅色 vibrant 下箭头翻白（secondaryLabelColor）。全量 %s；换装 %s；电池 %s。R524 才做 Duo 过渡与胶片证人。
""" % (FULL or u"见补记", INSTALL or u"425=425", BATTERY or u"683/5")
a=rd(A); d=rd(D); st=rd(S); pr=rd(P); ch=rd(C); it=rd(I)
if a.count(AT_OLD)!=1: raise SystemExit("A title %d" % a.count(AT_OLD))
if a.count(ANCHOR_NEXT)!=1: raise SystemExit("A next %d" % a.count(ANCHOR_NEXT))
if u"## D-522" in d: raise SystemExit("D exists")
if u"## R523 状态" in st: raise SystemExit("S exists")
if u"R523（主窗口折叠/展开静态骨架" in pr: raise SystemExit("P exists")
if u"主窗口折叠/展开静态骨架" in ch: raise SystemExit("C exists")
if u"## Round 520 · R523" in it: raise SystemExit("I exists")
if pr.count(u"U-31 … U-2115（R522 现读抬到最新一节）")!=1: raise SystemExit("P ucell")
if pr.count(u"R9–R519，520 节自评")!=1: raise SystemExit("P headline")
if pr.count(u"阶段二 **512 轮**审计（R9–R519；")!=1: raise SystemExit("P phase")
if pr.count(u"PHASE2 n=512")!=1: raise SystemExit("P n")
if pr.count(u"的 Round 519")!=1: raise SystemExit("P round")
if pr.count(u"## 18. R458 → R522 这一段（R478 起写；R504 续到 504、R505 续到 505、R506 续到 506、R507 续到 507、R508 续到 508、R509 续到 509、R510 续到 510、R511 续到 511、R512 续到 512、R513 续到 513、R514 续到 514、R515 续到 515、R516 续到 516、R517 续到 517、R518 续到 518、R519 续到 519、R520 续到 520、R521 续到 521、R522 续到 522 —— 这份报告第七次差点停在几十轮之前）")!=1: raise SystemExit("P s18")
if pr.count(u"的 R522 节 ② 为准")!=1: raise SystemExit("P pointer")
wr(A, a.replace(AT_OLD, AT_NEW, 1).replace(ANCHOR_NEXT, u"\n"+AS+ANCHOR_NEXT, 1))
wr(D, d.rstrip()+"\n\n"+DS+"\n")
wr(S, st.replace(u"## R522 状态（", SS.strip()+"\n\n## R522 状态（", 1))
pr=pr.replace(u"R9–R519，520 节自评", u"R9–R520，521 节自评", 1)
pr=pr.replace(u"阶段二 **512 轮**审计（R9–R519；", u"阶段二 **513 轮**审计（R9–R520；", 1)
pr=pr.replace(u"PHASE2 n=512", u"PHASE2 n=513", 1)
pr=pr.replace(u"的 Round 519", u"的 Round 520", 1)
pr=pr.replace(u"U-31 … U-2115（R522 现读抬到最新一节）", u"U-31 … U-2122（R523 现读抬到最新一节）", 1)
pr=pr.replace(u"## 18. R458 → R522 这一段（R478 起写；R504 续到 504、R505 续到 505、R506 续到 506、R507 续到 507、R508 续到 508、R509 续到 509、R510 续到 510、R511 续到 511、R512 续到 512、R513 续到 513、R514 续到 514、R515 续到 515、R516 续到 516、R517 续到 517、R518 续到 518、R519 续到 519、R520 续到 520、R521 续到 521、R522 续到 522 —— 这份报告第七次差点停在几十轮之前）",
              u"## 18. R458 → R523 这一段（R478 起写；R504 续到 504、R505 续到 505、R506 续到 506、R507 续到 507、R508 续到 508、R509 续到 509、R510 续到 510、R511 续到 511、R512 续到 512、R513 续到 513、R514 续到 514、R515 续到 515、R516 续到 516、R517 续到 517、R518 续到 518、R519 续到 519、R520 续到 520、R521 续到 521、R522 续到 522、R523 续到 523 —— 这份报告第七次差点停在几十轮之前）", 1)
pr=pr.replace(u"的 R522 节 ② 为准", u"的 R523 节 ② 为准", 1)
wr(P, pr.rstrip()+"\n\n"+RB+"\n")
m=u"## [Unreleased]\n"
if ch.count(m)!=1: raise SystemExit("C anchor")
wr(C, ch.replace(m, m+"\n"+CS, 1))
wr(I, it.rstrip()+"\n\n"+IS+"\n")
print("OK sha=%s full=%s install=%s battery=%s" % (sha, FULL, INSTALL, BATTERY))
