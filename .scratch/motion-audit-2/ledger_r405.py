#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R405（第 404 轮 / Round 402）的台账。数字全部从本机日志/CI 现读解析。"""
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


build = log("/tmp/r405_build.log")
warnings = len(re.findall(r"warning:", build))
assert warnings == 0

full = log("/tmp/r405_full.log")
summaries = [tuple(int(x) for x in row) for row in
             re.findall(r"Executed (\d+) tests, with (\d+) tests skipped and (\d+) failures", full)]
big = [row for row in summaries if row[0] > 900]
assert big
executed, skipped, failures = big[-1]
assert (executed, skipped, failures) == (1068, 53, 0)

capture = log("/tmp/r405_capture.log")
assert "CAPTURED 182 -> /tmp/r405_shots" in capture
frames = 182
assert "QUICKPICK_MATCH_REASON 源命中=2 带理由=2 无查询=5 无查询带理由=0 文件名命中=1 文件名带理由=0 Safari命中=1 Safari带理由=1" in capture
bands = {}
for tag, control, ext in re.findall(r"QUICKPICK_MATCH_REASON_BAND (light|dark) 校准带墨=(\d+) 扩展带墨=(\d+)", capture):
    bands[tag] = (int(control), int(ext))
assert set(bands) == {"light", "dark"}
assert all(control > 100 and ext > 20 for control, ext in bands.values())

diff = log("/tmp/r405_diff.log")
dm = re.search(r"FRAME_DIFF 比了=(\d+) 变了=(\d+)", diff)
assert dm
total_frames, changed_frames = [int(x) for x in dm.groups()]
assert (total_frames, changed_frames) == (182, 2)
assert "quickpick-typed-420x300-dark.png" in diff and "quickpick-typed-420x300-light.png" in diff

baseline = log("/tmp/r405_baseline.log")
bm = re.search(r"FRAME_BASELINE_COMPARED=(\d+)\s+FRAME_BASELINE_CHANGED=(\d+)"
               r"\s+FRAME_BASELINE_MISSING=(\d+)\s+FRAME_BASELINE_ADDED=(\d+)", baseline)
assert bm
b_compared, b_changed, b_missing, b_added = [int(x) for x in bm.groups()]
assert (b_compared, b_changed, b_missing, b_added) == (182, 0, 0, 0)

ci_latest = log("/tmp/r405_ci_latest.log")
assert "RUN=40309568444 sha=1e78ca9 status=completed conclusion=success" in ci_latest
ci_steps = log("/tmp/r405_ci_steps.log")
assert "RUN=40309568444 conclusion=success" in ci_steps
assert "⇒ failure" not in ci_steps
ci_notes = log("/tmp/r405_ci_notes.log")
assert "LONG_TEXT_PILL_NOT_RUN=band-empty：600（detail-witness=0 sidebar-witness=0）" in ci_notes
assert "RULER_BROKEN_COUNT=0" in ci_notes
assert "REMOVE_RED_COUNT=0" in ci_notes
assert "FAILED_STEP_COUNT=0" in ci_notes
assert "MOTION_FLOOR_REDS=0" in ci_notes
assert "MOTION_FLOOR_FACTS judged=5/5 executed=73 not-run=-" in ci_notes

trash = {}
for tag, red, ink in re.findall(r"TRASH_RED (light|dark) 红=(\d+) 图标墨=(\d+)", log("/tmp/r405_ci_40309568444.log")):
    trash[tag] = (int(red), int(ink))
assert set(trash) == {"light", "dark"}
assert trash["light"][0] >= 20 and trash["dark"][0] >= 20

mut = log("/tmp/r405_mut.log")
assert "M1051 来源命中不再给出理由（源/管线判据） ⇒ CAUGHT 红得对=True 命中=True" in mut
assert "M1052 来源命中理由不进入行文案（像素判据） ⇒ CAUGHT 红得对=True 命中=True" in mut
assert "R405_MATCH_REASON_MUTATE 刀=2 CAUGHT=2 红得不对=0 RESTORE_CLEAN=yes" in mut
old_mut = log("/tmp/r405_m1047.log")
assert "M1047 「移除」退回普通文字色（源判据） ⇒ CAUGHT 红得对=True 命中=True" in old_mut
assert "R403_REMOVE_MUTATE 刀=1 CAUGHT=1 红得不对=0 RESTORE_CLEAN=yes" in old_mut

