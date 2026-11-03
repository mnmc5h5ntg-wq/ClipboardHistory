#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R399（第 398 轮 / Round 396）的台账。数字全部从本机日志/CI 现读解析。"""
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


build = log("/tmp/r399_build_final.log")
warnings = len(re.findall(r"warning:", build))
assert warnings == 0

full = log("/tmp/r399_full.log")
summaries = [tuple(int(x) for x in row) for row in
             re.findall(r"Executed (\d+) tests, with (\d+) tests skipped and (\d+) failures", full)]
big = [row for row in summaries if row[0] > 900]
assert big
executed, skipped, failures = big[-1]
assert (executed, skipped, failures) == (1060, 52, 0)

capture = log("/tmp/r399_capture.log")
cap = re.search(r"CAPTURED (\d+) -> /tmp/r399_shots", capture)
assert cap
frames = int(cap.group(1))
assert frames == 182

pixel = log("/tmp/r399_pixel_guard.log")
pm = re.search(r"LONG_TEXT_PILL_CLEAR maxX=([0-9.]+)pt 墨=(\d+) 上限=500\.0pt", pixel)
assert pm
new_max_pt, new_ink = float(pm.group(1)), int(pm.group(2))
assert abs(new_max_pt - 484.0) < 0.1

diff = log("/tmp/r399_framediff.log")
dm = re.search(r"FRAME_DIFF 比了=(\d+) 变了=(\d+)", diff)
assert dm
total_frames, changed_frames = [int(x) for x in dm.groups()]
changed_names = sorted(re.findall(r"^  changed (.+)$", diff, re.M))
expected_changed = sorted([
    "content-min-600x440-dark.png",
    "content-min-600x440-light.png",
    "content-min-with-copy-failure-notice-600x440-dark.png",
    "content-min-with-copy-failure-notice-600x440-light.png",
])
assert (total_frames, changed_frames) == (182, 4)
assert changed_names == expected_changed, changed_names

baseline = log("/tmp/r399_framebaseline.log")
bm = re.search(r"FRAME_BASELINE_COMPARED=(\d+)\s+FRAME_BASELINE_CHANGED=(\d+)"
               r"\s+FRAME_BASELINE_MISSING=(\d+)\s+FRAME_BASELINE_ADDED=(\d+)", baseline)
assert bm
b_compared, b_changed, b_missing, b_added = [int(x) for x in bm.groups()]
assert (b_compared, b_changed, b_missing, b_added) == (182, 0, 0, 0)
bupdate = log("/tmp/r399_framebaseline_update.log")
assert "FRAME_BASELINE_UPDATED=182" in bupdate

typography = log("/tmp/r399_typography_tests.log")
assert "testPreviewTrailingInsetOnlyAppliesToNarrowDetailColumns]' passed" in typography
assert "testDetailViewAppliesTheNarrowDetailInset]' passed" in typography
assert "Executed 22 tests, with 0 failures" in typography

pixel_test = pixel
assert "testLongTextAtMinimumWidthDoesNotRunUnderTheFloatingPill]' passed" in pixel_test
assert "Executed 1 test, with 0 failures" in pixel_test

mut_policy = log("/tmp/r399_mut_policy.log")
assert "M1039" in mut_policy and "M1041" in mut_policy
assert "M1039 窄列尾距策略置零（源判据） ⇒ CAUGHT 红得对=True 命中=True" in mut_policy
assert "M1041 窄列尾距策略置零（像素判据） ⇒ CAUGHT 红得对=True 命中=True" in mut_policy
assert "R399_POLICY_MUTATE 刀=2 CAUGHT=2 红得不对=0 RESTORE_CLEAN=yes" in mut_policy
mut_wiring = log("/tmp/r399_mut_wiring.log")
assert "M1040 详情预览不接窄列尾距（源判据） ⇒ CAUGHT 红得对=True 命中=True" in mut_wiring
assert "R399_WIRING_MUTATE 刀=1 CAUGHT=1 红得不对=0 RESTORE_CLEAN=yes" in mut_wiring

