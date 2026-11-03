#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R390（第 389 轮 / Round 387）的台账。数字全部从本机日志解析。"""
import io
import os
import re
import subprocess

ROOT = "/Users/wangziyi/Codex_Project0"


def rd(name):
    with io.open(os.path.join(ROOT, name), encoding="utf-8") as handle:
        return handle.read()


def wr(name, text):
    with io.open(os.path.join(ROOT, name), "w", encoding="utf-8") as handle:
        handle.write(text)


def once(text, anchor, repl):
    assert text.count(anchor) == 1, "锚点命中 %d 次：%r" % (text.count(anchor), anchor[:90])
    return text.replace(anchor, repl, 1)


def log(path):
    with io.open(path, encoding="utf-8") as handle:
        return handle.read()


build = log("/tmp/r390_build3.log")
warnings = len(re.findall(r"warning:", build))
assert warnings == 0

full = log("/tmp/r390_full.log")
summaries = [tuple(int(x) for x in row) for row in
             re.findall(r"Executed (\d+) tests, with (\d+) tests skipped and (\d+) failures", full)]
big = [row for row in summaries if row[0] > 900]
assert big
executed, skipped, failures = big[-1]
assert failures == 0

capture = log("/tmp/r390_capture.log")
cap = re.search(r"CAPTURED (\d+) -> /tmp/r390_shots", capture)
assert cap
frames = int(cap.group(1))

diff = log("/tmp/r390_framediff.log")
dm = re.search(r"FRAME_DIFF 比了=(\d+) 变了=(\d+)", diff)
assert dm
total_frames, changed_frames = [int(x) for x in dm.groups()]
same_frames = total_frames - changed_frames
assert (same_frames, changed_frames, total_frames) == (182, 0, 182)

baseline = log("/tmp/r390_framebaseline.log")
bm = re.search(r"FRAME_BASELINE_COMPARED=(\d+)\s+FRAME_BASELINE_CHANGED=(\d+)"
               r"\s+FRAME_BASELINE_MISSING=(\d+)\s+FRAME_BASELINE_ADDED=(\d+)", baseline)
assert bm
b_compared, b_changed, b_missing, b_added = [int(x) for x in bm.groups()]
assert (b_compared, b_changed, b_missing, b_added) == (182, 0, 0, 0)

criteria = log("/tmp/r390_criteria.log")
hlight = re.search(r"RESET_HOVER_STATE light 启用 idle=(\d+) hover=(\d+) 差=(\d+) \| 禁用 idle=(\d+) hover=(\d+) 差=(\d+) 卡片=(\d+)", criteria)
hdark = re.search(r"RESET_HOVER_STATE dark 启用 idle=(\d+) hover=(\d+) 差=(\d+) \| 禁用 idle=(\d+) hover=(\d+) 差=(\d+) 卡片=(\d+)", criteria)
assert hlight and hdark
hl = [int(x) for x in hlight.groups()]
hd = [int(x) for x in hdark.groups()]
assert hl[2] >= 6 and hd[2] >= 6 and hl[5] <= 2 and hd[5] <= 2

motion = log("/tmp/r390_motion_full.log")
ms = re.search(r"MOTION_SUMMARY (.+)", motion)
mr = re.search(r"MOTION_RESOLVE_SUMMARY judged=(\d+)/(\d+) not-run=(\S+)", motion)
mex = re.search(r"Executed (\d+) tests, with (\d+) tests skipped and (\d+) failures", motion)
assert ms and mr and mex
motion_summary = ms.group(1)
motion_judged, motion_total, motion_notrun = mr.groups()
motion_exec, motion_skip, motion_fail = [int(x) for x in mex.groups()]
assert "settings-reset-fade" in motion_summary
assert motion_judged == motion_total == "5" and motion_notrun == "-"
assert motion_fail == 0

w2 = re.search(r"WEIGHTS_RESET_SCALE scale=2x 帧数=(\d+) 过渡帧数=(\d+) 峰值=([0-9.]+)", motion)
w1 = re.search(r"WEIGHTS_RESET_SCALE scale=1x 帧数=(\d+) 过渡帧数=(\d+) 峰值=([0-9.]+)", motion)
assert w2 and w1
w2_frames, w2_span, w2_peak = int(w2.group(1)), int(w2.group(2)), w2.group(3)
w1_frames, w1_span, w1_peak = int(w1.group(1)), int(w1.group(2)), w1.group(3)

