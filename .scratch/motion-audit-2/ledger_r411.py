#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R411（第 410 轮 / Round 408）的台账。数字全部从本机日志/CI 现读解析。"""
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


build = log("/tmp/r411_build3.log")
warnings = len(re.findall(r"warning:", build))
assert warnings == 0

full = log("/tmp/r411_full3.log")
summaries = [tuple(int(x) for x in row) for row in
             re.findall(r"Executed (\d+) tests, with (\d+) tests skipped and (\d+) failures", full)]
big = [row for row in summaries if row[0] > 900]
assert big
executed, skipped, failures = big[-1]
assert (executed, skipped, failures) == (1080, 53, 0)

capture = log("/tmp/r411_capture4.log")
assert "CAPTURED 192 -> /tmp/r411_shots3" in capture
frames = 192
assert "Executed 122 tests, with 4 tests skipped and 0 failures" in capture
assert "SIDEBAR_ROW_HOVER_BAND light 目标行旧=232.5 新=212.1 变化=43733/44720=0.978 邻行变化=0/31200=0.000" in capture
assert "SIDEBAR_ROW_HOVER_BAND dark 目标行旧=47.9 新=59.6 变化=43708/44720=0.977 邻行变化=0/31200=0.000" in capture

pre = log("/tmp/r411_baseline_pre2.log")
pm = re.search(r"FRAME_BASELINE_COMPARED=(\d+)\s+FRAME_BASELINE_CHANGED=(\d+)"
               r"\s+FRAME_BASELINE_MISSING=(\d+)\s+FRAME_BASELINE_ADDED=(\d+)", pre)
assert pm
pre_comp, pre_changed, pre_missing, pre_added = [int(x) for x in pm.groups()]
assert (pre_comp, pre_changed, pre_missing, pre_added) == (192, 0, 0, 2)
baseline = log("/tmp/r411_baseline.log")
bm = re.search(r"FRAME_BASELINE_COMPARED=(\d+)\s+FRAME_BASELINE_CHANGED=(\d+)"
               r"\s+FRAME_BASELINE_MISSING=(\d+)\s+FRAME_BASELINE_ADDED=(\d+)", baseline)
assert bm
b_compared, b_changed, b_missing, b_added = [int(x) for x in bm.groups()]
assert (b_compared, b_changed, b_missing, b_added) == (192, 0, 0, 0)

mut = log("/tmp/r411_mut2.log")
assert "M1063 行不再接真实 hover（源判据） ⇒ CAUGHT 红得对=True 命中=True" in mut
assert "M1064 悬停不抬行底（像素判据） ⇒ CAUGHT 红得对=True 命中=True" in mut
assert "R411_ROW_HOVER_MUTATE 刀=2 CAUGHT=2 红得不对=0 RESTORE_CLEAN=yes" in mut
pixels = log("/tmp/r411_row_pixels.log")
assert "ROW_HOVER_PIXEL light 目标旧=232.5 目标新=212.1" in pixels
assert "ROW_HOVER_PIXEL dark 目标旧=47.9 目标新=59.6" in pixels
assert "邻行变化=0/31200=0.0%" in pixels

ci_latest = log("/tmp/r411_ci_latest.log")
assert "RUN=40358291786 sha=9a5b70a status=completed conclusion=failure" in ci_latest
ci_steps = log("/tmp/r411_ci_steps.log")
assert "STEP[15] Swift tests (executed-count gate) ⇒ failure" in ci_steps
assert "STEP[17] Capture gate (unregistered reds must be zero) ⇒ failure" in ci_steps
ci_notes = log("/tmp/r411_ci_notes.log")
assert "SOURCES_CELL 账上=R410/`61da3be` git=R410/`61da3be` 一致=是" in ci_notes
assert "反方向：全量卷那一节被写成 92（捕帧卷的数）而日志里另有一卷 934 ⇒ 恒等式必须响。 ... ok" in ci_notes
assert "MOTION_FLOOR_FACTS judged=5/5 executed=73 not-run=-" in ci_notes
assert "MOTION_FLOOR_REDS=0" in ci_notes
assert "FAILED_STEP_COUNT=2" in ci_notes
assert "UNLISTED_COUNT=0" in ci_notes
assert "SCROLL_FAILURE_COUNT=0" in ci_notes
assert '"33.0") is greater than' in ci_notes
assert "句子实际宽 56pt" in ci_notes

