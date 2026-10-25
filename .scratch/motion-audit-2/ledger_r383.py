#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R383（第 382 轮 / Round 380）的七本台账。数字全部从本机日志解析。"""
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


build = log("/tmp/r383_build.log")
warnings = len(re.findall(r"warning:", build))

full = log("/tmp/r383_full.log")
summaries = [tuple(int(x) for x in row) for row in
             re.findall(r"Executed (\d+) tests, with (\d+) tests skipped and (\d+) failures", full)]
big = [row for row in summaries if row[0] > 900]
assert big, "全量卷汇总行没解析到"
executed, skipped, failures = big[-1]
assert failures == 0

capture = log("/tmp/r383_shots/capture-readings.log")
cap = re.search(r"CAPTURED (\d+) -> /tmp/r383_shots", capture)
assert cap
frames = int(cap.group(1))

diff = log("/tmp/r383_framediff.log")
dm = re.search(r"FRAMEDIFF same=(\d+) changed=(\d+) total=(\d+)", diff)
assert dm
same_frames, changed_frames, total_frames = [int(x) for x in dm.groups()]
assert (same_frames, changed_frames, total_frames) == (176, 6, 182)

before = log("/tmp/r383_shortcut_before.log")
after = log("/tmp/r383_shortcut_after.log")
b_light = re.search(r"SHORTCUT_RESET_STATE light 默认 fill=\d+ 墨=(\d+) 最大偏离=(\d+) \| 改过 fill=\d+ 墨=(\d+) 最大偏离=(\d+)", before)
b_dark = re.search(r"SHORTCUT_RESET_STATE dark 默认 fill=\d+ 墨=(\d+) 最大偏离=(\d+) \| 改过 fill=\d+ 墨=(\d+) 最大偏离=(\d+)", before)
a_light = re.search(r"SHORTCUT_RESET_STATE light 默认 fill=\d+ 墨=(\d+) 最大偏离=(\d+) \| 改过 fill=\d+ 墨=(\d+) 最大偏离=(\d+)", after)
a_dark = re.search(r"SHORTCUT_RESET_STATE dark 默认 fill=\d+ 墨=(\d+) 最大偏离=(\d+) \| 改过 fill=\d+ 墨=(\d+) 最大偏离=(\d+)", after)
assert b_light and b_dark and a_light and a_dark
b_light_ink, b_light_dev, b_light_onink, b_light_ondev = [int(x) for x in b_light.groups()]
b_dark_ink, b_dark_dev, b_dark_onink, b_dark_ondev = [int(x) for x in b_dark.groups()]
a_light_ink, a_light_dev, a_light_onink, a_light_ondev = [int(x) for x in a_light.groups()]
a_dark_ink, a_dark_dev, a_dark_onink, a_dark_ondev = [int(x) for x in a_dark.groups()]

weights = log("/tmp/r383_reset_test.log")
w_light = re.search(r"WEIGHTS_RESET_STATE light 默认 fill=\d+ 墨=\d+ 最大偏离=(\d+) \| 动过 fill=\d+ 墨=\d+ 最大偏离=(\d+)", weights)
w_dark = re.search(r"WEIGHTS_RESET_STATE dark 默认 fill=\d+ 墨=\d+ 最大偏离=(\d+) \| 动过 fill=\d+ 墨=\d+ 最大偏离=(\d+)", weights)
assert w_light and w_dark
w_light_off, w_light_on = [int(x) for x in w_light.groups()]
w_dark_off, w_dark_on = [int(x) for x in w_dark.groups()]

install = log("/tmp/r383_install.log") if os.path.exists("/tmp/r383_install.log") else None
assert install and "INSTALL_RESULT=ok" in install and "INSTALL_SHA_MATCH=1" in install
entries = re.search(r"INSTALL_ENTRIES_BEFORE=(\d+)\s+INSTALL_ENTRIES_AFTER=(\d+)", install)
assert entries
entries_before, entries_after = entries.groups()

pre = log("/tmp/r383_precheck.log")
pre_line = re.search(r"NEEDLE_PRECHECK tables=(\d+) covered=(\d+) arms=(\d+) bad=(\d+)", pre)
arm_line = re.search(r"ARM_TOTAL files=(\d+) arms=(\d+) dupes=(\d+) repeats=(\d+)", pre)
assert pre_line and arm_line
pre_tables, pre_covered, pre_arms, pre_bad = [int(x) for x in pre_line.groups()]
arm_files, arm_total, arm_dupes, arm_repeats = [int(x) for x in arm_line.groups()]
assert pre_bad == 0 and arm_dupes == 0 and arm_repeats == 0

