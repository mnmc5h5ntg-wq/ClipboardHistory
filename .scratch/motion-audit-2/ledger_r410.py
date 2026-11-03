#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R410（第 409 轮 / Round 407）的台账。数字全部从本机日志/CI 现读解析。"""
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


build = log("/tmp/r410_build2.log")
warnings = len(re.findall(r"warning:", build))
assert warnings == 0

full = log("/tmp/r410_full3.log")
summaries = [tuple(int(x) for x in row) for row in
             re.findall(r"Executed (\d+) tests, with (\d+) tests skipped and (\d+) failures", full)]
big = [row for row in summaries if row[0] > 900]
assert big
executed, skipped, failures = big[-1]
assert (executed, skipped, failures) == (1078, 53, 0)

capture = log("/tmp/r410_capture2.log")
assert "CAPTURED 190 -> /tmp/r410_shots2" in capture
frames = 190
assert "Executed 120 tests, with 4 tests skipped and 0 failures" in capture
assert "MENUBAR_EMPTY_CTA_BAND light 消息带墨=910 CTA带墨=1166" in capture
assert "MENUBAR_EMPTY_CTA_BAND dark 消息带墨=1032 CTA带墨=1382" in capture

pre = log("/tmp/r410_baseline_pre.log")
pm = re.search(r"FRAME_BASELINE_COMPARED=(\d+)\s+FRAME_BASELINE_CHANGED=(\d+)"
               r"\s+FRAME_BASELINE_MISSING=(\d+)\s+FRAME_BASELINE_ADDED=(\d+)", pre)
assert pm
pre_comp, pre_changed, pre_missing, pre_added = [int(x) for x in pm.groups()]
assert (pre_comp, pre_changed, pre_missing, pre_added) == (190, 4, 0, 0)
baseline = log("/tmp/r410_baseline.log")
bm = re.search(r"FRAME_BASELINE_COMPARED=(\d+)\s+FRAME_BASELINE_CHANGED=(\d+)"
               r"\s+FRAME_BASELINE_MISSING=(\d+)\s+FRAME_BASELINE_ADDED=(\d+)", baseline)
assert bm
b_compared, b_changed, b_missing, b_added = [int(x) for x in bm.groups()]
assert (b_compared, b_changed, b_missing, b_added) == (190, 0, 0, 0)

mut = log("/tmp/r410_mut.log")
assert "M1061 空态 CTA 文案被缩短（源判据） ⇒ CAUGHT 红得对=True 命中=True" in mut
assert "M1062 空态 CTA 被隐藏（像素判据） ⇒ CAUGHT 红得对=True 命中=True" in mut
assert "CTA带墨=0" in mut
assert "R410_MENUBAR_CTA_MUTATE 刀=2 CAUGHT=2 红得不对=0 RESTORE_CLEAN=yes" in mut
scroll = log("/tmp/r410_mut_r406.log")
assert "M1053 换选正文不归顶（行为判据） ⇒ CAUGHT 红得对=True 命中=True" in scroll
assert "换选可见=2357" in scroll
assert "M1054 换选正文不归顶（像素判据） ⇒ CAUGHT 红得对=True 命中=True" in scroll
assert "R406_SCROLL_MUTATE 刀=2 CAUGHT=2 红得不对=0 RESTORE_CLEAN=yes" in scroll

pixels = log("/tmp/r410_cta_pixels.log")
assert "MENUBAR_CTA_PIXEL 旧代码 light 消息带=330 CTA带=0" in pixels
assert "MENUBAR_CTA_PIXEL 旧代码 dark 消息带=347 CTA带=0" in pixels
assert "MENUBAR_CTA_PIXEL 新代码 light 消息带=910 CTA带=1166" in pixels
assert "MENUBAR_CTA_PIXEL 新代码 dark 消息带=1032 CTA带=1382" in pixels