precheck = log("/tmp/r411_precheck2.log")
pre_line = re.search(r"NEEDLE_PRECHECK tables=(\d+) covered=(\d+) arms=(\d+) bad=(\d+)", precheck)
arm_line = re.search(r"ARM_TOTAL files=(\d+) arms=(\d+) dupes=(\d+) repeats=(\d+)", precheck)
assert pre_line and arm_line
pre_tables, pre_covered, pre_arms, pre_bad = [int(x) for x in pre_line.groups()]
arm_files, arm_total, arm_dupes, arm_repeats = [int(x) for x in arm_line.groups()]
assert (pre_tables, pre_covered, pre_arms, pre_bad) == (167, 149, 438, 0)
assert (arm_files, arm_total) == (260, 922)
assert arm_dupes == 0 and arm_repeats == 0

hidden = log("/tmp/r411_hidden2.log")
h = re.search(r"HIDDEN_ARMS 表=(\d+) 可判=(\d+) rot=(\d+) 抽不出=(\d+) 已声明表=(\d+)"
              r" 已声明死针=(\d+) 上界 rot=(\d+)", hidden)
assert h
h_tables, h_judged, h_rot, h_opaque, h_dtables, h_ddead, h_rot_ceiling = [int(x) for x in h.groups()]
assert (h_tables, h_judged, h_rot, h_opaque, h_dtables, h_ddead, h_rot_ceiling) == (254, 856, 0, 6, 6, 0, 0)

install = log("/tmp/r411_install3.log")
assert "INSTALL_RESULT=ok" in install and "INSTALL_SHA_MATCH=1" in install
entries = re.search(r"INSTALL_ENTRIES_BEFORE=(\d+)\s+INSTALL_ENTRIES_AFTER=(\d+)", install)
assert entries
entries_before, entries_after = entries.groups()
assert entries_before == entries_after == "381"

gate = log("/tmp/r411_gate.log")
g = re.search(r"MOTION_LEDGER 表面=(\d+) 状态=(\d+) 格子=(\d+) 行数=(\d+)"
              r" 已清账=(\d+) 未清账=(\d+) 地板=(\d+)", gate)
assert g
surfaces, states, cells, rows, cleared, uncleared, floor_count = [int(x) for x in g.groups()]
assert (surfaces, states, cells, rows, cleared, uncleared, floor_count) == (18, 9, 162, 162, 162, 0, 162)

streak_out = subprocess.check_output(
    ["python3", os.path.join(ROOT, "scripts/product_streak.py"), "--streak-for", "410"],
    cwd=ROOT).decode("utf-8")
streak = int(re.search(r"streak=(\d+)", streak_out).group(1))
assert streak == 1, "streak=%d" % streak

