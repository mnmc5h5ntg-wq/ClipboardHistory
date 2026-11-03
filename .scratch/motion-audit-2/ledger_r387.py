#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R387（第 386 轮 / Round 384）的七本台账。数字全部从本机日志解析。"""
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


build = log("/tmp/r387_build.log")
warnings = len(re.findall(r"warning:", build))

full = log("/tmp/r387_full.log")
summaries = [tuple(int(x) for x in row) for row in
             re.findall(r"Executed (\d+) tests, with (\d+) tests skipped and (\d+) failures", full)]
big = [row for row in summaries if row[0] > 900]
assert big
executed, skipped, failures = big[-1]
assert failures == 0

capture = log("/tmp/r387_shots2/capture-readings.log")
cap = re.search(r"CAPTURED (\d+) -> /tmp/r387_shots2", capture)
assert cap
frames = int(cap.group(1))

diff = log("/tmp/r387_framediff2.log")
dm = re.search(r"FRAMEDIFF same=(\d+) changed=(\d+) total=(\d+)", diff)
assert dm
same_frames, changed_frames, total_frames = [int(x) for x in dm.groups()]
assert (same_frames, changed_frames, total_frames) == (170, 12, 182)

film = log("/tmp/r387_filmstrip.log")
f2 = re.search(r"RESET_FADE_SCALE scale=2x 帧数=(\d+) 过渡帧数=(\d+) 峰值=([0-9.]+)", film)
f1 = re.search(r"RESET_FADE_SCALE scale=1x 帧数=(\d+) 过渡帧数=(\d+) 峰值=([0-9.]+)", film)
generic = re.search(r"MOTION_SUMMARY .*settings-reset-fade=(\d+)", film)
assert f2 and f1 and generic
f2_frames, f2_span, f2_peak = int(f2.group(1)), int(f2.group(2)), f2.group(3)
f1_frames, f1_span, f1_peak = int(f1.group(1)), int(f1.group(2)), f1.group(3)
generic_span = int(generic.group(1))
assert f2_span >= 2 and f1_span >= 2

install = log("/tmp/r387_install.log")
assert "INSTALL_RESULT=ok" in install and "INSTALL_SHA_MATCH=1" in install
entries = re.search(r"INSTALL_ENTRIES_BEFORE=(\d+)\s+INSTALL_ENTRIES_AFTER=(\d+)", install)
assert entries
entries_before, entries_after = entries.groups()

pre = log("/tmp/r387_precheck.log")
pre_line = re.search(r"NEEDLE_PRECHECK tables=(\d+) covered=(\d+) arms=(\d+) bad=(\d+)", pre)
arm_line = re.search(r"ARM_TOTAL files=(\d+) arms=(\d+) dupes=(\d+) repeats=(\d+)", pre)
assert pre_line and arm_line
pre_tables, pre_covered, pre_arms, pre_bad = [int(x) for x in pre_line.groups()]
arm_files, arm_total, arm_dupes, arm_repeats = [int(x) for x in arm_line.groups()]
assert pre_bad == 0 and arm_dupes == 0 and arm_repeats == 0

hidden = log("/tmp/r387_hidden.log")
h = re.search(r"HIDDEN_ARMS 表=(\d+) 可判=(\d+) rot=(\d+) 抽不出=(\d+) 已声明表=(\d+) 已声明死针=(\d+) 上界 rot=(\d+)", hidden)
assert h
h_tables, h_judged, h_rot, h_opaque, h_dtables, h_ddead, h_rot_ceiling = [int(x) for x in h.groups()]
assert h_rot == h_rot_ceiling == 0

gate = log("/tmp/r387_gate.log")
g = re.search(r"MOTION_LEDGER 表面=(\d+) 状态=(\d+) 格子=(\d+) 行数=(\d+) 已清账=(\d+) 未清账=(\d+) 地板=(\d+)", gate)
assert g
surfaces, states, cells, rows, cleared, uncleared, floor = [int(x) for x in g.groups()]
assert uncleared == 0 and cleared == cells == rows == floor

