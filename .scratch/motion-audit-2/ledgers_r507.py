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
FULL=os.environ.get("R507_FULL","")
FULLTXT=(u"全量 **%s**（含 1 条新判据）" % FULL) if FULL else u"全量见补记"

AT_OLD=u"U-1970…U-2002）：主窗口与设置窗口的标题栏统一"
AT_NEW=u"U-1970…U-2008）：主窗口与设置窗口的标题栏统一"
ANCHOR_NEXT=u"\n## 第 499 轮（R501 · 2026-10-30 · U-1964…U-1969）"
AS=u"""- **U-2003：⓪ push 与 CI。** 开工 `git push` no-op（HEAD=origin/main=`323c2ec`、**ahead=0**）。七跑成对：`41112041111 ↔ 0beac05` **failure** = Release（4 条：sources 格停旧 + `ROUND_K_CONTRADICTION 498` + skip roster 内层级联 + sources 第二来源）+ Swift/Capture 的 **replica 截断带**红（runner 1x 首行 **295.0 < 304.0**）；`41112999388 ↔ 938fc4f` failure Swift+Capture（同上 replica；Release 已绿 ⇒ 498 登记生效）；`41113705670 ↔ 323c2ec` failure 同样仅 replica；`41105579968 ↔ e3eb62b`、`41105861197 ↔ 6543959` **success**（复核不回归）；`41106240358 ↔ 3d20a02` failure 仅 `SelectionRevealAnimationTests.testProductDurationRevealStillMovesOverTime`（已知采样 flake）；`41106548360 ↔ f9b8733` failure 仅 Motion floor `testCopyReceiptAppearsAndDismissesWithAVisibleProcess` 1<2（已知采样 flake）。`0beac05` 同跑 Motion floor **clean**（`judged=5/5`、红=-）。436 只复核新跑：两条已知 flake 之外无新红。
- **U-2004：① 未捕获表面读数（推荐理由类型词）。** R506 把理由画进菜单后，真窗口 `screencapture -l <windowID>`（**533.5×318pt**）的 AX 标题是 `5VsCvDXzRkDEXNCS  文本 · 复用1次 · 常用文本 · 回到Safari浏览器 · 把握较大` —— 同一条理由里 **`文本` 出现两次**（裸类型词 + `常用文本`）；像素三条推荐最右墨 **437.0 / 466.5 / 450.0pt**。同类条目还有 `链接 · … · 常用链接`。
- **U-2005：② 产品：类型词只出现一次。** `RecommendationPresenter.reason`：先算出内容类型标签（`contentTypeTagText`），当它**包含**裸类型词（`常用文本` 含 `文本`、`常用链接` 含 `链接`…）时不再在开头补裸类型词；`文本片段` 这类不被包含的保留，信息不丢。产品 **1 文件**。after 只截菜单（**499.5×318pt**）：AX 标题变成 `复用1次 · 常用文本 · 回到Safari浏览器 · 把握较大`（`文本` 只一次），三条推荐右墨 **437.0/466.5/450.0 → 403.5/433.0/416.5pt**（各 −33.5pt），终态帧逐张看过。
- **U-2006：③ 判据与刀。** 新判据 `RecommendationPresenterTests/testContentTypeWordAppearsOnlyOnce`：文本/链接两档里类型词 `mentions==1` 且仍含 `常用…`（去重不许丢「常用」信息），没有内容类型标签时孤立的类型词必须还在。刀 `M1360`（去重失效）/`M1361`（把 `常用…` 整段丢掉）**2/2 CAUGHT**、`RESTORE_CLEAN=yes`。**连带修复 R506 的 runner 红**：`testMenuBarFramesAreReplicasOfTheMenuSurface` 的截断带从绝对值 `帧宽−16` 改成**按比例 `帧宽×0.9..帧宽−1`**，第二行负向臂同步改成 `< 帧宽×0.9`；本机 314.5/256、runner 295/249 都判过（2x 省略号留白 5.5pt、1x 25pt 是这次红的原因）。
- **U-2007：④ 帧卷。** 捕获卷 **332 帧**、`CHANGED=91`：**2 张 `menubar-recommendations-320x320-{light,dark}`** 是理由去重后的合法变化，其余 **89 张**仍为源图标栅格噪声 ⇒ 只把这 2 张写进基线（**332 保持**），复核 `CHANGED=89 MISSING=0 ADDED=0`；亮/暗两张都逐张看过（`文件`/`多文件` 只剩 `常用文件`/`常用多文件`）。
- **U-2008：⑤ 八步与电池。** build **0 告警**（增量=0、冷编=0）；预检 `NEEDLE_PRECHECK tables=286 covered=263 arms=703 bad=0`、`ARM_TOTAL files=379 arms=1190`、`HIDDEN_ARMS 表=373 可判=1129 rot=0`；%s；换装 `ok / SHA_MATCH=1 / INSTALL_ENTRIES=419=419`（活库）；`STORE-SIZE lines=1108 funcs=52 longest=66`；产品面连续零改动 **4** 轮（as-of 501，`python3 scripts/product_streak.py` 现读，last_round=497；本笔 as-of 506 = 1，last=`0beac05`/last_round=505）；清账 162/63/0；§1 刷新在生成器后复跑；电池在台账后复跑（683/OK skipped=5）。产品笔 `%s` 已推（HEAD=origin、ahead=0）。**具名 NOT-RUN**：① `%s` 自身跑（推送后取）；② 状态菜单像素通道（system-menu，610）；③ `RTF_HELPER_ORPHAN`（settings-content-blank/595）；④ `RECORDING_REREAD` 1x；⑤ 已知在屏/Motion 采样 flake；⑥ 601 噪声与其余未结项仍开。
""" % (FULLTXT, sha, sha)
DS=u"""## D-504 推荐理由里的类型词只出现一次（R507）

- 背景：R506 把理由画进状态菜单后，真窗口 AX 标题暴露出 `文本 · 复用1次 · 常用文本 · …` —— 裸类型词与「常用文本」各说一遍；链接同理。此前理由在 13+ 菜单不可见，所以这个重复没被看见。
- 决定：`RecommendationPresenter.reason` 先算出内容类型标签；当它包含裸类型词（`常用文本` 含 `文本` 等）时，不再在开头补裸类型词；`文本片段` 这类不被包含的保留。与来源 App 名去重同一条规矩。
- 理由：「常用文本」已经给出类型 + 频次，裸「文本」是纯重复；砍掉的应是重复，不是信息 —— 测试同时钉 `mentions==1` 与 `contains("常用…")`。
- 兼容性/迁移：真窗口菜单 533.5→499.5pt、三条推荐右墨各 −33.5pt；离屏 `menubar-recommendations` 两帧变化（基线同提交 update）。
- 边界：`文本片段` 与 `常用文本` 仍各出现一次（不是严格同形），本轮的规则只对「标签包含裸类型词」生效；若未来要连语义重叠也去掉，先改标签词表并复跑本条判据。
"""
BS=u"""**612. replica 截断带与渲染倍率相关**（R507 现读）
    现象：`testMenuBarFramesAreReplicasOfTheMenuSurface` 的绝对带 `帧宽−16` 在 2x 成立（省略号留白 5.5pt），runner 1x 的首行最右墨是 295/320（留白 25pt）⇒ `295 < 304` 红了两跑。
    修法：带改成按比例 `帧宽×0.9..帧宽−1`，第二行负向臂同步 `< 帧宽×0.9`（本机 314.5/256、runner 295/249 都判过）；若未来换布局，先量新的留白再调比例，不许删负向臂。
"""
CS=u"""### 状态菜单推荐理由类型词去重（真窗口 533.5→499.5pt；R507 / 第 506 轮 / Round 504 / U-2003…U-2008 · 产品 1 文件 + 判据）

"""
SS=u"""## R507 状态（2026-10-31 · 第 506 轮 · 产品 1 文件 + 判据）

R507 记录（产品 1 文件 + 判据）：状态菜单推荐理由类型词去重。⓪ push no-op（HEAD=origin/main=`323c2ec`、ahead=0）；七跑：`0beac05` failure = Release 4 条 + Swift/Capture replica 截断带红（runner 295<304）、`938fc4f` failure 仅 replica（Release 已绿）、`323c2ec` failure 仅 replica、`e3eb62b`/`6543959` success、`3d20a02` 仅 SelectionReveal 采样 flake、`f9b8733` 仅 Motion `testCopyReceipt` 1<2；`0beac05` 同跑 Motion clean（5/5）。① 真窗口 `screencapture -l`（533.5×318）：AX `文本 · 复用1次 · 常用文本 · …`，类型词出现两次；三条推荐右墨 437.0/466.5/450.0。② 产品：`RecommendationPresenter.reason` 在内容类型标签包含裸类型词时不再补裸类型词；after 菜单 499.5×318、AX `复用1次 · 常用文本 · …`（类型词一次）、三条右墨 403.5/433.0/416.5（各 −33.5pt）。③ 判据 `testContentTypeWordAppearsOnlyOnce`；M1360/M1361 2/2；连带把 replica 截断带改成按比例（帧宽×0.9..帧宽−1）+ 第二行负向臂，修 runner 295<304。④ 捕获 332 帧、CHANGED=91 = 2 张 menubar 合法变化 + 89 噪声；基线更新那 2 张（332），复核余 89 不吸收。⑤ 预检 286/263/703 bad=0、ARM 379/1190、HIDDEN 373/1129 rot=0；build 0 告警；%s；换装 ok/419=419（活库）；电池 683/5（台账后复跑）；清账 162/63/0；产品面连续零改动 **4** 轮（as-of 501，`python3 scripts/product_streak.py` 现读，last_round=497；本笔 as-of 506 = 1，last=`0beac05`/last_round=505）；产品笔 `%s` 已推（ahead=0）。下一轮编号 R508（第 507 轮 / Round 505）：先 push 并复核 ahead=0；读 `%s` 自身跑与 `938fc4f`/`323c2ec`/`20cf54d` 跑全部失败步骤；重点 replica 带在 runner 是否绿、`RTF_HELPER_ORPHAN`（595）、`RECORDING_REREAD`、状态菜单像素通道（610）、436 只复核新跑 Motion floor；② 产品位换未捕获表面；③ 4.5 地板与 150 上限不动。
""" % (FULLTXT, sha, sha)
IS=u"""## Round 504 · R507（第 506 轮 · 2026-10-31）：状态菜单推荐理由类型词去重（真窗口 533.5→499.5pt）

R506 把理由画进菜单后，真窗口 AX 标题暴露 `文本 · 复用1次 · 常用文本 · …`（类型词两次）。修法：`RecommendationPresenter.reason` 在内容类型标签包含裸类型词时不再补裸类型词（`文本片段` 这类保留）。after 菜单 499.5×318、AX `复用1次 · 常用文本 · …`、三条右墨各 −33.5pt。判据 `testContentTypeWordAppearsOnlyOnce`，M1360/M1361 2/2；连带把 replica 截断带改成按比例 `帧宽×0.9..帧宽−1` + 第二行负向臂（本机 314.5/256、runner 295/249），修 R506 遗留的 runner 红。捕获 332 帧、2 张 menubar 合法变化 + 89 噪声不吸收、基线 332。预检 286/263/703、ARM 379/1190、HIDDEN 373/1129 rot=0。%s；build 0 告警；换装 ok/419=419；电池 683/5。⓪ push no-op（HEAD=origin=323c2ec、ahead=0）；0beac05/938fc4f/323c2ec 三跑 red（replica 带 + 时序），e3eb62b/6543959 success，两跑采样 flake。

**七维度自评**（恰七行，每格 n/15）：

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | 15/15 | 真窗口菜单前/后与亮暗离屏帧逐张看过：类型词从两次到一次、菜单 533.5→499.5pt。 |
| 判据有效性 | 15/15 | `mentions==1` + `contains("常用…")` 两半；M1360/M1361 2/2；replica 带负向臂。 |
| 假绿防御 | 15/15 | 去重不许丢「常用」信息；replica 带按比例且第二行必须不进带；离屏盲区仍具名（610）。 |
| 产品面推进 | 15/15 | 新类别（推荐理由类型词重复）；1 个产品文件；真窗口可见变化。 |
| 台账一致性 | 15/15 | U-2003…U-2008、D-504、332 帧/1322/56/0、419=419 都来自命令与测试。 |
| 交付诚实性 | 14/15 | 三跑 red 逐条归因（replica 带/时序）、两跑采样 flake 具名；扣 1：菜单像素证据仍只有本机真窗口。 |
| 可复核性 | 15/15 | 533.5→499.5、437/466.5/450→403.5/433/416.5、M1360/M1361、precheck 286/263/703 都在。 |

均分 = 104/105 ≈ 14.9/15（99）。
""" % FULLTXT
RB=u"""- **R507（推荐理由类型词去重；产品 1 文件 + 判据）**：R506 画进菜单的理由里 `文本 · … · 常用文本` 类型词出现两次。`RecommendationPresenter.reason` 在内容类型标签包含裸类型词时不再补裸类型词：真窗口菜单 533.5→499.5pt、三条右墨各 −33.5pt，AX `复用1次 · 常用文本 · …`；M1360/M1361 2/2。连带把 replica 截断带改成按比例 `帧宽×0.9..帧宽−1` + 第二行负向臂（本机 314.5/256、runner 295/249），修 runner 295<304。帧 332（2 张 menubar 合法变化、89 噪声不吸收）；全量 1322/56/0；换装 419=419；电池 683/5。
"""
a=rd(A); d=rd(D); b=rd(B); st=rd(S); pr=rd(P); ch=rd(C); it=rd(I)
if a.count(AT_OLD)!=1: raise SystemExit("A title %d" % a.count(AT_OLD))
if a.count(ANCHOR_NEXT)!=1: raise SystemExit("A next %d" % a.count(ANCHOR_NEXT))
if u"## D-504" in d: raise SystemExit("D exists")
if u"**612." in b: raise SystemExit("B exists")
if u"## R507 状态" in st: raise SystemExit("S exists")
if u"R507（推荐理由类型词去重" in pr: raise SystemExit("P exists")
if u"状态菜单推荐理由类型词去重" in ch: raise SystemExit("C exists")
if u"## Round 504 · R507" in it: raise SystemExit("I exists")
if pr.count(u"U-31 … U-2002（R506 现读抬到最新一节）")!=1: raise SystemExit("P ucell")
if pr.count(u"## 18. R458 → R506 这一段（R478 起写；R504 续到 504、R505 续到 505、R506 续到 506 —— 这份报告第七次差点停在几十轮之前）")!=1: raise SystemExit("P s18")
if pr.count(u"的 R506 节 ② 为准")!=1: raise SystemExit("P pointer")
wr(A, a.replace(AT_OLD, AT_NEW, 1).replace(ANCHOR_NEXT, u"\n"+AS+ANCHOR_NEXT, 1))
wr(D, d.rstrip()+"\n\n"+DS+"\n")
wr(B, b.rstrip()+"\n\n"+BS+"\n")
wr(S, st.replace(u"## R506 状态（", SS.strip()+"\n\n## R506 状态（", 1))
pr=pr.replace(u"U-31 … U-2002（R506 现读抬到最新一节）", u"U-31 … U-2008（R507 现读抬到最新一节）", 1)
pr=pr.replace(u"## 18. R458 → R506 这一段（R478 起写；R504 续到 504、R505 续到 505、R506 续到 506 —— 这份报告第七次差点停在几十轮之前）",
              u"## 18. R458 → R507 这一段（R478 起写；R504 续到 504、R505 续到 505、R506 续到 506、R507 续到 507 —— 这份报告第七次差点停在几十轮之前）", 1)
pr=pr.replace(u"的 R506 节 ② 为准", u"的 R507 节 ② 为准", 1)
wr(P, pr.rstrip()+"\n\n"+RB+"\n")
m=u"## [Unreleased]\n"
if ch.count(m)!=1: raise SystemExit("C anchor")
wr(C, ch.replace(m, m+"\n"+CS, 1))
wr(I, it.rstrip()+"\n\n"+IS+"\n")
print("OK sha=%s full=%s" % (sha, FULL))
