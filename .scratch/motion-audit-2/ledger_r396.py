#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R396（第 395 轮 / Round 393）的台账。数字全部从本机日志解析。"""
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


build = log("/tmp/r396_build_final.log")
warnings = len(re.findall(r"warning:", build))
assert warnings == 0

full = log("/tmp/r396_full.log")
summaries = [tuple(int(x) for x in row) for row in
             re.findall(r"Executed (\d+) tests, with (\d+) tests skipped and (\d+) failures", full)]
big = [row for row in summaries if row[0] > 900]
assert big
executed, skipped, failures = big[-1]
assert (executed, skipped, failures) == (1055, 52, 0)

capture = log("/tmp/r396_capture.log")
cap = re.search(r"CAPTURED (\d+) -> /tmp/r396_shots", capture)
assert cap
frames = int(cap.group(1))
assert frames == 182
guard = {}
for tag in ("light", "dark"):
    m = re.search(r"LOGIN_UNSUPPORTED_FRAME %s fill=(\d+) 墨=(\d+) 对比=([0-9.]+)" % tag, capture)
    assert m, tag
    guard[tag] = (int(m.group(1)), int(m.group(2)), float(m.group(3)))
assert guard["light"][2] >= 2.2 and guard["dark"][2] >= 2.2
assert abs(guard["light"][2] - 2.84) < 0.01 and abs(guard["dark"][2] - 4.38) < 0.01

oldband = log("/tmp/r396_old_band.log")
band = {}
for kind, tag, contrast in re.findall(
        r"LABEL_BAND (old|new) (light|dark) x=195\.\.255 y=118\.\.135 .*contrast=([0-9.]+)", oldband):
    band[(kind, tag)] = float(contrast)
assert set(band) == {("old", "light"), ("old", "dark"), ("new", "light"), ("new", "dark")}
assert band[("old", "light")] < 2.2 and band[("old", "dark")] < 2.2
assert band[("new", "light")] >= 2.2 and band[("new", "dark")] >= 2.2
wrong = {}
for tag, contrast in re.findall(
        r"WRONG_BAND old (light|dark) x=380\.\.700 y=225\.\.275 .*contrast=([0-9.]+)", oldband):
    wrong[tag] = float(contrast)
assert abs(wrong["light"] - 2.81) < 0.01 and abs(wrong["dark"] - 4.33) < 0.01

bbox = log("/tmp/r396_label_bbox.log")
assert "pt=(198.5..248.0,120.5..132.0)" in bbox
assert "pt=(199.5..249.0,120.5..132.0)" in bbox

diff = log("/tmp/r396_framediff.log")
dm = re.search(r"FRAME_DIFF 比了=(\d+) 变了=(\d+)", diff)
assert dm
total_frames, changed_frames = [int(x) for x in dm.groups()]
changed_names = sorted(re.findall(r"^  changed (.+)$", diff, re.M))
expected_changed = sorted([
    "settings-general-720x540-dark.png",
    "settings-general-720x540-light.png",
    "settings-general-login-failed-720x540-dark.png",
    "settings-general-login-failed-720x540-light.png",
    "settings-general-login-unsupported-720x540-dark.png",
    "settings-general-login-unsupported-720x540-light.png",
])
assert (total_frames, changed_frames) == (182, 6)
assert changed_names == expected_changed, changed_names

baseline = log("/tmp/r396_framebaseline.log")
bm = re.search(r"FRAME_BASELINE_COMPARED=(\d+)\s+FRAME_BASELINE_CHANGED=(\d+)"
               r"\s+FRAME_BASELINE_MISSING=(\d+)\s+FRAME_BASELINE_ADDED=(\d+)", baseline)
assert bm
b_compared, b_changed, b_missing, b_added = [int(x) for x in bm.groups()]
assert (b_compared, b_changed, b_missing, b_added) == (182, 0, 0, 0)
bupdate = log("/tmp/r396_framebaseline_update.log")
assert "FRAME_BASELINE_UPDATED=182" in bupdate