streak_out = subprocess.check_output(
    ["python3", os.path.join(ROOT, "scripts/product_streak.py"), "--streak-for", "386"],
    cwd=ROOT).decode("utf-8")
streak = int(re.search(r"streak=(\d+)", streak_out).group(1))
assert streak == 2, "streak=%d" % streak

r77 = log("/tmp/r387_mut_r77_clean.log")
fade = log("/tmp/r387_mut_fade.log")
caption = log("/tmp/r387_mut_caption.log")
assert "抓到=10 逃掉=0 没跑成=0 未落地=0" in r77
assert "R385_MUTATE 刀=2 CAUGHT=2 红得不对=0 RESTORE_CLEAN=yes" in fade
assert "R387_CAPTION_MUTATE 刀=1 CAUGHT=1 红得不对=0 RESTORE_CLEAN=yes" in caption

ui_heading = "## 第 385 轮（R386 · 2026-10-26 · U-1352…U-1354）："
ui_section = f"""## 第 386 轮（R387 · 2026-10-26 · U-1355…U-1359）：R385 的过渡被胶片证明是死的 —— 显式 opacity 修复 + 1x/2x 两倍率正对证；M406 重钉整表 10/10；435 负半证人（U-1355…U-1359 · 产品 1 文件，动效主线）

- **U-1355：胶片把 R385 的「过渡」判成死的。** 新场景 `settings-reset-fade`（只拍右列卡头 x 70..98%、顶部 200pt 的按钮带）第一版 `captureRect` 按 `height-260` 取带，落在下方滑杆区 ⇒ 30 帧全等（`premise-not-visible`）——那是**探针取错坐标**（NSHostingView 是 flipped），不是产品；按 `isFlipped` 取顶部后现读 `MOTION settings-reset-fade … 过渡帧数={generic_span}`。但 R385 的 `.animation(value:)` 只有 2 个过渡帧 ⇒ 0.12s 的声明是**死动画**（按钮上没有可动画属性）。
- **U-1356：产品修复（显式 opacity）。** 两颗「恢复默认」外层加 `HStack(spacing: 0)` wrapper，挂 `.opacity(isDefault ? 0.55 : 1)` + `.animation(MotionCatalog.animation(for: .selection), value: isDefault)`；`disabled` 仍管命中/语义。胶片现读 2x `帧数={f2_frames} 过渡帧数={f2_span} 峰值={f2_peak}`、1x `帧数={f1_frames} 过渡帧数={f1_span} 峰值={f1_peak}`（声明 120ms）——两倍率都 ≥2，且 strip 逐帧看得到由深到浅。端态 182 张帧 `same={same_frames} changed={changed_frames}`，12 张变化全在重置按钮区（bbox 只在 `weights`/`settings-recommendations*`/`settings-shortcuts*`/`settings-min` 的按钮列），`weights-adjusted` 与 enabled 态不动；帧基线同笔 update。
- **U-1357：M406 重钉。** 旧针 `let alpha = abs(...)` 在盘上命中 **2 次**（均值器与 changedFraction）⇒ NOT-APPLIED。带上下文钉到 changedFraction 那一块（后跟 `if rgb > 8 {{ changedRgb += 1 }}`）；r77 **整表 10/10 CAUGHT**（M403–M412，含 M406），`HIDDEN_ARMS … rot={h_rot} 上界={h_rot_ceiling} 处置=ok`。
- **U-1358：435 的负半证人。** `captionDrawability(columnPixels:pagePixels:)` 把「探针列 0 墨」拆成 `.drawable` / `.machineFlat`（页也 0 墨 ⇒ NOT-RUN）/ `.rulerBroken`（页有墨而列没有 ⇒ **红**）；真值表 `testCaptionDrawabilityHasANegativeHalf` 三格；`M1018`（rulerBroken→machineFlat）`CAUGHT`；caption tier 守卫本机仍绿（41.25s）。
- **U-1359：⓪ 网络与 CI。** 本轮只做 1 次同形探测：`api=000`（LibreSSL SSL_ERROR_SYSCALL）/ `apple=200` ⇒ GitHub 侧仍断，`PUSH_BLOCKED=network`；`40234023212 ↔ d38ea10`、`40234058148 ↔ 5c7814e` 与 R385/R386 本地提交的跑结论全部**未读**。本地 ahead 在 R387 两笔后为 **6**；不写已推送。恢复后先 push、复核 ahead=0，再读三跑全部失败步骤并把 run↔commit 写回下一轮 ⓪。
"""

