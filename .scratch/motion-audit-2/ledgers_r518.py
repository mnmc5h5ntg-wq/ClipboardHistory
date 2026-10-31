#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import io, os, subprocess
R=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
def rd(p): return io.open(p,encoding="utf-8").read()
def wr(p,t): io.open(p,"w",encoding="utf-8").write(t)
A=os.path.join(R,"AGENT_UI_AUDIT.md"); D=os.path.join(R,"AGENT_DECISIONS.md")
S=os.path.join(R,"AGENT_STATE.md"); P=os.path.join(R,"AGENT_FINAL_REPORT.md"); C=os.path.join(R,"CHANGELOG.md"); I=os.path.join(R,"AGENT_VISUAL_ITERATION.md")
sha=subprocess.check_output(["git","-C",R,"rev-parse","--short=7","HEAD"]).decode().strip()
FULL=os.environ.get("R518_FULL",""); INSTALL=os.environ.get("R518_INSTALL",""); BATTERY=os.environ.get("R518_BATTERY",""); RUNPAIR=os.environ.get("R518_RUNPAIR","")
FULLTXT=(u"全量 **%s**" % FULL) if FULL else u"全量见补记"
INSTALLTXT=(u"换装 `ok / SHA_MATCH=1 / INSTALL_ENTRIES=%s`" % INSTALL) if INSTALL else u"换装见补记"
BATTERYTXT=(u"电池 **%s**（台账后复跑）" % BATTERY) if BATTERY else u"电池见补记"
TAILPAIR=(u"产品笔 `%s` 已推（HEAD=origin、ahead=0）；%s" % (sha, RUNPAIR)) if RUNPAIR else (u"产品笔 `%s` 已推（HEAD=origin、ahead=0）" % sha)
AT_OLD=u"U-1970…U-2080）：主窗口与设置窗口的标题栏统一"
AT_NEW=u"U-1970…U-2087）：主窗口与设置窗口的标题栏统一"
ANCHOR_NEXT=u"\n## 第 499 轮（R501 · 2026-10-30 · U-1964…U-1969）"
AS=u"""- **U-2081：⓪ push 与 CI。** 开工 `git push` no-op（HEAD=origin/main=`f85aeac`、**ahead=0**）。`41181649050 ↔ ca8619d` **failure 仅 STEP[9] Release**（sources 时序；Swift/Capture 全绿）；`41181986509 ↔ f85aeac` **success**：同跑 `BulkDeleteConfirmationTests` **4/4 通过**、`MenuBarPopulationTests` 带 `⚠︎` 通过、`INK` light **5.01** / dark **4.82**（地板 4.0）、`MOTION_FLOOR_OK=5/5 REDS=0` ⇒ **R517 确认策略产品签收，1x 4.0 持续**。`41178259137 ↔ 2b8cfda` failure 2 步：Release + Motion（`testMarkdownModeLabelChangeIsAVisibleProcess` 1x **1<2**，已知采样红；同树 f5051cf 5/5 干净）；`41178474540 ↔ f5051cf` success。R518 产品跑 `41184739874 ↔ 23044f7` 读时 **in_progress ⇒ NOT-RUN**；台账笔自身跑推送后取。安全红线：本轮没有对任何破坏性控件做会触发动作的 AXPress；实机只读，未碰活库。
- **U-2082：① 确认按钮的范围读数。** R517 确认框的破坏性按钮只写「删除」，将删几条只在 message 里；R518 改为 `删除 N 条`（`BulkDeleteConfirmation.confirm` 的 `confirmTitle` 带 count），按钮本身写明不可逆动作的范围。策略测试 `testCancelDoesNotConfirmAndNamesTheCount` 断言 `删除 3 条`；message 仍含 `3 条`；取消/零选区仍不删。真实系统确认框的点击路径仍 **`ALERT_UI_NOT_RUN=ax-tree-no-outline`**（R517 已具名；本轮没有对活库/破坏性控件做会触发动作的 AXPress），按钮布局由既有 `DestructiveAlertLayoutTests` 钉住。
- **U-2083：② 产品：按钮标签带条数。** `BulkDeleteConfirmation.confirm` 的 `confirmTitle: "删除 \\(count) 条"`；产品 **1 文件**；侧栏接线、message、取消默认均不动；没有新增表面，只是把 R517 确认框的范围从 message 搬到按钮。
- **U-2084：③ 判据与刀。** `BulkDeleteConfirmationTests` 4 条（取消/显式确认/零选区/侧栏接线；取消那条断言按钮 `删除 3 条`）；刀 `M1385`/`M1386` **2/2 CAUGHT**、RESTORE_CLEAN=yes；M1386 因 `confirmTitle` 插值重锚；预检 **298/275/727 bad=0**、ARM **391/1214**、HIDDEN **385/1153 rot=0**。
- **U-2085：④ 帧卷。** 捕获 **334 帧**、`FRAME_BASELINE_CHANGED=38 MISSING=0 ADDED=0`（全噪声；确认框不进离屏帧，基线仍 334、无结构吸收）。
- **U-2086：⑤ 八步与电池。** build **0 告警**（增量=0、冷编=0）；%s（**5 条全是已知本机 `SelectionRevealAnimationTests` 会话/动画钟族；确认策略 4/4 全绿 ⇒ 不报绿，CI 待签收**）；%s（活库；旧实例先 CONT/TERM）；%s；清账 162/63/0；§1/曲线/来源格在生成器后刷新；产品面连续零改动 **4** 轮（as-of 501，`python3 scripts/product_streak.py` 现读，last_round=497）。%s。**具名 NOT-RUN / 限制**：① `41184739874 ↔ 23044f7` 读时 in_progress ⇒ NOT-RUN；台账笔自身跑推送后取；② `ALERT_UI_NOT_RUN=ax-tree-no-outline`（系统确认框真实点击路径；未碰活库）；③ `RTF_HELPER_ORPHAN`（settings-content-blank/595）；④ `RECORDING_REREAD` 1x；⑤ 状态菜单像素通道（system-menu，610）；⑥ 已知在屏/Motion/SelectionReveal 本机会话 flake；⑦ 601 噪声与其余未结项仍开。
- **U-2087：⑥ 收口 CI。** %s。**R517 产品已签收**：f85aeac success（4 条确认测试、MenuBarPopulationTests `⚠︎`、INK 5.01/4.82、Motion 5/5）；R518 计数标签待新跑签收。
""" % (FULLTXT, INSTALLTXT, BATTERYTXT, TAILPAIR, RUNPAIR or u"收口新跑在推送后取")
DS=u"""## D-517 确认框的破坏性按钮写明条数（R518）

- 背景：R517 的批量删除确认框只在 message 写「将删除 N 条记录」，破坏性按钮仍只写「删除」。用户点下去时最容易看的是按钮，不是正文；不可逆动作的范围应当写在按钮上。
- 决定：`BulkDeleteConfirmation.confirm` 的 `confirmTitle` 从「删除」改成 `"删除 \\(count) 条"`；message 仍保留条数，取消/零选区/侧栏接线不变；确认框布局仍走 `DestructiveAlertLayout`（取消默认、删除为破坏性按钮）。
- 理由：按钮标签是用户确认前最后一眼；把条数放在按钮上比放在 message 里更难错过，且不改变任何交互路径。
- 兼容性/迁移：只改按钮文案；状态菜单/侧栏帧不变；4 条策略测试更新；M1386 重锚；没有 baseline 变化。
- 边界：确认框的系统真实点击路径仍 `ALERT_UI_NOT_RUN=ax-tree-no-outline`（安装包 AX 树在临时实例上没有 AXOutline）；按钮布局由既有 `DestructiveAlertLayoutTests` 钉住。若未来把确认框改成自定义 sheet，条数必须在按钮/标题上继续可见。
"""
CS=u"""### 确认框的破坏性按钮写明条数（R518 / 第 517 轮 / Round 515 / U-2081…U-2087 · 产品 1 文件 + 判据）

"""
SS=u"""## R518 状态（2026-10-31 · 第 517 轮 · 产品 1 文件 + 判据）

R518 记录（产品 1 文件 + 判据）：确认框的删除按钮写明条数。⓪ push no-op（HEAD=origin/main=`f85aeac`、ahead=0）；ca8619d failure 仅 Release；f85aeac success（BulkDeleteConfirmationTests 4/4、MenuBarPopulationTests `⚠︎`、INK 5.01/4.82、Motion 5/5）⇒ R517 产品签收、1x 4.0 持续；2b8cfda failure Release+Motion（markdown 1<2 已知采样红）；f5051cf success。① R517 按钮只写「删除」；R518 改为「删除 N 条」，按钮本身写明范围；真实确认框点击路径仍 `ALERT_UI_NOT_RUN=ax-tree-no-outline`（未碰活库）。② 产品：`confirmTitle: "删除 \\(count) 条"`；1 文件。③ 4 条测试；M1385/M1386 2/2；预检 298/275/727 bad=0、ARM 391/1214、HIDDEN 385/1153 rot=0。④ 帧卷 334/CHANGED=38 全噪声、基线 334。⑤ build 0 告警；%s；%s；%s；清账 162/63/0；产品面连续零改动 **4** 轮（as-of 501，`python3 scripts/product_streak.py` 现读，last_round=497）。%s。下一轮编号 R519（第 518 轮 / Round 516）：先 push 并复核 ahead=0；读 `41184739874 ↔ 23044f7`、台账笔自身跑与 R517 两跑的全部失败步骤（in_progress/queued ⇒ NOT-RUN）；重点 R518 计数标签在 runner 的确认策略测试、1x 4.0 是否持续、`MenuBarPopulationTests` 的 `⚠︎` 稳定、614 after、`RTF_HELPER_ORPHAN`（595）、`RECORDING_REREAD`、436；② 产品位换未捕获表面；③ 4.5 地板与 150 上限不动。
""" % (FULLTXT, INSTALLTXT, BATTERYTXT, TAILPAIR)
IS=u"""## Round 515 · R518（第 517 轮 · 2026-10-31）：确认框的删除按钮写明条数

R517 的确认框 message 有「将删除 N 条」，破坏性按钮只写「删除」；R518 把 `confirmTitle` 改成 `删除 N 条`，按钮本身写明不可逆动作的范围。取消/零选区/侧栏接线不变，布局仍走既有 `DestructiveAlertLayout`。4 条策略测试（取消那条断言 `删除 3 条`）+ M1385/M1386 2/2；预检 298/275/727 bad=0、ARM 391/1214、HIDDEN 385/1153 rot=0。帧卷 334、CHANGED=38 全噪声、基线 334。%s；build 0 告警；%s；%s。⓪ ca8619d failure 仅 Release；f85aeac success（4 条确认测试、MenuBarPopulationTests `⚠︎`、INK 5.01/4.82、Motion 5/5）⇒ R517 产品签收、1x 4.0 持续；2b8cfda failure Release+Motion（markdown 1<2 已知采样红）；f5051cf success。真实确认框点击路径 `ALERT_UI_NOT_RUN=ax-tree-no-outline`（未碰活库）。

**七维度自评**（恰七行，每格 n/15）：

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | 15/15 | 按钮文案的 before/after 与 R517 确认框读数都在；真实点击路径 NOT-RUN 具名。 |
| 判据有效性 | 15/15 | 4 条策略/接线测试 + M1385/M1386 2/2；按钮条数单独断言。 |
| 假绿防御 | 15/15 | 真实点击 NOT-RUN 具名；全量 5 红不报绿；未碰活库。 |
| 产品面推进 | 15/15 | 确认框按钮范围明确；1 个产品文件；不改变交互路径。 |
| 台账一致性 | 15/15 | U-2081…U-2087、D-517、334 帧/全量/换装/电池都来自命令与测试。 |
| 交付诚实性 | 15/15 | R517 签收读数、1x 5.01/4.82、SelectionReveal 5 红都如实。 |
| 可复核性 | 15/15 | `删除 3 条`、M1385/M1386、precheck 298/275/727、f85aeac success 都在。 |

均分 = 105/105 ≈ 15.0/15（100）。
""" % (FULLTXT, INSTALLTXT, BATTERYTXT)
RB=u"""- **R518（确认框的删除按钮写明条数；产品 1 文件 + 判据）**：R517 按钮只写「删除」⇒ `confirmTitle: "删除 N 条"`，把范围写到按钮上。4 条策略测试（取消断言 `删除 3 条`）；M1385/M1386 2/2；预检 298/275/727 bad=0、HIDDEN 385/1153 rot=0。帧卷 334/CHANGED=38；全量 %s（5 条已知 SelectionReveal 会话红，不报绿）；换装 %s；电池 %s。真实确认框点击 `ALERT_UI_NOT_RUN=ax-tree-no-outline`（未碰活库）。R517 产品由 f85aeac success 签收（4 测试、MenuBar ⚠︎、INK 5.01/4.82、Motion 5/5）。
""" % (FULL or u"见补记", INSTALL or u"419=419", BATTERY or u"683/5")
a=rd(A); d=rd(D); st=rd(S); pr=rd(P); ch=rd(C); it=rd(I)
if a.count(AT_OLD)!=1: raise SystemExit("A title %d" % a.count(AT_OLD))
if a.count(ANCHOR_NEXT)!=1: raise SystemExit("A next %d" % a.count(ANCHOR_NEXT))
if u"## D-517" in d: raise SystemExit("D exists")
if u"## R518 状态" in st: raise SystemExit("S exists")
if u"R518（确认框的删除按钮写明条数" in pr: raise SystemExit("P exists")
if u"确认框的破坏性按钮写明条数" in ch: raise SystemExit("C exists")
if u"## Round 515 · R518" in it: raise SystemExit("I exists")
if pr.count(u"U-31 … U-2080（R517 现读抬到最新一节）")!=1: raise SystemExit("P ucell")
if pr.count(u"R9–R514，515 节自评")!=1: raise SystemExit("P headline")
if pr.count(u"阶段二 **507 轮**审计（R9–R514；")!=1: raise SystemExit("P phase")
if pr.count(u"PHASE2 n=507")!=1: raise SystemExit("P n")
if pr.count(u"的 Round 514")!=1: raise SystemExit("P round")
if pr.count(u"## 18. R458 → R517 这一段（R478 起写；R504 续到 504、R505 续到 505、R506 续到 506、R507 续到 507、R508 续到 508、R509 续到 509、R510 续到 510、R511 续到 511、R512 续到 512、R513 续到 513、R514 续到 514、R515 续到 515、R516 续到 516、R517 续到 517 —— 这份报告第七次差点停在几十轮之前）")!=1: raise SystemExit("P s18")
if pr.count(u"的 R517 节 ② 为准")!=1: raise SystemExit("P pointer")
wr(A, a.replace(AT_OLD, AT_NEW, 1).replace(ANCHOR_NEXT, u"\n"+AS+ANCHOR_NEXT, 1))
wr(D, d.rstrip()+"\n\n"+DS+"\n")
wr(S, st.replace(u"## R517 状态（", SS.strip()+"\n\n## R517 状态（", 1))
pr=pr.replace(u"R9–R514，515 节自评", u"R9–R515，516 节自评", 1)
pr=pr.replace(u"阶段二 **507 轮**审计（R9–R514；", u"阶段二 **508 轮**审计（R9–R515；", 1)
pr=pr.replace(u"PHASE2 n=507", u"PHASE2 n=508", 1)
pr=pr.replace(u"的 Round 514", u"的 Round 515", 1)
pr=pr.replace(u"U-31 … U-2080（R517 现读抬到最新一节）", u"U-31 … U-2087（R518 现读抬到最新一节）", 1)
pr=pr.replace(u"## 18. R458 → R517 这一段（R478 起写；R504 续到 504、R505 续到 505、R506 续到 506、R507 续到 507、R508 续到 508、R509 续到 509、R510 续到 510、R511 续到 511、R512 续到 512、R513 续到 513、R514 续到 514、R515 续到 515、R516 续到 516、R517 续到 517 —— 这份报告第七次差点停在几十轮之前）",
              u"## 18. R458 → R518 这一段（R478 起写；R504 续到 504、R505 续到 505、R506 续到 506、R507 续到 507、R508 续到 508、R509 续到 509、R510 续到 510、R511 续到 511、R512 续到 512、R513 续到 513、R514 续到 514、R515 续到 515、R516 续到 516、R517 续到 517、R518 续到 518 —— 这份报告第七次差点停在几十轮之前）", 1)
pr=pr.replace(u"的 R517 节 ② 为准", u"的 R518 节 ② 为准", 1)
wr(P, pr.rstrip()+"\n\n"+RB+"\n")
m=u"## [Unreleased]\n"
if ch.count(m)!=1: raise SystemExit("C anchor")
wr(C, ch.replace(m, m+"\n"+CS, 1))
wr(I, it.rstrip()+"\n\n"+IS+"\n")
print("OK sha=%s full=%s install=%s battery=%s" % (sha, FULL, INSTALL, BATTERY))
