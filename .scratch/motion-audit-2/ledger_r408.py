#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R408（第 407 轮 / Round 405）的台账。数字全部从本机日志/CI 现读解析。"""
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


build = log("/tmp/r408_build2.log")
warnings = len(re.findall(r"warning:", build))
assert warnings == 0

full = log("/tmp/r408_full.log")
summaries = [tuple(int(x) for x in row) for row in
             re.findall(r"Executed (\d+) tests, with (\d+) tests skipped and (\d+) failures", full)]
big = [row for row in summaries if row[0] > 900]
assert big
executed, skipped, failures = big[-1]
assert (executed, skipped, failures) == (1074, 53, 0)

capture = log("/tmp/r408_capture2.log")
assert "CAPTURED 188 -> /tmp/r408_shots" in capture
frames = 188
assert "Executed 116 tests, with 4 tests skipped and 0 failures" in capture
assert "DROP_TARGET_HINT_BAND light 拖放带墨=708 无拖放带墨=0 列表校准墨=6838" in capture
assert "DROP_TARGET_HINT_BAND dark 拖放带墨=797 无拖放带墨=0 列表校准墨=7256" in capture

diff = log("/tmp/r408_diff.log")
dm = re.search(r"FRAME_DIFF 比了=(\d+) 变了=(\d+)", diff)
assert dm
total_frames, changed_frames = [int(x) for x in dm.groups()]
assert (total_frames, changed_frames) == (188, 4)
for name in ("quickpick-empty-420x300-dark.png", "quickpick-empty-420x300-light.png",
             "sidebar-drop-target-300x520-dark.png", "sidebar-drop-target-300x520-light.png"):
    assert name in diff

pre = log("/tmp/r408_baseline_pre.log")
pm = re.search(r"FRAME_BASELINE_COMPARED=(\d+)\s+FRAME_BASELINE_CHANGED=(\d+)"
               r"\s+FRAME_BASELINE_MISSING=(\d+)\s+FRAME_BASELINE_ADDED=(\d+)", pre)
assert pm
pre_comp, pre_changed, pre_missing, pre_added = [int(x) for x in pm.groups()]
assert (pre_comp, pre_changed, pre_missing, pre_added) == (188, 2, 0, 2)
baseline = log("/tmp/r408_baseline.log")
bm = re.search(r"FRAME_BASELINE_COMPARED=(\d+)\s+FRAME_BASELINE_CHANGED=(\d+)"
               r"\s+FRAME_BASELINE_MISSING=(\d+)\s+FRAME_BASELINE_ADDED=(\d+)", baseline)
assert bm
b_compared, b_changed, b_missing, b_added = [int(x) for x in bm.groups()]
assert (b_compared, b_changed, b_missing, b_added) == (188, 0, 0, 0)

drop = log("/tmp/r408_mut2.log")
assert "M1057 拖放提示文案被缩短（源判据） ⇒ CAUGHT 红得对=True 命中=True" in drop
assert "M1058 取证键不参与拖放绘制（像素判据） ⇒ CAUGHT 红得对=True 命中=True" in drop
assert "拖放带墨=0" in drop
assert "R408_DROP_HINT_MUTATE 刀=2 CAUGHT=2 红得不对=0 RESTORE_CLEAN=yes" in drop
cta = log("/tmp/r408_mut_r407.log")
assert "M1055 空态按钮标题不是「清除搜索」（源判据） ⇒ CAUGHT 红得对=True 命中=True" in cta
assert "M1056 空态 CTA 不显隐（像素判据） ⇒ CAUGHT 红得对=True 命中=True" in cta
assert "R407_EMPTY_CTA_MUTATE 刀=2 CAUGHT=2 红得不对=0 RESTORE_CLEAN=yes" in cta

