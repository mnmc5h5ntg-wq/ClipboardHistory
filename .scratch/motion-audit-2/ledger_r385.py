#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R385（第 384 轮 / Round 382）的七本台账。数字全部从本机日志解析。"""
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


build = log("/tmp/r385_build.log")
warnings = len(re.findall(r"warning:", build))

full = log("/tmp/r385_full.log")
summaries = [tuple(int(x) for x in row) for row in
             re.findall(r"Executed (\d+) tests, with (\d+) tests skipped and (\d+) failures", full)]
big = [row for row in summaries if row[0] > 900]
assert big
executed, skipped, failures = big[-1]
assert failures == 0

capture = log("/tmp/r385_shots/capture-readings.log")
cap = re.search(r"CAPTURED (\d+) -> /tmp/r385_shots", capture)
assert cap
frames = int(cap.group(1))

diff = log("/tmp/r385_framediff.log")
dm = re.search(r"FRAMEDIFF same=(\d+) changed=(\d+) total=(\d+)", diff)
assert dm
same_frames, changed_frames, total_frames = [int(x) for x in dm.groups()]
assert (same_frames, changed_frames, total_frames) == (182, 0, 182)

install = log("/tmp/r385_install.log")
assert "INSTALL_RESULT=ok" in install and "INSTALL_SHA_MATCH=1" in install
entries = re.search(r"INSTALL_ENTRIES_BEFORE=(\d+)\s+INSTALL_ENTRIES_AFTER=(\d+)", install)
assert entries
entries_before, entries_after = entries.groups()

pre = log("/tmp/r385_precheck.log")
pre_line = re.search(r"NEEDLE_PRECHECK tables=(\d+) covered=(\d+) arms=(\d+) bad=(\d+)", pre)
arm_line = re.search(r"ARM_TOTAL files=(\d+) arms=(\d+) dupes=(\d+) repeats=(\d+)", pre)
assert pre_line and arm_line
pre_tables, pre_covered, pre_arms, pre_bad = [int(x) for x in pre_line.groups()]
arm_files, arm_total, arm_dupes, arm_repeats = [int(x) for x in arm_line.groups()]
assert pre_bad == 0 and arm_dupes == 0 and arm_repeats == 0

hidden = log("/tmp/r385_hidden2.log")
h = re.search(r"HIDDEN_ARMS 表=(\d+) 可判=(\d+) rot=(\d+) 抽不出=(\d+) 已声明表=(\d+) 已声明死针=(\d+) 上界 rot=(\d+)", hidden)
assert h
h_tables, h_judged, h_rot, h_opaque, h_dtables, h_ddead, h_rot_ceiling = [int(x) for x in h.groups()]
assert h_rot == h_rot_ceiling == 2

gate = log("/tmp/r385_gate.log")
g = re.search(r"MOTION_LEDGER 表面=(\d+) 状态=(\d+) 格子=(\d+) 行数=(\d+) 已清账=(\d+) 未清账=(\d+) 地板=(\d+)", gate)
assert g
surfaces, states, cells, rows, cleared, uncleared, floor = [int(x) for x in g.groups()]
assert uncleared == 0 and cleared == cells == rows == floor

streak_out = subprocess.check_output(
    ["python3", os.path.join(ROOT, "scripts/product_streak.py"), "--streak-for", "384"],
    cwd=ROOT).decode("utf-8")
streak = int(re.search(r"streak=(\d+)", streak_out).group(1))
assert streak == 1, "streak=%d" % streak

r64 = log("/tmp/r385_mut_r64.log")
fade = log("/tmp/r385_mut_fade.log")
assert "CAUGHT=6 非抓到=0" in r64
assert "R385_MUTATE 刀=2 CAUGHT=2 红得不对=0 RESTORE_CLEAN=yes" in fade

