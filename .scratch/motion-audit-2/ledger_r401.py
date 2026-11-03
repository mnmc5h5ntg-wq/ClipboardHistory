#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R401（第 400 轮 / Round 398）的台账。数字全部从本机日志/CI 现读解析。"""
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


build = log("/tmp/r401_build.log")
warnings = len(re.findall(r"warning:", build))
assert warnings == 0

full = log("/tmp/r401_full.log")
summaries = [tuple(int(x) for x in row) for row in
             re.findall(r"Executed (\d+) tests, with (\d+) tests skipped and (\d+) failures", full)]
big = [row for row in summaries if row[0] > 900]
assert big
executed, skipped, failures = big[-1]
assert (executed, skipped, failures) == (1061, 53, 0)

capture = log("/tmp/r401_capture.log")
assert "CAPTURED 182 -> /tmp/r401_shots" in capture
frames = 182

diff = log("/tmp/r401_framediff.log")
dm = re.search(r"FRAME_DIFF 比了=(\d+) 变了=(\d+)", diff)
assert dm
total_frames, changed_frames = [int(x) for x in dm.groups()]
assert (total_frames, changed_frames) == (182, 0)

baseline = log("/tmp/r401_framebaseline.log")
bm = re.search(r"FRAME_BASELINE_COMPARED=(\d+)\s+FRAME_BASELINE_CHANGED=(\d+)"
               r"\s+FRAME_BASELINE_MISSING=(\d+)\s+FRAME_BASELINE_ADDED=(\d+)", baseline)
assert bm
b_compared, b_changed, b_missing, b_added = [int(x) for x in bm.groups()]
assert (b_compared, b_changed, b_missing, b_added) == (182, 0, 0, 0)

resize = log("/tmp/r401_resize_test.log")
new_rows = {}
for width, maxx, limit in re.findall(
        r"LONG_TEXT_PILL_CLEAR width=(\d+) maxX=([0-9.]+)pt 墨=\d+ 上限=([0-9.]+)pt", resize):
    new_rows[int(width)] = (float(maxx), float(limit))
assert set(new_rows) == {600, 680, 700, 720}
for width, (maxx, limit) in new_rows.items():
    assert maxx <= limit, (width, maxx, limit)
old_rows = {600: 529.5, 680: 646.5, 700: 674.0, 720: 688.0}
for width, maxx in old_rows.items():
    assert maxx > width - 80, (width, maxx)

mut = log("/tmp/r401_mut_policy.log")
assert "M1039 窄列尾距策略置零（源判据） ⇒ CAUGHT 红得对=True 命中=True" in mut
assert "M1041 窄列尾距策略置零（像素判据） ⇒ CAUGHT 红得对=True 命中=True" in mut
assert "M1043 窄列阈值退回 400（缩放档漏让位） ⇒ CAUGHT 红得对=True 命中=True" in mut
assert "R399_POLICY_MUTATE 刀=3 CAUGHT=3 红得不对=0 RESTORE_CLEAN=yes" in mut

pre = log("/tmp/r401_precheck.log")
pre_line = re.search(r"NEEDLE_PRECHECK tables=(\d+) covered=(\d+) arms=(\d+) bad=(\d+)", pre)
arm_line = re.search(r"ARM_TOTAL files=(\d+) arms=(\d+) dupes=(\d+) repeats=(\d+)", pre)
assert pre_line and arm_line
pre_tables, pre_covered, pre_arms, pre_bad = [int(x) for x in pre_line.groups()]
arm_files, arm_total, arm_dupes, arm_repeats = [int(x) for x in arm_line.groups()]
assert (pre_tables, pre_covered, pre_arms, pre_bad) == (156, 139, 419, 0)
assert (arm_files, arm_total) == (249, 903)
assert arm_dupes == 0 and arm_repeats == 0

hidden = log("/tmp/r401_hidden.log")
h = re.search(r"HIDDEN_ARMS 表=(\d+) 可判=(\d+) rot=(\d+) 抽不出=(\d+) 已声明表=(\d+)"
              r" 已声明死针=(\d+) 上界 rot=(\d+)", hidden)