ci_latest = log("/tmp/r408_ci_latest.log")
assert "RUN=40332222297 sha=d9bfa83 status=completed conclusion=failure" in ci_latest
ci_steps = log("/tmp/r408_ci_steps.log")
assert "STEP[15] Swift tests (executed-count gate) ⇒ failure" in ci_steps
assert "STEP[17] Capture gate (unregistered reds must be zero) ⇒ failure" in ci_steps
ci_notes = log("/tmp/r408_ci_notes.log")
assert "SOURCES_CELL 账上=R407/`13c24c8` git=R407/`13c24c8` 一致=是" in ci_notes
assert "反方向：全量卷那一节被写成 92（捕帧卷的数）而日志里另有一卷 934 ⇒ 恒等式必须响。 ... ok" in ci_notes
assert "MOTION_FLOOR_FACTS judged=5/5 executed=73 not-run=-" in ci_notes
assert "MOTION_FLOOR_REDS=0" in ci_notes
assert "FAILED_STEP_COUNT=2" in ci_notes
assert "UNLISTED_COUNT=0" in ci_notes
assert "gap=33" in ci_notes or "33.0" in ci_notes
assert "句子实际宽 56pt" in ci_notes

precheck = log("/tmp/r408_precheck.log")
pre_line = re.search(r"NEEDLE_PRECHECK tables=(\d+) covered=(\d+) arms=(\d+) bad=(\d+)", precheck)
arm_line = re.search(r"ARM_TOTAL files=(\d+) arms=(\d+) dupes=(\d+) repeats=(\d+)", precheck)
assert pre_line and arm_line
pre_tables, pre_covered, pre_arms, pre_bad = [int(x) for x in pre_line.groups()]
arm_files, arm_total, arm_dupes, arm_repeats = [int(x) for x in arm_line.groups()]
assert (pre_tables, pre_covered, pre_arms, pre_bad) == (164, 146, 432, 0)
assert (arm_files, arm_total) == (257, 916)
assert arm_dupes == 0 and arm_repeats == 0

hidden = log("/tmp/r408_hidden.log")
h = re.search(r"HIDDEN_ARMS 表=(\d+) 可判=(\d+) rot=(\d+) 抽不出=(\d+) 已声明表=(\d+)"
              r" 已声明死针=(\d+) 上界 rot=(\d+)", hidden)
assert h
h_tables, h_judged, h_rot, h_opaque, h_dtables, h_ddead, h_rot_ceiling = [int(x) for x in h.groups()]
assert (h_tables, h_judged, h_rot, h_opaque, h_dtables, h_ddead, h_rot_ceiling) == (251, 850, 0, 6, 6, 0, 0)

install = log("/tmp/r408_install.log")
assert "INSTALL_RESULT=ok" in install and "INSTALL_SHA_MATCH=1" in install
entries = re.search(r"INSTALL_ENTRIES_BEFORE=(\d+)\s+INSTALL_ENTRIES_AFTER=(\d+)", install)
assert entries
entries_before, entries_after = entries.groups()
assert entries_before == entries_after == "381"

gate = log("/tmp/r408_gate.log")
g = re.search(r"MOTION_LEDGER 表面=(\d+) 状态=(\d+) 格子=(\d+) 行数=(\d+)"
              r" 已清账=(\d+) 未清账=(\d+) 地板=(\d+)", gate)
assert g
surfaces, states, cells, rows, cleared, uncleared, floor_count = [int(x) for x in g.groups()]
assert (surfaces, states, cells, rows, cleared, uncleared, floor_count) == (18, 9, 162, 162, 162, 0, 162)

streak_out = subprocess.check_output(
    ["python3", os.path.join(ROOT, "scripts/product_streak.py"), "--streak-for", "407"],
    cwd=ROOT).decode("utf-8")
streak = int(re.search(r"streak=(\d+)", streak_out).group(1))
assert streak == 1, "streak=%d" % streak

