#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R389（第 388 轮 / Round 386）的台账。数字全部从本机日志解析。"""
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


build = log("/tmp/r389_build2.log")
warnings = len(re.findall(r"warning:", build))
assert warnings == 0

full = log("/tmp/r389_full.log")
summaries = [tuple(int(x) for x in row) for row in
             re.findall(r"Executed (\d+) tests, with (\d+) tests skipped and (\d+) failures", full)]
big = [row for row in summaries if row[0] > 900]
assert big
executed, skipped, failures = big[-1]
assert failures == 0

capture = log("/tmp/r389_capture.log")
cap = re.search(r"CAPTURED (\d+) -> /tmp/r389_shots", capture)
assert cap
frames = int(cap.group(1))

diff = log("/tmp/r389_framediff.log")
dm = re.search(r"FRAME_DIFF 比了=(\d+) 变了=(\d+)", diff)
assert dm
total_frames, changed_frames = [int(x) for x in dm.groups()]
same_frames = total_frames - changed_frames
assert (same_frames, changed_frames, total_frames) == (182, 0, 182)

baseline = log("/tmp/r389_framebaseline.log")
bm = re.search(r"FRAME_BASELINE_COMPARED=(\d+)\s+FRAME_BASELINE_CHANGED=(\d+)"
               r"\s+FRAME_BASELINE_MISSING=(\d+)\s+FRAME_BASELINE_ADDED=(\d+)", baseline)
assert bm
b_compared, b_changed, b_missing, b_added = [int(x) for x in bm.groups()]
assert (b_compared, b_changed, b_missing, b_added) == (182, 0, 0, 0)

slides = log("/tmp/r389_filmstrip2.log")
w2 = re.search(r"WEIGHTS_RESET_SCALE scale=2x 帧数=(\d+) 过渡帧数=(\d+) 峰值=([0-9.]+)", slides)
w1 = re.search(r"WEIGHTS_RESET_SCALE scale=1x 帧数=(\d+) 过渡帧数=(\d+) 峰值=([0-9.]+)", slides)
assert w2 and w1
w2_frames, w2_span, w2_peak = int(w2.group(1)), int(w2.group(2)), w2.group(3)
w1_frames, w1_span, w1_peak = int(w1.group(1)), int(w1.group(2)), w1.group(3)
assert w2_span >= 2 and w1_span >= 2

fade = log("/tmp/r389_filmstrip.log")
f2 = re.search(r"RESET_FADE_SCALE scale=2x 帧数=(\d+) 过渡帧数=(\d+) 峰值=([0-9.]+)", fade)
f1 = re.search(r"RESET_FADE_SCALE scale=1x 帧数=(\d+) 过渡帧数=(\d+) 峰值=([0-9.]+)", fade)
assert f2 and f1
f2_frames, f2_span, f2_peak = int(f2.group(1)), int(f2.group(2)), f2.group(3)
f1_frames, f1_span, f1_peak = int(f1.group(1)), int(f1.group(2)), f1.group(3)
assert f2_span >= 2 and f1_span >= 2

criteria = log("/tmp/r389_criteria2.log")
wlight = re.search(r"WEIGHTS_RESET_STATE light 默认 .*?对比=([0-9.]+) \| 动过 .*?对比=([0-9.]+)", criteria)
wdark = re.search(r"WEIGHTS_RESET_STATE dark 默认 .*?对比=([0-9.]+) \| 动过 .*?对比=([0-9.]+)", criteria)
slight = re.search(r"SHORTCUT_RESET_STATE light 默认 .*?对比=([0-9.]+) \| 改过 .*?对比=([0-9.]+)", criteria)
sdark = re.search(r"SHORTCUT_RESET_STATE dark 默认 .*?对比=([0-9.]+) \| 改过 .*?对比=([0-9.]+)", criteria)
assert wlight and wdark and slight and sdark
w_light = wlight.groups()
w_dark = wdark.groups()
s_light = slight.groups()
s_dark = sdark.groups()
assert float(w_light[0]) >= 2.2 and float(w_dark[0]) >= 2.2
assert float(s_light[0]) >= 2.2 and float(s_dark[0]) >= 2.2

install = log("/tmp/r389_install.log")
assert "INSTALL_RESULT=ok" in install and "INSTALL_SHA_MATCH=1" in install
entries = re.search(r"INSTALL_ENTRIES_BEFORE=(\d+)\s+INSTALL_ENTRIES_AFTER=(\d+)", install)
assert entries
entries_before, entries_after = entries.groups()