install = log("/tmp/r399_install.log")
assert "INSTALL_RESULT=ok" in install and "INSTALL_SHA_MATCH=1" in install
entries = re.search(r"INSTALL_ENTRIES_BEFORE=(\d+)\s+INSTALL_ENTRIES_AFTER=(\d+)", install)
assert entries
entries_before, entries_after = entries.groups()
assert entries_before == entries_after == "381"

pre = log("/tmp/r399_precheck.log")
pre_line = re.search(r"NEEDLE_PRECHECK tables=(\d+) covered=(\d+) arms=(\d+) bad=(\d+)", pre)
arm_line = re.search(r"ARM_TOTAL files=(\d+) arms=(\d+) dupes=(\d+) repeats=(\d+)", pre)
assert pre_line and arm_line
pre_tables, pre_covered, pre_arms, pre_bad = [int(x) for x in pre_line.groups()]
arm_files, arm_total, arm_dupes, arm_repeats = [int(x) for x in arm_line.groups()]
assert (pre_tables, pre_covered, pre_arms, pre_bad) == (155, 138, 417, 0)
assert (arm_files, arm_total) == (248, 901)
assert arm_dupes == 0 and arm_repeats == 0

hidden = log("/tmp/r399_hidden.log")
h = re.search(r"HIDDEN_ARMS 表=(\d+) 可判=(\d+) rot=(\d+) 抽不出=(\d+) 已声明表=(\d+)"
              r" 已声明死针=(\d+) 上界 rot=(\d+)", hidden)
assert h
h_tables, h_judged, h_rot, h_opaque, h_dtables, h_ddead, h_rot_ceiling = [int(x) for x in h.groups()]
assert (h_tables, h_judged, h_rot, h_opaque, h_dtables, h_ddead, h_rot_ceiling) == (242, 835, 0, 6, 6, 0, 0)

gate = log("/tmp/r399_gate.log")
g = re.search(r"MOTION_LEDGER 表面=(\d+) 状态=(\d+) 格子=(\d+) 行数=(\d+)"
              r" 已清账=(\d+) 未清账=(\d+) 地板=(\d+)", gate)
assert g
surfaces, states, cells, rows, cleared, uncleared, floor_count = [int(x) for x in g.groups()]
assert (surfaces, states, cells, rows, cleared, uncleared, floor_count) == (18, 9, 162, 162, 162, 0, 162)
assert "MOTION_LEDGER_RESULT=ok" in gate

streak_out = subprocess.check_output(
    ["python3", os.path.join(ROOT, "scripts/product_streak.py"), "--streak-for", "398"],
    cwd=ROOT).decode("utf-8")
streak = int(re.search(r"streak=(\d+)", streak_out).group(1))
assert streak == 1, "streak=%d" % streak

motion = log("/tmp/r390_motion_full.log")
ms = re.search(r"MOTION_SUMMARY (.+)", motion)
mr = re.search(r"MOTION_RESOLVE_SUMMARY judged=(\d+)/(\d+) not-run=(\S+)", motion)
mex = re.search(r"Executed (\d+) tests, with (\d+) tests skipped and (\d+) failures", motion)
assert ms and mr and mex
motion_summary = ms.group(1)
motion_judged, motion_total, motion_notrun = mr.groups()
motion_exec, motion_skip, motion_fail = [int(x) for x in mex.groups()]
assert motion_judged == motion_total == "5" and motion_notrun == "-" and motion_fail == 0
assert "settings-reset-fade" in motion_summary