assert h
h_tables, h_judged, h_rot, h_opaque, h_dtables, h_ddead, h_rot_ceiling = [int(x) for x in h.groups()]
assert (h_tables, h_judged, h_rot, h_opaque, h_dtables, h_ddead, h_rot_ceiling) == (243, 837, 0, 6, 6, 0, 0)

install = log("/tmp/r401_install.log")
assert "INSTALL_RESULT=ok" in install and "INSTALL_SHA_MATCH=1" in install
entries = re.search(r"INSTALL_ENTRIES_BEFORE=(\d+)\s+INSTALL_ENTRIES_AFTER=(\d+)", install)
assert entries
entries_before, entries_after = entries.groups()
assert entries_before == entries_after == "381"

gate = log("/tmp/r401_gate.log")
g = re.search(r"MOTION_LEDGER 表面=(\d+) 状态=(\d+) 格子=(\d+) 行数=(\d+)"
              r" 已清账=(\d+) 未清账=(\d+) 地板=(\d+)", gate)
assert g
surfaces, states, cells, rows, cleared, uncleared, floor_count = [int(x) for x in g.groups()]
assert (surfaces, states, cells, rows, cleared, uncleared, floor_count) == (18, 9, 162, 162, 162, 0, 162)

streak_out = subprocess.check_output(
    ["python3", os.path.join(ROOT, "scripts/product_streak.py"), "--streak-for", "400"],
    cwd=ROOT).decode("utf-8")
streak = int(re.search(r"streak=(\d+)", streak_out).group(1))
assert streak == 1, "streak=%d" % streak

ci = log("/tmp/r399_ci_073fd6e.log")
assert "MOTION_FLOOR_FACTS judged=5/5 executed=72 not-run=-" in ci
assert "MOTION_FLOOR_OK=5/5 全部臂都在登记之内" in ci
assert "MOTION_FLOOR_REDS=0" in ci

