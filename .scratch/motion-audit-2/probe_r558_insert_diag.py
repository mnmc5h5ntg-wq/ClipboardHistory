# -*- coding: utf-8 -*-
"""R558 一次性探针：往 MotionFilmstripTests 里插一格临时诊断，读「这卷胶片到底在动哪一块」。

用完就撤（不入库、不是判据）：它只负责**形成问题**，结论要由量它的仪器进仓库之后才配写进台账。
"""
import io
import os
import sys

ROOT = "/Users/wangziyi/Codex_Project0"
P = os.path.join(ROOT, "ClipboardHistory/Tests/ClipboardHistoryAppTests/MotionFilmstripTests.swift")

DIAG = u"""
    func testR558ProbeWhereTheFilmChanges() throws {
        try skipUnlessEnabledAndCapable()
        let scenario = Scenario.markdownModeLabel()
        let film = record(scenario, scale: 1.0)
        let frames = film.motionFrames
        let bitmaps = frames.map(raster)
        for index in 1..<min(10, bitmaps.count) {
            let a = bitmaps[index - 1]
            let b = bitmaps[index]
            var rows = Set<Int>()
            var cols = Set<Int>()
            var hits = 0
            var y = 0
            while y < a.height {
                var x = 0
                while x < a.width {
                    let p = (y * a.width + x) * 4
                    let rgb = max(abs(Int(a.pixels[p]) - Int(b.pixels[p])),
                                  max(abs(Int(a.pixels[p + 1]) - Int(b.pixels[p + 1])),
                                      abs(Int(a.pixels[p + 2]) - Int(b.pixels[p + 2]))))
                    let alpha = abs(Int(a.pixels[p + 3]) - Int(b.pixels[p + 3]))
                    if rgb > 8 || alpha > 8 {
                        hits += 1
                        rows.insert(y)
                        cols.insert(x)
                    }
                    x += 1
                }
                y += 1
            }
            let rowSpan = rows.isEmpty ? "无" : "\\(rows.min()!)…\\(rows.max()!)"
            let colSpan = cols.isEmpty ? "无" : "\\(cols.min()!)…\\(cols.max()!)"
            emit("R558PROBE 帧对=\\(index - 1)→\\(index) 尺寸=\\(a.width)x\\(a.height) 变化像素=\\(hits) 行带=[\\(rowSpan)] 列带=[\\(colSpan)]")
        }
        for index in 1..<min(10, bitmaps.count) {
            let b = bitmaps[index]
            var ink = 0
            var lumaHist = [Int](repeating: 0, count: 0)
            _ = lumaHist
            var y = 0
            while y < b.height {
                var x = 0
                while x < b.width {
                    let p = (y * b.width + x) * 4
                    let luma = (Int(b.pixels[p]) * 299 + Int(b.pixels[p + 1]) * 587 + Int(b.pixels[p + 2]) * 114) / 1000
                    if luma < 120 { ink += 1 }
                    x += 2
                }
                y += 2
            }
            emit("R558PROBE 帧=\\(index) 暗墨像素=\\(ink)")
        }
    }
"""


def main():
    check = "--check" in sys.argv
    text = io.open(P, encoding="utf-8").read()
    anchor = u"    /// R558 / 629：新口径的**合成真值表**"
    if text.count(anchor) != 1:
        sys.stderr.write("ANCHOR_BAD hits=%d\n" % text.count(anchor))
        return 1
    if check:
        print("PROBE_ANCHOR_OK")
        return 0
    io.open(P, "w", encoding="utf-8").write(text.replace(anchor, DIAG + u"\n" + anchor, 1))
    print("PROBE_INSERTED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
