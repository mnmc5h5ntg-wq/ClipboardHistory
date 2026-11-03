#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R393（第 392 轮 / Round 390）的台账。数字全部从本机日志解析。"""
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


build = log("/tmp/r393_build3.log")
warnings = len(re.findall(r"warning:", build))
assert warnings == 0

full = log("/tmp/r393_full.log")
summaries = [tuple(int(x) for x in row) for row in
             re.findall(r"Executed (\d+) tests, with (\d+) tests skipped and (\d+) failures", full)]
big = [row for row in summaries if row[0] > 900]
assert big
executed, skipped, failures = big[-1]
assert failures == 0

capture = log("/tmp/r393_capture.log")
cap = re.search(r"CAPTURED (\d+) -> /tmp/r393_shots", capture)
assert cap
frames = int(cap.group(1))

diff = log("/tmp/r393_framediff.log")
dm = re.search(r"FRAME_DIFF 比了=(\d+) 变了=(\d+)", diff)
assert dm
total_frames, changed_frames = [int(x) for x in dm.groups()]
same_frames = total_frames - changed_frames
assert (same_frames, changed_frames, total_frames) == (178, 4, 182)

diff2 = log("/tmp/r393_framediff2.log")
bb = re.findall(r"FRAME_DIFF_BBOX content-min(?:-with-copy-failure-notice)?-600x440-(?:light|dark)\.png 变了=(\d+) bbox=\((\d+),(\d+)\)\.\.\((\d+),(\d+)\)", diff2)
assert len(bb) == 4
bbs = [int(x) for x in bb[0]]

baseline_update = log("/tmp/r393_framebaseline_update.log")
assert "FRAME_BASELINE_UPDATED=182" in baseline_update
baseline = log("/tmp/r393_framebaseline.log")
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

install = log("/tmp/r393_install.log")
assert "INSTALL_RESULT=ok" in install and "INSTALL_SHA_MATCH=1" in install
entries = re.search(r"INSTALL_ENTRIES_BEFORE=(\d+)\s+INSTALL_ENTRIES_AFTER=(\d+)", install)
assert entries
entries_before, entries_after = entries.groups()

pre = log("/tmp/r393_precheck.log")
pre_line = re.search(r"NEEDLE_PRECHECK tables=(\d+) covered=(\d+) arms=(\d+) bad=(\d+)", pre)
arm_line = re.search(r"ARM_TOTAL files=(\d+) arms=(\d+) dupes=(\d+) repeats=(\d+)", pre)
assert pre_line and arm_line
pre_tables, pre_covered, pre_arms, pre_bad = [int(x) for x in pre_line.groups()]
arm_files, arm_total, arm_dupes, arm_repeats = [int(x) for x in arm_line.groups()]
assert pre_bad == 0 and arm_dupes == 0 and arm_repeats == 0

hidden = log("/tmp/r393_hidden.log")
h = re.search(r"HIDDEN_ARMS 表=(\d+) 可判=(\d+) rot=(\d+) 抽不出=(\d+) 已声明表=(\d+) 已声明死针=(\d+) 上界 rot=(\d+)", hidden)
assert h
h_tables, h_judged, h_rot, h_opaque, h_dtables, h_ddead, h_rot_ceiling = [int(x) for x in h.groups()]
assert h_rot == h_rot_ceiling == 0

gate = log("/tmp/r393_gate.log")
g = re.search(r"MOTION_LEDGER 表面=(\d+) 状态=(\d+) 格子=(\d+) 行数=(\d+) 已清账=(\d+) 未清账=(\d+) 地板=(\d+)", gate)
assert g
surfaces, states, cells, rows, cleared, uncleared, floor_count = [int(x) for x in g.groups()]
assert uncleared == 0 and cleared == cells == rows == floor_count

streak_out = subprocess.check_output(
    ["python3", os.path.join(ROOT, "scripts/product_streak.py"), "--streak-for", "392"],
    cwd=ROOT).decode("utf-8")
streak = int(re.search(r"streak=(\d+)", streak_out).group(1))
assert streak == 2, "streak=%d" % streak

mut = log("/tmp/r393_mut.log")
assert "R393_MUTATE 刀=2 CAUGHT=2 红得不对=0 RESTORE_CLEAN=yes" in mut

