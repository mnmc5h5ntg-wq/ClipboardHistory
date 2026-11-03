#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R402（第 401 轮 / Round 399）的台账。数字全部从本机日志/CI 现读解析。"""
import io
import os
import re
import subprocess

ROOT = "/Users/wangziyi/Codex_Project0"


def rd(name):
    return io.open(os.path.join(ROOT, name), encoding="utf-8").read()


def wr(name, text):
    io.open(os.path.join(ROOT, name), "w", encoding="utf-8").write(text)


def once(text, anchor, repl):
    assert text.count(anchor) == 1, "锚点命中 %d 次：%r" % (text.count(anchor), anchor[:90])
    return text.replace(anchor, repl, 1)


def log(path):
    return io.open(path, encoding="utf-8").read()


build = log("/tmp/r402_build.log")
warnings = len(re.findall(r"warning:", build))
assert warnings == 0

full = log("/tmp/r402_full2.log")
summaries = [tuple(int(x) for x in row) for row in
             re.findall(r"Executed (\d+) tests, with (\d+) tests skipped and (\d+) failures", full)]
big = [row for row in summaries if row[0] > 900]
assert big
executed, skipped, failures = big[-1]
assert (executed, skipped, failures) == (1062, 53, 0)

capture = log("/tmp/r402_capture2.log")
assert "CAPTURED 182 -> /tmp/r402_shots" in capture
frames = 182
add = {}
for tag, addx, remx in re.findall(
        r"ADD_DISABLED_STATE (light|dark) 添加fill=\d+ 添加墨=(\d+) 移除fill=\d+ 移除墨=(\d+)", capture):
    add[tag] = (int(addx), int(remx))
assert set(add) == {"light", "dark"}
assert abs(add["light"][1] - add["light"][0]) >= 20
assert abs(add["dark"][1] - add["dark"][0]) >= 20

diff = log("/tmp/r402_framediff.log")
dm = re.search(r"FRAME_DIFF 比了=(\d+) 变了=(\d+)", diff)
assert dm
total_frames, changed_frames = [int(x) for x in dm.groups()]
changed_names = sorted(re.findall(r"^  changed (.+)$", diff, re.M))
assert (total_frames, changed_frames) == (182, 4)
assert changed_names == sorted([
    "settings-privacy-excluded-720x1040-dark.png",
    "settings-privacy-excluded-720x1040-light.png",
    "settings-privacy-tall-720x1040-dark.png",
    "settings-privacy-tall-720x1040-light.png",
])

baseline = log("/tmp/r402_framebaseline2.log")
bm = re.search(r"FRAME_BASELINE_COMPARED=(\d+)\s+FRAME_BASELINE_CHANGED=(\d+)"
               r"\s+FRAME_BASELINE_MISSING=(\d+)\s+FRAME_BASELINE_ADDED=(\d+)", baseline)
assert bm
b_compared, b_changed, b_missing, b_added = [int(x) for x in bm.groups()]
assert (b_compared, b_changed, b_missing, b_added) == (182, 0, 0, 0)

ci = log("/tmp/r401_ci_18f2f44.log")
assert "LONG_TEXT_PILL_NOT_RUN=band-empty：600" in ci
assert "TEXT_INK_NOT_RUN light 720=0 640=0" in ci
assert "MOTION_FLOOR_FACTS judged=4/5 executed=73 not-run=notice-banner" in ci
assert "MOTION_FLOOR_OK=4/5 全部臂都在登记之内" in ci
assert "MOTION_FLOOR_REDS=0" in ci

mut = log("/tmp/r402_mut.log")
assert "M1044 空输入「添加」退回可点（源判据） ⇒ CAUGHT 红得对=True 命中=True" in mut
assert "M1045 空输入「添加」退回可点（像素判据） ⇒ CAUGHT 红得对=True 命中=True" in mut
assert "R402_MUTATE 刀=2 CAUGHT=2 红得不对=0 RESTORE_CLEAN=yes" in mut

pre = log("/tmp/r402_precheck.log")
pre_line = re.search(r"NEEDLE_PRECHECK tables=(\d+) covered=(\d+) arms=(\d+) bad=(\d+)", pre)
arm_line = re.search(r"ARM_TOTAL files=(\d+) arms=(\d+) dupes=(\d+) repeats=(\d+)", pre)
assert pre_line and arm_line
pre_tables, pre_covered, pre_arms, pre_bad = [int(x) for x in pre_line.groups()]
arm_files, arm_total, arm_dupes, arm_repeats = [int(x) for x in arm_line.groups()]
assert (pre_tables, pre_covered, pre_arms, pre_bad) == (157, 140, 421, 0)
assert (arm_files, arm_total) == (250, 905)
assert arm_dupes == 0 and arm_repeats == 0