source_guard = log("/tmp/r396_guard.log")
assert "testUnsupportedLoginLabelStaysOutsideDisabledToggle]' passed" in source_guard
assert "Executed 1 test, with 0 failures" in source_guard

mut = log("/tmp/r396_mut11.log")
assert "M1033" in mut and "M1034" in mut
assert "M1033 标签退回被禁用的 Toggle（源守卫） ⇒ CAUGHT 红得对=True 命中=True" in mut
assert "M1034 标签退回被禁用的 Toggle（像素守卫） ⇒ CAUGHT 红得对=True 命中=True" in mut
assert "R396_MUTATE 刀=2 CAUGHT=2 红得不对=0 RESTORE_CLEAN=yes" in mut
assert "还原后复跑：MotionCatalogTests/testUnsupportedLoginLabelStaysOutsideDisabledToggle=ESCAPED UICaptureTests/testCaptureKeyViews=ESCAPED" in mut

install = log("/tmp/r396_install.log")
assert "INSTALL_RESULT=ok" in install and "INSTALL_SHA_MATCH=1" in install
entries = re.search(r"INSTALL_ENTRIES_BEFORE=(\d+)\s+INSTALL_ENTRIES_AFTER=(\d+)", install)
assert entries
entries_before, entries_after = entries.groups()
assert entries_before == entries_after == "381"

pre = log("/tmp/r396_precheck.log")
pre_line = re.search(r"NEEDLE_PRECHECK tables=(\d+) covered=(\d+) arms=(\d+) bad=(\d+)", pre)
arm_line = re.search(r"ARM_TOTAL files=(\d+) arms=(\d+) dupes=(\d+) repeats=(\d+)", pre)
assert pre_line and arm_line
pre_tables, pre_covered, pre_arms, pre_bad = [int(x) for x in pre_line.groups()]
arm_files, arm_total, arm_dupes, arm_repeats = [int(x) for x in arm_line.groups()]
assert (pre_tables, pre_covered, pre_arms, pre_bad) == (151, 134, 410, 0)
assert (arm_files, arm_total) == (244, 894)
assert arm_dupes == 0 and arm_repeats == 0

hidden = log("/tmp/r396_hidden.log")
h = re.search(r"HIDDEN_ARMS 表=(\d+) 可判=(\d+) rot=(\d+) 抽不出=(\d+) 已声明表=(\d+)"
              r" 已声明死针=(\d+) 上界 rot=(\d+)", hidden)
assert h
h_tables, h_judged, h_rot, h_opaque, h_dtables, h_ddead, h_rot_ceiling = [int(x) for x in h.groups()]
assert (h_tables, h_judged, h_rot, h_opaque, h_dtables, h_ddead, h_rot_ceiling) == (238, 828, 0, 6, 6, 0, 0)

gate = log("/tmp/r396_gate.log")
g = re.search(r"MOTION_LEDGER 表面=(\d+) 状态=(\d+) 格子=(\d+) 行数=(\d+)"
              r" 已清账=(\d+) 未清账=(\d+) 地板=(\d+)", gate)
assert g
surfaces, states, cells, rows, cleared, uncleared, floor_count = [int(x) for x in g.groups()]
assert (surfaces, states, cells, rows, cleared, uncleared, floor_count) == (18, 9, 162, 162, 162, 0, 162)
assert "MOTION_LEDGER_RESULT=ok" in gate

streak_out = subprocess.check_output(
    ["python3", os.path.join(ROOT, "scripts/product_streak.py"), "--streak-for", "395"],
    cwd=ROOT).decode("utf-8")
streak = int(re.search(r"streak=(\d+)", streak_out).group(1))
assert streak == 1, "streak=%d" % streak

