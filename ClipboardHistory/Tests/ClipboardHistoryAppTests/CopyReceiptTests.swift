// R416：复制回执文字的真值表与 GlassPill 接线。
// 不覆盖详情页的完整入口：回执的可见帧在 UICaptureHarness 的三个组件夹具里判；
// 出现/消失的过程在 MotionFilmstripTests 的专用场景里判。
import XCTest
@testable import ClipboardHistoryApp

final class CopyReceiptTests: XCTestCase {

    func testCopyReceiptTruthTable() {
        XCTAssertNil(CopyReceiptPresentation.receipt(copyConfirmed: false, copyFailed: false),
                     "没有回执时不能凭空画一句")
        XCTAssertEqual(CopyReceiptPresentation.receipt(copyConfirmed: true, copyFailed: false),
                       .init(text: "已复制", tone: .success))
        XCTAssertEqual(CopyReceiptPresentation.receipt(copyConfirmed: false, copyFailed: true),
                       .init(text: "复制失败", tone: .failure))
        XCTAssertEqual(CopyReceiptPresentation.receipt(copyConfirmed: true, copyFailed: true),
                       .init(text: "复制失败", tone: .failure),
                       "两态同时为 true 时失败优先：不能把失败说成已复制")
    }

    func testCopyReceiptIsWiredIntoThePill() throws {
        let source = codeOnly(try productSourceText(named: "Views/GlassControls.swift"))
        XCTAssertTrue(source.contains("CopyReceiptPresentation.receipt(copyConfirmed: copyConfirmed, copyFailed: copyFailed)"),
                      "GlassPill 没有从两态算出回执 ⇒ 回执永远是 nil")
        XCTAssertTrue(source.contains("CopyReceiptView(receipt: receipt)"),
                      "GlassPill 没有挂回执视图")
        XCTAssertTrue(source.contains(".transition(.opacity.combined(with: .move(edge: .bottom)))"),
                      "回执没有出现/消失过渡 ⇒ 还是一帧硬切")
        XCTAssertTrue(source.contains(".animation(MotionCatalog.animation(for: .emphasis), value: receipt)"),
                      "回执没有驱动 ⇒ 过渡声明不会演")
        XCTAssertTrue(source.contains("fixedSize(horizontal: true"),
                      "回执又允许被药丸的窄宽折行 ⇒ 会出现竖排的「已复制」")
    }

    private func codeOnly(_ source: String) -> String {
        source.components(separatedBy: "\n")
            .filter { !$0.trimmingCharacters(in: .whitespaces).hasPrefix("//") }
            .joined(separator: "\n")
    }

    private func productSourceText(named relativePath: String) throws -> String {
        var candidate = URL(fileURLWithPath: #filePath).deletingLastPathComponent()
        for _ in 0..<6 {
            let url = candidate.appendingPathComponent("Sources/ClipboardHistoryApp", isDirectory: true)
                .appendingPathComponent(relativePath)
            if let text = try? String(contentsOf: url, encoding: .utf8) { return text }
            candidate = candidate.deletingLastPathComponent()
        }
        throw NSError(domain: "CopyReceiptTests", code: 1,
                      userInfo: [NSLocalizedDescriptionKey:
                        "找不到 Sources/ClipboardHistoryApp/\(relativePath)"])
    }
}
