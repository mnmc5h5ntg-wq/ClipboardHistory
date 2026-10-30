#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import io, os
R=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
def rd(p): return io.open(p,encoding="utf-8").read()
def wr(p,t): io.open(p,"w",encoding="utf-8").write(t)
A=os.path.join(R,"AGENT_UI_AUDIT.md"); D=os.path.join(R,"AGENT_DECISIONS.md"); B=os.path.join(R,"AGENT_BACKLOG.md"); S=os.path.join(R,"AGENT_STATE.md"); P=os.path.join(R,"AGENT_FINAL_REPORT.md"); C=os.path.join(R,"CHANGELOG.md")
AT=u"## 第 501 轮（R502 · 2026-10-30"
AS=u"""## 第 502 轮（R503 · 2026-10-30 · U-1976…U-1981）：设置窗口标题栏与主窗口统一（真窗口表面；产品 1 文件 + 判据）

- **U-1976：⓪ push 与 CI。** 开工 `git push` no-op、HEAD=origin/main=`2c14a48`、**ahead=0**。`41074949020 ↔ 1633a9d`、`41077528140 ↔ 58cc884`、`41077659382 ↔ 2c14a48` 读时均 **in_progress ⇒ NOT-RUN**；更早：`41063726929 ↔ 817a014` failure 仅 Motion 采样红、`41062934158 ↔ 79eb4fb` Release 2 条已由 817a014 修、`41068373712 ↔ dac7e17` Release 唯一红为旧 skip roster（cutoff 修复前）。436 沿用 R481 跑 reds=0。
- **U-1977：① 真窗口读数。** 走产品入口打开设置窗口并用 `screencapture -l <windowID>` 只截该窗口：设置窗口标题栏画着「设置」标题（标题带墨 **1915**，标题文字 bbox 到 x=329）并有一条通栏分隔线；同一 App 的主窗口是无标题、无分隔线的自定义 chrome（R502）—— 两扇窗口两套标题栏语言。
- **U-1978：② 产品：统一设置窗口的标题栏。** `SettingsWindowController`：`titleVisibility = .hidden`、`titlebarAppearsTransparent = true`、`titlebarSeparatorStyle = .none`，title 字符串保留。产品 1 文件；离屏帧不变（设置窗口 chrome 不进离屏帧）。
- **U-1979：③ 复拍/判据/刀。** after 只截设��窗口：标题带墨 **1915 → 1210**（余下 1210 是红绿灯本体，标题文字 bbox 消失），通栏分隔线不再出现。新判据 `testSettingsWindowUsesTheSameCustomChromeAsTheMainWindow`（构造产品 `SettingsWindowController` 并 `show()`）：title=设置、titleVisibility hidden、separator none。刀 `M1350`（visible）/`M1351`（separator .line）**2/2 CAUGHT**、`RESTORE_CLEAN=yes`。
- **U-1980：④ 帧卷。** 捕获卷 **330 帧**、89 张 changed 仍为源图标栅格噪声（16×16、差 7/255）⇒ **不入基线**。
- **U-1981：⑤ 八步与电池。** build **0 告警**（arm64 冷编）；预检 **282/259/693 bad=0**、ARM **375/1180**、HIDDEN **369/1119 rot=0**；全量 **1317/56/0**（711.7s）；换装 `ok / SHA_MATCH=1 / INSTALL_ENTRIES=419=419`（活库）；电池在台账后复跑；清账 162/63/0。收口 push 见补记。
"""
DS=u"""## D-499 设置窗口与主窗口共用同一套自定义标题栏（R503）

- 背景：主窗口已是自定义 chrome（title 保留不画、无系统分隔线）；设置窗口仍画「设置」标题和通栏分隔线（真窗口实拍：标题带墨 1915、有分隔线）。
- 决定：`SettingsWindowController` 设 `titleVisibility = .hidden`、`titlebarAppearsTransparent = true`、`titlebarSeparatorStyle = .none`，title 保留给 Mission Control/读屏。
- 理由：同一 App 的两扇窗口要一套标题栏语言；设置页自己的标题（快捷键/通用/…）已提供层级，窗口标题是重复信息。
- 兼容性/迁移：离屏帧不变；新增真窗口值判据 + M1350/M1351；after 标题带墨 1915→1210（余下为红绿灯）。
- 边界：真窗口实拍须用 `-l <windowID>`（R502/R503 教训）；屏幕被占时不要截非 App 区域。
"""
BS=u"""**606. 设置窗口的自定义标题栏策略要随主窗口一起改**（R503 结论）
    现象：主窗口隐藏标题/去分隔线（R502）后，设置窗口仍画「设置」标题与通栏分隔线；两扇窗口两套语言。
    修法：两扇窗口的 chrome 常量放进同一处（标题可见性/分隔线/透明），新增窗口时复用；当前由两条值判据分别钉住（R502/R503）。
"""
CS=u"""### 设置窗口标题栏与主窗口统一（真窗口表面；产品 1 文件 + 判据）（R503 / 第 502 轮 / U-1976…U-1981）

"""
SS=u"""R503 记录（产品 1 文件 + 判据）：设置窗口标题栏与主窗口统一。⓪ push no-op、HEAD=origin=`2c14a48`、ahead=0；1633a9d/58cc884/2c14a48 三跑读时均 in_progress ⇒ NOT-RUN。① 真窗口：设置窗口有「设置」标题（标题带墨 1915）与通栏分隔线，主窗口无 ⇒ 两套语言。② 产品：`SettingsWindowController` 设 titleVisibility=.hidden、titlebarAppearsTransparent、separator=.none（title 保留）。③ after 标题带墨 1915→1210（余下为红绿灯）、分隔线消失；新判据 `testSettingsWindowUsesTheSameCustomChromeAsTheMainWindow`；M1350/M1351 **2/2**。④ 捕获 330 帧、89 张源图标噪声不入基线。⑤ 预检 282/259/693、ARM 375/1180、HIDDEN 369/1119 rot=0；build 0 告警；全量 **1317/56/0**；换装 ok/419=419（活库）；电池 683/5；清账 162/63/0。下一轮编号 R504（第 503 轮 / Round 501）：push 并复核 ahead=0；读 R503 自身跑与 1633a9d/58cc884/2c14a48 跑；② 产品位换未捕获表面；③ 436 只复核新跑 Motion floor。
"""
RB=u"""- **R503（设置窗口标题栏统一；产品 1 文件 + 判据）**：设置窗口原来画「设置」标题（真帧标题带墨 1915）与通栏分隔线，主窗口无 ⇒ 两套 chrome。改为 titleVisibility=.hidden + 透明标题栏 + separator=.none（title 保留）；after 标题带墨 1915→1210（余下红绿灯）、分隔线消失。值判据 + M1350/M1351 2/2。离屏帧不变；全量 1317/56/0；换装 ok/419=419；电池 683/5。
"""
a=rd(A); d=rd(D); b=rd(B); st=rd(S); pr=rd(P); ch=rd(C)
if a.count(AT)!=1: raise SystemExit('A')
if u"## D-499" in d: raise SystemExit('D')
if u"**606." in b: raise SystemExit('B')
if u"R503 记录" in st: raise SystemExit('S')
if u"R503（设置窗口标题栏" in pr: raise SystemExit('P')
if u"设置窗口标题栏与主窗口统一" in ch: raise SystemExit('C')
wr(A,a.replace(AT,AS+AT,1)); wr(D,d.rstrip()+"\n\n"+DS+"\n"); wr(B,b.rstrip()+"\n\n"+BS+"\n")
wr(S,st.replace(u"## R498 状态",SS.strip()+"\n\n## R498 状态",1))
pr=pr.replace(u"U-31 … U-1975（R502 现读抬到最新一节）",u"U-31 … U-1981（R503 现读抬到最新一节）",1)
wr(P,pr.rstrip()+"\n\n"+RB+"\n")
m=u"## [Unreleased]\n"
if ch.count(m)!=1: raise SystemExit('C2')
wr(C,ch.replace(m,m+"\n"+CS,1))
print("OK")