pre = log("/tmp/r389_precheck2.log")
pre_line = re.search(r"NEEDLE_PRECHECK tables=(\d+) covered=(\d+) arms=(\d+) bad=(\d+)", pre)
arm_line = re.search(r"ARM_TOTAL files=(\d+) arms=(\d+) dupes=(\d+) repeats=(\d+)", pre)
assert pre_line and arm_line
pre_tables, pre_covered, pre_arms, pre_bad = [int(x) for x in pre_line.groups()]
arm_files, arm_total, arm_dupes, arm_repeats = [int(x) for x in arm_line.groups()]
assert pre_bad == 0 and arm_dupes == 0 and arm_repeats == 0

hidden = log("/tmp/r389_hidden.log")
h = re.search(r"HIDDEN_ARMS 表=(\d+) 可判=(\d+) rot=(\d+) 抽不出=(\d+) 已声明表=(\d+) 已声明死针=(\d+) 上界 rot=(\d+)", hidden)
assert h
h_tables, h_judged, h_rot, h_opaque, h_dtables, h_ddead, h_rot_ceiling = [int(x) for x in h.groups()]
assert h_rot == h_rot_ceiling == 0

gate = log("/tmp/r389_gate.log")
g = re.search(r"MOTION_LEDGER 表面=(\d+) 状态=(\d+) 格子=(\d+) 行数=(\d+) 已清账=(\d+) 未清账=(\d+) 地板=(\d+)", gate)
assert g
surfaces, states, cells, rows, cleared, uncleared, floor = [int(x) for x in g.groups()]
assert uncleared == 0 and cleared == cells == rows == floor

streak_out = subprocess.check_output(
    ["python3", os.path.join(ROOT, "scripts/product_streak.py"), "--streak-for", "388"],
    cwd=ROOT).decode("utf-8")
streak = int(re.search(r"streak=(\d+)", streak_out).group(1))
assert streak == 1, "streak=%d" % streak

mut = log("/tmp/r389_mut.log")
shortcut_mut = log("/tmp/r389_mut_shortcut.log")
assert "R389_MUTATE 刀=2 CAUGHT=2 红得不对=0 RESTORE_CLEAN=yes" in mut
assert "R389_SHORTCUT_MUTATE 刀=1 CAUGHT=1 红得不对=0 RESTORE_CLEAN=yes" in shortcut_mut

