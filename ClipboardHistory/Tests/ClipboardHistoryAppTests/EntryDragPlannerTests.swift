// 不覆盖管线：本文件只钉载荷规划的纯函数真值表。真实拖放（拖出到 Finder、拖入入库）需要
// `NSDraggingSession`，离屏测不到；管线级验收见 `PipelineAcceptanceTests`（C-1 的三条之一）
// 与 docs/MANUAL_TEST_v1.4.9_round3.md 第 2 节。
// （第三轮审计 C-1：这类文件要自己写明边界，别让读者以为它覆盖了产品路径。）
import AppKit
import UniformTypeIdentifiers
import XCTest
@testable import ClipboardHistoryApp

/// 审计第二轮 1.5 / 账本 R2-05：拖拽能力以前是零。
/// 这里钉住"哪种内容拖出去是什么"（纯函数）与"provider 真的带着载荷"（否则创建了 provider 也可能空的）。
/// 真实拖放需要鼠标事件与辅助功能授权，离屏测不了 —— 那部分在账本里记为未验证。
@MainActor
final class EntryDragPlannerTests: XCTestCase {
    /// 异步回调结果的容器（回调在别的队列上跑，不能用捕获的 var）。
    private final class PayloadBox: @unchecked Sendable {
        var data: Data?
        var error: Error?
    }

    func testTextDragsAsAStringAndEmptyTextOffersNothing() {
        XCTAssertEqual(EntryDragPlanner.payload(for: .text("拖我")), .text("拖我"))
        XCTAssertNil(EntryDragPlanner.payload(for: .text("")), "空文本拖出去是空 provider，不如不给")
    }

    func testImageDragsAsTheSamePNGBytes() throws {
        let image = try makeStoredImage(color: .systemTeal, size: NSSize(width: 12, height: 9))
        let expected = try XCTUnwrap(image.pngData())
        XCTAssertEqual(EntryDragPlanner.payload(for: .image(image)), .png(expected),
                       "拖出去的必须是同一份 PNG 字节，而不是重新编码或缩略图")
    }

    func testFileURLDragsAsAFileReferenceButWebURLDoesNot() throws {
        let file = URL(fileURLWithPath: "/tmp/拖拽-\(UUID().uuidString).txt")
        XCTAssertEqual(EntryDragPlanner.payload(for: .file(file)), .fileURL(file))

        let web = try XCTUnwrap(URL(string: "https://example.com/page"))
        XCTAssertNil(EntryDragPlanner.payload(for: .file(web)),
                     "Web URL 拖进 Finder 没有意义，而且这正是 P-15 那类'把链接当文件'混淆的起点")
    }

    /// 第三轮审计 §4 U-2：多文件条目现在**能**拖出了。
    /// 这条以前断言的是"宁可没有拖拽"（`XCTAssertNil`），改成断言"provider 带全部路径" ——
    /// 这是随能力变化而更新的契约，不是为了让测试变绿：判据比以前更强（要看回真实字节）。
    func testMultipleFileEntriesCarryEveryPath() throws {
        let urls = [
            URL(fileURLWithPath: "/tmp/a-\(UUID().uuidString).txt"),
            URL(fileURLWithPath: "/tmp/b-\(UUID().uuidString).txt"),
            URL(fileURLWithPath: "/tmp/c-\(UUID().uuidString).txt")
        ]
        XCTAssertEqual(EntryDragPlanner.payload(for: .files(urls)), .fileList(urls))
        XCTAssertTrue(EntryDragGate.offersDrag(for: .files(urls)),
                      "多文件条目既然有载荷，就必须承诺可拖")

        let provider = try XCTUnwrap(EntryDragPlanner.itemProvider(forContent: .files(urls)))
        XCTAssertTrue(provider.hasItemConformingToTypeIdentifier(EntryDragPlanner.fileListPasteboardType),
                      "没登记路径数组那份表示：拖出去只会落地一个文件\(provider.registeredTypeIdentifiers)")
        // 半截动作的判据：**解码出来的**是全部三个路径，而不是"登记了某个类型"就算数
        let decoded = try waitForData(from: provider, type: EntryDragPlanner.fileListPasteboardType)
        let paths = try XCTUnwrap(
            PropertyListSerialization.propertyList(from: decoded, format: nil) as? [String])
        XCTAssertEqual(paths, urls.map { $0.path },
                       "拖 3 个只带出去 \(paths.count) 个 —— 这正是当初拒绝多文件拖出的理由")

        // 空数组不该承诺拖拽
        XCTAssertNil(EntryDragPlanner.payload(for: .files([])))
    }