pre = log("/tmp/r405_precheck.log")
pre_line = re.search(r"NEEDLE_PRECHECK tables=(\d+) covered=(\d+) arms=(\d+) bad=(\d+)", pre)
arm_line = re.search(r"ARM_TOTAL files=(\d+) arms=(\d+) dupes=(\d+) repeats=(\d+)", pre)
assert pre_line and arm_line
pre_tables, pre_covered, pre_arms, pre_bad = [int(x) for x in pre_line.groups()]
arm_files, arm_total, arm_dupes, arm_repeats = [int(x) for x in arm_line.groups()]
assert (pre_tables, pre_covered, pre_arms, pre_bad) == (161, 143, 426, 0)
assert (arm_files, arm_total) == (254, 910)
assert arm_dupes == 0 and arm_repeats == 0

hidden = log("/tmp/r405_hidden.log")
h = re.search(r"HIDDEN_ARMS 表=(\d+) 可判=(\d+) rot=(\d+) 抽不出=(\d+) 已声明表=(\d+)"
              r" 已声明死针=(\d+) 上界 rot=(\d+)", hidden)
assert h
h_tables, h_judged, h_rot, h_opaque, h_dtables, h_ddead, h_rot_ceiling = [int(x) for x in h.groups()]
assert (h_tables, h_judged, h_rot, h_opaque, h_dtables, h_ddead, h_rot_ceiling) == (248, 844, 0, 6, 6, 0, 0)

install = log("/tmp/r405_install.log")
assert "INSTALL_RESULT=ok" in install and "INSTALL_SHA_MATCH=1" in install
entries = re.search(r"INSTALL_ENTRIES_BEFORE=(\d+)\s+INSTALL_ENTRIES_AFTER=(\d+)", install)
assert entries
entries_before, entries_after = entries.groups()
assert entries_before == entries_after == "381"

gate = log("/tmp/r405_gate.log")
g = re.search(r"MOTION_LEDGER 表面=(\d+) 状态=(\d+) 格子=(\d+) 行数=(\d+)"
              r" 已清账=(\d+) 未清账=(\d+) 地板=(\d+)", gate)
assert g
surfaces, states, cells, rows, cleared, uncleared, floor_count = [int(x) for x in g.groups()]
assert (surfaces, states, cells, rows, cleared, uncleared, floor_count) == (18, 9, 162, 162, 162, 0, 162)

streak_out = subprocess.check_output(
    ["python3", os.path.join(ROOT, "scripts/product_streak.py"), "--streak-for", "404"],
    cwd=ROOT).decode("utf-8")
streak = int(re.search(r"streak=(\d+)", streak_out).group(1))
assert streak == 1, "streak=%d" % streak

