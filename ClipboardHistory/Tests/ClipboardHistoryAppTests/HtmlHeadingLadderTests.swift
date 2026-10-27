import AppKit
import XCTest
@testable import ClipboardHistoryApp

/// R434：HTML 的标题档必须落在 Markdown 同一条梯子上（正文已经搬过，标题也要搬）。
@MainActor
final class HtmlHeadingLadderTests: XCTestCase {
    private func page(_ headings: [CGFloat], body: CGFloat = 14, bodyChars: Int = 200) -> NSAttributedString {
        let out = NSMutableAttributedString()
        for size in headings {
            out.append(NSAttributedString(string: "标题", attributes: [
                .font: NSFont.systemFont(ofSize: size, weight: .bold),
            ]))
        }
        out.append(NSAttributedString(string: String(repeating: "正", count: bodyChars), attributes: [
            .font: NSFont.systemFont(ofSize: body),
        ]))
        return out
    }

    private func sizes(_ text: NSAttributedString) -> [CGFloat] {
        var result: [CGFloat] = []
        text.enumerateAttribute(.font, in: NSRange(location: 0, length: text.length)) { value, _, _ in
            if let font = value as? NSFont { result.append(font.pointSize) }
        }
        return result
    }

    func testHeadingsLandOnTheMarkdownLadder() {
        let fitted = HtmlRendering.fitHeadingsToLadder(page([28, 21, 16.5]))
        let got = sizes(fitted)
        XCTAssertEqual(got[0], MarkdownPresentation.headingFontSize(level: 1), accuracy: 0.01,
                       "HTML 的 h1 没有落到 Markdown 的 h1 那一档")
        XCTAssertEqual(got[1], MarkdownPresentation.headingFontSize(level: 2), accuracy: 0.01,
                       "HTML 的 h2 没有落到 Markdown 的 h2 那一档")
        XCTAssertEqual(got[2], MarkdownPresentation.headingFontSize(level: 3), accuracy: 0.01,
                       "HTML 的 h3 没有落到 Markdown 的 h3 那一档")
        XCTAssertEqual(got[3], 14, accuracy: 0.01, "正文被标题映射改动了")
    }

    func testPagesWithoutHeadingsAreNotTouched() {
        let input = page([])
        let fitted = HtmlRendering.fitHeadingsToLadder(input)
        XCTAssertEqual(sizes(fitted), sizes(input),
                       "没有标题的页面被改动了 ⇒ 映射把正文误当标题")
    }

    func testEmptyOrUnreadableBaseIsIdentity() {
        let empty = NSAttributedString(string: "")
        XCTAssertEqual(HtmlRendering.fitHeadingsToLadder(empty).length, 0)
    }
}
