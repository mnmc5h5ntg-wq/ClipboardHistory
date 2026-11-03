#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R398（第 397 轮 / Round 395）的台账。数字全部从本机日志解析。"""
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


build = log("/tmp/r398_build_final.log")
warnings = len(re.findall(r"warning:", build))
assert warnings == 0

full = log("/tmp/r398_full.log")
summaries = [tuple(int(x) for x in row) for row in
             re.findall(r"Executed (\d+) tests, with (\d+) tests skipped and (\d+) failures", full)]
big = [row for row in summaries if row[0] > 900]
assert big
executed, skipped, failures = big[-1]
assert (executed, skipped, failures) == (1057, 52, 0)

capture = log("/tmp/r398_capture.log")
cap = re.search(r"CAPTURED (\d+) -> /tmp/r398_shots", capture)
assert cap
frames = int(cap.group(1))
assert frames == 182
guard = {}
for tag in ("light", "dark"):
    m = re.search(r"DETAIL_LOADING_HINT %s fill=(\d+) 墨=(\d+) 对比=([0-9.]+)" % tag, capture)
    assert m, tag
    guard[tag] = (int(m.group(1)), int(m.group(2)), float(m.group(3)))
assert guard["light"][2] >= 4.5 and guard["dark"][2] >= 4.5
assert abs(guard["light"][2] - 4.84) < 0.01 and abs(guard["dark"][2] - 6.53) < 0.01

bandlog = log("/tmp/r398_old_new_band.log")
band = {}
for kind, tag, contrast in re.findall(
        r"DETAIL_LOADING (old|new) (light|dark) x=18\.\.115 y=102\.\.120 .*contrast=([0-9.]+)", bandlog):
    band[(kind, tag)] = float(contrast)
assert set(band) == {("old", "light"), ("old", "dark"), ("new", "light"), ("new", "dark")}
assert abs(band[("old", "light")] - 2.86) < 0.01
assert abs(band[("old", "dark")] - 4.52) < 0.01
assert band[("new", "light")] >= 4.5 and band[("new", "dark")] >= 4.5
assert band[("old", "light")] < 4.5

diff = log("/tmp/r398_framediff.log")
dm = re.search(r"FRAME_DIFF 比了=(\d+) 变了=(\d+)", diff)
assert dm
total_frames, changed_frames = [int(x) for x in dm.groups()]
changed_names = sorted(re.findall(r"^  changed (.+)$", diff, re.M))
expected_changed = sorted([
    "detail-2-file-720x520-dark.png",
    "detail-2-file-720x520-light.png",
    "detail-loading-720x520-dark.png",
    "detail-loading-720x520-light.png",
    "detail-loading-composed-720x520-dark.png",
    "detail-loading-composed-720x520-light.png",
])
assert (total_frames, changed_frames) == (182, 6)
assert changed_names == expected_changed, changed_names

baseline = log("/tmp/r398_framebaseline.log")
bm = re.search(r"FRAME_BASELINE_COMPARED=(\d+)\s+FRAME_BASELINE_CHANGED=(\d+)"
               r"\s+FRAME_BASELINE_MISSING=(\d+)\s+FRAME_BASELINE_ADDED=(\d+)", baseline)
assert bm
b_compared, b_changed, b_missing, b_added = [int(x) for x in bm.groups()]
assert (b_compared, b_changed, b_missing, b_added) == (182, 0, 0, 0)
bupdate = log("/tmp/r398_framebaseline_update.log")
assert "FRAME_BASELINE_UPDATED=182" in bupdate

source_guard = log("/tmp/r398_guard.log")
assert "testDetailLoadingMessageUsesTheAAInkSeam]' passed" in source_guard
assert "Executed 1 test, with 0 failures" in source_guard

