import SwiftUI
import XCTest
@testable import ClipboardHistoryApp

/// 审计第二轮 R2-10（1.1 / 1.12）：筛选 pill 的过冲弹簧与 hover 放大以前不读「减弱动态效果」，
/// 而系统分段控件本来也没有这种弹性。策略抽成纯值 `SlideMotion`，两个分支都在这里钉住。
final class FilterPillMotionTests: XCTestCase {
    func testSlideMotionGivesUpTheOvershootWhenReducingMotion() {
        let normal = FilterPillMotion.slideMotion(reduceMotion: false)
        XCTAssertFalse(normal.isInstant)
        XCTAssertLessThan(normal.damping, 1.0, "正常态保留轻微过冲（damping < 1）")
        XCTAssertEqual(normal.response, 0.38, accuracy: 0.0001)

        let reduced = FilterPillMotion.slideMotion(reduceMotion: true)
        XCTAssertTrue(reduced.isInstant, "减少动态时滑块必须瞬移，不做弹簧动画")
        XCTAssertEqual(reduced.damping, 1.0)
        XCTAssertNotEqual(normal, reduced)
    }

    func testHoverScaleIsOneWhenReducingMotionOrNotHovered() {
        XCTAssertEqual(FilterPillMotion.hoverScale(isHovered: true, reduceMotion: false), 1.08)
        XCTAssertEqual(FilterPillMotion.hoverScale(isHovered: true, reduceMotion: true), 1.0,
                       "减少动态时不许放大")
        XCTAssertEqual(FilterPillMotion.hoverScale(isHovered: false, reduceMotion: false), 1.0)
        XCTAssertEqual(FilterPillMotion.hoverScale(isHovered: false, reduceMotion: true), 1.0)
    }

    /// 接线守卫：视图必须真的走这套策略。纯函数正确但没人调用 = 没修。
    func testSidebarConsumesTheMotionPolicyInsteadOfHardcodingSpring() throws {
        var candidate = URL(fileURLWithPath: #filePath).deletingLastPathComponent()
        var file: URL?
        for _ in 0..<6 {
            let probe = candidate
                .appendingPathComponent("Sources/ClipboardHistoryApp/Views/HistorySidebarView.swift")
            if FileManager.default.fileExists(atPath: probe.path) { file = probe; break }
            candidate = candidate.deletingLastPathComponent()
        }
        guard let file else { throw XCTSkip("找不到 HistorySidebarView.swift") }
        let source = try String(contentsOf: file, encoding: .utf8)

        XCTAssertFalse(source.contains(".spring(response: 0.38"),
                       "pill 的弹簧参数又被写死在视图里了，减少动态的门控会被绕过")
        XCTAssertEqual(
            source.components(separatedBy: "FilterPillMotion.slideAnimation(reduceMotion:").count - 1, 1,
            "滑块动画应当恰好在一处由策略给出"
        )
        XCTAssertEqual(
            source.components(separatedBy: "FilterPillMotion.hoverScale(isHovered:").count - 1, 1,
            "hover 放大应当恰好在一处由策略给出"
        )
        XCTAssertTrue(source.contains("accessibilityReduceMotion"),
                      "必须读系统的「减弱动态效果」，而不是自己猜")
    }
}