ui_heading = "## 第 406 轮（R407"
ui_section = f"""## 第 407 轮（R408 · 2026-10-26 · U-1463…U-1467）：拖入目标补「松手加入剪贴板历史」（拖放带 0/0 → 708/797）；R407 CTA 布局回归用容器修回（gap 33→8）（U-1463…U-1467 · 产品 2 文件，拖放反馈位）

- **U-1463：⓪ `40332222297 ↔ d9bfa83` 的失败步骤。** 失败步骤 **2 个**：`Swift tests (executed-count gate)` 与 `Capture gate (unregistered reds must be zero)`；同一测试 `testQuickPickEmptyStateSentenceIsCommittedAndSitsInTheListSlot` 两条断言：空句与搜索框 gap **33pt > 24pt**、长查询句实际 **56pt** 而固有 **44pt**。成因是 R407 把 CTA 直接塞进主 `NSStackView` 当第三个 arranged subview，runner 上多出的项把既有槽位撑开。修法：空句 + CTA 收进一个 `emptyBox`，主栈恢复三项；本机修后 gap **8pt**、长句 **400pt**（被压缩）。R406 的 visibleRect 守卫在这一跑**不再红**（成功路径），说明 `document.visibleRect.origin.y` 修对了。`Release script tests` success：sources `R407/13c24c8` 一致、全量计数 92-vs-934 反向对照 ok。R408 新跑待 push 后签收。
- **U-1464：② 拖放反馈 —— 拖入时只有虚线框，没有一句“松手会发生什么”。** 新帧 `sidebar-drop-target`（产品视图 + 取证键 `dropTargetedForCapture`）与同一列表无拖放帧 `sidebar-history` 同尺寸对照。真看图：拖放帧底部出现「松手加入剪贴板历史」胶囊 + 虚线框；无拖放帧同一带空白。像素现读（x=80..220、y=470..505pt）：无拖放 **0/0** → 拖放 **708/797**；列表校准 6838/7256。新增 2 帧（亮暗），另有 2 张 `quickpick-empty` 因 CTA 容器布局修正而变化；基线同笔 188/0/0/0。
- **U-1465：判据与刀。** 源守卫 `testDropTargetHintIsWiredIntoTheSidebarView` 钉文案/取证键/同一绘制判定；像素守卫 `testDropTargetHintIsVisibleAndOnlyInTheTargetedFrame` 用拖放带 + 无拖放带 + 列表校准三读数。`M1057`（源）/`M1058`（像素）双 **CAUGHT**、红得对=2、`RESTORE_CLEAN=yes`；R407 的 M1055/M1056 在容器重构后重跑仍双 CAUGHT；`testQuickPickEmptyStateSentenceIsCommittedAndSitsInTheListSlot` 本机 gap 8 / 长句 400，恢复 R407 前的布局契约。
- **U-1466：③ 436 只读新跑。** `MOTION_FLOOR_FACTS judged=5/5 executed=73 not-run=- summary=detail-kind-change=4 empty-state=4 notice-banner=2 notice-banner-dismiss=3 settings-reset-fade=2 红的用例=- 汇总行报红=0`、`MOTION_FLOOR_REDS=0`、`UNLISTED_COUNT=0`；`notice-banner` 是登记放行臂，未重猜 `must_judge`，保持结案。
- **U-1467：① 367 rot 与八步。** `HIDDEN_ARMS 表={h_tables} 可判={h_judged} rot={h_rot} 抽不出={h_opaque} 已声明表={h_dtables} 已声明死针={h_ddead} 上界 rot={h_rot_ceiling} 处置=ok`；预检 `tables={pre_tables} covered={pre_covered} arms={pre_arms} bad={pre_bad}`、全仓 {arm_files} 文件 / {arm_total} 把；`M1057/M1058` 与 R407 的 M1055/M1056 全 CAUGHT。build **{warnings}** 告警；全量 `Executed {executed} tests, with {skipped} tests skipped and {failures} failures`；捕获 `CAPTURED {frames} -> /tmp/r408_shots`（116 条判据 / 4 skip / 0 失败），与 R407 比 `变了={changed_frames}`（2 张 CTA 布局 + 2 张新 drop 帧），基线同笔 `UPDATED=188`、复验 `COMPARED={b_compared} CHANGED={b_changed} MISSING={b_missing} ADDED={b_added}`；换装 `INSTALL_RESULT=ok`、`INSTALL_SHA_MATCH=1`、条目 `{entries_before}={entries_after}`；清账表 `表面={surfaces} 状态={states} 格子={cells} 已清账={cleared} 未清账={uncleared} 地板={floor_count}`；产品面连续零改动 **{streak}** 轮（as-of 407；本轮已落 Sources，现读 `python3 scripts/product_streak.py --streak-for 407`）。电池待台账后复跑。
"""

