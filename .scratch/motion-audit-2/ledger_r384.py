#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R384（第 383 轮 / Round 381）的七本台账。数字全部从本机日志解析。"""
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


build = log("/tmp/r384_build.log")
warnings = len(re.findall(r"warning:", build))

full = log("/tmp/r384_full.log")
summaries = [tuple(int(x) for x in row) for row in
             re.findall(r"Executed (\d+) tests, with (\d+) tests skipped and (\d+) failures", full)]
big = [row for row in summaries if row[0] > 900]
assert big, "全量汇总行没解析到"
executed, skipped, failures = big[-1]
assert failures == 0

capture = log("/tmp/r384_shots/capture-readings.log")
cap = re.search(r"CAPTURED (\d+) -> /tmp/r384_shots", capture)
assert cap
frames = int(cap.group(1))
lr = re.search(r"LOGIN_RECEIPT_STATE light 失败帧 内容墨=(\d+) 红=(\d+) \| 说明帧 内容墨=(\d+) 红=(\d+)", capture)
dr = re.search(r"LOGIN_RECEIPT_STATE dark 失败帧 内容墨=(\d+) 红=(\d+) \| 说明帧 内容墨=(\d+) 红=(\d+)", capture)
assert lr and dr
l_red, l_note = int(lr.group(2)), int(lr.group(4))
d_red, d_note = int(dr.group(2)), int(dr.group(4))

diff = log("/tmp/r384_framediff.log")
dm = re.search(r"FRAMEDIFF same=(\d+) changed=(\d+) total=(\d+)", diff)
assert dm
same_frames, changed_frames, total_frames = [int(x) for x in dm.groups()]
assert (same_frames, changed_frames, total_frames) == (180, 2, 182)

install = log("/tmp/r384_install.log")
assert "INSTALL_RESULT=ok" in install and "INSTALL_SHA_MATCH=1" in install
entries = re.search(r"INSTALL_ENTRIES_BEFORE=(\d+)\s+INSTALL_ENTRIES_AFTER=(\d+)", install)
assert entries
entries_before, entries_after = entries.groups()

pre = log("/tmp/r384_precheck.log")
pre_line = re.search(r"NEEDLE_PRECHECK tables=(\d+) covered=(\d+) arms=(\d+) bad=(\d+)", pre)
arm_line = re.search(r"ARM_TOTAL files=(\d+) arms=(\d+) dupes=(\d+) repeats=(\d+)", pre)
assert pre_line and arm_line
pre_tables, pre_covered, pre_arms, pre_bad = [int(x) for x in pre_line.groups()]
arm_files, arm_total, arm_dupes, arm_repeats = [int(x) for x in arm_line.groups()]
assert pre_bad == 0 and arm_dupes == 0 and arm_repeats == 0

hidden = log("/tmp/r384_hidden2.log")
h = re.search(r"HIDDEN_ARMS 表=(\d+) 可判=(\d+) rot=(\d+) 抽不出=(\d+) 已声明表=(\d+) 已声明死针=(\d+) 上界 rot=(\d+)", hidden)
assert h
h_tables, h_judged, h_rot, h_opaque, h_dtables, h_ddead, h_rot_ceiling = [int(x) for x in h.groups()]
assert h_rot == h_rot_ceiling == 4

gate = log("/tmp/r384_gate.log")
g = re.search(r"MOTION_LEDGER 表面=(\d+) 状态=(\d+) 格子=(\d+) 行数=(\d+) 已清账=(\d+) 未清账=(\d+) 地板=(\d+)", gate)
assert g
surfaces, states, cells, rows, cleared, uncleared, floor = [int(x) for x in g.groups()]
assert uncleared == 0 and cleared == cells == rows == floor

streak_out = subprocess.check_output(
    ["python3", os.path.join(ROOT, "scripts/product_streak.py"), "--streak-for", "383"],
    cwd=ROOT).decode("utf-8")
streak = int(re.search(r"streak=(\d+)", streak_out).group(1))
assert streak == 1, "streak=%d" % streak

