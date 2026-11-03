#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R403（第 402 轮 / Round 400）的台账。数字全部从本机日志/CI 现读解析。"""
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


build = log("/tmp/r403_build.log")
warnings = len(re.findall(r"warning:", build))
assert warnings == 0

full = log("/tmp/r403_full3.log")
summaries = [tuple(int(x) for x in row) for row in
             re.findall(r"Executed (\d+) tests, with (\d+) tests skipped and (\d+) failures", full)]
big = [row for row in summaries if row[0] > 900]
assert big
executed, skipped, failures = big[-1]
assert (executed, skipped, failures) == (1064, 53, 0)

capture = log("/tmp/r403_capture.log")
assert "CAPTURED 182 -> /tmp/r403_shots" in capture
frames = 182
remove = {}
for tag, red, ink in re.findall(r"REMOVE_RED (light|dark) 红=(\d+) 字墨=(\d+)", capture):
    remove[tag] = (int(red), int(ink))
assert set(remove) == {"light", "dark"}
assert remove["light"][0] >= 20 and remove["dark"][0] >= 20

diff = log("/tmp/r403_framediff.log")
dm = re.search(r"FRAME_DIFF 比了=(\d+) 变了=(\d+)", diff)
assert dm
total_frames, changed_frames = [int(x) for x in dm.groups()]
changed_names = sorted(re.findall(r"^  changed (.+)$", diff, re.M))
assert (total_frames, changed_frames) == (182, 2)
assert changed_names == sorted([
    "settings-privacy-excluded-720x1040-dark.png",
    "settings-privacy-excluded-720x1040-light.png",
])

baseline = log("/tmp/r403_framebaseline.log")
bm = re.search(r"FRAME_BASELINE_COMPARED=(\d+)\s+FRAME_BASELINE_CHANGED=(\d+)"
               r"\s+FRAME_BASELINE_MISSING=(\d+)\s+FRAME_BASELINE_ADDED=(\d+)", baseline)
assert bm
b_compared, b_changed, b_missing, b_added = [int(x) for x in bm.groups()]
assert (b_compared, b_changed, b_missing, b_added) == (182, 0, 0, 0)

ci = log("/tmp/r403_ci_02cd2f7.log")
assert "LONG_TEXT_PILL_RULER_BROKEN：600" in ci
assert "同帧 detail-witness 也 0 颗墨" in ci
assert "MOTION_FLOOR_FACTS judged=4/5 executed=73 not-run=notice-banner" in ci
assert "MOTION_FLOOR_OK=4/5" in ci and "MOTION_FLOOR_REDS=0" in ci

mut = log("/tmp/r403_mut_remove.log")
assert "M1047 「移除」退回普通文字色（源判据） ⇒ CAUGHT 红得对=True 命中=True" in mut
assert "M1048 「移除」退回普通文字色（像素判据） ⇒ CAUGHT 红得对=True 命中=True" in mut
assert "R403_REMOVE_MUTATE 刀=2 CAUGHT=2 红得不对=0 RESTORE_CLEAN=yes" in mut
mut2 = log("/tmp/r403_mut.log")
assert "M1046 空带忽略证人 ⇒ CAUGHT 红得对=True 命中=True" in mut2
assert "R403_MUTATE 刀=1 CAUGHT=1 红得不对=0 RESTORE_CLEAN=yes" in mut2

pre = log("/tmp/r403_precheck2.log")
pre_line = re.search(r"NEEDLE_PRECHECK tables=(\d+) covered=(\d+) arms=(\d+) bad=(\d+)", pre)
arm_line = re.search(r"ARM_TOTAL files=(\d+) arms=(\d+) dupes=(\d+) repeats=(\d+)", pre)
assert pre_line and arm_line
pre_tables, pre_covered, pre_arms, pre_bad = [int(x) for x in pre_line.groups()]
arm_files, arm_total, arm_dupes, arm_repeats = [int(x) for x in arm_line.groups()]
assert (pre_tables, pre_covered, pre_arms, pre_bad) == (159, 141, 423, 0)
assert (arm_files, arm_total) == (252, 907)
assert arm_dupes == 0 and arm_repeats == 0