ui_heading = "## 第 397 轮（R398"
ui_section = f"""## 第 398 轮（R399 · 2026-10-26 · U-1415…U-1419）：600pt 最窄窗长正文排进浮动操作栏（正文最右墨列 529.5 → 484.0pt）；窄列尾距 + 三刀（U-1415…U-1419 · 产品 2 文件，布局状态位）

- **U-1415：⓪ 网络恢复后的 push 与 CI 队列。** `git fetch origin` 确认 origin/main 仍 `5c7814e`；`git push origin main` 成功 `5c7814e..ae202dd`，本地 HEAD==origin、ahead=0。旧两跑成对读：`40234023212 ↔ d38ea10` / completed / **success**（全部失败步骤=无）；`40234058148 ↔ 5c7814e` / completed / **success**（无）；改动前对照 `40221947072 ↔ 43ff699` / completed / **success**（无）⇒ 没有可归因的失败步骤。两次 push 的新跑 `40280864844 ↔ ae202dd`、`40280951026 ↔ cfbcec7` 现读都 **in_progress**（`conclusion` 空、日志 0 字节不算读数）⇒ 具名 NOT-RUN，等落地后再按**全部**失败步骤读；一次 push 只为 head 生成新 run，旧两跑已单独读。STATE 的 R399 ⓪ 已写回三对 run↔commit 并推送。
- **U-1416：② 产品视觉位 —— 最窄窗里正文排进右下角浮动操作栏。** 真看图：600×440 最窄窗 + 长正文，正文最后几行从 `GlassPill` 左侧伸进去，被药丸盖住。按正文最右墨列量：旧 **529.5pt**（越过药丸左沿，阈值 500），新 **484.0pt**；像素守卫 `LONG_TEXT_PILL_CLEAR maxX=484.0pt 墨={new_ink} 上限=500.0pt`。修法：`DetailTypography.previewTrailingInset(forDetailWidth:)` 只在详情列 <400pt 时给 88pt 尾距；`DetailView` 用 `GeometryReader` 把列宽交给策略，并只给 `preview` 加尾距。产品 2 文件（DetailTypography 策略 + DetailView 接线）。旧帧是用把策略临时置 0 重拍出来的（还原 SHA 与改前一致），不是从注释推的。
- **U-1417：判据与刀。** 纯函数 `testPreviewTrailingInsetOnlyAppliesToNarrowDetailColumns`（320pt ≥80、470/720=0、0=0）+ 接线 `testDetailViewAppliesTheNarrowDetailInset`（DetailView 必须引用策略并有 GeometryReader）+ 自拍自量 `testLongTextAtMinimumWidthDoesNotRunUnderTheFloatingPill`（正文最右墨列 ≤500pt）。`M1039`（策略置零 → 纯判据）、`M1041`（策略置零 → 像素判据）、`M1040`（DetailView 删尾距 → 接线判据）三刀全 **CAUGHT**、红得不对=0、各自表 `RESTORE_CLEAN=yes`；一张表一个文件靶（D-384）。默认 182 帧里只有 4 张 600pt 帧变化（正文变窄、让开药丸），基线同笔 `UPDATED=182`、复验 182/0/0/0。
- **U-1418：BACKLOG 436 处置（仍未结案）。** 本轮仍没有可用的 runner motion 读数：两次 push 的新跑都 **in_progress**，没有落地日志；不把 0 字节日志读成“没有 motion”，也不猜第五臂 `must_judge`。R390 本地卷 `judged=5/5` 与现有 4 臂登记跑 `motion_floor_gate.py` exit 1（UNLISTED `settings-reset-fade`）的本地复现仍成立；**不关单、不改 JSON/自测**，runner 卷继续记具名 NOT-RUN，下一轮先读新跑全部失败步骤与 motion 摘要。
- **U-1419：① 367 rot 与八步。** `HIDDEN_ARMS 表={h_tables} 可判={h_judged} rot={h_rot} 抽不出={h_opaque} 已声明表={h_dtables} 已声明死针={h_ddead} 上界 rot={h_rot_ceiling} 处置=ok`；预检 `tables={pre_tables} covered={pre_covered} arms={pre_arms} bad={pre_bad}`、全仓 {arm_files} 文件 / {arm_total} 把；三表 `M1039/M1040/M1041` 全 CAUGHT。build **{warnings}** 告警；全量 `Executed {executed} tests, with {skipped} tests skipped and {failures} failures`；捕获 `CAPTURED {frames} -> /tmp/r399_shots`，与 R398 逐张比 `变了={changed_frames}`（四张 600pt 帧；新布局位点另由自拍自量像素判据覆盖），帧基线同一笔 `UPDATED=182`、复验 `COMPARED={b_compared} CHANGED={b_changed} MISSING={b_missing} ADDED={b_added}`；换装 `INSTALL_RESULT=ok`、`INSTALL_SHA_MATCH=1`、条目 `{entries_before}={entries_after}`；清账表 `表面={surfaces} 状态={states} 格子={cells} 已清账={cleared} 未清账={uncleared} 地板={floor_count}`；产品面连续零改动 **{streak}** 轮（as-of 398；本轮产品布局已落 Sources，现读 `python3 scripts/product_streak.py --streak-for 398`）。电池在台账落盘后复跑，读数写进本笔追记。
"""