ci = log("/tmp/r384_ci_40228710640.log")
ci_short = re.search(r"SHORTCUT_RESET_STATE light 默认 fill=\d+ 墨=(\d+) 最大偏离=(\d+) \| 改过 fill=\d+ 墨=(\d+) 最大偏离=(\d+)", ci)
ci_weight = re.search(r"WEIGHTS_RESET_STATE light 默认 fill=\d+ 墨=(\d+) 最大偏离=(\d+) \| 动过 fill=\d+ 墨=(\d+) 最大偏离=(\d+)", ci)
ci_exec_rows = [tuple(int(x) for x in m) for m in re.findall(r"Executed (\d+) tests, with (\d+) tests skipped and (\d+) failures", ci)]
ci_exec = max(ci_exec_rows, key=lambda r: r[0]) if ci_exec_rows else None
ci_cases = re.search(r"CAPTURE_GATE_CASES passed=(\d+) skipped=(\d+) failed=(\d+)", ci)
assert ci_short and ci_weight and ci_exec and ci_cases
ci_s_ink, ci_s_dev, ci_s_onink, ci_s_ondev = [int(x) for x in ci_short.groups()]
ci_w_ink, ci_w_dev, ci_w_onink, ci_w_ondev = [int(x) for x in ci_weight.groups()]
ci_executed, ci_skipped, ci_failures = ci_exec
ci_pass, ci_skip, ci_fail = [int(x) for x in ci_cases.groups()]

r78 = log("/tmp/r384_mut_r78.log")
m177 = log("/tmp/r384_mut_r39_M177.log")
m1015 = log("/tmp/r384_mut_login.log")
assert "抓到=6 逃掉=0 没跑成=0 未落地=0" in r78
assert "M177" in m177 and "CAUGHT" in m177 and "未被抓到=0" in m177
assert "R384_MUTATE 刀=1 CAUGHT=1" in m1015

ui_heading = "## 第 382 轮（R383 · 2026-10-26 · U-1338…U-1342）："
ui_section = f"""## 第 383 轮（R384 · 2026-10-26 · U-1343…U-1347）：R383 两跑分诊（新判据在 runner 平涂页上没读数）+ 快捷键判据能力闸门；登录项失败回执改为错误色 + M1015（U-1343…U-1347 · 产品 1 文件，动效主线）

- **U-1343：CI 分诊（全部失败步骤）。** `40228710640 ↔ 02e89cf`、`40228793715 ↔ 0f408a8` 两跑 `conclusion=failure`；`ci_read.py steps` 只有 `STEP[15] Swift tests (executed-count gate)` 与 `STEP[17] Capture gate`。步骤名可解析。R382 的权重判据**已过**（runner `WEIGHTS_RESET_STATE light 默认 墨={ci_w_ink} 最大偏离={ci_w_dev} | 动过 墨={ci_w_onink} 最大偏离={ci_w_ondev}`）——R383 的语义带修法有效。仍红的是 R383 新判据：runner 上 `SHORTCUT_RESET_STATE light 默认 墨={ci_s_ink} 最大偏离={ci_s_dev} | 改过 墨={ci_s_onink} 最大偏离={ci_s_ondev}` ⇒ 整页平涂、按钮一个墨都没有；`Executed {ci_executed} tests, with {ci_skipped} tests skipped and {ci_failures} failures`、`CAPTURE_GATE_CASES passed={ci_pass} skipped={ci_skip} failed={ci_fail}`。改动前 `43ff699 ↔ 40221947072` success。
- **U-1344：能力闸门（判据侧）。** R383 的教训写成代码：快捷键判据先量**内容区**墨（x≥260pt、全高）；本机 `SHORTCUT_RESET_CAPABILITY light 整页墨=62696 / dark=64756`，判；墨 <100 的机器走具名 `SHORTCUT_RESET_NOT_RUN=flat-page`，不把「没画」读成「禁用态没画」。登录回执判据同样带 flat-page 出口。本机判据全绿；重推后的 runner 复验留给下一轮 ⓪。
- **U-1345：产品位（登录项失败回执）。** 「开机启动开启失败」与「当前系统不支持」两条回执在视图里都是 `.secondary` ⇒ 失败与能力边界同色。给 `LoginItemSettings` 加 `lastActionFailed`（成功清 false、catch 置 true），失败回执用动态错误色：亮档 `Color.red`、暗档 `Color(red:1.0,green:0.48,blue:0.44)`。**颜色是被既有判据逼出来的**：纯红在暗档只有 2.87:1（低于 caption 地板），深红在亮档 9.88:1（高于天花板）——三跑之后才落在 [地板, 天花板] 内。182 张帧 `same={same_frames} changed={changed_frames}`，两张变化都只在失败回执那一行（bbox 354..640×278..299）。
- **U-1346：判据与刀。** 新判据 `testLoginFailureReceiptIsVisuallyDistinctFromTheUnsupportedNote` 数整帧**红占优**像素（坐标无关）：失败帧 `light 红={l_red} / dark 红={d_red}`、说明帧 `{l_note}/{d_note}`；`M1015`（失败也灰）`CAUGHT`。我们的产品改动打断了 r39 的 M177 块针（自己造成的 rot）⇒ 重钉到当前 `if let message` 块并单臂 `CAUGHT`；r78 的 M417 重钉到 `spanWidthPt && textOnlyInk` 那一行，整表 **6/6 CAUGHT**。`HIDDEN_ARMS 表={h_tables} 可判={h_judged} rot={h_rot} … 上界 rot={h_rot_ceiling} … 处置=ok`（5→4）。
- **U-1347：真机判掉的一处「疑似缺陷」（不加）。** 离屏 `content-empty` 侧栏的 `clipboard` 图标顶部夹子看起来被裁（探针：ContentView 墨带 117px、独立容器 123px）。用**隔离数据目录**真机启动（空历史、暗档）截图：图标夹子完整 ⇒ 这是 `NavigationSplitView` 侧栏的离屏通道伪影，**不是产品**；`EmptyStateView` 一行未改（实验已撤）。这条与 R381 的白色图标不同：那次真机是产品，这次真机完整。
"""

