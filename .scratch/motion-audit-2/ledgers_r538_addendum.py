#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R538 补记二：21a5440 跑的补读（622 code-block 签收、frame 第五值、628）。"""
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


U2229 = u"""- **U-2229：⓪ 补读 `41308835299 ↔ 21a5440`（收口后落地）。** run **failure**：STEP[9] Release script tests + STEP[18] On-screen probe coverage floor；STEP[15] Swift tests / STEP[16] Motion gate / STEP[17] Capture gate 全 **success**。**622 code-block 半签收**：日志里 `testCodeBlocksShowLineNumbers` 与 `testCodeBlocksShowTheirLanguage` 在 Offscreen 与 Swift steps 各 passed 一遍，`NSInvalidArgumentException` 计数 **0**（含 `21a5440` 的跑）⇒ 按判法签收；**frame 半第五值 151.4ms/2/195**（544.1→162.2→175.8→243.2→151.4，120ms 与容差不动、保持开单）。STEP[18] 红因两件事：`testFrameIntervalsUnderStateChanges` 151.4ms 红 + `testRightClickMenusAppKitWouldShowAreChinese` `PROBE_PULSE_OPEN`（BACKLOG 132），6/14 条探针没轮到。STEP[9] 5 红 = **4 条 git 缩写长度**（runner `%h` 给 8 位 `21a5440f`、账上存 7 位 `21a5440`：`test_recent_subjects_are_clean` / `test_roster_must_retire` / `test_the_second_label_source_is_a_derivation_not_a_roster` / `test_the_cell_agrees_with_its_own_source`；5837d65 跑没有前三条）+ **624** `skip_roster`。新开 **BACKLOG 628**（缩写长度确定性），不改名册、不放宽地板。
"""


