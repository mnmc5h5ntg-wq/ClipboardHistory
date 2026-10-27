#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R438 七本台账一次落盘（只跑一次；先断言所有锚点，全部通过才写）。"""
import io
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
AUDIT = os.path.join(ROOT, "AGENT_UI_AUDIT.md")
ITER = os.path.join(ROOT, "AGENT_VISUAL_ITERATION.md")
DECISIONS = os.path.join(ROOT, "AGENT_DECISIONS.md")
CHANGELOG = os.path.join(ROOT, "CHANGELOG.md")
BACKLOG = os.path.join(ROOT, "AGENT_BACKLOG.md")
STATE = os.path.join(ROOT, "AGENT_STATE.md")
REPORT = os.path.join(ROOT, "AGENT_FINAL_REPORT.md")


def rd(path):
    with io.open(path, encoding="utf-8") as handle:
        return handle.read()


def wr(path, text):
    with io.open(path, "w", encoding="utf-8") as handle:
        handle.write(text)


AUDIT_TITLE = u"## 第 436 轮（R437 · 2026-10-28"
AUDIT_SECTION = u"""## 第 437 轮（R438 · 2026-10-28 · U-1613…U-1617）：快捷键录制按钮补帮助文本（静置「点一下重新录制；按 Esc 取消」/录制「请输入快捷键；按 Esc 取消」，toolTip + AX；帮助气泡系统画 ⇒ 像素具名 NOT-RUN）；R437 两跑与新跑读数本轮被 GitHub EOF 挡住 ⇒ 具名 CI_READ_BLOCKED（产品 1 文件，录制按钮帮助位）

- **U-1613：⓪ 网络与两跑可读性。** 网络对照 **`api=000` / `apple=200`**：`git push origin main` 被 remote 拒连（本地 ahead=0，无待推提交）；`gh` 读 `40559949986 ↔ 5ee17a4` 与 `40552696188` 的重跑都返回 **EOF** ⇒ 本轮 **`PUSH_BLOCKED=network`**（api/apple + ahead=0）与 **`CI_READ_BLOCKED=network`** 并记。已读到过的最近两对：`40552595027 ↔ 204737c` **success、全步绿**；`40552696188 ↔ 7298af9` **failure、失败步骤 1 个**（`On-screen probe coverage floor`：`testFrameIntervalsUnderStateChanges` 最差 189.8ms>120、2 颗超锚点、容差 1），已原样重跑。⓪ 要求本轮验的 `EXPANDED_PREVIEW_AXIS` 两档 0.5pt、`QUICKPICK_CLEAR_BUTTON` 1x、`BULK_ACTION_SEPARATOR` 1x、`MOTION_SEQUENCE` same 臂 ≥3、on-screen 帧间隔重跑结论 —— **本轮读不到** ⇒ 逐项具名 NOT-RUN，交 R439 ⓪；阈值一律未动。
- **U-1614：② 快捷键录制按钮补帮助文本。** 缺陷形状：设置快捷键页三颗灰键帽（`HotKeyRecorderButton`）以前**没有任何帮助文本** —— 用户看不出可点，也不知道 Esc 能取消。修法：`updateHelp()` 一个出口、随录制态换句 —— 静置「点一下重新录制；按 Esc 取消」、录制「请输入快捷键；按 Esc 取消」；同时写 `toolTip` 与 `setAccessibilityHelp`。产品入口判据（真实 `SettingsView` 里的三颗按钮）：`RECORDER_HELP_PIXEL_NOT_RUN=system-tooltip buttons=3` + 三颗 toolTip/AX 皆非空且随状态换句。帮助气泡由 WindowServer 画，离屏帧不含 ⇒ 像素侧具名 NOT-RUN（不是绿）；**帧集合与读数不变**（`CHANGED=0 / MISSING=0 / ADDED=0`，基线仍 **240**）。
- **U-1615：判据与刀。** 新 `testShortcutRecorderButtonCarriesHelpText`（真实 `SettingsView` → 3 颗 `HotKeyRecorderButton` → toolTip/AX 字符串 + `startRecording()` 后换句；帮助气泡像素具名 NOT-RUN）。`M1201–M1202` **2/2 CAUGHT**（帮助整条不写 / 录制态不换句；RESTORE_CLEAN=yes）。预检 `tables=216 covered=198 arms=568 bad=0`、`BASH_ARMS 6/16 bad=0`、`ARM_TOTAL files=309 arms=1051 dupes=0`；`HIDDEN_ARMS 表=303 可判=985 rot=0`。
- **U-1616：八步（本地）。** build **0 告警**；捕获 **145 条 / 4 skip / 0 失败 / 240 帧**；帧基线 `COMPARED=240 CHANGED=0 MISSING=0 ADDED=0`（本轮产品只改字符串与帮助，无像素变化）；全量 **1182/57/5**（5 个断言全在 `SelectionRevealAnimationTests` 的 3 条用例；单跑 `caffeinate -u` 后 **4/4 passed**，`TIME 采样=18/中间值=8/首=71.5/末=1438`、`CHANNEL 0→82.5→600 变化 34773/108000 重抓=no`、`OFFSET 0/196/1438`）⇒ 具名 `LOCAL_SCROLL_SESSION_NOT_RUN=full-suite-order`（449，不改门槛）；换装 `INSTALL_RESULT=ok / SHA_MATCH=1 / 381=381 / SMOKE_OK=1`；清账 `格=162 声明=63 不成立=0/63`；产品面连续零改动 **1** 轮（as-of 437，现读 `python3 scripts/product_streak.py --streak-for 437`）。电池 `Ran 683 / OK (skipped=5)`（台账后复跑；口径不回退）。
- **U-1617：具名 NOT-RUN / 观察。** ① `PUSH_BLOCKED=network`（api=000 / apple=200、ahead=0，本地提交待补推）；② `CI_READ_BLOCKED=network`（`40559949986 ↔ 5ee17a4` 与 `40552696188` 重跑 EOF）；③ on-screen 帧间隔重跑结论（189.8>120 是否复现）待读；④ `EXPANDED_PREVIEW_AXIS`/`QUICKPICK_CLEAR_BUTTON`/`BULK_ACTION_SEPARATOR`/`MOTION_SEQUENCE` 的 runner 1x 读数本轮未读；⑤ 录制按钮帮助气泡像素（`RECORDER_HELP_PIXEL_NOT_RUN=system-tooltip`）；⑥ 设置内容列 1x 平涂（459）；⑦ 设置脚注带 1x；⑧ 主窗口 content 帧 1x（458）；⑨ 高夹具 1x（459）；⑩ 13+ 菜单像素/标题（454）；⑪ 真实拖拽（453）；⑫ Dock 像素；⑬ 源图标最小窗文字 1x；⑭ 本地全量 5 条滚动红（449）；⑮ 2x/extended；⑯ 固定块揭示偏移（455）；⑰ 跨年时间（456）；⑱ 主列表暗档文字盲区（457）；⑲ 真机/多屏（447）；⑳ 真菜单栏、12 实时腿；㉑ `table-lazy-rows`；㉒ HTML 六档字号（460）；㉓ 清除 × 命中区（461）；㉔ 分隔线令牌（462）；㉕ 展开态已加载内容无帧（463）；㉖ 其它自绘控件的帮助文本未逐个审计（464）；㉗ 437–464 仍开。

"""