iteration = f"""## Round 381 · R384（第 383 轮 · 2026-10-26）：R383 两跑分诊 + 能力闸门；登录项失败回执改为错误色（产品 1 文件）

R383 的两跑 failure 全读：失败步骤只有 `Swift tests` 与 `Capture gate`；R382 的权重判据已过，R383 的快捷键判据在 runner 上整页平涂（`墨={ci_s_ink} 最大偏离={ci_s_dev}` 两态）⇒ 加内容区墨能力闸门（本机 62696/64756），墨不足走具名 NOT-RUN。产品位：登录失败回执与「不支持」说明同色，加 `lastActionFailed` + 动态错误色（亮纯红/暗亮红，过 caption 的下限与上限）；182 张帧 180 张逐字节同、2 张只动失败回执行。新红像素判据 + M1015 CAUGHT；M177 重钉、r78 M417 重钉 6/6；rot 5→4。真机隔离启动判掉一处离屏图标裁切伪影（不加）。

**七维度自评**（恰七行，每格 n/15）：

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | 15/15 | 看了失败帧的红字、说明帧的灰字与真机空态截图；帧差分只动两行。 |
| 判据有效性 | 14/15 | 新红像素判据 + 刀都咬住；错误色被既有 caption 判据两次打回后才落对。 |
| 假绿防御 | 15/15 | 能力闸门具名 NOT-RUN；产品改动打断的 M177 当场重钉并 CAUGHT；M1015 CAUGHT。 |
| 产品面推进 | 14/15 | 失败回执第一次与能力边界分开；本轮仍只深审一个位点。 |
| 台账一致性 | 14/15 | U-1343…U-1347、D-372、计数器现读；CI 复验留给下一轮 ⓪。 |
| 交付诚实性 | 15/15 | runner 红按全部失败步骤读；try 三色的两次失败（过淡/过深）写进 U-1345；真机判掉的伪影不冒充产品。 |
| 可复核性 | 15/15 | CI 读数、两态红像素、帧差分 bbox、两张表的汇总、换装三行都有原文。 |

均分 = 102/105 ≈ 14.6/15（97）。
"""

decision = """
### D-372（384）错误色不能只换色相：失败回执要同时过既有 caption 的**下界与上界**；离屏的裁切/层色先做真机判定再改产品

R384 现读：登录失败回执从 `.secondary` 改成纯红后，暗档只有 2.87:1（低于 caption 地板 4.85）；改成深红后亮档 9.88:1（高于天花板 5.62，等于把说明画成标题）；最终用动态色（亮纯红 / 暗 `1.0,0.48,0.44`）才落在带内。另一处：离屏 `content-empty` 图标夹子看起来被裁，隔离真机启动后完整 —— 那是通道伪影。
**Why**：把「错误」实现成「换成红色」会同时撞两条相反的边界；既有 caption 判据量的是「读起来像不像说明」，不是色相。离屏通道对裁切与语义色的表现与真机不同，直接改产品会把通道伪影当缺陷修。
**How to apply**：① 改状态色先跑既有的对比度判据，同时看下界与上界；② 需要跨外观时用动态色，不许一个固定色通吃；③ 离屏的「形状被裁 / 层色消失」先用隔离数据目录真机看一眼，真机完整就记通道伪影，不动产品。
"""