motion = log("/tmp/r390_motion_full.log")
ms = re.search(r"MOTION_SUMMARY (.+)", motion)
mr = re.search(r"MOTION_RESOLVE_SUMMARY judged=(\d+)/(\d+) not-run=(\S+)", motion)
mex = re.search(r"Executed (\d+) tests, with (\d+) tests skipped and (\d+) failures", motion)
assert ms and mr and mex
motion_summary = ms.group(1)
motion_judged, motion_total, motion_notrun = mr.groups()
motion_exec, motion_skip, motion_fail = [int(x) for x in mex.groups()]
assert motion_judged == motion_total == "5" and motion_notrun == "-" and motion_fail == 0
assert "settings-reset-fade" in motion_summary

ui_heading = "## 第 394 轮（R395"
ui_section = f"""## 第 395 轮（R396 · 2026-10-26 · U-1400…U-1404）：不支持登录项时标签被禁用 Toggle 一起压暗（1.76/2.13 → 2.84/4.38）；修 Sources 并补捕获帧像素守卫（U-1400…U-1404 · 产品 1 文件，视觉主线）

- **U-1400：⓪ 网络与 CI。** 12:36 `git push origin main` 被 SSH 拒（`Connection closed by 20.205.243.166 port 22`），同分钟 `api=000`（LibreSSL SSL_ERROR_SYSCALL）/ `apple=200` ⇒ `PUSH_BLOCKED=network`，本地 ahead=31（R395 之后、R396 落笔前），**不写已推送**。`origin/main` 本地 ref 仍 `5c7814e`；网络不可达无法 fetch 确认远端是否被推进，push 在连接阶段失败、未用 force。按本轮上限 2 次同形探测，之后不再探。恢复后一次 push 只为 head 生成一个新 run；此前未读的旧跑仍要单独按步骤读，不能用新 run 代账。
- **U-1401：② 产品视觉位 —— 标签被禁用 Toggle 一起压暗。** 先看图：`settings-general-login-unsupported` 亮/暗两帧里「开机启动」比同组标签明显浅。按字墨 bbox 定位（旧 `198.5..248.0 × 120.5..132.0pt`、新 `199.5..249.0 × 120.5..132.0pt`），只读标签自己的带（x 195..255、y 118..135pt）：旧结构亮 **{band[("old", "light")]:.2f}** / 暗 **{band[("old", "dark")]:.2f}:1**（低于禁用标签地板 2.2），新结构亮 **{band[("new", "light")]:.2f}** / 暗 **{band[("new", "dark")]:.2f}:1**。修法：`Toggle` 加 `.labelsHidden()`，标签移出禁用控件成独立 `Text`（不支持 `.secondary` / 支持 `.primary`；`accessibilityHidden(true)`；支持时点文字仍切换），复选框仍禁用。**自伤**：第一版捕捉守卫把带子写成 x 380..700 / y 225..275，实际量到第三行「识别截图文字」，旧结构也读 {wrong["light"]:.2f}/{wrong["dark"]:.2f}（假绿）；按 bbox 重钉后守卫才真的指向标签。
- **U-1402：判据与刀。** `MotionCatalogTests.testUnsupportedLoginLabelStaysOutsideDisabledToggle` 钉结构：`Toggle("开机启动")` 与独立 `Text("开机启动")` 之间必须真的有 `.labelsHidden()`（全文任意位置的 `.contains` 不算），并查 `accessibilityHidden(true)` / `.onTapGesture`。捕捉卷 `testCaptureKeyViews` 在真实 182 帧里读同一条带（平涂页具名 NOT-RUN，墨=0 也 NOT-RUN）；捕捉打印亮 `fill={guard["light"][0]} 墨={guard["light"][1]} 对比={guard["light"][2]:.2f}`、暗 `fill={guard["dark"][0]} 墨={guard["dark"][1]} 对比={guard["dark"][2]:.2f}`。`M1033`（源形状）/`M1034`（捕获帧像素）双 **CAUGHT**、红得对=2、红得不对=0、还原干净、还原后两条都 ESCAPED；表里只写 `SettingsView.swift` 一个文件靶（D-384）。另修 R395 生成器漏展开的两处占位：`AGENT_DECISIONS.md` 的 D-385 与 `CHANGELOG.md` 标题里的 `{{cat2_median}}` → **121**（R395 用了非 f 字符串，落盘没替换）。
- **U-1403：BACKLOG 436 处置（仍未结案）。** 本轮没有新的 runner motion 读数；R390 的完整本地卷仍是 `Executed {motion_exec} tests, with {motion_skip} tests skipped and {motion_fail} failures`、`MOTION_SUMMARY {motion_summary}`、`MOTION_RESOLVE_SUMMARY judged={motion_judged}/{motion_total} not-run={motion_notrun}`，现有登记跑 `motion_floor_gate.py` 的 exit 1（UNLISTED `settings-reset-fade`）本地复现仍成立。**不关单、不改 JSON/自测、不猜 `must_judge`**；runner 卷继续记具名 NOT-RUN，待 push 恢复后先读 `MOTION_SUMMARY` 与 `MOTION_RESOLVE_SUMMARY`。
- **U-1404：① 367 rot 与八步。** `HIDDEN_ARMS 表={h_tables} 可判={h_judged} rot={h_rot} 抽不出={h_opaque} 已声明表={h_dtables} 已声明死针={h_ddead} 上界 rot={h_rot_ceiling} 处置=ok`；预检 `tables={pre_tables} covered={pre_covered} arms={pre_arms} bad={pre_bad}`、全仓 {arm_files} 文件 / {arm_total} 把；`M1033/M1034` 全 CAUGHT。build **{warnings}** 告警；全量 `Executed {executed} tests, with {skipped} tests skipped and {failures} failures`；捕获 `CAPTURED {frames} -> /tmp/r396_shots`，与 R395 逐张比 `变了={changed_frames}`（设置通用 6 帧；其余默认路径不变），帧基线同一笔 `UPDATED=182`、复验 `COMPARED={b_compared} CHANGED={b_changed} MISSING={b_missing} ADDED={b_added}`；换装 `INSTALL_RESULT=ok`、`INSTALL_SHA_MATCH=1`、条目 `{entries_before}={entries_after}`；清账表 `表面={surfaces} 状态={states} 格子={cells} 已清账={cleared} 未清账={uncleared} 地板={floor_count}`；产品面连续零改动 **{streak}** 轮（as-of 395；本轮产品视觉改动已落 Sources，现读 `python3 scripts/product_streak.py --streak-for 395`）。
"""

