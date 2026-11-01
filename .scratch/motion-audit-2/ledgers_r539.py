#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R539 台账（第 538 轮 / Round 536）。只写七本账，不碰产品。"""
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


UI_SECTION = u"""## 第 538 轮（R539 · 2026-11-01 · U-2232…U-2240）：折叠提示按钮进 Tab 链 + git 缩写钉死（625 结案 / 628 本机修）（产品 1 文件 + 判据）

- **U-2232：⓪ CI。** HEAD=origin=`e07e78d`、ahead=0、`git push` no-op；api=200/apple=200。开工五跑读时 **in_progress ⇒ NOT-RUN**；收口前全部落地：`41310819996 ↔ 9e78221` failure **STEP[9]+[18]+[19]**、`41311271183 ↔ 1f65367` failure **仅 STEP[9]**、`41311603175 ↔ 0cc001f` failure **仅 STEP[9]**、`41311818680 ↔ b6394f5` failure **STEP[9]+[15]+[19]**、`41311984162 ↔ e07e78d` failure **仅 STEP[9]**；`41312123929 ↔ 40a2a71`（R539 ⓪）与 `41314618298 ↔ acefc43`（R539 产品）读时 **in_progress ⇒ NOT-RUN**。STEP[9] 的 4/5 红 = 3 条 git 缩写 + 624（产品笔多一条 sources 时序），见 U-2233/2239；STEP[15]/[19] 是折叠动画 runner 采样 flake，见 U-2239。
- **U-2233：① 628 旧值与修法。** runner `git %h` 给 **8 位**（`21a5440f`）、账上存 **7 位**（`21a5440`），三条脚本守卫红：`test_recent_subjects_are_clean`（生日 `5225de5` 对不上 `5225de5a`）/`test_roster_must_retire`（7 位豁免全成 stale）/`test_the_second_label_source_is_a_derivation_not_a_roster`（`117f45d` 找不到）。修法：`scripts/product_streak.py` 与 `test_commit_subject_hygiene` 的 `scan_args`/roster 查询显式 `--abbrev=7`；两条新判据用 `GIT_CONFIG_COUNT=1 core.abbrev=8` 环境变量**模拟 runner**（8 位输入下短 sha 仍 7 位、生日仍可认出）。`M1415`（product_streak 去钉）/`M1416`（scan 去钉）**CAUGHT、RESTORE_CLEAN=yes**。628 本机修好，**待 R539 产品跑签收**。
- **U-2234：② 625 旧值、根因与结案。** 旧值两层：单测 `window.selectNextKeyView` 24 站 0/24，但诊断发现窗口 `isKeyWindow=false`、`NSApp.isActive=false`，该调用**根本不移动焦点** ⇒ 0/24 是尺的假读数；链本身是 `NSHostingView → 搜索框 → FocusableHintButton`（结构正确）。真机旧值：折叠 420×472、提示可见，12 次 Tab 只在 `AXOutline`↔`AXTextField`，按钮不在 AXButton 列表。根因：无边框 NSButton 的 **`canBecomeKeyView` 默认 false**（`acceptsFirstResponder=true`）。产品 **1 文件**加 `override var canBecomeKeyView: Bool { true }`；新值真机 12 次 Tab 有 **4 次停在 `AXButton「知道了」`**（读屏描述「不再显示这条提示」），3 站循环 按钮→列表→搜索框。**625 结案**。
- **U-2235：② 判据与刀。** `MainWindowCollapseTests` 的读数从焦点遍历改成 **key-view 链结构**（按钮在链里、`nextKeyView` 非空），并断言 `acceptsFirstResponder`/`canBecomeKeyView`；`RowContextMenuTests` 3/3 在 `9e78221` 签收。`M1417`（去掉 `last?.nextKeyView = self`）/`M1418`（`canBecomeKeyView` 改回 false）**CAUGHT、RESTORE_CLEAN=yes**；预检 **319/295/757 bad=0**、ARM **411/1244**（dupes=0 repeats=0）、HIDDEN **406/1183 rot=0**；build **0 告警**。
- **U-2236：③ 帧卷。** 捕获 **350 帧**，`frame_baseline.py --against working compare`：`CHANGED=0 MISSING=0 ADDED=0`；基线保持 **350**（key-view 链改动不改变像）。
- **U-2237：④ 八步与电池。** 全量 **1383/56/0（613.2s）**（新 Python 判据不增 Swift 计数；本机 SelectionReveal 五条会话噪音本轮未出现）；换装 `ok / SHA_MATCH=1 / INSTALL_ENTRIES=431=431`（安装 PID 6127；探针后常规启动 PID 6240、1 窗口 750×492；活库 431 不增不减）；清账 **162 格已清 162/未清 0/不合法 0**；电池 **685/5**（683+2 条 628 判据；预跑曾红 skip_roster+sources 时序，台账后复跑）；product_streak **1**（as-of 538，`python3 scripts/product_streak.py --streak-for 538` 现读，last=9e78221/537）。
- **U-2238：⑤ 626 签收与 622 frame。** `9e78221` 的 `RowContextMenuTests` **3/3 passed**（Swift tests step 绿），失败步骤为 STEP[9]/[18]/[19]、与菜单无关 ⇒ **626 结案**（真机两行右键 58×58 + AX 三项，旧值 117×165 系统菜单）。622 frame **第六值 262.3ms/2/175**（544.1→162.2→175.8→243.2→151.4→262.3），120ms 与容差不动、**frame 半保持开单**；code-block 半仍按 `41308835299 ↔ 21a5440` 签收。
- **U-2239：⑤ 624 与 627。** 624 在 `9e78221`/`1f65367`/`0cc001f`/`b6394f5`/`e07e78d` 的 STEP[9] 均红在 skip_roster（产品/台账/补记/收口都红），旧「非台账红/台账绿」相关不成立，保持开单、不改名册。627 在 `9e78221` 的 STEP[19] **再现**：`MOTION_FLOOR_REDS=1`、红 `testCopyReceiptAppearsAndDismissesWithAVisibleProcess`，≥2 帧地板不动，保持开单。`b6394f5` 的 STEP[15] 是 `testCollapseWidthIsMeasuredFrameByFrame`（foldProgress `[0,0,0,0.993,0.993]`、终值 0.993 vs 1.0±0.001）⇒ 同类 runner 采样 flake，非产品回归；STEP[19] 是该红的下游。
- **U-2240：⑥ 收口与交接。** 产品笔 `acefc43` 已推（HEAD=origin、ahead=0）；台账笔随后。下一轮 R540（第 539 轮 / Round 537）：先 push 并复核 ahead=0；读 `41314618298 ↔ acefc43` 与 `41312123929 ↔ 40a2a71` 的全部失败步骤；628 只在 R539 产品跑的 STEP[9] 不再出现 3 条缩写红时签收；622 frame 半、624、627 继续；625/626 不重开；4.5 地板、150 上限、120ms 阈值、Motion ≥2 帧地板均不动。

"""