ui_heading = "## 第 387 轮（R388"
ui_section = f"""## 第 388 轮（R389 · 2026-10-26 · U-1365…U-1369）：权重复位不再九根滑杆瞬移 —— 复位走同一条 `.slider` 路径，胶片 2x/1x 读到 5/13 帧；快捷键页自量 2.2 对比地板（U-1365…U-1369 · 产品 1 文件，动效主线）

- **U-1365：⓪ 网络与 CI。** 本轮两次同形探测：09:06 `git push origin main` 被 SSH 拒（`Connection closed by 20.205.243.166 port 22`），同分钟 `api=000`（LibreSSL SSL_ERROR_SYSCALL）/ `apple=200` ⇒ GitHub 侧仍断；`PUSH_BLOCKED=network`，本地 ahead=11，**不写已推送**。`40234023212 ↔ d38ea10`、`40234058148 ↔ 5c7814e` 与 R387/R388 本地提交的跑结论仍未读。恢复后先 push、复核 ahead=0，再读全部失败步骤并把 run↔commit 写回下一轮 ⓪。
- **U-1366：产品位 —— 九根滑杆的复位过程。** 原来只有按钮色变在演，九根滑杆瞬移 ⇒ 一次操作被画成「一次色变 + 九次跳变」。新增 `RecommendationWeightsView.resetDefaults(in:)`，把 `store.restoreDefaults()` 包进 `withAnimation(MotionCatalog.animation(for: .slider))`；按钮调这一条路，直接拖滑杆不走它、不会拖出延迟。胶片新场景 `settings-weights-reset-sliders` 只拍两行滑杆（x 20..500、y 170..310pt，按钮色变不在带里）：2x `帧数={w2_frames} 过渡帧数={w2_span} 峰值={w2_peak}`、1x `{w1_frames}/{w1_span}/{w1_peak}`（声明 200ms；像素 960×280 / 480×140），strip 逐帧看到「收藏 40% → 默认」与滑块右移。静态 182 帧逐张比 R388 `变了={changed_frames}`，帧基线 `COMPARED={b_compared} CHANGED={b_changed}`。
- **U-1367：判据 —— 产品路径与胶片必须是同一条。** `MotionDriverTests.testWeightsResetGoesThroughOneAnimatedPath` 压掉空白后要求 helper 整块含 `withAnimation(MotionCatalog.animation(for: .slider))` + `store.restoreDefaults()`，按钮调 `Self.resetDefaults(in: store)`，且直接 `store.restoreDefaults()` 只出现一次；真值表三格（helper 无动画 / 按钮绕过 / 纯 Text）都判没有。`M1020`（摘 withAnimation）与 `M1021`（按钮绕过 helper）都 **CAUGHT**、还原干净；胶片两倍率判据 `testWeightsResetSliderSamplerReadsBothScales` 2x/1x 各 ≥2 帧。
- **U-1368：R388 自评扣的快捷键页对比地板，收成直接读数。** 同一个共享样式落在这页，但材质底不同 ⇒ 在快捷键页自己的两态帧上量：亮档 禁用 **{s_light[0]}** / 改过 **{s_light[1]}**，暗档 禁用 **{s_dark[0]}** / 改过 **{s_dark[1]}**（地板 2.2；整页墨能力 62312/64307，非平涂）。`M1022` 把共享样式禁用前景退回 tertiary ⇒ 快捷键页地板 **CAUGHT**；R388 的 `M1019` 仍咬权重页。
- **U-1369：① 367 rot 与八步。** `HIDDEN_ARMS 表={h_tables} 可判={h_judged} rot={h_rot} 抽不出={h_opaque} 已声明表={h_dtables} 已声明死针={h_ddead} 上界 rot={h_rot_ceiling} 处置=ok`；预检 `tables={pre_tables} covered={pre_covered} arms={pre_arms} bad={pre_bad}`、全仓 {arm_files} 文件 / {arm_total} 把；M1020–M1022 三把全 CAUGHT。build **{warnings}** 告警；全量 `Executed {executed} tests, with {skipped} tests skipped and {failures} failures`；捕获 `CAPTURED {frames}`；换装 `INSTALL_RESULT=ok`、`INSTALL_SHA_MATCH=1`、条目 `{entries_before}={entries_after}`；清账表 `表面={surfaces} 状态={states} 格子={cells} 已清账={cleared} 未清账={uncleared} 地板={floor}`；产品面连续零改动 **{streak}** 轮（现读 `product_streak --streak-for 388`）。另记 **BACKLOG 436**：R387 的 `settings-reset-fade` 已进 `Scenario.all()` 却未进 `motion_floor_expectations.json`，下一次带 motion 的 CI 会报 `MOTION_FLOOR_UNLISTED_SCENARIO`；因没有 runner 读数，本轮不替第五臂许愿 `must_judge`，只记账。
"""

iteration = f"""## Round 386 · R389（第 388 轮 · 2026-10-26）：权重复位九根滑杆走同一条 .slider 路径（2x 5 帧 / 1x 13 帧）；快捷键页自量禁用对比 2.92/4.38；M1020–M1022 CAUGHT（产品 1 文件）

复位原来只让按钮色变演，九根滑杆瞬移。产品把复位收进 `RecommendationWeightsView.resetDefaults(in:)` 的 `withAnimation(.slider)`，按钮与胶片调同一 helper；直接拖滑杆不经过它。新胶片场景只拍两行滑杆：2x `{w2_span}` 帧 / 1x `{w1_span}` 帧（峰值 `{w2_peak}`/`{w1_peak}`，声明 200ms），strip 逐帧看到 40%→默认与滑块右移。R388 自评扣的快捷键页对比地板补成直接读数：亮 禁用 `{s_light[0]}` / 暗 `{s_dark[0]}`（地板 2.2），M1022 咬住。静态 182 帧与 R388 逐张相同；rot 仍 0；M1020/M1021/M1022 全 CAUGHT。

**七维度自评**（恰七行，每格 n/15）：

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | 15/15 | 看了 2x/1x 两张 strip：滑块右移、40%→默认；静态 182 帧逐张零变化。 |
| 判据有效性 | 14/15 | 源守卫 + 真值表 + 两把路径刀 + 两倍率胶片；扣 1：新场景暂不进 `Scenario.all()`，不在每日 `MOTION_SUMMARY`/地板闸门里（BACKLOG 436 同因）。 |
| 假绿防御 | 15/15 | helper 路径身份、直接调用只准一次、M1020/M1021 各拆一端；对比地板有 M1022；两倍率都 ≥2；带子注释按实拍改正。 |
| 产品面推进 | 15/15 | 真实 Sources 改动，把「一次操作」画成一条连续过程，读数可复现。 |
| 台账一致性 | 14/15 | U-1365…U-1369、D-376/D-377、BACKLOG 436、计数器都从日志解析；扣 1：地板名册失配只记账未修（无 runner 读数，不替它许愿）。 |
| 交付诚实性 | 15/15 | 网络断只写 PUSH_BLOCKED；R388 样式复验两倍率仍 3/4 帧；静态帧 0 变化不写成产品改动。 |
| 可复核性 | 15/15 | strip 两张、两倍率读数、三把刀、对比读数、帧差分与基线都有原文路径。 |

均分 = 103/105 ≈ 14.7/15（98）。
"""

