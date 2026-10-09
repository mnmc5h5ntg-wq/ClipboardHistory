import AppKit
import XCTest
@testable import ClipboardHistoryApp

/// 审计第二轮 B-4 / 账本 R2-08：图片以前没有像素上限，原分辨率整张入库。
/// 最后一条用例走**真实采集管线**（pasteboard → `ClipboardIntake.readChangedEntry`），
/// 因为只测 helper 证明不了产品路径真的接上了 —— N-1 就是这么漏掉的。
@MainActor
final class ImageIntakePolicyTests: XCTestCase {
    func testPlanOnlyDownsamplesAboveTheLimit() {
        XCTAssertFalse(ImageIntakePolicy.plan(pixelWidth: 3840, pixelHeight: 2160).shouldDownsample,
                       "4K 截图必须逐字节不动，这是阈值取 4096 的理由")
        XCTAssertFalse(ImageIntakePolicy.plan(pixelWidth: 4096, pixelHeight: 4096).shouldDownsample,
                       "等于上限不算超限")
        XCTAssertTrue(ImageIntakePolicy.plan(pixelWidth: 5120, pixelHeight: 2880).shouldDownsample,
                      "5K 截图要缩")
        XCTAssertTrue(ImageIntakePolicy.plan(pixelWidth: 100, pixelHeight: 9000).shouldDownsample,
                      "竖长图也要按最长边判")
        XCTAssertEqual(ImageIntakePolicy.plan(pixelWidth: 10, pixelHeight: 20, limit: 5).longestEdge, 20)
        XCTAssertFalse(ImageIntakePolicy.plan(pixelWidth: 0, pixelHeight: 0).shouldDownsample)
    }

    func testPlanHonoursACustomLimit() {
        XCTAssertTrue(ImageIntakePolicy.plan(pixelWidth: 200, pixelHeight: 100, limit: 64).shouldDownsample)
        XCTAssertFalse(ImageIntakePolicy.plan(pixelWidth: 200, pixelHeight: 100, limit: 200).shouldDownsample)
    }

    func testPixelDimensionsReadsARealPNG() throws {
        let image = try makeStoredImage(color: .systemTeal, size: NSSize(width: 41, height: 17))
        let bytes = try XCTUnwrap(image.pngData())
        let dimensions = try XCTUnwrap(ImageIntakePolicy.pixelDimensions(of: bytes))
        // 读出来的必须是**像素**而不是点：本机 `makeStoredImage` 以 2× 位图渲染，
        // 所以 41×17 点会得到 82×34 像素（这也是所有捕获帧"名字里是点、文件里是 2× 像素"的原因）。
        // 断言写成"严格大于点尺寸 + 宽高比不变"，不把某个倍数钉死 —— 换个非 retina 环境倍数就变了。
        XCTAssertGreaterThan(dimensions.width, 41)
        XCTAssertGreaterThan(dimensions.height, 17)
        XCTAssertEqual(dimensions.width * 17, dimensions.height * 41, "宽高比必须与请求的一致")
        XCTAssertNil(ImageIntakePolicy.pixelDimensions(of: Data("这不是图片".utf8)),
                     "非图片数据必须返回 nil，而不是编一组宽高")
    }

    func testImageUnderTheLimitIsKeptByteForByte() throws {
        let small = try makeStoredImage(color: .systemOrange, size: NSSize(width: 40, height: 30))
        let bytes = try XCTUnwrap(small.pngData())
        let result = StoredImage.downsamplingIfNeeded(small.nsImage, pngData: bytes)
        XCTAssertEqual(result.pngData(), bytes,
                       "未超限的图必须逐字节保留 —— 重新编码会白白改一次内容还拖慢采集")
    }

    func testOversizedImageIsDownsampledPreservingAspectRatio() throws {
        let huge = try makeStoredImage(color: .systemTeal, size: NSSize(width: 5000, height: 100))
        let result = StoredImage.downsamplingIfNeeded(huge.nsImage)
        let dimensions = try XCTUnwrap(ImageIntakePolicy.pixelDimensions(of: try XCTUnwrap(result.pngData())))
        XCTAssertEqual(max(dimensions.width, dimensions.height), ImageIntakePolicy.maxPixelDimension)
        // 5000×100 → 4096×81.92：允许 ±1 像素的取整误差，但不许变形。
        XCTAssertEqual(dimensions.width, 4096)
        XCTAssertLessThanOrEqual(abs(Double(dimensions.height) - 81.92), 1.0,
                                 "长宽比被改了：\(dimensions.width)×\(dimensions.height)")
    }

    func testIntakeBoundsAnOversizedClipboardImageEndToEnd() throws {
        let pasteboard = NSPasteboard(
            name: NSPasteboard.Name("clipboardhistory.tests.bigimage.\(UUID().uuidString)")
        )
        pasteboard.clearContents()
        let huge = try makeStoredImage(color: .systemTeal, size: NSSize(width: 5000, height: 100))
        let png = try XCTUnwrap(huge.pngData())
        XCTAssertGreaterThan(png.count, 0)
        XCTAssertTrue(pasteboard.setData(png, forType: .png))

        var intake = ClipboardIntake(pasteboard: pasteboard)
        intake.markChangeCount(-1)
        let entry = try XCTUnwrap(intake.readChangedEntry(), "超大图必须仍然被记录，不能因为限流而丢")
        guard case .image(let stored) = entry.content else {
            return XCTFail("图片被记成了别的内容类型")
        }
        let storedBytes = try XCTUnwrap(stored.pngData())
        let dimensions = try XCTUnwrap(ImageIntakePolicy.pixelDimensions(of: storedBytes))
        XCTAssertLessThanOrEqual(
            max(dimensions.width, dimensions.height),
            ImageIntakePolicy.maxPixelDimension,
            "采集管线没有接上限：入库的是 \(dimensions.width)×\(dimensions.height)"
        )
        XCTAssertLessThan(storedBytes.count, png.count,
                          "降采样之后落盘的字节必须比原图少，否则上限没有起到限制磁盘占用的作用")
    }
}