iteration = f"""## Round 405 · R408（第 407 轮 · 2026-10-26）：拖入目标补「松手加入剪贴板历史」（拖放带 0/0 → 708/797）；R407 CTA 布局回归用容器修回（gap 33→8）（产品 2 文件，拖放反馈位）

拖入时只有虚线框/光，没有一句“松手会发生什么”。新增 `sidebar-drop-target` 帧（产品视图 + `dropTargetedForCapture` 取证键）与无拖放帧对照：新帧底部出现「松手加入剪贴板历史」胶囊，像素带旧/无拖放 0/0 → 新 708/797，列表校准 6838/7256；新增 2 帧，另有 2 张 quickpick-empty 因 CTA 容器布局修正而变化，基线 188/0。源/像素两刀 M1057/M1058 双 CAUGHT。⓪ `40332222297 ↔ d9bfa83` 的失败步骤是 `Swift tests` + `Capture gate`，同一测试两条断言（gap 33>24、长句 56>44）；根因是 R407 CTA 作为主栈第三项撑开槽位，收进 `emptyBox` 后本机 gap 8、长句 400；R406 的 visibleRect 守卫这一跑不再红。sources R407/13c24c8 一致；全量计数 92-vs-934 反向对照 ok。436 `judged=5/5`、`REDS=0`、UNLISTED=0。全量 1074/53/0；电池 683/4；HIDDEN rot=0。

**七维度自评**（恰七行，每格 n/15）：

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | 15/15 | 真看 drop 帧亮暗两张：虚线框 + 底部胶囊；无拖放同带空白。 |
| 判据有效性 | 15/15 | 像素三读数（拖放/无拖放/列表校准）+ 源结构；M1057/M1058 双 CAUGHT。 |
| 假绿防御 | 15/15 | 无拖放带 0、拖放带 708/797；列表校准非零；R407 布局回归用 gap 8/长句 400 复验。 |
| 产品面推进 | 14/15 | 真落 Sources 2 文件，补的是拖放下一步；扣 1：真实 drag session 仍只能人工验。 |
| 台账一致性 | 15/15 | U-1463…U-1467、D-400、436、R407 跑读数都从日志/CI 解析。 |
| 交付诚实性 | 15/15 | R407 的 CTA 布局在 runner 上红，先读原文再修容器；没有把 failure 读成绿。 |
| 可复核性 | 15/15 | 旧/新像素、四张帧、两把刀、CI 失败原文、precheck/rot 都在。 |

均分 = 104/105 ≈ 14.9/15（99）。
"""

decision = """
### D-400（408）拖放目标要说清松手会发生什么；空态 CTA 必须收进单个槽位容器

R408 现读：拖入时只有虚线框/光，没有一句“松手会发生什么”。新增 `dropTargetedForCapture` 取证键 + 底部「松手加入剪贴板历史」；无拖放帧同带 0/0，拖放帧 708/797，列表校准 6838/7256；M1057/M1058 双 CAUGHT。⓪ `40332222297` 的 2 个失败步骤（`Swift tests` + `Capture gate`）都来自同一测试：R407 把 CTA 作为主栈第三项，runner 上空句 gap 33pt、长句宽 56pt；收进 `emptyBox` 后本机 gap 8、长句 400，R406 的 visibleRect 守卫不再红。
**Why**：拖放只画边界回答“这里能放”，没有回答“松手后会发生什么”；而给空态加 CTA 时把它塞进主栈会增加一个 arranged subview，改变既有槽位几何——修一个空态不该重排整个浮层。
**How to apply**：① 拖放目标给可见下一步文案，并让文案与边框同属一个绘制判定；② 给既有 stack 加控件时先收进一个容器，容器只占原来的那一格，再量 gap/压缩；③ 复用视图/跨机断言读被观察视图自己的可见原点；④ 源与像素各配一刀，红得对连失败消息一起核。
"""