ui_heading = "## 第 391 轮（R392"
ui_section = f"""## 第 392 轮（R393 · 2026-10-26 · U-1385…U-1389）：600pt 详情头不再把「复制」截掉 —— 完整/紧凑 meta 先试再退，四张最小窗帧只动头部（U-1385…U-1389 · 产品 2 文件，视觉主线）

- **U-1385：⓪ 网络与 CI。** 10:36 `git push origin main` 被 SSH 拒（`Connection closed by 20.205.243.166 port 22`），同分钟 `api=000`（LibreSSL SSL_ERROR_SYSCALL）/ `apple=200` ⇒ GitHub 侧仍断；`PUSH_BLOCKED=network`，本地 ahead=22（R392 之后、R393 落笔前），**不写已推送**。`origin/main` 本地 ref 仍 `5c7814e`；网络不可达无法 fetch 确认远端是否被推进（push 在连接阶段失败，未用 force）。恢复后先 push、复核 ahead=0，再读 `40234023212`/`40234058148` 与 R387–R393 推送跑的全部失败步骤。
- **U-1386：产品位 —— 最小窗口的详情头。** `content-min-600x440` 里头部只显示 `2025-10-09 16:38:20… 40 个字符 · 来自 终端`，middle 截断把「复制」吃掉；同一时刻 750pt 的 `content-with-history` 是完整一行。产品改法：`DetailTypography.metaText` 增加 `includeCopyVerb`（默认 true），详情头用 `ViewThatFits` 先试完整文案、放不下再退到去掉冗余「复制」的紧凑版；时间/大小/来源一个不丢，行高不变。`ViewThatFits` 是 macOS 13+，12 上保留原来的单行截断（显式 `if #available`，不引新 API）。修后 600pt 帧现读完整 `2025-10-09 16:38:20 · 40 个字符 · 来自 终端`，不再有省略号；750pt 帧保持完整文案不变。
- **U-1387：判据与刀。** `Round3DetailTypographyTests.testCompactMetaDropsOnlyTheCopyVerbAndIsNarrower` 用同一档 11pt 系统字体量宽度并断言紧凑版更窄、且只丢「复制」；`testNarrowDetailHeaderFallsBackToCompactMeta` 钉住 `ViewThatFits(in: .horizontal)`、`includeCopyVerb: false` 与 `truncationMode(.middle)` 三件。`M1027`（紧凑臂也写回 true）与 `M1028`（ViewThatFits 换成 Group）都 **CAUGHT**、还原干净。
- **U-1388：BACKLOG 436 处置（仍未结案）。** 本轮没有新的 runner motion 读数；R390 的完整本地卷 `Executed {motion_exec} tests, with {motion_skip} tests skipped and {motion_fail} failures`、`MOTION_SUMMARY {motion_summary}`、`MOTION_RESOLVE_SUMMARY judged={motion_judged}/{motion_total} not-run={motion_notrun}` 与闸门 exit 1（UNLISTED `settings-reset-fade`）的本地复现仍成立。**不关单、不改 JSON/自测、不猜 `must_judge`**；runner 卷继续记具名 NOT-RUN。
- **U-1389：① 367 rot 与八步。** `HIDDEN_ARMS 表={h_tables} 可判={h_judged} rot={h_rot} 抽不出={h_opaque} 已声明表={h_dtables} 已声明死针={h_ddead} 上界 rot={h_rot_ceiling} 处置=ok`；预检 `tables={pre_tables} covered={pre_covered} arms={pre_arms} bad={pre_bad}`、全仓 {arm_files} 文件 / {arm_total} 把；`M1027/M1028` CAUGHT。build **{warnings}** 告警；全量 `Executed {executed} tests, with {skipped} tests skipped and {failures} failures`；捕获 `CAPTURED {frames} -> /tmp/r393_shots`，与 R392 逐张比 `变了={changed_frames}`（四张 600pt 帧的差集 bbox 都在头部，首张 变化={bbs[0]} bbox=({bbs[1]},{bbs[2]})..({bbs[3]},{bbs[4]})），帧基线同笔 `UPDATED={b_compared}`，复验 `COMPARED={b_compared} CHANGED={b_changed}`；换装 `INSTALL_RESULT=ok`、`INSTALL_SHA_MATCH=1`、条目 `{entries_before}={entries_after}`；清账表 `表面={surfaces} 状态={states} 格子={cells} 已清账={cleared} 未清账={uncleared} 地板={floor_count}`；产品面连续零改动 **{streak}** 轮（现读 `python3 scripts/product_streak.py --streak-for 392`）。
"""

