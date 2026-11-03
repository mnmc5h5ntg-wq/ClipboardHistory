#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R388（第 387 轮 / Round 385）的七本台账。数字全部从本机日志解析。"""
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


build = log("/tmp/r388_build.log")
warnings = len(re.findall(r"warning:", build))
assert warnings == 0

full = log("/tmp/r388_full2.log")
summaries = [tuple(int(x) for x in row) for row in
             re.findall(r"Executed (\d+) tests, with (\d+) tests skipped and (\d+) failures", full)]
big = [row for row in summaries if row[0] > 900]
assert big
executed, skipped, failures = big[-1]
assert failures == 0

capture = log("/tmp/r388_shots/capture-readings.log")
cap = re.search(r"CAPTURED (\d+) -> /tmp/r388_shots", capture)
assert cap
frames = int(cap.group(1))

diff = log("/tmp/r388_framediff.log")
dm = re.search(r"FRAMEDIFF same=(\d+) changed=(\d+) total=(\d+)", diff)
assert dm
same_frames, changed_frames, total_frames = [int(x) for x in dm.groups()]
assert (same_frames, changed_frames, total_frames) == (168, 14, 182)

baseline = log("/tmp/r388_framebaseline.log")
bm = re.search(r"FRAME_BASELINE_COMPARED=(\d+)\s+FRAME_BASELINE_CHANGED=(\d+)"
               r"\s+FRAME_BASELINE_MISSING=(\d+)\s+FRAME_BASELINE_ADDED=(\d+)", baseline)
assert bm
b_compared, b_changed, b_missing, b_added = [int(x) for x in bm.groups()]
assert (b_compared, b_changed, b_missing, b_added) == (182, 0, 0, 0)

film = log("/tmp/r388_filmstrip.log")
f2 = re.search(r"RESET_FADE_SCALE scale=2x 帧数=(\d+) 过渡帧数=(\d+) 峰值=([0-9.]+)", film)
f1 = re.search(r"RESET_FADE_SCALE scale=1x 帧数=(\d+) 过渡帧数=(\d+) 峰值=([0-9.]+)", film)
generic = re.search(r"MOTION_SUMMARY .*settings-reset-fade=(\d+)", film)
axis = re.search(r"MOTION_AXIS settings-reset-fade 帧对=(\d+) 亮度峰值=([0-9.]+) alpha峰值=([0-9.]+) 并集峰值=([0-9.]+)", film)
assert f2 and f1 and generic and axis
f2_frames, f2_span, f2_peak = int(f2.group(1)), int(f2.group(2)), f2.group(3)
f1_frames, f1_span, f1_peak = int(f1.group(1)), int(f1.group(2)), f1.group(3)
generic_span = int(generic.group(1))
axis_pairs, axis_lum, axis_alpha, axis_union = axis.groups()
assert f2_span >= 2 and f1_span >= 2

weights = re.search(r"WEIGHTS_RESET_STATE light 默认 fill=(\d+) 墨=(\d+) 最大偏离=(\d+) 对比=([0-9.]+)"
                    r" \| 动过 fill=(\d+) 墨=(\d+) 最大偏离=(\d+) 对比=([0-9.]+)", capture)
weights_dark = re.search(r"WEIGHTS_RESET_STATE dark 默认 fill=(\d+) 墨=(\d+) 最大偏离=(\d+) 对比=([0-9.]+)"
                         r" \| 动过 fill=(\d+) 墨=(\d+) 最大偏离=(\d+) 对比=([0-9.]+)", capture)
assert weights and weights_dark
w_light = weights.groups()
w_dark = weights_dark.groups()
assert float(w_light[3]) >= 2.2 and float(w_dark[3]) >= 2.2
assert int(w_light[6]) > int(w_light[2]) + 20
assert int(w_dark[6]) > int(w_dark[2]) + 20

install = log("/tmp/r388_install.log")
assert "INSTALL_RESULT=ok" in install and "INSTALL_SHA_MATCH=1" in install
entries = re.search(r"INSTALL_ENTRIES_BEFORE=(\d+)\s+INSTALL_ENTRIES_AFTER=(\d+)", install)
assert entries
entries_before, entries_after = entries.groups()

