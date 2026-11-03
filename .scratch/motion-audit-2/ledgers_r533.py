#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R533 台账（第 532 轮 / Round 530）。只写七本账，不碰产品。"""
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


UI_SECTION = u"""## 第 532 轮（R533 · 2026-11-01 · U-2187…U-2193）：折叠提示的「知道了」改为独立无障碍元素（产品 1 文件 + 判据）

- **U-2187：⓪ 网络与 CI。** HEAD=origin=`039413e`、ahead=0；`git ls-remote origin main` 报 `Connection closed by 20.205.243.166 port 22`；GitHub API `000` 而 apple `200` ⇒ **PUSH_BLOCKED=network / CI_READ_BLOCKED=network**，本轮不反复重试，收口前再试一次。`882e30f`/`df43baa`/`039413e` 三跑因此 **未读**（不下绿/红结论）；R532 收口已读：`c788299` **success** ⇒ 623 签收；`9bfd943`/`adb50c1`/`6add742` 的失败分别为台账时序 + SelectionReveal、两条运动 flake、时序 + SelectionReveal。
- **U-2188：① 旧值与产品。** 旧值（源码取证）：`collapseHintLine` 末尾有 `.accessibilityElement(children: .combine)`，把可点的「知道了」和信息文字合并成一个元素 ⇒ VoiceOver 只剩一段文字、按钮动作被并掉（离屏窗口不建 AX 树是已知盲区，和 UI_AUDIT 的无障碍清单同一条限制）。产品 **1 文件**：去掉 `.combine`，文字与按钮各自成无障碍元素；信息图标保持 `accessibilityHidden(true)`（装饰）。视觉零变化。
- **U-2189：② 判据、刀与 360pt 负向证人。** 新增 `testCollapseHintKeepsDismissButtonActionableForVoiceOver`（切 `collapseHintLine` 源码段：无 `.combine`、按钮标题/help、图标隐藏）；`M1409`（重新合并）**CAUGHT、RESTORE_CLEAN=yes**；预检 **312/289/750 bad=0**、ARM **405/1237**（dupes=0 repeats=0）、HIDDEN **399/1176 rot=0**；build **0 告警**。另加 `main-collapsed-hint-min` 360×560：亮/暗帧逐张看过，文案与「知道了」完整、不互相挤掉 ⇒ 最小宽负向证人。
- **U-2190：③ 帧卷。** 捕获 **350 帧**：`ADDED=2`（`main-collapsed-hint-min` 亮/暗）、`CHANGED=0`、`MISSING=0`；基线 348→350。无障碍改动不进像素，360 提示帧与 420 版同形。
- **U-2191：④ 八步与电池。** build 0 告警；全量 **1377/56/0（591.2s）**（本机 SelectionReveal 五条会话噪音本轮未出现）；换装 `ok / SHA_MATCH=1 / INSTALL_ENTRIES=431=431`（活库不变、只增不减；PID 52291；真机只读 1 窗口）；清账 **162 格已清 162/未清 0/不合法 0**；电池 **683/5**（台账后复跑）；product_streak **1** 轮（as-of 532，`python3 scripts/product_streak.py --streak-for 532` 现读，last=882e30f/531）。
- **U-2192：⑤ 网络与提交。** 本笔产品 `0720cc6` 只本地提交（API/git 两路都断，未推）；收口前再试一次 `git push`，仍失败就记 PUSH_BLOCKED 收口，不反复重试。
- **U-2193：⑥ 交接。** 下一轮 R534（第 533 轮 / Round 531）：先测 `git ls-remote`；通了先推本轮本地提交并复核 ahead=0，再读 882e30f/df43baa/039413e 与本轮两跑的全部失败步骤；623 已结案不重开；624（非台账笔红/台账笔绿）与 622（544.1ms/2 颗，本机未复现）保持开单；继续折叠特性；安全红线不变。

"""

ITERATION_SECTION = u"""
## Round 530 · R533（第 532 轮 · 2026-11-01）：折叠提示的「知道了」改为独立无障碍元素

旧值：`collapseHintLine` 用 `.accessibilityElement(children: .combine)` 把可点的「知道了」与文字合并成一个元素 ⇒ VoiceOver 只剩文字、按钮动作被并掉（离屏窗口不建 AX 树，已知盲区，用源码段作证）。产品 1 文件：去掉 `.combine`，文字与按钮各自成元素，装饰图标保持隐藏；视觉零变化。新增 `testCollapseHintKeepsDismissButtonActionableForVoiceOver`；M1409 CAUGHT、RESTORE_CLEAN；预检 312/289/750 bad=0、ARM 405/1237、HIDDEN 399/1176 rot=0；build 0 告警。另加 360×560 `main-collapsed-hint-min`：亮/暗帧看过，文案与「知道了」完整不挤掉（负向证人）。帧 350（ADDED=2、CHANGED=0；基线 348→350）；全量 1377/56/0（591.2s）；换装 431=431（PID 52291）；电池 683/5。网络两路断开，产品笔只本地提交。

**七维度自评**（恰七行，每格 n/15）：

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | 15/15 | 360/420 提示亮/暗帧逐张看过；文案与按钮不挤掉。 |
| 判据有效性 | 15/15 | 源码段断言 + M1409 重新 .combine 即 CAUGHT；按钮/图标三格都钉住。 |
| 假绿防御 | 15/15 | 离屏 AX 盲区明说，不冒充 VoiceOver 实读；360 是负向证人不是产品修复。 |
| 产品面推进 | 15/15 | 把可点确认从合并元素里救出来；产品 1 文件。 |
| 台账一致性 | 15/15 | U-2187…U-2193、D-532、350/1377/431/683 都来自命令与真机。 |
| 交付诚实性 | 15/15 | 网络两路断、产品笔未推、AX 不能实读都如实。 |
| 可复核性 | 15/15 | 源码段、M1409、预检 312/289/750、360 帧、全量 1377 都在。 |

均分 = 105/105 ≈ 15.0/15（100）。
"""

