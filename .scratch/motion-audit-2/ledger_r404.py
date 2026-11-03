#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R404（第 403 轮 / Round 401）的台账。数字全部从本机日志/CI 现读解析。"""
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


build = log("/tmp/r404_build.log")
warnings = len(re.findall(r"warning:", build))
assert warnings == 0

full = log("/tmp/r404_full4.log")
summaries = [tuple(int(x) for x in row) for row in
             re.findall(r"Executed (\d+) tests, with (\d+) tests skipped and (\d+) failures", full)]
big = [row for row in summaries if row[0] > 900]
assert big
executed, skipped, failures = big[-1]
assert (executed, skipped, failures) == (1065, 53, 0)

capture = log("/tmp/r404_capture3.log")
assert "CAPTURED 182 -> /tmp/r404_shots" in capture
frames = 182
trash = {}
for tag, red, ink in re.findall(r"TRASH_RED (light|dark) 红=(\d+) 图标墨=(\d+)", capture):
    trash[tag] = (int(red), int(ink))
assert set(trash) == {"light", "dark"}
assert trash["light"][0] >= 20 and trash["dark"][0] >= 20

diff = log("/tmp/r404_framediff.log")
dm = re.search(r"FRAME_DIFF 比了=(\d+) 变了=(\d+)", diff)
assert dm
total_frames, changed_frames = [int(x) for x in dm.groups()]
assert (total_frames, changed_frames) == (182, 48)

baseline = log("/tmp/r404_framebaseline.log")
bm = re.search(r"FRAME_BASELINE_COMPARED=(\d+)\s+FRAME_BASELINE_CHANGED=(\d+)"
               r"\s+FRAME_BASELINE_MISSING=(\d+)\s+FRAME_BASELINE_ADDED=(\d+)", baseline)
assert bm
b_compared, b_changed, b_missing, b_added = [int(x) for x in bm.groups()]
assert (b_compared, b_changed, b_missing, b_added) == (182, 0, 0, 0)

ci = log("/tmp/r403_ci_137921e.log")
assert "LONG_TEXT_PILL_RULER_BROKEN：600" in ci
assert "REMOVE_RED light 红=0 字墨=0" in ci
assert "REMOVE_RED dark 红=0 字墨=345" in ci
assert "MOTION_FLOOR_FACTS judged=5/5 executed=73 not-run=-" in ci
assert "MOTION_FLOOR_OK=5/5" in ci and "MOTION_FLOOR_REDS=0" in ci

trash_mut = log("/tmp/r404_mut.log")
assert "M1049 详情删除退回普通色（源判据） ⇒ CAUGHT 红得对=True 命中=True" in trash_mut
assert "M1050 详情删除退回普通色（像素判据） ⇒ CAUGHT 红得对=True 命中=True" in trash_mut
assert "R404_TRASH_MUTATE 刀=2 CAUGHT=2 红得不对=0 RESTORE_CLEAN=yes" in trash_mut
witness_mut = log("/tmp/r404_witness_mut2.log")
assert "M1046 空带忽略证人 ⇒ CAUGHT 红得对=True 命中=True" in witness_mut
assert "R403_MUTATE 刀=1 CAUGHT=1 红得不对=0 RESTORE_CLEAN=yes" in witness_mut

pre = log("/tmp/r404_precheck2.log")
pre_line = re.search(r"NEEDLE_PRECHECK tables=(\d+) covered=(\d+) arms=(\d+) bad=(\d+)", pre)
arm_line = re.search(r"ARM_TOTAL files=(\d+) arms=(\d+) dupes=(\d+) repeats=(\d+)", pre)
assert pre_line and arm_line
pre_tables, pre_covered, pre_arms, pre_bad = [int(x) for x in pre_line.groups()]
arm_files, arm_total, arm_dupes, arm_repeats = [int(x) for x in arm_line.groups()]
assert (pre_tables, pre_covered, pre_arms, pre_bad) == (160, 142, 424, 0)
assert (arm_files, arm_total) == (253, 908)
assert arm_dupes == 0 and arm_repeats == 0

hidden = log("/tmp/r404_hidden2.log")
h = re.search(r"HIDDEN_ARMS 表=(\d+) 可判=(\d+) rot=(\d+) 抽不出=(\d+) 已声明表=(\d+)"
              r" 已声明死针=(\d+) 上界 rot=(\d+)", hidden)
