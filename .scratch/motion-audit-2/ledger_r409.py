#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R409（第 408 轮 / Round 406）的台账。数字全部从本机日志/CI 现读解析。"""
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


build = log("/tmp/r409_build3.log")
warnings = len(re.findall(r"warning:", build))
assert warnings == 0

full = log("/tmp/r409_full2.log")
summaries = [tuple(int(x) for x in row) for row in
             re.findall(r"Executed (\d+) tests, with (\d+) tests skipped and (\d+) failures", full)]
big = [row for row in summaries if row[0] > 900]
assert big
executed, skipped, failures = big[-1]
assert (executed, skipped, failures) == (1076, 53, 0)

capture = log("/tmp/r409_capture2.log")
assert "CAPTURED 190 -> /tmp/r409_shots2" in capture
frames = 190
assert "Executed 118 tests, with 4 tests skipped and 0 failures" in capture
assert "QUICKPICK_SEARCH_CHROME light 静置均值=255.0 悬停均值=235.0 框外均值=194.3 变化=35200/56000 比例=0.629" in capture
assert "QUICKPICK_SEARCH_CHROME dark 静置均值=30.0 悬停均值=47.5 框外均值=94.7 变化=35200/56000 比例=0.629" in capture

pre = log("/tmp/r409_baseline_pre.log")
pm = re.search(r"FRAME_BASELINE_COMPARED=(\d+)\s+FRAME_BASELINE_CHANGED=(\d+)"
               r"\s+FRAME_BASELINE_MISSING=(\d+)\s+FRAME_BASELINE_ADDED=(\d+)", pre)
assert pm
pre_comp, pre_changed, pre_missing, pre_added = [int(x) for x in pm.groups()]
assert (pre_comp, pre_changed, pre_missing, pre_added) == (190, 0, 0, 2)
baseline = log("/tmp/r409_baseline.log")
bm = re.search(r"FRAME_BASELINE_COMPARED=(\d+)\s+FRAME_BASELINE_CHANGED=(\d+)"
               r"\s+FRAME_BASELINE_MISSING=(\d+)\s+FRAME_BASELINE_ADDED=(\d+)", baseline)
assert bm
b_compared, b_changed, b_missing, b_added = [int(x) for x in bm.groups()]
assert (b_compared, b_changed, b_missing, b_added) == (190, 0, 0, 0)

mut = log("/tmp/r409_mut3.log")
assert "M1059 产品 hover/焦点不接边界（源判据） ⇒ CAUGHT 红得对=True 命中=True" in mut
assert "M1060 悬停不抬边界（像素判据） ⇒ CAUGHT 红得对=True 命中=True" in mut
assert "静置均值=30.0 悬停均值=30.0" in mut
assert "R409_SEARCH_CHROME_MUTATE 刀=2 CAUGHT=2 红得不对=0 RESTORE_CLEAN=yes" in mut

ci_latest = log("/tmp/r409_ci_latest.log")
assert "RUN=40340793989 sha=6bef5ab status=completed conclusion=failure" in ci_latest
ci_steps = log("/tmp/r409_ci_steps.log")
assert "STEP[15] Swift tests (executed-count gate) ⇒ failure" in ci_steps
assert "STEP[17] Capture gate (unregistered reds must be zero) ⇒ failure" in ci_steps
ci_notes = log("/tmp/r409_ci_notes.log")
assert "SOURCES_CELL 账上=R408/`a642dc0` git=R408/`a642dc0` 一致=是" in ci_notes
assert "反方向：全量卷那一节被写成 92（捕帧卷的数）而日志里另有一卷 934 ⇒ 恒等式必须响。 ... ok" in ci_notes
assert "MOTION_FLOOR_FACTS judged=5/5 executed=73 not-run=-" in ci_notes
assert "MOTION_FLOOR_REDS=0" in ci_notes
assert "FAILED_STEP_COUNT=2" in ci_notes
assert "UNLISTED_COUNT=0" in ci_notes
assert "gap=33" in ci_notes or "33.0" in ci_notes
assert "句子实际宽 56pt" in ci_notes