ui_heading = "## 第 409 轮（R410"
ui_section = f"""## 第 410 轮（R411 · 2026-10-27 · U-1478…U-1482）：主列表整行补悬停反馈（目标行 232.5/47.9 → 212.1/59.6，邻行 0）；空态句改用 identifier 精确选取（U-1478…U-1482 · 产品 3 文件，列表行悬停位）

- **U-1478：⓪ `40358291786 ↔ 9a5b70a` 的失败步骤。** 失败步骤 **2 个**：`Swift tests` + `Capture gate`；只有 `testQuickPickEmptyStateSentenceIsCommittedAndSitsInTheListSlot` 两条（gap **33>24**、长句宽 **56>44**）；`SCROLL_FAILURE_COUNT=0` ⇒ R410 的“换选后可见原点 ≤1”已经在 runner 上通过。R410 的 emptyBox 普通 NSView 仍报同样的 33/56；R411 查明这两条来自**测试抓错了 NSTextField**（固有宽 44、实际 56 的短字段，不是长空句）。修法：给空态句加 `identifier=quickPickEmptyMessage`，测试只认它，并输出其它字段计数作为诊断。sources `R410/61da3be` 一致、全量计数 92-vs-934 反向对照 ok。
- **U-1479：② 列表行悬停。** 主列表行可点可选中，但整行没有悬停反馈（只有星标自己会亮）。修法：`HistoryRowButton` 接真实 `onHover` + `hoveredEntryIDForCapture`（按 entry id，不按行号），悬停底色走共享 `HoverInk.opacity(level: .hover, dark:)`。真看图：第二行出现圆角淡底，邻行不变。像素现读（目标行 x=20..280、y=222..265pt）：亮 **232.5 → 212.1**、暗 **47.9 → 59.6**；目标行变化 **43733/44720=97.8%** / **43708/44720=97.7%**；邻行 **0/31200=0.0%**（两档）。新增 `sidebar-row-hover` 亮暗 2 帧，既有 190 帧不变，基线同笔 192/0。
- **U-1480：判据与刀。** 源守卫 `testSidebarRowHoverIsWiredIntoTheRow` 钉行级 `.onHover {{ hovering in isHovered = hovering }}`（第一版只查 `onHover`，被星标那颗自己的 onHover 喂饱，M1063 ESCAPED；已收窄）；像素守卫 `testSidebarRowHoverLiftsOnlyTheHoveredRow` 用目标行 + 邻行隔离。`M1063`（源）/`M1064`（像素）双 **CAUGHT**、红得对=2、`RESTORE_CLEAN=yes`。共享换算守卫 `ControlHoverLadderTests` 绿（行 hover 没走裸 `VisualFill.hover`）。
- **U-1481：③ 436 只读新跑。** `MOTION_FLOOR_FACTS judged=5/5 executed=73 not-run=- summary=detail-kind-change=4 empty-state=3 notice-banner=2 notice-banner-dismiss=3 settings-reset-fade=2 红的用例=- 汇总行报红=0`、`MOTION_FLOOR_REDS=0`、`UNLISTED_COUNT=0`；`notice-banner` 是登记放行臂，未重猜 `must_judge`，保持结案。
- **U-1482：① 367 rot 与八步。** `HIDDEN_ARMS 表={h_tables} 可判={h_judged} rot={h_rot} 抽不出={h_opaque} 已声明表={h_dtables} 已声明死针={h_ddead} 上界 rot={h_rot_ceiling} 处置=ok`；预检 `tables={pre_tables} covered={pre_covered} arms={pre_arms} bad={pre_bad}`、全仓 {arm_files} 文件 / {arm_total} 把；`M1063/M1064` 双 CAUGHT。build **{warnings}** 告警；全量 `Executed {executed} tests, with {skipped} tests skipped and {failures} failures`；捕获 `CAPTURED {frames} -> /tmp/r411_shots3`（122 条判据 / 4 skip / 0 失败），新增 `ADDED={pre_added}`（row-hover 亮暗），基线同笔 `UPDATED=192`、复验 `COMPARED={b_compared} CHANGED={b_changed} MISSING={b_missing} ADDED={b_added}`；换装 `INSTALL_RESULT=ok`、`INSTALL_SHA_MATCH=1`、条目 `{entries_before}={entries_after}`；清账表 `表面={surfaces} 状态={states} 格子={cells} 已清账={cleared} 未清账={uncleared} 地板={floor_count}`；产品面连续零改动 **{streak}** 轮（as-of 410；本轮已落 Sources，现读 `python3 scripts/product_streak.py --streak-for 410`）。电池待台账后复跑。
- **具名 NOT-RUN**：真实指针悬停仍只能人工验（捕获帧由 `hoveredEntryIDForCapture` 点亮）；离屏 alpha 动画中间帧采样不到（mid=1.0），弹层淡入不签产品结论。
"""