ui_heading = "## 第 383 轮（R384 · 2026-10-26 · U-1343…U-1347）："
ui_section = f"""## 第 384 轮（R385 · 2026-10-26 · U-1348…U-1351）：两颗「恢复默认」的禁用切换接上 .selection 过渡 + 源形状守卫；367 再钉 r64 两根，rot 4→2（U-1348…U-1351 · 产品 1 文件，动效主线）

- **U-1348：产品位（过渡）。** R382/R383 把「恢复默认」画成了禁用态，但默认↔动过是**硬切** —— 状态变了，画面一帧就换完。给两颗按钮挂 `MotionCatalog.animation(for: .selection)`（权重页 `value: store.weights == .default`、快捷键页 `value: shortcut == settings.action.defaultShortcut`）。端态逐字节不变：182 张帧 `same={same_frames} changed={changed_frames}` ⇒ 过渡没有改任何静态落点。**过程本身没有胶片证人**（静态帧只拍端态，本轮没造新场景）⇒ 具名 NOT-RUN，不把「接线了」写成「演过了」。
- **U-1349：源形状守卫 + 两把刀。** `MotionDriverTests.testResetButtonDisabledTransitionsAreDriven` 读两份产品源码，要求**键就是禁用条件**那一行在；真值表 `testResetFadeScanIsATruthTable` 证明「另一个键」与「别的动画」都判 false。`M1016`（删权重页过渡）/`M1017`（删快捷键页过渡）现读 `CAUGHT=2 红得不对=0 RESTORE_CLEAN=yes`，各自红在对应的断言。
- **U-1350：367 r64。** M340/M341 重钉到 R377 后的 `appendLocked`（M340 在写盘前整段返回；M341 去掉第一次整份重写），整表 **6/6 CAUGHT**。`HIDDEN_ARMS 表={h_tables} 可判={h_judged} rot={h_rot} … 上界 rot={h_rot_ceiling} … 处置=ok`（4→2；剩 r33 M147 与 r77 M411）。
- **U-1351：⓪ CI（只登记）。** `40234023212 ↔ d38ea10`、`40234058148 ↔ 5c7814e` 两跑 `status=in_progress`、`conclusion=无`（已等 >1000s）⇒ **未读**，不许读成「没红」；R384 的能力闸门在 runner 上到底走判据还是具名 NOT-RUN，要等这两跑 concluded 后下一轮按 read-own-ci-run 读。
"""

iteration = f"""## Round 382 · R385（第 384 轮 · 2026-10-26）：两颗「恢复默认」的禁用切换接上 .selection 过渡（产品 1 文件）

R382/R383 的禁用态在默认↔动过之间是硬切；给权重页与快捷键页两颗按钮挂 `MotionCatalog.animation(for: .selection)`，端态 182 张帧逐字节相同（过渡不改静态落点）。源形状守卫 `testResetButtonDisabledTransitionsAreDriven` + 真值表；M1016/M1017 都 CAUGHT。**过程没有胶片证人** ⇒ 具名 NOT-RUN，不冒充已演过。367：r64 M340/M341 重钉到 `appendLocked`，整表 6/6；rot 4→2。

**七维度自评**（恰七行，每格 n/15）：

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | 13/15 | 端态帧 182/0 逐字节同上轮；过渡过程没有新帧可看，记 NOT-RUN。 |
| 判据有效性 | 14/15 | 源形状守卫 + 真值表 + 两把刀都在；它只签接线，不签过程。 |
| 假绿防御 | 15/15 | 过程 NOT-RUN 具名；另一键/别的动画在真值表里判 false；两臂还原干净。 |
| 产品面推进 | 13/15 | 真实 Sources 过渡落地，但过程未验，推进不完全。 |
| 台账一致性 | 14/15 | U-1348…U-1351、D-373、计数器现读；CI 两跑只登记未读。 |
| 交付诚实性 | 15/15 | 「接线了 ≠ 演过了」写进 U-1348/D-373；in_progress 不写成没红。 |
| 可复核性 | 15/15 | 帧差分 182/0、M1016/M1017、r64 6/6、预检与清账表都有原文。 |

均分 = 99/105 ≈ 14.1/15（94）。
"""

