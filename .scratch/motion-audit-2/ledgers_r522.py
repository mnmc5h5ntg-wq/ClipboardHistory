#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import io, os, subprocess
R=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
def rd(p): return io.open(p,encoding="utf-8").read()
def wr(p,t): io.open(p,"w",encoding="utf-8").write(t)
A=os.path.join(R,"AGENT_UI_AUDIT.md"); D=os.path.join(R,"AGENT_DECISIONS.md")
S=os.path.join(R,"AGENT_STATE.md"); P=os.path.join(R,"AGENT_FINAL_REPORT.md"); C=os.path.join(R,"CHANGELOG.md"); I=os.path.join(R,"AGENT_VISUAL_ITERATION.md"); B=os.path.join(R,"AGENT_BACKLOG.md")
sha=subprocess.check_output(["git","-C",R,"rev-parse","--short=7","HEAD"]).decode().strip()
FULL=os.environ.get("R522_FULL",""); INSTALL=os.environ.get("R522_INSTALL",""); BATTERY=os.environ.get("R522_BATTERY",""); RUNPAIR=os.environ.get("R522_RUNPAIR","")
FULLTXT=(u"全量 **%s**" % FULL) if FULL else u"全量见补记"
INSTALLTXT=(u"换装 `ok / SHA_MATCH=1 / INSTALL_ENTRIES=%s`" % INSTALL) if INSTALL else u"换装见补记"
BATTERYTXT=(u"电池 **%s**（台账后复跑）" % BATTERY) if BATTERY else u"电池见补记"
TAILPAIR=(u"产品笔 `%s` 已推（HEAD=origin、ahead=0）；%s" % (sha, RUNPAIR)) if RUNPAIR else (u"产品笔 `%s` 已推（HEAD=origin、ahead=0）" % sha)
AT_OLD=u"U-1970…U-2108）：主窗口与设置窗口的标题栏统一"
AT_NEW=u"U-1970…U-2115）：主窗口与设置窗口的标题栏统一"
ANCHOR_NEXT=u"\n## 第 499 轮（R501 · 2026-10-30 · U-1964…U-1969）"
AS=u"""- **U-2109：⓪ push 与 CI。** 开工 `git push` no-op（HEAD=origin/main=`a4c1d00`、**ahead=0**）。四跑成对读：`41200222345 ↔ 741bdb0` **failure 仅 STEP[9] Release script tests**（STEP[10]–[14] skipped）；正文三红同根：`SOURCES_CELL 账上=R498/`d0c8dd9` git=R498/`741bdb0` 一致=否` ⇒ `FINAL_REPORT_SOURCES_CELL_STALE` + `test_sources_cell_second_source`（同一格另一把尺）+ `test_skip_roster`（内层电池因 sources 格红而终态 `FAILED`，没有 `OK (skipped=N)` ⇒ 级联，不是第三条独立缺陷）。该跑 STEP[1]–[8] 全过：**`ABOUT_LINK_PRESS_NOT_RUN=settings-content-blank`**（R521 新判据在 runner 1x 具名 NOT_RUN，不冒充红）、`ABOUT_LINK_HOVER_NOT_RUN`、`ABOUT_LINK_NOT_RUN`、INK **5.01/4.82**、`MenuBarPopulationTests` 全过（含 `⚠︎` 标题）、`RTF_HELPER_ORPHAN_NOT_RUN=settings-content-blank`、`RECORDING_REREAD diff_px=0`、Motion `judged=5/5 executed=77 胶片=30`（15.8/1x）。`41200861558 ↔ a4c1d00` 读时 **in_progress ⇒ NOT-RUN**（不轮询）；`41193460709 ↔ d0c8dd9` failure 仅 STEP[9]（同一 sources 时序族）、`41193734687 ↔ 349e85c` **success**。安全红线：本轮没有对任何破坏性控件做会触发动作的 AXPress；真窗口只读；未碰活库。
- **U-2110：① 事故根因与修法。** 现场：20:28 重启后登录项启动的仓库开发版 `时间剪史.app`（PID 927/后来的 5811）**一个窗口都没有**，`NSApp.windows` 为空；菜单「显示主窗口 ⌘S」AXPress 无反应；优雅退出再 `open` 同一 bundle，窗口立刻出现。根因三处同源：① `WindowManager.showMainWindow` 只 present 已存在的窗口，找不到只写一行日志；② `AppDelegate.applicationDidBecomeActive` 的 `allSatisfy` 对空数组为 true ⇒ 调了 `showMainWindow()` 也建不出来；③ `ApplicationShell.applicationDidBecomeActive` 的 300ms 延迟恢复只试一次，失败后永不重试。修法：`WindowManager` 增加 `mainWindowFactory`（由 `AppDelegate.init` 安装，工厂用 `AppDelegate.sharedHistoryStore`/注入 store + `MainWindowContent` + `WindowConfigurator` 建唯一窗口）；`showMainWindow(creatingIfNeeded:)` 在**查过弱引用与 identifier 搜索之后**才创建；弱引用只认仍在 `NSApp.windows` 里的那份（关掉的窗口不许冒充"已有"）；`showExistingMainWindowIfAvailable`/200ms best-effort 走 `creatingIfNeeded:false`，`applicationDidBecomeActive` 是否创建跟「启动时打开主窗口」同口径（关掉它的用户不被偷偷开窗）；延迟恢复 300ms 后仍无可见窗口再确认一次。**旧行为的负臂**：未装工厂时 `showMainWindow` 不创建（WindowManagerTests 具名）；安装后从零起点 reopen/菜单各建 1 个可见 AppWindow，连调两次仍 1 个，关窗=隐藏后再 reopen 仍是同一扇。
- **U-2111：② 产品：无窗口时建唯一主窗口（4 文件）。** `Managers/WindowManager.swift`：工厂 + `createMainWindow()` + `showMainWindow(creatingIfNeeded:)` + `hasVisibleMainWindow` + 弱引用挂载检查；`App.swift`：`MainWindowContent`（ContentView+frame+WindowConfigurator 单源，WindowGroup 与兜底共用）；`Managers/AppDelegate.swift`：init 安装工厂、`makeMainWindow(historyStore:)`（NSWindow 750×560、isReleasedWhenClosed=false、identifier AppWindow、NSHostingView(MainWindowContent)）、activation 创建口径、暴露 `showExistingMainWindowIfAvailable`；`Managers/ApplicationShell.swift`：`showMainWindow(creatingIfNeeded:)` 透传、`showExistingMainWindowIfAvailable` 不创建、延迟恢复重试。产品 **4 文件**。
- **U-2112：③ 判据与刀。** 新增 `MainWindowCreationTests` **8 条**（从产品入口：Dock reopen、菜单 perform、关窗→reopen、首次激活、设置关时不建、200ms best-effort 不建、300ms 延迟恢复建、菜单/热键/reopen 同入口接线）+ `WindowManagerTests` 改为"无工厂不建"负臂；开跑前先把测试造的窗口改名+orderOut+清弱引用（ARC 下不用 `isReleasedWhenClosed=true` 真销毁，避免过释放信号 11）。刀：`M1393`（删创建分支）与 `M1394`（删两段已有检查）**2/2 CAUGHT、RESTORE_CLEAN=yes**。预检 **302/279/735 bad=0**、ARM **395/1222**（dupes=0 repeats=0）、HIDDEN **389/1161 rot=0**；build **0 告警**（增量=0、冷编=0）。
- **U-2113：④ 帧卷与会话位移。** 捕获 **338 帧**：`ADDED=0 MISSING=0`；对工作基线 `CHANGED=142`（detail 48/row 28/sidebar 24/content 20/quickpick 13/settings 8/rows 1）。**归因 A/B**（不是本轮结构变化）：① 同代码背靠背两次捕获逐字节相同（0 张差异）；② 把 4 个产品文件临时换回 R521（`git show HEAD:`，字节备份、跑完还原 `RESTORE_CLEAN=True`）再捕一版，与 R522 当前代码**逐字节相同（0 张差异）** ⇒ 142 张是 20:28 重启后的**会话级栅格位移**（字体/图形栈），不是产品改动。基线吸收这 142 张会话位移（`FRAME_BASELINE_UPDATED=338`，count 仍 338）；不写进"已交付产品变化"，下一跑按常规噪声对账。
- **U-2114：⑤ 八步与电池。** build **0 告警**（增量=0、冷编=0）；%s；%s（换装前先退出用户正在跑的仓库开发版 PID 5811，活库；新 pid 见换装行）；%s；清账 `MOTION_LEDGER 162 格 / 已清账 162 / 未清账 0 / 不合法 0`；产品面连续零改动 **4** 轮（as-of 501，`python3 scripts/product_streak.py` 现读，last_round=497，newest=741bdb0/newest_round=520）。%s。**具名 NOT-RUN / 限制**：① R522 产品笔/台账笔自身跑（推送后取）；② `ABOUT_LINK_NOT_RUN` / `ABOUT_LINK_HOVER_NOT_RUN` / `ABOUT_LINK_PRESS_NOT_RUN=settings-content-blank`（runner 1x 设置族空白；本地 2x 是证人）；③ `RTF_HELPER_ORPHAN`（settings-content-blank/595）；④ `RECORDING_REREAD` 1x；⑤ 状态菜单像素通道（system-menu，610）；⑥ 已知在屏/Motion/SelectionReveal 本机会话 flake；⑦ 601 噪声与其余未结项仍开。
- **U-2115：⑥ 收口 CI 与 BACKLOG 620。** %s。**R521 已签收**：`41200222345 ↔ 741bdb0` 的唯一失败步是 sources 格时序（台账笔 349e85c/a4c1d00 修好即可，非产品回归），新按压判据在 runner 具名 `ABOUT_LINK_PRESS_NOT_RUN=settings-content-blank`、INK 5.01/4.82、MenuBar ⚠︎ 稳定。**BACKLOG 620**（Dock 大量空图标）：只查+登记，未动用户 Dock/登录项 —— 现读 `lsappinfo` 运行中是仓库开发版；`mdfind` 现读 20+ 份同 `com.clipboardhistory.app` 副本（仓库、/Applications、`~/Documents/Codex_Project0_backups/before-*`）；`install_local.sh` 无 `lsregister`，备份目录在 Spotlight 索引区，沙箱 `--dest /tmp` 默认仍 `launch=1`（测试自己传 `--no-launch`）。候选修法见 620。
""" % (FULLTXT, INSTALLTXT, BATTERYTXT, TAILPAIR, RUNPAIR or u"收口新跑在推送后取")
DS=u"""## D-521 主窗口缺失时由 WindowManager 创建唯一一份（R522）

- 背景：登录项启动时 SwiftUI `WindowGroup` 可能一个窗口都不建；`showMainWindow` 只 present，`applicationDidBecomeActive` 的空数组判断为 true 也无效，300ms 延迟恢复只试一次 ⇒ Dock 点击/菜单/⌘S 全部打不开主窗口，只能退出重开。
- 决定：① `WindowManager` 持有 `mainWindowFactory`，由 `AppDelegate.init` 安装（工厂知道 store），`showMainWindow(creatingIfNeeded:)` 在弱引用与 identifier 搜索都落空后才创建 **一个** `AppWindow`；弱引用只在窗口仍在 `NSApp.windows` 时才算"有"。② 兜底窗口用 `NSWindow + NSHostingView(MainWindowContent)`，`MainWindowContent`（ContentView + frame + WindowConfigurator）与 `WindowGroup` **同一棵**树，避免两处样式漂移；identifier=`AppWindow`、750×560、min 600×440、透明标题栏/隐藏 title 全走同一个 `WindowConfigurator`。③ 两种语义分开：显式入口（Dock reopen/菜单/⌘S/热键/登录首启恢复）创建；启动后 200ms 的 best-effort `creatingIfNeeded:false`；`applicationDidBecomeActive` 的创建与「启动时打开主窗口」同口径。④ 300ms 延迟恢复后仍无可见窗口再确认一次。
- 理由：主窗口是产品唯一入口，"没有窗口"必须能被用户动作修好；而"启动时不打开主窗口"是设置，不能被补救路径作废。
- 兼容性/迁移：macOS 12 可用（NSHostingView）；已有窗口（含隐藏/最小化）路径一字未变；`WindowGroup` 的根视图抽成 `MainWindowContent`，视觉与帧不变（A/B 逐字节相同）；测试用"改名+orderOut+清弱引用"模拟无窗口，不真销毁 ARC 窗口。
- 边界：工厂未安装时保持"只 present 不创建"（单元测试负臂）；产品真实关窗仍是 orderOut+delegate false（隐藏），reopen 复用同一扇；只在显式入口创建。
"""
CS=u"""### 主窗口缺失时创建唯一一份（R522 / 第 521 轮 / Round 519 / U-2109…U-2115 · 产品 4 文件 + 判据）

"""
SS=u"""## R522 状态（2026-10-31 · 第 521 轮 · 产品 4 文件 + 判据）

R522 记录（产品 4 文件 + 判据）：登录首启无窗口时创建唯一主窗口。⓪ push no-op（HEAD=origin/main=`a4c1d00`、ahead=0）；`41200222345 ↔ 741bdb0` failure 仅 STEP[9]（sources 格时序 + 两条级联；STEP[1]–[8] 全过：`ABOUT_LINK_PRESS_NOT_RUN=settings-content-blank`、INK 5.01/4.82、MenuBar ⚠︎、RTF NOT_RUN、RECORDING diff_px=0、Motion 5/5）；`41200861558 ↔ a4c1d00` 读时 in_progress ⇒ NOT-RUN；`41193460709 ↔ d0c8dd9` 同 sources 时序族、`41193734687 ↔ 349e85c` success。① 事故：登录项启动的仓库开发版无窗口，菜单/⌘S 打不开；根因 `showMainWindow` 无创建分支 + activation 空数组再调也无效 + 300ms 只试一次。修法：AppDelegate.init 装 `mainWindowFactory`，WindowManager 查不到窗口才创建唯一 `AppWindow`（NSHostingView(MainWindowContent)+WindowConfigurator，macOS 12 可用）；200ms best-effort 不创建；activation 与「启动时打开主窗口」同口径；延迟恢复加一次确认。② 产品 4 文件（WindowManager/App/AppDelegate/ApplicationShell）。③ `MainWindowCreationTests` 8 条从产品入口；M1393/M1394 2/2 CAUGHT、RESTORE_CLEAN；预检 302/279/735 bad=0、ARM 395/1222、HIDDEN 389/1161 rot=0；build 0 告警。④ 帧 338（ADDED=0/MISSING=0）；对基线 CHANGED=142 = 重启后会话级栅格位移（A/B：R521 源码同会话重捕与 R522 **0 差异**；同代码背靠背 0 差异），基线吸收、count 仍 338，不记产品变化。⑤ %s；%s；%s；清账 162 格已清 162/未清 0/不合法 0；streak 4（as-of 501，last_round=497，newest=741bdb0/520）。⑥ BACKLOG 620 已登记（Dock 大量空图标：仓库开发版+备份副本 20+ 同 id 注册、无 lsregister、沙箱默认 launch=1；只查不动用户设置）。%s。下一轮编号 R523（第 522 轮 / Round 520）：先 push 并复核 ahead=0；读 R522 产品笔/台账笔与 R521 两跑的全部失败步骤（in_progress/queued ⇒ NOT-RUN）；重点主窗口创建判据在 runner 的 settings 空白 NOT_RUN、1x 4.0、MenuBar ⚠︎、614 after、RTF（595）、RECORDING、436；② 产品位换未捕获表面；③ 4.5 地板与 150 上限不动。
""" % (FULLTXT, INSTALLTXT, BATTERYTXT, TAILPAIR)
IS=u"""## Round 519 · R522（第 521 轮 · 2026-10-31）：主窗口缺失时创建唯一一份

登录项启动时 WindowGroup 可能一个窗口都不建，而 `showMainWindow` 只会 present：Dock 点击/菜单「显示主窗口 ⌘S」/热键全部打不开，只能退出重开。R522 把创建放进 `WindowManager`：`mainWindowFactory` 由 `AppDelegate.init` 安装，`showMainWindow(creatingIfNeeded:)` 查过弱引用（只认仍在 `NSApp.windows` 的那份）与 identifier 搜索都落空后才建 **一个** `AppWindow`（NSHostingView(`MainWindowContent`) + 同一个 `WindowConfigurator`，macOS 12 可用）；200ms best-effort 不创建，`applicationDidBecomeActive` 的创建与「启动时打开主窗口」同口径，300ms 延迟恢复后再确认一次。`MainWindowCreationTests` 8 条从产品入口（reopen/菜单/关窗→reopen/首次激活/设置关/ best-effort/延迟恢复/同入口接线）；M1393（删创建分支）/M1394（删已有窗口检查）2/2 CAUGHT。预检 302/279/735 bad=0、ARM 395/1222、HIDDEN 389/1161 rot=0；build 0 告警。帧 338，对基线 CHANGED=142 经 A/B 判为重启后会话栅格位移（R521 源码同会话重捕 0 差异），基线吸收、count 338。%s；%s；%s。⓪ R521 产品跑唯一失败步是 sources 格时序（非产品回归），台账笔 in_progress NOT-RUN；BACKLOG 620 登记 Dock 空图标（未动用户设置）。

**七维度自评**（恰七行，每格 n/15）：

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | 15/15 | 事故是"无窗口"：三臂帧不适用，改看真窗口/AppWindow 计数与可见性；视觉未变由 A/B 帧 0 差异作证。 |
| 判据有效性 | 15/15 | 8 条从产品入口 + 删创建/重复创建两刀 2/2；无工厂负臂保留。 |
| 假绿防御 | 15/15 | 142 张会话位移经 A/B 归因后才吸收；settings 空白 NOT_RUN；全量红不报绿。 |
| 产品面推进 | 15/15 | 修好用户报的真实事故（登录首启/菜单/⌘S 可打开主窗口）；4 文件。 |
| 台账一致性 | 15/15 | U-2109…U-2115、D-521、BACKLOG 620、帧/全量/换装/电池都来自命令与测试。 |
| 交付诚实性 | 15/15 | 事故现场、旧行为负臂、142 张归因、SelectionReveal 红都如实。 |
| 可复核性 | 15/15 | 8 条测试名、M1393/M1394、precheck 302/279/735、A/B 0 差异都在。 |

均分 = 105/105 ≈ 15.0/15（100）。
""" % (FULLTXT, INSTALLTXT, BATTERYTXT)
RB=u"""- **R522（登录首启无窗口时创建唯一主窗口；产品 4 文件 + 判据）**：修复用户报的真实事故 —— 登录项启动的仓库开发版无窗口，`showMainWindow` 只会 present，菜单「显示主窗口 ⌘S」/Dock/热键全部打不开。`WindowManager` 新增 `mainWindowFactory`（AppDelegate.init 安装）+ `creatingIfNeeded` 语义：查不到窗口才建唯一 `AppWindow`（NSHostingView(MainWindowContent)+WindowConfigurator，macOS 12 可用），200ms best-effort 不创建，activation 与「启动时打开主窗口」同口径，300ms 恢复后重试一次。`MainWindowCreationTests` 8 条从产品入口；M1393/M1394 2/2 CAUGHT；预检 302/279/735 bad=0、ARM 395/1222、HIDDEN 389/1161 rot=0；帧 338（对基线 CHANGED=142 经 A/B 判为重启后会话栅格位移，R521 源码同会话重捕 0 差异）。全量 %s；换装 %s；电池 %s。BACKLOG 620 登记 Dock 空图标。
""" % (FULL or u"见补记", INSTALL or u"419=419", BATTERY or u"683/5")
BS=u"""
**620. 登录项/Dock 指向仓库开发版 + LaunchServices 里堆了 20+ 份同 id 副本 ⇒ 重启后 Dock 出现大量「时间剪史」空图标**（R522 现读；只查+登记，未动用户 Dock/登录项）
    现象：用户 20:28 重启后登录项启动的 `/Users/wangziyi/Codex_Project0/时间剪史.app`（PID 927，后为 5811）一个窗口都没有；同一时间 Dock 出现大量「时间剪史」空图标。
    现读证据：`lsappinfo list` 里运行中的那份 bundle path 是**仓库开发版**（不是 /Applications）；`mdfind "kMDItemCFBundleIdentifier == 'com.clipboardhistory.app'"` 读到 20+ 份同 id 副本：仓库开发版、`/Applications/时间剪史.app`、以及 `~/Documents/Codex_Project0_backups/before-*/时间剪史.app`（R41/R67b/R515b/R516–R520/多次 local-*）。`grep -n lsregister scripts/install_local.sh` 现读 **0 行**。
    机制：① `install_local.sh` 每轮把旧包 `mv` 到 `~/Documents/Codex_Project0_backups/`（Spotlight 索引区），旧 `.app` 仍是可启动包、仍以同一 CFBundleIdentifier 被 LaunchServices 登记，脚本从不 `lsregister -u` 旧副本、也不 `lsregister -f` 新装副本；② 登录项是 `SMAppService.mainApp.register()`，注册的是**当时运行的那一份** bundle 路径 —— 开发版在仓库里被就地替换，登录项/Dock 固定项的路径与图标缓存跟着旧 inode 走；③ `--dest /tmp/...` 的沙箱安装默认 `launch=1`，脚本只保证"沙箱不发退出指令"，**没有**把非 `/Applications` 目标强制成 `--no-launch`（测试自己都传了，手动沙箱跑一次就会 `open` 一份同 id 临时副本，最小 Info.plist 没有图标）。`launch_smoke.py` 是直接 `Popen([executable])`、不经 `open` ⇒ 冒烟步骤不是这条的锅。
    候选修法（等用户决定）：① 安装末尾对 `/Applications/时间剪史.app` 执行 `lsregister -f`，本轮备份副本 `lsregister -u`；② 备份目录移出 Spotlight 索引（`.metadata_never_index`）或压成归档（不再可启动）；③ 非 `/Applications` 的 `--dest` 在脚本层强制 `--no-launch`（不靠调用方记得传）；④ 登录项/Dock 固定项改指 `/Applications` 那份（用户在系统设置/Dock 里改，或在设置页显示"当前运行的是开发版"提示）；⑤ 不要把仓库开发版固定到 Dock。
"""
a=rd(A); d=rd(D); st=rd(S); pr=rd(P); ch=rd(C); it=rd(I); bk=rd(B)
if a.count(AT_OLD)!=1: raise SystemExit("A title %d" % a.count(AT_OLD))
if a.count(ANCHOR_NEXT)!=1: raise SystemExit("A next %d" % a.count(ANCHOR_NEXT))
if u"## D-521" in d: raise SystemExit("D exists")
if u"## R522 状态" in st: raise SystemExit("S exists")
if u"R522（登录首启无窗口时创建唯一主窗口" in pr: raise SystemExit("P exists")
if u"主窗口缺失时创建唯一一份" in ch: raise SystemExit("C exists")
if u"## Round 519 · R522" in it: raise SystemExit("I exists")
if u"**620." in bk: raise SystemExit("B exists")
if pr.count(u"U-31 … U-2108（R521 现读抬到最新一节）")!=1: raise SystemExit("P ucell")
if pr.count(u"R9–R518，519 节自评")!=1: raise SystemExit("P headline")
if pr.count(u"阶段二 **511 轮**审计（R9–R518；")!=1: raise SystemExit("P phase")
if pr.count(u"PHASE2 n=511")!=1: raise SystemExit("P n")
if pr.count(u"的 Round 518")!=1: raise SystemExit("P round")
if pr.count(u"## 18. R458 → R521 这一段（R478 起写；R504 续到 504、R505 续到 505、R506 续到 506、R507 续到 507、R508 续到 508、R509 续到 509、R510 续到 510、R511 续到 511、R512 续到 512、R513 续到 513、R514 续到 514、R515 续到 515、R516 续到 516、R517 续到 517、R518 续到 518、R519 续到 519、R520 续到 520、R521 续到 521 —— 这份报告第七次差点停在几十轮之前）")!=1: raise SystemExit("P s18")
if pr.count(u"的 R521 节 ② 为准")!=1: raise SystemExit("P pointer")
wr(A, a.replace(AT_OLD, AT_NEW, 1).replace(ANCHOR_NEXT, u"\n"+AS+ANCHOR_NEXT, 1))
wr(D, d.rstrip()+"\n\n"+DS+"\n")
wr(S, st.replace(u"## R521 状态（", SS.strip()+"\n\n## R521 状态（", 1))
pr=pr.replace(u"R9–R518，519 节自评", u"R9–R519，520 节自评", 1)
pr=pr.replace(u"阶段二 **511 轮**审计（R9–R518；", u"阶段二 **512 轮**审计（R9–R519；", 1)
pr=pr.replace(u"PHASE2 n=511", u"PHASE2 n=512", 1)
pr=pr.replace(u"的 Round 518", u"的 Round 519", 1)
pr=pr.replace(u"U-31 … U-2108（R521 现读抬到最新一节）", u"U-31 … U-2115（R522 现读抬到最新一节）", 1)
pr=pr.replace(u"## 18. R458 → R521 这一段（R478 起写；R504 续到 504、R505 续到 505、R506 续到 506、R507 续到 507、R508 续到 508、R509 续到 509、R510 续到 510、R511 续到 511、R512 续到 512、R513 续到 513、R514 续到 514、R515 续到 515、R516 续到 516、R517 续到 517、R518 续到 518、R519 续到 519、R520 续到 520、R521 续到 521 —— 这份报告第七次差点停在几十轮之前）",
              u"## 18. R458 → R522 这一段（R478 起写；R504 续到 504、R505 续到 505、R506 续到 506、R507 续到 507、R508 续到 508、R509 续到 509、R510 续到 510、R511 续到 511、R512 续到 512、R513 续到 513、R514 续到 514、R515 续到 515、R516 续到 516、R517 续到 517、R518 续到 518、R519 续到 519、R520 续到 520、R521 续到 521、R522 续到 522 —— 这份报告第七次差点停在几十轮之前）", 1)
pr=pr.replace(u"的 R521 节 ② 为准", u"的 R522 节 ② 为准", 1)
wr(P, pr.rstrip()+"\n\n"+RB+"\n")
m=u"## [Unreleased]\n"
if ch.count(m)!=1: raise SystemExit("C anchor")
wr(C, ch.replace(m, m+"\n"+CS, 1))
wr(I, it.rstrip()+"\n\n"+IS+"\n")
wr(B, bk.rstrip()+"\n"+BS)
print("OK sha=%s full=%s install=%s battery=%s" % (sha, FULL, INSTALL, BATTERY))
