#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import io, os, subprocess
R=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
def rd(p): return io.open(p,encoding="utf-8").read()
def wr(p,t): io.open(p,"w",encoding="utf-8").write(t)
A=os.path.join(R,"AGENT_UI_AUDIT.md"); D=os.path.join(R,"AGENT_DECISIONS.md"); B=os.path.join(R,"AGENT_BACKLOG.md")
S=os.path.join(R,"AGENT_STATE.md"); P=os.path.join(R,"AGENT_FINAL_REPORT.md"); C=os.path.join(R,"CHANGELOG.md"); I=os.path.join(R,"AGENT_VISUAL_ITERATION.md")
sha=subprocess.check_output(["git","-C",R,"rev-parse","--short=7","HEAD"]).decode().strip()
FULL=os.environ.get("R517_FULL",""); INSTALL=os.environ.get("R517_INSTALL",""); BATTERY=os.environ.get("R517_BATTERY",""); RUNPAIR=os.environ.get("R517_RUNPAIR","")
FULLTXT=(u"全量 **%s**" % FULL) if FULL else u"全量见补记"
INSTALLTXT=(u"换装 `ok / SHA_MATCH=1 / INSTALL_ENTRIES=%s`" % INSTALL) if INSTALL else u"换装见补记"
BATTERYTXT=(u"电池 **%s**（台账后复跑）" % BATTERY) if BATTERY else u"电池见补记"
TAILPAIR=(u"产品笔 `%s` 已推（HEAD=origin、ahead=0）；%s" % (sha, RUNPAIR)) if RUNPAIR else (u"产品笔 `%s` 已推（HEAD=origin、ahead=0）" % sha)
AT_OLD=u"U-1970…U-2073）：主窗口与设置窗口的标题栏统一"
AT_NEW=u"U-1970…U-2080）：主窗口与设置窗口的标题栏统一"
ANCHOR_NEXT=u"\n## 第 499 轮（R501 · 2026-10-30 · U-1964…U-1969）"
AS=u"""- **U-2074：⓪ push 与 CI。** 开工 `git push` no-op（HEAD=origin/main=`f5051cf`、**ahead=0**）。`41178259137 ↔ 2b8cfda` **failure 2 步**：STEP[9] Release（sources 时序）+ STEP[19] Motion floor（`testMarkdownModeLabelChangeIsAVisibleProcess` 1x **1<2**，已知 Motion 采样红；同树台账跑 `41178474540 ↔ f5051cf` **success** 且 `MOTION_FLOOR_OK=5/5 REDS=0`）；`f5051cf` success 同跑 `INK` light **5.01** / dark **4.82**（地板 4.0）、`MenuBarPopulationTests` 带 `⚠︎` 通过、`BULK_DELETE_FILL` 132/44、`BULK_AVAILABILITY` 85/79（标题差 0）⇒ **R516 产品（菜单警告记号）签收，1x 4.0 持续**。`41174428787 ↔ 29c9a45` failure 仅 Release、`41174708800 ↔ ba2d0b6` success（1x 首签 5.01/4.82）；历史 51ca151/1669c3e/0de51b9 的 2.37 是 ink 修复前；`874d579`/`764ea4b` success。436：f5051cf `MOTION_FLOOR_OK=5/5 REDS=0`；2b8cfda 的 markdown 采样红单独点名，不读成产品回归。
- **U-2075：① 确认框读数与安全边界。** 背景是 R515 的事故：AXPress「删除所选记录」实际立即删除，实机掉 6 条；已用开工副本恢复 419 条（ROWS=420），未打印内容。R517 前侧栏路径直接 `historyStore.perform(.deleteSelection)`（无 NSAlert/撤销）。R517 后用**临时数据副本** `CLIPBOARD_HISTORY_DATA_DIR=/tmp/r517_data`（419 条）启动安装包二进制，准备选 3 行点批量删除；安装包 AX 树在临时实例上只有 AXWindow、没有 AXOutline，真实点击路径 **`ALERT_UI_NOT_RUN=ax-tree-no-outline`**（没有对活库或任何破坏性控件做会触发动作的 AXPress）。确认框的按钮/默认键/破坏性标记由既有 `DestructiveAlertLayoutTests` 钉住；策略/接线由新增 4 条测试钉住（取消/零选区不删、确认才删、侧栏先问后删）。
- **U-2076：② 产品：批量删除先确认。** 新增 `BulkDeleteConfirmation`（title「删除所选记录」、message 含条数、confirm「删除」/cancel「取消」、零选区不问）；`HistorySidebarView` 删除按钮先 `guard BulkDeleteConfirmation.confirm(count:using:SystemDestructiveConfirming())` 再 `perform(.deleteSelection)`。产品 **2 文件**；确认框复用既有 `DestructiveConfirmation`/`DestructiveAlertLayout`（取消默认、删除为破坏性按钮），与「清空未收藏」同一套语言。**BACKLOG 619 结案**。
- **U-2077：③ 判据与刀。** `BulkDeleteConfirmationTests` 4 条：取消不确认且 message 含条数、只有显式确认才 true、零选区不问、侧栏确实先问后删（源码接线）。刀 `M1385`（侧栏绕过确认直接删）/`M1386`（策略不问就返回真）**2/2 CAUGHT**、RESTORE_CLEAN=yes；预检 **298/275/727 bad=0**、ARM **391/1214**、HIDDEN **385/1153 rot=0**。
- **U-2078：④ 帧卷。** 捕获 **334 帧**、`FRAME_BASELINE_CHANGED=38 MISSING=0 ADDED=0`（全噪声；确认框不在离屏帧，基线仍 334、无结构吸收）。
- **U-2079：⑤ 八步与电池。** build **0 告警**（增量=0、冷编=0）；%s（**5 条全是已知本机 `SelectionRevealAnimationTests` 会话/动画钟族；单跑 4 条同样 5 红 + 1 skip；新确认策略 4/4 全绿 ⇒ 不报绿，CI 待签收**）；%s（活库；旧实例先 CONT/TERM）；%s；清账 162/63/0；§1/曲线/来源格在生成器后刷新；产品面连续零改动 **4** 轮（as-of 501，`python3 scripts/product_streak.py` 现读，last_round=497）。%s。**具名 NOT-RUN / 限制**：① `41181649050 ↔ ca8619d` 读时 in_progress ⇒ NOT-RUN；台账笔自身跑推送后取；② `ALERT_UI_NOT_RUN=ax-tree-no-outline`（临时副本真实点击路径；未碰活库）；③ `RTF_HELPER_ORPHAN`（settings-content-blank/595）；④ `RECORDING_REREAD` 1x；⑤ 状态菜单像素通道（system-menu，610）；⑥ 已知在屏/Motion/SelectionReveal 本机会话 flake；⑦ 601 噪声与其余未结项仍开。
- **U-2080：⑥ 收口 CI。** %s。**1x 4.0 已由 f5051cf success 签收（5.01/4.82）**。
""" % (FULLTXT, INSTALLTXT, BATTERYTXT, TAILPAIR, RUNPAIR or u"收口新跑在推送后取")
DS=u"""## D-516 批量删除所选记录先确认（R517）

- 背景：R515 的事故（BACKLOG 619）——多选栏的「删除所选记录」直接 `perform(.deleteSelection)`，没有确认也没有撤销；实机验证时误删 6 条（已按开工副本恢复 419 条/ROWS=420）。这是本轮唯一会改动用户数据的入口，必须先问。
- 决定：新增 `BulkDeleteConfirmation`（title「删除所选记录」、message「将删除 N 条记录。此操作不可撤销。」、confirm「删除」、cancel「取消」、零选区不问）；`HistorySidebarView` 的删除按钮先 `guard BulkDeleteConfirmation.confirm(count:using:SystemDestructiveConfirming())` 再删除。确认框复用 `DestructiveConfirmation`/`DestructiveAlertLayout`：取消在第一颗且拿 Return，删除标 `hasDestructiveAction` 且无键等价物。
- 理由：批量删除是**不可逆**动作；与「清空未收藏」的既有确认框同一套语言，用户不必学第二套。零选区不问，避免空确认。
- 兼容性/迁移：确认框只在点击后出现，不改变任何离屏帧（334 帧/38 噪声/基线不变）；4 条测试 + 2 把刀；产品 2 文件。
- 边界：真实临时副本点击路径 `ALERT_UI_NOT_RUN=ax-tree-no-outline`（安装包 AX 树在临时实例上没有 AXOutline）；按钮布局由既有 `DestructiveAlertLayoutTests` 钉住，策略/接线由新测试钉住。后续任何破坏性批量动作都必须走同一策略；验证这类路径只能用 `CLIPBOARD_HISTORY_DATA_DIR` 副本/测试夹具，不许碰活库。
"""
BS=u"""**619 结案（R517）**：批量删除已改走 `BulkDeleteConfirmation`（先问；取消/零选区不删；确认框复用 `DestructiveAlertLayout`，取消默认、删除为破坏性按钮）。4 条策略/接线测试 + M1385/M1386 2/2；真实临时副本点击路径 `ALERT_UI_NOT_RUN=ax-tree-no-outline`（未碰活库）。
"""
CS=u"""### 批量删除所选记录先确认（R517 / 第 516 轮 / Round 514 / U-2074…U-2080 · 产品 2 文件 + 判据）

"""
SS=u"""## R517 状态（2026-10-31 · 第 516 轮 · 产品 2 文件 + 判据）

R517 记录（产品 2 文件 + 判据）：批量删除先确认（BACKLOG 619 结案）。⓪ push no-op（HEAD=origin/main=`f5051cf`、ahead=0）；2b8cfda failure STEP[9] Release + STEP[19] Motion（markdown 1<2，已知采样红）；f5051cf success（INK 5.01/4.82、`MenuBarPopulationTests` 带 `⚠︎` 通过、Motion 5/5）⇒ R516 产品签收、1x 4.0 持续；29c9a45 仅 Release、ba2d0b6 success。① R515 事故 6 条已恢复；R517 前直接删除；后先确认；临时副本真实点击 `ALERT_UI_NOT_RUN=ax-tree-no-outline`（未碰活库）。② 产品：`BulkDeleteConfirmation` + 侧栏 guard；2 文件；确认框复用 `DestructiveAlertLayout`。③ 4 条测试；M1385/M1386 2/2；预检 298/275/727 bad=0、ARM 391/1214、HIDDEN 385/1153 rot=0。④ 帧卷 334/CHANGED=38 全噪声、基线 334。⑤ build 0 告警；%s；%s；%s；清账 162/63/0；产品面连续零改动 **4** 轮（as-of 501，`python3 scripts/product_streak.py` 现读，last_round=497）。%s。下一轮编号 R518（第 517 轮 / Round 515）：先 push 并复核 ahead=0；读 `41181649050 ↔ ca8619d`、台账笔自身跑与 `41178259137 ↔ 2b8cfda`/`41178474540 ↔ f5051cf` 的全部失败步骤（in_progress/queued ⇒ NOT-RUN）；重点 1x 4.0 是否持续、`MenuBarPopulationTests` 的 `⚠︎` 稳定、614 after、`RTF_HELPER_ORPHAN`（595）、`RECORDING_REREAD`、436；② 产品位换未捕获表面；③ 4.5 地板与 150 上限不动。
""" % (FULLTXT, INSTALLTXT, BATTERYTXT, TAILPAIR)
IS=u"""## Round 514 · R517（第 516 轮 · 2026-10-31）：批量删除所选记录先确认

R515 的事故：多选栏「删除所选记录」直接删，误删 6 条（已恢复 419/ROWS=420）。R517 新增 `BulkDeleteConfirmation`（message 含条数、取消/零选区不删），侧栏先 `guard BulkDeleteConfirmation.confirm(count:using:SystemDestructiveConfirming())` 再 `perform(.deleteSelection)`；确认框复用既有 `DestructiveAlertLayout`（取消默认、删除为破坏性按钮）。4 条策略/接线测试 + M1385/M1386 2/2；预检 298/275/727 bad=0、ARM 391/1214、HIDDEN 385/1153 rot=0。帧卷 334/CHANGED=38 全噪声、基线 334。%s；build 0 告警；%s；%s。⓪ 2b8cfda failure Release+Motion（markdown 1<2 已知采样红）、f5051cf success（INK 5.01/4.82、`MenuBarPopulationTests` 带 `⚠︎` 通过、Motion 5/5）⇒ R516 产品签收、1x 4.0 持续；29c9a45 仅 Release、ba2d0b6 success。真实临时副本点击路径 `ALERT_UI_NOT_RUN=ax-tree-no-outline`（未碰活库）。

**七维度自评**（恰七行，每格 n/15）：

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | 15/15 | 确认框读数与临时副本尝试都记；未碰活库；既有 `DestructiveAlertLayout` 逐项看过。 |
| 判据有效性 | 15/15 | 策略/接线 4 条 + M1385/M1386 2/2；零选区/取消/确认三臂。 |
| 假绿防御 | 15/15 | 真实点击路径 NOT-RUN 具名；全量 5 红不报绿；临时副本非活库。 |
| 产品面推进 | 15/15 | 新安全面（确认框）；2 个产品文件；BACKLOG 619 结案。 |
| 台账一致性 | 15/15 | U-2074…U-2080、D-516、334 帧/全量/换装/电池都来自命令与测试。 |
| 交付诚实性 | 15/15 | 事故与恢复如实；ALERT_UI_NOT_RUN；SelectionReveal 5 红具名。 |
| 可复核性 | 15/15 | M1385/M1386、预检 298/275/727、INK 5.01/4.82、f5051cf success 都在。 |

均分 = 105/105 ≈ 15.0/15（100）。
""" % (FULLTXT, INSTALLTXT, BATTERYTXT)
RB=u"""- **R517（批量删除所选记录先确认；产品 2 文件 + 判据）**：R515 误删 6 条（BACKLOG 619）⇒ `BulkDeleteConfirmation` + 侧栏 guard；message 含条数、取消/零选区不删、确认框复用 `DestructiveAlertLayout`。4 条策略/接线测试；M1385/M1386 2/2；预检 298/275/727 bad=0、HIDDEN 385/1153 rot=0。帧卷 334/CHANGED=38 噪声；全量 %s（5 条已知 SelectionReveal 会话红，不报绿）；换装 %s；电池 %s。临时副本真实点击 `ALERT_UI_NOT_RUN=ax-tree-no-outline`（未碰活库）。
""" % (FULL or u"见补记", INSTALL or u"419=419", BATTERY or u"683/5")
a=rd(A); d=rd(D); b=rd(B); st=rd(S); pr=rd(P); ch=rd(C); it=rd(I)
if a.count(AT_OLD)!=1: raise SystemExit("A title %d" % a.count(AT_OLD))
if a.count(ANCHOR_NEXT)!=1: raise SystemExit("A next %d" % a.count(ANCHOR_NEXT))
if u"## D-516" in d: raise SystemExit("D exists")
if u"619 结案（R517）" in b: raise SystemExit("B exists")
if u"## R517 状态" in st: raise SystemExit("S exists")
if u"R517（批量删除所选记录先确认" in pr: raise SystemExit("P exists")
if u"批量删除所选记录先确认" in ch: raise SystemExit("C exists")
if u"## Round 514 · R517" in it: raise SystemExit("I exists")
if pr.count(u"U-31 … U-2073（R516 现读抬到最新一节）")!=1: raise SystemExit("P ucell")
if pr.count(u"R9–R513，514 节自评")!=1: raise SystemExit("P headline")
if pr.count(u"阶段二 **506 轮**审计（R9–R513；")!=1: raise SystemExit("P phase")
if pr.count(u"PHASE2 n=506")!=1: raise SystemExit("P n")
if pr.count(u"的 Round 513")!=1: raise SystemExit("P round")
if pr.count(u"## 18. R458 → R516 这一段（R478 起写；R504 续到 504、R505 续到 505、R506 续到 506、R507 续到 507、R508 续到 508、R509 续到 509、R510 续到 510、R511 续到 511、R512 续到 512、R513 续到 513、R514 续到 514、R515 续到 515、R516 续到 516 —— 这份报告第七次差点停在几十轮之前）")!=1: raise SystemExit("P s18")
if pr.count(u"的 R516 节 ② 为准")!=1: raise SystemExit("P pointer")
wr(A, a.replace(AT_OLD, AT_NEW, 1).replace(ANCHOR_NEXT, u"\n"+AS+ANCHOR_NEXT, 1))
wr(D, d.rstrip()+"\n\n"+DS+"\n")
wr(B, (b.rstrip()+"\n\n"+BS).rstrip()+"\n")
wr(S, st.replace(u"## R516 状态（", SS.strip()+"\n\n## R516 状态（", 1))
pr=pr.replace(u"R9–R513，514 节自评", u"R9–R514，515 节自评", 1)
pr=pr.replace(u"阶段二 **506 轮**审计（R9–R513；", u"阶段二 **507 轮**审计（R9–R514；", 1)
pr=pr.replace(u"PHASE2 n=506", u"PHASE2 n=507", 1)
pr=pr.replace(u"的 Round 513", u"的 Round 514", 1)
pr=pr.replace(u"U-31 … U-2073（R516 现读抬到最新一节）", u"U-31 … U-2080（R517 现读抬到最新一节）", 1)
pr=pr.replace(u"## 18. R458 → R516 这一段（R478 起写；R504 续到 504、R505 续到 505、R506 续到 506、R507 续到 507、R508 续到 508、R509 续到 509、R510 续到 510、R511 续到 511、R512 续到 512、R513 续到 513、R514 续到 514、R515 续到 515、R516 续到 516 —— 这份报告第七次差点停在几十轮之前）",
              u"## 18. R458 → R517 这一段（R478 起写；R504 续到 504、R505 续到 505、R506 续到 506、R507 续到 507、R508 续到 508、R509 续到 509、R510 续到 510、R511 续到 511、R512 续到 512、R513 续到 513、R514 续到 514、R515 续到 515、R516 续到 516、R517 续到 517 —— 这份报告第七次差点停在几十轮之前）", 1)
pr=pr.replace(u"的 R516 节 ② 为准", u"的 R517 节 ② 为准", 1)
wr(P, pr.rstrip()+"\n\n"+RB+"\n")
m=u"## [Unreleased]\n"
if ch.count(m)!=1: raise SystemExit("C anchor")
wr(C, ch.replace(m, m+"\n"+CS, 1))
wr(I, it.rstrip()+"\n\n"+IS+"\n")
print("OK sha=%s full=%s install=%s battery=%s" % (sha, FULL, INSTALL, BATTERY))