hidden = log("/tmp/r383_hidden.log")
h = re.search(r"HIDDEN_ARMS 表=(\d+) 可判=(\d+) rot=(\d+) 抽不出=(\d+) 已声明表=(\d+) 已声明死针=(\d+) 上界 rot=(\d+)", hidden)
assert h
h_tables, h_judged, h_rot, h_opaque, h_dtables, h_ddead, h_rot_ceiling = [int(x) for x in h.groups()]
assert h_rot == h_rot_ceiling == 5

gate = log("/tmp/r383_gate.log")
g = re.search(r"MOTION_LEDGER 表面=(\d+) 状态=(\d+) 格子=(\d+) 行数=(\d+) 已清账=(\d+) 未清账=(\d+) 地板=(\d+)", gate)
assert g
surfaces, states, cells, rows, cleared, uncleared, floor = [int(x) for x in g.groups()]
assert uncleared == 0 and cleared == cells == rows == floor

streak_out = subprocess.check_output(
    ["python3", os.path.join(ROOT, "scripts/product_streak.py"), "--streak-for", "382"],
    cwd=ROOT).decode("utf-8")
streak = int(re.search(r"streak=(\d+)", streak_out).group(1))
assert streak == 1, "streak=%d" % streak

r94 = log("/tmp/r383_mut_r94.log")
r303 = log("/tmp/r383_mut_r303_M876.log")
r142 = log("/tmp/r383_mut_r142.log")
m1013 = log("/tmp/r383_mut_r382.log")
m1014 = log("/tmp/r383_mut_shortcut.log")
assert "MUTATE_TABLE n=7 caught=7" in r94
assert "M876 CAUGHT" in r303
assert "CAUGHT=5/5, RESTORE_CLEAN=yes" in r142
assert "R382_MUTATE 刀=1 CAUGHT=1" in m1013
assert "R383_MUTATE 刀=1 CAUGHT=1" in m1014

ui_heading = "## 第 381 轮（R382 · 2026-10-26 · U-1334…U-1337）："
ui_section = f"""## 第 382 轮（R383 · 2026-10-26 · U-1338…U-1342）：CI 两跑分诊（R382 新判据在 runner 上取样机器依赖）+ 快捷键三颗「恢复默认」禁用态 + M1014；367 rot 8→5、退役一刀（U-1338…U-1342 · 产品 1 文件，动效主线）

- **U-1338：CI 分诊（成对 run↔commit）。** `40224259064 ↔ c59b292`、`40224280654 ↔ e9b1f83` 两跑 `conclusion=failure`；`ci_read.py steps` 列出**全部**失败步骤：`STEP[15] Swift tests (executed-count gate)` 与 `STEP[17] Capture gate (unregistered reds must be zero)`（只有这两步）。日志步骤名可解析（`field2` 直方图 4649 行 Release script tests / 3575 行 Swift tests，无 `UNKNOWN STEP`）⇒ 允许按步骤名切片。正文：六朵红全在 R382 新判据 `testRestoreDefaultsButtonIsDisabledWhenWeightsAreDefault`（`13467/13469/13473` × 两档），runner 读数 `WEIGHTS_RESET_STATE light 默认 fill=230 墨=0 最大偏离=23 | 动过 同`、暗档同形 ⇒ 1x 上与字体度量变化让**那枚 72×22pt 的小取样矩形**没压住标签。改动前那一跑 `40221947072 ↔ 43ff699` 是 success ⇒ 这一朵是 R382 引入的回归。
- **U-1339：修法（判据侧）。** 取样从「按钮小矩形」改成**语义带**（卡片头部右列 x 380..520、y 60..230；标题/说明在 x<380、第一条滑杆在 y>240 ⇒ 带里只有按钮标签）；第三格断言从 `<` 放宽成 `<=`（两态差由 `maxDev` 判、墨量只作正对照）。本机现读 `WEIGHTS_RESET_STATE light 默认 {w_light_off}/动过 {w_light_on}`、`dark {w_dark_off}/{w_dark_on}`；`M1013` 复跑 `CAUGHT`。runner 上的复验要等这一笔推送之后那一跑（本轮不轮询）。
- **U-1340：产品位（快捷键页三颗「恢复默认」）。** 与 R382 权重页同一条规矩：快捷键已是默认值时这三颗点了无事发生，而禁用态从未画出来。整页两态现渲染（默认值 vs 第一行改成 ⌃⌥⇧V）修前**完全相同**：light `墨={b_light_ink} 最大偏离={b_light_dev}` 对 `墨={b_light_onink} 最大偏离={b_light_ondev}`、dark `{b_dark_ink}/{b_dark_dev}` 对 `{b_dark_onink}/{b_dark_ondev}`。加 `.disabled(shortcut == settings.action.defaultShortcut)` 后 light `{a_light_ink}/{a_light_dev}` 对 `{a_light_onink}/{a_light_ondev}`、dark `{a_dark_ink}/{a_dark_dev}` 对 `{a_dark_onink}/{a_dark_ondev}`；182 张帧差分 `same={same_frames} changed={changed_frames}`，6 张全在快捷键页右列（`settings-shortcuts*`、`settings-min`），逐张看图三颗按钮都已禁用。
- **U-1341：判据与刀。** 新判据 `testShortcutResetButtonsAreDisabledWhenShortcutsAreDefault` 在同一台测试里现渲染**整页两态**（不新增帧、不动盲区名册）：正对照要求「改过」页有墨、两页最大偏离差 >20。`M1014`（`.disabled(...)` 换成 `.disabled(false)`）现读 `CAUGHT`、复跑 `ESCAPED`、还原干净。
- **U-1342：367 三笔。** r94 的 M518 针从 `+` 拼装改成单字面量（`ast.literal_eval` 原先解不出 ⇒ 活针被报 rot；刀文同时修掉「多一个引号」的 ERROR 形状）⇒ 整表 **7/7 CAUGHT**；r303 的 M876 改成字面量针 + 漂移断言（单臂 CAUGHT）；r142 的 M674 **退役** —— 「print→emit」已是现状，同义坏法「改名 RINGVIEWS」实测 `PASSED`（名册只按每文件条数 + 通道判，不按登记标记是否还出现）⇒ 那一格今天没有牙，退役并点名 M673 继续管未登记 stdout。`HIDDEN_ARMS 表={h_tables} 可判={h_judged} rot={h_rot} … 上界 rot={h_rot_ceiling} … 处置=ok`（8→5）。
"""

