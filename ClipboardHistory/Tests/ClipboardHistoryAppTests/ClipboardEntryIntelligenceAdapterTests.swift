import XCTest
@testable import ClipboardHistoryApp

final class ClipboardEntryIntelligenceAdapterTests: XCTestCase {
    private let adapter = ClipboardEntryIntelligenceAdapter()

    func testSummaryKeepsEntryIdentityAndSearchablePreview() {
        let id = UUID()
        let entry = ClipboardEntry(
            id: id,
            content: .text("https://github.com/mnmc5h5ntg-wq/ClipboardHistory\nREADME"),
            timestamp: Date(timeIntervalSince1970: 42),
            thumbnail: nil,
            sourceURL: nil,
            isFavorite: true,
            sourceUTIs: ["public.utf8-plain-text"]
        )

        let summary = adapter.summary(for: entry)

        XCTAssertEqual(summary.id, id)
        XCTAssertEqual(summary.contentKind, "url")
        XCTAssertEqual(summary.copiedAt, entry.timestamp)
        XCTAssertTrue(summary.isFavorite)
        XCTAssertEqual(summary.sourceUTIs, ["public.utf8-plain-text"])
        XCTAssertTrue(summary.preview.contains("github.com"))
        XCTAssertTrue(summary.preview.contains("↵"))
    }

    func testIntelligenceDetectsCodeAndShellCommand() {
        let codeEntry = textEntry("swift build --package-path ClipboardHistory")

        let intelligence = adapter.intelligence(for: codeEntry)

        XCTAssertTrue(intelligence.tags.contains(.shellCommand))
        XCTAssertFalse(intelligence.tags.contains(.apiKeyCandidate))
        XCTAssertEqual(intelligence.sensitivity, .publicLike)
        XCTAssertEqual(intelligence.source, .ruleBased)
    }

    func testIntelligenceMarksApiKeysAsSecret() {
        let entry = textEntry("OPENAI_API_KEY=sk-abcdefghijklmnopqrstuvwxyz123456")

        let intelligence = adapter.intelligence(for: entry)

        XCTAssertTrue(intelligence.tags.contains(.apiKeyCandidate))
        XCTAssertEqual(intelligence.sensitivity, .secret)
    }

    func testIntelligenceMarksVerificationCodesAsSensitive() {
        let entry = textEntry("验证码是 123456，五分钟内有效")

        let intelligence = adapter.intelligence(for: entry)

        XCTAssertTrue(intelligence.tags.contains(.verificationCode))
        XCTAssertEqual(intelligence.sensitivity, .sensitive)
    }

    func testFileEntriesUseFileSpecificKindsAndTags() {
        let imageURL = URL(fileURLWithPath: "/Users/test/Desktop/cat.png")
        let documentURL = URL(fileURLWithPath: "/Users/test/Desktop/report.pdf")
        let archiveURL = URL(fileURLWithPath: "/Users/test/Desktop/archive.zip")

        let imageSummary = adapter.summary(for: fileEntry(imageURL))
        let documentIntelligence = adapter.intelligence(for: fileEntry(documentURL))
        let archiveIntelligence = adapter.intelligence(for: fileEntry(archiveURL))

        XCTAssertEqual(imageSummary.contentKind, "image-file")
        XCTAssertTrue(documentIntelligence.tags.contains(.document))
        XCTAssertTrue(archiveIntelligence.tags.contains(.archive))
        XCTAssertEqual(documentIntelligence.sensitivity, .personal)
    }

    func testMultipleFilesAggregateTags() {
        let entry = ClipboardEntry(
            content: .files([
                URL(fileURLWithPath: "/tmp/demo.mov"),
                URL(fileURLWithPath: "/tmp/notes.md")
            ]),
            timestamp: Date(timeIntervalSince1970: 1),
            thumbnail: nil,
            sourceURL: nil,
            sourceUTIs: ["public.file-url"]
        )

        let summary = adapter.summary(for: entry)
        let intelligence = adapter.intelligence(for: entry)

        XCTAssertEqual(summary.contentKind, "files")
        XCTAssertTrue(summary.preview.contains("demo.mov"))
        XCTAssertTrue(intelligence.tags.contains(.video))
        XCTAssertTrue(intelligence.tags.contains(.document))
    }

    private func textEntry(_ text: String) -> ClipboardEntry {
        ClipboardEntry(
            content: .text(text),
            timestamp: Date(timeIntervalSince1970: 1),
            thumbnail: nil,
            sourceURL: nil,
            sourceUTIs: ["public.utf8-plain-text"]
        )
    }

    private func fileEntry(_ url: URL) -> ClipboardEntry {
        ClipboardEntry(
            content: .file(url),
            timestamp: Date(timeIntervalSince1970: 1),
            thumbnail: nil,
            sourceURL: url,
            sourceUTIs: ["public.file-url"]
        )
    }
}
