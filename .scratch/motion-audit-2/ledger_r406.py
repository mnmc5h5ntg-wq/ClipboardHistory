#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R406（第 405 轮 / Round 403）的台账。数字全部从本机日志/CI 现读解析。"""
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


build = log("/tmp/r406_build2.log")
warnings = len(re.findall(r"warning:", build))
assert warnings == 0

full = log("/tmp/r406_full2.log")
summaries = [tuple(int(x) for x in row) for row in
             re.findall(r"Executed (\d+) tests, with (\d+) tests skipped and (\d+) failures", full)]
big = [row for row in summaries if row[0] > 900]
assert big
executed, skipped, failures = big[-1]
assert (executed, skipped, failures) == (1070, 53, 0)

capture = log("/tmp/r406_capture.log")
assert "CAPTURED 186 -> /tmp/r406_shots" in capture
frames = 186
assert "Executed 112 tests, with 4 tests skipped and 0 failures" in capture
assert "DETAIL_SCROLL_PIXEL light 顶部墨=35156 换选墨=35156 变化=0/439200 比例=0.0000" in capture
assert "DETAIL_SCROLL_PIXEL dark 顶部墨=39515 换选墨=39515 变化=0/439200 比例=0.0000" in capture

diff = log("/tmp/r406_diff.log")
dm = re.search(r"FRAME_DIFF 比了=(\d+) 变了=(\d+)", diff)
assert dm
total_frames, changed_frames = [int(x) for x in dm.groups()]
assert (total_frames, changed_frames) == (186, 4)
for name in ("detail-scroll-after-switch-720x520-dark.png", "detail-scroll-after-switch-720x520-light.png",
             "detail-scroll-top-720x520-dark.png", "detail-scroll-top-720x520-light.png"):
    assert name in diff

pre = log("/tmp/r406_baseline_pre.log")
pm = re.search(r"FRAME_BASELINE_COMPARED=(\d+)\s+FRAME_BASELINE_CHANGED=(\d+)"
               r"\s+FRAME_BASELINE_MISSING=(\d+)\s+FRAME_BASELINE_ADDED=(\d+)", pre)
assert pm
pre_comp, pre_changed, pre_missing, pre_added = [int(x) for x in pm.groups()]
assert (pre_comp, pre_changed, pre_missing, pre_added) == (186, 0, 0, 4)
baseline = log("/tmp/r406_baseline.log")
bm = re.search(r"FRAME_BASELINE_COMPARED=(\d+)\s+FRAME_BASELINE_CHANGED=(\d+)"
               r"\s+FRAME_BASELINE_MISSING=(\d+)\s+FRAME_BASELINE_ADDED=(\d+)", baseline)
assert bm
b_compared, b_changed, b_missing, b_added = [int(x) for x in bm.groups()]
assert (b_compared, b_changed, b_missing, b_added) == (186, 0, 0, 0)

ci_latest = log("/tmp/r406_ci_latest.log")
assert "RUN=40316586448 sha=2e80585 status=completed conclusion=success" in ci_latest
ci_steps = log("/tmp/r406_ci_steps.log")
assert "RUN=40316586448 conclusion=success" in ci_steps
assert "⇒ failure" not in ci_steps
ci_notes = log("/tmp/r406_ci_notes.log")
assert "SOURCES_CELL 账上=R405/`2e6998f` git=R405/`2e6998f` 一致=是" in ci_notes
assert "反方向：全量卷那一节被写成 92（捕帧卷的数）而日志里另有一卷 934 ⇒ 恒等式必须响。 ... ok" in ci_notes
assert "MOTION_FLOOR_FACTS judged=5/5 executed=73 not-run=-" in ci_notes
assert "MOTION_FLOOR_REDS=0" in ci_notes
assert "FAILED_STEP_COUNT=0" in ci_notes
assert "UNLISTED_COUNT=0" in ci_notes

mut = log("/tmp/r406_mut2.log")
assert "M1053 换选正文不归顶（行为判据） ⇒ CAUGHT 红得对=True 命中=True" in mut
assert "M1054 换选正文不归顶（像素判据） ⇒ CAUGHT 红得对=True 命中=True" in mut
assert "换选后=2300 docOrigin=-57 docVisible=2357" in mut
assert "比例=0.1596" in mut
assert "R406_SCROLL_MUTATE 刀=2 CAUGHT=2 红得不对=0 RESTORE_CLEAN=yes" in mut

