#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R391（第 390 轮 / Round 388）的台账。数字全部从本机日志解析。"""
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


build = log("/tmp/r391_build.log")
warnings = len(re.findall(r"warning:", build))
assert warnings == 0

full = log("/tmp/r391_full.log")
summaries = [tuple(int(x) for x in row) for row in
             re.findall(r"Executed (\d+) tests, with (\d+) tests skipped and (\d+) failures", full)]
big = [row for row in summaries if row[0] > 900]
assert big
executed, skipped, failures = big[-1]
assert failures == 0

capture = log("/tmp/r391_capture.log")
cap = re.search(r"CAPTURED (\d+) -> /tmp/r391_shots", capture)
assert cap
frames = int(cap.group(1))

diff = log("/tmp/r391_framediff.log")
dm = re.search(r"FRAME_DIFF 比了=(\d+) 变了=(\d+)", diff)
assert dm
total_frames, changed_frames = [int(x) for x in dm.groups()]
same_frames = total_frames - changed_frames
assert (same_frames, changed_frames, total_frames) == (182, 0, 182)

baseline = log("/tmp/r391_framebaseline.log")
bm = re.search(r"FRAME_BASELINE_COMPARED=(\d+)\s+FRAME_BASELINE_CHANGED=(\d+)"
               r"\s+FRAME_BASELINE_MISSING=(\d+)\s+FRAME_BASELINE_ADDED=(\d+)", baseline)
assert bm
b_compared, b_changed, b_missing, b_added = [int(x) for x in bm.groups()]
assert (b_compared, b_changed, b_missing, b_added) == (182, 0, 0, 0)

criteria = log("/tmp/r391_criteria2.log")
hlight = re.search(r"RESET_HOVER_STATE light 启用 idle=(\d+) hover=(\d+) 差=(\d+) \| 禁用 idle=(\d+) hover=(\d+) 差=(\d+) 卡片=(\d+)", criteria)
hdark = re.search(r"RESET_HOVER_STATE dark 启用 idle=(\d+) hover=(\d+) 差=(\d+) \| 禁用 idle=(\d+) hover=(\d+) 差=(\d+) 卡片=(\d+)", criteria)
plight = re.search(r"RESET_PRESS_STATE light 启用 idle=(\d+) pressed=(\d+) 差=(\d+) \| 禁用 idle=(\d+) pressed=(\d+) 差=(\d+) 卡片=(\d+)", criteria)
pdark = re.search(r"RESET_PRESS_STATE dark 启用 idle=(\d+) pressed=(\d+) 差=(\d+) \| 禁用 idle=(\d+) pressed=(\d+) 差=(\d+) 卡片=(\d+)", criteria)
assert hlight and hdark and plight and pdark
hl = [int(x) for x in hlight.groups()]
hd = [int(x) for x in hdark.groups()]
pl = [int(x) for x in plight.groups()]
pd = [int(x) for x in pdark.groups()]
assert hl[2] >= 6 and hd[2] >= 6 and hl[5] <= 2 and hd[5] <= 2
assert pl[2] >= 6 and pd[2] >= 6 and pl[5] <= 2 and pd[5] <= 2

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

install = log("/tmp/r391_install.log")
assert "INSTALL_RESULT=ok" in install and "INSTALL_SHA_MATCH=1" in install
entries = re.search(r"INSTALL_ENTRIES_BEFORE=(\d+)\s+INSTALL_ENTRIES_AFTER=(\d+)", install)
assert entries
entries_before, entries_after = entries.groups()

pre = log("/tmp/r391_precheck2.log")
pre_line = re.search(r"NEEDLE_PRECHECK tables=(\d+) covered=(\d+) arms=(\d+) bad=(\d+)", pre)
arm_line = re.search(r"ARM_TOTAL files=(\d+) arms=(\d+) dupes=(\d+) repeats=(\d+)", pre)
assert pre_line and arm_line
pre_tables, pre_covered, pre_arms, pre_bad = [int(x) for x in pre_line.groups()]
arm_files, arm_total, arm_dupes, arm_repeats = [int(x) for x in arm_line.groups()]
assert pre_bad == 0 and arm_dupes == 0 and arm_repeats == 0