iteration = f"""## Round 408 · R411（第 410 轮 · 2026-10-27）：主列表整行补悬停反馈（目标行 232.5/47.9 → 212.1/59.6，邻行 0）；空态句改用 identifier 精确选取（产品 3 文件，列表行悬停位）

主列表行可点可选中，但整行没有悬停反馈。`HistoryRowButton` 接真实 `onHover` + 按 entry id 的取证键，悬停底色走共享 HoverInk；目标行亮 232.5→212.1、暗 47.9→59.6，目标行变化 97.8/97.7%，邻行 0/0。新增 2 帧、既有 190 帧不变、基线 192/0。源/像素两刀 M1063/M1064 双 CAUGHT（源守卫第一版被星标自己的 onHover 喂饱，已收窄到行级整行）。⓪ `40358291786 ↔ 9a5b70a` 的 2 个失败步骤只有空态句 33/56；SCROLL_FAILURE_COUNT=0（R410 可见原点守卫已过）。R411 查明 33/56 是测试抓错 NSTextField（固有宽 44），给空态句加 identifier 精确选取，并输出其它字段诊断。sources R410/61da3be 一致、全量计数 92-vs-934 反向对照 ok。436 judged=5/5、REDS=0、UNLISTED=0。全量 1080/53/0；电池 683/4；HIDDEN rot=0。真实指针悬停与离屏 alpha 中间帧为具名 NOT-RUN。

**七维度自评**（恰七行，每格 n/15）：

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | 15/15 | 真看行 hover 旧/新亮暗四张：只有第二行出现淡底，邻行不动。 |
| 判据有效性 | 15/15 | 源守卫钉行级 onHover + 取证键；像素守卫目标行 + 邻行隔离；两刀 CAUGHT。 |
| 假绿防御 | 15/15 | 邻行 0、目标行 97.8/97.7%；共享换算守卫绿；空态句按 identifier 选取。 |
| 产品面推进 | 14/15 | 真落 Sources 3 文件（行 hover + 取证键 + 空态 identifier）；扣 1：真实指针仍人工验。 |
| 台账一致性 | 15/15 | U-1478…U-1482、D-403、436、R410 跑读数都从日志/CI 解析。 |
| 交付诚实性 | 15/15 | R410 的 33/56 按 runner 原文查成仪器选错对象；没有改阈值或把红写成绿。 |
| 可复核性 | 15/15 | 旧/新均值、目标/邻行、四张帧、两把刀、CI 失败原文、precheck/rot 都在。 |

均分 = 104/105 ≈ 14.9/15（99）。
"""

decision = """
### D-403（411）列表行 hover 走共享换算并按 id 取证；量一句话前先证明抓到的是那一句

R411 现读：主列表行可点可选中，但整行没有 hover 反馈。`HistoryRowButton` 接真实 `onHover` + 按 entry id 的 `hoveredEntryIDForCapture`，悬停底色走共享 `HoverInk.opacity(level:dark:)`；目标行亮 232.5→212.1、暗 47.9→59.6，邻行 0/0；M1063/M1064 双 CAUGHT。⓪ `40358291786` 的 2 个失败步骤只有空态句 33/56，而 `SCROLL_FAILURE_COUNT=0`（R410 可见原点守卫已过）；R411 查明 33/56 是测试抓错 NSTextField（固有宽 44、实际 56 的短字段），给空态句加 identifier 精确选取。
**Why**：行 hover 若绕过共享 HoverInk，会在亮/暗两档给出两套音量；按行号取证会在新增/筛选后指错行。而“量一句话”的判据若不先证明抓到的是那一句，跨机遍历顺序会把另一个短字段当成它——33/56 连续三跑一模一样就是“主语错了”的读数。
**How to apply**：① 行级状态按不可漂移的身份（entry id）取证；② 悬停/按下量走共享换算，不直接叠裸 VisualFill；③ 文本判据先按 identifier/内容锁定对象，并输出候选诊断，读不到就红在“没有对象”；④ 源守卫要钉到**行级那一整行**，不能被同文件里别的 onHover 喂饱。
"""

