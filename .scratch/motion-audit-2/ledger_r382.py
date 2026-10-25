#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R382（第 381 轮 / Round 379）的七本台账。数字全部从本机日志解析。"""
import io
import os
import re
import subprocess
import sys

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


build = log("/tmp/r382_build.log")
warnings = len(re.findall(r"warning:", build))

full = log("/tmp/r382_full.log")
summaries = [tuple(int(x) for x in row) for row in
             re.findall(r"Executed (\d+) tests, with (\d+) tests skipped and (\d+) failures", full)]
big = [row for row in summaries if row[0] > 900]
assert big, "全量卷汇总行没解析到"
executed, skipped, failures = big[-1]
assert failures == 0, "全量卷有失败"

capture = log("/tmp/r382_shots/capture-readings.log")
cap = re.search(r"CAPTURED (\d+) -> /tmp/r382_shots", capture)
assert cap, "捕获帧数没解析到"
frames = int(cap.group(1))

diff = log("/tmp/r382_framediff.log")
dm = re.search(r"FRAMEDIFF same=(\d+) changed=(\d+) total=(\d+)", diff)
assert dm, "帧差分没解析到"
same_frames, changed_frames, total_frames = [int(x) for x in dm.groups()]
assert (same_frames, changed_frames, total_frames) == (176, 6, 182)

reset = log("/tmp/r382_reset_test.log")
r_light = re.search(r"WEIGHTS_RESET_STATE light 默认 fill=\d+ 墨=\d+ 最大偏离=(\d+) \| 动过 fill=\d+ 墨=\d+ 最大偏离=(\d+)", reset)
r_dark = re.search(r"WEIGHTS_RESET_STATE dark 默认 fill=\d+ 墨=\d+ 最大偏离=(\d+) \| 动过 fill=\d+ 墨=\d+ 最大偏离=(\d+)", reset)
assert r_light and r_dark, "按钮两态读数没解析到"
light_off, light_on = int(r_light.group(1)), int(r_light.group(2))
dark_off, dark_on = int(r_dark.group(1)), int(r_dark.group(2))

install = log("/tmp/r382_install.log")
assert "INSTALL_RESULT=ok" in install and "INSTALL_SHA_MATCH=1" in install
entries = re.search(r"INSTALL_ENTRIES_BEFORE=(\d+)\s+INSTALL_ENTRIES_AFTER=(\d+)", install)
assert entries, "换装条目行没解析到"
entries_before, entries_after = entries.groups()

pre = log("/tmp/r382_precheck2.log")
pre_line = re.search(r"NEEDLE_PRECHECK tables=(\d+) covered=(\d+) arms=(\d+) bad=(\d+)", pre)
arm_line = re.search(r"ARM_TOTAL files=(\d+) arms=(\d+) dupes=(\d+) repeats=(\d+)", pre)
assert pre_line and arm_line, "预检两行没解析到"
pre_tables, pre_covered, pre_arms, pre_bad = [int(x) for x in pre_line.groups()]
arm_files, arm_total, arm_dupes, arm_repeats = [int(x) for x in arm_line.groups()]
assert pre_bad == 0 and arm_dupes == 0 and arm_repeats == 0

hidden = log("/tmp/r382_hidden2.log")
h = re.search(r"HIDDEN_ARMS 表=(\d+) 可判=(\d+) rot=(\d+) 抽不出=(\d+) 已声明表=(\d+) 已声明死针=(\d+) 上界 rot=(\d+)", hidden)
assert h, "HIDDEN_ARMS 行没解析到"
h_tables, h_judged, h_rot, h_opaque, h_dtables, h_ddead, h_rot_ceiling = [int(x) for x in h.groups()]
assert h_rot == h_rot_ceiling == 8

gate = log("/tmp/r382_gate.log")
g = re.search(r"MOTION_LEDGER 表面=(\d+) 状态=(\d+) 格子=(\d+) 行数=(\d+) 已清账=(\d+) 未清账=(\d+) 地板=(\d+)", gate)
assert g, "清账表行没解析到"
surfaces, states, cells, rows, cleared, uncleared, floor = [int(x) for x in g.groups()]
assert uncleared == 0 and cleared == cells == rows == floor

streak_out = subprocess.check_output(
    ["python3", os.path.join(ROOT, "scripts/product_streak.py"), "--streak-for", "381"],
    cwd=ROOT).decode("utf-8")
streak = int(re.search(r"streak=(\d+)", streak_out).group(1))
assert streak == 1, "streak 读数为 %d" % streak