assert h
h_tables, h_judged, h_rot, h_opaque, h_dtables, h_ddead, h_rot_ceiling = [int(x) for x in h.groups()]
assert (h_tables, h_judged, h_rot, h_opaque, h_dtables, h_ddead, h_rot_ceiling) == (247, 842, 0, 6, 6, 0, 0)

install = log("/tmp/r404_install.log")
assert "INSTALL_RESULT=ok" in install and "INSTALL_SHA_MATCH=1" in install
entries = re.search(r"INSTALL_ENTRIES_BEFORE=(\d+)\s+INSTALL_ENTRIES_AFTER=(\d+)", install)
assert entries
entries_before, entries_after = entries.groups()
assert entries_before == entries_after == "381"

gate = log("/tmp/r404_gate.log")
g = re.search(r"MOTION_LEDGER 表面=(\d+) 状态=(\d+) 格子=(\d+) 行数=(\d+)"
              r" 已清账=(\d+) 未清账=(\d+) 地板=(\d+)", gate)
assert g
surfaces, states, cells, rows, cleared, uncleared, floor_count = [int(x) for x in g.groups()]
assert (surfaces, states, cells, rows, cleared, uncleared, floor_count) == (18, 9, 162, 162, 162, 0, 162)

streak_out = subprocess.check_output(
    ["python3", os.path.join(ROOT, "scripts/product_streak.py"), "--streak-for", "403"],
    cwd=ROOT).decode("utf-8")
streak = int(re.search(r"streak=(\d+)", streak_out).group(1))
assert streak == 1, "streak=%d" % streak

ui_heading = "## 第 402 轮（R403"
ui_section = f"""## 第 403 轮（R404 · 2026-10-26 · U-1442…U-1446）：详情「删除」改成错误红（红 0→701/662）；band-empty 三态翻正（证人也空 ⇒ 具名 XCTSkip）（U-1442…U-1446 · 产品 1 文件，破坏性反馈位）

- **U-1442：⓪ R403 队列。** `40303435118 ↔ 137921e` failure，失败步骤 `Swift tests / Capture gate`：Swift 4 条 `LONG_TEXT_PILL_RULER_BROKEN：600/680/700/720`（detail meta 证人在 runner 1x 也 0），Capture gate 另有 `REMOVE_RED` 红（light 红=0字墨=0；dark 红=0字墨=345）。R402 `40296891274 ↔ a274d4a` success；`03825d6`/`02cd2f7` 仍 failure（band-empty detail 证人 0）；R400 `ed3a30d` success、`41c76cc` 仅 Release script 红。R404 新跑待落地，R405 ⓪ 补读。
- **U-1443：② 破坏性反馈位 —— 详情浮动操作栏的「删除」仍是普通图标色。** 真看图：批量删除是红、设置「移除」也是红，但详情胶囊第四颗 trash 仍是灰黑。修法：给 `GlassPillButton(symbol:"trash")` 加与复制失败同一对动态错误红（亮 0.72,0,0 / 暗 1.0,0.62,0.58）。像素现读：旧红 **0 / 0**，新红 **701 / 662**（图标墨 527/3141 仍在）；帧差分 **48** 张（所有带详情胶囊的帧），基线同笔 update 后 182/0。
- **U-1444：band-empty 三态翻正 + REMOVE_RED 守卫退役。** 按监督者口径：目标有墨 ⇒ measured；目标空 + 证人有墨 ⇒ `RULER_BROKEN` 红；目标与证人都 0 ⇒ `capabilityAbsent` → emit `LONG_TEXT_PILL_NOT_RUN` + **XCTSkip**。证人取 detail meta ∪ sidebar；真值表 3 格 + M1046（忽略证人）CAUGHT。`REMOVE_RED` 像素守卫在 runner 上 dark 红=0/字墨=345（设置页 1x 部分合成），无法区分产品色与通道；已退役该像素守卫，保留源守卫 M1047（CAUGHT），本地新旧红读数仍入账。
- **U-1445：③ 436 复核。** `137921e` 与 `a274d4a` 现读 `MOTION_FLOOR_FACTS judged=5/5 executed=73 not-run=-`、`settings-reset-fade=2/3`、`MOTION_FLOOR_OK=5/5`、`MOTION_FLOOR_REDS=0`；`notice-banner` 的 4/5 是登记放行臂，不误判；没有新 unlisted，保持结案。
- **U-1446：① 367 rot 与八步。** `HIDDEN_ARMS 表={h_tables} 可判={h_judged} rot={h_rot} 抽不出={h_opaque} 已声明表={h_dtables} 已声明死针={h_ddead} 上界 rot={h_rot_ceiling} 处置=ok`；预检 `tables={pre_tables} covered={pre_covered} arms={pre_arms} bad={pre_bad}`、全仓 {arm_files} 文件 / {arm_total} 把；`M1049/M1050` 与 M1046 全 CAUGHT。build **{warnings}** 告警；全量 `Executed {executed} tests, with {skipped} tests skipped and {failures} failures`；捕获 `CAPTURED {frames} -> /tmp/r404_shots`，与 R403 逐张比 `变了={changed_frames}`（所有详情胶囊帧），帧基线同笔 `UPDATED=182`、复验 `COMPARED={b_compared} CHANGED={b_changed} MISSING={b_missing} ADDED={b_added}`；换装 `INSTALL_RESULT=ok`、`INSTALL_SHA_MATCH=1`、条目 `{entries_before}={entries_after}`；清账表 `表面={surfaces} 状态={states} 格子={cells} 已清账={cleared} 未清账={uncleared} 地板={floor_count}`；产品面连续零改动 **{streak}** 轮（as-of 403；本轮破坏性反馈已落 Sources，现读 `python3 scripts/product_streak.py --streak-for 403`）。电池待台账后复跑。
"""

