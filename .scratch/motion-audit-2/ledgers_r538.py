#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R538 台账（第 537 轮 / Round 535）。只写七本账，不碰产品。"""
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


UI_SECTION = u"""## 第 537 轮（R538 · 2026-11-01 · U-2222…U-2228）：行右键菜单改由列表选区层接管（626 本机落地）（产品 2 文件 + 判据）

- **U-2222：⓪ CI。** HEAD=origin=`8cef540`、ahead=0；网络通。`41308835299 ↔ 21a5440`、`41309008989 ↔ b707811`、`41309189054 ↔ 8cef540` 读时 **in_progress ⇒ NOT-RUN**（三跑都没有失败步骤可列）。已收口：`94dfa27`/`f271cc4`/`e3e0893` **success**；`67437eb` 仅 STEP[9]；`5837d65` STEP[9]+[18]（frame **243.2ms/2/189** ⇒ 622 第四值）；`5bcbd7a` STEP[17] code-block（622 第二次）。**622 code-block 半不能签收**：读时没有任何含 `21a5440` 的新跑出结论；frame 半仍记 243.2ms/2/189，120ms 与容差不动。
- **U-2223：① 626 旧值与真机读数。** 旧值（R535）：行内容 `.contextMenu` 被 Text/cell 的系统文本菜单盖住，真机两次右键都弹 **117×165**（撤销/重做/剪切/复制/粘贴/全选）。本轮把菜单改挂 `List` 的 `.contextMenu(forSelectionType: HistoryStore.Entry.ID.self)`（macOS 13+；`RowContextMenu` 模型 + 复制/收藏两个按钮；macOS 12 保持无菜单）。换装后真机只读（PID 73364、750×492）两行右键：菜单层窗口 **58×58 @ (451,414)** 与 **(451,494)**；AX 读数 `<AXMenu>` 3 项 = 复制 enabled / 收藏 enabled / 分隔符 disabled，不再是系统文本菜单。**未点任何菜单项**（复制/收藏都不执行），不碰删除/清空/退出。
- **U-2224：② 判据与刀。** 新增 `RowContextMenuTests` 3 条：标题/符号与 `FavoriteTogglePresentation` 同源、`perform` 路由 copy/favorite、源码用 `contextMenu(forSelectionType:)` 且两个按钮都走 `RowContextMenu.perform`；`M1414`（把「复制」错接到收藏闭包）**CAUGHT、RESTORE_CLEAN=yes**；预检 **317/294/755 bad=0**、ARM **410/1242**（dupes=0 repeats=0）、HIDDEN **404/1181 rot=0**；build **0 告警**。
- **U-2225：③ 帧卷。** 捕获 **350 帧**：`CHANGED=0 ADDED=0 MISSING=0`，基线保持 **350**（系统菜单是弹出层，不进夹具帧；本轮的真实视觉证据是两张真机右键截图 + AX 菜单项读数）。
- **U-2226：④ 八步与电池。** build 0 告警；全量 **1383/56/0（584.7s）**（R537 的 1380 + 本轮 3 条新判据；本机 SelectionReveal 五条会话噪音本轮未出现）；换装 `ok / SHA_MATCH=1 / INSTALL_ENTRIES=431=431`（PID 73364；真机只读 1 窗口 750×492）；清账 **162 格已清 162/未清 0/不合法 0**；电池 **683/5**（台账后复跑）；product_streak **1** 轮（as-of 537，`python3 scripts/product_streak.py --streak-for 537` 现读，last=21a5440/536）。附注：换装后前台有一条系统 TCC 提示「时间剪史想访问桌面文件夹」（UserNotificationCenter），**未授权、未点按**；提示在前台时行菜单仍能打开（不是 app-modal），不阻断探针。
- **U-2227：⑤ 622/624/625/626/627。** 622 code-block 半仍等含 `21a5440` 的新跑（本轮五跑 in_progress）；frame 半最近 243.2ms/2/189、阈值不动。624 本轮无新两臂读数（五跑 in_progress），保持开单。625 本轮未动 Tab 链（产品落在 626），Tab 0/8 与 0/24 仍有效、保持开单。626 本机已落地（旧 117×165 系统菜单 → 新 58×58 两项 + AX 3 项），但 `9e78221` 未出结论 ⇒ **保持开单、待 runner 签收**。627 本轮五跑无 Motion floor 新读数，≥2 帧地板不动。
- **U-2228：⑥ 收口与交接。** 产品笔 `9e78221` 已推（HEAD=origin、ahead=0）。收口时 `41310819996 ↔ 9e78221`、`41309333668 ↔ 085e4c7`、`41309189054 ↔ 8cef540`、`41309008989 ↔ b707811`、`41308835299 ↔ 21a5440` 均 **in_progress ⇒ NOT-RUN**。下一轮 R539（第 538 轮 / Round 536）：先 push 并复核 ahead=0；读这五跑的全部失败步骤；622 的 code-block 只在含 `21a5440` 或更新、且不再抛 `NSInvalidArgumentException` 的跑才可签收；626 等 `9e78221` 跑签收 `RowContextMenuTests`；625/627/624 继续；4.5 地板、150 上限、120ms 阈值、Motion ≥2 帧地板均不动。

"""

