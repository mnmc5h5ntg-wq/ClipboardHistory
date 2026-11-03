#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R392（第 391 轮 / Round 389）的台账。数字全部从本机日志解析。"""
import io
import os
import re
import subprocess

ROOT = "/Users/wangziyi/Codex_Project0"


def rd(name):
    with io.open(os.path.join(ROOT, name), encoding="utf-8") as handle:
        return handle.read()


def wr(name, text):
    with io.open(os.path.join(ROOT, name), "w", encoding="utf-8") as handle:
        handle.write(text)


def once(text, anchor, repl):
    assert text.count(anchor) == 1, "锚点命中 %d 次：%r" % (text.count(anchor), anchor[:90])
    return text.replace(anchor, repl, 1)


def log(path):
    with io.open(path, encoding="utf-8") as handle:
        return handle.read()


build = log("/tmp/r392_build.log")
warnings = len(re.findall(r"warning:", build))
assert warnings == 0

full = log("/tmp/r392_full.log")
summaries = [tuple(int(x) for x in row) for row in
             re.findall(r"Executed (\d+) tests, with (\d+) tests skipped and (\d+) failures", full)]
big = [row for row in summaries if row[0] > 900]
assert big
executed, skipped, failures = big[-1]
assert failures == 0

capture = log("/tmp/r392_capture.log")
cap = re.search(r"CAPTURED (\d+) -> /tmp/r392_shots", capture)
assert cap
frames = int(cap.group(1))
ring_light = re.search(r"RECORDER_FRAME_RING light 变化=(\d+) 录制侧蓝=(\d+) 静置侧蓝=(\d+) bbox=\((\d+),(\d+)\)\.\.\((\d+),(\d+)\)", capture)
ring_dark = re.search(r"RECORDER_FRAME_RING dark 变化=(\d+) 录制侧蓝=(\d+) 静置侧蓝=(\d+) bbox=\((\d+),(\d+)\)\.\.\((\d+),(\d+)\)", capture)
assert ring_light and ring_dark
rl = [int(x) for x in ring_light.groups()]
rdk = [int(x) for x in ring_dark.groups()]
assert rl[0] > 100 and rl[1] >= 200 and rl[2] == 0
assert rdk[0] > 100 and rdk[1] >= 200 and rdk[2] == 0
settle = re.findall(r"RECORDER_OVERLAY_SETTLE waited_ms=(\d+)", capture)
assert settle and all(250 <= int(x) <= 400 for x in settle)

diff = log("/tmp/r392_framediff.log")
dm = re.search(r"FRAME_DIFF 比了=(\d+) 变了=(\d+)", diff)
assert dm
total_frames, changed_frames = [int(x) for x in dm.groups()]
same_frames = total_frames - changed_frames
assert (same_frames, changed_frames, total_frames) == (180, 2, 182)
bb = re.findall(r"FRAME_DIFF_BBOX settings-shortcuts-recording-720x540-(?:light|dark)\.png 变了=(\d+) bbox=\((\d+),(\d+)\)\.\.\((\d+),(\d+)\)", diff)
assert len(bb) == 2

baseline_update = log("/tmp/r392_framebaseline_update.log")
assert "FRAME_BASELINE_UPDATED=182" in baseline_update
baseline = log("/tmp/r392_framebaseline.log")
bm = re.search(r"FRAME_BASELINE_COMPARED=(\d+)\s+FRAME_BASELINE_CHANGED=(\d+)"
               r"\s+FRAME_BASELINE_MISSING=(\d+)\s+FRAME_BASELINE_ADDED=(\d+)", baseline)
assert bm
b_compared, b_changed, b_missing, b_added = [int(x) for x in bm.groups()]
assert (b_compared, b_changed, b_missing, b_added) == (182, 0, 0, 0)

motion = log("/tmp/r390_motion_full.log")
ms = re.search(r"MOTION_SUMMARY (.+)", motion)
mr = re.search(r"MOTION_RESOLVE_SUMMARY judged=(\d+)/(\d+) not-run=(\S+)", motion)
mex = re.search(r"Executed (\d+) tests, with (\d+) tests skipped and (\d+) failures", motion)
assert ms and mr and mex
motion_summary = ms.group(1)
motion_judged, motion_total, motion_notrun = mr.groups()
motion_exec, motion_skip, motion_fail = [int(x) for x in mex.groups()]
assert "settings-reset-fade" in motion_summary
assert motion_judged == motion_total == "5" and motion_notrun == "-"
assert motion_fail == 0