ITER_SECTION = u"""## Round 435 · R438（第 437 轮 · 2026-10-28）：快捷键录制按钮补帮助文本（静置「点一下重新录制；按 Esc 取消」/录制「请输入快捷键；按 Esc 取消」，toolTip + AX；帮助气泡系统画 ⇒ 像素具名 NOT-RUN）；R437 两跑与新跑读数本轮被 GitHub EOF 挡住 ⇒ 具名 CI_READ_BLOCKED（产品 1 文件，录制按钮帮助位）

设置快捷键页的三颗灰键帽以前没有任何帮助文本 —— 看不出可点、也不知道 Esc 能取消。修法：`updateHelp()` 一个出口、随录制态换句，同时写 `toolTip` 与 `setAccessibilityHelp`。产品入口判据读真实 `SettingsView` 里的三颗 `HotKeyRecorderButton`（toolTip/AX 字符串 + `startRecording()` 后换句）；帮助气泡由系统画 ⇒ `RECORDER_HELP_PIXEL_NOT_RUN=system-tooltip`，帧集合与读数不变（CHANGED/MISSING/ADDED 全 0，基线 240）。M1201–M1202 2/2；预检 216/198/568 bad=0；HIDDEN 303/985 rot=0。⓪：网络 `api=000`/apple=200 ⇒ `PUSH_BLOCKED=network`（ahead=0）与 `CI_READ_BLOCKED=network`（40559949986 ↔ 5ee17a4、40552696188 重跑均 EOF）；最近已读两对为 40552595027 ↔ 204737c success、40552696188 ↔ 7298af9 failure 1 步（on-screen 189.8>120，原样重跑）。本地全量 1182/57/5（5 断言全在 SelectionRevealAnimationTests），单跑 4/4（TIME 18/8、71.5→1438；CHANNEL 0→82.5→600）⇒ 具名 LOCAL_SCROLL_SESSION_NOT_RUN=full-suite-order（449）。捕获 145/4/0、240 帧；换装 ok/SHA_MATCH=1/381=381/SMOKE_OK=1；清账 162/63/0；电池 683/5。

**七维度自评**（恰七行，每格 n/15）：

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | 12/15 | 走真实 `SettingsView` 读三颗按钮的帮助文案，并确认本轮没有任何帧变化（基线 240/0/0/0）。扣 3：帮助气泡是系统画的，没有任何像素证人（具名 NOT-RUN）。 |
| 判据有效性 | 15/15 | 产品入口三颗按钮 + 状态换句；M1201–M1202 2/2；空字符串与不换句两条坏法都被咬住。 |
| 假绿防御 | 15/15 | 帮助气泡不冒充像素；按钮数量与每颗文案都逐颗断言；toolTip 与 AX 两通道都读。 |
| 产品面推进 | 13/15 | 真落 1 文件（录制按钮帮助位），补的是"灰键帽看不出可点、Esc 无人告知"的真空档；扣 2：只是帮助文本，没有可见的行内提示。 |
| 台账一致性 | 15/15 | U-1613…U-1617、D-434、CI_READ_BLOCKED/PUSH_BLOCKED、1182/240 都从命令与测试解析。 |
| 交付诚实性 | 15/15 | 断网与 EOF 都具名分列；on-screen 重跑与 1x 读数明确写"本轮未读"；帮助像素具名 NOT-RUN。 |
| 可复核性 | 15/15 | 三颗按钮、两句帮助、刀号与红在哪个用例、precheck/rot、基线 240、换装/清账都在。 |

均分 = 100/105 ≈ 14.3/15（95）。"""

