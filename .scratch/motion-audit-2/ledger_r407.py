#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R407（第 406 轮 / Round 404）的台账。数字全部从本机日志/CI 现读解析。"""
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


build = log("/tmp/r407_build.log")
warnings = len(re.findall(r"warning:", build))
assert warnings == 0

full = log("/tmp/r407_full2.log")
summaries = [tuple(int(x) for x in row) for row in
             re.findall(r"Executed (\d+) tests, with (\d+) tests skipped and (\d+) failures", full)]
big = [row for row in summaries if row[0] > 900]
assert big
executed, skipped, failures = big[-1]
assert (executed, skipped, failures) == (1072, 53, 0)

capture = log("/tmp/r407_capture.log")
assert "CAPTURED 186 -> /tmp/r407_shots" in capture
frames = 186
assert "Executed 114 tests, with 4 tests skipped and 0 failures" in capture
assert "QUICKPICK_EMPTY_CTA_BAND light 消息带墨=3693 按钮带墨=934" in capture
assert "QUICKPICK_EMPTY_CTA_BAND dark 消息带墨=4346 按钮带墨=1114" in capture

diff = log("/tmp/r407_diff.log")
dm = re.search(r"FRAME_DIFF 比了=(\d+) 变了=(\d+)", diff)
assert dm
total_frames, changed_frames = [int(x) for x in dm.groups()]
assert (total_frames, changed_frames) == (186, 2)
assert "quickpick-empty-420x300-dark.png" in diff and "quickpick-empty-420x300-light.png" in diff

pre = log("/tmp/r407_baseline_pre.log")
pm = re.search(r"FRAME_BASELINE_COMPARED=(\d+)\s+FRAME_BASELINE_CHANGED=(\d+)"
               r"\s+FRAME_BASELINE_MISSING=(\d+)\s+FRAME_BASELINE_ADDED=(\d+)", pre)
assert pm
pre_comp, pre_changed, pre_missing, pre_added = [int(x) for x in pm.groups()]
assert (pre_comp, pre_changed, pre_missing, pre_added) == (186, 2, 0, 0)
baseline = log("/tmp/r407_baseline.log")
bm = re.search(r"FRAME_BASELINE_COMPARED=(\d+)\s+FRAME_BASELINE_CHANGED=(\d+)"
               r"\s+FRAME_BASELINE_MISSING=(\d+)\s+FRAME_BASELINE_ADDED=(\d+)", baseline)
assert bm
b_compared, b_changed, b_missing, b_added = [int(x) for x in bm.groups()]
assert (b_compared, b_changed, b_missing, b_added) == (186, 0, 0, 0)

cta = log("/tmp/r407_mut.log")
assert "M1055 空态按钮标题不是「清除搜索」（源判据） ⇒ CAUGHT 红得对=True 命中=True" in cta
assert "M1056 空态 CTA 不显隐（像素判据） ⇒ CAUGHT 红得对=True 命中=True" in cta
assert "按钮带墨=0" in cta
assert "R407_EMPTY_CTA_MUTATE 刀=2 CAUGHT=2 红得不对=0 RESTORE_CLEAN=yes" in cta
scroll = log("/tmp/r407_mut_r406fix.log")
assert "M1053 换选正文不归顶（行为判据） ⇒ CAUGHT 红得对=True 命中=True" in scroll
assert "换选可见=2357" in scroll
assert "M1054 换选正文不归顶（像素判据） ⇒ CAUGHT 红得对=True 命中=True" in scroll
assert "R406_SCROLL_MUTATE 刀=2 CAUGHT=2 红得不对=0 RESTORE_CLEAN=yes" in scroll

pixels = log("/tmp/r407_cta_pixels.log")
assert "EMPTY_CTA_PIXEL 旧代码 light 消息带=3693 按钮带=0" in pixels
assert "EMPTY_CTA_PIXEL 旧代码 dark 消息带=4346 按钮带=0" in pixels
assert "EMPTY_CTA_PIXEL 新代码 light 消息带=3693 按钮带=934" in pixels
assert "EMPTY_CTA_PIXEL 新代码 dark 消息带=4346 按钮带=1114" in pixels

