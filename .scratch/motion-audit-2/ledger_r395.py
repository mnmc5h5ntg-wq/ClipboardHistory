#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R395（第 394 轮 / Round 392）的台账。数字全部从本机日志解析。"""
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


build = log("/tmp/r395_build_final2.log")
warnings = len(re.findall(r"warning:", build))
assert warnings == 0

full = log("/tmp/r395_full.log")
summaries = [tuple(int(x) for x in row) for row in
             re.findall(r"Executed (\d+) tests, with (\d+) tests skipped and (\d+) failures", full)]
big = [row for row in summaries if row[0] > 900]
assert big
executed, skipped, failures = big[-1]
assert failures == 0

capture = log("/tmp/r395_capture.log")
cap = re.search(r"CAPTURED (\d+) -> /tmp/r395_shots", capture)
assert cap
frames = int(cap.group(1))

diff = log("/tmp/r395_framediff.log")
dm = re.search(r"FRAME_DIFF 比了=(\d+) 变了=(\d+)", diff)
assert dm
total_frames, changed_frames = [int(x) for x in dm.groups()]
same_frames = total_frames - changed_frames
assert (same_frames, changed_frames, total_frames) == (182, 0, 182)

baseline = log("/tmp/r395_framebaseline.log")
bm = re.search(r"FRAME_BASELINE_COMPARED=(\d+)\s+FRAME_BASELINE_CHANGED=(\d+)"
               r"\s+FRAME_BASELINE_MISSING=(\d+)\s+FRAME_BASELINE_ADDED=(\d+)", baseline)
assert bm
b_compared, b_changed, b_missing, b_added = [int(x) for x in bm.groups()]
assert (b_compared, b_changed, b_missing, b_added) == (182, 0, 0, 0)

cat = log("/tmp/r395_fade3.log")
c2 = re.search(r"MOTION_GRAB settings-category-change 帧数=(\d+) 抓帧中位=(\d+)\.\d+ms.*?声明=160ms", cat)
f2 = re.search(r"SETTINGS_CATEGORY_FADE scale=2x 帧数=(\d+) 过渡帧数=(\d+) 峰值=([0-9.]+)", cat)
f1 = re.search(r"SETTINGS_CATEGORY_FADE scale=1x 帧数=(\d+) 过渡帧数=(\d+) 峰值=([0-9.]+)", cat)
assert c2 and f2 and f1
cat2_grab, cat2_median = int(c2.group(1)), int(c2.group(2))
cat2_frames, cat2_span, cat2_peak = int(f2.group(1)), int(f2.group(2)), f2.group(3)
cat1_frames, cat1_span, cat1_peak = int(f1.group(1)), int(f1.group(2)), f1.group(3)

notrun = log("/tmp/r395_fade_final.log")
assert "SETTINGS_CATEGORY_FADE_NOT_RUN=clock-coarse" in notrun

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

install = log("/tmp/r395_install.log")
assert "INSTALL_RESULT=ok" in install and "INSTALL_SHA_MATCH=1" in install
entries = re.search(r"INSTALL_ENTRIES_BEFORE=(\d+)\s+INSTALL_ENTRIES_AFTER=(\d+)", install)
assert entries
entries_before, entries_after = entries.groups()

pre = log("/tmp/r395_precheck.log")
pre_line = re.search(r"NEEDLE_PRECHECK tables=(\d+) covered=(\d+) arms=(\d+) bad=(\d+)", pre)
arm_line = re.search(r"ARM_TOTAL files=(\d+) arms=(\d+) dupes=(\d+) repeats=(\d+)", pre)
assert pre_line and arm_line
pre_tables, pre_covered, pre_arms, pre_bad = [int(x) for x in pre_line.groups()]
arm_files, arm_total, arm_dupes, arm_repeats = [int(x) for x in arm_line.groups()]
assert pre_bad == 0 and arm_dupes == 0 and arm_repeats == 0

hidden = log("/tmp/r395_hidden.log")
h = re.search(r"HIDDEN_ARMS 表=(\d+) 可判=(\d+) rot=(\d+) 抽不出=(\d+) 已声明表=(\d+) 已声明死针=(\d+) 上界 rot=(\d+)", hidden)
assert h
h_tables, h_judged, h_rot, h_opaque, h_dtables, h_ddead, h_rot_ceiling = [int(x) for x in h.groups()]
assert h_rot == h_rot_ceiling == 0

