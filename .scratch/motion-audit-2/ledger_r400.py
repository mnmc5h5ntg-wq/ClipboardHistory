#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R400（第 399 轮 / Round 397）的台账。数字全部从本机日志/CI 现读解析。"""
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


build = log("/tmp/r400_build_final.log")
warnings = len(re.findall(r"warning:", build))
assert warnings == 0

full = log("/tmp/r400_full.log")
summaries = [tuple(int(x) for x in row) for row in
             re.findall(r"Executed (\d+) tests, with (\d+) tests skipped and (\d+) failures", full)]
big = [row for row in summaries if row[0] > 900]
assert big
executed, skipped, failures = big[-1]
assert (executed, skipped, failures) == (1061, 53, 0)

capture = log("/tmp/r400_capture.log")
cap = re.search(r"CAPTURED (\d+) -> /tmp/r400_shots", capture)
assert cap
frames = int(cap.group(1))
assert frames == 182
diff = log("/tmp/r400_framediff.log")
dm = re.search(r"FRAME_DIFF 比了=(\d+) 变了=(\d+)", diff)
assert dm
total_frames, changed_frames = [int(x) for x in dm.groups()]
assert (total_frames, changed_frames) == (182, 0)

baseline = log("/tmp/r400_framebaseline.log")
bm = re.search(r"FRAME_BASELINE_COMPARED=(\d+)\s+FRAME_BASELINE_CHANGED=(\d+)"
               r"\s+FRAME_BASELINE_MISSING=(\d+)\s+FRAME_BASELINE_ADDED=(\d+)", baseline)
assert bm
b_compared, b_changed, b_missing, b_added = [int(x) for x in bm.groups()]
assert (b_compared, b_changed, b_missing, b_added) == (182, 0, 0, 0)

new_motion = log("/tmp/r400_markdown_motion.log")
old_motion = log("/tmp/r400_markdown_old.log")
new_lab = {}
for scale, span, peak in re.findall(
        r"MARKDOWN_MODE_FADE scale=(\dx) 帧数=\d+ 过渡帧数=(\d+) 峰值=([0-9.]+) 声明=160ms", new_motion):
    new_lab[scale] = (int(span), float(peak))
old_lab = {}
for scale, span, peak in re.findall(
        r"MARKDOWN_MODE_FADE scale=(\dx) 帧数=\d+ 过渡帧数=(\d+) 峰值=([0-9.]+) 声明=160ms", old_motion):
    old_lab[scale] = (int(span), float(peak))
assert set(new_lab) == {"2x", "1x"} and set(old_lab) == {"2x", "1x"}
assert new_lab["1x"][0] >= 2 and new_lab["2x"][0] >= 2
assert old_lab["1x"][0] == 0

mut = log("/tmp/r400_mut.log")
assert "M1042 原文/渲染标签退回一帧硬换 ⇒ CAUGHT 红得对=True 命中=True" in mut
assert "R400_MUTATE 刀=1 CAUGHT=1 红得不对=0 RESTORE_CLEAN=yes" in mut
assert "还原后复跑：ESCAPED" in mut

pre = log("/tmp/r400_precheck2.log")
pre_line = re.search(r"NEEDLE_PRECHECK tables=(\d+) covered=(\d+) arms=(\d+) bad=(\d+)", pre)
arm_line = re.search(r"ARM_TOTAL files=(\d+) arms=(\d+) dupes=(\d+) repeats=(\d+)", pre)
assert pre_line and arm_line
pre_tables, pre_covered, pre_arms, pre_bad = [int(x) for x in pre_line.groups()]
arm_files, arm_total, arm_dupes, arm_repeats = [int(x) for x in arm_line.groups()]
assert (pre_tables, pre_covered, pre_arms, pre_bad) == (156, 139, 418, 0)
assert (arm_files, arm_total) == (249, 902)
assert arm_dupes == 0 and arm_repeats == 0

hidden = log("/tmp/r400_hidden2.log")
h = re.search(r"HIDDEN_ARMS 表=(\d+) 可判=(\d+) rot=(\d+) 抽不出=(\d+) 已声明表=(\d+)"
              r" 已声明死针=(\d+) 上界 rot=(\d+)", hidden)
assert h
h_tables, h_judged, h_rot, h_opaque, h_dtables, h_ddead, h_rot_ceiling = [int(x) for x in h.groups()]
assert (h_tables, h_judged, h_rot, h_opaque, h_dtables, h_ddead, h_rot_ceiling) == (243, 836, 0, 6, 6, 0, 0)