mut = log("/tmp/r398_mut.log")
assert "M1037" in mut and "M1038" in mut
assert "M1037 加载句墨退回 secondary（源守卫） ⇒ CAUGHT 红得对=True 命中=True" in mut
assert "M1038 加载句墨退回 secondary（像素守卫） ⇒ CAUGHT 红得对=True 命中=True" in mut
assert "R398_MUTATE 刀=2 CAUGHT=2 红得不对=0 RESTORE_CLEAN=yes" in mut
assert "还原后复跑：MotionCatalogTests/testDetailLoadingMessageUsesTheAAInkSeam=ESCAPED UICaptureTests/testCaptureKeyViews=ESCAPED" in mut

install = log("/tmp/r398_install.log")
assert "INSTALL_RESULT=ok" in install and "INSTALL_SHA_MATCH=1" in install
entries = re.search(r"INSTALL_ENTRIES_BEFORE=(\d+)\s+INSTALL_ENTRIES_AFTER=(\d+)", install)
assert entries
entries_before, entries_after = entries.groups()
assert entries_before == entries_after == "381"

pre = log("/tmp/r398_precheck.log")
pre_line = re.search(r"NEEDLE_PRECHECK tables=(\d+) covered=(\d+) arms=(\d+) bad=(\d+)", pre)
arm_line = re.search(r"ARM_TOTAL files=(\d+) arms=(\d+) dupes=(\d+) repeats=(\d+)", pre)
assert pre_line and arm_line
pre_tables, pre_covered, pre_arms, pre_bad = [int(x) for x in pre_line.groups()]
arm_files, arm_total, arm_dupes, arm_repeats = [int(x) for x in arm_line.groups()]
assert (pre_tables, pre_covered, pre_arms, pre_bad) == (153, 136, 414, 0)
assert (arm_files, arm_total) == (246, 898)
assert arm_dupes == 0 and arm_repeats == 0

hidden = log("/tmp/r398_hidden.log")
h = re.search(r"HIDDEN_ARMS 表=(\d+) 可判=(\d+) rot=(\d+) 抽不出=(\d+) 已声明表=(\d+)"
              r" 已声明死针=(\d+) 上界 rot=(\d+)", hidden)
assert h
h_tables, h_judged, h_rot, h_opaque, h_dtables, h_ddead, h_rot_ceiling = [int(x) for x in h.groups()]
assert (h_tables, h_judged, h_rot, h_opaque, h_dtables, h_ddead, h_rot_ceiling) == (240, 832, 0, 6, 6, 0, 0)

gate = log("/tmp/r398_gate.log")
g = re.search(r"MOTION_LEDGER 表面=(\d+) 状态=(\d+) 格子=(\d+) 行数=(\d+)"
              r" 已清账=(\d+) 未清账=(\d+) 地板=(\d+)", gate)
assert g
surfaces, states, cells, rows, cleared, uncleared, floor_count = [int(x) for x in g.groups()]
assert (surfaces, states, cells, rows, cleared, uncleared, floor_count) == (18, 9, 162, 162, 162, 0, 162)
assert "MOTION_LEDGER_RESULT=ok" in gate

