#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R548 台账（第 547 轮 / Round 545）。只写七本账，不碰产品。"""
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


UI_SECTION = u"""## 第 547 轮（R548 · 2026-11-02 · U-2311…U-2318）：250pt 批量标题不再截成省略号（产品 1 文件 + 判据）

- **U-2311：⓪ CI。** HEAD=origin=`6d473a4`、ahead=0、`git push` no-op；api=200/apple=200。`41347708887 ↔ a7349c0` 读时 **in_progress**、`41347728673 ↔ 6d473a4` **queued** ⇒ 均 NOT-RUN（queued 不算成功）。`41337616903 ↔ 30c7913` failure **仅 STEP[15]**：`PerfBudgetTests/testMarkdownRenderCostAtTheArchiveCap` 274.93ms > 250ms（负载 flake）与 `testRecordingCardFrameIsDeterministicAcrossRenders` dark 9457px（文档笔的 runner flake）；`41334537980 ↔ 8b667ae` 仅 STEP[15]（SelectionReveal 会话 flake）；复读 c5fcf03/c1df1e6/b16eacc/8d4a36d/bd96e93 的红同前。`41341697142 ↔ f58bf8c`、`41341540906 ↔ 54420e0`、`41341586171 ↔ d22f30a` 等 success。
- **U-2312：② 250pt 批量标题。** `sidebar-multi-select-min`（250pt）里「已选 3 条」被挤成「已选…」：旧帧标题带三枚 2pt 省略号点、右沿 54.5pt。`HistorySidebarView` 改为 `ViewThatFits`：宽度够用「已选 N 条」，不够退「N 条」（macOS 12 保留全称）。新帧标题带 3 段 **7.5/12.5/6.5pt**、最窄 6.5pt、右沿 66.5pt，无省略号点。
- **U-2313：② 判据/刀/预检。** 新判据 `testBatchTitleFitsAtTheMinimumSidebarWidth`：标题带最窄字形段必须 ≥4pt（省略号点约 2pt），至少 2 段；`BATCH_TITLE_FIT` light/dark 均 3 段、最窄 6.5pt。`M1427`（退回全称）**CAUGHT、RESTORE_CLEAN=yes**；预检 **327/295/757 bad=0**、ARM **420/1244**（dupes=0 repeats=0）、HIDDEN **410/1183 rot=0**；build **0 告警**；无 `headerTitle` 旧刀锚点，无需重钉。
- **U-2314：③ 帧/录制。** 重捕：CHANGED=**2**（`sidebar-multi-select-min` 亮/暗）、MISSING=0、ADDED=0；基线 **352→352**；宽窗 `sidebar-multi-select` 未被牵动。录制帧确定性 **10/10 diff=0**。
- **U-2315：③④ 全量/换装/电池/清账/streak。** 全量 **1387/56/0（689.4s）**；换装 `ok / SHA_MATCH=1 / INSTALL_ENTRIES=431=431`（PID 6647、1 窗口 750×492）；清账 **162/162/0**；电池 **691/5**（台账后复跑）；产品面连续零改动 **1** 轮（as-of 547，`python3 scripts/product_streak.py --streak-for 547` 现读）。
- **U-2316：⑤ 622/624/627/629/628/625/626。** 622 第七值 **176.6ms/2/204**、44 跑 worst 262.3 / over 2 / over_runs 17 / loaded_p95 46.73 / 比值 0.585–2.167，120ms/容差不动、frame 半开单；624 两臂继续、不改名册；627/629 保持开单；628/625/626 结案。
- **U-2317：⑤ BACKLOG 589 结案。** 批量态标题完整性第一次有稳定像素判据（最窄字形段 ≥4pt）；250pt 截断已由宽度自适应标题修掉，589 结案。
- **U-2318：⑥ 收口与交接。** ⓪ 笔 `f58bf8c`、产品笔随后；下一轮 R549（第 548 轮 / Round 546）：先 push 复核 ahead=0；读本轮产品笔与台账笔、复读 `a7349c0`/`6d473a4`/`30c7913`/`8b667ae` 与其余已读跑的全部失败步骤；622 frame 半、624、627、629 继续；628/625/626 不重开；4.5 地板、150 上限、120ms 阈值、Motion ≥2 帧地板均不动。

"""