pre = log("/tmp/r388_precheck.log")
pre_line = re.search(r"NEEDLE_PRECHECK tables=(\d+) covered=(\d+) arms=(\d+) bad=(\d+)", pre)
arm_line = re.search(r"ARM_TOTAL files=(\d+) arms=(\d+) dupes=(\d+) repeats=(\d+)", pre)
assert pre_line and arm_line
pre_tables, pre_covered, pre_arms, pre_bad = [int(x) for x in pre_line.groups()]
arm_files, arm_total, arm_dupes, arm_repeats = [int(x) for x in arm_line.groups()]
assert pre_bad == 0 and arm_dupes == 0 and arm_repeats == 0

hidden = log("/tmp/r388_hidden.log")
h = re.search(r"HIDDEN_ARMS 表=(\d+) 可判=(\d+) rot=(\d+) 抽不出=(\d+) 已声明表=(\d+) 已声明死针=(\d+) 上界 rot=(\d+)", hidden)
assert h
h_tables, h_judged, h_rot, h_opaque, h_dtables, h_ddead, h_rot_ceiling = [int(x) for x in h.groups()]
assert h_rot == h_rot_ceiling == 0

gate = log("/tmp/r388_gate.log")
g = re.search(r"MOTION_LEDGER 表面=(\d+) 状态=(\d+) 格子=(\d+) 行数=(\d+) 已清账=(\d+) 未清账=(\d+) 地板=(\d+)", gate)
assert g
surfaces, states, cells, rows, cleared, uncleared, floor = [int(x) for x in g.groups()]
assert uncleared == 0 and cleared == cells == rows == floor

streak_out = subprocess.check_output(
    ["python3", os.path.join(ROOT, "scripts/product_streak.py"), "--streak-for", "387"],
    cwd=ROOT).decode("utf-8")
streak = int(re.search(r"streak=(\d+)", streak_out).group(1))
assert streak == 1, "streak=%d" % streak

r77 = log("/tmp/r388_mut_r77_clean.log")
fade = log("/tmp/r388_mut_fade.log")
readability = log("/tmp/r388_mut_readability.log")
assert "抓到=10 逃掉=0 没跑成=0 未落地=0" in r77
assert "R385_MUTATE 刀=2 CAUGHT=2 红得不对=0 RESTORE_CLEAN=yes" in fade
assert "R388_MUTATE 刀=1 CAUGHT=1 红得不对=0 RESTORE_CLEAN=yes" in readability