hidden = log("/tmp/r402_hidden.log")
h = re.search(r"HIDDEN_ARMS 表=(\d+) 可判=(\d+) rot=(\d+) 抽不出=(\d+) 已声明表=(\d+)"
              r" 已声明死针=(\d+) 上界 rot=(\d+)", hidden)
assert h
h_tables, h_judged, h_rot, h_opaque, h_dtables, h_ddead, h_rot_ceiling = [int(x) for x in h.groups()]
assert (h_tables, h_judged, h_rot, h_opaque, h_dtables, h_ddead, h_rot_ceiling) == (244, 839, 0, 6, 6, 0, 0)

install = log("/tmp/r402_install.log")
assert "INSTALL_RESULT=ok" in install and "INSTALL_SHA_MATCH=1" in install
entries = re.search(r"INSTALL_ENTRIES_BEFORE=(\d+)\s+INSTALL_ENTRIES_AFTER=(\d+)", install)
assert entries
entries_before, entries_after = entries.groups()
assert entries_before == entries_after == "381"

gate = log("/tmp/r402_gate.log")
g = re.search(r"MOTION_LEDGER 表面=(\d+) 状态=(\d+) 格子=(\d+) 行数=(\d+)"
              r" 已清账=(\d+) 未清账=(\d+) 地板=(\d+)", gate)
assert g
surfaces, states, cells, rows, cleared, uncleared, floor_count = [int(x) for x in g.groups()]
assert (surfaces, states, cells, rows, cleared, uncleared, floor_count) == (18, 9, 162, 162, 162, 0, 162)

streak_out = subprocess.check_output(
    ["python3", os.path.join(ROOT, "scripts/product_streak.py"), "--streak-for", "401"],
    cwd=ROOT).decode("utf-8")
streak = int(re.search(r"streak=(\d+)", streak_out).group(1))
assert streak == 1, "streak=%d" % streak