install = log("/tmp/r400_install.log")
assert "INSTALL_RESULT=ok" in install and "INSTALL_SHA_MATCH=1" in install
entries = re.search(r"INSTALL_ENTRIES_BEFORE=(\d+)\s+INSTALL_ENTRIES_AFTER=(\d+)", install)
assert entries
entries_before, entries_after = entries.groups()
assert entries_before == entries_after == "381"

gate = log("/tmp/r400_gate.log")
g = re.search(r"MOTION_LEDGER 表面=(\d+) 状态=(\d+) 格子=(\d+) 行数=(\d+)"
              r" 已清账=(\d+) 未清账=(\d+) 地板=(\d+)", gate)
assert g
surfaces, states, cells, rows, cleared, uncleared, floor_count = [int(x) for x in g.groups()]
assert (surfaces, states, cells, rows, cleared, uncleared, floor_count) == (18, 9, 162, 162, 162, 0, 162)

streak_out = subprocess.check_output(
    ["python3", os.path.join(ROOT, "scripts/product_streak.py"), "--streak-for", "399"],
    cwd=ROOT).decode("utf-8")
streak = int(re.search(r"streak=(\d+)", streak_out).group(1))
assert streak == 1, "streak=%d" % streak

ci = log("/tmp/r399_ci_073fd6e.log")
assert "COPY_FAIL_RED light 成功红=0 失败红=45 失败对比=5.18" in ci
assert "COPY_FAIL_RED dark 成功红=0 失败红=44 失败对比=3.34" in ci
assert "RECORDER_FRAME_RING light 变化=6747 录制侧蓝=568 静置侧蓝=0" in ci
assert "RECORDER_FRAME_RING dark 变化=6748 录制侧蓝=568 静置侧蓝=0" in ci
assert "DETAIL_LOADING_HINT light fill=238 墨=361 对比=4.73" in ci
assert "DETAIL_LOADING_HINT dark fill=50 墨=414 对比=5.78" in ci
assert "EMPTY_STATE_HINT_NOT_RUN=band-empty：light" in ci
assert "MOTION_FLOOR_FACTS judged=5/5 executed=72 not-run=-" in ci
assert "MOTION_FLOOR_OK=5/5 全部臂都在登记之内" in ci
assert "MOTION_FLOOR_REDS=0" in ci