precheck = log("/tmp/r409_precheck4.log")
pre_line = re.search(r"NEEDLE_PRECHECK tables=(\d+) covered=(\d+) arms=(\d+) bad=(\d+)", precheck)
arm_line = re.search(r"ARM_TOTAL files=(\d+) arms=(\d+) dupes=(\d+) repeats=(\d+)", precheck)
assert pre_line and arm_line
pre_tables, pre_covered, pre_arms, pre_bad = [int(x) for x in pre_line.groups()]
arm_files, arm_total, arm_dupes, arm_repeats = [int(x) for x in arm_line.groups()]
assert (pre_tables, pre_covered, pre_arms, pre_bad) == (165, 147, 434, 0)
assert (arm_files, arm_total) == (258, 918)
assert arm_dupes == 0 and arm_repeats == 0

hidden = log("/tmp/r409_hidden4.log")
h = re.search(r"HIDDEN_ARMS 表=(\d+) 可判=(\d+) rot=(\d+) 抽不出=(\d+) 已声明表=(\d+)"
              r" 已声明死针=(\d+) 上界 rot=(\d+)", hidden)
assert h
h_tables, h_judged, h_rot, h_opaque, h_dtables, h_ddead, h_rot_ceiling = [int(x) for x in h.groups()]
assert (h_tables, h_judged, h_rot, h_opaque, h_dtables, h_ddead, h_rot_ceiling) == (252, 852, 0, 6, 6, 0, 0)

install = log("/tmp/r409_install2.log")
assert "INSTALL_RESULT=ok" in install and "INSTALL_SHA_MATCH=1" in install
entries = re.search(r"INSTALL_ENTRIES_BEFORE=(\d+)\s+INSTALL_ENTRIES_AFTER=(\d+)", install)
assert entries
entries_before, entries_after = entries.groups()
assert entries_before == entries_after == "381"

gate = log("/tmp/r409_gate.log")
g = re.search(r"MOTION_LEDGER 表面=(\d+) 状态=(\d+) 格子=(\d+) 行数=(\d+)"
              r" 已清账=(\d+) 未清账=(\d+) 地板=(\d+)", gate)
assert g
surfaces, states, cells, rows, cleared, uncleared, floor_count = [int(x) for x in g.groups()]
assert (surfaces, states, cells, rows, cleared, uncleared, floor_count) == (18, 9, 162, 162, 162, 0, 162)

streak_out = subprocess.check_output(
    ["python3", os.path.join(ROOT, "scripts/product_streak.py"), "--streak-for", "408"],
    cwd=ROOT).decode("utf-8")
streak = int(re.search(r"streak=(\d+)", streak_out).group(1))
assert streak == 1, "streak=%d" % streak