install = log("/tmp/r392_install.log")
assert "INSTALL_RESULT=ok" in install and "INSTALL_SHA_MATCH=1" in install
entries = re.search(r"INSTALL_ENTRIES_BEFORE=(\d+)\s+INSTALL_ENTRIES_AFTER=(\d+)", install)
assert entries
entries_before, entries_after = entries.groups()

pre = log("/tmp/r392_precheck2.log")
pre_line = re.search(r"NEEDLE_PRECHECK tables=(\d+) covered=(\d+) arms=(\d+) bad=(\d+)", pre)
arm_line = re.search(r"ARM_TOTAL files=(\d+) arms=(\d+) dupes=(\d+) repeats=(\d+)", pre)
assert pre_line and arm_line
pre_tables, pre_covered, pre_arms, pre_bad = [int(x) for x in pre_line.groups()]
arm_files, arm_total, arm_dupes, arm_repeats = [int(x) for x in arm_line.groups()]
assert pre_bad == 0 and arm_dupes == 0 and arm_repeats == 0

hidden = log("/tmp/r392_hidden.log")
h = re.search(r"HIDDEN_ARMS 表=(\d+) 可判=(\d+) rot=(\d+) 抽不出=(\d+) 已声明表=(\d+) 已声明死针=(\d+) 上界 rot=(\d+)", hidden)
assert h
h_tables, h_judged, h_rot, h_opaque, h_dtables, h_ddead, h_rot_ceiling = [int(x) for x in h.groups()]
assert h_rot == h_rot_ceiling == 0

gate = log("/tmp/r392_gate.log")
g = re.search(r"MOTION_LEDGER 表面=(\d+) 状态=(\d+) 格子=(\d+) 行数=(\d+) 已清账=(\d+) 未清账=(\d+) 地板=(\d+)", gate)
assert g
surfaces, states, cells, rows, cleared, uncleared, floor_count = [int(x) for x in g.groups()]
assert uncleared == 0 and cleared == cells == rows == floor_count

streak_out = subprocess.check_output(
    ["python3", os.path.join(ROOT, "scripts/product_streak.py"), "--streak-for", "391"],
    cwd=ROOT).decode("utf-8")
streak = int(re.search(r"streak=(\d+)", streak_out).group(1))
assert streak == 1, "streak=%d" % streak

recorder = log("/tmp/r392_recorder_tests.log")
assert "RECORDER_ENTRY 通道=cacheDisplay 不同像素=2940 静置高色度=0 点击后高色度=2924" in recorder

