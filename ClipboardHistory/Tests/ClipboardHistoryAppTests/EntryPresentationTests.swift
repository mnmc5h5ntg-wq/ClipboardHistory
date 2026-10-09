import AppKit
import XCTest
@testable import ClipboardHistoryApp

final class EntryPresentationTests: XCTestCase {
    func testTextPreviewReplacesNewlinesAndTruncatesLongText() {
        let text = String(repeating: "a", count: 30) + "\n" + String(repeating: "b", count: 40)

        let preview = EntryPresentation.preview(for: .text(text))

        XCTAssertTrue(preview.contains(" ↵ "))
        XCTAssertEqual(preview.count, 61)
        XCTAssertTrue(preview.hasSuffix("…"))
    }

    func testSizeDescriptionForText() {
        XCTAssertEqual(
            EntryPresentation.sizeDescription(for: .text("hello")),
            "5 个字符"
        )
    }

    func testSizeDescriptionForFilesHidesFullPath() {
        let url = URL(fileURLWithPath: "/Users/me/private/report.pdf")

        let description = EntryPresentation.sizeDescription(for: .file(url))

        XCTAssertEqual(description, "文件: report.pdf")
        XCTAssertFalse(description.contains("/Users/me/private"))
    }

    func testFileNamePartsSplitsExtensionAndUsesFallbackForHiddenFile() {
        let fileURL = URL(fileURLWithPath: "/tmp/report.final.pdf")
        let hiddenURL = URL(fileURLWithPath: "/tmp/.gitignore")

        let fileParts = EntryPresentation.fileNameParts(for: fileURL)
        let hiddenParts = EntryPresentation.fileNameParts(for: hiddenURL)

        XCTAssertEqual(fileParts.baseName, "report.final")
        XCTAssertEqual(fileParts.fileExtension, "pdf")
        XCTAssertEqual(fileParts.displayBaseName, "report.final")
        XCTAssertEqual(hiddenParts.displayBaseName, ".gitignore")
    }

    func testMenuTitleTruncatesTextAndUsesFileName() {
        let textEntry = makeClipboardEntry(
            content: .text("line one\n" + String(repeating: "a", count: 80))
        )
        let fileEntry = makeClipboardEntry(
            content: .file(URL(fileURLWithPath: "/tmp/report.pdf"))
        )

        XCTAssertEqual(EntryPresentation.menuTitle(for: textEntry, maxLength: 12), "line one aa…")
        XCTAssertEqual(EntryPresentation.menuTitle(for: fileEntry), "report.pdf")
    }

    // MARK: - 有界字符计数（审计第二轮 B-3 / R2-11）

    func testCharacterCountStopsAtTheLimit() {
        XCTAssertEqual(EntryPresentation.characterCount(of: "abc", limit: 3), 3, "刚好到上限仍给准确值")
        XCTAssertNil(EntryPresentation.characterCount(of: "abcd", limit: 3), "超过上限返回 nil，由文案说“超过”")
        XCTAssertEqual(EntryPresentation.characterCount(of: "", limit: 3), 0)
        XCTAssertNil(EntryPresentation.characterCount(of: "aaaaa", limit: 0), "上限为 0 时任何非空串都算超限")
    }

    func testSizeDescriptionStillCountsGraphemesNotScalars() {
        // 换实现不许换语义：显示给用户的一直是"字素数"，
        // 所以 ZWJ 家庭 emoji 是 1 个字符，不是 5 个 scalar。
        XCTAssertEqual(EntryPresentation.sizeDescription(for: .text("👨‍👩‍👧")), "1 个字符")
        XCTAssertEqual(EntryPresentation.characterCount(of: "é"), 1)
        XCTAssertEqual(EntryPresentation.sizeDescription(for: .text("hello")), "5 个字符")
    }

    func testSizeDescriptionFallsBackToTheBoundForHugeText() {
        let limit = EntryPresentation.sizeCountLimit
        let huge = String(repeating: "a", count: limit + 1)
        XCTAssertEqual(EntryPresentation.sizeDescription(for: .text(huge)), "超过 \(limit) 个字符")

        let exactlyAtLimit = String(repeating: "a", count: limit)
        XCTAssertEqual(EntryPresentation.sizeDescription(for: .text(exactlyAtLimit)), "\(limit) 个字符",
                       "边界值必须给准确数字，不能提前退化")
    }

}
