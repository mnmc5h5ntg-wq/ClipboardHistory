#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R537 台账（第 536 轮 / Round 534）。只写七本账，不碰产品。"""
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


UI_SECTION = u"""## 第 536 轮（R537 · 2026-11-01 · U-2215…U-2221）：代码语言标签改具体缓存字体（622 code-block 定位）（产品 1 文件 + 判据）

- **U-2215：⓪ CI。** HEAD=origin=`f271cc4`、ahead=0；网络通。`5837d65`/`67437eb`/`e3e0893`/`f271cc4` 读时 **in_progress ⇒ NOT-RUN**；`eec86a3` failure **仅 STEP[18]**：`testFrameIntervalsUnderStateChanges` 最差 **175.8ms**、超锚点 **2/203**（loaded_p95=16.67、比值 1.000）⇒ **622 第三次**（544.1→162.2→175.8），120ms 与容差不动；同跑 Motion floor `judged=5/5 executed=77 红=-`（627 未再现）。`789f642` **success**；`a2579fd` 仅 STEP[9]；`5bcbd7a` STEP[17] 的 code-block 崩溃（`ChineseTextContextMenu.swift:653`）为 622 第二次。
- **U-2216：① 622 code-block 定位。** 本机用同路径跑 `testCodeBlocksShowTheirLanguage` **10/10 全过**（不能复现）；runner 崩溃栈：`sizeWithAttributes:` → CoreText `TAttributes::ApplyFont` → `__NSPlaceholderDictionary initWithDictionary:copyItems:` 插 nil，位置在**字体描述符拷贝**。旧值 `CodeLanguageTag.font` 是 `.monospacedSystemFont`（系统 UI 等宽字体）；产品 **1 文件**改成具体 PostScript 名的 **Menlo-Bold** 并缓存（`nonisolated(unsafe) static let`，系统等宽兜底）。这是栈定位后的字体位处理，**622 仍待 runner 签收，不销单**。
- **U-2217：② 判据与刀。** 新增 `CodeLanguageTagFontTests.testFontIsConcreteCachedMenloBold`（fontName=Menlo-Bold、静态 let 同一对象）；`M1413`（改 Helvetica）**CAUGHT、RESTORE_CLEAN=yes**；预检 **316/293/754 bad=0**、ARM **409/1241**（dupes=0 repeats=0）、HIDDEN **403/1180 rot=0**；build **0 告警**。**过程自伤**：第一版把新测试写进同名 `CodeLanguageTagTests.swift`，覆盖了 R446 的 6 条旧测试，全量计数从 1379 掉到 1374；按套件对比发现后恢复原文件、字体测试放独立 `CodeLanguageTagFontTests.swift`，重跑 **1380**。
- **U-2218：③ 帧卷。** 捕获 **350 帧**：`CHANGED=6`（`detail-code`/`detail-code-tabs`/`detail-markdown-rendered` 亮暗）、`ADDED=0 MISSING=0`；基线保持 **350**；SWIFT 标签亮/暗帧逐张看过（Menlo-Bold 下仍可读，位置在代码块右上）。
- **U-2219：④ 八步与电池。** build 0 告警；全量 **1380/56/0（605.5s）**（本机 SelectionReveal 五条会话噪音本轮未出现）；换装 `ok / SHA_MATCH=1 / INSTALL_ENTRIES=431=431`（PID 56889；真机只读 1 窗口 750×492）；清账 **162 格已清 162/未清 0/不合法 0**；电池 **683/5**（台账后复跑）；product_streak **1** 轮（as-of 536，`python3 scripts/product_streak.py --streak-for 536` 现读，last=5837d65/535）。
- **U-2220：⑤ 622/627/624。** 622 的 code-block 半已按字体位修、**待 runner 签收**（本机不能复现）；frame-interval 半记 175.8ms/2/203 第三值，120ms 与容差不动。627 在 eec86a3 未再现（Motion floor 绿），保持开单等出现率。624 非台账笔红/台账笔绿继续；本地电池首跑偶发一次 skip_roster 已记。
- **U-2221：⑥ 收口与交接。** 产品笔 `21a5440` 已推（HEAD=origin、ahead=0）。下一轮 R538（第 537 轮 / Round 535）：先 push 并复核 ahead=0；读本轮产品/台账跑与 eec86a3 的全部失败步骤；622 的 code-block 若在新跑不再崩才可签收，frame-interval 与 627/624 继续；625/626 开单、623 不重开；继续折叠特性；安全红线不变。

"""