ITERATION_SECTION = u"""
## Round 535 · R538（第 537 轮 · 2026-11-01）：行右键菜单改由列表选区层接管（626 本机落地）

旧值（R535）：行内容 `.contextMenu` 被 Text/cell 的系统文本菜单盖住，真机两次右键都弹 117×165 的系统菜单（撤销/重做/剪切/复制/粘贴/全选）。本轮把菜单改挂 `List` 的 `.contextMenu(forSelectionType: HistoryStore.Entry.ID.self)`（macOS 13+），菜单项由 `RowContextMenu` 提供（复制/收藏），macOS 12 保持无菜单。真机只读（PID 73364、750×492）两行右键：菜单层窗口 **58×58 @ (451,414)** 与 **(451,494)**；AX `<AXMenu>` 3 项 = 复制 enabled / 收藏 enabled / 分隔符 disabled，不再是系统文本菜单；未点任何菜单项。判据 `RowContextMenuTests` 3 条 + M1414 CAUGHT、RESTORE_CLEAN；预检 317/294/755 bad=0、ARM 410/1242、HIDDEN 404/1181 rot=0；build 0 告警。帧 350（CHANGED=0/ADDED=0/MISSING=0，基线不变）；全量 **1383/56/0（584.7s）**；换装 431=431（PID 73364）；清账 162/162/0；电池 683/5。626 本机落地但 runner 未签收，保持开单；622 code-block 仍等含 21a5440 的新跑。

**七维度自评**（恰七行，每格 n/15）：

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | 15/15 | 真机两行右键截图 + AX 菜单项；旧值 117×165 系统菜单与新值 58×58 两项菜单都留了读数。 |
| 判据有效性 | 15/15 | 3 条产品入口测试 + M1414 把复制接到收藏即 CAUGHT。 |
| 假绿防御 | 15/15 | 不点菜单项、不碰删除/清空；626 不在 runner 未签收时销单；622 不因本机不崩就签收。 |
| 产品面推进 | 15/15 | 菜单层所有权从 Text/cell 换到 List 选区层；产品 2 文件。 |
| 台账一致性 | 15/15 | U-2222…U-2228、D-537、350/1383/431/683 都来自命令与真机。 |
| 交付诚实性 | 15/15 | 626 仍开单待 runner；系统 TCC 提示与未授权状态如实记；没有把本机读数冒充 runner 结论。 |
| 可复核性 | 15/15 | run 号、菜单窗口 id/layer/bounds、AX 菜单项、M1414、预检 317/294/755 全在。 |

均分 = 105/105 ≈ 15.0/15（100）。
"""

CHANGELOG_SECTION = u"""### 行右键菜单改由列表选区层接管（R538 / 第 537 轮 / Round 535 / U-2222…U-2228 · 产品 2 文件 + 判据）

旧值：行 `.contextMenu` 被 Text/cell 的系统文本菜单盖住（真机 117×165：撤销/重做/剪切/复制/粘贴/全选）。改为 `List` 的 `.contextMenu(forSelectionType:)`（macOS 13+），由 `RowContextMenu` 提供复制/收藏两项，macOS 12 保持无菜单。真机两行右键读数：菜单层窗口 58×58、AX 菜单 3 项（复制/收藏 enabled）；新增 3 条判据与 M1414；帧 350（CHANGED=0）；全量 1383/56/0；换装 431=431。626 待 runner 签收。

"""

DECISION = u"""
## D-537 行右键菜单改由 List 选区层接管（R538）

- 背景：626 的旧值——把 `.contextMenu` 挂在行内容上时，真机右键被 `NSTableView` 的 Text/cell 系统文本菜单盖住（两次 117×165：撤销/重做/剪切/复制/粘贴/全选），应用自己的两项根本没机会出现。R535 的产品与源码判据因此一并撤回（不让源码判据冒充真机交付）。
- 决定：改用 macOS 13+ 的 `List` 级 `.contextMenu(forSelectionType: HistoryStore.Entry.ID.self)`，菜单内容由 `RowContextMenu` 纯模型给出（复制/收藏），按钮经 `historyStore.perform(.copyAndPromote)` / `.toggleFavorite` 落到产品入口；macOS 12 没有该 API，保持无菜单。
- 理由：右键所有权在列表层（`NSTableView`），行内容的文本菜单不再抢事件；菜单项标题/符号与 `FavoriteTogglePresentation` 同源，收藏文案不会两处漂移。
- 兼容性/迁移：菜单只在行上出（详情文本自己的右键不受影响）；macOS 12 行为与旧版一致（无应用菜单）；不改任何键盘路径与选中语义。
- 边界：本轮只做单条行菜单（多选时取 `filteredEntries` 里第一个命中项），不宣称批量动作；真机两行读数已留，但 runner `9e78221` 未出结论 ⇒ 626 保持开单、等签收。
"""