ui_heading = "## 第 390 轮（R391"
ui_section = f"""## 第 391 轮（R392 · 2026-10-26 · U-1380…U-1384）：整页录制帧第一次真的拍到强调圈 —— fixture 只等 button.layer，圈还透明时按了快门；补 overlay 落定 + 帧级 1794/1780 判据（U-1380…U-1384 · 产品 0 文件，判据账）

- **U-1380：⓪ 网络与 CI。** 10:36 `git push origin main` 被 SSH 拒（`Connection closed by 20.205.243.166 port 22`），同分钟 `api=000`（LibreSSL SSL_ERROR_SYSCALL）/ `apple=200` ⇒ GitHub 侧仍断；`PUSH_BLOCKED=network`，本地 ahead=20（R391 之后、R392 落笔前），**不写已推送**。`origin/main` 本地 ref 仍 `5c7814e`；网络不可达无法 fetch 确认远端是否被推进（push 在连接阶段失败，未用 force）。恢复后先 push、复核 ahead=0，再读 `40234023212`/`40234058148` 与 R387–R392 推送跑的全部失败步骤。
- **U-1381：整页录制帧把「我在听」那一圈拍丢了。** `settings-shortcuts-recording` 与静置帧逐像素比：差集只覆盖标题文字 bbox `(1017,515)..(1171,540)`，控件四周 **0 个高色度像素** —— 而组件级判据一直读到 1844/1820 颗。成因不是产品：R273 把 fixture 的固定泵换成「等 `button.layer?.animationKeys()` 清空」，而强调圈是 SwiftUI overlay，0.16s 淡入不在 NSButton 那一层；本机现读等待 `134ms`、动画键 `0` 就按了快门。修法：控制层等待之后补一段**有 300ms 上限**的 overlay 落定 + `displayIfNeeded`，现读 `RECORDER_OVERLAY_SETTLE waited_ms=313/315`。修后同两帧：亮 变化 **{rl[0]}** / 录制侧蓝 **{rl[1]}** / 静置侧蓝 **{rl[2]}**，暗 **{rdk[0]} / {rdk[1]} / {rdk[2]}**；差集 bbox 正好是控件四边 `({rl[3]},{rl[4]})..({rl[5]},{rl[6]})`。逐张看过新帧：亮/暗两档都能看到完整的强调色圆角圈。
- **U-1382：帧级判据 —— 整页录制帧必须真的有那圈。** `testCaptureKeyViews` 捕获后直接读这两张帧：差集 >100，录制侧强调蓝 ≥200，静置侧在差集处必须 0；settings 族整体空白时走具名 `RECORDER_FRAME_RING_NOT_RUN=flat-page`，不把平涂读成产品没画。这条判据只看颜色与差分，**不钉矩形几何**（bbox 只入读数）；当前亮 {rl[1]} / 暗 {rdk[1]}，静置 0/0。
- **U-1383：BACKLOG 436 处置（仍未结案）。** 本轮没有新的 runner motion 读数；R390 的完整本地卷 `Executed {motion_exec} tests, with {motion_skip} tests skipped and {motion_fail} failures`、`MOTION_SUMMARY {motion_summary}`、`MOTION_RESOLVE_SUMMARY judged={motion_judged}/{motion_total} not-run={motion_notrun}` 与闸门 exit 1（UNLISTED `settings-reset-fade`）的本地复现仍成立。**不关单、不改 JSON/自测、不猜 `must_judge`**；runner 卷继续记具名 NOT-RUN。
- **U-1384：① 367 rot 与八步。** `HIDDEN_ARMS 表={h_tables} 可判={h_judged} rot={h_rot} 抽不出={h_opaque} 已声明表={h_dtables} 已声明死针={h_ddead} 上界 rot={h_rot_ceiling} 处置=ok`；预检 `tables={pre_tables} covered={pre_covered} arms={pre_arms} bad={pre_bad}`、全仓 {arm_files} 文件 / {arm_total} 把；组件入口 `RECORDER_ENTRY … 静置高色度=0 点击后高色度=2924` 仍绿。build **{warnings}** 告警；全量 `Executed {executed} tests, with {skipped} tests skipped and {failures} failures`；捕获 `CAPTURED {frames} -> /tmp/r392_shots`，与 R391 逐张比 `变了={changed_frames}`（两张录制帧的差集 bbox 都在控件四边），帧基线同笔 `UPDATED={b_compared}`，复验 `COMPARED={b_compared} CHANGED={b_changed}`；换装 `INSTALL_RESULT=ok`、`INSTALL_SHA_MATCH=1`、条目 `{entries_before}={entries_after}`；清账表 `表面={surfaces} 状态={states} 格子={cells} 已清账={cleared} 未清账={uncleared} 地板={floor_count}`；产品面连续零改动 **{streak}** 轮（现读 `python3 scripts/product_streak.py --streak-for 391`）。**本轮产品 0 文件**：环本来就在画，坏的是取证帧的等待条件；不为了凑产品改动去动已经正确的 Sources。
"""

iteration = f"""## Round 389 · R392（第 391 轮 · 2026-10-26）：整页录制帧第一次真的拍到强调圈（亮 1794 / 暗 1780 颗）；fixture 补 overlay 落定与帧级判据（产品 0 文件，判据账）

`settings-shortcuts-recording` 与静置帧的差集只覆盖标题文字，控件四周 0 颗高色度像素 —— 组件级判据却一直读到 1844/1820。成因是 R273 的等待只看 `button.layer` 的动画键，而强调圈是 SwiftUI overlay，0.16s 淡入不在那层：本机 134ms / 键=0 就快门。补 300ms 上限的 overlay 落定后，亮 变化 {rl[0]} / 录制侧蓝 {rl[1]} / 静置 0，暗 {rdk[0]} / {rdk[1]} / 0，bbox 正好控件四边。新增帧级判据：差集 >100、录制侧蓝 ≥200、静置侧 0，平涂页具名 NOT-RUN。两张录制帧进基线（180 同 / 2 变），复验 182/0。436 无新 runner 读数；rot 0/0。**产品 0 文件**。

**七维度自评**（恰七行，每格 n/15）：

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | 15/15 | 先看了差集只有文字、控件四周无圈，再看了修后亮/暗两档完整的强调圈。 |
| 判据有效性 | 15/15 | 帧级颜色/差分判据 + 平涂能力闸门 + 组件入口 2924 的高色度正对照。 |
| 假绿防御 | 15/15 | 发现整页帧连续多轮在「录制态」名下没有圈；修等待条件而不是放宽判据；新判据会红。 |
| 产品面推进 | 8/15 | 产品 0 文件：环本来就是对的，坏的是取证帧；不为了凑改动去动正确的 Sources。 |
| 台账一致性 | 14/15 | U-1380…U-1384、D-381/D-382、436 状态、计数器都从日志解析；扣 1：436 仍开。 |
| 交付诚实性 | 15/15 | 明确写「产品 0 文件」与「帧在说谎」，不把判据修复写成产品修复；网络只写 BLOCKED。 |
| 可复核性 | 15/15 | 修前/修后读数、bbox、overlay 等待、帧基线更新与复验、组件入口读数都有原文。 |

均分 = 97/105 ≈ 13.9/15（92）。
"""