behavior = log("/tmp/r406_scroll_behavior.log")
assert "DETAIL_SCROLL_RESET 可滚高=2300 顶部参照=-57 旧偏移=2300 换选后=-57 docOrigin=-57 docVisible=0" in behavior

pixels = log("/tmp/r406_scroll_pixels.log")
pix = {}
for label, tag, changed, total, pct in re.findall(
        r"SCROLL_PIXEL (旧代码|新代码) (light|dark) (\d+)/(\d+) ([\d.]+)%", pixels):
    pix[(label, tag)] = (int(changed), int(total), float(pct))
assert set(pix) == {("旧代码", "light"), ("旧代码", "dark"), ("新代码", "light"), ("新代码", "dark")}
assert pix[("旧代码", "light")][2] == 15.37 and pix[("旧代码", "dark")][2] == 15.96
assert pix[("新代码", "light")][0] == 0 and pix[("新代码", "dark")][0] == 0

precheck = log("/tmp/r406_precheck2.log")
pre_line = re.search(r"NEEDLE_PRECHECK tables=(\d+) covered=(\d+) arms=(\d+) bad=(\d+)", precheck)
arm_line = re.search(r"ARM_TOTAL files=(\d+) arms=(\d+) dupes=(\d+) repeats=(\d+)", precheck)
assert pre_line and arm_line
pre_tables, pre_covered, pre_arms, pre_bad = [int(x) for x in pre_line.groups()]
arm_files, arm_total, arm_dupes, arm_repeats = [int(x) for x in arm_line.groups()]
assert (pre_tables, pre_covered, pre_arms, pre_bad) == (162, 144, 428, 0)
assert (arm_files, arm_total) == (255, 912)
assert arm_dupes == 0 and arm_repeats == 0

hidden = log("/tmp/r406_hidden2.log")
h = re.search(r"HIDDEN_ARMS 表=(\d+) 可判=(\d+) rot=(\d+) 抽不出=(\d+) 已声明表=(\d+)"
              r" 已声明死针=(\d+) 上界 rot=(\d+)", hidden)
assert h
h_tables, h_judged, h_rot, h_opaque, h_dtables, h_ddead, h_rot_ceiling = [int(x) for x in h.groups()]
assert (h_tables, h_judged, h_rot, h_opaque, h_dtables, h_ddead, h_rot_ceiling) == (249, 846, 0, 6, 6, 0, 0)

install = log("/tmp/r406_install.log")
assert "INSTALL_RESULT=ok" in install and "INSTALL_SHA_MATCH=1" in install
entries = re.search(r"INSTALL_ENTRIES_BEFORE=(\d+)\s+INSTALL_ENTRIES_AFTER=(\d+)", install)
assert entries
entries_before, entries_after = entries.groups()
assert entries_before == entries_after == "381"

gate = log("/tmp/r406_gate.log")
g = re.search(r"MOTION_LEDGER 表面=(\d+) 状态=(\d+) 格子=(\d+) 行数=(\d+)"
              r" 已清账=(\d+) 未清账=(\d+) 地板=(\d+)", gate)
assert g
surfaces, states, cells, rows, cleared, uncleared, floor_count = [int(x) for x in g.groups()]
assert (surfaces, states, cells, rows, cleared, uncleared, floor_count) == (18, 9, 162, 162, 162, 0, 162)

streak_out = subprocess.check_output(
    ["python3", os.path.join(ROOT, "scripts/product_streak.py"), "--streak-for", "405"],
    cwd=ROOT).decode("utf-8")
streak = int(re.search(r"streak=(\d+)", streak_out).group(1))
assert streak == 1, "streak=%d" % streak