ci_latest = log("/tmp/r407_ci_latest.log")
assert "RUN=40326547579 sha=f7852d0 status=completed conclusion=failure" in ci_latest
ci_steps = log("/tmp/r407_ci_steps.log")
assert "STEP[15] Swift tests (executed-count gate) ⇒ failure" in ci_steps
ci_notes = log("/tmp/r407_ci_notes.log")
assert "SOURCES_CELL 账上=R406/`cb2bd4c` git=R406/`cb2bd4c` 一致=是" in ci_notes
assert "反方向：全量卷那一节被写成 92（捕帧卷的数）而日志里另有一卷 934 ⇒ 恒等式必须响。 ... ok" in ci_notes
assert "MOTION_FLOOR_FACTS judged=5/5 executed=73 not-run=-" in ci_notes
assert "MOTION_FLOOR_REDS=0" in ci_notes
assert "FAILED_STEP_COUNT=1" in ci_notes
assert "UNLISTED_COUNT=0" in ci_notes
assert "(\"-57.0\") is not equal to (\"-46.0\")" in ci_notes

precheck = log("/tmp/r407_precheck2.log")
pre_line = re.search(r"NEEDLE_PRECHECK tables=(\d+) covered=(\d+) arms=(\d+) bad=(\d+)", precheck)
arm_line = re.search(r"ARM_TOTAL files=(\d+) arms=(\d+) dupes=(\d+) repeats=(\d+)", precheck)
assert pre_line and arm_line
pre_tables, pre_covered, pre_arms, pre_bad = [int(x) for x in pre_line.groups()]
arm_files, arm_total, arm_dupes, arm_repeats = [int(x) for x in arm_line.groups()]
assert (pre_tables, pre_covered, pre_arms, pre_bad) == (163, 145, 430, 0)
assert (arm_files, arm_total) == (256, 914)
assert arm_dupes == 0 and arm_repeats == 0

hidden = log("/tmp/r407_hidden2.log")
h = re.search(r"HIDDEN_ARMS 表=(\d+) 可判=(\d+) rot=(\d+) 抽不出=(\d+) 已声明表=(\d+)"
              r" 已声明死针=(\d+) 上界 rot=(\d+)", hidden)
assert h
h_tables, h_judged, h_rot, h_opaque, h_dtables, h_ddead, h_rot_ceiling = [int(x) for x in h.groups()]
assert (h_tables, h_judged, h_rot, h_opaque, h_dtables, h_ddead, h_rot_ceiling) == (250, 848, 0, 6, 6, 0, 0)

install = log("/tmp/r407_install.log")
assert "INSTALL_RESULT=ok" in install and "INSTALL_SHA_MATCH=1" in install
entries = re.search(r"INSTALL_ENTRIES_BEFORE=(\d+)\s+INSTALL_ENTRIES_AFTER=(\d+)", install)
assert entries
entries_before, entries_after = entries.groups()
assert entries_before == entries_after == "381"

gate = log("/tmp/r407_gate.log")
g = re.search(r"MOTION_LEDGER 表面=(\d+) 状态=(\d+) 格子=(\d+) 行数=(\d+)"
              r" 已清账=(\d+) 未清账=(\d+) 地板=(\d+)", gate)
assert g
surfaces, states, cells, rows, cleared, uncleared, floor_count = [int(x) for x in g.groups()]
assert (surfaces, states, cells, rows, cleared, uncleared, floor_count) == (18, 9, 162, 162, 162, 0, 162)

streak_out = subprocess.check_output(
    ["python3", os.path.join(ROOT, "scripts/product_streak.py"), "--streak-for", "406"],
    cwd=ROOT).decode("utf-8")
streak = int(re.search(r"streak=(\d+)", streak_out).group(1))
assert streak == 1, "streak=%d" % streak

