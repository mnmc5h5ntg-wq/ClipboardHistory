#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R541 补记二：d984ab7 的 622 第七值 176.6ms/2/204。"""
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


U2259 = u"""- **U-2259：⓪ 补读 `41318294600 ↔ d984ab7`（R541 ⓪ 笔）。** failure **仅 STEP[18]**：`testFrameIntervalsUnderStateChanges` 最差 **176.6ms**、超锚点 **2/204**、loaded_p95=16.67、比值 1.000 ⇒ **622 第七值**（544.1→162.2→175.8→243.2→151.4→262.3→176.6）；另 `testRightClickMenusAppKitWouldShowAreChinese` 心跳未闭合（BACKLOG 132）、6/14 探针没跑。120ms 与容差不动，frame 半保持开单。
"""


def main():
    name = "AGENT_UI_AUDIT.md"
    text = rd(name)
    text = replace_once(text,
                        u"## 第 540 轮（R541 · 2026-11-01 · U-2250…U-2258）",
                        u"## 第 540 轮（R541 · 2026-11-01 · U-2250…U-2259）",
                        u"ui title")
    text = append_after_line(text, u"- **U-2258：⑥ 收口与交接。**", U2259, u"ui u2259")
    wr(name, text)

    name = "AGENT_BACKLOG.md"
    text = rd(name)
    add622 = u"""    复查（R541 收口）：`41318294600 ↔ d984ab7` 的 STEP[18] 最差 **176.6ms/2/204**（loaded_p95=16.67、比值 1.000）⇒ 第七值（544.1→162.2→175.8→243.2→151.4→262.3→176.6）；120ms/容差不动、frame 半保持开单。
"""
    text = append_after_line(text, u"复查（R541）：40 跑 `FRAME_MULTI`", add622, u"b622r541b")
    wr(name, text)

    name = "AGENT_FINAL_REPORT.md"
    text = rd(name)
    text = replace_once(text, u"| 视觉台账 | U-31 … U-2258", u"| 视觉台账 | U-31 … U-2259", u"fr u")
    text = replace_once(
        text,
        u"627 保持开单，新开 629；624 保持开单。\n",
        u"627 保持开单，新开 629；624 保持开单；`d984ab7` 的 STEP[18] 再读 176.6ms/2/204（622 第七值，120ms/容差不动）。\n",
        u"fr bullet")
    wr(name, text)

    name = "AGENT_STATE.md"
    text = rd(name)
    old = u"`41318132821 ↔ 172d8de`、`41318294600 ↔ d984ab7` 读时 in_progress ⇒ NOT-RUN；`41320804339 ↔ 7353513` queued ⇒ NOT-RUN。"
    new = u"`41318132821 ↔ 172d8de` **success**；`41318294600 ↔ d984ab7` failure **仅 STEP[18]**（`testFrameIntervalsUnderStateChanges` **176.6ms/2/204** ⇒ 622 第七值 544.1→162.2→175.8→243.2→151.4→262.3→176.6；另右击探针心跳未闭合/BACKLOG 132）；`41320804339 ↔ 7353513` in_progress、`41321009857 ↔ cc15c76` queued ⇒ NOT-RUN。"
    text = replace_once(text, old, new, u"state 5")
    wr(name, text)

    sys.stdout.write("LEDGERS_R541_ADDENDUM_OK\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