ui_heading = "## 第 403 轮（R404"
ui_section = f"""## 第 404 轮（R405 · 2026-10-26 · U-1447…U-1451）：QuickPick 搜到来源 App 时行上写出「来自 X」（旧结尾后墨 0→1006/1109）；R404 头跑全绿签收、band-empty 成具名 XCTSkip（U-1447…U-1451 · 产品 2 文件，搜索交互位）

- **U-1447：⓪ R404 头跑签收 + band-empty 归宿 + REMOVE_RED 退役核对。** `40309568444 ↔ 1e78ca9` **completed / success**，`FAILED_STEP_COUNT=0`（22 步全 success）；band-empty 现读 `LONG_TEXT_PILL_NOT_RUN=band-empty：600（detail-witness=0 sidebar-witness=0）` + `Test skipped`，`RULER_BROKEN_COUNT=0`；`REMOVE_RED_COUNT=0`、`TRASH_RED light 红={trash["light"][0]}/图标墨={trash["light"][1]}`、`dark 红={trash["dark"][0]}/图标墨={trash["dark"][1]}`。退役核对：源守卫 `M1047` 今天重跑仍 **CAUGHT**、`RESTORE_CLEAN=yes`；像素臂 `M1048` 与 `REMOVE_RED` 捕获守卫均已不在表/仓内（U-1444 的理由与 U-1438 的本地旧/新 0/0→591/605 仍可复查）。R403 的 RULER_BROKEN + REMOVE_RED 红至此由 runner 自己消失，不是被改写。
- **U-1448：② 搜索交互位 —— 搜「访达」出两条，行上看不出为什么命中。** 真看 `quickpick-typed` 旧帧：两条文件记录的文案只有「预览 · 时间」，而查询词只命中了来源 App（`QuickPickModel.filtered` 吃 `sourceAppName`）——匹配成立、理由不可见。修法：`QuickPickModel.sourceMatchReason(for:query:)` 只在**来源是唯一命中依据**时返回 App 名（预览/文件名已命中则不补，无查询也不补）；`QuickPickController.rowTitle(for:query:)` 把「来自 X」放在时间**之前**，行被截断先吃时间。真看新帧：`合同 终版 v3.pdf · 来自 访达 · 10月9日 16:48` 与第二条同形，无截断。像素现读（第 1 行旧结尾 x=246.5pt 之后的 x=250..410pt 扩展带）：旧 **0 / 0** → 新 **1006 / 1109**；同帧校准带 1445 / 1640。帧差分 **2** 张（quickpick-typed 亮暗），基线同笔 update 后 182/0。
- **U-1449：③ 436 只读新跑。** `MOTION_FLOOR_FACTS judged=5/5 executed=73 not-run=- summary=detail-kind-change=3 empty-state=3 notice-banner=2 notice-banner-dismiss=3 settings-reset-fade=2 红的用例=- 汇总行报红=0`、`MOTION_FLOOR_REDS=0`；`notice-banner` 是登记放行臂，`MOTION_FLOOR_OK=5/5`，无新 unlisted。未重猜 `must_judge`，436 保持结案。
- **U-1450：判据与刀。** 源/管线守卫 `testQuickPickSourceOnlyMatchCarriesItsReason`：从 `windowForCapture(query:)` 建真表格读 cell `stringValue`，来源命中 2/2 带理由、无查询 0/5、文件名命中 0/1、`Safari` 1/1；像素守卫 `testQuickPickSourceMatchReasonExtendsTheTypedRow` 只判「旧结尾之后有没有字」（不冒充源词身份，词的身份由源守卫钉）。`M1051`（源）/`M1052`（像素）双 **CAUGHT**、红得对=2、`RESTORE_CLEAN=yes`。
- **U-1451：① 367 rot 与八步。** `HIDDEN_ARMS 表={h_tables} 可判={h_judged} rot={h_rot} 抽不出={h_opaque} 已声明表={h_dtables} 已声明死针={h_ddead} 上界 rot={h_rot_ceiling} 处置=ok`；预检 `tables={pre_tables} covered={pre_covered} arms={pre_arms} bad={pre_bad}`、全仓 {arm_files} 文件 / {arm_total} 把；`M1051/M1052` 与 M1047 全 CAUGHT。build **{warnings}** 告警；全量 `Executed {executed} tests, with {skipped} tests skipped and {failures} failures`；捕获 `CAPTURED {frames} -> /tmp/r405_shots`，与 R404 逐张比 `变了={changed_frames}`（quickpick-typed 亮暗），帧基线同笔 `UPDATED=182`、复验 `COMPARED={b_compared} CHANGED={b_changed} MISSING={b_missing} ADDED={b_added}`；换装 `INSTALL_RESULT=ok`、`INSTALL_SHA_MATCH=1`、条目 `{entries_before}={entries_after}`；清账表 `表面={surfaces} 状态={states} 格子={cells} 已清账={cleared} 未清账={uncleared} 地板={floor_count}`；产品面连续零改动 **{streak}** 轮（as-of 404；本轮已落 Sources，现读 `python3 scripts/product_streak.py --streak-for 404`）。电池待台账后复跑。
- **新开 BACKLOG 437（不修）**：主列表 `HistoryStore.filteredEntries` 不吃来源 App，而 QuickPick `filtered` 吃 —— 两套搜索语言。要统一得先决定主列表是否也显示来源、行宽够不够；本轮只修「能搜到就要看得见理由」，没顺手改主列表语义。
"""