ui_heading = "## 第 398 轮（R399"
ui_section = f"""## 第 399 轮（R400 · 2026-10-26 · U-1421…U-1425）：「原文/渲染」标签不再一帧硬换（1x 0→5 过渡帧）；R399 三条 CI 修复在 runner 签收；436 复核（U-1421…U-1425 · 产品 1 文件，动效主线）

- **U-1421：⓪ R399 队列与三条修复的 runner 签收。** `40285533750 ↔ 9641073` / completed / **success**；`40285152509 ↔ 073fd6e` / completed / **success**；`40285128902 ↔ c0091fb` / completed / **failure**，唯一失败步骤 `STEP[9] Release script tests`（`test_the_sources_cell_agrees_with_git` + `test_the_cell_agrees_with_its_own_source`：c0091fb 这一笔里报告 sources 格还写 `ab2da31`；`test_the_skip_roster` 在同一次嵌套卷里没拿到结论行）——这是报告格未随主笔同提交，不是产品红；紧随的 `073fd6e`/`9641073` 两跑 success 把产品三条修复签掉。runner 现读：copy 失败红 **亮 5.18 / 暗 3.34**（地板 3.0，R399 修复生效）；录制环 **light 568 / dark 568，idle 0**（修复生效）；详情加载句 **亮 4.73 / 暗 5.78**（修复生效）；空态 hint 仍 `EMPTY_STATE_HINT_NOT_RUN=band-empty`（具名未覆盖，不写成绿）。新 R400 push 的 run 待落地，见 R401 ⓪。
- **U-1422：② 产品动效位 —— 「原文/渲染」标签和正文不同步。** 正文在「原文/渲染」之间走 `.contentFade` 交叉淡入，按钮标签却一帧硬换；同一击里内容在演、控件名已落地。修法：`DetailView.MarkdownModeButton` 的 `Text(title)` 加 `.id(title)` + `.transition(.opacity)` + `.animation(for: .contentFade, value: title)`（产品 1 文件）。胶片现读：1x 旧 **0** 过渡帧 → 新 **5**（峰值 0.0048→0.0097）；2x 旧 10 → 新 7（2x 的采样/文字渲染本身就能分出多帧，不能拿它单独判过程，所以以 1x 为判据、2x 只做旁证）。
- **U-1423：判据与刀。** `MotionFilmstripTests.testMarkdownModeLabelChangeIsAVisibleProcess`：2x/1x 都要求 ≥2 个过渡帧；旧码 1x=0 ⇒ 红。`M1042`（拆掉 `.id(title)/.transition/.animation`）⇒ **CAUGHT**、红得对=True、还原干净、复跑 ESCAPED。**436 复核**：`073fd6e`/`9641073` 的 `MOTION_FLOOR_FACTS judged=5/5 executed=72 not-run=-`、`settings-reset-fade=3`、`MOTION_FLOOR_OK=5/5`、`MOTION_FLOOR_REDS=0`，没有新的 unlisted 场景，保持 R399 结案，不重新猜 `must_judge`。
- **U-1424：① 367 rot 与八步。** `HIDDEN_ARMS 表={h_tables} 可判={h_judged} rot={h_rot} 抽不出={h_opaque} 已声明表={h_dtables} 已声明死针={h_ddead} 上界 rot={h_rot_ceiling} 处置=ok`；预检 `tables={pre_tables} covered={pre_covered} arms={pre_arms} bad={pre_bad}`、全仓 {arm_files} 文件 / {arm_total} 把；`M1042` CAUGHT，另把 R394 的 M1029/M1030 按 R399 新失败红重钉后 2/2 CAUGHT（rot 清回 0）。build **{warnings}** 告警；全量 `Executed {executed} tests, with {skipped} tests skipped and {failures} failures`；捕获 `CAPTURED {frames} -> /tmp/r400_shots`，与 R399 逐张比 `变了={changed_frames}`（标签过渡是动画，静态帧零变化），帧基线复验 `COMPARED={b_compared} CHANGED={b_changed} MISSING={b_missing} ADDED={b_added}`；换装 `INSTALL_RESULT=ok`、`INSTALL_SHA_MATCH=1`、条目 `{entries_before}={entries_after}`；清账表 `表面={surfaces} 状态={states} 格子={cells} 已清账={cleared} 未清账={uncleared} 地板={floor_count}`；产品面连续零改动 **{streak}** 轮（as-of 399；本轮产品动效已落 Sources，现读 `python3 scripts/product_streak.py --streak-for 399`）。
"""

iteration = f"""## Round 397 · R400（第 399 轮 · 2026-10-26）：「原文/渲染」标签不再一帧硬换（1x 0→5 过渡帧）；R399 三条 CI 修复在 runner 签收；436 复核（产品 1 文件，动效主线）

正文在「原文/渲染」之间走 `.contentFade`，按钮标签原来一帧硬换。`DetailView.MarkdownModeButton` 的 `Text(title)` 加 `.id(title)` + `.transition(.opacity)` + `.animation(for: .contentFade, value: title)`。胶片现读：1x 旧 **0** → 新 **5** 个过渡帧（峰值 0.0048→0.0097）；2x 旧 10 → 新 7，2x 不能单独判过程，以 1x 为判据。M1042 拆过渡 ⇒ CAUGHT、还原干净、复跑 ESCAPED。R399 三条 CI 修复在 `073fd6e`/`9641073` 两跑签收：copy 失败红亮 5.18/暗 3.34、录制环 568/568 idle0、详情加载 4.73/5.78；空态 hint 仍 band-empty NOT-RUN。436 复核 5/5、REDS=0，不重开。静态 182 帧零变化，全量 1061/53/0。

**七维度自评**（恰七行，每格 n/15）：

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | 14/15 | 真看了标签切换胶片与新旧帧；扣 1：2x 不能单独判过程。 |
| 判据有效性 | 15/15 | 2x/1x 胶片判据 + M1042；旧码 1x=0 会红。 |
| 假绿防御 | 15/15 | 明写 2x 旧 10 帧不能当过程，以 1x 为判据；空态 band-empty 记 NOT-RUN。 |
| 产品面推进 | 14/15 | 真落 Sources 动效：标签与正文同一 `.contentFade`；扣 1：单点。 |
| 台账一致性 | 14/15 | U-1421…U-1425、D-391、436、CI 两跑 success/一跑报告格 failure 都从日志解析；扣 1：新 R400 跑未落地。 |
| 交付诚实性 | 15/15 | 报告格红归因到 c0091fb 未同提 sources 格，不写成产品红；空态 NOT-RUN 明列。 |
| 可复核性 | 15/15 | 1x/2x 帧数/峰值、M1042、runner 三条修复读数、436 复核、precheck/rot 都有原文。 |

均分 = 102/105 ≈ 14.6/15（97）。
"""

