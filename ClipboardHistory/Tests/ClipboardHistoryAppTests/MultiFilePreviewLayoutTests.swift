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

    /// UI 量化检查 5：系统「减弱动态效果」必须真的把会改变尺寸/位置的动画退化为无动画。
    /// `accessibilityDisplayShouldReduceMotion` 是全局状态、测试改不了，
    /// 所以断言打在"取值参数化"后的纯函数上。
    func testReduceMotionRemovesLayoutAnimation() {
        XCTAssertEqual(MultiFilePreviewLayout.animation(reduceMotion: true), .linear(duration: 0),
                       "开启减弱动态后展开/收起不该再有位移")
        XCTAssertNotEqual(MultiFilePreviewLayout.animation(reduceMotion: false), .linear(duration: 0),
                          "没开的时候不能顺手把动画也关掉")
    }

    func testReduceMotionKeepsCollapsedRowAtFullSize() {
        XCTAssertEqual(MultiFilePreviewLayout.collapsedScale(reduceMotion: true), 1,
                       "缩放也属于会动的那一类")
        XCTAssertEqual(MultiFilePreviewLayout.collapsedScale(reduceMotion: false),
                       MultiFilePreviewLayout.collapsedScale)
    }
}