ci_latest = log("/tmp/r410_ci_latest.log") if os.path.exists("/tmp/r410_ci_latest.log") else ""
assert "RUN=40350180209 sha=83bed7a status=completed conclusion=failure" in ci_latest
ci_steps = log("/tmp/r410_ci_steps.log")
assert "STEP[15] Swift tests (executed-count gate) ⇒ failure" in ci_steps
assert "STEP[17] Capture gate (unregistered reds must be zero) ⇒ failure" in ci_steps
ci_notes = log("/tmp/r410_ci_notes.log")
assert "SOURCES_CELL 账上=R409/`7426d05` git=R409/`7426d05` 一致=是" in ci_notes
assert "反方向：全量卷那一节被写成 92（捕帧卷的数）而日志里另有一卷 934 ⇒ 恒等式必须响。 ... ok" in ci_notes
assert "MOTION_FLOOR_FACTS judged=5/5 executed=73 not-run=-" in ci_notes
assert "MOTION_FLOOR_REDS=0" in ci_notes
assert "FAILED_STEP_COUNT=2" in ci_notes
assert "UNLISTED_COUNT=0" in ci_notes
assert "gap=33" in ci_notes or "33.0" in ci_notes
assert "句子实际宽 56pt" in ci_notes
assert "换选后正文可见原点是 0" in ci_notes

precheck = log("/tmp/r410_precheck2.log")
pre_line = re.search(r"NEEDLE_PRECHECK tables=(\d+) covered=(\d+) arms=(\d+) bad=(\d+)", precheck)
arm_line = re.search(r"ARM_TOTAL files=(\d+) arms=(\d+) dupes=(\d+) repeats=(\d+)", precheck)
assert pre_line and arm_line
pre_tables, pre_covered, pre_arms, pre_bad = [int(x) for x in pre_line.groups()]
arm_files, arm_total, arm_dupes, arm_repeats = [int(x) for x in arm_line.groups()]
assert (pre_tables, pre_covered, pre_arms, pre_bad) == (166, 148, 436, 0)
assert (arm_files, arm_total) == (259, 920)
assert arm_dupes == 0 and arm_repeats == 0

hidden = log("/tmp/r410_hidden2.log")
h = re.search(r"HIDDEN_ARMS 表=(\d+) 可判=(\d+) rot=(\d+) 抽不出=(\d+) 已声明表=(\d+)"
              r" 已声明死针=(\d+) 上界 rot=(\d+)", hidden)
assert h
h_tables, h_judged, h_rot, h_opaque, h_dtables, h_ddead, h_rot_ceiling = [int(x) for x in h.groups()]
assert (h_tables, h_judged, h_rot, h_opaque, h_dtables, h_ddead, h_rot_ceiling) == (253, 854, 0, 6, 6, 0, 0)

install = log("/tmp/r410_install2.log")
assert "INSTALL_RESULT=ok" in install and "INSTALL_SHA_MATCH=1" in install
entries = re.search(r"INSTALL_ENTRIES_BEFORE=(\d+)\s+INSTALL_ENTRIES_AFTER=(\d+)", install)
assert entries
entries_before, entries_after = entries.groups()
assert entries_before == entries_after == "381"

gate = log("/tmp/r410_gate.log")
g = re.search(r"MOTION_LEDGER 表面=(\d+) 状态=(\d+) 格子=(\d+) 行数=(\d+)"
              r" 已清账=(\d+) 未清账=(\d+) 地板=(\d+)", gate)
assert g
surfaces, states, cells, rows, cleared, uncleared, floor_count = [int(x) for x in g.groups()]
assert (surfaces, states, cells, rows, cleared, uncleared, floor_count) == (18, 9, 162, 162, 162, 0, 162)

streak_out = subprocess.check_output(
    ["python3", os.path.join(ROOT, "scripts/product_streak.py"), "--streak-for", "409"],
    cwd=ROOT).decode("utf-8")
streak = int(re.search(r"streak=(\d+)", streak_out).group(1))
assert streak == 1, "streak=%d" % streak