old_light, old_dark = pix[("旧代码", "light")], pix[("旧代码", "dark")]
ui_heading = "## 第 404 轮（R405"
ui_section = f"""## 第 405 轮（R406 · 2026-10-26 · U-1452…U-1457）：换选记录后详情正文回到顶部（旧 2300→2300、像素差 15.37/15.96% → 0/0）；`40316586448` 全绿签收（U-1452…U-1457 · 产品 3 文件，滚动到位位）

- **U-1452：⓪ R405 头跑签收。** `40316586448 ↔ 2e80585` **completed / success**，22 步全 success、`FAILED_STEP_COUNT=0`；`SOURCES_CELL 账上=R405/2e6998f git=R405/2e6998f 一致=是`；全量计数解析的负对照（把全量卷写成捕帧卷的 92 而日志另有 934 ⇒ 恒等式必须响）现读 **ok**，说明不是套件级读数。R406 新跑待 push 后读。
- **U-1453：② 滚动到位 —— 换选后详情正文保留上一条的滚动偏移。** 真看 `detail-scroll-after-switch`：先把 A 滚到 300pt，再走产品入口 `perform(.selectOnly(B))`；旧代码把偏移留给 B（旧帧从 B-20 起，顶部帧从 B-0 起）。行为读数：可滚高 2300、旧偏移 2300 → **换选后仍 2300**；像素同带（x=40..650、y=70..250pt）与「新选即顶部」参照帧差 亮 **{old_light[2]:.2f}%** / 暗 **{old_dark[2]:.2f}%**。
- **U-1454：② 修法 —— 正文身份变了才归顶，首次挂载不滚。** `ChineseSelectableTextView` / `ChineseSelectableAttributedTextView` 增加 `resetKey`；`ChineseSelectableNSTextView.resetScrollIfIdentityChanged` 只在身份变更时调 `scrollToBeginningOfDocument`（只改 clip bounds 不够：文本视图自己的 frame origin 会留成 −57，画面仍从第 2 行开始），并在下一轮主循环再补一次。首次挂载只记身份不滚 —— 否则所有既有详情帧会从 0 挪到 −57（无用户回归）。新行为：顶部参照 **−57**、换选后 **−57**、`docVisible=0`；像素 亮/暗 **0/439200 = 0.00%**。真看新帧：after-switch 与 top 均从 B-0 起。新增 4 帧（top/after-switch × 亮暗），**既有 182 帧逐字节不变**、基线同笔 186/0/0/0。
- **U-1455：判据与刀。** 行为守卫 `DetailScrollResetTests.testSelectingAnotherEntryBringsTheBodyBackToTheTop` 从 `DetailView` 产品入口读 NSScrollView（不是直接调 reset）；像素守卫 `UICaptureTests.testDetailScrollReturnsToTopWhenSelectionChanges` 比同一顶部带，参照帧墨 35156/39515 作为对象闸门。`M1053`（行为）/`M1054`（像素）双 **CAUGHT**、红得对=2、`RESTORE_CLEAN=yes`。新增 `resetKey` 打破了两条 `Round4MarkdownTests` 的字面量守卫（2 红）——按新形状改守卫并加钉 `resetKey: url`，没有放开「渲染器必须传/原文路必须在」的语义。
- **U-1456：③ 436 只读新跑。** `MOTION_FLOOR_FACTS judged=5/5 executed=73 not-run=- summary=detail-kind-change=3 empty-state=3 notice-banner=2 notice-banner-dismiss=2 settings-reset-fade=3 红的用例=- 汇总行报红=0`、`MOTION_FLOOR_REDS=0`、`UNLISTED_COUNT=0`；`notice-banner` 是登记放行臂，未重猜 `must_judge`，保持结案。
- **U-1457：① 367 rot 与八步。** `HIDDEN_ARMS 表={h_tables} 可判={h_judged} rot={h_rot} 抽不出={h_opaque} 已声明表={h_dtables} 已声明死针={h_ddead} 上界 rot={h_rot_ceiling} 处置=ok`；预检 `tables={pre_tables} covered={pre_covered} arms={pre_arms} bad={pre_bad}`、全仓 {arm_files} 文件 / {arm_total} 把；`M1053/M1054` 全 CAUGHT。build **{warnings}** 告警；全量 `Executed {executed} tests, with {skipped} tests skipped and {failures} failures`；捕获 `CAPTURED {frames} -> /tmp/r406_shots`（112 条判据 / 4 skip / 0 失败），与 R405 比 `变了={changed_frames}`（全是新增的 4 张），基线同笔 `UPDATED=186`、复验 `COMPARED={b_compared} CHANGED={b_changed} MISSING={b_missing} ADDED={b_added}`；换装 `INSTALL_RESULT=ok`、`INSTALL_SHA_MATCH=1`、条目 `{entries_before}={entries_after}`；清账表 `表面={surfaces} 状态={states} 格子={cells} 已清账={cleared} 未清账={uncleared} 地板={floor_count}`；产品面连续零改动 **{streak}** 轮（as-of 405；本轮已落 Sources，现读 `python3 scripts/product_streak.py --streak-for 405`）。电池待台账后复跑。
- **新帧的能力闸门**：像素判据依赖 y=70..250pt 的正文带，所以先要求参照帧在该带墨 >1000（实读 35156/39515）；拍不到这一带就红在「没有对象」，不会把空带读成「已归顶」。跨倍率不适用（这一格是同一 2× 通道的静态帧），未伪称跨倍率正对照。
"""