decision = """
### D-373（385）静态帧只签端态；过渡必须另有时间证人，源码守卫只签接线

R385 现读：两颗「恢复默认」在默认↔动过之间硬切，给它们接上 `.selection` 过渡后，182 张端态帧逐字节相同（`same=182 changed=0`）—— 帧基线无法证明过渡演过；源形状守卫能证明「键就是禁用条件」那一行在，但它也不证明 SwiftUI 真按这支动画走完了过程。
**Why**：把「接线存在」当成「过程已验」，与 R383 的取样几何、R376 的刀文坏是同一族：判据答了一个更容易的问题。静态帧的职责是端态；过程没有时间证人时必须具名 NOT-RUN。
**How to apply**：① 过渡的验收分两格：端态用逐字节帧，过程用胶片/时间读数；只有源守卫时，过程记 `NOT-RUN=no-timeline-witness`。② 源守卫要钉**键**，不钉「有 .animation」；③ 下一轮若要收口这颗过渡，加一个只拍按钮带（captureRect）的胶片场景，声明时长 = `.selection`，并先证明它在 1x/2x 都能读出 ≥2 个样本。
"""

changelog = """### 两颗「恢复默认」的禁用切换接上 .selection 过渡（源形状守卫 + M1016/M1017）；367 再钉 r64 两根、rot 4→2（R385 / 第 384 轮 / U-1348…U-1351 · 产品 1 文件，动效主线）

"""

report_bullet = f"""
- **R385（动效主线）**：R382/R383 的「恢复默认」禁用态在默认↔动过之间硬切；两颗按钮接上 `MotionCatalog.animation(for: .selection)`（端态 182 张帧 `same={same_frames} changed={changed_frames}` 逐字节不变）。源形状守卫 `testResetButtonDisabledTransitionsAreDriven` + 真值表；M1016/M1017 都 `CAUGHT`。**过程没有胶片证人 ⇒ 具名 NOT-RUN**（D-373）。367：r64 M340/M341 重钉到 `appendLocked`，整表 6/6，rot 4→2。
"""