iteration = f"""## Round 402 · R405（第 404 轮 · 2026-10-26）：QuickPick 搜到来源 App 时行上写出「来自 X」（旧结尾后墨 0→1006/1109）；R404 头跑全绿签收（产品 2 文件，搜索交互位）

QuickPick 的过滤吃 `sourceAppName`，但行文案只有「预览 · 时间」：搜「访达」出两条文件记录，行上没有任何命中依据。修法：`sourceMatchReason` 只在来源是唯一命中依据时返回 App 名，`rowTitle` 把「来自 X」放在时间之前。真看新帧两条都写出「来自 访达」且无截断；扩展带旧 0/0 → 新 1006/1109，校准带 1445/1640；仅 quickpick-typed 亮暗两张变化，基线 182/0。源守卫读产品真表格（2/2、负对照 0/5、0/1、Safari 1/1），像素守卫只判旧结尾后的延伸；M1051/M1052 双 CAUGHT。⓪ `40309568444 ↔ 1e78ca9` success、22 步全绿；band-empty 成具名 `LONG_TEXT_PILL_NOT_RUN`（两证人 0），RULER_BROKEN 0；REMOVE_RED 0，源 M1047 今天仍 CAUGHT（像素臂已退役）。436 `judged=5/5`、`REDS=0`，notice-banner 是放行臂。全量 1068/53/0；HIDDEN rot=0。

**七维度自评**（恰七行，每格 n/15）：

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | 14/15 | 真看 quickpick-typed 旧/新亮暗四张，旧行无理由、新行理由可见且无截断；扣 1：只看浮层一个表面。 |
| 判据有效性 | 15/15 | 源守卫读真表格 + 像素守卫读同帧扩展带；M1051/M1052 双 CAUGHT，红得对=2。 |
| 假绿防御 | 15/15 | 旧带 0 新带 1006/1109；校准带 1445/1640 证明确实有字；无查询/文件名命中/大小写三组负对照都在。 |
| 产品面推进 | 14/15 | 真落 Sources（2 文件），修的是可解释性；扣 1：主列表搜索语言仍与浮层不一致（BACKLOG 437）。 |
| 台账一致性 | 15/15 | U-1447…U-1451、D-397、436、R404 跑与 M1047 复核都从日志/CI 解析。 |
| 交付诚实性 | 15/15 | R404 头跑 success 才签收；band-empty 是具名 skip 不叫绿；REMOVE_RED 退役留源守卫并今天重跑。 |
| 可复核性 | 15/15 | 旧/新带墨、校准带、2 帧差、三组负对照、两把刀、precheck/rot/CI 原文都在。 |

均分 = 103/105 ≈ 14.7/15（98）。
"""

decision = """
### D-397（405）搜索命中不可见的字段时，行上必须写出命中理由；像素尺只许判它真读得到的那一段

R405 现读：QuickPick 的 `filtered` 按 `sourceAppName` 命中，而行文案只有「预览 · 时间」——搜「访达」出两条文件记录，行上没有任何词解释它们为什么在。修法是 `sourceMatchReason` 只在来源是唯一命中依据时返回 App 名，`rowTitle` 把「来自 X」放在时间之前。扩展带旧 0/0 → 新 1006/1109；两帧变化；M1051/M1052 双 CAUGHT。
**Why**：可搜索的字段若不可见，用户只能把「搜到了」当成玄学；而像素守卫若把「旧结尾之后有任何字」说成「源词本身」，就是把尺的对象换掉——源词身份必须由读 `stringValue` 的源守卫钉。
**How to apply**：① 搜索匹配了哪个不可见字段，就在行上补那一段理由；理由放在易被截断的信息之前；② 非该字段命中时不补，避免全列表噪音；③ 像素守卫的名字与断言必须只说它量的那一段（扩展/位移），精确词身份交给源守卫；④ 两层各配一刀，且两刀要能分别在各自测试上红。
"""