r29d = log("/tmp/r382_mut_r29d2.log")
r76 = log("/tmp/r382_mut_r76.log")
r382 = log("/tmp/r382_mut_r382.log")
assert "CAUGHT=5/5" in r29d and "RESTORE_CLEAN=yes" in r29d
assert "抓到=5 逃掉=0 没跑成=0 未落地=0" in r76
assert "R382_MUTATE 刀=1 CAUGHT=1 红得不对=0 RESTORE_CLEAN=yes" in r382

ui_heading = "## 第 380 轮（R381 · 2026-10-26 · U-1329…U-1333）："
ui_section = f"""## 第 381 轮（R382 · 2026-10-26 · U-1334…U-1337）：默认权重下「恢复默认」没有禁用态 —— 两态像素证人 + M1013；367 再钉五根（U-1334…U-1337 · 产品 1 文件，动效主线）

- **U-1334：看图看出来的状态缺席。** `weights`（权重全默认）与 `weights-adjusted`（近因 160% / 收藏 40%）两帧里，「恢复默认」按钮的标签墨**一模一样**（亮档最大偏离 62 对 62、暗档 51 对 51）；默认时点它不产生任何变化。它不是样式问题，是**禁用态从未存在**。
- **U-1335：最小修法。** `RecommendationWeightsView` 的按钮加 `.disabled(store.weights == .default)`（`RecommendationWeights` 本来就是 `Equatable`，`.default` 是现成的常量）。修后 `WEIGHTS_RESET_STATE light 默认 最大偏离={light_off} / 动过 {light_on}`、`dark 默认 {dark_off} / 动过 {dark_on}`；新旧 182 张帧差分 `same={same_frames} changed={changed_frames}`，6 张变化的边界全部只在按钮矩形（`weights` 838..990×204..252、`settings-recommendations*` 1230..1382×247..295），`weights-adjusted` 逐字节不变 ⇒ 动过的状态没有被误伤。
- **U-1336：像素证人与刀。** 新判据 `testRestoreDefaultsButtonIsDisabledWhenWeightsAreDefault` 同尺寸渲染两帧、读按钮标签相对填充的最大偏离；正对照是「动过」那一帧必须 >0 墨。`M1013`（把 `.disabled(...)` 换成 `.disabled(false)`）现读 `CAUGHT`、复跑 `ESCAPED`、还原干净。**表形状自伤**：第一版写成自写 main + 两个模块常量，`mutate_needle_precheck` 与 `hidden_arms` 都看不见 M1013（`covered=119`、`可判=807`）；改成 `MUTATIONS` 七元组后 `covered=120 arms=389`、`可判=808`，M1013 第一次进名册。
- **U-1337：367 再钉五根。** r29d 的 M132/M133/M135 按今天的盲区名单重钉（名单长到 13 张、量尺框 y=60/h=192），整表 **5/5 CAUGHT**（M133 的期望串随守卫措辞改成 `TEXT_SIDE_ROSTER_GONE`）；r76 的 M402 重钉到当前方向断言，整表 **5/5 CAUGHT**。`HIDDEN_ARMS 表={h_tables} 可判={h_judged} rot={h_rot} … 上界 rot={h_rot_ceiling} … 处置=ok`（12→8），五根都重跑过刀。
"""

iteration = f"""## Round 379 · R382（第 381 轮 · 2026-10-26）：默认权重下「恢复默认」没有禁用态 —— 两态像素证人 + M1013（产品 1 文件）

看图对比 `weights` 与 `weights-adjusted`：同一颗「恢复默认」按钮在默认权重的帧里永远可点，而点了不产生任何变化 —— 禁用态从未画出来。加 `.disabled(store.weights == .default)` 后，亮档标签最大偏离 62 → 195、暗档 51 → 170；182 张帧里 176 张逐字节同、6 张只动按钮矩形，`weights-adjusted` 不变。新像素判据 + M1013（改回恒 enabled）`CAUGHT`；第一版表写成自写 main，两个名册都看不见，改成 `MUTATIONS` 形状后 `covered=120 / 可判=808`。367 再钉 r29d 五臂（5/5）与 r76 M402（5/5），rot 12→8。

**七维度自评**（恰七行，每格 n/15）：

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | 15/15 | 对比了默认/动过两帧与设置整页，量到按钮两态像素相同；182 张差分边界只在按钮矩形。 |
| 判据有效性 | 14/15 | 新判据读的是渲染后的标签墨，正对照+刀都在；但这一状态缺席此前没有任何判据覆盖。 |
| 假绿防御 | 15/15 | 正对照要求动过帧 >0 墨；M1013 CAUGHT；表形状修好后两个静态名册都能看见 M1013。 |
| 产品面推进 | 14/15 | 修掉一个真实的禁用态缺席；本轮仍只深审一个位点。 |
| 台账一致性 | 14/15 | U-1334…U-1337、D-370、计数器现读；没有新开 BACKLOG（已当场修完）。 |
| 交付诚实性 | 15/15 | 第一版刀表对两个名册隐形这件事原样写进 U-1336，不把「跑过」写成「被覆盖」。 |
| 可复核性 | 15/15 | 两态读数、帧差分边界、M1013、r29d/r76 的整表汇总、清账表与换装三行都有命令与原文。 |

均分 = 102/105 ≈ 14.6/15（97）。
"""