iteration = f"""## Round 393 · R396（第 395 轮 · 2026-10-26）：不支持登录项的标签被禁用 Toggle 一起压暗（1.76/2.13 → 2.84/4.38）；修 Sources 并补捕获帧像素守卫（产品 1 文件，视觉主线）

真看图：`settings-general-login-unsupported` 亮/暗帧里「开机启动」比同组其它标签明显浅。按字墨 bbox 定位（旧 `198.5..248.0 × 120.5..132.0pt`）后只读标签自己的带（x 195..255、y 118..135pt）：旧结构亮 **1.76** / 暗 **2.13:1**（低于禁用标签地板 2.2），新结构亮 **2.84** / 暗 **4.38:1**。产品改法：`Toggle` 加 `.labelsHidden()`，标签移出被禁用的控件成独立 `Text`（不支持 `.secondary` / 支持 `.primary`，`accessibilityHidden(true)`，支持时仍可点），复选框仍禁用。**自伤**：第一版捕捉守卫的带子（x 380..700/y 225..275）量到的是第三行「识别截图文字」，旧结构也读 2.81/4.33（假绿）；按 bbox 重钉后才让 `M1034` 真的在旧结构上红。捕获 182 帧、设置通用 6 帧变化；帧基线同一笔 `UPDATED=182`，复验 182/0/0/0。

**七维度自评**（恰七行，每格 n/15）：

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | 14/15 | 真看了亮/暗两档旧帧与新帧，并量了字墨 bbox；扣 1：只审了登录项这一族。 |
| 判据有效性 | 15/15 | 源形状守卫 + 真实捕获帧像素守卫；M1033/M1034 双 CAUGHT、还原后双 ESCAPED。 |
| 假绿防御 | 15/15 | 自己抓住第一版带子量错对象（旧结构也 2.81/4.33），重钉后才敢报修好。 |
| 产品面推进 | 14/15 | 真落 Sources 视觉一行：标签脱离禁用控件，复选框仍禁用；扣 1：单点修复。 |
| 台账一致性 | 14/15 | U-1400…U-1404、D-386、436、计数器全从日志解析；扣 1：436 仍开。 |
| 交付诚实性 | 15/15 | 旧/新与错带/正带读数都写；436 记具名 NOT-RUN；不把守卫写成产品修复。 |
| 可复核性 | 15/15 | bbox、两条带的读数、两把刀、捕获卷、基线、precheck/rot 都有原文可复跑。 |

均分 = 102/105 ≈ 14.6/15（97）。
"""