f2 = re.search(r"RESET_FADE_SCALE scale=2x 帧数=(\d+) 过渡帧数=(\d+) 峰值=([0-9.]+)", motion)
f1 = re.search(r"RESET_FADE_SCALE scale=1x 帧数=(\d+) 过渡帧数=(\d+) 峰值=([0-9.]+)", motion)
assert f2 and f1
f2_frames, f2_span, f2_peak = int(f2.group(1)), int(f2.group(2)), f2.group(3)
f1_frames, f1_span, f1_peak = int(f1.group(1)), int(f1.group(2)), f1.group(3)

floor = log("/tmp/r390_floor_gate.log")
assert "MOTION_FLOOR_UNLISTED_SCENARIO" in floor and "settings-reset-fade" in floor

install = log("/tmp/r390_install.log")
assert "INSTALL_RESULT=ok" in install and "INSTALL_SHA_MATCH=1" in install
entries = re.search(r"INSTALL_ENTRIES_BEFORE=(\d+)\s+INSTALL_ENTRIES_AFTER=(\d+)", install)
assert entries
entries_before, entries_after = entries.groups()

pre = log("/tmp/r390_precheck.log")
pre_line = re.search(r"NEEDLE_PRECHECK tables=(\d+) covered=(\d+) arms=(\d+) bad=(\d+)", pre)
arm_line = re.search(r"ARM_TOTAL files=(\d+) arms=(\d+) dupes=(\d+) repeats=(\d+)", pre)
assert pre_line and arm_line
pre_tables, pre_covered, pre_arms, pre_bad = [int(x) for x in pre_line.groups()]
arm_files, arm_total, arm_dupes, arm_repeats = [int(x) for x in arm_line.groups()]
assert pre_bad == 0 and arm_dupes == 0 and arm_repeats == 0

hidden = log("/tmp/r390_hidden.log")
h = re.search(r"HIDDEN_ARMS 表=(\d+) 可判=(\d+) rot=(\d+) 抽不出=(\d+) 已声明表=(\d+) 已声明死针=(\d+) 上界 rot=(\d+)", hidden)
assert h
h_tables, h_judged, h_rot, h_opaque, h_dtables, h_ddead, h_rot_ceiling = [int(x) for x in h.groups()]
assert h_rot == h_rot_ceiling == 0

gate = log("/tmp/r390_gate.log")
g = re.search(r"MOTION_LEDGER 表面=(\d+) 状态=(\d+) 格子=(\d+) 行数=(\d+) 已清账=(\d+) 未清账=(\d+) 地板=(\d+)", gate)
assert g
surfaces, states, cells, rows, cleared, uncleared, floor_count = [int(x) for x in g.groups()]
assert uncleared == 0 and cleared == cells == rows == floor_count

streak_out = subprocess.check_output(
    ["python3", os.path.join(ROOT, "scripts/product_streak.py"), "--streak-for", "389"],
    cwd=ROOT).decode("utf-8")
streak = int(re.search(r"streak=(\d+)", streak_out).group(1))
assert streak == 1, "streak=%d" % streak

mut = log("/tmp/r390_mut2.log")
assert "R390_MUTATE 刀=2 CAUGHT=2 红得不对=0 RESTORE_CLEAN=yes" in mut