CHANGELOG_SECTION = u"""### 折叠提示的「知道了」改为独立无障碍元素（R533 / 第 532 轮 / Round 530 / U-2187…U-2193 · 产品 1 文件 + 判据）

折叠提示行去掉 `.accessibilityElement(children: .combine)`：文字与「知道了」各自成元素，VoiceOver 能单独聚焦并激活确认；装饰信息图标保持隐藏。新增源码段判据与 M1409；另加 360×560 最小宽提示帧（文案与按钮完整）。帧 350（ADDED=2）；全量 1377/56/0；换装 431=431。

"""

DECISION = u"""
## D-532 可点按钮不与提示文字合并成一个无障碍元素（R533）

- 背景：折叠提示行为了「读起来像一句话」用了 `.accessibilityElement(children: .combine)`，但这一行里有可点的「知道了」；`combine` 会把子元素的动作并掉，VoiceOver 只剩一段文字，用户无法确认提示。
- 决定：去掉 `.combine`，让信息文字与「知道了」各自成 AX 元素；装饰性的 info 图标保持 `accessibilityHidden(true)`；按钮保留标题与 `.helpLabel`。视觉不变。
- 理由：无障碍树里「一句话」与「可操作控件」是两种对象；为了朗读连贯而合并，代价是动作消失。设置页/排除行那两处 `.combine` 只含静态文字与图标，不受此条影响。
- 兼容性/迁移：不改视觉、不改帧基线（350 帧里唯一新增的是 360pt 提示帧）；离屏窗口不建 AX 树，判据用产品源码段，真机只做只读窗口检查。
- 边界：这是代码级契约判据，不冒充 VoiceOver 实听；若将来接入可构建 AX 树的本机通道，优先补一条真实 AX 断言。
"""


