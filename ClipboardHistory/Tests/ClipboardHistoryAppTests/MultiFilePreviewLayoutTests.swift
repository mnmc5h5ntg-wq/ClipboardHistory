import CoreGraphics
import Foundation
import AppKit
import XCTest
@testable import ClipboardHistoryApp

final class MultiFilePreviewLayoutTests: XCTestCase {
    func testAnimationUsesShortNativeFeelingDuration() {
        XCTAssertEqual(MultiFilePreviewLayout.animationDuration, 0.22, accuracy: 0.001)
        XCTAssertLessThan(MultiFilePreviewLayout.animationDuration, 0.3)
    }

    func testUnknownFilePreviewUsesCompactFallbackInsteadOfOldFixedHeight() {
        let url = URL(fileURLWithPath: "/tmp/archive.dmg")

        let height = MultiFilePreviewLayout.preferredHeight(for: url, availableWidth: 720)

        XCTAssertEqual(height, MultiFilePreviewLayout.fallbackCompactPreviewHeight)
        XCTAssertLessThan(height, MultiFilePreviewLayout.fallbackPreviewHeight)
    }

    func testShortTextPreviewCanUseContentSizedHeight() throws {
        let url = FileManager.default.temporaryDirectory
            .appendingPathComponent(UUID().uuidString)
            .appendingPathExtension("md")
        try "一行短文本".write(to: url, atomically: true, encoding: .utf8)
        defer { try? FileManager.default.removeItem(at: url) }

        let height = MultiFilePreviewLayout.preferredHeight(for: url, availableWidth: 720)

        XCTAssertEqual(height, MultiFilePreviewLayout.minimumPreviewHeight)
        XCTAssertLessThan(height, MultiFilePreviewLayout.fallbackPreviewHeight)
    }

    func testLargeImageHeightIsClamped() throws {
        let image = NSImage(size: NSSize(width: 800, height: 2_400))
        image.lockFocus()
        NSColor.red.setFill()
        NSRect(x: 0, y: 0, width: 800, height: 2_400).fill()
        image.unlockFocus()

        let url = FileManager.default.temporaryDirectory
            .appendingPathComponent(UUID().uuidString)
            .appendingPathExtension("png")
        let tiffData = try XCTUnwrap(image.tiffRepresentation)
        let bitmap = try XCTUnwrap(NSBitmapImageRep(data: tiffData))
        let pngData = try XCTUnwrap(bitmap.representation(using: .png, properties: [:]))
        try pngData.write(to: url)
        defer { try? FileManager.default.removeItem(at: url) }

        let height = MultiFilePreviewLayout.preferredHeight(for: url, availableWidth: 720)

        XCTAssertEqual(height, MultiFilePreviewLayout.maximumPreviewHeight)
    }
}