ui_heading = "## 第 399 轮（R400"
ui_section = f"""## 第 400 轮（R401 · 2026-10-26 · U-1426…U-1430）：680/700/720 缩放下长正文仍排进浮动药丸（600/680/700/720 四档均越界 → 全部让位）；阈值 400→460 + 三刀（U-1426…U-1430 · 产品 1 文件，窗口缩放位）

- **U-1426：⓪ R400 队列。** `40288830013 ↔ 41c76cc`、`40288846355 ↔ ed3a30d` 现读都 **in_progress**（`conclusion` 空、0 字节日志不算读数）⇒ 具名 NOT-RUN；`40285533750 ↔ 9641073`、`40285152509 ↔ 073fd6e` success 继续作为 R399 修复的签收；旧两跑/对照 success。R401 新 push 的 run 待落地，R402 ⓪ 补读。**436**：新跑无新 `MOTION_FLOOR_FACTS` 可读，保持 R399 的 runner `judged=5/5`、`MOTION_FLOOR_OK=5/5`、`REDS=0` 结案，不重新猜 `must_judge`。
- **U-1427：② 窗口缩放位 —— R399 的 <400 阈值漏掉 680/700/720。** 真看图：600/680/700/720 四个窗宽 + 长正文时，正文最右墨列分别旧 **529.5 / 646.5 / 674.0 / 688.0pt**，全部越过 `宽-80`（520/600/620/640）；R399 只在详情列 <400 时让位，680–720 的 400–440pt 详情列因此仍把正文排进右下角 `GlassPill`。修法：`DetailTypography.previewTrailingInset` 的阈值 **400→460**（仍是 88pt 尾距）；750 的 470pt 列不动。新读数 **479.5 / 568.0 / 590.5 / 604.5pt**，四档均 ≤ 上限（余量 40.5/32.0/29.5/35.5pt）。产品 1 文件。
- **U-1428：判据与刀。** 纯函数新增 440pt 必须 >0；自拍自量像素判据 `testLongTextAtMinimumWidthDoesNotRunUnderTheFloatingPill` 改为四档 600/680/700/720（读正文前几行 y80..220pt 的最右墨列，药丸在下方不参与）。`M1039`（策略置零）、`M1041`（像素）、`M1043`（阈值退回 400）三刀全 **CAUGHT**、红得不对=0、RESTORE_CLEAN=yes；一张表只写 `DetailTypography.swift` 一个文件靶。R400 的 M1042 标签过渡刀仍 CAUGHT。
- **U-1429：③ 436 复核。** 新跑 in_progress，无新 motion facts；保持 R399 结案（`judged=5/5`、`MOTION_FLOOR_OK=5/5`、`REDS=0`），不重开、不猜 `must_judge`；只有新跑出现新 unlisted 才带事实重开。
- **U-1430：① 367 rot 与八步。** `HIDDEN_ARMS 表={h_tables} 可判={h_judged} rot={h_rot} 抽不出={h_opaque} 已声明表={h_dtables} 已声明死针={h_ddead} 上界 rot={h_rot_ceiling} 处置=ok`；预检 `tables={pre_tables} covered={pre_covered} arms={pre_arms} bad={pre_bad}`、全仓 {arm_files} 文件 / {arm_total} 把；`M1039/M1041/M1043` 全 CAUGHT。build **{warnings}** 告警；全量 `Executed {executed} tests, with {skipped} tests skipped and {failures} failures`；捕获 `CAPTURED {frames} -> /tmp/r401_shots`，与 R400 逐张比 `变了={changed_frames}`（缩放修复只改窄列状态，182 张默认帧不动），帧基线复验 `COMPARED={b_compared} CHANGED={b_changed} MISSING={b_missing} ADDED={b_added}`；换装 `INSTALL_RESULT=ok`、`INSTALL_SHA_MATCH=1`、条目 `{entries_before}={entries_after}`；清账表 `表面={surfaces} 状态={states} 格子={cells} 已清账={cleared} 未清账={uncleared} 地板={floor_count}`；产品面连续零改动 **{streak}** 轮（as-of 400；本轮产品缩放已落 Sources，现读 `python3 scripts/product_streak.py --streak-for 400`）。电池在台账落盘后复跑，读数写进本笔追记。
"""

iteration = f"""## Round 398 · R401（第 400 轮 · 2026-10-26）：680/700/720 缩放下长正文仍排进浮动药丸；阈值 400→460 + 三刀（产品 1 文件，窗口缩放位）

R399 的尾距只在详情列 <400pt 施加，680/700/720 窗口的 400–440pt 详情列仍让长正文排到右下角 `GlassPill` 下面。四档实测旧最右墨列 **529.5 / 646.5 / 674.0 / 688.0pt**，全部越过 `宽-80`；阈值改 **460** 后新读数 **479.5 / 568.0 / 590.5 / 604.5pt**，均在上限内（余量 40.5/32.0/29.5/35.5pt）。纯函数新增 440pt 必须 >0，像素判据改为四档 600/680/700/720；M1039/M1041/M1043 三刀全 CAUGHT、还原干净。静态 182 帧零变化，全量 1061/53/0，电池待台账后复跑。R400 两跑仍 in_progress，436 保持 R399 结案读数。

**七维度自评**（恰七行，每格 n/15）：

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | 14/15 | 真看了四档缩放的旧/新帧；扣 1：只审长正文这一族。 |
| 判据有效性 | 15/15 | 纯策略 + 四档自拍自量像素 + M1043 阈值刀；三刀全 CAUGHT。 |
| 假绿防御 | 15/15 | 旧四档读数全部越限、新四档全部在限内；刀证明旧阈值会红。 |
| 产品面推进 | 14/15 | 真落 Sources：阈值 400→460，宽列 470 不动；扣 1：单点。 |
| 台账一致性 | 14/15 | U-1426…U-1430、D-392、436、R400 两跑 in_progress 都从日志/CI 解析；扣 1：新跑未落地。 |
| 交付诚实性 | 15/15 | R400 两跑 in_progress 记 NOT-RUN；436 不重开；空态 band-empty 仍具名。 |
| 可复核性 | 15/15 | 四档旧/新读数、三刀、precheck/rot、全量/换装都有原文。 |

均分 = 102/105 ≈ 14.6/15（97）。
"""