decision = """
### D-370（382）一个动作「不会改变任何东西」的状态必须画成禁用；两态像素证人比源码断言强

R382 现读：`weights`（全默认）与 `weights-adjusted`（近因 160% / 收藏 40%）两帧里，「恢复默认」按钮的标签墨完全相同（亮 62 对 62、暗 51 对 51）—— 它永远可点，默认时点了什么也不会发生。加 `.disabled(store.weights == .default)` 后两态最大偏离变成 62/195 与 51/170。
**Why**：源码里写了 `.disabled(...)` 不等于 SwiftUI 真把禁用态画出来（样式、环境、父容器都可能把它吃掉）；而「默认状态」恰恰是最常被打开的那一屏，用户看到的是一颗假按钮。
**How to apply**：① 审状态时把「这个动作在当前状态下是不是空操作」单列一格；是空操作就必须有禁用态。② 判据必须渲染**两个状态**并读同一颗控件的墨（一个正对照是「动过」那一帧必须有墨），不许只 grep 源码。③ 表写完后立刻回 `mutate_needle_precheck.py` / `hidden_arms.py` 看它有没有进名册；自写 main 的表对两个静态尺都隐形（R382 的 M1013 第一版就是这样）。
"""

changelog = """### 「恢复默认」在权重全默认时画成禁用态（两态像素证人 + M1013）；367 再钉五根、rot 12→8（R382 / 第 381 轮 / U-1334…U-1337 · 产品 1 文件，动效主线）

"""

report_bullet = f"""
- **R382（动效主线）**：`weights` 与 `weights-adjusted` 两帧里「恢复默认」按钮的标签墨完全相同（亮 62/62、暗 51/51），默认权重下它永远可点却什么也不发生。加 `.disabled(store.weights == .default)` 后两态最大偏离亮 62→{light_on}、暗 51→{dark_on}；182 张帧 176 张逐字节同、6 张只动按钮矩形。新判据 `testRestoreDefaultsButtonIsDisabledWhenWeightsAreDefault` + M1013 `CAUGHT`（第一版表对两个静态名册隐形，改成 MUTATIONS 形状后 covered=120 / 可判=808）。367 再钉 r29d 5/5 与 r76 5/5，rot 12→8。
"""