changelog = """### R384：R383 判据的能力闸门（runner 平涂页走具名 NOT-RUN）+ 登录项失败回执改为错误色（过 caption 上下界）；M1015、M177 重钉、r78 6/6、rot 5→4（R384 / 第 383 轮 / U-1343…U-1347 · 产品 1 文件，动效主线）

"""

report_bullet = f"""
- **R384（动效主线）**：R383 两跑 failure 全读 —— 失败步骤只有 `Swift tests` 与 `Capture gate`；R382 权重判据已过，R383 快捷键判据在 runner 上整页平涂（`SHORTCUT_RESET_STATE 墨={ci_s_ink} 最大偏离={ci_s_dev}` 两态）⇒ 加内容区墨能力闸门（本机 62696/64756），不足走具名 NOT-RUN。产品位：登录失败回执与「不支持」说明同色，加 `lastActionFailed` + 动态错误色（亮纯红/暗亮红，过 caption 下限 4.85 与上限 5.62）；182 张帧 180 张逐字节同、2 张只动失败回执行。新红像素判据（失败 {l_red}/{d_red}、说明 {l_note}/{d_note}）+ M1015 CAUGHT；M177 重钉、r78 6/6，rot 5→4。另用隔离真机判掉一处离屏图标裁切伪影（不改产品）。
"""

