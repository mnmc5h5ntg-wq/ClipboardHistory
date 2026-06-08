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
}