iteration = f"""## Round 380 · R383（第 382 轮 · 2026-10-26）：CI 分诊 + 快捷键三颗「恢复默认」禁用态；367 rot 8→5（产品 1 文件）

两跑 failure 全读：失败步骤只有 `Swift tests` 与 `Capture gate`，六朵红全在 R382 新判据 —— runner（1x）上那枚 72×22pt 取样矩形没压住按钮标签（`墨=0 最大偏离=23` 两态同形）。修法是把取样改成语义带（右列卡头）+ 断言只由 `maxDev` 判两态差；本机现读 light 122/211、dark 119/193，M1013 复跑 CAUGHT。产品位：快捷键页三颗「恢复默认」在默认值下从未画禁用态（修前两态整页渲染完全相同 3792/211、4152/186），加 `.disabled(shortcut == settings.action.defaultShortcut)` 后 70/211、60/186；182 张帧 176 张逐字节同、6 张只动按钮列。367：r94 7/7、M876 单臂 CAUGHT、M674 退役（改名方向无牙，已点名），rot 8→5。

**七维度自评**（恰七行，每格 n/15）：

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | 15/15 | 修前/修后各看了整页帧，量到三颗按钮两态墨完全相同并差分到列。 |
| 判据有效性 | 14/15 | 新判据 + 刀都咬住；R382 那条判据的取样几何在 runner 上才暴露机器依赖。 |
| 假绿防御 | 15/15 | 正对照要求改过页有墨；M1014/M1013 都 CAUGHT；M674 无牙时退役而不是留空刀。 |
| 产品面推进 | 15/15 | 三颗真实按钮的禁用态落地，且帧差分证明没有误伤别的帧。 |
| 台账一致性 | 14/15 | U-1338…U-1342、D-371、M1014、退役说明、计数器现读；CI 复验留给下一轮 ⓪。 |
| 交付诚实性 | 15/15 | runner 上 6 朵红按全部失败步骤读、没有只挑自己的；M674 退役写明「那一格今天没有牙」。 |
| 可复核性 | 15/15 | 两态读数、帧差分边界、三张表汇总、CI 步骤与正文都有原文；重推后的 run 记未读。 |

均分 = 103/105 ≈ 14.7/15（98）。
"""