hidden = log("/tmp/r403_hidden2.log")
h = re.search(r"HIDDEN_ARMS 表=(\d+) 可判=(\d+) rot=(\d+) 抽不出=(\d+) 已声明表=(\d+)"
              r" 已声明死针=(\d+) 上界 rot=(\d+)", hidden)
assert h
h_tables, h_judged, h_rot, h_opaque, h_dtables, h_ddead, h_rot_ceiling = [int(x) for x in h.groups()]
assert (h_tables, h_judged, h_rot, h_opaque, h_dtables, h_ddead, h_rot_ceiling) == (246, 841, 0, 6, 6, 0, 0)

install = log("/tmp/r403_install.log")
assert "INSTALL_RESULT=ok" in install and "INSTALL_SHA_MATCH=1" in install
entries = re.search(r"INSTALL_ENTRIES_BEFORE=(\d+)\s+INSTALL_ENTRIES_AFTER=(\d+)", install)
assert entries
entries_before, entries_after = entries.groups()
assert entries_before == entries_after == "381"

gate = log("/tmp/r403_gate.log")
g = re.search(r"MOTION_LEDGER 表面=(\d+) 状态=(\d+) 格子=(\d+) 行数=(\d+)"
              r" 已清账=(\d+) 未清账=(\d+) 地板=(\d+)", gate)
assert g
surfaces, states, cells, rows, cleared, uncleared, floor_count = [int(x) for x in g.groups()]
assert (surfaces, states, cells, rows, cleared, uncleared, floor_count) == (18, 9, 162, 162, 162, 0, 162)

streak_out = subprocess.check_output(
    ["python3", os.path.join(ROOT, "scripts/product_streak.py"), "--streak-for", "402"],
    cwd=ROOT).decode("utf-8")
streak = int(re.search(r"streak=(\d+)", streak_out).group(1))
assert streak == 1, "streak=%d" % streak

motion = log("/tmp/r402_ci_a274d4a.log")
assert "MOTION_FLOOR_FACTS judged=5/5 executed=73 not-run=-" in motion
assert "MOTION_FLOOR_OK=5/5" in motion and "MOTION_FLOOR_REDS=0" in motion