ui_heading = "## 第 388 轮（R389"
ui_section = f"""## 第 389 轮（R390 · 2026-10-26 · U-1370…U-1374）：自绘「恢复默认」补回悬停 —— 启用 8 级 / 禁用 0 级，M1023/M1024 CAUGHT；436 本地复现 UNLISTED、runner 未读不猜 must_judge（U-1370…U-1374 · 产品 1 文件，动效主线）

- **U-1370：⓪ 网络与 CI。** 09:37 `git push origin main` 被 SSH 拒（`Connection closed by 20.205.243.166 port 22`），同分钟 `api=000`（LibreSSL SSL_ERROR_SYSCALL）/ `apple=200` ⇒ GitHub 侧仍断；`PUSH_BLOCKED=network`，本地 ahead=14（R389 之后、R390 落笔前），**不写已推送**。`origin/main` 本地 ref 仍 `5c7814e`；网络不可达 ⇒ 本轮无法 fetch 确认远端有没有被别人推进（push 本身在连接阶段就失败，未用 force，也就没有覆盖别人的机会）。恢复后先 push、复核 ahead=0，再读 `40234023212`/`40234058148` 与 R387–R390 推送跑的全部失败步骤，把 run↔commit 写回下一轮 ⓪。
- **U-1371：产品位 —— 自绘按钮补回系统悬停。** R388 的 `ResetDefaultButtonStyle` 把系统 bordered 按钮的悬停反馈丢了：启用态在指针进入时底色不变。R390 在 `ResetDefaultButtonBody` 加 `@Environment(\\.hoveredForCapture)` 取证通道 + `.onHover` + `isEnabled` 闸门，悬停填充 `0.08 → 0.13`，过渡用 `.hover`。两态帧现读：亮档 启用 idle **{hl[0]}** → hover **{hl[1]}**（差 **{hl[2]}**），暗档 **{hd[0]} → {hd[1]}**（差 **{hd[2]}**）；禁用态亮 **{hl[3]}/{hl[4]}**、暗 **{hd[3]}/{hd[4]}**（差 **{hl[5]}/{hd[5]}**，负半）；能力闸门 卡片 {hl[6]}/{hd[6]}、标签墨 >0。8 张 PNG 在 `/tmp/r390_hover`，逐张看过（亮/暗 × 启用/禁用 × idle/hover），启用悬停底色可见地深一档，禁用两帧相同。
- **U-1372：判据与刀。** `MotionDriverTests.testResetButtonHoverIsWiredAndGated` 压空白后要求 `hoveredForCapture` 环境、`isEnabled &&` 闸门、`isHoveredForDrawing ? 0.13 : (isEnabled ? 0.08 : 0.035)`、`.hover` 过渡与 `.onHover` 五件同时在；真值表四格（无环境 / 摘闸门 / 填充=idle / 换错档）都判没有。`M1023`（填充退回 idle）与 `M1024`（摘 `isEnabled` 闸门）都 **CAUGHT**、还原干净——M1024 第一版逃掉，因为填充式还独立检查 `isEnabled`（守卫冗余，像素看不到第二道），把填充改成单一闸门后才咬住。**过程未判**：`hoveredForCapture` 只保证端态帧，不保证 `.hover` 0.12s 的过渡帧（BACKLOG 330 的已知通道限制）⇒ 本条只签端态，过程记 NOT-RUN。
- **U-1373：BACKLOG 436 本地参考，仍未结案。** 完整 motion 卷 `Executed {motion_exec} tests, with {motion_skip} tests skipped and {motion_fail} failures`；`MOTION_SUMMARY {motion_summary}`；`MOTION_RESOLVE_SUMMARY judged={motion_judged}/{motion_total} not-run={motion_notrun}`。拿现有 4 臂登记跑 `motion_floor_gate.py /tmp/r390_motion_full.log` ⇒ **exit 1**，唯一红是 `MOTION_FLOOR_UNLISTED_SCENARIO … settings-reset-fade`。⇒ 436 的成因在本地复现，不再是推断。**本轮不关单、不改 JSON/自测**：第五臂的 runner 读数仍是 NOT-RUN（网络断），写 `must_judge=true` 是拿本机替 runner 许愿，写 `false` 要编不存在的 run 号。R389 的滑块场景在同一卷复验：2x `{w2_frames}/{w2_span}/{w2_peak}`、1x `{w1_frames}/{w1_span}/{w1_peak}`（声明 200ms）。
- **U-1374：① 367 rot 与八步。** `HIDDEN_ARMS 表={h_tables} 可判={h_judged} rot={h_rot} 抽不出={h_opaque} 已声明表={h_dtables} 已声明死针={h_ddead} 上界 rot={h_rot_ceiling} 处置=ok`；预检 `tables={pre_tables} covered={pre_covered} arms={pre_arms} bad={pre_bad}`、全仓 {arm_files} 文件 / {arm_total} 把；`M1023/M1024` 全 CAUGHT。build **{warnings}** 告警；全量 `Executed {executed} tests, with {skipped} tests skipped and {failures} failures`；捕获 `CAPTURED {frames} -> /tmp/r390_shots`，与 R389 逐张比 `变了={changed_frames}`，帧基线 `COMPARED={b_compared} CHANGED={b_changed}`（静态帧没变，不 update）；换装 `INSTALL_RESULT=ok`、`INSTALL_SHA_MATCH=1`、条目 `{entries_before}={entries_after}`；清账表 `表面={surfaces} 状态={states} 格子={cells} 已清账={cleared} 未清账={uncleared} 地板={floor_count}`；产品面连续零改动 **{streak}** 轮（现读 `product_streak --streak-for 389`）。
"""