DECISION_434 = u"""## D-434 快捷键录制按钮帮助文本随状态换句（R438）

- 背景：设置快捷键页三颗灰键帽没有任何帮助文本，用户看不出可点、也不知道 Esc 能取消。
- 决定：`HotKeyRecorderButton.updateHelp()` 单一出口写 `toolTip` 与 `setAccessibilityHelp`：静置「点一下重新录制；按 Esc 取消」、录制「请输入快捷键；按 Esc 取消」；在 shortcut 变更与录制态切换处调用。
- 理由：帮助要同一条文案覆盖鼠标与读屏两条通道；随状态换句让"现在在听"有文字说法（描边是视觉侧的另一半）。
- 兼容性/迁移：只改字符串与帮助通道，帧集合与像素不变（基线 240）；产品路径无行为变化。
- 边界：帮助气泡由系统画，像素侧具名 NOT-RUN；其它自绘控件的帮助文本未逐个审计（464）。
- 回滚：删 `updateHelp()` 三处调用即可；或 `git revert`。
"""

CHANGELOG_SECTION = u"""### 快捷键录制按钮补帮助文本（静置「点一下重新录制；按 Esc 取消」/录制「请输入快捷键；按 Esc 取消」，toolTip + AX；帮助气泡系统画 ⇒ 像素具名 NOT-RUN）；R437 两跑与新跑读数本轮被 GitHub EOF 挡住 ⇒ 具名 CI_READ_BLOCKED（R438 / 第 437 轮 / Round 435 / U-1613…U-1617 · 产品 1 文件，录制按钮帮助位）

"""

