// R425：详情状态条左边的来源 App 图标 —— 只在有来源名时出现；
// 图标解析不到时退回 `app` 符号，而不是让状态条少一截。
// 像素正/负臂在 UICaptureHarness 的 detail-0-text 与 detail-no-source 两帧。
import AppKit
import XCTest
@testable import ClipboardHistoryApp

@MainActor
final class SourceAppBadgeTests: XCTestCase {

    func testBadgeIsVisibleOnlyForANonBlankSourceName() {
        XCTAssertFalse(SourceAppBadgePolicy.isVisible(sourceAppName: nil))
        XCTAssertFalse(SourceAppBadgePolicy.isVisible(sourceAppName: ""))
        XCTAssertFalse(SourceAppBadgePolicy.isVisible(sourceAppName: " \n\t "))
        XCTAssertTrue(SourceAppBadgePolicy.isVisible(sourceAppName: "Safari"))
        XCTAssertTrue(SourceAppBadgePolicy.isVisible(sourceAppName: " 终端 "))
    }

    func testNarrowDetailWidthHidesTheIconBeforeItStealsMetaText() {
        XCTAssertFalse(SourceAppBadgePolicy.isVisible(sourceAppName: "Safari", detailWidth: 399))
        XCTAssertTrue(SourceAppBadgePolicy.isVisible(sourceAppName: "Safari", detailWidth: 400))
        XCTAssertFalse(SourceAppBadgePolicy.isVisible(sourceAppName: nil, detailWidth: 1_000),
                       "宽度再够，没有来源名也不画")
    }

    func testResolvedIconTrimsTheBundleIDAndSkipsBlankOnes() {
        let fake = NSImage(size: NSSize(width: SourceAppBadgePolicy.iconSize,
                                        height: SourceAppBadgePolicy.iconSize))
        var asked: [String] = []
        let found = SourceAppBadgePolicy.resolvedIcon(bundleID: "  com.apple.Safari \n") { id in
            asked.append(id)
            return fake
        }
        XCTAssertTrue(found === fake)
        XCTAssertEqual(asked, ["com.apple.Safari"])

        asked = []
        XCTAssertNil(SourceAppBadgePolicy.resolvedIcon(bundleID: nil) { asked.append($0); return fake })
        XCTAssertNil(SourceAppBadgePolicy.resolvedIcon(bundleID: "") { asked.append($0); return fake })
        XCTAssertNil(SourceAppBadgePolicy.resolvedIcon(bundleID: "   ") { asked.append($0); return fake })
        XCTAssertEqual(asked, [], "空 bundle ID 也不许去问系统：那会把一次解析交给一个不存在的键")
    }

    func testFallbackSymbolIsAnAppGlyph() {
        XCTAssertEqual(SourceAppBadgePolicy.fallbackSymbolName, "app")
        XCTAssertGreaterThan(SourceAppBadgePolicy.iconSize, 0)
    }

    func testRealProviderResolvesAnInstalledApplicationIconAndCachesIt() throws {
        guard let icon = SourceAppIconProvider.icon(forBundleID: "com.apple.Safari") else {
            throw XCTSkip("SOURCE_APP_ICON_NOT_RUN=no-safari-icon：这台机器上解析不到 Safari")
        }
        XCTAssertGreaterThan(icon.size.width, 0)
        XCTAssertTrue(SourceAppIconProvider.icon(forBundleID: "com.apple.Safari") === icon,
                      "同一个 bundle 第二次解析返回了不同的对象 ⇒ 缓存没有生效")
        XCTAssertNil(SourceAppIconProvider.icon(forBundleID: "com.example.r425.nonexistent"),
                     "不存在的 bundle 必须返回 nil，交给视图退回 app 符号")
    }

    func testDetailHeaderWiresTheBadgeAndTheFallback() throws {
        let detail = codeOnly(try productSource(named: "Views/DetailView.swift"))
        XCTAssertTrue(detail.contains("SourceAppBadgePolicy.isVisible(sourceAppName: entry.sourceAppName)"),
                      "详情头部没有用 policy 判可见性 ⇒ 没有来源的记录也会占一格")
        XCTAssertTrue(detail.contains("SourceAppBadge(sourceAppBundleID: entry.sourceAppBundleID)"),
                      "详情头部没有挂 SourceAppBadge")
        XCTAssertTrue(detail.contains("headerMeta(entry, includeIcon: true, includeCopyVerb: true)")
                      && detail.contains("headerMeta(entry, includeIcon: false, includeCopyVerb: false)"),
                      "详情状态条没有「带图标/不带图标」两档候选 ⇒ 窄窗口只能截断时间或来源")
        XCTAssertTrue(detail.contains("SourceAppBadgePolicy.isVisible(sourceAppName: entry.sourceAppName,"),
                      "12 的窄宽分支没有按 detailWidth 判 ⇒ 最小窗口会把时间截掉")

        let badge = codeOnly(try productSource(named: "Views/SourceAppBadge.swift"))
        XCTAssertTrue(badge.contains("NSWorkspace.shared.urlForApplication(withBundleIdentifier: id)"),
                      "图标没有从系统解析应用 ⇒ 只能画出一颗通用符号")
        XCTAssertTrue(badge.contains("Image(systemName: SourceAppBadgePolicy.fallbackSymbolName)"),
                      "解析不到时没有退回 app 符号 ⇒ 有来源名的记录会少一截状态条")
    }

    private func codeOnly(_ source: String) -> String {
        source.components(separatedBy: "\n")
            .filter { !$0.trimmingCharacters(in: .whitespaces).hasPrefix("//") }
            .joined(separator: "\n")
    }

    private func productSource(named relativePath: String) throws -> String {
        var candidate = URL(fileURLWithPath: #filePath).deletingLastPathComponent()
        for _ in 0..<6 {
            let url = candidate.appendingPathComponent("Sources/ClipboardHistoryApp", isDirectory: true)
                .appendingPathComponent(relativePath)
            if let text = try? String(contentsOf: url, encoding: .utf8) { return text }
            candidate = candidate.deletingLastPathComponent()
        }
        throw NSError(domain: "SourceAppBadgeTests", code: 1,
                      userInfo: [NSLocalizedDescriptionKey:
                        "找不到 Sources/ClipboardHistoryApp/\(relativePath)"])
    }
}