streak_out = subprocess.check_output(
    ["python3", os.path.join(ROOT, "scripts/product_streak.py"), "--streak-for", "397"],
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

ui_heading = "## 第 396 轮（R397"
ui_section = f"""## 第 397 轮（R398 · 2026-10-26 · U-1410…U-1414）：详情加载唯一那句话亮档 2.86:1 → 4.84（暗 4.52 → 6.53）；pane 墨档接进加载态 + 双刀（U-1410…U-1414 · 产品 2 文件，视觉主线）

- **U-1410：⓪ 网络与 CI。** 本轮开场 `git push origin main` 被 SSH 拒（`Connection closed by 20.205.243.166 port 22`），同分钟 `api=000` / `apple=200` ⇒ `PUSH_BLOCKED=network`；本地 ahead=36（R397 两次提交之后），不写已推送。`origin/main` 本地 ref 仍 `5c7814e`；未 force，网络不可达无法 fetch 确认远端是否被推进。2 次同形探测额度已用完。恢复后一次 push 只为 head 生成新 run；此前未读的旧两跑仍要单独按步骤读。
- **U-1411：② 产品视觉位 —— 详情加载态的唯一一句话读不清。** 先看图：`detail-loading-720x520-{{light,dark}}` 里「正在加载预览…」是整块加载面板唯一的人话。按字墨 bbox 定位后只读 x 18..115 / y 102..120pt 的句子带：旧 `.secondary` 亮 **{band[("old", "light")]:.2f}** / 暗 **{band[("old", "dark")]:.2f}:1**（暗档刚好贴 4.5 线，亮档低于 AA）；新 pane 墨档亮 **{band[("new", "light")]:.2f}** / 暗 **{band[("new", "dark")]:.2f}:1**。修法：`DetailLoadingView` 的句子改走 R397 已立的 `StatePresentation.paneMessageInkStyle`；三根骨架不动，inline `StateLine` 的 `.subdued` 也不动。产品 2 文件（DetailPreviewViews 接线 + StatePresentation 的 pane 注释扩展到加载态）。
- **U-1412：判据与刀。** `MotionCatalogTests.testDetailLoadingMessageUsesTheAAInkSeam` 钉加载句的接线：`Text("正在加载预览…")` 之后 240 字符内不得出现硬写 `.secondary`，必须出现 `StatePresentation.paneMessageInkStyle`；`testCaptureKeyViews` 在真实 182 帧里读同一条句子带（带空写具名 NOT-RUN）。`M1037`（源接线）/`M1038`（捕获帧像素）双 **CAUGHT**、红得对=2、红得不对=0、还原干净、还原后双 ESCAPED；一张表只写 `DetailPreviewViews.swift` 一个文件靶（D-384）。**带子身份**：旧/新读数都在同一条由 bbox 推出的带上，旧亮 2.86 先量到、再修。
- **U-1413：BACKLOG 436 处置（仍未结案）。** 本轮无新的 runner motion 读数；R390 本地完整卷仍是 `Executed {motion_exec} tests, with {motion_skip} tests skipped and {motion_fail} failures`、`MOTION_SUMMARY {motion_summary}`、`MOTION_RESOLVE_SUMMARY judged={motion_judged}/{motion_total} not-run={motion_notrun}`，现有 4 臂登记跑 `motion_floor_gate.py` 的 exit 1（UNLISTED `settings-reset-fade`）本地复现仍成立。**不关单、不改 JSON/自测、不猜 `must_judge`**；runner 卷继续记具名 NOT-RUN。
- **U-1414：① 367 rot 与八步。** `HIDDEN_ARMS 表={h_tables} 可判={h_judged} rot={h_rot} 抽不出={h_opaque} 已声明表={h_dtables} 已声明死针={h_ddead} 上界 rot={h_rot_ceiling} 处置=ok`；预检 `tables={pre_tables} covered={pre_covered} arms={pre_arms} bad={pre_bad}`、全仓 {arm_files} 文件 / {arm_total} 把；`M1037/M1038` 全 CAUGHT。build **{warnings}** 告警；全量 `Executed {executed} tests, with {skipped} tests skipped and {failures} failures`；捕获 `CAPTURED {frames} -> /tmp/r398_shots`，与 R397 逐张比 `变了={changed_frames}`（detail-loading / detail-loading-composed / detail-2-file 亮暗各一张；其余默认路径不变），帧基线同一笔 `UPDATED=182`、复验 `COMPARED={b_compared} CHANGED={b_changed} MISSING={b_missing} ADDED={b_added}`；换装 `INSTALL_RESULT=ok`、`INSTALL_SHA_MATCH=1`、条目 `{entries_before}={entries_after}`；清账表 `表面={surfaces} 状态={states} 格子={cells} 已清账={cleared} 未清账={uncleared} 地板={floor_count}`；产品面连续零改动 **{streak}** 轮（as-of 397；本轮产品视觉已落 Sources，现读 `python3 scripts/product_streak.py --streak-for 397`）。电池在台账落盘后复跑，读数写进本笔追记。
"""

iteration = f"""## Round 395 · R398（第 397 轮 · 2026-10-26）：详情加载唯一那句话亮档 2.86:1 → 4.84（暗 4.52 → 6.53）；pane 墨档接进加载态 + 双刀（产品 2 文件，视觉主线）

真看图：`detail-loading-720x520-{{light,dark}}` 的「正在加载预览…」是整块加载面板唯一的人话；旧 `.secondary` 在句子带（x18..115/y102..120pt）亮 **2.86** / 暗 **4.52:1**（暗档刚好贴线，亮档低于 AA 4.5）。新 pane 墨档亮 **4.84** / 暗 **6.53**。产品改法：`DetailLoadingView` 的句子改走 R397 的 `StatePresentation.paneMessageInkStyle`；骨架与 inline StateLine 不动。detail-loading / detail-loading-composed / detail-2-file 亮暗共 6 张变化，其余 176 张不变；基线同笔 update 后 182/0。

**七维度自评**（恰七行，每格 n/15）：

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | 14/15 | 真看了加载态亮/暗新旧帧，量了句子带；扣 1：只审了加载态这一族。 |
| 判据有效性 | 15/15 | 源接线守卫 + 真实捕获帧像素守卫；M1037/M1038 双 CAUGHT、还原后双 ESCAPED。 |
| 假绿防御 | 15/15 | 先用 bbox 钉带、再量旧读数 2.86/4.52，修后同带 4.84/6.53；没有拿别的行当句子。 |
| 产品面推进 | 14/15 | 真落 Sources 视觉：加载态唯一信息；扣 1：单点修复。 |
| 台账一致性 | 14/15 | U-1410…U-1414、D-388、436、计数器全从日志解析；扣 1：436 仍开。 |
| 交付诚实性 | 15/15 | 明写暗档旧值 4.52 只是刚好贴线、不是失败；电池/网络分开记。 |
| 可复核性 | 15/15 | 句子带坐标、旧/新双读数、两把刀、捕获卷、基线、precheck/rot 都有原文。 |

均分 = 102/105 ≈ 14.6/15（97）。
"""

decision = """
### D-388（398）加载态也是 pane-only 的一句话：走同一档 AA 墨，inline 状态不跟着抬

R398 现读：`DetailLoadingView` 的「正在加载预览…」旧用 `.secondary`，句子带（x 18..115、y 102..120pt）亮 **2.86:1**、暗 **4.52:1**；亮档低于 AA 正文线 4.5。改走 `StatePresentation.paneMessageInkStyle` 后亮 **4.84** / 暗 **6.53**。三根骨架与 inline `StateLine` 的 `.subdued` 都不动。
**Why**：加载态和空态一样，整块面板只剩这句话；但它是短暂状态，容易被"反正马上就走"放过。暗档旧值 4.52 只是刚好贴线，不能把"临界通过"写成"暗档也失败"。同一 `.secondary` 在 inline 与 pane 两种表面承担的信息量不同，必须分表面取墨。
**How to apply**：① 加载/空态的 pane-only 句子按 4.5 量，inline 状态仍按 subdued；② 修法只改 pane 的取墨缝，不把 `messageInk(for:)` 的 inline 真值表改绿；③ 像素判据先按字墨 bbox 钉住句子，旧/新同带读数；④ 源接线刀与捕获帧像素刀分开（R398 M1037/M1038）。
"""

changelog = """### 详情加载唯一那句话亮档 2.86:1 → 4.84（暗 4.52 → 6.53）；pane 墨档接进加载态 + 双刀（R398 / 第 397 轮 / Round 395 / U-1410…U-1414 · 产品 2 文件，视觉主线）

"""

report_bullet = """
- **R398（视觉主线）**：详情加载态的「正在加载预览…」是整块面板唯一的人话，旧 `.secondary` 在句子带（x18..115/y102..120pt）亮 `2.86` / 暗 `4.52:1`，亮档低于 AA 4.5。`DetailLoadingView` 的句子改走 `StatePresentation.paneMessageInkStyle`；骨架与 inline StateLine 不动。修后亮 `4.84` / 暗 `6.53`。6 张加载帧变化，基线同笔 update 后 182/0；全量 1057/52/0；M1037/M1038 双 CAUGHT。436 无新 runner 读数，仍未结案；rot 0/0。**网络仍断 ⇒ PUSH_BLOCKED=network（api=000/apple=200），ahead=36（落笔前），未推送。**
"""

state_section = f"""## R398 状态（2026-10-26 · 本地 · 第 397 轮 / Round 395）：详情加载唯一那句话亮档 2.86:1 → 4.84（暗 4.52 → 6.53）；pane 墨档接进加载态 + 双刀（产品 2 文件，视觉主线）

最后更新：2026-10-26（本地 · R398 / 第 397 轮 / Round 395）：先真看 `detail-loading-720x520-{{light,dark}}` 的「正在加载预览…」：旧 `.secondary` 在亮档偏灰。按字墨 bbox 定位后只读 x 18..115 / y 102..120pt：旧亮 **2.86** / 暗 **4.52:1**（暗档刚好贴 4.5 线，亮档低于 AA），新 pane 墨档亮 **4.84** / 暗 **6.53:1**。产品改法：`DetailLoadingView` 的句子改走 `StatePresentation.paneMessageInkStyle`；三根骨架与 inline `StateLine` 的 `.subdued` 保持不动。判据：源接线守卫 + 捕获帧像素守卫；M1037/M1038 双 CAUGHT、还原后双 ESCAPED。detail-loading / detail-loading-composed / detail-2-file 亮暗 6 张变化，其余 176 张不变；基线同笔 `UPDATED=182`，复验 182/0/0/0。全量 `Executed {executed} tests, with {skipped} tests skipped and {failures} failures`；换装 `ok / SHA_MATCH=1 / 381=381`；清账表 162=162；`HIDDEN_ARMS 表={h_tables} 可判={h_judged} rot={h_rot} … 上界 rot={h_rot_ceiling} 处置=ok`；预检 `tables={pre_tables} covered={pre_covered} arms={pre_arms} bad={pre_bad}`、全仓 {arm_files} 文件 / {arm_total} 把；产品面连续零改动 **{streak}** 轮（as-of 397，现读 `python3 scripts/product_streak.py --streak-for 397`；本轮产品视觉已落 Sources）。电池在台账落盘后复跑，读数写进本笔追记。

本轮做了什么：
① ⓪ 网络：push 被 SSH 拒 + `api=000`/`apple=200` ⇒ `PUSH_BLOCKED=network`；ahead=36，未推送；未 force。
② 看图找到真缺陷：详情加载态唯一那句话亮档 2.86、暗 4.52；修 Sources 后 4.84/6.53。
③ 判据：源接线守卫 + 捕获帧像素守卫；M1037/M1038 双 CAUGHT、还原后双 ESCAPED。
④ 带子身份：按字墨 bbox 钉 x18..115/y102..120；旧/新都在同带读数，没有假绿。
⑤ 367：hidden 表 {h_tables} / 可判 {h_judged} / rot {h_rot} / 上界 {h_rot_ceiling}；预检 {pre_tables}/{pre_covered}/{pre_arms}/{pre_bad}。
⑥ 验证：build 0 告警；全量 `{executed}/{skipped}/{failures}`；捕获 {frames} 帧、6 帧变化、基线 update 后 182/0；换装 ok；清账表 162=162。

验证读数（现读）：`DETAIL_LOADING old light=2.86 dark=4.52 / new light=4.84 dark=6.53`（x18..115/y102..120pt）；捕获 `DETAIL_LOADING_HINT light 墨={guard["light"][1]} 对比={guard["light"][2]:.2f}`、`dark 墨={guard["dark"][1]} 对比={guard["dark"][2]:.2f}`；`M1037/M1038` 双 CAUGHT；`HIDDEN_ARMS … rot={h_rot} … 处置=ok`。

NOT-RUN / 阻塞（分开写）：① **`PUSH_BLOCKED=network`**：push 被 SSH 拒 + `api=000`/`apple=200`；本地 ahead=36（R398 主笔前，追记后 38）；② 旧的两跑与 R387–R397 本地提交的 conclusion **未读**（网络）；③ BACKLOG 436 的 runner motion 卷未读（本地 5/5、UNLISTED `settings-reset-fade` 仍可复现）；④ 亮档真机腿仍没跑；⑤ macOS 12 的紧凑详情头仍走旧截断（13+ 才有 ViewThatFits）。

下一轮（R399）的靶：⓪ 先 `git push origin main`（禁 amend/force）并复核 ahead=0；一次 push 只为 head 生成新 run，旧两跑仍要单独按步骤读；① 367 现读 rot=0，按 `HIDDEN_ROT` 查新腐烂；② 继续产品视觉位并落 Sources；③ 436 待 runner motion 读数恢复后再决定第五臂 `must_judge`，本轮仍不动 JSON/自测。
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
report_new = once(report_old, "D-069 … **D-387**", "D-069 … **D-388**")
report_new = once(report_new, "U-31 … U-1409（R397 现读抬到最新一节）", "U-31 … U-1414（R398 现读抬到最新一节）")
report_new = once(
    report_new,
    "R397 现读：注册表 **152** 张 / 刀号最大 **M1036** / 预检 covered=135 arms=412 bad=0；全仓 245 文件 / 896 把；M674 退役、M906 空刀退役",
    f"R398 现读：注册表 **{pre_tables}** 张 / 刀号最大 **M1038** / 预检 covered={pre_covered} arms={pre_arms} bad={pre_bad}；"
    f"全仓 {arm_files} 文件 / {arm_total} 把；M674 退役、M906 空刀退役")
report_new = once(
    report_new,
    "**网络仍断 ⇒ PUSH_BLOCKED=network（api=000/apple=200），ahead=36（含本追记），未推送。**",
    "**网络仍断 ⇒ PUSH_BLOCKED=network（api=000/apple=200），ahead=36（含本追记），未推送。**" + report_bullet)
report_new = once(report_new, "`AGENT_STATE.md` 的 R397 节", "`AGENT_STATE.md` 的 R398 节")

state_old = rd("AGENT_STATE.md")
state_anchor = "## R397 状态（2026-10-26"
assert state_old.count(state_anchor) == 1
state_new = once(state_old, state_anchor, state_section + "\n" + state_anchor)

wr("AGENT_UI_AUDIT.md", audit_new)
wr("AGENT_VISUAL_ITERATION.md", iteration_new)
wr("AGENT_DECISIONS.md", decisions_new)
wr("CHANGELOG.md", changelog_new)
wr("AGENT_FINAL_REPORT.md", report_new)
wr("AGENT_STATE.md", state_new)

print("R398_LEDGERS_OK warnings=%s full=%s/%s/%s frames=%s changed=%s baseline=%s/%s/%s/%s old=%s/%s new=%s/%s mut=2 pre=%s/%s/%s/%s arms=%s/%s rot=%s gate=%s=%s streak=%s"
      % (warnings, executed, skipped, failures, frames, changed_frames,
         b_compared, b_changed, b_missing, b_added,
         band[("old", "light")], band[("old", "dark")], band[("new", "light")], band[("new", "dark")],
         pre_tables, pre_covered, pre_arms, pre_bad, arm_files, arm_total,
         h_rot, cleared, cells, streak))