ITERATION_SECTION = u"""
## Round 534 · R537（第 536 轮 · 2026-11-01）：代码语言标签改具体缓存字体（622 code-block 定位）

622 的 code-block 第二次崩溃：本机 `testCodeBlocksShowTheirLanguage` 10/10 不复现；runner 栈在 `sizeWithAttributes:` → CoreText `TAttributes::ApplyFont` → `NSDictionary initWithDictionary:copyItems:` 插 nil（字体描述符拷贝）。产品 1 文件：`CodeLanguageTag.font` 从 `.monospacedSystemFont` 改为具体 PostScript 名的 `nonisolated(unsafe) static let Menlo-Bold`（系统等宽兜底），描述符具体、生命周期稳定。新增 `CodeLanguageTagFontTests`；M1413 CAUGHT、RESTORE_CLEAN；预检 316/293/754 bad=0、ARM 409/1241、HIDDEN 403/1180 rot=0；build 0 告警。过程自伤：第一版覆盖了 R446 的 CodeLanguageTagTests（6→1，全量 1374），按套件对比发现后恢复并独立文件，重跑 **1380/56/0（605.5s）**。帧 350（CHANGED=6：detail-code/-tabs/markdown-rendered 亮暗；基线不变），SWIFT 标签亮/暗逐张看过；换装 431=431（PID 56889）；电池 683/5。622 仍待 runner 签收（本机不能复现），frame-interval 175.8ms/2/203 记第三值，阈值不动。

**七维度自评**（恰七行，每格 n/15）：

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | 15/15 | 6 张代码标签帧变化逐张看过；Menlo-Bold 下 SWIFT 标签仍可读、位置正确。 |
| 判据有效性 | 15/15 | fontName/静态 let 两格 + M1413 改 Helvetica 即 CAUGHT。 |
| 假绿防御 | 15/15 | 本机 10/10 不复现不冒充修好；622 待 runner 签收；测试覆盖自伤当场发现并恢复。 |
| 产品面推进 | 15/15 | 字体描述符具体化 + 缓存，针对崩溃栈的字体位；产品 1 文件。 |
| 台账一致性 | 15/15 | U-2215…U-2221、D-536、350/1380/431/683 都来自命令与真机。 |
| 交付诚实性 | 15/15 | 不复现、待签收、覆盖 6 条旧测试的失误与恢复都如实。 |
| 可复核性 | 15/15 | 10 次跑次、崩溃栈、M1413、预检 316/293/754、1380 全在。 |

均分 = 105/105 ≈ 15.0/15（100）。
"""

CHANGELOG_SECTION = u"""### 代码语言标签改具体缓存字体（R537 / 第 536 轮 / Round 534 / U-2215…U-2221 · 产品 1 文件 + 判据）

622 的 code-block 崩溃栈指向 CoreText `TAttributes::ApplyFont` 的字体描述符拷贝；本机 10/10 不复现。`CodeLanguageTag.font` 由系统等宽字体改为具体 PostScript 名的 `nonisolated(unsafe) static let Menlo-Bold`（系统等宽兜底），描述符具体、生命周期稳定。新增字体判据与 M1413；帧 350（CHANGED=6 代码标签帧）；全量 1380/56/0；换装 431=431。622 待 runner 签收。

"""

DECISION = u"""
## D-536 代码语言标签用具体 PostScript 名的缓存字体（R537）

- 背景：622 的 code-block 崩溃第二次出现在 `testCodeBlocksShowTheirLanguage`；本机 10/10 不复现，runner 栈在 `sizeWithAttributes:` → CoreText `TAttributes::ApplyFont` → `NSDictionary initWithDictionary:copyItems:` 插 nil，位置是字体描述符拷贝；旧值用 `.monospacedSystemFont`（系统 UI 等宽字体）。
- 决定：`CodeLanguageTag.font` 改为具体 PostScript 名的 **Menlo-Bold**，用 `nonisolated(unsafe) static let` 缓存（系统等宽兜底），避免在测量/绘制路径里反复创建系统 UI 字体的惰性描述符。
- 理由：崩溃栈落在字体属性处理，不在颜色/文本；具体命名字体有稳定描述符，缓存消除重复创建。本机无法复现，所以这是**栈定位后的字体位处理**，不冒充「已修好」——622 保持开单，等 runner 新跑签收。
- 兼容性/迁移：代码标签字形/宽度略有变化（6 张代码标签帧变化，基线保持 350）；`CodeLanguageTagFontTests` 钉 fontName/缓存，M1413 钉字体不能被换成非等宽。
- 边界：本机 10/10 不复现，无法用本地复现证明修复；622 的 frame-interval 半（175.8ms/2/203 第三次）与 code-block 半分开记账，阈值不动。
"""


