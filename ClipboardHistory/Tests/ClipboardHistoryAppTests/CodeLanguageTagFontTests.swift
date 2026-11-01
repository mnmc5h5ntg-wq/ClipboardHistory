import AppKit
import XCTest
@testable import ClipboardHistoryApp

/// R537：代码语言标签的字体必须具体、缓存。
/// 622 的第二次崩溃栈在 CoreText `TAttributes::ApplyFont`（`sizeWithAttributes:` 内插 nil），
/// 旧值用的是系统 UI 等宽字体；本机 10/10 不复现，这条只钉「字体是具体 PostScript 名」这一半。
final class CodeLanguageTagFontTests: XCTestCase {
    func testFontIsConcreteCachedMenloBold() {
        XCTAssertEqual(CodeLanguageTag.font.fontName, "Menlo-Bold",
                       "代码语言标签必须用具体 PostScript 名的 Menlo-Bold"
                       + "（旧系统等宽字体在 runner 的 CoreText ApplyFont 偶发插 nil）")
        XCTAssertTrue(CodeLanguageTag.font === CodeLanguageTag.font,
                      "字体必须是缓存的静态 let，不能每次新建")
    }
}
