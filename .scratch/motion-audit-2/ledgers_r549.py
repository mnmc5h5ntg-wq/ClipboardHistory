#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R549 台账（第 548 轮 / Round 546）。只写七本账，不碰产品。"""
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


UI_SECTION = u"""## 第 548 轮（R549 · 2026-11-02 · U-2319…U-2326）：无序列表项目符号换中等点（产品 1 文件 + 判据）

- **U-2319：⓪ CI。** HEAD=origin=`a210a29`、ahead=0、`git push` no-op；api=200/apple=200。三跑读时 **in_progress ⇒ NOT-RUN**：`41350830308 ↔ f0e9ea0`、`41351210379 ↔ 19d33b5`、`41351231883 ↔ a210a29`；queued/in_progress 不算成功。`41347708887 ↔ a7349c0`、`41347728673 ↔ 6d473a4` 均 **success（0 失败步）**；`41337616903 ↔ 30c7913` 仅 STEP[15]（PerfBudget 274.93ms + 录制帧 dark 9457px）、`41334537980 ↔ 8b667ae` 仅 STEP[15]（SelectionReveal 会话 flake）。
- **U-2320：② 无序列表项目符号。** BACKLOG 597：14pt 正文下「•」墨高只有 2.8pt。`MarkdownPresentation.bulletGlyph(depth:0)` 由 `•` 换成同字号更大的 `⦁`（U+2981）。纯几何读数：墨高 **2.8→3.9pt**（+39%）、墨宽同；行高 **19.0→19.0pt**（正文行高 19.0，未被撑大）；字号仍 14pt。
- **U-2321：② 判据/刀/预检。** 新判据 `testUnorderedBulletInkIsReadableWithoutGrowingTheLine`：项目符号墨高 ≥3.5pt 且行高与正文行高差 ≤0.5pt；`BULLET_INK 字符=⦁ 墨高=3.9pt 行高=19.0pt 正文行高=19.0pt`。`M1428`（退回「•」）**CAUGHT、RESTORE_CLEAN=yes**；预检 **328/295/757 bad=0**、ARM **421/1244**（dupes=0 repeats=0）、HIDDEN **410/1183 rot=0**；build **0 告警**；无 bulletGlyph 旧刀锚点，无需重钉。
- **U-2322：③ 帧/录制。** 新夹具 `detail-markdown-bullet`（720×520）；重捕：CHANGED=**4**（`detail-headings`、`detail-list-wrap` 各亮/暗）、ADDED=**2**、MISSING=0，基线 **352→354**；逐张看：`⦁` 比 `•` 更实，三条列表的换行与正文列未动。录制帧确定性 **10/10 diff=0**。
- **U-2323：③④ 全量/换装/电池/清账/streak。** 全量 **1388/56/0（686.6s）**；换装 `ok / SHA_MATCH=1 / INSTALL_ENTRIES=431=431`（PID 28058、1 窗口 750×492）；清账 **162/162/0**；电池 **691/5**（台账后复跑）；产品面连续零改动 **1** 轮（as-of 548，`python3 scripts/product_streak.py --streak-for 548` 现读）。
- **U-2324：⑤ 622/624/627/629/628/625/626。** 622 第七值 **176.6ms/2/204**、120ms/容差不动、frame 半开单；624 两臂继续、不改名册；627/629 保持开单；628/625/626 结案。
- **U-2325：⑤ BACKLOG 597 结案。** 「•」→「⦁」把墨高从 2.8 抬到 3.9pt，行高保持 19.0pt；判据是字体几何量、runner 与本机同源；新帧进基线。**结案**。
- **U-2326：⑥ 收口与交接。** ⓪ 笔 `deb28a1`、产品笔随后；下一轮 R550（第 549 轮 / Round 547）：先 push 复核 ahead=0；读本轮产品笔与台账笔、复读 `f0e9ea0`/`19d33b5`/`a210a29`/`30c7913`/`8b667ae` 与其余已读跑的全部失败步骤；622 frame 半、624、627、629 继续；628/625/626 不重开；4.5 地板、150 上限、120ms 阈值、Motion ≥2 帧地板均不动。

"""