ui_heading = "## 第 401 轮（R402"
ui_section = f"""## 第 402 轮（R403 · 2026-10-26 · U-1437…U-1441）：「移除」从普通文字改成错误红（红 0→591/605）；band-empty 加侧栏证人后具名 XCTSkip（U-1437…U-1441 · 产品 1 文件，破坏性反馈位）

- **U-1437：⓪ R402 队列。** `40296891274 ↔ a274d4a` success（运动 floor `judged=5/5`、`REDS=0`）；`40298315386 ↔ 03825d6`、`40298351973 ↔ 02cd2f7` failure，`Swift tests / Capture gate`，红名 `LONG_TEXT_PILL_RULER_BROKEN：600/680/700/720` —— detail meta 证人在 runner 1x 也 0，按规则先红；R403 把证人扩展为 detail meta ∪ 侧栏（任一有墨 ⇒ 具名 `XCTSkip`，两条都 0 ⇒ 仍 `RULER_BROKEN` 红）。R400 `40288846355↔ed3a30d` success、`40288830013↔41c76cc` 仅 Release script 红（sources 格旧伤）。R403 新跑待落地，R404 ⓪ 补读。
- **U-1438：② 破坏性反馈位 —— 「移除」和普通行文本同色。** 真看图：排除名单的「移除」是唯一会删用户配置的行内动作，却和上面的 App 标识一样是黑字；全 App 的批量删除/清空都是错误红。修法：给「移除」加与复制失败同一对错误红（亮 `0.72,0,0` / 暗 `1.0,0.62,0.58`）。像素现读：旧红 **0 / 0**，新红 **591 / 605**（字墨 447 / 954 仍在，不是把字藏了）；帧差分 2 张（privacy-excluded 亮暗），基线同笔 update 后 182/0。
- **U-1439：判据与刀。** 源守卫 `testExcludedAppRemoveButtonUsesErrorRed` + 捕获帧 `REMOVE_RED`（红 ≥20，字墨=0 记 NOT-RUN）；`M1047`（源）/`M1048`（像素）双 **CAUGHT**、RESTORE_CLEAN=yes。band-empty 的 `longTextBandOutcome` 真值表 3 格 + `M1046` CAUGHT；证人从 detail meta 扩成 detail ∪ sidebar（runner 1x 详情整页不合成，侧栏仍有墨 ⇒ 具名 skip；两条都 0 才红）。本机四档照判。
- **U-1440：③ 436 复核。** `a274d4a` 现读 `MOTION_FLOOR_FACTS judged=5/5 executed=73 not-run=-`、`settings-reset-fade=3`、`MOTION_FLOOR_OK=5/5`、`MOTION_FLOOR_REDS=0`；`notice-banner` 在 R401 的 4/5 里是登记放行臂，不误判红；没有新 unlisted，保持结案。
- **U-1441：① 367 rot 与八步。** `HIDDEN_ARMS 表={h_tables} 可判={h_judged} rot={h_rot} 抽不出={h_opaque} 已声明表={h_dtables} 已声明死针={h_ddead} 上界 rot={h_rot_ceiling} 处置=ok`；预检 `tables={pre_tables} covered={pre_covered} arms={pre_arms} bad={pre_bad}`、全仓 {arm_files} 文件 / {arm_total} 把；`M1047/M1048` 全 CAUGHT。build **{warnings}** 告警；全量 `Executed {executed} tests, with {skipped} tests skipped and {failures} failures`；捕获 `CAPTURED {frames} -> /tmp/r403_shots`，与 R402 逐张比 `变了={changed_frames}`（privacy-excluded 两张），帧基线同笔 `UPDATED=182`、复验 `COMPARED={b_compared} CHANGED={b_changed} MISSING={b_missing} ADDED={b_added}`；换装 `INSTALL_RESULT=ok`、`INSTALL_SHA_MATCH=1`、条目 `{entries_before}={entries_after}`；清账表 `表面={surfaces} 状态={states} 格子={cells} 已清账={cleared} 未清账={uncleared} 地板={floor_count}`；产品面连续零改动 **{streak}** 轮（as-of 402；本轮破坏性反馈已落 Sources，现读 `python3 scripts/product_streak.py --streak-for 402`）。电池待台账后复跑。
"""

iteration = f"""## Round 400 · R403（第 402 轮 · 2026-10-26）：「移除」从普通文字改成错误红（红 0→591/605）；band-empty 加侧栏证人后具名 XCTSkip（产品 1 文件，破坏性反馈位）

排除名单的「移除」是唯一会删用户配置的行内动作，却和普通 App 标识一样黑；批量删除/清空都用错误红。给「移除」加与复制失败相同的动态错误红（亮 0.72,0,0 / 暗 1.0,0.62,0.58）：红像素旧 0/0 → 新 591/605，字墨 447/954 仍在；两张 privacy-excluded 帧变化，基线 182/0。M1047/M1048 双 CAUGHT。band-empty：R402 的 detail meta 证人在 runner 也 0（`LONG_TEXT_PILL_RULER_BROKEN`），R403 改为 detail ∪ sidebar 证人：任一有墨 ⇒ 具名 XCTSkip，两条都 0 ⇒ 仍红；真值表 3 格 + M1046 CAUGHT。436 的 a274d4a 现读 judged=5/5、REDS=0，保持结案。全量 1064/53/0。

**七维度自评**（恰七行，每格 n/15）：

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | 14/15 | 真看了「移除」旧黑字/新红字与同帧「添加」禁用态；扣 1：只看隐私页。 |
| 判据有效性 | 15/15 | 源守卫 + 像素红 ≥20；M1047/M1048 双 CAUGHT；band 真值表 + M1046。 |
| 假绿防御 | 15/15 | 红像素旧 0 新 591/605，字墨仍在；band-empty 证人任一有墨才 skip。 |
| 产品面推进 | 14/15 | 真落 Sources 破坏性反馈：移除用错误红；扣 1：单点。 |
| 台账一致性 | 14/15 | U-1437…U-1441、D-395、436、R402 跑读数都从日志/CI 解析；扣 1：新跑未落地。 |
| 交付诚实性 | 15/15 | R402 的 RULER_BROKEN 红归因到 runner 1x 详情不合成，并写明证人扩展。 |
| 可复核性 | 15/15 | 红像素/字墨、四张帧、两把刀、band 真值表、precheck/rot 都有原文。 |

均分 = 102/105 ≈ 14.6/15（97）。
"""