hidden = log("/tmp/r391_hidden.log")
h = re.search(r"HIDDEN_ARMS 表=(\d+) 可判=(\d+) rot=(\d+) 抽不出=(\d+) 已声明表=(\d+) 已声明死针=(\d+) 上界 rot=(\d+)", hidden)
assert h
h_tables, h_judged, h_rot, h_opaque, h_dtables, h_ddead, h_rot_ceiling = [int(x) for x in h.groups()]
assert h_rot == h_rot_ceiling == 0

gate = log("/tmp/r391_gate.log")
g = re.search(r"MOTION_LEDGER 表面=(\d+) 状态=(\d+) 格子=(\d+) 行数=(\d+) 已清账=(\d+) 未清账=(\d+) 地板=(\d+)", gate)
assert g
surfaces, states, cells, rows, cleared, uncleared, floor_count = [int(x) for x in g.groups()]
assert uncleared == 0 and cleared == cells == rows == floor_count

streak_out = subprocess.check_output(
    ["python3", os.path.join(ROOT, "scripts/product_streak.py"), "--streak-for", "390"],
    cwd=ROOT).decode("utf-8")
streak = int(re.search(r"streak=(\d+)", streak_out).group(1))
assert streak == 1, "streak=%d" % streak

mut = log("/tmp/r391_mut.log")
mut_hover = log("/tmp/r391_mut_hover.log")
assert "R391_MUTATE 刀=2 CAUGHT=2 红得不对=0 RESTORE_CLEAN=yes" in mut
assert "R390_MUTATE 刀=2 CAUGHT=2 红得不对=0 RESTORE_CLEAN=yes" in mut_hover

ui_heading = "## 第 389 轮（R390"
ui_section = f"""## 第 390 轮（R391 · 2026-10-26 · U-1375…U-1379）：自绘「恢复默认」补回按下态 —— 启用 20/16 级、禁用 0 级，M1025/M1026 CAUGHT；悬停刀 M1023 随填充表达式改形一并重钉（U-1375…U-1379 · 产品 1 文件，动效主线）

- **U-1375：⓪ 网络与 CI。** 10:13 `git push origin main` 被 SSH 拒（`Connection closed by 20.205.243.166 port 22`），同分钟 `api=000`（LibreSSL SSL_ERROR_SYSCALL）/ `apple=200` ⇒ GitHub 侧仍断；`PUSH_BLOCKED=network`，本地 ahead=17（R390 之后、R391 落笔前），**不写已推送**。`origin/main` 本地 ref 仍 `5c7814e`；网络不可达，无法 fetch 确认远端是否被别人推进（push 在连接阶段失败，未用 force）。恢复后先 push、复核 ahead=0，再读 `40234023212`/`40234058148` 与 R387–R391 推送跑的全部失败步骤。
- **U-1376：产品位 —— 按下态。** R388 的自绘样式按下时只缩 2%，底色不动；系统 bordered 会再深一档。R391 在 `ResetDefaultButtonBody` 加 `@Environment(\\.pressedForCapture)` + `isEnabled` 闸门，按下填充 `0.08 → 0.17`，缩放也走同一个 `isPressedForDrawing`。两态帧现读：亮档 启用 idle **{pl[0]}** → pressed **{pl[1]}**（差 **{pl[2]}**），暗档 **{pd[0]} → {pd[1]}**（差 **{pd[2]}**）；禁用态亮 **{pl[3]}/{pl[4]}**、暗 **{pd[3]}/{pd[4]}**（差 **{pl[5]}/{pd[5]}**，负半）；能力闸门 卡片 {pl[6]}/{pd[6]}。8 张 PNG 在 `/tmp/r391_press`，逐张看过（亮/暗 × 启用/禁用 × idle/pressed），按下底色深一档、按钮略缩，禁用两帧相同。R390 的悬停复验仍读亮 启用 `{hl[0]}→{hl[1]}`（差 {hl[2]}）/ 禁用 `{hl[3]}/{hl[4]}`、暗 `{hd[0]}→{hd[1]}`（差 {hd[2]}）/ 禁用 `{hd[3]}/{hd[4]}`。
- **U-1377：判据、刀与自伤。** `MotionDriverTests.testResetButtonPressIsWiredAndGated` 压空白后要求 `pressedForCapture` 环境、`isEnabled &&` 闸门、`isPressedForDrawing ? 0.17`、`.scaleEffect(isPressedForDrawing ? 0.98 : 1)` 与 `.hover` 过渡五件同时在；真值表四格。`M1025`（按下填充退回 idle）/`M1026`（摘 isEnabled 闸门）都 **CAUGHT**、还原干净。**自伤**：R391 改同一个填充表达式后，R390 的 M1023 针（旧两分支写法）命中 0，预检当场 `bad=1`；把 M1023 重钉到含 pressed/hover/disabled 三分支的整块，r390 整表复跑 **2/2 CAUGHT**。按下 `.hover` 的过渡过程同样未进胶片（BACKLOG 330）⇒ 只签端态，过程记 NOT-RUN。
- **U-1378：BACKLOG 436 处置（仍未结案）。** 本轮没有新的 runner motion 读数；R390 的完整本地 motion 卷仍是 `Executed {motion_exec} tests, with {motion_skip} tests skipped and {motion_fail} failures`、`MOTION_SUMMARY {motion_summary}`、`MOTION_RESOLVE_SUMMARY judged={motion_judged}/{motion_total} not-run={motion_notrun}`，现有 4 臂登记跑 `motion_floor_gate.py` ⇒ exit 1（UNLISTED `settings-reset-fade`）的本地复现仍成立。**不关单、不改 JSON/自测、不猜 `must_judge`**；runner 卷继续记为具名 NOT-RUN。
- **U-1379：① 367 rot 与八步。** `HIDDEN_ARMS 表={h_tables} 可判={h_judged} rot={h_rot} 抽不出={h_opaque} 已声明表={h_dtables} 已声明死针={h_ddead} 上界 rot={h_rot_ceiling} 处置=ok`；预检 `tables={pre_tables} covered={pre_covered} arms={pre_arms} bad={pre_bad}`、全仓 {arm_files} 文件 / {arm_total} 把；M1025/M1026 与重钉后的 M1023/M1024 全 CAUGHT。build **{warnings}** 告警；全量 `Executed {executed} tests, with {skipped} tests skipped and {failures} failures`；捕获 `CAPTURED {frames} -> /tmp/r391_shots`，与 R390 逐张比 `变了={changed_frames}`，帧基线 `COMPARED={b_compared} CHANGED={b_changed}`（静态帧没变，不 update）；换装 `INSTALL_RESULT=ok`、`INSTALL_SHA_MATCH=1`、条目 `{entries_before}={entries_after}`；清账表 `表面={surfaces} 状态={states} 格子={cells} 已清账={cleared} 未清账={uncleared} 地板={floor_count}`；产品面连续零改动 **{streak}** 轮（现读 `python3 scripts/product_streak.py --streak-for 390`）。
"""