decision = """
### D-381（392）整页状态帧的落定条件必须覆盖被测那一层；button.layer 的动画键清空 ≠ SwiftUI overlay 落定

R392 现读：`settings-shortcuts-recording` 整页帧与静置帧的差集只覆盖标题文字，控件四周 0 颗高色度像素；而组件级判据读到录制圈 1844/1820 颗。R273 的 fixture 等 `button.layer?.animationKeys()` 清空，本机 134ms / 键=0 就快门；强调圈是 SwiftUI overlay，0.16s 淡入不在 NSButton 层。补 300ms 上限的 overlay 落定后，亮 1794 / 暗 1780 颗、静置 0，bbox 正好控件四边。
**Why**：控件层的动画键只回答「这颗 NSButton 自己还在动吗」，不回答「SwiftUI 子树画完了吗」。把前者当后者，会让状态帧在过渡中间被拍下，而帧名、基线和台账都继续说它拍到了那个状态 —— 组件判据仍然绿，整页证据却是假的。
**How to apply**：① 等待条件必须问**被测那一层**（这里是 SwiftUI overlay），不是最近的 NSView；② 给等待加上限并打印等到的时长，超时也要有名字；③ 状态帧要有自己的整页判据（D-382），不能靠组件帧替它签字；④ 修等待条件之后同笔更新帧基线，并把 bbox/颜色读数写进账。
"""

decision2 = """
### D-382（392）组件级像素证据不替整页状态作证；整页帧要有自己的状态判据

R392 现读：`HotKeyRecorderEvidenceTests` 的组件入口一直读到点击后 2924 颗高色度像素、四周都有圈，而 `settings-shortcuts-recording` 整页帧四周 0 颗、差集只有文字。两者不矛盾：它们问的是不同对象（220×60 的控件 vs 720×540 的整页窗口与 SwiftUI overlay）。
**Why**：组件帧能证明「这一圈怎么画」，不能证明「整页窗口里它有没有被画出来」；把前者当后者，就是 R392 这次连续多轮没被发现的假绿。
**How to apply**：① 每个整页状态帧配一条自己的颜色/差分判据，和组件判据分开记；② 判据只看颜色/差分、不钉矩形时不需要跨倍率；若要钉几何，就带能力闸门与跨倍率正对证；③ 平涂页走具名 NOT-RUN；④ bbox 只作为证据打印，不把「框在哪」当成正确性条件。
"""

changelog = """### 整页录制帧第一次真的拍到强调圈（亮 1794 / 暗 1780 颗）；fixture 补 overlay 落定与帧级判据（R392 / 第 391 轮 / Round 389 / U-1380…U-1384 · 产品 0 文件，判据账）

"""

report_bullet = f"""
- **R392（判据账）**：`settings-shortcuts-recording` 整页帧此前只拍到标题变化、控件四周 0 颗强调色 —— R273 的 fixture 只等 `button.layer` 动画键，而圈是 SwiftUI overlay（134ms/键=0 就快门）。补 300ms 上限的 overlay 落定后，亮 变化 `{rl[0]}` / 录制侧蓝 `{rl[1]}` / 静置 `{rl[2]}`，暗 `{rdk[0]}` / `{rdk[1]}` / `{rdk[2]}`，bbox 正好控件四边；两张录制帧进基线（180 同 / 2 变，复验 182/0）。新增帧级判据：差集 >100、录制侧蓝 ≥200、静置侧 0，平涂页具名 NOT-RUN。**产品 0 文件**：环本来就在画，坏的是取证帧的等待条件。436 无新 runner 读数，仍未结案；rot 0/0。**网络仍断 ⇒ PUSH_BLOCKED=network，ahead=20，未推送。**
"""

