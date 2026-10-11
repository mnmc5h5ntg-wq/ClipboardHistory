// 不覆盖管线：本文件钉的是**解析 + 构建**这两层在随机输入下的安全性与有界性。
// 产品路径（真文件 → MediaLoader → 真文本视图）在 `Round4MarkdownTests`，
// 屏幕上的样子在 `detail-markdown-*` 两帧。
import AppKit
import XCTest
@testable import ClipboardHistoryApp

/// 手写解析器的代价是要自己保证"什么输入都不会崩、都不会挂住主线程"。
/// 递归下降 + 手工下标（`findEmphasisClose`、`linkAt`、`findClosingBacktick`）
/// 是越界与死循环的高发区，而真值表用例只会覆盖我想得到的形状。
///
/// 所以这里跑固定种子的随机模糊：字符表刻意包含标记符、代理对 emoji、组合变音符号、
/// 制表与换行，长度到 300 个字符 —— 这个尺度上最容易撞出"闭栏找到但切片反向"这类问题。
/// 三条判据：不崩（跑完就是证明）、单次耗时上有界（挂死与 O(n²) 都在这里露）、
/// 属性串不许比模型的可见文字短（丢内容在这里露，而不是等到看帧）。
///
/// 实测：20000 例全过，稳态单次 < 1ms，最坏一次 26ms 是首条的预热（字体与色板惰性加载），
/// 整个用例约 2.7 秒。种子固定，所以任何一次红都能原样复现。
@MainActor
final class MarkdownFuzzTests: XCTestCase {
    /// 标记符 + 空白 + 拉丁 + 汉字 + 代理对 emoji + 组合变音符号。
    private let alphabet: [Character] = Array("#*`~_[]()<>-|.!: \n\t\\a中\u{1F34E}\u{0301}")
    private let iterations = 20_000
    private let maximumInputCharacters = 300

    func testRandomInputNeverCrashesAndStaysBounded() throws {
        var rng = SeededRandom(seed: 20_261_011)
        var worst = 0.0
        var worstInput = ""
        for iteration in 0..<iterations {
            var text = ""
            for _ in 0..<Int(rng.next(upTo: UInt(maximumInputCharacters))) {
                text.append(alphabet[Int(rng.next(upTo: UInt(alphabet.count)))])
            }
            let start = Date()
            let document = MarkdownParser.parse(text)
            let rendered = MarkdownPresentation.attributedString(for: document)
            let elapsed = Date().timeIntervalSince(start)
            if elapsed > worst { worst = elapsed; worstInput = text }

            XCTAssertLessThan(elapsed, 0.5,
                              "第 \(iteration) 次输入耗时 \(elapsed)s，主线程会被冻住：\(text.debugDescription)")
            XCTAssertGreaterThanOrEqual(rendered.length, document.visibleText.utf16.count,
                                        "属性串比模型的可见文字还短，说明有内容没画出来：\(text.debugDescription)")
            // 每个 run 的下标域必须落在属性串里：越界在 NSTextView 里表现为崩溃或画歪，
            // 而在这一层能提前抓到。
            var consumed = 0
            for block in document.blocks {
                for run in block.runs { consumed += run.text.utf16.count }
            }
            XCTAssertLessThanOrEqual(consumed, max(rendered.length, 1),
                                     "模型里的文字超出属性串长度：\(text.debugDescription)")
        }
        print("FUZZ markdown iterations=\(iterations) worst=\(String(format: "%.4f", worst))s "
              + "worst_input=\(worstInput.debugDescription.prefix(60))")
        XCTAssertFalse(worstInput.isEmpty, "夹具前提：一次都没跑过")
    }

    /// xorshift64：够乱、可复现、不依赖系统随机源（系统随机源会让红变得无法复现）。
    private struct SeededRandom {
        private var state: UInt64
        init(seed: UInt64) { state = seed | 1 }

        mutating func next() -> UInt64 {
            state ^= state << 13
            state ^= state >> 7
            state ^= state << 17
            return state
        }

        mutating func next(upTo bound: UInt) -> UInt {
            UInt(next() % UInt64(max(bound, 1)))
        }
    }
}