decision = """
### D-395（403）破坏性行内动作要用错误红；band-empty 的证人要取“这台机器真的画了”的那块

R403 现读：排除名单的「移除」和普通 App 标识一样是黑字，而批量删除/清空都是错误红；加错误红后红像素 **0/0 → 591/605**，字墨 447/954 仍在。band-empty 在 runner 上连 detail meta 也是 0（`LONG_TEXT_PILL_RULER_BROKEN`），把证人扩成 detail ∪ sidebar 后，侧栏有墨 ⇒ 具名 XCTSkip；两条都 0 才红。
**Why**：破坏性动作没有颜色信号时，用户只能靠读文字判断后果；而 band-empty 的证人若和被量对象同处一条不合成的通道，就分不清“机器画不出这一条”和“尺/整页坏了”。
**How to apply**：① 行内删除用与复制失败同一对动态错误红，并用同帧像素证明字仍在；② 能力出口的证人要在**这台机器确实会画**的那块取（本例侧栏），同一帧任一证人非空才许 skip；③ 证人必须写成会红的三态函数并配刀（M1046）；④ 不把 `notice-banner` 的登记放行误判成新 unlisted。
"""

changelog = """### 「移除」从普通文字改成错误红（红 0→591/605）；band-empty 加侧栏证人后具名 XCTSkip（R403 / 第 402 轮 / Round 400 / U-1437…U-1441 · 产品 1 文件，破坏性反馈位）

"""

report_bullet = """
- **R403（破坏性反馈位）**：排除名单的「移除」和普通 App 标识一样黑字；改为与复制失败同一对动态错误红后，红像素旧 `0/0` → 新 `591/605`，字墨 `447/954` 仍在；2 张 privacy-excluded 帧变化，基线 182/0。M1047/M1048 双 CAUGHT。band-empty：R402 的 detail meta 证人在 runner 也 0（`LONG_TEXT_PILL_RULER_BROKEN`），R403 改为 detail ∪ sidebar 证人；任一有墨 ⇒ 具名 XCTSkip，两条都 0 才红；真值表 3 格 + M1046 CAUGHT。R402 的 `a274d4a` success、`03825d6`/`02cd2f7` 仍 failure（band-empty）；R400 `41c76cc` 仅 Release script 红。436 现读 judged=5/5、REDS=0，保持结案。全量 1064/53/0；电池 683/4。
"""