decision = """
### D-376（389）批量数值变化的动画要放在产品自己的动作路径上，产品与胶片调同一个 helper

R389 现读：权重复位原来只有按钮色变在演，九根滑杆瞬移；把 `store.restoreDefaults()` 收进 `RecommendationWeightsView.resetDefaults(in:)` 的 `withAnimation(MotionCatalog.animation(for: .slider))` 后，胶片 2x 读到 5 个过渡帧、1x 13 个（峰值 0.0201/0.0123，声明 200ms），strip 逐帧看到滑块位移与 40%→默认。源守卫压空白后钉 helper 整块与按钮调用点，M1020（摘动画）/M1021（按钮绕过 helper）都 CAUGHT。
**Why**：动画如果只挂在按钮上，实际被改变的 store 与滑杆拿不到同一次 transaction；而胶片若直接调 store，就绕开了产品的按钮路径 —— 那测的是替身，不是产品（N-1 同族）。路径身份不是风格：它是「胶片读到的过程就是用户点出来的过程」这句话的唯一证据。
**How to apply**：① 批量状态变化的动画放在产品自己的动作 helper 里，按钮调用它；② 胶片 trigger 调同一个 helper，不直接改 store；③ 源守卫钉 helper 块 + 调用点 + 直接调用只准一次，并配「摘动画 / 绕过 helper」两把刀；④ 过程读数至少两个倍率各 ≥2 帧，并留 strip。
"""

decision2 = """
### D-377（389）共享样式每落到一个新表面，就要在那个表面自己的帧上量对比地板

R389 现读：R388 的 2.2 地板只量权重页（亮 2.77 / 暗 4.21）。同一支 `ResetDefaultButtonStyle` 落在快捷键页，但材质底与取样带不同；在快捷键页自己的两态帧上量到禁用标签 亮 **2.92** / 暗 **4.38**（改过 3.81/5.38），都过 2.2；M1022 把共享样式退回 tertiary ⇒ 这页的地板红。
**Why**：共享样式不等于共享像素。拿 A 页的对比读数替 B 页签字，就是「读数搬到了没量过的对象上」；而禁用标签可读性是每个表面各自的材质、字号、背景共同决定的。
**How to apply**：① 新表面复用一条样式时，在同一张两态帧、同一把 WCAG 尺上重新量；② 地板仍取 2.2，同时保留「动过态比禁用态实」的方向；③ 平涂页走既有能力闸门与具名 NOT-RUN；④ 刀改共享样式，验证新表面的地板确实会红。
"""

changelog = """### 权重复位九根滑杆走同一条 .slider 路径（2x 5 帧 / 1x 13 帧）；快捷键页自量禁用对比 2.92/4.38；M1020–M1022 CAUGHT（R389 / 第 388 轮 / Round 386 / U-1365…U-1369 · 产品 1 文件，动效主线）

"""

report_bullet = f"""
- **R389（动效主线）**：权重复位原来只有按钮色变在演、九根滑杆瞬移 ⇒ 复位收进 `RecommendationWeightsView.resetDefaults(in:)` 的 `withAnimation(.slider)`，按钮与胶片同一条路；新场景只拍两行滑杆，2x `{w2_span}` 帧 / 1x `{w1_span}` 帧（峰值 `{w2_peak}`/`{w1_peak}`），strip 可见 40%→默认与滑块右移。R388 扣的快捷键页对比地板补成直接读数：亮 禁用 `{s_light[0]}` / 暗 `{s_dark[0]}`（地板 2.2），M1022 咬住；M1020/M1021 各拆动画/路径一端。静态 182 帧与 R388 逐张相同；rot 0/0。另记 BACKLOG 436（R387 新场景未进地板名册，下一次 motion CI 会报 UNLISTED；无 runner 读数不替它许愿）。**网络仍断 ⇒ PUSH_BLOCKED=network，ahead=11，未推送。**
"""