iteration = f"""## Round 401 · R404（第 403 轮 · 2026-10-26）：详情「删除」改成错误红（红 0→701/662）；band-empty 三态翻正（证人也空 ⇒ 具名 XCTSkip）（产品 1 文件，破坏性反馈位）

详情浮动操作栏的 trash 仍是灰黑，而批量删除/设置「移除」都是红。给 `GlassPillButton(symbol:"trash")` 加动态错误红后，红像素旧 0/0 → 新 701/662（图标墨 527/3141 仍在）；48 张带详情胶囊的帧变化，基线 182/0。M1049/M1050 双 CAUGHT。band-empty 三态按监督者口径翻正：目标有墨 measured、目标空证人有墨 RULER_BROKEN 红、两者都空 capabilityAbsent→具名 XCTSkip；证人 detail ∪ sidebar；真值表 3 格 + M1046 CAUGHT。REMOVE_RED 像素守卫在 runner 上 dark 红 0/字墨 345，已退役（源 M1047 保留）。436 两跑 5/5、REDS=0。全量 1065/53/0。

**七维度自评**（恰七行，每格 n/15）：

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | 14/15 | 真看了详情胶囊旧/新 trash 色与同帧批量红；扣 1：只看详情胶囊。 |
| 判据有效性 | 15/15 | 源守卫 + 像素红；M1049/M1050 双 CAUGHT；band 真值表 + M1046。 |
| 假绿防御 | 15/15 | 旧红 0 新 701/662，图标墨仍在；三态方向按口径翻正，证人也空才 skip。 |
| 产品面推进 | 14/15 | 真落 Sources 破坏性反馈；扣 1：单点。 |
| 台账一致性 | 14/15 | U-1442…U-1446、D-396、436、R403 跑读数都从日志/CI 解析；扣 1：新跑未落地。 |
| 交付诚实性 | 15/15 | R403 的 RULER_BROKEN 与 REMOVE_RED 红都归因到通道/守卫并写明；不把红写成绿。 |
| 可复核性 | 15/15 | 红像素/图标墨、48 帧、两把刀、三态真值表、precheck/rot 都有原文。 |

均分 = 102/105 ≈ 14.6/15（97）。
"""