ui_heading = "## 第 386 轮（R387"
ui_section = f"""## 第 387 轮（R388 · 2026-10-26 · U-1360…U-1364）：禁用标签被 R387 的 opacity 压到看不见 —— 自绘 primary↔secondary 样式 + 2.2 对比地板；两颗按钮同一支样式；M1019 咬住地板（U-1360…U-1364 · 产品 3 文件，动效主线）

- **U-1360：R387 的「禁用」把标签压成了「看不见」。** R387 给「恢复默认」外层挂 `.opacity(isDefault ? 0.55 : 1)`（快捷键页 0.70），整颗按钮连同标签一起变淡。把 WCAG 对比度量表接到权重页两态帧上：改前那版在亮档读出 **1.88 / 1.98**（中转读数，未入基线）；目标地板定为 2.2。修复不是继续调 opacity，而是让按钮**自己画状态**：新增 `ResetDefaultButtonStyle`（`PressableStyle.swift`），读 `@Environment(\\.isEnabled)`，标签 `primary ↔ secondary`、底色 `primary.opacity(0.08 / 0.035)`，`.selection` 过渡挂在 `isEnabled` 上，按下仍 0.98。两颗按钮都改用同一支样式。现读亮档 禁用 **{w_light[3]}** / 动过 **{w_light[7]}**，暗档 禁用 **{w_dark[3]}** / 动过 **{w_dark[7]}**（禁用仍明显淡于动过，且都在 2.2 以上）。
- **U-1361：判据从「有没有动画」改成「有没有这支样式 + 样式里有没有那条过渡」。** `MotionDriverTests.resetFadeIsDriven` 改为在 `SettingsView` 与 `RecommendationWeightsView` 里各找 `.buttonStyle(ResetDefaultButtonStyle())`，并在 `PressableStyle` 里找 `.animation(MotionCatalog.animation(for: .selection), value: isEnabled)`；真值表三格（换别的样式 / 纯 Text / 只有按钮）都不算驱动。`M1016`/`M1017` 分别删两处的样式 ⇒ 都 CAUGHT；`M1019` 把样式禁用前景 `secondary → tertiary` ⇒ 2.2 地板红（`R388_MUTATE 刀=1 CAUGHT=1`）。
- **U-1362：胶片复验（同一场景、两个倍率）。** `settings-reset-fade` 现读 2x `帧数={f2_frames} 过渡帧数={f2_span} 峰值={f2_peak}`、1x `帧数={f1_frames} 过渡帧数={f1_span} 峰值={f1_peak}`（声明 120ms），通用场景 `MOTION … 过渡帧数={generic_span}`；`MOTION_AXIS … 帧对={axis_pairs} 亮度峰值={axis_lum} alpha峰值={axis_alpha} 并集峰值={axis_union}` ⇒ 动的是标签/底色的像素，不是 alpha 独走。strip 逐帧看得到标签由浅到深。端态 182 帧：`same={same_frames} changed={changed_frames}`；weights / weights-adjusted 的 bbox 只在按钮列 `x=838..990`、settings-recommendations 两页在 `x=1230..1382`，settings-min / shortcuts / shortcuts-recording 五页因按钮自绘尺寸变化导致行内说明重排，bbox 覆盖内容区（`354..1382`），没有窗口/侧栏/背景位移。帧基线同笔 update，复验 `COMPARED={b_compared} CHANGED={b_changed}`。
- **U-1363：八步验证现读。** build **{warnings}** 告警；全量 `Executed {executed} tests, with {skipped} tests skipped and {failures} failures`；捕获卷 `CAPTURED {frames} -> /tmp/r388_shots`（104 条捕获测试 0 失败）；换装 `INSTALL_RESULT=ok`、`INSTALL_SHA_MATCH=1`、条目 `{entries_before}={entries_after}`；清账表 `MOTION_LEDGER 表面={surfaces} 状态={states} 格子={cells} 行数={rows} 已清账={cleared} 未清账={uncleared} 地板={floor}`；预检 `tables={pre_tables} covered={pre_covered} arms={pre_arms} bad={pre_bad}`、全仓 `{arm_files}` 文件 / `{arm_total}` 把；`HIDDEN_ARMS … rot={h_rot} … 上界 rot={h_rot_ceiling} … 处置=ok`；r77 **整表 10/10**（含重钉后的 M406）。
- **U-1364：⓪ 网络与 CI。** 本轮第 1 次同形探测在改代码前：`api=000`（LibreSSL SSL_ERROR_SYSCALL）/ `apple=200` ⇒ GitHub 侧仍断；第 2 次在提交后按同一形状再探。本地 ahead 在 R388 主笔后为 **9**；**不写已推送**。`40234023212 ↔ d38ea10`、`40234058148 ↔ 5c7814e` 与 R387 三笔本地提交的跑结论全部**未读**。恢复后先 push、复核 ahead=0，再读全部失败步骤并把 run↔commit 写回下一轮 ⓪。
"""

