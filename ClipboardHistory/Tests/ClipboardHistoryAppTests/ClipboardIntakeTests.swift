import AppKit
import XCTest
@testable import ClipboardHistoryApp

final class ClipboardIntakeTests: XCTestCase {
    func testRefreshReadsTextFromPasteboard() throws {
        let pasteboard = makePasteboard()
        pasteboard.setString("hello", forType: .string)
        var intake = ClipboardIntake()

        let entry = intake.refresh(from: pasteboard)

        XCTAssertEqual(entry?.content, .text("hello"))
        XCTAssertTrue(entry?.sourceUTIs.contains(NSPasteboard.PasteboardType.string.rawValue) == true)
    }

    func testRefreshIgnoresBlankText() throws {
        let pasteboard = makePasteboard()
        pasteboard.setString("   \n", forType: .string)
        var intake = ClipboardIntake()

        XCTAssertNil(intake.refresh(from: pasteboard))
    }

    func testRefreshReadsPNGImageFromPasteboard() throws {
        let pasteboard = makePasteboard()
        let image = try makeStoredImage(size: NSSize(width: 3, height: 4))
        let pngData = try XCTUnwrap(image.pngData())
        pasteboard.setData(pngData, forType: .png)
        var intake = ClipboardIntake()

        let entry = intake.refresh(from: pasteboard)

        guard case .image(let storedImage) = entry?.content else {
            return XCTFail("Expected image entry")
        }
        XCTAssertEqual(Int(storedImage.nsImage.size.width), 3)
        XCTAssertEqual(Int(storedImage.nsImage.size.height), 4)
    }

    func testRefreshReadsFileURLFromPasteboard() throws {
        let pasteboard = makePasteboard()
        let url = URL(fileURLWithPath: "/tmp/example.pdf")
        pasteboard.setString(url.absoluteString, forType: .fileURL)
        var intake = ClipboardIntake()

        let entry = intake.refresh(from: pasteboard)

        XCTAssertEqual(entry?.content, .file(url))
    }

    func testRefreshReadsMultipleFileURLsFromPasteboard() throws {
        let pasteboard = makePasteboard()
        let firstURL = URL(fileURLWithPath: "/tmp/first.txt")
        let secondURL = URL(fileURLWithPath: "/tmp/second.txt")
        XCTAssertTrue(pasteboard.writeObjects([firstURL as NSURL, secondURL as NSURL]))
        var intake = ClipboardIntake()

        let entry = intake.refresh(from: pasteboard)

        XCTAssertEqual(entry?.content, .files([firstURL, secondURL]))
    }

    func testFileURLTakesPriorityOverText() throws {
        let pasteboard = makePasteboard()
        let url = URL(fileURLWithPath: "/tmp/example.mov")
        pasteboard.setString(url.absoluteString, forType: .fileURL)
        pasteboard.setString("plain text", forType: .string)
        var intake = ClipboardIntake()

        let entry = intake.refresh(from: pasteboard)

        XCTAssertEqual(entry?.content, .file(url))
    }

    func testRefreshReadsVideoFileURLWithoutGeneratingThumbnail() throws {
        let pasteboard = makePasteboard()
        let url = URL(fileURLWithPath: "/tmp/example.mov")
        pasteboard.setString(url.absoluteString, forType: .fileURL)
        var intake = ClipboardIntake()

        let entry = intake.refresh(from: pasteboard)

        XCTAssertEqual(entry?.content, .file(url))
        XCTAssertNil(entry?.thumbnail)
    }

    func testRefreshReadsImageFileURLWithoutSynchronouslyLoadingThumbnail() throws {
        let pasteboard = makePasteboard()
        let directory = try makeTemporaryDirectory()
        let imageURL = directory.appendingPathComponent("large-image.png")
        let image = try makeStoredImage(size: NSSize(width: 8, height: 8))
        try XCTUnwrap(image.pngData()).write(to: imageURL)
        pasteboard.setString(imageURL.absoluteString, forType: .fileURL)
        var intake = ClipboardIntake()

        let entry = intake.refresh(from: pasteboard)

        XCTAssertEqual(entry?.content, .file(imageURL))
        XCTAssertNil(entry?.thumbnail)
    }

    private func makePasteboard() -> NSPasteboard {
        let pasteboard = NSPasteboard(name: NSPasteboard.Name(UUID().uuidString))
        pasteboard.clearContents()
        return pasteboard
    }
}
