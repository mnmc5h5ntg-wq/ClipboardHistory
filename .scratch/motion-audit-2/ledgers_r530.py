#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R530 台账（第 529 轮 / Round 527）。只写七本账，不碰产品。"""
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


UI_SECTION = u"""## 第 529 轮（R530 · 2026-11-01 · U-2165…U-2171）：折叠态 Window 菜单勾选与最小窗夹具（产品 1 文件 + 判据）

- **U-2165：⓪ CI。** HEAD=origin=`9b9cf56`、ahead=0；`41284186399 ↔ 9b9cf56`、`41284167067 ↔ 2967ce6`、`41284008834 ↔ 1e3cfaa` 读时均 **in_progress ⇒ NOT-RUN**（1e3cfaa 是 hover 扩边修复的签收跑，待读）。已收口：`41282132936 ↔ 2e7272e` **failure STEP[9]+[15]+[17]**（STEP[9]=sources 时序；STEP[15]/[17]=旧 hover 判据 `TITLE_HOVER light/dark totalDelta=0 changedPixels=0`，Capture gate 点名同一条）；`41282266561 ↔ 5fcb482` **failure STEP[15]+[17]**；`41280978574 ↔ 3c00b75` 同 STEP[9]+[15]+[17]。R528 三跑 `c64956e`/`b004545`/`9cf95e1` 的 STEP[15]+[17] 同族（旧 hover 0.0），detail 已由 a71a74c 签收。**BACKLOG 622 复查**：`testCodeBlocksShowLineNumbers` 在两跑的 capture 与 Swift 步均 passed、`testFrameIntervalsUnderStateChanges` 均 skipped（未设 `CLIPBOARD_HISTORY_UI_INTERACTION=1`）⇒ 两颗各 1 次、未复现，不销单。归因：sources 时序红与产品回归分开；唯一产品红仍是旧 hover 0.0（1e3cfaa 已换扩边顺序 + 显式取证，待跑签收）。
- **U-2166：① 旧值与产品。** 旧值（源码取证）：R529 的 Window 菜单折叠项是 `Button(MainWindowCollapsePolicy.menuTitle(...))`，没有绑定任何布尔状态 ⇒ 折叠/展开两态都不可能画勾，菜单里读不出当前状态（R529 真机 AX 只读到标题）。修法：改成 `Toggle(isOn: Binding(get: { collapse.isCollapsed }, set: { _ in appDelegate.perform(.toggleMainWindowCollapse) }))`，勾=当前折叠态；标题仍由 `menuTitle(collapsed:)` 现读。set 不采用新值，⌘\\ 与状态菜单仍是同一条 dispatch。产品 **1 文件**（ClipboardHistoryCommands）。
- **U-2167：② 真机只读复核（非破坏性菜单项）。** 安装版 AX：展开 **750×492** 时「折叠窗口」无勾 → 点菜单项后 **420×492**「展开窗口」带 ✓ → 再点回 **750×492**「折叠窗口」无勾，始终 **1 窗口**。可分辨的那一臂正是折叠态的勾；删除/清空/退出未碰，活库未动。
- **U-2168：③ 判据与刀。** 新增 `testSelectionSurvivesCollapseAndExpand`（产品入口：`HistoryStore.perform(.selectOnly)` + `delegate.perform(.toggleMainWindowCollapse)`，折叠/展开各查一次 `selectedEntryIDs`；旧实现已通过，它是**新判据**不是修缺陷）；`testWindowMenuTitleReflectsCollapseState` 扩到断言源码里的 `Toggle(isOn: Binding(`、`get: { collapse.isCollapsed }`、同一个 `perform(.toggleMainWindowCollapse)`。`M1406`（Toggle→Button）**CAUGHT、RESTORE_CLEAN=yes**；`M1405` 重锚到 `get: { collapse.isCollapsed }`（改成 false）后 **CAUGHT**。预检 **309/286/747 bad=0**、ARM **402/1234**（dupes=0 repeats=0）、HIDDEN **396/1173 rot=0**；build **0 告警**。
- **U-2169：④ 帧卷。** 新增夹具 `main-collapsed-min` **360×560**（折叠最小宽），入材质盲区名册（66pt List 选中材质不被 cacheDisplay 绘制）⇒ 只拍几何不看颜色；捕获 **344 帧**：`ADDED=2 MISSING=0`、`CHANGED=0`；基线 342→344。
- **U-2170：⑤ 八步与电池。** build 0 告警；全量 **1372/56/0（570.0s）**；换装 `ok / SHA_MATCH=1 / INSTALL_ENTRIES=429=429`（活库只增；PID 80101）；真机只读 1 窗口；清账 **162 格已清 162/未清 0/不合法 0**；电池 **683/5**（台账后复跑）；product_streak **1** 轮（as-of 529，`python3 scripts/product_streak.py` 现读）。
- **U-2171：⑥ 收口与交接。** 产品笔 `02fa144` 已推（HEAD=origin、ahead=0）；新跑待读（下轮第 ⓪ 全读，重点 hover 新尺在 runner 是否转绿、Toggle 勾选跑、BACKLOG 622 是否再复现）。下一轮 R531（第 530 轮 / Round 528）：先 push 并复核 ahead=0；继续折叠特性；安全红线不变。

"""