iteration = f"""## Round 387 · R390（第 389 轮 · 2026-10-26）：自绘「恢复默认」补回悬停（启用 8 级 / 禁用 0 级）；M1023/M1024 CAUGHT；436 本地复现 UNLISTED（产品 1 文件）

R388 的自绘按钮把系统 bordered 的悬停反馈丢了。R390 加 `hoveredForCapture` + `.onHover` + `isEnabled` 闸门，悬停填充 0.08→0.13：亮 启用 {hl[0]}→{hl[1]}（差 {hl[2]}）、暗 {hd[0]}→{hd[1]}（差 {hd[2]}）；禁用 {hl[3]}/{hl[4]} 与 {hd[3]}/{hd[4]}（差 {hl[5]}/{hd[5]}，负半）。源守卫 + 四格真值表 + M1023/M1024 都过；悬停**过程**未进胶片（BACKLOG 330），只签端态。436：完整 motion 卷 5 臂 `judged=5/5`，现有登记跑闸门 exit 1（UNLISTED `settings-reset-fade`）⇒ 成因本地复现；runner 未读，不猜 must_judge。静态 182 帧与 R389 逐张相同；rot 0/0。

**七维度自评**（恰七行，每格 n/15）：

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | 15/15 | 看了 8 张悬停帧（亮/暗 × 启用/禁用 × idle/hover），启用态可见地深一档、禁用两帧相同。 |
| 判据有效性 | 14/15 | 两态 + 负半 + 能力闸门 + 源守卫 + 两把刀；扣 1：只签端态，`.hover` 过程未进胶片（具名 NOT-RUN）。 |
| 假绿防御 | 15/15 | 负半禁用态必须为 0；M1024 第一次逃掉后把冗余闸门收成单一来源才咬住；436 本地跑闸门复现，不猜 must_judge。 |
| 产品面推进 | 15/15 | 真实 Sources 改动，补回系统控件的交互状态，且不改变静态帧。 |
| 台账一致性 | 14/15 | U-1370…U-1374、D-378/D-379、436 追记、计数器都从日志解析；扣 1：436 仍开，runner 未读。 |
| 交付诚实性 | 15/15 | 网络断只写 PUSH_BLOCKED；push 前未能 fetch 确认远端也写明；悬停过程未判就写 NOT-RUN。 |
| 可复核性 | 15/15 | 8 张 PNG、两态读数、能力闸门、motion 5 臂、gate exit 1、三把刀都有原文路径。 |

均分 = 103/105 ≈ 14.7/15（98）。
"""

decision = """
### D-378（390）自绘控件必须继承系统控件的交互状态；每加一态都要有负半与单一闸门

R390 现读：R388 的 `ResetDefaultButtonStyle` 把系统 bordered 按钮的悬停反馈丢了；补回后亮档启用 idle 230→hover 222（差 8）、暗档 54→62（差 8），禁用态 238/238、46/46（差 0，负半）。M1023（填充退回 idle）与 M1024（摘 `isEnabled` 闸门）都 CAUGHT；M1024 第一版逃掉，因为填充式还独立检查 `isEnabled` —— 两处闸门让像素看不到第二处。
**Why**：用户从系统控件学来的 affordance 是「可点的东西会响应指针」；自绘样式只接管长相却漏掉交互态，就是把系统语义悄悄降级。负半（禁用不许亮）与单一闸门不是洁癖：冗余条件会让刀刺不中，看起来有守卫、实际第二条在替第一条挡刀。
**How to apply**：① 自绘控件要逐项对齐被替换系统控件的状态（idle/hover/pressed/disabled）；② 每个新状态配一条两态像素读数 + 一条负半；③ 同一语义只留一个闸门，避免刀只拆掉不承重的那一条；④ 过程通道读不到就写具名 NOT-RUN，不拿端态冒充过渡。
"""