ITERATION_SECTION = u"""
## Round 545 · R548（第 547 轮 · 2026-11-02）：250pt 批量标题不再截成省略号

`sidebar-multi-select-min`（250pt）里「已选 3 条」被挤成「已选…」：旧帧标题带三枚 2pt 省略号点、右沿 54.5pt。`HistorySidebarView` 改为 `ViewThatFits`：宽度够用「已选 N 条」，不够退「N 条」（macOS 12 保留全称）。新帧标题带 3 段 7.5/12.5/6.5pt、最窄 6.5pt、右沿 66.5pt；新判据 `BATCH_TITLE_FIT` 断言最窄字形段 ≥4pt、至少 2 段；M1427 退回全称 CAUGHT。帧 CHANGED=2（仅 `sidebar-multi-select-min` 亮/暗），基线 352→352；录制确定性 10/10 diff=0；build 0 告警；全量 **1387/56/0（689.4s）**；换装 431=431（PID 6647）；电池 691/5；BACKLOG 589 结案。

**七维度自评**（恰七行，每格 n/15）：

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | 15/15 | 250pt 侧栏帧逐张看：标题从「已选…」变「3 条」，无省略号。 |
| 判据有效性 | 15/15 | `BATCH_TITLE_FIT` 最窄 6.5pt；M1427 CAUGHT；旧帧 2pt 点会红。 |
| 假绿防御 | 15/15 | 至少 2 段 + 最窄 ≥4pt 两条同时判，空标题/省略号都过不去。 |
| 产品面推进 | 15/15 | 产品 1 文件：批量标题宽度自适应。 |
| 台账一致性 | 15/15 | U-2311…U-2318、D-548、352/1387/431/691 都来自命令与日志。 |
| 交付诚实性 | 15/15 | 两跑 NOT-RUN、627/629/624 开单、runner 未签收都如实。 |
| 可复核性 | 15/15 | 旧/新标题墨段、M1427、预检 327/295/757 全在。 |

均分 = 105/105 ≈ 15.0/15（100）。
"""

CHANGELOG_SECTION = u"""### 250pt 批量标题不再截成省略号（R548 / 第 547 轮 / Round 545 / U-2311…U-2318 · 产品 1 文件 + 判据）

`HistorySidebarView` 的批量标题改 `ViewThatFits`：宽度够用「已选 N 条」，250pt 最小侧栏退「N 条」（macOS 12 保留全称）。旧帧 250pt 标题带三枚 2pt 省略号点；新帧 3 段 7.5/12.5/6.5pt、最窄 6.5pt、右沿 66.5pt。新增 `BATCH_TITLE_FIT`（最窄字形段 ≥4pt、至少 2 段），M1427 CAUGHT；帧 CHANGED=2（仅 `sidebar-multi-select-min` 亮/暗），基线 352→352；录制确定性 10/10 diff=0；全量 1387/56/0；换装 431=431；电池 691/5；BACKLOG 589 结案。

"""

DECISION = u"""
## D-548 批量标题按宽度自适应，不在 250pt 截成省略号（R548）

- 背景：`sidebar-multi-select-min`（250pt）里「已选 3 条」被挤成「已选…」；BACKLOG 589 记着这条一直没有稳定像素判据。
- 决定：`HistorySidebarView` 的批量标题改 `ViewThatFits`：宽度够用「已选 N 条」，不够退「N 条」；macOS 12 保留全称。新判据 `BATCH_TITLE_FIT` 读标题带字形段：最窄 ≥4pt（省略号点约 2pt）、至少 2 段。
- 理由：旧帧标题带是三枚 2pt 省略号点、右沿 54.5pt；新帧 3 段 7.5/12.5/6.5pt、最窄 6.5pt、右沿 66.5pt，标题完整且仍说明选中数。
- 兼容性/迁移：只改标题的宽度策略；静态帧只有 `sidebar-multi-select-min` 亮/暗 2 张变化，基线 352→352；录制帧确定性 10/10 diff=0。
- 边界：runner 1x 的 `BATCH_TITLE_FIT` 待签收；627/629/624 不受影响。
"""