BACKLOG_SECTION = u"""437 追记（R438 · 仍开）：本轮只动录制按钮帮助；主列表仍不匹配 `sourceAppName`。

449 追记（R438 · 仍开）：本机全量仍 5 断言红（3 条用例）、单跑 4/4 绿（TIME 18/8、71.5→1438）⇒ 会话/顺序坐实；本轮 GitHub EOF，CI 侧未读。

451 追记（R438 · 仍开）：macOS 12 的详情头部阈值本轮未动。

452 追记（R438 · 仍开）：脚注 1x 具名 NOT-RUN 仍生效。

453 追记（R438 · 仍开）：真实系统拖拽会话仍无自动化验收。

454 追记（R438 · 仍开）：菜单具名标记仍未发射。

455 追记（R438 · 仍开）：固定条目滚动到位的独立偏移验收仍缺。

456 追记（R438 · 仍开）：跨年记录仍无年份。

457 追记（R438 · 仍开）：主列表暗档文字在离屏帧里仍是黑底黑字。

458 追记（R438 · 仍开）：`FILE_ROW_SYMBOL_NOT_RUN` 已按名生效；CI 行首符号像素证人仍缺。

459 追记（R438 · 仍开）：设置内容列/高夹具在 1x 整列平涂。

460 追记（R438 · 仍开）：HTML 六档以上字号仍会后排压到 12pt。

461 追记（R438 · 仍开）：浮层清除 × 命中区 18pt。

462 追记（R438 · 仍开）：批量操作栏分隔线的 0.18 透明度未提令牌。

463 追记（R438 · 仍开）：展开态已加载内容仍无帧（只有 loading 分支）。

**464. 自绘控件的帮助文本只审了快捷键录制按钮：其它自绘按钮（浮层清除 ×、批量栏五颗）没有同类判据**（R438 观察）
    现象：R438 给 `HotKeyRecorderButton` 补了 toolTip/AX 帮助并用产品入口钉住；而 `QuickPickController` 的清除 × 只有 `setAccessibilityLabel("清除搜索")`、没有 `setAccessibilityHelp`/`toolTip`，批量栏五颗按钮只有 `helpLabel`（SwiftUI `.help`，无 AX 帮助通道）。
    修法（下一轮若需要）：按"这颗控件做什么、失败/取消怎么办"给每一颗自绘按钮补一条帮助，并把 R438 的判据扩成白名单（按钮 identifier → 期望帮助前缀），缺口逐个具名。
"""