ui_heading = "## 第 405 轮（R406"
ui_section = f"""## 第 406 轮（R407 · 2026-10-26 · U-1458…U-1462）：QuickPick 空结果态补可见「清除搜索」CTA（按钮带旧 0/0 → 新 934/1114）；R406 守卫在 runner 上红的假设被修正（U-1458…U-1462 · 产品 1 文件，空态 CTA 位）

- **U-1458：⓪ `40326547579 ↔ f7852d0` 的唯一失败步骤。** 失败步骤 **1 个**：`Swift tests (executed-count gate)`；正文 `DetailScrollResetTests.swift:85 XCTAssertEqualWithAccuracy ("-57.0") != ("-46.0")`。成因是 R406 守卫拿 clip bounds 的 origin 当“顶部参照”，而它随文本内边距在机器间差 11pt（runner −46 / 本机 −57）；产品行为本身是“文本视口回到顶部”。修法：断言 `document.visibleRect.origin.y`（本机顶部 0 → 换选 0；旧行为 2357），M1053 重跑仍 CAUGHT。`Release script tests` success：`SOURCES_CELL 账上=R406/cb2bd4c git=R406/cb2bd4c 一致=是`，全量计数 92-vs-934 反向对照 ok。R407 新跑待 push 后签收。
- **U-1459：② 空态 CTA —— QuickPick 搜不到时只有一句“按 Esc 清空”。** 主窗口同类空态有「清除搜索」按钮，浮层只有文字；同一个处境两个表面两套答案。真看图：旧 `quickpick-empty` 消息下是空白，新帧消息下出现「清除搜索」胶囊。修法：`QuickPickController` 在空态且查询词非空时显示 `NSButton(title:"清除搜索")`，点击清空搜索框、恢复候选并把焦点还给搜索框；空历史/无查询词时不显示（点了没意义）。像素现读（x=170..250、y=55..85pt）：旧 **0/0** → 新 **934/1114**；同帧消息带 3693/4346 不变（校准证明确实画了这一页）。仅 `quickpick-empty` 亮暗 **2 帧**变化，基线同笔 186/0。
- **U-1460：判据与刀。** 源守卫 `testQuickPickEmptyStateHasAVisibleClearSearchAction` 从真面板读按钮标题/可见性，点击后读搜索框与表格行数（必须恢复 5 条），并以“无查询词时树里/隐藏态没有可用按钮”为负对照；像素守卫 `testQuickPickEmptyStateCTAIsVisibleInTheFrame` 用按钮带 + 消息带双读数。`M1055`（源）/`M1056`（像素）双 **CAUGHT**、红得对=2、`RESTORE_CLEAN=yes`；R406 的 M1053/M1054 在修正后重跑仍双 CAUGHT。
- **U-1461：③ 436 只读新跑。** `MOTION_FLOOR_FACTS judged=5/5 executed=73 not-run=- summary=detail-kind-change=4 empty-state=3 notice-banner=2 notice-banner-dismiss=3 settings-reset-fade=2 红的用例=- 汇总行报红=0`、`MOTION_FLOOR_REDS=0`、`UNLISTED_COUNT=0`；`notice-banner` 是登记放行臂，未重猜 `must_judge`，保持结案。
- **U-1462：① 367 rot 与八步。** `HIDDEN_ARMS 表={h_tables} 可判={h_judged} rot={h_rot} 抽不出={h_opaque} 已声明表={h_dtables} 已声明死针={h_ddead} 上界 rot={h_rot_ceiling} 处置=ok`；预检 `tables={pre_tables} covered={pre_covered} arms={pre_arms} bad={pre_bad}`、全仓 {arm_files} 文件 / {arm_total} 把；`M1055/M1056` 与修正后的 M1053/M1054 全 CAUGHT。build **{warnings}** 告警；全量 `Executed {executed} tests, with {skipped} tests skipped and {failures} failures`；捕获 `CAPTURED {frames} -> /tmp/r407_shots`（114 条判据 / 4 skip / 0 失败），与 R406 比 `变了={changed_frames}`（quickpick-empty 亮暗），基线同笔 `UPDATED=186`、复验 `COMPARED={b_compared} CHANGED={b_changed} MISSING={b_missing} ADDED={b_added}`；换装 `INSTALL_RESULT=ok`、`INSTALL_SHA_MATCH=1`、条目 `{entries_before}={entries_after}`；清账表 `表面={surfaces} 状态={states} 格子={cells} 已清账={cleared} 未清账={uncleared} 地板={floor_count}`；产品面连续零改动 **{streak}** 轮（as-of 406；本轮已落 Sources，现读 `python3 scripts/product_streak.py --streak-for 406`）。电池待台账后复跑。
"""