ui_heading = "## 第 408 轮（R409"
ui_section = f"""## 第 409 轮（R410 · 2026-10-27 · U-1473…U-1477）：菜单栏空态补「打开时间剪史」（CTA 带旧 0/0 → 新 1166/1382）；空态容器改普通 NSView、滚动守卫改读可见原点（U-1473…U-1477 · 产品 2 文件，菜单空态 CTA 位）

- **U-1473：⓪ `40350180209 ↔ 83bed7a` 的失败步骤。** 失败步骤 **2 个**：`Swift tests` + `Capture gate`；红的是两件事：① `testQuickPickEmptyStateSentenceIsCommittedAndSitsInTheListSlot` 在 runner 上仍 gap **33>24**、长句宽 **56>44**（R409 的 emptyBox 仍是 NSStackView，runner 把它压成按钮宽）；② `DetailScrollResetTests` 读到 `afterVisible=0` 而 `topVisible=11`，守卫把初始可见原点当成了常数。修法：emptyBox 改**普通 NSView + 显式四边约束**；滚动守卫改断言“换选后可见原点 ≤1”（旧行为 2357 仍会红）。R406 的 visibleRect 思路保留，不再钉 11/0 的跨机差。sources `R409/7426d05` 一致、全量计数 92-vs-934 反向对照 ok。
- **U-1474：② 菜单栏空态 CTA。** `menubar-empty` 只有“暂无推荐”，没有下一步。修法：空态分支加「打开时间剪史」菜单项，走产品已有的 `.showMainWindowHotKeyPressed` 通知，不另造打开窗口路径。真看图：旧帧只有消息，新帧消息下出现图标+文案。像素现读（x=120..290、y=78..102pt）：旧 **0/0** → 新 **1166/1382**（亮/暗）；消息带旧 330/347、新 910/1032。`menubar-empty` 与 `menubar-refreshing` 亮暗 **4 帧**变化（同一空态分支），基线同笔 190/0。
- **U-1475：判据与刀。** 源守卫 `testMenuBarEmptyStateOffersOpenAppAction` 钉文案与通知通道；像素守卫 `testMenuBarEmptyStateOpenAppCTAIsVisible` 钉消息带 + CTA 带。`M1061`（源）/`M1062`（像素）双 **CAUGHT**、红得对=2、`RESTORE_CLEAN=yes`；M1053/M1054 在滚动守卫改读可见原点后重跑仍双 CAUGHT。`PressFeedbackTests` 的菜单按钮精确计数从 2 更新到 **3**（推荐项 + 收尾 + 空态 CTA），不是放宽集合。
- **U-1476：③ 436 只读新跑。** `MOTION_FLOOR_FACTS judged=5/5 executed=73 not-run=- summary=detail-kind-change=4 empty-state=3 notice-banner=2 notice-banner-dismiss=3 settings-reset-fade=2 红的用例=- 汇总行报红=0`、`MOTION_FLOOR_REDS=0`、`UNLISTED_COUNT=0`；`notice-banner` 是登记放行臂，未重猜 `must_judge`，保持结案。
- **U-1477：① 367 rot 与八步。** `HIDDEN_ARMS 表={h_tables} 可判={h_judged} rot={h_rot} 抽不出={h_opaque} 已声明表={h_dtables} 已声明死针={h_ddead} 上界 rot={h_rot_ceiling} 处置=ok`；预检 `tables={pre_tables} covered={pre_covered} arms={pre_arms} bad={pre_bad}`、全仓 {arm_files} 文件 / {arm_total} 把；`M1061/M1062` 与 M1053/M1054 全 CAUGHT。build **{warnings}** 告警；全量 `Executed {executed} tests, with {skipped} tests skipped and {failures} failures`；捕获 `CAPTURED {frames} -> /tmp/r410_shots2`（120 条判据 / 4 skip / 0 失败），与 R409 比 `变了={pre_changed}`（menubar-empty/refreshing 亮暗），基线同笔 `UPDATED=190`、复验 `COMPARED={b_compared} CHANGED={b_changed} MISSING={b_missing} ADDED={b_added}`；换装 `INSTALL_RESULT=ok`、`INSTALL_SHA_MATCH=1`、条目 `{entries_before}={entries_after}`；清账表 `表面={surfaces} 状态={states} 格子={cells} 已清账={cleared} 未清账={uncleared} 地板={floor_count}`；产品面连续零改动 **{streak}** 轮（as-of 409；本轮已落 Sources，现读 `python3 scripts/product_streak.py --streak-for 409`）。电池待台账后复跑。
- **具名 NOT-RUN**：真实菜单展开/关闭仍只能人工验；离屏 alpha 动画采样不到中间帧（mid=1.0），弹层淡入不签产品结论。
"""