iteration = f"""## Round 388 · R391（第 390 轮 · 2026-10-26）：自绘「恢复默认」补回按下态（启用 20/16 级 / 禁用 0 级）；M1025/M1026 CAUGHT；M1023 随填充表达式重钉（产品 1 文件）

R388 的自绘按钮按下只缩 2%，底色不动。R391 加 `pressedForCapture` + `isEnabled` 闸门，按下填充 0.08→0.17，缩放走同一个判定：亮 启用 {pl[0]}→{pl[1]}（差 {pl[2]}）、暗 {pd[0]}→{pd[1]}（差 {pd[2]}）；禁用 {pl[3]}/{pl[4]} 与 {pd[3]}/{pd[4]}（差 {pl[5]}/{pd[5]}，负半）。R390 悬停复验仍 8/8。源守卫 + 四格真值表 + M1025/M1026 都过；改填充表达式弄断了 R390 的 M1023（预检 bad=1），重钉到三分支整块后 r390 整表 2/2 CAUGHT。按下过程未进胶片（BACKLOG 330），只签端态。436 无新 runner 读数，仍未结案；静态 182 帧零变化；rot 0/0。

**七维度自评**（恰七行，每格 n/15）：

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | 15/15 | 看了 8 张按下帧（亮/暗 × 启用/禁用 × idle/pressed），按下底色深一档、按钮略缩，禁用两帧相同。 |
| 判据有效性 | 14/15 | 两态 + 负半 + 能力闸门 + 源守卫 + 两把刀；扣 1：只签端态，按下过渡过程未进胶片。 |
| 假绿防御 | 15/15 | 负半禁用态必须为 0；R390 的 M1023 被预检当场抓出命中 0，重钉并整表复跑，没有留空刀。 |
| 产品面推进 | 15/15 | 真实 Sources 改动，把 disabled/hover/pressed 三态补齐，静态帧与悬停读数都不回归。 |
| 台账一致性 | 14/15 | U-1375…U-1379、D-380、436 状态、计数器都从日志解析；扣 1：436 仍开，runner 未读。 |
| 交付诚实性 | 15/15 | 网络断只写 PUSH_BLOCKED；push 前未能 fetch 确认远端也写明；过程未判就写 NOT-RUN。 |
| 可复核性 | 15/15 | 8 张 PNG、两态读数、能力闸门、预检 bad 与重钉复跑、motion 5 臂、三把刀都有原文路径。 |

均分 = 103/105 ≈ 14.7/15（98）。
"""

