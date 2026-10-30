#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import io, os
R=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
def rd(p): return io.open(p,encoding="utf-8").read()
def wr(p,t): io.open(p,"w",encoding="utf-8").write(t)
A=os.path.join(R,"AGENT_UI_AUDIT.md"); D=os.path.join(R,"AGENT_DECISIONS.md"); B=os.path.join(R,"AGENT_BACKLOG.md"); S=os.path.join(R,"AGENT_STATE.md"); P=os.path.join(R,"AGENT_FINAL_REPORT.md"); C=os.path.join(R,"CHANGELOG.md")
AT=u"## 第 499 轮（R501 · 2026-10-30"
AS=u"""## 第 501 轮（R502 · 2026-10-30 · U-1970…U-1975）：主窗口标题栏标题策略（真窗口表面；产品 1 文件 + 判据）

- **U-1970：⓪ push 与 CI。** 开工 `git push` no-op（HEAD=origin/main=`ec299eb`、ahead=0）。`41068373712 ↔ dac7e17` 读时 in_progress（STEP[9] 已红）⇒ NOT-RUN；`41062934158 ↔ 79eb4fb` failure Release 2 条（hygiene + 内层 skip roster，已由 817a014 修）；`41063726929 ↔ 817a014` failure 仅 Motion `testCopyReceiptAppearsAndDismissesWithAVisibleProcess`（已知采样 flake；Swift/Capture 绿：15.8 键一致、录制帧 12/11）。436 沿用 R481 跑 reds=0。
- **U-1971：① 真实窗口表面与读数。** 走产品入口（⌘S「显示主窗口」）打开主窗口，用 `screencapture -R` 只截该窗口矩形：**标题栏是空的**（窗口 `title="时间剪史"` 但未画出，应用名只在侧栏标题）。为验证「画出 title 会怎样」，临时把 `titleVisibility` 设为 `.visible` 并换装实拍：title 出现在窗口中央、**压在详情头部来源图标上方**（实拍可见），说明这个空白不是缺字，而是自定义标题栏的设计。
- **U-1972：② 产品：把「标题不画」写成显式契约。** 修法：`WindowConfigurator` 显式 `window.title = "时间剪史"` + `window.titleVisibility = .hidden`（title 字符串保留给 Mission Control/读屏；像素与此前一致，但不再依赖系统默认）。产品 1 文件；离屏帧不变。
- **U-1973：③ 判据与刀。** 新 `testMainWindowHidesItsTitlebarTitleButKeepsTheName`（挂产品 `WindowConfigurator` 的真窗口）：断言 `titleVisibility == .hidden`、`title == "时间剪史"`。刀 `M1347`（改 `.visible`）/`M1348`（title 清空）**2/2 CAUGHT**、`RESTORE_CLEAN=yes`。
- **U-1974：④ 帧卷与实拍边界。** 捕获卷 **330 帧**、89 张 changed 仍为源图标栅格噪声（16×16px、最大差 7/255）⇒ **不入基线**；第二次实拍时屏幕被其他应用占据，**未截取非 App 区域**，改用早前同构帧（title 隐藏）作最终态证据。
- **U-1975：⑤ 八步与电池。** build **0 告警**（arm64 冷编）；预检 **281/258/690 bad=0**、ARM **374/1177**、HIDDEN **368/1116 rot=0**；全量 **1316/56/0**（678.0s）；换装 `ok / SHA_MATCH=1 / INSTALL_ENTRIES=419=419`（活库 419 条，非产品增删）；电池在台账后复跑；清账 162/63/0。收口 push 见补记。
"""
DS=u"""## D-498 主窗口标题栏：title 保留、标题显式隐藏（R502）

- 背景：真窗口帧里标题栏空白；临时显式画出 title 后，它与详情头部来源图标重叠（实拍可见）。
- 决定：`WindowConfigurator` 显式 `title = "时间剪史"`、`titleVisibility = .hidden`，把自定义标题栏写成契约；title 字符串留给 Mission Control/读屏。
- 理由：空白标题栏是设计（应用名在侧栏标题），不是缺字；显式隐藏可防系统默认/未来 OS 把 title 画出来压住详情。
- 兼容性/迁移：像素不变；新增真窗口值判据 `testMainWindowHidesItsTitlebarTitleButKeepsTheName` 与 M1347/M1348。
- 边界：实拍通道在屏幕被占用时不可用；后续用 `screencapture -l` 或先确认 App 在前台，不截非 App 区域。
"""
BS=u"""**603. 真实窗口实拍通道会被其他应用/空间占住**（R502 观察）
    现象：同一 `-R` 矩形第二次截到的是别的应用（屏幕已切走）；未截取非 App 区域。
    修法：优先用 `screencapture -l <windowID>` 只截目标窗口；或在截图前确认 App 前台与窗口 id，读不到就具名 NOT-RUN。

**604. 主窗口标题栏的「空白」是设计而非缺字**（R502 结论）
    现象：窗口 title 存在但未画；强行画出会与详情头部重叠。
    修法：保持 `titleVisibility = .hidden`；若未来要显示标题，先改详情头部让位并从真窗口帧测重叠。
"""
CS=u"""### 主窗口标题栏标题策略：title 保留、标题显式隐藏（R502 / 第 501 轮 / U-1970…U-1975 · 产品 1 文件 + 判据）

"""
SS=u"""R502 记录（产品 1 文件 + 判据）：主窗口标题栏 title 保留、标题显式隐藏。⓪ push no-op、HEAD=origin=`ec299eb`、ahead=0；`41068373712 ↔ dac7e17` in_progress ⇒ NOT-RUN；`41062934158 ↔ 79eb4fb` Release 2 条（已由 817a014 修）、`41063726929 ↔ 817a014` 仅 Motion 采样 flake。① 真窗口实拍：标题栏空白；临时 `.visible` 实拍 title 压在详情头部上方 ⇒ 空白是设计。② 产品：`WindowConfigurator` 显式 `title="时间剪史"` + `titleVisibility=.hidden`（像素不变，写死契约）。③ 判据 `testMainWindowHidesItsTitlebarTitleButKeepsTheName`；M1347/M1348 **2/2**。④ 捕获 330 帧、89 张仍为源图标噪声（不入基线）；第二次实拍被其他应用占屏，未截非 App 区域。⑤ 预检 281/258/690、ARM 374/1177、HIDDEN 368/1116 rot=0；build 0 告警；全量 **1316/56/0**；换装 ok/419=419（活库）；电池 683/5；清账 162/63/0。下一轮编号 R503（第 502 轮 / Round 500）：push 并复核 ahead=0；读 R502 自身跑与 dac7e17/79eb4fb/817a014 跑；② 产品位换未捕获表面（真实窗口 `-l` 通道或新设计位）；③ 436 只复核新跑 Motion floor。
"""
RB=u"""- **R502（主窗口标题栏标题策略；产品 1 文件 + 判据）**：真窗口里 title 未画；临时 `.visible` 实拍与详情头部重叠 ⇒ 空白是设计。改为显式 `title="时间剪史"` + `titleVisibility=.hidden`；新值判据 + M1347/M1348 2/2；像素不变。捕获 330 帧 89 张源图标噪声不入基线；预检 281/258/690、全量 1316/56/0；换装 ok/419=419；电池 683/5。
"""
a=rd(A); d=rd(D); b=rd(B); st=rd(S); pr=rd(P); ch=rd(C)
if a.count(AT)!=1: raise SystemExit('A')
if u"## D-498" in d: raise SystemExit('D')
if u"**603." in b: raise SystemExit('B')
if u"R502 记录" in st: raise SystemExit('S')
if u"R502（主窗口标题栏" in pr: raise SystemExit('P')
if u"主窗口标题栏标题策略" in ch: raise SystemExit('C')
wr(A,a.replace(AT,AS+AT,1)); wr(D,d.rstrip()+"\n\n"+DS+"\n"); wr(B,b.rstrip()+"\n\n"+BS+"\n")
wr(S,st.replace(u"## R498 状态",SS.strip()+"\n\n## R498 状态",1))
pr=pr.replace(u"U-31 … U-1969（R501 现读抬到最新一节）",u"U-31 … U-1975（R502 现读抬到最新一节）",1)
wr(P,pr.rstrip()+"\n\n"+RB+"\n")
m=u"## [Unreleased]\n"
if ch.count(m)!=1: raise SystemExit('C2')
wr(C,ch.replace(m,m+"\n"+CS,1))
print("OK")