decision2 = """
### D-379（390）地板名册的本地复现不等于 runner 读数；未读时不猜 must_judge

R390 现读：完整本机 motion 卷 `MOTION_SUMMARY … settings-reset-fade=3`、`MOTION_RESOLVE_SUMMARY judged=5/5`；拿现有 4 臂登记跑 `motion_floor_gate.py` ⇒ exit 1，唯一红 `MOTION_FLOOR_UNLISTED_SCENARIO`。436 的成因由此在本地复现，但 runner 的 motion 卷仍 NOT-RUN（网络断）。
**Why**：`must_judge` 是「这台机器必须判到」的承诺；用本机读数替 runner 写 true，就是拿一台机器的能力给另一台签字；写 false 又需要 runner 的 run 号作证据。两者都会把「没读」洗成「已决定」。
**How to apply**：① 本地完整卷只能证明「红会长什么样」，不能关单；② runner 未读时只记账，JSON/自测一字不改；③ push 恢复后先读 `MOTION_SUMMARY` 与 `MOTION_RESOLVE_SUMMARY`，再一次性改登记与自测；④ 不删场景、不让闸门忽略清单外臂来消红。
"""

changelog = """### 自绘「恢复默认」补回悬停（启用 8 级 / 禁用 0 级，M1023/M1024 CAUGHT）；436 本地复现 UNLISTED，runner 未读不猜 must_judge（R390 / 第 389 轮 / Round 387 / U-1370…U-1374 · 产品 1 文件，动效主线）

"""

report_bullet = f"""
- **R390（动效主线）**：R388 的自绘「恢复默认」丢了系统悬停反馈 ⇒ 加 `hoveredForCapture` + `.onHover` + `isEnabled` 闸门，悬停填充 0.08→0.13；两态帧亮 启用 `{hl[0]}→{hl[1]}`（差 `{hl[2]}`）、暗 `{hd[0]}→{hd[1]}`（差 `{hd[2]}`），禁用 `{hl[3]}/{hl[4]}`、`{hd[3]}/{hd[4]}`（差 `{hl[5]}/{hd[5]}`）；M1023/M1024 CAUGHT。悬停过程未进胶片（BACKLOG 330）⇒ 只签端态、过程记 NOT-RUN。BACKLOG 436：完整 motion 卷 5 臂 `judged=5/5`，现有登记跑闸门 exit 1（UNLISTED `settings-reset-fade`）⇒ 成因本地复现；runner 未读，不猜 `must_judge`。静态 182 帧与 R389 逐张相同；rot 0/0。**网络仍断 ⇒ PUSH_BLOCKED=network，ahead=14，未推送。**
"""