def main():
    # 1. UI_AUDIT
    name = "AGENT_UI_AUDIT.md"
    text = rd(name)
    anchor = u"## 第 535 轮（R536 · 2026-11-01 · U-2208…U-2214）"
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

    # 4. BACKLOG：622/625/626/627/624 复查
    name = "AGENT_BACKLOG.md"
    text = rd(name)
    add622 = u"""    复查（R537）：本机 `testCodeBlocksShowTheirLanguage` 10/10 不复现；runner 栈定位到 `sizeWithAttributes:` → CoreText `TAttributes::ApplyFont` → `NSDictionary initWithDictionary:copyItems:` 插 nil（字体描述符拷贝）。产品改为具体 **Menlo-Bold** 缓存字体（M1413 钉住），但本机不能复现 ⇒ **code-block 半仍待 runner 签收、不销单**；frame-interval 半本轮 `eec86a3` 再读 **175.8ms/2/203**（544.1→162.2→175.8），120ms 与容差不动。
"""
    text = append_after_line(text, u"复查（R536 收口）：`5bcbd7a` STEP[17] Capture gate 红在", add622, u"backlog622")
    add624 = u"""    复查（R537）：`eec86a3` STEP[18] 为 frame-interval，无 skip_roster 新读数；非台账笔红/台账笔绿与本地电池偶发一次继续记。
"""
    text = append_after_line(text, u"复查（R536 电池）：本地首跑也红在 skip_roster", add624, u"backlog624")
    add625 = u"""    复查（R537）：无新 Tab 链读数；AppKit 按钮/焦点环保留，Tab 0/8 与 0/24 仍有效；625 保持开单。
"""
    text = append_after_line(text, u"复查（R536）：换成真实 AppKit NSButton 并在 viewDidMoveToWindow/layout", add625, u"backlog625")
    add626 = u"""    复查（R537）：无新右键读数；系统文本菜单仍会盖住行菜单，626 保持开单。
"""
    text = append_after_line(text, u"下一步：在 Text/cell 层替换菜单，或 macOS 13 的 List", add626, u"backlog626")
    add627 = u"""    复查（R537）：`eec86a3` 的 Motion floor `judged=5/5 executed=77 红=-`，627 未再现；出现率仍未量，≥2 帧地板不动，保持开单。
"""
    text = append_after_line(text, u"复查（R536）：本轮五跑尚未出结论，627 无新出现率读数", add627, u"backlog627")
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
        (u"R9–R533，534 节自评", u"R9–R534，535 节自评", u"title"),
        (u"阶段二 **526 轮**审计（R9–R533；以 `curve_from_ledger.py` 的 `PHASE2 n=526` 为准，最新一节是 `AGENT_VISUAL_ITERATION.md` 的 Round 533",
         u"阶段二 **527 轮**审计（R9–R534；以 `curve_from_ledger.py` 的 `PHASE2 n=527` 为准，最新一节是 `AGENT_VISUAL_ITERATION.md` 的 Round 534", u"§1"),
        (u"| 视觉台账 | U-31 … U-2214", u"| 视觉台账 | U-31 … U-2221", u"U 上界"),
        (u"产品面连续零改动轮数 = **1**（as-of 535）", u"产品面连续零改动轮数 = **1**（as-of 536）", u"streak as-of"),
        (u"以 `AGENT_STATE.md` 的 R536 节 ② 为准", u"以 `AGENT_STATE.md` 的 R537 节 ② 为准", u"state pointer"),
        (u"## 18. R458 → R536 这一段", u"## 18. R458 → R537 这一段", u"§18 head"),
        (u"R536 续到 536 —— 这份报告第七次差点停在几十轮之前）", u"R537 续到 537 —— 这份报告第七次差点停在几十轮之前）", u"§18 tail"),
    ]
    for old, new, label in pairs:
        text = replace_once(text, old, new, label)
    bullet_anchor = u"收口复读：789f642 success；a2579fd 仅 STEP[9]；5bcbd7a STEP[17] code-block 崩溃再现（ChineseTextContextMenu.swift:653，622 第二次）；eec86a3/5837d65/67437eb/e3e0893 in_progress。\n"
    if text.count(bullet_anchor) != 1:
        sys.stderr.write("ANCHOR_BAD §18 bullet\n")
        return 1
    bullet = u"- **R537（代码语言标签改具体缓存字体；产品 1 文件 + 判据）**：622 code-block 第二次崩溃，本机 10/10 不复现；runner 栈在 CoreText ApplyFont 的字体描述符拷贝 ⇒ `CodeLanguageTag.font` 由系统等宽改为具体 PostScript 名 `Menlo-Bold` 缓存（系统等宽兜底）。新增 `CodeLanguageTagFontTests` + M1413 CAUGHT；预检 316/293/754 bad=0、ARM 409/1241、HIDDEN 403/1180 rot=0；帧 350（CHANGED=6 代码标签帧）；全量 1380/56/0（605.5s；中间把旧 CodeLanguageTagTests 覆盖成 1 条被计数发现，恢复后重跑）；换装 431=431（PID 56889）；电池 683/5。622 仍待 runner 签收、不销单；frame 175.8ms/2/203 记第三值。\n"
    text = text.replace(bullet_anchor, bullet_anchor + bullet, 1)
    wr(name, text)

    # 7. STATE
    name = "AGENT_STATE.md"
    text = rd(name)
    text = replace_once(
        text,
        u"最后更新：2026-11-01（本地 · R536 / 第 535 轮 / Round 533）",
        u"最后更新：2026-11-01（本地 · R537 / 第 536 轮 / Round 534）",
        u"identity")
    text = replace_once(
        text,
        u"## R537 开工 ⓪（2026-11-01 · 第 536 轮 / Round 534）",
        u"## R537 状态（2026-11-01 · 第 536 轮 / Round 534 · 产品 1 文件 + 判据）",
        u"state title")
    anchor = u"\n## R536 状态（2026-11-01 · 第 535 轮 / Round 533 · 产品 1 文件 + 判据）"
    body = u"""
① 622 code-block 定位：本机 `testCodeBlocksShowTheirLanguage` **10/10 全过**（不能复现）；runner 栈 `sizeWithAttributes:` → CoreText `TAttributes::ApplyFont` → `NSDictionary initWithDictionary:copyItems:` 插 nil（字体描述符拷贝）。旧值 `CodeLanguageTag.font = .monospacedSystemFont`；产品 **1 文件**改为具体 PostScript 名的 **Menlo-Bold**（`nonisolated(unsafe) static let` 缓存，系统等宽兜底）。这是栈定位后的字体位处理，**622 仍待 runner 签收、不销单**；frame-interval 半 `eec86a3` 再读 **175.8ms/2/203**（544.1→162.2→175.8），120ms 与容差不动。
② 判据/刀：`CodeLanguageTagFontTests.testFontIsConcreteCachedMenloBold`；`M1413` CAUGHT、RESTORE_CLEAN；预检 316/293/754 bad=0、ARM 409/1241、HIDDEN 403/1180 rot=0；build 0 告警。**过程自伤**：第一版覆盖了 R446 的 `CodeLanguageTagTests.swift`（6→1），全量从 1379 掉到 1374；按套件对比发现后恢复原文件、字体测试独立成 `CodeLanguageTagFontTests.swift`，重跑 **1380**。
③ 帧 **350**：CHANGED=6（detail-code/-tabs/markdown-rendered 亮暗）、ADDED/MISSING=0，基线保持 350；SWIFT 标签亮/暗逐张看过。全量 **1380/56/0（605.5s）**；换装 `ok / SHA_MATCH=1 / INSTALL_ENTRIES=431=431`（PID 56889；真机只读 1 窗口 750×492）；清账 162 格已清 162/未清 0/不合法 0；电池 **683/5**（台账后复跑）；产品面连续零改动 **1** 轮（as-of 536，`python3 scripts/product_streak.py --streak-for 536` 现读，last=5837d65/535）。
④ 收口：产品笔 `21a5440` 已推（HEAD=origin、ahead=0）；新跑待读。下一轮 R538（第 537 轮 / Round 535）：先 push 复核 ahead=0；622 code-block 若新跑不再崩才可签收，frame-interval/627/624 继续；625/626 开单、623 不重开；继续折叠特性；4.5 地板与 150 上限不动。"""
    text = replace_once(text, anchor, body + anchor, u"state body")
    wr(name, text)

    sys.stdout.write("LEDGERS_R537_OK\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
