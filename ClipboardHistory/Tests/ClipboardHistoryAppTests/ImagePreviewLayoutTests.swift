import XCTest
@testable import ClipboardHistoryApp

/// R433：详情图片预览的贴合尺寸（边必须贴在图本身，不是贴在上限框上）。
final class ImagePreviewLayoutTests: XCTestCase {
    func testFittedSizeNeverUpscalesASmallImage() {
        // 旧行为（`scaledToFit` + 上限 frame）只缩不放：240×140 的图在 680 宽的框里仍是 240×140。
        // R433 第一版漏了 `1`，帧上量到图被拉到 680×397 —— 这是自伤，不是改进。
        let fitted = ImagePreviewLayout.fittedSize(image: CGSize(width: 240, height: 140),
                                                   available: CGSize(width: 680, height: 480))
        XCTAssertEqual(fitted, CGSize(width: 240, height: 140),
                       "小图被放大了 ⇒ 旧帧与旧观感都会被改掉")
    }

    func testFittedSizeKeepsTheAspectRatioWhenDownscaling() {
        let fitted = ImagePreviewLayout.fittedSize(image: CGSize(width: 1000, height: 500),
                                                   available: CGSize(width: 500, height: 500))
        XCTAssertEqual(fitted.width, 500, accuracy: 0.5)
        XCTAssertEqual(fitted.height, 250, accuracy: 0.5)
        XCTAssertEqual(fitted.width / fitted.height, 2.0, accuracy: 0.01,
                       "贴合尺寸改变了宽高比 ⇒ 图会被拉伸（边也就贴不到图上）")
    }

    func testFittedSizeRespectsTheHeightLimit() {
        let fitted = ImagePreviewLayout.fittedSize(image: CGSize(width: 400, height: 800),
                                                   available: CGSize(width: 680, height: 480))
        XCTAssertEqual(fitted.height, 480, accuracy: 0.5)
        XCTAssertEqual(fitted.width, 240, accuracy: 0.5)
    }

    func testFittedSizeRefusesDegenerateInput() {
        XCTAssertEqual(ImagePreviewLayout.fittedSize(image: .zero,
                                                     available: CGSize(width: 680, height: 480)),
                       .zero, "零尺寸图没有贴合解 ⇒ 返回零，不许除以零")
        XCTAssertEqual(ImagePreviewLayout.fittedSize(image: CGSize(width: 240, height: 140),
                                                     available: .zero),
                       .zero)
    }
}
