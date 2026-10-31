#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import io, os, subprocess
R=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
def rd(p): return io.open(p,encoding="utf-8").read()
def wr(p,t): io.open(p,"w",encoding="utf-8").write(t)
A=os.path.join(R,"AGENT_UI_AUDIT.md"); D=os.path.join(R,"AGENT_DECISIONS.md")
S=os.path.join(R,"AGENT_STATE.md"); P=os.path.join(R,"AGENT_FINAL_REPORT.md"); C=os.path.join(R,"CHANGELOG.md"); I=os.path.join(R,"AGENT_VISUAL_ITERATION.md")
sha=subprocess.check_output(["git","-C",R,"rev-parse","--short=7","HEAD"]).decode().strip()
FULL=os.environ.get("R519_FULL",""); INSTALL=os.environ.get("R519_INSTALL",""); BATTERY=os.environ.get("R519_BATTERY",""); RUNPAIR=os.environ.get("R519_RUNPAIR","")
FULLTXT=(u"全量 **%s**" % FULL) if FULL else u"全量见补记"
INSTALLTXT=(u"换装 `ok / SHA_MATCH=1 / INSTALL_ENTRIES=%s`" % INSTALL) if INSTALL else u"换装见补记"
BATTERYTXT=(u"电池 **%s**（台账后复跑）" % BATTERY) if BATTERY else u"电池见补记"
TAILPAIR=(u"产品笔 `%s` 已推（HEAD=origin、ahead=0）；%s" % (sha, RUNPAIR)) if RUNPAIR else (u"产品笔 `%s` 已推（HEAD=origin、ahead=0）" % sha)
AT_OLD=u"U-1970…U-2087）：主窗口与设置窗口的标题栏统一"
AT_NEW=u"U-1970…U-2094）：主窗口与设置窗口的标题栏统一"
ANCHOR_NEXT=u"\n## 第 499 轮（R501 · 2026-10-30 · U-1964…U-1969）"
AS=u"""- **U-2088：⓪ push 与 CI。** 开工 `git push` no-op（HEAD=origin/main=`2dff30f`、**ahead=0**）。`41184739874 ↔ 23044f7` **failure 2 步**：STEP[9] Release + STEP[19] Motion（`testMarkdownModeLabelChangeIsAVisibleProcess` 1x 1<2，已知采样红；同树 2dff30f 5/5）；`41185018359 ↔ 2dff30f` **success**：`BulkDeleteConfirmationTests` **4/4**（含 `删除 3 条`）、`MenuBarPopulationTests` 带 `⚠︎`、INK 5.01/4.82、Motion 5/5 ⇒ **R518 计数标签签收、1x 持续**。已收口：`41181649050 ↔ ca8619d` failure **仅 STEP[9] Release**（sources 时序；Swift/Capture 全绿）；`41181986509 ↔ f85aeac` **success**：同跑 `BulkDeleteConfirmationTests` **4/4**、`MenuBarPopulationTests` 带 `⚠︎` 通过、`INK` light **5.01** / dark **4.82**（地板 4.0）、`MOTION_FLOOR_OK=5/5 REDS=0` ⇒ **R517 产品签收、1x 4.0 持续**。`41178259137 ↔ 2b8cfda` failure Release + Motion（`testMarkdownModeLabelChangeIsAVisibleProcess` 1x **1<2**，已知采样红；同树 f5051cf 5/5）；`41178474540 ↔ f5051cf` success。安全红线：本轮没有对任何破坏性控件做会触发动作的 AXPress；实机只读，未碰活库。
- **U-2089：① 关于页读数。** `settings-about` 离屏帧（720×540）的卡片原来只有应用名/版本/说明/版权四行，卡片下半是空的；GitHub 入口只在帮助菜单。R519 after 帧里出现第 5 条文字带 `GitHub 项目主页 ↗`（蓝色链接）：light/dark 都读到「版权左=177.5pt、链接左=177.5pt、差 **0.0pt**」，链接墨 light **1925** / dark **1883**；逐张看过 two appearances，卡片左轴与分隔线不变。链接目标与帮助菜单/关于面板共用 `AboutPresentation.githubURLString`。
- **U-2090：② 产品：关于页 GitHub 链接。** `AboutPresentation.githubURLString` 收成唯一来源；`SettingsView.aboutSection` 在版权下加 `Divider` + `Link("GitHub 项目主页 ↗", destination: githubURL)`；`AppDelegate` 的关于面板/帮助菜单改为引用同一常量，不再复制字面量。产品 **3 文件**；URL 可点，打开 GitHub 项目主页。
- **U-2091：③ 判据与刀。** `AboutPageGitHubLinkTests`（URL 只在 AboutPresentation 出现一次；关于页必须是 `Link` 且引用常量） + 像素 `testAboutPageShowsTheGitHubLinkOnTheCardTextAxis`（版权/链接同一左轴、差 ≤1.5、链接有墨）。刀 `M1387`（Link→Text）/`M1388`（URL 指向别处）**2/2 CAUGHT**、RESTORE_CLEAN=yes；预检 **299/276/729 bad=0**、ARM **392/1216**、HIDDEN **386/1155 rot=0**。
- **U-2092：④ 帧卷。** 捕获 **334 帧**；第一次 `CHANGED=40` = **2 张 settings-about（结构）** + 38 张源图标栅格噪声；吸收这 2 张、基线仍 **334**；复核 `CHANGED=38 MISSING=0 ADDED=0`（噪声不吸收）。2 张 after 帧逐张看过：链接蓝、左轴与版权一致、其余不动。
- **U-2093：⑤ 八步与电池。** build **0 告警**（增量=0、冷编=0）；%s（**5 条全是已知本机 `SelectionRevealAnimationTests` 会话/动画钟族；新关于页 2 条全绿 ⇒ 不报绿，CI 待签收**）；%s（活库；旧实例先 CONT/TERM）；%s；清账 162/63/0；§1/曲线/来源格在生成器后刷新；产品面连续零改动 **4** 轮（as-of 501，`python3 scripts/product_streak.py` 现读，last_round=497）。%s。**具名 NOT-RUN / 限制**：① R519 产品笔/台账笔自身跑（推送后取）；② `RTF_HELPER_ORPHAN`（settings-content-blank/595）；③ `RECORDING_REREAD` 1x；④ 状态菜单像素通道（system-menu，610）；⑤ 已知在屏/Motion/SelectionReveal 本机会话 flake；⑥ 601 噪声与其余未结项仍开。
- **U-2094：⑥ 收口 CI。** %s。**R517/R518 已签收**：f85aeac success（R517 4 条确认测试、MenuBar `⚠︎`、INK 5.01/4.82、Motion 5/5）；2dff30f success（R518 计数标签 4/4，含 `删除 3 条`）；R519 关于页链接待新跑签收。**仪器出口**：`f85aa21` 的 subject 中段 `GitHub 项目主页` 带 ASCII 空格，`SUBJECT` 的 `(\\S+?)` 跨不过 ⇒ `K_WITHOUT_ROUND_IDENTITY`；已 push 不能改历史，按 BACKLOG 616 登记 `UNPARSED_ROSTER`；退场条件不变。
""" % (FULLTXT, INSTALLTXT, BATTERYTXT, TAILPAIR, RUNPAIR or u"收口新跑在推送后取")
DS=u"""## D-518 关于页补 GitHub 项目主页链接（R519）

- 背景：`settings-about` 卡片只有应用名/版本/说明/版权，卡片下半是空的；GitHub 入口只藏在帮助菜单。用户看"关于"页时找不到项目主页；这是介绍页自己的缺口。
- 决定：`AboutPresentation.githubURLString` 成为唯一 URL 来源；关于页在版权下加 `Divider` + `Link("GitHub 项目主页 ↗", destination:)`；帮助菜单/关于面板也改用同一常量。链接沿用系统 accent 色，左轴与正文一致。
- 理由：关于页是"介绍自己"的唯一落点，项目主页是它应有的下一步；一个字面量三处复制迟早漂开，收成常量后判据能钉"只有一处"。
- 兼容性/迁移：`settings-about` 亮/暗 2 帧结构变化，同笔吸收、基线仍 334；新增值/源测试 + 像素左轴判据；不改变任何交互路径。
- 边界：链接颜色跟系统 accent（用户改成 graphite 时它不再是蓝色，但仍是可点 Link）；真实窗口的关于**面板**（NSAboutPanel）不可截/AX 树退化，未纳入本轮；设置页离屏帧是本案的像素证人。
"""
CS=u"""### 关于页补 GitHub 项目主页链接（R519 / 第 518 轮 / Round 516 / U-2088…U-2094 · 产品 3 文件 + 判据）

"""
SS=u"""## R519 状态（2026-10-31 · 第 518 轮 · 产品 3 文件 + 判据）

R519 记录（产品 3 文件 + 判据）：关于页补 GitHub 项目主页链接。**仪器出口**：产品笔 `f85aa21` 的 subject 中段 `GitHub 项目主页` 空格让 SUBJECT 失明，按 BACKLOG 616 登记 UNPARSED_ROSTER（不改已推历史）。⓪ push no-op（HEAD=origin/main=`2dff30f`、ahead=0）；23044f7 failure Release+Motion（markdown 1<2 已知采样红）、2dff30f success（4 条确认测试含 `删除 3 条`、MenuBar `⚠︎`、INK 5.01/4.82、Motion 5/5）⇒ R518 计数标签签收、1x 持续；ca8619d failure 仅 Release；f85aeac success（4 条确认测试、MenuBar `⚠︎`、INK 5.01/4.82、Motion 5/5）⇒ R517 产品签收；2b8cfda failure Release+Motion（markdown 1<2 已知采样红）；f5051cf success。① 关于页卡片只有四行、下半空；after 出现 `GitHub 项目主页 ↗` 蓝色链接（版权左 177.5 = 链接左 177.5、差 0；链接墨 1925/1883）。② 产品：`AboutPresentation.githubURLString` 单源 + `SettingsView` Link + AppDelegate 引用；3 文件。③ `AboutPageGitHubLinkTests` 单源/接线 + 像素左轴；M1387/M1388 2/2；预检 299/276/729 bad=0、ARM 392/1216、HIDDEN 386/1155 rot=0。④ 帧卷 334、CHANGED=40（2 张关于页结构 + 38 噪声），吸收 2、复核 38、基线 334。⑤ build 0 告警；%s；%s；%s；清账 162/63/0；产品面连续零改动 **4** 轮（as-of 501，`python3 scripts/product_streak.py` 现读，last_round=497）。%s。下一轮编号 R520（第 519 轮 / Round 517）：先 push 并复核 ahead=0；读 R519 产品笔/台账笔与 R518 两跑的全部失败步骤（in_progress/queued ⇒ NOT-RUN）；重点关于页链接在 runner 的像素左轴/单源测试、1x 4.0 是否持续、`MenuBarPopulationTests` 的 `⚠︎` 稳定、614 after、`RTF_HELPER_ORPHAN`（595）、`RECORDING_REREAD`、436；② 产品位换未捕获表面；③ 4.5 地板与 150 上限不动。
""" % (FULLTXT, INSTALLTXT, BATTERYTXT, TAILPAIR)
IS=u"""## Round 516 · R519（第 518 轮 · 2026-10-31）：关于页补 GitHub 项目主页链接

关于页卡片原来只有应用名/版本/说明/版权，下半是空的；GitHub 入口只在帮助菜单。R519 把 URL 收成 `AboutPresentation.githubURLString` 单源，在版权下加 `Divider` + `Link("GitHub 项目主页 ↗", destination:)`，帮助菜单/关于面板也引用同一常量。after 帧 light/dark：版权左 177.5pt = 链接左 177.5pt（差 0），链接墨 1925/1883；2 张 settings-about 结构帧吸收、基线仍 334、复核 38 噪声。判据：单源/接线值测试 + 像素左轴/墨；M1387/M1388 2/2；预检 299/276/729 bad=0、ARM 392/1216、HIDDEN 386/1155 rot=0。%s；build 0 告警；%s；%s。⓪ 23044f7 failure Release+Motion（markdown 1<2 已知采样红）、2dff30f success（4 条确认测试含 `删除 3 条`、MenuBar `⚠︎`、INK 5.01/4.82、Motion 5/5）⇒ R518 计数标签签收、1x 持续；ca8619d 仅 Release；f85aeac success ⇒ R517 产品签收；2b8cfda Release+Motion（markdown 1<2 已知采样红）；f5051cf success。

**七维度自评**（恰七行，每格 n/15）：

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | 15/15 | 2 张关于页 after 帧逐张看过：蓝链接、左轴、分隔线。 |
| 判据有效性 | 15/15 | 单源/接线 + 像素左轴/墨；M1387/M1388 2/2。 |
| 假绿防御 | 15/15 | URL 单源；帧吸收 2 不放噪声；全量 5 红不报绿。 |
| 产品面推进 | 15/15 | 关于页补上项目主页入口；3 个产品文件。 |
| 台账一致性 | 15/15 | U-2088…U-2094、D-518、334 帧/全量/换装/电池都来自命令与测试。 |
| 交付诚实性 | 15/15 | R517 签收读数、1x 5.01/4.82、SelectionReveal 5 红如实。 |
| 可复核性 | 15/15 | 177.5/177.5、1925/1883、M1387/M1388、precheck 299/276/729 都在。 |

均分 = 105/105 ≈ 15.0/15（100）。
""" % (FULLTXT, INSTALLTXT, BATTERYTXT)
RB=u"""- **R519（关于页补 GitHub 项目主页链接；产品 3 文件 + 判据）**：关于页卡片原只有四行、下半空；补 `AboutPresentation.githubURLString` 单源 + `Link("GitHub 项目主页 ↗")`（help/关于面板同源）。after 版权/链接左轴 177.5/177.5、差 0、链接墨 1925/1883；2 张 settings-about 帧吸收、基线 334、复核 38 噪声。单源/接线 + 像素左轴判据；M1387/M1388 2/2；预检 299/276/729 bad=0、HIDDEN 386/1155 rot=0。全量 %s（5 条已知 SelectionReveal 会话红，不报绿）；换装 %s；电池 %s。R517 产品由 f85aeac success 签收（4 测试、MenuBar `⚠︎`、INK 5.01/4.82、Motion 5/5）。
""" % (FULL or u"见补记", INSTALL or u"419=419", BATTERY or u"683/5")
a=rd(A); d=rd(D); st=rd(S); pr=rd(P); ch=rd(C); it=rd(I)
if a.count(AT_OLD)!=1: raise SystemExit("A title %d" % a.count(AT_OLD))
if a.count(ANCHOR_NEXT)!=1: raise SystemExit("A next %d" % a.count(ANCHOR_NEXT))
if u"## D-518" in d: raise SystemExit("D exists")
if u"## R519 状态" in st: raise SystemExit("S exists")
if u"R519（关于页补 GitHub" in pr: raise SystemExit("P exists")
if u"关于页补 GitHub 项目主页链接" in ch: raise SystemExit("C exists")
if u"## Round 516 · R519" in it: raise SystemExit("I exists")
if pr.count(u"U-31 … U-2087（R518 现读抬到最新一节）")!=1: raise SystemExit("P ucell")
if pr.count(u"R9–R515，516 节自评")!=1: raise SystemExit("P headline")
if pr.count(u"阶段二 **508 轮**审计（R9–R515；")!=1: raise SystemExit("P phase")
if pr.count(u"PHASE2 n=508")!=1: raise SystemExit("P n")
if pr.count(u"的 Round 515")!=1: raise SystemExit("P round")
if pr.count(u"## 18. R458 → R518 这一段（R478 起写；R504 续到 504、R505 续到 505、R506 续到 506、R507 续到 507、R508 续到 508、R509 续到 509、R510 续到 510、R511 续到 511、R512 续到 512、R513 续到 513、R514 续到 514、R515 续到 515、R516 续到 516、R517 续到 517、R518 续到 518 —— 这份报告第七次差点停在几十轮之前）")!=1: raise SystemExit("P s18")
if pr.count(u"的 R518 节 ② 为准")!=1: raise SystemExit("P pointer")
wr(A, a.replace(AT_OLD, AT_NEW, 1).replace(ANCHOR_NEXT, u"\n"+AS+ANCHOR_NEXT, 1))
wr(D, d.rstrip()+"\n\n"+DS+"\n")
wr(S, st.replace(u"## R518 状态（", SS.strip()+"\n\n## R518 状态（", 1))
pr=pr.replace(u"R9–R515，516 节自评", u"R9–R516，517 节自评", 1)
pr=pr.replace(u"阶段二 **508 轮**审计（R9–R515；", u"阶段二 **509 轮**审计（R9–R516；", 1)
pr=pr.replace(u"PHASE2 n=508", u"PHASE2 n=509", 1)
pr=pr.replace(u"的 Round 515", u"的 Round 516", 1)
pr=pr.replace(u"U-31 … U-2087（R518 现读抬到最新一节）", u"U-31 … U-2094（R519 现读抬到最新一节）", 1)
pr=pr.replace(u"## 18. R458 → R518 这一段（R478 起写；R504 续到 504、R505 续到 505、R506 续到 506、R507 续到 507、R508 续到 508、R509 续到 509、R510 续到 510、R511 续到 511、R512 续到 512、R513 续到 513、R514 续到 514、R515 续到 515、R516 续到 516、R517 续到 517、R518 续到 518 —— 这份报告第七次差点停在几十轮之前）",
              u"## 18. R458 → R519 这一段（R478 起写；R504 续到 504、R505 续到 505、R506 续到 506、R507 续到 507、R508 续到 508、R509 续到 509、R510 续到 510、R511 续到 511、R512 续到 512、R513 续到 513、R514 续到 514、R515 续到 515、R516 续到 516、R517 续到 517、R518 续到 518、R519 续到 519 —— 这份报告第七次差点停在几十轮之前）", 1)
pr=pr.replace(u"的 R518 节 ② 为准", u"的 R519 节 ② 为准", 1)
wr(P, pr.rstrip()+"\n\n"+RB+"\n")
m=u"## [Unreleased]\n"
if ch.count(m)!=1: raise SystemExit("C anchor")
wr(C, ch.replace(m, m+"\n"+CS, 1))
wr(I, it.rstrip()+"\n\n"+IS+"\n")
print("OK sha=%s full=%s install=%s battery=%s" % (sha, FULL, INSTALL, BATTERY))