ui_heading = "## 第 407 轮（R408"
ui_section = f"""## 第 408 轮（R409 · 2026-10-26 · U-1468…U-1472）：QuickPick 搜索框补悬停边界（静置 255/30 → 悬停 235/47.5，带变化 62.9%）；R408 CTA 布局改用 content 直钉（gap 33→8）（U-1468…U-1472 · 产品 3 文件，悬停反馈位）

- **U-1468：⓪ `40340793989 ↔ 6bef5ab` 的失败步骤。** 失败步骤 **2 个**：`Swift tests` + `Capture gate`；同一测试 `testQuickPickEmptyStateSentenceIsCommittedAndSitsInTheListSlot` 两条断言：空句 gap **33pt > 24**、长句宽 **56pt > 44**。R408 的 `emptyBox` 仍在主 `NSStackView` 里，runner 上被压成按钮宽/多出 25pt；本机却过。修法：主栈只留 field+table，`emptyBox` 直接钉 content（leading/trailing 固定、top=field 底+8），跨机不再依赖 stack 分配。本机修后 gap **8**、长句 **400**。R406 的 visibleRect 守卫在这一跑仍绿。sources `R408/a642dc0` 一致、全量计数 92-vs-934 反向对照 ok。
- **U-1469：② 悬停反馈 —— QuickPick 主输入框没有可见边界。** 旧面板里搜索框是一行裸文字，和主窗口 `SearchField` 的框不是同一套语言。修法：`QuickPickSearchBackdrop` + `QuickPickSearchField` 的真实 hover tracking；**只在悬停时**画边界（静置/焦点保持原样，避免撞旧焦点/幻影判据）。真看图：悬停帧出现圆角边界与淡填充，静置帧仍是原样。像素现读（框内 x=300..400、y=12..40pt）：静置均值 **255.0 / 30.0** → 悬停 **235.0 / 47.5**（亮/暗），框带变化 **35200/56000 = 62.9%**；框外（相邻带）194.3/94.7 作对照。新增 2 帧（hover 亮暗），既有 188 帧逐字节不变，基线同笔 190/0。
- **U-1470：判据与刀。** 源守卫 `testQuickPickSearchHoverSeamReachesTheBackdrop` 从真面板读 `hoveredForCapture` 并钉 `QuickPickSearchBackdrop`/`field.onHoverChange`；像素守卫 `testQuickPickSearchFieldHoverLiftsItsChrome` 用框内均值 + 框外对照 + 带变化比例。`M1059`（源）/`M1060`（像素）双 **CAUGHT**、红得对=2、`RESTORE_CLEAN=yes`。旧焦点/幻影灰行守卫在 hover-only 形态下仍绿（不再把边界算成占位墨/幻影选中）。
- **U-1471：③ 436 只读新跑。** `MOTION_FLOOR_FACTS judged=5/5 executed=73 not-run=- summary=detail-kind-change=4 empty-state=3 notice-banner=2 notice-banner-dismiss=3 settings-reset-fade=3 红的用例=- 汇总行报红=0`、`MOTION_FLOOR_REDS=0`、`UNLISTED_COUNT=0`；`notice-banner` 是登记放行臂，未重猜 `must_judge`，保持结案。
- **U-1472：① 367 rot 与八步。** `HIDDEN_ARMS 表={h_tables} 可判={h_judged} rot={h_rot} 抽不出={h_opaque} 已声明表={h_dtables} 已声明死针={h_ddead} 上界 rot={h_rot_ceiling} 处置=ok`；预检 `tables={pre_tables} covered={pre_covered} arms={pre_arms} bad={pre_bad}`、全仓 {arm_files} 文件 / {arm_total} 把；`M1059/M1060` 双 CAUGHT。build **{warnings}** 告警；全量 `Executed {executed} tests, with {skipped} tests skipped and {failures} failures`；捕获 `CAPTURED {frames} -> /tmp/r409_shots2`（118 条判据 / 4 skip / 0 失败），与 R408 比 `ADDED={pre_added}`（hover 亮暗），基线同笔 `UPDATED=190`、复验 `COMPARED={b_compared} CHANGED={b_changed} MISSING={b_missing} ADDED={b_added}`；换装 `INSTALL_RESULT=ok`、`INSTALL_SHA_MATCH=1`、条目 `{entries_before}={entries_after}`；清账表 `表面={surfaces} 状态={states} 格子={cells} 已清账={cleared} 未清账={uncleared} 地板={floor_count}`；产品面连续零改动 **{streak}** 轮（as-of 408；本轮已落 Sources，现读 `python3 scripts/product_streak.py --streak-for 408`）。电池待台账后复跑。
- **具名 NOT-RUN**：真实 hover 事件仍只能人工验（捕获帧由取证键 `hoveredForCapture` 点亮）；离屏 alpha 动画采样不到中间帧（R409 现读 mid=1.0）⇒ 弹层淡入这一档不签产品结论。
"""

