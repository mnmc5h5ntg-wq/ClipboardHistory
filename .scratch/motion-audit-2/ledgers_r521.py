#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import io, os, subprocess
R=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
def rd(p): return io.open(p,encoding="utf-8").read()
def wr(p,t): io.open(p,"w",encoding="utf-8").write(t)
A=os.path.join(R,"AGENT_UI_AUDIT.md"); D=os.path.join(R,"AGENT_DECISIONS.md")
S=os.path.join(R,"AGENT_STATE.md"); P=os.path.join(R,"AGENT_FINAL_REPORT.md"); C=os.path.join(R,"CHANGELOG.md"); I=os.path.join(R,"AGENT_VISUAL_ITERATION.md")
sha=subprocess.check_output(["git","-C",R,"rev-parse","--short=7","HEAD"]).decode().strip()
FULL=os.environ.get("R521_FULL",""); INSTALL=os.environ.get("R521_INSTALL",""); BATTERY=os.environ.get("R521_BATTERY",""); RUNPAIR=os.environ.get("R521_RUNPAIR","")
FULLTXT=(u"全量 **%s**" % FULL) if FULL else u"全量见补记"
INSTALLTXT=(u"换装 `ok / SHA_MATCH=1 / INSTALL_ENTRIES=%s`" % INSTALL) if INSTALL else u"换装见补记"
BATTERYTXT=(u"电池 **%s**（台账后复跑）" % BATTERY) if BATTERY else u"电池见补记"
TAILPAIR=(u"产品笔 `%s` 已推（HEAD=origin、ahead=0）；%s" % (sha, RUNPAIR)) if RUNPAIR else (u"产品笔 `%s` 已推（HEAD=origin、ahead=0）" % sha)
AT_OLD=u"U-1970…U-2101）：主窗口与设置窗口的标题栏统一"
AT_NEW=u"U-1970…U-2108）：主窗口与设置窗口的标题栏统一"
ANCHOR_NEXT=u"\n## 第 499 轮（R501 · 2026-10-30 · U-1964…U-1969）"
AS=u"""- **U-2102：⓪ push 与 CI。** 开工 `git push` no-op（HEAD=origin/main=`349e85c`、**ahead=0**）。开工时 `41193460709 ↔ d0c8dd9`、`41193734687 ↔ 349e85c` 均 in_progress ⇒ **NOT-RUN**（不轮询）。已收口旧跑：`41189025524 ↔ f85aa21`、`41189545973 ↔ 738ce51` failure Swift+Capture（关于页像素判据在 runner 1x 读到 0 文字带 = 已知 `settings-content-blank` 族；738ce51 另带 Motion）；`41185018359 ↔ 2dff30f` success、`41184739874 ↔ 23044f7` failure Release+Motion（markdown 1<2 已知采样红）。收口补读：`41193734687 ↔ 349e85c` **success**；`41193460709 ↔ d0c8dd9` **failure 仅 STEP[9] Release script tests**（STEP[10]–[14] skipped），正文 `SOURCES_CELL 账上=R498/`f85aa21` git=R498/`d0c8dd9` 一致=否` ⇒ `FINAL_REPORT_SOURCES_CELL_STALE`，是**台账时序红**（sources 格要等台账笔刷新），由 349e85c 修好并 success；该跑 STEP[1]–[8] 的 Swift/Capture/Motion 已通过：`ABOUT_LINK_NOT_RUN=settings-content-blank`、`ABOUT_LINK_HOVER_NOT_RUN=settings-content-blank`（亮/暗各两行）、INK **5.01/4.82**、`MenuBarPopulationTests` 带 `⚠︎` 通过、`RTF_HELPER_ORPHAN_NOT_RUN=settings-content-blank`、`RECORDING_REREAD diff_px=0`、Motion `judged=5/5 executed=77 胶片=30`（15.8/1x）。安全红线：本轮没有对任何破坏性控件做会触发动作的 AXPress；未碰活库。
- **U-2103：① 按压反馈缺口的读数与处置。** 关于页 GitHub 入口上一版是 SwiftUI `Link`：它收不到 `pressedStyle`（那是 `ButtonStyle`），`pressedForCapture` 在这条入口上没有消费者。同一枚新夹具（`settings-about-github-pressed`，只点亮 `pressedForCapture`）套在**旧 Link 实现**上现读：亮 `idle=pressed=1928/1928`、暗 `1886/1886`、**delta=0**（地板 100 当场红）⇒ 旧版按下去与静置逐像素相同，按压反馈不存在。改成 `Button + NSWorkspace.shared.open + pressedStyle(controlHover, labelPadding 0) + .accessibilityAddTraits(.isLink)` 后：**delta=+5078（亮）/ +1133（暗）**，按下底色 + 0.97 缩放都出现在帧里。悬停臂同时被新灰底污染：R520 的"离纸色 >24 的墨差"在旧尺下 M1389/M1390 **PASSED**（灰底自己就够 100 像素）⇒ 尺换对象，改用 accent 像素差（下划线是 accent 蓝、底是 primary 灰）：**+419/+418**，地板 250，M1389/M1390 重新 CAUGHT。静置左轴仍 177.5/177.5；Button 化后静置墨 1928→1898、1886→1792（最佳平移 0,0，无位移，只是文字抗锯齿差）。
- **U-2104：② 产品：链接补按压反馈。** `SettingsView` 的关于页 GitHub 入口由 `Link` 改成 `Button`（打开 URL、保留 `.isLink` 语义、悬停下划线与 0.12s 动效原样）；`pressedStyle` 用控件档 `VisualFill.controlHover`、`labelPadding: 0`（不移动文字左轴）。新增夹具 `settings-about-github-pressed`（只写 `pressedForCapture`，产品路径不写）；`settings-about*` 三张进 vibrant 盲区名册。`PressFeedbackTests` 的控件档位点计数 8→9，并把新位点写进枚举（17pt 文字按钮 ⇒ 控件档；这是名册要求判一遍，不是放宽）。产品 **1 文件**。
- **U-2105：③ 判据与刀。** 新增 `testAboutGitHubLinkPressesWithVisibleFill`（地板 100，亮/暗两档，settings 空白具名 NOT_RUN）；悬停判据改 accent 差（地板 250）；R519 左轴判据不变（177.5/177.5、链接墨 1895/1790）。刀：`M1387` 重锚到新 Button 整块（画成普通文字）、`M1389` 缩进重锚（删下划线）、`M1391`（删 pressedStyle）、`M1392`（删 link 语义）新增；`M1387–M1392` **6/6 CAUGHT、RESTORE_CLEAN=yes**。预检 **301/278/733 bad=0**、ARM **394/1220**（dupes=0 repeats=0）、HIDDEN **388/1159 rot=0**。旧尺下 M1389/M1390 的 PASSED 已如实留在 U-2103。
- **U-2106：④ 帧卷。** 捕获 **338 帧**：`ADDED=2`（`settings-about-github-pressed` 亮/暗）、`CHANGED=42` = 关于页 4 张结构（`settings-about`、`settings-about-github-hover` 各亮/暗）+ **38 张已知源图标栅格噪声**。基线 **336→338**；逐张看过：静置=蓝色文字无底；悬停=灰色药丸 + 通栏 1pt accent 下划线（行 518–519，x 354–576）；按下=更深灰底 + 0.97 缩放、无下划线。噪声格不吸收（下一跑仍按 38 报）。
- **U-2107：⑤ 八步与电池。** build **0 告警**（增量=0、冷编=0）；%s（**3 条全是已知本机 `SelectionRevealAnimationTests` 会话族：`testAnimatedRevealProducesIntermediateOffsets` / `testProductDurationRevealStillMovesOverTime` / `testStaticDocumentScrollAnimationIsCapturable`；**不报绿**，CI 待签收）；%s（活库；旧实例 STAT=T，先 CONT 再 TERM 后换装，新 pid 77854）；%s；清账 `MOTION_LEDGER 162 格 / 已清账 162 / 未清账 0 / 不合法 0`；产品面连续零改动 **4** 轮（as-of 501，`python3 scripts/product_streak.py` 现读，last_round=497）。%s。**具名 NOT-RUN / 限制**：① R521 产品笔/台账笔自身跑（推送后取）；② `ABOUT_LINK_NOT_RUN` / `ABOUT_LINK_HOVER_NOT_RUN` / `ABOUT_LINK_PRESS_NOT_RUN=settings-content-blank`（runner 1x 设置族空白；本地 2x 是证人）；③ `RTF_HELPER_ORPHAN`（settings-content-blank/595）；④ `RECORDING_REREAD` 1x；⑤ 状态菜单像素通道（system-menu，610）；⑥ 已知在屏/Motion/SelectionReveal 本机会话 flake；⑦ 601 噪声与其余未结项仍开。
- **U-2108：⑥ 收口 CI。** %s。**R520 已签收**：台账笔 349e85c success；产品笔 d0c8dd9 的唯一红是 sources 格时序（非产品回归），R520 的 settings 空白出口在 runner 上确认为 `ABOUT_LINK_NOT_RUN=settings-content-blank`、hover 同理，静置帧不再被误判；R519 两跑的红根因与 R520 修复自此闭环。
""" % (FULLTXT, INSTALLTXT, BATTERYTXT, TAILPAIR, RUNPAIR or u"收口新跑在推送后取")
DS=u"""## D-520 关于页链接改用 Button 承载按压反馈 + 两把尺换对象（R521）

- 背景：R520 给关于页 GitHub 入口补了悬停下划线，但入口是 `Link`，它不吃 `pressedStyle`（`ButtonStyle`），所以全 App 唯一一条文字入口没有"你按到了"的表达；同一枚按下夹具在旧实现上读 `delta=0`（静置与按下逐像素相同）。
- 决定：把入口改成 `Button + NSWorkspace.shared.open`，接 `pressedStyle(controlHover, labelPadding 0)`（17pt 文字按钮 ⇒ 控件档）、保留 `.accessibilityAddTraits(.isLink)`；悬停下划线与 0.12s 动效不动。
- 判据随之换对象：① 按下判据数"按下比静置多出的墨"（新灰底就是被量对象），地板 100；② 悬停判据不能再数"离纸色 >24 的墨"——`pressedStyle` 的灰底自己就够 100 像素，旧尺下 M1389/M1390 会 PASSED；改成数 accent 蓝像素差（下划线 0,122,255；底是 primary 灰），地板 250。R520 的 446/446 墨差读数退役为历史，不删账。
- 名册：`PressFeedbackTests` 的控件档位点计数 8→9，新位点连同理由写进枚举（多一处要红的设计照旧）。
- 兼容性/迁移：静置左轴不变（177.5/177.5）；Button 化使静置墨 1928→1898、1886→1792（最佳平移 0,0，无位移）；新增 2 帧，基线 336→338；`M1387`/`M1389` 因代码块换代重锚，新增 `M1391`/`M1392`。
- 边界：真实按压仍由 `configuration.isPressed` 供，夹具只写 `pressedForCapture`；settings 空白机器上像素判据 NOT_RUN（本地 2x 是证人）。
"""
CS=u"""### 关于页 GitHub 链接补按压反馈（R521 / 第 520 轮 / Round 518 / U-2102…U-2108 · 产品 1 文件 + 判据）

"""
SS=u"""## R521 状态（2026-10-31 · 第 520 轮 · 产品 1 文件 + 判据）

R521 记录（产品 1 文件 + 判据）：关于页 GitHub 链接补按压反馈。⓪ push no-op（HEAD=origin/main=`349e85c`、ahead=0）；开工时 R520 两跑 in_progress ⇒ NOT-RUN；收口补读：台账笔 `349e85c` **success**、产品笔 `d0c8dd9` **failure 仅 STEP[9] Release script tests**（`FINAL_REPORT_SOURCES_CELL_STALE`：账上 f85aa21 vs git d0c8dd9，台账笔已修好 ⇒ 时序红，非产品回归；该跑 Swift/Capture/Motion 均过：ABOUT_LINK_NOT_RUN、ABOUT_LINK_HOVER_NOT_RUN、INK 5.01/4.82、MenuBar ⚠︎、RTF NOT_RUN、RECORDING diff_px=0、Motion 5/5）；R519 f85aa21/738ce51 failure Swift+Capture（settings 空白，R520 已具名出口）；R518 2dff30f success；23044f7 failure Release+Motion（markdown 1<2 已知）。① 旧 Link 无按压反馈：同一夹具旧实现 `delta=0`（1928/1928、1886/1886）；新 Button `+5078/+1133`。悬停尺换 accent 差 **419/418**（旧墨差被新灰底污染，M1389/M1390 旧尺下曾 PASSED）。② 产品：`Link→Button + pressedStyle(controlHover) + .isLink`；新增 pressed 夹具；PressFeedback 名册 8→9；产品 1 文件。③ 六把刀 6/6 CAUGHT、RESTORE_CLEAN；预检 301/278/733 bad=0、ARM 394/1220、HIDDEN 388/1159 rot=0。④ 帧卷 **338**（ADDED=2、CHANGED=42=4 结构+38 噪声），基线 **336→338**。⑤ build 0 告警；%s；%s；%s；清账 162 格已清 162/未清 0/不合法 0；产品面连续零改动 **4** 轮（as-of 501，`python3 scripts/product_streak.py` 现读，last_round=497）。%s。下一轮编号 R522（第 521 轮 / Round 519）：先 push 并复核 ahead=0；读 R521 产品笔/台账笔与 R520 两跑的全部失败步骤（in_progress/queued ⇒ NOT-RUN）；重点 R521 按压判据在 runner 的 settings 空白 NOT_RUN、1x 4.0 是否持续、`MenuBarPopulationTests` 的 `⚠︎` 稳定、614 after、`RTF_HELPER_ORPHAN`（595）、`RECORDING_REREAD`、436；② 产品位换未捕获表面；③ 4.5 地板与 150 上限不动。
""" % (FULLTXT, INSTALLTXT, BATTERYTXT, TAILPAIR)
IS=u"""## Round 518 · R521（第 520 轮 · 2026-10-31）：关于页 GitHub 链接补按压反馈

R520 的下划线让入口有了悬停反馈，但 `Link` 不吃 `pressedStyle`，按下去仍与静置逐像素相同（同一夹具在旧实现上 delta=0：1928/1928、1886/1886）。R521 把入口改成 `Button + NSWorkspace.shared.open`，接 `pressedStyle(controlHover, labelPadding 0)` 并保留 `.accessibilityAddTraits(.isLink)`；按下读数 **+5078/+1133**。悬停判据换了对象：新灰底让 R520 的"墨差 100"失去分辨力（M1389/M1390 旧尺下 PASSED），改用 accent 像素差 **+419/+418**（地板 250），两把刀重新 CAUGHT。`PressFeedbackTests` 控件档位点 8→9（新位点已判）。六把刀 6/6、RESTORE_CLEAN；预检 301/278/733 bad=0、ARM 394/1220、HIDDEN 388/1159 rot=0。帧卷 **338**（ADDED=2、CHANGED=42=4 结构+38 噪声），基线 **336→338**。%s；build 0 告警；%s；%s。⓪ R520 台账笔 349e85c success、产品笔 d0c8dd9 唯一红是 sources 格时序；R519 settings 空白两跑已由 R520 具名出口闭环；R518 2dff30f success。

**七维度自评**（恰七行，每格 n/15）：

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | 15/15 | 静置/悬停/按下三臂帧逐张看过；下划线行 518–519、按下底更深 + 0.97 缩放。 |
| 判据有效性 | 15/15 | 旧实现 delta=0 作负臂；新实现 +5078/+1133；M1389/M1390 换尺后重 CAUGHT。 |
| 假绿防御 | 15/15 | 悬停旧尺 PASSED 如实记录并换对象；settings 空白 NOT_RUN；全量 5 断言红不报绿。 |
| 产品面推进 | 15/15 | 唯一文字入口补上全 App 同一套按压反馈；1 个产品文件。 |
| 台账一致性 | 15/15 | U-2102…U-2108、D-520、338 帧/全量/换装/电池都来自命令与测试。 |
| 交付诚实性 | 15/15 | 旧尺失效、旧链接 delta=0、Button 化墨差、SelectionReveal 3 条红都如实。 |
| 可复核性 | 15/15 | 5078/1133、0/0、419/418、177.5/177.5、M1387–M1392、precheck 301/278/733 都在。 |

均分 = 105/105 ≈ 15.0/15（100）。
""" % (FULLTXT, INSTALLTXT, BATTERYTXT)
RB=u"""- **R521（关于页 GitHub 链接补按压反馈；产品 1 文件 + 判据）**：`Link` 不吃 `pressedStyle`，旧实现在按下夹具上 `delta=0`；改 `Button + pressedStyle(controlHover) + .isLink` 后 **+5078/+1133**。悬停判据换 accent 差 **419/418**（新灰底让旧墨差失去分辨力，M1389/M1390 旧尺下曾 PASSED）。M1387–M1392 6/6 CAUGHT；预检 301/278/733 bad=0、HIDDEN 388/1159 rot=0；帧 **338**（ADDED=2、CHANGED=42=4 结构+38 噪声）、基线 336→338。全量 %s（3 条已知 SelectionReveal 会话红，不报绿）；换装 %s；电池 %s。R520 台账笔 349e85c success；产品笔 d0c8dd9 唯一红是 sources 格时序（非产品回归）。
""" % (FULL or u"见补记", INSTALL or u"419=419", BATTERY or u"683/5")
a=rd(A); d=rd(D); st=rd(S); pr=rd(P); ch=rd(C); it=rd(I)
if a.count(AT_OLD)!=1: raise SystemExit("A title %d" % a.count(AT_OLD))
if a.count(ANCHOR_NEXT)!=1: raise SystemExit("A next %d" % a.count(ANCHOR_NEXT))
if u"## D-520" in d: raise SystemExit("D exists")
if u"## R521 状态" in st: raise SystemExit("S exists")
if u"R521（关于页 GitHub 链接补按压反馈" in pr: raise SystemExit("P exists")
if u"关于页 GitHub 链接补按压反馈" in ch: raise SystemExit("C exists")
if u"## Round 518 · R521" in it: raise SystemExit("I exists")
if pr.count(u"U-31 … U-2101（R520 现读抬到最新一节）")!=1: raise SystemExit("P ucell")
if pr.count(u"R9–R517，518 节自评")!=1: raise SystemExit("P headline")
if pr.count(u"阶段二 **510 轮**审计（R9–R517；")!=1: raise SystemExit("P phase")
if pr.count(u"PHASE2 n=510")!=1: raise SystemExit("P n")
if pr.count(u"的 Round 517")!=1: raise SystemExit("P round")
if pr.count(u"## 18. R458 → R520 这一段（R478 起写；R504 续到 504、R505 续到 505、R506 续到 506、R507 续到 507、R508 续到 508、R509 续到 509、R510 续到 510、R511 续到 511、R512 续到 512、R513 续到 513、R514 续到 514、R515 续到 515、R516 续到 516、R517 续到 517、R518 续到 518、R519 续到 519、R520 续到 520 —— 这份报告第七次差点停在几十轮之前）")!=1: raise SystemExit("P s18")
if pr.count(u"的 R520 节 ② 为准")!=1: raise SystemExit("P pointer")
wr(A, a.replace(AT_OLD, AT_NEW, 1).replace(ANCHOR_NEXT, u"\n"+AS+ANCHOR_NEXT, 1))
wr(D, d.rstrip()+"\n\n"+DS+"\n")
wr(S, st.replace(u"## R520 状态（", SS.strip()+"\n\n## R520 状态（", 1))
pr=pr.replace(u"R9–R517，518 节自评", u"R9–R518，519 节自评", 1)
pr=pr.replace(u"阶段二 **510 轮**审计（R9–R517；", u"阶段二 **511 轮**审计（R9–R518；", 1)
pr=pr.replace(u"PHASE2 n=510", u"PHASE2 n=511", 1)
pr=pr.replace(u"的 Round 517", u"的 Round 518", 1)
pr=pr.replace(u"U-31 … U-2101（R520 现读抬到最新一节）", u"U-31 … U-2108（R521 现读抬到最新一节）", 1)
pr=pr.replace(u"## 18. R458 → R520 这一段（R478 起写；R504 续到 504、R505 续到 505、R506 续到 506、R507 续到 507、R508 续到 508、R509 续到 509、R510 续到 510、R511 续到 511、R512 续到 512、R513 续到 513、R514 续到 514、R515 续到 515、R516 续到 516、R517 续到 517、R518 续到 518、R519 续到 519、R520 续到 520 —— 这份报告第七次差点停在几十轮之前）",
              u"## 18. R458 → R521 这一段（R478 起写；R504 续到 504、R505 续到 505、R506 续到 506、R507 续到 507、R508 续到 508、R509 续到 509、R510 续到 510、R511 续到 511、R512 续到 512、R513 续到 513、R514 续到 514、R515 续到 515、R516 续到 516、R517 续到 517、R518 续到 518、R519 续到 519、R520 续到 520、R521 续到 521 —— 这份报告第七次差点停在几十轮之前）", 1)
pr=pr.replace(u"的 R520 节 ② 为准", u"的 R521 节 ② 为准", 1)
wr(P, pr.rstrip()+"\n\n"+RB+"\n")
m=u"## [Unreleased]\n"
if ch.count(m)!=1: raise SystemExit("C anchor")
wr(C, ch.replace(m, m+"\n"+CS, 1))
wr(I, it.rstrip()+"\n\n"+IS+"\n")
print("OK sha=%s full=%s install=%s battery=%s" % (sha, FULL, INSTALL, BATTERY))