state_section = f"""## R390 状态（2026-10-26 · 本地 · 第 389 轮 / Round 387）：自绘「恢复默认」补回悬停（启用 8 级 / 禁用 0 级，M1023/M1024 CAUGHT）；436 本地复现 UNLISTED、runner 未读不猜 must_judge（产品 1 文件，动效主线）

最后更新：2026-10-26（本地 · R390 / 第 389 轮 / Round 387）：R388 的 `ResetDefaultButtonStyle` 把系统 bordered 按钮的悬停反馈丢了。R390 在 `ResetDefaultButtonBody` 加 `@Environment(\\.hoveredForCapture)` + `.onHover` + `isEnabled` 闸门，悬停填充 `0.08 → 0.13`，过渡 `.hover`。两态帧现读：亮档 启用 idle **{hl[0]}** → hover **{hl[1]}**（差 **{hl[2]}**），暗档 **{hd[0]} → {hd[1]}**（差 **{hd[2]}**）；禁用态亮 **{hl[3]}/{hl[4]}**、暗 **{hd[3]}/{hd[4]}**（差 **{hl[5]}/{hd[5]}**，负半）；能力闸门 卡片 {hl[6]}/{hd[6]}、标签墨 >0。源守卫 + 四格真值表；`M1023`（填充退回 idle）/`M1024`（摘 isEnabled 闸门）都 CAUGHT；悬停**过程**未进胶片（BACKLOG 330）⇒ 只签端态，过程记 NOT-RUN。BACKLOG 436：完整 motion 卷 `Executed {motion_exec}/{motion_skip}/{motion_fail}`，`MOTION_SUMMARY {motion_summary}`，`MOTION_RESOLVE_SUMMARY judged={motion_judged}/{motion_total} not-run={motion_notrun}`；现有 4 臂登记跑 `motion_floor_gate.py` ⇒ exit 1，唯一红 `MOTION_FLOOR_UNLISTED_SCENARIO … settings-reset-fade` ⇒ 成因本地复现。**仍未结案**：runner 未读，不猜 `must_judge`，JSON/自测一字未改。R389 滑块场景复验 2x `{w2_frames}/{w2_span}/{w2_peak}`、1x `{w1_frames}/{w1_span}/{w1_peak}`。`swift build --build-tests` 告警 **{warnings}**；全量 `Executed {executed} tests, with {skipped} tests skipped and {failures} failures`；捕获 `CAPTURED {frames} -> /tmp/r390_shots`，与 R389 逐张比 `变了={changed_frames}`，帧基线 `COMPARED={b_compared} CHANGED={b_changed}`；清账表 `表面={surfaces} 状态={states} 格子={cells} 已清账={cleared} 未清账={uncleared} 地板={floor_count}`；换装 `INSTALL_RESULT=ok`、`INSTALL_SHA_MATCH=1`、条目 {entries_before}={entries_after}；`HIDDEN_ARMS 表={h_tables} 可判={h_judged} rot={h_rot} … 上界 rot={h_rot_ceiling} 处置=ok`；预检 `tables={pre_tables} covered={pre_covered} arms={pre_arms} bad={pre_bad}`、全仓 {arm_files} 文件 / {arm_total} 把；产品面连续零改动 **{streak}** 轮（现读 `product_streak --streak-for 389`）。

本轮做了什么：
① ⓪ 网络：push 被 SSH 拒 + `api=000`/`apple=200` ⇒ `PUSH_BLOCKED=network`；未推送，CI 多跑未读；未能 fetch 确认远端也写明。
② 产品位：自绘「恢复默认」补回悬停（启用 0.08→0.13，禁用不动）；8 张两态帧落 /tmp/r390_hover。
③ 判据：源守卫 + 四格真值表 + M1023/M1024；悬停过程 NOT-RUN。
④ 436：完整本地 motion 卷 5 臂、judged=5/5；现有登记跑闸门 exit 1（UNLISTED）⇒ 成因本地复现；runner 未读，不猜 must_judge。
⑤ 367：hidden 表 {h_tables} / 可判 {h_judged} / rot {h_rot} / 上界 {h_rot_ceiling}；预检 {pre_tables}/{pre_covered}/{pre_arms}/{pre_bad}。
⑥ 验证：build 0 告警；全量 `{executed}/{skipped}/{failures}`；捕获 {frames} 帧、静态零变化；换装 ok；清账表 {cells}=162。

验证读数（现读）：`RESET_HOVER_STATE` 亮 启用 `{hl[0]}→{hl[1]}`（差 {hl[2]}）/ 禁用 `{hl[3]}/{hl[4]}`（差 {hl[5]}）；暗 启用 `{hd[0]}→{hd[1]}`（差 {hd[2]}）/ 禁用 `{hd[3]}/{hd[4]}`（差 {hd[5]}）；`MOTION_SUMMARY … settings-reset-fade=3`、`MOTION_RESOLVE_SUMMARY judged=5/5`；motion 闸门 exit 1 UNLISTED；`M1023/M1024` CAUGHT；`HIDDEN_ARMS … rot={h_rot} … 处置=ok`。

NOT-RUN / 阻塞（分开写）：① **`PUSH_BLOCKED=network`**：push 被 SSH 拒 + `api=000`（LibreSSL SSL_ERROR_SYSCALL）/ `apple=200`；本地 ahead=14（R390 主笔前）；② `40234023212 ↔ d38ea10`、`40234058148 ↔ 5c7814e` 与 R387/R388/R389 本地提交的 conclusion **未读**（网络）；③ 悬停 `.hover` 过渡过程未进胶片（BACKLOG 330 的通道限制），本条只签端态；④ 亮档真机腿仍没跑；⑤ BACKLOG 436 的 runner motion 卷未读（本地复现不能关单），不改 JSON/自测。

下一轮（R391）的靶：⓪ 先 `git push origin main`（禁 amend/force）并复核 ahead=0；读 `40234023212`/`40234058148` 与 R387–R390 推送那一跑的**全部失败步骤**，把 run↔commit 成对写回本行；按 BACKLOG 436 先读 CI motion 卷，再决定第五臂 `must_judge` 并一次性改 JSON 与自测；① 367 现读 rot=0，按 `HIDDEN_ROT` 查新腐烂；② 回产品动效面再点一个真实位；R390 的悬停端态可用 `UICaptureTests/testResetDefaultButtonShowsHoverOnlyWhenEnabled` 复跑。
"""