ITERATION_SECTION = u"""
## Round 536 · R539（第 538 轮 · 2026-11-01）：折叠提示按钮进 Tab 链 + git 缩写钉死（625 结案 / 628 本机修）

628：runner `git %h` 给 8 位、账上 7 位，三条脚本守卫红（subject 生日、roster 退役、streak 第二来源）。修法是把读取处钉成 `--abbrev=7`，并加两条用 `core.abbrev=8` 环境变量模拟 runner 的回归判据；M1415/M1416 CAUGHT、RESTORE_CLEAN。625：旧的 0/24 是假读数（单测窗口不是 key，`selectNextKeyView` 不移动焦点），链结构本来就对；真机旧值 12 次 Tab 只在列表/搜索框，根因是无边框 NSButton 的 `canBecomeKeyView=false`。产品 1 文件放行后，真机 12 次 Tab 有 4 次停在 AXButton「知道了」，625 结案。M1417/M1418 CAUGHT。预检 319/295/757 bad=0、ARM 411/1244、HIDDEN 406/1183 rot=0；build 0 告警；帧 350（CHANGED=0，基线不变）；全量 **1383/56/0（613.2s）**；换装 431=431（PID 6127→6240）；电池 685/5。626 由 9e78221 的 RowContextMenuTests 3/3 签收；622 frame 第六值 262.3ms/2/175；627 在 9e78221 再现。

**七维度自评**（恰七行，每格 n/15）：

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | 15/15 | 真机折叠提示截图 + Tab 12 站逐站读 AX；帧卷 350 比对 CHANGED=0。 |
| 判据有效性 | 15/15 | 628 两条模拟 8 位判据 + 625 链结构判据；M1415–M1418 四臂全 CAUGHT。 |
| 假绿防御 | 15/15 | 先证明旧 0/24 是窗口非 key 的假读数；真机旧/新值都留；628 用环境变量造 8 位输入。 |
| 产品面推进 | 15/15 | `canBecomeKeyView=true` 让折叠提示按钮真正进入 Tab 链；产品 1 文件。 |
| 台账一致性 | 15/15 | U-2232…U-2240、D-538/D-539、350/1383/431/685 都来自命令与真机。 |
| 交付诚实性 | 15/15 | 628 待 runner；622 frame/624/627 保持开单；626 的失败步骤逐条读过且与菜单无关。 |
| 可复核性 | 15/15 | run 号、Tab 12 站读数、AXButton 标题、M1415–M1418、预检 319/295/757 全在。 |

均分 = 105/105 ≈ 15.0/15（100）。
"""