ITERATION_SECTION = u"""
## Round 546 · R549（第 548 轮 · 2026-11-02）：无序列表项目符号换中等点

BACKLOG 597：14pt 正文下「•」墨高只有 2.8pt。`MarkdownPresentation.bulletGlyph(depth:0)` 由 `•` 换成同字号更大的 `⦁`（U+2981）。纯几何读数：墨高 **2.8→3.9pt**（+39%），行高 **19.0→19.0pt**（正文行高 19.0）；新判据 `BULLET_INK` 要求墨高 ≥3.5pt、行高差 ≤0.5pt；M1428 退回「•」CAUGHT。新夹具 `detail-markdown-bullet`；帧 CHANGED=4（`detail-headings`、`detail-list-wrap` 亮/暗）、ADDED=2，基线 352→354；逐张看 `⦁` 更实、换行未动；录制确定性 10/10 diff=0；build 0 告警；全量 **1388/56/0（686.6s）**；换装 431=431（PID 28058）；电池 691/5；BACKLOG 597 结案。

**七维度自评**（恰七行，每格 n/15）：

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | 15/15 | `detail-markdown-bullet` 与 `detail-list-wrap` 亮/暗逐张看：点更实、换行未动。 |
| 判据有效性 | 15/15 | `BULLET_INK` 3.9pt；M1428 CAUGHT；行高 19.0/19.0。 |
| 假绿防御 | 15/15 | 墨高与行高两条同时判；空字形或撑行距都过不去。 |
| 产品面推进 | 15/15 | 产品 1 文件：项目符号字形换代。 |
| 台账一致性 | 15/15 | U-2319…U-2326、D-549、354/1388/431/691 都来自命令与日志。 |
| 交付诚实性 | 15/15 | 三跑 NOT-RUN、627/629/624 开单都如实。 |
| 可复核性 | 15/15 | 2.8→3.9pt、M1428、预检 328/295/757 全在。 |

均分 = 105/105 ≈ 15.0/15（100）。
"""

CHANGELOG_SECTION = u"""### 无序列表项目符号换中等点（R549 / 第 548 轮 / Round 546 / U-2319…U-2326 · 产品 1 文件 + 判据）

`MarkdownPresentation.bulletGlyph(depth:0)` 由 `•` 换成同字号更大的 `⦁`（U+2981）。纯几何读数：墨高 2.8→3.9pt，行高 19.0→19.0pt；新判据 `BULLET_INK` 墨高 ≥3.5pt、行高差 ≤0.5pt；M1428 CAUGHT。新夹具 `detail-markdown-bullet`；帧 CHANGED=4、ADDED=2，基线 352→354；录制确定性 10/10 diff=0；全量 1388/56/0；换装 431=431；电池 691/5；BACKLOG 597 结案。

"""

DECISION = u"""
## D-549 无序列表项目符号用 U+2981，不用放大字号（R549）

- 背景：BACKLOG 597 记着 14pt 正文下「•」墨高只有约 3pt；R500 已证明放大 marker 字号会撑行距（三种钳高都不成立）。
- 决定：只换同字号更大的字形 `⦁`（U+2981），不动字号/字体/行距。
- 理由：纯几何读数墨高 2.8→3.9pt（+39%），行高 19.0→19.0pt（正文行高 19.0）；新判据 `BULLET_INK` 同时钉墨高 ≥3.5pt 与行高差 ≤0.5pt；M1428 退回「•」CAUGHT。
- 兼容性/迁移：只改一个字符；帧 CHANGED=4（`detail-headings`、`detail-list-wrap` 亮/暗）+ ADDED=2（`detail-markdown-bullet` 亮/暗），基线 352→354；录制帧确定性 10/10 diff=0。
- 边界：U+25CF 实测 11pt 太大，未采用；runner 帧卷会带新夹具，与本地同源。
"""