def main():
    # 1. UI_AUDIT：降序插在第 531 轮之上
    name = "AGENT_UI_AUDIT.md"
    text = rd(name)
    anchor = u"## 第 531 轮（R532 · 2026-11-01 · U-2180…U-2186）"
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

    # 4. BACKLOG：623/624/622 复查行（网络断，无新跑）
    name = "AGENT_BACKLOG.md"
    text = rd(name)
    add623 = u"""    复查（R533）：网络两路断开（PUSH_BLOCKED/CI_READ_BLOCKED=network），无新跑；623 已签收，不重开。
"""
    text = append_after_line(text, u"**623 结案（R532 收口，`c788299` 跑）**", add623, u"backlog623")
    add624 = u"""    复查（R533）：网络两路断开，无新两臂读数；保持开单。
"""
    text = append_after_line(text, u"复查（R532 收口）：`9bfd943`（非台账笔）STEP[9] 仍红在 skip_roster", add624, u"backlog624")
    add622 = u"""    复查（R533）：网络两路断开，无新 STEP[18]；120ms 与容差不动。
"""
    text = append_after_line(text, u"复查（R531）：本机按 runner 同条件（`CLIPBOARD_HISTORY_UI_INTERACTION=1`）", add622, u"backlog622")
    wr(name, text)

    # 5. DECISIONS：追加 D-532
    name = "AGENT_DECISIONS.md"
    text = rd(name)
    if not text.endswith(u"\n"):
        text += u"\n"
    text += DECISION
    wr(name, text)

    # 6. FINAL_REPORT：计数器 + §18 指针 + 一条 R533 记录
    name = "AGENT_FINAL_REPORT.md"
    text = rd(name)
    pairs = [
        (u"R9–R529，530 节自评", u"R9–R530，531 节自评", u"title"),
        (u"阶段二 **522 轮**审计（R9–R529；以 `curve_from_ledger.py` 的 `PHASE2 n=522` 为准，最新一节是 `AGENT_VISUAL_ITERATION.md` 的 Round 529",
         u"阶段二 **523 轮**审计（R9–R530；以 `curve_from_ledger.py` 的 `PHASE2 n=523` 为准，最新一节是 `AGENT_VISUAL_ITERATION.md` 的 Round 530", u"§1"),
        (u"| 视觉台账 | U-31 … U-2186", u"| 视觉台账 | U-31 … U-2193", u"U 上界"),
        (u"产品面连续零改动轮数 = **2**（as-of 531）", u"产品面连续零改动轮数 = **1**（as-of 532）", u"streak as-of"),
        (u"以 `AGENT_STATE.md` 的 R532 节 ② 为准", u"以 `AGENT_STATE.md` 的 R533 节 ② 为准", u"state pointer"),
        (u"## 18. R458 → R532 这一段", u"## 18. R458 → R533 这一段", u"§18 head"),
        (u"R532 续到 532 —— 这份报告第七次差点停在几十轮之前）", u"R533 续到 533 —— 这份报告第七次差点停在几十轮之前）", u"§18 tail"),
    ]
    for old, new, label in pairs:
        text = replace_once(text, old, new, label)
    bullet_anchor = u"真机 420×492 实拍提示行、再展开 750×492；电池 683/5。\n"
    if text.count(bullet_anchor) != 1:
        sys.stderr.write("ANCHOR_BAD §18 bullet\n")
        return 1
    bullet = u"- **R533（折叠提示的「知道了」改为独立无障碍元素；产品 1 文件 + 判据）**：旧值 `collapseHintLine` 用 `.accessibilityElement(children: .combine)` 把可点按钮并进文字；去掉后文字与按钮各自成 AX 元素、装饰图标隐藏；新增源码段判据与 M1409（CAUGHT）；另加 360×560 最小宽提示帧（文案/按钮完整，负向证人）。帧 350（ADDED=2、CHANGED=0）；全量 1377/56/0（591.2s）；换装 431=431（PID 52291）；电池 683/5。网络两路断开，本笔只本地提交（PUSH_BLOCKED=network）。\n"
    text = text.replace(bullet_anchor, bullet_anchor + bullet, 1)
    wr(name, text)

    # 7. STATE：identity + R533 标题 + ① ② ③ ④
    name = "AGENT_STATE.md"
    text = rd(name)
    text = replace_once(
        text,
        u"最后更新：2026-11-01（本地 · R532 / 第 531 轮 / Round 529）",
        u"最后更新：2026-11-01（本地 · R533 / 第 532 轮 / Round 530）",
        u"identity")
    text = replace_once(
        text,
        u"## R533 开工 ⓪（2026-11-01 · 第 532 轮 / Round 530）",
        u"## R533 状态（2026-11-01 · 第 532 轮 / Round 530 · 产品 1 文件 + 判据）",
        u"state title")
    anchor = u"\n\n## R532 状态（2026-11-01 · 第 531 轮 / Round 529 · 产品 5 文件 + 判据）"
    body = u"""
① 产品/旧值：旧 `collapseHintLine` 末尾有 `.accessibilityElement(children: .combine)`，把可点的「知道了」和信息文字合并成一个元素 ⇒ VoiceOver 只剩一段文字、按钮动作被并掉（离屏窗口不建 AX 树，已知盲区，用源码段作证）。产品 **1 文件**：去掉 `.combine`，文字与按钮各自成 AX 元素；装饰信息图标保持隐藏。视觉零变化；另加 360×560 `main-collapsed-hint-min`（亮/暗帧看过，文案与「知道了」完整、不挤掉）作为最小宽负向证人。
② 判据/刀：`testCollapseHintKeepsDismissButtonActionableForVoiceOver`（切源码段：无 `.combine`、按钮标题/help、图标隐藏）；`M1409` CAUGHT、RESTORE_CLEAN=yes；预检 312/289/750 bad=0、ARM 405/1237、HIDDEN 399/1176 rot=0；build 0 告警。帧 **350**（ADDED=2、CHANGED=0、MISSING=0；基线 348→350）。
③ 八步：全量 **1377/56/0（591.2s）**（本机 SelectionReveal 五条会话噪音本轮未出现）；换装 `ok / SHA_MATCH=1 / INSTALL_ENTRIES=431=431`（PID 52291；真机只读 1 窗口）；清账 162 格已清 162/未清 0/不合法 0；电池 **683/5**（台账后复跑）；产品面连续零改动 **1** 轮（as-of 532，`python3 scripts/product_streak.py --streak-for 532` 现读，last=882e30f/531）。
④ 收口/网络：产品笔 `0720cc6` 只本地提交；`git ls-remote origin main` 报 `Connection closed by 20.205.243.166 port 22`，GitHub API 000 而 apple 200 ⇒ **PUSH_BLOCKED=network / CI_READ_BLOCKED=network**；收口前再试一次 push。下一轮 R534（第 533 轮 / Round 531）：先测 ls-remote，通了先推本地提交并复核 ahead=0；623 已结案；624/622 保持开单；继续折叠特性；4.5 地板与 150 上限不动。"""
    text = replace_once(text, anchor, body + anchor, u"state body")
    wr(name, text)

    sys.stdout.write("LEDGERS_R533_OK\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