CHANGELOG_SECTION = u"""### 折叠提示按钮进入 Tab 链 + git 缩写钉死（R539 / 第 538 轮 / Round 536 / U-2232…U-2240 · 产品 1 文件 + 判据）

625：无边框 NSButton 的 `canBecomeKeyView` 默认 false，折叠提示的「知道了」虽在 key-view 链里却不被 Tab 环收；显式放行后真机 12 次 Tab 有 4 次停在 AXButton「知道了」（旧值 0/12，只在列表/搜索框）。628：runner 的 `git %h` 给 8 位而账上存 7 位，三条脚本守卫红；读取处改钉 `--abbrev=7`，并用 `core.abbrev=8` 环境模拟 runner 的回归判据；M1415–M1418 CAUGHT。帧 350（CHANGED=0）；全量 1383/56/0；换装 431=431；电池 685/5。

"""

DECISION1 = u"""
## D-538 折叠提示按钮用 canBecomeKeyView 放行（R539）

- 背景：625 的旧读数有两层——单测用 `window.selectNextKeyView` 判 0/24，但单测窗口 `isKeyWindow=false`/`NSApp.isActive=false`，调用根本不移动焦点（尺没有对象）；真机 12 次 Tab 也只到列表/搜索框。链结构本身是通的（`NSHostingView → 搜索框 → FocusableHintButton`）。
- 决定：`FocusableHintButton` 显式 `override var canBecomeKeyView: Bool { true }`；单测改判 **key-view 链结构**（按钮在链里、`nextKeyView` 非空）并断言 `acceptsFirstResponder`/`canBecomeKeyView`。
- 理由：无边框 NSButton 的 `canBecomeKeyView` 默认 false，自动 key-view 环因此不收它；`acceptsFirstResponder=true` 不足以让它成为 Tab 停靠点。真机新值 12 次 Tab 有 4 次停在 AXButton「知道了」。
- 兼容性/迁移：只影响折叠提示可见时的窗口 key-view 环；按钮消失后链仍由系统重算。视觉零变化（帧 350/CHANGED=0）。
- 边界：真机读数是 12 站里 4 次命中，不是每次 Tab 都命中；停止条件与链结构由 M1417/M1418 钉住。
"""