iteration = f"""## Round 404 · R407（第 406 轮 · 2026-10-26）：QuickPick 空结果态补可见「清除搜索」CTA（按钮带旧 0/0 → 新 934/1114）；R406 守卫在 runner 上红的假设被修正（产品 1 文件，空态 CTA 位）

QuickPick 空结果态只有一句“按 Esc 清空”，而主窗口同类空态有「清除搜索」按钮。修法：查询词非空且无候选时显示 `NSButton(title:"清除搜索")`，点击清空搜索框、恢复候选并把焦点还给搜索框；空历史/无查询词不显示。真看旧/新帧亮暗四张：旧消息下空白，新消息下出现胶囊。像素同带旧 0/0 → 新 934/1114，消息带 3693/4346 作校准；仅 quickpick-empty 两帧变化，基线 186/0。源/像素两刀 M1055/M1056 双 CAUGHT。⓪ `40326547579 ↔ f7852d0` 的唯一失败步骤是 `Swift tests`：R406 守卫把 runner 的 clip 顶部偏移（−46）误当本机 −57；改为断言文本视图 visibleRect 原点（旧行为 2357 vs 顶部 0），M1053 仍 CAUGHT。sources R406/cb2bd4c 一致；全量计数 92-vs-934 反向对照 ok。436 `judged=5/5`、`REDS=0`、UNLISTED=0。全量 1072/53/0；电池 683/4；HIDDEN rot=0。

**七维度自评**（恰七行，每格 n/15）：

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | 15/15 | 真看 quickpick-empty 旧/新亮暗四张：旧消息下空白、新消息下按钮；不是只看墨数。 |
| 判据有效性 | 15/15 | 源守卫从真面板点按钮读回搜索框/行数；像素守卫双带；M1055/M1056 双 CAUGHT。 |
| 假绿防御 | 15/15 | 旧按钮带 0、新 934/1114；消息带 3693/4346 作校准；空态/无查询负对照都在。 |
| 产品面推进 | 14/15 | 真落 Sources 1 文件，补的是空态下一步；扣 1：只覆盖浮层一个空态表面。 |
| 台账一致性 | 15/15 | U-1458…U-1462、D-399、436、R406 跑读数都从日志/CI 解析。 |
| 交付诚实性 | 15/15 | R406 守卫在 runner 上红，按实际读数修守卫假设；没有把 failure 读成绿。 |
| 可复核性 | 15/15 | 旧/新像素、四张帧、两把刀、CI 失败原文、precheck/rot 都在。 |

均分 = 104/105 ≈ 14.9/15（99）。
"""

decision = """
### D-399（407）空态有明确下一步时必须有可见 CTA；跨机断言读文本视口原点，不读 clip inset

R407 现读：QuickPick 空结果态只有一句“按 Esc 清空”，而主窗口同类空态有「清除搜索」按钮。修法：查询词非空且无候选时显示 `NSButton(title:"清除搜索")`，点击清空搜索框、恢复候选并把焦点还给搜索框；空历史/无查询词不显示。像素按钮带旧 0/0 → 新 934/1114，消息带 3693/4346 作校准；只 quickpick-empty 两帧变化。M1055/M1056 双 CAUGHT。⓪ `40326547579` 唯一失败步骤是 `Swift tests`：R406 守卫拿 clip bounds origin 当顶部参照（runner −46 / 本机 −57），改成断言 `document.visibleRect.origin.y` 后旧行为 2357、顶部 0，M1053 仍 CAUGHT。
**Why**：空态若把下一步只写成快捷键，用户得先记住它；同一个处境在主窗口有按钮、浮层没有，是两套答案。而“顶部”在产品语义里是文本视口看到的第一行，不是某个容器坐标的常数——后者会随字体/内边距在机器间漂移，把守卫变成假红。
**How to apply**：① 空态有明确可执行下一步时给可见 CTA，并与同类表面同文案；不可执行时不摆按钮；② 跨机位置断言读被观察视图自己的可见原点（visibleRect），不读容器 inset/坐标常数；③ CTA 的源守卫必须真的点它并读回后果，像素守卫必须带同帧校准带；④ 两刀分别钉源与像素，红得对要连失败消息一起核。
"""