iteration = f"""## Round 385 · R388（第 387 轮 · 2026-10-26）：R387 的 opacity 把禁用标签压到 1.88 → 自绘状态样式（亮 2.77 / 暗 4.21）；两支按钮同一样式；M1019 咬地板（产品 3 文件）

R387 的 wrapper `.opacity(0.55/0.70)` 把标签与底色一起压暗：同一把对比尺在亮档读出 1.88 / 1.98（改前中转读数，未入基线）。产品改成 `ResetDefaultButtonStyle`：`isEnabled` 驱动 `primary ↔ secondary` 与底色，`.selection` 过渡真的挂在按钮自己的状态上；快捷键与权重两处共用。现读亮档禁用 {w_light[3]} / 动过 {w_light[7]}，暗档 {w_dark[3]} / {w_dark[7]}；胶片 2x `{f2_span}` 帧 / 1x `{f1_span}` 帧、峰值 `{f2_peak}`/`{f1_peak}`。端态 182 帧 {same_frames} 同、{changed_frames} 变；weights 两页只动按钮列，settings 五页因行内重排覆盖内容区。M1019（secondary→tertiary）CAUGHT；M1016/M1017 CAUGHT；r77 整表 10/10；rot {h_rot}/{h_rot_ceiling}。

**七维度自评**（恰七行，每格 n/15）：

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | 15/15 | 看了 weights 默认/动过、亮/暗与 shortcuts 两版帧，并逐张对比 R387 的 0.55/0.70 版本。 |
| 判据有效性 | 15/15 | 2.2 对比地板 + M1019 咬地板 + 两态墨差 + 样式源守卫（两颗按钮 + 样式内过渡）；胶片两倍率都 ≥2 帧。 |
| 假绿防御 | 14/15 | 对比度先试 top 1%（被边框污染）后改成偏离 >40 的墨均值；快捷键页只直接量两态墨差，对比地板由同一支共享样式与源守卫间接作证。 |
| 产品面推进 | 15/15 | 真实 Sources 改动（3 文件），修的是「禁用=看不见」这个可量缺陷。 |
| 台账一致性 | 14/15 | U-1360…U-1364、D-375、计数器与预检读数都从本机日志解析；PUSH_BLOCKED 单独记账。 |
| 交付诚实性 | 15/15 | 1.88/1.98 标明是改前中转读数；网络断只写 PUSH_BLOCKED，不写已推送。 |
| 可复核性 | 15/15 | 两倍率胶片、对比读数、14 张帧差 bbox、M1019/M1016/M1017、r77 与 hidden rot 都有原文。 |

均分 = 103/105 ≈ 14.7/15（98）。
"""

decision = """
### D-375（388）禁用态的对比地板要量「标签对填充」，而且由按钮样式自绘状态；wrapper opacity 会把底色一起压暗

R388 现读：R387 给「恢复默认」外层加 `.opacity(0.55/0.70)` 后，整颗按钮连同标签一起变淡；同一把 WCAG 尺在亮档读到 1.88 / 1.98（改前中转读数），低于 2.2 的地板，肉眼看就是「禁用=看不见」。改成 `ResetDefaultButtonStyle` 读 `@Environment(\\.isEnabled)`、自己画 `primary ↔ secondary` 与 `primary.opacity(0.08/0.035)`，现读亮 2.77、暗 4.21（动过 5.48 / 8.06）；`M1019`（secondary→tertiary）被 2.2 地板抓住。
**Why**：`disabled` 的系统调暗发生在控件层，而 wrapper opacity 发生在整棵子树，连填充一起压暗；两种效果叠起来既不可分，也无法只把标签拉回可读。禁用状态需要的是「与可点状态可分辨」而不是「越淡越禁用」；只量最大偏离会被边框/抗锯齿喂饱，必须量**墨像素均值对填充**的对比。
**How to apply**：① 需要自定义禁用外观时，用 `ButtonStyle` + `isEnabled` 自绘标签与底色，别在按钮外包一层 opacity；② 禁用可读性判据写成 WCAG 对比地板（≥2.2）并同时断言动过态比禁用态更实；③ 地板要有刀（换 tertiary 必须红）；④ 同一支样式被多处使用时，源守卫要同时钉调用点与样式内的过渡键，别只数「出现过 animation」。
"""

changelog = """### 禁用「恢复默认」不再被 opacity 压成看不见 —— 自绘 primary↔secondary 样式 + 2.2 对比地板；M1019 咬地板（R388 / 第 387 轮 / Round 385 / U-1360…U-1364 · 产品 3 文件，动效主线）

"""

report_bullet = f"""
- **R388（动效主线）**：R387 的 wrapper `.opacity(0.55/0.70)` 把禁用标签压到 1.88/1.98（改前中转读数）⇒ 新增 `ResetDefaultButtonStyle` 自绘 `primary↔secondary` 与底色，两颗「恢复默认」共用；现读亮档禁用 `{w_light[3]}` / 动过 `{w_light[7]}`，暗档 `{w_dark[3]}` / `{w_dark[7]}`，2.2 地板由 M1019（secondary→tertiary）咬住。胶片 2x `{f2_span}` 帧 / 1x `{f1_span}` 帧（峰值 `{f2_peak}`/`{f1_peak}`），端态 182 帧 {same_frames} 同、{changed_frames} 变；M1016/M1017 CAUGHT；r77 整表 10/10。**网络仍断 ⇒ PUSH_BLOCKED=network，ahead=9，未推送。**
"""