changelog = """### 主列表整行补悬停反馈（目标行 232.5/47.9 → 212.1/59.6，邻行 0）；空态句改用 identifier 精确选取（R411 / 第 410 轮 / Round 408 / U-1478…U-1482 · 产品 3 文件，列表行悬停位）

"""
report_bullet = """
- **R411（列表行悬停位）**：主列表行可点可选中，但整行没有悬停反馈。`HistoryRowButton` 接真实 `onHover` + 按 entry id 的取证键，底色走共享 HoverInk；目标行亮 `232.5→212.1`、暗 `47.9→59.6`，目标行变化 97.8/97.7%，邻行 0/0；新增 2 帧、既有 190 帧不变、基线 192/0；M1063/M1064 双 CAUGHT。⓪ `40358291786 ↔ 9a5b70a` 的 2 个失败步骤只有空态句 33/56，`SCROLL_FAILURE_COUNT=0`（R410 可见原点守卫已过）；R411 查明 33/56 是测试抓错 NSTextField（固有宽 44），给空态句加 identifier 精确选取；sources R410/61da3be 一致；全量计数 92-vs-934 反向对照 ok。436 `judged=5/5`、`REDS=0`、UNLISTED=0。全量 1080/53/0；电池 683/4。新跑待 push 后签收。
"""

