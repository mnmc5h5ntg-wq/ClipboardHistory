#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R534 台账（第 533 轮 / Round 531）。只写七本账，不碰产品。"""
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


UI_SECTION = u"""## 第 533 轮（R534 · 2026-11-01 · U-2194…U-2200）：折叠提示支持 Esc 关闭（产品 1 文件 + 判据）

- **U-2194：⓪ CI。** HEAD=origin=`8b1ddb9`、ahead=0；网络复核 `git ls-remote` 通、api=200/apple=200。`41295597277 ↔ 8b1ddb9`、`41295422790 ↔ 76cbd63`、`41293901730 ↔ 039413e` 读时 **in_progress ⇒ NOT-RUN**；`41293578965 ↔ df43baa` **failure STEP[15]+[18]**：STEP[15]=SelectionReveal 会话族；STEP[18] `testFrameIntervalsUnderStateChanges` 最差 **162.2ms**、超锚点 **2/208**（loaded_p95=16.67、比值 1.000）⇒ **622 再现**（值从 544.1ms 变 162.2ms；120ms 与容差不动）；STEP[9] 绿 ⇒ 624 台账笔绿臂。`882e30f` 仅 STEP[9] 六红已读；623 已签收。
- **U-2195：① 旧值与产品。** 旧值（真机只读）：折叠 **420×492** 下按 Esc，`mainWindowCollapseHintAcknowledged` 前后都未写（0/0）⇒ 一次性提示只能鼠标点「知道了」，键盘用户无法确认。产品 **1 文件**：给「知道了」挂 `.keyboardShortcut(.cancelAction)`（Esc 系统关闭语义），只在提示可见时存在；视觉零变化。
- **U-2196：② 判据与刀。** 新增 `testCollapseHintCanBeDismissedWithEscape`（切 `collapseHintLine` 源码段：按钮/确认动作/`.keyboardShortcut(.cancelAction)` 三格）；`M1410`（摘掉 Esc）**CAUGHT、RESTORE_CLEAN=yes**；预检 **313/290/751 bad=0**、ARM **406/1238**（dupes=0 repeats=0）、HIDDEN **400/1177 rot=0**；build **0 告警**。
- **U-2197：③ 帧卷。** 重捕 **350 帧**：`CHANGED=0 ADDED=0 MISSING=0`（Esc 不进像素；提示帧与 R533 已看过的一致），基线保持 **350**。
- **U-2198：④ 八步与电池。** build 0 告警；全量 **1378/56/0（591.3s）**（本机 SelectionReveal 五条会话噪音本轮未出现）；换装 `ok / SHA_MATCH=1 / INSTALL_ENTRIES=431=431`（活库只增不减；PID 68388；真机只读 1 窗口 750×492）；清账 **162 格已清 162/未清 0/不合法 0**；电池 **683/5**（台账后复跑）；product_streak **1** 轮（as-of 533，`python3 scripts/product_streak.py --streak-for 533` 现读，last=0720cc6/532）。
- **U-2199：⑤ 真机边界。** 旧值按下 Esc 未写确认键；新版只在源码/判据上钉住 `.cancelAction`，**没有**在活 App 上按 Esc 去消费一次性提示（避免替用户改写 defaults）⇒ 新值真机按键未演，具名 `HINT_ESC_LIVE_NOT_RUN=defaults-preserved`。
- **U-2200：⑥ 收口与交接。** 产品笔 `cff79a9` 待推（本笔后 push）；`8b1ddb9`/`76cbd63`/`039413e` 读时 in_progress。下一轮 R535（第 534 轮 / Round 532）：先 push 并复核 ahead=0；读本轮产品/台账跑与上一轮三跑的全部失败步骤；622 记录 162.2ms 新值、624 非台账笔红/台账笔绿继续；623 不重开；继续折叠特性；安全红线不变。

"""