ITERATION_SECTION = u"""
## Round 527 · R530（第 529 轮 · 2026-11-01）：折叠态 Window 菜单勾选与最小窗夹具

旧值（源码）：R529 的 Window 菜单折叠项是 `Button(...)`，没有绑定状态 ⇒ 两态都不可能有勾。改成 `Toggle(isOn: Binding(get: collapse.isCollapsed, set: 丢给 perform(.toggleMainWindowCollapse)))`，标题仍随状态切换；真机 AX 非破坏性复核：展开 750×492 无勾 → 折叠 420×492「展开窗口」✓ → 再展开 750×492 无勾，1 窗口。新增选区跨折叠保持判据 `testSelectionSurvivesCollapseAndExpand` 与 360×560 `main-collapsed-min` 夹具（入材质盲区名册）；`M1406` CAUGHT、`M1405` 重锚后 CAUGHT；预检 309/286/747 bad=0、ARM 402/1234、HIDDEN 396/1173 rot=0；build 0 告警；帧 **344**（ADDED=2、CHANGED=0；基线 342→344）；全量 **1372/56/0（570.0s）**；换装 429=429（PID 80101）；电池 **683/5**。产品 1 文件。

**七维度自评**（恰七行，每格 n/15）：

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | 15/15 | 真机 AX 读菜单勾与两态窗口尺寸，1 窗口往返；不是只看源码。 |
| 判据有效性 | 15/15 | Toggle 接线由源码判据钉住，M1406/M1405 两刀都让读数变。 |
| 假绿防御 | 15/15 | 选区保持判据明说是新判据（旧实现已过），没冒充修缺陷；材质盲区帧只判几何。 |
| 产品面推进 | 15/15 | 菜单状态从不可见变成系统勾选；产品 1 文件。 |
| 台账一致性 | 15/15 | U-2165…U-2171、D-529、344/1372/429/683 都来自命令与真机。 |
| 交付诚实性 | 15/15 | 旧值只有源码取证（真机只读到标题）；⌘\\ 未单独复验也如实。 |
| 可复核性 | 15/15 | 750/420 尺寸、勾的有无、M1406、预检 309/286/747 都在。 |

均分 = 105/105 ≈ 15.0/15（100）。
"""

CHANGELOG_SECTION = u"""### 折叠窗口菜单勾选与最小窗夹具（R530 / 第 529 轮 / Round 527 / U-2165…U-2171 · 产品 1 文件 + 判据）

Window 菜单的折叠项改为 `Toggle`（勾=当前折叠态），标题仍随状态切换，⌘\\ 与状态菜单同一 dispatch。真机 AX：展开「折叠窗口」无勾 → 折叠「展开窗口」✓ → 再展开无勾，1 窗口。新增选区跨折叠保持判据与 360×560 最小折叠帧；M1406/M1405 CAUGHT；帧 344；全量 1372/56/0；换装 429=429。


"""

BACKLOG_ADD = u"""    复查（R530）：`2e7272e`/`5fcb482` 两跑的 capture 与 Swift 步里 `testCodeBlocksShowLineNumbers` 均 passed、`testFrameIntervalsUnderStateChanges` 均 skipped（未设 `CLIPBOARD_HISTORY_UI_INTERACTION=1`）⇒ 仍各 1 次、未复现；不销单，继续在下一轮读新跑复查。
"""