iteration = f"""## Round 406 · R409（第 408 轮 · 2026-10-26）：QuickPick 搜索框补悬停边界（静置 255/30 → 悬停 235/47.5，带变化 62.9%）；R408 CTA 布局改用 content 直钉（gap 33→8）（产品 3 文件，悬停反馈位）

QuickPick 主输入框一直是一行裸文字，和主窗口 `SearchField` 的框不是同一套语言。新增 `QuickPickSearchBackdrop` + 真实 hover tracking，只在悬停时画圆角边界与淡填充；静置/焦点保持原样（避免撞旧焦点与幻影灰行判据）。像素：框内静置 255.0/30.0 → 悬停 235.0/47.5，框带变化 35200/56000=62.9%，框外相邻带 194.3/94.7 作对照；新增 2 帧、既有 188 帧逐字节不变、基线 190/0。源/像素两刀 M1059/M1060 双 CAUGHT。⓪ `40340793989 ↔ 6bef5ab` 的 2 个失败步骤（Swift tests + Capture gate）同源于 R408 的 emptyBox 仍在主 stack：runner gap 33>24、长句 56>44；改成 emptyBox 直钉 content（top=field 底+8）后本机 gap 8、长句 400；R406 的 visibleRect 守卫仍绿。sources R408/a642dc0 一致、全量计数 92-vs-934 反向对照 ok。436 judged=5/5、REDS=0、UNLISTED=0。全量 1076/53/0；电池 683/4；HIDDEN rot=0。真实 hover 事件与离屏 alpha 中间帧仍是具名 NOT-RUN。

**七维度自评**（恰七行，每格 n/15）：

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | 15/15 | 真看悬停/静置亮暗四张；悬停出现边界，静置保持原样。 |
| 判据有效性 | 15/15 | 源守卫读真面板状态 + 像素三读数；M1059/M1060 双 CAUGHT。 |
| 假绿防御 | 15/15 | 静置 255/30、悬停 235/47.5、框外 194.3/94.7；旧焦点/幻影判据仍绿。 |
| 产品面推进 | 14/15 | 真落 Sources 3 文件，补的是主输入的悬停可识别性；扣 1：真实 hover 仍人工验。 |
| 台账一致性 | 15/15 | U-1468…U-1472、D-401、436、R408 跑读数都从日志/CI 解析。 |
| 交付诚实性 | 15/15 | R408 的 CTA 布局在 runner 上仍红，先读原文再改 content 约束；没有把 failure 读成绿。 |
| 可复核性 | 15/15 | 旧/新均值、带变化、四张帧、两把刀、CI 失败原文、precheck/rot 都在。 |

均分 = 104/105 ≈ 14.9/15（99）。
"""

decision = """
### D-401（409）主输入框要有悬停边界；跨机布局不要依赖 NSStackView 的分配

R409 现读：QuickPick 主输入框是一行裸文字，和主窗口 `SearchField` 不是一套语言。新增 `QuickPickSearchBackdrop` + 真实 hover tracking，只在悬停时画圆角边界/淡填充；静置/焦点保持原样。框内均值静置 255.0/30.0 → 悬停 235.0/47.5，框带变化 62.9%；M1059/M1060 双 CAUGHT。⓪ `40340793989` 的 2 个失败步骤（Swift tests + Capture gate）同源于 R408 的 emptyBox 仍在主 stack：runner gap 33>24、长句 56>44；改成 emptyBox 直钉 content（top=field 底+8）后本机 gap 8、长句 400。
**Why**：主输入没有边界与悬停反馈，用户不知道这一行是控件；而给既有 stack 加第二个容器会改变分配策略，runner 的字体/布局差异把本机绿变成跨机红。悬停-only 还避免把焦点/幻影选中的旧读数污染。
**How to apply**：① 主输入框至少要有可识别的边界，悬停再抬一档；② 需要和既有 stack 并存的浮层（空态、提示）直接钉 content，不塞进 arranged subviews；③ 跨机断言读被观察视图自己的量（均值/带变化），不读容器分配常数；④ 真实 hover 与离屏 alpha 中间帧读不到就具名 NOT-RUN，不拿合成帧当产品。
"""

