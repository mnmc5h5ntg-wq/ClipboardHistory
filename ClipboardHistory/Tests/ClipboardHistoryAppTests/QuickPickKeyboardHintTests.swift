import AppKit
import CoreText
import XCTest
@testable import ClipboardHistoryApp

/// 不覆盖管线：这是提示文案的键名几何判据；提示标签接入 QuickPick 面板的管线证人
/// 在 `UICaptureHarness.testQuickPickShowsKeyboardHints`（视图树 + 帧底带有墨）。
final class QuickPickKeyboardHintTests: XCTestCase {

    /// R550：提示里关闭键写成小写 `esc`，键名像普通单词、x-height 只有 5.99pt。
    /// 改成 `Esc` 后大写 E 的 cap height 必须 ≥7pt；文本本身也必须用大写键名。
    func testCloseKeyUsesAnUppercaseKeyNameWithReadableCaps() {
        XCTAssertTrue(QuickPickKeyboardHint.text.contains("Esc 关闭"),
                      "提示里没有大写键名「Esc 关闭」：\(QuickPickKeyboardHint.text)")
        XCTAssertFalse(QuickPickKeyboardHint.text.contains("esc 关闭"),
                       "提示仍在用小写键名：\(QuickPickKeyboardHint.text)")

        let font = QuickPickKeyboardHint.font
        let word = Array("Esc".utf16)
        var glyphs = [CGGlyph](repeating: 0, count: word.count)
        CTFontGetGlyphsForCharacters(font as CTFont, word, &glyphs, word.count)
        var rects = [CGRect](repeating: .zero, count: glyphs.count)
        CTFontGetBoundingRectsForGlyphs(font as CTFont, .horizontal, glyphs, &rects, glyphs.count)
        let union = rects.reduce(CGRect.null) { $0.union($1) }
        CaptureReadings.emit("HINT_KEY_CAPS 键=Esc 高=\(String(format: "%.2f", union.height))pt"
            + " 宽=\(String(format: "%.2f", union.width))pt 字号=\(font.pointSize)pt")
        XCTAssertGreaterThanOrEqual(union.height, 7.0,
            "键名墨高只有 \(String(format: "%.2f", union.height))pt ⇒ 还是小写 x-height，不是键名")
    }
}
