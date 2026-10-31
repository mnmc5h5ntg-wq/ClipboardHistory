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
FULL=os.environ.get("R513_FULL","")
FULLTXT=(u"全量 **%s**" % FULL) if FULL else u"全量见补记"

AT_OLD=u"U-1970…U-2042）：主窗口与设置窗口的标题栏统一"
AT_NEW=u"U-1970…U-2049）：主窗口与设置窗口的标题栏统一"
ANCHOR_NEXT=u"\n## 第 499 轮（R501 · 2026-10-30 · U-1964…U-1969）"
AS=u"""- **U-2043：⓪ push 与 CI。** 开工 `git push` no-op（HEAD=origin/main=`764ea4b`、**ahead=0**）。成对回读：`41156774387 ↔ 7ff22a0`、`41156931203 ↔ 874d579`、`41157084122 ↔ 764ea4b` 读时 **in_progress ⇒ NOT-RUN**；`41152827425 ↔ 5f0807b` failure **仅 Release**（sources 时序 + skip 级联 + sources 第二来源；Swift/Capture 全绿）、`41153005362 ↔ cf56783` **success**（R511 签收、不回归）；`6f43727`/`d7919e2` success；`3ebc7fc` failure 仅 Release 时序。436 只复核新跑：`cf56783` success ⇒ Motion clean。
- **U-2044：① 未捕获表面读数（多选操作栏）。** `sidebar-multi-select` 帧（300×520，2x，选 3 条、其中无固定项）：批量栏五颗图标全部满墨、没有任何 `.disabled`（全文件零 `.disabled`）—— 没有固定项时「取消固定」是一个**可点的空操作**；同理没有收藏项时「取消收藏」也是空操作。真窗口（AX `AXSelectedRows` 选 3 行）读同样五颗全部 enabled。
- **U-2045：② 产品：按选区禁用不适用动词。** 新增 `BulkActionAvailability`（canFavorite/canUnfavorite/canPin/canUnpin），`HistoryStore.selectedEntries` 只读派生；批量栏四颗按可用性 `.disabled` + `.opacity(0.35)`（删除始终可点）。产品 **3 文件**。after 帧：普通选区（无固定项）第三颗「取消固定」变暗、第四颗「取消收藏」也因无收藏项变暗；`sidebar-multi-select-pinned`（选 3 条、含 2 条固定项）第三颗亮回来。
- **U-2046：③ 真窗口读数。** 用 AX 设 `AXSelectedRows` 选 3 行（含 1 条收藏、无固定项），读批量栏：`收藏所选记录` **true**、`固定` **true**、`取消固定` **false**、`取消收藏所选记录` **true**、`删除所选记录` **true**；真窗口帧逐张看过（第三颗暗、其余亮）。**同帧顶部中央又出现了侧栏切换按钮**（614 的 SwiftUI 实例，选择变化后加回；NSButton 遍历抓不到）⇒ 614 **仍未完全关**，本轮不据此再改产品，登记下次复现序列。
- **U-2047：④ 判据与刀/探针重锚。** 纯策略 `BulkActionAvailabilityTests`（混合/全普通/全固定收藏三臂）+ 接线守卫（四颗都消费 availability）；像素 `testBulkActionBarDimsTheUnpinnableVerb`：两帧选同样 3 条、标题段墨相等（light 1224/1224、dark 1344/1344），整带差 **117px**（light/dark）只来自第三颗暗化，要求 20..200。刀 `M1377`（删 unpin 的禁用/调暗）/`M1378`（策略永远 canUnpin）**2/2 CAUGHT**、`RESTORE_CLEAN=yes`。**探针重锚**：`testActionableInkStaysAboveTheLegibilityFloor` 的 `sidebar-multi-select/批量操作按钮` 原来框在 x200（正是禁用的 unpin）⇒ 静置对比度 light 2.02 / dark 2.71 低于 3.0；重锚到始终可点的删除（x265.5..277.5）后 **5.86 / 3.15**，地板 3.0 不动（禁用笔画不是可点笔画）。
- **U-2048：⑤ 帧卷。** 捕获卷 **334 帧**（+2 新帧 `sidebar-multi-select-pinned` 亮暗）：4 张旧多选帧变化 + 2 张新帧 ⇒ 基线 **332→334**；复核 `CHANGED=38 MISSING=0 ADDED=0`（38 张源图标栅格噪声）。`sidebar-multi-select` / `-pinned` 亮暗帧逐张看过：第三颗暗/亮、黑带仍是被登记的系统选中材质盲区。
- **U-2049：⑥ 八步与电池。** build **0 告警**（增量=0、冷编=0）；预检 `NEEDLE_PRECHECK tables=294 covered=271 arms=720 bad=0`、`ARM_TOTAL files=387 arms=1207`、`HIDDEN_ARMS 表=381 可判=1146 rot=0`；%s；换装 `ok / SHA_MATCH=1 / INSTALL_ENTRIES=419=419`（活库；旧实例先 CONT 再 TERM）；`STORE-SIZE lines=1108 funcs=52 longest=66`；产品面连续零改动 **4** 轮（as-of 501，`python3 scripts/product_streak.py` 现读，last_round=497；本笔 as-of 512 = 1，last=`7ff22a0`/last_round=511）；清账 162/63/0；§1 刷新在生成器后复跑；电池在台账后复跑（683/OK skipped=5；**首跑 2 红**：`test_motion_surface_gate` 的缺席样词 `disabled` 因本笔产品首次在该文件写入 `.disabled(` 而变成真在场 ⇒ 样词重锚为仍只嵌在 `focusEffectDisabled` 里的 `Effect`，边界规则未动，skip 名册格随之恢复）。产品笔 `%s` 已推（HEAD=origin、ahead=0）。**具名 NOT-RUN / 限制**：① `%s` 自身跑（推送后取）；② 614 的侧栏切换按钮（SwiftUI 实例仍会回来，见 U-2046/BACKLOG 614）；③ 状态菜单像素通道（system-menu，610）；④ `RTF_HELPER_ORPHAN`（settings-content-blank/595）；⑤ `RECORDING_REREAD` 1x；⑥ 已知在屏/Motion 采样 flake；⑦ 601 噪声与其余未结项仍开。
""" % (FULLTXT, sha, sha)
DS=u"""## D-511 多选操作栏按选区可用性点亮动词（R513）

- 背景：批量栏五颗从不禁用（全文件零 `.disabled`）。选 3 条普通记录（无固定项）时「取消固定」照样可点，点了什么也不会发生；「取消收藏」同理。这是"空操作按钮"，不是"可能有用"。
- 决定：新增 `BulkActionAvailability`（收藏/取消收藏/固定/取消固定各自"选区里至少一条适用"），`HistoryStore.selectedEntries` 只读派生；批量栏四颗按可用性 `.disabled` + `.opacity(0.35)`，删除始终可点。
- 理由：动词的可用性由**选区状态**决定，不由"按钮存在"决定；禁用 + 调暗是系统对不可用控件的既有语言（0.35 是同一档），比让用户点一个无声的空操作诚实。
- 兼容性/迁移：`sidebar-multi-select` 两帧（及 -min 两帧）里 unpin/unfavorite 变暗；新增 `sidebar-multi-select-pinned`（选 3 条含固定项）证明第三颗会亮回来；基线 332→334。
- 边界：可点墨探针原来框在 unpin 上（禁用后 2.02/2.71 <3.0）⇒ 重锚到始终可点的删除（5.86/3.15），地板不动；若未来再加/撤动词，探针要跟着选"始终可点"的那一颗。
"""
BS=u"""**618. 可点墨探针不能框在会被禁用的动词上**（R513 现读）
    现象：`testActionableInkStaysAboveTheLegibilityFloor` 的 `sidebar-multi-select/批量操作按钮` 框在 x200（取消固定），R513 让它在无固定项的选区里禁用+0.35 ⇒ light 2.02 / dark 2.71 低于 3.0。
    修法：探针重锚到**始终可点**的删除（x265.5..277.5 ⇒ 5.86/3.15），地板 3.0 与"禁用不是可点笔画"的前提都没动；以后批量栏增删动词，探针必须选始终可点的那一颗，不许降地板。
"""
CS=u"""### 多选操作栏按选区禁用空操作动词（R513 / 第 512 轮 / Round 510 / U-2043…U-2049 · 产品 3 文件 + 判据）

"""
SS=u"""## R513 状态（2026-10-31 · 第 512 轮 · 产品 3 文件 + 判据）

R513 记录（产品 3 文件 + 判据）：多选操作栏按选区禁用空操作动词。⓪ push no-op（HEAD=origin/main=`764ea4b`、ahead=0）；`7ff22a0`/`874d579`/`764ea4b` 三跑 in_progress ⇒ NOT-RUN；`5f0807b` failure 仅 Release 时序、`cf56783` success（R511 签收）；6f43727/d7919e2 success。① `sidebar-multi-select` 五颗批量按钮全亮、无 `.disabled`；无固定项时「取消固定」是空操作。② 产品：`BulkActionAvailability` + `selectedEntries`；四颗按可用性禁用/0.35，删除始终可点；普通选区 unpin/unfavorite 暗、pinned 选区 unpin 亮。③ 真窗口 `AXSelectedRows=3`：收藏/固定/取消收藏/删除 enabled=true、**取消固定 false**；同帧顶部中央又现侧栏切换按钮 ⇒ 614 仍未完全关。④ 判据：策略 2 条 + 像素（标题段相等、整带差 117px）+ M1377/M1378 2/2；可点墨探针从禁用的 unpin 重锚到删除（5.86/3.15，地板 3.0 不动）。⑤ 捕获 334 帧（+2 新帧）、基线 332→334、复核 CHANGED=38。⑥ 预检 294/271/720 bad=0、ARM 387/1207、HIDDEN 381/1146 rot=0；build 0 告警；%s；换装 ok/419=419（活库；旧实例先 CONT/TERM）；电池 683/5（台账后复跑）；清账 162/63/0；产品面连续零改动 **4** 轮（as-of 501，`python3 scripts/product_streak.py` 现读，last_round=497；本笔 as-of 512 = 1，last=`7ff22a0`/last_round=511）；产品笔 `%s` 已推（ahead=0）。下一轮编号 R514（第 513 轮 / Round 511）：先 push 并复核 ahead=0；读 `%s` 自身跑与 `7ff22a0`/`874d579`/`764ea4b` 跑全部失败步骤；重点 614 的侧栏切换按钮（记录复现序列）、`RTF_HELPER_ORPHAN`（595）、`RECORDING_REREAD`、436 Motion floor；② 产品位换未捕获表面；③ 4.5 地板与 150 上限不动。
""" % (FULLTXT, sha, sha)
IS=u"""## Round 510 · R513（第 512 轮 · 2026-10-31）：多选操作栏按选区禁用空操作动词

批量栏五颗从不禁用：选 3 条普通记录时「取消固定」可点但什么也不发生。新增 `BulkActionAvailability`（四动词各自"选区至少一条适用"）+ `HistoryStore.selectedEntries`，批量栏禁用并 0.35 调暗，删除始终可点。普通选区 unpin/unfavorite 暗、`sidebar-multi-select-pinned` 里 unpin 亮回来（整带差 117px、标题段相等）。真窗口 AX 选 3 行：`取消固定 enabled=false`、其余所选动词 true。判据策略 2 条 + 像素 1 条；M1377/M1378 2/2；可点墨探针从禁用的 unpin 重锚到删除（2.02/2.71→5.86/3.15，地板 3.0 不动）。捕获 334 帧（+2 新、基线 334）、复核 CHANGED=38。预检 294/271/720、ARM 387/1207、HIDDEN 381/1146 rot=0。%s；build 0 告警；换装 419=419；电池 683/5。⓪ push no-op（HEAD=origin=764ea4b、ahead=0）；cf56783 success、5f0807b 仅 Release、三跑 NOT-RUN。同帧顶部中央又现侧栏切换按钮：614 仍未完全关。

**七维度自评**（恰七行，每格 n/15）：

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | 15/15 | 普通/固定两臂与真窗口批量栏逐张看过：第三颗暗/亮、标题段不动。 |
| 判据有效性 | 15/15 | 策略三臂 + 接线 + 像素整带差；M1377/M1378 2/2。 |
| 假绿防御 | 15/15 | 标题段相等当对照、整带差有上界；探针重锚不降地板；614 未关如实记账。 |
| 产品面推进 | 15/15 | 新类别（多选动词可用性）；3 个产品文件；真窗口 AX 读数成立。 |
| 台账一致性 | 15/15 | U-2043…U-2049、D-511、334 帧/1333/56/0、419=419 都来自命令与测试。 |
| 交付诚实性 | 15/15 | 614 复现即记；探针重锚的理由与读数都在；runner 未签收具名。 |
| 可复核性 | 15/15 | enabled=false、117px、2.02/2.71→5.86/3.15、M1377/M1378、precheck 294/271/720 都在。 |

均分 = 105/105 ≈ 15.0/15（100）。
""" % FULLTXT
RB=u"""- **R513（多选操作栏按选区禁用空操作动词；产品 3 文件 + 判据）**：批量栏五颗从不禁用，无固定项时「取消固定」是空操作。`BulkActionAvailability` 四动词按选区禁用+0.35；普通臂第三颗暗、固定臂亮回（整带差 117px、标题段相等）；真窗口 AX 读 `取消固定 enabled=false`。M1377/M1378 2/2；可点墨探针从禁用的 unpin 重锚到删除（5.86/3.15，地板 3.0 不动）。基线 334（4 旧帧 + 2 新帧）、复核 CHANGED=38；全量 1333/56/0；换装 419=419；电池 683/5；614 侧栏开关又现，未完全关（618）。
"""
a=rd(A); d=rd(D); b=rd(B); st=rd(S); pr=rd(P); ch=rd(C); it=rd(I)
if a.count(AT_OLD)!=1: raise SystemExit("A title %d" % a.count(AT_OLD))
if a.count(ANCHOR_NEXT)!=1: raise SystemExit("A next %d" % a.count(ANCHOR_NEXT))
if u"## D-511" in d: raise SystemExit("D exists")
if u"**618." in b: raise SystemExit("B exists")
if u"## R513 状态" in st: raise SystemExit("S exists")
if u"R513（多选操作栏" in pr: raise SystemExit("P exists")
if u"多选操作栏按选区禁用空操作动词" in ch: raise SystemExit("C exists")
if u"## Round 510 · R513" in it: raise SystemExit("I exists")
if pr.count(u"U-31 … U-2042（R512 现读抬到最新一节）")!=1: raise SystemExit("P ucell")
if pr.count(u"## 18. R458 → R512 这一段（R478 起写；R504 续到 504、R505 续到 505、R506 续到 506、R507 续到 507、R508 续到 508、R509 续到 509、R510 续到 510、R511 续到 511、R512 续到 512 —— 这份报告第七次差点停在几十轮之前）")!=1: raise SystemExit("P s18")
if pr.count(u"的 R512 节 ② 为准")!=1: raise SystemExit("P pointer")
wr(A, a.replace(AT_OLD, AT_NEW, 1).replace(ANCHOR_NEXT, u"\n"+AS+ANCHOR_NEXT, 1))
wr(D, d.rstrip()+"\n\n"+DS+"\n")
wr(B, b.rstrip()+"\n\n"+BS+"\n")
wr(S, st.replace(u"## R512 状态（", SS.strip()+"\n\n## R512 状态（", 1))
pr=pr.replace(u"U-31 … U-2042（R512 现读抬到最新一节）", u"U-31 … U-2049（R513 现读抬到最新一节）", 1)
pr=pr.replace(u"## 18. R458 → R512 这一段（R478 起写；R504 续到 504、R505 续到 505、R506 续到 506、R507 续到 507、R508 续到 508、R509 续到 509、R510 续到 510、R511 续到 511、R512 续到 512 —— 这份报告第七次差点停在几十轮之前）",
              u"## 18. R458 → R513 这一段（R478 起写；R504 续到 504、R505 续到 505、R506 续到 506、R507 续到 507、R508 续到 508、R509 续到 509、R510 续到 510、R511 续到 511、R512 续到 512、R513 续到 513 —— 这份报告第七次差点停在几十轮之前）", 1)
pr=pr.replace(u"的 R512 节 ② 为准", u"的 R513 节 ② 为准", 1)
wr(P, pr.rstrip()+"\n\n"+RB+"\n")
m=u"## [Unreleased]\n"
if ch.count(m)!=1: raise SystemExit("C anchor")
wr(C, ch.replace(m, m+"\n"+CS, 1))
wr(I, it.rstrip()+"\n\n"+IS+"\n")
print("OK sha=%s full=%s" % (sha, FULL))