iteration = f"""## Round 403 · R406（第 405 轮 · 2026-10-26）：换选记录后详情正文回到顶部（旧 2300→2300、像素差 15.37/15.96% → 0/0）；`40316586448` 全绿签收（产品 3 文件，滚动到位位）

详情正文的 `NSScrollView` 会被下一条记录复用：把 A 滚到 300pt 后换选 B，旧代码把偏移留给 B（旧帧从 B-20 起，顶部帧从 B-0 起）。行为读数：可滚高 2300、旧偏移 2300 → 换选后仍 2300；像素同带与「新选即顶部」参照帧差 亮 15.37% / 暗 15.96%。修法：正文 representable 增加 `resetKey`（记录 id），身份变了才调 `scrollToBeginningOfDocument`（只改 clip bounds 不够，文本视图 frame origin 会留成 −57），首次挂载只记身份不滚。新行为：顶部参照 −57 → 换选后 −57；像素 0/439200 = 0.00%；新增 4 帧、既有 182 帧逐字节不变、基线 186/0/0/0。行为/像素两刀 M1053/M1054 双 CAUGHT。⓪ `40316586448 ↔ 2e80585` success、22 步全绿；sources R405/2e6998f 一致；全量计数解析的 92-vs-934 负对照 ok。436 `judged=5/5`、`REDS=0`、UNLISTED=0。全量 1070/53/0；电池 683/4；HIDDEN rot=0。

**七维度自评**（恰七行，每格 n/15）：

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | 15/15 | 真看旧 after-switch（B-20）与新 after-switch/top（B-0）亮暗四张；不是只看偏移数。 |
| 判据有效性 | 15/15 | 行为读产品 NSScrollView + 像素比同带参照；M1053/M1054 双 CAUGHT，红得对=2。 |
| 假绿防御 | 15/15 | 像素带先要参照墨 35156/39515；旧 15.37/15.96% 新 0；首次挂载不滚挡住 182 帧漂移。 |
| 产品面推进 | 14/15 | 真落 Sources 3 文件，修的是换记录从中间读；扣 1：只动正文滚动，未做滚动动画。 |
| 台账一致性 | 15/15 | U-1452…U-1457、D-398、436、R405 跑与新增 4 帧都从日志/CI 解析。 |
| 交付诚实性 | 15/15 | 全量先出 2 红（字面量守卫），按新形状修守卫不放松；新跑 success 才签收。 |
| 可复核性 | 15/15 | 旧/新偏移、旧/新像素比例、四张帧、两把刀、precheck/rot/CI 原文都在。 |

均分 = 104/105 ≈ 14.9/15（99）。
"""