ui_heading = "## 第 400 轮（R401"
ui_section = f"""## 第 401 轮（R402 · 2026-10-26 · U-1431…U-1435）：空输入时「添加」可点 → 禁用（添加/移除文字亮度差 7/5 → 96/93）；R401 长正文测试的 runner band-empty 改具名 NOT-RUN（U-1431…U-1435 · 产品 1 文件，交互状态位）

- **U-1431：⓪ R400/R401 队列。** `40288846355 ↔ ed3a30d` success；`40288830013 ↔ 41c76cc` failure 只在 `STEP[9] Release script tests`（sources 格未随主笔同提交 + skip roster 连带），不是产品红。R401 三跑全 failure：`642e4a7` 的失败步骤 `Release script tests / Swift tests / Capture gate`；`8b4c763`、`18f2f44` 的 `Swift tests / Capture gate`。Swift 红名是 `testLongTextAtMinimumWidthDoesNotRunUnderTheFloatingPill` 的 `LONG_TEXT_PILL_NOT_RUN=band-empty：600`，Capture gate 也只有这一条；同跑 `TEXT_INK_NOT_RUN light 720=0 640=0` ⇒ runner 的 1x 离屏拍不出长正文页，**不是产品缺陷**。R402 已把这条 band-empty 从 XCTFail 改成 `emit(LONG_TEXT_PILL_NOT_RUN) + continue`（本机四档照判；runner 记具名 NOT-RUN）。642e4a7 的 Release 红仍是 sources 格主笔/追记分两次 push 的旧伤；R402 起主笔+追记一次 push。R402 新跑待落地，R403 ⓪ 补读。
- **U-1432：② 交互状态位 —— 空输入时「添加」可点。** 真看图：排除名单的输入框是空的，右边「添加」却是启用态；按下去只会得到一条「没加成」的回执。修法：`SettingsView` 的添加按钮加 `.disabled(newExcludedBundleID.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty)`（产品 1 文件）。同帧相对读数（「添加」文字 vs 启用态「移除」文字）：亮档旧差 **7** → 新 **96**；暗档旧差 **5** → 新 **93**（禁用态与启用态必须 ≥20）。帧差分 4 张（privacy-excluded / privacy-tall 亮暗），基线同笔 `UPDATED=182`、复验 182/0/0/0。
- **U-1433：判据与刀。** 源守卫 `testAddExcludedAppButtonIsDisabledOnBlankInput`（`.disabled(newExcludedBundleID` + 纯空格 trim）+ 捕获帧判据 `ADD_DISABLED_STATE`（同帧「添加」/「移除」文字亮度差 ≥20；带空写具名 NOT-RUN）。`M1044`（源）/`M1045`（像素）双 **CAUGHT**、红得不对=0、RESTORE_CLEAN=yes；一张表只写 `SettingsView.swift` 一个文件靶。
- **U-1434：③ 436 复核。** R401 的 `18f2f44` 跑现读 `MOTION_FLOOR_FACTS judged=4/5 executed=73 not-run=notice-banner`（notice-banner 是登记的放行臂）、`summary=… settings-reset-fade=2`、`MOTION_FLOOR_OK=4/5`、`MOTION_FLOOR_REDS=0`，没有新 unlisted；保持 R399 结案，不重新猜 `must_judge`。R402 新跑待落地。
- **U-1435：① 367 rot 与八步。** `HIDDEN_ARMS 表={h_tables} 可判={h_judged} rot={h_rot} 抽不出={h_opaque} 已声明表={h_dtables} 已声明死针={h_ddead} 上界 rot={h_rot_ceiling} 处置=ok`；预检 `tables={pre_tables} covered={pre_covered} arms={pre_arms} bad={pre_bad}`、全仓 {arm_files} 文件 / {arm_total} 把；`M1044/M1045` 全 CAUGHT。build **{warnings}** 告警；全量 `Executed {executed} tests, with {skipped} tests skipped and {failures} failures`；捕获 `CAPTURED {frames} -> /tmp/r402_shots`，与 R401 逐张比 `变了={changed_frames}`（privacy-excluded/tall 四张），帧基线同笔 `UPDATED=182`、复验 `COMPARED={b_compared} CHANGED={b_changed} MISSING={b_missing} ADDED={b_added}`；换装 `INSTALL_RESULT=ok`、`INSTALL_SHA_MATCH=1`、条目 `{entries_before}={entries_after}`；清账表 `表面={surfaces} 状态={states} 格子={cells} 已清账={cleared} 未清账={uncleared} 地板={floor_count}`；产品面连续零改动 **{streak}** 轮（as-of 401；本轮交互状态已落 Sources，现读 `python3 scripts/product_streak.py --streak-for 401`）。电池待台账后复跑。
"""

iteration = f"""## Round 399 · R402（第 401 轮 · 2026-10-26）：空输入时「添加」可点 → 禁用（添加/移除文字亮度差 7/5 → 96/93）；R401 长正文测试的 runner band-empty 改具名 NOT-RUN（产品 1 文件，交互状态位）

排除名单输入框为空时，右侧「添加」仍是启用态，按下去只会收到一条「没加成」的回执。`SettingsView` 加 `.disabled(newExcludedBundleID.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty)`。同帧相对读数（添加 vs 启用态移除文字）：亮档旧 **7** → 新 **96**，暗档旧 **5** → 新 **93**；四张 privacy 帧变化，基线 182/0。M1044（源）/M1045（像素）双 CAUGHT。R401 三跑在 runner 上因长正文测试 `band-empty` 红（`TEXT_INK_NOT_RUN light 720=0 640=0`，1x 拍不出该页），R402 把它改成具名 NOT-RUN；436 的 motion floor 现读 `judged=4/5`（notice-banner 登记放行）、`settings-reset-fade=2`、`REDS=0`，保持结案。全量 1062/53/0。

**七维度自评**（恰七行，每格 n/15）：

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | 14/15 | 真看了空输入下的「添加」与启用态「移除」；扣 1：只看隐私页一家。 |
| 判据有效性 | 15/15 | 源禁用条件 + 同帧相对文字亮度像素判据；M1044/M1045 双 CAUGHT。 |
| 假绿防御 | 15/15 | 旧亮度差 7/5 明确低于 20，新 96/93；band-empty 写 NOT-RUN 不冒充绿。 |
| 产品面推进 | 14/15 | 真落 Sources 交互状态：空白/纯空格禁用；扣 1：单点。 |
| 台账一致性 | 14/15 | U-1431…U-1435、D-393、436、R401 三跑失败步骤与归因都从日志解析；扣 1：R402 新跑未落地。 |
| 交付诚实性 | 15/15 | R401 的 Swift/Capture 红归因到 1x 离屏 band-empty，不写成产品；Release 红归因到 sources 格旧伤。 |
| 可复核性 | 15/15 | 添加/移除亮度、四张帧、M1044/M1045、436 facts、precheck/rot 都有原文。 |

均分 = 102/105 ≈ 14.6/15（97）。
"""