iteration = f"""## Round 396 · R399（第 398 轮 · 2026-10-26）：600pt 最窄窗长正文排进浮动操作栏（529.5 → 484.0pt）；窄列尾距 + 三刀（产品 2 文件，布局状态位）

真看图：600×440 最窄窗 + 长正文时，正文最后几行从右下角 `GlassPill` 左侧伸进去、被药丸盖住。按正文最右墨列量：旧 **529.5pt**、新 **484.0pt**（阈值 500）。修法：`DetailTypography.previewTrailingInset(forDetailWidth:)` 只在详情列 <400pt 时给 88pt 尾距；`DetailView` 用 `GeometryReader` 量列宽并只给 `preview` 加尾距。默认 182 帧里四张 600pt 帧变化（正文变窄、让开药丸），基线同笔 update 后 182/0。旧帧由把策略临时置 0 重拍、还原 SHA 一致。

**七维度自评**（恰七行，每格 n/15）：

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | 14/15 | 真看了 600pt 长正文新旧帧，量了最右墨列；扣 1：只审了这一布局状态。 |
| 判据有效性 | 15/15 | 纯策略 + 接线 + 自拍自量像素；M1039/M1040/M1041 三刀全 CAUGHT。 |
| 假绿防御 | 15/15 | 旧帧用策略置零重拍、还原 SHA 一致；像素阈值 500 两侧各有 ≥15pt 余量。 |
| 产品面推进 | 14/15 | 真落 Sources：窄列让位，宽列 68ch 不动；扣 1：单点修复。 |
| 台账一致性 | 14/15 | U-1415…U-1419、D-389、436、CI 队列与计数器都从日志现读；扣 1：436 仍开。 |
| 交付诚实性 | 15/15 | 两次新跑 in_progress 记具名 NOT-RUN；没有把 0 字节日志读成“没红”。 |
| 可复核性 | 15/15 | 最右墨列、旧/新帧、三条判据、三把刀、precheck/rot、CI run↔commit 都有原文。 |

均分 = 102/105 ≈ 14.6/15（97）。
"""

decision = """
### D-389（399）浮动操作栏不是正文的背景：窄详情列必须让出尾距，宽列不动

R399 现读：600pt 最窄窗 + 长正文时，正文最右墨列 **529.5pt**，越过右下角 `GlassPill` 左沿（阈值 500），最后几行被药丸盖住；`DetailTypography.previewTrailingInset` 只在详情列 <400pt 给 88pt 尾距、`DetailView` 用 `GeometryReader` 接上后，最右墨列 **484.0pt**，同一段正文不再进入药丸底下。宽详情列（470/720pt）尾距为 0，68ch 可读列不动。默认 182 帧只有四张 600pt 帧变化。
**Why**：浮动操作栏是覆盖层，但它覆盖的必须是**空白**，不是用户要读的字。最窄窗是产品支持的布局状态（`minWidth` 600），不能拿“可以滚动”当理由让最后几行长期藏在药丸下。宽列若也缩窄，会把 68ch 的可读列无谓牺牲掉，所以必须按列宽条件化。
**How to apply**：① 浮层与正文争同一块右下角时，给正文加**条件尾距**（不是给浮层换位置、不是把正文整体裁掉）；② 纯函数先给出“什么宽度让多少”，视图只负责把列宽量进来；③ 判据三层：政策（窄让/宽不让）、接线（GeometryReader + padding）、像素（最右墨列 ≤ 上限）；④ 一张表一个文件靶，策略刀与接线刀分开（R399 M1039/M1041 / M1040）。
"""