    private func waitForData(from provider: NSItemProvider, type: String) throws -> Data {
        let expectation = XCTestExpectation(description: "provider 交回 \(type)")
        let box = PayloadBox()
        _ = provider.loadDataRepresentation(forTypeIdentifier: type) { data, error in
            box.data = data
            box.error = error
            expectation.fulfill()
        }
        wait(for: [expectation], timeout: 2.0)
        if let error = box.error { throw error }
        return try XCTUnwrap(box.data, "provider 没交回 \(type) 的字节")
    }

    func testItemProvidersActuallyCarryTheirPayload() throws {
        let textProvider = EntryDragPlanner.itemProvider(for: .text("拖我"))
        XCTAssertTrue(
            textProvider.registeredTypeIdentifiers.contains(UTType.utf8PlainText.identifier),
            "文本 provider 没有登记任何可拖类型：\(textProvider.registeredTypeIdentifiers)"
        )

        let image = try makeStoredImage(color: .systemOrange, size: NSSize(width: 8, height: 6))
        let pngBytes = try XCTUnwrap(image.pngData())
        let imageProvider = EntryDragPlanner.itemProvider(for: .png(pngBytes))
        XCTAssertTrue(
            imageProvider.registeredTypeIdentifiers.contains(UTType.png.identifier),
            "图片 provider 没有登记 PNG：\(imageProvider.registeredTypeIdentifiers)"
        )

        // 把字节真的读回来：只断言"登记了类型"证明不了载荷没丢。
        // 用引用类型的盒子接结果：Swift 6 不许在 @Sendable 回调里改捕获的 var。
        let box = PayloadBox()
        let loaded = expectation(description: "PNG 载荷载得回来")
        imageProvider.loadDataRepresentation(forTypeIdentifier: UTType.png.identifier) { data, error in
            box.data = data
            box.error = error
            loaded.fulfill()
        }
        wait(for: [loaded], timeout: 5)
        XCTAssertNil(box.error)
        XCTAssertEqual(box.data, pngBytes, "拖拽载荷与原始 PNG 字节不一致")

        let file = URL(fileURLWithPath: "/tmp/拖拽-\(UUID().uuidString).txt")
        let fileProvider = EntryDragPlanner.itemProvider(for: .fileURL(file))
        XCTAssertTrue(
            fileProvider.registeredTypeIdentifiers.contains(UTType.fileURL.identifier),
            "文件 provider 没有登记 file URL：\(fileProvider.registeredTypeIdentifiers)"
        )
    }

    func testContentWithoutPayloadGetsNoProviderAtAll() {
        XCTAssertNil(EntryDragPlanner.itemProvider(forContent: .text("")))
        XCTAssertNil(EntryDragPlanner.itemProvider(forContent: .files([])),
                     "空的文件列表不该承诺拖出一个东西")
        XCTAssertNotNil(EntryDragPlanner.itemProvider(forContent: .text("有内容")))
    }

    /// 接线守卫：行视图必须真的挂上这个 modifier，否则规划函数再对也没人用。
    func testRowViewWiresTheDragModifier() throws {
        var candidate = URL(fileURLWithPath: #filePath).deletingLastPathComponent()
        var file: URL?
        for _ in 0..<6 {
            let probe = candidate
                .appendingPathComponent("Sources/ClipboardHistoryApp/Views/HistoryRowViews.swift")
            if FileManager.default.fileExists(atPath: probe.path) { file = probe; break }
            candidate = candidate.deletingLastPathComponent()
        }
        guard let file else { throw XCTSkip("找不到 HistoryRowViews.swift") }
        let source = try String(contentsOf: file, encoding: .utf8)
        XCTAssertEqual(
            source.components(separatedBy: "EntryDragModifier(content:").count - 1, 1,
            "行视图应当恰好挂一次拖拽 modifier"
        )
    }
}
