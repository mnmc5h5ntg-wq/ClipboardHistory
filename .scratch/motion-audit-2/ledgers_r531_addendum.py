#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R531 收口后 CI 复读补记：只补台账。"""
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


def main():
    # 1. UI_AUDIT：U-2179 尾部追加收口复读
    name = "AGENT_UI_AUDIT.md"
    text = rd(name)
    old = u"下一轮 R532（第 531 轮 / Round 529）：先 push 并复核 ahead=0；继续折叠特性；安全红线不变。\n"
    new = old.rstrip(u"\n") + u" 收口后复读四跑：`41286598804 ↔ 02fa144` **STEP[9]+[15]+[17]**（STEP[9]=sources/streak 时序 + skip_roster；STEP[15]/[17]=旧 hover 0/0）；`41287008886 ↔ ac04e2d` 与 `41287270623 ↔ 76b24b8` **仅 STEP[15]+[17]**（hover 0/0，STEP[9] 绿）；`41287495651 ↔ a13636a` **STEP[9]+[15]+[17]**（STEP[9]=指针/streak/citations 时序 + skip_roster；hover 0/0）。skip_roster 在 ac04e2d/76b24b8 绿、其余五跑红 ⇒ 间歇性 runner flake，624 记两臂；`9bfd943`/`adb50c1` 读时 in_progress/queued ⇒ NOT-RUN。\n"
    text = replace_once(text, old, new, u"ui2179")
    wr(name, text)

    # 2. STATE：R531 ③ 追加复读
    name = "AGENT_STATE.md"
    text = rd(name)
    old = u"下一轮编号 R532（第 531 轮 / Round 529）：先 push 并复核 ahead=0；继续折叠特性；4.5 地板与 150 上限不动。\n"
    new = old.rstrip(u"\n") + u"\n④ 收口后 CI 复读：`02fa144` STEP[9]+[15]+[17]（sources/streak 时序 + skip_roster；旧 hover 0/0）、`ac04e2d`/`76b24b8` 仅 STEP[15]+[17]（hover 0/0，STEP[9] 绿）、`a13636a` STEP[9]+[15]+[17]（指针/streak/citations 时序 + skip_roster；hover 0/0）。skip_roster 五红两绿（ac04e2d/76b24b8 绿）⇒ 间歇性 runner flake，624 记两臂；`9bfd943`/`adb50c1` 读时 in_progress/queued ⇒ NOT-RUN。\n"
    text = replace_once(text, old, new, u"state4")
    wr(name, text)

    # 3. BACKLOG 624：两臂追记
    name = "AGENT_BACKLOG.md"
    text = rd(name)
    add = u"""    复查（R531 收口）：同一卷在 `ac04e2d`/`76b24b8` 两跑 STEP[9] **绿**，在 `2e7272e`/`1e3cfaa`/`730dc5e`/`02fa144`/`a13636a` 五跑红 ⇒ **间歇性 runner flake**（不是稳定环境红）；两臂都记，继续按「内层退出码/尾部输出落盘」定位，不销单、不改名册。
"""
    text = append_after_line(text, u"下一步：在 runner 上让内层 subprocess 的退出码与尾部输出落盘", add, u"backlog624")
    wr(name, text)

    # 4. FINAL_REPORT：§18 R531 那一条补复读读数
    name = "AGENT_FINAL_REPORT.md"
    text = rd(name)
    anchor = u"622 本机 4 跑未复现，具名 flake；折叠焦点负向证人通过。"
    new = anchor + u" 收口后：02fa144 STEP[9]+[15]+[17]、ac04e2d/76b24b8 仅 STEP[15]+[17]（hover 0/0、STEP[9] 绿）、a13636a STEP[9]+[15]+[17]；skip_roster 五红两绿 ⇒ 624 记间歇 flake。"
    text = replace_once(text, anchor, new, u"final18")
    wr(name, text)

    sys.stdout.write("LEDGERS_R531_ADDENDUM_OK\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