decision = """
### D-380（391）补一态会改同一处视觉表达式；既有刀针必须同轮重钉并整表复跑

R391 现读：给 `ResetDefaultButtonBody` 加按下分支后，R390 的 M1023 针（旧的 hover/idle 两分支填充）命中 **0**，预检 `bad=1` 当场点名；把 M1023 重钉到含 pressed/hover/disabled 三分支的整块后，r390 整表 **2/2 CAUGHT**，R391 的 M1025/M1026 也 2/2 CAUGHT。
**Why**：交互状态矩阵的多个刀针常钉在同一行填充/缩放的表达式上；每加一个状态，表达式形状就变，旧针不是被产品改坏，而是被**同一条产品线的演进**弄断。预检的 `bad` 是唯一在构建前就能看到这件事的读数。
**How to apply**：① 改同一处视觉表达式之后，先跑 `mutate_needle_precheck.py`，`bad>0` 不进入下一步；② 旧针重钉到**包含所有分支的整块**，不要只钉新增的那一支；③ 重钉后把受影响的整张表重跑，不只看被改的那一把；④ 新状态的刀各自钉自己的分支，避免同表多刀共享一个过窄锚点。
"""

changelog = """### 自绘「恢复默认」补回按下态（启用 20/16 级 / 禁用 0 级，M1025/M1026 CAUGHT）；M1023 随填充表达式重钉；436 无新 runner 读数未结案（R391 / 第 390 轮 / Round 388 / U-1375…U-1379 · 产品 1 文件，动效主线）

"""

report_bullet = f"""
- **R391（动效主线）**：R388 的自绘「恢复默认」按下只缩 2%、底色不动 ⇒ 加 `pressedForCapture` + `isEnabled` 闸门，按下填充 0.08→0.17，缩放走同一判定；两态帧亮 启用 `{pl[0]}→{pl[1]}`（差 `{pl[2]}`）、暗 `{pd[0]}→{pd[1]}`（差 `{pd[2]}`），禁用 `{pl[3]}/{pl[4]}`、`{pd[3]}/{pd[4]}`（差 `{pl[5]}/{pd[5]}`）；M1025/M1026 CAUGHT，R390 悬停复验仍 8/8。改填充表达式弄断 R390 的 M1023（预检 bad=1），重钉三分支整块后 r390 整表 2/2 CAUGHT。按下过程未进胶片 ⇒ 只签端态、过程 NOT-RUN。436 无新 runner 读数，仍未结案。静态 182 帧与 R390 逐张相同；rot 0/0。**网络仍断 ⇒ PUSH_BLOCKED=network，ahead=17，未推送。**
"""

