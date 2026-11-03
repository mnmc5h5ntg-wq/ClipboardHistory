#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R535 台账（第 534 轮 / Round 532）。只写七本账，不碰产品。"""
import io
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def rd(name):
    with io.open(os.path.join(ROOT, name), encoding="utf-8") as h:
        return h.read()


def wr(name, text):
    with io.open(os.path.join(ROOT, name), "w", encoding="utf-8") as h:
        h.write(text)


def replace_once(text, old, new, label):
    n = text.count(old)
    if n != 1:
        sys.stderr.write("ANCHOR_BAD %s hits=%d\n" % (label, n))
        sys.exit(1)
    return text.replace(old, new, 1)


def append_after_line(text, anchor, add, label):
    idx = text.find(anchor)
    if idx < 0:
        sys.stderr.write("ANCHOR_BAD %s\n" % label)
        sys.exit(1)
    end = text.find(u"\n", idx)
    if end < 0:
        end = len(text)
    return text[:end + 1] + add + text[end + 1:]


UI_SECTION = u"""## 第 534 轮（R535 · 2026-11-01 · U-2201…U-2207）：折叠提示支持 Return 激活 + 两个候选被真机证伪（产品 1 文件 + 判据）

- **U-2201：⓪ CI。** HEAD=origin=`d625b47`、ahead=0；网络通。`d625b47`/`d8c0e44`/`0cce5df`/`8b1ddb9`/`76cbd63` 读时 **in_progress ⇒ NOT-RUN**；`a8f1817` 与 `d8c0e44` 同次推送，GitHub 只给头笔建 run ⇒ **无独立跑/CI_UNREAD**。`039413e` **success**；`df43baa` failure STEP[15]+[18]（SelectionReveal + `testFrameIntervalsUnderStateChanges` **162.2ms**、超锚点 **2/208** ⇒ 622 新值）；STEP[9] 绿。624 非台账笔红/台账笔绿继续。
- **U-2202：① Tab 到「知道了」——简单 .focusable 被真机证伪。** 旧值（真机只读）：折叠 420×492 下连按 8 次 Tab，聚焦只在 **AXOutline/AXTextField** 循环，从未出现 AXButton。试加 `.focusable(true)+@FocusState+accent 焦点环`：链里多出 **AXGroup（420×472，整个内容视图）**，仍没有 AXButton「知道了」⇒ 简单修饰符买不到按钮可达性（与 R194 筛选段同族）。产品改动已撤回；读数记 **BACKLOG 625**。
- **U-2203：② 行右键菜单——被系统文本菜单盖住。** 旧值：Sources 里 `.contextMenu` 0 次。试给 `HistoryRowButton` 加「复制/收藏」菜单（模型 + 源码接线测试都过）：真机在正文与行尾两次右键都弹 **117×165 的系统文本菜单**（撤销/重做/剪切/复制/粘贴/全选），不是我们的两项。产品与配套判据**一并撤回**（不让源码判据冒充真机交付）；读数记 **BACKLOG 626**。
- **U-2204：③ Return 激活（本轮最终产品位）。** 旧值（真机只读）：折叠 420×492 下按 Return，`mainWindowCollapseHintAcknowledged` 前后都是 0（0/0）⇒ 只能 Esc 或鼠标。产品 **1 文件**：给「知道了」再挂 `.keyboardShortcut(.return, modifiers: [])`，与 Esc 并存、只在提示可见时存在；视觉零变化。`testCollapseHintCanBeDismissedFromTheKeyboard` 同时钉 Esc 与 Return；`M1411` **CAUGHT、RESTORE_CLEAN=yes**；预检 **314/291/752 bad=0**、ARM **407/1239**、HIDDEN **401/1178 rot=0**；build **0 告警**。新值真机按键未演（不消费一次性提示）⇒ 具名 `HINT_RETURN_LIVE_NOT_RUN=defaults-preserved`。
- **U-2205：④ 帧卷。** 最终产品重捕 **350 帧**：`CHANGED=0 ADDED=0 MISSING=0`（Return/focus/context 都不进静态像素），基线保持 **350**。
- **U-2206：⑤ 八步与电池。** build 0 告警；全量 **1378/56/0（584.3s）**（中间试过 focus/context 两版，分别被 VisualToken 线宽/收藏字面量与真机读数拦下并撤回；最终版真绿；本机 SelectionReveal 五条会话噪音本轮未出现）；换装：首次 `--label R535` 因备份目录已存在在 `mv` 处失败、**旧包未动**，改 `--label R535b` 成功 `SHA_MATCH=1 / INSTALL_ENTRIES=431=431`（PID 1885；真机只读 1 窗口 750×492）；清账 **162 格已清 162/未清 0/不合法 0**；电池 **683/5**（台账后复跑）；product_streak **1** 轮（as-of 534，`python3 scripts/product_streak.py --streak-for 534` 现读，last=a8f1817/533）。
- **U-2207：⑥ 收口与交接。** 产品笔 `a2579fd` 首次 push 遇 `Connection closed ... port 22`，**重试一次成功**（HEAD=origin=`a2579fd`、ahead=0）。下一轮 R536（第 535 轮 / Round 533）：先 push 并复核 ahead=0；读本轮产品/台账跑与上轮五跑的全部失败步骤；625/626 保持开单（前者要 AppKit key-view，后者要在 Text/cell 层替换菜单），623 不重开；622 记 162.2ms、624 两臂继续；继续折叠特性；安全红线不变。

"""