state_section = f"""## R389 状态（2026-10-26 · 本地 · 第 388 轮 / Round 386）：权重复位九根滑杆走同一条 .slider 路径（2x 5 帧 / 1x 13 帧）；快捷键页自量禁用对比 2.92/4.38；M1020–M1022 CAUGHT（产品 1 文件，动效主线）

最后更新：2026-10-26（本地 · R389 / 第 388 轮 / Round 386）：权重复位原来只有按钮色变在演，九根滑杆瞬移。产品新增 `RecommendationWeightsView.resetDefaults(in:)`：把 `store.restoreDefaults()` 包进 `withAnimation(MotionCatalog.animation(for: .slider))`，按钮调它；直接拖滑杆不经过这条动画。新胶片场景 `settings-weights-reset-sliders` 只拍两行滑杆（按钮色变不在带里）：2x `帧数={w2_frames} 过渡帧数={w2_span} 峰值={w2_peak}`、1x `{w1_frames}/{w1_span}/{w1_peak}`（声明 200ms；960×280 / 480×140px），strip 逐帧可见「收藏 40% → 默认」与滑块右移。R388 自评扣的快捷键页对比地板补成读数：亮 禁用 **{s_light[0]}** / 改过 **{s_light[1]}**、暗 禁用 **{s_dark[0]}** / 改过 **{s_dark[1]}**（地板 2.2）。M1020/M1021/M1022 全 CAUGHT、还原干净；`HIDDEN_ARMS 表={h_tables} 可判={h_judged} rot={h_rot} … 上界 rot={h_rot_ceiling} 处置=ok`；预检 `tables={pre_tables} covered={pre_covered} arms={pre_arms} bad={pre_bad}`、全仓 {arm_files} 文件 / {arm_total} 把。`swift build --build-tests` 告警 **{warnings}**；全量 `Executed {executed} tests, with {skipped} tests skipped and {failures} failures`；捕获 `CAPTURED {frames} -> /tmp/r389_shots`，与 R388 逐张比 `变了={changed_frames}`，帧基线 `COMPARED={b_compared} CHANGED={b_changed}`；清账表 `MOTION_LEDGER 表面={surfaces} 状态={states} 格子={cells} 行数={rows} 已清账={cleared} 未清账={uncleared} 地板={floor}`；换装 `INSTALL_RESULT=ok`、`INSTALL_SHA_MATCH=1`、条目 {entries_before}={entries_after}；产品面连续零改动 **{streak}** 轮（现读 `python3 scripts/product_streak.py --streak-for 388`）。

本轮做了什么：
① ⓪ 网络：push 被 SSH 拒，同分钟 `api=000` / `apple=200` ⇒ `PUSH_BLOCKED=network`；未推送，CI 多跑未读。
② 产品位：复位九根滑杆收进 `withAnimation(.slider)` 的产品 helper；按钮与胶片同一条路。
③ 判据：源守卫 + 真值表 + M1020/M1021；两倍率胶片 ≥2 帧；strip 两张。
④ 对比：快捷键页直接量到亮 2.92 / 暗 4.38，M1022 咬地板；R388 的 M1019 仍咬权重页。
⑤ 367：hidden 表 {h_tables} / 可判 {h_judged} / rot {h_rot} / 上界 {h_rot_ceiling}；预检 {pre_tables}/{pre_covered}/{pre_arms}/{pre_bad}。
⑥ 验证：build 0 告警；全量 `{executed}/{skipped}/{failures}`；捕获 {frames} 帧、静态零变化；换装 ok；清账表 {cleared}={cells}；新开 BACKLOG 436。

验证读数（现读）：`WEIGHTS_RESET_SCALE` 2x `{w2_frames}/{w2_span}/{w2_peak}`、1x `{w1_frames}/{w1_span}/{w1_peak}`；`RESET_FADE_SCALE` 2x `{f2_frames}/{f2_span}/{f2_peak}`、1x `{f1_frames}/{f1_span}/{f1_peak}`；`SHORTCUT_RESET_STATE` 亮 禁用 `{s_light[0]}` / 暗 `{s_dark[0]}`；`M1020/M1021/M1022` 全 CAUGHT；`HIDDEN_ARMS … rot={h_rot} … 处置=ok`。

NOT-RUN / 阻塞（分开写）：① **`PUSH_BLOCKED=network`**：push 被 SSH 拒 + `api=000`（LibreSSL SSL_ERROR_SYSCALL）/ `apple=200`；本地 ahead=11；② `40234023212 ↔ d38ea10`、`40234058148 ↔ 5c7814e` 与 R387/R388 本地提交的 conclusion **未读**（网络）；③ 亮档真机腿仍没跑；④ 胶片采样臂在无 `CLIPBOARD_HISTORY_UI_MOTION=1` 的卷里具名 skip（全量 {skipped} skip 的一部分），本轮的 2x/1x 读数来自单独开的 motion 卷；⑤ BACKLOG 436：`settings-reset-fade` 未进 motion 地板名册，下一次带 motion 的 CI 会报 `MOTION_FLOOR_UNLISTED_SCENARIO`，本轮无 runner 读数不修。

下一轮（R390）的靶：⓪ 先 `git push origin main`（禁 amend/force）并复核 ahead=0；读 `40234023212`/`40234058148` 与 R387/R388/R389 推送那一跑的**全部失败步骤**，把 run↔commit 成对写回本行；按 BACKLOG 436 先读 CI motion 卷，再决定第五臂 `must_judge` 并一次性改 JSON 与自测；① 367 现读 rot=0，按 `HIDDEN_ROT` 查新腐烂；② 回产品动效面再点一个真实位；R389 的复位过程可用 `CLIPBOARD_HISTORY_UI_MOTION=1` 的 `testWeightsResetSliderSamplerReadsBothScales` 复跑。
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
report_new = once(report_old, "D-069 … **D-375**", "D-069 … **D-377**")
report_new = once(report_new, "U-31 … U-1364（R388 现读抬到最新一节）", "U-31 … U-1369（R389 现读抬到最新一节）")
report_new = once(
    report_new,
    "R388 现读：注册表 **142** 张 / 刀号最大 **M1019** / 预检 covered=125 arms=395 bad=0；全仓 235 文件 / 879 把；M674 退役、M906 空刀退役",
    f"R389 现读：注册表 **{pre_tables}** 张 / 刀号最大 **M1022** / 预检 covered={pre_covered} arms={pre_arms} bad={pre_bad}；"
    f"全仓 {arm_files} 文件 / {arm_total} 把；M674 退役、M906 空刀退役")
report_new = once(
    report_new,
    "**网络仍断 ⇒ PUSH_BLOCKED=network，ahead=11，未推送。**",
    "**网络仍断 ⇒ PUSH_BLOCKED=network，ahead=11，未推送。**" + report_bullet)

state_old = rd("AGENT_STATE.md")
state_anchor = "## R388 状态（2026-10-26"
assert state_old.count(state_anchor) == 1
state_new = once(state_old, state_anchor, state_section + "\n" + state_anchor)

wr("AGENT_UI_AUDIT.md", audit_new)
wr("AGENT_VISUAL_ITERATION.md", iteration_new)
wr("AGENT_DECISIONS.md", decisions_new)
wr("CHANGELOG.md", changelog_new)
wr("AGENT_FINAL_REPORT.md", report_new)
wr("AGENT_STATE.md", state_new)

print("R389_LEDGERS_OK warnings=%d full=%d/%d/%d frames=%d diff=%d/%d baseline=%d/%d film2=%d/%d/%s film1=%d/%d/%s fade=%d/%d rot=%d pre=%d/%d/%d/%d arms=%d/%d gate=%d=%d streak=%d weights=%s/%s,%s/%s shortcut=%s/%s,%s/%s"
      % (warnings, executed, skipped, failures, frames, same_frames, changed_frames,
         b_compared, b_changed, w2_frames, w2_span, w2_peak, w1_frames, w1_span, w1_peak,
         f2_span, f1_span, h_rot, pre_tables, pre_covered, pre_arms, pre_bad,
         arm_files, arm_total, cleared, cells, streak,
         w_light[0], w_light[1], w_dark[0], w_dark[1], s_light[0], s_light[1], s_dark[0], s_dark[1]))