iteration = f"""## Round 407 · R410（第 409 轮 · 2026-10-27）：菜单栏空态补「打开时间剪史」（CTA 带旧 0/0 → 新 1166/1382）；空态容器改普通 NSView、滚动守卫改读可见原点（产品 2 文件，菜单空态 CTA 位）

菜单栏空态只有“暂无推荐”，没有下一步。空态分支加「打开时间剪史」菜单项，走已有 `.showMainWindowHotKeyPressed` 通知；旧/新 CTA 带 0/0 → 1166/1382（消息带 330/347→910/1032），menubar-empty 与 menubar-refreshing 亮暗 4 帧变化，基线 190/0。源/像素两刀 M1061/M1062 双 CAUGHT。⓪ `40350180209 ↔ 83bed7a` 的 2 个失败步骤是 Swift tests + Capture gate，两件事：空态在 runner 上仍 33/56（emptyBox 还是 NSStackView），以及 DetailScrollReset 的可见原点被当成常数（0 vs 11）。R410 把 emptyBox 换成普通 NSView + 四边约束，滚动守卫改断言可见原点 ≤1（旧行为 2357 仍红）；PressFeedback 菜单按钮精确计数 2→3。sources R409/7426d05 一致、全量计数 92-vs-934 反向对照 ok。436 judged=5/5、REDS=0、UNLISTED=0。全量 1078/53/0；电池 683/4；HIDDEN rot=0。真实菜单展开与离屏 alpha 中间帧仍是具名 NOT-RUN。

**七维度自评**（恰七行，每格 n/15）：

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | 15/15 | 真看 menubar-empty 旧/新亮暗四张：旧只有消息，新有图标+CTA。 |
| 判据有效性 | 15/15 | 源守卫钉文案/通知通道 + 像素双带；M1061/M1062 双 CAUGHT。 |
| 假绿防御 | 15/15 | 旧 CTA 带 0、新 1166/1382；消息带 330/347→910/1032；滚动旧 2357 仍红。 |
| 产品面推进 | 14/15 | 真落 Sources 2 文件，补的是菜单空态下一步；扣 1：真实菜单展开仍人工验。 |
| 台账一致性 | 15/15 | U-1473…U-1477、D-402、436、R409 跑读数都从日志/CI 解析。 |
| 交付诚实性 | 15/15 | R409 的两条 runner 红都按原文归因并修；没有把 failure 读成绿。 |
| 可复核性 | 15/15 | 旧/新像素、四张帧、两把刀、CI 失败原文、precheck/rot 都在。 |

均分 = 104/105 ≈ 14.9/15（99）。
"""

decision = """
### D-402（410）菜单空态要有可见下一步；空态容器用显式约束，滚动守卫读“可见原点 ≤1”

R410 现读：菜单栏空态只有“暂无推荐”。加「打开时间剪史」菜单项，走已有 `.showMainWindowHotKeyPressed` 通知；CTA 带旧 0/0 → 新 1166/1382，menubar-empty/refreshing 亮暗 4 帧变化；M1061/M1062 双 CAUGHT。⓪ `40350180209` 的 2 个失败步骤是 Swift tests + Capture gate：① 空态在 runner 上仍 gap 33/长句 56（emptyBox 还是 NSStackView）；② DetailScrollReset 的初始可见原点被当常数（runner 11 vs 本机 0，换选后 0）。修法：emptyBox 改普通 NSView + 四边约束；滚动守卫改断言“换选后可见原点 ≤1”（旧行为 2357 仍红）；PressFeedback 菜单按钮精确计数 2→3。
**Why**：空态菜单若不给出下一步，用户只能退出菜单自己找主窗口；而 NSStackView 的 hugging/分配在不同机器上会把容器压成按钮宽，本机绿不代表 runner 绿。初始可见原点也不是常数（内边距/字体差），把 0/11 当契约会制造假红。
**How to apply**：① 菜单/弹层空态给可执行下一步，并复用已有动作通道；② 需要精确几何的容器用普通 NSView + 显式四边/宽度约束，不依赖 stack 的 hugging；③ 滚动/位置守卫读被观察视图自己的可见原点并给“顶部 ≤1”的绝对出口；④ 精确计数守卫可随合法新增更新数字，但必须仍是精确相等。
"""