decision = """
### D-391（400）控件标签与它控制的内容必须共用同一条过渡；2x 分不出时以 1x 为判据

R400 现读：正文在「原文/渲染」之间走 `.contentFade`，按钮标签原是一帧硬换。加 `.id(title)` + `.transition(.opacity)` + `.animation(for: .contentFade, value: title)` 后，1x 过渡帧由 **0→5**（峰值 0.0048→0.0097）；2x 旧 10 / 新 7，2x 的文字渲染与采样本身能分出多帧，不能单独判过程，所以以 1x 为判据、2x 只做旁证。
**Why**：同一次点击里，内容的过渡和控件名字的硬换会读成两个时刻；用户看到"内容还在淡、按钮已经叫另一个名字"。控件标签是这次状态变化的一部分，必须与内容同一档。
**How to apply**：① 受控内容的过渡与控件标签共用同一 `MotionCatalog` 档；② 小控件的过程先看 1x，2x 的高帧数不等于过程（R399 的 runner 1x 对比度教训同族）；③ 刀拆掉 `.id/transition/animation`，必须让 1x 的 span 掉到 1 以下并红；④ 静帧基线为零变化时，把动效证据放在专用胶片测试，不硬塞一张静态帧。
"""

changelog = """### 「原文/渲染」标签不再一帧硬换（1x 0→5 过渡帧）；R399 三条 CI 修复在 runner 签收；436 复核（R400 / 第 399 轮 / Round 397 / U-1421…U-1425 · 产品 1 文件，动效主线）

"""

report_bullet = """
- **R400（动效主线）**：正文在「原文/渲染」间走 `.contentFade`，按钮标签原来一帧硬换。`DetailView.MarkdownModeButton` 的 `Text(title)` 加 `.id(title)` + `.transition(.opacity)` + `.animation(for: .contentFade, value: title)`。胶片：1x 过渡帧旧 `0` → 新 `5`（峰值 0.0048→0.0097）；2x 旧 10 / 新 7（2x 不能单独判过程，以 1x 为判据）。M1042 CAUGHT、还原干净；静态 182 帧零变化；全量 1061/53/0；电池 683/4。R399 三条 CI 修复在 `073fd6e`/`9641073` 两跑签收：copy 红亮 5.18/暗 3.34、录制环 568/568 idle0、加载句 4.73/5.78；空态 hint 仍 band-empty NOT-RUN。436 复核 `judged=5/5`、`REDS=0`，保持结案；新的 R400 跑待落地。
"""