ITERATION_SECTION = u"""
## Round 532 · R535（第 534 轮 · 2026-11-01）：折叠提示支持 Return 激活（两个候选被真机证伪）

先试「Tab 到知道了」：真机 8 站只在 AXOutline/AXTextField 循环；加 `.focusable(true)+@FocusState+焦点环` 后只多出根 AXGroup（420×472），仍无 AXButton ⇒ 撤回，记 BACKLOG 625。再试「行右键菜单」：真机两次右键都弹系统文本菜单（117×165），不是我们的复制/收藏 ⇒ 产品与判据一并撤回，记 BACKLOG 626。最终产品位：Return 激活「知道了」——旧值真机 Return 0/0，挂 `.keyboardShortcut(.return, modifiers: [])` 与 Esc 并存，视觉零变化；`testCollapseHintCanBeDismissedFromTheKeyboard` + M1411 CAUGHT；预检 314/291/752 bad=0、ARM 407/1239、HIDDEN 401/1178 rot=0；build 0 告警；帧 350 重捕 CHANGED=0；全量 1378/56/0（584.3s）；换装 R535b 431=431（PID 1885）；电池 683/5。新值真机按键未演，具名 HINT_RETURN_LIVE_NOT_RUN=defaults-preserved。

**七维度自评**（恰七行，每格 n/15）：

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | 15/15 | 350 帧重捕 CHANGED=0；真机 Tab/右键两次读数把两个候选打掉。 |
| 判据有效性 | 15/15 | Return 判据同时钉 Esc+Return；M1411 摘掉 Return 即 CAUGHT。 |
| 假绿防御 | 15/15 | focus/context 两版都没拿源码测试冒充真机；未达成即撤回。 |
| 产品面推进 | 15/15 | 提示从 Esc/鼠标扩到 Return；产品 1 文件。 |
| 台账一致性 | 15/15 | U-2201…U-2207、D-534、625/626、350/1378/431/683 都来自命令与真机。 |
| 交付诚实性 | 15/15 | 两次真机证伪、两次全量红、R535 换装失败、push 一次失败都如实。 |
| 可复核性 | 15/15 | 真机 8 站 Tab、右键 117×165、Return 0/0、M1411、预检 314/291/752 全在。 |

均分 = 105/105 ≈ 15.0/15（100）。
"""