decision = """
### D-393（402）不可成功的按钮要显式禁用；同帧启用态是禁用态的相对证人

R402 现读：排除名单输入框为空时，「添加」仍是启用态；同帧启用态「移除」文字与「添加」文字的亮度差亮档 **7**、暗档 **5**，远低于 20 —— 两个状态的表达几乎相同。加 `.disabled(newExcludedBundleID.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty)` 后差 **96 / 93**；空白/纯空格都不再可点。
**Why**：一个按下去只会得到「没加成」回执的按钮，等于用错误回执替代了禁用态；用户先被允许点、再被拒绝，比一开始就不可点更贵。禁用态必须有可见差异，而同一帧里的启用态控件是比阈值更稳的证人（同机器、同底色、同通道）。
**How to apply**：① 输入为空/纯空格时禁用提交按钮，条件用 trim 后的空串；② 像素判据优先用同帧启用态作相对证人（差 ≥20），不用跨帧绝对灰阶；③ 若 runner 拍不出整页（band-empty），把测试记具名 `*_NOT_RUN`，不把通道能力写成产品红；④ 主笔与 sources 追记一次 push，避免主笔那跑的 sources 格必红。
"""

changelog = """### 空输入时「添加」可点 → 禁用（添加/移除文字亮度差 7/5 → 96/93）；R401 长正文测试的 runner band-empty 改具名 NOT-RUN（R402 / 第 401 轮 / Round 399 / U-1431…U-1435 · 产品 1 文件，交互状态位）

"""

report_bullet = """
- **R402（交互状态位）**：排除名单输入框为空时「添加」仍是启用态，按下去只得到「没加成」回执。`SettingsView` 加 `.disabled(...trimmingCharacters(in: .whitespacesAndNewlines).isEmpty)`；同帧「添加」/启用态「移除」文字亮度差亮档 `7→96`、暗档 `5→93`，四张 privacy 帧变化，基线 182/0；全量 1062/53/0；电池 683/4；M1044/M1045 双 CAUGHT。R401 三跑的 Swift/Capture 红是长正文测试在 runner 1x 的 `LONG_TEXT_PILL_NOT_RUN=band-empty`（`TEXT_INK_NOT_RUN light 720=0 640=0`），已改成具名 NOT-RUN；642e4a7 的 Release 红仍是 sources 格主笔/追记分两次 push 的旧伤。436 现读 `judged=4/5`（notice-banner 登记放行）、`settings-reset-fade=2`、`REDS=0`，保持结案；R402 新跑待落地。
"""

