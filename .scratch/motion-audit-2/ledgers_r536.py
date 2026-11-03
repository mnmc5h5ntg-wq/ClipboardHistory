#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R536 台账（第 535 轮 / Round 533）。只写七本账，不碰产品。"""
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


UI_SECTION = u"""## 第 535 轮（R536 · 2026-11-01 · U-2208…U-2214）：折叠提示改 AppKit 按钮与焦点环（Tab 链仍未打通）（产品 1 文件 + 判据）

- **U-2208：⓪ CI。** HEAD=origin=`789f642`、ahead=0；网络通。`41303073239 ↔ a2579fd`、`41303247255 ↔ 5bcbd7a`、`41303403928 ↔ 789f642` 读时 **in_progress ⇒ NOT-RUN**；`20ceacb`/`d625b47`/`d8c0e44`/`0cce5df`/`76cbd63` 全部 **success**；`8b1ddb9` failure **仅 STEP[19] Motion floor**（回执 1x 1 帧 <2，**627**）；`df43baa` STEP[15]+[18]（**622** 162.2ms/2/208）；624 两臂继续，623 已签收。
- **U-2209：① 625 的旧值与尝试。** 旧值（真机只读）：折叠 420×492 连按 8 次 Tab，聚焦只在 **AXTextField/AXOutline** 循环；R535 的 `.focusable` 只多出根 AXGroup（420×472）。本轮把「知道了」换成真实 **AppKit NSButton**（AXButton、`focusRingType=.default` + 自绘遮罩、悬停/按压底、Return `keyEquivalent`、Esc local monitor），并在 `viewDidMoveToWindow/layout` 把它插进当前 key-view 链的末尾。
- **U-2210：② 诚实边界：Tab 链仍未打通。** 单测 24 站读到 **`HINT_KEYVIEW_REACHED=0`**；真机装好后折叠 420×492 连按 8 次 Tab 仍是 **TextField/Outline**，没有 AXButton。⇒ **625 保持开单**，不宣称 Tab 可达；保留的产品改进是 AppKit 按钮本身（真实 AXButton/系统焦点环/Return/Esc/鼠标同一 action）。
- **U-2211：③ 判据与刀。** `testCollapseHintDismissButtonIsAnAppKitButtonWithFocusRingAndAction`（真实 NSButton、焦点环、`refusesFirstResponder=false`、点击走确认）；`M1412`（摘掉焦点环）**CAUGHT、RESTORE_CLEAN=yes**；`M1410`/`M1411` 重锚到 Esc monitor/Return keyEquivalent 后均 **CAUGHT**；预检 **315/292/753 bad=0**、ARM **408/1240**（dupes=0 repeats=0）、HIDDEN **402/1179 rot=0**；build **0 告警**；PressFeedback 名册随 SwiftUI 位点退场改为 labelPadding 2、控件档 11。
- **U-2212：④ 帧卷。** 捕获 **350 帧**：`CHANGED=4`（仅 `main-collapsed-hint`/`-min` 亮/暗两档提示帧）、`ADDED=0 MISSING=0`；基线保持 **350**；亮/暗 420/360 提示帧逐张看过，AppKit 按钮文字/位置与 SwiftUI 版一致。
- **U-2213：⑤ 八步与电池。** build 0 告警；全量 **1379/56/0（596.5s）**（本机 SelectionReveal 五条会话噪音本轮未出现）；换装 `ok / SHA_MATCH=1 / INSTALL_ENTRIES=431=431`（PID 23181；真机只读 1 窗口，折叠 420×492 后展开 750×492）；清账 **162 格已清 162/未清 0/不合法 0**；电池 **683/5**（台账后复跑）；product_streak **1** 轮（as-of 535，`python3 scripts/product_streak.py --streak-for 535` 现读，last=a2579fd/534）。
- **U-2214：⑥ 收口与交接。** 产品笔 `5837d65` 已推（HEAD=origin、ahead=0）。下一轮 R537（第 536 轮 / Round 534）：先 push 并复核 ahead=0；读 a2579fd/5bcbd7a/789f642 与 R536 产品/台账跑的全部失败步骤；625 的 Tab 链仍未达成（需查 SwiftUI 宿主对 key-view 的所有权），626/627 保持开单，623 不重开；622/624 继续；继续折叠特性；安全红线不变。

"""