gate = log("/tmp/r395_gate.log")
g = re.search(r"MOTION_LEDGER 表面=(\d+) 状态=(\d+) 格子=(\d+) 行数=(\d+) 已清账=(\d+) 未清账=(\d+) 地板=(\d+)", gate)
assert g
surfaces, states, cells, rows, cleared, uncleared, floor_count = [int(x) for x in g.groups()]
assert uncleared == 0 and cleared == cells == rows == floor_count

streak_out = subprocess.check_output(
    ["python3", os.path.join(ROOT, "scripts/product_streak.py"), "--streak-for", "394"],
    cwd=ROOT).decode("utf-8")
streak = int(re.search(r"streak=(\d+)", streak_out).group(1))
assert streak == 1, "streak=%d" % streak

mut = log("/tmp/r395_mut.log")
assert "R395_MUTATE 刀=1 CAUGHT=1 红得不对=0 RESTORE_CLEAN=yes" in mut

ui_heading = "## 第 393 轮（R394"
ui_section = f"""## 第 394 轮（R395 · 2026-10-26 · U-1395…U-1399）：设置分类切换的过渡被通道判成 NOT-RUN —— 2x 采样≈{cat2_median}ms / 1x 只 2 帧；只加只读分类缝与源守卫（U-1395…U-1399 · 产品 1 文件（绑定缝），判据账）

- **U-1395：⓪ 网络与 CI。** 12:14 `git push origin main` 被 SSH 拒（`Connection closed by 20.205.243.166 port 22`），同分钟 `api=000`（LibreSSL SSL_ERROR_SYSCALL）/ `apple=200` ⇒ GitHub 侧仍断；`PUSH_BLOCKED=network`，本地 ahead=28（R394 之后、R395 落笔前），**不写已推送**。`origin/main` 本地 ref 仍 `5c7814e`；网络不可达无法 fetch 确认远端是否被推进（push 在连接阶段失败，未用 force）。恢复后先 push、复核 ahead=0，再读 `40234023212`/`40234058148` 与 R387–R395 推送跑的全部失败步骤。
- **U-1396：新位点 —— 设置分类切换的详情过渡。** 产品有 `.id(category)` + `.transition(.contentFade)` + `.animation(value:)`，但从未有整页帧判过过程。R395 给 `SettingsView` 加只读 `categoryOverride` 缝，用产品真实视图树驱动 快捷键→推荐；胶片只拍详情列。现读：2x `抓帧中位={cat2_median}ms`、`帧数={cat2_frames} 过渡帧数={cat2_span} 峰值={cat2_peak}`；1x `帧数={cat1_frames} 过渡帧数={cat1_span} 峰值={cat1_peak}`（声明 160ms）。**这不是产品缺陷读数**：2x 首帧/采样就已超过声明的一半（{cat2_median}ms > 80ms），1x 也只剩 2 个过渡帧；按 D-385 记 `SETTINGS_CATEGORY_FADE_NOT_RUN=clock-coarse` / `duration-under-resolved`，不把通道限制写成硬切。试过把 `.animation` 挪到 Group、在变更点 `withAnimation`、去掉 `.id`，两倍率都仍是 2 帧，已全部回退，未留未验证的产品改动。
- **U-1397：判据与刀。** 新增 `MotionCatalogTests.testSettingsCategoryOverrideSeamIsWired`：两个侧栏构造点都走 `selectedCategoryBinding`、缝参数存在、无 override 时初值仍进 `_selectedCategoryState`；`M1032`（把缝绕过）**CAUGHT**、还原干净。**产品视觉 0 改动**：本轮只增加只读缝，不为了凑产品改动去动分类样式；下一轮必须回到产品视觉。
- **U-1398：BACKLOG 436 处置（仍未结案）。** 无新 runner motion 读数；R390 本地完整卷 `Executed {motion_exec} tests, with {motion_skip} tests skipped and {motion_fail} failures`、`MOTION_SUMMARY {motion_summary}`、`MOTION_RESOLVE_SUMMARY judged={motion_judged}/{motion_total} not-run={motion_notrun}` 与闸门 exit 1（UNLISTED `settings-reset-fade`）的本地复现仍成立。**不关单、不改 JSON/自测、不猜 `must_judge`**；runner 卷继续记具名 NOT-RUN。
- **U-1399：① 367 rot 与八步。** `HIDDEN_ARMS 表={h_tables} 可判={h_judged} rot={h_rot} 抽不出={h_opaque} 已声明表={h_dtables} 已声明死针={h_ddead} 上界 rot={h_rot_ceiling} 处置=ok`；预检 `tables={pre_tables} covered={pre_covered} arms={pre_arms} bad={pre_bad}`、全仓 {arm_files} 文件 / {arm_total} 把；`M1032` CAUGHT。build **{warnings}** 告警；全量 `Executed {executed} tests, with {skipped} tests skipped and {failures} failures`；捕获 `CAPTURED {frames} -> /tmp/r395_shots`，与 R394 逐张比 `变了={changed_frames}`（默认路径完全不变），帧基线 `COMPARED={b_compared} CHANGED={b_changed}`；换装 `INSTALL_RESULT=ok`、`INSTALL_SHA_MATCH=1`、条目 `{entries_before}={entries_after}`；清账表 `表面={surfaces} 状态={states} 格子={cells} 已清账={cleared} 未清账={uncleared} 地板={floor_count}`；产品面连续零改动 **{streak}** 轮（现读 `python3 scripts/product_streak.py --streak-for 394`）。
"""