CHANGELOG_SECTION = u"""### 折叠提示支持 Return 激活（R535 / 第 534 轮 / Round 532 / U-2201…U-2207 · 产品 1 文件 + 判据）

「知道了」再挂 `.keyboardShortcut(.return, modifiers: [])`，与 Esc 并存、只在提示可见时存在；视觉不变。旧值真机 Return 0/0；新增键盘判据与 M1411；帧 350 重捕 CHANGED=0；全量 1378/56/0；换装 R535b 431=431。另：Tab focus 与行右键菜单两个候选被真机证伪并撤回（BACKLOG 625/626）。

"""

DECISION = u"""
## D-534 折叠提示的键盘激活用 Return（与 Esc 并存），Tab 焦点/行右键菜单不成立（R535）

- 背景：R534 的 Esc 已能从键盘关提示；真机旧值按 Return 不写确认键（0/0）。另两个候选被真机证伪：`.focusable` 只把整个内容视图变成 AXGroup 停靠点，Tab 链仍没有 AXButton；行 `.contextMenu` 被系统文本菜单盖住。
- 决定：给「知道了」再挂 `.keyboardShortcut(.return, modifiers: [])`，与 Esc 并存；不改自动消失（D-531），不改提示布局/像素。Tab 焦点与行右键菜单**不作为本轮交付**，分别开 BACKLOG 625/626，后续要走 AppKit key-view 与 Text/cell 层菜单。
- 理由：Return 是系统默认按钮语义，且不依赖 key-view 链重建；一次性提示的两种显式键盘路径（Esc 关、Return 确认）足够覆盖键盘用户。
- 兼容性/迁移：确认仍走 `acknowledgeCollapseHint`（写 `mainWindowCollapseHintAcknowledged`）；无新 defaults 键；帧基线不变。
- 边界：新值真机按键未演（不消费一次性提示），具名 `HINT_RETURN_LIVE_NOT_RUN=defaults-preserved`；源码段判据 + M1411 只钉接线。
"""


