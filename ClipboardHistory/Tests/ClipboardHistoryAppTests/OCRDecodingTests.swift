import AppKit
import CryptoKit
import ImageIO
import XCTest
@testable import ClipboardHistoryApp

/// R-23：OCR 的像素解码过去整个发生在主线程 —— `add()` 里同步
/// `nsImage.cgImage(forProposedRect:)`，审计探针 P-13 实测 16.9ms/张，
/// 而启动时 `scheduleOCRForExistingImages()` 会对整库图片各来一次。
@MainActor
final class OCRDecodingTests: XCTestCase {
    private func makeStore() -> HistoryStore {
        HistoryStore(
            clipboardWriter: TestClipboardWriter(),
            persistence: RecordingHistoryPersistence(),
            retentionPolicy: HistoryRetentionPolicy(maxEntries: 50, maxAgeDays: nil)
        )
    }

    /// 解码必须被限到"够认字"的尺寸，并且字节与文件两条来源都走 ImageIO。
    func testOCRDecodeIsBoundedAndHandlesBothSources() throws {
        let stored = try makeStoredImage(color: .systemTeal, size: NSSize(width: 3000, height: 2000))
        let data = try XCTUnwrap(stored.pngData())

        let fromData = try XCTUnwrap(HistoryStore.decodeImageForOCR(.data(data)))
        XCTAssertLessThanOrEqual(max(fromData.width, fromData.height), 1_200,
                                 "整幅落地就是 R-23 的根因：必须限尺寸")
        XCTAssertGreaterThan(min(fromData.width, fromData.height), 400, "缩得太狠会认不出字")

        let dir = URL(fileURLWithPath: NSTemporaryDirectory(), isDirectory: true)
            .appendingPathComponent(UUID().uuidString, isDirectory: true)
        try FileManager.default.createDirectory(at: dir, withIntermediateDirectories: true)
        defer { try? FileManager.default.removeItem(at: dir) }
        let file = dir.appendingPathExtension("png")
        try data.write(to: file)

        let fromURL = try XCTUnwrap(HistoryStore.decodeImageForOCR(.url(file)))
        XCTAssertLessThanOrEqual(max(fromURL.width, fromURL.height), 1_200)

        XCTAssertNil(HistoryStore.decodeImageForOCR(.data(Data([0, 1, 2, 3]))),
                     "垃圾字节要返回 nil，不能崩也不能假装识别成功")
    }

    /// 主线程侧只允许"取到字节 + 入队"。取 3 次最快值，界值仍比旧实测低一截。
    func testAddingLargeImageDoesNotDecodeOnMainThread() throws {
        let store = makeStore()
        let big = try makeStoredImage(color: .systemIndigo, size: NSSize(width: 3000, height: 2000))
        var samples: [Double] = []
        for _ in 0..<3 {
            let entry = ClipboardIntake.Entry(
                content: .image(big), thumbnail: big, sourceUTIs: ["public.png"],
                sourceAppBundleID: "com.apple.Safari", sourceAppName: "Safari"
            )
            let start = Date()
            store.add(entry, timestamp: Date())
            samples.append(Date().timeIntervalSince(start) * 1000)
        }
        let best = samples.min() ?? .infinity
        print("PERF add(3000x2000 图片) 主线程 = "
            + samples.map { String(format: "%.2f", $0) }.joined(separator: " / ") + "ms")
        XCTAssertLessThan(best, 10.0, "旧实现主线程整幅解码实测 16.9ms/张，界值必须明显低于它")
    }
}
