#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import io, os, subprocess
R=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
def rd(p): return io.open(p,encoding="utf-8").read()
def wr(p,t): io.open(p,"w",encoding="utf-8").write(t)
A=os.path.join(R,"AGENT_UI_AUDIT.md"); D=os.path.join(R,"AGENT_DECISIONS.md"); B=os.path.join(R,"AGENT_BACKLOG.md")
S=os.path.join(R,"AGENT_STATE.md"); P=os.path.join(R,"AGENT_FINAL_REPORT.md"); I=os.path.join(R,"AGENT_VISUAL_ITERATION.md")
sha=subprocess.check_output(["git","-C",R,"rev-parse","--short=7","HEAD"]).decode().strip()

AT_OLD=u"U-1970…U-1993）：主窗口与设置窗口的标题栏统一"
AT_NEW=u"U-1970…U-1994）：主窗口与设置窗口的标题栏统一"
ANCHOR_NEXT=u"\n## 第 499 轮（R501 · 2026-10-30 · U-1964…U-1969）"
AS=u"""- **U-1994：⑥ R504 判据修复（runner 暗档 vibrant 具名 NOT_RUN）。** `41093593814 ↔ 800a45a` 的 Swift/Capture 双红都指向 R504 的 `testSettingsSidebarCarriesTheAppIdentity`：runner dark **正臂 10 带 / 负臂 1 带**（正首带 **0.0..248.0**、负首带 **282.0..539.0** —— 整列材质带，不是文字行），light 正 **9** / 负 **8** 通过。⇒ runner 1x 的暗档侧栏走 vibrant 合成前极性（D-090），负向臂的文字行结构上看不到，带数塌到 1；等式在那一臂没有对象。修法：负臂 <3 带 ⇒ 具名 `SETTINGS_IDENTITY_HEADER_NOT_RUN=sidebar-vibrant`，light 档必须照判（新增 `SETTINGS_IDENTITY_HEADER_CAPABILITY judged=… light=… vibrant_not_run=…` 行），本机 2x 仍 **2/2**（9/8、9/8）。没有放宽 light 档等式，也没有把整列材质带当文字带。修复笔 `%s`。
""" % sha
DS=u"""## D-502 暗档 vibrant 侧栏的带数不当作文字证据（R505）

- 背景：R504 的身份头判据在 runner 1x 的 dark 臂读到 正 **10** / 负 **1** 带，首带是 **0.0..248.0 / 282.0..539.0** 的整列材质带；同一判据在 light 臂 **9/8** 通过，本机 2x 两档 **9/8**。
- 决定：暗档负向臂带数 <3（文字行结构上看不到）⇒ `SETTINGS_IDENTITY_HEADER_NOT_RUN=sidebar-vibrant`，该臂不判；light 档必须照判，本机 2x 继续两档判。
- 理由：vibrant 合成前极性（D-090）让暗档未选中文字在离屏通道不可见，整列材质与页面纸面的差被尺读成一条带 —— 那不是产品缺陷，也不能当身份头证据。
- 边界：若未来要把暗档纳入 runner 门，先给 `sidebarInkBands` 立**列内纸面估计**的替代仪器（配刀），不许直接把 <3 的出口删掉或放宽 light 等式。
"""
BS=u"""**609. runner 1x 的暗档设置侧栏整列被读成材质带**（R505 现读）
    现象：`sidebarInkBands` 在 runner dark 帧上得到 `0.0..248.0` / `282.0..539.0` 的整列带，负向臂只剩 1 条；身份头判据的暗档臂没有对象（D-502）。
    修法：暗档负臂 <3 带 ⇒ 具名 `NOT_RUN=sidebar-vibrant`，light 档照判；若要把暗档纳入门，先换列内纸面估计的尺（另立仪器 + 刀），不许直接放宽等式。
"""
STATE_OLD=u"产品笔 `f7ea8b4` 已推（ahead=0）。下一轮编号 R506"
STATE_NEW=u"产品笔 `f7ea8b4` 已推；⑥ R504 判据修复：runner `41093593814 ↔ 800a45a` 的 Swift/Capture 双红 = 身份头判据 dark 正 10 / 负 1（首带 0.0..248.0 / 282.0..539.0，整列材质带）⇒ 暗档负臂 <3 带具名 `NOT_RUN=sidebar-vibrant`，light 照判（runner 9/8），本机 2x 仍 2/2；修复笔 `%s` 已推（ahead=0）。下一轮编号 R506" % sha
ITER_OLD=u"**七维度自评**（恰七行，每格 n/15）：\n\n| 维度 | 分 | 依据 |\n| --- | --- | --- |\n| 真实视觉审查 | 15/15 | 状态菜单前后各只截 App 窗口"
ITER_NEW=u"⑥ R504 判据修复：runner `41093593814 ↔ 800a45a` 的 dark 臂 正 10 / 负 1（首带 0.0..248.0 / 282.0..539.0 整列材质带）⇒ 暗档负臂 <3 带具名 `NOT_RUN=sidebar-vibrant`，light 照判；本机 2x 仍 2/2；修复笔 `%s`。\n\n**七维度自评**（恰七行，每格 n/15）：\n\n| 维度 | 分 | 依据 |\n| --- | --- | --- |\n| 真实视觉审查 | 15/15 | 状态菜单前后各只截 App 窗口" % sha
RB_OLD=u"；M1354–M1356 3/3。帧 332（89 噪声不吸收、0 合法变化）；全量 1319/56/0；换装 419=419；电池 683/5。"
RB_NEW=u"；M1354–M1356 3/3；并修 R504 身份头判据的 runner 暗档臂（dark 正 10/负 1 整列材质带 ⇒ `NOT_RUN=sidebar-vibrant`，light 照判）。帧 332（89 噪声不吸收、0 合法变化）；全量 1319/56/0；换装 419=419；电池 683/5。"
a=rd(A); d=rd(D); b=rd(B); st=rd(S); pr=rd(P); it=rd(I)
if a.count(AT_OLD)!=1: raise SystemExit("A title %d" % a.count(AT_OLD))
if a.count(ANCHOR_NEXT)!=1: raise SystemExit("A next %d" % a.count(ANCHOR_NEXT))
if u"## D-502" in d: raise SystemExit("D exists")
if u"**609." in b: raise SystemExit("B exists")
if st.count(STATE_OLD)!=1: raise SystemExit("S anchor %d" % st.count(STATE_OLD))
if it.count(ITER_OLD)!=1: raise SystemExit("I anchor %d" % it.count(ITER_OLD))
if pr.count(RB_OLD)!=1: raise SystemExit("P rb %d" % pr.count(RB_OLD))
if pr.count(u"U-31 … U-1993（R505 现读抬到最新一节）")!=1: raise SystemExit("P ucell %d" % pr.count(u"U-31 … U-1993（R505 现读抬到最新一节）"))
wr(A, a.replace(AT_OLD, AT_NEW, 1).replace(ANCHOR_NEXT, u"\n"+AS+ANCHOR_NEXT, 1))
wr(D, d.rstrip()+"\n\n"+DS+"\n")
wr(B, b.rstrip()+"\n\n"+BS+"\n")
wr(S, st.replace(STATE_OLD, STATE_NEW, 1))
wr(I, it.replace(ITER_OLD, ITER_NEW, 1))
pr=pr.replace(u"U-31 … U-1993（R505 现读抬到最新一节）", u"U-31 … U-1994（R505 现读抬到最新一节）", 1)
wr(P, pr.replace(RB_OLD, RB_NEW, 1))
print("OK sha=%s" % sha)