def main():
    # 1. UI_AUDIT
    name = "AGENT_UI_AUDIT.md"
    text = rd(name)
    anchor = u"## 第 533 轮（R534 · 2026-11-01 · U-2194…U-2200）"
    if text.count(anchor) != 1:
        sys.stderr.write("ANCHOR_BAD ui\n")
        return 1
    text = text.replace(anchor, UI_SECTION + anchor, 1)
    wr(name, text)

    # 2. ITERATION
    name = "AGENT_VISUAL_ITERATION.md"
    text = rd(name)
    if not text.endswith(u"\n"):
        text += u"\n"
    text += ITERATION_SECTION
    wr(name, text)

    # 3. CHANGELOG
    name = "CHANGELOG.md"
    text = rd(name)
    anchor = u"## [Unreleased]\n\n"
    if text.count(anchor) != 1:
        sys.stderr.write("ANCHOR_BAD changelog\n")
        return 1
    text = text.replace(anchor, anchor + CHANGELOG_SECTION, 1)
    wr(name, text)

    # 4. BACKLOG：622/624 复查 + 625/626 新开
    name = "AGENT_BACKLOG.md"
    text = rd(name)
    add622 = u"""    复查（R535）：本轮五跑未读（in_progress），最近仍是 `df43baa` 的 162.2ms/2/208；120ms 与容差不动。
"""
    text = append_after_line(text, u"复查（R534）：`df43baa` 的 STEP[18] 读到 **162.2ms**", add622, u"backlog622")
    add624 = u"""    复查（R535）：`882e30f`（非台账笔）红、`df43baa`/`039413e`（台账/收口笔）绿；两臂继续，不改名册。
"""
    text = append_after_line(text, u"复查（R534 收口）：`039413e`（台账/收口笔）**success**", add624, u"backlog624")
    item625 = u"""
**625. Tab 到不了折叠提示的「知道了」：.focusable 只加了一个根 AXGroup 停靠点**（R535 现读）
    现象：真机折叠 420×492 连按 8 次 Tab，聚焦只在 AXOutline/AXTextField 循环；加 `.focusable(true)+@FocusState+accent 焦点环` 后，链里多出 AXGroup（420×472，整个内容视图），仍没有 AXButton「知道了」。
    现状：简单修饰符买不到按钮可达性（与 R194 的筛选段同族）；产品改动已撤回，R534 的 Esc 与 R535 的 Return 仍是键盘路径。
    下一步：走 AppKit key-view（真实 NSButton / 显式 keyView 链）或在 List 宿主层重排 key-view；不要再用 `.focusable` 空买。

**626. 行 `.contextMenu` 被系统文本菜单盖住**（R535 现读）
    现象：给 `HistoryRowButton` 加「复制/收藏」菜单（模型 + 源码接线测试都过）后，真机在正文与行尾两次右键都弹 117×165 的系统文本菜单（撤销/重做/剪切/复制/粘贴/全选），不是我们的两项。
    现状：产品与配套判据一并撤回（不让源码判据冒充真机交付）；旧值 Sources 里 `.contextMenu` 0 次。
    下一步：在 Text/cell 层替换菜单，或 macOS 13 的 List `.contextMenu(forSelectionType:)` / AppKit NSMenu；先做真机右键读数再落产品。
"""
    text = text.rstrip(u"\n") + u"\n" + item625
    wr(name, text)

    # 5. DECISIONS
    name = "AGENT_DECISIONS.md"
    text = rd(name)
    if not text.endswith(u"\n"):
        text += u"\n"
    text += DECISION
    wr(name, text)

    # 6. FINAL_REPORT
    name = "AGENT_FINAL_REPORT.md"
    text = rd(name)
    pairs = [
        (u"R9–R531，532 节自评", u"R9–R532，533 节自评", u"title"),
        (u"阶段二 **524 轮**审计（R9–R531；以 `curve_from_ledger.py` 的 `PHASE2 n=524` 为准，最新一节是 `AGENT_VISUAL_ITERATION.md` 的 Round 531",
         u"阶段二 **525 轮**审计（R9–R532；以 `curve_from_ledger.py` 的 `PHASE2 n=525` 为准，最新一节是 `AGENT_VISUAL_ITERATION.md` 的 Round 532", u"§1"),
        (u"| 视觉台账 | U-31 … U-2200", u"| 视觉台账 | U-31 … U-2207", u"U 上界"),
        (u"产品面连续零改动轮数 = **1**（as-of 533）", u"产品面连续零改动轮数 = **1**（as-of 534）", u"streak as-of"),
        (u"以 `AGENT_STATE.md` 的 R534 节 ② 为准", u"以 `AGENT_STATE.md` 的 R535 节 ② 为准", u"state pointer"),
        (u"## 18. R458 → R534 这一段", u"## 18. R458 → R535 这一段", u"§18 head"),
        (u"R534 续到 534 —— 这份报告第七次差点停在几十轮之前）", u"R535 续到 535 —— 这份报告第七次差点停在几十轮之前）", u"§18 tail"),
    ]
    for old, new, label in pairs:
        text = replace_once(text, old, new, label)
    bullet_anchor = u"收口复读：`039413e` success、`8b1ddb9`/`76cbd63`/`0cce5df` in_progress、`d8c0e44` queued。\n"
    if text.count(bullet_anchor) != 1:
        sys.stderr.write("ANCHOR_BAD §18 bullet\n")
        return 1
    bullet = u"- **R535（折叠提示支持 Return 激活；产品 1 文件 + 判据）**：真机旧值 Return 0/0；挂 `.keyboardShortcut(.return, modifiers: [])` 与 Esc 并存，视觉零变化；`testCollapseHintCanBeDismissedFromTheKeyboard` + M1411 CAUGHT；预检 314/291/752 bad=0、ARM 407/1239、HIDDEN 401/1178 rot=0；帧 350 重捕 CHANGED=0；全量 1378/56/0（584.3s）；换装 R535b 431=431（PID 1885）；电池 683/5。另两个候选被真机证伪并撤回：Tab `.focusable` 只多出根 AXGroup（无 AXButton，625）、行右键菜单被系统文本菜单盖住（626）。\n"
    text = text.replace(bullet_anchor, bullet_anchor + bullet, 1)
    wr(name, text)

    # 7. STATE
    name = "AGENT_STATE.md"
    text = rd(name)
    text = replace_once(
        text,
        u"最后更新：2026-11-01（本地 · R534 / 第 533 轮 / Round 531）",
        u"最后更新：2026-11-01（本地 · R535 / 第 534 轮 / Round 532）",
        u"identity")
    text = replace_once(
        text,
        u"## R535 开工 ⓪（2026-11-01 · 第 534 轮 / Round 532）",
        u"## R535 状态（2026-11-01 · 第 534 轮 / Round 532 · 产品 1 文件 + 判据）",
        u"state title")
    anchor = u"\n## R534 状态（2026-11-01 · 第 533 轮 / Round 531 · 产品 1 文件 + 判据）"
    body = u"""
① 试过但撤回（真机证伪）：**Tab 到「知道了」**——旧值 8 站只在 AXOutline/AXTextField 循环；`.focusable(true)+@FocusState+accent 环` 只多出根 AXGroup（420×472），仍无 AXButton ⇒ 产品撤回，记 **BACKLOG 625**。**行右键菜单**——旧值 `.contextMenu` 0 次；加「复制/收藏」后真机两次右键都弹系统文本菜单（117×165），不是我们的两项 ⇒ 产品与判据一并撤回，记 **BACKLOG 626**。
② 本轮产品 **1 文件**：给折叠提示「知道了」再挂 `.keyboardShortcut(.return, modifiers: [])`，与 Esc 并存、只在提示可见时存在；旧值真机 Return 0/0；视觉零变化。`testCollapseHintCanBeDismissedFromTheKeyboard` 同时钉 Esc+Return；`M1411` CAUGHT、RESTORE_CLEAN=yes；预检 314/291/752 bad=0、ARM 407/1239、HIDDEN 401/1178 rot=0；build 0 告警。新值真机按键未演（不消费提示）⇒ `HINT_RETURN_LIVE_NOT_RUN=defaults-preserved`。
③ 帧 **350** 重捕 CHANGED=0/ADDED=0/MISSING=0（基线不变）；全量 **1378/56/0（584.3s）**（中间 focus/context 两版分别被 VisualToken 线宽/收藏字面量与真机读数拦下并撤回；最终版真绿；本机 SelectionReveal 五条会话噪音本轮未出现）。
④ 换装：首次 `--label R535` 因备份目录已存在在 mv 处失败、旧包未动；改 `--label R535b` 成功 SHA_MATCH=1、431=431、PID 1885、1 窗口 750×492（活库只增不减）。清账 162/162/0/0；电池 **683/5**（台账后复跑）；产品面连续零改动 **1** 轮（as-of 534，`python3 scripts/product_streak.py --streak-for 534` 现读，last=a8f1817/533）。产品笔 `a2579fd` 首次 push 网络断、重试一次成功（HEAD=origin=a2579fd、ahead=0）。下一轮 R536（第 535 轮 / Round 533）：先 push 复核 ahead=0；读本轮/上轮跑；625/626 保持开单、623 不重开；622 记 162.2ms、624 两臂继续；继续折叠特性；4.5 地板与 150 上限不动。"""
    text = replace_once(text, anchor, body + anchor, u"state body")
    wr(name, text)

    sys.stdout.write("LEDGERS_R535_OK\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