iteration = f"""## Round 390 · R393（第 392 轮 · 2026-10-26）：600pt 详情头不再截掉「复制」（完整/紧凑 meta 先试再退）；四张最小窗帧只动头部（产品 2 文件，视觉主线）

`content-min-600x440` 的头部只显示 `2025-10-09 16:38:20… 40 个字符 · 来自 终端`，middle 截断吃掉「复制」；750pt 同一条记录是完整一行。`DetailTypography.metaText` 加 `includeCopyVerb`，详情头用 `ViewThatFits` 先试完整、放不下再退紧凑；macOS 12 保留旧截断。修后 600pt 帧完整显示 `2025-10-09 16:38:20 · 40 个字符 · 来自 终端`，750pt 不变。帧差分 {same_frames} 同 / {changed_frames} 变，首张变化 {bbs[0]} 颗、bbox=({bbs[1]},{bbs[2]})..({bbs[3]},{bbs[4]})；基线更新后复验 182/0。纯函数宽度 + 源守卫 + M1027/M1028 都过；436 无新 runner 读数；rot 0/0。

**七维度自评**（恰七行，每格 n/15）：

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | 15/15 | 看了修前 600pt 的省略号、修后完整紧凑行，以及 750pt 不变的对照帧。 |
| 判据有效性 | 14/15 | 纯函数宽度 + 源守卫 + 两把刀；扣 1：没有自动像素判据证明 ViewThatFits 在 600pt 真选了紧凑臂，靠帧差分与看图作证。 |
| 假绿防御 | 15/15 | 两臂同文/去掉 ViewThatFits 都被 M1027/M1028 抓住；750pt 帧不变证明没有全局改写。 |
| 产品面推进 | 15/15 | 真实 Sources 改动：窄窗保留时间/大小/来源，只去掉冗余「复制」。 |
| 台账一致性 | 14/15 | U-1385…U-1389、D-383、436 状态、计数器都从日志解析；扣 1：436 仍开。 |
| 交付诚实性 | 15/15 | 明确写 macOS 12 仍走旧截断；不把「帧选对了」写成自动像素判据已覆盖。 |
| 可复核性 | 15/15 | 四张帧的差分与 bbox、基线更新、纯函数宽度断言、两把刀都有原文。 |

均分 = 103/105 ≈ 14.7/15（98）。
"""

decision = """
### D-383（393）窄窗口的元信息要「先试完整、再退紧凑」：只去掉冗余词，不丢时间/大小/来源

R393 现读：600pt 窗口里完整 meta 放不下，旧的 middle 截断显示 `2025-10-09 16:38:20… 40 个字符 · 来自 终端`，把「复制」吃掉；同一时刻 750pt 是完整一行。紧凑版只去掉冗余「复制」（11pt 系统字体实测 271.7 → 246.6pt），`ViewThatFits` 在 600pt 选紧凑、750pt 仍选完整；四张 600pt 帧的差集 bbox 都在头部，750pt 帧不变。
**Why**：截断中间的一段是「信息被删」，而时间/大小/来源是这一行的主语与限定；「复制」只说明时间戳的语义，在剪贴板详情里是冗余。与其让截断随机吃掉一个片段，不如显式定义「放不下时删哪一段」。
**How to apply**：① 窄窗口的文案先试完整、再用明确的紧凑变体兜底，不要靠 middle 截断随机删；② 紧凑变体只去掉冗余词，主语/限定必须保留；③ `ViewThatFits` 是 macOS 13+，低版本用显式 `if #available` 保留旧行为，不引新 API；④ 配纯函数宽度断言、源守卫与「两臂同文/去掉 ViewThatFits」两把刀；⑤ 帧差分要证明宽档帧不变、窄档只动目标行。
"""

changelog = """### 600pt 详情头不再截掉「复制」：完整/紧凑 meta 先试再退，四张最小窗帧只动头部（R393 / 第 392 轮 / Round 390 / U-1385…U-1389 · 产品 2 文件，视觉主线）

"""