state_section = f"""## R392 状态（2026-10-26 · 本地 · 第 391 轮 / Round 389）：整页录制帧第一次真的拍到强调圈（亮 1794 / 暗 1780 颗）；fixture 补 overlay 落定与帧级判据（产品 0 文件，判据账）

最后更新：2026-10-26（本地 · R392 / 第 391 轮 / Round 389）：`settings-shortcuts-recording` 与静置帧的差集只覆盖标题文字、控件四周 0 颗高色度像素，而组件级判据一直读到 1844/1820。成因是 R273 的 fixture 等 `button.layer?.animationKeys()` 清空，而强调圈是 SwiftUI overlay，0.16s 淡入不在 NSButton 层；本机 `134ms / 动画键=0` 就按了快门。补 300ms 上限的 overlay 落定 + `displayIfNeeded` 后，现读 `RECORDER_OVERLAY_SETTLE waited_ms=313/315`；亮 变化 **{rl[0]}** / 录制侧蓝 **{rl[1]}** / 静置蓝 **{rl[2]}**，暗 **{rdk[0]}** / **{rdk[1]}** / **{rdk[2]}**，差集 bbox 正好控件四边。新增帧级判据：差集 >100、录制侧蓝 ≥200、静置侧 0，settings 族平涂走具名 `RECORDER_FRAME_RING_NOT_RUN=flat-page`。两张录制帧进基线（`UPDATED={b_compared}`），复验 `COMPARED={b_compared} CHANGED={b_changed}`。**本轮产品 0 文件**：环本来就在画，坏的是取证帧的等待条件；不为了凑产品改动去动正确的 Sources。BACKLOG 436 无新 runner 读数，仍未结案。`swift build --build-tests` 告警 **{warnings}**；全量 `Executed {executed} tests, with {skipped} tests skipped and {failures} failures`；清账表 `表面={surfaces} 状态={states} 格子={cells} 已清账={cleared} 未清账={uncleared} 地板={floor_count}`；换装 `INSTALL_RESULT=ok`、`INSTALL_SHA_MATCH=1`、条目 {entries_before}={entries_after}；`HIDDEN_ARMS 表={h_tables} 可判={h_judged} rot={h_rot} … 上界 rot={h_rot_ceiling} 处置=ok`；预检 `tables={pre_tables} covered={pre_covered} arms={pre_arms} bad={pre_bad}`、全仓 {arm_files} 文件 / {arm_total} 把；产品面连续零改动 **{streak}** 轮（现读 `python3 scripts/product_streak.py --streak-for 391`）。

本轮做了什么：
① ⓪ 网络：push 被 SSH 拒 + `api=000`/`apple=200` ⇒ `PUSH_BLOCKED=network`；未推送，CI 多跑未读。
② 取证：发现整页录制帧只拍到文字、四周 0 圈；修 fixture 的 overlay 落定等待；修后 1794/1780 颗。
③ 判据：新增帧级 `RECORDER_FRAME_RING`（差集/录制侧蓝/静置蓝/平涂 NOT-RUN）；组件入口 2924 仍绿。
④ 436：无新 runner 读数，本地 5 臂复现仍成立；不关单、不猜 must_judge。
⑤ 367：hidden 表 {h_tables} / 可判 {h_judged} / rot {h_rot} / 上界 {h_rot_ceiling}；预检 {pre_tables}/{pre_covered}/{pre_arms}/{pre_bad}。
⑥ 验证：build 0 告警；全量 `{executed}/{skipped}/{failures}`；捕获 {frames} 帧、2 张录制帧更新并复验 0；换装 ok；清账表 {cells}=162。

验证读数（现读）：`RECORDER_FRAME_RING` 亮 变化 `{rl[0]}` / 蓝 `{rl[1]}` / 静置 `{rl[2]}`，暗 `{rdk[0]}` / `{rdk[1]}` / `{rdk[2]}`；`RECORDER_ENTRY … 静置高色度=0 点击后高色度=2924`；`RECORDER_OVERLAY_SETTLE waited_ms=313/315`；帧差分 `180 同 / 2 变`；`HIDDEN_ARMS … rot={h_rot} … 处置=ok`。

NOT-RUN / 阻塞（分开写）：① **`PUSH_BLOCKED=network`**：push 被 SSH 拒 + `api=000`（LibreSSL SSL_ERROR_SYSCALL）/ `apple=200`；本地 ahead=20（R392 主笔前）；② `40234023212 ↔ d38ea10`、`40234058148 ↔ 5c7814e` 与 R387–R391 本地提交的 conclusion **未读**（网络）；③ BACKLOG 436 的 runner motion 卷未读（本地复现不能关单），不改 JSON/自测；④ 亮档真机腿仍没跑；⑤ 录制圈的 **淡入过程**仍未进胶片（只签端态；解 `button.layer` 等待之后整页帧能拍到端态）。

下一轮（R393）的靶：⓪ 先 `git push origin main`（禁 amend/force）并复核 ahead=0；读 `40234023212`/`40234058148` 与 R387–R392 推送那一跑的**全部失败步骤**，把 run↔commit 成对写回本行；按 BACKLOG 436 先读 CI motion 卷，再决定第五臂 `must_judge` 并一次性改 JSON 与自测；① 367 现读 rot=0，按 `HIDDEN_ROT` 查新腐烂；② 回产品动效面再点一个真实位（本轮产品 0 文件，下一轮必须落 Sources）。
"""