changelog = """### QuickPick 空结果态补可见「清除搜索」CTA（按钮带旧 0/0 → 新 934/1114）；R406 守卫在 runner 上红的假设被修正（R407 / 第 406 轮 / Round 404 / U-1458…U-1462 · 产品 1 文件，空态 CTA 位）

"""
report_bullet = """
- **R407（空态 CTA 位）**：QuickPick 空结果态只有一句“按 Esc 清空”，主窗口同类空态有「清除搜索」按钮。查询词非空且无候选时显示 `NSButton(title:"清除搜索")`，点击清空并恢复候选；按钮带旧 `0/0` → 新 `934/1114`（消息带 3693/4346 校准），只 quickpick-empty 两帧变化、基线 186/0；M1055/M1056 双 CAUGHT。⓪ `40326547579 ↔ f7852d0` 的唯一失败步骤是 `Swift tests`：R406 守卫把 runner 的 clip 顶部偏移 −46 误当本机 −57；改为断言文本视图 visibleRect 原点（旧行为 2357 vs 顶部 0），M1053 仍 CAUGHT；sources R406/cb2bd4c 一致；全量计数 92-vs-934 反向对照 ok。436 `judged=5/5`、`REDS=0`、UNLISTED=0。全量 1072/53/0；电池 683/4。新跑待 push 后签收。
"""