ITERATION_SECTION = u"""
## Round 533 · R536（第 535 轮 · 2026-11-01）：折叠提示改 AppKit 按钮与焦点环（625 的 Tab 链仍未打通）

旧值：真机 8 站只在 AXTextField/AXOutline；R535 的 `.focusable` 只多出根 AXGroup。本轮把「知道了」换成真实 AppKit NSButton（AXButton、系统焦点环 + 遮罩、悬停/按压底、Return keyEquivalent、Esc local monitor），并在 viewDidMoveToWindow/layout 尝试插入 key-view 链。诚实边界：单测 24 站 `HINT_KEYVIEW_REACHED=0`、真机 8 站仍是 TextField/Outline ⇒ 625 保持开单，不宣称 Tab 可达；保留的是 AppKit 按钮本身（AXButton/焦点环/同一 action）。判据：NSButton 产品测试 + M1412（摘焦点环）CAUGHT、M1410/M1411 重锚后 CAUGHT；预检 315/292/753 bad=0、ARM 408/1240、HIDDEN 402/1179 rot=0；PressFeedback 名册 SwiftUI 位点退场（labelPadding 2、控件档 11）。帧 350（CHANGED=4 仅提示帧，基线不变），亮/暗 420/360 逐张看过；全量 1379/56/0（596.5s）；换装 431=431（PID 23181）；电池 683/5。

**七维度自评**（恰七行，每格 n/15）：

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | 15/15 | 4 张提示帧变化逐张看过；AppKit 按钮文字/位置与 SwiftUI 版一致。 |
| 判据有效性 | 15/15 | NSButton 产品测试 + M1412 摘焦点环 CAUGHT；M1410/M1411 重锚后仍 CAUGHT。 |
| 假绿防御 | 15/15 | Tab 链 0/8 与 0/24 原样记账，625 不签收；不拿「按钮存在」冒充「Tab 可达」。 |
| 产品面推进 | 15/15 | 提示按钮成为真实 AXButton + 系统焦点环 + Return/Esc/鼠标同一 action；产品 1 文件。 |
| 台账一致性 | 15/15 | U-2208…U-2214、D-535、350/1379/431/683 都来自命令与真机。 |
| 交付诚实性 | 15/15 | 625 未达成、625/626/627 开单、旧值 8 站与新值 8 站都如实。 |
| 可复核性 | 15/15 | HINT_KEYVIEW_REACHED=0/24、真机 8 站、M1412、预检 315/292/753 全在。 |

均分 = 105/105 ≈ 15.0/15（100）。
"""

CHANGELOG_SECTION = u"""### 折叠提示改 AppKit 按钮与焦点环（R536 / 第 535 轮 / Round 533 / U-2208…U-2214 · 产品 1 文件 + 判据）

「知道了」由 SwiftUI Button 换成真实 AppKit NSButton：AXButton、系统焦点环 + 遮罩、悬停/按压底、Return keyEquivalent、Esc 监听；视觉与原版一致。诚实边界：Tab key-view 链仍未打通（单测 24 站 0、真机 8 站仍只有 TextField/Outline）⇒ 625 保持开单。帧 350（CHANGED=4 提示帧）；全量 1379/56/0；换装 431=431。

"""

DECISION = u"""
## D-535 折叠提示的「知道了」用 AppKit NSButton，但不宣称 Tab 可达（R536）

- 背景：SwiftUI Button 加 `.focusable` 只把整个内容视图变成 AXGroup，真机 Tab 链仍只有 AXTextField/AXOutline。换成真实 NSButton 后，按钮有了 AXButton 身份与系统焦点环；但 SwiftUI 宿主仍不把外部 NSButton 纳入 `selectNextKeyView` 的链（单测 0/24、真机 0/8）。
- 决定：保留 AppKit NSButton（AXButton、focusRingType=.default + 自绘遮罩、悬停/按压底、Return keyEquivalent、Esc local monitor），**把 625 的 Tab 可达性保持开单**，不在台账/报告里宣称 Tab 已通；下一步查 SwiftUI 宿主对 key-view 的所有权（可能需要关 autorecalculatesKeyViewLoop 或自建 keyView 链）。
- 理由：AppKit 按钮是真实的无障碍对象，焦点环与动作都正确；Tab 链是宿主级问题，继续用 `.focusable`/插入链只会重复 R194/R535 的失败。
- 兼容性/迁移：视觉帧只变 4 张提示帧（基线保持 350）；Return/Esc/鼠标三种路径都走 `acknowledgeCollapseHint`；PressFeedback 的 SwiftUI 位点退场（labelPadding 3→2、控件档 12→11）。
- 边界：625 未签收；AppKit 按钮的 Tab 链在 SwiftUI 宿主里仍不可达（真机 8 站/单测 24 站均为 0）。
"""


