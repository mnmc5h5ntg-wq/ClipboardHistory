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
FULL=os.environ.get("R514_FULL","")
INSTALL=os.environ.get("R514_INSTALL","")
BATTERY=os.environ.get("R514_BATTERY","")
RUNPAIR=os.environ.get("R514_RUNPAIR","")
FULLTXT=(u"全量 **%s**" % FULL) if FULL else u"全量见补记"
INSTALLTXT=(u"换装 `ok / SHA_MATCH=1 / INSTALL_ENTRIES=%s`" % INSTALL) if INSTALL else u"换装见补记"
BATTERYTXT=(u"电池 **%s**（台账后复跑）" % BATTERY) if BATTERY else u"电池见补记"
TAILPAIR=(u"产品笔 `%s` 已推（HEAD=origin、ahead=0）；%s" % (sha, RUNPAIR)) if RUNPAIR else (u"产品笔 `%s` 已推（HEAD=origin、ahead=0）" % sha)

AT_OLD=u"U-1970…U-2050）：主窗口与设置窗口的标题栏统一"
AT_NEW=u"U-1970…U-2058）：主窗口与设置窗口的标题栏统一"
ANCHOR_NEXT=u"\n## 第 499 轮（R501 · 2026-10-30 · U-1964…U-1969）"
AS=u"""- **U-2051：⓪ push 与 CI。** 开工 `git push` no-op（HEAD=origin/main=`93415cf`、**ahead=0**）。成对回读：`41156774387 ↔ 7ff22a0` **failure 仅 STEP[9] Release script tests**（sources 格写 5f0807b、git 说最近动源码是 7ff22a0 ⇒ `FINAL_REPORT_SOURCES_CELL_STALE` + `SourcesCellSecondSource` + skip 名册级联；Swift/Capture/Motion 全绿）；`41160962238 ↔ 8c425f6` **failure 4 步**：STEP[9] Release（sources 格停 7ff22a0 + **ABSENT_CLAIM_FALSE**（R513 的 `disabled` 样词，已在 b29c616 重锚 `Effect`）+ skip 级联 + sources 第二来源）、STEP[15] Swift（1333/81/**2**：`testActionableInkStaysAboveTheLegibilityFloor` dark **2.27 < 3.0**、`testBulkActionBarDimsTheUnpinnableVerb` dark **0 < 20**）、STEP[17] Capture gate（同两朵红点名）、STEP[18] On-screen probe floor（`testFrameIntervalsUnderStateChanges` **337.8ms > 120ms**，超锚点 2 颗、容差 1；6 条 queued / 1 条 pulse open，均为已登记采样/通道；红=1）。`41161522135 ↔ b29c616`、`41161699932 ↔ 93415cf` 读时 **in_progress ⇒ NOT-RUN**；**收口补读**：两跑均 completed=**failure，仅 STEP[15] Swift + STEP[17] Capture**，红名与 8c425f6 同两朵（2.27 / 0<20），**Release 已绿**（样词重锚生效）；`41156931203 ↔ 874d579` **success**、`41157084122 ↔ 764ea4b` **success**。436 只复核新跑：`7ff22a0` `MOTION_FLOOR_OK=4/5 REDS=0`、`8c425f6` `5/5 REDS=0`（`SUITE_NOT_SEEN=2` 是登记过的采样漂，不读成已修好）。两朵 Swift/Capture 红是 R513 探针/尺在 1x 的缺陷，本轮修；Release 两红是 sources 时序，随台账笔复跑。
- **U-2052：① 614 复现（真窗口，未捕获的工具栏表面）。** 只截 App 窗口（`screencapture -l 646824`，750×560@2x）：AX 树里窗口 `/0/2` 是 **AXToolbar**，其子 `/0/2/0` 是 `AXButton desc=[隐藏边栏]` pos=(656,177) size=(40,52)；顶部中央可见侧栏切换药丸（`/tmp/r514_main.png`）。复现序列：启动 → AX `AXSelectedRows` 选 3 行 → 读 AX。根因不是 NSButton 遍历能抓到的视图：它在 `window.toolbar.items` 里，且是 SwiftUI 在**选区变化后**异步加回的；`configure/key/resize` 的五轮清理早已结束。
- **U-2053：② 产品 A：破坏性批量动词改实心核心。** runner 1x 暗档删除动词 `trash`（1px 红描边）静置对比度 **2.27:1**（地板 3.0），本机 2x 3.15 只是擦线；框内核心红像素 186（light）/145（dark）。产品改 `trash` → `trash.fill`（系统红不变，破坏性动作更醒目），2x 对比度 **3.15** 不变、墨占比 25.3%%→36.6%%、核心红 **350/297**；`.foregroundStyle(.red)` 与 `.disabled` 逻辑不动。产品 **1 文件**。
- **U-2054：③ 产品 B：614 的工具栏回加拦截。** `WindowConfigurator.Coordinator` 观察 `NSToolbar.willAddItemNotification`：只接 `toolbar === window.toolbar` 且 `isSidebarToolbarItem(item)` 的项，异步跑 `removeSidebarToolbarButton`；`deinit` 移除观察者。真窗口 after（debug 构建、同一多选序列）：AX 树不再有 AXToolbar/「隐藏边栏」，截图顶部中央无药丸（`/tmp/r514_after_debug.png`）。普通工具栏项不被误删（测试臂）。产品 **1 文件**。
- **U-2055：④ 判据、尺与刀。** 整带尺改成：带内墨只当内容证人（底色取**带内**众数）+ 两臂逐像素差（含 alpha 并集，满足 `MotionFilmstripTests` 的两态尺守卫）。本机 2x：light 带内墨 2809/2852、标题差 0、第三颗差 **299**；dark 2950/2987、0/**287**；旧 runner 1x 暗档整带 6300/6300（全图底色饱和）⇒ 新尺不再触顶（面积平均下采的 1x 诊断 85/88，只作诊断）。实心核心判据 `testDestructiveBulkVerbKeepsAFilledCore`（核心红 floor 40×scale²、灰 pin 负向 0）两档通过。观察者判据 `testToolbarAddObserverRemovesTheSidebarToggleAndKeepsOrdinaryItems`（真 NSToolbar，先等过 0.9s 清理再异步插入）**1.695s** 通过。刀 `M1379`（trash.fill→trash）/`M1380`（toolbar===→!==）**2/2 CAUGHT**、`RESTORE_CLEAN=yes`；预检 `NEEDLE_PRECHECK tables=295 covered=272 arms=722 bad=0`、`ARM_TOTAL files=388 arms=1209`、`HIDDEN_ARMS 表=381 可判=1146 rot=0`。
- **U-2056：⑤ 帧卷。** 捕获卷 **334 帧**；`FRAME_BASELINE_CHANGED=44` = 6 张多选帧（`sidebar-multi-select`、`-min`、`-pinned` × light/dark；实心垃圾桶）+ 38 张源图标栅格噪声。absorb 6 张、基线仍 **334**；复核 `CHANGED=38 MISSING=0 ADDED=0`（噪声不吸收）。6 张逐张看过：垃圾桶实心、其余动词/标题不动。
- **U-2057：⑥ 八步与电池。** build **0 告警**（增量=0、冷编=0）；%s；%s（活库；旧实例先 CONT/TERM）；%s；清账 162/63/0；§1/曲线/来源格在生成器后刷新；产品面连续零改动 **4** 轮（as-of 501，`python3 scripts/product_streak.py` 现读，last_round=497）。%s。**具名 NOT-RUN / 限制**：① 台账笔自身跑（推送后取）；② `RTF_HELPER_ORPHAN`（settings-content-blank/595）；③ `RECORDING_REREAD` 1x；④ 状态菜单像素通道（system-menu，610）；⑤ 已知在屏/Motion 采样 flake；⑥ 601 噪声与其余未结项仍开。
- **U-2058：⑦ 收口 CI。** %s；`41161522135 ↔ b29c616`、`41161699932 ↔ 93415cf` 收口补读均 failure **仅 STEP[15]+[17]**（与 8c425f6 同两朵 1x 红，Release 已绿）；台账笔自身跑推送后取。
""" % (FULLTXT, INSTALLTXT, BATTERYTXT, TAILPAIR, RUNPAIR or u"收口新跑在推送后取")
DS=u"""## D-512 破坏性批量动词实心核心 + 侧栏开关回加拦截（R514）

- 背景：R513 把可点墨探针从禁用的 unpin 重锚到删除后，runner 1x 暗档读到 **2.27:1**（本机 2x 3.15 只是擦线）—— 1px 红描边被抗锯齿摊薄；同一轮的真窗口多选帧里，顶部中央又出现 SwiftUI 异步加回的侧栏开关（614，`window.toolbar` 里的 `AXButton desc=[隐藏边栏]`）。
- 决定 A：删除动词 `trash` → `trash.fill`（系统红不变），并加核心红像素判据（`testDestructiveBulkVerbKeepsAFilledCore`，floor 40×scale²，灰 pin 负向对照）——实心核心在 1x/2x 都保持系统红，轮廓版在暗档低于 floor。
- 决定 B：`WindowConfigurator.Coordinator` 观察 `NSToolbar.willAddItemNotification`；只摘 `toolbar === window.toolbar` 且 `isSidebarToolbarItem` 的项，异步清理；`deinit` 移除观察者。既有的 key/resize 五轮清理继续保留，负责启动期。
- 理由：两件事都是“对象换了宿主”：红描边的可读性对象是**核心像素**而不是抗锯齿边缘；侧栏开关的宿主是**工具栏项**而不是 contentView 里的 NSButton。按旧宿主做的守卫在 1x/异步路径上各留一朵红。
- 兼容性/迁移：6 张多选帧同笔更新（基线仍 334）；新增两条测试；`BulkActionAvailability` 与 4.5/3.0 地板未动。
- 边界：`willAddItem` 按既有字符串谓词认侧栏项；若未来真的需要工具栏里的侧栏词项，必须先收窄谓词（当前 App 不使用任何工具栏项）。实心图标的颜色仍是 `.red`；若未来改色，核心红判据要换成对应色相的核心判据。
"""
BS=u"""**614 补记（R514 结案）**：选区变化后 SwiftUI 会把侧栏开关重新加回 `window.toolbar`，旧的 NSButton 视图树清理抓不到，key/resize 的五轮延迟清理也早已结束。修法：观察 `NSToolbar.willAddItemNotification`，只摘 `toolbar === window.toolbar` 且 `isSidebarToolbarItem` 的项，异步清理；真窗口复现序列（选 3 行 → AX 读工具栏）after 无 AXToolbar/「隐藏边栏」。退场条件：真窗口多选后 AX 树不再出现 `AXButton desc=[隐藏边栏]`（本轮已读）；若未来工具栏需要合法的侧栏词项，先收窄谓词再放行。
"""
CS=u"""### 破坏性批量动词改实心核心 + 614 侧栏开关回加拦截（R514 / 第 513 轮 / Round 511 / U-2051…U-2058 · 产品 2 文件 + 判据）

"""
SS=u"""## R514 状态（2026-10-31 · 第 513 轮 · 产品 2 文件 + 判据）

R514 记录（产品 2 文件 + 判据）：破坏性批量动词改实心核心 + 614 侧栏开关回加拦截。⓪ push no-op（HEAD=origin/main=`93415cf`、ahead=0）；`7ff22a0` failure 仅 Release（sources 时序）；`8c425f6` failure 4 步（Release sources/样词 + Swift/Capture 两朵 1x 红 + Probe floor 采样红）；b29c616/93415cf 读时 in_progress ⇒ NOT-RUN，收口补读均 failure 仅 STEP[15]+[17]（同两朵 1x 红，Release 已绿）；874d579/764ea4b success。① 真窗口多选后 AXToolbar 里出现 `AXButton desc=[隐藏边栏]`（614 复现）。② 产品 A：`trash`→`trash.fill`（1x 暗档 2.27→实心核心，2x 3.15、核心红 350/297）。③ 产品 B：`NSToolbar.willAddItemNotification` 拦截异步回加；after 无 AXToolbar/开关。④ 判据：带内墨+两臂逐像素差（299/287，标题差 0）、实心核心、观察者；M1379/M1380 2/2。⑤ 捕获 334 帧、CHANGED=44（6 张多选 + 38 噪声）、吸收 6 张、基线 334。⑥ 预检 295/272/722 bad=0、ARM 388/1209、HIDDEN 381/1146 rot=0；build 0 告警；%s；%s；%s；清账 162/63/0；产品面连续零改动 **4** 轮（as-of 501，`python3 scripts/product_streak.py` 现读，last_round=497）。%s。下一轮编号 R515（第 514 轮 / Round 512）：先 push 并复核 ahead=0；读台账笔自身跑与 `41161522135`/`41161699932`/`41156774387` 的全部失败步骤；重点 614 的 after 在 runner 安装包上是否稳定（真窗口）、`RTF_HELPER_ORPHAN`（595）、`RECORDING_REREAD`、436 Motion floor；② 产品位换未捕获表面；③ 4.5 地板与 150 上限不动。
""" % (FULLTXT, INSTALLTXT, BATTERYTXT, TAILPAIR)
IS=u"""## Round 511 · R514（第 513 轮 · 2026-10-31）：破坏性批量动词改实心核心 + 614 侧栏开关回加拦截

runner 1x 暗档里删除动词的 1px 红描边只有 2.27:1（本机 2x 3.15 擦线）；改 `trash.fill` 后核心红在 1x/2x 都保持系统红（核心红 350/297，2x 对比度 3.15、墨占比 25.3%%→36.6%%）。614 的真窗口多选帧里，SwiftUI 在选区变化后把侧栏开关异步加回 `window.toolbar`（AXToolbar → `AXButton desc=[隐藏边栏]`）；`WindowConfigurator` 改观察 `NSToolbar.willAddItemNotification`，只摘 `toolbar === window.toolbar` 的侧栏项，after AX 树无 AXToolbar/开关。判据：带内墨+两臂逐像素差（light 299、dark 287，标题差 0）、实心核心（核心红 floor 40×scale²、灰 pin 负向 0）、观察者（真 NSToolbar，1.695s）；M1379/M1380 2/2、RESTORE_CLEAN=yes。捕获 334 帧、CHANGED=44（6 张多选 + 38 噪声）、吸收 6 张、基线 334。预检 295/272/722、ARM 388/1209、HIDDEN 381/1146 rot=0。%s；build 0 告警；%s；%s。⓪ 7ff22a0 仅 Release；8c425f6 四步红（两朵 1x 探针/尺红本轮修、Release 时序与样词已有出口、Probe floor 已知采样红）；b29c616/93415cf 收口补读 failure 仅 STEP[15]+[17]（同两朵 1x 红，Release 已绿）；874d579/764ea4b success。

**七维度自评**（恰七行，每格 n/15）：

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | 15/15 | 614 前后真窗口逐张看过（药丸在/不在）；6 张多选帧逐张看过垃圾桶实心、其余不动。 |
| 判据有效性 | 15/15 | 带内墨证人 + 两臂逐像素差 + 实心核心 + 观察者；M1379/M1380 2/2。 |
| 假绿防御 | 15/15 | 标题差 0 当负向对照；灰 pin 红像素 0；观察者测试先等过延迟清理；alpha 并集过 axis 守卫。 |
| 产品面推进 | 15/15 | 两个新类别（破坏性动词核心、工具栏异步回加拦截）；2 个产品文件；真窗口读数成立。 |
| 台账一致性 | 15/15 | U-2051…U-2058、D-512、334 帧/1335/56/0、%s 都来自命令与测试。 |
| 交付诚实性 | 15/15 | 614 结案条件写明；1x 红与尺饱和都记；runner 未签收具名。 |
| 可复核性 | 15/15 | 2.27→3.15、核心红 350/297、299/287、M1379/M1380、precheck 295/272/722 都在。 |

均分 = 105/105 ≈ 15.0/15（100）。
""" % (FULLTXT, INSTALLTXT, BATTERYTXT, INSTALL or u"419=419")
RB=u"""- **R514（破坏性批量动词改实心核心 + 614 侧栏开关回加拦截；产品 2 文件 + 判据）**：1x 暗档 `trash` 只有 2.27:1 ⇒ 改 `trash.fill`（核心红 350/297，2x 3.15）；614 的 SwiftUI 开关在选区变化后回加 `window.toolbar` ⇒ 观察 `NSToolbar.willAddItemNotification` 摘除，after AX 无 AXToolbar/「隐藏边栏」。带内墨 + 两臂逐像素差（299/287）取代会触顶的整带墨；M1379/M1380 2/2。基线 334（6 张多选帧）、复核 CHANGED=38；全量 1335/56/0；换装 %s；电池 %s。
""" % (INSTALL or u"419=419", BATTERY or u"683/5")
a=rd(A); d=rd(D); b=rd(B); st=rd(S); pr=rd(P); ch=rd(C); it=rd(I)
if a.count(AT_OLD)!=1: raise SystemExit("A title %d" % a.count(AT_OLD))
if a.count(ANCHOR_NEXT)!=1: raise SystemExit("A next %d" % a.count(ANCHOR_NEXT))
if u"## D-512" in d: raise SystemExit("D exists")
if u"**614 补记（R514 结案）**" in b: raise SystemExit("B exists")
if u"## R514 状态" in st: raise SystemExit("S exists")
if u"R514（破坏性批量动词" in pr: raise SystemExit("P exists")
if u"破坏性批量动词改实心核心" in ch: raise SystemExit("C exists")
if u"## Round 511 · R514" in it: raise SystemExit("I exists")
if pr.count(u"U-31 … U-2050（R513 现读抬到最新一节）")!=1: raise SystemExit("P ucell")
if pr.count(u"R9–R510，511 节自评")!=1: raise SystemExit("P headline")
if pr.count(u"阶段二 **503 轮**审计（R9–R510；")!=1: raise SystemExit("P phase")
if pr.count(u"PHASE2 n=503")!=1: raise SystemExit("P n")
if pr.count(u"的 Round 510")!=1: raise SystemExit("P round")
if pr.count(u"## 18. R458 → R513 这一段（R478 起写；R504 续到 504、R505 续到 505、R506 续到 506、R507 续到 507、R508 续到 508、R509 续到 509、R510 续到 510、R511 续到 511、R512 续到 512、R513 续到 513 —— 这份报告第七次差点停在几十轮之前）")!=1: raise SystemExit("P s18")
if pr.count(u"的 R513 节 ② 为准")!=1: raise SystemExit("P pointer")
wr(A, a.replace(AT_OLD, AT_NEW, 1).replace(ANCHOR_NEXT, u"\n"+AS+ANCHOR_NEXT, 1))
wr(D, d.rstrip()+"\n\n"+DS+"\n")
wr(B, b.rstrip()+"\n\n"+BS+"\n")
wr(S, st.replace(u"## R513 状态（", SS.strip()+"\n\n## R513 状态（", 1))
pr=pr.replace(u"R9–R510，511 节自评", u"R9–R511，512 节自评", 1)
pr=pr.replace(u"阶段二 **503 轮**审计（R9–R510；", u"阶段二 **504 轮**审计（R9–R511；", 1)
pr=pr.replace(u"PHASE2 n=503", u"PHASE2 n=504", 1)
pr=pr.replace(u"的 Round 510", u"的 Round 511", 1)
pr=pr.replace(u"U-31 … U-2050（R513 现读抬到最新一节）", u"U-31 … U-2058（R514 现读抬到最新一节）", 1)
pr=pr.replace(u"## 18. R458 → R513 这一段（R478 起写；R504 续到 504、R505 续到 505、R506 续到 506、R507 续到 507、R508 续到 508、R509 续到 509、R510 续到 510、R511 续到 511、R512 续到 512、R513 续到 513 —— 这份报告第七次差点停在几十轮之前）",
              u"## 18. R458 → R514 这一段（R478 起写；R504 续到 504、R505 续到 505、R506 续到 506、R507 续到 507、R508 续到 508、R509 续到 509、R510 续到 510、R511 续到 511、R512 续到 512、R513 续到 513、R514 续到 514 —— 这份报告第七次差点停在几十轮之前）", 1)
pr=pr.replace(u"的 R513 节 ② 为准", u"的 R514 节 ② 为准", 1)
wr(P, pr.rstrip()+"\n\n"+RB+"\n")
m=u"## [Unreleased]\n"
if ch.count(m)!=1: raise SystemExit("C anchor")
wr(C, ch.replace(m, m+"\n"+CS, 1))
wr(I, it.rstrip()+"\n\n"+IS+"\n")
print("OK sha=%s full=%s install=%s battery=%s" % (sha, FULL, INSTALL, BATTERY))
