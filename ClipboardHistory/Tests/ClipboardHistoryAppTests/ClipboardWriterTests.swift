import AppKit
import XCTest
@testable import ClipboardHistoryApp

@MainActor
final class ClipboardWriterTests: XCTestCase {
    func testWritingMissingFileURLFailsBeforeClearingPasteboard() throws {
        let pasteboard = NSPasteboard(name: NSPasteboard.Name(UUID().uuidString))
        pasteboard.clearContents()
        pasteboard.setString("keep me", forType: .string)
        let writer = SystemClipboardWriter(pasteboard: pasteboard)
        let missingURL = FileManager.default.temporaryDirectory
            .appendingPathComponent(UUID().uuidString)
            .appendingPathExtension("txt")

        XCTAssertThrowsError(try writer.write(.file(missingURL))) { error in
            XCTAssertEqual(error as? ClipboardWriteError, .fileDoesNotExist)
        }
        XCTAssertEqual(pasteboard.string(forType: .string), "keep me")
    }

    func testWritingMultipleFileURLsWritesAllFiles() throws {
        let pasteboard = NSPasteboard(name: NSPasteboard.Name(UUID().uuidString))
        pasteboard.clearContents()
        let directory = try makeTemporaryDirectory()
        let firstURL = directory.appendingPathComponent("first.txt")
        let secondURL = directory.appendingPathComponent("second.txt")
        try "first".write(to: firstURL, atomically: true, encoding: .utf8)
        try "second".write(to: secondURL, atomically: true, encoding: .utf8)
        let writer = SystemClipboardWriter(pasteboard: pasteboard)

        try writer.write(.files([firstURL, secondURL]))

        let urls = try XCTUnwrap(pasteboard.readObjects(forClasses: [NSURL.self]) as? [URL])
        XCTAssertEqual(urls, [firstURL, secondURL])
    }
}