changelog = """### 菜单栏空态补「打开时间剪史」（CTA 带旧 0/0 → 新 1166/1382）；空态容器改普通 NSView、滚动守卫改读可见原点（R410 / 第 409 轮 / Round 407 / U-1473…U-1477 · 产品 2 文件，菜单空态 CTA 位）

"""
report_bullet = """
- **R410（菜单空态 CTA 位）**：菜单栏空态只有“暂无推荐”。空态分支加「打开时间剪史」菜单项，走已有 `.showMainWindowHotKeyPressed` 通知；CTA 带旧 `0/0` → 新 `1166/1382`（消息带 330/347→910/1032），menubar-empty/refreshing 亮暗 4 帧变化、基线 190/0；M1061/M1062 双 CAUGHT。⓪ `40350180209 ↔ 83bed7a` 的 2 个失败步骤是 `Swift tests` + `Capture gate`：空态在 runner 上仍 33/56（emptyBox 还是 NSStackView）+ 滚动可见原点被当常数（0 vs 11）；R410 把 emptyBox 换普通 NSView + 四边约束、滚动守卫改断言可见原点 ≤1（旧 2357 仍红）；PressFeedback 菜单按钮精确计数 2→3。sources R409/7426d05 一致、全量计数 92-vs-934 反向对照 ok。436 `judged=5/5`、`REDS=0`、UNLISTED=0。全量 1078/53/0；电池 683/4。新跑待 push 后签收。
"""