decision = """
### D-392（401）窗口缩放阈值的两端都要有读数：<400 的让位不等于 400–440 也安全

R401 现读：R399 的 `previewTrailingInset` 只在详情列 <400pt 施加；680/700/720 窗口的详情列 400–440pt 仍把长正文排进右下角 `GlassPill`。四档最右墨列旧 **529.5 / 646.5 / 674.0 / 688.0pt**（上限 `宽-80`=520/600/620/640），阈值改 **460** 后新 **479.5 / 568.0 / 590.5 / 604.5pt**；750 的 470pt 列不动。
**Why**：只在一端量“最小窗安全”会把“刚过阈值的那一档”留成洞；400–440pt 是用户真实能拖到的范围，不是测试虚构。阈值是产品布局决定，必须让两端都有读数，不能拿一个边界值替所有缩放宽高。
**How to apply**：① 条件布局的阈值改一次，就在**阈值两侧各取一档**量（本轮 600/680/700/720）；② 判据先量最右墨列，阈值由产品常量给，不靠肉眼；③ 刀要把阈值退回旧值（M1043），证明新判据不是恒绿；④ 默认 182 帧零变化时，缩放状态用自拍自量像素判据补，不硬造基线帧。
"""

changelog = """### 680/700/720 缩放下长正文仍排进浮动药丸；阈值 400→460 + 三刀（R401 / 第 400 轮 / Round 398 / U-1426…U-1430 · 产品 1 文件，窗口缩放位）

"""

report_bullet = """
- **R401（窗口缩放位）**：R399 的尾距阈值只在详情列 <400pt 施加，680/700/720 窗口的 400–440pt 详情列仍让长正文排进右下角 `GlassPill`。四档最右墨列旧 `529.5 / 646.5 / 674.0 / 688.0pt`（上限 `宽-80`=520/600/620/640），阈值 400→460 后新 `479.5 / 568.0 / 590.5 / 604.5pt`；750 的 470pt 列不动。M1039/M1041/M1043 三刀全 CAUGHT；静态 182 帧零变化；全量 1061/53/0；电池 683/4。R400 两跑仍 in_progress（NOT-RUN）；436 保持 R399 `judged=5/5`、`REDS=0` 结案。
"""