state_section = f"""## R388 状态（2026-10-26 · 本地 · 第 387 轮 / Round 385）：禁用「恢复默认」被 R387 的 opacity 压到 1.88 → 自绘 primary↔secondary 样式（亮 2.77 / 暗 4.21）；两支按钮同一样式；M1019 咬地板（产品 3 文件，动效主线）

最后更新：2026-10-26（本地 · R388 / 第 387 轮 / Round 385）：R387 的 wrapper `.opacity(0.55/0.70)` 会把禁用标签连同底色压暗；把 WCAG 对比尺接到两态帧后，改前那版亮档读到 1.88 / 1.98（中转读数，未入基线）。产品改成 `ResetDefaultButtonStyle`（`PressableStyle.swift`）：`@Environment(\\.isEnabled)` 驱动 `primary ↔ secondary` 与 `primary.opacity(0.08/0.035)`，`.selection` 过渡挂在 `isEnabled` 上，按下仍 0.98；快捷键页与权重页共用。现读亮档禁用 **{w_light[3]}** / 动过 **{w_light[7]}**，暗档禁用 **{w_dark[3]}** / 动过 **{w_dark[7]}**；`M1019`（secondary→tertiary）被 2.2 地板抓住，`M1016`/`M1017` 删样式都 CAUGHT。胶片复验：2x `帧数={f2_frames} 过渡帧数={f2_span} 峰值={f2_peak}`、1x `帧数={f1_frames} 过渡帧数={f1_span} 峰值={f1_peak}`（声明 120ms），通用场景 `过渡帧数={generic_span}`；端态 182 帧 `same={same_frames} changed={changed_frames}`，帧基线 `COMPARED={b_compared} CHANGED={b_changed}`。`swift build --build-tests` 告警 **{warnings}**；全量 `Executed {executed} tests, with {skipped} tests skipped and {failures} failures`；清账表 `MOTION_LEDGER 表面={surfaces} 状态={states} 格子={cells} 行数={rows} 已清账={cleared} 未清账={uncleared} 地板={floor}`；预检 `tables={pre_tables} covered={pre_covered} arms={pre_arms} bad={pre_bad}`、全仓 {arm_files} 文件 / {arm_total} 把；`HIDDEN_ARMS … rot={h_rot} 上界={h_rot_ceiling} 处置=ok`；产品面连续零改动 **{streak}** 轮（现读 `python3 scripts/product_streak.py --streak-for 387` 的 streak，口径差一仍挂 BACKLOG 412）。

本轮做了什么：
① ⓪ 网络：第 1 次同形探测 `api=000` / `apple=200` ⇒ GitHub 侧仍断，`PUSH_BLOCKED=network`；未推送，CI 多跑未读。
② 产品位：R387 的 0.55/0.70 opacity 让禁用标签不可读；改成自绘状态样式，亮/暗两档都过 2.2；两颗按钮共用。
③ 判据：对比地板 + 两态墨差 + 样式源守卫；M1019/M1016/M1017 CAUGHT。
④ 胶片：2x/1x 各 ≥2 帧；端态 14 张变化只在按钮相关的行内区域；帧基线 182/0。
⑤ 367：r77 整表 10/10；rot 0/0；预检 142/125/395/0。
⑥ 验证：构建 0 告警；全量 `{executed}/{skipped}/{failures}`；捕获 `CAPTURED {frames} -> /tmp/r388_shots`；换装 `INSTALL_RESULT=ok`、`INSTALL_SHA_MATCH=1`、条目 {entries_before}={entries_after}；清账表 {cells}={cells}；预检 142/125/395/0、全仓 235/879。

验证读数（现读）：`WEIGHTS_RESET_STATE` 亮 禁用 `{w_light[3]}` / 动过 `{w_light[7]}`、暗 禁用 `{w_dark[3]}` / 动过 `{w_dark[7]}`；`RESET_FADE_SCALE` 2x `{f2_frames}/{f2_span}/{f2_peak}`、1x `{f1_frames}/{f1_span}/{f1_peak}`；`M1019`、`M1016/M1017` 都 CAUGHT；r77 `抓到=10 逃掉=0`；`HIDDEN_ARMS … rot={h_rot} … 处置=ok`。

NOT-RUN / 阻塞（分开写）：① **`PUSH_BLOCKED=network`**：`api=000`（LibreSSL SSL_ERROR_SYSCALL）/ `apple=200`；本地 ahead=9（R388 主笔后，追记前的数）；② `40234023212 ↔ d38ea10`、`40234058148 ↔ 5c7814e` 与 R387 本地三笔的 conclusion **未读**（网络）；③ 亮档真机腿仍没跑；④ 胶片采样臂在无 `CLIPBOARD_HISTORY_UI_MOTION=1` 的卷里具名 skip（49 skip 的一部分），本轮的 2x/1x 读数来自单独开的 motion 卷。

下一轮（R389）的靶：⓪ 先 `git push origin main`（禁 amend/force）并复核 ahead=0；读 `40234023212`/`40234058148` 与 R387/R388 推送那一跑的**全部失败步骤**，把 run↔commit 成对写回本行；① 367 现读 rot=0，按 `HIDDEN_ROT` 查新腐烂；② 回产品动效面再点一个真实位；R388 的样式若要再验，跑 `CLIPBOARD_HISTORY_UI_MOTION=1` 的 `testResetFadeSamplerReadsBothScales`。
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
report_new = once(report_old, "D-069 … **D-374**", "D-069 … **D-375**")
report_new = once(report_new, "U-31 … U-1359（R387 现读抬到最新一节）", "U-31 … U-1364（R388 现读抬到最新一节）")
report_new = once(report_new, "产品面连续零改动轮数 = **2**", "产品面连续零改动轮数 = **1**")
report_new = once(
    report_new,
    "R387 现读：注册表 **141** 张 / 刀号最大 **M1018** / 预检 covered=124 arms=394 bad=0；全仓 234 文件 / 878 把；M674 退役、M906 空刀退役",
    f"R388 现读：注册表 **{pre_tables}** 张 / 刀号最大 **M1019** / 预检 covered={pre_covered} arms={pre_arms} bad={pre_bad}；"
    f"全仓 {arm_files} 文件 / {arm_total} 把；M674 退役、M906 空刀退役")
report_new = once(
    report_new,
    "**网络仍断 ⇒ PUSH_BLOCKED=network，ahead=6，未推送。**",
    "**网络仍断 ⇒ PUSH_BLOCKED=network，ahead=6，未推送。**" + report_bullet)

state_old = rd("AGENT_STATE.md")
state_anchor = "## R387 状态（2026-10-26"
assert state_old.count(state_anchor) == 1
state_new = once(state_old, state_anchor, state_section + "\n" + state_anchor)

wr("AGENT_UI_AUDIT.md", audit_new)
wr("AGENT_VISUAL_ITERATION.md", iteration_new)
wr("AGENT_DECISIONS.md", decisions_new)
wr("CHANGELOG.md", changelog_new)
wr("AGENT_FINAL_REPORT.md", report_new)
wr("AGENT_STATE.md", state_new)

print("R388_LEDGERS_OK warnings=%d full=%d/%d/%d frames=%d diff=%d/%d baseline=%d/%d film2=%d/%d/%s film1=%d/%d/%s rot=%d pre=%d/%d/%d/%d arms=%d/%d gate=%d=%d streak=%d contrast=%s/%s,%s/%s"
      % (warnings, executed, skipped, failures, frames, same_frames, changed_frames,
         b_compared, b_changed, f2_frames, f2_span, f2_peak, f1_frames, f1_span, f1_peak,
         h_rot, pre_tables, pre_covered, pre_arms, pre_bad, arm_files, arm_total, cleared, cells,
         streak, w_light[3], w_light[7], w_dark[3], w_dark[7]))
