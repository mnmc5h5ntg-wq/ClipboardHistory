#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R303：把「Swift 那张按文件的读数名册」读成数，只留这一份解析（同一个估计量）。

为什么单独一支：本轮把 `UIInteractionProbeTests.swift` 的 15 行搬进 `CaptureReadings.emit` 之后，
那张按 `print("` 找读数的名册对搬走的读数瞎了（刀 M731 先 ESCAPED 才暴露，见 D-284）。
名册改成按通道读之后，**台账要引用的数（合计多少行、覆盖几份文件、探针那份几种标记）**
就不该由人手抄进生成器 —— 手抄的那一份会随 Swift 源码漂移，和 needle 腐烂是同一族。
`scripts/tests/test_readings_channel_coverage.py` 与本文件的 `ledgers_r303.py` 都从这里取，
所以两边数的必然是同一个东西。
"""
import io
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SWIFT_ROSTER = os.path.join(ROOT, "ClipboardHistory", "Tests", "ClipboardHistoryAppTests",
                            "FrameIntervalBudgetTests.swift")
PROBE_FILE = "UIInteractionProbeTests.swift"


def _block(text, opener, closer):
    i = text.index(opener) + len(opener)
    j = text.index(closer, i)
    return text[i:j]


def swift_roster_readings(path=SWIFT_ROSTER):
    """从 Swift 源码里读出名册的三个数；解析不出来一律抛错（不许给默认值）。"""
    text = io.open(path, encoding="utf-8").read()
    total = re.search(r"XCTAssertEqual\(total,\s*(\d+)", text)
    if not total:
        raise ValueError("读不到 XCTAssertEqual(total, N) ⇒ 那张名册的形状漂了")
    reg = _block(text, "let registered: [String: [String]] = [", "\n        ]")
    files = re.findall(r'"([\w.]+\.swift)":', reg)
    if not files:
        raise ValueError("registered 名册里没有文件键 ⇒ 名册空转")
    probe_block = _block(reg, '"' + PROBE_FILE + '": [', "]")
    markers = re.findall(r'"([^"]+)"', probe_block)
    counts = _block(text, "let counts: [String: Int] = [", "\n        ]")
    probe_lines = re.search(r'"' + re.escape(PROBE_FILE) + r'":\s*(\d+)', counts)
    if not probe_lines:
        raise ValueError("counts 表里没有探针文件的行数 ⇒ 两张表不同源")
    return {
        "total": int(total.group(1)),
        "files": len(files),
        "probe_markers": len(set(markers)),
        "probe_lines": int(probe_lines.group(1)),
    }


if __name__ == "__main__":
    r = swift_roster_readings()
    print("ROSTER_READINGS swift_total=%(total)d swift_files=%(files)d "
          "probe_lines=%(probe_lines)d probe_markers=%(probe_markers)d" % r)