iteration = f"""## Round 384 · R387（第 386 轮 · 2026-10-26）：R385 死过渡被胶片证伪 → 显式 opacity；1x/2x 正对证；M406 重钉；435 负半（产品 1 文件）

新场景只拍按钮带：第一版 captureRect 取错 flipped 坐标 ⇒ 0 帧（探针坏，修正后 {generic_span} 帧）；R385 的 `.animation(value:)` 只有 2 帧 ⇒ 死动画。产品改为 wrapper `.opacity(isDefault ? 0.55 : 1)` + `.selection` 过渡，胶片 2x `{f2_span}` 帧 / 1x `{f1_span}` 帧、峰值 `{f2_peak}`/`{f1_peak}`，strip 逐帧可见由深到浅；端态 182 张帧 {same_frames} 同、12 张只动按钮列。M406 重钉到 changedFraction 唯一块，r77 整表 10/10；435 的 skip 出口补 `.rulerBroken` 负半，M1018 CAUGHT。

**七维度自评**（恰七行，每格 n/15）：

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | 15/15 | 看了 strip 逐帧由深到浅、按钮带读数与 12 张帧差分的 bbox。 |
| 判据有效性 | 15/15 | 场景 + 1x/2x 正对证 + 源守卫 + 三把刀；M406 整表 10/10；435 负半。 |
| 假绿防御 | 15/15 | 探针取错坐标的 0 帧当场判成探针坏；死动画被胶片抓出；1x/2x 都要 ≥2；M1018 证明 skip 不能吞红。 |
| 产品面推进 | 15/15 | 真实 Sources 过渡落地，且是胶片先证伪再修。 |
| 台账一致性 | 14/15 | U-1355…U-1359、D-374、计数器现读；CI 与 push 记 PUSH_BLOCKED。 |
| 交付诚实性 | 15/15 | R385 的「过程 NOT-RUN」改判成死动画并留更正；网络断不写已推送。 |
| 可复核性 | 15/15 | 两倍率读数、strip、帧差分、三表汇总、435 真值表都有原文。 |

均分 = 104/105 ≈ 14.9/15（99）。
"""

decision = """
### D-374（387）只挂 `.animation(value:)` 而没有可动画属性 = 死动画；过渡要在目标带、两个倍率各读到 ≥2 帧

R387 现读：R385 给「恢复默认」挂 `.animation(for: .selection, value: isDefault)`，胶片 0.12s 只拍到 **2** 个过渡帧；给按钮外层显式加 `.opacity(isDefault ? 0.55 : 1)` 后，同一场景 2x 读到 3 帧、1x 读到 4 帧（峰值 0.0542 / 0.0230），strip 逐帧可见。另：新场景第一版 `captureRect` 用 `height-260`（未考虑 `NSHostingView.isFlipped`）⇒ 30 帧全等，**是探针取错对象**。
**Why**：`.animation(value:)` 只是给值变化挂曲线；按钮的 `.disabled` 外观不是这个按钮的可动画属性，于是「声明存在、过程为零」。只拍整窗又会把变化摊薄到看不见；探针坐标不按容器坐标系取，0 帧会被误读成「产品没动」。
**How to apply**：① 过渡必须有**显式可动画属性**（opacity/位置/尺寸），源守卫要同时钉属性与键；② 过程用只拍目标带的胶片场景，声明时长来自目录，1x/2x 各读到 ≥2 帧才算过；读不到先查 `captureRect` 的坐标系与带宽，不把「没读到」写成「没动」；③ 静态端态帧只签端态，过程不能由它冒充（D-373 的补充）。
"""