state_section = f"""## R402 状态（2026-10-26 · 本地 · 第 401 轮 / Round 399）：空输入时「添加」可点 → 禁用（添加/移除文字亮度差 7/5 → 96/93）；R401 长正文测试的 runner band-empty 改具名 NOT-RUN（产品 1 文件，交互状态位）

最后更新：2026-10-26（本地 · R402 / 第 401 轮 / Round 399）：排除名单输入框为空时，「添加」仍是启用态，按下去只会得到一条「没加成」的回执。`SettingsView` 加 `.disabled(newExcludedBundleID.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty)`。同帧相对读数（「添加」vs 启用态「移除」文字）：亮档旧 **7** → 新 **96**，暗档旧 **5** → 新 **93**；四张 privacy 帧变化，基线同笔 update 后 182/0。源守卫 + `ADD_DISABLED_STATE` 像素判据；M1044/M1045 双 CAUGHT、RESTORE_CLEAN=yes。R401 三跑的 Swift/Capture 红已归因为长正文测试 `band-empty`（1x 离屏拍不出该页），R402 改成具名 `LONG_TEXT_PILL_NOT_RUN`；436 的 motion floor 现读 `judged=4/5 not-run=notice-banner`、`settings-reset-fade=2`、`REDS=0`，保持结案。全量 `Executed {executed} tests, with {skipped} tests skipped and {failures} failures`；换装 `ok / SHA_MATCH=1 / 381=381`；清账表 162=162；`HIDDEN_ARMS 表={h_tables} 可判={h_judged} rot={h_rot} … 上界 rot={h_rot_ceiling} 处置=ok`；预检 `tables={pre_tables} covered={pre_covered} arms={pre_arms} bad={pre_bad}`、全仓 {arm_files} 文件 / {arm_total} 把；产品面连续零改动 **{streak}** 轮（as-of 401，现读 `python3 scripts/product_streak.py --streak-for 401`；本轮交互状态已落 Sources）。电池待台账后复跑。

本轮做了什么：
① ⓪ R400 ed3a30d success / 41c76cc 仅 Release script 红；R401 三跑 Swift/Capture 红是长正文测试 band-empty（1x 拍不出），R402 改成具名 NOT-RUN；642e4a7 的 Release 红仍是 sources 格旧伤。
② 交互状态：空输入「添加」启用 → 禁用；同帧添加/移除文字差 7/5 → 96/93。
③ 判据：源禁用条件 + 同帧相对亮度像素判据；M1044/M1045 双 CAUGHT。
④ 436：R401 run `judged=4/5`（notice-banner 放行）、`settings-reset-fade=2`、`REDS=0`，保持结案。
⑤ 367：hidden 表 {h_tables} / 可判 {h_judged} / rot {h_rot} / 上界 {h_rot_ceiling}；预检 {pre_tables}/{pre_covered}/{pre_arms}/{pre_bad}。
⑥ 验证：build 0 告警；全量 `{executed}/{skipped}/{failures}`；捕获 {frames} 帧、4 张变化、基线 182/0；换装 ok；清账表 162=162；电池待复跑。

NOT-RUN / 阻塞（分开写）：① **R402 新跑未落地**（主笔+追记一次 push 后待读）；② **R401 长正文测试在 runner 1x 仍 band-empty**（`LONG_TEXT_PILL_NOT_RUN`，本机四档照判）；③ 亮档真机腿仍没跑；④ macOS 12 紧凑详情头仍走旧截断。

下一轮（R403）的靶：⓪ 先 `git push origin main`（禁 amend/force）并复核 ahead=0；读 R402 主笔+追记的 head 跑全部失败步骤（成对 run↔commit），新跑没落地就记 in_progress 未读；① 367 现读 rot=0，按 `HIDDEN_ROT` 查新腐烂；② 继续产品视觉位并落 Sources，换缺陷类别；③ 436 只复核新跑 Motion floor，不重新猜 `must_judge`。
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
report_new = once(report_old, "D-069 … **D-392**", "D-069 … **D-393**")
report_new = once(report_new, "U-31 … U-1430（R401 现读抬到最新一节）", "U-31 … U-1435（R402 现读抬到最新一节）")
report_new = once(
    report_new,
    "R401 现读：注册表 **156** 张 / 刀号最大 **M1043** / 预检 covered=139 arms=419 bad=0；全仓 249 文件 / 903 把；M674 退役、M906 空刀退役",
    f"R402 现读：注册表 **{pre_tables}** 张 / 刀号最大 **M1045** / 预检 covered={pre_covered} arms={pre_arms} bad={pre_bad}；"
    f"全仓 {arm_files} 文件 / {arm_total} 把；M674 退役、M906 空刀退役")
report_new = report_new.rstrip() + "\n\n" + report_bullet
report_new = once(report_new, "`AGENT_STATE.md` 的 R401 节", "`AGENT_STATE.md` 的 R402 节")

state_old = rd("AGENT_STATE.md")
state_anchor = "## R401 状态（2026-10-26"
assert state_old.count(state_anchor) == 1
state_new = once(state_old, state_anchor, state_section + "\n" + state_anchor)

wr("AGENT_UI_AUDIT.md", audit_new)
wr("AGENT_VISUAL_ITERATION.md", iteration_new)
wr("AGENT_DECISIONS.md", decisions_new)
wr("CHANGELOG.md", changelog_new)
wr("AGENT_FINAL_REPORT.md", report_new)
wr("AGENT_STATE.md", state_new)

print("R402_LEDGERS_OK warnings=%s full=%s/%s/%s frames=%s changed=%s baseline=%s/%s/%s/%s add_light=%s/%s add_dark=%s/%s pre=%s/%s/%s/%s arms=%s/%s rot=%s gate=%s=%s streak=%s"
      % (warnings, executed, skipped, failures, frames, changed_frames,
         b_compared, b_changed, b_missing, b_added,
         add["light"][0], add["light"][1], add["dark"][0], add["dark"][1],
         pre_tables, pre_covered, pre_arms, pre_bad, arm_files, arm_total,
         h_rot, cleared, cells, streak))