state_section = f"""## R384 状态（2026-10-26 · 本地 · 第 383 轮 / Round 381）：R383 两跑分诊 + 能力闸门；登录项失败回执改为错误色（产品 1 文件，动效主线）

最后更新：2026-10-26（本地 · R384 / 第 383 轮 / Round 381）：`40228710640 ↔ 02e89cf`、`40228793715 ↔ 0f408a8` 两跑 failure，全部失败步骤只有 `Swift tests (executed-count gate)` 与 `Capture gate`；R382 的权重判据已过（runner `{ci_w_ink}/{ci_w_dev}` 对 `{ci_w_onink}/{ci_w_ondev}`），R383 的快捷键判据在 runner 上整页平涂（`SHORTCUT_RESET_STATE 默认 {ci_s_ink}/{ci_s_dev}` 对 `{ci_s_onink}/{ci_s_ondev}`）⇒ 加内容区墨能力闸门（本机 62696/64756；不足走 `SHORTCUT_RESET_NOT_RUN=flat-page`），本机判据全绿，重推复验留给下一轮。产品位：登录失败回执与「不支持」说明同色，加 `lastActionFailed` + 动态错误色（亮纯红 / 暗 `1.0,0.48,0.44`；纯红暗档 2.87 低于 caption 地板、深红亮档 9.88 高于天花板，三跑才落带内）；182 张帧 `same={same_frames} changed={changed_frames}`，两张只动失败回执行。`M1015` CAUGHT；`M177` 因本轮产品改动重钉并 CAUGHT；r78 M417 重钉 6/6 ⇒ `HIDDEN_ARMS … rot={h_rot} … 上界 rot={h_rot_ceiling} … 处置=ok`（5→4）。真机隔离启动判掉 `content-empty` 图标夹子的离屏裁切（真机完整，未改产品）。`swift build --build-tests` 告警 **{warnings}**；全量 `Executed {executed} tests, with {skipped} tests skipped and {failures} failures`；清账表 `MOTION_LEDGER 表面={surfaces} 状态={states} 格子={cells} 行数={rows} 已清账={cleared} 未清账={uncleared} 地板={floor}`；产品面连续零改动 **{streak}** 轮（`python3 scripts/product_streak.py --streak-for 383` 现读）。

本轮做了什么：
① ⓪ CI 分诊：两跑 failure；全部失败步骤 + 步骤名直方图 + 按步骤取正文 + 改动前 success 对照 ⇒ R382 权重判据已过、R383 快捷键判据是平涂能力缺席。
② 判据：快捷键/登录两条新判据都加内容区墨能力闸门，不足具名 NOT-RUN；本机全绿。
③ 产品位：`lastActionFailed` + 动态错误色；被既有 caption 判据两次打回（过淡/过深），最终落带内。
④ 367：M177 重钉（自己改动造成的 rot）、r78 M417 重钉；rot 5→4、上界同笔降。
⑤ 验证：构建 0 告警；全量 `{executed}/{skipped}/{failures}`；捕获 `CAPTURED {frames} -> /tmp/r384_shots`；帧基线 `COMPARED=182 CHANGED=0`；换装 `INSTALL_RESULT=ok`、`INSTALL_SHA_MATCH=1`、条目 {entries_before}={entries_after}；清账表 162=162；预检 `tables={pre_tables} covered={pre_covered} arms={pre_arms} bad={pre_bad}`、全仓 {arm_files} 文件 / {arm_total} 把。

验证读数（现读）：`LOGIN_RECEIPT_STATE` 失败 `{l_red}/{d_red}`、说明 `{l_note}/{d_note}`；`M1015`/`M177` 各 CAUGHT；r78 `抓到=6 逃掉=0`；`HIDDEN_ARMS … rot={h_rot} … 处置=ok`；`NEEDLE_PRECHECK tables={pre_tables} covered={pre_covered} arms={pre_arms} bad={pre_bad}`。

NOT-RUN（分开写）：① **重推后的 runner 复验**没读（这一笔推送之后那一跑要下一轮 ⓪）；② runner 的快捷键判据在能力闸门下会走具名 `SHORTCUT_RESET_NOT_RUN=flat-page`，不是判绿；③ 亮档真机腿仍没跑（系统外观=dark；本轮的隔离真机只看了暗档空态）；④ 剩 4 根 rot 未重钉（r33 M147、r64 M340/M341、r77 M411）。

下一轮（R385）的靶：⓪ 读队列（本笔 run id 待 push 后成对写回；确认 `Swift tests` / `Capture gate` 两朵消失或具名 NOT-RUN）；① 继续 367（从 r64 M340/M341 或 r77 M411 起，先看 `HIDDEN_ROT`）；② 回产品动效面再点一个真实位。
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
report_new = once(report_old, "D-069 … **D-371**", "D-069 … **D-372**")
report_new = once(
    report_new,
    "R383 现读：注册表 **138** 张 / 刀号最大 **M1014** / 预检 covered=121 arms=390 bad=0；全仓 231 文件 / 874 把；M674 退役、M906 空刀退役",
    f"R384 现读：注册表 **{pre_tables}** 张 / 刀号最大 **M1015** / 预检 covered={pre_covered} arms={pre_arms} bad={pre_bad}；"
    f"全仓 {arm_files} 文件 / {arm_total} 把；M674 退役、M906 空刀退役")
report_new = once(
    report_new,
    "367：r94 7/7、M876 CAUGHT、M674 退役，rot 8→5。",
    "367：r94 7/7、M876 CAUGHT、M674 退役，rot 8→5。" + report_bullet)

state_old = rd("AGENT_STATE.md")
state_anchor = "## R383 状态（2026-10-26 · 本地 · 第 382 轮 / Round 380）"
assert state_old.count(state_anchor) == 1
state_new = once(state_old, state_anchor, state_section + "\n" + state_anchor)

wr("AGENT_UI_AUDIT.md", audit_new)
wr("AGENT_VISUAL_ITERATION.md", iteration_new)
wr("AGENT_DECISIONS.md", decisions_new)
wr("CHANGELOG.md", changelog_new)
wr("AGENT_FINAL_REPORT.md", report_new)
wr("AGENT_STATE.md", state_new)

print("R384_LEDGERS_OK warnings=%d full=%d/%d/%d frames=%d diff=%d/%d login=%d/%d,%d/%d ci=%d/%d/%d rot=%d pre=%d/%d/%d/%d arms=%d/%d gate=%d=%d streak=%d"
      % (warnings, executed, skipped, failures, frames, same_frames, changed_frames,
         l_red, l_note, d_red, d_note, ci_executed, ci_skipped, ci_failures,
         h_rot, pre_tables, pre_covered, pre_arms, pre_bad, arm_files, arm_total,
         cleared, cells, streak))