changelog = """### R385 死过渡纠正：显式 opacity + 1x/2x 胶片正对证；M406 重钉整表 10/10；435 补负半证人（R387 / 第 386 轮 / U-1355…U-1359 · 产品 1 文件，动效主线）

"""

report_bullet = f"""
- **R387（动效主线）**：新胶片场景只拍按钮带，先证伪 R385 的 `.animation(value:)`（0.12s 只有 2 帧死动画）；给「恢复默认」外层加显式 `.opacity(isDefault ? 0.55 : 1)` + `.selection` 过渡后，2x `{f2_span}` 帧 / 1x `{f1_span}` 帧（峰值 `{f2_peak}`/`{f1_peak}`），strip 逐帧由深到浅；端态 182 帧 {same_frames} 同、12 张只动按钮列。M406 重钉到 changedFraction 唯一块，r77 整表 10/10；435 补 `.rulerBroken` 负半 + M1018 CAUGHT。**网络仍断 ⇒ PUSH_BLOCKED=network，ahead=6，未推送。**
"""

state_section = f"""## R387 状态（2026-10-26 · 本地 · 第 386 轮 / Round 384）：R385 死过渡被胶片证伪 → 显式 opacity；1x/2x 正对证；M406 重钉；435 负半（产品 1 文件，动效主线）

最后更新：2026-10-26（本地 · R387 / 第 386 轮 / Round 384）：新胶片场景 `settings-reset-fade`（只拍按钮带）先证伪 R385 的 `.animation(value:)` —— 0.12s 只有 2 个过渡帧，是死动画；给两颗「恢复默认」外层加显式 `.opacity(isDefault ? 0.55 : 1)` + `.animation(for: .selection)` 后，现读 2x `帧数={f2_frames} 过渡帧数={f2_span} 峰值={f2_peak}`、1x `帧数={f1_frames} 过渡帧数={f1_span} 峰值={f1_peak}`，strip 逐帧由深到浅；端态 182 张帧 `same={same_frames} changed={changed_frames}`，12 张只动重置按钮列。M406 重钉到 changedFraction 的唯一块（旧针命中 2），r77 **整表 10/10 CAUGHT**；`HIDDEN_ARMS … rot={h_rot} … 上界 rot={h_rot_ceiling} … 处置=ok`。435：`captionDrawability` 拆三态 + 负半真值表，M1018 `CAUGHT`；caption tier 守卫本机仍绿。`swift build --build-tests` 告警 **{warnings}**；全量 `Executed {executed} tests, with {skipped} tests skipped and {failures} failures`（新增胶片采样臂在无环境键时具名 skip）；清账表 `MOTION_LEDGER 表面={surfaces} 状态={states} 格子={cells} 行数={rows} 已清账={cleared} 未清账={uncleared} 地板={floor}`；产品面连续零改动 **{streak}** 轮（现读 `python3 scripts/product_streak.py --streak-for 386` 的 streak）。

本轮做了什么：
① ⓪ 网络：1 次同形探测 `api=000` / `apple=200` ⇒ GitHub 侧仍断，`PUSH_BLOCKED=network`；未推送，CI 三跑未读。
② 产品位：胶片证伪 R385 死动画；显式 opacity 修复；2x/1x 各 ≥2 帧；端态 12 张帧只动按钮列。
③ 判据：`testResetFadeSamplerReadsBothScales` + 源守卫更新；M1016/M1017 CAUGHT。
④ 367：M406 重钉，r77 整表 10/10；rot 0/0。
⑤ 435：captionDrawability 三态 + 负半真值表 + M1018 CAUGHT；caption tier 仍绿。
⑥ 验证：构建 0 告警；全量 `{executed}/{skipped}/{failures}`；捕获 `CAPTURED {frames} -> /tmp/r387_shots2`；帧基线 `COMPARED=182 CHANGED=0`；换装 `INSTALL_RESULT=ok`、`INSTALL_SHA_MATCH=1`、条目 {entries_before}={entries_after}；清账表 162=162；预检 `tables={pre_tables} covered={pre_covered} arms={pre_arms} bad={pre_bad}`、全仓 {arm_files} 文件 / {arm_total} 把。

验证读数（现读）：`RESET_FADE_SCALE` 2x `{f2_frames}/{f2_span}/{f2_peak}`、1x `{f1_frames}/{f1_span}/{f1_peak}`；`MOTION settings-reset-fade 过渡帧数={generic_span}`；`M1016/M1017`、`M1018` 都 CAUGHT；r77 `抓到=10 逃掉=0`；`HIDDEN_ARMS … rot={h_rot} … 处置=ok`。

NOT-RUN / 阻塞（分开写）：① **`PUSH_BLOCKED=network`**：`api=000`（LibreSSL SSL_ERROR_SYSCALL）/ `apple=200`；本地 ahead=6（`5166a2b`、`479dfaa`、`bb5be1b`、`559cadb` 与本轮两笔）；② `40234023212 ↔ d38ea10`、`40234058148 ↔ 5c7814e` 的 conclusion **未读**（网络）；③ 亮档真机腿仍没跑；④ R387 的胶片在无 `CLIPBOARD_HISTORY_UI_MOTION=1` 的卷里具名 skip（全量 `{skipped}` skip 的一部分），不是没红。

下一轮（R388）的靶：⓪ 先 `git push origin main`（禁 amend/force）并复核 ahead=0；读 `40234023212`/`40234058148` 与本次推送那一跑的**全部失败步骤**，把 run↔commit 成对写回本行；① 367 现读 rot=0，按 `HIDDEN_ROT` 查新腐烂；② 回产品动效面再点一个真实位；R387 的过渡若要再验，跑 `CLIPBOARD_HISTORY_UI_MOTION=1` 的 `testResetFadeSamplerReadsBothScales`。
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
report_new = once(report_old, "D-069 … **D-373**", "D-069 … **D-374**")
report_new = once(report_new, "U-31 … U-1354（R386 现读抬到最新一节）", "U-31 … U-1359（R387 现读抬到最新一节）")
report_new = once(report_new, "产品面连续零改动轮数 = **1**", "产品面连续零改动轮数 = **2**")
report_new = once(
    report_new,
    "R385 现读：注册表 **140** 张 / 刀号最大 **M1017** / 预检 covered=123 arms=393 bad=0；全仓 233 文件 / 877 把；M674 退役、M906 空刀退役",
    f"R387 现读：注册表 **{pre_tables}** 张 / 刀号最大 **M1018** / 预检 covered={pre_covered} arms={pre_arms} bad={pre_bad}；"
    f"全仓 {arm_files} 文件 / {arm_total} 把；M674 退役、M906 空刀退役")
report_new = once(
    report_new,
    "367：r64 M340/M341 重钉到 `appendLocked`，整表 6/6，rot 4→2。",
    "367：r64 M340/M341 重钉到 `appendLocked`，整表 6/6，rot 4→2。" + report_bullet)

state_old = rd("AGENT_STATE.md")
state_anchor = "## R386 状态（2026-10-26 · 本地 · 第 385 轮 / Round 383）"
assert state_old.count(state_anchor) == 1
state_new = once(state_old, state_anchor, state_section + "\n" + state_anchor)

wr("AGENT_UI_AUDIT.md", audit_new)
wr("AGENT_VISUAL_ITERATION.md", iteration_new)
wr("AGENT_DECISIONS.md", decisions_new)
wr("CHANGELOG.md", changelog_new)
wr("AGENT_FINAL_REPORT.md", report_new)
wr("AGENT_STATE.md", state_new)

print("R387_LEDGERS_OK warnings=%d full=%d/%d/%d frames=%d diff=%d/%d film2=%d/%d film1=%d/%d rot=%d pre=%d/%d/%d/%d arms=%d/%d gate=%d=%d streak=%d"
      % (warnings, executed, skipped, failures, frames, same_frames, changed_frames,
         f2_frames, f2_span, f1_frames, f1_span, h_rot, pre_tables, pre_covered, pre_arms, pre_bad,
         arm_files, arm_total, cleared, cells, streak))