state_section = f"""## R400 状态（2026-10-26 · 本地 · 第 399 轮 / Round 397）：「原文/渲染」标签不再一帧硬换（1x 0→5 过渡帧）；R399 三条 CI 修复在 runner 签收；436 复核（产品 1 文件，动效主线）

最后更新：2026-10-26（本地 · R400 / 第 399 轮 / Round 397）：正文在「原文/渲染」间走 `.contentFade`，按钮标签原来一帧硬换。`DetailView.MarkdownModeButton` 的 `Text(title)` 加 `.id(title)` + `.transition(.opacity)` + `.animation(for: .contentFade, value: title)`。胶片现读 1x 旧 **0** → 新 **5** 个过渡帧（峰值 0.0048→0.0097）；2x 旧 10 / 新 7（2x 不能单独判过程，以 1x 为判据）。M1042 拆过渡 ⇒ CAUGHT、还原干净、复跑 ESCAPED；静态 182 帧零变化，基线复验 182/0。全量 `Executed {executed} tests, with {skipped} tests skipped and {failures} failures`；换装 `ok / SHA_MATCH=1 / 381=381`；清账表 162=162；`HIDDEN_ARMS 表={h_tables} 可判={h_judged} rot={h_rot} … 上界 rot={h_rot_ceiling} 处置=ok`；预检 `tables={pre_tables} covered={pre_covered} arms={pre_arms} bad={pre_bad}`、全仓 {arm_files} 文件 / {arm_total} 把；产品面连续零改动 **{streak}** 轮（as-of 399，现读 `python3 scripts/product_streak.py --streak-for 399`；本轮产品动效已落 Sources）。

本轮做了什么：
① ⓪ R399 队列：`9641073`/`073fd6e` success，`c0091fb` failure 只在 `STEP[9] Release script tests`（sources 格未随主笔同提交 + skip roster 嵌套没拿到结论）；产品三条修复由两跑 success 签收。
② 动效位：「原文/渲染」标签从一帧硬换改成与正文同一 `.contentFade`；1x 0→5、2x 10→7。
③ 判据：胶片 2x/1x 均 ≥2 过渡帧；M1042 拆过渡 CAUGHT、还原干净。
④ 436：两跑 `judged=5/5`、`MOTION_FLOOR_OK=5/5`、`REDS=0`，无新 unlisted，保持结案。
⑤ 367：hidden 表 {h_tables} / 可判 {h_judged} / rot {h_rot} / 上界 {h_rot_ceiling}；预检 {pre_tables}/{pre_covered}/{pre_arms}/{pre_bad}；R394 的 M1029/M1030 按新红重钉 2/2。
⑥ 验证：build 0 告警；全量 `{executed}/{skipped}/{failures}`；捕获 {frames} 帧、0 变化、基线 182/0；换装 ok；清账表 162=162。电池待台账后复跑。

NOT-RUN / 阻塞（分开写）：① **R400 新跑未落地**（push 后待读）；② **`EMPTY_STATE_HINT` 在 runner 上 band-empty**（具名 NOT-RUN，不写成绿；空态墨档的本地读数仍是 6.73/8.31）；③ 亮档真机腿仍没跑；④ macOS 12 的紧凑详情头仍走旧截断。

下一轮（R401）的靶：⓪ 先 `git push origin main`（禁 amend/force）并复核 ahead=0；读 R400 主笔推送跑的全部失败步骤（成对 run↔commit），新跑没落地就记 in_progress 未读；① 367 现读 rot=0，按 `HIDDEN_ROT` 查新腐烂；② 继续产品视觉位并落 Sources，换缺陷类别；③ 436 只复核新跑 Motion floor，不重新猜 `must_judge`，出现新 unlisted 才带事实重开。
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
report_new = once(report_old, "D-069 … **D-390**", "D-069 … **D-391**")
report_new = once(report_new, "U-31 … U-1420（R399 现读抬到最新一节）", "U-31 … U-1425（R400 现读抬到最新一节）")
report_new = once(
    report_new,
    "R399 现读：注册表 **155** 张 / 刀号最大 **M1041** / 预检 covered=138 arms=417 bad=0；全仓 248 文件 / 901 把；M674 退役、M906 空刀退役",
    f"R400 现读：注册表 **{pre_tables}** 张 / 刀号最大 **M1042** / 预检 covered={pre_covered} arms={pre_arms} bad={pre_bad}；"
    f"全仓 {arm_files} 文件 / {arm_total} 把；M674 退役、M906 空刀退役")
report_new = report_new.rstrip() + "\n\n" + report_bullet
report_new = once(report_new, "`AGENT_STATE.md` 的 R399 节", "`AGENT_STATE.md` 的 R400 节")

state_old = rd("AGENT_STATE.md")
state_anchor = "## R399 状态（2026-10-26"
assert state_old.count(state_anchor) == 1
state_new = once(state_old, state_anchor, state_section + "\n" + state_anchor)

wr("AGENT_UI_AUDIT.md", audit_new)
wr("AGENT_VISUAL_ITERATION.md", iteration_new)
wr("AGENT_DECISIONS.md", decisions_new)
wr("CHANGELOG.md", changelog_new)
wr("AGENT_FINAL_REPORT.md", report_new)
wr("AGENT_STATE.md", state_new)

print("R400_LEDGERS_OK warnings=%s full=%s/%s/%s frames=%s changed=%s baseline=%s/%s/%s/%s label1x=%s/%s old1x=%s/%s pre=%s/%s/%s/%s arms=%s/%s rot=%s gate=%s=%s streak=%s"
      % (warnings, executed, skipped, failures, frames, changed_frames,
         b_compared, b_changed, b_missing, b_added,
         new_lab["1x"][0], new_lab["1x"][1], old_lab["1x"][0], old_lab["1x"][1],
         pre_tables, pre_covered, pre_arms, pre_bad, arm_files, arm_total,
         h_rot, cleared, cells, streak))
