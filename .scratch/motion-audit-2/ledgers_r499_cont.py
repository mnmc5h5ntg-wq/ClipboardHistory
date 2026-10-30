#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import io, os
R=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
def rd(p): return io.open(p,encoding="utf-8").read()
def wr(p,t): io.open(p,"w",encoding="utf-8").write(t)
A=os.path.join(R,"AGENT_UI_AUDIT.md"); D=os.path.join(R,"AGENT_DECISIONS.md"); B=os.path.join(R,"AGENT_BACKLOG.md"); S=os.path.join(R,"AGENT_STATE.md"); P=os.path.join(R,"AGENT_FINAL_REPORT.md")
AT=u"## 第 498 轮（R499 · 2026-10-30 · 空轮 Round=0"
AS=u"""## 第 498 轮续（R499 续 · 2026-10-30 · U-1957…U-1959 / U-1960…U-1961 / U-1962…U-1963）：三条 CI 红分诊（录制帧相位、sources 格时序、runner 机器键）

- **U-1957：① 录制帧底留白红的分诊。** run `40941281838 ↔ c9d8d6c` 的 Capture gate 四条断言对象是 `settings-shortcuts-recording light`（内侧 `…/30.0/0.0`、底留白 1.0pt）。**但同一次跑稍后重读同一张帧是 `…/12.0/11.0`**（日志 19:44 vs 20:03），本机 2x 恒为 `14.0/14.5/14.0/12.0`；⇒ 这是快门打在 SwiftUI 布局尚未落定的相位，不是稳定的产品布局缺陷。没有据此盲改产品布局（本机复现不出 30/0）。
- **U-1958：① 修复与复验。** 在录制夹具的 overlay 等待之后补一次**有界**布局落定：三轮 `layoutSubtreeIfNeeded + displayIfNeeded`（每轮泵 0.05s），并打 `RECORDER_LAYOUT_SETTLE waited_ms/轮=3`；不动任何期望值。复跑 `testSettingsCardVerticalRhythmIsOneNumber` 通过、录制帧仍 `14.0/14.5/14.0/12.0`；捕获卷 330 帧 **0 变化**（基线不变）。**没有登记新刀**：删掉这段等待在本机 2x 不产生可判读数变化，按“抓不到的刀不登记”。若 runner 新跑仍读到 30/0，则按 U-1959 当产品问题重开。
- **U-1959：① 边界。** runner 1x 帧无法在本机复现（离屏窗口 2x）；settle 后若仍红，需要下一次跑把 1x 帧存档/用 `CARD_ABOVE` 的六段定位是哪一行，不许再拿同跑另一读掩盖。
- **U-1960：② sources 格时序红。** run `40937242846 ↔ a98e65d` 的 Release 三条红里，`FINAL_REPORT_SOURCES_CELL_STALE` 是**主笔跑早于补记**：那一笔的格还指 `R496/3c64394`，而 git 说 `a98e65d`。补记 `c9d8d6c` 的跑 `40941281838` **Release 已绿（唯一红是 Capture）** ⇒ 时序已被既有流程吸收；现读 `report_sources_cell.py` 账上=git=`R498/05771dc`。**未放宽任何守卫**。
- **U-1961：② 内层无汇总的根因。** `skip_roster` 的“内层没有结论行”不是 flake：空轮 STATE 的「最后更新」行里带了下一轮三口径 `R500 / 第 499 轮`，`current_round()` 读成 (R500,第499)，`test_round_batch_consistency` 找不到对应审计节 ⇒ 内层 `FAILED` 而非 `OK (skipped=N)`。修法：空轮节改「记录（空轮，不记完成）」、下一轮编号改括号写法 `R500（第 499 轮 / Round 497）`；复跑 `test_round_batch_consistency` 3/3 + `test_skip_roster` **6/6 OK**。
- **U-1962：③ runner 机器键。** run `40922562716 ↔ 2e7828f` 的 Swift gate 红在 `TEXT_SIDE_ROSTER_UNKEYED arm64/macOS 15.8/1x`（实测反侧 **0** 张）。按 R124 / BACKLOG 171 的既有出口登记这一台自己的空集声明：`"arm64/macOS 15.8/1x": []`，注释写自己的 run 来源与测法（同跑 27/27 夹具判完）；**没有复制 15.7 那行的措辞**，15.7 留旧账。本机 27.0/2x 复跑 `TEXT_SIDE_ROSTER_KEY 判了 25/25 ⇒ 一致`。
- **U-1963：④ 八步与电池。** build **0 告警**（`scripts/warning_gate.sh` arm64 冷编）；捕获卷 **330 帧**、`CHANGED=0 ADDED=0 MISSING=0`；全量 **1314/56/1**（唯一红 PerfBudget 本机负载 flake，单跑原样复验）；**无产品文件 ⇒ 不换装**（具名 skip：本轮无 Sources 改动，397 保持 R498 装好的那份）；电池 **683/OK skipped=5**；清账 `格=162 声明=63 不成立=0/63`；工作树仅本轮测试/台账文件。收口 push 见补记。
"""
DS=u"""## D-496 三条 CI 红：录制帧按捕获相位修、sources 格按补记收、runner 机器键按本机读数登记（R499 续）

- 背景：三条红分别落在录制帧底留白、主笔跑 sources 格、runner 未登记机器键。
- 决定：① 录制帧同跑两读一坏一好（30/0 vs 12/11）、本机 2x 恒干净 ⇒ 判为捕获打在未落定布局上，补有界 layout+display 落定，不改产品布局、不登记抓不到的刀；② sources 格红是主笔跑早于补记，补记跑 Release 已绿、现读一致 ⇒ 不放宽守卫；③ runner OS 15.8 的键按这一台自己的读数新增空集声明，不抄 15.7。
- 理由：没有可复现的产品读数就不盲改产品（R482 空轮同一族）；时序红由既有补记流程吸收；未登记机器键按 R124/BACKLOG 171 出口登记。
- 边界：settle 后 runner 若仍读到 30/0 ⇒ 按 U-1959 当产品问题重开并定位到行。
"""
BS=u"""**599. runner OS 小版本升级会让侧栏盲区位键漂移**（R499 现读）
    现象：15.7 → 15.8 后 `TEXT_SIDE_ROSTER_UNKEYED arm64/macOS 15.8/1x` 红；每次升 OS 都要补一行空集声明。
    修法：若要减少漂移，可让键匹配只到主版本（或允许 `+` 通配）并配一条“缩小匹配不许丢告警”的正对照；先不改。

**600. 录制帧 30/0 只出现在 runner 1x 的一次读里**（R499 观察）
    现象：同跑两读 30/0 与 12/11，本机 2x 恒 12/11；已补有界布局落定，但未在 runner 复验。
    修法：下一跑读 `CARD_RHYTHM settings-shortcuts-recording`；若仍 30/0，按 `CARD_ABOVE` 六段定行后改产品布局。
"""
SS_ADD=u"""

续（三条 CI 红，分节账 R499 续）：① 录制帧底留白红（run `40941281838 ↔ c9d8d6c`，Capture gate）——同跑两读 30/0 与 12/11、本机 2x 恒 12/11 ⇒ 捕获相位；补三轮有界 `layoutSubtreeIfNeeded + displayIfNeeded`（`RECORDER_LAYOUT_SETTLE`），不动期望、不盲改产品、不登记抓不到的刀；复跑卡片节奏绿、捕获 330 帧 0 变化。② sources 格红（run `40937242846 ↔ a98e65d`）——主笔跑早于补记；补记跑 `40941281838` Release 已绿、现读 `R498/05771dc`=git；另把空轮 STATE 的「最后更新」行污染 `current_round()` 的根因修掉（改「记录（空轮…）」+ 下一轮括号编号），`test_round_batch_consistency` 3/3、`test_skip_roster` 6/6。③ runner 键红（run `40922562716 ↔ 2e7828f`）——`TEXT_SIDE_ROSTER_UNKEYED arm64/macOS 15.8/1x`（反侧 0 张），按本机读数新增 `"arm64/macOS 15.8/1x": []`，不抄 15.7 行；本机 25/25 一致。build 0 告警；全量 1314/56/1（PerfBudget flake 单跑过）；无产品文件 ⇒ 不换装；电池 683/5；清账 162/63/0；HEAD=origin/main（收口 push 后）。
"""
RB=u"""- **R499 续（三条 CI 红分诊）**：① 录制帧底留白（run 40941281838）同跑两读 30/0 与 12/11、本机 2x 恒 12/11 ⇒ 捕获相位；补有界 layout+display 落定、不改期望不盲改产品；② sources 格（run 40937242846）是主笔跑早于补记、补记跑 Release 已绿，现读一致；并修空轮 STATE 污染 `current_round()` 的根因；③ runner `arm64/macOS 15.8/1x` 按本机读数登记空集声明。build 0 告警；捕获 330 帧 0 变化；全量 1314/56/1（PerfBudget flake 单跑过）；无产品文件 ⇒ 不换装；电池 683/5。
"""
a=rd(A); d=rd(D); b=rd(B); st=rd(S); pr=rd(P)
if a.count(AT)!=1: raise SystemExit('A:'+str(a.count(AT)))
if u"## D-496" in d: raise SystemExit('D')
if u"**599." in b: raise SystemExit('B')
if st.count(u"## R499 空轮记录")!=1: raise SystemExit('S')
if u"R499 续（三条 CI 红分诊）" in pr: raise SystemExit('P')
wr(A,a.replace(AT,AS+AT,1)); wr(D,d.rstrip()+"\n\n"+DS+"\n"); wr(B,b.rstrip()+"\n\n"+BS+"\n")
wr(S,st.replace(u"## R498 状态",SS_ADD.strip()+"\n\n## R498 状态",1))
wr(P,pr.rstrip()+"\n\n"+RB+"\n"); print("OK")