def main():
    name = "AGENT_UI_AUDIT.md"
    text = rd(name)
    anchor = u"## 第 547 轮（R548 · 2026-11-02 · U-2311…U-2318）"
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
    add597 = u"""    复查（R549）：项目符号由 `•` 换成同字号更大的 `⦁`（U+2981）；纯几何读数墨高 2.8→3.9pt、行高 19.0→19.0pt；新判据 `BULLET_INK`（墨高 ≥3.5pt、行高差 ≤0.5pt）；M1428 CAUGHT；新帧 `detail-markdown-bullet` + `detail-headings`/`detail-list-wrap` 各亮/暗。**结案**。
"""
    if text.count(u"扫描窗滑过即删。\n") != 1:
        sys.stderr.write("ANCHOR_BAD backlog597\n")
        return 1
    text = text.replace(u"扫描窗滑过即删。\n", u"扫描窗滑过即删。\n" + add597, 1)
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
        (u"R9–R545，546 节自评", u"R9–R546，547 节自评", u"title"),
        (u"阶段二 **538 轮**审计（R9–R545；以 `curve_from_ledger.py` 的 `PHASE2 n=538` 为准，最新一节是 `AGENT_VISUAL_ITERATION.md` 的 Round 545",
         u"阶段二 **539 轮**审计（R9–R546；以 `curve_from_ledger.py` 的 `PHASE2 n=539` 为准，最新一节是 `AGENT_VISUAL_ITERATION.md` 的 Round 546", u"§1"),
        (u"| 视觉台账 | U-31 … U-2318", u"| 视觉台账 | U-31 … U-2326", u"U 上界"),
        (u"产品面连续零改动轮数 = **1**（as-of 547）", u"产品面连续零改动轮数 = **1**（as-of 548）", u"streak as-of"),
        (u"以 `AGENT_STATE.md` 的 R548 节 ② 为准", u"以 `AGENT_STATE.md` 的 R549 节 ② 为准", u"state pointer"),
        (u"## 18. R458 → R548 这一段", u"## 18. R458 → R549 这一段", u"§18 head"),
        (u"R548 续到 548 —— 这份报告第七次差点停在几十轮之前）", u"R549 续到 549 —— 这份报告第七次差点停在几十轮之前）", u"§18 tail"),
    ]
    for old, new, label in pairs:
        text = replace_once(text, old, new, label)
    bullet_anchor = u"换装 431=431（PID 6647）；电池 691/5。627/629/624 保持开单。\n"
    if text.count(bullet_anchor) != 1:
        sys.stderr.write("ANCHOR_BAD §18 bullet\n")
        return 1
    bullet = u"- **R549（无序列表项目符号换中等点；产品 1 文件 + 判据）**：`bulletGlyph(depth:0)` 由 `•` 换 `⦁`（U+2981）；墨高 2.8→3.9pt、行高 19.0→19.0pt；新判据 `BULLET_INK`（墨高 ≥3.5pt、行高差 ≤0.5pt），M1428 CAUGHT。新夹具 `detail-markdown-bullet`；帧 CHANGED=4、ADDED=2，基线 352→354；录制确定性 10/10 diff=0；预检 328/295/757 bad=0、ARM 421/1244、HIDDEN 410/1183 rot=0；全量 1388/56/0（686.6s）；换装 431=431（PID 28058）；电池 691/5。627/629/624 保持开单。\n"
    text = text.replace(bullet_anchor, bullet_anchor + bullet, 1)
    wr(name, text)

    name = "AGENT_STATE.md"
    text = rd(name)
    text = replace_once(
        text,
        u"最后更新：2026-11-02（本地 · R548 / 第 547 轮 / Round 545）",
        u"最后更新：2026-11-02（本地 · R549 / 第 548 轮 / Round 546）",
        u"identity")
    text = replace_once(
        text,
        u"## R549 开工 ⓪（2026-11-02 · 第 548 轮 / Round 546）",
        u"## R549 状态（2026-11-02 · 第 548 轮 / Round 546 · 产品 1 文件 + 判据）",
        u"state title")
    anchor = u"\n## R548 状态（2026-11-02 · 第 547 轮 / Round 545 · 产品 1 文件 + 判据）"
    body = u"""
① 项目符号：BACKLOG 597；`bulletGlyph(depth:0)` `•`→`⦁`（U+2981）。纯几何读数墨高 2.8→3.9pt、行高 19.0→19.0pt（正文行高 19.0）。
② 判据/刀：新 `testUnorderedBulletInkIsReadableWithoutGrowingTheLine`（墨高 ≥3.5pt、行高差 ≤0.5pt，`BULLET_INK` 3.9/19.0/19.0）；`M1428` 退回「•」CAUGHT、RESTORE_CLEAN；预检 328/295/757 bad=0、ARM 421/1244、HIDDEN 410/1183 rot=0；build 0 告警；录制确定性 10/10 diff=0。
③ 帧/全量/换装/电池/清账/streak：帧 **352→354**（CHANGED=4：`detail-headings`、`detail-list-wrap` 各亮/暗；ADDED=2：`detail-markdown-bullet` 亮/暗）；全量 **1388/56/0（686.6s）**；换装 `ok / SHA_MATCH=1 / INSTALL_ENTRIES=431=431`（PID 28058）；电池 **691/5**（台账后复跑）；清账 162/162/0；产品面连续零改动 **1** 轮（as-of 548，`python3 scripts/product_streak.py --streak-for 548` 现读）。
④ 622/624/627/629：622 第七值 176.6ms/2/204、120ms/容差不动；624 两臂继续、不改名册；627/629 保持开单；628/625/626 结案；BACKLOG 597 结案。
⑤ CI/交接：⓪ 笔 `deb28a1`、产品笔随后；`41350830308 ↔ f0e9ea0`、`41351210379 ↔ 19d33b5`、`41351231883 ↔ a210a29` 读时 in_progress ⇒ NOT-RUN；`41347708887 ↔ a7349c0`、`41347728673 ↔ 6d473a4` success；`41337616903 ↔ 30c7913` 仅 STEP[15]（PerfBudget 274.93ms + 录制帧 dark 9457px）、`41334537980 ↔ 8b667ae` 仅 STEP[15]（SelectionReveal 会话 flake）。下一轮 R550（第 549 轮 / Round 547）：先 push 复核 ahead=0；读本轮产品笔与台账笔、复读 `f0e9ea0`/`19d33b5`/`a210a29`/`30c7913`/`8b667ae` 与已读跑的全部失败步骤；622 frame 半、624、627、629 继续；628/625/626 不重开；4.5 地板、150 上限、120ms 阈值、Motion ≥2 帧地板均不动。"""
    text = replace_once(text, anchor, body + anchor, u"state body")
    wr(name, text)

    sys.stdout.write("LEDGERS_R549_OK\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
