#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R538 补记三：b707811/8cef540 补读、缩写计数量更正、624 两臂更新。"""
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


U2230 = u"""- **U-2230：⓪ 补读 `41309008989 ↔ b707811`、`41309189054 ↔ 8cef540`（两跑收口）。** 两跑均 **仅 STEP[9]**；STEP[15] Swift / STEP[16] Motion gate / STEP[17] Capture gate / STEP[18] On-screen probe coverage / STEP[19] Motion coverage **全 success**（21a5440 的 STEP[18] frame/probe 红未再现）。STEP[9] 各 **4 红** = **3 条 git 缩写长度**（`test_recent_subjects_are_clean` / `test_roster_must_retire` / `test_the_second_label_source_is_a_derivation_not_a_roster`）+ **624** `skip_roster`；`test_the_cell_agrees_with_its_own_source` **绿**（sources 格已随台账笔更新）⇒ 21a5440 的 sources 红确认为**产品笔早于台账的时序**，不是缩写长度。**624 两臂更新**：`b707811`（台账笔）与 `8cef540`（收口笔）也红在 skip_roster ⇒ 本批「非台账笔红、台账笔绿」不再成立，保持开单、不改名册。
"""


def main():
    # 1. UI_AUDIT：区间扩到 U-2230；更正 U-2229 的计数；补 U-2230
    name = "AGENT_UI_AUDIT.md"
    text = rd(name)
    text = replace_once(
        text,
        u"## 第 537 轮（R538 · 2026-11-01 · U-2222…U-2229）",
        u"## 第 537 轮（R538 · 2026-11-01 · U-2222…U-2230）",
        u"ui title")
    old = u"STEP[9] 5 红 = **4 条 git 缩写长度**（runner `%h` 给 8 位 `21a5440f`、账上存 7 位 `21a5440`：`test_recent_subjects_are_clean` / `test_roster_must_retire` / `test_the_second_label_source_is_a_derivation_not_a_roster` / `test_the_cell_agrees_with_its_own_source`；5837d65 跑没有前三条）+ **624** `skip_roster`。"
    new = u"STEP[9] 5 红 = **3 条 git 缩写长度**（runner `%h` 给 8 位 `21a5440f`、账上存 7 位 `21a5440`：`test_recent_subjects_are_clean` / `test_roster_must_retire` / `test_the_second_label_source_is_a_derivation_not_a_roster`；5837d65 跑没有这三条）+ **1 条 sources 时序**（`test_the_cell_agrees_with_its_own_source`：产品笔早于台账；b707811/8cef540 已绿）+ **624** `skip_roster`。"
    text = replace_once(text, old, new, u"ui u2229 fix")
    text = append_after_line(text, u"- **U-2229：⓪ 补读", U2230, u"ui u2230")
    wr(name, text)

    # 2. BACKLOG：628 更正为 3 条；622/624 追加补读
    name = "AGENT_BACKLOG.md"
    text = rd(name)
    text = replace_once(
        text,
        u"**628. runner 的 git 缩写从 7 位变 8 位：四条脚本守卫把 7 位当固定长度**",
        u"**628. runner 的 git 缩写从 7 位变 8 位：三条脚本守卫把 7 位当固定长度**",
        u"b628 title")
    text = replace_once(
        text,
        u"STEP[9] 5 红中有 4 条同族：`test_recent_subjects_are_clean`（'5225de5' not found in ['21a5440f', … '5225de5a']）、`test_roster_must_retire`（[] != ['07acf2e', …]）、`test_the_second_label_source_is_a_derivation_not_a_roster`（git 里读不到 117f45d）、`test_the_cell_agrees_with_its_own_source`（报告格与 git 派生不一致）。",
        u"STEP[9] 5 红中有 3 条同族：`test_recent_subjects_are_clean`（'5225de5' not found in ['21a5440f', … '5225de5a']）、`test_roster_must_retire`（[] != ['07acf2e', …]）、`test_the_second_label_source_is_a_derivation_not_a_roster`（git 里读不到 117f45d）；第 4 条 `test_the_cell_agrees_with_its_own_source` 是产品笔早于台账的 sources 时序（b707811/8cef540 两跑已绿）。",
        u"b628 body")
    add622 = u"""    复查（R538 补读）：`41309008989 ↔ b707811`、`41309189054 ↔ 8cef540` 两跑的 STEP[17] Capture gate 也全 **success**（同样含 21a5440 的 code-block 两测试），STEP[18] 也全绿 ⇒ code-block 签收获两跑旁证，frame 半无新值。
"""
    text = append_after_line(text, u"复查（R538 收口复读）：`41308835299 ↔ 21a5440`", add622, u"b622b")
    add624 = u"""    复查（R538 补读）：`41309008989`（台账笔）与 `41309189054`（收口笔）的 STEP[9] 也红在 skip_roster ⇒ 本批「非台账笔红、台账笔绿」不再成立（三跑都红）；保持开单、不改名册。
"""
    text = append_after_line(text, u"复查（R538 收口复读）：`41308835299`（非台账产品笔）STEP[9] 仍红在 skip_roster", add624, u"b624b")
    wr(name, text)

    # 3. STATE：④ 计数更正 + 两跑补读 + 下一轮交接
    name = "AGENT_STATE.md"
    text = rd(name)
    old = u"STEP[18] = frame 151.4ms + `testRightClickMenusAppKitWouldShowAreChinese` 心跳未闭合（BACKLOG 132，6/14 探针没跑）；STEP[9] 5 红 = 4 条 git 缩写长度（runner `%h`=8 位 vs 账上 7 位）→ 新开 **BACKLOG 628** + 624 skip_roster，均非产品回归。"
    new = u"STEP[18] = frame 151.4ms + `testRightClickMenusAppKitWouldShowAreChinese` 心跳未闭合（BACKLOG 132，6/14 探针没跑）；STEP[9] 5 红 = **3 条 git 缩写长度**（runner `%h`=8 位 vs 账上 7 位）→ 新开 **BACKLOG 628** + 1 条 sources 时序（产品笔早于台账）+ 624 skip_roster，均非产品回归。**补读 `41309008989 ↔ b707811`、`41309189054 ↔ 8cef540`**：两跑均仅 STEP[9] 4 红（3 缩写 + 624），STEP[15]–[19] 全 success（frame/probe 红未再现，sources 格已绿）⇒ sources 时序只在产品笔跑；624 的「台账笔绿」本批不成立（两跑也红），保持开单。"
    text = replace_once(text, old, new, u"state 4 fix")
    wr(name, text)

    # 4. FINAL_REPORT：U 上界 + 计数更正 + 两跑
    name = "AGENT_FINAL_REPORT.md"
    text = rd(name)
    text = replace_once(text, u"| 视觉台账 | U-31 … U-2229", u"| 视觉台账 | U-31 … U-2230", u"fr u2")
    text = replace_once(
        text,
        u"同跑 STEP[9] 另开 4 条 git 缩写长度红（628）。",
        u"同跑 STEP[9] 另开 3 条 git 缩写长度红（628）+ 1 条 sources 时序；b707811/8cef540 两跑仅 STEP[9] 4 红（3 缩写 + 624），STEP[15]–[19] 全绿。",
        u"fr bullet fix")
    wr(name, text)

    # 5. ITERATION：更正 4→3 并补两跑
    name = "AGENT_VISUAL_ITERATION.md"
    text = rd(name)
    old = u"STEP[9] 5 红 = 4 条 git 缩写长度（runner `%h`=8 位 vs 账上 7 位）→ 新开 BACKLOG 628 + 624 skip_roster；不是产品回归。"
    new = u"STEP[9] 5 红 = 3 条 git 缩写长度（runner `%h`=8 位 vs 账上 7 位）→ 新开 BACKLOG 628 + 1 条 sources 时序 + 624 skip_roster；不是产品回归。另补读 `b707811`/`8cef540` 两跑：均仅 STEP[9] 4 红（3 缩写 + 624），STEP[15]–[19] 全 success，sources 格绿 ⇒ 时序只在产品笔跑；624 台账笔本批也红。"
    text = replace_once(text, old, new, u"iter fix")
    wr(name, text)

    sys.stdout.write("LEDGERS_R538_ADDENDUM2_OK\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