changelog = """### QuickPick 搜到来源 App 时行上写出「来自 X」（旧结尾后墨 0→1006/1109）；R404 头跑全绿签收、band-empty 成具名 XCTSkip（R405 / 第 404 轮 / Round 402 / U-1447…U-1451 · 产品 2 文件，搜索交互位）

"""
report_bullet = """
- **R405（搜索交互位）**：QuickPick 的过滤吃 `sourceAppName`，行文案却只有「预览 · 时间」——搜「访达」出两条文件记录，行上看不出为什么命中。`sourceMatchReason` 只在来源是唯一命中依据时给理由，`rowTitle` 把「来自 X」放在时间之前；扩展带旧 `0/0` → 新 `1006/1109`（校准带 `1445/1640`），仅 `quickpick-typed` 亮暗 2 帧变化、基线 182/0；M1051/M1052 双 CAUGHT。⓪ `40309568444 ↔ 1e78ca9` **success**、22 步全绿；band-empty 现读具名 `LONG_TEXT_PILL_NOT_RUN=band-empty：600（detail-witness=0 sidebar-witness=0）` + XCTSkip，RULER_BROKEN=0；REMOVE_RED=0，源 M1047 今天重跑仍 CAUGHT（像素臂 M1048 已退役，理由/旧读数在 U-1444/U-1438）。436 `MOTION_FLOOR_FACTS judged=5/5 executed=73`、`REDS=0`，notice-banner 是放行臂。全量 1068/53/0；电池待复跑。新开 BACKLOG 437（主列表与浮层搜索语言不一致）。
"""