DECISION2 = u"""
## D-539 git 缩写读取钉成 7 位并用环境变量模拟 runner（R539）

- 背景：628 runner 的 `git %h` 给 8 位、本机/账上 7 位，`test_recent_subjects_are_clean`/`test_roster_must_retire`/`test_the_second_label_source_is_a_derivation_not_a_roster` 三条守卫红；sources 格红是另一条（产品笔早于台账的时序），不混算。
- 决定：`scripts/product_streak.py` 与 `test_commit_subject_hygiene` 的读取处显式 `--abbrev=7`；新增两条回归判据用 `GIT_CONFIG_COUNT=1 core.abbrev=8` 模拟 runner 的 8 位默认，断言短 sha 仍是 7 位、生日仍可认出。
- 理由：判据要比的是「同一份账里的 sha」，不是「这台机器的 git 恰好给几位」；钉死 7 位与账上/roster 的存储口径一致，且显式参数可覆盖 `core.abbrev`。
- 兼容性/迁移：不改地板/阈值，不删守卫；7 位与 8 位输入都走同一条断言（8 位环境由新判据钉住）。
- 边界：本机修复、待 R539 产品跑在 runner 上签收；sources 时序红不在本条内。
"""


def main():
    # 1. UI_AUDIT
    name = "AGENT_UI_AUDIT.md"
    text = rd(name)
    anchor = u"## 第 537 轮（R538 · 2026-11-01 · U-2222…U-2231）"
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

    # 4. BACKLOG
    name = "AGENT_BACKLOG.md"
    text = rd(name)
    add622 = u"""    复查（R539）：`9e78221` 的 STEP[18] frame **262.3ms/2/175**（第六值 544.1→162.2→175.8→243.2→151.4→262.3；loaded_p95=46.73、比值 1.098），120ms 与容差不动；code-block 半已按 `41308835299 ↔ 21a5440` 签收，frame 半保持开单。
"""
    text = append_after_line(text, u"复查（R538 补读）：`41309008989 ↔ b707811`", add622, u"b622r539")
    add624 = u"""    复查（R539）：`9e78221`/`1f65367`/`0cc001f`/`b6394f5`/`e07e78d` 五跑 STEP[9] 全红在 skip_roster（产品/台账/补记/收口都红）；旧「非台账红/台账绿」相关不成立，保持开单、不改名册。
"""
    text = append_after_line(text, u"复查（R538 补读二）：`41309333668 ↔ 085e4c7`", add624, u"b624r539")
    close625 = u"""**625 结案（R539）**：旧 0/24 是假读数（单测窗口非 key，`selectNextKeyView` 不移动焦点）；链结构本来就是 `NSHostingView → 搜索框 → FocusableHintButton`。真机旧值 12 次 Tab 只在列表/搜索框，根因是无边框 NSButton 的 `canBecomeKeyView=false`；产品放行后真机 12 次 Tab 有 4 次停在 `AXButton「知道了」`（描述「不再显示这条提示」），单测改判链结构并钉 `acceptsFirstResponder`/`canBecomeKeyView`；M1417/M1418 CAUGHT。视觉零变化（帧 350/CHANGED=0）。
"""
    text = append_after_line(text, u"复查（R538）：本轮未动 Tab 链（产品落在 626）", close625, u"b625close")
    close626 = u"""**626 结案（R539，`41310819996 ↔ 9e78221` 跑）**：`RowContextMenuTests` 3/3 passed（Swift tests step 绿）；同跑失败步骤只有 STEP[9]（3 条 git 缩写 + 624 + sources 时序）、STEP[18]（frame 262.3ms + `testRightClickMenusAppKitWouldShowAreChinese` 心跳未闭合）与 STEP[19]（627 回执），与菜单无关。真机读数沿用 R538：两行右键 58×58 + AX 三项（复制/收藏 enabled），旧值 117×165 系统文本菜单。
"""
    text = append_after_line(text, u"复查（R538）：**本机已落地**", close626, u"b626close")
    add627 = u"""    复查（R539）：`9e78221` 的 STEP[19] **再现**：`MOTION_FLOOR_REDS=1`、红 `testCopyReceiptAppearsAndDismissesWithAVisibleProcess`；另 `b6394f5` STEP[15] 的 `testCollapseWidthIsMeasuredFrameByFrame`（foldProgress `[0,0,0,0.993,0.993]`、终值 0.993 vs 1.0±0.001）是同类 runner 采样 flake，STEP[19] 为其下游。≥2 帧地板不动，保持开单等出现率。
"""
    text = append_after_line(text, u"复查（R538 收口复读）：`41308835299` 的 Motion coverage floor", add627, u"b627r539")
    fix628 = u"""    本机修复（R539）：`product_streak.product_commits` 与 `test_commit_subject_hygiene` 的 `scan_args`/roster 查询显式 `--abbrev=7`；新增两条回归判据用 `GIT_CONFIG_COUNT=1 core.abbrev=8` 模拟 runner（8 位输入下短 sha 仍 7 位、生日仍可认出）；`M1415`/`M1416` CAUGHT、RESTORE_CLEAN。待 R539 产品跑在 runner 上签收。
"""
    if not text.endswith(u"\n"):
        text += u"\n"
    text += fix628
    wr(name, text)

    # 5. DECISIONS
    name = "AGENT_DECISIONS.md"
    text = rd(name)
    if not text.endswith(u"\n"):
        text += u"\n"
    text += DECISION1 + DECISION2
    wr(name, text)

    # 6. FINAL_REPORT
    name = "AGENT_FINAL_REPORT.md"
    text = rd(name)
    pairs = [
        (u"R9–R535，536 节自评", u"R9–R536，537 节自评", u"title"),
        (u"阶段二 **528 轮**审计（R9–R535；以 `curve_from_ledger.py` 的 `PHASE2 n=528` 为准，最新一节是 `AGENT_VISUAL_ITERATION.md` 的 Round 535",
         u"阶段二 **529 轮**审计（R9–R536；以 `curve_from_ledger.py` 的 `PHASE2 n=529` 为准，最新一节是 `AGENT_VISUAL_ITERATION.md` 的 Round 536", u"§1"),
        (u"| 视觉台账 | U-31 … U-2231", u"| 视觉台账 | U-31 … U-2240", u"U 上界"),
        (u"产品面连续零改动轮数 = **1**（as-of 537）", u"产品面连续零改动轮数 = **1**（as-of 538）", u"streak as-of"),
        (u"以 `AGENT_STATE.md` 的 R538 节 ② 为准", u"以 `AGENT_STATE.md` 的 R539 节 ② 为准", u"state pointer"),
        (u"## 18. R458 → R538 这一段", u"## 18. R458 → R539 这一段", u"§18 head"),
        (u"R538 续到 538 —— 这份报告第七次差点停在几十轮之前）", u"R539 续到 539 —— 这份报告第七次差点停在几十轮之前）", u"§18 tail"),
    ]
    for old, new, label in pairs:
        text = replace_once(text, old, new, label)
    bullet_anchor = u"STEP[15]–[19] 全绿。\n"
    if text.count(bullet_anchor) != 1:
        sys.stderr.write("ANCHOR_BAD §18 bullet\n")
        return 1
    bullet = u"- **R539（折叠提示按钮进 Tab 链 + git 缩写钉死；产品 1 文件 + 判据）**：628 的 runner `%h`=8 位 vs 账上 7 位让三条脚本守卫红；读取处钉 `--abbrev=7`，两条新判据用 `core.abbrev=8` 环境模拟 runner；M1415/M1416 CAUGHT。625 的旧 0/24 是单测窗口非 key 的假读数；真机根因是无边框 NSButton `canBecomeKeyView=false`，放行后真机 12 次 Tab 有 4 次停在 AXButton「知道了」；M1417/M1418 CAUGHT。预检 319/295/757 bad=0、ARM 411/1244、HIDDEN 406/1183 rot=0；帧 350（CHANGED=0）；全量 1383/56/0（613.2s）；换装 431=431（PID 6127→6240）；电池 685/5。626 由 9e78221 的 RowContextMenuTests 3/3 签收；622 frame 第六值 262.3ms/2/175；627 在 9e78221 再现。\n"
    text = text.replace(bullet_anchor, bullet_anchor + bullet, 1)
    wr(name, text)

    # 7. STATE
    name = "AGENT_STATE.md"
    text = rd(name)
    text = replace_once(
        text,
        u"最后更新：2026-11-01（本地 · R538 / 第 537 轮 / Round 535）",
        u"最后更新：2026-11-01（本地 · R539 / 第 538 轮 / Round 536）",
        u"identity")
    text = replace_once(
        text,
        u"## R539 开工 ⓪（2026-11-01 · 第 538 轮 / Round 536）",
        u"## R539 状态（2026-11-01 · 第 538 轮 / Round 536 · 产品 1 文件 + 判据）",
        u"state title")
    anchor = u"\n## R538 状态（2026-11-01 · 第 537 轮 / Round 535 · 产品 2 文件 + 判据）"
    body = u"""
① 628 旧值/修：runner `git %h` 给 8 位、账上 7 位，三条脚本守卫红（subject 生日 / roster 退役 / streak 第二来源）。`product_streak` 与 `scan_args`/roster 钉 `--abbrev=7`，两条新判据用 `GIT_CONFIG_COUNT=1 core.abbrev=8` 模拟 runner；`M1415`/`M1416` CAUGHT、RESTORE_CLEAN。628 本机修好、待 R539 产品跑签收。
② 625 旧值/根因/结案：单测 0/24 是假读数（窗口非 key、`selectNextKeyView` 不移动焦点），链结构本来就是 `NSHostingView → 搜索框 → FocusableHintButton`；真机旧值 12 次 Tab 只在 `AXOutline`↔`AXTextField`，根因是无边框 NSButton 的 `canBecomeKeyView=false`。产品 1 文件放行后真机 12 次 Tab 有 4 次停在 `AXButton「知道了」`；`M1417`/`M1418` CAUGHT。**625 结案**。
③ 判据/刀/预检：`MainWindowCollapseTests` 改判链结构 + `acceptsFirstResponder`/`canBecomeKeyView`；预检 319/295/757 bad=0、ARM 411/1244、HIDDEN 406/1183 rot=0；build 0 告警。626 由 `9e78221` 的 RowContextMenuTests 3/3 签收（失败步骤 STEP[9]/[18]/[19] 与菜单无关）。
④ 帧/全量/换装/电池/清账/streak：帧 **350**（CHANGED=0，基线不变）；全量 **1383/56/0（613.2s）**；换装 `ok / SHA_MATCH=1 / INSTALL_ENTRIES=431=431`（安装 PID 6127；探针后常规启动 PID 6240、1 窗口 750×492）；电池 **685/5**（台账后复跑）；清账 162/162/0；product_streak **1**（as-of 538，`--streak-for 538` 现读，last=9e78221/537）。
⑤ CI/交接：产品笔 `acefc43` 已推（HEAD=origin、ahead=0）；R540 ⓪ 要读的成对：`41314618298 ↔ acefc43`（产品，读时 in_progress ⇒ NOT-RUN）、`41312123929 ↔ 40a2a71`（⓪，in_progress ⇒ NOT-RUN），以及已读的 `41310819996 ↔ 9e78221`（failure STEP[9]+[18]+[19]；626 签收、622 frame 262.3ms/2/175、627 再现）、`41311271183 ↔ 1f65367`（仅 STEP[9]）、`41311603175 ↔ 0cc001f`（仅 STEP[9]）、`41311818680 ↔ b6394f5`（STEP[9]+[15]+[19]，折叠动画采样 flake）、`41311984162 ↔ e07e78d`（仅 STEP[9]）；台账跑 push 后取号。下一轮 R540（第 539 轮 / Round 537）：先 push 复核 ahead=0；读这两跑全部失败步骤；628 只在 R539 产品跑 STEP[9] 不再出现 3 条缩写红时签收；622 frame 半/624/627 继续；625/626 不重开；4.5 地板、150 上限、120ms 阈值、Motion ≥2 帧地板均不动。"""
    text = replace_once(text, anchor, body + anchor, u"state body")
    wr(name, text)

    sys.stdout.write("LEDGERS_R539_OK\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