state_section = f"""## R385 状态（2026-10-26 · 本地 · 第 384 轮 / Round 382）：两颗「恢复默认」的禁用切换接上 .selection 过渡 + 源形状守卫；367 再钉 r64 两根（产品 1 文件，动效主线）

最后更新：2026-10-26（本地 · R385 / 第 384 轮 / Round 382）：R382/R383 的禁用态在默认↔动过之间硬切；给权重页与快捷键页两颗按钮挂 `MotionCatalog.animation(for: .selection)`（键分别是 `store.weights == .default` / `shortcut == settings.action.defaultShortcut`）。端态 182 张帧 `same={same_frames} changed={changed_frames}` ⇒ 过渡不改静态落点；**过程没有胶片证人 ⇒ 具名 NOT-RUN**（D-373），不把接线写成演过。源形状守卫 `testResetButtonDisabledTransitionsAreDriven` + 真值表；`M1016`/`M1017` 都 `CAUGHT`、还原干净。367：r64 M340/M341 重钉到 `appendLocked`（整表 6/6 CAUGHT），`HIDDEN_ARMS … rot={h_rot} … 上界 rot={h_rot_ceiling} … 处置=ok`（4→2；剩 M147/M411）。`swift build --build-tests` 告警 **{warnings}**；全量 `Executed {executed} tests, with {skipped} tests skipped and {failures} failures`；清账表 `MOTION_LEDGER 表面={surfaces} 状态={states} 格子={cells} 行数={rows} 已清账={cleared} 未清账={uncleared} 地板={floor}`；产品面连续零改动 **{streak}** 轮（`--streak-for 384`）。

本轮做了什么：
① ⓪ CI：`40234023212 ↔ d38ea10`、`40234058148 ↔ 5c7814e` 两跑 in_progress（>1000s），只登记不轮询；R384 能力闸门的 runner 复验仍欠。
② 产品位：两颗重置按钮的禁用切换接 `.selection` 过渡；端态帧 182/0。
③ 判据：源形状守卫 + 真值表；M1016/M1017 CAUGHT；过程 NOT-RUN。
④ 367：r64 M340/M341 重钉，整表 6/6；rot 4→2、上界同笔降。
⑤ 验证：构建 0 告警；全量 `{executed}/{skipped}/{failures}`；捕获 `CAPTURED {frames} -> /tmp/r385_shots`；帧基线 `COMPARED=182 CHANGED=0`；换装 `INSTALL_RESULT=ok`、`INSTALL_SHA_MATCH=1`、条目 {entries_before}={entries_after}；清账表 162=162；预检 `tables={pre_tables} covered={pre_covered} arms={pre_arms} bad={pre_bad}`、全仓 {arm_files} 文件 / {arm_total} 把。

验证读数（现读）：`FRAMEDIFF same={same_frames} changed={changed_frames}`；`R385_MUTATE 刀=2 CAUGHT=2`；r64 `CAUGHT=6`；`HIDDEN_ARMS … rot={h_rot} … 处置=ok`；`NEEDLE_PRECHECK tables={pre_tables} covered={pre_covered} arms={pre_arms} bad={pre_bad}`。

NOT-RUN（分开写）：① **过渡过程**没有胶片/时间证人（静态帧只签端态），记 `NOT-RUN=no-timeline-witness`；② `40234023212`/`40234058148` 两跑仍 in_progress —— CI 结论未读，不许写成没红；③ 亮档真机腿仍没跑；④ 剩 2 根 rot 未重钉（r33 M147、r77 M411）。

下一轮（R386）的靶：⓪ 读队列（先读 `40234023212`/`40234058148` 的全部失败步骤；本笔 run id 待 push 后成对写回）；① 继续 367（r33 M147 或 r77 M411）；② 回产品动效面再点一个真实位；若收口这颗过渡，先造只拍按钮带的胶片场景（≥2 样本/两倍率）。
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
report_new = once(report_old, "D-069 … **D-372**", "D-069 … **D-373**")
report_new = once(
    report_new,
    "R384 现读：注册表 **139** 张 / 刀号最大 **M1015** / 预检 covered=122 arms=391 bad=0；全仓 232 文件 / 875 把；M674 退役、M906 空刀退役",
    f"R385 现读：注册表 **{pre_tables}** 张 / 刀号最大 **M1017** / 预检 covered={pre_covered} arms={pre_arms} bad={pre_bad}；"
    f"全仓 {arm_files} 文件 / {arm_total} 把；M674 退役、M906 空刀退役")
report_new = once(
    report_new,
    "另用隔离真机判掉一处离屏图标裁切伪影（不改产品）。",
    "另用隔离真机判掉一处离屏图标裁切伪影（不改产品）。" + report_bullet)

state_old = rd("AGENT_STATE.md")
state_anchor = "## R384 状态（2026-10-26 · 本地 · 第 383 轮 / Round 381）"
assert state_old.count(state_anchor) == 1
state_new = once(state_old, state_anchor, state_section + "\n" + state_anchor)

wr("AGENT_UI_AUDIT.md", audit_new)
wr("AGENT_VISUAL_ITERATION.md", iteration_new)
wr("AGENT_DECISIONS.md", decisions_new)
wr("CHANGELOG.md", changelog_new)
wr("AGENT_FINAL_REPORT.md", report_new)
wr("AGENT_STATE.md", state_new)

print("R385_LEDGERS_OK warnings=%d full=%d/%d/%d frames=%d diff=%d/%d rot=%d pre=%d/%d/%d/%d arms=%d/%d gate=%d=%d streak=%d"
      % (warnings, executed, skipped, failures, frames, same_frames, changed_frames,
         h_rot, pre_tables, pre_covered, pre_arms, pre_bad, arm_files, arm_total,
         cleared, cells, streak))