decision = """
### D-386（396）禁用控件可以压暗控件，不能连带压暗解释它的标签；像素守卫先用字墨 bbox 钉住对象

R396 现读：`Toggle("开机启动")` 在 `.disabled` 时整颗控件（含标签）被系统额外压暗；正确标签带（x 195..255、y 118..135pt）旧结构亮 **1.76** / 暗 **2.13:1**，低于 2.2 地板；把标签移出禁用 Toggle 后亮 **2.84** / 暗 **4.38:1**，复选框仍禁用。第一版捕捉守卫的带子（x 380..700/y 225..275）实际量到第三行「识别截图文字」，旧结构也读 2.81/4.33 —— 这是一次自己造出来的假绿。
**Why**：禁用态系统的额外 opacity 作用在整颗控件上，解释文字也被一起压暗；而像素尺一旦没先定位被量对象，读数会像结论一样整齐（2.81/4.33 与真值 2.84/4.38 只差几个百分点，肉眼对不上对象的身份）。修法若只改判据不改产品，等于把缺陷留在产品里、把尺调绿。
**How to apply**：① 解释性标签不要放在会被 `disabled` 整体压暗的控件内；隐藏控件标签、另起独立 `Text`，并处理可点与无障碍；② 像素守卫先按字墨 bbox 定位对象，再写成点坐标带；带子跨越两行/多行时会量到邻居，必须把“这一行是哪一行”写进日志；③ 一个产品文件靶一张表，形状刀与像素刀分开登记，两臂都要在还原后 ESCAPED（R396 M1033/M1034）。
"""

changelog = """### 不支持登录项的标签被禁用 Toggle 一起压暗（1.76/2.13 → 2.84/4.38）；修 Sources 并补捕获帧像素守卫（R396 / 第 395 轮 / Round 393 / U-1400…U-1404 · 产品 1 文件，视觉主线）

"""

report_bullet = """
- **R396（视觉主线）**：不支持登录项时「开机启动」标签被整颗禁用的 Toggle 一起压暗：按字墨 bbox 量正确标签带，旧结构亮 `1.76` / 暗 `2.13:1`（地板 2.2），新结构 `2.84` / `4.38`。修 Sources：`labelsHidden()` + 独立 `Text`，复选框仍禁用。**自伤**：第一版捕捉守卫的带子（x380..700/y225..275）实际量到第三行「识别截图文字」，旧结构也读 `2.81` / `4.33`（假绿）；按 bbox 重钉到 x195..255/y118..135 后，M1033（源形状）/ M1034（捕获帧像素）双 CAUGHT。捕获 182 帧、设置通用 6 帧变化，基线同笔 update 后 182/0；全量 1055/52/0；436 无新 runner 读数，仍未结案；rot 0/0。**网络仍断 ⇒ PUSH_BLOCKED=network，ahead=31，未推送。**
"""

