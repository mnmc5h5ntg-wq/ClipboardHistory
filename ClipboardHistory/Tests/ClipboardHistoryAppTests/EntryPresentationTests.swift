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

    func testPrivateMenuTitleHidesTextAndFileName() {
        let textEntry = makeClipboardEntry(content: .text("secret token 123"))
        let fileEntry = makeClipboardEntry(
            content: .file(URL(fileURLWithPath: "/Users/me/private/report.pdf")),
            isFavorite: true
        )

        XCTAssertEqual(EntryPresentation.privateMenuTitle(for: textEntry), "最近文本记录")
        XCTAssertEqual(EntryPresentation.privateMenuTitle(for: fileEntry), "收藏文件记录")
        XCTAssertFalse(EntryPresentation.privateMenuTitle(for: textEntry).contains("secret"))
        XCTAssertFalse(EntryPresentation.privateMenuTitle(for: fileEntry).contains("report.pdf"))
    }

    func testMenuSymbolUsesFavoriteStarBeforeContentType() {
        let entry = makeClipboardEntry(content: .text("saved"), isFavorite: true)

        XCTAssertEqual(EntryPresentation.menuSymbol(for: entry), "star.fill")
    }
}