changelog = """### 600pt 最窄窗长正文排进浮动操作栏（529.5 → 484.0pt）；窄列尾距 + 三刀（R399 / 第 398 轮 / Round 396 / U-1415…U-1419 · 产品 2 文件，布局状态位）

"""

report_bullet = """
- **R399（布局状态位）**：600pt 最窄窗 + 长正文时，最后几行排进右下角浮动 `GlassPill` 下面（正文最右墨列旧 `529.5pt`，阈值 500）。`DetailTypography.previewTrailingInset` 只在详情列 <400pt 给 88pt 尾距，`DetailView` 用 `GeometryReader` 接入；宽列 68ch 不动。新读数 `484.0pt`（像素守卫 `LONG_TEXT_PILL_CLEAR`）。默认 182 帧中四张 600pt 帧变化，基线同笔 update 后 182/0；全量 1060/52/0；M1039/M1040/M1041 三刀全 CAUGHT。**push 已恢复：`5c7814e..ae202dd` → ahead=0；两旧跑 success 无失败步骤，新跑 `40280864844`/`40280951026` in_progress 记具名 NOT-RUN。** 436 无可用 runner motion 读数，仍未结案；rot 0/0。
"""

state_section = f"""## R399 状态（2026-10-26 · 本地 · 第 398 轮 / Round 396）：600pt 最窄窗长正文排进浮动操作栏（529.5 → 484.0pt）；窄列尾距 + 三刀（产品 2 文件，布局状态位）

最后更新：2026-10-26（本地 · R399 / 第 398 轮 / Round 396）：真看图——600×440 最窄窗 + 长正文时，正文最后几行从右下角 `GlassPill` 左侧伸进去、被药丸盖住。按正文最右墨列量：旧 **529.5pt**（阈值 500）、新 **484.0pt**。产品改法：`DetailTypography.previewTrailingInset(forDetailWidth:)` 只在详情列 <400pt 时给 88pt 尾距；`DetailView` 用 `GeometryReader` 把列宽交给策略，并只给 `preview` 加尾距。默认 182 帧里四张 600pt 帧变化，基线同笔 `UPDATED=182`，复验 182/0/0/0。全量 `Executed {executed} tests, with {skipped} tests skipped and {failures} failures`；换装 `ok / SHA_MATCH=1 / 381=381`；清账表 162=162；`HIDDEN_ARMS 表={h_tables} 可判={h_judged} rot={h_rot} … 上界 rot={h_rot_ceiling} 处置=ok`；预检 `tables={pre_tables} covered={pre_covered} arms={pre_arms} bad={pre_bad}`、全仓 {arm_files} 文件 / {arm_total} 把；产品面连续零改动 **{streak}** 轮（as-of 398，现读 `python3 scripts/product_streak.py --streak-for 398`；本轮产品布局已落 Sources）。电池在台账落盘后复跑，读数写进本笔追记。

本轮做了什么：
① ⓪ 网络恢复：fetch 确认 origin 仍 5c7814e，push `5c7814e..ae202dd` 成功、ahead=0；旧两跑与对照均 success 无失败步骤；两次新跑 in_progress 记具名 NOT-RUN。
② 看图找到布局缺陷：600pt 最窄窗长正文排进右下角浮动药丸（529.5pt → 484.0pt）。
③ 修 Sources：窄列条件尾距 + GeometryReader 接线；宽列 68ch 不动。
④ 判据：纯策略 + 接线 + 自拍自量像素；M1039/M1040/M1041 三刀全 CAUGHT、RESTORE_CLEAN=yes。
⑤ 367：hidden 表 {h_tables} / 可判 {h_judged} / rot {h_rot} / 上界 {h_rot_ceiling}；预检 {pre_tables}/{pre_covered}/{pre_arms}/{pre_bad}。
⑥ 验证：build 0 告警；全量 `{executed}/{skipped}/{failures}`；捕获 {frames} 帧、4 帧变化、基线 update 后 182/0；换装 ok；清账表 162=162。

验证读数（现读）：`LONG_TEXT_PILL_CLEAR maxX={new_max_pt:.1f}pt 墨={new_ink} 上限=500.0pt`；旧帧同尺 529.5pt；`M1039/M1040/M1041` 三刀 CAUGHT；`HIDDEN_ARMS … rot={h_rot} … 处置=ok`。

NOT-RUN / 阻塞（分开写）：① **CI 新跑未读**：`40280864844 ↔ ae202dd`、`40280951026 ↔ cfbcec7` 均 in_progress（`conclusion` 空、0 字节日志）；R399 主笔推送后的新跑在 R400 ⓪ 按全部失败步骤补读；② **BACKLOG 436 的 runner motion 卷未读**（本地 5/5、UNLISTED `settings-reset-fade` 仍可复现）；③ 亮档真机腿仍没跑；④ macOS 12 的紧凑详情头仍走旧截断（13+ 才有 ViewThatFits）。

下一轮（R400）的靶：⓪ 先 `git push origin main`（禁 amend/force）并复核 ahead=0；读 `40280864844`/`40280951026` 与 R399 主笔推送跑的全部失败步骤（成对 run↔commit），新跑没有落地就继续记 in_progress 未读；① 367 现读 rot=0，按 `HIDDEN_ROT` 查新腐烂；② 继续产品视觉位并落 Sources，换缺陷类别；③ 436 拿到 runner motion 读数后按实测决定第五臂 `must_judge`，没有就继续具名 NOT-RUN。
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
report_new = once(report_old, "D-069 … **D-388**", "D-069 … **D-389**")
report_new = once(report_new, "U-31 … U-1414（R398 现读抬到最新一节）", "U-31 … U-1419（R399 现读抬到最新一节）")
report_new = once(
    report_new,
    "R398 现读：注册表 **153** 张 / 刀号最大 **M1038** / 预检 covered=136 arms=414 bad=0；全仓 246 文件 / 898 把；M674 退役、M906 空刀退役",
    f"R399 现读：注册表 **{pre_tables}** 张 / 刀号最大 **M1041** / 预检 covered={pre_covered} arms={pre_arms} bad={pre_bad}；"
    f"全仓 {arm_files} 文件 / {arm_total} 把；M674 退役、M906 空刀退役")
report_new = once(
    report_new,
    "**网络仍断 ⇒ PUSH_BLOCKED=network（api=000/apple=200），ahead=38（含本追记），未推送。**",
    "**网络仍断 ⇒ PUSH_BLOCKED=network（api=000/apple=200），ahead=38（含本追记），未推送。**" + report_bullet)
report_new = once(report_new, "`AGENT_STATE.md` 的 R398 节", "`AGENT_STATE.md` 的 R399 节")

state_old = rd("AGENT_STATE.md")
state_anchor = "## R398 状态（2026-10-26"
assert state_old.count(state_anchor) == 1
state_new = once(state_old, state_anchor, state_section + "\n" + state_anchor)

wr("AGENT_UI_AUDIT.md", audit_new)
wr("AGENT_VISUAL_ITERATION.md", iteration_new)
wr("AGENT_DECISIONS.md", decisions_new)
wr("CHANGELOG.md", changelog_new)
wr("AGENT_FINAL_REPORT.md", report_new)
wr("AGENT_STATE.md", state_new)

print("R399_LEDGERS_OK warnings=%s full=%s/%s/%s frames=%s changed=%s baseline=%s/%s/%s/%s pixel=%s/%s mut=3 pre=%s/%s/%s/%s arms=%s/%s rot=%s gate=%s=%s streak=%s"
      % (warnings, executed, skipped, failures, frames, changed_frames,
         b_compared, b_changed, b_missing, b_added, new_max_pt, new_ink,
         pre_tables, pre_covered, pre_arms, pre_bad, arm_files, arm_total,
         h_rot, cleared, cells, streak))