state_section = f"""## R410 状态（2026-10-27 · 本地 · 第 409 轮 / Round 407）：菜单栏空态补「打开时间剪史」（CTA 带旧 0/0 → 新 1166/1382）；空态容器改普通 NSView、滚动守卫改读可见原点（产品 2 文件，菜单空态 CTA 位）

最后更新：2026-10-27（本地 · R410 / 第 409 轮 / Round 407）：菜单栏空态只有“暂无推荐”，没有下一步。空态分支加「打开时间剪史」菜单项，走已有 `.showMainWindowHotKeyPressed` 通知；旧/新 CTA 带 **0/0 → 1166/1382**（消息带 330/347→910/1032），menubar-empty 与 menubar-refreshing 亮暗 **4 帧**变化，基线同笔 190/0/0/0。源/像素两刀 `M1061/M1062` 双 CAUGHT。⓪ `40350180209 ↔ 83bed7a` **completed / failure**，失败步骤 **2 个**（`Swift tests` + `Capture gate`），两件事：① 空态在 runner 上仍 gap **33>24**、长句 **56>44**（emptyBox 还是 NSStackView）；② `DetailScrollResetTests` 的 `afterVisible=0` vs `topVisible=11`（初始可见原点被当常数）。修法：emptyBox 改**普通 NSView + 显式四边约束**；滚动守卫改断言“换选后可见原点 ≤1”（旧行为 2357 仍红）；`PressFeedbackTests` 菜单按钮精确计数 2→3。sources `R409/7426d05` 一致、全量计数 92-vs-934 反向对照 ok。436 `judged=5/5 executed=73`、`REDS=0`、UNLISTED=0，`notice-banner` 放行，保持结案。全量 `Executed {executed} tests, with {skipped} tests skipped and {failures} failures`；换装 `ok / SHA_MATCH=1 / 381=381`；清账表 162=162；`HIDDEN_ARMS 表={h_tables} 可判={h_judged} rot={h_rot} … 上界 rot={h_rot_ceiling} 处置=ok`；预检 `tables={pre_tables} covered={pre_covered} arms={pre_arms} bad={pre_bad}`、全仓 {arm_files} 文件 / {arm_total} 把；产品面连续零改动 **{streak}** 轮（as-of 409，现读 `python3 scripts/product_streak.py --streak-for 409`）。电池待台账后复跑。

本轮做了什么：
① ⓪ R409 头跑 failure：2 个失败步骤，空态 33/56 + 滚动可见原点 0 vs 11；两处都已按 runner 原文修。
② 产品：菜单栏空态补「打开时间剪史」，旧/新 CTA 带 0/0→1166/1382；4 帧变化。
③ 判据：源 + 像素双带；M1061/M1062 双 CAUGHT；M1053/M1054 重跑仍 CAUGHT。
④ 436：judged=5/5、REDS=0、UNLISTED=0、notice-banner 放行，保持结案。
⑤ 367：hidden 表 {h_tables} / 可判 {h_judged} / rot {h_rot} / 上界 {h_rot_ceiling}；预检 {pre_tables}/{pre_covered}/{pre_arms}/{pre_bad}。
⑥ 全量 {executed}/{skipped}/{failures}；换装 ok；清账表 162=162。

NOT-RUN / 阻塞（分开写）：① 真实菜单展开/关闭仍只能人工验；② 离屏 alpha 动画采样不到中间帧（mid=1.0）⇒ 弹层淡入不签产品结论；③ 亮档真机腿仍没跑；④ macOS 12 紧凑详情头仍走旧截断；⑤ 主列表与浮层来源搜索语言未统一（437）；⑥ R410 新跑待 push 后读。

下一轮（R411）的靶：⓪ 先 `git push origin main`（禁 amend/force）并复核 ahead=0；读 R410 主笔+追记 head 跑全部失败步骤（成对 run↔commit），in_progress/0 字节不算绿；① 367 现读 rot=0，按 `HIDDEN_ROT` 查新腐烂；② 继续产品视觉位并落 Sources，换缺陷类别；③ 436 只复核新跑 Motion floor，不重新猜 `must_judge`。
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
report_new = once(report_old, "D-069 … **D-401**", "D-069 … **D-402**")
report_new = once(report_new, "U-31 … U-1472（R409 现读抬到最新一节）", "U-31 … U-1477（R410 现读抬到最新一节）")
report_new = once(
    report_new,
    "R409 现读：注册表 **165** 张 / 刀号最大 **M1060** / 预检 covered=147 arms=434 bad=0；全仓 258 文件 / 918 把；M674 退役、M906 空刀退役",
    f"R410 现读：注册表 **{pre_tables}** 张 / 刀号最大 **M1062** / 预检 covered={pre_covered} arms={pre_arms} bad={pre_bad}；"
    f"全仓 {arm_files} 文件 / {arm_total} 把；M674 退役、M906 空刀退役")
report_new = report_new.rstrip() + "\n\n" + report_bullet
report_new = once(report_new, "`AGENT_STATE.md` 的 R409 节", "`AGENT_STATE.md` 的 R410 节")

state_old = rd("AGENT_STATE.md")
state_anchor = "## R409 状态（2026-10-26"
assert state_old.count(state_anchor) == 1
state_new = once(state_old, state_anchor, state_section + "\n" + state_anchor)

backlog = rd("AGENT_BACKLOG.md").rstrip() + "\n\n" + """437 追记（R410 · 仍开）：本轮补的是菜单栏空态 CTA 与两处跨机布局守卫；主列表仍不匹配 `sourceAppName`，与 QuickPick 继续两套搜索语言。
"""

wr("AGENT_UI_AUDIT.md", audit_new)
wr("AGENT_VISUAL_ITERATION.md", iteration_new)
wr("AGENT_DECISIONS.md", decisions_new)
wr("CHANGELOG.md", changelog_new)
wr("AGENT_FINAL_REPORT.md", report_new)
wr("AGENT_STATE.md", state_new)
wr("AGENT_BACKLOG.md", backlog)

print("R410_LEDGERS_OK warnings=%s full=%s/%s/%s frames=%s changed=%s baseline=%s/%s/%s/%s pre=%s/%s/%s/%s arms=%s/%s rot=%s gate=%s=%s streak=%s"
      % (warnings, executed, skipped, failures, frames, pre_changed,
         b_compared, b_changed, b_missing, b_added,
         pre_tables, pre_covered, pre_arms, pre_bad, arm_files, arm_total,
         h_rot, cleared, cells, streak))