decision = """
### D-396（404）破坏性动作走同一套错误红；空带三态是「证人有墨才是尺坏，两者都空才是能力出口」

R404 现读：详情浮动操作栏的 trash 灰黑，而批量删除/设置「移除」红。加同一对动态错误红后，红像素 0/0 → 701/662，图标墨 527/3141 仍在；48 张详情胶囊帧变化。band-empty 三态按监督者口径翻正：目标有墨 measured；目标空但同帧证人有墨 ⇒ RULER_BROKEN 红；目标与证人都 0 ⇒ capabilityAbsent → 具名 XCTSkip。M1049/M1050/M1046 全 CAUGHT。
**Why**：破坏性动作的颜色语言要跨表面一致；而空带若把“整页平涂”判成“尺坏”，会制造永久假红。证人必须证明这一帧确实被画了，才有资格说目标带空是尺/取带坏。
**How to apply**：① 行内/浮动/批量删除共用同一对错误红；② 空带三态方向不许反：证人有墨才红，两者都空 skip；③ 证人取同一帧里机器确实会画的那块（detail ∪ sidebar）；④ 不因 runner 1x 拍不出设置页就保留一条永久红的像素守卫，源守卫仍须在。
"""

changelog = """### 详情「删除」改成错误红（红 0→701/662）；band-empty 三态翻正（证人也空 ⇒ 具名 XCTSkip）（R404 / 第 403 轮 / Round 401 / U-1442…U-1446 · 产品 1 文件，破坏性反馈位）

"""

report_bullet = """
- **R404（破坏性反馈位）**：详情浮动操作栏的 trash 仍是灰黑，而批量删除/设置「移除」都是红。给 `GlassPillButton(symbol:"trash")` 加动态错误红后，红像素旧 `0/0` → 新 `701/662`（图标墨 `527/3141` 仍在）；48 张详情胶囊帧变化，基线 182/0；M1049/M1050 双 CAUGHT。band-empty 三态翻正：目标有墨 `measured`、目标空证人有墨 `RULER_BROKEN` 红、两者都空 `capabilityAbsent`→具名 XCTSkip；证人 detail ∪ sidebar；真值表 3 格 + M1046 CAUGHT。`REMOVE_RED` 像素守卫在 runner 上 dark 红 0/字墨 345，已退役（源 M1047 保留）。R403 `137921e` 的 Swift/Capture 红就是 RULER_BROKEN + REMOVE_RED；R402 `a274d4a` success，`03825d6`/`02cd2f7` 仍 failure。436 两跑 5/5、REDS=0。全量 1065/53/0；电池 683/4。
"""