def main():
    # 1. UI_AUDIT：标题区间 + 末尾补 U-2229
    name = "AGENT_UI_AUDIT.md"
    text = rd(name)
    text = replace_once(
        text,
        u"## 第 537 轮（R538 · 2026-11-01 · U-2222…U-2228）",
        u"## 第 537 轮（R538 · 2026-11-01 · U-2222…U-2229）",
        u"ui title")
    text = append_after_line(text, u"- **U-2228：⑥ 收口与交接。**", U2229, u"ui u2229")
    wr(name, text)

    # 2. CHANGELOG：区间 + 签收句
    name = "CHANGELOG.md"
    text = rd(name)
    text = replace_once(
        text,
        u"（R538 / 第 537 轮 / Round 535 / U-2222…U-2228 · 产品 2 文件 + 判据）",
        u"（R538 / 第 537 轮 / Round 535 / U-2222…U-2229 · 产品 2 文件 + 判据）",
        u"changelog heading")
    old = u"626 待 runner 签收。\n"
    text = replace_once(text, old, u"626 待 runner 签收。622 的 code-block 半由 41308835299（21a5440）签收：两条 code-block 测试各 passed 一遍、零 NSInvalidArgumentException；frame 半记第五值 151.4ms/2/195。\n", u"changelog codeblock")
    wr(name, text)

    # 3. BACKLOG：622/624/627 补读 + 628
    name = "AGENT_BACKLOG.md"
    text = rd(name)
    add622 = u"""    复查（R538 收口复读）：`41308835299 ↔ 21a5440`（R537 产品笔）**STEP[17] Capture gate success**；`testCodeBlocksShowLineNumbers` 与 `testCodeBlocksShowTheirLanguage` 在 Offscreen 与 Swift steps 各 passed 一遍，`NSInvalidArgumentException`=0 ⇒ **code-block 半签收**。同跑 STEP[18] 红：`testFrameIntervalsUnderStateChanges` 最差 **151.4ms**、超锚点 **2** 颗、n=195（622 第五值 544.1→162.2→175.8→243.2→151.4），120ms 与容差不动；另 `testRightClickMenusAppKitWouldShowAreChinese` 心跳未闭合（BACKLOG 132）⇒ 6/14 探针没跑。**frame 半保持开单**。
"""
    text = append_after_line(text, u"复查（R538）：`21a5440`/`b707811`/`8cef540`/`085e4c7`/`9e78221` 读时均 in_progress", add622, u"b622")
    add624 = u"""    复查（R538 收口复读）：`41308835299`（非台账产品笔）STEP[9] 仍红在 skip_roster「内层没有结论行」；同跑另 4 条是 628 的缩写长度族，不混算。两臂继续，保持开单。
"""
    text = append_after_line(text, u"复查（R538）：本轮五跑 in_progress，无新两臂读数", add624, u"b624")
    add627 = u"""    复查（R538 收口复读）：`41308835299` 的 Motion coverage floor `judged=5/5 executed=77 REDS=0`，627 未再现；出现率仍未量，≥2 帧地板不动，保持开单。
"""
    text = append_after_line(text, u"复查（R538）：本轮五跑 in_progress，无 Motion floor 新读数", add627, u"b627")
    item628 = u"""
**628. runner 的 git 缩写从 7 位变 8 位：四条脚本守卫把 7 位当固定长度**（R538 收口现读）
    现象：`41308835299 ↔ 21a5440` 的 STEP[9] 5 红中有 4 条同族：`test_recent_subjects_are_clean`（'5225de5' not found in ['21a5440f', … '5225de5a']）、`test_roster_must_retire`（[] != ['07acf2e', …]）、`test_the_second_label_source_is_a_derivation_not_a_roster`（git 里读不到 117f45d）、`test_the_cell_agrees_with_its_own_source`（报告格与 git 派生不一致）。runner 的 git 2.56.0 `%h` 现在给 **8 位**（21a5440f），本机给 **7 位**（21a5440）；roster/报告格存的是 7 位。`5837d65` 的跑没有前三条（当时 `%h` 还是 7 位），所以这不是产品回归。
    现状：读取处假设固定 7 位缩写；对象集变化会让同一份账在两台机器上答两个数。
    下一步：把读取处统一成确定性口径（`--abbrev=7`，或前缀比较 / `%H` 再裁剪），先在本地用 8 位模拟样本造红、再在 runner 签收；不放宽任何地板。
"""
    if not text.endswith(u"\n"):
        text += u"\n"
    text += item628
    wr(name, text)

    # 4. FINAL_REPORT：U 上界 + R538 bullet 补读
    name = "AGENT_FINAL_REPORT.md"
    text = rd(name)
    text = replace_once(text, u"| 视觉台账 | U-31 … U-2228", u"| 视觉台账 | U-31 … U-2229", u"fr u")
    old = u"626 待 runner 签收；622 code-block 仍等含 21a5440 的新跑。\n"
    new = u"626 待 runner 签收；622 code-block 半已由 `41308835299`（21a5440）签收（两测试各 passed、零 NSInvalidArgumentException），frame 半记第五值 **151.4ms/2/195**；同跑 STEP[9] 另开 4 条 git 缩写长度红（628）。\n"
    text = replace_once(text, old, new, u"fr bullet")
    wr(name, text)

    # 5. ITERATION：尾部追加收口复读
    name = "AGENT_VISUAL_ITERATION.md"
    text = rd(name)
    addendum = u"""
### R538 收口复读（`41308835299 ↔ 21a5440`）

收口后 `21a5440` 落地：STEP[15] Swift tests / STEP[16] Motion gate / STEP[17] Capture gate **success**；`testCodeBlocksShowLineNumbers` 与 `testCodeBlocksShowTheirLanguage` 在 Offscreen 与 Swift steps 各 passed 一遍、`NSInvalidArgumentException`=0 ⇒ **622 code-block 半签收**。STEP[18] 红在 `testFrameIntervalsUnderStateChanges` **151.4ms/2/195**（622 第五值）与 `testRightClickMenusAppKitWouldShowAreChinese` 心跳未闭合（BACKLOG 132，6/14 探针没跑）；frame 半保持开单、阈值不动。STEP[9] 5 红 = 4 条 git 缩写长度（runner `%h`=8 位 vs 账上 7 位）→ 新开 BACKLOG 628 + 624 skip_roster；不是产品回归。
"""
    if not text.endswith(u"\n"):
        text += u"\n"
    text += addendum
    wr(name, text)

    # 6. STATE：④ 收口段改写
    name = "AGENT_STATE.md"
    text = rd(name)
    old = u"④ 收口：产品笔 `9e78221` 已推（HEAD=origin、ahead=0）；`41310819996 ↔ 9e78221`、`41309333668 ↔ 085e4c7`、`41309189054 ↔ 8cef540`、`41309008989 ↔ b707811`、`41308835299 ↔ 21a5440` 读时 in_progress ⇒ NOT-RUN。下一轮 R539（第 538 轮 / Round 536）：先 push 复核 ahead=0；读这五跑的全部失败步骤；622 code-block 只在含 `21a5440` 或更新、且不再抛 `NSInvalidArgumentException` 的跑才可签收；626 等 `9e78221` 跑签收 `RowContextMenuTests`；625/627/624 继续；4.5 地板、150 上限、120ms 阈值、Motion ≥2 帧地板均不动。"
    new = u"""④ 收口与补读：产品笔 `9e78221`、台账笔 `1f65367` 已推（HEAD=origin、ahead=0）；`41310819996 ↔ 9e78221`、`41309333668 ↔ 085e4c7`、`41309189054 ↔ 8cef540`、`41309008989 ↔ b707811` 读时 in_progress ⇒ NOT-RUN。**补读 `41308835299 ↔ 21a5440`（failure）**：STEP[15]/[16]/[17] 全 success；code-block 两测试在 Offscreen 与 Swift steps 各 passed、`NSInvalidArgumentException`=0 ⇒ **622 code-block 半签收**；frame 半第五值 **151.4ms/2/195**（120ms/容差不动、保持开单）。STEP[18] = frame 151.4ms + `testRightClickMenusAppKitWouldShowAreChinese` 心跳未闭合（BACKLOG 132，6/14 探针没跑）；STEP[9] 5 红 = 4 条 git 缩写长度（runner `%h`=8 位 vs 账上 7 位）→ 新开 **BACKLOG 628** + 624 skip_roster，均非产品回归。
下一轮 R539（第 538 轮 / Round 536）：先 push 复核 ahead=0；读 `9e78221`/`1f65367` 及仍未结的五跑全部失败步骤；622 frame 半与 627/624 继续；626 等 `9e78221` 跑签收 `RowContextMenuTests`；修 628（缩写确定性，不放宽地板）；625 继续；4.5 地板、150 上限、120ms 阈值、Motion ≥2 帧地板均不动。"""
    text = replace_once(text, old, new, u"state 4")
    wr(name, text)

    sys.stdout.write("LEDGERS_R538_ADDENDUM_OK\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