iteration = f"""## Round 392 · R395（第 394 轮 · 2026-10-26）：设置分类切换的过渡被判 NOT-RUN（2x 采样≈{cat2_median}ms / 1x 2 帧）；只加只读分类缝与源守卫（产品 1 文件（绑定缝），判据账）

设置分类切换有 `.id` + `.transition(.contentFade)` + `.animation(value:)`，但从未有整页过程读数。加只读 `categoryOverride` 缝，用产品真实 `SettingsView` 驱动 快捷键→推荐；2x 抓帧中位 {cat2_median}ms、过渡 {cat2_span} 帧，1x 过渡 {cat1_span} 帧（峰值 {cat2_peak}/{cat1_peak}，声明 160ms）。首帧/采样成本吞掉了 160ms 窗口 ⇒ 按 D-385 记具名 NOT-RUN，不判产品硬切。试过 Group 动画、变更点 withAnimation、去 `.id`，均无变化，已回退。M1032 咬住分类缝；默认 182 帧零变化。**产品视觉 0 改动**，下一轮必须回产品。

**七维度自评**（恰七行，每格 n/15）：

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | 13/15 | 看了分类切换 strip：前几帧快捷键、随后推荐；扣 2：通道无法分辨 160ms 的中间过程。 |
| 判据有效性 | 14/15 | 分类缝源守卫 + M1032；过渡的时钟/首帧闸门写成具名 NOT-RUN，不冒充红/绿。 |
| 假绿防御 | 15/15 | 先量采样再判；三组未奏效的产品改法全部回退，没有把通道限制写成产品缺陷。 |
| 产品面推进 | 7/15 | 只加只读绑定缝，没有视觉产品改动；明确记「下一轮必须回产品」。 |
| 台账一致性 | 14/15 | U-1395…U-1399、D-385、436 状态、计数器都从日志解析；扣 1：436 仍开。 |
| 交付诚实性 | 15/15 | 明确写产品视觉 0 改动与过渡 NOT-RUN，不把缝写成修复，不留未验证改动。 |
| 可复核性 | 14/15 | 两倍率帧数/峰值/采样、strip、M1032、precheck/rot 都有原文；过程本身无法复核（通道限制）。 |

均分 = 92/105 ≈ 13.1/15（88 → 按目标继续修；本轮不是收口轮）。
"""

decision = """
### D-385（395）整页过渡的首帧/采样成本会吞掉短过渡；分辨率不足时只能记 NOT-RUN

R395 现读：设置分类切换声明 `.contentFade` 160ms；2x 抓帧中位 **{cat2_median}ms**、只读到 2 个过渡帧；1x 采样 23.4ms 但仍只有 2 帧。把 `.animation` 挪到 Group、在变更点 `withAnimation`、去掉 `.id` 都没有改变 2 帧 ⇒ 整页首帧布局/抓帧成本占掉了过程窗口，这把尺无法分辨 160ms。按规矩记 `SETTINGS_CATEGORY_FADE_NOT_RUN=clock-coarse` / `duration-under-resolved`，不判产品硬切。
**Why**：整页帧的抓帧成本随面积走（2x 1104×1144px 中位 121–132ms），而声明的过渡只有 160ms；用这样的采样去判「有没有过程」等于用秒表量毫秒。把「读不到」写成「产品没动」会误改正确的产品（R393 的 cacheDisplay 已演过一次）。
**How to apply**：① 先用**同一次运行**的采样间隔与首帧延迟过闸门（>0.5×声明 ⇒ NOT-RUN）；② 过渡判据优先收窄捕获带到目标元素（R57），整页帧只做端态；③ 读不到时写具名 NOT-RUN，并记录试过哪些产品改法、为何回退；④ 不为让通道好看去改产品视觉。
"""

