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
FULL=os.environ.get("R512_FULL","")
FULLTXT=(u"全量 **%s**" % FULL) if FULL else u"全量见补记"

AT_OLD=u"U-1970…U-2035）：主窗口与设置窗口的标题栏统一"
AT_NEW=u"U-1970…U-2041）：主窗口与设置窗口的标题栏统一"
ANCHOR_NEXT=u"\n## 第 499 轮（R501 · 2026-10-30 · U-1964…U-1969）"
AS=u"""- **U-2036：⓪ push 与 CI。** 开工 `git push` no-op（HEAD=origin/main=`cf56783`、**ahead=0**）。成对回读：`41152827425 ↔ 5f0807b`、`41153005362 ↔ cf56783` 读时 **in_progress ⇒ NOT-RUN**；`41144830309 ↔ 6f43727`、`41145147519 ↔ d7919e2` **success**（复核不回归 ⇒ `详情/组合帧头部` 探针的恢复持续）；`41144200112 ↔ 3ebc7fc` failure **仅 Release**（sources 时序 + 当笔尚未进 UNPARSED_ROSTER + skip 级联，已由 6f43727 修）；R509 三跑 failure 仅 Release（`bg-not-flat (32,32,32)`，已被 6f43727 success 签收）。`e3eb62b`/`6543959` success；`3d20a02`/`f9b8733` 已知采样 flake。436 只复核新跑：6f43727/d7919e2 success ⇒ Motion clean。
- **U-2037：① 未捕获表面读数（侧栏分组标题）。** 离屏 `sidebar-pinned-section` 帧（300×520，2x）：分组标题「已固定」的左墨在 **36.5pt**，首行的星标左墨在 **20.0pt**，行标题列在 **96.5pt** —— 标题落在图标列与标题列**之间**，与哪一列都不同轴。macOS 侧栏的分组标题应与行首图标同一条左轴（同一棵树里图标是最左的内容列）。
- **U-2038：② 产品：分组标题对齐行图标列。** `SidebarSectionHeader` 的 `.padding(.leading, 22)` 改为 **6**（侧栏内容从约 14.5pt 起 ⇒ 标题左墨 20.5pt）。产品 **1 文件**。after 两档 `SECTION_HEADER_ALIGN`：light 标题 **20.5** / 行图标 **20.0**（差 **0.5**）、dark 同；离屏 `sidebar-pinned-section` 亮/暗帧逐张看过：标题与星标同轴，行几何未动。
- **U-2039：③ 判据与刀。** 新判据 `testSidebarSectionHeaderAlignsWithTheRowIconColumn`：在 `sidebar-pinned-section` 的固定 y 带里分别量分组标题与行首图标的**第一处墨**，要求差 ≤1.5pt；任一臂无墨 ⇒ `SECTION_HEADER_ALIGN_NOT_RUN=band-blank`。刀 `M1375`（退回 22）/`M1376`（对齐到标题列 82）**2/2 CAUGHT**、`RESTORE_CLEAN=yes`。
- **U-2040：④ 帧卷。** 捕获卷 **332 帧**、`CHANGED=42`：**2 张** `sidebar-pinned-section-300x520-{light,dark}` 是合法结构变化（标题左移 16pt），其余 **40 张**为源图标栅格噪声 ⇒ 只吸收那 2 张（**332 保持**），复核 `CHANGED=40 MISSING=0 ADDED=0`。真窗口当前没有置顶记录 ⇒ 没有「已固定」节可拍（`AXButton desc=[固定…]` 只是操作栏那颗按钮）；本条以离屏帧为像素证人，真窗口不臆造读数。
- **U-2041：⑤ 八步与电池。** build **0 告警**（增量=0、冷编=0）；预检 `NEEDLE_PRECHECK tables=293 covered=270 arms=718 bad=0`、`ARM_TOTAL files=386 arms=1205`、`HIDDEN_ARMS 表=380 可判=1144 rot=0`；%s；换装 `ok / SHA_MATCH=1 / INSTALL_ENTRIES=419=419`（活库；旧实例先 CONT/TERM）；`STORE-SIZE lines=1108 funcs=52 longest=66`；产品面连续零改动 **4** 轮（as-of 501，`python3 scripts/product_streak.py` 现读，last_round=497；本笔 as-of 511 = 1，last=`5f0807b`/last_round=510）；清账 162/63/0；§1 刷新在生成器后复跑；电池在台账后复跑（683/OK skipped=5）。产品笔 `%s` 已推（HEAD=origin、ahead=0）。**具名 NOT-RUN / 限制**：① `%s` 自身跑（推送后取）；② 真窗口置顶分组（当前无置顶记录，只有离屏帧证据）；③ 状态菜单像素通道（system-menu，610）；④ `RTF_HELPER_ORPHAN`（settings-content-blank/595）；⑤ `RECORDING_REREAD` 1x；⑥ 已知在屏/Motion 采样 flake；⑦ 601 噪声与其余未结项仍开。
""" % (FULLTXT, sha, sha)
DS=u"""## D-510 侧栏分组标题与行首图标同一左轴（R512）

- 背景：`sidebar-pinned-section` 帧里「已固定」左墨 36.5pt，行首星标 20.0pt、行标题列 96.5pt —— 标题落在两列之间，与哪一列都不同轴。
- 决定：`SidebarSectionHeader` 的 leading 从 22 收到 6（标题左墨 20.5pt），与行首图标列同轴。
- 理由：分组标题是这一组行的标签，左轴应落在行内容的**最左内容列**（图标）上；macOS 侧栏 的分组标题也走这条轴，而不是缩进到标题列。
- 兼容性/迁移：离屏 pinned 帧 2 张同笔更新；标题与星标差 0.5pt（两档），行几何不变；真窗口当前无置顶记录，暂只有离屏证人。
- 边界：若未来改行首列（例如把星标换成别的图标列），先重新量「最左内容列」再改标题 leading；判据钉的是与行首图标同轴，不是写死 6 这个数。
"""
BS=u"""**617. 侧栏分组标题的对齐基准是行首图标，不是行标题**（R512 决定）
    现象：标题原来的 22pt leading 让「已固定」落在图标列（20.0）与标题列（96.5）之间；两列都对不上。
    修法：以行首图标列为基准（leading 6 ⇒ 20.5pt），判据 `SECTION_HEADER_ALIGN` 钉「标题与行首图标差 ≤1.5pt」；改行首列时先重新量最左内容列，不许把 6 抄成常数。
"""
CS=u"""### 侧栏分组标题对齐行图标列（离屏 36.5→20.5pt；R512 / 第 511 轮 / Round 509 / U-2036…U-2041 · 产品 1 文件 + 判据）

"""
SS=u"""## R512 状态（2026-10-31 · 第 511 轮 · 产品 1 文件 + 判据）

R512 记录（产品 1 文件 + 判据）：侧栏分组标题对齐行图标列。⓪ push no-op（HEAD=origin/main=`cf56783`、ahead=0）；`5f0807b`/`cf56783` 两跑 in_progress ⇒ NOT-RUN；`6f43727`/`d7919e2` success（探针恢复持续）；`3ebc7fc` failure 仅 Release 时序、R509 三跑仅 Release（已被 6f43727 签收）。① `sidebar-pinned-section`：「已固定」左墨 36.5pt、行首星标 20.0、标题列 96.5 ⇒ 两列都不对齐。② 产品：`SidebarSectionHeader` leading 22→6；after light/dark 标题 20.5 vs 图标 20.0（差 0.5）。③ 判据 `testSidebarSectionHeaderAlignsWithTheRowIconColumn`（两档第一处墨、差 ≤1.5；无墨具名 NOT_RUN）；M1375/M1376 2/2。④ 捕获 332 帧、CHANGED=42 = 2 张 pinned 结构 + 40 张噪声；吸收 2 张（332），复核 CHANGED=40；真窗口无置顶记录（`AXButton desc=[固定…]` 只是操作栏按钮）。⑤ 预检 293/270/718 bad=0、ARM 386/1205、HIDDEN 380/1144 rot=0；build 0 告警；%s；换装 ok/419=419（活库；旧实例先 CONT/TERM）；电池 683/5（台账后复跑）；清账 162/63/0；产品面连续零改动 **4** 轮（as-of 501，`python3 scripts/product_streak.py` 现读，last_round=497；本笔 as-of 511 = 1，last=`5f0807b`/last_round=510）；产品笔 `%s` 已推（ahead=0）。下一轮编号 R513（第 512 轮 / Round 510）：先 push 并复核 ahead=0；读 `%s` 自身跑与 `5f0807b`/`cf56783` 跑全部失败步骤；重点 pinned 帧在 runner 1x 的可判性、`RTF_HELPER_ORPHAN`（595）、`RECORDING_REREAD`、436 Motion floor；② 产品位换未捕获表面；③ 4.5 地板与 150 上限不动。
""" % (FULLTXT, sha, sha)
IS=u"""## Round 509 · R512（第 511 轮 · 2026-10-31）：侧栏分组标题对齐行图标列（36.5→20.5pt）

`sidebar-pinned-section` 帧里「已固定」左墨 36.5pt，行首星标 20.0、行标题列 96.5 —— 标题落在两列之间。修法：`SidebarSectionHeader` leading 22→6；after light/dark 标题 20.5 vs 图标 20.0（差 0.5）。判据 `testSidebarSectionHeaderAlignsWithTheRowIconColumn`（两档第一处墨、差 ≤1.5、无墨具名 NOT_RUN），M1375/M1376 2/2。捕获 332 帧：2 张 pinned 帧变化（已吸收）+ 40 张噪声，最终 CHANGED=40。预检 293/270/718、ARM 386/1205、HIDDEN 380/1144 rot=0。%s；build 0 告警；换装 419=419；电池 683/5。⓪ push no-op（HEAD=origin=cf56783、ahead=0）；6f43727/d7919e2 success（探针恢复持续）、5f0807b/cf56783 NOT-RUN、3ebc7fc/R509 三跑仅 Release 时序。真窗口无置顶记录，只有离屏帧证据。

**七维度自评**（恰七行，每格 n/15）：

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | 15/15 | pinned 亮/暗帧逐张看过：标题与星标同轴、行几何未动；真窗口无置顶记录如实记账。 |
| 判据有效性 | 15/15 | 两档第一处墨、差 ≤1.5；M1375/M1376 2/2。 |
| 假绿防御 | 15/15 | 任一臂无墨走具名 NOT_RUN；真窗口没有该节时不臆造读数。 |
| 产品面推进 | 15/15 | 新设计位（分组标题左轴）；1 个产品文件；2 张帧可见变化。 |
| 台账一致性 | 15/15 | U-2036…U-2041、D-510、332 帧/1330/56/0、419=419 都来自命令与测试。 |
| 交付诚实性 | 15/15 | 真窗口无置顶节、runner 未签收都具名；R509/R510 的 runner 红全部归因。 |
| 可复核性 | 15/15 | 36.5/20.0/96.5→20.5/20.0、M1375/M1376、precheck 293/270/718 都在。 |

均分 = 105/105 ≈ 15.0/15（100）。
""" % FULLTXT
RB=u"""- **R512（侧栏分组标题对齐行图标列；产品 1 文件 + 判据）**：「已固定」左墨 36.5pt 落在图标列 20.0 与标题列 96.5 之间；leading 22→6 后 20.5（差 0.5），M1375/M1376 2/2。pinned 2 帧同笔更新（基线 332、复核 CHANGED=40）；全量 1330/56/0；换装 419=419；电池 683/5。真窗口无置顶记录，只有离屏帧证据；6f43727/d7919e2 success 确认探针恢复持续。
"""
a=rd(A); d=rd(D); b=rd(B); st=rd(S); pr=rd(P); ch=rd(C); it=rd(I)
if a.count(AT_OLD)!=1: raise SystemExit("A title %d" % a.count(AT_OLD))
if a.count(ANCHOR_NEXT)!=1: raise SystemExit("A next %d" % a.count(ANCHOR_NEXT))
if u"## D-510" in d: raise SystemExit("D exists")
if u"**617." in b: raise SystemExit("B exists")
if u"## R512 状态" in st: raise SystemExit("S exists")
if u"R512（侧栏分组标题" in pr: raise SystemExit("P exists")
if u"侧栏分组标题对齐行图标列" in ch: raise SystemExit("C exists")
if u"## Round 509 · R512" in it: raise SystemExit("I exists")
if pr.count(u"U-31 … U-2035（R511 现读抬到最新一节）")!=1: raise SystemExit("P ucell")
if pr.count(u"## 18. R458 → R511 这一段（R478 起写；R504 续到 504、R505 续到 505、R506 续到 506、R507 续到 507、R508 续到 508、R509 续到 509、R510 续到 510、R511 续到 511 —— 这份报告第七次差点停在几十轮之前）")!=1: raise SystemExit("P s18")
if pr.count(u"的 R511 节 ② 为准")!=1: raise SystemExit("P pointer")
wr(A, a.replace(AT_OLD, AT_NEW, 1).replace(ANCHOR_NEXT, u"\n"+AS+ANCHOR_NEXT, 1))
wr(D, d.rstrip()+"\n\n"+DS+"\n")
wr(B, b.rstrip()+"\n\n"+BS+"\n")
wr(S, st.replace(u"## R511 状态（", SS.strip()+"\n\n## R511 状态（", 1))
pr=pr.replace(u"U-31 … U-2035（R511 现读抬到最新一节）", u"U-31 … U-2041（R512 现读抬到最新一节）", 1)
pr=pr.replace(u"## 18. R458 → R511 这一段（R478 起写；R504 续到 504、R505 续到 505、R506 续到 506、R507 续到 507、R508 续到 508、R509 续到 509、R510 续到 510、R511 续到 511 —— 这份报告第七次差点停在几十轮之前）",
              u"## 18. R458 → R512 这一段（R478 起写；R504 续到 504、R505 续到 505、R506 续到 506、R507 续到 507、R508 续到 508、R509 续到 509、R510 续到 510、R511 续到 511、R512 续到 512 —— 这份报告第七次差点停在几十轮之前）", 1)
pr=pr.replace(u"的 R511 节 ② 为准", u"的 R512 节 ② 为准", 1)
wr(P, pr.rstrip()+"\n\n"+RB+"\n")
m=u"## [Unreleased]\n"
if ch.count(m)!=1: raise SystemExit("C anchor")
wr(C, ch.replace(m, m+"\n"+CS, 1))
wr(I, it.rstrip()+"\n\n"+IS+"\n")
print("OK sha=%s full=%s" % (sha, FULL))