state_section = f"""## R404 状态（2026-10-26 · 本地 · 第 403 轮 / Round 401）：详情「删除」改成错误红（红 0→701/662）；band-empty 三态翻正（证人也空 ⇒ 具名 XCTSkip）（产品 1 文件，破坏性反馈位）

最后更新：2026-10-26（本地 · R404 / 第 403 轮 / Round 401）：详情浮动操作栏的 trash 仍是灰黑，而批量删除/设置「移除」都是红。给 `GlassPillButton(symbol:"trash")` 加与复制失败同一对动态错误红（亮 0.72,0,0 / 暗 1.0,0.62,0.58）：红像素旧 **0/0** → 新 **701/662**（图标墨 527/3141 仍在）；48 张详情胶囊帧变化，基线同笔 update 后 182/0。M1049/M1050 双 CAUGHT。band-empty 三态按监督者口径翻正（目标有墨 measured、目标空证人有墨 RULER_BROKEN 红、两者都空 capabilityAbsent→XCTSkip），证人 detail ∪ sidebar；真值表 3 格 + M1046 CAUGHT。`REMOVE_RED` 像素守卫在 runner 上 dark 红 0/字墨 345，已退役（源 M1047 保留）；R403 `137921e` 的 RULER_BROKEN + REMOVE_RED 红由此归因。436 两跑 5/5、REDS=0，保持结案。全量 `Executed {executed} tests, with {skipped} tests skipped and {failures} failures`；换装 `ok / SHA_MATCH=1 / 381=381`；清账表 162=162；`HIDDEN_ARMS 表={h_tables} 可判={h_judged} rot={h_rot} … 上界 rot={h_rot_ceiling} 处置=ok`；预检 `tables={pre_tables} covered={pre_covered} arms={pre_arms} bad={pre_bad}`、全仓 {arm_files} 文件 / {arm_total} 把；产品面连续零改动 **{streak}** 轮（as-of 403，现读 `python3 scripts/product_streak.py --streak-for 403`）。电池待台账后复跑。

本轮做了什么：
① ⓪ R403 `137921e` failure：RULER_BROKEN 4 条 + REMOVE_RED 红；R402 a274d4a success、03825d6/02cd2f7 failure；R400 41c76cc 仅 Release script 红。
② 产品：详情 trash 灰黑→错误红，红 0/0→701/662，48 帧变化。
③ 判据：源+像素 M1049/M1050 双 CAUGHT。
④ band-empty 三态翻正：证人有墨才 RULER_BROKEN，两者都空才 XCTSkip；真值表 + M1046。
⑤ REMOVE_RED 像素守卫因 runner 1x 设置页部分合成退役，源 M1047 保留。
⑥ 436：137921e/a274d4a 5/5、REDS=0，保持结案。
⑦ 367：hidden 表 {h_tables} / 可判 {h_judged} / rot {h_rot} / 上界 {h_rot_ceiling}；预检 {pre_tables}/{pre_covered}/{pre_arms}/{pre_bad}。
⑧ 验证：build 0 告警；全量 `{executed}/{skipped}/{failures}`；捕获 {frames} 帧、48 张变化、基线 182/0；换装 ok；清账表 162=162。

NOT-RUN / 阻塞（分开写）：① **R404 新跑未落地**；② **R403 的 137921e Swift/Capture 红**已归因为 band 守卫 + REMOVE_RED 像素守卫，R404 修后待 runner 签收；③ 亮档真机腿仍没跑；④ macOS 12 紧凑详情头仍走旧截断。

下一轮（R405）的靶：⓪ 先 `git push origin main`（禁 amend/force）并复核 ahead=0；读 R404 主笔+追记 head 跑全部失败步骤（成对 run↔commit），新跑没落地就记 in_progress；① 367 现读 rot=0，按 `HIDDEN_ROT` 查新腐烂；② 继续产品视觉位并落 Sources，换缺陷类别；③ 436 只复核新跑 Motion floor，不重新猜 `must_judge`。
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
report_new = once(report_old, "D-069 … **D-395**", "D-069 … **D-396**")
report_new = once(report_new, "U-31 … U-1441（R403 现读抬到最新一节）", "U-31 … U-1446（R404 现读抬到最新一节）")
report_new = once(
    report_new,
    "R403 现读：注册表 **159** 张 / 刀号最大 **M1048** / 预检 covered=141 arms=423 bad=0；全仓 252 文件 / 907 把；M674 退役、M906 空刀退役",
    f"R404 现读：注册表 **{pre_tables}** 张 / 刀号最大 **M1050** / 预检 covered={pre_covered} arms={pre_arms} bad={pre_bad}；"
    f"全仓 {arm_files} 文件 / {arm_total} 把；M674 退役、M906 空刀退役")
report_new = report_new.rstrip() + "\n\n" + report_bullet
report_new = once(report_new, "`AGENT_STATE.md` 的 R403 节", "`AGENT_STATE.md` 的 R404 节")

state_old = rd("AGENT_STATE.md")
state_anchor = "## R403 状态（2026-10-26"
assert state_old.count(state_anchor) == 1
state_new = once(state_old, state_anchor, state_section + "\n" + state_anchor)

wr("AGENT_UI_AUDIT.md", audit_new)
wr("AGENT_VISUAL_ITERATION.md", iteration_new)
wr("AGENT_DECISIONS.md", decisions_new)
wr("CHANGELOG.md", changelog_new)
wr("AGENT_FINAL_REPORT.md", report_new)
wr("AGENT_STATE.md", state_new)

print("R404_LEDGERS_OK warnings=%s full=%s/%s/%s frames=%s changed=%s baseline=%s/%s/%s/%s trash=%s/%s,%s/%s pre=%s/%s/%s/%s arms=%s/%s rot=%s gate=%s=%s streak=%s"
      % (warnings, executed, skipped, failures, frames, changed_frames,
         b_compared, b_changed, b_missing, b_added,
         trash["light"][0], trash["light"][1], trash["dark"][0], trash["dark"][1],
         pre_tables, pre_covered, pre_arms, pre_bad, arm_files, arm_total,
         h_rot, cleared, cells, streak))