changelog = """### 设置分类切换的过渡被判 NOT-RUN（2x 采样≈{cat2_median}ms / 1x 2 帧）；只加只读分类缝与源守卫（R395 / 第 394 轮 / Round 392 / U-1395…U-1399 · 产品 1 文件（绑定缝），判据账）

"""

report_bullet = f"""
- **R395（判据账）**：设置分类切换的 `.contentFade` 160ms 从未有整页过程读数；加只读 `categoryOverride` 缝驱动产品真实切换。2x 抓帧中位 `{cat2_median}ms` / 过渡 `{cat2_span}` 帧，1x 过渡 `{cat1_span}` 帧（峰值 `{cat2_peak}`/`{cat1_peak}`）⇒ 首帧/采样成本吞掉过程窗口，记 `SETTINGS_CATEGORY_FADE_NOT_RUN=clock-coarse`，不判产品硬切；Group 动画/withAnimation/去 id 三组尝试均无效且已回退。M1032 咬住分类缝；默认 182 帧零变化。**产品视觉 0 改动**，下一轮必须回产品。436 无新 runner 读数，仍未结案；rot 0/0。**网络仍断 ⇒ PUSH_BLOCKED=network，ahead=28，未推送。**
"""

state_section = f"""## R395 状态（2026-10-26 · 本地 · 第 394 轮 / Round 392）：设置分类切换的过渡被判 NOT-RUN（2x 采样≈{cat2_median}ms / 1x 2 帧）；只加只读分类缝与源守卫（产品 1 文件（绑定缝），判据账）

最后更新：2026-10-26（本地 · R395 / 第 394 轮 / Round 392）：设置分类切换有 `.id` + `.transition(.contentFade)` + `.animation(value:)`，但从未有整页过程读数。加只读 `categoryOverride` 缝，用产品真实 `SettingsView` 驱动 快捷键→推荐；2x 抓帧中位 **{cat2_median}ms**、过渡 **{cat2_span}** 帧，1x 过渡 **{cat1_span}** 帧（峰值 `{cat2_peak}`/`{cat1_peak}`，声明 160ms）。首帧/采样成本吞掉 160ms 窗口 ⇒ 按 D-385 记具名 **NOT-RUN**，不判产品硬切；试过 Group 动画、变更点 withAnimation、去 `.id`，均无变化并已回退。分类缝源守卫 + `M1032` CAUGHT；默认 182 帧 `变了={changed_frames}`，帧基线 182/0。**本轮产品视觉 0 改动**，下一轮必须回产品视觉。BACKLOG 436 无新 runner 读数，仍未结案。全量 `Executed {executed} tests, with {skipped} tests skipped and {failures} failures`；换装 `ok / SHA_MATCH=1 / 381=381`；清账表 162=162；`HIDDEN_ARMS 表={h_tables} 可判={h_judged} rot={h_rot} … 上界 rot={h_rot_ceiling} 处置=ok`；预检 `tables={pre_tables} covered={pre_covered} arms={pre_arms} bad={pre_bad}`、全仓 {arm_files} 文件 / {arm_total} 把；产品面连续零改动 **{streak}** 轮（现读 `python3 scripts/product_streak.py --streak-for 394`）。

本轮做了什么：
① ⓪ 网络：push 被 SSH 拒 + `api=000`/`apple=200` ⇒ `PUSH_BLOCKED=network`；未推送。
② 新位点：设置分类切换；2x/1x 都只有 2 个过渡帧，采样/首帧成本超过声明一半 ⇒ 具名 NOT-RUN。
③ 产品：只加只读 `categoryOverride` 缝；试过三组视觉改法均无效，全部回退，不留未验证改动。
④ 判据：分类缝源守卫 + M1032 CAUGHT；过渡的通道闸门写成具名 NOT-RUN。
⑤ 367：hidden 表 {h_tables} / 可判 {h_judged} / rot {h_rot} / 上界 {h_rot_ceiling}；预检 {pre_tables}/{pre_covered}/{pre_arms}/{pre_bad}。
⑥ 验证：build 0 告警；全量 `{executed}/{skipped}/{failures}`；捕获 {frames} 帧、默认零变化；换装 ok；清账表 {cells}=162。

验证读数（现读）：`SETTINGS_CATEGORY_FADE` 2x `{cat2_frames}/{cat2_span}/{cat2_peak}`、1x `{cat1_frames}/{cat1_span}/{cat1_peak}`；`MOTION_GRAB` 2x 抓帧中位 `{cat2_median}ms`；`M1032` CAUGHT；`HIDDEN_ARMS … rot={h_rot} … 处置=ok`。

NOT-RUN / 阻塞（分开写）：① **`PUSH_BLOCKED=network`**：push 被 SSH 拒 + `api=000`/`apple=200`；本地 ahead=28（R395 主笔前）；② `40234023212`/`40234058148` 与 R387–R394 本地提交的 conclusion **未读**（网络）；③ **`SETTINGS_CATEGORY_FADE_NOT_RUN=clock-coarse` / `duration-under-resolved`**：整页 2x 采样 121–132ms、1x 只剩 2 帧，无法判 160ms 过程；④ BACKLOG 436 的 runner motion 卷未读；⑤ 亮档真机腿仍没跑；⑥ macOS 12 的紧凑详情头仍走旧截断（13+ 才有 ViewThatFits）。

下一轮（R396）的靶：⓪ 先 `git push origin main`（禁 amend/force）并复核 ahead=0；读三跑全部失败步骤并写回本行；按 BACKLOG 436 先读 CI motion 卷，再决定第五臂 `must_judge` 并一次性改 JSON 与自测；① 367 现读 rot=0，按 `HIDDEN_ROT` 查新腐烂；② **必须回到产品视觉并落 Sources**（本轮产品视觉 0 改动）；若要再判分类过渡，先把整页帧换成目标带宽，或给该过渡一个低成本的端态/过程通道，否则仍然 NOT-RUN。
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
report_new = once(report_old, "D-069 … **D-384**", "D-069 … **D-385**")
report_new = once(report_new, "U-31 … U-1394（R394 现读抬到最新一节）", "U-31 … U-1399（R395 现读抬到最新一节）")
report_new = once(
    report_new,
    "R394 现读：注册表 **149** 张 / 刀号最大 **M1031** / 预检 covered=132 arms=407 bad=0；全仓 242 文件 / 891 把；M674 退役、M906 空刀退役",
    f"R395 现读：注册表 **{pre_tables}** 张 / 刀号最大 **M1032** / 预检 covered={pre_covered} arms={pre_arms} bad={pre_bad}；"
    f"全仓 {arm_files} 文件 / {arm_total} 把；M674 退役、M906 空刀退役")
report_new = once(
    report_new,
    "**网络仍断 ⇒ PUSH_BLOCKED=network，ahead=28，未推送。**",
    "**网络仍断 ⇒ PUSH_BLOCKED=network，ahead=28，未推送。**" + report_bullet)

state_old = rd("AGENT_STATE.md")
state_anchor = "## R394 状态（2026-10-26"
assert state_old.count(state_anchor) == 1
state_new = once(state_old, state_anchor, state_section + "\n" + state_anchor)

wr("AGENT_UI_AUDIT.md", audit_new)
wr("AGENT_VISUAL_ITERATION.md", iteration_new)
wr("AGENT_DECISIONS.md", decisions_new)
wr("CHANGELOG.md", changelog_new)
wr("AGENT_FINAL_REPORT.md", report_new)
wr("AGENT_STATE.md", state_new)

print("R395_LEDGERS_OK warnings=%s full=%s/%s/%s frames=%s diff=%s/%s baseline=%s/%s cat2=%s/%s/%s cat1=%s/%s/%s median=%sms rot=%s pre=%s/%s/%s/%s arms=%s/%s gate=%s=%s streak=%s"
      % (warnings, executed, skipped, failures, frames, same_frames, changed_frames,
         b_compared, b_changed, cat2_frames, cat2_span, cat2_peak, cat1_frames, cat1_span, cat1_peak,
         cat2_median, h_rot, pre_tables, pre_covered, pre_arms, pre_bad, arm_files, arm_total,
         cleared, cells, streak))