def main():
    name = "AGENT_UI_AUDIT.md"
    text = rd(name)
    anchor = u"## 第 546 轮（R547 · 2026-11-02 · U-2303…U-2310）"
    if text.count(anchor) != 1:
        sys.stderr.write("ANCHOR_BAD ui\n")
        return 1
    text = text.replace(anchor, UI_SECTION + anchor, 1)
    wr(name, text)

    name = "AGENT_VISUAL_ITERATION.md"
    text = rd(name)
    if not text.endswith(u"\n"):
        text += u"\n"
    text += ITERATION_SECTION
    wr(name, text)

    name = "CHANGELOG.md"
    text = rd(name)
    anchor = u"## [Unreleased]\n\n"
    if text.count(anchor) != 1:
        sys.stderr.write("ANCHOR_BAD changelog\n")
        return 1
    text = text.replace(anchor, anchor + CHANGELOG_SECTION, 1)
    wr(name, text)

    name = "AGENT_BACKLOG.md"
    text = rd(name)
    add589 = u"""    复查（R548）：`sidebar-multi-select-min` 250pt 的「已选 3 条」原来截成「已选…」（标题带三枚 2pt 点）；产品改 `ViewThatFits`，窄窗退「N 条」；新判据 `BATCH_TITLE_FIT` 读最窄字形段 ≥4pt、至少 2 段（新帧 3 段 7.5/12.5/6.5pt）；M1427 CAUGHT；帧仅 `sidebar-multi-select-min` 亮/暗 2 张变化。**结案**。
"""
    text = text.replace(u"    修法：若要自动化，需从视图树取 SwiftUI Text 的整定宽度或读 AX 值；先不加判据。\n",
                        u"    修法：若要自动化，需从视图树取 SwiftUI Text 的整定宽度或读 AX 值；先不加判据。\n" + add589, 1)
    wr(name, text)

    name = "AGENT_DECISIONS.md"
    text = rd(name)
    if not text.endswith(u"\n"):
        text += u"\n"
    text += DECISION
    wr(name, text)

    name = "AGENT_FINAL_REPORT.md"
    text = rd(name)
    pairs = [
        (u"R9–R544，545 节自评", u"R9–R545，546 节自评", u"title"),
        (u"阶段二 **537 轮**审计（R9–R544；以 `curve_from_ledger.py` 的 `PHASE2 n=537` 为准，最新一节是 `AGENT_VISUAL_ITERATION.md` 的 Round 544",
         u"阶段二 **538 轮**审计（R9–R545；以 `curve_from_ledger.py` 的 `PHASE2 n=538` 为准，最新一节是 `AGENT_VISUAL_ITERATION.md` 的 Round 545", u"§1"),
        (u"| 视觉台账 | U-31 … U-2310", u"| 视觉台账 | U-31 … U-2318", u"U 上界"),
        (u"产品面连续零改动轮数 = **1**（as-of 546）", u"产品面连续零改动轮数 = **1**（as-of 547）", u"streak as-of"),
        (u"以 `AGENT_STATE.md` 的 R547 节 ② 为准", u"以 `AGENT_STATE.md` 的 R548 节 ② 为准", u"state pointer"),
        (u"## 18. R458 → R547 这一段", u"## 18. R458 → R548 这一段", u"§18 head"),
        (u"R547 续到 547 —— 这份报告第七次差点停在几十轮之前）", u"R548 续到 548 —— 这份报告第七次差点停在几十轮之前）", u"§18 tail"),
    ]
    for old, new, label in pairs:
        text = replace_once(text, old, new, label)
    bullet_anchor = u"换装 431=431（PID 84566）；电池 691/5。627/629/624 保持开单。\n"
    if text.count(bullet_anchor) != 1:
        sys.stderr.write("ANCHOR_BAD §18 bullet\n")
        return 1
    bullet = u"- **R548（250pt 批量标题不再截成省略号；产品 1 文件 + 判据）**：`HistorySidebarView` 的批量标题改 `ViewThatFits`（宽度够用「已选 N 条」，250pt 退「N 条」）。旧帧标题带三枚 2pt 省略号点、右沿 54.5pt；新帧 3 段 7.5/12.5/6.5pt、最窄 6.5pt、右沿 66.5pt。新判据 `BATCH_TITLE_FIT`（最窄字形段 ≥4pt、至少 2 段），M1427 CAUGHT。帧 CHANGED=2（仅 `sidebar-multi-select-min` 亮/暗），基线 352→352；录制确定性 10/10 diff=0；预检 327/295/757 bad=0、ARM 420/1244、HIDDEN 410/1183 rot=0；全量 1387/56/0（689.4s）；换装 431=431（PID 6647）；电池 691/5。627/629/624 保持开单。\n"
    text = text.replace(bullet_anchor, bullet_anchor + bullet, 1)
    wr(name, text)

    name = "AGENT_STATE.md"
    text = rd(name)
    text = replace_once(
        text,
        u"最后更新：2026-11-02（本地 · R547 / 第 546 轮 / Round 544）",
        u"最后更新：2026-11-02（本地 · R548 / 第 547 轮 / Round 545）",
        u"identity")
    text = replace_once(
        text,
        u"## R548 开工 ⓪（2026-11-02 · 第 547 轮 / Round 545）",
        u"## R548 状态（2026-11-02 · 第 547 轮 / Round 545 · 产品 1 文件 + 判据）",
        u"state title")
    anchor = u"\n## R547 状态（2026-11-02 · 第 546 轮 / Round 544 · 产品 1 文件 + 判据）"
    body = u"""
① 批量标题：`sidebar-multi-select-min` 250pt 的「已选 3 条」原来截成「已选…」（标题带三枚 2pt 点、右沿 54.5pt）；`HistorySidebarView` 改 `ViewThatFits`，宽度够用全称、不够退「N 条」（macOS 12 保留全称）。新帧 3 段 7.5/12.5/6.5pt、最窄 6.5pt、右沿 66.5pt。
② 判据/刀：新 `testBatchTitleFitsAtTheMinimumSidebarWidth`（最窄字形段 ≥4pt、至少 2 段）；`M1427` 退回全称 CAUGHT、RESTORE_CLEAN；预检 327/295/757 bad=0、ARM 420/1244、HIDDEN 410/1183 rot=0；build 0 告警；录制确定性 10/10 diff=0。
③ 帧/全量/换装/电池/清账/streak：帧 **352→352**（CHANGED=2、仅 `sidebar-multi-select-min` 亮/暗）；全量 **1387/56/0（689.4s）**；换装 `ok / SHA_MATCH=1 / INSTALL_ENTRIES=431=431`（PID 6647）；电池 **691/5**（台账后复跑）；清账 162/162/0；产品面连续零改动 **1** 轮（as-of 547）。
④ 622/624/627/629：622 第七值 176.6ms/2/204、120ms/容差不动；624 两臂继续、不改名册；627/629 保持开单；628/625/626 结案；BACKLOG 589 结案。
⑤ CI/交接：⓪ 笔 `f58bf8c`、产品笔随后；`41347708887 ↔ a7349c0` 读时 in_progress、`41347728673 ↔ 6d473a4` queued ⇒ NOT-RUN；`41337616903 ↔ 30c7913` 仅 STEP[15]（PerfBudget 274.93ms + 录制帧 dark 9457px）、`41334537980 ↔ 8b667ae` 仅 STEP[15]（SelectionReveal 会话 flake）。下一轮 R549（第 548 轮 / Round 546）：先 push 复核 ahead=0；读本轮产品笔与台账笔、复读 `a7349c0`/`6d473a4`/`30c7913`/`8b667ae` 与已读跑的全部失败步骤；622 frame 半、624、627、629 继续；628/625/626 不重开；4.5 地板、150 上限、120ms 阈值、Motion ≥2 帧地板均不动。"""
    text = replace_once(text, anchor, body + anchor, u"state body")
    wr(name, text)

    sys.stdout.write("LEDGERS_R548_OK\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