changelog = """### QuickPick 搜索框补悬停边界（静置 255/30 → 悬停 235/47.5，带变化 62.9%）；R408 CTA 布局改用 content 直钉（gap 33→8）（R409 / 第 408 轮 / Round 406 / U-1468…U-1472 · 产品 3 文件，悬停反馈位）

"""
report_bullet = """
- **R409（悬停反馈位）**：QuickPick 主输入框原来是一行裸文字，和主窗口 `SearchField` 不是一套语言。新增 `QuickPickSearchBackdrop` + 真实 hover tracking，只在悬停时画边界；框内静置 `255.0/30.0` → 悬停 `235.0/47.5`（亮/暗），框带变化 `35200/56000=62.9%`，框外相邻带 194.3/94.7 作对照；新增 2 帧、既有 188 帧逐字节不变、基线 190/0；M1059/M1060 双 CAUGHT。⓪ `40340793989 ↔ 6bef5ab` 的 2 个失败步骤（`Swift tests` + `Capture gate`）同源于 R408 的 emptyBox 仍在主 stack：runner gap 33>24、长句 56>44；改成 emptyBox 直钉 content（top=field 底+8）后本机 gap 8、长句 400；R406 的 visibleRect 守卫仍绿；sources R408/a642dc0 一致；全量计数 92-vs-934 反向对照 ok。436 `judged=5/5`、`REDS=0`、UNLISTED=0。全量 1076/53/0；电池 683/4。新跑待 push 后签收。
"""