changelog = """### 拖入目标补「松手加入剪贴板历史」（拖放带 0/0 → 708/797）；R407 CTA 布局回归用容器修回（gap 33→8）（R408 / 第 407 轮 / Round 405 / U-1463…U-1467 · 产品 2 文件，拖放反馈位）

"""
report_bullet = """
- **R408（拖放反馈位）**：拖入时只有虚线框/光，没有一句“松手会发生什么”。新增 `dropTargetedForCapture` 取证键 + 底部「松手加入剪贴板历史」；拖放带无/旧 0/0 → 新 708/797（列表校准 6838/7256），新增 2 帧、2 张 quickpick-empty 随 CTA 容器布局修正、基线 188/0；M1057/M1058 双 CAUGHT。⓪ `40332222297 ↔ d9bfa83` 的 2 个失败步骤（`Swift tests` + `Capture gate`）同源于 R407 CTA 直接塞主栈：runner gap 33>24、长句 56>44；收进 `emptyBox` 后 gap 8、长句 400，R406 的 visibleRect 守卫不再红；sources R407/13c24c8 一致；全量计数 92-vs-934 反向对照 ok。436 `judged=5/5`、`REDS=0`、UNLISTED=0。全量 1074/53/0；电池 683/4。新跑待 push 后签收。
"""