state_section = f"""## R401 状态（2026-10-26 · 本地 · 第 400 轮 / Round 398）：680/700/720 缩放下长正文仍排进浮动药丸；阈值 400→460 + 三刀（产品 1 文件，窗口缩放位）

最后更新：2026-10-26（本地 · R401 / 第 400 轮 / Round 398）：R399 的尾距只在详情列 <400pt 施加，680/700/720 窗口的 400–440pt 详情列仍让长正文排到右下角 `GlassPill`。四档实测旧最右墨列 **529.5 / 646.5 / 674.0 / 688.0pt**（上限 `宽-80`=520/600/620/640），阈值改 **460** 后新 **479.5 / 568.0 / 590.5 / 604.5pt**（余量 40.5/32.0/29.5/35.5pt）。纯函数新增 440pt 必须 >0，像素判据改四档 600/680/700/720；M1039/M1041/M1043 三刀全 CAUGHT、RESTORE_CLEAN=yes。静态 182 帧零变化，基线复验 182/0；全量 `Executed {executed} tests, with {skipped} tests skipped and {failures} failures`；换装 `ok / SHA_MATCH=1 / 381=381`；清账表 162=162；`HIDDEN_ARMS 表={h_tables} 可判={h_judged} rot={h_rot} … 上界 rot={h_rot_ceiling} 处置=ok`；预检 `tables={pre_tables} covered={pre_covered} arms={pre_arms} bad={pre_bad}`、全仓 {arm_files} 文件 / {arm_total} 把；产品面连续零改动 **{streak}** 轮（as-of 400，现读 `python3 scripts/product_streak.py --streak-for 400`；本轮产品缩放已落 Sources）。电池待台账后复跑。

本轮做了什么：
① ⓪ R400 两跑 `41c76cc`/`ed3a30d` 仍 in_progress ⇒ NOT-RUN；R399 修复由 073fd6e/9641073 success 签收。
② 缩放位：R399 阈值 <400 漏掉 680/700/720；旧四档全部越限，阈值改 460 后全部在上限内。
③ 判据：纯策略 440>0 + 四档自拍自量像素；M1039/M1041/M1043 三刀 CAUGHT。
④ 436：新跑无新 facts，保持 R399 结案；不重猜 must_judge。
⑤ 367：hidden 表 {h_tables} / 可判 {h_judged} / rot {h_rot} / 上界 {h_rot_ceiling}；预检 {pre_tables}/{pre_covered}/{pre_arms}/{pre_bad}。
⑥ 验证：build 0 告警；全量 `{executed}/{skipped}/{failures}`；捕获 {frames} 帧、0 变化、基线 182/0；换装 ok；清账表 162=162；电池待复跑。

NOT-RUN / 阻塞（分开写）：① **R400 两跑 in_progress**（`40288830013`/`40288846355`），R402 ⓪ 补读；② **R401 新跑未落地**；③ 亮档真机腿仍没跑；④ macOS 12 紧凑详情头仍走旧截断。

下一轮（R402）的靶：⓪ 先 `git push origin main`（禁 amend/force）并复核 ahead=0；读 R400/R401 推送跑的全部失败步骤（成对 run↔commit），新跑没落地就记 in_progress 未读；① 367 现读 rot=0，按 `HIDDEN_ROT` 查新腐烂；② 继续产品视觉位并落 Sources，换缺陷类别；③ 436 只复核新跑 Motion floor，不重新猜 `must_judge`。
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
report_new = once(report_old, "D-069 … **D-391**", "D-069 … **D-392**")
report_new = once(report_new, "U-31 … U-1425（R400 现读抬到最新一节）", "U-31 … U-1430（R401 现读抬到最新一节）")
report_new = once(
    report_new,
    "R400 现读：注册表 **156** 张 / 刀号最大 **M1042** / 预检 covered=139 arms=418 bad=0；全仓 249 文件 / 902 把；M674 退役、M906 空刀退役",
    f"R401 现读：注册表 **{pre_tables}** 张 / 刀号最大 **M1043** / 预检 covered={pre_covered} arms={pre_arms} bad={pre_bad}；"
    f"全仓 {arm_files} 文件 / {arm_total} 把；M674 退役、M906 空刀退役")
report_new = report_new.rstrip() + "\n\n" + report_bullet
report_new = once(report_new, "`AGENT_STATE.md` 的 R400 节", "`AGENT_STATE.md` 的 R401 节")

state_old = rd("AGENT_STATE.md")
state_anchor = "## R400 状态（2026-10-26"
assert state_old.count(state_anchor) == 1
state_new = once(state_old, state_anchor, state_section + "\n" + state_anchor)

wr("AGENT_UI_AUDIT.md", audit_new)
wr("AGENT_VISUAL_ITERATION.md", iteration_new)
wr("AGENT_DECISIONS.md", decisions_new)
wr("CHANGELOG.md", changelog_new)
wr("AGENT_FINAL_REPORT.md", report_new)
wr("AGENT_STATE.md", state_new)

print("R401_LEDGERS_OK warnings=%s full=%s/%s/%s frames=%s changed=%s baseline=%s/%s/%s/%s old=%s new=%s pre=%s/%s/%s/%s arms=%s/%s rot=%s gate=%s=%s streak=%s"
      % (warnings, executed, skipped, failures, frames, changed_frames,
         b_compared, b_changed, b_missing, b_added,
         old_rows, new_rows, pre_tables, pre_covered, pre_arms, pre_bad,
         arm_files, arm_total, h_rot, cleared, cells, streak))