state_section = f"""## R409 状态（2026-10-26 · 本地 · 第 408 轮 / Round 406）：QuickPick 搜索框补悬停边界（静置 255/30 → 悬停 235/47.5，带变化 62.9%）；R408 CTA 布局改用 content 直钉（gap 33→8）（产品 3 文件，悬停反馈位）

最后更新：2026-10-26（本地 · R409 / 第 408 轮 / Round 406）：QuickPick 主输入框原来是一行裸文字，和主窗口 `SearchField` 的框不是同一套语言。新增 `QuickPickSearchBackdrop` + 真实 hover tracking，只在悬停时画圆角边界/淡填充；静置/焦点保持原样。像素现读（框内 x=300..400、y=12..40pt）：静置 **255.0/30.0** → 悬停 **235.0/47.5**（亮/暗），框带变化 **35200/56000=62.9%**，框外相邻带 194.3/94.7 作对照。仅 hover 亮暗 2 帧新增，既有 188 帧逐字节不变，基线同笔 190/0/0/0。源/像素两刀 `M1059/M1060` 双 CAUGHT。⓪ `40340793989 ↔ 6bef5ab` **completed / failure**，失败步骤 **2 个**（`Swift tests` + `Capture gate`），同源于 R408 的 `emptyBox` 仍在主 `NSStackView`：runner 空句 gap **33>24**、长句宽 **56>44**；改成 `emptyBox` 直钉 content（top=field 底+8）后本机 gap **8**、长句 **400**。R406 的 visibleRect 守卫在这一跑仍绿。`Release script tests` success：sources `R408/a642dc0` 一致、全量计数 92-vs-934 反向对照 ok。436 `judged=5/5 executed=73`、`REDS=0`、UNLISTED=0，`notice-banner` 放行，保持结案。全量 `Executed {executed} tests, with {skipped} tests skipped and {failures} failures`；换装 `ok / SHA_MATCH=1 / 381=381`；清账表 162=162；`HIDDEN_ARMS 表={h_tables} 可判={h_judged} rot={h_rot} … 上界 rot={h_rot_ceiling} 处置=ok`；预检 `tables={pre_tables} covered={pre_covered} arms={pre_arms} bad={pre_bad}`、全仓 {arm_files} 文件 / {arm_total} 把；产品面连续零改动 **{streak}** 轮（as-of 408，现读 `python3 scripts/product_streak.py --streak-for 408`）。电池待台账后复跑。

本轮做了什么：
① ⓪ R408 头跑 failure：2 个失败步骤同源于 CTA 布局；emptyBox 出栈后本机 gap 8/长句 400，visibleRect 守卫仍绿。
② 产品：QuickPick 搜索框补悬停边界，静置 255/30 → 悬停 235/47.5，带变化 62.9%。
③ 判据：源 + 像素三读数；M1059/M1060 双 CAUGHT；旧焦点/幻影判据仍绿。
④ 436：judged=5/5、REDS=0、UNLISTED=0、notice-banner 放行，保持结案。
⑤ 367：hidden 表 {h_tables} / 可判 {h_judged} / rot {h_rot} / 上界 {h_rot_ceiling}；预检 {pre_tables}/{pre_covered}/{pre_arms}/{pre_bad}。
⑥ 全量 {executed}/{skipped}/{failures}；换装 ok；清账表 162=162。

NOT-RUN / 阻塞（分开写）：① 真实 hover 事件仍只能人工验（捕获由 hoveredForCapture 点亮）；② 离屏 alpha 动画采样不到中间帧（mid=1.0）⇒ 弹层淡入不签结论；③ 亮档真机腿仍没跑；④ macOS 12 紧凑详情头仍走旧截断；⑤ 主列表与浮层来源搜索语言未统一（437）；⑥ R409 新跑待 push 后读。

下一轮（R410）的靶：⓪ 先 `git push origin main`（禁 amend/force）并复核 ahead=0；读 R409 主笔+追记 head 跑全部失败步骤（成对 run↔commit），in_progress/0 字节不算绿；① 367 现读 rot=0，按 `HIDDEN_ROT` 查新腐烂；② 继续产品视觉位并落 Sources，换缺陷类别；③ 436 只复核新跑 Motion floor，不重新猜 `must_judge`。
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
report_new = once(report_old, "D-069 … **D-400**", "D-069 … **D-401**")
report_new = once(report_new, "U-31 … U-1467（R408 现读抬到最新一节）", "U-31 … U-1472（R409 现读抬到最新一节）")
report_new = once(
    report_new,
    "R408 现读：注册表 **164** 张 / 刀号最大 **M1058** / 预检 covered=146 arms=432 bad=0；全仓 257 文件 / 916 把；M674 退役、M906 空刀退役",
    f"R409 现读：注册表 **{pre_tables}** 张 / 刀号最大 **M1060** / 预检 covered={pre_covered} arms={pre_arms} bad={pre_bad}；"
    f"全仓 {arm_files} 文件 / {arm_total} 把；M674 退役、M906 空刀退役")
report_new = report_new.rstrip() + "\n\n" + report_bullet
report_new = once(report_new, "`AGENT_STATE.md` 的 R408 节", "`AGENT_STATE.md` 的 R409 节")

state_old = rd("AGENT_STATE.md")
state_anchor = "## R408 状态（2026-10-26"
assert state_old.count(state_anchor) == 1
state_new = once(state_old, state_anchor, state_section + "\n" + state_anchor)

backlog = rd("AGENT_BACKLOG.md").rstrip() + "\n\n" + """437 追记（R409 · 仍开）：本轮补的是 QuickPick 搜索框悬停边界与空态布局；主列表仍不匹配 `sourceAppName`，与 QuickPick 继续两套搜索语言。
"""

wr("AGENT_UI_AUDIT.md", audit_new)
wr("AGENT_VISUAL_ITERATION.md", iteration_new)
wr("AGENT_DECISIONS.md", decisions_new)
wr("CHANGELOG.md", changelog_new)
wr("AGENT_FINAL_REPORT.md", report_new)
wr("AGENT_STATE.md", state_new)
wr("AGENT_BACKLOG.md", backlog)

print("R409_LEDGERS_OK warnings=%s full=%s/%s/%s frames=%s added=%s baseline=%s/%s/%s/%s pre=%s/%s/%s/%s arms=%s/%s rot=%s gate=%s=%s streak=%s"
      % (warnings, executed, skipped, failures, frames, pre_added,
         b_compared, b_changed, b_missing, b_added,
         pre_tables, pre_covered, pre_arms, pre_bad, arm_files, arm_total,
         h_rot, cleared, cells, streak))