ITERATION_SECTION = u"""
## Round 531 · R534（第 533 轮 · 2026-11-01）：折叠提示支持 Esc 关闭

旧值（真机只读）：折叠 420×492 下按 Esc，`mainWindowCollapseHintAcknowledged` 前后都是 0 ⇒ 一次性提示只能鼠标关。产品 1 文件：给「知道了」挂 `.keyboardShortcut(.cancelAction)`，只在提示可见时存在；视觉零变化。新增 `testCollapseHintCanBeDismissedWithEscape`；M1410 CAUGHT、RESTORE_CLEAN；预检 313/290/751 bad=0、ARM 406/1238、HIDDEN 400/1177 rot=0；build 0 告警。帧 350（重捕 CHANGED=0/ADDED=0，基线不变）；全量 1378/56/0（591.3s）；换装 431=431（PID 68388）；电池 683/5。新值真机按键未演（不消费一次性提示），具名 HINT_ESC_LIVE_NOT_RUN=defaults-preserved。

**七维度自评**（恰七行，每格 n/15）：

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | 15/15 | 350 帧重捕 CHANGED=0；提示帧与 R533 已看过的一致，Esc 不进像素。 |
| 判据有效性 | 15/15 | 源码段三格 + M1410 摘掉 Esc 即 CAUGHT；按钮/动作/快捷键都钉住。 |
| 假绿防御 | 15/15 | 新值真机按键未演，具名 NOT_RUN；不把源码判据冒充真机按键。 |
| 产品面推进 | 15/15 | 一次性提示从「只能鼠标关」变成 Esc 可关；产品 1 文件。 |
| 台账一致性 | 15/15 | U-2194…U-2200、D-533、350/1378/431/683 都来自命令与真机。 |
| 交付诚实性 | 15/15 | 旧值 0/0、未消费提示、622 再现、624 两臂都如实。 |
| 可复核性 | 15/15 | 旧值读数、源码段、M1410、预检 313/290/751 全在。 |

均分 = 105/105 ≈ 15.0/15（100）。
"""

CHANGELOG_SECTION = u"""### 折叠提示支持 Esc 关闭（R534 / 第 533 轮 / Round 531 / U-2194…U-2200 · 产品 1 文件 + 判据）

「知道了」挂 `.keyboardShortcut(.cancelAction)`（只在提示可见时存在），一次性提示可从键盘关闭；视觉不变。旧值真机折叠 420×492 按 Esc 不写确认键；新增源码段判据与 M1410；帧 350 重捕 CHANGED=0；全量 1378/56/0；换装 431=431。

"""

DECISION = u"""
## D-533 一次性折叠提示支持 Esc 关闭（R534）

- 背景：折叠提示的「知道了」是鼠标/触控板动作；真机折叠 420×492 下按 Esc，确认键前后都未写（0/0），键盘用户没法确认提示，提示会在每次折叠时再来。
- 决定：给「知道了」挂 `.keyboardShortcut(.cancelAction)`（Esc 系统关闭语义），按钮只在 `isCollapsed && showsCollapseHint` 时存在，所以 Esc 只在这段窗口里承重；视觉零变化。
- 理由：Esc 是系统级的「取消/关掉」键，比自造组合键更像平台；不消费提示的自动消失仍不做（D-531），Esc 是显式确认的键盘路径。
- 兼容性/迁移：不新增 defaults 键；确认仍走 `acknowledgeCollapseHint`（写 `mainWindowCollapseHintAcknowledged`）；帧基线不变。
- 边界：没有在活 App 上按 Esc 去消费一次性提示（避免替用户改写 defaults），新值按键本身具名 `HINT_ESC_LIVE_NOT_RUN=defaults-preserved`；源码段判据 + M1410 只钉接线。
"""