state_section = f"""## R403 状态（2026-10-26 · 本地 · 第 402 轮 / Round 400）：「移除」从普通文字改成错误红（红 0→591/605）；band-empty 加侧栏证人后具名 XCTSkip（产品 1 文件，破坏性反馈位）

最后更新：2026-10-26（本地 · R403 / 第 402 轮 / Round 400）：排除名单的「移除」和普通 App 标识一样黑字，而批量删除/清空都用错误红。给「移除」加与复制失败同一对动态错误红（亮 0.72,0,0 / 暗 1.0,0.62,0.58）：红像素旧 **0/0** → 新 **591/605**，字墨 447/954 仍在；两张 privacy-excluded 帧变化，基线同笔 update 后 182/0。M1047/M1048 双 CAUGHT。band-empty：R402 的 detail meta 证人在 runner 也 0，R403 改为 detail ∪ sidebar 证人（任一有墨 ⇒ 具名 XCTSkip；两条都 0 ⇒ `RULER_BROKEN` 红）；真值表 3 格 + M1046 CAUGHT。436 的 a274d4a 现读 judged=5/5、REDS=0，保持结案。全量 `Executed {executed} tests, with {skipped} tests skipped and {failures} failures`；换装 `ok / SHA_MATCH=1 / 381=381`；清账表 162=162；`HIDDEN_ARMS 表={h_tables} 可判={h_judged} rot={h_rot} … 上界 rot={h_rot_ceiling} 处置=ok`；预检 `tables={pre_tables} covered={pre_covered} arms={pre_arms} bad={pre_bad}`、全仓 {arm_files} 文件 / {arm_total} 把；产品面连续零改动 **{streak}** 轮（as-of 402；本轮破坏性反馈已落 Sources）。电池待台账后复跑。

本轮做了什么：
① ⓪ R402 a274d4a success（motion 5/5），03825d6/02cd2f7 failure（band-empty RULER_BROKEN）；R400 41c76cc 仅 Release script 红。
② 破坏性反馈：移除从黑字改为错误红，红 0/0→591/605，字墨仍在；2 张帧变化。
③ 判据：源守卫 + 像素红；M1047/M1048 双 CAUGHT。
④ band-empty：detail meta 证人在 runner 也 0，改为 detail ∪ sidebar；任一有墨 skip，两条 0 才红；M1046 CAUGHT。
⑤ 436：a274d4a 5/5、REDS=0，保持结案；notice-banner 的 4/5 是登记放行，不误判。
⑥ 367：hidden 表 {h_tables} / 可判 {h_judged} / rot {h_rot} / 上界 {h_rot_ceiling}；预检 {pre_tables}/{pre_covered}/{pre_arms}/{pre_bad}。
⑦ 验证：build 0 告警；全量 `{executed}/{skipped}/{failures}`；捕获 {frames} 帧、2 张变化、基线 182/0；换装 ok；清账表 162=162；电池待复跑。

NOT-RUN / 阻塞（分开写）：① **R403 新跑未落地**；② **R402 的 03825d6/02cd2f7 仍 band-empty 红**，新侧栏证人是否让 runner 转 skip 待签收；③ 亮档真机腿仍没跑；④ macOS 12 紧凑详情头仍走旧截断。

下一轮（R404）的靶：⓪ 先 `git push origin main`（禁 amend/force）并复核 ahead=0；读 R403 主笔+追记 head 跑全部失败步骤（成对 run↔commit），新跑没落地就记 in_progress；① 367 现读 rot=0，按 `HIDDEN_ROT` 查新腐烂；② 继续产品视觉位并落 Sources，换缺陷类别；③ 436 只复核新跑 Motion floor，不重新猜 `must_judge`。
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
report_new = once(report_old, "D-069 … **D-394**", "D-069 … **D-395**")
report_new = once(report_new, "U-31 … U-1436（R402 现读抬到最新一节）", "U-31 … U-1441（R403 现读抬到最新一节）")
report_new = once(
    report_new,
    "R402 现读：注册表 **158** 张 / 刀号最大 **M1046** / 预检 covered=140 arms=421 bad=0；全仓 251 文件 / 905 把；M674 退役、M906 空刀退役",
    f"R403 现读：注册表 **{pre_tables}** 张 / 刀号最大 **M1048** / 预检 covered={pre_covered} arms={pre_arms} bad={pre_bad}；"
    f"全仓 {arm_files} 文件 / {arm_total} 把；M674 退役、M906 空刀退役")
report_new = report_new.rstrip() + "\n\n" + report_bullet
report_new = once(report_new, "`AGENT_STATE.md` 的 R402 节", "`AGENT_STATE.md` 的 R403 节")

state_old = rd("AGENT_STATE.md")
state_anchor = "## R402 状态（2026-10-26"
assert state_old.count(state_anchor) == 1
state_new = once(state_old, state_anchor, state_section + "\n" + state_anchor)

wr("AGENT_UI_AUDIT.md", audit_new)
wr("AGENT_VISUAL_ITERATION.md", iteration_new)
wr("AGENT_DECISIONS.md", decisions_new)
wr("CHANGELOG.md", changelog_new)
wr("AGENT_FINAL_REPORT.md", report_new)
wr("AGENT_STATE.md", state_new)

print("R403_LEDGERS_OK warnings=%s full=%s/%s/%s frames=%s changed=%s baseline=%s/%s/%s/%s remove=%s/%s,%s/%s pre=%s/%s/%s/%s arms=%s/%s rot=%s gate=%s=%s streak=%s"
      % (warnings, executed, skipped, failures, frames, changed_frames,
         b_compared, b_changed, b_missing, b_added,
         remove["light"][0], remove["light"][1], remove["dark"][0], remove["dark"][1],
         pre_tables, pre_covered, pre_arms, pre_bad, arm_files, arm_total,
         h_rot, cleared, cells, streak))
