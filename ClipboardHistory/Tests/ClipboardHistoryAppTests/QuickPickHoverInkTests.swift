// 不覆盖管线：这两格量的是「悬停那一档在两档色档下各自看不看得见」这个**数值决定**，
// 以及「产品画法有没有真的去读按档的那个函数」。管线级的像素证人在捕获卷：
// `quickpick-hover-420x300-{dark,light}` 两张帧 + 帧基线（本轮亮档那张会变），
// 同一族的管线判据形状见 `SkeletonMotionTests.testSkeletonViewReadsItsInkPerAppearance`（R219）。
import XCTest
import AppKit
@testable import ClipboardHistoryApp

@MainActor
final class QuickPickHoverInkTests: XCTestCase {

    // MARK: - 两档各自的地板（与 R220 的骨架条带同一套算法，不新造数）

    private func luminance(_ channel255: CGFloat) -> CGFloat {
        let c = channel255 / 255.0
        return c <= 0.03928 ? c / 12.92 : pow((c + 0.055) / 1.055, 2.4)
    }

    private func contrast(_ a: CGFloat, _ b: CGFloat) -> Double {
        let la = luminance(a), lb = luminance(b)
        return Double((max(la, lb) + 0.05) / (min(la, lb) + 0.05))
    }

    /// `labelColor`（亮档黑 / 暗档白）按 alpha 压在该档的底上之后的灰度。
    private func composite(ink: CGFloat, over background: CGFloat, alpha: CGFloat) -> CGFloat {
        background + (ink - background) * alpha
    }

    func testHoverInkIsPerAppearanceAndEachAppearanceClearsItsOwnFloor() {
        let dark = QuickPickController.hoverFillAlpha(dark: true)
        let light = QuickPickController.hoverFillAlpha(dark: false)

        XCTAssertEqual(dark, CGFloat(VisualFill.hover), accuracy: 0.0001,
                       "暗档必须还是那枚共享令牌（R219 的教训：抬亮档不许顺手改暗档）")
        XCTAssertGreaterThan(light, dark,
                             "亮档必须比暗档更重 ——『一个数管两档』正是本轮修的病")

        let lightRatio = contrast(composite(ink: 0, over: 255, alpha: light), 255)
        let darkRatio = contrast(composite(ink: 255, over: 30, alpha: dark), 30)
        XCTAssertGreaterThanOrEqual(lightRatio, 1.20,
                                    "亮档悬停带对底 \(lightRatio):1 < 仓库自己定的亮档地板 1.20（R220）")
        XCTAssertGreaterThanOrEqual(darkRatio, 1.10,
                                    "暗档悬停带对底 \(darkRatio):1 < 暗档地板 1.10")

        // 悬停不该读成选中：亮档选中带实测 (220,220,220)（`quickpick-hover-*-light` 的行带众数），
        // 抬完的悬停带必须仍与它差 ≥8 级灰。只测"看得见"会允许悬停一路抬到贴住选中。
        let hoverGrey = composite(ink: 0, over: 255, alpha: light)
        XCTAssertGreaterThanOrEqual(hoverGrey, CGFloat(228),
                                    "悬停带 \(hoverGrey) 与选中带 220 差不足 8 级 ⇒ 两态会撞")
    }

    // MARK: - 画法必须去读按档的那个函数（源码守卫，R219 同一形状）

    func testHoverFillViewReadsThePerAppearanceToken() {
        let text = productSource("Managers/QuickPickController.swift")
        XCTAssertTrue(text.contains("hoverFillAlpha(dark: dark)"),
                      "HoverFillView 没在按色档取墨 ⇒ 亮档那一抬是死数")
        XCTAssertTrue(text.contains("effectiveAppearance.bestMatch"),
                      "色档必须由视图自己问，不从外面传布尔（否则夹具能替产品决定这一档多亮）")
        XCTAssertFalse(text.contains("withAlphaComponent(QuickPickController.hoverFillAlpha)"),
                       "画法还在读那个不分色档的老令牌")
    }

    private func productSource(_ relative: String) -> String {
        var dir = URL(fileURLWithPath: #filePath).deletingLastPathComponent()
        for _ in 0..<8 {
            let url = dir.appendingPathComponent("Sources/ClipboardHistoryApp/" + relative)
            if let text = try? String(contentsOf: url, encoding: .utf8) { return text }
            dir = dir.deletingLastPathComponent()
        }
        // 读不到**红**而不是跳过：一个会跳过的守卫和一个通过的守卫在报表里长得一样。
        // 返回空串会让下面三条 contains 断言一起红，不会静默通过。
        XCTFail("读不到 Sources/ClipboardHistoryApp/" + relative)
        return ""
    }
}
