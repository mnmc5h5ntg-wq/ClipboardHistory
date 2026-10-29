import AppKit
import XCTest
@testable import ClipboardHistoryApp

/// R440：表格表头字重。
///
/// 属性串这一层只换字体（等宽 semibold），不动推进宽度；像素那一半在
/// `UICaptureTests.testTableHeadersAreSemibold` —— 它读 `detail-table` 帧上
/// 表头行与表体行的墨量比（同字同字号的两行，只有字重不同）。
@MainActor
final class TableHeaderPresentationTests: XCTestCase {
    func testHeaderRangeIsTheFirstLineOnly() {
        let two = TableHeaderPresentation.headerRange(in: "甲 | 乙\n甲 | 乙")
        XCTAssertEqual(two?.location, 0)
        XCTAssertEqual(two?.length, 5)
        XCTAssertEqual(TableHeaderPresentation.headerRange(in: "没有换行")?.length, 4)
        XCTAssertNil(TableHeaderPresentation.headerRange(in: ""))
        XCTAssertNil(TableHeaderPresentation.headerRange(in: "\n表体"))
    }

    func testHeaderFontIsMonospacedSemiboldAtTheCodeSize() {
        let font = TableHeaderPresentation.headerFont
        XCTAssertTrue(font.isFixedPitch, "表头字体不是等宽 ⇒ 加粗会挪列")
        XCTAssertEqual(font.pointSize, MarkdownPresentation.codeFontSize, accuracy: 0.01)
        XCTAssertTrue(NSFontManager.shared.traits(of: font).contains(.boldFontMask),
                      "表头字体没有粗体特征 ⇒ 与表体分不开")
        XCTAssertFalse(NSFontManager.shared.traits(of: MarkdownPresentation.codeFont).contains(.boldFontMask),
                       "表体字体本来就带粗体 ⇒ 这一档对比没有对象")
    }

    /// 产品入口：同一段带表格的 Markdown 里，第一行（表头）是 semibold、第二行（表体）不是；
    /// 表格之外的段落也不被这条规则碰到。
    func testOnlyTheTableHeaderGetsTheSemiboldFont() {
        let source = """
        # 表

        | 甲 | 乙 |
        | --- | --- |
        | 甲 | 乙 |

        正文段落
        """
        let attributed = MarkdownPresentation.attributedString(for: MarkdownParser.parse(source))
        let text = attributed.string as NSString

        func font(at needle: String, from location: Int = 0) -> NSFont? {
            let range = text.range(of: needle, options: [], range: NSRange(location: location,
                                                                          length: text.length - location))
            guard range.location != NSNotFound else { return nil }
            return attributed.attribute(.font, at: range.location, effectiveRange: nil) as? NSFont
        }

        // R487：渲染态已把 `|` 换成同宽空格 ⇒ 表格行的新形状是 `甲   乙`。
        let tableRow = "甲   乙"
        let firstRange = text.range(of: tableRow)
        guard firstRange.location != NSNotFound else {
            return XCTFail("属性串里找不到表格首行 ⇒ 这条判据没有对象")
        }
        let first = firstRange.location
        guard let header = font(at: tableRow, from: first),
              let body = font(at: tableRow, from: first + 1),
              let paragraph = font(at: "正文段落") else {
            return XCTFail("属性串里找不到表头/表体/段落 ⇒ 这条判据没有对象")
        }
        XCTAssertTrue(NSFontManager.shared.traits(of: header).contains(.boldFontMask),
                      "表头不是 semibold")
        XCTAssertFalse(NSFontManager.shared.traits(of: body).contains(.boldFontMask),
                       "表体被一起加粗了 ⇒ 表头/表体仍然同形")
        XCTAssertFalse(NSFontManager.shared.traits(of: paragraph).contains(.boldFontMask),
                       "普通段落被表格规则误伤")
        XCTAssertEqual(header.pointSize, body.pointSize, accuracy: 0.01)
        XCTAssertEqual(header.isFixedPitch, body.isFixedPitch)
    }
}