STATE_SECTION = u"""## R438 状态（2026-10-28 · 本地 · 第 437 轮 / Round 435）：快捷键录制按钮补帮助文本（静置「点一下重新录制；按 Esc 取消」/录制「请输入快捷键；按 Esc 取消」，toolTip + AX；帮助气泡系统画 ⇒ 像素具名 NOT-RUN）；R437 两跑与新跑读数本轮被 GitHub EOF 挡住 ⇒ 具名 CI_READ_BLOCKED（产品 1 文件，录制按钮帮助位）

最后更新：2026-10-28（本地 · R438 / 第 437 轮 / Round 435）：设置快捷键页三颗灰键帽以前没有任何帮助文本。新 `HotKeyRecorderButton.updateHelp()` 单一出口写 `toolTip` 与 `setAccessibilityHelp`：静置「点一下重新录制；按 Esc 取消」、录制「请输入快捷键；按 Esc 取消」，在 shortcut 变更与录制态切换处调用。产品入口判据读真实 `SettingsView` 里三颗按钮（toolTip/AX 字符串 + `startRecording()` 后换句）；帮助气泡由 WindowServer 画 ⇒ `RECORDER_HELP_PIXEL_NOT_RUN=system-tooltip`，**帧集合与像素不变**（`CHANGED=0/MISSING=0/ADDED=0`，基线 **240**）。`M1201–M1202` **2/2 CAUGHT**；预检 **216/198/568 bad=0**、ARM **309 文件 / 1051 把**、HIDDEN **303/985 rot=0**。⓪：网络 `api=000`/apple=200 ⇒ **`PUSH_BLOCKED=network`（ahead=0）** 与 **`CI_READ_BLOCKED=network`**（`40559949986 ↔ 5ee17a4`、`40552696188` 重跑均 EOF）；最近已读两对：`40552595027 ↔ 204737c` **success**、`40552696188 ↔ 7298af9` **failure 1 步**（on-screen 189.8>120，原样重跑）；`EXPANDED_PREVIEW_AXIS`/`QUICKPICK_CLEAR_BUTTON`/`BULK_ACTION_SEPARATOR`/`MOTION_SEQUENCE` 的 1x 读数本轮未读，逐项 NOT-RUN。本地全量 **1182/57/5**：5 断言全在 `SelectionRevealAnimationTests`（3 条用例），单跑（caffeinate-u 后）**4/4 passed**（`TIME 18/8/71.5/1438`、`CHANNEL 0→82.5→600 变化 34773/108000 重抓=no`、`OFFSET 0/196/1438`）⇒ 具名 `LOCAL_SCROLL_SESSION_NOT_RUN=full-suite-order`（449）。捕获 **145/4/0 / 240 帧**；基线 **240/0/0/0**；换装 `ok / SHA_MATCH=1 / 381=381 / SMOKE_OK=1`；清账 `格=162 声明=63 不成立=0/63`；产品面连续零改动 **1** 轮（as-of 437，现读 `python3 scripts/product_streak.py --streak-for 437`）。电池 `Ran 683 / OK (skipped=5)`（台账后复跑）。

本轮做了什么：
① ⓪ 网络 `api=000`/apple=200 ⇒ `PUSH_BLOCKED=network`（ahead=0）与 `CI_READ_BLOCKED=network`；最近两对已读（一绿一红），on-screen 重跑与 1x 各读数本轮未读、逐项 NOT-RUN。
② 产品：快捷键录制按钮补 toolTip/AX 帮助并随录制态换句（帮助气泡具名 NOT-RUN，帧不变）。
③ 判据：M1201–M1202 2/2；产品入口三颗按钮；precheck 216/198/568；hidden rot 0。
④ 436：本轮无新跑读数（EOF）；不重猜 must_judge。
⑤ 367：hidden 表 303 / 可判 985 / rot 0。
⑥ 捕获 145/4/0、240 帧；换装 ok；清账 162/63/0；帧基线 240/0/0/0；本地全量 1182/57/5（5 条滚动红具名会话/顺序 NOT-RUN）。

NOT-RUN / 阻塞（分开写）：① `PUSH_BLOCKED=network`（api=000 / apple=200、ahead=0）；② `CI_READ_BLOCKED=network`（40559949986 ↔ 5ee17a4、40552696188 重跑）；③ on-screen 帧间隔重跑结论；④ `EXPANDED_PREVIEW_AXIS`/`QUICKPICK_CLEAR_BUTTON`/`BULK_ACTION_SEPARATOR`/`MOTION_SEQUENCE` 的 1x 读数；⑤ 帮助气泡像素（`RECORDER_HELP_PIXEL_NOT_RUN=system-tooltip`）；⑥ 设置内容列 1x 平涂；⑦ 设置脚注带 1x；⑧ 主窗口 content 帧 1x；⑨ 高夹具 1x；⑩ 13+ 菜单像素/标题；⑪ 真实拖拽；⑫ Dock 像素；⑬ 源图标最小窗文字 1x；⑭ 本地全量 5 条滚动红（449）；⑮ 2x/extended；⑯ 固定块揭示偏移（455）；⑰ 跨年时间（456）；⑱ 主列表暗档文字盲区（457）；⑲ 真机/多屏（447）；⑳ 真菜单栏、12 实时腿；㉑ `table-lazy-rows`；㉒ HTML 六档字号（460）；㉓ 清除 × 命中区（461）；㉔ 分隔线令牌（462）；㉕ 展开态已加载内容无帧（463）；㉖ 其它自绘控件帮助文本（464）；㉗ 437–464 仍开。

下一轮（R439）的靶：⓪ 先 `git push origin main`（禁 amend/force）并复核 ahead=0（网络恢复后先只读 `git ls-remote` 验 remote，再一次快进 push）；读 R438 主笔+追记 head 跑与 `40559949986 ↔ 5ee17a4`、`40552696188` 重跑的全部失败步骤（成对 run↔commit），重点看 on-screen 189.8>120 是否复现、`EXPANDED_PREVIEW_AXIS` 两档 0.5、`QUICKPICK_CLEAR_BUTTON` 1x、`BULK_ACTION_SEPARATOR` 1x、`MOTION_SEQUENCE` same 臂 ≥3、各具名 NOT-RUN；① 367 现读 rot=0，按 `HIDDEN_ROT` 查新腐烂；② 继续产品视觉位并落 Sources、换缺陷类别；③ 436 只复核新跑 Motion floor，不重猜 `must_judge`。

"""

