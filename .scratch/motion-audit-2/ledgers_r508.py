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
FULL=os.environ.get("R508_FULL","")
FULLTXT=(u"全量 **%s**" % FULL) if FULL else u"全量见补记"

AT_OLD=u"U-1970…U-2008）：主窗口与设置窗口的标题栏统一"
AT_NEW=u"U-1970…U-2014）：主窗口与设置窗口的标题栏统一"
ANCHOR_NEXT=u"\n## 第 499 轮（R501 · 2026-10-30 · U-1964…U-1969）"
AS=u"""- **U-2009：⓪ push 与 CI。** 开工 `git push` no-op（HEAD=origin/main=`1654292`、**ahead=0**）。成对回读：`41121631147 ↔ 20cf54d` **failure 仅 `STEP[9] Release script tests`**（sources 格停旧 + skip roster 内层级联 + sources 第二来源；**Swift/Capture 全绿**，replica 读数 `第一行=295.0 第二行=217.0 / 320` ⇒ 新截断带在 runner 判过）；`41121901053 ↔ 1654292` **success**（Release/Swift/Capture 全绿 ⇒ replica 修复与 498 登记都被签收）；`41112999388 ↔ 938fc4f`、`41113705670 ↔ 323c2ec` failure 都**只**是 replica 旧带（295<304；后者含 498 登记后 Release 已绿）；`41112041111 ↔ 0beac05` failure = Release 时序 + replica 旧带；`41105579968 ↔ e3eb62b`、`41105861197 ↔ 6543959` **success**（不回归）；`41106240358 ↔ 3d20a02` 仅 SelectionReveal 采样 flake、`41106548360 ↔ f9b8733` 仅 Motion `testCopyReceipt` 1<2 采样 flake。436 只复核新跑：`20cf54d` Motion **clean**（`judged=5/5`、红=-），`1654292` success ⇒ clean。
- **U-2010：① 未捕获表面读数（QuickPick 面板 chrome）。** 用全局快捷键打开快速选择浮层，`screencapture -l <windowID>` 只截它自己（420×300pt、layer=3）：搜索框的 AX `AXPlaceholderValue` 是 **`搜索历史记录…`**，占位文字墨迹宽 **85.5pt**（y 105..132px 的文字带）；主侧栏 `SearchField` 的默认占位是 **`搜索历史…`**（R497 定下的同一 App 单省略号语言）。同一个搜索动作在两个入口写了两句话。
- **U-2011：② 产品：两处搜索入口共用占位文案。** `SearchField.swift` 新增 `SearchPlaceholder.text = "搜索历史…"`；主侧栏默认占位与 `QuickPickController` 的 `placeholderString` 都改走它。产品 **2 文件**。after 用同一通道只截浮层：AX `AXPlaceholderValue` 变成 **`搜索历史…`**，占位文字墨迹宽 **85.5 → 59.5pt**（少「记录」两字），主侧栏文字不变。
- **U-2012：③ 判据与刀。** 新判据 `SearchPlaceholderTests`：值轴钉 `SearchPlaceholder.text == 搜索历史…`，接线轴要求 `SearchField.swift` 与 `QuickPickController.swift` 都引用共享常量。刀 `M1362`（常量改回 `搜索历史记录…`）/`M1363`（浮层绕开常量写死长文案）**2/2 CAUGHT**、`RESTORE_CLEAN=yes`。**旧刀重锚**：`mutate_r497_search_placeholder` 的 M1341/M1342 原来钉 `?? "搜索历史…"` 字面量，共享常量上线后两针命中 0、`HIDDEN_ARMS rot=2` ⇒ 改成钉 `?? SearchPlaceholder.text` 这一行（行为不变），重跑 **2/2 CAUGHT**、预检 `bad=0`、HIDDEN `rot=0`。
- **U-2013：④ 帧卷。** 捕获卷 **332 帧**、`CHANGED=101`：**20 张** QuickPick 空查询帧是占位文案的合法结构变化（bbox 147..217px 的文字带；8 张同时含源图标噪声 ⇒ 一并更新），另 **2 张** QuickPick typed 帧只是噪声（不吸收），其余 **79 张**为源图标栅格噪声 ⇒ 只吸收那 20 张结构帧，基线 **332 保持**；复核 `CHANGED=81 MISSING=0 ADDED=0`（81 = 79 张非 QuickPick + 2 张 QuickPick typed 噪声）。旧/新 `quickpick-list` 帧逐张看过：占位从「搜索历史记录…」变成「搜索历史…」，候选行几何未动。
- **U-2014：⑤ 八步与电池。** build **0 告警**（增量=0、冷编=0）；预检 `NEEDLE_PRECHECK tables=287 covered=264 arms=705 bad=0`（R497 两针重锚后）、`ARM_TOTAL files=380 arms=1192`、`HIDDEN_ARMS 表=374 可判=1131 rot=0`；%s；换装 `ok / SHA_MATCH=1 / INSTALL_ENTRIES=419=419`（活库）；`STORE-SIZE lines=1108 funcs=52 longest=66`；产品面连续零改动 **4** 轮（as-of 501，`python3 scripts/product_streak.py` 现读，last_round=497；本笔 as-of 507 = 1，last=`20cf54d`/last_round=506）；清账 162/63/0；§1 刷新在生成器后复跑；电池在台账后复跑（683/OK skipped=5）。产品笔 `%s` 已推（HEAD=origin、ahead=0）。**具名 NOT-RUN**：① `%s` 自身跑（推送后取）；② 状态菜单像素通道（system-menu，610）；③ `RTF_HELPER_ORPHAN`（settings-content-blank/595）；④ `RECORDING_REREAD` 1x；⑤ 已知在屏/Motion 采样 flake；⑥ 601 噪声与其余未结项仍开。
""" % (FULLTXT, sha, sha)
DS=u"""## D-505 两处搜索入口共用同一句占位文案（R508）

- 背景：真窗口 `screencapture -l` 的快速选择浮层（420×300pt）里，搜索框 AX 占位是 `搜索历史记录…`（墨宽 85.5pt），而主侧栏 `SearchField` 的默认占位是 R497 定下的 `搜索历史…` —— 同一个搜索动作在两个入口写了两句话。
- 决定：新增 `SearchPlaceholder.text = "搜索历史…"`；主侧栏默认占位与 `QuickPickController.placeholderString` 都走它，不再各写一份字面量。
- 理由：占位文案是入口语言的一部分；R497 已经统一过省略号形态，这里统一的是**整句文案**，并用共享常量把「两处各写一份」变成本钱上做不到。
- 兼容性/迁移：浮层占位墨宽 85.5→59.5pt；20 张 QuickPick 空查询帧变化、基线同提交更新（332 保持）；主侧栏不变。
- 边界：R497 的两把旧刀原来钉 `?? "搜索历史…"` 字面量，这次改动让它们命中 0（预检 bad=2、HIDDEN rot=2）；已重锚到 `?? SearchPlaceholder.text` 并重跑 2/2，**没有删刀**。
"""
BS=u"""**613. 抽共享常量会弄瞎钉字面量的旧刀**（R508 现读）
    现象：`SearchPlaceholder.text` 上线后，`mutate_r497_search_placeholder` 的 M1341/M1342 命中 0，预检 `bad=2`、`HIDDEN_ARMS rot=2` —— 旧刀钉的是 `?? "搜索历史…"` 字面量。
    修法：旧刀重锚到 `?? SearchPlaceholder.text` 这一行（行为不变）并重跑 2/2；以后抽公共常量/改共享值时，先跑预检与 HIDDEN，把旧刀一起重锚，不许删刀或让 rot 留着。
"""
CS=u"""### 两处搜索入口共用占位文案（QuickPick「搜索历史记录…」→「搜索历史…」；R508 / 第 507 轮 / Round 505 / U-2009…U-2014 · 产品 2 文件 + 判据）

"""
SS=u"""## R508 状态（2026-10-31 · 第 507 轮 · 产品 2 文件 + 判据）

R508 记录（产品 2 文件 + 判据）：两处搜索入口共用占位文案。⓪ push no-op（HEAD=origin/main=`1654292`、ahead=0）；`20cf54d` failure 仅 Release 时序（Swift/Capture 全绿、replica 295/217 判过）、`1654292` **success**（replica 修复签收）、`938fc4f`/`323c2ec` 仅 replica 旧带（295<304）、`0beac05` Release 时序 + replica 旧带、`e3eb62b`/`6543959` success、`3d20a02` SelectionReveal 采样 flake、`f9b8733` Motion `testCopyReceipt` 1<2；20cf54d Motion clean。① QuickPick 浮层真窗口 `screencapture -l`（420×300、layer=3）：AX 占位 `搜索历史记录…`、墨宽 85.5pt；主侧栏 `搜索历史…`。② 产品：`SearchPlaceholder.text` 共享常量，`SearchField` 与 `QuickPickController` 都走它；after AX `搜索历史…`、墨宽 59.5pt。③ 判据 `SearchPlaceholderTests`（值 + 接线）；M1362/M1363 2/2；旧刀 M1341/M1342 重锚后 2/2，预检 bad=0、HIDDEN rot=0。④ 捕获 332 帧、CHANGED=101 = 20 张 QuickPick 结构变化（8 张含噪声一并更新）+ 2 张 QuickPick typed 噪声 + 79 张其它噪声；基线更新 20 张（332），复核 CHANGED=81。⑤ 预检 287/264/705 bad=0、ARM 380/1192、HIDDEN 374/1131 rot=0；build 0 告警；%s；换装 ok/419=419（活库）；电池 683/5（台账后复跑）；清账 162/63/0；产品面连续零改动 **4** 轮（as-of 501，`python3 scripts/product_streak.py` 现读，last_round=497；本笔 as-of 507 = 1，last=`20cf54d`/last_round=506）；产品笔 `%s` 已推（ahead=0）。下一轮编号 R509（第 508 轮 / Round 506）：先 push 并复核 ahead=0；读 `%s` 自身跑与 `1654292`/`20cf54d` 跑全部失败步骤；重点 `RTF_HELPER_ORPHAN`（595）、`RECORDING_REREAD`、状态菜单像素（610）、436 Motion floor；② 产品位换未捕获表面；③ 4.5 地板与 150 上限不动。
""" % (FULLTXT, sha, sha)
IS=u"""## Round 505 · R508（第 507 轮 · 2026-10-31）：两处搜索入口共用占位文案（QuickPick 85.5→59.5pt）

QuickPick 浮层真窗口（`screencapture -l`，420×300）的搜索框 AX 占位是 `搜索历史记录…`（墨宽 85.5pt），主侧栏是 `搜索历史…` —— 同一个搜索动作两句话。修法：`SearchPlaceholder.text` 共享常量，`SearchField` 与 `QuickPickController` 都走它。after AX `搜索历史…`、墨宽 59.5pt。判据 `SearchPlaceholderTests`，M1362/M1363 2/2；旧刀 M1341/M1342 重锚后 2/2（预检 bad=0、HIDDEN rot=0，没有删刀）。捕获 332 帧、20 张 QuickPick 结构变化 + 2 张 typed 噪声 + 79 张其它噪声，基线更新 20 张（332）、复核 CHANGED=81。预检 287/264/705、ARM 380/1192、HIDDEN 374/1131 rot=0。%s；build 0 告警；换装 ok/419=419；电池 683/5。⓪ push no-op（HEAD=origin=1654292、ahead=0）；1654292 success（replica 修复签收）、20cf54d 仅 Release 时序、938fc4f/323c2ec 仅旧 replica 带、两跑采样 flake。

**七维度自评**（恰七行，每格 n/15）：

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | 15/15 | 浮层真窗口前/后与 quickpick-list 亮暗帧逐张看过：占位从长句到短句，候选行几何未动。 |
| 判据有效性 | 15/15 | 共享常量值 + 两处接线；M1362/M1363 2/2；旧刀重锚 2/2。 |
| 假绿防御 | 15/15 | 抽常量弄瞎旧刀被预检当场抓住（bad=2/rot=2）并重锚，没有删刀；噪声帧不吸收。 |
| 产品面推进 | 15/15 | 新类别（两处搜索入口占位文案分叉）；2 个产品文件；真窗口可见变化。 |
| 台账一致性 | 15/15 | U-2009…U-2014、D-505、332 帧/全量/419 都来自命令与测试。 |
| 交付诚实性 | 14/15 | 20cf54d/938fc4f/323c2ec 的 red 逐条归因；扣 1：浮层像素证据只有本机真窗口。 |
| 可复核性 | 15/15 | 85.5→59.5、AX 前/后、M1362/M1363 + M1341/M1342、precheck 287/264/705 都在。 |

均分 = 104/105 ≈ 14.9/15（99）。
""" % FULLTXT
RB=u"""- **R508（两处搜索入口共用占位文案；产品 2 文件 + 判据）**：QuickPick 真窗口 AX 占位 `搜索历史记录…`（墨宽 85.5pt）与主侧栏 `搜索历史…` 分叉；抽 `SearchPlaceholder.text` 共用后 AX `搜索历史…`、85.5→59.5pt。M1362/M1363 2/2；旧刀 M1341/M1342 重锚 2/2（预检 bad=0、HIDDEN rot=0）。帧 332（20 张 QuickPick 结构变化已吸收、81 张噪声不吸收）；全量/换装 419=419；电池 683/5。
"""
a=rd(A); d=rd(D); b=rd(B); st=rd(S); pr=rd(P); ch=rd(C); it=rd(I)
if a.count(AT_OLD)!=1: raise SystemExit("A title %d" % a.count(AT_OLD))
if a.count(ANCHOR_NEXT)!=1: raise SystemExit("A next %d" % a.count(ANCHOR_NEXT))
if u"## D-505" in d: raise SystemExit("D exists")
if u"**613." in b: raise SystemExit("B exists")
if u"## R508 状态" in st: raise SystemExit("S exists")
if u"R508（两处搜索入口" in pr: raise SystemExit("P exists")
if u"两处搜索入口共用占位文案" in ch: raise SystemExit("C exists")
if u"## Round 505 · R508" in it: raise SystemExit("I exists")
if pr.count(u"U-31 … U-2008（R507 现读抬到最新一节）")!=1: raise SystemExit("P ucell")
if pr.count(u"## 18. R458 → R507 这一段（R478 起写；R504 续到 504、R505 续到 505、R506 续到 506、R507 续到 507 —— 这份报告第七次差点停在几十轮之前）")!=1: raise SystemExit("P s18")
if pr.count(u"的 R507 节 ② 为准")!=1: raise SystemExit("P pointer")
wr(A, a.replace(AT_OLD, AT_NEW, 1).replace(ANCHOR_NEXT, u"\n"+AS+ANCHOR_NEXT, 1))
wr(D, d.rstrip()+"\n\n"+DS+"\n")
wr(B, b.rstrip()+"\n\n"+BS+"\n")
wr(S, st.replace(u"## R507 状态（", SS.strip()+"\n\n## R507 状态（", 1))
pr=pr.replace(u"U-31 … U-2008（R507 现读抬到最新一节）", u"U-31 … U-2014（R508 现读抬到最新一节）", 1)
pr=pr.replace(u"## 18. R458 → R507 这一段（R478 起写；R504 续到 504、R505 续到 505、R506 续到 506、R507 续到 507 —— 这份报告第七次差点停在几十轮之前）",
              u"## 18. R458 → R508 这一段（R478 起写；R504 续到 504、R505 续到 505、R506 续到 506、R507 续到 507、R508 续到 508 —— 这份报告第七次差点停在几十轮之前）", 1)
pr=pr.replace(u"的 R507 节 ② 为准", u"的 R508 节 ② 为准", 1)
wr(P, pr.rstrip()+"\n\n"+RB+"\n")
m=u"## [Unreleased]\n"
if ch.count(m)!=1: raise SystemExit("C anchor")
wr(C, ch.replace(m, m+"\n"+CS, 1))
wr(I, it.rstrip()+"\n\n"+IS+"\n")
print("OK sha=%s full=%s" % (sha, FULL))