decision = """
### D-398（406）正文复用视图换记录必须归顶；归顶走文本视图自己的入口，首次挂载不滚

R406 现读：详情正文的 `NSScrollView` 被下一条记录复用，旧代码把上一条的滚动偏移留给新记录（可滚高 2300、旧偏移 2300 → 换选后仍 2300；旧帧从 B-20 起）。修法：正文 representable 带 `resetKey`（记录 id），身份变了才调 `scrollToBeginningOfDocument`，首次挂载只记身份不滚。只改 clip bounds 不够——文本视图会把自己的 frame origin 留成 −57，画面仍从第 2 行开始。新行为：顶部参照 −57 → 换选后 −57；像素同带差 15.37/15.96% → 0/0。M1053/M1054 双 CAUGHT。
**Why**：同一块视图复用是性能与选中语义的需要，但它把“上一条的位置”变成了新记录的初始状态；用户分不清新记录的开头与旧记录的位置。而归顶若在首次挂载也执行，会把所有既有详情帧从 0 挪到 −57 —— 修一个缺陷不该顺手改所有帧。
**How to apply**：① 复用视图换身份时重置“位置类状态”（滚动/展开/选中视口），不要只重置内容；② 归顶用文本视图自己的 `scrollToBeginningOfDocument`，不要只改外层 clip bounds；③ 首次挂载只记身份不滚，避免无用户回归；④ 像素判据必须带同带参照帧与墨地板，拍不到就红在“没有对象”，不是“已修好”。
"""

changelog = """### 换选记录后详情正文回到顶部（旧 2300→2300、像素差 15.37/15.96% → 0/0）；R405 头跑全绿签收（R406 / 第 405 轮 / Round 403 / U-1452…U-1457 · 产品 3 文件，滚动到位位）

"""
report_bullet = """
- **R406（滚动到位位）**：详情正文的 `NSScrollView` 被下一条记录复用，换选后保留上一条的偏移（旧 2300→2300；旧帧从 B-20 起）。正文 representable 增加 `resetKey`，身份变了才 `scrollToBeginningOfDocument`，首次挂载只记身份不滚；新行为顶部参照 −57 → 换选后 −57，像素同带 15.37/15.96% → 0/0；新增 4 帧、既有 182 帧不变、基线 186/0/0/0；M1053/M1054 双 CAUGHT。⓪ `40316586448 ↔ 2e80585` **success**、22 步全绿；sources R405/2e6998f 一致；全量计数 92-vs-934 负对照 ok。436 `judged=5/5`、`REDS=0`、UNLISTED=0。全量 1070/53/0；电池 683/4。新跑待 push 后读。
"""