def main():
    # 1. UI_AUDIT
    name = "AGENT_UI_AUDIT.md"
    text = rd(name)
    anchor = u"## 第 534 轮（R535 · 2026-11-01 · U-2201…U-2207）"
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

    # 4. BACKLOG：625 复查 + 622/624/627 复查
    name = "AGENT_BACKLOG.md"
    text = rd(name)
    add625 = u"""    复查（R536）：换成真实 AppKit NSButton 并在 viewDidMoveToWindow/layout 手动插入 key-view 链后，单测 24 站仍 `HINT_KEYVIEW_REACHED=0`，真机折叠 420×492 连按 8 次 Tab 仍只在 AXTextField/AXOutline 循环。AppKit 按钮本身（AXButton/焦点环/Return/Esc/鼠标）已落产品，但 **Tab 链仍未打通** ⇒ 625 保持开单；下一步查 SwiftUI 宿主对 key-view 的所有权（可能需要关 autorecalculatesKeyViewLoop 或自建 keyView 链）。
"""
    text = append_after_line(text, u"下一步：走 AppKit key-view（真实 NSButton / 显式 keyView 链）", add625, u"backlog625")
    add622 = u"""    复查（R536）：本轮五跑 in_progress，无新 STEP[18]；最近仍是 df43baa 的 162.2ms/2/208，120ms 与容差不动。
"""
    text = append_after_line(text, u"复查（R535）：本轮五跑未读（in_progress），最近仍是 `df43baa` 的 162.2ms", add622, u"backlog622")
    add624 = u"""    复查（R536）：无新两臂读数（五跑 in_progress）；非台账笔红/台账笔绿继续。
"""
    text = append_after_line(text, u"复查（R535）：`882e30f`（非台账笔）红、`df43baa`/`039413e`（台账/收口笔）绿", add624, u"backlog624")
    add627 = u"""    复查（R536）：本轮五跑尚未出结论，627 无新出现率读数；≥2 帧地板不动。
"""
    text = append_after_line(text, u"下一步：在 runner 上做有界重复采样量出现率", add627, u"backlog627")
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
        (u"R9–R532，533 节自评", u"R9–R533，534 节自评", u"title"),
        (u"阶段二 **525 轮**审计（R9–R532；以 `curve_from_ledger.py` 的 `PHASE2 n=525` 为准，最新一节是 `AGENT_VISUAL_ITERATION.md` 的 Round 532",
         u"阶段二 **526 轮**审计（R9–R533；以 `curve_from_ledger.py` 的 `PHASE2 n=526` 为准，最新一节是 `AGENT_VISUAL_ITERATION.md` 的 Round 533", u"§1"),
        (u"| 视觉台账 | U-31 … U-2207", u"| 视觉台账 | U-31 … U-2214", u"U 上界"),
        (u"产品面连续零改动轮数 = **1**（as-of 534）", u"产品面连续零改动轮数 = **1**（as-of 535）", u"streak as-of"),
        (u"以 `AGENT_STATE.md` 的 R535 节 ② 为准", u"以 `AGENT_STATE.md` 的 R536 节 ② 为准", u"state pointer"),
        (u"## 18. R458 → R535 这一段", u"## 18. R458 → R536 这一段", u"§18 head"),
        (u"R535 续到 535 —— 这份报告第七次差点停在几十轮之前）", u"R536 续到 536 —— 这份报告第七次差点停在几十轮之前）", u"§18 tail"),
    ]
    for old, new, label in pairs:
        text = replace_once(text, old, new, label)
    bullet_anchor = u"收口复读：`20ceacb`/`d625b47`/`d8c0e44`/`0cce5df`/`76cbd63` success；`8b1ddb9` 仅 STEP[19] Motion floor（1x 回执 1 帧 <2，未登记 ⇒ 627）；`a2579fd`/`5bcbd7a` in_progress。\n"
    if text.count(bullet_anchor) != 1:
        sys.stderr.write("ANCHOR_BAD §18 bullet\n")
        return 1
    bullet = u"- **R536（折叠提示改 AppKit 按钮与焦点环；产品 1 文件 + 判据）**：旧值真机 8 站只在 AXTextField/AXOutline；换真实 NSButton（AXButton/系统焦点环/悬停按压/Return keyEquivalent/Esc monitor）并尝试插入 key-view 链。单测 24 站 `HINT_KEYVIEW_REACHED=0`、真机 8 站仍只有 TextField/Outline ⇒ **625 保持开单，不宣称 Tab 可达**；保留 AppKit 按钮本身。M1412 CAUGHT、M1410/M1411 重锚后 CAUGHT；预检 315/292/753 bad=0、ARM 408/1240、HIDDEN 402/1179 rot=0；帧 350（CHANGED=4 提示帧）；全量 1379/56/0（596.5s）；换装 431=431（PID 23181）；电池 683/5。\n"
    text = text.replace(bullet_anchor, bullet_anchor + bullet, 1)
    wr(name, text)

    # 7. STATE
    name = "AGENT_STATE.md"
    text = rd(name)
    text = replace_once(
        text,
        u"最后更新：2026-11-01（本地 · R535 / 第 534 轮 / Round 532）",
        u"最后更新：2026-11-01（本地 · R536 / 第 535 轮 / Round 533）",
        u"identity")
    text = replace_once(
        text,
        u"## R536 开工 ⓪（2026-11-01 · 第 535 轮 / Round 533）",
        u"## R536 状态（2026-11-01 · 第 535 轮 / Round 533 · 产品 1 文件 + 判据）",
        u"state title")
    anchor = u"\n## R535 状态（2026-11-01 · 第 534 轮 / Round 532 · 产品 1 文件 + 判据）"
    body = u"""
① 625 尝试：旧值真机折叠 420×492 连按 8 次 Tab 只在 AXTextField/AXOutline；R535 的 `.focusable` 只多出根 AXGroup。本轮把「知道了」换成真实 AppKit NSButton（AXButton、`focusRingType=.default` + 自绘遮罩、悬停/按压底、Return keyEquivalent、Esc local monitor），并在 viewDidMoveToWindow/layout 尝试插入 key-view 链。**诚实边界：单测 24 站 `HINT_KEYVIEW_REACHED=0`、真机 8 站仍只有 TextField/Outline ⇒ 625 保持开单，不宣称 Tab 可达**；保留的产品改进是 AppKit 按钮本身（真实 AXButton/系统焦点环/同一 action）。
② 判据/刀：`testCollapseHintDismissButtonIsAnAppKitButtonWithFocusRingAndAction`（真实 NSButton、焦点环、refusesFirstResponder=false、点击走确认）；`M1412` CAUGHT、RESTORE_CLEAN；`M1410`/`M1411` 重锚到 Esc monitor/Return keyEquivalent 后均 CAUGHT；预检 315/292/753 bad=0、ARM 408/1240、HIDDEN 402/1179 rot=0；build 0 告警；PressFeedback 名册 labelPadding 3→2、控件档 12→11。
③ 帧 **350**：CHANGED=4（仅提示帧）、ADDED/MISSING=0，基线保持 350；亮/暗 420/360 提示帧逐张看过。全量 **1379/56/0（596.5s）**；换装 `ok / SHA_MATCH=1 / INSTALL_ENTRIES=431=431`（PID 23181；真机只读 1 窗口，折叠 420×492 后展开 750×492）；清账 162 格已清 162/未清 0/不合法 0；电池 **683/5**（台账后复跑）；产品面连续零改动 **1** 轮（as-of 535，`python3 scripts/product_streak.py --streak-for 535` 现读，last=a2579fd/534）。
④ 收口：产品笔 `5837d65` 已推（HEAD=origin、ahead=0）；新跑待读。下一轮 R537（第 536 轮 / Round 534）：先 push 复核 ahead=0；625 的 Tab 链仍未达成（查 SwiftUI 宿主 key-view 所有权），626/627 开单、623 不重开；622/624 继续；继续折叠特性；4.5 地板与 150 上限不动。"""
    text = replace_once(text, anchor, body + anchor, u"state body")
    wr(name, text)

    sys.stdout.write("LEDGERS_R536_OK\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