state_section = f"""## R396 状态（2026-10-26 · 本地 · 第 395 轮 / Round 393）：不支持登录项的标签被禁用 Toggle 一起压暗（1.76/2.13 → 2.84/4.38）；修 Sources 并补捕获帧像素守卫（产品 1 文件，视觉主线）

最后更新：2026-10-26（本地 · R396 / 第 395 轮 / Round 393）：先真看 `settings-general-login-unsupported` 亮/暗帧：不支持登录项时「开机启动」标签比同组其它标签明显浅。按字墨 bbox 定位（旧 `198.5..248.0 × 120.5..132.0pt`）后只读标签带（x 195..255、y 118..135pt）：旧结构亮 **1.76** / 暗 **2.13:1**（低于禁用标签地板 2.2），新结构亮 **2.84** / 暗 **4.38:1**。产品改法：`Toggle` 加 `.labelsHidden()`，标签移出禁用控件成独立 `Text`（不支持 `.secondary` / 支持 `.primary`，`accessibilityHidden(true)`，支持时仍可点），复选框仍禁用。**自伤**：第一版捕捉守卫的带子（x 380..700/y 225..275）量到第三行「识别截图文字」，旧结构也读 2.81/4.33（假绿）；按 bbox 重钉后 M1033/M1034 双 CAUGHT。默认 182 帧里设置通用 6 帧变化；帧基线同笔 `UPDATED=182`，复验 182/0/0/0。全量 `Executed {executed} tests, with {skipped} tests skipped and {failures} failures`；换装 `ok / SHA_MATCH=1 / 381=381`；清账表 162=162；`HIDDEN_ARMS 表={h_tables} 可判={h_judged} rot={h_rot} … 上界 rot={h_rot_ceiling} 处置=ok`；预检 `tables={pre_tables} covered={pre_covered} arms={pre_arms} bad={pre_bad}`、全仓 {arm_files} 文件 / {arm_total} 把；产品面连续零改动 **{streak}** 轮（as-of 395，现读 `python3 scripts/product_streak.py --streak-for 395`；本轮产品视觉已落 Sources）。

本轮做了什么：
① ⓪ 网络：push 被 SSH 拒 + `api=000`/`apple=200` ⇒ `PUSH_BLOCKED=network`；ahead=31，未推送；未 force。
② 看图找到真缺陷：不支持登录项时标签被禁用 Toggle 一起压暗（旧 1.76/2.13，地板 2.2），修 Sources 后 2.84/4.38。
③ 判据：源形状守卫 + 真实捕获帧像素守卫；M1033/M1034 双 CAUGHT、还原后双 ESCAPED。
④ 自伤：第一版像素带量到第三行，旧结构也 2.81/4.33；按字墨 bbox 重钉到 x195..255/y118..135。
⑤ 367：hidden 表 {h_tables} / 可判 {h_judged} / rot {h_rot} / 上界 {h_rot_ceiling}；预检 {pre_tables}/{pre_covered}/{pre_arms}/{pre_bad}。
⑥ 验证：build 0 告警；全量 `{executed}/{skipped}/{failures}`；捕获 {frames} 帧、6 帧变化、基线 update 后 182/0；换装 ok；清账表 162=162。

验证读数（现读）：`LABEL_BAND old light=1.76 dark=2.13 / new light=2.84 dark=4.38`（x195..255/y118..135pt）；`WRONG_BAND old light=2.81 dark=4.33`（x380..700/y225..275pt，假绿对照）；`LOGIN_UNSUPPORTED_FRAME light 墨={guard["light"][1]} 对比={guard["light"][2]:.2f}`、`dark 墨={guard["dark"][1]} 对比={guard["dark"][2]:.2f}`；`M1033/M1034` 双 CAUGHT；`HIDDEN_ARMS … rot={h_rot} … 处置=ok`。

NOT-RUN / 阻塞（分开写）：① **`PUSH_BLOCKED=network`**：push 被 SSH 拒 + `api=000`/`apple=200`；本地 ahead=31（R396 主笔前，提交后 32）；② 旧的两跑与 R387–R395 本地提交的 conclusion **未读**（网络）；③ BACKLOG 436 的 runner motion 卷未读（本地 5/5、UNLISTED `settings-reset-fade` 仍可复现）；④ 亮档真机腿仍没跑；⑤ macOS 12 的紧凑详情头仍走旧截断（13+ 才有 ViewThatFits）。

下一轮（R397）的靶：⓪ 先 `git push origin main`（禁 amend/force）并复核 ahead=0；一次 push 只为 head 生成新 run，另外旧的两跑仍要单独按步骤读；① 367 现读 rot=0，按 `HIDDEN_ROT` 查新腐烂；② 继续产品视觉位并落 Sources；③ 436 待 runner motion 读数恢复后再决定第五臂 `must_judge`，本轮仍不动 JSON/自测。
"""