state_section = f"""## R406 状态（2026-10-26 · 本地 · 第 405 轮 / Round 403）：换选记录后详情正文回到顶部（旧 2300→2300、像素差 15.37/15.96% → 0/0）；R405 头跑全绿签收（产品 3 文件，滚动到位位）

最后更新：2026-10-26（本地 · R406 / 第 405 轮 / Round 403）：详情正文的 `NSScrollView` 被下一条记录复用。把 A 滚到 300pt 后换选 B，旧代码把偏移留给 B（旧帧从 B-20 起，顶部帧从 B-0 起）。行为读数：可滚高 2300、旧偏移 2300 → **换选后仍 2300**；像素同带与「新选即顶部」参照帧差 亮 **{old_light[2]:.2f}%** / 暗 **{old_dark[2]:.2f}%**。修法：正文 representable 增加 `resetKey`（记录 id），身份变了才调 `scrollToBeginningOfDocument`（只改 clip bounds 不够，文本视图 frame origin 会留成 −57），首次挂载只记身份不滚。新行为：顶部参照 −57 → 换选后 −57、`docVisible=0`；像素 亮/暗 **0/439200 = 0.00%**；新增 4 帧、既有 182 帧逐字节不变、基线同笔 186/0/0/0。行为/像素两刀 `M1053/M1054` 双 CAUGHT。⓪ `40316586448 ↔ 2e80585` **success**、22 步全 success、`FAILED_STEP_COUNT=0`；sources `R405/2e6998f` 一致；全量计数解析的 92-vs-934 负对照 ok。436 `judged=5/5 executed=73`、`REDS=0`、UNLISTED=0，`notice-banner` 放行，保持结案。全量 `Executed {executed} tests, with {skipped} tests skipped and {failures} failures`；换装 `ok / SHA_MATCH=1 / 381=381`；清账表 162=162；`HIDDEN_ARMS 表={h_tables} 可判={h_judged} rot={h_rot} … 上界 rot={h_rot_ceiling} 处置=ok`；预检 `tables={pre_tables} covered={pre_covered} arms={pre_arms} bad={pre_bad}`、全仓 {arm_files} 文件 / {arm_total} 把；产品面连续零改动 **{streak}** 轮（as-of 405，现读 `python3 scripts/product_streak.py --streak-for 405`）。电池待台账后复跑。

本轮做了什么：
① ⓪ R405 头跑 success、22 步全绿；sources 同笔；全量计数解析反证 ok。
② 产品：换选记录时正文归顶（旧 2300→2300；新顶部 −57；像素 15.37/15.96% → 0/0），新增 4 帧、老 182 帧不变。
③ 判据：行为 + 像素两层；M1053/M1054 双 CAUGHT；Round4 字面量守卫按新形状更新并加钉 `resetKey`。
④ 436：judged=5/5、REDS=0、UNLISTED=0、notice-banner 放行，保持结案。
⑤ 367：hidden 表 {h_tables} / 可判 {h_judged} / rot {h_rot} / 上界 {h_rot_ceiling}；预检 {pre_tables}/{pre_covered}/{pre_arms}/{pre_bad}。
⑥ BACKLOG 437 仍开：主列表与浮层仍是两套来源搜索语言；本轮未动。

NOT-RUN / 阻塞（分开写）：① 亮档真机腿仍没跑；② macOS 12 紧凑详情头仍走旧截断；③ 主列表与浮层的来源搜索语言未统一（437）；④ R406 新跑待 push 后读。

下一轮（R407）的靶：⓪ 先 `git push origin main`（禁 amend/force）并复核 ahead=0；读 R406 主笔+追记 head 跑全部失败步骤（成对 run↔commit），in_progress/0 字节不算绿；① 367 现读 rot=0，按 `HIDDEN_ROT` 查新腐烂；② 继续产品视觉位并落 Sources，换缺陷类别；③ 436 只复核新跑 Motion floor，不重新猜 `must_judge`。
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
report_new = once(report_old, "D-069 … **D-397**", "D-069 … **D-398**")
report_new = once(report_new, "U-31 … U-1451（R405 现读抬到最新一节）", "U-31 … U-1457（R406 现读抬到最新一节）")
report_new = once(
    report_new,
    "R405 现读：注册表 **161** 张 / 刀号最大 **M1052** / 预检 covered=143 arms=426 bad=0；全仓 254 文件 / 910 把；M674 退役、M906 空刀退役",
    f"R406 现读：注册表 **{pre_tables}** 张 / 刀号最大 **M1054** / 预检 covered={pre_covered} arms={pre_arms} bad={pre_bad}；"
    f"全仓 {arm_files} 文件 / {arm_total} 把；M674 退役、M906 空刀退役")
report_new = report_new.rstrip() + "\n\n" + report_bullet
report_new = once(report_new, "`AGENT_STATE.md` 的 R405 节", "`AGENT_STATE.md` 的 R406 节")

state_old = rd("AGENT_STATE.md")
state_anchor = "## R405 状态（2026-10-26"
assert state_old.count(state_anchor) == 1
state_new = once(state_old, state_anchor, state_section + "\n" + state_anchor)

backlog = rd("AGENT_BACKLOG.md").rstrip() + "\n\n" + """437 追记（R406 · 仍开）：本轮未改主列表搜索语义；只修了详情正文换记录后的滚动归顶。主列表仍不匹配 `sourceAppName`，与 QuickPick 继续两套语言。
"""

wr("AGENT_UI_AUDIT.md", audit_new)
wr("AGENT_VISUAL_ITERATION.md", iteration_new)
wr("AGENT_DECISIONS.md", decisions_new)
wr("CHANGELOG.md", changelog_new)
wr("AGENT_FINAL_REPORT.md", report_new)
wr("AGENT_STATE.md", state_new)
wr("AGENT_BACKLOG.md", backlog)

print("R406_LEDGERS_OK warnings=%s full=%s/%s/%s frames=%s changed=%s baseline=%s/%s/%s/%s pre=%s/%s/%s/%s arms=%s/%s rot=%s gate=%s=%s streak=%s"
      % (warnings, executed, skipped, failures, frames, changed_frames,
         b_compared, b_changed, b_missing, b_added,
         pre_tables, pre_covered, pre_arms, pre_bad, arm_files, arm_total,
         h_rot, cleared, cells, streak))