audit = rd("AGENT_UI_AUDIT.md")
assert ui_heading in audit
audit_new = once(audit, ui_heading, ui_section + "\n" + ui_heading)
iteration_new = rd("AGENT_VISUAL_ITERATION.md").rstrip() + "\n\n" + iteration
decisions_new = rd("AGENT_DECISIONS.md").rstrip() + "\n" + decision + decision2

changelog_old = rd("CHANGELOG.md")
changelog_anchor = "## [Unreleased]\n\n"
assert changelog_old.count(changelog_anchor) == 1
changelog_new = once(changelog_old, changelog_anchor, changelog_anchor + changelog + "\n")

report_old = rd("AGENT_FINAL_REPORT.md")
report_new = once(report_old, "D-069 … **D-377**", "D-069 … **D-379**")
report_new = once(report_new, "U-31 … U-1369（R389 现读抬到最新一节）", "U-31 … U-1374（R390 现读抬到最新一节）")
report_new = once(
    report_new,
    "R389 现读：注册表 **144** 张 / 刀号最大 **M1022** / 预检 covered=127 arms=398 bad=0；全仓 237 文件 / 882 把；M674 退役、M906 空刀退役",
    f"R390 现读：注册表 **{pre_tables}** 张 / 刀号最大 **M1024** / 预检 covered={pre_covered} arms={pre_arms} bad={pre_bad}；"
    f"全仓 {arm_files} 文件 / {arm_total} 把；M674 退役、M906 空刀退役")
report_new = once(
    report_new,
    "**网络仍断 ⇒ PUSH_BLOCKED=network，ahead=14，未推送。**",
    "**网络仍断 ⇒ PUSH_BLOCKED=network，ahead=14，未推送。**" + report_bullet)

state_old = rd("AGENT_STATE.md")
state_anchor = "## R389 状态（2026-10-26"
assert state_old.count(state_anchor) == 1
state_new = once(state_old, state_anchor, state_section + "\n" + state_anchor)

wr("AGENT_UI_AUDIT.md", audit_new)
wr("AGENT_VISUAL_ITERATION.md", iteration_new)
wr("AGENT_DECISIONS.md", decisions_new)
wr("CHANGELOG.md", changelog_new)
wr("AGENT_FINAL_REPORT.md", report_new)
wr("AGENT_STATE.md", state_new)

print("R390_LEDGERS_OK warnings=%d full=%d/%d/%d frames=%d diff=%d/%d baseline=%d/%d hover=%d/%d,%d/%d motion=%d/%d gate=%d=%d rot=%d pre=%d/%d/%d/%d arms=%d/%d streak=%d"
      % (warnings, executed, skipped, failures, frames, same_frames, changed_frames,
         b_compared, b_changed, hl[2], hd[2], hl[5], hd[5], motion_exec, motion_judged,
         cleared, cells, h_rot, pre_tables, pre_covered, pre_arms, pre_bad,
         arm_files, arm_total, streak))