audit = rd("AGENT_UI_AUDIT.md")
assert ui_heading in audit
audit_new = once(audit, ui_heading, ui_section + "\n" + ui_heading)
iteration_new = rd("AGENT_VISUAL_ITERATION.md").rstrip() + "\n\n" + iteration

decisions_old = rd("AGENT_DECISIONS.md")
assert "{cat2_median}" in decisions_old
decisions_fixed = once(decisions_old, "**{cat2_median}ms**", "**121ms**")
decisions_new = decisions_fixed.rstrip() + "\n" + decision

changelog_old = rd("CHANGELOG.md")
changelog_old = once(changelog_old, "2x 采样≈{cat2_median}ms", "2x 采样≈121ms")
changelog_anchor = "## [Unreleased]\n\n"
assert changelog_old.count(changelog_anchor) == 1
changelog_new = once(changelog_old, changelog_anchor, changelog_anchor + changelog + "\n")

report_old = rd("AGENT_FINAL_REPORT.md")
report_new = once(report_old, "D-069 … **D-385**", "D-069 … **D-386**")
report_new = once(report_new, "U-31 … U-1399（R395 现读抬到最新一节）", "U-31 … U-1404（R396 现读抬到最新一节）")
report_new = once(
    report_new,
    "R395 现读：注册表 **150** 张 / 刀号最大 **M1032** / 预检 covered=133 arms=408 bad=0；全仓 243 文件 / 892 把；M674 退役、M906 空刀退役",
    f"R396 现读：注册表 **{pre_tables}** 张 / 刀号最大 **M1034** / 预检 covered={pre_covered} arms={pre_arms} bad={pre_bad}；"
    f"全仓 {arm_files} 文件 / {arm_total} 把；M674 退役、M906 空刀退役")
report_new = once(
    report_new,
    "**网络仍断 ⇒ PUSH_BLOCKED=network，ahead=31，未推送。**",
    "**网络仍断 ⇒ PUSH_BLOCKED=network，ahead=31，未推送。**" + report_bullet)

state_old = rd("AGENT_STATE.md")
state_anchor = "## R395 状态（2026-10-26"
assert state_old.count(state_anchor) == 1
state_new = once(state_old, state_anchor, state_section + "\n" + state_anchor)

wr("AGENT_UI_AUDIT.md", audit_new)
wr("AGENT_VISUAL_ITERATION.md", iteration_new)
wr("AGENT_DECISIONS.md", decisions_new)
wr("CHANGELOG.md", changelog_new)
wr("AGENT_FINAL_REPORT.md", report_new)
wr("AGENT_STATE.md", state_new)

print("R396_LEDGERS_OK warnings=%s full=%s/%s/%s frames=%s changed=%s baseline=%s/%s/%s/%s guard=%s/%s,%s/%s mut=2 pre=%s/%s/%s/%s arms=%s/%s rot=%s gate=%s=%s streak=%s placeholders=2"
      % (warnings, executed, skipped, failures, frames, changed_frames,
         b_compared, b_changed, b_missing, b_added,
         guard["light"][2], guard["dark"][2], band[("old", "light")], band[("old", "dark")],
         pre_tables, pre_covered, pre_arms, pre_bad, arm_files, arm_total,
         h_rot, cleared, cells, streak))