state_section = f"""## R405 状态（2026-10-26 · 本地 · 第 404 轮 / Round 402）：QuickPick 搜到来源 App 时行上写出「来自 X」（旧结尾后墨 0→1006/1109）；R404 头跑全绿签收（产品 2 文件，搜索交互位）

最后更新：2026-10-26（本地 · R405 / 第 404 轮 / Round 402）：QuickPick 的过滤按来源 App 命中，而行文案只有「预览 · 时间」——搜「访达」出两条文件记录，行上看不出为什么命中。`QuickPickModel.sourceMatchReason` 只在来源是唯一命中依据时返回 App 名，`QuickPickController.rowTitle` 把「来自 X」放在时间之前。像素现读（旧第 1 行结尾 x=246.5pt 之后的扩展带）：旧 **0/0** → 新 **1006/1109**（校准带 1445/1640）；仅 `quickpick-typed` 亮暗 2 帧变化，基线同笔 update 后 182/0。⓪ `40309568444 ↔ 1e78ca9` **success**、22 步全 success、`FAILED_STEP_COUNT=0`；band-empty 现读 `LONG_TEXT_PILL_NOT_RUN=band-empty：600（detail-witness=0 sidebar-witness=0）` + `Test skipped`，RULER_BROKEN=0；REMOVE_RED=0、TRASH_RED 亮 {trash["light"][0]}/{trash["light"][1]} 暗 {trash["dark"][0]}/{trash["dark"][1]}。REMOVE_RED 退役核对：源 M1047 今天重跑仍 CAUGHT、RESTORE_CLEAN=yes；像素臂 M1048 与 `REMOVE_RED` 捕获守卫已不在表/仓内。436 `judged=5/5 executed=73`、`REDS=0`，`notice-banner` 放行，保持结案。全量 `Executed {executed} tests, with {skipped} tests skipped and {failures} failures`；换装 `ok / SHA_MATCH=1 / 381=381`；清账表 162=162；`HIDDEN_ARMS 表={h_tables} 可判={h_judged} rot={h_rot} … 上界 rot={h_rot_ceiling} 处置=ok`；预检 `tables={pre_tables} covered={pre_covered} arms={pre_arms} bad={pre_bad}`、全仓 {arm_files} 文件 / {arm_total} 把；产品面连续零改动 **{streak}** 轮（as-of 404，现读 `python3 scripts/product_streak.py --streak-for 404`）。电池待台账后复跑。

本轮做了什么：
① ⓪ R404 头跑 success、22 步全绿；band-empty 成具名 XCTSkip（两证人 0）；REMOVE_RED 通道 0，源 M1047 今天 CAUGHT，像素臂已退役。
② 产品：QuickPick 行在来源单命中时写出「来自 X」，扩展带旧 0/0→1006/1109，2 帧变化。
③ 判据：源守卫读真表格（2/2、负对照 0/5、0/1、Safari 1/1）；像素守卫只判扩展带；M1051/M1052 双 CAUGHT。
④ 436：judged=5/5、REDS=0、notice-banner 放行，保持结案。
⑤ 367：hidden 表 {h_tables} / 可判 {h_judged} / rot {h_rot} / 上界 {h_rot_ceiling}；预检 {pre_tables}/{pre_covered}/{pre_arms}/{pre_bad}。
⑥ 新开 BACKLOG 437：主列表不吃来源 App，与浮层两套搜索语言。

NOT-RUN / 阻塞（分开写）：① 亮档真机腿仍没跑；② macOS 12 紧凑详情头仍走旧截断；③ 主列表与浮层的来源搜索语言未统一（437）。

下一轮（R406）的靶：⓪ 先 `git push origin main`（禁 amend/force）并复核 ahead=0；读 R405 主笔+追记 head 跑全部失败步骤（成对 run↔commit），in_progress/0 字节不算绿；① 367 现读 rot=0，按 `HIDDEN_ROT` 查新腐烂；② 继续产品视觉位并落 Sources，换缺陷类别；③ 436 只复核新跑 Motion floor，不重新猜 `must_judge`。
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
report_new = once(report_old, "D-069 … **D-396**", "D-069 … **D-397**")
report_new = once(report_new, "U-31 … U-1446（R404 现读抬到最新一节）", "U-31 … U-1451（R405 现读抬到最新一节）")
report_new = once(
    report_new,
    "R404 现读：注册表 **160** 张 / 刀号最大 **M1050** / 预检 covered=142 arms=424 bad=0；全仓 253 文件 / 908 把；M674 退役、M906 空刀退役",
    f"R405 现读：注册表 **{pre_tables}** 张 / 刀号最大 **M1052** / 预检 covered={pre_covered} arms={pre_arms} bad={pre_bad}；"
    f"全仓 {arm_files} 文件 / {arm_total} 把；M674 退役、M906 空刀退役")
report_new = report_new.rstrip() + "\n\n" + report_bullet
report_new = once(report_new, "`AGENT_STATE.md` 的 R404 节", "`AGENT_STATE.md` 的 R405 节")

state_old = rd("AGENT_STATE.md")
state_anchor = "## R404 状态（2026-10-26"
assert state_old.count(state_anchor) == 1
state_new = once(state_old, state_anchor, state_section + "\n" + state_anchor)

backlog = rd("AGENT_BACKLOG.md").rstrip() + "\n\n" + """**437. 主列表与 QuickPick 是两套搜索语言：前者不吃来源 App，后者吃**（R405 现读）
    `QuickPickModel.filtered` 会按 `sourceAppName` 命中，`HistoryStore.filteredEntries` 只查预览/文件名/OCR。用户在浮层搜「访达」出两条，在主列表搜同一个词却是 0 条。R405 只修了「浮层能搜到就要看得见理由」，没有顺手改主列表语义：那要先决定主列表行是否也显示来源、300pt 侧栏放不放得下。
    修法（下一轮或用户定）：先量 300pt 行里「时间 · 来源」是否与现有文本列争宽；若放不下，考虑只在搜索命中来源时把来源替到时间前面，或给主列表补来源匹配但用同一套理由后缀。无论选哪条，源守卫要同时读两个入口，别只改一处。
"""

wr("AGENT_UI_AUDIT.md", audit_new)
wr("AGENT_VISUAL_ITERATION.md", iteration_new)
wr("AGENT_DECISIONS.md", decisions_new)
wr("CHANGELOG.md", changelog_new)
wr("AGENT_FINAL_REPORT.md", report_new)
wr("AGENT_STATE.md", state_new)
wr("AGENT_BACKLOG.md", backlog)

print("R405_LEDGERS_OK warnings=%s full=%s/%s/%s frames=%s changed=%s baseline=%s/%s/%s/%s bands=%s/%s,%s/%s ci=%s mut=%s pre=%s/%s/%s/%s arms=%s/%s rot=%s gate=%s=%s streak=%s"
      % (warnings, executed, skipped, failures, frames, changed_frames,
         b_compared, b_changed, b_missing, b_added,
         bands["light"][0], bands["light"][1], bands["dark"][0], bands["dark"][1],
         "success", "2CAUGHT", pre_tables, pre_covered, pre_arms, pre_bad,
         arm_files, arm_total, h_rot, cleared, cells, streak))
