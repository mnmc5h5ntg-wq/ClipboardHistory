import XCTest
@testable import ClipboardHistoryApp

/// R432：设置页排除名单的「ID → 人话」映射。
final class ExcludedAppPresentationTests: XCTestCase {
    func testEveryDefaultExclusionHasAReadableName() {
        let defaults = CapturePolicy.defaultExcludedBundleIDs.sorted()
        XCTAssertEqual(defaults.count, 9, "默认排除名单的数量变了 ⇒ 这张名字表要跟着对账")
        for id in defaults {
            let name = ExcludedAppPresentation.displayName(for: id)
            XCTAssertTrue(ExcludedAppPresentation.hasKnownName(id),
                          "默认排除项「\(id)」没有名字 ⇒ 设置页又会出现认不出的裸 ID")
            XCTAssertNotEqual(name, id, "默认排除项「\(id)」的名字退回了 ID 本身")
            XCTAssertFalse(name.trimmingCharacters(in: .whitespaces).isEmpty,
                           "默认排除项「\(id)」的名字是空白")
        }
    }

    private func productSource(_ relative: String) throws -> String {
        let root = URL(fileURLWithPath: #filePath)
            .deletingLastPathComponent()
            .deletingLastPathComponent()
            .deletingLastPathComponent()
            .appendingPathComponent("Sources/ClipboardHistoryApp")
        return try String(contentsOf: root.appendingPathComponent(relative), encoding: .utf8)
    }

    func testTheBundleIDStaysOnTheSecondaryTier() throws {
        let source = try productSource("Views/ExcludedAppRow.swift")
        XCTAssertTrue(source.contains(".foregroundStyle(.secondary)"),
                      "bundle ID 那一格没有走 .secondary ⇒ 它会和应用名抢同一档（R432 退役的 caption 探针就是因为两种色阶同带）")
        XCTAssertTrue(source.contains("ExcludedAppPresentation.displayName(for: bundleID)"),
                      "行里的名字没有走映射 ⇒ 设置页又会显示裸 ID")
    }

    func testUnknownIDsFallBackToTheIDInsteadOfDisappearing() {
        XCTAssertEqual(ExcludedAppPresentation.displayName(for: "com.example.app"), "com.example.app",
                       "用户自己加的、没有名字的 App 必须原样显示 ID")
        XCTAssertEqual(ExcludedAppPresentation.displayName(for: "  com.example.app  "), "com.example.app",
                       "首尾空格没有归一 ⇒ 同一行会出现两种 ID 形状")
        XCTAssertFalse(ExcludedAppPresentation.hasKnownName("com.example.app"))
        XCTAssertFalse(ExcludedAppPresentation.fallbackSymbolName.isEmpty,
                       "兜底符号名为空 ⇒ 找不到图标的 App 那一格会留白")
    }
}
