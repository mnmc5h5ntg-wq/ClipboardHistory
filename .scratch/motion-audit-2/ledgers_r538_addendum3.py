#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R538 补记四：085e4c7 跑补读（628 第三例、624 第三例）。"""
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


U2231 = u"""- **U-2231：⓪ 补读 `41309333668 ↔ 085e4c7`（R538 ⓪ 笔）。** 仅 **STEP[9]** 4 红（**3 条 git 缩写长度** + **624** `skip_roster`），STEP[15]/[16]/[17]/[18]/[19] 全 **success**，sources 格绿（本笔没动它）⇒ 628 在三个台账/收口笔上稳定复现；624 的台账/⓪ 笔也红（同一批第三例）。不是产品回归。
"""


def main():
    # 1. UI_AUDIT
    name = "AGENT_UI_AUDIT.md"
    text = rd(name)
    text = replace_once(
        text,
        u"## 第 537 轮（R538 · 2026-11-01 · U-2222…U-2230）",
        u"## 第 537 轮（R538 · 2026-11-01 · U-2222…U-2231）",
        u"ui title")
    text = append_after_line(text, u"- **U-2230：⓪ 补读", U2231, u"ui u2231")
    wr(name, text)

    # 2. BACKLOG：628/624 追加 085e4c7
    name = "AGENT_BACKLOG.md"
    text = rd(name)
    old = u"`5837d65` 的跑没有前三条（当时 `%h` 还是 7 位），所以这不是产品回归。"
    new = u"`5837d65` 的跑没有前三条（当时 `%h` 还是 7 位），所以这不是产品回归。同一批 `085e4c7`（⓪ 笔）也复现同样 3 条 + skip_roster。"
    text = replace_once(text, old, new, u"b628 085")
    add624 = u"""    复查（R538 补读二）：`41309333668 ↔ 085e4c7`（⓪ 笔）STEP[9] 也红在 skip_roster ⇒ 同一批台账/⓪/收口三笔都红，非台账笔红/台账笔绿的旧相关不成立；保持开单、不改名册。
"""
    text = append_after_line(text, u"复查（R538 补读）：`41309008989`（台账笔）与 `41309189054`（收口笔）", add624, u"b624c")
    wr(name, text)

    # 3. STATE
    name = "AGENT_STATE.md"
    text = rd(name)
    old = u"**补读 `41309008989 ↔ b707811`、`41309189054 ↔ 8cef540`**：两跑均仅 STEP[9] 4 红（3 缩写 + 624），STEP[15]–[19] 全 success（frame/probe 红未再现，sources 格已绿）⇒ sources 时序只在产品笔跑；624 的「台账笔绿」本批不成立（两跑也红），保持开单。"
    new = u"**补读 `41309008989 ↔ b707811`、`41309189054 ↔ 8cef540`、`41309333668 ↔ 085e4c7`**：三跑均仅 STEP[9] 4 红（3 缩写 + 624），STEP[15]–[19] 全 success（frame/probe 红未再现，sources 格已绿）⇒ sources 时序只在产品笔跑；624 的「台账笔绿」本批不成立（三跑也红），保持开单。"
    text = replace_once(text, old, new, u"state 4 085")
    wr(name, text)

    # 4. FINAL_REPORT U 上界
    name = "AGENT_FINAL_REPORT.md"
    text = rd(name)
    text = replace_once(text, u"| 视觉台账 | U-31 … U-2230", u"| 视觉台账 | U-31 … U-2231", u"fr u3")
    wr(name, text)

    # 5. ITERATION
    name = "AGENT_VISUAL_ITERATION.md"
    text = rd(name)
    old = u"另补读 `b707811`/`8cef540` 两跑：均仅 STEP[9] 4 红（3 缩写 + 624），STEP[15]–[19] 全 success，sources 格绿 ⇒ 时序只在产品笔跑；624 台账笔本批也红。"
    new = u"另补读 `b707811`/`8cef540`/`085e4c7` 三跑：均仅 STEP[9] 4 红（3 缩写 + 624），STEP[15]–[19] 全 success，sources 格绿 ⇒ 时序只在产品笔跑；624 台账/⓪ 笔本批也红。"
    text = replace_once(text, old, new, u"iter 085")
    wr(name, text)

    sys.stdout.write("LEDGERS_R538_ADDENDUM3_OK\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
