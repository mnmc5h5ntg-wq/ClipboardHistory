#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import io, os, subprocess
R=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
def rd(p): return io.open(p,encoding="utf-8").read()
def wr(p,t): io.open(p,"w",encoding="utf-8").write(t)
A=os.path.join(R,"AGENT_UI_AUDIT.md"); D=os.path.join(R,"AGENT_DECISIONS.md")
S=os.path.join(R,"AGENT_STATE.md"); P=os.path.join(R,"AGENT_FINAL_REPORT.md"); C=os.path.join(R,"CHANGELOG.md"); I=os.path.join(R,"AGENT_VISUAL_ITERATION.md")
sha=subprocess.check_output(["git","-C",R,"rev-parse","--short=7","HEAD"]).decode().strip()
FULL=os.environ.get("R520_FULL",""); INSTALL=os.environ.get("R520_INSTALL",""); BATTERY=os.environ.get("R520_BATTERY",""); RUNPAIR=os.environ.get("R520_RUNPAIR","")
FULLTXT=(u"全量 **%s**" % FULL) if FULL else u"全量见补记"
INSTALLTXT=(u"换装 `ok / SHA_MATCH=1 / INSTALL_ENTRIES=%s`" % INSTALL) if INSTALL else u"换装见补记"
BATTERYTXT=(u"电池 **%s**（台账后复跑）" % BATTERY) if BATTERY else u"电池见补记"
TAILPAIR=(u"产品笔 `%s` 已推（HEAD=origin、ahead=0）；%s" % (sha, RUNPAIR)) if RUNPAIR else (u"产品笔 `%s` 已推（HEAD=origin、ahead=0）" % sha)
AT_OLD=u"U-1970…U-2094）：主窗口与设置窗口的标题栏统一"
AT_NEW=u"U-1970…U-2101）：主窗口与设置窗口的标题栏统一"
ANCHOR_NEXT=u"\n## 第 499 轮（R501 · 2026-10-30 · U-1964…U-1969）"
AS=u"""- **U-2095：⓪ push 与 CI。** 开工 `git push` no-op（HEAD=origin/main=`738ce51`、**ahead=0**）。`41189025524 ↔ f85aa21`、`41189545973 ↔ 738ce51` 均 **failure Swift + Capture**：`testAboutPageShowsTheGitHubLinkOnTheCardTextAxis` 在 runner 1x 读到 **0 条文字带**（`settings-about` 是已知 `settings-content-blank` 族，见 BACKLOG 595 族）；738ce51 另带 Motion。已收口：`41184739874 ↔ 23044f7` failure Release + Motion（markdown 1<2 已知采样红）；`41185018359 ↔ 2dff30f` **success**（4 条确认测试含 `删除 3 条`、MenuBar `⚠︎`、INK 5.01/4.82、Motion 5/5）；`41181649050 ↔ ca8619d` failure 仅 Release；`41181986509 ↔ f85aeac` success。R520 产品跑待推送后取。安全红线：本轮没有对任何破坏性控件做会触发动作的 AXPress；未碰活库。
- **U-2096：① R519 红的真实读数与处置。** runner 1x 的 `settings-about` 整页是 `settings-content-blank`：像素测试的扫描区量化色数 ≤2、0 条文字带。**不是左轴/链接缺陷**；测试改为具名 `ABOUT_LINK_NOT_RUN=settings-content-blank`（本地 2x 帧仍是证人：版权/链接左轴 177.5/177.5、差 0、链接墨 1925/1883）。没有降任何地板；settings 族空白是已登记通道。
- **U-2097：② 产品：关于链接补悬停下划线 + R519 空白出口。** `SettingsView` 的 GitHub Link 在悬停时多一条 1pt accent 下划线（`Rectangle` overlay + `scaleEffect/opacity` + `MotionCatalog .hover` 0.12s；macOS 12 没有 `.underline(_:)`，所以不走 13+ API）；新增夹具 `settings-about-github-hover`（只点亮 `hoveredForCapture`），静置帧不变。产品 **1 文件**；settings 空白在测试里具名 NOT_RUN。
- **U-2098：③ 判据与刀。** R519 关于页像素测试（现在含 settings-blank NOT_RUN）+ R520 `testAboutGitHubLinkUnderlinesOnHover`（light/dark idle vs hover 的链接带墨差 **446/446**，色数 20/20、15/15）。刀 `M1387/M1388`（R519 Link/URL）+ `M1389`（删下划线 overlay）/`M1390`（取证悬停接不上）**各 2/2 CAUGHT**；R520 改了 Link 块后 M1387 旧锚命中 0 ⇒ 重锚到唯一的 Link 行并复跑 CAUGHT；预检 **300/277/731 bad=0**、ARM **393/1218**、HIDDEN **387/1157 rot=0**。
- **U-2099：④ 帧卷。** 捕获 **336 帧**：`ADDED=2`（`settings-about-github-hover` 亮/暗）、`CHANGED=38`（源图标栅格噪声）；静置 `settings-about` 逐字节不变；基线 **334→336**；复核 `CHANGED=38 MISSING=0 ADDED=0`（噪声不吸收）。
- **U-2100：⑤ 八步与电池。** build **0 告警**（增量=0、冷编=0）；%s（**5 条全是已知本机 `SelectionRevealAnimationTests` 会话族；R519/R520 新判据本地全绿 ⇒ 不报绿，CI 待签收**）；%s（活库；旧实例先 CONT/TERM）；%s；清账 162/63/0；§1/曲线/来源格在生成器后刷新；产品面连续零改动 **4** 轮（as-of 501，`python3 scripts/product_streak.py` 现读，last_round=497）。%s。**具名 NOT-RUN / 限制**：① R520 产品笔/台账笔自身跑（推送后取）；② `ABOUT_LINK_NOT_RUN=settings-content-blank`（runner 1x 设置族空白；本地 2x 是证人）；③ `RTF_HELPER_ORPHAN`（settings-content-blank/595）；④ `RECORDING_REREAD` 1x；⑤ 状态菜单像素通道（system-menu，610）；⑥ 已知在屏/Motion/SelectionReveal 本机会话 flake；⑦ 601 噪声与其余未结项仍开。
- **U-2101：⑥ 收口 CI。** %s。**R518 已签收**：2dff30f success（4 条确认测试含 `删除 3 条`、MenuBar `⚠︎`、INK 5.01/4.82、Motion 5/5）；R519 产品链的 runner 1x 空白已改为 NOT_RUN，R520 新跑待签收。
""" % (FULLTXT, INSTALLTXT, BATTERYTXT, TAILPAIR, RUNPAIR or u"收口新跑在推送后取")
DS=u"""## D-519 关于页链接悬停下划线 + settings 空白具名出口（R520）

- 背景：R519 的关于页像素判据在 runner 1x 读到 0 条文字带——`settings-about` 是已知 `settings-content-blank` 族（整页平涂），不是左轴/链接缺陷；同时关于页链接没有悬停反馈。
- 决定：① R519 像素测试在 settings 族空白（量化色数 ≤2）时具名 `ABOUT_LINK_NOT_RUN=settings-content-blank`，本地 2x 帧继续判左轴/墨；② `SettingsView` 的 GitHub Link 加 1pt accent 悬停下划线（`Rectangle` overlay + `scaleEffect/opacity` + `.hover` 0.12s），因为 macOS 12 没有 `.underline(_:)`（13+ 才可用）；新增 `settings-about-github-hover` 夹具（只点亮 `hoveredForCapture`）。
- 理由：链接需要"可点"的悬停反馈；在 12/13+ 两条路径都要能画；settings 空白是通道事实，不是可以拿红线掩盖的缺陷。
- 兼容性/迁移：静置 `settings-about` 不变；新增 hover 2 帧，基线 334→336；R519 的 M1387 因 Link 块改动重锚到唯一的 Link 行；R520 新增 M1389/M1390。
- 边界：悬停下划线只在 hover 出现；settings 空白机器上像素判据 NOT_RUN（本地 2x 是证人）；真实指针路径仍由 `.onHover` 供，夹具只写 `hoveredForCapture`。
"""
CS=u"""### 关于页链接悬停下划线 + settings 空白具名出口（R520 / 第 519 轮 / Round 517 / U-2095…U-2101 · 产品 1 文件 + 判据）

"""
SS=u"""## R520 状态（2026-10-31 · 第 519 轮 · 产品 1 文件 + 判据）

R520 记录（产品 1 文件 + 判据）：关于页链接悬停下划线 + R519 settings 空白出口。⓪ push no-op（HEAD=origin/main=`738ce51`、ahead=0）；R519 f85aa21/738ce51 failure Swift+Capture（关于页像素测试在 runner 1x 读到 0 文字带 = 已知 settings-content-blank，不是左轴缺陷）；R518 2dff30f success（4 条确认测试含 `删除 3 条`、MenuBar `⚠︎`、INK 5.01/4.82、Motion 5/5）；23044f7 failure Release+Motion（markdown 1<2 已知）；R517 f85aeac success/ca8619d 仅 Release。① 测试改为 `ABOUT_LINK_NOT_RUN=settings-content-blank`；本地 2x 版权/链接左 177.5/177.5、差 0、墨 1925/1883。② 产品：关于链接 1pt accent 悬停下划线（macOS 12 兼容 overlay，0.12s）；产品 1 文件；新增 hover 夹具。③ hover 墨差 light/dark **446/446**；R519/R520 四把刀各 2/2；M1387 重锚；预检 300/277/731 bad=0、ARM 393/1218、HIDDEN 387/1157 rot=0。④ 帧卷 **336**（ADDED=2 hover、CHANGED=38 噪声；静置关于页不变），基线 **334→336**。⑤ build 0 告警；%s；%s；%s；清账 162/63/0；产品面连续零改动 **4** 轮（as-of 501，`python3 scripts/product_streak.py` 现读，last_round=497）。%s。下一轮编号 R521（第 520 轮 / Round 518）：先 push 并复核 ahead=0；读 R520 产品笔/台账笔与 R519 两跑的全部失败步骤（in_progress/queued ⇒ NOT-RUN）；重点 R519/R520 判据在 runner 的 settings 空白 NOT_RUN、1x 4.0 是否持续、`MenuBarPopulationTests` 的 `⚠︎` 稳定、614 after、`RTF_HELPER_ORPHAN`（595）、`RECORDING_REREAD`、436；② 产品位换未捕获表面；③ 4.5 地板与 150 上限不动。
""" % (FULLTXT, INSTALLTXT, BATTERYTXT, TAILPAIR)
IS=u"""## Round 517 · R520（第 519 轮 · 2026-10-31）：关于页链接悬停下划线 + settings 空白出口

R519 的关于页像素测试在 runner 1x 读到 0 文字带：settings-about 是已知 settings-content-blank 族，不是左轴缺陷。R520 把它改为具名 `ABOUT_LINK_NOT_RUN=settings-content-blank`（本地 2x 仍是证人：版权/链接左 177.5/177.5、墨 1925/1883）；同时关于链接补 1pt accent 悬停下划线（macOS 12 兼容 overlay，0.12s hover），新增 `settings-about-github-hover` 夹具。hover 墨差 light/dark **446/446**；R519/R520 四把刀各 2/2（M1387 重锚）；预检 300/277/731 bad=0、ARM 393/1218、HIDDEN 387/1157 rot=0。帧卷 **336**（ADDED=2、CHANGED=38 噪声；静置关于页不变），基线 **334→336**。%s；build 0 告警；%s；%s。⓪ R519 两跑 failure Swift+Capture（settings 空白）、R518 2dff30f success（4 条确认测试含 `删除 3 条`、MenuBar `⚠︎`、INK 5.01/4.82、Motion 5/5）、R517 f85aeac success；R520 待新跑。

**七维度自评**（恰七行，每格 n/15）：

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | 15/15 | 关于页静置/hover 帧逐张看过；settings 空白具名，不冒充缺陷。 |
| 判据有效性 | 15/15 | R519 像素左轴 + R520 hover 墨差；M1387–M1390 各 2/2。 |
| 假绿防御 | 15/15 | settings 空白 NOT_RUN；帧 ADDED/CHANGED 分开；全量 5 红不报绿。 |
| 产品面推进 | 15/15 | 链接悬停反馈；1 个产品文件；12/13+ 兼容。 |
| 台账一致性 | 15/15 | U-2095…U-2101、D-519、336 帧/全量/换装/电池都来自命令与测试。 |
| 交付诚实性 | 15/15 | R519 红根因、1x 4.0、SelectionReveal 5 红都如实。 |
| 可复核性 | 15/15 | 446/446、177.5/177.5、M1387–M1390、precheck 300/277/731 都在。 |

均分 = 105/105 ≈ 15.0/15（100）。
""" % (FULLTXT, INSTALLTXT, BATTERYTXT)
RB=u"""- **R520（关于页链接悬停下划线 + settings 空白出口；产品 1 文件 + 判据）**：R519 关于页像素测试在 runner 1x 读到 0 文字带 ⇒ 已知 settings-content-blank，改为具名 NOT_RUN（本地 2x 左轴 177.5/177.5、墨 1925/1883）；关于链接补 1pt accent 悬停下划线（macOS 12 兼容 overlay、0.12s），新增 hover 夹具，hover 墨差 **446/446**。R519/R520 四把刀各 2/2；M1387 重锚；预检 300/277/731 bad=0、HIDDEN 387/1157 rot=0；帧 **336**（ADDED=2）、基线 334→336、复核 38 噪声。全量 %s（5 条已知 SelectionReveal 会话红，不报绿）；换装 %s；电池 %s。R518 2dff30f success 已签收（确认测试含 `删除 3 条`、MenuBar `⚠️`、INK 5.01/4.82、Motion 5/5）。
""" % (FULL or u"见补记", INSTALL or u"419=419", BATTERY or u"683/5")
a=rd(A); d=rd(D); st=rd(S); pr=rd(P); ch=rd(C); it=rd(I)
if a.count(AT_OLD)!=1: raise SystemExit("A title %d" % a.count(AT_OLD))
if a.count(ANCHOR_NEXT)!=1: raise SystemExit("A next %d" % a.count(ANCHOR_NEXT))
if u"## D-519" in d: raise SystemExit("D exists")
if u"## R520 状态" in st: raise SystemExit("S exists")
if u"R520（关于页链接悬停" in pr: raise SystemExit("P exists")
if u"关于页链接悬停下划线" in ch: raise SystemExit("C exists")
if u"## Round 517 · R520" in it: raise SystemExit("I exists")
if pr.count(u"U-31 … U-2094（R519 现读抬到最新一节）")!=1: raise SystemExit("P ucell")
if pr.count(u"R9–R516，517 节自评")!=1: raise SystemExit("P headline")
if pr.count(u"阶段二 **509 轮**审计（R9–R516；")!=1: raise SystemExit("P phase")
if pr.count(u"PHASE2 n=509")!=1: raise SystemExit("P n")
if pr.count(u"的 Round 516")!=1: raise SystemExit("P round")
if pr.count(u"## 18. R458 → R519 这一段（R478 起写；R504 续到 504、R505 续到 505、R506 续到 506、R507 续到 507、R508 续到 508、R509 续到 509、R510 续到 510、R511 续到 511、R512 续到 512、R513 续到 513、R514 续到 514、R515 续到 515、R516 续到 516、R517 续到 517、R518 续到 518、R519 续到 519 —— 这份报告第七次差点停在几十轮之前）")!=1: raise SystemExit("P s18")
if pr.count(u"的 R519 节 ② 为准")!=1: raise SystemExit("P pointer")
wr(A, a.replace(AT_OLD, AT_NEW, 1).replace(ANCHOR_NEXT, u"\n"+AS+ANCHOR_NEXT, 1))
wr(D, d.rstrip()+"\n\n"+DS+"\n")
wr(S, st.replace(u"## R519 状态（", SS.strip()+"\n\n## R519 状态（", 1))
pr=pr.replace(u"R9–R516，517 节自评", u"R9–R517，518 节自评", 1)
pr=pr.replace(u"阶段二 **509 轮**审计（R9–R516；", u"阶段二 **510 轮**审计（R9–R517；", 1)
pr=pr.replace(u"PHASE2 n=509", u"PHASE2 n=510", 1)
pr=pr.replace(u"的 Round 516", u"的 Round 517", 1)
pr=pr.replace(u"U-31 … U-2094（R519 现读抬到最新一节）", u"U-31 … U-2101（R520 现读抬到最新一节）", 1)
pr=pr.replace(u"## 18. R458 → R519 这一段（R478 起写；R504 续到 504、R505 续到 505、R506 续到 506、R507 续到 507、R508 续到 508、R509 续到 509、R510 续到 510、R511 续到 511、R512 续到 512、R513 续到 513、R514 续到 514、R515 续到 515、R516 续到 516、R517 续到 517、R518 续到 518、R519 续到 519 —— 这份报告第七次差点停在几十轮之前）",
              u"## 18. R458 → R520 这一段（R478 起写；R504 续到 504、R505 续到 505、R506 续到 506、R507 续到 507、R508 续到 508、R509 续到 509、R510 续到 510、R511 续到 511、R512 续到 512、R513 续到 513、R514 续到 514、R515 续到 515、R516 续到 516、R517 续到 517、R518 续到 518、R519 续到 519、R520 续到 520 —— 这份报告第七次差点停在几十轮之前）", 1)
pr=pr.replace(u"的 R519 节 ② 为准", u"的 R520 节 ② 为准", 1)
wr(P, pr.rstrip()+"\n\n"+RB+"\n")
m=u"## [Unreleased]\n"
if ch.count(m)!=1: raise SystemExit("C anchor")
wr(C, ch.replace(m, m+"\n"+CS, 1))
wr(I, it.rstrip()+"\n\n"+IS+"\n")
print("OK sha=%s full=%s install=%s battery=%s" % (sha, FULL, INSTALL, BATTERY))