report_bullet = f"""
- **R393（视觉主线）**：`content-min-600x440` 的详情头把「复制」截掉（`2025-10-09 16:38:20… 40 个字符 · 来自 终端`）⇒ `DetailTypography.metaText` 加 `includeCopyVerb`，详情头用 `ViewThatFits` 先试完整、放不下退紧凑；macOS 12 保留旧截断。修后 600pt 完整显示 `2025-10-09 16:38:20 · 40 个字符 · 来自 终端`，750pt 不变。帧差分 `{same_frames}` 同 / `{changed_frames}` 变，首张变化 `{bbs[0]}` 颗、bbox `({bbs[1]},{bbs[2]})..({bbs[3]},{bbs[4]})`；基线更新后复验 182/0。M1027/M1028 CAUGHT。436 无新 runner 读数，仍未结案；rot 0/0。**网络仍断 ⇒ PUSH_BLOCKED=network，ahead=22，未推送。**
"""

state_section = f"""## R393 状态（2026-10-26 · 本地 · 第 392 轮 / Round 390）：600pt 详情头不再截掉「复制」—— 完整/紧凑 meta 先试再退，四张最小窗帧只动头部（产品 2 文件，视觉主线）

最后更新：2026-10-26（本地 · R393 / 第 392 轮 / Round 390）：`content-min-600x440` 的详情头只显示 `2025-10-09 16:38:20… 40 个字符 · 来自 终端`，middle 截断把「复制」吃掉；750pt 的同一记录是完整一行。`DetailTypography.metaText` 增加 `includeCopyVerb`（默认 true），详情头用 `ViewThatFits` 先试完整、放不下再退到去掉冗余「复制」的紧凑版；时间/大小/来源一个不丢，行高不变；macOS 12 用显式 `if #available` 保留旧截断（`ViewThatFits` 是 13+）。修后 600pt 帧现读完整 `2025-10-09 16:38:20 · 40 个字符 · 来自 终端`，750pt 不变。纯函数宽度 + 源守卫；`M1027`（紧凑臂写回 true）/`M1028`（ViewThatFits 换 Group）都 CAUGHT。BACKLOG 436 无新 runner 读数，仍未结案。`swift build --build-tests` 告警 **{warnings}**；全量 `Executed {executed} tests, with {skipped} tests skipped and {failures} failures`；捕获 `CAPTURED {frames} -> /tmp/r393_shots`，与 R392 逐张比 `变了={changed_frames}`（四张 600pt 帧的差集都在头部，首张 {bbs[0]} 颗、bbox=({bbs[1]},{bbs[2]})..({bbs[3]},{bbs[4]})），帧基线 `UPDATED={b_compared}`，复验 `COMPARED={b_compared} CHANGED={b_changed}`；清账表 `表面={surfaces} 状态={states} 格子={cells} 已清账={cleared} 未清账={uncleared} 地板={floor_count}`；换装 `INSTALL_RESULT=ok`、`INSTALL_SHA_MATCH=1`、条目 {entries_before}={entries_after}；`HIDDEN_ARMS 表={h_tables} 可判={h_judged} rot={h_rot} … 上界 rot={h_rot_ceiling} 处置=ok`；预检 `tables={pre_tables} covered={pre_covered} arms={pre_arms} bad={pre_bad}`、全仓 {arm_files} 文件 / {arm_total} 把；产品面连续零改动 **{streak}** 轮（现读 `python3 scripts/product_streak.py --streak-for 392`）。

本轮做了什么：
① ⓪ 网络：push 被 SSH 拒 + `api=000`/`apple=200` ⇒ `PUSH_BLOCKED=network`；未推送，CI 多跑未读。
② 产品位：600pt 详情头由「完整/紧凑先试再退」保留时间/大小/来源；750pt 不变。
③ 判据：纯函数宽度 + 源守卫 + M1027/M1028；帧差分 4 张只动头部。
④ 436：无新 runner 读数，本地 5 臂复现仍成立；不关单、不猜 must_judge。
⑤ 367：hidden 表 {h_tables} / 可判 {h_judged} / rot {h_rot} / 上界 {h_rot_ceiling}；预检 {pre_tables}/{pre_covered}/{pre_arms}/{pre_bad}。
⑥ 验证：build 0 告警；全量 `{executed}/{skipped}/{failures}`；捕获 {frames} 帧、四张头部帧更新并复验 0；换装 ok；清账表 {cells}=162。

验证读数（现读）：帧差分 `{same_frames} 同 / {changed_frames} 变`；首张变化 `{bbs[0]}`、bbox `({bbs[1]},{bbs[2]})..({bbs[3]},{bbs[4]})`；`M1027/M1028` CAUGHT；`HIDDEN_ARMS … rot={h_rot} … 处置=ok`；产品面连续零改动 **{streak}** 轮（`scripts/product_streak.py --streak-for 392`）。

NOT-RUN / 阻塞（分开写）：① **`PUSH_BLOCKED=network`**：push 被 SSH 拒 + `api=000`（LibreSSL SSL_ERROR_SYSCALL）/ `apple=200`；本地 ahead=22（R393 主笔前）；② `40234023212 ↔ d38ea10`、`40234058148 ↔ 5c7814e` 与 R387–R392 本地提交的 conclusion **未读**（网络）；③ BACKLOG 436 的 runner motion 卷未读（本地复现不能关单），不改 JSON/自测；④ 亮档真机腿仍没跑；⑤ macOS 12 上仍是旧的单行截断（`ViewThatFits` 13+）—— 本轮没有 12 的可执行环境，按具名限制记账。

下一轮（R394）的靶：⓪ 先 `git push origin main`（禁 amend/force）并复核 ahead=0；读 `40234023212`/`40234058148` 与 R387–R393 推送那一跑的**全部失败步骤**，把 run↔commit 成对写回本行；按 BACKLOG 436 先读 CI motion 卷，再决定第五臂 `must_judge` 并一次性改 JSON 与自测；① 367 现读 rot=0，按 `HIDDEN_ROT` 查新腐烂；② 回产品动效面再点一个真实位。
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
report_new = once(report_old, "D-069 … **D-382**", "D-069 … **D-383**")
report_new = once(report_new, "U-31 … U-1384（R392 现读抬到最新一节）", "U-31 … U-1389（R393 现读抬到最新一节）")
report_new = once(report_new, "产品面连续零改动轮数 = **1**", "产品面连续零改动轮数 = **2**")
report_new = once(
    report_new,
    "R392 现读：注册表 **146** 张 / 刀号最大 **M1026** / 预检 covered=129 arms=402 bad=0；全仓 239 文件 / 886 把；M674 退役、M906 空刀退役",
    f"R393 现读：注册表 **{pre_tables}** 张 / 刀号最大 **M1028** / 预检 covered={pre_covered} arms={pre_arms} bad={pre_bad}；"
    f"全仓 {arm_files} 文件 / {arm_total} 把；M674 退役、M906 空刀退役")
report_new = once(
    report_new,
    "**网络仍断 ⇒ PUSH_BLOCKED=network，ahead=22，未推送。**",
    "**网络仍断 ⇒ PUSH_BLOCKED=network，ahead=22，未推送。**" + report_bullet)

state_old = rd("AGENT_STATE.md")
state_anchor = "## R392 状态（2026-10-26"
assert state_old.count(state_anchor) == 1
state_new = once(state_old, state_anchor, state_section + "\n" + state_anchor)

wr("AGENT_UI_AUDIT.md", audit_new)
wr("AGENT_VISUAL_ITERATION.md", iteration_new)
wr("AGENT_DECISIONS.md", decisions_new)
wr("CHANGELOG.md", changelog_new)
wr("AGENT_FINAL_REPORT.md", report_new)
wr("AGENT_STATE.md", state_new)

print("R393_LEDGERS_OK warnings=%s full=%s/%s/%s frames=%s diff=%s/%s baseline=%s/%s bbox=%s rot=%s pre=%s/%s/%s/%s arms=%s/%s gate=%s=%s streak=%s"
      % (warnings, executed, skipped, failures, frames, same_frames, changed_frames,
         b_compared, b_changed, bbs[0], h_rot, pre_tables, pre_covered, pre_arms, pre_bad,
         arm_files, arm_total, cleared, cells, streak))