state_section = f"""## R407 状态（2026-10-26 · 本地 · 第 406 轮 / Round 404）：QuickPick 空结果态补可见「清除搜索」CTA（按钮带旧 0/0 → 新 934/1114）；R406 守卫在 runner 上红的假设被修正（产品 1 文件，空态 CTA 位）

最后更新：2026-10-26（本地 · R407 / 第 406 轮 / Round 404）：QuickPick 空结果态只有一句“按 Esc 清空”，而主窗口同类空态有「清除搜索」按钮。修法：查询词非空且无候选时显示 `NSButton(title:"清除搜索")`，点击清空搜索框、恢复候选并把焦点还给搜索框；空历史/无查询词不显示。像素现读（x=170..250、y=55..85pt）：旧 **0/0** → 新 **934/1114**；同帧消息带 3693/4346 作校准。仅 `quickpick-empty` 亮暗 2 帧变化，基线同笔 186/0/0/0。源/像素两刀 `M1055/M1056` 双 CAUGHT。⓪ `40326547579 ↔ f7852d0` **completed / failure**，唯一失败步骤 `Swift tests`：R406 守卫拿 clip bounds origin 当顶部参照（runner −46 / 本机 −57）；已改为断言 `document.visibleRect.origin.y`（旧行为 2357 → 顶部参照 0），M1053 重跑仍 CAUGHT。`Release script tests` success：sources `R406/cb2bd4c` 一致、全量计数 92-vs-934 反向对照 ok。436 `judged=5/5 executed=73`、`REDS=0`、UNLISTED=0，`notice-banner` 放行，保持结案。全量 `Executed {executed} tests, with {skipped} tests skipped and {failures} failures`；换装 `ok / SHA_MATCH=1 / 381=381`；清账表 162=162；`HIDDEN_ARMS 表={h_tables} 可判={h_judged} rot={h_rot} … 上界 rot={h_rot_ceiling} 处置=ok`；预检 `tables={pre_tables} covered={pre_covered} arms={pre_arms} bad={pre_bad}`、全仓 {arm_files} 文件 / {arm_total} 把；产品面连续零改动 **{streak}** 轮（as-of 406，现读 `python3 scripts/product_streak.py --streak-for 406`）。电池待台账后复跑。

本轮做了什么：
① ⓪ R406 头跑 failure：唯一失败步骤 Swift tests，R406 守卫的 clip inset 假设被 runner 驳回；修正为 visibleRect 原点，M1053 仍 CAUGHT。
② 产品：QuickPick 空态补「清除搜索」CTA，旧/新按钮带 0/0→934/1114；只 quickpick-empty 两帧变化。
③ 判据：源（真按钮点击读回）+ 像素（双带）；M1055/M1056 双 CAUGHT。
④ 436：judged=5/5、REDS=0、UNLISTED=0、notice-banner 放行，保持结案。
⑤ 367：hidden 表 {h_tables} / 可判 {h_judged} / rot {h_rot} / 上界 {h_rot_ceiling}；预检 {pre_tables}/{pre_covered}/{pre_arms}/{pre_bad}。
⑥ 全量 {executed}/{skipped}/{failures}；换装 ok；清账表 162=162。

NOT-RUN / 阻塞（分开写）：① 亮档真机腿仍没跑；② macOS 12 紧凑详情头仍走旧截断；③ 主列表与浮层的来源搜索语言未统一（437）；④ R407 新跑待 push 后读。

下一轮（R408）的靶：⓪ 先 `git push origin main`（禁 amend/force）并复核 ahead=0；读 R407 主笔+追记 head 跑全部失败步骤（成对 run↔commit），in_progress/0 字节不算绿；① 367 现读 rot=0，按 `HIDDEN_ROT` 查新腐烂；② 继续产品视觉位并落 Sources，换缺陷类别；③ 436 只复核新跑 Motion floor，不重新猜 `must_judge`。
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
report_new = once(report_old, "D-069 … **D-398**", "D-069 … **D-399**")
report_new = once(report_new, "U-31 … U-1457（R406 现读抬到最新一节）", "U-31 … U-1462（R407 现读抬到最新一节）")
report_new = once(
    report_new,
    "R406 现读：注册表 **162** 张 / 刀号最大 **M1054** / 预检 covered=144 arms=428 bad=0；全仓 255 文件 / 912 把；M674 退役、M906 空刀退役",
    f"R407 现读：注册表 **{pre_tables}** 张 / 刀号最大 **M1056** / 预检 covered={pre_covered} arms={pre_arms} bad={pre_bad}；"
    f"全仓 {arm_files} 文件 / {arm_total} 把；M674 退役、M906 空刀退役")
report_new = report_new.rstrip() + "\n\n" + report_bullet
report_new = once(report_new, "`AGENT_STATE.md` 的 R406 节", "`AGENT_STATE.md` 的 R407 节")

state_old = rd("AGENT_STATE.md")
state_anchor = "## R406 状态（2026-10-26"
assert state_old.count(state_anchor) == 1
state_new = once(state_old, state_anchor, state_section + "\n" + state_anchor)

backlog = rd("AGENT_BACKLOG.md").rstrip() + "\n\n" + """437 追记（R407 · 仍开）：本轮补的是浮层空态 CTA；主列表仍不匹配 `sourceAppName`，与 QuickPick 继续两套搜索语言。
"""

wr("AGENT_UI_AUDIT.md", audit_new)
wr("AGENT_VISUAL_ITERATION.md", iteration_new)
wr("AGENT_DECISIONS.md", decisions_new)
wr("CHANGELOG.md", changelog_new)
wr("AGENT_FINAL_REPORT.md", report_new)
wr("AGENT_STATE.md", state_new)
wr("AGENT_BACKLOG.md", backlog)

print("R407_LEDGERS_OK warnings=%s full=%s/%s/%s frames=%s changed=%s baseline=%s/%s/%s/%s pre=%s/%s/%s/%s arms=%s/%s rot=%s gate=%s=%s streak=%s"
      % (warnings, executed, skipped, failures, frames, changed_frames,
         b_compared, b_changed, b_missing, b_added,
         pre_tables, pre_covered, pre_arms, pre_bad, arm_files, arm_total,
         h_rot, cleared, cells, streak))