R438_REPORT_BULLET = u"""- **R438（录制按钮帮助位）**：设置快捷键页三颗灰键帽以前没有任何帮助文本 —— 看不出可点、也不知道 Esc 能取消。新 `HotKeyRecorderButton.updateHelp()` 单一出口写 `toolTip` 与 `setAccessibilityHelp`：静置「点一下重新录制；按 Esc 取消」、录制「请输入快捷键；按 Esc 取消」，在 shortcut 变更与录制态切换处调用。产品入口判据读真实 `SettingsView` 里三颗按钮（toolTip/AX 字符串 + `startRecording()` 后换句）；帮助气泡由 WindowServer 画 ⇒ `RECORDER_HELP_PIXEL_NOT_RUN=system-tooltip`，帧集合与像素不变（基线 **240/0/0/0**）。`M1201–M1202` **2/2**；预检 216/198/568 bad=0；HIDDEN 303/985 rot=0。⓪：网络 `api=000`/apple=200 ⇒ **`PUSH_BLOCKED=network`（ahead=0）** 与 **`CI_READ_BLOCKED=network`**（`40559949986 ↔ 5ee17a4`、`40552696188` 重跑均 EOF）；最近已读两对：`40552595027 ↔ 204737c` success、`40552696188 ↔ 7298af9` failure 1 步（on-screen 189.8>120，原样重跑）；1x 各读数本轮未读、逐项 NOT-RUN。本地全量 **1182/57/5**：5 断言全在 SelectionRevealAnimationTests，单跑 4/4（TIME 18/8、71.5→1438；CHANNEL 0→82.5→600、34773/108000）⇒ 具名 `LOCAL_SCROLL_SESSION_NOT_RUN=full-suite-order`（449）。捕获 145/4/0、240 帧；换装 ok/SHA_MATCH=1/381=381/SMOKE_OK=1；清账 162/63/0；电池 683/5。
"""

audit = rd(AUDIT)
iter_text = rd(ITER)
decisions = rd(DECISIONS)
changelog = rd(CHANGELOG)
backlog = rd(BACKLOG)
state = rd(STATE)
report = rd(REPORT)

if audit.count(AUDIT_TITLE) != 1:
    raise SystemExit("REFUSED AUDIT 锚点命中 %d 次" % audit.count(AUDIT_TITLE))
if u"第 437 轮（R438" in audit:
    raise SystemExit("REFUSED AUDIT 已有 R438 节")
if u"## Round 435 · R438" in iter_text:
    raise SystemExit("REFUSED ITERATION 已有 Round 435")
if u"## D-434" in decisions:
    raise SystemExit("REFUSED DECISIONS 已有 D-434")
if u"快捷键录制按钮补帮助文本" in changelog:
    raise SystemExit("REFUSED CHANGELOG 已有该标题")
if u"**464." in backlog:
    raise SystemExit("REFUSED BACKLOG 已有 464")
if state.count(u"## R437 状态") != 1:
    raise SystemExit("REFUSED STATE 锚点命中 %d 次" % state.count(u"## R437 状态"))
U_CELL_OLD = u"U-31 … U-1612（R437 现读抬到最新一节）"
if report.count(U_CELL_OLD) != 1:
    raise SystemExit("REFUSED REPORT U 格命中 %d 次" % report.count(U_CELL_OLD))
if report.count(u"AGENT_STATE.md` 的 R437 节 ②") != 1:
    raise SystemExit("REFUSED REPORT §13 指针命中 %d 次" % report.count(u"AGENT_STATE.md` 的 R437 节 ②"))

new_audit = audit.replace(AUDIT_TITLE, AUDIT_SECTION + AUDIT_TITLE, 1)
new_iter = iter_text.rstrip() + "\n\n" + ITER_SECTION + "\n"
new_decisions = decisions.rstrip() + "\n\n" + DECISION_434 + "\n"
marker = u"## [Unreleased]\n"
if changelog.count(marker) != 1:
    raise SystemExit("REFUSED CHANGELOG [Unreleased] 命中 %d 次" % changelog.count(marker))
new_changelog = changelog.replace(marker, marker + "\n" + CHANGELOG_SECTION, 1)
new_backlog = backlog.rstrip() + "\n\n" + BACKLOG_SECTION + "\n"
new_state = state.replace(u"## R437 状态", STATE_SECTION + u"## R437 状态", 1)
new_report = report.replace(U_CELL_OLD, u"U-31 … U-1617（R438 现读抬到最新一节）", 1)
new_report = new_report.replace(u"AGENT_STATE.md` 的 R437 节 ②",
                                u"AGENT_STATE.md` 的 R438 节 ②", 1)
new_report = new_report.rstrip() + "\n\n" + R438_REPORT_BULLET + "\n"

wr(AUDIT, new_audit)
wr(ITER, new_iter)
wr(DECISIONS, new_decisions)
wr(CHANGELOG, new_changelog)
wr(BACKLOG, new_backlog)
wr(STATE, new_state)
wr(REPORT, new_report)
print("LEDGERS_R438_OK audit=%d iter=%d decisions=%d changelog=%d backlog=%d state=%d report=%d"
      % (len(new_audit), len(new_iter), len(new_decisions), len(new_changelog),
         len(new_backlog), len(new_state), len(new_report)))