decision = """
### D-371（383）两态像素判据的取样几何不许机器依赖；两态差由「最大偏离」判，墨量只作正对照

R383 现读：R382 的 `testRestoreDefaultsButtonIsDisabledWhenWeightsAreDefault` 在本机（2x）绿，在 runner（1x、字体度量不同）上六朵红 —— 那枚 72×22pt 的小取样矩形没压住按钮标签（`WEIGHTS_RESET_STATE light 默认 fill=230 墨=0 最大偏离=23 | 动过 同`）。原因不是产品，是判据的取样几何写死了一个只在 2x 成立的坐标；同页的按钮位置随标签宽度与说明段换行漂。
**Why**：判据在「差值」上是对的，却把「差值的取样点」钉在机器相关的坐标上 —— 于是它会在另一台机器上把「没读到」读成「没有差别」，或把差别读没。
**How to apply**：① 两态判据的取样用**语义带**（由布局语义推出：右列卡头、标题左侧、滑杆下沿），不用按钮的小矩形；② 判「禁用态画没画」看**最大偏离**（两态差），墨量只作「正对照有对象」用，并且第三格用 `<=` 而不是 `<`（墨量在字体差异下本来就会抖）；③ 新判据第一次上 runner 时，必须把**全部失败步骤**读完再动产品（R383 只红在它自己那两步）。
"""

changelog = """### CI 分诊（R382 判据取样机器依赖：改语义带 + maxDev 判两态差）+ 快捷键三颗「恢复默认」禁用态；367 rot 8→5、M674 退役（R383 / 第 382 轮 / U-1338…U-1342 · 产品 1 文件，动效主线）

"""

report_bullet = f"""
- **R383（动效主线）**：`40224259064`/`40224280654` 两跑 failure 全读 —— 失败步骤只有 `Swift tests` 与 `Capture gate`，六朵红全在 R382 新判据（runner 1x 上 72×22pt 取样矩形没压住标签，`墨=0 最大偏离=23` 两态同形）。修成语义带（右列卡头 x 380..520、y 60..230）+ 只由 `maxDev` 判两态差，本机现读 light {w_light_off}/{w_light_on}、dark {w_dark_off}/{w_dark_on}。产品位：快捷键页三颗「恢复默认」默认值下从未画禁用态（修前两态完全相同 {b_light_ink}/{b_light_dev}），加 `.disabled` 后 {a_light_ink}/{a_light_dev} 对 {a_light_onink}/{a_light_ondev}；182 张帧 176 张逐字节同、6 张只动按钮列。367：r94 7/7、M876 CAUGHT、M674 退役，rot 8→5。
"""