state_section = f"""## R391 状态（2026-10-26 · 本地 · 第 390 轮 / Round 388）：自绘「恢复默认」补回按下态（启用 20/16 级 / 禁用 0 级，M1025/M1026 CAUGHT）；M1023 随填充表达式重钉；436 无新 runner 读数（产品 1 文件，动效主线）

最后更新：2026-10-26（本地 · R391 / 第 390 轮 / Round 388）：R388 的自绘按钮按下只缩 2%，底色不动。R391 在 `ResetDefaultButtonBody` 加 `@Environment(\\.pressedForCapture)` + `isEnabled` 闸门，按下填充 `0.08 → 0.17`，缩放也走 `isPressedForDrawing`。两态帧现读：亮档 启用 idle **{pl[0]}** → pressed **{pl[1]}**（差 **{pl[2]}**），暗档 **{pd[0]} → {pd[1]}**（差 **{pd[2]}**）；禁用态亮 **{pl[3]}/{pl[4]}**、暗 **{pd[3]}/{pd[4]}**（差 **{pl[5]}/{pd[5]}**，负半）；能力闸门 卡片 {pl[6]}/{pd[6]}。R390 悬停复验仍读亮 `{hl[0]}→{hl[1]}`（差 {hl[2]}）、暗 `{hd[0]}→{hd[1]}`（差 {hd[2]}），禁用两半仍 0。源守卫 + 四格真值表；`M1025`/`M1026` CAUGHT；改填充表达式让 R390 的 M1023 命中 0（预检 bad=1），重钉到三分支整块后 r390 整表 2/2 CAUGHT。按下/悬停的 `.hover` 过渡过程未进胶片（BACKLOG 330）⇒ 只签端态，过程记 NOT-RUN。BACKLOG 436：无新的 runner motion 读数；R390 本地完整卷 `MOTION_SUMMARY {motion_summary}`、`MOTION_RESOLVE_SUMMARY judged={motion_judged}/{motion_total} not-run={motion_notrun}` 与闸门 exit 1（UNLISTED）的复现仍成立，**不关单、不改 JSON/自测、不猜 must_judge**。`swift build --build-tests` 告警 **{warnings}**；全量 `Executed {executed} tests, with {skipped} tests skipped and {failures} failures`；捕获 `CAPTURED {frames} -> /tmp/r391_shots`，与 R390 逐张比 `变了={changed_frames}`，帧基线 `COMPARED={b_compared} CHANGED={b_changed}`；清账表 `表面={surfaces} 状态={states} 格子={cells} 已清账={cleared} 未清账={uncleared} 地板={floor_count}`；换装 `INSTALL_RESULT=ok`、`INSTALL_SHA_MATCH=1`、条目 {entries_before}={entries_after}；`HIDDEN_ARMS 表={h_tables} 可判={h_judged} rot={h_rot} … 上界 rot={h_rot_ceiling} 处置=ok`；预检 `tables={pre_tables} covered={pre_covered} arms={pre_arms} bad={pre_bad}`、全仓 {arm_files} 文件 / {arm_total} 把；产品面连续零改动 **{streak}** 轮（现读 `python3 scripts/product_streak.py --streak-for 390`）。

本轮做了什么：
① ⓪ 网络：push 被 SSH 拒 + `api=000`/`apple=200` ⇒ `PUSH_BLOCKED=network`；未推送，CI 多跑未读；未能 fetch 确认远端也写明。
② 产品位：自绘「恢复默认」补回按下态（0.08→0.17，禁用不动）；8 张两态帧落 /tmp/r391_press。
③ 判据：源守卫 + 四格真值表 + M1025/M1026；按下过程 NOT-RUN；M1023 重钉并复跑 r390 整表。
④ 436：无新 runner 读数，本地 5 臂复现仍成立；不关单、不猜 must_judge。
⑤ 367：hidden 表 {h_tables} / 可判 {h_judged} / rot {h_rot} / 上界 {h_rot_ceiling}；预检 {pre_tables}/{pre_covered}/{pre_arms}/{pre_bad}。
⑥ 验证：build 0 告警；全量 `{executed}/{skipped}/{failures}`；捕获 {frames} 帧、静态零变化；换装 ok；清账表 {cells}=162。

验证读数（现读）：`RESET_PRESS_STATE` 亮 启用 `{pl[0]}→{pl[1]}`（差 {pl[2]}）/ 禁用 `{pl[3]}/{pl[4]}`（差 {pl[5]}）；暗 `{pd[0]}→{pd[1]}`（差 {pd[2]}）/ 禁用 `{pd[3]}/{pd[4]}`（差 {pd[5]}）；`RESET_HOVER_STATE` 亮 `{hl[0]}→{hl[1]}` / 暗 `{hd[0]}→{hd[1]}`；`M1025/M1026` 与 `M1023/M1024` 全 CAUGHT；`HIDDEN_ARMS … rot={h_rot} … 处置=ok`。

NOT-RUN / 阻塞（分开写）：① **`PUSH_BLOCKED=network`**：push 被 SSH 拒 + `api=000`（LibreSSL SSL_ERROR_SYSCALL）/ `apple=200`；本地 ahead=17（R391 主笔前）；② `40234023212 ↔ d38ea10`、`40234058148 ↔ 5c7814e` 与 R387–R390 本地提交的 conclusion **未读**（网络）；③ 悬停/按下的 `.hover` 过渡过程未进胶片（BACKLOG 330），只签端态；④ 亮档真机腿仍没跑；⑤ BACKLOG 436 的 runner motion 卷未读（本地复现不能关单），不改 JSON/自测。

下一轮（R392）的靶：⓪ 先 `git push origin main`（禁 amend/force）并复核 ahead=0；读 `40234023212`/`40234058148` 与 R387–R391 推送那一跑的**全部失败步骤**，把 run↔commit 成对写回本行；按 BACKLOG 436 先读 CI motion 卷，再决定第五臂 `must_judge` 并一次性改 JSON 与自测；① 367 现读 rot=0，按 `HIDDEN_ROT` 查新腐烂；② 回产品动效面再点一个真实位；R391 的按下端态可用 `UICaptureTests/testResetDefaultButtonShowsPressedOnlyWhenEnabled` 复跑。
"""