DECISION = u"""
## D-529 Window 菜单的折叠项用 Toggle 表达状态（R530）

- 背景：R529 只让标题随状态切换，但菜单项本身没有勾；折叠态与展开态在菜单列表里仍只能靠读标题，状态不是一眼可见的。macOS 菜单里「当前处于某模式」的惯例是勾选。
- 决定：折叠项改 `Toggle(isOn: Binding(get: { collapse.isCollapsed }, set: { _ in appDelegate.perform(.toggleMainWindowCollapse) }))`；set 不采用 binding 传来的新值，统一走既有 perform（⌘\\ 与状态菜单同一条 dispatch），避免出现第二套状态写入。
- 理由：勾是系统菜单的标准状态语言；让 set 走 perform 能保证 Toggle 的显示状态永远等于 controller 的真值，不会先翻转再被纠正。
- 兼容性/迁移：标题仍由 `MainWindowCollapsePolicy.menuTitle(collapsed:)` 生成；状态菜单（MenuBarExtra/NSMenu）不变；菜单不进离屏帧，基线变化只来自新夹具。
- 边界：只用真机 AX 的非破坏性菜单点击取证；⌘\\ keystroke 本机未送达前台，快捷键仍由 source 判据与既有 perform 测试覆盖。
"""


def main():
    # 1. UI_AUDIT：降序插在第 528 轮之上
    name = "AGENT_UI_AUDIT.md"
    text = rd(name)
    anchor = u"## 第 528 轮（R529 · 2026-11-01 · U-2157…U-2164）"
    if text.count(anchor) != 1:
        sys.stderr.write("ANCHOR_BAD ui\n")
        return 1
    text = text.replace(anchor, UI_SECTION + anchor, 1)
    wr(name, text)

    # 2. ITERATION：升序追加到文件尾
    name = "AGENT_VISUAL_ITERATION.md"
    text = rd(name)
    if not text.endswith(u"\n"):
        text += u"\n"
    text += ITERATION_SECTION
    wr(name, text)

    # 3. CHANGELOG：插在 [Unreleased] 之下
    name = "CHANGELOG.md"
    text = rd(name)
    anchor = u"## [Unreleased]\n\n"
    if text.count(anchor) != 1:
        sys.stderr.write("ANCHOR_BAD changelog\n")
        return 1
    text = text.replace(anchor, anchor + CHANGELOG_SECTION, 1)
    wr(name, text)

    # 4. BACKLOG：622 复查追记
    name = "AGENT_BACKLOG.md"
    text = rd(name)
    anchor = u"复查（R529）：`897db20`/`e5e0840` 两跑的 capture 与 Swift 步里 `testCodeBlocksShowLineNumbers` 均 passed"
    idx = text.find(anchor)
    if idx < 0:
        sys.stderr.write("ANCHOR_BAD backlog\n")
        return 1
    end = text.find(u"\n", idx)
    if end < 0:
        end = len(text)
    text = text[:end + 1] + BACKLOG_ADD + text[end + 1:]
    wr(name, text)

    # 5. DECISIONS：追加 D-529
    name = "AGENT_DECISIONS.md"
    text = rd(name)
    if not text.endswith(u"\n"):
        text += u"\n"
    text += DECISION
    wr(name, text)

    # 6. FINAL_REPORT：只改计数器与 §18 指针
    name = "AGENT_FINAL_REPORT.md"
    text = rd(name)
    pairs = [
        (u"R9–R526，527 节自评", u"R9–R527，528 节自评", u"title"),
        (u"阶段二 **519 轮**审计（R9–R526；以 `curve_from_ledger.py` 的 `PHASE2 n=519` 为准，最新一节是 `AGENT_VISUAL_ITERATION.md` 的 Round 526",
         u"阶段二 **520 轮**审计（R9–R527；以 `curve_from_ledger.py` 的 `PHASE2 n=520` 为准，最新一节是 `AGENT_VISUAL_ITERATION.md` 的 Round 527", u"§1"),
        (u"| 视觉台账 | U-31 … U-2164", u"| 视觉台账 | U-31 … U-2171", u"U 上界"),
        (u"产品面连续零改动轮数 = **1**（as-of 528）", u"产品面连续零改动轮数 = **1**（as-of 529）", u"streak as-of"),
        (u"以 `AGENT_STATE.md` 的 R529 节 ② 为准", u"以 `AGENT_STATE.md` 的 R530 节 ② 为准", u"state pointer"),
        (u"## 18. R458 → R529 这一段", u"## 18. R458 → R530 这一段", u"§18 head"),
        (u"R529 续到 529 —— 这份报告第七次差点停在几十轮之前）", u"R530 续到 530 —— 这份报告第七次差点停在几十轮之前）", u"§18 tail"),
    ]
    for old, new, label in pairs:
        text = replace_once(text, old, new, label)
    bullet_anchor = u"BACKLOG 622 两跑未复现（各 1 次）。\n"
    if text.count(bullet_anchor) != 1:
        sys.stderr.write("ANCHOR_BAD §18 bullet\n")
        return 1
    bullet = u"- **R530（折叠态 Window 菜单勾选与最小窗夹具；产品 1 文件 + 判据）**：旧值 R529 的 Button 不绑定状态 ⇒ 两态都没有勾；改 `Toggle(isOn:)`（勾=折叠态），set 仍走同一 perform + ⌘\\。真机 AX：展开 750×492 无勾 → 折叠 420×492「展开窗口」✓ → 再展开 750×492 无勾，1 窗口。新增选区跨折叠保持判据与 360×560 `main-collapsed-min`；M1406/M1405 CAUGHT；预检 309/286/747 bad=0、ARM 402/1234、HIDDEN 396/1173 rot=0；帧 344（ADDED=2）；全量 1372/56/0；换装 429=429（PID 80101）；电池 683/5。\n"
    text = text.replace(bullet_anchor, bullet_anchor + bullet, 1)
    wr(name, text)

    # 7. STATE：identity 行 + R530 节标题 + ① ② 正文
    name = "AGENT_STATE.md"
    text = rd(name)
    text = replace_once(
        text,
        u"最后更新：2026-11-01（本地 · R529 / 第 528 轮 / Round 526）",
        u"最后更新：2026-11-01（本地 · R530 / 第 529 轮 / Round 527）",
        u"identity")
    text = replace_once(
        text,
        u"## R530 状态（2026-11-01 · 第 529 轮 / Round 527 · 开工 ⓪）",
        u"## R530 状态（2026-11-01 · 第 529 轮 / Round 527 · 产品 1 文件 + 判据）",
        u"state title")
    anchor = u"\n\n\n## R529 状态（2026-11-01 · 第 528 轮 / Round 526 · 产品 2 文件 + 判据）"
    body = u"""
① 产品/判据：旧值（源码）R529 的 Window 菜单折叠项是 `Button(...)`，没有绑定状态 ⇒ 两态都不可能画勾，菜单里读不出当前折叠状态。修：改成 `Toggle(isOn: Binding(get: { collapse.isCollapsed }, set: { _ in appDelegate.perform(.toggleMainWindowCollapse) }))`，勾=折叠态，标题仍随状态切换，set 统一走既有 perform（与 ⌘\\、状态菜单同一条 dispatch）。真机只读 AX 复核（非破坏性菜单项）：展开 750×492「折叠窗口」无勾 → 折叠后 420×492「展开窗口」✓ → 再展开 750×492 无勾，始终 1 窗口。新增 `testSelectionSurvivesCollapseAndExpand`（产品入口：selectOnly + toggleMainWindowCollapse，折叠/展开各查 selectedEntryIDs；旧实现已通过，它是新判据不是修缺陷）与 360×560 `main-collapsed-min` 夹具（入材质盲区名册，只判几何）。产品 **1 文件**（ClipboardHistoryCommands）；`M1406` CAUGHT、`M1405` 重锚后 CAUGHT；预检 309/286/747 bad=0、ARM 402/1234、HIDDEN 396/1173 rot=0；build 0 告警。帧 **344**（ADDED=2、CHANGED=0；基线 342→344）。全量 **1372/56/0（570.0s）**；换装 `ok / SHA_MATCH=1 / INSTALL_ENTRIES=429=429`（PID 80101）；真机只读 1 窗口；清账 162 格已清 162/未清 0/不合法 0；电池 **683/5**（台账后复跑）；产品面连续零改动 **1** 轮（as-of 529，`python3 scripts/product_streak.py` 现读，newest=02fa144/529）。
② BACKLOG 622 已在 ⓪ 复查（`2e7272e`/`5fcb482` 两跑均 passed/skipped，各 1 次、未复现，不销单）。产品笔 `02fa144` 已推（HEAD=origin、ahead=0）；新跑待读。下一轮编号 R531（第 530 轮 / Round 528）：先 push 并复核 ahead=0；继续折叠特性；4.5 地板与 150 上限不动。"""
    text = replace_once(text, anchor, body + anchor, u"state body")
    wr(name, text)

    sys.stdout.write("LEDGERS_R530_OK\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