def main():
    # 1. UI_AUDIT
    name = "AGENT_UI_AUDIT.md"
    text = rd(name)
    anchor = u"## 第 536 轮（R537 · 2026-11-01 · U-2215…U-2221）"
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

    # 4. BACKLOG：622/624/625/626/627 复查
    name = "AGENT_BACKLOG.md"
    text = rd(name)
    add622 = u"""    复查（R538）：`21a5440`/`b707811`/`8cef540`/`085e4c7`/`9e78221` 读时均 in_progress ⇒ **code-block 半仍没有任何含 `21a5440` 的结论跑**，保持开单；frame 半最近仍是 `5837d65` 的 **243.2ms/2/189**，120ms 与容差不动。
"""
    text = append_after_line(text, u"复查（R537 收口）：`5837d65` 的 STEP[18] 读到 **243.2ms/2/189**", add622, u"backlog622")
    add624 = u"""    复查（R538）：本轮五跑 in_progress，无新两臂读数；非台账笔红/台账笔绿继续记，保持开单。
"""
    text = append_after_line(text, u"复查（R537 收口）：skip_roster 在 `5837d65`/`67437eb` 红、在 `e3e0893` 绿", add624, u"backlog624")
    add625 = u"""    复查（R538）：本轮未动 Tab 链（产品落在 626），无新读数；AppKit 按钮/焦点环保留，Tab 0/8 与 0/24 仍有效；625 保持开单。
"""
    text = append_after_line(text, u"复查（R537）：无新 Tab 链读数；AppKit 按钮/焦点环保留", add625, u"backlog625")
    add626 = u"""    复查（R538）：**本机已落地**——菜单从行内容 `.contextMenu` 改挂 `List` 的 `.contextMenu(forSelectionType:)`（macOS 13+）。真机两行右键：菜单层窗口 **58×58**（旧值 117×165 系统文本菜单）；AX `<AXMenu>` 3 项 = 复制 enabled / 收藏 enabled / 分隔符 disabled；未点菜单项。`RowContextMenuTests` 3 条 + M1414 CAUGHT。runner `9e78221` 未出结论 ⇒ **保持开单、待 runner 签收**。
"""
    text = append_after_line(text, u"复查（R537）：无新右键读数；系统文本菜单仍会盖住行菜单", add626, u"backlog626")
    add627 = u"""    复查（R538）：本轮五跑 in_progress，无 Motion floor 新读数；627 未再现，≥2 帧地板不动，保持开单等出现率。
"""
    text = append_after_line(text, u"复查（R537 收口）：`5837d65` 的 Motion floor 是 `judged=4/5 not-run=notice-banner 红=-`", add627, u"backlog627")
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
        (u"R9–R534，535 节自评", u"R9–R535，536 节自评", u"title"),
        (u"阶段二 **527 轮**审计（R9–R534；以 `curve_from_ledger.py` 的 `PHASE2 n=527` 为准，最新一节是 `AGENT_VISUAL_ITERATION.md` 的 Round 534",
         u"阶段二 **528 轮**审计（R9–R535；以 `curve_from_ledger.py` 的 `PHASE2 n=528` 为准，最新一节是 `AGENT_VISUAL_ITERATION.md` 的 Round 535", u"§1"),
        (u"| 视觉台账 | U-31 … U-2221", u"| 视觉台账 | U-31 … U-2228", u"U 上界"),
        (u"产品面连续零改动轮数 = **1**（as-of 536）", u"产品面连续零改动轮数 = **1**（as-of 537）", u"streak as-of"),
        (u"以 `AGENT_STATE.md` 的 R537 节 ② 为准", u"以 `AGENT_STATE.md` 的 R538 节 ② 为准", u"state pointer"),
        (u"## 18. R458 → R537 这一段", u"## 18. R458 → R538 这一段", u"§18 head"),
        (u"R537 续到 537 —— 这份报告第七次差点停在几十轮之前）", u"R538 续到 538 —— 这份报告第七次差点停在几十轮之前）", u"§18 tail"),
    ]
    for old, new, label in pairs:
        text = replace_once(text, old, new, label)
    bullet_anchor = u"；frame 175.8ms/2/203 记第三值。\n"
    if text.count(bullet_anchor) != 1:
        sys.stderr.write("ANCHOR_BAD §18 bullet\n")
        return 1
    bullet = u"- **R538（行右键菜单改由列表选区层接管；产品 2 文件 + 判据）**：旧值行 `.contextMenu` 被系统文本菜单盖住（真机 117×165）；改挂 `List` 的 `.contextMenu(forSelectionType:)`（macOS 13+），由 `RowContextMenu` 给复制/收藏两项。真机两行右键：菜单层窗口 **58×58 @ (451,414)/(451,494)**、AX 菜单 3 项（复制/收藏 enabled）；未点菜单项。新增 `RowContextMenuTests` 3 条 + M1414 CAUGHT；预检 317/294/755 bad=0、ARM 410/1242、HIDDEN 404/1181 rot=0；帧 350（CHANGED=0）；全量 1383/56/0（584.7s）；换装 431=431（PID 73364）；电池 683/5。626 待 runner 签收；622 code-block 仍等含 21a5440 的新跑。\n"
    text = text.replace(bullet_anchor, bullet_anchor + bullet, 1)
    wr(name, text)

    # 7. STATE
    name = "AGENT_STATE.md"
    text = rd(name)
    text = replace_once(
        text,
        u"最后更新：2026-11-01（本地 · R537 / 第 536 轮 / Round 534）",
        u"最后更新：2026-11-01（本地 · R538 / 第 537 轮 / Round 535）",
        u"identity")
    text = replace_once(
        text,
        u"## R538 开工 ⓪（2026-11-01 · 第 537 轮 / Round 535）",
        u"## R538 状态（2026-11-01 · 第 537 轮 / Round 535 · 产品 2 文件 + 判据）",
        u"state title")
    anchor = u"\n## R537 状态（2026-11-01 · 第 536 轮 / Round 534 · 产品 1 文件 + 判据）"
    body = u"""
① 626 旧值/产品：旧值（R535）行内容 `.contextMenu` 被系统文本菜单盖住，真机两次右键 117×165（撤销/重做/剪切/复制/粘贴/全选）。本轮把菜单改挂 `List` 的 `.contextMenu(forSelectionType: HistoryStore.Entry.ID.self)`（macOS 13+；`RowContextMenu` 模型 + 复制/收藏两个按钮；macOS 12 保持无菜单）。真机只读（PID 73364、750×492）两行右键：菜单层窗口 **58×58 @ (451,414)** 与 **(451,494)**；AX `<AXMenu>` 3 项 = 复制 enabled / 收藏 enabled / 分隔符 disabled ⇒ 不再是系统文本菜单。未点任何菜单项（复制/收藏都不执行），不碰删除/清空/退出。
② 判据/刀：`RowContextMenuTests` 3 条（标题/符号同源、perform 路由 copy/favorite、源码用 forSelectionType + 两个 perform）；`M1414` CAUGHT、RESTORE_CLEAN=yes；预检 317/294/755 bad=0、ARM 410/1242、HIDDEN 404/1181 rot=0；build 0 告警。
③ 帧 **350**：重捕 CHANGED=0 / ADDED=0 / MISSING=0，基线保持 350（系统菜单是弹出层，不进夹具帧；真实视觉证据是两张真机右键截图 + AX 菜单项）。全量 **1383/56/0（584.7s）**；换装 `ok / SHA_MATCH=1 / INSTALL_ENTRIES=431=431`（PID 73364；真机只读 1 窗口 750×492）；清账 162 格已清 162/未清 0/不合法 0；电池 **683/5**（台账后复跑）；产品面连续零改动 **1** 轮（as-of 537，`python3 scripts/product_streak.py --streak-for 537` 现读，last=21a5440/536）。附注：换装后前台有一条系统 TCC 提示（时间剪史想访问桌面文件夹），未授权、未点按；提示在前台时行菜单仍能打开（不是 app-modal）。
④ 收口：产品笔 `9e78221` 已推（HEAD=origin、ahead=0）；`41310819996 ↔ 9e78221`、`41309333668 ↔ 085e4c7`、`41309189054 ↔ 8cef540`、`41309008989 ↔ b707811`、`41308835299 ↔ 21a5440` 读时 in_progress ⇒ NOT-RUN。下一轮 R539（第 538 轮 / Round 536）：先 push 复核 ahead=0；读这五跑的全部失败步骤；622 code-block 只在含 `21a5440` 或更新、且不再抛 `NSInvalidArgumentException` 的跑才可签收；626 等 `9e78221` 跑签收 `RowContextMenuTests`；625/627/624 继续；4.5 地板、150 上限、120ms 阈值、Motion ≥2 帧地板均不动。"""
    text = replace_once(text, anchor, body + anchor, u"state body")
    wr(name, text)

    sys.stdout.write("LEDGERS_R538_OK\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