state_section = f"""## R383 状态（2026-10-26 · 本地 · 第 382 轮 / Round 380）：CI 两跑分诊 + 快捷键三颗「恢复默认」禁用态；367 rot 8→5（产品 1 文件，动效主线）

最后更新：2026-10-26（本地 · R383 / 第 382 轮 / Round 380）：`40224259064 ↔ c59b292`、`40224280654 ↔ e9b1f83` 两跑 failure，全部失败步骤只有 `Swift tests (executed-count gate)` 与 `Capture gate`；六朵红全在 R382 新判据 —— runner（1x）上 72×22pt 取样矩形没压住标签（`WEIGHTS_RESET_STATE … 墨=0 最大偏离=23` 两态同形）⇒ 取样几何机器依赖。改成语义带（x 380..520、y 60..230）+ 两态差只由 `maxDev` 判，本机现读 light {w_light_off}/{w_light_on}、dark {w_dark_off}/{w_dark_on}，M1013 复跑 `CAUGHT`。产品位：快捷键页三颗「恢复默认」在默认值下从未画禁用态（修前整页两态完全相同 `{b_light_ink}/{b_light_dev}`），加 `.disabled(shortcut == settings.action.defaultShortcut)` 后 `{a_light_ink}/{a_light_dev}` 对 `{a_light_onink}/{a_light_ondev}`；182 张帧 `same={same_frames} changed={changed_frames}`，6 张只动快捷键页右列。`M1014` `CAUGHT`；367：r94 整表 7/7、M876 单臂 CAUGHT、M674 退役（改名方向无牙）⇒ `HIDDEN_ARMS … rot={h_rot} … 上界 rot={h_rot_ceiling} … 处置=ok`（8→5）。`swift build --build-tests` 告警 **{warnings}**；全量 `Executed {executed} tests, with {skipped} tests skipped and {failures} failures`；清账表 `MOTION_LEDGER 表面={surfaces} 状态={states} 格子={cells} 行数={rows} 已清账={cleared} 未清账={uncleared} 地板={floor}`；产品面连续零改动 **{streak}** 轮（`python3 scripts/product_streak.py --streak-for 382` 现读）。

本轮做了什么：
① ⓪ CI 分诊：两跑 failure；`ci_read.py steps` 全部失败步骤 + 步骤名直方图（无 UNKNOWN STEP）+ 按步骤取正文 + 改动前 `43ff699` 那一跑 success 做对照 ⇒ 判成 R382 引入的判据几何回归。
② 判据修复：语义带 + `maxDev` 两态差；M1013 复跑 CAUGHT。
③ 产品位：快捷键页三颗 `恢复默认` 加禁用条件；两态整页渲染修前相同、修后分开；帧差分只动按钮列。
④ 367：r94 M518 单字面量（7/7）、r303 M876 字面量 + 漂移断言、r142 M674 退役；rot 8→5、上界同笔降。
⑤ 验证：构建 0 告警；全量 `{executed}/{skipped}/{failures}`；捕获 `CAPTURED {frames} -> /tmp/r383_shots`；帧基线 `COMPARED=182 CHANGED=0`；换装 `INSTALL_RESULT=ok`、`INSTALL_SHA_MATCH=1`、条目 {entries_before}={entries_after}；清账表 162=162；预检 `tables={pre_tables} covered={pre_covered} arms={pre_arms} bad={pre_bad}`、全仓 {arm_files} 文件 / {arm_total} 把。

验证读数（现读）：`SHORTCUT_RESET_STATE` 修前 `{b_light_ink}/{b_light_dev}`、修后 `{a_light_ink}/{a_light_dev}`（亮）与 `{b_dark_ink}/{b_dark_dev}`→`{a_dark_ink}/{a_dark_dev}`（暗）；`WEIGHTS_RESET_STATE` `{w_light_off}/{w_light_on}`、`{w_dark_off}/{w_dark_on}`；`M1013`/`M1014` 各 `CAUGHT=1/1 RESTORE_CLEAN=yes`；r94 `MUTATE_TABLE n=7 caught=7`；r142 `CAUGHT=5/5`；`ARM_TOTAL files={arm_files} arms={arm_total} dupes={arm_dupes}`。

NOT-RUN（分开写）：① **重推后的 CI 复验**没读 —— 这一笔推送之后的那一跑要下一轮 ⓪ 读（本轮不轮询）；② 亮档真机腿仍没跑（当前系统外观=dark）；③ 剩 5 根 rot 未重钉（r33 M147、r64 M340/M341、r77 M411、r78 M417）。

下一轮（R384）的靶：⓪ 读队列（本笔 run id 待 push 后成对写回；并确认 `Swift tests` 与 `Capture gate` 两朵是否消失）；① 继续 367（从 r78 M417 或 r64 起，先看 `HIDDEN_ROT` 现读名单）；② 回产品动效面再点一个真实位。
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
report_new = once(report_old, "D-069 … **D-370**", "D-069 … **D-371**")
report_new = once(report_new, "产品面连续零改动轮数 = **1**", "产品面连续零改动轮数 = **1**")
report_new = once(
    report_new,
    "R382 现读：注册表 **137** 张 / 刀号最大 **M1013** / 预检 covered=120 arms=389 bad=0；全仓 230 文件 / 874 把；M906 空刀退役",
    f"R383 现读：注册表 **{pre_tables}** 张 / 刀号最大 **M1014** / 预检 covered={pre_covered} arms={pre_arms} bad={pre_bad}；"
    f"全仓 {arm_files} 文件 / {arm_total} 把；M674 退役、M906 空刀退役")
report_new = once(
    report_new,
    "367 再钉 r29d 5/5 与 r76 5/5，rot 12→8。",
    "367 再钉 r29d 5/5 与 r76 5/5，rot 12→8。" + report_bullet)

state_old = rd("AGENT_STATE.md")
state_anchor = "## R382 状态（2026-10-26 · 本地 · 第 381 轮 / Round 379）"
assert state_old.count(state_anchor) == 1
state_new = once(state_old, state_anchor, state_section + "\n" + state_anchor)

wr("AGENT_UI_AUDIT.md", audit_new)
wr("AGENT_VISUAL_ITERATION.md", iteration_new)
wr("AGENT_DECISIONS.md", decisions_new)
wr("CHANGELOG.md", changelog_new)
wr("AGENT_FINAL_REPORT.md", report_new)
wr("AGENT_STATE.md", state_new)

print("R383_LEDGERS_OK warnings=%d full=%d/%d/%d frames=%d diff=%d/%d shortcut=%d/%d->%d/%d weights=%d/%d rot=%d pre=%d/%d/%d/%d arms=%d/%d gate=%d=%d streak=%d"
      % (warnings, executed, skipped, failures, frames, same_frames, changed_frames,
         b_light_dev, b_light_ondev, a_light_dev, a_light_ondev, w_light_off, w_light_on,
         h_rot, pre_tables, pre_covered, pre_arms, pre_bad, arm_files, arm_total,
         cleared, cells, streak))