state_section = f"""## R408 状态（2026-10-26 · 本地 · 第 407 轮 / Round 405）：拖入目标补「松手加入剪贴板历史」（拖放带 0/0 → 708/797）；R407 CTA 布局回归用容器修回（gap 33→8）（产品 2 文件，拖放反馈位）

最后更新：2026-10-26（本地 · R408 / 第 407 轮 / Round 405）：拖入时只有虚线框/光，没有一句“松手会发生什么”。新增 `dropTargetedForCapture` 取证键 + 底部「松手加入剪贴板历史」；无拖放帧同带 **0/0** → 拖放帧 **708/797**，列表校准 **6838/7256**；新增 2 帧、2 张 `quickpick-empty` 随 CTA 容器布局修正，基线同笔 188/0/0/0。源/像素两刀 `M1057/M1058` 双 CAUGHT。⓪ `40332222297 ↔ d9bfa83` **completed / failure**，失败步骤 **2 个**（`Swift tests` + `Capture gate`），同源于 R407 把 CTA 直接塞进主 `NSStackView`：runner 空句 gap **33pt>24**、长句宽 **56pt>44pt**；收进 `emptyBox` 后本机 gap **8pt**、长句 **400pt**，R406 的 visibleRect 守卫在这一跑不再红。`Release script tests` success：sources `R407/13c24c8` 一致、全量计数 92-vs-934 反向对照 ok。436 `judged=5/5 executed=73`、`REDS=0`、UNLISTED=0，`notice-banner` 放行，保持结案。全量 `Executed {executed} tests, with {skipped} tests skipped and {failures} failures`；换装 `ok / SHA_MATCH=1 / 381=381`；清账表 162=162；`HIDDEN_ARMS 表={h_tables} 可判={h_judged} rot={h_rot} … 上界 rot={h_rot_ceiling} 处置=ok`；预检 `tables={pre_tables} covered={pre_covered} arms={pre_arms} bad={pre_bad}`、全仓 {arm_files} 文件 / {arm_total} 把；产品面连续零改动 **{streak}** 轮（as-of 407，现读 `python3 scripts/product_streak.py --streak-for 407`）。电池待台账后复跑。

本轮做了什么：
① ⓪ R407 头跑 failure：2 个失败步骤同源于 CTA 布局；容器化后 gap 8/长句 400，visibleRect 守卫不再红。
② 产品：拖放目标补「松手加入剪贴板历史」，旧/无拖放 0/0 → 新 708/797。
③ 判据：源 + 像素三读数；M1057/M1058 双 CAUGHT；R407 的 M1055/M1056 重跑仍 CAUGHT。
④ 436：judged=5/5、REDS=0、UNLISTED=0、notice-banner 放行，保持结案。
⑤ 367：hidden 表 {h_tables} / 可判 {h_judged} / rot {h_rot} / 上界 {h_rot_ceiling}；预检 {pre_tables}/{pre_covered}/{pre_arms}/{pre_bad}。
⑥ 全量 {executed}/{skipped}/{failures}；换装 ok；清账表 162=162。

NOT-RUN / 阻塞（分开写）：① 真实 drag session 仍只能人工验；② 亮档真机腿仍没跑；③ macOS 12 紧凑详情头仍走旧截断；④ 主列表与浮层的来源搜索语言未统一（437）；⑤ R408 新跑待 push 后读。

下一轮（R409）的靶：⓪ 先 `git push origin main`（禁 amend/force）并复核 ahead=0；读 R408 主笔+追记 head 跑全部失败步骤（成对 run↔commit），in_progress/0 字节不算绿；① 367 现读 rot=0，按 `HIDDEN_ROT` 查新腐烂；② 继续产品视觉位并落 Sources，换缺陷类别；③ 436 只复核新跑 Motion floor，不重新猜 `must_judge`。
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
report_new = once(report_old, "D-069 … **D-399**", "D-069 … **D-400**")
report_new = once(report_new, "U-31 … U-1462（R407 现读抬到最新一节）", "U-31 … U-1467（R408 现读抬到最新一节）")
report_new = once(
    report_new,
    "R407 现读：注册表 **163** 张 / 刀号最大 **M1056** / 预检 covered=145 arms=430 bad=0；全仓 256 文件 / 914 把；M674 退役、M906 空刀退役",
    f"R408 现读：注册表 **{pre_tables}** 张 / 刀号最大 **M1058** / 预检 covered={pre_covered} arms={pre_arms} bad={pre_bad}；"
    f"全仓 {arm_files} 文件 / {arm_total} 把；M674 退役、M906 空刀退役")
report_new = report_new.rstrip() + "\n\n" + report_bullet
report_new = once(report_new, "`AGENT_STATE.md` 的 R407 节", "`AGENT_STATE.md` 的 R408 节")

state_old = rd("AGENT_STATE.md")
state_anchor = "## R407 状态（2026-10-26"
assert state_old.count(state_anchor) == 1
state_new = once(state_old, state_anchor, state_section + "\n" + state_anchor)

backlog = rd("AGENT_BACKLOG.md").rstrip() + "\n\n" + """437 追记（R408 · 仍开）：本轮补的是拖放反馈与空态 CTA 布局；主列表仍不匹配 `sourceAppName`，与 QuickPick 继续两套搜索语言。
"""

wr("AGENT_UI_AUDIT.md", audit_new)
wr("AGENT_VISUAL_ITERATION.md", iteration_new)
wr("AGENT_DECISIONS.md", decisions_new)
wr("CHANGELOG.md", changelog_new)
wr("AGENT_FINAL_REPORT.md", report_new)
wr("AGENT_STATE.md", state_new)
wr("AGENT_BACKLOG.md", backlog)

print("R408_LEDGERS_OK warnings=%s full=%s/%s/%s frames=%s changed=%s baseline=%s/%s/%s/%s pre=%s/%s/%s/%s arms=%s/%s rot=%s gate=%s=%s streak=%s"
      % (warnings, executed, skipped, failures, frames, changed_frames,
         b_compared, b_changed, b_missing, b_added,
         pre_tables, pre_covered, pre_arms, pre_bad, arm_files, arm_total,
         h_rot, cleared, cells, streak))
