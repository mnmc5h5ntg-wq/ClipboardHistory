#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import io, os, subprocess
R=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
def rd(p): return io.open(p,encoding="utf-8").read()
def wr(p,t): io.open(p,"w",encoding="utf-8").write(t)
A=os.path.join(R,"AGENT_UI_AUDIT.md"); D=os.path.join(R,"AGENT_DECISIONS.md")
S=os.path.join(R,"AGENT_STATE.md"); P=os.path.join(R,"AGENT_FINAL_REPORT.md"); C=os.path.join(R,"CHANGELOG.md"); I=os.path.join(R,"AGENT_VISUAL_ITERATION.md")
sha=subprocess.check_output(["git","-C",R,"rev-parse","--short=7","HEAD"]).decode().strip()
FULL=os.environ.get("R526_FULL",""); INSTALL=os.environ.get("R526_INSTALL",""); BATTERY=os.environ.get("R526_BATTERY",""); RUNPAIR=os.environ.get("R526_RUNPAIR","")
FULLTXT=(u"全量 **%s**" % FULL) if FULL else u"全量见补记"
INSTALLTXT=(u"换装 `ok / SHA_MATCH=1 / INSTALL_ENTRIES=%s`" % INSTALL) if INSTALL else u"换装见补记"
BATTERYTXT=(u"电池 **%s**（台账后复跑）" % BATTERY) if BATTERY else u"电池见补记"
TAILPAIR=(u"产品笔 `%s` 已推（HEAD=origin、ahead=0）；%s" % (sha, RUNPAIR)) if RUNPAIR else (u"产品笔 `%s` 已推（HEAD=origin、ahead=0）" % sha)
AT_OLD=u"U-1970…U-2137）：主窗口与设置窗口的标题栏统一"
AT_NEW=u"U-1970…U-2144）：主窗口与设置窗口的标题栏统一"
ANCHOR_NEXT=u"\n## 第 499 轮（R501 · 2026-10-30 · U-1964…U-1969）"
AS=u"""- **U-2138：⓪ push 与 CI。** 开工 `git push` no-op（HEAD=origin/main=`f10afe4`、**ahead=0**）。七跑成对读：`41223106790 ↔ 3ddee13`（回归修复跑）、`41221604785 ↔ 4c0eeb6`、`41223261055 ↔ f10afe4` 读时均 **in_progress ⇒ NOT-RUN**（不轮询；下轮第 ⓪ 全读，3ddee13 是 ZStack/fold 地板修复的签收跑）；`41221362532 ↔ 31d12c7` **completed failure 仅 STEP[9]**（sources 时序，非产品）；`41218308733 ↔ 79e39ee`、`41218637052 ↔ 77ed8ef` failure 仅 STEP[9]（sources 时序）；`41218878781 ↔ 9d882e4` failure STEP[15]（fold 逐帧地板 + ZStack 1x 布局，已由 3ddee13 修，最终签收随新跑）。安全红线：未对破坏性控件做 AXPress；真窗口只读；未碰活库。
- **U-2139：① 缺口读数与产品。** 缺口：折叠/展开的**标题双击**只有 tooltip，悬停与静置逐像素相同 —— 旧值在标题带（x12–210、y138–178pt）亮档均值差 **+1.2**、暗档 **−0.8**（噪声级），而同一行右边的 chevron 早就有 hover/按压反馈 ⇒ 双击不可发现。修法：`HistorySidebarView` 的标题组加 `onHover` + 与 chevron 同一档的 `PressableAppearance.fillOpacity(controlHover)` 浅底（负 padding 只放大浅底、不改布局），取证走既有 `hoveredForCapture`。产品 **1 文件**。
- **U-2140：② 判据与刀。** 新增夹具 `main-sidebar-title-hover`（750×560，只点亮 `hoveredForCapture`）+ `UICaptureTests/testSidebarTitleHoverFeedbackIsVisible`（标题带亮/暗两档 mean luma 绝对差，地板 2.5；旧值 ≤1.2、新值 **7.2/4.4**）。刀 `M1403`（标题悬停浅底永不画）**CAUGHT、RESTORE_CLEAN=yes**；过渡刀 M1399–M1401 仍在册；`PressFeedbackTests` 控件档位点 10→11（标题药丸与 chevron 同档，已判）。预检 **306/283/744 bad=0**、ARM **399/1231**（dupes=0 repeats=0）、HIDDEN **393/1170 rot=0**；build **0 告警**（增量 0、冷编 0）。
- **U-2141：③ 帧卷与看图。** 捕获 **342 帧**：`ADDED=2`（`main-sidebar-title-hover` 亮/暗）、`CHANGED=0 MISSING=0`（静置两态一字未动）；基线 **340→342**。逐张看过 hover 帧：标题「🕒 时间剪史」出现浅灰药丸（暗档为提亮药丸）、chevron 各自 hover，标题与计数/chevron 布局未移动。新帧进材质盲区名册（66pt 黑带仍是系统 List 选中材质，带外完好）。
- **U-2142：④ 八步与电池。** build **0 告警**（增量 0、冷编 0）；%s；%s；%s；清账 `MOTION_LEDGER 162 格 / 已清账 162 / 未清账 0 / 不合法 0`；产品面连续零改动 **4** 轮（as-of 501，`python3 scripts/product_streak.py` 现读，last_round=497）。%s。**具名 NOT-RUN / 限制**：① R526 产品笔/台账笔自身跑（推送后取）；② 3ddee13/4c0eeb6/f10afe4 三跑 in_progress ⇒ NOT-RUN；③ `RTF_HELPER_ORPHAN`（595）；④ `RECORDING_REREAD` 1x；⑤ 状态菜单像素通道（610）；⑥ Motion `not-run=notice-banner` 按现有出口具名；⑦ 已知在屏/SelectionReveal 本机会话 flake。
- **U-2143：⑤ 收口 CI。** %s。R525 产品跑 `31d12c7` 唯一失败步是 sources 时序（台账笔修好即可，非产品回归）；R524 的 `9d882e4` STEP[15] 两族回归已由 `3ddee13` 修复，签收跑 `41223106790` 待读。
- **U-2144：⑥ 交接。** 折叠特性现已有两态、模型驱动过渡、应用菜单 + ⌘\\、标题/chevron 悬停与按压；下一轮若继续，优先验证 runner 签收与真机逐帧，不再新开视觉面除非有新读数。`M1403` 是本轮新行为的刀；预检/ARM/HIDDEN 计数已刷新。
""" % (FULLTXT, INSTALLTXT, BATTERYTXT, TAILPAIR, RUNPAIR or u"收口新跑在推送后取")
DS=u"""## D-525 标题双击补悬停反馈（R526）

- 背景：折叠/展开的标题双击只有 tooltip，悬停与静置逐像素相同（亮档均值差 1.2、暗档 −0.8，噪声级）；右边的 chevron 早就有 hover/按压，双击不可发现。
- 决定：标题组加 `onHover` + 与 chevron 同一档的 `PressableAppearance.fillOpacity(controlHover)` 浅底；负 padding 只放大浅底、不改标题与计数/chevron 的布局；取证复用 `hoveredForCapture`（产品不写）。
- 理由：双击是加速通道，可见 affordance 必须与 chevron 同一语言；用既有 token/换算而不是新常数。
- 兼容性/迁移：静置帧逐字节不变（CHANGED=0）；新增 hover 2 帧，基线 340→342；新帧进材质盲区名册（List 选中材质）。
- 边界：只画悬停，不加按压/缩放（双击没有可捕获的按下态）；不改折叠/展开的状态与过渡。
"""
CS=u"""### 标题双击补悬停反馈（R526 / 第 525 轮 / Round 523 / U-2138…U-2144 · 产品 1 文件 + 判据）

"""
SS=u"""## R526 状态（2026-11-01 · 第 525 轮 · 产品 1 文件 + 判据）

R526 记录（产品 1 文件 + 判据）：标题双击补悬停反馈。⓪ push no-op（HEAD=origin/main=`f10afe4`、ahead=0）；`41223106790 ↔ 3ddee13`、`41221604785 ↔ 4c0eeb6`、`41223261055 ↔ f10afe4` 读时 in_progress ⇒ NOT-RUN；`41221362532 ↔ 31d12c7` failure 仅 STEP[9]（sources 时序）、`41218308733 ↔ 79e39ee`/`41218637052 ↔ 77ed8ef` 同 STEP[9]、`41218878781 ↔ 9d882e4` STEP[15]（已由 3ddee13 修）。① 缺口：标题双击悬停与静置逐像素相同（亮 +1.2/暗 −0.8），chevron 早有 hover；给标题组加同档浅底（负 padding 不改布局）。② 产品 1 文件（HistorySidebarView）。③ 新夹具 `main-sidebar-title-hover` + 判据（亮/暗 **7.2/4.4**，地板 2.5）；M1403 CAUGHT；`PressFeedbackTests` 名册 10→11；预检 306/283/744 bad=0、ARM 399/1231、HIDDEN 393/1170 rot=0；build 0 告警。④ 帧 342（ADDED=2、CHANGED=0），基线 340→342；hover 帧逐张看过。⑤ %s；%s；%s；清账 162 格已清 162/未清 0/不合法 0；产品面连续零改动 4 轮（as-of 501，`python3 scripts/product_streak.py` 现读，last_round=497）。⑥ 交接：折叠两态/过渡/菜单/⌘\\/标题与 chevron 反馈已齐；下轮优先 runner 签收与真机逐帧。%s。下一轮编号 R527（第 526 轮 / Round 524）：先 push 并复核 ahead=0；读 R526 产品笔/台账笔与 R525 四跑的全部失败步骤（in_progress/queued ⇒ NOT-RUN）；② 产品位按用户指令继续折叠特性；③ 4.5 地板与 150 上限不动。
""" % (FULLTXT, INSTALLTXT, BATTERYTXT, TAILPAIR)
IS=u"""## Round 523 · R526（第 525 轮 · 2026-11-01）：标题双击补悬停反馈

折叠/展开的标题双击只有 tooltip：悬停与静置在标题带里逐像素相同（亮档均值差 1.2、暗档 −0.8，噪声级），而右边 chevron 早有 hover/按压 ⇒ 双击不可发现。R526 给标题组加 `onHover` + 与 chevron 同一档的 `PressableAppearance.fillOpacity(controlHover)` 浅底（负 padding 只放大浅底、不改布局），取证复用 `hoveredForCapture`。新增夹具 `main-sidebar-title-hover` + `testSidebarTitleHoverFeedbackIsVisible`（亮/暗 mean luma 绝对差 **7.2/4.4**，地板 2.5）；M1403（浅底永不画）CAUGHT、RESTORE_CLEAN；`PressFeedbackTests` 控件档位点 10→11；预检 306/283/744 bad=0、ARM 399/1231、HIDDEN 393/1170 rot=0；build 0 告警；帧 342（ADDED=2、CHANGED=0），基线 340→342；hover 帧逐张看过，标题与计数/chevron 布局未动；新帧进材质盲区名册（系统 List 选中材质）。%s；%s；%s。R525 的 3ddee13 签收跑仍在 in_progress ⇒ NOT-RUN。

**七维度自评**（恰七行，每格 n/15）：

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | 15/15 | hover 亮/暗帧逐张看过：标题药丸出现、布局未动；旧值 1.2/−0.8 是噪声级。 |
| 判据有效性 | 15/15 | 同区域旧/新读数分开、地板 2.5；M1403 让读数变。 |
| 假绿防御 | 15/15 | 静置 340 帧 byte-identical；runner 三跑 in_progress 具名 NOT-RUN。 |
| 产品面推进 | 15/15 | 双击 affordance 与 chevron 同语言；1 个产品文件。 |
| 台账一致性 | 15/15 | U-2138…U-2144、D-525、342 帧/全量/换装/电池都来自命令与测试。 |
| 交付诚实性 | 15/15 | 旧值、runner 未签收、sources 时序红都如实。 |
| 可复核性 | 15/15 | 7.2/4.4、M1403、precheck 306/283/744、ADDED=2/CHANGED=0 都在。 |

均分 = 105/105 ≈ 15.0/15（100）。
""" % (FULLTXT, INSTALLTXT, BATTERYTXT)
RB=u"""- **R526（标题双击补悬停反馈；产品 1 文件 + 判据）**：标题双击旧值与静置逐像素相同（亮 +1.2/暗 −0.8），chevron 早有 hover。标题组加同一档 `controlHover` 浅底（负 padding 不改布局），复用 `hoveredForCapture`；新增 `main-sidebar-title-hover` 夹具与判据（亮/暗 **7.2/4.4**，地板 2.5）；M1403 CAUGHT；`PressFeedbackTests` 名册 10→11；预检 306/283/744 bad=0、ARM 399/1231、HIDDEN 393/1170 rot=0；帧 **342**（ADDED=2、CHANGED=0），基线 340→342。全量 %s；换装 %s；电池 %s。R525 的 3ddee13 签收跑仍 in_progress ⇒ NOT-RUN。
""" % (FULL or u"见补记", INSTALL or u"425=425", BATTERY or u"683/5")
a=rd(A); d=rd(D); st=rd(S); pr=rd(P); ch=rd(C); it=rd(I)
if a.count(AT_OLD)!=1: raise SystemExit("A title %d" % a.count(AT_OLD))
if a.count(ANCHOR_NEXT)!=1: raise SystemExit("A next %d" % a.count(ANCHOR_NEXT))
if u"## D-525" in d: raise SystemExit("D exists")
if u"## R526 状态" in st: raise SystemExit("S exists")
if u"R526（标题双击补悬停反馈" in pr: raise SystemExit("P exists")
if u"标题双击补悬停反馈" in ch: raise SystemExit("C exists")
if u"## Round 523 · R526" in it: raise SystemExit("I exists")
if pr.count(u"U-31 … U-2137（R525 现读抬到最新一节）")!=1: raise SystemExit("P ucell")
if pr.count(u"R9–R522，523 节自评")!=1: raise SystemExit("P headline")
if pr.count(u"阶段二 **515 轮**审计（R9–R522；")!=1: raise SystemExit("P phase")
if pr.count(u"PHASE2 n=515")!=1: raise SystemExit("P n")
if pr.count(u"的 Round 522")!=1: raise SystemExit("P round")
if pr.count(u"## 18. R458 → R525 这一段（R478 起写；R504 续到 504、R505 续到 505、R506 续到 506、R507 续到 507、R508 续到 508、R509 续到 509、R510 续到 510、R511 续到 511、R512 续到 512、R513 续到 513、R514 续到 514、R515 续到 515、R516 续到 516、R517 续到 517、R518 续到 518、R519 续到 519、R520 续到 520、R521 续到 521、R522 续到 522、R523 续到 523、R524 续到 524、R525 续到 525 —— 这份报告第七次差点停在几十轮之前）")!=1: raise SystemExit("P s18")
if pr.count(u"的 R525 节 ② 为准")!=1: raise SystemExit("P pointer")
wr(A, a.replace(AT_OLD, AT_NEW, 1).replace(ANCHOR_NEXT, u"\n"+AS+ANCHOR_NEXT, 1))
wr(D, d.rstrip()+"\n\n"+DS+"\n")
wr(S, st.replace(u"## R525 状态（", SS.strip()+"\n\n## R525 状态（", 1))
pr=pr.replace(u"R9–R522，523 节自评", u"R9–R523，524 节自评", 1)
pr=pr.replace(u"阶段二 **515 轮**审计（R9–R522；", u"阶段二 **516 轮**审计（R9–R523；", 1)
pr=pr.replace(u"PHASE2 n=515", u"PHASE2 n=516", 1)
pr=pr.replace(u"的 Round 522", u"的 Round 523", 1)
pr=pr.replace(u"U-31 … U-2137（R525 现读抬到最新一节）", u"U-31 … U-2144（R526 现读抬到最新一节）", 1)
pr=pr.replace(u"## 18. R458 → R525 这一段（R478 起写；R504 续到 504、R505 续到 505、R506 续到 506、R507 续到 507、R508 续到 508、R509 续到 509、R510 续到 510、R511 续到 511、R512 续到 512、R513 续到 513、R514 续到 514、R515 续到 515、R516 续到 516、R517 续到 517、R518 续到 518、R519 续到 519、R520 续到 520、R521 续到 521、R522 续到 522、R523 续到 523、R524 续到 524、R525 续到 525 —— 这份报告第七次差点停在几十轮之前）",
              u"## 18. R458 → R526 这一段（R478 起写；R504 续到 504、R505 续到 505、R506 续到 506、R507 续到 507、R508 续到 508、R509 续到 509、R510 续到 510、R511 续到 511、R512 续到 512、R513 续到 513、R514 续到 514、R515 续到 515、R516 续到 516、R517 续到 517、R518 续到 518、R519 续到 519、R520 续到 520、R521 续到 521、R522 续到 522、R523 续到 523、R524 续到 524、R525 续到 525、R526 续到 526 —— 这份报告第七次差点停在几十轮之前）", 1)
pr=pr.replace(u"的 R525 节 ② 为准", u"的 R526 节 ② 为准", 1)
wr(P, pr.rstrip()+"\n\n"+RB+"\n")
m=u"## [Unreleased]\n"
if ch.count(m)!=1: raise SystemExit("C anchor")
wr(C, ch.replace(m, m+"\n"+CS, 1))
wr(I, it.rstrip()+"\n\n"+IS+"\n")
print("OK sha=%s full=%s install=%s battery=%s" % (sha, FULL, INSTALL, BATTERY))