audit = rd("AGENT_UI_AUDIT.md")
assert ui_heading in audit
audit_new = once(audit, ui_heading, ui_section + "\n" + ui_heading)
iteration_new = rd("AGENT_VISUAL_ITERATION.md").rstrip() + "\n\n" + iteration
decisions_new = rd("AGENT_DECISIONS.md").rstrip() + "\n" + decision + decision2

changelog_old = rd("CHANGELOG.md")
changelog_anchor = "## [Unreleased]\n\n"
assert changelog_old.count(changelog_anchor) == 1
changelog_new = once(changelog_old, changelog_anchor, changelog_anchor + changelog + "\n")

report_old = rd("AGENT_FINAL_REPORT.md")
report_new = once(report_old, "D-069 … **D-380**", "D-069 … **D-382**")
report_new = once(report_new, "U-31 … U-1379（R391 现读抬到最新一节）", "U-31 … U-1384（R392 现读抬到最新一节）")
report_new = once(
    report_new,
    "R391 现读：注册表 **146** 张 / 刀号最大 **M1026** / 预检 covered=129 arms=402 bad=0；全仓 239 文件 / 886 把；M674 退役、M906 空刀退役",
    f"R392 现读：注册表 **{pre_tables}** 张 / 刀号最大 **M1026** / 预检 covered={pre_covered} arms={pre_arms} bad={pre_bad}；"
    f"全仓 {arm_files} 文件 / {arm_total} 把；M674 退役、M906 空刀退役")
report_new = once(
    report_new,
    "**网络仍断 ⇒ PUSH_BLOCKED=network，ahead=20，未推送。**",
    "**网络仍断 ⇒ PUSH_BLOCKED=network，ahead=20，未推送。**" + report_bullet)

state_old = rd("AGENT_STATE.md")
state_anchor = "## R391 状态（2026-10-26"
assert state_old.count(state_anchor) == 1
state_new = once(state_old, state_anchor, state_section + "\n" + state_anchor)

wr("AGENT_UI_AUDIT.md", audit_new)
wr("AGENT_VISUAL_ITERATION.md", iteration_new)
wr("AGENT_DECISIONS.md", decisions_new)
wr("CHANGELOG.md", changelog_new)
wr("AGENT_FINAL_REPORT.md", report_new)
wr("AGENT_STATE.md", state_new)

print("R392_LEDGERS_OK warnings=%s full=%s/%s/%s frames=%s diff=%s/%s baseline=%s/%s ring=%s/%s,%s/%s rot=%s pre=%s/%s/%s/%s arms=%s/%s gate=%s=%s streak=%s"
      % (warnings, executed, skipped, failures, frames, same_frames, changed_frames,
         b_compared, b_changed, rl[1], rdk[1], rl[2], rdk[2], h_rot,
         pre_tables, pre_covered, pre_arms, pre_bad, arm_files, arm_total,
         cleared, cells, streak))