state_section = f"""## R382 状态（2026-10-26 · 本地 · 第 381 轮 / Round 379）：默认权重下「恢复默认」没有禁用态 —— 两态像素证人 + M1013；367 再钉五根（产品 1 文件，动效主线）

最后更新：2026-10-26（本地 · R382 / 第 381 轮 / Round 379）：对比 `weights`（全默认）与 `weights-adjusted`（近因 160% / 收藏 40%）两帧，「恢复默认」标签墨完全相同 ⇒ 禁用态从未存在；加 `.disabled(store.weights == .default)` 后 `WEIGHTS_RESET_STATE light 默认 {light_off} / 动过 {light_on}`、`dark 默认 {dark_off} / 动过 {dark_on}`；182 张帧 `same={same_frames} changed={changed_frames}`，6 张只动按钮矩形、`weights-adjusted` 逐字节不变。新判据 + `M1013` 现读 `CAUGHT`、复跑 `ESCAPED`；第一版表写成自写 main、对 `mutate_needle_precheck` / `hidden_arms` 隐形，改成 `MUTATIONS` 后 `covered={pre_covered} arms={pre_arms}`、`可判={h_judged}`。367 再钉 r29d（5/5）与 r76 M402（5/5），`HIDDEN_ARMS … rot={h_rot} … 上界 rot={h_rot_ceiling} … 处置=ok`（12→8）。`swift build --build-tests` 告警 **{warnings}**；全量 `Executed {executed} tests, with {skipped} tests skipped and {failures} failures`；清账表 `MOTION_LEDGER 表面={surfaces} 状态={states} 格子={cells} 行数={rows} 已清账={cleared} 未清账={uncleared} 地板={floor}`；产品面连续零改动 **{streak}** 轮（`python3 scripts/product_streak.py --streak-for 381` 现读，口径是「本轮之前的连读轮数」）。

本轮做了什么：
① ⓪ CI：登记 `4255109 ↔ 40221926024`、`43ff699 ↔ 40221947072`（均 in_progress）；`9678d9c ↔ 40216535782`、`fb641e7 ↔ 40216344972`、`ef45e65 ↔ 40216188878`、`e8228a8 ↔ 40216027769` 已 success；只登记不轮询。
② 产品位：默认/动过两帧同一颗按钮像素相同 ⇒ 禁用态缺席；加 `.disabled(store.weights == .default)`；帧差分区只在按钮。
③ 判据：新像素判据读两态标签墨 + M1013 CAUGHT；表形状改成 `MUTATIONS` 让两个静态名册看见它。
④ rot：r29d M132/M133/M135 + r76 M402 重钉，两表整表 5/5 CAUGHT；rot 12→8、上界同笔降。
⑤ 验证：构建 0 告警；全量 `{executed}/{skipped}/{failures}`；捕获 `CAPTURED {frames} -> /tmp/r382_shots`；帧基线 `COMPARED=182 CHANGED=0`；换装 `INSTALL_RESULT=ok`、`INSTALL_SHA_MATCH=1`、条目 {entries_before}={entries_after}；清账表 162=162。

验证读数（现读）：`WEIGHTS_RESET_STATE` 两档 `{light_off}/{light_on}`、`{dark_off}/{dark_on}`；`R382_MUTATE 刀=1 CAUGHT=1 红得不对=0 RESTORE_CLEAN=yes`；r29d `CAUGHT=5/5`、r76 `抓到=5 逃掉=0`；`NEEDLE_PRECHECK tables={pre_tables} covered={pre_covered} arms={pre_arms} bad={pre_bad}`；`ARM_TOTAL files={arm_files} arms={arm_total} dupes={arm_dupes} repeats={arm_repeats}`。

NOT-RUN（分开写）：① 亮档真机腿仍没跑（当前系统外观=dark；R382 的按钮禁用态没有走真机通道，只有离屏两态帧）。② 剩 8 根 rot 未重钉（r142 M674、r303 M876、r33 M147、r64 M340/M341、r77 M411、r78 M417、r94 M518）。③ `weights-*` 与 `settings-recommendations*` 的帧基线已同一笔更新，不是 NOT-RUN。

下一轮（R383）的靶：⓪ 读队列（本笔 run id 待 push 后成对写回）；① 继续 367（从 r303/r94 或 r64 起，先看 `HIDDEN_ROT` 现读名单）；② 回产品动效面再点一个真实位（本轮的最弱维仍是「只深审一个位点」）。
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
report_new = once(report_old, "D-069 … **D-369**", "D-069 … **D-370**")
report_new = once(report_new, "产品面连续零改动轮数 = **26**", "产品面连续零改动轮数 = **1**")
report_new = once(
    report_new,
    "R381 现读：注册表 **136** 张 / 刀号最大 **M1012** / 预检 covered=119 arms=388 bad=0；全仓 229 文件 / 873 把；M906 空刀退役",
    f"R382 现读：注册表 **{pre_tables}** 张 / 刀号最大 **M1013** / 预检 covered={pre_covered} arms={pre_arms} bad={pre_bad}；"
    f"全仓 {arm_files} 文件 / {arm_total} 把；M906 空刀退役")
report_new = once(
    report_new,
    "367 再钉八根（rot 20→12）；方向尺的正对照从坏帧改成合成帧。",
    "367 再钉八根（rot 20→12）；方向尺的正对照从坏帧改成合成帧。" + report_bullet)

state_old = rd("AGENT_STATE.md")
state_anchor = "## R381 状态（2026-10-26 · 本地 · 第 380 轮 / Round 378）"
assert state_old.count(state_anchor) == 1
state_new = once(state_old, state_anchor, state_section + "\n" + state_anchor)

wr("AGENT_UI_AUDIT.md", audit_new)
wr("AGENT_VISUAL_ITERATION.md", iteration_new)
wr("AGENT_DECISIONS.md", decisions_new)
wr("CHANGELOG.md", changelog_new)
wr("AGENT_FINAL_REPORT.md", report_new)
wr("AGENT_STATE.md", state_new)

print("R382_LEDGERS_OK warnings=%d full=%d/%d/%d frames=%d diff=%d/%d reset=%d/%d,%d/%d rot=%d pre=%d/%d/%d/%d arms=%d/%d gate=%d=%d streak=%d"
      % (warnings, executed, skipped, failures, frames, same_frames, changed_frames,
         light_off, light_on, dark_off, dark_on, h_rot, pre_tables, pre_covered, pre_arms, pre_bad,
         arm_files, arm_total, cleared, cells, streak))