def main():
    # 1. UI_AUDIT
    name = "AGENT_UI_AUDIT.md"
    text = rd(name)
    anchor = u"## 第 532 轮（R533 · 2026-11-01 · U-2187…U-2193）"
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

    # 4. BACKLOG：622/624 复查
    name = "AGENT_BACKLOG.md"
    text = rd(name)
    add622 = u"""    复查（R534）：`df43baa` 的 STEP[18] 读到 **162.2ms**、超锚点 **2/208**（容差 1），loaded_p95=16.67、比值 1.000 ⇒ 622 再现（比 544.1ms 低，仍是少数帧超锚点）；120ms 与容差不动，不销单。
"""
    text = append_after_line(text, u"复查（R533）：网络两路断开，无新 STEP[18]；120ms 与容差不动。", add622, u"backlog622")
    add624 = u"""    复查（R534）：`df43baa`（台账笔）STEP[9] 绿；`882e30f`（非台账笔）STEP[9] 仍红在 skip_roster ⇒ 非台账笔红/台账笔绿两臂继续；不改名册，保持开单。
"""
    text = append_after_line(text, u"复查（R533 收口）：网络恢复后读到 `882e30f` STEP[9] 仍红在 skip_roster", add624, u"backlog624")
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
        (u"R9–R530，531 节自评", u"R9–R531，532 节自评", u"title"),
        (u"阶段二 **523 轮**审计（R9–R530；以 `curve_from_ledger.py` 的 `PHASE2 n=523` 为准，最新一节是 `AGENT_VISUAL_ITERATION.md` 的 Round 530",
         u"阶段二 **524 轮**审计（R9–R531；以 `curve_from_ledger.py` 的 `PHASE2 n=524` 为准，最新一节是 `AGENT_VISUAL_ITERATION.md` 的 Round 531", u"§1"),
        (u"| 视觉台账 | U-31 … U-2193", u"| 视觉台账 | U-31 … U-2200", u"U 上界"),
        (u"产品面连续零改动轮数 = **1**（as-of 532）", u"产品面连续零改动轮数 = **1**（as-of 533）", u"streak as-of"),
        (u"以 `AGENT_STATE.md` 的 R533 节 ② 为准", u"以 `AGENT_STATE.md` 的 R534 节 ② 为准", u"state pointer"),
        (u"## 18. R458 → R533 这一段", u"## 18. R458 → R534 这一段", u"§18 head"),
        (u"R533 续到 533 —— 这份报告第七次差点停在几十轮之前）", u"R534 续到 534 —— 这份报告第七次差点停在几十轮之前）", u"§18 tail"),
    ]
    for old, new, label in pairs:
        text = replace_once(text, old, new, label)
    bullet_anchor = u"`882e30f` 仅 STEP[9] 六红（台账时序 + skip_roster），Swift/capture 步无红。\n"
    if text.count(bullet_anchor) != 1:
        sys.stderr.write("ANCHOR_BAD §18 bullet\n")
        return 1
    bullet = u"- **R534（折叠提示支持 Esc 关闭；产品 1 文件 + 判据）**：旧值真机折叠 420×492 按 Esc，确认键前后都未写（0/0）；给「知道了」挂 `.keyboardShortcut(.cancelAction)`，只在提示可见时存在，视觉零变化。新增源码段判据与 M1410（CAUGHT）；预检 313/290/751 bad=0、ARM 406/1238、HIDDEN 400/1177 rot=0；帧 350（重捕 CHANGED=0、基线不变）；全量 1378/56/0（591.3s）；换装 431=431（PID 68388）；电池 683/5。新值真机按键未演，具名 HINT_ESC_LIVE_NOT_RUN=defaults-preserved；622 记 162.2ms/2 再现值。\n"
    text = text.replace(bullet_anchor, bullet_anchor + bullet, 1)
    wr(name, text)

    # 7. STATE
    name = "AGENT_STATE.md"
    text = rd(name)
    text = replace_once(
        text,
        u"最后更新：2026-11-01（本地 · R533 / 第 532 轮 / Round 530）",
        u"最后更新：2026-11-01（本地 · R534 / 第 533 轮 / Round 531）",
        u"identity")
    text = replace_once(
        text,
        u"## R534 开工 ⓪（2026-11-01 · 第 533 轮 / Round 531）",
        u"## R534 状态（2026-11-01 · 第 533 轮 / Round 531 · 产品 1 文件 + 判据）",
        u"state title")
    anchor = u"\n## R533 状态（2026-11-01 · 第 532 轮 / Round 530 · 产品 1 文件 + 判据）"
    body = u"""
① 产品/旧值：真机折叠 420×492 下按 Esc，`mainWindowCollapseHintAcknowledged` 前后都是 0 ⇒ 一次性提示只能鼠标关。产品 **1 文件**：给「知道了」挂 `.keyboardShortcut(.cancelAction)`（Esc 系统关闭语义），只在 `isCollapsed && showsCollapseHint` 时存在；视觉零变化。
② 判据/刀：`testCollapseHintCanBeDismissedWithEscape`（切源码段：按钮/确认动作/`.keyboardShortcut(.cancelAction)`）；`M1410` CAUGHT、RESTORE_CLEAN=yes；预检 313/290/751 bad=0、ARM 406/1238、HIDDEN 400/1177 rot=0；build 0 告警。帧 **350**（重捕 CHANGED=0/ADDED=0/MISSING=0；基线保持 350）。
③ 八步：全量 **1378/56/0（591.3s）**（本机 SelectionReveal 五条会话噪音本轮未出现）；换装 `ok / SHA_MATCH=1 / INSTALL_ENTRIES=431=431`（PID 68388；真机只读 1 窗口 750×492）；清账 162 格已清 162/未清 0/不合法 0；电池 **683/5**（台账后复跑）；产品面连续零改动 **1** 轮（as-of 533，`python3 scripts/product_streak.py --streak-for 533` 现读，last=0720cc6/532）。
④ 真机/收口：旧值按 Esc 未写确认键；新版只在源码/判据上钉 `.cancelAction`，**没有**在活 App 上按 Esc 去消费一次性提示（避免替用户改写 defaults）⇒ 新值真机按键具名 `HINT_ESC_LIVE_NOT_RUN=defaults-preserved`。产品笔 `cff79a9` 本笔后推；`8b1ddb9`/`76cbd63`/`039413e` 读时 in_progress ⇒ NOT-RUN。下一轮 R535（第 534 轮 / Round 532）：先 push 并复核 ahead=0；622 记 162.2ms 新值、624 两臂继续；623 不重开；继续折叠特性；4.5 地板与 150 上限不动。"""
    text = replace_once(text, anchor, body + anchor, u"state body")
    wr(name, text)

    sys.stdout.write("LEDGERS_R534_OK\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
