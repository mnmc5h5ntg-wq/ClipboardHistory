#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import io, os
R=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
def rd(p): return io.open(p,encoding="utf-8").read()
def wr(p,t): io.open(p,"w",encoding="utf-8").write(t)
A=os.path.join(R,"AGENT_UI_AUDIT.md"); D=os.path.join(R,"AGENT_DECISIONS.md"); B=os.path.join(R,"AGENT_BACKLOG.md"); S=os.path.join(R,"AGENT_STATE.md"); P=os.path.join(R,"AGENT_FINAL_REPORT.md")
AT=u"## 第 497 轮（R498 · 2026-10-30"
AS=u"""## 第 498 轮（R499 · 2026-10-30 · 空轮 Round=0）：无产品变更（候选位逐个排除；未验证改动已撤回；不记完成）

- ⓪ 开工网络已恢复：`git ls-remote` 读到 remote main=`d87d258`、HEAD=origin/main、**ahead=0**（R498 两笔主笔/补记已在 remote，无需再推）。`gh` 可读：R497 跑 `40937242846 ↔ a98e65d` **failure 仅 `STEP[9] Release script tests`**（Swift 1313/80/0 绿；sources 格为补记前形态）；同跑 `SEARCH_PLACEHOLDER` **1x 签收**（light 正臂 60.0 / 负臂 70.0、dark 61.0/71.0，差 10.0pt ⇒ **BACKLOG 593 结案**），`QUICKPICK_MATCH_HIGHLIGHT` 1x 已签收；R498 跑 `41051398635 ↔ d87d258` 读时 **in_progress ⇒ NOT-RUN**（`RTF_HELPER_ORPHAN` 1x 待读）。② 候选位逐个排除（都有读数）：① **无序列表「•」**墨径 3pt（正文墨高 ~10pt）；把项目符号字号放大 1.25 倍实测把首行带从 275 顶到 281（**+3pt**，整段行距被撑高）⇒ 会移动每一行，违背“只动标记”，**改动已全部撤回**（工作树干净）；后续只能走同字号大字形或固定行高的附件，未验证。② **设置页未选中复选框边界** 222 vs 卡片 247（1.2:1）—— 这是**非活动窗口**下系统控件的灰化外观（勾选态也是灰底黑勾），属捕获通道事实，不是产品缺陷。③ **有序/任务/无序列表的正文列**实测同一起点 36.5pt，不存在参差。④ **关于页版本行**源码已是全角括号「版本 1.4.8（build 1）」，与全 App 中文括号一致，无缺陷。⑤ 其余候选（RTF 孤字行/占位符省略号/浮层命中高亮/设置说明字号/主侧栏标题图标/恢复默认图标…）均为已完成类别。⇒ **没有合法新类别：无产品文件/帧/判据/刀，未记完成**。
"""
DS=u"""## D-495 R499 空轮：候选位逐个排除，未验证改动撤回（Round=0）

- 背景：本轮要求落一个新类别；候选位搜索后全部不成立。
- 决定：① 无序列表「•」放大项目符号字号会撑高行距（实测首行带 275→281，+3pt），撤回；② 复选框边界 1.2:1 是非活动窗口系统控件的灰化外观（捕获通道事实），不改；③ 列表正文列实测一致（36.5pt）；④ 关于页版本行已是全角括号；⑤ 其余均为已完成类别。
- 理由：没有合法产品位时不许用未验证改动或捕获假象充数（R482 先例）；空轮具名、不记完成。
- 后果：无产品文件/帧/判据/刀/commit 记完成；工作树干净。
- 下一轮：候选见 BACKLOG 597（项目符号同字号大字形，须保行高）与 598（非活动窗口控件灰化事实）。
"""
BS=u"""**597. 无序列表项目符号偏小，但放大字号会撑行距**（R499 观察）
    现象：14pt 正文下「•」墨径 3pt（正文墨高 ~10pt）；把 marker 字号放大 1.25 倍，首行带 275→281（+3pt），整段行距被撑高。
    修法：若要放大，只能换**同字号更大字形**（如 U+25CF 但需设计确认）或固定行高的附件；采纳前先拿两臂证明正文列/行距不变。

**598. 非活动窗口下系统控件边界被灰化（捕获事实）**（R499 观察）
    现象：未选中复选框 222 vs 卡片 247（1.2:1），勾选态也是灰底黑勾；这是离屏窗口非 key 时的系统外观。
    修法：不要用离屏帧判系统控件边界对比度；要判需真机活动窗口或自定义控件。
"""
SS=u"""## R499 状态（2026-10-30 · 本地 · 第 498 轮 · 空轮 Round=0）：无产品变更（候选位逐个排除；未验证改动已撤回，不记完成）

最后更新：2026-10-30（本地 · R499 / 空轮 Round=0）：⓪ 开工网络已恢复：`git ls-remote` 读到 remote main=`d87d258`、HEAD=origin/main、**ahead=0**（R498 两笔已在 remote）；`gh` 可读：R497 跑 `40937242846 ↔ a98e65d` **failure 仅 Release**（Swift 1313/80/0 绿；`SEARCH_PLACEHOLDER` 1x light 60/70、dark 61/71 差 10.0pt ⇒ **593 结案**；`QUICKPICK_MATCH_HIGHLIGHT` 1x 已签收）；R498 跑 `41051398635 ↔ d87d258` **in_progress ⇒ NOT-RUN**（`RTF_HELPER_ORPHAN` 1x 待读）。② 候选位逐个排除（都有读数）：无序列表「•」墨径 3pt，放大 1.25 倍会把首行带 275→281（+3pt、整段行距被撑高）⇒ **撤回**；未选中复选框 1.2:1 是非活动窗口系统控件灰化（捕获事实）；有序/任务/无序列表正文列同为 36.5pt；关于页版本行已是全角括号；其余均为已完成类别。**没有合法新类别 ⇒ 无产品文件/帧/判据/刀，不记完成**；工作树干净、HEAD=origin/main=`d87d258`。下一轮（R500）靶：① 先 `git push origin main`（无待推则 no-op）并复核 ahead=0；读 R498 跑 `41051398635`（`RTF_HELPER_ORPHAN` 1x/595）、R497 跑、R496 跑及更早各跑全部失败步骤；重点 `RTF_HELPER_ORPHAN`（正臂 ≥22pt、负臂 ≤18pt）、`SEARCH_PLACEHOLDER` 1x 已签收、`QUICKPICK_MATCH_HIGHLIGHT` 1x 已签收、`SETTINGS_HELPER_FONT`、`MAIN_TITLE_ICON`、`RESET_ICON`、`LOGIN_FAILURE_ICON`、`DEFAULT_BADGE`、inline 4.5/150 不动；② **必须换新类别**——候选：BACKLOG 597 的项目符号同字号大字形（须先证行距不变）或新一轮真实窗口/未捕获表面的缺陷；③ 436 只复核新跑 Motion floor。
"""
RB=u"""- **R499（空轮 Round=0，不记完成）**：候选位逐个排除——无序列表「•」放大字号会把行距撑高 3pt（已撤回）；复选框边界 1.2:1 是非活动窗口灰化（捕获事实）；列表正文列同 36.5pt；关于页版本行已全角括号；其余均为已完成类别。无产品变更。⓪ 网络恢复，remote main=`d87d258`、ahead=0；R497 跑 failure 仅 Release（Swift 1313/80/0 绿；SEARCH_PLACEHOLDER 1x 签收 ⇒ 593 结案）；R498 跑 in_progress ⇒ NOT-RUN。
"""
a=rd(A); d=rd(D); b=rd(B); st=rd(S); pr=rd(P)
if a.count(AT)!=1: raise SystemExit('A')
if u"## D-495" in d: raise SystemExit('D')
if u"**597." in b: raise SystemExit('B')
if st.count(u"## R498 状态")!=1: raise SystemExit('S')
wr(A,a.replace(AT,AS+AT,1)); wr(D,d.rstrip()+"\n\n"+DS+"\n"); wr(B,b.rstrip()+"\n\n"+BS+"\n")
wr(S,st.replace(u"## R498 状态",SS+u"## R498 状态",1)); wr(P,pr.rstrip()+"\n\n"+RB+"\n"); print("OK")