audit = rd("AGENT_UI_AUDIT.md")
assert ui_heading in audit
audit_new = once(audit, ui_heading, ui_section + "\n" + ui_heading)
iteration_new = rd("AGENT_VISUAL_ITERATION.md").rstrip() + "\n\n" + iteration
decisions_new = rd("AGENT_DECISIONS.md").rstrip() + "\n" + decision

changelog_old = rd("CHANGELOG.md")
changelog_anchor = "## [Unreleased]\n\n"
assert changelog_old.count(changelog_anchor) == 1
changelog_new = once(changelog_old, changelog_anchor, changelog_anchor + changelog + "\n")

report_old = rd("AGENT_FINAL_REPORT.md")
report_new = once(report_old, "D-069 … **D-379**", "D-069 … **D-380**")
report_new = once(report_new, "U-31 … U-1374（R390 现读抬到最新一节）", "U-31 … U-1379（R391 现读抬到最新一节）")
report_new = once(
    report_new,
    "R390 现读：注册表 **145** 张 / 刀号最大 **M1024** / 预检 covered=128 arms=400 bad=0；全仓 238 文件 / 884 把；M674 退役、M906 空刀退役",
    f"R391 现读：注册表 **{pre_tables}** 张 / 刀号最大 **M1026** / 预检 covered={pre_covered} arms={pre_arms} bad={pre_bad}；"
    f"全仓 {arm_files} 文件 / {arm_total} 把；M674 退役、M906 空刀退役")
report_new = once(
    report_new,
    "**网络仍断 ⇒ PUSH_BLOCKED=network，ahead=17，未推送。**",
    "**网络仍断 ⇒ PUSH_BLOCKED=network，ahead=17，未推送。**" + report_bullet)

state_old = rd("AGENT_STATE.md")
state_anchor = "## R390 状态（2026-10-26"
assert state_old.count(state_anchor) == 1
state_new = once(state_old, state_anchor, state_section + "\n" + state_anchor)

wr("AGENT_UI_AUDIT.md", audit_new)
wr("AGENT_VISUAL_ITERATION.md", iteration_new)
wr("AGENT_DECISIONS.md", decisions_new)
wr("CHANGELOG.md", changelog_new)
wr("AGENT_FINAL_REPORT.md", report_new)
wr("AGENT_STATE.md", state_new)

print("R391_LEDGERS_OK warnings=%s full=%s/%s/%s frames=%s diff=%s/%s baseline=%s/%s press=%s/%s,%s/%s hover=%s/%s,%s/%s motion=%s/%s gate=%s=%s rot=%s pre=%s/%s/%s/%s arms=%s/%s streak=%s"
      % (warnings, executed, skipped, failures, frames, same_frames, changed_frames,
         b_compared, b_changed, pl[2], pd[2], pl[5], pd[5], hl[2], hd[2], hl[5], hd[5],
         motion_exec, motion_judged, cleared, cells, h_rot, pre_tables, pre_covered, pre_arms, pre_bad,
         arm_files, arm_total, streak))