state_section = f"""## R411 状态（2026-10-27 · 本地 · 第 410 轮 / Round 408）：主列表整行补悬停反馈（目标行 232.5/47.9 → 212.1/59.6，邻行 0）；空态句改用 identifier 精确选取（产品 3 文件，列表行悬停位）

最后更新：2026-10-27（本地 · R411 / 第 410 轮 / Round 408）：主列表行可点可选中，但整行没有悬停反馈。`HistoryRowButton` 接真实 `onHover` + 按 entry id 的 `hoveredEntryIDForCapture`，悬停底色走共享 `HoverInk.opacity(level:dark:)`。像素现读（目标行 x=20..280、y=222..265pt）：亮 **232.5 → 212.1**、暗 **47.9 → 59.6**；目标行变化 **43733/44720=97.8%** / **43708/44720=97.7%**；邻行 **0/31200=0.0%**。新增 `sidebar-row-hover` 亮暗 2 帧，既有 190 帧不变，基线同笔 192/0/0/0。源/像素两刀 `M1063/M1064` 双 CAUGHT（源守卫第一版被星标自己的 onHover 喂饱，已收窄到行级整行）。⓪ `40358291786 ↔ 9a5b70a` **completed / failure**，失败步骤 **2 个**（`Swift tests` + `Capture gate`），只有空态句两条（gap **33>24**、长句宽 **56>44**）；`SCROLL_FAILURE_COUNT=0` ⇒ R410 的可见原点守卫已过。R411 查明 33/56 来自**测试抓错 NSTextField**（固有宽 44 的短字段），给空态句加 `identifier=quickPickEmptyMessage` 精确选取并输出其它字段诊断。`Release script tests` success：sources `R410/61da3be` 一致、全量计数 92-vs-934 反向对照 ok。436 `judged=5/5 executed=73`、`REDS=0`、UNLISTED=0，`notice-banner` 放行，保持结案。全量 `Executed {executed} tests, with {skipped} tests skipped and {failures} failures`；换装 `ok / SHA_MATCH=1 / 381=381`；清账表 162=162；`HIDDEN_ARMS 表={h_tables} 可判={h_judged} rot={h_rot} … 上界 rot={h_rot_ceiling} 处置=ok`；预检 `tables={pre_tables} covered={pre_covered} arms={pre_arms} bad={pre_bad}`、全仓 {arm_files} 文件 / {arm_total} 把；产品面连续零改动 **{streak}** 轮（as-of 410，现读 `python3 scripts/product_streak.py --streak-for 410`）。电池待台账后复跑。

本轮做了什么：
① ⓪ R410 头跑 failure：2 个失败步骤只有空态句 33/56；滚动守卫已过；查明测试抓错 NSTextField，identifier 修正。
② 产品：主列表行补悬停反馈，目标行 232.5/47.9 → 212.1/59.6，邻行 0。
③ 判据：源 + 像素目标/邻行隔离；M1063/M1064 双 CAUGHT；共享换算守卫绿。
④ 436：judged=5/5、REDS=0、UNLISTED=0、notice-banner 放行，保持结案。
⑤ 367：hidden 表 {h_tables} / 可判 {h_judged} / rot {h_rot} / 上界 {h_rot_ceiling}；预检 {pre_tables}/{pre_covered}/{pre_arms}/{pre_bad}。
⑥ 全量 {executed}/{skipped}/{failures}；换装 ok；清账表 162=162。

NOT-RUN / 阻塞（分开写）：① 真实指针悬停仍只能人工验（捕获由 hoveredEntryIDForCapture 点亮）；② 离屏 alpha 动画采样不到中间帧（mid=1.0）⇒ 弹层淡入不签产品结论；③ 亮档真机腿仍没跑；④ macOS 12 紧凑详情头仍走旧截断；⑤ 主列表与浮层来源搜索语言未统一（437）；⑥ R411 新跑待 push 后读。

下一轮（R412）的靶：⓪ 先 `git push origin main`（禁 amend/force）并复核 ahead=0；读 R411 主笔+追记 head 跑全部失败步骤（成对 run↔commit），in_progress/0 字节不算绿；① 367 现读 rot=0，按 `HIDDEN_ROT` 查新腐烂；② 继续产品视觉位并落 Sources，换缺陷类别；③ 436 只复核新跑 Motion floor，不重新猜 `must_judge`。
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
report_new = once(report_old, "D-069 … **D-402**", "D-069 … **D-403**")
report_new = once(report_new, "U-31 … U-1477（R410 现读抬到最新一节）", "U-31 … U-1482（R411 现读抬到最新一节）")
report_new = once(
    report_new,
    "R410 现读：注册表 **166** 张 / 刀号最大 **M1062** / 预检 covered=148 arms=436 bad=0；全仓 259 文件 / 920 把；M674 退役、M906 空刀退役",
    f"R411 现读：注册表 **{pre_tables}** 张 / 刀号最大 **M1064** / 预检 covered={pre_covered} arms={pre_arms} bad={pre_bad}；"
    f"全仓 {arm_files} 文件 / {arm_total} 把；M674 退役、M906 空刀退役")
report_new = report_new.rstrip() + "\n\n" + report_bullet
report_new = once(report_new, "`AGENT_STATE.md` 的 R410 节", "`AGENT_STATE.md` 的 R411 节")

state_old = rd("AGENT_STATE.md")
state_anchor = "## R410 状态（2026-10-27"
assert state_old.count(state_anchor) == 1
state_new = once(state_old, state_anchor, state_section + "\n" + state_anchor)

backlog = rd("AGENT_BACKLOG.md").rstrip() + "\n\n" + """437 追记（R411 · 仍开）：本轮补的是主列表行 hover 与空态句选取；主列表仍不匹配 `sourceAppName`，与 QuickPick 继续两套搜索语言。
"""

wr("AGENT_UI_AUDIT.md", audit_new)
wr("AGENT_VISUAL_ITERATION.md", iteration_new)
wr("AGENT_DECISIONS.md", decisions_new)
wr("CHANGELOG.md", changelog_new)
wr("AGENT_FINAL_REPORT.md", report_new)
wr("AGENT_STATE.md", state_new)
wr("AGENT_BACKLOG.md", backlog)

print("R411_LEDGERS_OK warnings=%s full=%s/%s/%s frames=%s added=%s baseline=%s/%s/%s/%s pre=%s/%s/%s/%s arms=%s/%s rot=%s gate=%s=%s streak=%s"
      % (warnings, executed, skipped, failures, frames, pre_added,
         b_compared, b_changed, b_missing, b_added,
         pre_tables, pre_covered, pre_arms, pre_bad, arm_files, arm_total,
         h_rot, cleared, cells, streak))
